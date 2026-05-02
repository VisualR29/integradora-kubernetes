from __future__ import annotations

import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.db import create_engine, fetch_history, fetch_latest, init_schema, insert_signal
from app.logic import compute_signal
from app.market_client import fetch_prices
from app.metrics import APP_INFO, LATENCY, MARKET_FETCH, REQUESTS, SIGNAL_GEN
from app.models import SignalRecord

settings = Settings()
engine = create_engine(settings.database_url)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
http_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    APP_INFO.info({"version": "0.1.0", "service": settings.service_name})
    await init_schema(engine)
    http_client = httpx.AsyncClient()
    yield
    await http_client.aclose()
    await engine.dispose()


app = FastAPI(title="signal-engine", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def observe_requests(request: Request, call_next):
    path = request.url.path
    if path == "/metrics":
        return await call_next(request)
    start = time.perf_counter()
    response: Response = await call_next(request)
    elapsed = time.perf_counter() - start
    status = str(response.status_code)
    REQUESTS.labels(request.method, path, status).inc()
    LATENCY.labels(request.method, path).observe(elapsed)
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def _normalize_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not s or not s.replace(".", "").isalnum():
        raise HTTPException(status_code=400, detail="invalid symbol")
    return s


async def _build_signal(symbol: str) -> SignalRecord:
    assert http_client is not None
    need = max(settings.sma_long + 2, settings.pct_window + 2, 60)
    try:
        series = await fetch_prices(settings.market_data_base_url, symbol, need, http_client)
        MARKET_FETCH.labels("ok").inc()
    except Exception:
        MARKET_FETCH.labels("error").inc()
        raise HTTPException(status_code=502, detail="market_data_unavailable")

    comp = compute_signal(
        series.points,
        sma_short=settings.sma_short,
        sma_long=settings.sma_long,
        pct_window=settings.pct_window,
        pct_buy=settings.pct_buy_threshold,
        pct_sell=settings.pct_sell_threshold,
    )
    now = datetime.now(UTC).replace(microsecond=0)
    rec = SignalRecord(
        symbol=symbol,
        created_at=now.isoformat().replace("+00:00", "Z"),
        result=comp.result,
        reason=comp.reason,
        sma5=comp.sma5,
        sma20=comp.sma20,
        pct_change=comp.pct_change,
    )
    reason_label = (comp.reason.split(",")[0][:40] or "none").replace(" ", "_")
    SIGNAL_GEN.labels(comp.result, reason_label).inc()
    return rec


@app.post("/signals/generate", response_model=SignalRecord)
async def generate_signal(symbol: str):
    sym = _normalize_symbol(symbol)
    rec = await _build_signal(sym)
    async with SessionLocal() as session:
        async with session.begin():
            await insert_signal(session, rec)
    return rec


@app.get("/signals/latest", response_model=SignalRecord)
async def latest_signal(symbol: str):
    sym = _normalize_symbol(symbol)
    async with SessionLocal() as session:
        row = await fetch_latest(session, sym)
        if row:
            return row
    rec = await _build_signal(sym)
    async with SessionLocal() as session:
        async with session.begin():
            await insert_signal(session, rec)
    return rec


@app.get("/signals/history")
async def history(symbol: str, limit: int = 20):
    sym = _normalize_symbol(symbol)
    lim = max(1, min(limit, 100))
    async with SessionLocal() as session:
        items = await fetch_history(session, sym, lim)
    return {"items": items}

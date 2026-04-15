from __future__ import annotations

import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.config import Settings
from app.metrics import APP_INFO, LATENCY, REQUESTS
from app.models import PriceSeriesResponse, SignalRecord, SummaryResponse

settings = Settings()
client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    APP_INFO.info({"version": "0.1.0", "service": settings.service_name})
    client = httpx.AsyncClient(timeout=settings.request_timeout_seconds)
    yield
    await client.aclose()


app = FastAPI(title="api-bff", version="0.1.0", lifespan=lifespan, root_path="")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


def _symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not s or not s.replace(".", "").isalnum():
        raise HTTPException(status_code=400, detail="invalid symbol")
    return s


async def _get_prices(symbol: str, limit: int = 40) -> PriceSeriesResponse:
    assert client is not None
    url = f"{settings.market_data_base_url.rstrip('/')}/prices/{symbol}"
    r = await client.get(url, params={"limit": limit})
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail="market_data_error")
    return PriceSeriesResponse.model_validate(r.json())


async def _get_latest_signal(symbol: str) -> SignalRecord:
    assert client is not None
    url = f"{settings.signal_engine_base_url.rstrip('/')}/signals/latest"
    r = await client.get(url, params={"symbol": symbol})
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail="signal_engine_error")
    return SignalRecord.model_validate(r.json())


@app.get("/api/v1/summary", response_model=SummaryResponse)
async def summary(symbol: str):
    sym = _symbol(symbol)
    prices, signal = await _get_prices(sym, 40), await _get_latest_signal(sym)
    return SummaryResponse(symbol=sym, prices=prices, signal=signal)


@app.post("/api/v1/signals/recalculate", response_model=SignalRecord)
async def recalculate(symbol: str):
    sym = _symbol(symbol)
    assert client is not None
    url = f"{settings.signal_engine_base_url.rstrip('/')}/signals/generate"
    r = await client.post(url, params={"symbol": sym})
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail="signal_engine_error")
    return SignalRecord.model_validate(r.json())

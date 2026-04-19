from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.config import Settings
from app.db import create_engine, init_schema, session_factory
from app.metrics import APP_INFO, LATENCY, REQUESTS
from app.models import PriceSeriesResponse
from app.price_service import SymbolNotPermitted, resolve_prices

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    APP_INFO.info({"version": "0.2.0", "service": settings.service_name})
    engine = None
    app.state.session_maker = None
    if settings.database_url:
        engine = create_engine(settings.database_url)
        await init_schema(engine)
        app.state.session_maker = session_factory(engine)
    yield
    if engine is not None:
        await engine.dispose()


app = FastAPI(title="market-data", version="0.2.0", lifespan=lifespan)


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


@app.get("/prices/{symbol}", response_model=PriceSeriesResponse)
async def get_prices(request: Request, symbol: str, limit: int | None = None):
    lim = limit or settings.default_price_limit
    lim = max(1, min(lim, settings.max_price_limit))
    sm = getattr(request.app.state, "session_maker", None)
    try:
        return await resolve_prices(settings, sm, symbol, lim)
    except ValueError:
        raise HTTPException(status_code=404, detail="invalid symbol") from None
    except SymbolNotPermitted:
        raise HTTPException(
            status_code=403,
            detail="symbol not permitted for this deployment (see MARKET_ALLOWED_SYMBOLS)",
        ) from None

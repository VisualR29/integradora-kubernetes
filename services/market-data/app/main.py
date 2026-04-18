from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.config import Settings
from app.metrics import APP_INFO, FETCH, LATENCY, REQUESTS
from app.mock_series import generate_mock_series
from app.models import PriceSeriesResponse

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    APP_INFO.info({"version": "0.1.0", "service": settings.service_name})
    yield


app = FastAPI(title="market-data", version="0.1.0", lifespan=lifespan)


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
def get_prices(symbol: str, limit: int | None = None):
    sym = symbol.strip().upper()
    if not sym or not sym.replace(".", "").isalnum():
        raise HTTPException(status_code=404, detail="invalid symbol")
    lim = limit or settings.default_price_limit
    lim = max(1, min(lim, settings.max_price_limit))
    points = generate_mock_series(sym, lim)
    FETCH.labels("mock", "ok").inc()
    return PriceSeriesResponse(symbol=sym, source="mock", points=points)

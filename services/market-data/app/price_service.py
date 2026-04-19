from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.db import (
    fetch_candles_desc,
    get_last_sync_at,
    upsert_candles,
    upsert_sync_meta,
)
from app.metrics import FETCH
from app.mock_series import generate_mock_series
from app.models import PricePoint, PriceSeriesResponse
from app.providers import twelve_data, tiingo


class SymbolNotPermitted(Exception):
    """El símbolo no está en MARKET_ALLOWED_SYMBOLS (modo demo)."""


def parse_allowed_symbols(raw: str | None) -> frozenset[str] | None:
    if raw is None or not str(raw).strip():
        return None
    parts = {p.strip().upper() for p in str(raw).split(",") if p.strip()}
    return frozenset(parts) if parts else None


def _valid_symbol(sym: str) -> bool:
    if not sym or len(sym) > 32:
        return False
    if not sym[0].isalpha():
        return False
    for c in sym:
        if c.isalnum() or c in ".-":
            continue
        return False
    return True


def _is_fresh(last: datetime | None, stale_after_seconds: int) -> bool:
    if last is None:
        return False
    return datetime.now(UTC) - last <= timedelta(seconds=stale_after_seconds)


async def resolve_prices(
    settings: Settings,
    session_maker: async_sessionmaker[AsyncSession] | None,
    symbol: str,
    limit: int,
) -> PriceSeriesResponse:
    sym = symbol.strip().upper()
    if not _valid_symbol(sym):
        raise ValueError("invalid symbol")

    allowed = parse_allowed_symbols(settings.allowed_symbols)
    if allowed is not None and sym not in allowed:
        raise SymbolNotPermitted(sym)

    interval = settings.candle_interval
    timeout = settings.fetch_timeout_seconds
    order = [p.strip().lower() for p in settings.provider_order.split(",") if p.strip()]

    db_points: list[PricePoint] = []
    if session_maker is not None:
        async with session_maker() as session:
            db_points = await fetch_candles_desc(session, symbol=sym, interval=interval, limit=limit)
            last_sync = await get_last_sync_at(session, symbol=sym, interval=interval)
        if (
            last_sync is not None
            and _is_fresh(last_sync, settings.stale_after_seconds)
            and db_points
            and (
                len(db_points) >= limit
                or len(db_points) >= settings.cache_serve_min_rows
            )
        ):
            FETCH.labels("postgres", "ok").inc()
            return PriceSeriesResponse(symbol=sym, source="postgres", points=db_points)

    async with httpx.AsyncClient(headers={"User-Agent": "signals-market-data/0.2"}) as client:
        for name in order:
            if name == "mock":
                continue
            try:
                if name == "tiingo" and settings.tiingo_token:
                    pts = await tiingo.fetch_daily_prices(
                        client,
                        base_url=settings.tiingo_base_url,
                        token=settings.tiingo_token,
                        symbol=sym,
                        limit=limit,
                        timeout=timeout,
                    )
                    if pts:
                        await _persist(settings, session_maker, sym, interval, pts, "tiingo")
                        FETCH.labels("tiingo", "ok").inc()
                        return PriceSeriesResponse(symbol=sym, source="tiingo", points=pts)
                elif name in ("twelvedata", "twelve_data", "12data") and settings.twelvedata_api_key:
                    pts = await twelve_data.fetch_daily_time_series(
                        client,
                        base_url=settings.twelvedata_base_url,
                        apikey=settings.twelvedata_api_key,
                        symbol=sym,
                        limit=limit,
                        timeout=timeout,
                    )
                    if pts:
                        await _persist(settings, session_maker, sym, interval, pts, "twelvedata")
                        FETCH.labels("twelvedata", "ok").inc()
                        return PriceSeriesResponse(symbol=sym, source="twelvedata", points=pts)
            except httpx.HTTPStatusError as e:
                FETCH.labels(name, f"http_{e.response.status_code}").inc()
            except Exception:
                FETCH.labels(name, "error").inc()

    if db_points:
        FETCH.labels("postgres_stale", "ok").inc()
        return PriceSeriesResponse(symbol=sym, source="postgres_stale", points=db_points)

    pts = generate_mock_series(sym, limit)
    FETCH.labels("mock", "ok").inc()
    return PriceSeriesResponse(symbol=sym, source="mock", points=pts)


async def _persist(
    settings: Settings,
    session_maker: async_sessionmaker[AsyncSession] | None,
    symbol: str,
    interval: str,
    points: list[PricePoint],
    source: str,
) -> None:
    if session_maker is None or not points:
        return
    async with session_maker() as session:
        async with session.begin():
            await upsert_candles(session, symbol=symbol, interval=interval, points=points, source=source)
            if source in ("tiingo", "twelvedata"):
                await upsert_sync_meta(session, symbol=symbol, interval=interval, source=source)

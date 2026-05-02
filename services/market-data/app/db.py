from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import PricePoint

SCHEMA_STATEMENTS = (
    "CREATE SCHEMA IF NOT EXISTS market",
    """
    CREATE TABLE IF NOT EXISTS market.price_candles (
        symbol TEXT NOT NULL,
        interval TEXT NOT NULL,
        bucket_ts TIMESTAMPTZ NOT NULL,
        open DOUBLE PRECISION NOT NULL,
        high DOUBLE PRECISION NOT NULL,
        low DOUBLE PRECISION NOT NULL,
        close DOUBLE PRECISION NOT NULL,
        volume DOUBLE PRECISION NOT NULL DEFAULT 0,
        source TEXT NOT NULL,
        PRIMARY KEY (symbol, interval, bucket_ts)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS price_candles_symbol_interval_ts_desc_idx
    ON market.price_candles (symbol, interval, bucket_ts DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS market.price_sync_meta (
        symbol TEXT NOT NULL,
        interval TEXT NOT NULL,
        synced_at TIMESTAMPTZ NOT NULL,
        source TEXT NOT NULL,
        PRIMARY KEY (symbol, interval)
    )
    """,
)


def create_engine(database_url: str):
    return create_async_engine(database_url, pool_pre_ping=True)


async def init_schema(engine) -> None:
    async with engine.begin() as conn:
        for stmt in SCHEMA_STATEMENTS:
            await conn.execute(text(stmt))


def session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def fetch_candles_desc(
    session: AsyncSession, *, symbol: str, interval: str, limit: int
) -> list[PricePoint]:
    res = await session.execute(
        text(
            """
            SELECT bucket_ts, open, high, low, close, volume
            FROM market.price_candles
            WHERE symbol = :symbol AND interval = :interval
            ORDER BY bucket_ts DESC
            LIMIT :limit
            """
        ),
        {"symbol": symbol, "interval": interval, "limit": limit},
    )
    rows = list(res.mappings().all())
    rows.reverse()
    out: list[PricePoint] = []
    for row in rows:
        ts = row["bucket_ts"]
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        out.append(
            PricePoint(
                ts=ts.isoformat().replace("+00:00", "Z"),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"] or 0),
            )
        )
    return out


async def get_last_sync_at(
    session: AsyncSession, *, symbol: str, interval: str
) -> datetime | None:
    res = await session.execute(
        text(
            """
            SELECT synced_at
            FROM market.price_sync_meta
            WHERE symbol = :symbol AND interval = :interval
            """
        ),
        {"symbol": symbol, "interval": interval},
    )
    row = res.mappings().first()
    if not row:
        return None
    ts = row["synced_at"]
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return ts


async def upsert_sync_meta(
    session: AsyncSession, *, symbol: str, interval: str, source: str
) -> None:
    synced_at = datetime.now(UTC)
    await session.execute(
        text(
            """
            INSERT INTO market.price_sync_meta (symbol, interval, synced_at, source)
            VALUES (:symbol, :interval, :synced_at, :source)
            ON CONFLICT (symbol, interval) DO UPDATE SET
                synced_at = EXCLUDED.synced_at,
                source = EXCLUDED.source
            """
        ),
        {
            "symbol": symbol,
            "interval": interval,
            "synced_at": synced_at,
            "source": source,
        },
    )


async def upsert_candles(
    session: AsyncSession,
    *,
    symbol: str,
    interval: str,
    points: list[PricePoint],
    source: str,
) -> None:
    for p in points:
        ts = datetime.fromisoformat(p.ts.replace("Z", "+00:00"))
        await session.execute(
            text(
                """
                INSERT INTO market.price_candles
                (symbol, interval, bucket_ts, open, high, low, close, volume, source)
                VALUES (:symbol, :interval, :bucket_ts, :open, :high, :low, :close, :volume, :source)
                ON CONFLICT (symbol, interval, bucket_ts) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume,
                    source = EXCLUDED.source
                """
            ),
            {
                "symbol": symbol,
                "interval": interval,
                "bucket_ts": ts,
                "open": p.open,
                "high": p.high,
                "low": p.low,
                "close": p.close,
                "volume": p.volume,
                "source": source,
            },
        )

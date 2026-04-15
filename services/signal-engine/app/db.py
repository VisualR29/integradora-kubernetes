from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.models import SignalRecord

SCHEMA_SQL = """
CREATE SCHEMA IF NOT EXISTS signals;
CREATE TABLE IF NOT EXISTS signals.signal_history (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    result TEXT NOT NULL,
    reason TEXT NOT NULL,
    sma5 DOUBLE PRECISION,
    sma20 DOUBLE PRECISION,
    pct_change DOUBLE PRECISION
);
CREATE INDEX IF NOT EXISTS signal_history_symbol_created_idx
ON signals.signal_history (symbol, created_at DESC);
"""


def create_engine(database_url: str):
    return create_async_engine(database_url, pool_pre_ping=True)


async def init_schema(engine) -> None:
    async with engine.begin() as conn:
        await conn.execute(text(SCHEMA_SQL))


async def insert_signal(session: AsyncSession, row: SignalRecord) -> None:
    created = datetime.fromisoformat(row.created_at.replace("Z", "+00:00"))
    await session.execute(
        text(
            """
            INSERT INTO signals.signal_history
            (symbol, created_at, result, reason, sma5, sma20, pct_change)
            VALUES (:symbol, :created_at, :result, :reason, :sma5, :sma20, :pct_change)
            """
        ),
        {
            "symbol": row.symbol,
            "created_at": created,
            "result": row.result,
            "reason": row.reason,
            "sma5": row.sma5,
            "sma20": row.sma20,
            "pct_change": row.pct_change,
        },
    )


async def fetch_latest(session: AsyncSession, symbol: str) -> SignalRecord | None:
    res = await session.execute(
        text(
            """
            SELECT symbol, created_at, result, reason, sma5, sma20, pct_change
            FROM signals.signal_history
            WHERE symbol = :symbol
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {"symbol": symbol},
    )
    row = res.mappings().first()
    if not row:
        return None
    created = row["created_at"]
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    return SignalRecord(
        symbol=row["symbol"],
        created_at=created.isoformat().replace("+00:00", "Z"),
        result=row["result"],
        reason=row["reason"],
        sma5=row["sma5"],
        sma20=row["sma20"],
        pct_change=row["pct_change"],
    )


async def fetch_history(session: AsyncSession, symbol: str, limit: int) -> list[SignalRecord]:
    res = await session.execute(
        text(
            """
            SELECT symbol, created_at, result, reason, sma5, sma20, pct_change
            FROM signals.signal_history
            WHERE symbol = :symbol
            ORDER BY created_at DESC
            LIMIT :limit
            """
        ),
        {"symbol": symbol, "limit": limit},
    )
    out: list[SignalRecord] = []
    for row in res.mappings().all():
        created = row["created_at"]
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        out.append(
            SignalRecord(
                symbol=row["symbol"],
                created_at=created.isoformat().replace("+00:00", "Z"),
                result=row["result"],
                reason=row["reason"],
                sma5=row["sma5"],
                sma20=row["sma20"],
                pct_change=row["pct_change"],
            )
        )
    return out

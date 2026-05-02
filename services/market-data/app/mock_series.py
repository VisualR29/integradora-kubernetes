"""Serie de precios sintética determinista por símbolo (sin trading real)."""
from __future__ import annotations

import hashlib
import math
from datetime import UTC, datetime, timedelta

from app.models import PricePoint


def _seed(symbol: str) -> int:
    h = hashlib.sha256(symbol.upper().encode()).hexdigest()
    return int(h[:8], 16)


def generate_mock_series(symbol: str, n: int) -> list[PricePoint]:
    seed = _seed(symbol)
    rng = (seed % 10_000) / 10_000.0
    base = 50.0 + (seed % 200)
    points: list[PricePoint] = []
    now = datetime.now(UTC).replace(microsecond=0)
    for i in range(n):
        t = now - timedelta(minutes=n - 1 - i)
        wave = math.sin(i / 5.0 + rng) * 2.0 + math.cos(i / 13.0) * 0.8
        noise = ((seed >> (i % 16)) & 0xFF) / 512.0 - 0.25
        close = round(base + wave + noise + i * 0.02, 4)
        spread = 0.05 + abs(wave) * 0.01
        high = round(close + spread, 4)
        low = round(close - spread, 4)
        open_ = round(points[-1].close if points else close, 4)
        vol = float(1_000 + (seed + i * 17) % 5_000)
        points.append(
            PricePoint(
                ts=t.isoformat().replace("+00:00", "Z"),
                open=open_,
                high=max(open_, high, close),
                low=min(open_, low, close),
                close=close,
                volume=vol,
            )
        )
    return points

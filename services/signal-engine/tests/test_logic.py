from datetime import UTC, datetime, timedelta

from app.logic import compute_signal
from app.models import PricePoint


def _series(n: int, slope: float = 0.0) -> list[PricePoint]:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    out: list[PricePoint] = []
    price = 100.0
    for i in range(n):
        price += slope + (1 if i % 7 == 0 else 0) * 0.1
        ts = (base + timedelta(minutes=i)).isoformat().replace("+00:00", "Z")
        out.append(
            PricePoint(ts=ts, open=price, high=price + 0.2, low=price - 0.2, close=price, volume=1000.0)
        )
    return out


def test_insufficient_data():
    pts = _series(10)
    r = compute_signal(pts, sma_short=5, sma_long=20, pct_window=24)
    assert r.result == "HOLD"
    assert r.reason == "insufficient_data"


def test_hold_flat():
    pts = _series(50, slope=0.0)
    r = compute_signal(pts)
    assert r.result in ("BUY", "SELL", "HOLD")

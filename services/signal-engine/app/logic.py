"""Reglas simples: cruce SMA(5)/SMA(20) y cambio % en ventana corta."""
from __future__ import annotations

from dataclasses import dataclass

from app.models import PricePoint


@dataclass
class SignalComputation:
    result: str
    reason: str
    sma5: float | None
    sma20: float | None
    pct_change: float | None


def _sma(values: list[float], window: int) -> float | None:
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def compute_signal(
    points: list[PricePoint],
    *,
    sma_short: int = 5,
    sma_long: int = 20,
    pct_window: int = 24,
    pct_buy: float = 1.5,
    pct_sell: float = -1.5,
) -> SignalComputation:
    closes = [p.close for p in points]
    if len(closes) < max(sma_long + 1, pct_window + 1):
        return SignalComputation(
            result="HOLD",
            reason="insufficient_data",
            sma5=_sma(closes, sma_short),
            sma20=_sma(closes, sma_long),
            pct_change=None,
        )

    sma5 = _sma(closes, sma_short)
    sma20 = _sma(closes, sma_long)
    prev_sma5 = _sma(closes[:-1], sma_short)
    prev_sma20 = _sma(closes[:-1], sma_long)

    ref = closes[-(pct_window + 1)]
    last = closes[-1]
    pct_change = round((last - ref) / ref * 100.0, 4) if ref else None

    reasons: list[str] = []

    cross_buy = (
        prev_sma5 is not None
        and prev_sma20 is not None
        and sma5 is not None
        and sma20 is not None
        and prev_sma5 <= prev_sma20
        and sma5 > sma20
    )
    cross_sell = (
        prev_sma5 is not None
        and prev_sma20 is not None
        and sma5 is not None
        and sma20 is not None
        and prev_sma5 >= prev_sma20
        and sma5 < sma20
    )

    if pct_change is not None and pct_change >= pct_buy:
        reasons.append("pct_momentum_up")
    if pct_change is not None and pct_change <= pct_sell:
        reasons.append("pct_momentum_down")
    if cross_buy:
        reasons.append("sma_cross_bullish")
    if cross_sell:
        reasons.append("sma_cross_bearish")

    if "sma_cross_bullish" in reasons or "pct_momentum_up" in reasons:
        return SignalComputation(
            result="BUY",
            reason=",".join(reasons) or "rules",
            sma5=sma5,
            sma20=sma20,
            pct_change=pct_change,
        )
    if "sma_cross_bearish" in reasons or "pct_momentum_down" in reasons:
        return SignalComputation(
            result="SELL",
            reason=",".join(reasons) or "rules",
            sma5=sma5,
            sma20=sma20,
            pct_change=pct_change,
        )
    return SignalComputation(
        result="HOLD",
        reason="no_rule_trigger",
        sma5=sma5,
        sma20=sma20,
        pct_change=pct_change,
    )

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from app.models import PricePoint


async def fetch_daily_time_series(
    client: httpx.AsyncClient,
    *,
    base_url: str,
    apikey: str,
    symbol: str,
    limit: int,
    timeout: float,
) -> list[PricePoint]:
    url = f"{base_url.rstrip('/')}/time_series"
    r = await client.get(
        url,
        params={
            "symbol": symbol,
            "interval": "1day",
            "outputsize": min(limit + 5, 5000),
            "apikey": apikey,
        },
        timeout=timeout,
    )
    r.raise_for_status()
    body = r.json()
    if body.get("status") == "error":
        msg = body.get("message") or body.get("code") or "twelvedata_error"
        raise RuntimeError(str(msg))
    values = body.get("values") or []
    if not isinstance(values, list):
        return []
    parsed: list[tuple[datetime, PricePoint]] = []
    for row in values:
        dt_raw = row.get("datetime")
        if not dt_raw:
            continue
        s = str(dt_raw).strip()
        day_part = s[:10]
        if len(day_part) != 10:
            continue
        try:
            day = datetime.strptime(day_part, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            continue
        close = float(row.get("close") or 0)
        open_ = float(row.get("open") or close)
        high = float(row.get("high") or max(open_, close))
        low = float(row.get("low") or min(open_, close))
        vol = float(row.get("volume") or 0)
        if vol < 0:
            vol = 0.0
        parsed.append(
            (
                day,
                PricePoint(
                    ts=day.isoformat().replace("+00:00", "Z"),
                    open=open_,
                    high=max(open_, high, close),
                    low=min(open_, low, close),
                    close=close,
                    volume=vol,
                ),
            )
        )
    parsed.sort(key=lambda x: x[0])
    return [p for _, p in parsed[-limit:]]

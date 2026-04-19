from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import httpx

from app.models import PricePoint


async def fetch_daily_prices(
    client: httpx.AsyncClient,
    *,
    base_url: str,
    token: str,
    symbol: str,
    limit: int,
    timeout: float,
) -> list[PricePoint]:
    end = date.today()
    start = end - timedelta(days=limit + 40)
    url = f"{base_url.rstrip('/')}/tiingo/daily/{symbol}/prices"
    r = await client.get(
        url,
        params={"startDate": start.isoformat(), "endDate": end.isoformat(), "token": token},
        timeout=timeout,
    )
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        return []
    points: list[PricePoint] = []
    for row in data[-limit:]:
        d = row.get("date") or row.get("Date")
        if not d:
            continue
        day = datetime.strptime(str(d)[:10], "%Y-%m-%d").replace(tzinfo=UTC)
        close = float(row.get("close") or row.get("adjClose") or 0)
        open_ = float(row.get("open") or close)
        high = float(row.get("high") or max(open_, close))
        low = float(row.get("low") or min(open_, close))
        vol = float(row.get("volume") or 0)
        if vol < 0:
            vol = 0.0
        points.append(
            PricePoint(
                ts=day.isoformat().replace("+00:00", "Z"),
                open=open_,
                high=max(open_, high, close),
                low=min(open_, low, close),
                close=close,
                volume=vol,
            )
        )
    return points

from __future__ import annotations

import httpx

from app.models import PriceSeriesResponse


async def fetch_prices(base_url: str, symbol: str, limit: int, client: httpx.AsyncClient) -> PriceSeriesResponse:
    url = f"{base_url.rstrip('/')}/prices/{symbol}"
    r = await client.get(url, params={"limit": limit}, timeout=10.0)
    r.raise_for_status()
    return PriceSeriesResponse.model_validate(r.json())

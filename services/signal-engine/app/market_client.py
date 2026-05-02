from __future__ import annotations

import httpx
from fastapi import HTTPException

from app.models import PriceSeriesResponse


async def fetch_prices(base_url: str, symbol: str, limit: int, client: httpx.AsyncClient) -> PriceSeriesResponse:
    url = f"{base_url.rstrip('/')}/prices/{symbol}"
    r = await client.get(url, params={"limit": limit}, timeout=10.0)
    if r.status_code == 400:
        raise HTTPException(status_code=400, detail="invalid symbol")
    r.raise_for_status()
    return PriceSeriesResponse.model_validate(r.json())

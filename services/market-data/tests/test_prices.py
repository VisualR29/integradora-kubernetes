import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.price_service import SymbolNotPermitted, parse_allowed_symbols, resolve_prices
from app.providers import tiingo, twelve_data

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_prices_mock():
    r = client.get("/prices/AAPL", params={"limit": 30})
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == "AAPL"
    assert body["source"] == "mock"
    assert len(body["points"]) == 30
    assert "close" in body["points"][0]


def test_prices_invalid():
    r = client.get("/prices/@@")
    assert r.status_code == 400


def test_prices_symbol_with_hyphen():
    r = client.get("/prices/BRK-A", params={"limit": 5})
    assert r.status_code == 200
    assert r.json()["symbol"] == "BRK-A"


def test_parse_allowed_symbols_none_and_set():
    assert parse_allowed_symbols(None) is None
    assert parse_allowed_symbols("") is None
    assert parse_allowed_symbols("  ") is None
    s = parse_allowed_symbols(" AAPL , msft , ")
    assert s == frozenset({"AAPL", "MSFT"})


def test_resolve_prices_symbol_not_permitted():
    cfg = Settings(
        allowed_symbols="MSFT,GOOG",
        database_url=None,
        provider_order="mock",
    )

    async def blocked():
        await resolve_prices(cfg, None, "AAPL", 5)

    with pytest.raises(SymbolNotPermitted):
        asyncio.run(blocked())


def test_resolve_prices_allowed_with_mock():
    cfg = Settings(
        allowed_symbols="AAPL",
        database_url=None,
        provider_order="mock",
    )

    async def ok():
        return await resolve_prices(cfg, None, "AAPL", 5)

    r = asyncio.run(ok())
    assert r.symbol == "AAPL"
    assert r.source == "mock"


def test_prices_403_when_allowlist_excludes_symbol(monkeypatch):
    import app.main as main_mod

    monkeypatch.setattr(
        main_mod,
        "settings",
        Settings(allowed_symbols="MSFT", database_url=None, provider_order="mock"),
    )
    with TestClient(main_mod.app) as c:
        r = c.get("/prices/AAPL", params={"limit": 5})
    assert r.status_code == 403


def test_tiingo_fetch_daily_parses_rows():
    sample = [
        {
            "date": "2024-01-02",
            "open": 100,
            "high": 102,
            "low": 99,
            "close": 101,
            "volume": 1000,
        },
        {
            "date": "2024-01-03",
            "open": 101,
            "high": 103,
            "low": 100,
            "close": 102,
            "volume": 1100,
        },
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=sample)

    transport = httpx.MockTransport(handler)

    async def run():
        async with httpx.AsyncClient(transport=transport) as client:
            return await tiingo.fetch_daily_prices(
                client,
                base_url="https://api.tiingo.com",
                token="t",
                symbol="TEST",
                limit=2,
                timeout=5.0,
            )

    pts = asyncio.run(run())
    assert len(pts) == 2
    assert pts[-1].close == 102


def test_twelvedata_fetch_daily_parses_values():
    body = {
        "values": [
            {
                "datetime": "2024-01-04",
                "open": "10",
                "high": "11",
                "low": "9",
                "close": "10.5",
                "volume": "100",
            },
            {
                "datetime": "2024-01-05",
                "open": "10.5",
                "high": "12",
                "low": "10",
                "close": "11.5",
                "volume": "200",
            },
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)

    async def run():
        async with httpx.AsyncClient(transport=transport) as client:
            return await twelve_data.fetch_daily_time_series(
                client,
                base_url="https://api.twelvedata.com",
                apikey="k",
                symbol="TEST",
                limit=2,
                timeout=5.0,
            )

    pts = asyncio.run(run())
    assert len(pts) == 2
    assert pts[-1].close == 11.5


def test_fallback_tiingo_500_to_twelvedata():
    def handler(request: httpx.Request) -> httpx.Response:
        u = str(request.url)
        if "/tiingo/daily/" in u:
            return httpx.Response(500, text="upstream")
        if "/time_series" in u:
            return httpx.Response(
                200,
                json={
                    "values": [
                        {
                            "datetime": "2024-01-04",
                            "open": "10",
                            "high": "11",
                            "low": "9",
                            "close": "10.5",
                            "volume": "100",
                        }
                    ]
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    cfg = Settings(
        database_url=None,
        tiingo_token="t",
        twelvedata_api_key="k",
        provider_order="tiingo,twelvedata,mock",
    )

    async def run():
        async with httpx.AsyncClient(transport=transport) as hc:
            return await resolve_prices(cfg, None, "AAPL", 1, http_client=hc)

    r = asyncio.run(run())
    assert r.source == "twelvedata"
    assert len(r.points) == 1
    assert r.points[0].close == 10.5

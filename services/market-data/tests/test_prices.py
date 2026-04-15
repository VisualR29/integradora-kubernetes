from fastapi.testclient import TestClient

from app.main import app

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
    assert r.status_code == 404

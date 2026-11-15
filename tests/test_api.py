from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json()["status"] == "ok"


def test_compare():
    r = client.post("/api/compare", json={"name": "Pilot", "area_ha": 2, "texture": "sandy"})
    assert r.status_code == 200
    assert len(r.json()["scenarios"]) == 3


def test_synthetic_endpoint_label():
    r = client.get("/api/climate?mode=synthetic&lat=15.289&lon=120.024&year=2025")
    assert r.status_code == 200
    assert r.json()["source_type"] == "synthetic"


def test_coordinates_validated():
    assert client.get("/api/climate?lat=200&mode=synthetic").status_code == 422
    assert client.post("/api/compare", json={"soil_ph": 17}).status_code == 422

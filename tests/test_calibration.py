from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_calibration_overlay_has_unambiguous_provenance_labels():
    r = client.get("/")
    assert r.status_code == 200
    for text in (
        'AgriORBIT<br><em>Calibration</em>',
        'id="cal-enter"',
        'id="cal-replay"',
        'NASA POWER historical data',
        'Manual connection on dashboard',
        'Concept; telemetry simulator only',
        'Concept art, not geospatial terrain',
    ):
        assert text in r.text

def test_calibration_image_and_js_are_served():
    image = client.get("/assets/calibration-art.png")
    script = client.get("/assets/app.js")
    assert image.status_code == 200
    assert image.headers.get("content-type", "").startswith("image/png")
    assert script.status_code == 200
    assert "startupChecks" in script.text
    assert "NASA data still requires manual retrieval" in script.text

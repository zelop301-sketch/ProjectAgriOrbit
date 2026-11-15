from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

ROOT=Path(__file__).resolve().parents[1]

def test_phase20_asset_not_old_rover_photo():
    css=(ROOT/'web/styles.css').read_text(encoding='utf-8')
    assert "url('/assets/mission-farm-clean-v20.jpg')" in css
    assert 'mission-farm-scene.jpg' not in css
    assert (ROOT/'web/mission-farm-clean-v20.jpg').is_file()
    assert not (ROOT/'web/mission-farm-scene.jpg').exists()

def test_phase20_served_as_real_app_asset():
    client=TestClient(app)
    response=client.get('/assets/mission-farm-clean-v20.jpg')
    assert response.status_code==200 and response.headers['content-type'].startswith('image/jpeg')
    health=client.get('/api/health').json()
    assert health['build']=='phase34-botolan-evidence-decisions-3.4.0'
    assert health['photographic_rover_in_backdrop'] is False
    assert health['recommended_port']==8034

def test_phase20_keeps_separate_3d_rover_and_boot():
    html=(ROOT/'web/index.html').read_text(encoding='utf-8')
    assert 'id="cmd-viewport"' in html
    assert 'id="cmd-rover-phase"' in html
    assert 'id="calibration"' in html
    assert 'phase34-botolan-evidence-decisions-3.4.0' in html

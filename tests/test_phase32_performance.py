from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
ROOT=Path(__file__).resolve().parents[1]

def test_build_and_100fps_settings():
    client=TestClient(app)
    health=client.get('/api/health').json()
    assert health['build']=='phase34-botolan-evidence-decisions-3.4.0'
    assert health['renderer_preset']=='fps100'
    assert health['renderer_target_fps']==100
    assert health['fps_guaranteed'] is False
    html=client.get('/').text
    assert '<option value="fps100" selected>' in html
    assert '100 FPS Target' in html
    assert client.get('/assets/rover3d.js').status_code==200
    assert client.get('/assets/click-drop-fx.js').status_code==200

def test_real_fps_measurement_and_adaptive_cpu_cost():
    js=(ROOT/'web/rover3d.js').read_text()
    ui=(ROOT/'web/command-dashboard.js').read_text()
    assert 'this.fps=Math.round(this.frameCount/seconds)' in js
    assert "this.quality==='fps100'?this.drawIntervalMs" in js
    assert 'this.drawMsEma' in js
    assert "this.adaptiveScale=Math.max(.60" in js
    assert 'this.ca=Math.cos(this.yaw)' in js
    assert "quality==='fps100'?'⚡ 100 FPS TARGET'" in ui
    assert '100 TARGET' in ui

def test_preserves_boot_science_and_click_safety():
    c=TestClient(app)
    assert c.get('/api/health').json()['boot_duration_seconds']==15
    assert c.get('/api/hazards/capabilities').status_code==200
    assert c.get('/assets/leaf-cursor.js').status_code==200
    assert 'LIFETIME_MS = 1250' in (ROOT/'web/click-drop-fx.js').read_text()
    assert 'DURATION_MS = 15000' in (ROOT/'web/seedling-boot.js').read_text()

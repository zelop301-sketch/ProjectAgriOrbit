from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
ROOT=Path(__file__).resolve().parents[1]

def test_phase31_launch_and_health():
    client=TestClient(app)
    assert client.get('/api/health').json()['build']=='phase34-botolan-evidence-decisions-3.4.0'
    assert client.get('/api/health').json()['recommended_port']==8034
    assert 'phase34-botolan-evidence-decisions-3.4.0' in client.get('/').text
    assert 'launch_phase34.py' in (ROOT/'START_AGRIORBIT_WINDOWS.cmd').read_text()

def test_pointer_capture_and_diagnostic_trigger():
    js=(ROOT/'web/click-drop-fx.js').read_text()
    html=(ROOT/'web/index.html').read_text()
    css=(ROOT/'web/styles.css').read_text()
    assert 'id="agri-splash-test"' in html
    assert 'testButton?.addEventListener' in js
    assert "{capture:true, passive:true}" in js
    assert 'MAX_IMPACTS = 10' in js
    assert 'LIFETIME_MS = 1250' in js
    assert 'prefers-reduced-motion' in js
    assert '.agri-droplet-layer:not(.agri-drop-motion-override)' in css
    assert (ROOT/'VERIFY_PHASE31_SPLASH_FIX_OFFLINE.html').is_file()

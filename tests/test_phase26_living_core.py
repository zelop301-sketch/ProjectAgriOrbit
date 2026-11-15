from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
R=Path(__file__).resolve().parents[1]

def test_phase26_live_asset_and_health():
    resp=TestClient(app).get('/api/health')
    assert resp.status_code==200
    assert resp.json()['build']=='phase34-botolan-evidence-decisions-3.4.0'
    assert resp.json()['recommended_port']==8034
    assert resp.json()['living_core']=='compositor-static-webp-v27'
    assert (R/'web/agriorbit-living-core.gif').read_bytes().startswith(b'GIF89a')

def test_phase26_boot_has_original_gif_and_separate_checks():
    html=TestClient(app).get('/').text
    assert 'id="cal26-core-animation"' in html
    assert '/assets/agriorbit-living-core-fast.webp' in html
    assert 'id="cal-progress"' in html
    assert 'Only checks 01–04 count toward application readiness' in html
    for key in ['interface','farm','api','scenarios']:
        assert f'id="cal-check-{key}"' in html

def test_phase26_replay_and_reduced_motion():
    js=(R/'web/seedling-boot.js').read_text()
    assert 'DURATION_MS = 15000' in js
    assert 'restartLivingCore(token)' in js
    assert 'forceFullMotion' in js
    assert 'clamped === 1' in js
    assert 'not a diagnostic score' in (R/'web/index.html').read_text()

def test_phase26_launcher_and_asset_delivery():
    assert 'launch_phase34.py' in (R/'START_AGRIORBIT_WINDOWS.cmd').read_text()
    assert 'PORT=8034' in (R/'scripts/launch_phase34.py').read_text()
    c=TestClient(app)
    r=c.get('/assets/agriorbit-living-core-fast.webp')
    assert r.status_code==200 and r.content[:4] == b'RIFF'

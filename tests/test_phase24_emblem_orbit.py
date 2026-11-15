from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web'
client = TestClient(app)


def test_emblem_cursor_asset_served_and_optimized():
    response = client.get('/assets/agriorbit-cursor.webp')
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('image/webp')
    assert len(response.content) < 100_000


def test_cursor_loaded_in_actual_main_ui():
    html = client.get('/').text
    assert '/assets/leaf-cursor.js?v=phase34-botolan-evidence-decisions-3.4.0' in html
    assert 'LEAF FX ON' in html
    assert 'agriorbit-cursor.webp' not in html
    assert 'id="agri-wind-toggle"' in html
    assert 'id="agri-drop-sfx-toggle"' in html


def test_emblem_is_directly_used_in_existing_cursor_engine():
    js = (WEB / 'leaf-cursor.js').read_text()
    css = (WEB / 'styles.css').read_text()
    assert 'agri-leaf-svg' in js
    assert 'agri-bio-leaf-cursor' in js
    assert js.count('<i class="leaf-cursor-orb"') == 3
    assert '.agri-emblem-cursor .leaf-cursor-ring::before' in css
    assert 'conic-gradient' in css
    assert 'MAX_RIBBONS = 75' in js
    assert 'clickPulse' in js


def test_accessibility_is_unchanged():
    js = (WEB / 'leaf-cursor.js').read_text()
    css = (WEB / 'styles.css').read_text()
    assert 'prefers-reduced-motion: reduce' in js
    assert 'any-pointer: fine' in js
    assert 'agri-leaf-editing' in js
    assert 'pointer-events:none' in css
    assert 'pointer: coarse' in css


def test_relaunch_uses_dedicated_phase24_port():
    data = client.get('/api/health').json()
    assert data['build'] == 'phase34-botolan-evidence-decisions-3.4.0'
    assert data['recommended_port'] == 8034
    assert 'launch_phase34.py' in (ROOT / 'START_AGRIORBIT_WINDOWS.cmd').read_text()
    assert 'PORT=8034' in (ROOT / 'scripts/launch_phase34.py').read_text()


def test_offline_verification_is_bundled():
    html = (ROOT / 'VERIFY_EMBLEM_CURSOR_OFFLINE.html').read_text()
    assert 'web/leaf-cursor.js' in html
    assert 'web/styles.css' in html
    assert 'web/agriorbit-cursor.webp' in html

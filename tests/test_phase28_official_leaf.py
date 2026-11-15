from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'

def test_leaf_cursor_native_svg_and_default():
    js=(WEB/'leaf-cursor.js').read_text()
    assert 'agri-bio-leaf-cursor' in js
    assert 'agri-leaf-svg' in js
    assert 'agri-leaf-vein' in js
    assert 'agri-emblem-cursor-image' not in js
    assert "'agriorbit:official-leaf:v4'" in js
    assert 'MAX_RIBBONS = 75' in js
    assert 'onPointerMove' in js and 'emitWind' in js

def test_controls_and_sound_are_in_app():
    html=(WEB/'index.html').read_text()
    assert 'LEAF FX ON' in html
    assert 'WIND: BREEZE' in html
    assert 'DROP SFX ON' in html
    assert '/assets/leaf-cursor.js?v=phase34-botolan-evidence-decisions-3.4.0' in html
    assert 'cursor-toggle-emblem' not in html
    sfx=(WEB/'drop-sfx.js').read_text()
    assert 'AudioContext' in sfx and 'event.isTrusted' in sfx and 'pointerdown' in sfx

def test_native_leaves_styled_and_touch_safe():
    css=(WEB/'styles.css').read_text()
    assert '.agri-bio-leaf-cursor' in css
    assert '.agri-leaf-vein-wrap' in css
    assert '.agri-leaf-wind' in css
    assert 'html.agri-leaf-explicit' in css

def test_build_and_launcher():
    c=TestClient(app)
    j=c.get('/api/health').json()
    assert j['build']=='phase34-botolan-evidence-decisions-3.4.0'
    assert j['recommended_port']==8034
    assert 'PORT=8034' in (ROOT/'scripts/launch_phase34.py').read_text()
    assert 'launch_phase34.py' in (ROOT/'START_AGRIORBIT_WINDOWS.cmd').read_text()
    assert c.get('/assets/leaf-cursor.js').status_code==200
    assert c.get('/assets/drop-sfx.js').status_code==200
    assert 'no-store' in c.get('/assets/leaf-cursor.js').headers.get('cache-control','')

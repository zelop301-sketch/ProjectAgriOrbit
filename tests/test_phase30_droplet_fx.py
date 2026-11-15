from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'

def test_click_splash_is_real_site_module():
    c=TestClient(app)
    assert c.get('/assets/click-drop-fx.js').status_code==200
    assert 'no-store' in c.get('/assets/click-drop-fx.js').headers.get('cache-control','')
    html=(WEB/'index.html').read_text()
    assert '/assets/click-drop-fx.js?v=phase34-botolan-evidence-decisions-3.4.0' in html
    assert 'id="agri-drop-fx-toggle"' in html
    assert 'SPLASH FX ON' in html

def test_click_animation_is_bounded_and_accessible():
    src=(WEB/'click-drop-fx.js').read_text()
    css=(WEB/'styles.css').read_text()
    for token in ['MAX_IMPACTS = 10', 'MIN_GAP_MS = 90', 'capture:true', "event.pointerType !== 'mouse'", 'event.button !== 0', 'agri-droplet-spark', 'agri-droplet-ring', 'window.setTimeout', 'document.hidden']:
        assert token in src
    assert 'requestAnimationFrame' not in src
    assert '.agri-droplet-layer' in css
    assert 'pointer-events:none' in css
    assert '@keyframes agri31-ring' in css
    assert '(prefers-reduced-motion:reduce)' in css

def test_independent_sound_and_other_animations_preserved():
    assert 'AudioContext' in (WEB/'drop-sfx.js').read_text()
    assert 'emitWind' in (WEB/'leaf-cursor.js').read_text()
    assert 'agriInitNavigationMotion' in (WEB/'app.js').read_text()
    c=TestClient(app)
    assert c.get('/api/health').json()['build']=='phase34-botolan-evidence-decisions-3.4.0'
    assert c.get('/api/health').json()['recommended_port']==8034
    assert 'PORT=8034' in (ROOT/'scripts/launch_phase34.py').read_text()

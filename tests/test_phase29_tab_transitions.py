from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
ROOT=Path(__file__).resolve().parents[1]

def test_phase29_nav_animation_bounded_and_accessible():
    html=(ROOT/'web/index.html').read_text()
    js=(ROOT/'web/app.js').read_text()
    css=(ROOT/'web/styles.css').read_text()
    for item in ('command','overview','farm','rotations','rover','evidence','guidelines','hazards'):
        assert html.count(f'data-view="{item}"')==2
    assert 'agriInitNavigationMotion()' in js
    assert 'if (!changed && agriNavigationReady) return' in js
    assert 'agriScheduleIndicators()' in js
    assert 'window.AgriOrbitCommand?.onView(view)' in js
    assert 'window.AgriOrbitMission?.onView(view)' in js
    assert 'agri-view-entering' in js
    assert '.view.active.agri-view-entering' in css
    assert 'prefers-reduced-motion:reduce' in css
    assert '.agri-mobile-rail' in css
    assert '.agri-nav-rail' in css
    assert '@keyframes agri-page-arrive' in css

def test_phase29_build_server_and_launchers():
    client=TestClient(app)
    health=client.get('/api/health').json()
    assert health['build']=='phase34-botolan-evidence-decisions-3.4.0'
    assert health['recommended_port']==8034
    assert 'phase34-botolan-evidence-decisions-3.4.0' in client.get('/').text
    assert client.get('/assets/app.js').status_code==200
    assert 'no-store' in client.get('/assets/styles.css').headers['cache-control']
    assert 'PORT=8034' in (ROOT/'scripts/launch_phase34.py').read_text()
    for ext in ('cmd','bat'):
        launcher=(ROOT/f'START_AGRIORBIT_WINDOWS.{ext}').read_text()
        assert '8034' in launcher and 'launch_phase34.py' in launcher

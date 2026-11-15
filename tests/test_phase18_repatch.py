from fastapi.testclient import TestClient
from app.main import app
from pathlib import Path

client=TestClient(app)

def test_new_version_is_unmistakable():
    response=client.get('/')
    assert response.status_code==200
    assert 'PHASE 34 · BOTOLAN RESEARCH MISSION' in response.text
    assert 'phase34-botolan-evidence-decisions-3.4.0' in response.text
    assert response.headers['X-AgriORBIT-Build']=='phase34-botolan-evidence-decisions-3.4.0'


def test_no_cached_js_css_or_boot_frames():
    for path in ['/', '/assets/styles.css', '/assets/seedling-boot.js', '/assets/boot-frames/seed-07.webp']:
        response=client.get(path)
        assert response.status_code == 200
        assert 'no-store' in response.headers['cache-control']


def test_health_reports_correct_release_and_port():
    data=client.get('/api/health').json()
    assert data['build']=='phase34-botolan-evidence-decisions-3.4.0'
    assert data['recommended_port']==8034
    assert data['boot_duration_seconds']==15


def test_windows_launch_on_dedicated_port():
    root=Path(__file__).resolve().parents[1]
    assert 'PORT=8034' in (root/'scripts/launch_phase34.py').read_text()
    assert 'scripts\\launch_phase34.py' in (root/'START_AGRIORBIT_WINDOWS.cmd').read_text()

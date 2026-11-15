from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

ROOT=Path(__file__).resolve().parents[1]
client=TestClient(app)


def test_phase7_dashboard_and_assets_served():
    home=client.get('/')
    assert home.status_code==200
    assert 'id="view-command"' in home.text
    for asset in ['styles.css','app.js','command-dashboard.js','rover3d.js','mission-farm-clean-v20.jpg']:
        r=client.get('/assets/'+asset)
        assert r.status_code==200, asset
    assert 'phase34-botolan-evidence-decisions-3.4.0' == client.get('/api/health').json()['build']


def test_dashboard_source_labels_in_markup_and_ui_code():
    html=(ROOT/'web/index.html').read_text()
    js=(ROOT/'web/command-dashboard.js').read_text()
    assert 'SIMULATED · NOT SURVEYED' in html
    assert 'NOT ECOSTRESS DATA' in html
    assert 'NOT FETCHED' in html
    assert 'ILLUSTRATIVE SHAPE' in html
    assert 'fetchClimate' in js
    assert "sample?.source_type!=='simulated'" in js


def test_simulated_rover_has_no_actuation():
    d=client.get('/api/mission/simulate?progress=0.45').json()
    assert d['source_type']=='simulated'
    assert d['hardware_connected'] is False
    assert d['autonomy']=='disabled'


def test_viewports_and_controls_are_wired():
    html=(ROOT/'web/index.html').read_text()
    js=(ROOT/'web/command-dashboard.js').read_text()
    for control in ['cmd-run','cmd-progress','cmd-overlay','cmd-weather','cmd-blend','cmd-boundary','cmd-nasa-fetch']:
        assert f'id="{control}"' in html,control
    assert "addEventListener('input'" in js
    assert 'new window.AgriOrbitHologram' in js


def test_windows_launchers_use_folder_relative_paths():
    for name in ['START_AGRIORBIT_WINDOWS.bat','START_AGRIORBIT_WINDOWS.cmd']:
        content=(ROOT/name).read_text()
        assert 'cd /d "%~dp0"' in content
        assert 'launch_phase34.py' in content
        assert 'app.main:app' in (ROOT/'scripts/launch_phase34.py').read_text()

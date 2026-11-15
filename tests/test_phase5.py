from fastapi.testclient import TestClient
from app.main import app
from pathlib import Path

client=TestClient(app)
BASE=Path(__file__).resolve().parents[1]


def test_phase5_contract_does_not_claim_live_rasters_or_autonomy():
    r=client.get('/api/hud/capabilities')
    assert r.status_code==200
    d=r.json()
    assert d['render_engine']=='browser_canvas2d_projected_3d'
    assert d['visualization_layers']['field_thermal']=='synthetic_not_ecostress'
    assert d['integrations']['modis']=='catalog_metadata_only'
    assert d['integrations']['ecostress']=='catalog_metadata_only'
    assert d['integrations']['rover_lidar']=='not_connected'
    assert d['physical_rover_commands_enabled'] is False
    assert d['augmented_reality_registration'] is False
    assert d['realtime_latency_guarantee'] is False


def test_phase5_ui_components_present_and_served():
    html=client.get('/').text
    for node in ('hud-crt','hud-bloom','hud-quality','hud-ar','hud-ar-video',
                 'hud-sun','hud-boundary-preview','hud-trace','hud-scanlines'):
        assert f'id="{node}"' in html
    assert 'Satellite rasters' in html and 'NOT INGESTED' in html
    assert 'Synthetic canopy density' in html
    for js in ('rover3d.js','mission-ui.js','hud5.js'):
        assert client.get('/assets/'+js).status_code==200
    assert 'data-hud-widget="feed"' in html
    assert 'data-hud-widget="trace"' in html


def test_phase5_uses_exact_palette_and_avoids_false_ndvi_labels():
    css=client.get('/assets/styles.css').text
    for color in ('#00F0FF','#00FF66','#FFB700','#FF0055'):
        assert color in css
    rover=client.get('/assets/rover3d.js').text
    assert 'SYNTHETIC' in rover
    assert 'tileColor' in rover
    assert 'this.sunAngle' in rover
    assert 'NO ACTUATOR CONTROL' in rover


def test_phase5_local_launch_alternative_included():
    assert (BASE/'START_AGRIORBIT_WINDOWS.cmd').exists()
    assert (BASE/'START_AGRIORBIT_WINDOWS.bat').exists()
    text=(BASE/'START_AGRIORBIT_WINDOWS.cmd').read_text()
    assert 'cd /d "%~dp0"' in text
    assert '127.0.0.1:8034' in text

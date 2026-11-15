"""Phase 6 executable-client contract; browser motion is verified separately."""
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

ROOT=Path(__file__).resolve().parents[1]
client=TestClient(app)


def test_phase6_has_real_animation_director_controls():
    html=client.get('/').text
    for element in ('holo-cinematic','holo-speed','holo-loop','holo-ambient',
                    'holo-orbit','holo-animation-state','holo-stage','holo-render-fps'):
        assert f'id="{element}"' in html
    assert 'ANIMATED MISSION DIRECTOR' in html
    assert 'No physical rover controls' in html


def test_phase6_animation_pipeline_is_real_javascript_not_a_mockup():
    js=client.get('/assets/rover3d.js').text
    for method in ('drawSatellite()', 'drawWeatherEffects()', 'drawSkyEffects()',
                   'requestAnimationFrame','this.speed','this.loop','this.autoOrbit',
                   'this.onCinematicStage'):
        assert method in js
    assert 'this.roverTransform' in js
    assert 'NO ACTUATOR CONTROL' in js


def test_phase6_scene_data_remains_simulated():
    sim=client.get('/api/mission/simulate?progress=0.35')
    assert sim.status_code==200
    assert sim.json()['source_type']=='simulated'
    caps=client.get('/api/hud/capabilities').json()
    assert caps['physical_rover_commands_enabled'] is False
    assert caps['visualization_layers']['field_thermal']=='synthetic_not_ecostress'


def test_phase6_served_scripts_and_styles():
    for name in ('styles.css','rover3d.js','mission-ui.js','hud5.js'):
        assert client.get('/assets/'+name).status_code==200
    assert client.get('/api/health').json()['build']=='phase34-botolan-evidence-decisions-3.4.0'


def test_phase6_launcher_is_relative_to_extraction_directory():
    for name in ('START_AGRIORBIT_WINDOWS.bat','START_AGRIORBIT_WINDOWS.cmd'):
        text=(ROOT/name).read_text()
        assert 'cd /d "%~dp0"' in text
        assert 'launch_phase34.py' in text
        assert 'app.main:app' in (ROOT/'scripts/launch_phase34.py').read_text()
    assert (ROOT/'RUN_AGRIORBIT_MANUALLY.txt').exists()

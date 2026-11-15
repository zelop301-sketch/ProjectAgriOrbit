"""Phase 8 graphics UI and provenance guardrails."""
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

ROOT = Path(__file__).resolve().parents[1]


def test_ultra_graphics_controls_ship_as_real_ui():
    html = (ROOT/'web/index.html').read_text(encoding='utf-8')
    js = (ROOT/'web/command-dashboard.js').read_text(encoding='utf-8')
    for cid in ('cmd-quality', 'cmd-postfx', 'cmd-sun', 'cmd-render-stats', 'cmd-immersive'):
        assert f'id="{cid}"' in html, cid
        assert cid in js, cid
    for mode in ('ultra', 'high', 'auto', 'eco'):
        assert f'value="{mode}"' in html
    assert 'cmd-fullscreen' in js
    assert "localStorage.setItem('agriorbit-phase32-graphics'" in js


def test_ultra_renderer_is_animated_and_pixel_budgeted():
    s=(ROOT/'web/rover3d.js').read_text(encoding='utf-8')
    for method in ('drawUltraAtmosphere', 'drawUltraRouteGlow', 'drawUltraRoverShadow', 'drawUltraPostFX'):
        assert f'{method}()' in s
    assert 'ultra:2350000' in s
    assert 'requestAnimationFrame' in s
    assert 'this.progress=clamp(this.progress+dt*this.speed/23' in s
    assert 'canvas.getContext(\'2d\'' in s


def test_ultra_still_labels_farm_as_synthetic_not_satellite_raster():
    html=(ROOT/'web/index.html').read_text(encoding='utf-8')
    assert 'SIMULATED · NOT SURVEYED' in html
    assert 'NOT ECOSTRESS DATA' in html
    assert 'Farm-only cinematic field backdrop is illustrative' in html
    assert 'no hardware connection' in html
    assert 'source_type' in (ROOT/'web/command-dashboard.js').read_text()


def test_existing_endpoints_work():
    client=TestClient(app)
    assert client.get('/').status_code==200
    assert client.get('/assets/command-dashboard.js').status_code==200
    assert client.get('/assets/rover3d.js').status_code==200
    assert client.get('/api/health').status_code==200
    d=client.get('/api/mission/simulate?progress=0.25').json()
    assert d['hardware_connected'] is False
    assert d['source_type']=='simulated'

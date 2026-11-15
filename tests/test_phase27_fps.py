from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
ROOT=Path(__file__).resolve().parents[1]
def test_phase27_fast_compositor_assets():
    c=TestClient(app)
    h=c.get('/api/health').json()
    assert h['build']=='phase34-botolan-evidence-decisions-3.4.0'
    assert h['recommended_port']==8034
    assert h['boot_duration_seconds']==15
    assert h['living_core']=='compositor-static-webp-v27'
    assert c.get('/assets/agriorbit-living-core-fast.webp').content[:4]==b'RIFF'
    html=c.get('/').text
    assert 'cal27-fps-core' in html
    assert '/assets/agriorbit-living-core-fast.webp' in html
    assert 'option value="boost"' in html
    assert c.get('/assets/agriorbit-living-core-fast.webp').status_code==200

def test_phase27_faster_animation_does_not_change_timeline():
    css=(ROOT/'web/styles.css').read_text()
    js=(ROOT/'web/seedling-boot.js').read_text()
    assert 'cal27-heartbeat 1.08s' in css
    assert 'cal27-rotate 3.0s' in css
    assert 'cal27-rotate-reverse 4.7s' in css
    assert 'DURATION_MS = 15000' in js
    assert 'requestAnimationFrame' in js
    assert 'agriorbit-living-core-fast.webp' in js
    assert 'agriorbit-living-core.gif?' not in js
    assert 'clock - lastUiPaint >= 100' in js

def test_phase27_render_boost_is_real_not_fake_fps():
    render=(ROOT/'web/rover3d.js').read_text()
    ui=(ROOT/'web/command-dashboard.js').read_text()
    assert 'boost:540000' in render and 'fps100:420000' in render
    assert "this.quality==='boost'?15" in render
    assert "this.quality==='boost'" in render
    assert "(quality==='boost'||quality==='fps100')?false:postFX" in ui
    assert 'this.fps=Math.round(this.frameCount/seconds)' in render

def test_phase27_launcher_correct_build():
    script=(ROOT/'scripts/launch_phase34.py').read_text()
    assert 'PORT=8034' in script
    assert 'phase34-botolan-evidence-decisions-3.4.0' in script
    assert 'phase34-botolan-evidence-decisions-2.5.0' not in script
    for f in ['START_AGRIORBIT_WINDOWS.cmd','START_AGRIORBIT_WINDOWS.bat']:
        assert 'launch_phase34.py' in (ROOT/f).read_text()

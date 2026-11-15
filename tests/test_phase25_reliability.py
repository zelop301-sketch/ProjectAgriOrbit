from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'
client=TestClient(app)

def test_unique_release_port_and_no_stale_assets():
    health=client.get('/api/health').json()
    assert health['build']=='phase34-botolan-evidence-decisions-3.4.0'
    assert health['recommended_port']==8034
    html=client.get('/').text
    assert '/assets/seedling-boot.js?v=phase34-botolan-evidence-decisions-3.4.0' in html
    assert 'PHASE 34 · BOTOLAN RESEARCH MISSION' in html
    assert 'cal25-engine-state' in html
    assert 'no-store' in client.get('/assets/leaf-cursor.js').headers['cache-control']

def test_monotonic_boot_clock_controls_both_bars():
    script=(WEB/'seedling-boot.js').read_text()
    assert 'DURATION_MS = 15000' in script
    assert "mainBar.style.setProperty('transform', scale, 'important')" in script
    assert "bar.style.setProperty('transform', scale, 'important')" in script
    assert "const elapsedSeconds = clamped * 15" in script
    assert 'requestAnimationFrame' in script
    assert 'force-15' in script

def test_cursor_motion_opt_in_and_image_fallback():
    script=(WEB/'leaf-cursor.js').read_text()
    css=(WEB/'styles.css').read_text()
    assert 'any-pointer: fine' in script
    assert 'MOTION_KEY' in script
    assert 'explicitMotion = true' in script
    assert 'agri-leaf-svg' in script
    assert 'agri-orbit-explicit' in css
    assert 'leaf-cursor-visible' in script

def test_adaptive_fps_uses_real_frame_stats_and_view_suspension():
    js=(WEB/'rover3d.js').read_text()
    assert 'drawTerrainCached' in js
    assert 'this.fps=Math.round(this.frameCount/seconds)' in js
    assert 'this.adaptiveScale' in js
    assert 'setTimeout(()=>this.tick(performance.now()),240)' in js
    assert "this.ctx.drawImage(this.terrainCache,0,0)" in js

def test_windows_launcher_and_independent_verification():
    assert 'launch_phase34.py' in (ROOT/'START_AGRIORBIT_WINDOWS.cmd').read_text()
    assert 'launch_phase34.py' in (ROOT/'START_AGRIORBIT_WINDOWS.bat').read_text()
    assert 'PORT=8034' in (ROOT/'scripts/launch_phase34.py').read_text()
    for file in ['VERIFY_PHASE26_CURSOR_OFFLINE.html','VERIFY_PHASE26_LIVING_CORE_OFFLINE.html']:
        assert (ROOT/file).is_file()

"""Phase 17: visual elapsed time is separate from readiness and uses one clock."""
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_five_loading_milestones_and_semantics():
    html = client.get('/').text
    for marker in ('data-cal-stage="0"','data-cal-stage="1"','data-cal-stage="2"',
                   'data-cal-stage="3"','data-cal-stage="4"','id="cal-sequence-time"',
                   'id="cal-check-count"','id="cal-progress-fill"',
                   '15-second cinematic growth progress, not system readiness'):
        assert marker in html

def test_synchronized_fifteen_second_visual_clock():
    js = client.get('/assets/seedling-boot.js').text
    for marker in ('DURATION_MS = 15000', 'performance.now()', 'requestAnimationFrame',
                   'const elapsedSeconds = clamped * 15', 'const forceFullMotion',
                   'overlay?.classList.add', "mainMeter.setAttribute('aria-valuenow'",
                   'window.AgriOrbitBootFX?.progress(percent)',
                   "if (bootClock) bootClock.textContent",'milestones[index].classList.toggle'):
        assert marker in js
    assert 'fetch(' not in js and 'WebSocket' not in js

def test_actual_checks_never_drive_cinematic_progress():
    js = client.get('/assets/app.js').text
    check_block = js.split('function calProgress(',1)[1].split('function closeCalibration()',1)[0]
    assert 'cal-progress-fill' not in check_block
    assert 'cal-progress-value' not in check_block
    assert "LOCAL CHECKS · ${passed}/4 PASSED" in js
    assert 'window.AgriOrbitSeedlingBoot?.wait()' in js
    assert 'window.AgriOrbitSeedlingBoot?.skip()' in js
    assert 'NASA POWER has NOT been fetched' in js

def test_cinematic_glow_and_reduced_motion():
    css=client.get('/assets/styles.css').text
    assert '.cal-progress-shell #cal-progress-fill' in css
    assert 'cal17-energy' in css
    assert '@media(prefers-reduced-motion:reduce)' in css

"""Boot animation is real UI code; it must not spoof NASA data or rover checks."""
from fastapi.testclient import TestClient
from app.main import app
from PIL import Image
from io import BytesIO

client=TestClient(app)

def test_boot_uses_new_custom_agriorbit_emblem():
    r=client.get('/assets/agriorbit-emblem.png')
    assert r.status_code==200
    assert r.headers['content-type'].startswith('image/png')
    im=Image.open(BytesIO(r.content))
    assert im.size==(820,820)

def test_boot_markup_has_logo_animation_and_accessible_progress():
    html=client.get('/').text
    for token in ('id="calibration"','/assets/agriorbit-emblem.png', 'id="cal-particle-canvas"',
                  'cal-orbit-shell-outer','cal-orbit-shell-middle','cal-orbit-shell-inner',
                  'id="cal-progress"','aria-valuenow="0"', 'id="cal-enter"','id="cal-retry"',
                  'Only checks 01–04 count toward application readiness','Concept; telemetry simulator only'):
        assert token in html
    assert '/assets/boot-fx.js' in html

def test_boot_script_only_renders_decorative_effects():
    script=client.get('/assets/boot-fx.js').text
    assert 'requestAnimationFrame' in script
    assert 'prefers-reduced-motion' in script
    assert 'document.hidden' in script
    assert 'AgriOrbitBootFX' in script
    assert 'fetch(' not in script
    assert 'WebSocket' not in script

def test_existing_checks_are_wired_to_animation_lifecycle():
    js=client.get('/assets/app.js').text
    assert "window.AgriOrbitBootFX?.progress(pct)" not in js
    assert "window.AgriOrbitBootFX?.progress(percent)" in client.get('/assets/seedling-boot.js').text
    assert "window.AgriOrbitBootFX?.start()" in js
    assert "window.AgriOrbitBootFX?.stop()" in js
    assert 'startupChecks()' in js
    assert 'NASA POWER has NOT been fetched' in js

def test_boot_visuals_respect_reduced_motion():
    css=client.get('/assets/styles.css').text
    assert '.cal-orbital-stage' in css
    assert '@media(prefers-reduced-motion:reduce)' in css
    assert '.cal-particle-canvas{display:none}' in css

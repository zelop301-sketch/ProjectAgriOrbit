from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "web/index.html").read_text(encoding="utf-8")
JS = (ROOT / "web/drop-sfx.js").read_text(encoding="utf-8")
CSS = (ROOT / "web/styles.css").read_text(encoding="utf-8")


def test_sound_controller_is_served_in_actual_dashboard():
    client = TestClient(app)
    assert client.get("/").status_code == 200
    assert "id=\"agri-drop-sfx-toggle\"" in HTML
    assert "id=\"agri-drop-sfx-toggle-text\"" in HTML
    assert '<script defer src="/assets/drop-sfx.js?v=phase34-botolan-evidence-decisions-3.4.0"></script>' in HTML
    assert client.get('/assets/drop-sfx.js').status_code == 200


def test_water_drop_is_local_and_generated_on_click_only():
    assert 'window.AudioContext || window.webkitAudioContext' in JS
    assert "context.createOscillator()" in JS
    assert 'exponentialRampToValueAtTime' in JS
    assert "document.addEventListener('pointerdown'" in JS
    assert "event.pointerType !== 'mouse'" in JS
    assert 'event.button !== 0' in JS
    assert 'event.isTrusted' in JS
    assert 'localStorage.setItem(PREF' in JS
    assert 'oscillator.stop(' in JS
    assert 'MIN_GAP_MS = 85' in JS
    assert 'requestAnimationFrame' not in JS


def test_sfx_button_and_mobile_safety():
    assert '.drop-sfx-toggle' in CSS
    assert '(pointer:coarse)' in CSS
    assert 'aria-pressed' in JS
    assert 'if (document.hidden' in JS
    assert "enabled = !enabled" in JS
    assert 'ctx.suspend()' in JS


def test_health_build_identity():
    assert 'phase34-botolan-evidence-decisions' in TestClient(app).get('/api/health').json()['build']

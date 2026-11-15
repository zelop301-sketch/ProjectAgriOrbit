from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / 'web/index.html').read_text(encoding='utf-8')
js = (ROOT / 'web/leaf-cursor.js').read_text(encoding='utf-8')
css = (ROOT / 'web/styles.css').read_text(encoding='utf-8')


def test_wind_controls_in_real_dashboard():
    page = TestClient(app).get('/')
    assert page.status_code == 200
    assert 'id="agri-wind-toggle"' in page.text
    assert 'id="agri-wind-toggle-text"' in page.text
    assert 'leaf-cursor.js' in page.text
    assert TestClient(app).get('/assets/leaf-cursor.js').status_code == 200


def test_canvas_wind_ribbons_and_bounded_emission():
    assert 'document.createElement(\'canvas\')' in js
    assert 'windCanvas.id = \'agri-leaf-wind\'' in js
    assert 'quadraticCurveTo' in js
    assert 'createLinearGradient' in js
    assert 'MAX_RIBBONS = 75' in js
    assert 'windMode === \'gust\'' in js
    assert 'speed = Math.min' in js
    assert 'lifetime:' in js
    assert 'windCtx.clearRect' in js
    assert 'pointer-events:none!important' in css


def test_visual_controls_and_safety():
    assert 'agriorbit:official-leaf-wind:v4' in js
    assert 'windToggle.disabled = !shouldUse()' in js
    assert 'windMode === \'off\'' in js
    assert 'if (editing) clearWind()' in js
    assert 'hideOutside' in js
    assert 'visibilitychange' in js
    assert '(prefers-reduced-motion: reduce)' in js
    assert '(any-pointer: fine)' in js
    assert '(pointer:coarse)' in css
    assert 'aria-hidden' in js
    assert 'localStorage.setItem(WIND_KEY' in js

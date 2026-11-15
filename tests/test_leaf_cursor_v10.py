from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
html=(ROOT/'web/index.html').read_text(encoding='utf-8')
js=(ROOT/'web/leaf-cursor.js').read_text(encoding='utf-8')
css=(ROOT/'web/styles.css').read_text(encoding='utf-8')

def test_cursor_script_integrated():
    assert '<script defer src="/assets/leaf-cursor.js?v=phase34-botolan-evidence-decisions-3.4.0"></script>' in html
    assert 'id="agri-cursor-toggle"' in html
    assert 'id="agri-cursor-toggle-text"' in html

def test_three_independently_animated_orbs_and_leaf():
    assert 'leaf-cursor-ring-one' in js
    assert 'leaf-cursor-ring-two' in js
    assert 'leaf-cursor-ring-three' in js
    assert 'agri-leaf-vein-wrap' in js and 'agri-leaf-svg' in js
    assert '@keyframes agri-leaf-orbit' in css
    assert 'animation-direction:reverse' in css

def test_accessibility_touch_motion_and_clicks():
    assert 'prefers-reduced-motion: reduce' in js
    assert '(any-pointer: fine)' in js
    assert '(pointer:coarse)' in css
    assert 'pointer-events:none' in css
    assert 'aria-hidden' in js
    assert 'leaf-cursor-click-pulse' in js
    assert 'agri-leaf-editing' in js
    assert 'localStorage.setItem' in js

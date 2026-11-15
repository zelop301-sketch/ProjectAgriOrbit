from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/'web/index.html').read_text(encoding='utf-8')
css=(ROOT/'web/styles.css').read_text(encoding='utf-8')
js=(ROOT/'web/app.js').read_text(encoding='utf-8')
views=['command','overview','farm','rotations','rover','evidence']
def test_navigation_has_six_both_places():
 for v in views:
  assert len(re.findall(r'data-view="'+v+'"', html))==2
  assert f'id="view-{v}"' in html
def test_accessible_nav_and_quick_tabs():
 assert 'aria-label="Main navigation"' in html
 assert 'aria-label="Mobile quick navigation"' in html
 assert "el.setAttribute('aria-current'" in js
 assert '.nav-v9 .nav-button:focus-visible' in css
 assert '@media(prefers-reduced-motion:reduce)' in css
def test_preserves_layer_hooks():
 for x in ['structural','diagnostic','navigation']:
  assert f'data-cmd-layer="{x}"' in html
  assert f'data-holo-layer="{x}"' in html

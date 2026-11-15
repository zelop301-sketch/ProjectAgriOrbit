from fastapi.testclient import TestClient
from app.main import app
from pathlib import Path
client=TestClient(app)
ROOT=Path(__file__).resolve().parents[1]

def test_main_boot_uses_native_15s_timeline():
  html=client.get('/').text
  css=client.get('/assets/styles.css').text
  script=client.get('/assets/seedling-boot.js').text
  assert 'PHASE 34 — EVIDENCE TO FARMER DECISIONS' in html
  assert 'phase34-botolan-evidence-decisions-3.4.0' in html
  assert '@keyframes agriorbit-true-15s' in css
  assert 'agriorbit-true-15s 15000ms linear 1 both' in css
  assert 'force-15' in script
  assert "mainBar.style.width =" not in script
  assert "bar.style.width =" not in script

def test_standalone_boot_test_served_without_app_javascript():
  r=client.get('/assets/boot-check.html')
  assert r.status_code==200
  assert 'animation:fill 15s linear both' in r.text
  assert '/?calibration-hold=1&amp;force-15=1' in r.text

def test_version_dedicated_port_and_no_cache():
  health=client.get('/api/health').json()
  assert health['build']=='phase34-botolan-evidence-decisions-3.4.0'
  assert health['recommended_port']==8034
  assert 'no-store' in client.get('/').headers['cache-control']
  assert 'no-store' in client.get('/assets/seedling-boot.js').headers['cache-control']

def test_launcher_opens_new_build():
  assert 'PORT=8034' in (ROOT/'scripts'/'launch_phase34.py').read_text()
  assert 'scripts\\launch_phase34.py' in (ROOT/'START_AGRIORBIT_WINDOWS.cmd').read_text()

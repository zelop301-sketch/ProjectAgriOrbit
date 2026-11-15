"""Phase 16 checks: deterministic 15-second seed animation and independent diagnostics."""
from fastapi.testclient import TestClient
from app.main import app
from PIL import Image
from io import BytesIO
client=TestClient(app)

def test_new_logo_replaces_small_previous_emblem():
    response=client.get('/assets/agriorbit-emblem.png')
    assert response.status_code==200
    assert Image.open(BytesIO(response.content)).size==(820,820)

def test_exactly_fifteen_local_seed_frames():
    for i in range(15):
        response=client.get(f'/assets/boot-frames/seed-{i:02d}.webp')
        assert response.status_code==200
        assert Image.open(BytesIO(response.content)).size==(241,405)

def test_reel_in_actual_boot_markup():
    html=client.get('/').text
    for text in ('/assets/seedling-boot.js','id="cal-sprout-image"','id="cal-seed-countdown"',
                 'id="cal-sprout-percent"','id="cal-skip"','id="cal-cinematic-note"',
                 '/assets/agriorbit-emblem.png','Only checks 01–04 count toward application readiness'):
        assert text in html

def test_cinematic_duration_readiness_remains_separate():
    script=client.get('/assets/seedling-boot.js').text
    assert 'DURATION_MS = 15000' in script
    assert 'FRAME_COUNT = 15' in script
    assert 'prefers-reduced-motion' in script
    assert 'performance.now()' in script
    assert 'AgriOrbitSeedlingBoot' in script
    assert 'fetch(' not in script and 'WebSocket' not in script
    main=client.get('/assets/app.js').text
    assert "window.AgriOrbitSeedlingBoot?.start()" in main
    assert "window.AgriOrbitSeedlingBoot?.stop()" in main
    assert "window.AgriOrbitSeedlingBoot?.wait()" in main
    assert "window.AgriOrbitSeedlingBoot?.skip()" in main
    assert "response = await fetch('/api/health'" in main
    assert 'NASA POWER has NOT been fetched' in main

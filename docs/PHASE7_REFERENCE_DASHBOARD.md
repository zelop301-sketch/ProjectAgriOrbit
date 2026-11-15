# Phase 7 — Reference-matched, interactive Mission Control

## User-facing changes

This is the first page of the actual AgriORBIT web app, not a rendered concept picture. It aims to reproduce the supplied screenshot's layout with functional UI: dark aerospace HUD, left navigation, telemetry cards, farm stage, transparent floating rover diagnostics, canopy/thermal/boundary side panels, and lower moisture, climate, soil, irrigation and crop-rotation cards. The original views remain in the sidebar.

## Runtime architecture

- `web/command-dashboard.js` gets a reference to the active farm and comparison state from the existing `web/app.js`, and instantiates a second renderer from `web/rover3d.js`.
- `Hologram(canvas, { transparent: true })` uses the same animated 3D scene as the detailed Agro Sentinel page, with transparent farm tiles so that an illustrative background photograph appears underneath. The generated scene image is *a decorative aid only.*
- The actual 3D scene is drawn by Canvas 2D with synthetic topography, projected crop plots, solar light effects, simulated rover body and wheel motion, waypoints and scanning effects. It is not WebGL and not a surveyed digital twin.
- `GET /api/mission/simulate?progress=...` returns **simulated** rover packets in a provenance-labeled schema. Mission playback and dashboard card updates follow this API and are not physical control commands.
- `POST /api/mission/environment` calculates a **hypothetical exposure index**. Controls may vary weather, irrigation and drainage assumptions. The index is neither weather forecasting nor agronomic advice.
- `POST /api/compare` and `POST /api/assess` provide experimental crop rotation scores and optional source-controlled historical NASA POWER records. The frontend never assigns a NASA label to synthetic data.
- GeoJSON boundary previews display a supplied polygon shape but do **not** align it onto the procedural 3D board. Placeholder geometry is explicitly labeled.

## Test evidence

- Local FastAPI `/api/health` starts and reports Phase 7.
- Existing and new tests: 41 passed.
- Syntax checks: `node --check web/app.js web/rover3d.js web/command-dashboard.js` pass when invoked on each file.
- Headless Chromium was exercised with the HTML/CSS/scripts embedded and API responses supplied by FastAPI TestClient. Both desktop and mobile rendered the 3D Canvas; playback advanced from 0% to 4%, the live-requested **simulated** soil moisture appeared, the hypothetical environment index appeared, and neither run produced JavaScript exceptions.
- This runtime blocks ordinary Chromium URL navigation, so a full browser-to-live-Uvicorn network integration test on Windows remains outstanding.

## Deployment

Use `START_AGRIORBIT_WINDOWS.cmd` from within the extracted folder. See `README.md` for commands if Windows cannot locate the launcher or Python.

## Known limitations

1. The center-stage photographic illustration is not a live farm camera, NASA raster, or surveyed field.
2. The rover is conceptual. No hardware is connected; all its simulated readings, scan beams, waypoints, NDVI proxy and LiDAR layer are synthetic.
3. The NASA POWER integration retrieves historical point climate when explicitly requested and internet access permits; it does not make MODIS, Landsat, or ECOSTRESS rasters automatically appear.
4. Crop scenario scores are illustrative and unvalidated; do not make planting, irrigation, or safety decisions from them.
5. Real-time measurement pipelines, calibrated sensors and authenticated autonomy would require dedicated hardware, validation, secured commands and georeferenced data.

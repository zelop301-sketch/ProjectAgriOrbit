# AgriORBIT NASA — Phase 5 HUD: Architecture, Source Boundaries & Demonstration

## Design objective

Make complex field context easy to inspect while preserving source truth. This is a research-prototype **visualization layer**, not a certified instrument, validated predictive model, true holographic projection, or autonomous robot controller.

## Architecture

- `web/index.html`: mission lab layout, HUD controls, simulated solar-angle slider, evidence/sensor cards, field and rover canvas, local camera-scouter dialog and provenance statements.
- `web/styles.css`: high contrast mission theme, exact palette Cyan `#00F0FF`, Emerald `#00FF66`, Amber `#FFB700`, Crimson `#FF0055`; scanline effect, light text glow, responsive controls, reduced-motion protections.
- `web/rover3d.js`: dependency-free CPU-projected 3D `Canvas2D` mesh. Thermal, canopy, illumination and shadows are **procedural artwork**, not GPU GLSL shaders or image-derived quantitative maps. Orbit/zoom/route playback still work. Eco render mode reduces mesh density and DPR.
- `web/mission-ui.js`: fetches existing FastAPI demonstration telemetry and experimental environment scenarios; passes source-tagged sample objects to Phase 5 trend chart, preserving the existing provenance labels.
- `web/hud5.js`: effects/preferences, local storage, dock order (keyboard-friendly up/down buttons), trace drawing, normalized polygon preview, and opt-in camera lifecycle. The frontend does **not** transmit camera frames.
- `app/hud_contract.py`: exhaustive capability truth table, exposed through `/api/hud/capabilities` in `app/main.py`.

## What does NOT exist yet

| Requested specification | Current implementation | Requirements before honest field claim |
|---|---|---|
| ECOSTRESS thermal overlays | Synthetic color gradient; metadata lookup only | Geolocated raster retrieval, quality flags, pixel units, overpass time, correct projection and coverage |
| MODIS / Landsat vegetation health | Synthetic canopy artwork | Product selection, cloud masking, NDVI/QA computation or verified surface reflectance, parcel-scale QA |
| Solar panel efficiency | Historical/simulated solar assist telemetry; UI shows hypothetical sun angle | Verified panel model, geometry, measured irradiance and instrument validation |
| Microclimatic winds / shadows | Pure visual effects | Local terrain/canopy geometry, weather input, verified physics, time zone/solar geometry |
| Rover LIDAR / motor temperatures | Simulator API; 8×8 illustrative grid | Calibrated connected sensors, timestamp/quality checks and hardware permissions |
| 3D field boundaries / point clouds | User GeoJSON preview + independently procedural 3D mesh | Georeferencing, DEM, coordinate transforms, survey/RTK validation and sensor point-cloud ingestion |
| AR field tracking | Local camera with stationary decorative markers | Camera calibration, spatial registration, permissions and measured data associations |
| Dockable panels | Saved card reordering | Free-form drag/drop dock layout if necessary |
| Real-time telemetry / sub-second update | Demo HTTP polling; browser redraw frames | Reliable secured streaming, performance instrumentation and explicit latency budgets |

## Functional verification

Phase 5 added tests for the capability contract, markup, visual source labels and launch fallback; **31 automated tests passed** in the build environment. The UI was evaluated with Chromium using the complete frontend and **mocked API responses** via an in-memory HTML harness, avoiding network access. It rendered on 1520 px desktop and 390 px mobile without JavaScript exceptions. Settings, scenario overlays, the 3D canvas, card reorder and camera fallback were exercised. Camera access was unavailable in this container, so we verified the safe fallback, not a physical camera image.

For Windows, run `py -m pytest -q` within the extracted project folder to repeat backend/static tests. To validate the complete live system, load real historical NASA POWER data on the farm-profile workflow and verify provider, time coverage, retrieval timestamp and units before claiming any data-derived conclusions.

## Judge-facing demonstration: 45 seconds

1. From the calibration screen, show system startup readiness while noting the rover is not connected and NASA POWER has not been fetched automatically.
2. In Mission Control, retrieve real NASA POWER climate and inspect source/date/unit metadata.
3. Compare A/B/C crop rotations using transparent assumptions, gaps and rainfall-history screening.
4. Open Agro Sentinel. Switch thermal ↔ health ↔ canopy visual layers, adjust the synthetic sun angle and change the 3D rover layer. Explain each is conceptual until satellite rasters and instrument data are available.
5. Play the waypoint route, inspect `SIMULATED` status, and show the telemetry trace. Do not describe it as live rover navigation or automated agronomy.
6. Optionally open the camera-scout overlay locally. The demo markers are not tracked or tied to a specific field position.

**Safety:** Commands are never sent to real actuators. Do not deploy rover autonomy without independent hardware verification, geofence, collision detection, E-stop and direct human authorization.

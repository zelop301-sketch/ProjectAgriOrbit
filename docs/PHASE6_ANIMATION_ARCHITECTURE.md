# Phase 6 — Animated Mission Architecture

## What is actually running

The site serves `web/index.html` from the existing FastAPI backend. The Agro Sentinel page runs a **Canvas2D projected 3D renderer** in `web/rover3d.js` using `requestAnimationFrame`, with no video playback, no static imagery pretending to be a simulation, and no third-party JavaScript CDN. On every frame, the renderer projects procedural farm tiles, canopy stems, a schematic rover model, and a route into 2D. This is a lightweight projected 3D *visualization*, not a physically accurate CAD renderer.

The new **Animated Mission Director** in `web/index.html` and `web/mission-ui.js` provides:

- **Play cinematic tour**: replays a simulated 4-stage route, automatically selecting structural, synthetic LIDAR, diagnostic, then LIDAR presentation layers.
- **Speed 0.5×, 1×, 2×, 3×** and **loop** settings for simulated rover position.
- **Ambient animation switch**: optionally pauses moving scan markers, wind, water-like pulses, and satellite beam. Browser reduced-motion preference starts with ambient effects off; explicit user controls can enable them.
- **Auto-orbit**: gently rotates the visualization camera. Dragging the canvas cancels auto-orbit.
- **On-screen FPS**: observes the browser's actual drawn frame cadence, not guaranteed sub-second telemetry delivery.

Animations are computed using time deltas and logical route progression; rover body proxy solids rotate with the route tangent, wheel spokes spin, waypoint scan rings pulse, and an *illustrative* satellite beam sweeps the field. Rain streaks and dust particles change with the existing hypothetical weather control. None of these implies orbital accuracy, real soil measurements, GNSS, LiDAR, field survey, remote sensing pixels, actuator motion, or a connected machine.

## Sources and safety

The rover telemetric response comes from `GET /api/mission/simulate`; the underlying endpoint is deterministic **synthetic demonstration data**. The UI polls as route progress changes. WebSocket ingestion and motor commands are NOT built. Farm tile colors, wind, water pulses, satellite scan, and weather are all designed visualizations. They do not represent NASA ECOSTRESS/MODIS/Landsat raster measurements. The only implemented live data route is user-triggered historical NASA POWER point data; provenance and limitations remain visible.

## Performance and testing

- The renderer caps redraw rate using the existing Auto / High / Eco quality choice. Rendering pauses when its canvas has no layout rectangles or the page is hidden.
- No sustained FPS or CPU performance guarantee is claimed; test on the actual presentation laptop.
- Python/FastAPI tests exercise endpoints and HTML contracts. Browser UI was tested in desktop and mobile Chromium using in-page mocked JSON responses because direct localhost/file navigation was blocked in the test environment. This validates interactive JavaScript and rendering with mock data, **not live NASA retrieval or Windows deployment**.
- Generated GIF is a capture of frames from the running Canvas renderer in that browser harness. It is not a video of physical hardware.

## Location of integration code

| File | Responsibility |
|---|---|
| `web/rover3d.js` | Frame timer, 3D projection, satellite, rover and environmental animation |
| `web/mission-ui.js` | Playback controls, cinematic sequence, simulated telemetry coordination |
| `web/index.html` | Holographic scene viewport and animation director controls |
| `web/styles.css` | Responsive animation deck and high-contrast HUD |
| `app/mission.py` | Backend synthetic rover telemetry generator |
| `app/environment.py` | Hypothetical farm stress-index engine |

## Competition evidence boundary

Label images and demos as **“Agro Sentinel digital-twin concept — simulated telemetry, unsurveyed geometry”**. Do not quote the illustrated color grid as verified NDVI, yield, water balance, or thermal observations. Keep project assessment centered on crop-rotation scenarios and traceable NASA POWER observations.

# Phase 32 measured browser performance — not a guarantee

The application is a projected-3D Canvas2D renderer. This phase provides an adaptive preset **targeting 100 FPS**, not a verified 100-FPS output on all devices. It does **not** bypass the display refresh rate or the browser's `requestAnimationFrame` scheduling.

## Isolated local test (headless Chromium, 1200 × 575 Canvas, 1× device scale)

| Mode | Actual rendered FPS | Mean recent JavaScript draw time | Approx. Canvas megapixels |
|---|---:|---:|---:|
| Ultra | 30 | ~1.9 ms | 0.69 MP |
| Earlier FPS Boost | 60 | ~0.8 ms | 0.54 MP |
| **100 FPS Target** | **60** | **~0.4 ms** | **0.42 MP** |

The browser test appeared limited to about 60 render opportunities/s. This is *not* a 100-FPS result. Draw CPU ms is a code-side measure, not end-to-end GPU rendering latency.

## Whole dashboard offline test

The responsive dashboard correctly loaded the new preset, rendered the 3D scene, changed Ultra / 100 FPS Target modes, and preserved the droplet splash. Full dashboard rates in this headless environment varied between approximately 21–44 FPS with background UI effects and test harness overhead. No JavaScript exceptions were observed. No live NASA/PHIVOLCS fetch was performed.

## Test on Windows

1. Extract the full Phase 32 folder.
2. Double-click `VERIFY_PHASE32_REAL_FPS_OFFLINE.html` to measure isolated local rendering without Python.
3. Switch between the three render modes, keeping the same window size.
4. Launch the full app on port 8032 and read `ACTUAL FPS` in Mission Control for a realistic combined UI measurement.
5. For true 100-FPS presentation, a >100 Hz display, compatible browser/GPU hardware and sufficiently light scene are required. Even then 100 cannot be promised.

The FASTAPI scientific data pipeline is unchanged. No simulated instrument values are represented as measured observations.

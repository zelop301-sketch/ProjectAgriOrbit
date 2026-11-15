# Phase 26 — Living AI Core Calibration Patch

## Actual code changes

- `web/index.html`: new living-core visual layers in the real calibration overlay, including the pulse GIF, glowing aura rotors and two heartbeat shockwaves.
- `web/styles.css`: compositor-friendly transformations and opacity animations, responsive sizing and reduced-motion support.
- `web/seedling-boot.js`: retains the one 15,000 ms clock for both bars, the seedling, and phase milestones; updates the core phase label and refreshes the original animated core on replay.
- `web/agriorbit-living-core.gif`: the **user-selected original animated emblem** from the chat (12 frames, 140 ms each, loops for the duration of boot).
- `web/agriorbit-boot-storyboard-15s.gif`: 15-second user-selected visual storyboard, retained as an optional reference asset. The running app uses native text, progress and controls instead of baking the storyboard labels into a video.
- `app/main.py` and `scripts/launch_phase26.py`: new build `phase26-living-ai-core-2.6.0` with dedicated Windows port 8026 and cache protection.
- `VERIFY_PHASE26_LIVING_CORE_OFFLINE.html`: actual app layout with explicitly mocked API responses for testing without network.

## Safety and scientific labeling

The living core is a cinematic visual, **not an operating AI model, sensor measurement, NASA sync confirmation or actual calibration**. The four local boot checks are unchanged and independent. No physical rover controls, PHIVOLCS permissions or NASA observations are certified by this animation.

## Timing and accessibility

15,000 ms is an **intro duration**, not a data-retrieval SLA. Real readiness checks can complete earlier or later. Skip, replay, reduce-motion behavior and the `?force-15=1` demonstration override remain available. FPS varies by hardware and browser.

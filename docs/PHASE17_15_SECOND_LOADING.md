# Phase 17 — Synchronized 15-second cinematic loading

## Intended behavior

The main loading bar and the seedling growth bar derive from one `performance.now()` timeline in `web/seedling-boot.js`. The normal-motion visual animation takes 15,000 ms, and increments according to actual elapsed time rather than fixed cosmetic jumps.

- 00:00–00:03: ORBIT
- 00:03–00:06: GERMINATE
- 00:06–00:09: EMERGE
- 00:09–00:12: UNFURL
- 00:12–00:15: COMPLETE

Both bars, the label, percent, seedling image, decorative boot clock, and elapsed/remaining counters remain synchronized. The animation may have fewer frames when the browser is backgrounded or heavily loaded; elapsed-time completion remains anchored to the clock. A reduced-motion preference immediately completes the decorative sequence.

## Readiness and honesty

The four startup checks remain real (interface, farm profile, FastAPI health, and initial crop-comparison API). Their progress is shown only in the separate diagnostic list and the `LOCAL CHECKS X/4 PASSED` badge. The cinematic bar must never be described as readiness, a NASA sync, a rover calibration, or scientifically verified crop information.

A normal, healthy boot transitions into Mission Control after both tasks finish. `Skip intro` skips the visual delay without passing an unsuccessful check. `?calibration-hold=1` prevents auto transition for presentation rehearsals. `Retry checks` reruns both processes.

## Tests and preview

Run `py -m pytest -q` from the project folder. Phase 17 passed 92 Python tests and JavaScript syntax checks in the build environment. The visible boot interface was checked in offline Chromium at 1440 × 900 and 390 × 844; full live-origin browser navigation was blocked in the build environment, so final Windows startup remains to be verified.

Captured renderer samples are in `phase17_loading_*`; the six-keyframe GIF is a preview from the actual browser-rendered interface, not an independently generated mockup.

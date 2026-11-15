# Phase 16 — 15-second seedling calibration implementation

## Purpose
A decorative seedling-growth sequence plays **inside** the actual AgriORBIT startup overlay, using the new AI-generated AgriORBIT emblem (the previously supplied image has been replaced). The sequence is **not a NASA dataset, a soil measurement, a rover calibration, or a health certification**.

## Implementation
- `web/seedling-boot.js` controls a 15,000 ms animation from `performance.now()`, progressing through 15 local WebP images sourced from the requested generated GIF, one image per second. Local asset preloading helps avoid image flicker; each frame is the original 241 × 405 visual.
- `web/index.html` adds a separate cinematic growth reel, countdown, growth bar, and Skip button alongside the existing orbital HUD, while maintaining the separate actual-check progressbar and diagnostic status list.
- `web/app.js` launches the cinematic and the four checks independently, waits for both to finish, then transitions to Mission Control **only if local checks pass**. Failures remain on screen for retry or explicit limited-mode entry. `?calibration-hold=1` disables automatic transition.
- Reduced-motion preferences skip the 15-second wait and display the final seedling state; no autoplay audio. Controls remain keyboard accessible.
- `web/styles.css` adds mobile and desktop layout and avoids horizontal overflow.

## Genuine readiness checks, unchanged
1. Local interface initialized.
2. Farm context coordinates present.
3. `/api/health` responds correctly.
4. Initial crop-rotation comparison returns three scenarios.

The startup **does not** fetch or verify NASA POWER data, validated crop suitability, physical rover sensors, or satellite imagery. The NASA Guidelines tab remains a team self-audit, not a submission approval.

## Verification
- 88 Python regression tests passed in the build environment.
- JavaScript syntax verified via `node --check`.
- Browser controller checked for ~1s advancement, completion on skip, reset on replay, and reduced-motion instant completion with local HTML in Chromium.
- The layout was visually rendered in desktop and mobile Chromium via a static offline preview assembled from the exact project markup, CSS and local frame files. Full navigation to the running local FastAPI application was blocked by the execution environment and requires the user's Windows verification.

## Asset credit
The newly requested emblem and seedling frames are AI-generated visuals; include this fact in any formal source-credit register. They are not official NASA branding. Review NASA guidelines and permissions independently before any official competition submission.

# Phase 10 — Animated Leaf Cursor: Implementation Notes

The custom cursor runs in `web/leaf-cursor.js` after the current `web/app.js`, `web/mission-ui.js`, and dashboard scripts. The effect is a decorative HTML/SVG overlay added to the DOM only when `(hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)` is satisfied.

### Rendering
- Main cursor is anchored to `pointermove` coordinates without easing, preserving click-target accuracy.
- Five simple CSS-glowing trail dots interpolate independently using `requestAnimationFrame` and `translate3d`.
- The SVG leaf is painted with a green linear gradient, a stroked edge and visible veins.
- Three circular orbits use CSS animation durations of 2.25s, 1.52s (counter-rotating) and 3.6s, with accelerated hover timings.
- The effect uses CSS only; no external image, Three.js import or backend dependency.

### Accessibility and user control
- Decorative nodes are `aria-hidden`, `pointer-events:none` and cannot intercept clicks or keyboard input.
- Touch and reduced-motion configurations leave the default cursor intact.
- The toggle is an ordinary accessible button with `aria-pressed` and a descriptive label. Browser storage remembers the preference.
- Text inputs and contenteditable surfaces use a native text-selection caret.
- Cursor motion is not transmitted or logged by the application.

### Limitations
CSS glows/animation complexity are purely presentation effects, not holography or sensor visualization. Browser rendering performance varies by machine. Existing farm data provenance and rover simulation disclaimers remain unchanged.

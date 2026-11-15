# Phase 11 — Wind Leaf Cursor Engineering Notes

## Architecture

The leaf cursor is owned by `web/leaf-cursor.js`, loaded after the main AgriMind UI. It generates an inline SVG leaf, three CSS-animated orb rings, five trailing particles, and an optional high-z-index, pointer-transparent 2D canvas (`#agri-leaf-wind`). All layers are visual-only.

For every pointer displacement, the emission routine uses `dx`, `dy`, `dt`, and computed speed. It rejects small movements, discontinuous jumps, long idle gaps, and emission intervals under 15 ms. It emits 1–3 curved ribbons according to Breeze/Gust intensity. The ribbon direction points behind the mouse's travel vector. Each ribbon ages out in ~450–750 ms, using a Bézier path, a three-stop luminous color gradient, and a small highlight mote. A maximum of 75 live ribbons limits memory and rendering work.

The canvas is scaled to device pixel ratio capped at 1.5. Its drawing loop is linked to the existing leaf animation frame. When there are no live ribbons, the canvas is not continuously cleared, avoiding unnecessary work when the pointer is stationary.

## Runtime controls

- Local keys: `agriorbit:leaf-cursor:v1` and `agriorbit:leaf-wind:v1`.
- Leaf FX: global effect on/off (existing feature).
- WIND: Breeze → Gust → Off → Breeze. Wind is disabled when Leaf FX is off.
- `matchMedia('(hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)')` checks hardware capability and reduced-motion preferences.
- Cursor and canvas are `pointer-events:none`. The native text caret remains visible over editable elements. Hidden tabs and pointer exits clear wind.

## Scope and claims

The wind trails do **not** use satellite weather, real-time wind sensors, or NASA data. They are decorative pointer effects. The underlying farming decision-support workflow remains experimental and should retain provenance labels.

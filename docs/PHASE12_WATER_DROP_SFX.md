# Phase 12 — Water Drop SFX Architecture

- Entry point `web/drop-sfx.js` runs as deferred script; the sound button is independent of the leaf FX controller.
- Trusted primary mouse `pointerdown` starts a local `AudioContext` after the browser allows playback from a user gesture.
- Two oscillator voices with decreasing pitch and exponential gain envelopes imitate a water droplet. They finish after approximately 0.23 seconds, stop, and disconnect their nodes.
- Button `#agri-drop-sfx-toggle` stores enabled state in `agriorbit:water-drop-sfx:v1` localStorage (with a storage-availability fallback).
- Only primary mouse interactions produce sound, not touch, keyboard, right-click, background pages or autoplay.
- Uses no remote audio assets, no microphone and no network telemetry.
- Missing Web Audio silently disables the optional sound feature.
- Limitations: synthesized/plop-style aesthetic, not a hydrophone recording or real field-water sensor. Final loudness depends on browser and OS volume.

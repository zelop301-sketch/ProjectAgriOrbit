# Phase 21 Change Log

Starting code: Phase 20 Clean Farm Background.

- Added `app/science_core.py`: source-gated scenario screening and user-reviewed crop requirement rules, never a yield forecast.
- Added `app/validation.py`: observed daily gauge pairs compared with server-obtained POWER daily values.
- Added `app/water_balance.py`: audited gross-precipitation water budget using user-provided inputs.
- Added `scripts/hls_field_ndvi.py`: optional 30 m HLS GeoTIFF Fmask QA and NDVI extraction from Earthdata-downloaded co-registered inputs.
- Added HLS L30/S30 metadata catalog search through NASA CMR (raster download still requires user-authenticated Earthdata access).
- Added `app/evidence_store.py`: opt-in SQLite WAL report snapshots with SHA-256 hashes.
- Added `web/science-ui.js`, science panels in `web/index.html`, and corresponding CSS in `web/styles.css`.
- Added PostGIS sample schema and science QA/methods/scalability documentation.
- Revised dedicated Windows launcher to **8021**, build ID `phase21-scientific-core-2.1.0` and cache-busted assets.
- Preserved clean farm panorama, Agro Sentinel simulation, NASA Guidelines, and true 15-second seedling calibration.
- 122 passing automated tests, plus offline desktop/mobile Chromium module checks. Live NASA requests and actual Windows installation not verified here.

Synthetic fixtures, illustrative environmental layers, user-submitted raster metadata, and rover telemetry must never be represented as verified NASA or field observations.

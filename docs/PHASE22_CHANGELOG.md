# Phase 22 — release highlights

- Added `PHIVOLCS HAZARDS` as the eighth navigation section (desktop and mobile).
- Added locally imported GeoJSON hazard map overlays; no official government vector assets are bundled.
- Added geometry validity checks, local UTM intersection, area calculations, clipped overlays, map source/edition/permission metadata, and a SHA-256 identifier.
- Added distinct unknown / mapped overlap / no overlap in supplied data states.
- Added optional *server-obtained* NASA POWER historical rainfall context, clearly separated from lahar forecasting.
- Added self-contained **fictional sample geometry** and optional local KML/KMZ polygon conversion tool.
- Added official PHIVOLCS, HazardHunterPH, and vector-permission reference links.
- Dedicated local port **8022** and build identifier `phase22-phivolcs-hazard-2.2.0` to avoid old versions being mistaken for the patch.
- Preserved AgriMind AI crop screening, Phase 21 evidence studio, animated farm/rover, aesthetics, and 15-second startup.

**Not included:** official PHIVOLCS map files, legally verified permissions, real-time warnings, government assessment reports, authenticated PHIVOLCS APIs, crop yield predictions, field hardware control.

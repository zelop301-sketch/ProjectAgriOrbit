# Phase 23 — Real NASA data and Pinatubo map-use rights

## NASA POWER

The `GET /api/phase23/nasa/observations` endpoint requests an entire historical year from the official NASA POWER **Daily Point** API. It uses parameters `T2M`, `PRECTOTCORR` and `ALLSKY_SFC_SW_DWN`, community `AG`, and explicit Local Solar Time (LST). The endpoint does not accept client-supplied "NASA" measurements. It checks coverage, rejects missing-value sentinels, calculates a SHA-256 digest of the original NASA response, and maintains a 24-hour cache. Cached data are labeled `nasa_cached`, new downloads are `nasa_api`. Retrieval failure returns an error, never a fabricated replacement.

Run online from a permitted field's actual coordinates: `py -m scripts.verify_nasa_phase23 --lat 15.289 --lon 120.024 --year 2025 --refresh`. **The supplied coordinates represent an illustrative Botolan-area point, NOT a surveyed farm.** The script saves a source-labeled JSON receipt in `reports/` only if genuine official-API/cached observations exist. It does not include actual NASA records in this release because this build environment could not reach the NASA endpoint. The 2025 complete historical year is used for demonstration (not a 2026 forecast).

NASA POWER gridded data are regional and may contain model/reanalysis components. A SHA-256 digest proves local payload consistency, not a NASA digital signature. Avoid calling the data ground truth, in-field rainfall, live weather, soil moisture, or a lahar forecast. The original daily values preserve missing days, with annual totals withheld if fewer than 95% of precipitation days are valid.

NASA docs: https://power.larc.nasa.gov/docs/services/api/temporal/daily/

## Pinatubo PHIVOLCS map layer

**The software cannot grant PHIVOLCS authorization or verify a user's signed agreement.** DOST-PHIVOLCS controls access and data-use terms. Official maps are viewable, but a SHP/WMS/vector-layer request can require a signed Data User Agreement for government/academic users or MOA for other user types. Refer to the agency's current application guidance and the returned agreement. PHIVOLCS may restrict redistribution even when viewing is permitted.

- Official request portal: https://gisweb.phivolcs.dost.gov.ph/gisweb/geomatics-services-request
- Official volcano hazard maps, including Pinatubo: https://www.phivolcs.dost.gov.ph/volcano-hazard/
- Alternative hazard reference portal: https://hazardhunter.georisk.gov.ph/
- PHIVOLCS public volcanic data policy: https://volcano.phivolcs.dost.gov.ph/user/policy

Phase 23 `POST /api/phase23/phivolcs/permission-review` records **user self-attestation only**. It never returns `official_approval_granted_by_app: true` or `public_distribution_approved: true`. Public republishing requires explicit written rights and external confirmation; the source layers are not bundled and should not be posted publicly through the application. The existing local GeoJSON screening remains a private, indicative map preview, not an official hazard assessment or permission to farm in an at-risk area.

If the PHIVOLCS GIS portal is undergoing maintenance, use official alternative portals or contact the agency. A private data-use declaration is not proof of data authenticity, legend accuracy, current coverage, or grant of rights. The app also cannot issue an official Hazard Assessment Report.

## Safety and reconciliation

NASA historical rainfall and the PHIVOLCS volcanic hazard map are **independent evidence streams**. Their coexistence cannot predict the next lahar, current safety, soil fertility, crop yield, or future water availability. NASA precipitation alone is not a volcanic activity trigger model. Real field decisions require official PHIVOLCS/LGU interpretation, appropriately surveyed field boundaries, and local agronomic evidence.

## Audit endpoints

- `/api/health` → `phase23-permission-nasa-2.3.0`
- `/api/phase23/capabilities`
- `POST /api/phase23/phivolcs/permission-review` (self-reported only)
- `GET /api/phase23/nasa/observations?lat=...&lon=...&year=2025&include_daily=true`
- Existing `/api/hazards/screen` for user-provided GIS polygons (unverified)

No credential secrets or official agency map geometry are embedded in this project.

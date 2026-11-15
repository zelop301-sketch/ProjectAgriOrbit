# AgriORBIT v1.3 — NASA Precision Climate Lab: methods, limits and data contracts

**Competition:** NASA Space Apps 2026, **Field Shift: Adapting Farms with NASA Data**. The challenge calls for NASA Earth observations **plus** local soil information, crop characteristics and farmer priorities. The app is a **decision-support research prototype**, not a validated agricultural prescription or fully autonomous system.

## 1. Source-of-truth hierarchy

1. **NASA POWER daily point API** (`nasa_api`): historical, gridded, variable-dependent data. Download uses T2M (°C), PRECTOTCORR (mm/day) and ALLSKY_SFC_SW_DWN (kWh/m²/day) from the NASA AG community, `time-standard=LST`. The application retains the original request URL, UTC retrieval date, SHA-256 of raw JSON, input coordinates and individual data coverage counts. POWER is not an on-farm rain gauge, soil sensor or local weather station. NASA's data products may include modeled / reanalysis inputs.
2. **NASA cached** (`nasa_cached`): same original NASA payload, with its original retrieval date and warning on fetch failure. *Cached does not mean live.* Raw responses are stored in `.cache/` (excluded from release packages and version control). Atomic write/replacement helps protect against concurrent writes.
3. **Farmer-entered** (`farmer_entered`) soil, coordinates, field area and priorities: the app cannot independently authenticate these values.
4. **Reported field-measured / laboratory**: tagged by the contributor, but not verified or calibrated by the app.
5. **Synthetic demonstration** (`synthetic`): entirely fabricated values for presentation/testing. Distinct gold badge; **never submit these as NASA evidence**.
6. **Rover/thermal/canopy visuals**: simulated concept imagery, never a raster observation or verified measurement.

## 2. Precision benchmark

The new `POST /api/precision/assess` takes only validated farm inputs, a completed target year, a baseline length of 3–10 prior seasons (UI offers 5 or 10), and either `nasa` or explicitly `synthetic` mode. Data is **retrieved server-side**; the browser cannot relabel uploaded numbers as NASA.

For a starting month of June, compare **June–August of the target year** to **June–August in earlier years**. For a November start, the period ending in 2025 is **November 2024 → December 2024 → January 2025**. The benchmark selects preceding seasons ending in prior years, never moves January to a chronologically earlier position.

- Require >= **95% valid rainfall days** in *each month* of each candidate three-month season. This is **AgriORBIT's conservative engineering rule**, not a NASA-endorsed threshold.
- If any month fails, mark that entire season unusable. Incomplete daily precipitation is **never filled with zero**.
- Require the target season and at least **three** usable preceding seasons before showing a rainfall deviation.
- Reference mean = arithmetic mean of precipitation totals from usable *previous* seasons (target excluded).
- Reference standard deviation = sample standard deviation across previous seasons. It is **descriptive**; it is not a confidence interval or a validated drought probability.
- Percent difference = `100 × (target three-month rainfall / prior-season mean − 1)`. Only show when target and adequate reference history are complete and the mean is positive.
- Labels `relatively dry` (<= -20%) and `relatively wet` (>= +20%) are **illustrative descriptive thresholds**; neither is a meteorological drought index.
- Keep `rainfall_anomaly_pct=null` if evidence is insufficient; do not silently fabricate observations.
- This is a **5–10 season comparison**, not a 30-year climate normal; avoid trend or future forecast claims.

**What it does not establish:** root-zone soil moisture, crop water requirement, runoff, evapotranspiration, lahar susceptibility, local cultivar suitability, future yield or price. Never derive field-level NDVI or ECOSTRESS data from the synthetic thermal overlay.

## 3. Existing Rotation Studio remains a screening heuristic

The A/B/C point scores were **not calibrated with plot yields, soil laboratory tests or crop trials**. The old `/api/assess` single-year within-year rainfall adjustment remains available for backward compatibility but is unvalidated. **The new precision benchmark deliberately does not feed its rainfall anomaly directly into these crop suitability scores.** A seasonal rainfall difference is not the same as crop demand or expected yield loss.

To create an agronomically defensible next version, collect reviewed crop tables with cultivar, acceptable soil pH/texture, rooting/planting calendar, water and market constraints, uncertainties and locally verified references. Validate against field trials or extension workers before deployment.

## 4. Field boundary quality

`POST /api/precision/boundary` accepts one closed GeoJSON exterior polygon and the reported farm area. It rejects invalid coordinates, open or nonlocal polygons, and missing values. It uses a **local planar equirectangular approximation**, then flags a >25% mismatch or a farm point outside the polygon's bounding box. This is a sanity check **only**, not a surveyed/legally valid boundary or exact area. Polygon holes, crossing the dateline and cadastral calculations are out of scope.

## 5. Scalability and failure handling

- The NASA data adapter is asynchronous, with a **process-wide semaphore capped at four requests** to prevent a single machine from overwhelming POWER. This prototype should not be deployed with unbounded workers/tenants, or claimed to be a high-availability production service.
- Cached year/coordinate requests expire after 24 hours before refresh attempts; a failed refresh may fall back to explicitly labeled stale NASA cache. Each raw payload has an SHA-256 for provenance. Writes use `os.replace` to avoid torn files.
- Input year range and baseline counts are bounded, and all APIs validate lat/lon. A missing NASA response is reported as a failed year, not replaced with synthetic data.
- **Next production step:** PostgreSQL/PostGIS for farm data, object storage for immutable raw NASA payloads, a bounded request queue and worker for ingestion, authentication and permissions for user farms, instrument calibration certificates, monitoring, and per-user rate limits.
- The browser does not connect directly to physical rover actuators; all rover animation remains a client-side concept.

## 6. Endpoints and smoke tests

```text
GET  /api/health
GET  /api/precision/capabilities
POST /api/precision/assess      {"farm":{"start_month":6},"end_year":2025,"baseline_years":5,"mode":"nasa"}
POST /api/precision/assess      {"farm":{"start_month":11},"end_year":2025,"baseline_years":5,"mode":"synthetic"}
POST /api/precision/boundary    {"geometry":{...GeoJSON Polygon...},"reported_area_ha":1,"farm_latitude":15.28,"farm_longitude":120.02}
```

The real NASA endpoint requires internet access. Network access to NASA could not be independently confirmed in the build environment; the tests use deterministic synthetic cases and controlled payloads. A successful `NASA HISTORICAL` result from a real deployment should be verified by the downloadable hashes/URLs and dates before claiming it in competition materials.

## 7. Authoritative references

- NASA Space Apps Field Shift: https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/
- NASA POWER Daily API: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
- NASA POWER parameter details: https://power.larc.nasa.gov/docs/services/api/projection/
- NASA HLS algorithms, 30-meter harmonized imagery (NOT INGESTED HERE): https://hls.gsfc.nasa.gov/algorithms/
- NASA ECOSTRESS data access (NOT INGESTED HERE): https://ecostress.jpl.nasa.gov/data
- NASA SMAP L4 soil moisture, ~9-km gridded regional context (NOT INGESTED HERE): https://ntrs.nasa.gov/citations/20260007170

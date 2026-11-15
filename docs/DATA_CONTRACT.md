# Data contracts and validation boundary

## `GET /api/climate?lat=15.289&lon=120.024&year=2025&mode=nasa`

Returns source_type=`nasa_api` after a successful fresh fetch, `nasa_cached` when a raw NASA cache entry is used, or 503 on failure without a cache. `mode=synthetic` explicitly returns source_type=`synthetic` for fictional UX-only numbers. The `months[]` values contain `temperature_c`, `precipitation_mm` (sum of valid daily totals), `solar_kwh_m2_day` (daily average), and `complete_days` (all three variables valid). NASA POWER is a gridded point time series, not a plot survey. Annual precipitation sums accepted daily values; records may be incomplete, and completeness should be shown.

## `POST /api/compare`

Submit `Farm` in `app/scoring.py`, with `latitude`, `longitude`, `area_ha`, `texture`, optional `soil_ph` / `organic_matter_pct`, `irrigation`, `current_crop`, `soil_source` and `priorities` (each 0..10). Returns exactly three alternatives A/B/C, per-criterion scores and weights, method, limitations, and missing evidence. The **heuristics are uncalibrated design placeholders** and must be replaced with evidence-based agronomy before real-world use.

### Proxy dimensions

- Water feasibility: base scenario values adjusted down for no/limited irrigation and sandy texture according to transparent prototype assumptions.
- Soil cover: illustrative scenario-level proxy; not an observed percentage or erosion model.
- Rotation diversity: illustrative proxy based on number of distinct crops.
- Affordability: qualitative simplicity proxy, not a cost estimate.
- Practice continuity: illustrative learning/labor complexity proxy.

The farmer's five selected weights are normalized to 100% and the weighted average is rounded. If all five input weights are 0, equal weights are used. **Soil pH and organic matter are preserved for future validation but are not scored now.** Historical NASA data is intentionally not used in scoring; using a historical year as a growing-season forecast would be misleading.

## Source boundaries

- `nasa_api`: genuine response retrieved over HTTPS from NASA POWER; gridded meteorological context.
- `nasa_cached`: genuine response previously retrieved, timestamp kept and current request marked cached.
- `synthetic`: fabricated values for display testing, **never** tagged NASA.
- `farmer_entered`: user-reported soil/farm information, unverified.
- `field_measured` / `laboratory`: user-selected evidence class, **no independent verification** in MVP.
- Rover: UI-only simulated values marked `SIMULATED`, never measurements.

## Privacy and safety

Browser stores farm profile and optional field polygon in localStorage. Avoid inputting unconsented landowner details in shared machines; ask permission before testing on a specific field. No field work should occur in unstable lahar channels, riverbeds or prohibited hazard areas. No recommendations for pesticide or fertilizer dosing are issued.

---

## Phase 2 extension (v0.2)

`POST /api/assess` accepts:

```json
{"farm":{"name":"Pilot","latitude":15.289,"longitude":120.024,"start_month":3},"year":2025,"mode":"nasa","refresh":false}
```

- `mode` is `nasa` or `synthetic`. `nasa` results may be labeled `nasa_api` (API response) or `nasa_cached` (cached raw NASA response with original retrieval time). `synthetic` values always say `synthetic` and have no NASA request URL.
- The backend obtains the climate itself, rather than accepting asserted NASA climate data from the browser.
- The response returns `{climate, comparison, binding_note}`. `comparison.season_context` contains `window`, `months`, `rainfall_mm`, `three_month_annual_mean_mm`, `rainfall_fraction_of_annual_pct`, `ratio_to_equal_3_month_share`, `coverage_pct_by_month`, `usable`, `status`, `notice`, `calendar_grouping_note`.
- `comparison.scenarios[*].climate_water_penalty` is an **experimental** adjustment and `rainfall_stress_test` gives *counterfactual* ±20% penalties (not forecasts). For missing or insufficient data, penalty is zero and mode reverts to `heuristic_only`.
- `climate.raw_payload_sha256` records the canonical JSON SHA-256 digest of the underlying raw climate payload, not a guarantee that an external party validated the data.
- `climate.expected_days` and `data_coverage_pct` show completeness in the selected year.

See `docs/PHASE2_SCIENCE_AND_LIMITATIONS.md` for methodology, data warnings, and non-claims.

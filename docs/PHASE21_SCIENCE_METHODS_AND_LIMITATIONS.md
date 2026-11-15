# Phase 21 — Scientific methods, provenance and evidence gates

## 1. Target decision and limitations

AgriORBIT assists exploration of **three crop-rotation scenarios** around a farmer-reported field. Its role is to expose constraints and tradeoffs rather than issue a planting order. It does NOT estimate crop yields or ROI from NASA POWER. The older 0–100 scores are preserved as legacy prototype UI data only, **not used as scientifically validated screening decisions**.

## 2. Historical NASA POWER benchmark

NASA POWER uses gridded products for regional climate variables, not precise field rain gauges. The daily historical `PRECTOTCORR` parameter is summed across the actual consecutive three-month season; for Nov/Dec starts, the season crosses a calendar year correctly. Each month requires >=95% valid daily precipitation records, with ≥3 eligible prior seasons. Up to 10 previous seasons are compared. No imputation occurs when data are absent.

The Phase 13 benchmark currently reports percentage departure from **previous-season mean**:

`(P_target / mean(P_reference_seasons) - 1) * 100`.

The median and sample standard deviation are provided as context. A 5–10 season mean is NOT a 30-year climate normal, a drought probability, an irrigation need, or forecast; results require local interpretation. Neither negative anomaly nor a rain-gauge mismatch automatically proves crop stress.

## 3. Evidence-based crop screening

Each crop rule is **user-supplied**. It includes optional pH range, allowed textures, minimum irrigation requirement, source URL and review details. Only a rule with a date, named reviewer and HTTPS reference is treated as *reviewed for screening*; the system cannot verify those claims. Unreviewed entries cannot create hard exclusions. A pH conflict with a self-reported laboratory value is flagged as `reported_lab_rule_conflict`; confirm the actual test method, depth, location, date and agronomist interpretation.

The system always returns `decision_ready=false`. No score ranking is used to recommend a farm action. Farmer priorities remain visible in the separate legacy comparison for transparent review, but they cannot override a conflict from reviewed constraints. There is no built-in table of fabricated local pH or crop requirements.

## 4. Gauge validation

A rain-gauge dataset is entered by the user as dates and daily totals. `GET POWER` is server-initiated. Paired comparison requires matching day keys and rejects negative or missing rainfall. With >=5 paired days it computes:

* MAE = mean(abs(POWER - gauge)), in mm/day
* Signed bias = mean(POWER - gauge), in mm/day
* RMSE = sqrt(mean((POWER - gauge)^2)), in mm/day

These are descriptive. A 5-day sample is grossly inadequate for proving site-specific accuracy, and an uncalibrated gauge can be misleading. The gauge's type, siting, rain-screening, calibration method and spatial separation from POWER grid should be documented before interpreting errors.

## 5. Optional HLS cloud-masked NDVI

For HLS v2.0, red and NIR COGs must originate from the same granule, have the same CRS/transform/shape, and be clipped to an actual user-provided field polygon. NDVI = (NIR−red)/(NIR+red) for finite nonnegative, non-nodata values; Fmask bits 1–5 remove cloud, adjacency, shadow, snow and water. This tool returns the number of field pixels, clear coverage and NDVI distribution. Without source authentication the output is `processed_user_supplied_rasters_unverified_source`. 30 m pixels can represent mixed land cover. NDVI is not a soil water reading, yield estimate or nutrient assay.

Access and documentation: https://hls.gsfc.nasa.gov/data-access-and-tools/ ; https://hls.gsfc.nasa.gov/algorithms/

## 6. Water-balance prototype

`ΔS = P + I − ETc − RO − D`. P is **gross rainfall over the same period**, I irrigation, ETc crop evapotranspiration, RO runoff and D drainage, in millimeters. If direct ETc is not supplied, user inputs can estimate `ETc = Kc × ETo × days` with ETo in mm/day. These data are neither fetched nor calculated from NASA by this water-budget endpoint. Storage bounds are informational; excess/deficit outside bounds are **unaccounted**, not automatically measured runoff/drainage or drought stress. Ground validation is essential.

Reference: FAO-56 https://www.fao.org/4/x0490e/x0490e0a.htm

## 7. Local validation agenda (not yet completed)

1. Obtain landowner consent, farm coordinates and actual polygon survey quality.
2. Collect gauge observations alongside NASA POWER history; inspect biases across wet/dry seasons.
3. Gather dated lab soil reports (sample depth, texture, pH, OM, N/P/K, EC where relevant).
4. Obtain DA/municipal agronomist review of actual cultivar requirements and planting calendars.
5. Run historical backtests across multiple growing seasons and compare with real farm outcomes (crop performance and harvests, with confounding factors).
6. Only then explore field-verified irrigation budgets, crop suitability validation, or predictive models. Never test in unstable lahar channels.

## 8. Data categories and source labeling

`nasa_api`, `nasa_cached`: server-retrieved NASA POWER, with retrieval date, period, variable coverage, request URL, raw SHA-256. `synthetic`, `synthetic_rehearsal_not_nasa`: fabricated teaching fixtures, not Earth observations. `farmer_entered`, `field_measured`, `laboratory`: user-asserted local provenance, not authenticated by the server. `processed_user_supplied_rasters_unverified_source`: local HLS-format band processing without Earthdata identity validation. `hypothetical_model`: 3D scene, rover, stress and thermal visualizations. Never combine categories without explicit disclosure.

These safeguards improve traceability, not scientific calibration by themselves.

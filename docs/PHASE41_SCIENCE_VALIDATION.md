# Phase 41 — Original visuals preserved / NASA seasonal science

## Provenance and integrity

This build is based on the uploaded original Phase 34 backup. Every original file under `web/` remains **byte-for-byte identical**; the existing 3D renderer, cinematic boot, cursor, background, visuals and dashboard navigation remain unchanged. The only changed original file is `app/main.py`, to add a separate scientific API and research page. The Phase 34 existing science routes remain. Added scientific page is `/science` and does not replace `/`.

## Scientific methods

Added `app/seasonal_science.py` (independently tested in a prior patch), which requests NASA POWER daily meteorological fields and uses 2015–2024 planting cohorts (plus 2025 padding) to compare the three existing crop sequences under user-entered planting month, durations, and gap. NASA POWER is gridded model/observation-informed climate context, not plot measurement. Request receipt contains URL, time, SHA-256 and coverage/units validation. Network failure does not silently produce synthetic observations. Synthetic mode is explicitly labelled and isolated.

Reference evapotranspiration uses FAO-56 Penman–Monteith and meteorological requirements where units, completeness and physical consistency are sufficient. Actual crop ETc is WITHHELD unless user supplies a complete, documented stage-specific crop-coefficient (Kc) schedule for each crop. ETc is *not* equivalent to applied irrigation or water savings. Rice paddy water demands additionally depend on ponding, land preparation, percolation and seepage; these are not measured here. Uncertainty is represented by historical year-to-year quantiles, not precise farm probabilities or future forecasts.

## Not validated

- No independent successful live NASA API call from the judging computer; must test real NASA mode with internet, inspect response `source_type` and original request receipt.
- No field-calibrated soil water storage, measured irrigation rate, plot rain gauge, locally reviewed crop duration and coefficient table, independent agricultural expert sign-off or farmer/outcome trial.
- Historical quantiles are **not** projected future climate, prediction skill, verified crop yield or recommended planting dates.
- Original Phase 34 optional archive functionality, including historical non-NASA reference links, remains to protect all original features. The **new** Phase 41 science endpoint uses only NASA POWER external meteorology; other farmer entries are labeled assumptions.
- Real browser and Windows startup, and live internet request on the user machine, remain to be checked.

## Running

`py -m pip install -r requirements.txt` then `py START_AGRIORBIT_PHASE41.py` (or substitute `python`). Open original dashboard `http://127.0.0.1:8034/?force-15=1#botolan` or the separate scientific research workspace `http://127.0.0.1:8034/science`.

## Sources

- NASA POWER API: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
- FAO Irrigation and Drainage Paper 56: https://www.fao.org/4/x0490e/x0490e00.htm


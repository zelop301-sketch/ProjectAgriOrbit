# Phase 42 — judge-critical science & demonstration patch

## Provenance of this patch

Built from the **complete Phase 41 ZIP** using its Phase 34 original visual assets. Compared against Phase 41, this patch only modifies:

- `app/seasonal_science.py` (additional historical rainfall-normalization, dry-spell screening, source provenance labels)
- `web/nasa-seasonal-workspace.html` (fix back link; readable side-by-side evidence cards)

New files are `web/science-phase42-ui.js`, `START_AGRIORBIT_PHASE42.py`, this documentation, a short usage guide, and `tests/test_phase42_judge_science.py`.

**All Phase 34 original `web/index.html`, `web/app.js`, `web/styles.css`, the original 3D rover JavaScript, imagery, boot animations, original cursor, and existing features are preserved byte-for-byte.** Phase 41's original Python launcher and legacy modules remain.

## New judge-critical corrections

1. **Navigation:** `/science` back link now points to `/?force-15=1#botolan`, with no embedded space. The JS asset is served by the app's existing `/assets` mount.
2. **Readable evidence:** three side-by-side rotation cards replace the JSON dump. Per-card results include historical total rain, rainfall per occupied crop day, reference ETo, longest <1 mm/day spell, and conditional crop ETc (or **WITHHELD**). User-entered field checks remain visible. Full reproducible JSON is in collapsed receipt and downloadable export.
3. **Different crop durations:** rotation total rainfall is not used by itself as a comparable suitability score. Normalized rainfall and ETo (mm per occupied crop day) are added, with historical P10/median/P90 across the 2015–2024 planting cohorts. These distributions are historical *sample percentiles*, not forecast probabilities or statistical confidence intervals.
4. **Dry-spell convention:** longest run of daily NASA POWER precipitation <1 mm on consecutively occupied crop days. A fallow gap breaks the spell and missing days invalidate the corresponding season. The 1 mm threshold is a screening convention, not a locally validated drought threshold.
5. **Kc source traceability:** crop profiles accept optional source title, publisher and crop variety, expose `USER_SUPPLIED_UNVERIFIED` status, and reject malformed/private/credential-bearing URLs. **A syntactically valid HTTPS link does not verify the research content or local crop applicability**. ETc remains conditional on complete Kc stages and met coverage; the model assumes well-watered standard conditions.
6. **Misleading irrigation claim avoided:** the old `idealized_rain_offset_shortfall_mm` field remains for archival compatibility but is **not displayed** on judge cards. It assumes 100% rainfall effectiveness and must not be interpreted as applied irrigation, real crop deficit, or water saving. Crop-water figures do not include paddy ponding, soil saturation, seepage, percolation, distribution efficiency, runoff, storage or timing.
7. **Failure behavior:** another attempted run clears the previous report first. If live NASA fetch fails, prior synthetic data cannot continue showing under a NASA-selected mode or be exported as if new results.

## Scientific boundaries and what is NOT validated

- No live NASA POWER run was completed in this isolated environment. All browser component tests use explicitly synthetic API fixtures; they are not evidence of real observations. Request a **live NASA** report with internet on your own computer and check `source_type`, date, NASA URL, units, SHA-256 receipt and the crop-window daily completeness.
- NASA POWER daily data are a gridded meteorological estimate, not a measured plot-scale rain gauge, local soil profile, or on-farm irrigation survey.
- Historical planting-cohort percentiles are **not** future predictions, exact uncertainty bounds, confidence intervals or drought probabilities.
- NASA-derived ETo is a FAO-56 daily reference ET estimate with approximated actual vapour pressure from NASA mean RH; independent station validation is not complete.
- Provided crop coefficient schedules are *not* read and checked against their URL content, crop varieties, soil, altitude, growing stage or local management. An expert must review stages and validity.
- ETc when present represents *illustrative standard-condition crop evapotranspiration*, **not** rice field total water use, water withdrawal, irrigation requirement or cost savings.
- No field agronomist review, verified soil data, plot geolocation, farmer testing, crop yield observations, irrigation-delivery measurements or quantified farmer impact have been provided.
- Original optional non-NASA legacy features are retained untouched to protect your dashboard and existing functionality. The **new** Phase 42 climate-analysis endpoint uses NASA POWER for external meteorological data and clearly labels user inputs.

## Reproducibility and quality checks

Run `py -m pytest -q` from the project root. Phase 42 adds tests for corrected back navigation/static asset, normalized crop-window metrics, missing-data withholding, dry-spell gap handling, malformed Kc URLs, unverified provenance and synthetic separation, without deleting existing tests. Browser component check was performed using synthetic API output and injected page resources because isolated Chromium blocks normal HTTP navigation in this environment. Actual browser-to-server navigation on Windows is still to be checked.

### References

- NASA POWER documented API: https://power.larc.nasa.gov/docs/tutorials/service-data-request/api/
- NASA POWER data sources and daily units: https://power.larc.nasa.gov/docs/methodology/data/sources_hydrology/
- FAO-56 crop coefficients, ETc = Kc × ETo: https://www.fao.org/4/X0490E/x0490e0b.htm
- FAO irrigation water needs for rice, including ponding and seepage: https://www.fao.org/4/s2022e/s2022e08.htm

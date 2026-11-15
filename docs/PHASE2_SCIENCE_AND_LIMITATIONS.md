# Phase 2 science and limitations — AgriORBIT NASA

## What is actually observed or entered?

1. **NASA POWER 2025 historical daily-point record:** temperature `T2M` (°C), precipitation `PRECTOTCORR` (mm/day), and all-sky surface solar radiation `ALLSKY_SFC_SW_DWN` (kWh/m²/day). NASA POWER provides gridded meteorological and solar context derived from multiple sources; it is **not a farm rain gauge, surveyed parcel, field soil measurement, or planting forecast**. Only one historic year is implemented.
2. **Farmer-entered information:** site coordinate, field size, soil texture, soil pH (optional), organic matter (optional), irrigation, current crop, priorities and intended example planting month. A `field_measured` or `laboratory` declaration is a label supplied by the user, not third-party verified.
3. **Proposed crop sequences:** repeated current crop; current crop → mung bean; maize → mung bean → sweet potato. They are *candidates for discussion*, not locally approved planting recommendations.
4. **Rover telemetry:** independently generated synthetic measurements for UI demonstration. No real rover is integrated.

## Historical rainfall exposure screen (Phase 2)

The backend fetches 2025 POWER data at the farm's coordinates (or creates explicitly synthetic demo data). `/api/assess` returns both the observed/illustrative climate payload and rotation scores in one server-controlled transaction. Browser clients cannot inject their own `NASA` payload into this route.

For a farmer-selected month `m`, select 3 months starting at `m` and sum 2025 monthly rainfall, `R3`. Let 2025 annual rainfall be `R12`. Compute a *within-year equal-share benchmark* `R12/4`. Define:

```
dry_share = max(0, 1 - (R3 / (R12 / 4)))  # cap at 1
water_penalty = round(24 * dry_share * illustrative_demand_index / 3 * irrigation_factor)

irrigation_factor: none = 1.00; limited = 0.65; reliable = 0.25
illustrative_demand_index: baseline = 3; legume option = 2; diverse = 2.4
```

The nonnegative penalty is subtracted from **only the prototype's water-feasibility dimension**. All other scoring dimensions are unchanged; the existing farmer-selected weights still control aggregate scores. The coefficients, demand indices and original scenario dimensions are **unvalidated design assumptions**, not published agronomic thresholds. Their use is disclosed on-screen and in the export.

**Important:** The comparison is relative to an annual-average 3-month share **within the same historical year**. It is *not* a precipitation climatology, drought index, long-term anomaly, field water balance, crop evapotranspiration model, irrigation prescription, or crop suitability score. A rainy period can also bring erosion and waterlogging risks that the present proxy does not model. No yield, income or fertilizer predictions are made.

When start month is November or December, the cyclic grouping includes January (or January–February) **from that same year**, which occurred earlier, so this is a month-of-year pattern rather than 3 chronologically consecutive months. A clear warning is displayed in these cases. Future work: genuinely contiguous seasons across calendar-year boundaries using 2-year records.

## Quality gates and provenance

- Source labeling: `nasa_api`, `nasa_cached`, or `synthetic`; synthetic mode has no NASA request URL.
- NASA access uses documented daily endpoint; requests include latitude, longitude, year, parameters, AG community, LST time standard and JSON format.
- Missing NASA sentinel values (`-999`) and non-finite values are excluded.
- Three selected months must each have **at least 80% complete daily observations across all requested parameters** for a climate water penalty to be applied; otherwise the score reverts to heuristic only and explains why.
- NASA cached raw response contains a retrieval timestamp; when a live update fails it remains explicitly labeled cached.
- For reproducibility the API provides exact NASA request URL, retrieved UTC time, parameter units, coverage and a SHA-256 hash of the returned raw payload.
- `±20% rainfall` is a transparently counterfactual **stress test**, not a probability, forecast, or actual measured anomaly.

## Agricultural literature: what it supports, and what it does not

- [FAO, *Soil health for paddy rice*, 2021](https://www.fao.org/family-farming/detail/en/c/1637590/) discusses soil health and farmer field school practices in the Philippines; supports considering soil-health constraints, **not** site-specific scores or a Botolan crop suitability judgment.
- [DA-PhilRice / Palayamanan rice technology material](https://www.pinoyrice.com/wp-content/uploads/palayamanan.pdf) describes rice-legume and diversified rotation concepts; supports choosing candidate sequences to explore, **not** the model coefficients or yield changes.
- [NASA POWER daily API documentation](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) supports provenance and data parameter interpretation.

## Missing before responsible farmer use

- Verified location and parcel permission; soil texture, pH, organic matter and nutrient labs; drainage/slope and lahar deposit description.
- Local crop calendars, tolerance ranges, adapted varieties, disease/pest constraints, market and labor considerations, planting date and farmer interviews.
- Local agronomist validation, plus sensitivity and retrospective evaluation across multiple years and independent sites.
- Real farmer usability testing and translations (e.g., Filipino) when appropriate.
- Tests that clearly separate crop-specific water demand and irrigation constraints from past regional rainfall.

**Claim allowed for judges:** "We demonstrate how NASA POWER historical rainfall and farmer priorities can jointly inform transparent *exploratory* rotation comparisons and show where local evidence is missing." 

**Claim not allowed:** "NASA proves these crops will grow here," "our AI predicts yield/profit," "real rover samples were collected," or "the prototype is validated for lahar deposits."

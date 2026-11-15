# Phase 34: Scientific Method and NASA Space Apps Judge Demonstration

**AgriORBIT: From NASA Data to Farmer Decisions — Botolan, Zambales**

## One-sentence mission

Use NASA's gridded precipitation and temperature history as **one evidence layer** to help a Botolan farmer and a local agronomist identify the information they still need before considering crop-rotation changes under El Niño uncertainty.

## Problem and context

DOST-PAGASA announced **very strong El Niño** in the tropical Pacific on November 4, 2026. This creates preparedness concerns for many Philippine farms but does not determine whether an individual field in Botolan has experienced drought. A NASA POWER point is climate context rather than ground rain-gauge or soil-moisture evidence. Tropical cyclones and monsoon rains may still bring significant rainfall.

Official advisory: https://pagasa.dost.gov.ph/press-release/233?page=2

## Scientific reference window

- **Location:** 15.289° N, 120.024° E. Geographical point only, not a mapped farm boundary.
- **2026 target:** January–October 2026, completed months only, daily NASA POWER `PRECTOTCORR` and `T2M`. The existing Phase 33 bounded daily request is reused.
- **Reference period:** 1991–2020 monthly NASA POWER `PRECTOTCORR` and `T2M`. These are selected reference years, **not** an official municipal drought classification or a spatially validated farm climate normal.
- **Monthly rain units:** NASA POWER monthly `PRECTOTCORR` is a **mean daily rate (mm/day)**. The calculation refuses to use the response unless the header confirms mm/day and `T2M` confirms degrees C.
- **Monthly historical coverage:** For each calendar month, at least **24 valid yearly monthly values** out of 30. This gate counts monthly product records and does not verify the underlying historical daily completeness.
- **2026 target daily coverage:** At least **95%** valid daily rainfall values for each month. Missing/nonphysical daily values are excluded by the existing Phase 33 data parser. Coverage percent is shown, not concealed.

### Formula

For calendar month `m`:

```
R_reference_mm(m) = mean(R_1991_mm_day(m), ..., R_2020_mm_day(m)) * days_in_2026(m)
D_m (%)           = 100 * (R_2026_mm(m) / R_reference_mm(m) - 1)
D_Jan-Oct (%)     = 100 * (sum_2026_10months / sum_reference_10months - 1)
```

A month is eligible only with valid target daily coverage, at least 24 historical monthly values, and a positive reference rainfall total. If **any of the ten months** fails, the Jan–Oct departure is null—not an estimated value filled with zeros.

**Note:** 1991–2020 is often used for a standard 30-year reference period, but the Phase 34 product is a *NASA POWER gridded study average* rather than a station-normal calculation with validated daily observational coverage. Do not call it an official plot-level normal.

### What the climate flag does

The app's `BELOW_30Y_REFERENCE` research flag uses a **deliberate, non-clinical −10% demonstrator threshold**. It changes which questions appear about water exposure, and is **not an agronomic suitability threshold, drought index, ENSO attribution, or prediction of a coming planting period**.

## Agronomic screening / traceability

Inputs: farmer-reported irrigation, texture, optional pH, asserted lab provenance, intended planting month and farmer priority. The proposed rotations **Rice → Rice**, **Rice → Mungbean**, **Corn → Mungbean** have no numeric suitability scores. The science engine lists questions about irrigation, soil, verified crop calendars, and missing documentation.

The general need to account for paddy-rice soil saturation, ponding, and losses comes from the **FAO Irrigation Water Needs, section 4.4**, https://www.fao.org/4/s2022e/s2022e08.htm . The app does not calculate a water budget from that generic guidance because effective rainfall, ETo, Kc, soil permeability and water availability are not locally measured.

Users may submit source-linked crop pH/irrigation rules. Their labels are **self-attested and unverified**, even if an arbitrary reviewer name and date are entered. Any mismatch is a candidate question for a field expert, not an automated prohibition or recommendation.

Quality gates distinguish: validated NASA gridded context, measured irrigation, source-attested lab pH, authenticated crop requirements, and measured outcomes. Critical gates never silently pass. No crop planting authorization or yield predictions are issued.

## NASA POWER and PAGASA references

- NASA POWER monthly documentation: https://power.larc.nasa.gov/docs/services/api/temporal/monthly/
- NASA POWER daily documentation: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
- DOST-PAGASA November 4, 2026: https://pagasa.dost.gov.ph/press-release/233?page=2
- NASA Space Apps Field Shift: https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/
- FAO rice water needs: https://www.fao.org/4/s2022e/s2022e08.htm

## Suggested 30-second demo script (single-take, calibrated on your recording device)

**0–5s:** “In Botolan, Zambales, El Niño brings uncertainty to farmers planning crop rotations.” Show Phase 34 hero, not the full 15-second startup.

**5–12s:** “AgriORBIT tests 2026 NASA POWER rainfall against a 1991–2020 historical reference and reports the evidence coverage.” Show live **NASA POWER** only after verifying real retrieval on the team's computer. Otherwise explicitly announce “simulated workflow” and do not claim observed rainfall.

**12–22s:** “Now we change irrigation from reported reliable to limited. Our screening changes the water questions for rice and rotation alternatives—without inventing suitability scores.” Show three candidates and change the select.

**22–30s:** “The evidence report shows source links, missing field data, and agronomist validation needed before a decision. AgriORBIT supports questions, not unverified planting orders.” Show the export and quality gates.

**Critical submission step:** Verify the competition's video/slide limits, originality, team and attribution requirements in the official rules. Differentiate pre-existing Sammium portfolio code from in-hackathon changes. Do not use the synthetic chart as evidence that the 2026 rainfall was below a 30-year reference.

## What is still not done

1. Live 1991–2020 NASA POWER response **not fetched or independently verified** in the build environment; unit and schema checks must be tested against real online responses before a NASA evidence claim.
2. No real soil sample, irrigation measurement, planting calendar or agronomy reviewer has been authenticated.
3. No verified farmer pilot or yield outcome trial, no plot-scale remote sensing validation, and no physical Agro Sentinel rover.
4. No guarantee of 100 FPS; the performance mode is a target only.

These are explicit scientific constraints, not a reason to invent demo results.

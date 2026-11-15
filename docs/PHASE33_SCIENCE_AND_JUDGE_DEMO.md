# Phase 33 • Judge demonstration and scientific method

## What is directly established?

- **PAGASA**: the November 4, 2026 official press statement says a very strong El Niño is present in the tropical Pacific. This is **not** an official declaration that every field in Botolan is experiencing drought. https://pagasa.dost.gov.ph/press-release/233?page=2
- **NASA POWER**: the executable backend requests server-side daily regional climate context for a fixed Botolan reference coordinate. Actual monthly totals and temperature means **appear only after successful NASA retrieval** and quality checks. The present build does **not bundle** a verified NASA API result.
- **Farmer inputs**: irrigation and soil texture are manually declared and **not verified**. The program does not infer soil moisture or nutrition from satellite temperature or precipitation.
- **Crop options**: three research hypotheses with open evidence questions. There is no validated yield model, drought damage prediction or planting-ready crop ranking.

## Data pipeline

1. NASA POWER `PRECTOTCORR`, `T2M`, `ALLSKY_SFC_SW_DWN` daily point data, time standard local solar time (LST).
2. Fetch January–October 2026 explicitly ending **October 31**, not a future/unknown 2026 complete-year record.
3. Retrieve 2021–2025 historical full-year records via the existing cached, server-side NASA POWER pipeline.
4. Verify valid calendar days and physically plausible values using the existing NASA data parser. Require **≥95% monthly rainfall coverage** for each reported month.
5. For each Jan–Oct calendar month, require **≥3 valid reference years**. A monthly reference is the arithmetic mean of available 2021–2025 same-month totals.
6. Jan–Oct comparison = sum of the ten 2026 monthly totals versus sum of the ten reference-month means; withhold the overall departure if **any** of the ten monthly comparisons is missing.
7. Show the raw payload SHA-256, source request URL and retrieval timestamp by year; identify any missing years. Cached NASA readings remain labeled as `nasa_cached`.
8. No scientific crop score is computed from this rainfall difference. Refrain from attribution, water demand/ET estimates, moisture mapping and crop ranking without additional field evidence.

## Suggested 30-second recording

- **0–5s — Local challenge:** “Botolan farmers need to plan crop sequences under El Niño-related climate uncertainty. PAGASA confirms the regional ENSO context, not drought at this field.”
- **5–13s — NASA evidence:** “AgriORBIT compares NASA POWER 2026 rainfall with the same months from five previous years. The quality table and source links show which claims are supported.” *Record this with a successfully verified NASA response, if possible.*
- **13–22s — Farmer adaptation:** “We compare rice–rice, rice–mungbean and corn–mungbean as candidates, using local water access and soil questions. We do not invent a planting prescription.”
- **22–30s — Responsible next step:** “The output identifies missing field measurements and the need for local agronomy review before a real recommendation.”

If NASA is not accessible, use the **Synthetic rehearsal** and say **explicitly** that the generated rainfall values are fictional. Do not narrate them as observed climate or claim a local deficit percentage.

## Model caveats

The 2021–2025 baseline is a short recent reference, not the 30-year WMO normal. A statistical rainfall departure does not by itself prove drought, field stress, water savings or ENSO attribution. NASA POWER point estimates may not resolve field-scale rainfall or irrigated conditions. Scientific validity requires comparisons to local rain gauges and specialist-reviewed agronomic requirements.

## Before submission

Confirm Internet connectivity and NASA retrieval from the actual demo machine. Review the terms for any previously developed code, declare your team’s newly created work, cite the official challenge and other data sources, and get the demo into the event's permitted presentation/video length. Fix any unrelated dashboard errors you plan to show before recording.

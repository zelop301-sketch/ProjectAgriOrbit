# AgriORBIT NASA — three-minute evidence-led pitch (working draft)

## Core story

**Problem:** Farm families near lahar-affected areas can face complex soil and water uncertainty. Space data provide environmental context, but farmers also need their own soil observations and priorities reflected before they consider a crop rotation.

**Solution:** AgriMind AI combines historical NASA POWER rainfall/temperature and a local farm profile with three *exploratory* rotations. The interface lets users change priorities, choose a season, inspect a source record, stress-test historic rainfall by ±20% as a counterfactual, and export a report of assumptions and missing evidence. Agro Sentinel is a planned optional field-sensor platform, not represented as built.

**Important non-claim:** We have not proven improvement in yields, nitrogen balance or profits, and we do not present predictions from a 2025 historical climate record.

## Pitch timing / six-person division

- **0:00–0:25 — Team lead:** A farmer is balancing water, soil and cost decisions. AgriORBIT starts with Botolan as a pilot context (not a verified farm parcel).
- **0:25–0:50 — GIS/NASA engineer:** Show genuine NASA POWER `T2M`, `PRECTOTCORR`, `ALLSKY_SFC_SW_DWN` and point at provider, date, units, coverage and retrieval time. If no live network, say the dataset is cached, or switch to synthetic mode with a visible disclaimer.
- **0:50–1:20 — Research specialist:** Explain how farmer-entered soil data and locally researched crop options enter the same workflow. Mention soil tests, calendar and agronomist approval as requirements before field use.
- **1:20–2:05 — Developer + analytics engineer:** In Rotation Studio choose a month, show 3 options, change water priority, point to the historical rainfall screening formula, score breakdown and hypothetical ±20% stress. Emphasize that numerical coefficients are experimental.
- **2:05–2:30 — Hardware engineer:** Display Agro Sentinel as an *engineering concept*; simulated readouts never passed off as measured field data.
- **2:30–3:00 — Team lead:** Export the evidence report, summarize intended farmer value and name the next validation steps. Close with an invitation to pilot-test with a local extension specialist.

## Judge-ready demonstration checklist

- [ ] Real NASA POWER returns and source URL works on the presentation laptop, **or** a verified cached dataset is explicitly labeled with its actual retrieval date.
- [ ] The synthetic rehearsal mode has a conspicuous *NOT NASA* label.
- [ ] A farm input change re-generates the scenario and does not leave NASA data tied to old coordinates.
- [ ] A selected dry 2025 month changes the *prototype water factor*; no claim that it demonstrates actual crop yield.
- [ ] Agricultural references can be opened and numerical heuristics are clearly acknowledged as assumptions.
- [ ] Report export downloads and includes evidence/limitations.
- [ ] Agro Sentinel shows *SIMULATED* or *PLANNED* rather than *measured*.
- [ ] Pitch uses up to the actual local presentation time limit; confirm separately with the selected local event.
- [ ] Official 2026 team submission and registration done; deadline checked on event site.

## Official links

- Official Field Shift challenge: https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/
- NASA Space Apps 2026: https://www.spaceappschallenge.org/2026/
- NASA POWER: https://power.larc.nasa.gov/docs/services/api/temporal/daily/

NASA Space Apps officially says 2026 submission opens November 14 at 9 AM and closes November 15 at 11:59 PM **local time**. Confirm latest event-specific rules and upload formats on the team's registration page; older years' instructions should not be treated as this year's requirements.

# AgriORBIT Phase 34 — Botolan Evidence to Farmer Decisions

**Sammium Tech / Sammium Smart Labs | Independent NASA Space Apps 2026 prototype**

Phase 34 is a **working FastAPI + HTML/CSS/JavaScript patch** built on the complete Phase 33 application. The main **BOTOLAN EL NIÑO** tab now leads with the **Phase 34 evidence-to-decision workflow**. All previous dashboard modules, 15-second seedling boot, leaf cursor, droplet splash, navigation transitions, 100 FPS *target* graphics (not guaranteed), hazard screening and simulated Agro Sentinel remain included. The old five-year Botolan study is accessible below in an optional, collapsed section and must not be confused with the new reference period.

## Mission

**Problem:** A farmer in Botolan, Zambales deciding what to plant faces uncertain seasonal rainfall, irrigation availability and unmeasured soils during a national El Niño event. DOST-PAGASA on **November 4, 2026** described a *very strong El Niño in the tropical Pacific*, but this is **not a declaration of drought on a particular farm**.

**Phase 34 response:** Use NASA POWER gridded historical climate estimates as context, distinguish a complete comparison from missing data, collect a farmer's irrigation, soil, planning month and priority, and explain why each proposed rotation still needs field verification. None of the results authorize planting, predict yields or claim water savings.

Primary references:

- [NASA Space Apps 2026 — Field Shift challenge](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/)
- [NASA POWER Monthly Point API specification](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/)
- [NASA POWER Daily Point API specification](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)
- [DOST-PAGASA El Niño press release — November 4, 2026](https://pagasa.dost.gov.ph/press-release/233?page=2)
- [FAO irrigation water needs, including paddy rice](https://www.fao.org/4/s2022e/s2022e08.htm)

## Windows installation

1. Extract the ZIP into a **new folder**, e.g. `C:\AgriORBIT_Phase34_Botolan_Evidence_to_Decisions`. Do not execute from a ZIP preview or from `C:\Windows\System32`.
2. Double-click **`START_AGRIORBIT_WINDOWS.cmd`**. Its launcher creates a local `.venv`, installs `requirements.txt`, verifies the running build and opens the browser on port **8034**.
3. After the normal 15-second boot, select **BOTOLAN EL NIÑO**. Phase 34's first panel is the primary judge workflow.
4. Use **Run NASA 30-year comparison** on a network-connected Windows PC. If NASA is not reachable or data are invalid, the app **reports failure**, not an invented result.
5. Use **Synthetic judge rehearsal** to demonstrate controls when offline. A prominent badge says **SYNTHETIC REHEARSAL · NOT NASA**; simulated rainfall and years never count as NASA evidence.

Manual command (PowerShell opened **in the extracted project root**):

```powershell
py -m pip install -r requirements.txt
py -m uvicorn app.main:app --host 127.0.0.1 --port 8034
```

App: **http://127.0.0.1:8034/?force-15=1#botolan**  
Health: **http://127.0.0.1:8034/api/health**  
Expected `build`: **`phase34-botolan-evidence-decisions-3.4.0`**

The separate offline page `VERIFY_PHASE34_DECISION_REHEARSAL_OFFLINE.html` uses the actual Phase 34 UI scripts but **mocked synthetic responses** for browser interaction verification. It does not call NASA or the real backend and does **not** validate live agricultural outcomes.

## Core method

- **Point:** 15.289° N, 120.024° E — **town reference, not surveyed farmland**.
- **Reference:** NASA POWER monthly `PRECTOTCORR`, `T2M` from **1991–2020** (30-year research window) via one monthly API request. The monthly rainfall series is a **mean daily rainfall rate in mm/day**, not a monthly sum. Unit metadata must explicitly confirm mm/day before any arithmetic.
- **Target:** 2026 January–October via the existing audited NASA POWER **daily** API. Every target month requires at least **95%** valid daily values before its rainfall total may be included.
- **Comparison:** For each month, `reference_month_total_mm = average(valid 1991–2020 monthly mm/day values) × number_of_days_in_that_2026_month`. At least **24 of 30** valid reference monthly values are required per month. Compare target daily sum against that matching reference. The cumulative January–October departure is withheld unless **all 10 months** pass the gates; missing values do not become zero.
- **Interpretation:** The **−10%** alert threshold is explicitly a demo *flag to investigate historical rainfall exposure*, not a statistically calibrated anomaly, official drought threshold, ENSO attribution, or next-season forecast. NASA's monthly product does not guarantee underlying daily coverage of historical records; the application claims only that the monthly value was returned as valid.
- **Temperature:** Displayed for historical comparison (where eligible); temperature is **not** converted into water demand, soil moisture, or irrigation savings.
- **Provenance:** NASA request URLs, retrieval UTC timestamps, raw-response SHA-256 and status (`nasa_api` vs `nasa_cached`), plus cached age and warning if network retry fails.

See [docs/PHASE34_SCIENCE_AND_JUDGE_DEMO.md](docs/PHASE34_SCIENCE_AND_JUDGE_DEMO.md) for equations, limitations and a 30-second walkthrough.

## Rotation screening is NOT a crop recommendation

**Rice → Rice**, **Rice → Mungbean** and **Corn → Mungbean** are **unranked research candidates**. The server responds to changes in irrigation, soil texture, soil pH, farmer goals, and a proposed planting month. Climate departures change descriptive warnings when there is sufficient real historical evidence. Irrigation changes which **water-supply questions** are emphasized. No crop is graded as "best," no numeric crop suitability is fabricated, and no approval for planting is issued.

Researchers may **optionally input a crop requirement rule** with pH range, minimum irrigation, a reviewer, review date and an HTTPS source link. The software can flag potential pH or irrigation conflicts, but **it cannot authenticate the supplied reviewer, source content, soil test certificate, or local agronomy**. The quality gate for validated crop requirements remains not passed.

Use the **Download judge evidence report** action to save a Markdown document with climate sources, quality gates, farmer-reported context, assumptions, and each candidate's review flags. The export reflects the loaded mode; synthetic results remain explicitly marked.

## Verification in the build environment

- `python -m pytest -q`: **206 passed**, including all prior Phase 33 tests and 16 new Phase 34 tests.
- `node --check web/field-decisions-ui.js`: parsed successfully.
- **Offline Chromium desktop + mobile:** Phase 34 navigation, three candidates, synthetic chart, changing irrigation flags, Markdown download, NASA-request error handling, and a standalone offline verifier all passed without page JavaScript exceptions. This is a test harness with **mocked synthetic API responses**, not a test of external NASA connectivity.
- **FastAPI TestClient:** verified the actual server route for synthetic mode, validation and error handling; unit tests use synthetic fixture NASA-like payloads solely to test conversion and quality gating.
- **Not verified here:** live NASA POWER retrieval, local farmer data, soil sampling, agronomist approval, field yield improvements, and hardware rover functionality. Before judging, verify live requests on an Internet-connected machine and disclose any pre-hackathon work.

## Troubleshooting

If you still see Phase 33, stop the old server with **Ctrl+C**, launch the extracted Phase 34 folder on port **8034**, then use **Ctrl+Shift+R**. Check `http://127.0.0.1:8034/api/health` for the Phase 34 build ID. If NASA requests fail, check your network connection and see the on-screen error; do not present the synthetic rehearsal as an observed Botolan result.

This is an independent Sammium Tech/Sammium Smart Labs project. No NASA, DOST-PAGASA or PHIVOLCS endorsement is claimed.

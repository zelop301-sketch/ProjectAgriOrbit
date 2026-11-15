AGRIORBIT PHASE 42 — ORIGINAL VISUALS PROTECTED / SCIENCE & DEMO HOTFIX
=======================================================================

WHAT WAS PRESERVED
- Original Phase 34 dashboard HTML, CSS, JavaScript, rover 3D renderers,
  cinematics, cursor, all GIFs/images, audio and navigation are unchanged.
- Existing Phase 41 scientific endpoints and all other original features remain.
- The separately added /science page is enhanced, not the original homepage.

RUN ON WINDOWS POWERSHELL (NO cmd.exe REQUIRED)
1. Extract the ZIP fully.
2. Open PowerShell INSIDE this project directory.
3. py -m pip install -r requirements.txt
4. py START_AGRIORBIT_PHASE42.py
   (If py is not recognized, replace py with python.)
5. Original dashboard: http://127.0.0.1:8034/?force-15=1#botolan
6. Scientific analysis: http://127.0.0.1:8034/science

Do not run two servers on port 8034 simultaneously. Stop the previous server
with Ctrl+C before starting this Phase 42 launcher.

GET A REAL NASA EVIDENCE RECEIPT
On /science, select "Real NASA POWER", enter planting month and farmer
constraints, then RUN HISTORICAL ANALYSIS. Requires internet. Inspect the
receipt: source_type must be nasa_api or nasa_cached, the request URL must
start https://power.larc.nasa.gov/, and a SHA-256 must be present. A cache
receipt shows the ORIGINAL fetch time. If NASA is unreachable, results are
withheld rather than invented. Do not present synthetic rehearsal as NASA.

WHAT THE CARDS MEAN
- Rainfall and ETo are historical crop-window exposure, NOT farm forecasts.
- Historical P10-P90 is across planting cohorts, not a confidence interval.
- Different rotations occupy the field for different numbers of days. Both
  total mm and mm/day are shown to reduce misleading comparisons.
- Longest dry spell: <1 mm/day in an occupied crop period, resets at gaps.
- Crop ETc is withheld unless complete user-supplied sourced Kc schedules
  and NASA meteorology are available, and even then stays unverified.
- Crop ETc is NOT irrigation demand. Rainfall effectiveness, rice ponding,
  seepage/percolation, local soil water, irrigation efficiency are unknown.
- No yield, crop choice, percent water savings or farm accuracy is certified.

READ THE AUDIT
  docs/PHASE42_JUDGE_VALIDATION.md

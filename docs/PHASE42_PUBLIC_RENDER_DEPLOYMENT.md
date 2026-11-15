# AgriORBIT Phase 42 — Public Render Deployment Guide

**Source repository**: https://github.com/zelop301-sketch/ProjectAgriOrbit

## Purpose and preservation

This is an additive hosting patch. All existing Phase 42 source, original
dashboard HTML/CSS, 3D assets, graphics, GIFs, and NASA crop-season methods
are unchanged. `deploy_public.py` imports the original FastAPI app and adds
narrowly scoped public-demo protection for local-only evidence/telemetry writes.

## Publish the three added files

Put these at the root of your existing GitHub clone:
- `render.yaml`
- `deploy_public.py`
- `docs/PHASE42_PUBLIC_RENDER_DEPLOYMENT.md`

In GitHub Desktop, review changes, commit with the summary
`Add Render public demo deployment for Phase 42`, then **Push origin**.
Do not replace the application, and do not remove `.git`.

## Connect Render

1. Visit https://dashboard.render.com/ and sign in.
2. Choose **New → Blueprint**. Connect `zelop301-sketch/ProjectAgriOrbit`
   (branch `main`), then apply the root `render.yaml` settings.
   Alternatively choose **New → Web Service** and configure manually:
   - language/runtime: Python 3
   - plan: Free, if offered
   - branch: `main`, root directory: blank (repository root)
   - build: `pip install -r requirements.txt`
   - start: `uvicorn deploy_public:app --host 0.0.0.0 --port $PORT --workers 1`
   - health check: `/api/health`
   - environment: `PYTHON_VERSION=3.11.11`, `AGRIORBIT_PUBLIC_DEMO=1`,
     `AGRIORBIT_CACHE_DIR=/tmp/agriorbit-cache`
3. Create/deploy the service. Render supplies the actual HTTPS URL;
   never assume your preferred `onrender.com` subdomain is available.
4. Verify the generated URL on another device:
   - `https://<your-render-domain>/api/health`
   - `https://<your-render-domain>/?force-15=1#botolan`
   - `https://<your-render-domain>/science`
5. In `/science`, first run **Synthetic Rehearsal** and verify that
   results are clearly labeled NOT NASA. Then run **Real NASA POWER**.
   A successful real-data run must identify `nasa_api` or `nasa_cached`,
   request URL, UTC retrieval time, daily coverage / units and SHA-256
   receipt. Record which class and actual values appear; do NOT claim a
   fresh API fetch if a cached response appears.
6. Share the actual public Render URL on your NASA Space Apps submission.
   Keep the GitHub URL as a separate source-code link.

## Important caveats

- No real NASA response is bundled with this patch. NASA POWER external
  API network availability and scientific calculations must be tested in
  the deployed environment; scientific limitations in
  `docs/PHASE42_JUDGE_VALIDATION.md` continue to apply.
- Render Free spins down after 15 minutes idle and can take a minute to
  restart. Pre-open the page before a judged demonstration; do not present
  cold-start delays as application failures.
- Free instance local files are temporary and not durable. NASA caches
  created in `/tmp` may disappear at restart. Local SQLite evidence writes
  and telemetry writes are blocked on public demo; the browser-side science
  JSON download still works. Original 3D rover demonstration is simulated.
- This app is a research prototype, not a secure multi-user production
  platform. A public demo may incur bandwidth or resource usage. Do not
  encourage visitors to submit private farm records or exact coordinates.
- The original legacy dashboard has optional non-NASA prototypes and
  agency references. The Phase 42 `/science` module relies on NASA POWER
  for its external meteorological data, not all legacy modules.
- The user's team must authorize public use of all assets and contributions.

## Troubleshooting

- **Build error:** confirm `requirements.txt` is at repo root, Python
  environment is 3.11.11, and inspect Render build logs.
- **Application failed to bind port:** the start command must include
  `--host 0.0.0.0 --port $PORT` (not localhost:8034).
- **404 `/science` or missing 3D assets:** confirm `web/` exists at root
  and Render's Root Directory setting is empty.
- **NASA retrieval returns 503:** inspect the real NASA API request,
  timing and server logs; do not silently substitute synthetic readings.
  The NASA retrieval can require substantial time.
- **403 on telemetry/evidence persistence:** intentional in PUBLIC_DEMO=1.
- **Blank screen:** use `/api/health` to distinguish server errors from
  browser/asset errors. Try an incognito window.

## Links

- Render FastAPI: https://render.com/docs/deploy-fastapi
- Render Blueprint YAML: https://render.com/docs/blueprint-spec
- Render free instance behavior: https://render.com/docs/free
- NASA POWER daily API: https://power.larc.nasa.gov/docs/services/api/temporal/daily/

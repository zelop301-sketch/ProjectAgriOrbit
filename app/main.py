from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Header
from pydantic import BaseModel, Field
from typing import Literal
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .climate import fetch_climate, synthetic_data
from .botolan_demo import mission_metadata, load_comparison
from .seasonal_science import SeasonalRequest, calculate as calculate_seasonal
from .field_decisions import DecisionRequest, calculate as calculate_field_decision, BUILD as PHASE34_BUILD
from .scoring import Farm, compare
from .mission import SensorSample, persist_sample, latest_samples, rover_step, mission_plan, farm_scene, diagnostics, rover_model
from .environment import EnvironmentRequest, environment_exposure, DATASET_REGISTRY
from .earth_catalog import search_granules
from .hud_contract import hud_capabilities
from .precision import PrecisionRequest, precision_assessment
from .boundary import BoundaryRequest, check_boundary
from .spaceapps import GUIDE, SubmissionDraft, audit_draft
from .science_core import ScreeningRequest, screen_against_benchmark
from .hazards import HazardScreenRequest, screen_hazard, DEMO_FARM, DEMO_HAZARDS
from .phase23_integrations import PermissionReview, review_permission, nasa_observation_receipt
from .water_balance import WaterBalanceRequest, calculate_water_balance
from .validation import RainValidationRequest, validate_against_power
from .evidence_store import save_report, read_report
from pydantic import field_validator

app = FastAPI(title="AgriORBIT — AgriMind AI MVP", version="3.4.0", description="NASA POWER climate context + explainable rotation-planning prototype")
ROOT = Path(__file__).resolve().parent.parent


@app.middleware("http")
async def prevent_stale_boot_assets(request, call_next):
    """Phase 27: prevent browsers from silently retaining an older calibration UI."""
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/assets/"):
        response.headers["Cache-Control"] = "no-store, no-cache, max-age=0, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    response.headers["X-AgriORBIT-Build"] = "phase34-botolan-evidence-decisions-3.4.0"
    return response



@app.get("/api/health")
def health():
    return {"status": "ok", "project": "AgriORBIT", "build": "phase34-botolan-evidence-decisions-3.4.0", "boot_duration_seconds": 15, "recommended_port": 8034, "assets_cache": "no-store", "farm_backdrop": "mission-farm-clean-v20.jpg", "photographic_rover_in_backdrop": False, "click_fx": "visible-splash-v31", "living_core": "compositor-static-webp-v27", "cinematic_duration_seconds": 15, "botolan_mission": "live-nasa-power-or-explicit-synthetic-demo", "phase34_scientific_workflow": "1991-2020-reference-and-evidence-gated-screening", "renderer_preset": "fps100", "renderer_target_fps": 100, "fps_guaranteed": False, "fps_note": "Actual rate depends on display refresh, browser scheduling, hardware and scene complexity."}


@app.post("/api/botolan/seasonal")
async def nasa_seasonal_crop_comparison(payload: SeasonalRequest):
    """Historical NASA crop-season climate exposure with explicit data-quality gates."""
    try:
        return await calculate_seasonal(payload)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/science", include_in_schema=False)
def science_workspace():
    """Additive research workspace: original homepage stays byte-for-byte identical."""
    return FileResponse(ROOT / "web" / "nasa-seasonal-workspace.html")


@app.post("/api/botolan/decision")
async def botolan_field_decision(payload: DecisionRequest):
    """Server-verified 30-year POWER reference and qualitative farmer decisions.

    Never accept a client-provided 'NASA response'; provenance is server-side.
    """
    try:
        return await calculate_field_decision(payload)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/botolan/mission")
def botolan_mission():
    """Static provenance/official ENSO context; no NASA data is preloaded."""
    return mission_metadata()


@app.get("/api/botolan/climate")
async def botolan_climate(mode: Literal["nasa", "synthetic"] = "nasa", refresh: bool = False):
    """Server-side NASA comparison or explicitly fabricated demo, never mixed."""
    try:
        return await load_comparison(mode=mode, refresh=refresh)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/spaceapps/guide")
def spaceapps_guide():
    """User-provided Judging & Awards Guide summary, not a NASA eligibility decision."""
    return GUIDE


@app.post("/api/spaceapps/audit")
def spaceapps_audit(draft: SubmissionDraft):
    """Validate structural demo/team limits and report the remaining self-attested rules."""
    return audit_draft(draft)


@app.get("/api/hud/capabilities")
def capabilities():
    return hud_capabilities()


@app.get("/api/climate")
async def climate(
    lat: float = Query(15.289, ge=-90, le=90),
    lon: float = Query(120.024, ge=-180, le=180),
    year: int = Query(2025, ge=1981, le=2025),
    mode: str = Query("nasa", pattern="^(nasa|synthetic)$"),
    refresh: bool = False,
):
    if mode == "synthetic":
        return synthetic_data(lat, lon, year)
    try:
        return await fetch_climate(lat, lon, year, refresh=refresh)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/compare")
def rotations(farm: Farm):
    return compare(farm)


class AssessmentRequest(BaseModel):
    farm: Farm
    year: int = Field(default=2025, ge=1981, le=2025)
    mode: Literal["nasa", "synthetic"] = "nasa"
    refresh: bool = False


@app.post("/api/assess")
async def assess(payload: AssessmentRequest):
    """Server-controlled data provenance: do not accept claimed NASA JSON from a client."""
    farm = payload.farm
    try:
        if payload.mode == "synthetic":
            data = synthetic_data(farm.latitude, farm.longitude, payload.year)
        else:
            data = await fetch_climate(farm.latitude, farm.longitude, payload.year, refresh=payload.refresh)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "climate": data,
        "comparison": compare(farm, data),
        "binding_note": "Climate obtained server-side for matching farm coordinates. NASA cached and synthetic data remain visibly labeled; no external client-supplied provenance is trusted.",
    }



@app.get('/api/phase23/capabilities')
def phase23_capabilities():
    return {'build':'phase34-botolan-evidence-decisions-3.4.0',
            'phivolcs_permission_status':'requires external agency grant; app cannot authorize',
            'official_layer_included':False,'live_nasa_request_supported':True,
            'bundled_nasa_observations':False,'nasa_origin':'NASA POWER daily point API',
            'hazard_use':'Local user-supplied GIS preview only until scope verified',
            'request_url':'https://gisweb.phivolcs.dost.gov.ph/gisweb/geomatics-services-request'}

@app.post('/api/phase23/phivolcs/permission-review')
def phase23_permission_review(payload:PermissionReview):
    return review_permission(payload)

@app.get('/api/phase23/nasa/observations')
async def phase23_nasa_observations(
    lat:float=Query(15.289,ge=-90,le=90),
    lon:float=Query(120.024,ge=-180,le=180),
    year:int=Query(2025,ge=1981,le=2025),
    refresh:bool=False,include_daily:bool=False):
    return await nasa_observation_receipt(lat,lon,year,refresh=refresh,include_daily=include_daily)


@app.get("/api/hazards/capabilities")
def hazard_capabilities():
    """No live PHIVOLCS GIS feed or official data is embedded."""
    return {
        "build": "phase34-botolan-evidence-decisions-3.4.0", "phivolcs_connection": "none (manual source references and user-provided GeoJSON only)",
        "hazard_geometry": "locally supplied GeoJSON clipped to the farm boundary; UTM approximate overlap",
        "sources_authenticated": False, "official_hazard_map_included": False,
        "rainfall_context": "optional historical NASA POWER, separately labeled, NOT a lahar forecast",
        "safety_assessment_or_lahar_forecast": False,
        "source_references": [
            {"label":"PHIVOLCS volcano hazard maps", "url":"https://www.phivolcs.dost.gov.ph/volcano-hazard/"},
            {"label":"PHIVOLCS hazard map download guidance", "url":"https://www.phivolcs.dost.gov.ph/gisweb-download-hazard-maps-instruction/"},
            {"label":"PHIVOLCS map portal", "url":"https://maps.phivolcs.dost.gov.ph/"},
            {"label":"HazardHunterPH", "url":"https://hazardhunter.georisk.gov.ph/"},
            {"label":"PHIVOLCS vector data request", "url":"https://gisweb.phivolcs.dost.gov.ph/gisweb/geomatics-services-request"},
        ],
    }


@app.get("/api/hazards/demo")
def hazard_demo():
    return {"demo_only":True,"official_phivolcs_data":False,
            "farm_geometry":DEMO_FARM,"hazard_geojson":DEMO_HAZARDS,
            "notice":"Both sample shapes are fictional. They do not indicate real conditions in Botolan."}


@app.post("/api/hazards/screen")
async def hazard_screen(payload:HazardScreenRequest):
    """Screen geometry; NASA season context is never used to forecast a lahar."""
    try:
        report=screen_hazard(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422,detail=str(exc)) from exc
    report['nasa_climate_context']={"status":"not_requested","data_class":"none", "historical_only":True,
                                    "note":"NASA data is independent of mapped hazard exposure; neither predicts future lahar occurrence."}
    if payload.climate_mode!='none':
        if payload.farm is None:
            raise HTTPException(status_code=422,detail='Provide farm profile for historical NASA POWER request.')
        benchmark=await precision_assessment(PrecisionRequest(
            farm=payload.farm,end_year=payload.climate_end_year,
            baseline_years=payload.climate_baseline_years,mode=payload.climate_mode))
        b=benchmark.get('benchmark') or {}
        report['nasa_climate_context']={
            'status':b.get('status','unavailable'), 'data_class':b.get('data_class','insufficient_evidence'),
            'rainfall_anomaly_pct':b.get('rainfall_anomaly_pct') if b.get('data_class')=='historical_nasa' else None,
            'baseline_seasons_valid':b.get('baseline_seasons_valid'),
            'historical_only':True,'nasa_request_result':benchmark.get('retrieval_status','see benchmark'),
            'note':'A historical precipitation comparison is NOT a real-time lahar warning, flood forecast or trigger probability.'
        }
    return report


@app.get("/api/science/capabilities")
def science_capabilities():
    return {
        "build": "phase34-botolan-evidence-decisions-3.4.0",
        "integrations": {
            "nasa_power": "historical server-side fetch with verified request and coverage checks; NOT plot-scale",
            "hls_cmr": "granule discovery; metadata only",
            "hls_ndvi": "optional offline processing of user-downloaded COGs with real per-pixel Fmask QA; NASA authenticity unverified",
            "ecostress": "catalog lookup only; no thermal raster analysis",
            "smap": "not ingested; regional context only",
            "gauge_validation": "NASA POWER daily pairs vs user-supplied gauge data; calibration self-reported",
            "crop_rules": "user-entered agronomist-reviewed constraints; reviewer identity not authenticated",
            "water_balance": "arithmetic FAO-56 framework using supplied ETc or ETo/Kc inputs; not calibrated",
            "evidence_store": "opt-in local SQLite/WAL; NOT multi-tenant cloud production ready",
        },
        "automatic_crop_or_yield_predictions": False,
        "rover_hardware_connected": False,
        "field_planting_authorized": False,
        "reference_links": ["https://hls.gsfc.nasa.gov/data-access-and-tools/",
                            "https://power.larc.nasa.gov/",
                            "https://www.fao.org/4/x0490e/x0490e0a.htm"],
    }


@app.post('/api/science/screen')
async def scientific_screen(payload: ScreeningRequest):
    """Server-obtained POWER benchmark; never silently substitute synthetic data."""
    result = await precision_assessment(PrecisionRequest(
        farm=payload.farm, end_year=payload.end_year,
        baseline_years=payload.baseline_years, mode=payload.mode))
    result['scientific_screening'] = screen_against_benchmark(
        payload.farm, result['benchmark'], payload.crop_rules)
    result['scientific_notice'] = 'Descriptive historical climate and reviewed constraints only. No planting-ready decision or validated yield projection.'
    return result


@app.post('/api/science/validate/rainfall')
async def science_validate_rainfall(payload: RainValidationRequest):
    try:
        return await validate_against_power(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=503,detail=str(exc)) from exc


@app.post('/api/science/water-balance')
def science_water_balance(payload: WaterBalanceRequest):
    return calculate_water_balance(payload)


class EvidenceRecordRequest(BaseModel):
    source_kind: Literal['historical_nasa', 'synthetic_demo', 'user_supplied', 'mixed_unverified']
    report: dict


@app.post('/api/science/evidence', status_code=201)
def science_save_evidence(payload: EvidenceRecordRequest):
    import json
    if len(json.dumps(payload.report)) > 200_000:
        raise HTTPException(status_code=413,detail='Evidence export exceeds 200 KB')
    return save_report(payload.report, 'user_supplied_unverified')


@app.get('/api/science/evidence/{report_id}')
def science_read_evidence(report_id: str):
    from uuid import UUID
    try: UUID(report_id)
    except ValueError: raise HTTPException(status_code=422,detail='Invalid report ID')
    report=read_report(report_id)
    if report is None: raise HTTPException(status_code=404,detail='Evidence record not found')
    return report


@app.post("/api/precision/assess")
async def run_precision_assessment(payload: PrecisionRequest):
    """Server-only NASA multi-year historical benchmark; no client-claimed NASA payloads."""
    return await precision_assessment(payload)


@app.post("/api/precision/boundary")
def precision_boundary(payload: BoundaryRequest):
    """Rough geographic area sanity check for a user-provided small field polygon."""
    try:
        return check_boundary(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/precision/capabilities")
def precision_capabilities():
    return {
        "version": "1.3.0",
        "validated_nasa_integration": "NASA POWER historical daily point API (when reachable)",
        "new_capabilities": ["Multi-season precipitation benchmark (5–10 previous seasons)",
                             "95% monthly precipitation coverage gate", "Chronologically correct Nov–Feb season windows",
                             "Field GeoJSON approximate area sanity check", "Bounded concurrent fetch + atomic historical caches"],
        "unverified": ["Farm-level crop suitability", "Site-specific rainfall gauges", "NDVI or ECOSTRESS raster pixels",
                       "Yield forecast", "Physical rover calibration"],
        "data_categories": ["nasa_api", "nasa_cached", "synthetic", "farmer_entered"],
    }


class SceneRequest(BaseModel):
    farm: Farm
    scenario: Literal["A", "B", "C"] = "B"


@app.get("/api/earth/sources")
def earth_sources():
    return {"datasets": DATASET_REGISTRY, "warning": "Catalog references are not raster ingestion; only NASA POWER live-point integration is available."}


@app.get("/api/earth/granules")
async def earth_granules(product: Literal["modis", "ecostress", "hls_l30", "hls_s30"] = "modis",
                         lat: float = Query(15.289, ge=-90, le=90),
                         lon: float = Query(120.024, ge=-180, le=180),
                         year: int = Query(2025, ge=2001, le=2026)):
    try:
        return await search_granules(product, lat, lon, year)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/mission/environment")
def mission_environment(payload: EnvironmentRequest):
    return environment_exposure(payload)


@app.get("/api/mission/rover-model")
def mission_rover_model():
    return rover_model()


@app.get("/api/mission/diagnostics")
def mission_diagnostics():
    return diagnostics()


@app.post("/api/mission/scene")
def mission_scene(payload: SceneRequest):
    return farm_scene(payload.farm, payload.scenario)


@app.post("/api/mission/plan")
def mission_route(farm: Farm):
    return mission_plan(farm)


@app.get("/api/mission/simulate")
def mission_simulate(progress: float = Query(0, ge=0, le=1)):
    return rover_step(progress)


@app.post("/api/mission/telemetry", status_code=201)
def add_telemetry(sample: SensorSample, x_agriorbit_sensor_token: str | None = Header(default=None)):
    # Measured samples require an intentionally configured shared secret.
    # This is an explicit ingestion gate, NOT proof a sensor is actually calibrated.
    if sample.source_type == "field_measured":
        import os
        import secrets
        expected = os.environ.get("AGRIORBIT_SENSOR_TOKEN", "")
        if not expected or not x_agriorbit_sensor_token or not secrets.compare_digest(expected, x_agriorbit_sensor_token):
            raise HTTPException(status_code=403, detail="Measured data ingestion disabled or token invalid; simulation must remain labeled simulated.")
    persist_sample(sample)
    return {"stored": True, "source_type": sample.source_type, "hardware_verified": False,
            "notice": "Stored provenance metadata does not independently authenticate the physical sensor."}


@app.get("/api/mission/telemetry")
def read_telemetry(limit: int = Query(default=12, ge=1, le=100)):
    return {"samples": latest_samples(limit), "note": "Check source_type; stored samples are unverified by the service."}

@app.get("/")
def index():
    return FileResponse(ROOT / "web" / "index.html")


app.mount("/assets", StaticFiles(directory=ROOT / "web"), name="assets")

from fastapi.testclient import TestClient
from app.main import app
from app.precision import summarize_season, compute_benchmark
from app.boundary import BoundaryRequest, check_boundary
from app.climate import synthetic_data, summarise
import pytest

client = TestClient(app)


def samples(first=2019, last=2025):
    return {year: synthetic_data(15.289, 120.024, year) for year in range(first,last+1)}


def test_precision_end_to_end_synthetic_never_claims_nasa():
    r = client.post('/api/precision/assess',json={'farm': {'start_month': 6},'end_year':2025,'baseline_years':5,'mode':'synthetic'})
    assert r.status_code == 200
    d = r.json()
    b = d['benchmark']
    assert b['status']=='ready'
    assert b['data_class']=='synthetic_demo'
    assert b['provenance']['endpoint'] is None
    assert b['provenance']['provider'].startswith('AgriORBIT')
    assert b['baseline_seasons_valid']==5
    assert b['rainfall_anomaly_pct']==0
    assert d['comparison']['comparison_mode']=='heuristic_only'
    assert d['quality_gate_passed'] is False


def test_cross_year_nov_dec_jan_chronology():
    d=samples()
    s=summarize_season(d,2025,11)
    assert s['period']==[(2024,11),(2024,12),(2025,1)]
    assert s['usable']
    assert s['precipitation_mm'] == round(d[2024]['months'][10]['precipitation_mm']+d[2024]['months'][11]['precipitation_mm']+d[2025]['months'][0]['precipitation_mm'],2)


def test_cross_year_dec_jan_feb_chronology():
    s=summarize_season(samples(), 2025,12)
    assert s['period']==[(2024,12),(2025,1),(2025,2)]


def test_missing_or_invalid_month_aborts_anomaly():
    d=samples()
    d[2025]['months'][5]['coverage_pct_by_variable']['PRECTOTCORR']=50
    benchmark=compute_benchmark(d,end_year=2025,start_month=6,baseline_years=5,requested_source='nasa')
    assert benchmark['status']=='insufficient_coverage'
    assert benchmark['target_season']['precipitation_mm'] is None
    assert benchmark['rainfall_anomaly_pct'] is None


def test_missing_month_not_treated_as_zero():
    d=samples()
    d[2025]['months'][0]['precipitation_mm']=None
    s=summarize_season(d,2025,1)
    assert s['usable'] is False


def test_partial_daily_precip_does_not_appear_as_annual_total():
    r={'properties':{'parameter':{'T2M':{'20250101':28},'PRECTOTCORR':{'20250101':5},'ALLSKY_SFC_SW_DWN':{'20250101':4}}}}
    data=summarise(r,15.289,120.024,2025,'nasa_api','2026-11-11T00:00:00+00:00','https://power.larc.nasa.gov')
    assert data['summary']['annual_precipitation_mm'] is None
    assert data['months'][0]['precipitation_is_partial'] is True
    assert data['warnings']
    assert data['quality_gate']['annual_precipitation_ready'] is False


def test_negative_precipitation_rejected_not_made_zero():
    r={'properties':{'parameter':{'T2M':{'20250101':28,'20250102':28},'PRECTOTCORR':{'20250101':5,'20250102':-2},'ALLSKY_SFC_SW_DWN':{'20250101':4,'20250102':4}}}}
    data=summarise(r,15.289,120.024,2025,'nasa_api','2026-11-11T00:00:00+00:00','url')
    assert data['months'][0]['precipitation_mm'] == 5
    assert data['rejected_daily_values_by_parameter']['PRECTOTCORR'] >= 1


def test_server_precision_api_rejects_invalid_bounds():
    assert client.post('/api/precision/assess',json={'farm': {},'baseline_years':40,'mode':'synthetic'}).status_code == 422
    assert client.post('/api/precision/assess',json={'farm': {'latitude':110},'mode':'synthetic'}).status_code == 422
    assert client.get('/api/precision/capabilities').status_code == 200


def test_area_sanity_check_and_discrepancy_warning():
    polygon={'type':'Polygon','coordinates':[[[120.02,15.28],[120.021,15.28],[120.021,15.281],[120.02,15.281],[120.02,15.28]]]}
    response=client.post('/api/precision/boundary',json={'geometry': polygon,'reported_area_ha':1,'farm_latitude':15.2805,'farm_longitude':120.0205})
    assert response.status_code==200
    d=response.json()
    assert 1 < d['approximate_area_ha'] < 2
    assert d['source_type']=='user_supplied_geometry'
    assert d['surveyed'] is False
    assert isinstance(d['flags'],list)


def test_boundary_open_ring_rejected():
    geo={'type':'Polygon','coordinates':[[[120,15],[120.001,15],[120.001,15.001],[120,15.001]]]}
    r=client.post('/api/precision/boundary',json={'geometry':geo,'reported_area_ha':1,'farm_latitude':15,'farm_longitude':120})
    assert r.status_code==422


def test_frontend_renders_precision_ui_with_controls():
    from pathlib import Path
    root=Path(__file__).resolve().parent.parent
    html=(root/'web/index.html').read_text(encoding='utf-8')
    js=(root/'web/precision-ui.js').read_text(encoding='utf-8')
    for needle in ['precision-fetch','precision-demo','precision-year','precision-export','precision-boundary','precision-ui.js']:
        assert needle in html
    assert '/api/precision/assess' in js
    assert 'SYNTHETIC' in js
    assert 'No missing values were fabricated' in js


def test_real_nasa_outage_does_not_silently_fabricate(monkeypatch):
    from unittest.mock import AsyncMock
    monkeypatch.setattr('app.precision.fetch_climate', AsyncMock(side_effect=RuntimeError('network unavailable')))
    r = client.post('/api/precision/assess', json={
        'farm': {'start_month': 11}, 'end_year': 2025, 'baseline_years': 5, 'mode': 'nasa'})
    assert r.status_code == 200
    b=r.json()
    assert b['benchmark']['status'] == 'insufficient_coverage'
    assert b['benchmark']['data_class'] != 'historical_nasa'
    assert b['quality_gate_passed'] is False
    assert b['failed_years']
    assert b['years_received'] == []
    assert b['benchmark']['rainfall_anomaly_pct'] is None

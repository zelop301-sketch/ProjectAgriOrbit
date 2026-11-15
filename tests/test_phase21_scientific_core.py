"""Phase 21 scientific behavior; mocked fixtures are NOT actual NASA evidence."""
from datetime import date
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.science_core import CropRule, screen_against_benchmark
from app.scoring import Farm
from app.water_balance import WaterBalanceRequest, calculate_water_balance
from app.validation import RainGaugeReading, compare_daily_rainfall

client=TestClient(app)

def fake_benchmark(kind='historical_nasa', status='ready'):
    return {'data_class':kind,'status':status, 'rainfall_anomaly_pct':-31 if status=='ready' else None,
            'recent_median_rainfall_mm':240,'baseline_seasons_valid':5,
            'target_season':{'precipitation_mm':177}}


def test_missing_nasa_and_crop_rules_never_claim_suitability():
    result=screen_against_benchmark(Farm(),fake_benchmark('synthetic_demo'),[])
    assert not result['decision_ready']
    assert all(not sc['farm_planting_authorized'] for sc in result['scenarios'])
    assert all(sc['screening_status']=='further_field_review_required' for sc in result['scenarios'])
    assert result['historical_climate']['rainfall_anomaly_pct'] is None
    assert result['quality_gates'][0]['passed'] is False


def test_historical_nasa_anomaly_changes_explanation_but_not_prototype_score():
    farm=Farm(soil_ph=4.0,soil_source='laboratory')
    baseline=screen_against_benchmark(farm,fake_benchmark(),[])
    assert baseline['historical_climate']['rainfall_anomaly_pct']==-31
    assert baseline['historical_climate']['valid_nasa_context']
    assert any('31.0%' in w for w in baseline['scenarios'][1]['missing_and_precautions'])
    assert all(not s['legacy_score_used_for_decision'] for s in baseline['scenarios'])


def test_reviewed_crop_rules_can_flag_reported_lab_conflict():
    farm=Farm(current_crop='Rice',soil_ph=3.4,soil_source='laboratory')
    reviewed=CropRule(crop='Rice',ph_min=5.0,ph_max=7.0,
                     reviewed_by='Example agronomist (unverified)',reviewed_on=date(2026,11,14),
                     source_url='https://example.edu/field-report')
    result=screen_against_benchmark(farm,fake_benchmark(),[reviewed])
    assert result['scenarios'][0]['screening_status']=='reported_lab_rule_conflict'
    assert result['scenarios'][0]['constraints_from_reviewed_rules']
    assert not result['decision_ready']
    assert result['quality_gates'][2]['passed'] is False # missing rules for other candidate crops


def test_unreviewed_rule_does_not_create_hard_conflict():
    farm=Farm(soil_ph=3.4,soil_source='laboratory')
    rule=CropRule(crop='Rice',ph_min=5.0,ph_max=7.0)
    result=screen_against_benchmark(farm,fake_benchmark(),[rule])
    assert all(not s['constraints_from_reviewed_rules'] for s in result['scenarios'])


def test_invalid_crop_rule_rejected():
    assert client.post('/api/science/screen',json={'farm':{},'mode':'synthetic','crop_rules':[{'crop':'Rice','ph_min':8,'ph_max':6}]}).status_code==422


def test_scientific_screen_endpoint_never_calls_synthetic_as_nasa():
    response=client.post('/api/science/screen',json={'farm':{'start_month':11},'mode':'synthetic','baseline_years':5})
    assert response.status_code==200,response.text
    data=response.json()
    assert data['benchmark']['data_class']=='synthetic_demo'
    assert not data['scientific_screening']['quality_gates'][0]['passed']
    assert data['scientific_screening']['historical_climate']['rainfall_anomaly_pct'] is None
    assert data['scientific_screening']['decision_ready'] is False


def test_nasa_failure_does_not_return_fabricated_history(monkeypatch):
    monkeypatch.setattr('app.precision.fetch_climate',AsyncMock(side_effect=RuntimeError('NASA offline')))
    r=client.post('/api/science/screen',json={'farm':{},'mode':'nasa','baseline_years':5})
    assert r.status_code==200
    data=r.json()
    assert data['benchmark']['status']=='insufficient_coverage'
    assert not data['scientific_screening']['historical_climate']['valid_nasa_context']
    assert data['failed_years']


def test_water_budget_arithmetic_and_limits():
    req=WaterBalanceRequest(period_days=30,starting_storage_mm=75,soil_capacity_mm=120,
         precipitation_mm=60,irrigation_mm=20,etc_mm=95,runoff_mm=5,drainage_mm=10)
    d=calculate_water_balance(req)
    assert d['net_change_mm']==-30
    assert d['bounded_storage_mm']==45
    assert d['simulation_only'] is True
    assert d['unaccounted_shortfall_mm']==0
    assert client.post('/api/science/water-balance',json=req.model_dump()).status_code==200


def test_water_balance_fao56_etc_formula():
    r=WaterBalanceRequest(period_days=10,starting_storage_mm=50,soil_capacity_mm=100,
                          precipitation_mm=0,eto_mm_per_day=4,crop_coefficient=1.2)
    d=calculate_water_balance(r)
    assert d['crop_evapotranspiration_mm']==48
    assert d['etc_method'].startswith('FAO56')


def test_water_budget_out_of_range_and_missing_eto_rejected():
    base={'period_days':30,'starting_storage_mm':30,'soil_capacity_mm':100,'precipitation_mm':30}
    assert client.post('/api/science/water-balance',json=base).status_code==422
    assert client.post('/api/science/water-balance',json={**base,'etc_mm':50,'runoff_mm':-1}).status_code==422


def test_gauge_errors_and_missing_pairs():
    readings=[RainGaugeReading(day=date(2025,6,i),precipitation_mm=i) for i in range(1,7)]
    data={f'202506{i:02}':i+1 for i in range(1,6)}
    result=compare_daily_rainfall(readings,data,'synthetic_rehearsal_not_nasa',False)
    assert result['paired_days']==5
    assert result['unpaired_gauge_days']==1
    assert result['statistics']['mae_mm']==1
    assert result['statistics']['bias_power_minus_gauge_mm']==1
    assert result['independent_validation_completed'] is False


def test_bad_dates_and_duplicates_rejected():
    d={'latitude':15.2,'longitude':120.2,'year':2025,'mode':'synthetic','observations':[{'day':'2025-06-01','precipitation_mm':1},{'day':'2025-06-01','precipitation_mm':2}]}
    assert client.post('/api/science/validate/rainfall',json=d).status_code==422


def test_daily_gauge_api_synthetic_provenance():
    r=client.post('/api/science/validate/rainfall',json={'latitude':15,'longitude':120,'year':2025,'mode':'synthetic',
        'observations':[{'day':f'2025-06-{i:02}','precipitation_mm':3} for i in range(1,7)]})
    assert r.status_code==200
    assert r.json()['source_type']=='synthetic_rehearsal_not_nasa'
    assert not r.json()['independent_validation_completed']


def test_hls_mask_excludes_clouds_and_water():
    import numpy as np
    from scripts.hls_field_ndvi import calculate_ndvi
    red=np.ones((4,4),dtype='int16')*1000
    nir=np.ones((4,4),dtype='int16')*3000
    qa=np.zeros((4,4),dtype='uint8')
    qa[0,0]=1<<1 # cloud
    qa[1,0]=1<<5 # water
    result=calculate_ndvi(red,nir,qa,np.ones((4,4),dtype=bool))
    assert result['clear_valid_pixels']==14
    assert result['valid_pixel_coverage_pct']==87.5
    assert result['ndvi_median']==0.5
    assert result['field_statistic_usable'] is True


def test_hls_too_few_valid_pixels_is_not_classified():
    import numpy as np
    from scripts.hls_field_ndvi import calculate_ndvi
    red=np.ones((2,2))*1000;nir=np.ones((2,2))*3000; qa=np.zeros((2,2),dtype='uint8')
    result=calculate_ndvi(red,nir,qa,np.ones((2,2),dtype=bool))
    assert result['field_statistic_usable'] is False


def test_capabilities_and_hls_catalog_presence():
    r=client.get('/api/science/capabilities')
    assert r.status_code==200
    assert r.json()['integrations']['hls_cmr'].startswith('granule discovery')
    sources=client.get('/api/earth/sources').json()['datasets']
    assert any(s['id']=='nasa_hls' and s['status']=='MANUAL_IMPORT_ONLY' for s in sources)
    assert client.get('/assets/science-ui.js').status_code==200


def test_evidence_store_opt_in_local_and_does_not_trust_source_claim(monkeypatch,tmp_path):
    import app.evidence_store as store
    monkeypatch.setattr(store,'DB_FILE',tmp_path/'evidence.sqlite3')
    r=client.post('/api/science/evidence',json={'source_kind':'historical_nasa','report':{'score':4,'label':'self-asserted'}})
    assert r.status_code==201,r.text
    assert r.json()['source_kind']=='user_supplied_unverified'
    record=client.get('/api/science/evidence/'+r.json()['id'])
    assert record.status_code==200
    assert record.json()['sha256']==r.json()['sha256']
    assert record.json()['report']['label']=='self-asserted'


def test_evidence_ui_scripts_and_control_ids():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    html=(root/'web/index.html').read_text(encoding='utf-8')
    js=(root/'web/science-ui.js').read_text(encoding='utf-8')
    for identifier in ('science21-lab','science21-run-nasa','science21-water-run','science21-hls-find','science21-gauge-run'):
        assert f'id="{identifier}"' in html
    assert '/api/science/screen' in js
    assert 'synthetic' in js
    assert 'science-ui.js?v=phase34-botolan-evidence-decisions-3.4.0' in html

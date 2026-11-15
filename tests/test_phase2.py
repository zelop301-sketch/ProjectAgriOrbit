import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.assessment import season_context, exposure_penalty
from app.scoring import Farm, compare
from app.climate import synthetic_data

client = TestClient(app)


def test_season_is_mathematically_traceable():
    climate = synthetic_data(15.289, 120.024, 2025)
    context = season_context(climate, 6)
    expected = sum(climate['months'][i-1]['precipitation_mm'] for i in [6, 7, 8])
    assert context['usable'] is True
    assert context['window'] == 'Jun–Jul–Aug'
    assert abs(context['rainfall_mm'] - expected) < 0.11
    assert 0 <= context['within_year_dry_share'] <= 1
    assert context['status'] == 'SYNTHETIC REHEARSAL'


def test_historical_weather_changes_only_experimental_water_dimension():
    farm = Farm(start_month=2, irrigation='none')
    data = synthetic_data(farm.latitude, farm.longitude, 2025)
    plain = {s['id']:s for s in compare(farm)['scenarios']}
    linked = {s['id']:s for s in compare(farm, data)['scenarios']}
    assert linked['A']['climate_water_penalty'] > 0
    assert linked['A']['breakdown'][0]['score'] < plain['A']['breakdown'][0]['score']
    for key in ['soil_cover', 'diversity', 'affordability', 'simplicity']:
        i = next(i for i, (k, _) in enumerate(__import__('app.scoring',fromlist=['CRITERIA']).CRITERIA) if k == key)
        assert linked['A']['breakdown'][i]['score'] == plain['A']['breakdown'][i]['score']
    assert linked['A']['rainfall_stress_test']['drier_20_pct_water_penalty'] >= linked['A']['rainfall_stress_test']['wetter_20_pct_water_penalty']


def test_incomplete_climate_cannot_influence_score():
    farm = Farm(start_month=4)
    data = synthetic_data(farm.latitude, farm.longitude, 2025)
    for month in [4, 5, 6]:
        data['months'][month-1]['complete_days'] = 1
    result = compare(farm, data)
    assert result['season_context']['usable'] is False
    assert result['comparison_mode'] == 'heuristic_only'
    assert all(s['climate_water_penalty'] == 0 for s in result['scenarios'])


def test_invalid_start_month_rejected():
    assert client.post('/api/compare',json={'start_month':13}).status_code == 422
    assert client.post('/api/assess',json={'farm':{},'year':2027}).status_code == 422


def test_assess_synthetic_never_nasa():
    r=client.post('/api/assess',json={'farm':{'start_month':3}, 'mode':'synthetic', 'year':2025})
    assert r.status_code==200
    v=r.json()
    assert v['climate']['source_type']=='synthetic'
    assert v['climate']['request_url'] is None
    assert v['comparison']['data_kind']=='synthetic'
    assert v['comparison']['season_context']['status']=='SYNTHETIC REHEARSAL'


def test_assess_real_path_uses_server_response(monkeypatch):
    # Representative response injected into the backend, not an actual NASA API call.
    climate=synthetic_data(15.289, 120.024, 2025)
    climate['source_type']='nasa_api'
    climate['provider']='NASA POWER'
    monkeypatch.setattr('app.main.fetch_climate', AsyncMock(return_value=climate))
    r=client.post('/api/assess',json={'farm':{'latitude':15.289, 'longitude':120.024},'mode':'nasa'})
    assert r.status_code==200
    assert r.json()['comparison']['data_kind']=='nasa_api'
    assert 'matching farm coordinates' in r.json()['binding_note']


def test_no_assessment_data_accepted_from_client():
    r=client.post('/api/assess',json={'farm':{},'mode':'synthetic', 'climate':{'source_type':'nasa_api'}})
    assert r.status_code == 200
    assert r.json()['climate']['source_type'] == 'synthetic'

"""Phase33 evidence integrity and actual navigation smoke checks."""
import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import botolan_demo as b
from app.climate import synthetic_data

R = Path(__file__).resolve().parents[1]
C = TestClient(app)


def nasa_record(year):
    r=synthetic_data(b.LAT,b.LON,year)
    r['source_type']='nasa_api'
    r['provider']='NASA POWER'
    r['request_url']='https://power.larc.nasa.gov/api/temporal/daily/point?start='+str(year)+'0101'
    return r


def test_health_and_navigation_integrated():
    health=C.get('/api/health').json()
    assert health['recommended_port']==8034
    assert health['build']==b.BUILD
    assert health['botolan_mission']=='live-nasa-power-or-explicit-synthetic-demo'
    html=C.get('/').text
    assert 'id="view-botolan"' in html
    assert 'data-view="botolan"' in html
    assert 'botolan-ui.js' in html and 'botolan.css' in html
    assert 'NASA POWER / explicit simulation' in html
    assert 'Synthetic rehearsal' in html
    js=C.get('/assets/botolan-ui.js')
    assert js.status_code==200
    assert 'data_class' in js.text


def test_metadata_distinguishes_published_enso_from_local_drought():
    m=C.get('/api/botolan/mission').json()
    assert m['advisory']['issued_on']=='2026-11-04'
    assert 'not a Botolan-specific drought' in m['advisory']['caution']
    assert m['period']['reference_not_climate_normal']
    assert len(m['rotation_options'])==3
    assert 'no crop sequence is proven suitable' in m['decision_limit']


def test_nasa_partial_request_does_not_request_future_december():
    params,url=b.partial_request()
    assert params['start']=='20260101' and params['end']=='20261031'
    assert params['latitude']=='15.28900'
    assert 'PRECTOTCORR' in url and 'T2M' in url


def test_deterministic_synthetic_explicit_and_not_nasa():
    d=C.get('/api/botolan/climate?mode=synthetic').json()
    assert d['data_class']=='SYNTHETIC_DEMO_NOT_NASA'
    assert d['source_status']=='complete_comparison'
    assert d['summary']['months_usable']==10
    assert -36 < d['summary']['rain_anomaly_pct'] < -34
    assert 'Artificial 2026 scenario' in d['simulation_assumption']
    assert all(row['request_url'] is None for row in d['provenance'])
    assert 'No crop suitability' in ' '.join(d['cautions'])


def test_real_comparison_checks_coverage_in_each_month():
    records={year:nasa_record(year) for year in (*b.BASELINE_YEARS,b.TARGET_YEAR)}
    for row in records[2026]['months'][:10]:
        row['precipitation_mm']*=0.73
    result=b.build_comparison(records,mode='nasa')
    assert result['data_class']=='HISTORICAL_NASA_POWER'
    assert result['summary']['months_usable']==10
    assert -28 < result['summary']['rain_anomaly_pct'] < -26
    records[2026]['months'][3]['coverage_pct_by_variable']['PRECTOTCORR']=89
    result=b.build_comparison(records,mode='nasa')
    assert result['months'][3]['rain_2026_mm'] is None
    assert result['summary']['rain_anomaly_pct'] is None
    assert result['source_status']=='incomplete'
    assert result['summary']['months_usable']==9


def test_three_reference_years_required_per_month():
    records={year:nasa_record(year) for year in (*b.BASELINE_YEARS,b.TARGET_YEAR)}
    for year in (2021,2022,2023):
        records[year]['months'][1]['coverage_pct_by_variable']['PRECTOTCORR']=0
    d=b.build_comparison(records,mode='nasa')
    assert d['months'][1]['valid_reference_years']==2
    assert d['months'][1]['rain_reference_mm'] is None
    assert d['summary']['rain_anomaly_pct'] is None


def test_never_mislabel_synthetic_as_nasa():
    records={year:nasa_record(year) for year in (*b.BASELINE_YEARS,b.TARGET_YEAR)}
    records[2023]['source_type']='synthetic'
    with pytest.raises(ValueError,match='Synthetic source'):
        b.build_comparison(records,mode='nasa')


def test_endpoint_nasa_success_mock_server_data(monkeypatch):
    async def fake(mode='nasa', refresh=False):
        assert mode=='nasa'
        return b.build_comparison({year:nasa_record(year) for year in (*b.BASELINE_YEARS,b.TARGET_YEAR)},mode='nasa')
    monkeypatch.setattr('app.main.load_comparison',fake)
    response=C.get('/api/botolan/climate?mode=nasa')
    assert response.status_code==200
    assert response.json()['data_class']=='HISTORICAL_NASA_POWER'


def test_endpoint_error_does_not_silently_substitute_synthetic(monkeypatch):
    async def offline(mode='nasa',refresh=False):
        raise RuntimeError('No NASA access')
    monkeypatch.setattr('app.main.load_comparison',offline)
    response=C.get('/api/botolan/climate?mode=nasa')
    assert response.status_code==503
    assert 'No NASA access' in response.json()['detail']


def test_invalid_mode_rejected():
    assert C.get('/api/botolan/climate?mode=third_party').status_code==422


def test_script_asset_and_windows_launcher():
    assert 'scripts\\launch_phase34.py' in (R/'START_AGRIORBIT_WINDOWS.cmd').read_text()
    assert 'PORT=8034' in (R/'scripts/launch_phase34.py').read_text()
    assert '#botolan' in (R/'scripts/launch_phase34.py').read_text()
    assert 'window.AgriOrbitBotolan?.onView(view)' in (R/'web/app.js').read_text()
    assert 'No synthetic fallback occurred' in (R/'web/botolan-ui.js').read_text()

"""Scientific regression cases for the additive NASA seasonal engine.

NASA-shaped fixtures are only in tests. They are never shipped as real observations.
"""
from copy import deepcopy
from datetime import date
from pathlib import Path
import asyncio

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import seasonal_science as s

C=TestClient(app)
ROOT=Path(__file__).resolve().parents[1]


def req(**kw):return s.SeasonalRequest(mode='synthetic',**kw)


def sample(req_=None):
    req_=req_ or req()
    return s.parse_daily(s.demo_daily(),source_type='synthetic',retrieved_at=None,url=None,
                         latitude=req_.latitude,longitude=req_.longitude)


def test_original_renderer_assets_and_science_workspace():
    assert C.get('/').status_code == 200
    assert C.get('/science').status_code == 200
    for file in ('rover3d.js','mission-farm-clean-v20.jpg','agriorbit-seedling-original.gif'):
        assert (ROOT/'web'/file).is_file()
    assert 'SYNTHETIC REHEARSAL' in C.get('/science').text


def test_request_url_and_coordinates_are_server_composed():
    payload=s.SeasonalRequest(latitude=15.42,longitude=120.18,location_source='farmer_report')
    p,url=s.api_request(payload)
    assert p['start']=='20150101' and p['end']=='20251231'
    assert 'PRECTOTCORR' in p['parameters'] and 'ALLSKY_SFC_SW_DWN' in p['parameters']
    assert p['latitude']=='15.42000' and p['longitude']=='120.18000'
    assert 'community=AG' in url and 'time-standard=LST' in url
    with pytest.raises(ValueError):s.SeasonalRequest(latitude=15.42,location_source='botolan_reference')


def test_synthetic_rehearsal_remains_visibly_separate():
    resp=C.post('/api/botolan/seasonal',json={'mode':'synthetic'})
    assert resp.status_code==200,resp.text
    result=resp.json()
    assert result['data_class']=='SYNTHETIC_REHEARSAL_NOT_NASA'
    assert result['provenance']['request_url'] is None
    assert result['provenance']['raw_payload_sha256'] is None
    assert result['provenance']['retrieved_at'] is None
    assert all(x['planting_authorized'] is False for x in result['candidates'])
    assert all(x['illustrative_et_c_mm'] is None for x in result['candidates'])
    assert all(x['historical_rain_mm'] for x in result['candidates'])


def test_stage_kc_source_proof_is_required_and_total_must_match():
    with pytest.raises(ValueError,match='HTTPS'):
        s.CropProfile(stages=[s.Stage(days=120,kc=1.0)])
    with pytest.raises(ValueError,match='must total'):
        s.SeasonalRequest(crop_profiles={'Rice':s.CropProfile(stages=[s.Stage(days=30,kc=1.0)],source_url='https://www.fao.org/')})


def test_crop_water_computed_only_with_all_necessary_user_coefficients():
    profiles={
        'Rice':{'stages':[{'days':30,'kc':0.8},{'days':60,'kc':1.15},{'days':30,'kc':0.9}], 'source_url':'https://www.fao.org/'},
        'Mungbean':{'stages':[{'days':75,'kc':0.8}],'source_url':'https://www.fao.org/'},
        'Corn':{'stages':[{'days':105,'kc':0.95}],'source_url':'https://www.fao.org/'},
    }
    request=s.SeasonalRequest(mode='synthetic',crop_profiles=profiles)
    res=s.compare(request,sample())
    assert all(x['illustrative_et_c_mm'] is not None for x in res['candidates'])
    assert all(x['valid_et_c_years']==10 for x in res['candidates'])
    assert res['candidates'][0]['illustrative_et_c_mm']['median']>0
    assert res['candidates'][1]['historical_rain_mm']['median']!=res['candidates'][0]['historical_rain_mm']['median']
    assert not res['validated_crop_recommendation']
    assert 'NOT a farm irrigation recommendation' in res['methodology']['water_balance']


def test_different_planting_month_changes_historical_exposure():
    data=sample()
    a=s.compare(req(planting_month=1),data)
    b=s.compare(req(planting_month=8),data)
    assert a['candidates'][0]['historical_rain_mm']['median']!=b['candidates'][0]['historical_rain_mm']['median']
    assert a['candidates'][0]['historical_eto_mm']['median']!=b['candidates'][0]['historical_eto_mm']['median']


def test_missing_day_withheld_no_zero_imputation_and_reject_invalid_data():
    raw=s.demo_daily()
    raw['properties']['parameter']['PRECTOTCORR']['20200620']=-999
    raw['properties']['parameter']['RH2M']['20200620']=-999
    parsed=s.parse_daily(raw,source_type='synthetic',retrieved_at=None,url=None,latitude=s.LAT,longitude=s.LON)
    outcome=s.compare(req(),parsed)
    rice=outcome['candidates'][0]
    assert rice['valid_rain_years']==9
    assert rice['valid_eto_years']==9
    assert rice['years'][5]['rain_mm'] is None
    assert rice['years'][5]['eto_mm'] is None
    assert parsed['rejected_or_missing_days_by_variable']['PRECTOTCORR']>=1
    assert parsed['rejected_or_missing_days_by_variable']['RH2M']>=1


def test_less_than_eight_complete_cohorts_blocks_distribution():
    raw=s.demo_daily()
    for year in range(2015,2020):
        raw['properties']['parameter']['PRECTOTCORR'][f'{year}0620']=-999
    data=s.parse_daily(raw,source_type='synthetic',retrieved_at=None,url=None,latitude=s.LAT,longitude=s.LON)
    out=s.compare(req(),data)
    assert out['candidates'][0]['valid_rain_years']==5
    assert out['candidates'][0]['historical_rain_mm'] is None


@pytest.mark.parametrize('variable,unit',[('PRECTOTCORR','mm/month'),('ALLSKY_SFC_SW_DWN','joules'),('PS','hPa')])
def test_bad_units_fail_closed(variable,unit):
    raw=s.demo_daily();raw['parameters'][variable]['units']=unit
    with pytest.raises(ValueError,match='unit'):
        s.parse_daily(raw,source_type='synthetic',retrieved_at=None,url=None,latitude=s.LAT,longitude=s.LON)


def test_nasa_receipt_requires_real_retrieval_meta_even_for_mock_payload():
    raw=s.demo_daily()
    with pytest.raises(ValueError,match='request URL'):
        s.parse_daily(raw,source_type='nasa_api',retrieved_at=None,url=None,latitude=s.LAT,longitude=s.LON)
    parsed=s.parse_daily(raw,source_type='nasa_api',retrieved_at='2026-11-15T00:00:00+00:00',
                         url=s.API+'?a=b',latitude=s.LAT,longitude=s.LON)
    assert parsed['raw_payload_sha256'] and len(parsed['raw_payload_sha256'])==64
    result=s.compare(s.SeasonalRequest(mode='nasa'),parsed)
    assert result['data_class']=='HISTORICAL_NASA_POWER'  # NASA-shaped fixture ONLY in tests; not real observations
    with pytest.raises(ValueError,match='Cannot label synthetic'):
        s.compare(s.SeasonalRequest(mode='nasa'),sample())


def test_fao_eto_physical_sanity_and_solar_conversion():
    # FAO-56 test of physical sanity; not a local station cross-validation.
    day={'T2M':26.0,'T2M_MAX':31.0,'T2M_MIN':21.0,'RH2M':65.0,'WS2M':2.0,'PS':100.0,'ALLSKY_SFC_SW_DWN':17.0}
    et=s.eto_fao56(day,15.289,0,date(2020,6,15))
    assert 2<et<8
    assert s.extraterrestrial_radiation(15.289,date(2020,6,15))>25
    assert s.eto_fao56({**day,'WS2M':None},15.289,0,date(2020,6,15)) is None
    raw=s.demo_daily();parsed=s.parse_daily(raw,source_type='synthetic',retrieved_at=None,url=None,latitude=s.LAT,longitude=s.LON)
    assert parsed['solar_conversion_to_mj_m2_day']==3.6
    assert parsed['days']['20150101']['ALLSKY_SFC_SW_DWN']>10


def test_api_fail_closed_not_nasa_fabrication(monkeypatch):
    async def down(_request):raise RuntimeError('NASA POWER seasonal data unavailable')
    monkeypatch.setattr(s,'retrieve',down)
    response=C.post('/api/botolan/seasonal',json={'mode':'nasa'})
    assert response.status_code==503
    assert 'NASA POWER' in response.json()['detail']
    assert 'SYNTHETIC' not in str(response.json())


def test_api_rejects_client_supplied_raw_weather_data():
    response=C.post('/api/botolan/seasonal',json={'mode':'synthetic','raw_payload':{'PRECTOTCORR':99999}})
    assert response.status_code==422


def test_field_check_outputs_track_reported_priorities_and_irrigation():
    synthetic=sample()
    water=s.compare(req(irrigation='none',soil='unknown',farmer_priority='conserve_water'),synthetic)
    soil=s.compare(req(irrigation='reliable',soil='clayey',soil_source='farmer_report',farmer_priority='soil_health'),synthetic)
    a=' '.join(water['candidates'][0]['farmer_field_checks']).lower()
    b=' '.join(soil['candidates'][0]['farmer_field_checks']).lower()
    assert 'measure irrigation' in a and 'soil texture' in a and 'water savings' in a
    assert 'confirm reliability' in b and 'organic matter' in b
    assert all(c['status']=='HISTORICAL_SCREENING_ONLY' for c in soil['candidates'])


def test_stage_kc_sensitivity_not_false_confidence_interval():
    profiles={'Rice':{'stages':[{'days':120,'kc':1.0}],'source_url':'https://www.fao.org/'}}
    q=req(crop_profiles=profiles)
    res=s.compare(q,sample())
    rich=res['candidates'][0]
    sensitivity=rich['kc_sensitivity_not_statistical_ci']
    assert sensitivity['median_et_c_if_kc_15pct_lower_mm']<rich['illustrative_et_c_mm']['median']
    assert sensitivity['median_et_c_if_kc_15pct_higher_mm']>rich['illustrative_et_c_mm']['median']
    assert 'not a Kc uncertainty estimate' in sensitivity['note']
    assert res['candidates'][1]['illustrative_et_c_mm'] is None


def test_fao56_example_18_reproduces_published_reference_with_equivalent_vapor_pressure():
    # FAO-56 Ch. 4 Example 18, Uccle, 6 July; published ET0 ≈3.9 mm/day.
    # RHmean 70.56% is derived from the example's ea=1.409 kPa / es=1.997 kPa.
    # It is NOT a measured NASA RH2M record. This tests the equation implementation.
    inputs={'T2M':16.9,'T2M_MAX':21.5,'T2M_MIN':12.3,'RH2M':70.56,
            'WS2M':2.078,'PS':100.1,'ALLSKY_SFC_SW_DWN':22.07}
    actual=s.eto_fao56(inputs,50.8,100,date(2020,7,6))
    assert abs(actual-3.88)<0.08

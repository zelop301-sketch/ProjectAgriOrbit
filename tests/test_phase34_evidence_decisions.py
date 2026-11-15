"""Phase 34: actual evidence-to-decision engine regressions.

The NOAA/PAGASA context and NASA POWER API are not forged for live mode;
mock payloads are ONLY used in unit tests and are not bundled as observations.
"""
import copy
import calendar
from pathlib import Path
from datetime import date

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.climate import synthetic_data
from app import field_decisions as d

C = TestClient(app)
R = Path(__file__).resolve().parents[1]


def nasa_monthly_fixture():
    p={'PRECTOTCORR':{},'T2M':{}}
    for year in range(1991,2021):
        for month in range(1,13):
            p['PRECTOTCORR'][f'{year}{month:02d}']=10.0
            p['T2M'][f'{year}{month:02d}']=29.0
    return {'properties':{'parameter':p},'parameters':{'PRECTOTCORR':{'units':'mm/day'},'T2M':{'units':'C'}}}


def reference():
    return d.parse_monthly(nasa_monthly_fixture(),source_type='nasa_api',timestamp='2026-11-15T00:00:00+00:00',url='https://power.larc.nasa.gov/api/temporal/monthly/point')


def target():
    x=synthetic_data(d.LAT,d.LON,2026)
    x['source_type']='nasa_api'
    x['request_url']='https://power.larc.nasa.gov/api/temporal/daily/point'
    for row in x['months'][:10]:
        row['precipitation_mm']=calendar.monthrange(2026,row['month'])[1]*7.0
    return x


def test_main_endpoints_and_navigation_assets():
    health=C.get('/api/health').json()
    assert health['build']==d.BUILD
    assert health['recommended_port']==8034
    assert '1991-2020-reference' in health['phase34_scientific_workflow']
    html=C.get('/').text
    assert 'id="b34-mission"' in html and 'id="b34-fetch"' in html
    assert '1991–2020 NASA POWER' in html
    assert 'field-decisions-ui.js' in html and 'phase34.css' in html
    assert html.index('b34-mission')<html.index('b33-action-bar')
    assert C.get('/assets/field-decisions-ui.js').status_code==200
    assert C.get('/assets/phase34.css').status_code==200
    assert 'launch_phase34.py' in (R/'START_AGRIORBIT_WINDOWS.cmd').read_text()
    assert 'PORT=8034' in (R/'scripts/launch_phase34.py').read_text()


def test_monthly_api_request_is_single_30year_history():
    params,url=d.monthly_request()
    assert params['start']=='1991' and params['end']=='2020'
    assert params['parameters']=='PRECTOTCORR,T2M'
    assert 'monthly/point?' in url
    assert '15.28900' in url and '120.02400' in url


def test_monthly_30year_conversion_with_leap_year_and_valid_years():
    ref=reference()
    assert ref['months'][0]['rain_years']==30
    assert ref['months'][1]['rain_mm_day']==10
    recent=target()
    x=d.build_evidence(recent,ref,mode='nasa')
    assert x['summary']['months_usable']==10
    assert -31<x['summary']['rain_departure_pct']<-29
    assert x['months'][1]['rain_reference_mm']==280  # 2026 February has 28 days
    assert x['months'][1]['rain_2026_mm']==196
    assert x['data_class']=='HISTORICAL_NASA_POWER'
    assert x['summary']['signal']=='BELOW_30Y_REFERENCE'
    assert len(x['provenance'])==2
    assert len(ref['raw_payload_sha256'])==64


def test_quality_gates_require_24_valid_years_and_no_invented_missing_values():
    raw=nasa_monthly_fixture()
    for year in range(1991,1998):
        raw['properties']['parameter']['PRECTOTCORR'][f'{year}04']=-999
    ref=d.parse_monthly(raw,source_type='nasa_api',timestamp='x',url='https://power.larc.nasa.gov/')
    assert ref['months'][3]['rain_years']==23
    assert ref['months'][3]['rain_mm_day'] is None
    result=d.build_evidence(target(),ref,mode='nasa')
    assert result['months'][3]['rain_reference_mm'] is None
    assert result['summary']['rain_departure_pct'] is None
    assert result['summary']['signal']=='INSUFFICIENT_EVIDENCE'


def test_target_month_below_95_coverage_withholds_full_2026_departure():
    t=target()
    t['months'][5]['coverage_pct_by_variable']['PRECTOTCORR']=94
    x=d.build_evidence(t,reference(),mode='nasa')
    assert x['summary']['months_usable']==9
    assert x['summary']['rain_departure_pct'] is None
    assert x['months'][5]['rain_2026_mm'] is None


@pytest.mark.parametrize('mutation',[
    lambda raw:raw.pop('parameters'),
    lambda raw:raw['parameters']['PRECTOTCORR'].update(units='mm/month'),
    lambda raw:raw['properties']['parameter'].pop('PRECTOTCORR'),
])
def test_unknown_monthly_units_and_shape_fail_closed(mutation):
    raw=nasa_monthly_fixture()
    mutation(raw)
    with pytest.raises(ValueError):
        d.parse_monthly(raw,source_type='nasa_api',timestamp='x',url='u')


def test_synthetic_is_separate_from_nasa_and_does_not_forge_nasa_url():
    resp=C.post('/api/botolan/decision',json={'mode':'synthetic'})
    assert resp.status_code==200,resp.text
    result=resp.json()
    e=result['evidence'];s=result['screening']
    assert e['data_class']=='SYNTHETIC_REHEARSAL_NOT_NASA'
    assert e['summary']['months_usable']==10
    assert all(p['request_url'] is None and p['source_type']=='synthetic' for p in e['provenance'])
    assert all(c['planting_authorized'] is False and c['validated_suitability'] is False for c in s['candidates'])
    assert not s['decision_ready'] and not s['ranked']
    assert not s['quality_gates'][0]['passed']
    assert 'SYNTHETIC' in ' '.join(e['warnings'])


def test_farm_irrigation_changes_scientific_review_flags():
    t,r=d.simulated_inputs()
    e=d.build_evidence(t,r,mode='synthetic')
    a=d.make_screening(e,d.FarmContext(irrigation='none'))
    b=d.make_screening(e,d.FarmContext(irrigation='reliable'))
    f1=[f['label'] for f in a['candidates'][0]['flags'] if f['type']=='water']
    f2=[f['label'] for f in b['candidates'][0]['flags'] if f['type']=='water']
    assert f1!=f2
    assert 'TWO PADDY CYCLES' in f1[0]
    assert 'REPORTED' in f2[0]
    assert all(c['status']=='FIELD_REVIEW_REQUIRED' for c in a['candidates'])


def test_actual_historical_dry_context_changes_review_flags():
    no_alert=d.build_evidence(target(),reference(),mode='nasa')
    assert no_alert['summary']['signal']=='BELOW_30Y_REFERENCE'
    wet=target()
    for row in wet['months'][:10]:
        row['precipitation_mm']=calendar.monthrange(2026,row['month'])[1]*10
    neutral=d.build_evidence(wet,reference(),mode='nasa')
    a=d.make_screening(no_alert,d.FarmContext())
    b=d.make_screening(neutral,d.FarmContext())
    assert any(f['type']=='climate' for f in a['candidates'][0]['flags'])
    assert not any(f['type']=='climate' for f in b['candidates'][0]['flags'])
    assert a['quality_gates'][0]['passed'] and b['quality_gates'][0]['passed']
    assert a['decision_ready'] is False


def test_soil_lab_claim_does_not_authorize_planting():
    e=d.build_evidence(*d.simulated_inputs(),mode='synthetic')
    s=d.make_screening(e,d.FarmContext(soil='clayey',soil_ph=4.5,soil_source='laboratory'))
    assert s['quality_gates'][2]['passed']
    assert 'self-attested' in s['quality_gates'][2]['name'].lower()
    assert not s['decision_ready']
    assert all(c['planting_authorized'] is False for c in s['candidates'])


def test_user_entered_crop_rule_is_self_attested_not_authenticity_proof():
    e=d.build_evidence(*d.simulated_inputs(),mode='synthetic')
    context=d.FarmContext(soil='sandy',soil_ph=4.5,soil_source='laboratory',crop_rules=[{
        'crop':'Rice','ph_min':5.5,'ph_max':7.0,'source_url':'https://example.org/field-reviewed',
        'reviewed_by':'Demo Reviewer','reviewed_on':'2026-11-15','minimum_irrigation':'reliable',
    }])
    screen=d.make_screening(e,context)
    rice_flags=' '.join(x['label'] for x in screen['candidates'][0]['flags'])
    assert 'PH CONFLICT' in rice_flags and 'WATER-RULE CONFLICT' in rice_flags
    assert screen['quality_gates'][3]['passed'] is False
    assert screen['decision_ready'] is False


def test_rejects_forged_nasa_and_mixed_sources():
    a,b=d.simulated_inputs()
    with pytest.raises(ValueError,match='Unverified source'):
        d.build_evidence(a,b,mode='nasa')
    with pytest.raises(ValueError,match='Synthetic rehearsal'):
        d.build_evidence(target(),reference(),mode='synthetic')
    bad=C.post('/api/botolan/decision',json={'mode':'synthetic','farm':{'irrigation':'none','soil_ph':16}})
    assert bad.status_code==422
    forged=C.post('/api/botolan/decision',json={'mode':'synthetic','nasa_raw_payload':{'value':-10}})
    assert forged.status_code==200  # ignored by Pydantic, NEVER treated as observational provenance
    assert forged.json()['evidence']['data_class']=='SYNTHETIC_REHEARSAL_NOT_NASA'


def test_nasa_failure_does_not_silently_switch_modes(monkeypatch):
    async def down(**kwargs):raise RuntimeError('NASA POWER unavailable')
    monkeypatch.setattr('app.field_decisions.fetch_reference',down)
    monkeypatch.setattr('app.field_decisions.fetch_2026',down)
    response=C.post('/api/botolan/decision',json={'mode':'nasa'})
    assert response.status_code==503
    assert 'NASA POWER unavailable' in response.json()['detail']
    assert 'synthetic' not in response.json()['detail'].lower()


def test_js_requests_only_server_context_and_exposes_report():
    js=(R/'web/field-decisions-ui.js').read_text()
    assert "fetch('/api/botolan/decision'" in js
    assert "No synthetic fallback occurred." in js
    assert 'AgriORBIT_Phase34_Botolan_Evidence_Report.md' in js
    assert 'new URL(p.request_url)' in js
    assert 'window.AgriOrbitPhase34' in js

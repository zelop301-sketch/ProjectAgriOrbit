"""Judge-critical Phase 42 gates: original visual preservation, safe climate evidence labels."""
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import seasonal_science as ss

ROOT = Path(__file__).resolve().parents[1]
client=TestClient(app)


def _data():
    return ss.parse_daily(ss.demo_daily(),source_type='synthetic',retrieved_at=None,
                          url=None,latitude=ss.LAT,longitude=ss.LON)


def test_science_navigation_uses_valid_url_and_asset_is_loaded():
    page=client.get('/science')
    assert page.status_code==200
    assert 'href="/?force-15=1#botolan"' in page.text
    assert 'href="/ ?force-15=1#botolan"' not in page.text
    assert 'src="/assets/science-phase42-ui.js"' in page.text
    script=client.get('/assets/science-phase42-ui.js')
    assert script.status_code==200
    assert 'rotation-card' in script.text
    assert 'idealized_rain_offset_shortfall_mm' not in script.text


def test_original_mission_control_unchanged_and_3d_files_present():
    assert client.get('/').status_code==200
    for name in ('rover3d.js','app.js','seedling-boot.js','agriorbit-boot-storyboard-15s.gif',
                 'mission-farm-clean-v20.jpg','agriorbit-living-core-fast.webp'):
        assert (ROOT/'web'/name).is_file()


def test_normalized_rain_eto_and_dry_spell_are_reported_but_not_ranked():
    q=ss.SeasonalRequest(mode='synthetic')
    result=ss.compare(q,_data())
    assert result['version']=='phase42-judge-science-patch'
    assert len(result['candidates'])==3
    assert result['validated_crop_recommendation'] is False
    for candidate in result['candidates']:
        assert candidate['crop_days_per_rotation']>=140
        assert candidate['historical_rain_mm_per_crop_day']['median']>0
        assert candidate['historical_eto_mm_per_crop_day']['median']>0
        assert candidate['historical_longest_dry_spell_days_lt_1mm']['median']>=0
        assert candidate['illustrative_et_c_mm'] is None
        assert candidate['status']=='HISTORICAL_SCREENING_ONLY'
        assert len(candidate['years'])==10
        for year in candidate['years']:
            if year['rain_mm'] is not None:
                assert abs(year['rain_mm_per_crop_day'] * year['crop_days'] - year['rain_mm'])<.2
    assert 'normalised mm per occupied crop day' in result['methodology']['weather_summary']


def test_dry_spell_breaks_across_fallow_gap_and_rejects_gaps():
    days=[date(2020,6,1)+timedelta(days=d) for d in (0,1,2,8,9)]
    assert ss._longest_dry_spell(days,[0,0,0,0,0])==3
    assert ss._longest_dry_spell(days,[0,0,0,None,0]) is None
    assert ss._longest_dry_spell(days,[1,0,0,0,1])==2


def test_crop_coefficient_link_is_only_syntactically_checked():
    for invalid in ('https://','https://localhost/test','http://www.fao.org/kc',
                    'https://user:password@www.fao.org/', 'https://www.fao.org:1234/path'):
        with pytest.raises(ValueError,match='HTTPS'):
            ss.CropProfile(stages=[ss.Stage(days=120,kc=1.1)],source_url=invalid)
    p=ss.CropProfile(stages=[ss.Stage(days=120,kc=1.1)],source_url='https://www.fao.org/4/x0490e/x0490e0b.htm',
                     source_title='FAO-56 crop coefficient chapter',source_publisher='FAO',crop_variety='unspecified')
    assert p.source_title.startswith('FAO')


def test_kc_provenance_retains_source_but_never_asserts_verification():
    q=ss.SeasonalRequest(mode='synthetic',crop_profiles={
        'Rice':{'stages':[{'days':120,'kc':1.1}],
                'source_url':'https://www.fao.org/4/x0490e/x0490e0b.htm',
                'source_title':'Provided source (test)', 'source_publisher':'Researcher reported'}
    })
    data=ss.compare(q,_data())
    rice=data['candidates'][0]['kc_provenance']['Rice']
    assert rice['status']=='USER_SUPPLIED_UNVERIFIED'
    assert rice['local_stage_applicability_verified'] is False
    assert rice['source_title']=='Provided source (test)'
    assert data['candidates'][0]['illustrative_et_c_mm'] is not None
    assert data['candidates'][1]['illustrative_et_c_mm'] is None
    assert 'NOT checked' in data['limitations'][-2] or any('NOT checked' in x for x in data['limitations'])


def test_incomplete_data_withholds_all_affected_metrics():
    raw=ss.demo_daily()
    for year in range(2015,2020):
        raw['properties']['parameter']['PRECTOTCORR'][f'{year}0620']=-999
    sample=ss.parse_daily(raw,source_type='synthetic',retrieved_at=None,url=None,
                          latitude=ss.LAT,longitude=ss.LON)
    result=ss.compare(ss.SeasonalRequest(mode='synthetic'),sample)
    a=result['candidates'][0]
    assert a['historical_rain_mm'] is None
    assert a['historical_rain_mm_per_crop_day'] is None
    assert a['historical_longest_dry_spell_days_lt_1mm'] is None
    assert a['historical_eto_mm_per_crop_day'] is not None


def test_original_and_new_science_routes_keep_demo_separate():
    res=client.post('/api/botolan/seasonal',json={'mode':'synthetic'})
    assert res.status_code==200
    o=res.json()
    assert o['provenance']['request_url'] is None
    assert o['provenance']['raw_payload_sha256'] is None
    assert o['data_class']=='SYNTHETIC_REHEARSAL_NOT_NASA'
    assert client.get('/api/health').json()['boot_duration_seconds']==15

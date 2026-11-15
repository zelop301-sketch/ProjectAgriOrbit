"""Checks based on the user-supplied November 13, 2026 guide."""
from fastapi.testclient import TestClient
from app.main import app
from app.spaceapps import SubmissionDraft, audit_draft, GUIDE

client = TestClient(app)


def test_guide_five_criteria_and_demo_limits():
    guide = client.get('/api/spaceapps/guide')
    assert guide.status_code == 200
    d = guide.json()
    assert d['guide_date'] == '2026-11-13'
    assert [x['name'] for x in d['scoring']['criteria']] == ['Impact', 'Creativity', 'Validity', 'Relevance', 'Presentation']
    assert d['demo']['slide_limit'] == 7 and d['demo']['video_seconds_limit'] == 30
    assert d['scoring']['max'] == 5


def test_baseline_self_report_is_not_nasa_certification():
    a = client.post('/api/spaceapps/audit', json={}).json()
    assert a['status'] == 'self_reported_checklist_only'
    assert not a['all_self_reported']
    assert a['passed'] < a['total']
    assert 'NOT independently verified' in a['disclaimer']


def test_team_size_rules_local_and_universal():
    local = audit_draft(SubmissionDraft(event_type='local', team_size=1))
    universal = audit_draft(SubmissionDraft(event_type='universal', team_size=1))
    too_many = audit_draft(SubmissionDraft(event_type='local', team_size=7))
    by_id=lambda a: {x['id']:x['pass'] for x in a['checks']}
    assert by_id(local)['team_size'] is True
    assert by_id(universal)['team_size'] is False
    assert by_id(too_many)['team_size'] is False


def test_seven_slide_demo_limit():
    for n,valid in [(0,False),(7,True),(8,False)]:
        result=audit_draft(SubmissionDraft(demo_format='slides', slide_count=n))
        assert next(x['pass'] for x in result['checks'] if x['id']=='demo') is valid


def test_30_second_video_limit_and_english_subtitles():
    for sec,valid in [(0,False),(30,True),(30.1,False)]:
        r=audit_draft(SubmissionDraft(demo_format='video', video_seconds=sec))
        assert next(x['pass'] for x in r['checks'] if x['id']=='demo') is valid
    r=audit_draft(SubmissionDraft(demo_format='video',video_seconds=20,video_spoken_english=False,video_english_subtitles=False))
    assert next(x['pass'] for x in r['checks'] if x['id']=='subtitles') is False
    r=audit_draft(SubmissionDraft(demo_format='video',video_seconds=20,video_spoken_english=False,video_english_subtitles=True))
    assert next(x['pass'] for x in r['checks'] if x['id']=='subtitles') is True


def test_references_require_manual_review_and_nonempty_list():
    r=audit_draft(SubmissionDraft(references=['NASA POWER: https://power.larc.nasa.gov/'], references_verified=False))
    assert next(x['pass'] for x in r['checks'] if x['id']=='references') is False
    r=audit_draft(SubmissionDraft(references=['NASA POWER: https://power.larc.nasa.gov/'], references_verified=True))
    assert next(x['pass'] for x in r['checks'] if x['id']=='references') is True


def test_all_checked_is_still_manual_and_unverified():
    payload={
        'team_size':2,'event_type':'universal','registered_same_event':True,'members_tab_complete':True,
        'official_challenge':True,'fields_complete':True,'materials_english':True,
        'demo_format':'video','video_seconds':30,'video_spoken_english':True,
        'references':['NASA POWER source'], 'references_verified':True,
        'copyright_permissions_confirmed':True,'originality_attested':True,
        'terms_privacy_attested':True,'submitted_on_time':True
    }
    result=client.post('/api/spaceapps/audit',json=payload).json()
    assert result['passed']==result['total'] and result['all_self_reported']
    assert result['status']=='self_reported_checklist_only'
    assert 'Scientific validity of agronomic scores' in result['unverified']


def test_invalid_audit_is_422_not_trusted():
    assert client.post('/api/spaceapps/audit',json={'team_size':-2}).status_code==422
    assert client.post('/api/spaceapps/audit',json={'demo_format':'photo'}).status_code==422


def test_navigation_and_assets_served():
    html=client.get('/').text
    assert html.count('data-view="guidelines"')==2
    assert 'id="view-guidelines"' in html
    assert 'Global Judging eligibility' in html
    assert 'sa-references' in html
    assert client.get('/assets/spaceapps-ui.js').status_code==200
    js=client.get('/assets/app.js').text
    assert "'guidelines':'NASA Guidelines'" in js
    assert 'phase34-botolan-evidence-decisions' in client.get('/api/health').json()['build']

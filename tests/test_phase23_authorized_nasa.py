"""Behavior tests: authorization is external; mocked NASA records are not real-world evidence."""
import hashlib
import json
import math
from fastapi.testclient import TestClient
from fastapi import HTTPException
import pytest
from unittest.mock import AsyncMock

from app.main import app
from app import phase23_integrations as p23
from app.climate import summarise

client=TestClient(app)


def test_capabilities_and_build_status():
    assert client.get('/api/health').json()['build']=='phase34-botolan-evidence-decisions-3.4.0'
    assert client.get('/api/health').json()['recommended_port']==8034
    capabilities=client.get('/api/phase23/capabilities').json()
    assert capabilities['official_layer_included'] is False
    assert capabilities['live_nasa_request_supported'] is True
    assert capabilities['bundled_nasa_observations'] is False


def test_private_review_does_not_authorize():
    result=client.post('/api/phase23/phivolcs/permission-review',json={}).json()
    assert result['official_approval_granted_by_app'] is False
    assert result['public_distribution_approved'] is False
    assert result['status']=='local_private_preview_only_pending_agreement'


def test_signed_agreement_self_report_still_not_official():
    body={'intended_use':'team_internal_analysis','signed_agreement_attested':True,
          'agreement_reference':'USER-DESCRIBED-REF'}
    result=client.post('/api/phase23/phivolcs/permission-review',json=body).json()
    assert result['user_reports_agreement'] is True
    assert result['official_approval_granted_by_app'] is False
    assert 'not_verified' in result['status']


def test_reference_alone_is_not_accepted_as_signed():
    result=client.post('/api/phase23/phivolcs/permission-review',json={'agreement_reference':'X'}).json()
    assert not result['user_reports_agreement']


def test_public_use_without_permission_is_explicitly_blocked():
    result=client.post('/api/phase23/phivolcs/permission-review',json={'intended_use':'public_redistribution'}).json()
    assert result['status']=='public_use_blocked_pending_agency_permission'
    assert result['public_distribution_approved'] is False


def test_public_redistribution_attestation_is_not_official():
    result=client.post('/api/phase23/phivolcs/permission-review',json={
        'intended_use':'public_redistribution',
        'signed_agreement_attested':True,
        'agreement_reference':'USER-REF',
        'explicit_redistribution_permission_attested':True}).json()
    assert result['status']=='user_attests_explicit_public_rights_not_verified'
    assert not result['public_distribution_approved']


def test_invalid_permission_purpose_fails():
    result=client.post('/api/phase23/phivolcs/permission-review',json={'intended_use':'automatic_official_approval'})
    assert result.status_code==422


def test_nasa_endpoint_rejects_synthetic_response(monkeypatch):
    monkeypatch.setattr(p23,'fetch_climate',AsyncMock(return_value={'source_type':'synthetic'}))
    result=client.get('/api/phase23/nasa/observations?year=2025')
    assert result.status_code==503
    assert 'Synthetic' in result.json()['detail']


def test_nasa_endpoint_errors_on_unavailable_network(monkeypatch):
    monkeypatch.setattr(p23,'fetch_climate',AsyncMock(side_effect=RuntimeError('NASA offline')))
    response=client.get('/api/phase23/nasa/observations?year=2025')
    assert response.status_code==503
    assert 'NASA offline' in response.json()['detail']


def test_nasa_json_receipt_from_mocked_official_payload(tmp_path,monkeypatch):
    # This is a controlled test fixture, NOT a downloaded NASA measurement.
    year=2025
    param={code:{} for code in ('T2M','PRECTOTCORR','ALLSKY_SFC_SW_DWN')}
    for day in range(1,6):
        key=f'202501{day:02d}'
        param['T2M'][key]=25.
        param['PRECTOTCORR'][key]=float(day)
        param['ALLSKY_SFC_SW_DWN'][key]=4.5
    raw={'properties':{'parameter':param}}
    checksum=hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    entry=tmp_path/'cached.json'
    entry.write_text(json.dumps({'fetched_at':'2026-11-14T00:00:00+00:00','raw':raw}),encoding='utf8')
    monkeypatch.setattr(p23,'cache_path',lambda lat,lon,year:entry)
    result=summarise(raw,15.289,120.024,year,'nasa_api','2026-11-14T00:00:00+00:00',
                     'https://power.larc.nasa.gov/api/temporal/daily/point?test=1')
    monkeypatch.setattr(p23,'fetch_climate',AsyncMock(return_value=result))
    response=client.get('/api/phase23/nasa/observations?include_daily=true')
    assert response.status_code==200,response.text
    doc=response.json()
    assert doc['data_class']=='historical_nasa'
    assert doc['metadata']['raw_payload_sha256']==checksum
    assert doc['metadata']['source_type']=='nasa_api'
    assert doc['daily_records']==5 and len(doc['daily'])==5
    assert doc['annual_quality_gate']['annual_precipitation_ready'] is False
    assert doc['annual_summary']['annual_precipitation_mm'] is None
    assert doc['daily'][0]['PRECTOTCORR']==1.0


def test_nasa_digest_mismatch_is_safe_error(tmp_path,monkeypatch):
    entry=tmp_path/'cached.json';entry.write_text('{"raw":{}}',encoding='utf8')
    monkeypatch.setattr(p23,'cache_path',lambda lat,lon,year:entry)
    monkeypatch.setattr(p23,'fetch_climate',AsyncMock(return_value={
        'source_type':'nasa_cached','raw_payload_sha256':'0'*64}))
    response=client.get('/api/phase23/nasa/observations')
    assert response.status_code==503
    assert 'cache' in response.json()['detail'].lower()


def test_ui_and_source_assets_are_served():
    for url in ['/', '/assets/phase23-ui.js','/assets/phase23.css']:
        assert client.get(url).status_code==200
    html=client.get('/').text
    assert 'id="p23-fetch-nasa"' in html and 'id="p23-check-rights"' in html
    assert 'phase34-botolan-evidence-decisions-3.4.0' in html
    assert 'port 8022' not in html.lower()

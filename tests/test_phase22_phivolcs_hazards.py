"""Synthetic polygons only. Tests do not assert actual PHIVOLCS exposure."""
from io import BytesIO
import json
import zipfile
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.main import app
from app.hazards import HazardScreenRequest, DEMO_FARM, DEMO_HAZARDS, screen_hazard, HazardSource
from scripts.convert_hazard_kmz import convert_file,convert_kml

client=TestClient(app)

def payload(layer=DEMO_HAZARDS):
    return {'farm_geometry':DEMO_FARM,'hazard_geojson':layer,
            'source':{'title':'FICTIONAL TEST ZONE','use_permission':'not_checked'},'climate_mode':'none'}


def test_demo_layer_is_explicitly_fictional():
    r=client.get('/api/hazards/demo');assert r.status_code==200
    assert r.json()['official_phivolcs_data'] is False
    assert 'FICTIONAL' in str(r.json()['hazard_geojson'])


def test_mapped_overlap_is_clipped_not_a_disaster_prediction():
    r=client.post('/api/hazards/screen',json=payload())
    assert r.status_code==200,r.text
    d=r.json()
    assert d['status']=='mapped_overlap_detected'
    assert 40 < d['mapped_overlap_percent'] < 60
    assert d['no_lahar_prediction'] is True and d['no_safety_certification'] is True
    assert d['climate_independent_of_hazard'] is True
    assert d['clipped_overlays']['features']
    assert all('USER-SUPPLIED' in f['properties']['source_status'] for f in d['clipped_overlays']['features'])
    assert not d['nasa_climate_context']['data_class'] == 'historical_nasa'


def test_no_overlap_does_not_mean_no_hazard():
    layer={'type':'Polygon','coordinates':[[[120.05,15.31],[120.051,15.31],[120.051,15.312],[120.05,15.312],[120.05,15.31]]]}
    d=client.post('/api/hazards/screen',json=payload(layer)).json()
    assert d['status']=='no_overlap_in_supplied_layers'
    assert d['mapped_overlap_percent']==0
    assert any('not proof' in s.lower() or 'cannot establish safety' in s.lower() for s in d['flags'])


def test_no_map_is_unknown_not_zero():
    d=client.post('/api/hazards/screen',json={'farm_geometry':DEMO_FARM}).json()
    assert d['status']=='not_assessed_no_map'
    assert d['mapped_overlap_percent'] is None
    assert 'UNKNOWN' in str(d['flags'])


def test_missing_map_date_and_license_are_flagged():
    d=screen_hazard(HazardScreenRequest(**payload()))
    assert any('permission' in f.lower() for f in d['flags'])
    assert any('revision date' in f.lower() for f in d['flags'])
    assert d['provenance'].startswith('USER_SUPPLIED')


def test_bad_polygon_and_wrong_crs_are_rejected():
    bowtie={'type':'Polygon','coordinates':[[[120.02,15.28],[120.026,15.29],[120.02,15.29],[120.026,15.28],[120.02,15.28]]]}
    assert client.post('/api/hazards/screen',json=payload({'type':'Feature','geometry':bowtie,'properties':{}})).status_code==422
    custom={**DEMO_FARM,'crs':{'type':'name','properties':{'name':'EPSG:3857'}}}
    assert client.post('/api/hazards/screen',json={**payload(),'farm_geometry':custom}).status_code==422


def test_unknown_source_cannot_claim_license():
    d=client.post('/api/hazards/screen',json={**payload(),'source':{'title':'Test hazard','source_url':'https://example.org/map',
                                                                    'use_permission':'permission_confirmed_by_user'}}).json()
    assert any('not a recognized PHIVOLCS' in x for x in d['flags'])
    assert d['provenance'].startswith('USER_SUPPLIED')


def test_farm_profile_must_be_inside_field():
    d={**payload(),'farm':{'latitude':15.22,'longitude':120.024}}
    assert client.post('/api/hazards/screen',json=d).status_code==422


def test_synthetic_nasa_context_stays_synthetic():
    d={**payload(),'farm':{'latitude':15.289,'longitude':120.024},'climate_mode':'synthetic'}
    r=client.post('/api/hazards/screen',json=d)
    assert r.status_code==200,r.text
    climate=r.json()['nasa_climate_context']
    assert climate['data_class'] != 'historical_nasa'
    assert climate['rainfall_anomaly_pct'] is None
    assert 'NOT a real-time lahar' in climate['note']


def test_kmz_polygon_converter(tmp_path):
    kml=b'''<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark><name>Example only</name><Polygon><outerBoundaryIs><LinearRing><coordinates>120.0,15.0,0 120.1,15.0,0 120.1,15.1,0 120.0,15.1,0</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></Document></kml>'''
    z=tmp_path/'local.kmz'
    with zipfile.ZipFile(z,'w') as out:out.writestr('doc.kml',kml)
    result=convert_file(z)
    assert len(result['features'])==1
    ring=result['features'][0]['geometry']['coordinates'][0]
    assert ring[0]==ring[-1]
    assert result['features'][0]['properties']['imported_from'].startswith('local')


def test_no_kmz_network_entity():
    try:convert_kml(b'<!DOCTYPE kml SYSTEM "http://example.net/evil.dtd"><kml/>')
    except ValueError:pass
    else:raise AssertionError('unsafe DTD should fail')


def test_new_tab_asset_routes_and_build():
    assert client.get('/assets/hazards-ui.js').status_code==200
    assert client.get('/assets/hazards.css').status_code==200
    h=client.get('/api/health').json()
    assert h['build']=='phase34-botolan-evidence-decisions-3.4.0'
    assert h['recommended_port']==8034
    text=client.get('/').text
    assert 'id="view-hazards"' in text
    assert text.count('data-view="hazards"')==2
    assert client.get('/api/hazards/capabilities').json()['official_hazard_map_included'] is False

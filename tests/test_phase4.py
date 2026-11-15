from fastapi.testclient import TestClient
from app.main import app
from app.environment import EnvironmentRequest, environment_exposure
from app.scoring import Farm

client=TestClient(app)
FARM={
 'name': 'Demo plot', 'latitude': 15.289, 'longitude': 120.024, 'area_ha': 1,
 'texture':'unknown','irrigation':'limited','current_crop':'Rice','start_month':6,
 'soil_source':'farmer_entered','priorities':{'water':5,'soil_cover':5,'diversity':5,'affordability':5,'simplicity':5}
}
def test_earth_registry_is_honest():
 r=client.get('/api/earth/sources');assert r.status_code==200
 d={x['id']:x for x in r.json()['datasets']}
 assert set(d)=={'nasa_power','modis','landsat','ecostress','nasa_hls'}
 assert d['nasa_power']['integration']=='live_point_api'
 assert all(d[k]['status']=='NOT_INGESTED' for k in ('modis','landsat','ecostress'))

def test_environment_synthetic_units_and_control_effect():
 data={'farm':FARM,'scenario':'B','weather':'drought','irrigation_percent':0,'drainage_percent':25}
 dry=client.post('/api/mission/environment',json=data);assert dry.status_code==200
 assert dry.json()['validated'] is False
 assert dry.json()['source_type']=='hypothetical_model'
 assert len(dry.json()['zones'])==3
 data['irrigation_percent']=100
 irrigation=client.post('/api/mission/environment',json=data)
 assert irrigation.json()['average_stress_index']<dry.json()['average_stress_index']
 data['weather']='surge';data['drainage_percent']=0
 wet=client.post('/api/mission/environment',json=data)
 assert wet.status_code==200
 assert wet.json()['rainfall_multiplier']==1.65
 assert any(z['excess_water_index']>0 for z in wet.json()['zones'])

def test_environment_rejects_unknown_input():
 r=client.post('/api/mission/environment',json={'farm':FARM,'weather':'actual_future_forecast'})
 assert r.status_code==422

def test_rover_endpoints_never_claim_hardware_control():
 model=client.get('/api/mission/rover-model').json()
 assert model['hardware_connected'] is False
 assert model['autonomous_control']=='disabled'
 sim=client.get('/api/mission/simulate?progress=0.5').json()
 assert sim['source_type']=='simulated'
 assert sim['navigation']['lidar_connected'] is False
 assert sim['payload']['hyperspectral']['source_type']=='planned'

def test_ui_has_interactive_renderer_and_controls():
 page=client.get('/').text
 for id in ('holo-viewport','holo-play','env-weather','env-overlay','env-light','env-irrigation','env-drainage','env-zones'):
  assert f'id="{id}"' in page
 for file in ('rover3d.js','mission-ui.js','app.js'):
  assert client.get('/assets/'+file).status_code==200

def test_catalog_metadata_route_does_not_invent_raster(monkeypatch):
 import app.main as main_module
 async def fake(product, latitude, longitude, year):
  return {'product':product,'source_type':'nasa_catalog_metadata','raster_pixels_ingested':False,'field_values_verified':False,'granules':[]}
 monkeypatch.setattr(main_module, 'search_granules', fake)
 r=client.get('/api/earth/granules?product=modis&lat=15.289&lon=120.024&year=2025')
 assert r.status_code==200 and r.json()['raster_pixels_ingested'] is False
 assert client.get('/api/earth/granules?product=unsupported').status_code==422


def test_catalog_fails_closed(monkeypatch):
 import app.main as main_module
 async def broken(*args):
  raise RuntimeError('catalog offline')
 monkeypatch.setattr(main_module, 'search_granules', broken)
 r=client.get('/api/earth/granules?product=ecostress')
 assert r.status_code==503
 assert 'offline' in r.json()['detail']

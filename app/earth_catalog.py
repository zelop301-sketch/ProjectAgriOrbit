"""Optional metadata-only NASA Earthdata CMR granule discovery.

A granule search is not raster download, cloud-mask processing, validation,
vegetation measurement, evapotranspiration analysis or field-specific QA.
"""
from __future__ import annotations
from datetime import date
from typing import Literal
import httpx

CMR_URL = 'https://cmr.earthdata.nasa.gov/search/granules.json'
DATASETS = {
    'hls_l30': {'short_name': 'HLSL30', 'version': '2.0', 'provider': 'NASA HLS Landsat L30 v2.0', 'resolution_note': '30 m surface reflectance: QA-masked reflectance, not field crop diagnosis.'},
    'hls_s30': {'short_name': 'HLSS30', 'version': '2.0', 'provider': 'NASA HLS Sentinel S30 v2.0', 'resolution_note': '30 m surface reflectance: mask clouds, shadows, water; ensure field valid pixels.'},
    'modis': {'short_name': 'MOD13Q1', 'version': '061', 'provider': 'NASA MODIS NDVI/EVI', 'resolution_note': 'Moderate-resolution 16-day composites; field pixel suitability requires QA.'},
    'ecostress': {'short_name': 'ECO_L3T_JET', 'version': '002', 'provider': 'NASA ECOSTRESS evapotranspiration', 'resolution_note': 'Irregular overpasses, clouds and quality masks limit usable scenes.'},
}

async def search_granules(product: Literal['modis', 'ecostress', 'hls_l30', 'hls_s30'], latitude: float, longitude: float, year: int=2025):
    if product not in DATASETS:
        raise ValueError('Unsupported product')
    ds=DATASETS[product]
    lat0=max(-90,latitude-.012);lat1=min(90,latitude+.012)
    lon0=max(-180,longitude-.012);lon1=min(180,longitude+.012)
    params={
        'short_name': ds['short_name'], 'version': ds['version'],
        'bounding_box': f'{lon0:.5f},{lat0:.5f},{lon1:.5f},{lat1:.5f}',
        'temporal': f'{year}-01-01T00:00:00Z,{year}-12-31T23:59:59Z',
        'page_size':3,'sort_key':'-start_date',
    }
    async with httpx.AsyncClient(timeout=12, follow_redirects=False) as client:
        try:
            resp=await client.get(CMR_URL,params=params,headers={'Accept':'application/json'})
            resp.raise_for_status()
            entries=resp.json().get('feed',{}).get('entry',[])
        except (httpx.HTTPError,ValueError,KeyError) as exc:
            raise RuntimeError('NASA CMR metadata lookup unavailable; raster ingestion has not been performed') from exc
    return {
        'product':product, 'provider':ds['provider'], 'source_type':'nasa_catalog_metadata',
        'raster_pixels_ingested':False, 'field_values_verified':False,
        'granules': [{'id':str(e.get('id',''))[:150], 'title':str(e.get('title',''))[:180],
                      'time_start':e.get('time_start'), 'time_end':e.get('time_end')} for e in entries],
        'search_center':{'latitude':latitude,'longitude':longitude},
        'query_year':year, 'search_spatial_note':'Point +/- 0.012 degrees for catalog discovery, not a surveyed farm footprint.',
        'scientific_note':ds['resolution_note'],
        'warning':'Catalog metadata only. This endpoint does NOT download or process NDVI, thermal or ET pixels; use the optional HLS local COG tool for QA-masked raster statistics.',
        'catalog_endpoint':CMR_URL,
    }

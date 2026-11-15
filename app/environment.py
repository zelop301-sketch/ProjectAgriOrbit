"""Explicitly hypothetical climate / irrigation exposure screening for a procedural 3D farm.

No claim of actual hydrology, crop yield, real ET, farm DEM, weather prediction, or
remote sensing raster ingestion. Values are dimensionless visualization indices.
"""
from __future__ import annotations
import math
from typing import Literal
from pydantic import BaseModel, Field
from .scoring import Farm

class EnvironmentRequest(BaseModel):
    farm: Farm
    scenario: Literal['A', 'B', 'C'] = 'B'
    weather: Literal['normal', 'drought', 'surge'] = 'normal'
    irrigation_percent: int = Field(default=35, ge=0, le=100)
    drainage_percent: int = Field(default=35, ge=0, le=100)
    day_phase: Literal['day', 'night'] = 'day'


def environment_exposure(inp: EnvironmentRequest) -> dict:
    """Deterministic hypothetical 3-zone response, not scientific forecast.

    Indices 0..100 denote relative exposure under the chosen assumptions.
    Irrigation and drainage are abstract management intensity knobs, not litres.
    """
    rain_multiplier = {'normal': 1.0, 'drought': .55, 'surge': 1.65}[inp.weather]
    crop_factor = {'A': 1.08, 'B': .90, 'C': .82}[inp.scenario]
    water = inp.irrigation_percent / 100
    drain = inp.drainage_percent / 100
    shortage_base = (44 + (1-rain_multiplier)*68 - water*29) * crop_factor
    excess_base = (16 + max(0, rain_multiplier-1)*91 - drain*31) * crop_factor
    zones = []
    for i, bias in enumerate([1.0, 1.18, .83]):
        deficit = min(100, max(0, round(shortage_base*bias)))
        excess = min(100, max(0, round(excess_base*(1.13 if i==2 else bias))))
        stress = max(deficit, excess)
        zones.append({'id': f'Z{i+1}', 'water_deficit_index': deficit, 'excess_water_index': excess,
                      'stress_index': stress, 'health_band': 'critical' if stress >= 67 else 'moderate' if stress >= 36 else 'lower_exposure',
                      'source_type': 'hypothetical_model'})
    return {
        'source_type': 'hypothetical_model',
        'validated': False,
        'weather_mode': inp.weather,
        'rainfall_multiplier': rain_multiplier,
        'scenario': inp.scenario,
        'day_phase': inp.day_phase,
        'management': {'irrigation_intensity_pct': inp.irrigation_percent, 'drainage_intensity_pct': inp.drainage_percent},
        'zones': zones,
        'average_stress_index': round(sum(z['stress_index'] for z in zones)/len(zones), 1),
        'units': {'stress_index': 'dimensionless 0–100 illustrative index', 'rainfall_multiplier': 'counterfactual multiplier, not observation'},
        'explanations': [
            'Drought = hypothetical rainfall 45% lower; surge = hypothetical rainfall 65% higher. These are not forecasts.',
            'Irrigation and drainage sliders are abstract indices; no soil hydraulic model or measured water balance is used.',
            'The result visualizes relative stress assumptions only, not crop-health measurements, yield, water volumes or recommendations.',
        ],
        'terrain_provenance': 'synthetic procedural geometry; no digital elevation model, soil strata profile, or surveyed boundary',
        'remote_sensing_provenance': 'none; MODIS, Landsat, and ECOSTRESS are documented future layer adapters, not loaded pixels',
    }


DATASET_REGISTRY = [
    {'id': 'nasa_power', 'provider': 'NASA POWER', 'use': 'Historical gridded rainfall, air temperature and radiation',
     'integration': 'live_point_api', 'status': 'available_on_user_request',
     'source_url': 'https://power.larc.nasa.gov/docs/services/api/temporal/daily/',
     'spatial_limit': 'Gridded climate; not field-scale conditions'},
    {'id': 'nasa_hls', 'provider': 'NASA HLS v2.0 (L30 and S30)', 'use': 'QA-masked local NDVI from authenticated downloaded COG bands', 'integration': 'optional_offline_raster_processor', 'status': 'MANUAL_IMPORT_ONLY', 'source_url': 'https://hls.gsfc.nasa.gov/data-access-and-tools/', 'spatial_limit': '30 m; few/mixed pixels make small-plot inference unreliable'},
    {'id': 'modis', 'provider': 'NASA MODIS vegetation indices', 'use': '16-day NDVI/EVI vegetation context',
     'integration': 'metadata_reference_only', 'status': 'NOT_INGESTED',
     'source_url': 'https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/science-domain/vegetation-indices/',
     'spatial_limit': 'Moderate resolution; careful QA, compositing and field pixel matching required'},
    {'id': 'landsat', 'provider': 'USGS/NASA Landsat Collection 2', 'use': 'Surface reflectance and derived vegetation metrics',
     'integration': 'metadata_reference_only', 'status': 'NOT_INGESTED',
     'source_url': 'https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-reflectance',
     'spatial_limit': '30m reflectance requires radiometric scaling, masks and georeferencing'},
    {'id': 'ecostress', 'provider': 'NASA ECOSTRESS', 'use': 'Irregular-overpass surface thermal and ET products',
     'integration': 'metadata_reference_only', 'status': 'NOT_INGESTED',
     'source_url': 'https://ecostress.jpl.nasa.gov/data',
     'spatial_limit': '70m ET products; temporal coverage, cloud QA and Earthdata access required'},
]

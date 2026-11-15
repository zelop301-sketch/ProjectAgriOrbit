"""Phase 22: PHIVOLCS-compatible local hazard exposure *screening*.

This module intentionally does not obtain or certify official government vector
assets. All geometry is provided by the user. PHIVOLCS's hazard legend and
licensing must be checked by the user; this is NOT a disaster forecast.
"""
from __future__ import annotations

from datetime import date
import hashlib
import json
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.ops import transform, unary_union
from pyproj import Transformer

from .scoring import Farm

_ALLOWED_GEOMETRY = {'Polygon', 'MultiPolygon'}
_MAX_HAZARDS = 100
_MAX_VERTICES = 16000


class HazardSource(BaseModel):
    agency_declared: str = Field(default='DOST-PHIVOLCS (user declaration, not independently authenticated)', max_length=180)
    title: str = Field(default='Pinatubo lahar hazard map — user-provided', min_length=3, max_length=180)
    source_url: str | None = Field(default=None, max_length=500)
    map_date: date | None = None
    edition: str = Field(default='Unspecified', max_length=100)
    use_permission: Literal['not_checked', 'local_review_only', 'permission_confirmed_by_user'] = 'not_checked'
    permission_notes: str = Field(default='', max_length=500)

    @field_validator('source_url')
    @classmethod
    def valid_url(cls, value):
        if value is not None:
            p=urlparse(value)
            if p.scheme != 'https' or not p.hostname:
                raise ValueError('Source URL must use HTTPS.')
        return value


class HazardScreenRequest(BaseModel):
    farm_geometry: dict[str, Any]
    hazard_geojson: dict[str, Any] | None = None
    source: HazardSource = Field(default_factory=HazardSource)
    farm: Farm | None = None
    climate_mode: Literal['none', 'nasa', 'synthetic'] = 'none'
    climate_end_year: int = Field(default=2025, ge=1986, le=2025)
    climate_baseline_years: int = Field(default=5, ge=3, le=10)


def _geometry(data: dict, label: str, allow_multi=True):
    if not isinstance(data, dict):
        raise ValueError(f'{label} must be a GeoJSON object.')
    if data.get('crs'):
        raise ValueError(f'{label} must be RFC 7946 WGS84 longitude/latitude GeoJSON, without a custom CRS.')
    if data.get('type') == 'Feature':
        data=data.get('geometry')
    if not isinstance(data, dict) or data.get('type') not in (_ALLOWED_GEOMETRY if allow_multi else {'Polygon'}):
        raise ValueError(f'{label} must be a GeoJSON Polygon or MultiPolygon.')
    try:
        geom=shape(data)
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        raise ValueError(f'{label} geometry could not be parsed.') from exc
    if geom.is_empty or not geom.is_valid or geom.area <= 0:
        raise ValueError(f'{label} is empty, self-intersecting, or topologically invalid.')
    bounds=geom.bounds
    if not all(-180 <= v <= 180 for v in (bounds[0],bounds[2])) or not all(-90 <= v <= 90 for v in (bounds[1],bounds[3])):
        raise ValueError(f'{label} must contain valid longitude/latitude positions.')
    def count(g):
        if g.geom_type == 'Polygon':
            return len(g.exterior.coords) + sum(len(r.coords) for r in g.interiors)
        return sum(count(p) for p in g.geoms)
    if count(geom) > _MAX_VERTICES:
        raise ValueError(f'{label} exceeds geometry vertex limit.')
    return geom


def _features(value: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        raise ValueError('Hazard map must be a GeoJSON object.')
    if value.get('crs'):
        raise ValueError('Hazard GeoJSON must be WGS84 (no custom CRS).')
    kind=value.get('type')
    if kind=='FeatureCollection':
        features=value.get('features')
        if not isinstance(features,list):
            raise ValueError('FeatureCollection.features must be an array.')
    elif kind=='Feature':
        features=[value]
    elif kind in _ALLOWED_GEOMETRY:
        features=[{'type':'Feature','geometry':value,'properties':{}}]
    else:
        raise ValueError('Supply a GeoJSON FeatureCollection, Feature, Polygon or MultiPolygon.')
    if len(features) > _MAX_HAZARDS:
        raise ValueError('Maximum 100 hazard features per request.')
    return features


def _utm_crs(lon:float,lat:float) -> str:
    zone=min(60,max(1,int((lon+180)/6)+1))
    return f'EPSG:{32600+zone if lat>=0 else 32700+zone}'


def screen_hazard(request:HazardScreenRequest)->dict:
    farm=_geometry(request.farm_geometry, 'Farm boundary',allow_multi=False)
    # Keep farm scale local; UTM area is inappropriate for huge or discontinuous farm envelopes.
    minx,miny,maxx,maxy=farm.bounds
    if maxx-minx >= 0.5 or maxy-miny >= 0.5:
        raise ValueError('Farm boundary must be local (under 0.5° across each axis).')
    lon,lat=farm.centroid.x,farm.centroid.y
    transformer=Transformer.from_crs('EPSG:4326',_utm_crs(lon,lat),always_xy=True)
    inverse=Transformer.from_crs(_utm_crs(lon,lat),'EPSG:4326',always_xy=True)
    projected_farm=transform(transformer.transform,farm)
    area_ha=projected_farm.area/10000
    if not 0.0001 <= area_ha <= 10000:
        raise ValueError('Field size outside accepted pilot-scale screening range.')
    if request.farm and not farm.covers(shape({'type':'Point','coordinates':[request.farm.longitude,request.farm.latitude]})):
        raise ValueError('Farm profile coordinate must lie inside the uploaded field boundary.')
    source=request.source
    flags=[]
    has_source=bool(request.hazard_geojson)
    overlap_geometries=[]
    areas=[]
    display=[]
    if has_source:
        features=_features(request.hazard_geojson)
        if len(json.dumps(request.hazard_geojson, ensure_ascii=False, separators=(',',':'))) > 2_000_000:
            raise ValueError('Hazard GeoJSON exceeds 2 MB local analysis limit.')
        if not features:
            flags.append('Hazard GeoJSON has no features. This means NO ASSESSMENT, not no hazard.')
        for index, item in enumerate(features):
            if not isinstance(item,dict) or item.get('type') != 'Feature':
                raise ValueError('Hazard collection must contain GeoJSON Features only.')
            geometry=_geometry(item,'Hazard feature')
            if not geometry.intersects(farm):
                continue
            clipped=transform(transformer.transform,geometry).intersection(projected_farm)
            if clipped.is_empty or clipped.area <= 1e-5:
                continue
            props=item.get('properties') or {}
            if not isinstance(props,dict):
                props={}
            category=str(props.get('hazard_type') or props.get('zone') or props.get('name') or 'Unclassified mapped hazard')[:100]
            area=clipped.area/10000
            overlap_geometries.append(clipped)
            areas.append({'feature_index':index,'legend_label_as_supplied':category,
                          'overlap_area_ha':round(area,4),'percent_of_farm':round(100*area/area_ha,2)})
            # Only clipped overlay is returned: avoid redistribution of the full supplied map.
            clipped_wgs=transform(inverse.transform,clipped)
            if clipped_wgs.geom_type not in _ALLOWED_GEOMETRY:
                clipped_wgs=clipped_wgs.buffer(0)
            if clipped_wgs.geom_type in _ALLOWED_GEOMETRY:
                display.append({'type':'Feature','geometry':mapping(clipped_wgs),
                                'properties':{'legend_label_as_supplied':category,'feature_index':index,
                                              'source_status':'USER-SUPPLIED UNVERIFIED'}})
    if has_source and _features(request.hazard_geojson):
        combined=unary_union(overlap_geometries) if overlap_geometries else None
        overlapped=combined.area/10000 if combined is not None else 0.0
        status='mapped_overlap_detected' if overlapped>1e-8 else 'no_overlap_in_supplied_layers'
    else:
        overlapped=0.0
        status='not_assessed_no_map'
    if not source.map_date:
        flags.append('Map publication / revision date missing: currency cannot be checked.')
    elif source.map_date > date.today():
        flags.append('Map publication date is in the future; verify the map metadata.')
    if source.use_permission != 'permission_confirmed_by_user':
        flags.append('Reuse permission not confirmed. Do not redistribute maps or generated overlays publicly.')
    hostname=(urlparse(source.source_url).hostname or '') if source.source_url else ''
    if not (hostname == 'phivolcs.dost.gov.ph' or hostname.endswith('.phivolcs.dost.gov.ph')):
        flags.append('Source URL is not a recognized PHIVOLCS domain. Agency origin cannot be independently verified.')
    if status == 'no_overlap_in_supplied_layers':
        flags.append('No overlap only means no intersection with supplied features. Missing map coverage cannot establish safety.')
    if status == 'mapped_overlap_detected':
        flags.append('Mapped exposure requires PHIVOLCS / LGU interpretation. Overlay does not measure current lahar activity or future occurrence.')
    if not has_source:
        flags.append('No hazard map provided. Hazard exposure is UNKNOWN, never safe by default.')
    return {'status':status,'farm_area_ha_utm_approx':round(area_ha,4),
            'mapped_overlap_area_ha_utm_approx':round(overlapped,4) if has_source else None,
            'mapped_overlap_percent':round(100*overlapped/area_ha,2) if has_source else None,
            'overlap_by_source_feature':areas, 'clipped_overlays':{'type':'FeatureCollection','features':display},
            'farm_geometry':mapping(farm),'farm_crs':'WGS84 longitude/latitude',
            'area_method':_utm_crs(lon,lat)+' projected planar area; indicative only, not legal surveying',
            'map_metadata':source.model_dump(mode='json'),
            'user_supplied_geojson_sha256':(hashlib.sha256(json.dumps(request.hazard_geojson,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')).hexdigest() if has_source else None),
            'provenance':'USER_SUPPLIED_UNVERIFIED even if official agency named; no authentication performed',
            'climate_independent_of_hazard':True,'no_lahar_prediction':True,
            'no_safety_certification':True,'crop_suitability_not_inferred':True,'flags':flags}


DEMO_FARM={'type':'Polygon','coordinates':[[[120.0230,15.2884],[120.0250,15.2884],
                                        [120.0250,15.2897],[120.0230,15.2897],[120.0230,15.2884]]]}
DEMO_HAZARDS={'type':'FeatureCollection','features':[{'type':'Feature',
    'properties':{'hazard_type':'FICTIONAL EXAMPLE / Not PHIVOLCS'},
    'geometry':{'type':'Polygon','coordinates':[[[120.0240,15.2880],[120.0260,15.2880],
                                              [120.0260,15.2900],[120.0240,15.2900],[120.0240,15.2880]]]}}]}

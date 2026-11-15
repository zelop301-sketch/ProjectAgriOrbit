"""Phase 23 — user-permission workflow and traceable NASA POWER daily retrieval.

Only DOST-PHIVOLCS grants DUA/MOA or other appropriate permission. This code
never authenticates a government hazard layer or publishes government data.
NASA POWER observations must be fetched server-side from the official endpoint.
"""
from __future__ import annotations
import hashlib
import json
import math
from datetime import datetime, date
from typing import Literal
from pydantic import BaseModel, Field
from fastapi import HTTPException
from .climate import fetch_climate, cache_path, PARAMS

PHIVOLCS_REQUEST_URL = 'https://gisweb.phivolcs.dost.gov.ph/gisweb/geomatics-services-request'
PHIVOLCS_MAPS_URL = 'https://www.phivolcs.dost.gov.ph/volcano-hazard/'
NASA_POWER_DOCS_URL = 'https://power.larc.nasa.gov/docs/services/api/temporal/daily/'

class PermissionReview(BaseModel):
    intended_use: Literal['private_local_preview', 'team_internal_analysis', 'public_redistribution'] = 'private_local_preview'
    agreement_reference: str = Field(default='',max_length=160)
    signed_agreement_attested: bool = False
    explicit_redistribution_permission_attested: bool = False
    official_layer_loaded_by_user: bool = False
    notes: str = Field(default='',max_length=400)


def review_permission(request: PermissionReview) -> dict:
    """A private self-attestation only. Never a PHIVOLCS authorization decision."""
    reference = request.agreement_reference.strip()
    agreement_asserted = bool(reference and request.signed_agreement_attested)
    warnings = [
        'The app cannot independently authenticate a DOST-PHIVOLCS agreement, map version, or license.',
        'PHIVOLCS may require a signed Data User Agreement or MOA for vector layers; confirm exact scope with the agency.',
        'An official Hazard Assessment Report is separate from this GIS screening and is not generated here.',
    ]
    if request.intended_use == 'public_redistribution':
        if agreement_asserted and request.explicit_redistribution_permission_attested:
            status='user_attests_explicit_public_rights_not_verified'
            warnings.append('Explicit public redistribution rights are asserted by user only. Obtain independent agency confirmation before publishing.')
        else:
            status='public_use_blocked_pending_agency_permission'
            warnings.append('Public distribution must not proceed without explicit applicable agency permission.')
    elif agreement_asserted:
        status='user_attests_signed_agreement_not_verified'
    else:
        status='local_private_preview_only_pending_agreement'
        warnings.append('Do not label user-provided shapes as authenticated PHIVOLCS hazard data.')
    return {
        'status':status,
        'official_approval_granted_by_app':False,
        'official_layer_included':False,
        'purpose':request.intended_use,
        'user_reports_agreement':agreement_asserted,
        'user_reports_layer_loaded':request.official_layer_loaded_by_user,
        'agreement_reference_recorded':reference or None,
        'public_distribution_approved':False,
        'review_type':'SELF-ATTESTED LOCAL WORKFLOW — NOT GOVERNMENT VALIDATION',
        'next_steps':['Request the appropriate Pinatubo lahar vector layer and map legend from DOST-PHIVOLCS.',
                      'Follow the supplied Data User Agreement / MOA procedure and keep the original file and edition.',
                      'Only then import a local authorized polygon; obtain PHIVOLCS/LGU interpretation for safety questions.'],
        'official_request_url':PHIVOLCS_REQUEST_URL,
        'official_map_index_url':PHIVOLCS_MAPS_URL,
        'warnings':warnings
    }


def daily_rows_from_cache(lat:float,lon:float,year:int,checksum:str) -> list[dict]:
    """Extract audited daily rows from the raw NASA server cache, never client JSON."""
    path=cache_path(lat,lon,year)
    try:
        payload=json.loads(path.read_text(encoding='utf-8'))
        raw=payload['raw']
        digest=hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if digest != checksum:
            raise ValueError('NASA cache digest mismatch')
        param=raw['properties']['parameter']
        if not all(isinstance(param[k],dict) for k in PARAMS):
            raise ValueError('NASA payload missing variable arrays')
    except (OSError,ValueError,TypeError,KeyError) as exc:
        raise RuntimeError('Real NASA response cannot be reconstructed from the verified cache; retry the official download.') from exc
    rows=[]
    from .climate import numeric
    for ds in sorted(set().union(*(set(param[k].keys()) for k in PARAMS))):
        if len(ds)!=8 or not ds.isdigit() or not ds.startswith(str(year)):
            continue
        try:
            day=date.fromisoformat(f'{ds[:4]}-{ds[4:6]}-{ds[6:8]}')
        except ValueError:continue
        values={}
        for code in PARAMS:
            v=numeric(param[code].get(ds))
            if (code=='T2M' and (v is None or not -90<=v<=65) or
                code=='PRECTOTCORR' and (v is None or not 0<=v<=2000) or
                code=='ALLSKY_SFC_SW_DWN' and (v is None or not 0<=v<=25)):
                v=None
            values[code]=round(v,3) if v is not None else None
        rows.append({'date':day.isoformat(),**values})
    return rows


async def nasa_observation_receipt(lat:float,lon:float,year:int,*,refresh:bool=False,include_daily:bool=False) -> dict:
    """Only real NASA API or authentic cache results. No synthetic substitution."""
    try:
        result=await fetch_climate(lat,lon,year,refresh=refresh)
    except RuntimeError as exc:
        raise HTTPException(status_code=503,detail=str(exc)) from exc
    source=result.get('source_type')
    if source not in ('nasa_api','nasa_cached'):
        raise HTTPException(status_code=503,detail='NASA data unavailable. Synthetic or user-supplied values are not accepted as NASA evidence.')
    try:
        rows=daily_rows_from_cache(lat,lon,year,result['raw_payload_sha256'])
    except RuntimeError as exc:
        raise HTTPException(status_code=503,detail=str(exc)) from exc
    if not rows:
        raise HTTPException(status_code=503,detail='No valid daily NASA observations in verified cache.')
    meta={'provider':'NASA POWER','product':'Daily point, agricultural community',
          'source_type':source,'access':'downloaded_from_official_endpoint' if source=='nasa_api' else 'cached_official_response',
          'request_url':result['request_url'],'retrieved_at':result['retrieved_at'],
          'raw_payload_sha256':result['raw_payload_sha256'],
          'time_standard':result['time_standard'],
          'coordinates':{'latitude':lat,'longitude':lon},
          'spatial_note':result['spatial_note'],
          'scientific_scope':'Historical regional gridded context; NOT farm-gauge rainfall, a lahar forecast, or crop-yield prediction.',
          'daily_units':{'T2M':'degrees C','PRECTOTCORR':'mm/day','ALLSKY_SFC_SW_DWN':'kWh/m2/day'},
          'retrieval_warning':result.get('fetch_warning'),
          'original_api_docs':NASA_POWER_DOCS_URL}
    return {'status':'historical_nasa_received', 'data_class':'historical_nasa',
            'annual_quality_gate':result['quality_gate'],
            'coverage_pct_by_variable':result['coverage_pct_by_variable'],
            'year':year,'daily_records':len(rows),
            'metadata':meta,'monthly':result['months'],
            'annual_summary':result['summary'],
            'quality_warnings':result.get('warnings',[]),
            'daily':rows if include_daily else None,
            'source_integrity':'SHA-256 records local raw response integrity, not an agency digital signature.',
            'safety_note':'DOST-PHIVOLCS provides volcanic hazard guidance separately. Rainfall history does not predict future lahar.'}

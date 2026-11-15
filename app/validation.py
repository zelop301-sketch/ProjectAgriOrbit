"""Pair local rain-gauge readings with server-obtained NASA POWER daily rainfall.

Pairing and bias are descriptive; no calibrated accuracy claim is possible
until local gauge siting, instruments and data quality are documented.
"""
from __future__ import annotations
import calendar
from datetime import date
import math
from pydantic import BaseModel, Field, model_validator
from typing import Literal
from .climate import synthetic_data, fetch_climate, cache_path, numeric
import json

class RainGaugeReading(BaseModel):
    day: date
    precipitation_mm: float = Field(ge=0, le=2000)

class RainValidationRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    year: int = Field(default=2025, ge=1981, le=2025)
    gauge_id: str = Field(default='Unverified gauge', min_length=1, max_length=120)
    gauge_calibrated: bool = False
    mode: Literal['nasa','synthetic'] = 'nasa'
    observations: list[RainGaugeReading] = Field(min_length=1, max_length=366)

    @model_validator(mode='after')
    def validate_dates(self):
        days=[r.day for r in self.observations]
        if len(set(days)) != len(days) or any(d.year != self.year for d in days):
            raise ValueError('Daily gauge dates must be unique and inside selected year')
        return self


def compare_daily_rainfall(readings: list[RainGaugeReading], estimates: dict[str,float],
                           source_kind: str, calibrated: bool) -> dict:
    paired=[]
    for r in readings:
        val=estimates.get(r.day.strftime('%Y%m%d'))
        if val is not None and math.isfinite(val) and val>=0:
            paired.append({'date':r.day.isoformat(),'gauge_mm':r.precipitation_mm,'power_mm':round(val,2)})
    missing=len(readings)-len(paired)
    n=len(paired)
    diffs=[p['power_mm']-p['gauge_mm'] for p in paired]
    min_pairs=5
    metrics={'mae_mm':round(sum(abs(d) for d in diffs)/n,3),
             'bias_power_minus_gauge_mm':round(sum(diffs)/n,3),
             'rmse_mm':round(math.sqrt(sum(d*d for d in diffs)/n),3)} if n>=min_pairs else None
    return {'source_type':source_kind,'gauge_provenance':'user_supplied_not_authenticated',
            'gauge_calibration_self_reported':calibrated, 'pairs':paired,
            'paired_days':n,'unpaired_gauge_days':missing,
            'total_gauge_days':len(readings),'paired_pct':round(100*n/len(readings),1),
            'minimum_pairs_for_metrics':min_pairs,
            'statistics':metrics,'independent_validation_completed':False,
            'notice':'Descriptive comparison only. The NASA grid is not a point gauge, and uploaded gauge calibration/siting is not verified.',
            'quality_gate':n>=min_pairs,
            'scientific_reference':'https://power.larc.nasa.gov/'}


def _demo_daily(year: int) -> dict[str,float]:
    # Clearly synthetic. Matches the monthly synthetic rainfall generator.
    data=synthetic_data(0,0,year)
    return {f'{year}{m["month"]:02d}{day:02d}':m['precipitation_mm']/calendar.monthrange(year,m['month'])[1]
            for m in data['months'] for day in range(1,calendar.monthrange(year,m['month'])[1]+1)}

async def validate_against_power(p:RainValidationRequest)->dict:
    if p.mode=='synthetic':
        estimates=_demo_daily(p.year)
        kind='synthetic_rehearsal_not_nasa'
    else:
        climate=await fetch_climate(p.latitude,p.longitude,p.year)
        path=cache_path(p.latitude,p.longitude,p.year)
        if not path.exists():
            raise RuntimeError('Cached source JSON unavailable; cannot validate NASA daily data')
        obj=json.loads(path.read_text(encoding='utf-8'))
        raw=obj.get('raw',{}).get('properties',{}).get('parameter',{}).get('PRECTOTCORR',{})
        estimates={k:v for k,value in raw.items() if (v:=numeric(value)) is not None and 0<=v<=2000}
        kind=climate['source_type']
    result=compare_daily_rainfall(p.observations,estimates,kind,p.gauge_calibrated)
    result['year']=p.year
    result['latitude']=p.latitude
    result['longitude']=p.longitude
    result['gauge_id']=p.gauge_id
    return result

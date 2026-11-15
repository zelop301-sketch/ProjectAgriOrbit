"""Auditable arithmetic soil-water budget; inputs are provided, not observed by the app.

This is not a calibrated hydrologic model. Use FAO-56 ETc = Kc * ET0 only
when both ETo and Kc are supplied with their original units and source.
"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, model_validator

class WaterBalanceRequest(BaseModel):
    period_days: int = Field(default=30, ge=1, le=366)
    starting_storage_mm: float = Field(ge=0, le=2000)
    soil_capacity_mm: float = Field(ge=0, le=2000)
    precipitation_mm: float = Field(ge=0, le=5000)
    irrigation_mm: float = Field(default=0, ge=0, le=5000)
    runoff_mm: float = Field(default=0, ge=0, le=5000)
    drainage_mm: float = Field(default=0, ge=0, le=5000)
    etc_mm: float | None = Field(default=None, ge=0, le=5000)
    eto_mm_per_day: float | None = Field(default=None, ge=0, le=30)
    crop_coefficient: float | None = Field(default=None, ge=0, le=3)
    inputs_note: str = Field(default='User-supplied illustrative inputs', max_length=240)
    source_type: Literal['user_entered','field_measured','research_estimate'] = 'user_entered'

    @model_validator(mode='after')
    def valid(self):
        if self.starting_storage_mm > self.soil_capacity_mm:
            raise ValueError('starting_storage_mm must not exceed soil_capacity_mm')
        if self.etc_mm is None and (self.eto_mm_per_day is None or self.crop_coefficient is None):
            raise ValueError('Supply ETc or both ETo and Kc')
        return self


def calculate_water_balance(p: WaterBalanceRequest) -> dict:
    etc = (p.etc_mm if p.etc_mm is not None else p.eto_mm_per_day * p.crop_coefficient * p.period_days)
    delta = p.precipitation_mm + p.irrigation_mm - etc - p.runoff_mm - p.drainage_mm
    raw_end = p.starting_storage_mm + delta
    return {'source_type': 'user_supplied_water_budget', 'simulation_only':True,
        'inputs_provenance':p.source_type,
        'period_days':p.period_days,
        'crop_evapotranspiration_mm':round(etc,2),
        'etc_method':'user_supplied_ETc' if p.etc_mm is not None else 'FAO56_Kc_times_ETo_from_user_inputs',
        'net_change_mm':round(delta,2),
        'unbounded_end_storage_mm':round(raw_end,2),
        'bounded_storage_mm':round(max(0,min(p.soil_capacity_mm,raw_end)),2),
        'unaccounted_shortfall_mm':round(max(0,-raw_end),2),
        'unaccounted_excess_mm':round(max(0,raw_end-p.soil_capacity_mm),2),
        'input_note':p.inputs_note,
        'requires_local_validation':True,
        'cautions':['Rainfall is gross precipitation and runoff is subtracted separately. All inputs are user supplied, not a NASA-derived water prediction.',
                    'Do not interpret unaccounted excess as measured drainage or unaccounted shortfall as measured crop stress.',
                    'Confirm soil capacity, runoff, drainage, ETo, crop coefficient and rainfall with local methods before irrigation planning.'],
        'formula':'delta_storage = gross_rainfall + irrigation - ETc - runoff - drainage; ETc = Kc * ETo when applicable.',
        'reference':'https://www.fao.org/4/x0490e/x0490e0a.htm'}

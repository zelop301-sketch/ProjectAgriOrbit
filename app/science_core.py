"""Phase 21: evidence-gated agricultural screening (NOT a planting prescription).

No numeric crop suitability/yield scores are synthesized. Verified NASA POWER
history changes descriptive climate exposure flags; local agronomy requirements
can constrain options only when explicitly reviewed and accompanied by evidence.
"""
from __future__ import annotations

from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, model_validator

from .scoring import Farm, compare


class CropRule(BaseModel):
    crop: str = Field(min_length=1, max_length=80)
    ph_min: float | None = Field(default=None, ge=0, le=14)
    ph_max: float | None = Field(default=None, ge=0, le=14)
    allowed_textures: list[Literal['sandy', 'loamy', 'clayey']] = Field(default_factory=list, max_length=3)
    minimum_irrigation: Literal['none', 'limited', 'reliable'] = 'none'
    source_url: str = Field(default='', max_length=500)
    reviewed_by: str = Field(default='', max_length=120)
    reviewed_on: date | None = None

    @model_validator(mode='after')
    def validate_rule(self):
        if self.ph_min is not None and self.ph_max is not None and self.ph_min > self.ph_max:
            raise ValueError('ph_min cannot exceed ph_max')
        return self

    @property
    def reviewed(self):
        return bool(self.reviewed_on and self.reviewed_by.strip() and self.source_url.startswith('https://'))


class ScreeningRequest(BaseModel):
    farm: Farm
    # Source data are obtained by the server's precision_assessment, never accepted here.
    end_year: int = Field(default=2025, ge=1986, le=2025)
    baseline_years: int = Field(default=5, ge=3, le=10)
    mode: Literal['nasa', 'synthetic'] = 'nasa'
    crop_rules: list[CropRule] = Field(default_factory=list, max_length=35)


def screen_against_benchmark(farm: Farm, benchmark: dict, crop_rules: list[CropRule]) -> dict:
    """Identify verified conflicts, missing evidence, and historical climate context.

    Historic rainfall anomaly is descriptive and NOT a crop-specific drought
    probability. Never translate it into invented suitability percentage.
    """
    source = benchmark.get('data_class')
    observed = benchmark.get('status') == 'ready' and source == 'historical_nasa'
    anomaly = benchmark.get('rainfall_anomaly_pct') if observed else None
    rules = {x.crop.strip().casefold(): x for x in crop_rules}
    legacy = compare(farm)
    results = []
    for sequence in sorted(legacy['scenarios'], key=lambda x: x['id']):
        conflicts = []
        reviews = []
        evidence = []
        for crop in sequence['crops']:
            rule = rules.get(crop.casefold())
            if rule is None:
                reviews.append(f'{crop}: no crop-specific locally reviewed requirements supplied.')
                continue
            if not rule.reviewed:
                reviews.append(f'{crop}: supplied requirement is UNREVIEWED (need reviewer, date and HTTPS source).')
                continue
            evidence.append({'crop':crop, 'source_url':rule.source_url, 'reviewer':rule.reviewed_by,
                             'reviewed_on':rule.reviewed_on.isoformat()})
            if farm.soil_ph is not None and rule.ph_min is not None and rule.ph_max is not None:
                if not (rule.ph_min <= farm.soil_ph <= rule.ph_max):
                    finding = f'{crop}: input pH {farm.soil_ph:.1f} outside reviewed {rule.ph_min:.1f}–{rule.ph_max:.1f} range.'
                    if farm.soil_source == 'laboratory':
                        conflicts.append(finding + ' Confirm sample location, depth and lab method.')
                    else:
                        reviews.append(finding + ' Farmer/field input not laboratory verified: confirmation required.')
            elif rule.ph_min is not None or rule.ph_max is not None:
                reviews.append(f'{crop}: measured pH is missing or rule pH range is incomplete.')
            if rule.allowed_textures:
                if farm.texture == 'unknown':
                    reviews.append(f'{crop}: soil texture is unknown.')
                elif farm.texture not in rule.allowed_textures:
                    reviews.append(f'{crop}: reported texture outside reviewed range; confirm soil test.')
            irrigation_rank = {'none':0, 'limited':1, 'reliable':2}
            if irrigation_rank[farm.irrigation] < irrigation_rank[rule.minimum_irrigation]:
                reviews.append(f'{crop}: reviewed irrigation requirement exceeds reported irrigation availability; verify locally.')

        if not observed:
            reviews.append('No qualified real NASA historical rainfall comparison; climate exposure cannot be evaluated.')
        elif anomaly is not None and anomaly < 0:
            reviews.append(f'Historic three-month rainfall was {abs(anomaly):.1f}% below the recent reference mean; historical context, NOT a forecast or crop water-deficit estimate.')
        elif anomaly is not None:
            reviews.append(f'Historic three-month rainfall was {anomaly:+.1f}% versus the recent reference mean; NOT evidence of future water availability.')
        status = 'reported_lab_rule_conflict' if conflicts else 'further_field_review_required'
        results.append({
            'scenario_id':sequence['id'], 'title':sequence['title'], 'crops':sequence['crops'],
            'screening_status':status, 'reviewed_crop_evidence':evidence,
            'constraints_from_reviewed_rules':conflicts, 'missing_and_precautions':reviews,
            'legacy_illustrative_score':sequence['score'],
            'legacy_score_used_for_decision':False, 'validated_crop_suitability':False,
            'farm_planting_authorized':False,
        })
    gates = [
        {'key':'historical_nasa','passed':observed,'detail':'NASA POWER same-season historical rainfall comparison meets coverage gate.'},
        {'key':'local_soil_report','passed':farm.soil_source=='laboratory' and farm.soil_ph is not None,
         'detail':'Lab provenance is user-asserted, not independently authenticated; requires sample/date/depth confirmation.'},
        {'key':'crop_rules','passed':bool(crop_rules) and all(r.reviewed for r in crop_rules) and all(crop.casefold() in rules and rules[crop.casefold()].reviewed for scenario in results for crop in scenario['crops']),
         'detail':'At least one user-supplied requirement marked reviewed; local agronomy review is not authenticated.'},
        {'key':'field_outcome_validation','passed':False,'detail':'No independently validated planting outcomes or observed yield trials available.'},
        {'key':'field_imagery','passed':False,'detail':'No quality-checked farm-level HLS pixels automatically ingested into this assessment.'},
    ]
    return {
        'scientific_version':'phase21-1.0', 'data_class':source,
        'decision_ready':False, 'quality_gates':gates,
        'historical_climate': {'valid_nasa_context':observed,
            'rainfall_anomaly_pct':anomaly,
            'baseline_seasons_valid':benchmark.get('baseline_seasons_valid'),
            'historical_median_mm':benchmark.get('recent_median_rainfall_mm'),
            'target_rainfall_mm':(benchmark.get('target_season') or {}).get('precipitation_mm') if observed else None,
            'explanation':'Relative to previous same-season years; a descriptive historic comparison, not a seasonal forecast, crop requirement or drought probability.'},
        'scenarios':results,
        'notice':'SCIENTIFIC SCREENING ONLY. No planting recommendation or validated yield/ROI estimate. Missing inputs and unreviewed crop rules never become zero risk.',
        'no_fabrication_rule':'A missing NASA record or unavailable rule blocks an assessment instead of triggering synthetic substitution.',
    }

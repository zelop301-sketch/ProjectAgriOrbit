"""Phase 34: evidence-to-decision screening for Botolan.

NASA POWER monthly PRECTOTCORR is a monthly *mean daily precipitation rate*
(mm/day). Compare against daily-derived 2026 *monthly totals* by multiplying
reference rates by the actual number of days in the 2026 calendar month.

The long 1991–2020 reference is an intentionally specified 30-year study window,
not an official drought classification or a forecast. A monthly POWER value does
not establish within-month daily coverage. Never synthesize observations when NASA
is unavailable. This API **does not prescribe planting**, rank suitability, or
estimate crop-water budgets/yields. All agronomic rules are user-asserted.
"""
from __future__ import annotations

import calendar
import copy
import hashlib
import json
import math
import os
from datetime import date, datetime, timezone
from typing import Literal
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, Field, model_validator

from .botolan_demo import LAT, LON, TARGET_YEAR, TARGET_END_MONTH, PAGASA_URL, fetch_2026, MONTHS
from .climate import CACHE_ROOT, now_utc, synthetic_data
from .science_core import CropRule

BUILD = 'phase34-botolan-evidence-decisions-3.4.0'
REF_START, REF_END, REFERENCE_MIN_YEARS = 1991, 2020, 24
MONTHLY_URL = 'https://power.larc.nasa.gov/api/temporal/monthly/point'
FAO_RICE_URL = 'https://www.fao.org/4/s2022e/s2022e08.htm'

CANDIDATES = (
    ('rice-rice', 'Rice → Rice', ('Rice','Rice'), 'Two paddy-rice growing cycles'),
    ('rice-mungbean', 'Rice → Mungbean', ('Rice','Mungbean'), 'One rice cycle followed by a legume'),
    ('corn-mungbean', 'Corn → Mungbean', ('Corn','Mungbean'), 'Non-paddy diversified sequence'),
)

class FarmContext(BaseModel):
    irrigation: Literal['none','limited','reliable'] = 'limited'
    irrigation_source: Literal['farmer_report','measured'] = 'farmer_report'
    soil: Literal['unknown','sandy','loamy','clayey'] = 'unknown'
    soil_ph: float | None = Field(default=None, ge=0, le=14)
    soil_source: Literal['not_tested','farmer_report','laboratory'] = 'not_tested'
    planting_month: int = Field(default=6, ge=1, le=12)
    priority: Literal['conserve_water','soil_health','food_supply'] = 'conserve_water'
    crop_rules: list[CropRule] = Field(default_factory=list, max_length=10)

    @model_validator(mode='after')
    def unique_rules(self):
        names = [r.crop.strip().casefold() for r in self.crop_rules]
        if len(names) != len(set(names)):
            raise ValueError('Duplicate crop rule: supply one documented rule per crop')
        if any(name not in ('rice','mungbean','corn') for name in names):
            raise ValueError('Only rice, mungbean and corn requirements are supported in this pilot')
        return self

class DecisionRequest(BaseModel):
    mode: Literal['nasa','synthetic'] = 'nasa'
    refresh: bool = False
    farm: FarmContext = Field(default_factory=FarmContext)


def monthly_request():
    params = {
        'parameters': 'PRECTOTCORR,T2M', 'community': 'AG',
        'longitude': f'{LON:.5f}', 'latitude': f'{LAT:.5f}',
        'start': str(REF_START), 'end': str(REF_END), 'format': 'JSON',
    }
    return params, MONTHLY_URL + '?' + urlencode(params)


def parse_monthly(raw: dict, *, source_type: str, timestamp: str, url: str) -> dict:
    """Fail closed for missing metadata, unknown rainfall units or malformed series."""
    if source_type not in ('nasa_api','nasa_cached'):
        raise ValueError('Monthly climate reference requires server-fetched NASA provenance')
    try:
        p = raw['properties']['parameter']
        rain = p['PRECTOTCORR']; temp = p['T2M']
        if not isinstance(rain, dict) or not isinstance(temp, dict):
            raise TypeError('parameter values must be dictionaries')
        units = raw['parameters']
        rain_unit = units['PRECTOTCORR']['units'].strip().lower().replace(' ', '')
        temp_unit = units['T2M']['units'].strip().lower().replace(' ', '')
        if rain_unit not in ('mm/day', 'mm/d') or temp_unit not in ('c', '°c','degc','degrees_c'):
            raise ValueError('Unexpected NASA monthly precipitation/temperature units')
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError('NASA monthly payload has no verified parameter maps/units; reference withheld') from exc
    rows = {m: {'rain_rates':[], 'temperatures':[]} for m in range(1,13)}
    for year in range(REF_START, REF_END+1):
        for month in range(1,13):
            key = f'{year}{month:02d}'
            rv, tv = rain.get(key), temp.get(key)
            if type(rv) in (float,int) and math.isfinite(rv) and 0 <= rv < 1000:
                rows[month]['rain_rates'].append((year,float(rv)))
            if type(tv) in (float,int) and math.isfinite(tv) and -90 <= tv <= 65:
                rows[month]['temperatures'].append((year,float(tv)))
    if not any(rows[month]['rain_rates'] for month in rows):
        raise ValueError('NASA monthly reference contains no valid 1991–2020 precipitation records')
    out = []
    for m in range(1,13):
        rains=rows[m]['rain_rates']; temps=rows[m]['temperatures']
        out.append({
            'month':m, 'rain_mm_day':round(sum(v for _,v in rains)/len(rains), 5) if len(rains)>=REFERENCE_MIN_YEARS else None,
            'temp_c':round(sum(v for _,v in temps)/len(temps), 3) if len(temps)>=REFERENCE_MIN_YEARS else None,
            'rain_years':len(rains), 'temp_years':len(temps),
            'missing_rain_years':[year for year in range(REF_START,REF_END+1) if year not in {y for y,_ in rains}],
        })
    return {
        'months':out, 'source_type':source_type, 'retrieved_at':timestamp,
        'request_url':url,
        'raw_payload_sha256':hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        'reference_years':f'{REF_START}–{REF_END}',
        'units':'PRECTOTCORR monthly mean daily rate mm/day; T2M monthly mean °C',
        'quality_note':'Monthly product coverage = number of valid calendar-year values; underlying daily coverage is not asserted.',
    }


async def fetch_reference(*, refresh: bool = False) -> dict:
    params,url=monthly_request()
    key=hashlib.sha256(('monthly34:'+url).encode()).hexdigest()[:24]
    path=CACHE_ROOT / f'botolan_phase34_{key}.json'
    cached=None
    if path.exists():
        try:
            cached=json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            cached=None
    if cached and not refresh:
        try:
            age=(datetime.now(timezone.utc)-datetime.fromisoformat(cached['fetched_at'])).total_seconds()
            if 0<=age<24*3600:
                return parse_monthly(cached['raw'],source_type='nasa_cached',timestamp=cached['fetched_at'],url=url)
        except (KeyError, TypeError, ValueError):
            pass
    try:
        async with httpx.AsyncClient(timeout=45,follow_redirects=True) as client:
            r=await client.get(MONTHLY_URL,params=params)
            r.raise_for_status()
            raw=r.json()
        now=now_utc()
        result=parse_monthly(raw,source_type='nasa_api',timestamp=now,url=url)
        path.parent.mkdir(parents=True,exist_ok=True)
        tmp=path.with_suffix('.tmp.'+os.urandom(5).hex())
        try:
            tmp.write_text(json.dumps({'fetched_at':now,'raw':raw}),encoding='utf-8')
            os.replace(tmp,path)
        finally:
            tmp.unlink(missing_ok=True)
        return result
    except (httpx.HTTPError, ValueError, KeyError, TypeError, OSError) as exc:
        if cached:
            try:
                out=parse_monthly(cached['raw'],source_type='nasa_cached',timestamp=cached['fetched_at'],url=url)
                out['warning']='NASA request failed; using previously retrieved cached NASA payload with original timestamp.'
                return out
            except (ValueError,KeyError,TypeError):
                pass
        raise RuntimeError('NASA POWER 1991–2020 monthly reference unavailable; no NASA values were substituted.') from exc


def simulated_inputs() -> tuple[dict,dict]:
    """Separate pedagogical rehearsal, never an observational feed."""
    recent=synthetic_data(LAT,LON,TARGET_YEAR)
    for row in recent['months'][:TARGET_END_MONTH]:
        row['precipitation_mm']=round(row['precipitation_mm']*0.65,3)
        row['temperature_c']=round(row['temperature_c']+1,3)
    recent['raw_payload_sha256']=None
    reference={
        'months':[], 'source_type':'synthetic', 'request_url':None,
        'raw_payload_sha256':None, 'retrieved_at':None,
        'reference_years':'SIMULATED 1991–2020',
        'quality_note':'All 30 synthetic years fabricated; no historical NASA records.'
    }
    base=synthetic_data(LAT,LON,2020)
    for row in base['months']:
        m=row['month']
        reference['months'].append({'month':m,'rain_mm_day':row['precipitation_mm']/calendar.monthrange(2020,m)[1],
                                    'temp_c':row['temperature_c'],'rain_years':30,'temp_years':30,'missing_rain_years':[]})
    return recent,reference


def _valid_recent(row:dict|None,parameter:str,field:str) -> float|None:
    if not row: return None
    coverage=(row.get('coverage_pct_by_variable') or {}).get(parameter,0)
    value=row.get(field)
    if type(coverage) not in (int,float) or coverage<95 or type(value) not in (float,int) or not math.isfinite(value):
        return None
    return float(value)


def build_evidence(target:dict,reference:dict,*,mode:str)->dict:
    if mode not in ('nasa','synthetic'):
        raise ValueError('Unsupported source mode')
    if mode=='nasa' and (target.get('source_type') not in ('nasa_api','nasa_cached') or reference.get('source_type') not in ('nasa_api','nasa_cached')):
        raise ValueError('Unverified source cannot enter a NASA climate comparison')
    if mode=='synthetic' and (target.get('source_type')!='synthetic' or reference.get('source_type')!='synthetic'):
        raise ValueError('Synthetic rehearsal must not contain NASA records')
    target_rows={r['month']:r for r in target.get('months',[])}
    reference_rows={r['month']:r for r in reference.get('months',[])}
    months=[]
    for month in range(1,TARGET_END_MONTH+1):
        r=target_rows.get(month); base=reference_rows.get(month,{})
        rain=_valid_recent(r,'PRECTOTCORR','precipitation_mm')
        temp=_valid_recent(r,'T2M','temperature_c')
        rate=base.get('rain_mm_day');base_temp=base.get('temp_c')
        days=calendar.monthrange(TARGET_YEAR,month)[1]
        ref_total=round(rate*days,2) if type(rate) in (int,float) and math.isfinite(rate) and rate>=0 and base.get('rain_years',0)>=REFERENCE_MIN_YEARS else None
        reference_t=round(base_temp,2) if type(base_temp) in (int,float) and math.isfinite(base_temp) and base.get('temp_years',0)>=REFERENCE_MIN_YEARS else None
        delta=100*(rain/ref_total-1) if rain is not None and ref_total and ref_total>0 else None
        months.append({
            'month':month,'label':MONTHS[month-1],
            'rain_2026_mm':round(rain,2) if rain is not None else None,
            'rain_reference_mm':ref_total,
            'rain_departure_pct':round(delta,1) if delta is not None else None,
            'temp_2026_c':round(temp,2) if temp is not None else None,
            'temp_reference_c':reference_t,
            'valid_reference_years':base.get('rain_years',0),
            'temp_reference_years':base.get('temp_years',0),
            'target_rain_coverage_pct':(r or {}).get('coverage_pct_by_variable',{}).get('PRECTOTCORR',0),
            'has_comparison':delta is not None,
        })
    complete=all(row['has_comparison'] for row in months)
    rain_total=sum(row['rain_2026_mm'] for row in months) if complete else None
    reference_total=sum(row['rain_reference_mm'] for row in months) if complete else None
    departure=round(100*(rain_total/reference_total-1),1) if complete and reference_total and reference_total>0 else None
    lower=departure is not None and departure<=-10
    signal=('BELOW_30Y_REFERENCE' if lower else 'ABOVE_30Y_REFERENCE' if departure is not None and departure>=10
            else 'NEAR_30Y_REFERENCE' if departure is not None else 'INSUFFICIENT_EVIDENCE')
    return {
        'build':BUILD,'location':{'name':'Botolan town reference (not surveyed farm)', 'latitude':LAT,'longitude':LON},
        'data_class':'SYNTHETIC_REHEARSAL_NOT_NASA' if mode=='synthetic' else 'HISTORICAL_NASA_POWER',
        'source_mode':mode,
        'period':{'target':'2026-01 through 2026-10', 'reference':'1991–2020', 'minimum_reference_years_per_month':REFERENCE_MIN_YEARS,
                  'reference_method':'NASA POWER monthly mean daily rainfall (mm/day) × days in each 2026 calendar month; monthly temperature mean.',
                  'monthly_product_daily_coverage_not_verified':True},
        'months':months,
        'summary':{'months_usable':sum(r['has_comparison'] for r in months),'months_requested':TARGET_END_MONTH,
                   'rain_2026_jan_oct_mm':round(rain_total,1) if rain_total is not None else None,
                   'rain_reference_jan_oct_mm':round(reference_total,1) if reference_total is not None else None,
                   'rain_departure_pct':departure,'signal':signal,
                   'message':('2026 Jan–Oct gridded rainfall lower than 1991–2020 reference.' if lower else
                              'Full-window rainfall comparison available; no descriptive deficit alert.' if complete else
                              'Incomplete month coverage. No Jan–Oct rainfall departure is available.'),
                   'alert_threshold':'-10% is an AgriORBIT demonstrator flag, NOT an official drought/ENSO threshold.'},
        'provenance':[{'label':'2026 daily target', 'source_type':target.get('source_type'),
                       'retrieved_at':target.get('retrieved_at'),'request_url':target.get('request_url'),
                       'raw_payload_sha256':target.get('raw_payload_sha256')},
                      {'label':'1991–2020 monthly reference', 'source_type':reference.get('source_type'),
                       'retrieved_at':reference.get('retrieved_at'),'request_url':reference.get('request_url'),
                       'raw_payload_sha256':reference.get('raw_payload_sha256')}],
        'warnings':[
            'NASA POWER is gridded/reanalysis-derived climate context, NOT a field rain gauge or soil-moisture observation.',
            'PAGASA El Niño describes Pacific-wide conditions; it is not a Botolan field-level drought declaration.',
            '1991–2020 is a selected 30-year POWER study reference, not a field-observed normal or official drought index.',
            'Monthly reference values do not certify daily coverage. At least 24 of 30 valid monthly values are required.',
            'Target precipitation and temperature each require at least 95% valid daily values per month.',
            'A past Jan–Oct difference is not a planting-season forecast, causal ENSO attribution or water budget.',
            'No crop suitability percentages, yield benefits, water savings, or planting advice are generated.',
        ]+(['ALL climate values in this rehearsal are SYNTHETIC; use live NASA mode for actual Earth observations.'] if mode=='synthetic' else [])+
          ([reference['warning']] if reference.get('warning') else []),
        'official_sources':{'nasa_power':'https://power.larc.nasa.gov/docs/services/api/temporal/monthly/',
                            'fao_paddy':FAO_RICE_URL,'pagasa':PAGASA_URL},
    }


def make_screening(evidence:dict,farm:FarmContext)->dict:
    """Rule-based *question triage*, not inferred crop feasibility or numeric ranking."""
    alert=evidence['summary']['signal']=='BELOW_30Y_REFERENCE'
    observed=evidence['source_mode']=='nasa' and evidence['summary']['months_usable']==10
    demo=evidence['source_mode']=='synthetic'
    rulemap={r.crop.strip().casefold():r for r in farm.crop_rules}
    outcomes=[]
    for candidate_id,title,crops,focus in CANDIDATES:
        flags=[]; reasons=[]
        is_two_paddy=crops==('Rice','Rice')
        contains_paddy='Rice' in crops
        if alert and contains_paddy:
            flags.append({'type':'climate','label':'REVIEW RAINFALL EXPOSURE',
                          'reason':f"{evidence['summary']['rain_departure_pct']:+.1f}% Jan–Oct rainfall departure at a gridded town reference; this is historical context, not the next crop-season forecast."})
        elif alert:
            flags.append({'type':'climate','label':'CLIMATE EXPOSURE TO VERIFY',
                          'reason':'Lower historical gridded rainfall warrants local rain-gauge and planting-calendar checks even for non-paddy crops.'})
        elif not observed:
            flags.append({'type':'climate','label':'OBSERVATIONAL CLIMATE NOT CONFIRMED',
                          'reason':'Simulation or insufficient historical coverage cannot establish local climate exposure.'})
        if farm.irrigation!='reliable':
            if is_two_paddy:
                flags.append({'type':'water','label':'TWO PADDY CYCLES: WATER SUPPLY CHECK',
                              'reason':'Paddy rice can require added water for soil saturation, water layer and losses; reported irrigation is not reliable. FAO guidance is generic, not a Botolan water budget.'})
            elif contains_paddy:
                flags.append({'type':'water','label':'ONE PADDY CYCLE: WATER SUPPLY CHECK',
                              'reason':'Confirm rainfed/limited water supply through the rice stage, not just the following legume stage.'})
            else:
                flags.append({'type':'water','label':'RAINFED SEQUENCE: WATER CHECK',
                              'reason':'Alternative crops still need water; establish season-specific effective rainfall and soil-water storage before assessing them.'})
        else:
            flags.append({'type':'water','label':'IRRIGATION REPORTED — NOT VERIFIED',
                          'reason':'Capacity, timing, cost and permission to draw water still need independent field verification.'})
        if farm.soil=='unknown':
            flags.append({'type':'soil','label':'SOIL TEXTURE UNKNOWN','reason':'No soil texture result was provided; field compatibility cannot be established.'})
        elif farm.soil_source!='laboratory':
            flags.append({'type':'soil','label':'SOIL REPORTED — NOT LAB VERIFIED',
                          'reason':f'{farm.soil.title()} texture is self-reported; validate texture, drainage and sampling depth.'})
        if farm.soil_ph is None:
            flags.append({'type':'soil','label':'SOIL PH MISSING','reason':'No pH test was supplied for crop requirement checks.'})
        elif farm.soil_source!='laboratory':
            flags.append({'type':'soil','label':'PH NOT LAB VERIFIED','reason':f'pH {farm.soil_ph:.1f} is self-reported; no verified soil-compatibility conclusion.'})
        for crop in sorted(set(crops)):
            r=rulemap.get(crop.casefold())
            if r is None or not r.reviewed:
                flags.append({'type':'rule','label':f'{crop.upper()} RULE UNVERIFIED',
                              'reason':'A locally reviewed crop requirement with HTTPS citation, reviewer and review date is missing. Supplied attestations are not independently authenticated.'})
                continue
            if farm.soil_ph is not None and r.ph_min is not None and r.ph_max is not None and not(r.ph_min<=farm.soil_ph<=r.ph_max):
                flags.append({'type':'rule','label':f'{crop.upper()} PH CONFLICT TO CONFIRM',
                              'reason':f'Input pH {farm.soil_ph:.1f} falls outside user-asserted reviewed {r.ph_min:.1f}–{r.ph_max:.1f} range. Confirm both rule and sample locally.'})
            if r.allowed_textures and farm.soil!='unknown' and farm.soil not in r.allowed_textures:
                flags.append({'type':'rule','label':f'{crop.upper()} TEXTURE CONFLICT TO CONFIRM',
                              'reason':'Input texture falls outside user-asserted reviewed crop textures; require field and source verification.'})
            irrigation_rank={'none':0,'limited':1,'reliable':2}
            if irrigation_rank[farm.irrigation]<irrigation_rank[r.minimum_irrigation]:
                flags.append({'type':'rule','label':f'{crop.upper()} WATER-RULE CONFLICT TO CONFIRM',
                              'reason':'Reported irrigation is below user-supplied crop rule requirement; independent field review is needed.'})
        reasons.append(f'Farmer priority: {farm.priority.replace("_"," ")}; no scoring or optimization has been validated for this priority.')
        reasons.append(f'Proposed first planting month: {MONTHS[farm.planting_month-1]}; no locally reviewed crop calendar was supplied.')
        outcomes.append({'id':candidate_id,'name':title,'crops':crops,'focus':focus,
                         'status':'FIELD_REVIEW_REQUIRED','flags':flags,'questions':reasons,
                         'validated_suitability':False,'planting_authorized':False,
                         'fao_water_reference':FAO_RICE_URL if contains_paddy else None})
    attention={x['id']:sum(f['type'] in ('water','rule') for f in x['flags']) for x in outcomes}
    return {
        'decision_ready':False,'screening_type':'qualitative_evidence_question_triage',
        'candidates':outcomes,'confidence':'NOT VALIDATED','ranked':False,
        'research_note':'NO crop sequence is recommended; differences flag what field data should be collected next.',
        'sensitivity':{'variable':'irrigation','current_value':farm.irrigation,
                       'explanation':('Switch to Reliable irrigation to see which water-supply verification questions change.'
                                      if farm.irrigation!='reliable' else
                                      'Switch to Limited irrigation to see water-supply questions become more urgent.'),
                       'water_question_count':sum(1 for x in outcomes for flag in x['flags'] if flag['type']=='water')},
        'quality_gates':[
            {'name':'NASA gridded rainfall comparison','passed':observed,'note':'All Jan–Oct months must pass the target and 30-year reference gates.'},
            {'name':'Local measured irrigation supply','passed':False,'note':'Self-declared measured status is not independently verified.'},
            {'name':'Laboratory soil evidence (self-attested)','passed':farm.soil_source=='laboratory' and farm.soil_ph is not None,
             'note':'Laboratory source claimed by user; no test certificate was authenticated.'},
            {'name':'Locally validated crop requirements','passed':False,'note':'User-supplied reviewer metadata is not independently authenticated.'},
            {'name':'Field outcome validation','passed':False,'note':'No actual crop yields or comparative field trials are measured.'},
        ],
    }


async def calculate(request:DecisionRequest)->dict:
    if request.mode=='synthetic':
        recent,reference=simulated_inputs()
    else:
        import asyncio
        recent,reference=await asyncio.gather(fetch_2026(refresh=request.refresh),fetch_reference(refresh=request.refresh))
    evidence=build_evidence(recent,reference,mode=request.mode)
    return {'build':BUILD,'evidence':evidence,'farm':request.farm.model_dump(mode='json'),
            'screening':make_screening(evidence,request.farm),
            'notice':'EXPLORATORY RESEARCH ONLY. NOT farm-specific drought classification, a planting recommendation or a validated forecast.'}

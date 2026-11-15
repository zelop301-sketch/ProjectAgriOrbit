"""Phase 41 NASA POWER daily crop-season exposure and optional FAO-56 water-demand screening.

Only HTTP data retrieved server-side from NASA POWER may be labelled NASA. A distinct
synthetic mode is explicitly fictional. The historical 2015-2024 planting cohorts are
not future weather predictions. Crop coefficients, durations, soil and crop calendars
are assumptions, NOT derived from NASA or validated with farmers.
"""
from __future__ import annotations

import calendar
import hashlib
import json
import math
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Literal
from urllib.parse import urlencode, urlsplit

import httpx
from pydantic import BaseModel, Field, ConfigDict, model_validator

from .botolan_demo import LAT, LON
from .climate import CACHE_ROOT, now_utc

API = 'https://power.larc.nasa.gov/api/temporal/daily/point'
FIRST_YEAR, LAST_YEAR, PADDING_YEAR = 2015, 2024, 2025
REQUIRED_YEARS = 8
PARAMETERS = ('PRECTOTCORR','T2M','T2M_MAX','T2M_MIN','RH2M','WS2M','PS','ALLSKY_SFC_SW_DWN')
CROPS = ('Rice','Corn','Mungbean')
ROTATIONS = (
    ('rice-rice','Rice → Rice',('Rice','Rice')),
    ('rice-mungbean','Rice → Mungbean',('Rice','Mungbean')),
    ('corn-mungbean','Corn → Mungbean',('Corn','Mungbean')),
)


class Stage(BaseModel):
    model_config = ConfigDict(extra='forbid')
    days: int = Field(ge=1,le=180)
    kc: float = Field(gt=0,le=2.0)


class CropProfile(BaseModel):
    model_config = ConfigDict(extra='forbid')
    stages: list[Stage] = Field(default_factory=list,max_length=10)
    source_url: str | None = None
    source_title: str | None = Field(default=None, max_length=180)
    source_publisher: str | None = Field(default=None, max_length=120)
    crop_variety: str | None = Field(default=None, max_length=120)
    review_note: str | None = Field(default=None, max_length=250)

    @model_validator(mode='after')
    def require_source_if_profile(self):
        if self.stages:
            url = urlsplit(self.source_url or '')
            # A plausible URL is NOT a verified agronomic source; this only rejects malformed
            # links. Source credibility and Kc applicability still require human review.
            if (url.scheme != 'https' or not url.hostname or '.' not in url.hostname
                    or url.username or url.password or url.port is not None
                    or url.hostname.lower() in {'localhost', '127.0.0.1'}):
                raise ValueError('Crop coefficients require a valid public HTTPS agronomy source URL (not independently verified)')
        return self


class CropDurations(BaseModel):
    model_config = ConfigDict(extra='forbid')
    Rice: int = Field(default=120,ge=30,le=200)
    Corn: int = Field(default=105,ge=30,le=200)
    Mungbean: int = Field(default=75,ge=30,le=200)


class SeasonalRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    mode: Literal['nasa','synthetic']='nasa'
    refresh: bool=False
    latitude: float=Field(default=LAT,ge=-90,le=90)
    longitude: float=Field(default=LON,ge=-180,le=180)
    location_source: Literal['botolan_reference','farmer_report']='botolan_reference'
    elevation_m: float = Field(default=0,ge=-400,le=4000)
    elevation_source: Literal['assumed','measured']='assumed'
    planting_month: int=Field(default=6,ge=1,le=12)
    planting_day: int=Field(default=1,ge=1,le=28)
    gap_days: int=Field(default=0,ge=0,le=90)
    crop_days: CropDurations=Field(default_factory=CropDurations)
    crop_profiles: dict[str,CropProfile]=Field(default_factory=dict)
    farmer_priority: Literal['conserve_water','soil_health','food_supply']='conserve_water'
    irrigation: Literal['none','limited','reliable']='limited'
    soil: Literal['unknown','sandy','loamy','clayey']='unknown'
    soil_source: Literal['not_tested','farmer_report','laboratory']='not_tested'

    @model_validator(mode='after')
    def validate_profiles(self):
        if set(self.crop_profiles)-set(CROPS):
            raise ValueError('Only Rice, Corn, Mungbean crop profiles are supported')
        for name, profile in self.crop_profiles.items():
            if profile.stages and sum(s.days for s in profile.stages)!=getattr(self.crop_days,name):
                raise ValueError(f'{name} Kc stage lengths must total the entered crop duration')
        if self.location_source=='botolan_reference' and (abs(self.latitude-LAT)>1e-6 or abs(self.longitude-LON)>1e-6):
            raise ValueError('Changed coordinates must be declared farmer_report')
        return self


def api_request(req:SeasonalRequest)->tuple[dict,str]:
    params={'parameters':','.join(PARAMETERS),'community':'AG',
            'longitude':f'{req.longitude:.5f}','latitude':f'{req.latitude:.5f}',
            'start':f'{FIRST_YEAR}0101','end':f'{PADDING_YEAR}1231',
            'format':'JSON','time-standard':'LST'}
    return params,API+'?'+urlencode(params)


def _norm(unit:str)->str:
    return unit.strip().lower().replace(' ','').replace('²','2').replace('°','').replace('−','-')


def _units(raw):
    try:
        metadata=raw['parameters']; fields=raw['properties']['parameter']
        units={p:_norm(metadata[p]['units']) for p in PARAMETERS}
        if any(not isinstance(fields[p],dict) for p in PARAMETERS):
            raise TypeError('Not a parameter dictionary')
    except (KeyError,TypeError,AttributeError) as exc:
        raise ValueError('NASA daily payload missing parameter maps or units; all seasonal estimates withheld') from exc
    expected={
        'PRECTOTCORR':{'mm/day','mm/d'},
        'T2M':{'c','degc','degrees_c'},'T2M_MAX':{'c','degc','degrees_c'},'T2M_MIN':{'c','degc','degrees_c'},
        'RH2M':{'%','percent'},'WS2M':{'m/s','m/s'},'PS':{'kpa'},
    }
    for p,allowed in expected.items():
        if units[p] not in allowed:raise ValueError(f'Unverified {p} unit {units[p]}; results withheld')
    solar=units['ALLSKY_SFC_SW_DWN']
    if solar in {'kw-hr/m2/day','kwh/m2/day','kw-hr/m^2/day','kwh/m^2/day'}:
        factor=3.6
    elif solar in {'mj/m2/day','mj/m^2/day'}:
        factor=1.0
    else:raise ValueError(f'Unverified solar radiation unit {solar}; ETo withheld')
    return fields,units,factor


def _number(x,lower,upper):
    if type(x) not in (int,float) or not math.isfinite(x) or not lower<=x<=upper:return None
    return float(x)


def parse_daily(raw:dict, *,source_type:str,retrieved_at:str|None,url:str|None,latitude:float,longitude:float)->dict:
    if source_type not in ('nasa_api','nasa_cached','synthetic'):
        raise ValueError('Unsupported data provenance')
    if source_type=='synthetic' and (retrieved_at or url):
        raise ValueError('Synthetic climate must not impersonate NASA provenance')
    if source_type!='synthetic' and (not url or not url.startswith(API+'?') or not retrieved_at):
        raise ValueError('NASA request URL and retrieval time required')
    fields,units,solar_factor=_units(raw)
    start=date(FIRST_YEAR,1,1);end=date(PADDING_YEAR,12,31)
    days={};rejected={p:0 for p in PARAMETERS}
    # Iterate a fixed calendar, not arbitrary keys supplied by the response.
    day=start
    while day<=end:
        key=day.strftime('%Y%m%d')
        r=_number(fields['PRECTOTCORR'].get(key),0,700)
        avg=_number(fields['T2M'].get(key),-60,60)
        hi=_number(fields['T2M_MAX'].get(key),-60,65)
        lo=_number(fields['T2M_MIN'].get(key),-80,60)
        rh=_number(fields['RH2M'].get(key),0,100)
        wind=_number(fields['WS2M'].get(key),0,45)
        pressure=_number(fields['PS'].get(key),65,110)
        rs=_number(fields['ALLSKY_SFC_SW_DWN'].get(key),0,20)
        if rs is not None:rs*=solar_factor
        valid={'PRECTOTCORR':r,'T2M':avg,'T2M_MAX':hi,'T2M_MIN':lo,'RH2M':rh,
               'WS2M':wind,'PS':pressure,'ALLSKY_SFC_SW_DWN':rs}
        if hi is not None and lo is not None and hi<lo:
            valid['T2M_MAX']=None;valid['T2M_MIN']=None
        if avg is not None and hi is not None and avg>hi+1:
            valid['T2M']=None
        if avg is not None and lo is not None and avg<lo-1:
            valid['T2M']=None
        for p,v in valid.items():
            if v is None:rejected[p]+=1
        days[key]=valid
        day+=timedelta(days=1)
    if all(v is None for day in days.values() for v in day.values()):
        raise ValueError('NASA payload contains no valid daily values; results withheld')
    return {'days':days,'rejected_or_missing_days_by_variable':rejected,'units':units,
            'solar_conversion_to_mj_m2_day':solar_factor,
            'source_type':source_type,'retrieved_at':retrieved_at,'request_url':url,
            'raw_payload_sha256':None if source_type=='synthetic' else hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            'location':{'latitude':latitude,'longitude':longitude}}


async def retrieve(req:SeasonalRequest)->dict:
    if req.mode=='synthetic':
        return parse_daily(demo_daily(),source_type='synthetic',retrieved_at=None,url=None,
                           latitude=req.latitude,longitude=req.longitude)
    params,url=api_request(req)
    key=hashlib.sha256(('phase41:'+url).encode()).hexdigest()[:24]
    path=CACHE_ROOT/f'phase41_nasa_{key}.json'
    cached=None
    try:
        if path.is_file():cached=json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError):pass
    if cached and not req.refresh:
        try:
            age=(datetime.now(timezone.utc)-datetime.fromisoformat(cached['fetched_at'])).total_seconds()
            if 0<=age<24*3600:
                return parse_daily(cached['raw'],source_type='nasa_cached',retrieved_at=cached['fetched_at'],
                                   url=url,latitude=req.latitude,longitude=req.longitude)
        except (KeyError,TypeError,ValueError):pass
    try:
        async with httpx.AsyncClient(timeout=85,follow_redirects=True) as client:
            response=await client.get(API,params=params)
            response.raise_for_status()
            raw=response.json()
        stamp=now_utc()
        result=parse_daily(raw,source_type='nasa_api',retrieved_at=stamp,url=url,
                           latitude=req.latitude,longitude=req.longitude)
        path.parent.mkdir(parents=True,exist_ok=True)
        tmp=path.with_suffix('.tmp.'+os.urandom(5).hex())
        try:
            tmp.write_text(json.dumps({'fetched_at':stamp,'raw':raw}),encoding='utf-8')
            os.replace(tmp,path)
        finally:tmp.unlink(missing_ok=True)
        return result
    except (httpx.HTTPError,ValueError,KeyError,TypeError,OSError) as exc:
        if cached:
            try:
                result=parse_daily(cached['raw'],source_type='nasa_cached',retrieved_at=cached['fetched_at'],
                                   url=url,latitude=req.latitude,longitude=req.longitude)
                result['fetch_warning']='Fresh NASA retrieval failed; displaying an older authentic cached payload with its original date.'
                return result
            except (ValueError,KeyError,TypeError):pass
        raise RuntimeError('NASA POWER seasonal data unavailable or failed unit/shape QA. No fabricated NASA values were substituted.') from exc


def _sat_vp(temp):return .6108*math.exp(17.27*temp/(temp+237.3))


def extraterrestrial_radiation(lat:float,day:date)->float:
    # FAO-56 Eq 21; daily radiation in MJ m^-2 d^-1.
    phi=math.radians(lat);doy=day.timetuple().tm_yday
    dr=1+.033*math.cos(2*math.pi*doy/365)
    delta=.409*math.sin(2*math.pi*doy/365-1.39)
    arg=max(-1.,min(1.,-math.tan(phi)*math.tan(delta)))
    ws=math.acos(arg)
    return (24*60/math.pi)*.0820*dr*(ws*math.sin(phi)*math.sin(delta)+math.cos(phi)*math.cos(delta)*math.sin(ws))


def eto_fao56(values:dict,lat:float,elevation_m:float,day:date)->float|None:
    """Daily grass reference ET0 using FAO-56 Penman-Monteith, approximate RHmean ea.

    Requires verified daily temperature, max/min, RH, WS2M, PS and shortwave Rs.
    G=0 at a daily timestep; albedo=0.23, cloudiness via FAO Rs/Rso.
    NASA POWER gridded meteorology does not guarantee a station-calibrated ET0.
    """
    names=('T2M','T2M_MAX','T2M_MIN','RH2M','WS2M','PS','ALLSKY_SFC_SW_DWN')
    if any(values[p] is None for p in names):return None
    t,hi,lo,rh,u2,p,rs=[values[x] for x in names]
    if hi<lo or t<-45 or t>60 or not (0<=rh<=100):return None
    es=(_sat_vp(hi)+_sat_vp(lo))/2
    ea=es*rh/100  # RHmean approximation; not station RHmax/min observations.
    delta=4098*_sat_vp(t)/(t+237.3)**2
    gamma=.000665*p
    ra=extraterrestrial_radiation(lat,day)
    rso=(.75+.00002*elevation_m)*ra
    if rso<=0:return None
    # NASA Rs occasionally slightly exceeds estimated Rso; cap only cloudiness factor.
    rns=.77*rs
    rnl=4.903e-9*(((hi+273.16)**4+(lo+273.16)**4)/2)*(0.34-0.14*math.sqrt(ea))*(1.35*max(.3,min(1.,rs/rso))-.35)
    rn=rns-rnl
    denominator=delta+gamma*(1+0.34*u2)
    numerator=.408*delta*rn+gamma*(900/(t+273))*u2*max(0,es-ea)
    et0=max(0,numerator/denominator) if denominator>0 else None
    return et0 if et0 is not None and math.isfinite(et0) and et0<=25 else None


def _pctl(values:list[float],percent:float)->float|None:
    if not values:return None
    vals=sorted(values); i=(len(vals)-1)*percent/100;a=math.floor(i);b=math.ceil(i)
    return round(vals[a]+(vals[b]-vals[a])*(i-a),1)


def _longest_dry_spell(active_days:list[date], rains:list[float|None],threshold_mm:float=1.0)->int|None:
    """Longest sequence of <1 mm rainfall on CONSECUTIVE occupied crop dates.

    Fallow-gap dates do not join two spells; null rainfall invalidates the summary.
    The threshold is a screening convention, not a locally calibrated dry-spell definition.
    """
    if not active_days or any(r is None for r in rains):
        return None
    streak=longest=0
    prev=None
    for day,rain in zip(active_days,rains):
        if prev is not None and day != prev+timedelta(days=1):
            streak=0
        streak=streak+1 if rain<threshold_mm else 0
        longest=max(longest,streak)
        prev=day
    return longest


def _window(req:SeasonalRequest,year:int,crops:tuple[str,str]):
    start=date(year,req.planting_month,req.planting_day)
    first=getattr(req.crop_days,crops[0]);second=getattr(req.crop_days,crops[1]);end=start+timedelta(days=first+req.gap_days+second)
    if end>date(PADDING_YEAR,12,31)+timedelta(days=1):raise ValueError('Historical window extends beyond retrieved data')
    phases=[(crops[0],start,first),(crops[1],start+timedelta(days=first+req.gap_days),second)]
    return start,end,phases


def _one_year(req:SeasonalRequest,parsed:dict,year:int,crops:tuple[str,str])->dict:
    start,end,phases=_window(req,year,crops)
    all_days=[];dt=start
    while dt<end:
        if not (start+timedelta(days=getattr(req.crop_days,crops[0]))<=dt<start+timedelta(days=getattr(req.crop_days,crops[0])+req.gap_days)):
            all_days.append(dt)
        dt+=timedelta(days=1)
    vals=[parsed['days'].get(dt.strftime('%Y%m%d'),{}) for dt in all_days]
    rains=[v.get('PRECTOTCORR') for v in vals]
    rainfall_complete=all(v is not None for v in rains)
    ets=[eto_fao56(v,req.latitude,req.elevation_m,dt) if v else None for dt,v in zip(all_days,vals)]
    eto_complete=all(v is not None for v in ets)
    total_rain=round(sum(rains),2) if rainfall_complete else None
    total_eto=round(sum(ets),2) if eto_complete else None
    # Crop-specific Kc MUST be explicitly supplied, with stage totals validated.
    stage_by_date={}
    has_profiles=all(req.crop_profiles.get(name) and req.crop_profiles[name].stages for name in set(crops))
    if has_profiles:
        for crop,dt,days in phases:
            cursor=dt
            for stage in req.crop_profiles[crop].stages:
                for i in range(stage.days):stage_by_date[cursor+timedelta(days=i)]=stage.kc
                cursor+=timedelta(days=stage.days)
    etc=round(sum(v*stage_by_date[d] for d,v in zip(all_days,ets)),2) if eto_complete and has_profiles else None
    return {'year':year,'start':start.isoformat(),'end_exclusive':end.isoformat(),
            'crop_days':len(all_days),'rain_valid_days':sum(v is not None for v in rains),
            'eto_valid_days':sum(v is not None for v in ets),
            'rain_mm':total_rain,'eto_mm':total_eto,
            'rain_mm_per_crop_day':round(total_rain/len(all_days),3) if total_rain is not None else None,
            'eto_mm_per_crop_day':round(total_eto/len(all_days),3) if total_eto is not None else None,
            'longest_dry_spell_days_lt_1mm':_longest_dry_spell(all_days,rains),
            'et_c_mm':etc,
            # Legacy field: an optimistic arithmetic LOWER-BOUND indicator only. Not
            # effective rainfall, crop water deficit, or irrigation prescription.
            'idealized_rain_offset_shortfall_mm':round(max(0.,etc-total_rain),2) if etc is not None and total_rain is not None else None}


def compare(req:SeasonalRequest,parsed:dict)->dict:
    if req.mode=='nasa' and parsed['source_type'] not in ('nasa_api','nasa_cached'):
        raise ValueError('Cannot label synthetic payload NASA')
    if req.mode=='synthetic' and parsed['source_type']!='synthetic':
        raise ValueError('Cannot label NASA payload synthetic')
    results=[]
    for rotation_id,label,crops in ROTATIONS:
        years=[_one_year(req,parsed,y,crops) for y in range(FIRST_YEAR,LAST_YEAR+1)]
        rain=[r['rain_mm'] for r in years if r['rain_mm'] is not None]
        eto=[r['eto_mm'] for r in years if r['eto_mm'] is not None]
        etc=[r['et_c_mm'] for r in years if r['et_c_mm'] is not None]
        deficit=[r['idealized_rain_offset_shortfall_mm'] for r in years if r['idealized_rain_offset_shortfall_mm'] is not None]
        rain_daily=[r['rain_mm_per_crop_day'] for r in years if r['rain_mm_per_crop_day'] is not None]
        eto_daily=[r['eto_mm_per_crop_day'] for r in years if r['eto_mm_per_crop_day'] is not None]
        dry_spells=[r['longest_dry_spell_days_lt_1mm'] for r in years if r['longest_dry_spell_days_lt_1mm'] is not None]
        enough=lambda x:len(x)>=REQUIRED_YEARS
        rain_ok=enough(rain); eto_ok=enough(eto); etc_ok=enough(etc)
        actions=[]
        if req.irrigation!='reliable':
            actions.append('Measure irrigation capacity and timing through the planting window; reported '+req.irrigation+' access is not a verified water budget.')
        else:
            actions.append('Confirm reliability of reported irrigation with actual delivery records; no water capacity is verified.')
        if req.soil=='unknown':
            actions.append('Obtain representative soil texture, drainage and pH evidence before crop compatibility decisions.')
        elif req.soil_source!='laboratory':
            actions.append('Confirm reported '+req.soil+' soil using appropriate field/laboratory sampling; drainage and rooting-depth remain unknown.')
        if 'Rice' in crops:
            actions.append('For paddy rice, check ponding, land preparation, seepage and percolation separately; ETc alone is not rice field water demand.')
        if req.farmer_priority=='conserve_water':
            actions.append('Compare measured available water and farmer costs before acting; no percent water savings are supported by these historical screens.')
        elif req.farmer_priority=='soil_health':
            actions.append('Assess residue, erosion, organic matter and legume management locally; NASA meteorology cannot certify soil improvement.')
        else:
            actions.append('Confirm planting calendar, inputs and market needs locally; rainfall and ET0 do not predict food production or yield.')
        if not etc_ok:
            actions.append('Obtain crop-stage Kc coefficients from local agronomic guidance; provisional NASA-derived ET0 is NOT crop ETc.')
        results.append({
            'id':rotation_id,'name':label,'crop_sequence':crops,
            'status':'HISTORICAL_SCREENING_ONLY','planting_authorized':False,
            'valid_rain_years':len(rain),'valid_eto_years':len(eto),'valid_et_c_years':len(etc),
            'historical_rain_mm':{'p10':_pctl(rain,10),'median':_pctl(rain,50),'p90':_pctl(rain,90)} if rain_ok else None,
            'historical_eto_mm':{'p10':_pctl(eto,10),'median':_pctl(eto,50),'p90':_pctl(eto,90)} if eto_ok else None,
            # Daily-normalised metrics permit describing seasons of unequal lengths
            # without confusing longer occupation with higher water exposure.
            'crop_days_per_rotation':sum(getattr(req.crop_days,c) for c in crops),
            'historical_rain_mm_per_crop_day':{'p10':_pctl(rain_daily,10),'median':_pctl(rain_daily,50),'p90':_pctl(rain_daily,90)} if enough(rain_daily) else None,
            'historical_eto_mm_per_crop_day':{'p10':_pctl(eto_daily,10),'median':_pctl(eto_daily,50),'p90':_pctl(eto_daily,90)} if enough(eto_daily) else None,
            'historical_longest_dry_spell_days_lt_1mm':{'p10':_pctl(dry_spells,10),'median':_pctl(dry_spells,50),'p90':_pctl(dry_spells,90)} if enough(dry_spells) else None,
            'illustrative_et_c_mm':{'p10':_pctl(etc,10),'median':_pctl(etc,50),'p90':_pctl(etc,90)} if etc_ok else None,
            'kc_provenance':{crop:{'status':'USER_SUPPLIED_UNVERIFIED',
                                   'source_url':req.crop_profiles[crop].source_url,
                                   'source_title':req.crop_profiles[crop].source_title,
                                   'source_publisher':req.crop_profiles[crop].source_publisher,
                                   'crop_variety':req.crop_profiles[crop].crop_variety,
                                   'review_note':req.crop_profiles[crop].review_note,
                                   'local_stage_applicability_verified':False}
                             for crop in sorted(set(crops)) if req.crop_profiles.get(crop) and req.crop_profiles[crop].stages},
            'idealized_rain_offset_shortfall_mm':{'p10':_pctl(deficit,10),'median':_pctl(deficit,50),'p90':_pctl(deficit,90)} if enough(deficit) else None,
            'years':years,
            'farmer_field_checks':actions,
            'kc_sensitivity_not_statistical_ci':({'median_et_c_if_kc_15pct_lower_mm':round(_pctl(etc,50)*.85,1),
                                                 'median_et_c_if_kc_15pct_higher_mm':round(_pctl(etc,50)*1.15,1),
                                                 'note':'Illustrative ±15% change to every user-entered Kc; a sensitivity exercise, not a Kc uncertainty estimate or confidence interval.'}
                                                if etc_ok else None),
            'quality_note':'At least 8/10 planting cohorts must have 100% daily coverage within occupied crop days; missing days are never filled or treated as zero.' if rain_ok else 'Insufficient complete historical seasons; rainfall distribution withheld.',
            'water_note':('Conditional FAO-56 ETc = daily NASA-derived ETo × user-supplied stage Kc. No local crop, paddy loss, soil storage, or rainfall effectiveness calibration.'
                          if etc_ok else 'Water-demand estimates withheld: supply HTTPS-sourced stage Kc matching crop durations and complete daily NASA meteorology.'),
        })
    source_type=parsed['source_type']; synthetic=req.mode=='synthetic'
    return {'version':'phase42-judge-science-patch','data_class':'SYNTHETIC_REHEARSAL_NOT_NASA' if synthetic else 'HISTORICAL_NASA_POWER',
            'source_mode':req.mode,'forecast':False,'validated_crop_recommendation':False,
            'years':{'planting_cohorts':f'{FIRST_YEAR}–{LAST_YEAR}','minimum_complete_seasons':REQUIRED_YEARS,
                     'historical_not_forecast':True,'end_padding_year':PADDING_YEAR},
            'location':{'latitude':req.latitude,'longitude':req.longitude,'coordinate_source':req.location_source,
                        'field_location_verified':False,'elevation_m':req.elevation_m,'elevation_source':req.elevation_source},
            'assumptions':{'planting_month':req.planting_month,'planting_day':req.planting_day,
                           'gap_days':req.gap_days,'crop_duration_days':req.crop_days.model_dump(),
                           'crop_profiles_user_supplied':{c:p.model_dump() for c,p in req.crop_profiles.items()},
                           'farmer_priority':req.farmer_priority,'irrigation':req.irrigation,
                           'soil':req.soil,'soil_source':req.soil_source},
            'candidates':results,
            'provenance':{'provider':'NASA POWER daily AG point API' if not synthetic else 'SYNTHETIC FUNCTION — NOT NASA',
                          'source_type':source_type,'retrieved_at':parsed['retrieved_at'],
                          'request_url':parsed['request_url'],'raw_payload_sha256':parsed['raw_payload_sha256'],
                          'units_from_nasa_payload':parsed['units'],'solar_to_mj_factor':parsed['solar_conversion_to_mj_m2_day'],
                          'rejected_or_missing_days_by_variable':parsed['rejected_or_missing_days_by_variable'],
                          'fetch_warning':parsed.get('fetch_warning')},
            'methodology':{'daily_reference_et':'FAO-56 grass Penman–Monteith; daily G=0; mean RH approximates actual vapour pressure; Rs converted to MJ/m²/day by metadata; ETc computed only if crop Kc stages provided',
                           'season_window':'Two user-stated crop durations from planting day and a user-stated fallow gap; historical calendar cohorts',
                           'weather_summary':'P10, median, P90 across fully covered planting years; no imputation, no projection; normalised mm per occupied crop day is provided for differently long rotations',
                           'dry_spell':'Longest consecutive crop-occupied days with NASA POWER daily precipitation <1 mm in each historical cohort. Fallow-gap dates break spells. Threshold is a stated screening convention, not a drought declaration.',
                           'kc_provenance':'HTTPS source links are user-provided and syntactically checked, not downloaded, fact-checked or locally reviewed; computed ETc remains an illustrative crop-demand scenario.',
                           'water_balance':'Optimistic ETc minus all rainfall is NOT a farm irrigation recommendation, because rainfall effectiveness, runoff, ponding/percolation, soil water, irrigation schedule and carryover are unknown.'},
            'limitations':[
                'NASA POWER is gridded climate context, not a plot-scale rain gauge or verified farm soil measurement.',
                'A historical season distribution does not forecast a future planting season, yields, flood damage, or drought.',
                'Planting dates, two crop durations, gap and coefficients are farmer/analyst assumptions and are not locally verified.',
                'FAO ETo uses NASA humidity, pressure, wind, radiation and temperature; mean RH approximates actual vapour pressure.',
                'Legacy idealized rain-offset shortfall credits every millimetre of rainfall and is deliberately excluded from judge-facing comparison cards: NOT measured effective rainfall or real irrigation demand.',
                'Crop coefficient source URLs are NOT checked against their content; coefficients, varieties and growth stages require expert review.',
                'Paddy rice water layer, seepage, percolation, land preparation, actual soil-water storage and management are excluded.',
                'No crop yield, suitability ranking, water-savings percentage, planting authorization or farm impact validation is provided.',
            ]+(['SYNTHETIC REHEARSAL — every daily record was fabricated; source links and NASA hashes are deliberately absent.'] if synthetic else [])}


async def calculate(req:SeasonalRequest)->dict:
    return compare(req,await retrieve(req))


def demo_daily()->dict:
    """Completely fabricated daily NASA-shaped weather for *clearly labelled* UI rehearsals."""
    parameters={p:{} for p in PARAMETERS}
    current=date(FIRST_YEAR,1,1);end=date(PADDING_YEAR,12,31)
    while current<=end:
        key=current.strftime('%Y%m%d');m=current.month
        rainy=max(0.,math.sin((m-4)/12*2*math.pi))
        swing=1.+.15*math.sin((current.year-FIRST_YEAR)*1.19)
        values={'PRECTOTCORR':(1.5+rainy*8)*swing,'T2M':28.+1.4*math.cos(m/12*2*math.pi),
                'T2M_MAX':33.+1.4*math.cos(m/12*2*math.pi),'T2M_MIN':23.+1.4*math.cos(m/12*2*math.pi),
                'RH2M':75+rainy*12,'WS2M':2.0,'PS':100.8,'ALLSKY_SFC_SW_DWN':4.1-rainy*.7}
        for p,v in values.items():parameters[p][key]=round(v,4)
        current+=timedelta(days=1)
    units={'PRECTOTCORR':'mm/day','T2M':'C','T2M_MAX':'C','T2M_MIN':'C','RH2M':'%',
           'WS2M':'m/s','PS':'kPa','ALLSKY_SFC_SW_DWN':'kW-hr/m^2/day'}
    return {'properties':{'parameter':parameters},'parameters':{k:{'units':u} for k,u in units.items()}}

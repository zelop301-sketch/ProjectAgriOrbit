"""Botolan El Niño mission: audited NASA POWER comparisons, never a simulated drought map.

The 2026 series requests completed months only (Jan--Oct). Previous 2021--2025
calendar months are the *recent reference*, NOT a WMO 30-year climate normal.
No crop suitability score, field moisture estimate, forecast, or yield claim is made.
"""
from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import httpx

from .climate import (CACHE_ROOT, POWER_URL, PARAMS, fetch_climate, now_utc,
                      summarise, synthetic_data)

BUILD = 'phase34-botolan-evidence-decisions-3.4.0'
LAT, LON = 15.289, 120.024
TARGET_YEAR = 2026
TARGET_END_MONTH = 10
BASELINE_YEARS = (2021, 2022, 2023, 2024, 2025)
MONTHS = ('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec')
PAGASA_DATE = '2026-11-04'
PAGASA_URL = 'https://pagasa.dost.gov.ph/press-release/233?page=2'
MAX_CONCURRENT = asyncio.Semaphore(3)

ROTATIONS = [
    {'id': 'rice-rice', 'name': 'Rice → Rice', 'focus': 'Continuous paddy production',
     'questions': ['Is irrigation reliable throughout both planting windows?',
                   'What are the locally measured soil and water conditions?']},
    {'id': 'rice-mungbean', 'name': 'Rice → Mungbean', 'focus': 'Diversification hypothesis',
     'questions': ['Are soil drainage, the mungbean planting window and seed supply suitable?',
                   'Does an agronomist confirm the proposed sequence for this field?']},
    {'id': 'corn-mungbean', 'name': 'Corn → Mungbean', 'focus': 'Alternate crop sequence',
     'questions': ['Are maize and mungbean suited to local soil, market and season?',
                   'What crop-water budgets are supported by field measurements?']},
]


def mission_metadata() -> dict:
    return {
        'build': BUILD,
        'location': {'name': 'Botolan reference point, Zambales, Philippines',
                     'latitude': LAT, 'longitude': LON,
                     'note': 'Fixed town reference coordinate for a gridded climate demonstration; NOT a surveyed farm or a municipal-scale drought map.'},
        'advisory': {'agency': 'DOST-PAGASA', 'status': 'Very Strong El Niño reported in the tropical Pacific',
                     'issued_on': PAGASA_DATE, 'source_url': PAGASA_URL,
                     'caution': 'National ENSO context is not a Botolan-specific drought declaration. Heavy rainfall is still possible.'},
        'period': {'target': 'January–October 2026 (completed months requested)',
                   'reference': 'Matching calendar months across 2021–2025',
                   'reference_not_climate_normal': True},
        'rotation_options': ROTATIONS,
        'decision_limit': 'Exploratory screening only: no crop sequence is proven suitable or recommended for planting.',
        'official_challenge': 'https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/',
    }


def partial_request():
    params = {'parameters': ','.join(PARAMS), 'community': 'AG',
              'longitude': f'{LON:.5f}', 'latitude': f'{LAT:.5f}',
              'start': f'{TARGET_YEAR}0101', 'end': f'{TARGET_YEAR}{TARGET_END_MONTH:02d}31',
              'format': 'JSON', 'time-standard': 'LST'}
    return params, POWER_URL + '?' + urlencode(params)


async def fetch_2026(*, refresh: bool = False) -> dict:
    """Fetch a bounded, completed-month window; never ask POWER for future dates."""
    params, url = partial_request()
    key = hashlib.sha256(('botolan2026:' + url).encode()).hexdigest()[:24]
    filepath = CACHE_ROOT / ('botolan_' + key + '.json')
    cached = None
    if filepath.exists():
        try:
            cached = json.loads(filepath.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            pass
    if cached and not refresh:
        try:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(cached['fetched_at'])).total_seconds()
            if 0 <= age < 24*3600:
                return summarise(cached['raw'], LAT, LON, TARGET_YEAR, 'nasa_cached', cached['fetched_at'], url)
        except (KeyError, TypeError, ValueError):
            pass
    try:
        async with httpx.AsyncClient(timeout=35, follow_redirects=True) as client:
            response = await client.get(POWER_URL, params=params)
            response.raise_for_status()
            raw = response.json()
        received = now_utc()
        data = summarise(raw, LAT, LON, TARGET_YEAR, 'nasa_api', received, url)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        tmp = filepath.with_suffix('.tmp.' + os.urandom(5).hex())
        try:
            tmp.write_text(json.dumps({'fetched_at': received, 'raw': raw}), encoding='utf-8')
            os.replace(tmp, filepath)
        finally:
            tmp.unlink(missing_ok=True)
        return data
    except (httpx.HTTPError, ValueError, KeyError, TypeError, OSError) as exc:
        if cached:
            try:
                result = summarise(cached['raw'], LAT, LON, TARGET_YEAR, 'nasa_cached', cached['fetched_at'], url)
                result['fetch_warning'] = 'The latest API request failed; a previously obtained NASA response is shown with its original retrieval timestamp.'
                return result
            except (ValueError, TypeError, KeyError):
                pass
        raise RuntimeError('2026 NASA POWER data unavailable; no observed rainfall anomaly can be claimed.') from exc


def _coverage(row: dict, code: str) -> float:
    return float((row.get('coverage_pct_by_variable') or {}).get(code, 0) or 0)


def _rain(row: dict | None) -> float | None:
    if row and _coverage(row, 'PRECTOTCORR') >= 95 and isinstance(row.get('precipitation_mm'), (float, int)):
        return float(row['precipitation_mm'])
    return None


def _temp(row: dict | None) -> float | None:
    if row and _coverage(row, 'T2M') >= 95 and isinstance(row.get('temperature_c'), (float, int)):
        return float(row['temperature_c'])
    return None


def build_comparison(records: dict[int, dict], *, mode: str) -> dict:
    """Aggregate only sufficiently covered matching months; don't interpolate gaps."""
    meta = mission_metadata()
    is_demo = mode == 'synthetic'
    if mode not in ('nasa', 'synthetic'):
        raise ValueError('Unsupported provenance')
    if mode == 'nasa' and any(v.get('source_type') not in ('nasa_api','nasa_cached') for v in records.values()):
        raise ValueError('Synthetic source may not enter a NASA comparison')
    recent = records.get(TARGET_YEAR)
    months = []
    for i in range(TARGET_END_MONTH):
        month = i+1
        sample = recent.get('months', [])[i] if recent and len(recent.get('months', []))>i else None
        rr = _rain(sample)
        rt = _temp(sample)
        baselines = [(year, data['months'][i]) for year,data in records.items()
                     if year in BASELINE_YEARS and len(data.get('months', [])) > i]
        rain_ref = [_rain(row) for _,row in baselines]
        temp_ref = [_temp(row) for _,row in baselines]
        rain_ref = [v for v in rain_ref if v is not None]
        temp_ref = [v for v in temp_ref if v is not None]
        ref = sum(rain_ref)/len(rain_ref) if len(rain_ref)>=3 else None
        t_ref = sum(temp_ref)/len(temp_ref) if len(temp_ref)>=3 else None
        anomaly = (100*(rr/ref-1)) if rr is not None and ref is not None and ref>0 else None
        months.append({'month': month, 'label': MONTHS[i],
                       'rain_2026_mm': round(rr, 1) if rr is not None else None,
                       'rain_reference_mm': round(ref, 1) if ref is not None else None,
                       'rain_anomaly_pct': round(anomaly,1) if anomaly is not None else None,
                       'temp_2026_c': round(rt,1) if rt is not None else None,
                       'temp_reference_c': round(t_ref,1) if t_ref is not None else None,
                       'valid_reference_years': len(rain_ref),
                       'target_rain_coverage_pct': _coverage(sample, 'PRECTOTCORR') if sample else 0,
                       'has_comparison': anomaly is not None})
    complete = all(m['has_comparison'] for m in months)
    total_target = sum(m['rain_2026_mm'] for m in months) if complete else None
    total_ref = sum(m['rain_reference_mm'] for m in months) if complete else None
    anomaly = 100*(total_target/total_ref-1) if complete and total_ref and total_ref>0 else None
    # A descriptive signal, NEVER an official drought classification or ENSO attribution.
    signal = ('Lower than the 2021–2025 same-month average' if anomaly is not None and anomaly <= -10
              else 'Higher than the 2021–2025 same-month average' if anomaly is not None and anomaly >= 10
              else 'Near the 2021–2025 same-month average' if anomaly is not None
              else 'Insufficient NASA coverage for the Jan–Oct comparison')
    urls = []
    for year, data in sorted(records.items()):
        urls.append({'year': year, 'source_type': data.get('source_type'),
                     'retrieved_at': data.get('retrieved_at'),
                     'request_url': data.get('request_url'),
                     'sha256': data.get('raw_payload_sha256')})
    return {**meta, 'data_class': 'SYNTHETIC_DEMO_NOT_NASA' if is_demo else 'HISTORICAL_NASA_POWER',
            'source_status': 'complete_comparison' if complete else 'incomplete',
            'months': months,
            'summary': {'target_rain_jan_oct_mm': round(total_target,1) if total_target is not None else None,
                        'reference_rain_jan_oct_mm': round(total_ref,1) if total_ref is not None else None,
                        'rain_anomaly_pct': round(anomaly,1) if anomaly is not None else None,
                        'signal': signal, 'months_usable': sum(m['has_comparison'] for m in months),
                        'months_requested': TARGET_END_MONTH},
            'provenance': urls,
            'cautions': [
                'NASA POWER is a gridded point dataset; this is NOT field-measured rainfall or soil moisture.',
                '2021–2025 is a five-year recent reference, NOT a 30-year climatological normal.',
                'A rainfall departure alone does not establish local drought or prove El Niño caused the change.',
                'No crop suitability, yield, irrigation savings or crop ranking has been calibrated or validated.',
                'PAGASA El Niño statement applies to the tropical Pacific/Philippines, not an official plot-scale drought status.',
                '95% per-month data coverage required; missing months prevent Jan–Oct comparison.',
            ] + (['SYNTHETIC REHEARSAL: all precipitation and temperature values are fabricated.'] if is_demo else []),
            'next_steps': [
                'Ask the farmer for irrigation availability and planned planting dates.',
                'Measure soil texture/drainage and water access; confirm boundaries if permitted.',
                'Review crop calendars and input requirements with a Zambales agricultural specialist.',
                'Compare NASA gridded context with a local rain gauge before a field decision.',
            ]}


async def load_comparison(*, mode: str = 'nasa', refresh: bool = False) -> dict:
    if mode == 'synthetic':
        records = {year: synthetic_data(LAT, LON, year) for year in (*BASELINE_YEARS, TARGET_YEAR)}
        # Exactly one clearly simulated 2026 deficit experiment. Values are not observed.
        example = copy.deepcopy(records[TARGET_YEAR])
        for row in example['months'][:TARGET_END_MONTH]:
            row['precipitation_mm'] = round(float(row['precipitation_mm'])*0.65, 2)
            row['temperature_c'] = round(float(row['temperature_c'])+1, 2)
        example['raw_payload_sha256'] = None  # Modified scenario is not the original synthetic raw payload.
        example['demo_warning'] = 'The 2026 series is intentionally fabricated: 35% less rain and +1°C relative to the synthetic baseline.'
        records[TARGET_YEAR] = example
        data = build_comparison(records, mode=mode)
        data['simulation_assumption'] = 'Artificial 2026 scenario: 35% lower rain, +1°C. FOR REHEARSAL ONLY.'
        return data
    if mode != 'nasa':
        raise ValueError('Unsupported data mode')
    async def load(year: int):
        try:
            async with MAX_CONCURRENT:
                source = await (fetch_2026(refresh=refresh) if year == TARGET_YEAR else
                                fetch_climate(LAT, LON, year, refresh=refresh))
            return year, source, None
        except (RuntimeError, OSError, ValueError, asyncio.TimeoutError) as exc:
            return year, None, str(exc)
    results = await asyncio.gather(*(load(year) for year in (*BASELINE_YEARS, TARGET_YEAR)))
    records = {year: data for year, data, _ in results if data is not None}
    errors = [{'year': year, 'reason': reason} for year, data, reason in results if data is None]
    if not records:
        raise RuntimeError('NASA POWER not reachable and no cached response was available; no NASA data has been shown.')
    data = build_comparison(records, mode=mode)
    data['failed_years'] = errors
    return data

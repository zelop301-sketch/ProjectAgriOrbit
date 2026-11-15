"""NASA POWER daily-point fetch, provenance, validation and truthful demo fallback."""
from __future__ import annotations

import hashlib
import asyncio
import tempfile
import calendar
import json
import math
import os
from datetime import datetime, timezone, date
from pathlib import Path
from urllib.parse import urlencode

import httpx

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMS = ("T2M", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN")
UNITS = {
    "T2M": "°C",
    "PRECTOTCORR": "mm/day (daily values); mm (monthly sums)",
    "ALLSKY_SFC_SW_DWN": "kWh/m²/day",
}
CACHE_ROOT = Path(os.environ.get("AGRIORBIT_CACHE_DIR", Path(__file__).resolve().parent.parent / ".cache"))


def now_utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def request_details(lat: float, lon: float, year: int):
    params = {
        "parameters": ",".join(PARAMS), "community": "AG",
        "longitude": f"{lon:.5f}", "latitude": f"{lat:.5f}",
        "start": f"{year}0101", "end": f"{year}1231",
        "format": "JSON", "time-standard": "LST",
    }
    url = POWER_URL + "?" + urlencode(params)
    return params, url


def cache_path(lat: float, lon: float, year: int):
    key = f"{lat:.5f}:{lon:.5f}:{year}"
    return CACHE_ROOT / (hashlib.sha256(key.encode()).hexdigest()[:24] + ".json")


def numeric(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value) or value <= -900:
        return None
    return float(value)


def summarise(raw: dict, lat: float, lon: float, year: int, source_type: str, fetched_at: str, url: str):
    try:
        parameters = raw["properties"]["parameter"]
        if not all(isinstance(parameters[name], dict) for name in PARAMS):
            raise KeyError("Parameter shape")
    except (KeyError, TypeError) as exc:
        raise ValueError("Invalid NASA POWER payload: missing daily parameter maps") from exc

    # Verify each calendar key; do not assume that a string shaped like YYYYMMDD
    # represents a real day. Preserve per-variable missingness instead of using zero.
    buckets = {i: {"temp": [], "rain": [], "solar": []} for i in range(1, 13)}
    completeness = {i: {name: 0 for name in PARAMS} for i in range(1, 13)}
    valid_days = set()
    valid_by_variable = {name: set() for name in PARAMS}
    rejected = {name: 0 for name in PARAMS}
    for key in sorted(set().union(*(set(parameters[name]) for name in PARAMS))):
        val = parameters["T2M"].get(key)
        if not isinstance(key, str) or len(key) != 8 or not key.isdigit() or not key.startswith(str(year)):
            continue
        try:
            actual = datetime.strptime(key, "%Y%m%d").date()
        except ValueError:
            continue
        month = actual.month
        t = numeric(val)
        r = numeric(parameters["PRECTOTCORR"].get(key))
        s = numeric(parameters["ALLSKY_SFC_SW_DWN"].get(key))
        # Reject invalid values. In particular, negative precipitation is NOT zero.
        vals = {"T2M": t if t is not None and -90 <= t <= 65 else None,
                "PRECTOTCORR": r if r is not None and 0 <= r <= 2000 else None,
                "ALLSKY_SFC_SW_DWN": s if s is not None and 0 <= s <= 25 else None}
        for name, value in vals.items():
            if value is None:
                rejected[name] += 1
            else:
                completeness[month][name] += 1
                valid_by_variable[name].add(key)
        if vals["T2M"] is not None: buckets[month]["temp"].append(vals["T2M"])
        if vals["PRECTOTCORR"] is not None: buckets[month]["rain"].append(vals["PRECTOTCORR"])
        if vals["ALLSKY_SFC_SW_DWN"] is not None: buckets[month]["solar"].append(vals["ALLSKY_SFC_SW_DWN"])
        if all(v is not None for v in vals.values()): valid_days.add(key)

    if not any(valid_by_variable[name] for name in PARAMS):
        raise ValueError("NASA response contains no usable daily observations")

    months = []
    for m, b in buckets.items():
        days = calendar.monthrange(year, m)[1]
        monthly_counts = completeness[m]
        months.append({
            "month": m,
            "temperature_c": round(sum(b["temp"]) / len(b["temp"]), 2) if b["temp"] else None,
            "precipitation_mm": round(sum(b["rain"]), 2) if b["rain"] else None,
            "solar_kwh_m2_day": round(sum(b["solar"]) / len(b["solar"]), 2) if b["solar"] else None,
            "complete_days": sum(1 for day in valid_days if int(day[4:6]) == m),
            "expected_days": days,
            "valid_days_by_variable": monthly_counts,
            "coverage_pct_by_variable": {name: round(100*count/days, 1) for name,count in monthly_counts.items()},
            "precipitation_is_partial": monthly_counts["PRECTOTCORR"] < days,
        })

    expected = 366 if calendar.isleap(year) else 365
    annual_counts = {name: len(keys) for name, keys in valid_by_variable.items()}
    # An incomplete yearly sum must never be silently displayed as an annual total.
    precip_sufficient = annual_counts["PRECTOTCORR"] >= math.ceil(expected * 0.95)
    temp_sufficient = annual_counts["T2M"] >= math.ceil(expected * 0.95)
    solar_sufficient = annual_counts["ALLSKY_SFC_SW_DWN"] >= math.ceil(expected * 0.95)
    all_t = [v for b in buckets.values() for v in b["temp"]]
    all_r = [v for b in buckets.values() for v in b["rain"]]
    all_s = [v for b in buckets.values() for v in b["solar"]]
    return {
        "source_type": source_type,
        "provider": "NASA POWER" if source_type != "synthetic" else "AgriORBIT synthetic demo",
        "period": f"{year}-01-01 to {year}-12-31",
        "year": year,
        "latitude": lat,
        "longitude": lon,
        "retrieved_at": fetched_at,
        "request_url": url if source_type != "synthetic" else None,
        "parameters": [
            {"code": "T2M", "label": "2 m air temperature", "unit": "°C"},
            {"code": "PRECTOTCORR", "label": "Daily corrected precipitation", "unit": "mm/day; monthly observed sum in mm"},
            {"code": "ALLSKY_SFC_SW_DWN", "label": "All-sky surface shortwave irradiance", "unit": "kWh/m²/day"},
        ],
        "spatial_note": "NASA POWER gridded regional point context, not a measurement of this plot; native resolution varies by variable." if source_type != "synthetic" else "Fabricated educational values; not an Earth observation.",
        "temporal_note": "Historical observations / reanalysis-derived estimates, NOT a forecast for the next crop cycle." if source_type != "synthetic" else "Synthetic example only.",
        "time_standard": "LST (local solar time)",
        "complete_days": len(valid_days),
        "expected_days": expected,
        "data_coverage_pct": round(100 * len(valid_days) / expected, 1),
        "valid_days_by_variable": annual_counts,
        "coverage_pct_by_variable": {name: round(100*count/expected,1) for name,count in annual_counts.items()},
        "rejected_daily_values_by_parameter": rejected,
        "quality_gate": {"minimum_annual_coverage_pct": 95, "annual_precipitation_ready": precip_sufficient,
                         "temperature_ready": temp_sufficient, "solar_ready": solar_sufficient},
        "raw_payload_sha256": hashlib.sha256(json.dumps(raw, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "months": months,
        "summary": {
            "average_temperature_c": round(sum(all_t) / len(all_t), 1) if all_t and temp_sufficient else None,
            "annual_precipitation_mm": round(sum(all_r), 1) if all_r and precip_sufficient else None,
            "average_solar_kwh_m2_day": round(sum(all_s) / len(all_s), 2) if all_s and solar_sufficient else None,
        },
        "warnings": (["Annual rainfall total withheld because fewer than 95% of daily rainfall values are valid."] if not precip_sufficient else []),
    }


def synthetic_data(lat: float, lon: float, year: int):
    """Deterministic FABRICATED data for UI demo, never represented as NASA observations."""
    import calendar
    rain = [25, 18, 20, 35, 115, 230, 310, 365, 290, 190, 80, 38]
    temp = [26.1, 26.7, 28.1, 29.4, 29.7, 28.9, 28.1, 27.9, 28.0, 28.3, 27.8, 26.7]
    solar = [4.9, 5.3, 5.7, 5.9, 5.0, 4.3, 3.8, 3.7, 4.0, 4.4, 4.6, 4.7]
    parameters = {name: {} for name in PARAMS}
    for mon in range(1, 13):
        days = calendar.monthrange(year, mon)[1]
        for day in range(1, days + 1):
            key = f"{year}{mon:02d}{day:02d}"
            parameters["T2M"][key] = temp[mon - 1]
            parameters["PRECTOTCORR"][key] = rain[mon - 1] / days
            parameters["ALLSKY_SFC_SW_DWN"][key] = solar[mon - 1]
    result = summarise({"properties": {"parameter": parameters}}, lat, lon, year, "synthetic", now_utc(), "")
    result["demo_warning"] = "SYNTHETIC DATA: generated for UI demonstration, not NASA or field measurements."
    return result


async def fetch_climate(lat: float, lon: float, year: int, refresh: bool = False):
    params, url = request_details(lat, lon, year)
    filepath = cache_path(lat, lon, year)
    cached = None
    if filepath.exists():
        try:
            cached = json.loads(filepath.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    if cached and not refresh:
        try:
            age = datetime.now(timezone.utc) - datetime.fromisoformat(cached["fetched_at"])
        except (ValueError, TypeError, KeyError):
            age = None
        if age is not None and 0 <= age.total_seconds() < 24 * 3600:
            try:
                return summarise(cached["raw"], lat, lon, year, "nasa_cached", cached["fetched_at"], url)
            except (ValueError, TypeError, KeyError):
                cached = None

    try:
        async with httpx.AsyncClient(timeout=35, follow_redirects=True) as client:
            response = await client.get(POWER_URL, params=params)
            response.raise_for_status()
            raw = response.json()
        fetched_at = now_utc()
        result = summarise(raw, lat, lon, year, "nasa_api", fetched_at, url)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        # Atomic cache replacement avoids torn JSON when two server workers write.
        temp_file = filepath.with_suffix(".tmp." + os.urandom(5).hex())
        try:
            temp_file.write_text(json.dumps({"fetched_at": fetched_at, "raw": raw}), encoding="utf-8")
            os.replace(temp_file, filepath)
        finally:
            temp_file.unlink(missing_ok=True)
        return result
    except (httpx.HTTPError, ValueError, KeyError, TypeError, OSError) as exc:
        if cached:
            try:
                result = summarise(cached["raw"], lat, lon, year, "nasa_cached", cached["fetched_at"], url)
                result["fetch_warning"] = f"Latest fetch failed; displaying cached NASA values from {cached['fetched_at']}."
                return result
            except (ValueError, TypeError, KeyError):
                pass
        raise RuntimeError("NASA POWER could not be reached or returned unusable values. No real data is being displayed; use Synthetic demo only for UI rehearsal.") from exc

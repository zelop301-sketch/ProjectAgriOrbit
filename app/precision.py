"""Multi-season NASA historical evidence and field-boundary screening.

This module does NOT estimate crop yield, ET, NPK, future weather, or pixel-scale
soil moisture. It provides a verifiable, conservative historical comparison.
"""
from __future__ import annotations

import asyncio
import math
import statistics
from typing import Literal

from pydantic import BaseModel, Field

from .climate import fetch_climate, synthetic_data
from .scoring import Farm, compare

# A global limit bounds simultaneous NASA requests across independent users.
_POWER_LIMIT = asyncio.Semaphore(4)
_MIN_MONTHLY_COVERAGE = 95.0


class PrecisionRequest(BaseModel):
    farm: Farm
    end_year: int = Field(default=2025, ge=1986, le=2025)
    baseline_years: int = Field(default=5, ge=3, le=10)
    mode: Literal["nasa", "synthetic"] = "nasa"


def _month_coordinates(end_year: int, start_month: int) -> list[tuple[int, int]]:
    # A season is the ACTUAL consecutive three-month period ending in end_year;
    # Nov/Dec starts in the previous year, not Jan/Feb earlier in the same year.
    first_year = end_year - (1 if start_month in (11, 12) else 0)
    return [(first_year + (start_month - 1 + i) // 12, (start_month - 1 + i) % 12 + 1)
            for i in range(3)]


def _monthly_coverage(month: dict, code: str) -> float:
    values = month.get("coverage_pct_by_variable") or {}
    if code in values:
        return float(values[code])
    expected = month.get("expected_days")
    if expected is None:
        return 0.0  # Do not claim full coverage when a response omitted it.
    return 100 * int(month.get("complete_days", 0)) / int(expected)


def summarize_season(records: dict[int, dict], end_year: int, start_month: int) -> dict:
    pairs = _month_coordinates(end_year, start_month)
    coverage, monthly = [], []
    for year, month_num in pairs:
        data = records.get(year)
        if not data or len(data.get("months", [])) != 12:
            return {"end_year": end_year, "period": pairs, "usable": False,
                    "reason": f"Missing NASA daily record for {year}.", "precipitation_mm": None}
        row = data["months"][month_num - 1]
        pct = _monthly_coverage(row, "PRECTOTCORR")
        coverage.append(round(pct, 1))
        monthly.append(row)
        if row.get("month") != month_num or pct < _MIN_MONTHLY_COVERAGE or row.get("precipitation_mm") is None:
            return {"end_year": end_year, "period": pairs, "usable": False,
                    "coverage_pct_by_month": coverage,
                    "reason": f"{year}-{month_num:02d} precipitation coverage {pct:.1f}% below 95%, or rainfall missing.",
                    "precipitation_mm": None}
    total = sum(float(row["precipitation_mm"]) for row in monthly)
    temp_weights = [(row.get("temperature_c"), int(row.get("valid_days_by_variable", {}).get("T2M", 0)))
                    for row in monthly]
    temp = (sum(t * n for t, n in temp_weights if t is not None) /
            sum(n for t, n in temp_weights if t is not None)) if any(t is not None and n > 0 for t, n in temp_weights) else None
    return {"end_year": end_year, "period": pairs, "usable": True,
            "precipitation_mm": round(total, 2),
            "average_air_temperature_c": round(temp, 2) if temp is not None else None,
            "coverage_pct_by_month": coverage,
            "source_types": sorted({records[y]["source_type"] for y, _ in pairs}),
            "raw_payload_sha256_by_year": {str(y): records[y].get("raw_payload_sha256") for y, _ in pairs},
            "reason": None}


def compute_benchmark(records: dict[int, dict], *, end_year: int, start_month: int,
                      baseline_years: int, requested_source: str) -> dict:
    series = [summarize_season(records, year, start_month)
              for year in range(end_year - baseline_years, end_year + 1)]
    recent = series[-1]
    usable_baseline = [r for r in series[:-1] if r["usable"]]
    rainfall = [r["precipitation_mm"] for r in usable_baseline]
    # At least 3 independent complete seasons; descriptive only. Five years are
    # insufficient to establish a 30-year climate normal or calibrated drought risk.
    ready = recent["usable"] and len(rainfall) >= 3
    mean = statistics.mean(rainfall) if len(rainfall) >= 3 else None
    median = statistics.median(rainfall) if len(rainfall) >= 3 else None
    stdev = statistics.stdev(rainfall) if len(rainfall) >= 3 else None
    anomaly = (100 * (recent["precipitation_mm"] / mean - 1)
               if ready and mean and mean > 0 else None)
    label = "within historic range"
    if anomaly is not None:
        label = "relatively dry" if anomaly <= -20 else "relatively wet" if anomaly >= 20 else "near recent mean"
    # Synthetic values are always explicitly tagged; never claim evidence.
    any_synthetic = requested_source == "synthetic" or any(
        r.get("source_type") == "synthetic" for r in records.values())
    all_nasa = requested_source == "nasa" and bool(records) and all(
        r.get("source_type") in {"nasa_api", "nasa_cached"} for r in records.values())
    quality = ("synthetic_demo" if any_synthetic else
               "historical_nasa" if ready and all_nasa else "insufficient_evidence")
    hashes = sorted({r.get("raw_payload_sha256") for r in records.values() if r.get("raw_payload_sha256")})
    return {
        "status": "ready" if ready else "insufficient_coverage",
        "data_class": quality,
        "historical_only": True,
        "decision_ready_for_planting": False,
        "baseline_years_requested": baseline_years,
        "baseline_seasons_valid": len(rainfall),
        "target_season": recent,
        "reference_seasons": series[:-1],
        "recent_mean_rainfall_mm": round(mean, 2) if mean is not None else None,
        "recent_median_rainfall_mm": round(median, 2) if median is not None else None,
        "historical_stddev_mm": round(stdev, 2) if stdev is not None else None,
        "rainfall_anomaly_pct": round(anomaly, 1) if anomaly is not None else None,
        "rainfall_context": label if ready else "insufficient evidence",
        "minimum_monthly_precipitation_coverage_pct": _MIN_MONTHLY_COVERAGE,
        "provenance": {
            "provider": "AgriORBIT SYNTHETIC DEMO — NOT NASA" if any_synthetic else "NASA POWER",
            "endpoint": "https://power.larc.nasa.gov/api/temporal/daily/point" if not any_synthetic else None,
            "variables": ["PRECTOTCORR (mm/day)", "T2M (°C)", "ALLSKY_SFC_SW_DWN (kWh/m²/day)"],
            "reference_timing": "POWER local solar time (LST); historical daily time series",
            "raw_hashes": hashes,
            "years_loaded": sorted(records),
            "records_by_year": [
                {"year": year, "source_type": r.get("source_type"),
                 "retrieved_at": r.get("retrieved_at"),
                 "coverage_precipitation_pct": (r.get("coverage_pct_by_variable") or {}).get("PRECTOTCORR"),
                 "raw_payload_sha256": r.get("raw_payload_sha256"),
                 "request_url": r.get("request_url")}
                for year, r in sorted(records.items())
            ],
            "spatial_scale": "NASA POWER gridded regional context, NOT farm-plot rainfall or soil moisture",
        },
        "cautions": [
            "Descriptive comparison of the latest complete 3-month season against previous historical seasons; not a forecast.",
            "Five to ten previous seasons are NOT a climatological normal or a drought likelihood estimate.",
            "The ±20% dry/wet label is an illustrative descriptive threshold, not an official drought classification.",
            "Missing daily data invalidates a month below 95% coverage; incomplete years are never treated as dry days.",
            "NASA POWER meteorological grids cannot locate within-field stress or replace measured rainfall gauges.",
            "Crop suitability, yield, economic return, soil pH and nutrient recommendations require local agronomic evidence.",
        ] + (["SYNTHETIC DATA: results cannot be submitted as verified NASA evidence."] if any_synthetic else []),
    }


async def precision_assessment(payload: PrecisionRequest) -> dict:
    # The requested target end year is the last COMPLETED year, currently 2025.
    # For seasons crossing January, load an extra year for the first baseline season.
    cross_year = payload.farm.start_month in (11, 12)
    first = payload.end_year - payload.baseline_years - int(cross_year)
    years = list(range(first, payload.end_year + 1))
    records = {}
    errors = []

    async def load(year: int):
        if payload.mode == "synthetic":
            return year, synthetic_data(payload.farm.latitude, payload.farm.longitude, year), None
        try:
            async with _POWER_LIMIT:
                result = await asyncio.wait_for(
                    fetch_climate(payload.farm.latitude, payload.farm.longitude, year), timeout=45)
            return year, result, None
        except (RuntimeError, asyncio.TimeoutError, ValueError) as exc:
            return year, None, str(exc)

    # Concurrency limited globally; existing per-year cache avoids repeated requests.
    responses = await asyncio.gather(*(load(y) for y in years))
    for year, data, error in responses:
        if data is not None:
            records[year] = data
        elif error:
            errors.append({"year": year, "error": error})
    benchmark = compute_benchmark(records, end_year=payload.end_year,
                                  start_month=payload.farm.start_month,
                                  baseline_years=payload.baseline_years,
                                  requested_source=payload.mode)
    # Existing heuristic scenario scores are exposed as separate, unvalidated
    # comparison: historical benchmark NEVER calibrates their numeric values.
    comparison = compare(payload.farm)
    return {"benchmark": benchmark, "comparison": comparison,
            "farm": payload.farm.model_dump(), "years_requested": years,
            "years_received": sorted(records), "failed_years": errors,
            "quality_gate_passed": benchmark["status"] == "ready" and benchmark["data_class"] == "historical_nasa",
            "science_notice": "NASA historical benchmark is observational context only. The three crop scores remain UNVALIDATED heuristics; no field-specific crop recommendation is authorized."}

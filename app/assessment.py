"""Transparent historical-rainfall *screening proxy*, not agronomic suitability.

Only call through the backend /api/assess route: its NASA or synthetic payload
is obtained server-side rather than trusting an arbitrary browser claim.
"""
from __future__ import annotations

import calendar
from datetime import date


MONTH_NAMES = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
ALLOWED = {"nasa_api", "nasa_cached", "synthetic"}


def season_context(climate: dict, start_month: int) -> dict:
    if start_month not in range(1, 13):
        raise ValueError("start_month must be 1 through 12")
    if climate.get("source_type") not in ALLOWED or len(climate.get("months", [])) != 12:
        raise ValueError("Unsupported climate format")

    months = [((start_month - 1 + i) % 12) + 1 for i in range(3)]
    rows = [climate["months"][i - 1] for i in months]
    year = int(climate["year"])
    periods = [calendar.monthrange(year, i)[1] for i in months]
    coverage = [round(100 * row["complete_days"] / period) for row, period in zip(rows, periods)]
    annual = climate["summary"].get("annual_precipitation_mm")
    is_usable = bool(annual and annual > 0) and all(
        coverage[i] >= 80 and rows[i].get("precipitation_mm") is not None for i in range(3)
    )
    total = round(sum(row.get("precipitation_mm") or 0 for row in rows), 1)
    annual_quarter = round(annual / 4, 1) if annual is not None else None
    ratio = total / annual_quarter if is_usable and annual_quarter and annual_quarter > 0 else None
    deficit = round(min(1, max(0, 1 - ratio)), 4) if ratio is not None else None
    selected = "–".join(MONTH_NAMES[i - 1] for i in months)
    year_wrap = start_month in (11, 12)
    year_wrap_note = ("CAUTION: This selection groups months from the SAME calendar year in cyclic month order. It does not represent three chronologically consecutive observed months; January/February precede November/December. Use for seasonal-pattern illustration only." if year_wrap else "The selected months are chronologically consecutive in the selected calendar year.")
    return {
        "window": selected,
        "start_month": start_month,
        "months": months,
        "calendar_grouping_note": year_wrap_note,
        "rainfall_mm": total if is_usable else None,
        "annual_rainfall_mm": annual,
        "three_month_annual_mean_mm": annual_quarter,
        "rainfall_fraction_of_annual_pct": round(total / annual * 100, 1) if annual and is_usable else None,
        "ratio_to_equal_3_month_share": round(ratio, 3) if ratio is not None else None,
        "within_year_dry_share": deficit,
        "coverage_pct_by_month": coverage,
        "usable": is_usable,
        "status": ("SYNTHETIC REHEARSAL" if climate["source_type"] == "synthetic" else
                   "NASA HISTORICAL / CACHED" if climate["source_type"] == "nasa_cached" else
                   "NASA HISTORICAL / API"),
        "method": "Historical selected 3-month rainfall / (observed annual rainfall ÷ 4). A ratio below 1 indicates a relatively drier 3-month window WITHIN THAT YEAR, not a climate-change anomaly or crop-water deficit.",
        "notice": ("UNUSABLE: at least 80% of each selected month's daily records are required; no adjustment applied."
                   if not is_usable else
                   "A retrospective seasonal context only: not a planting forecast, crop water requirement, field rainfall gauge, flood-risk measure, or crop-suitability determination. " + year_wrap_note),
    }


def exposure_penalty(context: dict, demand_index: float, irrigation: str, multiplier: float = 1.0) -> int:
    """Illustrative downside-only water proxy. 0-24 points; not validated."""
    if not context["usable"]:
        return 0
    if multiplier <= 0:
        raise ValueError("multiplier must be positive")
    window = context["rainfall_mm"] * multiplier
    annual_quarter = context["three_month_annual_mean_mm"]
    deficit = min(1, max(0, 1 - window / annual_quarter)) if annual_quarter else 0
    irrigation_factor = {"none": 1.0, "limited": 0.65, "reliable": 0.25}[irrigation]
    return round(24 * deficit * (demand_index / 3) * irrigation_factor)

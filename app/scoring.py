"""Explainable *illustrative* crop-rotation comparison: NOT agronomic validation."""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal
from .assessment import season_context, exposure_penalty


class Priorities(BaseModel):
    water: int = Field(default=5, ge=0, le=10)
    soil_cover: int = Field(default=5, ge=0, le=10)
    diversity: int = Field(default=5, ge=0, le=10)
    affordability: int = Field(default=5, ge=0, le=10)
    simplicity: int = Field(default=5, ge=0, le=10)


class Farm(BaseModel):
    name: str = Field(default="Botolan pilot farm", max_length=90)
    latitude: float = Field(default=15.289, ge=-90, le=90)
    longitude: float = Field(default=120.024, ge=-180, le=180)
    area_ha: float = Field(default=1.0, gt=0, le=100000)
    texture: Literal["unknown", "sandy", "loamy", "clayey"] = "unknown"
    soil_ph: float | None = Field(default=None, ge=0, le=14)
    organic_matter_pct: float | None = Field(default=None, ge=0, le=100)
    irrigation: Literal["none", "limited", "reliable"] = "limited"
    current_crop: str = Field(default="Rice", min_length=1, max_length=70)
    start_month: int = Field(default=6, ge=1, le=12, description="Beginning of an illustrative 3-month planning window")
    soil_source: Literal["farmer_entered", "field_measured", "laboratory"] = "farmer_entered"
    priorities: Priorities = Field(default_factory=Priorities)


CRITERIA = [
    ("water", "Water feasibility"),
    ("soil_cover", "Soil cover (proxy)"),
    ("diversity", "Rotation diversity"),
    ("affordability", "Cost simplicity (proxy)"),
    ("simplicity", "Practice continuity"),
]


def compare(farm: Farm, climate: dict | None = None):
    # Heuristic prototype values only. NO measured yield, ROI, nitrogen balance or crop suitability.
    scenarios = [
        {
            "id": "A", "title": "Current practice", "type": "Baseline",
            "crops": [farm.current_crop, farm.current_crop],
            "base": [35, 30, 20, 90, 95], "water_demand_index": 3,
            "description": "Keeps the reported current crop in a repeated sequence for a baseline comparison.",
            "evidence_references": [],
            "watchout": "A baseline cannot establish crop suitability or future yield; ask for local rotation history.",
        },
        {
            "id": "B", "title": "Legume-based option", "type": "Legume rotation",
            "crops": [farm.current_crop, "Mung bean"],
            "base": [72, 65, 70, 68, 74], "water_demand_index": 2,
            "description": "Introduces a legume candidate for agronomist review; nitrogen and soil effects are not quantified.",
            "evidence_references": [
                {"title": "DA-PhilRice Palayamanan: crop rotation (rice–legumes–rice)", "url": "https://www.pinoyrice.com/wp-content/uploads/palayamanan.pdf", "use": "General support for considering crop rotation; does NOT validate mung bean at this plot or the numerical scores."},
                {"title": "FAO: Soil health for paddy rice (Philippine farmer-field-school practices)", "url": "https://www.fao.org/family-farming/detail/en/c/1637590/", "use": "General soil-health context; no claimed local yield impact."},
            ],
            "watchout": "Validate mung bean variety, soil chemistry, sowing dates, water and pest conditions locally.",
        },
        {
            "id": "C", "title": "Diversified option", "type": "Multiple crops",
            "crops": ["Maize", "Mung bean", "Sweet potato"],
            "base": [64, 83, 95, 50, 48], "water_demand_index": 2.4,
            "description": "Tests a more diverse sequence with an illustrative soil-cover proxy.",
            "evidence_references": [
                {"title": "FAO: Soil health for paddy rice", "url": "https://www.fao.org/family-farming/detail/en/c/1637590/", "use": "Supports examining cropping-system diversity; does NOT verify maize or sweet potato at this site."},
            ],
            "watchout": "Crop calendar, market access, inputs and agronomic suitability are not verified.",
        },
    ]
    context = season_context(climate, farm.start_month) if climate is not None else None
    priorities = farm.priorities.model_dump()
    weights = {k: max(0, v) for k, v in priorities.items()}
    if sum(weights.values()) == 0:
        weights = {k: 1 for k in weights}
    total_weight = sum(weights.values())
    outputs = []
    for scenario in scenarios:
        water, cover, diversity, affordability, simplicity = scenario["base"]
        adjustments = []
        if farm.irrigation == "none":
            p = 24 if scenario["water_demand_index"] >= 3 else 10
            water -= p
            adjustments.append(f"No irrigation: -{p} water points (prototype assumption).")
        elif farm.irrigation == "limited":
            p = 12 if scenario["water_demand_index"] >= 3 else 3
            water -= p
            adjustments.append(f"Limited irrigation: -{p} water points (prototype assumption).")
        if farm.texture == "sandy":
            p = 10 if scenario["water_demand_index"] >= 3 else 3
            water -= p
            adjustments.append(f"Sandy texture: -{p} water points; local infiltration not measured.")
        climate_penalty = exposure_penalty(context, scenario["water_demand_index"], farm.irrigation) if context else 0
        if climate_penalty:
            water -= climate_penalty
            adjustments.append(f"Historical 3-month relative rainfall share: -{climate_penalty} water points (UNVALIDATED seasonal exposure proxy; NOT a crop water requirement).")
        if context and not context["usable"]:
            adjustments.append("Historical rainfall record insufficient for this 3-month window; climate adjustment skipped.")
        values = [max(0, round(v)) for v in (water, cover, diversity, affordability, simplicity)]
        breakdown = [
            {"key": k, "label": label, "score": val, "weight": round(weights[k] / total_weight * 100, 1)}
            for (k, label), val in zip(CRITERIA, values)
        ]
        score = round(sum(item["score"] * weights[item["key"]] for item in breakdown) / total_weight)
        outputs.append({
            "id": scenario["id"], "title": scenario["title"], "type": scenario["type"],
            "crops": scenario["crops"], "score": score, "breakdown": breakdown,
            "evidence_references": scenario["evidence_references"],
            "description": scenario["description"], "watchout": scenario["watchout"],
            "adjustments": adjustments,
            "climate_water_penalty": climate_penalty,
            "rainfall_stress_test": ({
                "drier_20_pct_water_penalty": exposure_penalty(context, scenario["water_demand_index"], farm.irrigation, 0.8),
                "wetter_20_pct_water_penalty": exposure_penalty(context, scenario["water_demand_index"], farm.irrigation, 1.2),
                "note": "Counterfactual ±20% change to historical 3-month rainfall only. NOT a forecast or probability."
            } if context and context["usable"] else None),
            "score_note": "Unvalidated planning heuristic (0–100); neither yield, profit nor agronomic suitability.",
        })
    outputs.sort(key=lambda x: (-x["score"], x["id"]))
    missing = [
        "Locally verified crop calendars and crop-specific requirements",
        "Agronomist review of each proposed crop sequence",
        "Plot-specific soil test and nutrient measurements",
        "Local prices, labor, input costs and market access",
        "Season-specific forecast and planting decisions; historical NASA data is not a forecast",
    ]
    if farm.soil_ph is None:
        missing.insert(0, "Soil pH is not supplied")
    if farm.organic_matter_pct is None:
        missing.insert(0, "Organic matter is not supplied")
    return {
        "farm": farm.model_dump(), "scenarios": outputs,
        "season_context": context,
        "comparison_mode": "historical_climate_screening" if context and context["usable"] else "heuristic_only",
        "data_kind": climate["source_type"] if climate else "none",
        "method": {
            "label": "EXPERIMENTAL / NOT VALIDATED",
            "formula": "Sum(dimension score × farmer-selected importance) / sum(importances), rounded to nearest integer.",
            "weights": {k: round(v / total_weight * 100, 1) for k, v in weights.items()},
            "scoring_input": "Farmer-entered irrigation and texture; prototype crop-sequence proxies. Soil pH and organic matter are recorded but intentionally NOT scored without validated crop ranges.",
            "climate_use": ("If valid historical NASA climate is available, a limited relative-seasonality rainfall exposure penalty is applied to the ILLUSTRATIVE water dimension. This is a proxy using unvalidated demand indices, NOT agronomic suitability."
                            if context and context["usable"] else "No historical climate adjustment is applied; rainfall is unavailable, incomplete or not loaded."),
            "climate_formula": "Dry share = max(0, 1 − (3-month rainfall ÷ (annual rainfall / 4))). Water penalty = round(24 × dry share × illustrative water-demand index / 3 × irrigation factor [none 1, limited .65, reliable .25]). Capped by the 0–100 water dimension.",
            "calibration": "The baseline point values and adjustments are illustrative design assumptions, not calibrated agronomic reference ranges.",
        },
        "missing_evidence": missing,
        "advisory": "Scenario ordering and climate stress tests are prototype planning exercises. Do not plant, invest or apply nutrients on this basis without local agricultural extension or agronomist review.",
    }

from app.scoring import Farm, compare


def test_always_three_scenarios_and_explanations():
    result = compare(Farm())
    assert {s["id"] for s in result["scenarios"]} == {"A", "B", "C"}
    assert all(0 <= s["score"] <= 100 and s["watchout"] for s in result["scenarios"])
    assert "NOT VALIDATED" in result["method"]["label"]
    assert "NOT scored" in result["method"]["scoring_input"]


def test_weights_change_scenario_ordering():
    water = compare(Farm(priorities={"water": 10, "soil_cover": 0, "diversity": 0, "affordability": 0, "simplicity": 0}))
    affordable = compare(Farm(priorities={"water": 0, "soil_cover": 0, "diversity": 0, "affordability": 10, "simplicity": 0}))
    assert water["scenarios"][0]["id"] == "B"
    assert affordable["scenarios"][0]["id"] == "A"


def test_sandy_texture_penalizes_water_intensive_baseline():
    regular = {x["id"]: x for x in compare(Farm(texture="loamy"))["scenarios"]}
    sandy = {x["id"]: x for x in compare(Farm(texture="sandy"))["scenarios"]}
    assert sandy["A"]["score"] < regular["A"]["score"]


def test_zero_weights_have_defined_behavior():
    result = compare(Farm(priorities={"water": 0, "soil_cover": 0, "diversity": 0, "affordability": 0, "simplicity": 0}))
    assert sum(result["method"]["weights"].values()) == 100

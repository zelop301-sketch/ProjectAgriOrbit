from app.climate import numeric, summarise, synthetic_data


def test_synthetic_is_never_claimed_as_nasa():
    d = synthetic_data(15.289, 120.024, 2025)
    assert d["source_type"] == "synthetic"
    assert d["provider"] != "NASA POWER"
    assert d["request_url"] is None
    assert len(d["months"]) == 12
    assert d["complete_days"] == 365


def test_missing_sentinel_is_removed_not_averaged():
    raw = {"properties": {"parameter": {
        "T2M": {"20250101": 27, "20250102": -999},
        "PRECTOTCORR": {"20250101": 4, "20250102": 5},
        "ALLSKY_SFC_SW_DWN": {"20250101": 4.5, "20250102": 3.4},
    }}}
    result = summarise(raw, 15.2, 120.0, 2025, "nasa_api", "2026-11-11T00:00:00+00:00", "https://power.larc.nasa.gov")
    assert result["complete_days"] == 1
    assert result["months"][0]["temperature_c"] == 27
    assert result["months"][0]["precipitation_mm"] == 9
    assert numeric(-999) is None


def test_bad_payload_rejected():
    try:
        summarise({}, 15.2, 120, 2025, "nasa_api", "now", "url")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")

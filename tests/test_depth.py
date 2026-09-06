"""Depth profiles, and the limits of what the paper declared."""

from __future__ import annotations

import pytest

import jerlov
from jerlov import _data


def test_the_top_layer_is_the_type_itself():
    for water_type in ("I", "IA", "IB", "II", "III", "1C", "3C", "5C", "7C", "9C"):
        assert jerlov.water_type_at_depth(water_type, 0.0) == water_type
        assert jerlov.water_type_at_depth(water_type, 9.9) == water_type


def test_clear_water_degrades_with_depth():
    """Jerlov I is IA by 20 m and IB by 40 m; see the paper's Table 2."""
    assert jerlov.water_type_at_depth("I", 15.0) == "I"
    assert jerlov.water_type_at_depth("I", 25.0) == "IA"
    assert jerlov.water_type_at_depth("I", 45.0) == "IB"
    assert jerlov.water_type_at_depth("I", 195.0) == "IB"


def test_turbid_water_clears_with_depth():
    assert jerlov.water_type_at_depth("3C", 5.0) == "3C"
    assert jerlov.water_type_at_depth("3C", 25.0) == "III"
    assert jerlov.water_type_at_depth("3C", 45.0) == "II"


def test_everything_tends_to_IB():
    """Below about 120 m every declared profile has reached Jerlov IB."""
    for water_type in ("I", "IA", "IB", "II", "III"):
        assert jerlov.water_type_at_depth(water_type, 125.0) == "IB"


def test_undeclared_returns_none_rather_than_guessing():
    # The most turbid type has too few campaigns below the top layer.
    assert jerlov.water_type_at_depth("9C", 15.0) is None
    # Coastal 3C runs out at 70 m.
    assert jerlov.water_type_at_depth("3C", 75.0) is None
    # The paper stops at 200 m.
    assert jerlov.water_type_at_depth("I", 250.0) is None


def test_boundaries_belong_to_the_layer_below():
    assert jerlov.water_type_at_depth("I", 20.0) == "IA"   # start of 20-30
    assert jerlov.water_type_at_depth("I", 19.999) == "I"  # end of 10-20


def test_unknown_type_names_the_alternatives():
    with pytest.raises(KeyError, match="known:"):
        jerlov.water_type_at_depth("IV", 10.0)


def test_negative_depth_is_refused():
    with pytest.raises(ValueError, match="cannot be negative"):
        jerlov.water_type_at_depth("I", -1.0)


def test_the_three_documented_departures_are_marked():
    """The paper chose the second-highest count in 3 of 119 cases."""
    rows = _data._rows("williamson2023_depth.csv")
    marked = {
        (r["surface_water_type"], r["depth_min_m"])
        for r in rows if r["status"] == "second_highest"
    }
    assert marked == {("I", "90"), ("I", "180"), ("IA", "190")}


def test_every_type_has_twenty_layers():
    rows = _data._rows("williamson2023_depth.csv")
    assert len(rows) == 200
    for water_type in ("I", "9C"):
        own = [r for r in rows if r["surface_water_type"] == water_type]
        assert len(own) == 20
        assert own[0]["depth_min_m"] == "0"
        assert own[-1]["depth_max_m"] == "200"


def test_declared_rows_carry_their_campaign_count():
    rows = _data._rows("williamson2023_depth.csv")
    for row in rows:
        if row["status"] in ("ok", "second_highest"):
            assert int(row["n_campaigns"]) >= 10
        elif row["status"] == "undeclared":
            assert row["water_type"] == ""

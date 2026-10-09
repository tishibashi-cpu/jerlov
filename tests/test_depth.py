"""Depth profiles, and the limits of what the paper declared."""

from __future__ import annotations

import math

import numpy as np
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


def test_the_bottom_of_the_profile_is_inside_it():
    """200 m closes the deepest layer; there is no layer below to own it."""
    assert jerlov.water_type_at_depth("I", 200.0) == "IB"
    assert jerlov.water_type_at_depth("I", 199.9) == "IB"
    assert jerlov.water_type_at_depth("I", 200.1) is None


def test_a_depth_that_is_not_a_number_is_refused():
    """NaN used to fall through to None, which reads as the paper's answer."""
    for bad in (float("nan"), float("inf")):
        with pytest.raises(ValueError, match="finite"):
            jerlov.water_type_at_depth("I", bad)


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


# -- descending through the profile ----------------------------------------

def test_descent_within_the_surface_layer_is_beer_lambert():
    wl = np.array([450.0, 550.0])
    d = jerlov.descend("III", 8.0, wl)
    kd = jerlov.water("III", source="jerlov1976").kd(wl)
    assert np.allclose(d.transmittance, np.exp(-kd * 8.0))
    assert d.layers == ((0.0, 8.0, "III"),)


def test_descent_follows_the_type_of_each_layer():
    """1C is 1C to 20 m, III to 40, II below; see the paper's Table 2."""
    d = jerlov.descend("1C", 45.0, 500.0)
    assert [t for _, _, t in d.layers] == ["1C", "1C", "III", "III", "II"]
    assert d.layers[-1] == (40.0, 45.0, "II")
    kd = {t: jerlov.water(t, source="jerlov1976").kd(500.0)
          for t in ("1C", "III", "II")}
    expected = math.exp(-(20 * kd["1C"] + 20 * kd["III"] + 5 * kd["II"]))
    assert d.transmittance == pytest.approx(expected)


def test_clearing_water_lets_more_light_down_than_its_surface_type_says():
    d = jerlov.descend("3C", 60.0, 500.0)
    surface_only = math.exp(-jerlov.water("3C", source="jerlov1976").kd(500.0)
                            * 60.0)
    assert d.transmittance > 10 * surface_only


def test_descent_stops_where_the_paper_declared_nothing():
    jerlov.descend("3C", 70.0, 500.0)          # the last declared layer
    with pytest.raises(jerlov.MissingQuantityError, match="70 and 80 m"):
        jerlov.descend("3C", 70.5, 500.0)
    with pytest.raises(jerlov.MissingQuantityError, match="10 and 20 m"):
        jerlov.descend("9C", 15.0, 500.0)
    with pytest.raises(jerlov.MissingQuantityError, match="below 200 m"):
        jerlov.descend("IB", 250.0, 500.0)


def test_descent_needs_a_source_covering_every_layer():
    """austin1986 has no 3C, which the 3C profile starts in."""
    with pytest.raises(KeyError, match="does not cover"):
        jerlov.descend("3C", 30.0, 500.0, source="austin1986")
    jerlov.descend("I", 30.0, 500.0, source="austin1986")


def test_descent_refuses_what_is_not_a_depth():
    for bad in (-1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            jerlov.descend("I", bad, 500.0)
    with pytest.raises(KeyError, match="known"):
        jerlov.descend("XI", 10.0, 500.0)


def test_descent_to_the_surface_is_no_attenuation():
    d = jerlov.descend("II", 0.0, [450.0, 550.0])
    assert np.all(d.transmittance == 1.0)
    assert d.layers == ()


def test_an_array_of_depths_gives_one_type_per_depth():
    depths = np.array([[0.0, 30.0], [60.0, 250.0]])
    types = jerlov.water_type_at_depth("I", depths)
    assert types.shape == depths.shape
    assert types.tolist() == [["I", "IA"], ["IB", None]]
    for depth, got in zip(depths.ravel(), types.ravel()):
        assert got == jerlov.water_type_at_depth("I", float(depth))
    # A list is an array too; a scalar is still a plain string.
    assert list(jerlov.water_type_at_depth("9C", [5, 15])) == ["9C", None]
    assert isinstance(jerlov.water_type_at_depth("I", np.float64(5)), str)


def test_one_bad_depth_in_an_array_refuses_the_whole_array():
    with pytest.raises(ValueError, match="finite"):
        jerlov.water_type_at_depth("I", [10.0, float("nan")])
    with pytest.raises(ValueError, match="cannot be negative"):
        jerlov.water_type_at_depth("I", [10.0, -1.0])


def test_a_descent_prints_its_path_not_its_arrays():
    """The generated repr printed every wavelength and transmittance."""
    d = jerlov.descend("1C", 45.0, np.arange(400.0, 701.0, 1.0))
    text = repr(d)
    assert text == ("<Descent 1C to 45 m: 1C 0-20, III 20-40, II 40-45 m; "
                    "Kd from jerlov1976; 301 wavelengths>")
    assert repr(jerlov.descend("II", 0.0, 500.0)).startswith(
        "<Descent II to 0 m: no layer crossed;")

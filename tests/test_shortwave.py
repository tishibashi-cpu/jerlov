"""Paulson & Simpson shortwave penetration, and what it does not cover."""

from __future__ import annotations

import numpy as np
import pytest

import jerlov
from jerlov import _data


def test_the_five_oceanic_types_are_present():
    for water_type in ("I", "IA", "IB", "II", "III"):
        p = jerlov.shortwave_parameters(water_type)
        assert 0 < p.R < 1
        assert 0 < p.zeta1_m < p.zeta2_m


def test_the_surface_is_unattenuated():
    for water_type in ("I", "IA", "IB", "II", "III"):
        assert jerlov.solar_fraction(water_type, 0.0) == pytest.approx(1.0)


def test_clearer_water_lets_more_through():
    at30 = [jerlov.solar_fraction(t, 30.0)
            for t in ("I", "IA", "IB", "II", "III")]
    assert at30 == sorted(at30, reverse=True)


def test_it_decays_with_depth():
    previous = 2.0
    for depth in (0.0, 1.0, 5.0, 20.0, 100.0):
        value = jerlov.solar_fraction("IB", depth)
        assert value < previous
        previous = value


def test_the_two_terms_are_red_and_blue_green():
    """zeta1 is metres, zeta2 tens of metres; the fast term dies first."""
    p = jerlov.shortwave_parameters("II")
    assert p.zeta1_m < 3.0
    assert p.zeta2_m > 10.0
    deep = (1 - p.R) * np.exp(-50.0 / p.zeta2_m)
    assert deep / p.fraction_at(50.0) > 0.99   # only the slow term survives


def test_how_far_the_published_fit_sits_from_its_own_source():
    """The published parameters do not reproduce Jerlov Table XXI at 1 m.

    Two exponentials cannot follow the sharp near-surface decay, and Paulson
    & Simpson say so. The error reaches 46 percent at 1 m for types II and
    III, and settles below 25 percent from 2 m down. Pinned here because a
    caller heating a 1 m surface layer should know, and because a change in
    either the parameters or the source table would move these numbers.
    """
    rows = _data._rows("jerlov1968_total_irradiance.csv")
    worst_at_1m, worst_below = 0.0, 0.0
    for row in rows:
        if row["water_type"] not in ("I", "IA", "IB", "II", "III"):
            continue
        if not row["percent_of_surface"]:
            continue
        depth = float(row["depth_m"])
        if depth == 0 or depth > 100:
            continue
        want = float(row["percent_of_surface"]) / 100
        error = abs(jerlov.solar_fraction(row["water_type"], depth) - want) / want
        if depth == 1:
            worst_at_1m = max(worst_at_1m, error)
        else:
            worst_below = max(worst_below, error)

    assert 0.40 < worst_at_1m < 0.50, worst_at_1m
    assert worst_below < 0.25, worst_below


# -- what it does not cover ----------------------------------------------


def test_coastal_types_are_refused_rather_than_substituted():
    for water_type in ("1C", "3C", "5C", "7C", "9C"):
        with pytest.raises(KeyError, match="oceanic types only"):
            jerlov.shortwave_parameters(water_type)


def test_the_alternative_type_I_fit_is_reachable():
    hundred = jerlov.shortwave_parameters("I")
    fifty = jerlov.shortwave_parameters("I_upper50")
    assert hundred.fit_depth_m == 100
    assert fifty.fit_depth_m == 50
    assert fifty.water_type == "I"
    assert fifty.R != hundred.R
    # The paper gives it because the profile changes slope; deeper down they
    # must therefore disagree.
    assert abs(fifty.fraction_at(80.0) - hundred.fraction_at(80.0)) > 1e-4


def test_the_rows_that_are_not_water_types_are_not_offered():
    for key in ("composite_observations", "run_1", "kraus_1972_very_clear"):
        p = jerlov.shortwave_parameters(key)
        assert p.water_type == ""      # reachable by key, but not a type
        assert "Not a Jerlov type" in p.note


def test_negative_depth_is_refused():
    with pytest.raises(ValueError, match="cannot be negative"):
        jerlov.solar_fraction("I", -1.0)


def test_scalar_in_scalar_out():
    assert isinstance(jerlov.solar_fraction("I", 10.0), float)
    assert isinstance(jerlov.solar_fraction("I", [1.0, 10.0]), np.ndarray)

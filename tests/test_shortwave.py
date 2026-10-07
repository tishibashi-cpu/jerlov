"""Paulson & Simpson shortwave penetration, and what it does not cover."""

from __future__ import annotations

import numpy as np
import pytest

import jerlov


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
    worst_at_1m, worst_below = 0.0, 0.0
    for water_type in ("I", "IA", "IB", "II", "III"):
        depths, measured = jerlov.jerlov1968_solar_fraction(water_type)
        for depth, want in zip(depths, measured):
            if depth == 0 or depth > 100 or np.isnan(want):
                continue
            error = abs(jerlov.solar_fraction(water_type, depth) - want) / want
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
    # The paper gives it because the profile changes slope; they must
    # therefore disagree, even inside the 50 m both were fitted over.
    assert abs(fifty.fraction_at(40.0) - hundred.fraction_at(40.0)) > 1e-4


def test_the_rows_that_are_not_water_types_are_not_offered():
    """They used to come back like any type, so `solar_fraction("run_1", z)`
    gave a Jerlov-looking answer for one cruise's run."""
    for key in ("composite_observations", "run_1", "kraus_1972_very_clear"):
        with pytest.raises(KeyError, match="not a Jerlov water type"):
            jerlov.shortwave_parameters(key)
        with pytest.raises(KeyError, match="not a Jerlov water type"):
            jerlov.solar_fraction(key, 10.0)
        p = jerlov.shortwave_parameters(key, include_non_types=True)
        assert p.water_type == ""      # reachable when asked for, not a type
        assert "Not a Jerlov type" in p.note


def test_negative_depth_is_refused():
    with pytest.raises(ValueError, match="cannot be negative"):
        jerlov.solar_fraction("I", -1.0)


def test_scalar_in_scalar_out():
    assert isinstance(jerlov.solar_fraction("I", 10.0), float)
    assert isinstance(jerlov.solar_fraction("I", [1.0, 10.0]), np.ndarray)


def test_a_depth_that_is_nan_is_refused():
    with pytest.raises(ValueError, match="not NaN"):
        jerlov.solar_fraction("I", float("nan"))
    with pytest.raises(ValueError, match="not NaN"):
        jerlov.solar_fraction("I", [1.0, float("nan")])


def test_table_xxi_is_public():
    depths, fraction = jerlov.jerlov1968_solar_fraction("I")
    assert depths[0] == 0 and fraction[0] == 1.0
    assert fraction[list(depths).index(10.0)] == pytest.approx(0.222)
    # Blanks in the table stay blanks.
    assert np.isnan(fraction[list(depths).index(20.0)])
    # All ten types, coastal included, though Paulson & Simpson fitted five.
    for t in ("1C", "3C", "5C", "7C", "9C"):
        assert len(jerlov.jerlov1968_solar_fraction(t)[0]) == 12
    with pytest.raises(KeyError, match="known:"):
        jerlov.jerlov1968_solar_fraction("IV")


def test_below_the_fitted_depth_it_warns():
    """Paulson & Simpson fitted the upper 100 m, and 50 m for I_upper50."""
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        jerlov.solar_fraction("IB", 100.0)
        jerlov.shortwave_parameters("I_upper50").fraction_at([0.0, 50.0])
    with pytest.warns(jerlov.ProvenanceWarning, match="upper 100 m"):
        jerlov.solar_fraction("IB", 100.5)
    with pytest.warns(jerlov.ProvenanceWarning, match="upper 50 m"):
        jerlov.shortwave_parameters("I_upper50").fraction_at([10.0, 60.0])


def test_rows_that_are_not_types_carry_no_fit_depth_and_do_not_warn():
    import warnings

    p = jerlov.shortwave_parameters("run_1", include_non_types=True)
    assert p.fit_depth_m is None
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        p.fraction_at(150.0)

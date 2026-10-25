"""Scalar PAR from a mean cosine and a reflectance the caller gives
(DECISIONS.md section 59)."""

from __future__ import annotations

import numpy as np
import pytest

import jerlov

WL = np.arange(400.0, 701.0, 5.0)
SURFACE = np.interp(WL, *jerlov.d65())
DEPTHS = (0.0, 10.0, 20.0)


def _profile(depths=DEPTHS):
    return jerlov.par_profile(SURFACE, WL, depths,
                              kd=jerlov.water("II", source="jerlov1976"),
                              unit="energy")


def _hemisphere(steps: int = 200_000):
    """Ed and E0 of unit radiance over one hemisphere, by the midpoint rule
    in the cosine: Ed = 2 pi int mu dmu, E0 = 2 pi int dmu."""
    mu = (np.arange(steps) + 0.5) / steps
    planar = 2 * np.pi * mu.mean()
    scalar = 2 * np.pi
    return planar, scalar


def test_a_beam_straight_down_has_scalar_equal_to_planar():
    p = _profile()
    np.testing.assert_allclose(p.scalar_par(mean_cosine=1, reflectance=0),
                               p.par)


def test_uniform_downwelling_radiance_has_scalar_twice_planar():
    ed, e0 = _hemisphere()
    assert ed == pytest.approx(np.pi) and e0 == pytest.approx(2 * np.pi)
    p = _profile()
    np.testing.assert_allclose(
        p.scalar_par(mean_cosine=ed / e0, reflectance=0), 2 * p.par)


def test_light_only_straight_up_and_down_is_the_limit():
    """Ed = 1, Eu = R: E0 = 1 + R, so the mean cosine is (1 - R) / (1 + R)."""
    p = _profile()
    r = 0.3
    np.testing.assert_allclose(
        p.scalar_par(mean_cosine=(1 - r) / (1 + r), reflectance=r),
        (1 + r) * p.par)
    with pytest.raises(ValueError, match="at least Ed \\+ Eu"):
        p.scalar_par(mean_cosine=(1 - r) / (1 + r) + 1e-6, reflectance=r)


def test_values_per_depth_are_applied_depth_by_depth():
    p = _profile()
    mu = np.array([0.8, 0.75, 0.7])
    r = np.array([0.02, 0.03, 0.04])
    np.testing.assert_allclose(p.scalar_par(mean_cosine=mu, reflectance=r),
                               p.par * (1 - r) / mu)
    one = _profile(depths=5.0)
    assert one.scalar_par(mean_cosine=0.5, reflectance=0) == pytest.approx(
        2 * one.par)


@pytest.mark.parametrize("mu, r, match", [
    (0.0, 0.0, "mean_cosine must lie"),
    (1.1, 0.0, "mean_cosine must lie"),
    (0.7, -0.01, "reflectance must lie"),
    (0.7, 1.0, "reflectance must lie"),
    (np.nan, 0.0, "must be finite"),
    (0.7, np.inf, "must be finite"),
    ([0.7, 0.7], 0.0, "one value per depth"),
])
def test_values_outside_a_light_field_are_refused(mu, r, match):
    with pytest.raises(ValueError, match=match):
        _profile().scalar_par(mean_cosine=mu, reflectance=r)


def test_neither_has_a_default():
    p = _profile()
    with pytest.raises(TypeError):
        p.scalar_par(mean_cosine=0.7)
    with pytest.raises(TypeError):
        p.scalar_par(0.7, 0.0)

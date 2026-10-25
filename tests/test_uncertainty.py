"""A measured Kd's uncertainty carried through to PAR and to the nearest
type (DECISIONS.md section 57)."""

from __future__ import annotations

import math
import warnings

import numpy as np
import pytest

import jerlov

WL = np.arange(400.0, 701.0, 5.0)
SURFACE = np.interp(WL, *jerlov.d65())
FLAT = np.full(WL.shape, 0.1)


def _profile(kd=FLAT, sigma=None, depths=(0.0, 10.0, 20.0), **kwargs):
    return jerlov.par_profile(SURFACE, WL, list(depths), kd=kd,
                              kd_uncertainty=sigma, unit="energy", **kwargs)


def test_a_flat_kd_gives_bounds_at_ln_1_over_f_over_kd_plus_and_minus():
    """With the same Kd at every wavelength the depth of f is ln(1/f) / Kd
    whatever the spectrum, so the bounds are ln(1/f) / (Kd +- k sigma)."""
    p = _profile(sigma=np.full(WL.shape, 0.01))
    for fraction in (0.1, 0.01):
        shallow, deep = p.depth_of_fraction_bounds(fraction)
        assert shallow == pytest.approx(math.log(1 / fraction) / 0.11,
                                        rel=1e-9)
        assert deep == pytest.approx(math.log(1 / fraction) / 0.09,
                                     rel=1e-9)
    shallow, deep = p.depth_of_fraction_bounds(0.01, k=2)
    assert (shallow, deep) == pytest.approx(
        (math.log(100) / 0.12, math.log(100) / 0.08), rel=1e-9)


def test_par_bounds_are_the_shifted_exponentials_and_the_surface_has_none():
    p = _profile(sigma=np.full(WL.shape, 0.01))
    lower, higher = p.par_bounds()
    assert lower[0] == higher[0] == p.surface_par
    np.testing.assert_allclose(lower, p.surface_par
                               * np.exp(-0.11 * np.array([0, 10, 20])))
    np.testing.assert_allclose(higher, p.surface_par
                               * np.exp(-0.09 * np.array([0, 10, 20])))
    assert np.all(lower <= p.par) and np.all(p.par <= higher)


def test_bounds_bracket_the_depth_and_shrink_to_it():
    kd = jerlov.water("III", source="jerlov1976").kd(WL)
    p = _profile(kd=kd, sigma=0.05 * kd)
    z = p.depth_of_fraction(0.01)
    shallow, deep = p.depth_of_fraction_bounds(0.01)
    assert shallow < z < deep
    wider = p.depth_of_fraction_bounds(0.01, k=2)
    assert wider[0] < shallow and deep < wider[1]
    assert p.depth_of_fraction_bounds(0.01, k=0) == pytest.approx((z, z))
    zero = _profile(kd=kd, sigma=np.zeros(WL.shape))
    assert zero.depth_of_fraction_bounds(0.01) == pytest.approx((z, z))


def test_a_water_with_an_uncertainty_gives_the_same_bounds_as_arrays():
    kd = jerlov.water("III", source="jerlov1976").kd(WL)
    w = jerlov.Water.from_measurements(WL, kd=kd,
                                       uncertainty={"kd": 0.05 * kd})
    from_water = _profile(kd=w)
    from_arrays = _profile(kd=kd, sigma=0.05 * kd)
    assert from_water.depth_of_fraction_bounds(0.01) == pytest.approx(
        from_arrays.depth_of_fraction_bounds(0.01))


def test_published_types_and_descents_have_no_range():
    for kd in (jerlov.water("II", source="jerlov1976"), FLAT):
        with pytest.raises(jerlov.MissingQuantityError, match="no range"):
            _profile(kd=kd).depth_of_fraction_bounds()
    descent = jerlov.descend("II", 100.0, WL)
    p = _profile(kd=descent)
    with pytest.raises(jerlov.MissingQuantityError,
                       match="publish no uncertainty"):
        p.par_bounds()
    with pytest.raises(ValueError, match="goes with an array kd"):
        _profile(kd=descent, sigma=np.full(WL.shape, 0.01))


def test_a_water_and_kd_uncertainty_together_are_refused():
    w = jerlov.Water.from_measurements(WL, kd=FLAT)
    with pytest.raises(ValueError, match="carries its own"):
        _profile(kd=w, sigma=np.full(WL.shape, 0.01))


def test_a_gap_in_the_uncertainty_is_refused_only_when_a_range_is_asked():
    sigma = np.full(WL.shape, 0.01)
    sigma[10] = np.nan
    p = _profile(sigma=sigma)
    assert p.depth_of_fraction(0.01) == pytest.approx(math.log(100) / 0.1)
    with pytest.raises(jerlov.MissingQuantityError, match="gap"):
        p.depth_of_fraction_bounds(0.01)
    outside = np.full(WL.shape, 0.01)
    outside[0] = np.nan
    wide = jerlov.par_profile(SURFACE, WL, 0.0, kd=FLAT,
                              kd_uncertainty=outside, unit="energy",
                              band=(450.0, 650.0))
    assert wide.depth_of_fraction_bounds(0.01)[0] == pytest.approx(
        math.log(100) / 0.11)


def test_an_uncertainty_larger_than_kd_is_refused_not_clipped():
    sigma = np.full(WL.shape, 0.01)
    sigma[20] = 0.2
    p = _profile(sigma=sigma)
    with pytest.raises(ValueError, match="negative at 500 nm"):
        p.depth_of_fraction_bounds(0.01)


@pytest.mark.parametrize("sigma", [-0.01, np.inf])
def test_a_negative_or_infinite_uncertainty_is_refused(sigma):
    with pytest.raises(ValueError, match="finite and not negative"):
        _profile(sigma=np.full(WL.shape, sigma))


@pytest.mark.parametrize("k", [-1.0, np.nan, np.inf])
def test_k_must_be_finite_and_not_negative(k):
    p = _profile(sigma=np.full(WL.shape, 0.01))
    with pytest.raises(ValueError):
        p.depth_of_fraction_bounds(0.01, k=k)


def test_classify_kd_names_every_type_nearest_within_the_uncertainty():
    """Half-way between II and III, a 30 percent uncertainty makes either
    nearest; a measurement near II with 10 percent leaves only II."""
    wl = np.array([412.0, 443.0, 490.0, 510.0, 555.0])
    ii = jerlov.water("II", source="jerlov1976").kd(wl)
    iii = jerlov.water("III", source="jerlov1976").kd(wl)
    middle = np.sqrt(ii * iii)
    r = jerlov.classify_kd(wl, middle, uncertainty=0.3 * middle)
    assert set(r.nearest_within_uncertainty) == {"II", "III"}
    assert r.nearest_within_uncertainty[0] == r.water_type
    assert "within the uncertainty also" in repr(r)
    near = jerlov.classify_kd(wl, 1.05 * ii, uncertainty=0.1 * ii)
    assert near.nearest_within_uncertainty == ("II",)
    assert jerlov.classify_kd(wl, ii).nearest_within_uncertainty is None


def test_classify_kd_refuses_an_uncertainty_as_large_as_kd():
    wl = np.array([443.0, 490.0])
    kd = jerlov.water("II", source="jerlov1976").kd(wl)
    with pytest.raises(ValueError, match="as large as the value"):
        jerlov.classify_kd(wl, kd, uncertainty=kd)
    with pytest.raises(ValueError, match="one value per wavelength"):
        jerlov.classify_kd(wl, kd, uncertainty=[0.01])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        with pytest.raises(jerlov.MissingQuantityError, match="gap"):
            jerlov.classify_kd(wl, kd, uncertainty=[0.01, np.nan])

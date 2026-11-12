"""A slanted line of sight, Duntley (1963) (DECISIONS.md section 75)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import jerlov
from jerlov import MissingQuantityError

WL = np.array([450.0, 500.0, 550.0])
KD = np.array([0.05, 0.06, 0.09])
ED = np.array([1.0, 1.2, 1.1])
NW = np.array([0.010, 0.012, 0.008])
K = np.array([0.06, 0.07, 0.10])
RHO = np.array([0.3, 0.5, 0.2])


def _scene(depth=10.0):
    return jerlov.Scene(jerlov.water("II"), ED, WL, depth_m=depth)


def _slant(scene, rho, r, zt, **kw):
    args = dict(target_depth_m=zt, kd=KD, water_radiance=NW,
                radiance_attenuation=K, face_irradiance_ratio=1.0)
    args.update(kw)
    return scene.observe_slant(rho, r, **args)


def test_horizontal_is_observe_exactly():
    s = _scene()
    flat = s.observe(RHO, 5.0, veiling_radiance=NW, face_irradiance_ratio=0.6)
    slant = _slant(s, RHO, 5.0, 10.0, face_irradiance_ratio=0.6)
    for name in ("direct", "veiling", "transmittance", "radiance"):
        assert np.array_equal(getattr(flat, name), getattr(slant, name))


def test_written_out():
    s = _scene()
    c = jerlov.water("II").c(WL)
    r, zt = 8.0, 14.0
    got = _slant(s, RHO, r, zt)
    lit = ED * np.exp(-KD * (zt - 10.0))
    assert np.allclose(got.direct, RHO * lit / np.pi * np.exp(-c * r),
                       rtol=1e-14, atol=0)
    assert np.allclose(got.veiling,
                       NW * (1 - np.exp(-c * r - K * (zt - 10.0))),
                       rtol=1e-14, atol=0)


@pytest.mark.parametrize("zt", [4.0, 10.0, 16.0])
def test_a_target_that_is_the_water_reads_as_the_water(zt):
    """With L_target = Nw(zt) = Nw(z) exp(-K (zt - z)) the observer sees
    Nw(z): the check that eq. (12) as printed fails."""
    s = _scene()
    got = _slant(s, RHO, 6.0, zt)
    t = got.transmittance
    lt = NW * np.exp(-K * (zt - 10.0))
    assert np.allclose(lt * t + got.veiling, NW, rtol=1e-14, atol=0)


def _duntley(alpha, kk, cos_theta, r, n_zt, t0, b0):
    """Eq. (12) with the sign in front of the path radiance corrected,
    Duntley's own variables, and eqs. (14) and (15) as printed."""
    def apparent(n0):
        return (n0 * math.exp(-alpha * r) + n_zt
                * math.exp(-kk * r * cos_theta)
                * (1 - math.exp(-alpha * r + kk * r * cos_theta)))
    c0 = (t0 - b0) / b0
    cr = (apparent(t0) - apparent(b0)) / apparent(b0)
    eq14 = 1 - (n_zt / b0) * (1 - math.exp(alpha * r - kk * r * cos_theta))
    return apparent, c0, cr, eq14


@pytest.mark.parametrize("zt", [3.0, 10.0, 15.0])
def test_eqs_13_14_15_through_contrast(zt):
    """K (zt - z) here is -K r cos(theta) in Duntley's eq. (9)."""
    s = _scene()
    r = 9.0
    c = jerlov.water("II").c(WL)
    obs = _slant(s, RHO, r, zt)
    lt = obs.direct / obs.transmittance
    lb = np.array([0.02, 0.01, 0.03])
    nw_zt = NW * np.exp(-K * (zt - 10.0))
    # eq. (13): differences fall as exp(-c r)
    tb = lb * obs.transmittance + obs.veiling
    assert np.allclose(obs.radiance - tb, (lt - lb) * np.exp(-c * r),
                       rtol=1e-13, atol=0)
    for i in range(WL.size):
        cos_theta = -(zt - 10.0) / r
        app, c0, cr, eq14 = _duntley(c[i], K[i], cos_theta, r, nw_zt[i],
                                     lt[i], lb[i])
        assert obs.contrast(lb)[i] == pytest.approx(cr, rel=1e-12)
        assert c0 / cr == pytest.approx(eq14, rel=1e-12)
        # eq. (15): against the water itself
        against_water = obs.contrast(nw_zt)[i]
        c0w = (lt[i] - nw_zt[i]) / nw_zt[i]
        assert against_water == pytest.approx(
            c0w * math.exp(-c[i] * r + K[i] * r * cos_theta), rel=1e-12)


def test_down_loses_contrast_faster_than_up():
    s = _scene()
    r = 6.0
    ratios = []
    for zt in (16.0, 10.0, 4.0):
        obs = _slant(s, RHO, r, zt)
        nw_zt = NW * np.exp(-K * (zt - 10.0))
        lt = obs.direct / obs.transmittance
        ratios.append(obs.contrast(nw_zt) / ((lt - nw_zt) / nw_zt))
    down, flat, up = ratios
    assert np.all(down < flat) and np.all(flat < up)


def test_refusals():
    with pytest.raises(MissingQuantityError, match="depth_m"):
        _slant(jerlov.Scene(jerlov.water("II"), ED, WL), RHO, 5.0, 10.0)
    s = _scene()
    with pytest.raises(ValueError, match="more than"):
        _slant(s, RHO, 3.0, 14.0)
    for zt in (-1.0, np.nan, np.inf, [10.0, 11.0]):
        with pytest.raises(ValueError):
            _slant(s, RHO, 5.0, zt)
    for name in ("water_radiance", "radiance_attenuation",
                 "face_irradiance_ratio"):
        with pytest.raises(MissingQuantityError, match=name):
            _slant(s, RHO, 5.0, 12.0, **{name: None})
    for bad in (-0.01, np.inf, np.array([0.1, 0.1])):
        with pytest.raises(ValueError, match="radiance_attenuation"):
            _slant(s, RHO, 5.0, 12.0, radiance_attenuation=bad)
    with pytest.raises(ValueError, match="water_radiance"):
        _slant(s, RHO, 5.0, 12.0, water_radiance=-NW)
    with pytest.raises(ValueError, match="Kd"):
        _slant(s, RHO, 5.0, 12.0, kd=-KD)
    with pytest.raises(ValueError, match="Descent"):
        _slant(s, RHO, 5.0, 12.0, kd=jerlov.descend("1C", 10.0, WL))
    with pytest.raises(TypeError):
        s.observe_slant(RHO, 5.0, target_depth_m=12.0)


def test_kd_from_a_water_and_a_scalar_k():
    s = _scene()
    w = jerlov.water("II", source="austin1986")
    got = _slant(s, RHO, 5.0, 12.0, kd=w, radiance_attenuation=0.07)
    want = _slant(s, RHO, 5.0, 12.0, kd=w.kd(WL),
                  radiance_attenuation=np.full(3, 0.07))
    assert np.array_equal(got.radiance, want.radiance)


# -- a K the water cannot have (DECISIONS.md section 80) --------------------

def _ib_scene():
    wl = np.array([450.0, 500.0, 550.0])
    water = jerlov.water("IB", source="solonenko2015")
    return wl, water, jerlov.Scene(water, np.ones(3), wl, depth_m=10.0)


def _up(scene, k, r=5.0, zt=5.0):
    return scene.observe_slant(
        np.full(3, 0.5), r, target_depth_m=zt, kd=np.full(3, 0.05),
        water_radiance=np.ones(3), radiance_attenuation=k,
        face_irradiance_ratio=1.0)


def test_a_path_radiance_that_would_be_negative_is_refused():
    """Straight up over 5 m in Jerlov IB, c about 0.09 1/m, with K = 0.15:
    up to 1.10.1 the veiling came out -0.34 Nw."""
    wl, water, scene = _ib_scene()
    assert np.all(water.c(wl) < 0.15)
    with pytest.raises(ValueError, match="path radiance would be negative"):
        _up(scene, 0.15)


def test_k_equal_to_c_straight_up_adds_nothing():
    wl, water, scene = _ib_scene()
    got = _up(scene, water.c(wl))
    assert np.allclose(got.veiling, 0.0, atol=1e-15)
    assert np.all(got.veiling >= 0)


def test_inside_the_tolerance_the_veiling_is_zero_not_just_below():
    """The geometry allows the rise to exceed the distance by a part in
    1e12; the bracket is then a rounding error below zero."""
    wl, water, scene = _ib_scene()
    got = _up(scene, water.c(wl), r=5.0, zt=5.0 - 4e-12)
    assert np.all(got.veiling >= 0)


def test_the_wavelengths_over_the_limit_are_named():
    wl, water, scene = _ib_scene()
    k = water.c(wl) * np.array([0.5, 1.5, 0.5])
    with pytest.raises(ValueError, match=r"at 500 nm"):
        _up(scene, k)


def test_looking_down_is_never_refused_for_it():
    _, _, scene = _ib_scene()
    got = _up(scene, 5.0, r=5.0, zt=15.0)
    assert np.all(got.veiling > 0)


def test_a_slanted_line_up_is_judged_on_the_rise_not_the_distance():
    """K above c is allowed while K times the rise stays below c r."""
    wl, water, scene = _ib_scene()
    c = water.c(wl)
    got = _up(scene, 1.5 * c, r=5.0, zt=7.0)          # rise 3 m of 5
    assert np.all(got.veiling > 0)
    with pytest.raises(ValueError, match="negative"):
        _up(scene, 1.8 * c, r=5.0, zt=7.0)


def test_a_gap_in_k_still_passes_as_nan():
    _, _, scene = _ib_scene()
    got = _up(scene, np.array([0.05, np.nan, 0.05]))
    assert np.isnan(got.veiling[1]) and np.all(got.veiling[[0, 2]] > 0)

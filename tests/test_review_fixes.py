"""Faults found in a review of 0.22.0, each a test that failed before its
fix (DECISIONS.md section 60)."""

from __future__ import annotations

import warnings

import numpy as np
import pytest

import jerlov

WL = np.arange(420.0, 701.0, 10.0)   # inside the measured band
FLAT = np.ones_like(WL)


# -- 1. salinity as an array ------------------------------------------------

@pytest.mark.parametrize("function", [jerlov.pure_water_backscattering,
                                      jerlov.pure_water_scattering])
def test_salinities_are_each_computed(function):
    salinities = [0.0, 20.0, 37.0]
    together = function(500.0, salinity_psu=salinities)
    one_at_a_time = [function(500.0, salinity_psu=s) for s in salinities]
    assert np.shape(together) == (3,)
    assert np.allclose(together, one_at_a_time, rtol=1e-15)
    assert isinstance(function(500.0, salinity_psu=37.0), float)


def test_bb_from_vsf_with_salinities():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.AngleWarning)
        together = jerlov.bb_from_vsf(0.001, 120.0, 500.0,
                                      salinity_psu=[0.0, 37.0])
        apart = [jerlov.bb_from_vsf(0.001, 120.0, 500.0, salinity_psu=s)
                 for s in (0.0, 37.0)]
    assert np.allclose(together.bb, [r.bb for r in apart], rtol=1e-15)
    assert np.allclose(together.water, [r.water for r in apart], rtol=1e-15)
    assert isinstance(apart[0].bb, float)


# -- 2. Scene.at_depth refuses what par_profile refuses ----------------------

@pytest.mark.parametrize("value", [-0.1, np.inf])
def test_at_depth_refuses_an_impossible_kd(value):
    kd = np.full_like(WL, 0.05)
    kd[3] = value
    with pytest.raises(ValueError, match="Kd is negative|kd must be finite"):
        jerlov.Scene.at_depth(jerlov.water("II"), 10.0, FLAT, WL, kd=kd)
    with pytest.raises(ValueError, match="kd must be finite and not negative"):
        jerlov.par_profile(FLAT, WL, [10.0], kd=kd, unit="photons",
                            band=(420.0, 700.0))


def test_at_depth_refuses_an_infinite_depth():
    with pytest.raises(ValueError, match="depth_m must be finite"):
        jerlov.Scene.at_depth(jerlov.water("II"), np.inf, FLAT, WL,
                              kd=np.zeros_like(WL))


def test_at_depth_keeps_a_gap_in_kd_visible():
    kd = np.full_like(WL, 0.05)
    kd[3] = np.nan
    scene = jerlov.Scene.at_depth(jerlov.water("II"), 10.0, FLAT, WL, kd=kd)
    assert np.isnan(scene.downwelling[3])
    assert np.allclose(np.delete(scene.downwelling, 3), np.exp(-0.5))


# -- 3. the constructor checks a status as from_measurements does ------------

def test_constructor_refuses_a_misspelt_status():
    with pytest.raises(ValueError, match="unknown status 'supect'"):
        jerlov.Water([400.0, 500.0], a=[0.1, 0.2],
                     flags={"a": ("supect", "ok")})


@pytest.mark.parametrize("water_type", jerlov.get_source("austin1986")
                         .water_types)
def test_austin_statuses_are_known(water_type):
    w = jerlov.water(water_type, source="austin1986")
    assert set(w._flags["Kd"]) <= {"model", "jerlov_original",
                                   "pure_seawater"}


# -- 4. a negative total coefficient: warned, kept, refused where used -------

def _negative_water():
    a = np.full_like(WL, 0.05)
    a[-2:] = -0.01
    with pytest.warns(jerlov.ProvenanceWarning,
                      match=r"negative values: a at 690, 700 nm"):
        # c = a + b is then -0.005 at 690 and 700 nm.
        w = jerlov.Water.from_measurements(WL, a=a,
                                           b=np.full_like(WL, 0.005),
                                           kd=a + 0.02)
    return w


def test_negative_values_warn_and_are_kept():
    w = _negative_water()
    assert w.a(700.0) == -0.01
    # Kd = a + 0.02 stays positive, so only a is named.
    assert w.kd(700.0) > 0


def test_negative_values_are_refused_where_a_result_rests_on_them():
    w = _negative_water()
    with pytest.raises(ValueError, match="c = a \\+ b is negative at 690"):
        jerlov.Scene(w, FLAT, WL)
    with pytest.raises(ValueError, match="c = a \\+ b is negative"):
        jerlov.veiling_radiance_estimate(w, FLAT, WL, backscatter_ratio=0.02)
    # Where the scene does not reach them, the water is usable.
    blue = WL[WL <= 600.0]
    assert np.all(jerlov.Scene(w, np.ones_like(blue), blue)
                  .transmittance(1.0) < 1)


def test_a_negative_kd_from_a_water_is_refused():
    kd = np.full_like(WL, 0.05)
    kd[0] = -0.01
    with pytest.warns(jerlov.ProvenanceWarning, match="Kd at 420 nm"):
        w = jerlov.Water.from_measurements(WL, kd=kd)
    with pytest.raises(ValueError, match="Kd is negative at 420"):
        jerlov.Scene.at_depth(jerlov.water("II"), 5.0, FLAT, WL, kd=w)
    with pytest.raises(ValueError, match="kd must be finite and not negative"):
        jerlov.par_profile(FLAT, WL, [5.0], kd=w, unit="photons",
                            band=(420.0, 700.0))


def test_a_negative_bb_is_refused_by_the_veiling_estimate():
    b = np.full_like(WL, 0.2)
    b[5] = -0.01
    with pytest.warns(jerlov.ProvenanceWarning, match="b at 470 nm"):
        w = jerlov.Water.from_measurements(WL, a=np.full_like(WL, 0.1), b=b)
    with pytest.raises(ValueError, match="bb is negative at 470"):
        jerlov.veiling_radiance_estimate(w, FLAT, WL, backscatter_ratio=0.02)


def test_shipped_waters_have_no_negative_values():
    with warnings.catch_warnings():
        warnings.simplefilter("error", jerlov.ProvenanceWarning)
        # Building alone warns only for a negative value; flags warn on use.
        for key, source in jerlov.SOURCES.items():
            for water_type in source.water_types:
                jerlov.water(water_type, key)


# -- 5. smaller things -------------------------------------------------------

def test_a_white_with_a_gap_is_refused():
    wl = np.arange(360.0, 831.0)
    white = np.ones_like(wl)
    white[100] = np.nan
    with pytest.raises(ValueError, match="white reference has a gap"):
        jerlov.spectrum_to_srgb(np.ones_like(wl), wl, white=white)


def test_a_one_wavelength_response_is_refused():
    with pytest.raises(ValueError, match="two response wavelengths"):
        jerlov.integrate_response([1.0, 1.0], [500.0, 510.0], [1.0], [505.0])
    with pytest.raises(ValueError, match="response_wavelengths must all be"):
        jerlov.integrate_response([1.0, 1.0], [500.0, 510.0], [1.0, 1.0],
                                  [np.nan, 505.0])


def test_single_number_arguments_say_so():
    scene = jerlov.Scene(jerlov.water("II"), FLAT, WL)
    with pytest.raises(ValueError, match="single distance"):
        scene.transmittance(np.array([1.0, 2.0]))
    assert np.allclose(scene.transmittance(np.array([2.0])),
                       scene.transmittance(2.0))
    with pytest.raises(ValueError, match="backscatter_ratio must be a single"):
        jerlov.water("II").bb(500.0, backscatter_ratio=[0.01, 0.02])
    with pytest.raises(ValueError, match="1-D array"):
        jerlov.water("II").a(np.array([[450.0, 500.0], [550.0, 600.0]]))
    with pytest.raises(ValueError, match="1-D array"):
        jerlov.descend("I", 30.0, [[450.0, 500.0]])


def test_kd_spectrum_on_a_2d_grid():
    at = np.array([[450.0, 500.0], [550.0, 600.0]])
    kd = [0.05, 0.08, 0.1]
    result = jerlov.kd_spectrum(kd, 490.0, at)
    one_at_a_time = np.array([[[jerlov.kd_spectrum(k, 490.0, float(a))
                                for a in row] for row in at] for k in kd])
    assert result.shape == (3, 2, 2)
    assert np.allclose(result, one_at_a_time, rtol=0, atol=1e-15)


"""Kd from chlorophyll and from a and bb, Rrs, and the Secchi depth
(DECISIONS.md section 66).

The constants were read from the papers' page images; each test writes the
paper's equation out by hand, or reproduces a number the paper prints."""

from __future__ import annotations

import math
import warnings

import numpy as np
import pytest

import jerlov

#: Morel & Maritorena (2001) Table 2 at a few wavelengths: Kw, e, chi.
TABLE2 = {350: (0.02710, 0.77800, 0.15300), 420: (0.00758, 0.65917, 0.12269),
          490: (0.01660, 0.68955, 0.07242), 555: (0.06053, 0.64204, 0.03996),
          700: (0.62438, 0.60000, 0.03000)}


def _quiet(function, *args, **kwargs):
    """Call with every ProvenanceWarning an error."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", jerlov.ProvenanceWarning)
        return function(*args, **kwargs)


def _warns(function, *args, **kwargs):
    with pytest.warns(jerlov.ProvenanceWarning) as caught:
        value = function(*args, **kwargs)
    return value, caught


# -- Morel & Maritorena (2001) ---------------------------------------------

@pytest.mark.parametrize("chl", [0.03, 0.1, 1.0, 10.0])
@pytest.mark.parametrize("wl", [420, 490, 555, 700])
def test_morel_is_kw_plus_chi_chl_to_the_e(chl, wl):
    kw, e, chi = TABLE2[wl]
    assert _quiet(jerlov.morel2001_kd, float(wl), chlorophyll_mg_m3=chl) \
        == pytest.approx(kw + chi * chl ** e, rel=1e-12)


def test_morel_at_one_mg_is_kw_plus_chi():
    """With [Chl] = 1, K_bio = chi (Figure 4 caption, p. 7167)."""
    kw, _, chi = TABLE2[490]
    assert _quiet(jerlov.morel2001_kd, 490.0, chlorophyll_mg_m3=1.0) \
        == pytest.approx(kw + chi)


def test_morel_interpolates_kd_between_the_table_wavelengths():
    k = [_quiet(jerlov.morel2001_kd, w, chlorophyll_mg_m3=0.2)
         for w in (490.0, 495.0)]
    mid = _quiet(jerlov.morel2001_kd, 492.0, chlorophyll_mg_m3=0.2)
    assert mid == pytest.approx(k[0] + 0.4 * (k[1] - k[0]))


def test_morel_keeps_the_shape_of_its_input():
    wl = np.array([[440.0, 450.0], [500.0, 550.0]])
    out = _quiet(jerlov.morel2001_kd, wl, chlorophyll_mg_m3=0.3)
    assert out.shape == (2, 2)
    assert isinstance(_quiet(jerlov.morel2001_kd, 450,
                             chlorophyll_mg_m3=0.3), float)
    assert _quiet(jerlov.morel2001_kd, np.array([]),
                  chlorophyll_mg_m3=0.3).shape == (0,)


def test_morel_warns_below_400_nm_where_the_values_were_extrapolated():
    value, caught = _warns(jerlov.morel2001_kd, 350.0, chlorophyll_mg_m3=0.1)
    kw, e, chi = TABLE2[350]
    assert value == pytest.approx(kw + chi * 0.1 ** e)
    assert "Morel & Antoine" in str(caught[0].message)
    # 398 nm rests on 395 and 400; 400 rests on 400 alone.
    _warns(jerlov.morel2001_kd, 398.0, chlorophyll_mg_m3=0.1)
    _quiet(jerlov.morel2001_kd, 400.0, chlorophyll_mg_m3=0.1)


@pytest.mark.parametrize("chl", [0.01, 40.0])
def test_morel_warns_outside_the_chlorophyll_of_its_data(chl):
    _, caught = _warns(jerlov.morel2001_kd, 490.0, chlorophyll_mg_m3=chl)
    assert "0.02-30" in str(caught[0].message)
    for inside in (0.02, 30.0):
        _quiet(jerlov.morel2001_kd, 490.0, chlorophyll_mg_m3=inside)


@pytest.mark.parametrize("wl", [349.0, 701.0, np.nan, np.inf])
def test_morel_refuses_wavelengths_outside_its_table(wl):
    with pytest.raises(ValueError):
        jerlov.morel2001_kd(wl, chlorophyll_mg_m3=0.1)


@pytest.mark.parametrize("chl", [0.0, -1.0, np.nan, np.inf, [0.1, 0.2],
                                 None])
def test_morel_needs_one_positive_chlorophyll(chl):
    with pytest.raises((ValueError, TypeError)):
        jerlov.morel2001_kd(490.0, chlorophyll_mg_m3=chl)


def test_morel_has_no_default_chlorophyll():
    with pytest.raises(TypeError):
        jerlov.morel2001_kd(490.0)  # type: ignore[call-arg]


# -- Lee et al. (2005) and (2013) ------------------------------------------

def _lee2005(a, bb, sun):
    return (1 + 0.005 * sun) * a + 4.18 * (1 - 0.52 * math.exp(-10.8 * a)) * bb


def _lee2013(a, bb, bbw, sun):
    return ((1 + 0.005 * sun) * a
            + (1 - 0.265 * bbw / bb) * 4.259
            * (1 - 0.52 * math.exp(-10.8 * a)) * bb)


@pytest.mark.parametrize("a,bb", [(0.05, 0.002), (0.2, 0.01), (1.0, 0.05)])
@pytest.mark.parametrize("sun", [10.0, 30.0, 60.0])
def test_lee2005_is_its_eq_11(a, bb, sun):
    assert _quiet(jerlov.lee2005_kd, a, bb, sun_zenith_deg=sun) \
        == pytest.approx(_lee2005(a, bb, sun), rel=1e-12)


@pytest.mark.parametrize("a,bb,bbw", [(0.03, 0.003, 0.0015),
                                      (0.2, 0.01, 0.001), (1.0, 0.05, 0.0)])
@pytest.mark.parametrize("sun", [5.0, 30.0, 60.0])
def test_lee2013_is_its_eq_5(a, bb, bbw, sun):
    assert _quiet(jerlov.lee2013_kd, a, bb, bb_water=bbw,
                  sun_zenith_deg=sun) \
        == pytest.approx(_lee2013(a, bb, bbw, sun), rel=1e-12)


def test_lee2013_without_water_is_lee2005_with_its_own_m1():
    a, bb, sun = 0.3, 0.02, 30.0
    k13 = _quiet(jerlov.lee2013_kd, a, bb, bb_water=0.0, sun_zenith_deg=sun)
    k05 = _quiet(jerlov.lee2005_kd, a, bb, sun_zenith_deg=sun)
    # The same form; only m1 changed, 4.18 to 4.259 (Table 1, p. 4243).
    assert (k13 - (1 + 0.005 * sun) * a) / (k05 - (1 + 0.005 * sun) * a) \
        == pytest.approx(4.259 / 4.18)


def test_lee_kd_broadcasts():
    a = np.array([0.05, 0.1, 0.5])
    out = _quiet(jerlov.lee2013_kd, a, 0.01, bb_water=0.002,
                 sun_zenith_deg=np.array([[10.0], [50.0]]))
    assert out.shape == (2, 3)
    assert out[1, 2] == pytest.approx(_lee2013(0.5, 0.01, 0.002, 50.0))
    assert isinstance(_quiet(jerlov.lee2005_kd, 0.1, 0.01,
                             sun_zenith_deg=30.0), float)


@pytest.mark.parametrize("function,kwargs,sun", [
    (jerlov.lee2005_kd, {}, 5.0), (jerlov.lee2005_kd, {}, 70.0),
    (jerlov.lee2013_kd, {"bb_water": 0.001}, 2.0),
    (jerlov.lee2013_kd, {"bb_water": 0.001}, 75.0)])
def test_lee_kd_warns_outside_the_fitted_sun(function, kwargs, sun):
    _, caught = _warns(function, 0.2, 0.01, sun_zenith_deg=sun, **kwargs)
    assert "zenith" in str(caught[0].message)


def test_lee_kd_warns_outside_the_stated_range_of_kd():
    # Clear water: 2005 is stated good from 0.05 1/m, 2013 from 0.02.
    _, caught = _warns(jerlov.lee2005_kd, 0.02, 0.002, sun_zenith_deg=30.0)
    assert "0.05 to 5.7" in str(caught[0].message)
    _quiet(jerlov.lee2013_kd, 0.02, 0.002, bb_water=0.001,
           sun_zenith_deg=30.0)
    _, caught = _warns(jerlov.lee2013_kd, 5.0, 0.5, bb_water=0.001,
                       sun_zenith_deg=30.0)
    assert "0.02 to 5" in str(caught[0].message)


@pytest.mark.parametrize("a,bb", [(0.0, 0.01), (0.1, 0.0), (-0.1, 0.01),
                                  (0.1, np.inf), (-np.inf, 0.01)])
def test_lee_kd_refuses_a_and_bb_that_are_not_positive(a, bb):
    with pytest.raises(ValueError):
        jerlov.lee2005_kd(a, bb, sun_zenith_deg=30.0)
    with pytest.raises(ValueError):
        jerlov.lee2013_kd(a, bb, bb_water=0.0, sun_zenith_deg=30.0)


@pytest.mark.parametrize("sun", [-1.0, 90.0, np.nan])
def test_lee_kd_refuses_a_sun_below_the_horizon(sun):
    with pytest.raises(ValueError):
        jerlov.lee2005_kd(0.1, 0.01, sun_zenith_deg=sun)


@pytest.mark.parametrize("bbw", [-0.001, 0.02, np.inf])
def test_lee2013_refuses_water_backscattering_outside_bb(bbw):
    with pytest.raises(ValueError):
        jerlov.lee2013_kd(0.1, 0.01, bb_water=bbw, sun_zenith_deg=30.0)


def test_lee_kd_has_no_defaults():
    with pytest.raises(TypeError):
        jerlov.lee2005_kd(0.1, 0.01)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        jerlov.lee2013_kd(0.1, 0.01,  # type: ignore[call-arg]
                          sun_zenith_deg=30.0)


# -- Rrs: Gordon et al. (1988), Lee et al. (2002) -------------------------

def test_the_coefficient_pairs_are_as_printed():
    assert jerlov.GORDON1988_RRS_COEFFICIENTS == (0.0949, 0.0794)
    assert jerlov.LEE2002_RRS_COEFFICIENTS == (0.0895, 0.1247)


@pytest.mark.parametrize("pair", [jerlov.GORDON1988_RRS_COEFFICIENTS,
                                  jerlov.LEE2002_RRS_COEFFICIENTS])
def test_subsurface_rrs_round_trips_through_lee2002_eq_3(pair):
    """Lee et al. (2002) eq. (3) recovers u from rrs; it must recover the
    u the forward relation was given."""
    g0, g1 = pair
    a = np.array([0.02, 0.1, 0.5, 2.0])
    bb = np.array([0.001, 0.005, 0.02, 0.1])
    rrs = jerlov.subsurface_rrs(a, bb, coefficients=pair)
    u = (-g0 + np.sqrt(g0 ** 2 + 4 * g1 * rrs)) / (2 * g1)
    np.testing.assert_allclose(u, bb / (a + bb), rtol=1e-12)


def test_above_surface_rrs_inverts_lee2002_eq_8():
    rrs = np.array([0.0, 0.001, 0.005, 0.02, 0.05])
    big = jerlov.above_surface_rrs(rrs)
    # Eq. (8) as printed, and as QAA v6 step 1 writes it.
    np.testing.assert_allclose(big / (0.52 + 1.7 * big), rrs, rtol=1e-12)
    assert isinstance(jerlov.above_surface_rrs(0.004), float)


@pytest.mark.parametrize("rrs", [-0.001, 1 / 1.7, np.inf])
def test_above_surface_rrs_refuses_impossible_values(rrs):
    with pytest.raises(ValueError):
        jerlov.above_surface_rrs(rrs)


@pytest.mark.parametrize("pair", [None, (0.09,), (0.09, 0.1, 0.1),
                                  (0.09, -0.1), (np.nan, 0.1)])
def test_subsurface_rrs_needs_a_pair_of_coefficients(pair):
    with pytest.raises((ValueError, TypeError)):
        jerlov.subsurface_rrs(0.1, 0.01, coefficients=pair)


def test_subsurface_rrs_has_no_default_coefficients():
    with pytest.raises(TypeError):
        jerlov.subsurface_rrs(0.1, 0.01)  # type: ignore[call-arg]


# -- Lee et al. (2015) ----------------------------------------------------

def test_the_disc_constant_is_the_papers_own_figures_cut_to_two_places():
    """0.14 in eq. (33): a disc of reflectance 0.85, as radiance
    0.85 / pi = 0.27, times t^2 / n^2 = 0.54 (p. 146). Those give 0.146,
    which rounds to 0.15; eq. (33) uses 0.14 (DATA.md section 27)."""
    product = 0.85 / math.pi * 0.54
    assert product == pytest.approx(0.146, abs=0.0005)
    assert 0.27 * 0.54 == pytest.approx(0.146, abs=0.0005)
    assert math.floor(product * 100) / 100 == 0.14


def test_secchi_is_eq_33_at_the_most_transparent_wavelength():
    wl = np.array([443.0, 490.0, 555.0, 665.0])
    kd = np.array([0.03, 0.025, 0.07, 0.45])
    rrs = np.array([0.008, 0.006, 0.002, 0.0002])
    expected = math.log(abs(0.14 - 0.006) / 0.013) / (2.5 * 0.025)
    assert _quiet(jerlov.lee2015_secchi_depth, wl, kd * 3, rrs) \
        == pytest.approx(expected / 3)


def test_secchi_warns_outside_the_depths_it_was_checked_against():
    wl, rrs = np.array([490.0]), np.array([0.006])
    _, caught = _warns(jerlov.lee2015_secchi_depth, wl, np.array([0.02]), rrs)
    assert "0.1 to 30" in str(caught[0].message)
    _warns(jerlov.lee2015_secchi_depth, wl, np.array([20.0]), rrs)


def test_secchi_refuses_a_reflectance_that_leaves_no_contrast():
    with pytest.raises(ValueError, match="contrast"):
        jerlov.lee2015_secchi_depth([490.0], [0.1], [0.13])


@pytest.mark.parametrize("wl,kd,rrs", [
    ([399.0], [0.1], [0.005]), ([701.0], [0.1], [0.005]),
    ([490.0], [0.0], [0.005]), ([490.0], [0.1], [-0.001]),
    ([490.0], [np.nan], [0.005]), ([490.0, 500.0], [0.1], [0.005]),
    ([], [], []), (490.0, 0.1, 0.005)])
def test_secchi_refuses_what_is_not_one_visible_spectrum(wl, kd, rrs):
    with pytest.raises(ValueError):
        jerlov.lee2015_secchi_depth(wl, kd, rrs)


@pytest.mark.parametrize("rrs,argument,depth", [(0.0, 1.044, 1.018),
                                                (0.01, 1.047, 1.020)])
def test_what_0_146_would_change_as_DATA_md_says(rrs, argument, depth):
    """DATA.md section 27: 0.146 for 0.14 makes the argument of the
    logarithm 4.4 to 4.7 percent larger and Z_SD 1.8 to 2.0 percent
    deeper, for Rrs_tr from 0 to 0.01."""
    p = 0.85 / math.pi * 0.54
    assert (p - rrs) / (0.14 - rrs) == pytest.approx(argument, abs=0.0006)
    assert (math.log((p - rrs) / 0.013) / math.log((0.14 - rrs) / 0.013)
            == pytest.approx(depth, abs=0.0006))


def test_nan_marks_a_gap_and_passes_through():
    a = np.array([0.1, np.nan, 0.3])
    bb = np.array([0.01, 0.01, np.nan])
    for out in (
            _quiet(jerlov.lee2005_kd, a, bb, sun_zenith_deg=30.0),
            _quiet(jerlov.lee2013_kd, a, bb, bb_water=0.001,
                   sun_zenith_deg=30.0),
            jerlov.subsurface_rrs(a, bb,
                                  coefficients=jerlov.LEE2002_RRS_COEFFICIENTS)):
        assert np.isfinite(out[0]) and np.isnan(out[1]) and np.isnan(out[2])
    assert np.isnan(jerlov.above_surface_rrs([0.003, np.nan])[1])
    # A gap does not hide a Kd outside the stated range.
    _warns(jerlov.lee2005_kd, np.array([0.02, np.nan]), 0.002,
           sun_zenith_deg=30.0)

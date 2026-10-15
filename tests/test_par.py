"""PAR down through the water column, and the depth of 1 percent."""

from __future__ import annotations

import warnings

import numpy as np
import pytest

import jerlov
from jerlov import _data

WL = np.arange(400.0, 701.0, 1.0)
FLAT = np.ones_like(WL)


@pytest.fixture(autouse=True)
def _quiet():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        yield


def test_an_energy_spectrum_is_counted_in_photons():
    """1 W m-2 nm-1 from 400 to 700 nm is about 4.6 umol of photons per J."""
    p = jerlov.par_profile(FLAT, WL, 0.0, kd=np.zeros_like(WL), unit="energy")
    expected = _data.trapezoid(WL * 1e-9 / (6.62607015e-34 * 299792458.0)
                               / 6.02214076e23 * 1e6, WL)
    assert p.surface_par == pytest.approx(expected, rel=1e-12)
    assert p.surface_par / 300.0 == pytest.approx(4.6, abs=0.02)


def test_a_photon_spectrum_is_integrated_as_it_is():
    p = jerlov.par_profile(FLAT, WL, 0.0, kd=np.zeros_like(WL), unit="photons")
    assert p.surface_par == pytest.approx(300.0)


def test_one_kd_at_every_wavelength_is_beer_lambert():
    kd = np.full_like(WL, 0.1)
    p = jerlov.par_profile(FLAT, WL, [0.0, 10.0, 20.0], kd=kd, unit="photons")
    assert p.fraction == pytest.approx(np.exp(-0.1 * np.array([0, 10, 20])))
    assert p.depth_of_fraction(0.01) == pytest.approx(np.log(100) / 0.1)


def test_par_is_not_attenuated_by_any_single_kd():
    """Red goes first, so PAR falls fast and then slowly: the 1 percent
    depth is not ln(100) / Kd at any one wavelength in particular."""
    w = jerlov.water("II", source="jerlov1976")
    p = jerlov.par_profile(FLAT, WL, [5.0, 10.0, 20.0], kd=w, unit="energy")
    effective = -np.log(p.fraction) / p.depths_m
    assert np.all(np.diff(effective) < 0)
    z1 = p.depth_of_fraction()
    assert jerlov.par_profile(FLAT, WL, z1, kd=w, unit="energy").fraction \
        == pytest.approx(0.01, rel=1e-6)


def test_clearer_water_lets_par_deeper():
    depths = [jerlov.par_profile(FLAT, WL, 0.0, unit="energy",
                                 kd=jerlov.water(t, source="jerlov1976")
                                 ).depth_of_fraction()
              for t in ("I", "IB", "II", "III", "3C", "9C")]
    assert depths == sorted(depths, reverse=True)


def test_a_descent_matches_its_own_transmittance():
    d = jerlov.descend("1C", 45.0, WL)
    p = jerlov.par_profile(FLAT, WL, 45.0, kd=d, unit="photons")
    assert p.par == pytest.approx(_data.trapezoid(d.transmittance, WL))
    # And part-way down, a shorter descent through the same layers.
    p = jerlov.par_profile(FLAT, WL, 27.0, kd=d, unit="photons")
    shorter = jerlov.descend("1C", 27.0, WL)
    assert p.par == pytest.approx(_data.trapezoid(shorter.transmittance, WL))


def test_a_descent_that_ends_too_soon_gives_no_depth():
    d = jerlov.descend("I", 50.0, WL)
    p = jerlov.par_profile(FLAT, WL, 0.0, kd=d, unit="energy")
    with pytest.raises(jerlov.MissingQuantityError, match="bottom of the descent"):
        p.depth_of_fraction(0.01)
    assert 0 < p.depth_of_fraction(0.5) < 50
    with pytest.raises(jerlov.MissingQuantityError, match="stops at 50 m"):
        jerlov.par_profile(FLAT, WL, 60.0, kd=d, unit="energy")


def test_the_band_ends_are_interpolated_not_widened():
    """Samples outside 400-700 nm count only through the ends."""
    wide = np.arange(390.0, 711.0, 20.0)       # no sample at 400 or 700
    p = jerlov.par_profile(np.ones_like(wide), wide, 0.0,
                           kd=np.zeros_like(wide), unit="photons")
    assert p.surface_par == pytest.approx(300.0)


def test_what_par_cannot_be_computed_from_is_refused():
    with pytest.raises(ValueError, match="unit must be one of"):
        jerlov.par_profile(FLAT, WL, 0.0, kd=FLAT, unit="W")
    with pytest.raises(TypeError):
        jerlov.par_profile(FLAT, WL, 0.0, kd=FLAT)   # unit has no default
    with pytest.raises(ValueError, match="PAR needs 400-700"):
        jerlov.par_profile(FLAT[:-10], WL[:-10], 0.0, kd=FLAT[:-10],
                           unit="photons")
    gap = FLAT.copy()
    gap[100] = np.nan
    with pytest.raises(jerlov.MissingQuantityError, match="gap"):
        jerlov.par_profile(gap, WL, 0.0, kd=FLAT, unit="photons")
    with pytest.raises(jerlov.MissingQuantityError, match="Kd has a gap"):
        jerlov.par_profile(FLAT, WL, 0.0, kd=gap, unit="photons")
    for bad in (-1.0, np.nan, np.inf):
        with pytest.raises(ValueError):
            jerlov.par_profile(FLAT, WL, bad, kd=FLAT, unit="photons")
    infinite = FLAT.copy()
    infinite[0] = np.inf
    with pytest.raises(ValueError, match="finite"):
        jerlov.par_profile(infinite, WL, 0.0, kd=FLAT, unit="photons")
    with pytest.raises(ValueError, match="finite"):
        jerlov.par_profile(FLAT, WL, 0.0, kd=infinite, unit="photons")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        dark = jerlov.par_profile(FLAT * 0, WL, [0.0, 1.0], kd=FLAT,
                                  unit="photons")
        assert np.all(np.isnan(dark.fraction))
    with pytest.raises(ValueError, match="other wavelengths"):
        jerlov.par_profile(FLAT, WL, 0.0, unit="photons",
                           kd=jerlov.descend("I", 20.0, WL[::2]))
    with pytest.raises(jerlov.MissingQuantityError):
        jerlov.par_profile(FLAT, WL, 0.0, kd=jerlov.water("II"), unit="photons")
    p = jerlov.par_profile(FLAT, WL, 0.0, kd=FLAT, unit="photons")
    for bad in (0.0, 1.0, np.nan):
        with pytest.raises(ValueError):
            p.depth_of_fraction(bad)


def test_the_profile_keeps_the_shape_of_the_depths_and_cannot_be_changed():
    depths = np.array([[0.0, 5.0], [10.0, 20.0]])
    p = jerlov.par_profile(FLAT, WL, depths, kd=np.full_like(WL, 0.1),
                           unit="photons")
    assert p.par.shape == (2, 2)
    with pytest.raises(ValueError):
        p.par[0, 0] = 1.0
    depths[0, 0] = 99.0
    assert p.depths_m[0, 0] == 0.0
    assert repr(p).startswith("<ParProfile surface 300 umol m-2 s-1, 4 depths")


def test_light_outside_the_band_neither_refuses_nor_warns():
    """A radiometer's 300-800 nm spectrum was refused because Jerlov (1976)
    stops at 715 nm, and Kd flagged at 705 nm warned, though PAR counts
    neither."""
    w = jerlov.water("II", source="jerlov1976")
    wide = np.arange(300.0, 801.0, 5.0)
    band = np.arange(400.0, 701.0, 5.0)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        p_wide = jerlov.par_profile(np.ones_like(wide), wide, [0.0, 10.0],
                                    kd=w, unit="energy")
        p_band = jerlov.par_profile(np.ones_like(band), band, [0.0, 10.0],
                                    kd=w, unit="energy")
        just_past = np.arange(380.0, 711.0, 5.0)
        jerlov.par_profile(np.ones_like(just_past), just_past, 10.0, kd=w,
                           unit="energy")
    assert p_wide.par == pytest.approx(p_band.par, rel=1e-12)
    # A gap outside the band does not matter either; one inside does.
    kd = np.full_like(wide, 0.1)
    kd[0] = np.nan
    assert jerlov.par_profile(FLAT, WL, 1.0, kd=np.full_like(WL, 0.1),
                              unit="photons").par == pytest.approx(
        jerlov.par_profile(np.ones_like(wide), wide, 1.0, kd=kd,
                           unit="photons").par)


# -- other bands -------------------------------------------------------------

WIDE = np.arange(300.0, 801.0, 5.0)


def test_the_default_band_is_par():
    assert jerlov.PAR_RANGE_NM == (400.0, 700.0)
    p = jerlov.par_profile(FLAT, WL, 0.0, kd=FLAT, unit="photons")
    q = jerlov.par_profile(FLAT, WL, 0.0, kd=FLAT, unit="photons",
                           band=(400, 700))
    assert p.band_nm == q.band_nm == (400.0, 700.0)
    assert p.par == q.par and repr(p) == repr(q)
    assert " over " not in repr(p)


def test_another_band_is_the_same_integral_over_it():
    """350-700 nm, Jerlov's quanta band, is the photon flux there,
    integrated by hand here; the band's ends are interpolated."""
    wl = np.arange(300.0, 711.0, 5.0)
    surface = np.interp(wl, *jerlov.d65())
    kd = jerlov.water("II", source="jerlov1976").kd(wl)
    p = jerlov.par_profile(surface, wl, [0.0, 10.0], kd=kd,
                           unit="photons", band=jerlov.QUANTA_BAND_NM)
    inside = (wl >= 350) & (wl <= 700)
    by_hand = [_data.trapezoid((surface * np.exp(-kd * z))[inside],
                               wl[inside]) for z in (0.0, 10.0)]
    assert p.par == pytest.approx(by_hand, rel=1e-12)
    assert p.band_nm == (350.0, 700.0)
    assert repr(p).startswith("<ParProfile surface") and \
        " over 350-700 nm, 2 depths" in repr(p)
    flat = jerlov.par_profile(np.ones_like(WIDE), WIDE, 0.0, unit="photons",
                              kd=np.zeros_like(WIDE), band=(402.5, 497.5))
    assert flat.surface_par == pytest.approx(95.0)
    narrow = jerlov.par_profile(FLAT, WL, [0.0, 10.0], unit="photons",
                                kd=np.full_like(WL, 0.1), band=(400.2, 400.7))
    assert narrow.surface_par == pytest.approx(0.5)
    assert narrow.fraction[1] == pytest.approx(np.exp(-1.0))


def test_the_colours_of_par_add_up_to_par():
    d = jerlov.descend("IA", 100.0, WL)
    surface = np.interp(WL, *jerlov.d65())
    whole = jerlov.par_profile(surface, WL, [0.0, 50.0, 100.0], kd=d,
                               unit="energy")
    parts = [jerlov.par_profile(surface, WL, [0.0, 50.0, 100.0], kd=d,
                                unit="energy", band=b).par
             for b in ((400, 500), (500, 600), (600, 700))]
    assert sum(parts) == pytest.approx(whole.par, rel=1e-12)


def test_only_the_band_needs_data():
    """Kd missing below 380 nm and above 520 nm, and a flagged one past
    them, do not matter to 400-500 nm."""
    kd = np.full_like(WIDE, 0.05)
    kd[(WIDE < 380) | (WIDE > 520)] = np.nan
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        p = jerlov.par_profile(np.ones_like(WIDE), WIDE, 10.0, kd=kd,
                               unit="photons", band=(400, 500))
    assert p.fraction == pytest.approx(np.exp(-0.5))
    with pytest.raises(jerlov.MissingQuantityError,
                       match="gap between 400 and 600 nm"):
        jerlov.par_profile(np.ones_like(WIDE), WIDE, 10.0, kd=kd,
                           unit="photons", band=(400, 600))
    with pytest.raises(ValueError, match="the band needs 350-700"):
        jerlov.par_profile(FLAT, WL, 0.0, kd=FLAT, unit="photons",
                           band=jerlov.QUANTA_BAND_NM)


def test_a_band_that_is_not_one_is_refused():
    for bad in ((700, 400), (400, 400), (0, 700), (-1, 700), (np.inf, 700),
                (400, np.nan), (400,), (400, 500, 600), "400-700", None,
                ((1, 2), (3, 4))):
        with pytest.raises(ValueError, match="band"):
            jerlov.par_profile(FLAT, WL, 0.0, kd=FLAT, unit="photons",
                               band=bad)


def test_the_band_given_is_not_changed():
    band = np.array([400.0, 500.0])
    p = jerlov.par_profile(FLAT, WL, 0.0, kd=FLAT, unit="photons",
                           band=band)
    band[0] = 450.0
    assert p.band_nm == (400.0, 500.0)


# -- the spectrum at depth, and Kd between two depths -------------------------


def test_the_spectrum_at_depth_integrates_to_par():
    d = jerlov.descend("IB", 100.0, WL)
    surface = np.interp(WL, *jerlov.d65())
    p = jerlov.par_profile(surface, WL, [0.0, 20.0, 60.0], kd=d,
                           unit="energy")
    for z, par in zip(p.depths_m, p.par):
        assert _data.trapezoid(p.spectrum_at(z), p.wavelengths_nm) == \
            pytest.approx(par, rel=1e-12)
    rows = p.spectrum_at([0.0, 20.0])
    assert rows.shape == (2, p.wavelengths_nm.size)
    assert np.allclose(rows[1], surface * WL * 1e-9 / (6.62607015e-34
                       * 299792458.0) / 6.02214076e23 * 1e6
                       * d.transmittance_at(20.0))
    with pytest.raises(ValueError):
        p.wavelengths_nm[0] = 0.0


def test_the_spectrum_is_on_the_band_with_its_ends():
    wide = np.arange(390.0, 711.0, 20.0)
    p = jerlov.par_profile(np.ones_like(wide), wide, 0.0, unit="photons",
                           kd=np.full_like(wide, 0.1), band=(400, 500))
    assert p.wavelengths_nm.tolist() == [400.0, 410.0, 430.0, 450.0, 470.0,
                                         490.0, 500.0]
    assert np.allclose(p.spectrum_at(10.0), np.exp(-1.0))


def test_kd_between_two_depths():
    """With one Kd at every wavelength, the effective Kd is that Kd; with a
    real spectrum it falls with depth as the red is removed."""
    flat = jerlov.par_profile(FLAT, WL, 0.0, kd=np.full_like(WL, 0.08),
                              unit="photons")
    assert flat.kd_par(0.0, 10.0) == pytest.approx(0.08, rel=1e-12)
    assert flat.kd_par(3.0, 3.5) == pytest.approx(0.08, rel=1e-12)
    p = jerlov.par_profile(np.interp(WL, *jerlov.d65()), WL, 0.0,
                           kd=jerlov.water("1C", source="jerlov1976"),
                           unit="energy")
    assert p.kd_par(0.0, 1.0) > p.kd_par(1.0, 5.0) > p.kd_par(5.0, 20.0)
    z1 = p.depth_of_fraction(0.01)
    assert p.kd_par(0.0, z1) == pytest.approx(np.log(100) / z1, rel=1e-9)


def test_depths_the_profile_cannot_answer_are_refused():
    p = jerlov.par_profile(FLAT, WL, 0.0, unit="photons",
                           kd=jerlov.descend("II", 50.0, WL))
    for bad in (-1.0, np.nan, np.inf):
        with pytest.raises(ValueError):
            p.spectrum_at(bad)
        with pytest.raises(ValueError):
            p.kd_par(0.0, bad)
    with pytest.raises(jerlov.MissingQuantityError, match="stops at 50 m"):
        p.spectrum_at(60.0)
    with pytest.raises(jerlov.MissingQuantityError, match="stops at 50 m"):
        p.kd_par(10.0, 60.0)
    for z1, z2 in ((10.0, 10.0), (20.0, 10.0)):
        with pytest.raises(ValueError, match="above"):
            p.kd_par(z1, z2)
    with pytest.raises(ValueError):
        p.spectrum_at(np.zeros((2, 2)))
    dark = jerlov.par_profile(FLAT * 0, WL, 0.0, kd=FLAT, unit="photons")
    with pytest.raises(ValueError, match="no light"):
        dark.kd_par(0.0, 1.0)


# -- a weight for each photon ------------------------------------------------


def test_a_photon_weight_weights_the_integral_and_nothing_else():
    d = jerlov.descend("II", 100.0, WL)
    surface = np.interp(WL, *jerlov.d65())
    weight = np.exp(-0.5 * ((WL - 480.0) / 40.0) ** 2)
    plain = jerlov.par_profile(surface, WL, [0.0, 30.0], kd=d, unit="energy")
    w = jerlov.par_profile(surface, WL, [0.0, 30.0], kd=d, unit="energy",
                           photon_weight=weight)
    for z, value in zip(w.depths_m, w.par):
        assert value == pytest.approx(_data.trapezoid(
            plain.spectrum_at(z) * weight, WL), rel=1e-12)
        assert np.array_equal(w.spectrum_at(z), plain.spectrum_at(z))
    assert w.weighted and not plain.weighted
    assert "weighted" in repr(w) and "weighted" not in repr(plain)
    # Its scale cancels from every fraction.
    w10 = jerlov.par_profile(surface, WL, 0.0, kd=d, unit="energy",
                             photon_weight=10 * weight)
    assert w10.depth_of_fraction(0.01) == pytest.approx(
        jerlov.par_profile(surface, WL, 0.0, kd=d, unit="energy",
                           photon_weight=weight).depth_of_fraction(0.01),
        rel=1e-9)


def test_a_weight_of_one_is_par():
    surface = np.interp(WL, *jerlov.d65())
    kd = jerlov.water("III", source="jerlov1976")
    p = jerlov.par_profile(surface, WL, [0.0, 10.0], kd=kd, unit="energy")
    q = jerlov.par_profile(surface, WL, [0.0, 10.0], kd=kd, unit="energy",
                           photon_weight=np.ones_like(WL))
    assert np.allclose(p.par, q.par, rtol=1e-12)
    assert p.kd_par(0.0, 10.0) == pytest.approx(q.kd_par(0.0, 10.0))


def test_a_blue_weight_goes_deeper_than_a_red_one_in_clear_water():
    surface = np.interp(WL, *jerlov.d65())
    d = jerlov.descend("I", 200.0, WL)
    blue, red = (np.exp(-0.5 * ((WL - peak) / 30.0) ** 2)
                 for peak in (470.0, 600.0))
    depth = {name: jerlov.par_profile(surface, WL, 0.0, kd=d, unit="energy",
                                      photon_weight=w).depth_of_fraction()
             for name, w in (("blue", blue), ("red", red))}
    assert depth["blue"] > 2 * depth["red"]


def test_a_weight_that_is_not_one_is_refused():
    for bad in (np.full_like(WL, -1.0), np.full_like(WL, np.inf),
                np.ones(WL.size + 1)):
        with pytest.raises(ValueError, match="photon_weight"):
            jerlov.par_profile(FLAT, WL, 0.0, kd=FLAT, unit="photons",
                               photon_weight=bad)
    gap = np.ones_like(WL)
    gap[50] = np.nan
    with pytest.raises(jerlov.MissingQuantityError, match="photon_weight"):
        jerlov.par_profile(FLAT, WL, 0.0, kd=FLAT, unit="photons",
                           photon_weight=gap)
    # Outside the band a gap does not matter.
    p = jerlov.par_profile(FLAT, WL, 1.0, kd=np.full_like(WL, 0.1),
                           unit="photons", band=(400, 500),
                           photon_weight=np.where(WL > 520, np.nan, 1.0))
    assert p.fraction == pytest.approx(np.exp(-0.1))
    zero = jerlov.par_profile(FLAT, WL, 0.0, kd=FLAT, unit="photons",
                              photon_weight=np.zeros_like(WL))
    with pytest.raises(ValueError, match="no PAR at the surface"):
        zero.depth_of_fraction()


def test_the_weight_given_is_not_changed():
    weight = np.ones_like(WL)
    p = jerlov.par_profile(FLAT, WL, 0.0, kd=FLAT, unit="photons",
                           photon_weight=weight)
    weight[:] = 0.0
    assert p.surface_par == pytest.approx(300.0)

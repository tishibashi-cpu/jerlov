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

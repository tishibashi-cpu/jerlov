"""Removing Raman scattering from Rrs, Lee et al. (2013) (DECISIONS.md
section 71)."""

from __future__ import annotations

import csv
import pathlib

import numpy as np
import pytest

import jerlov

TESTS_DATA = pathlib.Path(__file__).resolve().parent / "data"

# Lee et al. (2013) Table 2, p. 4245, as printed (signs from the page
# image): band nm, alpha, beta1, beta2.
TABLE2 = (
    (412, 0.003, 0.014, -0.022),
    (443, 0.004, 0.015, -0.023),
    (488, 0.011, 0.010, -0.051),
    (531, 0.015, 0.010, -0.070),
    (551, 0.017, 0.010, -0.080),
    (667, 0.018, 0.010, -0.081),
)
MODIS = np.array([412.0, 443.0, 488.0, 531.0, 551.0, 667.0])
BANDS = {"440": 443.0, "550": 551.0}
CLEAR = np.array([0.0080, 0.0070, 0.0050, 0.0025, 0.0018, 0.0002])


def _rf_by_hand(r440, r550):
    return np.array([a * r440 / r550 + b1 * r550 ** b2
                     for _, a, b1, b2 in TABLE2])


def test_at_the_six_bands_it_is_eq_11():
    out = jerlov.lee2013_raman_correction(MODIS, CLEAR, bands=BANDS)
    want = _rf_by_hand(CLEAR[1], CLEAR[4])
    assert np.allclose(out.raman_factor, want, rtol=1e-14, atol=0)
    assert np.allclose(out.rrs, CLEAR / (1 + want), rtol=1e-14, atol=0)
    assert np.array_equal(out.wavelengths, MODIS)


def test_between_bands_rf_is_interpolated_linearly():
    wl = np.array([443.0, 465.5, 500.0, 551.0, 600.0])
    r = np.array([0.007, 0.006, 0.004, 0.0018, 0.0006])
    out = jerlov.lee2013_raman_correction(wl, r, bands=BANDS)
    at_bands = _rf_by_hand(0.007, 0.0018)
    want = np.interp(wl, MODIS, at_bands)
    assert np.allclose(out.raman_factor, want, rtol=1e-14, atol=0)


def test_eq_13_inverts():
    out = jerlov.lee2013_raman_correction(MODIS, CLEAR, bands=BANDS)
    assert np.allclose(out.rrs * (1 + out.raman_factor), CLEAR,
                       rtol=1e-14, atol=0)


def test_several_spectra_at_once():
    many = np.stack([CLEAR, CLEAR * 2, CLEAR * 0.5])
    out = jerlov.lee2013_raman_correction(MODIS, many, bands=BANDS)
    assert out.raman_factor.shape == (3, 6)
    for i, row in enumerate(many):
        one = jerlov.lee2013_raman_correction(MODIS, row, bands=BANDS)
        assert np.array_equal(out.raman_factor[i], one.raman_factor)


def test_nan_passes_through():
    r = CLEAR.copy()
    r[2] = np.nan
    out = jerlov.lee2013_raman_correction(MODIS, r, bands=BANDS)
    assert np.isnan(out.rrs[2]) and np.all(np.isfinite(out.rrs[[0, 1, 3]]))
    r[1] = np.nan                  # the "440" band: every RF is NaN
    out = jerlov.lee2013_raman_correction(MODIS, r, bands=BANDS)
    assert np.all(np.isnan(out.raman_factor))


def test_the_input_is_not_modified():
    r = CLEAR.copy()
    jerlov.lee2013_raman_correction(MODIS, r, bands=BANDS)
    assert np.array_equal(r, CLEAR)


def test_plausible_on_the_ioccg_synthetic_data():
    """Not a validation: these spectra exclude inelastic scattering
    (Report 5, p. 17), so they are Rrs, not Rrs_T. RF stays below the
    paper's "generally less than 0.20" (p. 4244) and rises from 440 to 560
    nm (DECISIONS.md section 71)."""
    with open(TESTS_DATA / "ioccg2006_sun30.csv", encoding="utf-8",
              newline="") as f:
        rows = list(csv.DictReader(f))
    wl = np.array([440.0, 490.0, 510.0, 550.0, 560.0])
    r = np.array([[float(row[f"Rrs_{int(w)}"]) for w in wl] for row in rows])
    out = jerlov.lee2013_raman_correction(
        wl, r, bands={"440": 440.0, "550": 550.0})
    assert out.raman_factor.shape == (500, 5)
    assert np.all(out.raman_factor < 0.20)
    assert round(float(out.raman_factor.max()), 3) == 0.135
    assert np.all(np.diff(np.median(out.raman_factor, axis=0)) >= 0)


@pytest.mark.parametrize("wl", [[411.0, 443.0, 551.0],
                                [443.0, 551.0, 668.0],
                                [400.0, 443.0, 551.0, 700.0]])
def test_no_extrapolation(wl):
    with pytest.raises(ValueError, match="does not extrapolate"):
        jerlov.lee2013_raman_correction(
            np.array(wl), np.full(len(wl), 0.002), bands=BANDS)


def test_refusals():
    call = jerlov.lee2013_raman_correction
    for bad in (np.inf, -0.001):
        r = CLEAR.copy()
        r[3] = bad
        with pytest.raises(ValueError, match="negative or infinite"):
            call(MODIS, r, bands=BANDS)
    r = CLEAR.copy()
    r[4] = 0.0
    with pytest.raises(ValueError, match="'550' band must be positive"):
        call(MODIS, r, bands=BANDS)
    with pytest.raises(ValueError, match="not one of wavelengths"):
        call(MODIS, CLEAR, bands={"440": 440.0, "550": 551.0})
    for bands in ({"440": 443.0}, {"440": 443.0, "550": 551.0, "x": 1.0},
                  [443.0, 551.0]):
        with pytest.raises(ValueError, match="bands must name"):
            call(MODIS, CLEAR, bands=bands)
    with pytest.raises(ValueError, match="one value for each wavelength"):
        call(MODIS, CLEAR[:5], bands=BANDS)
    with pytest.raises(ValueError, match="ascending"):
        call(MODIS[::-1], CLEAR, bands=BANDS)
    with pytest.raises(ValueError, match="ascending"):
        call(np.array([]), np.array([]), bands=BANDS)
    with pytest.raises(TypeError):
        call(MODIS, CLEAR)          # no default bands

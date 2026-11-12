"""Chlorophyll to aph and bbp for case 1 water (DECISIONS.md section 72).

Bricaud et al. (1995) Table 2 is transcribed in tools/build_bricaud1995.py,
which checks it against the paper's text before writing.
"""

from __future__ import annotations

import csv
import io
import warnings
from importlib.resources import files

import numpy as np
import pytest

import jerlov
from jerlov import ProvenanceWarning


def _table():
    text = files("jerlov.data").joinpath("bricaud1995_aph.csv").read_text(
        encoding="utf-8")
    return list(csv.DictReader(io.StringIO(text)))


# -- bricaud1995_aph ------------------------------------------------------

def test_the_table_is_complete():
    rows = _table()
    wl = sorted(int(r["wavelength_nm"]) for r in rows)
    assert wl == sorted(list(range(400, 701, 2)) + [675])


@pytest.mark.parametrize("chl", [0.02, 0.1, 1.0, 25.0])
def test_aph_at_the_printed_wavelengths(chl):
    rows = _table()
    wl = np.array([float(r["wavelength_nm"]) for r in rows])
    want = np.array([float(r["A_m2_per_mg"])
                     * chl ** (1 - float(r["B_exponent"])) for r in rows])
    got = jerlov.bricaud1995_aph(wl, chlorophyll_mg_m3=chl)
    assert np.allclose(got, want, rtol=1e-14, atol=0)


def test_aph_at_440_is_the_text_equation():
    """a*ph(440) = 0.0403 [Chl]^-0.332, twice in the text."""
    for chl in (0.05, 0.5, 5.0):
        got = jerlov.bricaud1995_aph(440.0, chlorophyll_mg_m3=chl)
        assert isinstance(got, float)
        assert got == pytest.approx(chl * 0.0403 * chl ** -0.332, rel=1e-14)


def test_aph_between_rows_is_linear():
    chl = 0.3
    a, b = jerlov.bricaud1995_aph([674.0, 675.0], chlorophyll_mg_m3=chl)
    mid = jerlov.bricaud1995_aph(674.5, chlorophyll_mg_m3=chl)
    assert mid == pytest.approx((a + b) / 2, rel=1e-14)


def test_aph_package_effect():
    """a*ph(440) falls by about ten times from 0.02 to 25 mg m-3 (the
    text, p. 13,330: 'by about a factor of 10')."""
    low = jerlov.bricaud1995_aph(440.0, chlorophyll_mg_m3=0.02) / 0.02
    high = jerlov.bricaud1995_aph(440.0, chlorophyll_mg_m3=25.0) / 25.0
    assert 9.0 < low / high < 11.0


def test_aph_refusals_and_warnings():
    f = jerlov.bricaud1995_aph
    for outside in (399.0, 701.0, np.nan, np.inf):
        with pytest.raises(ValueError):
            f(outside, chlorophyll_mg_m3=1.0)
    for bad in (0.0, -1.0, np.nan, np.inf, [0.1, 1.0]):
        with pytest.raises(ValueError, match="chlorophyll"):
            f(440.0, chlorophyll_mg_m3=bad)
    for outside in (0.01, 30.0):
        with pytest.warns(ProvenanceWarning, match="0.02-25"):
            f(440.0, chlorophyll_mg_m3=outside)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ProvenanceWarning)
        f([400.0, 700.0], chlorophyll_mg_m3=0.02)
        f([400.0, 700.0], chlorophyll_mg_m3=25.0)
    with pytest.raises(TypeError):
        f(440.0)
    assert f([], chlorophyll_mg_m3=1.0).shape == (0,)


# -- morel2001_bbp --------------------------------------------------------

def _bbp_by_hand(wl, chl):
    v = 0.5 * (np.log10(chl) - 0.3) if chl < 2 else 0.0
    return ((0.002 + 0.01 * (0.50 - 0.25 * np.log10(chl))
             * (np.asarray(wl) / 550.0) ** v) * 0.30 * chl ** 0.62)


@pytest.mark.parametrize("chl", [0.02, 0.1, 1.0, 2.0, 10.0, 30.0])
def test_bbp_is_eqs_13_14_9(chl):
    wl = np.array([350.0, 412.0, 550.0, 700.0])
    got = jerlov.morel2001_bbp(wl, chlorophyll_mg_m3=chl)
    assert np.allclose(got, _bbp_by_hand(wl, chl), rtol=1e-14, atol=0)


def test_the_exponent_as_the_text_describes():
    """'lambda^-1 at 0.02' and 'neutral at 2 mg m-3' (p. 7171): v is
    -0.9995 and +0.0005 there by eq. (14)."""
    for chl, v in ((0.02, -0.9995), (2.0 - 1e-9, 0.0005)):
        assert 0.5 * (np.log10(chl) - 0.3) == pytest.approx(v, abs=5e-5)
    flat = jerlov.morel2001_bbp([400.0, 700.0], chlorophyll_mg_m3=5.0)
    assert flat[0] == flat[1]
    steep = jerlov.morel2001_bbp([400.0, 550.0], chlorophyll_mg_m3=0.02)
    assert steep[0] > steep[1]


def test_not_eq_10():
    """Eq. (10), the 1988 form, would give a larger bbp: 0.02 against
    0.01 in the varying term."""
    chl, wl = 0.1, 550.0
    eq10 = (0.002 + 0.02 * (0.50 - 0.25 * np.log10(chl))) * 0.30 * chl ** 0.62
    assert jerlov.morel2001_bbp(wl, chlorophyll_mg_m3=chl) < eq10


def test_bbp_refusals_and_warnings():
    f = jerlov.morel2001_bbp
    for outside in (349.0, 701.0, np.nan, np.inf):
        with pytest.raises(ValueError):
            f(outside, chlorophyll_mg_m3=1.0)
    with pytest.raises(ValueError, match="negative"):
        f(550.0, chlorophyll_mg_m3=101.0)
    for bad in (0.0, -1.0, np.nan, [0.1, 1.0]):
        with pytest.raises(ValueError, match="chlorophyll"):
            f(550.0, chlorophyll_mg_m3=bad)
    for outside in (0.01, 50.0, 100.0):
        with pytest.warns(ProvenanceWarning, match="0.02-30"):
            f(550.0, chlorophyll_mg_m3=outside)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ProvenanceWarning)
        f([350.0, 700.0], chlorophyll_mg_m3=0.02)
        f([350.0, 700.0], chlorophyll_mg_m3=30.0)
    assert isinstance(f(550.0, chlorophyll_mg_m3=1.0), float)
    assert f(np.array([[400.0, 500.0]]), chlorophyll_mg_m3=1.0).shape == (1, 2)

"""Published pure water absorption spectra (DECISIONS.md section 70).

The tables are transcribed in tools/build_pure_water_aw.py, which checks
them against the papers' own statements before writing.
"""

from __future__ import annotations

import csv
import io
import pathlib
import warnings
from importlib.resources import files

import numpy as np
import pytest

import jerlov
from jerlov import ProvenanceWarning

TESTS_DATA = pathlib.Path(__file__).resolve().parent / "data"
KEYS = ("pope1997", "smith1981", "mason2016", "lee2015", "lee2015_smoothed")
FILES = {"pope1997": "pope1997_aw.csv", "smith1981": "smith1981_aw.csv",
         "mason2016": "mason2016_aw.csv", "lee2015": "lee2015_aw.csv",
         "lee2015_smoothed": "lee2015_aw.csv"}
RANGES = {"pope1997": (380.0, 727.5), "smith1981": (200.0, 800.0),
          "mason2016": (250.0, 550.0), "lee2015": (350.0, 550.0),
          "lee2015_smoothed": (350.0, 550.0)}


def _table(name):
    text = files("jerlov.data").joinpath(name).read_text(encoding="utf-8")
    return list(csv.DictReader(io.StringIO(text)))


def _quiet(call):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ProvenanceWarning)
        return call()


@pytest.mark.parametrize("key", KEYS)
def test_the_printed_wavelengths_return_the_printed_values(key):
    rows = _table(FILES[key])
    wl = np.array([float(r["wavelength_nm"]) for r in rows])
    want = np.array([float(r["smoothed_aw_per_m"] or r["aw_per_m"])
                     if key == "lee2015_smoothed" else float(r["aw_per_m"])
                     for r in rows])
    got = _quiet(lambda: jerlov.pure_water_absorption_table(wl, source=key))
    assert np.array_equal(got, want)
    assert (wl[0], wl[-1]) == RANGES[key]


def test_the_row_counts_and_spacing():
    assert len(_table("pope1997_aw.csv")) == 140
    assert len(_table("smith1981_aw.csv")) == 61
    assert len(_table("mason2016_aw.csv")) == 131
    assert len(_table("lee2015_aw.csv")) == 41


def test_between_printed_wavelengths_is_linear():
    got = jerlov.pure_water_absorption_table(401.25, source="pope1997")
    assert got == pytest.approx((0.00663 + 0.00579) / 2, rel=1e-12)
    got = jerlov.pure_water_absorption_table(295.0, source="mason2016")
    assert got == pytest.approx((9.39e-3 + 4.67e-3) / 2, rel=1e-12)


def test_scalars_arrays_and_empty():
    one = jerlov.pure_water_absorption_table(440.0, source="pope1997")
    assert isinstance(one, float) and one == 0.00635
    many = jerlov.pure_water_absorption_table([440.0, 500.0],
                                              source="pope1997")
    assert isinstance(many, np.ndarray) and list(many) == [0.00635, 0.0204]
    assert jerlov.pure_water_absorption_table(
        [], source="pope1997").shape == (0,)


def test_the_IOCCG_synthetic_data_used_pope_and_fry():
    """Report 5 (p. 15) attributes its aw to Pope & Fry; at its 31
    wavelengths, 400-700 nm, they are the same numbers."""
    with open(TESTS_DATA / "ioccg2006_pure_water.csv", encoding="utf-8",
              newline="") as f:
        rows = list(csv.DictReader(f))
    wl = np.array([float(r["wavelength_nm"]) for r in rows])
    ioccg = np.array([float(r["aw_per_m"]) for r in rows])
    assert (wl[0], wl[-1], len(wl)) == (400.0, 700.0, 31)
    pf = jerlov.pure_water_absorption_table(wl, source="pope1997")
    assert np.allclose(pf, ioccg, rtol=1e-12, atol=0)


def test_mason_is_in_per_metre():
    """Table 2 prints 1e-3 1/m; the minimum is 0.000811 at 344 nm
    (abstract), printed 0.81."""
    assert jerlov.pure_water_absorption_table(
        344.0, source="mason2016") == 0.00081


def test_the_smoothed_key_differs_only_where_the_paper_smoothed():
    wl = np.arange(350.0, 551.0, 5.0)
    raw = jerlov.pure_water_absorption_table(wl, source="lee2015")
    smooth = jerlov.pure_water_absorption_table(wl, source="lee2015_smoothed")
    differ = wl[raw != smooth]
    assert list(differ) == [360.0, 370.0, 385.0, 395.0, 400.0]


def test_smith_and_baker_at_710_nm_warns():
    with pytest.warns(ProvenanceWarning, match="710 nm"):
        jerlov.pure_water_absorption_table(710.0, source="smith1981")
    with pytest.warns(ProvenanceWarning, match="Eq. \\(6\\)"):
        jerlov.pure_water_absorption_table(705.0, source="smith1981")
    with warnings.catch_warnings():
        warnings.simplefilter("error", ProvenanceWarning)
        jerlov.pure_water_absorption_table([700.0, 720.0], source="smith1981")


@pytest.mark.parametrize("key", KEYS)
def test_no_other_value_warns(key):
    lo, hi = RANGES[key]
    wl = np.linspace(lo, hi, 997)
    if key == "smith1981":
        wl = wl[np.abs(wl - 710.0) >= 10.0]
    with warnings.catch_warnings():
        warnings.simplefilter("error", ProvenanceWarning)
        jerlov.pure_water_absorption_table(wl, source=key)


@pytest.mark.parametrize("key", KEYS)
def test_no_extrapolation(key):
    lo, hi = RANGES[key]
    for outside in (lo - 0.1, hi + 0.1, np.inf, -np.inf):
        with pytest.raises(ValueError, match="does not extrapolate"):
            jerlov.pure_water_absorption_table(outside, source=key)


def test_refusals():
    with pytest.raises(ValueError, match="NaN"):
        jerlov.pure_water_absorption_table(np.nan, source="pope1997")
    with pytest.raises(KeyError, match="pope1997, smith1981"):
        jerlov.pure_water_absorption_table(440.0, source="williamson2022")
    with pytest.raises(TypeError):
        jerlov.pure_water_absorption_table(440.0)  # no default source


def test_the_input_is_not_modified():
    wl = np.array([440.0, 500.0])
    jerlov.pure_water_absorption_table(wl, source="pope1997")
    assert list(wl) == [440.0, 500.0]


def test_it_feeds_qaa():
    """The use the section was written for: a pure_water QAA accepts."""
    wl = np.array([410.0, 440.0, 490.0, 510.0, 555.0, 640.0, 670.0])
    aw = jerlov.pure_water_absorption_table(wl, source="pope1997")
    bbw = jerlov.pure_water_backscattering(wl, salinity_psu=35.0)
    rrs = np.array([0.008, 0.007, 0.005, 0.004, 0.002, 0.0003, 0.0002])
    out = jerlov.qaa_ioccg2006(
        wl, rrs,
        bands={"410": 410.0, "440": 440.0, "490": 490.0, "510": 510.0,
               "555": 555.0, "670": 670.0},
        pure_water=(wl, aw, bbw))
    assert np.all(np.isfinite(out.a))

"""The uncertainties printed with the published pure water absorption
spectra: DECISIONS.md section 125, DATA.md section 29."""

from __future__ import annotations

import csv
import io
import math
import warnings
from importlib.resources import files

import numpy as np
import pytest

import jerlov

COLUMNS = {"pope1997": ("pope1997_aw.csv", "aw_per_m", "sigma_per_m"),
           "mason2016": ("mason2016_aw.csv", "aw_per_m", "sigma_per_m"),
           "lee2015": ("lee2015_aw.csv", "aw_per_m", "delta_aw_per_m")}


def _rows(name):
    text = files("jerlov.data").joinpath(name).read_text()
    return list(csv.DictReader(io.StringIO(text)))


def _quiet(wl, source):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        return jerlov.pure_water_absorption_uncertainty(wl, source=source)


@pytest.mark.parametrize("source", sorted(COLUMNS))
def test_every_printed_value_is_returned_as_printed(source):
    name, aw_col, u_col = COLUMNS[source]
    rows = _rows(name)
    wl = np.array([float(r["wavelength_nm"]) for r in rows])
    r = _quiet(wl, source)
    assert np.array_equal(r.wavelengths_nm, wl)
    assert np.array_equal(r.uncertainty, [float(x[u_col]) for x in rows])
    assert np.array_equal(r.aw, [float(x[aw_col]) for x in rows])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        assert np.array_equal(
            r.aw, jerlov.pure_water_absorption_table(wl, source=source))
    assert r.source == source and r.meaning


def test_pope_and_fry_s_percent_is_printed_and_follows_from_sigma():
    """p. 8719: sigma and a 2 percent calibration error in quadrature,
    rounded up, within the rounding of the printed aw and sigma."""
    rows = _rows("pope1997_aw.csv")
    wl = np.array([float(r["wavelength_nm"]) for r in rows])
    r = _quiet(wl, "pope1997")
    assert np.array_equal(r.percent_error, [float(x["percent_error"])
                                            for x in rows])

    def half(text):
        return 0.5 * 10.0 ** -len(text.split(".")[1])

    for x, pct in zip(rows, r.percent_error):
        a, s = x["aw_per_m"], x["sigma_per_m"]
        low = 100 * math.hypot((float(s) - half(s)) / (float(a) + half(a)),
                               0.02)
        high = 100 * math.hypot((float(s) + half(s)) / (float(a) - half(a)),
                                0.02)
        assert math.ceil(low - 1e-9) <= pct <= math.ceil(high - 1e-9), x
    assert _quiet(450.0, "mason2016").percent_error is None
    assert _quiet(450.0, "lee2015").percent_error is None


def test_a_scalar_gives_floats_and_arrays_keep_their_shape():
    r = _quiet(440.0, "pope1997")
    assert isinstance(r.uncertainty, float) and isinstance(r.aw, float)
    grid = _quiet(np.array([[440.0, 442.5], [445.0, 447.5]]), "pope1997")
    assert grid.uncertainty.shape == (2, 2)
    assert grid.uncertainty[1, 0] == _quiet(445.0, "pope1997").uncertainty


@pytest.mark.parametrize("source", ["smith1981", "morel2007", "morel2007_aw2"])
def test_sources_that_print_none_are_refused(source):
    with pytest.raises(jerlov.MissingQuantityError, match="prints no"):
        jerlov.pure_water_absorption_uncertainty(400.0, source=source)


def test_only_printed_wavelengths_are_accepted():
    with pytest.raises(ValueError, match="380 and 382.5 nm"):
        jerlov.pure_water_absorption_uncertainty(381.0, source="pope1997")
    with pytest.raises(ValueError, match="does not extrapolate"):
        jerlov.pure_water_absorption_uncertainty(560.0, source="mason2016")
    with pytest.raises(ValueError):
        jerlov.pure_water_absorption_uncertainty(float("nan"),
                                                 source="lee2015")
    with pytest.raises(KeyError):
        jerlov.pure_water_absorption_uncertainty(400.0, source="nobody")


def test_lee_smoothed_warns_at_exactly_its_five_wavelengths():
    rows = _rows("lee2015_aw.csv")
    smoothed = [float(r["wavelength_nm"]) for r in rows
                if r["smoothed_aw_per_m"].strip()]
    assert smoothed == [360.0, 370.0, 385.0, 395.0, 400.0]
    for r in rows:
        w = float(r["wavelength_nm"])
        with warnings.catch_warnings(record=True) as record:
            warnings.simplefilter("always", jerlov.ProvenanceWarning)
            out = jerlov.pure_water_absorption_uncertainty(
                w, source="lee2015_smoothed")
        said = [x for x in record if "not given for it" in str(x.message)]
        assert bool(said) == (w in smoothed), w
        assert out.uncertainty == float(r["delta_aw_per_m"])
        if w in smoothed:
            assert out.aw == float(r["smoothed_aw_per_m"])
    with warnings.catch_warnings():
        warnings.simplefilter("error", jerlov.ProvenanceWarning)
        jerlov.pure_water_absorption_uncertainty(360.0, source="lee2015")


def test_the_meanings_say_what_each_column_is():
    assert "standard deviation" in _quiet(400.0, "pope1997").meaning
    assert "sigma" in _quiet(400.0, "mason2016").meaning
    assert "not a measured spread" in _quiet(400.0, "lee2015").meaning


def test_the_caller_s_array_is_not_modified():
    wl = np.array([400.0, 405.0])
    before = wl.copy()
    _quiet(wl, "lee2015")
    assert np.array_equal(wl, before)


def test_the_table_function_is_unchanged():
    assert jerlov.pure_water_absorption_table(380.0, source="pope1997") \
        == 0.01137
    assert jerlov.pure_water_absorption_table(381.25, source="pope1997") \
        == pytest.approx(0.5 * (0.01137 + 0.01044))

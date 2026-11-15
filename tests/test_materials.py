"""Measured reflectances of ten materials, the USGS Spectral Library
(DECISIONS.md section 85, DATA.md section 37)."""

from __future__ import annotations

import csv
import io
import warnings
from importlib.resources import files

import numpy as np
import pytest

import jerlov


def _table():
    text = files("jerlov.data").joinpath(
        "usgs2017_reflectance.csv").read_text()
    return list(csv.DictReader(io.StringIO(text)))


def test_the_ten_materials():
    assert jerlov.USGS2017_MATERIALS == (
        "white_pvc", "black_abs", "grey_concrete", "red_nylon",
        "orange_cadmium", "yellow_cadmium", "green_tarp", "blue_green_hdpe",
        "blue_nylon", "violet_cobalt")


@pytest.mark.parametrize("material", jerlov.USGS2017_MATERIALS)
def test_each_is_the_table_as_shipped(material):
    m = jerlov.usgs2017_reflectance(material)
    rows = [r for r in _table() if r["material"] == material]
    np.testing.assert_array_equal(m.wavelengths, np.arange(350.0, 831.0))
    np.testing.assert_array_equal(
        m.reflectance, [float(r["reflectance"]) for r in rows])
    assert all(r["status"] == "ok" for r in rows)
    assert np.all((m.reflectance > 0) & (m.reflectance < 1))
    assert m.material == material and "10.5066/F7RR1WDJ" in m.citation
    with pytest.raises(ValueError):
        m.reflectance[0] = 0.5
    assert m == jerlov.usgs2017_reflectance(material)


def test_the_records_are_the_librarys():
    """Record numbers and names as the ASCII files print them."""
    m = jerlov.usgs2017_reflectance("violet_cobalt")
    assert (m.record, m.sample) == (18485, "Cobalt_violet GDS803")
    m = jerlov.usgs2017_reflectance("white_pvc")
    assert (m.record, m.sample) == (19775, "Plastic_PVC GDS338 White")


def test_neutral_and_coloured_materials_are_what_their_names_say():
    """Under D65 the three neutral samples come out nearly grey and the
    coloured ones in the hue their name gives (sRGB, balanced on D65)."""
    wl = np.arange(360.0, 781.0)
    d65 = np.interp(wl, *jerlov.d65())

    def srgb(key):
        m = jerlov.usgs2017_reflectance(key)
        with warnings.catch_warnings():
            # The cadmium pigments lie outside sRGB; clipping is enough to
            # tell which channel is largest.
            warnings.simplefilter("ignore", jerlov.GamutWarning)
            return jerlov.spectrum_to_srgb(
                d65 * np.interp(wl, m.wavelengths, m.reflectance), wl,
                white=d65, clip=True)

    neutral = ("white_pvc", "black_abs", "grey_concrete")
    spread = {k: float(np.ptp(srgb(k))) for k in jerlov.USGS2017_MATERIALS}
    assert max(spread[k] for k in neutral) < min(
        v for k, v in spread.items() if k not in neutral), spread
    assert np.argmax(srgb("red_nylon")) == 0
    assert np.argmax(srgb("green_tarp")) == 1
    assert np.argmax(srgb("blue_nylon")) == 2


def test_an_unknown_material_is_refused():
    with pytest.raises(KeyError, match="unknown material"):
        jerlov.usgs2017_reflectance("ColorChecker red")

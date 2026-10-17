"""Tyler's measured radiance distribution, read back as printed.

The tables are transcribed in tools/build_tyler1958.py, which also checks
them against each other; DATA.md section 23.
"""

from __future__ import annotations

import math
import warnings

import numpy as np
import pytest

import jerlov


def _table(depth):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        return jerlov.tyler1958_radiance(depth)


def test_the_tables_are_read_back_as_printed():
    shallow = _table(4.24)
    assert shallow.tilt_deg.tolist() == list(range(0, 181, 10))
    assert shallow.azimuth_deg.tolist() == list(range(0, 181, 20))
    assert shallow.radiance[3, 0] == 7_980_000          # the sun, tilt 30
    assert shallow.radiance[2, 1] == 1_320_000
    deep = _table(66.1)
    assert deep.radiance[0, 0] == 28.8 and deep.radiance[-1, -1] == 0.0975
    assert _table(41.3).radiance[3, 2] == 1049           # printed so
    assert _table(10.4).radiance[11, 4] == 2880          # text layer: 2,380
    for array in (deep.radiance, deep.tilt_deg, deep.azimuth_deg):
        with pytest.raises(ValueError):
            array[0] = 0.0


def test_straight_up_and_down_have_one_value_and_the_sun_side_is_brighter():
    for depth in jerlov.TYLER1958_DEPTHS:
        r = _table(depth).radiance
        assert np.ptp(r[0]) == 0 and np.ptp(r[-1]) == 0
        assert np.all(np.diff(r, axis=1) <= 0)


def test_the_suspect_cells_warn_and_the_deep_tables_do_not():
    for depth, count in ((4.24, 3), (10.4, 2), (16.6, 2), (29.0, 2)):
        with pytest.warns(jerlov.ProvenanceWarning, match="DATA.md section 23"):
            table = jerlov.tyler1958_radiance(depth)
        assert len(table.suspect) == count
        assert any("factor of 2" in s for s in table.suspect)
    assert any("overstruck" in s for s in _table(4.24).suspect)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        for depth in (41.3, 53.7, 66.1):
            assert jerlov.tyler1958_radiance(depth).suspect == ()


def test_what_the_report_says_about_the_conditions():
    t = _table(41.3)
    assert t.sun_altitude_deg == 56.6
    assert t.band_nm == (430.0, 546.0)
    assert round(t.beam_attenuation, 3) == 0.396
    assert math.isclose(math.exp(-t.beam_attenuation), 0.673)
    assert repr(t) == ("<RadianceDistribution Tyler 1958, 41.3 m, "
                       "19 tilts x 10 azimuths>")


def test_an_unknown_depth_names_the_known_ones():
    with pytest.raises(KeyError, match="known: 4.24, 10.4, 16.6, 29, 41.3"):
        jerlov.tyler1958_radiance(20.0)

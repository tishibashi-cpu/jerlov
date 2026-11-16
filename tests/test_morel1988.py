"""Morel's (1988) Kd: DECISIONS.md section 101, DATA.md section 45."""

import warnings

import numpy as np
import pytest

import jerlov
from jerlov import _data


def test_table_2_rows_quoted():
    wl, kw, chi, e = _data.morel1988()
    assert len(wl) == 61 and wl[0] == 400 and wl[-1] == 700
    rows = {int(w): (k, c, x) for w, k, c, x in zip(wl, kw, chi, e)}
    assert rows[400] == (0.0209, 0.1100, 0.668)
    assert rows[450] == (0.0168, 0.0971, 0.701)    # Fig. 7a's 0.0168
    assert rows[555] == (0.0683, 0.0400, 0.645)
    assert rows[700] == (0.6500, 0.0300, 0.600)


def test_eq_9_by_hand():
    # 440 nm, C = 0.3: 0.0168 + 0.1041 * 0.3^0.707.
    assert jerlov.morel1988_kd(440.0, pigment_mg_m3=0.3) == pytest.approx(
        0.0168 + 0.1041 * 0.3 ** 0.707, rel=1e-12)
    # Between the 5 nm points, K is interpolated linearly.
    k = jerlov.morel1988_kd([440.0, 445.0, 442.0], pigment_mg_m3=1.0)
    assert k[2] == pytest.approx(0.6 * k[0] + 0.4 * k[1], rel=1e-12)


def test_from_560_nm_only_kw_differs_from_2001():
    wl = np.arange(560.0, 701.0, 5.0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        for c in (0.03, 1.0, 30.0):
            diff = (jerlov.morel1988_kd(wl, pigment_mg_m3=c)
                    - jerlov.morel2001_kd(wl, chlorophyll_mg_m3=c))
            g88, kw88, _, _ = _data.morel1988()
            g01, kw01, _, _, _ = _data.morel2001()
            want = (np.interp(wl, g88, kw88) - np.interp(wl, g01, kw01))
            np.testing.assert_allclose(diff, want, atol=1e-15)


def test_refusals_and_no_default():
    for bad in (395.0, 705.0, np.nan):
        with pytest.raises(ValueError):
            jerlov.morel1988_kd(bad, pigment_mg_m3=0.3)
    for bad in (0.0, -1.0, np.inf, np.nan, [0.3, 1.0]):
        with pytest.raises(ValueError):
            jerlov.morel1988_kd(440.0, pigment_mg_m3=bad)
    with pytest.raises(TypeError):
        jerlov.morel1988_kd(440.0)
    with pytest.raises(TypeError):
        jerlov.morel1988_kd(440.0, chlorophyll_mg_m3=0.3)


def test_warnings():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", jerlov.ProvenanceWarning)
        jerlov.morel1988_kd([400.0, 650.0], pigment_mg_m3=0.3)
    assert not caught
    with pytest.warns(jerlov.ProvenanceWarning, match="0.03-30"):
        jerlov.morel1988_kd(440.0, pigment_mg_m3=0.01)
    with pytest.warns(jerlov.ProvenanceWarning, match="mesotrophic"):
        jerlov.morel1988_kd(655.0, pigment_mg_m3=1.0)

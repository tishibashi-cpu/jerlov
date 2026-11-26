"""Quan & Fry's (1995) refractive index of sea water: DECISIONS.md section
124, DATA.md section 51."""

from __future__ import annotations

import math
import warnings

import numpy as np
import pytest

import jerlov

#: Quan & Fry's Table 1 (p. 3478), Austin & Halikas's selected data, as
#: printed: (wavelength nm, salinity per mil, n at 1, 5, 10, 15, 20, 25 and
#: 30 C). Transcribed from the page and checked against its image.
TABLE1_TEMPERATURES = (1.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0)
TABLE1 = (
    (404.7, 0.000, (1.34375, 1.34368, 1.34348, 1.34316, 1.34274, 1.34224, 1.34166)),
    (404.7, 34.998, (1.35093, 1.35072, 1.35040, 1.34999, 1.34950, 1.34894, 1.34831)),
    (435.8, 0.000, (1.34121, 1.34114, 1.34094, 1.34062, 1.34021, 1.33971, 1.33913)),
    (435.8, 34.998, (1.34831, 1.34811, 1.34778, 1.34736, 1.34688, 1.34632, 1.34569)),
    (467.8, 0.000, (1.33913, 1.33906, 1.33886, 1.33854, 1.33813, 1.33764, 1.33706)),
    (467.8, 34.998, (1.34615, 1.34596, 1.34563, 1.34520, 1.34471, 1.34416, 1.34355)),
    (480.0, 0.000, (1.33844, 1.33837, 1.33817, 1.33786, 1.33745, 1.33695, 1.33638)),
    (480.0, 34.998, (1.34544, 1.34525, 1.34492, 1.34450, 1.34401, 1.34345, 1.34284)),
    (508.5, 0.000, (1.33701, 1.33694, 1.33674, 1.33644, 1.33603, 1.33554, 1.33497)),
    (508.5, 34.998, (1.34397, 1.34378, 1.34344, 1.34302, 1.34253, 1.34199, 1.34138)),
    (546.1, 0.000, (1.33544, 1.33537, 1.33518, 1.33487, 1.33447, 1.33398, 1.33341)),
    (546.1, 34.998, (1.34235, 1.34215, 1.34183, 1.34140, 1.34092, 1.34037, 1.33977)),
    (577.0, 0.000, (1.33434, 1.33428, 1.33408, 1.33378, 1.33338, 1.33289, 1.33233)),
    (577.0, 34.998, (1.34122, 1.34104, 1.34070, 1.34028, 1.33979, 1.33924, 1.33865)),
    (579.1, 0.000, (1.33427, 1.33421, 1.33402, 1.33371, 1.33331, 1.33282, 1.33226)),
    (579.1, 34.998, (1.34115, 1.34097, 1.34064, 1.34021, 1.33972, 1.33917, 1.33858)),
    (589.3, 0.000, (1.33395, 1.33388, 1.33369, 1.33339, 1.33299, 1.33250, 1.33194)),
    (589.3, 34.998, (1.34081, 1.34063, 1.34030, 1.33987, 1.33938, 1.33883, 1.33824)),
    (643.8, 0.000, (1.33241, 1.33234, 1.33215, 1.33186, 1.33146, 1.33098, 1.33042)),
    (643.8, 34.998, (1.33924, 1.33905, 1.33872, 1.33830, 1.33781, 1.33726, 1.33666)),
    (700.0, 0.000, (1.33109, 1.33103, 1.33084, 1.33055, 1.33016, 1.32968, 1.32913)),
    (700.0, 34.998, (1.33788, 1.33771, 1.33738, 1.33695, 1.33644, 1.33591, 1.33532)),
)


def _table():
    for wl, s, values in TABLE1:
        for t, n in zip(TABLE1_TEMPERATURES, values):
            yield wl, s, t, n


def _n(wl, s, t):
    with warnings.catch_warnings():
        # 643.8-700 nm warns; these tests check the values.
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        return jerlov.quan1995_refractive_index(wl, salinity_psu=s,
                                                temperature_c=t)


def test_table1_as_transcribed_is_whole():
    assert len(TABLE1) == 22
    assert sorted({wl for wl, _, _ in TABLE1}) == [
        404.7, 435.8, 467.8, 480.0, 508.5, 546.1, 577.0, 579.1, 589.3,
        643.8, 700.0]
    assert {s for _, s, _ in TABLE1} == {0.0, 34.998}
    assert all(len(v) == 7 for _, _, v in TABLE1)
    # Within each row the index falls with temperature, and salt raises it.
    for wl, s, values in TABLE1:
        assert all(a > b for a, b in zip(values, values[1:])), (wl, s)
    fresh = {wl: v for wl, s, v in TABLE1 if s == 0}
    salt = {wl: v for wl, s, v in TABLE1 if s > 0}
    assert all(all(a > b for a, b in zip(salt[w], fresh[w])) for w in fresh)


def test_the_fit_s_rms_deviation_is_the_paper_s():
    """The paper (p. 3479): "The rms deviation of the dn'' is 1.5e-5".
    Over all 154 values it comes out 1.56e-5, without the 700 nm
    extrapolations 1.47e-5 (DECISIONS.md section 124)."""
    rows = list(_table())
    d = np.array([_n(wl, s, t) - n for wl, s, t, n in rows])
    measured = np.array([wl < 700 for wl, _, _, _ in rows])
    assert len(d) == 154
    rms = float(np.sqrt(np.mean(d ** 2)))
    assert f"{rms:.2e}" == "1.56e-05"
    assert f"{float(np.sqrt(np.mean(d[measured] ** 2))):.2e}" == "1.47e-05"
    assert abs(rms - 1.5e-5) < 0.1e-5
    assert np.max(np.abs(d)) < 5e-5


def test_the_coefficients_and_ranges_are_as_printed():
    from jerlov import refraction as r
    assert r._QUAN1995 == (1.31405, 1.779e-4, -1.05e-6, 1.6e-8, -2.02e-6,
                           15.868, 0.01155, -0.00423, -4382.0, 1.1455e6)
    assert r._QUAN1995_NM == (400.0, 700.0)
    assert r._QUAN1995_SALINITY == (0.0, 35.0)
    assert r._QUAN1995_TEMPERATURE == (0.0, 30.0)


def test_scalars_give_a_float_and_arrays_broadcast():
    n = _n(550.0, 35.0, 20.0)
    assert isinstance(n, float)
    grid = _n(np.array([400.0, 550.0, 700.0]), 35.0,
              np.array([[0.0], [30.0]]))
    assert grid.shape == (2, 3)
    assert grid[1, 1] == pytest.approx(_n(550.0, 35.0, 30.0), abs=0)


def test_nan_is_a_gap_and_the_ranges_are_kept():
    assert math.isnan(_n(float("nan"), 35.0, 20.0))
    for wl, s, t in ((399.9, 1, 1), (700.1, 1, 1), (500, -0.1, 1),
                     (500, 35.1, 1), (500, 1, -0.1), (500, 1, 30.1),
                     (float("inf"), 1, 1), (500, float("nan"), 1),
                     (500, 1, float("nan"))):
        with pytest.raises(ValueError):
            _n(wl, s, t)
    # The ends are inside, as Table 1 has them.
    for wl, s, t in ((400, 0, 0), (700, 35, 30)):
        assert np.isfinite(_n(wl, s, t))


def test_no_default_for_salinity_or_temperature():
    with pytest.raises(TypeError):
        jerlov.quan1995_refractive_index(550.0, salinity_psu=35.0)
    with pytest.raises(TypeError):
        jerlov.quan1995_refractive_index(550.0, temperature_c=20.0)


def test_it_warns_only_where_the_table_was_extrapolated():
    with warnings.catch_warnings():
        warnings.simplefilter("error", jerlov.ProvenanceWarning)
        jerlov.quan1995_refractive_index(643.8, salinity_psu=35.0,
                                         temperature_c=20.0)
    with pytest.warns(jerlov.ProvenanceWarning, match="extrapolations"):
        jerlov.quan1995_refractive_index(643.9, salinity_psu=35.0,
                                         temperature_c=20.0)


def test_the_caller_s_arrays_are_not_modified():
    wl = np.array([450.0, np.nan, 600.0])
    t = np.array([5.0, 10.0, 15.0])
    before = (wl.copy(), t.copy())
    _n(wl, 10.0, t)
    assert np.array_equal(wl, before[0], equal_nan=True)
    assert np.array_equal(t, before[1])

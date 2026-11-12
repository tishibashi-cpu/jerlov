"""D0 and Kd at another sun angle, Gordon (1989) (DECISIONS.md section 74)."""

from __future__ import annotations

import math
import warnings

import numpy as np
import pytest

import jerlov
from jerlov import ProvenanceWarning

# Table 3, p. 1399: the sun's zenith angle in air and 1/cos of its angle
# in the water, as printed; and D0 for a uniform sky.
TABLE3_SECANT = {0: 1.000, 20: 1.035, 25: 1.054, 30: 1.079, 40: 1.142,
                 60: 1.315, 80: 1.484}
DIFFUSE = 1.197


def _sec_w(sun_deg, n=1.333):
    return 1 / math.sqrt(1 - (math.sin(math.radians(sun_deg)) / n) ** 2)


def _misses(n):
    return [s for s, v in TABLE3_SECANT.items()
            if abs(_sec_w(s, n) - v) > 0.0005 + 1e-12]


def test_the_refractive_index_against_table_3():
    """n = 1.333 gives Table 3's 1/cos column to its printed rounding at
    six angles; 40 degrees, printed 1.142, comes out 1.14148. No index
    from 1.3200 to 1.3499 matches more than six rows, and 1.33, the
    text's value, matches four (DECISIONS.md section 74)."""
    assert _misses(1.333) == [40]
    assert round(_sec_w(40), 5) == 1.14148
    assert min(len(_misses(i / 10000)) for i in range(13200, 13500)) == 1
    assert _misses(1.33) == [25, 60, 80]


def test_direct_sun_only_is_the_secant():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ProvenanceWarning)
        for sun, printed in TABLE3_SECANT.items():
            got = jerlov.gordon1989_d0(float(sun), direct_fraction=1.0)
            assert got == pytest.approx(_sec_w(sun), rel=1e-14)
            if sun != 40:
                assert abs(got - printed) <= 0.0005 + 1e-12


def test_sky_only_is_the_diffuse_row():
    for sun in (0.0, 30.0, 60.0):
        assert jerlov.gordon1989_d0(sun, direct_fraction=0.0) == DIFFUSE


def test_eq_12_written_out():
    sun = np.array([0.0, 15.0, 30.0, 45.0, 60.0])
    f = 0.7
    want = f * np.array([_sec_w(s) for s in sun]) + DIFFUSE * (1 - f)
    got = jerlov.gordon1989_d0(sun, direct_fraction=f)
    assert np.allclose(got, want, rtol=1e-14, atol=0)
    assert isinstance(jerlov.gordon1989_d0(30.0, direct_fraction=f), float)
    fs = np.array([0.2, 0.9])
    got = jerlov.gordon1989_d0(np.array([20.0, 40.0]), direct_fraction=fs)
    assert np.allclose(got, fs * np.array([_sec_w(20), _sec_w(40)])
                       + DIFFUSE * (1 - fs), rtol=1e-14, atol=0)


def test_d0_warns_above_60_degrees():
    with pytest.warns(ProvenanceWarning, match="p. 1402"):
        jerlov.gordon1989_d0(70.0, direct_fraction=0.8)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ProvenanceWarning)
        jerlov.gordon1989_d0([0.0, 60.0], direct_fraction=0.8)


def test_d0_refusals():
    f = jerlov.gordon1989_d0
    for sun in (-1.0, 90.0, 95.0, np.nan, np.inf):
        with pytest.raises(ValueError):
            f(sun, direct_fraction=0.5)
    for frac in (-0.1, 1.1, np.nan):
        with pytest.raises(ValueError):
            f(30.0, direct_fraction=frac)
    with pytest.raises(TypeError):
        f(30.0)


def test_kd_rescaling_written_out():
    kd = np.array([0.02, 0.05, 0.3])
    got = jerlov.gordon1989_kd(kd, d0_from=1.10, d0_to=1.25)
    assert np.allclose(got, kd * 1.25 / 1.10, rtol=1e-15, atol=0)
    one = jerlov.gordon1989_kd(0.1, d0_from=1.1, d0_to=1.1)
    assert isinstance(one, float) and one == 0.1


def test_kd_round_trip_through_d0():
    """From the sun at 10 degrees to 50 and back gives the Kd back."""
    d10 = jerlov.gordon1989_d0(10.0, direct_fraction=0.8)
    d50 = jerlov.gordon1989_d0(50.0, direct_fraction=0.8)
    there = jerlov.gordon1989_kd(0.05, d0_from=d10, d0_to=d50)
    assert there > 0.05
    back = jerlov.gordon1989_kd(there, d0_from=d50, d0_to=d10)
    assert back == pytest.approx(0.05, rel=1e-14)


def test_kd_refusals():
    f = jerlov.gordon1989_kd
    with pytest.raises(ValueError, match="negative"):
        f(-0.1, d0_from=1.0, d0_to=1.1)
    for bad in (0.0, -1.0, np.nan, np.inf):
        with pytest.raises(ValueError):
            f(0.1, d0_from=bad, d0_to=1.1)
        with pytest.raises(ValueError):
            f(0.1, d0_from=1.1, d0_to=bad)
    with pytest.raises(TypeError):
        f(0.1, d0_to=1.1)

"""Rrs with water and particles apart, Lee et al. (2011) (DECISIONS.md
section 73)."""

from __future__ import annotations

import warnings

import numpy as np
import pytest

import jerlov
from jerlov import ProvenanceWarning

# Table 2, p. 3159, as printed (checked against the page image):
# (sun, view, azimuth) -> (G0w, G1w, G0p, G1p).
TABLE2 = {
    (0, 0, 0): (0.0604, 0.0406, 0.0402, 0.1310),
    (0, 30, 90): (0.0596, 0.0516, 0.0408, 0.1420),
    (15, 30, 90): (0.0590, 0.0562, 0.0411, 0.1461),
    (30, 30, 90): (0.0584, 0.0601, 0.0418, 0.1492),
    (0, 40, 135): (0.0581, 0.0581, 0.0414, 0.1458),
    (15, 40, 135): (0.0614, 0.0524, 0.0425, 0.1408),
    (30, 40, 135): (0.0624, 0.0524, 0.0434, 0.1406),
}
NADIR = jerlov.LEE2011_RRS_COEFFICIENTS[(0.0, 0.0, 0.0)]


def test_the_seven_printed_geometries():
    got = {tuple(int(x) for x in k): v
           for k, v in jerlov.LEE2011_RRS_COEFFICIENTS.items()}
    assert got == TABLE2


def test_nadir_is_what_lee_2013_quotes():
    """Lee et al. (2013), p. 4244: (0.0604, 0.0406, 0.0402, 0.1310)."""
    assert NADIR == (0.0604, 0.0406, 0.0402, 0.1310)


def test_the_count_of_sets_matches_the_grid():
    """'(6 x 7 x 13 + 6)' (p. 3159): six sun angles 0-75 by 15; seven
    viewing angles 10-70 by 10 at thirteen azimuths 0-180 by 15; plus
    nadir once per sun angle."""
    suns = np.arange(0, 76, 15)
    views = np.arange(10, 71, 10)
    azimuths = np.arange(0, 181, 15)
    assert len(suns) * len(views) * len(azimuths) + len(suns) \
        == 6 * 7 * 13 + 6


def test_the_mapping_is_read_only():
    with pytest.raises(TypeError):
        jerlov.LEE2011_RRS_COEFFICIENTS[(0.0, 0.0, 0.0)] = (1, 1, 1, 1)


@pytest.mark.parametrize("geometry", sorted(TABLE2))
def test_eq_14_written_out(geometry):
    g0w, g1w, g0p, g1p = TABLE2[geometry]
    a = np.array([0.02, 0.05, 0.3, 1.0])
    bb = np.array([0.003, 0.004, 0.02, 0.1])
    bbw = np.array([0.0015, 0.0011, 0.0009, 0.0008])
    k = a + bb
    want = ((g0w + g1w * bbw / k) * bbw / k
            + (g0p + g1p * (bb - bbw) / k) * (bb - bbw) / k)
    coef = jerlov.LEE2011_RRS_COEFFICIENTS[tuple(float(x) for x in geometry)]
    got = jerlov.lee2011_rrs(a, bb, bb_water=bbw, coefficients=coef)
    assert np.allclose(got, want, rtol=1e-14, atol=0)


def test_scalars_give_a_float():
    got = jerlov.lee2011_rrs(0.02, 0.003, bb_water=0.0015,
                             coefficients=NADIR)
    assert isinstance(got, float)


def test_water_alone():
    """With no particles only the water terms remain."""
    a, bb = 0.05, 0.002
    k = a + bb
    got = jerlov.lee2011_rrs(a, bb, bb_water=bb, coefficients=NADIR)
    assert got == pytest.approx((0.0604 + 0.0406 * bb / k) * bb / k,
                                rel=1e-14)


def test_nan_passes_and_input_is_kept():
    a = np.array([0.02, np.nan])
    bb = np.array([0.003, 0.004])
    got = jerlov.lee2011_rrs(a, bb, bb_water=0.001, coefficients=NADIR)
    assert np.isfinite(got[0]) and np.isnan(got[1])
    assert np.isnan(a[1]) and a[0] == 0.02


def test_the_range_of_the_fit_warns():
    with pytest.warns(ProvenanceWarning, match="0.0002-0.37"):
        jerlov.lee2011_rrs(1.0, 0.0001, bb_water=0.00005,
                           coefficients=NADIR)
    with pytest.warns(ProvenanceWarning, match="0.0002-0.37"):
        jerlov.lee2011_rrs(0.1, 0.1, bb_water=0.001, coefficients=NADIR)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ProvenanceWarning)
        jerlov.lee2011_rrs([0.05, np.nan], [0.005, 0.01], bb_water=0.001,
                           coefficients=NADIR)


def test_refusals():
    f = jerlov.lee2011_rrs
    for a, bb in ((0.0, 0.01), (0.05, 0.0), (-0.1, 0.01), (np.inf, 0.01)):
        with pytest.raises(ValueError):
            f(a, bb, bb_water=0.001, coefficients=NADIR)
    for bbw in (-0.001, 0.02):
        with pytest.raises(ValueError, match="bb_water"):
            f(0.05, 0.01, bb_water=bbw, coefficients=NADIR)
    for coef in ((0.06, 0.04, 0.04), (0.06, 0.04, 0.04, -0.13),
                 (0.06, 0.04, 0.04, np.nan),
                 jerlov.GORDON1988_RRS_COEFFICIENTS):
        with pytest.raises(ValueError, match="coefficients"):
            f(0.05, 0.01, bb_water=0.001, coefficients=coef)
    with pytest.raises(TypeError):
        f(0.05, 0.01, bb_water=0.001)

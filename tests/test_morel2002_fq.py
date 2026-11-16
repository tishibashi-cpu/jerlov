"""Morel et al. (2002) Appendix B: f and Q for a nadir view. DECISIONS.md
section 103."""

import math
import warnings

import pytest

import jerlov


def _fq(wl, chl, sun):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        return jerlov.morel2002_nadir_fq(wl, chlorophyll_mg_m3=chl,
                                         sun_zenith_deg=sun)


def test_at_the_zenith_the_tables_come_back():
    r = _fq(412.5, 0.03, 0.0)
    assert (r.f, r.q, r.f_over_q, r.correction) == (0.297892, 3.318220,
                                                    0.089538, 1.0)
    r = _fq(660.0, 10.0, 0.0)
    assert (r.f, r.q, r.f_over_q) == (0.340204, 4.371050, 0.078632)


def test_eqs_b1_b2_b4_by_hand():
    x = 1 - math.cos(math.radians(45.0))
    r = _fq(560.0, 1.0, 45.0)
    assert r.f == pytest.approx(0.357388 + 0.305781 * x, rel=1e-12)
    assert r.q == pytest.approx(3.942030 + 2.479820 * x, rel=1e-12)
    assert r.f_over_q == pytest.approx(0.091167 + 0.013461 * x, rel=1e-12)
    assert r.correction == pytest.approx(0.091167 / r.f_over_q, rel=1e-12)
    # Sf/Q is negative at 0.03 mg m^-3: f/Q falls as the sun goes down.
    assert _fq(560.0, 0.03, 60.0).f_over_q < 0.118970


def test_beyond_60_degrees():
    with pytest.warns(jerlov.ProvenanceWarning, match="60 degrees"):
        r = jerlov.morel2002_nadir_fq(490.0, chlorophyll_mg_m3=0.3,
                                      sun_zenith_deg=70.0)
    assert math.isnan(r.f) and math.isnan(r.q) and r.f_over_q > 0
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", jerlov.ProvenanceWarning)
        jerlov.morel2002_nadir_fq(490.0, chlorophyll_mg_m3=0.3,
                                  sun_zenith_deg=59.0)
    assert not caught


@pytest.mark.parametrize("args", [
    (500.0, 0.3, 30.0), (412.0, 0.3, 30.0), (490.0, 0.2, 30.0),
    (490.0, 0.3, 76.0), (490.0, 0.3, -1.0), (490.0, 0.3, float("nan")),
    (None, 0.3, 30.0),
])
def test_refusals(args):
    wl, chl, sun = args
    with pytest.raises(ValueError):
        jerlov.morel2002_nadir_fq(wl, chlorophyll_mg_m3=chl,
                                  sun_zenith_deg=sun)


def test_no_defaults():
    with pytest.raises(TypeError):
        jerlov.morel2002_nadir_fq(490.0, chlorophyll_mg_m3=0.3)
    with pytest.raises(TypeError):
        jerlov.morel2002_nadir_fq(490.0, sun_zenith_deg=30.0)


def test_against_eq_17():
    # Measured at 490 nm, Chl 0.1: Qn = 5.20 - 1.82 cos theta_s, which the
    # paper says agrees over 0-45 degrees. At 0 and 45 degrees:
    for sun, want in ((0.0, 3.38), (45.0, 3.913)):
        eq17 = 5.20 - 1.82 * math.cos(math.radians(sun))
        assert eq17 == pytest.approx(want, abs=1e-3)
    assert _fq(490.0, 0.1, 0.0).q == 3.408430
    assert _fq(490.0, 0.1, 45.0).q == pytest.approx(3.8132, abs=1e-4)

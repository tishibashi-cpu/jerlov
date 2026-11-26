"""The Fournier-Forand phase function, as Mobley et al. (2002) print it:
DECISIONS.md section 127, DATA.md section 52."""

from __future__ import annotations

import numpy as np
import pytest

import jerlov
from jerlov._data import trapezoid

#: (n, mu) pairs across the accepted range, for the identities.
PAIRS = ((1.10, 3.5835), (1.05, 3.3), (1.15, 4.0), (1.3, 4.9), (2.0, 4.5))

#: The Ocean Optics Web Book's Table 1 (page "The Fournier-Forand Phase
#: Function", updated 2021-10-13): (n, mu, B as printed).
WEB_BOOK = ((1.021, 3.0742, 0.0001), (1.040, 3.2010, 0.001),
            (1.08, 3.483, 0.01), (1.175, 4.065, 0.1), (1.15, 4.874, 0.4))


def _ff(n, mu):
    return jerlov.fournier_forand(refractive_index=n, junge_slope=mu)


def _sphere(f, low_deg, high_deg, weight=lambda p: 1.0):
    """2 pi integral of beta * weight * sin, in log angle."""
    t = np.geomspace(low_deg, high_deg, 400001)
    p = np.radians(t)
    return 2 * np.pi * float(trapezoid(
        f.phase_function(t) * np.sin(p) * weight(p) * p, np.log(p)))


def _round_to(value, printed: str) -> bool:
    """Whether value rounds to the printed number at its printed digits."""
    decimals = len(printed.split(".")[1]) if "." in printed else 0
    return round(value, decimals) == float(printed)


@pytest.mark.parametrize("n,mu", [p for p in PAIRS if p[1] >= 3.3])
def test_eq1_integrates_to_one_over_the_sphere(n, mu):
    # Below 1e-9 degree the forward peak is too narrow to sample; its share
    # there is taken from the closed form, and is under 0.2 percent.
    f = _ff(n, mu)
    cap = f.cumulative(1e-9)
    assert cap < 0.002
    assert _sphere(f, 1e-9, 180.0) + cap == pytest.approx(1.0, abs=1e-6)


@pytest.mark.parametrize("n,mu", PAIRS + ((1.01, 3.001), (1.02, 3.05)))
def test_the_cumulative_ends_at_one_and_meets_eq3_at_90(n, mu):
    f = _ff(n, mu)
    assert f.cumulative(0.0) == 0.0
    assert f.cumulative(180.0) == pytest.approx(1.0, abs=1e-12)
    assert 1.0 - f.cumulative(90.0) == pytest.approx(f.backscatter_ratio,
                                                     abs=1e-12)


@pytest.mark.parametrize("n,mu", PAIRS)
def test_the_cumulative_is_the_integral_of_eq1(n, mu):
    f = _ff(n, mu)
    angles = np.array([0.1, 1.0, 10.0, 45.0, 90.0, 135.0, 170.0, 179.0])
    h = 1e-6 * angles
    slope = (f.cumulative(angles + h) - f.cumulative(angles - h)) / (
        2 * np.radians(h))
    want = 2 * np.pi * f.phase_function(angles) * np.sin(np.radians(angles))
    assert np.allclose(slope, want, rtol=1e-5, atol=0)


@pytest.mark.parametrize("n,mu", PAIRS)
def test_eq3_is_the_integral_over_the_back_hemisphere(n, mu):
    f = _ff(n, mu)
    assert _sphere(f, 90.0, 180.0) == pytest.approx(f.backscatter_ratio,
                                                    abs=1e-6)


def test_mobley_et_als_fit_to_petzolds_average():
    # p. 1037: n = 1.10 and mu = 3.5835 for B = 0.0183.
    f = _ff(1.10, 3.5835)
    assert _round_to(f.backscatter_ratio, "0.0183")
    # The line passes through that fit (Eq. 7), and back again.
    g = jerlov.mobley2002_fournier_forand(f.backscatter_ratio)
    assert _round_to(g.refractive_index, "1.10")
    assert abs(g.junge_slope - 3.5835) < 1e-4
    # 0.0183 as printed lies 0.0001 short of it in mu.
    h = jerlov.mobley2002_fournier_forand(0.0183)
    assert _round_to(h.refractive_index, "1.10")
    assert _round_to(h.junge_slope, "3.5834")


def test_eqs_7_and_8_are_the_same_line():
    for b in (0.0001, 0.001, 0.0183, 0.1, 0.4):
        f = jerlov.mobley2002_fournier_forand(b)
        n, mu, nu = f.refractive_index, f.junge_slope, f.nu
        assert n == pytest.approx(1.01 + 0.1542 * (mu - 3), abs=1e-12)
        d90 = 2.0 / (3.0 * (n - 1) ** 2)
        assert 2 / (3 * d90) == pytest.approx((0.01 - 0.3084 * nu) ** 2,
                                              rel=1e-12)
        assert f.backscatter_ratio == pytest.approx(b, rel=1e-9)
        assert f.relation is not None and "Eq. (7)" in f.relation


def test_the_web_books_pairs_give_its_ratios():
    for n, mu, printed in WEB_BOOK:
        b = _ff(n, mu).backscatter_ratio
        digits = len(str(printed).split(".")[1].lstrip("0"))
        assert float(f"{b:.{digits}g}") == printed, (n, mu, b)


def test_the_web_books_pairs_and_the_line():
    # Four lie within 0.005 of the line in n; the one for B = 0.4 does not.
    off = [abs(n - (1.01 + 0.1542 * (mu - 3))) for n, mu, _ in WEB_BOOK]
    assert max(off[:4]) < 0.005
    assert off[4] > 0.14


def test_the_ratio_rises_along_the_line():
    ratios = [jerlov.mobley2002_fournier_forand(b) for b in
              np.geomspace(0.0001, 0.5, 40)]
    mus = [f.junge_slope for f in ratios]
    assert all(np.diff(mus) > 0)
    end = jerlov.mobley2002_fournier_forand(0.5)
    assert end.junge_slope == 5.0
    assert end.refractive_index == pytest.approx(1.3184)


def test_mu_of_5_is_symmetric_for_any_n():
    for n in (1.05, 1.2, 1.9):
        f = _ff(n, 5.0)
        assert f.backscatter_ratio == pytest.approx(0.5, abs=1e-12)
        assert abs(f.mean_cosine()) < 1e-8


def test_the_function_is_positive_over_the_accepted_range():
    angles = np.geomspace(1e-4, 180.0, 2000)
    for n in np.linspace(1.001, 2.154, 40):
        for mu in np.linspace(3.001, 5.0, 40):
            assert np.all(_ff(n, mu).phase_function(angles) > 0), (n, mu)


def test_the_mean_cosine_is_the_integral_of_cos():
    for n, mu in PAIRS[:3]:
        f = _ff(n, mu)
        direct = _sphere(f, 1e-9, 180.0, np.cos) + f.cumulative(1e-9)
        assert f.mean_cosine() == pytest.approx(direct, abs=2e-6)
    assert _round_to(_ff(1.10, 3.5835).mean_cosine(), "0.9300")


def test_numbers_and_arrays():
    f = _ff(1.10, 3.5835)
    assert isinstance(f.phase_function(30.0), float)
    assert isinstance(f.cumulative(30.0), float)
    out = f.phase_function([30.0, 60.0])
    assert isinstance(out, np.ndarray) and out.shape == (2,)
    angles = np.array([30.0, 60.0])
    f.cumulative(angles)
    assert np.array_equal(angles, [30.0, 60.0])
    assert f.cumulative([0.0, 90.0])[0] == 0.0


@pytest.mark.parametrize("kwargs", [
    dict(refractive_index=1.0, junge_slope=3.5),
    dict(refractive_index=0.9, junge_slope=3.5),
    dict(refractive_index=2.2, junge_slope=3.5),
    dict(refractive_index=1.1, junge_slope=3.0),
    dict(refractive_index=1.1, junge_slope=5.01),
    dict(refractive_index=np.nan, junge_slope=3.5),
    dict(refractive_index=1.1, junge_slope=np.inf),
    dict(refractive_index=[1.1, 1.2], junge_slope=3.5),
])
def test_refusals_of_n_and_mu(kwargs):
    with pytest.raises(ValueError):
        jerlov.fournier_forand(**kwargs)


def test_n_and_mu_have_no_default():
    with pytest.raises(TypeError):
        jerlov.fournier_forand(refractive_index=1.1)
    with pytest.raises(TypeError):
        jerlov.fournier_forand(1.1, 3.5)


@pytest.mark.parametrize("bad", [0.0, 0.00009, 0.51, -0.1, np.nan, np.inf])
def test_refusals_of_the_ratio(bad):
    with pytest.raises(ValueError):
        jerlov.mobley2002_fournier_forand(bad)


@pytest.mark.parametrize("bad", [0.0, -1.0, 180.5, np.nan, np.inf])
def test_refusals_of_the_angle(bad):
    f = _ff(1.10, 3.5835)
    with pytest.raises(ValueError):
        f.phase_function(bad)
    if bad != 0.0:
        with pytest.raises(ValueError):
            f.cumulative(bad)
    with pytest.raises(ValueError):
        f.phase_function(np.ones((2, 2)))


def test_the_figures_quoted_in_data_md_section_52():
    fit = _ff(1.10, 3.5835)
    assert f"{fit.backscatter_ratio:.6f}" == "0.018313"
    assert f"{1.01 + 0.1542 * (3.5835 - 3):.6f}" == "1.099976"
    assert f"{jerlov.mobley2002_fournier_forand(0.0183).junge_slope:.4f}" \
        == "3.5834"
    low = jerlov.mobley2002_fournier_forand(0.0001).refractive_index
    high = jerlov.mobley2002_fournier_forand(0.5).refractive_index
    assert (f"{low:.3f}", f"{high:.3f}") == ("1.021", "1.318")
    assert f"{1.01 + 0.1542 * (4.874 - 3):.3f}" == "1.299"

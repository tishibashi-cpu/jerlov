"""Turning a single-angle measurement into bb, and the limits of doing so."""

from __future__ import annotations

import math
import warnings

import numpy as np
import pytest

import jerlov
from jerlov.backscattering import AngleWarning, DEPOLARISATION_RATIO


# -- the analytic half ----------------------------------------------------


def test_pure_water_backscattering_is_the_integral_of_its_own_vsf():
    """bb_w must be what Eq. (3) gives when applied to Eq. (4)."""
    for nm in (440.0, 532.0, 650.0):
        theta = np.radians(np.linspace(90.0, 180.0, 90001))
        vsf = jerlov.pure_water_vsf(np.degrees(theta), nm)
        integrated = 2 * math.pi * float(np.trapezoid(vsf * np.sin(theta), theta))
        assert jerlov.pure_water_backscattering(nm) == pytest.approx(
            integrated, rel=1e-6
        )


def test_chi_w_gives_the_same_answer_at_every_angle():
    """The water conversion is exact, so it cannot depend on where you look."""
    r = (1 - DEPOLARISATION_RATIO) / (1 + DEPOLARISATION_RATIO)
    nm = 532.0
    expected = jerlov.pure_water_backscattering(nm)
    for angle in (90.0, 110.0, 130.0, 150.0, 170.0):
        chi_w = (1 + r / 3) / (1 + r * math.cos(math.radians(angle)) ** 2)
        recovered = 2 * math.pi * jerlov.pure_water_vsf(angle, nm) * chi_w
        assert recovered == pytest.approx(expected, rel=1e-9)


def test_pure_water_scattering_rises_steeply_towards_the_blue():
    """Morel's exponent is -4.32, close to Rayleigh's -4."""
    blue = jerlov.pure_water_backscattering(400.0)
    red = jerlov.pure_water_backscattering(700.0)
    assert blue / red == pytest.approx((700.0 / 400.0) ** 4.32, rel=1e-9)


def test_fresher_water_scatters_less():
    assert (jerlov.pure_water_backscattering(532.0, salinity_psu=0.0)
            < jerlov.pure_water_backscattering(532.0, salinity_psu=37.0))


# -- the tabulated half ---------------------------------------------------


def test_chi_p_matches_the_published_table():
    published = {90: 0.71, 100: 0.90, 110: 1.03, 120: 1.12, 130: 1.17,
                 140: 1.18, 150: 1.13, 160: 1.00, 170: 0.62}
    for angle, value in published.items():
        assert jerlov.particulate_chi(angle) == pytest.approx(value)


def test_chi_p_peaks_in_the_middle_of_the_backward_hemisphere():
    """Which is why both papers recommend 110-160 degrees."""
    angles = np.arange(90.0, 171.0, 1.0)
    values = [jerlov.particulate_chi(a) for a in angles]
    assert 130.0 <= angles[int(np.argmax(values))] <= 145.0


def test_chi_w_and_chi_p_cross_near_118_degrees():
    """The paper's reason that instruments settled on 120."""
    r = (1 - DEPOLARISATION_RATIO) / (1 + DEPOLARISATION_RATIO)
    angles = np.linspace(90.0, 170.0, 8001)
    gap = [
        (1 + r / 3) / (1 + r * math.cos(math.radians(a)) ** 2)
        - jerlov.particulate_chi(a)
        for a in angles
    ]
    crossing = angles[int(np.argmin(np.abs(gap)))]
    assert 114.0 < crossing < 122.0, crossing


def test_angles_outside_the_measurements_are_refused():
    for angle in (89.0, 171.0, 180.0, 0.0):
        with pytest.raises(ValueError, match="90 to 170"):
            jerlov.particulate_chi(angle)


# -- the conversion -------------------------------------------------------


def test_it_reproduces_the_published_equation():
    beta, angle, nm = 0.0021, 140.0, 532.0
    result = jerlov.bb_from_vsf(beta, angle, nm)
    chi_p = jerlov.particulate_chi(angle)
    expected = (2 * math.pi * chi_p
                * (beta - jerlov.pure_water_vsf(angle, nm))
                + jerlov.pure_water_backscattering(nm))
    assert result.bb == pytest.approx(expected)
    assert result.particulate + result.water == pytest.approx(result.bb)


def test_water_alone_gives_the_water_answer():
    """Measuring pure sea water must return bb_w and no particles."""
    nm = 532.0
    beta = jerlov.pure_water_vsf(130.0, nm)
    result = jerlov.bb_from_vsf(beta, 130.0, nm)
    assert result.particulate == pytest.approx(0.0, abs=1e-12)
    assert result.bb == pytest.approx(jerlov.pure_water_backscattering(nm))


def test_more_scattering_gives_more_backscattering():
    previous = -1.0
    for beta in (0.0005, 0.001, 0.002, 0.005):
        value = jerlov.bb_from_vsf(beta, 140.0, 532.0).bb
        assert value > previous
        previous = value


def test_a_typical_coastal_reading_lands_in_the_reported_range():
    """A sanity anchor, not a validation. Coastal bb/b is put at 0.015-0.03."""
    result = jerlov.bb_from_vsf(0.0021, 140.0, 532.0, salinity_psu=35.0)
    assert 0.005 < result.bb < 0.05


def test_170_degrees_warns_about_its_own_error():
    with pytest.warns(AngleWarning, match="34.8%"):
        jerlov.bb_from_vsf(0.002, 170.0, 532.0)


def test_the_recommended_angles_do_not_warn():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        for angle in (110.0, 120.0, 130.0, 140.0, 150.0, 160.0):
            jerlov.bb_from_vsf(0.002, angle, 532.0)


def test_a_reading_below_pure_water_warns_rather_than_passing():
    with pytest.warns(AngleWarning, match="below that of pure sea water"):
        jerlov.bb_from_vsf(1e-6, 140.0, 400.0)


def test_negative_scattering_is_refused():
    with pytest.raises(ValueError, match="cannot be negative"):
        jerlov.bb_from_vsf(-0.001, 140.0, 532.0)


def test_the_result_carries_the_quoted_error():
    result = jerlov.bb_from_vsf(0.002, 140.0, 532.0)
    assert result.chi_p == pytest.approx(1.18)
    assert result.quoted_error_percent == pytest.approx(3.5)
    assert result.angle_deg == 140.0


def test_scalar_in_scalar_out():
    assert isinstance(jerlov.bb_from_vsf(0.002, 140.0, 532.0).bb, float)
    array = jerlov.bb_from_vsf([0.001, 0.002], 140.0, 532.0).bb
    assert isinstance(array, np.ndarray) and array.shape == (2,)


# -- what it does not do --------------------------------------------------


def test_it_says_nothing_about_a_jerlov_type():
    """The point of DATA.md section 10 has not quietly gone away."""
    with pytest.raises(jerlov.MissingQuantityError):
        jerlov.water("III").bb(532)

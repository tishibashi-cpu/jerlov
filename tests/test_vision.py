"""Visual pigment templates and receptor noise (DECISIONS.md section 64).

The constants were read from the papers' page images; each test reproduces
a number the paper prints, or one of its equations, from them."""

from __future__ import annotations

import warnings

import numpy as np
import pytest

import jerlov

FINE = np.arange(331.0, 900.0, 0.001)
#: The peaks of the pigments Govardovskii et al. measured (Table 1, p. 519).
MEASURED = {"A1": (357.0, 569.0), "A2": (444.0, 619.0)}
#: Their relations between lambda_max and the long-wave half-maximum:
#: eq. (3), p. 516, for A1 and eq. (7), p. 517, for A2.
HALF_MAXIMUM = {
    "A1": lambda l5: 45.02 + 0.756 * l5 + 0.000141 * l5 ** 2,
    "A2": lambda l5: 30.6 + 0.7907 * l5 + 0.000102 * l5 ** 2,
}


def _alpha(lambda_max, chromophore, wl=FINE):
    return jerlov.visual_pigment_template(
        wl, lambda_max=lambda_max, chromophore=chromophore, beta=False)


def _quiet_alpha(lambda_max, chromophore):
    with warnings.catch_warnings():
        warnings.simplefilter("error", jerlov.ProvenanceWarning)
        return _alpha(lambda_max, chromophore)


@pytest.mark.parametrize("chromophore", ["A1", "A2"])
def test_the_half_maximum_relation_holds_across_the_measured_range(
        chromophore):
    """Eqs. (3) and (7) follow from the paper's template; they must follow
    from this one, within 0.5 nm across the pigments it measured."""
    lo, hi = MEASURED[chromophore]
    for lambda_max in np.arange(lo, hi + 0.1, 4.0):
        s = _quiet_alpha(lambda_max, chromophore)
        peak = int(np.argmax(s))
        half = FINE[peak:][np.argmin(np.abs(s[peak:] - 0.5 * s[peak]))]
        assert HALF_MAXIMUM[chromophore](half) == pytest.approx(
            lambda_max, abs=0.5)


@pytest.mark.parametrize("chromophore", ["A1", "A2"])
def test_the_alpha_band_peaks_at_lambda_max_near_one(chromophore):
    lo, hi = MEASURED[chromophore]
    for lambda_max in np.arange(lo, hi + 0.1, 4.0):
        s = _quiet_alpha(lambda_max, chromophore)
        assert FINE[np.argmax(s)] == pytest.approx(lambda_max, abs=0.5)
        assert s.max() == pytest.approx(1.0, abs=0.002)


def test_the_beta_band_gives_the_papers_most_accurate_point():
    """p. 516: the regressions pass through the amphibian rhodopsins'
    average, lambda_max 502.6 nm, beta-peak 347.3 nm, bandwidth 57.5 nm.
    The beta-band is the difference between the full template and the
    alpha-band, a Gaussian whose peak and width are read back here."""
    wl = np.arange(331.0, 500.0, 0.01)
    full = jerlov.visual_pigment_template(wl, lambda_max=502.6,
                                          chromophore="A1")
    band = full - _alpha(502.6, "A1", wl)
    peak = wl[np.argmax(band)]
    assert round(peak, 1) == 347.3
    assert band.max() == pytest.approx(0.26, abs=1e-6)
    # exp(-1) of the peak lies one bandwidth from it
    above = wl[wl > peak][np.argmin(np.abs(band[wl > peak]
                                           - 0.26 * np.exp(-1.0)))]
    assert round(above - peak, 1) == 57.5


def test_a2_beta_band_is_the_papers_fixed_amplitude():
    """No equation for it; 0.37 is the value the paper fixed (p. 517)."""
    wl = np.arange(331.0, 500.0, 0.01)
    lambda_max = 560.0
    band = (jerlov.visual_pigment_template(wl, lambda_max=lambda_max,
                                           chromophore="A2")
            - _alpha(lambda_max, "A2", wl))
    assert band.max() == pytest.approx(0.37, abs=1e-6)
    assert wl[np.argmax(band)] == pytest.approx(216.7 + 0.287 * lambda_max,
                                                abs=0.01)


def test_a_number_gives_a_number_and_an_array_an_array():
    one = jerlov.visual_pigment_template(500.0, lambda_max=500.0,
                                         chromophore="A1")
    many = jerlov.visual_pigment_template([450.0, 500.0], lambda_max=500.0,
                                          chromophore="A1")
    assert isinstance(one, float)
    assert many.shape == (2,) and many[1] == one


@pytest.mark.parametrize("chromophore", ["A1", "A2"])
def test_outside_the_measured_peaks_it_warns(chromophore):
    lo, hi = MEASURED[chromophore]
    for lambda_max in (lo - 1.0, hi + 1.0):
        with pytest.warns(jerlov.ProvenanceWarning, match="not their fit"):
            jerlov.visual_pigment_template(500.0, lambda_max=lambda_max,
                                           chromophore=chromophore)


@pytest.mark.parametrize("kwargs, message", [
    (dict(lambda_max=350.0, chromophore="A1"), "above 350"),
    (dict(lambda_max=float("nan"), chromophore="A1"), "above 350"),
    (dict(lambda_max=[500.0, 510.0], chromophore="A1"), "one number"),
    (dict(lambda_max=500.0, chromophore="a1"), "'A1' or 'A2'"),
])
def test_the_template_refuses_what_the_paper_does_not_cover(kwargs, message):
    with pytest.raises(ValueError, match=message):
        jerlov.visual_pigment_template(500.0, **kwargs)


@pytest.mark.parametrize("wavelength", [330.0, 300.0, float("nan"),
                                        float("inf")])
def test_the_template_refuses_wavelengths_it_was_not_made_for(wavelength):
    with pytest.raises(ValueError, match="above 330 nm"):
        jerlov.visual_pigment_template([wavelength, 500.0], lambda_max=500.0,
                                       chromophore="A1")


def test_the_template_needs_both_its_parameters_named():
    with pytest.raises(TypeError):
        jerlov.visual_pigment_template(500.0, lambda_max=500.0)
    with pytest.raises(TypeError):
        jerlov.visual_pigment_template(500.0, chromophore="A1")


# -- receptor noise --------------------------------------------------------

RNG = np.random.default_rng(1998)


def _a7(delta, noise, rng=RNG):
    """(A7), p. 356, with a random opponent matrix F whose rows sum to zero
    (A8) and the noise diagonal (A9)."""
    n = delta.size
    f = rng.normal(size=(n - 1, n))
    f -= f.mean(axis=1, keepdims=True)
    x = f @ delta
    return float(np.sqrt(x @ np.linalg.solve(
        f @ np.diag(noise ** 2) @ f.T, x)))


def _printed(delta, e):
    """Eqs. (3) to (5), p. 353; eq. (4) with the Delta its last term lacks
    in print restored."""
    if delta.size == 2:
        q1, q2 = delta
        e1, e2 = e
        return np.sqrt((q1 - q2) ** 2 / (e1 ** 2 + e2 ** 2))
    if delta.size == 3:
        q1, q2, q3 = delta
        e1, e2, e3 = e
        return np.sqrt((e1 ** 2 * (q3 - q2) ** 2 + e2 ** 2 * (q3 - q1) ** 2
                        + e3 ** 2 * (q1 - q2) ** 2)
                       / ((e1 * e2) ** 2 + (e1 * e3) ** 2 + (e2 * e3) ** 2))
    q1, q2, q3, q4 = delta
    e1, e2, e3, e4 = e
    return np.sqrt(
        ((e1 * e2) ** 2 * (q4 - q3) ** 2 + (e1 * e3) ** 2 * (q4 - q2) ** 2
         + (e1 * e4) ** 2 * (q3 - q2) ** 2 + (e2 * e3) ** 2 * (q4 - q1) ** 2
         + (e2 * e4) ** 2 * (q3 - q1) ** 2 + (e3 * e4) ** 2 * (q2 - q1) ** 2)
        / ((e1 * e2 * e3) ** 2 + (e1 * e2 * e4) ** 2 + (e1 * e3 * e4) ** 2
           + (e2 * e3 * e4) ** 2))


@pytest.mark.parametrize("n", [2, 3, 4])
def test_the_distance_is_the_papers_equations(n):
    for _ in range(200):
        a = 1.0 + RNG.normal(size=n) * 0.05
        b = 1.0 + RNG.normal(size=n) * 0.05
        e = RNG.uniform(0.02, 0.2, size=n)
        d = jerlov.receptor_noise_distance(a, b, noise=e)
        assert d == pytest.approx(_printed(a - b, e), rel=1e-9)
        assert d == pytest.approx(_a7(a - b, e), rel=1e-6)


def test_eq_4_as_printed_is_not_a_distance():
    """The misprint: without the Delta on q_2, the last term of eq. (4)
    holds the catch itself, 1 at the background (eq. 2), so identical
    stimuli come out apart. DATA.md section 26."""
    e = np.array([0.05, 0.07, 0.1])
    for a in (np.ones(3), np.array([1.03, 0.98, 1.01])):
        q1, q2, q3 = a - a
        e1, e2, e3 = e
        printed = np.sqrt((e1 ** 2 * (q3 - q2) ** 2 + e2 ** 2 * (q3 - q1) ** 2
                           + e3 ** 2 * (q1 - a[1]) ** 2)
                          / ((e1 * e2) ** 2 + (e1 * e3) ** 2
                             + (e2 * e3) ** 2))
        assert printed > 1.0
        assert jerlov.receptor_noise_distance(a, a, noise=e) == 0.0


def test_more_receptors_follow_the_general_form_too():
    for n in (5, 6):
        a = 1.0 + RNG.normal(size=n) * 0.05
        e = RNG.uniform(0.02, 0.2, size=n)
        assert jerlov.receptor_noise_distance(a, np.ones(n), noise=e) \
            == pytest.approx(_a7(a - 1.0, e), rel=1e-6)


def test_a_change_of_intensity_alone_is_no_distance():
    """Assumption 2, p. 352: opponent channels ignore intensity."""
    e = np.array([0.05, 0.07, 0.1, 0.08])
    assert jerlov.receptor_noise_distance(np.full(4, 1.3), np.ones(4),
                                          noise=e) == pytest.approx(
        0.0, abs=1e-12)


def test_pairs_broadcast_along_the_leading_axes():
    e = np.array([0.05, 0.07, 0.1])
    a = 1.0 + RNG.normal(size=(5, 3)) * 0.05
    together = jerlov.receptor_noise_distance(a, np.ones(3), noise=e)
    assert together.shape == (5,)
    for row, d in zip(a, together):
        assert jerlov.receptor_noise_distance(row, np.ones(3), noise=e) \
            == pytest.approx(d, rel=1e-12)
    assert isinstance(jerlov.receptor_noise_distance(a[0], np.ones(3),
                                                     noise=e), float)


@pytest.mark.parametrize("a, b, noise, message", [
    ([1.0, 1.1], [1.0, 1.0], [0.05], "two or more"),
    ([1.0, 1.1], [1.0, 1.0], [0.05, 0.0], "positive"),
    ([1.0, 1.1], [1.0, 1.0], [0.05, float("nan")], "positive"),
    ([1.0, 1.1, 1.0], [1.0, 1.0], [0.05, 0.05], "last axis"),
    (1.0, [1.0, 1.0], [0.05, 0.05], "one value for each"),
    ([1.0, float("inf")], [1.0, 1.0], [0.05, 0.05], "finite"),
])
def test_the_distance_refuses_what_it_cannot_use(a, b, noise, message):
    with pytest.raises(ValueError, match=message):
        jerlov.receptor_noise_distance(a, b, noise=noise)


def test_the_noise_has_no_default():
    with pytest.raises(TypeError):
        jerlov.receptor_noise_distance([1.0, 1.1], [1.0, 1.0])


@pytest.mark.parametrize("n", [2, 3, 4])
def test_the_printed_equations_agree_with_a7_as_data_md_says(n):
    """DATA.md section 26: eqs. (3) and (5) as printed, and eq. (4) with
    its Delta restored, agree with (A7) to within 2e-9. F here is the
    differences of neighbouring receptors, rows summing to zero (A8)."""
    f = np.eye(n - 1, n) - np.eye(n - 1, n, k=1)
    rng = np.random.default_rng(356)
    for _ in range(500):
        delta = rng.normal(size=n) * 0.05
        e = rng.uniform(0.02, 0.2, size=n)
        x = f @ delta
        a7 = np.sqrt(x @ np.linalg.solve(f @ np.diag(e ** 2) @ f.T, x))
        assert _printed(delta, e) == pytest.approx(a7, rel=2e-9)

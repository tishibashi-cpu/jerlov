"""Röttgers et al.'s (2013) scatter corrections: DECISIONS.md section 100."""

import warnings

import numpy as np
import pytest

import jerlov

AM = np.array([0.62, 0.41, 0.25, 0.12])
CM = np.array([2.1, 1.8, 1.5, 1.3])
AM715, CM715 = 0.06, 1.1


def _f(method, **kwargs):
    return jerlov.rottgers2013_scatter_correction(AM, CM, AM715, CM715,
                                                  method=method, **kwargs)


def test_flat_is_eq_1():
    np.testing.assert_allclose(_f("flat"), AM - AM715, rtol=1e-15)


def test_proportional_is_eq_2b_and_2a():
    for ec in (1.0, 0.56):
        want = AM - AM715 * (CM / ec - AM) / (CM715 / ec - AM715)
        np.testing.assert_allclose(_f("proportional", ec=ec), want,
                                   rtol=1e-14)
    # ec = 1: Zaneveld et al.'s (1994) form, Eq. (2a).
    np.testing.assert_allclose(
        _f("proportional", ec=1.0),
        AM - AM715 * (CM - AM) / (CM715 - AM715), rtol=1e-14)


def test_the_plus_methods_are_eqs_3_and_4():
    a715 = 0.02
    np.testing.assert_allclose(_f("flat+", a_ref=a715),
                               AM - (AM715 - a715), rtol=1e-15)
    for ec in (1.0, 0.56):
        want = AM - (AM715 - a715) * (CM / ec - AM) / (CM715 / ec - a715)
        np.testing.assert_allclose(_f("proportional+", ec=ec, a_ref=a715),
                                   want, rtol=1e-14)
    # With a715 = 0, Eq. (3) is Eq. (1) ...
    np.testing.assert_allclose(_f("flat+", a_ref=0.0), _f("flat"),
                               rtol=1e-15)
    # ... but Eq. (4) is not Eq. (2b): the denominators differ by am715.
    four = _f("proportional+", ec=1.0, a_ref=0.0)
    two = _f("proportional", ec=1.0)
    np.testing.assert_allclose((AM - four) / (AM - two),
                               (CM715 - AM715) / CM715, rtol=1e-12)


def test_one_case_by_hand():
    # am 0.5, cm 1.5, am715 0.05, cm715 0.8: 0.5 - 0.05 * 1.0 / 0.75.
    assert jerlov.rottgers2013_scatter_correction(
        0.5, 1.5, 0.05, 0.8, method="proportional", ec=1.0) \
        == pytest.approx(0.5 - 0.05 / 0.75, rel=1e-14)
    assert isinstance(jerlov.rottgers2013_scatter_correction(
        0.5, 1.5, 0.05, 0.8, method="flat"), float)


def test_nan_is_a_gap():
    out = jerlov.rottgers2013_scatter_correction(
        [0.5, np.nan], [1.5, 1.2], 0.05, 0.8, method="proportional", ec=1.0)
    assert np.isnan(out[1]) and not np.isnan(out[0])


@pytest.mark.parametrize("method,kwargs", [
    ("flat", dict(ec=1.0)), ("flat", dict(a_ref=0.01)),
    ("proportional", {}), ("proportional", dict(ec=1.0, a_ref=0.01)),
    ("flat+", {}), ("proportional+", dict(ec=1.0)),
    ("proportional+", dict(a_ref=0.01)), ("baseline", {}), (None, {}),
    ("proportional", dict(ec=0.0)), ("proportional", dict(ec=-1.0)),
    ("proportional", dict(ec=np.nan)), ("flat+", dict(a_ref=np.inf)),
])
def test_refusals(method, kwargs):
    with pytest.raises(ValueError):
        _f(method, **kwargs)


def test_no_method_is_chosen_for_you():
    with pytest.raises(TypeError):
        jerlov.rottgers2013_scatter_correction(AM, CM, AM715, CM715)


def test_a_denominator_that_is_not_positive_is_refused():
    with pytest.raises(ValueError, match="denominator"):
        jerlov.rottgers2013_scatter_correction(
            0.5, 1.5, 0.8, 0.8, method="proportional", ec=1.0)
    with pytest.raises(ValueError, match="denominator"):
        jerlov.rottgers2013_scatter_correction(
            0.5, 1.5, 0.05, 0.01, method="proportional+", ec=1.0,
            a_ref=0.02)
    with pytest.raises(ValueError):
        jerlov.rottgers2013_scatter_correction(
            AM, CM, [0.05, 0.06], CM715, method="flat")


def test_a715_is_eq_5():
    for am in (0.1, 0.5, 2.0, 7.0):
        assert jerlov.rottgers2013_a715(am) == pytest.approx(
            0.212 * am ** 1.135, rel=1e-14)
    out = jerlov.rottgers2013_a715(np.array([0.5, np.nan]))
    assert np.isnan(out[1])
    with pytest.raises(ValueError):
        jerlov.rottgers2013_a715(0.0)
    with pytest.raises(ValueError):
        jerlov.rottgers2013_a715(np.inf)


def test_a715_warns_outside_their_samples():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", jerlov.ProvenanceWarning)
        jerlov.rottgers2013_a715(1.0)
    assert not caught
    for am in (0.005, 12.0):
        with pytest.warns(jerlov.ProvenanceWarning, match="Fig. 4"):
            jerlov.rottgers2013_a715(am)

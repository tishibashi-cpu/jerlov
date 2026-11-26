"""What the review after 1.22.0 found (DECISIONS.md section 105): one
function without the keyword shim, its one-number check, a gap the flat
scatter corrections keep, and a NaN wavelength's message."""

from __future__ import annotations

import inspect
import warnings

import numpy as np
import pytest

import jerlov
from jerlov import _data


def _public_functions():
    for name in jerlov.__all__:
        obj = getattr(jerlov, name)
        if inspect.isfunction(obj):
            yield name, obj


def test_every_positional_only_function_takes_a_keyword_with_a_warning():
    # Section 61's shim; since 1.14.0 every new function has carried it
    # (section 86), and morel2002_nadir_fq was the one left out.
    missing = []
    for name, function in _public_functions():
        parameters = inspect.signature(inspect.unwrap(function)).parameters
        if any(p.kind is p.POSITIONAL_ONLY for p in parameters.values()) \
                and not hasattr(function, "__wrapped__"):
            missing.append(name)
    assert not missing


def test_morel2002_nadir_fq_by_keyword():
    kw = dict(chlorophyll_mg_m3=0.1, sun_zenith_deg=30.0)
    expected = jerlov.morel2002_nadir_fq(490.0, **kw)
    with pytest.warns(FutureWarning, match="by position, not by keyword"):
        got = jerlov.morel2002_nadir_fq(wavelength_nm=490.0, **kw)
    assert got == expected


@pytest.mark.parametrize("bad", ["412.5", np.nan, np.inf, [412.5], None])
def test_morel2002_nadir_fq_takes_one_finite_number(bad):
    # Text is refused by the check every public function has since 1.29.0
    # (DECISIONS.md section 126), in its own words.
    said = "must be (one finite number|a number or numbers)"
    with pytest.raises(ValueError, match=said):
        jerlov.morel2002_nadir_fq(bad, chlorophyll_mg_m3=0.1,
                                  sun_zenith_deg=0.0)
    with pytest.raises(ValueError, match="sun_zenith_deg " + said):
        jerlov.morel2002_nadir_fq(412.5, chlorophyll_mg_m3=0.1,
                                  sun_zenith_deg=bad)


def test_morel2002_nadir_fq_still_takes_numpy_numbers():
    a = jerlov.morel2002_nadir_fq(np.float32(412.5),
                                  chlorophyll_mg_m3=np.array(0.1),
                                  sun_zenith_deg=np.int64(0))
    assert a == jerlov.morel2002_nadir_fq(412.5, chlorophyll_mg_m3=0.1,
                                          sun_zenith_deg=0.0)


def test_morel2002_nadir_fq_points_to_the_full_tables():
    doc = jerlov.morel2002_nadir_fq.__doc__
    assert "could not reach" not in doc
    assert ":func:`morel2002_fq_tables`" in doc


def test_one_check_of_one_number():
    from jerlov import absorption_meter, fq_tables, sky
    assert sky._number is absorption_meter._number is fq_tables._one \
        is _data.finite_number
    assert _data.finite_number(np.float64(2.5), "x") == 2.5
    for bad in ("1", np.nan, -np.inf, [1.0], np.zeros(2)):
        with pytest.raises(ValueError, match="x must be one finite number"):
            _data.finite_number(bad, "x")


@pytest.mark.parametrize("method,extra", [("flat", {}),
                                          ("flat+", {"a_ref": 0.01})])
def test_the_flat_methods_ignore_a_gap_in_cm(method, extra):
    """Section 105 kept cm's gaps in the flat methods' result; since 1.29.0
    (section 126) they do not reach it, since Eqs. (1) and (3) do not use
    cm. A gap in am still does."""
    out = jerlov.rottgers2013_scatter_correction(
        np.array([0.5, 0.4]), np.array([np.nan, 1.0]), 0.05, 0.5,
        method=method, **extra)
    assert np.all(np.isfinite(out))
    gap = jerlov.rottgers2013_scatter_correction(
        np.array([np.nan, 0.4]), np.array([1.0, 1.0]), 0.05, 0.5,
        method=method, **extra)
    assert np.isnan(gap[0]) and np.isfinite(gap[1])
    assert "a gap in cm leaves their result as it is" in " ".join(
        jerlov.rottgers2013_scatter_correction.__doc__.split())


@pytest.mark.parametrize("function,kw", [
    (jerlov.morel2001_kd, {"chlorophyll_mg_m3": 0.1}),
    (jerlov.morel1988_kd, {"pigment_mg_m3": 0.1}),
    (jerlov.bricaud1995_aph, {"chlorophyll_mg_m3": 0.1}),
    (jerlov.morel2001_bbp, {"chlorophyll_mg_m3": 0.1}),
])
def test_a_nan_wavelength_is_named_as_such(function, kw):
    with pytest.raises(ValueError, match="wavelengths must be numbers, "
                                         "not NaN"):
        function([450.0, np.nan], **kw)
    with pytest.raises(ValueError, match="must lie within"):
        function([450.0, 900.0], **kw)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        assert np.all(np.isfinite(function([450.0, 500.0], **kw)))

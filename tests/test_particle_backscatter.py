"""bb from the particles' backscattering ratio (DECISIONS.md section 68)."""

from __future__ import annotations

import warnings

import numpy as np
import pytest

import jerlov
from jerlov import MissingQuantityError, ProvenanceWarning

# Both sources print Haltrin's pure water term as 0.00583 (400/l)^4.322:
# Williamson & Hollins (2022) Eq. (8), Solonenko & Mobley (2015) Eq. (8a).
BW_COEFF = 0.00583
BW_EXPONENT = 4.322

SOURCES = ("williamson2022", "solonenko2015")


def _quiet(call):
    """Flagged values warn; these tests are about the arithmetic."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ProvenanceWarning)
        return call()


def _waters():
    for source in SOURCES:
        for water_type in jerlov.get_source(source).water_types:
            yield jerlov.water(water_type, source=source)


def test_the_source_constants_are_the_printed_ones():
    for source in SOURCES:
        model = jerlov.get_source(source).scattering
        assert (model.bw_coeff, model.bw_exponent) == (BW_COEFF, BW_EXPONENT)


@pytest.mark.parametrize("ratio", [0.005, 0.0183, 0.03])
def test_the_formula_written_out(ratio):
    for w in _waters():
        for wl in (300.0, 412.5, 550.0, 700.0):
            b = _quiet(lambda: w.b(wl))
            bw = BW_COEFF * (400.0 / wl) ** BW_EXPONENT
            got = _quiet(lambda: w.bb(wl, particle_backscatter_ratio=ratio))
            assert isinstance(got, float)
            assert got == pytest.approx(0.5 * bw + ratio * (b - bw),
                                        rel=1e-12)


def test_arrays_match_scalars():
    w = jerlov.water("II", source="solonenko2015")
    wl = np.array([400.0, 455.0, 510.0, 600.0])
    got = w.bb(wl, particle_backscatter_ratio=0.0183)
    assert isinstance(got, np.ndarray) and got.shape == wl.shape
    for x, y in zip(wl, got):
        assert y == w.bb(float(x), particle_backscatter_ratio=0.0183)
    assert w.bb([], particle_backscatter_ratio=0.0183).shape == (0,)


def test_never_below_pure_water_at_one_nm():
    """b - b_w > 0 for every type of both sources, so bb > 0.5 b_w."""
    for w in _waters():
        lo, hi = w.range_nm
        wl = np.arange(lo, hi + 1.0, 1.0)
        bw = BW_COEFF * (400.0 / wl) ** BW_EXPONENT
        b = _quiet(lambda: w.b(wl))
        assert np.all(b > bw), (w.name, w.source.key)
        for ratio in (1e-6, 0.0183, 0.4999):
            bb = _quiet(lambda: w.bb(wl, particle_backscatter_ratio=ratio))
            assert np.all(bb > 0.5 * bw)


def test_half_and_half_is_half_of_b():
    """Water and particles both symmetric: bb = b / 2. Reached as a limit,
    because 0.5 itself is refused, as for backscatter_ratio."""
    w = jerlov.water("IB", source="williamson2022")
    r = np.nextafter(0.5, 0.0)
    assert w.bb(550.0, particle_backscatter_ratio=r) == pytest.approx(
        0.5 * w.b(550.0), rel=1e-12)


def test_where_the_two_ratios_differ():
    """Clear water: the whole water's ratio gives a bb below what the water
    alone backscatters; the particles' ratio does not. The figures quoted
    in CHANGELOG.md for 1.4.0, from unflagged values (an error if not)."""
    w = jerlov.water("IB", source="solonenko2015")
    bw = BW_COEFF * (400.0 / 450.0) ** BW_EXPONENT
    with warnings.catch_warnings():
        warnings.simplefilter("error", ProvenanceWarning)
        whole = w.bb(450.0, backscatter_ratio=0.0183)
        particles = w.bb(450.0, particle_backscatter_ratio=0.0183)
    assert whole < 0.5 * bw < particles
    assert (f"{whole:.3g}", f"{0.5 * bw:.3g}", f"{particles:.3g}") == (
        "0.00124", "0.00175", "0.00293")


def test_backscatter_ratio_is_unchanged():
    for w in _waters():
        b = _quiet(lambda: w.b(550.0))
        assert _quiet(lambda: w.bb(550.0, backscatter_ratio=0.02)) == b * 0.02


def test_neither_or_both():
    w = jerlov.water("III")
    with pytest.raises(MissingQuantityError,
                       match="particle_backscatter_ratio"):
        w.bb(550.0)
    with pytest.raises(ValueError, match="not both"):
        w.bb(550.0, backscatter_ratio=0.01, particle_backscatter_ratio=0.01)


@pytest.mark.parametrize("bad", [0.0, -0.01, 0.5, 0.9, np.nan, np.inf,
                                 -np.inf])
def test_the_ratio_must_lie_in_range(bad):
    w = jerlov.water("III")
    with pytest.raises(ValueError, match=r"\(0, 0.5\)"):
        w.bb(550.0, particle_backscatter_ratio=bad)


def test_the_ratio_is_one_number():
    w = jerlov.water("III")
    for bad in ([0.01, 0.02], np.array([0.01, 0.02]), []):
        with pytest.raises(ValueError, match="single number"):
            w.bb(550.0, particle_backscatter_ratio=bad)


def test_the_wavelength_is_checked_as_for_b():
    w = jerlov.water("III", source="solonenko2015")
    with pytest.raises(ValueError, match="NaN"):
        w.bb(np.nan, particle_backscatter_ratio=0.01)
    for outside in (299.0, 701.0, np.inf):
        with pytest.raises(ValueError):
            w.bb(outside, particle_backscatter_ratio=0.01)


def test_a_measured_water_is_refused():
    m = jerlov.Water.from_measurements([400.0, 500.0],
                                       a=[0.1, 0.1], b=[0.2, 0.2])
    with pytest.raises(MissingQuantityError, match="section 68"):
        m.bb(450.0, particle_backscatter_ratio=0.01)
    assert m.bb(450.0, backscatter_ratio=0.01) == pytest.approx(0.002)


def test_a_water_without_b_says_so():
    k = jerlov.water("II", source="jerlov1976")
    with pytest.raises(MissingQuantityError, match="'b' is not available"):
        k.bb(450.0, particle_backscatter_ratio=0.01)


def test_flagged_values_still_warn():
    w = jerlov.water("I", source="solonenko2015")
    with pytest.warns(ProvenanceWarning, match="suspect"):
        w.bb(450.0, particle_backscatter_ratio=0.0183)

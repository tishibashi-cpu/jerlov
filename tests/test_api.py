"""Behaviour that keeps a doubtful number from looking like a sound one."""

from __future__ import annotations

import warnings

import numpy as np
import pytest

import jerlov
from jerlov import MissingQuantityError, ProvenanceWarning, Water


def test_default_source_is_the_measured_one():
    w = jerlov.water("III")
    assert w.source.key == "williamson2022"
    assert w.source.measured is True


def test_unknown_type_for_a_source_names_the_alternatives():
    with pytest.raises(KeyError, match="IB, II, III"):
        jerlov.water("I", source="williamson2022")


def test_solonenko_covers_all_ten_types():
    for water_type in ("I", "IA", "IB", "II", "III", "1C", "3C", "5C", "7C", "9C"):
        w = jerlov.water(water_type, source="solonenko2015")
        assert w.has("a") and w.has("b") and w.has("Kd")


def test_no_extrapolation():
    w = jerlov.water("III")
    lo, hi = w.range_nm
    for outside in (lo - 1, hi + 1):
        with pytest.raises(ValueError, match="does not extrapolate"):
            w.a(outside)


def test_bb_requires_an_explicit_ratio():
    w = jerlov.water("5C")
    with pytest.raises(MissingQuantityError, match="not determined by the water type"):
        w.bb(550)
    assert w.bb(550, backscatter_ratio=0.02) == pytest.approx(
        w.b(550) * 0.02
    )


def test_bb_ratio_must_be_plausible():
    w = jerlov.water("5C")
    for bad in (0.0, -0.01, 0.9):
        with pytest.raises(ValueError):
            w.bb(550, backscatter_ratio=bad)


def test_missing_values_stay_missing():
    """3C has no absorption at 675 nm; interpolation must not paper over it."""
    w = jerlov.water("3C", source="solonenko2015")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ProvenanceWarning)
        assert np.isnan(w.a(675)).all()
        assert np.isnan(w.a(690)).all()  # between two unusable samples
        assert np.isfinite(w.a(600)).all()


def test_flagged_wavelengths_warn():
    """Jerlov IA's b is inconsistent with its own Table 3; see README 4."""
    w = jerlov.water("IA", source="solonenko2015")
    with pytest.warns(ProvenanceWarning, match="suspect"):
        w.b(550)


def test_reconstructed_values_warn():
    w = jerlov.water("5C", source="solonenko2015")
    with pytest.warns(ProvenanceWarning, match="reconstructed"):
        w.b(650)


def test_sound_wavelengths_do_not_warn():
    w = jerlov.water("9C", source="solonenko2015")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        w.a(500)


def test_caveats_are_reported():
    w = jerlov.water("5C", source="solonenko2015")
    text = " ".join(w.caveats())
    assert "inverting Kd" in text
    assert "missing" in text


def test_user_measurements_take_the_same_path():
    wl = np.array([450.0, 500.0, 550.0])
    w = Water.from_measurements(wl, a=[0.05, 0.04, 0.06], b=[0.3, 0.29, 0.28])
    assert w.source is None
    assert w.c(500) == pytest.approx(0.33)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        w.a(475)


def test_wavelengths_must_ascend():
    with pytest.raises(ValueError, match="ascending"):
        Water([550.0, 450.0], a=[0.1, 0.2])


def test_kd_spectrum_reproduces_austin_table6():
    """Anchoring at Jerlov's K(475) must give back the published row."""
    from jerlov import _data

    wl, kd, _ = _data.spectrum(
        "austin1986_kd.csv", "II", None, "Kd_downwelling_per_m"
    )
    k475 = float(kd[np.where(wl == 475)[0][0]])
    predicted = jerlov.kd_spectrum(k475, 475, wl)
    assert np.max(np.abs(100 * (predicted - kd) / kd)) < 0.5


def test_kd_spectrum_warns_below_pure_sea_water():
    with pytest.warns(ProvenanceWarning, match="pure sea water"):
        jerlov.kd_spectrum(0.001, 550, 600)


def test_kd_spectrum_refuses_outside_its_range():
    with pytest.raises(ValueError, match="model range"):
        jerlov.kd_spectrum(0.05, 475, 800)


def test_b_from_c_matches_the_ratio_table():
    """Smart (2007): b = (c - cw) * ratio + bw."""
    bw, cw = 0.0019, 0.0659
    c = 0.5
    b = jerlov.b_from_c(c, 555, bw=bw, cw=cw)
    assert b == pytest.approx((c - cw) * 0.904 + bw, rel=1e-6)

    lower = jerlov.b_from_c(c, 555, bw=bw, cw=cw, bound="min")
    upper = jerlov.b_from_c(c, 555, bw=bw, cw=cw, bound="max")
    assert lower < b < upper


def test_sources_are_described():
    for key, source in jerlov.SOURCES.items():
        assert source.key == key
        assert source.citation
        assert source.water_types
        if key != "jerlov1976":
            assert source.doi

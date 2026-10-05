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
    """Jerlov IA's b is inconsistent with its own Table 3; see DATA.md section 4."""
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
    # Table VI starts at 350 nm, where the paper itself flags M as
    # extrapolated, so reproducing it must say so.
    with pytest.warns(ProvenanceWarning, match="extrapolated at 350 nm"):
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


# -- scalar in, scalar out -----------------------------------------------


def test_a_scalar_wavelength_gives_a_scalar():
    """numpy.interp behaves this way, and float(w.a(550)) must work."""
    w = jerlov.water("III")
    for value in (w.a(550), w.b(550), w.c(550),
                  w.bb(550, backscatter_ratio=0.02)):
        assert isinstance(value, float)
        assert not isinstance(value, np.ndarray)
    assert float(w.a(550)) == w.a(550)


def test_an_array_of_wavelengths_gives_an_array():
    w = jerlov.water("III")
    out = w.a([450.0, 550.0])
    assert isinstance(out, np.ndarray)
    assert out.shape == (2,)
    # A one-element list is still a sequence, so it stays an array.
    assert jerlov.water("III").a([550.0]).shape == (1,)


def test_the_other_entry_points_follow_the_same_rule():
    assert isinstance(jerlov.kd_spectrum(0.06, 490, 550), float)
    assert isinstance(jerlov.kd_spectrum(0.06, 490, [440.0, 550.0]), np.ndarray)
    assert isinstance(
        jerlov.b_from_c(0.5, 555, bw=0.0019, cw=0.0659), float
    )
    assert isinstance(
        jerlov.b_from_c(0.5, [510.0, 555.0], bw=0.0019, cw=0.0659), np.ndarray
    )


def test_a_missing_value_is_nan_whether_scalar_or_array():
    w = jerlov.water("3C", source="solonenko2015")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ProvenanceWarning)
        assert np.isnan(w.a(675))
        assert np.isnan(w.a([675.0])).all()


# -- landing exactly on a sample -----------------------------------------


def test_an_exact_hit_survives_a_missing_neighbour():
    """A query on a sample is not interpolated, so a gap beside it is not its
    problem. Found by checking the shipped 1976 file against the printed
    table: Jerlov 7C has no data below 350 nm, and kd(350) was returning nan
    although 350 nm itself is tabulated.
    """
    w = jerlov.water("7C", source="jerlov1976")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ProvenanceWarning)
        assert w.kd(350.0) == pytest.approx(3.0)
        assert np.isnan(w.kd(349.0))      # inside the gap, still nan
        assert np.isnan(w.kd(348.0))


def test_interpolating_across_a_gap_still_gives_nan():
    """The guard this rests on must not have been loosened."""
    w = jerlov.water("5C", source="solonenko2015")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ProvenanceWarning)
        assert np.isnan(w.a(650))          # a published value that is wrong
        assert np.isnan(w.a(660))          # and interpolation across it
        assert np.isnan(w.a(675))


def test_b_from_c_keeps_every_c_at_a_single_wavelength():
    """An array of c at one wavelength used to come back as its first value."""
    c = np.array([0.5, 1.0, 2.0])
    out = jerlov.b_from_c(c, 488.0, bw=0.003, cw=0.02)
    assert out.shape == (3,)
    for value, single in zip(out, c):
        assert value == pytest.approx(
            jerlov.b_from_c(float(single), 488.0, bw=0.003, cw=0.02)
        )
    assert isinstance(jerlov.b_from_c(0.5, 488.0, bw=0.003, cw=0.02), float)


def test_a_returned_water_cannot_corrupt_the_packaged_table():
    """The loaders are cached; a caller's in-place edit must stay local."""
    w = jerlov.water("III")
    before = jerlov.water("III").wavelengths.copy()
    w.wavelengths *= 2.0
    assert np.array_equal(jerlov.water("III").wavelengths, before)


def test_the_cached_tables_are_read_only():
    from jerlov import _data

    wl, m, kw = _data.austin_model()
    with pytest.raises(ValueError):
        wl[0] = 0.0
    wl, values, _ = _data.spectrum(
        "williamson2022_iop.csv", "III", "a", "value_per_m"
    )
    with pytest.raises(ValueError):
        values[0] = 0.0


def test_measurements_are_copied_not_shared():
    wl = np.array([400.0, 500.0, 600.0])
    a = np.array([0.1, 0.2, 0.3])
    mine = Water.from_measurements(wl, a=a)
    a[1] = 99.0
    assert mine.a(500.0) == pytest.approx(0.2)


@pytest.mark.parametrize("method", ["kd", "c"])
def test_a_provenance_warning_points_at_the_callers_line(method):
    """Not at water.py: `c` reaches the check one frame deeper than `kd`."""
    source = "jerlov1976" if method == "kd" else "williamson2022"
    w = jerlov.water("9C" if method == "kd" else "III", source=source)
    query = 349.5 if method == "kd" else 305.0
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        getattr(w, method)(query)
    flagged = [c for c in caught if issubclass(c.category, ProvenanceWarning)]
    assert flagged
    assert all(c.filename == __file__ for c in flagged)


def test_a_flag_on_a_neighbour_does_not_warn_at_an_exact_sample():
    """350 nm is sound; only 349 nm is missing. The answer at 350 rests on
    350 alone, as the NaN check already knew."""
    w = jerlov.water("9C", source="jerlov1976")
    with warnings.catch_warnings():
        warnings.simplefilter("error", ProvenanceWarning)
        assert np.isfinite(w.kd(350.0))
    with pytest.warns(ProvenanceWarning, match="missing at 349 nm"):
        w.kd(349.5)


def test_kd_spectrum_takes_several_measurements_at_once():
    kd = np.array([0.03, 0.06, 0.1])
    at = np.array([440.0, 550.0, 650.0])
    together = jerlov.kd_spectrum(kd, 490, at)
    assert together.shape == (3, 3)
    for row, single in zip(together, kd):
        assert np.allclose(row, jerlov.kd_spectrum(float(single), 490, at))
    at_one = jerlov.kd_spectrum(kd, 490, 550.0)
    assert at_one.shape == (3,)
    assert np.allclose(at_one, together[:, 1])


def test_kd_spectrum_wants_one_measurement_wavelength():
    with pytest.raises(ValueError, match="single wavelength"):
        jerlov.kd_spectrum(0.06, [490, 500], 550)


def test_kd_spectrum_warns_outside_the_fitted_range():
    """Austin & Petzold: the model holds for K(490) < 0.16 1/m."""
    with pytest.warns(ProvenanceWarning, match="0.16"):
        jerlov.kd_spectrum(0.2, 490, 550)
    # Measured elsewhere, the K(490) the model implies is what counts.
    with pytest.warns(ProvenanceWarning, match="implied by the model"):
        jerlov.kd_spectrum(0.3, 440, 550)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ProvenanceWarning)
        jerlov.kd_spectrum(0.15, 490, 550)


def test_kd_spectrum_warns_where_m_is_extrapolated():
    with pytest.warns(ProvenanceWarning, match="extrapolated at 355 nm"):
        jerlov.kd_spectrum(0.06, 490, 355.0)
    with pytest.warns(ProvenanceWarning, match="extrapolated at 360 nm"):
        jerlov.kd_spectrum(0.06, 490, 362.0)
    # 365 nm is the first sound value of M, and rests on it alone.
    with warnings.catch_warnings():
        warnings.simplefilter("error", ProvenanceWarning)
        jerlov.kd_spectrum(0.06, 490, [365.0, 550.0])

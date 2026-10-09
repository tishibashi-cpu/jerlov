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
        # Jerlov's books predate DOIs; everything else must carry one.
        if key not in ("jerlov1968", "jerlov1976"):
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


def test_wavelengths_must_be_finite():
    """NaN passed the ascending check, because every comparison with it is
    False, and broke interpolation afterwards."""
    with pytest.raises(ValueError, match="finite"):
        Water([400.0, float("nan"), 600.0], a=[0.1, 0.2, 0.3])


def test_flags_must_cover_every_wavelength():
    """Too few used to surface as IndexError when a value was asked for."""
    with pytest.raises(ValueError, match="one per wavelength"):
        Water([400.0, 500.0, 600.0], a=[0.1, 0.2, 0.3], flags={"a": ("ok",)})


def test_flags_for_a_quantity_the_water_lacks_are_refused():
    """They used to be kept and never consulted, so the doubt they recorded
    was lost without a word; "kd" for "Kd" was lost the same way."""
    with pytest.raises(ValueError, match="flags given for 'b'.*it has a"):
        Water([400.0, 500.0], a=[0.1, 0.2], flags={"b": ("suspect", "ok")})
    with pytest.raises(ValueError, match="flags given for 'kd'"):
        Water([400.0, 500.0], kd=[0.1, 0.2], flags={"kd": ("suspect", "ok")})


def test_b_from_c_warns_when_c_is_below_pure_water():
    """b came out negative without a word; kd_spectrum already warned in the
    same situation."""
    with pytest.warns(ProvenanceWarning, match="below the pure water value"):
        jerlov.b_from_c(0.01, 555.0, bw=0.0019, cw=0.0659)
    # cw may be given per wavelength; the warning must not trip over that.
    with pytest.warns(ProvenanceWarning, match="below the pure water value"):
        jerlov.b_from_c(0.01, [532.0, 555.0], bw=np.array([0.0024, 0.0019]),
                        cw=np.array([0.0545, 0.0659]))
    with warnings.catch_warnings():
        warnings.simplefilter("error", ProvenanceWarning)
        jerlov.b_from_c(0.5, 555.0, bw=0.0019, cw=0.0659)


# -- tables that were shipped but not reachable ----------------------------


def test_the_first_edition_is_a_kd_source():
    """jerlov1968_kd.csv was shipped and checked but only reachable through a
    private loader. It is the Kd0 column of Solonenko & Mobley."""
    w = jerlov.water("III", source="jerlov1968")
    assert w.source.key == "jerlov1968"
    assert w.range_nm == (310.0, 700.0)
    assert w.has("Kd") and not w.has("a")
    # Jerlov printed transmittance per metre; Kd is -ln of it.
    assert w.kd(475.0) == pytest.approx(-np.log(0.89), abs=5e-4)
    # Kd0 of Solonenko & Mobley is this table.
    from jerlov import _data
    wl, kd0, _ = _data.spectrum("solonenko2015_iop.csv", "III", "Kd0",
                                "value_per_m")
    inside = (wl >= 350) & (wl <= 700)
    assert np.allclose(w.kd(wl[inside]), kd0[inside], rtol=0.01)


def test_the_first_edition_keeps_its_gaps():
    w = jerlov.water("7C", source="jerlov1968")
    with pytest.warns(ProvenanceWarning, match="missing at 310 nm"):
        assert np.isnan(w.kd(310.0))


def test_measured_points_follow_the_papers_filter():
    for quantity in ("a", "b"):
        total = sum(
            len(jerlov.measured_points(t, quantity).values)
            for t in ("IB", "II", "III", "1C", "3C", "5C")
        )
        assert total == 53
    m = jerlov.measured_points("III", "a")
    assert np.all(m.included) and np.all(m.n_campaigns >= 5)
    assert np.all(np.diff(m.wavelengths) > 0)
    assert 412 <= m.wavelengths[0] and m.wavelengths[-1] <= 715


def test_measured_points_refuse_a_type_with_none_kept():
    with pytest.raises(KeyError, match="include_sparse=True"):
        jerlov.measured_points("IA", "a")
    sparse = jerlov.measured_points("IA", "a", include_sparse=True)
    assert len(sparse.values) > 0 and not np.any(sparse.included)


def test_measured_points_sit_near_the_fitted_spectrum():
    """The smooth spectra were fitted to these points."""
    m = jerlov.measured_points("III", "b")
    fitted = jerlov.water("III").b(m.wavelengths)
    assert np.max(np.abs(fitted - m.values) / m.values) < 0.25


def test_measured_points_name_bad_arguments():
    with pytest.raises(ValueError, match="'a' or 'b'"):
        jerlov.measured_points("III", "Kd")
    with pytest.raises(KeyError, match="known:"):
        jerlov.measured_points("I", "a")


def test_kd_hydrolight_is_the_papers_third_kd_column():
    """Solonenko & Mobley Tables 4-8, K_d^H, read off the printed page."""
    printed = {("I", 300): 0.200, ("III", 475): 0.101, ("1C", 700): 0.688,
               ("9C", 300): 7.066, ("IB", 550): 0.072}
    for (t, nm), value in printed.items():
        w = jerlov.water(t, source="solonenko2015")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ProvenanceWarning)
            assert w.kd_hydrolight(nm) == pytest.approx(value)
    # It is a different quantity from .kd(), not a copy of it.
    w = jerlov.water("III", source="solonenko2015")
    assert w.kd(475.0) == pytest.approx(0.110)
    assert w.kd_hydrolight(475.0) != w.kd(475.0)


def test_kd_hydrolight_keeps_the_unrecoverable_cells_missing():
    w = jerlov.water("5C", source="solonenko2015")
    with pytest.warns(ProvenanceWarning, match="missing at 650 nm"):
        assert np.isnan(w.kd_hydrolight(650.0))


def test_only_solonenko_has_kd_hydrolight():
    for source in ("williamson2022", "jerlov1976", "jerlov1968", "austin1986"):
        t = jerlov.SOURCES[source].water_types[0]
        with pytest.raises(MissingQuantityError, match="'KdH'"):
            jerlov.water(t, source=source).kd_hydrolight(500.0)


# -- what Jerlov printed, and what the dataset filled in ------------------


def test_jerlov1976_marks_what_jerlov_did_not_print():
    """Jerlov printed 310-700 nm at 16 wavelengths. Until 0.5.2 the 1 nm
    values the Dstl file filled in, including 230 linear extrapolations
    beyond that range, were all marked ok. DATA.md section 16."""
    from collections import Counter
    from jerlov import _data
    counts = Counter(r["status"] for r in _data._rows("jerlov1976_kd.csv"))
    assert counts == {"ok": 158, "interpolated": 3672,
                      "extrapolated_by_dataset": 230, "missing": 100}
    for t in ("I", "III", "9C"):
        wl, _, st = _data.spectrum("jerlov1976_kd.csv", t, None,
                                   "Kd_downwelling_per_m")
        status = dict(zip(wl, st))
        assert status[475.0] == "ok" and status[480.0] == "interpolated"
        assert status[701.0] == status[715.0] == "extrapolated_by_dataset"


def test_an_extrapolated_jerlov1976_value_warns_and_the_rest_do_not():
    w = jerlov.water("I", source="jerlov1976")
    with pytest.warns(ProvenanceWarning, match="extrapolated_by_dataset"):
        w.kd(305.0)
    with pytest.warns(ProvenanceWarning, match="extrapolated_by_dataset"):
        w.kd(710.0)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ProvenanceWarning)
        w.kd(310.0)                       # printed
        w.kd(480.0)                       # interpolated
        w.kd(np.arange(310.0, 701.0))     # everything Jerlov's table spans
    # 300-309 and 701-715 nm: ten below, fifteen above.
    assert "Kd: 25 wavelength(s) marked 'extrapolated_by_dataset'" in w.caveats()


# -- pure water absorption -------------------------------------------------

@pytest.mark.filterwarnings("ignore::jerlov.ProvenanceWarning")
def test_pure_water_absorption_is_the_one_williamson2022_built_a_on():
    """From 720 nm their model leaves only water; a is aw there."""
    for t in ("IB", "III", "5C"):
        w = jerlov.water(t)
        for wl in (720.0, 760.0, 800.0):
            assert w.a(wl) == pytest.approx(
                jerlov.pure_water_absorption(wl), rel=0.005)


@pytest.mark.filterwarnings("ignore::jerlov.ProvenanceWarning")
def test_pure_water_absorption_never_exceeds_a():
    wl = np.arange(300.0, 801.0)
    aw = jerlov.pure_water_absorption(wl)
    for t in jerlov.get_source("williamson2022").water_types:
        assert np.all(aw <= jerlov.water(t).a(wl) * 1.005)


def test_pure_water_absorption_scalar_in_scalar_out():
    assert isinstance(jerlov.pure_water_absorption(440), float)
    assert jerlov.pure_water_absorption(440) == pytest.approx(0.0104)


def test_sources_without_pure_water_absorption_say_why():
    with pytest.raises(MissingQuantityError, match="Fig. 2"):
        jerlov.pure_water_absorption(500, source="solonenko2015")
    with pytest.raises(MissingQuantityError, match="not its absorption"):
        jerlov.pure_water_absorption(500, source="austin1986")
    for key in ("jerlov1976", "jerlov1968"):
        with pytest.raises(MissingQuantityError, match="Kd only"):
            jerlov.pure_water_absorption(500, source=key)
    with pytest.raises(KeyError, match="known sources"):
        jerlov.pure_water_absorption(500, source="pope1997")


def test_pure_water_absorption_does_not_extrapolate():
    for wl in (299.0, 801.0):
        with pytest.raises(ValueError, match="does not extrapolate"):
            jerlov.pure_water_absorption(wl)
    with pytest.raises(ValueError, match="NaN"):
        jerlov.pure_water_absorption(float("nan"))


# -- the caller's own flags and uncertainty --------------------------------

def _station(**kwargs):
    return Water.from_measurements(
        [400.0, 500.0, 600.0], a=[0.10, 0.05, 0.30], b=[0.20, 0.18, 0.15],
        name="station 4", **kwargs)


def test_a_flag_on_a_measurement_warns_like_a_published_one():
    w = _station(flags={"a": ["ok", "suspect", "ok"]})
    with pytest.warns(ProvenanceWarning, match="'station 4'.*suspect at 500"):
        w.a(450)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        w.a(400)
        w.b(450)
    assert "a: 1 wavelength(s) marked 'suspect'" in w.caveats()


def test_a_misspelt_flag_is_refused_rather_than_never_warning():
    with pytest.raises(ValueError, match="unknown status 'suspcet'"):
        _station(flags={"a": ["ok", "suspcet", "ok"]})


def test_flags_must_match_a_given_quantity_and_the_grid():
    with pytest.raises(ValueError, match="expected one of"):
        _station(flags={"c": ["ok"] * 3})
    with pytest.raises(ValueError, match="no Kd values"):
        _station(flags={"kd": ["ok"] * 3})
    with pytest.raises(ValueError, match="one per wavelength"):
        _station(flags={"a": ["ok"] * 2})


def test_uncertainty_is_interpolated_like_the_values():
    w = _station(uncertainty={"a": [0.01, 0.02, np.nan]})
    assert w.uncertainty("a", 450) == pytest.approx(0.015)
    assert np.isnan(w.uncertainty("a", 550))
    with pytest.raises(MissingQuantityError, match="'b'"):
        w.uncertainty("b", 450)


def test_uncertainty_is_refused_where_it_cannot_be_right():
    with pytest.raises(ValueError, match="negative"):
        _station(uncertainty={"a": [0.01, -0.02, 0.01]})
    with pytest.raises(ValueError, match="same shape"):
        _station(uncertainty={"b": [0.01]})
    with pytest.raises(ValueError, match="does not carry"):
        Water.from_measurements([400.0, 500.0], a=[0.1, 0.2],
                                uncertainty={"b": [0.01, 0.01]})


def test_published_sources_have_no_uncertainty_to_give():
    with pytest.raises(MissingQuantityError, match="publishes none"):
        jerlov.water("III").uncertainty("a", 500)


def test_c_warns_once_for_a_wavelength_flagged_in_both_a_and_b():
    """Solonenko 3C at 675 nm: a missing and b reconstructed, one warning."""
    w = jerlov.water("3C", source="solonenko2015")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        w.c(675)
    messages = [str(x.message) for x in caught
                if issubclass(x.category, ProvenanceWarning)]
    assert len(messages) == 1
    assert messages[0].startswith("c for Jerlov 3C")
    assert "a missing at 675 nm" in messages[0]
    assert "b reconstructed at 675 nm" in messages[0]


# -- 0.7.2: inputs that slipped through -------------------------------------

@pytest.mark.parametrize("call", [
    lambda: jerlov.water("III").a(float("nan")),
    lambda: jerlov.water("III").c([500.0, float("nan")]),
    lambda: jerlov.water("I", source="jerlov1976").kd(float("nan")),
    lambda: jerlov.water("III", source="solonenko2015").kd_hydrolight(
        float("nan")),
    lambda: jerlov.kd_spectrum(0.06, 490.0, float("nan")),
    lambda: jerlov.kd_spectrum(0.06, float("nan"), 500.0),
    lambda: jerlov.b_from_c(0.5, float("nan"), bw=0.002, cw=0.066),
])
def test_a_wavelength_that_is_not_a_number_is_refused(call):
    """NaN < lo is False, so NaN passed the range check, came back as NaN,
    and warned about the last sample of the table instead."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")         # and no misleading warning
        with pytest.raises(ValueError, match="NaN"):
            call()


def test_descend_leaves_the_callers_array_alone():
    wl = np.array([450.0, 550.0])
    d = jerlov.descend("II", 30.0, wl)
    assert wl.flags.writeable
    wl[0] = 999.0
    assert d.wavelengths[0] == 450.0
    assert not d.wavelengths.flags.writeable

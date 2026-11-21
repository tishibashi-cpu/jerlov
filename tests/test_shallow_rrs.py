"""The remote sensing reflectance of shallow water, Lee et al. (1998, 1999):
DECISIONS.md section 113, DATA.md section 50."""

from __future__ import annotations

import csv
import math
import pathlib
import pickle
import sys
import warnings

import numpy as np
import pytest

import jerlov

ROOT = pathlib.Path(__file__).resolve().parent.parent
MC = ROOT / "examples" / "data" / "shallow_rrs_mc" / "monte_carlo.csv"
source_tree = pytest.mark.skipif(
    not (ROOT / "pyproject.toml").exists(),
    reason="not running from a source tree")


def _quiet(*args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        return jerlov.lee1999_shallow_rrs(*args, **kwargs)


def _by_hand(a, bb, depth, rho, sun, constants="1999"):
    """Eqs. (A6), (A7) and (A9) of the 1999 paper, or Eqs. (21) and (25) of
    the 1998 paper, written out again."""
    u = bb / (a + bb)
    kappa = a + bb
    mu = math.sqrt(1.0 - (math.sin(math.radians(sun)) / 1.34) ** 2)
    if constants == "1999":
        deep = (0.084 + 0.170 * u) * u
        a0, a1 = 1.0, 1.0 / math.pi
        dc = 1.03 * math.sqrt(1 + 2.4 * u)
        db = 1.04 * math.sqrt(1 + 5.4 * u)
        zeta, gamma = 0.5, 1.5
    else:
        deep = (0.070 + 0.155 * u ** 0.752) * u
        a0, a1 = 1.03, 0.31
        dc = 1.2 * math.sqrt(1 + 2.0 * u)
        db = 1.1 * math.sqrt(1 + 4.9 * u)
        zeta, gamma = 0.518, 1.562
    column = deep * (1 - a0 * math.exp(-(1 / mu + dc) * kappa * depth))
    bottom = a1 * rho * math.exp(-(1 / mu + db) * kappa * depth)
    rrs = column + bottom
    return rrs, column, bottom, deep, zeta * rrs / (1 - gamma * rrs)


# -- the equations ------------------------------------------------------------

@pytest.mark.parametrize("a, bb, depth, rho, sun", [
    (0.1, 0.01, 5.0, 0.3, 30.0),
    (0.05, 0.002, 2.0, 1.0, 0.0),
    (0.8, 0.2, 10.0, 0.1, 60.0),
    (0.3, 0.0015, 0.5, 0.0, 45.0),
])
def test_every_field_is_the_equations(a, bb, depth, rho, sun):
    got = jerlov.lee1999_shallow_rrs(a, bb, depth_m=depth, bottom_albedo=rho,
                                     sun_zenith_deg=sun)
    want = _by_hand(a, bb, depth, rho, sun)
    for field, value in zip(("rrs", "column", "bottom", "deep",
                             "above_surface"), want):
        assert getattr(got, field) == pytest.approx(value, rel=1e-12)
        assert isinstance(getattr(got, field), float)


def test_a_shallow_bright_bottom_in_clear_water_is_rho_over_pi():
    # With u -> 0, rho = 1 and H -> 0 the 1999 model gives rrs = 1/pi and
    # Rrs = 0.5/pi / (1 - 1.5/pi) = 0.3046; the 1998 paper's own check
    # with its constants gave 0.31 for both (p. 6336).
    got = _quiet(1e-9, 1e-12, depth_m=1e-9, bottom_albedo=1.0,
                 sun_zenith_deg=0.0)
    assert got.rrs == pytest.approx(1 / math.pi, rel=1e-6)
    assert got.above_surface == pytest.approx(
        0.5 / math.pi / (1 - 1.5 / math.pi), rel=1e-6)
    assert round(got.above_surface, 4) == 0.3046
    old = _by_hand(1e-9, 1e-12, 1e-9, 1.0, 0.0, constants="1998")
    assert round(old[0], 2) == 0.31 and round(old[4], 2) == 0.31


def test_a_deep_bottom_leaves_the_deep_water():
    got = _quiet(0.2, 0.01, depth_m=500.0, bottom_albedo=1.0,
                 sun_zenith_deg=30.0)
    assert got.bottom < 1e-30
    assert got.rrs == pytest.approx(got.deep, rel=1e-12)
    assert got.deep == pytest.approx(
        jerlov.lee1999_shallow_rrs(0.2, 0.01, depth_m=5.0, bottom_albedo=0.0,
                                   sun_zenith_deg=0.0).deep)


def test_the_bottom_s_share_falls_with_depth_and_rises_with_albedo():
    depths = np.linspace(0.5, 30.0, 60)
    r = _quiet(0.06, 0.003, depth_m=depths, bottom_albedo=0.3,
               sun_zenith_deg=30.0)
    share = r.bottom / r.rrs
    assert np.all(np.diff(share) < 0)
    albedos = np.linspace(0.0, 1.0, 11)
    r = jerlov.lee1999_shallow_rrs(0.06, 0.003, depth_m=5.0,
                                   bottom_albedo=albedos, sun_zenith_deg=30.0)
    assert np.all(np.diff(r.rrs) > 0)
    assert np.all(np.diff(r.column) == 0)


def test_with_no_bottom_reflection_shallow_water_is_darker_than_deep():
    r = jerlov.lee1999_shallow_rrs(0.1, 0.01, depth_m=np.array([1.0, 5.0]),
                                   bottom_albedo=0.0, sun_zenith_deg=30.0)
    assert np.all(r.rrs < r.deep)
    assert r.rrs[0] < r.rrs[1]


# -- shapes, gaps, results ----------------------------------------------------

def test_inputs_broadcast_and_nan_marks_a_gap():
    a = np.array([0.05, 0.1, np.nan])
    depth = np.array([[2.0], [5.0]])
    r = jerlov.lee1999_shallow_rrs(a, 0.004, depth_m=depth,
                                   bottom_albedo=0.3, sun_zenith_deg=30.0)
    for field in ("rrs", "column", "bottom", "deep", "above_surface"):
        value = getattr(r, field)
        assert value.shape == (2, 3)
        assert np.all(np.isnan(value[:, 2]))
        assert np.all(np.isfinite(value[:, :2]))
    assert r.rrs[1, 0] == pytest.approx(
        _by_hand(0.05, 0.004, 5.0, 0.3, 30.0)[0], rel=1e-12)


def test_the_caller_s_arrays_are_not_touched_or_shared():
    a = np.array([0.05, 0.1])
    bb = np.array([0.002, 0.004])
    before = (a.copy(), bb.copy())
    r = jerlov.lee1999_shallow_rrs(a, bb, depth_m=3.0, bottom_albedo=0.3,
                                   sun_zenith_deg=30.0)
    assert np.array_equal(a, before[0]) and np.array_equal(bb, before[1])
    r.rrs[0] = 99.0
    assert not np.shares_memory(r.rrs, r.column)


def test_results_compare_by_value_and_pickle():
    one = jerlov.lee1999_shallow_rrs(np.array([0.05, np.nan]), 0.002,
                                     depth_m=3.0, bottom_albedo=0.3,
                                     sun_zenith_deg=30.0)
    two = jerlov.lee1999_shallow_rrs(np.array([0.05, np.nan]), 0.002,
                                     depth_m=3.0, bottom_albedo=0.3,
                                     sun_zenith_deg=30.0)
    assert one == two and hash(one) == hash(two)
    assert pickle.loads(pickle.dumps(one)) == one
    assert one != jerlov.lee1999_shallow_rrs(
        np.array([0.05, np.nan]), 0.002, depth_m=4.0, bottom_albedo=0.3,
        sun_zenith_deg=30.0)


def test_a_and_bb_are_positional_and_the_rest_keywords():
    with pytest.raises(TypeError):
        jerlov.lee1999_shallow_rrs(0.1, 0.01, 5.0, 0.3, 30.0)
    with pytest.raises(TypeError):
        jerlov.lee1999_shallow_rrs(0.1, 0.01, depth_m=5.0, bottom_albedo=0.3)


# -- refusals and warnings ----------------------------------------------------

@pytest.mark.parametrize("change", [
    {"depth_m": 0.0}, {"depth_m": -1.0}, {"depth_m": math.inf},
    {"depth_m": math.nan},
    {"bottom_albedo": -0.01}, {"bottom_albedo": 1.01},
    {"bottom_albedo": math.nan}, {"bottom_albedo": math.inf},
    {"sun_zenith_deg": -1.0}, {"sun_zenith_deg": 90.0},
    {"sun_zenith_deg": math.nan},
])
def test_refused(change):
    kwargs = {"depth_m": 5.0, "bottom_albedo": 0.3, "sun_zenith_deg": 30.0}
    kwargs.update(change)
    with pytest.raises(ValueError):
        jerlov.lee1999_shallow_rrs(0.1, 0.01, **kwargs)


@pytest.mark.parametrize("a, bb", [(0.0, 0.01), (0.1, 0.0), (-0.1, 0.01),
                                   (math.inf, 0.01), (0.1, math.inf)])
def test_iops_refused(a, bb):
    with pytest.raises(ValueError):
        jerlov.lee1999_shallow_rrs(a, bb, depth_m=5.0, bottom_albedo=0.3,
                                   sun_zenith_deg=30.0)


@pytest.mark.parametrize("a, bb, depth, sun, words", [
    (0.1, 0.01, 5.0, 61.0, "60 degrees"),
    (0.1, 0.01, 0.4, 30.0, "0.5 to 32 m"),
    (0.1, 0.01, 33.0, 30.0, "0.5 to 32 m"),
    (0.1, 0.16, 5.0, 30.0, "above 0.6"),
])
def test_outside_the_runs_warns(a, bb, depth, sun, words):
    with pytest.warns(jerlov.ProvenanceWarning, match=words) as caught:
        jerlov.lee1999_shallow_rrs(a, bb, depth_m=depth, bottom_albedo=0.3,
                                   sun_zenith_deg=sun)
    assert caught[0].filename == __file__


def test_inside_the_runs_is_quiet():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        jerlov.lee1999_shallow_rrs(
            np.array([0.02, 0.5, 2.0, np.nan]), np.array([0.001, 0.05, 1.0, 0.1]),
            depth_m=np.array([0.5, 3.0, 32.0, 10.0]), bottom_albedo=1.0,
            sun_zenith_deg=60.0)


# -- the Monte Carlo (DATA.md section 50) -------------------------------------

def _mc_rows():
    with MC.open() as f:
        rows = list(csv.DictReader(f))
    out = {k: np.array([float(r[k]) for r in rows])
           for k in ("a", "bp", "bw", "bb", "u", "depth_m", "albedo",
                     "sun_deg", "monte_carlo", "standard_error", "model")}
    return out


@source_tree
def test_the_monte_carlo_checks_itself():
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import shallow_rrs_mc
    finally:
        sys.path.pop(0)
    for key, value in shallow_rrs_mc.check().items():
        if isinstance(key, tuple):
            assert value == pytest.approx(1.0, abs=0.01), key
        else:
            assert value < 1e-12, key


@source_tree
def test_the_stored_model_column_is_today_s_function():
    r = _mc_rows()
    for i in range(len(r["a"])):
        depth = r["depth_m"][i]
        got = _quiet(r["a"][i], r["bb"][i],
                     depth_m=depth if math.isfinite(depth) else 1.0,
                     bottom_albedo=r["albedo"][i],
                     sun_zenith_deg=r["sun_deg"][i])
        want = got.rrs if math.isfinite(depth) else got.deep
        assert r["model"][i] == pytest.approx(want, rel=2e-5)  # bb has 6 digits


@source_tree
def test_the_figures_data_md_quotes():
    r = _mc_rows()
    text = " ".join((ROOT / "DATA.md").read_text().split())
    q = r["model"] / r["monte_carlo"]
    ratio = r["bp"] / r["a"]
    shallow = np.isfinite(r["depth_m"])
    within = np.abs(q - 1) <= 0.1
    assert q.size == 270
    assert f"u {r['u'].min():.3f} to {r['u'].max():.3f}" in text
    rel = r["standard_error"] / r["monte_carlo"]
    assert (f"{100 * np.median(rel):.1f} percent in the median run and "
            f"{100 * rel.max():.1f} percent at the worst") in text
    assert f"median {np.median(q):.3f}, within 10 percent in " \
           f"{100 * within.mean():.1f} percent of the runs and within 5 " \
           f"percent in {100 * np.mean(np.abs(q - 1) <= 0.05):.1f}" in text
    assert np.median(q) == pytest.approx(1.0, abs=0.05)
    assert within.mean() < 0.9          # the criterion missed, as stated
    counts = [(int(within[m].sum()), int(m.sum())) for m in (
        shallow & (r["albedo"] == 0.3), shallow & (r["albedo"] == 1.0),
        shallow & (r["albedo"] == 0.0), ~shallow)]
    assert (f"{counts[0][0]} of the {counts[0][1]} runs with a bottom of "
            f"albedo 0.3, {counts[1][0]} of {counts[1][1]} with albedo 1, "
            f"{counts[2][0]} of {counts[2][1]} with a black bottom and "
            f"{counts[3][0]} of the {counts[3][1]} with no bottom") in text
    # The three groups outside 10 percent.
    out = ~within
    water = out & np.isclose(ratio, 0.3)
    dark = out & (r["albedo"] == 0.0) & ~np.isclose(ratio, 0.3)
    white = out & (r["albedo"] == 1.0) & ~np.isclose(ratio, 0.3)
    assert water.sum() + dark.sum() + white.sum() == out.sum() == 34
    assert f"{water.sum()} have bp/a = 0.3" in text
    assert f"low, {q[water].min():.3f} to {q[water].max():.3f}" in text
    assert np.all(q[water] < 1)
    assert set(r["depth_m"][dark]) <= {1.0, 4.0} and np.all(q[dark] > 1)
    assert set(np.round(ratio[dark])) <= {3.0, 30.0}
    assert f"{dark.sum()} have a black bottom at 1 or 4 m" in text
    assert f"high, {q[dark].min():.3f} to {q[dark].max():.3f}" in text
    assert set(r["depth_m"][white]) <= {1.0, 4.0}
    assert set(np.round(ratio[white])) == {30.0}
    assert f"{white.sum()} have a white bottom at 1 or 4 m and bp/a = 30: " \
           f"{q[white].min():.3f} to {q[white].max():.3f}" in text
    # Each miss is far outside the Monte Carlo's noise.
    assert np.all(np.abs(q[out] - 1) > 2 * rel[out] * q[out])


@source_tree
def test_the_1998_constants_against_the_same_runs():
    r = _mc_rows()
    old = np.array([
        _by_hand(a, bb, h if math.isfinite(h) else 1e6, rho, sun, "1998")[0]
        for a, bb, h, rho, sun in zip(r["a"], r["bb"], r["depth_m"],
                                      r["albedo"], r["sun_deg"])])
    q = old / r["monte_carlo"]
    text = " ".join((ROOT / "DATA.md").read_text().split())
    assert (f"median {np.median(q):.3f}, within 10 percent in "
            f"{100 * np.mean(np.abs(q - 1) <= 0.1):.1f} percent. The update"
            ) in text
    decisions = " ".join((ROOT / "DECISIONS.md").read_text().split())
    assert (f"median {np.median(q):.3f}, {100 * np.mean(np.abs(q - 1) <= 0.1):.1f}"
            " percent within 10 percent") in decisions


def test_the_cut_share_quoted_in_decisions():
    if not (ROOT / "tools" / "shallow_rrs_mc.py").exists():
        pytest.skip("not running from a source tree")
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import shallow_rrs_mc
    finally:
        sys.path.pop(0)
    below = shallow_rrs_mc.petzold_phase("NUC 2240")[2]
    decisions = " ".join((ROOT / "DECISIONS.md").read_text().split())
    assert f"{100 * below:.1f} percent at NUC 2240" in decisions


@source_tree
def test_the_figures_the_changelog_quotes():
    r = _mc_rows()
    q = r["model"] / r["monte_carlo"]
    text = " ".join((ROOT / "CHANGELOG.md").read_text().split())
    section = text.split("## 1.26.0")[1].split("## 1.25.2")[0]
    within = 100 * np.mean(np.abs(q - 1) <= 0.1)
    assert (f"median ratio of {np.median(q):.3f}, and {within:.1f} percent of "
            "the runs are within 10 percent") in section
    assert f"low, by up to {100 * (1 - q.min()):.0f} percent" in section
    assert f"high, by up to {100 * (q.max() - 1):.0f} percent" in section
    old = np.array([
        _by_hand(a, bb, h if math.isfinite(h) else 1e6, rho, sun, "1998")[0]
        for a, bb, h, rho, sun in zip(r["a"], r["bb"], r["depth_m"],
                                      r["albedo"], r["sun_deg"])])
    q_old = old / r["monte_carlo"]
    assert np.mean(np.abs(q_old - 1) <= 0.1) < np.mean(np.abs(q - 1) <= 0.1)
    assert "The 1998 constants do worse against the same runs" in section

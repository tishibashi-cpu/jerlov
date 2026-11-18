"""The light kept within an angle, from Petzold's forward scattering:
DECISIONS.md section 107, DATA.md section 49."""

from __future__ import annotations

import csv
import pathlib
import re
import warnings

import numpy as np
import pytest

import jerlov
from jerlov import _data

ROOT = pathlib.Path(__file__).resolve().parent.parent
MC = ROOT / "examples" / "data" / "forward_scatter" / "monte_carlo.csv"
source_tree = pytest.mark.skipif(
    not (ROOT / "pyproject.toml").exists(),
    reason="not running from a source tree")


def _fs(station, theta0):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        return jerlov.forward_scatter(jerlov.petzold_scattering(station),
                                      theta0)


def _flat(path):
    return " ".join((ROOT / path).read_text().split())


# -- criteria 1 and 2 ---------------------------------------------------------

@pytest.mark.parametrize("station", jerlov.PETZOLD_STATIONS)
def test_all_of_b_within_180_degrees_and_a_left(station):
    s = jerlov.petzold_scattering(station)
    r = _fs(station, 180.0)
    assert r.fraction == pytest.approx(1.0, abs=0.003)
    assert r.c_within == pytest.approx(s.a, abs=0.003 * s.b)


@pytest.mark.parametrize("station", jerlov.PETZOLD_STATIONS)
def test_the_share_rises_with_the_angle(station):
    grid = np.geomspace(0.1, 180.0, 300)
    shares = [_fs(station, t).fraction for t in grid]
    assert np.all(np.diff(shares) >= 0)
    within = [_fs(station, t).c_within for t in grid]
    assert np.all(np.diff(within) <= 0)


@pytest.mark.parametrize("station", jerlov.PETZOLD_STATIONS)
def test_at_a_printed_angle_the_share_is_the_report_s(station):
    rows = sorted((r for r in _data._rows("petzold1972_vsf.csv")
                   if r["station"] == station),
                  key=lambda r: float(r["angle_deg"]))
    for r in rows[::7]:
        assert _fs(station, float(r["angle_deg"])).fraction == \
            float(r["normalized_integral"])
    assert _fs(station, 0.1).fraction == pytest.approx(
        jerlov.petzold_scattering(station).fraction_below_0_1_deg)


@pytest.mark.parametrize("station", jerlov.PETZOLD_STATIONS)
def test_between_printed_angles_the_vsf_reproduces_the_report(station):
    """DATA.md section 49: within 0.33 percent everywhere (0.325 at the
    worst, AUTEC 8)."""
    s = jerlov.petzold_scattering(station)
    rows = sorted((r for r in _data._rows("petzold1972_vsf.csv")
                   if r["station"] == station),
                  key=lambda r: float(r["angle_deg"]))
    printed = np.array([float(r["integral_per_m"]) for r in rows])
    ours = [printed[0]]
    for i in range(s.angles_deg.size - 1):
        theta = np.linspace(s.angles_deg[i], s.angles_deg[i + 1], 257)
        vsf = s.vsf_at(theta) if i > 2 else np.exp(np.interp(
            np.log(theta), np.log(s.angles_deg), np.log(s.vsf)))
        rad = np.radians(theta)
        ours.append(ours[-1] + 2 * np.pi * float(
            _data.trapezoid(vsf * np.sin(rad), rad)))
    worst = np.max(np.abs(np.array(ours) - printed) / printed)
    assert worst < 0.0033
    if station == "AUTEC 8":
        assert worst > 0.0032


# -- the figures DATA.md section 49 quotes ------------------------------------

def test_the_shares_quoted():
    for theta0, lo, hi in ((1.0, 0.200, 0.375), (5.0, 0.458, 0.641),
                           (20.0, 0.753, 0.871)):
        shares = {s: _fs(s, theta0).fraction for s in jerlov.PETZOLD_STATIONS}
        assert round(min(shares.values()), 3) == lo
        assert round(max(shares.values()), 3) == hi
    assert min({s: _fs(s, 1.0).fraction for s in jerlov.PETZOLD_STATIONS}
               .items(), key=lambda kv: kv[1])[0] == "AUTEC 8"
    assert max({s: _fs(s, 1.0).fraction for s in jerlov.PETZOLD_STATIONS}
               .items(), key=lambda kv: kv[1])[0] == "HAOCE 5"


@source_tree
def test_the_topic_page_states_them():
    text = _flat("docs/topics/seeing_through_water.rst")
    assert "At Petzold's eight stations 46 to 64 percent" in text
    shares = [_fs(s, 5.0).fraction for s in jerlov.PETZOLD_STATIONS]
    assert round(100 * min(shares)) == 46 and round(100 * max(shares)) == 64


@source_tree
def test_the_data_md_section_states_them():
    text = _flat("DATA.md")
    for phrase in ("Within 1 degree lies 20.0 (AUTEC 8) to 37.5 percent",
                   "within 5 degrees 45.8 to 64.1 percent",
                   "within 20 degrees 75.3 to 87.1 percent",
                   "within 0.33 percent at every angle",
                   "agree within 0.36 percent",
                   "8.5 percent below at 20 degrees (AUTEC 8)",
                   "up to 3.1 percent above",
                   "up to 1.1 percentage points (HAOCE 11 at 0.5 degree)"):
        assert phrase in text, phrase


# -- criterion 3: the Monte Carlo, as run -------------------------------------

def _mc():
    return list(csv.DictReader(MC.open()))


@source_tree
def test_the_monte_carlo_meets_its_criterion():
    rows = _mc()
    assert len(rows) == 48
    near = [abs(float(r["ratio"]) - 1) for r in rows
            if float(r["b_r"]) <= 0.5]
    assert max(near) < 0.03                 # the criterion set beforehand
    assert round(100 * max(near), 2) == 0.36  # as DATA.md says


@source_tree
def test_the_monte_carlo_figures_quoted():
    rows = _mc()
    far = [r for r in rows if float(r["b_r"]) == 3.0]
    low = min(far, key=lambda r: float(r["ratio"]))
    assert (low["station"], float(low["half_angle_deg"])) == ("AUTEC 8", 20.0)
    assert round(100 * (1 - float(low["ratio"])), 1) == 8.5
    assert round(100 * (max(float(r["ratio"]) for r in far) - 1), 1) == 3.1
    gap = max(rows, key=lambda r: abs(float(r["share_sampler"])
                                      - float(r["share_package"])))
    assert (gap["station"], float(gap["half_angle_deg"])) == ("HAOCE 11", 0.5)
    assert round(100 * abs(float(gap["share_sampler"])
                           - float(gap["share_package"])), 1) == 1.1


@source_tree
def test_the_monte_carlo_share_is_the_package_s_as_run():
    for r in _mc():
        assert float(r["share_package"]) == pytest.approx(
            _fs(r["station"], float(r["half_angle_deg"])).fraction, abs=6e-6)


# -- the API ------------------------------------------------------------------

def test_it_always_warns_and_points_at_the_caller():
    s = jerlov.petzold_scattering("AUTEC 8")
    with pytest.warns(jerlov.ProvenanceWarning, match="3.4%") as caught:
        jerlov.forward_scatter(s, 5.0)
    assert caught[0].filename == __file__
    with pytest.warns(jerlov.ProvenanceWarning) as caught:
        jerlov.forward_scatter(jerlov.petzold_scattering("NUC 2200"), 5.0)
    assert "extrapolated angles" not in str(caught[0].message)


@pytest.mark.parametrize("bad", [0.05, 180.5, -1.0, np.nan, np.inf, "5",
                                 [5.0], None])
def test_the_half_angle_is_one_measured_angle(bad):
    with pytest.raises(ValueError):
        jerlov.forward_scatter(jerlov.petzold_scattering("AUTEC 8"), bad)


def test_the_station_has_no_default():
    with pytest.raises(TypeError):
        jerlov.forward_scatter("AUTEC 8", 5.0)
    with pytest.raises(TypeError):
        jerlov.forward_scatter(half_angle_deg=5.0)


def test_attenuation_within_a_water():
    fw = _fs("HAOCE 11", 5.0)
    w = jerlov.water("III")
    got = jerlov.attenuation_within(w, 550.0, forward=fw)
    assert isinstance(got, float)
    assert got == pytest.approx(w.c(550.0) - fw.fraction * w.b(550.0))
    assert w.a(550.0) < got < w.c(550.0)
    wl = np.array([450.0, 550.0, 650.0])
    arr = jerlov.attenuation_within(w, wl, forward=fw)
    assert arr.shape == (3,)
    assert np.allclose(arr, w.c(wl) - fw.fraction * w.b(wl))
    assert np.array_equal(wl, [450.0, 550.0, 650.0])


def test_attenuation_within_refuses_what_it_cannot_do():
    fw = _fs("HAOCE 11", 5.0)
    with pytest.raises(TypeError):
        jerlov.attenuation_within(jerlov.water("III"), 550.0, forward=0.6)
    with pytest.raises(TypeError):
        jerlov.attenuation_within(jerlov.water("III"), 550.0)
    with pytest.raises(jerlov.MissingQuantityError):
        jerlov.attenuation_within(jerlov.water("III", source="jerlov1976"),
                                  550.0, forward=fw)
    with pytest.raises(ValueError):
        jerlov.attenuation_within(jerlov.water("III"), 900.0, forward=fw)


def test_the_result_is_a_value():
    a, b = _fs("AUTEC 8", 5.0), _fs("AUTEC 8", 5.0)
    assert a == b and hash(a) == hash(b)
    assert a != _fs("AUTEC 8", 6.0)
    assert re.search(r"fraction=0\.45", repr(a))

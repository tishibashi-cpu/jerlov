"""Solonenko & Mobley's IOPs through the Monte Carlo and OSOAA, against
their HydroLight Kd (DATA.md section 40, OPEN_QUESTIONS.md, DECISIONS.md
section 94): the Monte Carlo's new options, the runs kept in examples/data,
and every figure the documents quote, recomputed from them. Away from the
source tree, all skipped."""

from __future__ import annotations

import contextlib
import csv
import io
import math
import pathlib
import runpy
import sys
import warnings

import pytest

import jerlov

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "examples" / "data"
pytestmark = pytest.mark.skipif(
    not (ROOT / "DATA.md").exists() or not (DATA / "sm_closure").exists()
    or not (ROOT / "tools" / "kd_monte_carlo.py").exists(),
    reason="needs the source tree (DATA.md, examples/data and tools)")
SM_TYPES = ("I", "IA", "IB", "II", "III", "1C", "3C", "5C", "7C", "9C")


def _flat(name):
    return " ".join((ROOT / name).read_text().split())


@pytest.fixture(scope="module")
def tools():
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import kd_monte_carlo
        import sm_closure
    finally:
        sys.path.remove(str(ROOT / "tools"))
    return kd_monte_carlo, sm_closure


@pytest.fixture(scope="module")
def runs():
    with open(DATA / "sm_closure" / "runs.csv") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def closure():
    module = runpy.run_path(str(ROOT / "examples" / "closure_with_jerlov_kd.py"),
                            run_name="closure_with_jerlov_kd")
    with contextlib.redirect_stdout(io.StringIO()), \
            warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        return module["main"]()


# -- The Monte Carlo's two options -------------------------------------------


def test_a_sky_with_no_scattering_against_quadrature(tools):
    mc, _ = tools
    sample, _ = mc.petzold_sampler("HAOCE 5")
    (k,) = mc.kd(0.1, 0.0, sample, 30.0, optical_depths=(math.log(10),),
                 photons=200_000, sky_share=0.3)
    assert k == pytest.approx(mc.sky_only_kd(0.1, 30.0, 0.3, math.log(10)),
                              rel=0.005)
    # The sky slants the light: Kd above the sun's beam alone.
    assert k > 0.1 / mc.refracted_cosine(30.0)


def test_pure_water_phase_function(tools):
    mc, _ = tools
    angles = mc.water_sampler()(
        __import__("numpy").random.default_rng(3).random(400_000))
    assert float(__import__("numpy").cos(angles).mean()) == pytest.approx(
        0.0, abs=0.004)
    assert float((angles > math.pi / 2).mean()) == pytest.approx(0.5,
                                                                abs=0.003)


def test_the_options_refuse_a_share_outside_0_and_1(tools):
    mc, _ = tools
    sample, _ = mc.petzold_sampler("HAOCE 5")
    for bad in (dict(water_share=1.5), dict(sky_share=-0.1)):
        with pytest.raises(ValueError):
            mc.ed_profile(0.1, 0.1, sample, 0.9, 10.0, photons=10, **bad)


def test_a_stored_run_with_both_options_is_reproduced(tools, runs):
    mc, _ = tools
    run = min((r for r in runs if r["factor"] == "base"
               and r["set"] == "solonenko2015"),
              key=lambda r: float(r["b"]) / float(r["a"]))
    sample, _ = mc.petzold_sampler(run["station"])
    k1, k10 = mc.kd(float(run["a"]), float(run["b"]), sample,
                    float(run["sun_deg"]),
                    optical_depths=(1.0, math.log(10.0)),
                    photons=int(run["photons"]), seed=int(run["seed"]),
                    water_share=float(run["water_share"]),
                    sky_share=float(run["sky_share"]))
    assert k1 == pytest.approx(float(run["kd_first_penetration_depth"]),
                               rel=1e-9)
    assert k10 == pytest.approx(float(run["kd_to_10_percent"]), rel=1e-9)


# -- The runs ----------------------------------------------------------------


def test_the_runs(tools, runs):
    _, sm = tools
    assert len(runs) == 2457
    counts = {}
    for r in runs:
        counts[(r["set"], r["factor"])] = counts.get(
            (r["set"], r["factor"]), 0) + 1
    assert counts == {
        ("solonenko2015", "as_section_92"): 143,
        ("solonenko2015", "water_only"): 143,
        ("solonenko2015", "base"): 143,
        ("solonenko2015", "station"): 1001,
        ("solonenko2015", "sun_deg"): 429,
        ("solonenko2015", "aot"): 286,
        ("williamson2022", "water_only"): 72,
        ("williamson2022", "base"): 72,
        ("williamson2022", "sun_deg"): 48,
        ("williamson2022", "station"): 72,
        ("williamson2022", "pure_water"): 48}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        base = [r for r in runs if r["set"] == "solonenko2015"
                and r["factor"] == "base"]
        for r in base:
            water = jerlov.water(r["water_type"], source="solonenko2015")
            wl = float(r["wavelength_nm"])
            assert float(r["a"]) == float(water.a(wl))
            assert float(r["b"]) == float(water.b(wl))
            assert float(r["kd_hydrolight"]) == float(water.kd_hydrolight(wl))
            bw = 0.00583 * (400.0 / wl) ** 4.322
            assert float(r["water_share"]) == pytest.approx(
                bw / float(r["b"]), rel=1e-12)
            assert float(r["sun_deg"]) == (
                15.0 if r["water_type"] in SM_TYPES[:5] else 45.0)
            assert r["station"] == "NUC 2240"
        # The sky's share as Gregg & Carder give it, for a few cells (to
        # the last bits, which differ between NumPy versions).
        for r in base[::29]:
            assert float(r["sky_share"]) == pytest.approx(sm.sky_share(
                float(r["sun_deg"]), float(r["wavelength_nm"]), 0.2),
                rel=1e-12)
    # Every run of one cell shares its seed.
    seeds = {}
    for r in runs:
        if r["set"] == "solonenko2015":
            seeds.setdefault((r["water_type"], r["wavelength_nm"]),
                             set()).add(r["seed"])
    assert len(seeds) == 143
    assert all(len(s) == 1 for s in seeds.values())
    assert sum(r["status_b"] == "suspect" for r in base) == 30


def test_the_williamson_and_hollins_runs_use_section_92s_seeds(runs):
    with open(DATA / "kd_closure" / "runs.csv") as handle:
        old = {(r["factor"], r["value"], r["water_type"], r["wavelength_nm"]):
               r for r in csv.DictReader(handle)}
    for r in runs:
        if r["set"] != "williamson2022":
            continue
        factor = "base" if r["factor"] == "water_only" else r["factor"]
        match = old[(factor, r["value"], r["water_type"], r["wavelength_nm"])]
        assert r["seed"] == match["seed"]
        assert float(r["a"]) == float(match["a"])
        assert float(r["b"]) == float(match["b"])


def test_the_osoaa_runs():
    with open(DATA / "osoaa_sm_closure" / "runs.csv") as handle:
        runs = list(csv.DictReader(handle))
    assert len(runs) == 286
    base = [r for r in runs if r["factor"] == "base"]
    assert len(base) == 143
    assert sum(r["status"] == "ok" for r in base) == 114
    assert {r["status"].split(" less")[0] for r in runs
            if r["status"] != "ok"} == {"not_run: a", "not_run: b"}


# -- What the documents quote ------------------------------------------------


def test_against_hydrolight(closure):
    h = closure["hydrolight"]
    assert h["cells"] == 143
    printed = {"as_section_92": (0.945, 79.7, 0.769, 1.110),
               "water_only": (0.951, 90.2, 0.852, 1.138),
               "base": (0.970, 94.4, 0.881, 1.157)}
    for factor, (median, within, low, high) in printed.items():
        s = h["stats"][factor]
        assert (round(s["median"], 3), round(100 * s["within"], 1),
                round(s["low"], 3), round(s["high"], 3)) == (
            median, within, low, high), factor
    assert h["agrees"]
    assert h["outside"] == []
    per_type = {t: (round(lo, 2), round(hi, 2))
                for t, (lo, hi) in h["per_type"].items()}
    assert per_type == {"I": (0.93, 0.99), "IA": (0.93, 0.99),
                        "IB": (0.93, 1.0), "II": (0.95, 1.16),
                        "III": (0.88, 0.96), "1C": (1.0, 1.08),
                        "3C": (0.93, 1.0), "5C": (0.93, 1.0),
                        "7C": (1.0, 1.1), "9C": (0.93, 0.98)}
    moves = {f: (round(100 * (lo - 1), 1), round(100 * (hi - 1), 1))
             for f, (lo, hi) in h["moves"].items()}
    assert moves == {"station": (-12.7, 26.0), "sun_deg": (-12.7, 21.5),
                     "aot": (-1.8, 2.0)}
    assert len(h["over_h"]) == 114 and h["not_run"] == 29
    assert (round(h["over_h"][0][0], 3), round(h["over_h"][-1][0], 3)) == (
        0.877, 1.158)
    assert (round(h["over_mc"][0][0], 3), round(h["over_mc"][-1][0], 3)) == (
        0.986, 1.037)
    data, oq = _flat("DATA.md"), _flat("OPEN_QUESTIONS.md")
    rows = ("| As section 39: one phase function, no sky | 0.945 | 79.7 "
            "percent | 0.769 to 1.110 |",
            "| With pure water's own scattering | 0.951 | 90.2 percent | "
            "0.852 to 1.138 |",
            "| With it and a sky | 0.970 | 94.4 percent | 0.881 to 1.157 |")
    for row in rows:
        assert row in data, row
    for row in ("| One phase function, no sky (as first run) | 0.945 | 79.7 "
                "percent |", "| With pure water's own scattering | 0.951 | "
                "90.2 percent |", "| With it and a clear sky | 0.970 | 94.4 "
                "percent |"):
        assert row in oq, row
    for quoted in ("0.93 to 1.00 for I, IA, IB, 3C, 5C and 9C, 1.00 to 1.08 "
                   "for 1C and 1.00 to 1.10 for 7C",
                   "II reaches 1.16 (1.13 to 1.16 from 425 to 500 nm)",
                   "stays at 0.88 to 0.96", "-12.7 to +26.0 percent",
                   "the sun by -12.7 to +21.5", "the aerosol by -1.8 to +2.0",
                   "at all 143 cells", "29 of the 143 cells",
                   "0.986 to 1.037 times the Monte Carlo's",
                   "0.877 to 1.158 times K_d^H (median 0.978)",
                   "30 of the 143 cells", "2457 runs"):
        assert quoted in data, quoted
    assert round(float(sorted(x for x, _, _ in h["over_h"])[56]), 3) <= 0.978
    for quoted in ("-12.7 to +26.0 percent, the sun by -12.7 to +21.5",
                   "0.986 to 1.037 times the Monte Carlo's Kd at the 114 "
                   "cells", "0.877 to 1.158 times K_d^H", "29 cells",
                   "up to 1.16 times K_d^H at 425 to 500 nm",
                   "at 0.88 to 0.96", "in 2457 runs"):
        assert quoted in oq, quoted
    site = _flat("docs/open_questions.rst")
    assert "a median 0.970" in site and "94.4 percent of 143 cells" in site
    assert "within 4 percent" in site
    readme = _flat("examples/README.md")
    assert "a median **0.970**" in readme
    assert "94.4 percent of 143 cells within 10 percent" in readme


def test_the_median_of_osoaa_over_hydrolight(closure):
    import numpy as np
    h = np.array([x for x, _, _ in closure["hydrolight"]["over_h"]])
    assert round(float(np.median(h)), 3) == 0.978
    assert max(abs(x - 1) for x, _, _ in
               closure["hydrolight"]["over_mc"]) < 0.04


def test_williamson_and_hollins_with_water_and_sky(closure):
    w = closure["water_and_sky"]
    assert (round(100 * (w["rise"][0] - 1), 1),
            round(100 * (w["rise"][1] - 1), 1)) == (1.3, 7.6)
    assert (round(100 * (w["rise_water"][0] - 1), 1),
            round(100 * (w["rise_water"][1] - 1), 1)) == (-0.1, 4.7)
    sec = w["against"]
    assert [(round(sec[k][0][0], 3), round(sec[k][-1][0], 3))
            for k in ("section_92", "water", "water_and_sky")] == [
        (1.007, 1.096), (1.006, 1.047), (0.991, 1.018)]
    assert (round(w["down"], 2), round(w["up"], 2)) == (0.79, 1.44)
    tables = {t: tuple(f"{min(r.values()):.2f} to {max(r.values()):.2f}"
                       for r in (w["ratios"][(t, "jerlov1976")],))[0]
              for t in ("IB", "III")}
    assert tables == {"IB": "1.00 to 1.55", "III": "0.86 to 1.03"}
    assert round(w["ratios"][("3C", "jerlov1976")][425], 2) == 0.53
    beyond = {k: round(v, 2) for k, v in w["beyond"].items()}
    assert beyond == {("IB", 425): 1.41, ("IB", 450): 1.55,
                      ("IB", 475): 1.55, ("IB", 500): 1.27,
                      ("1C", 425): 0.59, ("3C", 425): 0.53,
                      ("3C", 450): 0.64, ("5C", 425): 0.66}
    assert w["went_outside"] == [("IB", 500)] and w["came_inside"] == []
    assert (round(100 * w["sky"][0]), round(100 * w["sky"][1])) == (19, 31)
    data, oq = _flat("DATA.md"), _flat("OPEN_QUESTIONS.md")
    for text in (data, oq):
        assert "+1.3 to +7.6 percent" in text
        assert "0.991 to 1.018" in text
        assert "0.79 to 1.44 times" in text
    assert "now 1.41 to 1.55 times Jerlov's" in data
    assert "and also IB at 500 nm (1.27)" in data
    assert ("1.00 to 1.55 for IB, 0.86 to 1.03 for III and down to 0.53 for "
            "3C at 425 nm") in oq
    assert "0.991 to 1.018 times the Monte Carlo's Kd" in _flat(
        "examples/README.md")

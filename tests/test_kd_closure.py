"""Williamson & Hollins's IOPs against Jerlov's Kd (DATA.md section 39,
OPEN_QUESTIONS.md, DECISIONS.md sections 90 to 93): the Monte Carlo's own
checks, and every figure the documents quote, recomputed from the runs in
examples/data. Away from the source tree, all skipped."""

from __future__ import annotations

import contextlib
import csv
import io
import math
import pathlib
import runpy
import sys
import warnings

import numpy as np
import pytest

import jerlov

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "examples" / "data"
pytestmark = pytest.mark.skipif(
    not (ROOT / "DATA.md").exists() or not (DATA / "kd_closure").exists()
    or not (ROOT / "tools" / "kd_monte_carlo.py").exists(),
    reason="needs the source tree (DATA.md, examples/data and tools)")
TYPES = ("IB", "II", "III", "1C", "3C", "5C")
WAVELENGTHS = tuple(range(425, 701, 25))


@pytest.fixture(scope="module")
def mc():
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import kd_monte_carlo
    finally:
        sys.path.remove(str(ROOT / "tools"))
    return kd_monte_carlo


@pytest.fixture(scope="module")
def runs():
    with open(DATA / "kd_closure" / "runs.csv") as handle:
        return list(csv.DictReader(handle))


def _flat(name):
    return " ".join((ROOT / name).read_text().split())


def jerlov_kd(water_type, wl, source):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        return float(jerlov.water(water_type, source=source).kd(float(wl)))


def base_kd(runs):
    return {(r["water_type"], int(r["wavelength_nm"])):
            float(r["kd_first_penetration_depth"])
            for r in runs if r["factor"] == "base"}


# -- The Monte Carlo ---------------------------------------------------------


def test_no_scattering_is_beer(mc):
    sample, _ = mc.petzold_sampler("HAOCE 5")
    (k,) = mc.kd(0.1, 0.0, sample, 30.0, photons=100_000)
    assert k == pytest.approx(0.1 / mc.refracted_cosine(30.0), rel=0.01)


def test_against_morel_and_loisel(mc):
    """NUC 2240's phase function, b/a = 3: within 2 percent of Eq. (2) of
    Williamson & Hollins (2022), Morel and Loisel's relation."""
    mu0 = mc.refracted_cosine(30.0)
    sample, ratio = mc.petzold_sampler("NUC 2240")
    assert ratio == pytest.approx(0.0179, abs=5e-5)
    (k,) = mc.kd(0.1, 0.3, sample, 30.0, photons=200_000)
    assert k / 0.1 == pytest.approx(mc.morel_loisel(3.0, mu0, 0.0),
                                    rel=0.02)


def test_a_stored_run_is_reproduced(mc, runs):
    """The run with the least scattering, made again from its seed."""
    run = min((r for r in runs if r["factor"] == "base"),
              key=lambda r: float(r["b"]) / float(r["a"]))
    sample, _ = mc.petzold_sampler(run["station"])
    k1, k10 = mc.kd(float(run["a"]), float(run["b"]), sample,
                    float(run["sun_deg"]),
                    optical_depths=(1.0, 2.302585092994046),
                    photons=int(run["photons"]), seed=int(run["seed"]))
    assert k1 == pytest.approx(float(run["kd_first_penetration_depth"]),
                               rel=1e-9)
    assert k10 == pytest.approx(float(run["kd_to_10_percent"]), rel=1e-9)


def test_the_runs(runs):
    assert len(runs) == 240
    counts = {}
    for r in runs:
        counts[r["factor"]] = counts.get(r["factor"], 0) + 1
    assert counts == {"base": 72, "sun_deg": 48, "station": 72,
                      "pure_water": 48}
    assert set(base_kd(runs)) == {(t, wl) for t in TYPES
                                  for wl in WAVELENGTHS}
    stations = {r["water_type"]: r["station"] for r in runs
                if r["factor"] == "base"}
    assert stations == {"IB": "AUTEC 7", "II": "HAOCE 11", "III": "HAOCE 5",
                        "1C": "HAOCE 5", "3C": "HAOCE 5", "5C": "NUC 2240"}
    # Each run's a and b are the type's, or its contents on another aw.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        for r in runs:
            wl = float(r["wavelength_nm"])
            water = jerlov.water(r["water_type"])
            a = float(water.a(wl))
            if r["pure_water"] != "williamson2022":
                a += (float(jerlov.pure_water_absorption_table(
                    wl, source=r["pure_water"]))
                    - float(jerlov.pure_water_absorption(wl)))
            assert float(r["a"]) == pytest.approx(a, rel=1e-12)
            assert float(r["b"]) == float(water.b(wl))


# -- What DATA.md and OPEN_QUESTIONS.md quote --------------------------------


def test_the_tables_against_jerlov(runs):
    base = base_kd(runs)
    expected = {"IB": ("0.98 to 1.47", "0.99 to 1.56"),
                "II": ("0.92 to 1.10", "0.81 to 1.22"),
                "III": ("0.84 to 0.98", "0.65 to 1.09"),
                "1C": ("0.56 to 1.03", "0.72 to 1.11"),
                "3C": ("0.51 to 1.01", "0.66 to 1.01"),
                "5C": ("0.64 to 1.02", "0.64 to 1.01")}
    for document in ("DATA.md", "OPEN_QUESTIONS.md"):
        text = (ROOT / document).read_text()
        for water_type, (r76, r68) in expected.items():
            assert f"| {water_type} | {r76} | {r68} |" in text, (
                document, water_type)
    for water_type, printed in expected.items():
        for source, cell in zip(("jerlov1976", "jerlov1968"), printed):
            r = [base[(water_type, wl)] / jerlov_kd(water_type, wl, source)
                 for wl in WAVELENGTHS]
            assert f"{min(r):.2f} to {max(r):.2f}" == cell


def _moves(runs):
    base = {(r["water_type"], r["wavelength_nm"]):
            float(r["kd_first_penetration_depth"])
            for r in runs if r["factor"] == "base"}
    out = {}
    for factor in ("sun_deg", "station", "pure_water"):
        changes = [float(r["kd_first_penetration_depth"])
                   / base[(r["water_type"], r["wavelength_nm"])]
                   for r in runs if r["factor"] == factor]
        assert {r["water_type"] for r in runs
                if r["factor"] == factor} == {"IB", "III"}
        out[factor] = (min(changes), max(changes))
    return out


def test_the_conditions(runs):
    moves = _moves(runs)
    printed = {"sun_deg": "-7.7 to +22.4 percent",
               "station": "-6.4 to +14.5 percent",
               "pure_water": "-10.9 to +9.3 percent"}
    for factor, (low, high) in moves.items():
        cell = f"{100 * (low - 1):+.1f} to {100 * (high - 1):+.1f} percent"
        assert cell == printed[factor]
        for document in ("DATA.md", "OPEN_QUESTIONS.md"):
            assert cell in _flat(document), (document, factor)
    layer = [float(r["kd_to_10_percent"])
             / float(r["kd_first_penetration_depth"])
             for r in runs if r["factor"] == "base"]
    assert (f"{100 * (min(layer) - 1):+.1f} to "
            f"{100 * (max(layer) - 1):+.1f} percent") == (
        "+0.3 to +8.0 percent")
    assert "+0.3 to +8.0 percent" in _flat("DATA.md")


def test_where_the_conditions_cannot_reach(runs):
    moves = _moves(runs)
    up = float(np.prod([h for _, h in moves.values()]))
    down = float(np.prod([lo for lo, _ in moves.values()]))
    assert (round(down, 2), round(up, 2)) == (0.77, 1.53)
    base = base_kd(runs)
    beyond = {}
    for water_type in TYPES:
        for wl in WAVELENGTHS:
            r = base[(water_type, wl)] / jerlov_kd(water_type, wl,
                                                    "jerlov1976")
            if r * up < 1 or r * down > 1:
                beyond[(water_type, wl)] = round(r, 2)
    assert beyond == {("IB", 425): 1.31, ("IB", 450): 1.45,
                      ("IB", 475): 1.47, ("1C", 425): 0.56,
                      ("3C", 425): 0.51, ("3C", 450): 0.62,
                      ("5C", 425): 0.64}
    for document in ("DATA.md", "OPEN_QUESTIONS.md"):
        assert "0.77 to 1.53 times" in _flat(document)


def test_williamson_and_hollins_chose_their_waters_by_jerlov_1976():
    """Their ip_jerlov.csv is not shipped; DATA.md records that it equals
    jerlov1976_kd.csv at every wavelength compared, and their Table 5."""
    text = _flat("DATA.md")
    assert "within 25 percent" in text
    assert "equal `jerlov1976_kd.csv` at every wavelength compared here" in (
        text)
    assert "Kd within 14 to 17 percent of Jerlov's" in text


# -- OSOAA, a second calculation (DECISIONS.md section 93) -------------------


@pytest.fixture(scope="module")
def closure():
    module = runpy.run_path(str(ROOT / "examples" / "closure_with_jerlov_kd.py"),
                            run_name="closure_with_jerlov_kd")
    with contextlib.redirect_stdout(io.StringIO()), \
            warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        return module["main"]()


def test_osoaa_runs_are_made_with_the_corrected_phase_function():
    """Each run's phase function in OSOAA's record is what the writer
    writes today, 4 pi vsf / b, for the station the run names."""
    with open(DATA / "osoaa_closure" / "runs.csv") as handle:
        runs = list(csv.DictReader(handle))
    assert len(runs) == 408
    made = [r for r in runs if r["status"] == "ok"]
    assert len(made) == 362
    with open(DATA / "osoaa_closure" / "truncation.csv") as handle:
        assert [int(r["run_id"]) for r in csv.DictReader(handle)] == [
            int(r["run_id"]) for r in made]
    for station in {r["station"] for r in made}:
        s = jerlov.petzold_scattering(station)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
            text = jerlov.osoaa_phase_function(
                s, minus_f12_over_f11=0.0, f22_over_f11=1.0,
                f33_over_f11=1.0)
        assert "F11 = 4 pi vsf/b" in text


def test_osoaa_against_the_monte_carlo(closure):
    now = closure["osoaa"]["now"]
    ratios = now["ratios"]
    assert len(ratios) == 62
    assert (round(ratios[0][0], 3), ratios[0][1], ratios[0][2]) == (
        1.007, "1C", 675)
    assert (round(ratios[-1][0], 3), ratios[-1][1], ratios[-1][2]) == (
        1.096, "IB", 425)
    share = now["share"]
    assert (round(100 * share[0], 1), round(100 * share[1], 1)) == (
        56.2, 72.7)
    station = closure["osoaa"]["station"]
    assert (round(100 * (station[0] - 1), 1),
            round(100 * (station[1] - 1), 1)) == (-5.8, 14.9)
    sky = closure["osoaa"]["sky"]
    assert (round(100 * (sky[0] - 1), 1), round(100 * (sky[1] - 1), 1)) == (
        -0.3, 0.8)
    assert sorted(closure["osoaa"]["beyond"]) == [
        ("1C", 425), ("3C", 425), ("3C", 450), ("IB", 425), ("IB", 450),
        ("IB", 475)]
    assert closure["osoaa"]["missing"] == [("5C", 425)]
    data = _flat("DATA.md")
    for quoted in ("OSOAA's Kd is 1.007 to 1.096 times the Monte Carlo's",
                   "1.096 for IB at 425 nm, 1.007 for 1C at 675 nm",
                   "56.2 to 72.7 percent", "-5.8 to +14.9 percent",
                   "-0.3 to +0.8", "but for 5C at 425 nm",
                   "46 runs cannot be made"):
        assert quoted in data, quoted
    assert "Kd 1.007 to 1.096 times the Monte Carlo's" in _flat(
        "OPEN_QUESTIONS.md")
    assert "but for 5C at 425 nm" in _flat("OPEN_QUESTIONS.md")
    assert "up to 9.6 percent above" in _flat("OPEN_QUESTIONS.md")
    assert round(100 * (ratios[-1][0] - 1), 1) == 9.6
    assert "1.007 to 1.096 times" in _flat("examples/README.md")
    assert "within 10 percent" in _flat("docs/open_questions.rst")


def test_osoaa_record_with_f11_too_small(closure):
    """The runs of 1.15.3, kept: the phase function 4 pi too small."""
    before = closure["osoaa"]["before"]
    share = before["share"]
    assert (round(100 * share[0], 1), round(100 * share[1], 1)) == (
        96.5, 97.8)
    ratios = before["ratios"]
    assert len(ratios) == 62
    low, high = 100 * (1 - ratios[-1][0]), 100 * (1 - ratios[0][0])
    assert (round(low, 1), round(high, 1)) == (0.7, 23.1)
    for document in ("DATA.md", "OPEN_QUESTIONS.md"):
        assert "96.5 to 97.8 percent" in _flat(document)
        assert "0.7 to 23.1 percent" in _flat(document)
    assert "96.5 to 97.8 percent" in " ".join(
        jerlov.osoaa_phase_function.__doc__.split())
    assert "up to 23.1 percent too low" in _flat("examples/README.md")
    # Petzold's functions hold far less within 23 degrees, at every
    # station OSOAA was given at the base.
    within = []
    for station in ("AUTEC 7", "HAOCE 11", "HAOCE 5", "NUC 2240"):
        s = jerlov.petzold_scattering(station)
        angles = np.asarray(s.angles_deg)
        theta = np.logspace(-1, math.log10(23.0), 4000)
        p = np.exp(np.interp(np.log(theta), np.log(angles),
                             np.log(np.asarray(s.phase_function()))))
        rad = np.radians(theta)
        w = 2 * math.pi * p * np.sin(rad)
        inside = float(np.sum(0.5 * (w[1:] + w[:-1]) * np.diff(rad)))
        within.append(s.fraction_below_0_1_deg + inside)
    assert (round(100 * min(within)), round(100 * max(within))) == (84, 89)
    assert "84 to 89 percent" in _flat("DATA.md")

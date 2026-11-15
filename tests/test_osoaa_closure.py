"""Williamson & Hollins's IOPs through OSOAA, against Jerlov's Kd: every
figure DATA.md section 39 quotes, recomputed from the runs kept in
tests/data/osoaa_closure (DECISIONS.md section 90). OSOAA itself is not run
here; tools/osoaa_closure.py made the runs."""

from __future__ import annotations

import csv
import math
import pathlib
import warnings

import numpy as np
import pytest

import jerlov

RUNS = pathlib.Path(__file__).resolve().parent / "data" / "osoaa_closure"
ROOT = pathlib.Path(__file__).resolve().parent.parent
source_tree = pytest.mark.skipif(
    not (ROOT / "DATA.md").exists(),
    reason="needs the source tree (DATA.md)")
TYPES = ("IB", "II", "III", "1C", "3C", "5C")
WAVELENGTHS = tuple(range(425, 701, 25))
SUN_IN_WATER = math.asin(math.sin(math.radians(30.0)) / 1.34)


@pytest.fixture(scope="module")
def runs():
    with open(RUNS / "runs.csv") as handle:
        table = {int(r["run_id"]): r for r in csv.DictReader(handle)}
    profiles: dict[int, list[tuple[float, float]]] = {}
    with open(RUNS / "ed.csv") as handle:
        for r in csv.DictReader(handle):
            profiles.setdefault(int(r["run_id"]), []).append(
                (float(r["depth_m"]), float(r["ed"])))
    return table, profiles


def kd(profile, drop=1.0):
    """Mean Kd from just below the surface to where Ed has fallen by
    exp(-drop), ln Ed linear between levels, the first surface level for
    depth 0."""
    z, ed = np.array(profile).T
    keep = np.concatenate([[True], np.diff(z) > 0])
    z, log_ed = z[keep], np.log(ed[keep])
    return drop / float(np.interp(-(log_ed[0] - drop), -log_ed, z))


def jerlov_kd(water_type, wl, source):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        return float(jerlov.water(water_type, source=source).kd(float(wl)))


def base_runs(runs):
    table, profiles = runs
    return {(r["water_type"], int(r["wavelength_nm"])): kd(profiles[k])
            for k, r in table.items()
            if r["factor"] == "base" and r["status"] == "ok"}


def test_the_runs(runs):
    table, profiles = runs
    assert len(table) == 408
    not_run = [r for r in table.values() if r["status"] != "ok"]
    assert len(not_run) == 46
    assert all(r["status"].startswith("not_run") for r in not_run)
    assert set(profiles) == {k for k, r in table.items()
                             if r["status"] == "ok"}
    base = base_runs(runs)
    missing = {(t, wl) for t in TYPES for wl in WAVELENGTHS} - set(base)
    assert missing == {("IB", 650), ("IB", 675), ("IB", 700), ("II", 650),
                       ("II", 675), ("II", 700), ("III", 700), ("1C", 700),
                       ("3C", 700), ("5C", 700)}
    # The contents on OSOAA's own water were run everywhere.
    assert sum(1 for r in table.values() if r["value"] == "osoaa"
               and r["status"] == "ok") == 72


def test_runs_refused_are_the_ones_osoaa_cannot_be_given(runs):
    """OSOAA's own pure water, at 650 and 700 nm, against Williamson &
    Hollins's aw (fic/OSOAA_SEA_MOL_COEFFS_JUNE_2013.txt: 0.340, 0.624)."""
    aw = jerlov.pure_water_absorption(np.array([650.0, 700.0]))
    np.testing.assert_allclose(aw, [0.3315, 0.5722])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        assert float(jerlov.water("IB").a(650.0)) < 0.340
        assert float(jerlov.water("5C").a(700.0)) < 0.624
        assert float(jerlov.water("III").a(675.0)) > 0.448


def test_osoaa_follows_the_simple_estimate(runs):
    table, profiles = runs
    deviations = []
    for k, r in table.items():
        if r["factor"] != "base" or r["status"] != "ok":
            continue
        wl = float(r["wavelength_nm"])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
            water = jerlov.water(r["water_type"])
            a, b = float(water.a(wl)), float(water.b(wl))
        ratio = jerlov.petzold_scattering(r["station"]).backscatter_ratio
        estimate = (a + ratio * b) / math.cos(SUN_IN_WATER)
        deviations.append(kd(profiles[k]) / estimate - 1)
    assert round(100 * min(deviations), 1) == -7.5
    assert round(100 * max(deviations), 1) == 5.5


@source_tree
def test_DATA_table_against_jerlov(runs):
    text = (ROOT / "DATA.md").read_text()
    base = base_runs(runs)
    expected = {"IB": ("1.00 to 1.36", "0.99 to 1.46"),
                "II": ("0.87 to 1.07", "0.78 to 1.21"),
                "III": ("0.79 to 0.95", "0.61 to 1.05"),
                "1C": ("0.54 to 1.01", "0.65 to 1.04"),
                "3C": ("0.48 to 0.98", "0.61 to 0.98"),
                "5C": ("0.54 to 0.94", "0.50 to 0.93")}
    for water_type, (r76, r68) in expected.items():
        assert f"| {water_type} | {r76} | {r68} |" in text, water_type
        for source, printed in (("jerlov1976", r76), ("jerlov1968", r68)):
            ratios = [k / jerlov_kd(water_type, wl, source)
                      for (t, wl), k in base.items() if t == water_type]
            assert f"{min(ratios):.2f} to {max(ratios):.2f}" == printed
    assert round(base[("IB", 450)] / jerlov_kd("IB", 450, "jerlov1976"),
                 2) == 1.36
    assert round(base[("3C", 425)] / jerlov_kd("3C", 425, "jerlov1976"),
                 2) == 0.48


@source_tree
def test_DATA_table_of_factors(runs):
    table, profiles = runs
    text = (ROOT / "DATA.md").read_text()
    base = {(r["water_type"], r["wavelength_nm"]): k
            for k, r in table.items()
            if r["factor"] == "base" and r["status"] == "ok"}
    printed = {"sun_deg": (-7.1, 20.7), "pure_water": (-12.0, 6.2),
               "station": (-0.6, 1.4), "aot": (-0.2, 0.8),
               "wind": (-0.3, 0.5)}
    for factor, (low, high) in printed.items():
        changes = [100 * (kd(profiles[k])
                          / kd(profiles[base[(r["water_type"],
                                              r["wavelength_nm"])]]) - 1)
                   for k, r in table.items()
                   if r["factor"] == factor and r["status"] == "ok"
                   and r["water_type"] in ("IB", "III")
                   and (r["water_type"], r["wavelength_nm"]) in base]
        assert (round(min(changes), 1), round(max(changes), 1)) == (
            low, high), factor
        assert f"{low:+.1f} to {high:+.1f} percent".replace(
            "+-", "-") in text.replace("-0.", "-0."), factor
    layer = [kd(profiles[k], math.log(10)) / kd(profiles[k]) - 1
             for k, r in table.items()
             if r["factor"] == "base" and r["status"] == "ok"]
    assert (round(100 * min(layer), 2), round(100 * max(layer), 2)) == (
        -0.10, 0.82)
    assert "-0.10 to +0.82 percent" in " ".join(text.split())


@source_tree
def test_DATA_editions_and_backscatter(runs):
    text = " ".join((ROOT / "DATA.md").read_text().split())
    for water_type, printed in (("IB", "0.99 to 1.32"),
                                ("III", "0.77 to 1.15")):
        ratios = [jerlov_kd(water_type, wl, "jerlov1976")
                  / jerlov_kd(water_type, wl, "jerlov1968")
                  for wl in WAVELENGTHS]
        assert f"{min(ratios):.2f} to {max(ratios):.2f}" == printed
        assert f"{printed} for {water_type}" in text
    # The backscatter ratio 5C at 550 nm would need to reach Jerlov (1976).
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        water = jerlov.water("5C")
        a, b = float(water.a(550.0)), float(water.b(550.0))
    needed = (jerlov_kd("5C", 550, "jerlov1976") * math.cos(SUN_IN_WATER)
              - a) / b
    assert round(needed, 1) == 0.1
    largest = max(jerlov.petzold_scattering(s).backscatter_ratio
                  for s in jerlov.PETZOLD_STATIONS)
    assert round(largest, 3) == 0.044 and needed > 2 * largest
    assert "about 0.1 for 5C at 550 nm" in text and "(0.044)" in text


@source_tree
def test_DATA_what_the_conditions_can_reach(runs):
    """Against 1976, II and III lie within the sun's largest rise times
    the pure water's; IB in the blue and the coastal types do not, and III
    against 1968 does not."""
    text = " ".join((ROOT / "DATA.md").read_text().split())
    reach = 1.207 * 1.062
    assert round(reach, 2) == 1.28
    assert "at most a factor of 1.28 (1.207 times 1.062)" in text
    base = base_runs(runs)

    def ratios(water_type, source):
        return [k / jerlov_kd(water_type, wl, source)
                for (t, wl), k in base.items() if t == water_type]
    for water_type in ("II", "III"):
        r = ratios(water_type, "jerlov1976")
        assert min(r) * reach >= 1 and max(r) * (1 - 0.071) * (1 - 0.12) <= 1
    assert min(ratios("III", "jerlov1968")) * reach < 1
    assert round(min(ratios("III", "jerlov1968")), 2) == 0.61
    assert min(ratios("3C", "jerlov1976")) * reach < 1
    assert max(ratios("IB", "jerlov1976")) * (1 - 0.071) * (1 - 0.12) > 1


def test_the_base_stations(runs):
    table, _ = runs
    stations = {r["water_type"]: r["station"] for r in table.values()
                if r["factor"] == "base"}
    assert stations == {"IB": "AUTEC 7", "II": "HAOCE 11", "III": "HAOCE 5",
                        "1C": "HAOCE 5", "3C": "HAOCE 5", "5C": "NUC 2240"}

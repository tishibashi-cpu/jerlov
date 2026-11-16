"""Why the blue end disagrees (DATA.md section 41, OPEN_QUESTIONS.md,
DECISIONS.md section 95): the tables reduced from Williamson & Hollins's
dataset, the Monte Carlo runs on the matched entries, and every figure the
documents quote, recomputed. Away from the source tree, all skipped."""

from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import math
import pathlib
import runpy
import sys
import warnings

import pytest

import jerlov

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "examples" / "data" / "blue_end"
pytestmark = pytest.mark.skipif(
    not (ROOT / "DATA.md").exists() or not DATA.exists()
    or not (ROOT / "tools" / "blue_end.py").exists(),
    reason="needs the source tree (DATA.md, examples/data and tools)")


def _flat(name):
    return " ".join((ROOT / name).read_text().split())


def _read(name):
    with open(DATA / name) as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def closure():
    module = runpy.run_path(str(ROOT / "examples" / "closure_with_jerlov_kd.py"),
                            run_name="closure_with_jerlov_kd")
    with contextlib.redirect_stdout(io.StringIO()), \
            warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        return module["main"]()["blue_end"]


# -- The tables --------------------------------------------------------------


def test_the_matched_set_is_figshares_file():
    digest = hashlib.md5((DATA / "matched.csv").read_bytes()).hexdigest()
    assert digest == "64fdbfcdad23c600375e62c472aa2bff"


def test_the_reduced_tables():
    kd = _read("kd_campaigns.csv")
    assert len(kd) == 15308
    assert len({r["campaign"] for r in kd}) == 2710
    counts = {}
    for r in kd:
        counts.setdefault(r["water_type"], set()).add(r["campaign"])
    # Williamson & Hollins's log: campaigns of each type.
    assert {t: len(c) for t, c in counts.items()} == {
        "I": 202, "IA": 296, "IB": 485, "II": 660, "III": 459, "1C": 223,
        "3C": 208, "5C": 67, "7C": 52, "9C": 58}
    iop = _read("iop_campaigns.csv")
    assert sum(r["quantity"] == "a" for r in iop) == 1708
    assert sum(r["quantity"] == "b" for r in iop) == 1674
    ib = {r["campaign"] for r in iop
          if r["water_type"] == "IB" and r["quantity"] == "a"}
    assert ib == {"292", "293", "1642", "1648", "1841", "1845"}
    # The averages shipped in williamson2022_measured come from these:
    # IB's a at 412 nm is the mean of its six campaigns.
    a412 = [float(r["value"]) for r in iop if r["water_type"] == "IB"
            and r["quantity"] == "a" and r["wavelength_nm"] == "412"]
    points = jerlov.measured_points("IB", "a")
    # (the shipped averages are rounded to six figures)
    assert sum(a412) / len(a412) == pytest.approx(points.values[0],
                                                  rel=1e-6)


def test_the_runs():
    runs = _read("runs.csv")
    assert len(runs) == 2365
    assert all(r["status"] == "ok" for r in runs)
    factors = {}
    for r in runs:
        factors[r["factor"]] = factors.get(r["factor"], 0) + 1
    assert factors == {"base": 473, "station": 946, "sun_deg": 946}
    assert min(float(r["kd_first_penetration_depth"]) / float(r["a"])
               for r in runs) > 1.1


def test_a_stored_run_is_reproduced():
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import kd_monte_carlo as mc
    finally:
        sys.path.remove(str(ROOT / "tools"))
    run = next(r for r in _read("runs.csv")
               if r["factor"] == "base" and r["campaign"] == "292"
               and r["wavelength_nm"] == "412")
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


# -- What the documents quote ------------------------------------------------


def test_the_campaigns_against_jerlov(closure):
    c = closure["campaigns"]

    def median(t, wl, source):
        return round(c[(t, wl, source)][0][1], 2)

    assert [median(t, 412, "jerlov1976") for t in ("1C", "3C", "5C")] == [
        0.59, 0.53, 0.56]
    assert [median(t, 443, "jerlov1976") for t in ("1C", "3C", "5C")] == [
        0.78, 0.72, 0.72]
    assert [median(t, 490, "jerlov1976") for t in ("1C", "3C", "5C")] == [
        1.03, 0.92, 0.91]
    assert [median(t, 412, "jerlov1968") for t in ("1C", "3C", "5C")] == [
        0.85, 0.66, 0.62]
    assert [median("IB", wl, "jerlov1976") for wl in (412, 443, 490)] == [
        1.02, 1.12, 1.03]
    e = closure["editions"]
    assert [round(e[(t, 425)], 2) for t in ("IB", "1C", "3C", "5C")] == [
        0.87, 0.65, 0.77, 0.89]
    data = _flat("DATA.md")
    for quoted in ("median 0.59, 0.53 and 0.56 of Jerlov's (1976)",
                   "at 443 nm 0.78, 0.72 and 0.72",
                   "by 490 nm they are 0.91 to 1.03",
                   "0.65 (1C), 0.77 (3C) and 0.89 (5C)",
                   "412 nm are a median 0.85, 0.66 and 0.62",
                   "median 1.02, 1.12 and 1.03 of Jerlov's (1976) at 412, 443 "
                   "and 490 nm", "15308 Kd values of the 2710 campaigns",
                   "473 entries", "2365 runs"):
        assert quoted in data, quoted
    oq = _flat("OPEN_QUESTIONS.md")
    for quoted in ("at 412 nm of a median 0.59, 0.53 and 0.56 of Jerlov's "
                   "(1976)", "0.85, 0.66 and 0.62 of his",
                   "measured Kd of 1.02 to 1.12 of Jerlov's (1976)"):
        assert quoted in oq, quoted
    readme = _flat("examples/README.md")
    assert "nm of **0.59** and 0.53 of Jerlov's (1976)" in readme


def test_the_matched_entries(closure):
    m = closure["matched"]
    base = {k: round(v[0], 2) for k, v in m["base"].items()}
    assert [base[(t, 412)] for t in ("1C", "3C", "5C", "IB")] == [
        0.90, 0.93, 1.06, 0.57]
    reach = {t: (round(m["reach"][(t, 412)][0], 2),
                 round(m["reach"][(t, 412)][1], 2))
             for t in ("1C", "3C", "5C")}
    assert reach == {"1C": (0.85, 1.01), "3C": (0.87, 1.04),
                     "5C": (1.0, 1.19)}
    assert m["not_run"] == 0
    assert m["above"] == {"IA": (3, 1), "IB": (11, 3), "II": (88, 9),
                          "III": (211, 30), "1C": (68, 0), "3C": (79, 3),
                          "5C": (12, 3), "7C": (1, 0)}
    data, oq = _flat("DATA.md"), _flat("OPEN_QUESTIONS.md")
    assert "a median 0.90, 0.93 and 1.06 of its own Kd at 412 nm (0.85 to " \
        "1.19 with the sun or the station varied)" in data
    assert "a median 0.57 of the measured Kd at 412 nm" in data
    for text in (data, oq):
        assert "30 of 211" in text or "30 of the 211" in text
    assert ("3 of 11 entries for IB, 9 of 88 for II, 30 of 211 for III, 3 of "
            "79 for 3C, 3 of 12 for 5C and none of 68 for 1C") in data
    assert ("30 of the 211 matched entries for Jerlov III, 9 of 88 for II, 3 "
            "of 11 for IB, 3 of 79 for 3C, 3 of 12 for 5C and none of 68 for "
            "1C") in oq
    assert "median 0.90, 0.93 and 1.06 of its own Kd" in oq


def test_ibs_six_campaigns(closure):
    ib = {(c, wl): (a, k) for c, wl, a, _, k in closure["ib"]}
    # At or above their own Kd: 292 at 440 and 510, 293 at 440, 510 and
    # 555.
    above = sorted(key for key, (a, k) in ib.items() if a >= k)
    assert above == [(292, 440), (292, 510), (293, 440), (293, 510),
                     (293, 555)]
    # A third of their own Kd at 412 nm.
    for campaign in (1841, 1845):
        a, k = ib[(campaign, 412)]
        assert 0.3 < a / k < 0.36
    assert {c for c, _ in ib} == {292, 293, 1642, 1648, 1841, 1845}
    assert {wl for c, wl in ib if c in (1642, 1648) and wl <= 510} == {488}


def test_the_spread(closure):
    spread = {(t, wl): (round(sds, 1), round(ses, 1))
              for t, wl, _, _, sds, ses in closure["spread"]}
    ib = [spread[("IB", wl)] for wl in (425, 450, 475, 500)]
    assert (min(s for s, _ in ib), max(s for s, _ in ib)) == (-1.8, -1.0)
    assert (min(e for _, e in ib), max(e for _, e in ib)) == (-4.3, -2.4)
    coastal = [spread[k][0] for k in (("1C", 425), ("3C", 425), ("3C", 450))]
    assert (min(coastal), max(coastal)) == (3.4, 5.2)
    assert spread[("5C", 425)][0] == 1.7
    n = closure["neighbours"]
    a = [v for (q, *_), v in n.items() if q == "a"]
    b = [v for (q, *_), v in n.items() if q == "b"]
    assert (round(min(a), 1), round(max(a), 1)) == (1.2, 2.1)
    assert (round(min(b), 1), round(max(b), 1)) == (0.9, 1.4)
    data, oq = _flat("DATA.md"), _flat("OPEN_QUESTIONS.md")
    assert "fall by 1.0 to 1.8 standard deviations" in data
    assert "(2.4 to 4.3 standard errors)" in data
    assert "rise by 3.4 to 5.2 standard deviations" in data
    assert "(1.7 for 5C)" in data
    assert "rises by 1.2 to 2.1 pooled standard deviations and b by 0.9 to " \
        "1.4" in data
    assert "1.0 to 1.8 standard deviations lower" in oq

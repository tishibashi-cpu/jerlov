"""tools/polarised_mc.py, a vector Monte Carlo, against Natraj et al.'s
(2009) tables, Kokhanovsky et al.'s (2010) benchmark, and
tools/polarised_ocean.py against Chowdhary et al.'s (2020) testbed:
DECISIONS.md sections 145 to 148, with tools/polarised_coupled.py."""

from __future__ import annotations

import csv
import math
import pathlib
import sys

import numpy as np
import pytest

from jerlov._data import trapezoid

ROOT = pathlib.Path(__file__).resolve().parent.parent
source_tree = pytest.mark.skipif(
    not (ROOT / "pyproject.toml").exists(),
    reason="not running from a source tree")


def _tool():
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import polarised_mc
    finally:
        sys.path.pop(0)
    return polarised_mc


def _section():
    text = " ".join((ROOT / "DECISIONS.md").read_text().split())
    return text.split("## 145. ")[1]


@source_tree
def test_the_tables_as_transcribed_hold_together():
    p = _tool()
    assert sum(len(v) for v in p.TABLES.values()) * len(p.PHIS) == 672
    for (level, q), rows in p.TABLES.items():
        assert [mu for mu, _ in rows] == list(p.MUS)
        for mu, values in rows:
            if q == "U":                 # in the principal plane, none
                assert values[0] == 0 and values[-1] == 0
            if mu == 1.0 and q == "I":   # straight up or down, one value
                assert len(set(values)) == 1
            if mu == 1.0 and q != "I":   # Q0 cos 2 phi and Q0 sin 2 phi
                q0 = dict(rows)[1.0][0] if q == "Q" else None
                if q == "Q":
                    want = [q0 * math.cos(2 * math.radians(f))
                            for f in p.PHIS]
                    assert np.allclose(values, want, atol=1e-8)
    top_q0 = dict(p.TABLES["top", "Q"])[1.0][0]
    top_u = dict(p.TABLES["top", "U"])[1.0]
    assert np.allclose(top_u, [top_q0 * math.sin(2 * math.radians(f))
                               for f in p.PHIS], atol=1e-8)


@source_tree
@pytest.mark.parametrize("tau, quoted", [(0.001, "1.51"), (0.5, "1.11")])
def test_single_scattering_is_the_exact_one(tau, quoted):
    p = _tool()
    runs = [p.run(10 + k, 100_000, tau=tau, orders=1) for k in range(20)]
    m = np.mean(runs, axis=0)
    se = np.std(runs, axis=0, ddof=1) / math.sqrt(20)
    exact = p.single_scattering(tau)
    worst = 0.0
    for i in range(3):
        ok = np.abs(exact[i]) > 1e-15
        z = np.abs(m[i] - exact[i])[ok] / se[i][ok]
        worst = max(worst, float(z.max()))
    assert worst <= 3
    assert np.all(m[3] == 0)
    assert f"{worst:.2f}" == quoted
    assert "at most 1.51 standard errors from it at optical thickness " \
        "0.001 and 1.11 at 0.5" in _section()


def _rows():
    path = ROOT / "examples" / "data" / "polarisation" / "natraj2009.csv"
    with path.open() as handle:
        return list(csv.DictReader(handle))


@source_tree
def test_the_tables_are_reproduced_as_quoted():
    p = _tool()
    rows = _rows()
    assert len(rows) == 224
    good, worst = 0, (0.0, None)
    same_sign_u = {"top": 0, "bottom": 0}
    for r in rows:
        for q in "IQU":
            t = dict(p.TABLES[r["level"], q])[float(r["mu"])][
                p.PHIS.index(float(r["phi"]))]
            x, se = float(r[q]), float(r[q + "_se"])
            good += abs(x - t) <= 3 * se + 2e-4
            if abs(x - t) > worst[0]:
                worst = (abs(x - t), r, q, se)
            if q == "U":
                same_sign_u[r["level"]] += abs(-x - t) <= 3 * se + 2e-4
    assert good == 672
    section = _section()
    assert "all 672 values agree" in section
    d, r, q, se = worst
    assert (q, r["level"], r["mu"]) == ("I", "top", "0.02")
    assert (f"The largest difference is {d:.5f} in I at the top for mu = "
            f"0.02, where the standard error is {se:.5f}") in section
    assert same_sign_u == {"top": 33, "bottom": 33}
    assert "33 of the 112 at each boundary agree" in section
    log = " ".join((ROOT / "CHANGELOG.md").read_text().split())
    assert "all 672 values of I, Q and U" in log


@source_tree
def test_the_scalar_error_is_quoted_as_run():
    rows = _rows()
    section = _section()
    log = " ".join((ROOT / "CHANGELOG.md").read_text().split())
    worst = 0.0
    for level, text in (("top", "at the top"), ("bottom", "at the bottom")):
        r = [x for x in rows if x["level"] == level]
        ratio = np.array([float(x["I_scalar"]) / float(x["I"]) for x in r])
        off = int(np.sum(np.abs(ratio - 1) > 0.05))
        assert f"{ratio.min():.3f} to {ratio.max():.3f} {text}" in section
        assert f"{off}" in section
        worst = max(worst, float(np.max(np.abs(ratio - 1))))
        se = max(math.hypot(float(x["I_scalar_se"]) / float(x["I_scalar"]),
                            float(x["I_se"]) / float(x["I"])) for x in r)
        assert se < 0.005
    assert f"up to {round(100 * worst)} percent" in section
    assert f"up to {round(100 * worst)} percent off" in log


# -- Kokhanovsky et al. (2010), DECISIONS.md section 146 --------------------

def _section_146():
    text = " ".join((ROOT / "DECISIONS.md").read_text().split())
    return text.split("## 146. ")[1]


def _kokhanovsky_rows():
    path = ROOT / "examples" / "data" / "polarisation" / \
        "kokhanovsky2010.csv"
    with path.open() as handle:
        return list(csv.DictReader(handle))


@source_tree
def test_kokhanovsky_s_tables_as_transcribed():
    p = _tool()
    assert sorted(p.K_TABLE_A1) == list(p.K_VZA)
    assert len(p.K_TABLE_A1) * 3 * 4 + len(p.K_TABLE_U90) * 2 == 84
    for v in p.K_VZA:
        rows = p.K_TABLE_A1[v]
        assert rows[0][0] > 0 and rows[0][2] > 0
        if v == 0.0:      # straight up or down: I one value, Q cos 2 phi
            assert rows[0][0] == rows[1][0] == rows[2][0]
            assert rows[0][1] == -rows[1][1] == rows[2][1]
            assert p.K_TABLE_U90[v] == (0.0, 0.0)


@source_tree
def test_the_tables_q_is_single_scattering_s_sign():
    """Light from the sun scattered straight up by Rayleigh scattering is
    polarised across the plane of the sun: in that reference plane I_perp
    exceeds I_par, so I_perp - I_par > 0 straight up, as Table A1 has it,
    where the paper's Eq. (2), I_par - I_perp, would be negative."""
    p = _tool()
    exact = p.single_scattering(p.K_TAU, mu0=p.K_MU0, mus=(1.0,),
                                phis=(0.0,))
    i_par_less_perp = exact[1, 0]          # this tool's Q, e1 meridional
    assert i_par_less_perp < 0
    assert p.K_TABLE_A1[0.0][0][1] > 0
    assert p.TO_KOKHANOVSKY[1] < 0
    assert "The tables' Q has the opposite sign of the paper's Eq. (2)" in \
        _section_146().replace("**", "")


@source_tree
def test_kokhanovsky_s_values_are_reproduced_as_quoted():
    p = _tool()
    rows = _kokhanovsky_rows()
    assert len(rows) == 36
    good, worst = 0, (0.0,)
    for r in rows:
        v, phi = float(r["vza"]), float(r["phi"])
        top = r["level"] == "top"
        row = p.K_TABLE_A1[v][p.K_PHIS.index(phi)]
        pairs = [("I", row[0] if top else row[2]),
                 ("Q", row[1] if top else row[3])]
        if phi == 90.0:
            pairs.append(("U", p.K_TABLE_U90[v][0 if top else 1]))
        for q, t in pairs:
            x, se = float(r[q]), float(r[q + "_se"])
            good += abs(x - t) <= 3 * se + 2e-4
            if abs(x - t) > worst[0]:
                worst = (abs(x - t), q, r["level"], v, phi, se)
    assert good == 84
    section = _section_146()
    assert "all 84 values agree" in section
    d, q, level, v, phi, se = worst
    assert (f"The largest difference is {d:.5f} in {q} at the {level} at "
            f"{v:.0f} degrees and azimuth {phi:.0f}, where the standard "
            f"error is {se:.5f}") in section
    for level, text in (("top", "at the top"), ("bottom", "at the bottom")):
        sel = [x for x in rows if x["level"] == level]
        ratio = np.array([float(x["I_scalar"]) / float(x["I"]) for x in sel])
        assert f"{ratio.min():.3f} to {ratio.max():.3f} {text}" in section
    log = " ".join((ROOT / "CHANGELOG.md").read_text().split())
    assert "all 84 values" in log


# -- Chowdhary et al. (2020), DECISIONS.md section 147 ----------------------

def _ocean():
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import polarised_ocean
    finally:
        sys.path.pop(0)
    return polarised_ocean


def _section_147():
    text = " ".join((ROOT / "DECISIONS.md").read_text().split())
    return text.split("## 147. ")[1]


def _csv(name):
    path = ROOT / "examples" / "data" / "polarisation" / name
    with path.open() as handle:
        return list(csv.DictReader(handle))


def _testbed():
    """Section 147's tables: AOS-I and AOS-II just above the surface."""
    return {(r["model"], r["wavelength"], r["sun"], r["phi"], r["vza"]): r
            for r in _csv("chowdhary2020_tables.csv")
            if r["model"] in ("AOS-I", "AOS-II") and r["level"] == "SRF"}


def _misprint(t):
    return t["U"] == t["I"] and float(t["U"]) != 0


@source_tree
def test_fresnel_s_matrices_keep_the_flux():
    o = _ocean()
    rng = np.random.default_rng(1)
    worst, total = 0.0, 0
    for n1, n2 in ((1.0, o.N_WATER), (o.N_WATER, 1.0)):
        ci = rng.random(10_000)
        S = rng.normal(size=(4, 10_000))
        S[0] = np.linalg.norm(S[1:], axis=0) * (1 + rng.random(10_000))
        rp, rs, tp, ts, ct = o.fresnel(ci, n1, n2)
        flux = o.reflect_matrix(S, rp, rs).real[0] + \
            o.transmit_matrix(S, tp, ts, ci, ct, n1, n2)[0]
        worst = max(worst, float(np.max(np.abs(flux - S[0]) / S[0])))
        total += int(np.sum(ct == 0))
    assert worst < 1e-12
    assert total == 6658
    assert f"to {worst:.1e}" in _section_147()
    assert "(6658 of those from the water totally reflected)" in \
        _section_147()


@source_tree
def test_the_testbed_as_read():
    rows = _csv("chowdhary2020_tables.csv")
    assert len(rows) == 2800
    assert len(_testbed()) == 800
    bad = [r for r in rows if _misprint(r)]
    assert len(bad) == 25
    assert {(r["model"], r["wavelength"], r["sun"]) for r in bad} == \
        {("AOS-II", "450", "60")}
    assert {r["phi"] for r in bad} == {"0", "180"}
    for r in rows:                   # in the principal plane U is zero
        if r["phi"] in ("0", "180") and not _misprint(r):
            assert float(r["U"]) == 0
    assert "(azimuths 0 and 180, 25 values) repeats R_I,Vector" in \
        _section_147()


@source_tree
def test_the_glint_alone_as_quoted():
    o = _ocean()
    ref = _testbed()
    dirs = o.directions()
    n = ok = 0
    rest = []
    for sun in (30, 60):
        g = o.glint(sun) * np.array(o.TO_TESTBED)[:, None]
        for j, (phi, vza, _, _) in enumerate(dirs):
            t = float(ref["AOS-II", "650", str(sun), str(int(phi)),
                          str(int(vza))]["I"])
            if g[0, j] > 0.9 * t:
                n += 1
                ok += abs(g[0, j] / t - 1) <= 0.02
                rest.append(t - g[0, j])
    assert (ok, n) == (32, 40)
    section = _section_147()
    assert "Not met as set: 32 of 40." in section
    assert (f"exceed the closed-form glint by {min(rest) * 1e4:.1f}e-4 to "
            f"{max(rest) * 1e4:.1f}e-4") in section


@source_tree
def test_the_testbed_is_reproduced_as_quoted():
    ref = _testbed()
    run = _csv("chowdhary2020.csv")
    assert len(run) == 800
    section = _section_147()
    found = {}
    for model in ("AOS-I", "AOS-II"):
        good = total = sgood = 0
        worst = (0.0,)
        ratios = []
        for r in (x for x in run if x["model"] == model):
            t = ref[model, r["wavelength"], r["sun"], r["phi"], r["vza"]]
            for q in "IQU":
                if q == "U" and _misprint(t):
                    continue
                x, se, v = float(r[q]), float(r[q + "_se"]), float(t[q])
                total += 1
                good += abs(x - v) <= 3 * se + 1e-5
                if abs(x - v) > worst[0]:
                    worst = (abs(x - v), q, r, se)
            x, se = float(r["I_scalar"]), float(r["I_scalar_se"])
            sgood += abs(x - float(t["I_scalar"])) <= 3 * se + 1e-5
            ratios.append(float(r["I_scalar"]) / float(r["I"]))
        found[model] = (good, total, sgood, worst, np.array(ratios))
    assert found["AOS-I"][:3] == (1198, 1200, 398)
    assert found["AOS-II"][:3] == (1175, 1175, 400)
    assert "Met: AOS-I 1198 of 1200 values, AOS-II all 1175" in section
    assert "Met: AOS-I 398 of 400, AOS-II all 400." in section
    for model, (text, spread) in {
            "AOS-I": ("for AOS-I at 450 nm, the sun at 60 degrees, azimuth "
                      "180 and 60 degrees viewing, where the standard error "
                      "is", "0.595 to 1.462 for AOS-I"),
            "AOS-II": ("at 350 nm, the sun at 30 degrees, azimuth 180 and "
                       "60 degrees viewing", "0.938 to 1.047 for AOS-II")
            }.items():
        d, q, r, se = found[model][3]
        assert q == "I"
        if model == "AOS-I":
            assert f"{d:.5f} in I {text}" in section
        else:
            assert f"for AOS-II {d:.5f} in I {text}" in section
        assert f"{se:.5f}" in section
        ratio = found[model][4]
        assert f"{ratio.min():.3f} to {ratio.max():.3f} for {model}" \
            == spread
        assert spread in section
    assert int(np.sum(np.abs(found["AOS-I"][4] - 1) > 0.05)) == 187
    assert int(np.sum(np.abs(found["AOS-II"][4] - 1) > 0.05)) == 22
    log = " ".join((ROOT / "CHANGELOG.md").read_text().split())
    assert "1198 of 1200" in log and "all 1175" in log


# -- the coupled atmosphere and ocean, DECISIONS.md section 148 -------------

def _coupled():
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import polarised_coupled
    finally:
        sys.path.pop(0)
    return polarised_coupled


def _section_148():
    text = " ".join((ROOT / "DECISIONS.md").read_text().split())
    return text.split("## 148. ")[1]


def _copied(r, quantity):
    """The supplement's copying errors (DATA.md section 54)."""
    key = (r["model"], r["level"], r["wavelength"], r["sun"])
    off_plane = r["phi"] in ("60", "240")
    if quantity == "U" and r["U"] == r["I"] and float(r["U"]) != 0:
        return True
    if key == ("AOS-I", "TOA", "650", "60") and off_plane:
        return quantity == "I_scalar"
    if key == ("AOS-III", "SRF", "450", "30") and off_plane:
        return quantity in ("I", "Q", "U")
    return False


@source_tree
def test_the_copied_columns_are_copies():
    rows = _csv("chowdhary2020_tables.csv")
    index = {(r["model"], r["level"], r["wavelength"], r["sun"], r["phi"],
              r["vza"]): r for r in rows}
    n = {"I_scalar": 0, "I": 0, "Q": 0, "U": 0}
    for r in rows:
        for q in n:
            if not _copied(r, q):
                continue
            n[q] += 1
            if r["model"] == "AOS-I":
                src = index["AOS-I", "SRF", "650", "60", r["phi"], r["vza"]]
                assert r[q] == src[q]
            elif r["model"] == "AOS-III":
                src = index["AOS-III", "SRF", "350", "30", r["phi"], r["vza"]]
                assert r[q] == src[q]
    assert n == {"I_scalar": 25, "I": 25, "Q": 25, "U": 50}
    assert "the 450 nm columns R_I, R_Q and R_U (75 values) are the 350 nm " \
        "columns beside them" in _section_148()


@source_tree
def test_the_particles_matrix_as_quoted():
    pc = _coupled()
    section = _section_148()
    found = []
    for table in ("S1a", "S1b"):
        p = pc.Particles(table)
        assert p.angle.size == 271
        g = p.grid
        f = p.phase(np.cos(g))
        asym = trapezoid(f * np.sin(g) * np.cos(g), g) * 2 * math.pi
        back = g >= math.pi / 2
        bb = trapezoid((f * np.sin(g))[back], g[back]) * 2 * math.pi
        found.append((p.integral, asym, bb))
    assert (f"integrates to {found[0][0]:.5f} (S1a) and {found[1][0]:.5f} "
            "(S1b)") in section
    assert (f"asymmetry parameters {found[0][1]:.3f} and {found[1][1]:.3f}"
            in section)
    assert f"is {found[1][2]:.5f} for S1b" in section
    assert f"but {found[0][2]:.5f} for S1a" in section
    assert round(found[0][2], 4) == 0.0109 and round(found[1][2], 4) == 0.0058


@source_tree
def test_depolarisation_as_quoted():
    p = _tool()
    worst = 0.0
    for delta in (0.0, 0.039, 0.09):
        S = np.array([[1.0], [0.0], [0.0], [0.0]])
        out = p._rayleigh(S, np.array([0.0]), True, delta)
        worst = max(worst, abs(abs(out[1, 0]) / out[0, 0]
                               - (1 - delta) / (1 + delta)))
    assert worst <= 2.3e-16
    x = np.linspace(-1, 1, 200_001)
    S = np.zeros((4, x.size))
    S[0] = 1
    norm = trapezoid(p._rayleigh(S, x, True, 0.09)[0], x) * 2 * math.pi
    assert abs(norm - 1) < 1.2e-11
    rng = np.random.default_rng(5)
    ks = []
    for delta in (0.0, 0.039, 0.09):
        c = np.sort(p._draw_rayleigh_cos(rng, 1_000_000, delta))
        D = (1 - delta) / (1 + delta / 2)
        F = D * (c ** 3 + 3 * c + 4) / 8 + (1 - D) * (c + 1) / 2
        n = c.size
        stat = max(np.max(np.arange(1, n + 1) / n - F),
                   np.max(F - np.arange(n) / n)) * math.sqrt(n)
        assert stat < 1.36
        ks.append(f"{stat:.2f}")
    assert "sqrt(n) D = 1.01, 0.89 and 0.87" in _section_148()
    assert ks == ["1.01", "0.89", "0.87"]


@source_tree
def test_the_coupled_testbed_is_reproduced_as_quoted():
    ref = {(r["model"], r["level"], r["wavelength"], r["sun"], r["phi"],
            r["vza"]): r for r in _csv("chowdhary2020_tables.csv")}
    run = _csv("chowdhary2020_coupled.csv")
    assert len(run) == 2800
    counts, worst, ratios = {}, {}, {}
    for r in run:
        key = (r["model"], r["level"])
        t = ref[key + (r["wavelength"], r["sun"], r["phi"], r["vza"])]
        tol = 2e-5 if r["model"] == "AOS-IV" else 1e-5
        c = counts.setdefault(key, [0, 0, 0, 0])
        for q in "IQU":
            if _copied(t, q):
                continue
            x, se, v = float(r[q]), float(r[q + "_se"]), float(t[q])
            c[1] += 1
            c[0] += abs(x - v) <= 3 * se + tol
            if abs(x - v) > worst.get(key, (0.0,))[0]:
                worst[key] = (abs(x - v), q, r, se)
        if not _copied(t, "I_scalar"):
            x, se = float(r["I_scalar"]), float(r["I_scalar_se"])
            c[3] += 1
            c[2] += abs(x - float(t["I_scalar"])) <= 3 * se + tol
        ratios.setdefault(key, []).append(float(r["I_scalar"])
                                          / float(r["I"]))
    assert counts == {
        ("AOS-I", "SRF"): [1197, 1200, 400, 400],
        ("AOS-I", "TOA"): [1199, 1200, 375, 375],
        ("AOS-II", "SRF"): [1175, 1175, 400, 400],
        ("AOS-III", "SRF"): [1119, 1125, 399, 400],
        ("AOS-III", "TOA"): [1196, 1200, 390, 400],
        ("AOS-IV", "SRF"): [1179, 1200, 387, 400],
        ("AOS-IV", "TOA"): [1185, 1200, 396, 400]}
    for good, total, sgood, stotal in counts.values():
        assert good >= 0.95 * total and sgood >= 0.95 * stotal
    section = _section_148()
    for phrase in ("1197 of 1200 vector values, all 400 scalar",
                   "AOS-II: all 1175 and all 400",
                   "1199 of 1200, and all 375 scalar values",
                   "1119 of 1125 vector values (the copied 75 out), 399 of "
                   "400 scalar; at the top: 1196 of 1200 and 390 of 400",
                   "1179 of 1200 and 387 of 400; at the top: 1185 of 1200 "
                   "and 396 of 400"):
        assert phrase in section
    for key, where in ((("AOS-IV", "SRF"), "just above the surface"),
                       (("AOS-IV", "TOA"), "at the top")):
        d, q, r, se = worst[key]
        assert q == "I"
        assert f"{d:.5f}" in section and f"{se:.5f}" in section
    for key, text in ((("AOS-III", "SRF"), "AOS-III {} just above"),
                      (("AOS-IV", "SRF"), "AOS-IV {} and"),
                      (("AOS-I", "TOA"), "AOS-I at the top {}")):
        ratio = np.array(ratios[key])
        assert text.format(f"{ratio.min():.3f} to {ratio.max():.3f}") \
            in section
    for key, text in ((("AOS-III", "TOA"), "and {} at the top;"),
                      (("AOS-IV", "TOA"), "and {};")):
        ratio = np.array(ratios[key])
        assert text.format(f"{ratio.min():.3f} to {ratio.max():.3f}") \
            in section
    log = " ".join((ROOT / "CHANGELOG.md").read_text().split())
    assert "1119 of 1125" in log and "1179 and 1185 of 1200" in log

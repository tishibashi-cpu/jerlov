"""tools/polarised_mc.py, a vector Monte Carlo, against Natraj et al.'s
(2009) tables: DECISIONS.md section 145."""

from __future__ import annotations

import csv
import math
import pathlib
import sys

import numpy as np
import pytest

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

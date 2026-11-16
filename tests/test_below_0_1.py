"""What rests on Petzold's extension below 0.1 degree (DATA.md section 21,
OPEN_QUESTIONS.md, DECISIONS.md section 96): the Monte Carlo runs and the
figures the documents quote. Away from the source tree, all skipped."""

from __future__ import annotations

import contextlib
import csv
import io
import pathlib
import runpy
import sys
import warnings

import pytest

import jerlov

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "examples" / "data" / "below_0_1"
pytestmark = pytest.mark.skipif(
    not (ROOT / "DATA.md").exists() or not DATA.exists()
    or not (ROOT / "tools" / "below_0_1.py").exists(),
    reason="needs the source tree (DATA.md, examples/data and tools)")


def _flat(name):
    return " ".join((ROOT / name).read_text().split())


@pytest.fixture(scope="module")
def runs():
    with open(DATA / "runs.csv") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def extension():
    module = runpy.run_path(str(ROOT / "examples" / "phase_function_choice.py"),
                            run_name="phase_function_choice")
    with contextlib.redirect_stdout(io.StringIO()), \
            warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        return module["main"]()["extension"]


def test_the_runs(runs):
    assert len(runs) == 96
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        for r in runs:
            f = jerlov.petzold_scattering(r["station"]).fraction_below_0_1_deg
            assert float(r["fraction_below_0_1_deg"]) == f
            expected = 0.1 * float(r["b_over_a"]) * (
                1 - f if r["variant"] == "unscattered" else 1)
            assert float(r["b"]) == pytest.approx(expected, rel=1e-12)
    seeds = {}
    for r in runs:
        seeds.setdefault((r["station"], r["b_over_a"]), set()).add(r["seed"])
    assert all(len(s) == 1 for s in seeds.values())


def test_a_stored_run_without_the_extension_is_reproduced(runs):
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import kd_monte_carlo as mc
    finally:
        sys.path.remove(str(ROOT / "tools"))
    run = next(r for r in runs if r["station"] == "AUTEC 7"
               and r["b_over_a"] == "1" and r["variant"] == "unscattered")
    sample, _ = mc.petzold_sampler(run["station"], without_extension=True)
    (k,) = mc.kd(float(run["a"]), float(run["b"]), sample,
                 float(run["sun_deg"]), photons=int(run["photons"]),
                 seed=int(run["seed"]))
    assert k == pytest.approx(float(run["kd_first_penetration_depth"]),
                              rel=1e-9)


def test_the_figures(extension):
    e = extension
    assert (round(-e["dg"][1], 3), round(-e["dg"][0], 3)) == (0.004, 0.015)
    assert (round(100 * e["dbs"][0], 1), round(100 * e["dbs"][1], 1)) == (
        3.5, 17.0)
    assert (round(-e["dhg"][1], 3), round(-e["dhg"][0], 3)) == (0.004, 0.016)
    assert (round(100 * e["unscattered"][0], 2),
            round(100 * e["unscattered"][1], 2)) == (-0.63, 0.13)
    assert (round(100 * e["spread"][0], 2),
            round(100 * e["spread"][1], 2)) == (0.11, 4.40)
    assert max(abs(x) for x in e["unscattered"]) < 0.01  # DECISIONS 96
    data = _flat("DATA.md")
    for quoted in ("the mean cosine at the eight stations falls by 0.004 to "
                   "0.015, B/S rises by 3.5 to 17.0 percent",
                   "falls by 0.004 to 0.016", "-0.63 to +0.13 percent",
                   "by +0.11 to +4.40"):
        assert quoted in data, quoted
    oq = _flat("OPEN_QUESTIONS.md")
    assert "falls by 0.004 to 0.015 and B/S rises by 3.5 to 17.0 percent" in oq
    assert "moves by -0.63 to +0.13 percent" in oq
    readme = _flat("examples/README.md")
    assert "cosine falls by 0.004 to 0.015 and B/S rises by 3.5 to 17.0" in (
        readme)
    assert "**-0.63 to +0.13** percent" in readme


def test_the_literature_is_quoted_with_its_pages():
    data = _flat("DATA.md")
    for quoted in ("(1976, *Marine Optics*, p. 133)", "(p. 137)",
                   "pp. 122 and 124", "doi:10.5697/oc.55-2.471, p. 477",
                   "43(2), 139-168, p. 146",
                   "Rep. Dept. Phys. Oceanogr. 36, Univ. Copenhagen, 46 pp."):
        assert quoted in data, quoted

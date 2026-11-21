"""Why the shallow-water model misses two groups of the Monte Carlo's runs:
DECISIONS.md section 114, OPEN_QUESTIONS.md question 5, DATA.md section
50. Everything here reads the repository's examples/ and tools/."""

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
DATA = ROOT / "examples" / "data" / "shallow_rrs_mc"
pytestmark = pytest.mark.skipif(
    not (ROOT / "pyproject.toml").exists(),
    reason="not running from a source tree")


@pytest.fixture(scope="module")
def result():
    with contextlib.redirect_stdout(io.StringIO()):
        module = runpy.run_path(str(ROOT / "examples" /
                                    "shallow_water_closure.py"),
                                run_name="shallow_water_closure")
        return module["main"]()


def _flat(name):
    return " ".join((ROOT / name).read_text().split())


def _tool(name):
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        return __import__(name)
    finally:
        sys.path.pop(0)


def test_the_rebuilt_runs_are_what_the_tool_writes():
    rows = _tool("lee1998_runs").rows()
    with (DATA / "lee1998_runs.csv").open() as f:
        stored = list(csv.DictReader(f))
    assert len(rows) == len(stored) == 576
    for got, want in zip(rows, stored):
        assert {k: str(v) for k, v in got.items()} == want


def test_table_2_as_transcribed_gives_af_440_back():
    # Eq. (12) at 440 nm must return af(440) itself: a0 = 1, a1 = 0.
    assert _tool("lee1998_runs").TABLE2[440] == (1.0, 0.0)


@pytest.mark.parametrize("name", ["water_share.csv", "black_bottom.csv"])
def test_the_stored_model_column_is_today_s_function(name):
    with (DATA / name).open() as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        depth = float(r["depth_m"])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
            m = jerlov.lee1999_shallow_rrs(
                float(r["a"]), float(r["bb"]),
                depth_m=depth if math.isfinite(depth) else 1.0,
                bottom_albedo=0.0, sun_zenith_deg=float(r.get("sun_deg", 30.0)))
        want = m.rrs if math.isfinite(depth) else m.deep
        assert float(r["model"]) == pytest.approx(want, rel=2e-5)


def test_the_sky_option_off_repeats_the_grid_bit_for_bit():
    mc = _tool("shallow_rrs_mc")
    phase = mc.petzold_phase(mc.STATION)
    with (DATA / "monte_carlo.csv").open() as f:
        row = next(csv.DictReader(f))
    value, error = mc.rrs(float(row["a"]), float(row["bp"]),
                          float(row["bw"]), float(row["depth_m"]),
                          float(row["albedo"]), float(row["sun_deg"]), phase,
                          sky_share=0.0)
    assert f"{value:.6e}" == row["monte_carlo"]
    assert f"{error:.2e}" == row["standard_error"]


def test_open_questions_quotes_the_example(result):
    text = _flat("OPEN_QUESTIONS.md")
    section = text.split("## 5. ")[1]
    p, s, d = result["paper"], result["share"], result["dark"]
    assert f"at most {p['share_max']:.2f}" in section
    assert ("have " + " and ".join(f"{x:g}" for x in p["water_shares"])
            ) in section
    assert (f"{p['missed'][0]:.3f} to {p['missed'][1]:.3f} of the Monte "
            "Carlo") in section
    assert f"in {s['falling']} of {s['cases']} cases" in section
    assert (f"from {s['zero'][0]:.3f}-{s['zero'][1]:.3f} with particles "
            f"alone to {s['most'][0]:.3f}-{s['most'][1]:.3f}") in section
    assert (f"ratio is still {s['inside'][0]:.3f} to {s['inside'][1]:.3f}"
            ) in section
    assert (f"for {p['covered']} of its {p['dark']} runs") in section
    assert (f"{d['small'][0]:.2f} to {d['small'][1]:.2f} of the model's "
            f"where kappa H is below 0.1, and {d['large'][0]:.2f} to "
            f"{d['large'][1]:.2f} where it is above 0.5") in section
    c = d["counts"]
    assert d["accounted"] == []
    assert (f"HAOCE 11's phase function brought {c['HAOCE 11'][0]}, AUTEC "
            f"8's {c['AUTEC 8'][0]}, the sky {c['sky'][0]}, the 1998 "
            f"constants {c['1998 constants'][0]}") in section
    assert (f"factor of {d['spread'][0]:.2f} in the median cell and "
            f"{d['spread'][1]:.2f} at the most; adding the sky, by "
            f"{d['sky_spread'][0]:.2f} and {d['sky_spread'][1]:.2f}"
            ) in section


def test_the_trend_read_off_at_the_group_s_shares(result):
    s = result["share"]
    decisions = _flat("DECISIONS.md").split("## 114. ")[1]
    missed = result["paper"]["missed"]
    assert (f"({s['at_their'][0]:.3f} to {s['at_their'][1]:.3f}, against "
            f"the misses' {missed[0]:.3f} to {missed[1]:.3f})") in decisions
    assert f"it is {s['inside'][0]:.3f} to {s['inside'][1]:.3f}, not" in \
        decisions


def test_decisions_and_data_quote_the_same(result):
    c = result["dark"]["counts"]
    decisions = _flat("DECISIONS.md").split("## 114. ")[1]
    assert (f"HAOCE 11 brought {c['HAOCE 11'][0]} of the 13 within 10 "
            f"percent, AUTEC 8 and the sky {c['AUTEC 8'][0]}, the 1998 "
            f"constants {c['1998 constants'][0]}") in decisions
    assert c["AUTEC 8"][0] == c["sky"][0]
    assert (f"by {result['dark']['excess']:.1f} times the standard error"
            ) in decisions
    data = _flat("DATA.md").split("## 50. ")[1]
    assert (f"give pure water at most {result['paper']['share_max']:.2f} of "
            "bb") in data
    assert (f"in {result['share']['falling']} of "
            f"{result['share']['cases']} cases") in data
    assert f"factor of up to {result['dark']['spread'][1]:.2f}" in data


def test_the_readmes_and_the_site_quote_the_same(result):
    s, d = result["share"], result["dark"]
    readme = _flat("examples/README.md")
    assert (f"from **{s['zero'][0]:.3f}-{s['zero'][1]:.3f}** with particles "
            f"alone to {s['most'][0]:.3f}-{s['most'][1]:.3f}") in readme
    assert f"factor of up to **{d['spread'][1]:.2f}**" in readme
    site = _flat("docs/open_questions.rst")
    assert f"factor of up to {d['spread'][1]:.2f}" in site


def test_the_changelog_quotes_the_same(result):
    d = result["dark"]
    text = _flat("CHANGELOG.md").split("## 1.26.1")[1].split("## 1.26.0")[0]
    assert f"factor of up to {d['spread'][1]:.2f}" in text
    assert (f"{result['share']['falling']} of {result['share']['cases']}"
            ) in text

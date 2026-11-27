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
    text = _flat("CHANGELOG.md").split("## 1.26.1 ")[1].split("## 1.26.0")[0]
    assert f"factor of up to {d['spread'][1]:.2f}" in text
    assert (f"{result['share']['falling']} of {result['share']['cases']}"
            ) in text


# -- DECISIONS.md section 115 --------------------------------------------------

@pytest.mark.parametrize("name", ["water_share_nadir.csv", "cut_check.csv"])
def test_the_new_runs_model_column_is_today_s_function(name):
    with (DATA / name).open() as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        depth = float(r["depth_m"])
        sun = float(r.get("sun_deg", 0.0))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
            m = jerlov.lee1999_shallow_rrs(
                float(r["a"]), float(r["bb"]),
                depth_m=depth if math.isfinite(depth) else 1.0,
                bottom_albedo=0.0, sun_zenith_deg=sun)
        want = m.rrs if math.isfinite(depth) else m.deep
        assert float(r["model"]) == pytest.approx(want, rel=2e-5)


def test_the_cut_check_stores_the_sampler_s_shares():
    mc = _tool("shallow_rrs_mc")
    with (DATA / "cut_check.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 9
    for r in rows:
        phase = mc.petzold_phase(r["station"], float(r["cut_deg"]))
        assert float(r["share_below_cut"]) == pytest.approx(phase[2],
                                                            rel=1e-5)
        assert float(r["backscatter_share"]) == pytest.approx(phase[3],
                                                              rel=1e-5)
    below = {r["station"]: float(r["share_below_cut"]) for r in rows
             if float(r["cut_deg"]) == 1.0}
    decisions = _flat("DECISIONS.md").split("## 115. ")[1]
    assert (f"({below['HAOCE 11']:.3f}, {below['NUC 2240']:.3f} and "
            f"{below['AUTEC 8']:.3f} below 1 degree at HAOCE 11, NUC 2240 "
            "and AUTEC 8)") in decisions


def test_section_115_figures_are_quoted_as_computed(result):
    s = result["separated"]
    oq = _flat("OPEN_QUESTIONS.md").split("## 5. ")[1]
    data = _flat("DATA.md").split("## 50. ")[1]
    decisions = _flat("DECISIONS.md").split("## 115. ")[1]
    log = _flat("CHANGELOG.md").split("## 1.26.2")[1].split("## 1.26.1")[0]
    moves = (f"by {s['spread_2011'][0]:.3f} to {s['spread_2011'][1]:.3f} "
             "times against the Monte Carlo")
    old = f"by {s['spread_1999'][0]:.3f} to {s['spread_1999'][1]:.3f}"
    for text in (oq, data, log):
        assert moves in text
        assert old in text
    assert (f"lies at {s['q2011'][0]:.3f} to {s['q2011'][1]:.3f} of the "
            "Monte Carlo") in oq
    assert (f"is {s['fraction'][0]:.2f} to {s['fraction'][1]:.2f} of the "
            "1999 model's") in decisions
    assert s["fraction"][1] <= 1 / 3          # the plan's test, met
    rising = f"rises with bb/b in {s['rising']} of the {s['cells']} cells " \
        f"and falls in {'none' if s['falling'] == 0 else s['falling']}"
    assert rising in oq
    assert s["rising"] < 20 and s["falling"] < 20   # the plan's test, missed
    assert (f"in {s['middle']} the middle station, {s['by_back'][1]}, gives "
            "the highest") in oq
    assert s["cosine_falls"]
    assert f"by a factor of {s['cut_spread']:.3f} at most" in oq
    assert f"by a factor of {s['cut_spread']:.3f} at most" in data
    assert f"by a factor of {s['cut_spread']:.3f} at most" in decisions
    assert (f"({s['at_cut_cell']:.2f} there, {s['largest']:.2f} at a 0.2 "
            "1/m)") in decisions
    assert f"rises with bb/b in {s['rising']} of {s['cells']} cells" in log
    assert f"rises with the particles' bb/b in {s['rising']} of " \
        f"{s['cells']} cells" in data


# -- Section 134: the shape apart from bb/b, with Fournier-Forands ----------

def _ff_rows():
    with (DATA / "fournier_forand.csv").open() as f:
        return list(csv.DictReader(f))


def test_the_fournier_forand_runs_hold_all_but_the_shape():
    mc = _tool("shallow_rrs_mc")
    rows = _ff_rows()
    assert len(rows) == 72
    for station in ("NUC 2240", "AUTEC 8", "HAOCE 11"):
        back = mc.petzold_phase(station)[3]
        ff = jerlov.mobley2002_fournier_forand(back)
        phase = mc.fournier_forand_phase(ff)
        assert phase[3] == pytest.approx(back, abs=1e-6)
        for r in rows:
            if r["station"] == station:
                assert float(r["backscatter_share"]) == pytest.approx(
                    back, rel=1e-5)
                assert float(r["refractive_index"]) == pytest.approx(
                    ff.refractive_index, rel=1e-5)
                bb = float(r["bb"])
                assert float(r["bp"]) == pytest.approx(
                    (bb - 0.5 * float(r["bw"])) / back, rel=1e-5)
    # bp and bb are the station's run's: the black-bottom file's.
    with (DATA / "black_bottom.csv").open() as f:
        stored = {(r["a"], r["bp_over_a"], r["depth_m"], r["sun_deg"],
                   r["change"]): r for r in csv.DictReader(f)}
    for r in rows:
        key = (r["a"], r["bp_over_a"], r["depth_m"], r["sun_deg"],
               r["station"])
        if key in stored:
            assert r["bp"] == stored[key]["bp"]
            assert r["bb"] == stored[key]["bb"]


def test_a_stored_fournier_forand_run_is_reproduced():
    mc = _tool("shallow_rrs_mc")
    r = next(x for x in _ff_rows() if x["station"] == "AUTEC 8")
    # As the tool builds them, not from the rounded columns.
    back = mc.petzold_phase("AUTEC 8")[3]
    a = float(r["a"])
    bb = 0.5 * mc.BW + mc.petzold_phase(mc.STATION)[3] * float(
        r["bp_over_a"]) * a
    ff = jerlov.mobley2002_fournier_forand(back)
    value, error = mc.rrs(a, (bb - 0.5 * mc.BW) / back, mc.BW,
                          float(r["depth_m"]), 0.0, float(r["sun_deg"]),
                          mc.fournier_forand_phase(ff))
    assert f"{value:.6e}" == r["monte_carlo"]
    assert f"{error:.2e}" == r["standard_error"]


def test_the_fournier_forand_sampler_is_its_closed_form():
    import numpy as np
    mc = _tool("shallow_rrs_mc")
    ff = jerlov.mobley2002_fournier_forand(0.0183)
    sample, pdf, below, back = mc.fournier_forand_phase(ff)
    assert below == pytest.approx(float(ff.cumulative(1.0)), rel=1e-12)
    draws = np.degrees(sample(np.random.default_rng(1).random(400_000)))
    assert draws.min() >= 1.0 - 1e-9
    for cone in (5.0, 30.0, 90.0):
        want = (float(ff.cumulative(cone)) - below) / (1 - below)
        assert float(np.mean(draws <= cone)) == pytest.approx(want,
                                                              abs=0.003)
    angle = np.radians(np.array([10.0, 90.0, 170.0]))
    np.testing.assert_allclose(
        pdf(angle), np.asarray(ff.phase_function(np.degrees(angle)))
        / (1 - below), rtol=1e-3)


def test_the_fournier_forand_model_column_is_today_s_function():
    for r in _ff_rows():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
            m = jerlov.lee1999_shallow_rrs(
                float(r["a"]), float(r["bb"]), depth_m=float(r["depth_m"]),
                bottom_albedo=0.0, sun_zenith_deg=float(r["sun_deg"]))
        assert float(r["model"]) == pytest.approx(m.rrs, rel=2e-5)


def test_section_134_figures_are_quoted_as_computed(result):
    f = result["fournier"]
    v = [x for values in f["by_station"].values() for x in values]
    span = f"{min(v):.2f} to {max(v):.2f}"
    assert span == "0.49 to 1.09"
    oq = _flat("OPEN_QUESTIONS.md").split("## 5. ")[1].split("## 6. ")[0]
    data = _flat("DATA.md").split("## 50. ")[1].split("## 51. ")[0]
    decisions = _flat("DECISIONS.md").split("## 134. ")[1]
    log = _flat("CHANGELOG.md").split("## 1.32.2")[1].split("## 1.32.1")[0]
    readme = _flat("examples/README.md")
    site = _flat("docs/open_questions.rst")
    pairs = f"{f['same']} of the {f['pairs']} pairs"
    assert (f["same"], f["pairs"]) == (43, 72) and f["same"] < 54
    for text in (oq, data, decisions):
        assert pairs in text
    assert f"{f['same']} of 72 pairs" in log
    for text in (oq, data, decisions, log, site):
        assert span in text
    assert f"**{span}**" in readme
    assert "reads 435 more Monte Carlo runs" in readme
    counted = 0
    for name in ("water_share.csv", "black_bottom.csv",
                 "water_share_nadir.csv", "cut_check.csv",
                 "fournier_forand.csv", "halves.csv",
                 "average_particle.csv", "quads.csv"):
        with (DATA / name).open() as handle:
            counted += len(list(csv.DictReader(handle)))
    assert counted == 435
    assert (f["rising"], f["falling"]) == (8, 4)
    assert f"rises with bb/b in {f['rising']} cells and falls in " \
        f"{f['falling']}" in decisions
    assert f"(rising in {f['rising']} cells, falling in {f['falling']}" in oq
    assert f["ordered"] == 1
    assert f"in {f['ordered']} of 24 cells" in oq
    assert f"in {f['ordered']} of the 24 cells" in decisions
    median = f"{float(__import__('numpy').median(f['ff_spread'])):.2f}"
    assert f"by a factor of only {median} in the median cell" in oq
    assert f"by a factor of {median} in the median cell" in decisions
    assert f"({max(f['ff_spread']):.2f} at most)" in decisions
    station = f"{float(__import__('numpy').median(f['station_spread'])):.2f}"
    assert f"the stations differ by {station}" in decisions
    assert f"up to {100 * f['noise']:.0f} percent" in decisions
    follows = f["follows"]
    assert (f"{follows[0.0]:.2f} with the sun overhead, {follows[30.0]:.2f} "
            f"at 30 degrees and {follows[60.0]:.2f} at 60") in decisions
    assert (f"{follows[0.0]:.2f} with the sun overhead and "
            f"{follows[60.0]:.2f} with the sun at 60") in oq


# -- Section 135: the halves apart ------------------------------------------

def test_the_hybrids_are_proper_phase_functions_with_the_station_s_b():
    import numpy as np
    mc = _tool("shallow_rrs_mc")
    for station in ("NUC 2240", "AUTEC 8", "HAOCE 11"):
        back = mc.petzold_phase(station)[3]
        ff = jerlov.mobley2002_fournier_forand(back)
        for forward in ("station", "ff"):
            sample, pdf, below, b = mc.hybrid_phase(station, ff, forward)
            assert b == pytest.approx(back, abs=1e-5)
            theta = np.linspace(math.radians(1.0), math.pi, 200001)
            y = pdf(theta) * 2 * math.pi * np.sin(theta)
            assert float(jerlov._data.trapezoid(y, theta)) == pytest.approx(
                1.0, abs=1e-4)
            draws = sample(np.random.default_rng(1).random(400_000))
            assert float(np.mean(draws > math.pi / 2)) == pytest.approx(
                back / (1 - below), abs=0.002)
            # Each half is its owner's.
            ahead, behind = np.radians([30.0]), np.radians([150.0])
            station_pdf = mc.petzold_phase(station)[1]
            ff_pdf = mc.fournier_forand_phase(ff)[1]
            owner_ahead = station_pdf if forward == "station" else ff_pdf
            owner_behind = ff_pdf if forward == "station" else station_pdf
            own_below = (mc.petzold_phase(station)[2] if forward == "station"
                         else mc.fournier_forand_phase(ff)[2])
            assert below == pytest.approx(own_below, abs=1e-3)
            assert float(pdf(ahead)[0]) == pytest.approx(
                float(owner_ahead(ahead)[0]), rel=2e-3)
            # The backward owner's pdf is normalised over its own cut; the
            # hybrid's over the forward owner's.
            other_below = (mc.fournier_forand_phase(ff)[2]
                           if forward == "station"
                           else mc.petzold_phase(station)[2])
            assert float(pdf(behind)[0]) * (1 - below) == pytest.approx(
                float(owner_behind(behind)[0]) * (1 - other_below), rel=2e-3)


def test_a_stored_hybrid_run_is_reproduced():
    mc = _tool("shallow_rrs_mc")
    with (DATA / "halves.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 144
    r = next(x for x in rows if x["station"] == "HAOCE 11"
             and x["forward_from"] == "ff")
    back = mc.petzold_phase("HAOCE 11")[3]
    a = float(r["a"])
    bb = 0.5 * mc.BW + mc.petzold_phase(mc.STATION)[3] * float(
        r["bp_over_a"]) * a
    phase = mc.hybrid_phase("HAOCE 11",
                            jerlov.mobley2002_fournier_forand(back), "ff")
    value, error = mc.rrs(a, (bb - 0.5 * mc.BW) / back, mc.BW,
                          float(r["depth_m"]), 0.0, float(r["sun_deg"]), phase)
    assert f"{value:.6e}" == r["monte_carlo"]
    assert f"{error:.2e}" == r["standard_error"]


def test_section_135_figures_are_quoted_as_computed(result):
    import numpy as np
    h = result["fournier"]["halves"]
    oq = _flat("OPEN_QUESTIONS.md").split("## 5. ")[1].split("## 6. ")[0]
    data = _flat("DATA.md").split("## 50. ")[1].split("## 51. ")[0]
    decisions = _flat("DECISIONS.md").split("## 135. ")[1]
    log = _flat("CHANGELOG.md").split("## 1.32.3")[1].split("## 1.32.2")[0]
    assert (h["dominant"], len(h["rows"])) == (49, 72) and h["dominant"] < 54
    assert h["lead_corr"] >= 0.9 and h["lead_pairs"] == 24
    corr = f"{h['lead_corr']:.3f}"
    for text in (oq, data, decisions, log):
        assert corr in text
    assert f"larger in {h['dominant']}, short of the 54" in oq
    assert f"larger in {h['dominant']}, short of the 54" in data
    assert f"larger in {h['dominant']} of the 72 pairs (54" in decisions
    assert f"is not ({h['dominant']})" in log
    missing = 72 - h["dominant"]
    nuc_missing = 24 - (h["dominant"] - h["others_dominant"])
    assert nuc_missing > missing / 2      # "mostly NUC 2240's"
    assert f"the {missing} pairs that miss measure 1 are mostly NUC 2240's" \
        in decisions
    assert (f"is {h['nuc'][0]:.2f} to {h['nuc'][1]:.2f})") in decisions
    assert f"in {h['others_dominant']} of {h['others']}" in oq
    assert f"in {h['others_dominant']} of {h['others']} pairs" in decisions
    factors = [f"{math.exp(b):.2f}" for b, _ in h["by_sun"].values()]
    assert (f"median factor of {factors[0]} with the sun overhead, "
            f"{factors[1]} at 30 degrees and {factors[2]} at 60") in decisions
    assert (f"median factor of {factors[0]} with the sun overhead and "
            f"{factors[2]} with the sun at 60 degrees") in oq
    forward = ", ".join(f"{fw:.3f}" for _, fw in h["by_sun"].values())
    assert forward.replace(", 0.054", " and 0.054") in decisions
    assert (f"{h['interaction'][0]:.3f} in the median pair "
            f"({h['interaction'][1]:.3f} at most)") in decisions
    assert np.isfinite(h["lead_corr"])


# -- Section 136: Petzold's average particle, built from three stations -----

def test_the_average_particle_is_the_web_book_s_table(result):
    import numpy as np
    mc = _tool("shallow_rrs_mc")
    angles, pf = mc.average_particle_table()
    assert len(angles) == 55
    module = runpy.run_path(str(ROOT / "examples" /
                                "shallow_water_closure.py"), run_name="q")
    table = module["WEB_BOOK_AVERAGE"]
    assert len(table) == 12
    at = np.exp(np.interp(np.log(list(table)), np.log(angles), np.log(pf)))
    worst = float(np.max(np.abs(at / np.array(list(table.values())) - 1)))
    assert worst < 0.005
    assert result["average"]["rebuilt"] == pytest.approx(worst, rel=1e-12)
    sample, pdf, below, back = mc.average_particle_phase()
    assert round(back, 4) == 0.0183
    theta = np.linspace(math.radians(1.0), math.pi, 200001)
    y = pdf(theta) * 2 * math.pi * np.sin(theta)
    assert float(jerlov._data.trapezoid(y, theta)) == pytest.approx(1.0,
                                                                    abs=1e-4)


def test_a_stored_average_particle_run_is_reproduced():
    mc = _tool("shallow_rrs_mc")
    with (DATA / "average_particle.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 24
    r = rows[5]
    phase = mc.average_particle_phase()
    a = float(r["a"])
    bb = 0.5 * mc.BW + mc.petzold_phase(mc.STATION)[3] * float(
        r["bp_over_a"]) * a
    value, error = mc.rrs(a, (bb - 0.5 * mc.BW) / phase[3], mc.BW,
                          float(r["depth_m"]), 0.0, float(r["sun_deg"]), phase)
    assert f"{value:.6e}" == r["monte_carlo"]
    assert f"{error:.2e}" == r["standard_error"]
    for row in rows:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
            m = jerlov.lee1999_shallow_rrs(
                float(row["a"]), float(row["bb"]),
                depth_m=float(row["depth_m"]), bottom_albedo=0.0,
                sun_zenith_deg=float(row["sun_deg"]))
        assert float(row["model"]) == pytest.approx(m.rrs, rel=2e-5)


def test_section_136_figures_are_quoted_as_computed(result):
    v = result["average"]
    oq = _flat("OPEN_QUESTIONS.md").split("## 5. ")[1].split("## 6. ")[0]
    data50 = _flat("DATA.md").split("## 50. ")[1].split("## 51. ")[0]
    data21 = _flat("DATA.md").split("## 21. ")[1].split("## 22. ")[0]
    decisions = _flat("DECISIONS.md").split("## 136. ")[1]
    log = _flat("CHANGELOG.md").split("## 1.32.4")[1].split("## 1.32.3")[0]
    readme = _flat("examples/README.md")
    assert (v["within"], v["group"]) == (1, 13) and v["within"] < 10
    assert v["before"] == 0
    rebuilt = f"within {100 * v['rebuilt']:.2f} percent"
    for text in (oq, data21, decisions, log):
        assert rebuilt in text, text[:40]
    group = f"{v['within']} of the group's {v['group']}"
    for text in (oq, decisions):
        assert group in text
    assert f"{v['within']} of the second group's {v['group']}" in data50
    assert f"{v['within']} of the second group's {v['group']}" in log
    assert f"brings **{v['within']}** of the black-bottom group's" in readme
    assert "reads 435 more Monte Carlo runs" in readme
    p = f"{v['p_over'][0]:.2f} to {v['p_over'][1]:.2f}"
    for text in (oq, data50, decisions):
        assert p in text
    rrs = f"{v['over_nuc'][0]:.2f} to {v['over_nuc'][1]:.2f}"
    assert f"rrs {rrs}" in oq
    assert f"rrs {rrs} times" in decisions
    assert f"{v['every']} of the {v['cells']} cells" in decisions
    assert f"{v['q'][0]:.3f} to {v['q'][1]:.3f}" in decisions
    assert f"{v['back']:.5f}"[:7] in decisions      # 0.01825


# -- Section 137: HydroLight's angular quads --------------------------------

def test_the_quads_meet_their_closed_form_and_stay_off_by_default():
    import numpy as np
    mc = _tool("shallow_rrs_mc")
    phase = mc.petzold_phase(mc.STATION)
    for a, depth, rho, sun in ((0.1, 3.0, 0.5, 30.0), (0.5, 1.0, 1.0, 0.0),
                               (0.05, 10.0, 0.3, 60.0)):
        value, error = mc.rrs(a, 0.0, 1e-12, depth, rho, sun, phase,
                              surface=False, cap_deg=5.0, sun_quad=True)
        lo, hi, _ = mc.sun_quad_bounds(sun)
        cos_air = np.linspace(math.cos(math.radians(hi)),
                              math.cos(math.radians(lo)), 4001)
        mu_w = np.sqrt(1 - (1 - cos_air ** 2) / mc.N_WATER ** 2)
        mu_v = np.linspace(math.cos(math.radians(5.0)), 1.0, 4001)
        exact = (rho / math.pi * float(np.mean(np.exp(-a * depth / mu_w)))
                 * float(np.mean(np.exp(-a * depth / mu_v))))
        assert abs(value - exact) <= 3 * error
    assert mc.sun_quad_bounds(0.0) == (0.0, 5.0, None)
    assert mc.sun_quad_bounds(30.0) == (25.0, 35.0, 7.5)
    assert mc.sun_quad_bounds(60.0) == (55.0, 65.0, 7.5)


def test_a_stored_quad_run_is_reproduced():
    mc = _tool("shallow_rrs_mc")
    with (DATA / "quads.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 24
    r = rows[7]
    phase = mc.average_particle_phase()
    a = float(r["a"])
    bb = 0.5 * mc.BW + mc.petzold_phase(mc.STATION)[3] * float(
        r["bp_over_a"]) * a
    value, error = mc.rrs(a, (bb - 0.5 * mc.BW) / phase[3], mc.BW,
                          float(r["depth_m"]), 0.0, float(r["sun_deg"]), phase,
                          cap_deg=float(r["cap_deg"]), sun_quad=True)
    assert f"{value:.6e}" == r["monte_carlo"]
    assert f"{error:.2e}" == r["standard_error"]


def test_section_137_figures_are_quoted_as_computed(result):
    v = result["average"]
    oq = _flat("OPEN_QUESTIONS.md").split("## 5. ")[1].split("## 6. ")[0]
    data50 = _flat("DATA.md").split("## 50. ")[1].split("## 51. ")[0]
    decisions = _flat("DECISIONS.md").split("## 137. ")[1]
    log = _flat("CHANGELOG.md").split("## 1.32.4")[1].split("## 1.32.3")[0]
    readme = _flat("examples/README.md")
    assert v["quad_within"] == 4 and v["quad_within"] < 10
    moves = f"{v['quad_over'][0]:.2f} to {v['quad_over'][1]:.2f} times"
    assert moves in oq and moves in decisions
    assert f"brings {v['quad_within']} of the 13 within 10 percent" in oq
    assert f"in {v['quad_within']} of the group's 13 runs (1" in decisions
    assert f"{v['quad_within']} of the 13." in data50
    assert f"bring {v['quad_within']} of the 13" in log
    assert f"and with HydroLight's angular quads {v['quad_within']}." in readme
    assert f"{v['quad_every']} of the 24 cells" in decisions
    assert f"{v['q_quad'][0]:.3f} to {v['q_quad'][1]:.3f}" in decisions
    assert f"up to {100 * v['quad_noise']:.1f} percent" in decisions

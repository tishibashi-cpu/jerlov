"""The two pages of the site made from the package's values (DECISIONS.md
section 109): daylight on the way down, and where the sources disagree.

The pages live in docs/pages/ and are written by tools/site_pages.py, so
every test here needs the source tree.
"""

from __future__ import annotations

import importlib.util
import json
import math
import pathlib
import re
import shutil
import subprocess
import warnings

import numpy as np
import pytest

import jerlov
from jerlov._data import trapezoid

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ROOT / "docs" / "pages"
source_tree = pytest.mark.skipif(
    not (ROOT / "pyproject.toml").exists(),
    reason="not running from a source tree",
)
pytestmark = source_tree

DATA_LINE = re.compile(r"^const DATA = (\{.*\});$", re.M)


def _tool():
    spec = importlib.util.spec_from_file_location(
        "site_pages", ROOT / "tools" / "site_pages.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _data(text):
    match = DATA_LINE.search(text)
    assert match, "the page embeds no `const DATA = {...};` line"
    return json.loads(match.group(1))


def _page(name):
    return (PAGES / name).read_text()


def _flat(text):
    """Prose with tags removed and whitespace collapsed."""
    return " ".join(re.sub(r"<[^>]+>", "", text).replace("&amp;", "&").split())


def _close(made, kept, where):
    """Equal, or, for a number, apart by no more than its last printed digit:
    a value rounded on one machine may round the other way on another."""
    if isinstance(kept, dict):
        assert made.keys() == kept.keys(), where
        for k in kept:
            _close(made[k], kept[k], f"{where}.{k}")
    elif isinstance(kept, list):
        assert len(made) == len(kept), where
        for i, (m, k) in enumerate(zip(made, kept)):
            _close(m, k, f"{where}[{i}]")
    elif isinstance(kept, float) and not isinstance(made, (str, bool)) \
            and made is not None:
        r = repr(kept)
        digits = len(r.split(".")[1]) if "." in r and "e" not in r else 15
        assert abs(made - kept) <= 1.0001 * 10.0 ** -digits + 1e-12 * abs(kept), (
            f"{where}: {made} written, {kept} in the page")
    else:
        assert made == kept, f"{where}: {made!r} written, {kept!r} in the page"


# -- the pages are what the tool writes now ----------------------------------

PAGE_NAMES = ["dive.html", "disagree.html", "waters.html", "shallow.html"]


@pytest.mark.parametrize("name", PAGE_NAMES)
def test_the_page_is_what_the_tool_writes_now(name):
    made = _tool().pages()[name]
    kept = _page(name)
    assert DATA_LINE.sub("", made) == DATA_LINE.sub("", kept), (
        f"docs/pages/{name} differs from what tools/site_pages.py writes; "
        "run it again")
    _close(_data(made), _data(kept), name)
    assert _data(kept)["jerlov_version"] == jerlov.__version__


@pytest.mark.parametrize("name", PAGE_NAMES)
def test_the_page_asks_nothing_of_another_host(name):
    text = _page(name)
    assert "<script src" not in text
    assert 'rel="stylesheet"' not in text
    assert "@import" not in text
    assert "url(" not in text
    assert "{{" not in text, "a placeholder was left unfilled"


def test_the_site_carries_the_pages_and_links_to_them():
    conf = (ROOT / "docs" / "conf.py").read_text()
    assert 'html_extra_path = ["pages", "extra"]' in conf
    assert '"pages"' in conf.split("exclude_patterns")[1].splitlines()[0]
    index = (ROOT / "docs" / "index.rst").read_text()
    assert "<dive.html>`_" in index and "<disagree.html>`_" in index
    assert "<waters.html>`_" in index and "<shallow.html>`_" in index
    assert '"waters.html"' in conf.split("_EXTRA_PAGES")[1].splitlines()[0]
    assert '"shallow.html"' in conf.split("_EXTRA_PAGES")[1].splitlines()[0]
    # Each page's navigation names the other three (DECISIONS.md section 121).
    for name in PAGE_NAMES:
        nav = _page(name).split('<nav class="nav">')[1].split("</nav>")[0]
        for other in PAGE_NAMES:
            assert (f'href="{other}"' in nav) == (other != name), (name, other)
    assert "<disagree.html>`_" in (ROOT / "docs" / "open_questions.rst").read_text()


# -- the first page: its arithmetic is jerlov's --------------------------------

CHECKS = [(t, z) for t in ("I", "II", "1C", "9C") for z in (0.0, 5.0, 20.0, 50.0)]


def _signed_gamma(linear):
    """sRGB's transfer function as jerlov.xyz_to_srgb applies it, unclipped."""
    return np.where(linear <= 0.0031308, 12.92 * linear,
                    1.055 * np.power(np.maximum(linear, 0), 1 / 2.4) - 0.055)


def _jerlov_at(sky, water, wl, z):
    """sRGB (unclipped) and PAR over the surface's, by jerlov's own functions,
    from its own unrounded inputs."""
    ed = sky * np.exp(-np.asarray(water.kd(wl)) * z)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.GamutWarning)
        warnings.simplefilter("ignore", jerlov.CoverageWarning)
        rgb = jerlov.spectrum_to_srgb(ed, wl, white=sky, clip=False)
    par = jerlov.par_profile(sky, wl, [0.0, z], kd=water, unit="energy").par
    return np.asarray(rgb), float(par[1] / par[0])


def _page_at(data, water_type, z):
    """The page's arithmetic (tools/site_pages/dive_core.js) in NumPy."""
    wl = np.asarray(data["wl"], float)
    es = np.asarray(data["es"], float)
    cmf = np.asarray(data["cmf"], float)
    ed = es * np.exp(-np.asarray(data["kd"][water_type], float) * z)
    xyz = np.array([trapezoid(ed * cmf[k], wl) for k in range(3)])
    white = np.array([trapezoid(es * cmf[k], wl) for k in range(3)])
    linear = np.asarray(data["xyz_to_srgb"]) @ (xyz / white * data["srgb_white"])
    band = (wl >= 400) & (wl <= 700)
    photons = es * wl
    par = trapezoid((photons * np.exp(
        -np.asarray(data["kd"][water_type], float) * z))[band], wl[band]) \
        / trapezoid(photons[band], wl[band])
    return _signed_gamma(linear), float(par)


def _sky(tool, wl):
    return np.asarray(jerlov.gregg1990_irradiance(
        wl, sun_zenith_deg=tool.SUN_DEG, visibility_km=tool.VISIBILITY_KM,
        **tool.ATMOSPHERE).below)


def test_the_first_page_gives_jerlovs_colours_and_par_within_1e5():
    """The page says so; DECISIONS.md section 109 set the tolerance."""
    tool = _tool()
    data = _data(_page("dive.html"))
    wl = tool.DIVE_WL
    sky = _sky(tool, wl)
    for water_type, z in CHECKS:
        water = jerlov.water(water_type, source="jerlov1976")
        rgb, par = _jerlov_at(sky, water, wl, z)
        page_rgb, page_par = _page_at(data, water_type, z)
        assert np.max(np.abs(page_rgb - rgb)) < 1e-5, (water_type, z)
        assert abs(page_par / par - 1) < 1e-5, (water_type, z)
    assert "match jerlov's own <code>spectrum_to_srgb</code> and " \
           "<code>par_profile</code> to within 0.00001" in _page("dive.html")


def test_the_first_page_quotes_the_one_percent_depths_it_computes():
    tool = _tool()
    wl = tool.DIVE_WL
    sky = _sky(tool, wl)
    flat = jerlov.par_profile(sky, wl, 0.0, unit="energy",
                              kd=jerlov.water("I", source="jerlov1976"))
    layered = jerlov.par_profile(sky, wl, 0.0, unit="energy",
                                 kd=jerlov.descend("I", jerlov.profile_depth("I"), wl))
    one, two = flat.depth_of_fraction(), layered.depth_of_fraction()
    assert f"type I from {one:.0f} m to {two:.0f} m" in _flat(_page("dive.html"))
    assert (round(one), round(two)) == (162, 105)


def test_the_first_pages_spectrum_says_it_shows_shape_only():
    """DECISIONS.md section 111: the curves are each scaled to their own peak."""
    page = _flat(_page("dive.html"))
    assert "Each is scaled to its own peak, so their heights cannot be compared" in page
    assert "solid line drawn \\u00d7 ${times(k)}" in _page("dive.html")


@pytest.mark.parametrize("name", ["dive.html", "disagree.html"])
def test_the_hidden_attribute_hides(name):
    """The drafts ran where the viewer added this rule; the site does not. Without it the
    first page showed its "outside sRGB" chip at every depth (DECISIONS.md section 111)."""
    assert "[hidden] { display: none !important; }" in _page(name)


def test_the_first_page_says_what_data_md_says_of_jerlovs_table():
    data_md = (ROOT / "DATA.md").read_text()
    assert "Jerlov printed 16 wavelengths, 310-700" in data_md
    assert "printed at 16 wavelengths from 310 to 700 nm" in _flat(_page("dive.html"))


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_the_first_pages_own_script_gives_jerlovs_values(tmp_path):
    """The script itself, not a copy of it, where node can run it."""
    tool = _tool()
    data = _data(_page("dive.html"))
    (tmp_path / "data.json").write_text(json.dumps(data))
    core = ROOT / "tools" / "site_pages" / "dive_core.js"
    (tmp_path / "run.js").write_text(f"""
const Core = require({json.dumps(str(core))});
const D = require("./data.json");
const c = Core.make(D);
const out = {json.dumps(CHECKS)}.map(([t, z]) => [c.linear(c.edAt(t, z)), c.parFraction(t, z),
  c.depthOfParFraction(t, 0.01), c.enlargement(t, z), c.outside(c.linear(c.edAt(t, z)))]);
console.log(JSON.stringify(out));
""")
    result = subprocess.run(["node", str(tmp_path / "run.js")], capture_output=True,
                            text=True, check=True, cwd=tmp_path)
    wl = tool.DIVE_WL
    sky = _sky(tool, wl)
    es = np.asarray(data["es"], float)
    seen_outside = set()
    for (water_type, z), (linear, par, d1, k, outside) in zip(CHECKS, json.loads(result.stdout)):
        seen_outside.add(outside)
        # The factor the chart prints (DECISIONS.md section 111): the surface's peak over
        # this depth's, on the page's own values.
        ed = es * np.exp(-np.asarray(data["kd"][water_type], float) * z)
        assert math.isclose(k, es.max() / ed.max(), rel_tol=1e-12), (water_type, z)
        water = jerlov.water(water_type, source="jerlov1976")
        rgb, expected_par = _jerlov_at(sky, water, wl, z)
        # The chip (DECISIONS.md section 111): outside sRGB where jerlov's colour has a negative
        # channel, however dim the light; the sign survives sRGB's transfer function.
        assert outside == bool(rgb.min() < -1e-6 * rgb.max()), (water_type, z, rgb)
        assert np.max(np.abs(_signed_gamma(np.asarray(linear)) - rgb)) < 1e-5
        assert abs(par / expected_par - 1) < 1e-5
        depth = jerlov.par_profile(sky, wl, 0.0, kd=water,
                                   unit="energy").depth_of_fraction()
        assert abs(d1 - depth) < 1e-3, (water_type, d1, depth)
    assert seen_outside == {True, False}, "the cases should include colours in and out of sRGB"


# -- the second page: what it draws and what it quotes -------------------------

def test_the_second_page_outlines_the_cells_open_questions_names():
    closure = _data(_page("disagree.html"))["closure"]
    beyond = {(c["type"], c["wl"]) for c in closure["cells"] if c["beyond"]}
    assert beyond == {("IB", 425), ("IB", 450), ("IB", 475), ("IB", 500),
                      ("1C", 425), ("5C", 425), ("3C", 425), ("3C", 450)}
    assert len(closure["types"]) == 6 and len(closure["wl"]) == 12
    questions = _flat((ROOT / "OPEN_QUESTIONS.md").read_text())
    reach = f"{closure['down']:.2f} to {closure['up']:.2f}"
    assert f"the conditions move them by {reach} times" in questions
    page = _flat(_page("disagree.html"))
    assert "for six types at twelve wavelengths" in page
    assert "IB is too high at 425 to 500 nm, and the coastal types too low " \
           "at 425 to 450 nm" in page


#: What the second page quotes, and where OPEN_QUESTIONS.md (or DATA.md)
#: says it; the tests of those documents recompute the figures.
QUOTED = [
    ("up to 6.85 times apart at 380 nm and 2.62 at 443 nm",
     "up to 6.85 times apart at 380 nm, 4.28 at 412, 2.62 at 443", "OPEN_QUESTIONS.md"),
    ("only 1.12 to 1.34 times", "move Rrs by only 1.12 to 1.34 times", "OPEN_QUESTIONS.md"),
    ("of 1 to 10 per metre", "is between 1 and 10 m-1", "OPEN_QUESTIONS.md"),
    ("moves Kd by −0.63 to +0.13 %", "moves by -0.63 to +0.13 percent",
     "OPEN_QUESTIONS.md"),
    ("At 143 cells from 350 to 700 nm", "run at the 143 cells from 350 to 700 nm",
     "OPEN_QUESTIONS.md"),
    ("a median within 0.95 to 1.05 and 90 % of the cells within 10 %",
     "a median within 0.95 to 1.05 and 90 percent of the cells within 10 percent",
     "OPEN_QUESTIONS.md"),
    ("Petzold's measurements of 1971", "Petzold's measurements of 1971",
     "OPEN_QUESTIONS.md"),
    ("the other stations move it by -12.7 to +26.0 percent, the sun by -12.7 "
     "to +21.5", "the other stations move it by -12.7 to +26.0 percent, the "
     "sun by -12.7 to +21.5", "OPEN_QUESTIONS.md"),
    ("in 12 of 12 cases: from 1.023-1.157 with particles alone to "
     "0.783-0.902 with pure water nearly alone",
     "in 12 of 12 cases: from 1.023-1.157 with particles alone to "
     "0.783-0.902 with pure water nearly alone", "OPEN_QUESTIONS.md"),
    ("No single change brought 10 of the 13 within 10 percent",
     "No single change brought 10 of the 13 within 10 percent",
     "OPEN_QUESTIONS.md"),
    ("moves by 1.054 to 1.079 times across the shares against the Monte "
     "Carlo, the 1999 model by 1.232 to 1.333",
     "it moves by 1.054 to 1.079 times against the Monte Carlo, the 1999 "
     "model by 1.232 to 1.333", "OPEN_QUESTIONS.md"),
    ("Their archive's f at 45 degrees lies up to 3.44 percent below the line "
     "between its own values at 30 and 60",
     "Their archive's f at 45 degrees lies up to 3.44 percent below the line "
     "between its own values at 30 and 60", "OPEN_QUESTIONS.md"),
    ("at all 7 wavelengths, by 1.01 to 3.44 percent",
     "f lies below the chord at all 7 wavelengths, by 1.01 to 3.44 percent",
     "OPEN_QUESTIONS.md"),
    ("Its symbols hold all 60 of the archive's values",
     "hold all 60 of the archive's values", "OPEN_QUESTIONS.md"),
    ('it seems that the last word is not said about the behaviour of the '
     'irradiance attenuation in the "slope" region of 600 nm',
     'it seems that the last word is not said about the behaviour of the > '
     'irradiance attenuation in the "slope" region of 600 nm', "DATA.md"),
]


@pytest.mark.parametrize("on_page, in_source, source", QUOTED)
def test_what_the_second_page_quotes_is_in_its_source(on_page, in_source, source):
    assert on_page in _flat(_page("disagree.html"))
    assert in_source in _flat((ROOT / source).read_text())


def test_the_second_pages_figures_are_jerlovs():
    data = _data(_page("disagree.html"))
    ratio = data["pure_water"]["pope_over_mason"]["380.0"]
    assert ratio == 7.95  # OPEN_QUESTIONS.md, question 1
    below = [p["below"] for p in data["petzold"]]
    assert (round(100 * min(below), 1), round(100 * max(below), 1)) == (3.4, 14.5)
    assert "3.4 to 14.5 percent of the scattering" in _flat(
        (ROOT / "OPEN_QUESTIONS.md").read_text())
    cells = {(c["type"], c["wl"]): c["ratio"] for c in data["editions"]["cells"]}
    assert math.isclose(cells[("1C", 425.0)], 1.527, abs_tol=1e-3)


# -- what a search engine is pointed to (DECISIONS.md section 112) ------------

def test_the_search_console_file_is_googles_and_reaches_the_root():
    name = "google8846fd1b128ec3b7.html"
    assert (ROOT / "docs" / "extra" / name).read_text() == \
        f"google-site-verification: {name}"
    conf = (ROOT / "docs" / "conf.py").read_text()
    assert 'html_extra_path = ["pages", "extra"]' in conf
    assert '"extra"]' in conf.split("exclude_patterns")[1].splitlines()[0]


def test_the_site_writes_a_sitemap_with_its_pages():
    conf = (ROOT / "docs" / "conf.py").read_text()
    assert 'html_baseurl = "https://tishibashi-cpu.github.io/jerlov/"' in conf
    assert 'app.connect("build-finished", _sitemap)' in conf
    assert ('_EXTRA_PAGES = ("dive.html", "disagree.html", "waters.html", '
            '"shallow.html")') in conf
    # The docs workflow reads the built sitemap back.
    docs_yml = (ROOT / ".github" / "workflows" / "docs.yml").read_text()
    for page in ("index.html", "dive.html", "shallow.html"):
        assert f"<loc>https://tishibashi-cpu.github.io/jerlov/{page}</loc>" in docs_yml


def test_the_zenodo_record_links_the_site():
    record = json.loads((ROOT / ".zenodo.json").read_text())
    assert {"identifier": "https://tishibashi-cpu.github.io/jerlov/",
            "relation": "isDocumentedBy", "scheme": "url"} in record["related_identifiers"]


# -- questions 4 to 6 on the second page (DECISIONS.md section 119) ----------

def _oq(n):
    text = _flat((ROOT / "OPEN_QUESTIONS.md").read_text())
    return text.split(f"## {n}. ")[1].split(f"## {n + 1}. ")[0]


def test_the_second_pages_hydrolight_figures_are_open_questions():
    cells = _data(_page("disagree.html"))["hydrolight"]["cells"]
    ratios = np.array([c["ratio"] for c in cells])
    assert len(ratios) == 143
    median = f"{np.median(ratios):.3f}"
    within = f"{100 * np.mean(np.abs(ratios - 1) <= 0.1):.1f}"
    assert f"| With it and a clear sky | {median} | {within} percent |" in _oq(4)


def test_the_second_pages_shallow_figures_are_open_questions():
    s = _data(_page("disagree.html"))["shallow"]
    runs = s["runs"]
    q = np.array([r["ratio"] for r in runs])
    g1 = np.array([r["group"] == 1 for r in runs])
    g2 = np.array([r["group"] == 2 for r in runs])
    within = 100 * np.mean(np.abs(q - 1) <= s["miss"])
    text = _oq(5)
    assert f"within 10 percent in {within:.1f} percent of {len(q)} runs" in text
    assert (f"({g1.sum()} runs, the model low, {q[g1].min():.3f} to "
            f"{q[g1].max():.3f} of the Monte Carlo)") in text
    assert f"({g2.sum()} runs, the model high, to {q[g2].max():.3f})" in text
    shares = sorted({f"{r['share']:.2f}" for r in runs if r["group"] == 1})
    assert (f"in the paper's runs is at most {s['paper_share_max']:.2f}. The "
            f"first group's runs have {' and '.join(shares)}.") in text
    assert len(s["held"]) == 12


def test_the_second_pages_fig13_figures_are_open_questions():
    f = _data(_page("disagree.html"))["fig13"]

    def gap(chl, value):
        return min(0.0 if s["bottom"] <= value <= s["top"]
                   else min(abs(value - s["top"]), abs(value - s["bottom"]))
                   for s in f["spans"] if s["chl"] == chl)

    far = [gap(0.03, x["value"]) for x in f["fits"]
           if x["chl"] == 0.03 and x["sun"] == 45.0 and x["wl"] >= 560]
    text = _oq(6)
    assert f"no symbol stands within {min(far):.4f} to {max(far):.4f}" in text
    assert f"a symbol on its own within {f['accuracy']:.4f} of its value" in text
    # The fits drawn are the package's Eq. (B1); nothing from the archive.
    for x in f["fits"]:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
            f0 = jerlov.morel2002_nadir_fq(x["wl"], chlorophyll_mg_m3=x["chl"],
                                           sun_zenith_deg=0.0).f
            fs = jerlov.morel2002_nadir_fq(x["wl"], chlorophyll_mg_m3=x["chl"],
                                           sun_zenith_deg=x["sun"]).f
        assert x["value"] == round(f0 / fs, 4)


def test_the_second_pages_fig13_misses_are_what_decisions_says():
    f = _data(_page("disagree.html"))["fig13"]

    def gap(chl, value):
        return min(0.0 if s["bottom"] <= value <= s["top"]
                   else min(abs(value - s["top"]), abs(value - s["bottom"]))
                   for s in f["spans"] if s["chl"] == chl)

    worst = {c: max(gap(c, x["value"]) for x in f["fits"] if x["chl"] == c)
             for c in (0.03, 0.1)}
    text = _flat((ROOT / "DECISIONS.md").read_text()).split("## 119. ")[1]
    assert (f"up to {worst[0.1]:.4f} at 0.1 mg m^-3 and {worst[0.03]:.4f} at "
            "0.03 mg m^-3 and 45 degrees") in text


# -- the figures, the third page and the card (DECISIONS.md section 120) ------

NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def _figures_tool():
    spec = importlib.util.spec_from_file_location(
        "site_figures", ROOT / "tools" / "site_figures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def made_figures():
    return _tool().figures()


def test_the_figures_are_what_the_tool_writes_now(made_figures):
    """Byte for byte but for coordinates, which may round the other way on
    another machine: those within 0.15 of a pixel."""
    kept_names = sorted(p.name for p in (ROOT / "docs" / "figures").glob("*.svg"))
    assert kept_names == sorted(made_figures)
    for name, made in made_figures.items():
        kept = (ROOT / "docs" / "figures" / name).read_text()
        assert NUMBER.sub("#", made) == NUMBER.sub("#", kept), name
        for a, b in zip(NUMBER.findall(made), NUMBER.findall(kept)):
            assert abs(float(a) - float(b)) <= 0.15, (name, a, b)


def test_the_figures_name_what_they_draw(made_figures):
    for name, svg in made_figures.items():
        assert 'role="img" aria-label="' in svg, name
        assert "<script" not in svg and "href" not in svg, name
    assert "Jerlov 1976" in made_figures["kd_types.svg"]


def test_the_swatches_are_spectrum_to_srgb_of_the_stated_spectra(made_figures):
    tool = _figures_tool()
    es = tool.surface()
    wl = tool.WL
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for t, z in (("IB", 0.0), ("1C", 10.0), ("5C", 20.0), ("II", 10.0)):
            kd = np.asarray(jerlov.water(t, source="jerlov1976").kd(wl))
            rgb = jerlov.spectrum_to_srgb(es * np.exp(-kd * z), wl, white=es)
            hexed = "#" + "".join(f"{int(round(255 * min(max(float(c), 0), 1))):02x}"
                                  for c in rgb)
            assert tool.colour_at(t, z, es) == hexed
            where = "kd_types.svg" if z == 10.0 and t == "II" else "card_colours.svg"
            assert f'fill="{hexed}"' in made_figures[where], (t, z)


def test_the_docs_show_the_figures():
    index = (ROOT / "docs" / "index.rst").read_text()
    assert ".. figure:: figures/kd_types.svg" in index
    examples = (ROOT / "docs" / "examples.rst").read_text()
    for name in ("par", "sources", "colours", "heating", "chlorophyll",
                 "scattering"):
        assert f".. image:: figures/card_{name}.svg" in examples


def test_the_third_page_draws_what_water_returns():
    data = _data(_page("waters.html"))
    tool = _tool()
    assert len(data["series"]) == sum(
        len(jerlov.SOURCES[s].water_types) for _, s, _ in tool.WATER_SERIES)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        for s in data["series"][::7]:
            method = {(q, src): m for q, src, m in tool.WATER_SERIES}[
                (s["quantity"], s["source"])]
            w = jerlov.water(s["type"], source=s["source"])
            values = np.asarray(getattr(w, method)(np.asarray(s["wl"])), float)
            for got, want in zip(s["v"], values):
                if got is None:
                    assert not np.isfinite(want)
                else:
                    assert got == pytest.approx(want, abs=1e-5)
    for s in data["series"]:
        if s["source"] == "williamson2022":
            assert min(s["wl"]) >= 412.0     # measured from 412 nm
    for source, info in data["sources"].items():
        assert info["caveats"] == list(jerlov.SOURCES[source].caveats)


def test_the_card_is_a_png_of_1200_by_630_and_every_page_names_it():
    import struct
    png = (ROOT / "docs" / "extra" / "og.png").read_bytes()
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", png[16:24]) == (1200, 630)
    image = '<meta property="og:image" content="https://tishibashi-cpu.github.io/jerlov/og.png">'
    for name in PAGE_NAMES:
        assert image in _page(name), name
        assert (f'<meta property="og:url" content="https://tishibashi-cpu.github.io/'
                f'jerlov/{name}">') in _page(name)
    layout = (ROOT / "docs" / "_templates" / "layout.html").read_text()
    assert '{% extends "!layout.html" %}' in layout
    assert 'content="{{ theme_og_root }}og.png"' in layout
    conf = (ROOT / "docs" / "conf.py").read_text()
    assert 'templates_path = ["_templates"]' in conf


# -- the fourth page: when the bottom shows through (DECISIONS.md section 121) -

def test_the_fourth_page_embeds_what_water_returns():
    data = _data(_page("shallow.html"))
    tool = _tool()
    wl = np.asarray(data["wl"], float)
    assert wl[0] == 400.0 and wl[-1] == 700.0
    assert data["types"] == list(tool.TYPES)
    assert data["ratios"] == [0.005, 0.0183, 0.03]
    def array(values):
        return np.array([np.nan if x is None else x for x in values], float)

    for t in data["types"]:
        w = jerlov.water(t, source="solonenko2015")
        with warnings.catch_warnings(record=True) as record:
            warnings.simplefilter("always", jerlov.ProvenanceWarning)
            assert np.allclose(array(data["a"][t]), w.a(wl), rtol=0,
                               atol=1e-7, equal_nan=True)
            for r in data["ratios"]:
                assert np.allclose(array(data["bb"][t][f"{r:g}"]),
                                   w.bb(wl, particle_backscatter_ratio=r),
                                   rtol=0, atol=1e-9, equal_nan=True)
        # The flags the page shows are the package's own warnings.
        said = {str(x.message) for x in record
                if issubclass(x.category, jerlov.ProvenanceWarning)}
        assert set(data["flags"][t]) == said, t
    # The gaps of Table 7 (DATA.md section 1) and the suspect b of I and IA
    # are on the page.
    assert data["a"]["5C"][data["wl"].index(600.0)] is None
    assert data["a"]["3C"][data["wl"].index(675.0)] is None
    assert data["a"]["3C"][data["wl"].index(650.0)] is not None
    assert all(data["flags"][t] for t in ("I", "IA", "3C", "5C"))
    assert not data["flags"]["IB"]
    from jerlov import ocean_colour as oc
    m = data["model"]
    assert (tuple(m["g"]), tuple(m["dc"]), tuple(m["db"])) == (
        oc._LEE1999_G, oc._LEE1999_D_COLUMN, oc._LEE1999_D_BOTTOM)
    assert (m["zeta"], m["gamma"], m["n"], m["u_max"]) == (
        oc._LEE1999_ZETA, oc._LEE1999_GAMMA, oc._LEE1998_N, oc._LEE1998_U)
    assert tuple(m["depth"]) == oc._LEE1998_DEPTH
    # The equations as the page prints them carry the same constants.
    import html
    text = html.unescape(_flat(_page("shallow.html"))).replace("\u2212", "-")
    assert (f"{m['dc'][0]:g} (1 + {m['dc'][1]:g} u)^0.5" in text
            and f"{m['db'][0]:g} (1 + {m['db'][1]:g} u)^0.5" in text)
    assert f"rrs_dp = ({m['g'][0]:.3f} + {m['g'][1]:.3f} u) u" in text
    assert (f"Rrs = {m['zeta']:g} rrs / (1 - {m['gamma']:g} rrs)" in text)
    assert f"n = {m['n']:g}" in text


def test_the_fourth_page_quotes_the_monte_carlo_as_the_records_do():
    text = _flat(_page("shallow.html"))
    figures = _tool().shallow_figures()
    quoted = (f"{figures['MC_RUNS']} runs", f"is {figures['MC_MEDIAN']}",
              f"within 10 percent in {figures['MC_WITHIN']} percent")
    for q in quoted:
        assert q in text, q
    assert (f"within 10 percent in {figures['MC_WITHIN']} percent of "
            f"{figures['MC_RUNS']} runs") in _oq(5)
    data_md = _flat((ROOT / "DATA.md").read_text())
    assert (f"median {figures['MC_MEDIAN']}, within 10 percent in "
            f"{figures['MC_WITHIN']} percent") in data_md


SHALLOW_CASES = [(t, sun, r, depth, albedo)
                 for t, sun, r in (("I", 0.0, 0.0183), ("IB", 30.0, 0.005),
                                   ("1C", 60.0, 0.03), ("9C", 30.0, 0.0183),
                                   ("5C", 30.0, 0.0183))
                 for depth, albedo in ((0.5, 1.0), (5.0, 0.3), (17.3, 0.0),
                                       (32.0, 0.1))]


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_the_fourth_pages_own_script_gives_jerlovs_values(tmp_path):
    """shallow_core.js against lee1999_shallow_rrs, and dive_core.js's colour
    against spectrum_to_srgb, on the page's own values."""
    data = _data(_page("shallow.html"))
    (tmp_path / "data.json").write_text(json.dumps(data))
    pages = ROOT / "tools" / "site_pages"
    (tmp_path / "run.js").write_text(f"""
const Core = require({json.dumps(str(pages / "dive_core.js"))});
const Shallow = require({json.dumps(str(pages / "shallow_core.js"))});
const D = require("./data.json");
const S = Shallow.make(D);
const out = {json.dumps(SHALLOW_CASES)}.map(([t, sun, r, H, rho]) => {{
  const x = S.rrs(t, sun, r, H, rho);
  const sky = D.sky[String(sun)];
  const c = Core.make({{ wl: D.wl, cmf: D.cmf, es: sky, xyz_to_srgb: D.xyz_to_srgb, srgb_white: D.srgb_white }});
  return [x, c.linear(x.above.map((v, i) => Math.PI * v * sky[i]))];
}});
console.log(JSON.stringify(out));
""")
    result = subprocess.run(["node", str(tmp_path / "run.js")], capture_output=True,
                            text=True, check=True, cwd=tmp_path)
    wl = np.asarray(data["wl"], float)
    for (t, sun, r, depth, albedo), (got, linear) in zip(
            SHALLOW_CASES, json.loads(result.stdout)):
        a = np.array([np.nan if x is None else x for x in data["a"][t]])
        bb = np.asarray(data["bb"][t][f"{r:g}"], float)
        got = {k: np.array([np.nan if x is None else x for x in v])
               for k, v in got.items()}
        want = jerlov.lee1999_shallow_rrs(a, bb, depth_m=depth,
                                          bottom_albedo=albedo,
                                          sun_zenith_deg=sun)
        for mine, theirs in (("rrs", "rrs"), ("column", "column"),
                             ("bottom", "bottom"), ("deep", "deep"),
                             ("above", "above_surface")):
            assert np.allclose(got[mine], getattr(want, theirs),
                               rtol=1e-12, atol=1e-15, equal_nan=True), (
                t, sun, r, depth, mine)
        deep_above = 0.5 * want.deep / (1 - 1.5 * want.deep)
        assert np.allclose(got["aboveDeep"], deep_above, rtol=1e-12,
                           equal_nan=True)
        if np.isnan(a).any():
            continue    # no colour where the source has a gap
        sky = np.asarray(data["sky"][f"{sun:g}"], float)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", jerlov.GamutWarning)
            warnings.simplefilter("ignore", jerlov.CoverageWarning)
            rgb = jerlov.spectrum_to_srgb(np.pi * want.above_surface * sky, wl,
                                          white=sky, clip=False)
        assert np.max(np.abs(_signed_gamma(np.asarray(linear)) - rgb)) < 1e-5


def test_the_fourth_page_agrees_with_the_example_on_when_the_bottom_fades():
    """The depth at which the bottom's part of rrs falls to 10 percent, by
    the page's values, against examples/ocean_colour_and_secchi.py part 13,
    which takes pure water's backscattering from
    pure_water_backscattering rather than the source's own model (Water.bb):
    the depths differ by up to 3.6 percent (DECISIONS.md section 121)."""
    data = _data(_page("shallow.html"))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        ex = _example_module("ocean_colour_and_secchi")
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            got = ex["shallow_part"](set())["depths"]
    depths = ex["SHALLOW_DEPTHS"]
    wl = list(data["wl"])
    for (t, rho), want in got.items():
        cols = [wl.index(w) for w in ex["SHALLOW_WL"]]
        a = np.asarray(data["a"][t], float)[cols]
        bb = np.asarray(data["bb"][t]["0.0183"], float)[cols]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
            r = jerlov.lee1999_shallow_rrs(a, bb, depth_m=depths[:, None],
                                           bottom_albedo=rho,
                                           sun_zenith_deg=ex["SUN_ZENITH_DEG"])
        share = r.bottom / r.rrs
        for k, column in enumerate(share.T):
            below = np.flatnonzero(column < ex["BOTTOM_SHARE"])
            mine = depths[below[0]] if below.size else np.inf
            if np.isinf(want[k]):
                assert np.isinf(mine), (t, rho, k)
            else:
                assert mine == pytest.approx(want[k], rel=0.04), (t, rho, k)


def _example_module(name):
    import runpy
    return runpy.run_path(str(ROOT / "examples" / f"{name}.py"), run_name=name)


# -- the first page: why the colour changes (DECISIONS.md section 128) -------

PRINTED = np.arange(400.0, 701.0, 25.0)


def test_the_printed_wavelengths_are_jerlovs():
    """The window is looked for among the wavelengths Table XXVII prints."""
    import csv
    import importlib.resources
    text = (importlib.resources.files("jerlov.data") / "jerlov1976_kd.csv"
            ).read_text()
    ok = {float(r["wavelength_nm"]) for r in csv.DictReader(text.splitlines())
          if r["status"] == "ok"}
    assert sorted(w for w in ok if 380 <= w <= 700) == PRINTED.tolist()
    assert np.array_equal(_tool().PRINTED_WL, PRINTED)


def test_the_windows_on_the_first_page_are_jerlovs():
    data = _data(_page("dive.html"))
    windows = {}
    for t in _tool().TYPES:
        kd = np.asarray(jerlov.water(t, source="jerlov1976").kd(PRINTED))
        windows[t] = float(PRINTED[np.argmin(kd)])
    assert data["window"] == windows
    assert windows["I"] == windows["II"] == 475.0
    assert (windows["III"], windows["1C"], windows["7C"], windows["9C"]) == \
        (500.0, 550.0, 550.0, 575.0)
    assert ("Kd is least at 475 nm for I to II, 500 nm for III, 550 nm for "
            "1C to 7C and 575 nm for 9C") in _flat(_page("dive.html"))


def test_the_first_pages_red_and_blue_figures_are_jerlovs():
    page = _flat(_page("dive.html"))
    kd = {t: jerlov.water(t, source="jerlov1976") for t in ("I", "9C")}
    all650 = [float(jerlov.water(t, source="jerlov1976").kd(650.0))
              for t in _tool().TYPES]
    aw = float(jerlov.pure_water_absorption_table(650.0, source="pope1997"))
    assert (f"At 650 nm pure water alone absorbs {aw:.2f} per metre, and Kd "
            f"is {min(all650):.2f} to {max(all650):.2f} per metre") in page
    blue = float(kd["9C"].kd(400.0)) / float(kd["I"].kd(400.0))
    red = float(kd["9C"].kd(650.0)) / float(kd["I"].kd(650.0))
    assert (f"At 400 nm Kd is {float(kd['I'].kd(400.0)):.3f} per metre in "
            f"type I and {float(kd['9C'].kd(400.0)):.1f} in 9C, {blue:.0f} "
            f"times as much; at 650 nm only {red:.1f} times") in page
    assert (aw, round(blue), round(red, 1)) == (0.34, 86, 2.1)


def test_the_first_pages_absorption_beyond_pure_water_is_williamsons():
    wl = np.array([412.0, 550.0])
    ratios = []
    for t in ("IB", "5C"):
        extra = (np.asarray(jerlov.water(t, source="williamson2022").a(wl))
                 - np.asarray(jerlov.pure_water_absorption(
                     wl, source="williamson2022")))
        ratios.append(extra[0] / extra[1])
    assert (f"does so {ratios[0]:.1f} times as strongly at 412 nm as at 550 "
            f"nm in IB, and {ratios[1]:.1f} times in 5C") in \
        _flat(_page("dive.html"))
    assert all(r > 1 for r in ratios)


def test_where_jerlovs_kd_lies_below_pure_water_is_said():
    aw = np.asarray(jerlov.pure_water_absorption_table(PRINTED,
                                                       source="pope1997"))
    below = {}
    for t in _tool().TYPES:
        r = np.asarray(jerlov.water(t, source="jerlov1976").kd(PRINTED)) / aw
        if np.any(r < 1):
            below[t] = (PRINTED[r < 1].tolist(), float(1 - r.min()))
    assert list(below) == ["I", "IA", "IB", "II"]
    worst = max(v[1] for v in below.values())
    page = _flat(_page("dive.html"))
    assert (f"At 675 and 700 nm the Kd Jerlov printed for types I to II lies "
            f"below it, by up to {100 * worst:.0f} %. Austin & Petzold (1986) "
            "pointed this out") in page
    assert "doi:10.1117/12.7973845" in page
    # It was known before 1.31.0 (DECISIONS.md section 129).
    data_md = " ".join(re.sub(r"^> ?", "", (ROOT / "DATA.md").read_text(),
                              flags=re.M).split())
    assert ("## 3. Jerlov's Kd falls below pure sea water (confirmed, "
            "documented in 1986)") in data_md
    assert ("at some wavelengths the values given by Jerlov for K are less "
            "than the values of absorption alone published by Morel and "
            "Prieur") in data_md
    assert sorted({w for v in below.values() for w in v[0]}) == [675.0, 700.0]


def test_the_first_pages_quotation_is_in_data_md():
    quote = ("These northern water masses are characterized by a relatively "
             "high amount of yellow substance.")
    assert quote in " ".join((ROOT / "DATA.md").read_text().split())
    assert f"“{quote}”" in _flat(_page("dive.html"))
    assert "Marine Optics, 1976, p. 137" in _flat(_page("dive.html"))


def test_the_first_page_embeds_pope_and_frys_absorption():
    data = _data(_page("dive.html"))
    tool = _tool()
    want = jerlov.pure_water_absorption_table(tool.DIVE_WL, source="pope1997")
    _close(np.round(want, 6).tolist(), data["aw"], "aw")

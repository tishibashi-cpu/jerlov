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

@pytest.mark.parametrize("name", ["dive.html", "disagree.html"])
def test_the_page_is_what_the_tool_writes_now(name):
    made = _tool().pages()[name]
    kept = _page(name)
    assert DATA_LINE.sub("", made) == DATA_LINE.sub("", kept), (
        f"docs/pages/{name} differs from what tools/site_pages.py writes; "
        "run it again")
    _close(_data(made), _data(kept), name)
    assert _data(kept)["jerlov_version"] == jerlov.__version__


@pytest.mark.parametrize("name", ["dive.html", "disagree.html"])
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
    ("a median 0.970 of HydroLight's, with 94.4 % of the cells within 10 %",
     "| With it and a clear sky | 0.970 | 94.4 percent |", "OPEN_QUESTIONS.md"),
    ("At 143 cells from 350 to 700 nm", "run at the 143 cells from 350 to 700 nm",
     "OPEN_QUESTIONS.md"),
    ("a median within 0.95 to 1.05 and 90 % of the cells within 10 %",
     "a median within 0.95 to 1.05 and 90 percent of the cells within 10 percent",
     "OPEN_QUESTIONS.md"),
    ("Petzold's measurements of 1971", "Petzold's measurements of 1971",
     "OPEN_QUESTIONS.md"),
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
    assert '_EXTRA_PAGES = ("dive.html", "disagree.html")' in conf
    # The docs workflow reads the built sitemap back.
    docs_yml = (ROOT / ".github" / "workflows" / "docs.yml").read_text()
    for page in ("index.html", "dive.html"):
        assert f"<loc>https://tishibashi-cpu.github.io/jerlov/{page}</loc>" in docs_yml


def test_the_zenodo_record_links_the_site():
    record = json.loads((ROOT / ".zenodo.json").read_text())
    assert {"identifier": "https://tishibashi-cpu.github.io/jerlov/",
            "relation": "isDocumentedBy", "scheme": "url"} in record["related_identifiers"]

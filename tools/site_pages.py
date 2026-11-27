"""Write the pages and figures of the site that are made from the package's values.

    python tools/site_pages.py              # writes docs/pages/ and docs/figures/
    python tools/site_pages.py --out DIR    # writes the pages elsewhere

DECISIONS.md section 109. ``docs/pages/dive.html`` shows the colour and
amount of daylight left at each depth in the ten Jerlov types;
``docs/pages/disagree.html`` gives the questions of OPEN_QUESTIONS.md a
figure each (questions 5 and 6 since 1.26.6, section 119);
``docs/pages/waters.html`` sets every source of each type side by side,
``docs/pages/shallow.html`` puts a bottom under the water (1.26.8,
section 121),
and ``docs/figures/`` holds the front page's figure and the gallery of
the examples (both since 1.26.7, section 120, drawn by
``tools/site_figures.py``). The templates are in ``tools/site_pages/``.
Every value the pages draw is taken from jerlov here and embedded as JSON;
the pages' scripts only multiply, integrate and draw. ``docs/conf.py``
copies ``docs/pages/`` to the site's root.

``tests/test_site_pages.py`` checks that the pages in ``docs/pages/`` are
what this writes now, so run it again after any change to a value the
pages use, and at every release (the pages name the version).
"""

from __future__ import annotations

import argparse
import csv
import json
import warnings
from pathlib import Path

import numpy as np

import jerlov
from jerlov.colour import SRGB_WHITEPOINT_XYZ, XYZ_TO_LINEAR_SRGB

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "tools" / "site_pages"
OUT = ROOT / "docs" / "pages"

TYPES = ("I", "IA", "IB", "II", "III", "1C", "3C", "5C", "7C", "9C")

# -- the first page: daylight on the way down -------------------------------

#: 380-700 nm: where both the sky model and the colour matching matter.
DIVE_WL = np.arange(380.0, 701.0)
#: The sky of examples/sunlight_and_d65.py: Gregg & Carder's Table 5
#: standard conditions (p. 1670), 21 June, a visibility of 10 km.
SUN_DEG = 30.0
VISIBILITY_KM = 10.0
ATMOSPHERE = dict(day_of_year=172, pressure_hpa=1013.25, air_mass_type=1,
                  relative_humidity=80.0, precipitable_water_cm=1.5,
                  wind_speed_24h=3.0, wind_speed=5.0, ozone_du=300.0)


#: The wavelengths Jerlov's Table XXVII prints within the page's range
#: (DATA.md: 16 wavelengths from 310 to 700 nm; the rest of the 1 nm
#: dataset is interpolated). The window is looked for among these only.
PRINTED_WL = np.arange(400.0, 701.0, 25.0)
#: The pure water absorption the panel "Why the colour changes" draws.
PURE_WATER_SOURCE = "pope1997"


def _rounded(values, digits):
    return [None if not np.isfinite(v) else round(float(v), digits)
            for v in np.asarray(values, dtype=float)]


def dive_inputs() -> dict:
    """The values the first page embeds."""
    sky = jerlov.gregg1990_irradiance(DIVE_WL, sun_zenith_deg=SUN_DEG,
                                      visibility_km=VISIBILITY_KM,
                                      **ATMOSPHERE)
    cmf_wl, cmf = jerlov.cie_1931_cmf()
    refl = {}
    for material in jerlov.USGS2017_MATERIALS:
        r = jerlov.usgs2017_reflectance(material)
        refl[material] = _rounded(
            np.interp(DIVE_WL, r.wavelengths, r.reflectance), 5)
    return dict(
        jerlov_version=jerlov.__version__,
        wl=DIVE_WL.tolist(),
        es=_rounded(sky.below, 6),
        sun_zenith=SUN_DEG,
        kd={t: _rounded(jerlov.water(t, source="jerlov1976").kd(DIVE_WL), 5)
            for t in TYPES},
        aw=_rounded(jerlov.pure_water_absorption_table(
            DIVE_WL, source=PURE_WATER_SOURCE), 6),
        window={t: window_nm(t) for t in TYPES},
        cmf=[_rounded(np.interp(DIVE_WL, cmf_wl, cmf[:, k]), 7)
             for k in range(3)],
        refl=refl,
        xyz_to_srgb=np.asarray(XYZ_TO_LINEAR_SRGB).tolist(),
        srgb_white=[float(v) for v in SRGB_WHITEPOINT_XYZ],
    )


def window_nm(water_type: str) -> float:
    """Where among Jerlov's printed wavelengths a type's Kd is least."""
    kd = np.asarray(jerlov.water(water_type, source="jerlov1976").kd(PRINTED_WL))
    return float(PRINTED_WL[int(np.argmin(kd))])


def _types_at(windows: dict, nm: float) -> str:
    names = [t for t in TYPES if windows[t] == nm]
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{names[0]} to {names[-1]}"


def why_figures() -> dict:
    """The numbers of the panel "Why the colour changes" (DECISIONS.md
    section 128)."""
    windows = {t: window_nm(t) for t in TYPES}
    order = sorted(set(windows.values()))
    parts = [f"{nm:.0f} nm for {_types_at(windows, nm)}" for nm in order]
    window = ", ".join(parts[:-1]) + f" and {parts[-1]}"
    kd = {t: jerlov.water(t, source="jerlov1976") for t in TYPES}
    kd650 = [float(kd[t].kd(650.0)) for t in TYPES]
    aw650 = float(jerlov.pure_water_absorption_table(650.0,
                                                     source=PURE_WATER_SOURCE))
    blue = float(kd["9C"].kd(400.0)) / float(kd["I"].kd(400.0))
    red = float(kd["9C"].kd(650.0)) / float(kd["I"].kd(650.0))
    beyond = {}
    for t in ("IB", "5C"):
        w = jerlov.water(t, source="williamson2022")
        extra = (np.asarray(w.a(np.array([412.0, 550.0])))
                 - np.asarray(jerlov.pure_water_absorption(
                     np.array([412.0, 550.0]), source="williamson2022")))
        beyond[t] = f"{extra[0] / extra[1]:.1f}"
    aw_printed = np.asarray(jerlov.pure_water_absorption_table(
        PRINTED_WL, source=PURE_WATER_SOURCE))
    below_types, below_wl, below_most = [], set(), 0.0
    for t in TYPES:
        ratio = np.asarray(kd[t].kd(PRINTED_WL)) / aw_printed
        if np.any(ratio < 1):
            below_types.append(t)
            below_wl.update(float(w) for w in PRINTED_WL[ratio < 1])
            below_most = max(below_most, float(1 - ratio.min()))
    below_nm = sorted(below_wl)
    return {
        "BELOW_TYPES": (f"{below_types[0]} to {below_types[-1]}"
                        if len(below_types) > 1 else below_types[0]),
        "BELOW_NM": (", ".join(f"{w:.0f}" for w in below_nm[:-1])
                     + f" and {below_nm[-1]:.0f}" if len(below_nm) > 1
                     else f"{below_nm[0]:.0f}"),
        "BELOW_PERCENT": f"{100 * below_most:.0f}",
        "WINDOWS": window,
        "AW650": f"{aw650:.2f}",
        "KD650_LOW": f"{min(kd650):.2f}",
        "KD650_HIGH": f"{max(kd650):.2f}",
        "KD400_I": f"{float(kd['I'].kd(400.0)):.3f}",
        "KD400_9C": f"{float(kd['9C'].kd(400.0)):.1f}",
        "BLUE_RATIO": f"{blue:.0f}",
        "RED_RATIO": f"{red:.1f}",
        "BEYOND_IB": beyond["IB"],
        "BEYOND_5C": beyond["5C"],
    }


def dive_figures(inputs: dict) -> dict:
    """The numbers the first page's prose gives: the PAR 1 percent depth of
    type I with one Kd all the way down, and through the typical profile."""
    wl = np.asarray(inputs["wl"], dtype=float)
    es = np.asarray(inputs["es"], dtype=float)
    flat = jerlov.par_profile(es, wl, 0.0, kd=jerlov.water("I", source="jerlov1976"),
                              unit="energy")
    descent = jerlov.descend("I", jerlov.profile_depth("I"), wl)
    layered = jerlov.par_profile(es, wl, 0.0, kd=descent, unit="energy")
    return {
        **why_figures(),
        "I_ONE_KD": f"{flat.depth_of_fraction():.0f}",
        "I_LAYERED": f"{layered.depth_of_fraction():.0f}",
        "SUN": f"{SUN_DEG:g}",
        "VISIBILITY": f"{VISIBILITY_KM:g}",
    }


# -- the second page: where the sources disagree ----------------------------

PURE_WATERS = ("pope1997", "mason2016", "lee2015", "smith1981", "morel2007")
PURE_WATER_WL = np.arange(350.0, 601.0, 2.5)
#: The types Williamson & Hollins give.
MEASURED_TYPES = ("IB", "II", "III", "1C", "3C", "5C")
#: What the unrecorded conditions are, as examples/closure_with_jerlov_kd.py
#: varies them.
CONDITIONS = ("sun_deg", "station", "pure_water")


def _closure() -> dict:
    """Kd by Monte Carlo from Williamson & Hollins's a and b, with pure
    water's own scattering and a sky (DECISIONS.md section 94), over Jerlov's
    (1976), and the reach of the conditions neither source records."""
    with open(ROOT / "examples" / "data" / "sm_closure" / "runs.csv") as handle:
        runs = [r for r in csv.DictReader(handle) if r["set"] == "williamson2022"]
    column = "kd_first_penetration_depth"

    def key(r):
        return (r["water_type"], int(r["wavelength_nm"]))

    base = {key(r): float(r[column]) for r in runs if r["factor"] == "base"}
    moves = {}
    for factor in CONDITIONS:
        changes = [float(r[column]) / base[key(r)]
                   for r in runs if r["factor"] == factor]
        moves[factor] = (min(changes), max(changes))
    up = float(np.prod([high for _, high in moves.values()]))
    down = float(np.prod([low for low, _ in moves.values()]))
    types = sorted({t for t, _ in base}, key=TYPES.index)
    wavelengths = sorted({wl for _, wl in base})
    cells = []
    for t in types:
        water = jerlov.water(t, source="jerlov1976")
        for wl in wavelengths:
            ratio = base[(t, wl)] / float(water.kd(float(wl)))
            cells.append(dict(type=t, wl=wl, ratio=round(ratio, 3),
                              beyond=bool(ratio * up < 1 or ratio * down > 1)))
    return dict(types=types, wl=wavelengths, cells=cells,
                down=round(down, 3), up=round(up, 3))


def _hydrolight() -> dict:
    """Question 4 (DECISIONS.md section 119): the Monte Carlo's Kd, with
    pure water's own scattering and a clear sky, over HydroLight's as
    Solonenko & Mobley printed it, at the 143 cells."""
    with open(ROOT / "examples" / "data" / "sm_closure" / "runs.csv") as handle:
        runs = [r for r in csv.DictReader(handle)
                if r["set"] == "solonenko2015" and r["factor"] == "base"]
    types = sorted({r["water_type"] for r in runs}, key=TYPES.index)
    wavelengths = sorted({int(r["wavelength_nm"]) for r in runs})
    cells = [dict(type=r["water_type"], wl=int(r["wavelength_nm"]),
                  ratio=round(float(r["kd_to_10_percent"])
                              / float(r["kd_hydrolight"]), 3))
             for r in runs]
    return dict(types=types, wl=wavelengths, cells=cells)


def _example(name: str) -> dict:
    """An example's functions, read without running its main."""
    import runpy
    return runpy.run_path(str(ROOT / "examples" / f"{name}.py"),
                          run_name=name)


def _shallow() -> dict:
    """Question 5 (DECISIONS.md section 119): the shallow-water model over
    the Monte Carlo, with the two groups as the example defines them."""
    ex = _example("shallow_water_closure")
    grid = ex["read"]("monte_carlo.csv")
    q, water, dark = ex["groups"](grid)
    share = (grid["bw"] / 2) / grid["bb"]
    runs = []
    for i in range(len(q)):
        runs.append(dict(share=round(float(share[i]), 4),
                         ratio=round(float(q[i]), 4),
                         group=1 if water[i] else 2 if dark[i] else 0))
    paper = ex["read"]("lee1998_runs.csv")
    held = ex["read"]("water_share.csv")
    ratio = held["model"] / held["monte_carlo"]
    lines = []
    for key in sorted(set(zip(held["u"], held["a"], held["depth_m"]))):
        pick = ((held["u"] == key[0]) & (held["a"] == key[1])
                & (held["depth_m"] == key[2]))
        order = np.argsort(held["water_share"][pick])
        lines.append(dict(
            u=float(key[0]), a=float(key[1]),
            depth=None if not np.isfinite(key[2]) else float(key[2]),
            share=[float(x) for x in held["water_share"][pick][order]],
            ratio=_rounded(ratio[pick][order], 4)))
    return dict(runs=runs, paper_share_max=round(
        float(paper["water_share"].max()), 4), held=lines, miss=ex["MISS"])


#: The sun angles at which question 6's figure sets the paper's fits.
FIG13_FIT_SUNS = (15.0, 30.0, 45.0)
#: The reading's accuracy, as OPEN_QUESTIONS.md question 6 quotes it
#: (a symbol on its own within 0.0006 of its value, DECISIONS.md section
#: 118): a fit nearer a band than this is drawn as inside it.
FIG13_ACCURACY = 0.0006


def _fig13() -> dict:
    """Question 6 (DECISIONS.md section 119): the paper's Fig. 13 as read
    (section 118) and its own Eq. (B1), nothing from the archive."""
    with open(ROOT / "examples" / "data" / "fq_at_45_degrees"
              / "fig13.csv") as handle:
        spans = [{k: float(v) for k, v in r.items()}
                 for r in csv.DictReader(handle)]
    columns = sorted({s["chl_mg_m3"] for s in spans})
    fits = []
    for chl in columns:
        for wl in (412.5, 490.0, 510.0, 560.0, 620.0, 660.0):
            f0 = jerlov.morel2002_nadir_fq(wl, chlorophyll_mg_m3=chl,
                                           sun_zenith_deg=0.0).f
            for sun in FIG13_FIT_SUNS:
                f = jerlov.morel2002_nadir_fq(wl, chlorophyll_mg_m3=chl,
                                              sun_zenith_deg=sun).f
                fits.append(dict(chl=chl, wl=wl, sun=sun,
                                 value=round(f0 / f, 4)))
    return dict(columns=columns, suns=list(FIG13_FIT_SUNS),
                accuracy=FIG13_ACCURACY,
                spans=[dict(chl=s["chl_mg_m3"], top=s["top_f0_over_f"],
                            bottom=s["bottom_f0_over_f"]) for s in spans],
                fits=fits)


def disagree_inputs() -> dict:
    """The values the second page embeds."""
    pure = {}
    for source in PURE_WATERS:
        values = []
        for wl in PURE_WATER_WL:
            try:
                values.append(round(float(jerlov.pure_water_absorption_table(
                    float(wl), source=source)), 6))
            except ValueError:  # outside what the source gives
                values.append(None)
        pure[source] = values

    def ratio(wl):
        return round(float(
            jerlov.pure_water_absorption_table(wl, source="pope1997")
            / jerlov.pure_water_absorption_table(wl, source="mason2016")), 2)

    petzold = []
    for station in jerlov.PETZOLD_STATIONS:
        f = jerlov.petzold_scattering(station)
        petzold.append(dict(
            station=station,
            angles=[float(a) for a in f.angles_deg],
            phase=_rounded(np.asarray(f.vsf) / f.b, 6),
            below=round(float(f.fraction_below_0_1_deg), 4)))

    editions = []
    w68 = {t: jerlov.water(t, source="jerlov1968") for t in TYPES}
    w76 = {t: jerlov.water(t, source="jerlov1976") for t in TYPES}
    both = [float(wl) for wl in w68["I"].wavelengths if 375 <= wl <= 700]
    for t in TYPES:
        for wl in both:
            editions.append(dict(type=t, wl=wl, ratio=round(
                float(w76[t].kd(wl)) / float(w68[t].kd(wl)), 3)))

    two = {}
    for source in ("williamson2022", "solonenko2015"):
        two[source] = {}
        for t in MEASURED_TYPES:
            w = jerlov.water(t, source=source)
            wl = np.asarray(w.wavelengths, dtype=float)
            keep = (wl >= 400) & (wl <= 700) & (wl % 5 == 0)
            c = np.asarray(w.a(wl[keep]), dtype=float) \
                + np.asarray(w.b(wl[keep]), dtype=float)
            two[source][t] = dict(wl=wl[keep].tolist(), c=_rounded(c, 4))

    return dict(
        jerlov_version=jerlov.__version__,
        pure_water=dict(wl=PURE_WATER_WL.tolist(), aw=pure,
                        pope_over_mason={f"{wl:.1f}": ratio(wl)
                                         for wl in (380.0, 400.0, 420.0, 440.0)}),
        petzold=petzold,
        closure=_closure(),
        editions=dict(types=list(TYPES), wl=both, cells=editions),
        two_sources=two,
        hydrolight=_hydrolight(),
        shallow=_shallow(),
        fig13=_fig13(),
    )


# -- the third page: the waters side by side (DECISIONS.md section 120) -----

#: What the third page draws: (quantity, source, the method of Water).
WATER_SERIES = (
    ("a", "williamson2022", "a"), ("a", "solonenko2015", "a"),
    ("b", "williamson2022", "b"), ("b", "solonenko2015", "b"),
    ("c", "williamson2022", "c"), ("c", "solonenko2015", "c"),
    ("Kd", "jerlov1968", "kd"), ("Kd", "jerlov1976", "kd"),
    ("Kd", "austin1986", "kd"), ("Kd", "solonenko2015", "kd_hydrolight"),
)
#: Williamson & Hollins measured from 412 to 715 nm; beyond it their table
#: is a model's (their source's caveat), so the page starts at 415 nm.
WATER_RANGE = {"williamson2022": (415.0, 700.0)}


def waters_inputs() -> dict:
    """The values the third page embeds: what water() returns, every 5 nm
    from 350 to 700 nm (or the source's own wavelengths where coarser)."""
    series = []
    for quantity, source, method in WATER_SERIES:
        lo, hi = WATER_RANGE.get(source, (350.0, 700.0))
        for t in jerlov.SOURCES[source].water_types:
            w = jerlov.water(t, source=source)
            wl = np.asarray(w.wavelengths, dtype=float)
            keep = (wl >= lo) & (wl <= hi) & (wl % 5 == 0)
            values = np.asarray(getattr(w, method)(wl[keep]), dtype=float)
            series.append(dict(quantity=quantity, source=source, type=t,
                               wl=wl[keep].tolist(), v=_rounded(values, 5)))
    sources = {}
    for _, source, _ in WATER_SERIES:
        src = jerlov.SOURCES[source]
        sources[source] = dict(citation=src.citation,
                               caveats=list(src.caveats),
                               measured=bool(src.measured))
    return dict(jerlov_version=jerlov.__version__, types=list(TYPES),
                series=series, sources=sources)


# -- the fourth page: when the bottom shows through (DECISIONS.md section 121) -

#: The runs' wavelengths, 400-700 nm (Lee et al. 1998, Table 1), every 5 nm.
SHALLOW_WL = np.arange(400.0, 701.0, 5.0)
#: The suns of the runs (1998, Table 1), degrees from the zenith.
SHALLOW_SUNS = (0.0, 30.0, 60.0)
#: The particles' bbp/bp of examples/ocean_colour_and_secchi.py; 0.0183 is
#: that of Petzold's average-particle phase function, which the runs used.
SHALLOW_RATIOS = (0.005, 0.0183, 0.03)
#: The source with a and b for all ten types.
SHALLOW_SOURCE = "solonenko2015"


def shallow_inputs() -> dict:
    """The values the fourth page embeds."""
    from jerlov import ocean_colour as oc
    a, bb, flags = {}, {}, {}
    for t in TYPES:
        w = jerlov.water(t, source=SHALLOW_SOURCE)
        with warnings.catch_warnings(record=True) as record:
            # What the source flags, in the package's own words: the page
            # shows them beside the type.
            warnings.simplefilter("always", jerlov.ProvenanceWarning)
            a[t] = _rounded(w.a(SHALLOW_WL), 7)
            bb[t] = {f"{r:g}": _rounded(w.bb(SHALLOW_WL,
                                              particle_backscatter_ratio=r), 9)
                     for r in SHALLOW_RATIOS}
        flags[t] = list(dict.fromkeys(
            str(x.message) for x in record
            if issubclass(x.category, jerlov.ProvenanceWarning)))
    sky = {}
    for sun in SHALLOW_SUNS:
        s = jerlov.gregg1990_irradiance(SHALLOW_WL, sun_zenith_deg=sun,
                                        visibility_km=VISIBILITY_KM,
                                        **ATMOSPHERE)
        sky[f"{sun:g}"] = _rounded(s.above, 6)
    cmf_wl, cmf = jerlov.cie_1931_cmf()
    return dict(
        jerlov_version=jerlov.__version__,
        wl=SHALLOW_WL.tolist(), types=list(TYPES),
        suns=list(SHALLOW_SUNS), ratios=list(SHALLOW_RATIOS),
        a=a, bb=bb, flags=flags, sky=sky,
        model=dict(g=list(oc._LEE1999_G), dc=list(oc._LEE1999_D_COLUMN),
                   db=list(oc._LEE1999_D_BOTTOM), zeta=oc._LEE1999_ZETA,
                   gamma=oc._LEE1999_GAMMA, n=oc._LEE1998_N,
                   depth=list(oc._LEE1998_DEPTH), u_max=oc._LEE1998_U),
        cmf=[_rounded(np.interp(SHALLOW_WL, cmf_wl, cmf[:, k]), 7)
             for k in range(3)],
        xyz_to_srgb=np.asarray(XYZ_TO_LINEAR_SRGB).tolist(),
        srgb_white=[float(v) for v in SRGB_WHITEPOINT_XYZ],
    )


def shallow_figures() -> dict:
    """The numbers the fourth page's prose gives: the model against the
    Monte Carlo of DECISIONS.md section 113, from question 5's data."""
    s = _shallow()
    q = np.array([r["ratio"] for r in s["runs"]])
    return {
        "MC_RUNS": f"{len(q)}",
        "MC_MEDIAN": f"{np.median(q):.3f}",
        "MC_WITHIN": f"{100 * np.mean(np.abs(q - 1) <= s['miss']):.1f}",
        "VISIBILITY": f"{VISIBILITY_KM:g}",
    }


# -- writing -----------------------------------------------------------------

def _fill(template: str, data: dict, figures: dict, core: str = "") -> str:
    page = template.replace("/*DATA*/", json.dumps(data, separators=(",", ":")))
    page = page.replace("/*CORE*/", core)
    for name, value in figures.items():
        page = page.replace("{{" + name + "}}", value)
    left = [part.split("}}")[0] for part in page.split("{{")[1:]]
    if left:
        raise ValueError(f"placeholders left unfilled: {left}")
    return page


def pages() -> dict[str, str]:
    """The pages, by file name."""
    with warnings.catch_warnings():
        # Petzold's extension below 0.1 degree, and the 1968 table's values
        # below pure water, warn; the page is about exactly those.
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        dive = dive_inputs()
        disagree = disagree_inputs()
        waters = waters_inputs()
        shallow = shallow_inputs()
        figures = dive_figures(dive)
        shallow_numbers = shallow_figures()
    return {
        "dive.html": _fill((TEMPLATES / "dive.html").read_text(), dive, figures,
                           (TEMPLATES / "dive_core.js").read_text()),
        "disagree.html": _fill((TEMPLATES / "disagree.html").read_text(),
                               disagree, {}),
        "waters.html": _fill((TEMPLATES / "waters.html").read_text(),
                             waters, {}),
        "shallow.html": _fill((TEMPLATES / "shallow.html").read_text(),
                              shallow, shallow_numbers,
                              (TEMPLATES / "dive_core.js").read_text()
                              + (TEMPLATES / "shallow_core.js").read_text()),
    }


#: The static figures of the documentation (DECISIONS.md section 120).
FIGURES = ROOT / "docs" / "figures"


def figures() -> dict[str, str]:
    """The SVGs of tools/site_figures.py, by file name."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "site_figures", ROOT / "tools" / "site_figures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.figures()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--figures", type=Path, default=FIGURES)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    for name, text in pages().items():
        (args.out / name).write_text(text)
        print(f"wrote {args.out / name} ({len(text.encode()):,} bytes)")
    args.figures.mkdir(parents=True, exist_ok=True)
    for name, text in figures().items():
        (args.figures / name).write_text(text)
        print(f"wrote {args.figures / name} ({len(text.encode()):,} bytes)")


if __name__ == "__main__":
    main()

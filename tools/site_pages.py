"""Write the two pages of the site that are made from the package's values.

    python tools/site_pages.py              # writes docs/pages/
    python tools/site_pages.py --out DIR    # writes them elsewhere

DECISIONS.md section 109. ``docs/pages/dive.html`` shows the colour and
amount of daylight left at each depth in the ten Jerlov types;
``docs/pages/disagree.html`` gives the questions of OPEN_QUESTIONS.md a
figure each (questions 5 and 6 since 1.26.6, section 119). The templates are in ``tools/site_pages/``. Every value the
pages draw is taken from jerlov here and embedded as JSON; the pages'
scripts only multiply, integrate and draw. ``docs/conf.py`` copies
``docs/pages/`` to the site's root.

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
        cmf=[_rounded(np.interp(DIVE_WL, cmf_wl, cmf[:, k]), 7)
             for k in range(3)],
        refl=refl,
        xyz_to_srgb=np.asarray(XYZ_TO_LINEAR_SRGB).tolist(),
        srgb_white=[float(v) for v in SRGB_WHITEPOINT_XYZ],
    )


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
        figures = dive_figures(dive)
    return {
        "dive.html": _fill((TEMPLATES / "dive.html").read_text(), dive, figures,
                           (TEMPLATES / "dive_core.js").read_text()),
        "disagree.html": _fill((TEMPLATES / "disagree.html").read_text(),
                               disagree, {}),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    for name, text in pages().items():
        (args.out / name).write_text(text)
        print(f"wrote {args.out / name} ({len(text.encode()):,} bytes)")


if __name__ == "__main__":
    main()

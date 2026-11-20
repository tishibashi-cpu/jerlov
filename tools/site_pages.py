"""Write the two pages of the site that are made from the package's values.

    python tools/site_pages.py              # writes docs/pages/
    python tools/site_pages.py --out DIR    # writes them elsewhere

DECISIONS.md section 109. ``docs/pages/dive.html`` shows the colour and
amount of daylight left at each depth in the ten Jerlov types;
``docs/pages/disagree.html`` gives the four questions of OPEN_QUESTIONS.md
a figure each. The templates are in ``tools/site_pages/``. Every value the
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

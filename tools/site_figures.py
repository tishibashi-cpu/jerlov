"""The static figures of the documentation site: DECISIONS.md section 120.

``tools/site_pages.py`` calls :func:`figures` and writes each SVG into
``docs/figures/``: one for the front page (``kd_types.svg``) and six cards
for the gallery of examples. Every value drawn comes from jerlov here; the
SVGs are plain files with fixed colours, drawn on white as the
documentation's theme is.
"""

from __future__ import annotations

import warnings
from xml.sax.saxutils import escape

import numpy as np

import jerlov

TYPES = ("I", "IA", "IB", "II", "III", "1C", "3C", "5C", "7C", "9C")
#: One colour per type: the oceanic types in blues, the coastal in greens
#: and browns, darker for the clearer and the more turbid ends.
TYPE_COLOURS = {
    "I": "#08306b", "IA": "#1d5fa0", "IB": "#3a87c0", "II": "#6aaed6",
    "III": "#8fb8d0", "1C": "#3a8a3a", "3C": "#6b9a2e", "5C": "#a5882a",
    "7C": "#a5682a", "9C": "#6e4219",
}
INK, MUTED, GRID = "#12232b", "#56707b", "#dde6ea"
SERIES = ("#0b7f99", "#c8641a", "#7a52b3", "#3a8a3a", "#c23a6b", "#56707b")
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

#: The daylight of dive.html (DECISIONS.md section 109): Gregg & Carder's
#: model, the sun 30 degrees from the zenith, 21 June, a visibility of 10 km.
WL = np.arange(380.0, 701.0)
SUN_DEG = 30.0
ATMOSPHERE = dict(day_of_year=172, pressure_hpa=1013.25, air_mass_type=1,
                  relative_humidity=80.0, precipitable_water_cm=1.5,
                  wind_speed_24h=3.0, wind_speed=5.0, ozone_du=300.0)


def surface() -> np.ndarray:
    return np.asarray(jerlov.gregg1990_irradiance(
        WL, sun_zenith_deg=SUN_DEG, visibility_km=10.0, **ATMOSPHERE).below,
        dtype=float)


def colour_at(water_type: str, depth_m: float, es: np.ndarray) -> str:
    """The daylight left at a depth as sRGB, white-balanced at the surface,
    Kd of Jerlov (1976) constant with depth."""
    kd = np.asarray(jerlov.water(water_type, source="jerlov1976").kd(WL),
                    dtype=float)
    rgb = jerlov.spectrum_to_srgb(es * np.exp(-kd * depth_m), WL, white=es)
    return "#" + "".join(f"{int(round(255 * min(max(float(c), 0.0), 1.0))):02x}"
                         for c in rgb)


# -- a small SVG writer ------------------------------------------------------

class Svg:
    def __init__(self, width: int, height: int, label: str):
        self.w, self.h = width, height
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} '
            f'{height}" width="{width}" height="{height}" role="img" '
            f'aria-label="{escape(label)}" font-family="{FONT}" '
            f'font-size="10">',
            f'<rect width="{width}" height="{height}" fill="#ffffff"/>']

    def add(self, text: str) -> None:
        self.parts.append(text)

    def line(self, x1, y1, x2, y2, stroke=GRID, width=1.0, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" '
                 f'y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{d}/>')

    def text(self, x, y, s, anchor="start", fill=MUTED, size=10, weight=None):
        w = f' font-weight="{weight}"' if weight else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
                 f'fill="{fill}" font-size="{size}"{w}>{escape(s)}</text>')

    def path(self, points, stroke, width=1.8):
        d, pen = "", False
        for p in points:
            if p is None or not all(np.isfinite(p)):
                pen = False
                continue
            d += ("L" if pen else "M") + f"{p[0]:.1f},{p[1]:.1f}"
            pen = True
        if d:
            self.add(f'<path d="{d}" fill="none" stroke="{stroke}" '
                     f'stroke-width="{width}" stroke-linejoin="round"/>')

    def rect(self, x, y, w, h, fill, stroke=None, rx=2):
        s = f' stroke="{stroke}"' if stroke else ""
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" '
                 f'height="{h:.1f}" rx="{rx}" fill="{fill}"{s}/>')

    def done(self) -> str:
        return "\n".join(self.parts + ["</svg>"]) + "\n"


def lin(d0, d1, r0, r1):
    return lambda x: r0 + (np.asarray(x, dtype=float) - d0) / (d1 - d0) * (r1 - r0)


def logs(d0, d1, r0, r1):
    return lambda x: r0 + (np.log10(np.asarray(x, dtype=float)) - np.log10(d0)) \
        / (np.log10(d1) - np.log10(d0)) * (r1 - r0)


def spread(ys, gap):
    """Move label positions apart, in order, so that none is nearer than
    ``gap`` to the next."""
    order = np.argsort(ys)
    out = np.array(ys, dtype=float)
    for k in range(1, len(order)):
        prev, cur = order[k - 1], order[k]
        out[cur] = max(out[cur], out[prev] + gap)
    return out


def axes(svg, x, y, m, xticks, yticks, xfmt, yfmt, xlabel, ylabel=None):
    for g in yticks:
        svg.line(m["l"], float(y(g)), svg.w - m["r"], float(y(g)))
        svg.text(m["l"] - 5, float(y(g)) + 3, yfmt(g), anchor="end")
    for g in xticks:
        svg.text(float(x(g)), svg.h - m["b"] + 13, xfmt(g), anchor="middle")
    svg.text((m["l"] + svg.w - m["r"]) / 2, svg.h - 3, xlabel, anchor="middle")
    if ylabel:
        svg.text(m["l"], m["t"] - 6, ylabel)


# -- the front page ----------------------------------------------------------

def kd_types(es: np.ndarray) -> str:
    W, H = 680, 420
    m = dict(l=46, r=40, t=24, b=124)
    svg = Svg(W, H, "Kd of the ten Jerlov water types, 350 to 700 nm, and "
              "the colour of the daylight left at 10 m in each")
    wl = np.arange(350.0, 701.0, 5.0)
    x = lin(350, 700, m["l"], W - m["r"])
    y = logs(0.015, 5.0, H - m["b"], m["t"])
    axes(svg, x, y, m, range(350, 701, 50), (0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5),
         lambda v: f"{v}", lambda v: f"{v:g}", "", "Kd, 1/m (Jerlov 1976)")
    ends = []
    for t in TYPES:
        kd = np.asarray(jerlov.water(t, source="jerlov1976").kd(wl), dtype=float)
        svg.path(list(zip(x(wl), y(kd))), TYPE_COLOURS[t])
        ends.append(float(y(kd[-1])))
    for t, ly in zip(TYPES, spread(ends, 10.5)):
        svg.text(W - m["r"] + 4, ly + 3, t, fill=TYPE_COLOURS[t], weight=700)
    svg.text((m["l"] + W - m["r"]) / 2, H - m["b"] + 27, "wavelength, nm",
             anchor="middle")
    # The strip: the daylight left at 10 m.
    top = H - 70
    cw = (W - m["l"] - m["r"]) / len(TYPES)
    svg.text(m["l"], top - 8, "the daylight left at 10 m, white-balanced at "
             "the surface", fill=INK)
    for k, t in enumerate(TYPES):
        x0 = m["l"] + k * cw
        svg.rect(x0 + 2, top, cw - 4, 40, colour_at(t, 10.0, es), stroke=GRID)
        svg.text(x0 + cw / 2, top + 54, t, anchor="middle", fill=INK)
    return svg.done()


# -- the gallery -------------------------------------------------------------

CARD = (360, 230)
CM = dict(l=42, r=12, t=22, b=30)


def card_par(es: np.ndarray) -> str:
    W, H = CARD
    svg = Svg(W, H, "PAR left with depth in the ten Jerlov types")
    depths = np.arange(0.0, 100.1, 1.0)
    x = lin(0, 100, CM["l"], W - CM["r"])
    y = logs(1e-3, 1.0, H - CM["b"], CM["t"])
    axes(svg, x, y, CM, (0, 25, 50, 75, 100), (1e-3, 1e-2, 1e-1, 1.0),
         lambda v: f"{v}", lambda v: f"{100 * v:g} %", "depth, m",
         "PAR left, share of the surface")
    for t in TYPES:
        p = jerlov.par_profile(es, WL, depths,
                               kd=jerlov.water(t, source="jerlov1976"),
                               unit="energy")
        f = np.asarray(p.fraction, dtype=float)
        keep = f >= 1e-3
        svg.path(list(zip(x(depths[keep]), y(f[keep]))), TYPE_COLOURS[t], 1.5)
    return svg.done()


def card_sources() -> str:
    W, H = CARD
    svg = Svg(W, H, "Kd of Jerlov type II from four sources")
    x = lin(350, 700, CM["l"], W - CM["r"])
    y = logs(0.02, 1.0, H - CM["b"], CM["t"])
    axes(svg, x, y, CM, (400, 500, 600, 700), (0.02, 0.05, 0.1, 0.2, 0.5, 1.0),
         lambda v: f"{v}", lambda v: f"{v:g}", "wavelength, nm",
         "Kd of type II, 1/m")
    series = [("jerlov1968", "kd", "Jerlov 1968"),
              ("jerlov1976", "kd", "Jerlov 1976"),
              ("austin1986", "kd", "Austin & Petzold 1986"),
              ("solonenko2015", "kd_hydrolight", "HydroLight, S&M 2015")]
    for k, (source, what, name) in enumerate(series):
        w = jerlov.water("II", source=source)
        wl = np.asarray([v for v in w.wavelengths if 350 <= v <= 700], float)
        kd = np.asarray(getattr(w, what)(wl), dtype=float)
        svg.path(list(zip(x(wl), y(kd))), SERIES[k], 1.6)
        svg.rect(CM["l"] + 8, CM["t"] + 6 + 13 * k, 10, 3, SERIES[k], rx=1)
        svg.text(CM["l"] + 22, CM["t"] + 10 + 13 * k, name, fill=INK)
    return svg.done()


def card_colours(es: np.ndarray) -> str:
    W, H = CARD
    svg = Svg(W, H, "The colour of the daylight left at 0, 5, 10 and 20 m "
              "in Jerlov types IB, 1C and 5C")
    depths = (0.0, 5.0, 10.0, 20.0)
    types = ("IB", "1C", "5C")
    L, T, cw, ch = 46, 34, 74, 56
    svg.text(L, 16, "daylight left, white-balanced at the surface", fill=INK)
    for j, d in enumerate(depths):
        svg.text(L + cw * j + cw / 2, T - 6, f"{d:g} m", anchor="middle")
    for i, t in enumerate(types):
        svg.text(L - 8, T + ch * i + ch / 2 + 4, t, anchor="end", fill=INK,
                 size=12)
        for j, d in enumerate(depths):
            svg.rect(L + cw * j + 2, T + ch * i + 2, cw - 4, ch - 4,
                     colour_at(t, d, es), stroke=GRID, rx=4)
    return svg.done()


def card_heating() -> str:
    W, H = CARD
    svg = Svg(W, H, "Fraction of the solar irradiance left with depth, "
              "the oceanic Jerlov types")
    depths = np.arange(0.5, 100.1, 0.5)
    x = lin(0, 100, CM["l"], W - CM["r"])
    y = logs(1e-3, 1.0, H - CM["b"], CM["t"])
    axes(svg, x, y, CM, (0, 25, 50, 75, 100), (1e-3, 1e-2, 1e-1, 1.0),
         lambda v: f"{v}", lambda v: f"{100 * v:g} %", "depth, m",
         "solar irradiance left (Paulson & Simpson)")
    for t in ("I", "IA", "IB", "II", "III"):
        f = np.asarray(jerlov.solar_fraction(t, depths), dtype=float)
        keep = f >= 1e-3
        svg.path(list(zip(x(depths[keep]), y(f[keep]))), TYPE_COLOURS[t], 1.6)
    return svg.done()


def card_chlorophyll() -> str:
    W, H = CARD
    svg = Svg(W, H, "Kd of case 1 water from its chlorophyll, Morel & "
              "Maritorena 2001")
    wl = np.arange(350.0, 701.0, 5.0)
    x = lin(350, 700, CM["l"], W - CM["r"])
    y = logs(0.01, 2.0, H - CM["b"], CM["t"])
    axes(svg, x, y, CM, (400, 500, 600, 700), (0.01, 0.1, 1.0),
         lambda v: f"{v}", lambda v: f"{v:g}", "wavelength, nm",
         "Kd from chlorophyll, 1/m")
    chls = (0.03, 0.1, 0.3, 1.0, 3.0, 10.0)
    greens = ("#0b4f8a", "#2f6fb0", "#3a8a8a", "#3a8a3a", "#6b8a1e", "#7a5a1e")
    for k, chl in enumerate(chls):
        kd = np.asarray(jerlov.morel2001_kd(wl, chlorophyll_mg_m3=chl), float)
        svg.path(list(zip(x(wl), y(kd))), greens[k], 1.5)
        svg.text(W - CM["r"] - 2, H - CM["b"] - 60 + 11 * k,
                 f"{chl:g} mg/m3", anchor="end", fill=greens[k])
    return svg.done()


def card_scattering() -> str:
    W, H = CARD
    svg = Svg(W, H, "Phase functions of Petzold's eight stations")
    x = logs(0.1, 180, CM["l"], W - CM["r"])
    y = logs(1e-3, 1e4, H - CM["b"], CM["t"])
    axes(svg, x, y, CM, (0.1, 1, 10, 180), (1e-3, 1e-1, 1e1, 1e3),
         lambda v: f"{v:g}°", lambda v: f"{v:g}", "scattering angle",
         "phase function, 1/sr (Petzold 1972)")
    colour = {"AUTEC": "#2f6fb0", "HAOCE": "#3a8a3a", "NUC": "#a5682a"}
    for station in jerlov.PETZOLD_STATIONS:
        f = jerlov.petzold_scattering(station)
        a = np.asarray(f.angles_deg, dtype=float)
        p = np.asarray(f.vsf, dtype=float) / f.b
        keep = a >= 0.1
        svg.path(list(zip(x(a[keep]), y(p[keep]))),
                 colour[station.split()[0]], 1.2)
    for k, (name, c) in enumerate(colour.items()):
        svg.rect(W - CM["r"] - 70, CM["t"] + 6 + 13 * k, 10, 3, c, rx=1)
        svg.text(W - CM["r"] - 56, CM["t"] + 10 + 13 * k, name, fill=INK)
    return svg.done()


def figures() -> dict[str, str]:
    """Every figure, by file name."""
    with warnings.catch_warnings():
        # Petzold's extension below 0.1 degree and Jerlov's extrapolated
        # values warn; the figures draw within what the sources give.
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        # As on dive.html: 380-700 nm leaves 0.2 percent of the observer
        # out, and the colours are clipped to sRGB, as the figure says.
        warnings.simplefilter("ignore", jerlov.CoverageWarning)
        warnings.simplefilter("ignore", jerlov.GamutWarning)
        es = surface()
        return {
            "kd_types.svg": kd_types(es),
            "card_par.svg": card_par(es),
            "card_sources.svg": card_sources(),
            "card_colours.svg": card_colours(es),
            "card_heating.svg": card_heating(),
            "card_chlorophyll.svg": card_chlorophyll(),
            "card_scattering.svg": card_scattering(),
        }

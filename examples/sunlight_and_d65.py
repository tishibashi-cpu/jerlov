"""The light of a clear sky at the sea surface, set beside D65.

For anyone who has used CIE illuminant D65 as the light above the sea, as
twelve of these examples do, and wants to know how much that choice
matters:

    python examples/sunlight_and_d65.py

It computes the direct and diffuse irradiance at the sea surface by the
model of Gregg & Carder (1990) for one stated sky and four suns, and sets
it beside D65: the shape of the spectrum and its colour; the level, which
D65 does not have; the depth at which 1 percent of PAR is left; the colour
of a white card at depth as a camera balanced for D65 records it; and, by
Gordon (1989), how much the sun's height changes Kd (DECISIONS.md section
77).
"""

import warnings

import numpy as np

import jerlov

#: numpy.trapezoid from NumPy 2.0, numpy.trapz before.
trapezoid = getattr(np, "trapezoid", None) or np.trapz


def rule(title):
    print(f"\n{title}\n" + "-" * len(title))


def _banner():
    """Say which copy of the package is being used.

    Running ``python examples/foo.py`` puts ``examples/`` on sys.path, not the
    current directory, so an installed copy wins over the working tree. That
    is easy to miss and gives confusing failures; ``pip install -e .`` in the
    repository is the usual fix.
    """
    print(f"jerlov {jerlov.__version__} from {jerlov.__file__}")


WL = np.arange(350.0, 701.0)
PAR = (WL >= 400) & (WL <= 700)
#: The sky: Gregg & Carder's Table 5 standard conditions (p. 1670), a
#: visibility of 10 km, and 21 June. Every one is an assumption about a
#: place and a day, stated here because the model has no defaults.
ATMOSPHERE = dict(day_of_year=172, pressure_hpa=1013.25, air_mass_type=1,
                  relative_humidity=80.0, precipitable_water_cm=1.5,
                  wind_speed_24h=3.0, wind_speed=5.0, ozone_du=300.0)
VISIBILITY_KM = 10.0
#: The ends of Table 5's range of visibility.
VISIBILITIES_KM = (5.0, 10.0, 25.0)
SUNS = (0.0, 30.0, 60.0, 80.0)
TYPES = ("IB", "II", "III", "1C", "5C", "9C")
CARD_TYPE, CARD_DEPTHS = "III", (5.0, 10.0, 20.0)
#: The sun Jerlov's Kd is assumed, for part 5 only, to have been measured
#: under. His tables do not say.
ASSUMED_SUN = 30.0


def sky(sun, visibility=VISIBILITY_KM):
    return jerlov.gregg1990_irradiance(WL, sun_zenith_deg=sun,
                                       visibility_km=visibility,
                                       **ATMOSPHERE)


def d65():
    return np.interp(WL, *jerlov.d65())


def same_energy(spectrum):
    """Scaled to 1 W m-2 over 400-700 nm, so that only the shape is left."""
    return spectrum / trapezoid(spectrum[PAR], WL[PAR])


def chromaticity(spectrum, caught):
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always", jerlov.CoverageWarning)
        xyz = jerlov.spectrum_to_xyz(spectrum, WL)
    caught.update(str(w.message) for w in seen)
    return xyz[:2] / xyz.sum()


def chromaticity_y(spectrum, caught):
    """Y, the luminance, over 350-700 nm."""
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always", jerlov.CoverageWarning)
        y = jerlov.spectrum_to_xyz(spectrum, WL)[1]
    caught.update(str(w.message) for w in seen)
    return y


def shape_part(caught):
    rule("1. The shape and the colour")
    full = jerlov.spectrum_to_xyz(*reversed(jerlov.d65()))
    full_xy = full[:2] / full.sum()
    d65_xy = chromaticity(d65(), caught)
    d = same_energy(d65())
    i450, i650 = np.searchsorted(WL, (450.0, 650.0))
    tilt = {"D65": d[i450] / d[i650]}
    xy = {"D65": d65_xy}
    print(f"""The model stops at 700 nm and the colour matching functions go on
to 830, so every colour below is computed over 350-700 nm, D65's
included. That moves D65's own chromaticity from x = {full_xy[0]:.4f} to
{d65_xy[0]:.4f}, y = {full_xy[1]:.4f} to {d65_xy[1]:.4f}; the package's
CoverageWarning says how much of each function is left out.

Above the sea, scaled to the same energy over 400-700 nm:

  {'light':<26}{'450 / 650 nm':>13}{'x':>9}{'y':>9}""")
    print(f"  {'D65':<26}{tilt['D65']:>13.2f}{d65_xy[0]:>9.4f}"
          f"{d65_xy[1]:>9.4f}")
    for sun in SUNS:
        for visibility in VISIBILITIES_KM:
            if visibility != VISIBILITY_KM and sun not in (30.0,):
                continue
            s = sky(sun, visibility).above
            key = (sun, visibility)
            tilt[key] = s[i450] / s[i650]
            xy[key] = chromaticity(s, caught)
            label = f"sun {sun:g} deg, {visibility:g} km"
            print(f"  {label:<26}{tilt[key]:>13.2f}{xy[key][0]:>9.4f}"
                  f"{xy[key][1]:>9.4f}")
    print(f"""
Every one of the model's skies is redder than D65: less blue for its
red, {min(v for k, v in tilt.items() if k != 'D65'):.2f} to {max(v for k, v in tilt.items() if k != 'D65'):.2f} against {tilt['D65']:.2f}, and its chromaticity lies towards
yellow. Hazier air (5 km) makes it redder still. Lower than 60 degrees
it turns bluer again ({tilt[(80.0, VISIBILITY_KM)]:.2f} at 80), as the direct beam fades through a
longer path and the blue sky's own light takes over.""")
    return dict(tilt=tilt, xy=xy, full_xy=full_xy, d65_xy=d65_xy)


def level_part():
    rule("2. How much light")
    print("PAR above the sea, W m-2, 400-700 nm:\n")
    print(f"  {'sun':>5}" + "".join(f"{v:>9g} km" for v in VISIBILITIES_KM))
    level = {}
    for sun in SUNS:
        row = []
        for visibility in VISIBILITIES_KM:
            s = sky(sun, visibility).above
            level[(sun, visibility)] = trapezoid(s[PAR], WL[PAR])
            row.append(level[(sun, visibility)])
        print(f"  {sun:>5g}" + "".join(f"{x:>12.0f}" for x in row))
    print("""
D65 is a relative spectrum and says none of this. Anything absolute, a
dose of PAR or the photons a cone catches at noon, needs a sky.""")
    return level


def depth_part():
    rule("3. Where 1 percent of PAR is left")
    print("Below the surface, with Jerlov's (1976) Kd. The depth is a ratio,\n"
          "so only the shape of the light matters:\n")
    print(f"  {'type':>5}{'D65':>8}" + "".join(f"{'sun ' + format(s, 'g'):>9}"
                                             for s in SUNS))
    depth = {}
    for t in TYPES:
        kd = jerlov.water(t, source="jerlov1976")
        depth[(t, "D65")] = jerlov.par_profile(
            d65(), WL, [0.0], kd=kd, unit="energy").depth_of_fraction(0.01)
        for sun in SUNS:
            depth[(t, sun)] = jerlov.par_profile(
                sky(sun).below, WL, [0.0], kd=kd,
                unit="energy").depth_of_fraction(0.01)
        print(f"  {t:>5}{depth[(t, 'D65')]:>8.1f}"
              + "".join(f"{depth[(t, s)]:>9.1f}" for s in SUNS))
    gap = {t: max(abs(depth[(t, s)] - depth[(t, "D65")]) for s in SUNS)
           for t in TYPES}
    spread = {t: max(depth[(t, s)] for s in SUNS)
              - min(depth[(t, s)] for s in SUNS) for t in TYPES}
    print(f"""
The model's skies put it up to {gap['IB']:.1f} m shallower in IB and within
{max(gap[t] for t in ('1C', '5C', '9C')):.1f} m in the coastal types. In IB to III the sun's height moves
it by at most {max(spread[t] for t in ('IB', 'II', 'III')):.1f} m, less than the change from D65 does.""")
    return depth, gap


def card_part(caught):
    rule(f"4. A white card in Jerlov {CARD_TYPE}")
    kd = jerlov.water(CARD_TYPE, source="jerlov1976").kd(WL)
    reference = d65()
    luminance = chromaticity_y(reference, caught)
    print("As a camera white-balanced to D65 in air records it, lit from above\n"
          "by each light (sRGB, 1 is the card in air under D65):\n")
    print(f"  {'light':<12}" + "".join(f"{format(d, 'g') + ' m':>21}"
                                       for d in CARD_DEPTHS))
    rgb = {}
    lights = {"D65": reference}
    lights.update({f"sun {s:g}": sky(s).below for s in SUNS})
    for name, light in lights.items():
        # The camera's white is D65 at the brightness of this light at the
        # surface: what matters is its colour, not how much light there is.
        white = reference * (chromaticity_y(light, caught) / luminance)
        cells = []
        for depth in CARD_DEPTHS:
            with warnings.catch_warnings(record=True) as seen:
                warnings.simplefilter("always", jerlov.CoverageWarning)
                warnings.simplefilter("always", jerlov.GamutWarning)
                value = jerlov.spectrum_to_srgb(
                    light * np.exp(-kd * depth), WL, white=white)
            caught.update(str(w.message) for w in seen)
            rgb[(name, depth)] = value
            cells.append(" ".join(f"{v:.2f}" for v in value))
        print(f"  {name:<12}" + "".join(f"{c:>21}" for c in cells))
    blue = max(abs(rgb[(n, d)][2] / rgb[("D65", d)][2] - 1)
               for n in lights if n != "D65" for d in CARD_DEPTHS)
    green = max(abs(rgb[(n, d)][1] / rgb[("D65", d)][1] - 1)
                for n in lights if n != "D65" for d in CARD_DEPTHS)
    print(f"""
The water decides the colour: by 10 m the card lies outside sRGB under
any light, and its red is clipped to 0. The
sky changes the blue channel by up to {100 * blue:.0f} percent and the green by up
to {100 * green:.0f}. A rendering that stands D65 in for the sky is close; one that
needs the blue right to a few percent needs the sky.""")
    return rgb, blue, green


def d0_part():
    rule("5. The sun's height and Kd (Gordon 1989)")
    kd490 = float(jerlov.water("II", source="jerlov1976").kd(490.0))
    print(f"""Gordon found Kd / D0 nearly independent of the light field, D0 being
the reciprocal of the mean cosine just below the surface. His eq. (12)
needs f, the share of direct sunlight there; the model gives it.
Jerlov's tables do not record the sun they were measured under. Taking
it, for illustration only, as {ASSUMED_SUN:g} degrees, Jerlov II's Kd(490) =
{kd490:.4f} 1/m becomes:
""")
    print(f"  {'sun':>5}{'f':>8}{'D0':>8}{'Kd(490)':>10}{'change':>9}")
    rows = {}
    reference = None
    for sun in sorted(set(SUNS) | {ASSUMED_SUN}):
        s = jerlov.gregg1990_irradiance(490, sun_zenith_deg=sun,
                                        visibility_km=VISIBILITY_KM,
                                        **ATMOSPHERE)
        f = float(s.direct_below / s.below)
        with warnings.catch_warnings():
            # Above 60 degrees eq. (12) is 5-8 percent low at 80 (p. 1402);
            # the warning is the point of printing that row.
            warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
            d0 = jerlov.gordon1989_d0(sun, direct_fraction=f)
        rows[sun] = (f, d0)
    reference = rows[ASSUMED_SUN][1]
    for sun, (f, d0) in rows.items():
        kd = jerlov.gordon1989_kd(kd490, d0_from=reference, d0_to=d0)
        rows[sun] = (f, d0, kd)
        print(f"  {sun:>5g}{f:>8.2f}{d0:>8.3f}{kd:>10.4f}"
              f"{100 * (kd / kd490 - 1):>+8.0f}%")
    low = min(r[2] for r in rows.values())
    high = max(r[2] for r in rows.values())
    print(f"""
At 80 degrees most of the light is the sky's, so D0 falls back towards
the diffuse 1.197. Gordon's eq. (12) is 5-8 percent low there (p. 1402);
that row is the formula's, not a measurement's. Under this one sky, Kd
spans {100 * (high / low - 1):.0f} percent between the sun overhead and 60 degrees from it.""")
    return rows


def main():
    _banner()
    caught = set()
    shape = shape_part(caught)
    level = level_part()
    depth, gap = depth_part()
    rgb, blue, green = card_part(caught)
    d0 = d0_part()
    if caught:
        rule("Warnings")
        print("Raised along the way:")
        for message in sorted(caught):
            print(f"  - {message}")

    rule("Before you use any of this")
    print("""  - One modelled sky: cloudless, maritime, with the inputs stated at
    the top. Real skies have clouds, other aerosols, and a sun that moves.
  - Gregg & Carder checked their model against 115 measured spectra and
    found 6.56 percent rms error (p. 1668); it stops at 350 and 700 nm.
  - Nothing here says D65 is wrong for the examples that use it. It says
    how large the difference is, in their units.
""")
    return dict(shape=shape, level=level, depth=depth, gap=gap, rgb=rgb,
                blue=blue, green=green, d0=d0, caught=caught)


if __name__ == "__main__":
    main()

"""How deep seagrass can grow, and how far a change in the water moves it.

For coastal ecology and habitat restoration. Seagrasses are found down to
the depth at which enough of the surface light still reaches the bottom,
and how much is enough is not one number:

- Duarte (1991), a regression over 72 depth limits worldwide: on average
  10.8 percent of the surface irradiance (geometric mean, coefficient of
  variation 16 percent; p. 365), "about 11%" in the abstract.
- Dennison et al. (1993): 4 to 29 percent of the light just below the
  surface, for submersed aquatic vegetation across species (p. 87 and
  Table 1).
- Kenworthy & Haunert (1991), a workshop's conclusion: at least 15 to 25
  percent just for maintenance (p. 4).
- Duarte et al. (2007), 424 later reports: in turbid water, with an
  attenuation coefficient above 0.27 1/m, the apparent requirement is
  higher; their equations give 45.0 percent for plants whose limit is at
  1 m and 33.3 percent at 5 m, against 12.2 percent at 30 m (pp. 654-655).

The threshold is a property of the species and the site, not of the
water, so it is an argument here: 25, 11 and 5 percent are tried, and the
turbid-water figure in part 2.

    python examples/seagrass_depth_limit.py

These are quoted, not checked by this package. Two cautions from the
papers themselves: most of their attenuation coefficients were estimated
from Secchi depths, by K = 1.7 / Secchi depth in Duarte (1991, p. 364) and
for all but 27 of 424 reports in Duarte et al. (2007, p. 652); and neither
says over which waveband K was measured where it was.

    Duarte, C. M. (1991), Aquatic Botany 40, 363-377.
        doi:10.1016/0304-3770(91)90081-F
    Dennison, W. C. et al. (1993), BioScience 43, 86-94.
        doi:10.2307/1311969
    Kenworthy, W. J. & Haunert, D. E., eds. (1991), The light requirements
        of seagrasses, NOAA Technical Memorandum NMFS-SEFC-287.
    Duarte, C. M. et al. (2007), Estuaries and Coasts 30, 652-656.
        doi:10.1007/BF02841962
"""

import math

import numpy as np

import jerlov


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


_banner()

BAND = np.arange(400.0, 701.0, 5.0)
SURFACE = np.interp(BAND, *jerlov.d65())     # stands in for the real sky
THRESHOLDS = (0.25, 0.11, 0.05)              # fraction of surface PAR
TYPES = ("II", "III", "1C", "3C", "5C", "7C", "9C")


def profile(water_type):
    """PAR below ``water_type``, layer by layer where the profile allows.

    Williamson & Hollins (2023) declare a type only where ten or more
    campaigns support one, so a coastal descent stops early: 9C at 10 m,
    5C and 7C at 20 m. Below that this falls back to the surface type's Kd
    all the way down, and says so.
    """
    for depth in np.arange(200.0, 0.0, -10.0):
        try:
            d = jerlov.descend(water_type, depth, BAND)
        except jerlov.MissingQuantityError:
            continue
        return jerlov.par_profile(SURFACE, BAND, 0.0, kd=d, unit="energy"), d
    return None, None


def depth_limit(water_type, threshold):
    """(depth, how): layered if the descent reaches it, else one Kd."""
    layered, d = profile(water_type)
    try:
        return layered.depth_of_fraction(threshold), "layers"
    except jerlov.MissingQuantityError:
        one = jerlov.par_profile(SURFACE, BAND, 0.0, unit="energy",
                                 kd=jerlov.water(water_type,
                                                 source="jerlov1976"))
        return one.depth_of_fraction(threshold), f"one Kd below {d.depth_m:g} m"


# --------------------------------------------------------------------------
rule("1. The depth limit for three light requirements")

print("""The depth at which the bottom receives 25, 11 and 5 percent of the
surface PAR, by water type. Jerlov (1976) Kd, each 10 m layer with its own
type as far as the profile goes.""")

print(f"\n  {'type':>5}" + "".join(f"{f:>9.0%}" for f in THRESHOLDS))
limits = {}
notes = set()
for t in TYPES:
    cells = []
    for f in THRESHOLDS:
        z, how = depth_limit(t, f)
        limits[t, f] = z
        cells.append(f"{z:>7.1f} m" + ("*" if how != "layers" else " "))
        if how != "layers":
            notes.add(f"{t}: {how}")
    print(f"  {t:>5}" + "".join(f"{c:>9}" for c in cells))
for note in sorted(notes):
    print(f"   * {note}")

print(f"""
  The requirement matters as much as the water. In 3C, going from 25 to 5
  percent moves the limit from {limits["3C", 0.25]:.1f} m to {limits["3C", 0.05]:.1f} m; a plant needing 5 percent
  in 3C goes as deep as one needing 11 percent in 1C ({limits["1C", 0.11]:.1f} m). A depth
  limit quoted without the requirement it assumed is not a prediction.""")

# --------------------------------------------------------------------------
rule("2. Turbid water needs more light")

print("""Duarte et al. (2007) found that above an attenuation coefficient of
0.27 1/m seagrasses stop where more light is left: 33.3 percent for plants
limited at 5 m. Which types are above 0.27, as Kd(PAR) averaged down to
the 11 percent depth, and where 33.3 percent puts their limit:""")

print(f"\n  {'type':>5} {'Kd(PAR)':>8} {'at 11%':>8} {'at 33.3%':>9}")
turbid = {}
for t in TYPES:
    k_column = math.log(1 / 0.11) / limits[t, 0.11]
    if k_column > 0.27:
        turbid[t] = depth_limit(t, 0.333)[0]
        print(f"  {t:>5} {k_column:>8.3f} {limits[t, 0.11]:>6.1f} m "
              f"{turbid[t]:>7.1f} m")
    else:
        print(f"  {t:>5} {k_column:>8.3f} {limits[t, 0.11]:>6.1f} m "
              f"{'clear':>9}")

print(f"""
  In the turbid types the 11 percent of Duarte (1991) puts the limit about
  {min(limits[t, 0.11] / turbid[t] for t in turbid):.1f} to {max(limits[t, 0.11] / turbid[t] for t in turbid):.1f} times deeper than the 33.3 percent of Duarte et al. (2007).
  And 33.3 percent is their figure for a limit at 5 m; every limit here is
  shallower, where their equations ask for more still, up to 45.0 percent
  at 1 m, so even these are if anything too deep. Their attenuation
  coefficients are not Jerlov's, so which side of 0.27 a type falls is
  approximate; near it, try both.""")

# --------------------------------------------------------------------------
rule("3. One step more turbid")

print("""A restoration target is often a change in the water: less run-off,
less resuspension. Moving one type along the coastal scale, at the 11
percent requirement:""")

print(f"\n  {'from':>5} {'to':>5} {'limit before':>13} {'after':>8} {'change':>8}")
coastal = ("1C", "3C", "5C", "7C", "9C")
for here, there in zip(coastal, coastal[1:]):
    before, after = limits[here, 0.11], limits[there, 0.11]
    print(f"  {here:>5} {there:>5} {before:>11.1f} m {after:>6.1f} m "
          f"{after - before:>+6.1f} m")

print("""
  On a gently sloping bottom the area lost is the change in depth divided
  by the slope, so a metre of depth limit can be a long strip of meadow.""")

# --------------------------------------------------------------------------
rule("4. One attenuation coefficient for PAR is not one number")

print("""The depth limit is often estimated from a single Kd(PAR), measured
near the surface, as ln(1 / threshold) / Kd(PAR). But the red is gone in
the first metre or two, so PAR attenuates fastest near the surface and
more slowly below. The effective Kd(PAR) over the top 1 m, and over the
whole column down to the 11 percent depth:""")

print(f"\n  {'type':>5} {'top 1 m':>9} {'to limit':>9} {'estimate':>9} {'actual':>8}")
for t in ("III", "1C", "3C", "5C"):
    layered, _ = profile(t)
    z_limit = limits[t, 0.11]
    k_top = -math.log(jerlov.par_profile(SURFACE, BAND, 1.0, unit="energy",
                                         kd=jerlov.water(t, source="jerlov1976"))
                      .fraction)
    k_column = math.log(1 / 0.11) / z_limit
    estimate = math.log(1 / 0.11) / k_top
    print(f"  {t:>5} {k_top:>9.3f} {k_column:>9.3f} {estimate:>7.1f} m "
          f"{z_limit:>6.1f} m")

print("""
  Kd(PAR) from the top metre makes the water look murkier than it is
  further down, and puts the depth limit too shallow. Measure Kd(PAR) over
  the depth range you care about, or attenuate the spectrum, as here.""")

# --------------------------------------------------------------------------
rule("Before you use any of this")

print("""  - The light requirements are quoted from the literature, not
    derived, and the papers' own attenuation coefficients are mostly
    estimated from Secchi depths. Use the requirement measured for your
    species and site.
  - This is planar PAR, from Ed: the light on a flat surface facing up,
    which is what a flat quantum sensor on the bottom reads, and roughly
    what a meadow's canopy receives.
  - Epiphytes and the plants' own canopy shade the leaves further, and are
    not included.
  - D65 stands in for the surface spectrum. The tide, the season and the
    sun's elevation all change both the spectrum and the depth.
  - The Jerlov type is what was typical for that clarity, and coastal water
    changes by the week. Kd measured at the site replaces all of it:
    `par_profile` takes an array.
""")

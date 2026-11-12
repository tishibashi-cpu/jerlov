"""Looking up, across and down, in a lake whose light was measured.

For divers, ROV pilots and anyone who sees under water along a slanted
line:

    python examples/looking_up_and_down.py

A black target is seen from 41.3 m in Lake Pend Oreille, straight up, at
40 degrees, horizontally, and down, through `Scene.observe_slant` (Duntley
1963). The radiance of the water along each line and how fast it changes
with depth come from Tyler's (1958) measured radiance distribution in that
lake, not from a guess (DECISIONS.md section 78).
"""

import math
import warnings

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


OBSERVER_M = 41.3
#: Tyler's band runs from 430 to 546 nm (p. 5); 488 nm is its middle. One
#: wavelength stands for the band, which is broad.
WAVELENGTH_NM = 488.0
#: Tilts from straight up, at an azimuth of 80 degrees from the sun's, so
#: that no cell near the sun's direction is used (DATA.md section 23).
DIRECTIONS = {"up": 0.0, "40 deg up": 40.0, "horizontal": 90.0,
              "40 deg down": 140.0, "down": 180.0}
AZIMUTH_DEG = 80.0
#: The yardstick: the distance at which the contrast falls to 2 percent of
#: its start. Not a claim about what an eye or a camera can see.
YARDSTICK = 0.02


def load(caught):
    """Tyler's seven tables. Those at 4.24-29.0 m warn of suspect cells
    in the sun's direction; none of those cells is used here."""
    tables = {}
    for depth in jerlov.TYLER1958_DEPTHS:
        with warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter("always", jerlov.ProvenanceWarning)
            tables[depth] = jerlov.tyler1958_radiance(depth)
        caught.update(str(w.message) for w in seen)
    return tables


def radiance(tables, depth, tilt):
    t = tables[depth]
    i = list(t.tilt_deg).index(tilt)
    j = list(t.azimuth_deg).index(AZIMUTH_DEG)
    return float(t.radiance[i, j])


def k_part(tables):
    rule("1. How fast the water's radiance falls with depth")
    depths = jerlov.TYLER1958_DEPTHS
    print("K = -d ln N / dz between Tyler's depths, 1/m, by the direction\n"
          "looked in:\n")
    print(f"  {'depths, m':<14}" + "".join(f"{name:>13}"
                                          for name in DIRECTIONS))
    table = {}
    for upper, lower in zip(depths, depths[1:]):
        row = []
        for name, tilt in DIRECTIONS.items():
            k = (math.log(radiance(tables, upper, tilt)
                          / radiance(tables, lower, tilt)) / (lower - upper))
            table[(upper, name)] = k
            row.append(k)
        print(f"  {f'{upper:g}-{lower:g}':<14}" + "".join(f"{k:>13.3f}"
                                                        for k in row))
    def spread(upper):
        ks = [table[(upper, n)] for n in DIRECTIONS]
        return max(ks) / min(ks) - 1
    print(f"""
Near the surface the light from above fades more slowly than the light
from below, by a factor of {1 + spread(depths[0]):.1f}. From 16.6 to 53.7 m every direction
agrees within {100 * max(spread(d) for d in depths[2:5]):.0f} percent: Duntley's asymptotic light field (p. 231), in
which K is the same in every direction. In the deepest interval the
directions part again, by {100 * spread(depths[-2]):.0f} percent.""")
    return table


def scene(c):
    # Scene needs a and b; only c = a + b enters a black target's contrast
    # and the path. Tyler gives c and no split, so all of it goes in a.
    water = jerlov.Water.from_measurements([WAVELENGTH_NM], a=[c], b=[0.0],
                                           name="Lake Pend Oreille")
    return jerlov.Scene(water, [1.0], [WAVELENGTH_NM], depth_m=OBSERVER_M)


def contrast_part(tables, c):
    rule(f"2. A black target, seen from {OBSERVER_M:g} m")
    view = scene(c)
    print(f"""c = {c:.3f} 1/m (Tyler, p. 8). The contrast left of a black target
against the water behind it, which starts at -1:
""")
    print(f"  {'direction':<14}{'target, m':>10}{'distance, m':>13}"
          f"{'K, 1/m':>9}{'contrast':>11}{'horizontal':>12}")
    seen = {}
    others = [d for d in jerlov.TYLER1958_DEPTHS if d != OBSERVER_M]
    for name, tilt in DIRECTIONS.items():
        if tilt == 90.0:
            targets = [(OBSERVER_M, r) for r in (12.3, 24.7)]
        else:
            cos = math.cos(math.radians(tilt))
            near = sorted(others, key=lambda d: abs(d - OBSERVER_M))
            targets = [(d, (d - OBSERVER_M) / -cos) for d in near
                       if (d < OBSERVER_M) == (cos > 0)][:2]
        for target, distance in targets:
            nw = radiance(tables, OBSERVER_M, tilt)
            nw_target = radiance(tables, target, tilt)
            k = (0.0 if target == OBSERVER_M else
                 math.log(nw / nw_target) / (target - OBSERVER_M))
            obs = view.observe_slant(
                [0.0], distance, target_depth_m=target,
                kd=[0.0],    # cannot matter: a black target reflects nothing
                water_radiance=[nw], radiance_attenuation=[k],
                face_irradiance_ratio=1.0)
            contrast = float(obs.contrast([nw_target])[0])
            flat = -math.exp(-c * distance)
            seen[(name, target)] = dict(distance=distance, k=k,
                                        contrast=contrast, flat=flat,
                                        observation=obs, nw=nw,
                                        nw_target=nw_target)
            print(f"  {name:<14}{target:>10g}{distance:>13.1f}{k:>9.3f}"
                  f"{contrast:>11.4f}{flat:>12.4f}")
    up = seen[("up", 29.0)]["contrast"] / seen[("up", 29.0)]["flat"]
    down = seen[("down", 53.7)]["flat"] / seen[("down", 53.7)]["contrast"]
    print(f"""
Over about 12 m, looking up leaves {up:.1f} times the contrast a horizontal
line does; looking down leaves 1/{down:.1f} of it. The target and the water
are the same in every row; only the light behind the target changes.""")
    return seen


def yardstick_part(tables, c):
    rule("3. How far before the contrast is down to 2 percent")
    print("Duntley's eq. (16), with K at the observer held constant along the\n"
          "line:\n")
    ranges = {}
    for name, tilt in DIRECTIONS.items():
        cos = math.cos(math.radians(tilt))
        if tilt == 90.0:
            k = 0.0
        else:
            other = (29.0 if cos > 0 else 53.7)
            k = (math.log(radiance(tables, OBSERVER_M, tilt)
                          / radiance(tables, other, tilt))
                 / (other - OBSERVER_M))
        # Rising a distance r along the line changes the depth by -r cos.
        ranges[name] = -math.log(YARDSTICK) / (c - k * cos)
        print(f"  {name:<14}{ranges[name]:>7.1f} m")
    print(f"""
Horizontally it is 3.91 / c = {ranges['horizontal']:.1f} m whatever the light. Up it is
{ranges['up'] / ranges['horizontal']:.1f} times that, down {ranges['down'] / ranges['horizontal']:.2f}.""")
    return ranges


def misprint_part(seen, c):
    rule("4. Duntley's eq. (12) as printed")
    row = seen[("up", 29.0)]
    r, nw, nw_target = row["distance"], row["nw"], row["nw_target"]
    # Duntley's K r cos(theta) is ln(N(zt) / N(z)) for the water itself.
    g = math.log(nw_target / nw)
    printed = (nw_target * math.exp(-c * r)
               + nw_target * math.exp(g) * (1 - math.exp(-c * r + g)))
    corrected = (nw_target * math.exp(-c * r)
                 + nw_target * math.exp(-g) * (1 - math.exp(-c * r + g)))
    print(f"""The open water looked at straight up over {r:.1f} m. Tyler measured
{nw:.0f} at the observer. With the sign Duntley printed in front of the
path radiance it would read {printed:.0f}, {printed / nw:.0f} times the
measurement; with the sign corrected it reads {corrected:.0f}, the
measurement, which is what the package uses (DATA.md section 34).""")
    return printed / nw, corrected / nw


def main():
    _banner()
    caught = set()
    tables = load(caught)
    c = tables[OBSERVER_M].beam_attenuation
    k = k_part(tables)
    seen = contrast_part(tables, c)
    ranges = yardstick_part(tables, c)
    printed, corrected = misprint_part(seen, c)
    if caught:
        rule("Warnings")
        print("Raised along the way, each a ProvenanceWarning about cells "
              "not used here:")
        for message in sorted(caught):
            print(f"  - {message}")

    rule("Before you use any of this")
    print("""  - One lake, one clear day, one band: Tyler's measurement, adjusted
    to a sun 56.6 degrees above the horizon. c is the transmissometer's at
    the surface, in a band the report does not give.
  - The target is black and seen against the open water behind it. A
    lit target, or one against the bottom, needs its own radiance.
  - The 2 percent yardstick holds K constant along the line, as Duntley's
    eq. (16) does; part 2 uses the measured K over each path.
  - No blur: the contrast of a point, not the sharpness of an image.
""")
    return dict(k=k, seen=seen, ranges=ranges, printed=printed,
                corrected=corrected, caught=caught)


if __name__ == "__main__":
    main()

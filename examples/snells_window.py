"""Snell's window: the sky seen from under water, squeezed into a cone.

For those who look up from under water: divers, underwater photographers,
and those who study what fish and other animals see from below. Looking
up through a flat surface, the whole sky is seen inside a cone of about
97 degrees; outside it the surface is a mirror of the water below. This
example works out the cone's size, where in it a thing at a given height
above the horizon appears, how bright it is across its radius, and how
large it is on the surface; then it looks for the cone's edge in a
measured radiance distribution, Tyler's (1958), at seven depths in a lake.

    python examples/snells_window.py

Parts 1 to 5 are geometry and Fresnel's equations at a flat surface,
written out here: the package solves no radiative transfer and has no
public Fresnel function (DECISIONS.md section 123). Part 6 uses
jerlov.tyler1958_radiance.
"""

import re
import warnings

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


#: Waters to show in part 1, by jerlov.quan1995_refractive_index (Quan &
#: Fry 1995): (label, wavelength nm, salinity, temperature C). The first
#: and last are the lowest and highest index within the equation's range.
WATERS = (("fresh, 30 C, 700 nm (lowest)", 700.0, 0.0, 30.0),
          ("fresh, 20 C, 550 nm", 550.0, 0.0, 20.0),
          ("sea, 35, 20 C, 550 nm", 550.0, 35.0, 20.0),
          ("sea, 35, 0 C, 400 nm (highest)", 400.0, 35.0, 0.0))
#: The index used from part 2 on: that of Lee et al.'s shallow-water runs,
#: which part 1 sets beside the sea water at 550 nm.
N_WATER = 1.34


def critical_deg(n):
    """The window's half-angle: the refraction of a ray at grazing incidence."""
    return np.degrees(np.arcsin(1.0 / n))


def fresnel(cos_i, n1, n2):
    """Fresnel reflectance for unpolarised light going from index n1 to n2,
    at incidence cos_i; 1 beyond the critical angle."""
    cos_i = np.asarray(cos_i, dtype=float)
    sin_t = n1 / n2 * np.sqrt(np.clip(1.0 - cos_i ** 2, 0.0, None))
    total = sin_t >= 1.0
    cos_t = np.sqrt(np.clip(1.0 - sin_t ** 2, 0.0, None))
    rs = ((n1 * cos_i - n2 * cos_t) / (n1 * cos_i + n2 * cos_t)) ** 2
    rp = ((n1 * cos_t - n2 * cos_i) / (n1 * cos_t + n2 * cos_i)) ** 2
    return np.where(total, 1.0, 0.5 * (rs + rp))


def _index(wavelength, salinity, temperature, caught):
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always", jerlov.ProvenanceWarning)
        n = jerlov.quan1995_refractive_index(
            wavelength, salinity_psu=salinity, temperature_c=temperature)
    caught.update(str(w.message) for w in record
                  if issubclass(w.category, jerlov.ProvenanceWarning))
    return n


def size_part(caught):
    rule("1. How wide the window is")
    print("""Light from the whole sky, down to the horizon, enters the water within a
cone of half-angle arcsin(1/n) about the vertical. The refractive index
n depends on the wavelength, the salinity and the temperature
(jerlov.quan1995_refractive_index, Quan & Fry 1995):
""")
    print(f"  {'water':<31} {'n':>7} {'half-angle':>11} {'full cone':>10}")
    rows = []
    for label, wl, sal, temp in WATERS:
        n = _index(wl, sal, temp, caught)
        c = float(critical_deg(n))
        rows.append(dict(label=label, n=n, angle=c))
        print(f"  {label:<31} {n:>7.4f} {c:>10.2f}° {2 * c:>9.1f}°")
    # The extremes over the equation's whole range, on a grid.
    grid = _index(np.linspace(400.0, 700.0, 61)[:, None, None],
                  np.linspace(0.0, 35.0, 8)[None, :, None],
                  np.linspace(0.0, 30.0, 7)[None, None, :], caught)
    low, high = float(grid.min()), float(grid.max())
    assert np.isclose(low, rows[0]["n"]) and np.isclose(high, rows[-1]["n"])
    sea = rows[2]["n"]
    print(f"""
Over 400 to 700 nm, 0 to 35 and 0 to 30 C the index runs from {low:.4f} to
{high:.4f}, and the edge moves by {rows[0]["angle"] - rows[-1]["angle"]:.2f} degrees. The rest of this example
uses n = {N_WATER:g}, the index of Lee et al.'s shallow-water runs; sea water at
550 nm and 20 C has {sea:.4f}, whose edge lies {float(critical_deg(N_WATER)) - float(critical_deg(sea)):.2f} degrees nearer the
vertical than n = {N_WATER:g} puts it.""")
    return dict(rows=rows, low=low, high=high, sea=sea,
                at_n=float(critical_deg(N_WATER)))


#: Heights above the horizon, degrees, to place in the window.
ELEVATIONS = (0, 5, 10, 20, 30, 45, 60, 90)


def squeeze_part():
    rule("2. The sky squeezed")
    c = float(critical_deg(N_WATER))
    seen = np.degrees(np.arcsin(np.cos(np.radians(ELEVATIONS)) / N_WATER))
    print(f"""A thing at elevation e above the horizon is seen at arcsin(cos e / n)
from the vertical, under water. The sky's 90 degrees from horizon to
zenith fill the {c:.1f} degrees from the window's edge to its centre:
""")
    print(f"  {'elevation':>10} {'seen from vertical':>19} {'from the edge':>14}")
    for e, s in zip(ELEVATIONS, seen):
        print(f"  {e:>9}° {s:>18.1f}° {c - s:>13.1f}°")
    sky = 2 * np.pi
    cone = 2 * np.pi * (1 - np.cos(np.radians(c)))
    low = int(np.argmax(np.asarray(ELEVATIONS) >= 20))
    print(f"""
The lowest {ELEVATIONS[low]} degrees of sky, everything from the horizon up to
{ELEVATIONS[low]} degrees, crowd into the outer {c - seen[low]:.1f} degrees of the window. In solid
angle the whole sky, {sky:.2f} sr, fills {cone:.2f} sr: {sky / cone:.1f} times less.""")
    return dict(seen=seen, solid_ratio=sky / cone, outer=c - seen[low],
                low=ELEVATIONS[low])


#: Angles from the vertical under water at which to show the window's
#: brightness, degrees.
WINDOW_ANGLES = (0, 20, 30, 40, 44, 46, 47, 48, 48.2)


def brightness_part():
    rule("3. How bright the window is, from centre to rim")
    c = float(critical_deg(N_WATER))
    theta_w = np.radians(WINDOW_ANGLES)
    sin_a = np.clip(N_WATER * np.sin(theta_w), 0, 1)
    cos_a = np.sqrt(1 - sin_a ** 2)
    t = 1 - fresnel(cos_a, 1.0, N_WATER)
    gain = N_WATER ** 2 * t
    print("""Under a sky of the same radiance in every direction, the radiance seen
looking up at an angle theta_w is n^2 (1 - rho) times the sky's: the
light is squeezed into a smaller solid angle (n^2), less what the surface
reflects (rho, Fresnel, for unpolarised light, at the angle in air):
""")
    print(f"  {'theta_w':>8} {'in air':>8} {'transmitted':>12} {'radiance x sky':>15}")
    for w, a, tt, g in zip(WINDOW_ANGLES, np.degrees(np.arcsin(sin_a)), t, gain):
        print(f"  {w:>7g}° {a:>7.1f}° {tt:>12.3f} {g:>15.2f}")
    fine = np.linspace(0.0, c, 100001)
    sin_f = np.clip(N_WATER * np.sin(np.radians(fine)), 0, 1)
    t_fine = 1 - fresnel(np.sqrt(1 - sin_f ** 2), 1.0, N_WATER)
    half = float(fine[np.flatnonzero(t_fine < 0.5)[0]])
    print(f"""
At the centre the window is {gain[0]:.2f} times as bright as the sky; the
transmitted share falls below a half {c - half:.1f} degrees inside the edge
({half:.1f} degrees from the vertical): even under an even sky the rim is
dark.""")
    return dict(centre=float(gain[0]), half=half, rim_width=c - half,
                normal=float(fresnel(1.0, 1.0, 1.333)))


#: Angles from the vertical for the reflectance seen from below, degrees.
BELOW_ANGLES = (0, 30, 40, 45, 47, 48, 48.5, 50, 60)


def mirror_part():
    rule("4. Outside the window: a mirror")
    c = float(critical_deg(N_WATER))
    r = fresnel(np.cos(np.radians(BELOW_ANGLES)), N_WATER, 1.0)
    print(f"""Looking up at more than {c:.1f} degrees from the vertical, no light from
the sky arrives: the surface reflects all the light that reaches it from
below. Its reflectance seen from below:
""")
    print(f"  {'theta_w':>8} {'reflectance':>12}")
    for a, rr in zip(BELOW_ANGLES, r):
        print(f"  {a:>7g}° {rr:>12.3f}")
    print("""
Outside the window the surface shows the water below it, and the bottom
where it is shallow enough, as a mirror would.""")
    return dict(reflectance=r)


#: Depths of an eye, m.
EYE_DEPTHS = (0.5, 1, 2, 5, 10)


def footprint_part():
    rule("5. The window on the surface")
    c = float(critical_deg(N_WATER))
    k = np.tan(np.radians(c))
    print(f"""The window is a circle on the surface of radius d tan({c:.1f}°) =
{k:.3f} d above an eye at depth d:
""")
    print(f"  {'depth':>6} {'radius':>8} {'diameter':>9}")
    for d in EYE_DEPTHS:
        print(f"  {d:>5g} m {k * d:>6.2f} m {2 * k * d:>7.2f} m")
    return dict(factor=k)


#: The azimuths of the test of part 6, degrees from the sun's: away from
#: the sun and its glitter (DECISIONS.md section 123).
AWAY = (90.0, 180.0)
#: The tilts the steps start at, looking up.
STEP_TILTS = np.arange(0.0, 81.0, 10.0)


def _suspect_cells(distribution):
    cells = set()
    for text in distribution.suspect:
        m = re.match(r"tilt (\d+), azimuth (\d+)", text)
        if m:
            cells.add((float(m.group(1)), float(m.group(2))))
    return cells


def measured_part(caught, size):
    rule("6. Is the edge in a measured radiance distribution?")
    edge = (float(critical_deg(size["high"])), float(critical_deg(size["low"])))
    rows = []
    for depth in jerlov.TYLER1958_DEPTHS:
        with warnings.catch_warnings(record=True) as record:
            warnings.simplefilter("always", jerlov.ProvenanceWarning)
            d = jerlov.tyler1958_radiance(depth)
        caught.update(str(w.message).split(":")[0] for w in record
                      if issubclass(w.category, jerlov.ProvenanceWarning))
        tilt = np.asarray(d.tilt_deg, dtype=float)
        bad = _suspect_cells(d)
        for j, az in enumerate(d.azimuth_deg):
            if not AWAY[0] <= az <= AWAY[1]:
                continue
            steps = {}
            for t in STEP_TILTS:
                i = int(np.flatnonzero(tilt == t)[0])
                if (t, az) in bad or (t + 10, az) in bad:
                    continue
                steps[t] = d.radiance[i, j] / d.radiance[i + 1, j]
            steepest = max(steps, key=steps.get)
            rows.append(dict(depth=depth, azimuth=float(az),
                             steepest=steepest, ratio=steps[steepest],
                             at_edge=steps[40.0],
                             seen=steepest == 40.0))
    print(f"""Tyler (1958) measured the radiance in every direction at seven depths in
Lake Pend Oreille under a clear sky, the sun {d.sun_altitude_deg:g} degrees above the horizon,
every 10 degrees of tilt with a {d.acceptance_deg:g} degree field of view. The window's edge,
{edge[0]:.1f} to {edge[1]:.1f} degrees from the vertical, lies in the step from 40 to 50
degrees. At each depth and each tabulated azimuth from {AWAY[0]:g} to {AWAY[1]:g} degrees
from the sun's (away from it and its glitter; Tyler tabulated every 20),
the step between neighbouring tilts, looking up, with the largest ratio
L(t)/L(t + 10), and the 40-50 step's ratio:
""")
    print(f"  {'depth':>6} {'azimuth':>8} {'steepest step':>14} {'ratio':>6} "
          f"{'40-50 step':>11}")
    for r in rows:
        mark = "  edge" if r["seen"] else ""
        step = f"{r['steepest']:g}-{r['steepest'] + 10:g} deg"
        print(f"  {r['depth']:>5g} m {r['azimuth']:>7g}° {step:>14} "
              f"{r['ratio']:>6.2f} {r['at_edge']:>11.2f}{mark}")
    counts = {}
    for r in rows:
        counts[r["depth"]] = counts.get(r["depth"], 0) + int(r["seen"])
    n_az = sum(1 for r in rows if r["depth"] == rows[0]["depth"])
    seen_at = [dep for dep, k in counts.items() if k]
    none = [dep for dep, k in counts.items() if not k]
    others = {}
    for r in rows:
        if not r["seen"]:
            others[r["steepest"]] = others.get(r["steepest"], 0) + 1
    where = "; ".join(f"{k} at {s:g}-{s + 10:g} degrees"
                      for s, k in sorted(others.items()))
    print(f"""
Of the {n_az} azimuths at each depth, the 40-50 step is the steepest at
{', '.join(f'{counts[dep]} at {dep:g} m' for dep in seen_at)}, and at none at {', '.join(f'{dep:g}' for dep in none)} m. Where it is the steepest, the
measured radiance falls across the window's edge faster than across any
other 10 degrees looking up. At the other {sum(others.values())} the steepest step lies elsewhere
({where}); there the edge does not stand out at this resolution.""")
    return dict(rows=rows, counts=counts, seen_at=seen_at, none=none,
                n_az=n_az, edge=edge, acceptance=d.acceptance_deg)


def main():
    _banner()
    caught = set()
    size = size_part(caught)
    squeeze = squeeze_part()
    bright = brightness_part()
    mirror = mirror_part()
    footprint = footprint_part()
    measured = measured_part(caught, size)
    if caught:
        print("\nThe package warned:\n  " + "\n  ".join(sorted(caught)) +
              "\n  Part 1 shows the index at 700 nm all the same, as the "
              "lowest the\n  equation gives; none of Tyler's suspect cells "
              "is used in part 6.")
    rule("Before you use any of this")
    print(f"""  - The surface is flat. Waves tilt it, and the window breaks into
    moving pieces whose edges come and go.
  - Part 3's sky has the same radiance in every direction, and its light
    is taken as unpolarised. A real sky is neither.
  - One refractive index, n = {N_WATER:g}, for every wavelength from part 2
    on. Part 1 shows how far the edge moves with the water.
  - Parts 1 to 5 have no scattering in the water. Part 6 is one lake, on
    one day, under one sun,
    with a {measured['acceptance']:g} degree field of view and 10 degree steps; it says
    where the edge stands out, not how sharp it is.
""")
    return dict(size=size, squeeze=squeeze, bright=bright, mirror=mirror,
                footprint=footprint, measured=measured, caught=caught)


if __name__ == "__main__":
    main()

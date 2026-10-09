"""Where a given light level lies, and how far it moves at dusk.

For the study of diel vertical migration and the depth distribution of
marine animals. Many zooplankton and fish are thought to track an
isolume, a depth of constant light, moving up as the light fades in the
evening and down at dawn. Where an isolume lies, and how fast it moves
for a given dimming at the surface, both follow from how the water
attenuates light, and both change with depth because the spectrum does.

    python examples/isolumes.py

PAR stands in for what an animal sees. An eye's or a photoreceptor's own
sensitivity can be used instead with `integrate_response`; see
`what_an_eye_sees.py`.
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
LEVELS = (1e-1, 1e-2, 1e-3, 1e-4, 1e-5)      # of the surface PAR
OCEANIC = ("I", "IA", "IB", "II", "III")


def deepest_descent(water_type):
    """The descent to the bottom of the typical profile for this type."""
    return jerlov.descend(water_type, jerlov.profile_depth(water_type), BAND)


def isolume(profile, level):
    """The depth of ``level``, or None if it is below the descent."""
    try:
        return profile.depth_of_fraction(level)
    except jerlov.MissingQuantityError:
        return None


# --------------------------------------------------------------------------
rule("1. Where each light level lies")

print("""The depth at which PAR is a tenth, a hundredth, ... of its surface
value, each 10 m layer with its own type down to 200 m (Williamson &
Hollins 2023, Jerlov 1976 Kd). A dash: below 200 m, where the profile, and
so this, says nothing.""")

print(f"\n  {'type':>5}" + "".join(f"{lv:>9.0e}" for lv in LEVELS))
depths = {}
for t in OCEANIC:
    p = jerlov.par_profile(SURFACE, BAND, 0.0, kd=deepest_descent(t),
                           unit="energy")
    depths[t] = [isolume(p, lv) for lv in LEVELS]
    print(f"  {t:>5}" + "".join(f"{z:>7.0f} m" if z is not None else
                                f"{'-':>9}" for z in depths[t]))

# --------------------------------------------------------------------------
rule("2. How far an isolume moves for each tenfold dimming")

print("""At dusk the surface light falls by orders of magnitude, and every
isolume rises. The distance it moves for each factor of ten is ln(10)
divided by the mean Kd(PAR) over the depths it passes through, and
Kd(PAR) is not the same at every depth.""")

print(f"\n  {'type':>5}" + "".join(f"{f'{a:.0e}->{b:.0e}':>15}"
                                    for a, b in zip(LEVELS, LEVELS[1:])))
flat = jerlov.par_profile(SURFACE, BAND, 0.0, unit="energy",
                         kd=jerlov.water("I", source="jerlov1976"))
flat_z = [flat.depth_of_fraction(lv) for lv in LEVELS[:3]]
flat_i = [b - a for a, b in zip(flat_z, flat_z[1:])]
step = {}
for t in OCEANIC:
    z = depths[t]
    step[t] = [b - a if a is not None and b is not None else None
               for a, b in zip(z, z[1:])]
    print(f"  {t:>5}" + "".join(f"{s:>13.1f} m" if s is not None else
                                f"{'-':>15}" for s in step[t]))

print(f"""
  In III the first tenfold takes {step["III"][0]:.0f} m and the next ones {min(s for s in step["III"][1:] if s):.0f} to {max(s for s in step["III"][1:] if s):.0f} m:
  near the surface the red and the violet are still being lost, and below
  only the blue-green is left, which goes further. In every type shown the
  steps grow with depth, so an animal holding to an isolume moves further,
  for the same dimming, the deeper it is.

  The depth profile matters as much. In I the steps are {step["I"][0]:.0f} and {step["I"][1]:.0f} m; with
  I's own Kd all the way down they would be {flat_i[0]:.0f} and {flat_i[1]:.0f} m. Below 20 m the
  water typically turns IA and then IB, and that roughly halves them.""")

# --------------------------------------------------------------------------
rule("3. The colour of the light at each isolume")

print("""Below the first few tens of metres almost nothing but blue is left.
The wavelength carrying the most photons, at each level, in Jerlov II:""")

d = deepest_descent("II")
photons = SURFACE * BAND          # proportional to photons, per nm
print(f"\n  {'level':>7} {'depth':>8} {'peak':>8}")
for level, z in zip(LEVELS, depths["II"]):
    if z is None:
        continue
    t = d.transmittance_at(z)
    print(f"  {level:>7.0e} {z:>6.0f} m {BAND[np.argmax(photons * t)]:>6.0f} nm")
print(f"  {'surface':>7} {0:>6.0f} m {BAND[np.argmax(photons)]:>6.0f} nm")

print("""
  From the first isolume down, the light that is left peaks in the blue,
  where at the surface it peaked in the green. An animal does not count
  photons the way PAR does, and one whose eye is tuned away from the blue
  sees its own isolumes at other depths; `what_an_eye_sees.py` shows how
  to integrate against a receptor's sensitivity instead.""")

# --------------------------------------------------------------------------
rule("4. Oceanic against coastal")

print("""The depth of one light level, a thousandth of the surface PAR, along
the coastal scale. The typical profile stops early in coastal water, so
here the surface type's Kd is used all the way down.""")

print(f"\n  {'type':>5} {'1e-03':>8}")
milli = {}
for t in ("II", "III", "1C", "3C", "5C", "7C", "9C"):
    p = jerlov.par_profile(SURFACE, BAND, 0.0, unit="energy",
                           kd=jerlov.water(t, source="jerlov1976"))
    milli[t] = p.depth_of_fraction(1e-3)
    print(f"  {t:>5} {milli[t]:>6.1f} m")

print(f"""
  The same light level lies {milli["II"] / milli["9C"]:.0f} times shallower in 9C than in II, so the
  same behaviour, tracking the same isolume, means a migration of metres
  rather than tens of metres. (III is at {milli["III"]:.0f} m here and at {depths["III"][2]:.0f} m in
  part 1: there the water typically clears below the surface layer.)""")

# --------------------------------------------------------------------------
rule("Before you use any of this")

print("""  - PAR stands in for the animal's own sensitivity. Use
    `integrate_response` with a measured spectral sensitivity if you have
    one.
  - The levels are fractions of the surface PAR. Twilight and moonlight
    have spectra of their own, which D65 does not represent, and the
    absolute threshold an animal responds to is a biological measurement.
  - This is planar PAR, from Ed. An eye looking sideways or up sees
    radiance, which falls off at a rate of its own.
  - Each layer's Kd is its type's surface Kd, and the profile is what was
    typical across more than 2500 campaigns, not what holds on the night
    you sampled.
""")

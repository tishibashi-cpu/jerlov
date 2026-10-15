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

light = jerlov.par_profile(SURFACE, BAND, 0.0, kd=deepest_descent("II"),
                           unit="energy")
print(f"\n  {'level':>7} {'depth':>8} {'peak':>8}")
for level, z in zip(LEVELS, depths["II"]):
    if z is None:
        continue
    spectrum = light.spectrum_at(z)
    print(f"  {level:>7.0e} {z:>6.0f} m "
          f"{light.wavelengths_nm[np.argmax(spectrum)]:>6.0f} nm")
print(f"  {'surface':>7} {0:>6.0f} m "
      f"{light.wavelengths_nm[np.argmax(light.spectrum_at(0.0))]:>6.0f} nm")

print("""
  From the first isolume down, the light that is left peaks in the blue,
  where at the surface it peaked in the green. An animal does not count
  photons the way PAR does, and one whose eye is tuned away from the blue
  sees its own isolumes at other depths; part 5 shows by how much.""")

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
rule("5. Isolumes for an eye rather than for PAR")

print("""An eye counts photons weighted by its pigment's sensitivity, not every
photon from 400 to 700 nm alike. `par_profile(..., photon_weight=)` takes
that weight, and the levels are then fractions of what the same eye would
catch at the surface. Three rods, as Gaussians at the peaks
`what_an_eye_sees.py` uses, against PAR, for a thousandth of the surface:""")

RODS = {"deep-sea 480 nm": 480.0, "shallow 500 nm": 500.0,
        "red-shifted 530 nm": 530.0}
eye_types = ("I", "II", "1C")
print(f"\n  {'':>19}" + "".join(f"{t:>9}" for t in eye_types))
eye = {}
for name, peak in [("PAR", None)] + list(RODS.items()):
    weight = None if peak is None else np.exp(-0.5 * ((BAND - peak) / 40.0) ** 2)
    eye[name] = {t: jerlov.par_profile(SURFACE, BAND, 0.0, unit="energy",
                                       kd=deepest_descent(t),
                                       photon_weight=weight
                                       ).depth_of_fraction(1e-3)
                 for t in eye_types}
    print(f"  {name:>19}" + "".join(f"{eye[name][t]:>7.0f} m"
                                    for t in eye_types))

deepest_rod = {t: max(RODS, key=lambda n: eye[n][t]) for t in eye_types}
peak_nm = {}
for t in ("II", "1C"):
    light = jerlov.par_profile(SURFACE, BAND, 0.0, unit="energy",
                               kd=deepest_descent(t))
    spectrum = light.spectrum_at(eye["PAR"][t])
    peak_nm[t] = light.wavelengths_nm[np.argmax(spectrum)]
tie = abs(eye["shallow 500 nm"]["1C"] - eye["red-shifted 530 nm"]["1C"])
print(f"""
  In I and II the {deepest_rod["I"]} rod's isolume is the deepest, {eye[deepest_rod["I"]]["I"] - eye["PAR"]["I"]:.0f} and
  {eye[deepest_rod["II"]]["II"] - eye["PAR"]["II"]:.0f} m below PAR's. In 1C the 500 and 530 nm rods are within {tie:.2f} m of
  each other and both below the 480 nm one: there the light left at PAR's
  isolume peaks at {peak_nm["1C"]:g} nm, against {peak_nm["II"]:g} nm in II. These are fractions of
  each eye's own surface catch: they say where an animal tracking a fixed
  share of its surface light would sit, not which eye sees best at depth.""")

# --------------------------------------------------------------------------
rule("Before you use any of this")

print("""  - Parts 1 to 4 use PAR for the animal's own sensitivity, and part 5's
    rods are Gaussians at plausible peaks, not measured curves. Pass a
    measured spectral sensitivity, per photon, as photon_weight.
  - The levels are fractions of the surface PAR. Twilight and moonlight
    have spectra of their own, which D65 does not represent, and the
    absolute threshold an animal responds to is a biological measurement.
  - This is planar PAR, from Ed. An eye looking sideways or up sees
    radiance, which falls off at a rate of its own.
  - Each layer's Kd is its type's surface Kd, and the profile is what was
    typical across more than 2500 campaigns, not what holds on the night
    you sampled.
""")

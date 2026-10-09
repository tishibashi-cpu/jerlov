"""How much light reaches a given depth, when the water changes on the way down.

The Jerlov type describes the top 10 m. Below that, water that is turbid at
the surface typically clears, and the clearest water typically turns a little
less clear. Williamson & Hollins (2023) give the type that is typical in each
10 m layer; `descend` attenuates the light layer by layer through it.

    python examples/light_at_depth.py

The profile is what was typical across more than 2500 campaigns, not what
holds at a given place or season.
"""

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


_banner()

NM = 490.0

# --------------------------------------------------------------------------
rule("1. What the profile says")

print("""The type that is typical in each layer below a given surface type. A
blank means fewer than ten campaigns supported a declaration, and nothing is
asserted there.""")

depths = [5, 15, 25, 35, 45, 55, 65, 75, 95, 125]
print("\n  surface" + "".join(f"{d:>6} m" for d in depths))
for surface_type in ("I", "II", "1C", "3C", "9C"):
    cells = [jerlov.water_type_at_depth(surface_type, d) or "" for d in depths]
    print(f"  {surface_type:>7}" + "".join(f"{c:>8}" for c in cells))

# --------------------------------------------------------------------------
rule(f"2. One Kd all the way down, or one per layer ({NM:g} nm)")

print("""`Scene.at_depth` uses the surface type's Kd at every depth. `descend`
uses the Kd of each layer's own type, from Jerlov (1976) by default.""")


def constant(surface_type, depth):
    kd = jerlov.water(surface_type, source="jerlov1976").kd(NM)
    return float(np.exp(-kd * depth))


print(f"\n  {'surface':>7} {'depth':>6} {'one Kd':>10} {'per layer':>10}"
      f" {'ratio':>7}   layers crossed")
for surface_type, depth in (("I", 60.0), ("II", 60.0), ("1C", 45.0),
                            ("3C", 60.0)):
    d = jerlov.descend(surface_type, depth, NM)
    one = constant(surface_type, depth)
    types = []
    for _, _, t in d.layers:
        if not types or types[-1] != t:
            types.append(t)
    print(f"  {surface_type:>7} {depth:>4.0f} m {one:>10.2e} "
          f"{d.transmittance:>10.2e} {d.transmittance / one:>7.2g}   "
          + " > ".join(types))

print("""
  The correction runs both ways. Jerlov I water typically turns IA and then
  IB below 20 m, so at 60 m it receives a third less light than its surface
  Kd implies. 3C typically clears to III and then II, so at 60 m it receives
  hundreds of times more. II stays II to 100 m, and the two agree.""")

# --------------------------------------------------------------------------
rule("3. The depth of the 1 percent light level")

print(f"""Where Ed({NM:g}) falls to 1 percent of its surface value, a common
working definition of the bottom of the euphotic zone, found by stepping
down 0.5 m at a time.""")


def one_percent_depth(surface_type, *, layered):
    for depth in np.arange(0.5, 200.5, 0.5):
        try:
            t = (jerlov.descend(surface_type, depth, NM).transmittance
                 if layered else constant(surface_type, depth))
        except jerlov.MissingQuantityError:
            return None, depth
        if t <= 0.01:
            return depth, None
    return None, None


print(f"\n  {'surface':>7} {'one Kd':>9} {'per layer':>10}")
for surface_type in ("I", "IB", "II", "III", "1C", "3C", "5C"):
    flat, _ = one_percent_depth(surface_type, layered=False)
    layered, stopped = one_percent_depth(surface_type, layered=True)
    shown = (f"{layered:>8.1f} m" if layered
             else f"  none above {stopped - 0.5:g} m")
    print(f"  {surface_type:>7} {flat:>7.1f} m {shown:>10}")

print("""
  Most types reach 1 percent while still inside the layers that are their
  own type, so the profile changes nothing. It matters where the light goes
  deeper than that: the 1 percent level of Jerlov I rises by more than 60 m,
  and that of 1C falls by a few metres.""")

# --------------------------------------------------------------------------
rule("4. PAR, not one wavelength")

print("""Photosynthesis uses 400-700 nm, not 490. `par_profile` attenuates
each wavelength with its own Kd and counts the photons that are left. D65
stands in for the surface spectrum.""")

band = np.arange(400.0, 701.0, 5.0)
d65 = np.interp(band, *jerlov.d65())
print(f"\n  {'surface':>7} {'one Kd':>9} {'per layer':>10}   1% at {NM:g} nm, per layer")
par_depths = {}
for surface_type in ("I", "IB", "II", "III", "1C", "3C", "5C", "7C", "9C"):
    w = jerlov.water(surface_type, source="jerlov1976")
    flat = jerlov.par_profile(d65, band, 0.0, kd=w, unit="energy")
    # As deep as the profile goes for this type.
    d = jerlov.descend(surface_type, jerlov.profile_depth(surface_type), band)
    layered = jerlov.par_profile(d65, band, 0.0, kd=d, unit="energy")
    par_depths[surface_type] = (flat.depth_of_fraction(),
                                layered.depth_of_fraction())
    try:
        shown = f"{par_depths[surface_type][1]:>8.1f} m"
    except jerlov.MissingQuantityError:
        shown = f"  none above {d.depth_m:g} m"
    single, stopped = one_percent_depth(surface_type, layered=True)
    print(f"  {surface_type:>7} {flat.depth_of_fraction():>7.1f} m {shown:>10}"
          f"   {f'{single:.1f} m' if single else f'none above {stopped - 0.5:g} m':>10}")

print(f"""
  From I to 5C the 1 percent depth of PAR is shallower than that of light
  at 490 nm: the red and the violet are gone within the first few metres,
  so PAR loses most of its photons early and only then settles to the decay
  of the blue-green. In 7C and 9C it is deeper, because there 490 nm is no
  longer the wavelength that gets furthest; the yellow-green is. The layers
  matter only where the light gets below the surface type's own layers, as
  for Jerlov I, where the 1 percent depth of PAR rises from
  {par_depths["I"][0]:.0f} m to {par_depths["I"][1]:.0f} m.""")

# --------------------------------------------------------------------------
rule("5. Where the profile runs out")

for surface_type, depth in (("3C", 80.0), ("9C", 15.0), ("IB", 250.0)):
    try:
        jerlov.descend(surface_type, depth, NM)
    except jerlov.MissingQuantityError as error:
        print(f"\n  {surface_type} to {depth:g} m:\n    {error}")

# --------------------------------------------------------------------------
rule("6. Into a scene")

print("""`Scene.at_depth` takes the descent as it is, and builds the
downwelling irradiance from it. A diver at 40 m under water that was 1C at
the surface is typically in II, so the path between diver and target is
II.""")

wl = np.arange(450.0, 651.0, 50.0)
surface = np.interp(wl, *jerlov.d65())
with warnings.catch_warnings():
    # Jerlov (1976) is interpolated between its printed wavelengths here,
    # which does not warn; nothing below rests on its extrapolated ends.
    warnings.simplefilter("error", jerlov.ProvenanceWarning)
    d = jerlov.descend("1C", 40.0, wl)
here = jerlov.water_type_at_depth("1C", 40.0)
scene = jerlov.Scene.at_depth(jerlov.water(here), 40.0, surface, wl, kd=d)
print(f"\n  {d!r}")
print(f"  water at 40 m: Jerlov {here}")
print(f"  {'nm':>6} {'Ed(40)/Ed(0)':>14}")
for nm, t in zip(wl, d.transmittance):
    print(f"  {nm:>6.0f} {t:>14.2e}")
print(f"\n  {scene!r}")

# --------------------------------------------------------------------------
rule("Before you use any of this")

print("""  - The profile is typical, not local. Williamson & Hollins (2023) give
    per-cell cruise and month counts for judging how well a cell is
    supported; a season or a front can change everything.
  - Each layer's Kd is that type's surface Kd, applied unchanged at depth,
    since that is how the classification is defined. Kd also depends on the
    sun and the sky, which the Jerlov tables average over.
  - Every layer's Kd comes from one source, Jerlov (1976) here. Mixing
    sources between layers would make the profile partly a profile of
    sources.
  - D65 stands in for the real surface spectrum.
  - PAR here is planar: it integrates Ed. PAR defined on scalar
    irradiance is larger, by a factor that depends on the light field.

  Every one of these is a choice you can replace with a measurement.
""")

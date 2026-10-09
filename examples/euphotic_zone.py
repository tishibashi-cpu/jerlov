"""How deep photosynthesis can go, from one Kd reading.

For phytoplankton ecology and biological oceanography: the depth of the
euphotic zone is usually quoted as where PAR falls to 1 percent of its
surface value, and usually estimated as 4.6 / Kd at a single wavelength.
This goes the long way round, with every step stated:

    a Kd(490) reading
    -> the Jerlov type it is nearest       (classify_kd)
    -> how that water changes with depth   (descend)
    -> PAR, wavelength by wavelength       (par_profile)

    python examples/euphotic_zone.py

Nothing here has been compared with a measured PAR profile. The output is
what the published coefficients imply.
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

# Nothing below rests on a flagged value, so nothing warns. If you change
# the reading or the band and something does, the warning is left to show.
BAND = np.arange(400.0, 701.0, 5.0)
SURFACE = np.interp(BAND, *jerlov.d65())    # stands in for the real sky
KD_490 = 0.030                               # the reading, 1/m

# --------------------------------------------------------------------------
rule("1. Which type is this water nearest?")

print(f"""Say a radiometer gave Kd(490) = {KD_490:.3f} 1/m. Austin & Petzold (1986)
reconstruct a spectrum from that one value; `classify_kd` ranks the Jerlov
types by their distance from it.""")

measured = jerlov.kd_spectrum(KD_490, 490.0, BAND)
nearest = jerlov.classify_kd(BAND, measured)
print(f"\n  {nearest!r}")
print(f"\n  {'type':>5} {'distance':>9}")
for water_type, distance in nearest.distances[:4]:
    print(f"  {water_type:>5} {distance:>9.3f}")

(first, d1), (second, d2) = nearest.distances[:2]
print(f"""
  The distance is the rms of ln(measured / type), so {d1:.2f} is a
  difference of about {100 * (math.exp(d1) - 1):.0f} percent on average, and {second} is not far
  behind at {d2:.2f}. The water is reported as {first}, with that runner-up,
  rather than as a fraction of the way between them: the types are points
  Jerlov chose, and a fractional type would be a quantity nobody defined.""")

TYPE = nearest.water_type

# --------------------------------------------------------------------------
rule("2. The 1 percent depth, three ways")

print(f"""4.6 / Kd(490) is the usual shortcut. PAR attenuated wavelength by
wavelength, with {TYPE}'s Kd at every depth, is another. The same, with the
type changing layer by layer as Williamson & Hollins (2023) found typical,
is a third.""")

shortcut = math.log(100) / KD_490
measured_par = jerlov.par_profile(SURFACE, BAND, 0.0, kd=measured,
                                  unit="energy")
one_kd = jerlov.par_profile(SURFACE, BAND, 0.0, unit="energy",
                            kd=jerlov.water(TYPE, source="jerlov1976"))
descent = jerlov.descend(TYPE, 200.0, BAND)
layered = jerlov.par_profile(SURFACE, BAND, 0.0, kd=descent, unit="energy")

rows = (
    ("4.6 / Kd(490)", shortcut),
    ("PAR, the reconstructed spectrum", measured_par.depth_of_fraction()),
    (f"PAR, {TYPE} all the way down", one_kd.depth_of_fraction()),
    ("PAR, layer by layer", layered.depth_of_fraction()),
)
print()
for label, depth in rows:
    print(f"  {label:<36} {depth:>6.1f} m")
print(f"\n  {descent!r}")

clearest_nm = BAND[np.argmin(measured)]
print(f"""
  The shortcut is the deepest. Kd(490) is close to the smallest Kd in the
  spectrum, which is at {clearest_nm:g} nm, so it describes the light that gets
  furthest; PAR also counts the red and the violet, which are gone within
  the first few metres.

  Rounding the spectrum to {TYPE} moves the answer by {abs(rows[2][1] - rows[1][1]):.0f} m, the price of
  a distance of {d1:.2f}. And {TYPE} does not stay {TYPE}: below {descent.layers[-1][0] if len(descent.layers) == 1 else next(lo for lo, _, t in descent.layers if t != TYPE):g} m it is typically
  {next((t for _, _, t in descent.layers if t != TYPE), TYPE)}, which is less clear, and the 1 percent level rises by
  {rows[2][1] - rows[3][1]:.0f} m.""")

# --------------------------------------------------------------------------
rule("3. The profile")

depths = np.array([0.0, 5.0, 10.0, 20.0, 40.0, 60.0, 80.0, 100.0])
profile = jerlov.par_profile(SURFACE, BAND, depths, kd=descent, unit="energy")
print(f"\n  {'depth':>7} {'PAR / PAR(0)':>13} {'type there':>11}")
for z, f, t in zip(depths, profile.fraction,
                   jerlov.water_type_at_depth(TYPE, depths)):
    print(f"  {z:>5.0f} m {f:>13.4f} {t or '':>11}")

print(f"""
  PAR(0) itself is {profile.surface_par:.0f} in D65's relative units. It is printed only
  to say that it is meaningless: give `par_profile` a measured surface
  spectrum in W m-2 nm-1 and it is umol photons m-2 s-1.""")

# --------------------------------------------------------------------------
rule("4. What colour is the light at the bottom?")

print("""Photosynthetic pigments do not absorb all of PAR equally, so the
colour of what is left matters as much as how much. Passing the surface
spectrum through one band at a time gives each band's share.""")

z1 = layered.depth_of_fraction()
bands = (("violet-blue", 400.0, 500.0), ("green", 500.0, 600.0),
         ("orange-red", 600.0, 700.0))
print(f"\n  {'':>12} {'surface':>9} {f'{z1:.0f} m':>9}")
total = jerlov.par_profile(SURFACE, BAND, [0.0, z1], kd=descent,
                           unit="energy").par
shares = {}
for name, lo, hi in bands:
    mask = (BAND >= lo) & ((BAND < hi) if hi < 700 else True)
    part = jerlov.par_profile(SURFACE * mask, BAND, [0.0, z1], kd=descent,
                              unit="energy").par
    shares[name] = part / total
    print(f"  {name:>12} {shares[name][0]:>8.0%} {shares[name][1]:>9.0%}")

print(f"""
  At the surface the three bands are comparable. At the bottom of the
  euphotic zone {shares["violet-blue"][1]:.0%} of what is left is violet-blue and the orange-red
  is gone, so the red absorption band of chlorophyll a, near 675 nm,
  receives almost none; only its blue band, near 440 nm, has light to use.
  (Each band's edge samples are shared by the trapezoid rule, so a column
  can miss 100 percent by a rounding.)""")

# --------------------------------------------------------------------------
rule("5. Which edition of the classification?")

print("""The editions of the classification differ, and Jerlov's (1976) Kd
for type I falls below that of pure sea water at 9 of the 15 wavelengths
Austin & Petzold (1986) tabulate (DATA.md section 3); they replace it. The
distances, and the 1 percent depth of the nearest type, depend on which
table you compare with.""")

print(f"\n  {'source':>12} {'nearest':>8} {'distance':>9} {'1% depth':>9}")
for source in ("jerlov1976", "jerlov1968", "austin1986"):
    r = jerlov.classify_kd(BAND, measured, source=source)
    p = jerlov.par_profile(SURFACE, BAND, 0.0, unit="energy",
                           kd=jerlov.water(r.water_type, source=source))
    print(f"  {source:>12} {r.water_type:>8} {r.distances[0][1]:>9.3f} "
          f"{p.depth_of_fraction():>7.1f} m")

other = jerlov.kd_spectrum(0.045, 490.0, BAND)
by_edition = {source: jerlov.classify_kd(BAND, other, source=source).water_type
              for source in ("jerlov1976", "jerlov1968")}
print(f"""
  Here the three editions agree on {TYPE}, and their 1 percent depths are
  within a few metres. They need not agree: Kd(490) = 0.045 is nearest
  {by_edition["jerlov1976"]} in Jerlov (1976) and {by_edition["jerlov1968"]} in Jerlov (1968). Name the source when you
  report a type; a Jerlov type without its edition is not one number.""")

# --------------------------------------------------------------------------
rule("Before you use any of this")

print("""  - The Kd spectrum is reconstructed from one reading by a model good to
    about 8 percent below 590 nm and 31 percent at 670 nm. Measure the
    spectrum if you can; `classify_kd` and `par_profile` take it as it is.
  - D65 stands in for the surface spectrum. The sky, the sun's elevation
    and the sea surface all change it, and with it PAR's colour.
  - This is planar PAR, from Ed. PAR on scalar irradiance, which is what
    a spherical quantum sensor reads, is larger by a factor that depends on
    the light field and is not determined here.
  - Each layer's Kd is its type's surface Kd, and the profile is what was
    typical across more than 2500 campaigns, not what holds at your
    station in your season.
  - The 1 percent depth is a convention. Phytoplankton grow below it.

  Every one of these is a choice you can replace with a measurement.
""")

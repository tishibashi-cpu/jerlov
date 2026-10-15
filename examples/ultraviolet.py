"""How deep UV-A goes, against PAR, in each Jerlov type.

For work on ultraviolet exposure under water: corals and other reef
organisms, plankton and larvae near the surface, photochemistry. UV-A is
315-400 nm, as the CIE divides the ultraviolet (UV-B 280-315 nm, UV-C
100-280 nm):

    CIE S 017:2020, International Lighting Vocabulary, 2nd edition,
        term 17-21-008, "ultraviolet radiation", note 1.

`par_profile` integrates over any band with `band=`, so UV-A and PAR come
from the same call, wavelength by wavelength, layer by layer as in
`descend`. What the published tables do not cover is said, not filled.

    python examples/ultraviolet.py

Nothing here has been compared with a measured ultraviolet profile.
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

UVA = (315.0, 400.0)
# From 310 nm: par_profile reads the sample either side of each end of the
# band, and Jerlov's (1976) Kd below 310 nm is extrapolated (DATA.md
# section 16), so starting lower would rest on it for nothing.
WAVELENGTHS = np.arange(310.0, 701.0, 5.0)
SURFACE = np.interp(WAVELENGTHS, *jerlov.d65())     # stands in for the sky
TYPES = ("I", "IA", "IB", "II", "III", "1C", "3C", "5C", "7C", "9C")


def profiles(water_type):
    """(UV-A, PAR) profiles from the surface, layer by layer."""
    d = jerlov.descend(water_type, jerlov.profile_depth(water_type),
                       WAVELENGTHS)
    return tuple(jerlov.par_profile(SURFACE, WAVELENGTHS, 0.0, kd=d,
                                    unit="energy", band=band)
                 for band in (UVA, jerlov.PAR_RANGE_NM))


# --------------------------------------------------------------------------
rule("1. What the tables cover in the ultraviolet")

print("""Jerlov's (1976) Kd is printed from 310 nm for most types, so UV-A is
covered and UV-B, which starts at 280 nm, is not. Not every type reaches that
far down.""")

covered = {}
for water_type in TYPES:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", jerlov.ProvenanceWarning)
        try:
            covered[water_type] = profiles(water_type)
        except jerlov.MissingQuantityError:
            first = str(caught[0].message) if caught else ""
            gaps = [w for w in WAVELENGTHS if f"missing at {w:g} nm" in first]
            print(f"\n  {water_type}: no answer. Kd is missing at "
                  f"{gaps[0]:g}-{gaps[-1]:g} nm, inside UV-A,\n"
                  "  and the gap is not filled in.")
missing = [t for t in TYPES if t not in covered]
print(f"""
  So {len(covered)} of the {len(TYPES)} types have an answer below, and {' and '.join(missing)} are
  left out rather than guessed.""")

# --------------------------------------------------------------------------
rule("2. How deep UV-A goes, against PAR")

print("""The depths at which 10 and 1 percent of the surface photons remain,
for UV-A and for PAR, with the surface spectrum the same for both.""")

print(f"\n  {'type':>5} {'UV-A 10%':>9} {'UV-A 1%':>8} {'PAR 1%':>7} "
      f"{'UV-A / PAR':>11}")
share = {}
for water_type, (uva, par) in covered.items():
    z_uva, z_par = uva.depth_of_fraction(0.01), par.depth_of_fraction(0.01)
    share[water_type] = z_uva / z_par
    print(f"  {water_type:>5} {uva.depth_of_fraction(0.1):>7.1f} m "
          f"{z_uva:>6.1f} m {z_par:>5.1f} m {share[water_type]:>11.2f}")

oceanic = [t for t in covered if not t.endswith("C")]
coastal = [t for t in covered if t.endswith("C")]
names = list(share)
steps = [share[a] - share[b] for a, b in zip(names, names[1:])]
big = int(np.argmax(steps))
in_uva = (WAVELENGTHS >= UVA[0]) & (WAVELENGTHS <= UVA[1])
in_par = (WAVELENGTHS >= 400.0) & (WAVELENGTHS <= 700.0)
clearest = {}
for water_type in (names[big], names[big + 1]):
    k = jerlov.water(water_type, source="jerlov1976").kd(WAVELENGTHS)
    clearest[water_type] = (k[in_uva].min(), k[in_par].min(),
                            WAVELENGTHS[in_par][np.argmin(k[in_par])])
(a_uv, a_par, a_nm), (b_uv, b_par, b_nm) = clearest.values()
print(f"""
  In the oceanic types UV-A reaches {min(share[t] for t in oceanic):.2f} to {max(share[t] for t in oceanic):.2f} of PAR's 1 percent
  depth; in the coastal types {min(share[t] for t in coastal):.2f} to {max(share[t] for t in coastal):.2f}. The step is between {names[big]} and
  {names[big + 1]}, and the tables show where it comes from. The smallest Kd in UV-A
  goes from {a_uv:.3f} to {b_uv:.2f} 1/m; the smallest in PAR barely moves, from {a_par:.3f}
  at {a_nm:g} nm to {b_par:.2f} at {b_nm:g} nm. The clearest UV-A is {a_uv / a_par:.1f} times as
  attenuated as the clearest PAR in {names[big]}, and {b_uv / b_par:.1f} times in {names[big + 1]}.""")

# --------------------------------------------------------------------------
rule("3. What is left of UV-A where PAR is at 10 percent")

print("""An organism that sits where a tenth of the surface PAR reaches it gets
this much of the surface UV-A.""")

print(f"\n  {'type':>5} {'depth':>7} {'UV-A left':>10}")
left = {}
for water_type, (uva, par) in covered.items():
    z = par.depth_of_fraction(0.1)
    left[water_type] = jerlov.par_profile(
        SURFACE, WAVELENGTHS, [0.0, z], unit="energy", band=UVA,
        kd=jerlov.descend(water_type, jerlov.profile_depth(water_type),
                          WAVELENGTHS)).fraction[1]
    print(f"  {water_type:>5} {z:>5.1f} m {left[water_type]:>10.2%}")

print(f"""
  In the oceanic types that is {min(left[t] for t in oceanic):.1%} to {max(left[t] for t in oceanic):.1%} of the surface UV-A; in the
  coastal ones {min(left[t] for t in coastal):.2%} to {max(left[t] for t in coastal):.2%}. The same share of PAR comes with
  {min(left[t] for t in oceanic) / max(left[t] for t in coastal):.0f} times as much UV-A or more in the open ocean as on
  the coast.""")

# --------------------------------------------------------------------------
rule("Before you use any of this")

print("""  - D65 stands in for the surface spectrum. It is a standard daylight,
    not a measured sky, and the ultraviolet at the surface depends on the
    sun's elevation, the atmosphere and the ozone column. The depths are
    fractions of the surface value, so they depend on its shape across
    each band, not on its size.
  - These are photons, counted over the band, from planar downwelling
    irradiance. Biological or chemical effect needs an action spectrum,
    and the package applies none.
  - The Kd is Jerlov's (1976), the layers those Williamson & Hollins
    (2023) found typical. Another edition, or your station's own water,
    gives other depths.
  - UV-B is not covered at all, and 7C and 9C not even for UV-A.

  Every one of these is a choice you can replace with a measurement.
""")

"""How far a blue-green laser gets: underwater optical links and lidar.

For engineers designing underwater optical wireless communication or a
lidar. A narrow beam received by a narrow field of view loses power as
exp(-c r), with c the beam attenuation coefficient, so the range a loss
budget buys is set by c, and c is set by the water and by whose
coefficients you believe.

    python examples/optical_link.py

What this does not do: a wide receiver also collects light scattered back
into it, so its signal falls off more slowly than exp(-c r). That needs
the phase function and multiple scattering, which this package does not
model. Everything below is the narrow-beam, narrow-field case, the one
with no approximation in it beyond the value of c.
"""

import math
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

LASERS = (450.0, 470.0, 488.0, 520.0, 532.0)
TYPES = ("IB", "II", "III", "1C", "3C", "5C")   # williamson2022 covers these
LOSS_DB = 40.0          # the attenuation the link can afford, after geometry
DB_PER_ATTENUATION_LENGTH = 10.0 * math.log10(math.e)   # 4.34 dB per c*r = 1


def range_for(loss_db, c):
    """The path at which exp(-c r) has cost ``loss_db``."""
    return loss_db / DB_PER_ATTENUATION_LENGTH / c


# --------------------------------------------------------------------------
rule("1. Beam attenuation at common laser lines")

print("""c = a + b from Williamson & Hollins (2022), the default source and the
only one whose a and b rest on measurement. 1/m.""")

print(f"\n  {'type':>5}" + "".join(f"{nm:>8.0f}" for nm in LASERS)
      + "   lowest c, 420-650 nm")
grid = np.arange(420.0, 651.0, 1.0)
best = {}
for t in TYPES:
    w = jerlov.water(t)
    c_grid = w.c(grid)
    best[t] = grid[np.argmin(c_grid)]
    print(f"  {t:>5}" + "".join(f"{w.c(nm):>8.3f}" for nm in LASERS)
          + f"   {np.min(c_grid):.3f} at {best[t]:.0f} nm")

gain = {t: jerlov.water(t).c(450.0) / jerlov.water(t).c(532.0) - 1
        for t in TYPES}
print(f"""
  The clearest wavelength moves from {best["IB"]:.0f} nm in IB to {best["5C"]:.0f} nm in 5C, as
  dissolved and particulate matter absorb the blue. Even in IB, the
  clearest type this source has, c at 450 nm is within {100 * abs(gain["IB"]):.0f} percent of c
  at 532 nm; from II onwards it is {100 * min(gain[t] for t in TYPES[1:]):.0f} to {100 * max(gain.values()):.0f} percent higher.""")

sm = {t: jerlov.water(t, source="solonenko2015") for t in ("I", "IA", "IB")}
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always", jerlov.ProvenanceWarning)
    sm_gain = {t: w.c(450.0) / w.c(532.0) - 1 for t, w in sm.items()}
    b_share = sm["I"].b(450.0) / sm["I"].c(450.0)
print(f"""
  The advantage of a blue source belongs to clearer water, Jerlov I and
  IA, which Williamson & Hollins do not cover because too few measurements
  exist. Solonenko & Mobley do: their c at 450 nm is {-100 * sm_gain["I"]:.0f} percent below
  c at 532 nm in I and {-100 * sm_gain["IA"]:.0f} percent in IA. They put it {-100 * sm_gain["IB"]:.0f} percent below in
  IB too, where Williamson & Hollins see no difference; part 3 is about
  that kind of disagreement.""")
print()
for message in sorted({str(w.message).split(" See DATA")[0] for w in caught}):
    print(f"  warned: {message}")
print(f"""
  Their b for the clearest types is flagged as suspect, since the
  scattering parameter they print for them does not fit their own b
  column (DATA.md section 4). At 450 nm in I, b is {100 * b_share:.0f} percent of c: were
  it twice as large, c would rise by that much, against a gap of
  {-100 * sm_gain["I"]:.0f} percent. The blue advantage there is absorption's.""")

# --------------------------------------------------------------------------
rule(f"2. The range a {LOSS_DB:g} dB attenuation budget buys")

print(f"""Each attenuation length, c r = 1, costs {DB_PER_ATTENUATION_LENGTH:.2f} dB. {LOSS_DB:g} dB is therefore
{LOSS_DB / DB_PER_ATTENUATION_LENGTH:.1f} attenuation lengths, whatever the water. Geometric spreading and
the receiver's own losses come out of the budget first; this is what is
left for the water.""")

print(f"\n  {'type':>5} {'450 nm':>9} {'532 nm':>9} {'best':>9}")
for t in TYPES:
    w = jerlov.water(t)
    r450, r532 = range_for(LOSS_DB, w.c(450.0)), range_for(LOSS_DB, w.c(532.0))
    r_best = range_for(LOSS_DB, w.c(best[t]))
    print(f"  {t:>5} {r450:>7.1f} m {r532:>7.1f} m {r_best:>7.1f} m")

shrink = jerlov.water("5C").c(532.0) / jerlov.water("IB").c(532.0)
print(f"""
  Range is proportional to the budget: twice the dB, twice the distance.
  And inversely to c, so a link that reaches a given distance in IB
  reaches 1/{shrink:.0f} of it in 5C, whatever the budget.""")

# --------------------------------------------------------------------------
rule("3. Whose c?")

print("""Solonenko & Mobley (2015) obtained a and b by inverting Kd. At 532 nm
the two published sets give these ranges for the same budget:""")

print(f"\n  {'type':>5} {'Williamson':>11} {'Solonenko':>10} {'ratio':>7}")
ratios = []
for t in TYPES:
    r_wh = range_for(LOSS_DB, jerlov.water(t).c(532.0))
    r_sm = range_for(LOSS_DB,
                     jerlov.water(t, source="solonenko2015").c(532.0))
    ratios.append(max(r_wh, r_sm) / min(r_wh, r_sm))
    print(f"  {t:>5} {r_wh:>9.1f} m {r_sm:>8.1f} m {r_sm / r_wh:>7.2f}")

print(f"""
  The two sources disagree on the range by up to a factor of
  {max(ratios):.1f}. A link specified as "100 m in Jerlov III" is not a
  specification until it says whose Jerlov III.""")

# --------------------------------------------------------------------------
rule("4. Measured waters")

print("""Petzold (1972) measured c at 530 nm in eight real waters. They are not
Jerlov types, and no mapping to types is made here; they show what a range
in water that was actually measured looks like.""")

print(f"\n  {'station':>9} {'c(530)':>8} {'range':>8}   where")
for station in jerlov.PETZOLD_STATIONS:
    f = jerlov.petzold_scattering(station)
    print(f"  {station:>9} {f.c:>8.3f} {range_for(LOSS_DB, f.c):>6.1f} m   "
          f"{f.locale}")

# --------------------------------------------------------------------------
rule("5. Lidar: the same budget, there and back")

print(f"""A lidar's narrow beam goes down and comes back, so it pays exp(-2 c z)
and the depth it reaches is half the range. At 532 nm, with the same
{LOSS_DB:g} dB for the water:""")

print(f"\n  {'type':>5} {'depth':>8}")
for t in TYPES:
    print(f"  {t:>5} {range_for(LOSS_DB, jerlov.water(t).c(532.0)) / 2:>6.1f} m")

print("""
  A wide-field lidar receiver also collects light scattered back into it,
  so its signal falls more slowly and it reaches deeper. That gain depends
  on the phase function and on the field of view, and is not computed
  here.""")

# --------------------------------------------------------------------------
rule("Before you use any of this")

print(f"""  - The budget is {LOSS_DB:g} dB of attenuation by the water alone. Spreading,
    pointing error, the receiver's noise and the sun's background are the
    rest of the link and are yours to supply.
  - exp(-c r) is exact only for a beam received with no scattered light.
    A real receiver collects some, and does better.
  - c comes from published spectra for Jerlov types, which describe the
    upper 10 m and what was typical. Coastal water varies by the day.
  - The two sources disagree. Pick one, and say which.
""")

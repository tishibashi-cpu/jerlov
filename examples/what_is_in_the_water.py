"""How much of the absorption is the water, and how much is what is in it.

A Jerlov type's absorption is that of pure water plus that of whatever the
water carries: phytoplankton, dissolved organic matter, sediment. Taking the
pure water out shows what distinguishes one type from another, and where in
the spectrum there is nothing to distinguish.

    python examples/what_is_in_the_water.py

The pure water spectrum must be the one the source itself built its a on;
subtracting another laboratory's mixes two sets of measurements.
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

TYPES = jerlov.get_source("williamson2022").water_types
WL = np.array([412.0, 440.0, 490.0, 550.0, 600.0, 650.0, 700.0])
AW = jerlov.pure_water_absorption(WL)

# --------------------------------------------------------------------------
rule("1. The absorption of what is in the water")

print("""a - aw, in 1/m, from Williamson & Hollins (2022) and the pure water
spectrum they built it on.""")

print(f"\n  {'':>8}" + "".join(f"{nm:>8.0f}" for nm in WL) + "   nm")
print(f"  {'aw':>8}" + "".join(f"{v:>8.4f}" for v in AW))
for t in TYPES:
    contents = jerlov.water(t).a(WL) - AW
    print(f"  {t:>8}" + "".join(f"{v:>8.4f}" for v in contents))

print("""
  At 412 nm the contents of 5C absorb twelve times what those of IB do. The
  small rise from 600 to 650 nm in the turbid types is the red absorption
  band of chlorophyll, which the model behind the spectra includes.""")

# --------------------------------------------------------------------------
rule("2. The share that is the water")

print("""aw / a: how much of each type's absorption is pure water.""")

print(f"\n  {'':>8}" + "".join(f"{nm:>8.0f}" for nm in WL) + "   nm")
for t in TYPES:
    share = AW / jerlov.water(t).a(WL)
    print(f"  {t:>8}" + "".join(f"{v:>8.0%}" for v in share))

wide = np.arange(600.0, 801.0)
with warnings.catch_warnings(record=True) as caught:
    # Beyond 715 nm the spectra are the fitted model, not measurement, and
    # the package says so; here that is the point being made.
    warnings.simplefilter("always")
    a_5c = jerlov.water("5C").a(wide)
water_only = [nm for nm, a_ in zip(wide, a_5c)
              if abs(a_ - jerlov.pure_water_absorption(nm)) <= 0.005 * a_]
print(f"""
  From {water_only[0]:g} nm on, even the most turbid type, 5C, absorbs as pure
  water does, to within half a percent: the model behind these spectra
  gives the contents no absorption there. That is the model, not a
  measurement, and the package warned as much: beyond 715 nm every value is
  model extrapolation ({len(caught)} warning here). Section 3 shows what the
  measurements say at 715 nm.""")

# --------------------------------------------------------------------------
rule("3. The same, at the measured points")

print("""The smooth spectra were fitted to measured averages. At those, with
their spread across campaigns, for Jerlov III:""")

m = jerlov.measured_points("III", "a")
aw_m = jerlov.pure_water_absorption(m.wavelengths)
print(f"\n  {'nm':>6} {'a':>8} {'+-':>7} {'a - aw':>8} {'campaigns':>10}")
for nm, a_, sd, aw_, n in zip(m.wavelengths, m.values, m.std_dev, aw_m,
                              m.n_campaigns):
    print(f"  {nm:>6.0f} {a_:>8.4f} {sd:>7.4f} {a_ - aw_:>8.4f} {n:>10d}")

fitted = jerlov.water("III").a(715.0)
print(f"""
  Where a - aw is smaller than the spread, as at 630 nm, the measurement does
  not resolve the contents' absorption at all.

  At 715 nm it is the other way round. The measured a is {m.values[-1]:.3f},
  seven times its spread above aw, while the fitted spectrum there is
  {fitted:.3f}, which is aw itself. The fit gives the contents nothing in the
  near infrared; the measurement does not. Take the model's near-infrared
  values as the model's.""")

# --------------------------------------------------------------------------
rule("4. Only one source can do this")

for source in ("solonenko2015", "jerlov1976", "austin1986"):
    try:
        jerlov.pure_water_absorption(500.0, source=source)
    except jerlov.MissingQuantityError as error:
        print(f"\n  {source}:\n    {error}")

# --------------------------------------------------------------------------
rule("Before you use any of this")

print("""  - The pure water spectrum is the one in Williamson & Hollins' own
    spreadsheet, which their paper attributes to Buiteveld et al. (1994).
    It has not been compared with Buiteveld's table. DATA.md section 20.
  - Everything outside 412 to 715 nm is the fitted model, not measurement.
  - a - aw lumps phytoplankton, dissolved matter and sediment together.
    Separating them needs measurements these data do not include.

  Every one of these is a choice you can replace with a measurement.
""")

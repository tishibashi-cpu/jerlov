"""Solar heating of the upper ocean, for people writing ocean models.

ROMS, MITgcm, NEMO and CESM all absorb shortwave radiation with the same two
exponentials and the same six numbers from Paulson & Simpson (1977). The
numbers are usually copied from a secondary source. This shows where they come
from, how they behave, and where they do not reproduce the table they were
fitted to.

    python examples/solar_heating.py
"""

import numpy as np

import jerlov
from jerlov import _data


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
OCEANIC = ("I", "IA", "IB", "II", "III")

# --------------------------------------------------------------------------
rule("1. The parameters")

print("""    I(z) / I(0) = R exp(-z/zeta1) + (1 - R) exp(-z/zeta2)

The first term is the red end of the spectrum, gone within a few metres. The
second is blue-green, and carries the heat down.
""")
print(f"  {'type':>5} {'R':>7} {'zeta1 [m]':>11} {'zeta2 [m]':>11}")
for water_type in OCEANIC:
    p = jerlov.shortwave_parameters(water_type)
    print(f"  {water_type:>5} {p.R:>7.2f} {p.zeta1_m:>11.2f} {p.zeta2_m:>11.1f}")

alternative = jerlov.shortwave_parameters("I_upper50")
print(f"\n  There is a second row for type I, fitted over the upper 50 m:")
print(f"  {'I*':>5} {alternative.R:>7.2f} {alternative.zeta1_m:>11.2f} "
      f"{alternative.zeta2_m:>11.1f}")
print(f"    {alternative.note}")

# --------------------------------------------------------------------------
rule("2. What fraction reaches each level")

depths = [0.0, 0.5, 1, 2, 5, 10, 20, 50, 100]
print(f"  {'type':>5}" + "".join(f"{d:>9g} m" for d in depths))
for water_type in OCEANIC:
    row = "".join(f"{jerlov.solar_fraction(water_type, d):>11.4f}"
                  for d in depths)
    print(f"  {water_type:>5}{row}")

print("""
  Read across from 0 to 0.5 m: between a quarter and a half of the surface
  flux is gone in the first half metre, almost all of it to water absorbing
  red light. A model with a 1 m top cell puts all of that in the top cell.""")

# --------------------------------------------------------------------------
rule("3. Heating rate per layer")

print("""What a model actually needs is the divergence: how much is absorbed
between one level and the next.
""")
levels = np.array([0.0, 1.0, 2.5, 5.0, 10.0, 20.0, 50.0, 100.0])
print(f"  {'layer':>14}" + "".join(f"{t:>9}" for t in OCEANIC))
for top, bottom in zip(levels[:-1], levels[1:]):
    cells = "".join(
        f"{jerlov.solar_fraction(t, top) - jerlov.solar_fraction(t, bottom):>8.1%} "
        for t in OCEANIC
    )
    print(f"  {top:>5.1f}-{bottom:<6.1f} m {cells}")
remainder = "".join(f"{jerlov.solar_fraction(t, 100.0):>8.1%} " for t in OCEANIC)
print(f"  {'below 100':>12} m {remainder}")

print("""
  In Jerlov III almost nothing is left below 20 m; in Jerlov I a percent or so
  still reaches 100 m. That difference is what the classification buys you.""")

# --------------------------------------------------------------------------
rule("4. Where the parameters came from, and where they fail")

print("""Paulson & Simpson fitted Jerlov (1968) Table XXI, which this package
ships. Feeding the published parameters back gives:
""")
rows = _data._rows("jerlov1968_total_irradiance.csv")
print(f"  {'type':>5} {'depth':>7} {'Jerlov':>9} {'2-exp fit':>11} {'error':>8}")
worst = 0.0
for row in rows:
    if row["water_type"] not in OCEANIC or not row["percent_of_surface"]:
        continue
    depth = float(row["depth_m"])
    if depth == 0 or depth > 100:
        continue
    want = float(row["percent_of_surface"]) / 100
    got = jerlov.solar_fraction(row["water_type"], depth)
    error = (got - want) / want
    worst = max(worst, abs(error))
    if depth in (1.0, 10.0, 50.0):
        flag = "  <--" if abs(error) > 0.30 else ""
        print(f"  {row['water_type']:>5} {depth:>5.0f} m {want:>9.4g} "
              f"{got:>11.4g} {error:>+7.1%}{flag}")

print(f"""
  Worst disagreement anywhere in the upper 100 m: {worst:.0%}, at 1 m.

  Two exponentials cannot follow the sharp decay in the first metre or two.
  The paper is explicit about the same limitation deeper down: it excluded the
  10 m point from the fit because the form does not capture the transition
  there.

  **If your top cell is a metre thick, this matters to you.** DATA.md
  section 14.""")

# --------------------------------------------------------------------------
rule("5. Which type applies at depth")

print("""The classification is defined on the top 10 m. Below that, clear water
is typically less clear and turbid water typically clearer (Williamson &
Hollins 2023). A model with 50 m cells may want the deeper type.
""")
print(f"  {'surface':>8}" + "".join(f"{d:>8g} m" for d in (5, 25, 55, 105, 155)))
for water_type in ("I", "IA", "II", "III", "3C"):
    row = "".join(f"{(jerlov.water_type_at_depth(water_type, d) or '--'):>10}"
                  for d in (5, 25, 55, 105, 155))
    print(f"  {water_type:>8}{row}")

print("""
  `--` means the paper declined to declare a type there, on fewer than ten
  measurement campaigns. Coastal water runs out quickly.

  Note that Paulson & Simpson fitted the oceanic types only. Asking for a
  coastal type raises rather than substituting a neighbour:""")
try:
    jerlov.shortwave_parameters("3C")
except KeyError as error:
    print(f"\n    {str(error)[:96]}...")

# --------------------------------------------------------------------------
rule("Before you put these in a model")

print("""  - The parameters are broadband, 300-2500 nm, and say nothing about
    spectrum. The rest of this package is spectral; the two do not mix.
  - They were fitted to Jerlov (1968), the first edition. The classification
    was revised at least three times after that. DATA.md section 2.
  - The fit misses its own source by 46 percent at 1 m. If your vertical grid
    resolves the top metre, that error is in your surface heat budget.
  - Jerlov (1968) Table XXI assumes a solar altitude of 90 degrees for the
    oceanic types. A low sun attenuates faster, as Paulson & Simpson's own
    Run 1 shows.
  - Real water is not one Jerlov type all year. Choosing one is a modelling
    decision, not a lookup.
""")

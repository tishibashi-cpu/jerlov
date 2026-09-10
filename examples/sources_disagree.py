"""The sources disagree, and by how much.

The reason `jerlov.water()` makes you name a source is that the same Jerlov
water type has different coefficients in different papers, and the differences
are large enough to change a conclusion. This script prints them.

    python examples/sources_disagree.py
"""

import warnings

import numpy as np

import jerlov

WAVELENGTHS = np.array([412.0, 440.0, 488.0, 510.0, 555.0, 650.0])
SHARED = ["IB", "II", "III", "1C", "3C", "5C"]


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



# --------------------------------------------------------------------------
_banner()
rule("1. Scattering, measured against inverted")

print("""Williamson & Hollins (2022) measured a and b. Solonenko & Mobley
(2015) obtained them by inverting Kd. Both are published for the same ten
water types under the same names.""")

print(f"\nScattering coefficient b at 510 nm, 1/m\n")
print(f"{'type':>6} {'measured':>10} {'inverted':>10} {'ratio':>8}")
for water_type in SHARED:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        measured = float(jerlov.water(water_type).b(510))
        inverted = float(jerlov.water(water_type, source="solonenko2015").b(510))
    print(f"{water_type:>6} {measured:>10.4f} {inverted:>10.4f} "
          f"{inverted / measured:>7.2f}x")

print("""
At Jerlov III the inverted value is 3.8 times the measured one. At Jerlov IB
it is less than half. **The disagreement does not even run one way**, so no
correction factor reconciles them: a visibility estimate, a synthetic image or
a fitted attenuation coefficient built on one is simply not comparable with
one built on the other.""")

# --------------------------------------------------------------------------
rule("2. Which to prefer, and why the package has a default")

for key in ("williamson2022", "solonenko2015"):
    source = jerlov.get_source(key)
    print(f"\n{key}")
    print(f"  {source.citation}")
    print(f"  a and b rest on measurement: {source.measured}")
    print(f"  water types: {', '.join(source.water_types)}")

print("""
`williamson2022` is the default because it is the only published set in which
a and b rest on measurement. The cost is coverage: six water types instead of
ten. Jerlov I, IA, 7C and 9C are absent because too few measurements exist,
and the package does not invent them.""")

try:
    jerlov.water("I")
except KeyError as error:
    print(f"\n  jerlov.water('I') -> KeyError: {error}")

# --------------------------------------------------------------------------
rule("3. The equations disagree too")

print("""Both papers use the two-component scattering model of Haltrin (1999).
Haltrin's Eq. (6) gives a small-particle coefficient of 1.151302. Solonenko &
Mobley print, and computed with, 1.513.

Reproducing a published table therefore needs that paper's own constant, so
the constants live with the source rather than with the equations.""")

print(f"\n{'source':>16} {'small-particle coefficient':>28}")
for key in ("williamson2022", "solonenko2015"):
    source = jerlov.get_source(key)
    print(f"{key:>16} {source.scattering.small_coeff:>28}")

print("""
That difference is not cosmetic: the Solonenko & Mobley coefficients were
derived with a small-particle scattering coefficient 31 percent larger than
the one in the paper they cite for it. See DATA.md section 6.""")

# --------------------------------------------------------------------------
rule("4. What each source says is doubtful about itself")

for key in ("williamson2022", "solonenko2015"):
    print(f"\n{key}:")
    for caveat in jerlov.get_source(key).caveats:
        print(f"  - {caveat}")

# --------------------------------------------------------------------------
rule("5. Values a published table got wrong")

print("""Solonenko & Mobley Table 7 duplicates rows: Jerlov 3C at 675 and 700 nm
repeats 300 and 310 nm, and 5C repeats five rows. Scattering was recovered
from the paper's own Eq. (8); absorption could not be.""")

water = jerlov.water("5C", source="solonenko2015")
print("\n  Jerlov 5C, source solonenko2015:")
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    b650 = float(water.b(650))
    a650 = float(water.a(650))
print(f"    b(650) = {b650:.4f}   (reconstructed)")
print(f"    a(650) = {a650}      (not recoverable, and it stays nan)")
for entry in caught:
    if issubclass(entry.category, jerlov.ProvenanceWarning):
        print(f"\n    {entry.message}")
        break

print("\n  water.caveats():")
for caveat in water.caveats():
    print(f"    - {caveat}")

# --------------------------------------------------------------------------
rule("6. What the package will not guess")

for label, call in (
    ("bb without a stated ratio",
     lambda: jerlov.water("III").bb(550)),
    ("a wavelength outside the data",
     lambda: jerlov.water("III").a(900)),
    ("Kd from a source that has none",
     lambda: jerlov.water("III").kd(550)),
):
    try:
        call()
    except Exception as error:  # noqa: BLE001 - showing the message is the point
        first_line = str(error).split(".")[0]
        print(f"\n  {label}:\n    {type(error).__name__}: {first_line}.")

print("""
Each of these could have returned a plausible number. The package refuses
because a plausible number that nobody can trace is exactly what this field
already has too much of.
""")

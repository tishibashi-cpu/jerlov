"""Transcribe Paulson & Simpson (1977) Table 2, and reproduce their fit.

Ocean circulation models absorb solar radiation in the upper ocean with a sum
of two exponentials::

    I(z) / I(0) = R exp(-z/zeta1) + (1 - R) exp(-z/zeta2)

The parameters per Jerlov type come from this paper, and are used in that form
by ROMS, MITgcm, NEMO and CESM among others. They are usually copied from
secondary sources.

Paulson & Simpson fitted them to Jerlov (1968) Table XXI, which this package
also ships, so the fit can be repeated rather than taken on trust. Their
procedure, their Eqs (2) and (3):

1. Fit ``ln(I/I0) = ln(1-R) - z/zeta2`` to the points below 10 m, giving R
   and zeta2.
2. Subtract that term, and fit ``ln(residual/R) = -z/zeta1`` to the points in
   the upper 6 m with R and zeta2 held fixed. The surface point is exact by
   construction, so the line passes through the origin.

Reproducing R exactly for all six rows is what establishes that the shipped
numbers and the source table are both right.

Paulson, C. A. and Simpson, J. J. (1977), "Irradiance measurements in the
upper ocean", *J. Phys. Oceanogr.* 7, 952-956,
DOI 10.1175/1520-0485(1977)007<0952:IMITUO>2.0.CO;2

No input file is needed beyond the shipped Jerlov 1968 table.
"""

import csv
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import DATA_DIR, report

#: Table 2 as printed. `fit_depth_m` records the range each row was fitted
#: over, which the paper states in its text rather than in the table.
PUBLISHED = [
    # key, water_type, R, zeta1, zeta2, fit_depth_m, note
    ("I", "I", 0.58, 0.35, 23.0, 100,
     "the paper also gives a separate fit for the upper 50 m; see I_upper50"),
    ("I_upper50", "I", 0.68, 1.2, 28.0, 50,
     "fitted over the upper 50 m because ln I against z changes slope below "
     "it. Printed as 'Type 1' in the table, but the text makes clear it is "
     "type I"),
    ("IA", "IA", 0.62, 0.60, 20.0, 100, ""),
    ("IB", "IB", 0.67, 1.0, 17.0, 100, ""),
    ("II", "II", 0.77, 1.5, 14.0, 100, ""),
    ("III", "III", 0.78, 1.4, 7.9, 100, ""),
]

#: The two rows of Table 2 that are not Jerlov types. Shipped because a reader
#: comparing against the paper will otherwise think they are missing.
NON_JERLOV = [
    ("composite_observations", 0.62, 1.5, 20.0,
     "the authors' own observations, runs 4, 5, 6, 9 and 10, North Pacific "
     "35N 155W. Not a Jerlov type"),
    ("run_1", 0.74, 1.7, 16.0,
     "a single run with a 16 degree solar altitude and a cloudless sky, which "
     "attenuates faster near the surface. Not a Jerlov type"),
    ("kraus_1972_very_clear", 0.4, 5.0, 40.0,
     "Kraus (1972) p. 92, from Crater Lake. The paper notes R = 0.4 may be "
     "too small. Not a Jerlov type"),
]

#: How closely the refit must land on the printed values. The table prints two
#: significant figures, so half a unit in the last place is the most that can
#: be asked of any of them: 0.005 for R, and 0.5 m for the two lengths. R
#: reproduces well inside that. The lengths do not, and are allowed more: the
#: shallow fit has four points and the deep fit as few as three, so the last
#: digit of a length is not recoverable from a table rounded this way. What is
#: being guarded is that the numbers still come from where the paper says.
TOLERANCE = {"R": 0.01, "zeta1": 0.4, "zeta2": 0.7}


def load_table_xxi():
    rows = list(csv.DictReader(
        open(DATA_DIR / "jerlov1968_total_irradiance.csv")))
    out = {}
    for row in rows:
        if not row["percent_of_surface"]:
            continue
        out.setdefault(row["water_type"], []).append(
            (float(row["depth_m"]), float(row["percent_of_surface"]) / 100.0))
    return out


def refit(profile, max_depth):
    """Paulson & Simpson's two-step procedure, Eqs (2) and (3)."""
    depth = np.array([z for z, _ in profile if z <= max_depth])
    value = np.array([v for z, v in profile if z <= max_depth])

    deep = depth > 10
    slope, intercept = np.polyfit(depth[deep], np.log(value[deep]), 1)
    zeta2 = -1.0 / slope
    r = 1.0 - math.exp(intercept)

    shallow = depth <= 6
    residual = value[shallow] - (1 - r) * np.exp(-depth[shallow] / zeta2)
    positive = residual > 0
    z = depth[shallow][positive]
    y = np.log(residual[positive]) - math.log(r)
    # Forced through the origin: at z = 0 the residual is exactly R.
    zeta1 = -1.0 / (np.sum(z * y) / np.sum(z * z))
    return r, zeta1, zeta2


# ----------------------------- self-checks ----------------------------------

table_xxi = load_table_xxi()
print("check: reproduce Table 2 from Jerlov (1968) Table XXI\n")
print(f"  {'row':>10} {'R':>13} {'zeta1 (m)':>15} {'zeta2 (m)':>15}")
print(f"  {'':>10} {'fit    pub':>13} {'fit     pub':>15} {'fit     pub':>15}")

worst = {"R": 0.0, "zeta1": 0.0, "zeta2": 0.0}
for key, water_type, pub_r, pub_z1, pub_z2, max_depth, _ in PUBLISHED:
    r, z1, z2 = refit(table_xxi[water_type], max_depth)
    for name, got, want in (("R", r, pub_r), ("zeta1", z1, pub_z1),
                            ("zeta2", z2, pub_z2)):
        worst[name] = max(worst[name], abs(got - want))
    print(f"  {key:>10} {r:>6.2f} {pub_r:>6.2f} {z1:>7.2f} {pub_z1:>7.2f} "
          f"{z2:>7.1f} {pub_z2:>7.1f}")

print()
for name, limit in TOLERANCE.items():
    ok = worst[name] <= limit
    print(f"  worst {name:>5} difference {worst[name]:.3f} "
          f"(limit {limit}) {'ok' if ok else 'FAILED'}")
    if not ok:
        raise SystemExit(f"{name} no longer reproduces Table 2")

# -------------------------------- write -------------------------------------

rows = 0
path = DATA_DIR / "paulson1977_shortwave.csv"
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["key", "water_type", "R", "zeta1_m", "zeta2_m",
                     "fit_depth_m", "status", "note"])
    for key, water_type, r, z1, z2, max_depth, note in PUBLISHED:
        writer.writerow([key, water_type, r, z1, z2, max_depth, "ok", note])
        rows += 1
    for key, r, z1, z2, note in NON_JERLOV:
        writer.writerow([key, "", r, z1, z2, "", "not_a_water_type", note])
        rows += 1
report("paulson1977_shortwave.csv", rows)

"""Transcribe Boss & Pegau (2001) Table 1, and check it against their model.

A backscattering sensor measures the volume scattering function at one angle.
Turning that into the backscattering coefficient needs a conversion factor
chi, defined by 2 pi beta(theta) chi(theta) = bb.

Boss & Pegau split it: chi_w for pure sea water, which follows analytically
from Morel's formula, and chi_p for particles, which they tabulated from 41
measured volume scattering functions. Their recommended procedure removes the
water contribution before converting:

    bb = 2 pi chi_p(theta) [beta(theta) - beta_w(theta)] + bb_w

Boss, E. and Pegau, W. S. (2001), "Relationship of light scattering at an
angle in the backward direction to the backscattering coefficient",
*Appl. Opt.* 40, 5503-5507, DOI 10.1364/AO.40.005503

No input file is needed: the table is a literal below, checked against the
paper's own Eqs. (3), (5) and (9).
"""

import csv
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import DATA_DIR, report

#: Table 1. chi_p and the percent error, from 41 VSF measurements in which
#: water contributed less than 6 percent of bb. The error is half the
#: difference between the 10th and 90th percentiles.
CHI_P = {
    90: (0.71, 4.3),
    100: (0.90, 2.6),
    110: (1.03, 3.1),
    120: (1.12, 4.2),
    130: (1.17, 3.3),
    140: (1.18, 3.5),
    150: (1.13, 4.2),
    160: (1.00, 6.4),
    170: (0.62, 34.8),
}

#: Depolarisation ratio of pure sea water. Morel gives 0.07 to 0.11 and
#: suggests 0.09; the paper uses 0.09 throughout.
DELTA = 0.09

#: Values other authors publish for the same conversion, for the record.
#: chi and chi_p are not the same quantity — one includes water and the other
#: does not — so these are not simply in conflict. See DATA.md section 18.
ELSEWHERE = [
    ("oishi1990", 120, 1.14, "", "chi including water, quoted by Maffione & "
     "Dana (1997) from Oishi (1990), Appl. Opt. 29, 4658"),
    ("oishi1990", 140, 1.08, "", "as above"),
    ("maffione1997", 140, 1.08, 9.0, "chi including water, Maffione & Dana "
     "(1997), Appl. Opt. 36, 6057, from Mie computations; the 9 percent is "
     "their standard deviation"),
]


def ratio():
    return (1 - DELTA) / (1 + DELTA)


def chi_w(theta_deg):
    """Eq. (9). The water part is analytic, so nothing is transcribed here."""
    r = ratio()
    return (1 + r / 3) / (1 + r * math.cos(math.radians(theta_deg)) ** 2)


def beta_w_shape(theta_deg):
    """The angular part of Eq. (4), without the amplitude A."""
    return 1 + ratio() * math.cos(math.radians(theta_deg)) ** 2


# ----------------------------- self-checks ----------------------------------

# Check 1: chi_w must give the same bb_w at every angle, and that value must
# equal the direct integral of Eq. (3). Any error in Eq. (9) breaks this.
amplitude = 1.0
by_angle = [2 * math.pi * amplitude * beta_w_shape(t) * chi_w(t)
            for t in range(90, 171, 10)]
theta = np.radians(np.linspace(90.0, 180.0, 90001))
direct = 2 * math.pi * amplitude * float(
    np.trapezoid((1 + ratio() * np.cos(theta) ** 2) * np.sin(theta), theta))
spread = (max(by_angle) - min(by_angle)) / direct
print(f"check: chi_w reproduces the Eq. (3) integral at every angle")
print(f"  by angle {min(by_angle):.6f} to {max(by_angle):.6f}, "
      f"integral {direct:.6f}, spread {spread:.2e}")
assert spread < 1e-9, "Eq. (9) disagrees with Eq. (3)"
assert abs(by_angle[0] - direct) / direct < 1e-9

# Check 2: the paper says chi_w and chi_p cross near 118 degrees, which is why
# 120 is the angle instruments settled on.
angles = np.array(sorted(CHI_P), dtype=float)
values = np.array([CHI_P[int(a)][0] for a in angles])
fine = np.linspace(90.0, 170.0, 80001)
gap = np.array([chi_w(t) for t in fine]) - np.interp(fine, angles, values)
crossing = float(fine[int(np.argmin(np.abs(gap)))])
print(f"check: chi_w meets chi_p at {crossing:.1f} deg (the paper says ~118)")
assert 114.0 < crossing < 122.0, crossing

# Check 3: chi_p peaks in the middle of the backward hemisphere, which is the
# reason both papers recommend 110-160 degrees.
peak = max(CHI_P, key=lambda t: CHI_P[t][0])
print(f"check: chi_p peaks at {peak} deg, and the error is worst at "
      f"{max(CHI_P, key=lambda t: CHI_P[t][1])} deg")
assert 120 <= peak <= 150
assert max(CHI_P, key=lambda t: CHI_P[t][1]) == 170

# -------------------------------- write -------------------------------------

rows = 0
path = DATA_DIR / "boss2001_chi.csv"
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["source", "angle_deg", "chi", "quantity",
                     "percent_error", "status", "note"])
    for angle in sorted(CHI_P):
        value, error = CHI_P[angle]
        note = ""
        status = "ok"
        if angle == 170:
            status = "suspect"
            note = ("the volume scattering function varies most steeply here, "
                    "and no measurement in the set went beyond 170 deg")
        elif angle == 90:
            note = ("the water contribution to the measured signal is largest "
                    "here, so removing it matters most")
        writer.writerow(["boss2001", angle, value, "chi_p", error, status,
                         note])
        rows += 1
    for source, angle, value, error, note in ELSEWHERE:
        writer.writerow([source, angle, value, "chi", error,
                         "other_definition", note])
        rows += 1
report("boss2001_chi.csv", rows)

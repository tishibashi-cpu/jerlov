"""Transcribe Jerlov's classification in terms of quanta irradiance.

Jerlov arranged measured profiles of quanta irradiance, 350-700 nm, from
fourteen regions by optical water type, and tabulated the depths at which
30, 10, 3 and 1 percent of the surface value remain (Table 2), the
percentage at depth (Table 3), and the attenuation coefficients between
levels (Table 4) and between depths (Table 5). They are measurements, not a
model, which makes them the one published check on `par_profile` and
`descend` from the other side.

No input file is needed: the tables are literals below, transcribed from the
publisher's scan and checked against it image by image, since its text layer
reads decimal points as hyphens ("17-5" for 17.5). The checks below then
recompute Tables 4 and 5 from Tables 2 and 3, and Table 2's normalised
column from its depths, allowing for the rounding of every printed value.
Eight values do not follow, one of them by a wide margin; they are kept as
printed and marked suspect, since the paper does not say which table is
right. See DATA.md section 22.

The coastal types are printed as "1" and "3", the notation of the time;
they are Jerlov's coastal types 1 and 3, written 1C and 3C here as
everywhere else in the package.

Jerlov, N. G., "Classification of sea water in terms of quanta irradiance",
J. Cons. int. Explor. Mer 37(3), 281-287. The pages carry no year; the
latest observations used are from June 1976. Tables 2 and 4 p. 284 and
286, Tables 3 and 5 p. 285 and 286.
"""

import csv
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import DATA_DIR, report

TYPES = ["I", "IA", "IB", "II", "III", "1C", "3C"]

#: Table 2: depth (m) at which 30, 10, 3 and 1 percent of surface quanta
#: remain, and the same normalised by the 10 percent depth.
PERCENT_LEVELS = [30, 10, 3, 1]
LEVEL_DEPTHS = {
    "I":   [19, 49, 79, 103],
    "IA":  [16.5, 41, 66, 87],
    "IB":  [14, 33, 54, 70],
    "II":  [10.5, 24, 39, 52],
    "III": [6.5, 14, 23, 31],
    "1C":  [5.3, 12, 20, 27],
    "3C":  [3.7, 8.5, 14, 19],
}
NORMALIZED = {          # z(30)/z(10), z(3)/z(10), z(1)/z(10)
    "I":   [0.39, 1.65, 2.15],
    "IA":  [0.40, 1.66, 2.12],
    "IB":  [0.42, 1.63, 2.12],
    "II":  [0.44, 1.63, 2.17],
    "III": [0.46, 1.64, 2.21],
    "1C":  [0.44, 1.67, 2.25],
    "3C":  [0.44, 1.65, 2.23],
}

#: Table 3: percent of surface quanta at depth. None where blank.
PROFILE_DEPTHS = [0, 2, 5, 10, 15, 20, 30, 40, 50, 60, 70, 80, 90, 100]
PROFILE = {
    "I":   [100, 79, 64, 46, 35.5, 29, 20, 13.7, 9.5, 6.5, 4.3, 2.9,
            1.85, 1.14],
    "IA":  [100, 77, 59, 42, 32, 25.5, 16.4, 10.3, 6.6, 4.1, 2.5, 1.47,
            None, None],
    "IB":  [100, 75, 54, 38, 28, 21, 12.0, 6.7, 3.8, 2.0, 1.01, None,
            None, None],
    "II":  [100, 70, 48, 32, 21, 14.2, 6.4, 2.8, 1.23, None, None, None,
            None, None],
    "III": [100, 63, 38, 17.5, 8.5, 4.6, 1.22, None, None, None, None, None,
            None, None],
    "1C":  [100, 54, 30, 13.3, 6.0, 3.0, 0.65, None, None, None, None, None,
            None, None],
    "3C":  [100, 44, 21, 7.0, 2.3, 0.73, None, None, None, None, None, None,
            None, None],
}

#: Table 4: Kd (1/m) between the percent levels.
INTERVALS = ["100-30", "30-10", "10-3", "3-1"]
LEVEL_KD = {
    "I":   [0.063, 0.037, 0.040, 0.046],
    "IA":  [0.073, 0.043, 0.048, 0.052],
    "IB":  [0.086, 0.053, 0.057, 0.068],
    "II":  [0.114, 0.082, 0.080, 0.084],
    "III": [0.185, 0.146, 0.134, 0.137],
    "1C":  [0.227, 0.164, 0.150, 0.157],
    "3C":  [0.325, 0.229, 0.218, 0.220],
}

#: Table 5: Kd (1/m) for quanta between depths. None where blank.
LAYERS = [(0, 2), (2, 5), (5, 10), (10, 15), (15, 20), (20, 30), (30, 40),
          (40, 50), (50, 60), (60, 70), (70, 80), (80, 90), (90, 100)]
LAYER_KD = {
    "I":   [0.118, 0.073, 0.065, 0.052, 0.040, 0.039, 0.039, 0.037, 0.038,
            0.040, 0.040, 0.045, 0.048],
    "IA":  [0.130, 0.089, 0.068, 0.054, 0.042, 0.046, 0.046, 0.045, 0.048,
            0.049, 0.053, None, None],
    "IB":  [0.144, 0.107, 0.071, 0.061, 0.056, 0.057, 0.058, 0.059, 0.064,
            0.069, None, None, None],
    "II":  [0.178, 0.126, 0.099, 0.084, 0.078, 0.080, 0.082, 0.082, None,
            None, None, None, None],
    "III": [0.230, 0.169, 0.155, 0.144, 0.123, 0.134, None, None, None,
            None, None, None, None],
    "1C":  [0.310, 0.196, 0.163, 0.154, 0.140, 0.153, None, None, None,
            None, None, None, None],
    "3C":  [0.41, 0.25, 0.22, 0.22, 0.23, None, None, None, None, None,
            None, None, None],
}

#: Printed values that do not follow from the table they are derived from,
#: even allowing for the rounding of both. Kept as printed and marked
#: suspect: the paper does not say which is right. DATA.md section 22.
NORMALIZED_NOT_FROM_DEPTHS = {("I", 3), ("I", 1), ("IA", 3)}
LEVEL_KD_NOT_FROM_DEPTHS = {("IA", "30-10"), ("IB", "30-10")}
LAYER_KD_NOT_FROM_PROFILE = {("IA", 20, 30), ("II", 5, 10), ("1C", 10, 15)}


def half_unit(value) -> float:
    """Half the last printed digit: the rounding a printed value carries."""
    text = f"{value}"
    places = len(text.split(".")[1]) if "." in text else 0
    return 0.5 * 10 ** -places


def kd_range(p1, p2, z1, z2, dp1, dp2, dz1, dz2):
    """ln(p1/p2)/(z2 - z1) over every rounding of the four inputs."""
    values = [math.log((p1 + a) / (p2 + b)) / ((z2 + d) - (z1 + c))
              for a in (-dp1, dp1) for b in (-dp2, dp2)
              for c in (-dz1, dz1) for d in (-dz2, dz2)]
    return min(values), max(values)


def overlaps(printed, low, high) -> bool:
    h = half_unit(printed)
    return printed + h >= low and printed - h <= high


# ----------------------------- self-checks ----------------------------------

# Table 4 is ln(p1/p2) over the distance between Table 2's levels.
off = set()
for t in TYPES:
    z = [0.0] + LEVEL_DEPTHS[t]
    p = [100.0] + PERCENT_LEVELS
    for i, printed in enumerate(LEVEL_KD[t]):
        low, high = kd_range(p[i], p[i + 1], z[i], z[i + 1], 0, 0,
                             0 if i == 0 else half_unit(z[i]),
                             half_unit(z[i + 1]))
        if not overlaps(printed, low, high):
            off.add((t, INTERVALS[i]))
assert off == LEVEL_KD_NOT_FROM_DEPTHS, off
print(f"check: Table 4 follows from Table 2 within rounding except "
      f"{sorted(off)}")

# Table 5 is ln(p1/p2) over Table 3's depths.
off, checked = set(), 0
for t in TYPES:
    for (top, bottom), printed in zip(LAYERS, LAYER_KD[t]):
        if printed is None:
            continue
        p1 = PROFILE[t][PROFILE_DEPTHS.index(top)]
        p2 = PROFILE[t][PROFILE_DEPTHS.index(bottom)]
        low, high = kd_range(p1, p2, top, bottom,
                             0 if top == 0 else half_unit(p1),
                             half_unit(p2), 0, 0)
        checked += 1
        if not overlaps(printed, low, high):
            off.add((t, top, bottom))
assert off == LAYER_KD_NOT_FROM_PROFILE, off
print(f"check: Table 5 follows from Table 3 within rounding at "
      f"{checked - len(off)} of {checked} layers, except {sorted(off)}")

# Table 2's normalised values, against its own depths.
off = set()
for t in TYPES:
    z10 = LEVEL_DEPTHS[t][1]
    for level, depth, printed in zip((30, 3, 1),
                                     (LEVEL_DEPTHS[t][0], LEVEL_DEPTHS[t][2],
                                      LEVEL_DEPTHS[t][3]),
                                     NORMALIZED[t]):
        ratios = [(depth + a) / (z10 + b)
                  for a in (-half_unit(depth), half_unit(depth))
                  for b in (-half_unit(z10), half_unit(z10))]
        if not overlaps(printed, min(ratios), max(ratios)):
            off.add((t, level))
assert off == NORMALIZED_NOT_FROM_DEPTHS, off
print(f"check: Table 2's normalised values follow from its depths except "
      f"{sorted(off)}")

# Tables 2 and 3 agree: interpolating Table 3 in log percent puts each
# level within 2.5 m of Table 2.
worst = 0.0
for t in TYPES:
    zs = [d for d, v in zip(PROFILE_DEPTHS, PROFILE[t]) if v is not None]
    logs = [math.log(v) for v in PROFILE[t] if v is not None]
    for level, printed in zip(PERCENT_LEVELS, LEVEL_DEPTHS[t]):
        target = math.log(level)
        for i in range(len(zs) - 1):
            if logs[i] >= target >= logs[i + 1]:
                f = (logs[i] - target) / (logs[i] - logs[i + 1])
                z = zs[i] + f * (zs[i + 1] - zs[i])
                worst = max(worst, abs(z - printed))
                assert abs(z - printed) <= 2.5, (t, level, z, printed)
                break
print(f"check: Table 3 puts Table 2's levels within {worst:.1f} m")

# -------------------------------- write -------------------------------------

def note_for(water_type: str) -> str:
    if water_type.endswith("C"):
        return (f"printed as coastal type '{water_type[0]}'; written "
                f"{water_type} here as elsewhere in this package")
    return ""


def flagged(condition: bool, why: str, water_type: str):
    return ("suspect", why) if condition else ("ok", note_for(water_type))


NOT_FROM = ("does not follow from {}, even allowing for rounding "
            "(DATA.md section 22)")

# One row per printed value. Depths are the interval a value applies to
# (top equal to bottom for a single depth); percents likewise.
HEADER = ["table", "water_type", "depth_top_m", "depth_bottom_m",
          "percent_top", "percent_bottom", "value", "unit", "status", "note"]
rows = 0
path = DATA_DIR / "jerlov1977_quanta.csv"
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(HEADER)
    for t in TYPES:
        for level, depth in zip(PERCENT_LEVELS, LEVEL_DEPTHS[t]):
            writer.writerow(["2", t, depth, depth, level, level, depth, "m",
                             "ok", note_for(t)])
            rows += 1
        for level, value in zip((30, 3, 1), NORMALIZED[t]):
            status, note = flagged((t, level) in NORMALIZED_NOT_FROM_DEPTHS,
                                   NOT_FROM.format("the depths in Table 2"), t)
            writer.writerow(["2n", t, "", "", level, level, value,
                             "z/z(10)", status, note])
            rows += 1
        for depth, value in zip(PROFILE_DEPTHS, PROFILE[t]):
            if value is None:
                continue
            writer.writerow(["3", t, depth, depth, "", "", value, "percent",
                             "ok", note_for(t)])
            rows += 1
        for interval, value in zip(INTERVALS, LEVEL_KD[t]):
            upper, lower = (int(x) for x in interval.split("-"))
            top = (0 if upper == 100
                   else LEVEL_DEPTHS[t][PERCENT_LEVELS.index(upper)])
            bottom = LEVEL_DEPTHS[t][PERCENT_LEVELS.index(lower)]
            status, note = flagged((t, interval) in LEVEL_KD_NOT_FROM_DEPTHS,
                                   NOT_FROM.format("the depths in Table 2"), t)
            writer.writerow(["4", t, top, bottom, upper, lower, value, "1/m",
                             status, note])
            rows += 1
        for (top, bottom), value in zip(LAYERS, LAYER_KD[t]):
            if value is None:
                continue
            status, note = flagged(
                (t, top, bottom) in LAYER_KD_NOT_FROM_PROFILE,
                NOT_FROM.format("the percentages in Table 3"), t)
            writer.writerow(["5", t, top, bottom, "", "", value, "1/m",
                             status, note])
            rows += 1
report("jerlov1977_quanta.csv", rows)

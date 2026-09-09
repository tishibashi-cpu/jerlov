"""Transcribe Jerlov (1968) Table XX and Table XXI.

Jerlov's classification was revised in 1976, and the two editions differ. This
matters because Solonenko & Mobley (2015) cite the 1968 edition for their Kd0
reference column, so checking their table against the 1976 one — which the
Dstl dataset carries — makes them look wrong when they are not. See DATA.md
section 2.

Table XX gives irradiance transmittance per metre, from which Kd follows as
-ln(T). Table XXI gives the fraction of total irradiance (300-2500 nm)
surviving to depth, and is the source Paulson & Simpson (1977) fitted; it is
used by `build_paulson1977.py` and is written here so that fit can be checked
against something with a provenance of its own.

No input file is needed: both tables are literals below, transcribed from
scans and checked against Solonenko & Mobley's published Kd0 column.

Jerlov, N. G. (1968), *Optical Oceanography*, Elsevier Oceanography Series
Vol. 5, Table XX p. 120 and Table XXI p. 121. No DOI exists.
"""

import csv
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import DATA_DIR, report

WAVELENGTHS = [310, 350, 375, 400, 425, 450, 475, 500,
               525, 550, 575, 600, 625, 650, 675, 700]

#: Table XX, part 1: irradiance transmittance in percent per metre.
TRANSMITTANCE = {
    "I":   [86, 94, 96.3, 97.2, 97.8, 98.1, 98.2, 97.2,
            96.1, 94.2, 92, 85, 74, 70, 66, 59],
    "IA":  [83, 92.5, 95.1, 96.3, 97.1, 97.4, 97.5, 96.6,
            95.5, 93.6, 91, 84, 73.5, 69.5, 65.5, 58.5],
    "IB":  [80, 90.5, 94, 95.5, 96.4, 96.7, 96.8, 96.0,
            95.0, 93.0, 90.5, 83, 73, 69, 65, 58.0],
    "II":  [69, 84, 89, 92, 93.5, 94, 94, 93.5,
            92.5, 90.5, 87.5, 80, 71, 67.5, 63.5, 56],
    "III": [50, 71, 79, 84, 87, 88.5, 89, 89,
            88.5, 86.5, 82.5, 75, 68, 65, 61, 54],
    "1C":  [16, 32, 54, 69, 79, 84, 87.5, 88.8,
            88.5, 86.5, 82.5, 75, 68, 65, 61, 54],
    "3C":  [9, 19, 34, 53, 66, 75, 80, 82,
            82, 81, 78, 71, 65, 62, 57, 51],
    "5C":  [3, 10, 21, 36, 50, 60, 67, 71,
            73, 72, 70, 67, 62, 58, 52, 45],
    "7C":  [None, 5.0, 12, 22, 32, 42, 50, 56,
            61, 63, 63, 62, 58, 53, 46, 40],
    "9C":  [None, 1.5, 4.7, 9, 15, 21, 29, 37,
            46, 53, 56, 55, 52, 47, 40, 33],
}

#: Table XXI: percent of total irradiance, 300-2500 nm, from sun and sky.
#: Solar altitude 90 degrees for oceanic types, 45 degrees for coastal.
DEPTHS_M = [0, 1, 2, 5, 10, 20, 25, 50, 75, 100, 150, 200]
TOTAL_IRRADIANCE = {
    "I":   [100, 44.5, 38.5, 30.2, 22.2, None, 13.2, 5.3, 1.68, 0.53,
            0.056, 0.0062],
    "IA":  [100, 44.1, 37.9, 29.0, 20.8, None, 11.1, 3.3, 0.95, 0.28,
            None, None],
    "IB":  [100, 42.9, 36.0, 25.8, 16.9, None, 7.7, 1.8, 0.42, 0.10,
            None, None],
    "II":  [100, 42.0, 34.7, 23.4, 14.2, None, 4.2, 0.70, 0.124, 0.0228,
            0.00080, None],
    "III": [100, 39.4, 30.3, 16.8, 7.6, None, 0.97, 0.041, 0.0018, None,
            None, None],
    "1C":  [100, 36.9, 27.1, 14.2, 5.9, 1.3, None, 0.022, None, None,
            None, None],
    "3C":  [100, 33.0, 22.5, 9.3, 2.7, 0.29, None, None, None, None,
            None, None],
    "5C":  [100, 27.8, 16.4, 4.6, 0.69, 0.020, None, None, None, None,
            None, None],
    "7C":  [100, 22.6, 11.3, 2.1, 0.17, None, None, None, None, None,
            None, None],
    "9C":  [100, 17.6, 7.5, 1.0, 0.052, None, None, None, None, None,
            None, None],
}

#: Wavelengths at which coastal type 1C repeats oceanic type III exactly.
#: Present in the original; see DATA.md section 5.
DUPLICATED_1C = [525, 550, 575, 600, 625, 650, 675, 700]


def kd(transmittance_percent):
    return -math.log(transmittance_percent / 100.0)


# ----------------------------- self-checks ----------------------------------

same = [w for i, w in enumerate(WAVELENGTHS)
        if TRANSMITTANCE["1C"][i] == TRANSMITTANCE["III"][i]]
print(f"check: coastal 1C repeats oceanic III at {len(same)} wavelengths "
      f"{same}")
assert same == DUPLICATED_1C, f"the duplication changed: {same}"

# Every profile must decrease with depth.
for water_type, row in TOTAL_IRRADIANCE.items():
    seen = [v for v in row if v is not None]
    assert seen == sorted(seen, reverse=True), f"{water_type} is not monotonic"
print(f"check: all {len(TOTAL_IRRADIANCE)} depth profiles decrease with depth")

# Turbidity must order the types at 475 nm.
order = [TRANSMITTANCE[t][WAVELENGTHS.index(475)] for t in
         ("I", "IA", "IB", "II", "III", "1C", "3C", "5C", "7C", "9C")]
assert order == sorted(order, reverse=True), f"types out of order: {order}"
print("check: transmittance at 475 nm decreases from I to 9C")

# -------------------------------- write -------------------------------------

rows = 0
path = DATA_DIR / "jerlov1968_kd.csv"
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["water_type", "wavelength_nm", "Kd_downwelling_per_m",
                     "transmittance_percent_per_m", "status", "note"])
    for water_type, row in TRANSMITTANCE.items():
        for wavelength, value in zip(WAVELENGTHS, row):
            if value is None:
                writer.writerow([water_type, wavelength, "", "", "missing",
                                 "blank in Table XX"])
            else:
                note = ""
                if water_type == "1C" and wavelength in DUPLICATED_1C:
                    note = ("identical to oceanic III at this wavelength in "
                            "the original table; see DATA.md section 5")
                writer.writerow([water_type, wavelength,
                                 f"{kd(value):.4f}", value, "ok", note])
            rows += 1
report("jerlov1968_kd.csv", rows)

rows = 0
path = DATA_DIR / "jerlov1968_total_irradiance.csv"
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["water_type", "depth_m", "percent_of_surface",
                     "status", "note"])
    for water_type, row in TOTAL_IRRADIANCE.items():
        for depth, value in zip(DEPTHS_M, row):
            if value is None:
                writer.writerow([water_type, depth, "", "missing",
                                 "blank in Table XXI"])
            else:
                writer.writerow([water_type, depth, value, "ok", ""])
            rows += 1
report("jerlov1968_total_irradiance.csv", rows)

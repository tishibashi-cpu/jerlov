"""Transcribe Table 1 of Smart (2007).

Least squares fits of (b - bw) / (c - cw) for six datasets: the US
continental shelf, Chesapeake Bay, the Sea of Japan and the Yellow Sea.
A transmissometer measures c, so this is the usual route to b.

No input file is needed; the values are literals below.
"""

import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import DATA_DIR, report

WAVELENGTHS = [412, 440, 488, 510, 532, 555, 630, 650, 676, 715]
AVERAGE = [0.716, 0.759, 0.840, 0.861, 0.893, 0.904, 0.890, 0.921, 0.920, 0.945]
MINIMUM = [0.598, 0.648, 0.750, 0.780, 0.798, 0.822, 0.828, 0.830, 0.833, 0.837]
MAXIMUM = [0.840, 0.872, 0.914, 0.927, 0.937, 0.949, 0.959, 0.978, 0.984, 0.999]

NOTES = {
    "average": (
        "mean of the least squares fits for six datasets; accurate to about "
        "10 percent. Ratios are lower than this in CDOM-rich water, "
        "particularly below 488 nm"
    ),
    "min": "closer for clear water",
    "max": "closer for turbid water (c at 488 nm above 1.0 1/m)",
}

# The bounds must bracket the average at every wavelength.
for i, nm in enumerate(WAVELENGTHS):
    assert MINIMUM[i] <= AVERAGE[i] <= MAXIMUM[i], f"bounds inverted at {nm} nm"
print(f"check: bounds bracket the average at all {len(WAVELENGTHS)} wavelengths")

rows = 0
path = DATA_DIR / "smart2007_b_from_c.csv"
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(
        ["wavelength_nm", "statistic", "b_minus_bw_over_c_minus_cw", "note"]
    )
    for i, nm in enumerate(WAVELENGTHS):
        for statistic, values in (
            ("average", AVERAGE), ("min", MINIMUM), ("max", MAXIMUM)
        ):
            writer.writerow([nm, statistic, values[i], NOTES[statistic]])
            rows += 1

report("smart2007_b_from_c.csv", rows)

"""Read Gernez & Antoine's (2009) irradiance fluctuations off their Figure 8a.

At the BOUSSOLE buoy in the Ligurian Sea, Gernez and Antoine recorded the
downwelling irradiance at 510 nm, 6 times a second for a minute every 15
minutes, at a nominal depth between 2.7 and 3.7 m. Figure 8a gives, for
clear skies, the mean coefficient of variation (standard deviation over
mean) of those minutes and its standard deviation, and the mean period of
the strongest fluctuation, Tmax, against the sun's zenith angle. The paper
prints them only in the figure.

The figure is a raster image in the PDF, 877 by 821 pixels at 150 pixels
per inch (page 9 of 15). The numbers below are pixel rows in that image,
read by finding dark pixels (grey level below 150 of 255) and checked on
the image by eye; the axes are calibrated on the tick marks.

- CV: each vertical solid bar is the mean plus and minus one standard
  deviation, so its midpoint is the mean, and the circle drawn there was
  found within a pixel of it at every angle. The rows are the first and
  last dark pixel of the bar. One pixel is 0.115 percent of CV.
- Tmax: the value is the centre of the square marker, between the top
  and bottom of its vertical sides, which are 7 or 8 pixels long. Where
  only one side could be told apart from the dashed bar, the value is
  read to two pixels instead of one. One pixel is 0.013 s. The dashed
  bars' ends fall between dashes and cannot be placed closer than a
  dash, so the standard deviation of Tmax is not read.

No input file is needed. DATA.md section 25.

Gernez, P. and Antoine, D. (2009), "Field characterization of
wave-induced underwater light field fluctuations", J. Geophys. Res. 114,
C06025, doi:10.1029/2008JC005059. Figure 8a, p. 9.
"""

import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import DATA_DIR, report


def calibrate(positions, values):
    n = len(positions)
    mx, my = sum(positions) / n, sum(values) / n
    slope = (sum((p - mx) * (v - my) for p, v in zip(positions, values))
             / sum((p - mx) ** 2 for p in positions))
    line = lambda p: my + slope * (p - mx)                  # noqa: E731
    return line, max(abs(line(p) - v) for p, v in zip(positions, values))


# Tick marks, as pixel column (x) or row (y) of their centre.
ANGLE_TICKS = ([79.0, 120.0, 160.5, 201.0, 242.0, 283.0, 324.0, 364.5],
               [20, 30, 40, 50, 60, 70, 80, 90])
CV_TICKS = ([360.5, 317.0, 273.0, 229.5, 186.0, 142.0, 98.5, 55.0],
            [0, 5, 10, 15, 20, 25, 30, 35])
TMAX_TICKS = ([360.5, 284.0, 208.0, 131.0, 55.0], [0, 1, 2, 3, 4])

# sun zenith: (column of the CV bar, its first and last dark row,
#              row of the square's centre, pixels the square is read to)
FIG8A = {
    20: (79, 116, 178, 282.5, 1),
    25: (99, 114, 180, 282.0, 1),
    30: (120, 124, 194, 277.0, 2),
    35: (140, 120, 186, 275.25, 1),
    40: (161, 133, 197, 270.5, 1),
    45: (181, 143, 205, 262.5, 2),
    50: (201, 160, 217, 260.5, 1),
    55: (222, 170, 227, 253.5, 2),
    60: (242, 185, 238, 241.5, 1),
    65: (263, 207, 258, 233.5, 1),
    70: (283, 233, 278, 198.5, 2),
    75: (303, 262, 303, 161.75, 1),
    80: (324, 284, 317, 145.5, 1),
    85: (344, 309, 328, 137.5, 1),
}
# At 65 degrees the square sits on the CV bar and hides rows 231-236 of
# it; the bar's two ends are clear of it.

angle_of, a_err = calibrate(*ANGLE_TICKS)
cv_of, c_err = calibrate(*CV_TICKS)
tmax_of, t_err = calibrate(*TMAX_TICKS)
assert a_err < 0.15 and c_err < 0.1 and t_err < 0.01, (a_err, c_err, t_err)
cv_per_px = abs(cv_of(1.0) - cv_of(0.0))
t_per_px = abs(tmax_of(1.0) - tmax_of(0.0))

rows = []
for zenith, (column, top, bottom, square, px) in FIG8A.items():
    # Each bar stands at its angle: within a degree.
    assert abs(angle_of(column) - zenith) < 1.0, zenith
    mean = cv_of(0.5 * (top + bottom))
    sd = 0.5 * (bottom - top) * cv_per_px
    rows.append((zenith, mean, sd, tmax_of(square), px * t_per_px))

cv = [r[1] for r in rows]
tmax = [r[3] for r in rows]
# "maximal at 25% when the sun is at its maximum elevation ... and
# decreases down to 5% when the sun approaches the horizon", and "an
# increase of Tmax from 1s to 3s" (p. 7).
assert round(cv[0]) in (24, 25) and round(cv[-1]) == 5, (cv[0], cv[-1])
assert round(tmax[0]) == 1 and round(tmax[-1]) == 3, (tmax[0], tmax[-1])
# Beyond 35 degrees CV only falls and Tmax only rises.
assert all(a > b for a, b in zip(cv[3:], cv[4:])), cv
assert all(a < b for a, b in zip(tmax[1:], tmax[2:])), tmax

NOTE = "read from the figure's pixels; DATA.md section 25"
path = DATA_DIR / "gernez2009_sun_zenith.csv"
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["sun_zenith_deg", "cv_percent", "cv_sd_percent",
                     "cv_reading_percent", "tmax_s", "tmax_reading_s",
                     "status", "note"])
    for zenith, mean, sd, t, t_unc in rows:
        writer.writerow([zenith, f"{mean:.2f}", f"{sd:.2f}",
                         f"{cv_per_px:.2f}", f"{t:.3f}", f"{t_unc:.3f}",
                         "read_from_figure", NOTE])
report(path.name, len(rows))

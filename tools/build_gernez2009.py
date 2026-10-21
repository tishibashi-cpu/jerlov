"""Read Gernez & Antoine's (2009) irradiance fluctuations off their Figure 8.

At the BOUSSOLE buoy in the Ligurian Sea, Gernez and Antoine recorded the
downwelling irradiance at 510 nm, 6 times a second for a minute every 15
minutes, at a nominal depth between 2.7 and 3.7 m. Figure 8 gives, for
clear skies, the median coefficient of variation (standard deviation over
mean) of those minutes and its standard deviation, and the median period
of the strongest fluctuation, Tmax, against (a) the sun's zenith angle,
(b) the wave height, (c) the square root of the wind speed and (d)
Kd(490). "The symbols are the median values, and the vertical bars are
the standard deviations", and "the Tmax curve is shifted to avoid that
error bars for CV and Tmax are superimposed" (caption of Figure 7, p. 8,
to which Figure 8's refers). The paper prints them only in the figure.

The figure is a raster image in the PDF, 877 by 821 pixels at 150 pixels
per inch (page 9 of 15). The numbers below are pixel rows in that image,
read by finding dark pixels (grey level below 150 of 255) and checked on
the image by eye; the axes are calibrated on the tick marks.

- CV: each vertical solid bar is drawn the same length either side of
  its circle, so where the bar's ends are clear its midpoint is the
  median; in panel a the circle was found within a pixel of it at every
  angle. The rows are the first and last dark pixel of the bar. One pixel
  is 0.115 percent of CV. In panels b to d, where a marker or the other
  series' bar crosses the bar, the circle is found by its outline; the
  bar is read only where its midpoint lies within 1.5 pixels of the
  circle, and otherwise the standard deviation is left out.
- Tmax: the value is the centre of the square marker, between the top
  and bottom of its vertical sides, which are 7 or 8 pixels long. Where
  only one side could be told apart from the dashed bar, the value is
  read to two pixels instead of one. One pixel is 0.013 s. The squares
  are shifted sideways for legibility, so each goes with the class of
  the circle it follows, not with where it is drawn. The dashed
  bars' ends fall between dashes and cannot be placed closer than a
  dash, so the standard deviation of Tmax is not read.

No input file is needed. DATA.md section 25.

Gernez, P. and Antoine, D. (2009), "Field characterization of
wave-induced underwater light field fluctuations", J. Geophys. Res. 114,
C06025, doi:10.1029/2008JC005059. Figure 8, p. 9.
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
    median = cv_of(0.5 * (top + bottom))
    sd = 0.5 * (bottom - top) * cv_per_px
    rows.append((zenith, median, sd, tmax_of(square), px * t_per_px))

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
    for zenith, median, sd, t, t_unc in rows:
        writer.writerow([zenith, f"{median:.2f}", f"{sd:.2f}",
                         f"{cv_per_px:.2f}", f"{t:.3f}", f"{t_unc:.3f}",
                         "read_from_figure", NOTE])
report(path.name, len(rows))


# -- Figure 8b-d ---------------------------------------------------------------
# The same axes as panel a for CV and Tmax, b on the upper row, c and d on
# the lower, whose ticks are the same 0-35 percent and 0-4 s 404 pixels
# further down.
LOWER_CV = ([764.5, 721.0, 677.0, 633.5, 590.0, 546.0, 502.5, 459.0],
            [0, 5, 10, 15, 20, 25, 30, 35])
LOWER_TMAX = ([764.5, 688.0, 612.0, 535.0, 459.0], [0, 1, 2, 3, 4])
X_TICKS = {
    "wave_height_m": ([529.0, 588.0, 647.0, 705.5, 764.0, 823.0],
                      [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]),
    "sqrt_wind": ([66.0, 140.5, 215.0, 290.0, 364.5], [0, 1, 2, 3, 4]),
    "kd490_per_m": ([527.0, 626.0, 724.5], [0.0, 0.05, 0.10]),
}
CLASSES = {"wave_height_m": 0.25, "sqrt_wind": 0.4, "kd490_per_m": 0.01}
FIRST = {"wave_height_m": 0.0, "sqrt_wind": 0.0, "kd490_per_m": 0.025}
# (column of the CV bar, its first and last dark row, row of the circle's
#  centre, row of the square's centre, pixels the square is read to).
# In panel d, from 0.085 on, the bars run under squares and are read
# from the first dark row above the square to the last below it.
FIG8BCD = {
    "wave_height_m": [
        (529, 169, 244, 206, 274, 1), (558, 152, 223, 188, 271, 1),
        (588, 144, 211, 177, 265, 1), (617, 156, 224, 190, 258, 1),
        (647, 161, 229, 195, 247, 1), (676, 175, 231, 203, 241, 1),
        (705, 180, 251, 215, 239, 2), (735, 181, 255, 218, 240, 1),
        (764, 188, 240, 213, 234, 1), (794, 212, 276, 244, 219, 1)],
    "sqrt_wind": [
        (66, 588, 659, 623, 668, 1), (96, 580, 662, 619, 659, 1),
        (126, 568, 647, 607, 670, 1), (156, 542, 611, 576, 679, 1),
        (185, 535, 596, 564, 677, 1), (215, 547, 603, 575, 666, 1),
        (245, 580, 627, 604, 650, 1), (275, 607, 649, 628, 642, 1),
        (305, 607, 653, 630, 632, 1), (335, 623, 657, 639, 617, 1)],
    "kd490_per_m": [
        (576, 526, 584, 555, 683, 1), (596, 543, 606, 575, 673, 1),
        (616, 555, 622, 588, 664, 1), (636, 571, 639, 605, 653, 1),
        (655, 580, 644, 614, 648, 1), (675, 584, 646, 619, 650, 1),
        (695, 595, 663, 629, 655, 1), (715, 598, 671, 634, 653, 1),
        (734, 614, 675, 645, 653, 1), (754, 623, 678, 650, 650, 1),
        (774, 632, 681, 656, 649, 1), (794, 631, 680, 656, 646, 1),
        (813, 622, 665, 643, 667, 2)],
}

upper_cv, upper_tmax = cv_of, tmax_of
lower_cv, lc_err = calibrate(*LOWER_CV)
lower_tmax, lt_err = calibrate(*LOWER_TMAX)
assert lc_err < 0.1 and lt_err < 0.01, (lc_err, lt_err)
conditions = []
for variable, points in FIG8BCD.items():
    x_of, x_err = calibrate(*X_TICKS[variable])
    assert x_err < 0.01 * X_TICKS[variable][1][-1], variable
    cv_line, t_line = ((upper_cv, upper_tmax) if variable == "wave_height_m"
                       else (lower_cv, lower_tmax))
    for k, (column, top, bottom, circle, square, px) in enumerate(points):
        x = FIRST[variable] + k * CLASSES[variable]
        # Each circle stands at its class, within a fifth of a class.
        assert abs(x_of(column) - x) < 0.2 * CLASSES[variable], (variable, k)
        mid = 0.5 * (top + bottom)
        if abs(mid - circle) <= 1.5:
            median, sd = cv_line(mid), 0.5 * (bottom - top) * cv_per_px
        else:
            median, sd = cv_line(circle), None
        conditions.append((variable, x, median, sd, t_line(square),
                           px * t_per_px))

by = {v: [r for r in conditions if r[0] == v] for v in FIG8BCD}
# "a maximum of about 22% when the wind speed is around 3 m s-1" (p. 7)
peak = max(by["sqrt_wind"], key=lambda r: r[2])
assert 2 <= peak[1] ** 2 <= 4 and 21 <= peak[2] <= 24, peak
# "minimal at 1.2s for wind speeds between 2 and 4 m s-1 and reaches a
# maximum of 1.6s as the wind speed increases up to 8 m s-1" (p. 8)
# The lowest Tmax read is in the class next below 2-4 m/s (DATA.md
# section 25); the check is that it is 1.1-1.25 s and below 4 m/s.
low = min(by["sqrt_wind"], key=lambda r: r[4])
assert low[1] ** 2 <= 4 and 1.1 <= low[4] <= 1.25, low
at8 = min(by["sqrt_wind"], key=lambda r: abs(r[1] ** 2 - 8))
assert round(at8[4], 1) == 1.6, at8
# "CV decreasing ... to 12 % when Kd(490) varies from 0.03 to 0.15"
# (p. 8): the low end. The high end, "from 30%", is not in this figure,
# whose largest CV is below 25: DATA.md section 25.
kd = by["kd490_per_m"]
assert max(r[2] for r in kd) < 25 and 11.5 <= min(r[2] for r in kd) <= 14
# "Tmax from 1 to 1.5s" as Kd(490) rises to 0.07, "and then Tmax remains
# stable" (p. 8)
assert 0.95 <= kd[0][4] <= 1.1 and 1.4 <= kd[4][4] <= 1.6

path = DATA_DIR / "gernez2009_conditions.csv"
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["variable", "x", "cv_percent", "cv_sd_percent",
                     "cv_reading_percent", "tmax_s", "tmax_reading_s",
                     "status", "note"])
    for variable, x, median, sd, t, t_unc in conditions:
        writer.writerow([variable, f"{x:g}", f"{median:.2f}",
                         "" if sd is None else f"{sd:.2f}",
                         f"{cv_per_px:.2f}", f"{t:.3f}", f"{t_unc:.3f}",
                         "read_from_figure", NOTE])
report(path.name, len(conditions))


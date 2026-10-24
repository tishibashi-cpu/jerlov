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

Figures 7, 10, 11, 13 and 14 are read further down, each with its own
notes. No input file is needed. DATA.md section 25.

Gernez, P. and Antoine, D. (2009), "Field characterization of
wave-induced underwater light field fluctuations", J. Geophys. Res. 114,
C06025, doi:10.1029/2008JC005059. Figures 7 to 14, pp. 8-13.
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



# -- Figures 7 and 13 -------------------------------------------------------------
# As Figure 8, for the overcast subset at the upper depth (Figure 7, page 8
# of 15, an 876 by 782 pixel image) and for the upward irradiance under clear
# skies at the upper depth (Figure 13, page 12, 877 by 785). Both have four
# panels, against the sun's zenith angle, the wave height, the wind speed
# itself (not its square root) and Kd(490); CV is 0-8 percent on the left,
# Tmax 0-4 s (Figure 7) or 0-8 s (Figure 13) on the right. The symbols are
# the medians ("As in Figure 8", whose caption refers to Figure 7's).
#
# Figure 7's circles and squares are filled. The circle's centre is the
# midpoint of its top and bottom edges two pixels either side of the bar,
# and the square's that of its top and bottom edges. Figure 13's are open:
# the circle's centre is the midpoint of its outline two pixels either side
# of the bar, and the square's that of its top and bottom edges, found by
# matching an outline 7 to 9 pixels across. Where an edge was not clear the
# rows were read from the pixels by eye, to a pixel. The CV bars are solid
# and read as in Figure 8; Tmax's are dashed and not read.

def ticks(px, first, step):
    return list(px), [first + k * step for k in range(len(px))]


FIG7_X = {
    "sun_zenith_deg": ticks([72.0, 113.0, 154.0, 195.0, 236.0, 277.0,
                             318.0, 359.0], 20, 10),
    "wave_height_m": ticks([525.0, 584.56, 644.0, 703.0, 762.53, 822.0],
                           0.0, 0.5),
    "wind_m_s": ticks([54.0, 84.51, 115.0, 145.54, 176.0, 207.0, 237.0,
                       268.0, 298.0, 329.0, 359.0], 0, 1),
    "kd490_per_m": ticks([513.4, 616.0, 719.0], 0.0, 0.05),
}
FIG7_Y = {"upper_cv": ticks([317.0, 240.0, 163.0, 86.0, 9.0], 0, 2),
          "upper_tmax": ticks([317.0, 240.0, 163.0, 86.0, 9.0], 0, 1),
          "lower_cv": ticks([723.0, 646.0, 569.0, 492.0, 415.0], 0, 2),
          "lower_tmax": ticks([723.0, 646.0, 569.0, 492.0, 415.0], 0, 1)}
FIG13_X = {
    "sun_zenith_deg": ticks([70.0, 111.0, 152.0, 193.54, 235.0, 276.0,
                             317.0, 358.0], 20, 10),
    "wave_height_m": ticks([525.0, 584.0, 644.0, 703.0, 762.44, 822.0],
                           0.0, 0.5),
    "wind_m_s": ticks([52.5, 83.0, 114.0, 144.0, 175.0, 205.0, 236.0,
                       266.42, 297.0, 328.0, 358.0], 0, 1),
    "kd490_per_m": ticks([523.0, 622.0, 722.0], 0.0, 0.05),
}
FIG13_Y = {"upper_cv": ticks([318.0, 279.0, 240.0, 202.0, 163.0, 124.0,
                              86.0, 47.0, 9.0], 0, 1),
           "lower_cv": ticks([726.0, 687.0, 649.0, 610.0, 571.0, 533.0,
                              494.0, 456.0, 417.0], 0, 1)}
FIG13_Y["upper_tmax"] = FIG13_Y["upper_cv"]
FIG13_Y["lower_tmax"] = FIG13_Y["lower_cv"]
PANEL_ROW = {"sun_zenith_deg": "upper", "wave_height_m": "upper",
             "wind_m_s": "lower", "kd490_per_m": "lower"}
CLASS = {"sun_zenith_deg": (20, 5), "wave_height_m": (0.0, 0.25),
         "wind_m_s": (0, 1), "kd490_per_m": (0.025, 0.01)}

# (column of the CV bar, its first and last dark row, row of the circle's
#  centre, row of the square's centre). None where the bar's midpoint is
#  not at the circle (see below).
FIG7 = {
    "sun_zenith_deg": [
        (71, 175, 215, 195, 128), (92, 165, 214, 189, 124),
        (113, 171, 219, 195, 131), (133, 172, 215, 194, 123),
        (154, 167, 209, 188, 123), (174, 168, 215, 191.25, 116.5),
        (195, 163, 208, 185.25, 110), (215, 160, 208, 184, 113),
        (236, 165, 213, 189, 113), (257, 159, 205, 182, 107),
        (277, 160, 209, 185, 106.5), (298, 170, 216, 193, 113),
        (318, 161, 206, 183, 105), (339, 147, 187, 167, 98)],
    "wave_height_m": [
        (525, 239, 282, 260, 136), (555, 211, 254, 232.25, 125.5),
        (585, 184, 218, 201.5, 116), (614, 172, 204, 188, 110),
        (644, 160, 191, 176, 110), (674, 143, 171, 157.5, 107),
        (703, 136, 166, 151, 88), (733, 120, 151, 135, 73),
        (763, 109, 136, 122.5, 66), (792, 99, 125, 112, 60)],
    "wind_m_s": [
        (54, 616, 653, 634, 520), (84, 602, 647, 624.75, 526),
        (115, 589, 636, 612, 526), (146, 592, 633, 613, 526),
        (176, 584, 621, 602.5, 529), (207, 570, 610, 589.75, 518),
        (237, 566, 601, 583.25, 520), (268, 570, 608, 589.25, 520),
        (298, 556, 589, 573, 513), (329, 549, 583, 566.75, 510)],
    "kd490_per_m": [
        (565, 585, 628, 606, 526), (585, 573, 618, 595, 523),
        (606, 576, 620, 598, 517), (626, 562, 608, 585, 517),
        (647, 566, 609, 587, 517), (668, 572, 614, 593, 513),
        (688, 556, 606, 581.5, 517), (709, 576, 623, 600, 526),
        (729, 582, 635, 608.5, 538), (750, 570, 614, 592, 540),
        (770, 587, 636, 611.75, 538), (791, 579, 636, 607.5, 523),
        (811, 643, 683, 663, 540)],
}
# In Figure 13a at 85 degrees the bar runs from row 140, above the square,
# to the axis, and its midpoint is 13 pixels below the circle; at Kd 0.035
# the bar is faint and its midpoint 2 pixels from the circle. Their
# standard deviations are not read. At 1.75 m the circle's lower edge runs
# into the S of the panel's "SUN"; the bar's midpoint is at the circle.
FIG13 = {
    "sun_zenith_deg": [
        (70, 266, 297, 281.75, 194.5), (91, 261, 294, 277.5, 186.5),
        (111, 253, 292, 272.5, 180.5), (132, 245, 300, 272.5, 186.5),
        (152, 245, 289, 267, 180.5), (173, 243, 282, 262.5, 183.5),
        (194, 224, 293, 258.5, 174.5), (214, 230, 283, 256.5, 174.5),
        (235, 223, 270, 246.5, 168.5), (255, 210, 263, 236.5, 160.5),
        (276, 205, 263, 233.5, 160.5), (296, 186, 260, 223, 156.5),
        (317, 168, 260, 213.5, 148.5), (338, None, None, 215.5, 152.5)],
    "wave_height_m": [
        (525, 263, 311, 286.75, 208.5), (554, 256, 300, 278.5, 200.5),
        (584, 241, 285, 262.5, 178), (614, 214, 277, 245.5, 156.5),
        (644, 206, 247, 226.5, 139.5), (673, 181, 234, 207.5, 128.5),
        (703, 176, 225, 200.5, 110.5), (733, 118, 291, 204.5, 92.5),
        (762, 131, 222, 176, 88.5), (792, 133, 216, 174.5, 103.5)],
    "wind_m_s": [
        (52, 660, 710, 685.25, 586.5), (83, 659, 703, 681.25, 583.5),
        (114, 650, 705, 677.5, 578.5), (144, 650, 696, 673.25, 591.5),
        (175, 639, 688, 662.75, 593.5), (205, 620, 695, 657.5, 597.5),
        (236, 626, 684, 654.5, 591.5), (266, 631, 676, 653, 589),
        (297, 620, 668, 644.25, 572.5), (328, 568, 689, 628.5, 552.5)],
    "kd490_per_m": [
        (573, 667, 711, 689, 604.5), (593, None, None, 681.5, 594.5),
        (612, 644, 696, 669.75, 586.5), (632, 624, 691, 657.5, 576.5),
        (652, 626, 690, 658, 572.5), (672, 619, 696, 657.5, 569),
        (692, 638, 687, 662.5, 565.5), (712, 640, 687, 663.5, 569),
        (732, 639, 686, 662.5, 554.5), (752, 626, 680, 653.5, 565.5),
        (772, 632, 683, 657.5, 569.5), (792, 613, 678, 645.5, 542.5),
        (812, 608, 683, 645.5, 515.5)],
}


def read_panels(points, x_ticks, y_ticks, name):
    lines = {k: calibrate(*v) for k, v in y_ticks.items()}
    for key, (_, err) in lines.items():
        assert err < 0.02 * y_ticks[key][1][-1], (name, key, err)
    out = []
    for variable, pts in points.items():
        x_of, x_err = calibrate(*x_ticks[variable])
        assert x_err < 0.01 * x_ticks[variable][1][-1], (name, variable)
        first, step = CLASS[variable]
        row = PANEL_ROW[variable]
        cv_line, t_line = lines[row + "_cv"][0], lines[row + "_tmax"][0]
        per_px = abs(cv_line(1.0) - cv_line(0.0))
        t_px = abs(t_line(1.0) - t_line(0.0))
        for k, (column, top, bottom, circle, square) in enumerate(pts):
            x = round(first + k * step, 3)
            assert abs(x_of(column) - x) < 0.2 * step, (name, variable, k)
            sd = None
            if top is not None and abs(0.5 * (top + bottom) - circle) <= 1.5:
                sd = 0.5 * (bottom - top) * per_px
            out.append((variable, x, cv_line(circle), sd, per_px,
                        t_line(square), t_px))
    return out


fig7 = read_panels(FIG7, FIG7_X, FIG7_Y, "Figure 7")
fig13 = read_panels(FIG13, FIG13_X, FIG13_Y, "Figure 13")


def series(rows, variable, k):
    return [r[k] for r in rows if r[0] == variable]


# Figure 7: "CV is low (steadily around 3%) and nearly independent of the
# sun altitude (Figure 7a) or the water clarity (Figure 7d)", "CV and Tmax
# regularly and slightly increasing with the wave height (Figure 7b), and,
# to a lesser extent, with the wind speed (Figure 7c). The average Tmax is
# of about 2.5s" (p. 7). Kd's last class, read at 1.6 percent, is the
# exception to "steadily around 3%": DATA.md section 25.
assert all(2.5 <= c <= 4.0 for c in series(fig7, "sun_zenith_deg", 2))
assert all(2.5 <= c <= 4.0 for c in series(fig7, "kd490_per_m", 2)[:-1])
for v in ("wave_height_m", "wind_m_s"):
    for k in (2, 5):
        s = series(fig7, v, k)
        assert s[-1] > s[0], (v, k, s)
cv = series(fig7, "wave_height_m", 2)
assert cv == sorted(cv), cv
t7 = [r[5] for r in fig7]
assert 2.3 <= sum(t7) / len(t7) <= 2.8, sum(t7) / len(t7)
# Figure 13: "as qs increases, CV increases from 1 to 3% and Tmax goes from
# 3.5 to 4.5s (Figure 13a)" (p. 10); the figure's Tmax is 3.2 s at 20
# degrees and 4.3 at 85: DATA.md section 25.
cv = series(fig13, "sun_zenith_deg", 2)
assert round(cv[0]) == 1 and round(cv[-1]) == 3, cv
t = series(fig13, "sun_zenith_deg", 5)
assert 3.0 <= t[0] <= 3.5 and 4.2 <= t[-1] <= 4.6, t
# "Larger changes ... with the wave height (Figure 13b)", and "both
# parameters increase when the water gets less clear (Figure 13d)".
for k in (2, 5):
    w = series(fig13, "wave_height_m", k)
    assert max(w) - min(w) > max(series(fig13, "wind_m_s", k)) \
        - min(series(fig13, "wind_m_s", k)), k
    d = series(fig13, "kd490_per_m", k)
    assert d[-1] > d[0], (k, d)

path = DATA_DIR / "gernez2009_more_conditions.csv"
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["figure", "sky", "irradiance", "variable", "x",
                     "cv_percent", "cv_sd_percent", "cv_reading_percent",
                     "tmax_s", "tmax_reading_s", "status", "note"])
    for figure, sky, flux, rows_ in (("7", "overcast", "Ed", fig7),
                                     ("13", "clear", "Eu", fig13)):
        for variable, x, cv_, sd, per_px, tm, t_px in rows_:
            writer.writerow([figure, sky, flux, variable, f"{x:g}",
                             f"{cv_:.2f}", "" if sd is None else f"{sd:.2f}",
                             f"{per_px:.3f}", f"{tm:.3f}", f"{t_px:.3f}",
                             "read_from_figure", NOTE])
report(path.name, len(fig7) + len(fig13))


# -- Figures 11 and 14 -----------------------------------------------------------
# The average CV and Tmax against wavelength, for the clear (open symbols,
# solid lines and bars) and overcast (filled, dotted) subsets: Figure 11 of
# the downwelling irradiance at the upper depth (page 11, 877 by 389
# pixels), Figure 14 of the upward irradiance at the lower depth, 8 to
# 8.7 m (page 13, 877 by 402). The captions say "average", not median.
# Clear-sky symbols and bars are read as in Figure 13; the overcast
# symbols as in Figure 7. The overcast bars are dotted, a dot every four
# pixels, and are not read. In Figure 11b the clear-sky bars at 665 and
# 683 nm run past the axis at 0 s; the standard deviation is read from the
# upper end, the bars being drawn the same length either side. In Figure
# 14 the overcast symbols are drawn 5 nm to the right of their band.

FIG11_X = {"a": ticks([59.0, 112.0, 166.0, 219.0, 273.0, 326.0, 380.0],
                      400, 50),
           "b": ticks([541.0, 594.0, 647.51, 701.0, 754.52, 808.0, 861.57],
                      400, 50)}
FIG11_Y = {"a": ticks([330.0, 250.0, 169.0, 89.0, 9.0], 0, 10),
           "b": ticks([330.0, 290.0, 250.0, 210.0, 169.0, 129.0, 89.0, 49.0,
                       9.0], 0, 1)}
FIG14_X = {"a": ticks([60.5, 116.0, 171.0, 226.49, 282.0, 337.0, 393.0],
                      400, 50),
           "b": ticks([529.0, 584.0, 639.45, 695.0, 750.0, 806.0, 861.0],
                      400, 50)}
FIG14_Y = {"a": ticks([341.0, 308.0, 275.0, 242.0, 208.44, 175.0, 142.0,
                       109.0, 76.0, 42.42], 0, 1),
           "b": ticks([341.0, 300.0, 258.0, 217.0, 175.0, 134.0, 92.0, 51.0],
                      0, 1)}
BANDS = (412, 442, 490, 510, 560, 665, 683)
# band: ((clear: column, bar's first and last dark row, symbol's centre),
#        (overcast: column, symbol's centre)), for panel a (CV) and b (Tmax).
# A last row of None is a bar that runs past the axis.
FIG11 = {
    "a": {412: ((72, 176, 242, 209.25), (72, 304.5)),
          442: ((104, 168, 240, 204.5), (104, 304.5)),
          490: ((155, 144, 223, 183.5), (155, 303.5)),
          510: ((177, 128, 215, 171.25), (177, 303.5)),
          560: ((230, 122, 207, 164.5), (230, 303.5)),
          665: ((342, 71, 173, 121.5), (343, 266.5)),
          683: ((362, 65, 169, 117.0), (362, 259.75))},
    "b": {412: ((553, 254, 300, 276.5), (554, 221.0)),
          442: ((585, 248, 301, 274.5), (586, 224.5)),
          490: ((637, 253, 300, 276.5), (637, 224.5)),
          510: ((658, 256, 302, 278.5), (659, 224.5)),
          560: ((712, 253, 303, 277.5), (712, 226.0)),
          665: ((824, 190, None, 281.5), (824, 91.5)),
          683: ((843, 187, None, 280.5), (843, 100.0))},
}
FIG14 = {
    "a": {412: ((74, 266, 314, 290.0), (80, 283.5)),
          442: ((107, 272, 311, 292.0), (113, 282.5)),
          490: ((160, 280, 312, 296.0), (166, 288.5)),
          510: ((182, 276, 309, 292.5), (189, 287.5)),
          560: ((238, 257, 295, 276.0), (244, 272.0)),
          665: ((354, 139, 194, 166.0), (360, 163.0)),
          683: ((374, 161, 213, 187.0), (380, 195.0))},
    "b": {412: ((542, 105, 194, 149.5), (548, 103.5)),
          442: ((575, 125, 212, 168.5), (581, 103.0)),
          490: ((628, 152, 237, 194.5), (634, 111.0)),
          510: ((650, 161, 240, 200.0), (657, 111.0)),
          560: ((706, 178, 258, 218.0), (712, 111.0)),
          665: ((822, 215, 290, 252.5), (828, 257.0)),
          683: ((842, 217, 271, 244.0), (848, 224.0))},
}


def read_bands(points, x_ticks, y_ticks, name, shift=0.0):
    out = {}
    for panel in ("a", "b"):
        x_of, x_err = calibrate(*x_ticks[panel])
        y_of, y_err = calibrate(*y_ticks[panel])
        assert x_err < 1.0 and y_err < 0.01 * y_ticks[panel][1][-1], \
            (name, panel, x_err, y_err)
        per_px = abs(y_of(1.0) - y_of(0.0))
        for band, ((col, top, bottom, centre), (col2, centre2)) \
                in points[panel].items():
            assert abs(x_of(col) - band) < 3, (name, panel, band)
            assert abs(x_of(col2) - band - shift) < 3, (name, panel, band)
            if bottom is None:
                sd = (centre - top) * per_px
            else:
                assert abs(0.5 * (top + bottom) - centre) <= 1.0, \
                    (name, panel, band)
                sd = 0.5 * (bottom - top) * per_px
            out.setdefault(band, {})[panel] = (y_of(centre), sd,
                                               y_of(centre2), per_px)
    return out


fig11 = read_bands(FIG11, FIG11_X, FIG11_Y, "Figure 11")
fig14 = read_bands(FIG14, FIG14_X, FIG14_Y, "Figure 14", shift=5.5)

# Figure 11: "the average value of CV for clear skies steadily increases
# from the blue (~15%) to the red (~25%), whereas it is slightly larger
# only for the red bands in the case of overcast skies", "The average Tmax
# period is spectrally flat for clear skies ..., whereas two distinct
# regimes appear under overcast skies, with larger values (Tmax = 6s) for
# the red bands" (p. 10).
clear = [fig11[b]["a"][0] for b in BANDS]
over = [fig11[b]["a"][2] for b in BANDS]
assert round(clear[0]) == 15 and 25 <= clear[-1] <= 27, clear
assert all(a < b for a, b in zip(clear, clear[1:])), clear
assert max(over[:5]) - min(over[:5]) < 0.2 and min(over[5:]) > 2 * max(over[:5])
t_clear = [fig11[b]["b"][0] for b in BANDS]
t_over = [fig11[b]["b"][2] for b in BANDS]
assert max(t_clear) - min(t_clear) < 0.25, t_clear
assert all(round(t) == 6 for t in t_over[5:]), t_over
# Figure 14: "The coefficient of variation is almost spectrally flat and
# equal to about 2% for l < 600 nm, and then increases to about 6% in the
# red"; the figure's largest is 5.4: DATA.md section 25. Tmax "monotonously
# decreases from 5s (at 442 nm) to 2s (red bands)" on one curve and is
# "constant for l < 600 nm" on the other (p. 10); the text gives these to
# the opposite skies from the figure's labels and caption, which are
# followed here: DATA.md section 25.
for k in (0, 2):
    cv14 = [fig14[b]["a"][k] for b in BANDS]
    assert all(1.2 <= c <= 2.5 for c in cv14[:5]) and min(cv14[5:]) > 4, cv14
    assert max(cv14) < 5.5, cv14
t_clear = [fig14[b]["b"][0] for b in BANDS]
t_over = [fig14[b]["b"][2] for b in BANDS]
assert all(a > b for a, b in zip(t_clear[:6], t_clear[1:6])), t_clear
assert 4 <= t_clear[1] <= 5 and all(2 <= t <= 2.5 for t in t_clear[5:])
assert max(t_over[:5]) - min(t_over[:5]) < 0.3, t_over

path = DATA_DIR / "gernez2009_spectral.csv"
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["figure", "irradiance", "sky", "wavelength_nm",
                     "cv_percent", "cv_sd_percent", "cv_reading_percent",
                     "tmax_s", "tmax_sd_s", "tmax_reading_s", "status",
                     "note"])
    count = 0
    for figure, flux, data in (("11", "Ed", fig11), ("14", "Eu", fig14)):
        for sky in ("clear", "overcast"):
            for band in BANDS:
                a, b = data[band]["a"], data[band]["b"]
                k = 0 if sky == "clear" else 2
                sd_a = f"{a[1]:.2f}" if sky == "clear" else ""
                sd_b = f"{b[1]:.3f}" if sky == "clear" else ""
                writer.writerow([figure, flux, sky, band, f"{a[k]:.2f}",
                                 sd_a, f"{a[3]:.3f}", f"{b[k]:.3f}", sd_b,
                                 f"{b[3]:.3f}", "read_from_figure", NOTE])
                count += 1
report(path.name, count)


# -- Figure 10 -------------------------------------------------------------------
# Figure 8 for six bands, under clear skies at the upper depth ("As in
# Figure 8, but for all bands", page 11, an 877 by 823 pixel colour image),
# against the sun's zenith angle, the wave height, the wind speed itself and
# Kd(490). Each band is a coloured line, CV and Tmax alike, without symbols
# or bars. The CV lines bend at the classes of Figure 8, and Figure 10's 510
# nm line lies on Figure 8's medians (checked below); the wind classes are
# whole metres per second, as in Figures 7 and 13. The Tmax lines bend a
# few pixels to the side of the classes and, in the same colours, cross
# their own band's CV line and run within a pixel or two of each other: they
# are not read.
#
# Each band's pixels are found by hue (443 nm blue, 490 sky blue, 510
# turquoise, 560 green, 670 red, 683 orange). The CV line is followed from
# its left end, where it is the band's upper line, class by class, taking at
# each class the run of the band's colour whose straight segment back to the
# previous class, and on to the next, is best covered by that colour. Each
# segment is then fitted with a straight line through the band's pixels
# along it, where they make a single run; the row given is the mean of the
# two fits that meet at the class's column, or the one fit at either end.
# Three places are read otherwise. At 20 degrees the 510 nm line lies under
# the 560 nm line; its row is where the fit to its visible pixels, 84 to 100,
# meets the class's column. In panel b at 1.75 and 2 m the 683 nm line runs
# beside its own Tmax line; the rows are where the fits to the segments
# beyond them meet the classes, and past 2 m the line leaves the axes at 35
# percent (column 777), so 2.25 m is not read (None).
FIG10_X = {
    "sun_zenith_deg": ticks([81.0, 121.0, 162.0, 203.0, 243.0, 284.0, 325.0,
                             365.0], 20, 10),
    "wave_height_m": ticks([530.0, 588.0, 647.0, 706.0, 764.61, 823.0],
                           0.0, 0.5),
    "wind_m_s": ticks([63.0, 93.0, 124.0, 154.0, 184.0, 214.0, 245.0, 275.0,
                       305.0, 335.0, 365.46], 0, 1),
    "kd490_per_m": ticks([528.0, 626.0, 725.0], 0.0, 0.05),
}
FIG10_Y = {"upper": ticks([361.0, 317.0, 273.0, 230.0, 186.0, 143.0, 99.0,
                           56.0], 0, 5),
           "lower": ticks([763.0, 720.0, 676.0, 632.0, 589.0, 545.0, 502.0,
                           458.0], 0, 5)}
FIG10_CLASS = {"sun_zenith_deg": (20, 5, 14), "wave_height_m": (0.0, 0.25, 10),
               "wind_m_s": (0, 1, 10), "kd490_per_m": (0.025, 0.01, 13)}
FIG10_BANDS = (443, 490, 510, 560, 670, 683)
# Rows of the CV line at each class, top of the image 0.
FIG10 = {
    "sun_zenith_deg": {
        443: [188.0, 186.7, 196.9, 195.4, 202.8, 212.0, 226.8, 234.5, 247.9,
              267.1, 286.9, 308.7, 317.3, 326.5],
        490: [165.6, 165.1, 174.5, 172.4, 180.8, 188.4, 203.5, 210.9, 224.3,
              244.5, 264.6, 289.4, 306.7, 320.9],
        510: [147.4, 146.2, 159.8, 154.2, 165.7, 174.5, 189.4, 198.9, 212.4,
              233.4, 254.7, 283.0, 300.6, 319.4],
        560: [146.0, 144.7, 154.7, 150.5, 160.5, 167.8, 182.9, 190.1, 200.4,
              220.0, 240.1, 269.6, 284.5, 306.6],
        670: [99.7, 101.4, 109.4, 105.4, 113.6, 123.9, 141.1, 148.9, 165.0,
              185.8, 206.6, 233.7, 243.7, 265.0],
        683: [95.4, 99.2, 106.8, 101.5, 110.1, 118.6, 135.5, 144.9, 159.5,
              182.9, 204.0, 228.2, 239.9, 258.8],
    },
    "wave_height_m": {
        443: [241.9, 227.6, 214.9, 223.5, 227.0, 235.0, 238.5, 238.9, 237.8,
              265.0],
        490: [218.8, 203.6, 192.7, 202.5, 205.3, 215.7, 224.3, 225.9, 223.9,
              253.6],
        510: [206.5, 188.1, 177.7, 190.2, 195.2, 203.5, 215.3, 218.4, 213.9,
              244.1],
        560: [200.3, 180.8, 170.5, 181.4, 188.0, 193.6, 209.6, 211.7, 207.4,
              231.2],
        670: [168.1, 145.0, 131.5, 136.8, 131.1, 115.0, 117.2, 77.0, 83.4,
              65.7],
        683: [165.7, 141.6, 126.1, 132.0, 124.7, 106.2, 106.5, 75.5, 63.0,
              None],
    },
    "wind_m_s": {
        443: [651.5, 630.9, 614.3, 610.7, 609.6, 622.2, 635.8, 648.4, 643.4,
              659.1],
        490: [628.8, 608.5, 590.3, 585.9, 585.9, 600.7, 616.1, 626.8, 623.8,
              646.7],
        510: [616.0, 594.8, 575.1, 570.2, 571.7, 588.9, 604.2, 617.1, 614.0,
              638.6],
        560: [609.5, 587.7, 566.5, 563.6, 565.2, 581.2, 597.7, 607.3, 608.6,
              628.9],
        670: [576.4, 544.9, 520.5, 516.4, 515.0, 535.5, 554.9, 570.1, 571.8,
              583.1],
        683: [571.6, 539.3, 517.4, 511.6, 510.2, 533.3, 551.7, 565.5, 565.2,
              578.1],
    },
    "kd490_per_m": {
        443: [596.7, 613.3, 625.3, 637.9, 648.3, 649.5, 659.0, 660.7, 670.8,
              671.2, 681.7, 673.6, 670.4],
        490: [572.5, 589.4, 601.3, 615.5, 625.9, 627.6, 639.1, 644.2, 653.0,
              657.3, 665.3, 659.6, 652.5],
        510: [553.9, 573.8, 587.0, 603.9, 612.6, 617.7, 628.0, 633.7, 643.6,
              649.1, 654.9, 654.5, 642.6],
        560: [548.7, 567.0, 581.1, 593.3, 603.6, 607.4, 619.8, 626.4, 635.6,
              643.9, 642.9, 651.9, 639.1],
        670: [505.6, 522.0, 536.6, 550.4, 555.9, 558.3, 578.5, 576.2, 585.3,
              600.1, 603.5, 600.7, 586.4],
        683: [502.4, 517.8, 531.5, 547.6, 550.6, 551.1, 574.5, 571.5, 580.7,
              595.4, 599.7, 592.1, 582.3],
    },
}
# The share of diffuse light in the downwelling irradiance above the water,
# printed along the top of Figure 10a (and of Figure 8a) at the major ticks
# of the sun's zenith angle, 20 to 90 degrees.
DIFFUSE_SHARE = {20: 21, 30: 23, 40: 25, 50: 28, 60: 34, 70: 45, 80: 70,
                 90: 100}

fig10 = {}
for variable, bands in FIG10.items():
    x_of, x_err = calibrate(*FIG10_X[variable])
    assert x_err < 0.01 * FIG10_X[variable][1][-1], variable
    half = "upper" if variable in ("sun_zenith_deg", "wave_height_m") \
        else "lower"
    y_of, y_err = calibrate(*FIG10_Y[half])
    assert y_err < 0.1, (variable, y_err)
    per_px = abs(y_of(1.0) - y_of(0.0))
    first, step, count = FIG10_CLASS[variable]
    for band in FIG10_BANDS:
        assert len(bands[band]) == count, (variable, band)
        fig10[variable, band] = [
            (round(first + k * step, 3), None if row is None else y_of(row))
            for k, row in enumerate(bands[band])]
fig10_per_px = per_px

# Figure 10's 510 nm line is Figure 8's medians: within 0.2 percent at
# every class of panels a, b and d (panel c's classes differ).
fig8 = [("sun_zenith_deg", r[0], r[1]) for r in rows] \
    + [c[:3] for c in conditions]
checked = 0
for variable, x, median in fig8:
    line = dict(fig10.get((variable, 510), []))
    if round(x, 3) in line:
        assert abs(line[round(x, 3)] - median) < 0.2, (variable, x)
        checked += 1
assert checked == 14 + 10 + 13, checked
# "the shape of the CV curves is essentially preserved, whereas the
# amplitude changes, with larger CVs for longer wavelengths" (p. 9): at
# every class read, CV rises from band to band, 683 nm at least 670's.
for variable, (first, step, count) in FIG10_CLASS.items():
    for k in range(count):
        cvs = [fig10[variable, b][k][1] for b in FIG10_BANDS]
        if cvs[-1] is None:
            cvs = cvs[:-1]
        assert all(a < b for a, b in zip(cvs[:-2], cvs[1:-1])), (variable, k)
        assert cvs[-1] >= cvs[-2], (variable, k)
# "CV at these bands [the red] increases with wave height, contrary to what
# is observed at 510 nm and at other wavelengths < 600 nm" (p. 10).
for band in FIG10_BANDS:
    cvs = [c for _, c in fig10["wave_height_m", band] if c is not None]
    if band > 600:
        assert cvs[-1] > cvs[0] + 8, (band, cvs)
    else:
        assert cvs[-1] < cvs[0] and cvs[-1] < max(cvs) - 4, (band, cvs)
# The diffuse share rises with the sun's zenith angle to all of the light.
share = [DIFFUSE_SHARE[z] for z in sorted(DIFFUSE_SHARE)]
assert share == sorted(share) and share[-1] == 100, share

path = DATA_DIR / "gernez2009_bands.csv"
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["variable", "x", "wavelength_nm", "cv_percent",
                     "cv_reading_percent", "status", "note"])
    count = 0
    for variable in FIG10:
        for band in FIG10_BANDS:
            for x, cv_ in fig10[variable, band]:
                if cv_ is None:
                    writer.writerow([variable, f"{x:g}", band, "",
                                     f"{fig10_per_px:.3f}", "above_axis",
                                     "the line leaves the axes at 35 "
                                     "percent; DATA.md section 25"])
                else:
                    writer.writerow([variable, f"{x:g}", band, f"{cv_:.2f}",
                                     f"{fig10_per_px:.3f}",
                                     "read_from_figure", NOTE])
                count += 1
report(path.name, count)

path = DATA_DIR / "gernez2009_diffuse_share.csv"
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["sun_zenith_deg", "diffuse_percent", "status", "note"])
    for zenith in sorted(DIFFUSE_SHARE):
        writer.writerow([zenith, DIFFUSE_SHARE[zenith], "transcribed",
                         "printed along the top of Figures 8a and 10a; "
                         "DATA.md section 25"])
report(path.name, len(DIFFUSE_SHARE))

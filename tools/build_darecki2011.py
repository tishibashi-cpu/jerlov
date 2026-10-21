"""Read Darecki, Stramski & Sokolski's (2011) light fluctuations off their figures.

Darecki et al. measured how much the light under a wavy surface fluctuates,
as the coefficient of variation, standard deviation over mean, of time
series sampled at 1 kHz: of the downwelling irradiance at three depths
and wavelengths (Figure 13a), and of the radiance at thirteen zenith
angles in the plane of the sun (Figure 15). The paper prints neither as a
table.

Both figures are drawn in the PDF as vector graphics, so each marker's
position is read from the page's drawing commands rather than from an
image: the coordinates below, in PDF points (y down the page), are those
of the markers as drawn, and the axes are calibrated on the major tick
marks drawn with them. The reading itself is exact to about 0.001 pt,
which is far finer than the values are given to here; how exactly the
plotting program placed the markers is not known. DATA.md section 24.

No input file is needed: the coordinates are literals below, read with
PyMuPDF's ``get_drawings`` from the article as published (pages 12 and 14
of 16).

Darecki, M., Stramski, D. and Sokolski, M. (2011), "Measurements of
high-frequency light fluctuations induced by sea surface waves with an
Underwater Porcupine Radiometer System", J. Geophys. Res. 116, C00H09,
doi:10.1029/2011JC007338. Figures 13a (p. 12) and 15 (p. 14).
"""

import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import DATA_DIR, report


def calibrate(positions, values):
    """Least-squares line from page coordinate to axis value; returns the
    line and the largest residual of the ticks, in axis units."""
    n = len(positions)
    mx, my = sum(positions) / n, sum(values) / n
    slope = (sum((p - mx) * (v - my) for p, v in zip(positions, values))
             / sum((p - mx) ** 2 for p in positions))
    line = lambda p: my + slope * (p - mx)                  # noqa: E731
    return line, max(abs(line(p) - v) for p, v in zip(positions, values))


# -- Figure 13a: CV of Ed against depth --------------------------------------
# Frame x0 111.611 (CV 0), y0 63.795 (depth 0) to y1 202.498 (10 m). Major
# ticks: CV 0.1 to 0.7 along the bottom, depth 2 to 8 m along the left.
CV_TICKS = ([135.297, 158.983, 182.670, 206.355, 230.041, 253.781, 277.467],
            [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7])
DEPTH_TICKS = ([63.795, 91.535, 119.276, 147.017, 174.757, 202.498],
               [0.0, 2.0, 4.0, 6.0, 8.0, 10.0])

# Marker boxes (x0, y0, x1, y1). Circles and squares are centred on their
# point. The triangles point down, and are placed by their centroid, a third
# of the way from the top edge: the box centre would put every 532 nm depth
# 0.05 m deeper than the same depth at the other two wavelengths, which
# were measured at once.
FIG13A = {
    443: ("circle", [(120.788, 194.442, 125.162, 198.817),
                     (125.001, 154.912, 129.376, 159.232),
                     (142.125, 113.941, 146.500, 118.315),
                     (154.876, 100.978, 159.250, 105.352),
                     (186.938, 85.187, 191.312, 89.561),
                     (226.788, 73.505, 231.162, 77.878)]),
    532: ("triangle", [(121.587, 195.403, 125.908, 199.244),
                       (127.935, 155.872, 132.310, 159.713),
                       (148.314, 114.901, 152.688, 118.742),
                       (162.451, 101.938, 166.773, 105.832),
                       (198.728, 86.147, 203.048, 89.988),
                       (237.724, 74.464, 242.046, 78.305)]),
    670: ("square", [(129.056, 194.816, 132.736, 198.550),
                     (138.819, 155.285, 142.499, 158.966),
                     (164.478, 114.314, 168.159, 118.049),
                     (180.803, 101.404, 184.538, 105.086),
                     (226.415, 85.561, 230.149, 89.295),
                     (264.612, 73.877, 268.293, 77.611)]),
}
# The legend's three markers, at x 214.4-218.8, are not data.


def point(kind, box):
    x0, y0, x1, y1 = box
    y = y0 + (y1 - y0) / 3 if kind == "triangle" else (y0 + y1) / 2
    return (x0 + x1) / 2, y


cv_of, cv_err = calibrate(*CV_TICKS)
depth_of, depth_err = calibrate(*DEPTH_TICKS)
# The ticks themselves sit up to 0.03 pt off a straight line: 0.0001 in CV.
assert cv_err < 2e-4 and depth_err < 1e-3, (cv_err, depth_err)

irradiance = {}
for wl, (kind, boxes) in FIG13A.items():
    irradiance[wl] = [(depth_of(y), cv_of(x))
                      for x, y in (point(kind, b) for b in boxes)]

# The three wavelengths were measured at the same depths.
for k in range(6):
    depths = [irradiance[wl][k][0] for wl in FIG13A]
    assert max(depths) - min(depths) < 0.01, depths
for wl, pts in irradiance.items():
    # Deeper, steadier: CV falls with depth at every wavelength.
    assert all(a[0] < b[0] and a[1] > b[1]
               for a, b in zip(pts[::-1], pts[::-1][1:])), wl
# "the CV is higher in the red compared with the blue" (p. 12), at every
# depth here.
for k in range(6):
    assert irradiance[443][k][1] < irradiance[532][k][1] \
        < irradiance[670][k][1], k
DEPTHS = [round(sum(irradiance[wl][k][0] for wl in FIG13A) / 3, 2)
          for k in range(6)]


# -- Figure 15: CV of radiance against zenith angle ---------------------------
# Three panels, the same x axis: -90 to 90 degrees, positive towards the
# sun. Major ticks at -60, -30, 0, 30 and 60.
ANGLE_TICKS = {"a": [141.165, 168.184, 195.150, 222.169, 249.188],
               "b": [141.165, 168.184, 195.150, 222.169, 249.188],
               "c": [141.479, 168.497, 195.464, 222.482, 249.501]}
# Frame bottom (CV 0) and major ticks: 0.4 to 1.6 in panel a; 0.4 to 3.2
# in b and c.
CV15_TICKS = {
    "a": ([389.557, 362.487, 335.417, 308.241, 281.223],
          [0.0, 0.4, 0.8, 1.2, 1.6]),
    "b": ([547.912, 531.952, 515.992, 500.084, 484.174, 468.213, 452.252,
           436.396, 420.435],
          [0.0, 0.4, 0.8, 1.2, 1.6, 2.0, 2.4, 2.8, 3.2]),
    "c": ([706.583, 690.622, 674.661, 658.701, 642.843, 626.884, 610.924,
           595.014, 579.054],
          [0.0, 0.4, 0.8, 1.2, 1.6, 2.0, 2.4, 2.8, 3.2]),
}
# Circle centres (x, y), from -90 to 90 degrees.
FIG15 = {
    "a": [(114.198, 387.888), (141.190, 363.686), (168.184, 385.202),
          (181.640, 383.454), (195.176, 374.874), (208.659, 299.373),
          (213.145, 305.815), (217.632, 308.579), (222.168, 271.989),
          (226.654, 353.671), (231.141, 366.685), (249.186, 370.936),
          (276.180, 384.523)],
    "b": [(114.198, 545.854), (141.190, 521.912), (168.184, 543.558),
          (181.640, 542.723), (195.176, 541.472), (208.659, 508.899),
          (213.145, 479.037), (217.632, 481.853), (222.168, 505.586),
          (226.654, 493.434), (231.141, 428.181), (249.186, 526.399),
          (276.180, 545.358)],
    "c": [(114.512, 704.836), (141.478, 680.113), (168.497, 702.332),
          (181.953, 702.567), (195.490, 698.368), (208.973, 609.306),
          (213.458, 613.738), (217.943, 622.189), (222.482, 623.623),
          (226.967, 576.392), (231.453, 642.270), (249.501, 689.553),
          (276.494, 704.627)],
}
ANGLES = [-90, -60, -30, -15, 0, 15, 20, 25, 30, 35, 40, 60, 90]

radiance = {}
for panel, pts in FIG15.items():
    angle_of, a_err = calibrate(ANGLE_TICKS[panel], [-60, -30, 0, 30, 60])
    cv15_of, c_err = calibrate(*CV15_TICKS[panel])
    assert a_err < 0.05 and c_err < 2e-3, (panel, a_err, c_err)
    read = [(angle_of(x), cv15_of(y)) for x, y in pts]
    # The thirteen sensors sit at whole angles; every marker falls within
    # a tenth of a degree of one.
    assert all(abs(a - n) < 0.1 for (a, _), n in zip(read, ANGLES)), panel
    assert all(cv > 0 for _, cv in read), panel
    # "a major maximum of CV within the range of theta encompassing the
    # mean direction of solar beam in water" (p. 14): the largest value
    # lies between 15 and 40 degrees.
    peak = max(range(len(read)), key=lambda i: read[i][1])
    assert 15 <= ANGLES[peak] <= 40, panel
    radiance[panel] = [(n, cv) for n, (_, cv) in zip(ANGLES, read)]
# "the magnitude of CV of radiance within the major maximum ... can exceed
# 300%" (p. 14).
assert max(cv for _, cv in radiance["b"] + radiance["c"]) > 3.0


# -- Figure 13b: CV of Ed against wavelength, five winds -------------------
# Same frame as 13a in x, below it: x0 111.61 (400 nm) to 277.52 (700 nm),
# y 382.544 (CV 0) to 243.840 (0.6). Major ticks at 400-650 nm by 50 and
# at CV 0.1-0.5. The six irradiance channels are 410, 443, 488, 532, 610
# and 670 nm (p. 3). Each curve is labelled with its wind speed in the
# panel; the marker that goes with each label was matched by eye on a
# rendering of the panel.
WL_TICKS = ([121.960, 147.887, 173.814, 199.742, 225.669, 251.596],
            [400, 450, 500, 550, 600, 650])
CV13B_TICKS = ([382.544, 359.392, 336.292, 313.140, 290.040, 266.886],
               [0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
CHANNELS = [410, 443, 488, 532, 610, 670]
# wind m/s: (marker, boxes from 410 to 670 nm). Up triangles sit on their
# centroid two thirds of the way down, down triangles one third.
FIG13B = {
    3.9: ("circle", [(124.949, 288.226, 129.323, 292.602),
                     (142.073, 282.838, 146.394, 287.213),
                     (165.385, 279.957, 169.706, 284.331),
                     (188.217, 275.850, 192.590, 280.224),
                     (228.654, 261.393, 233.029, 265.767),
                     (259.757, 250.616, 264.132, 254.990)]),
    5.4: ("square", [(125.268, 300.603, 128.949, 304.336),
                     (142.392, 288.653, 146.073, 292.388),
                     (165.705, 281.184, 169.386, 284.919),
                     (188.538, 276.543, 192.273, 280.277),
                     (228.975, 265.287, 232.656, 269.022),
                     (260.077, 258.885, 263.757, 262.619)]),
    6.3: ("up", [(124.949, 316.554, 129.269, 320.395),
                 (142.073, 310.632, 146.394, 314.474),
                 (165.385, 304.124, 169.706, 307.965),
                 (188.218, 301.829, 192.591, 305.670),
                 (228.655, 287.852, 232.976, 291.693),
                 (259.757, 279.957, 264.078, 283.798)]),
    7.2: ("down", [(124.949, 321.621, 129.269, 325.463),
                   (142.073, 315.700, 146.394, 319.541),
                   (165.385, 313.833, 169.706, 317.728),
                   (188.218, 310.793, 192.591, 314.632),
                   (228.655, 303.004, 232.976, 306.897),
                   (259.757, 296.282, 264.078, 300.123)]),
    10.3: ("diamond", [(124.575, 337.572, 129.696, 342.694),
                       (141.700, 335.758, 146.767, 340.880),
                       (165.012, 334.852, 170.079, 340.026),
                       (187.844, 331.651, 192.965, 336.772),
                       (228.283, 315.594, 233.404, 320.715),
                       (259.383, 300.549, 264.505, 305.670)]),
}
# The caption's date and local time for each wind (p. 12).
DAYS = {3.9: "20 September 2008, 09:42", 5.4: "18 September 2008, 09:48",
        6.3: "16 September 2008, 13:55", 7.2: "19 September 2008, 13:41",
        10.3: "15 September 2008, 14:15"}


def point13b(kind, box):
    x0, y0, x1, y1 = box
    h = y1 - y0
    y = {"up": y1 - h / 3, "down": y0 + h / 3}.get(kind, (y0 + y1) / 2)
    return (x0 + x1) / 2, y


wl_of, w_err = calibrate(*WL_TICKS)
cv13b_of, c13_err = calibrate(*CV13B_TICKS)
assert w_err < 0.1 and c13_err < 2e-4, (w_err, c13_err)
spectral = {}
for wind, (kind, boxes) in FIG13B.items():
    read = [(wl_of(x), cv13b_of(y)) for x, y in (point13b(kind, b)
                                                for b in boxes)]
    # every marker sits on a channel, within a nanometre
    assert all(abs(w - n) < 1.0 for (w, _), n in zip(read, CHANNELS)), wind
    # "the CV of irradiance shows an increase with increasing light
    # wavelength" (p. 12): red above blue on every day
    assert read[-1][1] > read[0][1], wind
    spectral[wind] = [cv for _, cv in read]
# The windiest day is the steadiest at every wavelength.
assert all(spectral[10.3][k] < min(spectral[w][k] for w in DAYS if w != 10.3)
           for k in range(6))

NOTE = "read from the figure's drawing commands; DATA.md section 24"
path = DATA_DIR / "darecki2011_irradiance_cv.csv"
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["depth_m", "wavelength_nm", "cv", "status", "note"])
    rows = 0
    for k, depth in enumerate(DEPTHS):
        for wl in FIG13A:
            writer.writerow([f"{depth:.2f}", wl,
                             f"{irradiance[wl][k][1]:.4f}",
                             "read_from_figure", NOTE])
            rows += 1
report(path.name, rows)

path = DATA_DIR / "darecki2011_radiance_cv.csv"
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["panel", "zenith_deg", "cv", "status", "note"])
    rows = 0
    for panel, pts in radiance.items():
        for angle, cv in pts:
            writer.writerow([panel, angle, f"{cv:.4f}", "read_from_figure",
                             NOTE])
            rows += 1
report(path.name, rows)

path = DATA_DIR / "darecki2011_spectral_cv.csv"
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["wind_m_s", "day", "wavelength_nm", "cv", "status",
                     "note"])
    rows = 0
    for wind, cvs in spectral.items():
        for wl, cv in zip(CHANNELS, cvs):
            writer.writerow([wind, DAYS[wind], wl, f"{cv:.4f}",
                             "read_from_figure", NOTE])
            rows += 1
report(path.name, rows)

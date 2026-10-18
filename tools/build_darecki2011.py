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

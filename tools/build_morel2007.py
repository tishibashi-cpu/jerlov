# -*- coding: utf-8 -*-
"""Transcribe Morel et al. (2007) Tables 1 and 2.

Morel, A., Gentili, B., Claustre, H., Babin, M., Bricaud, A., Ras, J. and
Tièche, F. (2007), "Optical properties of the 'clearest' natural waters",
Limnol. Oceanogr. 52(1), 217-229, doi:10.4319/lo.2007.52.1.0217. Table 1
(p. 220): eight stations of the South Pacific gyre, November 2004. Table 2
(p. 224): the absorption of pure water they adopted, aw1 and aw2, and the
scattering of pure sea water, bsw.

No input file is needed: the values are literals below, read from the page
images and checked against the text layer, and checked here before
anything is written. See DATA.md section 46 and DECISIONS.md section 102.
"""

import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import DATA_DIR, report  # noqa: E402

# (nm, aw1, aw2 or "", bsw), as printed, Table 2.
TABLE2 = [
    (300, "0.03820", "0.01150", "0.0226"), (305, "0.03350", "0.01100", "0.0211"),
    (310, "0.02880", "0.01050", "0.0197"), (315, "0.02515", "0.01013", "0.0185"),
    (320, "0.02150", "0.00975", "0.0173"), (325, "0.01875", "0.00926", "0.0162"),
    (330, "0.01600", "0.00877", "0.0152"), (335, "0.01395", "0.00836", "0.0144"),
    (340, "0.01190", "0.00794", "0.0135"), (345, "0.01050", "0.00753", "0.0127"),
    (350, "0.00910", "0.00712", "0.0121"), (355, "0.00810", "0.00684", "0.0113"),
    (360, "0.00710", "0.00656", "0.0107"), (365, "0.00656", "0.00629", "0.0099"),
    (370, "0.00602", "0.00602", "0.0095"), (375, "0.00561", "", "0.0089"),
    (380, "0.00520", "", "0.0085"), (385, "0.00499", "", "0.0081"),
    (390, "0.00478", "", "0.0077"), (395, "0.00469", "", "0.0072"),
    (400, "0.00460", "", "0.0069"), (405, "0.00460", "", "0.0065"),
    (410, "0.00460", "", "0.0062"), (415, "0.00457", "", "0.0059"),
    (420, "0.00454", "", "0.0056"), (425, "0.00475", "", "0.0054"),
    (430, "0.00495", "", "0.0051"), (435, "0.00565", "", "0.0049"),
    (440, "0.00635", "", "0.0047"), (445, "0.00779", "", "0.0044"),
    (450, "0.00922", "", "0.0043"), (455, "0.00951", "", "0.0040"),
    (460, "0.00979", "", "0.0039"), (465, "0.01011", "", "0.0037"),
    (470, "0.01060", "", "0.0035"), (475, "0.01140", "", "0.0034"),
    (480, "0.01270", "", "0.0033"), (485, "0.01360", "", "0.0031"),
    (490, "0.01500", "", "0.0030"), (495, "0.01730", "", "0.0029"),
    (500, "0.02040", "", "0.0027"),
]

#: Where aw1 is the mean of Pope & Fry's 5 nm either side.
MEANS = (425, 435, 445, 455)

STATIONS = ("STB-4", "STB-5", "STB-7", "STB-8", "GYR-4", "GYR-5",
            "STB-14", "STB-15")
# (column, values in station order), as printed, Table 1.
TABLE1 = [
    ("latitude_deg_s", "16.52 18.44 22.03 23.33 26.03 26.04 29.55 30.47"),
    ("longitude_deg_w", "128.23 125.57 120.21 117.53 114.01 114.02 98.52 95.25"),
    ("date_2004", "06-Nov 07-Nov 09-Nov 10-Nov 14-Nov 15-Nov 23-Nov 24-Nov"),
    ("chl_5m_mg_m3",
     "0.0420 0.0350 0.0220 0.0240 0.0195 0.0200 0.0260 0.0460"),
    ("chl_30_40m_mg_m3",
     "0.0450 0.0350 0.0200 0.0250 0.0270 0.0250 0.0360 0.0770"),
    ("zeu_m", "135 142 172 170 160 166 138 108"),
    ("z_chl_max_m", "160 150 195 175 170 160 155 100"),
    ("chl_max_mg_m3", "0.195 0.204 0.173 0.152 0.178 0.195 0.225 0.247"),
    ("kd_420_per_m",
     "0.0184 0.0170 0.0134 0.0145 0.0120 0.0120 0.0165 0.0230"),
    ("kd_310_per_m",
     "0.0940 0.0810 0.0680 0.0690 0.0700 0.0690 0.0850 0.1150"),
    ("ap_420_per_m",
     "0.0041 0.0038 0.0023 0.0019 0.0022 0.0022 0.0041 0.0054"),
    ("ap_310_per_m",
     "0.0065 0.0045 0.0041 0.0031 0.0055 0.0057 0.0090 0.0120"),
    ("r_max_percent", "10.3 11.5 13.5 13.4 13.5 13.3 11.6 10.4"),
    ("r_max_nm", "390 396 395 394 394 396 396 396"),
    ("atot_420_per_m",
     "0.0120 0.0102 0.0072 0.0080 0.0061 0.0064 0.0095 0.0132"),
    ("atot_310_per_m",
     "0.0620 0.0520 0.0410 0.0430 0.0480 0.0430 0.0530 0.0690"),
    ("ay1_310_per_m",
     "0.0300 0.0210 0.0070 0.0110 0.0140 0.0120 0.0150 0.0300"),
    ("ay2_310_per_m",
     "0.0482 0.0392 0.0252 0.0292 0.0322 0.0202 0.0232 0.0482"),
]
#: ay2 - ay1 at 310 nm must be aw1(310) - aw2(310), since both are atot -
#: ap - aw; at these two stations it is 0.0100 less (DATA.md section 46).
SUSPECT_AY2 = ("GYR-5", "STB-14")
AY2_NOTE = ("ay2 - ay1 is 0.0082 here and 0.0182 at the other six stations, "
            "where it should be aw1(310) - aw2(310) = 0.0183; one of the two "
            "ay is likely misprinted by 0.0100 (DATA.md section 46)")


def check() -> dict:
    wl = [w for w, *_ in TABLE2]
    assert wl == list(range(300, 501, 5)), wl
    aw1 = {w: float(a) for w, a, _, _ in TABLE2}
    aw2 = {w: float(b) for w, _, b, _ in TABLE2 if b}
    # "Beyond 366 nm, aw1 and aw2 are identical": they meet at 370 nm.
    assert aw1[370] == aw2[370]
    # From 420 nm aw1 is Pope & Fry's (1997), shipped, at every 10 nm;
    # at 425, 435, 445 and 455 nm it is the mean of theirs 5 nm either
    # side, not their own value there (DATA.md section 46).
    with open(DATA_DIR / "pope1997_aw.csv", newline="") as handle:
        pope = {float(r["wavelength_nm"]): float(r["aw_per_m"])
                for r in csv.DictReader(handle)}
    for w in range(420, 501, 5):
        if w in MEANS:
            want = (pope[w - 5] + pope[w + 5]) / 2
        else:
            want = pope[w]
        assert abs(want - aw1[w]) <= 5.01e-6, (w, want, aw1[w])
    assert all(abs(pope[w] - aw1[w]) > 2e-5 for w in MEANS)
    columns = {name: values.split() for name, values in TABLE1}
    assert all(len(v) == 8 for v in columns.values())
    diff = {s: round(float(b) - float(a), 4) for s, a, b in zip(
        STATIONS, columns["ay1_310_per_m"], columns["ay2_310_per_m"])}
    expected = round(aw1[310] - aw2[310], 4)
    off = sorted(s for s, d in diff.items() if abs(d - expected) > 2e-4)
    assert off == sorted(SUSPECT_AY2), (off, diff, expected)
    return columns


def main() -> None:
    columns = check()
    out = DATA_DIR / "morel2007_aw.csv"
    with open(out, "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["wavelength_nm", "aw1_per_m", "aw2_per_m",
                         "bsw_per_m", "status", "note"])
        for w, a1, a2, b in TABLE2:
            writer.writerow([w, a1, a2, b, "ok", ""])
    report(out.name, len(TABLE2))
    out = DATA_DIR / "morel2007_stations.csv"
    names = [name for name, _ in TABLE1]
    with open(out, "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["station"] + names + ["status", "note"])
        for i, station in enumerate(STATIONS):
            suspect = station in SUSPECT_AY2
            writer.writerow([station] + [columns[n][i] for n in names]
                            + ["suspect" if suspect else "ok",
                               AY2_NOTE if suspect else ""])
    report(out.name, len(STATIONS))


if __name__ == "__main__":
    main()

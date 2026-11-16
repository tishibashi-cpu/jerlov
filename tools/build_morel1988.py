# -*- coding: utf-8 -*-
"""Transcribe Morel (1988) Table 2.

Morel, A. (1988), "Optical modeling of the upper ocean in relation to its
biogenous matter content (case I waters)", J. Geophys. Res. 93(C9),
10749-10768, doi:10.1029/JC093iC09p10749. Table 2 (p. 10,754) gives, every
5 nm from 400 to 700 nm, Kw of pure sea water and the coefficient chi and
exponent e of K = Kw + chi C^e (Eqs. 8 and 9), C the Chl a + Pheo a
concentration.

No input file is needed: the values are literals below, read from the page
image and checked against the text layer, and checked here before anything
is written. See DATA.md section 45 and DECISIONS.md section 101.
"""

import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import DATA_DIR, report  # noqa: E402

# (wavelength nm, Kw 1/m, chi, e), as printed, Table 2.
TABLE2 = [
    (400, "0.0209", "0.1100", "0.668"),
    (405, "0.0200", "0.1110", "0.672"),
    (410, "0.0196", "0.1125", "0.680"),
    (415, "0.0189", "0.1135", "0.687"),
    (420, "0.0183", "0.1126", "0.693"),
    (425, "0.0182", "0.1104", "0.701"),
    (430, "0.0171", "0.1078", "0.707"),
    (435, "0.0170", "0.1065", "0.708"),
    (440, "0.0168", "0.1041", "0.707"),
    (445, "0.0166", "0.0996", "0.704"),
    (450, "0.0168", "0.0971", "0.701"),
    (455, "0.0170", "0.0939", "0.699"),
    (460, "0.0173", "0.0896", "0.700"),
    (465, "0.0174", "0.0859", "0.703"),
    (470, "0.0175", "0.0823", "0.703"),
    (475, "0.0184", "0.0788", "0.703"),
    (480, "0.0194", "0.0746", "0.703"),
    (485, "0.0203", "0.0726", "0.704"),
    (490, "0.0217", "0.0690", "0.702"),
    (495, "0.0240", "0.0660", "0.700"),
    (500, "0.0271", "0.0636", "0.700"),
    (505, "0.0320", "0.0600", "0.695"),
    (510, "0.0384", "0.0578", "0.690"),
    (515, "0.0445", "0.0540", "0.685"),
    (520, "0.0490", "0.0498", "0.680"),
    (525, "0.0505", "0.0475", "0.675"),
    (530, "0.0518", "0.0467", "0.670"),
    (535, "0.0543", "0.0450", "0.665"),
    (540, "0.0568", "0.0440", "0.660"),
    (545, "0.0615", "0.0426", "0.655"),
    (550, "0.0640", "0.0410", "0.650"),
    (555, "0.0683", "0.0400", "0.645"),
    (560, "0.0717", "0.0390", "0.640"),
    (565, "0.0762", "0.0375", "0.630"),
    (570, "0.0807", "0.0360", "0.623"),
    (575, "0.0940", "0.0340", "0.615"),
    (580, "0.1070", "0.0330", "0.610"),
    (585, "0.1280", "0.0328", "0.614"),
    (590, "0.1570", "0.0325", "0.618"),
    (595, "0.2000", "0.0330", "0.622"),
    (600, "0.2530", "0.0340", "0.626"),
    (605, "0.2790", "0.0350", "0.630"),
    (610, "0.2960", "0.0360", "0.634"),
    (615, "0.3030", "0.0375", "0.638"),
    (620, "0.3100", "0.0385", "0.642"),
    (625, "0.3150", "0.0400", "0.647"),
    (630, "0.3200", "0.0420", "0.653"),
    (635, "0.3250", "0.0430", "0.658"),
    (640, "0.3300", "0.0440", "0.663"),
    (645, "0.3400", "0.0445", "0.667"),
    (650, "0.3500", "0.0450", "0.672"),
    (655, "0.3700", "0.0460", "0.677"),
    (660, "0.4050", "0.0475", "0.682"),
    (665, "0.4180", "0.0490", "0.687"),
    (670, "0.4300", "0.0515", "0.695"),
    (675, "0.4400", "0.0520", "0.697"),
    (680, "0.4500", "0.0505", "0.693"),
    (685, "0.4700", "0.0440", "0.665"),
    (690, "0.5000", "0.0390", "0.640"),
    (695, "0.5500", "0.0340", "0.620"),
    (700, "0.6500", "0.0300", "0.600"),
]
#: Beyond 650 nm chi and e "are only extracted from the mesotrophic and
#: eutrophic waters" (p. 10,755).
RED_NOTE = ("chi and e fitted to mesotrophic and eutrophic waters only "
            "(p. 10,755)")


def check() -> None:
    wl = [w for w, *_ in TABLE2]
    assert wl == list(range(400, 701, 5)), wl
    by_wl = {w: (float(k), float(c), float(e)) for w, k, c, e in TABLE2}
    # Fig. 7a plots K(450) - 0.0168 (p. 10,755): Kw(450).
    assert by_wl[450][0] == 0.0168
    # Morel & Maritorena (2001) Table 2, shipped: from 560 nm their chi
    # and e are these (DATA.md section 45).
    with open(DATA_DIR / "morel2001_kd.csv", newline="") as handle:
        later = {int(float(r["wavelength_nm"])): r
                 for r in csv.DictReader(handle)}
    for w in range(560, 701, 5):
        assert float(later[w]["chi_per_m"]) == by_wl[w][1], w
        assert float(later[w]["e_exponent"]) == by_wl[w][2], w
    assert float(later[555]["chi_per_m"]) != by_wl[555][1]


def main() -> None:
    check()
    out = DATA_DIR / "morel1988_kd.csv"
    with open(out, "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["wavelength_nm", "Kw_per_m", "chi_per_m",
                         "e_exponent", "status", "note"])
        for w, kw, chi, e in TABLE2:
            writer.writerow([w, kw, chi, e, "ok",
                             RED_NOTE if w > 650 else ""])
    report(out.name, len(TABLE2))


if __name__ == "__main__":
    main()

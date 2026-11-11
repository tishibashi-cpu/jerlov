# -*- coding: utf-8 -*-
"""Write the test data for the quasi-analytical algorithm.

Not a ``build_`` script: what it writes goes to ``tests/data/``, not into
the package.

Two inputs, both distributed by the IOCCG, kept in ``sources/ioccg/``:

- ``IOP_AOP_Sun30.xls``: the synthetic data set of IOCCG Report 5 (2006),
  chapter 2, with the sun 30 degrees from the zenith. 500 spectra, 400-800
  nm every 10 nm, from https://ioccg.org/what-we-do/ioccg-publications/
  ioccg-reports/synthesized-dataset-from-ioccg-report-5/. The IOCCG asks
  that it be cited as IOCCG (2006), Report 5.
- ``QAA_v6-202011.xlsm``: the spreadsheet distributed with
  ``qaa_v6_202011.pdf`` at https://ioccg.org/resources/software/. Only its
  cell values are read, the results its macro stored; the macro is not
  run.

Needs ``xlrd`` (the .xls) and ``openpyxl`` (the .xlsm), for this script
only. Writes ``tests/data/ioccg2006_sun30.csv``,
``tests/data/ioccg2006_pure_water.csv`` and
``tests/data/qaa_v6_spreadsheet.csv``; DECISIONS.md section 67, DATA.md
section 28.
"""

import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import ROOT, require  # noqa: E402

import openpyxl  # noqa: E402
import xlrd  # noqa: E402

OUT = ROOT / "tests" / "data"
IOCCG = ("https://ioccg.org/what-we-do/ioccg-publications/ioccg-reports/"
         "synthesized-dataset-from-ioccg-report-5/ (IOP_AOP_Sun30.xls) and\n"
         "  https://ioccg.org/resources/software/ (qaa_v6-202011.xlsm.zip)")

RRS_NM = (410, 440, 490, 510, 550, 560, 670)
A_NM = (410, 440, 490)
BB_NM = (440, 550, 560)
APH_NM = (440, 490)


def sheet(book, name):
    """(wavelengths, 500 rows) of one sheet: the header is row 9, column
    B on; the spectra rows 10-509."""
    sh = book.sheet_by_name(name)
    wl = [int(sh.cell_value(8, c)) for c in range(1, 42)]
    rows = [[sh.cell_value(r, c) for c in range(1, 42)]
            for r in range(9, 509)]
    if wl != list(range(400, 801, 10)) or len(rows) != 500:
        raise SystemExit(f"sheet {name!r} is not 500 spectra, 400-800 nm")
    return wl, rows


def main():
    book = xlrd.open_workbook(require("ioccg/IOP_AOP_Sun30.xls", IOCCG))
    wl, rrs = sheet(book, "Rrs")
    _, a = sheet(book, "a")
    _, bb = sheet(book, "bb")
    _, ag = sheet(book, "a_g")
    _, adm = sheet(book, "a_dm")
    _, aph = sheet(book, "a_ph")
    col = {w: i for i, w in enumerate(wl)}

    OUT.mkdir(parents=True, exist_ok=True)
    header = (["spectrum"] + [f"Rrs_{w}" for w in RRS_NM]
              + [f"a_{w}" for w in A_NM] + [f"bb_{w}" for w in BB_NM]
              + [f"adg_{w}" for w in A_NM] + [f"aph_{w}" for w in APH_NM])
    with open(OUT / "ioccg2006_sun30.csv", "w", newline="",
              encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(header)
        for i in range(500):
            row = [i + 1]
            row += [repr(rrs[i][col[w]]) for w in RRS_NM]
            row += [repr(a[i][col[w]]) for w in A_NM]
            row += [repr(bb[i][col[w]]) for w in BB_NM]
            row += [repr(ag[i][col[w]] + adm[i][col[w]]) for w in A_NM]
            row += [repr(aph[i][col[w]]) for w in APH_NM]
            wr.writerow(row)
    print(f"wrote {OUT / 'ioccg2006_sun30.csv'} (500 spectra)")

    basics = book.sheet_by_name("Basics")
    with open(OUT / "ioccg2006_pure_water.csv", "w", newline="",
              encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["wavelength_nm", "aw_per_m", "bbw_per_m"])
        n = 0
        for r in range(9, 50):
            w = int(basics.cell_value(r, 0))
            if 400 <= w <= 700:
                wr.writerow([w, repr(basics.cell_value(r, 1)),
                             repr(basics.cell_value(r, 2))])
                n += 1
    print(f"wrote {OUT / 'ioccg2006_pure_water.csv'} ({n} wavelengths)")

    wb = openpyxl.load_workbook(require("ioccg/QAA_v6-202011.xlsm", IOCCG),
                                data_only=True, keep_vba=False)
    rs, qa, dc = wb["Rrs"], wb["QAA_v6"], wb["Decompose_a"]
    names = (["Rrs_412", "Rrs_443", "Rrs_489", "Rrs_510", "Rrs_555",
              "Rrs_670", "eta", "bbp_555", "a_412", "a_443", "a_489",
              "a_510", "a_555", "adg_443", "aph_412", "aph_443", "aph_489",
              "aph_510", "aph_555"])
    n = 0
    with open(OUT / "qaa_v6_spreadsheet.csv", "w", newline="",
              encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["station"] + names)
        for r in range(15, 15 + 1000):
            stored = qa.cell(r, 68).value          # column BP
            if stored is None:
                break
            values = ([rs.cell(r, c).value for c in range(3, 9)]   # C-H
                      + [qa.cell(r, c).value for c in range(68, 75)]
                      + [dc.cell(r, c).value for c in range(28, 34)])
            wr.writerow([n + 1] + [repr(float(v)) for v in values])
            n += 1
    if n != 12:
        raise SystemExit(f"expected 12 stored stations, found {n}")
    print(f"wrote {OUT / 'qaa_v6_spreadsheet.csv'} ({n} stations)")


if __name__ == "__main__":
    main()

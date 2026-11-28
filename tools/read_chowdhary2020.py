"""Read Chowdhary et al.'s (2020) testbed tables S2a, S2b, S3a and S3b
(AOS-I and AOS-II just above the surface) from the article's supplementary
material: DECISIONS.md section 147, DATA.md section 54.

    J. Chowdhary, P.-W. Zhai, F. Xu, R. Frouin and D. Ramon (2020),
    J. Quant. Spectrosc. Radiat. Transfer 242, 106717,
    doi:10.1016/j.jqsrt.2019.106717; the supplement is Elsevier's
    1-s2.0-S002240731930370X-mmc2.docx (not shipped).

The tables are Word tables of text: each row holds two wavelengths side by
side (lambda, theta0, phi, vza, R_I scalar, R_I, R_Q, R_U), the first
column of a group given only on its first row. Straight up is one row
("N") between the two azimuths of a pair, kept here with the first
azimuth (0 or 60), whose plane Q and U are referred to. Values are copied
as printed.

    python tools/read_chowdhary2020.py SUPPLEMENT.docx OUT.csv
"""

from __future__ import annotations

import csv
import re
import sys
import zipfile

#: The tables, by their order in the document: (model, the sun's zenith).
WANTED = {6: ("AOS-I", 30), 7: ("AOS-I", 30), 8: ("AOS-I", 60),
          9: ("AOS-I", 60), 14: ("AOS-II", 30), 15: ("AOS-II", 30),
          16: ("AOS-II", 60), 17: ("AOS-II", 60)}


def _tables(xml: str) -> list[list[list[str]]]:
    out = []
    for tb in re.findall(r"<w:tbl>.*?</w:tbl>", xml, flags=re.S):
        rows = []
        for tr in re.findall(r"<w:tr[ >].*?</w:tr>", tb, flags=re.S):
            cells = []
            for tc in re.findall(r"<w:tc>.*?</w:tc>", tr, flags=re.S):
                ps = re.findall(r"<w:p[ >].*?</w:p>", tc, flags=re.S)
                cells.append(" | ".join(
                    "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", p))
                    for p in ps))
            rows.append(cells)
        out.append(rows)
    return out


def read(path: str) -> list[dict]:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf8")
    tables = _tables(xml)
    rows = []
    for k, (model, sun) in WANTED.items():
        lam, phi, plane = [0, 0], [0, 0], [0, 0]
        for r in tables[k][1:]:
            if len(r) < 17 or r[0] == "λ":
                continue
            for h in (0, 1):
                c = [x.strip() for x in r[9 * h: 9 * h + 8]]
                if c[0]:
                    lam[h] = int(re.match(r"(\d+)", c[0]).group(1))
                if c[1] and int(c[1]) != sun:
                    raise ValueError(f"table {k}: the sun {c[1]}")
                nadir = c[2].startswith("N")
                if c[2] and not nadir:
                    phi[h] = int(c[2])
                    if phi[h] in (0, 60):
                        plane[h] = phi[h]
                if not c[3]:
                    continue
                rows.append(dict(model=model, wavelength=lam[h], sun=sun,
                                 phi=plane[h] if nadir else phi[h],
                                 vza=int(c[3]), I_scalar=c[4], I=c[5],
                                 Q=c[6], U=c[7]))
    return rows


def main(src: str, dst: str) -> None:
    rows = read(src)
    with open(dst, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    else:
        sys.exit(__doc__)

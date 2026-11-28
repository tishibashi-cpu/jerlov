"""Read Chowdhary et al.'s (2020) testbed tables S2 to S5 (AOS-I to AOS-IV,
just above the surface and at the top of the atmosphere) and S1 (the
particles' scattering matrix) from the article's supplementary material:
DECISIONS.md sections 147 and 148, DATA.md section 54.

    J. Chowdhary, P.-W. Zhai, F. Xu, R. Frouin and D. Ramon (2020),
    J. Quant. Spectrosc. Radiat. Transfer 242, 106717,
    doi:10.1016/j.jqsrt.2019.106717; the supplement is Elsevier's
    1-s2.0-S002240731930370X-mmc2.docx (not shipped).

The tables are Word tables of text: each row holds two wavelengths side by
side (lambda, theta0, phi, vza, R_I scalar, R_I, R_Q, R_U), the first
column of a group given only on its first row. Straight up is one row
("N") between the two azimuths of a pair, kept here with the first
azimuth (0 or 60), whose plane Q and U are referred to. Values are copied
as printed, but for one decimal comma in Table S1a (F43 at 25 degrees,
"-0,00197102"), read as a point.

    python tools/read_chowdhary2020.py SUPPLEMENT.docx TABLES.csv PARTICLES.csv
"""

from __future__ import annotations

import csv
import re
import sys
import zipfile

#: The tables, by their order in the document: (model, level, the sun's
#: zenith), each in two parts (azimuths 0 and 180, then 60 and 240).
_ORDER = [("AOS-I", "SRF", 30), ("AOS-I", "SRF", 60), ("AOS-I", "TOA", 30),
          ("AOS-I", "TOA", 60), ("AOS-II", "SRF", 30), ("AOS-II", "SRF", 60),
          ("AOS-III", "SRF", 30), ("AOS-III", "SRF", 60),
          ("AOS-III", "TOA", 30), ("AOS-III", "TOA", 60),
          ("AOS-IV", "SRF", 30), ("AOS-IV", "SRF", 60),
          ("AOS-IV", "TOA", 30), ("AOS-IV", "TOA", 60)]
WANTED = {6 + 2 * i + part: key for i, key in enumerate(_ORDER)
          for part in (0, 1)}
#: Tables S1a ([Chl] 0.03 mg m^-3) and S1b (3 mg m^-3), three parts each.
PARTICLES = {0: "S1a", 1: "S1a", 2: "S1a", 3: "S1b", 4: "S1b", 5: "S1b"}


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
    for k, (model, level, sun) in WANTED.items():
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
                rows.append(dict(model=model, level=level,
                                 wavelength=lam[h], sun=sun,
                                 phi=plane[h] if nadir else phi[h],
                                 vza=int(c[3]), I_scalar=c[4], I=c[5],
                                 Q=c[6], U=c[7]))
    return rows


def read_particles(path: str) -> list[dict]:
    """Tables S1a and S1b: F11, F21, F33 and F43 over 4 pi by angle."""
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf8")
    tables = _tables(xml)
    rows = []
    for k, table in PARTICLES.items():
        for r in tables[k][2:]:
            if len(r) < 11:
                continue
            for h in (0, 1):
                c = [x.strip() for x in r[6 * h: 6 * h + 5]]
                if not c[0] or not c[0][0].isdigit():
                    continue
                c = [x.replace(",", ".") for x in c]
                rows.append(dict(table=table, angle=c[0], F11=c[1],
                                 F21=c[2], F33=c[3], F43=c[4]))
    rows.sort(key=lambda r: (r["table"], float(r["angle"])))
    return rows


def _write(rows: list[dict], dst: str) -> None:
    with open(dst, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(src: str, dst: str, particles: str) -> None:
    _write(read(src), dst)
    _write(read_particles(src), particles)


if __name__ == "__main__":
    if len(sys.argv) == 4:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)

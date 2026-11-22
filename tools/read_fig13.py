"""Read the filled symbols of Morel, Antoine & Gentili's (2002) Fig. 13 at
0.03 and 0.1 mg/m3: DECISIONS.md section 118.

Morel, A., Antoine, D. and Gentili, B. (2002), Appl. Opt. 41(30),
6289-6306, doi:10.1364/AO.41.006289, Fig. 13 (p. 6301): f0/f against Chl,
the sun at 0, 15, 30, 45 and 75 degrees, one symbol per wavelength.

    python tools/read_fig13.py PDF [OUT.csv]

PDF is your own copy of the paper as Optica distributes it (MD5 below; not
shipped). Fig. 13 is embedded in page 13 as a one-bit image at 300 pixels
per inch; poppler's ``pdfimages`` takes it out, and the rest is numpy:

- the f0/f axis is calibrated, linearly in pixels, from the left axis's
  tick marks labelled 1.0 and 0.6; the Chl axis, logarithmically, from
  the bottom axis's ticks labelled 0.1 and 10;
- the filled symbols (every wavelength but 442.5 nm, a cross) are what
  survives an erosion by a 5 x 5 square, which removes the one-pixel
  hatching of the shaded bands and the crosses;
- the blobs whose centres lie within ``HALF_WIDTH`` pixels of the column
  at 0.03 or 0.1 mg/m3 are kept, except those inside the legend.

Symbols that touch are one blob, so each row gives a blob's top and bottom
as f0/f, and its centre. A symbol of the figure is drawn at a value if
some blob of its column spans it: an eroded blob holds the centre of every
symbol it is made of. Without OUT.csv the rows are printed.
"""

from __future__ import annotations

import csv
import hashlib
import pathlib
import subprocess
import sys
import tempfile

import numpy as np

#: The user's copy of the paper (536,070 bytes).
MD5 = "1daf887204a1cb949ec62b15544f082e"
#: Fig. 13 is the second image on page 13, 863 x 846 pixels.
PAGE, INDEX, SHAPE = 13, 1, (846, 863)
#: The erosion's square, pixels.
ERODE = 5
#: How far from a column's tick a blob's centre may lie, pixels.
HALF_WIDTH = 12
#: The legend's box, (rows, columns) in pixels, read off the image: its
#: symbols stand in the 0.03 column's line below the data.
LEGEND = ((470, 700), (140, 400))
COLUMNS = (0.03, 0.1)
FIELDS = ("chl_mg_m3", "top_f0_over_f", "bottom_f0_over_f",
          "centre_f0_over_f", "pixels")


def _pbm(path):
    """A raw PBM (P4) as a boolean array, True where there is ink."""
    raw = path.read_bytes()
    magic, width, height, data = raw.split(maxsplit=3)
    if magic != b"P4":
        raise ValueError(f"{path} is not a raw PBM")
    w, h = int(width), int(height)
    bits = np.unpackbits(np.frombuffer(data, np.uint8)).reshape(h, -1)[:, :w]
    bits = bits.astype(bool)
    # pdfimages writes the stencil's mask; the ink is the minority.
    return bits if bits.mean() < 0.5 else ~bits


def image(pdf):
    pdf = pathlib.Path(pdf)
    digest = hashlib.md5(pdf.read_bytes()).hexdigest()
    if digest != MD5:
        raise SystemExit(f"{pdf}: MD5 {digest}, not the copy read for "
                         f"DECISIONS.md section 118 ({MD5})")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdfimages", "-f", str(PAGE), "-l", str(PAGE),
                        str(pdf), str(pathlib.Path(tmp) / "p")], check=True)
        ink = _pbm(pathlib.Path(tmp) / f"p-{INDEX:03d}.pbm")
    if ink.shape != SHAPE:
        raise SystemExit(f"Fig. 13 is {ink.shape}, expected {SHAPE}")
    return ink


def _runs(mask):
    """Centres of the runs of True in a 1-D mask."""
    idx = np.flatnonzero(mask)
    if idx.size == 0:
        return []
    groups = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
    return [float(g.mean()) for g in groups]


def axes(ink):
    """(rows of the ticks at 1.0 and 0.6, columns of those at 0.1 and 10,
    the row of the bottom frame line)."""
    cols = ink.sum(axis=0)
    rows = ink.sum(axis=1)
    left = int(np.argmax(cols[: SHAPE[1] // 2]))
    bottom = int(np.argmax(rows[SHAPE[0] // 2:])) + SHAPE[0] // 2
    # The left frame line is three pixels wide; ticks stand out left of it.
    frame_left = left - 1
    while ink[:, frame_left - 1].sum() > SHAPE[0] // 2:
        frame_left -= 1
    band = ink[:, frame_left - 11: frame_left].sum(axis=1)
    major_rows = _runs(band >= 9)              # labelled ticks, 11 px long
    frame_bottom = bottom + 1
    while ink[frame_bottom + 1].sum() > SHAPE[1] // 2:
        frame_bottom += 1
    band = ink[frame_bottom + 1: frame_bottom + 14].sum(axis=0)
    major_cols = _runs(band >= 10)             # labelled ticks, 12 px long
    if len(major_rows) != 5 or len(major_cols) != 3:
        raise SystemExit(f"ticks found: rows {major_rows}, cols {major_cols}")
    return ((major_rows[0], major_rows[-1]), (major_cols[0], major_cols[-1]),
            bottom)


def erode(ink, k=ERODE):
    h, w = ink.shape
    core = np.ones((h - k + 1, w - k + 1), bool)
    for dy in range(k):
        for dx in range(k):
            core &= ink[dy: dy + h - k + 1, dx: dx + w - k + 1]
    out = np.zeros_like(ink)
    out[k // 2: k // 2 + core.shape[0], k // 2: k // 2 + core.shape[1]] = core
    return out


def blobs(mask):
    """Each 8-connected blob's pixel rows and columns."""
    seen = np.zeros(mask.shape, bool)
    found = []
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]:
            continue
        seen[y, x] = True
        stack, pixels = [(y, x)], []
        while stack:
            a, b = stack.pop()
            pixels.append((a, b))
            for da in (-1, 0, 1):
                for db in (-1, 0, 1):
                    c, d = a + da, b + db
                    if (0 <= c < mask.shape[0] and 0 <= d < mask.shape[1]
                            and mask[c, d] and not seen[c, d]):
                        seen[c, d] = True
                        stack.append((c, d))
        found.append(np.array(pixels))
    return found


def read(pdf):
    ink = image(pdf)
    (y10, y06), (x01, x10), bottom = axes(ink)
    core = erode(ink)
    # The frame, its ticks and labels are not symbols.
    core[: int(y10) - 30] = False
    core[bottom - 3:] = False
    core[:, : int(x01) - 140] = False
    (r0, r1), (c0, c1) = LEGEND
    core[r0:r1, c0:c1] = False

    def value(row):
        return 1.0 - 0.4 * (row - y10) / (y06 - y10)

    def column(chl):
        return x01 + (x10 - x01) * (np.log10(chl) + 1) / 2

    out = []
    for chl in COLUMNS:
        x = column(chl)
        for p in blobs(core):
            if abs(p[:, 1].mean() - x) <= HALF_WIDTH:
                out.append(dict(
                    chl_mg_m3=chl,
                    top_f0_over_f=round(float(value(p[:, 0].min())), 4),
                    bottom_f0_over_f=round(float(value(p[:, 0].max())), 4),
                    centre_f0_over_f=round(float(value(p[:, 0].mean())), 4),
                    pixels=int(len(p))))
    out.sort(key=lambda r: (r["chl_mg_m3"], -r["top_f0_over_f"]))
    return out


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    rows = read(argv[0])
    if len(argv) > 1:
        with open(argv[1], "w", newline="") as f:
            w = csv.DictWriter(f, FIELDS, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    else:
        for r in rows:
            print(r)


if __name__ == "__main__":
    main(sys.argv[1:])

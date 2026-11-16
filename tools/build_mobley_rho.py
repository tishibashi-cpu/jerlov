"""Build jerlov/data/mobley1999_rho.csv and mobley2015_rho.csv.

The sea surface reflectance factors rho of Mobley (1999), Appl. Opt. 38,
7442-7455, and Mobley (2015), Appl. Opt. 54, 4828-4849, as the Ocean Optics
Web Book distributes them ("Surface Reflectance Factors", Creative Commons
Attribution licence): rhoTable_AO1999.txt and rhoTable_AO2015.txt
(DECISIONS.md section 99, DATA.md section 43).

The values are copied as the files print them; only the layout changes.
The 1999 file's Theta (direction of photon travel from the zenith) is the
radiometer's angle from the nadir, and its Phi-view the azimuth from the
sun; the 2015 file gives both directly. Every check below must pass before
anything is written.
"""

from __future__ import annotations

import csv
import hashlib
import re

from _common import DATA_DIR, report, require

ORIGIN = (
    "the Ocean Optics Web Book, page 'Surface Reflectance Factors',\n"
    "  https://www.oceanopticsbook.info/view/remote-sensing/level-3/"
    "surface-reflectance-factors\n"
    "  (the links 'original rho table' and 'revised rho table')."
)
FILES = {
    "mobley1999": ("mobley_rho/rhoTable_AO1999.txt",
                   "aefcb0da753be57f5e84cdd6951ba76a"),
    "mobley2015": ("mobley_rho/rhoTable_AO2015.txt",
                   "b24599f57b205435eaf95c161d624cf9"),
}
OUTPUTS = {"mobley1999": DATA_DIR / "mobley1999_rho.csv",
           "mobley2015": DATA_DIR / "mobley2015_rho.csv"}
NADIR = (0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 87.5)
AZIMUTH = tuple(15.0 * k for k in range(13))
#: The directions of each block: the nadir cap once, then every ring.
DIRECTIONS = [(0.0, 0.0)] + [(n, a) for n in NADIR[1:] for a in AZIMUTH]
GRID = {
    "mobley1999": ((0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0),
                   tuple(10.0 * k for k in range(9))),
    "mobley2015": ((0.0, 2.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 14.0, 15.0),
                   tuple(10.0 * k for k in range(9)) + (87.5,)),
}


def parse_1999(text: str):
    rows, key = [], None
    for line in text.splitlines():
        m = re.match(r"rho for WIND SPEED =\s*([\d.]+) m/s\s+"
                     r"THETA_SUN =\s*([\d.]+) deg", line.strip())
        if m:
            key = (m[1], m[2])
            continue
        f = line.split()
        if key and len(f) == 6 and f[0].isdigit():
            theta, phi, phi_view, rho = f[2], f[3], f[4], f[5]
            # Phi is the photons' azimuth; the sun's photons travel at 180.
            assert abs(float(phi) + float(phi_view) - 180.0) < 1e-9 \
                or (float(theta) == 0.0 and float(phi) == 0.0), line
            rows.append((*key, theta, phi_view, rho))
    return rows


def parse_2015(text: str):
    rows, key = [], None
    for line in text.splitlines():
        m = re.match(r"WIND SPEED =\s*([\d.]+); SUN ZENITH ANGLE =\s*"
                     r"([\d.]+)", line.strip())
        if m:
            key = (m[1], m[2])
            continue
        f = line.split()
        if key and len(f) == 3:
            try:
                float(f[2])
            except ValueError:
                continue
            rows.append((*key, f[0], f[1], f[2]))
    return rows


def check(source: str, rows) -> None:
    winds, suns = GRID[source]
    expected = [(w, s, n, a) for w in winds for s in suns
                for n, a in DIRECTIONS]
    got = [tuple(float(v) for v in r[:4]) for r in rows]
    # Every point once; the files differ in the order of the azimuths.
    assert len(got) == len(set(got)) == len(expected), (source, len(got))
    assert set(got) == set(expected), source
    values = [float(r[4]) for r in rows]
    assert all(0 < v < 3 for v in values), (source, min(values),
                                             max(values))
    print(f"{source}: {len(rows)} values, {len(winds)} winds, "
          f"{len(suns)} suns, rho {min(values):.4g}-{max(values):.4g}")


def main() -> None:
    for source, (relative, digest) in FILES.items():
        path = require(relative, ORIGIN)
        raw = path.read_bytes()
        got = hashlib.md5(raw).hexdigest()
        if got != digest:
            raise SystemExit(f"{path}: MD5 {got}, expected {digest}")
        text = raw.decode("ascii")
        rows = (parse_1999 if source == "mobley1999" else parse_2015)(text)
        check(source, rows)
        out = OUTPUTS[source]
        with open(out, "w", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(["wind_speed", "sun_zenith_deg",
                             "view_nadir_deg", "view_azimuth_deg", "rho"])
            for wind, sun, nadir, azimuth, rho in rows:
                # The value as printed; the angles as numbers.
                writer.writerow([f"{float(wind):g}", f"{float(sun):g}",
                                 f"{float(nadir):g}", f"{float(azimuth):g}",
                                 rho])
        report(out.name, len(rows))


if __name__ == "__main__":
    main()

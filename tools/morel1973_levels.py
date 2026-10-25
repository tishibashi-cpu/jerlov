"""The 10 and 1 percent levels of Morel's measured profiles of quanta.

Test A of DECISIONS.md section 58: the same question as section 55 asked of
Nygård's profiles, asked of Morel's, taken on the same cruise with another
quanta meter and another surface correction.

    python tools/morel1973_levels.py

`morel1973_quanta.csv`, beside this script, is the downwelling quanta from
Morel's tables (vol. I, section F), read from the page images: page,
station, set, depth (m) and the quanta as a percentage of the value above
the surface, corrected by Morel to a constant surface irradiance. A depth
printed twice, at two gain settings, has two rows. The table is not part of
the package.

    Morel, A. (1973), Measurements of spectral and total radiant flux, in
    Tyler, J. E. (ed.), Data Report, SCOR Discoverer Expedition, May 1970,
    vol. I, section F, SIO Ref. 73-16, Visibility Laboratory, Scripps
    Institution of Oceanography.
"""

from __future__ import annotations

import csv
import math
import pathlib
import statistics

TABLE = pathlib.Path(__file__).resolve().parent / "morel1973_quanta.csv"

#: The share of the light above the surface taken to be just below it.
SURFACE = 0.96
#: The range of that share the result must hold over.
SURFACE_RANGE = (0.92, 0.94, 0.96, 0.98, 1.00)
IB_LIKE_M = (28.5, 37.0)


def read(path=TABLE) -> dict[tuple[int, int], dict[float, float]]:
    """(station, set) -> depth -> mean ln(percent of the value above)."""
    logs: dict[tuple[int, int], dict[float, list[float]]] = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            (logs.setdefault((int(r["station"]), int(r["set"])), {})
                 .setdefault(float(r["depth_m"]), [])
                 .append(math.log(float(r["percent_of_above_surface"]))))
    return {key: {z: sum(v) / len(v) for z, v in by_z.items()}
            for key, by_z in logs.items()}


def levels(profile: dict[float, float], surface: float = SURFACE):
    """Depths of 10 and 1 percent of the light just below the surface."""
    below = math.log(100.0 * surface)
    points = [(0.0, below)] + sorted(profile.items())
    found = {}
    for fraction in (0.10, 0.01):
        target = below + math.log(fraction)
        found[fraction] = None
        for (z1, a), (z2, b) in zip(points, points[1:]):
            if a >= target > b:
                found[fraction] = z1 + (target - a) * (z2 - z1) / (b - a)
                break
    return found


def ib_like(z10) -> bool:
    return z10 is not None and IB_LIKE_M[0] < z10 <= IB_LIKE_M[1]


def ib_ratios(sets, surface: float = SURFACE):
    out = []
    for key, profile in sorted(sets.items()):
        if len(profile) < 3:
            continue
        lv = levels(profile, surface)
        if ib_like(lv[0.10]) and lv[0.01] is not None:
            out.append((key, lv[0.01] / lv[0.10]))
    return out


def main() -> None:
    sets = read()
    print(f"{len(sets)} downwelling sets")
    for (station, number), profile in sorted(sets.items()):
        lv = levels(profile)

        def show(z):
            return "    -" if z is None else f"{z:5.1f}"

        ratio = (lv[0.01] / lv[0.10]
                 if lv[0.01] is not None and lv[0.10] is not None else None)
        print(f"station {station:2d} set {number}: z(10) {show(lv[0.10])} "
              f"z(1) {show(lv[0.01])} "
              f"{'' if ratio is None else f'ratio {ratio:.2f}'}")
    for surface in SURFACE_RANGE:
        found = ib_ratios(sets, surface)
        rs = [r for _, r in found]
        median = statistics.median(rs) if rs else float("nan")
        print(f"t = {surface:.2f}: {len(rs)} IB-like, "
              f"median z(1) / z(10) {median:.2f} "
              f"({', '.join(f'{s}/{n} {r:.2f}' for (s, n), r in found)})")


if __name__ == "__main__":
    main()

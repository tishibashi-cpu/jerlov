"""The 10 and 1 percent levels of Nygård's measured profiles of quanta.

The analysis of DECISIONS.md section 55, which asks whether water as clear
as Jerlov's IB loses its light below the 10 percent level as fast as the
1977 classification says (z(1) / z(10) = 2.12) or as slowly as the spectral
Kd in this package says (2.49).

    python tools/nygard1973_levels.py

`nygard1973_quanta.csv`, beside this script, is Nygård's downwelling quantum
irradiance, in the order printed: page, station, depth (m), Q (1e18 quanta
m-2 s-1) and the deck monitor (relative units; a printed range as its
midpoint). It was drafted from the scan's text layer and every page compared
with its image; depths and Q are as printed, slips included. The monitor
column was checked against the images only for the lowerings the test
counts. `break` marks where the instrument changes without a 0 m reading,
and `not_a_start` a 0 m reading that closes one cast while the next reading
is much later or deep. The table is not part of the package.

    Nygård, K. (1973), Direct measurement of quanta, in Tyler, J. E. (ed.),
    Data Report, SCOR Discoverer Expedition, May 1970, vol. II, pp. I-1 to
    I-85, SIO Ref. 73-16, Visibility Laboratory, Scripps Institution of
    Oceanography.
"""

from __future__ import annotations

import csv
import math
import pathlib
import statistics

TABLE = pathlib.Path(__file__).resolve().parent / "nygard1973_quanta.csv"

#: How far below the deepest reading so far a lowering may come back up.
TURN_M = 6.0
#: Table 2's neighbours of IB at the 10 percent level, II 24 m and IA 41 m,
#: halfway to IB's 33 m.
IB_LIKE_M = (28.5, 37.0)


def read(path=TABLE) -> list[dict]:
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            rows.append({
                "page": r["page"], "station": int(r["station"]),
                "depth": float(r["depth_m"]), "q": float(r["quanta"]),
                "monitor": float(r["monitor"]) if r["monitor"] else None,
                "break": r["break"] == "1",
                "not_a_start": r["not_a_start"] == "1",
            })
    return rows


def lowerings(rows: list[dict]) -> list[list[dict]]:
    """Each lowering, from its 0 m reading to where it turns back up."""
    by_station: dict[int, list[dict]] = {}
    for r in rows:
        by_station.setdefault(r["station"], []).append(r)
    found = []
    for station_rows in by_station.values():
        for i, (here, after) in enumerate(zip(station_rows,
                                              station_rows[1:])):
            if (here["depth"] != 0 or here["not_a_start"]
                    or after["depth"] <= 0 or after["break"]):
                continue
            lowering, deepest = [here], 0.0
            for r in station_rows[i + 1:]:
                if r["break"] or r["depth"] < deepest - TURN_M:
                    break
                lowering.append(r)
                deepest = max(deepest, r["depth"])
            if len({r["depth"] for r in lowering}) >= 3:
                found.append(lowering)
    return found


def levels(lowering: list[dict], *, monitor: bool = False):
    """Depths of 10 and 1 percent, None where the lowering does not reach.

    ln Q is averaged at each depth and interpolated linearly in depth. With
    ``monitor``, each reading is first scaled by the monitor at the start
    over the monitor at the reading, the last one given standing for
    readings without one.
    """
    start = next((r["monitor"] for r in lowering
                  if r["monitor"] is not None), None)
    if monitor and start is None:
        return None
    current = start
    by_depth: dict[float, list[float]] = {}
    for r in lowering:
        if r["monitor"] is not None:
            current = r["monitor"]
        q = r["q"] * (start / current if monitor else 1.0)
        by_depth.setdefault(r["depth"], []).append(math.log(q))
    profile = sorted((z, sum(v) / len(v)) for z, v in by_depth.items())
    surface = profile[0][1]
    found = {}
    for fraction in (0.10, 0.01):
        target = math.log(fraction)
        found[fraction] = None
        for (z1, a), (z2, b) in zip(profile, profile[1:]):
            a, b = a - surface, b - surface
            if a >= target > b:
                found[fraction] = z1 + (target - a) * (z2 - z1) / (b - a)
                break
    return found


def ib_like(z10) -> bool:
    return z10 is not None and IB_LIKE_M[0] < z10 <= IB_LIKE_M[1]


def main() -> None:
    rows = read()
    print(f"{len(rows)} readings")
    print(" station  page   z(10)   z(1)  ratio   with the monitor")
    ratios, scaled = [], []
    for lowering in lowerings(rows):
        plain = levels(lowering)
        mon = levels(lowering, monitor=True)
        z10, z1 = plain[0.10], plain[0.01]

        def show(z):
            return "    -" if z is None else f"{z:5.1f}"

        ratio = z1 / z10 if z1 and z10 else None
        print(f"{lowering[0]['station']:8d} {lowering[0]['page']:>5} "
              f"{show(z10)}  {show(z1)}  "
              f"{'    -' if ratio is None else f'{ratio:5.2f}'}   "
              f"{show(mon[0.10])} {show(mon[0.01])}")
        if ib_like(z10) and z1:
            ratios.append(ratio)
        if mon and ib_like(mon[0.10]) and mon[0.01]:
            scaled.append(mon[0.01] / mon[0.10])
    print(f"\nIB-like lowerings that reach 1 percent: {len(ratios)}")
    print(f"z(1) / z(10): {', '.join(f'{r:.2f}' for r in ratios)}; "
          f"median {statistics.median(ratios):.2f} "
          "(Table 2: 2.12; the package: 2.49)")
    print(f"with the monitor: median {statistics.median(scaled):.2f} "
          f"of {len(scaled)}")


if __name__ == "__main__":
    main()

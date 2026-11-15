"""Williamson & Hollins's IOPs against Jerlov's Kd, by Monte Carlo:
DECISIONS.md section 92.

    python tools/kd_closure.py

Runs tools/kd_monte_carlo.py for six Jerlov types at the twelve wavelengths
Jerlov printed inside Williamson & Hollins's measured 412-715 nm, then
varies the sun, the Petzold station and the pure water one at a time on IB
and III, and writes examples/data/kd_closure/runs.csv: every run's
parameters, seed and Kd. About forty minutes on four cores. Each run is
seeded, so running it again on the same NumPy gives the same file.
"""

from __future__ import annotations

import concurrent.futures
import csv
import pathlib
import sys
import warnings

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import jerlov  # noqa: E402
import kd_monte_carlo as mc  # noqa: E402

OUT = (pathlib.Path(__file__).resolve().parent.parent / "examples" / "data"
       / "kd_closure")
TYPES = ("IB", "II", "III", "1C", "3C", "5C")
WAVELENGTHS = tuple(range(425, 701, 25))
FACTOR_TYPES = ("IB", "III")
BASE = dict(sun_deg=30.0, pure_water="williamson2022")
PHOTONS = 400_000
RANGES = {"pope1997": (380, 727.5), "mason2016": (250, 550),
          "lee2015": (350, 550)}


def nearest_station(water_type: str) -> str:
    b = float(jerlov.water(water_type).b(530.0))
    return min(jerlov.PETZOLD_STATIONS,
               key=lambda s: abs(jerlov.petzold_scattering(s).b - b))


def runs():
    out = []

    def add(factor, value, water_type, wavelength, **changes):
        run = {**BASE, "station": nearest_station(water_type), **changes}
        out.append(dict(run_id=len(out), factor=factor, value=value,
                        water_type=water_type, wavelength_nm=wavelength,
                        **run))

    for water_type in TYPES:
        for wl in WAVELENGTHS:
            add("base", "", water_type, wl)
    for water_type in FACTOR_TYPES:
        for wl in WAVELENGTHS:
            for sun in (0.0, 60.0):
                add("sun_deg", f"{sun:g}", water_type, wl, sun_deg=sun)
            for station in ("AUTEC 8", "HAOCE 5", "NUC 2200"):
                add("station", station, water_type, wl, station=station)
            for source, (low, high) in RANGES.items():
                if low <= wl <= high:
                    add("pure_water", source, water_type, wl,
                        pure_water=source)
    return out


def iops(run):
    """a and b for a run: the type's own, or its contents on another aw."""
    wl = float(run["wavelength_nm"])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        water = jerlov.water(run["water_type"])
        a = float(water.a(wl))
        b = float(water.b(wl))
        if run["pure_water"] != "williamson2022":
            a += (float(jerlov.pure_water_absorption_table(
                wl, source=run["pure_water"]))
                - float(jerlov.pure_water_absorption(wl)))
    return a, b


def one(run):
    a, b = iops(run)
    sample, _ = mc.petzold_sampler(run["station"])
    k1, k10 = mc.kd(a, b, sample, run["sun_deg"],
                    optical_depths=(1.0, 2.302585092994046),
                    photons=PHOTONS, seed=run["run_id"] + 1)
    return run, a, b, k1, k10


def main() -> None:
    plan = runs()
    print(f"{len(plan)} runs")
    results = []
    with concurrent.futures.ProcessPoolExecutor(4) as pool:
        for n, result in enumerate(pool.map(one, plan), 1):
            results.append(result)
            if n % 20 == 0:
                print(f"  {n} done")
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "runs.csv", "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["run_id", "factor", "value", "water_type",
                         "wavelength_nm", "sun_deg", "station",
                         "pure_water", "a", "b", "seed", "photons",
                         "kd_first_penetration_depth", "kd_to_10_percent"])
        for run, a, b, k1, k10 in results:
            writer.writerow([run["run_id"], run["factor"], run["value"],
                             run["water_type"], run["wavelength_nm"],
                             f"{run['sun_deg']:g}", run["station"],
                             run["pure_water"], repr(a), repr(b),
                             run["run_id"] + 1, PHOTONS, repr(k1),
                             repr(k10)])
    print(f"wrote {OUT / 'runs.csv'} ({len(results)} runs)")


if __name__ == "__main__":
    main()

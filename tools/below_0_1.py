"""What Kd rests on Petzold's extension below 0.1 degree: DECISIONS.md
section 96.

    python tools/below_0_1.py

For each of Petzold's eight stations, a = 0.1 per m, b/a of 0.5, 1, 3 and
10, the sun at 30 degrees and no sky, Kd over the first penetration depth
by tools/kd_monte_carlo.py three ways, with the same seed:

- ``as_shipped``: the phase function with the report's extension below 0.1
  degree, and b;
- ``unscattered``: without the extension, and b (1 - f), f the share of b
  below 0.1 degree: the light scattered by less than 0.1 degree is treated
  as not scattered at all;
- ``spread``: without the extension, and b kept: that light is spread over
  0.1 to 180 degrees.

Writes examples/data/below_0_1/runs.csv. A few minutes on four cores.
"""

from __future__ import annotations

import concurrent.futures
import csv
import pathlib
import sys
import warnings

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import jerlov  # noqa: E402
import kd_monte_carlo as mc  # noqa: E402

OUT = ROOT / "examples" / "data" / "below_0_1"
A = 0.1
RATIOS = (0.5, 1.0, 3.0, 10.0)
SUN = 30.0
PHOTONS = 400_000
VARIANTS = ("as_shipped", "unscattered", "spread")


def runs():
    out = []
    for case, (station, ratio) in enumerate(
            (s, r) for s in jerlov.PETZOLD_STATIONS for r in RATIOS):
        f = jerlov.petzold_scattering(station).fraction_below_0_1_deg
        for variant in VARIANTS:
            b = A * ratio * ((1.0 - f) if variant == "unscattered" else 1.0)
            out.append(dict(run_id=len(out), station=station,
                            b_over_a=ratio, variant=variant, a=A, b=b,
                            fraction_below_0_1_deg=f, seed=case + 1))
    return out


def one(run):
    sample, _ = mc.petzold_sampler(
        run["station"], without_extension=run["variant"] != "as_shipped")
    (k,) = mc.kd(run["a"], run["b"], sample, SUN, photons=PHOTONS,
                 seed=run["seed"])
    return run, k


def main() -> None:
    plan = runs()
    with concurrent.futures.ProcessPoolExecutor(4) as pool:
        results = list(pool.map(one, plan))
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "runs.csv", "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["run_id", "station", "b_over_a", "variant", "a",
                         "b", "fraction_below_0_1_deg", "sun_deg", "seed",
                         "photons", "kd_first_penetration_depth"])
        for run, k in results:
            writer.writerow([run["run_id"], run["station"],
                             f"{run['b_over_a']:g}", run["variant"],
                             repr(run["a"]), repr(run["b"]),
                             repr(run["fraction_below_0_1_deg"]),
                             f"{SUN:g}", run["seed"], PHOTONS, repr(k)])
    print(f"wrote {OUT / 'runs.csv'} ({len(results)} runs)")


if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        main()

"""jerlov.monte_carlo_light_field against tools/shallow_rrs_mc.py's stored
runs: DECISIONS.md section 138, check 4.

Every run of examples/data/shallow_rrs_mc/monte_carlo.csv with a bottom
(243), with the same water, NUC 2240's phase function, the same cut of 1
degree and the same sun, by the package's function (20 000 photons in
each of 10 batches, seed 1). The transports differ in two ways, said
here: the tool turns particles by NUC 2240's whole vsf, the package by
its vsf less pure water's (salinity 37); the tool starts its photons
just below the surface, the package thins them by Fresnel's
transmittance, which cancels in rrs.

The first is not small: the whole vsf counts pure water's scattering
twice, once in it and once on its own, so the tool's particles
backscatter more. ``--same-phase`` adds a second run of each, by the
package's engine with the particles turned by the whole vsf as the tool
does (DECISIONS.md section 138's result).

    python tools/monte_carlo_check.py OUT.csv
    python tools/monte_carlo_check.py --same-phase CSV
"""

from __future__ import annotations

import csv
import math
import pathlib
import sys

import jerlov

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNS = ROOT / "examples" / "data" / "shallow_rrs_mc" / "monte_carlo.csv"
PHOTONS, BATCHES, SEED = 20_000, 10, 1
SALINITY_PSU = 37.0
CUT_DEG = 1.0


def run(row: dict, phase) -> tuple[float, float]:
    a, bp, bw = float(row["a"]), float(row["bp"]), float(row["bw"])
    out = jerlov.monte_carlo_light_field(
        a, bp + bw, wavelength_nm=phase.wavelength_nm, pure_water_b=bw,
        salinity_psu=SALINITY_PSU, phase_function=phase,
        station_salinity_psu=SALINITY_PSU, cut_deg=CUT_DEG,
        refractive_index=1.34, sun_zenith_deg=float(row["sun_deg"]),
        depth_m=float(row["depth_m"]), bottom_albedo=float(row["albedo"]),
        depths_m=[0.25], slab_m=0.5, zenith_step_deg=10.0,
        azimuth_step_deg=45.0, photons=PHOTONS, batches=BATCHES, seed=SEED)
    return out.rrs, out.rrs_se


def run_same_phase(row: dict, phase) -> tuple[float, float]:
    """The package's engine, with NUC 2240's whole vsf for the particles,
    as the tool takes it."""
    import numpy as np
    from jerlov import monte_carlo as mc
    grid = np.geomspace(CUT_DEG, 180.0, 3000)
    grid[-1] = 180.0
    whole = np.asarray(phase.vsf_at(grid))
    cdf, cos_angle, measured = mc._inverse_cdf(grid, whole)
    particles = dict(cdf=cdf, cos=cos_angle, straight=1 - measured / phase.b,
                     angles=np.radians(grid), per_sr=whole / phase.b)
    water = mc._water_phase(phase.wavelength_nm, SALINITY_PSU)
    a, bp, bw = float(row["a"]), float(row["bp"]), float(row["bw"])
    values = [mc._simulate(a, bp + bw, bw, particles, water,
                           float(row["sun_deg"]), SEED + k, photons=PHOTONS,
                           depths=np.array([0.25]), half_slab=0.25,
                           n_water=1.34, d_zenith=10.0, d_azimuth=45.0,
                           depth=float(row["depth_m"]),
                           albedo=float(row["albedo"]))["rrs"]
              for k in range(BATCHES)]
    return (float(np.mean(values)),
            float(np.std(values, ddof=1) / math.sqrt(BATCHES)))


def same_phase(path: str) -> None:
    phase = jerlov.petzold_scattering("NUC 2240")
    with open(path) as handle:
        rows = list(csv.DictReader(handle))
    for r in rows:
        value, error = run_same_phase(r, phase)
        r["same_phase"] = f"{value:.6e}"
        r["same_phase_se"] = f"{error:.2e}"
        r["same_phase_z"] = (
            f"{(value - float(r['tool'])) / math.hypot(error, float(r['tool_se'])):.4f}")
        print(r, flush=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(path: str) -> None:
    phase = jerlov.petzold_scattering("NUC 2240")
    with open(RUNS) as handle:
        rows = [r for r in csv.DictReader(handle) if r["depth_m"] != "inf"]
    out = []
    for r in rows:
        value, error = run(r, phase)
        tool, tool_se = float(r["monte_carlo"]), float(r["standard_error"])
        out.append({
            "a": r["a"], "bp": r["bp"], "bw": r["bw"],
            "depth_m": r["depth_m"], "albedo": r["albedo"],
            "sun_deg": r["sun_deg"], "package": f"{value:.6e}",
            "package_se": f"{error:.2e}", "tool": r["monte_carlo"],
            "tool_se": r["standard_error"],
            "z": f"{(value - tool) / math.hypot(error, tool_se):.4f}",
        })
        print(out[-1], flush=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--same-phase":
        same_phase(sys.argv[2])
    elif len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        sys.exit(__doc__)

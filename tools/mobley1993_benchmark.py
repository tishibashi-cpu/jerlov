"""The package's Monte Carlo engine against Mobley et al.'s (1993)
canonical problems: DECISIONS.md section 140.

    C. D. Mobley, B. Gentili, H. R. Gordon, Z. Jin, G. W. Kattawar,
    A. Morel, P. Reinersman, K. Stamnes and R. H. Stavn (1993),
    "Comparison of numerical models for computing underwater light
    fields", Appl. Opt. 32(36), 7484-7504, doi:10.1364/AO.32.007484.

Table 5 (p. 7496) and Table 2 (p. 7491) are transcribed below from the
page images. Problems 1, 2, 5 and 6 are posed; 3 (stratified water), 4
(an atmosphere) and 7 (Raman scattering) are not.

    python tools/mobley1993_benchmark.py OUT.csv [--surface-facets all]

Lu is the radiance looking straight down by the engine's collision
estimator (DECISIONS.md section 144); ``lu_cap`` is the mean over the cap
within CAP_DEG of straight up, as sections 140 to 143 took it.

Problem 5's surface meets one facet per crossing, as in 1.34.1
(examples/data/mobley1993/runs.csv), or, with ``--surface-facets all``,
every facet the light meets (DECISIONS.md section 141,
examples/data/mobley1993/runs_all_facets.csv).

This is a tool for the comparison, not part of the package.
"""

from __future__ import annotations

import csv
import math
import sys

import numpy as np

from jerlov import monte_carlo as mc

N_WATER = 1.340
PHOTONS, BATCHES, SEED = 100_000, 10, 1993
#: Highly absorbing water returns few photons from depth: ten times as many.
PHOTONS_ABSORBING = 1_000_000
HALF_SLAB = 0.1
#: Lu, the radiance looking straight down: the mean over the cap within
#: this many degrees of straight up (HydroLight's polar cap).
CAP_DEG = 5.0

#: Table 2: the particle phase function, sr-1, at angles in degrees.
#: 0.50119 degree is printed 2.18839+2; DECISIONS.md section 140 takes it
#: as a misprint and uses the log-log interpolation between its
#: neighbours instead (TABLE2_MISPRINT).
TABLE2 = (
    (0.10000, 1.76661e3), (0.12589, 1.29564e3), (0.15849, 9.50172e2),
    (0.19953, 6.99092e2), (0.25119, 5.13687e2), (0.31623, 3.76373e2),
    (0.39811, 2.76318e2), (0.50119, 2.18839e2), (0.63096, 1.44369e2),
    (0.79433, 1.02241e2), (1.0000, 7.16082e1), (1.2589, 4.95803e1),
    (1.5849, 3.39511e1), (1.9953, 2.28129e1), (2.5119, 1.51622e1),
    (3.1623, 1.00154e1), (3.9811, 6.57957), (5.0119, 4.29530),
    (6.3096, 2.80690), (7.9433, 1.81927), (10.0, 1.15257),
    (15.0, 4.89344e-1), (20.0, 2.44424e-1), (25.0, 1.47151e-1),
    (30.0, 8.60848e-2), (35.0, 5.93075e-2), (40.0, 4.20985e-2),
    (45.0, 3.06722e-2), (50.0, 2.27533e-2), (55.0, 1.69904e-2),
    (60.0, 1.31254e-2), (65.0, 1.04625e-2), (70.0, 8.48826e-3),
    (75.0, 6.97601e-3), (80.0, 5.84232e-3), (85.0, 4.95306e-3),
    (90.0, 4.29232e-3), (95.0, 3.78161e-3), (100.0, 3.40405e-3),
    (105.0, 3.11591e-3), (110.0, 2.91222e-3), (115.0, 2.79696e-3),
    (120.0, 2.68568e-3), (125.0, 2.57142e-3), (130.0, 2.47603e-3),
    (135.0, 2.37667e-3), (140.0, 2.32898e-3), (145.0, 2.31308e-3),
    (150.0, 2.36475e-3), (155.0, 2.50584e-3), (160.0, 2.66183e-3),
    (165.0, 2.83472e-3), (170.0, 3.03046e-3), (175.0, 3.09206e-3),
    (180.0, 3.15366e-3))
TABLE2_MISPRINT = 0.50119

#: Table 5: (problem, omega0) -> {optical depth: (Ed, Eou, Lu), (s/x for
#: each)}, relative to 1 W m-2 nm-1 on a plane normal to the sun.
TABLE5 = {
    (1, 0.9): {1: ((3.66e-1, 3.72e-1, 4.85e-2), (0.002, 0.005, 0.015)),
               5: ((4.33e-2, 4.35e-2, 5.59e-3), (0.003, 0.007, 0.052)),
               10: ((3.16e-3, 3.20e-3, 4.37e-4), (0.015, 0.038, 0.091))},
    (1, 0.2): {1: ((1.41e-1, 1.34e-2, 1.72e-3), (0.001, 0.003, 0.044)),
               5: ((1.07e-3, 1.00e-4, 1.37e-5), (0.005, 0.039, 0.288)),
               10: ((2.93e-6, 3.00e-7, 3.39e-8), (0.102, 0.308, 0.197))},
    (2, 0.9): {1: ((4.13e-1, 9.31e-2, 6.99e-3), (0.001, 0.021, 0.063)),
               5: ((1.87e-1, 4.63e-2, 3.26e-3), (0.005, 0.017, 0.055)),
               10: ((6.85e-2, 1.65e-2, 1.21e-3), (0.010, 0.014, 0.109))},
    (2, 0.2): {1: ((1.62e-1, 9.66e-4, 5.47e-5), (0.000, 0.023, 0.060)),
               5: ((2.27e-3, 1.37e-5, 6.24e-7), (0.002, 0.063, 0.355)),
               10: ((1.30e-5, 7.28e-8, 4.02e-9), (0.047, 0.187, 0.248))},
    (5, 0.9): {1: ((1.14e-1, 3.55e-2, 2.09e-3), (0.012, 0.020, 0.031)),
               5: ((4.33e-2, 1.22e-2, 7.63e-4), (0.009, 0.028, 0.036)),
               10: ((1.48e-2, 3.65e-3, 2.49e-4), (0.007, 0.020, 0.025))},
    (6, 0.2): {1: ((1.62e-1, 9.81e-4, 6.84e-5), (0.000, 0.010, 0.020)),
               5: ((2.28e-3, 2.28e-3, 3.60e-4), (0.003, 0.002, 0.010))},
}
PROBLEMS = {(1, 0.9): dict(sun=60.0, phase="rayleigh"),
            (1, 0.2): dict(sun=60.0, phase="rayleigh"),
            (2, 0.9): dict(sun=60.0, phase="table2"),
            (2, 0.2): dict(sun=60.0, phase="table2"),
            (5, 0.9): dict(sun=80.0, phase="table2", slope_variance=0.04),
            (6, 0.2): dict(sun=60.0, phase="table2", depth=5.0,
                           albedo=0.5)}


def rayleigh():
    grid = np.linspace(0.0, 180.0, 18001)
    per_sr = 3 * (1 + np.cos(np.radians(grid)) ** 2) / (16 * math.pi)
    cdf, cos_angle, _ = mc._inverse_cdf(grid, per_sr)
    return dict(cdf=cdf, cos=cos_angle, straight=0.0,
                angles=np.radians(grid), per_sr=per_sr)


def table2(corrected: bool = True):
    """Table 2 as the paper prescribes it: linear between the angles,
    beta(0.12589) (0.12589 / psi)^1.346 below 0.12589 degree, here from
    1e-4 degree, normalised by its own integral."""
    angles = np.array([a for a, _ in TABLE2])
    values = np.array([v for _, v in TABLE2])
    if corrected:
        k = int(np.flatnonzero(angles == TABLE2_MISPRINT)[0])
        values[k] = math.exp(np.interp(
            math.log(angles[k]), np.log(angles[[k - 1, k + 1]]),
            np.log(values[[k - 1, k + 1]])))
    small = np.geomspace(1e-4, 0.12589, 400, endpoint=False)
    beta_small = values[1] * (0.12589 / small) ** 1.346
    fine = np.unique(np.concatenate([
        np.linspace(lo, hi, 200, endpoint=False)
        for lo, hi in zip(angles[1:-1], angles[2:])] + [[180.0]]))
    grid = np.concatenate([small, fine])
    per_sr = np.concatenate([beta_small, np.interp(fine, angles, values)])
    cdf, cos_angle, total = mc._inverse_cdf(grid, per_sr)
    return dict(cdf=cdf, cos=cos_angle, straight=0.0,
                angles=np.radians(grid), per_sr=per_sr / total,
                values=values)


def run(key, surface_facets="one"):
    spec = PROBLEMS[key]
    omega0 = key[1]
    a, b = 1.0 - omega0, omega0
    ray = rayleigh()
    if spec["phase"] == "rayleigh":
        particles, water, bw = ray, ray, b
    else:
        particles, water, bw = table2(), ray, 0.0
    depth = spec.get("depth", math.inf)
    taus = sorted(TABLE5[key])
    report = np.array([t for t in taus if t < depth], dtype=float)
    out = []
    for k in range(BATCHES):
        out.append(mc._simulate(
            a, b, bw, particles, water, spec["sun"], SEED + k,
            photons=PHOTONS_ABSORBING if omega0 < 0.5 else PHOTONS,
            depths=report, half_slab=HALF_SLAB,
            n_water=N_WATER, d_zenith=CAP_DEG, d_azimuth=45.0, depth=depth,
            albedo=spec.get("albedo"),
            slope_variance=spec.get("slope_variance"),
            surface_facets=surface_facets))
    scale = math.cos(math.radians(spec["sun"]))
    rows = []
    for j, tau in enumerate(taus):
        if tau < depth:
            # Lu by the collision estimator (DECISIONS.md section 144); the
            # mean over the cap within CAP_DEG is kept beside it
            per = np.array([[r["ed"][j], r["e0u"][j], r["lu"][j]]
                            for r in out])
            cap = np.array([r["radiance"][j, -1, :].mean() for r in out])
        else:       # at a Lambertian bottom: Eou = 2 rho Ed, Lu = rho Ed / pi
            rho = spec["albedo"]
            ed = np.array([r["ed_bottom"] for r in out])
            per = np.stack([ed, 2 * rho * ed, rho * ed / math.pi], axis=1)
            cap = per[:, 2]
        mean = per.mean(axis=0) * scale
        se = per.std(axis=0, ddof=1) / math.sqrt(BATCHES) * scale
        cap_mean = cap.mean() * scale
        cap_se = cap.std(ddof=1) / math.sqrt(BATCHES) * scale
        table, spread = TABLE5[key][tau]
        for q, name in enumerate(("Ed", "Eou", "Lu")):
            rows.append({
                "problem": key[0], "omega0": omega0, "tau": tau,
                "quantity": name, "jerlov": f"{mean[q]:.6e}",
                "jerlov_se": f"{se[q]:.2e}", "table5": f"{table[q]:.3e}",
                "table5_s_over_x": f"{spread[q]:.3f}",
                "lu_cap": f"{cap_mean:.6e}" if name == "Lu" else "",
                "lu_cap_se": f"{cap_se:.2e}" if name == "Lu" else ""})
    return rows


def main(path: str, surface_facets: str = "one") -> None:
    rows = []
    for key in PROBLEMS:
        rows += run(key, surface_facets)
        for r in rows[-3 * len(TABLE5[key]):]:
            print(r, flush=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 3 and args[1] == "--surface-facets" \
            and args[2] in ("one", "all"):
        main(args[0], args[2])
    elif len(args) == 1:
        main(args[0])
    else:
        sys.exit(__doc__)

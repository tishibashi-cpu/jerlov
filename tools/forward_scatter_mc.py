"""The attenuation of light kept within an angle, by Monte Carlo:
DECISIONS.md section 107.

A collimated beam in an unbounded homogeneous water. Photons start at
z = 0 along +z and travel exponential paths of mean 1/b, turning at each
scattering by an angle drawn from one of Petzold's phase functions
(tools/kd_monte_carlo.py's sampler, with its extension below 0.1 degree).
Absorption is applied once, as exp(-a L) over the path length L, which is
exact for a homogeneous water and less noisy than killing photons. At the
first crossing of the plane z = r a photon is scored if its direction is
within theta0 of +z; one that wanders back past z = -r is lost.

The score is compared with single scattering, exp(-(c - b F) r), F the
sampler's own share of the scattering within theta0. DECISIONS.md section
107's criterion: within 3 percent wherever b r <= 0.5.

    python tools/forward_scatter_mc.py OUT.csv

writes one row per station, b r and theta0. This is a tool for the check,
not part of the package.
"""

from __future__ import annotations

import csv
import math
import pathlib
import sys
import warnings

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kd_monte_carlo  # noqa: E402

import jerlov  # noqa: E402

STATIONS = ("AUTEC 8", "HAOCE 11", "NUC 2200")
OPTICAL = (0.1, 0.5, 1.0, 3.0)          # b r
HALF_ANGLES = (0.5, 1.0, 5.0, 20.0)     # degrees
PHOTONS = 400_000
SEED = 20261118


def sampler_share(sample, theta0_deg: float) -> float:
    """The sampler's share of the scattering within theta0: the inverse
    of its inverse cumulative distribution."""
    u = np.linspace(0.0, 1.0, 2_000_001)
    return float(np.interp(math.radians(theta0_deg), sample(u), u))


def transport(b: float, a: float, r: float, sample, rng):
    """Weights exp(-a L) and direction cosines at the first crossing of
    z = r, for the photons that cross it."""
    n = PHOTONS
    z = np.zeros(n)
    u = np.zeros((n, 3))
    u[:, 2] = 1.0
    length = np.zeros(n)
    alive = np.ones(n, dtype=bool)
    weights, cosines = [], []
    for _ in range(10_000):
        idx = np.flatnonzero(alive)
        if idx.size == 0:
            break
        step = -np.log(rng.random(idx.size)) / b
        uz = u[idx, 2]
        z_new = z[idx] + uz * step
        cross = (uz > 0) & (z_new >= r)
        hit = idx[cross]
        to_plane = (r - z[hit]) / u[hit, 2]
        weights.append(np.exp(-a * (length[hit] + to_plane)))
        cosines.append(u[hit, 2])
        alive[hit] = False
        go = idx[~cross]
        z[go] = z_new[~cross]
        length[go] += step[~cross]
        lost = go[z[go] < -r]
        alive[lost] = False
        go = go[z[go] >= -r]
        # Turn by theta (from the phase function) and a uniform azimuth.
        theta = sample(rng.random(go.size))
        phi = 2 * math.pi * rng.random(go.size)
        st, ct = np.sin(theta), np.cos(theta)
        ux, uy, uz = u[go, 0], u[go, 1], u[go, 2]
        flat = np.abs(uz) > 0.99999
        den = np.sqrt(np.maximum(1 - uz * uz, 1e-300))
        nx = np.where(flat, st * np.cos(phi),
                      st * (ux * uz * np.cos(phi) - uy * np.sin(phi)) / den
                      + ux * ct)
        ny = np.where(flat, st * np.sin(phi),
                      st * (uy * uz * np.cos(phi) + ux * np.sin(phi)) / den
                      + uy * ct)
        nz = np.where(flat, np.sign(uz) * ct, -st * np.cos(phi) * den
                      + uz * ct)
        norm = np.sqrt(nx * nx + ny * ny + nz * nz)
        u[go, 0], u[go, 1], u[go, 2] = nx / norm, ny / norm, nz / norm
    return np.concatenate(weights), np.concatenate(cosines)


def main(out: str) -> None:
    rng = np.random.default_rng(SEED)
    rows = []
    for station in STATIONS:
        s = jerlov.petzold_scattering(station)
        sample, _ = kd_monte_carlo.petzold_sampler(station)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
            package = {t: jerlov.forward_scatter(s, t).fraction
                       for t in HALF_ANGLES}
        shares = {t: sampler_share(sample, t) for t in HALF_ANGLES}
        for optical in OPTICAL:
            r = optical / s.b
            w, mu = transport(s.b, s.a, r, sample, rng)
            for t in HALF_ANGLES:
                kept = np.where(mu >= math.cos(math.radians(t)), w, 0.0)
                full = np.zeros(PHOTONS)
                full[:kept.size] = kept
                mc = float(full.mean())
                se = float(full.std(ddof=1) / math.sqrt(PHOTONS))
                single = math.exp(-(s.c - s.b * shares[t]) * r)
                rows.append({
                    "station": station, "b_r": optical, "r_m": round(r, 4),
                    "half_angle_deg": t,
                    "monte_carlo": f"{mc:.6e}", "standard_error": f"{se:.2e}",
                    "single_scattering": f"{single:.6e}",
                    "ratio": f"{mc / single:.5f}",
                    "share_sampler": f"{shares[t]:.5f}",
                    "share_package": f"{package[t]:.5f}"})
                print(station, optical, t, rows[-1]["ratio"], flush=True)
    with open(out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main(sys.argv[1])

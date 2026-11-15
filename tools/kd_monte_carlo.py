"""Kd of a homogeneous water by Monte Carlo: DECISIONS.md section 92.

A plane-parallel, infinitely deep, homogeneous water lit by a collimated
beam just below a flat surface, at the refracted angle of the sun. Photons
travel exponential paths of mean 1/c, keep the fraction b/c of their
weight at each interaction (Russian roulette below a small weight), and
turn by an angle drawn from a tabulated phase function. Ed(z) is the
weight crossing the plane z downwards: the planar irradiance. Light that
leaves through the surface is lost; the sky, the atmosphere and the
surface's reflection are not modelled.

    python tools/kd_monte_carlo.py --check

runs the checks of DECISIONS.md section 92 and prints them. The functions
are used by tools/kd_closure.py. This is not part of the package: it is a
tool, written for this comparison and validated only as far as the
checks go.
"""

from __future__ import annotations

import math
import sys
import warnings

import numpy as np

import jerlov

#: Refractive index of sea water for the refracted sun, as OSOAA's runs.
N_WATER = 1.34
#: Below this weight a photon plays Russian roulette, surviving with
#: probability ROULETTE at weight / ROULETTE.
WEIGHT_FLOOR = 1e-3
ROULETTE = 0.1


def refracted_cosine(sun_zenith_deg: float) -> float:
    """The cosine of the sun's beam just below a flat surface."""
    s = math.sin(math.radians(sun_zenith_deg)) / N_WATER
    return math.sqrt(1.0 - s * s)


def petzold_sampler(station: str):
    """Inverse cumulative distribution of the scattering angle (radians)
    for one of Petzold's stations, and its backscatter share.

    The vsf is taken as a power law between the printed angles, as
    ScatteringFunction.vsf_at takes it, and below 0.1 degree, down to
    0.001 degree, as the report's extension continues it, with the slope
    of the first two printed angles."""
    s = jerlov.petzold_scattering(station)
    angles = np.asarray(s.angles_deg, dtype=float)
    vsf = np.asarray(s.vsf, dtype=float)
    slope = ((math.log(vsf[1]) - math.log(vsf[0]))
             / (math.log(angles[1]) - math.log(angles[0])))
    theta = np.concatenate([
        np.logspace(-3.0, math.log10(angles[0]), 400, endpoint=False),
        np.logspace(math.log10(angles[0]), math.log10(180.0), 6000)])
    log_vsf = np.where(
        theta < angles[0],
        math.log(vsf[0]) + slope * (np.log(theta) - math.log(angles[0])),
        np.interp(np.log(theta), np.log(angles), np.log(vsf)))
    radians = np.radians(theta)
    density = np.exp(log_vsf) * np.sin(radians)
    cumulative = np.concatenate([[0.0], np.cumsum(
        0.5 * (density[1:] + density[:-1]) * np.diff(radians))])
    backscatter = float(1.0 - np.interp(math.pi / 2, radians, cumulative)
                        / cumulative[-1])
    cumulative /= cumulative[-1]

    def sample(u: np.ndarray) -> np.ndarray:
        return np.interp(u, cumulative, radians)

    return sample, backscatter


def isotropic_sampler():
    """Isotropic scattering, for a check with a known answer."""
    def sample(u: np.ndarray) -> np.ndarray:
        return np.arccos(1.0 - 2.0 * u)
    return sample, 0.5


def ed_profile(a: float, b: float, sample, mu0: float, depth_m: float,
               photons: int = 400_000, planes: int = 121, seed: int = 1):
    """Ed(z) / Ed(0) at evenly spaced planes from 0 to depth_m."""
    rng = np.random.default_rng(seed)
    c = a + b
    albedo = b / c if c > 0 else 0.0
    z_planes = np.linspace(0.0, depth_m, planes)
    ed = np.zeros(planes)
    ed[0] = photons
    z = np.zeros(photons)
    ux = np.full(photons, math.sqrt(max(0.0, 1.0 - mu0 * mu0)))
    uy = np.zeros(photons)
    uz = np.full(photons, mu0)
    weight = np.ones(photons)
    alive = np.ones(photons, dtype=bool)
    while alive.any():
        idx = np.flatnonzero(alive)
        z0 = z[idx]
        z1 = z0 + uz[idx] * (-np.log(rng.random(idx.size)) / c)
        down = uz[idx] > 0
        first = np.searchsorted(z_planes, z0, side="right")
        last = np.searchsorted(z_planes, np.minimum(z1, depth_m),
                               side="right")
        crossing = down & (last > first)
        if crossing.any():
            starts = first[crossing]
            stops = last[crossing]
            weights = weight[idx[crossing]]
            # Add each photon's weight to the planes it crossed.
            delta = np.zeros(planes + 1)
            np.add.at(delta, starts, weights)
            np.add.at(delta, stops, -weights)
            ed += np.cumsum(delta)[:planes]
        z[idx] = z1
        gone = (z1 < 0.0) | (z1 > depth_m)
        alive[idx[gone]] = False
        stay = idx[~gone]
        if albedo == 0.0:
            alive[stay] = False
            continue
        weight[stay] *= albedo
        low = stay[weight[stay] < WEIGHT_FLOOR]
        if low.size:
            survive = rng.random(low.size) < ROULETTE
            weight[low[survive]] /= ROULETTE
            alive[low[~survive]] = False
        stay = stay[alive[stay]]
        if stay.size == 0:
            break
        theta = sample(rng.random(stay.size))
        phi = 2.0 * math.pi * rng.random(stay.size)
        ct, st = np.cos(theta), np.sin(theta)
        cp, sp = np.cos(phi), np.sin(phi)
        x, y, w = ux[stay], uy[stay], uz[stay]
        r = np.sqrt(np.maximum(1.0 - w * w, 1e-12))
        vertical = r < 1e-6
        nx = np.where(vertical, st * cp,
                      st * (x * w * cp - y * sp) / r + x * ct)
        ny = np.where(vertical, st * sp,
                      st * (y * w * cp + x * sp) / r + y * ct)
        nz = np.where(vertical, np.sign(w) * ct, -st * cp * r + w * ct)
        ux[stay], uy[stay], uz[stay] = nx, ny, nz
    return z_planes, ed / photons


def mean_kd(z: np.ndarray, ed: np.ndarray, drop: float) -> float:
    """Mean Kd from the surface to where Ed has fallen by exp(drop)."""
    log_ed = np.log(ed)
    depth = float(np.interp(drop, -log_ed, z))
    if depth >= z[-1]:
        raise ValueError("the profile does not reach that depth")
    return drop / depth


def kd(a: float, b: float, sample, sun_zenith_deg: float,
       optical_depths=(1.0,), photons: int = 400_000, seed: int = 1):
    """Mean Kd to each of ``optical_depths`` (in units of Kd itself)."""
    mu0 = refracted_cosine(sun_zenith_deg)
    # Deep enough for the largest optical depth even if Kd is 3 a / mu0.
    guess = a / mu0
    depth = 1.6 * max(optical_depths) / guess
    z, ed = ed_profile(a, b, sample, mu0, depth, photons=photons,
                       seed=seed)
    return [mean_kd(z, ed, d) for d in optical_depths]


def morel_loisel(b_over_a, mu, eta):
    """Kd/a for optical depth 1, as Williamson & Hollins (2022) print it,
    their Eq. (2)."""
    return math.sqrt(1 + b_over_a * ((0.1304 + 0.272 * eta)
                                     + mu * (1.3433 * eta - 0.01414))) / mu


def solonenko_mobley(b_over_a, mu, eta):
    """Kd/a for optical depth about 2.3, Williamson & Hollins's Eq. (3)."""
    return math.sqrt(1 + b_over_a * (mu * (0.451 + 2.584 * eta)
                                     - (0.205 + 0.521 * eta))) / mu


def check():
    """The checks of DECISIONS.md section 92."""
    mu0 = refracted_cosine(30.0)
    out = {}
    # 1. No scattering: Ed falls as exp(-a z / mu0), exactly.
    sample, _ = petzold_sampler("HAOCE 5")
    (k,) = kd(0.1, 0.0, sample, 30.0, photons=100_000)
    out["no_scattering"] = k / (0.1 / mu0)
    # 2. Isotropic scattering at single-scattering albedo 0.5 and a
    #    vertical beam: compared with the same run's own analytic first
    #    step, Ed falls faster than c is impossible; slower than a / mu0
    #    impossible. Recorded only.
    # 3. Against Eqs. (2) and (3), b/a from 0.5 to 10, eta = 0.
    rows = []
    for station in ("NUC 2240", "HAOCE 5", "AUTEC 7"):
        sample, bb = petzold_sampler(station)
        for ratio in (0.5, 1.0, 3.0, 5.0, 10.0):
            k1, k23 = kd(0.1, 0.1 * ratio, sample, 30.0,
                         optical_depths=(1.0, 2.3))
            rows.append((station, bb, ratio, k1 / 0.1,
                         morel_loisel(ratio, mu0, 0.0), k23 / 0.1,
                         solonenko_mobley(ratio, mu0, 0.0)))
    out["against_formulas"] = rows
    return out


if __name__ == "__main__":
    if "--check" not in sys.argv:
        raise SystemExit(__doc__)
    warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
    result = check()
    print(f"no scattering: Kd / (a / mu0) = {result['no_scattering']:.4f}")
    print("station   bb/b    b/a   MC(1)  Eq.2   MC(2.3) Eq.3")
    for row in result["against_formulas"]:
        print(f"{row[0]:8} {row[1]:.4f} {row[2]:5.1f}  {row[3]:.3f}  "
              f"{row[4]:.3f}  {row[5]:.3f}  {row[6]:.3f}")

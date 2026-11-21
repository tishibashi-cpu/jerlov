"""The remote sensing reflectance of shallow water by Monte Carlo:
DECISIONS.md section 113.

A plane-parallel homogeneous water of depth H over a Lambertian bottom of
albedo rho, lit by the sun's beam just below a flat surface at the
refracted angle (n = 1.34, as tools/kd_monte_carlo.py and Lee et al.'s
runs). Photons travel exponential paths of mean 1/c and keep b/c of their
weight at each scattering (Russian roulette below a small weight, as
tools/kd_monte_carlo.py). A scattering turns a photon by pure water's
phase function with probability bw/b, otherwise by one of Petzold's (the
sampler of tools/kd_monte_carlo.py, rebuilt here with its density). At the
bottom a photon keeps rho of its weight and leaves in a cosine-weighted
direction; at the surface from below it keeps Fresnel's reflectance of
its weight and is turned down, and that weight is added to the
downwelling irradiance just below the surface. Starting a fresh path at a
boundary is exact, since the free path has no memory.

rrs is the upwelling radiance straight up just below the surface over that
irradiance. The radiance is scored by a collision estimator: each
scattering adds w (b/c) p(Theta) exp(-c z), p the mixture's phase function
per steradian and Theta the angle between the photon's direction and
straight up; each arrival at the bottom adds w (rho/pi) exp(-c H). The
irradiance is the photons' number plus the weight reflected down.

    python tools/shallow_rrs_mc.py --check
    python tools/shallow_rrs_mc.py OUT.csv
    python tools/shallow_rrs_mc.py --water-share OUT.csv
    python tools/shallow_rrs_mc.py --water-share-nadir OUT.csv
    python tools/shallow_rrs_mc.py --black-bottom OUT.csv
    python tools/shallow_rrs_mc.py --cut-check OUT.csv

The first runs the check of section 113 (no scattering, no reflection at
the surface: rrs = (rho/pi) exp(-a H / cos theta_w) exp(-a H)) and prints
it; the second writes one row per run of section 113's grid; the last two
write the runs of section 114's steps 2 and 3. This is a tool for the
comparison, not part of the package.
"""

from __future__ import annotations

import csv
import itertools
import math
import pathlib
import sys
import warnings

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kd_monte_carlo  # noqa: E402

import jerlov  # noqa: E402

N_WATER = kd_monte_carlo.N_WATER
STATION = "NUC 2240"
A = (0.05, 0.2, 1.0)                 # 1/m
BP_OVER_A = (0.3, 3.0, 30.0)
BW = 0.002                           # 1/m, pure water's scattering
DEPTHS = (1.0, 4.0, 16.0, math.inf)  # m; inf: no bottom
ALBEDOS = (0.0, 0.3, 1.0)
SUNS = (0.0, 30.0, 60.0)             # degrees, in air
PHOTONS = 200_000
BATCHES = 10
SEED = 20261121
#: Scattering by less than this, degrees, counts as none (petzold_phase).
CUT_DEG = 1.0


def petzold_phase(station: str, cut_deg: float = CUT_DEG):
    """The sampler of kd_monte_carlo.petzold_sampler, rebuilt with the
    density it samples and with scattering by less than ``cut_deg`` taken
    as no scattering: (sample, p per steradian of the rest at an angle in
    radians, the share below the cut, backscatter share).

    The collision estimator scores p(Theta) for the angle to straight up;
    with Petzold's forward peak its variance has no bound, since p grows
    faster than 1/Theta. A photon turned by less than a degree goes on
    nearly as before, so treating that share f as unscattered (b becomes
    (1 - f) b, p is renormalised over the rest) bounds the estimator and
    changes the upwelling light very little."""
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
    steps = 0.5 * (density[1:] + density[:-1]) * np.diff(radians)
    cumulative = np.concatenate([[0.0], np.cumsum(steps)])
    total = cumulative[-1]
    cumulative /= total
    back = 1.0 - float(np.interp(math.pi / 2, radians, cumulative))
    cut = math.radians(cut_deg)
    below = float(np.interp(cut, radians, cumulative))
    per_sr = np.exp(log_vsf) / (2.0 * math.pi * total * (1.0 - below))

    def sample(u: np.ndarray) -> np.ndarray:
        return np.interp(below + u * (1.0 - below), cumulative, radians)

    def pdf(angle: np.ndarray) -> np.ndarray:
        angle = np.clip(angle, radians[0], radians[-1])
        value = np.exp(np.interp(np.log(angle), np.log(radians),
                                 np.log(per_sr)))
        return np.where(angle < cut, 0.0, value)

    return sample, pdf, below, back


def water_pdf(angle: np.ndarray) -> np.ndarray:
    """Pure water's phase function per steradian, 1 + 0.835 cos^2, the
    shape kd_monte_carlo.water_sampler draws from."""
    c = np.cos(angle)
    return (1.0 + 0.835 * c * c) / (4.0 * math.pi * (1.0 + 0.835 / 3.0))


def fresnel_from_below(mu: np.ndarray) -> np.ndarray:
    """Fresnel's reflectance, unpolarised, for light in the water meeting
    a flat surface at cosine mu; 1 beyond the critical angle."""
    sin_t = N_WATER * np.sqrt(np.maximum(0.0, 1.0 - mu * mu))
    out = np.ones_like(mu)
    ok = sin_t < 1.0
    ci = mu[ok]
    ct = np.sqrt(1.0 - sin_t[ok] ** 2)
    rs = ((N_WATER * ci - ct) / (N_WATER * ci + ct)) ** 2
    rp = ((N_WATER * ct - ci) / (N_WATER * ct + ci)) ** 2
    out[ok] = 0.5 * (rs + rp)
    return out


def rrs(a: float, bp: float, bw: float, depth: float, rho: float,
        sun_deg: float, phase, photons: int = PHOTONS, seed: int = SEED,
        surface: bool = True, sky_share: float = 0.0):
    """rrs straight up just below the surface, and its standard error
    from BATCHES batches. ``surface`` False lets light leave through the
    surface instead of being partly reflected (the check). ``sky_share``
    of the irradiance just below the surface enters as diffuse light,
    uniform in radiance in the air (kd_monte_carlo.sky_cosines); at 0, the
    default, no random number is drawn for it, so earlier runs repeat bit
    for bit (DECISIONS.md section 114)."""
    sample, pdf, below, _ = phase
    water = kd_monte_carlo.water_sampler()
    bp = bp * (1.0 - below)
    b = bp + bw
    c = a + b
    albedo = b / c
    mu0 = kd_monte_carlo.refracted_cosine(sun_deg)
    rng = np.random.default_rng(seed)
    batch = np.arange(photons) % BATCHES
    radiance = np.zeros(BATCHES)
    irradiance = np.bincount(batch, minlength=BATCHES).astype(float)
    z = np.zeros(photons)
    ux = np.full(photons, math.sqrt(max(0.0, 1.0 - mu0 * mu0)))
    uy = np.zeros(photons)
    uz = np.full(photons, mu0)
    weight = np.ones(photons)
    alive = np.ones(photons, dtype=bool)
    if sky_share > 0.0:
        diffuse = rng.random(photons) < sky_share
        n_sky = int(diffuse.sum())
        cosines, cumulative = kd_monte_carlo.sky_cosines()
        w_sky = np.interp(rng.random(n_sky), cumulative, cosines)
        phi_sky = 2.0 * math.pi * rng.random(n_sky)
        s_sky = np.sqrt(np.maximum(0.0, 1.0 - w_sky ** 2))
        ux[diffuse] = s_sky * np.cos(phi_sky)
        uy[diffuse] = s_sky * np.sin(phi_sky)
        uz[diffuse] = w_sky
    while alive.any():
        idx = np.flatnonzero(alive)
        z1 = z[idx] + uz[idx] * (-np.log(rng.random(idx.size)) / c)
        top = z1 < 0.0
        bottom = z1 > depth
        inside = ~(top | bottom)
        # The bottom: score, then reflect or end.
        hit = idx[bottom]
        if hit.size:
            np.add.at(radiance, batch[hit],
                      weight[hit] * rho / math.pi * math.exp(-c * depth))
            z[hit] = depth
            if rho > 0.0:
                weight[hit] *= rho
                mu = np.sqrt(rng.random(hit.size))
                phi = 2.0 * math.pi * rng.random(hit.size)
                s = np.sqrt(1.0 - mu * mu)
                ux[hit], uy[hit], uz[hit] = s * np.cos(phi), s * np.sin(phi), -mu
            else:
                alive[hit] = False
        # The surface from below: reflect part, the rest leaves.
        up = idx[top]
        if up.size:
            if surface:
                r = fresnel_from_below(-uz[up])
                weight[up] *= r
                np.add.at(irradiance, batch[up], weight[up])
                z[up] = 0.0
                uz[up] = -uz[up]
            else:
                alive[up] = False
        # Collisions: absorption, then a scattering scored and drawn.
        hit = idx[inside]
        z[hit] = z1[inside]
        if albedo == 0.0 or hit.size == 0:
            alive[hit] = False
        else:
            weight[hit] *= albedo
            low = hit[weight[hit] < kd_monte_carlo.WEIGHT_FLOOR]
            if low.size:
                survive = rng.random(low.size) < kd_monte_carlo.ROULETTE
                weight[low[survive]] /= kd_monte_carlo.ROULETTE
                alive[low[~survive]] = False
            hit = hit[alive[hit]]
            angle = np.arccos(np.clip(-uz[hit], -1.0, 1.0))
            p = (bw * water_pdf(angle) + bp * pdf(angle)) / b
            np.add.at(radiance, batch[hit],
                      weight[hit] * p * np.exp(-c * z[hit]))
            theta = sample(rng.random(hit.size))
            by_water = rng.random(hit.size) < bw / b
            theta[by_water] = water(rng.random(int(by_water.sum())))
            phi = 2.0 * math.pi * rng.random(hit.size)
            ct, st = np.cos(theta), np.sin(theta)
            cp, sp = np.cos(phi), np.sin(phi)
            x, y, w = ux[hit], uy[hit], uz[hit]
            rr = np.sqrt(np.maximum(1.0 - w * w, 1e-12))
            vertical = rr < 1e-6
            nx = np.where(vertical, st * cp,
                          st * (x * w * cp - y * sp) / rr + x * ct)
            ny = np.where(vertical, st * sp,
                          st * (y * w * cp + x * sp) / rr + y * ct)
            nz = np.where(vertical, np.sign(w) * ct, -st * cp * rr + w * ct)
            ux[hit], uy[hit], uz[hit] = nx, ny, nz
    # A collision scores w (b/c) p exp(-c z): the albedo is applied to the
    # weight before scoring, and the roulette keeps its expectation.
    per_batch = radiance / irradiance
    total = float(radiance.sum() / irradiance.sum())
    return total, float(per_batch.std(ddof=1) / math.sqrt(BATCHES))


def check() -> dict:
    """No scattering and no reflection at the surface: the bottom term
    alone, against (rho/pi) exp(-a H / mu0) exp(-a H)."""
    phase = petzold_phase(STATION)
    out = {}
    for a, depth, rho, sun in ((0.1, 3.0, 0.5, 30.0), (0.5, 1.0, 1.0, 0.0),
                               (0.05, 10.0, 0.3, 60.0)):
        mc, _ = rrs(a, 0.0, 1e-12, depth, rho, sun, phase,
                    surface=False)
        mu0 = kd_monte_carlo.refracted_cosine(sun)
        exact = rho / math.pi * math.exp(-a * depth / mu0 - a * depth)
        out[(a, depth, rho, sun)] = mc / exact
    back = phase[3]
    _, back_kd = kd_monte_carlo.petzold_sampler(STATION)
    out["backscatter_share_matches_kd_monte_carlo"] = abs(back - back_kd)
    return out


def main(path: str) -> None:
    phase = petzold_phase(STATION)
    back = phase[3]
    rows = []
    for a, ratio, depth, sun in itertools.product(A, BP_OVER_A, DEPTHS,
                                                  SUNS):
        for rho in (ALBEDOS if math.isfinite(depth) else (0.0,)):
            bp = ratio * a
            bb = 0.5 * BW + back * bp
            value, error = rrs(a, bp, BW, depth, rho, sun, phase)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
                model = jerlov.lee1999_shallow_rrs(
                    a, bb, depth_m=depth if math.isfinite(depth) else 1.0,
                    bottom_albedo=rho, sun_zenith_deg=sun)
            rows.append({
                "a": a, "bp": bp, "bw": BW, "bb": f"{bb:.6g}",
                "u": f"{bb / (a + bb):.6g}",
                "depth_m": "inf" if not math.isfinite(depth) else depth,
                "albedo": rho, "sun_deg": sun,
                "monte_carlo": f"{value:.6e}", "standard_error": f"{error:.2e}",
                "model": f"{(model.rrs if math.isfinite(depth) else model.deep):.6e}",
            })
            print(rows[-1], flush=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


#: DECISIONS.md section 114, step 2: u, a and pure water's share of bb.
SHARE_U = (0.01, 0.025, 0.07)
SHARE_A = (0.05, 0.2)
SHARES = (0.0, 0.2, 0.4, 0.6, 0.8, 0.95)
SHARE_DEPTHS = (4.0, math.inf)
SHARE_SUN = 30.0
#: Step 3: the black-bottom cells, and the changes made to them.
DARK_A = (0.05, 0.2)
DARK_BP_OVER_A = (3.0, 30.0)
DARK_DEPTHS = (1.0, 4.0)
OTHER_STATIONS = ("AUTEC 8", "HAOCE 11")
SKY_SHARE = 0.3


def _write(path, rows) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _model(a, bb, depth, rho, sun):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        m = jerlov.lee1999_shallow_rrs(
            a, bb, depth_m=depth if math.isfinite(depth) else 1.0,
            bottom_albedo=rho, sun_zenith_deg=sun)
    return m.rrs if math.isfinite(depth) else m.deep


def water_share(path: str, sun: float = SHARE_SUN,
                depths=SHARE_DEPTHS, a_values=SHARE_A) -> None:
    """Step 2 of section 114: deep water and a black bottom at 4 m, u and
    a held, pure water's share of bb varied. Section 115 runs it with the
    sun at the zenith, deep water and one a."""
    phase = petzold_phase(STATION)
    back = phase[3]
    rows = []
    for u, a, share, depth in itertools.product(SHARE_U, a_values, SHARES,
                                                depths):
        bb = u * a / (1.0 - u)
        bw = 2.0 * share * bb
        bp = (1.0 - share) * bb / back
        value, error = rrs(a, bp, bw, depth, 0.0, sun, phase)
        rows.append({
            "u": u, "a": a, "water_share": share,
            "depth_m": "inf" if not math.isfinite(depth) else depth,
            "bp": f"{bp:.6g}", "bw": f"{bw:.6g}", "bb": f"{bb:.6g}",
            "monte_carlo": f"{value:.6e}", "standard_error": f"{error:.2e}",
            "model": f"{_model(a, bb, depth, 0.0, sun):.6e}",
        })
        print(rows[-1], flush=True)
    _write(path, rows)


def black_bottom(path: str) -> None:
    """Step 3 (a) and (b): the black-bottom cells with another particle
    phase function, a, bb and pure water's part held, or with a sky."""
    base = petzold_phase(STATION)
    rows = []
    for a, ratio, depth, sun in itertools.product(DARK_A, DARK_BP_OVER_A,
                                                  DARK_DEPTHS, SUNS):
        bp0 = ratio * a
        bb = 0.5 * BW + base[3] * bp0
        for change in ("none",) + OTHER_STATIONS + ("sky",):
            if change in OTHER_STATIONS:
                phase = petzold_phase(change)
                bp = (bb - 0.5 * BW) / phase[3]
                sky = 0.0
            else:
                phase, bp = base, bp0
                sky = SKY_SHARE if change == "sky" else 0.0
            if change == "none":
                continue        # in monte_carlo.csv already
            value, error = rrs(a, bp, BW, depth, 0.0, sun, phase,
                               sky_share=sky)
            rows.append({
                "a": a, "bp_over_a": ratio, "depth_m": depth,
                "sun_deg": sun, "change": change, "bp": f"{bp:.6g}",
                "bw": BW, "bb": f"{bb:.6g}",
                "monte_carlo": f"{value:.6e}",
                "standard_error": f"{error:.2e}",
                "model": f"{_model(a, bb, depth, 0.0, sun):.6e}",
            })
            print(rows[-1], flush=True)
    _write(path, rows)


#: DECISIONS.md section 115: the cut below which scattering counts as none,
#: tried at all three stations in the cell where they differ most.
CUT_CELL = dict(a=0.05, bp_over_a=3.0, depth=1.0, sun=0.0)
CUTS = (0.5, 1.0, 2.0)
CUT_PHOTONS = 400_000


def cut_check(path: str) -> None:
    """The black-bottom cell of CUT_CELL at each station and cut, a, bb and
    pure water's part held as in black_bottom."""
    cell = CUT_CELL
    a = cell["a"]
    bb = 0.5 * BW + petzold_phase(STATION)[3] * cell["bp_over_a"] * a
    rows = []
    for station, cut in itertools.product((STATION,) + OTHER_STATIONS,
                                          CUTS):
        phase = petzold_phase(station, cut)
        bp = (bb - 0.5 * BW) / phase[3]
        value, error = rrs(a, bp, BW, cell["depth"], 0.0, cell["sun"],
                           phase, photons=CUT_PHOTONS)
        rows.append({
            "station": station, "cut_deg": cut, "a": a,
            "bp_over_a": cell["bp_over_a"], "depth_m": cell["depth"],
            "sun_deg": cell["sun"], "bp": f"{bp:.6g}", "bw": BW,
            "bb": f"{bb:.6g}", "share_below_cut": f"{phase[2]:.6g}",
            "backscatter_share": f"{phase[3]:.6g}",
            "monte_carlo": f"{value:.6e}", "standard_error": f"{error:.2e}",
            "model": f"{_model(a, bb, cell['depth'], 0.0, cell['sun']):.6e}",
        })
        print(rows[-1], flush=True)
    _write(path, rows)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--water-share":
        water_share(sys.argv[2])
    elif len(sys.argv) == 3 and sys.argv[1] == "--water-share-nadir":
        water_share(sys.argv[2], sun=0.0, depths=(math.inf,),
                    a_values=(0.05,))
    elif len(sys.argv) == 3 and sys.argv[1] == "--cut-check":
        cut_check(sys.argv[2])
    elif len(sys.argv) == 3 and sys.argv[1] == "--black-bottom":
        black_bottom(sys.argv[2])
    elif sys.argv[1:] == ["--check"]:
        for key, value in check().items():
            print(key, f"{value:.5f}")
    elif len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        sys.exit(__doc__)

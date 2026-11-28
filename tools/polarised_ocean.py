"""A vector Monte Carlo for a wavy sea surface and a body of pure water,
against Chowdhary et al.'s (2020) testbed: DECISIONS.md section 147.

    J. Chowdhary, P.-W. Zhai, F. Xu, R. Frouin and D. Ramon (2020),
    "Testbed results for scalar and vector radiative transfer computations
    of light in atmosphere-ocean systems", J. Quant. Spectrosc. Radiat.
    Transfer 242, 106717, doi:10.1016/j.jqsrt.2019.106717.

Two of its models, just above the surface:

- AOS-I: a molecular atmosphere over a wavy surface, the ocean black;
- AOS-II: no atmosphere, a wavy surface over 100 m of pure seawater
  (Rayleigh scattering) and a black bottom.

The surface (their Table 4): Cox and Munk's isotropic Gaussian slopes,
mean square slope 0.03884, refractive index 1.34, no shadowing, no second
facet and no renormalisation. The photons are those of
``tools/polarised_mc.py`` (a Stokes vector with a reference axis e1 normal
to the direction d, e2 = d x e1, Q = I1 - I2). At a facet the Stokes
vector is turned into the plane of incidence (e1 = s x d, e2 = s, s
normal to that plane) and multiplied by Fresnel's matrix, the
transmission's in power, so that I is the flux; the weight takes the
facet's share of the beam, cos i / (mu_n mu), not divided by its mean.

The light leaving in each tabulated direction v is estimated at every
scattering by reciprocity: a facet is drawn for light travelling against
v, and the light the scattering sends along the reversed path is carried
through that facet into v (refracted, with 1 / m^2 on the radiance, for
AOS-II; reflected for AOS-I). The direct glint is added from its closed
form.

    python tools/polarised_ocean.py OUT.csv

The CSV holds R = pi L / (mu0 S0) for I, Q and U in the testbed's
conventions (TO_TESTBED).

This is a tool for the comparison, not part of the package.
"""

from __future__ import annotations

import csv
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from polarised_mc import (  # noqa: E402
    _cross, _draw_rayleigh_cos, _meridian_e1, _rayleigh, _rotate, _unit)

#: Table 4 (both models).
SLOPE_VARIANCE = 0.03884
N_WATER = 1.34
#: Table 5a: the molecular atmosphere's optical thickness (AOS-I).
ATMOSPHERE = {350: 0.63031, 450: 0.22111, 550: 0.097069, 650: 0.049188}
#: Table 2: the pure seawater's single scattering albedo and optical
#: thickness (100 m), AOS-II.
WATER = {350: (0.39644970, 3.38), 450: (0.32846715, 1.37),
         550: (0.03253425, 5.84), 650: (0.002932551, 34.1)}
SUNS = (30.0, 60.0)
VZA = tuple(float(v) for v in range(0, 65, 5))
#: Relative azimuths from the sun's direction of travel (0 towards the
#: glint), in the two pairs the tables give; straight up once for each
#: pair, Q and U in the plane of its first azimuth.
PAIRS = ((0.0, 180.0), (60.0, 240.0))
PHOTONS, BATCHES, SEED = 100_000, 10, 2020
_WEIGHT_FLOOR = 1e-4

#: From this module's I per unit planar irradiance to R = pi L / (mu0 S0):
#: times pi. Q = I1 - I2 with e1 in the meridian plane is the testbed's
#: Q (the glint, polarised across its plane of incidence, has Q < 0 in
#: both), and U is too, as the tables fix (DECISIONS.md section 147).
TO_TESTBED = (math.pi, math.pi, math.pi, math.pi)


# -- Fresnel -----------------------------------------------------------------

def fresnel(cos_i, n1, n2):
    """Fresnel's amplitude coefficients for the basis (s x d, s) on either
    side: (rp, rs, tp, ts, cos_t), complex where all is reflected (cos_t
    then 0 and tp = ts = 0)."""
    cos_i = np.asarray(cos_i, dtype=float)
    sin_t2 = (n1 / n2) ** 2 * (1 - cos_i * cos_i)
    ct = np.sqrt((1 - sin_t2).astype(complex))
    rs = (n1 * cos_i - n2 * ct) / (n1 * cos_i + n2 * ct)
    rp = (n2 * cos_i - n1 * ct) / (n2 * cos_i + n1 * ct)
    ok = sin_t2 < 1
    ts = np.where(ok, 2 * n1 * cos_i / (n1 * cos_i + n2 * ct), 0).real
    tp = np.where(ok, 2 * n1 * cos_i / (n2 * cos_i + n1 * ct), 0).real
    return rp, rs, tp, ts, np.where(ok, ct.real, 0.0)


def reflect_matrix(S, rp, rs):
    """Fresnel's reflection on Stokes vectors (4 x n) in the plane of
    incidence: E1 -> rp E1, E2 -> rs E2."""
    a2, b2 = np.abs(rp) ** 2, np.abs(rs) ** 2
    c = rp * np.conj(rs)
    out = np.empty_like(S)
    out[0] = 0.5 * ((a2 + b2) * S[0] + (a2 - b2) * S[1])
    out[1] = 0.5 * ((a2 - b2) * S[0] + (a2 + b2) * S[1])
    out[2] = c.real * S[2] - c.imag * S[3]
    out[3] = c.imag * S[2] + c.real * S[3]
    return out


def transmit_matrix(S, tp, ts, cos_i, cos_t, n1, n2):
    """Fresnel's transmission in power on Stokes vectors in the plane of
    incidence: the flux that crosses, not the radiance."""
    k = np.where(cos_i > 0, n2 * cos_t / (n1 * np.maximum(cos_i, 1e-300)),
                 0.0)
    tp2, ts2 = k * tp * tp, k * ts * ts
    g = np.sqrt(tp2 * ts2)
    out = np.empty_like(S)
    out[0] = 0.5 * ((tp2 + ts2) * S[0] + (tp2 - ts2) * S[1])
    out[1] = 0.5 * ((tp2 - ts2) * S[0] + (tp2 + ts2) * S[1])
    out[2] = g * S[2]
    out[3] = g * S[3]
    return out


def _through(S, matrix, polarised):
    """A facet's matrix on S, or without polarisation its (1,1) element
    alone (the matrix for unpolarised light)."""
    if polarised:
        return matrix(S)
    unpol = np.zeros_like(S)
    unpol[0] = 1.0
    out = np.zeros_like(S)
    out[0] = matrix(unpol)[0] * S[0]
    return out


def _to_plane(S, e1, d, s):
    """S referred to (e1, d x e1) turned to (s x d, s)."""
    p = _cross(s, d)
    e2 = _cross(d, e1)
    return _rotate(S, np.sum(p * e1, axis=0), np.sum(p * e2, axis=0)), p


def _plane_normal(d, n, fallback):
    """s, the unit normal to the plane of incidence of d on a facet n;
    ``fallback`` where d is along n."""
    s = _cross(d, n)
    size = np.linalg.norm(s, axis=0)
    return np.where(size > 1e-12, s / np.maximum(size, 1e-300), fallback)


def facets(d, rng):
    """For light travelling in directions d (3 x n), a facet normal on the
    side it comes from, slopes Gaussian of total variance SLOPE_VARIANCE,
    and its weight, cos i / (mu_n mu) for a facet that faces the light and
    0 for one that does not (no renormalisation): returns (normal, cos_i,
    w)."""
    n = d.shape[1]
    sd = math.sqrt(SLOPE_VARIANCE / 2)
    zx, zy = rng.normal(0.0, sd, n), rng.normal(0.0, sd, n)
    side = np.where(d[2] > 0, -1.0, 1.0)
    normal = np.array([-zx * side, -zy * side, side]) / np.sqrt(
        1 + zx * zx + zy * zy)
    cos_i = -np.sum(normal * d, axis=0)
    w = np.where(cos_i > 0, cos_i / (np.abs(normal[2]) * np.abs(d[2])), 0.0)
    return normal, np.maximum(cos_i, 0.0), w


def cross_surface(d, e1, S, from_air, branch, rng, polarised=True):
    """Light (d, e1, S) at the surface, one facet each. ``branch``
    "reflect" or "transmit": the Stokes vector is multiplied by that
    branch's matrix (its weight by the branch's share) and by the facet's
    weight. Returns (d, e1, S, ok), ok False where the branch's light
    would meet the surface again or the facet does not face the light."""
    normal, cos_i, w = facets(d, rng)
    n1, n2 = (1.0, N_WATER) if from_air else (N_WATER, 1.0)
    rp, rs, tp, ts, cos_t = fresnel(cos_i, n1, n2)
    s = _plane_normal(d, normal, _cross(d, e1))
    Sp, _ = _to_plane(S, e1, d, s)
    if branch == "reflect":
        out_d = d + 2 * cos_i * normal

        def matrix(X):
            return reflect_matrix(X, rp, rs).real
    else:
        eta = n1 / n2
        out_d = eta * d + (eta * cos_i - cos_t) * normal

        def matrix(X):
            return transmit_matrix(X, tp, ts, cos_i, cos_t, n1, n2)
    out_d = _unit(out_d)
    Sp = _through(Sp, matrix, polarised) * w
    # down into the water (or the air below an atmosphere) the light goes on
    want_down = (branch == "transmit") == from_air
    ok = (w > 0) & ((out_d[2] > 0) if want_down else (out_d[2] < 0))
    if branch == "transmit":
        ok &= cos_t > 0
    return out_d, _cross(s, out_d), Sp, ok


# -- the directions ----------------------------------------------------------

def directions():
    """The tabulated directions: (phi, vza, v, phi of the reference plane
    straight up). v travels up (z is down); phi from the sun's direction
    of travel (+x)."""
    out = []
    for first, second in PAIRS:
        for phi in (first, second):
            for vza in VZA:
                if vza == 0 and phi == second:
                    continue
                t, p = math.radians(vza), math.radians(phi)
                out.append((phi, vza, (math.sin(t) * math.cos(p),
                                       math.sin(t) * math.sin(p),
                                       -math.cos(t)), first))
    return out


def glint(sun, dirs=None, polarised=True):
    """The sun reflected once by the surface into each direction, per unit
    planar irradiance on it: p(n) R(n) / (4 mu mu0 mu_n^4), (4, k)."""
    dirs = directions() if dirs is None else dirs
    V = np.array([d[2] for d in dirs]).T
    e1_v = _meridian_e1(V, [d[3] for d in dirs])
    t0 = math.radians(sun)
    s0 = np.array([[math.sin(t0)], [0.0], [math.cos(t0)]])
    n = _unit(V - s0)                    # towards the air (n_z < 0)
    mu_n = np.abs(n[2])
    tan2 = (1 - mu_n * mu_n) / (mu_n * mu_n)
    p = np.exp(-tan2 / SLOPE_VARIANCE) / (math.pi * SLOPE_VARIANCE)
    cos_i = np.sum(n * V, axis=0)
    rp, rs, _, _, _ = fresnel(cos_i, 1.0, N_WATER)
    S = np.zeros((4, V.shape[1]))
    S[0] = 1.0
    S = reflect_matrix(S, rp, rs).real
    if not polarised:
        S[1:] = 0.0
    s = _plane_normal(V, n, _cross(V, e1_v))
    S = _from_plane(S, V, s, e1_v)
    return S * p / (4 * np.abs(V[2]) * math.cos(t0) * mu_n ** 4)


def _from_plane(S, v, s, e1_v):
    """S referred to (s x v, s) turned to (e1_v, v x e1_v)."""
    p = _cross(s, v)
    return _rotate(S, np.sum(e1_v * p, axis=0), np.sum(e1_v * s, axis=0))


# -- the estimate ------------------------------------------------------------

def _phase_into(d, e1, S, u, polarised):
    """Rayleigh's matrix per steradian from (d, e1, S) into directions u
    (3 x n, one each), referred to (nrm x u, nrm): (S_out, nrm)."""
    cos_t = np.clip(np.sum(d * u, axis=0), -1.0, 1.0)
    e2 = _cross(d, e1)
    nrm = _plane_normal(d, u, e2)
    if not polarised:
        out = np.zeros_like(S)
        out[0] = S[0] * 3 * (1 + cos_t ** 2) / (16 * math.pi)
        return out, nrm
    e1_sp = _cross(nrm, d)
    Sj = _rotate(S, np.sum(e1_sp * e1, axis=0), np.sum(e1_sp * e2, axis=0))
    return _rayleigh(Sj, cos_t, per_sr=True), nrm


def estimate(model, z, d, e1, S, tau, V, e1_v, rng, polarised):
    """The light each photon at optical depth z (from the surface: up for
    AOS-II's water, down from the top for AOS-I's air) sends, once
    scattered, into each direction V just above the surface: (4, k)."""
    n, k = d.shape[1], V.shape[1]
    out = np.zeros((4, k))
    for j in range(k):
        v = np.repeat(V[:, j:j + 1], n, axis=1)
        back = -v                                  # travelling against v
        normal, cos_i, w = facets(back, rng)
        if model == "AOS-II":
            rp, rs, tp, ts, cos_t = fresnel(cos_i, 1.0, N_WATER)
            eta = 1.0 / N_WATER
            dt = _unit(eta * back + (eta * cos_i - cos_t) * normal)
            u = -dt                                 # up in the water
            ok = (w > 0) & (dt[2] > 0)
            path = z / np.maximum(np.abs(u[2]), 1e-300)
        else:
            rp, rs = fresnel(cos_i, 1.0, N_WATER)[:2]
            dr = _unit(back + 2 * cos_i * normal)  # up in the air
            u = -dr                                 # down onto the surface
            ok = (w > 0) & (dr[2] < 0)
            path = (tau - z) / np.maximum(np.abs(u[2]), 1e-300)
        Su, nrm = _phase_into(d, e1, S, u, polarised)
        Su = Su * np.exp(-path) / np.maximum(np.abs(u[2]), 1e-300)
        # through the facet into v: the facet's normal on u's side
        nf = -normal if model == "AOS-II" else normal
        ci = np.maximum(-np.sum(nf * u, axis=0), 0.0)
        s = _plane_normal(u, nf, nrm)
        Sp, _ = _to_plane(Su, _cross(nrm, u), u, s)
        if model == "AOS-II":
            _, _, tp, ts, ct = fresnel(ci, N_WATER, 1.0)

            def matrix(X):
                # the radiance's 1 / m^2 as it leaves the water
                return transmit_matrix(X, tp, ts, ci, ct, N_WATER,
                                       1.0) / N_WATER ** 2
        else:
            def matrix(X):
                return reflect_matrix(X, rp, rs).real
        Sp = _through(Sp, matrix, polarised)
        Sv = _from_plane(Sp, v, s, np.repeat(e1_v[:, j:j + 1], n, axis=1))
        out[:, j] = np.sum(np.where(ok, Sv * w, 0.0), axis=1)
    return out


def run(model, wavelength, sun, seed, photons, polarised=True, dirs=None):
    """One batch: (4, k), the light just above the surface in each
    direction per unit planar irradiance, the glint included."""
    rng = np.random.default_rng(seed)
    dirs = directions() if dirs is None else dirs
    V = np.array([d[2] for d in dirs]).T
    e1_v = _meridian_e1(V, [d[3] for d in dirs])
    mu0 = math.cos(math.radians(sun))
    d = np.tile([[math.sqrt(1 - mu0 * mu0)], [0.0], [mu0]], photons)
    e1 = _meridian_e1(d)
    S = np.zeros((4, photons))
    S[0] = 1.0
    if model == "AOS-II":
        omega, tau = WATER[wavelength]
        d, e1, S, ok = cross_surface(d, e1, S, True, "transmit", rng,
                                     polarised)
        d, e1, S = d[:, ok], e1[:, ok], S[:, ok]
        z = np.zeros(d.shape[1])
    else:
        omega, tau = 1.0, ATMOSPHERE[wavelength]
        z = np.zeros(photons)
        direct = math.exp(-tau / mu0)
    total = glint(sun, dirs, polarised) * (direct if model == "AOS-I"
                                            else 1.0)
    while d.shape[1]:
        step = -np.log(1.0 - rng.random(d.shape[1]))
        z = z + step * d[2]
        if model == "AOS-II":
            gone = z >= tau                       # the black bottom
            at_surface = z <= 0
        else:
            gone = z <= 0                         # out of the top
            at_surface = z >= tau
        keep = ~gone
        d, e1, S, z = d[:, keep], e1[:, keep], S[:, keep], z[keep]
        at_surface = at_surface[keep]
        if np.any(at_surface):
            i = np.flatnonzero(at_surface)
            nd, ne, nS, ok = cross_surface(d[:, i], e1[:, i], S[:, i],
                                           model == "AOS-I", "reflect", rng,
                                           polarised)
            d[:, i], e1[:, i], S[:, i] = nd, ne, nS
            z[i] = 0.0 if model == "AOS-II" else tau
            alive = np.ones(d.shape[1], bool)
            alive[i[~ok]] = False
            d, e1, S, z = d[:, alive], e1[:, alive], S[:, alive], z[alive]
            at_surface = at_surface[alive]
        coll = ~at_surface
        if np.any(coll):
            c = np.flatnonzero(coll)
            S[:, c] *= omega
            total += estimate(model, z[c], d[:, c], e1[:, c], S[:, c], tau,
                              V, e1_v, rng, polarised) / photons
            cd, ce, cS = d[:, c], e1[:, c], S[:, c]
            cos_t = _draw_rayleigh_cos(rng, c.size)
            sin_t = np.sqrt(np.maximum(0.0, 1 - cos_t * cos_t))
            psi = 2 * math.pi * rng.random(c.size)
            e2 = _cross(cd, ce)
            nrm = np.cos(psi) * e2 + np.sin(psi) * ce
            e1_sp = _cross(nrm, cd)
            if polarised:
                cS = _rotate(cS, np.sum(e1_sp * ce, axis=0),
                             np.sum(e1_sp * e2, axis=0))
                cS = _rayleigh(cS, cos_t, per_sr=False)
            nd = _unit(cos_t * cd + sin_t * e1_sp)
            d[:, c], e1[:, c], S[:, c] = nd, _cross(nrm, nd), cS
        weak = S[0] < _WEIGHT_FLOOR
        lucky = rng.random(d.shape[1]) < 0.1
        S[:, weak & lucky] *= 10.0
        alive = ~weak | lucky
        d, e1, S, z = d[:, alive], e1[:, alive], S[:, alive], z[alive]
    return total


def main(path: str) -> None:
    dirs = directions()
    scale = np.array(TO_TESTBED)[:, None]
    rows = []
    for model in ("AOS-I", "AOS-II"):
        for wavelength in (350, 450, 550, 650):
            for sun in SUNS:
                base = SEED + 1000 * (model == "AOS-II") + wavelength + \
                    int(sun) * 10_000
                vec = [run(model, wavelength, sun, base + 100 * k, PHOTONS)
                       * scale for k in range(BATCHES)]
                sca = [run(model, wavelength, sun, base + 100 * k + 50,
                           PHOTONS, polarised=False) * scale
                       for k in range(BATCHES)]
                m, s = np.mean(vec, axis=0), np.std(vec, axis=0, ddof=1)
                ms, ss = np.mean(sca, axis=0), np.std(sca, axis=0, ddof=1)
                s, ss = s / math.sqrt(BATCHES), ss / math.sqrt(BATCHES)
                for j, (phi, vza, _, _) in enumerate(dirs):
                    rows.append(dict(
                        model=model, wavelength=wavelength, sun=int(sun),
                        phi=int(phi), vza=int(vza),
                        I=f"{m[0, j]:.8e}", I_se=f"{s[0, j]:.2e}",
                        Q=f"{m[1, j]:.8e}", Q_se=f"{s[1, j]:.2e}",
                        U=f"{m[2, j]:.8e}", U_se=f"{s[2, j]:.2e}",
                        V=f"{m[3, j]:.8e}", V_se=f"{s[3, j]:.2e}",
                        I_scalar=f"{ms[0, j]:.8e}",
                        I_scalar_se=f"{ss[0, j]:.2e}"))
                print(model, wavelength, sun, flush=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        sys.exit(__doc__)

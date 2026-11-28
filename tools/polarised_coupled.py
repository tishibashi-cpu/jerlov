"""A vector Monte Carlo for the coupled atmosphere and ocean, with the
particles' scattering matrix, against Chowdhary et al.'s (2020) testbed:
DECISIONS.md section 148.

    J. Chowdhary, P.-W. Zhai, F. Xu, R. Frouin and D. Ramon (2020),
    J. Quant. Spectrosc. Radiat. Transfer 242, 106717,
    doi:10.1016/j.jqsrt.2019.106717.

Its four models: AOS-I (a molecular atmosphere over a wavy surface, the
ocean black), AOS-II (the surface over pure seawater), AOS-III (the
atmosphere, the surface and pure seawater) and AOS-IV (the same with
marine particles, whose matrix the supplement's Tables S1a and S1b give).
The photons, the surface and the estimates just above it are those of
``tools/polarised_ocean.py`` (section 147); here the light is followed
through the atmosphere, the surface and the water in one path, crossing
the surface as often as it happens to: at each facet reflection or
transmission is drawn with the probability of that branch's flux for the
photon's Stokes vector. At the top of the atmosphere the light is the
light each scattering in the air sends straight out, and the light just
above the surface attenuated through the atmosphere.

    python tools/polarised_coupled.py OUT.csv [MODELS [WAVELENGTHS]]

MODELS and WAVELENGTHS are comma-separated (all by default); the seeds
depend only on the model, the wavelength and the sun, so a run split
into parts gives the same numbers.

The CSV holds R = pi L / (mu0 S0) for I, Q and U in the testbed's
conventions (``polarised_ocean.TO_TESTBED``), just above the surface (SRF)
and at the top of the atmosphere (TOA).

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
from polarised_ocean import (  # noqa: E402
    ATMOSPHERE, N_WATER, SLOPE_VARIANCE, SUNS, TO_TESTBED, WATER,
    _plane_normal, _through, _to_plane, directions, fresnel,
    glint, reflect_matrix, transmit_matrix)

PARTICLES_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples",
    "data", "polarisation", "chowdhary2020_particles.csv")

#: Table 2, AOS-IV: single scattering albedo, optical thickness (100 m),
#: b_w, b_p (per metre) and the particles' table (S1a for [Chl] 0.03,
#: S1b for 3 mg m^-3).
PARTICULATE = {350: (0.72114137, 7.71, 0.0134, 0.0422, "S1a"),
               450: (0.72519084, 5.24, 0.0045, 0.0335, "S1a"),
               550: (0.88340267, 91.34, 0.0019, 0.8050, "S1b"),
               650: (0.68034101, 118.47, 0.0010, 0.8050, "S1b")}
MODELS = ("AOS-I", "AOS-II", "AOS-III", "AOS-IV")
PHOTONS, BATCHES, SEED = 100_000, 10, 2148
_WEIGHT_FLOOR = 1e-4
_DEPTH_SCALE = 0.1


# -- the scatterers ----------------------------------------------------------

class Rayleigh:
    """Rayleigh's matrix (depolarisation ``delta``)."""

    def __init__(self, delta=0.0):
        self.delta = delta

    def per_sr(self, S, cos_t):
        return _rayleigh(S, cos_t, per_sr=True, delta=self.delta)

    def reduced(self, S, cos_t):
        return _rayleigh(S, cos_t, per_sr=False, delta=self.delta)

    def draw(self, rng, n):
        return _draw_rayleigh_cos(rng, n, self.delta)

    def phase(self, cos_t):
        one = np.zeros((4, cos_t.size))
        one[0] = 1.0
        return self.per_sr(one, cos_t)[0]


class Particles:
    """A tabulated matrix: F11, F21, F33 and F43 over 4 pi by angle, with
    F22 = F11, F44 = F33, F34 = -F43 (spheres). F11 is interpolated
    linearly in its log over the angle and normalised on a grid of
    0.0001 degree; the other elements as ratios to F11, linearly."""

    def __init__(self, table, path=PARTICLES_CSV):
        with open(path) as handle:
            rows = [r for r in csv.DictReader(handle) if r["table"] == table]
        self.angle = np.radians([float(r["angle"]) for r in rows])
        f = {k: np.array([float(r[k]) for r in rows])
             for k in ("F11", "F21", "F33", "F43")}
        self.log_f11 = np.log(f["F11"])
        self.r21 = f["F21"] / f["F11"]
        self.r33 = f["F33"] / f["F11"]
        self.r43 = f["F43"] / f["F11"]
        grid = np.linspace(0.0, math.pi, 1_800_001)
        density = np.exp(np.interp(grid, self.angle, self.log_f11)) \
            * np.sin(grid)
        cdf = np.concatenate([[0.0], np.cumsum(
            (density[1:] + density[:-1]) / 2 * np.diff(grid))]) * 2 * math.pi
        #: the interpolated phase function's integral over 4 pi before
        #: normalising (DECISIONS.md section 148, check 1)
        self.integral = float(cdf[-1])
        self.grid, self.cdf = grid, cdf / cdf[-1]
        # the same interpolation, read from a table every 0.001 degree (the
        # tabulated angles are multiples of it, so this is exact)
        self._fine = np.radians(np.arange(180_001) / 1000)
        self._step = self._fine[1]
        self._tables = np.stack([
            np.interp(self._fine, self.angle, self.log_f11),
            np.interp(self._fine, self.angle, self.r21),
            np.interp(self._fine, self.angle, self.r33),
            np.interp(self._fine, self.angle, self.r43)])

    def _lookup(self, cos_t, rows):
        x = np.arccos(np.clip(cos_t, -1.0, 1.0)) / self._step
        i = np.minimum(x.astype(int), self._fine.size - 2)
        f = x - i
        r = np.asarray(rows)[:, None]
        a = self._tables[r, i]
        b = self._tables[r, i + 1]
        return a + f * (b - a)

    def phase(self, cos_t):
        return np.exp(self._lookup(cos_t, [0])[0]) / self.integral

    def _apply(self, S, cos_t):
        r21, r33, r43 = self._lookup(cos_t, [1, 2, 3])
        out = np.empty_like(S)
        out[0] = S[0] + r21 * S[1]
        out[1] = r21 * S[0] + S[1]
        out[2] = r33 * S[2] - r43 * S[3]
        out[3] = r43 * S[2] + r33 * S[3]
        return out

    def per_sr(self, S, cos_t):
        return self._apply(S, cos_t) * self.phase(cos_t)

    def reduced(self, S, cos_t):
        return self._apply(S, cos_t)

    def draw(self, rng, n):
        return np.cos(np.interp(rng.random(n), self.cdf, self.grid))


class Medium:
    """A mixture: each scatterer with its share of the scattering
    coefficient, and the single scattering albedo."""

    def __init__(self, omega, parts):
        self.omega = omega
        self.parts = parts                    # [(share, scatterer)]

    def per_sr(self, S, cos_t, polarised):
        if not polarised:
            out = np.zeros_like(S)
            out[0] = S[0] * sum(w * p.phase(cos_t) for w, p in self.parts)
            return out
        return sum(w * p.per_sr(S, cos_t) for w, p in self.parts)

    def scatter(self, S, rng, polarised):
        """Draw the scatterer and the angle; S reduced by that scatterer's
        matrix over its (1,1) element. Returns (cos_t, S_function), the
        function to apply once S is in the scattering plane."""
        n = S.shape[1]
        cos_t = np.empty(n)
        which = np.zeros(n, int)
        if len(self.parts) > 1:
            u = rng.random(n)
            edge = np.cumsum([w for w, _ in self.parts])
            which = np.searchsorted(edge, u, side="right")
            which = np.minimum(which, len(self.parts) - 1)
        for k, (_, part) in enumerate(self.parts):
            sel = which == k
            if np.any(sel):
                cos_t[sel] = part.draw(rng, int(sel.sum()))

        def reduce(Sp):
            if not polarised:
                return Sp
            out = np.empty_like(Sp)
            for k, (_, part) in enumerate(self.parts):
                sel = which == k
                if np.any(sel):
                    out[:, sel] = part.reduced(Sp[:, sel], cos_t[sel])
            return out
        return cos_t, reduce


def model(name, wavelength):
    """(the atmosphere's optical thickness, its medium, the water's
    optical thickness or None, its medium)."""
    air = Medium(1.0, [(1.0, Rayleigh())])
    tau_air = ATMOSPHERE[wavelength] if name in ("AOS-I", "AOS-III",
                                                 "AOS-IV") else 0.0
    if name == "AOS-I":
        return tau_air, air, None, None
    if name in ("AOS-II", "AOS-III"):
        omega, tau = WATER[wavelength]
        return tau_air, air, tau, Medium(omega, [(1.0, Rayleigh())])
    omega, tau, bw, bp, table = PARTICULATE[wavelength]
    return tau_air, air, tau, Medium(omega, [(bw / (bw + bp), Rayleigh()),
                                             (bp / (bw + bp),
                                              Particles(table))])


# -- the surface -------------------------------------------------------------

def facets(d, rng):
    """For light travelling in directions d (3 x n), a facet drawn with the
    probability of the share of the beam it intercepts: along the light's
    horizontal direction the slope x (in units of its standard deviation
    s) has the density phi(x) (c - x) on x < c, c = cot(theta) / s, drawn
    by rejection from phi(x) (c + |x|); across it the slope is Gaussian.
    The weight is then the mean share, Phi(c) + phi(c) / c, the same for
    every facet, not divided by anything (no renormalisation): the
    expectation of section 147's facets, without their spread
    (DECISIONS.md section 148). Returns (normal, cos_i, w)."""
    n = d.shape[1]
    s = math.sqrt(SLOPE_VARIANCE / 2)
    mu = np.abs(d[2])
    sin = np.sqrt(np.maximum(0.0, 1 - mu * mu))
    c = np.where(sin > 1e-12, mu / np.maximum(sin, 1e-300) / s, np.inf)
    x = np.empty(n)
    todo = np.arange(n)
    while todo.size:
        ck = c[todo]
        flat = rng.random(todo.size) * (ck + math.sqrt(2 / math.pi)) < ck
        g = rng.normal(0.0, 1.0, todo.size)
        r = np.sqrt(-2 * np.log(1 - rng.random(todo.size))) * np.where(
            rng.random(todo.size) < 0.5, -1.0, 1.0)
        cand = np.where(flat | ~np.isfinite(ck), g, r)
        keep = rng.random(todo.size) * (ck + np.abs(cand)) < (ck - cand)
        keep |= ~np.isfinite(ck)
        x[todo[keep]] = cand[keep]
        todo = todo[~keep]
    y = rng.normal(0.0, 1.0, n)
    h = np.where(sin > 1e-12, d[:2] / np.maximum(sin, 1e-300),
                 np.array([[1.0], [0.0]]))
    zx = s * x * h[0] - s * y * h[1]
    zy = s * x * h[1] + s * y * h[0]
    side = np.where(d[2] > 0, -1.0, 1.0)
    # from below the facet facing the light has the opposite slope
    zx, zy = np.where(d[2] > 0, zx, -zx), np.where(d[2] > 0, zy, -zy)
    normal = np.array([-zx * side, -zy * side, side]) / np.sqrt(
        1 + zx * zx + zy * zy)
    cos_i = np.maximum(-np.sum(normal * d, axis=0), 0.0)
    cc = np.where(np.isfinite(c), c, 0.0)
    w = np.where(np.isfinite(c),
                 0.5 * np.vectorize(math.erfc)(-cc / math.sqrt(2))
                 + np.exp(-cc * cc / 2) / math.sqrt(2 * math.pi)
                 / np.maximum(cc, 1e-300), 1.0)
    return normal, cos_i, w


def surface(d, e1, S, from_air, rng, polarised):
    """Light at the surface, one facet each: reflected or transmitted with
    the probability of that branch's flux, the weight kept (times the
    facet's). Returns (d, e1, S, ok, crossed)."""
    normal, cos_i, w = facets(d, rng)
    n1 = np.where(from_air, 1.0, N_WATER)
    n2 = np.where(from_air, N_WATER, 1.0)
    rp, rs, tp, ts, cos_t = fresnel(cos_i, n1, n2)
    s = _plane_normal(d, normal, _cross(d, e1))
    Sp, _ = _to_plane(S, e1, d, s)
    Sr = _through(Sp, lambda X: reflect_matrix(X, rp, rs).real, polarised)
    St = _through(Sp, lambda X: transmit_matrix(X, tp, ts, cos_i, cos_t,
                                                 n1, n2), polarised)
    total = Sr[0] + St[0]
    p_r = np.where(total > 0, Sr[0] / np.where(total > 0, total, 1), 1.0)
    crossed = rng.random(d.shape[1]) >= p_r
    eta = n1 / n2
    refl = _unit(d + 2 * cos_i * normal)
    trans = _unit(eta * d + (eta * cos_i - cos_t) * normal)
    out_d = np.where(crossed, trans, refl)
    share = np.where(crossed, St[0], Sr[0])
    out_S = np.where(crossed, St, Sr) * np.where(
        share > 0, total / np.where(share > 0, share, 1), 0.0) * w
    # light goes on down into the water, or up into the air
    down = np.where(crossed, from_air, ~from_air)
    ok = (w > 0) & (total > 0) & np.where(down, out_d[2] > 0, out_d[2] < 0)
    return out_d, _cross(s, out_d), out_S, ok, crossed


# -- the estimates -----------------------------------------------------------

def _into(medium, d, e1, S, u, polarised):
    """The medium's matrix per steradian from (d, e1, S) into u (one each),
    referred to (nrm x u, nrm)."""
    cos_t = np.clip(np.sum(d * u, axis=0), -1.0, 1.0)
    e2 = _cross(d, e1)
    nrm = _plane_normal(d, u, e2)
    if polarised:
        e1_sp = _cross(nrm, d)
        S = _rotate(S, np.sum(e1_sp * e1, axis=0), np.sum(e1_sp * e2, axis=0))
    return medium.per_sr(S, cos_t, polarised), nrm


def _rotation(c, s):
    """The 4 x 4 matrix of _rotate for axes turned by chi (cos c, sin s)."""
    c2, s2 = c * c - s * s, 2 * s * c
    R = np.zeros((c.size, 4, 4))
    R[:, 0, 0] = R[:, 3, 3] = 1.0
    R[:, 1, 1] = R[:, 2, 2] = c2
    R[:, 1, 2], R[:, 2, 1] = s2, -s2
    return R


class Pool:
    """For each direction v just above the surface, ``size`` facets drawn
    for light travelling against v, once a batch, and for each the
    direction u the light must have below (``kind`` "water": refracted
    into the water) or above ("sky": reflected) and the matrix that takes
    it, referred to the facet's plane of incidence, into v's meridian
    plane (Fresnel's, the facet's weight, and for the water 1 / m^2 on
    the radiance). Each estimate picks one at random: drawn afresh each
    batch, the pool's own scatter is part of the batches' spread."""

    def __init__(self, kind, V, e1_v, rng, polarised, size=10_000):
        self.kind, self.size, self.entries = kind, size, []
        for j in range(V.shape[1]):
            v = np.repeat(V[:, j:j + 1], size, axis=1)
            back = -v
            normal, cos_i, w = facets(back, rng)
            rp, rs, _, _, cos_t = fresnel(cos_i, 1.0, N_WATER)
            if kind == "water":
                eta = 1.0 / N_WATER
                dt = _unit(eta * back + (eta * cos_i - cos_t) * normal)
                u, ok, nf = -dt, (w > 0) & (dt[2] > 0), -normal
            else:
                dr = _unit(back + 2 * cos_i * normal)
                u, ok, nf = -dr, (w > 0) & (dr[2] < 0), normal
            ci = np.maximum(-np.sum(nf * u, axis=0), 0.0)
            s = _plane_normal(u, nf, _cross(u, _meridian_e1(u)))
            if kind == "water":
                _, _, tp, ts, ct = fresnel(ci, N_WATER, 1.0)

                def matrix(X, tp=tp, ts=ts, ci=ci, ct=ct):
                    return transmit_matrix(X, tp, ts, ci, ct, N_WATER,
                                           1.0) / N_WATER ** 2
            else:
                def matrix(X, rp=rp, rs=rs):
                    return reflect_matrix(X, rp, rs).real
            A = np.zeros((size, 4, 4))
            for col in range(4):
                X = np.zeros((4, size))
                X[col] = 1.0
                A[:, :, col] = _through(X, matrix, polarised).T
            p_out = _cross(s, v)
            m = np.repeat(e1_v[:, j:j + 1], size, axis=1)
            R = _rotation(np.sum(m * p_out, axis=0), np.sum(m * s, axis=0))
            A = np.einsum("nij,njk->nik", R, A) * \
                np.where(ok, w, 0.0)[:, None, None]
            self.entries.append((u, 1 / np.maximum(np.abs(u[2]), 1e-300),
                                 _cross(s, u), A))


def above_surface(pool, medium, z, d, e1, S, tau_air, rng, polarised):
    """The light each photon, once scattered, sends into each direction
    just above the surface, by way of a facet from ``pool``: from the air
    at optical depth z, reflected ("sky"), or from the water at optical
    depth z, refracted ("water"). (4, k)."""
    n = d.shape[1]
    out = np.zeros((4, len(pool.entries)))
    depth = z if pool.kind == "water" else tau_air - z
    for j, (U, inv_mu, P, A) in enumerate(pool.entries):
        pick = rng.integers(pool.size, size=n)
        u, im, p_in = U[:, pick], inv_mu[pick], P[:, pick]
        Su, nrm = _into(medium, d, e1, S, u, polarised)
        Su = Su * (np.exp(-depth * im) * im)
        Su = _rotate(Su, np.sum(p_in * _cross(nrm, u), axis=0),
                     np.sum(p_in * nrm, axis=0))
        out[:, j] = np.einsum("nij,jn->i", A[pick], Su)
    return out


def out_of_top(medium, z, d, e1, S, V, e1_v, polarised):
    """The light each photon in the air at optical depth z, once
    scattered, sends straight out of the top in each direction V: (4, k)."""
    n, k = d.shape[1], V.shape[1]
    out = np.zeros((4, k))
    for j in range(k):
        v = np.repeat(V[:, j:j + 1], n, axis=1)
        Sv, nrm = _into(medium, d, e1, S, v, polarised)
        mu = abs(float(V[2, j]))
        Sv = Sv * np.exp(-z / mu) / mu
        if polarised:
            m = np.repeat(e1_v[:, j:j + 1], n, axis=1)
            Sv = _rotate(Sv, np.sum(m * _cross(nrm, v), axis=0),
                         np.sum(m * nrm, axis=0))
        out[:, j] = np.sum(Sv, axis=1)
    return out


# -- the photons -------------------------------------------------------------

def run(name, wavelength, sun, seed, photons, polarised=True, dirs=None):
    """One batch: ((4, k) just above the surface, (4, k) at the top), per
    unit planar irradiance at the top of the atmosphere."""
    rng = np.random.default_rng(seed)
    dirs = directions() if dirs is None else dirs
    V = np.array([x[2] for x in dirs]).T
    e1_v = _meridian_e1(V, [x[3] for x in dirs])
    tau_air, air_medium, tau_water, water_medium = model(name, wavelength)
    mu0 = math.cos(math.radians(sun))
    d = np.tile([[math.sqrt(1 - mu0 * mu0)], [0.0], [mu0]], photons)
    e1 = _meridian_e1(d)
    S = np.zeros((4, photons))
    S[0] = 1.0
    z = np.zeros(photons)
    air = np.ones(photons, bool)
    srf = glint(sun, dirs, polarised) * math.exp(-tau_air / mu0)
    sky_pool = Pool("sky", V, e1_v, rng, polarised) if tau_air > 0 else None
    water_pool = Pool("water", V, e1_v, rng, polarised) \
        if tau_water is not None else None
    top = np.zeros_like(srf)
    while d.shape[1]:
        step = -np.log(1.0 - rng.random(d.shape[1]))
        z = z + step * d[2]
        water_tau = tau_water if tau_water is not None else 0.0
        gone = np.where(air, z <= 0, z >= water_tau)
        at_surface = np.where(air, z >= tau_air, z <= 0) & ~gone
        keep = ~gone
        d, e1, S, z, air = d[:, keep], e1[:, keep], S[:, keep], z[keep], \
            air[keep]
        at_surface = at_surface[keep]
        alive = np.ones(d.shape[1], bool)
        if np.any(at_surface):
            i = np.flatnonzero(at_surface)
            nd, ne, nS, ok, crossed = surface(d[:, i], e1[:, i], S[:, i],
                                              air[i], rng, polarised)
            now_air = np.where(crossed, ~air[i], air[i])
            if tau_water is None:              # a black ocean
                ok &= now_air
            d[:, i], e1[:, i], S[:, i] = nd, ne, nS
            air[i] = now_air
            z[i] = np.where(now_air, tau_air, 0.0)
            alive[i[~ok]] = False
        coll = ~at_surface & alive
        for in_air, medium in ((True, air_medium), (False, water_medium)):
            c = np.flatnonzero(coll & (air == in_air))
            if not c.size:
                continue
            S[:, c] *= medium.omega
            args = (z[c], d[:, c], e1[:, c], S[:, c])
            if in_air:
                srf += above_surface(sky_pool, medium, *args, tau_air, rng,
                                     polarised) / photons
                top += out_of_top(medium, *args, V, e1_v, polarised) \
                    / photons
            else:
                srf += above_surface(water_pool, medium, *args, tau_air,
                                     rng, polarised) / photons
            cd, ce, cS = d[:, c], e1[:, c], S[:, c]
            cos_t, reduce = medium.scatter(cS, rng, polarised)
            sin_t = np.sqrt(np.maximum(0.0, 1 - cos_t * cos_t))
            psi = 2 * math.pi * rng.random(c.size)
            e2 = _cross(cd, ce)
            nrm = np.cos(psi) * e2 + np.sin(psi) * ce
            e1_sp = _cross(nrm, cd)
            if polarised:
                cS = _rotate(cS, np.sum(e1_sp * ce, axis=0),
                             np.sum(e1_sp * e2, axis=0))
                cS = reduce(cS)
            nd = _unit(cos_t * cd + sin_t * e1_sp)
            d[:, c], e1[:, c], S[:, c] = nd, _cross(nrm, nd), cS
        # Russian roulette on the weight, and in the water on the weight
        # times exp(-0.1 z), which ends light deep down sooner (unbiased:
        # the survivors carry the rest)
        weak = S[0] * np.where(air, 1.0, np.exp(-_DEPTH_SCALE * z)) \
            < _WEIGHT_FLOOR
        lucky = rng.random(d.shape[1]) < 0.1
        S[:, weak & lucky] *= 10.0
        alive &= ~weak | lucky
        d, e1, S, z, air = d[:, alive], e1[:, alive], S[:, alive], \
            z[alive], air[alive]
    # the light just above the surface, attenuated straight out
    top += srf * np.exp(-tau_air / np.abs(V[2]))
    return srf, top


def main(path: str, models=MODELS, wavelengths=(350, 450, 550, 650)) -> None:
    dirs = directions()
    scale = np.array(TO_TESTBED)[:, None]
    rows = []
    for name in models:
        for wavelength in wavelengths:
            for sun in SUNS:
                base = SEED + 1000 * MODELS.index(name) + wavelength + \
                    int(sun) * 10_000
                vec = [run(name, wavelength, sun, base + 100 * k, PHOTONS)
                       for k in range(BATCHES)]
                sca = [run(name, wavelength, sun, base + 100 * k + 50,
                           PHOTONS, polarised=False) for k in range(BATCHES)]
                for level, idx in (("SRF", 0), ("TOA", 1)):
                    if name == "AOS-II" and level == "TOA":
                        continue
                    v = np.array([b[idx] * scale for b in vec])
                    s = np.array([b[idx] * scale for b in sca])
                    m, se = v.mean(0), v.std(0, ddof=1) / math.sqrt(BATCHES)
                    ms = s.mean(0)
                    sse = s.std(0, ddof=1) / math.sqrt(BATCHES)
                    for j, (phi, vza, _, _) in enumerate(dirs):
                        rows.append(dict(
                            model=name, level=level, wavelength=wavelength,
                            sun=int(sun), phi=int(phi), vza=int(vza),
                            I=f"{m[0, j]:.8e}", I_se=f"{se[0, j]:.2e}",
                            Q=f"{m[1, j]:.8e}", Q_se=f"{se[1, j]:.2e}",
                            U=f"{m[2, j]:.8e}", U_se=f"{se[2, j]:.2e}",
                            V=f"{m[3, j]:.8e}", V_se=f"{se[3, j]:.2e}",
                            I_scalar=f"{ms[0, j]:.8e}",
                            I_scalar_se=f"{sse[0, j]:.2e}"))
                print(name, wavelength, sun, flush=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    if 2 <= len(sys.argv) <= 4:
        main(sys.argv[1],
             tuple(sys.argv[2].split(",")) if len(sys.argv) > 2 else MODELS,
             tuple(int(w) for w in sys.argv[3].split(","))
             if len(sys.argv) > 3 else (350, 450, 550, 650))
    else:
        sys.exit(__doc__)

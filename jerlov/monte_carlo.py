"""A light field under water by Monte Carlo. DECISIONS.md sections 38 to
40 and 138.

Photons enter through the surface, refracted and thinned by Fresnel
transmission: a flat surface, or, since 1.34.0, one facet of Cox and
Munk's isotropic wave slopes at each crossing (DECISIONS.md section 139).
Each travels a free path drawn from exp(-c s), and at its end is
scattered, never absorbed: instead its weight is multiplied by
b / c. Scattering is by pure water or by particles in proportion to their
share of b, at an angle drawn from that one's phase function and an
azimuth drawn uniformly. Light reaching the surface from below is
reflected back by the Fresnel reflectance (at a facet, if there are
waves) and the rest leaves; with waves, light that a facet sends towards
the surface again meets another facet, if the caller asks for it (since
1.35.0, DECISIONS.md section 141); light
reaching a bottom, if there is one, is reflected by its albedo into a
cosine-weighted direction. A photon whose weight falls below 1e-4
survives with probability 1/10 and ten times the weight.

Radiance and scalar irradiance at a depth are the path length photons
spend in a slab around it, per unit thickness; planar irradiance is the
weight crossing the depth. rrs straight up just below the surface is a
collision estimator: each scattering adds its weight times the phase
function towards straight up times exp(-c' z), each arrival at the bottom
its weight times albedo / pi times exp(-c' H), over the planar irradiance
just below the surface; c' is c less the particles' scattering that goes
straight on, which does not turn light out of the line of sight.

The engine is the one examples/radiance_distribution.py carried from
0.14.4 to 1.32.4 (checked against the exact solution for isotropic
scattering, Gershun's law, Jerlov's Kd and Tyler's lake; DECISIONS.md
sections 38 to 40), moved here with a bottom and the rrs estimator, which
draw no random number when not used: with no bottom it gives that
example's numbers bit for bit. Against Mobley et al.'s (1993) canonical
problems, solved by seven codes with HydroLight among them, it agrees in
46 of 51 published values (DECISIONS.md section 140).

Every choice that sets the result is a required argument; nothing is
defaulted (DECISIONS.md section 138, which amends section 12). Left out:
an atmosphere, polarisation, inelastic scattering (Raman, fluorescence),
water that varies with depth, and of the waves the wind's direction,
whitecaps, and either light meeting a second facet or the surface's shape
between one facet and the next.
"""

from __future__ import annotations

import functools
import math
import warnings
from dataclasses import dataclass
from typing import Any

import numpy as np

from . import _data
from .fournier_forand import FournierForand
from .petzold import ScatteringFunction
from .backscattering import pure_water_scattering, pure_water_vsf
from .water import MissingQuantityError

#: What the method does not include, said in every result; the second
#: entry is for a flat surface, the third for waves.
LEFT_OUT = (
    "an atmosphere: the sun's beam or a sky of uniform radiance is given "
    "just above the surface",
    "waves: the surface is flat",
    "polarisation: the scalar equation",
    "inelastic scattering: no Raman scattering, no fluorescence",
    "water that varies with depth: one homogeneous layer",
)
_LEFT_OUT_WAVES = (
    "of the waves: the wind's direction (Cox and Munk's isotropic slopes), "
    "whitecaps and foam, and light meeting a second facet")
_LEFT_OUT_ALL_FACETS = (
    "of the waves: the wind's direction (Cox and Munk's isotropic slopes), "
    "whitecaps and foam, and the surface's shape between one facet and the "
    "next: each facet light meets is drawn independently")

#: Cox and Munk (1954), J. Opt. Soc. Am. 44, 838-850, eq. (42), p. 221,
#: clean surface, converted from cm/s: the mean square slope is
#: 0.003 + 5.12e-3 W, W the wind in m/s at 12.5 m (41 ft, p. 199); as
#: transcribed in examples/wave_focusing.py (DECISIONS.md sections 44, 139).
COX_MUNK_MEAN_SQUARE_SLOPE = (0.003, 5.12e-3)

#: Below this weight a photon plays Russian roulette: it survives with
#: probability 1/10 at ten times the weight.
_WEIGHT_FLOOR = 1e-4


# -- the phase functions -----------------------------------------------------

def _inverse_cdf(angles_deg, vsf):
    """Cumulative probability against cos(angle), to draw angles from."""
    th = np.radians(angles_deg)
    f = vsf * 2 * np.pi * np.sin(th)
    cdf = np.concatenate([[0.0], np.cumsum(0.5 * (f[1:] + f[:-1])
                                           * np.diff(th))])
    return cdf / cdf[-1], np.cos(th), cdf[-1]


def _particle_phase(phase_function, cut_deg, salinity_psu):
    """The particles' phase function from ``cut_deg``: a table to draw
    from, the share of the particles' scattering below the cut (taken to
    go straight on), and the phase function per steradian on the table's
    angles, for the rrs estimator."""
    grid = np.geomspace(cut_deg, 180.0, 3000)
    grid[-1] = 180.0
    if isinstance(phase_function, ScatteringFunction):
        p = phase_function
        particles = np.asarray(p.vsf_at(grid)) - np.asarray(pure_water_vsf(
            grid, p.wavelength_nm, salinity_psu=salinity_psu))
        if np.any(particles <= 0):
            raise ValueError(
                f"{p.station}: pure water at salinity {salinity_psu:g} "
                "exceeds the measurement at some angle")
        cdf, cos_angle, measured = _inverse_cdf(grid, particles)
        b_particles = p.b - float(pure_water_scattering(
            p.wavelength_nm, salinity_psu=salinity_psu))
        per_sr = particles / b_particles
        straight = 1 - measured / b_particles
    else:
        per_sr = np.asarray(phase_function.phase_function(grid), dtype=float)
        cdf, cos_angle, measured = _inverse_cdf(grid, per_sr)
        straight = float(phase_function.cumulative(cut_deg))
        # the table's integral is 1 - straight, to the trapezoid's error;
        # its shape is what is drawn from, the share below is exact
    return dict(cdf=cdf, cos=cos_angle, straight=straight,
                angles=np.radians(grid), per_sr=per_sr)


def _water_phase(wavelength_nm, salinity_psu):
    grid = np.linspace(0.0, 180.0, 1801)
    vsf = np.asarray(pure_water_vsf(grid, wavelength_nm,
                                    salinity_psu=salinity_psu))
    cdf, cos_angle, total = _inverse_cdf(grid, vsf)
    return dict(cdf=cdf, cos=cos_angle, angles=np.radians(grid),
                per_sr=vsf / total)


def _per_sr(table, angle):
    """A phase function per steradian at ``angle`` (radians), from its
    table, log-linear between the table's angles; 0 below the table."""
    angles, values = table["angles"], table["per_sr"]
    out = np.interp(angle, angles, np.log(np.maximum(values, 1e-300)))
    return np.where(angle < angles[0], 0.0, np.exp(out))


# -- the photons -------------------------------------------------------------

def _fresnel(mu, n1, n2):
    """Reflectance of a flat surface for unpolarised light; 1 beyond the
    critical angle."""
    mu = np.abs(mu)
    sin_t = n1 / n2 * np.sqrt(np.maximum(0.0, 1 - mu * mu))
    out = np.ones_like(mu)
    ok = sin_t < 1
    ct, ci = np.sqrt(1 - sin_t[ok] ** 2), mu[ok]
    rs = (n1 * ci - n2 * ct) / (n1 * ci + n2 * ct)
    rp = (n1 * ct - n2 * ci) / (n1 * ct + n2 * ci)
    out[ok] = 0.5 * (rs * rs + rp * rp)
    return out


def _turn(ux, uy, uz, cos_t, rng):
    """Turn each direction by its scattering angle, at a random azimuth."""
    phi = 2 * np.pi * rng.random(ux.size)
    sin_t = np.sqrt(np.maximum(0.0, 1 - cos_t ** 2))
    cp, sp = np.cos(phi), np.sin(phi)
    perp = np.sqrt(np.maximum(1e-12, 1 - uz * uz))
    pole = np.abs(uz) > 1 - 1e-12
    nx = np.where(pole, sin_t * cp,
                  sin_t * (ux * uz * cp - uy * sp) / perp + ux * cos_t)
    ny = np.where(pole, sin_t * sp,
                  sin_t * (uy * uz * cp + ux * sp) / perp + uy * cos_t)
    nz = np.where(pole, np.sign(uz) * cos_t, -sin_t * cp * perp + uz * cos_t)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    return nx / norm, ny / norm, nz / norm


@functools.lru_cache(maxsize=16)
def _front_share_table(slope_variance):
    """For light meeting the surface at cosine mu (to the vertical), the
    mean over the facets that face it, slopes Gaussian, of the share of
    the beam each intercepts over a flat surface's: by quadrature, on a
    grid of mu. Facets turned away from the light are in shadow; dividing
    by this mean keeps the light that reaches the surface equal to what
    crosses a horizontal plane (DECISIONS.md section 140)."""
    sd = math.sqrt(slope_variance / 2)
    g = np.linspace(-8 * sd, 8 * sd, 401)
    zx, zy = np.meshgrid(g, g)
    p = np.exp(-(zx * zx + zy * zy) / (2 * sd * sd))
    norm = np.sqrt(1 + zx * zx + zy * zy)
    nx, nz = zx / norm, -1 / norm
    mus = np.concatenate([np.geomspace(1e-3, 0.2, 80, endpoint=False),
                          np.linspace(0.2, 1.0, 81)])
    share = np.empty(mus.size)
    for k, mu in enumerate(mus):
        dn = math.sqrt(1 - mu * mu) * nx + mu * nz
        front = dn < 0
        share[k] = np.sum(p * front * (-dn) / (-nz * mu)) / np.sum(p * front)
    return mus, share


def _facets(d, slope_variance, rng):
    """Facet normals for directions ``d`` (3 x n, unit) meeting a surface
    whose slopes are Gaussian, each direction with variance
    ``slope_variance`` / 2 (Cox and Munk's isotropic form), and the weight
    of each, the share of the beam it intercepts over a flat surface's.

    The normal is the one on the side the light comes from (z is positive
    downwards: upward for light from the air, downward for light from the
    water). A facet that faces away from the light is drawn again.
    """
    n = d.shape[1]
    from_air = d[2] > 0
    normal = np.empty((3, n))
    todo = np.arange(n)
    sd = math.sqrt(slope_variance / 2)
    while todo.size:
        zx = rng.normal(0.0, sd, todo.size)
        zy = rng.normal(0.0, sd, todo.size)
        norm = np.sqrt(1 + zx * zx + zy * zy)
        side = np.where(from_air[todo], -1.0, 1.0)
        cand = np.array([-zx * side, -zy * side, side]) / norm
        ok = np.sum(cand * d[:, todo], axis=0) < 0
        normal[:, todo[ok]] = cand[:, ok]
        todo = todo[~ok]
    cos_i = -np.sum(normal * d, axis=0)
    w = cos_i / (np.abs(normal[2]) * np.abs(d[2]))
    mus, share = _front_share_table(slope_variance)
    w = w / np.interp(np.abs(d[2]), mus, share)
    return normal, cos_i, w


def _fresnel_cos(cos_i, n1, n2):
    """Fresnel's reflectance for unpolarised light at a local angle of
    incidence, and the cosine of the refracted angle (0 where all is
    reflected)."""
    sin_t = n1 / n2 * np.sqrt(np.maximum(0.0, 1 - cos_i * cos_i))
    out = np.ones_like(cos_i)
    cos_t = np.zeros_like(cos_i)
    ok = sin_t < 1
    ct, ci = np.sqrt(1 - sin_t[ok] ** 2), cos_i[ok]
    rs = (n1 * ci - n2 * ct) / (n1 * ci + n2 * ct)
    rp = (n1 * ct - n2 * ci) / (n1 * ct + n2 * ci)
    out[ok] = 0.5 * (rs * rs + rp * rp)
    cos_t[ok] = ct
    return out, cos_t


#: With ``surface_facets="all"``, light still at the surface after this many
#: facets is dropped (DECISIONS.md section 141; not expected to happen).
_MAX_FACETS = 50


def _follow_surface(d, from_air, slope_variance, n_water, rng):
    """Light at a wavy surface followed from facet to facet until it
    leaves (DECISIONS.md section 141).

    ``d`` (3 x n, unit) are the directions arriving, ``from_air`` whether
    each arrives from the air. Returns the directions it leaves in, the
    factor on each weight that stays in the water (0 for light that left
    to the air), the factor that left to the air, and the factor that
    reached a second facet. At each facet a branch that leaves to the air
    takes its Fresnel share of the weight; when neither does, one branch
    is chosen with its share as the probability and the weight is kept.
    """
    d = d.copy()
    n = d.shape[1]
    air = np.asarray(from_air, bool).copy()
    stay = np.ones(n)
    gone = np.zeros(n)
    second = np.zeros(n)
    todo = np.arange(n)
    for k in range(_MAX_FACETS):
        if not todo.size:
            break
        if k == 1:
            second[todo] = stay[todo]
        dk, ak = d[:, todo], air[todo]
        normal, cos_i, w = _facets(dk, slope_variance, rng)
        r = np.empty(todo.size)
        cos_t = np.empty(todo.size)
        for side, n1, n2 in ((ak, 1.0, n_water), (~ak, n_water, 1.0)):
            r[side], cos_t[side] = _fresnel_cos(cos_i[side], n1, n2)
        eta = np.where(ak, 1.0 / n_water, n_water)
        refl = dk + 2 * cos_i * normal
        refl /= np.linalg.norm(refl, axis=0)
        trans = eta * dk + (eta * cos_i - cos_t) * normal
        trans /= np.maximum(np.linalg.norm(trans, axis=0), 1e-300)
        stay[todo] *= w
        # from the air, reflected light travelling up leaves; from below,
        # refracted light travelling up leaves (none if all is reflected)
        refl_leaves = ak & (refl[2] < 0)
        trans_leaves = ~ak & (trans[2] < 0) & (r < 1)
        share_left = np.where(refl_leaves, r, np.where(trans_leaves, 1 - r,
                                                       0.0))
        gone[todo] += stay[todo] * share_left
        stay[todo] *= 1 - share_left
        pick = rng.random(todo.size) < r
        reflect = np.where(refl_leaves, False,
                           np.where(trans_leaves, True, pick))
        out = np.where(reflect, refl, trans)
        # a reflection keeps the side; a refraction crosses it
        side_now = np.where(reflect, ak, ~ak)
        d[:, todo] = out
        air[todo] = side_now
        # in the water travelling down it is done; anything else meets the
        # surface again (in the air travelling down, below travelling up)
        again = np.where(side_now, out[2] > 0, out[2] <= 0)
        todo = todo[again]
    stay[todo] = 0.0
    d[2] = np.maximum(d[2], 1e-12)
    return d, stay, gone, second


def _simulate(a, b, bw, particles, water, sun_zenith, seed, *, photons,
              depths, half_slab, n_water, d_zenith, d_azimuth,
              depth=math.inf, albedo=None, slope_variance=None,
              surface_facets="one"):
    """One batch. ``sun_zenith`` in degrees, or None for an overcast sky of
    uniform radiance. z is positive downwards; the sun's light travels
    towards +x, so azimuth 0 is the direction away from the sun.

    Everything is per unit planar irradiance just above the surface.
    """
    rng = np.random.default_rng(seed)
    c = a + b
    if sun_zenith is None:
        mu_air = np.sqrt(rng.random(photons))     # cosine-weighted
        azimuth = np.pi * rng.random(photons)     # symmetric: fold to 0-180
    else:
        mu_air = np.full(photons, np.cos(np.radians(sun_zenith)))
        azimuth = np.zeros(photons)
    rough = slope_variance is not None
    if not rough:
        weight = 1 - _fresnel(mu_air, 1.0, n_water)
        reflected_above = float(np.sum(1 - weight))
        sin_w = np.sqrt(1 - mu_air ** 2) / n_water
        ux, uy = sin_w * np.cos(azimuth), sin_w * np.sin(azimuth)
        uz = np.sqrt(1 - sin_w ** 2)
    elif surface_facets == "all":
        s_air = np.sqrt(1 - mu_air ** 2)
        d = np.array([s_air * np.cos(azimuth), s_air * np.sin(azimuth),
                      mu_air])
        t, weight, gone, second = _follow_surface(
            d, np.ones(photons, bool), slope_variance, n_water, rng)
        reflected_above = float(np.sum(gone))
        ux, uy, uz = t[0].copy(), t[1].copy(), t[2].copy()
        again_in = float(np.sum(second))
    else:
        s_air = np.sqrt(1 - mu_air ** 2)
        d = np.array([s_air * np.cos(azimuth), s_air * np.sin(azimuth),
                      mu_air])
        normal, cos_i, w = _facets(d, slope_variance, rng)
        r, cos_t = _fresnel_cos(cos_i, 1.0, n_water)
        eta = 1.0 / n_water
        t = eta * d + (eta * cos_i - cos_t) * normal
        t /= np.linalg.norm(t, axis=0)
        weight = w * (1 - r)
        reflected_above = float(np.sum(w * r))
        ux, uy, uz = t[0].copy(), t[1].copy(), t[2].copy()
        # a refracted direction pointing up again would need a second facet
        lost = uz <= 0
        weight[lost] = 0.0
        uz[lost] = 1.0
    transmitted = float(np.sum(weight))
    ed_surface = transmitted
    z = np.zeros(photons)
    scattered = np.zeros(photons, bool)
    n_th, n_ph = int(180 / d_zenith), int(180 / d_azimuth)
    radiance = np.zeros((depths.size, n_th, n_ph))
    e0, ed, eu, e0u = (np.zeros(depths.size) for _ in range(4))
    ed_bottom = 0.0
    lu = 0.0
    arrived_below = again_below = 0.0
    bottom = math.isfinite(depth)
    # Scattering by less than the cut goes straight on and so does not turn
    # light out of the line of sight: towards the surface it attenuates by
    # c less that share (DECISIONS.md section 138).
    c_sight = c - (b - bw) * particles["straight"]

    alive = np.arange(photons)
    while alive.size:
        i = alive
        mu = uz[i]
        step = -np.log(1.0 - rng.random(i.size)) / c
        z0 = z[i]
        z1 = z0 + step * mu
        surfaced = z1 < 0
        z1 = np.where(surfaced, 0.0, z1)
        step = np.where(surfaced, z0 / np.maximum(-mu, 1e-12), step)
        if bottom:
            floored = z1 > depth
            z1 = np.where(floored, depth, z1)
            step = np.where(floored, (depth - z0) / np.maximum(mu, 1e-12),
                            step)
        else:
            floored = np.zeros(i.size, bool)
        lo, hi = np.minimum(z0, z1), np.maximum(z0, z1)
        th = np.minimum((np.degrees(np.arccos(np.clip(mu, -1, 1)))
                         / d_zenith).astype(int), n_th - 1)
        ph = np.minimum((np.abs(np.degrees(np.arctan2(uy[i], ux[i])))
                         / d_azimuth).astype(int), n_ph - 1)
        for k, zk in enumerate(depths):
            dz = np.clip(np.minimum(hi, zk + half_slab)
                         - np.maximum(lo, zk - half_slab), 0.0, None)
            path = np.minimum(np.where(np.abs(mu) > 1e-9,
                                       dz / np.maximum(np.abs(mu), 1e-9),
                                       step * (dz > 0)), step)
            e0[k] += np.sum(weight[i] * path) / (2 * half_slab)
            e0u[k] += np.sum((weight[i] * path)[mu < 0]) / (2 * half_slab)
            seen = (path > 0) & scattered[i]
            np.add.at(radiance[k], (th[seen], ph[seen]),
                      weight[i][seen] * path[seen] / (2 * half_slab))
            cross = (z0 - zk) * (z1 - zk) < 0
            ed[k] += np.sum(weight[i][cross & (mu > 0)])
            eu[k] += np.sum(weight[i][cross & (mu < 0)])
        z[i] = z1

        up = i[surfaced]
        if not rough:
            weight[up] *= _fresnel(uz[up], n_water, 1.0)
            uz[up] = -uz[up]
        elif up.size and surface_facets == "all":
            d = np.array([ux[up], uy[up], uz[up]])
            arrived_below += float(np.sum(weight[up]))
            out, stay, _, second = _follow_surface(
                d, np.zeros(up.size, bool), slope_variance, n_water, rng)
            again_below += float(np.sum(weight[up] * second))
            weight[up] *= stay
            ux[up], uy[up], uz[up] = out[0], out[1], out[2]
        elif up.size:
            d = np.array([ux[up], uy[up], uz[up]])
            normal, cos_i, w = _facets(d, slope_variance, rng)
            r, _ = _fresnel_cos(cos_i, n_water, 1.0)
            out = d + 2 * cos_i * normal
            out /= np.linalg.norm(out, axis=0)
            # reflected light still travelling up meets no second facet
            weight[up] *= np.where(out[2] > 0, w * r, 0.0)
            ux[up], uy[up], uz[up] = out[0], out[1], np.maximum(out[2], 1e-12)
        ed_surface += float(np.sum(weight[up]))

        if bottom:
            down = i[floored]
            ed_bottom += float(np.sum(weight[down]))
            lu += float(np.sum(weight[down])) * albedo / math.pi \
                * math.exp(-c_sight * depth)
            weight[down] *= albedo
            mu_b = np.sqrt(rng.random(down.size))
            phi_b = 2 * np.pi * rng.random(down.size)
            s_b = np.sqrt(1 - mu_b * mu_b)
            ux[down], uy[down], uz[down] = (s_b * np.cos(phi_b),
                                            s_b * np.sin(phi_b), -mu_b)
            scattered[down] = True

        hit = i[~surfaced & ~floored]
        weight[hit] *= b / c
        # rrs: what this scattering sends straight up, to the surface
        angle = np.arccos(np.clip(-uz[hit], -1.0, 1.0))
        p_up = (bw * _per_sr(water, angle)
                + (b - bw) * _per_sr(particles, angle)) / b
        lu += float(np.sum(weight[hit] * p_up * np.exp(-c_sight * z[hit])))
        by_water = rng.random(hit.size) < bw / b
        cos_t = np.empty(hit.size)
        cos_t[by_water] = np.interp(rng.random(by_water.sum()),
                                    water["cdf"], water["cos"])
        n_part = int((~by_water).sum())
        straight = rng.random(n_part) < particles["straight"]
        cos_t[~by_water] = np.where(
            straight, 1.0,
            np.interp(rng.random(n_part), particles["cdf"], particles["cos"]))
        ux[hit], uy[hit], uz[hit] = _turn(ux[hit], uy[hit], uz[hit], cos_t,
                                          rng)
        scattered[hit] = True

        weak = alive[weight[alive] < _WEIGHT_FLOOR]
        keep = rng.random(weak.size) < 0.1
        weight[weak[keep]] *= 10.0
        weight[weak[~keep]] = 0.0
        alive = alive[weight[alive] > 0]

    edges = np.radians(np.arange(n_th + 1) * d_zenith)
    d_omega = ((np.cos(edges[:-1]) - np.cos(edges[1:]))
               * np.radians(d_azimuth) * 2)          # both folded halves
    out = dict(radiance=radiance / photons / d_omega[None, :, None],
               e0=e0 / photons, ed=ed / photons, eu=eu / photons,
               e0u=e0u / photons, ed_bottom=ed_bottom / photons,
               rrs=lu / ed_surface, transmitted=transmitted / photons,
               reflected=reflected_above / photons)
    if rough and surface_facets == "all":
        # the share of the light that met more than one facet (section 141)
        out.update(second_facet_entering=again_in / photons,
                   second_facet_below=(again_below / arrived_below
                                       if arrived_below else 0.0))
    return out


# -- the public function -----------------------------------------------------

@_data.compared_by_value
@dataclass(frozen=True, eq=False)
class MonteCarloLightField:
    """What :func:`monte_carlo_light_field` returns.

    Everything is per unit planar irradiance just above the surface; the
    ``batch_*`` fields hold each batch, the others their means, and the
    ``*_se`` fields the standard error of the mean over the batches.
    """

    depths_m: np.ndarray
    zenith_edges_deg: np.ndarray
    azimuth_edges_deg: np.ndarray
    batch_ed: np.ndarray
    batch_eu: np.ndarray
    batch_e0: np.ndarray
    batch_radiance: np.ndarray
    batch_rrs: np.ndarray
    ed: np.ndarray
    eu: np.ndarray
    e0: np.ndarray
    radiance: np.ndarray
    kd: np.ndarray
    kd_se: np.ndarray
    mean_cosine: np.ndarray
    mean_cosine_se: np.ndarray
    eu_over_ed: np.ndarray
    eu_over_ed_se: np.ndarray
    e0_over_ed: np.ndarray
    e0_over_ed_se: np.ndarray
    rrs: float
    rrs_se: float
    reflected_at_surface: float
    reflected_at_surface_se: float
    transmitted_at_surface: float
    transmitted_at_surface_se: float
    inputs: dict
    left_out: tuple

    def as_dict(self) -> dict[str, Any]:
        """The means, their standard errors, the inputs and what was left
        out, as plain lists and numbers."""
        out: dict[str, Any] = {}
        for name in ("depths_m", "ed", "eu", "e0", "kd", "kd_se",
                     "mean_cosine", "mean_cosine_se", "eu_over_ed",
                     "eu_over_ed_se", "e0_over_ed", "e0_over_ed_se"):
            out[name] = np.asarray(getattr(self, name)).tolist()
        out.update(rrs=self.rrs, rrs_se=self.rrs_se,
                   reflected_at_surface=self.reflected_at_surface,
                   reflected_at_surface_se=self.reflected_at_surface_se,
                   transmitted_at_surface=self.transmitted_at_surface,
                   transmitted_at_surface_se=self.transmitted_at_surface_se,
                   inputs=dict(self.inputs), left_out=list(self.left_out),
                   method="Monte Carlo, DECISIONS.md sections 138 and 139")
        return out


def _number(name, value, *, low=None, high=None, low_open=False,
            high_open=False):
    if value is None:
        raise MissingQuantityError(f"{name} is required; there is no default")
    try:
        x = float(value)
    except (TypeError, ValueError):
        raise TypeError(f"{name} must be a number, not {value!r}") from None
    if not math.isfinite(x):
        raise ValueError(f"{name} must be finite, not {value!r}")
    if low is not None and (x < low or (low_open and x == low)):
        side = "above" if low_open else "at least"
        raise ValueError(f"{name} must be {side} {low:g}, not {x:g}")
    if high is not None and (x > high or (high_open and x == high)):
        side = "below" if high_open else "at most"
        raise ValueError(f"{name} must be {side} {high:g}, not {x:g}")
    return x


def _count(name, value, low):
    if value is None:
        raise MissingQuantityError(f"{name} is required; there is no default")
    if isinstance(value, (float, np.floating)) or not isinstance(
            value, (int, np.integer)):
        raise TypeError(f"{name} must be a whole number, not {value!r}")
    if value < low:
        raise ValueError(f"{name} must be at least {low}, not {value}")
    return int(value)


def _required(name, value):
    if value is None:
        raise MissingQuantityError(f"{name} is required; there is no default")
    return value


def monte_carlo_light_field(a, b, wavelength_nm, /, *,
                            pure_water_b=None, salinity_psu=None,
                            phase_function=None,
                            station_salinity_psu=None, cut_deg=None,
                            refractive_index=None, sun_zenith_deg=...,
                            depth_m=None, bottom_albedo=...,
                            depths_m=None, slab_m=None,
                            zenith_step_deg=None, azimuth_step_deg=None,
                            photons=None, batches=None, seed=None,
                            wind=..., surface_facets=...):
    """The light field in one homogeneous water by Monte Carlo
    (DECISIONS.md section 138).

    A flat surface, the sun's beam or an overcast sky above it, one layer
    of water with ``a`` and ``b``, infinitely deep or over a Lambertian
    bottom. It gives Ed, Eu and Eo and the radiance in cells of zenith and
    azimuth at ``depths_m``, Kd between them, the mean cosine, Eu / Ed and
    Eo / Ed, and rrs straight up just below the surface, each with its
    standard error over the batches. The method is in the module's
    docstring; what it leaves out is in ``left_out`` of the result. For
    more (an atmosphere, waves, layers, Raman scattering), use a radiative
    transfer code such as OSOAA or HydroLight (see
    :func:`osoaa_user_profile`).

    Every argument is required; nothing is defaulted, because each sets
    the result and none is fixed by a water type (DECISIONS.md sections 4,
    38 and 138). A missing one raises :class:`MissingQuantityError`.

    Parameters
    ----------
    a, b:
        Absorption and scattering coefficients, 1/m, at ``wavelength_nm``;
        ``b`` includes ``pure_water_b``.
    wavelength_nm:
        The wavelength they are for; it sets pure water's phase function.
    pure_water_b:
        The pure water scattering inside ``b``, 1/m, for example
        :func:`pure_water_scattering`; the rest of ``b`` is the particles'.
    salinity_psu:
        Of this water, for pure water's phase function (the shape of
        :func:`pure_water_vsf`), and stated in the result.
    phase_function:
        The particles': a :class:`ScatteringFunction` from
        :func:`petzold_scattering`, which is water and particles, whose
        vsf less :func:`pure_water_vsf` at its own wavelength is taken as
        the particles'; or a :class:`FournierForand`, the particles' alone.
    station_salinity_psu:
        For a Petzold station only: the salinity of the pure sea water
        taken out of its vsf, which is the station's water, not
        necessarily this one (a lake given a station's particles, for
        one). Refused with a Fournier-Forand.
    cut_deg:
        The particles' scattering by less than this, degrees, goes straight
        on. For a station it may not be below the first angle Petzold
        measured; below it lies the report's extension (DATA.md section
        21). At most 10.
    refractive_index:
        Of the water against air, 1 to 1.5; 1.34 for sea water in the
        visible.
    sun_zenith_deg:
        The sun's zenith angle in air, 0 to below 90, or None for an
        overcast sky of uniform radiance.
    depth_m:
        ``math.inf`` for no bottom, or the depth of a Lambertian bottom.
    bottom_albedo:
        0 to 1 with a bottom; None without one.
    depths_m:
        Where the field is reported, increasing, each slab within the
        water.
    slab_m:
        The thickness of the slab each depth's Eo and radiance are taken
        over.
    zenith_step_deg, azimuth_step_deg:
        The radiance's cells; each must divide 180. Azimuth runs from 0,
        away from the sun, to 180, the two halves folded.
    wind:
        ``"flat"``, or the wind speed in m/s at 12.5 m, for a surface of
        Cox and Munk's (1954) isotropic slopes, mean square slope 0.003 +
        5.12e-3 wind (DECISIONS.md section 139); ``surface_facets`` says
        what becomes of light that a facet sends towards the surface
        again. Since 1.34.0. Leaving it out takes the surface as flat, as
        1.33.0 did, with a FutureWarning; a later release will require it.
    surface_facets:
        With a wind: ``"one"``, each crossing of the surface meets one
        facet and light that it sends towards the surface again is taken
        as gone, as OSOAA does and as 1.34 did; or ``"all"``, such light
        meets another facet, drawn independently of the last, until it
        leaves the surface, as the Monte Carlo codes of Mobley et al.
        (1993) did (DECISIONS.md section 141). With the sun 80 degrees from
        the zenith the two differ by about 3 percent in the light that
        enters. ``None`` with ``wind="flat"``. Since 1.35.0. Leaving it out
        with a wind takes ``"one"``, as 1.34 did, with a FutureWarning; a
        later release will require it.
    photons, batches, seed:
        Photons per batch; at least 2 batches, for the standard errors;
        batch i uses the seed ``seed + i``.

    Returns
    -------
    :class:`MonteCarloLightField`.
    """
    a = _number("a", a, low=0.0)
    b = _number("b", b, low=0.0, low_open=True)
    wavelength_nm = _number("wavelength_nm", wavelength_nm, low=0.0,
                            low_open=True)
    pure_water_b = _number("pure_water_b", pure_water_b, low=0.0)
    if pure_water_b > b:
        raise ValueError(f"pure_water_b ({pure_water_b:g}) exceeds b "
                         f"({b:g}); it must be the pure water b includes")
    salinity_psu = _number("salinity_psu", salinity_psu, low=0.0, high=45.0)
    phase_function = _required("phase_function", phase_function)
    if not isinstance(phase_function, (ScatteringFunction, FournierForand)):
        raise TypeError(
            "phase_function must be a ScatteringFunction, from "
            "petzold_scattering(), or a FournierForand, not "
            f"{type(phase_function).__name__}")
    cut_deg = _number("cut_deg", cut_deg, low=0.0, low_open=True, high=10.0)
    if isinstance(phase_function, ScatteringFunction):
        if station_salinity_psu is None:
            raise MissingQuantityError(
                "a Petzold station is water and particles: "
                "station_salinity_psu, of the sea water taken out of its "
                "vsf, is required; there is no default")
        station_salinity_psu = _number("station_salinity_psu",
                                       station_salinity_psu, low=0.0,
                                       high=45.0)
        p = phase_function
        first = float(np.asarray(p.angles_deg)[
            [s == "ok" for s in p.statuses]][0])
        if cut_deg < first:
            raise ValueError(
                f"cut_deg ({cut_deg:g}) is below {first:g} degree, the "
                f"first angle measured at {p.station}; below it lies the "
                "report's extension")
    elif station_salinity_psu is not None:
        raise ValueError("station_salinity_psu is for a Petzold station; a "
                         "Fournier-Forand is the particles' alone")
    refractive_index = _number("refractive_index", refractive_index,
                               low=1.0, high=1.5)
    if sun_zenith_deg is ...:
        raise MissingQuantityError(
            "sun_zenith_deg is required (None for an overcast sky); there "
            "is no default")
    if sun_zenith_deg is not None:
        sun_zenith_deg = _number("sun_zenith_deg", sun_zenith_deg, low=0.0,
                                 high=90.0, high_open=True)
    if depth_m is None:
        raise MissingQuantityError(
            "depth_m is required (math.inf for no bottom); there is no "
            "default")
    depth_m = float(depth_m)
    if math.isnan(depth_m) or depth_m <= 0:
        raise ValueError(f"depth_m must be above 0, not {depth_m:g}")
    if bottom_albedo is ...:
        raise MissingQuantityError(
            "bottom_albedo is required (None with no bottom); there is no "
            "default")
    if math.isinf(depth_m):
        if bottom_albedo is not None:
            raise ValueError("bottom_albedo is for a bottom; with depth_m "
                             "infinite it must be None")
    else:
        if bottom_albedo is None:
            raise MissingQuantityError(
                "a bottom needs bottom_albedo, 0 to 1; there is no default")
        bottom_albedo = _number("bottom_albedo", bottom_albedo, low=0.0,
                                high=1.0)
    if depths_m is None:
        raise MissingQuantityError("depths_m is required; there is no "
                                   "default")
    depths = np.array(depths_m, dtype=float).ravel()
    slab_m = _number("slab_m", slab_m, low=0.0, low_open=True)
    if depths.size == 0 or not np.all(np.isfinite(depths)):
        raise ValueError("depths_m must be finite numbers, at least one")
    if np.any(np.diff(depths) <= 0):
        raise ValueError("depths_m must increase")
    if depths[0] - slab_m / 2 < 0 or depths[-1] + slab_m / 2 > depth_m:
        raise ValueError("every depth's slab must lie within the water")
    steps = []
    for name, value in (("zenith_step_deg", zenith_step_deg),
                        ("azimuth_step_deg", azimuth_step_deg)):
        x = _number(name, value, low=0.0, low_open=True, high=180.0)
        if abs(180.0 / x - round(180.0 / x)) > 1e-9:
            raise ValueError(f"{name} must divide 180, not {x:g}")
        steps.append(x)
    photons = _count("photons", photons, 1)
    batches = _count("batches", batches, 2)
    seed = _count("seed", seed, 0)
    if wind is ...:
        warnings.warn(
            "monte_carlo_light_field: wind was left out and the surface is "
            "taken as flat, as 1.33.0 did; pass wind='flat' or the wind "
            "speed in m/s at 12.5 m. A later release will require it "
            "(DECISIONS.md section 139).", FutureWarning,
            stacklevel=_data.caller_stacklevel())
        wind = "flat"
    if isinstance(wind, str):
        if wind != "flat":
            raise ValueError(f"wind must be 'flat' or a speed in m/s, not "
                             f"{wind!r}")
        slope_variance = None
    else:
        wind = _number("wind", wind, low=0.0)
        slope_variance = (COX_MUNK_MEAN_SQUARE_SLOPE[0]
                          + COX_MUNK_MEAN_SQUARE_SLOPE[1] * wind)
    if slope_variance is None:
        if surface_facets is ...:
            surface_facets = None
        elif surface_facets is not None:
            raise ValueError("surface_facets is for a wavy surface; with "
                             "wind='flat' it must be None")
    else:
        if surface_facets is ...:
            warnings.warn(
                "monte_carlo_light_field: surface_facets was left out and "
                "each crossing of the wavy surface meets one facet, as 1.34 "
                "did; pass surface_facets='one' or 'all'. A later release "
                "will require it (DECISIONS.md section 141).", FutureWarning,
                stacklevel=_data.caller_stacklevel())
            surface_facets = "one"
        if surface_facets not in ("one", "all"):
            raise ValueError("with a wind, surface_facets must be 'one' or "
                             f"'all', not {surface_facets!r}")

    particles = _particle_phase(phase_function, cut_deg,
                                station_salinity_psu)
    water = _water_phase(wavelength_nm, salinity_psu)
    runs = [_simulate(a, b, pure_water_b, particles, water, sun_zenith_deg,
                      seed + k, photons=photons, depths=depths,
                      half_slab=slab_m / 2, n_water=refractive_index,
                      d_zenith=steps[0], d_azimuth=steps[1], depth=depth_m,
                      albedo=bottom_albedo, slope_variance=slope_variance,
                      surface_facets=surface_facets or "one")
            for k in range(batches)]

    def frozen(x):
        return _data._frozen(np.asarray(x, dtype=float))

    def mean_se(values):
        v = np.asarray(values, dtype=float)
        return (v.mean(axis=0),
                v.std(axis=0, ddof=1) / math.sqrt(len(values)))

    batch = {k: np.array([r[k] for r in runs])
             for k in ("ed", "eu", "e0", "radiance", "rrs")}
    with np.errstate(divide="ignore", invalid="ignore"):
        kd, kd_se = mean_se([np.log(r["ed"][:-1] / r["ed"][1:])
                             / np.diff(depths) for r in runs])
        mu, mu_se = mean_se([(r["ed"] - r["eu"]) / r["e0"] for r in runs])
        ratio_u, ratio_u_se = mean_se([r["eu"] / r["ed"] for r in runs])
        ratio_0, ratio_0_se = mean_se([r["e0"] / r["ed"] for r in runs])
    rrs, rrs_se = mean_se(batch["rrs"])
    reflected, reflected_se = mean_se([r["reflected"] for r in runs])
    transmitted, transmitted_se = mean_se([r["transmitted"] for r in runs])
    name = (phase_function.station
            if isinstance(phase_function, ScatteringFunction)
            else f"Fournier-Forand, n = {phase_function.refractive_index:g},"
                 f" mu = {phase_function.junge_slope:g}")
    inputs = dict(a=a, b=b, wavelength_nm=wavelength_nm,
                  pure_water_b=pure_water_b, salinity_psu=salinity_psu,
                  phase_function=name,
                  station_salinity_psu=station_salinity_psu, cut_deg=cut_deg,
                  straight_share=float(particles["straight"]),
                  refractive_index=refractive_index,
                  sun_zenith_deg=sun_zenith_deg, depth_m=depth_m,
                  bottom_albedo=bottom_albedo, slab_m=slab_m,
                  zenith_step_deg=steps[0], azimuth_step_deg=steps[1],
                  photons=photons, batches=batches, seed=seed, wind=wind,
                  surface_facets=surface_facets)
    waves = (_LEFT_OUT_ALL_FACETS if surface_facets == "all"
             else _LEFT_OUT_WAVES)
    left_out = (LEFT_OUT if slope_variance is None
                else LEFT_OUT[:1] + (waves,) + LEFT_OUT[2:])
    return MonteCarloLightField(
        depths_m=frozen(depths),
        zenith_edges_deg=frozen(np.arange(0.0, 180.0 + steps[0] / 2,
                                          steps[0])),
        azimuth_edges_deg=frozen(np.arange(0.0, 180.0 + steps[1] / 2,
                                           steps[1])),
        batch_ed=frozen(batch["ed"]), batch_eu=frozen(batch["eu"]),
        batch_e0=frozen(batch["e0"]),
        batch_radiance=frozen(batch["radiance"]),
        batch_rrs=frozen(batch["rrs"]),
        ed=frozen(batch["ed"].mean(axis=0)),
        eu=frozen(batch["eu"].mean(axis=0)),
        e0=frozen(batch["e0"].mean(axis=0)),
        radiance=frozen(batch["radiance"].mean(axis=0)),
        kd=frozen(kd), kd_se=frozen(kd_se), mean_cosine=frozen(mu),
        mean_cosine_se=frozen(mu_se), eu_over_ed=frozen(ratio_u),
        eu_over_ed_se=frozen(ratio_u_se), e0_over_ed=frozen(ratio_0),
        e0_over_ed_se=frozen(ratio_0_se), rrs=float(rrs),
        rrs_se=float(rrs_se), reflected_at_surface=float(reflected),
        reflected_at_surface_se=float(reflected_se),
        transmitted_at_surface=float(transmitted),
        transmitted_at_surface_se=float(transmitted_se), inputs=inputs,
        left_out=left_out)

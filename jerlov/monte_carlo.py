"""A light field under water by Monte Carlo. DECISIONS.md sections 38 to
40 and 138.

Photons enter through a flat surface, refracted and thinned by Fresnel
transmission. Each travels a free path drawn from exp(-c s), and at its
end is scattered, never absorbed: instead its weight is multiplied by
b / c. Scattering is by pure water or by particles in proportion to their
share of b, at an angle drawn from that one's phase function and an
azimuth drawn uniformly. Light reaching the surface from below is
reflected back by the Fresnel reflectance and the rest leaves; light
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
example's numbers bit for bit.

Every choice that sets the result is a required argument; nothing is
defaulted (DECISIONS.md section 138, which amends section 12). Left out:
an atmosphere, waves, polarisation, inelastic scattering (Raman,
fluorescence) and water that varies with depth.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from . import _data
from .fournier_forand import FournierForand
from .petzold import ScatteringFunction
from .backscattering import pure_water_scattering, pure_water_vsf
from .water import MissingQuantityError

#: What the method does not include, said in every result.
LEFT_OUT = (
    "an atmosphere: the sun's beam or a sky of uniform radiance is given "
    "just above the surface",
    "waves: the surface is flat",
    "polarisation: the scalar equation",
    "inelastic scattering: no Raman scattering, no fluorescence",
    "water that varies with depth: one homogeneous layer",
)

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


def _simulate(a, b, bw, particles, water, sun_zenith, seed, *, photons,
              depths, half_slab, n_water, d_zenith, d_azimuth,
              depth=math.inf, albedo=None):
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
    weight = 1 - _fresnel(mu_air, 1.0, n_water)
    ed_surface = float(np.sum(weight))
    sin_w = np.sqrt(1 - mu_air ** 2) / n_water
    ux, uy = sin_w * np.cos(azimuth), sin_w * np.sin(azimuth)
    uz = np.sqrt(1 - sin_w ** 2)
    z = np.zeros(photons)
    scattered = np.zeros(photons, bool)
    n_th, n_ph = int(180 / d_zenith), int(180 / d_azimuth)
    radiance = np.zeros((depths.size, n_th, n_ph))
    e0, ed, eu = (np.zeros(depths.size) for _ in range(3))
    lu = 0.0
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
            seen = (path > 0) & scattered[i]
            np.add.at(radiance[k], (th[seen], ph[seen]),
                      weight[i][seen] * path[seen] / (2 * half_slab))
            cross = (z0 - zk) * (z1 - zk) < 0
            ed[k] += np.sum(weight[i][cross & (mu > 0)])
            eu[k] += np.sum(weight[i][cross & (mu < 0)])
        z[i] = z1

        up = i[surfaced]
        weight[up] *= _fresnel(uz[up], n_water, 1.0)
        uz[up] = -uz[up]
        ed_surface += float(np.sum(weight[up]))

        if bottom:
            down = i[floored]
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
    return dict(radiance=radiance / photons / d_omega[None, :, None],
                e0=e0 / photons, ed=ed / photons, eu=eu / photons,
                rrs=lu / ed_surface)


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
                   inputs=dict(self.inputs), left_out=list(self.left_out),
                   method="Monte Carlo, DECISIONS.md section 138")
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


def monte_carlo_light_field(a, b, /, *, wavelength_nm=None,
                            pure_water_b=None, salinity_psu=None,
                            phase_function=None,
                            station_salinity_psu=None, cut_deg=None,
                            refractive_index=None, sun_zenith_deg=...,
                            depth_m=None, bottom_albedo=...,
                            depths_m=None, slab_m=None,
                            zenith_step_deg=None, azimuth_step_deg=None,
                            photons=None, batches=None, seed=None):
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
        For pure water's phase function.
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

    particles = _particle_phase(phase_function, cut_deg,
                                station_salinity_psu)
    water = _water_phase(wavelength_nm, salinity_psu)
    runs = [_simulate(a, b, pure_water_b, particles, water, sun_zenith_deg,
                      seed + k, photons=photons, depths=depths,
                      half_slab=slab_m / 2, n_water=refractive_index,
                      d_zenith=steps[0], d_azimuth=steps[1], depth=depth_m,
                      albedo=bottom_albedo)
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
                  photons=photons, batches=batches, seed=seed)
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
        rrs_se=float(rrs_se), inputs=inputs, left_out=LEFT_OUT)

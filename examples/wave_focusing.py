"""Light under waves: how much it flickers, against what was measured.

For anyone working with the light just below a sunlit sea: the surface
waves gather the sunbeam into bright lines that move over everything
below, and how strongly the light at one point flickers falls with depth.
The package carries what Darecki et al. (2011) measured of it (section 42
of DECISIONS.md) and no model, since waves are not set by the water type.
This example builds one from published parts and checks it against that
measurement, with its choices fixed beforehand (sections 44, 45 and 48).

    python examples/wave_focusing.py               # about ten minutes
    python examples/wave_focusing.py --png shafts.png     # and a picture

With --png it also draws the light shafts seen looking up towards the sun
from 6 m, beside the same under a flat surface (section 46).

The method. A sea surface is drawn at random from the wave spectrum of
Elfouhaily et al. (1997), for a wind of 4.1, 5.5 or 6.4 m/s, on a square 4
m across with a point every millimetre. Each point refracts the sunbeam,
and the ray goes straight down to a depth, where the rays are counted on
a horizontal grid of the same spacing. The sun's disc and a 2.5 mm
collector blur that pattern. The coefficient of variation is the standard
deviation of the irradiance over the grid divided by its mean.

The scattered sunlight is treated two ways. As section 44 fixed it, it is
spread evenly, with its size from the Monte Carlo of
`radiance_distribution.py` under a flat surface, copied here so that the
script stands alone; that model falls short of the measurement. As
section 45 found, a photon scattered on its way down carries the same
pattern, shifted by how far the scattering moved it, and a second Monte
Carlo, with the same scattering, gives those shifts.

The sky, as section 48 fixed it: its share of the light above the sea
from the clear-sky model of Gregg and Carder (1990), for a range of
atmospheres since Darecki did not record one, and its light under the
waves taken as uniform, from the same Monte Carlo under a uniform
overcast. It is added to the second model as more light that does not
flicker.
"""

import contextlib
import io
import os
import struct
import sys
import zlib
from concurrent.futures import ThreadPoolExecutor

import numpy as np

import jerlov


def rule(title):
    print(f"\n{title}\n" + "-" * len(title))


def _banner():
    """Say which copy of the package is being used.

    Running ``python examples/foo.py`` puts ``examples/`` on sys.path, not the
    current directory, so an installed copy wins over the working tree. That
    is easy to miss and gives confusing failures; ``pip install -e .`` in the
    repository is the usual fix.
    """
    print(f"jerlov {jerlov.__version__} from {jerlov.__file__}")


N_WATER = 1.34              # sea water against air, in the visible
SALINITY_PSU = 37.0         # for pure water's scattering; not the type's
D_ZENITH, D_AZIMUTH = 10.0, 45.0
PHOTONS, BATCHES = 50_000, 4
G = 9.81                    # m s-2
SUN_ZENITH = 30.0           # degrees, in air (Darecki 30-33, You et al. 30)
SUN_DIAMETER = 0.53         # degrees
COLLECTOR = 2.5e-3          # m, the diameter of Darecki's irradiance sensors
SIDE, POINTS = 4.0, 4096    # the square of sea surface, m, and points a side
REALIZATIONS = 3
WINDS = (4.1, 5.5, 6.4)     # U10, m/s: Darecki's range and You et al.'s 5.5
WIND = 5.5                  # the one the third check is made at
DEPTHS = np.array([0.86, 1.70, 2.84, 3.78, 6.73, 9.58])   # Darecki's
CHECKED_TO = 2.84           # m, the deepest depth with a pass mark

#: You et al. (2010), Table 1, p. 1046, Santa Barbara Channel, 11 September
#: 2008: for pure sea water and for the rest, c (per m) and the single
#: scattering albedo, at 443, 532 and 670 nm.
YOU2010_TABLE1 = {
    443: (0.0113, 0.3944, 0.7853, 0.8476),
    532: (0.0460, 0.0457, 0.6522, 0.9314),
    670: (0.4398, 0.0018, 0.4867, 0.9184),
}

#: Elfouhaily et al. (1997): the fully developed sea (p. 15783), the
#: gravity-capillary peak (p. 15786) and its phase speed (p. 15789).
OMEGA_C = 0.84
K_M, C_M = 370.0, 0.23

#: Wu (1982), p. 9704: von Karman's constant and Charnock's.
KAPPA, CHARNOCK = 0.4, 0.0185

#: Cox and Munk (1954), equation (42), p. 221, clean surface, converted
#: from cm/s: mean square slope = 0.003 + 5.12e-3 W, +-0.004, with W the
#: wind in m/s at 41 ft (p. 199).
COX_MUNK = (0.003, 5.12e-3, 0.004)
COX_MUNK_HEIGHT = 12.5      # m

#: Gregg and Carder (1990): the Navy aerosol's mode radii, um, and its
#: factor R (p. 1664), and the standard pressure, hPa.
NAVY_RADII = (0.03, 0.24, 2.0)
NAVY_R = 0.05
STANDARD_PRESSURE = 1013.25
#: Section 48: the atmospheres the sky is bracketed with, as (aerosol
#: optical thickness at 550 nm, air-mass type); 80 percent relative
#: humidity and You et al.'s 5.5 m/s for both of the paper's winds.
ATMOSPHERES = [(tau, am) for tau in (0.05, 0.1, 0.2, 0.4) for am in (1, 10)]
SKY_HUMIDITY, SKY_WIND = 80.0, 5.5
#: Gernez and Antoine (2009), p. 4, and the share of diffuse light they
#: print along the top of Figure 10a: section 48's check.
GERNEZ_SKY = dict(tau550=0.2, air_mass_type=1, humidity=80.0,
                  wind_mean=5.0, wind=5.0)


# -- the Monte Carlo, as in radiance_distribution.py ---------------------------
# The six functions below are copied unchanged from that example; a test
# checks that the copies stay the same.

def inverse_cdf(angles_deg, vsf):
    """Cumulative probability against cos(angle), to draw angles from."""
    th = np.radians(angles_deg)
    f = vsf * 2 * np.pi * np.sin(th)
    cdf = np.concatenate([[0.0], np.cumsum(0.5 * (f[1:] + f[:-1])
                                           * np.diff(th))])
    return cdf / cdf[-1], np.cos(th), cdf[-1]


def particle_phase(station):
    """The particles' phase function at one of Petzold's stations.

    Petzold's vsf minus pure water's, from the first angle he measured;
    below it the report extended the curve, and that share of the
    particles' scattering is taken to go straight on.
    """
    p = jerlov.petzold_scattering(station)
    first = p.angles_deg[[s == "ok" for s in p.statuses]][0]
    grid = np.geomspace(first, 180.0, 3000)
    grid[-1] = 180.0
    particles = p.vsf_at(grid) - jerlov.pure_water_vsf(
        grid, p.wavelength_nm, salinity_psu=SALINITY_PSU)
    if np.any(particles <= 0):
        raise ValueError(f"{station}: pure water exceeds the measurement")
    cdf, cos_angle, measured = inverse_cdf(grid, particles)
    b_particles = p.b - float(jerlov.pure_water_scattering(
        p.wavelength_nm, salinity_psu=SALINITY_PSU))
    return dict(cdf=cdf, cos=cos_angle, straight=1 - measured / b_particles,
                first_deg=float(first), b=p.b)


def water_phase(wavelength, salinity=SALINITY_PSU):
    grid = np.linspace(0.0, 180.0, 1801)
    cdf, cos_angle, _ = inverse_cdf(
        grid, jerlov.pure_water_vsf(grid, wavelength, salinity_psu=salinity))
    return dict(cdf=cdf, cos=cos_angle)


def fresnel(mu, n1, n2):
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


def turn(ux, uy, uz, cos_t, rng):
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


def simulate(a, b, bw, particles, water, sun_zenith, seed,
             photons=PHOTONS, depths=DEPTHS, half_slab=0.5,
             n_water=N_WATER):
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
    weight = 1 - fresnel(mu_air, 1.0, n_water)
    sin_w = np.sqrt(1 - mu_air ** 2) / n_water
    ux, uy = sin_w * np.cos(azimuth), sin_w * np.sin(azimuth)
    uz = np.sqrt(1 - sin_w ** 2)
    z = np.zeros(photons)
    scattered = np.zeros(photons, bool)
    n_th, n_ph = int(180 / D_ZENITH), int(180 / D_AZIMUTH)
    radiance = np.zeros((depths.size, n_th, n_ph))
    e0, ed, eu = (np.zeros(depths.size) for _ in range(3))

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
        lo, hi = np.minimum(z0, z1), np.maximum(z0, z1)
        th = np.minimum((np.degrees(np.arccos(np.clip(mu, -1, 1)))
                         / D_ZENITH).astype(int), n_th - 1)
        ph = np.minimum((np.abs(np.degrees(np.arctan2(uy[i], ux[i])))
                         / D_AZIMUTH).astype(int), n_ph - 1)
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
        weight[up] *= fresnel(uz[up], n_water, 1.0)
        uz[up] = -uz[up]

        hit = i[~surfaced]
        weight[hit] *= b / c
        by_water = rng.random(hit.size) < bw / b
        cos_t = np.empty(hit.size)
        cos_t[by_water] = np.interp(rng.random(by_water.sum()),
                                    water["cdf"], water["cos"])
        n_part = int((~by_water).sum())
        straight = rng.random(n_part) < particles["straight"]
        cos_t[~by_water] = np.where(
            straight, 1.0,
            np.interp(rng.random(n_part), particles["cdf"], particles["cos"]))
        ux[hit], uy[hit], uz[hit] = turn(ux[hit], uy[hit], uz[hit], cos_t, rng)
        scattered[hit] = True

        weak = alive[weight[alive] < 1e-4]
        keep = rng.random(weak.size) < 0.1
        weight[weak[keep]] *= 10.0
        weight[weak[~keep]] = 0.0
        alive = alive[weight[alive] > 0]

    edges = np.radians(np.arange(n_th + 1) * D_ZENITH)
    d_omega = ((np.cos(edges[:-1]) - np.cos(edges[1:]))
               * np.radians(D_AZIMUTH) * 2)          # both folded halves
    return dict(radiance=radiance / photons / d_omega[None, :, None],
                e0=e0 / photons, ed=ed / photons, eu=eu / photons)


# -- the sea surface: Elfouhaily et al. (1997) --------------------------------

def friction_velocity(u10):
    """Wu (1982), equation (1): C10 = (0.8 + 0.065 U10) x 1e-3, and
    u* = sqrt(C10) U10."""
    return np.sqrt((0.8 + 0.065 * u10) * 1e-3) * u10


def wind_at(height, u10):
    """The wind at another height, by the logarithmic profile with Charnock's
    roughness length (Wu 1982, p. 9704)."""
    z0 = CHARNOCK * friction_velocity(u10) ** 2 / G
    return u10 * np.log(height / z0) / np.log(10.0 / z0)


def phase_speed(k):
    """Elfouhaily's dispersion relation, equation (24)."""
    return np.sqrt(G / k * (1 + (k / K_M) ** 2))


def spectrum(k, u10):
    """The omnidirectional spectrum S(k) = k^-3 (B_l + B_h), equation (30),
    and the spreading ratio Delta(k), equation (57), for a fully developed
    sea."""
    omega = OMEGA_C                       # Omega_c = Omega cos(0)
    k_p = G / u10 ** 2 * OMEGA_C ** 2     # equation (3)
    c_p, c = phase_speed(k_p), phase_speed(k)
    u_star = friction_velocity(u10)
    # long waves, equations (31), (32), (2), (3) and (34); gamma = 1.7 for
    # Omega_c between 0.84 and 1
    alpha_p = 6e-3 * np.sqrt(omega)
    sigma = 0.08 * (1 + 4 * OMEGA_C ** -3)
    peak = np.exp(-(np.sqrt(k / k_p) - 1) ** 2 / (2 * sigma ** 2))
    f_p = (np.exp(-1.25 * (k_p / k) ** 2) * 1.7 ** peak
           * np.exp(-omega / np.sqrt(10) * (np.sqrt(k / k_p) - 1)))
    b_l = 0.5 * alpha_p * c_p / c * f_p
    # short waves, equations (40), (41) and (44)
    ratio = u_star / C_M
    alpha_m = 1e-2 * (1 + np.log(ratio) if ratio < 1
                      else 1 + 3 * np.log(ratio))
    f_m = np.exp(-0.25 * (k / K_M - 1) ** 2)
    b_h = 0.5 * alpha_m * C_M / c * f_m
    # the spreading, equations (57) and (59)
    a_m = 0.13 * u_star / C_M
    delta = np.tanh(np.log(2) / 4 + 4 * (c / c_p) ** 2.5
                    + a_m * (C_M / c) ** 2.5)
    return (b_l + b_h) / k ** 3, delta


def slope_variance(u10, k_low, k_high, points=200_000):
    """The integral of k^2 S(k) between two wavenumbers: the mean square
    slope the waves between them carry."""
    k = np.geomspace(k_low, k_high, points)
    f = k * k * spectrum(k, u10)[0]
    return float(np.sum(0.5 * (f[1:] + f[:-1]) * np.diff(k)))


def wavenumbers(side=SIDE, points=POINTS):
    k = 2 * np.pi * np.fft.fftfreq(points, side / points)
    return np.meshgrid(k, k, indexing="xy")


def amplitudes(u10, side=SIDE, points=POINTS):
    """sqrt(Psi(k) dk^2) on the grid, Psi from equation (67) with the wind
    along +x; the mean is left out."""
    kx, ky = wavenumbers(side, points)
    k = np.hypot(kx, ky)
    k[0, 0] = 1.0
    s, delta = spectrum(k, u10)
    psi = s / k / (2 * np.pi) * (1 + delta * np.cos(2 * np.arctan2(ky, kx)))
    psi[0, 0] = 0.0
    return np.sqrt(psi) * (2 * np.pi / side)


def surface(amp, seed, side=SIDE):
    """Heights and slopes of one random linear sea, periodic on the square.

    Each wavenumber gets a complex Gaussian amplitude; the field is the
    real part, which is the inverse transform of the Hermitian part. Its
    variance is the sum of Psi dk^2 over the grid.
    """
    n = amp.shape[0]
    rng = np.random.default_rng(seed)
    a = amp * (rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n)))
    flipped = np.roll(a[::-1, ::-1], 1, axis=(0, 1))     # a at -k
    h = (0.5 * n * n) * (a + np.conj(flipped))[:, : n // 2 + 1]
    del a, flipped
    kx, ky = (k[:, : n // 2 + 1] for k in wavenumbers(side, n))
    return (np.fft.irfft2(h, s=(n, n)),
            np.fft.irfft2(1j * kx * h, s=(n, n)),
            np.fft.irfft2(1j * ky * h, s=(n, n)))


# -- the light ------------------------------------------------------------------

def unscattered(c, depth, sun_zenith=SUN_ZENITH):
    """The sunlight that reaches a depth unscattered under a flat surface,
    per unit planar irradiance above it."""
    mu = np.cos(np.radians(sun_zenith))
    mu_w = np.sqrt(1 - (1 - mu * mu) / N_WATER ** 2)
    return (1 - fresnel(np.array([mu]), 1.0, N_WATER)[0]) \
        * np.exp(-c * depth / mu_w)


def rays(eta, sx, sy, sun_zenith=SUN_ZENITH):
    """Refract the sunbeam at every point of the surface.

    The sunlight travels towards +x and down. A point whose surface has the
    upward normal N = (-sx, -sy, 1) intercepts (-s.N) / cos(zenith) of the
    planar irradiance per unit of horizontal area, and passes the Fresnel
    transmittance of it. Returns the direction in the water (z up) and the
    power, per unit planar irradiance above the surface and unit area.
    """
    t = np.radians(sun_zenith)
    s_x, s_z = np.sin(t), -np.cos(t)
    norm = np.sqrt(1 + sx * sx + sy * sy)
    cos_i = (s_x * sx - s_z) / norm
    lit = cos_i > 0
    cos_i = np.where(lit, cos_i, 0.0)
    r = 1 / N_WATER
    f = r * cos_i - np.sqrt(1 - r * r * (1 - cos_i * cos_i))
    tx = r * s_x - f * sx / norm
    ty = -f * sy / norm
    tz = r * s_z + f / norm
    power = np.where(lit, cos_i * norm / np.cos(t), 0.0) \
        * (1 - fresnel(cos_i, 1.0, N_WATER))
    return tx, ty, tz, power




def _band(eta, beams, depth, cs, step, top, rows):
    """The rays from one band of rows, counted over the rows they reach:
    the first of those rows, and an image for each c."""
    tx, ty, tz, power = (v[top:top + rows] for v in beams)
    n = eta.shape[1]
    columns = np.arange(n)
    travel = (depth + eta[top:top + rows]) / -tz      # along the ray
    px = columns[None, :] + travel * tx / step
    py = columns[top:top + rows, None] + travel * ty / step
    i0, j0 = np.floor(px), np.floor(py)
    fx, fy = px - i0, py - j0
    i0 = i0.astype(np.int64) % n
    j0 = j0.astype(np.int64)
    low = int(j0.min())
    j0 -= low
    height = int(j0.max()) + 2
    i1 = i0 + 1
    i1[i1 == n] = 0
    index = np.concatenate([(j0 * n + i0).ravel(), (j0 * n + i1).ravel(),
                            ((j0 + 1) * n + i0).ravel(),
                            ((j0 + 1) * n + i1).ravel()])
    share = np.concatenate([((1 - fx) * (1 - fy)).ravel(),
                            (fx * (1 - fy)).ravel(),
                            ((1 - fx) * fy).ravel(), (fx * fy).ravel()])
    return low, [np.bincount(index, np.tile((power * np.exp(-c * travel))
                                            .ravel(), 4) * share,
                             height * n).reshape(height, n) for c in cs]


def patterns(eta, beams, depth, cs, side=SIDE):
    """The unscattered irradiance on a horizontal grid at one depth, for
    each beam attenuation in ``cs``; each ray is shared among the four
    nearest grid points. A band of rows at a time, on as many threads as
    there are processors; the bands are added in order, so the sums do
    not depend on which thread finishes first."""
    n = eta.shape[0]
    # a band about as tall as its rays spread across the sun's plane
    reach = (depth + eta.max()) * np.max(np.abs(beams[1] / beams[2])) * n / side
    rows = max(128, int(reach))
    images = [np.zeros((n, n)) for _ in cs]
    with ThreadPoolExecutor(os.cpu_count()) as pool:
        bands = pool.map(lambda top: _band(eta, beams, depth, cs, side / n,
                                           top, rows), range(0, n, rows))
        for low, locals_ in bands:
            for image, local in zip(images, locals_):
                for first in range(0, len(local), n):   # rows wrap round
                    part = local[first:first + n]
                    image[(low + first + np.arange(len(part))) % n] += part
    return images


def moments(transform):
    """The mean and the mean square of a real field on an even square grid,
    from its rfft2, by Parseval's theorem."""
    n = transform.shape[0]
    power = transform.real ** 2 + transform.imag ** 2
    total = 2 * power.sum() - power[:, 0].sum() - power[:, -1].sum()
    return transform[0, 0].real / n ** 2, total / n ** 4


def blur(depth, side=SIDE, points=POINTS, sub=4):
    """The sun's disc and the collector together, as the transform of one
    kernel on the grid. To first order a small turn of the sun moves the
    whole pattern; over the disc it moves it across an ellipse, wider along
    the sun's plane."""
    step = side / points
    alpha = np.radians(SUN_DIAMETER / 2)
    t = np.radians(SUN_ZENITH)
    cos_w = np.sqrt(1 - (np.sin(t) / N_WATER) ** 2)
    rx = depth * alpha * np.cos(t) / (N_WATER * cos_w ** 3)
    ry = depth * alpha / (N_WATER * cos_w)

    def shape(inside, reach):
        half = int(np.ceil(reach / step)) + 1
        fine = (np.arange(-half * sub, (half + 1) * sub) + 0.5) / sub - 0.5
        x, y = np.meshgrid(fine * step, fine * step, indexing="xy")
        cells = inside(x, y).reshape(2 * half + 1, sub, 2 * half + 1, sub)
        k = np.zeros((points, points))
        idx = np.arange(-half, half + 1) % points
        k[np.ix_(idx, idx)] = cells.mean(axis=(1, 3))
        if not k.any():                   # smaller than the samples in a cell
            k[0, 0] = 1.0
        return np.fft.rfft2(k / k.sum())

    sun = shape(lambda x, y: (x / rx) ** 2 + (y / ry) ** 2 <= 1, max(rx, ry))
    disc = shape(lambda x, y: x * x + y * y <= (COLLECTOR / 2) ** 2,
                 COLLECTOR / 2)
    return sun * disc


def water_at(wl):
    """a, b and pure water's b at one of You et al.'s wavelengths."""
    c_w, w_w, c_p, w_p = YOU2010_TABLE1[wl]
    b_w, b = c_w * w_w, c_w * w_w + c_p * w_p
    return c_w + c_p - b, b, b_w


def background(station, sun_zenith=SUN_ZENITH):
    """Section 44: Ed under a flat surface from the Monte Carlo, less the
    sunlight that arrives unscattered, taken as uniform. Per unit planar
    irradiance above the surface, at each wavelength and depth."""
    particles = particle_phase(station)
    out = []
    for wl in YOU2010_TABLE1:
        a, b, b_w = water_at(wl)
        ed = np.mean([simulate(a, b, b_w, particles, water_phase(wl),
                               sun_zenith, seed, depths=DEPTHS)["ed"]
                      for seed in range(BATCHES)], axis=0)
        out.append(ed - unscattered(a + b, DEPTHS))
    return np.array(out)


def shifts(a, b, bw, particles, water, seed, photons=PHOTONS, depths=DEPTHS,
           sun_zenith=SUN_ZENITH, n_water=N_WATER):
    """Section 45: where the scattered sunlight crosses each depth going
    down, measured sideways from the line the unscattered light follows.

    The same scattering as ``simulate``. A photon that has met the surface
    from below is counted apart, as light to spread evenly. Per unit
    planar irradiance above a flat surface: for each depth the shifts in x
    and y and the weights of the scattered photons, and the weight of those
    that met the surface.
    """
    rng = np.random.default_rng(seed)
    c = a + b
    mu_air = np.cos(np.radians(sun_zenith))
    weight = np.full(photons, 1 - fresnel(np.array([mu_air]), 1.0,
                                          n_water)[0])
    sin_w = np.sqrt(1 - mu_air ** 2) / n_water
    tan_w = sin_w / np.sqrt(1 - sin_w ** 2)
    ux, uy = np.full(photons, sin_w), np.zeros(photons)
    uz = np.full(photons, np.sqrt(1 - sin_w ** 2))
    x, y, z = (np.zeros(photons) for _ in range(3))
    scattered = np.zeros(photons, bool)
    met = np.zeros(photons, bool)
    found = [[] for _ in depths]
    even = np.zeros(depths.size)

    alive = np.arange(photons)
    while alive.size:
        i = alive
        step = -np.log(1.0 - rng.random(i.size)) / c
        x0, y0, z0 = x[i], y[i], z[i]
        z1 = z0 + step * uz[i]
        surfaced = z1 < 0
        step = np.where(surfaced, z0 / np.maximum(-uz[i], 1e-12), step)
        x1, y1 = x0 + step * ux[i], y0 + step * uy[i]
        z1 = np.where(surfaced, 0.0, z1)
        for k, zk in enumerate(depths):
            down = (z0 < zk) & (z1 >= zk) & scattered[i]
            if not down.any():
                continue
            g = (zk - z0[down]) / (z1[down] - z0[down])
            w = weight[i][down]
            m = met[i][down]
            even[k] += w[m].sum()
            keep = ~m
            found[k].append((x0[down][keep] + g[keep] * (x1 - x0)[down][keep]
                             - zk * tan_w,
                             y0[down][keep] + g[keep] * (y1 - y0)[down][keep],
                             w[keep]))
        x[i], y[i], z[i] = x1, y1, z1

        up = i[surfaced]
        weight[up] *= fresnel(uz[up], n_water, 1.0)
        uz[up] = -uz[up]
        met[up] = True

        hit = i[~surfaced]
        weight[hit] *= b / c
        by_water = rng.random(hit.size) < bw / b
        cos_t = np.empty(hit.size)
        cos_t[by_water] = np.interp(rng.random(by_water.sum()),
                                    water["cdf"], water["cos"])
        n_part = int((~by_water).sum())
        straight = rng.random(n_part) < particles["straight"]
        cos_t[~by_water] = np.where(
            straight, 1.0,
            np.interp(rng.random(n_part), particles["cdf"], particles["cos"]))
        ux[hit], uy[hit], uz[hit] = turn(ux[hit], uy[hit], uz[hit], cos_t, rng)
        scattered[hit] = True

        weak = alive[weight[alive] < 1e-4]
        keep = rng.random(weak.size) < 0.1
        weight[weak[keep]] *= 10.0
        weight[weak[~keep]] = 0.0
        alive = alive[weight[alive] > 0]

    out = []
    for parts in found:
        dx, dy, w = (np.concatenate(p) / photons if j == 2
                     else np.concatenate(p)
                     for j, p in enumerate(zip(*parts)))
        out.append((dx, dy, w))
    return out, even / photons


def carried(station):
    """Section 45: for each wavelength and depth, the scattered light as
    shifts and weights, pooled over the batches, and the light that met the
    surface."""
    particles = particle_phase(station)
    out, even = {}, []
    for wl in YOU2010_TABLE1:
        a, b, b_w = water_at(wl)
        runs = [shifts(a, b, b_w, particles, water_phase(wl), seed)
                for seed in range(BATCHES)]
        out[wl] = [tuple(np.concatenate([r[0][k][j] for r in runs])
                         / (BATCHES if j == 2 else 1) for j in range(3))
                   for k in range(DEPTHS.size)]
        even.append(np.mean([r[1] for r in runs], axis=0))
    return out, np.array(even)


def spread_kernel(found, depth, c, side=SIDE, points=POINTS):
    """The unscattered light and the scattered light it carries, as the
    transform of one kernel: a spike at no shift, plus each scattered
    photon at its shift, relative to the unscattered irradiance."""
    dx, dy, w = found
    step = side / points
    i = np.rint(dx / step).astype(np.int64) % points
    j = np.rint(dy / step).astype(np.int64) % points
    k = np.bincount(j * points + i, w, points * points).reshape(points,
                                                                 points)
    k /= unscattered(c, depth)
    k[0, 0] += 1.0
    return np.fft.rfft2(k)


# -- the sky: Gregg and Carder (1990) ------------------------------------------
def air_mass(zenith):
    """Kasten's path length, equation (13); the zenith angle in degrees."""
    return 1 / (np.cos(np.radians(zenith)) + 0.15 * (93.885 - zenith)
                ** -1.253)


def angstrom(air_mass_type, humidity, wind_mean, wind):
    """The Navy aerosol model as a Junge distribution, equations (20) to
    (26): the Angstrom exponent."""
    a1 = 2000.0 * air_mass_type ** 2
    a2 = max(5.866 * (wind_mean - 2.2), 0.5)
    a3 = max(0.01527 * (wind - 2.2) * NAVY_R, 1.4e-5)
    f = ((2 - humidity / 100) / (6 * (1 - humidity / 100))) ** (1 / 3)
    r = np.array([0.1, 1.0, 10.0])
    dn = sum(a * np.exp(-np.log(r / (f * r0)) ** 2)
             for a, r0 in zip((a1, a2, a3), NAVY_RADII)) / f
    gamma = np.polyfit(np.log(r), np.log(dn), 1)[0]
    return -(gamma + 3)


def sky_share(wavelength, zenith, tau550, air_mass_type, humidity=SKY_HUMIDITY,
              wind_mean=SKY_WIND, wind=SKY_WIND, pressure=STANDARD_PRESSURE):
    """The diffuse share of the downwelling irradiance just above the sea,
    equations (2), (4) to (7), (15), (16), (27), (30) to (36). The gases'
    transmittances and the sun's spectrum multiply both parts alike and
    are left out. ``wavelength`` in nm, ``zenith`` in degrees."""
    lam = wavelength / 1000.0
    m = air_mass(zenith)
    t_r = np.exp(-m * pressure / STANDARD_PRESSURE
                 / (115.6406 * lam ** 4 - 1.335 * lam ** 2))
    alpha = angstrom(air_mass_type, humidity, wind_mean, wind)
    tau = tau550 * (lam / 0.55) ** -alpha
    omega = (-0.0032 * air_mass_type + 0.972) * np.exp(3.06e-4 * humidity)
    t_aa = np.exp(-(1 - omega) * tau * m)
    t_as = np.exp(-omega * tau * m)
    mean_cos = 0.82 if alpha < 0 else 0.65 if alpha > 1.2 \
        else -0.1417 * alpha + 0.82
    b3 = np.log(1 - mean_cos)
    b1 = b3 * (1.459 + b3 * (0.1595 + 0.4129 * b3))
    b2 = b3 * (0.0783 + b3 * (-0.3824 - 0.5874 * b3))
    mu = np.cos(np.radians(zenith))
    f_a = 1 - 0.5 * np.exp((b1 + b2 * mu) * mu)
    direct = t_r * np.exp(-tau * m)
    rayleigh = t_aa * (1 - t_r ** 0.95) * 0.5
    aerosol = t_aa * t_r ** 1.5 * (1 - t_as) * f_a
    return (rayleigh + aerosol) / (direct + rayleigh + aerosol)


def sky_below(station):
    """Section 48: Ed under a flat surface from the Monte Carlo, for a sky
    of uniform radiance, per unit planar irradiance of the sky above the
    surface, at each wavelength and depth."""
    particles = particle_phase(station)
    out = []
    for wl in YOU2010_TABLE1:
        a, b, b_w = water_at(wl)
        out.append(np.mean([simulate(a, b, b_w, particles, water_phase(wl),
                                     None, seed, depths=DEPTHS)["ed"]
                            for seed in range(BATCHES)], axis=0))
    return np.array(out)


def flicker(u10, models, seeds=range(REALIZATIONS), side=SIDE,
            points=POINTS, skies=None):
    """The coefficient of variation at each wavelength and depth, pooled
    over the realizations, for each model of the light; the surfaces' mean
    square slope, what the spectrum gives for the same wavenumbers, and the
    spread expected of that mean.

    ``models`` maps a name to (kernel, even): kernel(depth, i) gives the
    transform of the blur for wavelength i, and even[i, depth] the light
    spread evenly. ``skies`` maps a name to (model, more): that model with
    ``more`` added to its even light.
    """
    amp = amplitudes(u10, side, points)
    kx, ky = wavenumbers(side, points)
    w = (kx * kx + ky * ky) * amp * amp
    expected = float(np.sum(w))
    # a wavenumber and its opposite share one random amplitude, whose square
    # varies as much as its mean: the spread of the mean of the realizations
    sampling = float(np.sqrt(2 * np.sum(w * w) / len(seeds)))
    del kx, ky, w
    cs = [sum(water_at(wl)[:2]) for wl in YOU2010_TABLE1]
    seas, slopes = [], []
    for seed in seeds:
        eta, sx, sy = surface(amp, seed, side)
        slopes.append(float(np.mean(sx * sx + sy * sy)))
        seas.append((eta, rays(eta, sx, sy)))
        del sx, sy
    sums = {name: np.zeros((len(cs), DEPTHS.size, 2)) for name in models}
    for j, z in enumerate(DEPTHS):
        kernels = {name: [kernel(z, i) for i in range(len(cs))]
                   for name, (kernel, _) in models.items()}
        for eta, beams in seas:
            for i, image in enumerate(patterns(eta, beams, z, cs, side)):
                transform = np.fft.rfft2(image)
                for name in models:
                    sums[name][i, j] += moments(transform * kernels[name][i])
        del kernels
    cv = {}
    evens = {name: (name, even) for name, (_, even) in models.items()}
    for name, (model, more) in (skies or {}).items():
        evens[name] = (model, models[model][1] + more)
    for name, (model, even) in evens.items():
        mean, square = (sums[model] / len(seeds)).transpose(2, 0, 1)
        spread = np.sqrt(np.maximum(square - mean * mean, 0.0))
        cv[name] = spread / (mean + even)
    return cv, float(np.mean(slopes)), expected, sampling


# -- the run ------------------------------------------------------------------

def table(measured, cv, wls, title):
    print(f"\n{title}")
    for i, wl in enumerate(wls):
        print(f"\n  {wl} nm  depth  measured   model at "
              + "   ".join(f"{u:g}" for u in WINDS) + " m/s   measured/model")
        for j, z in enumerate(DEPTHS):
            print(f"         {z:5.2f}   {measured[i, j]:.3f}       "
                  + "   ".join(f"{cv[u][i, j]:.3f}" for u in WINDS)
                  + f"        {measured[i, j] / cv[WIND][i, j]:.2f}")


def checks(measured, cv):
    falls = all(np.all(np.diff(cv[u], axis=1) < 0) for u in WINDS)
    redder = all(np.all(cv[u][-1] > cv[u][0]) for u in WINDS)
    shallow = DEPTHS <= CHECKED_TO
    ratio = measured[:, shallow] / cv[WIND][:, shallow]
    within_two = bool(np.all((ratio >= 0.5) & (ratio <= 2.0)))
    for text, ok in (("falls with depth at every wavelength and wind", falls),
                     ("higher at 670 nm than at 443 nm at every depth", redder),
                     (f"measured within a factor of 2, to {CHECKED_TO} m, at "
                      f"{WIND} m/s", within_two)):
        print(f"  {'yes' if ok else 'NO '}  {text}")
    return dict(falls=falls, redder=redder, within_two=within_two,
                ratio=ratio)


def main():
    _banner()
    darecki = jerlov.darecki2011_irradiance_cv()
    assert np.allclose(darecki.depth_m, DEPTHS)
    wls = list(YOU2010_TABLE1)
    assert wls == [int(w) for w in darecki.wavelengths_nm]
    measured = darecki.cv.T
    b532 = water_at(532)[1]
    by_b = sorted(jerlov.PETZOLD_STATIONS,
                  key=lambda s: abs(jerlov.petzold_scattering(s).b - b532))
    station = by_b[0]
    others = [s for s in by_b[1:]
              if 1 / 3 <= jerlov.petzold_scattering(s).b / b532 <= 3]
    cs = [sum(water_at(wl)[:2]) for wl in wls]

    rest = background(station)
    blurs = {}

    def even_blur(z, i):
        if z not in blurs:
            blurs.clear()
            blurs[z] = blur(z)
        return blurs[z]

    def carrying(found, keep=False):
        made = {}

        def kernel(z, i):
            if (z, i) in made:
                return made[z, i]
            j = int(np.flatnonzero(DEPTHS == z)[0])
            out = even_blur(z, i) * spread_kernel(found[wls[i]][j], z, cs[i])
            if keep:                      # the same for every wind
                made[z, i] = out
            return out
        return kernel

    found, met = carried(station)
    models = {"even": (even_blur, rest),
              "carried": (carrying(found, keep=True), met)}
    below = sky_below(station)
    shares = {atm: np.array([sky_share(wl, SUN_ZENITH, *atm) for wl in wls])
              for atm in ATMOSPHERES}
    skies = {atm: ("carried", (share / (1 - share))[:, None] * below)
             for atm, share in shares.items()}

    rule("The sea surface")
    k_high = np.pi * POINTS / SIDE
    print(f"""Elfouhaily et al. (1997), fully developed (Omega_c = {OMEGA_C}),
the wind along the sun's plane; u* from Wu (1982). On a square {SIDE:g} m
across, {POINTS} points a side: waves from {2 * np.pi / k_high * 1000:.1f} mm
to {SIDE:g} m, {REALIZATIONS} realizations each. Mean square slope:

  U10    u*     realized  same waves         longer   all waves  Cox & Munk""")
    cv, surfaces = {"even": {}, "carried": {}}, {}
    for u in WINDS:
        these = dict(models)
        if u == WIND:
            for s in others:
                f, m = carried(s)
                these[s] = (carrying(f), m)
        found_cv, realized, within, sampling = flicker(u, these, skies=skies)
        for name, value in found_cv.items():
            cv.setdefault(name, {})[u] = value
        longer = slope_variance(u, 1e-4, 2 * np.pi / SIDE)
        total = slope_variance(u, 1e-4, 1e5)
        cm = COX_MUNK[0] + COX_MUNK[1] * wind_at(COX_MUNK_HEIGHT, u)
        surfaces[u] = dict(u_star=float(friction_velocity(u)),
                           realized=realized, expected=within,
                           sampling=sampling, longer=longer, total=total,
                           cox_munk=cm)
        print(f"  {u:4.1f}  {friction_velocity(u):.3f}   {realized:.4f}"
              f"    {within:.4f} +- {sampling:.4f}   {longer:.4f}   {total:.4f}"
              f"     {cm:.4f} +- {COX_MUNK[2]}")
    held = all(abs(v["realized"] - v["expected"]) <= 3 * v["sampling"]
               for v in surfaces.values())
    near = all(abs(v["total"] - v["cox_munk"]) <= COX_MUNK[2]
               for v in surfaces.values())
    print(f"""
"Same waves" is what the spectrum gives for the wavenumbers on the grid,
with the spread to expect of the mean of the realizations: a few long
waves carry much of the slope, and their amplitudes are random. "Longer"
is what the waves longer than the square would add, left out of the
realization; "all waves" is the spectrum's whole slope variance, and Cox
& Munk's is at the wind {COX_MUNK_HEIGHT:g} m up.

  {'yes' if held else 'NO '}  realized within three times that spread of the same waves
  {'yes' if near else 'NO '}  all waves within Cox & Munk's 0.004""")

    rule("The flicker, against Darecki et al. (2011), Figure 13a")
    print(f"""Water from You et al. (2010), Table 1; the particles scatter with
the phase function of Petzold's {station}. Coefficient of variation.""")
    table(measured, cv["even"], wls,
          "As section 44 fixed it: the scattered light spread evenly.")
    rule("The checks fixed beforehand (DECISIONS.md section 44)")
    first = checks(measured, cv["even"])

    rule("Looking for the cause (DECISIONS.md section 45)")
    table(measured, cv["carried"], wls,
          "1. The scattered light carries the pattern, shifted as it was "
          "scattered:")
    print("\nSection 44's checks, applied to it:")
    second = checks(measured, cv["carried"])
    print(f"""
2. With another station's phase function, measured/model at {WIND} m/s:

  station    b(530)   depth: """ + "  ".join(f"{z:5.2f}" for z in DEPTHS))
    for s in [station] + others:
        for i, wl in enumerate(wls):
            label = (f"  {s:<9}  {jerlov.petzold_scattering(s).b:5.3f}"
                     if i == 0 else " " * 19)
            print(f"{label}  {wl} nm "
                  + "  ".join(f"{measured[i, j] / cv[s if s != station else 'carried'][WIND][i, j]:5.2f}"
                              for j in range(DEPTHS.size)))

    sizes = {}
    for label, side, points in (("2 m square, 1 mm", SIDE / 2, POINTS // 2),
                                ("4 m square, 2 mm", SIDE, POINTS // 2)):
        def kernel(z, i, side=side, points=points):
            return blur(z, side, points)
        found_cv = flicker(WIND, {"even": (kernel, rest)}, side=side,
                           points=points)[0]
        sizes[label] = found_cv["even"]
    print(f"""
3 and 4. Section 44's model on a smaller square, and on a coarser grid,
at {WIND} m/s: the coefficient of variation as a share of section 44's.

  grid               depth: """ + "  ".join(f"{z:5.2f}" for z in DEPTHS))
    for label, value in sizes.items():
        for i, wl in enumerate(wls):
            head = f"  {label:<17}" if i == 0 else " " * 19
            print(f"{head}  {wl} nm "
                  + "  ".join(f"{value[i, j] / cv['even'][WIND][i, j]:5.2f}"
                              for j in range(DEPTHS.size)))
    rule("The sky's light (DECISIONS.md section 48)")
    g = GERNEZ_SKY
    zeniths = list(range(20, 90, 10))
    printed = jerlov.gernez2009_diffuse_share()
    printed = dict(zip(printed.sun_zenith_deg, 100 * printed.diffuse_fraction))
    ours = {wl: [100 * sky_share(wl, z, g["tau550"], g["air_mass_type"],
                                 g["humidity"], g["wind_mean"], g["wind"])
                 for z in zeniths] for wl in (442, 510, 560)}
    print(f"""The share of diffuse light above the sea, Gregg and Carder (1990), with
Gernez and Antoine's settings: tau(550) = {g['tau550']}, a marine air mass,
{g['humidity']:g} percent humidity; percent, against what they print.

  sun     """ + "".join(f"{z:6d}" for z in zeniths) + """
  printed """ + "".join(f"{printed[z]:6.0f}" for z in zeniths))
    for wl, row in ours.items():
        print(f"  {wl} nm  " + "".join(f"{v:6.1f}" for v in row))
    low = np.min([ours[wl] for wl in ours], axis=0) - 3
    high = np.max([ours[wl] for wl in ours], axis=0) + 3
    order = all(low[k] <= printed[z] <= high[k]
                for k, z in enumerate(zeniths) if z <= 70)
    print(f"""
  {'yes' if order else 'NO '}  20 to 70 degrees: each printed share within the model's at 442-560 nm,
       widened by 3 points

The sky as uniform light under the waves, added to section 45's model; the
sun at {SUN_ZENITH:g} degrees. For each atmosphere the sky's share at
""" + ", ".join(f"{wl}" for wl in wls) + f""" nm, section 44's checks, and measured/model at
{WIND} m/s to {CHECKED_TO} m and below.

  tau(550)  air mass   share, percent        checks    to {CHECKED_TO} m     below""")
    sky_checks = {}
    for atm in ATMOSPHERES:
        with_sky = {u: cv[atm][u] for u in WINDS}
        with contextlib.redirect_stdout(io.StringIO()):
            found_checks = checks(measured, with_sky)
        ratio = measured / with_sky[WIND]
        deep = ratio[:, DEPTHS > CHECKED_TO]
        sky_checks[atm] = dict(found_checks, deep=deep)
        marks = "".join("y" if found_checks[k] else "n"
                        for k in ("falls", "redder", "within_two"))
        print(f"  {atm[0]:8.2f}  {'marine' if atm[1] == 1 else 'continental':<11}"
              + " ".join(f"{100 * v:5.1f}" for v in shares[atm])
              + f"      {marks}      {found_checks['ratio'].min():.2f}-"
              f"{found_checks['ratio'].max():.2f}    {deep.min():.2f}-"
              f"{deep.max():.2f}")
    least = min(ATMOSPHERES, key=lambda a: shares[a].mean())
    most = max(ATMOSPHERES, key=lambda a: shares[a].mean())
    bare = (measured / cv["carried"][WIND])[:, DEPTHS > CHECKED_TO]
    print(f"""
  checks: falls with depth, higher at 670 than at 443 nm, within a factor
  of 2 to {CHECKED_TO} m (y or n). Without a sky, section 45's model:
  {second['ratio'].min():.2f}-{second['ratio'].max():.2f} and {bare.min():.2f}-{bare.max():.2f}.""")
    for atm, label in ((least, "smallest"), (most, "largest")):
        table(measured, {u: cv[atm][u] for u in WINDS}, wls,
              f"With the {label} sky's share: tau(550) = {atm[0]:g}, "
              f"{'marine' if atm[1] == 1 else 'continental'} air:")

    rule("Before you use any of this")
    fresh_less = 100 * (1 - jerlov.pure_water_scattering(
        500.0, salinity_psu=0.0) / jerlov.pure_water_scattering(
        500.0, salinity_psu=SALINITY_PSU))
    print(f"""  - The surface is linear, random and frozen; the variation is taken over
    positions, where Darecki's is over time at one point. Waves longer
    than {SIDE:g} m are left out (3 above suggests they matter little).
  - The sea is fully developed, the wind blows along the sun's plane, and
    the wind's height is taken as 10 m; Darecki gives none of these.
  - The pure water taken from Petzold's measurement, to leave the particles'
    scattering, is Morel's formula for a salinity of {SALINITY_PSU:g}, a choice
    of this script. At 0 it scatters {fresh_less:.0f} percent less.
  - Rays that would meet the surface again are not followed, and the sun's
    disc is applied as a shift of the whole pattern, which holds to first
    order.
  - The sky is taken as uniform, above the sea and under it, and its
    share from a model of the air, bracketed since Darecki did not record
    it. A real clear sky is brighter near the sun, and the waves gather
    some of that light too.
  - The water is You et al.'s, measured the same day; the phase function
    is Petzold's, and the station moves the result (2 above).

  Every one of these is a choice you can replace with a measurement.
""")
    return dict(station=station, others=others, cv=cv, surfaces=surfaces,
                held=held, near=near, first=first, second=second,
                sizes=sizes, measured=measured, order=order, ours=ours,
                shares=shares, sky_checks=sky_checks, least=least,
                most=most)


# -- the picture: light shafts, looking up towards the sun ---------------------

EYE_DEPTH = 6.0             # m
FIELD = 70.0                # degrees across the picture
PICTURE = 400               # pixels a side
SHAFT_POINTS = 1024         # a coarser surface for the picture, 4 mm apart
SLICE = 0.05                # m between the depths the light is found at
PICTURE_WAVELENGTH = 532


def write_png(path, pixels):
    """Write an 8-bit RGB image, ``pixels`` of shape (h, w, 3) in 0-1."""
    data = np.clip(np.rint(np.asarray(pixels) * 255), 0, 255).astype(np.uint8)
    height, width, _ = data.shape
    raw = b"".join(b"\x00" + row.tobytes() for row in data)

    def chunk(kind, body):
        return (struct.pack(">I", len(body)) + kind + body
                + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))

    with open(path, "wb") as handle:
        handle.write(b"\x89PNG\r\n\x1a\n")
        handle.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height,
                                                8, 2, 0, 0, 0)))
        handle.write(chunk(b"IDAT", zlib.compress(raw, 9)))
        handle.write(chunk(b"IEND", b""))


def sunbeam_in_water(sun_zenith=SUN_ZENITH):
    """The direction the refracted sunlight travels, z down."""
    sin_w = np.sin(np.radians(sun_zenith)) / N_WATER
    return np.array([sin_w, 0.0, np.sqrt(1 - sin_w ** 2)])


def view(pixels=PICTURE, field=FIELD, sun_zenith=SUN_ZENITH):
    """The direction each pixel looks along, z down: the centre straight
    towards the refracted sun, the top of the picture towards the horizon
    beyond it."""
    forward = -sunbeam_in_water(sun_zenith)
    right = np.array([0.0, 1.0, 0.0])
    up = np.cross(forward, right)
    if up[0] > 0:                         # beyond the sun is -x
        up = -up
    half = np.tan(np.radians(field / 2))
    a = (np.arange(pixels) + 0.5) / pixels * 2 - 1
    across, down = np.meshgrid(a * half, a * half, indexing="xy")
    look = (forward[None, None, :] + across[..., None] * right
            - down[..., None] * up)
    return look / np.linalg.norm(look, axis=-1, keepdims=True)


def vsf(station, angle_deg, b):
    """Petzold's volume scattering function scaled to the water's b. Below
    his first measured angle it is held at the first value."""
    p = jerlov.petzold_scattering(station)
    first = p.angles_deg[[s == "ok" for s in p.statuses]][0]
    angle = np.maximum(np.asarray(angle_deg, float), first)
    return p.vsf_at(angle.ravel()).reshape(angle.shape) * b / p.b


def shafts(eta, beams, station, side=SIDE, eye_depth=EYE_DEPTH,
           wavelength=PICTURE_WAVELENGTH, pixels=PICTURE, field=FIELD,
           step=SLICE):
    """The radiance of the sunlight scattered once towards an eye looking
    up, per unit planar irradiance above the surface.

    Along each line of sight, the unscattered sunlight at each depth, blurred
    by the sun's disc, is scattered towards the eye by the volume scattering
    function at the angle between the sunbeam and the line of sight, and
    thinned by exp(-c s) on its way to the eye.
    """
    a, b, _ = water_at(wavelength)
    c = a + b
    look = view(pixels, field)
    up = -look[..., 2]                    # cosine with the vertical, upwards
    beam = sunbeam_in_water()
    angle = np.degrees(np.arccos(np.clip(-(look @ beam), -1, 1)))
    beta = vsf(station, angle, b)
    n = eta.shape[0]
    cell = side / n
    radiance = np.zeros(look.shape[:2])
    seen = up > 0.05
    for z in np.arange(eye_depth - step / 2, 0, -step):
        image, = patterns(eta, beams, z, [c], side)
        kernel = blur(z, side, n)
        image = np.fft.irfft2(np.fft.rfft2(image) * kernel, s=image.shape)
        s = np.where(seen, (eye_depth - z) / np.where(seen, up, 1), 0.0)
        x = (s * look[..., 0]) / cell % n
        y = (s * look[..., 1]) / cell % n
        i, j = np.floor(x).astype(int), np.floor(y).astype(int)
        fx, fy = x - i, y - j
        i1, j1 = (i + 1) % n, (j + 1) % n
        here = ((1 - fx) * (1 - fy) * image[j, i] + fx * (1 - fy) * image[j, i1]
                + (1 - fx) * fy * image[j1, i] + fx * fy * image[j1, i1])
        radiance += np.where(seen, beta * here * np.exp(-c * s)
                             * step / np.where(seen, up, 1), 0.0)
    return radiance, seen


def picture(path, station):
    """Write the light shafts seen looking up towards the sun at 5.5 m/s."""
    amp = amplitudes(WIND, SIDE, SHAFT_POINTS)
    eta, sx, sy = surface(amp, 0, SIDE)
    beams = rays(eta, sx, sy)
    radiance, seen = shafts(eta, beams, station)
    flat = np.zeros_like(eta)
    smooth, _ = shafts(flat, rays(flat, flat, flat), station)
    rule("The picture")
    ratio = np.where(seen, radiance / np.where(seen, smooth, 1), 0.0)
    print(f"""Looking up towards the sun from {EYE_DEPTH:g} m, {FIELD:g} degrees across, at
{PICTURE_WAVELENGTH} nm: the sunlight scattered once towards the eye, from the unscattered
beam under a {WIND} m/s sea, beside the same under a flat surface. The
brightest point of the shafts is {ratio[seen].max():.1f} times the flat surface's there;
half the picture is within {np.percentile(np.abs(ratio[seen] - 1), 50) * 100:.0f} percent of it.""")
    top = np.percentile(np.concatenate([radiance[seen], smooth[seen]]), 99.5)
    tones = [np.clip(r / top, 0, 1) ** (1 / 2.2) for r in (radiance, smooth)]
    tones.append(np.clip(ratio / 2, 0, 1))
    gap = np.ones((PICTURE, 8))
    grey = np.hstack([tones[0], gap, tones[1], gap, tones[2]])
    write_png(path, np.repeat(grey[..., None], 3, axis=2))
    print(f"""
Written to {path}: left, the {WIND} m/s sea; middle, a flat surface,
both on the same scale; right, the one divided by the other, black at 0
and white at 2 or more.""")
    return dict(radiance=radiance, smooth=smooth, seen=seen, ratio=ratio)


if __name__ == "__main__":
    png = None
    if "--png" in sys.argv:
        png = sys.argv[sys.argv.index("--png") + 1]
    result = main()
    if png:
        picture(png, result["station"])
    sys.exit(0)

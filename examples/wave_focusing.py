"""Light under waves: how much it flickers, against what was measured.

For anyone working with the light just below a sunlit sea: the surface
waves gather the sunbeam into bright lines that move over everything
below, and how strongly the light at one point flickers falls with depth.
The package carries what Darecki et al. (2011) measured of it (section 42
of DECISIONS.md) and no model, since waves are not set by the water type.
This example builds one from published parts and checks it against that
measurement, with its choices fixed beforehand (section 44).

    python examples/wave_focusing.py               # about N minutes

The method. A sea surface is drawn at random from the wave spectrum of
Elfouhaily et al. (1997), for a wind of 4.1, 5.5 or 6.4 m/s, on a square 4
m across with a point every millimetre. Each point refracts the sunbeam,
and the ray goes straight down to a depth, where the rays are counted on
a horizontal grid of the same spacing. The sun's disc and a 2.5 mm
collector blur that pattern. Only the light that arrives unscattered
carries the pattern; the scattered sunlight is a uniform background,
taken from the Monte Carlo of `radiance_distribution.py` with a flat
surface, copied here so that the script stands alone. The coefficient of
variation is the standard deviation of the irradiance over the grid
divided by its mean.
"""

import sys

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
    particles = p.vsf_at(grid) - jerlov.pure_water_vsf(grid, p.wavelength_nm)
    if np.any(particles <= 0):
        raise ValueError(f"{station}: pure water exceeds the measurement")
    cdf, cos_angle, measured = inverse_cdf(grid, particles)
    b_particles = p.b - float(jerlov.pure_water_scattering(p.wavelength_nm))
    return dict(cdf=cdf, cos=cos_angle, straight=1 - measured / b_particles,
                first_deg=float(first), b=p.b)


def water_phase(wavelength, salinity=37.0):
    grid = np.linspace(0.0, 180.0, 1801)
    cdf, cos_angle, _ = inverse_cdf(
        grid, jerlov.pure_water_vsf(grid, wavelength, salinity))
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


def patterns(eta, beams, depth, cs, side=SIDE):
    """The unscattered irradiance on a horizontal grid at one depth, for
    each beam attenuation in ``cs``; each ray is shared among the four
    nearest grid points."""
    tx, ty, tz, power = beams
    n = eta.shape[0]
    step = side / n
    travel = (depth + eta) / -tz                      # along the ray
    grid = np.arange(n)
    px = grid[None, :] + travel * tx / step
    py = grid[:, None] + travel * ty / step
    i0, j0 = np.floor(px).astype(np.int64), np.floor(py).astype(np.int64)
    fx, fy = px - i0, py - j0
    i0, j0 = i0 % n, j0 % n
    i1, j1 = (i0 + 1) % n, (j0 + 1) % n
    corners = [(j0 * n + i0, (1 - fx) * (1 - fy)), (j0 * n + i1, fx * (1 - fy)),
               (j1 * n + i0, (1 - fx) * fy), (j1 * n + i1, fx * fy)]
    out = []
    for c in cs:
        weight = power * np.exp(-c * travel)
        image = np.zeros(n * n)
        for index, share in corners:
            image += np.bincount(index.ravel(), (weight * share).ravel(),
                                 n * n)
        out.append(image.reshape(n, n))
    return out


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
        return np.fft.rfft2(k / k.sum())

    sun = shape(lambda x, y: (x / rx) ** 2 + (y / ry) ** 2 <= 1, max(rx, ry))
    disc = shape(lambda x, y: x * x + y * y <= (COLLECTOR / 2) ** 2,
                 COLLECTOR / 2)
    return sun * disc


def background(station, sun_zenith=SUN_ZENITH):
    """Ed under a flat surface from the Monte Carlo, less the sunlight that
    arrives unscattered: the light taken as uniform. Per unit planar
    irradiance above the surface, at each wavelength and depth."""
    particles = particle_phase(station)
    out = {}
    for wl, (c_w, w_w, c_p, w_p) in YOU2010_TABLE1.items():
        b_w, b = c_w * w_w, c_w * w_w + c_p * w_p
        a = c_w + c_p - b
        ed = np.mean([simulate(a, b, b_w, particles, water_phase(wl),
                               sun_zenith, seed, depths=DEPTHS)["ed"]
                      for seed in range(BATCHES)], axis=0)
        out[wl] = ed - unscattered(a + b, DEPTHS)
    return out


def flicker(u10, rest, seeds=range(REALIZATIONS)):
    """The coefficient of variation at each wavelength and depth, pooled
    over the realizations; the surfaces' mean square slope, and what the
    spectrum gives for the same wavenumbers, with the spread expected of
    that mean."""
    amp = amplitudes(u10)
    kx, ky = wavenumbers()
    w = (kx * kx + ky * ky) * amp * amp
    expected = float(np.sum(w))
    # a wavenumber and its opposite share one random amplitude, whose square
    # varies as much as its mean: the spread of the mean of the realizations
    spread_expected = float(np.sqrt(2 * np.sum(w * w) / len(seeds)))
    del kx, ky, w
    cs = [c_w + c_p for c_w, _, c_p, _ in YOU2010_TABLE1.values()]
    kernels = {z: blur(z) for z in DEPTHS}
    sums = np.zeros((len(cs), DEPTHS.size, 2))
    slopes = []
    for seed in seeds:
        eta, sx, sy = surface(amp, seed)
        slopes.append(float(np.mean(sx * sx + sy * sy)))
        beams = rays(eta, sx, sy)
        del sx, sy
        for j, z in enumerate(DEPTHS):
            for i, image in enumerate(patterns(eta, beams, z, cs)):
                seen = np.fft.irfft2(np.fft.rfft2(image) * kernels[z],
                                     s=image.shape)
                sums[i, j] += seen.mean(), np.mean(seen * seen)
    sums /= len(seeds)
    mean, square = sums[..., 0], sums[..., 1]
    spread = np.sqrt(np.maximum(square - mean * mean, 0.0))
    rest = np.array([rest[wl] for wl in YOU2010_TABLE1])
    return (spread / (mean + rest), float(np.mean(slopes)), expected,
            spread_expected)


# -- the run ------------------------------------------------------------------

def main():
    _banner()
    measured = jerlov.darecki2011_irradiance_cv()
    assert np.allclose(measured.depth_m, DEPTHS)
    wls = list(YOU2010_TABLE1)
    assert wls == [int(w) for w in measured.wavelengths_nm]
    c_w, w_w, c_p, w_p = YOU2010_TABLE1[532]
    b532 = c_w * w_w + c_p * w_p
    station = min(jerlov.PETZOLD_STATIONS,
                  key=lambda s: abs(jerlov.petzold_scattering(s).b - b532))

    rule("The sea surface")
    k_low = 2 * np.pi / SIDE
    k_high = np.pi * POINTS / SIDE
    print(f"""Elfouhaily et al. (1997), fully developed (Omega_c = {OMEGA_C}),
the wind along the sun's plane; u* from Wu (1982). On a square {SIDE:g} m
across, {POINTS} points a side: waves from {2 * np.pi / k_high * 1000:.1f} mm
to {SIDE:g} m, {REALIZATIONS} realizations each. Mean square slope:

  U10    u*     realized  same waves         longer   all waves  Cox & Munk""")
    rest = background(station)
    cv, surfaces = {}, {}
    for u in WINDS:
        cv[u], realized, within, sampling = flicker(u, rest)
        longer = slope_variance(u, 1e-4, k_low)
        total = slope_variance(u, 1e-4, 1e5)
        w = wind_at(COX_MUNK_HEIGHT, u)
        cm = COX_MUNK[0] + COX_MUNK[1] * w
        surfaces[u] = dict(u_star=float(friction_velocity(u)),
                           realized=realized, expected=within,
                           sampling=sampling,
                           longer=longer, total=total, cox_munk=cm)
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
    print(f"""Water from You et al. (2010), Table 1; scattered light from the
Monte Carlo with {station}'s phase function. Coefficient of variation:""")
    for i, wl in enumerate(wls):
        print(f"\n  {wl} nm  depth  measured   model at "
              + "   ".join(f"{u:g}" for u in WINDS) + " m/s   measured/model")
        for j, z in enumerate(DEPTHS):
            print(f"         {z:5.2f}   {measured.cv[j, i]:.3f}       "
                  + "   ".join(f"{cv[u][i, j]:.3f}" for u in WINDS)
                  + f"        {measured.cv[j, i] / cv[WIND][i, j]:.2f}")

    falls = all(np.all(np.diff(cv[u], axis=1) < 0) for u in WINDS)
    redder = all(np.all(cv[u][-1] > cv[u][0]) for u in WINDS)
    shallow = DEPTHS <= CHECKED_TO
    ratio = measured.cv.T[:, shallow] / cv[WIND][:, shallow]
    within_two = bool(np.all((ratio >= 0.5) & (ratio <= 2.0)))
    rule("The checks fixed beforehand (DECISIONS.md section 44)")
    for text, ok in (("falls with depth at every wavelength and wind", falls),
                     ("higher at 670 nm than at 443 nm at every depth", redder),
                     (f"measured within a factor of 2, to {CHECKED_TO} m, at "
                      f"{WIND} m/s", within_two)):
        print(f"  {'yes' if ok else 'NO '}  {text}")
    return dict(station=station, cv=cv, surfaces=surfaces, ratio=ratio,
                held=held, near=near,
                falls=falls, redder=redder, within_two=within_two,
                measured=measured.cv.T)


if __name__ == "__main__":
    main()
    sys.exit(0)

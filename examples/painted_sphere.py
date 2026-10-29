"""A painted sphere under water, seen from four directions.

For anyone rendering, photographing or designing objects that are looked at
under water: how the colour and the shading of a painted object change
with the direction it is seen from. The package gives the light on a face
turned straight up, and refuses to guess any other (DECISIONS.md section
33). This example computes the light from every direction with the Monte
Carlo solution of `radiance_distribution.py`, copied here so that the
script stands alone, and lights a sphere with it (section 41).

    python examples/painted_sphere.py                   # about two minutes
    python examples/painted_sphere.py --png painted_sphere.png    # and an image

The image is written only when asked for, with nothing beyond the standard
library and NumPy: four paints down, under the sun and then under an
overcast; across, each paint in air under daylight, then the sphere seen
from the four directions, with a gloss coat and, under the sun, its shadow.

The method. The Monte Carlo gives the radiance arriving from each
direction at three depths, at twelve wavelengths, interpolated between
them. A face of the sphere receives the radiance from the half of the
directions it faces, weighted by the cosine, and the sunbeam if it faces
the sun; the paint scatters that equally in every direction. Between the
sphere and the eye, the sphere's light is thinned by exp(-c r), and the
water in between adds what it adds to the background seen past the sphere:
the background's radiance at the eye, less its radiance at the sphere,
thinned the same way. Looking horizontally that is `Scene.observe`.
"""

import struct
import sys
import warnings
import zlib

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


def swatch(rgb):
    """A terminal colour block."""
    r, g, b = (int(round(255 * float(np.clip(c, 0, 1)))) for c in rgb)
    return f"\x1b[48;2;{r};{g};{b}m    \x1b[0m"


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


N_WATER = 1.34              # sea water against air, in the visible
SALINITY_PSU = 37.0         # for pure water's scattering; not the type's
WATER_TYPE = "II"
DEPTH = 10.0                # the sphere's depth, m
DISTANCE = 2.0              # from the eye, m
DEPTHS = np.array([DEPTH - DISTANCE, DEPTH, DEPTH + DISTANCE])
SUN_ZENITH = 40.0           # degrees, in air
D_ZENITH, D_AZIMUTH = 10.0, 45.0
PHOTONS, BATCHES = 50_000, 4
MC_WAVELENGTHS = np.array([412.0, 440, 470, 500, 530, 560, 590, 610, 630,
                           650, 675, 700])
WAVELENGTHS = np.arange(412.0, 701.0, 4.0)
RADIUS = 0.1                # the sphere's, m; only its shadow depends on it
COAT = 1.5                  # refractive index of a clear gloss coat
PIXELS = 160                # across one sphere's square in the image
FILL = 0.85                 # the sphere's diameter, as a share of the square
SUBSAMPLES = 4              # per side of a pixel, to smooth the sphere's edge

#: Smooth stand-in paints, as in synthetic_underwater_images.py; real work
#: should use measured reflectance spectra.
PAINTS = {
    "grey 50%": lambda wl: np.full_like(wl, 0.50),
    "red":      lambda wl: 0.05 + 0.55 * (wl > 600),
    "green":    lambda wl: 0.05 + 0.35 * np.exp(-0.5 * ((wl - 550) / 45) ** 2),
    "blue":     lambda wl: 0.05 + 0.40 * np.exp(-0.5 * ((wl - 465) / 40) ** 2),
}

#: Where the eye looks, as a direction with z down and the sunlight
#: travelling towards +x; which way is up in the picture; and which of
#: DEPTHS the eye is at.
VIEWS = {
    "from above":    (np.array([0.0, 0.0, 1.0]), np.array([-1.0, 0.0, 0.0]), 0),
    "towards sun":   (np.array([-1.0, 0.0, 0.0]), np.array([0.0, 0.0, -1.0]), 1),
    "sun behind":    (np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, -1.0]), 1),
    "from below":    (np.array([0.0, 0.0, -1.0]), np.array([-1.0, 0.0, 0.0]), 2),
}


# -- the Monte Carlo, as in radiance_distribution.py ---------------------------
# The seven functions below are copied unchanged from that example; a test
# checks that the two copies stay the same.

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


def coefficients(water_type, wavelength):
    w = jerlov.water(water_type)
    return (float(w.a(wavelength)), float(w.b(wavelength)),
            float(jerlov.pure_water_scattering(wavelength, salinity_psu=SALINITY_PSU)))


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


# -- the light on a sphere ---------------------------------------------------

def light_field(station, sun_zenith=SUN_ZENITH):
    """The scattered radiance in every cell, Ed, a, b and pure water's b at
    MC_WAVELENGTHS and DEPTHS, with one of Petzold's phase functions for
    the particles; ``sun_zenith`` None for a uniform overcast."""
    particles = particle_phase(station)
    radiance, ed, iops = [], [], []
    for wl in MC_WAVELENGTHS:
        a, b, bw = coefficients(WATER_TYPE, wl)
        runs = [simulate(a, b, bw, particles, water_phase(wl), sun_zenith,
                         seed=seed, depths=DEPTHS) for seed in range(BATCHES)]
        radiance.append(np.mean([r["radiance"] for r in runs], axis=0))
        ed.append(np.mean([r["ed"] for r in runs], axis=0))
        iops.append((a, b, bw))
    a, b, bw = np.array(iops).T
    return dict(radiance=np.array(radiance), ed=np.array(ed), c=a + b, b=b,
                bw=bw, station=station, sun_zenith=sun_zenith)


def cell_directions(sub=6):
    """Directions filling every radiance cell of the whole sphere of
    directions, ``sub`` by ``sub`` to a cell and in cell order; their solid
    angles; and for each cell, the cell of the folded half (azimuth 0 to
    180) that the Monte Carlo counted it in."""
    n_th, n_ph = int(180 / D_ZENITH), int(180 / D_AZIMUTH)
    dirs, d_omega, folded = [], [], []
    for i in range(n_th):
        edges = np.radians(D_ZENITH * (i + np.arange(sub + 1) / sub))
        th = 0.5 * (edges[1:] + edges[:-1])
        band = (np.cos(edges[:-1]) - np.cos(edges[1:])) \
            * np.radians(D_AZIMUTH) / sub
        for j in range(2 * n_ph):
            ph = np.radians(D_AZIMUTH * (j + (np.arange(sub) + 0.5) / sub))
            t, p = np.meshgrid(th, ph, indexing="ij")
            dirs.append(np.stack([np.sin(t) * np.cos(p), np.sin(t) * np.sin(p),
                                  np.cos(t)], axis=-1).reshape(-1, 3))
            d_omega.append(np.repeat(band, sub))
            folded.append(i * n_ph + (j if j < n_ph else 2 * n_ph - 1 - j))
    return (np.concatenate(dirs), np.concatenate(d_omega), np.array(folded),
            sub * sub)


CELLS = cell_directions()


def cell_weights(normals, chunk=1000):
    """For faces with these outward normals, the cosine-weighted solid angle
    of each cell of the whole sphere of directions that shines on them:
    (faces, cells)."""
    dirs, d_omega, _, per_cell = CELLS
    out = []
    for start in range(0, len(normals), chunk):
        n = normals[start:start + chunk]
        # light travelling along d reaches a face whose normal points
        # against it
        cosine = np.maximum(0.0, -(n @ dirs.T)) * d_omega
        out.append(cosine.reshape(len(n), -1, per_cell).sum(axis=-1))
    return np.concatenate(out)


def sunbeam():
    """The refracted sunbeam's direction, and its irradiance on a face
    square to it per unit planar irradiance above the surface, before any
    loss in the water."""
    mu_air = np.cos(np.radians(SUN_ZENITH))
    sin_w = np.sin(np.radians(SUN_ZENITH)) / N_WATER
    s = np.array([sin_w, 0.0, np.sqrt(1 - sin_w ** 2)])
    return s, (1 - fresnel(np.array([mu_air]), 1.0, N_WATER)[0]) / s[2]


def face_irradiance(field, normals, k):
    """Irradiance on faces with these outward normals at DEPTHS[k], at
    MC_WAVELENGTHS: (faces, wavelengths)."""
    cells = field["radiance"][:, k].reshape(MC_WAVELENGTHS.size, -1)
    scattered = cell_weights(normals) @ cells[:, CELLS[2]].T
    if field["sun_zenith"] is None:
        return scattered
    s, square = sunbeam()
    direct = square * np.exp(-field["c"] * DEPTHS[k] / s[2])
    return scattered + np.maximum(0.0, -(normals @ s))[:, None] * direct


def cell_radiance(field, travel, k):
    """The scattered radiance travelling along each of these directions at
    DEPTHS[k], interpolated linearly between the centres of the cells, and
    to their mean round the vertical straight up and down: (directions,
    wavelengths)."""
    cells = field["radiance"][:, k]
    n_th, n_ph = cells.shape[1], cells.shape[2]
    # nodes: the poles, then cell centres; azimuth mirrored at 0 and 180
    grid = np.concatenate([cells[:, :1].mean(axis=2, keepdims=True)
                           .repeat(n_ph, axis=2), cells,
                           cells[:, -1:].mean(axis=2, keepdims=True)
                           .repeat(n_ph, axis=2)], axis=1)
    grid = np.concatenate([grid[:, :, :1], grid, grid[:, :, -1:]], axis=2)
    th_nodes = np.concatenate([[0.0], (np.arange(n_th) + 0.5) * D_ZENITH,
                               [180.0]])
    ph_nodes = np.concatenate([[0.0], (np.arange(n_ph) + 0.5) * D_AZIMUTH,
                               [180.0]])
    zenith = np.degrees(np.arccos(np.clip(travel[:, 2], -1, 1)))
    azimuth = np.abs(np.degrees(np.arctan2(travel[:, 1], travel[:, 0])))
    i = np.clip(np.searchsorted(th_nodes, zenith) - 1, 0, th_nodes.size - 2)
    j = np.clip(np.searchsorted(ph_nodes, azimuth) - 1, 0, ph_nodes.size - 2)
    u = ((zenith - th_nodes[i]) / (th_nodes[i + 1] - th_nodes[i]))[None, :]
    v = ((azimuth - ph_nodes[j]) / (ph_nodes[j + 1] - ph_nodes[j]))[None, :]
    return ((1 - u) * (1 - v) * grid[:, i, j] + u * (1 - v) * grid[:, i + 1, j]
            + (1 - u) * v * grid[:, i, j + 1]
            + u * v * grid[:, i + 1, j + 1]).T


def coat_reflectance(cos_view, outside=N_WATER):
    """The share of light a clear coat reflects like a mirror, seen at this
    cosine from its normal, from water or (outside=1) from air."""
    return fresnel(np.asarray(cos_view, dtype=float), outside, COAT)


def particle_vsf(field, angle_deg, station):
    """Volume scattering function of water and particles at one angle, at
    MC_WAVELENGTHS, 1/(m sr): the particles' share of b with the shape the
    Monte Carlo uses, Petzold's measured curve less pure water's."""
    p = jerlov.petzold_scattering(station)
    shape = (float(p.vsf_at(angle_deg))
             - float(jerlov.pure_water_vsf(angle_deg, p.wavelength_nm, salinity_psu=SALINITY_PSU)))
    shape /= p.b - float(jerlov.pure_water_scattering(
        p.wavelength_nm, salinity_psu=SALINITY_PSU))
    water = np.array([float(jerlov.pure_water_vsf(angle_deg, wl, salinity_psu=SALINITY_PSU))
                      for wl in MC_WAVELENGTHS])
    return (field["b"] - field["bw"]) * shape + water


def shadowed(field, look, starts, lengths, station):
    """The radiance that the sunbeam, scattered once towards the eye, would
    have added along each line of sight but for the sphere's shadow:
    (lines, wavelengths). Lines start at ``starts`` (m, from the sphere's
    centre, z down) and run along ``look`` for ``lengths`` metres. The
    shadow is the cylinder of RADIUS behind the sphere along the beam."""
    s_dir, square = sunbeam()
    angle = float(np.degrees(np.arccos(np.clip(s_dir @ -look, -1, 1))))
    beta = particle_vsf(field, angle, station)
    # where each line is inside the cylinder: |S + s L| off the axis < R
    s_perp = starts - np.outer(starts @ s_dir, s_dir)
    l_perp = look - (look @ s_dir) * s_dir
    qa = l_perp @ l_perp
    qb = s_perp @ l_perp
    qc = np.sum(s_perp * s_perp, axis=1) - RADIUS ** 2
    root = np.sqrt(np.maximum(qb * qb - qa * qc, 0.0))
    enter, leave = (-qb - root) / qa, (-qb + root) / qa
    leave = np.where(qb * qb - qa * qc > 0, leave, enter)
    # and downstream of the sphere's centre
    downstream = -(starts @ s_dir) / (look @ s_dir)
    if look @ s_dir > 0:
        enter = np.maximum(enter, downstream)
    else:
        leave = np.minimum(leave, downstream)
    enter = np.clip(enter, 0.0, lengths)
    leave = np.clip(leave, enter, lengths)
    # the beam reaching depth DEPTH + z, thinned again on the way to the eye
    k = np.outer(look[2] / s_dir[2] + 1.0, field["c"])
    first = np.exp(-np.outer(DEPTH + starts[:, 2], field["c"]) / s_dir[2])
    span = (np.exp(-k * enter[:, None]) - np.exp(-k * leave[:, None])) / k
    return beta * square * first * span


def background(field, look, k):
    """The water's radiance seen looking along ``look`` at DEPTHS[k]: the
    light travelling the other way. Straight up or down, averaged round the
    vertical; horizontal, the two cells either side of it."""
    travel = -look
    zenith = np.degrees(np.arccos(np.clip(travel[2], -1, 1)))
    azimuth = abs(np.degrees(np.arctan2(travel[1], travel[0])))
    cells = field["radiance"][:, k]
    j = min(int(azimuth // D_AZIMUTH), cells.shape[2] - 1)
    if zenith < D_ZENITH or zenith > 180 - D_ZENITH:
        return cells[:, int(min(zenith // D_ZENITH, cells.shape[1] - 1)), :].mean(-1)
    if np.isclose(zenith % D_ZENITH, 0.0):
        i = int(zenith // D_ZENITH)
        return 0.5 * (cells[:, i - 1, j] + cells[:, i, j])
    return cells[:, int(zenith // D_ZENITH), j]


def on_grid(values):
    """From MC_WAVELENGTHS to WAVELENGTHS, along the last axis."""
    values = np.atleast_2d(values)
    return np.array([np.interp(WAVELENGTHS, MC_WAVELENGTHS, v)
                     for v in values])


def disc():
    """The sphere on a PIXELS-square: where each pixel centre falls, in
    units of the sphere's radius, and the share of the pixel the sphere
    covers, from SUBSAMPLES by SUBSAMPLES points in it."""
    side = ((np.arange(PIXELS) + 0.5) / PIXELS * 2 - 1) / FILL
    x, y = np.meshgrid(side, -side)
    offsets = ((np.arange(SUBSAMPLES) + 0.5) / SUBSAMPLES - 0.5) \
        * (side[1] - side[0])
    cover = np.zeros_like(x)
    for dx in offsets:
        for dy in offsets:
            cover += (x + dx) ** 2 + (y + dy) ** 2 < 1
    return x, y, cover / SUBSAMPLES ** 2


def picture(field, look, up, k_eye, gloss=False, shadow=False):
    """For one direction: the radiance the eye receives from each face of
    the sphere it sees, per unit reflectance, and from the water in front of
    each pixel, with the pixels that show the sphere and how much of each.
    With ``gloss``, a clear coat reflects part of the light like a mirror;
    with ``shadow``, the lines of sight lose what the sphere's shadow keeps
    from them."""
    x, y, cover = disc()
    shown = cover > 0
    # a pixel the edge crosses takes the face at the edge
    r = np.hypot(x[shown], y[shown])
    scale = np.minimum(1.0, 0.999 / np.maximum(r, 1e-12))
    xs, ys = x[shown] * scale, y[shown] * scale
    right = np.cross(up, look)
    normals = (xs[:, None] * right + ys[:, None] * up
               - np.sqrt(1 - xs ** 2 - ys ** 2)[:, None] * look)
    t = np.exp(-jerlov.water(WATER_TYPE).c(WAVELENGTHS) * DISTANCE)
    lit = on_grid(face_irradiance(field, normals, 1)) / np.pi
    mirror = np.zeros_like(lit)
    if gloss:
        cos_view = normals @ -look
        coat = coat_reflectance(cos_view)[:, None]
        # the light the coat sends to the eye travels along -look after
        # reflection, so before it travelled along the mirror image
        travel = -look - 2 * cos_view[:, None] * normals
        mirror = coat * on_grid(cell_radiance(field, travel, 1))
        lit = lit * (1 - coat)
    behind = on_grid(background(field, look, 1))[0]
    at_eye = on_grid(background(field, look, k_eye))[0]
    path = np.tile(at_eye - behind * t, (int(shown.sum()), 1))
    water = np.tile(at_eye, (PIXELS * PIXELS, 1))
    if shadow and field["sun_zenith"] is not None:
        offsets = (x[..., None] * right + y[..., None] * up).reshape(-1, 3) \
            * RADIUS
        starts = offsets - DISTANCE * look
        # to the sphere for the pixels that show it, far past it otherwise
        lengths = np.where(shown.ravel(), DISTANCE, DISTANCE + 20.0)
        lost = on_grid(shadowed(field, look, starts, lengths,
                                field["station"]))
        water = water - lost
        path = path - lost[shown.ravel()]
    return dict(face=lit * t, gloss=mirror * t, path=path, water=water,
                clear=at_eye, shown=shown, cover=cover[shown],
                normals=normals, t=t)


def luminance(radiance):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.CoverageWarning)
        return float(jerlov.spectrum_to_xyz(radiance, WAVELENGTHS)[1])


def luminance_weights():
    """CIE Y of a unit of radiance at each wavelength, so that the luminance
    of many spectra is one matrix product."""
    return np.array([luminance(np.eye(WAVELENGTHS.size)[k])
                     for k in range(WAVELENGTHS.size)])


def linear_srgb(white):
    """The linear sRGB of a unit of radiance at each wavelength, relative to
    ``white``: (wavelengths, 3). sRGB before its transfer function is
    linear in the spectrum, so a picture's thousands of spectra need
    spectrum_to_srgb only once per wavelength. Colours outside the sRGB
    gamut are clipped, as spectrum_to_srgb does."""
    rows = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.CoverageWarning)
        warnings.simplefilter("ignore", jerlov.GamutWarning)
        for k in range(WAVELENGTHS.size):
            v = jerlov.spectrum_to_srgb(np.eye(WAVELENGTHS.size)[k],
                                        WAVELENGTHS, white=white, clip=False)
            # undo the sRGB transfer function (IEC 61966-2-1)
            rows.append(np.where(v <= 0.04045, v / 12.92,
                                 ((np.maximum(v, 0.04045) + 0.055) / 1.055)
                                 ** 2.4))
    return np.array(rows)


def colour(radiance, to_linear):
    """sRGB of one spectrum or of an array of them."""
    linear = np.clip(np.asarray(radiance) @ to_linear, 0.0, 1.0)
    return np.where(linear <= 0.0031308, 12.92 * linear,
                    1.055 * linear ** (1 / 2.4) - 0.055)


def look_at(field, daylight, to_linear, gloss=False, shadow=False):
    """Every sphere and the water round it: their colours, and each sphere's
    mean luminance as a multiple of the water's seen past it, out of any
    shadow."""
    out = {}
    for view, (look, up, k_eye) in VIEWS.items():
        p = picture(field, look, up, k_eye, gloss=gloss, shadow=shadow)
        water = p["water"] * daylight
        clear = p["clear"] * daylight
        w = p["cover"][:, None]
        for paint, reflectance in PAINTS.items():
            seen = (reflectance(WAVELENGTHS) * p["face"] + p["gloss"]
                    + p["path"]) * daylight
            mean = np.sum(w * seen, axis=0) / np.sum(w)
            tile = water.copy()
            tile[p["shown"].ravel()] = (w * seen
                                        + (1 - w) * water[p["shown"].ravel()])
            out[view, paint] = dict(
                pixels=colour(tile, to_linear).reshape(PIXELS, PIXELS, 3),
                mean=colour(mean, to_linear), water=colour(clear, to_linear),
                ratio=luminance(mean) / luminance(clear),
                darkest=float(np.min(water @ luminance_weights()))
                / luminance(clear))
    return out


# --------------------------------------------------------------------------
def main(png=None):
    _banner()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", jerlov.CoverageWarning)
        jerlov.spectrum_to_xyz(np.ones_like(WAVELENGTHS), WAVELENGTHS)
    coverage_note = (str(caught[0].message).split(". The integral")[0]
                     if caught else "")

    # ----------------------------------------------------------------------
    rule("1. What goes in")

    b530 = float(jerlov.water(WATER_TYPE).b(530.0))
    by_b = sorted(jerlov.PETZOLD_STATIONS,
                  key=lambda s: abs(jerlov.petzold_scattering(s).b - b530))
    near, other = by_b[0], by_b[2] if by_b[1] == by_b[0] else by_b[1]
    print(f"""A sphere painted with each of four smooth stand-in colours, {DEPTH:g} m deep in
Jerlov {WATER_TYPE}, seen from {DISTANCE:g} m away. The sun is {SUN_ZENITH:g} degrees from the zenith, alone
in the sky, with D65 for its spectrum. The water's a and b are Williamson
& Hollins's (2022); the particles scatter like Petzold's {near}, the
station nearest in b at 530 nm, as in radiance_distribution.py; {other}, the
next nearest, shows how much that matters (part 4). The Monte Carlo runs
at {MC_WAVELENGTHS.size} wavelengths from {MC_WAVELENGTHS[0]:g} to {MC_WAVELENGTHS[-1]:g} nm, {BATCHES} batches of {PHOTONS:,} photons each.""")

    field = light_field(near)
    daylight = np.interp(WAVELENGTHS, *jerlov.d65())
    ed = on_grid(field["ed"][:, 1])[0] * daylight
    white = ed / np.pi
    to_linear = linear_srgb(white)
    in_air = linear_srgb(daylight)

    # ----------------------------------------------------------------------
    rule("2. A check")

    up_down = np.array([[0.0, 0.0, -1.0], [0.0, 0.0, 1.0]])
    faces = face_irradiance(field, up_down, 1)
    counted = field["ed"][:, 1]
    print(f"""A face turned straight up receives the downwelling irradiance, which the
Monte Carlo also counts directly as the light crossing {DEPTH:g} m. The two
are computed differently: one from the binned radiance and the sunbeam,
the other from the photons themselves.""")
    print(f"\n  {'nm':>5} {'face up':>9} {'Ed':>9} {'face down / face up':>21}")
    for wl, up, down, e in zip(MC_WAVELENGTHS, faces[0], faces[1], counted):
        print(f"  {wl:>5.0f} {up:>9.4f} {e:>9.4f} {down / up:>21.4f}")
    agree = float(np.max(np.abs(faces[0] / counted - 1)))
    print(f"""
  They agree within {100 * agree:.1f} percent at every wavelength. The face turned down
  receives {100 * float(np.min(faces[1] / faces[0])):.1f} to {100 * float(np.max(faces[1] / faces[0])):.1f} percent as much.""")

    # ----------------------------------------------------------------------
    rule("3. Four directions")

    seen = look_at(field, daylight, to_linear)
    print(f"""Each sphere's mean colour, the water seen past it, and the sphere's mean
luminance as a multiple of that water's. Colours are white-balanced to a
white face turned up at {DEPTH:g} m with no water in front of it, the same for
every direction, so brightness can be compared across the table.""")
    if coverage_note:
        print(f"  ({coverage_note}.)")
    print("\n  in air, under daylight and balanced to it: " + "  ".join(
        f"{paint} {swatch(colour(PAINTS[paint](WAVELENGTHS) * daylight, in_air))}"
        for paint in PAINTS))
    for view in VIEWS:
        print(f"\n  {view:<12} water {swatch(seen[view, 'grey 50%']['water'])}")
        for paint in PAINTS:
            s = seen[view, paint]
            print(f"    {paint:<9} {swatch(s['mean'])} {s['ratio']:7.2f}")
    grey = {v: seen[v, "grey 50%"]["ratio"] for v in VIEWS}
    brightest = max(grey, key=grey.get)
    darkest = min(grey, key=grey.get)
    spread = {v: max(seen[v, p]["ratio"] for p in PAINTS)
              / min(seen[v, p]["ratio"] for p in PAINTS) for v in VIEWS}
    widest = max(spread, key=spread.get)
    narrowest = min(spread, key=spread.get)
    print(f"""
  The same grey sphere is {grey[brightest]:.1f} times as bright as the water seen {brightest},
  and {grey[darkest]:.2f} times seen {darkest}: the direction turns a bright object into
  a dark one. The brightest of the four paints is {spread[widest]:.1f} times the darkest
  seen {widest}, and {spread[narrowest]:.2f} times seen {narrowest}, where the face the eye
  sees is lit mostly by the little light that comes up from below.""")

    # ----------------------------------------------------------------------
    rule("4. The phase function")

    second = light_field(other)
    seen_other = look_at(second, daylight, to_linear)
    print(f"""The same spheres with {other}'s phase function for the particles in place of
{near}'s. The water's a and b are unchanged.""")
    print(f"\n  {'grey 50%':<12} {near:>10} {other:>10}")
    change = {}
    for view in VIEWS:
        a_, b_ = seen[view, "grey 50%"]["ratio"], \
            seen_other[view, "grey 50%"]["ratio"]
        change[view] = b_ / a_ - 1
        print(f"  {view:<12} {a_:>10.2f} {b_:>10.2f}")
    beam, _ = sunbeam()
    turned = {v: float(np.degrees(np.arccos(beam @ -VIEWS[v][0])))
              for v in VIEWS}
    moved = sorted(VIEWS, key=lambda v: -abs(change[v]))[:2]
    print(f"""
  The ratio moves most seen {moved[0]} ({100 * change[moved[0]]:+.0f} percent) and {moved[1]}
  ({100 * change[moved[1]]:+.0f} percent). Those are the two directions in which the water
  behind the sphere sends the eye light turned back from the sunbeam: by
  {turned[moved[0]]:.0f} and {turned[moved[1]]:.0f} degrees for light scattered once, against {turned[min(turned, key=turned.get)]:.0f} and {sorted(turned.values())[1]:.0f}
  for the other two. Backscattered light is the part the Jerlov type says
  least about (radiance_distribution.py, part 5).""")

    # ----------------------------------------------------------------------
    rule("5. An overcast sky")

    sky = light_field(near, sun_zenith=None)
    sky_white = on_grid(sky["ed"][:, 1])[0] * daylight / np.pi
    sky_linear = linear_srgb(sky_white)
    seen_sky = look_at(sky, daylight, sky_linear)
    print("""The same spheres under a uniformly bright overcast in place of the sun,
with D65 still for its spectrum, white-balanced to a white face turned up
under it.""")
    print(f"\n  {'grey 50%':<12} {'sun':>8} {'overcast':>9}   paints apart, sun / overcast")
    sky_grey, sky_spread = {}, {}
    for view in VIEWS:
        sky_grey[view] = seen_sky[view, "grey 50%"]["ratio"]
        ratios = [seen_sky[view, p]["ratio"] for p in PAINTS]
        sky_spread[view] = max(ratios) / min(ratios)
        print(f"  {view:<12} {grey[view]:>8.2f} {sky_grey[view]:>9.2f}"
              f"   {spread[view]:>6.2f} / {sky_spread[view]:.2f}")
    sides = ("towards sun", "sun behind")
    print(f"""
  Without the sun the two horizontal views come together: the grey sphere
  is {sky_grey[sides[0]]:.2f} and {sky_grey[sides[1]]:.2f} times the water, against {grey[sides[0]]:.2f} and {grey[sides[1]]:.2f} with
  the sun. Seen from above it is {sky_grey["from above"]:.1f} times the water, and from below
  {sky_grey["from below"]:.2f}: whether the sphere stands out bright or dark still depends
  on the direction it is seen from, sun or no sun.""")

    # ----------------------------------------------------------------------
    rule("6. Gloss")

    in_water = float(coat_reflectance(1.0))
    in_air_coat = float(coat_reflectance(1.0, outside=1.0))
    seen_gloss = look_at(field, daylight, to_linear, gloss=True)
    print(f"""A clear coat of refractive index {COAT} over the paint, reflecting like a
mirror by Fresnel's equations, and letting the rest through to the paint.
Looking straight at it, it reflects {100 * in_water:.2f} percent from water against {100 * in_air_coat:.1f}
percent from air: water and coat differ less in refractive index than
air and coat do. It reflects the scattered light from the direction it
mirrors, interpolated between the Monte Carlo's cells; the sun's own
mirror image is a point far smaller than a pixel, and is left out.""")
    print(f"\n  {'grey 50%':<12} {'matte':>8} {'gloss':>8}")
    glossed = {}
    for view in VIEWS:
        glossed[view] = seen_gloss[view, "grey 50%"]["ratio"] / grey[view] - 1
        print(f"  {view:<12} {grey[view]:>8.2f} "
              f"{seen_gloss[view, 'grey 50%']['ratio']:>8.2f}")
    most_gloss = max(glossed, key=lambda v: abs(glossed[v]))
    beam, _ = sunbeam()
    glint, glint_cos = {}, {}
    for view, (look, up, k_eye) in VIEWS.items():
        p = picture(field, look, up, k_eye, gloss=True)
        n = p["normals"][np.argmax(p["gloss"].sum(axis=1))]
        glint_cos[view] = float(n @ -look)
        mirrored = -look - 2 * (n @ -look) * n
        glint[view] = float(np.degrees(np.arccos(np.clip(mirrored @ beam,
                                                         -1, 1))))
    print(f"""
  The coat changes the grey sphere's mean luminance by at most {100 * abs(glossed[most_gloss]):.1f} percent,
  seen {most_gloss}, and by {100 * min(abs(g) for g in glossed.values()):.1f} to {100 * sorted(abs(g) for g in glossed.values())[-2]:.1f} percent from the other three
  directions. Where the coat is brightest, from every direction, it
  mirrors light travelling within {max(glint.values()):.0f} degrees of the sunbeam: the forward
  peak of the scattering round the beam. Seen from below that falls near
  the rim, where the coat is seen at a slant and reflects most.""")

    # ----------------------------------------------------------------------
    rule("7. The sphere's shadow")

    seen_shadow = look_at(field, daylight, to_linear, shadow=True)
    print(f"""A sphere {2 * RADIUS:g} m across keeps the sunbeam from a column of water behind
it, along the beam. Light the beam would have scattered once towards the
eye from inside that column is taken away, from the water in front of the
sphere and from the water seen past it; light scattered more than once
still fills the column, and is left as it was.""")
    print(f"\n  {'grey 50%':<12} {'sphere':>8} {'darkest water':>14}")
    shade, darkest_water = {}, {}
    for view in VIEWS:
        g = seen_shadow[view, "grey 50%"]
        shade[view] = g["ratio"] / grey[view] - 1
        darkest_water[view] = 1 - g["darkest"]
        print(f"  {view:<12} {100 * shade[view]:>+7.1f}% {-100 * darkest_water[view]:>+13.1f}%")
    deepest = max(darkest_water, key=darkest_water.get)
    print(f"""
  From none of the four directions does the shadow show: the water in it
  is at most {100 * darkest_water[deepest]:.1f} percent darker than the water out of it, seen
  {deepest}, and the sphere's luminance changes by at most
  {100 * max(abs(v) for v in shade.values()):.1f} percent. None of them looks along the beam, where the water
  scatters most of the sunlight it scatters; across the beam, a column
  {2 * RADIUS:g} m wide holds too little of the light that reaches the eye.""")

    if png:
        _, _, cover = disc()
        blocks = []
        for light_field_, linear, sun in ((field, to_linear, True),
                                          (sky, sky_linear, False)):
            full = look_at(light_field_, daylight, linear, gloss=True,
                           shadow=sun)
            for paint in PAINTS:
                # in air: the paint lit by daylight and balanced to it, flat,
                # on a mid-grey card
                card = 0.18 * daylight
                flat = PAINTS[paint](WAVELENGTHS) * daylight
                row = [colour(cover[..., None] * flat
                              + (1 - cover[..., None]) * card, in_air)]
                row += [full[view, paint]["pixels"] for view in VIEWS]
                blocks.append(np.concatenate(row, axis=1))
        write_png(png, np.concatenate(blocks, axis=0))
        print(f"""
  Wrote {png}: the sun above, the overcast below, each with
  {", ".join(PAINTS)} down; across, in air, then {", ".join(VIEWS)}.
  The pictures include the gloss coat, and under the sun the shadow.
  Under the overcast the water overhead is brighter than the white it is
  balanced to, and is clipped to white.""")

    # ----------------------------------------------------------------------
    rule("Before you use any of this")
    fresh_less = 100 * (1 - jerlov.pure_water_scattering(
        500.0, salinity_psu=0.0) / jerlov.pure_water_scattering(
        500.0, salinity_psu=SALINITY_PSU))

    print(f"""  - The paint is a perfect diffuser, under a coat that reflects like a
    perfect mirror in part 6. Real paint and coats are rougher, and spread
    the sun's mirror image into a highlight this leaves out.
  - Pure water scatters as Morel's formula gives for a salinity of
    {SALINITY_PSU:g}, a choice of this script. At 0 it scatters {fresh_less:.0f} percent
    less.
  - The shadow (part 7) removes only light scattered once; the sphere also
    takes from the water the light it blocks, which is left in.
  - The radiance is the Monte Carlo's, binned in {D_ZENITH:g} by {D_AZIMUTH:g} degree cells, at
    {MC_WAVELENGTHS.size} wavelengths, from a flat surface and either a sun alone or a uniform
    overcast; a clear sky lies between. Everything radiance_distribution.py
    says before you use it applies here.
  - The phase function moves the result (part 4), and the station nearest
    in b is not a good guide to it (DECISIONS.md section 40).
  - The colours are what a camera white-balanced to a white face turned up
    would record, not what an eye adapted to the water would see; those
    outside the sRGB gamut are clipped, and the paints are stand-ins.

  Every one of these is a choice you can replace with a measurement.
""")
    return dict(near=near, other=other, agree=agree, faces=faces,
                counted=counted, seen=seen, seen_other=seen_other,
                grey=grey, brightest=brightest, darkest=darkest,
                spread=spread, change=change, moved=moved, turned=turned,
                field=field, sky_grey=sky_grey, sky_spread=sky_spread,
                in_water=in_water, in_air_coat=in_air_coat, glossed=glossed,
                most_gloss=most_gloss, glint=glint, glint_cos=glint_cos, shade=shade,
                darkest_water=darkest_water, deepest=deepest,
                daylight=daylight, white=white, to_linear=to_linear)


if __name__ == "__main__":
    png = None
    if "--png" in sys.argv:
        png = sys.argv[sys.argv.index("--png") + 1]
    main(png)

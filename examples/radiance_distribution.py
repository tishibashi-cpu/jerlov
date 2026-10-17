"""The light arriving from each direction under water, by Monte Carlo.

For work that needs more of the light field than the irradiance: the
radiance distribution at depth, the mean cosine and the ratio of scalar to
planar irradiance, upwelling against downwelling light. The package itself
does not solve the radiative transfer equation (DECISIONS.md sections 12
and 38). This example does, in about 150 lines of NumPy, from the
coefficients the package carries:

    a and b         jerlov.water("II"), Williamson & Hollins (2022)
    particle phase  jerlov.petzold_scattering, Petzold (1972), 530 nm
    water phase     jerlov.pure_water_vsf, Morel's formula (Boss & Pegau)
    checked against jerlov.water("II", source="jerlov1976").kd

    python examples/radiance_distribution.py      # about half a minute

The method. Photons enter through a flat surface, refracted and thinned
by Fresnel transmission. Each travels a free path drawn from exp(-c s),
and at its end is scattered, never absorbed: instead its weight is
multiplied by b / c. Scattering is by water or by particles in proportion
to their share of b, at an angle drawn from that one's phase function and
an azimuth drawn uniformly. Light reaching the surface from below is
reflected back by the Fresnel reflectance and the rest leaves. A photon
whose weight falls below 1e-4 survives with probability 1/10 and ten times
the weight. Radiance and scalar irradiance at a depth are the path length
photons spend in a 1 m slab around it, per unit thickness; planar
irradiance is the weight crossing the depth.

Nothing here has been compared with a measured radiance distribution.
"""

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
WATER_TYPE = "II"
WAVELENGTHS = (450.0, 500.0, 550.0)
DEPTHS = np.array([2.0, 5.0, 10.0, 20.0])
SUN_ZENITH = 40.0           # degrees, in air
D_ZENITH, D_AZIMUTH = 10.0, 45.0
PHOTONS, BATCHES = 50_000, 4


# -- the coefficients --------------------------------------------------------

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


def water_phase(wavelength):
    grid = np.linspace(0.0, 180.0, 1801)
    cdf, cos_angle, _ = inverse_cdf(grid,
                                    jerlov.pure_water_vsf(grid, wavelength))
    return dict(cdf=cdf, cos=cos_angle)


def coefficients(water_type, wavelength):
    w = jerlov.water(water_type)
    return (float(w.a(wavelength)), float(w.b(wavelength)),
            float(jerlov.pure_water_scattering(wavelength)))


# -- the photons -------------------------------------------------------------

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
    pole = perp < 1e-6
    nx = np.where(pole, sin_t * cp,
                  sin_t * (ux * uz * cp - uy * sp) / perp + ux * cos_t)
    ny = np.where(pole, sin_t * sp,
                  sin_t * (uy * uz * cp + ux * sp) / perp + uy * cos_t)
    nz = np.where(pole, np.sign(uz) * cos_t, -sin_t * cp * perp + uz * cos_t)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    return nx / norm, ny / norm, nz / norm


def simulate(a, b, bw, particles, water, sun_zenith, seed,
             photons=PHOTONS, depths=DEPTHS, half_slab=0.5):
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
    weight = 1 - fresnel(mu_air, 1.0, N_WATER)
    sin_w = np.sqrt(1 - mu_air ** 2) / N_WATER
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
        weight[up] *= fresnel(uz[up], N_WATER, 1.0)
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


def light_field(water_type, wavelength, particles, sun_zenith):
    """Several batches; their mean, and the spread of the batch means."""
    a, b, bw = coefficients(water_type, wavelength)
    batches = [simulate(a, b, bw, particles, water_phase(wavelength),
                        sun_zenith, seed=seed) for seed in range(BATCHES)]
    out = {key: np.mean([r[key] for r in batches], axis=0)
           for key in batches[0]}
    kd = [np.log(r["ed"][0] / r["ed"][2]) / (DEPTHS[2] - DEPTHS[0])
          for r in batches]
    out.update(kd=float(np.mean(kd)),
               kd_se=float(np.std(kd, ddof=1) / np.sqrt(BATCHES)),
               a=a, b=b, bw=bw)
    return out


# --------------------------------------------------------------------------
def main():
    _banner()

    # ----------------------------------------------------------------------
    rule("1. What goes in")

    w = jerlov.water(WATER_TYPE)
    b530 = float(w.b(530.0))
    STATION = min(jerlov.PETZOLD_STATIONS,
                  key=lambda s: abs(jerlov.petzold_scattering(s).b - b530))
    OTHER = sorted(jerlov.PETZOLD_STATIONS,
                   key=lambda s: abs(jerlov.petzold_scattering(s).b - b530))[1]
    PARTICLES = {s: particle_phase(s) for s in (STATION, OTHER)}
    p = PARTICLES[STATION]
    print(f"""Jerlov {WATER_TYPE} has b = {b530:.3f} 1/m at 530 nm, the wavelength of
Petzold's scattering meters. Of his eight stations, {STATION} is nearest, at
{p["b"]:.3f} 1/m, so its phase function stands in for this water's
particles at every wavelength; {OTHER}, the next nearest, shows how much
that choice matters (part 5). His first measured angle is {p["first_deg"]:.3g} degree;
the {100 * p["straight"]:.0f} percent of the particles' scattering below it is taken to go
straight on.""")
    print(f"\n  {'nm':>5} {'a':>7} {'b':>7} {'water/b':>8} {'b/c':>6}")
    for wl in WAVELENGTHS:
        a, b, bw = coefficients(WATER_TYPE, wl)
        print(f"  {wl:>5.0f} {a:>7.4f} {b:>7.4f} {bw / b:>8.1%} {b / (a + b):>6.2f}")

    fields = {(wl, light): light_field(WATER_TYPE, wl, p, light)
              for wl in WAVELENGTHS for light in (SUN_ZENITH, None)}

    # ----------------------------------------------------------------------
    rule("2. A check that needs no measurement")

    print("""Energy is conserved, so the net downward irradiance can only fall by
what is absorbed: a = -d(Ed - Eu)/dz / E0 (Gershun's law). The model never
uses this; recovering a from its own output tests the bookkeeping.""")
    print(f"\n  {'nm':>5} {'light':>9} {'a given':>8} {'a found':>8}")
    gershun = []
    for (wl, light), f in fields.items():
        net = f["ed"] - f["eu"]
        k5, k10 = 1, 2
        found = -(net[k10] - net[k5]) / (DEPTHS[k10] - DEPTHS[k5]) \
            / (0.5 * (f["e0"][k5] + f["e0"][k10]))
        gershun.append(found / f["a"] - 1)
        name = "overcast" if light is None else f"sun {light:g}"
        print(f"  {wl:>5.0f} {name:>9} {f['a']:>8.4f} {found:>8.4f}")
    print(f"""
  Between 5 and 10 m the recovered a is within {100 * max(abs(g) for g in gershun):.1f} percent of the
  a put in, in every case.""")

    # ----------------------------------------------------------------------
    rule("3. Against Jerlov's Kd")

    print(f"""Kd of the downwelling irradiance between {DEPTHS[0]:g} and {DEPTHS[2]:g} m, against
Jerlov's (1976) Kd for {WATER_TYPE}. The spread is over {BATCHES} batches of {PHOTONS:,} photons.""")
    kd76 = jerlov.water(WATER_TYPE, source="jerlov1976")
    print(f"\n  {'nm':>5} {'sun':>15} {'overcast':>15} {'Jerlov 1976':>12}")
    ratio = {}
    for wl in WAVELENGTHS:
        sun, sky = fields[wl, SUN_ZENITH], fields[wl, None]
        ref = float(kd76.kd(wl))
        ratio[wl] = (sun["kd"] / ref, sky["kd"] / ref)
        print(f"  {wl:>5.0f} {sun['kd']:>8.4f}+-{sun['kd_se']:.4f} "
              f"{sky['kd']:>8.4f}+-{sky['kd_se']:.4f} {ref:>12.4f}")
    worst = max(WAVELENGTHS, key=lambda wl: abs(ratio[wl][0] - 1))
    print(f"""
  At {" and ".join(f"{wl:g}" for wl in WAVELENGTHS if wl != worst)} nm the computed Kd is within {100 * max(abs(r - 1) for wl in WAVELENGTHS if wl != worst for r in ratio[wl]):.0f} percent of Jerlov's; at
  {worst:g} nm it is {100 * (min(ratio[worst]) - 1):.0f} to {100 * (max(ratio[worst]) - 1):.0f} percent above it. The a and b are Williamson &
  Hollins's, not Jerlov's own, so this compares two sources as much as it
  checks the model. Under an overcast sky Kd is larger at every wavelength
  here: its light enters at slanting angles, and its mean cosine stays
  lower (part 5).""")

    # ----------------------------------------------------------------------
    rule("4. Where the light comes from")

    wl = 500.0
    sun = fields[wl, SUN_ZENITH]
    refracted = np.degrees(np.arcsin(np.sin(np.radians(SUN_ZENITH)) / N_WATER))
    print(f"""Radiance at {wl:g} nm, sun at {SUN_ZENITH:g} degrees from the zenith ({refracted:.1f} in the
water), in the vertical plane through the sun, relative to the radiance
from straight overhead. The unscattered sunbeam is left out: it is one
direction, carrying the share of Ed in the last row.""")
    views = (5, 25, 45, 85, 135, 175)
    print("\n  looking " + "".join(f"{v:>7}°" for v in views)
          + "   (0 = up, 180 = down)")
    for k, depth in enumerate(DEPTHS):
        overhead = sun["radiance"][k, 0, :].mean()
        # Looking towards the sun one sees light travelling away from it,
        # at azimuth 0; looking away, light travelling towards it.
        for col, label in ((0, "to sun"), (-1, "away")):
            cells = [sun["radiance"][k, int(v // D_ZENITH), col] / overhead
                     for v in views]
            print(f"  {depth:>4.0f} m {label:>6}"
                  + "".join(f"{x:>8.3g}" for x in cells))
    a, b, _ = coefficients(WATER_TYPE, wl)
    mu_w = np.cos(np.radians(refracted))
    direct = ((1 - fresnel(np.array([np.cos(np.radians(SUN_ZENITH))]),
                           1.0, N_WATER)[0])
              * np.exp(-(a + b) * DEPTHS / mu_w))
    print("\n  direct share of Ed "
          + "".join(f"{d:>5.0f} m {x / e:>5.0%}"
                    for d, x, e in zip(DEPTHS, direct, sun["ed"])))
    sun_cell = int(refracted // D_ZENITH)
    peak = [sun["radiance"][k, sun_cell, 0] / sun["radiance"][k, 0, :].mean()
            for k in range(DEPTHS.size)]
    down = [sun["radiance"][k, -1, :].mean() / sun["radiance"][k, 0, :].mean()
            for k in range(DEPTHS.size)]
    print(f"""
  The brightest scattered light is in the cell around the sunbeam's own
  direction, {peak[0]:.0f} times overhead at {DEPTHS[0]:g} m and {peak[-1]:.0f} times at {DEPTHS[-1]:g} m: the forward
  peak of the phase function keeps it close to the beam, and the beam
  itself fades. Looking straight down, the radiance falls from {down[0]:.0%} of
  overhead at {DEPTHS[0]:g} m to {down[-1]:.1%} at {DEPTHS[-1]:g} m. With depth less of Ed comes straight
  from the sun.""")

    # ----------------------------------------------------------------------
    rule("5. The numbers a planar sensor does not give")

    print(f"""The mean cosine is (Ed - Eu) / E0, and E0 / Ed is the factor by which
scalar irradiance, what a spherical sensor reads, exceeds planar. At
{wl:g} nm, and with the next nearest station, {OTHER}, for the particles:""")
    other = light_field(WATER_TYPE, wl, PARTICLES[OTHER], SUN_ZENITH)
    print(f"\n  {'':>22}" + "".join(f"{d:>7.0f} m" for d in DEPTHS))
    rows = (("mean cosine, sun", sun, "mu"),
            ("mean cosine, overcast", fields[wl, None], "mu"),
            (f"mean cosine, {OTHER}", other, "mu"),
            ("E0 / Ed, sun", sun, "ratio"),
            ("E0 / Ed, overcast", fields[wl, None], "ratio"),
            ("Eu / Ed, sun", sun, "R"),
            (f"Eu / Ed, {OTHER}", other, "R"))
    for label, f, what in rows:
        values = {"mu": (f["ed"] - f["eu"]) / f["e0"],
                  "ratio": f["e0"] / f["ed"], "R": f["eu"] / f["ed"]}[what]
        print(f"  {label:>22}" + "".join(f"{v:>9.3f}" for v in values))
    r_sun, r_other = sun["eu"][2] / sun["ed"][2], other["eu"][2] / other["ed"][2]
    print(f"""
  E0 / Ed is {(sun["e0"] / sun["ed"]).min():.2f} to {(fields[wl, None]["e0"] / fields[wl, None]["ed"]).max():.2f} here: the factor `par_profile` says it cannot
  supply, for these two skies, this water and this phase function. Swap
  the phase function for {OTHER}'s and Eu / Ed at {DEPTHS[2]:g} m changes by
  {100 * (r_other / r_sun - 1):+.0f} percent: the backscattered light is the part the Jerlov type
  says least about.""")

    # ----------------------------------------------------------------------
    rule("Before you use any of this")

    print(f"""  - The water is the same at every depth and has no bottom; its a and b
    are Williamson & Hollins's for {WATER_TYPE}, and the phase function is
    measured at one place and one wavelength, 530 nm, and used at all.
  - Scattering below Petzold's first measured angle goes straight on.
  - The surface is flat, with a refractive index of {N_WATER}. Waves focus and
    spread the sunbeam, and roughen the radiance near the surface.
  - The sky is either a sun alone or a uniformly bright overcast. A clear
    sky lies between, in proportions this package does not determine.
  - No inelastic scattering, no polarisation. Radiance is binned in
    {D_ZENITH:g} by {D_AZIMUTH:g} degree cells and averaged over 1 m of depth; cells near
    straight down carry few photons and the most noise.

  Every one of these is a choice you can replace with a measurement.
""")
    return dict(station=STATION, other=OTHER, straight=p["straight"],
                gershun=gershun, kd_ratio=ratio, fields=fields,
                other_field=other, peak=peak, down=down,
                direct_share=direct / sun["ed"])


if __name__ == "__main__":
    main()

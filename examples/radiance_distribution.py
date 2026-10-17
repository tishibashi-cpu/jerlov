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
    and against jerlov.tyler1958_radiance, Tyler (1958), measured in a lake

    python examples/radiance_distribution.py      # about a minute

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

Part 6 compares the model with the radiance Tyler measured in Lake Pend
Oreille, with every choice made before the model was run (DECISIONS.md
section 39).
"""

from types import SimpleNamespace

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


def water_phase(wavelength, salinity=37.0):
    grid = np.linspace(0.0, 180.0, 1801)
    cdf, cos_angle, _ = inverse_cdf(
        grid, jerlov.pure_water_vsf(grid, wavelength, salinity))
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


# -- Tyler's lake -----------------------------------------------------------

LAKE_DEPTHS = (41.3, 53.7, 66.1)    # his three deepest tables
LAKE_N = 1.333              # fresh water against air, in the visible
LAKE_WAVELENGTH = 488.0     # the middle of his band, 430 to 546 nm
LAKE_PHOTONS = 100_000
VIEWS = (5, 25, 45, 65, 85)


def trapezoid(y, x):
    """The trapezoid rule along the last axis."""
    return np.sum(0.5 * (y[..., 1:] + y[..., :-1]) * np.diff(x), axis=-1)


def measured_irradiances(table):
    """Ed, Eu and E0 from one of Tyler's tables, by the trapezoid rule over
    his grid, the other side of the sun's plane mirroring this one."""
    tilt = np.radians(table.tilt_deg)
    ring = (2 * trapezoid(table.radiance, np.radians(table.azimuth_deg))
            * np.sin(tilt))
    flux = ring * np.cos(tilt)
    down, up = tilt <= np.pi / 2, tilt >= np.pi / 2
    return dict(ed=trapezoid(flux[down], tilt[down]),
                eu=-trapezoid(flux[up], tilt[up]),
                e0=trapezoid(ring, tilt))


def measured_cells(table):
    """Tyler's radiance averaged over each of the model's cells, his table
    interpolated linearly to every half degree."""
    fine = np.arange(0.25, 180.0, 0.5)
    by_tilt = np.array([np.interp(fine, table.tilt_deg, column)
                        for column in table.radiance.T]).T
    grid = np.array([np.interp(fine, table.azimuth_deg, row)
                     for row in by_tilt])
    n_th, n_ph = int(180 / D_ZENITH), int(180 / D_AZIMUTH)
    w = np.sin(np.radians(fine))
    total = (grid * w[:, None]).reshape(n_th, -1, n_ph, int(2 * D_AZIMUTH))
    return (total.sum(axis=(1, 3))
            / (w.reshape(n_th, -1).sum(axis=1)[:, None] * 2 * D_AZIMUTH))


def summary(runs, depths):
    """Mean cosine, Eu / Ed, E0 / Ed and Kd per batch: their means and the
    standard error of the means. The mean radiance, and the relative
    standard error of the radiance relative to overhead."""
    per = {"mu": [(r["ed"] - r["eu"]) / r["e0"] for r in runs],
           "R": [r["eu"] / r["ed"] for r in runs],
           "ratio": [r["e0"] / r["ed"] for r in runs],
           "kd": [np.log(r["ed"][:-1] / r["ed"][1:]) / np.diff(depths)
                  for r in runs]}
    out = {k: np.mean(v, axis=0) for k, v in per.items()}
    out.update({k + "_se": np.std(v, axis=0, ddof=1) / np.sqrt(len(runs))
                for k, v in per.items()})
    radiance = [r["radiance"] / r["radiance"][:, :1, :].mean(axis=2,
                                                           keepdims=True)
                for r in runs]
    out["radiance"] = np.mean([r["radiance"] for r in runs], axis=0)
    out["relative_se"] = (np.std(radiance, axis=0, ddof=1)
                          / np.sqrt(len(runs)) / np.mean(radiance, axis=0))
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
    rule("6. Against a measured radiance distribution")

    tables = {d: jerlov.tyler1958_radiance(d) for d in LAKE_DEPTHS}
    t = tables[LAKE_DEPTHS[0]]
    measured = {d: measured_irradiances(tables[d]) for d in LAKE_DEPTHS}
    found = []
    for z1, z2 in zip(LAKE_DEPTHS[:-1], LAKE_DEPTHS[1:]):
        net1 = measured[z1]["ed"] - measured[z1]["eu"]
        net2 = measured[z2]["ed"] - measured[z2]["eu"]
        mu = np.sqrt(net1 / measured[z1]["e0"] * net2 / measured[z2]["e0"])
        found.append(float(np.log(net1 / net2) / (z2 - z1) * mu))
    a_lake = float(np.mean(found))
    c_lake = t.beam_attenuation
    b_lake = c_lake - a_lake
    by_b = sorted(jerlov.PETZOLD_STATIONS,
                  key=lambda s: abs(jerlov.petzold_scattering(s).b - b_lake))
    near, second = by_b[:2]
    sun_zenith = 90.0 - t.sun_altitude_deg
    print(f"""Tyler (1958) measured the radiance from every direction at seven
depths in Lake Pend Oreille, Idaho, a deep lake in which he found no
definite sign of stratification, under a clear sky with the sun {t.sun_altitude_deg:g}
degrees high, in a band from {t.band_nm[0]:g} to {t.band_nm[1]:g} nm. Of the water he gives the
beam attenuation, c = {c_lake:.3f} 1/m at the surface, and not a, b or a phase
function. What the model is given, all fixed before it was run
(DECISIONS.md section 39):

  - a from the measurement, by Gershun's law: Ed, Eu and E0 integrated
    from his tables, and a = K of Ed - Eu times the mean cosine, between
    {LAKE_DEPTHS[0]:g} and {LAKE_DEPTHS[1]:g} m and between {LAKE_DEPTHS[1]:g} and {LAKE_DEPTHS[2]:g} m: {found[0]:.4f} and {found[1]:.4f} 1/m. Their
    mean, {a_lake:.4f}, and b = c - a = {b_lake:.4f} 1/m.
  - the phase function of the Petzold station whose b is nearest that,
    {near} ({jerlov.petzold_scattering(near).b:.3f} 1/m), and of the next nearest, {second} ({jerlov.petzold_scattering(second).b:.3f}).
  - the sun alone, {sun_zenith:.1f} degrees from the zenith, and a uniform overcast,
    taken to bracket a clear sky.
  - fresh water: a refractive index of {LAKE_N}, and pure water's scattering
    at salinity 0 and {LAKE_WAVELENGTH:g} nm, the middle of the band.
  - his three deepest tables only. The four above carry the glitter of the
    sun on the surface in its direction (DATA.md section 23).""")

    depths = np.array(LAKE_DEPTHS)
    bw = float(jerlov.pure_water_scattering(LAKE_WAVELENGTH, 0.0))
    fresh = water_phase(LAKE_WAVELENGTH, 0.0)
    lake = {}
    for station, light in ((near, sun_zenith), (near, None),
                           (second, sun_zenith)):
        phase = (PARTICLES[station] if station in PARTICLES
                 else particle_phase(station))
        runs = [simulate(a_lake, b_lake, bw, phase, fresh, light, seed=seed,
                         photons=LAKE_PHOTONS, depths=depths, n_water=LAKE_N)
                for seed in range(BATCHES)]
        lake[station, light] = summary(runs, depths)
    tyler = {"mu": [], "R": [], "ratio": []}
    for d in LAKE_DEPTHS:
        m = measured[d]
        tyler["mu"].append((m["ed"] - m["eu"]) / m["e0"])
        tyler["R"].append(m["eu"] / m["ed"])
        tyler["ratio"].append(m["e0"] / m["ed"])
    tyler = {k: np.array(v) for k, v in tyler.items()}
    uniform = measured_irradiances(SimpleNamespace(
        tilt_deg=t.tilt_deg, azimuth_deg=t.azimuth_deg,
        radiance=np.ones_like(t.radiance)))
    grid_error = max(abs(uniform["e0"] / (4 * np.pi) - 1),
                     abs(uniform["ed"] / np.pi - 1))
    tyler["kd"] = (np.log([measured[d]["ed"] for d in LAKE_DEPTHS[:-1]])
                   - np.log([measured[d]["ed"] for d in LAKE_DEPTHS[1:]])) \
        / np.diff(depths)

    def name(key):
        station, light = key
        return f"{station}, {'overcast' if light is None else 'sun'}"

    print(f"\n  {'':>26}" + "".join(f"{d:>7g} m" for d in LAKE_DEPTHS))
    for what, label in (("mu", "mean cosine"), ("R", "Eu / Ed"),
                        ("ratio", "E0 / Ed")):
        print(f"  {label + ', Tyler':>26}"
              + "".join(f"{v:>9.3f}" for v in tyler[what]))
        for key, f in lake.items():
            print(f"  {name(key):>26}"
                  + "".join(f"{v:>9.3f}" for v in f[what]))
    print(f"\n  {'Kd of Ed':>26}" + "".join(
        f"{f'{z1:g}-{z2:g} m':>12}"
        for z1, z2 in zip(LAKE_DEPTHS[:-1], LAKE_DEPTHS[1:])))
    print(f"  {'Tyler':>26}" + "".join(f"{v:>12.4f}" for v in tyler["kd"]))
    for key, f in lake.items():
        print(f"  {name(key):>26}" + "".join(f"{v:>12.4f}" for v in f["kd"]))
    noise = max(float(np.max(f[k + "_se"] / f[k])) for f in lake.values()
                for k in ("mu", "R", "ratio", "kd"))

    model = {k: np.concatenate([f[k] for f in lake.values()])
             for k in ("mu", "R", "ratio", "kd")}
    print(f"""
  The standard error of the model's figures, over {BATCHES} batches of {LAKE_PHOTONS:,}
  photons, is at most {100 * noise:.0f} percent. Its mean cosine is {model["mu"].min():.3f} to {model["mu"].max():.3f}, with
  either phase function and either sky; Tyler's is {tyler["mu"].min():.3f} to {tyler["mu"].max():.3f}. Its Eu / Ed
  is {model["R"].min():.4f} to {model["R"].max():.4f}, against {tyler["R"].min():.4f} to {tyler["R"].max():.4f}, and its E0 / Ed {model["ratio"].min():.2f} to {model["ratio"].max():.2f},
  against {tyler["ratio"].min():.2f} to {tyler["ratio"].max():.2f}. Kd is {model["kd"].min():.3f} to {model["kd"].max():.3f} 1/m, against {tyler["kd"][0]:.3f} and {tyler["kd"][1]:.3f}.
  The model obeys Gershun's law (part 2), and its a was taken from
  Tyler's light by the same law, so a mean cosine too high has to come
  with a K too low.""")

    print(f"""
Radiance in the plane of the sun, averaged over the model's cells,
relative to the cell overhead; Tyler's table is interpolated linearly
across each cell. {near}'s phase function.""")
    print("\n  looking " + "".join(f"{v:>7}°" for v in VIEWS))
    rows = {}
    for k, d in enumerate(LAKE_DEPTHS):
        cells = measured_cells(tables[d])
        for col, label in ((0, "to sun"), (-1, "away")):
            rows[d, label] = {}
            for who, field in (("Tyler", cells),
                               ("sun", lake[near, sun_zenith]["radiance"][k]),
                               ("overcast", lake[near, None]["radiance"][k])):
                values = np.array([field[int(v // D_ZENITH), col]
                                   / field[0, :].mean() for v in VIEWS])
                rows[d, label][who] = values
                print(f"  {f'{d:g} m' if (col, who) == (0, 'Tyler') else '':>6}"
                      f" {label if who == 'Tyler' else '':>6} {who:>8}"
                      + "".join(f"{x:>8.3g}" for x in values))
    between = [v for i, v in enumerate(VIEWS)
               if all(min(r["sun"][i], r["overcast"][i]) <= r["Tyler"][i]
                      <= max(r["sun"][i], r["overcast"][i])
                      for r in rows.values())]
    above = [i for i, v in enumerate(VIEWS)
             if all(r["Tyler"][i] > max(r["sun"][i], r["overcast"][i])
                    for r in rows.values())]
    side = np.array([[r["sun"][i], r["overcast"][i]] / r["Tyler"][i]
                     for r in rows.values() for i in above])
    cell_se = max(float(lake[near, light]["relative_se"][k][
        int(VIEWS[i] // D_ZENITH), col])
        for light in (sun_zenith, None) for k in range(len(LAKE_DEPTHS))
        for col in (0, -1) for i in above)
    print(f"""
  At {" and ".join(f"{v}" for v in between)} degrees from the zenith, at every depth and on both sides,
  Tyler's radiance lies between the two skies'. At {" and ".join(f"{VIEWS[i]}" for i in above)} it is above
  both, at every depth and on both sides: the model gives {side.min():.2f} to {side.max():.2f} of
  his there, relative to overhead, with a standard error of at most {100 * cell_se:.0f}
  percent. The model's light is gathered closer about the vertical than
  the light Tyler measured.

  What this does not settle is why. The model differs from the lake in
  ways none of which was varied here: one wavelength for a band {t.band_nm[1] - t.band_nm[0]:g} nm
  wide; phase functions measured in the sea at 530 nm, and straight on
  below Petzold's first angle; a c measured at the surface the next day,
  in a band the report does not give, which fell to {-np.log(0.686):.3f} 1/m at 61 m;
  a flat surface; and no sky but the two bracketing ones.""")

    # ----------------------------------------------------------------------
    rule("Before you use any of this")

    print(f"""  - The water is the same at every depth and has no bottom; its a and b
    are Williamson & Hollins's for {WATER_TYPE}, and the phase function is
    measured at one place and one wavelength, 530 nm, and used at all.
  - Scattering below Petzold's first measured angle goes straight on.
  - The surface is flat, with a refractive index of {N_WATER} ({LAKE_N} in the
    lake). Waves focus and spread the sunbeam, and roughen the radiance
    near the surface.
  - The sky is either a sun alone or a uniformly bright overcast. A clear
    sky lies between, in proportions this package does not determine.
  - Part 6 takes the lake's a from Tyler's own light, by the law part 2
    checks, so it is not an independent check of a; its c is the surface
    value measured the day after. His tables are integrated on their own
    10 by 20 degree grid, which gets a uniform radiance's E0 and Ed right
    to within {100 * grid_error:.1f} percent.
  - No inelastic scattering, no polarisation. Radiance is binned in
    {D_ZENITH:g} by {D_AZIMUTH:g} degree cells and averaged over 1 m of depth; cells near
    straight down carry few photons and the most noise.

  Every one of these is a choice you can replace with a measurement.
""")
    return dict(station=STATION, other=OTHER, straight=p["straight"],
                gershun=gershun, kd_ratio=ratio, fields=fields,
                other_field=other, peak=peak, down=down,
                direct_share=direct / sun["ed"],
                lake=dict(found=found, a=a_lake, b=b_lake, near=near,
                          second=second, sun_zenith=sun_zenith, tyler=tyler,
                          fields=lake, rows=rows, between=between,
                          above=[VIEWS[i] for i in above], side=side,
                          cell_se=cell_se, noise=noise,
                          grid_error=grid_error))


if __name__ == "__main__":
    main()

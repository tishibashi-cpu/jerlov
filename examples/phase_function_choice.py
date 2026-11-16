"""What a Henyey-Greenstein phase function does to the light scattered in
the sea, against Petzold's measurements.

For people who simulate light in water, in a renderer or a model of their
own, and must pick a phase function:

    python examples/phase_function_choice.py

Most renderers offer one phase function, Henyey-Greenstein, with one
parameter g. `henyey_greenstein_fit` chooses g for each of Petzold's eight
measured waters, to match either the measured backscattering or the mean
cosine. This shows what each choice does to two things a viewer sees: the
light scattered towards the eye from the sun's beam, by the angle between
them, and the glow around the sun, the share of scattered light within a
few degrees of the forward direction (DECISIONS.md section 83). Part 3
asks what rests on the report's power-law extension below 0.1 degree,
which nobody measured: the mean cosine, the backscatter ratio and g, from
the package, and Kd, from Monte Carlo runs kept in
examples/data/below_0_1/ (DECISIONS.md section 96).
"""

import csv
import pathlib
import warnings

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


#: Scattering angles shown, degrees. The measurement starts at 0.1; below
#: 0.169 at the Bahamas and Catalina stations it is the report's extension,
#: so the smallest shown is 0.5.
ANGLES_DEG = (0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0)
#: Cone half-angles for the glow around the sun, degrees.
CONES_DEG = (1.0, 10.0, 90.0)
#: The sun 40 degrees from the zenith in air, refracted into sea water of
#: refractive index 1.34: the angles of the views in part 1 follow.
SUN_IN_AIR_DEG = 40.0
N_WATER = 1.34
METHODS = ("backscatter_ratio", "mean_cosine")


def hg(g, angle_deg):
    mu = np.cos(np.radians(angle_deg))
    return (1 - g * g) / (4 * np.pi * (1 + g * g - 2 * g * mu) ** 1.5)


def hg_share_within(g, angle_deg):
    """The share of an HG phase function within ``angle_deg`` of forward,
    its closed-form cumulative distribution."""
    mu = np.cos(np.radians(angle_deg))
    return (1 - g * g) / (2 * g) * (1 / (1 - g)
                                    - 1 / np.sqrt(1 + g * g - 2 * g * mu))


def measured_share_within(f, angle_deg):
    """The share of the station's scattering within ``angle_deg`` of
    forward: the vsf integrated over solid angle between the printed
    angles as a power law, as the package interpolates it, plus the
    report's share below 0.1 degree, all over the printed b."""
    angles, vsf = np.asarray(f.angles_deg), np.asarray(f.vsf)
    total = f.fraction_below_0_1_deg
    for i in range(angles.size - 1):
        lo, hi = angles[i], min(angles[i + 1], angle_deg)
        if lo >= angle_deg:
            break
        theta = np.linspace(lo, hi, 257)
        beta = np.exp(np.interp(np.log(theta), np.log(angles), np.log(vsf)))
        rad = np.radians(theta)
        y = beta * np.sin(rad)
        total += 2 * np.pi * float(np.sum((y[1:] + y[:-1]) / 2
                                          * np.diff(rad))) / f.b
    return total


def fits(caught):
    out = {}
    for station in jerlov.PETZOLD_STATIONS:
        f = jerlov.petzold_scattering(station)
        with warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter("always", jerlov.ProvenanceWarning)
            fitted = {m: jerlov.henyey_greenstein_fit(f, method=m)
                      for m in METHODS}
        caught.update(f"{w.category.__name__}: {str(w.message).split(',')[0]}"
                      for w in seen)
        out[station] = (f, fitted)
    return out


def views():
    """Scattering angles of four lines of sight, with the sun refracted."""
    sun_w = np.degrees(np.arcsin(np.sin(np.radians(SUN_IN_AIR_DEG))
                                 / N_WATER))
    return sun_w, {
        "at the sun": 0.0,
        "level, facing the sun": 90.0 - sun_w,
        "level, back to the sun": 90.0 + sun_w,
        "straight down": 180.0 - sun_w,
    }


def ratio_part(stations, caught):
    rule("1. Light scattered towards the eye, HG against measured")
    sun_w, lines = views()
    print(f"""The single-scattered radiance from the sun's beam along a line of sight
is proportional to the phase function at the angle between the two. Each
cell is HG / measured at that angle: above 1, HG sends too much light
that way; below 1, too little. g matched to B/S, then to the mean cosine.
With the sun {SUN_IN_AIR_DEG:g} degrees from the zenith in air ({sun_w:.1f} in the water), the
angle is""")
    for k, v in lines.items():
        print(f"  {v:5.0f} degrees looking {k}")
    print()
    head = "".join(f"{a:>8g}" for a in ANGLES_DEG)
    print(f"  {'station':<10}{'g by':>5}{head}")
    ratios = {}
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always", jerlov.ProvenanceWarning)
        for station, (f, fitted) in stations.items():
            measured = np.asarray(f.vsf_at(list(ANGLES_DEG))) / f.b
            for method, label in zip(METHODS, ("B/S", "cos")):
                r = hg(fitted[method].g, np.array(ANGLES_DEG)) / measured
                ratios[(station, method)] = r
                print(f"  {station if label == 'B/S' else '':<10}{label:>5}"
                      + "".join(f"{v:>8.2f}" for v in r))
    caught.update(f"{w.category.__name__}: {str(w.message).split(':')[0]}"
                  for w in seen)
    small = [ratios[k][ANGLES_DEG.index(1.0)] for k in ratios]
    side = [ratios[k][ANGLES_DEG.index(90.0)] for k in ratios]
    back = [ratios[(s, "backscatter_ratio")][-1] for s in stations]
    print(f"""
Within a degree of the beam HG gives {min(small):.2f} to {max(small):.2f} of the measured light,
at 90 degrees {min(side):.2f} to {max(side):.2f} times it, and straight back, matched to B/S,
{min(back):.2f} to {max(back):.2f} times. Matching B/S makes the backward hemisphere right on
average, not at each angle.""")
    return ratios, small, side, back


def glow_part(stations):
    rule("2. The glow around the sun: the share of scattered light near forward")
    head = "".join(f"{f'<{c:g} deg':>10}" for c in CONES_DEG)
    print("""Measured (with the report's extension below 0.1 degree), and HG with g
matched each way.
""")
    print(f"  {'station':<10}{'':>9}{head}")
    shares = {}
    for station, (f, fitted) in stations.items():
        measured = [measured_share_within(f, c) for c in CONES_DEG]
        rows = [("measured", measured)] + [
            (f"HG {lab}", [float(hg_share_within(fitted[m].g, c))
                           for c in CONES_DEG])
            for m, lab in zip(METHODS, ("B/S", "cos"))]
        shares[station] = dict(rows)
        for k, (label, values) in enumerate(rows):
            print(f"  {station if k == 0 else '':<10}{label:>9}"
                  + "".join(f"{v:>10.3f}" for v in values))
    within1 = [(shares[s]["measured"][0], shares[s]["HG B/S"][0],
                shares[s]["HG cos"][0]) for s in stations]
    print(f"""
Within 1 degree of forward the stations scatter {min(m for m, _, _ in within1):.2f} to {max(m for m, _, _ in within1):.2f} of their light;
HG puts {min(b for _, b, _ in within1):.3f} to {max(b for _, b, _ in within1):.3f} there matched to B/S and {min(c for _, _, c in within1):.3f} to {max(c for _, _, c in within1):.3f} matched to the
mean cosine. Within 90 degrees the measured share and HG's matched to
B/S agree to {max(abs(shares[s]["HG B/S"][2] - shares[s]["measured"][2]) for s in stations):.3f}; so HG moves the
light of the tight glow around the sun out to between 1 and 90 degrees,
a wider and fainter glow.""")
    return shares, within1


DATA = pathlib.Path(__file__).resolve().parent / "data" / "below_0_1"


def hg_backscatter(g):
    """The share of an HG phase function beyond 90 degrees."""
    return (1 - g) / (2 * g) * ((1 + g) / np.sqrt(1 + g * g) - 1)


def hg_g_for_backscatter(ratio):
    """The HG g whose backscatter share is ``ratio``, by bisection (the
    share falls as g rises)."""
    lo, hi = 1e-6, 1 - 1e-9
    for _ in range(200):
        mid = (lo + hi) / 2
        if hg_backscatter(mid) > ratio:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def extension_part(stations):
    rule("3. What rests on the extension below 0.1 degree")
    rows = {}
    for station, (f, fitted) in stations.items():
        share = f.fraction_below_0_1_deg
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
            g = f.mean_cosine()
        b_s = fitted["backscatter_ratio"].measured_backscatter_ratio
        rows[station] = dict(
            share=share, g=(g, (g - share) / (1 - share)),
            bs=(b_s, b_s / (1 - share)),
            hg_bs=(fitted["backscatter_ratio"].g,
                   hg_g_for_backscatter(b_s / (1 - share))))
    print("""Petzold's report extends each vsf below 0.1 degree by a power law and
counts it in b. Without it, the phase function starts at 0.1 degree and b
is b (1 - f), f the share below. The mean cosine (which is also the HG g of
the mean_cosine fit) and B/S, and the HG g of the backscatter fit, with and
without it:

  Station     f      mean cosine        B/S              HG g (B/S)""")
    for station, r in rows.items():
        print(f"  {station:<9}{100 * r['share']:5.1f}%  "
              f"{r['g'][0]:.3f} -> {r['g'][1]:.3f}  "
              f"{r['bs'][0]:.4f} -> {r['bs'][1]:.4f}  "
              f"{r['hg_bs'][0]:.3f} -> {r['hg_bs'][1]:.3f}")
    kd = {}
    if (DATA / "runs.csv").exists():
        with open(DATA / "runs.csv") as handle:
            for r in csv.DictReader(handle):
                kd.setdefault((r["station"], r["b_over_a"]), {})[
                    r["variant"]] = float(r["kd_first_penetration_depth"])
    if not kd:
        print("\n(The Monte Carlo runs are in the repository, "
              "examples/data/below_0_1/; not found here.)")
        return dict(rows=rows, kd=None)
    unscattered = [v["unscattered"] / v["as_shipped"] - 1 for v in kd.values()]
    spread = [v["spread"] / v["as_shipped"] - 1 for v in kd.values()]
    dg = [r["g"][1] - r["g"][0] for r in rows.values()]
    dbs = [r["bs"][1] / r["bs"][0] - 1 for r in rows.values()]
    dhg = [r["hg_bs"][1] - r["hg_bs"][0] for r in rows.values()]
    print(f"""
Without the extension the mean cosine falls by {-max(dg):.3f} to {-min(dg):.3f}, B/S rises by
{100 * min(dbs):.1f} to {100 * max(dbs):.1f} percent and the HG g of the backscatter fit falls by {-max(dhg):.3f} to {-min(dhg):.3f}. By Monte Carlo ({len(kd)} cases: each station, b/a of 0.5 to 10, the sun at 30
degrees), treating the light scattered by less than 0.1 degree as not
scattered at all moves Kd by {100 * min(unscattered):+.2f} to {100 * max(unscattered):+.2f} percent: light turned by
so little goes on as if unscattered. Spreading it over 0.1 to 180
degrees instead, b kept, moves Kd by {100 * min(spread):+.2f} to {100 * max(spread):+.2f} percent. So Kd does not
rest on the extension, and the mean cosine and g move by at most
{max(-min(dg), -min(dhg)):.3f}; what the extension does decide is how much of b is counted
as scattering at all, and with it B/S.""")
    return dict(rows=rows, kd=kd, unscattered=(min(unscattered),
                                               max(unscattered)),
                spread=(min(spread), max(spread)), dg=(min(dg), max(dg)),
                dbs=(min(dbs), max(dbs)), dhg=(min(dhg), max(dhg)))


def main():
    _banner()
    caught = set()
    stations = fits(caught)
    ratios, small, side, back = ratio_part(stations, caught)
    shares, within1 = glow_part(stations)
    extension = extension_part(stations)
    if caught:
        rule("Warnings")
        print("Raised along the way, and caught by type:")
        for message in sorted(caught):
            print(f"  - {message}")

    rule("Before you use any of this")
    print("""  - Petzold's eight waters, at 530 nm, total of water and particles,
    on particular days in 1971: not Jerlov types, and one g serves every
    wavelength in a renderer.
  - The measured shares and the mean cosine count the report's power-law
    extension below 0.1 degree, 3 to 15 percent of the scattering, which
    nobody measured; the warnings above say so.
  - Single scattering of a sun's beam only; light scattered more than
    once is not followed here.
  - The sun's position and the water's refractive index are this
    example's choices, stated at the top.
""")
    return dict(stations=stations, ratios=ratios, small=small, side=side,
                back=back, shares=shares, within1=within1,
                extension=extension, caught=caught)


if __name__ == "__main__":
    main()

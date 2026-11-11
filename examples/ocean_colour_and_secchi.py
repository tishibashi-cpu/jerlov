"""Kd without a water type, the colour of the sea from above, and the
Secchi depth.

For oceanographers and limnologists who have a chlorophyll concentration,
or a and bb, rather than a Jerlov type, or who want the Secchi depth a
water's optics imply:

    python examples/ocean_colour_and_secchi.py

It runs Lee et al.'s (2013) Kd model on Solonenko & Mobley's (2015) a and
b for four Jerlov types and checks it against the Kd Solonenko & Mobley
computed with Hydrolight from the same a and b; computes the remote
sensing reflectance and, from it, the Secchi depth by Lee et al.'s (2015)
model; sets that beside Poole & Atkins's (1929) rule; and finds the Jerlov
type nearest to Morel & Maritorena's (2001) Kd for a range of chlorophyll
concentrations (DECISIONS.md section 66).
"""

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


#: Solonenko & Mobley's wavelengths within the visible, where Lee et al.'s
#: (2015) model looks for the most transparent one.
WL = np.arange(400.0, 701.0, 25.0)
TYPES = ("IB", "II", "III", "1C")
SALINITY_PSU = 35.0
SUN_ZENITH_DEG = 30.0       # the angle Lee et al. (2015) used, p. 146
#: The particles' share of their scattering that goes backwards, bbp/bp.
#: 0.0183 is that of Petzold's average-particle phase function, which
#: Solonenko & Mobley used in Hydrolight; the others bracket it.
PETZOLD_RATIO = 0.0183
PARTICLE_RATIOS = (0.005, PETZOLD_RATIO, 0.03)
RRS_PAIRS = {"Gordon et al. (1988)": jerlov.GORDON1988_RRS_COEFFICIENTS,
             "Lee et al. (2002)": jerlov.LEE2002_RRS_COEFFICIENTS}
#: Poole & Atkins (1929), Table III: K times the Secchi depth, 14 times.
POOLE_RANGE = (1.32, 2.18)
CHLOROPHYLL = (0.03, 0.1, 0.3, 1.0, 3.0, 10.0)


def optics(water_type):
    """a, the particles' scattering, and pure sea water's backscattering."""
    water = jerlov.water(water_type, source="solonenko2015")
    a = water.a(WL)
    b_particles = water.b(WL) - jerlov.pure_water_scattering(
        WL, salinity_psu=SALINITY_PSU)
    bb_water = jerlov.pure_water_backscattering(WL, salinity_psu=SALINITY_PSU)
    return water, a, b_particles, bb_water


def expect_provenance(record, found):
    """Keep each ProvenanceWarning's message; let anything else through."""
    for w in record:
        if issubclass(w.category, jerlov.ProvenanceWarning):
            found.add(str(w.message))
        else:
            warnings.warn_explicit(w.message, w.category, w.filename,
                                   w.lineno)


def kd_part(caught):
    rule("1. Lee et al.'s Kd against Hydrolight, from the same a and b")
    print(f"""Solonenko & Mobley ran Hydrolight on their a and b with Petzold's
average-particle phase function, whose bbp/bp is {PETZOLD_RATIO}. Lee et al.'s (2013)
model, for a sun {SUN_ZENITH_DEG:g} degrees from the zenith, against that Kd and
against Jerlov's own (1976), {WL[0]:g}-{WL[-1]:g} nm; the largest departure of
the ratio from 1 at any wavelength, in percent:
""")
    print(f"  {'type':>5} {'bbp/bp':>7} {'vs Hydrolight':>14} {'vs Jerlov':>10}")
    worst = {}
    kd = {}
    for t in TYPES:
        water, a, bp, bbw = optics(t)
        hydrolight = water.kd_hydrolight(WL)
        jerlov_kd = jerlov.water(t, source="jerlov1976").kd(WL)
        for r in PARTICLE_RATIOS:
            bb = bbw + r * bp
            with warnings.catch_warnings(record=True) as record:
                warnings.simplefilter("always")
                k = jerlov.lee2013_kd(a, bb, bb_water=bbw,
                                      sun_zenith_deg=SUN_ZENITH_DEG)
            expect_provenance(record, caught)
            kd[t, r] = k
            off_h = np.max(np.abs(k / hydrolight - 1))
            off_j = np.max(np.abs(k / jerlov_kd - 1))
            worst[t, r] = off_h
            print(f"  {t:>5} {r:>7g} {100 * off_h:>13.0f}% {100 * off_j:>9.0f}%")
    petzold = max(worst[t, PETZOLD_RATIO] for t in TYPES)
    others = max(worst[t, r] for t in TYPES for r in PARTICLE_RATIOS
                 if r != PETZOLD_RATIO)
    print(f"""
With Hydrolight's own bbp/bp, {PETZOLD_RATIO}, Lee et al.'s Kd stays within
{100 * petzold:.0f} percent of Hydrolight's for every type and wavelength; with
{PARTICLE_RATIOS[0]} or {PARTICLE_RATIOS[-1]} it departs by up to {100 * others:.0f} percent. bb is not a property of
the type (DATA.md section 10): the agreement holds only for the bb that
Hydrolight was given.

The two are not quite the same quantity. Lee et al.'s Kd is the mean from
the surface down to 10 percent of the surface irradiance; Solonenko &
Mobley's is computed over the depths their Hydrolight runs covered.
Against Jerlov's Kd the comparison also carries whatever Solonenko &
Mobley's inversion of that Kd left behind.""")
    return worst, kd


def secchi_part(kd, caught):
    rule("2. The colour from above, and the Secchi depth")
    print("""The remote sensing reflectance from a and bb, by each pair of
coefficients, and the Secchi depth from it and Lee et al.'s Kd (eq. 33 of
Lee et al. 2015). Depth in m; the wavelength where Kd is smallest is
where the model reads the reflectance:
""")
    depths = {}
    tr = {}
    head = "".join(f" {r:>8g}" for r in PARTICLE_RATIOS)
    print(f"  {'type':>5} {'coefficients':<22}{head}   (bbp/bp)")
    for t in TYPES:
        _, a, bp, bbw = optics(t)
        for name, pair in RRS_PAIRS.items():
            row = []
            for r in PARTICLE_RATIOS:
                bb = bbw + r * bp
                rrs = jerlov.above_surface_rrs(
                    jerlov.subsurface_rrs(a, bb, coefficients=pair))
                with warnings.catch_warnings(record=True) as record:
                    warnings.simplefilter("always")
                    z = jerlov.lee2015_secchi_depth(WL, kd[t, r], rrs)
                expect_provenance(record, caught)
                i = int(np.argmin(kd[t, r]))
                depths[t, name, r] = z
                tr[t, name, r] = (WL[i], kd[t, r][i], rrs[i])
                row.append(z)
            print(f"  {t:>5} {name:<22}" + "".join(f" {z:>8.1f}" for z in row))
    variants = [(n, r) for n in RRS_PAIRS for r in PARTICLE_RATIOS]
    findings, depends = [], []
    for i, t1 in enumerate(TYPES):
        for t2 in TYPES[i + 1:]:
            deeper = [depths[t1, n, r] > depths[t2, n, r] for n, r in variants]
            if all(deeper):
                findings.append(f"{t1} deeper than {t2}")
            elif not any(deeper):
                findings.append(f"{t2} deeper than {t1}")
            else:
                depends.append(f"{t1} against {t2}")
    lo = min(depths.values())
    hi = max(depths.values())
    names = list(RRS_PAIRS)
    by_pair = max(abs(depths[t, names[0], r] / depths[t, names[1], r] - 1)
                  for t in TYPES for r in PARTICLE_RATIOS)
    by_ratio = max(max(depths[t, n, r] for r in PARTICLE_RATIOS)
                   / min(depths[t, n, r] for r in PARTICLE_RATIOS) - 1
                   for t in TYPES for n in names)
    print(f"""
Across all {len(variants)} variants (two pairs of coefficients, three bbp/bp):
  holds in every one:  {'; '.join(findings)}
  depends on them:     {'; '.join(depends) if depends else 'none'}
The depths run from {lo:.1f} to {hi:.1f} m. The two pairs of coefficients differ
by at most {100 * by_pair:.0f} percent in depth; across bbp/bp one type's depth varies by
up to a factor of {1 + by_ratio:.1f}. bb enters both terms of the model: the
reflectance, and Kd.""")
    return depths, tr, findings, depends, by_pair, by_ratio


def poole_part(depths, tr):
    rule("3. Beside Poole & Atkins's 1.7")
    products = [tr[key][1] * z for key, z in depths.items()]
    print(f"""Poole & Atkins (1929) found K times the Secchi depth to be {POOLE_RANGE[0]}
to {POOLE_RANGE[1]}, mean 1.7, with K the attenuation of daylight as their
photoelectric cells saw it from 0 to 20 m. In Lee et al.'s model the same
product, with the smallest spectral Kd, is ln(|0.14 - Rrs| / 0.013) / 2.5:
here {min(products):.2f} to {max(products):.2f} in every case. The two K are not the same quantity:
Poole & Atkins's mixes every wavelength their cells responded to, over 0
to 20 m; Lee et al.'s is the smallest spectral Kd, near the surface. The
products are two rules, not two estimates of one number.
jerlov.k_from_secchi with Poole & Atkins's 1.7 gives their K, not this
one.""")
    return products


def chlorophyll_part():
    rule("4. From a chlorophyll concentration to the nearest Jerlov type")
    wl = np.arange(400.0, 701.0, 5.0)
    print(f"""Morel & Maritorena's (2001) Kd for case 1 water, {wl[0]:g}-{wl[-1]:g} nm, and the
Jerlov type (1976) whose Kd it is closest to:
""")
    print(f"  {'[Chl] mg/m3':>11} {'Kd(490)':>8} {'nearest':>8} {'next':>6}")
    nearest = {}
    for chl in CHLOROPHYLL:
        k = jerlov.morel2001_kd(wl, chlorophyll_mg_m3=chl)
        found = jerlov.classify_kd(wl, k)
        ranked = [name for name, _ in found.distances]
        nearest[chl] = ranked[0]
        k490 = jerlov.morel2001_kd(490.0, chlorophyll_mg_m3=chl)
        print(f"  {chl:>11g} {k490:>8.3f} {ranked[0]:>8} {ranked[1]:>6}")
    coastal = [c for c in CHLOROPHYLL if nearest[c][0].isdigit()]
    print(f"""
The nearest type is a likeness of Kd, not a statement about the water.
Morel & Maritorena's relation is for case 1 water, whose optics follow its
phytoplankton; {' and '.join(f'{c:g}' for c in coastal)} mg/m3 come out nearest a coastal type
all the same, since Kd alone does not say which kind of water it is.""")
    return nearest


def main():
    _banner()
    caught = set()
    worst, kd = kd_part(caught)
    depths, tr, findings, depends, by_pair, by_ratio = secchi_part(kd,
                                                                    caught)
    products = poole_part(depths, tr)
    nearest = chlorophyll_part()
    if caught:
        rule("Warnings")
        print("Raised along the way, each a ProvenanceWarning:")
        for message in sorted(caught):
            print(f"  - {message}")

    rule("Before you use any of this")
    print(f"""  - a and b are Solonenko & Mobley's, inverted from Jerlov's Kd, not
    measured; bb is built from them with a stated bbp/bp, since no Jerlov
    type determines it (DATA.md section 10).
  - The pure water terms are Morel's formula at {SALINITY_PSU:g} psu.
  - The reflectance is for optically deep water seen from straight above:
    no bottom, no Raman scattering, no fluorescence.
  - The Secchi depth rests on the eye's contrast threshold and the white
    disc that Lee et al. assumed; their check against 338 measurements
    found about 18 percent.
  - Morel & Maritorena's Kd is a mean for case 1 water, about which real
    waters scatter.
""")
    return dict(worst=worst, depths=depths, findings=findings,
                depends=depends, by_pair=by_pair, by_ratio=by_ratio, products=products, nearest=nearest,
                caught=caught)


if __name__ == "__main__":
    main()

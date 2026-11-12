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
concentrations (DECISIONS.md section 66). Last, it inverts the reflectance
again by the quasi-analytical algorithm, both versions, and sets the a and
bbp they recover against the ones it started from (section 67). Finally,
it builds a and bb from chlorophyll alone and compares the Kd they give
with Morel & Maritorena's (section 72).
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


#: The bands of the round trip, a SeaWiFS-like set.
QAA_NM = np.array([412.0, 443.0, 490.0, 510.0, 555.0, 670.0])
V6_BANDS = {"412": 412, "443": 443, "490": 490, "55x": 555, "670": 670}
R5_BANDS = {"410": 412, "440": 443, "490": 490, "510": 510, "555": 555,
            "670": 670}
COMPARED_NM = (412.0, 443.0, 490.0, 555.0)


def qaa_part():
    rule("5. Back again: the quasi-analytical algorithm")
    print(f"""Rrs computed from known a and bb, as in part 2 with Lee et al.'s (2002)
coefficients, at {', '.join(f'{w:g}' for w in QAA_NM)} nm, then inverted by QAA_v6 and by
the version of IOCCG Report 5 (2006). Pure water for the inversion is the
package's: Williamson & Hollins's aw and Morel's bbw at {SALINITY_PSU:g} psu. The
largest departure, in percent, of the a recovered at {', '.join(f'{w:g}' for w in COMPARED_NM)} nm
from the a the reflectance was computed from:
""")
    pw_nm = np.arange(400.0, 701.0, 1.0)
    pure_water = (pw_nm, jerlov.pure_water_absorption(pw_nm),
                  jerlov.pure_water_backscattering(
                      pw_nm, salinity_psu=SALINITY_PSU))
    cols = [QAA_NM.tolist().index(w) for w in COMPARED_NM]
    worst = {"v6": 0.0, "ioccg2006": 0.0}
    head = "".join(f" {r:>8g}" for r in PARTICLE_RATIOS)
    print(f"  {'type':>5} {'version':<10}{head}   (bbp/bp)")
    for t in TYPES:
        water = jerlov.water(t, source="solonenko2015")
        a = water.a(QAA_NM)
        bbw = jerlov.pure_water_backscattering(QAA_NM,
                                               salinity_psu=SALINITY_PSU)
        bp = water.b(QAA_NM) - jerlov.pure_water_scattering(
            QAA_NM, salinity_psu=SALINITY_PSU)
        rows = {"v6": [], "ioccg2006": []}
        for r in PARTICLE_RATIOS:
            bb = bbw + r * bp
            rrs = jerlov.above_surface_rrs(jerlov.subsurface_rrs(
                a, bb, coefficients=jerlov.LEE2002_RRS_COEFFICIENTS))
            for version, q in (
                    ("v6", jerlov.qaa_v6(QAA_NM, rrs, bands=V6_BANDS,
                                         pure_water=pure_water)),
                    ("ioccg2006", jerlov.qaa_ioccg2006(
                        QAA_NM, rrs, bands=R5_BANDS,
                        pure_water=pure_water))):
                off = float(np.max(np.abs(q.a[cols] / a[cols] - 1)))
                rows[version].append(off)
                worst[version] = max(worst[version], off)
        for version, offs in rows.items():
            print(f"  {t:>5} {version:<10}"
                  + "".join(f" {100 * x:>7.0f}%" for x in offs))
    print(f"""
QAA_v6 recovers a within {100 * worst['v6']:.0f} percent here, the 2006 version within
{100 * worst['ioccg2006']:.0f}. Neither is told the backscatter ratio: both estimate a at a
reference wavelength from the colour alone, by relations fitted to other
water. This is a check that the pieces fit together, not a measure of
either algorithm on real water; IOCCG Report 5 gives that, for the 2006
version, against its synthetic and field data.""")
    return worst


#: Bricaud et al. (1998): nonalgal particles at 440 nm, eq. (3), and the
#: mean slope of their exponential, eq. (5), from 267 measured spectra.
NAP_440 = (0.0124, 0.724)
NAP_SLOPE = 0.011
#: Their appendix: CDOM at 440 nm as a share y of (aw + ap)(440), with
#: y = 0, 0.1 or 0.2, and a slope of 0.014 (eq. 11).
CDOM_SHARES = (0.0, 0.1, 0.2)
CDOM_SLOPE = 0.014
CASE1_NM = (440.0, 490.0, 555.0)
#: Lee et al. (2013): the model is good for Kd of about 0.02-5 1/m.
LEE2013_KD_RANGE = (0.02, 5.0)


def case1_part(caught):
    rule("6. From chlorophyll to a and bb, and on to Kd")
    wl = np.arange(400.0, 701.0, 5.0)
    print(f"""a and bb built from [Chl] alone, {wl[0]:g}-{wl[-1]:g} nm: pure water (Pope & Fry
1997; Morel's bbw at {SALINITY_PSU:g} psu), phytoplankton (Bricaud et al. 1995),
nonalgal particles ({NAP_440[0]} [Chl]^{NAP_440[1]} at 440 nm, slope {NAP_SLOPE} per nm, Bricaud
et al. 1998), CDOM as a share y = {', '.join(f'{y:g}' for y in CDOM_SHARES)} of the rest at 440 nm with
slope {CDOM_SLOPE} (their appendix), and particle backscattering (Morel &
Maritorena 2001, eqs. 13-14). Lee et al.'s (2013) Kd from them, sun at
{SUN_ZENITH_DEG:g} degrees, against Morel & Maritorena's Kd for the same [Chl], in percent:
""")
    aw = jerlov.pure_water_absorption_table(wl, source="pope1997")
    bbw = jerlov.pure_water_backscattering(wl, salinity_psu=SALINITY_PSU)
    at = {w: int(np.flatnonzero(wl == w)[0]) for w in (440.0,) + CASE1_NM}
    head = "".join(f" {f'y={y:g}':>17}" for y in CDOM_SHARES)
    print(f"  {'[Chl]':>6}{head}")
    print(f"  {'mg/m3':>6}" + "".join(
        f" {'/'.join(f'{w:g}' for w in CASE1_NM):>17}" for _ in CDOM_SHARES))
    diff = {}
    low_kd, low_chl = set(), set()
    for chl in CHLOROPHYLL:
        aph = jerlov.bricaud1995_aph(wl, chlorophyll_mg_m3=chl)
        anap = NAP_440[0] * chl ** NAP_440[1] * np.exp(
            -NAP_SLOPE * (wl - 440.0))
        bbp = jerlov.morel2001_bbp(wl, chlorophyll_mg_m3=chl)
        k_morel = jerlov.morel2001_kd(wl, chlorophyll_mg_m3=chl)
        cells = []
        for y in CDOM_SHARES:
            i = at[440.0]
            cdom = y * (aw[i] + aph[i] + anap[i]) * np.exp(
                -CDOM_SLOPE * (wl - 440.0))
            with warnings.catch_warnings(record=True) as record:
                warnings.simplefilter("always")
                kd = jerlov.lee2013_kd(aw + aph + anap + cdom, bbw + bbp,
                                       bb_water=bbw,
                                       sun_zenith_deg=SUN_ZENITH_DEG)
            expect_provenance(record, caught)
            if np.any(kd < LEE2013_KD_RANGE[0]):
                low_kd.update(wl[kd < LEE2013_KD_RANGE[0]].tolist())
                low_chl.add(chl)
            rel = kd / k_morel - 1
            diff[(chl, y)] = {w: float(rel[at[w]]) for w in CASE1_NM}
            cells.append("/".join(f"{100 * diff[(chl, y)][w]:+.0f}"
                                  for w in CASE1_NM))
        print(f"  {chl:>6g}" + "".join(f" {c:>17}" for c in cells))
    below = [c for c in CHLOROPHYLL
             if all(diff[(c, y)][w] < 0 for y in CDOM_SHARES
                    for w in CASE1_NM)]
    blue = {c: [100 * diff[(c, y)][440.0] for y in CDOM_SHARES]
            for c in CHLOROPHYLL}
    top, low = CHLOROPHYLL[-1], CHLOROPHYLL[0]
    mixed = min(blue[low]) < 0 < max(blue[low])
    low_text = (f"At {low:g} mg/m3 the sign at 440 nm depends on y "
                f"({min(blue[low]):+.0f} to {max(blue[low]):+.0f} percent)."
                if mixed else
                f"At {low:g} mg/m3 the difference at 440 nm is "
                f"{min(blue[low]):+.0f} to {max(blue[low]):+.0f} percent.")
    print(f"""
For [Chl] of {', '.join(f'{c:g}' for c in below)} mg/m3 the Kd built this way is below Morel &
Maritorena's at all three wavelengths, whatever y; at {top:g} mg/m3 by
{-max(blue[top]):.0f} to {-min(blue[top]):.0f} percent at 440 nm.
{low_text}
Both are means for case 1 water from different data sets; this sets two
published routes side by side and does not say which is nearer the sea.""")
    if low_kd:
        print(f"""The built Kd falls below the {LEE2013_KD_RANGE[0]:g} 1/m that Lee et al. (2013) state their
model good for at {min(low_kd):g}-{max(low_kd):g} nm, for [Chl] of {', '.join(f'{c:g}' for c in sorted(low_chl))} mg/m3; that is the
warning about it below.""")
    return dict(diff=diff, below=below, mixed=mixed, low_kd=sorted(low_kd),
                low_chl=sorted(low_chl))


#: The six MODIS bands of Lee et al.'s (2013) Table 2, where RF is defined.
MODIS_NM = np.array([412.0, 443.0, 488.0, 531.0, 551.0, 667.0])
NADIR = (0.0, 0.0, 0.0)


def geometry_part(kd, caught):
    rule("7. The reflectance by geometry, and Raman scattering")
    print(f"""Lee et al. (2011) keep water and particles apart and print their
coefficients for seven geometries (sun, view, azimuth from the sun, in
degrees). At the MODIS bands of Lee et al.'s (2013) Raman correction, with
bbp/bp = {PETZOLD_RATIO}; a and b interpolated linearly between Solonenko &
Mobley's 25 nm:
""")
    by_view, against, raman, fitted = {}, {}, {}, {}
    print(f"  {'type':>5} {'off nadir / nadir':>20} "
          f"{'nadir / Gordon et al.':>24} {'Raman RF':>14}")
    for t in TYPES:
        water = jerlov.water(t, source="solonenko2015")
        a = water.a(MODIS_NM)
        bbw = jerlov.pure_water_backscattering(MODIS_NM,
                                               salinity_psu=SALINITY_PSU)
        bp = water.b(MODIS_NM) - jerlov.pure_water_scattering(
            MODIS_NM, salinity_psu=SALINITY_PSU)
        bb = bbw + PETZOLD_RATIO * bp
        with warnings.catch_warnings(record=True) as record:
            warnings.simplefilter("always")
            lee = {g: jerlov.lee2011_rrs(a, bb, bb_water=bbw, coefficients=c)
                   for g, c in jerlov.LEE2011_RRS_COEFFICIENTS.items()}
        expect_provenance(record, caught)
        gordon = jerlov.above_surface_rrs(jerlov.subsurface_rrs(
            a, bb, coefficients=jerlov.GORDON1988_RRS_COEFFICIENTS))
        u = bb / (a + bb)
        # Lee et al. fitted to bb/(a + bb) from 0.0002 to 0.37 (p. 3159).
        fitted[t] = (u >= 0.0002) & (u <= 0.37)
        ratios = np.array([lee[g] / lee[NADIR] for g in lee])
        by_view[t] = (ratios.min(), ratios.max(),
                      ratios[:, fitted[t]].max())
        against[t] = lee[NADIR] / gordon
        # RF is defined on a measured reflectance, which holds Raman
        # scattering; this one is elastic, so RF here is the size of the
        # share a measured spectrum would carry, not a correction of it.
        raman[t] = jerlov.lee2013_raman_correction(
            MODIS_NM, gordon, bands={"440": 443.0, "550": 551.0}).raman_factor
        print(f"  {t:>5} {ratios.min():>9.3f} to {ratios.max():.3f}"
              f" {against[t].min():>13.2f} to {against[t].max():.2f}"
              f" {raman[t].min():>7.3f} to {raman[t].max():.3f}")
    view_hi = max(v[1] for v in by_view.values())
    view_fitted = max(v[2] for v in by_view.values())
    off = max(np.max(np.abs(v - 1)) for v in against.values())
    off_fitted = max(np.max(np.abs(against[t][fitted[t]] - 1)) for t in TYPES)
    outside = {t: MODIS_NM[~fitted[t]] for t in TYPES if not fitted[t].all()}
    rf_lo = min(v.min() for v in raman.values())
    rf_hi = max(v.max() for v in raman.values())
    worst_rf = max(TYPES, key=lambda t: raman[t].max())
    print(f"""
{"; ".join(f"{t} at {', '.join(f'{w:g}' for w in v)} nm" for t, v in outside.items())} lies outside the range of bb/(a + bb) Lee et al.
fitted to, 0.0002-0.37 (the warning below), so those figures are the
model's beyond its data. Within the range: looked at from off nadir, the
same water's reflectance is up to {100 * (view_fitted - 1):.0f} percent above the nadir one ({100 * (view_hi - 1):.0f}
with the rest), and at nadir Lee et al.'s (2011) model differs from Gordon
et al.'s (1988) by up to {100 * off_fitted:.0f} percent ({100 * off:.0f} with the rest). Both are fits to
radiative transfer calculations, made on different sets of waters.

RF, by Lee et al.'s (2013) empirical correction, is the Raman part of a
measured reflectance relative to its elastic part, Rrs_measured = Rrs (1 +
RF): {100 * rf_lo:.0f} to {100 * rf_hi:.0f} percent here, the most at 667 nm in {worst_rf}. These
reflectances are elastic, so RF is computed on them as on a measured one,
to show its size; a measured Rrs would carry that much more, and should
have it removed before it is compared with any of this.""")

    print("""
The Secchi depth by Lee et al. (2015), part 2's grid and part 1's Kd,
from each nadir reflectance, m:
""")
    secchi = {}
    for t in TYPES:
        _, a, bp, bbw = optics(t)
        bb = bbw + PETZOLD_RATIO * bp
        k = kd[t, PETZOLD_RATIO]
        with warnings.catch_warnings(record=True) as record:
            warnings.simplefilter("always")
            lee = jerlov.lee2011_rrs(
                a, bb, bb_water=bbw,
                coefficients=jerlov.LEE2011_RRS_COEFFICIENTS[NADIR])
            gordon = jerlov.above_surface_rrs(jerlov.subsurface_rrs(
                a, bb, coefficients=jerlov.GORDON1988_RRS_COEFFICIENTS))
            secchi[t] = (jerlov.lee2015_secchi_depth(WL, k, gordon),
                         jerlov.lee2015_secchi_depth(WL, k, lee))
        expect_provenance(record, caught)
        print(f"  {t:>5}  Gordon et al. {secchi[t][0]:>5.1f}   "
              f"Lee et al. (2011) {secchi[t][1]:>5.1f}")
    moved = max(abs(b / a - 1) for a, b in secchi.values())
    print(f"""
The reflectance model moves the Secchi depth by at most {100 * moved:.1f} percent: the
depth rests mostly on Kd, and on the reflectance only through a
logarithm. III's reflectance by Lee et al. (2011) rests partly on bands
outside their fit, as above.""")
    return dict(by_view=by_view, against=against, raman=raman,
                secchi=secchi, view_hi=view_hi, view_fitted=view_fitted,
                off=off,
                off_fitted=off_fitted, outside=outside, rf=(rf_lo, rf_hi),
                moved=moved)


def main():
    _banner()
    caught = set()
    worst, kd = kd_part(caught)
    depths, tr, findings, depends, by_pair, by_ratio = secchi_part(kd,
                                                                    caught)
    products = poole_part(depths, tr)
    nearest = chlorophyll_part()
    recovered = qaa_part()
    case1 = case1_part(caught)
    geometry = geometry_part(kd, caught)
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
  - The reflectance is for optically deep water: no bottom, no Raman
    scattering, no fluorescence. Part 7 looks off nadir with Lee et al.'s
    (2011) seven printed geometries, and gives Raman scattering's share
    by Lee et al.'s (2013) correction, which is empirical.
  - The Secchi depth rests on the eye's contrast threshold and the white
    disc that Lee et al. assumed; their check against 338 measurements
    found about 18 percent.
  - Morel & Maritorena's Kd is a mean for case 1 water, about which real
    waters scatter.
  - Part 6's a and bb are built from means as well, and from choices
    that are stated, not determined: the nonalgal slope, the share of
    CDOM, and Pope & Fry's pure water.
""")
    return dict(worst=worst, depths=depths, findings=findings,
                depends=depends, by_pair=by_pair, by_ratio=by_ratio, products=products, nearest=nearest,
                recovered=recovered, case1=case1, geometry=geometry,
                caught=caught)


if __name__ == "__main__":
    main()

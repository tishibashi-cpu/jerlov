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
with Morel & Maritorena's (section 72). Part 13 puts a bottom under the
water (section 113).
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


#: The five pure water spectra the package ships (DATA.md section 29).
PURE_WATERS = ("pope1997", "smith1981", "mason2016", "lee2015",
               "williamson2022")
BAND_NM = np.array([380.0, 400.0, 412.0, 443.0, 490.0, 510.0, 550.0])


def _aw(source, wl):
    if source == "williamson2022":
        return jerlov.pure_water_absorption(wl)
    return jerlov.pure_water_absorption_table(wl, source=source)


def _rrs(a, bb, bbw, relation, record_into):
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        if relation == "lee2011":
            out = jerlov.lee2011_rrs(
                a, bb, bb_water=bbw,
                coefficients=jerlov.LEE2011_RRS_COEFFICIENTS[(0.0, 0.0, 0.0)])
        else:
            out = jerlov.above_surface_rrs(jerlov.subsurface_rrs(
                a, bb, coefficients=jerlov.GORDON1988_RRS_COEFFICIENTS))
    expect_provenance(record, record_into)
    return np.asarray(out, dtype=float)


def pure_water_part(caught):
    rule("8. What the choice of pure water does to the colour of clear water")
    water = jerlov.water("IB")
    constants = water.source.scattering
    stations = {s: jerlov.petzold_scattering(s).backscatter_ratio
                for s in jerlov.PETZOLD_STATIONS}
    out = {}
    for relation in ("lee2011", "gordon1988"):
        wl = BAND_NM
        bw = constants.bw_coeff * (400.0 / wl) ** constants.bw_exponent
        pure = {src: _rrs(_aw(src, wl), bw / 2, bw / 2, relation, caught)
                for src in PURE_WATERS}
        # Williamson & Hollins's IB, measured from 412 nm.
        wb = BAND_NM[2:]
        bwb = bw[2:]
        contents = water.a(wb) - jerlov.pure_water_absorption(wb)
        ib = {}
        for station, r in stations.items():
            bb = water.bb(wb, particle_backscatter_ratio=r)
            ib[station] = {src: _rrs(contents + _aw(src, wb), bb, bwb / 2,
                                     relation, caught)
                           for src in PURE_WATERS}
        out[relation] = dict(pure=pure, ib=ib)

    def spread(by_source):
        stack = np.array(list(by_source.values()))
        return stack.max(axis=0) / stack.min(axis=0)

    def ratios(by_source, i, j):
        return {src: float(v[i] / v[j]) for src, v in by_source.items()}

    found = {}
    for relation, r in out.items():
        a_spread = spread(r["pure"])
        b_spread = {st: spread(v) for st, v in r["ib"].items()}
        by_ratio = (np.array([r["ib"][st]["pope1997"]
                              for st in stations]).max(axis=0)
                    / np.array([r["ib"][st]["pope1997"]
                                for st in stations]).min(axis=0))
        stack_b = np.array(list(b_spread.values()))
        verdict = np.where(stack_b.min(axis=0) > by_ratio, "pure water",
                           np.where(stack_b.max(axis=0) < by_ratio,
                                    "particles", "depends on r"))
        found[relation] = dict(
            a_spread=a_spread, b_spread=(stack_b.min(axis=0),
                                         stack_b.max(axis=0)),
            by_ratio=by_ratio, verdict=verdict,
            a_443_550=ratios(r["pure"], 3, 6), a_412_550=ratios(r["pure"], 2, 6),
            b_443_550=[ratios(v, 1, 4) for v in r["ib"].values()],
            b_412_550=[ratios(v, 0, 4) for v in r["ib"].values()])
    lee = found["lee2011"]
    print("""The five pure water absorption spectra the package ships, under (A) pure
sea water alone and (B) Williamson & Hollins's IB, its contents laid on
each spectrum, bb from Petzold's eight measured B/S in turn. Rrs by Lee et
al. (2011), nadir. Largest over smallest Rrs among the five spectra, and,
for IB, among the eight B/S with Pope & Fry's water:

  nm   (A) pure water   (B) IB: spectra      (B) IB: B/S    larger""")
    for k, wl in enumerate(BAND_NM):
        if k < 2:
            print(f"  {wl:3.0f}  {lee['a_spread'][k]:10.2f}")
            continue
        i = k - 2
        print(f"  {wl:3.0f}  {lee['a_spread'][k]:10.2f}       "
              f"{lee['b_spread'][0][i]:.2f} to {lee['b_spread'][1][i]:.2f}"
              f"{lee['by_ratio'][i]:14.2f}    {lee['verdict'][i]}")

    def span(d):
        values = list(d.values()) if isinstance(d, dict) else [
            x for item in d for x in item.values()]
        return min(values), max(values)

    a443, a412 = span(lee["a_443_550"]), span(lee["a_412_550"])
    b443, b412 = span(lee["b_443_550"]), span(lee["b_412_550"])
    g = found["gordon1988"]
    off = np.abs(g["a_spread"] / lee["a_spread"] - 1)
    violet = BAND_NM <= 412
    ib_off = float(np.max(np.abs(
        np.concatenate([g["b_spread"][0] / lee["b_spread"][0],
                        g["b_spread"][1] / lee["b_spread"][1],
                        g["by_ratio"] / lee["by_ratio"]]) - 1)))
    # Where pure sea water lies outside the bb / (a + bb) Lee et al. fitted.
    bw = constants.bw_coeff * (400.0 / BAND_NM) ** constants.bw_exponent
    outside = {src: [int(wl) for wl, u in zip(
        BAND_NM, (bw / 2) / (_aw(src, BAND_NM) + bw / 2)) if u > 0.37]
        for src in PURE_WATERS}
    outside = {k: v for k, v in outside.items() if v}
    same = all((g["verdict"] == lee["verdict"]))
    print(f"""
Rrs(443)/Rrs(550), which chlorophyll algorithms read, is {a443[0]:.2f} to {a443[1]:.2f} over the
five spectra in pure sea water and {b443[0]:.2f} to {b443[1]:.2f} in IB (all eight B/S);
Rrs(412)/Rrs(550) is {a412[0]:.2f} to {a412[1]:.2f} and {b412[0]:.2f} to {b412[1]:.2f}.

Gordon et al.'s (1988) relation gives IB's spreads within {100 * ib_off:.1f} percent of Lee
et al.'s, {"and the same verdict at every wavelength" if same else "but not the same verdict"}, and pure sea water's within {100 * float(np.max(off[~violet])):.1f} percent
from 443 nm. Not below: at 380 to 412 nm they differ by up to {100 * float(np.max(off[violet])):.1f} percent, and
there pure sea water lies outside the range of bb / (a + bb) Lee et al.
fitted (above 0.37) for""")
    for src, wls in outside.items():
        print(f"  {src}: {', '.join(str(w) for w in wls)} nm")
    print("""so the violet figures for pure sea water rest on Lee et al.'s relation
outside the data it was fitted to, where the two relations part. Which
spectrum is right is not settled (DATA.md section 29); this is what the
choice does.""")
    return dict(found=found, a443=a443, a412=a412, b443=b443, b412=b412,
                ib_off=ib_off, off_violet=float(np.max(off[violet])),
                off_rest=float(np.max(off[~violet])), outside=outside,
                same_verdict=same, stations=stations)


#: Part 9: the atmosphere of examples/sunlight_and_d65.py, and the
#: aerosol of tools/sm_closure.py.
ATMOSPHERE = dict(day_of_year=172, pressure_hpa=1013.25, air_mass_type=1,
                  relative_humidity=80.0, precipitable_water_cm=1.5,
                  wind_speed_24h=3.0, wind_speed=5.0, ozone_du=300.0,
                  aerosol_optical_thickness_550=0.2)
WIND = 5.0
VIEWS = ((40.0, 135.0), (30.0, 90.0))
RHO_SOURCES = ("mobley1999", "mobley2015")
SHOWN_NM = (443.0, 555.0, 670.0)


def above_water_part(caught):
    rule("9. Measured from above the water: the sky the sea reflects")
    print(f"""A radiometer above the sea sees Lt = Lw + rho Lsky, and Rrs = (Lt - rho
Lsky) / Ed (Mobley 1999). rho is not a property of the surface: it depends
on the sun, the view, the wind and the sky. Mobley's two tables
(`mobley_rho`) give it for a clear sky at 550 nm: 1999, unpolarised; 2015,
polarised, for a Rayleigh sky, a table that calls itself preliminary and
warns so. Here Jerlov IB's Rrs, as in part 5 with
bbp/bp = {PETZOLD_RATIO}, is the truth; Lsky / Ed is that of a uniform sky carrying
Gregg & Carder's diffuse irradiance (Lsky = Ed,diffuse / pi, a stand-in,
not a sky model); the sun is at {SUN_ZENITH_DEG:g} degrees and the wind {WIND:g} m/s. Lt is
made with one table's rho, and Rrs recovered with the other's, or with
0.028. The error, in percent, of the recovered Rrs and of QAA_v6's a(443):
""")
    water = jerlov.water("IB", source="solonenko2015")
    a = water.a(QAA_NM)
    bbw = jerlov.pure_water_backscattering(QAA_NM, salinity_psu=SALINITY_PSU)
    bp = water.b(QAA_NM) - jerlov.pure_water_scattering(
        QAA_NM, salinity_psu=SALINITY_PSU)
    rrs = jerlov.above_surface_rrs(jerlov.subsurface_rrs(
        a, bbw + PETZOLD_RATIO * bp,
        coefficients=jerlov.LEE2002_RRS_COEFFICIENTS))
    sky = jerlov.gregg1990_irradiance(QAA_NM.astype(int),
                                      sun_zenith_deg=SUN_ZENITH_DEG,
                                      **ATMOSPHERE)
    sky_over_ed = sky.diffuse_above / sky.above / np.pi
    pw_nm = np.arange(400.0, 701.0, 1.0)
    pure_water = (pw_nm, jerlov.pure_water_absorption(pw_nm),
                  jerlov.pure_water_backscattering(
                      pw_nm, salinity_psu=SALINITY_PSU))
    a443 = jerlov.qaa_v6(QAA_NM, rrs, bands=V6_BANDS,
                         pure_water=pure_water).a[1]
    cols = [QAA_NM.tolist().index(w) for w in SHOWN_NM]
    head = "".join(f" {f'Rrs {w:g}':>9}" for w in SHOWN_NM)
    print(f"  {'view':>9} {'Lt made with':>13} {'recovered with':>15}{head}"
          f" {'a(443)':>8}")
    out, rho_by_view = {}, {}
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        for nadir, azimuth in VIEWS:
            rho = {s: jerlov.mobley_rho(
                source=s, wind_speed=WIND, sun_zenith_deg=SUN_ZENITH_DEG,
                view_nadir_deg=nadir, view_azimuth_deg=azimuth)
                for s in RHO_SOURCES}
            rho_by_view[(nadir, azimuth)] = rho
            print(f"  ({nadir:g}, {azimuth:g}): rho "
                  + ", ".join(f"{s} {v:.4f}" for s, v in rho.items()))
            for true in RHO_SOURCES:
                lt_over_ed = rrs + rho[true] * sky_over_ed
                for guess in [s for s in RHO_SOURCES if s != true] + [None]:
                    used = 0.028 if guess is None else rho[guess]
                    got = jerlov.rrs_from_above_water(
                        lt_over_ed, sky_over_ed, 1.0, rho=used)
                    off = got / rrs - 1
                    if np.any(got < 0):
                        # QAA refuses a negative Rrs, as it should.
                        off_a = float("nan")
                    else:
                        off_a = jerlov.qaa_v6(
                            QAA_NM, got, bands=V6_BANDS,
                            pure_water=pure_water).a[1] / a443 - 1
                    out[(nadir, azimuth, true, guess)] = (off[cols], off_a)
                    print(f"  {'':>9} {true:>13} "
                          f"{guess or '0.028':>15}"
                          + "".join(f" {100 * x:>8.0f}%" for x in off[cols])
                          + (f" {'(Rrs<0)':>8}" if np.isnan(off_a)
                             else f" {100 * off_a:>7.0f}%"))
    expect_provenance(record, caught)
    worst_red = max(abs(v[0][2]) for v in out.values())
    gaps = [abs(rho_by_view[v]["mobley2015"] - rho_by_view[v]["mobley1999"])
            for v in VIEWS]
    print(f"""
Lsky / Ed here is {sky_over_ed[cols[0]]:.3f}, {sky_over_ed[cols[1]]:.3f} and {sky_over_ed[cols[2]]:.3f} per sr at 443, 555 and 670 nm, and
Rrs {rrs[cols[0]]:.4f}, {rrs[cols[1]]:.4f} and {rrs[cols[2]]:.5f}. The two tables' rho differ by {gaps[0]:.4f} at
(40, 135) and {gaps[1]:.4f} at (30, 90), and times Lsky / Ed that is a large
share of the Rrs of water this clear where it is dark, in the red: up to
{100 * worst_red:.0f} percent here, and below zero, which QAA refuses. QAA_v6's
reference a(555) comes from a band ratio with Rrs(670) inside it, so the
error reaches a(443). rho is for 550 nm; the
sky's colour and Sun glint make it vary with wavelength, which is not
followed here (Mobley 1999, section 4; Lee et al. 2010). DATA.md section
43.""")
    return dict(rho_sky_over_ed=sky_over_ed, errors=out,
                worst_red=worst_red)


EDITION_C = (0.03, 0.3, 3.0, 30.0)
EDITION_NM = (412.0, 443.0, 490.0, 555.0, 670.0)


def editions_part():
    rule("10. Morel's two editions of Kd from chlorophyll")
    wl = np.arange(400.0, 701.0, 5.0)
    print("""Morel (1988) and Morel & Maritorena (2001) give Kd = Kw + chi C^e for
case 1 water, the second a revision of the first. 1988's C is chlorophyll
a plus pheophytin a; 2001's is chlorophyll a by HPLC; the same number is
put into both here, which is itself an assumption. Kd 2001 / Kd 1988:
""")
    head = "".join(f" {f'{w:g}':>6}" for w in EDITION_NM)
    print(f"  {'C mg/m3':>8}{head}   nearest type, 1988 and 2001")
    ratios, nearest = {}, {}
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        for c in EDITION_C:
            k88 = jerlov.morel1988_kd(wl, pigment_mg_m3=c)
            k01 = jerlov.morel2001_kd(wl, chlorophyll_mg_m3=c)
            r = np.interp(EDITION_NM, wl, k01 / k88)
            ratios[c] = r
            nearest[c] = (jerlov.classify_kd(wl, k88).water_type,
                          jerlov.classify_kd(wl, k01).water_type)
            print(f"  {c:>8g}" + "".join(f" {x:>6.2f}" for x in r)
                  + f"   {nearest[c][0]:>4} {nearest[c][1]:>4}")
    for w in record:
        if not issubclass(w.category, jerlov.ProvenanceWarning):
            warnings.warn_explicit(w.message, w.category, w.filename,
                                   w.lineno)
    clear = ratios[EDITION_C[0]]
    c = EDITION_C[0]
    with warnings.catch_warnings():
        # Only the split below; the warnings were reported above.
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        k88 = jerlov.morel1988_kd(412.0, pigment_mg_m3=c)
        k01 = jerlov.morel2001_kd(412.0, chlorophyll_mg_m3=c)
        kw88 = jerlov.morel1988_kd(412.0, pigment_mg_m3=1e-12)
        kw01 = jerlov.morel2001_kd(412.0, chlorophyll_mg_m3=1e-12)
    kw_share = (kw01 - kw88) / (k01 - k88)
    print(f"""
In the clearest water the 2001 edition's Kd is {clear[0]:.2f} of 1988's at 412 nm and
{clear[2]:.2f} at 490. At 412 nm and {c:g} mg/m3 the change in Kw, pure sea water's
own term, is {kw_share:.2f} times the whole change: Kw alone lowers Kd by more than
it falls, and the revised chi C^e takes some of it back. From 560 nm on,
2001 kept 1988's chi and e unchanged and replaced only Kw, where DATA.md
section 27 had put the unrevised range at 590-600 nm from the paper's own
words. 1988's warning beyond 650 nm is its own. DATA.md section 45.""")
    return dict(ratios=ratios, nearest=nearest, kw_share=kw_share)


def clearest_part():
    rule("11. The clearest water measured, against the models and Jerlov I")
    print("""Morel et al. (2007) measured Kd in the South Pacific gyre, the clearest
ocean water known (`morel2007_stations`). Each station's Kd(420) beside
Morel & Maritorena's (2001) and Morel's (1988) Kd at its chlorophyll at 5
m, put into both, Jerlov's (1976) type I and Austin & Petzold's (1986)
type I, which they meant as pure sea water, at the same wavelength:
""")
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        stations = jerlov.morel2007_stations()
        jerlov_i = float(jerlov.water("I", source="jerlov1976").kd(420.0))
        austin_i = float(jerlov.water("I", source="austin1986").kd(420.0))
        rows = []
        for s in stations:
            c = s.chl_5m_mg_m3
            rows.append((s.station, c, s.kd_420_per_m,
                         jerlov.morel2001_kd(420.0, chlorophyll_mg_m3=c),
                         jerlov.morel1988_kd(420.0, pigment_mg_m3=c)))
    flagged = sorted({str(w.message)[:70] for w in record
                      if issubclass(w.category, jerlov.ProvenanceWarning)})
    for w in record:
        if not issubclass(w.category, jerlov.ProvenanceWarning):
            warnings.warn_explicit(w.message, w.category, w.filename,
                                   w.lineno)
    print(f"  {'station':>8} {'Chl':>6} {'Kd(420)':>8} {'2001':>7} {'1988':>7}")
    for station, c, kd, k01, k88 in rows:
        print(f"  {station:>8} {c:>6.4f} {kd:>8.4f} {k01:>7.4f} {k88:>7.4f}")
    aw1 = jerlov.pure_water_absorption_table(420.0, source="morel2007")
    kd_sw = aw1 + 0.0056 / 2      # Table 2: bsw(420) = 0.0056, bbsw half
    kds = np.array([r[2] for r in rows])
    to_2001 = np.array([r[2] / r[3] for r in rows])
    print(f"""
  Jerlov I {jerlov_i:.4f}, Austin & Petzold's type I {austin_i:.4f}, and their own
  pure sea water, aw1 + bsw / 2 (Table 2), {kd_sw:.4f}.

The stations' Kd(420) is {kds.min():.4f} to {kds.max():.4f}: {kds.min() / jerlov_i:.2f} to {kds.max() / jerlov_i:.2f} of Jerlov I,
and at {int(np.sum(kds < austin_i))} of the 8 stations below Austin & Petzold's type I, which is
pure sea water's Kw. The measured Kd is {to_2001.min():.2f} to {to_2001.max():.2f} of Morel & Maritorena's
(2001) at the same chlorophyll, and lower still against 1988's, whose
chlorophyll here is below the 0.03 mg/m3 it was run from. Morel et al.'s
Kd spectra (their Fig. 4) are from the surface to 20-59 m; the models' Kd
is of about one penetration depth. The warnings:""")
    for message in flagged:
        print(f"  - {message}...")
    print("  DATA.md section 46.")
    return dict(kd=kds, to_2001=to_2001, jerlov_i=jerlov_i,
                austin_i=austin_i, kd_sw=kd_sw)


FQ_CHL = (0.03, 0.1, 0.3, 1.0, 3.0, 10.0)
FQ_SUNS = (0.0, 15.0, 30.0, 45.0, 60.0, 75.0)


def nadir_fq_part():
    rule("12. Measured from below, looking up: f and Q for a nadir view")
    print("""Below the surface, a radiometer looking up from the nadir reads Lu, and
the water-leaving radiance it gives depends on the sun through f and Q,
the factors of R = f bb/a and Q = Eu/Lu. Morel et al. (2002) print them
for that view, for case 1 water (`morel2002_nadir_fq`). The factor of
their Eq. (B3), (f0/Q0) / (f/Qn), takes a radiance measured with the sun
at theta_s to the sun at the zenith:
""")
    head = "".join(f" {f'{s:g}':>6}" for s in FQ_SUNS)
    out = {}
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        for wl in (412.5, 560.0):
            print(f"  {wl:g} nm, Chl mg/m3{head}")
            for chl in FQ_CHL:
                row = [jerlov.morel2002_nadir_fq(
                    wl, chlorophyll_mg_m3=chl, sun_zenith_deg=s).correction
                    for s in FQ_SUNS]
                out[(wl, chl)] = row
                print(f"  {chl:>17g}" + "".join(f" {x:>6.3f}" for x in row))
        at_490 = {s: jerlov.morel2002_nadir_fq(
            490.0, chlorophyll_mg_m3=0.1, sun_zenith_deg=s).q
            for s in (0.0, 15.0, 30.0, 45.0)}
    for w in record:
        if not issubclass(w.category, jerlov.ProvenanceWarning):
            warnings.warn_explicit(w.message, w.category, w.filename,
                                   w.lineno)
    eq17 = {s: 5.20 - 1.82 * np.cos(np.radians(s)) for s in at_490}
    off = max(abs(at_490[s] / eq17[s] - 1) for s in at_490)
    low = min(min(v) for v in out.values())
    print(f"""
With the sun low and the water rich in chlorophyll the factor falls to
{low:.2f}: a radiance measured with the sun at 75 degrees is multiplied by
that to compare with one under a zenith sun. At 0.03 mg/m3 it rises a
little above 1 instead, by {100 * (out[(560.0, 0.03)][-1] - 1):.1f} percent at 560 nm. From 60 degrees the
paper's fits of f and Q stop and only their ratio goes on (it warns).
Aas & Højerslev's relation from Mediterranean measurements at 465-474 nm,
Qn = 5.20 - 1.82 cos theta_s (the paper's Eq. 17), is within {100 * off:.1f} percent of
Table 2 at 490 nm and 0.1 mg/m3, the paper's estimate for those waters, at
0 to 45 degrees. Only the nadir view is
printed in the paper; the tables for other views are on a server this
package could not reach. DATA.md section 47.""")
    return dict(correction=out, eq17_off=off, low=low)


SHALLOW_WL = (450.0, 550.0, 650.0)
#: Bottom albedos for part 13, flat in wavelength like those of Lee et
#: al.'s runs (which were 0, 0.1, 0.3 and 1). Choices, not measurements of
#: any sea bed.
SHALLOW_ALBEDOS = (0.1, 0.3)
#: The depths Lee et al.'s 1998 runs covered, m.
SHALLOW_DEPTHS = np.linspace(0.5, 32.0, 631)
#: The bottom counts as out of sight where its part of rrs falls below this.
BOTTOM_SHARE = 0.1


def shallow_part(caught):
    rule("13. Shallow water: how deep the bottom stays in view")
    print(f"""Over a bottom the reflectance has two parts, the water column's and the
bottom's (`lee1999_shallow_rrs`, Lee et al. 1998, 1999), straight down,
the sun at {SUN_ZENITH_DEG:g} degrees. For four types, a and b as in part 1 and
bbp/bp = {PETZOLD_RATIO}: the depth at which the bottom's part of rrs falls to
{100 * BOTTOM_SHARE:g} percent, for bottoms of albedo {SHALLOW_ALBEDOS[0]:g} and {SHALLOW_ALBEDOS[1]:g}, flat in wavelength.
">32" means it is still above that at 32 m, the deepest of the paper's
runs:
""")
    head = "".join(f" {f'{w:g} nm':>8}" for w in SHALLOW_WL)
    print(f"  {'type':>4} {'albedo':>6}{head}")
    out = {}
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        for water_type in TYPES:
            water, a, b_particles, bb_water = optics(water_type)
            keep = np.isin(WL, SHALLOW_WL)
            bb = bb_water[keep] + PETZOLD_RATIO * b_particles[keep]
            for rho in SHALLOW_ALBEDOS:
                r = jerlov.lee1999_shallow_rrs(
                    a[keep], bb, depth_m=SHALLOW_DEPTHS[:, None],
                    bottom_albedo=rho, sun_zenith_deg=SUN_ZENITH_DEG)
                share = r.bottom / r.rrs
                depths = []
                for column in share.T:
                    below = np.flatnonzero(column < BOTTOM_SHARE)
                    depths.append(SHALLOW_DEPTHS[below[0]] if below.size
                                  else np.inf)
                out[(water_type, rho)] = depths
                cells = "".join(f" {'>32' if d == np.inf else f'{d:.1f}':>8}"
                                for d in depths)
                print(f"  {water_type:>4} {rho:>6g}{cells}")
            if water_type == "IB":
                five = jerlov.lee1999_shallow_rrs(
                    a[keep], bb, depth_m=5.0, bottom_albedo=0.3,
                    sun_zenith_deg=SUN_ZENITH_DEG)
    expect_provenance(record, caught)
    ratio = five.above_surface / (0.5 * five.deep / (1 - 1.5 * five.deep))
    print(f"""
Over a bottom of albedo 0.3 at 5 m, IB's Rrs is {ratio[0]:.1f}, {ratio[1]:.1f} and {ratio[2]:.1f} times that of
the same water with no bottom at {SHALLOW_WL[0]:g}, {SHALLOW_WL[1]:g} and {SHALLOW_WL[2]:g} nm. The model is a fit
to HydroLight runs with a Lambertian bottom and one particle phase
function; the bottom's albedo and depth are the caller's. DATA.md section
50 sets it against a Monte Carlo.""")
    return dict(depths=out, ratio_5m=ratio)


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
    pure_water = pure_water_part(caught)
    above_water = above_water_part(caught)
    editions = editions_part()
    clearest = clearest_part()
    nadir_fq = nadir_fq_part()
    shallow = shallow_part(caught)
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
  - The reflectance is for optically deep water, except in part 13: no
    Raman scattering, no fluorescence. Part 13's bottoms are Lambertian
    and flat in wavelength, with albedos chosen, not measured. Part 7 looks off nadir with Lee et al.'s
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
  - Part 8 takes pure water's scattering from Williamson & Hollins's
    constants, not Morel's formula, so as to match their IB, and reads
    IB's averaged a as published, which part 7 of
    closure_with_jerlov_kd.py finds high in the blue.
""")
    return dict(worst=worst, depths=depths, findings=findings,
                depends=depends, by_pair=by_pair, by_ratio=by_ratio, products=products, nearest=nearest,
                recovered=recovered, case1=case1, geometry=geometry,
                pure_water=pure_water, above_water=above_water,
                editions=editions, clearest=clearest,
                nadir_fq=nadir_fq, shallow=shallow, caught=caught)


if __name__ == "__main__":
    main()

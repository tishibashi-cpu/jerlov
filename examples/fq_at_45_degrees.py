"""Where does the dip at a sun of 45 degrees in Morel et al.'s f/Q tables lie?

An open question, with numbers (OPEN_QUESTIONS.md, question 6). For those
who correct water-leaving radiance for the sun and the view with Morel,
Antoine & Gentili's (2002) f/Q tables:

    python examples/fq_at_45_degrees.py --archive PATH [--ocssw DIR]

PATH is your own copy of the authors' archive, DISTRIB_fQ_with_Raman.tar.gz
(DATA.md section 48); the package does not ship it, and without it this
example says so and stops. With it, the example finds where f.dat and the
f/Q tables leave the line between their neighbouring sun angles, and
whether one run of the table is out of line with the others
(DECISIONS.md section 116). With --ocssw DIR, the folder holding NASA's
OCSSW copies of the tables and the authors' later recomputation, it sets
the archive against those too (section 117; needs h5py).
"""

import sys
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


#: A departure from the chord larger than this, percent, counts as a dip.
DIP = 1.0


def read(path):
    with warnings.catch_warnings():
        # Since 1.26.3 the tables warn at the run this example finds
        # (DATA.md section 48); finding it is what the example is for.
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        tables = jerlov.morel2002_fq_tables(path)
        suns = np.asarray(tables.sun_zenith_deg)
        wl, chl = tables.wavelengths_nm, tables.chlorophyll_mg_m3
        nadirs, azimuths = tables.nadir_deg, tables.azimuth_deg
        f = np.array([[[tables.f(w, sun_zenith_deg=s, chlorophyll_mg_m3=c)
                        for s in suns] for c in chl] for w in wl])
        foq = np.array([[[[[tables.f_over_q(
            w, sun_zenith_deg=s, chlorophyll_mg_m3=c, nadir_deg=n,
            azimuth_deg=a) for a in azimuths] for n in nadirs]
            for s in suns] for c in chl] for w in wl])
    return dict(suns=suns, wl=wl, chl=chl, f=f, foq=foq)


def chord(values, x, i):
    """Percent departure of values[..., i] from the chord between i - 1 and
    i + 1, in x."""
    line = values[..., i - 1] + (values[..., i + 1] - values[..., i - 1]) * (
        (x[i] - x[i - 1]) / (x[i + 1] - x[i - 1]))
    return 100 * (values[..., i] / line - 1)


def where_part(t):
    rule("1. Where f and f/Q leave the line between neighbouring sun angles")
    x = 1 - np.cos(np.radians(t["suns"]))
    f = t["f"]                                     # (wl, chl, sun)
    foq = np.moveaxis(t["foq"], 2, -1)             # (wl, chl, n, az, sun)
    q_nadir = f / t["foq"][:, :, :, 0, 0]          # (wl, chl, sun)
    out = {}
    print(f"Percent from the chord in 1 - cos(theta_s), over the {f.shape[0] * f.shape[1]} "
          "(wavelength, Chl)\ncases; f/Q over all directions too:\n")
    print(f"  {'sun':>4}  {'f':>16}  {'f/Q, every view':>18}  {'Q at nadir':>16}")
    for i in range(1, len(x) - 1):
        df = chord(f, x, i)
        dq = chord(foq, x, i)
        dn = chord(q_nadir, x, i)
        out[t["suns"][i]] = dict(f=(df.min(), df.max()), foq=(dq.min(), dq.max()),
                                 q=(dn.min(), dn.max()))
        print(f"  {t['suns'][i]:>4g}  {df.min():+6.2f} to {df.max():+5.2f}  "
              f"{dq.min():+7.2f} to {dq.max():+5.2f}  "
              f"{dn.min():+6.2f} to {dn.max():+5.2f}")
    at45 = list(t["suns"]).index(45.0)
    d45 = chord(f, x, at45)                        # (wl, chl)
    below = np.argwhere(d45 < -DIP)
    rows = sorted({int(c) for _, c in below})
    print(f"\nf at 45 degrees, percent from the chord, by wavelength (rows) and "
          f"Chl (columns,\n{', '.join(f'{c:g}' for c in t['chl'])} mg/m3):\n")
    for w, row in zip(t["wl"], d45):
        print(f"  {w:>6g}" + "".join(f" {v:+6.2f}" for v in row))
    low = d45[:, rows[0]] if len(rows) == 1 else None
    others = np.delete(d45, rows, axis=1)
    dq45 = chord(foq, x, at45)                     # (wl, chl, n, az)
    medians = np.median(dq45.reshape(dq45.shape[0], dq45.shape[1], -1),
                        axis=2)                    # (wl, chl), over views
    out.update(dip_columns=[t["chl"][c] for c in rows],
               dip_range=(low.min(), low.max()) if low is not None else None,
               growing=bool(low is not None and np.all(np.diff(low) < 0)),
               others=(others.min(), others.max()),
               foq_median_at_dip=(medians[:, rows[0]].min(),
                                  medians[:, rows[0]].max())
               if low is not None else None,
               foq_median_others=(np.delete(medians, rows, axis=1).min(),
                                  np.delete(medians, rows, axis=1).max()),
               q45=out[45.0]["q"], f60=out[60.0]["f"])
    d30 = chord(f, x, list(t["suns"]).index(30.0))
    out["alone_at_30"] = bool(low is not None and np.all(d30[:, rows[0]] > 0)
                              and np.all(np.delete(d30, rows, axis=1) < 0))
    if low is not None:
        grows = ("growing with the wavelength" if out["growing"]
                 else "not in order of wavelength")
        print(f"""
Below the chord by more than {DIP:g} percent: only Chl {t['chl'][rows[0]]:g} mg/m3, at all
{len(t['wl'])} wavelengths, {-low.max():.2f} to {-low.min():.2f} percent, {grows}. Every
other Chl lies {out['others'][0]:+.2f} to {out['others'][1]:+.2f} percent from it. The f/Q tables move with f:
taking for each case the median over its 221 directions, f/Q at that Chl and
45 degrees lies {out['foq_median_at_dip'][0]:+.2f} to {out['foq_median_at_dip'][1]:+.2f} percent from its chord, at the other Chl
{out['foq_median_others'][0]:+.2f} to {out['foq_median_others'][1]:+.2f}. Q at the nadir, f over f/Q, lies {out['q45'][0]:+.2f} to {out['q45'][1]:+.2f}
percent from its chord at 45 degrees: no dip. (At 30 degrees Chl {t['chl'][rows[0]]:g} {'alone' if out['alone_at_30'] else 'too'}
lies above its chord, which has the low value at 45 as an end; at 60
every case lies {out['f60'][0]:+.2f} to {out['f60'][1]:+.2f} above, as f bends towards 75 degrees.)""")
    return out


def neighbour_part(t):
    rule("2. Against the next Chl")
    f = t["f"]
    suns = t["suns"]
    shape = f / f[:, :, :1]                        # f(theta_s) / f(0)
    ratio = shape[:, :-1] / shape[:, 1:]           # Chl over the next Chl
    out_of_order = []
    for k in range(ratio.shape[1]):
        for j in range(ratio.shape[0]):
            r = ratio[j, k]
            for i in range(1, len(suns) - 1):
                if r[i] < r[i + 1] - 1e-12 and r[i] < r[i - 1]:
                    out_of_order.append((t["wl"][j], t["chl"][k],
                                         t["chl"][k + 1], suns[i], r))
    pairs = sorted({(c1, c2, s) for _, c1, c2, s, _ in out_of_order})
    print("""f(theta_s)/f(0) at one Chl over the same at the next Chl, at each
wavelength. A sun angle where it falls below its value at the next larger
angle, and below the one before, is out of order:
""")
    for c1, c2, s in pairs:
        n = sum(1 for _, a, b, z, _ in out_of_order if (a, b, z) == (c1, c2, s))
        print(f"  Chl {c1:g} over {c2:g}, sun {s:g} degrees: at {n} of "
              f"{len(t['wl'])} wavelengths")
    j = list(t["wl"]).index(660.0)
    k = list(t["chl"]).index(0.03)
    example = ratio[j, k]
    print(f"""
At 660 nm, Chl 0.03 over 0.1: {', '.join(f'{v:.4f}' for v in example)} at
{', '.join(f'{s:g}' for s in suns)} degrees.""")
    return dict(pairs=pairs, count=len(out_of_order), example=example)


#: NASA's OCSSW files (DECISIONS.md section 117): the archive's tables in
#: netCDF, and Gentili's later tables at 70 wavelengths.
OCSSW_ARCHIVE = "morel_fq.nc"
OCSSW_HYPERSPECTRAL = "morel_fq_hyperspectral_2026.nc"


def _read_nadir(path):
    import h5py    # only for this part, which the package does not need

    with h5py.File(path, "r") as f:
        return (f["wave"][()].astype(float), f["chl"][()].astype(float),
                f["solz"][()].astype(float),
                f["foq"][()][:, :, :, 0, 0].astype(float))


def ocssw_part(t, directory):
    rule("3. Against the authors' later tables, as NASA distributes them")
    import pathlib

    folder = pathlib.Path(directory)
    suns = t["suns"]
    x = 1 - np.cos(np.radians(suns))
    archive = t["foq"][:, :, :, 0, 0]              # (wl, chl, sun)
    w0, c0, s0, netcdf = _read_nadir(folder / OCSSW_ARCHIVE)
    w1, c1, s1, hyper = _read_nadir(folder / OCSSW_HYPERSPECTRAL)
    assert list(s0) == list(s1) == list(suns)
    netcdf = np.moveaxis(netcdf, 1, 2)             # (wl, chl, sun)
    same = float(np.max(np.abs(netcdf - archive)))
    hyper_at = np.array([[[np.interp(w, w1, hyper[:, s, c])
                           for s in range(len(suns))]
                          for c in range(len(c1))] for w in t["wl"]])
    i45 = list(suns).index(45.0)
    own = chord(hyper_at, x, i45)                  # (wl, chl)
    ratio = hyper_at / archive
    against = chord(ratio, x, i45)                 # (wl, chl)
    k = list(t["chl"]).index(0.03)
    rest = np.delete(against, k, axis=1)
    out = dict(
        same=same, own_dip=(own[:, k].min(), own[:, k].max()),
        own_next=(own[:, k + 1].min(), own[:, k + 1].max()),
        level=(100 * (ratio.min() - 1), 100 * (ratio.max() - 1)),
        against=(against[:, k].min(), against[:, k].max()),
        against_rest=(rest.min(), rest.max()),
        red=(against[:, k].argmax() == len(t["wl"]) - 1),
        waves=(w1.min(), w1.max(), len(w1)))
    print(f"""NASA's OCSSW distributes the archive's tables as {OCSSW_ARCHIVE}, which agrees
with your archive's nadir f/Q to {same:.1e} at most, and {OCSSW_HYPERSPECTRAL},
"f and Q tables derived hyperspectrally by Bernard Gentili", one of the
paper's authors: {out['waves'][2]} wavelengths from {out['waves'][0]:g} to {out['waves'][1]:g} nm, the same sun
angles and Chl. Nadir f/Q at 45 degrees, percent from the chord between
30 and 60, and the ratio later/archive at 45 against its own chord:
""")
    print(f"  {'nm':>6} {'later, 0.03':>12} {'later, 0.1':>11} {'ratio, 0.03':>12} "
          f"{'ratio, other Chl':>18}")
    for j, w in enumerate(t["wl"]):
        others = np.delete(against[j], k)
        print(f"  {w:>6g} {own[j, k]:>+12.2f} {own[j, k + 1]:>+11.2f} "
              f"{against[j, k]:>+12.2f} {others.min():>+8.2f} to {others.max():+.2f}")
    print(f"""
The later tables have no dip: at 0.03 mg/m3 their nadir f/Q lies
{out['own_dip'][0]:+.2f} to {out['own_dip'][1]:+.2f} percent from its chord, at 0.1 {out['own_next'][0]:+.2f} to {out['own_next'][1]:+.2f}. They
differ from the archive by {out['level'][0]:+.1f} to {out['level'][1]:+.1f} percent over all runs, but along the
sun angle they follow it except at the one run: there the ratio stands
{out['against'][0]:+.2f} to {out['against'][1]:+.2f} percent above its chord, at every other Chl
{out['against_rest'][0]:+.2f} to {out['against_rest'][1]:+.2f}. The authors' own later computation does not have
the dip; what went wrong in the archive's run is not known.""")
    return out


def main(archive=None, ocssw=None):
    _banner()
    if not archive:
        print("""
This example needs your own copy of Morel et al.'s archive,
DISTRIB_fQ_with_Raman.tar.gz (DATA.md section 48), given as --archive PATH.
The package does not ship it. Nothing else is done.""")
        return None
    t = read(archive)
    where = where_part(t)
    neighbours = neighbour_part(t)
    later = None
    if ocssw:
        later = ocssw_part(t, ocssw)
    else:
        print("""
Part 3 compares the archive with the authors' later tables, which NASA's
OCSSW distributes; give the folder holding morel_fq.nc and
morel_fq_hyperspectral_2026.nc as --ocssw DIR (DECISIONS.md section 117).
It needs h5py, which the package does not.""")
    rule("Before you use any of this")
    print("""  - The chord is a straight line in 1 - cos(theta_s), the variable the
    paper's own fits are linear in up to 60 degrees; f bends away from it
    towards 75 degrees at every Chl, which is not a dip.
  - What made the one run out of line is not known. The paper computes
    Raman emission in every run; the archive gives only the totals, so
    nothing here can tell whether it is that part.
""")
    return dict(where=where, neighbours=neighbours, later=later)


if __name__ == "__main__":
    # Only an explicit --archive PATH is read: run through runpy from
    # "python -c", as CI runs the examples, sys.argv carries this script's
    # own path, which must not be taken for the archive.
    args = sys.argv[1:]

    def option(name):
        return args[args.index(name) + 1] if name in args[:-1] else None

    main(option("--archive"), option("--ocssw"))

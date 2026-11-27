"""Why does the shallow-water reflectance model miss two groups of runs?

An open question, with numbers (OPEN_QUESTIONS.md, question 5). For those
who model or invert the reflectance of shallow water, with the bottom in
view:

    python examples/shallow_water_closure.py

`lee1999_shallow_rrs` (Lee et al. 1998, 1999) was set against a Monte
Carlo in 270 runs, and missed by more than 10 percent in two groups: where
pure water carries most of the backscattering, and over a black bottom a
few metres down in turbid water (DATA.md section 50). HydroLight, which
the model was fitted to, is not available here. This example rebuilds the
waters of the paper's own runs, then reads further Monte Carlo runs, each
changing one thing, and works out which change moves each group and by
how much (DECISIONS.md section 114). Part 5 holds bb/b and changes only
the shape, with Fournier-Forand phase functions (section 134). The runs
are in
examples/data/shallow_rrs_mc/, written by tools/shallow_rrs_mc.py and
tools/lee1998_runs.py; the example needs the repository for them, but
nothing beyond the package and NumPy.
"""

import csv
import math
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


DATA = pathlib.Path(__file__).resolve().parent / "data" / "shallow_rrs_mc"
#: A run "misses" when model over Monte Carlo is off by more than this.
MISS = 0.1
#: The 1998 constants (Lee et al. 1998, Eqs. 16, 19-21), which the 1999
#: paper replaced; used here only to compare.
LEE1998 = dict(g=(0.070, 0.155, 0.752), a0=1.03, d=(1.2, 2.0))
#: The finite depths of the 1998 paper's runs, m (Table 1).
DEPTHS_1998 = np.array([0.5, 1.0, 3.0, 8.0, 16.0, 32.0])
N_WATER = 1.34


def read(name):
    with open(DATA / name) as handle:
        rows = list(csv.DictReader(handle))
    out = {}
    for key in rows[0]:
        try:
            out[key] = np.array([float(r[key]) for r in rows])
        except ValueError:
            out[key] = np.array([r[key] for r in rows])
    return out


def mu_w(sun_deg):
    return np.sqrt(1.0 - (np.sin(np.radians(sun_deg)) / N_WATER) ** 2)


def column_1998(a, bb, depth, sun_deg):
    """The 1998 paper's column term (its Eq. 21 with a black bottom)."""
    u = bb / (a + bb)
    g0, g1, g2 = LEE1998["g"]
    d0, d1 = LEE1998["d"]
    deep = (g0 + g1 * u ** g2) * u
    return deep * (1.0 - LEE1998["a0"] * np.exp(
        -(1.0 / mu_w(sun_deg) + d0 * np.sqrt(1.0 + d1 * u))
        * (a + bb) * depth))


def groups(grid):
    q = grid["model"] / grid["monte_carlo"]
    ratio = grid["bp"] / grid["a"]
    miss = np.abs(q - 1) > MISS
    water = miss & np.isclose(ratio, 0.3)
    dark = miss & (grid["albedo"] == 0.0) & ~np.isclose(ratio, 0.3)
    return q, water, dark


def paper_part():
    rule("1. The waters of the paper's runs, rebuilt")
    runs = read("lee1998_runs.csv")
    grid = read("monte_carlo.csv")
    q, water, dark = groups(grid)
    missed = (q[water].min(), q[water].max())
    kappa = runs["a"] + runs["bb"]
    turbid = runs["u"] > 0.3
    share = 0.5 * grid["bw"] / grid["bb"]
    grid_kappa = grid["a"] + grid["bb"]
    # Each run of the second group against the paper's runs of nearly the
    # same u (within 20 percent): the kappa H their depths gave.
    covered = 0
    for i in np.flatnonzero(dark):
        near = np.abs(np.log(runs["u"] / grid["u"][i])) < np.log(1.2)
        kh = np.outer(kappa[near], DEPTHS_1998).ravel()
        kh_run = grid_kappa[i] * grid["depth_m"][i]
        covered += int(kh.size > 0 and kh.min() <= kh_run <= kh.max())
    out = dict(u=(runs["u"].min(), runs["u"].max()),
               a=(runs["a"].min(), runs["a"].max()),
               share_max=runs["water_share"].max(),
               turbid_kappa_min=kappa[turbid].min(),
               water_shares=sorted(set(np.round(share[water], 2))),
               dark_kh=(np.min(grid_kappa[dark] * grid["depth_m"][dark]),
                        np.max(grid_kappa[dark] * grid["depth_m"][dark])),
               covered=covered, dark=int(dark.sum()), missed=missed)
    beyond = [s for s in out["water_shares"] if s > out["share_max"]]
    print(f"""From Table 1 and Eqs. (12)-(15) of the 1998 paper, with Pope & Fry's pure
water and Morel's pure sea water at 35 psu: {len(runs['a'])} sets of IOPs. In them
u runs from {out['u'][0]:.4f} to {out['u'][1]:.3f} and a from {out['a'][0]:.3f} to {out['a'][1]:.3f} 1/m; pure water's
share of bb is at most {out['share_max']:.2f}. Where u is above 0.3, kappa is at least
{out['turbid_kappa_min']:.3f} 1/m, so kappa H at least {0.5 * out['turbid_kappa_min']:.3f} at the shallowest bottom, 0.5 m.

The Monte Carlo's first group ({int(water.sum())} runs) has pure water's share of bb at
{', '.join(f'{s:g}' for s in out['water_shares'])}; {len(beyond)} of these {'is' if len(beyond) == 1 else 'are'} beyond the paper's largest. The second
group ({out['dark']} runs, a black bottom) has kappa H from {out['dark_kh'][0]:.3f} to {out['dark_kh'][1]:.3f}. For {out['covered']} of
its {out['dark']} runs, the paper's runs of nearly the same u (within 20 percent) at its
depths of 0.5 to 32 m spanned that kappa H: the second group lies, by these
two measures, among the paper's waters.""")
    return out


def share_part(missed, shares_missed):
    rule("2. Pure water's share of the backscattering, alone")
    runs = read("water_share.csv")
    q = runs["model"] / runs["monte_carlo"]
    shares = sorted(set(runs["water_share"]))
    print("Model over Monte Carlo, the sun at 30 degrees, u and a held, a black bottom\n"
          "at 4 m or none, by pure water's share of bb:\n")
    print(f"  {'u':>6} {'a':>5} {'H':>5}" + "".join(f" {s:>6g}" for s in shares))
    keys = sorted(set(zip(runs["u"], runs["a"], runs["depth_m"])))
    falling = 0
    for key in keys:
        pick = ((runs["u"] == key[0]) & (runs["a"] == key[1])
                & (runs["depth_m"] == key[2]))
        order = np.argsort(runs["water_share"][pick])
        row = q[pick][order]
        falling += int(row[-1] < row[0])
        depth = "none" if not np.isfinite(key[2]) else f"{key[2]:g} m"
        print(f"  {key[0]:>6g} {key[1]:>5g} {depth:>5}"
              + "".join(f" {x:>6.3f}" for x in row))
    at_their = []
    for key in keys:
        pick = ((runs["u"] == key[0]) & (runs["a"] == key[1])
                & (runs["depth_m"] == key[2]))
        order = np.argsort(runs["water_share"][pick])
        at_their += list(np.interp(shares_missed,
                                   runs["water_share"][pick][order],
                                   q[pick][order]))
    at_zero = q[runs["water_share"] == 0.0]
    at_most = q[runs["water_share"] == max(shares)]
    inside = q[runs["water_share"] <= 0.4]
    out = dict(zero=(at_zero.min(), at_zero.max()),
               most=(at_most.min(), at_most.max()),
               inside=(inside.min(), inside.max()),
               falling=falling, cases=len(keys),
               at_their=(min(at_their), max(at_their)))
    print(f"""
The ratio is lower at a share of 0.95 than at 0 in {falling} of the {len(keys)} cases: from
{out['zero'][0]:.3f}-{out['zero'][1]:.3f} with particles alone to {out['most'][0]:.3f}-{out['most'][1]:.3f} with pure water nearly alone.
Read off these runs at the first group's shares, {', '.join(f'{x:g}' for x in shares_missed)}, the ratio is
{out['at_their'][0]:.3f} to {out['at_their'][1]:.3f}; the group's misses are {missed[0]:.3f} to {missed[1]:.3f}. But up to a share of
0.4, within the paper's runs, the ratio is still {out['inside'][0]:.3f} to {out['inside'][1]:.3f}, not
within the 5 percent the plan asked. So pure water's share accounts for the
direction of the first group's miss: the model, a function of u alone in
deep water, gives the same rrs whoever does the backscattering, and the
Monte Carlo does not. The scatter that remains at small shares is not
accounted for here; the particles' phase function (NUC 2240 here,
Petzold's average in the paper) is one candidate, not tested in deep
water.""")
    return out


def dark_part():
    rule("3. The black bottom: three changes, each alone")
    grid = read("monte_carlo.csv")
    changed = read("black_bottom.csv")
    q, _, dark = groups(grid)
    ratio = grid["bp"] / grid["a"]
    cells = ((grid["albedo"] == 0.0) & np.isin(grid["depth_m"], (1.0, 4.0))
             & np.isin(np.round(ratio), (3.0, 30.0))
             & np.isin(grid["a"], (0.05, 0.2)))

    def key_of(a, r, h, s):
        return (round(float(a), 4), round(float(r)), float(h), float(s))

    base = {key_of(grid["a"][i], ratio[i], grid["depth_m"][i],
                   grid["sun_deg"][i]): i for i in np.flatnonzero(cells)}
    in_group = {k for k, i in base.items() if dark[i]}
    results = {"none": {k: q[i] for k, i in base.items()}}
    for change in sorted(set(changed["change"])):
        pick = changed["change"] == change
        results[change] = {
            key_of(a, r, h, s): m / mc for a, r, h, s, m, mc in zip(
                changed["a"][pick], changed["bp_over_a"][pick],
                changed["depth_m"][pick], changed["sun_deg"][pick],
                changed["model"][pick], changed["monte_carlo"][pick])}
    old = {}
    for k, i in base.items():
        old[k] = float(column_1998(grid["a"][i], grid["bb"][i],
                                   grid["depth_m"][i], grid["sun_deg"][i])
                       / grid["monte_carlo"][i])
    results["1998 constants"] = old
    labels = {"none": "none (section 113)",
              "AUTEC 8": "particles: AUTEC 8",
              "HAOCE 11": "particles: HAOCE 11",
              "sky": "30 percent sky",
              "1998 constants": "model: 1998 constants"}
    print(f"""Model over Monte Carlo for a black bottom at 1 or 4 m, bp/a 3 or 30, a 0.05
or 0.2 1/m and the sun at 0, 30 and 60 degrees ({len(base)} cells, of which the
second group's {len(in_group)} runs are part). Within {100 * MISS:g} percent:
""")
    counts = {}
    print(f"  {'change':<24} {'group':>7} {'cells':>7} {'range':>14}")
    for change in ("none", "AUTEC 8", "HAOCE 11", "sky", "1998 constants"):
        values = results[change]
        group = sum(abs(values[k] - 1) <= MISS for k in in_group)
        every = sum(abs(v - 1) <= MISS for v in values.values())
        lo, hi = min(values.values()), max(values.values())
        counts[change] = (group, every, lo, hi)
        print(f"  {labels[change]:<24} {group:>3} / {len(in_group):<3}"
              f"{every:>3} / {len(base):<3}  {lo:.3f}-{hi:.3f}")
    # The column's attenuation the Monte Carlo implies.
    rows = []
    excess = []
    for k, i in sorted(base.items()):
        deep = np.flatnonzero((grid["a"] == grid["a"][i])
                              & (grid["bp"] == grid["bp"][i])
                              & ~np.isfinite(grid["depth_m"])
                              & (grid["sun_deg"] == grid["sun_deg"][i]))[0]
        part = grid["monte_carlo"][i] / grid["monte_carlo"][deep]
        if part >= 1:
            noise = math.hypot(grid["standard_error"][i],
                               grid["standard_error"][deep])
            excess.append((grid["monte_carlo"][i] - grid["monte_carlo"][deep])
                          / noise)
        kh = (grid["a"][i] + grid["bb"][i]) * grid["depth_m"][i]
        u = grid["u"][i]
        model_d = 1 / mu_w(grid["sun_deg"][i]) + 1.03 * math.sqrt(1 + 2.4 * u)
        mc_d = -math.log(1 - part) / kh if part < 1 else math.nan
        rows.append((kh, mc_d, model_d))
    rows.sort()
    small = [r for r in rows if r[0] < 0.1]
    large = [r for r in rows if r[0] > 0.5 and np.isfinite(r[1])]
    out = dict(counts=counts, group=len(in_group), cells=len(base),
               small=(min(r[1] / r[2] for r in small),
                      max(r[1] / r[2] for r in small)),
               large=(min(r[1] / r[2] for r in large),
                      max(r[1] / r[2] for r in large)),
               beyond=sum(1 for r in rows if not np.isfinite(r[1])),
               excess=max(excess) if excess else 0.0)
    accounted = [c for c in ("AUTEC 8", "HAOCE 11", "sky")
                 if counts[c][0] >= 10]
    stations = ("none", "AUTEC 8", "HAOCE 11")
    spread = [max(results[c][k] for c in stations)
              / min(results[c][k] for c in stations) for k in base]
    out["spread"] = (float(np.median(spread)), max(spread))
    sky = [max(results[c][k] for c in ("none", "sky"))
           / min(results[c][k] for c in ("none", "sky")) for k in base]
    out["sky_spread"] = (float(np.median(sky)), max(sky))
    print(f"""
With a black bottom the column's share of the deep-water rrs is 1 - exp(-D
kappa H) in the model, D = 1/cos theta_w + 1.03 (1 + 2.4 u)^0.5. The D the
Monte Carlo implies, against the model's: {out['small'][0]:.2f} to {out['small'][1]:.2f} of it where kappa H
is below 0.1, {out['large'][0]:.2f} to {out['large'][1]:.2f} where it is above 0.5. In {out['beyond']} cell{'' if out['beyond'] == 1 else 's'} the
Monte Carlo gives more than for deep water, by {out['excess']:.1f} times the standard error
of the difference at most, and no D can be taken. So the model's single
exponential agrees with the Monte Carlo where kappa H is above 0.5, and
where it is below 0.1 makes the column's share grow with depth faster than
the Monte Carlo does.

{'Changes that bring at least 10 of the group within 10 percent: ' + ', '.join(accounted) + '.' if accounted else 'No change to the Monte Carlo brings 10 of the group within 10 percent,'}
{'' if accounted else 'the measure the plan set.'}
In the same cell, with a, bb and pure water's part the same, changing the
station alone (NUC 2240, AUTEC 8, HAOCE 11) changes the ratio by a factor
of {out['spread'][0]:.2f} in the median cell and {out['spread'][1]:.2f} at the most; adding the sky, by
{out['sky_spread'][0]:.2f} and {out['sky_spread'][1]:.2f}. Over a black bottom in shallow water
the column's rrs depends on the phase function, which the model, a
function of u and kappa H, does not take; which phase function HydroLight's
runs are nearest to, here, is not known. The 1998 constants, with their
A0 of 1.03, bring {counts['1998 constants'][0]} of the {len(in_group)}.""")
    out["accounted"] = accounted
    return out


#: Section 115: the stations' backscatter shares as the Monte Carlo's
#: sampler has them (tools/shallow_rrs_mc.py, petzold_phase), read from the
#: runs themselves where they are stored.
STATIONS = ("NUC 2240", "AUTEC 8", "HAOCE 11")


def separated_part():
    rule("4. Water and particles apart, and what orders the black-bottom miss")
    runs = read("water_share_nadir.csv")
    coefficients = jerlov.LEE2011_RRS_COEFFICIENTS[(0.0, 0.0, 0.0)]
    rrs_2011 = []
    for a, bb, bw in zip(runs["a"], runs["bb"], runs["bw"]):
        above = jerlov.lee2011_rrs(a, bb, bb_water=bw / 2,
                                   coefficients=coefficients)
        rrs_2011.append(above / (0.52 + 1.7 * above))
    q1999 = runs["model"] / runs["monte_carlo"]
    q2011 = np.array(rrs_2011) / runs["monte_carlo"]
    print("""Deep water, the sun at the zenith, viewed straight down; u held and pure
water's share of bb varied (18 runs). Lee et al. (2011) keep water and
particles apart; their Rrs is taken below the surface by Lee et al.'s
(2002) Eq. (8), an assumption. Model over Monte Carlo, and its spread
(largest over smallest) across the shares:
""")
    shares = sorted(set(runs["water_share"]))
    print(f"  {'u':>6} {'model':<11}" + "".join(f" {x:>6g}" for x in shares)
          + "  spread")
    spreads = {}
    for u in sorted(set(runs["u"])):
        pick = runs["u"] == u
        order = np.argsort(runs["water_share"][pick])
        for name, q in (("1999", q1999), ("2011", q2011)):
            row = q[pick][order]
            spreads[(u, name)] = row.max() / row.min()
            print(f"  {u:>6g} {'Lee ' + name:<11}"
                  + "".join(f" {x:>6.3f}" for x in row)
                  + f"  {spreads[(u, name)]:.3f}")
    us = sorted(set(runs["u"]))
    fraction = [(spreads[(u, '2011')] - 1) / (spreads[(u, '1999')] - 1)
                for u in us]
    out = dict(q2011=(q2011.min(), q2011.max()),
               spread_2011=(min(spreads[(u, '2011')] for u in us),
                            max(spreads[(u, '2011')] for u in us)),
               spread_1999=(min(spreads[(u, '1999')] for u in us),
                            max(spreads[(u, '1999')] for u in us)),
               fraction=(min(fraction), max(fraction)))
    print(f"""
Across pure water's share, Lee et al.'s (2011) separated form moves by
{out['spread_2011'][0]:.3f} to {out['spread_2011'][1]:.3f} times against the Monte Carlo, the 1999 model by {out['spread_1999'][0]:.3f} to {out['spread_1999'][1]:.3f}:
the separated form's excess over 1 is {out['fraction'][0]:.2f} to {out['fraction'][1]:.2f} of the 1999 model's. With
the surface taken as assumed, it lies at {out['q2011'][0]:.3f} to {out['q2011'][1]:.3f} of the Monte Carlo.
It is a deep-water form; this package has no shallow-water model that
keeps water and particles apart.""")

    grid = read("monte_carlo.csv")
    changed = read("black_bottom.csv")
    cut = read("cut_check.csv")
    back = {}
    for station in STATIONS:
        pick = (cut["station"] == station) & (cut["cut_deg"] == 1.0)
        back[station] = float(cut["backscatter_share"][pick][0])
    by_back = sorted(STATIONS, key=back.get)
    ratio = grid["bp"] / grid["a"]
    cells = {}
    for i in np.flatnonzero((grid["albedo"] == 0.0)
                            & np.isin(grid["depth_m"], (1.0, 4.0))
                            & np.isin(np.round(ratio), (3.0, 30.0))
                            & np.isin(grid["a"], (0.05, 0.2))):
        key = (grid["a"][i], round(ratio[i]), grid["depth_m"][i],
               grid["sun_deg"][i])
        cells[key] = {"NUC 2240": grid["model"][i] / grid["monte_carlo"][i]}
    for j in range(len(changed["a"])):
        if changed["change"][j] in back:
            key = (changed["a"][j], round(changed["bp_over_a"][j]),
                   changed["depth_m"][j], changed["sun_deg"][j])
            cells[key][changed["change"][j]] = (changed["model"][j]
                                                / changed["monte_carlo"][j])
    rising = falling = middle_highest = 0
    for values in cells.values():
        steps = np.diff([values[s] for s in by_back])
        rising += int(np.all(steps > 0))
        falling += int(np.all(steps < 0))
        middle_highest += int(values[by_back[1]] == max(values.values()))
    spread_by_cut = {
        station: (cut["model"][cut["station"] == station]
                  / cut["monte_carlo"][cut["station"] == station])
        for station in STATIONS}
    worst = max(v.max() / v.min() for v in spread_by_cut.values())
    cut_cell = (cut["a"][0], round(cut["bp_over_a"][0]), cut["depth_m"][0],
                cut["sun_deg"][0])
    at_cut_cell = max(cells[cut_cell].values()) / min(cells[cut_cell].values())
    largest = max(max(v.values()) / min(v.values()) for v in cells.values())
    with warnings.catch_warnings():
        # The mean cosine rests on the report's extension below 0.1 degree,
        # which always warns (DATA.md section 21).
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        cosine = {st: float(jerlov.petzold_scattering(st).mean_cosine())
                  for st in STATIONS}
    cosine_falls = all(cosine[a] > cosine[b]
                       for a, b in zip(by_back, by_back[1:]))
    noise = max((cut["standard_error"] / cut["monte_carlo"]))
    out.update(cells=len(cells), rising=rising, falling=falling,
               middle=middle_highest, back=back, by_back=by_back,
               cut_spread=worst, cut_noise=noise, at_cut_cell=at_cut_cell,
               largest=largest, cosine=cosine, cosine_falls=cosine_falls)
    print(f"""
Over a black bottom, the {len(cells)} cells of part 3 with the particles' bb/b
{', '.join(f'{back[s]:.4f} ({s})' for s in by_back)}: model over Monte
Carlo rises with bb/b in {rising} cells and falls in {falling}; in {middle_highest} the middle
station, {by_back[1]}, gives the highest. The miss is not ordered by bb/b,
nor by the mean cosine ({', '.join(f'{cosine[s]:.4f}' for s in by_back)}{', which falls as bb/b rises' if cosine_falls else ''}).
The Monte Carlo counts scattering by less than 1 degree as none. In the
cell with a {cut_cell[0]:g} 1/m, bp/a {cut_cell[1]:g}, H {cut_cell[2]:g} m and the sun at {cut_cell[3]:g} degrees,
where the stations differ by a factor of {at_cut_cell:.2f} ({largest:.2f} in the cell where
they differ most), a cut of 0.5, 1 or 2 degrees moves the ratio at any
one station by a factor of {worst:.3f} at most, with standard errors up to
{100 * noise:.1f} percent: the cut is not what sets the stations apart.""")
    return out


def ranks(values):
    order = np.argsort(values)
    out = np.empty(len(values))
    out[order] = np.arange(len(values))
    return out


def spearman(x, y):
    """Spearman's rank correlation, for values without ties."""
    rx, ry = ranks(np.asarray(x)), ranks(np.asarray(y))
    n = len(rx)
    return 1 - 6 * float(np.sum((rx - ry) ** 2)) / (n * (n * n - 1))


#: The measures set in DECISIONS.md section 134 before the runs.
SAME_WITHIN = 0.05
SAME_SE = 3.0
FIX_NEEDED = 54
ORDER_NEEDED = 20
RHO_NEEDED = 0.9


def fournier_part():
    rule("5. The shape apart from bb/b: Fournier-Forand phase functions")
    ff = read("fournier_forand.csv")
    grid = read("monte_carlo.csv")
    changed = read("black_bottom.csv")

    def key(a, r, h, s):
        return (round(float(a), 4), round(float(r)), float(h), float(s))

    station_mc = {}
    ratio = grid["bp"] / grid["a"]
    for i in np.flatnonzero(grid["albedo"] == 0.0):
        station_mc[key(grid["a"][i], ratio[i], grid["depth_m"][i],
                       grid["sun_deg"][i]) + ("NUC 2240",)] = (
            grid["monte_carlo"][i], grid["standard_error"][i])
    for j in range(len(changed["a"])):
        if changed["change"][j] in STATIONS:
            station_mc[key(changed["a"][j], changed["bp_over_a"][j],
                           changed["depth_m"][j], changed["sun_deg"][j])
                       + (changed["change"][j],)] = (
                changed["monte_carlo"][j], changed["standard_error"][j])
    cells = {}
    for j in range(len(ff["a"])):
        k = key(ff["a"][j], ff["bp_over_a"][j], ff["depth_m"][j],
                ff["sun_deg"][j])
        st = ff["station"][j]
        mc_s, se_s = station_mc[k + (st,)]
        cells.setdefault(k, {})[st] = dict(
            back=ff["backscatter_share"][j], model=ff["model"][j],
            ff=ff["monte_carlo"][j], ff_se=ff["standard_error"][j],
            station=mc_s, station_se=se_s,
            p_ff=ff["p_back_ff"][j], p_station=ff["p_back_station"][j])
    # 1. Does bb/b fix the rrs?
    pairs = [(r["ff"] / r["station"],
              abs(r["ff"] - r["station"])
              / math.hypot(r["ff_se"], r["station_se"]))
             for c in cells.values() for r in c.values()]
    same = sum(abs(q - 1) <= SAME_WITHIN or z <= SAME_SE for q, z in pairs)
    by_station = {st: [c[st]["ff"] / c[st]["station"] for c in cells.values()]
                  for st in STATIONS}
    # 2. Within the Fournier-Forands, model over Monte Carlo against bb/b.
    order = sorted(STATIONS, key=lambda s: next(iter(cells.values()))[s]
                   ["back"])
    rising = falling = 0
    for c in cells.values():
        steps = np.diff([c[s]["model"] / c[s]["ff"] for s in order])
        rising += int(np.all(steps > 0))
        falling += int(np.all(steps < 0))
    # 3. The phase function at the angle of single scattering.
    rho = {}
    for k, c in cells.items():
        p = [c[s]["p_station"] for s in STATIONS] + [c[s]["p_ff"]
                                                     for s in STATIONS]
        mc = [c[s]["station"] for s in STATIONS] + [c[s]["ff"]
                                                    for s in STATIONS]
        rho[k] = spearman(p, mc)
    ordered = sum(v >= RHO_NEEDED for v in rho.values())
    by_sun = {s: [v for k, v in rho.items() if k[3] == s]
              for s in sorted({k[3] for k in rho})}
    print(f"""Petzold's stations differ in bb/b and in shape at once. A Fournier-Forand
on Mobley et al.'s line with each station's backscatter share, and the
station's bp, keeps a, b, bb and pure water's part and changes only the
shape beyond bb/b ({len(pairs)} runs, the {len(cells)} black-bottom cells of part 3;
DECISIONS.md section 134, its measures set before the runs).

  Fournier-Forand rrs over the station's, over the {len(cells)} cells:""")
    for st in order:
        v = by_station[st]
        print(f"    {st:<9} bb/b {next(iter(cells.values()))[st]['back']:.4f}:"
              f"  {min(v):.2f} to {max(v):.2f}, median {float(np.median(v)):.2f}")
    print(f"""
1. Same bb/b, same rrs? {same} of the {len(pairs)} pairs are within {100 * SAME_WITHIN:g} percent or
   {SAME_SE:g} standard errors ({FIX_NEEDED} needed): bb/b {'fixes' if same >= FIX_NEEDED else 'does not fix'} the rrs over a black bottom.
2. Within the Fournier-Forands, model over Monte Carlo rises with bb/b in
   {rising} cells and falls in {falling} ({ORDER_NEEDED} needed either way): {'one smooth family is ordered by bb/b' if max(rising, falling) >= ORDER_NEEDED else 'the measure is not met'}.
3. Ranked over the six phase functions in each cell, the phase function at
   the angle of single scattering from the refracted sun to straight up
   and the Monte Carlo's rrs have a rank correlation of at least {RHO_NEEDED:g} in
   {ordered} of the {len(rho)} cells ({ORDER_NEEDED} needed); its median by sun is """ + ", ".join(
        f"{float(np.median(v)):.2f} at {s:g} degrees" for s, v in by_sun.items()) + f""".
   {'The backward phase function orders' if ordered >= ORDER_NEEDED else 'The backward phase function does not by itself order'} the black-bottom rrs.""")
    # Seen after the runs, not measures set before them.
    ff_spread = [max(c[s]["ff"] for s in order) / min(c[s]["ff"] for s in order)
                 for c in cells.values()]
    station_spread = [max(c[s]["station"] for s in order)
                      / min(c[s]["station"] for s in order)
                      for c in cells.values()]
    noise = max(c[s]["ff_se"] / c[s]["ff"] for c in cells.values()
                for s in order)
    follows = {}
    for sun in sorted({k[3] for k in cells}):
        x, y = [], []
        for k, c in cells.items():
            if k[1] == 3 and k[3] == sun:
                for s in order:
                    x.append(math.log(c[s]["p_station"] / c[s]["p_ff"]))
                    y.append(math.log(c[s]["station"] / c[s]["ff"]))
        follows[sun] = float(np.corrcoef(x, y)[0, 1])
    print(f"""
Seen after the runs, not measures set before them. The three
Fournier-Forands in a cell differ by a factor of {float(np.median(ff_spread)):.2f} in the median cell
({max(ff_spread):.2f} at most; standard errors up to {100 * noise:.0f} percent), the three stations
by {float(np.median(station_spread)):.2f}: at a and bb held, bb/b moves the rrs little within one
smooth family, and the noise is of the same size, so question 2 cannot
be read either way. In the cells with less scattering (bp/a 3)
the station's rrs over the Fournier-Forand's follows their phase
functions' ratio at the angle of single scattering, in logarithms, with
a correlation of """ + ", ".join(f"{v:.2f} with the sun at {s:g} degrees"
                               for s, v in follows.items()) + """: the
stations' larger rrs overhead comes with their larger backward peak, and
the relation fades as the sun goes down.""")
    halves = halves_part(cells)
    return dict(cells=cells, same=same, pairs=len(pairs),
                by_station=by_station, order=order, rising=rising,
                falling=falling, rho=rho, ordered=ordered, by_sun=by_sun,
                ff_spread=ff_spread, station_spread=station_spread,
                noise=noise, follows=follows, halves=halves)


#: The measures set in DECISIONS.md section 135 before the runs.
HALVES_NEEDED = 54
LEAD_NEEDED = 0.9


def halves_part(cells):
    """DECISIONS.md section 135: each station's phase function and its
    Fournier-Forand with the halves below and above 90 degrees exchanged."""
    h = read("halves.csv")
    runs = {}
    for j in range(len(h["a"])):
        k = (round(float(h["a"][j]), 4), round(float(h["bp_over_a"][j])),
             float(h["depth_m"][j]), float(h["sun_deg"][j]))
        runs[k + (h["station"][j], h["forward_from"][j])] = h["monte_carlo"][j]
    rows = []
    for k, c in cells.items():
        for st, v in c.items():
            s, f = v["station"], v["ff"]
            h1, h2 = runs[k + (st, "station")], runs[k + (st, "ff")]
            rows.append(dict(
                cell=k, station=st,
                backward=(math.log(s / h1) + math.log(h2 / f)) / 2,
                forward=(math.log(s / h2) + math.log(h1 / f)) / 2,
                interaction=math.log(s) - math.log(h1) - math.log(h2)
                + math.log(f),
                p_ratio=math.log(v["p_station"] / v["p_ff"])))
    dominant = sum(abs(r["backward"]) > abs(r["forward"]) for r in rows)
    lead = [r for r in rows if r["cell"][1] == 3 and r["cell"][3] in (0.0,
                                                                     30.0)]
    lead_corr = float(np.corrcoef([r["p_ratio"] for r in lead],
                                  [r["backward"] for r in lead])[0, 1])
    others = [r for r in rows if r["station"] != "NUC 2240"]
    others_dominant = sum(abs(r["backward"]) > abs(r["forward"])
                          for r in others)
    by_sun = {sun: (float(np.median([r["backward"] for r in others
                                     if r["cell"][3] == sun])),
                    float(np.median([abs(r["forward"]) for r in others
                                     if r["cell"][3] == sun])))
              for sun in sorted({r["cell"][3] for r in rows})}
    interaction = [abs(r["interaction"]) for r in rows]
    nuc = [math.exp(r["p_ratio"]) for r in rows if r["station"] == "NUC 2240"]
    print(f"""
The halves apart (DECISIONS.md section 135, its measures set before the
runs). Each station's phase function and its Fournier-Forand, with the
same bb/b, exchange their halves below and above 90 degrees; {len(h['a'])} more runs.
With the four, the backward half's effect on ln rrs and the forward
half's are each the mean of two differences.

1. The backward half's effect is the larger in {dominant} of the {len(rows)} pairs
   ({HALVES_NEEDED} needed): the measure is {'met' if dominant >= HALVES_NEEDED else 'not met'}.
2. In the {len(lead) // 3} cells with bp/a 3 and the sun at 0 or 30 degrees, the
   backward half's effect against ln of the two phase functions' ratio at
   the angle of single scattering: a correlation of {lead_corr:.3f} ({LEAD_NEEDED:g} needed),
   {'met' if lead_corr >= LEAD_NEEDED else 'not met'}.

Seen after the runs, not measures set before them. Without NUC 2240,
whose backward half is close to its Fournier-Forand's (at the angle of
single scattering their ratio is {min(nuc):.2f} to {max(nuc):.2f}), the backward half's
effect is the larger in {others_dominant} of {len(others)} pairs. For AUTEC 8 and HAOCE 11 its
median effect is a factor of """ + ", ".join(
        f"{math.exp(b):.2f} with the sun at {s:g} degrees" for s, (b, _) in by_sun.items()) + """;
the forward half's moves ln rrs by a median of """ + ", ".join(
        f"{fw:.3f}" for _, fw in by_sun.values()) + f""".
The interaction, 0 where the halves act apart, is {float(np.median(interaction)):.3f} in the median
pair ({max(interaction):.3f} at most).""")
    return dict(rows=rows, dominant=dominant, lead_corr=lead_corr,
                lead_pairs=len(lead), others_dominant=others_dominant,
                nuc=(min(nuc), max(nuc)),
                others=len(others), by_sun=by_sun,
                interaction=(float(np.median(interaction)),
                             max(interaction)))


#: Transcribed from the Ocean Optics Web Book's file of Petzold's data (C. D.
#: Mobley, oceanopticsbook.info, CC BY 2.0), column "avg-part PF", 1/sr,
#: "Data taken from Petzold (1972) and Light and Water, Table 3.10": twelve
#: of its 55 angles, degrees, to check the reconstruction against.
WEB_BOOK_AVERAGE = {0.1: 1.772e3, 1.0: 7.181e1, 10.0: 1.156, 30.0: 8.633e-2,
                    60.0: 1.316e-2, 90.0: 4.305e-3, 120.0: 2.693e-3,
                    140.0: 2.336e-3, 150.0: 2.371e-3, 160.0: 2.669e-3,
                    170.0: 3.039e-3, 180.0: 3.163e-3}


def average_part(dark):
    rule("6. Petzold's average-particle phase function, HydroLight's own")
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent
                           / "tools"))
    try:
        import shallow_rrs_mc as mc
    except ImportError:
        mc = None
    finally:
        sys.path.pop(0)
    rebuilt = None
    if mc is not None:
        angles, pf = mc.average_particle_table()
        at = np.exp(np.interp(np.log(list(WEB_BOOK_AVERAGE)), np.log(angles),
                              np.log(pf)))
        rebuilt = float(np.max(np.abs(
            at / np.array(list(WEB_BOOK_AVERAGE.values())) - 1)))
    runs = read("average_particle.csv")
    grid = read("monte_carlo.csv")
    q, _, group = groups(grid)
    ratio = grid["bp"] / grid["a"]
    key = {}
    for i in np.flatnonzero((grid["albedo"] == 0.0)
                            & np.isin(grid["depth_m"], (1.0, 4.0))
                            & np.isin(np.round(ratio), (3.0, 30.0))
                            & np.isin(grid["a"], (0.05, 0.2))):
        key[(round(float(grid["a"][i]), 4), round(float(ratio[i])),
             float(grid["depth_m"][i]), float(grid["sun_deg"][i]))] = i
    in_group = {k for k, i in key.items() if group[i]}
    q_avg, over_nuc, p_over = {}, {}, {}
    for j in range(len(runs["a"])):
        k = (round(float(runs["a"][j]), 4), round(float(runs["bp_over_a"][j])),
             float(runs["depth_m"][j]), float(runs["sun_deg"][j]))
        q_avg[k] = runs["model"][j] / runs["monte_carlo"][j]
        over_nuc[k] = runs["monte_carlo"][j] / grid["monte_carlo"][key[k]]
        p_over[k] = runs["p_back_average"][j] / runs["p_back_nuc2240"][j]
    within = sum(abs(q_avg[k] - 1) <= MISS for k in in_group)
    every = sum(abs(v - 1) <= MISS for v in q_avg.values())
    before = dark["counts"]["none"][0]
    back = float(runs["backscatter_share"][0])
    checked = ("" if rebuilt is None else
               " At the twelve angles checked it is the\nWeb Book's table "
               f"within {100 * rebuilt:.2f} percent.")
    print(f"""HydroLight's runs used Petzold's "average particle" phase function, which
Mobley et al. (2002, p. 1037) say "is derived from three measurements of
the VSF in San Diego Harbor". Built here from the package's own NUC 2040,
2200 and 2240 as the Ocean Optics Web Book describes (pure sea water at
514 nm and salinity 35 taken out of each, divided by the particles' b,
averaged at each angle).{checked} Its backscatter share in the
Monte Carlo's sampler is {back:.4f} (the paper: 0.0183).
In the {len(q_avg)} black-bottom cells, a, bb and pure water's part as in part 3:

  model within {100 * MISS:g} percent of the Monte Carlo: {within} of the group's {len(in_group)}
  ({before} with NUC 2240), {every} of the {len(q_avg)} cells; model over Monte Carlo
  {min(q_avg.values()):.3f} to {max(q_avg.values()):.3f}.

The measure set beforehand (10 of 13) is {'met' if within >= 10 else 'not met'}: HydroLight's own phase
function {'accounts' if within >= 10 else 'does not by itself account'} for the group.
Its rrs is {min(over_nuc.values()):.2f} to {max(over_nuc.values()):.2f} of NUC 2240's, and its phase function at
the angle of single scattering {min(p_over.values()):.2f} to {max(p_over.values()):.2f} of NUC 2240's.""")
    return dict(rebuilt=rebuilt, within=within, group=len(in_group),
                before=before, every=every, cells=len(q_avg),
                q=(min(q_avg.values()), max(q_avg.values())),
                over_nuc=(min(over_nuc.values()), max(over_nuc.values())),
                p_over=(min(p_over.values()), max(p_over.values())),
                back=back)


def main():
    _banner()
    with warnings.catch_warnings():
        warnings.simplefilter("error", jerlov.ProvenanceWarning)
        paper = paper_part()
        share = share_part(paper["missed"], paper["water_shares"])
        dark = dark_part()
        separated = separated_part()
        fournier = fournier_part()
        average = average_part(dark)
    rule("Before you use any of this")
    print("""  - The Monte Carlo is not HydroLight: a flat surface, no Raman scattering,
    Petzold's NUC 2240 for the particles where the paper used his average
    particle, and scattering by less than 1 degree counted as none.
  - The paper's waters are rebuilt from its Table 1 and equations, with a
    salinity chosen for pure sea water; the paper's further runs of 1999
    are not described and are not rebuilt.
  - A change that moves the ratio is not shown to be what HydroLight's runs
    differ by; the comparison says which differences matter, and how much.
  - Part 4 takes Lee et al.'s (2011) Rrs below the surface by Lee et al.'s
    (2002) Eq. (8), fitted for deep water seen from above; no coefficient
    is fitted here to the Monte Carlo.
  - Part 5's Fournier-Forands are on Mobley et al.'s line, one n and mu
    for each bb/b; another pair with the same bb/b is another shape.
""")
    return dict(paper=paper, share=share, dark=dark, separated=separated,
                fournier=fournier, average=average)


if __name__ == "__main__":
    main()

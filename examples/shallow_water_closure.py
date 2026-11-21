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
how much (DECISIONS.md section 114). The runs are in
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


def main():
    _banner()
    with warnings.catch_warnings():
        warnings.simplefilter("error", jerlov.ProvenanceWarning)
        paper = paper_part()
        share = share_part(paper["missed"], paper["water_shares"])
        dark = dark_part()
    rule("Before you use any of this")
    print("""  - The Monte Carlo is not HydroLight: a flat surface, no Raman scattering,
    Petzold's NUC 2240 for the particles where the paper used his average
    particle, and scattering by less than 1 degree counted as none.
  - The paper's waters are rebuilt from its Table 1 and equations, with a
    salinity chosen for pure sea water; the paper's further runs of 1999
    are not described and are not rebuilt.
  - A change that moves the ratio is not shown to be what HydroLight's runs
    differ by; the comparison says which differences matter, and how much.
""")
    return dict(paper=paper, share=share, dark=dark)


if __name__ == "__main__":
    main()

"""Do Williamson & Hollins's measured IOPs give back Jerlov's own Kd?

An open question, with numbers (OPEN_QUESTIONS.md). For anyone who uses
one source of a Jerlov type's optics to check another:

    python examples/closure_with_jerlov_kd.py

Williamson & Hollins (2022) measured a and b for six Jerlov types. Put
through a radiative transfer calculation, they should give back the Kd
Jerlov printed for the same types, if the two describe the same water. This
example reads 240 Monte Carlo runs made by tools/kd_closure.py and kept in
examples/data/kd_closure/, and works out, figure by figure, how close they
come, how far the conditions a Jerlov type leaves unrecorded (the sun, the
phase function, the pure water) move the answer, and where the gap is
larger than those conditions can make. It also sets beside them the Kd
that the radiative transfer code OSOAA gives for the same waters, a second
calculation made independently of the first; then does the same again with
pure water's own scattering and a sky (examples/data/sm_closure/), and
checks the Monte Carlo and OSOAA against the HydroLight Kd that Solonenko &
Mobley (2015) computed from their own a and b (examples/data/osoaa_sm_closure/
for OSOAA). It needs the repository, for those runs, but nothing beyond the
package and NumPy.
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


DATA = pathlib.Path(__file__).resolve().parent / "data"
TYPES = ("IB", "II", "III", "1C", "3C", "5C")
WAVELENGTHS = tuple(range(425, 701, 25))
EDITIONS = (("jerlov1976", "Jerlov (1976)"), ("jerlov1968", "Jerlov (1968)"))
FACTORS = (("sun_deg", "The sun, 0 or 60 degrees against 30"),
           ("station", "The Petzold station's phase function"),
           ("pure_water", "The pure water under the type's contents"))


def caught_by_type(caught, function, *args, **kwargs):
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always", jerlov.ProvenanceWarning)
        result = function(*args, **kwargs)
    caught.update(f"{w.category.__name__}: {str(w.message).split(':')[0]}"
                  for w in seen)
    return result


def load():
    with open(DATA / "kd_closure" / "runs.csv") as handle:
        return list(csv.DictReader(handle))


def jerlov_kd(caught, water_type, wl, source):
    water = jerlov.water(water_type, source=source)
    return float(caught_by_type(caught, water.kd, float(wl)))


def base_kd(runs, column="kd_first_penetration_depth"):
    return {(r["water_type"], int(r["wavelength_nm"])): float(r[column])
            for r in runs if r["factor"] == "base"}


def jerlov_part(runs, caught):
    rule("1. The computed Kd over Jerlov's")
    base = base_kd(runs)
    ratios = {}
    print(f"  {'Type':<6}" + "".join(f"{label:>18}" for _, label in EDITIONS))
    for water_type in TYPES:
        cells = []
        for source, _ in EDITIONS:
            r = {wl: base[(water_type, wl)]
                 / jerlov_kd(caught, water_type, wl, source)
                 for wl in WAVELENGTHS}
            ratios[(water_type, source)] = r
            cells.append(f"{min(r.values()):.2f} to {max(r.values()):.2f}")
        print(f"  {water_type:<6}" + "".join(f"{c:>18}" for c in cells))
    print("""
Kd over the first penetration depth, by Monte Carlo, from Williamson &
Hollins's a and b and the Petzold station nearest each type's b, the sun
30 degrees from the zenith, at the twelve wavelengths from 425 to 700 nm.""")
    return dict(base=base, ratios=ratios)


def factor_part(runs):
    rule("2. What the conditions a type leaves open can do")
    base = {(r["water_type"], r["wavelength_nm"]):
            float(r["kd_first_penetration_depth"])
            for r in runs if r["factor"] == "base"}
    moves = {}
    for factor, label in FACTORS:
        changes = [float(r["kd_first_penetration_depth"])
                   / base[(r["water_type"], r["wavelength_nm"])]
                   for r in runs if r["factor"] == factor]
        moves[factor] = (min(changes), max(changes))
        print(f"  {label:<44} {100 * (min(changes) - 1):+6.1f} to "
              f"{100 * (max(changes) - 1):+5.1f} percent")
    layer = [float(r["kd_to_10_percent"])
             / float(r["kd_first_penetration_depth"])
             for r in runs if r["factor"] == "base"]
    print(f"""
On IB and III, each varied alone at every wavelength. Taking Kd down to 10
percent of the surface light instead of the first penetration depth moves
it by {100 * (min(layer) - 1):+.1f} to {100 * (max(layer) - 1):+.1f} percent. Jerlov's tables record neither the sun nor
the layer.""")
    return dict(moves=moves, layer=(min(layer), max(layer)))


def verdict_part(found, factors):
    rule("3. Where the conditions cannot account for the gap")
    moves = factors["moves"]
    up = float(np.prod([high for _, high in moves.values()]))
    down = float(np.prod([low for low, _ in moves.values()]))
    beyond = {}
    for water_type in TYPES:
        r = found["ratios"][(water_type, "jerlov1976")]
        low = [wl for wl, v in r.items() if v * up < 1]
        high = [wl for wl, v in r.items() if v * down > 1]
        if low or high:
            beyond[water_type] = (low, high)
    print(f"""All three conditions at their extremes together move Kd by {down:.2f} to {up:.2f}
times. Against Jerlov (1976) the computed Kd lies outside that reach only
here:""")
    for water_type, (low, high) in beyond.items():
        r = found["ratios"][(water_type, "jerlov1976")]
        for wl in low + high:
            side = "below" if wl in low else "above"
            print(f"  {water_type:<4} at {wl} nm: {r[wl]:.2f} times, {side}")
    print("""
Everywhere else, Williamson & Hollins's IOPs and Jerlov's Kd are consistent
within what the unrecorded conditions can make. Where they are not, at the
blue end, the clearest type's IOPs attenuate more than Jerlov's Kd and the
coastal types' less.""")
    return dict(up=up, down=down, beyond=beyond)


def osoaa_kd(folder, drop=1.0):
    """Kd from the surface to where Ed has fallen by exp(drop) (the first
    penetration depth by default) of each OSOAA run that was made, from its
    Ed, with the run's parameters."""
    with open(folder / "runs.csv") as handle:
        runs = {int(r["run_id"]): r for r in csv.DictReader(handle)}
    profiles = {}
    with open(folder / "ed.csv") as handle:
        for r in csv.DictReader(handle):
            profiles.setdefault(int(r["run_id"]), []).append(
                (float(r["depth_m"]), float(r["ed"])))
    out = {}
    for k, r in runs.items():
        if r["status"] != "ok":
            continue
        z, ed = np.array(profiles[k]).T
        # The surface is printed twice below it; keep the first.
        keep = np.concatenate([[True], np.diff(z) > 0])
        z, log_ed = z[keep], np.log(ed[keep])
        out[k] = (r, drop / float(np.interp(-(log_ed[0] - drop), -log_ed,
                                            z)))
    if not (folder / "truncation.csv").exists():
        return out, None
    with open(folder / "truncation.csv") as handle:
        share = [float(r["truncation_coefficient"]) / 2
                 for r in csv.DictReader(handle)]
    return out, (min(share), max(share))


def against_monte_carlo(found, folder):
    kd, share = osoaa_kd(folder)
    ratios = sorted((v / found["base"][(r["water_type"],
                                        int(r["wavelength_nm"]))],
                     r["water_type"], int(r["wavelength_nm"]))
                    for r, v in kd.values() if r["factor"] == "base")
    return dict(kd=kd, share=share, ratios=ratios)


def osoaa_part(caught, found, factors, verdict):
    rule("4. A second calculation: OSOAA")
    now = against_monte_carlo(found, DATA / "osoaa_closure")
    before = against_monte_carlo(found, DATA / "osoaa_closure_f11_too_small")
    low, high = now["ratios"][0], now["ratios"][-1]
    base = {(r["water_type"], r["wavelength_nm"]): v
            for r, v in now["kd"].values() if r["factor"] == "base"}
    station = [v / base[(r["water_type"], r["wavelength_nm"])]
               for r, v in now["kd"].values() if r["factor"] == "station"]
    sky = [v / base[(r["water_type"], r["wavelength_nm"])]
           for r, v in now["kd"].values() if r["factor"] in ("aot", "wind")]
    beyond = {}
    for r, v in now["kd"].values():
        if r["factor"] != "base":
            continue
        ratio = v / jerlov_kd(caught, r["water_type"], r["wavelength_nm"],
                              "jerlov1976")
        if ratio * verdict["up"] < 1 or ratio * verdict["down"] > 1:
            beyond[(r["water_type"], int(r["wavelength_nm"]))] = ratio
    mc_beyond = {(water_type, wl) for water_type, (lo, hi)
                 in verdict["beyond"].items() for wl in lo + hi}
    moved = factors["moves"]["station"]
    print(f"""The radiative transfer code OSOAA (CNES), given the same a and b and the
same Petzold stations, with a sky, an aerosol and a wavy surface of its own,
gives for the {len(now["ratios"])} base runs it can make {low[0]:.3f} to {high[0]:.3f} times the Monte Carlo's
Kd: the lowest for {low[1]} at {low[2]} nm, the highest for {high[1]} at {high[2]} nm. It treats
{100 * now["share"][0]:.1f} to {100 * now["share"][1]:.1f} percent of the hydrosols' scattering as unscattered, the forward
peak it truncates. Its Kd is the higher the bluer the light and the
clearer the water; its sky, which the Monte Carlo lacks, may account for
that, but it was not checked. The station moves its Kd by {100 * (min(station) - 1):+.1f} to {100 * (max(station) - 1):+.1f} percent
(the Monte Carlo: {100 * (moved[0] - 1):+.1f} to {100 * (moved[1] - 1):+.1f}); the aerosol and the wind, which the
Monte Carlo does not have, by {100 * (min(sky) - 1):+.1f} to {100 * (max(sky) - 1):+.1f}. Against Jerlov (1976), OSOAA's Kd
lies outside the reach of section 3 at""")
    for key in sorted(beyond):
        print(f"  {key[0]:<4} at {key[1]} nm: {beyond[key]:.2f} times")
    missing = sorted(mc_beyond - set(beyond))
    print("the same places as the Monte Carlo's"
          + ("" if not missing else ", but for "
             + " and ".join(f"{t} at {wl} nm" for t, wl in missing)
             + ", which it brings just inside") + ".")
    print(f"""
Until release 1.15.5 the package wrote OSOAA's phase function 4 pi too
small. OSOAA then treated {100 * before["share"][0]:.1f} to {100 * before["share"][1]:.1f} percent of the scattering as
unscattered, its Kd came out {100 * (1 - before["ratios"][-1][0]):.1f} to {100 * (1 - before["ratios"][0][0]):.1f} percent below the Monte
Carlo's, and release 1.15.3 drew its conclusions from those runs. They
were wrong, and the fault was the package's, not OSOAA's (DECISIONS.md
section 93). The runs are kept in examples/data/osoaa_closure_f11_too_small/.""")
    return dict(now=now, before=before, station=(min(station), max(station)),
                sky=(min(sky), max(sky)), beyond=beyond, missing=missing)


TO_10_PERCENT = float(np.log(10.0))
SM_TYPES = ("I", "IA", "IB", "II", "III", "1C", "3C", "5C", "7C", "9C")


def load_sm():
    with open(DATA / "sm_closure" / "runs.csv") as handle:
        return list(csv.DictReader(handle))


def _key(r):
    return (r["water_type"], int(r["wavelength_nm"]))


def _span(values):
    return f"{100 * (min(values) - 1):+.1f} to {100 * (max(values) - 1):+.1f}"


def water_and_sky_part(caught, sm_runs, found, verdict):
    rule("5. With pure water's own scattering and a sky")
    wh = [r for r in sm_runs if r["set"] == "williamson2022"]
    column = "kd_first_penetration_depth"
    base = {_key(r): float(r[column]) for r in wh if r["factor"] == "base"}
    water = {_key(r): float(r[column]) for r in wh
             if r["factor"] == "water_only"}
    rise = [base[k] / found["base"][k] for k in base]
    rise_water = [water[k] / found["base"][k] for k in water]
    ratios = {}
    print(f"  {'Type':<6}" + "".join(f"{label:>18}" for _, label in EDITIONS))
    for water_type in TYPES:
        cells = []
        for source, _ in EDITIONS:
            r = {wl: base[(water_type, wl)]
                 / jerlov_kd(caught, water_type, wl, source)
                 for wl in WAVELENGTHS}
            ratios[(water_type, source)] = r
            cells.append(f"{min(r.values()):.2f} to {max(r.values()):.2f}")
        print(f"  {water_type:<6}" + "".join(f"{c:>18}" for c in cells))
    moves = {}
    for factor, label in FACTORS:
        changes = [float(r[column]) / base[_key(r)]
                   for r in wh if r["factor"] == factor]
        moves[factor] = (min(changes), max(changes))
    up = float(np.prod([high for _, high in moves.values()]))
    down = float(np.prod([low for low, _ in moves.values()]))
    beyond = {}
    for water_type in TYPES:
        for wl, v in ratios[(water_type, "jerlov1976")].items():
            if v * up < 1 or v * down > 1:
                beyond[(water_type, wl)] = v
    osoaa, _ = osoaa_kd(DATA / "osoaa_closure")
    against = {}
    for name, mc in (("section_92", found["base"]), ("water", water),
                     ("water_and_sky", base)):
        against[name] = sorted(
            (v / mc[_key(r)], r["water_type"], int(r["wavelength_nm"]))
            for r, v in osoaa.values() if r["factor"] == "base")
    now = against["water_and_sky"]
    sky = [float(r["sky_share"]) for r in wh if r["factor"] == "base"]
    print(f"""
Sections 1 to 4 took the Monte Carlo as section 92 ran it: one phase
function for all the scattering, and the sun's beam alone. Here pure water's
share of b (Williamson & Hollins's own bw, 0.00583 (400/lambda)^4.322) is
turned by pure water's own phase function, and {100 * min(sky):.0f} to {100 * max(sky):.0f} percent of the
light below the surface comes from a sky, as Gregg & Carder's model gives it
for an open-ocean aerosol of optical thickness 0.2 at 550 nm, uniform in
radiance in the air. Pure water's scattering alone moves Kd by
{_span(rise_water)} percent, with the sky {_span(rise)}; the table is section 1's
again with this Monte Carlo. Varied as in section 2, the sun moves Kd by
{_span(moves["sun_deg"])} percent, the station by {_span(moves["station"])}, the pure water by
{_span(moves["pure_water"])}; together {down:.2f} to {up:.2f} times. Outside that reach,
against Jerlov (1976):""")
    for key in sorted(beyond, key=lambda k: (TYPES.index(k[0]), k[1])):
        print(f"  {key[0]:<4} at {key[1]} nm: {beyond[key]:.2f} times")
    old = {(t, wl) for t, (lo, hi) in verdict["beyond"].items()
           for wl in lo + hi}
    came_inside = sorted(old - set(beyond))
    went_outside = sorted(set(beyond) - old)
    changes = [", ".join(f"{t} at {wl} nm" for t, wl in keys) + note
               for keys, note in ((went_outside, " lies outside as well"),
                                  (came_inside, " comes inside"))
               if keys]
    print("Against section 3, " + "; ".join(changes) + "."
          if changes else "The same places as in section 3.")
    first, last = against["section_92"][0], against["section_92"][-1]
    print(f"""
OSOAA's Kd (section 4) was {first[0]:.3f} to {last[0]:.3f} times the Monte Carlo's. Against the
Monte Carlo with pure water's scattering it is {against["water"][0][0]:.3f} to {against["water"][-1][0]:.3f}, and with the
sky as well {now[0][0]:.3f} to {now[-1][0]:.3f}: what OSOAA had and the Monte Carlo lacked
accounts for the gap, though OSOAA's sky is its own (an aerosol optical
thickness of 0.1, a wind of 7 m/s), not this one.""")
    return dict(base=base, rise=(min(rise), max(rise)),
                rise_water=(min(rise_water), max(rise_water)),
                ratios=ratios, moves=moves, up=up, down=down, beyond=beyond,
                came_inside=came_inside, went_outside=went_outside,
                against=against, sky=(min(sky), max(sky)))


def hydrolight_part(sm_runs):
    rule("6. Against HydroLight, from the same IOPs")
    sm = [r for r in sm_runs if r["set"] == "solonenko2015"]
    column = "kd_to_10_percent"
    kdh = {_key(r): float(r["kd_hydrolight"]) for r in sm
           if r["factor"] == "base"}
    stats = {}
    for factor in ("as_section_92", "water_only", "base"):
        r = np.array([float(x[column]) / kdh[_key(x)] for x in sm
                      if x["factor"] == factor])
        stats[factor] = dict(median=float(np.median(r)),
                             within=float(np.mean(abs(r - 1) <= 0.10)),
                             low=float(r.min()), high=float(r.max()))
    base = {_key(r): float(r[column]) for r in sm if r["factor"] == "base"}
    per_type = {}
    for t in SM_TYPES:
        v = [base[k] / kdh[k] for k in base if k[0] == t]
        per_type[t] = (min(v), max(v))
    moves = {}
    for factor in ("station", "sun_deg", "aot"):
        changes = [float(r[column]) / base[_key(r)] for r in sm
                   if r["factor"] == factor]
        moves[factor] = (min(changes), max(changes))
    reach = {}
    for r in sm:
        if r["factor"] in ("base", "station", "sun_deg", "aot"):
            reach.setdefault(_key(r), []).extend(
                [float(r[column]), float(r["kd_first_penetration_depth"])])
    outside = sorted(k for k, v in reach.items()
                     if not min(v) <= kdh[k] <= max(v))
    s = stats["base"]
    agrees = s["median"] >= 0.95 and s["median"] <= 1.05 and s["within"] >= 0.9
    print(f"""Solonenko & Mobley (2015) put the a and b they retrieved for ten Jerlov
types through HydroLight and printed its Kd, K_d^H. The same a and b, at
the {len(kdh)} cells from 350 to 700 nm where all three are given, through the
Monte Carlo: Kd to 10 percent of the surface light, over K_d^H.

  {'Monte Carlo':<44}{'median':>8}{'within 10%':>12}{'range':>16}""")
    labels = (("as_section_92", "as section 92: one phase function, no sky"),
              ("water_only", "with pure water's own scattering"),
              ("base", "with it and a sky"))
    for factor, label in labels:
        x = stats[factor]
        print(f"  {label:<44}{x['median']:>8.3f}{100 * x['within']:>11.1f}%"
              f"{x['low']:>9.3f} to {x['high']:.3f}")
    print("\nWith pure water's scattering and the sky, by type:")
    for t, (lo, hi) in per_type.items():
        print(f"  {t:<4} {lo:.2f} to {hi:.2f}")
    print(f"""
The paper does not print HydroLight's sun, the average-particle phase
function, or the depth its Kd belongs to. Here the sun is the paper's own
for its Eq. (3) (15 degrees from the zenith for the oceanic types, 45 for
the coastal), the phase function NUC 2240's (mean cosine 0.926, the paper's
average 0.924), and the sky Gregg & Carder's (aerosol optical thickness 0.2).
The other Petzold stations move Kd by {_span(moves["station"])} percent, the sun at 0, 30 or 60
degrees by {_span(moves["sun_deg"])}, the aerosol at 0.05 or 0.4 by {_span(moves["aot"])}. K_d^H lies
inside what they and the depth make of the Monte Carlo's Kd at
{len(kdh) - len(outside)} of the {len(kdh)} cells. The criterion set before the runs (DECISIONS.md
section 94: median within 0.95 to 1.05, 90 percent of cells within 10
percent) is {"met" if agrees else "not met"}.""")
    osoaa, _ = osoaa_kd(DATA / "osoaa_sm_closure", drop=TO_10_PERCENT)
    over_h = sorted((v / float(r["kd_hydrolight"]), r["water_type"],
                     int(r["wavelength_nm"]))
                    for r, v in osoaa.values() if r["factor"] == "base")
    over_mc = sorted((v / base[_key(r)], r["water_type"],
                      int(r["wavelength_nm"]))
                     for r, v in osoaa.values() if r["factor"] == "base")
    aot = {_key(r): v for r, v in osoaa.values() if r["factor"] == "aot"}
    aot_move = [aot[_key(r)] / v for r, v in osoaa.values()
                if r["factor"] == "base" and _key(r) in aot]
    with open(DATA / "osoaa_sm_closure" / "runs.csv") as handle:
        not_run = sum(1 for r in csv.DictReader(handle)
                      if r["factor"] == "base" and r["status"] != "ok")
    h = np.array([x for x, _, _ in over_h])
    print(f"""
OSOAA, given the same totals (its own pure water taken off and added back),
NUC 2240 and its own aerosol (optical thickness 0.2), at the {len(over_h)} cells it
can run ({not_run} cannot be: there a or b is below OSOAA's own pure water):
over K_d^H, median {np.median(h):.3f}, {100 * np.mean(abs(h - 1) <= 0.10):.1f} percent within 10 percent,
{over_h[0][0]:.3f} to {over_h[-1][0]:.3f}; over the Monte Carlo, {over_mc[0][0]:.3f} to {over_mc[-1][0]:.3f}. An aerosol of 0.05
moves OSOAA's Kd by {_span(aot_move)} percent.""")
    return dict(stats=stats, per_type=per_type, moves=moves, outside=outside,
                cells=len(kdh), agrees=agrees, over_h=over_h,
                over_mc=over_mc, not_run=not_run,
                aot_move=(min(aot_move), max(aot_move)))


PRINTED = (310, 350, 375, 400, 425, 450, 475, 500, 525, 550, 575, 600, 625,
           650, 675, 700)
COASTAL = ("1C", "3C", "5C")


def _read(name):
    with open(DATA / "blue_end" / name) as handle:
        return list(csv.DictReader(handle))


def _quartiles(values):
    q1, q2, q3 = np.percentile(values, [25, 50, 75])
    return float(q1), float(q2), float(q3)


def editions_part(caught):
    """Jerlov (1968) over Jerlov (1976) where both printed a value."""
    ratio = {}
    for t in SM_TYPES:
        old = jerlov.water(t, source="jerlov1968")
        new = jerlov.water(t, source="jerlov1976")
        for wl in PRINTED:
            r = (float(caught_by_type(caught, old.kd, float(wl)))
                 / float(caught_by_type(caught, new.kd, float(wl))))
            if np.isfinite(r):
                ratio[(t, wl)] = r
    return ratio


#: The bands the campaigns' wavelengths cluster in, named by their centre.
BANDS = {412: (410, 414), 443: (440, 445), 490: (486, 491), 510: (508, 512),
         555: (550, 560)}


def campaigns_part(caught):
    """Each campaign's measured Kd over Jerlov's at its own wavelength (the
    1 nm tables), by type and by band."""
    groups = {}
    for r in _read("kd_campaigns.csv"):
        wl = int(r["wavelength_nm"])
        nearest = next((band for band, (lo, hi) in BANDS.items()
                        if lo <= wl <= hi), None)
        if nearest is None:
            continue
        for source in ("jerlov1976", "jerlov1968"):
            water = jerlov.water(r["water_type"], source=source)
            k = float(caught_by_type(caught, water.kd, float(wl)))
            if np.isfinite(k):
                groups.setdefault((r["water_type"], nearest, source),
                                  []).append(float(r["kd"]) / k)
    return {key: (_quartiles(v), len(v)) for key, v in groups.items()}


def matched_part():
    """The Monte Carlo from each campaign's own a and b over the Kd
    measured in it; and where its a is at or above that Kd."""
    runs = _read("runs.csv")
    base = {}
    variants = {}
    for r in runs:
        if r["status"] != "ok":
            continue
        ratio = float(r["kd_first_penetration_depth"]) / float(
            r["kd_measured"])
        key = (r["water_type"], int(r["wavelength_nm"]))
        if r["factor"] == "base":
            base.setdefault(key, []).append(ratio)
        variants.setdefault((key, r["factor"], r["value"]), []).append(ratio)
    # The median under each sun and station: how far they move it.
    reach = {}
    for (key, _, _), v in variants.items():
        lo, hi = reach.get(key, (np.inf, -np.inf))
        reach[key] = (min(lo, float(np.median(v))),
                      max(hi, float(np.median(v))))
    not_run = sum(1 for r in runs
                  if r["factor"] == "base" and r["status"] != "ok")
    above = {}
    for r in _read("matched.csv"):
        key = r["Jerlov"].split("_", 1)[1]
        n, k = above.get(key, (0, 0))
        above[key] = (n + 1, k + (float(r["Val_a"]) >= float(r["Val_Kd"])))
    return dict(base={k: (float(np.median(v)), len(v), min(v), max(v))
                      for k, v in base.items()},
                reach=reach,
                not_run=not_run, above=above)


def ib_campaigns_part():
    """IB's six IOP campaigns: a against the Kd measured in the same
    campaign within 3 nm."""
    kd = {}
    for r in _read("kd_campaigns.csv"):
        kd.setdefault(r["campaign"], {})[int(r["wavelength_nm"])] = float(
            r["kd"])
    out = []
    for r in _read("iop_campaigns.csv"):
        if r["water_type"] != "IB" or r["quantity"] != "a":
            continue
        wl = int(r["wavelength_nm"])
        own = kd.get(r["campaign"], {})
        near = [w for w in own if abs(w - wl) <= 3]
        if near:
            w = min(near, key=lambda x: abs(x - wl))
            out.append((int(r["campaign"]), wl, float(r["value"]), w,
                        own[w]))
    return sorted(out)


def spread_part(caught):
    """The a that would close each blue cell, against the spread of the
    type's measured points."""
    rows = []
    for r in _read("closing_a.csv"):
        t, wl = r["water_type"], int(r["wavelength_nm"])
        points = caught_by_type(caught, jerlov.measured_points, t, "a")
        w = np.asarray(points.wavelengths, dtype=float)
        sd = float(np.interp(wl, w, np.asarray(points.std_dev, dtype=float)))
        n = float(np.interp(wl, w, np.asarray(points.n_campaigns,
                                                dtype=float)))
        change = float(r["closing_a"]) - float(r["a"])
        rows.append((t, wl, float(r["a"]), float(r["closing_a"]),
                     change / sd, change / (sd / np.sqrt(n))))
    return rows


NEIGHBOURS = ("IB", "II", "III", "1C", "3C", "5C")


def neighbours_part(caught):
    """The difference between neighbouring types' measured points, in
    units of their pooled SD, at the blue wavelengths."""
    out = {}
    for quantity in ("a", "b"):
        for lower, upper in zip(NEIGHBOURS, NEIGHBOURS[1:]):
            p = caught_by_type(caught, jerlov.measured_points, lower,
                               quantity)
            q = caught_by_type(caught, jerlov.measured_points, upper,
                               quantity)
            for wl in (412, 440, 488):
                i = list(p.wavelengths).index(wl)
                j = list(q.wavelengths).index(wl)
                pooled = np.sqrt((p.std_dev[i] ** 2 + q.std_dev[j] ** 2) / 2)
                out[(quantity, lower, upper, wl)] = float(
                    (q.values[j] - p.values[i]) / pooled)
    return out


def blue_end_part(caught, water_and_sky):
    rule("7. The blue end, from the Kd measured in the same waters")
    editions = editions_part(caught)
    campaigns = campaigns_part(caught)
    matched = matched_part()
    ib = ib_campaigns_part()
    spread = spread_part(caught)
    neighbours = neighbours_part(caught)
    print("""Williamson & Hollins gave each campaign of measured Kd the Jerlov type
nearest it over all its wavelengths, within 25 percent on average; their
a and b are averages over the campaigns so typed. Their dataset keeps
every campaign. Measured Kd over Jerlov's, median (and quartiles), by the
type each campaign was given:
""")
    print(f"  {'Type':<5}{'nm':>5}{'n':>6}{'over 1976':>22}{'over 1968':>22}")
    for t in ("IB",) + COASTAL:
        for wl in (412, 443, 490):
            cells = []
            for source in ("jerlov1976", "jerlov1968"):
                (q1, q2, q3), n = campaigns[(t, wl, source)]
                cells.append(f"{q2:.2f} ({q1:.2f}-{q3:.2f})")
            print(f"  {t:<5}{wl:>5}{n:>6}{cells[0]:>22}{cells[1]:>22}")
    ws = water_and_sky["ratios"]
    print(f"""
The averaged IOPs gave, by the Monte Carlo of part 5, {ws[("1C", "jerlov1976")][425]:.2f}, {ws[("3C", "jerlov1976")][425]:.2f} and {ws[("5C", "jerlov1976")][425]:.2f} of
Jerlov's (1976) at 425 nm for 1C, 3C and 5C, and {min(ws[("IB", "jerlov1976")][w] for w in (425, 450, 475)):.2f} to {max(ws[("IB", "jerlov1976")][w] for w in (425, 450, 475)):.2f} for IB at
425 to 475 nm.

Jerlov's own two editions differ there: 1968 over 1976 at 425 nm is""")
    print("  " + ", ".join(f"{t} {editions[(t, 425)]:.2f}"
                           for t in ("IB",) + COASTAL))
    base = matched["base"]
    print(f"""
In {sum(n for n, _ in matched["above"].values())} entries a, b and Kd were measured in the same campaign at the same
wavelength. The Monte Carlo from each entry's own a and b (as part 5,
the sun at 30 degrees, NUC 2240), over the Kd measured in it, median:""")
    for t in ("II", "III") + COASTAL + ("IB",):
        cells = [f"{wl} nm {base[(t, wl)][0]:.2f} (n {base[(t, wl)][1]})"
                 for wl in (412, 510, 555) if (t, wl) in base]
        print(f"  {t:<4} " + ", ".join(cells))
    reach = matched["reach"]
    print("With the sun at 0 or 60 degrees, or the stations HAOCE 11 or AUTEC 8,\n"
          "the median at 412 nm lies between " + ", ".join(
              f"{reach[(t, 412)][0]:.2f} and {reach[(t, 412)][1]:.2f} for {t}"
              for t in COASTAL) + ".")
    print("""In some entries the measured a is at or above the measured Kd, which no
radiative transfer calculation can give back:""")
    print("  " + ", ".join(f"{t} {k} of {n}" for t, (n, k)
                           in sorted(matched["above"].items(),
                                     key=lambda x: SM_TYPES.index(x[0]))))
    print("\nIB's averages rest on six campaigns of a. Where the same campaign "
          "measured\nKd within 3 nm, a and Kd:")
    for campaign, wl, a, w, k in ib:
        if wl <= 510:
            flag = "  a at or above Kd" if a >= k else ""
            print(f"  campaign {campaign:>5}: a({wl}) {a:.4f}, Kd({w}) "
                  f"{k:.4f}{flag}")
    print("""
The a that would make the Monte Carlo give Jerlov's (1976) Kd, b held,
against the spread of the type's measured points (SD, and the standard
error SD / sqrt(n)):""")
    for t, wl, a, a_star, sds, ses in spread:
        print(f"  {t:<4}{wl:>4} nm: a {a:.4f} -> {a_star:.4f}, "
              f"{sds:+.1f} SD, {ses:+.1f} SE")
    a_steps = [v for (q, *_), v in neighbours.items() if q == "a"]
    b_steps = [v for (q, *_), v in neighbours.items() if q == "b"]
    print(f"""
From one type to the next (IB to 5C) the measured a at 412, 440 and 488 nm
rises by {min(a_steps):.1f} to {max(a_steps):.1f} pooled SDs, and b by {min(b_steps):.1f} to {max(b_steps):.1f}.""")
    return dict(editions=editions, campaigns=campaigns, matched=matched,
                ib=ib, spread=spread, neighbours=neighbours)


def main():
    """Print the comparison; every figure is computed from the runs."""
    _banner()
    caught = set()
    runs = load()
    print(f"\n{len(runs)} Monte Carlo runs from {DATA / 'kd_closure'}")
    found = jerlov_part(runs, caught)
    factors = factor_part(runs)
    verdict = verdict_part(found, factors)
    osoaa = osoaa_part(caught, found, factors, verdict)
    sm_runs = load_sm()
    print(f"\n{len(sm_runs)} more Monte Carlo runs from {DATA / 'sm_closure'}")
    water_and_sky = water_and_sky_part(caught, sm_runs, found, verdict)
    hydrolight = hydrolight_part(sm_runs)
    blue_end = blue_end_part(caught, water_and_sky)
    if caught:
        rule("Warnings")
        print("Raised along the way, and caught by type:")
        for message in sorted(caught):
            print(f"  - {message}")

    rule("Before you use any of this")
    print("""  - The Monte Carlo (tools/kd_monte_carlo.py) was written for this and
    checked against Morel and Loisel's relation, OSOAA and the HydroLight
    Kd Solonenko & Mobley printed (section 6); in sections 1 to 4 it has
    no sky, in sections 5 and 6 a sky uniform in radiance, and never an
    atmosphere of its own or light reflected back down at the surface.
  - Solonenko & Mobley's HydroLight runs used Petzold's average-particle
    phase function, which is not shipped; NUC 2240's stands in for it, and
    the other stations show how much that choice can move Kd.
  - Petzold's phase functions are of water and particles together, from
    1971, at 530 nm, used at every wavelength.
  - Jerlov's Kd and Williamson & Hollins's IOPs are each summaries of many
    waters under one name; Williamson & Hollins chose their waters by
    matching measured Kd to Jerlov (1976) within 25 percent.
  - Part 7 takes each campaign's Kd, a and b as Williamson & Hollins's
    dataset gives them (examples/data/blue_end/); the sun of each
    campaign is not recorded, and 30 degrees was assumed for it.
""")
    return dict(runs=runs, found=found, factors=factors, verdict=verdict,
                osoaa=osoaa, sm_runs=sm_runs, water_and_sky=water_and_sky,
                hydrolight=hydrolight, blue_end=blue_end, caught=caught)


if __name__ == "__main__":
    main()

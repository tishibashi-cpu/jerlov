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
calculation made independently of the first. It needs the repository, for
those runs, but nothing beyond the package and NumPy.
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


def osoaa_kd(folder):
    """Kd over the first penetration depth of each OSOAA run that was
    made, from its Ed, with the run's parameters."""
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
        out[k] = (r, 1.0 / float(np.interp(-(log_ed[0] - 1.0), -log_ed, z)))
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


def osoaa_part(found):
    rule("4. A second calculation: OSOAA")
    now = against_monte_carlo(found, DATA / "osoaa_closure")
    before = against_monte_carlo(found, DATA / "osoaa_closure_f11_too_small")
    low, high = now["ratios"][0], now["ratios"][-1]
    print(f"""The radiative transfer code OSOAA, given the same a and b and the same
stations with a sky, an aerosol and a wavy surface of its own, gives for the
{len(now["ratios"])} base runs it can make {low[0]:.3f} to {high[0]:.3f} times the Monte Carlo's Kd
(the lowest for {low[1]} at {low[2]} nm, the highest for {high[1]} at {high[2]} nm). OSOAA
treats {100 * now["share"][0]:.1f} to {100 * now["share"][1]:.1f} percent of the hydrosols' scattering as unscattered,
the forward peak it truncates.

Until release 1.15.5 the package wrote OSOAA's phase function 4 pi too
small. OSOAA then treated {100 * before["share"][0]:.1f} to {100 * before["share"][1]:.1f} percent of the scattering as
unscattered, its Kd came out {100 * (1 - before["ratios"][-1][0]):.1f} to {100 * (1 - before["ratios"][0][0]):.1f} percent below the Monte
Carlo's, and release 1.15.3 drew its conclusions from those runs: wrong,
and the fault was the package's, not OSOAA's (DECISIONS.md section 93).
They are kept in examples/data/osoaa_closure_f11_too_small/.""")
    return dict(now=now, before=before)


def main():
    """Print the comparison; every figure is computed from the runs."""
    _banner()
    caught = set()
    runs = load()
    print(f"\n{len(runs)} Monte Carlo runs from {DATA / 'kd_closure'}")
    found = jerlov_part(runs, caught)
    factors = factor_part(runs)
    verdict = verdict_part(found, factors)
    osoaa = osoaa_part(found)
    if caught:
        rule("Warnings")
        print("Raised along the way, and caught by type:")
        for message in sorted(caught):
            print(f"  - {message}")

    rule("Before you use any of this")
    print("""  - The Monte Carlo (tools/kd_monte_carlo.py) was written for this and
    checked against Morel and Loisel's relation, not against another
    full code; it has no sky, atmosphere or surface reflection.
  - Petzold's phase functions are of water and particles together, from
    1971, at 530 nm, used at every wavelength.
  - Jerlov's Kd and Williamson & Hollins's IOPs are each summaries of many
    waters under one name; Williamson & Hollins chose their waters by
    matching measured Kd to Jerlov (1976) within 25 percent.
""")
    return dict(runs=runs, found=found, factors=factors, verdict=verdict,
                osoaa=osoaa, caught=caught)


if __name__ == "__main__":
    main()

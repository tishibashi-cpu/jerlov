"""Do Williamson & Hollins's measured IOPs give back Jerlov's own Kd?

An open question, with numbers (OPEN_QUESTIONS.md). For anyone who uses
one source of a Jerlov type's optics to check another:

    python examples/closure_with_jerlov_kd.py

Williamson & Hollins (2022) measured a and b for six Jerlov types. Put
through the radiative transfer code OSOAA, they should give back the Kd
Jerlov printed for the same types, if the two describe the same water. This
example reads 408 OSOAA runs made by tools/osoaa_closure.py and kept in
examples/data/osoaa_closure/, and works out, figure by figure, how close
they come, and how far the conditions a Jerlov type leaves unrecorded (the
sun, the pure water, the phase function, the sky, the wind) move the
answer. It needs the repository, for those runs, but not OSOAA
(DECISIONS.md sections 90 and 91).
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


RUNS = pathlib.Path(__file__).resolve().parent / "data" / "osoaa_closure"
TYPES = ("IB", "II", "III", "1C", "3C", "5C")
WAVELENGTHS = tuple(range(425, 701, 25))
EDITIONS = (("jerlov1976", "Jerlov (1976)"), ("jerlov1968", "Jerlov (1968)"))
FACTORS = (("sun_deg", "The sun, 0 or 60 degrees against 30"),
           ("pure_water", "The pure water under the type's contents"),
           ("station", "The Petzold station"),
           ("aot", "Aerosol, 0.05 or 0.3"),
           ("wind", "Wind, 2 or 15 m/s"))
#: The runs' sun, 30 degrees from the zenith, refracted into the sea.
SUN_IN_WATER = math.asin(math.sin(math.radians(30.0)) / 1.34)


def caught_by_type(caught, function, *args, **kwargs):
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always", jerlov.ProvenanceWarning)
        result = function(*args, **kwargs)
    caught.update(f"{w.category.__name__}: {str(w.message).split(':')[0]}"
                  for w in seen)
    return result


def load():
    """The runs' parameters and OSOAA's Ed at every level in the sea."""
    with open(RUNS / "runs.csv") as handle:
        runs = {int(r["run_id"]): r for r in csv.DictReader(handle)}
    profiles = {}
    with open(RUNS / "ed.csv") as handle:
        for r in csv.DictReader(handle):
            profiles.setdefault(int(r["run_id"]), []).append(
                (float(r["depth_m"]), float(r["ed"])))
    return runs, profiles


def kd(profile, drop=1.0):
    """The mean Kd from just below the surface to where Ed has fallen by a
    factor exp(drop): the first penetration depth for drop = 1."""
    z, ed = np.array(profile).T
    keep = np.concatenate([[True], np.diff(z) > 0])
    z, log_ed = z[keep], np.log(ed[keep])
    return drop / float(np.interp(-(log_ed[0] - drop), -log_ed, z))


def jerlov_kd(caught, water_type, wl, source):
    water = jerlov.water(water_type, source=source)
    return float(caught_by_type(caught, water.kd, float(wl)))


def check_part(runs, profiles, caught):
    rule("1. Does OSOAA do what a simple estimate says?")
    deviations = []
    for k, r in runs.items():
        if r["factor"] != "base" or r["status"] != "ok":
            continue
        wl = float(r["wavelength_nm"])
        water = jerlov.water(r["water_type"])
        a = float(caught_by_type(caught, water.a, wl))
        b = float(caught_by_type(caught, water.b, wl))
        ratio = jerlov.petzold_scattering(r["station"]).backscatter_ratio
        estimate = (a + ratio * b) / math.cos(SUN_IN_WATER)
        deviations.append(kd(profiles[k]) / estimate - 1)
    low, high = 100 * min(deviations), 100 * max(deviations)
    print(f"""At every base run OSOAA's Kd is within {low:+.1f} to {high:+.1f} percent of
(a + bb) / cos(theta_w), with bb the Petzold station's B/S times b. The run
is sound; what follows compares the data.""")
    return dict(low=low, high=high)


def jerlov_part(runs, profiles, caught):
    rule("2. OSOAA's Kd over Jerlov's")
    base = {(r["water_type"], int(r["wavelength_nm"])): kd(profiles[k])
            for k, r in runs.items()
            if r["factor"] == "base" and r["status"] == "ok"}
    ranges = {}
    print(f"  {'Type':<6}" + "".join(f"{label:>18}" for _, label in EDITIONS))
    for water_type in TYPES:
        cells = []
        for source, _ in EDITIONS:
            ratios = {wl: k / jerlov_kd(caught, water_type, wl, source)
                      for (t, wl), k in base.items() if t == water_type}
            low = min(ratios, key=ratios.get)
            high = max(ratios, key=ratios.get)
            ranges[(water_type, source)] = (ratios[low], low,
                                            ratios[high], high)
            cells.append(f"{ratios[low]:.2f} to {ratios[high]:.2f}")
        print(f"  {water_type:<6}" + "".join(f"{c:>18}" for c in cells))
    ib = ranges[("IB", "jerlov1976")]
    coastal = min((ranges[(t, "jerlov1976")] for t in ("1C", "3C", "5C")),
                  key=lambda v: v[0])
    print(f"""
At the twelve wavelengths from 425 to 700 nm (fewer where a run could not
be made). The clearest type gives more attenuation than Jerlov (1976)
printed, up to {ib[2]:.2f} times at {ib[3]} nm; the coastal types give much less,
down to {coastal[0]:.2f} times.""")
    return dict(base=base, ranges=ranges)


def factor_part(runs, profiles):
    rule("3. What the conditions a type leaves open can do")
    base = {(r["water_type"], r["wavelength_nm"]): k
            for k, r in runs.items()
            if r["factor"] == "base" and r["status"] == "ok"}
    moves = {}
    for factor, label in FACTORS:
        changes = [100 * (kd(profiles[k]) / kd(profiles[base[key]]) - 1)
                   for k, r in runs.items()
                   if r["factor"] == factor and r["status"] == "ok"
                   and r["water_type"] in ("IB", "III")
                   and (key := (r["water_type"], r["wavelength_nm"]))
                   in base]
        moves[factor] = (min(changes), max(changes))
        print(f"  {label:<44} {min(changes):+6.1f} to {max(changes):+5.1f} percent")
    print("""
On IB and III, each varied alone at every wavelength. Jerlov's tables
record neither the sun nor the sky they were measured under.""")
    return moves


def verdict_part(found, moves, caught):
    rule("4. What the conditions can explain, and what they cannot")
    reach = (1 + moves["sun_deg"][1] / 100) * (1 + moves["pure_water"][1] / 100)
    ranges = found["ranges"]
    within = [t for t in TYPES
              if ranges[(t, "jerlov1976")][0] * reach >= 1
              and ranges[(t, "jerlov1976")][2]
              * (1 + moves["sun_deg"][0] / 100)
              * (1 + moves["pure_water"][0] / 100) <= 1]
    water = jerlov.water("5C")
    a = float(caught_by_type(caught, water.a, 550.0))
    b = float(caught_by_type(caught, water.b, 550.0))
    needed = (jerlov_kd(caught, "5C", 550, "jerlov1976")
              * math.cos(SUN_IN_WATER) - a) / b
    largest = max(jerlov.petzold_scattering(s).backscatter_ratio
                  for s in jerlov.PETZOLD_STATIONS)
    iii_1968 = ranges[("III", "jerlov1968")][0]
    print(f"""Raising the sun to 60 degrees and taking the largest pure water together
lift Kd by at most {reach:.2f} times. Against Jerlov (1976) that covers the
gap for {' and '.join(within)} and no other type; against Jerlov (1968) not even
for III, which falls to {iii_1968:.2f}.

For 5C at 550 nm to reach Jerlov (1976), bb / b would have to be {needed:.2f};
the largest Petzold measured at any of his eight stations is {largest:.3f}.

So Williamson & Hollins's coastal types and the waters Jerlov measured his
coastal Kd in are different water, by more than the conditions a type
leaves open can make. Neither source confirms the other there.""")
    return dict(reach=reach, within=within, needed=needed, largest=largest,
                iii_1968=iii_1968)


def not_run_part(runs):
    rule("5. The runs that could not be made")
    refused = [r for r in runs.values() if r["status"] != "ok"]
    base = sorted((r["water_type"], int(r["wavelength_nm"]))
                  for r in refused if r["factor"] == "base")
    print(f"""{len(refused)} of the {len(runs)} runs could not be made, {len(base)} of them at the base. OSOAA
always adds its own pure water, and from 650 nm it absorbs more than the
aw Williamson & Hollins built a on; where a type's total a is below it,
the input OSOAA would need is negative. The type's own contents on
OSOAA's water were run instead, everywhere.""")
    return dict(refused=len(refused), base=base)


def main():
    """Print the comparison; every figure is computed from the runs."""
    _banner()
    caught = set()
    runs, profiles = load()
    print(f"\n{len(runs)} OSOAA runs from {RUNS}")
    check = check_part(runs, profiles, caught)
    found = jerlov_part(runs, profiles, caught)
    moves = factor_part(runs, profiles)
    verdict = verdict_part(found, moves, caught)
    refused = not_run_part(runs)
    if caught:
        rule("Warnings")
        print("Raised along the way, and caught by type:")
        for message in sorted(caught):
            print(f"  - {message}")

    rule("Before you use any of this")
    print("""  - One code, OSOAA (CNES, commit 8e4914f), one sun (30 degrees), one sky,
    and Petzold's phase functions, which he measured as water and particles
    together. Another code has not been compared (OPEN_QUESTIONS.md).
  - Kd is the mean over the first penetration depth; to the 10 percent
    depth instead it moves by under 1 percent.
  - Jerlov's Kd and Williamson & Hollins's IOPs are each summaries of many
    waters under one name. Which is closer to a given sea, this does not
    say.
""")
    return dict(runs=runs, check=check, found=found, moves=moves,
                verdict=verdict, refused=refused, caught=caught)


if __name__ == "__main__":
    main()

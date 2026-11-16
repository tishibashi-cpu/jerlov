"""Solonenko & Mobley's IOPs through OSOAA: DECISIONS.md section 94.

    python tools/osoaa_sm_closure.py OSOAA_ROOT WORK_DIR

The 143 cells of ``tools/sm_closure.py`` (Solonenko & Mobley's (2015) ten
Jerlov types, 350-700 nm every 25 nm, where a, b and K_d^H are all
given), with the sun of their Eq. (3) (15 degrees from the zenith for the
oceanic types, 45 for the coastal), the phase function of NUC 2240 as
``osoaa_phase_function`` writes it, OSOAA's maritime aerosol of section 90
at an AOT(550) of 0.2 and of 0.05, and a wind of 2 m/s. OSOAA adds its own
pure seawater back, so its own a_w and b_w are subtracted: the totals it
runs are Solonenko & Mobley's. Where their a or b is below OSOAA's own
pure water the run cannot be made and is recorded as not run.

OSOAA is not part of this package and CI cannot run this script; it is
run by hand with OSOAA as built for section 93 (CNES, commit 8e4914f). It
writes ``examples/data/osoaa_sm_closure/runs.csv`` and ``ed.csv``.
"""

from __future__ import annotations

import concurrent.futures
import csv
import pathlib
import sys
import warnings

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import jerlov  # noqa: E402
import osoaa_closure as oc  # noqa: E402
import sm_closure as sm  # noqa: E402

OUT = (pathlib.Path(__file__).resolve().parent.parent / "examples" / "data"
       / "osoaa_sm_closure")
AOTS = (0.2, 0.05)
WIND = 2.0
#: The seabed lies this many penetration depths down, by K_d^H.
DEPTH_IN_PENETRATION_DEPTHS = 6.0


def runs():
    out = []
    for aot in AOTS:
        for t, wl, a, b, kdh, flags in sm.cells():
            sun = sm.SUN_OCEANIC if t in sm.OCEANIC else sm.SUN_COASTAL
            out.append(dict(run_id=len(out), factor="base" if aot == sm.AOT
                            else "aot", value="" if aot == sm.AOT
                            else f"{aot:g}", water_type=t, wavelength_nm=wl,
                            sun_deg=sun, station=sm.STATION, aot=aot,
                            wind=WIND, a=a, b=b, kd_hydrolight=kdh))
    return out


def inputs(run, root):
    """OSOAA's two files for a run: Solonenko & Mobley's totals."""
    wl = float(run["wavelength_nm"])
    water = jerlov.water(run["water_type"], source="solonenko2015")
    aw_osoaa, bw_osoaa = oc.osoaa_pure_water(root, wl)
    depth = round(DEPTH_IN_PENETRATION_DEPTHS / run["kd_hydrolight"])
    profile = jerlov.osoaa_user_profile(
        water, wl, depths_m=[0.0, float(depth)],
        pure_water=(aw_osoaa, bw_osoaa))
    phase = jerlov.osoaa_phase_function(
        jerlov.petzold_scattering(run["station"]), **oc.RATIOS)
    return profile, phase, depth, aw_osoaa


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    root = pathlib.Path(sys.argv[1]).resolve()
    work = pathlib.Path(sys.argv[2]).resolve()
    if not (root / "exe" / "OSOAA_MAIN.exe").exists():
        raise SystemExit(f"no built OSOAA under {root}")
    work.mkdir(parents=True, exist_ok=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        plan = runs()
    print(f"{len(plan)} runs")
    results = {}
    with concurrent.futures.ThreadPoolExecutor(oc.MAX_WORKERS) as pool:
        for run, depth, aw, flux in pool.map(
                lambda r: oc.run_osoaa(r, root, work, inputs), plan):
            results[run["run_id"]] = (run, depth, aw, flux)
            if len(results) % 20 == 0:
                print(f"  {len(results)} done", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "runs.csv", "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["run_id", "factor", "value", "water_type",
                         "wavelength_nm", "sun_deg", "station", "aot",
                         "wind", "a", "b", "kd_hydrolight", "sea_depth_m",
                         "osoaa_aw", "status"])
        for key in sorted(results):
            run, depth, aw, flux = results[key]
            ran = not isinstance(flux, str)
            writer.writerow([run["run_id"], run["factor"], run["value"],
                             run["water_type"], run["wavelength_nm"],
                             f"{run['sun_deg']:g}", run["station"],
                             f"{run['aot']:g}", f"{run['wind']:g}",
                             repr(run["a"]), repr(run["b"]),
                             repr(run["kd_hydrolight"]),
                             depth if ran else "", repr(aw) if ran else "",
                             "ok" if ran else "not_run: " + flux])
    rows = 0
    with open(OUT / "ed.csv", "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["run_id", "depth_m", "ed"])
        for key in sorted(results):
            flux = results[key][3]
            if isinstance(flux, str):
                continue
            for depth, ed in zip(flux.sea_depths_m,
                                 flux.total_down[flux.in_sea]):
                writer.writerow([key, repr(float(depth)), repr(float(ed))])
                rows += 1
    print(f"wrote {OUT / 'runs.csv'} ({len(results)} runs) and "
          f"{OUT / 'ed.csv'} ({rows} rows)")


if __name__ == "__main__":
    main()

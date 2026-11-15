"""Run OSOAA over the Jerlov types and keep its Ed: DECISIONS.md section 90.

Williamson & Hollins's a and b for six Jerlov types, at the twelve
wavelengths Jerlov printed inside their measured range (425-700 nm), are
written with the package's own OSOAA writers, run through OSOAA, and its
Ed in the sea is kept, so that the Kd OSOAA makes of them can be set beside
the Kd Jerlov printed. Then the inputs a Jerlov type does not fix are
varied one at a time on IB and III: the sun, the phase function, the pure
water, the sky and the surface.

    python tools/osoaa_closure.py OSOAA_ROOT WORK_DIR

OSOAA_ROOT is a built copy of CNES's RadiativeTransferCode-OSOAA (GPL v3;
commit 8e4914f was used), WORK_DIR a scratch folder for its runs. OSOAA is
not part of this package, and CI cannot run this script; it writes
``examples/data/osoaa_closure/runs.csv`` and ``ed.csv``, which
``examples/closure_with_jerlov_kd.py`` and the tests read (DECISIONS.md
section 91).
"""

from __future__ import annotations

import concurrent.futures
import csv
import os
import pathlib
import subprocess
import sys
import warnings


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import jerlov  # noqa: E402

OUT = (pathlib.Path(__file__).resolve().parent.parent / "examples" / "data"
       / "osoaa_closure")
TYPES = ("IB", "II", "III", "1C", "3C", "5C")
#: Jerlov's printed wavelengths inside Williamson & Hollins's measured
#: 412-715 nm.
WAVELENGTHS = tuple(range(425, 701, 25))
FACTOR_TYPES = ("IB", "III")
#: The polarization ratios of examples/radiative_transfer_inputs.py: the
#: package's assumption, Petzold measured none.
RATIOS = dict(minus_f12_over_f11=0.0, f22_over_f11=1.0, f33_over_f11=1.0)
BASE = dict(sun_deg=30.0, aot=0.1, wind=7.0, pure_water="williamson2022")
#: The seabed lies this many penetration depths down, by Jerlov's 1976 Kd.
DEPTH_IN_PENETRATION_DEPTHS = 6.0
MAX_WORKERS = 4


def nearest_station(water_type: str) -> str:
    b = float(jerlov.water(water_type).b(530.0))
    return min(jerlov.PETZOLD_STATIONS,
               key=lambda s: abs(jerlov.petzold_scattering(s).b - b))


def osoaa_pure_water(root: pathlib.Path, wavelength: float):
    """OSOAA's own pure seawater, the a and b it adds back."""
    path = root / "fic" / "OSOAA_SEA_MOL_COEFFS_JUNE_2013.txt"
    for line in path.read_text().splitlines():
        fields = line.split()
        if fields and float(fields[0]) == wavelength:
            return float(fields[1]), float(fields[2])
    raise KeyError(wavelength)


def runs():
    """Every run: the base set, then each factor alone on IB and III."""
    out = []

    def add(factor, value, water_type, wavelength, **changes):
        run = {**BASE, "station": nearest_station(water_type), **changes}
        out.append(dict(run_id=len(out), factor=factor, value=value,
                        water_type=water_type, wavelength_nm=wavelength,
                        **run))

    for water_type in TYPES:
        for wl in WAVELENGTHS:
            add("base", "", water_type, wl)
    # Williamson & Hollins's contents on OSOAA's own pure water: always
    # runnable, where the type's total in the red is not.
    for water_type in TYPES:
        for wl in WAVELENGTHS:
            add("pure_water", "osoaa", water_type, wl, pure_water="osoaa")
    for water_type in FACTOR_TYPES:
        for wl in WAVELENGTHS:
            for sun in (0.0, 60.0):
                add("sun_deg", f"{sun:g}", water_type, wl, sun_deg=sun)
            for station in ("AUTEC 8", "HAOCE 5", "NUC 2200"):
                add("station", station, water_type, wl, station=station)
            for source in ("pope1997", "mason2016", "lee2015"):
                low, high = {"pope1997": (380, 727.5),
                             "mason2016": (250, 550),
                             "lee2015": (350, 550)}[source]
                if low <= wl <= high:
                    add("pure_water", source, water_type, wl,
                        pure_water=source)
            for aot in (0.05, 0.3):
                add("aot", f"{aot:g}", water_type, wl, aot=aot)
            for wind in (2.0, 15.0):
                add("wind", f"{wind:g}", water_type, wl, wind=wind)
    return out


def inputs(run, root):
    """The two OSOAA files for a run, from the package's writers."""
    wl = float(run["wavelength_nm"])
    water = jerlov.water(run["water_type"])
    aw_osoaa, bw_osoaa = osoaa_pure_water(root, wl)
    # OSOAA adds aw_osoaa back. To run a total of a - aw_WH + aw_X, take
    # off aw_WH - aw_X + aw_osoaa; at the base, aw_X = aw_WH.
    aw_wh = float(jerlov.pure_water_absorption(wl))
    if run["pure_water"] == "williamson2022":
        aw_x = aw_wh
    elif run["pure_water"] == "osoaa":
        aw_x = aw_osoaa
    else:
        aw_x = float(jerlov.pure_water_absorption_table(
            wl, source=run["pure_water"]))
    subtract = (aw_wh - aw_x + aw_osoaa, bw_osoaa)
    kd = float(jerlov.water(run["water_type"], source="jerlov1976").kd(wl))
    depth = round(DEPTH_IN_PENETRATION_DEPTHS / kd)
    profile = jerlov.osoaa_user_profile(
        water, wl, depths_m=[0.0, float(depth)], pure_water=subtract)
    phase = jerlov.osoaa_phase_function(
        jerlov.petzold_scattering(run["station"]), **RATIOS)
    return profile, phase, depth, aw_x


def run_osoaa(run, root: pathlib.Path, work: pathlib.Path):
    """OSOAA's Flux for one run, or None where OSOAA cannot be given it.

    OSOAA always adds its own pure water back. Where the total to be run
    is below OSOAA's own pure water, as Williamson & Hollins's a is in the
    red, where it is little more than their own aw, or as a total built on
    a smaller aw is, the profile would be negative, which the writer
    refuses: such a run is recorded as not run (DECISIONS.md section 90).
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        try:
            profile, phase, depth, aw_x = inputs(run, root)
        except ValueError as refused:
            if "less the pure water given is negative" not in str(refused):
                raise
            return run, None, None, str(refused).split(":")[0]
    where = work / f"run{run['run_id']:04d}"
    flux_path = where / "Advanced_outputs" / "Flux.txt"
    # A run already made with the same inputs is read, not repeated.
    if (flux_path.exists() and (where / "profile.txt").exists()
            and (where / "profile.txt").read_text() == profile
            and (where / "phase.txt").read_text() == phase
            and (where / "command.txt").exists()):
        return run, depth, aw_x, jerlov.read_osoaa_flux(
            flux_path.read_text())
    for sub in ("MIE_AER", "MIE_HYD", "SURF"):
        (where / sub).mkdir(parents=True, exist_ok=True)
    (where / "profile.txt").write_text(profile)
    (where / "phase.txt").write_text(phase)
    command = [
        str(root / "exe" / "OSOAA_MAIN.exe"),
        "-OSOAA.ResRoot", str(where), "-OSOAA.Log", "Main.Log",
        "-OSOAA.Wa", f"{run['wavelength_nm'] / 1000:.3f}",
        "-ANG.Thetas", f"{run['sun_deg']:g}",
        "-AP.Pressure", "1013.0", "-AP.HR", "8.0", "-AP.HA", "2.0",
        "-AER.Waref", "0.550", "-AER.AOTref", f"{run['aot']:g}",
        "-AER.DirMie", str(where / "MIE_AER"), "-AER.Model", "2",
        "-AER.SF.Model", "3", "-AER.SF.RH", "98.",
        "-SEA.Depth", f"{depth:.1f}", "-HYD.DirMie", str(where / "MIE_HYD"),
        "-HYD.Model", "3", "-HYD.ExtData", str(where / "phase.txt"),
        "-HYD.UserProfile", str(where / "profile.txt"),
        "-SEA.Dir", str(where / "SURF"), "-SEA.Ind", "1.34",
        "-SEA.Wind", f"{run['wind']:g}", "-SEA.SurfAlb", "0.0",
        "-SEA.BotType", "1", "-SEA.BotAlb", "0.0",
        "-OSOAA.View.Phi", "0.0", "-OSOAA.View.Level", "4",
    ]
    env = dict(os.environ, OSOAA_ROOT=str(root))
    done = subprocess.run(command, cwd=where, env=env, capture_output=True,
                          text=True)
    if done.returncode != 0 or not flux_path.exists():
        raise RuntimeError(f"run {run['run_id']} failed: "
                           f"{done.stdout[-400:]} {done.stderr[-400:]}")
    (where / "command.txt").write_text(" ".join(command[1:]))
    flux = jerlov.read_osoaa_flux(flux_path.read_text())
    return run, depth, aw_x, flux


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    root = pathlib.Path(sys.argv[1]).resolve()
    work = pathlib.Path(sys.argv[2]).resolve()
    if not (root / "exe" / "OSOAA_MAIN.exe").exists():
        raise SystemExit(f"no built OSOAA under {root}")
    work.mkdir(parents=True, exist_ok=True)
    plan = runs()
    print(f"{len(plan)} runs")
    results = {}
    with concurrent.futures.ThreadPoolExecutor(MAX_WORKERS) as pool:
        for run, depth, aw_x, flux in pool.map(
                lambda r: run_osoaa(r, root, work), plan):
            results[run["run_id"]] = (run, depth, aw_x, flux)
            if len(results) % 20 == 0:
                print(f"  {len(results)} done")
    OUT.mkdir(parents=True, exist_ok=True)
    fields = ["run_id", "factor", "value", "water_type", "wavelength_nm",
              "sun_deg", "station", "pure_water", "aot", "wind",
              "sea_depth_m", "aw_total_pure_water", "status"]
    with open(OUT / "runs.csv", "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(fields)
        for key in sorted(results):
            run, depth, aw_x, flux = results[key]
            ran = not isinstance(flux, str)
            writer.writerow([run["run_id"], run["factor"], run["value"],
                             run["water_type"], run["wavelength_nm"],
                             f"{run['sun_deg']:g}", run["station"],
                             run["pure_water"], f"{run['aot']:g}",
                             f"{run['wind']:g}", depth if ran else "",
                             repr(aw_x) if ran else "",
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
                # As OSOAA printed them: the floats read back exactly.
                writer.writerow([key, repr(float(depth)), repr(float(ed))])
                rows += 1
    print(f"wrote {OUT / 'runs.csv'} ({len(results)} runs) and "
          f"{OUT / 'ed.csv'} ({rows} rows)")


if __name__ == "__main__":
    main()

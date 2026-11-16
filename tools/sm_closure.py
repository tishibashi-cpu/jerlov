"""Solonenko & Mobley's IOPs through the Monte Carlo, against their
HydroLight Kd: DECISIONS.md section 94.

    python tools/sm_closure.py

Runs tools/kd_monte_carlo.py on the 143 cells of Solonenko & Mobley's
(2015) ten Jerlov types from 350 to 700 nm every 25 nm where a, b and
K_d^H are all given: as section 92 ran (no water share, no sky), with
pure water's share of the scattering alone, and with it and a sky (the
base); then on the base, one at a time, the seven other Petzold
stations, the sun at 0, 30 and 60 degrees and tau_a(550) of 0.05 and
0.4. Then Williamson & Hollins's 72 base cells of section 92 again, with
the water share and with the water share and the sky, and section 92's
168 factor runs with both. Writes
examples/data/sm_closure/runs.csv: every run's parameters, seed and Kd.
About half an hour on four cores.

Every run of one cell uses the same seed, so that differences between
them are not swamped by the noise; the Williamson & Hollins runs use the
seeds of their base runs in examples/data/kd_closure/runs.csv. Running
it again on the same NumPy gives the same file.
"""

from __future__ import annotations

import concurrent.futures
import csv
import importlib.resources
import io
import math
import pathlib
import sys
import warnings

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import jerlov  # noqa: E402
import kd_closure  # noqa: E402
import kd_monte_carlo as mc  # noqa: E402

OUT = (pathlib.Path(__file__).resolve().parent.parent / "examples" / "data"
       / "sm_closure")
TYPES = ("I", "IA", "IB", "II", "III", "1C", "3C", "5C", "7C", "9C")
OCEANIC = ("I", "IA", "IB", "II", "III")
WAVELENGTHS = tuple(range(350, 701, 25))
#: The sun of the paper's own Eq. (3), p. 5394: elevation 75 degrees for
#: the oceanic types and 45 for the coastal.
SUN_OCEANIC, SUN_COASTAL = 15.0, 45.0
#: The Petzold station whose mean cosine (0.9255) is nearest the 0.924 of
#: the average-particle phase function (p. 5394).
STATION = "NUC 2240"
AOT = 0.2
#: The atmosphere of examples/sunlight_and_d65.py.
ATMOSPHERE = dict(day_of_year=172, pressure_hpa=1013.25, air_mass_type=1,
                  relative_humidity=80.0, precipitable_water_cm=1.5,
                  wind_speed_24h=3.0, wind_speed=5.0, ozone_du=300.0)
PHOTONS = 400_000
TO_10_PERCENT = math.log(10.0)


def sky_share(sun_deg: float, wavelength: float, aot: float) -> float:
    """The diffuse share of Ed just below the surface, Gregg & Carder."""
    s = jerlov.gregg1990_irradiance(
        int(wavelength), sun_zenith_deg=sun_deg,
        aerosol_optical_thickness_550=aot, **ATMOSPHERE)
    return float(s.diffuse_below / s.below)


def water_share(source: str, water_type: str, wavelength: float,
                b: float) -> float:
    """bw / b, with bw the source's own pure-water term, Eq. (8a)."""
    constants = jerlov.water(water_type, source=source).source.scattering
    bw = constants.bw_coeff * (400.0 / wavelength) ** constants.bw_exponent
    if not 0.0 < bw < b:
        raise ValueError(f"bw {bw} is not below b {b}")
    return bw / b


def _statuses():
    """Each shipped value's status, from the package's own table."""
    text = (importlib.resources.files("jerlov.data")
            / "solonenko2015_iop.csv").read_text()
    return {(row["water_type"], int(float(row["wavelength_nm"])),
             row["quantity"]): row["status"]
            for row in csv.DictReader(io.StringIO(text))}


STATUS = _statuses()


def cells():
    """(type, wavelength, a, b, K_d^H, flags) where all three are given."""
    out = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        for water_type in TYPES:
            water = jerlov.water(water_type, source="solonenko2015")
            for wl in WAVELENGTHS:
                a = float(water.a(wl))
                b = float(water.b(wl))
                kdh = float(water.kd_hydrolight(wl))
                if math.isnan(a + b + kdh):
                    continue
                flags = {q: STATUS[(water_type, wl, q)]
                         for q in ("a", "b", "KdH")}
                out.append((water_type, wl, a, b, kdh, flags))
    return out


def runs():
    out = []

    def add(cell_id, factor, value, water_type, wl, a, b, kdh, flags,
            source, seed, sun, station, aot, water, sky):
        out.append(dict(
            run_id=len(out), set=source, factor=factor, value=value,
            water_type=water_type, wavelength_nm=wl, sun_deg=sun,
            station=station, aot_550="" if aot is None else aot,
            water_share=water, sky_share=sky, a=a, b=b,
            kd_hydrolight=kdh, flags=flags, seed=seed))

    for cell_id, (t, wl, a, b, kdh, flags) in enumerate(cells()):
        sun = SUN_OCEANIC if t in OCEANIC else SUN_COASTAL
        eta = water_share("solonenko2015", t, wl, b)
        sky = sky_share(sun, wl, AOT)
        common = (t, wl, a, b, kdh, flags, "solonenko2015", cell_id + 1)
        add(cell_id, "as_section_92", "", *common, sun, STATION, None,
            0.0, 0.0)
        add(cell_id, "water_only", "", *common, sun, STATION, None, eta, 0.0)
        add(cell_id, "base", "", *common, sun, STATION, AOT, eta, sky)
        for station in jerlov.PETZOLD_STATIONS:
            if station != STATION:
                add(cell_id, "station", station, *common, sun, station, AOT,
                    eta, sky)
        for other in (0.0, 30.0, 60.0):
            add(cell_id, "sun_deg", f"{other:g}", *common, other, STATION,
                AOT, eta, sky_share(other, wl, AOT))
        for aot in (0.05, 0.4):
            add(cell_id, "aot", f"{aot:g}", *common, sun, STATION, aot, eta,
                sky_share(sun, wl, aot))
    for run in kd_closure.runs():
        if run["factor"] != "base":
            continue
        a, b = kd_closure.iops(run)
        t, wl = run["water_type"], run["wavelength_nm"]
        eta = water_share("williamson2022", t, wl, b)
        common = (t, wl, a, b, "", {}, "williamson2022", run["run_id"] + 1)
        add(None, "water_only", "", *common, run["sun_deg"], run["station"],
            None, eta, 0.0)
        add(None, "base", "", *common, run["sun_deg"], run["station"], AOT,
            eta, sky_share(run["sun_deg"], wl, AOT))
    # Section 92's factor runs again, with the water share and the sky, so
    # that the reach of its section 3 can be taken from the same
    # Monte Carlo (added after the first run; DECISIONS.md section 94).
    for run in kd_closure.runs():
        if run["factor"] == "base":
            continue
        a, b = kd_closure.iops(run)
        t, wl = run["water_type"], run["wavelength_nm"]
        eta = water_share("williamson2022", t, wl, b)
        common = (t, wl, a, b, "", {}, "williamson2022", run["run_id"] + 1)
        add(None, run["factor"], run["value"], *common, run["sun_deg"],
            run["station"], AOT, eta, sky_share(run["sun_deg"], wl, AOT))
    return out


def one(run):
    sample, _ = mc.petzold_sampler(run["station"])
    k1, k10 = mc.kd(run["a"], run["b"], sample, run["sun_deg"],
                    optical_depths=(1.0, TO_10_PERCENT), photons=PHOTONS,
                    seed=run["seed"], water_share=run["water_share"],
                    sky_share=run["sky_share"])
    return run, k1, k10


def main() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        plan = runs()
    print(f"{len(plan)} runs")
    results = []
    with concurrent.futures.ProcessPoolExecutor(4) as pool:
        for n, result in enumerate(pool.map(one, plan, chunksize=4), 1):
            results.append(result)
            if n % 100 == 0:
                print(f"  {n} done", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "runs.csv", "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["run_id", "set", "factor", "value", "water_type",
                         "wavelength_nm", "sun_deg", "station", "aot_550",
                         "water_share", "sky_share", "a", "b",
                         "kd_hydrolight", "status_a", "status_b",
                         "status_kd_hydrolight", "seed", "photons",
                         "kd_first_penetration_depth", "kd_to_10_percent"])
        for run, k1, k10 in results:
            flags = run["flags"]
            writer.writerow([
                run["run_id"], run["set"], run["factor"], run["value"],
                run["water_type"], run["wavelength_nm"],
                f"{run['sun_deg']:g}", run["station"], run["aot_550"],
                repr(run["water_share"]), repr(run["sky_share"]),
                repr(run["a"]), repr(run["b"]),
                "" if run["kd_hydrolight"] == "" else
                repr(run["kd_hydrolight"]),
                flags.get("a", ""), flags.get("b", ""), flags.get("KdH", ""),
                run["seed"], PHOTONS, repr(k1), repr(k10)])
    print(f"wrote {OUT / 'runs.csv'} ({len(results)} runs)")


if __name__ == "__main__":
    main()

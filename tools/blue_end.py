"""Why the blue end disagrees: DECISIONS.md section 95.

    python tools/blue_end.py

Reads three files of Williamson & Hollins's figshare dataset (DOI
10.6084/m9.figshare.20290782, Version 3; Crown copyright (2022), Dstl,
Open Government Licence v3.0) from ``sources/20290782/``, checks each
against figshare's MD5, and writes ``examples/data/blue_end/``:

- ``kd_campaigns.csv``: the Kd of every campaign they kept, over the
  upper 10 m, with the Jerlov type they gave it (``op_STEP_5_k.csv``,
  rows not flagged for removal; only the campaign, the type, the
  wavelength, Kd and the fit's MAPE are kept);
- ``iop_campaigns.csv``: a and b of every campaign that went into their
  averages, with its type (``op_STEP_5_a.csv``, ``op_STEP_5_b.csv``);
- ``matched.csv``: ``op_STEP_7_kab.csv`` as it is, a, b and Kd measured in
  the same campaign at the same wavelength;
- ``runs.csv``: the Monte Carlo's Kd from each matched entry's own a and b
  (tools/kd_monte_carlo.py with section 94's options), its seed and
  parameters. About fifteen minutes on four cores.

    python tools/blue_end.py --closing

writes ``closing_a.csv`` instead: for each blue cell of section 94 that
lies beyond the reach of the conditions, the a that would make the Monte
Carlo's Kd equal Jerlov's (1976), b and everything else as section 94's
Williamson & Hollins base, found by the secant method on the logarithm
with a fixed seed.
"""

from __future__ import annotations

import concurrent.futures
import csv
import hashlib
import math
import pathlib
import shutil
import sys
import warnings

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import jerlov  # noqa: E402
import kd_monte_carlo as mc  # noqa: E402
import sm_closure  # noqa: E402

SOURCE = ROOT / "sources" / "20290782"
OUT = ROOT / "examples" / "data" / "blue_end"
#: figshare's MD5 of each file read (api.figshare.com, 2026-11-16).
MD5 = {"op_STEP_5_k.csv": "3bee1ffd65aa0c4a799f0497ae5d2ce7",
       "op_STEP_5_a.csv": "ef8df888747dc9f7c36bdac8c209ecd6",
       "op_STEP_5_b.csv": "4171598067cc44b8bdced4acab0e23ac",
       "op_STEP_7_kab.csv": "64fdbfcdad23c600375e62c472aa2bff"}
BASE = dict(sun_deg=30.0, station="NUC 2240")
#: The stations with the lowest and highest bb/b (0.013 and 0.044).
STATIONS = ("HAOCE 11", "AUTEC 8")
SUNS = (0.0, 60.0)
PHOTONS = 400_000


def check_sources() -> None:
    for name, digest in MD5.items():
        path = SOURCE / name
        if not path.exists():
            raise SystemExit(f"missing {path}: see sources/README.md")
        got = hashlib.md5(path.read_bytes()).hexdigest()
        if got != digest:
            raise SystemExit(f"{path}: MD5 {got}, figshare says {digest}")


def _type(label: str) -> str:
    """'c_IB' -> 'IB'."""
    return label.split("_", 1)[1]


def write_tables() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with open(SOURCE / "op_STEP_5_k.csv", newline="") as handle:
        rows = [r for r in csv.DictReader(handle)
                if float(r["FlagRemove"] or 0) == 0]
    with open(OUT / "kd_campaigns.csv", "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["campaign", "water_type", "wavelength_nm", "kd",
                         "mape"])
        for r in rows:
            writer.writerow([int(float(r["Campaign_Num"])),
                             _type(r["Jerlov"]),
                             int(float(r["CENTWAVE"])), r["Val"], r["mape"]])
    with open(OUT / "iop_campaigns.csv", "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["campaign", "water_type", "quantity",
                         "wavelength_nm", "value"])
        for quantity in ("a", "b"):
            with open(SOURCE / f"op_STEP_5_{quantity}.csv",
                      newline="") as source:
                for r in csv.DictReader(source):
                    writer.writerow([int(float(r["Campaign_Num"])),
                                     _type(r["Jerlov"]), quantity,
                                     int(float(r["CENTWAVE"])), r["Val"]])
    shutil.copyfile(SOURCE / "op_STEP_7_kab.csv", OUT / "matched.csv")


def matched():
    with open(OUT / "matched.csv", newline="") as handle:
        return [dict(entry=int(r[""]), campaign=int(float(r["Campaign_Num"])),
                     water_type=_type(r["Jerlov"]),
                     wavelength_nm=int(r["CENTWAVE"]), kd=float(r["Val_Kd"]),
                     a=float(r["Val_a"]), b=float(r["Val_b"]))
                for r in csv.DictReader(handle)]


def runs():
    """The base and each factor for every matched entry that can run."""
    constants = jerlov.water("III").source.scattering
    out = []
    for e in matched():
        wl = e["wavelength_nm"]
        bw = constants.bw_coeff * (400.0 / wl) ** constants.bw_exponent
        status = ("not_run: a is not positive" if e["a"] <= 0 else
                  "not_run: b is not above bw" if e["b"] <= bw else "ok")
        variants = [("base", "", BASE["sun_deg"], BASE["station"])]
        variants += [("station", s, BASE["sun_deg"], s) for s in STATIONS]
        variants += [("sun_deg", f"{s:g}", s, BASE["station"]) for s in SUNS]
        for factor, value, sun, station in variants:
            out.append(dict(
                run_id=len(out), entry=e["entry"], factor=factor, value=value,
                campaign=e["campaign"], water_type=e["water_type"],
                wavelength_nm=wl, a=e["a"], b=e["b"], kd_measured=e["kd"],
                sun_deg=sun, station=station,
                water_share=bw / e["b"] if status == "ok" else "",
                sky_share=(sm_closure.sky_share(sun, wl, sm_closure.AOT)
                           if status == "ok" else ""),
                seed=e["entry"] + 1, status=status))
    return out


def one(run):
    if run["status"] != "ok":
        return run, "", ""
    sample, _ = mc.petzold_sampler(run["station"])
    k1, k10 = mc.kd(run["a"], run["b"], sample, run["sun_deg"],
                    optical_depths=(1.0, math.log(10.0)), photons=PHOTONS,
                    seed=run["seed"], water_share=run["water_share"],
                    sky_share=run["sky_share"])
    return run, repr(k1), repr(k10)


#: Section 94's blue cells beyond the reach (DATA.md section 40).
BEYOND = (("IB", 425), ("IB", 450), ("IB", 475), ("IB", 500), ("1C", 425),
          ("3C", 425), ("3C", 450), ("5C", 425))


def closing_a(cell):
    """The a at which the Monte Carlo's Kd over the first penetration
    depth equals Jerlov's (1976), with section 94's base for Williamson &
    Hollins's cell otherwise."""
    water_type, wl = cell
    base = next(r for r in sm_closure.runs()
                if r["set"] == "williamson2022" and r["factor"] == "base"
                and r["water_type"] == water_type
                and r["wavelength_nm"] == wl)
    target = float(jerlov.water(water_type, source="jerlov1976").kd(wl))
    sample, _ = mc.petzold_sampler(base["station"])
    constants = jerlov.water(water_type).source.scattering
    bw = constants.bw_coeff * (400.0 / wl) ** constants.bw_exponent

    def kd(a):
        (k,) = mc.kd(a, base["b"], sample, base["sun_deg"], photons=PHOTONS,
                     seed=base["seed"], water_share=bw / base["b"],
                     sky_share=base["sky_share"])
        return k

    x0, f0 = math.log(base["a"]), math.log(kd(base["a"]) / target)
    x1 = x0 - f0
    f1 = math.log(kd(math.exp(x1)) / target)
    for _ in range(8):
        if abs(f1) < 1e-4:
            break
        x0, x1, f0 = x1, x1 - f1 * (x1 - x0) / (f1 - f0), f1
        f1 = math.log(kd(math.exp(x1)) / target)
    return cell, base["a"], base["b"], target, math.exp(x1), f1


def main_closing() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        with concurrent.futures.ProcessPoolExecutor(4) as pool:
            results = list(pool.map(closing_a, BEYOND))
    with open(OUT / "closing_a.csv", "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["water_type", "wavelength_nm", "a", "b",
                         "jerlov1976_kd", "closing_a", "residual_log"])
        for (water_type, wl), a, b, target, a_star, res in results:
            writer.writerow([water_type, wl, repr(a), repr(b), repr(target),
                             repr(a_star), repr(res)])
    print(f"wrote {OUT / 'closing_a.csv'}")


def main() -> None:
    if "--closing" in sys.argv:
        main_closing()
        return
    check_sources()
    write_tables()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        plan = runs()
    print(f"{len(plan)} runs")
    results = []
    with concurrent.futures.ProcessPoolExecutor(4) as pool:
        for n, result in enumerate(pool.map(one, plan, chunksize=4), 1):
            results.append(result)
            if n % 200 == 0:
                print(f"  {n} done", flush=True)
    fields = ["run_id", "entry", "factor", "value", "campaign", "water_type",
              "wavelength_nm", "a", "b", "kd_measured", "sun_deg", "station",
              "water_share", "sky_share", "seed", "photons", "status",
              "kd_first_penetration_depth", "kd_to_10_percent"]
    with open(OUT / "runs.csv", "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(fields)
        for run, k1, k10 in results:
            writer.writerow([
                run["run_id"], run["entry"], run["factor"], run["value"],
                run["campaign"], run["water_type"], run["wavelength_nm"],
                repr(run["a"]), repr(run["b"]), repr(run["kd_measured"]),
                f"{run['sun_deg']:g}", run["station"],
                "" if run["water_share"] == "" else repr(run["water_share"]),
                "" if run["sky_share"] == "" else repr(run["sky_share"]),
                run["seed"], PHOTONS, run["status"], k1, k10])
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

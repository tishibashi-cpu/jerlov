"""Input files for OSOAA and HydroLight from a Jerlov type.

For people who solve the radiative transfer equation with one of those
codes and want a Jerlov type as its water:

    python examples/radiative_transfer_inputs.py                 # print
    python examples/radiative_transfer_inputs.py --write out/    # also files
    python examples/radiative_transfer_inputs.py --read RESULTS/ # and OSOAA's

With --read, the folder of an OSOAA run made with these files
(-OSOAA.ResRoot), it also reads OSOAA's results back and sets the Kd OSOAA
made of the water beside Jerlov's own Kd and the Kd HydroLight made of
another source's IOPs for the same type.

It writes Jerlov III at 440 nm for OSOAA, with Petzold's HAOCE 5 phase
function, and Jerlov III from 400 to 700 nm for HydroLight, and prints the
OSOAA command line that takes them. It runs neither code. Both add their own
pure water back to what they are given, so the pure water to subtract is the
one the run will add; the example shows what a different one does
(DECISIONS.md section 86).
"""

import pathlib
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


WATER_TYPE = "III"
#: OSOAA runs at one wavelength, in micrometres on its command line.
OSOAA_NM = 440.0
#: OSOAA's own pure seawater at 440 nm, from its file
#: fic/OSOAA_SEA_MOL_COEFFS_JUNE_2013.txt: what it adds back.
OSOAA_PURE_WATER = (0.00635, 0.00501629)
#: The depths of the OSOAA profile, m; the type is the same at every depth.
OSOAA_DEPTHS_M = (0.0, 10.0, 50.0)
#: Petzold's station for the phase function: this example's choice.
STATION = "HAOCE 5"
#: Petzold measured no polarization. These ratios leave the polarization
#: of the light unchanged by scattering: this example's assumption, not a
#: measurement.
RATIOS = dict(minus_f12_over_f11=0.0, f22_over_f11=1.0, f33_over_f11=1.0)
HYDROLIGHT_NM = np.arange(400.0, 701.0, 10.0)
HYDROLIGHT_DEPTHS_M = (0.0, 50.0)
#: The pure water for HydroLight: the aw Williamson & Hollins built their a
#: on, and Morel's bw at salinity 35. This example's choice; the HydroLight
#: run must be set to add the same.
SALINITY_PSU = 35.0
SOURCES_TYPES = ("IB", "II", "III", "1C", "3C", "5C")


def caught_by_type(caught, function, *args, **kwargs):
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always", jerlov.ProvenanceWarning)
        warnings.simplefilter("always", jerlov.CoverageWarning)
        result = function(*args, **kwargs)
    caught.update(f"{w.category.__name__}: {str(w.message).split(':')[0]}"
                  for w in seen)
    return result


def osoaa_part(caught):
    rule(f"1. OSOAA: Jerlov {WATER_TYPE} at {OSOAA_NM:g} nm")
    water = jerlov.water(WATER_TYPE)
    profile = caught_by_type(caught, jerlov.osoaa_user_profile, water,
                             OSOAA_NM, depths_m=OSOAA_DEPTHS_M,
                             pure_water=OSOAA_PURE_WATER)
    phase = caught_by_type(caught, jerlov.osoaa_phase_function,
                           jerlov.petzold_scattering(STATION), **RATIOS)
    a = float(caught_by_type(caught, water.a, OSOAA_NM))
    b = float(caught_by_type(caught, water.b, OSOAA_NM))
    hydrosol = profile.split("\n")[5].split()[1:]
    print(f"""Williamson & Hollins's a = {a:.4g} and b = {b:.4g} per m. Less OSOAA's own pure
seawater ({OSOAA_PURE_WATER[0]:g} and {OSOAA_PURE_WATER[1]:g}), the profile gives the hydrosols
a = {float(hydrosol[0]):.5g} and b = {float(hydrosol[1]):.5g}, and OSOAA adds its water back: c = {a + b:.4g},
b/c = {b / (a + b):.4f}. The phase function is 4 pi times {STATION}'s vsf / b at
Petzold's 55 angles: OSOAA takes its integral over the sphere as 4 pi.

The profile:
""")
    print("  " + profile.replace("\n", "\n  "))
    # The other pure water a caller might reach for: the one Williamson &
    # Hollins built a on.
    aw_wh = float(jerlov.pure_water_absorption(OSOAA_NM))
    print(f"""
Williamson & Hollins built their a on aw = {aw_wh:g} at {OSOAA_NM:g} nm, not OSOAA's
{OSOAA_PURE_WATER[0]:g}. Subtracting theirs and letting OSOAA add its own would run a
water whose a is short by {aw_wh - OSOAA_PURE_WATER[0]:.5f} per m:""")
    short = {}
    for water_type in SOURCES_TYPES:
        total = float(caught_by_type(caught, jerlov.water(water_type).a,
                                     OSOAA_NM))
        short[water_type] = (aw_wh - OSOAA_PURE_WATER[0]) / total
    print("  " + ", ".join(f"{t} {100 * s:.1f}%" for t, s in short.items()))
    command = (
        f"OSOAA_MAIN.exe -OSOAA.Wa {OSOAA_NM / 1000:.3f} -HYD.Model 3 "
        "-HYD.ExtData phase_HAOCE5.txt -HYD.UserProfile profile_III_440.txt "
        f"-SEA.Depth {OSOAA_DEPTHS_M[-1]:g} ...")
    print(f"""
OSOAA takes them with
  {command}
and the rest of a run's arguments: sun, atmosphere, surface and seabed, all
the caller's. The cross-section lines at the top of the phase function
file are not read with -HYD.Model 3.""")
    return dict(profile=profile, phase=phase, a=a, b=b, short=short)


def hydrolight_part(caught):
    rule(f"2. HydroLight: Jerlov {WATER_TYPE}, "
         f"{HYDROLIGHT_NM[0]:g}-{HYDROLIGHT_NM[-1]:g} nm")
    water = jerlov.water(WATER_TYPE)
    aw = jerlov.pure_water_absorption(HYDROLIGHT_NM)
    bw = jerlov.pure_water_scattering(HYDROLIGHT_NM,
                                      salinity_psu=SALINITY_PSU)
    text = caught_by_type(caught, jerlov.hydrolight_ac9_file, water,
                          HYDROLIGHT_NM, depths_m=HYDROLIGHT_DEPTHS_M,
                          pure_water=(aw, bw))
    print(f"""a and c less pure water, every 10 nm, in HydroLight's standard ac-9
format; the pure water is the aw Williamson & Hollins built their a on and
Morel's bw at salinity {SALINITY_PSU:g}, and the HydroLight run must add the same. The
file has not been run in HydroLight. Its first depth record:
""")
    lines = text.splitlines()
    print("  " + lines[10])
    print("  " + lines[11][:72] + " ...")
    # Pope & Fry (1997), a pure water absorption many runs use.
    pope = jerlov.pure_water_absorption_table(HYDROLIGHT_NM,
                                              source="pope1997")
    refused = {}
    for water_type in SOURCES_TYPES:
        total = np.asarray(caught_by_type(caught,
                                          jerlov.water(water_type).a,
                                          HYDROLIGHT_NM))
        refused[water_type] = HYDROLIGHT_NM[total - pope < 0]
        try:
            caught_by_type(caught, jerlov.hydrolight_ac9_file,
                           jerlov.water(water_type), HYDROLIGHT_NM,
                           depths_m=HYDROLIGHT_DEPTHS_M,
                           pure_water=(pope, bw))
        except ValueError:
            pass
        else:
            assert refused[water_type].size == 0
    first = {t: float(w[0]) for t, w in refused.items() if w.size}
    print("""
With Pope & Fry's (1997) aw instead, which is larger in the red, a less
pure water goes negative, and the file is refused, from""")
    print("  " + ", ".join(f"{t} {nm:g} nm" for t, nm in first.items()))
    largest = max(
        float(np.max(np.abs(pope - aw) / np.asarray(caught_by_type(
            caught, jerlov.water(t).a, HYDROLIGHT_NM))))
        for t in SOURCES_TYPES)
    print(f"""because Williamson & Hollins's a there is little more than their own aw.
From {HYDROLIGHT_NM[0]:g} to {HYDROLIGHT_NM[-1]:g} nm the two aw differ by up to {100 * largest:.0f} percent of
the water's a in these types.""")
    return dict(text=text, refused=refused, first=first, largest=largest)


def write_part(osoaa, hydrolight, out_dir):
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = {
        out / "profile_III_440.txt": osoaa["profile"],
        out / "phase_HAOCE5.txt": osoaa["phase"],
        out / "hydrolight_III_ac9.txt": hydrolight["text"],
    }
    for path, text in written.items():
        path.write_text(text)
    print(f"\nWritten {', '.join(str(p) for p in written)}.")
    return list(written)


def _result(results, name):
    """A result file, in OSOAA's own folders or all in one."""
    for sub in ("", "Advanced_outputs", "Standard_outputs"):
        path = pathlib.Path(results) / sub / name
        if path.exists():
            return path.read_text()
    raise FileNotFoundError(f"no {name} under {results}")


def _parameter(list_param, key):
    """One value of OSOAA's ListParam.txt, ' -KEY : value'."""
    for line in list_param.splitlines():
        fields = line.split(":", 1)
        if fields[0].strip() == key:
            return float(fields[1])
    raise KeyError(key)


def read_part(results, caught):
    rule("3. OSOAA's results, read back")
    params = _result(results, "ListParam.txt")
    wavelength = 1000 * _parameter(params, "-OSOAA.Wa")
    sun = _parameter(params, "-ANG.Thetas")
    depth = _parameter(params, "-SEA.Depth")
    flux = jerlov.read_osoaa_flux(_result(results, "Flux.txt"))
    profile = jerlov.read_osoaa_radiance_vs_depth(
        _result(results, "RESLUM_vsZ.txt"))
    kd_osoaa = flux.kd(0.0, depth)
    # Jerlov's own Kd for the type, in both editions, and the Kd that
    # another code, HydroLight, made of other IOPs for it: Solonenko &
    # Mobley's (2015) K_d^H, from their retrieved a and b with Petzold's
    # average particle phase function, a clear sky and deep water.
    compared = {}
    for source, label, method in (
            ("jerlov1968", "Jerlov (1968)", "kd"),
            ("jerlov1976", "Jerlov (1976)", "kd"),
            ("solonenko2015", "HydroLight, Solonenko 2015", "kd_hydrolight")):
        water = jerlov.water(WATER_TYPE, source=source)
        compared[label] = float(caught_by_type(
            caught, getattr(water, method), wavelength))
    sea = flux.in_sea
    reflectance = float(flux.up_over_down[sea][0])
    # Q = Eu / Lu just below the surface, from the nadir-viewing radiance
    # (both normalized alike, so the normalization cancels).
    if profile.direction != "upward" or profile.viewing_zenith_deg != 0:
        raise ValueError("Q needs the upward radiance at a viewing zenith "
                         "angle of 0")
    q = float(flux.total_up[sea][0] / profile.radiance[0])
    print(f"""The run: {wavelength:g} nm, the sun {sun:g} degrees from the zenith, {depth:g} m of
water. Williamson & Hollins's IOPs for Jerlov {WATER_TYPE}, through OSOAA, give a mean
Kd of Ed from 0 to {depth:g} m of {kd_osoaa:.4f} per m. Beside it:""")
    for label, kd in compared.items():
        print(f"  {label:<27} {kd:.4f}  (OSOAA {100 * (kd_osoaa / kd - 1):+.1f}%)")
    print(f"""Just below the surface Eu/Ed = {reflectance:.5f} and Q = Eu/Lu = {q:.3f} sr. The
Kd of a single run depends on its sun, sky and surface, which a Jerlov
type does not fix: these are this run's. OSOAA's 'direct' flux is not the
unscattered beam (it counts the truncated forward peak as transmitted), so
only the totals are used.""")
    return dict(wavelength=wavelength, sun=sun, depth=depth, kd=kd_osoaa,
                compared=compared, reflectance=reflectance, q=q)


def main(out_dir=None, results=None):
    """Print the files; write them to ``out_dir`` if given; read an OSOAA
    run's results from ``results`` if given."""
    _banner()
    caught = set()
    osoaa = osoaa_part(caught)
    hydrolight = hydrolight_part(caught)
    written = write_part(osoaa, hydrolight, out_dir) if out_dir else None
    if out_dir is None:
        print("\nRun with --write DIR to write the three files.")
    read = read_part(results, caught) if results else None
    if results is None:
        print("Run with --read DIR, the folder of an OSOAA run made with them, "
              "to read its results.")
    if caught:
        rule("Warnings")
        print("Raised along the way, and caught by type:")
        for message in sorted(caught):
            print(f"  - {message}")

    rule("Before you use any of this")
    print(f"""  - A Jerlov type is the same at every depth, so every depth in the files
    carries the same values.
  - The pure water subtracted must be the one the code adds back: OSOAA's
    from its own file, HydroLight's as its run is set. jerlov has no
    default for it.
  - Petzold measured no polarization: the ratios in the phase function
    file ({', '.join(f'{k} = {v:g}' for k, v in RATIOS.items())}) are this
    example's assumption.
  - The OSOAA files were run once by hand with OSOAA outside CI (DATA.md
    section 38); the HydroLight file follows its documentation and has not
    been run.
  - OSOAA's results are normalized to the sun above the atmosphere; the
    ratios above (Kd, Eu/Ed, Q) do not depend on it.
""")
    return dict(osoaa=osoaa, hydrolight=hydrolight, written=written,
                read=read, caught=caught)


if __name__ == "__main__":
    # Only an explicit --write DIR writes files, and only --read DIR reads:
    # run through runpy from "python -c", as CI runs the examples, sys.argv
    # carries this script's own path, which must not be taken for a
    # directory.
    args = sys.argv[1:]

    def option(name):
        return args[args.index(name) + 1] if name in args[:-1] else None

    main(option("--write"), option("--read"))

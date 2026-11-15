"""Reference images: ten measured materials seen through three water types.

For people who need something to check a rendering or a photograph of
underwater colour against:

    python examples/reference_images.py                 # print the colours
    python examples/reference_images.py --write out/    # also CSV and images

Ten materials whose reflectance the USGS Spectral Library measured, from
white PVC to cobalt violet, are set out as a chart and seen along a
horizontal line through Jerlov IB, III and 1C, at 5 and 15 m depth and from
1 to 10 m away. The colours come from the spectra, through `Scene`, with
every choice that fills them stated below; nothing is invented about the
materials (DECISIONS.md section 85).
"""

import csv
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


TYPES = ("IB", "III", "1C")
DEPTHS_M = (5.0, 15.0)
DISTANCES_M = (1.0, 3.0, 5.0, 10.0)
#: Colours are formed where D65, the materials, Williamson & Hollins's a
#: and b and Jerlov's (1976) Kd all exist, and the observer is.
WL = np.arange(360.0, 716.0)
SURFACE = np.interp(WL, *jerlov.d65())
#: The light comes down by Jerlov's own Kd for the type, constant with
#: depth; the water along the line is Williamson & Hollins's.
KD_SOURCE = "jerlov1976"
#: A face turned towards a horizontal line of sight receives part of the
#: downwelling irradiance; how much the water type does not fix. 0.3 is
#: this example's assumption, as in fish_colour_differences.py.
FACE_IRRADIANCE_RATIO = 0.3


def caught_by_type(caught, function, *args, **kwargs):
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always", jerlov.ProvenanceWarning)
        warnings.simplefilter("always", jerlov.CoverageWarning)
        warnings.simplefilter("always", jerlov.GamutWarning)
        result = function(*args, **kwargs)
    caught.update(f"{w.category.__name__}: {str(w.message).split(':')[0]}"
                  for w in seen)
    return result


def materials():
    """Each material's reflectance on WL, interpolated linearly from the
    library's 1 nm channels: the grids coincide, so nothing moves."""
    out = {}
    for key in jerlov.USGS2017_MATERIALS:
        m = jerlov.usgs2017_reflectance(key)
        out[key] = np.interp(WL, m.wavelengths, m.reflectance)
    return out


def nearest_station(water, caught):
    """The Petzold station whose b at 530 nm is nearest the water's, for
    a measured bb/b in the path radiance."""
    b = float(caught_by_type(caught, water.b, 530.0))
    return min(jerlov.PETZOLD_STATIONS,
               key=lambda s: abs(jerlov.petzold_scattering(s).b - b))


def chart(caught):
    """sRGB of every material, type, depth and distance, balanced on the
    downwelling irradiance at the depth (a camera white-balanced there)."""
    reflectance = materials()
    out = {}
    stations = {}
    for water_type in TYPES:
        water = jerlov.water(water_type)
        kd = caught_by_type(caught, jerlov.water(water_type,
                                                 source=KD_SOURCE).kd, WL)
        station = nearest_station(water, caught)
        stations[water_type] = station
        ratio = jerlov.petzold_scattering(station).backscatter_ratio
        for depth in DEPTHS_M:
            scene = caught_by_type(caught, jerlov.Scene.at_depth, water,
                                   depth, SURFACE, WL, kd=kd)
            ed = scene.downwelling
            b_inf = caught_by_type(caught, jerlov.veiling_radiance_estimate,
                                   water, ed, WL, backscatter_ratio=ratio)
            # What a white diffuser lit like the targets would send: the
            # camera's white.
            white = FACE_IRRADIANCE_RATIO * ed / np.pi
            for key, rho in reflectance.items():
                for distance in (0.0,) + DISTANCES_M:
                    seen = caught_by_type(
                        caught, scene.observe, rho, distance,
                        veiling_radiance=b_inf,
                        face_irradiance_ratio=FACE_IRRADIANCE_RATIO)
                    linear = caught_by_type(
                        caught, jerlov.spectrum_to_srgb, seen.radiance, WL,
                        white=white, clip=False)
                    out[(water_type, depth, key, distance)] = linear
    return out, stations


def table_part(colours):
    rule("1. The chart, as 8-bit sRGB")
    print(f"""Each material's colour, balanced on the light at that depth, as a camera
white-balanced there would record it: first at the surface of the
material (0 m), then at {', '.join(f'{d:g}' for d in DISTANCES_M)} m. Out-of-gamut values are clipped
for printing only.""")
    for water_type in TYPES:
        for depth in DEPTHS_M:
            print(f"\n  Jerlov {water_type}, {depth:g} m deep")
            for key in jerlov.USGS2017_MATERIALS:
                cells = []
                for distance in (0.0,) + DISTANCES_M:
                    rgb = np.clip(colours[(water_type, depth, key,
                                           distance)], 0, 1)
                    cells.append("#" + "".join(f"{int(round(255 * v)):02x}"
                                               for v in rgb))
                print(f"    {key:<16}" + " ".join(cells))


def summary_part(colours):
    rule("2. What moves the colours")
    # Chroma in sRGB: how far a colour is from grey, max - min channel.

    def chroma(rgb):
        rgb = np.clip(rgb, 0, 1)
        return float(np.max(rgb) - np.min(rgb))

    coloured = [k for k in jerlov.USGS2017_MATERIALS
                if k not in ("white_pvc", "black_abs", "grey_concrete")]
    kept = {}
    for water_type in TYPES:
        for depth in DEPTHS_M:
            ratios = [chroma(colours[(water_type, depth, k, 10.0)])
                      / chroma(colours[(water_type, depth, k, 0.0)])
                      for k in coloured]
            kept[(water_type, depth)] = float(np.median(ratios))
    print("""The median share of each coloured material's chroma (the spread between
its largest and smallest sRGB channel) left at 10 m, of its chroma at the
surface of the material:
""")
    print(f"  {'':8}" + "".join(f"{f'{d:g} m deep':>14}" for d in DEPTHS_M))
    for water_type in TYPES:
        print(f"  {water_type:<8}" + "".join(
            f"{kept[(water_type, d)]:>14.2f}" for d in DEPTHS_M))
    least = {d: min(TYPES, key=lambda t: kept[(t, d)]) for d in DEPTHS_M}
    deeper_less = all(kept[(t, DEPTHS_M[1])] < kept[(t, DEPTHS_M[0])]
                      for t in TYPES)
    same = len(set(least.values())) == 1
    print(f"""
The path radiance replaces the material's colour with the water's as the
distance grows. At 10 m Jerlov {least[DEPTHS_M[0]]} keeps the least of it at {DEPTHS_M[0]:g} m{'' if same else f', {least[DEPTHS_M[1]]} at {DEPTHS_M[1]:g} m'}{' and at ' + f'{DEPTHS_M[1]:g} m' if same else ''},
and {'every type keeps less' if deeper_less else 'not every type keeps less'} at {DEPTHS_M[1]:g} m than at {DEPTHS_M[0]:g} m, with the camera balanced on
the light at each depth.""")
    return kept, least, deeper_less


def write_part(colours, out_dir):
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    table = out / "reference_images.csv"
    with open(table, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["water_type", "depth_m", "material", "distance_m",
                         "linear_r", "linear_g", "linear_b",
                         "srgb8_r", "srgb8_g", "srgb8_b"])
        for (water_type, depth, key, distance), rgb in colours.items():
            # spectrum_to_srgb returns encoded sRGB; the linear values
            # follow from the sRGB transfer function.
            encoded = np.clip(rgb, 0, 1)
            linear = np.where(encoded <= 0.04045, encoded / 12.92,
                              ((encoded + 0.055) / 1.055) ** 2.4)
            writer.writerow([water_type, f"{depth:g}", key, f"{distance:g}"]
                            + [f"{v:.6f}" for v in linear]
                            + [int(round(255 * v)) for v in encoded])
    images = []
    size = 20
    for water_type in TYPES:
        rows = bytearray()
        for depth in DEPTHS_M:
            for key in jerlov.USGS2017_MATERIALS:
                line = bytearray()
                for distance in (0.0,) + DISTANCES_M:
                    rgb = np.clip(colours[(water_type, depth, key, distance)],
                                  0, 1)
                    line += bytes(int(round(255 * v)) for v in rgb) * size
                rows += bytes(line) * size
        width = (1 + len(DISTANCES_M)) * size
        height = len(DEPTHS_M) * len(jerlov.USGS2017_MATERIALS) * size
        path = out / f"reference_jerlov_{water_type}.ppm"
        path.write_bytes(f"P6 {width} {height} 255\n".encode() + bytes(rows))
        images.append(path)
    print(f"\nWritten {table} and {', '.join(p.name for p in images)}: "
          "materials down, the surface of the material then "
          f"{', '.join(f'{d:g}' for d in DISTANCES_M)} m across, "
          f"{' m above '.join(f'{d:g}' for d in DEPTHS_M)} m deep.")
    return table, images


def main(out_dir=None):
    """Print the chart; write CSV and images to ``out_dir`` if given."""
    _banner()
    caught = set()
    colours, stations = chart(caught)
    table_part(colours)
    kept, least, deeper_less = summary_part(colours)
    written = write_part(colours, out_dir) if out_dir else None
    if out_dir is None:
        print("\nRun with --write DIR to write the chart as CSV and images.")
    if caught:
        rule("Warnings")
        print("Raised along the way, and caught by type:")
        for message in sorted(caught):
            print(f"  - {message}")

    rule("Before you use any of this")
    print(f"""  - The materials are particular dry samples measured in a laboratory
    (USGS Spectral Library 7, DATA.md section 37). Wet, or another sample
    of the same material, they would reflect differently.
  - D65 above the surface, Jerlov's (1976) Kd for the light coming down,
    constant with depth, Williamson & Hollins's a and b along the line.
    Values outside 412-715 nm, and Jerlov's from 701 nm, are extrapolated
    by their sources: the warnings above.
  - The face of each material receives {FACE_IRRADIANCE_RATIO:g} of the downwelling
    irradiance, this example's assumption.
  - The path radiance is the package's single-scattering estimate, an
    order of magnitude, with the bb/b of the Petzold station nearest
    each type's b ({', '.join(f'{t}: {s}' for t, s in stations.items())}).
  - A horizontal line in uniform water, no blur, a camera balanced on the
    light at depth. These are not photographs and have not been compared
    with any.
""")
    return dict(colours=colours, stations=stations, kept=kept,
                least=least, deeper_less=deeper_less,
                written=written, caught=caught)


if __name__ == "__main__":
    # Only an explicit --write DIR writes files: run through runpy from
    # "python -c", as CI runs the examples, sys.argv carries this script's
    # own path, which must not be taken for a directory.
    args = sys.argv[1:]
    main(args[args.index("--write") + 1]
         if "--write" in args[:-1] else None)

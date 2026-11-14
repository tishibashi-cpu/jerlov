"""Lookup tables of underwater light for games and real-time rendering.

For people who draw water every frame, in a game engine or a simulator,
from a precomputed table rather than by tracing light:

    python examples/water_lookup_tables.py                 # print a summary
    python examples/water_lookup_tables.py --write out/    # also the tables

For one Jerlov type it tabulates, by depth and by distance along a
horizontal line of sight, what a shader needs to fog an object: the share
of the object's light that survives in each RGB channel, and the light the
water itself adds along the line, the path radiance. Every input that fills
the tables is chosen at the top of this file and stated; the package
supplies none of them by default (DECISIONS.md section 83).
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


#: The water along the line of sight: Williamson & Hollins's a and b.
WATER_TYPE = "III"
#: How the light gets down: Jerlov's (1976) Kd for the same type, constant
#: with depth. Williamson & Hollins give no Kd.
KD_SOURCE = "jerlov1976"
#: The colours are formed where D65, Jerlov's Kd (to 715 nm) and the
#: observer all exist.
WL = np.arange(360.0, 716.0)
#: The light at the surface: D65, in relative units. Every radiance below is
#: relative to a white Lambertian surface lit by it at the sea surface.
SURFACE = np.interp(WL, *jerlov.d65())
#: For the path radiance, a measured bb/b: Petzold's HAOCE 5, the station
#: whose b at 530 nm is nearest Jerlov III's (rendering_export.py).
STATION = "HAOCE 5"
#: The table's colour space and grid.
COLOUR_SPACE = "acescg"
DEPTHS_M = np.arange(0.0, 51.0, 5.0)
DISTANCES_M = np.arange(0.0, 31.0, 1.0)


def _beyond():
    """The share of the CIE x-bar beyond the last wavelength used."""
    wl, cmf = jerlov.cie_1931_cmf()
    beyond = wl >= WL[-1]
    total = np.sum((cmf[1:, 0] + cmf[:-1, 0]) / 2 * np.diff(wl))
    part = np.sum((cmf[beyond][1:, 0] + cmf[beyond][:-1, 0]) / 2
                  * np.diff(wl[beyond]))
    return float(part / total)


BEYOND = _beyond()


def xy_to_xyz(x, y):
    return np.array([x / y, 1.0, (1 - x - y) / y])


def xyz_to_rgb_matrix(colour_space):
    """From the primaries and white `RgbAttenuation.as_dict()` records."""
    primaries = np.array(colour_space["primaries_xy"])
    white = xy_to_xyz(*colour_space["white_xy"])
    m = np.column_stack([xy_to_xyz(x, y) for x, y in primaries])
    return np.linalg.inv(m * np.linalg.solve(m, white))


def caught_by_type(caught, function, *args, **kwargs):
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always", jerlov.ProvenanceWarning)
        warnings.simplefilter("always", jerlov.CoverageWarning)
        result = function(*args, **kwargs)
    caught.update(f"{w.category.__name__}: {str(w.message).split(':')[0]}"
                  for w in seen)
    return result


def tables(caught):
    """Transmittance and path radiance, (depth, distance, channel)."""
    water = jerlov.water(WATER_TYPE)
    kd = caught_by_type(caught, jerlov.water(WATER_TYPE,
                                              source=KD_SOURCE).kd, WL)
    ratio = jerlov.petzold_scattering(STATION).backscatter_ratio
    c = caught_by_type(caught, water.c, WL)
    white = caught_by_type(caught, jerlov.spectrum_to_xyz, SURFACE / np.pi,
                           WL)[1]
    transmittance = np.empty((DEPTHS_M.size, DISTANCES_M.size, 3))
    path = np.empty_like(transmittance)
    sigma = {}
    m = None
    for i, depth in enumerate(DEPTHS_M):
        scene = caught_by_type(caught, jerlov.Scene.at_depth, water,
                               float(depth), SURFACE, WL, kd=kd)
        ed = scene.downwelling
        # The light at this depth is what lights the object, so it is the
        # illuminant whose colour the water changes along the line.
        fit = caught_by_type(caught, jerlov.rgb_attenuation, water,
                             colour_space=COLOUR_SPACE, illuminant=(WL, ed),
                             distance_range_m=(DISTANCES_M[1],
                                               DISTANCES_M[-1]))
        sigma[float(depth)] = fit
        if m is None:
            m = xyz_to_rgb_matrix(fit.as_dict()["colour_space"])
        b_inf = caught_by_type(caught, jerlov.veiling_radiance_estimate,
                               water, ed, WL, backscatter_ratio=ratio)
        # The transmittance is the package's, from the spectrum, nothing
        # fitted (DECISIONS.md section 84); the path radiance is this
        # example's own, from the package's single-scattering estimate.
        transmittance[i] = caught_by_type(
            caught, jerlov.rgb_transmittance, water, DISTANCES_M,
            colour_space=COLOUR_SPACE, illuminant=(WL, ed)).transmittance
        for j, r in enumerate(DISTANCES_M):
            through = np.exp(-c * r)
            path[i, j] = (m @ caught_by_type(
                caught, jerlov.spectrum_to_xyz, b_inf * (1 - through),
                WL)) / white
    return transmittance, path, sigma, m


def summary_part(transmittance, path, sigma):
    rule(f"1. Jerlov {WATER_TYPE} by depth and distance, in {COLOUR_SPACE}")
    print(f"""The share of an object's light that survives the line of sight, per
channel, and the light the water adds along it, relative to a white
surface at the sea surface under the same sky. Light from D65 at the
surface, carried down by Jerlov's Kd; the path radiance by the package's
single-scattering estimate with {STATION}'s measured bb/b.
""")
    shown = (5.0, 10.0, 20.0, 30.0)
    print(f"  {'depth':>6}  {'distance':>8}  {'transmittance R G B':>24}"
          f"  {'path radiance R G B':>27}")
    for i, depth in enumerate(DEPTHS_M):
        if depth not in (0.0, 10.0, 25.0, 50.0):
            continue
        for r in shown:
            j = int(np.flatnonzero(DISTANCES_M == r)[0])
            t, p = transmittance[i, j], path[i, j]
            print(f"  {depth:>5g}m  {r:>7g}m  "
                  f"{' '.join(f'{v:7.4f}' for v in t)}  "
                  f"{' '.join(f'{v:8.5f}' for v in p)}")
    deep, shallow = sigma[float(DEPTHS_M[-1])], sigma[0.0]
    print(f"""
One coefficient per channel fitted over {DISTANCES_M[1]:g}-{DISTANCES_M[-1]:g} m, if a shader would
rather have those: sigma_t {', '.join(f'{v:.3f}' for v in shallow.sigma_t)} 1/m at the surface and
{', '.join(f'{v:.3f}' for v in deep.sigma_t)} at {DEPTHS_M[-1]:g} m, with errors up to {100 * float(np.max(shallow.max_relative_error_t)):.0f} and
{100 * float(np.max(deep.max_relative_error_t)):.0f} percent. They differ because the light at depth is bluer, and
which part of each channel is left to attenuate changes with it.""")
    return shallow, deep


def write_part(transmittance, path, m, out_dir, caught):
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    table = out / f"jerlov_{WATER_TYPE}_{COLOUR_SPACE}.csv"
    with open(table, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["depth_m", "distance_m", "transmittance_r",
                         "transmittance_g", "transmittance_b", "path_r",
                         "path_g", "path_b"])
        for i, depth in enumerate(DEPTHS_M):
            for j, r in enumerate(DISTANCES_M):
                writer.writerow([f"{depth:g}", f"{r:g}"]
                                + [f"{v:.6g}" for v in transmittance[i, j]]
                                + [f"{v:.6g}" for v in path[i, j]])
    # Previews only: 8-bit sRGB, depth down, distance across. A shader
    # would read the CSV's linear values, not these.
    to_xyz = np.linalg.inv(m)
    srgb_white = xy_to_xyz(0.3127, 0.3290)
    images = []
    for name, values, scale in (("transmittance", transmittance, 1.0),
                                ("path", path, 1.0 / float(np.max(path)))):
        size = 12
        rows = bytearray()
        with warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter("always", jerlov.GamutWarning)
            for i in range(values.shape[0]):
                line = bytearray()
                for j in range(values.shape[1]):
                    xyz = to_xyz @ (values[i, j] * scale)
                    rgb = jerlov.xyz_to_srgb(xyz / to_xyz.sum(axis=1)
                                             * srgb_white)
                    line += bytes(int(round(255 * v)) for v in rgb) * size
                rows += bytes(line) * size
        caught.update(f"{w.category.__name__}: {w.message}" for w in seen)
        path_out = out / f"jerlov_{WATER_TYPE}_{name}.ppm"
        width, height = values.shape[1] * size, values.shape[0] * size
        path_out.write_bytes(f"P6 {width} {height} 255\n".encode()
                             + bytes(rows))
        images.append(path_out)
    print(f"\nWritten {table} and the previews "
          f"{', '.join(p.name for p in images)}.")
    return table, images


def main(out_dir=None):
    """Print a summary; write the tables to ``out_dir`` if given."""
    _banner()
    caught = set()
    transmittance, path, sigma, m = tables(caught)
    shallow, deep = summary_part(transmittance, path, sigma)
    written = (write_part(transmittance, path, m, out_dir, caught)
               if out_dir else None)
    if out_dir is None:
        print("\nRun with --write DIR to write the tables as CSV and "
              "preview images.")
    if caught:
        rule("Warnings")
        print("Raised along the way, and caught by type:")
        for message in sorted(caught):
            print(f"  - {message}")

    rule("Before you use any of this")
    print(f"""  - Two sources in one table: Williamson & Hollins's a and b along the
    line, Jerlov's (1976) Kd for the light coming down, Kd constant with
    depth. Williamson & Hollins's values outside 412-715 nm are their
    model's extrapolation, and Jerlov's Kd from 701 nm the dataset's it
    came through (DATA.md section 16): the warnings above.
  - D65 above the surface, and the colours formed over {WL[0]:g}-{WL[-1]:g} nm, where
    Jerlov's Kd stops: beyond it lies {100 * BEYOND:.2f} percent of the observer's x-bar,
    left out.
  - The path radiance is a single-scattering estimate with the
    backscattered light spread evenly; the package calls it an order of
    magnitude. It needs a bb/b, here {STATION}'s, which the Jerlov type
    does not fix.
  - Horizontal lines only: the sun's direction, a line looking up or down
    (Scene.observe_slant), and blur are not in the tables.
""")
    return dict(transmittance=transmittance, path=path, sigma=sigma,
                matrix=m, shallow=shallow, deep=deep, written=written,
                caught=caught)


if __name__ == "__main__":
    # Only an explicit --write DIR writes files: run through runpy from
    # "python -c", as CI runs the examples, sys.argv carries this script's
    # own path, which must not be taken for a directory.
    args = sys.argv[1:]
    main(args[args.index("--write") + 1]
         if "--write" in args[:-1] else None)

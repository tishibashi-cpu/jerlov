"""What rendering water in RGB does to colours, as a colour difference.

For people who make images of water, in film, games or visualisation, and
render it in RGB:

    python examples/rgb_versus_spectral.py                 # print the tables
    python examples/rgb_versus_spectral.py --write out/    # also an image

A renderer in RGB attenuates each channel with one coefficient. Here five
surfaces are seen through water twice: spectrally, as the light is, and as
an RGB renderer would draw them with the coefficients `rgb_attenuation`
fits. The difference is given as a CIE 1976 colour difference, Delta E*ab,
for three water types, three colour spaces and distances inside and beyond
the range the coefficients were fitted over (DECISIONS.md section 83).
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


#: Williamson & Hollins (2022), the default source, from clear to coastal.
TYPES = ("IB", "III", "1C")
#: D65 spans 300-780 nm, Williamson & Hollins 300-800: the colours are
#: formed over 360-780 nm, where both exist and the observer is.
WL = np.arange(360.0, 781.0)
ILLUMINANT = (WL, np.interp(WL, *jerlov.d65()))
#: The distances the RGB coefficients are fitted over, and those shown.
FIT_RANGE_M = (0.5, 10.0)
DISTANCES_M = (1.0, 2.0, 5.0, 10.0, 15.0, 20.0)


#: The sRGB white, D65 at x = 0.3127, y = 0.3290, with Y = 1.
SRGB_WHITE = np.array([0.3127 / 0.3290, 1.0, (1 - 0.3127 - 0.3290) / 0.3290])


def band(centre_nm, width_nm):
    return 0.05 + 0.75 * np.exp(-0.5 * ((WL - centre_nm) / width_nm) ** 2)


#: Invented reflectances, not measurements: two neutral greys and three
#: broad bands, enough to see how each part of the spectrum fares.
PATCHES = {
    "white": np.full(WL.shape, 0.9),
    "grey": np.full(WL.shape, 0.18),
    "red": band(630.0, 40.0),
    "green": band(530.0, 35.0),
    "blue": band(460.0, 30.0),
}


def xy_to_xyz(x, y):
    return np.array([x / y, 1.0, (1 - x - y) / y])


def xyz_to_rgb_matrix(colour_space):
    """The space's matrix from XYZ, from the primaries and white that
    `RgbAttenuation.as_dict()` records, derived as for any RGB space."""
    primaries = np.array(colour_space["primaries_xy"])
    white = xy_to_xyz(*colour_space["white_xy"])
    m = np.column_stack([xy_to_xyz(x, y) for x, y in primaries])
    return np.linalg.inv(m * np.linalg.solve(m, white))


def lab(xyz, white):
    """CIE 1976 L*a*b* of ``xyz`` against the reference ``white``."""
    t = np.asarray(xyz) / np.asarray(white)
    d = 6 / 29
    f = np.where(t > d ** 3, np.cbrt(t), t / (3 * d * d) + 4 / 29)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]),
                     200 * (f[1] - f[2])])


def to_xyz(spectrum):
    return jerlov.spectrum_to_xyz(spectrum, WL)


def renderings(water, fit, distances):
    """XYZ of each patch at each distance: spectrally, and as RGB."""
    m = xyz_to_rgb_matrix(fit.as_dict()["colour_space"])
    back = np.linalg.inv(m)
    c = water.c(WL)
    light = ILLUMINANT[1]
    out = {}
    for name, reflectance in PATCHES.items():
        rgb0 = m @ to_xyz(light * reflectance)
        for r in distances:
            spectral = to_xyz(light * reflectance * np.exp(-c * r))
            in_rgb = back @ (rgb0 * np.exp(-fit.sigma_t * r))
            out[(name, r)] = (spectral, in_rgb)
    return out


def differences(water, fit, distances):
    """Delta E*ab by patch and distance, against two references: the
    illuminant itself, and the white patch at that distance, rendered
    spectrally, as a camera exposed and balanced on the scene would."""
    seen = renderings(water, fit, distances)
    illuminant_white = to_xyz(ILLUMINANT[1])
    result = {}
    for (name, r), (spectral, in_rgb) in seen.items():
        scene_white = seen[("white", r)][0] / PATCHES["white"][0]
        result[(name, r)] = (
            float(np.linalg.norm(lab(in_rgb, illuminant_white)
                                 - lab(spectral, illuminant_white))),
            float(np.linalg.norm(lab(in_rgb, scene_white)
                                 - lab(spectral, scene_white))))
    return result, seen


def record(caught, seen):
    caught.update(f"{w.category.__name__}: {str(w.message).split(':')[0]}"
                  for w in seen)


def table_part(caught):
    rule("1. The largest colour difference, RGB against spectral")
    print(f"""Five invented surfaces under D65, seen through water. The RGB coefficients
are fitted over {FIT_RANGE_M[0]:g}-{FIT_RANGE_M[1]:g} m; distances past {FIT_RANGE_M[1]:g} m are outside that fit. Each
cell is the largest Delta E*ab over the five surfaces, first with the
illuminant as white, then with the white surface at that distance as
white (a camera exposed and balanced on the scene).""")
    header = "".join(f"{f'{r:g} m':>12}" for r in DISTANCES_M)
    results = {}
    for water_type in TYPES:
        water = jerlov.water(water_type)
        print(f"\n  Jerlov {water_type}")
        print(f"  {'space':<13}{header}")
        for space in jerlov.RGB_COLOUR_SPACES:
            with warnings.catch_warnings(record=True) as seen:
                warnings.simplefilter("always", jerlov.ProvenanceWarning)
                warnings.simplefilter("always", jerlov.CoverageWarning)
                try:
                    fit = jerlov.rgb_attenuation(
                        water, colour_space=space, illuminant=ILLUMINANT,
                        distance_range_m=FIT_RANGE_M)
                except ValueError as error:
                    record(caught, seen)
                    reach = str(error).split("up to about ")[1].split(" ")[0]
                    print(f"  {space:<13}refused: a channel turns negative "
                          f"past {reach} m")
                    results[(water_type, space)] = None
                    continue
                diff, rendered = differences(water, fit, DISTANCES_M)
            record(caught, seen)
            results[(water_type, space)] = (diff, rendered, fit)
            cells = []
            for r in DISTANCES_M:
                worst = max(diff[(n, r)][0] for n in PATCHES)
                balanced = max(diff[(n, r)][1] for n in PATCHES)
                cells.append(f"{worst:5.1f} {balanced:5.1f}")
            print(f"  {space:<13}" + "".join(f"{c:>12}" for c in cells))
    return results


def summary_part(results):
    rule("2. What the tables say")
    fitted = [r for r in DISTANCES_M if r <= FIT_RANGE_M[1]]
    beyond = [r for r in DISTANCES_M if r > FIT_RANGE_M[1]]

    def largest(space, distances, which):
        values = [diff[(n, r)][which]
                  for (t, s), v in results.items() if s == space and v
                  for diff in (v[0],) for n in PATCHES for r in distances]
        return max(values)

    worst = {space: (largest(space, fitted, 0), largest(space, fitted, 1),
                     largest(space, beyond, 1))
             for space in jerlov.RGB_COLOUR_SPACES}
    patch_worst = {}
    for (t, s), v in results.items():
        if not v:
            continue
        for (n, r), (_, balanced) in v[0].items():
            patch_worst[n] = max(patch_worst.get(n, 0.0), balanced)
    by_patch = sorted(patch_worst.items(), key=lambda kv: -kv[1])
    print(f"""Within the fitted range, the largest difference with the illuminant as
white is {worst['linear_srgb'][0]:.1f} in linear sRGB, {worst['acescg'][0]:.1f} in ACEScg and {worst['rec2020'][0]:.1f} in Rec. 2020; with
the scene's own white, {worst['linear_srgb'][1]:.1f}, {worst['acescg'][1]:.1f} and {worst['rec2020'][1]:.1f}. Beyond it, with the scene's
white, up to {worst['linear_srgb'][2]:.1f}, {worst['acescg'][2]:.1f} and {worst['rec2020'][2]:.1f}. Linear sRGB's figures leave out IB,
which it refuses. With the illuminant as white the far surfaces are
dark, and dark colours differ little in L*a*b*; a camera that brings
them back up brings the difference back with them.
The surface that suffers most is {by_patch[0][0]} (up to {by_patch[0][1]:.1f}), the least {by_patch[-1][0]}
(up to {by_patch[-1][1]:.1f}).""")
    return worst, by_patch


def image_part(results, out_dir, caught):
    """Spectral above, RGB below, for one water and space, as sRGB."""
    water_type, space = "III", "acescg"
    _, rendered, _ = results[(water_type, space)]
    rows = []
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always", jerlov.GamutWarning)
        for which in (0, 1):
            for name in PATCHES:
                row = []
                for r in DISTANCES_M:
                    # Balanced on the white surface at this distance, as
                    # spectrum_to_srgb balances on the white it is given:
                    # that white lands on sRGB's own white, D65 at Y = 1.
                    white = rendered[("white", r)][0] / PATCHES["white"][0]
                    row.append(jerlov.xyz_to_srgb(
                        rendered[(name, r)][which] / white * SRGB_WHITE))
                rows.append(row)
    record(caught, seen)
    size = 24
    height, width = len(rows) * size, len(DISTANCES_M) * size
    pixels = bytearray()
    for row in rows:
        line = bytearray()
        for colour in row:
            line += bytes(int(round(255 * v)) for v in colour) * size
        pixels += bytes(line) * size
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "rgb_versus_spectral.ppm"
    path.write_bytes(f"P6 {width} {height} 255\n".encode() + bytes(pixels))
    print(f"\nWritten {path}: Jerlov {water_type} in {space}, the five surfaces "
          "spectrally (top) and in RGB (bottom), "
          f"{', '.join(f'{r:g}' for r in DISTANCES_M)} m left to right, each "
          "balanced on the white surface at its distance.")
    return path


def main(out_dir=None):
    """Print the tables; write the image to ``out_dir`` if given."""
    _banner()
    caught = set()
    results = table_part(caught)
    worst, by_patch = summary_part(results)
    image = image_part(results, out_dir, caught) if out_dir else None
    if out_dir is None:
        print("\nRun with --write DIR to write the two renderings as an image.")
    if caught:
        rule("Warnings")
        print("Raised along the way, and caught by type:")
        for message in sorted(caught):
            print(f"  - {message}")

    rule("Before you use any of this")
    print(f"""  - The surfaces are invented smooth reflectances, not a measured chart.
    Narrower or more structured spectra would fare differently.
  - D65 is the light; the colours are formed over {WL[0]:g}-{WL[-1]:g} nm, where D65,
    the water and the observer all exist. Williamson & Hollins's a and b
    outside 412-715 nm are their model's extrapolation (the warnings).
  - Only the light from the surface is drawn, attenuated by c. The path
    radiance between, which a renderer adds by scattering, is left out
    of both renderings alike.
  - Delta E*ab is CIE 1976, chosen because anyone can check it in a few
    lines. Nothing here says which difference a viewer would notice.
""")
    return dict(results=results, worst=worst, by_patch=by_patch,
                image=image, caught=caught)


if __name__ == "__main__":
    # Only an explicit --write DIR writes a file: run through runpy from
    # "python -c", as CI runs the examples, sys.argv carries this script's
    # own path, which must not be taken for a directory.
    args = sys.argv[1:]
    main(args[args.index("--write") + 1]
         if "--write" in args[:-1] else None)

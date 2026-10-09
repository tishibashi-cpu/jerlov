"""How a coloured fishing lure looks across a horizontal stretch of water.

For anyone designing, testing or photographing fishing lures and other
painted gear: what is left of a colour after a few metres of water, and how
far it stands out from the water behind it, in numbers as well as colour.
The physics is the same as `synthetic_underwater_images.py`; this keeps to
the ranges a lure is seen at and puts the contrast first.

    python examples/lure_colours.py
    python examples/lure_colours.py --png lure_colours.png   # also an image

The image is written only when asked for, with nothing beyond the standard
library and NumPy.

Nothing here says which colour a fish notices or takes. The contrast is
computed with the CIE luminance of the human eye, and fish eyes differ.
"""

import struct
import sys
import warnings
import zlib

import numpy as np

import jerlov

# Williamson & Hollins (2022) rest on measurements from 412 to 715 nm.
WAVELENGTHS = np.arange(412.0, 701.0, 2.0)
TYPES = ("IB", "II", "III", "1C", "3C", "5C")
DEPTH_M = 3.0
RANGES_M = (0.5, 1.0, 2.0, 3.0, 5.0)
BACKSCATTER_RATIOS = (0.01, 0.02)    # bb/b, stated: see part 4


def sigmoid(wl, edge, width):
    return 1.0 / (1.0 + np.exp(-(wl - edge) / width))


#: Smooth stand-ins for painted finishes, diffuse reflectance 0 to 1. Real
#: paints should be measured with a spectrophotometer; these only have the
#: right general shape. Fluorescence, which many bright lure paints have,
#: is not modelled.
FINISHES = {
    "white":      lambda wl: np.full_like(wl, 0.80),
    "chartreuse": lambda wl: 0.06 + 0.78 * sigmoid(wl, 500, 12)
                             * (1 - 0.35 * sigmoid(wl, 625, 18)),
    "orange":     lambda wl: 0.05 + 0.75 * sigmoid(wl, 580, 14),
    "red":        lambda wl: 0.04 + 0.70 * sigmoid(wl, 610, 12),
    "blue":       lambda wl: 0.05 + 0.45 * np.exp(-0.5 * ((wl - 460) / 35) ** 2),
    "black":      lambda wl: np.full_like(wl, 0.04),
}


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


def swatch(rgb):
    """A terminal colour block."""
    r, g, b = (int(round(255 * float(np.clip(c, 0, 1)))) for c in rgb)
    return f"\x1b[48;2;{r};{g};{b}m      \x1b[0m"


def write_png(path, pixels):
    """Write an 8-bit RGB image, ``pixels`` of shape (h, w, 3) in 0-1."""
    data = np.clip(np.rint(np.asarray(pixels) * 255), 0, 255).astype(np.uint8)
    height, width, _ = data.shape
    raw = b"".join(b"\x00" + row.tobytes() for row in data)

    def chunk(kind, body):
        return (struct.pack(">I", len(body)) + kind + body
                + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))

    with open(path, "wb") as handle:
        handle.write(b"\x89PNG\r\n\x1a\n")
        handle.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height,
                                                8, 2, 0, 0, 0)))
        handle.write(chunk(b"IDAT", zlib.compress(raw, 9)))
        handle.write(chunk(b"IEND", b""))


_banner()

# The colour matching functions run from 360 nm; the coefficients here start
# at 412. Luminance, Y, is 99.9 percent covered; Z, the blue, less. Say so
# once rather than at every swatch.
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always", jerlov.CoverageWarning)
    jerlov.spectrum_to_xyz(np.ones_like(WAVELENGTHS), WAVELENGTHS)
coverage_note = (str(caught[0].message).split(". The integral")[0]
                 if caught else "")

daylight = np.interp(WAVELENGTHS, *jerlov.d65())


def luminance(radiance):
    """CIE Y of a radiance spectrum: the human eye's brightness."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.CoverageWarning)
        return float(jerlov.spectrum_to_xyz(radiance, WAVELENGTHS)[1])


def light_at_depth(water_type):
    """Downwelling irradiance at DEPTH_M, from Jerlov's (1976) Kd."""
    kd = jerlov.water(water_type, source="jerlov1976")
    return daylight * np.exp(-kd.kd(WAVELENGTHS) * DEPTH_M)


def look(water_type, finish, distance, *, side_light, ratio):
    """(observation, water radiance) for one finish at one range.

    ``side_light`` is the fraction of the downwelling irradiance that falls
    on the side of the lure the observer sees; ``ratio`` the backscatter
    ratio behind the water's glow. Neither follows from the water type.
    """
    iops = jerlov.water(water_type)
    ed = light_at_depth(water_type)
    water = jerlov.veiling_radiance_estimate(iops, ed, WAVELENGTHS,
                                             backscatter_ratio=ratio)
    scene = jerlov.Scene(iops, side_light * ed, WAVELENGTHS,
                         depth_m=DEPTH_M)
    seen = scene.observe(FINISHES[finish](WAVELENGTHS), distance,
                         veiling_radiance=water)
    return seen, water


def contrast(seen, water):
    """Luminance contrast against open water: (L - L_water) / L_water.

    Looking horizontally past the lure into open water, the background is
    the water itself, whose radiance is the same at every range. Negative
    means darker than the water.
    """
    background = luminance(water)
    return (luminance(seen.radiance) - background) / background


#: The two assumptions, stated. Part 4 shows what rests on them.
SIDE_LIGHT = 0.25
RATIO = BACKSCATTER_RATIOS[1]

# --------------------------------------------------------------------------
rule("1. The set-up")

print(f"""  Observer and lure at the same depth, {DEPTH_M:g} m, looking horizontally,
  with open water behind the lure. Daylight (D65) at the surface, carried
  down with Jerlov's (1976) Kd; a and b from Williamson & Hollins (2022).

  Two numbers the water type does not give, and which this script states:
    - the side of the lure facing the observer receives {SIDE_LIGHT:g} of the
      downwelling irradiance;
    - the water's own glow is the single-scattering estimate with a
      backscatter ratio bb/b of {RATIO:g}.
  Part 4 shows how much rests on them.

  The finishes are smooth stand-ins for paint, not measurements:""")
for name, finish in FINISHES.items():
    rho = finish(WAVELENGTHS)
    flat = rho.max() - rho.min() < 0.01
    shape = "flat" if flat else f"peak near {WAVELENGTHS[np.argmax(rho)]:.0f} nm"
    print(f"    {name:>10}  reflectance {rho.min():.2f}-{rho.max():.2f}, {shape}")

# --------------------------------------------------------------------------
rule("2. What it looks like")

print(f"""The first column is the paint in air: lit by daylight, and
white-balanced to daylight, as a camera on the bank would record it. The
others are white-balanced to the light reaching {DEPTH_M:g} m, as a camera set there
would be, and show the lure at each range; the last is the open water
behind it. Underwater the lure's side receives only {SIDE_LIGHT:g} of the light that
sets the white (part 1), so part of the darkening against the air column
is that stated geometry, not the water.""")


def in_air(name):
    """The paint under daylight, balanced to daylight."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.CoverageWarning)
        warnings.simplefilter("ignore", jerlov.GamutWarning)
        return jerlov.spectrum_to_srgb(FINISHES[name](WAVELENGTHS) * daylight,
                                       WAVELENGTHS, white=daylight)


image_rows = []
for water_type in ("II", "1C", "5C"):
    white = light_at_depth(water_type) / np.pi
    print(f"\n  Jerlov {water_type:<4}" + " " * 3 + "  in air"
          + "".join(f"{d:>7g} m" for d in RANGES_M) + "    water")
    for name in FINISHES:
        air = in_air(name)
        cells, row = [swatch(air)], [air]
        for distance in RANGES_M:
            seen, water = look(water_type, name, distance,
                               side_light=SIDE_LIGHT, ratio=RATIO)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", jerlov.CoverageWarning)
                warnings.simplefilter("ignore", jerlov.GamutWarning)
                rgb = jerlov.spectrum_to_srgb(seen.radiance, WAVELENGTHS,
                                              white=white)
                water_rgb = jerlov.spectrum_to_srgb(water, WAVELENGTHS,
                                                    white=white)
            cells.append(swatch(rgb))
            row.append(rgb)
        print(f"  {name:>12}  " + "  ".join(cells) + "   " + swatch(water_rgb))
        image_rows.append(row + [water_rgb])
if coverage_note:
    print(f"\n  Colours outside sRGB are clipped. "
          f"{coverage_note[0].upper() + coverage_note[1:]}.")

# --------------------------------------------------------------------------
rule("3. What the water decides: how much contrast is left")

print("""Whatever the lure's contrast against the water at arm's length, at
each wavelength the fraction left at range r is exp(-c r): the lure's own
light is lost, the water's glow is common to both and cancels. That rests
on c alone, the coefficient this package has measurements for.""")

lines = (450.0, 500.0, 550.0, 600.0, 650.0)
for water_type in TYPES:
    c = jerlov.water(water_type).c(np.array(lines))
    print(f"\n  Jerlov {water_type:<4}"
          + "".join(f"{nm:>8.0f} nm" for nm in lines))
    for distance in RANGES_M:
        print(f"  {distance:>8g} m " + "".join(
            f"{v:>11.0%}" for v in np.exp(-c * distance)))

best = {t: lines[int(np.argmin(jerlov.water(t).c(np.array(lines))))]
        for t in TYPES}
worst = {t: lines[int(np.argmax(jerlov.water(t).c(np.array(lines))))]
         for t in TYPES}
lost_first = sorted({worst[t] for t in TYPES})
where = "; ".join(
    f"{nm:.0f} nm in {', '.join(t for t in TYPES if worst[t] == nm)}"
    for nm in lost_first)
print(f"""
  Of these five wavelengths, the one that keeps its contrast longest moves
  from {best["IB"]:.0f} nm in IB to {best["5C"]:.0f} nm in 5C. The one that loses it first is
  {where}.
  A lure that differs from the water mainly in that first band keeps the
  difference; one that differs mainly in the last loses it first.""")

# --------------------------------------------------------------------------
rule("4. What the water does not decide: where the contrast starts")

print(f"""Luminance contrast at {RANGES_M[0]:g} m, (L_lure - L_water) / L_water, in Jerlov 1C,
for three guesses at the light on the lure's visible side and two at the
water's backscatter ratio. 0 means it matches the water; negative is
darker. These are the two numbers stated in part 1.""")

combos = [(f, r) for f in (1.0, 0.25, 0.05) for r in BACKSCATTER_RATIOS]
print("\n  " + " " * 12 + "".join(f"{f'side {f:g}':>11}" for f, _ in combos))
print("  " + " " * 12 + "".join(f"{f'bb/b {r:g}':>11}" for _, r in combos))
start = {}
for name in FINISHES:
    values = []
    for f, r in combos:
        seen, water = look("1C", name, RANGES_M[0], side_light=f, ratio=r)
        values.append(contrast(seen, water))
    start[name] = values
    print(f"  {name:>12}" + "".join(f"{v:>+11.2f}" for v in values))

flips = [n for n, v in start.items() if min(v) < 0 < max(v)]
spread = max(max(v) / min(v) for v in start.values() if min(v) > 0)
print(f"""
  The same finish in the same water starts anywhere across a factor of
  {spread:.0f}, and {", ".join(flips)} {"change" if len(flips) > 1 else "changes"} sign: brighter than the water under
  one guess, darker under another. The single-scattering glow also leaves
  out light scattered more than once. Ranking finishes by these numbers
  ranks the guesses, not the paint.

  What can be done instead: measure the lure's radiance and the water's,
  side by side, close up, in the water in question, at each wavelength or
  at least in a camera's three channels. Part 3 then carries that
  difference out to any range, at each wavelength, without either guess.""")

# --------------------------------------------------------------------------
if "--png" in sys.argv:
    path = sys.argv[sys.argv.index("--png") + 1]
    block = 24
    pixels = np.repeat(np.repeat(np.array(image_rows), block, axis=0),
                       block, axis=1)
    write_png(path, pixels)
    print(f"\n  wrote {path}: rows are the finishes for II, 1C and 5C in turn,")
    print(f"  columns the paint in air, the ranges "
          f"{', '.join(f'{d:g}' for d in RANGES_M)} m, and then the water")

# --------------------------------------------------------------------------
rule("Before you use any of this")

print("""  - The contrast uses the CIE luminance of the human eye. Fish see with
    other photoreceptors, and the ranking of colours depends on whose eye
    weighs them; `what_an_eye_sees.py` shows how to use another.
  - Nothing here is about whether a fish notices or takes a lure. Contrast
    is a property of light, and nothing more is claimed for it.
  - The line of sight is horizontal, with open water behind the lure. Seen
    from below or above, against the surface or the bottom, the background
    is different and is not computed here.
  - The light on the lure's visible side and the water's glow are guesses,
    stated in part 1; part 4 shows they decide where the contrast starts.
  - The lure is a flat diffuse surface, lit evenly. Its shape, any mirror
    finish, holographic flash and fluorescence are all left out.
  - The finishes are invented curves, and D65 stands in for the sky.
""")

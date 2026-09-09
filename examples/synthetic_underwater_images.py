"""Synthesising underwater appearance from an in-air spectrum.

Papers on underwater vision routinely need to turn an above-water image into
what it would look like at depth, usually to make training data. The
attenuation coefficients get hard-coded, and the numbers in circulation
disagree by large factors; see `sources_disagree.py`.

This does the same job from the published coefficients, with the provenance of
every number attached.

    python examples/synthetic_underwater_images.py

Read the limits before using this for anything. They are listed at the end,
and they are not small.
"""

import warnings

import numpy as np

import jerlov

# Measured points exist from 412 to 715 nm; staying inside that avoids
# relying on the model extrapolation at the ends.
WAVELENGTHS = np.arange(412.0, 701.0, 4.0)

#: A crude Macbeth-like set. Real work should use measured reflectance
#: spectra; these are smooth stand-ins, and the script says so.
PATCHES = {
    "neutral 50%": lambda wl: np.full_like(wl, 0.50),
    "red":         lambda wl: 0.05 + 0.55 * (wl > 600),
    "green":       lambda wl: 0.05 + 0.35 * np.exp(-0.5 * ((wl - 550) / 45) ** 2),
    "blue":        lambda wl: 0.05 + 0.40 * np.exp(-0.5 * ((wl - 465) / 40) ** 2),
    "orange":      lambda wl: 0.05 + 0.50 / (1 + np.exp(-(wl - 590) / 15)),
}


def swatch(rgb):
    """A terminal colour block plus the hex value."""
    r, g, b = (int(round(255 * float(np.clip(c, 0, 1)))) for c in rgb)
    return f"\x1b[48;2;{r};{g};{b}m    \x1b[0m #{r:02x}{g:02x}{b:02x}"


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



# --------------------------------------------------------------------------
_banner()
rule("Setting up")

water_type = "III"
depth_m = 15.0
backscatter_ratio = 0.015          # bb/b: stated, never assumed

iops = jerlov.water(water_type)                            # measured a and b
kd = jerlov.water(water_type, source="austin1986")         # Kd for the descent
daylight = np.interp(WAVELENGTHS, *jerlov.d65(), left=0.0, right=0.0)

print(f"  water type          {water_type}   ({iops.source.key})")
print(f"  depth               {depth_m:g} m")
print(f"  surface spectrum    CIE D65, a daylight phase, not a measurement")
print(f"  backscatter ratio   {backscatter_ratio}  (bb/b, stated by us)")

deeper = jerlov.water_type_at_depth(water_type, depth_m)
print(f"\n  At {depth_m:g} m, Jerlov {water_type} water is typically {deeper} "
      f"(Williamson & Hollins 2023).")
print(f"  This script keeps using {water_type}; swapping to {deeper} is one "
      f"line, and that\n  is the caller's decision to make.")

with warnings.catch_warnings():
    warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
    scene = jerlov.Scene.at_depth(iops, depth_m, daylight, WAVELENGTHS, kd=kd)
    veiling = jerlov.veiling_radiance_estimate(
        iops, scene.downwelling, WAVELENGTHS, backscatter_ratio=backscatter_ratio
    )

# --------------------------------------------------------------------------
rule("How the target's light is lost with range")

print("  transmittance exp(-c r), averaged over the band\n")
distances = [0.0, 1.0, 2.0, 4.0, 8.0, 16.0]
print("  " + "".join(f"{d:>8.0f} m" for d in distances))
print("  " + "".join(
    f"{np.mean(scene.transmittance(d)):>10.4f}" for d in distances))

# --------------------------------------------------------------------------
rule("What a camera white-balanced at the surface would record")

print("  The white reference is daylight, so the water's own cast stays in.\n")
surface_white = daylight / np.pi
print("  " + " " * 14 + "".join(f"{d:>12.0f} m" for d in distances))
for name, reflectance in PATCHES.items():
    rho = reflectance(WAVELENGTHS)
    cells = []
    for distance in distances:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            observed = scene.observe(rho, distance, veiling_radiance=veiling)
            cells.append(swatch(jerlov.spectrum_to_srgb(
                observed.radiance, WAVELENGTHS, white=surface_white)))
    print(f"  {name:>12}  " + "  ".join(cells))

# --------------------------------------------------------------------------
rule("What a camera white-balanced at depth would record")

print("  The white reference is the downwelling irradiance there, so a grey")
print("  card comes out grey at zero range and the loss with distance shows.\n")
local_white = scene.downwelling / np.pi
print("  " + " " * 14 + "".join(f"{d:>12.0f} m" for d in distances))
for name, reflectance in PATCHES.items():
    rho = reflectance(WAVELENGTHS)
    cells = []
    for distance in distances:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            observed = scene.observe(rho, distance, veiling_radiance=veiling)
            cells.append(swatch(jerlov.spectrum_to_srgb(
                observed.radiance, WAVELENGTHS, white=local_white)))
    print(f"  {name:>12}  " + "  ".join(cells))

# --------------------------------------------------------------------------
rule("How much of what you see is just water")

rho = PATCHES["neutral 50%"](WAVELENGTHS)
print(f"  {'range':>8} {'veiling share':>15} {'contrast vs 10% grey':>22}")
dark = 0.10 * scene.downwelling / np.pi
for distance in distances[1:]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        observed = scene.observe(rho, distance, veiling_radiance=veiling)
    print(f"  {distance:>6.0f} m {np.mean(observed.veiling_fraction):>14.1%} "
          f"{np.mean(np.abs(observed.contrast(dark))):>22.3f}")

# --------------------------------------------------------------------------
rule("Coefficients for a fitting pipeline")

coefficients = scene.attenuation_coefficients(
    (0.5, 8.0), veiling_radiance=veiling)
print("  For code that fits the Akkaynak-Treibitz form,")
print("  I = J exp(-beta_D r) + B_inf (1 - exp(-beta_B r)):\n")
for nm in (450.0, 550.0, 650.0):
    i = int(np.argmin(np.abs(WAVELENGTHS - nm)))
    print(f"    {WAVELENGTHS[i]:>5.0f} nm   beta_D {coefficients.beta_D[i]:.4f}"
          f"   beta_B {coefficients.beta_B[i]:.4f}"
          f"   B_inf {coefficients.B_inf[i]:.5f}")
print(f"\n  are_distinct = {coefficients.are_distinct}")
print(f"  {coefficients.note}")

# --------------------------------------------------------------------------
rule("Before you use any of this")

print("""  This computes what the published coefficients imply. It has not been
  compared against photographs, because the measurements needed to do that do
  not appear to exist. Treat the numbers as a physically grounded starting
  point, not as a prediction.

  Specifically:

  - bb/b was stated by us, not derived. It is not determined by the Jerlov
    classification: deriving it from the two sources' particle concentrations
    gives answers differing by up to a factor of 31. DATA.md section 10.
  - The veiling radiance came from the single-scattering estimate, whose
    factor of 2 pi assumes backscattered light spreads evenly over the
    backward hemisphere. Real phase functions are strongly peaked.
  - The path is horizontal, the target Lambertian, and there is no
    forward-scatter blur. This is the radiance of one point, not the
    sharpness of an image.
  - The surface spectrum is CIE D65. The real one depends on solar elevation,
    atmosphere and the state of the surface.
  - The reflectance spectra above are smooth inventions. Use measured ones.
  - The white balance is a von Kries transform in XYZ, not CAT02, and
    underwater illumination is strongly coloured.

  Every one of these is a choice you can replace with a measurement.
""")

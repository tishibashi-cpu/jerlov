"""What an eye or a sensor records, rather than what a display shows.

sRGB answers "what would a person see on a screen". Plenty of questions are
not that: what a fish's photoreceptors absorb, what a camera's three channels
record, what a filtered detector returns. `integrate_response` takes any
spectral sensitivity.

    python examples/what_an_eye_sees.py

The receptor curves below are Gaussians at plausible peak wavelengths, not
measured absorbances. Substitute real ones; that is the point of the function.
"""

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


def gaussian(wl, peak, width):
    return np.exp(-0.5 * ((wl - peak) / width) ** 2)


def bar(value, largest, width=22):
    filled = int(round(width * value / largest)) if largest > 0 else 0
    return "#" * filled + "." * (width - filled)


_banner()

# Austin & Petzold's Kd model runs 350-700 nm and the package will not
# extrapolate, so that is the band. The CIE observer reaches further, which is
# what part 4 is about.
WL = np.arange(350.0, 701.0, 2.0)

#: Rough peak absorbances. Real work needs measured curves.
RECEPTORS = {
    "human L cone (564 nm)": (564.0, 45.0),
    "human M cone (534 nm)": (534.0, 45.0),
    "human S cone (420 nm)": (420.0, 30.0),
    "deep-sea rod (480 nm)": (480.0, 40.0),
    "shallow rod (500 nm)": (500.0, 40.0),
    "red-shifted rod (530 nm)": (530.0, 40.0),
}

# --------------------------------------------------------------------------
rule("1. The light at depth")

water_type = "II"
iops = jerlov.water(water_type)
kd = jerlov.water(water_type, source="austin1986")
daylight = np.interp(WL, *jerlov.d65(), left=0.0, right=0.0)

print(f"  water {water_type}, illuminated by CIE D65 at the surface\n")
print(f"  {'depth':>7} {'400 nm':>9} {'480 nm':>9} {'550 nm':>9} {'650 nm':>9}")
scenes = {}
for depth in (0.0, 5.0, 20.0, 50.0):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        scene = jerlov.Scene.at_depth(iops, depth, daylight, WL, kd=kd)
    scenes[depth] = scene
    cells = "".join(
        f"{scene.downwelling[int(np.argmin(np.abs(WL - nm)))]:>9.2f}"
        for nm in (400, 480, 550, 650)
    )
    print(f"  {depth:>5.0f} m {cells}")

print("""
  The spectrum does not just dim, it narrows. By 50 m almost everything left
  is between 450 and 550 nm.""")

# --------------------------------------------------------------------------
rule("2. What each receptor absorbs")

print("""Each row is one receptor's response to the light at that depth,
normalised so the largest response at the surface is 1.
""")
sensitivities = {name: gaussian(WL, peak, width)
                 for name, (peak, width) in RECEPTORS.items()}

surface = {
    name: float(jerlov.integrate_response(
        scenes[0.0].downwelling, WL, curve, WL, name=name)[0])
    for name, curve in sensitivities.items()
}
reference = max(surface.values())

for depth in (0.0, 20.0, 50.0):
    print(f"  at {depth:.0f} m")
    responses = {
        name: float(jerlov.integrate_response(
            scenes[depth].downwelling, WL, curve, WL, name=name)[0])
        for name, curve in sensitivities.items()
    }
    for name, value in responses.items():
        print(f"    {name:>24} {bar(value, reference)} {value / reference:>6.1%}")
    print()

print("""  At the surface the long-wavelength receptors do best, because daylight
  has more energy there. By 50 m the order has reversed and the 480 nm
  receptor is ahead: the water has thrown away the wavelengths the others
  were built for.

  This is why deep-sea fish rod pigments cluster near 480 nm. The package
  does not know that; it falls out of the coefficients.""")

# --------------------------------------------------------------------------
rule("3. A three-channel camera")

print("""The same function takes an (n, k) array for k channels at once.
""")
centres = (450.0, 550.0, 620.0)
camera = np.stack([gaussian(WL, c, 35.0) for c in centres], axis=1)

print(f"  {'depth':>7} {'blue':>10} {'green':>10} {'red':>10}   {'R/B ratio':>10}")
for depth in (0.0, 5.0, 20.0, 50.0):
    channels = jerlov.integrate_response(
        scenes[depth].downwelling, WL, camera, WL, name="camera")
    normalised = channels / channels.max()
    ratio = channels[2] / channels[0]
    print(f"  {depth:>5.0f} m " + "".join(f"{v:>10.3f}" for v in normalised)
          + f"   {ratio:>10.4f}")

print("""
  The red-to-blue ratio is what an underwater white balance has to undo, and
  it changes by two orders of magnitude over 50 m. A fixed white balance is
  correct at exactly one depth.""")

# --------------------------------------------------------------------------
rule("4. The check that stops a silent error")

print("""Integrating a spectrum against a sensitivity that reaches further than
the spectrum does quietly drops the ends. Every integration reports how much
of the sensitivity it actually covered.
""")
narrow = np.arange(500.0, 601.0, 2.0)
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    jerlov.spectrum_to_xyz(np.ones_like(narrow), narrow)
for entry in caught:
    if issubclass(entry.category, jerlov.CoverageWarning):
        print(f"    {entry.message}")

print("""
  Without that, the answer looks like any other number.""")

# --------------------------------------------------------------------------
rule("What this assumed")

print("""  - The receptor and camera curves are Gaussians at plausible peaks, not
    measurements. Real absorbances are asymmetric and depend on the pigment.
  - The surface spectrum is CIE D65, a daylight phase, not a measurement of
    the light above any particular sea.
  - Only the downwelling irradiance is used. A real eye sees a target at some
    range, which needs `Scene.observe` and therefore a backscatter ratio you
    would have to state.
  - Absorption by the pigment is not the same as a signal: gain, noise and
    neural processing all sit between. This is the first step, not the
    answer.
""")

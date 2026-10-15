"""What an eye or a sensor records, rather than what a display shows.

sRGB answers "what would a person see on a screen". Plenty of questions are
not that: what a fish's photoreceptors absorb, what a camera's three channels
record, what a filtered detector returns. `integrate_response` takes any
spectral sensitivity.

    python examples/what_an_eye_sees.py

The receptor curves below are Gaussians at plausible peak wavelengths, not
measured absorbances. Substitute real ones; that is the point of the function.

A photoreceptor absorbs photons, and a camera's pixels count them, so every
spectrum is converted to photons before it is integrated. Until 0.14.1 this
example integrated the energy spectrum instead; part 2 shows what that
changes.
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
kd = jerlov.water(water_type, source="austin1986")
daylight = np.interp(WL, *jerlov.d65(), left=0.0, right=0.0)
# Only the downwelling irradiance is needed, so Kd alone is enough. A Scene
# would also evaluate the beam attenuation c of the default IOPs, which is
# extrapolated by their model at 350-410 nm and warns, for a quantity this
# example never uses.
downwelling = {depth: daylight * np.exp(-kd.kd(WL) * depth)
               for depth in (0.0, 5.0, 20.0, 50.0)}

print(f"  water {water_type}, illuminated by CIE D65 at the surface\n")
print(f"  {'depth':>7} {'400 nm':>9} {'480 nm':>9} {'550 nm':>9} {'650 nm':>9}")
for depth, ed in downwelling.items():
    cells = "".join(f"{ed[int(np.argmin(np.abs(WL - nm)))]:>9.2f}"
                    for nm in (400, 480, 550, 650))
    print(f"  {depth:>5.0f} m {cells}")


def photon_share(lo, hi, depth):
    """Share of the photons at ``depth`` that are between lo and hi nm."""
    def flux(band):
        return jerlov.par_profile(daylight, WL, depth, kd=kd, unit="energy",
                                  band=band).par
    return float(flux((lo, hi)) / flux((WL[0], WL[-1])))


print(f"""
  The spectrum does not just dim, it narrows. By 50 m {photon_share(450.0, 550.0, 50.0):.0%} of the photons
  left are between 450 and 550 nm.""")

# --------------------------------------------------------------------------
rule("2. What each receptor absorbs")

print("""Each row is one receptor's response to the light at that depth,
normalised so the largest response at the surface is 1.
""")
sensitivities = {name: gaussian(WL, peak, width)
                 for name, (peak, width) in RECEPTORS.items()}


def photons(depth):
    """The downwelling spectrum at ``depth`` as a count of photons, up to a
    constant: a photon of wavelength l carries energy h c / l."""
    return downwelling[depth] * WL


def catches(spectrum):
    return {name: float(jerlov.integrate_response(
                spectrum, WL, curve, WL, name=name)[0])
            for name, curve in sensitivities.items()}


reference = max(catches(photons(0.0)).values())
leader = {}
for depth in (0.0, 20.0, 50.0):
    print(f"  at {depth:.0f} m")
    responses = catches(photons(depth))
    leader[depth] = max(responses, key=responses.get)
    for name, value in responses.items():
        print(f"    {name:>24} {bar(value, reference)} {value / reference:>6.1%}")
    print()

surface = catches(photons(0.0))
energy = catches(downwelling[0.0])
first, second = sorted(surface, key=surface.get, reverse=True)[:2]
blue = "human S cone (420 nm)"
print(f"""  At the surface the {first.split(" (")[0]} and {second.split(" (")[0]} catch the most, within
  {100 * (1 - surface[second] / surface[first]):.1f} percent of each other. By 20 m the {leader[20.0]} is
  ahead, and still at 50 m: the water has removed most of the light at the
  wavelengths the others peak at.

  Counted as energy instead of photons, the S cone's surface catch would
  be {energy[blue] / max(energy.values()):.0%} of the largest rather than {surface[blue] / max(surface.values()):.0%}. A blue photon carries more energy
  than a red one, so energy weights the blue up; the basis of the curve
  has to be the basis of the spectrum.""")

# --------------------------------------------------------------------------
rule("3. A three-channel camera")

print("""The same function takes an (n, k) array for k channels at once.
""")
centres = (450.0, 550.0, 620.0)
camera = np.stack([gaussian(WL, c, 35.0) for c in centres], axis=1)

print(f"  {'depth':>7} {'blue':>10} {'green':>10} {'red':>10}   {'R/B ratio':>10}")
ratios = {}
for depth in (0.0, 5.0, 20.0, 50.0):
    channels = jerlov.integrate_response(
        photons(depth), WL, camera, WL, name="camera")
    normalised = channels / channels.max()
    ratios[depth] = channels[2] / channels[0]
    print(f"  {depth:>5.0f} m " + "".join(f"{v:>10.3f}" for v in normalised)
          + f"   {ratios[depth]:>10.4f}")

print(f"""
  The red-to-blue ratio is what an underwater white balance has to undo, and
  it falls by a factor of {ratios[0.0] / ratios[50.0]:.0f} over 50 m. A fixed white balance is
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
  - The curves are taken as sensitivities per photon. A camera's curve
    published per unit energy must be divided by the wavelength first.
  - The surface spectrum is CIE D65, a daylight phase, not a measurement of
    the light above any particular sea.
  - Only the downwelling irradiance is used. A real eye sees a target at some
    range, which needs `Scene.observe` and therefore a backscatter ratio you
    would have to state.
  - Absorption by the pigment is not the same as a signal: gain, noise and
    neural processing all sit between. This is the first step, not the
    answer.
""")

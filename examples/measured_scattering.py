"""Scattering that was measured, instead of a backscatter ratio that was guessed.

`Water.bb` refuses to guess bb/b, and every scene that needs veiling light
needs one. Petzold (1972) measured the full volume scattering function in
eight ocean waters, from the clear Tongue of the Ocean in the Bahamas to San
Diego Harbor. This shows what is in those measurements and what a measured
ratio changes.

    python examples/measured_scattering.py

These are eight particular waters in 1971, at 530 nm. None is a Jerlov type.
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


_banner()

STATIONS = [jerlov.petzold_scattering(s) for s in jerlov.PETZOLD_STATIONS]

# --------------------------------------------------------------------------
rule("1. Eight waters")

print(f"  {'station':>9}  {'c':>6} {'b':>7} {'b/c':>5} {'B/S':>6}"
      f" {'below 0.1 deg':>14}   where")
for f in STATIONS:
    print(f"  {f.station:>9}  {f.c:>6.3f} {f.b:>7.4f} {f.b / f.c:>5.2f}"
          f" {f.backscatter_ratio:>6.3f} {f.fraction_below_0_1_deg:>13.1%}"
          f"   {f.locale}")

print("""
  c and b in 1/m at 530 nm. B/S is the share of scattering beyond 90
  degrees, bb/b, and runs from 0.013 to 0.044: a factor of three, and the
  clearest water has the highest. Pure water scatters as much backward as
  forward, and it counts for more where there are fewer particles.

  The last column is the share of b below 0.1 degree, where nothing was
  measured and the report extended the curve. It is counted in b.""")

# --------------------------------------------------------------------------
rule("2. The shape: almost everything goes forward")

print("""The phase function, vsf / b, at a few angles. In every one of the eight
it falls by four orders of magnitude between 1 and 90 degrees.""")

angles = (1.0, 10.0, 45.0, 90.0, 135.0, 180.0)
print(f"\n  {'station':>9}" + "".join(f"{a:>10g}" for a in angles)
      + "   1/sr")
for f in STATIONS:
    values = [f.vsf_at(a) / f.b for a in angles]
    print(f"  {f.station:>9}" + "".join(f"{v:>10.3g}" for v in values))

print("""
  Every curve has its minimum between 100 and 150 degrees and rises again
  towards 180, by up to three times. The single-scattering
  estimate of the veiling light assumes the backward half is flat.""")

# --------------------------------------------------------------------------
rule("3. What the measured ratio changes")

print("""The veiling light of a scene scales with bb, so with the ratio. Here
is Jerlov 1C water at 10 m, a grey target at 5 m seen against open water,
with the ratio guessed at a usual coastal 0.015 and then taken in turn from
the measured coastal and harbor waters.""")

wl = np.arange(450.0, 651.0, 50.0)
w = jerlov.water("1C")
surface = np.interp(wl, *jerlov.d65())
with warnings.catch_warnings():
    warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
    scene = jerlov.Scene.at_depth(w, 10.0, surface, wl,
                                  kd=jerlov.water("1C", source="austin1986"))
grey = np.full(wl.size, 0.3)


def contrast_at(ratio):
    b_inf = jerlov.veiling_radiance_estimate(
        w, scene.downwelling, wl, backscatter_ratio=ratio)
    seen = scene.observe(grey, 5.0, veiling_radiance=b_inf)
    i = int(np.argmin(np.abs(wl - 550.0)))
    return seen.veiling_fraction[i], seen.contrast(b_inf)[i]


print(f"\n  {'ratio from':>18} {'bb/b':>6} {'veiling share':>14}"
      f" {'contrast':>9}   at 550 nm")
for label, ratio in [("a guess", 0.015)] + [
        (f.station, f.backscatter_ratio)
        for f in STATIONS if f.station.startswith("HAOCE")
        or f.station.startswith("NUC")]:
    share, contrast = contrast_at(ratio)
    print(f"  {label:>18} {ratio:>6.3f} {share:>13.1%} {contrast:>9.2f}")

print("""
  The measured ratios alone move the veiling share from 18.5 to 25.8 percent
  and the contrast against the water from 4.0 to 2.6. A brighter water
  background is a dimmer-looking target: against open water the contrast is
  (L_target - B) / B times the transmittance, and B scales with the ratio.""")

# --------------------------------------------------------------------------
rule("4. The angles nothing was measured at")

clear = jerlov.petzold_scattering("AUTEC 8")
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    clear.vsf_at(0.12)
for message in caught:
    print(f"\n  {message.message}")

try:
    clear.vsf_at(0.05)
except ValueError as error:
    print(f"\n  Below the table it refuses:\n    {error}")

# --------------------------------------------------------------------------
rule("Before you use any of this")

print("""  - These are eight waters on eight days in 1971. A measured ratio from
    a water like yours is better than a guess, but it is not yours.
  - Everything is at 530 nm. B/S changes with wavelength, because pure
    water's share of the scattering does.
  - Everything is total: pure water and particles together. That is what
    Water.bb multiplies, so the ratio can be passed straight in.
  - None of the stations is a Jerlov type, and none is mapped to one.
  - The veiling light still comes from the single-scattering estimate,
    whose flat backward half section 2 shows is not.

  Every one of these is a choice you can replace with a measurement.
""")

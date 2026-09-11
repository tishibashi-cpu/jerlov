"""You measured something in the field. What can you get from it?

Instruments give one quantity at one wavelength, or a handful. The published
relations turn that into more, at a stated accuracy. This shows the three
routes the package provides, and what each of them costs you.

    python examples/from_one_measurement.py

Everything here rests on empirical relations fitted to particular datasets.
The accuracy figures are the papers' own and are not small; they are printed
alongside each result rather than buried.
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

# --------------------------------------------------------------------------
rule("1. A single-wavelength Kd meter")

print("""Say you measured Kd = 0.060 1/m at 490 nm. Austin & Petzold (1986)
Eq. (6) reconstructs the rest of the spectrum from that one value, using the
slope of their model and the attenuation of pure sea water.""")

measured_kd, at_nm = 0.060, 490
wavelengths = np.array([440.0, 490.0, 550.0, 650.0])
spectrum = jerlov.kd_spectrum(measured_kd, at_nm, wavelengths)

print(f"\n  {'nm':>6} {'Kd [1/m]':>10}")
for nm, value in zip(wavelengths, spectrum):
    mark = "  <- measured" if nm == at_nm else ""
    print(f"  {nm:>6.0f} {value:>10.4f}{mark}")

print("""
  The measured wavelength comes back unchanged, which is the check that the
  anchoring is right rather than a coincidence.""")

print("""
Two limits, both stated by the authors:

  - K(490) must be below 0.16 1/m. Beyond that the linearity the model rests
    on fails. Yours is %.3f, so this is fine.
  - Accuracy is about 8 percent up to 590 nm, degrading to 31 percent at
    670 nm (Austin & Petzold 1990, from 83 stations up to 77.7 N).""" % measured_kd)

try:
    jerlov.kd_spectrum(0.060, 490, 900.0)
except ValueError as error:
    print(f"\n  Outside the model's range it refuses:\n    {error}")

# --------------------------------------------------------------------------
rule("2. A transmissometer")

print("""A transmissometer measures the beam attenuation c, not the scattering
b. Smart (2007) fitted (b - bw) / (c - cw) to six datasets, so b follows.""")

c_measured, nm = 0.50, 555.0
bw, cw = 0.0019, 0.0659           # pure sea water at 555 nm
for bound in ("average", "min", "max"):
    b = jerlov.b_from_c(c_measured, nm, bw=bw, cw=cw, bound=bound)
    print(f"  {bound:>8}: b = {b:.4f} 1/m")

print("""
  Use `min` for clear water and `max` for turbid water, meaning c at 488 nm
  above 1.0 1/m. The average is accurate to about 10 percent.

  Ratios are lower than tabulated in CDOM-rich water, near a river mouth for
  instance, particularly below 488 nm. And c itself carries perhaps 10
  percent error from forward-scattered light reaching the detector.""")

a_est = c_measured - jerlov.b_from_c(c_measured, nm, bw=bw, cw=cw)
print(f"\n  a = c - b = {a_est:.4f} 1/m, with both errors in it.")

# --------------------------------------------------------------------------
rule("3. Your own spectra")

print("""If you have measured a and b yourself, hand them over directly. The
object behaves exactly like one built from a published water type: no
extrapolation, gaps stay gaps, bb still has to be stated.""")

wl = np.arange(420.0, 681.0, 20.0)
a_measured = 0.02 + 0.35 * np.exp(-(wl - 420.0) / 90.0) + 0.30 * (wl > 600)
b_measured = 0.45 * (550.0 / wl) ** 0.8
mine = jerlov.Water.from_measurements(wl, a=a_measured, b=b_measured,
                                      name="Station 14, 3 m")   # reused below
print(f"\n  {mine}")
print(f"  a(550) = {mine.a(550):.4f}   b(550) = {mine.b(550):.4f}   "
      f"c(550) = {mine.c(550):.4f}")

try:
    mine.a(700)
except ValueError as error:
    print(f"\n  Outside your own data it refuses too:\n    {error}")

try:
    mine.bb(550)
except jerlov.MissingQuantityError as error:
    print(f"\n  And it will not invent a backscatter ratio:\n    "
          f"{str(error).split('.')[0]}.")

print("""
  Everything downstream takes it: Scene, the colour conversions, the
  Akkaynak-Treibitz coefficients. A published water type is only an entry
  point that builds the same kind of object.""")

# --------------------------------------------------------------------------
rule("4. A backscattering sensor")

print("""`Water.bb` refuses to guess a backscattering ratio, because the Jerlov
classification does not determine one. With an instrument you do not have to
guess: a HydroScat, an ECO-BB or a VSF meter reports the volume scattering
function at one angle, and Boss & Pegau (2001) give the conversion.""")

angle, beta, nm, salinity = 140.0, 0.0021, 532.0, 35.0
measured = jerlov.bb_from_vsf(beta, angle, nm, salinity_psu=salinity)

print(f"""
  reading      beta({angle:g} deg) = {beta} 1/(m sr) at {nm:g} nm, S = {salinity:g} psu

  bb           {measured.bb:.5f} 1/m
   of which
    particles  {measured.particulate:.5f}
    water      {measured.water:.5f}   (Morel's formula, not your instrument)

  chi_p        {measured.chi_p:.2f} +- {measured.quoted_error_percent:.1f}%""")

print("""
  The water term is subtracted before the conversion and added back after,
  because chi differs between water and particles everywhere except near 118
  degrees. That crossing is why instruments cluster around 120.""")

print(f"\n  {'angle':>7} {'chi_p':>7} {'spread':>8}")
for a_deg in (90, 110, 120, 140, 160, 170):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = jerlov.bb_from_vsf(beta, float(a_deg), nm, salinity_psu=salinity)
    flag = "  <- warns" if any(
        issubclass(e.category, jerlov.AngleWarning) for e in caught) else ""
    print(f"  {a_deg:>5} deg {r.chi_p:>7.2f} {r.quoted_error_percent:>7.1f}%{flag}")

print("""
  Angles outside 90 to 170 are refused: no measurement in the set went
  further. The quoted spread is chi_p alone; the water amplitude carries a
  further 15 percent, and your calibration sits on top of both.""")

# --------------------------------------------------------------------------
rule("5. What the measurement buys you")

print("""Combine parts 3 and 4: your own a and b, and your own bb. The
backscattering ratio is now measured rather than stated.""")

bb_over_b = measured.bb / mine.b(nm)
print(f"\n  bb/b at {nm:g} nm = {measured.bb:.5f} / {mine.b(nm):.4f} "
      f"= {bb_over_b:.4f}")
print("""
  Reported ranges are roughly 0.005 to 0.01 for open ocean and 0.015 to 0.03
  for coastal water, so this water sits at the turbid end.""")

surface = np.interp(wl, *jerlov.d65(), left=0.0, right=0.0)
kd_source = jerlov.water("II", source="austin1986")
with warnings.catch_warnings():
    warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
    scene = jerlov.Scene.at_depth(mine, 8.0, surface, wl, kd=kd_source)
white = scene.downwelling / np.pi

print("""
Had you guessed 0.015, a reasonable-looking coastal figure, against what you
measured:
""")
print(f"  {'':>18}" + "".join(f"{d:>10.0f} m" for d in (2.0, 5.0, 10.0)))
at_five = {}
for label, ratio in (("guessed 0.015", 0.015),
                     (f"measured {bb_over_b:.3f}", bb_over_b)):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        b_inf = jerlov.veiling_radiance_estimate(
            mine, scene.downwelling, wl, backscatter_ratio=ratio)
        veiling, contrast = [], []
        for distance in (2.0, 5.0, 10.0):
            observed = scene.observe(np.full_like(wl, 0.5), distance,
                                     veiling_radiance=b_inf)
            veiling.append(np.mean(observed.veiling_fraction))
            contrast.append(np.mean(np.abs(observed.contrast(0.1 * white))))
    at_five[label] = contrast[1]
    print(f"  {label:>16}  " + "".join(f"{v:>11.1%}" for v in veiling)
          + "   veiling")
    print(f"  {'':>16}  " + "".join(f"{c:>11.3f}" for c in contrast)
          + "   contrast")

guessed, actual = at_five["guessed 0.015"], at_five[f"measured {bb_over_b:.3f}"]
print(f"""
  At 5 m the guess puts the contrast {guessed / actual - 1:.0%} above what the
  measurement gives. That is why `Water.bb` has no default: a plausible number
  produces a plausible answer, and there is nothing in the output to say which
  one you got.""")

# --------------------------------------------------------------------------
rule("6. Which published type is your water closest to?")

print("""There is no classify() here, deliberately: a single Kd does not pin a
water type, and the boundaries differ between editions of the classification.
What you can do is compare.""")

print(f"\n  Your Kd(490) = {measured_kd:.3f} 1/m against the published types\n")
print(f"  {'type':>5} {'Kd(490) 1976':>14} {'ratio':>8}")
with warnings.catch_warnings():
    warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
    for water_type in ("I", "IA", "IB", "II", "III", "1C"):
        published = jerlov.water(water_type, source="jerlov1976").kd(490.0)
        print(f"  {water_type:>5} {published:>14.4f} {measured_kd/published:>7.2f}x")

print("""
  Closest is not the same as equal, and a match at one wavelength is not a
  match. Two waters with the same Kd(490) can differ severalfold in
  backscattering, which is why the classification says nothing about it.

  Aas et al. (2013) give K(475) boundaries for assigning a type, and note
  that Jerlov's own boundaries changed between the 1968, 1976 and 1978
  editions. If you need a type, use their table and say which one you used.""")

# --------------------------------------------------------------------------
rule("What each of these assumed")

print("""  - The Kd reconstruction is a two-parameter model fitted to Pacific and
    Atlantic stations. Its own authors put it at 8 percent below 590 nm and
    31 percent at 670 nm.
  - The b-from-c ratio is an average over six datasets, about 10 percent, and
    lower than tabulated in CDOM-rich water.
  - a = c - b inherits the error of both.
  - The synthetic spectra in part 3 are made up. Yours are not, which is the
    point of that route.
  - The backscattering conversion rests on 41 measured scattering functions,
    and on Morel's formula for pure sea water whose amplitude is good to
    about 15 percent. Neither includes your instrument's calibration.
  - Measuring bb tells you about the water you were in. It still gives no bb
    for a Jerlov water type, because a water type is defined by Kd and Kd
    barely depends on bb. DATA.md sections 10 and 18.
""")

# Changelog

Every release is archived on Zenodo under the concept DOI
[10.5281/zenodo.22321312](https://doi.org/10.5281/zenodo.22321312), which
always resolves to the latest version.

## 0.20.0 — 2026-10-24

An attenuation coefficient from a Secchi depth, by a rule the caller names.
No shipped value changed.

**Added.** `k_from_secchi(secchi_depth_m, coefficient=...)` returns
coefficient / Secchi depth, in 1/m. The coefficient has no default.
`POOLE1929_SECCHI_COEFFICIENT` is 1.7, the rule of Poole & Atkins (1929):
the mean of K times the Secchi depth over their 14 comparisons off
Plymouth in 1928, which ran from 1.32 to 2.18. Their K is the attenuation
from 0 to 20 m of the light on a horizontal surface, measured with
potassium photocells, so it is not a spectral Kd or Kd(PAR). Every call
raises a `ProvenanceWarning` that gives this range and the authors' own
words, "a very rough rule" (DECISIONS.md section 52).

**Examples.** `seagrass_depth_limit.py` has a fifth part, for when all you
have is a Secchi depth. Duarte (1991) and Duarte et al. (2007) used K =
1.7 / Secchi depth where a report gave no attenuation coefficient. With
that rule the 11 percent depth is 1.30 Secchi depths in any water, and
anywhere from 1.01 to 1.67 across Poole & Atkins's range.

**Fixed.** The example's docstring said most of both Duarte papers'
attenuation coefficients came from Secchi depths. Duarte (1991) does not
say how many of his did; the docstring now says what each paper says.

## 0.19.2 — 2026-10-24

**Packaging.** The release workflow now makes the GitHub Release itself,
with the version's section of CHANGELOG.md as its text, and only after
PyPI has the version (DECISIONS.md section 51). Zenodo archives the
Release, so a version can no longer reach Zenodo without reaching PyPI, as
0.19.0 did. The workflow is run from the Actions tab on main, takes the
version from `pyproject.toml` and makes the tag; pushing a tag still runs
it, and a Release that already exists is left as it is.
`tools/release_notes.py` prints the text, and a version without a section
in CHANGELOG.md stops the run before anything is uploaded. Nothing in the
package, the data or the examples changed.

## 0.19.1 — 2026-10-24

**Packaging.** 0.19.0 did not reach PyPI. The release workflow runs the
tests against the installed wheel, from a copy of `tests/` away from the
source tree, where the tests that need the examples are skipped. Two tests
added in 0.19.0 for `wave_focusing.py`'s sky needed the example but were
not marked as needing the source tree, so they failed there and the
upload never ran. They are marked now. CI's test job now also runs the
tests from such a copy on every push, so that this is found before a tag
rather than at it. Nothing in the package, the data or the examples
changed from 0.19.0; its tag stays, and it is not on PyPI.

## 0.19.0 — 2026-10-24

The rest of Gernez & Antoine's (2009) figures that carry measurements, and
the sky's light in `wave_focusing.py`. No shipped value changed; four data
files are added.

**Added.**

- `gernez2009_cv_by(variable, sky=..., irradiance=...)`: besides the clear
  sky and Ed of Figure 8, the overcast subset (Figure 7) and the upwelling
  irradiance Eu under clear skies (Figure 13), each against the sun's
  zenith angle, the wave height, the wind speed and Kd(490).
  `GERNEZ2009_PLOTS` gives the variables for each. `ConditionFluctuation`
  carries the figure and the irradiance.
- `gernez2009_spectral_cv(irradiance)`: the average CV and period of the
  strongest fluctuation at 412 to 683 nm under clear and overcast skies, of
  Ed at the upper depth (Figure 11) or Eu at the lower, 8 to 8.7 m (Figure
  14), as a `SkySpectralFluctuation`.
- `gernez2009_band_cv(variable)`: the median CV of Ed at 443 to 683 nm,
  clear skies, against the sun's zenith angle, the wave height, the wind
  speed or Kd(490) (Figure 10), as a `BandConditionFluctuation`; its 510
  nm line is Figure 8's medians to within 0.2 percent. The periods, drawn
  in the same colours and crossing the CV lines, are not read.
- `gernez2009_diffuse_share()`: the share of diffuse light above the water
  that the paper prints along the top of Figures 8a and 10a, from 21
  percent with the sun at 20 degrees to 100 at the horizon. It comes from
  a model of the sky (Gregg and Carder, 1990), not a measurement.

**Examples.** `wave_focusing.py` adds the sky's light (DECISIONS.md
section 48, written before the run): its share above the sea from the
clear-sky model of Gregg and Carder (1990), checked against the shares
Gernez and Antoine print, for eight atmospheres since Darecki did not
record one, and its light under the waves taken as uniform. Every
atmosphere passes section 44's checks. Below 2.84 m measured / model,
0.54-0.77 without a sky, becomes 0.64-0.88 with the smallest share and
0.86-1.20 with the largest, which lowers the model too far near the
surface (1.16-1.87 down to 2.84 m): the sky accounts for part of the
shortfall, and no one uniform sky fits every depth. Section 45's model
without a sky is printed as before.

**CI.** The examples run in a job of their own, beside the tests rather
than after them, on the same versions and with the same commands
(DECISIONS.md section 49): every check still runs, and a run should take
about 8 minutes rather than 11. A test checks that the two jobs cover the
same versions.

**Docs.** DATA.md section 25: how they were read, and where the text and
the figures differ. Figure 14's text gives its two Tmax curves the
opposite skies from the figure's own labels and caption; the values follow
the figure. Figure 8's caption calls the top axis the ratio of direct to
total light; the axis label, Ediffuse / Etotal, and the numbers say
diffuse.

## 0.18.2 — 2026-10-23

**Packaging.** CI ran `wave_focusing.py` twice in every job, once in the
loop over the examples and once in the test that recomputes its quoted
numbers, which took each job from about six minutes to about fifteen. The
loop now skips it, and the test runs it with `ProvenanceWarning` an error,
as the loop does (DECISIONS.md section 47). Nothing in the package or the
examples changed.

## 0.18.1 — 2026-10-23

**Examples.** `wave_focusing.py --png` draws the light shafts seen looking
up towards the sun from 6 m at 532 nm: the unscattered sunbeam under the
5.5 m/s sea, scattered once towards the eye by Petzold's volume scattering
function, beside the same under a flat surface and the one divided by
the other, where the shafts spread from the sun across the whole field.
No value printed without `--png` changed.

**Docs.** DECISIONS.md section 46.

## 0.18.0 — 2026-10-23

A model of the flicker under waves, as an example, checked against the
measurement the package carries. No shipped value changed.

**Examples.** `wave_focusing.py`, for anyone working with the light just
below a sunlit sea. It draws a random sea surface from the wave spectrum
of Elfouhaily et al. (1997), with the friction velocity from Wu (1982),
traces the refracted sunbeam down to Darecki et al.'s (2011) six depths,
blurs it by the sun's disc and their 2.5 mm collector, and compares the
coefficient of variation with `darecki2011_irradiance_cv()`, using the
water You et al. (2010) measured on the same day. The surface's mean
square slope agrees with Cox and Munk (1954). The checks were written
down before the run (DECISIONS.md section 44). With the scattered light
spread evenly, the measurement is 1.5 to 2.7 times the model down to
2.84 m, and the third check fails. Looking for the cause (section 45):
light scattered on its way down still carries the pattern, shifted, and
with that the model passes all three checks, the measurement 0.69 to
1.24 times it down to 2.84 m and 0.54 to 0.77 below, where the model
leaves out the sky. Petzold's NUC 2240 phase function brings the deeper
values to 0.78 to 0.97; a smaller square or a coarser grid moves the
result by 5 percent at most. Takes about ten minutes.

**Docs.** DECISIONS.md sections 44 and 45.

## 0.17.0 — 2026-10-21

The rest of the two fluctuation studies' figures. No shipped value
changed; two data files are added.

**Added.**

- `darecki2011_spectral_cv()`: the coefficient of variation of the
  downwelling irradiance at about 1 m, at 410, 443, 488, 532, 610 and
  670 nm, on five days with winds from 3.9 to 10.3 m/s (Darecki et al.
  2011, Figure 13b), as a `SpectralFluctuation` with each day's date and
  time. Read from the figure's drawing commands, like 13a and 15.
- `gernez2009_cv_by(variable)`: under clear skies at about 3 m, the
  coefficient of variation of the downwelling irradiance at 510 nm, its
  standard deviation and the period of the strongest fluctuation, against
  the wave height, the square root of the wind speed or Kd(490) (Gernez &
  Antoine 2009, Figures 8b-8d), as a `ConditionFluctuation`;
  `GERNEZ2009_VARIABLES` names the three. Read from the figure's pixels.
  Where a bar cannot be told from the other series', its standard
  deviation is nan.

**Fixed.** The values of `gernez2009_cv_by_sun_zenith()` are the medians
of each class, as the caption of the paper's Figure 7 says for Figure 8;
0.16.0 called them means in its docstrings, in DATA.md section 25 and in
the build script. The numbers are unchanged.

**Docs.** DATA.md sections 24 and 25: the new readings, and where the
paper's text and its figure differ (CV "from 30%" with Kd(490), where the
figure's largest is 24 percent; the wind of the shortest period; the depth
of the upper radiometers).

## 0.16.1 — 2026-10-21

The package's type annotations and its source are now checked in CI. No
shipped value changed, and no code changed what it does.

**Fixed.**

- Two annotations said less than the code returns. `Descent.transmittance`
  is a float when the wavelength asked for is a scalar, as every other
  wavelength-indexed result is, but was annotated as an array; so was the
  internal interpolation behind `Water.a`, `b`, `c` and `kd`. The table of
  Figure 15's conditions behind `darecki2011_radiance_cv` is annotated so
  that its mixed values type-check.
- Unused imports in `examples/isolumes.py`,
  `tests/test_reproduces_papers.py` and one build script, and f-strings
  with nothing to format in four examples and a build script. The
  examples' output is unchanged.

**Changed.** Lines in `jerlov/` longer than 79 characters are wrapped.
The text of every message and docstring is unchanged apart from where its
lines break.

**Packaging.**

- A new CI job runs `ruff check .` and `mypy` on the package, at pinned
  versions (ruff 0.15.20, mypy 1.20.2), configured in `pyproject.toml`.
- `actions/checkout` v4 → v5, `actions/setup-python` v5 → v6,
  `actions/upload-artifact` v4 → v6 and `actions/download-artifact`
  v4 → v7, the first versions of each that run on Node.js 24; GitHub
  warned that Node.js 20 is deprecated. The artifact is downloaded by name,
  whose behaviour none of these versions changed.
- The build scripts' imports were split one to a line. Rerunning every
  script reproduces every shipped CSV byte for byte.

**Docs.** DECISIONS.md section 43; CONTRIBUTING.md.

## 0.16.0 — 2026-10-18

The fluctuations of the light under a wavy surface, as two field studies
measured them, read from their figures. No shipped value changed; three
data files are added.

**Added.**

- `darecki2011_irradiance_cv()`: the coefficient of variation of the
  downwelling irradiance, sampled at 1 kHz with a 2.5 mm collector, at six
  depths from 0.86 to 9.58 m and at 443, 532 and 670 nm (Darecki,
  Stramski & Sokolski 2011, Figure 13a), as an `IrradianceFluctuation`
  with the conditions the caption gives.
- `darecki2011_radiance_cv(panel)`: the coefficient of variation of the
  radiance at 532 nm at thirteen zenith angles in the plane of the sun, on
  the three occasions of their Figure 15, as a `RadianceFluctuation`;
  `DARECKI2011_PANELS` names them.
- `gernez2009_cv_by_sun_zenith()`: under clear skies at about 3 m, the
  coefficient of variation of the downwelling irradiance at 510 nm, its
  standard deviation, and the period of the strongest fluctuation, from
  20 to 85 degrees of sun zenith angle (Gernez & Antoine 2009, Figure 8a),
  as a `SunZenithFluctuation`.
- A status, `read_from_figure`, which every value in the three files
  carries.

**How they were read.** Darecki et al.'s figures are vector graphics, and
each marker's coordinates were taken from the PDF's drawing commands;
Gernez & Antoine's is an image, read to the pixel. Both build scripts,
`tools/build_darecki2011.py` and `tools/build_gernez2009.py`, carry the
coordinates as literals, calibrate on the axes' tick marks, and check the
values against what the papers say in words. The accessors carry the
precision of the reading.

**Docs.** DATA.md sections 24 and 25: the readings, their precision, the
conditions, and Gernez & Antoine's equation (8), which as printed does not
give 1 at zero wind and is not shipped. DECISIONS.md section 42: values
read from figures are allowed under stated conditions, and the package
ships the measurements, not a model of the fluctuations.

## 0.15.2 — 2026-10-18

The painted sphere under an overcast, with a gloss coat, and with its
shadow. No code or shipped value changed.

**Examples.** `painted_sphere.py` gains three parts.

- An overcast sky: the same Monte Carlo with a uniformly bright sky in
  place of the sun. The two horizontal views come together, the grey
  sphere 2.17 and 2.19 times the water against 0.92 and 6.46 under the
  sun; it is still 11.9 times the water from above and 0.34 from below.
- Gloss: a clear coat of refractive index 1.5, reflecting by Fresnel's
  equations the scattered light it mirrors, interpolated between the
  Monte Carlo's cells. It reflects 0.32 percent looking straight at it
  from water, against 4.0 from air, and changes the grey sphere's mean
  luminance by at most 8.9 percent, seen from below; its brightest point
  mirrors light within 9 degrees of the sunbeam from every direction.
- The shadow: a sphere 0.2 m across keeps the sunbeam from the water
  behind it, and the light that beam would have scattered once towards
  the eye is taken away. From none of the four directions does it show:
  the water in it is at most 0.4 percent darker.
- The picture holds the sun and the overcast, with the coat and, under
  the sun, the shadow. It takes about two minutes.

## 0.15.1 — 2026-10-18

The search for why the Monte Carlo example differs from Tyler's lake, one
correction to that example's engine, and an example that lights a painted
sphere and looks at it from four directions. No code or shipped value
changed.

**Fixed.** In `radiance_distribution.py`, turning a direction exactly
straight up or down by a scattering angle left it unturned: the test for
that case could never be true. No photon in the example starts exactly
vertical, and no printed figure changed.

**Examples.** `radiance_distribution.py` part 7 changes one thing at a time
from part 6, as set down before the runs (DECISIONS.md section 40):

- c at depth, 0.377 1/m, moves the model's mean cosine further from
  Tyler's, to 0.773.
- Petzold's eight phase functions give mean cosines of 0.710 to 0.767.
  HAOCE 11 and HAOCE 5, chosen in part 6 for being nearest in b, have the
  two lowest backscatter ratios and the two highest mean cosines; with
  AUTEC 8, NUC 2200 or NUC 2040 the model comes within 0.002 of Tyler's
  mean cosine and 0.007 of his E0 / Ed.
- Holding HAOCE 5, b = 0.48 1/m (c = 0.60, 1.5 times the report's) gives
  Tyler's mean cosine, and Eu / Ed, E0 / Ed and the radiance near the
  horizontal then come close to his without being fitted.
- The figures compared do not tell a different phase function from a
  larger b. The example now takes about two minutes.

`painted_sphere.py`, for anyone rendering, photographing or designing
objects seen under water: a sphere in four stand-in paints, 10 m deep in
Jerlov II, seen 2 m away from above, from below, and horizontally towards
and away from the sun (DECISIONS.md section 41).

- Every face receives the radiance from the directions it faces, from the
  Monte Carlo of `radiance_distribution.py`, copied into the script so
  that it runs alone, and the sunbeam if it faces the sun. A face turned
  up receives the Ed the Monte Carlo counts directly within 2 percent.
- Between the sphere and the eye the water thins its light by exp(-c r)
  and adds the background's radiance at the eye less its radiance at the
  sphere, thinned the same way; looking horizontally that is
  `Scene.observe`, which a test confirms.
- The grey sphere is 14.5 times as bright as the water seen from above and
  0.42 times seen from below. The four paints are 7.0 times apart from
  above and 1.06 from below.
- AUTEC 7's phase function in place of HAOCE 11's moves the grey sphere by
  32 percent with the sun behind and 26 percent from above, the two
  directions whose background is light scattered back.
- `--png` writes the picture, 160 pixels to a sphere with its edge
  smoothed, four paints down and, across, each paint in air under daylight
  followed by the four directions, with nothing beyond the standard
  library and NumPy. It takes about a minute.

**Tests.** The engine against the exact asymptotic light field of
isotropic scattering, within 3 percent at single-scattering albedos 0.72
and 0.9 and 6 percent at 0.5; the turn, at every direction. The two
copies of the Monte Carlo are held identical; the sphere example's colour
shortcut matches `spectrum_to_srgb`.

**Docs.** DECISIONS.md sections 40 and 41.

## 0.15.0 — 2026-10-17

Tyler's (1958) measured radiance distribution, shipped, and the Monte
Carlo example compared with it. No shipped value changed; one data file
is added.

**Added.** `tyler1958_radiance(depth_m)`, the radiance from every
direction that Tyler measured in Lake Pend Oreille, Idaho, at seven depths
from 4.24 to 66.1 m under a clear sky, as a `RadianceDistribution`: tilt
by 10 degrees, azimuth from the sun by 20, in his relative unit, with the
sun altitude, band, beam attenuation and acceptance angle the report
gives. `TYLER1958_DEPTHS` lists the depths; nothing is interpolated
between them. The nine cells the report gives reason to doubt, the sun's
direction where Table XI gives its glitter and one overstruck digit, are
flagged `suspect` and warn. `jerlov/data/tyler1958_radiance.csv` is built
by `tools/build_tyler1958.py`, which carries the 1330 values as printed
and checks them against each other.

**Examples.** `radiance_distribution.py` part 6 runs the model on the
lake, with every choice fixed before the run (DECISIONS.md section 39):
a = 0.1119 1/m from Tyler's three deepest tables by Gershun's law,
b = c - a = 0.2841, the phase functions of HAOCE 5 and HAOCE 11, the sun
alone and a uniform overcast, fresh water.

- The model's mean cosine is 0.762 to 0.774 against Tyler's 0.704 to
  0.715; Eu / Ed 0.0131 to 0.0151 against 0.0189 to 0.0233; E0 / Ed 1.27
  to 1.29 against 1.37 to 1.39; Kd 0.144 to 0.146 1/m against 0.163 and
  0.153.
- In the sun's plane, relative to overhead, Tyler's radiance lies between
  the two skies' at 5 and 25 degrees from the zenith and above both at 65
  and 85, where the model gives 0.28 to 0.90 of it.
- What causes the difference is not established, and the example lists
  what was not varied. It now takes about a minute.

**Docs.** DATA.md section 23: the measurement, the transcription and the
flags. DECISIONS.md section 39: the comparison's choices, including one
corrected before the run.

## 0.14.4 — 2026-10-17

An example that solves for the radiance distribution. No code or shipped
value changed.

**Examples.** `radiance_distribution.py`, for work that needs the light
arriving from each direction: a Monte Carlo solution of the radiative
transfer equation in about 150 lines of NumPy, in the example, from
the package's coefficients. The package still does not solve it
(DECISIONS.md section 38).

- Jerlov II, with Williamson & Hollins's (2022) a and b at 450, 500 and
  550 nm; the phase function of HAOCE 11, the Petzold station whose b is
  nearest II's at 530 nm, from his first measured angle, the 18 percent of
  the particles' scattering below it taken as unscattered; pure water's
  from `pure_water_vsf`. A sun 40 degrees from the zenith, and a uniform
  overcast.
- Gershun's law recovers the a put in to within 2 percent. Kd from 2 to 10
  m is within 6 percent of Jerlov's (1976) at 500 and 550 nm, and 20 to 24
  percent above it at 450.
- The radiance in the plane of the sun at four depths; the mean cosine;
  E0 / Ed, 1.24 to 1.37, the factor `par_profile` does not supply; Eu / Ed,
  which the next nearest station, AUTEC 7, raises by 48 percent at 10 m.
- It takes about half a minute, and its figures are recomputed in the
  tests.

**Docs.** DECISIONS.md section 38: why an example may solve what the
package does not.

## 0.14.3 — 2026-10-15

The examples no longer silence warnings they do not explain. No code or
shipped value changed; one example prints two more lines under each of two
tables.

**Fixed.**

- `synthetic_underwater_images.py` ignored every warning around its colour
  swatches. That hid a `CoverageWarning` on each of them, since the spectra
  stop at 412 nm where the CIE observer's blue channel still has 2 percent
  of its weight, and a `GamutWarning` on 25 of the 30 swatches balanced to
  the surface. It now catches only those two, by category, and says under
  each table how much of the observer was covered and how many swatches
  were clipped.
- `from_one_measurement.py`, `measured_scattering.py`, `sources_disagree.py`
  and `synthetic_underwater_images.py` ignored `ProvenanceWarning` in six
  places, and `from_one_measurement.py` every warning in one more, where
  nothing raised one. They are removed, so a flag added later reaches the
  reader. These examples' output is unchanged.

**Packaging.** CI now runs every example with `ProvenanceWarning` as an
error, as the local pre-push checks did. A test refuses an example that
ignores every warning.

**Docs.** DECISIONS.md section 37.

## 0.14.2 — 2026-10-15

An example that silenced a warning it had no need to raise. No code,
shipped value or printed figure changed.

**Fixed.** `what_an_eye_sees.py` built a `Scene` at each depth only to read
its downwelling irradiance. `Scene` evaluates the beam attenuation c of the
default IOPs, which for Jerlov II is extrapolated by their model at 350 to
410 nm and raises a `ProvenanceWarning`; the example caught and ignored
it, though it never uses c. It now computes `Ed(0) exp(-Kd z)` from Austin &
Petzold's (1986) Kd directly, which raises nothing, and no longer catches
any `ProvenanceWarning`. Its output is the same, character for character.

## 0.14.1 — 2026-10-15

An example that counted energy where it should have counted photons, and
three figures in it that were not tested. No code or shipped value changed.

**Fixed.** `what_an_eye_sees.py`:

- Photoreceptors absorb photons and camera pixels count them, but the
  example integrated its receptor and camera curves against the energy
  spectrum. It now converts to photons first. This changes the figures in
  parts 2 and 3: the S cone's surface catch is 46 percent of the largest,
  not 57, and the L and M cones now tie at the surface, within 0.1 percent,
  where counted as energy the M cone led. The 480 nm rod is still ahead at
  20 and 50 m. Part 2 now shows the energy figure beside the photon one.
- The red-to-blue ratio of the camera was said to change "by two orders of
  magnitude" over 50 m. It falls by a factor of 25 counted as energy and 29
  counted as photons.
- "By 50 m almost everything left is between 450 and 550 nm": it is 76
  percent of the photons.
- The example said the reversal with depth "is why deep-sea fish rod
  pigments cluster near 480 nm". That is a claim about evolution the
  package does not test, and it is removed.
- Every figure the example prints is now computed in the text and
  recomputed in `tests/test_quoted_figures.py`; none of them was before.

## 0.14.0 — 2026-10-15

A weight for each photon, for PUR, visual pigments and sensors. No shipped
value changed, and no existing figure in an example changed.

**Added.**

- `par_profile(..., photon_weight=...)`: weights each photon by its
  wavelength, on the given wavelengths, before integrating. `par`, the
  fractions, `depth_of_fraction` and `kd_par` then follow the weighted flux;
  `spectrum_at` stays the unweighted light. A weight of 1 is PAR. The
  weight must be finite and not negative inside the band, and a gap there
  raises `MissingQuantityError`; outside the band it is not read.
  `ParProfile.weighted` says whether one was given, and the repr says so.

**Examples.** `isolumes.py` has a new part 5: isolumes for three rods
rather than for PAR, as Gaussians at the peaks `what_an_eye_sees.py` uses.
A thousandth of the 480 nm rod's surface catch lies 26 m below PAR's in
Jerlov I and 13 m in II. In 1C the 500 and 530 nm rods are within 0.02 m of
each other and both below the 480 nm one, where the light left peaks at
530 nm rather than 475 nm.

**Docs.** DECISIONS.md section 36; the README mentions the argument.

## 0.13.0 — 2026-10-15

The spectrum at any depth, and Kd(PAR) between two depths. No shipped value
changed, and no example's output changed.

**Added.**

- `ParProfile.kd_par(z1, z2)`: the effective Kd of PAR between two depths,
  `ln(PAR(z1) / PAR(z2)) / (z2 - z1)`, in 1/m; over another band, the same
  for that band.
- `ParProfile.spectrum_at(z)`: the downwelling spectrum at a depth, or one
  row per depth, in umol photons m-2 s-1 nm-1, on the new
  `ParProfile.wavelengths_nm`, the grid PAR is integrated over. Integrating
  it gives `par`.
- Both refuse a depth below the bottom of a descent, a negative one, NaN
  and inf; `kd_par` also refuses `z1 >= z2` and a depth with no light.

**Changed.** `seagrass_depth_limit.py` takes its top-metre and whole-column
Kd(PAR) from `kd_par`, and `isolumes.py` the colour of the light at each
isolume from `spectrum_at`, instead of computing them by hand. Their output
is the same.

**Docs.** DECISIONS.md section 35; the README shows both.

## 0.12.1 — 2026-10-15

An example for ultraviolet light under water. No code or shipped value
changed.

**Examples.** `ultraviolet.py`, for work on ultraviolet exposure under
water: reefs, plankton and larvae near the surface, photochemistry. It
integrates UV-A, 315-400 nm as the CIE defines it, and PAR with
`par_profile(..., band=)`, layer by layer through `descend`.

- Jerlov's (1976) Kd covers UV-A for 8 of the 10 types. 7C and 9C have no
  Kd below 350 nm, and are left out rather than filled in. UV-B is not
  covered for any type.
- UV-A reaches 0.61 to 0.76 of PAR's 1 percent depth in the oceanic types
  and 0.22 to 0.25 in the coastal ones. The step is between III and 1C:
  the clearest UV-A is 1.6 times as attenuated as the clearest PAR in III,
  and 4.2 times in 1C.
- Where PAR is down to 10 percent, 3.3 to 7.0 percent of the surface UV-A
  is left in the oceanic types, and 0.04 to 0.05 percent in the coastal
  ones.

The READMEs count fourteen examples; the figures quoted are tested.

## 0.12.0 — 2026-10-15

`face_irradiance_ratio` is required. No shipped value changed, and no
example's output changed.

**Changed.**

- `Scene.observe` raises `MissingQuantityError` when `face_irradiance_ratio`
  is left out, instead of taking it as 1 with a `FutureWarning` as 0.11.0
  did. The message says what the ratio is and that 1.0 is what earlier
  releases assumed. Code that passed it in 0.11.0 is unaffected; code that
  relied on the warning's default must now pass 1.0 to get the same
  results. DECISIONS.md section 34.

## 0.11.0 — 2026-10-15

The light falling on a target's visible face is stated rather than assumed.
No shipped value changed, and no example's output changed.

**Added.**

- `Scene.observe(..., face_irradiance_ratio=...)`: the irradiance on the
  face of the target the observer sees, divided by the downwelling
  irradiance, as a number or an array on the scene's wavelengths. It scales
  the target's radiance and nothing else; the veiling light is unchanged.

**Changed.**

- Leaving `face_irradiance_ratio` out takes it as 1, a face turned
  straight up, as every earlier release did without saying so, and now
  warns with `FutureWarning`. A later release will require it. DECISIONS.md
  section 33.
- `lure_colours.py` passes its share of the light on the lure's side as
  `face_irradiance_ratio` instead of scaling the downwelling irradiance
  before building the scene; the output is the same.
- `from_one_measurement.py`, `measured_scattering.py` and
  `synthetic_underwater_images.py` pass 1.0, which keeps their output, and
  list it among their assumptions.

**Docs.** DECISIONS.md section 33; the README and the `jerlov.scene`
docstring describe the argument.

## 0.10.0 — 2026-10-15

PAR over another band. No shipped value changed; one figure an example
printed was off by a rounding, and is corrected.

**Added.**

- `par_profile(..., band=(lo, hi))`: the photon flux over any band, not
  only PAR's 400-700 nm, which stays the default. The ends are
  interpolated, and nothing outside the band is read, as before.
  `ParProfile.band_nm` records the band, and the repr names it when it is
  not 400-700 nm. `band=jerlov.QUANTA_BAND_NM` integrates over the band of
  Jerlov's quanta meters.

**Fixed.**

- `euphotic_zone.py` took the share of each colour of PAR by zeroing the
  surface spectrum outside it, which divided the light near each boundary
  between the two colours by a ramp rather than at the boundary. With
  `band=` each share is the integral over its colour, and violet-blue at
  the 1 percent depth is 88 percent, not 87.

**Changed.**

- `euphotic_zone.py` section 4 now compares with Jerlov's quanta tables
  over his own band, 350-700 nm, rather than over PAR's: within 1.8
  percentage points down to 10 m, and the 1 percent level at 100 m
  against his 87, 15 percent deeper, as DATA.md section 22 has it. Over
  PAR's band it was 101 m; the band is not what separates them.
- `tests/test_quanta.py` uses `band=` instead of integrating by hand.

**Docs.** DECISIONS.md section 32: why the band has a default when the
unit has none, and why the result is still called `par`.

## 0.9.6 — 2026-10-15

The euphotic-zone example checked against a measurement, and the year of
Jerlov's quanta paper settled. No code or shipped value changed.

**Examples.** `euphotic_zone.py` has a new section 4, which sets its PAR
profile beside the quanta irradiance Jerlov measured in water of the same
type, IA, using `jerlov1977_quanta`. Down to 10 m they agree within 3.1
percentage points; below, the computed profile keeps more of the light,
1.6 times as much at 80 m, and puts the 1 percent level at 101 m against
the measured 87. The example used to say that nothing in it had been
compared with a measured profile. The one `ProvenanceWarning` that IA
raises, for a Table 5 coefficient the example does not use, is caught and
printed rather than left to the caller.

**Docs.** 0.9.4 recorded that the pages of Jerlov's "Classification of sea
water in terms of quanta irradiance" print no year, and DATA.md section 16
gave 1977 as Woźniak & Pelevin's. The publisher's record settles it:
*Journal du Conseil* 37(3), September 1977, doi:10.1093/icesjms/37.3.281.
DATA.md sections 16 and 22, the docstring of `jerlov1977_quanta` and
`tools/build_jerlov1977.py` now say so. Rerunning every build script leaves
the shipped tables byte for byte as they were.

## 0.9.5 — 2026-10-09

An example for painted gear, and a DOI that was missing. No code or shipped
value changed.

**Examples.** `lure_colours.py`, for designing or testing painted fishing
lures and other gear: six finishes seen horizontally through 0.5 to 5 m of
water, as colour swatches and luminance contrast against the open water.
The first column of swatches is the paint in air, under daylight, for
reference. `--png PATH` also writes the swatches as an image, with nothing
beyond the standard library and NumPy.

It separates what the water decides from what it does not. At each
wavelength the contrast left at range r is exp(-c r), whatever the lure and
whatever the water's glow. Where the contrast starts is another matter: it
rests on the light falling on the lure's visible side and on the water's
backscatter ratio, neither of which the Jerlov type fixes. Across three
guesses at the first and two at the second, the same finish in Jerlov 1C
starts anywhere across a factor of 124, and three finishes change sign. The
example shows that table rather than ranking finishes by one guess.

**Metadata.** Jerlov's "Classification of sea water in terms of quanta
irradiance", the source of `jerlov1977_quanta.csv` since 0.9.4, is now in
the Zenodo record's related identifiers, doi:10.1093/icesjms/37.3.281, and
the DOI is in DATA.md section 22, the build script and the docstring.

## 0.9.4 — 2026-10-09

Jerlov's measured quanta irradiance, shipped and used as a check on the
package. No existing shipped value changed.

**Added.**

- `jerlov1977_quanta(water_type)` and `QuantaLevels`: Jerlov's tables of
  quanta irradiance, 350-700 nm, measured at stations in fourteen regions,
  for types I, IA, IB, II, III, 1C and 3C. Table 2, the depths of 30, 10, 3
  and 1 percent of the surface quanta; Table 3, the percentage at depth;
  Table 5, Kd for quanta layer by layer. `QUANTA_BAND_NM` is the band.
- `jerlov1977_quanta.csv`, all four of the paper's tables, transcribed by
  `tools/build_jerlov1977.py` from the page images, since the scan's text
  layer reads decimal points as hyphens.

**Found.** DATA.md section 22.

- The tables do not all follow from each other. Allowing for the rounding
  of every printed value, eight values fall outside what the tables they
  derive from give. Seven are near misses. Table 5's Kd for II at 5-10 m,
  0.099, cannot come from Table 3, which gives 0.076 to 0.086. All eight
  are shipped as printed and marked `suspect`; the three that
  `jerlov1977_quanta` returns warn.
- Against the measurements, the package agrees within 2 m at every level
  from II to 3C. For Jerlov I one Kd puts the 1 percent level at 165 m
  against a measured 103; through `descend` it is 106, which is independent
  support for the depth profile. IA and IB stay 15 and 33 percent too deep:
  Jerlov's own IB water grew more turbid below 15 m, which the profile of
  Williamson & Hollins (2023) does not show. Why is unresolved.

**Docs.** DATA.md section 16 no longer says this paper was not obtained,
and records that its pages print no year. DECISIONS.md section 31 says why
checking against a published measurement is in scope when experimental
validation is not. The Zenodo description now counts twenty-two entries,
nine of them confirmed defects, and mentions the quanta tables.

## 0.9.3 — 2026-10-09

Small additions that the examples were working around, and checks on
publishing. No shipped value changed.

**Added.**

- `profile_depth(water_type)`: how deep `descend` can go below a surface
  type, the top of the first layer Williamson & Hollins (2023) declared no
  type for, or 200 m. Three examples found this by trying `descend` every
  10 m.
- `Descent.transmittance_at(z)`: `Ed(z) / Ed(0)` at any depth down to the
  descent's own, from the layers already crossed, for one depth or an
  array of them. `par_profile` now uses the same layers rather than
  looking each type's Kd up again. A `Descent` built by hand, which
  carries no layer Kd, is refused by both rather than treated as clear
  water.
- `classify_kd(..., types=...)`: compare with some of a source's types
  only. A wavelength is left out wherever any compared type has no Kd, so
  leaving out Solonenko & Mobley's 3C and 5C keeps 600-700 nm for an
  oceanic measurement.

**Fixed.** `tests/test_petzold.py` read Petzold's table from the source
tree rather than from the installed package, so it failed against a wheel.
It reads it through `importlib.resources`, and a test refuses the pattern.

**Packaging.**

- Publishing now stops if the tag is not the version in `pyproject.toml`.
- Publishing runs the whole test suite against the installed wheel, from a
  directory with no source tree beside it, before uploading. Doing that
  for the first time found the test above.

**Metadata.** The keywords in `.zenodo.json` and `CITATION.cff` drop
"underwater visibility", which the README says this package does not
predict, and add "diffuse attenuation coefficient", "photosynthetically
available radiation" and "euphotic zone". DECISIONS.md section 30.

**Examples.** `light_at_depth.py`, `seagrass_depth_limit.py` and
`isolumes.py` use `profile_depth` and `transmittance_at`. Their output is
unchanged.

## 0.9.2 — 2026-10-09

Three examples, each for a field the others did not reach. No code or
shipped value changed.

**Examples.**

- `optical_link.py`, for underwater optical communication and lidar: beam
  attenuation at laser lines, the range a loss budget buys, how far the two
  published IOP sets disagree on it (a factor of 2.9 at 532 nm, Jerlov III),
  Petzold's measured waters, and the narrow-beam lidar depth. What a wide
  receiver gains from scattered light is stated and not computed.
- `seagrass_depth_limit.py`, for coastal ecology and restoration: the depth
  at which the bottom receives 25, 11 or 5 percent of the surface PAR, the
  higher requirement Duarte et al. (2007) found in turbid water, the depth
  lost per step along the coastal scale, and why a Kd(PAR) from the top
  metre puts the limit too shallow. The light requirements are quoted from
  the four primary papers, with pages and DOIs: Duarte (1991), Dennison et
  al. (1993), Kenworthy & Haunert (1991) and Duarte et al. (2007). They are
  not checked here.
- `isolumes.py`, for vertical migration: where light levels from 1e-1 to
  1e-5 of the surface lie, how far each moves for a tenfold dimming, the
  colour of the light there, and oceanic against coastal water.

Every figure `examples/README.md` quotes from them is checked by
`tests/test_quoted_figures.py`.

## 0.9.1 — 2026-10-09

Fixes from a review of what 0.9.0 added, and an example for it. No shipped
value changed.

**Fixed.**

- `par_profile` evaluated Kd at every wavelength it was given, though PAR
  uses only 400 to 700 nm. A radiometer's 300-800 nm spectrum with Jerlov
  (1976), which stops at 715 nm, was refused, and Kd flagged at 705 nm
  warned about light PAR does not count. Kd is now evaluated only on the
  samples PAR rests on.
- `par_profile` let an infinite surface irradiance or Kd through, and
  returned inf or NaN with only a NumPy RuntimeWarning. Both are refused.
  With no light at the surface, `ParProfile.fraction` is NaN without a
  warning.
- `classify_kd` treated an infinite Kd as a gap and dropped it, leaving the
  other wavelengths to decide alone. It is refused.

**Examples.** `euphotic_zone.py`, for phytoplankton ecology: from one
Kd(490) reading to the nearest type, its depth profile, PAR wavelength by
wavelength, the 1 percent depth four ways, the colour of the light left at
the bottom, and three editions of the classification compared. A test now
keeps the count of examples in the two READMEs equal to the files.

## 0.9.0 — 2026-10-09

Three additions. No shipped value changed.

**Added.**

- `Scene.at_depth` takes the result of `descend` as `kd`, and builds the
  downwelling irradiance from its layer-by-layer transmittance. A descent
  to another depth, or on other wavelengths, is refused.
- `par_profile`: PAR, the photon flux from 400 to 700 nm, at any depths
  below a surface spectrum, each wavelength attenuated by its own Kd. `kd`
  is a `Water`, an array or a `Descent`. `ParProfile.depth_of_fraction`
  gives the depth at which PAR falls to a fraction of its surface value, 1
  percent by default. `unit` (`"energy"` or `"photons"`) has no default.
  This is planar PAR, from Ed.
- `classify_kd`: ranks the Jerlov types of one source by their distance
  from a measured Kd spectrum, the root mean square of ln(measured / type).
  The result names the nearest type, gives every distance, says when the
  measurement is clearer or more turbid than every type, and records the
  wavelengths it left out. Flagged reference values give one
  `ProvenanceWarning`, not one per type.

**Examples.** `light_at_depth.py` adds PAR and its 1 percent depth, and
builds its scene with `Scene.at_depth(kd=descent)`. `from_one_measurement.py`
uses `classify_kd` where it used to say there was none.

**Docs.** DECISIONS.md section 29 records the choices, including why the
example's "no classify(), deliberately" was answered rather than kept.

## 0.8.0 — 2026-10-09

Fixes from the review that followed 0.7.3. No shipped value changed.

**Changed.**

- The `plot` extra is gone. It installed matplotlib, which nothing in the
  package, its tests or its examples imports. `pip install "jerlov[plot]"`
  now installs plain `jerlov`, with a warning from pip that the extra does
  not exist. A test now fails if an extra installs something nothing
  imports.
- `Water` refuses flags for a quantity it does not carry. They used to be
  kept and never consulted, so `flags={"b": ...}` on a water with no b, or
  `"kd"` for `"Kd"`, dropped the caller's doubt without a word.
  `from_measurements` already refused this; the constructor now does too,
  as it already did for `uncertainty`.

**Added.**

- `water_type_at_depth` accepts an array of depths and returns an object
  array of the same shape, `None` where the paper declared no type. A
  single depth still gives a string or `None`. One NaN or negative depth
  refuses the whole array.

**Fixed.**

- The repr of a `Descent` printed every wavelength and transmittance. It
  now shows the path: `<Descent 1C to 45 m: 1C 0-20, III 20-40, II 40-45 m;
  Kd from jerlov1976; 301 wavelengths>`.

**Packaging.** The PyPI classifiers said "Pre-Alpha" and named no Python
version. They now say Beta, list Python 3.10 to 3.13, and mark the package
as typed. A test keeps the listed versions equal to the ones CI runs.

## 0.7.3 — 2026-10-07

**Fixed.** `ShortwaveParameters.fraction_at`, and so `solar_fraction`,
evaluated Paulson & Simpson's two exponentials at any depth without a word.
They were fitted to Jerlov's Table XXI in the upper 100 m, or 50 m for
`I_upper50`, as the paper's text says. Below that the result is
extrapolation, and it now raises a `ProvenanceWarning`. The values are
unchanged.

**Docs.** DECISIONS.md section 5, "No extrapolation", claimed more than the
package did. It now separates three cases:

- the package's own refusal to extrapolate;
- values that a source extrapolated, which are shipped, marked and warn;
- the axes that are not tables: the depth of a fitted formula, now warned
  about, and the wavelength of Morel's pure water formula, which is not
  range-checked.

The README's "will not extrapolate" says the same.

## 0.7.2 — 2026-10-07

Fixes from a review of the whole package. No shipped value changed.

**Fixed.**

- A NaN wavelength passed the range checks of `Water.a`, `b`, `c`, `kd`
  and `kd_hydrolight`, `kd_spectrum` and `b_from_c`, since `NaN < lo` is
  False. It came back as NaN, and `Water` warned about the last sample of
  the table, 800 nm or 715 nm, instead. It is now refused.
- `descend` froze the caller's wavelength array along with its own copy,
  so the caller could no longer write to it. It now copies first.
- `Scene` kept the caller's wavelength and downwelling arrays rather than
  copies. Changing them afterwards left the wavelengths out of step with
  c, which is evaluated once. It now copies them.
- The pure water scattering functions, and so `bb_from_vsf`, accepted a
  wavelength of zero or less and returned inf or NaN with only a NumPy
  RuntimeWarning. They now refuse it, as they already refused a bad
  salinity.

**Docs.** The README said the scattering coefficients of the two IOP sources
differ at 510 nm "by up to a factor of 2.6". The largest factor is 3.8, at
Jerlov III, as `examples/sources_disagree.py` already said. A test claimed to
check the README's figure but never read the README; one now does.

## 0.7.1 — 2026-10-07

Examples for what 0.6.0 and 0.7.0 added. No code or shipped value changed.

**Examples.** Three new scripts, and one extended; `examples/README.md` says
which to read.

- `light_at_depth.py`: `descend` through the typical depth profile. At 490
  nm and 60 m, Jerlov I receives a third less light than its surface Kd
  implies and 3C 530 times more; the 1 percent light level of I rises from
  197 to 133 m. It also shows where the profile runs out.
- `measured_scattering.py`: Petzold's eight stations, their B/S of 0.013 to
  0.044 and the shape of their phase functions, and what a measured ratio
  changes in a scene against a guessed one.
- `what_is_in_the_water.py`: a minus the pure water absorption the source
  built a on, the share of absorption that is the water, and the measured
  points behind it.
- `from_one_measurement.py` now marks a doubtful channel and attaches
  replicate uncertainties with `from_measurements(flags=, uncertainty=)`.

**Docs.** Writing the absorption example turned up something in the
Williamson & Hollins data, now in DATA.md section 20. The measured average a
at 715 nm is exactly 1.004 for 1C, 3C and 5C, with zero spread over 23, 28
and 6 campaigns. Identical values with no spread are not what independent
measurements give, and neither paper says why. The measured points lie 14
to 16 percent above the fitted a, which at 715 nm is pure water alone. Both
are shipped as published.

## 0.7.0 — 2026-10-07

**Added.** `petzold_scattering(station)`: the volume scattering functions
Petzold (1972) measured in eight ocean waters, from the Tongue of the Ocean,
Bahamas, to San Diego Harbor, at the report's 55 angles from 0.1 to 180
degrees and 530 nm, each with its c, b, a and backscatter ratio B/S. They are
shipped as `petzold1972_vsf.csv` and `petzold1972_stations.csv`, and
`PETZOLD_STATIONS` lists them clearest first.

- `vsf_at(angle)` interpolates in log-log within the table, and
  `phase_function()` is the vsf over b.
- `backscatter_ratio` is a measured bb/b, 0.013 to 0.044 across the eight,
  for `Water.bb` in place of a guess. It belongs to that water, not to a
  Jerlov type, and no station is mapped to one.
- Below 0.169 degree at the Bahamas and Catalina stations nothing was
  measured, and the report extended sigma with a power law. Those 15 values
  are `extrapolated` and warn.

Every value was read from the report's page images and compared with its
OCR text. `tools/build_petzold1972.py` carries them as literals and checks
them against the report's integrals, its second printing of sigma, its
summary pages and the smoothness of the curves. DATA.md section 21 and
DECISIONS.md section 27.

**Docs.** `tools/README.md` said two scripts need no input; seven do.

## 0.6.0 — 2026-10-07

**Added.**

- `pure_water_absorption(wavelength_nm, source="williamson2022")`: the
  absorption of pure water that the source built its a on, so that the part
  of a due to what is in the water is a minus this, from one source. Only
  Williamson & Hollins (2022) publish theirs, in their spreadsheet, 1 nm
  from 300 to 800 nm, now `williamson2022_aw.csv`. With it and their Table 6,
  their Eqs. (4)-(6) give back the shipped a to a median of 0.10-0.28
  percent, and `tools/build_williamson2022_aw.py` stops if that fails. From
  720 nm every type's a is this aw. Other sources raise
  `MissingQuantityError`, saying why: Solonenko & Mobley show theirs only as
  a figure, and the rest give Kd only. DATA.md section 20.
- `descend(surface_type, depth_m, wavelengths, source="jerlov1976")`:
  downwelling irradiance carried down through the typical profile of
  Williamson & Hollins (2023), each 10 m layer with the Kd of its own type.
  It returns the transmittance and the layers crossed, and stops with
  `MissingQuantityError` at a layer the paper declared no type for, rather
  than carrying the last type on. DECISIONS.md section 26.
- `Water.from_measurements(..., flags=..., uncertainty=...)`: a caller's own
  statuses, from the package's vocabulary, warn as published ones do; an
  unknown status is refused, so a misspelt one cannot silently never warn.
  Uncertainty is read back with `Water.uncertainty(quantity, wl)`.

**Fixed.**

- `Water.c` warned once for a and once for b, twice for a wavelength
  flagged in both. It now warns once, naming both.
- The pure water scattering functions accepted a negative or NaN salinity
  and returned a number. They now refuse it.
- `repr` of an `Observation` with no light anywhere raised a NumPy
  `RuntimeWarning`; it now says the veiling fraction is undefined.

**Not done.** Petzold's volume scattering functions are still planned. They
are to come from his report, SIO Ref. 72-78 (1972), which has not yet been
obtained.

## 0.5.2 — 2026-10-07

The two Dstl datasets behind five of the shipped tables were obtained and the
tables rebuilt from them: all five came out identical to the shipped files.
Doing so showed that one of them claims more than its source printed.

**Changed.** `jerlov1976_kd.csv` is at 1 nm from 300 to 715 nm, but Jerlov
(1976) Table XXVII has 16 wavelengths, 310 to 700 nm. The rest was filled in
by the Dstl dataset it comes through: 3672 values by linear interpolation
between printed wavelengths, and 230, at 300-309 and 701-715 nm, by linear
extrapolation from the two end values. All 4060 were marked `ok`, which
DATA.md defines as the published value. They are now `ok` (158, checked
against the table), `interpolated` and `extrapolated_by_dataset`, two new
statuses. The extrapolated ones raise a `ProvenanceWarning`, since the
package does not extrapolate; the interpolated ones do not. No value changed.

`tools/build_jerlov1976_and_solonenko2015.py` now carries Table XXVII as
printed and stops if the dataset departs from it, or stops being linear
between and beyond it.

**Docs.** The depth-profile dataset, figshare 21710252, is CC BY 4.0; its
download note said Open Government Licence, which is the 2022 dataset's. The
same script reported "19 layers from 0 to 200 m"; they are 10 to 200 m, below
the surface layer.

## 0.5.1 — 2026-10-07

Every paper this package draws on was read again against what it ships. No
shipped coefficient was wrong. Statements about the papers were, in several
places, and so was one of the checks.

**Checked against the papers.** All of: Jerlov (1968) Tables XX and XXI and
Jerlov (1976) Table XXVII; Austin & Petzold (1986) Tables IV and VI;
Solonenko & Mobley (2015) Tables 3 to 8, where the only cells that differ are
the duplicated rows already recorded; Williamson & Hollins (2022) Tables 3, 6
and 7, all 612 cells of the last; Williamson & Hollins (2023) Table 2;
Paulson & Simpson (1977) Table 2; Boss & Pegau (2001) Table 1 and Eqs. (4)
and (5); Smart (2007) Table 1; Haltrin (1999) Eqs. (4) to (7); and the
figures quoted from Austin & Petzold (1990), Hollins & Williamson (2023),
Oishi (1990), Maffione & Dana (1997), Woźniak & Pelevin (1991), Paglierani et
al. (2023), Jia et al. (2021) and Abd El-Mottaleb et al. (2024). DATA.md
records what was checked in each section.

**Fixed.** The check that Williamson & Hollins (2022) b follows from their
Eqs. (8)-(11) used the Table 6 of Hollins & Williamson (2023), a later refit
to the measured points, under the name of the 2022 table. With the 2022
table the agreement is 0.73 percent, not 5.3, and the build script and test
now require 1 percent. DATA.md had put the 5.3 down to a revision of Bl; the
cause was the wrong table. Only the check was affected.

The `williamson2022` source carried Haltrin's constants (0.005826, 1.151302,
0.341074) rather than the ones the paper prints and computed with (0.00583,
1.1513, 0.3411). The largest difference is 0.07 percent, in the pure water
term, and moves no result that matters; what it broke was the rule that a
source carries its own constants.

**Docs.** Statements the papers do not support, corrected:

- Boss & Pegau "made no measurement beyond 170 degrees": their instrument
  measured to 177.3; Table 1 stops at 170. In the error message, the CSV
  note, DATA.md, DECISIONS.md and an example.
- "Both papers recommend 110 to 160 degrees": that is Maffione & Dana. Boss
  & Pegau recommend near 117 degrees, or water removal from near 90 to 160.
- Paulson & Simpson excluded the 10 m point "because the two-exponential
  form does not capture the transition": the paper gives no reason.
- The spread of chi_p away from 170 degrees is 2.6 to 6.4 percent, not
  "3 to 6"; the test that pinned it checked only the upper end.
- DATA.md section 17 quoted Paglierani et al. about coefficients varying
  between works as if it concerned Jerlov types; it concerns Mobley's four.
- DATA.md section 13 said Williamson & Hollins (2023) do not say which three
  cells depart from their rule; they mark them with asterisks.

Added to the record: Jerlov (1968) Table XXI is for a solar altitude of 90
degrees (oceanic) and 45 (coastal), now in `jerlov1968_solar_fraction` and
DATA.md; the 8 percent accuracy of Austin & Petzold's model excludes 410 nm;
Hollins & Williamson (2023) Table 1 omits two a values that the 2022 paper's
own filter keeps, and this package follows the 2022 paper.

## 0.5.0 — 2026-10-06

Three tables that had been transcribed, checked against their papers and
shipped, but were reachable only through a private loader, now have public
entry points. No coefficient changed, and nothing existing behaves
differently.

**Added.** `water(t, source="jerlov1968")`: Kd from the first edition of the
classification, Jerlov (1968) Table XX, for all ten types from 310 to 700 nm.
It is also the Kd0 column of Solonenko & Mobley (2015), which reproduces it to
transcription accuracy. Its caveats say how far it is from the 1976 edition:
1 to 15 percent on average by type, up to 35 percent at single wavelengths.

`measured_points(t, quantity)`: the measured a and b points behind the
Williamson & Hollins (2022) spectra, with their standard deviation and the
number of campaigns behind each. Hollins & Williamson (2023) recommend these
over the fitted spectra for validation. The paper's own filter, five or more
campaigns, is applied unless `include_sparse=True`; Jerlov IA and 7C have no
point that passes it, and are refused rather than returned empty.

`jerlov1968_solar_fraction(t)`: Jerlov (1968) Table XXI, the broadband
irradiance with depth that Paulson & Simpson fitted, for all ten types. Blanks
stay NaN.

`pure_water_scattering(wavelength_nm)`: the total scattering coefficient of
pure sea water, from the same Morel formula as the rest of `backscattering`.
It is twice `pure_water_backscattering` by symmetry, and Morel's
`b_w = 16.06 beta_w(90)`, both checked. It is the `bw` that `b_from_c` asks
for, if that is what the c measurement was corrected with.

**Changed.** `examples/solar_heating.py` uses `jerlov1968_solar_fraction`
instead of the private loader; its output is unchanged. Tests now fail if a
shipped table is never read by the package, or if an example reaches into
`jerlov._data`.

`Water.kd_hydrolight(wl)`, for source `solonenko2015`: the paper's third Kd
column, K_d^H, which HydroLight computed from the retrieved a and b with the
Petzold average-particle phase function. It is the paper's check on its own
retrieval and a different quantity from `.kd()`, the Kd of its bio-optical
model. Its definition, from Section 4 and Appendix A of the paper, is now in
DATA.md section 19, with one finding: the paper says 90 percent of the points
in its Fig. 5 are within 20 percent of Jerlov's Kd, and the tabulated values
give 87 percent.

**Docs.** DATA.md has a nineteenth entry, so the count in DATA.md, the README
and `.zenodo.json` moves from eighteen to nineteen. The Solonenko & Mobley
caveat said only a is lost in the duplicated rows of Table 7; Kd and KdH are
lost there too.

The DOI of Paglierani et al. (2023) was given as `10.1155/2023.7185329`, which
resolves to nothing; it is `10.1155/2023/7185329`. It was wrong in DATA.md,
`sources/README.md` and `.zenodo.json`, so every Zenodo record from 0.2.2 on
carries the broken link in its related works; 0.5.0 will carry the right one.

## 0.4.1 — 2026-10-06

Inputs that used to slip past the package's own checks are now refused, and
two physically impossible results now say so. No coefficient changed, and
every valid call returns what it returned before.

**Fixed.** NaN passed every guard written as `value < 0`, since any comparison
with NaN is False. `Scene.observe` and `Scene.transmittance` with a NaN
distance, `Scene.at_depth` with a NaN depth, `attenuation_coefficients` with a
NaN in its range and `solar_fraction` with a NaN depth all returned results
made of NaN. They now raise. NaN inside a spectrum is still accepted, because
it marks a gap in the data, which the package keeps visible on purpose.

`Water` accepted NaN among its wavelengths, which passed the ascending check
for the same reason and broke interpolation afterwards. It also accepted
`flags` shorter than its wavelengths, which surfaced as `IndexError` only when
a value was asked for. Both are now refused when the `Water` is made.

`Scene.observe` and `attenuation_coefficients` accepted a negative veiling
radiance, and `veiling_radiance_estimate` a negative downwelling irradiance,
returning negative radiance. `Scene` itself already refused a negative
irradiance; all three now do.

`Scene.at_depth` given a surface spectrum of the wrong length failed inside
numpy with "operands could not be broadcast together"; it now names the
argument.

`b_from_c` with c below the pure water value cw returned a negative b without
comment. It now raises a `ProvenanceWarning`, as `kd_spectrum` already did in
the same situation.

**Changed.** `bb_from_vsf` warns of a reading below that of pure sea water
with a `ProvenanceWarning` rather than an `AngleWarning`. The angle is not
the problem, and a caller filtering out angle advice was silencing it too.

**Docs.** DECISIONS.md section 24 still listed the Akkaynak-Treibitz
coefficients as planned, though they arrived in 0.1.3, and section 12 still
listed `Scene` as planned and shortwave heating as out of scope, which
section 19 reversed. Both are annotated rather than rewritten, so the record
of each decision stays. The Solonenko & Mobley caveat said the Kd0 column is
not shipped; it is in the CSV, and what was meant is that `water()` does not
return it.

## 0.4.0 — 2026-10-06

Three calls that used to return an answer now raise instead, because the
answer was not one: hence 0.4 rather than 0.3.4. No coefficient changed.

**Changed.** `shortwave_parameters` refuses the three rows of Paulson &
Simpson's Table 2 that are not Jerlov types (the authors' composite
observations, their Run 1, and Kraus's Crater Lake value) unless called with
`include_non_types=True`. They used to come back like any type, so
`solar_fraction("run_1", 10.0)` gave a Jerlov-looking answer for one cruise.

**Fixed.** `water_type_at_depth` returned `None` for a NaN depth, which reads
as the paper declining to say; NaN and infinity now raise. 200 m, the bottom
of the paper's deepest layer, returned `None` as if beyond the profile; it now
belongs to the 190-200 m layer, since there is no layer below to own it.

`integrate_response`, and through it `spectrum_to_xyz` and `spectrum_to_srgb`,
integrated a spectrum given in descending wavelength order to a negative XYZ.
Both grids must now ascend.

**Docs.** `Observation.contrast` said the inherent contrast is reduced by the
transmittance. That holds only against a background as bright as the water's
own veiling light. Without veiling light the contrast is not reduced at all,
and against a darker background it falls faster than the transmittance. The
docstring now gives the formula and the three cases, and a test checks each.
The computation itself was right.

`integrate_response` now says how its accuracy depends on sampling. Moving
the integral onto the union of the two wavelength grids was tried and not
adopted: on five test spectra sampled at 25 nm it was better for a flat
spectrum and worse for the other four.

**Tools.** Three rebuild scripts printed their checks against the paper and
wrote the table whatever the checks said. `build_austin1986.py`,
`build_williamson2022_iop.py` and `build_williamson2022_measured.py` now stop
without writing when a check fails, as the others already did.

## 0.3.3 — 2026-10-05

**Fixed.** A `ProvenanceWarning` was raised for a wavelength that lands
exactly on a sound sample whenever the sample beside it was flagged:
`water("9C", source="jerlov1976").kd(350)` warned that 349 nm is missing,
though the answer at 350 nm rests on 350 nm alone. The NaN check has known
this since 0.2.1; the warning did not. Both now ask one function which
samples an answer rests on, so they cannot disagree again. The test suite,
which printed six such warnings, now prints none.

`kd_spectrum` given an array of Kd failed with numpy's "truth value of an
array is ambiguous". It now reconstructs one spectrum per measurement,
returning shape `kd.shape + at.shape`. Several measurement wavelengths are
refused with a message saying so.

**Added.** `kd_spectrum` warns when K(490), measured or implied by the
model, is not below 0.16 1/m, the limit Austin & Petzold give for their model.
It also warns when the answer rests on the values of M below 365 nm that the
paper itself flags as extrapolated. Both limits were stated in the docstring
and checked by nothing.

**Docs.** Error messages, docstrings and comments sent readers to "README
section 10" and the like. The README has no numbered sections; DATA.md does,
and every such reference now points there. The message raised by `Water.bb`
without a backscattering ratio, which every new user meets, was one of them.
A test now checks that every "DATA.md section N" cited in the code exists.

## 0.3.2 — 2026-10-01

**Fixed.** `b_from_c` given an array of c at a single wavelength returned
only the first element, silently. The shape of the answer was taken from the
wavelength alone; it now follows c and the wavelength together.

`pure_water_vsf` given one angle and several wavelengths returned the value at
the first wavelength only. Through it, `bb_from_vsf` with an array of
wavelengths subtracted the 450 nm water term from every reading, so its `bb`
and `particulate` were wrong at every wavelength but the first while `water`
looked right. Scalar calls, and every figure in the documentation, were not
affected.

`ProvenanceWarning` pointed at `water.py` rather than at the line that asked
for the value, and `CoverageWarning` and `GamutWarning` did the same when
reached through `spectrum_to_srgb`. A fixed `stacklevel` is right for one call
path only; warnings now point at the first frame outside the package.

The table loaders are cached, and `jerlov.water()` handed out the cached
arrays themselves. An in-place edit such as `w.wavelengths *= 2` changed the
table for every later caller in the process. The cached arrays are now
read-only, and `Water` copies what it is given, including a caller's own
measurements, which it previously shared.

## 0.3.1 — 2026-09-20

**Added.** `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, this changelog, and issue
templates. The contributing guide sets out what it takes to add a coefficient:
the paper itself rather than a table quoted from it, a script in `tools/` that
produces the table, checks inside that script against the paper's own
equations, an entry in `DATA.md`, and a regression test. It also says that a
coefficient disagreeing with a paper the reader has is the most useful report
this package can receive.

`py.typed`, so the annotations already in the package reach a caller's type
checker rather than being invisible to it.

`tests/test_quoted_figures.py` recomputes every figure the documentation
states: the factor of 3.8 between the two published scattering coefficients,
the 5.1 across three routes, the 46 percent by which the shortwave fit misses
its own source, the 34.8 percent spread at 170 degrees, the 116.9 degree
crossing, the 65 percent by which a guessed backscattering ratio overstates
contrast. Two of them read the number out of `README.md` and compare it
against the call printed beside it.

Those figures were each computed once and then written into prose, where
nothing was watching them. A reader cannot tell a stale number from a current
one, and the numbers are the reason to trust the package at all.

No coefficient and no function behaviour changed in this release.

## 0.3.0 — 2026-09-11

**Added.** `bb_from_vsf` converts a backscattering sensor's single-angle
reading into bb, following Boss & Pegau (2001). `Water.bb` still refuses to
guess a backscattering ratio, because the Jerlov classification still does not
determine one; what changed is that a caller with a HydroScat, an ECO-BB or a
VSF meter no longer has to.

The pure sea water half is analytic, so it is computed rather than
transcribed, and checked against the definition of bb: chi_w must give the
same bb_w at every angle and that value must equal the direct integral. Only
chi_p, resting on 41 measured scattering functions, is a table. Angles outside
90 to 170 degrees are refused, and 170 warns: its quoted spread is 34.8
percent against 3 to 6 in the middle.

Three examples, each aimed at a reader the existing two did not reach:
`from_one_measurement.py`, `solar_heating.py`, `what_an_eye_sees.py`. Before
these, half the public API appeared in no example at all.

**Changed.** `CoverageWarning` reports every channel rather than only the
worst. Integrating a 500-600 nm spectrum against the CIE 1931 observer used to
say "covers only 4.1%", which reads as if the whole observer were barely
covered; 4.1 percent is z-bar alone, and x-bar and y-bar are at 45 and 76.

**Fixed.** The NumPy compatibility shim moved from `colour.py` to `_data.py`.
It had been sitting in a module about colour, so two modules written
afterwards reached for `np.trapezoid` directly and broke the oldest supported
NumPy. A test now refuses the raw name anywhere in the repository.

**Data.** `boss2001_chi.csv`. `DATA.md` section 18 records that three
published values circulate for this conversion under two definitions differing
by 9 percent at 140 degrees, one including the water contribution and one not.

## 0.2.2 — 2026-09-10

**Added.** Examples became runnable scripts that CI executes on every push.

**Fixed.** Two examples made claims their own output contradicted: the
disagreement between the two published sources does not run in one direction,
and the depth-profile aside now finds the depth at which the water type
actually changes.

## 0.2.1 — 2026-09-10

**Fixed.** `kd(350)` for Jerlov 7C returned `nan` although 350 nm is
tabulated. The guard that stops interpolation bridging a gap was also firing
on queries that land exactly on a sample, which are not interpolated. Found by
checking the shipped 1976 table against the printed page cell by cell, which
had never been done before; 133 tests had not caught it.

**Data.** `DATA.md` gains two entries. Woźniak & Pelevin (1991) reprint
Jerlov's Kd spectra with the unit given as `[10⁻³ m⁻¹]` where the values are
in `10⁻² m⁻¹`, and with Jerlov IB at 700 nm printed as 59 where the original
has 58; read as published, Jerlov I at 475 nm comes out below the absorption
of pure sea water. Separately, a third route to a and b is in circulation —
assigning a chlorophyll concentration per Jerlov type — and at 532 nm the
three routes give beam attenuations differing by a factor of 5.1 for Jerlov
III. All three are peer reviewed.

## 0.2.0 — 2026-09-10

**Added.** `solar_fraction` and `shortwave_parameters`, the Paulson & Simpson
(1977) two-exponential parameters that ROMS, MITgcm, NEMO and CESM use. They
are usually copied from secondary sources; `tools/` refits them from the table
the paper fitted, Jerlov (1968) Table XXI, and reproduces R for all six rows.
Repeating the fit found that the published parameters miss their own source by
46 percent at 1 m for types II and III.

**Data.** Jerlov (1968) Tables XX and XXI. Obtaining the first edition settles
three questions that had been open in `DATA.md`:

- The Solonenko & Mobley reference column is Jerlov 1968, agreeing to 0.06 to
  0.25 percent. It was not an error; this file had said so on the strength of
  comparing their table against an edition they did not cite.
- The 600 nm anomaly for types I, IA, IB and II is a revision Jerlov made in
  1976 and documented in his own text.
- Coastal type 1 repeating oceanic III at eight wavelengths is in the original
  table, and survives the revision at seven.

**Changed.** Reverses the scope decision in `DECISIONS.md` section 12, which
had ruled shortwave heating out. The line had been drawn on similarity of
subject matter rather than on whether the provenance could be established.

## 0.1.4 — 2026-09-09

**Added.** Two runnable examples, `sources_disagree.py` and
`synthetic_underwater_images.py`, run by CI.

**Changed.** A scalar wavelength returns a float rather than a one-element
array, matching `numpy.interp`. `float(w.a(550))` raised under NumPy 2 before
this; writing the first example was what found it. Passing a sequence still
returns an array.

## 0.1.3 — 2026-09-07

**Added.** `Scene.attenuation_coefficients` returns beta_D, beta_B and B_inf
for the Akkaynak-Treibitz image formation model. `are_distinct` is False:
under single scattering both coefficients are the beam attenuation
coefficient. The limitation travels with the value rather than living in
documentation.

## 0.1.2 — 2026-09-06

**Added.** `water_type_at_depth`, the Jerlov type that typically applies in
each 10 m layer down to 200 m, from Williamson & Hollins (2023). Returns
`None` where fewer than ten measurement campaigns supported a declaration.

**Fixed.** 0.1.1 used `numpy.trapezoid`, a name added in NumPy 2.0, despite
declaring `numpy>=1.22`. It did not run on the versions it claimed to support,
and CI had not noticed because every job installed the newest NumPy. A job
pinned to the oldest declared version was added.

**Data.** `DATA.md` records that the depth-profile paper's Data Availability
Statement gives the DOI of an unrelated dataset — lake locations in the United
States — and identifies the three cells where the paper departed from its own
stated selection rule.

## 0.1.1 — 2026-09-05

**Changed.** Renamed from `uwlight`. The name now matches the term researchers
in this field search for; searching PyPI for `jerlov` was what established the
gap this package fills. Also modernises the licence metadata for setuptools
77 and later.

## 0.1.0 — 2026-09-05

First release. Absorption and scattering coefficients for the Jerlov optical
water types, from four sources, each carrying its own model constants and its
own caveats. Direct and veiling components along a horizontal underwater path.
CIE XYZ, sRGB, and arbitrary camera or photoreceptor responses. Every shipped
table regenerable from its primary source by `tools/`.

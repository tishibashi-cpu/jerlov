# Examples

Seventeen scripts. Each runs against the installed package and needs nothing beyond
NumPy.

```
python examples/sources_disagree.py
python examples/from_one_measurement.py
python examples/synthetic_underwater_images.py
python examples/solar_heating.py
python examples/what_an_eye_sees.py
python examples/light_at_depth.py
python examples/measured_scattering.py
python examples/what_is_in_the_water.py
python examples/euphotic_zone.py
python examples/optical_link.py
python examples/seagrass_depth_limit.py
python examples/isolumes.py
python examples/lure_colours.py
python examples/ultraviolet.py
python examples/radiance_distribution.py
python examples/painted_sphere.py
python examples/wave_focusing.py
```

CI runs all of them on every push, so an example that has stopped working is a
failed build rather than something a reader discovers.

Each prints the version and path it loaded first. `python examples/foo.py`
puts `examples/` on `sys.path`, not the current directory, so an installed
copy of the package silently wins over the working tree. In a clone, run
`pip install -e .` first.

## Which one to read

| If you | Start with |
|---|---|
| wonder why `water()` asks for a source | `sources_disagree.py` |
| have measurements from an instrument, including a backscattering sensor | `from_one_measurement.py` |
| need synthetic underwater imagery | `synthetic_underwater_images.py` |
| write an ocean circulation model | `solar_heating.py` |
| study vision, or design a sensor | `what_an_eye_sees.py` |
| need the light at depth, below the top 10 m | `light_at_depth.py` |
| need a backscatter ratio and have no instrument | `measured_scattering.py` |
| work with absorption, or with phytoplankton and CDOM | `what_is_in_the_water.py` |
| need the depth of the euphotic zone, or the light phytoplankton get | `euphotic_zone.py` |
| design an underwater optical link or a lidar | `optical_link.py` |
| work on seagrass, or on restoring a meadow | `seagrass_depth_limit.py` |
| study vertical migration, or where animals sit in the light | `isolumes.py` |
| design or test painted fishing lures or other gear | `lure_colours.py` |
| study ultraviolet exposure under water, of reefs, plankton or chemistry | `ultraviolet.py` |
| need the radiance distribution, the mean cosine or scalar irradiance | `radiance_distribution.py` |
| render or photograph objects under water, from any direction | `painted_sphere.py` |
| work with the flicker of light under waves, near the surface | `wave_focusing.py` |

## What each shows

**`sources_disagree.py`** — the same Jerlov water type has different
coefficients in different papers. At 510 nm the scattering coefficient of
Jerlov III differs by a factor of **3.8** between the two published sets. Also
shows what each source says is doubtful about itself, what happens at the
cells a published table got wrong, and the three things the package refuses to
guess.

**`from_one_measurement.py`** — the routes from an instrument reading to a
spectrum: reconstructing Kd from one wavelength (Austin & Petzold 1986),
estimating b from a transmissometer's c (Smart 2007), handing over your own
measured spectra with `Water.from_measurements`, and converting a
backscattering sensor's single-angle reading to bb (Boss & Pegau 2001). Each
result carries the accuracy the paper claims for it.

It also marks a doubtful channel and attaches replicate uncertainties to
your own spectra: a value you flag `suspect` warns exactly as a published one
does, and a status the package does not know is refused.

It ranks the published types by their distance from a measured Kd, from one
wavelength and from a spectrum, and shows why the spectrum tells oceanic and
coastal types apart better.

It ends by putting the measured bb back into a scene and comparing against a
plausible guess: at 5 m the guess overstates the contrast by 65 percent. That
is the argument for why `Water.bb` has no default, made with numbers rather
than asserted.

**`synthetic_underwater_images.py`** — how five reflectance patches appear at
ranges from 0 to 16 m in Jerlov III water at 15 m depth, white-balanced two
ways: to daylight, which keeps the water's cast, and to the downwelling
irradiance at depth, which removes it. Then the veiling fraction, the
contrast, and coefficients in the Akkaynak-Treibitz form.

**`solar_heating.py`** — the Paulson & Simpson (1977) two-exponential
parameters that ROMS, MITgcm, NEMO and CESM all use, the per-layer heating
they imply, and where they fail: **46 percent off their own source at 1 m**,
because two exponentials cannot follow the near-surface decay.

**`what_an_eye_sees.py`** — `integrate_response` against any spectral
sensitivity. Six photoreceptors and a three-channel camera, at four depths,
counting photons. At the surface the L and M cones catch the most; by 20 m
in Jerlov II the 480 nm rod is ahead. Counted as energy instead, the S
cone's surface catch would be 57 percent of the largest rather than 46: the
basis of the curve has to be that of the spectrum. The camera's red-to-blue
ratio falls by a factor of 29 over 50 m.

**`light_at_depth.py`** — `descend` carries the downwelling irradiance
down through the typical depth profile of Williamson & Hollins (2023), each
10 m layer with its own type's Kd. The correction runs both ways: at 490 nm
and 60 m, Jerlov I receives a third less light than its surface Kd implies,
and 3C **530 times more**. The 1 percent light level of Jerlov I rises from
197 m to 133 m. Where the paper declared no type, it stops. Then PAR, which
reaches 1 percent shallower than 490 nm light from I to 5C and deeper in 7C
and 9C, and a scene
built from the descent with `Scene.at_depth`.

**`measured_scattering.py`** — Petzold's (1972) eight measured volume
scattering functions. Their backscatter ratios run from **0.013 to 0.044**,
the clearest water highest; every phase function falls by four orders of
magnitude from 1 to 90 degrees and rises again by up to three times towards
180. Swapping a guessed 0.015 for the measured ratios of the coastal and
harbor waters moves the contrast of a target at 5 m from 4.0 to 2.6.

**`what_is_in_the_water.py`** — the absorption of a water's contents, a
minus the pure water spectrum the source built a on. At 412 nm the contents
of 5C absorb twelve times what those of IB do; at 600 nm pure water is 78
to 98 percent of every type's absorption. At
715 nm the measured averages lie 14 to 16 percent above a fit that gives
the contents nothing there.

**`euphotic_zone.py`** — from one Kd(490) reading to the depth of the
euphotic zone: `classify_kd` finds the nearest type (IA, with IB close
behind), `descend` follows it as it turns IB below 30 m, and `par_profile`
attenuates PAR wavelength by wavelength. The usual shortcut, 4.6 / Kd(490),
puts the 1 percent level at **154 m**; PAR, layer by layer, at **101 m**. At
that depth 88 percent of what is left is violet-blue and the red band of
chlorophyll a gets almost nothing. Set beside the quanta irradiance Jerlov
measured in IA water (`jerlov1977_quanta`), and integrated over his
350-700 nm with `band=`, the profile agrees within 1.8 percentage points
down to 10 m and then keeps too much light: its 1 percent level is
**100 m** against his **87 m**. Three editions of the classification
are compared, and agree here; at Kd(490) = 0.045 they do not.

**`optical_link.py`** — beam attenuation at common laser lines, and the
range a loss budget buys: each attenuation length costs 4.34 dB, so 40 dB
is 9.2 of them in any water. The clearest wavelength moves from 494 nm in
IB to 564 nm in 5C, and the two published IOP sets disagree on the range
at 532 nm by up to a factor of **2.9**, in Jerlov III. Petzold's eight
measured waters, and the depth a narrow-beam lidar reaches.

**`seagrass_depth_limit.py`** — the depth at which the bottom still gets
25, 11 or 5 percent of the surface PAR, spanning the light requirements
reported for seagrasses (Duarte 1991; Dennison et al. 1993; Kenworthy &
Haunert 1991). At 11 percent the limit runs from 13.4 m in Jerlov III to
2.7 m in 9C; one step from 1C to 3C costs 3.3 m of depth. In 3C and more
turbid water, Duarte et al. (2007) find seagrasses need more light, and
their 33.3 percent puts the limit 2.1 to 2.2 times shallower than 11
percent does. A Kd(PAR) measured in the top metre puts the limit in III at
9.4 m rather than 13.4, because PAR attenuates fastest near the surface.

**`isolumes.py`** — the depth of light levels from a tenth to a
hundred-thousandth of the surface PAR, and how far each moves for a tenfold
dimming at dusk. The steps grow with depth as the spectrum narrows to the
blue. In Jerlov I they are 58 and 61 m; with I's own Kd all the way down
they would be 106 and 114 m, so the typical turn to IB below 40 m roughly
halves them. A thousandth of the surface light lies 9 times shallower in 9C
than in II. For an eye rather than PAR, with `photon_weight=`, a 480 nm rod's
isolume lies 26 m below PAR's in I and 13 m in II.

**`lure_colours.py`** — six painted finishes seen horizontally through 0.5
to 5 m of water, as colour swatches beside the paint in air (and, with
`--png`, an image) and as luminance contrast against the open water behind
them. What the water
decides is exact: at each wavelength the contrast left at range r is
exp(-c r), so in Jerlov 1C 22 to 35 percent of it is left at 2 m,
depending on wavelength. What it does not decide is where the contrast
starts: with the light on the lure's side and the water's backscatter
ratio as guesses, the same finish starts anywhere across a factor of
**124**, and red, blue and black change sign. It says so, and suggests
measuring the start instead.

**`ultraviolet.py`** — how deep UV-A (315-400 nm) goes against PAR in each
Jerlov type, with `par_profile(..., band=)` and the depth profile of
`descend`. Jerlov's (1976) Kd covers UV-A for 8 of the 10 types; 7C and 9C
have none below 350 nm and are left out. UV-A reaches **0.61 to 0.76** of
PAR's 1 percent depth in the oceanic types and **0.22 to 0.25** in the
coastal ones, and where PAR is down to 10 percent, 3.3 to 7.0 percent of
the surface UV-A is left in the open ocean against 0.04 to 0.05 percent on
the coast.

**`radiance_distribution.py`** — the light arriving from each direction at
depth in Jerlov II, by a Monte Carlo solution of the radiative transfer
equation written in the example itself, from the package's a and b, a
Petzold phase function and pure water's. The package does not solve it
(DECISIONS.md section 38). Gershun's law recovers the a put in to within 2
percent; Kd is within 6 percent of Jerlov's (1976) at 500 and 550 nm and 20
to 24 percent above at 450. Scalar irradiance exceeds planar by 1.24 to
1.37, and the next nearest of Petzold's stations changes Eu / Ed at 10 m by
about half. Then the same model in Lake Pend Oreille against the radiance
Tyler (1958) measured there, with a taken from his light by Gershun's law:
the model's mean cosine is 0.76 to 0.77 against his 0.70 to 0.72, its Eu / Ed
0.56 to 0.80 of his, and its radiance 65 and 85 degrees from the zenith too
low, under either sky and with either phase function run. Changing one
thing at a time, any of three other Petzold phase functions, or a b about
1.7 times larger, brings it within 0.002 of his mean cosine; the figures
compared do not tell which. Takes about two minutes.

**`painted_sphere.py`** — a sphere in four stand-in paints, 10 m deep in
Jerlov II, seen 2 m away from above, from below, and horizontally towards
and away from the sun, lit by the same Monte Carlo light field, copied
into the script. A face turned up receives Ed within 2 percent. The grey
sphere is 14.5 times as bright as the water seen from above and 0.42 times
seen from below; the paints are 7.0 times apart from above and 1.06 from
below. The next nearest Petzold station moves the grey sphere by a quarter
to a third from above and with the sun behind. Under a uniform overcast the
two horizontal views come together, 2.17 and 2.19 times the water. A clear
coat reflects 0.32 percent from water against 4.0 from air, and changes the
grey sphere by at most 8.9 percent; the sphere's shadow, at most 0.4. `--png`
writes the picture, sun and overcast, with each paint in air beside it.
Takes about two minutes.

**`wave_focusing.py`** — the flicker of the light under a wind-driven
sea, against what Darecki et al. (2011) measured in the Santa Barbara
Channel. A random surface from Elfouhaily et al.'s (1997) spectrum refracts
the sunbeam; the rays are counted at each depth, blurred by the sun's disc
and a 2.5 mm collector. With the scattered light spread evenly, as fixed
beforehand, the measured coefficient of variation is 1.5 to 2.7 times the
model's down to 2.84 m. Light scattered on its way down still carries the
pattern, shifted; with that, the measurement is 0.69 to 1.24 times the
model down to 2.84 m and 0.54 to 0.77 below. Takes about ten minutes.

## What they do not show

Three scripts compare with field measurements: `euphotic_zone.py` with
Jerlov's quanta irradiance by water type, `radiance_distribution.py` with
Tyler's radiance distribution in a lake, which it does not match (part 6),
and `wave_focusing.py` with Darecki et al.'s flicker under waves.
Nothing else has been compared against photographs or field radiometry; the
output is what the published coefficients imply.

**Every script ends with the assumptions it made** — stated backscatter
ratios, approximate veiling geometry, invented reflectance and receptor
curves, D65 standing in for real daylight. Each is a choice a caller can
replace with a measurement.

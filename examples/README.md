# Examples

Thirteen scripts. Each runs against the installed package and needs nothing beyond
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
sensitivity. Six photoreceptors and a three-channel camera, at four depths.
The ordering of the receptors reverses with depth, which is the reason
deep-sea rod pigments cluster near 480 nm.

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
that depth 87 percent of what is left is violet-blue and the red band of
chlorophyll a gets almost nothing. Three editions of the classification are
compared, and agree here; at Kd(490) = 0.045 they do not.

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
than in II.

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

## What they do not show

None of this has been compared against photographs or field radiometry,
because the measurements needed to do that do not appear to exist. The output
is what the published coefficients imply.

**Every script ends with the assumptions it made** — stated backscatter
ratios, approximate veiling geometry, invented reflectance and receptor
curves, D65 standing in for real daylight. Each is a choice a caller can
replace with a measurement.

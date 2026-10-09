# Examples

Eight scripts. Each runs against the installed package and needs nothing beyond
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

## What they do not show

None of this has been compared against photographs or field radiometry,
because the measurements needed to do that do not appear to exist. The output
is what the published coefficients imply.

**Every script ends with the assumptions it made** — stated backscatter
ratios, approximate veiling geometry, invented reflectance and receptor
curves, D65 standing in for real daylight. Each is a choice a caller can
replace with a measurement.

# Examples

Five scripts. Each runs against the installed package and needs nothing beyond
NumPy.

```
python examples/sources_disagree.py
python examples/from_one_measurement.py
python examples/synthetic_underwater_images.py
python examples/solar_heating.py
python examples/what_an_eye_sees.py
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
| have measurements from an instrument | `from_one_measurement.py` |
| need synthetic underwater imagery | `synthetic_underwater_images.py` |
| write an ocean circulation model | `solar_heating.py` |
| study vision, or design a sensor | `what_an_eye_sees.py` |

## What each shows

**`sources_disagree.py`** — the same Jerlov water type has different
coefficients in different papers. At 510 nm the scattering coefficient of
Jerlov III differs by a factor of **3.8** between the two published sets. Also
shows what each source says is doubtful about itself, what happens at the
cells a published table got wrong, and the three things the package refuses to
guess.

**`from_one_measurement.py`** — the routes from an instrument reading to a
spectrum: reconstructing Kd from one wavelength (Austin & Petzold 1986),
estimating b from a transmissometer's c (Smart 2007), and handing over your
own measured spectra with `Water.from_measurements`. Each result carries the
accuracy the paper claims for it.

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

## What they do not show

None of this has been compared against photographs or field radiometry,
because the measurements needed to do that do not appear to exist. The output
is what the published coefficients imply.

**Every script ends with the assumptions it made** — stated backscatter
ratios, approximate veiling geometry, invented reflectance and receptor
curves, D65 standing in for real daylight. Each is a choice a caller can
replace with a measurement.

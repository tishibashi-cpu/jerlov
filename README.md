# jerlov

Inherent optical properties of the Jerlov optical water types, with
provenance.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22321312.svg)](https://doi.org/10.5281/zenodo.22321312)

https://github.com/tishibashi-cpu/jerlov

Documentation, with guides and the API reference:
https://tishibashi-cpu.github.io/jerlov/

```
pip install jerlov
```

Every coefficient carries the source it came from. Values that a published
table got wrong are flagged rather than quietly repaired, and quantities that
the data do not determine are refused rather than guessed.

**What is claimed.** That the published coefficients are implemented
correctly, and that every shipped table can be regenerated from its primary
source. The tests demonstrate both, by reproducing each paper's tables from
that paper's own equations.

**What is not claimed.** That this predicts what a camera will record
underwater. That would need measurements which, as far as we can tell, have
not been made. `DATA.md` records what is uncertain and `DECISIONS.md` records
where the model stops.

```python
import jerlov

w = jerlov.water("III")          # Williamson & Hollins (2022) by default
w.a(550), w.b(550), w.c(550)
```

## Why the source is part of the API

The same Jerlov water type has different coefficients in different papers, and
the differences are not small. Solonenko & Mobley (2015) obtained a and b by
inverting Kd; Williamson & Hollins (2022) measured them. At 510 nm their
scattering coefficients differ by up to a factor of 3.8, at Jerlov III.

The equations differ too. Both papers use the scattering model of Haltrin
(1999), but with different constants: Haltrin's Eq. (6) gives a
small-particle coefficient of 1.151302, and Solonenko & Mobley print and
compute with 1.513. Reproducing a published table therefore needs that
paper's own constant, so constants are attached to sources.

## What this package will not do

- **Extrapolate.** Asking for a wavelength outside the data raises. Values
  that a source itself extrapolated are returned, but marked, and they warn.
- **Fill a gap.** Where a published value is wrong and could not be
  recovered, the value is NaN and stays NaN through interpolation.
- **Supply bb.** The backscattering coefficient is not determined by the
  Jerlov classification. Deriving it from the particle concentrations of the
  two sources gives answers differing by up to a factor of 31, so
  `Water.bb` requires an explicit ratio: `backscatter_ratio` (bb/b, pure
  water included) or `particle_backscatter_ratio` (bbp/bp).

## Provenance warnings

Interpolating across a value that a paper got wrong gives a number that looks
no different from a sound one. `ProvenanceWarning` is the only thing that
tells them apart.

```python
>>> w = jerlov.water("5C", source="solonenko2015")
>>> w.b(650)
ProvenanceWarning: b for Jerlov 5C rests on flagged values:
reconstructed at 650 nm. ...
```

`Water.caveats()` returns everything known to be doubtful about that water.

## Sources

| key | a, b from | types | range |
|---|---|---|---|
| `williamson2022` | measurement | IB-5C | 300-800 nm |
| `solonenko2015` | inversion of Kd | I-9C | 300-700 nm |
| `jerlov1976` | Kd only | I-9C | 300-715 nm; printed 310-700, and outside that it warns |
| `jerlov1968` | Kd only, first edition | I-9C | 310-700 nm |
| `austin1986` | Kd only, replacement values | I-1C | 350-700 nm |

`solonenko2015` also carries `kd_hydrolight()`, the Kd that HydroLight
computed from its a and b; DATA.md section 19 says how it differs from `kd()`.

`jerlov.SOURCES` holds the full citation, DOI and caveats for each. The two
Jerlov editions differ by up to 35 percent at single wavelengths; establish
which one a number came from before comparing it with either.

## What it covers

Each topic has a page on the site with the calls and what they assume;
[Which function to use](https://tishibashi-cpu.github.io/jerlov/choosing.html) lists them all by what you
want and what you have.

- [Seeing through water](https://tishibashi-cpu.github.io/jerlov/topics/seeing_through_water.html): a target
  seen at a distance, looking up or down, the Akkaynak-Treibitz
  coefficients, light that forward scattering turns rather than loses,
  colour against a white you name, and colour differences to an eye
  (`Scene`, `forward_scatter`, `spectrum_to_srgb`,
  `visual_pigment_template`, `receptor_noise_distance`).
- [Light with depth](https://tishibashi-cpu.github.io/jerlov/topics/depth_and_light.html): the type changing
  with depth, irradiance through that profile, PAR and the depth of a
  fraction of it, with Jerlov's and Tyler's measurements and the flicker
  under waves to check against (`descend`, `par_profile`).
- [From a measurement](https://tishibashi-cpu.github.io/jerlov/topics/measurements.html): bb from a
  backscattering sensor, Petzold's scattering functions, measured
  reflectances, the type a measured Kd is nearest, b from c, and your own
  data in the same form (`bb_from_vsf`, `petzold_scattering`,
  `classify_kd`, `Water.from_measurements`).
- [Ocean colour, without a water type](https://tishibashi-cpu.github.io/jerlov/topics/ocean_colour.html): Kd,
  aph and bbp from chlorophyll, Kd from a and bb, f and Q, Rrs below and
  above the surface and from above-water radiances, Rrs of shallow water
  with the bottom in view, the Secchi depth, QAA,
  and the irradiance at the surface under a clear sky.
- [Water for other software](https://tishibashi-cpu.github.io/jerlov/topics/other_software.html): RGB
  coefficients and spectra for renderers, input files for OSOAA and
  HydroLight, and OSOAA's results read back.
- [Solar heating of the upper ocean](https://tishibashi-cpu.github.io/jerlov/topics/solar_heating.html): the
  shortwave absorbed with depth, as ocean models write it, and how far it
  misses its own source.

The guides on the site work through three calculations with every number
checked: the colour of the light at depth, the euphotic zone, and colours
through water.

## Examples

```
python examples/sources_disagree.py            why the source is an argument
python examples/from_one_measurement.py        from an instrument reading
python examples/synthetic_underwater_images.py appearance at range and depth
python examples/solar_heating.py               for ocean circulation models
python examples/what_an_eye_sees.py            any spectral sensitivity
python examples/light_at_depth.py              light through the depth profile
python examples/measured_scattering.py         Petzold's measured bb/b
python examples/what_is_in_the_water.py        absorption without the water
python examples/euphotic_zone.py               PAR and the 1 percent depth
python examples/optical_link.py                laser range for links and lidar
python examples/seagrass_depth_limit.py        light at the bottom, by requirement
python examples/isolumes.py                    light levels and vertical migration
python examples/lure_colours.py                painted lures: colour and contrast
python examples/ultraviolet.py                 UV-A at depth, against PAR
python examples/radiance_distribution.py       radiance from every direction
python examples/painted_sphere.py              a sphere seen from four directions
python examples/wave_focusing.py               flicker under waves, against Darecki
python examples/fish_colour_differences.py     colour differences for a fish's cones
python examples/ocean_colour_and_secchi.py      Kd from chlorophyll or a and bb, the Secchi depth
python examples/sunlight_and_d65.py            the clear sky at the surface against D65
python examples/looking_up_and_down.py         contrast looking up, across and down
python examples/snells_window.py               the sky seen from under water
python examples/rendering_export.py            water for Mitsuba, pbrt and Blender
python examples/rgb_versus_spectral.py         what RGB rendering does to colours
python examples/water_lookup_tables.py         tables for games and real-time shaders
python examples/phase_function_choice.py       Henyey-Greenstein against Petzold
python examples/reference_images.py            measured materials through three types
python examples/radiative_transfer_inputs.py   files for OSOAA and HydroLight
python examples/closure_with_jerlov_kd.py      an open question: IOPs against Jerlov's Kd
python examples/shallow_water_closure.py       an open question: shallow-water Rrs
python examples/fq_at_45_degrees.py --archive PATH   an open question: f/Q at a 45-degree sun
```

Thirty-one scripts, each aimed at a different reader; `examples/README.md` says
which to start with. CI runs all of them on every push, so an example that has
stopped working is a failed build. Every one ends with the assumptions it
made.

## Provenance and design

`DATA.md` records, for every shipped table, where it came from, what was
verified, and what is known to be wrong with it. Fifty entries are
documented there: thirteen confirmed defects in the source literature, three
questions the first edition of Jerlov settled, and the rest notes.

`DECISIONS.md` records why the package is shaped the way it is, including the
alternatives that were rejected and why.

`OPEN_QUESTIONS.md` gathers what comparing the sources found: where they
disagree, by how much, and how much of it the conditions a source leaves
unrecorded could explain. The package does not settle these questions;
it puts numbers on them, each recomputed by a test.

## Contributing, and reporting a wrong number

`CONTRIBUTING.md` sets out what goes in and what it takes: a primary source, a
script in `tools/` that produces the table, checks inside that script against
the paper's own equations, an entry in `DATA.md`, and a regression test.

**A coefficient that disagrees with a paper you have is the most useful report
this package can receive.** `DATA.md` exists because several such
disagreements turned out to be defects in the literature rather than here.
Issues: <https://github.com/tishibashi-cpu/jerlov/issues>

`CHANGELOG.md` covers every release. What a release may and may not change,
from 1.0 on, is under "Compatibility" in `CONTRIBUTING.md`.

## Licence

Apache-2.0. The Williamson & Hollins data are Crown copyright, Dstl, under
the Open Government Licence v3.0; Mobley's rho tables are from the Ocean
Optics Web Book, under a Creative Commons Attribution licence; see `NOTICE`.

## Citation

Cite the concept DOI, which always resolves to the latest version:

> Ishibashi, T. jerlov: inherent optical properties of the Jerlov optical
> water types, with provenance. Zenodo.
> https://doi.org/10.5281/zenodo.22321312

Please also cite the sources the coefficients came from; they are listed with
their DOIs at the top of `DATA.md`. The package is a carrier for other
people's measurements, and this work does not replace citing them.

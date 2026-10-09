# jerlov

Inherent optical properties of the Jerlov optical water types, with
provenance.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22321312.svg)](https://doi.org/10.5281/zenodo.22321312)

https://github.com/tishibashi-cpu/jerlov

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
  `Water.bb` requires an explicit `backscatter_ratio`.

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

## Looking at something through water

For a horizontal path, the observed radiance splits into the target's light
that survived and the light the water added along the way:

```python
import numpy as np, jerlov

wl   = np.arange(450., 651., 50.)
iops = jerlov.water("III")
kd   = jerlov.water("III", source="austin1986")

scene = jerlov.Scene.at_depth(iops, 10.0, np.ones_like(wl), wl, kd=kd)
b_inf = jerlov.veiling_radiance_estimate(
    iops, scene.downwelling, wl, backscatter_ratio=0.015
)

obs = scene.observe(np.full_like(wl, 0.8), distance_m=5.0,
                    veiling_radiance=b_inf)
obs.direct, obs.veiling, obs.radiance
obs.veiling_fraction        # how much of what you see is just water
obs.contrast(background)    # against another target down the same path
```

`veiling_radiance` has no default. B_inf depends on the backscattering
coefficient and the phase function, and neither follows from the water type.
`veiling_radiance_estimate` gives the usual single-scattering approximation
for callers with nothing better, but it has to be asked for.

Deliberate limits, all recorded in `DECISIONS.md`:

- **Horizontal paths only.** Observer and target at the same depth.
- **No forward-scatter blur.** This is the radiance of one point, not the
  sharpness of an image.
- **Lambertian targets.**

### Coefficients for the Akkaynak-Treibitz form

Underwater vision work usually writes the same physics as

```
I = J * exp(-beta_D * r) + B_inf * (1 - exp(-beta_B * r))
```

```python
p = scene.attenuation_coefficients((0.5, 5.0), veiling_radiance=b_inf)
p.beta_D, p.beta_B, p.B_inf
p.are_distinct      # False
p.note              # why
```

**`are_distinct` is False, and that is the honest answer.** Under single
scattering both coefficients are the beam attenuation coefficient c. The
central claim of Akkaynak & Treibitz (2018) is that in reality they differ and
vary with range, depth and target reflectance; separating them needs
measurements this package does not have.

It is still useful. Implementations that fit these coefficients often bound
them by guesswork for want of a physical starting point. This gives them one,
and says how far it can be trusted.

`distance_range_m` is required and recorded. A coefficient quoted without the
range it describes is not a well-defined quantity, so the API does not let you
omit it.

## What colour is that

```python
white = scene.downwelling / np.pi          # a perfect diffuser at that depth
rgb   = jerlov.spectrum_to_srgb(obs.radiance, wl, white=white)

jerlov.spectrum_to_xyz(spectrum, wl)      # unnormalised CIE XYZ
jerlov.integrate_response(spectrum, wl, sensitivity, sensitivity_wl)
```

`white` has no default. A radiance spectrum has no colour until something is
called white, and underwater the useful reference is usually the downwelling
irradiance at that depth rather than daylight. Both are legitimate and they
answer different questions:

| white | question answered |
|---|---|
| downwelling at depth | what a diver's adapted eye, or a camera white-balanced *there*, sees |
| daylight at the surface | what a camera set at the surface records |

`integrate_response` takes any spectral sensitivity: three camera channels,
or a set of photoreceptor absorbances.

Two silent errors are checked rather than assumed:

- **Coverage.** A spectrum spanning 450-650 nm integrated against colour
  matching functions spanning 360-830 nm quietly drops the ends. Every
  integration reports how much of the observer it actually covered and warns
  when it is not essentially all of it.
- **Gamut.** Underwater colours often fall outside sRGB. Clipping changes
  them, so `GamutWarning` says so.

## If you measured backscattering

`Water.bb` refuses to guess a backscattering ratio. If you have an instrument
you do not have to:

```python
r = jerlov.bb_from_vsf(beta=0.0021, angle_deg=140, wavelength_nm=532)
r.bb, r.particulate, r.water     # 1/m
r.chi_p, r.quoted_error_percent  # 1.18, 3.5
```

Boss & Pegau (2001). The pure sea water terms are analytic and are checked
against the definition of bb rather than transcribed; only the particle
conversion is tabulated. Angles outside 90-170 degrees are refused, and 170
warns: its quoted spread is **34.8 percent** against 2.6-6.4 from 90 to 160.

This gives the bb of the water your instrument was in. It still gives no bb
for a Jerlov water type, because nothing does.

## Measured scattering functions

Without an instrument, the next best thing to a guess is a water that was
measured. Petzold (1972) measured the volume scattering function from 0.1 to
180 degrees in eight ocean waters, from the clear Tongue of the Ocean to San
Diego Harbor:

```python
jerlov.PETZOLD_STATIONS                  # clearest first: 'AUTEC 8', ..., 'NUC 2040'
f = jerlov.petzold_scattering("HAOCE 11")
f.c, f.b, f.backscatter_ratio            # 0.398, 0.21933, 0.013  (1/m, 1/m, bb/b)
f.vsf_at(120.0)                          # 1/(m sr), at 530 nm
f.phase_function()                       # vsf / b, at f.angles_deg

w.bb(532, backscatter_ratio=f.backscatter_ratio)   # bb/b of a measured water
```

The ratio spans **0.013 to 0.044** across the eight. These are eight waters
on eight days in 1971, at 530 nm, water and particles together; none of them
is a Jerlov type. Every value was transcribed from the report and checked
against its own integrals and its second printing; DATA.md section 21.

## The type changes with depth

The classification is defined on the top 10 m, but clarity does not stay put.
Water that is Jerlov I at the surface is typically IB below 40 m; turbid
coastal water clears as you go down.

```python
jerlov.water_type_at_depth("I", 60.0)     # 'IB'
jerlov.water_type_at_depth("3C", 45.0)    # 'II'
jerlov.water_type_at_depth("9C", 15.0)    # None: the paper declined to say
jerlov.water_type_at_depth("I", [0, 30, 60])   # array(['I', 'IA', 'IB'], dtype=object)
```

`None` means fewer than ten measurement campaigns supported a declaration, so
nothing is asserted. This is a lookup, not a correction applied on your
behalf.

To carry the downwelling irradiance down through that profile, with each 10 m
layer attenuating by the Kd of its own type:

```python
d = jerlov.descend("1C", 45.0, wl)        # source="jerlov1976" by default
d.layers          # ((0, 10, '1C'), (10, 20, '1C'), (20, 30, 'III'), ..., (40, 45, 'II'))
d                 # <Descent 1C to 45 m: 1C 0-20, III 20-40, II 40-45 m; Kd from jerlov1976; ...>
scene = jerlov.Scene.at_depth(jerlov.water("II"), 45.0, surface, wl, kd=d)
```

It refuses to go through a layer the paper declared nothing for, rather than
carrying the last type on: 3C stops at 70 m, 9C at 10 m.
`jerlov.profile_depth("3C")` says how far a descent can go, and
`d.transmittance_at(z)` gives any depth above the descent's bottom without
descending again.

## Light for photosynthesis

PAR, the photon flux from 400 to 700 nm, attenuated wavelength by wavelength
rather than with one coefficient, and the depth at which it falls to 1
percent of its surface value:

```python
p = jerlov.par_profile(surface, wl, [0, 25, 50], kd=d, unit="energy")
p.par                      # umol photons m-2 s-1 at each depth
p.fraction                 # PAR(z) / PAR(0)
p.depth_of_fraction(0.01)  # m
```

`kd` is a `Water` carrying Kd, an array, or a `Descent`. `unit` has no
default, because PAR counts photons and an energy spectrum read as photons is
weighted wrongly with no sign of it. This is planar PAR, from Ed; PAR on
scalar irradiance is larger by a factor this package cannot supply.

## Which type is my water nearest?

```python
r = jerlov.classify_kd(wl, measured_kd)       # source="jerlov1976" by default
r                 # <KdClassification II 0.064, then IB 0.412 (jerlov1976, 26 wavelengths)>
r.distances       # every type, nearest first: rms of ln(measured / type)
r.beyond          # "clearer" or "more turbid" than every type, or None
```

It ranks the types of one edition; it draws no boundaries, since those differ
between editions. A single wavelength is accepted, and ranks oceanic and
coastal types less well apart than a spectrum does. `types=` compares with
some of the types only, which keeps the wavelengths where only the others
have gaps.

## Other entry points

```python
# Reconstruct a Kd spectrum from one measured value (Austin & Petzold 1986).
jerlov.kd_spectrum(kd=0.06, wavelength_nm=490, at=[440, 550, 650])

# Estimate b from a transmissometer's c (Smart 2007).
jerlov.b_from_c(c=0.5, wavelength_nm=555, bw=0.0019, cw=0.0659)
jerlov.pure_water_scattering(555)   # Morel's bw, if that is what c was corrected with

# The measured points behind the williamson2022 spectra, with their spread.
m = jerlov.measured_points("III", "a")   # m.wavelengths, m.values, m.std_dev

# The pure water absorption williamson2022 built its a on (300-800 nm).
jerlov.pure_water_absorption(440)        # 0.0104; other sources say why they have none

# Use your own measurements; they take exactly the same path, flags included.
w = jerlov.Water.from_measurements(
    wavelengths, a=..., b=...,
    flags={"a": statuses},             # "ok", "suspect", ...: as in DATA.md; flagged ones warn
    uncertainty={"a": sigma_a},        # 1/m; w.uncertainty("a", 532)
)
```

## Solar heating of the upper ocean

Ocean circulation models absorb shortwave radiation as a sum of two
exponentials, with parameters per Jerlov type from Paulson & Simpson (1977):

```python
jerlov.solar_fraction("IB", 10.0)        # 0.183 of the surface irradiance
p = jerlov.shortwave_parameters("IB")    # R, zeta1_m, zeta2_m
depths, fraction = jerlov.jerlov1968_solar_fraction("IB")   # the table itself
```

Broadband, 300-2500 nm; nothing to do with the spectral quantities above. The
parameters are usually copied from secondary sources, so `tools/` refits them
from the table the paper fitted, Jerlov (1968) Table XXI, and reproduces R for
every row.

**They miss their own source by 46 percent at 1 m** for types II and III. Two
exponentials cannot follow the near-surface decay. `DATA.md` section 14 has
the numbers; anyone heating a thin surface layer should read it.

Only the five oceanic types were fitted. Asking for a coastal type raises
rather than substituting a neighbour.

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
```

Twelve scripts, each aimed at a different reader; `examples/README.md` says
which to start with. CI runs all of them on every push, so an example that has
stopped working is a failed build. Every one ends with the assumptions it
made.

## Provenance and design

`DATA.md` records, for every shipped table, where it came from, what was
verified, and what is known to be wrong with it. Twenty-one entries are
documented there: eight confirmed defects in the source literature, three
questions the first edition of Jerlov settled, and the rest notes.

`DECISIONS.md` records why the package is shaped the way it is, including the
alternatives that were rejected and why.

## Contributing, and reporting a wrong number

`CONTRIBUTING.md` sets out what goes in and what it takes: a primary source, a
script in `tools/` that produces the table, checks inside that script against
the paper's own equations, an entry in `DATA.md`, and a regression test.

**A coefficient that disagrees with a paper you have is the most useful report
this package can receive.** `DATA.md` exists because several such
disagreements turned out to be defects in the literature rather than here.
Issues: <https://github.com/tishibashi-cpu/jerlov/issues>

`CHANGELOG.md` covers every release.

## Licence

Apache-2.0. The Williamson & Hollins data are Crown copyright, Dstl, under
the Open Government Licence v3.0; see `NOTICE`.

## Citation

Cite the concept DOI, which always resolves to the latest version:

> Ishibashi, T. jerlov: inherent optical properties of the Jerlov optical
> water types, with provenance. Zenodo.
> https://doi.org/10.5281/zenodo.22321312

Please also cite the sources the coefficients came from; they are listed with
their DOIs at the top of `DATA.md`. The package is a carrier for other
people's measurements, and this work does not replace citing them.

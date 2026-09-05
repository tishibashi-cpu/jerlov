# uwlight

Inherent optical properties of Jerlov water types, with provenance.

https://github.com/tishibashi-cpu/uwlight

*Working name; not yet released.*

Every coefficient carries the source it came from. Values that a published
table got wrong are flagged rather than quietly repaired, and quantities that
the data do not determine are refused rather than guessed.

```python
import uwlight

w = uwlight.water("III")          # Williamson & Hollins (2022) by default
w.a(550), w.b(550), w.c(550)
```

## Why the source is part of the API

The same Jerlov water type has different coefficients in different papers, and
the differences are not small. Solonenko & Mobley (2015) obtained a and b by
inverting Kd; Williamson & Hollins (2022) measured them. At 510 nm their
scattering coefficients differ by up to a factor of 2.6.

The equations differ too. Both papers use the scattering model of Haltrin
(1999), but with different constants: Haltrin's Eq. (6) gives a
small-particle coefficient of 1.151302, and Solonenko & Mobley print and
compute with 1.513. Reproducing a published table therefore needs that
paper's own constant, so constants are attached to sources.

## What this package will not do

- **Extrapolate.** Asking for a wavelength outside the data raises.
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
>>> w = uwlight.water("5C", source="solonenko2015")
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
| `jerlov1976` | Kd only | I-9C | 300-715 nm |
| `austin1986` | Kd only, replacement values | I-1C | 350-700 nm |

`uwlight.SOURCES` holds the full citation, DOI and caveats for each.

## Looking at something through water

For a horizontal path, the observed radiance splits into the target's light
that survived and the light the water added along the way:

```python
import numpy as np, uwlight

wl   = np.arange(450., 651., 50.)
iops = uwlight.water("III")
kd   = uwlight.water("III", source="austin1986")

scene = uwlight.Scene.at_depth(iops, 10.0, np.ones_like(wl), wl, kd=kd)
b_inf = uwlight.veiling_radiance_estimate(
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

## Other entry points

```python
# Reconstruct a Kd spectrum from one measured value (Austin & Petzold 1986).
uwlight.kd_spectrum(kd=0.06, wavelength_nm=490, at=[440, 550, 650])

# Estimate b from a transmissometer's c (Smart 2007).
uwlight.b_from_c(c=0.5, wavelength_nm=555, bw=0.0019, cw=0.0659)

# Use your own measurements; they take exactly the same path.
uwlight.Water.from_measurements(wavelengths, a=..., b=...)
```

## Provenance and design

`DATA.md` records, for every shipped table, where it came from, what was
verified, and what is known to be wrong with it. Eleven defects in the source
literature are documented there, six of them confirmed.

`DECISIONS.md` records why the package is shaped the way it is, including the
alternatives that were rejected and why.

## Licence

Apache-2.0. The Williamson & Hollins data are Crown copyright, Dstl, under
the Open Government Licence v3.0; see `NOTICE`.

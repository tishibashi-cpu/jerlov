# Data provenance

What every shipped table is, where it came from, what was verified, and what
is known to be wrong with it.

Eleven defects in the source literature are recorded below. Six are confirmed,
three could not be resolved because the material was not obtainable, and two
are notes rather than defects. None of them is repaired silently: values that
could be recovered carry `status = reconstructed` and say how, values that
could not are `missing`, and values that are used but doubtful are `suspect`.

## Files

| File | Contents | Rows |
|---|---|---|
| `jerlov1976_kd.csv` | Downwelling diffuse attenuation Kd. 1 nm, 300-715 nm, 10 types | 4160 |
| `williamson2022_iop.csv` | a and b. **1 nm**, 300-800 nm, 6 types | 6012 |
| `solonenko2015_iop.csv` | Kd0, Kd, KdH, a, b. 17 wavelengths, 10 types | 850 |
| `williamson2022_measured.csv` | Measured a, b points with standard deviation and count | 152 |
| `austin1986_kd.csv` | Replacement Kd for Jerlov's values. 15 wavelengths, 6 types | 90 |
| `austin1986_model.csv` | Slope M and pure sea water Kw. 5 nm, 350-700 nm | 71 |
| `smart2007_b_from_c.csv` | Measured (b-bw)/(c-cw). 412-715 nm, average and bounds | 30 |
| `cie1931_2deg_cmf.csv` | CIE 1931 2-degree colour matching functions. 1 nm, 360-830 nm | 471 |
| `cie_d65.csv` | CIE illuminant D65 relative spectral power. 5 nm, 300-780 nm | 97 |

## The `status` column

| Value | Meaning | How to treat it |
|---|---|---|
| `ok` | The published value, used as printed | Usable |
| `extrapolated` | The paper itself says it was extrapolated | Usable, but less accurate |
| `reconstructed` | The published value is wrong; recovered from an equation | Usable; `value_source` says how |
| `missing` | The published value is wrong and could not be recovered | Empty. Interpolate yourself or avoid that wavelength |
| `suspect` | Used as published, but an internal inconsistency was found | Read the `note` before relying on it |
| `model_extrapolation` | Outside the range of the underlying measurements | Usable, but not measured |

## Sources

- **Jerlov 1976.** From `ip_jerlov.csv` in the Dstl dataset, figshare DOI
  `10.6084/m9.figshare.20290782`, Version 3. Checked against an independent
  transcription of Jerlov (1976) Table XXVII in `jkibele/OpticalRS` and found
  to agree. The provenance of the file is not entirely clear: Williamson &
  Hollins (2022) attribute the same figure to Jerlov (1964), while Williamson
  & Hollins (2023) attribute it to Jerlov (1976). (c) Crown copyright (2022),
  Dstl. Open Government Licence v3.0.

- **Austin & Petzold 1986.** Opt. Eng. 25(3), 471-479, DOI
  `10.1117/12.7973845`. Tables VI and IV. The type I row is pure sea water Kw;
  only the 475 nm column is Jerlov's own value. The rest was computed with the
  paper's Eq. (6), which reproduces the printed table to within 0.39 percent.
  M at 350, 355 and 360 nm is extrapolated, as the paper states. Austin &
  Petzold (1990), Proc. SPIE 1302, 79-93, tested the model against 83 new
  stations from 24.4 to 77.7 degrees north and recommended no change, but
  reports poor agreement beyond 590 nm: a coefficient of variation of 31
  percent at 670 nm.

- **Solonenko & Mobley 2015.** Appl. Opt. 54, 5392-5401, DOI
  `10.1364/AO.54.005392`. Tables 3 to 8.

- **Williamson & Hollins 2022.** Appl. Opt. 61, 9951-9961, DOI
  `10.1364/AO.470464`. From the accompanying spreadsheet rather than the
  printed table; see section 9.

- **Smart 2007.** Opt. Express 15(12), 7152-7164, DOI
  `10.1364/OE.15.007152`. Table 1. Open access.

- **Haltrin 1999.** Appl. Opt. 38, 6826-6832. Origin of the scattering model
  used by both Solonenko & Mobley and Williamson & Hollins; see section 6.

---

## 1. Duplicated rows in Table 7 (confirmed)

In Solonenko & Mobley (2015) Table 7, the rows for Jerlov 3C at 675 and 700 nm
are identical in every column to the rows at 300 and 310 nm. For Jerlov 5C,
the five rows from 600 to 700 nm are identical to those from 300 to 400 nm.

Four independent lines of evidence:

1. The rows match exactly, in all five columns.
2. At 675 nm the value carries the parentheses that the paper uses to mark
   the coastal 300 and 310 nm extrapolations.
3. Computing b from the paper's own Eq. (8) with the Bs and Bl of its Table 3
   reproduces the sound wavelengths to within 0.8 percent, but is 60 to 75
   percent away at the duplicated rows.
4. Williamson & Hollins (2022) substituted values at exactly these cells; see
   the sources section below.

`b` was reconstructed from Eq. (8). For 5C this agrees with the Williamson &
Hollins substitution to three decimal places. For 3C they used linear
extrapolation instead, which differs from Eq. (8) by 1 to 3 percent; Eq. (8)
is used here because it follows from the paper's own scattering model, and
their value is carried in the `williamson2022_value_per_m` column for
comparison. `a`, `Kd` and `KdH` could not be recovered.

**Williamson & Hollins found this too, and did not publish it.** The
spreadsheet `20221121-Dstl_MIOP_analysis_v3.xlsx` in their figshare dataset
has a sheet `Sol_Mob data` whose third row reads "Highlighting denotes values
updated from those published in the original reference". The highlighted cells
are exactly the ones listed above. Nothing in either of their papers mentions
it.

## 2. The Kd0 reference column disagrees (not resolved)

The Kd0 column of `solonenko2015_iop.csv` differs from `jerlov1976_kd.csv` by
up to 34 percent. Solonenko & Mobley cite Jerlov & Koczy (1951) and Jerlov
(1968) for it, not Jerlov (1976).

**Whether this is an edition difference or an error could not be
determined**, because neither of the following could be obtained:

- Jerlov, N. G. (1968), *Optical Oceanography*, Elsevier Oceanography Series
  Vol. 5, pp. 118-120. ISBN 978-0-444-40320-9. **No DOI exists**; the DOIs
  `10.4319/lo.1968.13.4.0731` and `10.1126/science.163.3862.64.a` are reviews
  of the book, not the book.
- Jerlov, N. G. and Koczy, F. (1951), *Reports of the Swedish Deep-Sea
  Expedition 1947-1948*, Vol. 3, pp. 30-71.

Note that Jerlov (1976) *Marine Optics* is the second edition of Jerlov
(1968); they are not independent works.

**Practical effect: none.** Do not mix Kd0 and Kd across the two files. This
package's default source is Williamson & Hollins, and Kd0 is carried as a
reference column, never used as a computational input.

## 3. Jerlov's Kd falls below pure sea water (confirmed, documented in 1986)

Austin & Petzold (1986), section 7:

> We also call attention to the fact that some of the attenuation values for
> type I oceanic water as given by Jerlov are less than the values we suggest
> for Kw. In fact, at some wavelengths the values given by Jerlov for K are
> less than the values of absorption alone published by Morel and Prieur. We
> recommend, therefore, that the values of K as published by Jerlov be
> replaced by those in Table VI.

Checking `jerlov1976_kd.csv` type I against the Austin & Petzold Kw confirms
this at **9 of 15 wavelengths**: 2.2 percent below at 475 nm, 14.7 percent at
525 nm, 14.0 percent at 700 nm. The clearest ocean water would attenuate less
than pure water, which is not possible.

The replacement values are in `austin1986_kd.csv`.

**The Solonenko & Mobley Kd0 at 600 nm is a separate problem.** Jerlov's value
is 2.4 percent below Kw there; theirs is 32.3 percent below, for types I, IA,
IB and II alike. The known defect in Jerlov's data does not account for it.
Not resolved.

## 4. Table 3 parameters for the clearest types (confirmed)

Putting the Bs and Bl of Solonenko & Mobley Table 3 into their Eq. (8) does
not reproduce their b column for types I and IA, although it does for IB
through 9C. Least squares fitting the b column locates the problem (using
their own coefficient 1.513):

| Type | Fitted | Table 3 | Verdict |
|---|---|---|---|
| IA | Bs=0.00199, Bl=0.00102 | Bs=0.002, Bl=0.005 | **Bl is five times too large; Bs agrees** |
| I | Bs=0.00021, Bl=0.00016 | Bs=8e-5, Bl=2e-4 | Bs is 2.6 times off, but the values are tiny |

The fits reproduce the b column to within 0.2 to 0.4 percent, so **the b
column is right and the Table 3 entries are wrong.** The paper describes
special handling for type I, but says nothing about IA.

## 5. Possible duplicated column in Table 6 (not resolved)

The Kd0 of Jerlov 1C is identical to that of Jerlov III at all eight
wavelengths from 525 to 700 nm. In `jerlov1976_kd.csv` the two differ by 12
percent at 525 nm. Resolving this needs the same material as section 2, which
could not be obtained. Left as `suspect`.

## 6. The small-particle scattering coefficient (confirmed)

The model originates in Haltrin (1999), Eqs. (5)-(7):

```
bw(l) = 0.005826 (1/m)   * (400/l)**4.322
bs(l) = 1.151302 (m^2/g) * (400/l)**1.7
bl(l) = 0.341074 (m^2/g) * (400/l)**0.3
```

**The correct small-particle coefficient is 1.151302.** Williamson & Hollins
use 1.1513, which matches. Solonenko & Mobley print 1.513; a digit appears to
have been dropped.

**They also computed with it.** Only 1.513 reproduces their published b
column; Haltrin's 1.151302 is 14 to 25 percent away for types IB through 9C.
Their a and b tables were therefore derived with a small-particle scattering
coefficient 31 percent larger than the original.

Which constant to use depends on the purpose:

| Purpose | Coefficient |
|---|---|
| Reproduce the Solonenko & Mobley tables | 1.513 (their own value) |
| Use the Haltrin scattering model correctly | 1.151302 |

**The two must not be mixed.** The reconstruction in section 1 uses the
former, because its purpose is to fill gaps in their table.

Hollins & Williamson (2023) report that Solonenko & Mobley concluded small
particles dominate while they themselves found large particles dominate
(their Table 6, Fig. 15). Whether the coefficient error contributes has not
been checked.

## 7. A collision of symbols (note)

In Haltrin (1999):

- `Cs`, `Cl` are the small- and large-particle **concentrations** (g/m3)
- `Bs`, `Bl` are the **backscattering probabilities**, constants 0.039 and
  6.4e-4

Solonenko & Mobley and Williamson & Hollins both **rename the concentrations
to Bs, Bl**, colliding with symbols Haltrin uses for something else. Reading
the three papers side by side is easy to get wrong. This package follows
Haltrin.

## 8. Range of the Austin & Petzold model (note)

Given `austin1986_model.csv`, a whole Kd spectrum can be reconstructed from a
single measured value:

```
K(l2) = [M(l2)/M(l1)] * [K(l1) - Kw(l1)] + Kw(l2)
```

The paper states the limit: **K(490) < 0.16 1/m.** Linearity fails in more
turbid water. Beyond 590 nm, Austin & Petzold (1990) report growing
disagreement with measurement.

## 9. About the Williamson & Hollins data (note)

`williamson2022_iop.csv` comes from the sheet `a,b JIB-5C` of
`20221121-Dstl_MIOP_analysis_v3.xlsx` in the figshare dataset, not from the
printed Table 7. **The paper prints 10 nm spacing; the spreadsheet holds 1
nm.**

Two checks were made:

- 72 points against the printed Table 7: **all within 0.5 percent**
- b recomputed from Eqs. (7)-(11) with the Bs, Bl of Table 6 and the
  coefficient 1.1513: **within 5.3 percent**. The worst is Jerlov III at -5.3
  percent, probably because the 2023 paper updates its Bl from 0.90 to 0.91.

**Measured points exist only from 412 to 715 nm.** Everything outside that is
model interpolation or extrapolation and is marked `model_extrapolation`;
300-411 nm and 716-800 nm are affected.

`williamson2022_measured.csv` holds the raw measured points. Hollins &
Williamson (2023) state that the fitting process behind the smooth spectra
would bias some analyses and that the individual points are preferable
(section 2.A). Use these for validation.

The paper kept only averages built from five or more measurements.
Reproducing that filter gives **53 points each for a and b, 106 in total,
matching the paper.** The 46 excluded points are kept with
`status = excluded_sparse`. Jerlov IA and 7C are excluded throughout: one
measurement campaign each.

## 10. The backscattering coefficient cannot be derived from this data (confirmed)

**Veiling light needs bb, and none of these sources contains it.**

Haltrin (1999) Eq. (3) gives bb from the same two-component model:

```
bb(l) = 0.5*bw(l) + Bs*bs(l)*Cs + Bl*bl(l)*Cl
        Bs = 0.039 (small particles), Bl = 6.4e-4 (large)
```

Feeding it the particle concentrations of the two sources gives answers that
diverge:

| Type | From Williamson & Hollins | From Solonenko & Mobley | Ratio |
|---|---|---|---|
| IB | 0.0087 | 0.0325 | 3.7x |
| II | 0.0080 | 0.0410 | 5.1x |
| III | 0.0033 | 0.0398 | 12.2x |
| 1C | 0.0036 | 0.0413 | 11.5x |
| 3C | 0.0018 | 0.0398 | 22.3x |
| 5C | 0.0013 | 0.0394 | 31.2x |

(bb/b at 550 nm. Reported ranges are roughly 0.005-0.01 for open ocean and
0.015-0.03 for coastal water.)

**Neither is inside the plausible range.** The first is too low, the second
too high.

The reason is clear. The split between Cs and Cl is a fitting device, not a
particle size distribution; Williamson & Hollins say so themselves in the note
to their Table 6: "these parameters should be treated as fitting parameters,
rather than the physical properties they represent". Total scattering can be
reproduced with the wrong split, but backscattering is a different moment of
the phase function and depends on it directly.

**Conclusion: bb is not determined by the Jerlov classification.** This
package requires the caller to supply it and has no default.

### The state of the bb literature

**Layer 1: bb in general. Plentiful.** Measured volume scattering functions
(Petzold 1972), phase function parameterisations, statistics of the
particulate backscattering ratio. Decades of work, but none of it tied to the
Jerlov types.

**Layer 2: bb per Jerlov type. Not found.** This is the actual gap. The
closest is Neuner et al. (2020), Proc. SPIE 11506, 1150608, DOI
`10.1117/12.2567076`, which classifies Jerlov types from beam attenuation by
machine learning; from the abstract this is classification rather than
derivation of bb per type. **Abstract only; the full text was not obtained.**

**Layer 3: the data to close it exists.** Smart (2007) gives the inventory of
the World-wide Ocean Optics Database:

> more than 242,000 K profiles but only about 18,000 c profiles, 10,000 a
> profiles, 1,000 b profiles, and **1,200 bb profiles**

**There are more bb profiles than b profiles.** Since Williamson & Hollins
obtained results for six water types from the b data, the same campaign
matching applied to bb should yield something, and their analysis code is
public. **This is an open piece of research and out of scope for this
package.**

## 11. Estimating b from c (note)

`smart2007_b_from_c.csv`. A transmissometer measures c, so this conversion
comes up often.

```
b = (c - cw) * ratio + bw
```

Least squares fits for six datasets: the US continental shelf (CMO),
Chesapeake Bay (COPE), the Sea of Japan and the Yellow Sea. **Accurate to
about 10 percent.**

Three cautions:

- **Use the upper bound for turbid water (c at 488 nm above 1.0 1/m) and the
  lower bound for clear water.**
- **Ratios are lower than tabulated in CDOM-rich water**, such as near a river
  mouth, particularly below 488 nm.
- c itself carries perhaps 10 percent error from forward-scattered light
  reaching the detector.

The same paper gives further relations, not shipped here:

- `a = mu * K` with mu about 0.8, to within 20 percent. The oceanic range of
  the average cosine is 0.6 to 1.0.
- Shannon revised: `c = 1.74 K` at 535 nm for K < 0.06 1/m. Estimating c from
  K has a median error of 25 percent in the Sargasso Sea, 40 percent on the
  US continental shelf, 18 percent in the Sea of Japan and 15 percent in the
  Yellow Sea.
- The accuracy of the Austin & Petzold wavelength conversion is about 8
  percent up to 590 nm, degrading to 31 percent at 670 nm. This agrees
  independently with the conclusion of Austin & Petzold (1990) noted in
  section 8.


## 12. The CIE colorimetric data (note)

`cie1931_2deg_cmf.csv` and `cie_d65.csv` are standard reference data. They
were not measured or derived here, and they are not approximated: an analytic
fit to the colour matching functions would be smaller but would put numbers
in the package whose provenance is a curve fit rather than the standard.

They were transcribed via `colour-science`, which is a convenient and widely
used carrier of the CIE tabulations. `colour-science` is a build-time
dependency of `tools/build_cie.py` only; the package itself does not use it.

Three checks run before anything is written:

- the sums of x-bar, y-bar and z-bar agree to within the rounding of the
  published table
- y-bar peaks at 555 nm, which is the definition of the photopic maximum
- D65 is normalised to 100 at 560 nm

**D65 is the sRGB reference white.** It is a daylight phase, so it is a
reasonable stand-in for the solar spectrum above the surface, but it is not a
measurement of the light at any place or time: the real spectrum depends on
solar elevation, atmosphere and the state of the surface. Do not treat it as
an in-water downwelling spectrum.

The sRGB matrix is not shipped. It is derived in `uwlight/colour.py` from the
primaries and white point of IEC 61966-2-1, and `tests/test_colour.py` checks
the derivation against the published rounded matrix.

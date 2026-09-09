# Data provenance

What every shipped table is, where it came from, what was verified, and what
is known to be wrong with it.

Fifteen entries are recorded below. Seven are confirmed defects, three were
open questions that the first edition of Jerlov settled, and the rest are
notes rather than defects. None of them is repaired silently: values that
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
| `williamson2023_depth.csv` | Typical Jerlov type per 10 m layer to 200 m | 200 |
| `jerlov1968_kd.csv` | Kd from the **first edition**. 16 wavelengths, 10 types | 160 |
| `jerlov1968_total_irradiance.csv` | Percent of total irradiance 300-2500 nm by depth | 120 |
| `paulson1977_shortwave.csv` | Two-exponential shortwave penetration parameters | 9 |

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

## 2. The Kd0 reference column is the first edition, not an error (resolved)

The Kd0 column of `solonenko2015_iop.csv` differs from `jerlov1976_kd.csv` by
up to 34 percent. Solonenko & Mobley cite Jerlov & Koczy (1951) and Jerlov
(1968) for it, not Jerlov (1976).

**They were right and the discrepancy is an edition difference.** Jerlov
(1968) Table XX was obtained and transcribed; it is shipped as
`jerlov1968_kd.csv`. Converting its transmittances to Kd and comparing:

| Type | against Jerlov 1968 | against Jerlov 1976 |
|---|---|---|
| I | **0.09 %** | 3.75 % |
| IA | **0.10 %** | 4.11 % |
| IB | **0.06 %** | 4.72 % |
| II | **0.09 %** | 6.15 % |
| III | **0.15 %** | 7.66 % |
| 7C | **0.06 %** | 0.79 % |
| 9C | **0.25 %** | 0.89 % |

(mean absolute difference over the wavelengths both tables cover)

The coastal types agree to **0.05-0.11 percent** once 310 and 350 nm are set
aside, and those two are already carried as `extrapolated`: Solonenko & Mobley
substituted their own values at the short-wavelength end rather than using
Jerlov's.

Agreement at the first decimal place of a percent is transcription accuracy.
**There is no defect here. The earlier entry in this file was wrong, and said
so on the strength of comparing a paper against an edition it did not cite.**

Do not mix Kd0 and Kd across files: they are different editions of the same
classification, not different measurements of the same water.

Jerlov & Koczy (1951), *Reports of the Swedish Deep-Sea Expedition 1947-1948*
Vol. 3, 30-71, was not obtained and is not needed: the 1968 table accounts for
the column on its own.

### A third edition exists

Aas et al. (2013) cite **Jerlov, N. G. (1978), *The optical classification of
sea water in the euphotic zone*, Rep. Dept. Phys. Oceanogr. 36, Univ.
Copenhagen, 46 pp.** In it the coastal types are reduced from nine to three,
1, 3 and 5. Not obtained. Anyone comparing a coastal-type table against this
package should establish which of the three editions it came from first.

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

**The Solonenko & Mobley Kd0 at 600 nm is the first edition too (resolved).**
Jerlov revised it, and said so in the 1976 text:

> Deviations from the previous classification (Jerlov, 1968) occur at 600 nm
> where the new Kd values are higher for types I, IA, IB and II.

Those are exactly the four types where the anomaly appears. For type I at
600 nm, the 1968 table gives 85 percent per metre, so Kd = 0.1625, and
Solonenko & Mobley print 0.163; the 1976 table gives 79 percent, so
Kd = 0.2357, and the Dstl file gives 0.235.

The same passage accounts for the type III differences at 425, 550 and 575 nm:

> type III shows lower Kd values at 550 and 575 and somewhat higher values
> around 425 nm which may be caused by chlorophyll absorption

Jerlov also records that the 600 nm region is not settled:

> it seems that the last word is not said about the behaviour of the
> irradiance attenuation in the "slope" region of 600 nm

**The point in the first paragraph of this section still stands.** Jerlov's
values fall below pure sea water at 9 of 15 wavelengths in the 1968 edition,
which is why Austin & Petzold replaced them.

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

## 5. Coastal 1C repeats oceanic III, in Jerlov's own tables (resolved)

The Kd0 of Jerlov 1C is identical to that of Jerlov III at all eight
wavelengths from 525 to 700 nm. This was recorded here as a possible
duplicated column in Solonenko & Mobley's table.

**It is in the original.** Jerlov (1968) Table XX has the two rows identical
at those eight wavelengths, and Jerlov (1976) Table XXVI still has them
identical at seven, 550 to 700 nm, having separated 525.

Surviving a revision, and being trimmed by one wavelength rather than
removed, does not read like a copying mistake. Nor is it physically
surprising: beyond about 550 nm the absorption of pure water dominates, so
water types converge there whatever their particle load.

**Solonenko & Mobley transcribed it faithfully.** The affected cells are
carried as `ok` with a note, not as `suspect`. Whether Jerlov's own tables
should show two types as exactly equal is a question for someone with the
underlying observations, which are not in either edition.

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

The sRGB matrix is not shipped. It is derived in `jerlov/colour.py` from the
primaries and white point of IEC 61966-2-1, and `tests/test_colour.py` checks
the derivation against the published rounded matrix.


## 13. The depth profiles, and a wrong DOI in the paper (confirmed)

`williamson2023_depth.csv` gives, for each near-surface Jerlov type, the type
that typically applies in each 10 m layer down to 200 m. Water that is
Jerlov I at the surface is typically IA by 20 m and IB by 40 m; turbid coastal
water clears with depth, 3C reaching II by 40 m.

Source: Williamson, C. A. and Hollins, R. C. (2023), "Depth profiles of Jerlov
water types", *Limnol. Oceanogr. Lett.* 8, 781-788, DOI `10.1002/lol2.10338`.
Open access, CC-BY. Derived from `op_STEP_6_FINAL.csv` in the accompanying
dataset rather than from the printed Table 2, which gives the same values.

**The paper's Data Availability Statement gives the wrong DOI.**

| Where in the paper | DOI | What it actually is |
|---|---|---|
| Data Availability Statement | `10.6084/m9.figshare.24128862` | **A different dataset: 1020 lake locations in the United States** |
| Reference list | `10.6084/m9.figshare.21710252` | The depth profile data |

This was found by downloading the first one. Anyone following the Data
Availability Statement gets lake positions in Maine.

### Reproducing the published table

The published Table 2 takes, for each near-surface type and layer, the deeper
type with the largest campaign count, subject to a minimum of ten campaigns.
The paper states that in 3 of 119 cases it instead chose the second-highest,
"as this count was close to the maximum and more consistent with the
surrounding depth layers", but does not say which.

Applying the stated rule and comparing against the printed table locates them:

| Near-surface type | Layer | Largest count | Published |
|---|---|---|---|
| I | 90-100 m | II | **IB** |
| I | 180-190 m | IA | **IB** |
| IA | 190-200 m | IA | **IB** |

Exactly three, exactly where the paper's asterisks are. `tools/` fixes this
count, so a change in either the data or the rule will be noticed.

Cells with fewer than ten campaigns are carried with `status = undeclared` and
an empty type rather than being filled in. There are 80 of them. Jerlov 9C is
undeclared below the top layer entirely, and the coastal types run out
quickly: 3C reaches only 70 m.

**These are typical profiles, not predictions for a place or a season.** The
paper says so, and provides per-cell cruise and month counts for anyone who
needs to judge how well supported a particular cell is.


## 14. Shortwave penetration for ocean models (note)

`paulson1977_shortwave.csv`. Ocean circulation models absorb solar radiation
in the upper ocean as a sum of two exponentials:

```
I(z) / I(0) = R exp(-z/zeta1) + (1 - R) exp(-z/zeta2)
```

Source: Paulson, C. A. and Simpson, J. J. (1977), "Irradiance measurements in
the upper ocean", *J. Phys. Oceanogr.* 7, 952-956, DOI
`10.1175/1520-0485(1977)007<0952:IMITUO>2.0.CO;2`, Table 2.

These parameters are used by ROMS, MITgcm, NEMO and CESM among others, and are
usually copied from secondary sources rather than the paper.

### The fit is repeated rather than trusted

Paulson & Simpson fitted Jerlov (1968) Table XXI, which this package now
ships. `tools/build_paulson1977.py` repeats their two-step procedure, their
Eqs (2) and (3):

| row | R refit | R printed | zeta1 refit | printed | zeta2 refit | printed |
|---|---|---|---|---|---|---|
| I | **0.58** | 0.58 | 0.36 | 0.35 | 23.2 | 23 |
| I upper 50 m | 0.67 | 0.68 | 1.38 | 1.2 | 27.4 | 28 |
| IA | **0.62** | 0.62 | 0.63 | 0.60 | 20.4 | 20 |
| IB | **0.67** | 0.67 | 1.16 | 1.0 | 17.3 | 17 |
| II | **0.77** | 0.77 | 1.80 | 1.5 | 14.4 | 14 |
| III | **0.78** | 0.78 | 1.60 | 1.4 | 7.9 | 7.9 |

**R reproduces for every row.** The two lengths land within 0.3 m and 0.6 m,
which is as much as a table printed to two significant figures allows: the
shallow fit has four points and the deep fit as few as three.

### The published parameters miss their own source at 1 m

Feeding the printed parameters back gives, against Jerlov Table XXI, an error
of **46 percent at 1 m** for types II and III, falling below 25 percent from
2 m down. Two exponentials cannot follow the sharp near-surface decay; the
paper is explicit that the fit excludes the 10 m point for the same reason.

Anyone heating a 1 m surface layer with these parameters should know this.
`tests/test_shortwave.py` pins both numbers.

### What it does not cover

**Only the five oceanic types.** The paper fitted I, IA, IB, II and III.
There are no coastal parameters, and `shortwave_parameters` raises rather than
substituting a neighbouring type.

**Type I has two rows.** The paper gives a separate fit over the upper 50 m,
"because of a change in slope of ln I vs z below 50 m", available as
`I_upper50`. Table 2 prints its label as "Type 1" with an Arabic numeral, one
line below "Type I"; the text makes clear both are the oceanic type.

**Three rows are not water types at all**: the authors' own composite
observations, their Run 1, and a Kraus (1972) value from Crater Lake. They are
shipped with `status = not_a_water_type` so a reader comparing against the
paper does not think they are missing.

## 15. The backscattering ratio is still being guessed (note)

Jia et al. (2021), *Remote Sens.* 13, 4018, DOI `10.3390/rs13194018`, needed
bb for the Jerlov types in order to compare that scheme against their own.
They wrote:

> However, the exact B values for the Jerlov water types were unknown ... we
> assumed B = 0.001, 0.01, and 0.1 to represent the different scenarios as
> much as possible.

A peer-reviewed paper spanning three orders of magnitude, because there was
nothing to look up. This is independent support for section 10 and for the
decision that `Water.bb` has no default.

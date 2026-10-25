# Data provenance

What every shipped table is, where it came from, what was verified, and what
is known to be wrong with it.

Twenty-five entries are recorded below. Nine are confirmed defects, three were
open questions that the first edition of Jerlov settled, and the rest are
notes rather than defects. None of them is repaired silently: values that
could be recovered carry `status = reconstructed` and say how, values that
could not are `missing`, and values that are used but doubtful are `suspect`.

## Files

| File | Contents | Rows |
|---|---|---|
| `jerlov1976_kd.csv` | Downwelling diffuse attenuation Kd. 1 nm, 300-715 nm, 10 types; Jerlov printed 16 wavelengths, 310-700 | 4160 |
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
| `boss2001_chi.csv` | chi for converting a single-angle measurement to bb | 12 |
| `petzold1972_vsf.csv` | Volume scattering function at 55 angles, 0.1-180 deg, 530 nm, 8 stations | 440 |
| `petzold1972_stations.csv` | c, b, a, B/S, slope and median angle of each station | 8 |
| `williamson2022_aw.csv` | Pure water absorption that Williamson & Hollins (2022) built their a on. 1 nm, 300-800 nm | 501 |
| `jerlov1977_quanta.csv` | Jerlov's measured quanta irradiance, 350-700 nm: depths of 30, 10, 3 and 1 percent, percent by depth, Kd by level and by layer. 7 types | 202 |
| `tyler1958_radiance.csv` | Tyler's measured radiance distribution in Lake Pend Oreille: 19 tilts by 10 azimuths at 7 depths, 4.24-66.1 m, relative units | 1330 |
| `darecki2011_irradiance_cv.csv` | Coefficient of variation of Ed under waves, 6 depths 0.86-9.58 m, 443, 532 and 670 nm; **read from a figure** | 18 |
| `darecki2011_radiance_cv.csv` | Coefficient of variation of radiance at 532 nm, 13 zenith angles in the sun's plane, 3 occasions; **read from a figure** | 39 |
| `gernez2009_sun_zenith.csv` | Coefficient of variation of Ed at 510 nm, its spread, and the period of the strongest fluctuation, against the sun's zenith angle, clear skies; **read from a figure** | 14 |
| `darecki2011_spectral_cv.csv` | Coefficient of variation of Ed at about 1 m, 410-670 nm, on five days of wind from 3.9 to 10.3 m/s; **read from a figure** | 30 |
| `gernez2009_conditions.csv` | As `gernez2009_sun_zenith`, against wave height, the square root of the wind speed, and Kd(490); **read from a figure** | 33 |
| `gernez2009_more_conditions.csv` | As `gernez2009_conditions`, for Ed under overcast skies (Figure 7) and Eu under clear skies (Figure 13), against the sun's zenith angle, wave height, wind speed and Kd(490); **read from a figure** | 94 |
| `gernez2009_spectral.csv` | Average CV and period of the strongest fluctuation at seven wavelengths, clear and overcast skies, of Ed at the upper depth (Figure 11) and Eu at the lower (Figure 14); **read from a figure** | 28 |
| `gernez2009_bands.csv` | Median CV of Ed at six bands, 443-683 nm, clear skies, against the sun's zenith angle, wave height, wind speed and Kd(490) (Figure 10); **read from a figure** | 282 |
| `gernez2009_diffuse_share.csv` | Share of diffuse light in the downwelling irradiance above the water, sun 20-90 degrees, as printed on Figures 8a and 10a from a model of the sky | 8 |

The four tables drawn from the two Dstl datasets (`williamson2022_iop`,
`williamson2022_measured`, `solonenko2015_iop` and `williamson2023_depth`)
and `jerlov1976_kd` were rebuilt from those datasets with the scripts in
`tools/`, and came out identical, byte for byte, to the files shipped in
0.5.1. Version 0.5.2 then changed the `status` column of `jerlov1976_kd`
only; see section 16.

## The `status` column

| Value | Meaning | How to treat it |
|---|---|---|
| `ok` | The published value, used as printed | Usable |
| `extrapolated` | The paper itself says it was extrapolated | Usable, but less accurate |
| `reconstructed` | The published value is wrong; recovered from an equation | Usable; `value_source` says how |
| `missing` | The published value is wrong and could not be recovered | Empty. Interpolate yourself or avoid that wavelength |
| `suspect` | Used as published, but an internal inconsistency was found | Read the `note` before relying on it |
| `model_extrapolation` | Outside the range of the underlying measurements | Usable, but not measured |
| `interpolated` | Not printed: linearly interpolated between printed values by the dataset the table came through | Usable; no more precise than the printed neighbours |
| `extrapolated_by_dataset` | Not printed: beyond the printed range, linearly extrapolated by the dataset the table came through | Usable, but rests on nobody's measurement; warns |
| `read_from_figure` | Not printed as a number: read off a published figure, by the method its section gives | Usable to the reading's stated precision, which the accessor carries |

## Sources

- **Jerlov 1976.** From `ip_jerlov.csv` in the Dstl dataset, figshare DOI
  `10.6084/m9.figshare.20290782`, Version 3. Checked against an independent
  transcription of Jerlov (1976) Table XXVII in `jkibele/OpticalRS` and found
  to agree. The provenance of the file is not entirely clear: Williamson &
  Hollins (2022) attribute the same figure to Jerlov (1964), while Williamson
  & Hollins (2023) attribute it to Jerlov (1976). (c) Crown copyright (2022),
  Dstl. Open Government Licence v3.0. Only 158 of its values are Jerlov's;
  the rest were filled in by Dstl, and section 16 says how.

- **Austin & Petzold 1986.** Opt. Eng. 25(3), 471-479, DOI
  `10.1117/12.7973845`. Tables VI and IV, checked against the paper in full
  (71 rows of M and Kw, 90 values of K). The type I row is pure sea water Kw;
  only the 475 nm column is Jerlov's own value. The rest was computed with the
  paper's Eq. (6), which reproduces the printed table to within 0.39 percent.
  M at 350, 355 and 360 nm is extrapolated, as the paper states. Austin &
  Petzold (1990), Proc. SPIE 1302, 79-93, tested the model against 83 new
  stations from 24.4 to 77.7 degrees north and recommended no change. The
  coefficient of variation is under 8 percent up to 590 nm except at 410 nm,
  which the paper puts down to yellow substance, and 9 percent or more
  beyond, reaching 31 percent at 670 nm. (Its abstract gives the northern
  limit as 77.4 degrees; the body says 77.7 twice.)

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

Every other cell of Tables 4 to 8, 815 of 850, equals the shipped file; the
35 that do not are these seven rows in their five columns.

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
(1968) Table XX was obtained and transcribed; all 160 cells of its
transmittance per metre were checked against the scan, and Kd is -ln of each.
It is shipped as `jerlov1968_kd.csv`, and since 0.5.0 is `water(t, source="jerlov1968")`.
Converting its transmittances to Kd and comparing:

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

The model originates in Haltrin (1999), *Appl. Opt.* **38**, 6826-6832,
Eqs. (5)-(7), checked against the paper:

```
bw(l) = 0.005826 (1/m)   * (400/l)**4.322
bs(l) = 1.151302 (m^2/g) * (400/l)**1.7
bl(l) = 0.341074 (m^2/g) * (400/l)**0.3
```

**The correct small-particle coefficient is 1.151302.** Williamson & Hollins
use 1.1513, which matches; they print all three constants rounded (0.00583,
1.1513, 0.3411), and since 0.5.1 the `williamson2022` source carries those
rather than Haltrin's. Solonenko & Mobley print 1.513; a digit appears to
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

Checks against the paper:

- All 612 cells of the printed Table 7, at 10 nm from 300 to 800 nm: **equal
  to three significant figures.** (The build script checks 72 of them.)
- b recomputed from Eqs. (8)-(11) with the paper's own constants (0.00583,
  1.1513, 0.3411) and the Bs, Bl of its Table 6: **within 0.73 percent** at
  every wavelength from 300 to 800 nm, for every type.

**Until 0.5.1 the second check used the wrong Table 6.** Hollins & Williamson
(2023), Appl. Opt. 62, 6218-6233, DOI `10.1364/AO.493186`, also has a Table
6, which refits the same model to the measured points rather than to the
spectra (IB 0.010/0.37, II 0.022/0.52, III 0.00/0.90, ...). Its Table 11
revises Jerlov III's Bl to 0.91. Those values had been entered here as the
2022 table, and against the 2022 spectra they miss by up to 5.3 percent, at
Jerlov III. This file put that down to the revision to 0.91; the real cause
was the wrong table. Nothing shipped was affected, only the check.

**Measured points exist only from 412 to 715 nm.** Everything outside that is
model interpolation or extrapolation and is marked `model_extrapolation`;
300-411 nm and 716-800 nm are affected.

`williamson2022_measured.csv` holds the raw measured points. Hollins &
Williamson (2023) state that the fitting process behind the smooth spectra
would bias some analyses and that the individual points are preferable
(section 2.A). Use these for validation; `measured_points(t, "a")` returns
them with their spread and campaign count.

The paper kept only averages built from five or more measurements ("Entries
with less than five values contributing to the final average were removed").
Reproducing that filter gives **53 points each for a and b, 106 in total,
matching the paper**, and the campaign count of every point equals the 106
counts of its Table 3.

**Hollins & Williamson (2023) Table 1 prints only 51 of the 53 a values.**
Jerlov 5C at 676 and 715 nm are shown as "-", although the 2022 Table 3 gives
them 7 and 6 values, above the threshold. Their Table 2, for b, has all 53.
This package follows the 2022 paper, which states 53 for each. The 46 excluded points are kept with
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

**Layer 1b: from a measurement, yes.** If you have an instrument, the
conversion from what it reads to bb is settled; see section 18. That does not
give bb per water type, but it means a caller with a HydroScat or an ECO-BB
need not guess.

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
about 10 percent.** All 30 cells of the summary in Table 1 (average, minimum
and maximum at ten wavelengths) were checked against the paper.

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
Open access, CC-BY; the accompanying dataset is CC BY 4.0 too, unlike the
2022 one, which is under the Open Government Licence. Derived from
`op_STEP_6_FINAL.csv` in that dataset rather than from the printed Table 2, which gives the same values.

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
The paper states that in "three out of the 119 cases" it instead chose the
second-highest, "as this count was close to the maximum and more consistent
with the surrounding depth layers", and marks them with asterisks in the
table. (Table 2 in fact has 120 declared cells, the ten surface ones
included; the 119 is the paper's.)

Applying the stated rule independently finds the same three, which is the
check that the rule has been read correctly:

| Near-surface type | Layer | Largest count | Published |
|---|---|---|---|
| I | 90-100 m | II | **IB** |
| I | 180-190 m | IA | **IB** |
| IA | 190-200 m | IA | **IB** |

Exactly three, exactly where the paper's asterisks are. All 120 cells of the
printed Table 2, asterisks included, equal the shipped file. `tools/` fixes this
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

The table Paulson & Simpson fitted, Jerlov (1968) Table XXI, is
`jerlov1968_solar_fraction(t)`, for all ten types. Its footnote gives a solar
altitude of 90 degrees for the oceanic types and 45 for the coastal ones, so
the parameters describe a sun at the zenith. All 120 cells, blanks included,
were checked against a scan of the 1968 edition.

Source: Paulson, C. A. and Simpson, J. J. (1977), "Irradiance measurements in
the upper ocean", *J. Phys. Oceanogr.* 7, 952-956, DOI
`10.1175/1520-0485(1977)007<0952:IMITUO>2.0.CO;2`, Table 2.

These parameters are used by ROMS, MITgcm, NEMO and CESM among others, and are
usually copied from secondary sources rather than the paper. All nine rows of
Table 2 were checked against the paper.

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
2 m down. Two exponentials cannot follow the sharp near-surface decay. The
paper says "the fit is least accurate in the upper 10 m" and that it fitted
the table "neglecting the 10 m value", adding that the fit at 10 m "could be
improved by including" it. It gives no reason for the exclusion; this file
once supplied one.

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
paper does not think they are missing, and `shortwave_parameters` refuses
them unless asked with `include_non_types=True`, so that none can be taken
for a Jerlov type by accident.

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


## 16. A published table off by a factor of ten (confirmed)

Woźniak, B. and Pelevin, V. N. (1991), "Optical and bio-optical
classifications of natural waters", *Oceanologia* **31**, 25-55, reprints
Jerlov's Kd spectra as its Table 1. Two things in it are wrong.

**The unit is off by a factor of ten.** The header reads
`Kd(λ) [10⁻³ m⁻¹]`. The values are Jerlov's, and Jerlov (1976) Table XXVII
states `Kd · 10² m⁻¹`, so they are in units of 10⁻² m⁻¹.

Type I at 475 nm is printed as 1.8 in both. Under Jerlov's header that is
0.018 1/m, which agrees with Austin & Petzold's replacement value of 0.0184
and with the transmittance of 98.2 percent per metre in the same edition.
Under the Woźniak & Pelevin header it is 0.0018 1/m, **below the absorption
of pure sea water**, which is not possible for any water.

**Jerlov IB at 700 nm is printed as 59 where the original has 58.** A single
digit; the other 157 cells are exact.

Neither defect is in the values themselves. Anyone reading the numbers off the
page and applying the stated unit gets a Kd ten times too small.

### The values themselves check out

This was the first chance to check `jerlov1976_kd.csv`, which comes to us
through the Dstl dataset, against an independent transcription.

| Source | Agreement with the shipped file |
|---|---|
| Jerlov (1976) Table XXVII, from the scan | all 158 cells, **exactly** |
| Woźniak & Pelevin (1991) Table 1 | 157 of 158 cells |
| Paglierani et al. (2023) Table 10 | all 158 cells, unit stated correctly |

Three transcriptions, one of which has the unit wrong and one digit off. The
shipped file agrees with the two that are right.

**The comparison also found a bug in this package.** Jerlov 7C has no data
below 350 nm, and `kd(350)` was returning `nan` although 350 nm is tabulated:
the guard that stops interpolation bridging a gap was also being applied to
queries that land exactly on a sample, which are not interpolated at all.
Fixed, with both halves of the behaviour pinned in `tests/test_api.py`. It had
gone unnoticed because nothing had previously been checked against a printed
table cell by cell.

### What the shipped file adds to the table

Jerlov printed Table XXVII at 16 wavelengths, 310 to 700 nm. The Dstl file
the package takes it from is at 1 nm from 300 to 715 nm, and rebuilding it
from that file (`tools/build_jerlov1976_and_solonenko2015.py`) shows how the
rest was made:

| Rows | What they are | `status` |
|---|---|---|
| 158 | Jerlov's printed values, checked against the table | `ok` |
| 3672 | Between printed wavelengths: linear interpolation, to within 0.22 percent | `interpolated` |
| 230 | 300-309 and 701-715 nm: linear extrapolation from the two end values, to within 0.03 percent | `extrapolated_by_dataset` |
| 100 | No value: 7C and 9C below 350 nm | `missing` |

**Until 0.5.2 all 4060 values were marked `ok`.** The 230 extrapolated ones
rest on nobody's measurement, and the package's rule is that it does not
extrapolate (DECISIONS.md section 5); they now raise a `ProvenanceWarning`.
The interpolated ones are as good as the printed values either side of them
and do not warn, but they are no longer described as published values.

### More editions than expected

Woźniak & Pelevin cite the classification as Jerlov 1951, 1961, 1968, 1976,
1977 and 1978, and say the final version is the 1978 one. Adding Jerlov (1964),
where IA and IB were introduced, that is **seven editions**. Two of them are
new here:

- Jerlov, N. G. (1961), "Irradiance in the sea in relation to particle
  distribution".
- Jerlov, N. G. (1977), "Classification of sea water in terms of quanta
  irradiance", *J. Cons. int. Explor. Mer*.

Neither obtained. (The second has since been obtained and is section 22. Its
pages print no year, and until 0.9.6 this said the 1977 was Woźniak &
Pelevin's. The publisher's record settles it: *Journal du Conseil* 37(3),
September 1977, doi:10.1093/icesjms/37.3.281. The latest observations it
uses are from June 1976.) **Before comparing any Jerlov table against this package,
establish which edition it came from.** Section 2 is what happens when that is
not done.

## 17. Three routes to a and b, disagreeing by a factor of five (confirmed)

Sections 2 and 6 concern two published sets of coefficients for the same water
types. There is a third, and the field knows.

Abd El-Mottaleb et al. (2024), *Results in Engineering* **24**, 102941, DOI
`10.1016/j.rineng.2024.102941`, assign a chlorophyll concentration to each
Jerlov type (0.03, 0.1, 0.4, 1.25 and 3 mg/m³ for I through III) and run a
bio-optical model. Their Table 2 gives the beam attenuation at 532 nm.
Against the two sources this package ships:

| Type | Chlorophyll model 2024 | Williamson & Hollins 2022 | Solonenko & Mobley 2015 | Spread |
|---|---|---|---|---|
| I | 0.0576 | — | 0.0524 | 1.1x |
| IA | 0.0825 | — | 0.0550 | 1.5x |
| IB | 0.1895 | 0.1772 | 0.1069 | **1.8x** |
| II | 0.5297 | 0.2408 | 0.4301 | **2.2x** |
| III | 1.8998 | 0.3712 | 1.0922 | **5.1x** |

(c in 1/m. All three are peer reviewed.)

**A factor of five at Jerlov III.** A communication range, a visibility
estimate or a synthetic image built on one of these is not comparable with one
built on another, and none of the three papers says which of the others it
disagrees with.

Paglierani et al. (2023), *Quantum Engineering* **2023**, 7185329, DOI
`10.1155/2023/7185329`, a review of underwater quantum key distribution,
makes the same observation about a different scheme:

> some works strictly adopt the values proposed by Mobley ... Other works,
> conversely, though adopting the same water types, use slightly different
> numeric values for those coefficients.

The "water types" there are Mobley's four (pure sea water, clear ocean,
coastal, turbid harbour; their Table 11), not Jerlov's: their next sentence
begins "With respect to Jerlov classification". This file once quoted it as if
it were about the Jerlov coefficients. It is the same failure in a
neighbouring scheme, and the reason `jerlov.water()` requires a source and
`Water` carries the one it came from.

The chlorophyll route is not shipped. It is a model with a free parameter
assigned per water type, not a measurement or an inversion of one, and the
assignment differs between papers that use it. It is recorded here so that a
reader meeting those numbers can tell which family they belong to.


## 18. Converting a single-angle measurement to bb (note)

`boss2001_chi.csv`. Backscattering sensors measure the volume scattering
function at one angle in the backward hemisphere. The conversion is

```
bb = 2 pi chi_p(theta) [beta(theta) - beta_w(theta)] + bb_w
```

Source: Boss, E. and Pegau, W. S. (2001), "Relationship of light scattering at
an angle in the backward direction to the backscattering coefficient",
*Appl. Opt.* **40**, 5503-5507, DOI `10.1364/AO.40.005503`, Eq. (10) and
Table 1. Table 1 and the constants of Eqs. (4) and (5) were checked against
the paper.

### chi_p, from 41 measured scattering functions

| angle | 90 | 100 | 110 | 120 | 130 | 140 | 150 | 160 | 170 |
|---|---|---|---|---|---|---|---|---|---|
| chi_p | 0.71 | 0.90 | 1.03 | 1.12 | 1.17 | 1.18 | 1.13 | 1.00 | 0.62 |
| spread % | 4.3 | 2.6 | 3.1 | 4.2 | 3.3 | 3.5 | 4.2 | 6.4 | **34.8** |

**The error at 170 degrees is an order of magnitude worse than at the other
angles,** where it runs from 2.6 to 6.4 percent. The shape of the scattering
function varies most near the ends, so a measurement there pins bb least
well.

The two papers recommend different things, and this file once ran them
together. Maffione & Dana (1997), *Appl. Opt.* **36**, 6057-6067, recommend
sensors covering "roughly 110-160°". Boss & Pegau recommend measuring near
117 degrees, and otherwise removing the water contribution first, which they
support "for angles spanning from near 90° to 160°".

`bb_from_vsf` warns above 10 percent and refuses outside 90 to 170, the span
of Table 1. It is not the span of the measurements: the instrument behind
them measured from 90 to 177.3 degrees, and it is Petzold's measurements, an
older set, that stop at 170.

### The water half is analytic, and checked against itself

Morel's formula, the paper's Eqs. (4), (5) and (9):

```
A(lambda, S)  = 1.38 (lambda / 500 nm)^-4.32 (1 + 0.3 S / 37 psu) 1e-4
beta_w(theta) = A [1 + cos^2(theta) (1 - delta) / (1 + delta)]
chi_w(theta)  = [1 + (1/3)(1-delta)/(1+delta)] / [1 + ((1-delta)/(1+delta)) cos^2(theta)]
```

with delta = 0.09, the depolarisation ratio Morel suggests from a range of
0.07 to 0.11.

Because chi_w is exact, it must give the same bb_w at every angle, and that
value must equal the direct integral of the definition. It does, to one part
in 10^15. **Any transcription error in these three equations breaks that
check**, which is why they are checked rather than trusted.

The amplitude carries about 15 percent uncertainty, which the authors give as
the agreement between measurement and theory. That is not in the quoted error
on chi_p, and neither is your instrument's calibration.

### Three published values for the same conversion

| Source | Angle | Value | Quantity |
|---|---|---|---|
| Oishi (1990), quoted by Maffione & Dana | 120 | 1.14 | chi |
| Boss & Pegau (2001) | 120 | 1.12 | chi_p |
| Oishi (1990) | 140 | 1.08 | chi |
| Maffione & Dana (1997) | 140 | 1.08 | chi |
| Boss & Pegau (2001) | 140 | **1.18** | chi_p |

**chi and chi_p are not the same quantity**: one includes scattering by the
water and the other does not, so these are not simply in conflict. But they
are printed under the same symbol in the same field, and the 9 percent gap at
140 degrees is the water term. Anyone lifting a number without reading which
one it is will be wrong by about that much. The rows from other authors are
shipped with `status = other_definition` so they can be compared rather than
mistaken for each other.

The papers also explain why instruments cluster near 120 degrees: chi_w and
chi_p cross at about 118, and at the crossing the water contribution does not
have to be known. Reproducing that crossing from the shipped table gives
116.9 degrees.

### What this does and does not settle

**It settles the measurement route.** A caller with a HydroScat, an ECO-BB or
a VSF meter no longer has to state a backscattering ratio; they can convert
what they measured.

**It does not settle section 10.** There is still no bb for a Jerlov water
type, because a water type is defined by Kd and Kd barely depends on bb.
`Water.bb` still requires an explicit ratio.

## 19. Three Kd columns in Solonenko & Mobley (note)

Tables 4 to 8 of Solonenko & Mobley (2015) give Kd three times over, and they
are three different things (Section 4 and Appendix A of the paper):

| Column | What it is | Here |
|---|---|---|
| K_d^0 | Jerlov's reference values; parenthesised ones are extrapolated | `water(t, source="jerlov1968")`, section 2 |
| K_d | Kd of the paper's bio-optical model, Eq. (4), with the retrieved a and b; within 15 percent of K_d^0 | `.kd()` |
| K_d^H | Kd computed by HydroLight from the retrieved a and b | `.kd_hydrolight()` |

K_d^H is the paper's check on its own retrieval. HydroLight was run with the
retrieved a and b, the Petzold average-particle phase function, a clear sky,
infinitely deep water and no inelastic scattering. The modelling depth was 10
scattering lengths for every type except Jerlov III, where 6 matched Jerlov
better.

**The tabulated values do not quite reach the paper's figure for them.** The
paper says that 90 percent of the points in its Fig. 5 lie within 20 percent
of K_d^0. Recomputing `100 (K_d^0 - K_d^H) / K_d^0` from the tables gives
86.5 percent of all 163 cells where both are given, and 87.9 percent of the
141 where neither is flagged. The difference is probably which points made it
onto the plot; the tables are what is shipped. `tests/test_quoted_figures.py`
pins both numbers.

The KdH cells of the duplicated rows of section 1 are unrecoverable and are
shipped as `missing`.

A small slip in the same paper: its reference 2, Austin & Petzold (1986),
gives the pages as "253471"; they are 471-479.

## 20. The pure water absorption behind Williamson & Hollins (note)

A Jerlov type's a is that of pure water plus what is in it. Williamson &
Hollins (2022) build theirs as `a = aw + aChl + aCDOM`, Eqs. (4)-(6), and say
of aw only that it "was taken from Buiteveld et al." (1994, Proc. SPIE 2258,
174-183). `williamson2022_aw.csv` is the aw they actually used: the lookup
table in columns AK to AN of the sheet `a,b measured and model` of
`20221121-Dstl_MIOP_analysis_v3.xlsx`, 1 nm from 300 to 800 nm, the same grid
as their a. `pure_water_absorption()` returns it.

**It is the aw their a was built on.** With it and the Chl, M and alpha of
their Table 6, Eqs. (4)-(6) give back the shipped a of every type to a median
of 0.10-0.28 percent; the worst single wavelength is 4.1 percent, for Jerlov
1C at 301 nm, which is what Table 6's two or three printed figures allow.
`tools/build_williamson2022_aw.py` stops if either figure grows past 0.5 or 5
percent, or if aw exceeds any type's a beyond the rounding of a.

**From 720 nm their model gives the water's contents no absorption**: the
chlorophyll coefficient A of the same lookup table is zero there, so every
type's a is aw itself, to the three figures a is given to.

**The measurements at 715 nm do not agree.** The measured average a at 715
nm, `measured_points(t, "a")`, is 1.018 for Jerlov III and exactly 1.004 for
1C, 3C and 5C, with a spread across campaigns of zero (of order 1e-16) over
23, 28 and 6 campaigns; 7C's single campaign is 1.004 too. Identical values
with no spread are not what independent measurements give, and neither
paper says why. The fitted a there is 0.880 to 0.884, which is aw itself,
so the measured points lie 14 to 16 percent above the fit. Hollins &
Williamson (2023), whose Table 1 prints these as 1.02, 1.00 and 1.00,
discarded the 715 nm data from their Kd analysis "because the value of Kd
was usually less than a". Both are shipped as published.

**It has not been compared with Buiteveld's own table**, which has not been
obtained. Hollins & Williamson (2023) say that in their later study they
adjusted some of Buiteveld's values above 500 nm, so that Kd - aw was
smoother in the red; whether this 2022 table already carries such
adjustments is not stated, and is not assumed here.

Why only one source. Solonenko & Mobley (2015) averaged Pope & Fry (1997),
Buiteveld et al. (1994) and Pegau et al. (1997), and show the result only as
a curve in their Fig. 2; reading numbers off a figure is not done here. The
Jerlov and Austin & Petzold sources give Kd only, and Austin & Petzold's Kw is
the diffuse attenuation of pure sea water, not its absorption. Each of these
raises `MissingQuantityError`, saying which case it is.

Pope & Fry (1997) on its own, the most cited pure water spectrum, is not
shipped either: none of the sources here used it alone, and one source's a
minus another's aw is partly a difference between two laboratories' pure
water, not the absorption of what was in the water.

## 21. Petzold's volume scattering functions (note)

`petzold1972_vsf.csv` and `petzold1972_stations.csv` are transcribed from
Petzold, T. J. (1972), "Volume scattering functions for selected ocean
waters", SIO Ref. 72-78, Scripps Institution of Oceanography, Visibility
Laboratory; DTIC AD0753474. The report is marked "Approved for public
release; distribution unlimited". `petzold_scattering(station)` returns one
station.

**What was transcribed.** The eight ocean stations of the report's Figs. 22
to 37: three in the Tongue of the Ocean, Bahamas (AUTEC 7, 8, 9), two off
southern California (HAOCE 5 in Avalon Cove, Catalina Island, and HAOCE 11
in the channel between Catalina and the coast) and three in San Diego Harbor
(NUC 2200, 2040, 2240). For each, sigma(theta), its running integral and
that integral over s at the report's 55 angles, and from the summary page c,
s and a at 530 nm, B/S, the slope used below 0.1 degree and the median
angle. The laboratory runs of Figs. 38 to 51 (fresh water, filtered sea
water) are not ocean water and are not shipped.

**How it was checked.** All 1320 table entries were read from the page
images and compared with the report's own OCR text: every entry the OCR
rendered legibly agreed, and the ones it garbled were read again at higher
magnification. `tools/build_petzold1972.py` carries the numbers as literals
and then requires, for every station:

- sigma at the 21 angles it shares with the summary page's "ITERATED DATA"
  column, a second printing of the same numbers, to agree to one unit in the
  fifth figure;
- the normalised integral to equal the integral over s;
- each step of the integral to follow from sigma, taken as a power law
  between printed angles: within 1 percent below 10 degrees, 3 percent
  beyond;
- sigma/s at 20, 40, 45 and 90 degrees, s, a = c - s, B/S and the median
  angle to agree with the summary page;
- below 10 degrees, each sigma to lie within 1.5 percent of a smooth curve
  through its neighbours, and from 35 to 175 degrees each sigma between two
  twice-printed angles within -5 and +2 percent of their geometric mean
  (0.85 percent, and -3.9 and +1.0, as printed);
- where nothing was measured below 0.169 degree, the values there to follow
  the printed slope.

Altering one digit at random and rerunning the script, every change to the
first figure of sigma or of the integral, every change to the integral's
first four figures, and 28 of 30 changes to the second figure of sigma made
it fail. Changes of under about 1 percent to sigma mostly pass; for those the
values rest on the two readings, and at 21 angles on the second printing.

**Two things in the report itself.** At AUTEC 7 and 10 degrees the two
printings differ in the fifth figure, 9.9396E-02 and 9.9395E-02; the table's
value is shipped. And the running integral of NUC 2200 and NUC 2040
alternates about the true value beyond about 90 degrees: pairs of 5-degree
steps agree with sigma, single steps do not. It is in the printout, not the transcription, since the normalised
column alternates with it. Neither affects sigma.

**What is measured and what is not.** Only 0.169 degree and up was usable in
the clearer waters (the report's section 5.1), so at the AUTEC and HAOCE
stations sigma at 0.1, 0.126 and 0.158 degree is the report's power-law
extension; those 15 rows are `extrapolated` and warn. Below 0.1 degree
nothing is tabulated, but the report extends sigma to zero with the same
slope and counts it in s: 3.4 to 14.5 percent of s, in line with its "3 to
15 percent". The report puts the low-angle data at plus or minus 20 percent,
30 at 0.169 degree in the clearest water, and the general-angle data at 5.

**What these are not.** They are the scattering of eight particular waters on
particular days in 1971, total of water and particles, at 530 nm, the
wavelength the report gives for c; the scattering meters measured through a
band in the green (its Fig. 3). Petzold classified nothing: no station is a
Jerlov type, and none is mapped to one here. AUTEC 7, though in the Tongue of
the Ocean, was over 7 fathoms of water; AUTEC 8 and 9 were over 850 and 1045.

B/S across the eight runs from 0.013 to 0.044, a factor of three, which is
the same point as section 10 made from the other direction: a backscattering
ratio is a property of a water, not of a classification.

The phase function Solonenko & Mobley (2015) used with HydroLight (section
19) they describe as the average of Petzold's coastal, harbor and ocean
phase functions. That average is not in this report, which stations and
what processing went into it is not stated there, and it is not shipped.

## 22. Jerlov's measured quanta irradiance, and the package against it (confirmed)

`jerlov1977_quanta.csv` is transcribed from Jerlov, N. G. (1977),
"Classification of sea water in terms of quanta irradiance", *J. Cons. int.
Explor. Mer* 37(3), 281-287, doi:10.1093/icesjms/37.3.281, by
`tools/build_jerlov1977.py`. From profiles measured with quanta meters at
stations in fourteen regions, Jerlov tabulated, for types
I, IA, IB, II, III and coastal 1 and 3:

- Table 2: the depths at which 30, 10, 3 and 1 percent of the surface quanta
  remain, and the same divided by the 10 percent depth;
- Table 3: the percentage remaining at 0 to 100 m;
- Table 4: Kd between those levels;
- Table 5: Kd for quanta layer by layer.

The band is 350-700 nm, that of the Danish and French quanta meters, not the
400-700 nm of PAR. The coastal types are printed "1" and "3"; they are
written 1C and 3C here, as everywhere else. `jerlov1977_quanta()` returns
Tables 2, 3 and 5.

**The transcription.** The publisher's scan has a text layer that reads
decimal points as hyphens ("17-5" for 17.5) and drops some of them ("16 5"),
so every table was read from the page images and the text layer used only
to cross-check.

**The tables against each other (confirmed).** Table 4 should follow from
Table 2's depths, Table 5 from Table 3's percentages, and Table 2's
normalised column from its own depths. The build script recomputes all
three, allowing for the rounding of every printed value, and eight values
fall outside:

| Table | Type | Where | Printed | Recomputed |
|---|---|---|---|---|
| 2, normalised | I | 3 % level | 1.65 | 1.59-1.64 |
| 2, normalised | I | 1 % level | 2.15 | 2.07-2.13 |
| 2, normalised | IA | 3 % level | 1.66 | 1.58-1.64 |
| 4 | IA | 30-10 % | 0.043 | 0.0439-0.0459 |
| 4 | IB | 30-10 % | 0.053 | 0.0549-0.0610 |
| 5 | IA | 20-30 m | 0.046 | 0.0436-0.0446 |
| 5 | II | 5-10 m | **0.099** | **0.0759-0.0863** |
| 5 | 1C | 10-15 m | 0.154 | 0.1568-0.1616 |

All but one are near misses. II at 5-10 m is not: Table 3 has 48 percent at
5 m and 32 at 10, which cannot give 0.099. Integrating Table 5 down from the
surface would put 10 m at 29 percent, not 32.

The paper does not say which table is right. Jerlov formed the tables from
means over water masses (his Figs. 4 and 5), and a mean of ratios is not the
ratio of means, which may explain the near misses; it cannot explain II.
The values are shipped as printed, marked `suspect`, and the three in Table
5, the only ones `jerlov1977_quanta()` returns, warn. Table 3 then puts
every level of Table 2 within 0.4 m, so the two are consistent with each
other.

**The package against the measurements.** These are the first published
measurements in the package that `par_profile` and `descend` can be
checked against. `tests/test_quanta.py` computes the four levels from
Jerlov's (1976) Kd, with D65 standing in for the surface spectrum,
integrated over 350-700 nm:

- From II to 3C, one Kd all the way down agrees with Table 2 within 2 m at
  every level.
- For I, one Kd puts the 1 percent level at 165 m; Jerlov measured 103.
  Through the depth profile of Williamson & Hollins (2023), in which I
  typically turns IA and then IB below 20 m, it is 106 m, and the 10
  percent level 49 m against 49. That is independent support for `descend`.
- IA and IB stay too deep: layer by layer, 100 m against 87 and 93 m
  against 70, 15 and 33 percent.

For IB the reason can be seen in Table 5. Above 10 m, the depth on which the
classification is defined, Kd for quanta from Jerlov (1976) agrees with the
measured one within 0.004 1/m. Below 15 m the computed Kd keeps falling,
from 0.051 to 0.041, as the light narrows to the blue; the measured one
rises, from 0.056 to 0.069. The water Jerlov counted as IB became more
turbid with depth, and the profile of Williamson & Hollins keeps IB as IB to
200 m. Using Jerlov (1968) instead gives the same picture, so it is not the
edition.

**Unresolved.** Why the IB stations became more turbid with depth is not
stated. Jerlov's discussion (p. 286) notes that "ocean water is not
optically homogenous as particle accumulations occur at different levels";
a deep chlorophyll maximum would do it, but the paper does not say, and
nothing is assumed here. The comparison uses D65 for the sky. Tilting it
by (wavelength / 550 nm)^n, n from -2 to 2, moves IB's 1 percent level
between 98.9 and 84.7 m, and where it keeps the 10 percent level within 2
m of Jerlov's 33 it is 89.2 m; the same tilt stands for a quanta meter
whose response differs from a flat one, and gives the same levels. So
neither the sky's spectrum nor the meter's response explains the
difference over that range (DECISIONS.md section 53). The package's IB is
already 4.4 m too deep at the 10 percent level, 37.4 m against 33, and the
difference grows with depth.

## 23. Tyler's measured radiance distribution (note)

`tyler1958_radiance.csv` is transcribed from Tyler, J. E. (1958),
"Radiance distribution as a function of depth in the submarine
environment", SIO Reference 58-25, Visibility Laboratory, Scripps
Institution of Oceanography, Tables IV-X, by `tools/build_tyler1958.py`.
The scan read is eScholarship's, https://escholarship.org/uc/item/6vw86973,
whose pages 24-30 hold the tables. The report was later published as
Bull. Scripps Inst. Oceanogr. 7, 363-412 (1960); that version was not
read.

**The measurement.** Lake Pend Oreille, Idaho, from a barge over 750 ft of
water, on 28 April 1957 under a sky with no overhead cloud and a lake
"practically flat calm" (p. 15). A photometer with radiance tubes of 6.6
degree acceptance (p. 7), behind a Wratten No. 45 filter, measured a band
whose extreme limits are 430 and 546 nm, half width 64 nm (p. 5). Each
table gives the radiance at tilts of 0 to 180 degrees by 10, 0 looking
straight up, and azimuths of 0 to 180 by 20 from the sun, at one of seven
depths from 4.24 to 66.1 m, every one adjusted to a sun altitude of 56.6
degrees (pp. 14-15). The unit is relative and, as the tables are
normalised to one vertical run, shared by all seven; the report does not
name it. The beam transmittance was 67.3 percent per metre at the surface
and about 68.6 at 61 m (p. 8), c = 0.396 1/m and 0.377 1/m; the
transmissometer's band is not given. Bathythermograph, transmittance and
particle samples showed no stratification (pp. 7-9).

**The transcription.** Every value was read from the page images. The
text layer reads the thousands separators as decimal points and loses
whole rows, so it was used only to cross-check: of the 920 values in rows
it gives cleanly, four disagreed, and the image settled all four in favour
of the reading here (four were the text layer dropping or misreading a
digit). The build script checks that straight up and straight down have
one value at every azimuth, that the radiance never rises away from the
sun's azimuth at any tilt and depth, and that the zenith radiance falls
with depth. All hold.

**What is flagged.** Nine cells are `suspect`:

| Where | Why |
|---|---|
| Tilts 20 and 30 at azimuth 0, at 4.24, 10.4, 16.6 and 29.0 m | The sun's direction. "The reading obtained in the sun's direction could be low by a factor of 2 in the worst case", from the glitter of the sun on the surface (p. 16); Table XI gives that noise at 4.24 to 28.95 m, from 93.6 down to 10.5 percent of the mean |
| 4.24 m, tilt 160, azimuth 160 | The last digit is overstruck and reads as 3,230 or 3,290; 3,230, which continues the row, is kept |

**What the tables include that a model may not.** The clear sky's light,
not only the sun's. The barge's shadow and image, which Tyler read
around: about 54 degrees of the horizontal sweep were affected (pp. 12-13).
The depths 10.4, 16.6 and 29.0 m are printed as 10.43, 16.65 and 28.95 in
Tables III and XI; the radiance tables' labels are used here.

## 24. Darecki et al.'s light fluctuations, read from their figures (note)

`darecki2011_irradiance_cv.csv` and `darecki2011_radiance_cv.csv` are read
from Darecki, M., Stramski, D. and Sokolski, M. (2011), "Measurements of
high-frequency light fluctuations induced by sea surface waves with an
Underwater Porcupine Radiometer System", J. Geophys. Res. 116, C00H09,
doi:10.1029/2011JC007338, Figures 13a (p. 12) and 15 (p. 14), by
`tools/build_darecki2011.py`. The paper prints no table of either. These
are the first values in the package read from a figure rather than a
table (DECISIONS.md section 42).

**How they were read.** Both figures are drawn in the PDF as vector
graphics, so every marker is a drawing command with exact coordinates.
They were listed with PyMuPDF's `get_drawings`, and the build script
carries them, in PDF points, as literals. Each axis is calibrated by a
least-squares line through its major tick marks; the ticks themselves lie
within 0.03 pt of that line, which is 0.0001 in the CV of Figure 13a and
0.001 in Figure 15. The values are kept to four places. Circles and
squares are placed at the centre of their box. The downward triangles of
532 nm are placed at their centroid, a third of the way down: the three
wavelengths were measured at the same depths, and the centroid puts them
within 0.005 m of each other where the box centre would put 532 nm 0.05 m
deeper. What cannot be known from the page is how exactly the plotting
program placed the markers.

**What the build checks.** The three wavelengths share their depths; CV
falls with depth at every wavelength; it is higher in the red than the
blue at every depth, as the text says (p. 12). The thirteen radiance
markers of each panel fall within 0.1 degree of the whole angles of the
sensors; each panel's largest CV lies between 15 and 40 degrees, around
the refracted sunbeam (p. 14), and panels b and c exceed 3, "can exceed
300%" (p. 14).

**The measurements.** Figure 13a: the Santa Barbara Channel, 11 September
2008, 11:35 to 12:56 local time, sunny, sun 30-33 degrees from the zenith,
wind 4.1-6.4 m/s, c(555) = 0.68 1/m; irradiance collectors 2.5 mm across,
sampled at 1 kHz. The depths are 0.86, 1.70, 2.84, 3.78, 6.73 and 9.58 m
as read. Figure 15: radiance at 532 nm, field of view 4.5 degrees in water
(p. 4), in the plane of the sun, positive towards it, on three occasions
the caption gives and `darecki2011_radiance_cv` carries: depth 0.93, 0.59
and 0.54 m; sun 33, 41 and 35 degrees; refracted sunbeam 24, 29 and 25.

**Figure 13b** (`darecki2011_spectral_cv.csv`), read the same way from
the same page: CV at the six irradiance channels, 410, 443, 488, 532, 610
and 670 nm (p. 3), on five days. Each curve is labelled in the panel with
its wind speed, and the marker that goes with each label was matched on a
rendering of the panel: circles 3.9 m/s, squares 5.4, upward triangles
6.3, downward triangles 7.2, diamonds 10.3. Upward triangles are placed by
their centroid two thirds of the way down. Every marker falls within a
nanometre of a channel; on every day CV is larger in the red than the
blue, and the windiest day has the smallest CV at every wavelength. The
caption gives each day's date and local time, and for all five a depth of
0.91-1.25 m, a sun 42-46 degrees from the zenith and c(555) of 0.55-0.78
1/m, not which day had which.

**What they depend on that the package does not know.** The collector's
size: larger collectors read smaller fluctuations, and "a collector of a
few millimeters in diameter or smaller is required" near the surface
(Figures 10-12, paragraph 30, p. 11). The wind, the waves and the sky:
Figure 13b, which is not read, shows CV at about 1 m changing with the
wind on five days.

## 25. Gernez & Antoine's light fluctuations, read from their figure (note)

`gernez2009_sun_zenith.csv` and `gernez2009_conditions.csv` are read from
Gernez, P. and Antoine, D. (2009), "Field characterization of wave-induced
underwater light field fluctuations", J. Geophys. Res. 114, C06025,
doi:10.1029/2008JC005059, Figure 8 (p. 9), by `tools/build_gernez2009.py`;
`gernez2009_more_conditions.csv`, `gernez2009_spectral.csv`,
`gernez2009_bands.csv` and `gernez2009_diffuse_share.csv` from Figures 7,
10, 11, 13 and 14 by the same script (0.19.0, below).

**Medians, and a shifted series.** Figure 8 is "as in Figure 7", whose
caption says "The symbols are the median values, and the vertical bars are
the standard deviations" and "the Tmax curve is shifted to avoid that
error bars for CV and Tmax are superimposed" (p. 8). The values are
medians over the one-minute sequences in each class. Version 0.16.0 called
the values of Figure 8a means here and in its accessor; they are the same
numbers, and they are medians. The squares of Tmax are drawn shifted
sideways from their class, so each is assigned to the class of the circle
it follows.

**How it was read.** The figure is a greyscale raster in the PDF, 877 by
821 pixels at 150 per inch. The build script carries pixel rows and
columns as literals, read by locating dark pixels (below 150 of 255) and
checked by overlaying the readings on the image. The axes are calibrated
on their tick marks: one pixel is 0.115 percent of CV and 0.013 s of
Tmax.

- CV and its standard deviation: each solid bar is drawn the same length
  either side of its circle, so where its ends are clear its midpoint is
  the median. In panel a the circle was found within a pixel of the
  midpoint at every angle. In panels b to d, where markers and the other
  series' bars cross, the circle is found by its outline, and the bar is
  read only where its midpoint lies within 1.5 pixels of it; at three
  classes it does not, and their standard deviation is left empty (the
  accessor gives nan). Read to one pixel.
- Tmax: the centre of the square marker, from its vertical sides. At 30,
  45, 55 and 70 degrees only one side could be told from the dashed bar,
  and the value is read to two pixels. The `tmax_reading_s` column says
  which.
- The standard deviation of Tmax is in the figure but not read: the dashed
  bars end between dashes, and their ends cannot be placed closer than a
  dash.

**What the build checks.** The text's own figures. Panel a: CV "maximal
at 25%" at the highest sun, "down to 5%" near the horizon, Tmax rising
"from 1s to 3s" (p. 7); beyond 35 degrees CV only falls and Tmax only
rises. Panel c: CV "reaches a maximum of about 22% when the wind speed is
around 3 m s-1" (p. 7), read as 22.8 percent at a square-rooted wind of
1.6, 2.6 m/s; Tmax 1.6 s near 8 m/s (p. 8). Panel d: CV down to about 12
percent at the most turbid end of Kd(490), and Tmax from about 1 s to
1.5 s by 0.065 1/m (p. 8). Each circle stands at its class to within a fifth of a class.

**Where the text and the figure differ.** The text says CV decreases "from
30% to 12 %" as Kd(490) goes from 0.03 to 0.15 (p. 8); the figure's
largest CV in panel d is 24.0 percent, at 0.025. It says Tmax is "minimal
at 1.2s for wind speeds between 2 and 4 m s-1" (p. 8); the lowest Tmax
read in panel c is 1.12 s at a square-rooted wind of 1.2, about 1.4 m/s,
next to 1.15 s at 1.6, about 2.6 m/s. And it puts the upper radiometers
"around 4 m" (p. 8) where the description of the buoy gives 2.7 to 3.7 m
(p. 3). The values shipped are the figure's; the build checks the text
only where the two agree.

**The measurements.** The BOUSSOLE buoy in the Ligurian Sea, from 2003;
downwelling irradiance at 510 nm, collectors 8 mm across, sampled 6 times
a second for a minute every 15 minutes, so that fluctuations shorter than
a third of a second are not resolved (p. 4); nominal depth between 2.7 and
3.7 m, which changed between deployments (p. 3); clear skies only, the
above-water irradiance at least 0.85 of a clear-sky model (p. 6).

**Figures 7, 11, 13 and 14 (0.19.0).** Figure 7 is Figure 8 for the
overcast subset, the above-water irradiance below 0.6 of the clear-sky
model (p. 6); Figure 13 is Figure 8 for the upwelling irradiance Eu under
clear skies, at the upper depth; both against the sun's zenith angle, the
wave height, the wind speed itself (not its square root, as in Figure 8c)
and Kd(490), on 0-8 percent of CV. Figures 11 and 14 give CV and Tmax at
the seven bands, 412 to 683 nm, for both subsets: Figure 11 of Ed at the
upper depth, Figure 14 of Eu at the lower depth, 8 to 8.7 m (p. 3). All
four are greyscale rasters, read as Figure 8 was, with the same rule for
the standard deviation of CV: read only where the solid bar's midpoint
lies within 1.5 pixels of its symbol (within 1 pixel in Figures 11 and
14). Figure 7's symbols are filled; Figure 13's are open and were found by
their outlines; ten of its squares, whose outlines run into the dashed
bars, were read by eye from the pixels to a pixel. In Figure 13 the
standard deviation is left out at 85 degrees, where the bar runs from
above the square to the axis 13 pixels off centre, and at Kd 0.035, where
the bar is faint and 2 pixels off. In Figures 11 and 14 the overcast bars
are dotted, a dot every four pixels, and are not read; in Figure 11b the
clear-sky bars at 665 and 683 nm run past the axis at 0 s and are read
from their upper end, the bars being drawn the same length either side.
Figure 14's overcast symbols are drawn 5 nm to the right of their band.
One pixel is 0.026 percent of CV in Figures 7 and 13 and 0.125 and 0.030 in
Figures 11 and 14.

The build checks each against the text (pp. 7 and 10). Figure 7: CV
"steadily around 3%", independent of the sun and of Kd(490); CV and Tmax
rising with the wave height and the wind; Tmax "about 2.5s" on average.
Figure 13: CV from 1 to 3 percent as the sun goes down; larger changes
with the wave height than with the wind; both rising with Kd(490). Figure
11: clear-sky CV from about 15 percent in the blue to 25 in the red,
overcast CV flat but for the red bands, clear-sky Tmax flat, overcast Tmax
about 6 s in the red. Figure 14: CV about 2 percent below 600 nm and
higher in the red; on the clear-sky curve Tmax falls steadily from about
4.2 s at 442 nm to about 2 s in the red.

**Figure 10 (0.19.0).** Figure 8 for six bands, clear skies, upper depth:
one coloured line per band for CV and another for Tmax, without symbols or
bars, against the sun's zenith angle, the wave height, the wind speed
itself (in whole metres per second, as in Figures 7 and 13) and Kd(490).
The legend names the bands 443, 490, 510, 560, 670 and 683 nm; Figure 11
puts the same instruments' bands at 442 and 665, and the text says "from
442 to 683 nm" (p. 9). The legend's names are kept. Each band is found by
its hue. The CV line is followed from its left end, where it is the band's
upper line, class by class, taking at each class the run of the band's
colour whose straight segments back to the previous class and on to the
next are best covered by that colour; each segment is then fitted with a
straight line through the band's pixels along it, and the value at a class
is the mean of the two fits that meet there. This reads the classes where
a line is hidden under another, or crosses its own Tmax line. Three were
read otherwise: at 20 degrees the 510 nm line lies under the 560 nm line
and is read where the fit to its visible pixels meets the class; in panel
b the 683 nm line at 1.75 and 2 m runs beside its own Tmax line and is read
from the segments beyond; past 2 m it leaves the axes at 35 percent, and
2.25 m is left empty with status `above_axis`. One pixel is 0.115 percent
of CV. The Tmax lines are not read: they bend a few pixels to the side of
the classes, in each panel the red and orange ones cross their own band's
CV line, and the others run within a pixel or two of each other, so that
which line a pixel belongs to cannot be told along much of their length.

The build checks the 510 nm line against Figure 8's medians, read
separately from another image: within 0.2 percent at all 37 classes of
panels a, b and d (panel c's classes are not Figure 8c's). Against the
text: "larger CVs for longer wavelengths" (p. 9), which holds at every
class read, 683 nm at least 670's; and in panel b, CV at the red bands
"increases with wave height, contrary to what is observed at 510 nm and at
other wavelengths < 600 nm" (p. 10).

**The share of diffuse light (0.19.0).** Along the top of Figures 8a and
10a the paper prints, at the sun's zenith angles 20, 30, ... 90 degrees,
Ediffuse / Etotal: 21, 23, 25, 28, 34, 45, 70 and 100 percent. These come
from the clear-sky model of Gregg and Carder (1990), with the buoy's air
pressure, 80 percent relative humidity, the ozone of the TOMS satellite
product and a maritime aerosol of Shettle and Fenn (1979) of optical
thickness 0.2 at 550 nm (p. 4); the wavelength is not stated. They are
shipped as printed, in whole percents, with status `transcribed`.

**Where these differ from the text.**

- Figure 7's caption says "The symbols are the median values"; the text
  says each "show the average value and standard deviation" (p. 7). The
  caption is followed, as for Figure 8.
- Figure 7d's last class, Kd(490) = 0.145, is 1.6 percent, against the
  text's "steadily around 3%"; the check leaves it out.
- Figure 13a: the text has Tmax going "from 3.5 to 4.5s" as the sun goes
  down (p. 10); the figure has 3.2 s at 20 degrees and 4.3 s at 85.
- Figure 14: the text puts CV at "about 6% in the red"; the figure's
  largest is 5.4 percent. And the text gives the two Tmax curves the
  opposite skies from the figure: "constant for l < 600 nm under clear
  skies (dotted line ...), whereas it monotonously decreases from 5s (at
  442 nm) to 2s (red bands) under overcast skies (solid curve)" (p. 10),
  where the caption and the figure's own labels make the solid, open
  symbols the clear sky. The shipped values follow the figure. The falling
  curve is 4.2 s at 442 nm and 4.6 s at 412.
- Figures 11 and 14 are averages (their captions), where Figures 7, 8 and
  13 are medians.
- Figure 8's caption calls its top axis "The ratio of direct to total
  radiation within the above water downward irradiance"; the axis itself
  is labelled Ediffuse / Etotal, and its numbers rise with the sun's
  zenith angle to 100 percent at the horizon, which only the diffuse share
  does. The label is followed.

**Equation (8), not shipped.** The paper fits the change of CV with wind
speed as CV / CV(0) = a + b sqrt(w) + exp(-(sqrt(w) - c)^2 / 2 s^2) /
(s sqrt(2 pi)), with a = 0.894, b = -0.014, c = 1.627 and s = 0.752
(p. 7). The text layer of the PDF drops the minus sign of b; the page
image has it. As printed, the equation gives 0.945 at w = 0, not the 1
that CV(0) means. It is recorded here and not shipped.


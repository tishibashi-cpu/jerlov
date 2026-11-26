# Data provenance

What every shipped table is, where it came from, what was verified, and what
is known to be wrong with it.

Fifty-two entries are recorded below. Thirteen are confirmed defects, three were
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
| `morel2001_kd.csv` | Kw, e and chi of Kd = Kw + chi [Chl]^e for case 1 water. 5 nm, 350-700 nm | 71 |
| `pope1997_aw.csv` | Pure water absorption, Pope & Fry (1997) Table 3, with sigma and percent error. 2.5 nm, 380-727.5 nm | 140 |
| `smith1981_aw.csv` | Pure water absorption, Smith & Baker (1981) Table I. 10 nm, 200-800 nm | 61 |
| `mason2016_aw.csv` | Pure water absorption, Mason, Cone & Fry (2016) Table 2, with sigma. 250-550 nm: 10 nm to 300, then 2 nm | 131 |
| `bricaud1995_aph.csv` | A and B of a*ph = A [Chl]^-B, with r2, Bricaud et al. (1995) Table 2. 2 nm, 400-700 nm, and 675 nm | 152 |
| `lee2015_aw.csv` | "Pure" seawater absorption inverted from Rrs, Lee et al. (2015) Table 1, with the smoothed column and Delta aw. 5 nm, 350-550 nm | 41 |
| `gregg1990_table1.csv` | Extraterrestrial solar irradiance and the absorption coefficients of ozone, water vapour and oxygen, Gregg & Carder (1990) Table 1. 1 nm, 350-700 nm | 351 |
| `usgs2017_reflectance.csv` | Absolute reflectance of ten materials, the USGS Spectral Library Version 7's ASD records, as measured. 1 nm, 350-830 nm | 4810 |
| `mobley1999_rho.csv` | The sea surface's reflectance factor rho for above-water radiometry, Mobley (1999), as the Ocean Optics Web Book distributes it: 550 nm, wind 0-14 m/s, sun 0-80 degrees, 118 viewing directions | 8496 |
| `mobley2015_rho.csv` | The same, Mobley (2015), polarised, a Rayleigh sky; wind 0-15 m/s, sun 0-87.5 degrees; **calls itself preliminary** | 11800 |
| `morel1988_kd.csv` | Kw, chi and e of K = Kw + chi C^e for case 1 water, Morel (1988) Table 2, C the Chl a + Pheo a concentration. 5 nm, 400-700 nm | 61 |
| `morel2007_aw.csv` | Pure water absorption aw1 (300-500 nm) and aw2 (300-370 nm), and pure sea water scattering bsw, Morel et al. (2007) Table 2. 5 nm | 41 |
| `morel2007_stations.csv` | The eight stations of the clearest waters, South Pacific gyre 2004: Chl, Zeu, Kd and ap at 420 and 310 nm, Rmax, atot and ay; Morel et al. (2007) Table 1 | 8 |
| `morel2002_nadir_fq.csv` | f0, Sf, Q0, SQ, f0/Q0 and Sf/Q of the linear fits for the radiance from the nadir, Morel et al. (2002) Appendix B, Tables 1-3. 7 wavelengths, 412.5-660 nm, 6 Chl | 252 |

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
| `model` | Computed by the source's own model, not measured at that wavelength: Austin & Petzold's (1986) Kd from K(475) by their Eq. (6) | Usable, as accurate as the model |
| `jerlov_original` | Jerlov's own value, carried unchanged by a later source: Austin & Petzold's 475 nm column | Usable |
| `pure_seawater` | Not a measurement of the type: the attenuation of pure sea water, which Austin & Petzold give as type I | Usable; read the source's caveat |
| `transcribed` | Printed as a number and copied as printed, in a table none of whose rows is flagged: `gregg1990_table1` and `gernez2009_diffuse_share` | Usable, as `ok` is |
| `included` | `williamson2022_measured`: an average over five or more campaigns, which the paper kept | Usable; what `measured_points` returns |
| `excluded_sparse` | `williamson2022_measured`: an average over fewer than five campaigns, which the paper left out | Returned only with `include_sparse=True` |
| `identity` | `williamson2023_depth`: the 0-10 m layer, which is the surface type by definition, not a count of campaigns | Usable |
| `second_highest` | `williamson2023_depth`: the paper chose the type with the second-highest campaign count, as closer to the layers around it (section 13) | Usable; the `note` names the type passed over |
| `undeclared` | `williamson2023_depth`: fewer than ten campaigns supported any type, and the paper leaves the layer blank | Empty. `water_type_at_depth` gives `None`, and `descend` stops |
| `not_a_water_type` | `paulson1977_shortwave`: a row of the paper's Table 2 that is not a Jerlov type (section 14) | Refused unless `include_non_types=True` |
| `other_definition` | `boss2001_chi`: a chi from another paper, defined on the total scattering rather than the particles', kept for comparison (section 18) | Not used by `bb_from_vsf` |
| `above_axis` | `gernez2009_bands`: the line leaves the top of the figure's axes, so there is nothing to read (section 25) | Empty; NaN in `gernez2009_band_cv` |

The first twelve are the statuses a spectrum carries, and the ones a
caller's own `flags` may use, less `read_from_figure`. The rest belong to
one table each and say what kind of row it is.

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

- **Bricaud et al. 1995.** J. Geophys. Res. 100(C7), 13321-13332, DOI
  `10.1029/95JC00463`. Table 2; see section 31.

- **USGS Spectral Library Version 7 (Kokaly et al. 2017).** U.S.
  Geological Survey data release, DOI `10.5066/F7RR1WDJ`, CC0 1.0; report
  USGS Data Series 1035, DOI `10.3133/ds1035`. Ten records; see section 37.

- **Pope & Fry 1997, Smith & Baker 1981, Mason, Cone & Fry 2016, Lee et al.
  2015.** The pure water absorption spectra of section 29, each with its
  DOI there. Transcribed from the PDFs, which the user obtained.

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
water, not the absorption of what was in the water. (Since 1.4.0 it is shipped,
as a published spectrum in its own right, through a separate function;
the reason above still holds for subtracting it from a Jerlov type's a.
See section 29.)

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

**Below 0.1 degree, turbulence scatters too (an open question).**
Bogucki, Domaradzki, Ecke and Truman (2004), "Light scattering on
oceanic turbulence", Appl. Opt. 43(30), 5662-5668, DOI
`10.1364/AO.43.005662`, measured the volume scattering function from
1e-7 to 1e-3 rad, about 6e-6 to 0.06 degree, all of it below Petzold's
first angle. Their abstract: "The total scattering coefficient b, due to
scattering on turbulent inhomogeneities, is between 1 and 10 m-1 under
typical oceanographic conditions", and "optical measurements at small
angles are affected by turbulence-related scattering". The report's
extension below 0.1 degree is a power law of the scattering it measured;
scattering on turbulence, which depends on how the water is being mixed
that day rather than on what is in it, is not in it. So the 3.4 to 14.5
percent of s below 0.1 degree, and everything that rests on it, such as
`ScatteringFunction.mean_cosine`, describe the extension, not the water.
How much of the light near the beam turbulence takes, against particles,
was not settled in the literature found on 2026-11-15.

**What rests on the extension (1.15.8, DECISIONS.md section 96).** Without
it, the phase function renormalised over 0.1 to 180 degrees and b taken as
b (1 - f), the mean cosine at the eight stations falls by 0.004 to 0.015,
B/S rises by 3.5 to 17.0 percent, and the Henyey-Greenstein g fitted to the
backscatter falls by 0.004 to 0.016. Kd hardly moves: in 32 Monte Carlo
cases (each station, b/a of 0.5 to 10, the sun at 30 degrees,
`examples/data/below_0_1/`) treating the light scattered by less than 0.1
degree as unscattered moves Kd by -0.63 to +0.13 percent, and spreading it
over 0.1 to 180 degrees with b kept by +0.11 to +4.40. The extension
decides how much of b is counted as scattering; Kd does not depend on it.
`examples/phase_function_choice.py`, part 3.

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
difference grows with depth. Nor is it Jerlov's (1976) Kd for IB: Austin &
Petzold's (1986) revision puts the 1 percent level at 95.8 m, and the
fits of Solonenko & Mobley at 98.5 and 104.1 m (DECISIONS.md section 54).
Every set of spectral Kd for IB in the package gives 93 to 104 m against
the 70 of the 1977 paper.

**Nygård's own profiles (DECISIONS.md section 55).** Two of the 1977
paper's sources are in Tyler, J. E. (ed.) (1973), Data Report, SCOR
Discoverer Expedition, May 1970, SIO Ref. 73-16 (no DOI). Nygård's direct
measurements of quanta there (vol. II, section I) give 48 lowerings at 19
stations. The five whose 10 percent level is IB-like, between 28.5 and 37
m, reach 1 percent at 1.73 to 2.51 times that depth, median 1.95, against
2.12 in Table 2 and 2.49 in the package; over all 37 that reach both
levels the median is 2.05. So the faster loss below the 10 percent level
is in the measurements themselves, not only in how the 1977 tables were
formed, and a Kd that does not change with depth, from any of the tables
here, does not reproduce it. Smith's spectral irradiance at three of
those stations (vol. II, section G; DECISIONS.md section 56) shows why in
part: Kd at 465-505 nm, where the deep light lies, rose with depth at two
of them, by 1.63 and 1.56 times from the shallowest layer to the deepest,
and in every deepest layer was above Jerlov's IB, up to 1.89 times. Two of
the three were normalised in variable weather, with errors Smith puts as
high as a factor of two; the one measured in clear weather rises either
way. Morel's quanta, measured on the same cruise with another meter and
another surface correction (DECISIONS.md section 58), agree with
Nygård's: in the four sets whose 10 percent level is IB-like the 1
percent level lies 2.08 to 2.18 times as deep, median 2.14. Chlorophyll
was higher in the deepest of Smith's layers than in the shallowest at
the two stations where both can be compared, 2.80 and 1.42 times, but
also at the one of them where the blue Kd did not rise, so it is not
shown to be the cause.
`tools/nygard1973_quanta.csv`, `tools/smith1973_blue.csv`,
`tools/morel1973_quanta.csv` and `tools/baird1973_chlorophyll.csv` are
the transcriptions; they are not shipped.

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


## 26. Visual pigment templates and receptor noise: a misprint in eq. (4) of Vorobyev & Osorio (confirmed)

No table is shipped for either; the constants are written into
`jerlov/vision.py`, read from the page images of the two papers, and each
is checked by reproducing something the paper prints (DECISIONS.md section
64, `tests/test_vision.py`).

**The template.** Govardovskii, V. I., Fyhrquist, N., Reuter, T., Kuzmin,
D. G. and Donner, K. (2000), "In search of the visual pigment template",
*Visual Neuroscience* 17, 509-528, doi:10.1017/S0952523800174036; obtained
by the author. The text layer of the PDF reads "=" as "5", "+" as "1" and
brackets as "@" and "#", so nothing was taken from it.

| Constant | A1 | A2 | Where |
|---|---|---|---|
| A | 69.7 | 62.7 + 1.834 exp[(lambda_max - 625)/54.2] | p. 515; eq. (6a), p. 517 |
| a | 0.8795 + 0.0459 exp[-(lambda_max - 300)^2/11940] | 0.875 + 0.0268 exp[(lambda_max - 665)/40.7] | eq. (2), p. 515; eq. (6b) |
| B, b | 28, 0.922 | 20.85, 0.9101 | p. 515; p. 517 |
| C, c | -14.9, 1.104 | -10.37, 1.1123 | p. 515; p. 517 |
| D | 0.674 | 0.5343 | p. 515; p. 517 |
| A_beta | 0.26 | 0.37, not a regression (below) | p. 516; p. 517 |
| lambda_mbeta | 189 + 0.315 lambda_max | 216.7 + 0.287 lambda_max | eq. (5a), p. 516; eq. (8a), p. 517 |
| beta bandwidth | -40.5 + 0.195 lambda_max | 317 - 1.149 lambda_max + 0.00124 lambda_max^2 | eq. (5b); eq. (8b) |

What was checked: the beta-band regressions give the "most accurate
point" of p. 516 (lambda_max 502.6 nm: 347.3 and 57.5 nm); the paper's
relations between lambda_max and the long-wave half-maximum, eqs. (3) and
(7), hold for the template within 0.5 nm across the peaks it measured,
357-569 nm (A1) and 444-619 nm (A2, Table 1); and the alpha-band peaks
within 0.5 nm of lambda_max at a height within 0.2 percent of 1.

**A2's beta amplitude.** The paper gives no equation for it: it "shows no
correlation with lambda_max", and was fixed at 0.37 where the beta-peak lay
outside the recording (p. 517); Fig. 10 fits 0.37 and 0.38 where it could
be fitted. The package uses 0.37, the value the authors used, and says so.

**The noise model.** Vorobyev, M. and Osorio, D. (1998), "Receptor noise as
a determinant of colour thresholds", *Proc. R. Soc. Lond. B* 265, 351-358,
doi:10.1098/rspb.1998.0302; obtained by the author.

**Eq. (4) is misprinted (confirmed).** The distance for three receptor
types is printed (p. 353) with a last term e_3^2 (Delta q_1 - q_2)^2, with
no Delta on q_2. The paper derives eqs. (3) to (5) from its general form
(A7) (Appendix 1, p. 356). Computed from (A7) for random catches and noise,
eqs. (3) and (5) as printed, and eq. (4) with the Delta restored, agree
with it to within 2e-9. Read as printed, with q_2 the catch itself (1 at
the background, eq. 2), eq. (4) is not a distance between the two stimuli:
its last term does not vanish when they are identical. The package computes
(A7), and `tests/test_vision.py` checks it against all three equations, eq.
(4) corrected, and checks the misprint for that fault.

## 27. Kd from chlorophyll and from a and bb, Rrs and the Secchi depth (note)

DECISIONS.md section 66. One table is shipped; the other constants are
written into `jerlov/ocean_colour.py`. All were read from page images of
the primary papers, the text layers used only to cross-check.

**Morel & Maritorena (2001).** Morel, A. and Maritorena, S., "Bio-optical
properties of oceanic waters: A reappraisal", *J. Geophys. Res.* 106(C4),
7163-7180, doi:10.1029/2000JC000319; the copies on HAL and at UCSD.
`morel2001_kd.csv` is Table 2 (p. 7168), all 71 rows, written by
`tools/build_morel2001.py` from literals, which first checks Kw(420) =
0.00758 against p. 7167 and chi and e at 390 and 350 nm (0.119, 0.67 and
0.153, 0.778) against the caption of Figure 7 (p. 7170).

- Below 400 nm the rows repeat the chi and e that Morel & Antoine (1994)
  extrapolated below 400 nm; the authors find them "a kind of lower limit"
  for oligotrophic water, matching their Pacific data but not their
  Mediterranean data (p. 7170). They are marked `extrapolated`.
- The paper says its new data could not be used beyond 590-600 nm, so
  those values are Morel's (1988), not revised (p. 7168). The rows from
  595 nm say so in `note`; they are `ok`, as the paper presents them.
  (Corrected in 1.19.0: chi and e are Morel's (1988) exactly from 560 nm,
  not only beyond 590-600; Kw differs at every wavelength. Section 45.)
- From 560 nm, as below 400 nm, e and chi are printed rounded to two or
  three digits, where 400-555 nm have five. The paper does not say why.
  (From 560 nm they are Morel's (1988) values, printed with the digits of
  his Table 2; section 45.)
- The text gives Kw at 380 nm from Pope & Fry (1997) as 0.0167 (p. 7169);
  Table 2 has 0.01510 there. The table is used as printed.
- Kd here is the attenuation of the upper layer, from the surface to the
  first good irradiance spectrum, about one penetration depth (pp.
  7165-7166).

**Lee, Du & Arnone (2005)**, *J. Geophys. Res.* 110, C02016,
doi:10.1029/2004JC002275, the copy in the University of Maine's course
readings: eq. (11), p. 7 of 10, Kd(E10%) = (1 + 0.005 theta) a + 4.18 (1 -
0.52 exp(-10.8 a)) bb, for the layer down to 10 percent of the surface
irradiance. The text calls the angle theta_0 where the equation prints
theta_a; both are the sun's zenith angle above the surface in degrees.

**Lee et al. (2013)**, *J. Geophys. Res. Oceans* 118, 4241-4255,
doi:10.1002/jgrc.20308, obtained by the author: eq. (5) with eq. (3) and
Table 1 (pp. 4242-4243): m0 = 0.005, gamma = 0.265, m1 = 4.259, m2 =
0.52, m3 = 10.8.

**Gordon et al. (1988)**, *J. Geophys. Res.* 93(D9), 10909-10924,
doi:10.1029/JD093iD09p10909, obtained by the author: eq. (2), p. 10910,
R/Q = l1 u + l2 u^2 with l1 = 0.0949 and l2 = 0.0794, for a sun at least
20 degrees from the zenith. **Lee, Carder & Arnone (2002)**, *Appl. Opt.*
41, 5755-5772, doi:10.1364/AO.41.005755, the University of Maine copy:
g0 = 0.0895 and g1 = 0.1247, the mean of Gordon et al.'s and a coastal
pair (p. 5756), and eq. (8), rrs = Rrs / (T + gamma Q Rrs), with T = 0.52
and gamma Q = 1.7 (p. 5757). The coastal pair, 0.084 and 0.17, is from a
paper not read here and is not shipped.

**Lee et al. (2015)**, *Remote Sens. Environ.* 169, 139-149,
doi:10.1016/j.rse.2015.08.002, the NOAA repository copy: eq. (33), p. 146,
Z_SD = ln(|0.14 - Rrs_tr| / 0.013) / (2.5 Kd_tr); 0.013 sr^-1 on p. 147;
the validation, N = 338, 0.1 to 30 m, 18.2 percent, on p. 147.

**0.14 is not the product it is derived from (note).** The paper takes
the white disc as R_T = 0.85, so r_T = R_T / pi, about 0.27 sr^-1, and
t^2 / n^2 about 0.54, "Eq. (32) then becomes" eq. (33) with 0.14 (p. 146).
0.85 / pi x 0.54 is 0.146, and 0.27 x 0.54 is 0.146: either rounds to
0.15, not 0.14. The package uses 0.14, as eq. (33) prints and as the
validation used. With 0.146 instead, for Rrs_tr from 0 to 0.01 sr^-1, the
argument of the logarithm would be 4.4 to 4.7 percent larger and Z_SD 1.8
to 2.0 percent deeper.

## 28. The quasi-analytical algorithm: three versions of QAA_v6, and Table 10.1 reproduced (note)

DECISIONS.md section 67. No table is shipped; the constants are in
`jerlov/qaa.py`. The test data, from files the IOCCG distributes, are in
`tests/data/`, written by `tools/qaa_test_data.py`, and not in the wheel.

**QAA_v6.** Lee, Z. P., "Steps and calculations of the Quasi-Analytical
Algorithm (QAA_v6)", `qaa_v6_202011.pdf`, and its spreadsheet
`QAA_v6-202011.xlsm`, both from https://ioccg.org/resources/software/. The
spreadsheet's formulas and macro were read as text; the macro was not run.
The document's table of steps, its text, and the spreadsheet disagree:

| | table of steps (p. 1) | text (pp. 2-5) | spreadsheet |
|---|---|---|---|
| g0, g1 | 0.089, 0.1245 | 0.0895, 0.1247 (eq. 1, as -0.0895 + sqrt(0.008 + 0.499 rrs) over 0.249) | 0.08945, 0.1247 |
| xi | exp[S (442.5 - 415.5)] | exp[S (443 - 411)] (eq. 12) | exp[S (443 - 412)] |
| h0, h1, h2 | -1.146, -1.366, -0.469 | the same | -1.145902927834082, -1.365828264291757, -0.4692660279445807 |
| 55x for MODIS | 547 nm | 550 nm (p. 5) | 555 nm in its example |

The package follows the spreadsheet. With its own pure water values, it
reproduces the eta, bbp(555) and a at 412, 443, 489, 510 and 555 nm that
the spreadsheet stored for its 12 example stations, both reference
wavelengths among them, to a relative 1e-12, and their split into adg and
aph. Two smaller things in the spreadsheet: aw(555) is 0.0596 on its QAA
sheet and 0.0595, labelled "Lee et al. (2015)", on its decomposition
sheet; and a column header reads 530 nm over values computed at 510 nm.

**IOCCG Report 5.** IOCCG (2006), *Remote Sensing of Inherent Optical
Properties: Fundamentals, Tests of Algorithms, and Applications*, Lee,
Z.-P. (ed.), Reports of the International Ocean-Colour Coordinating Group
No. 5, IOCCG, Dartmouth, Canada; chapter 10, pp. 73-77, and the synthetic
data set of chapter 2 (pp. 15-18), `IOP_AOP_Sun30.xls`: 500 spectra from
Hydrolight, 400-800 nm every 10 nm, with the sun 30 degrees from the
zenith. Of it, `tests/data/ioccg2006_sun30.csv` keeps Rrs at the seven
wavelengths the algorithm used and the true a, bb, adg (a_g + a_dm) and aph
where compared, and `ioccg2006_pure_water.csv` the data set's aw and bbw,
400-700 nm.

Run as the report describes (p. 76: Rrs at 410, 440, 490, 510 and 670 nm,
Rrs(555) the mean of 550 and 560 nm), the package gives, against Table
10.1 (p. 76), RMSE and bias in log10 (eq. 2.1, p. 18):

| | RMSE, table | RMSE, here | bias, table | bias, here |
|---|---|---|---|---|
| a(410) | 0.061 | 0.060 | 0.016 | 0.016 |
| a(440) | 0.060 | 0.059 | 0.016 | 0.015 |
| a(490) | 0.062 | 0.062 | -0.005 | -0.007 |
| bbp(440) | 0.081 | 0.081 | 0.008 | 0.007 |
| bbp(555) | 0.079 | 0.079 | -0.029 | -0.030 |

N = n = 500 for each, as in the table. The table's slopes and intercepts
come from a "Type II" regression (p. 17) that is not specified further.
The geometric mean regression gives slopes and intercepts within 0.004 of
the table's for all five rows; ordinary least squares within 0.003 for the
three rows of a and up to 0.015 off for bbp.

The table counts 476 of 500 decompositions as valid without giving the
rule. Taking those with adg(440), aph(440) and aph(490) all positive gives
475.

## 29. Published pure water absorption, and an inconsistency in Smith & Baker (1981) Table I (confirmed)

`pure_water_absorption_table(wl, source=...)` returns one of four
published spectra (DECISIONS.md section 70). They are not the aw of any
Jerlov source; `pure_water_absorption` still returns that. All four were
transcribed by `tools/build_pure_water_aw.py` from PDFs the user
obtained, with the numbers as literals, and each was checked against the
paper's own statements first.

| Key | Paper | Table | Range | Checked against |
|---|---|---|---|---|
| `pope1997` | Pope & Fry, Appl. Opt. 36(33), 8710-8723, DOI `10.1364/AO.36.008710` | 3, pp. 8718-8719 | 380-727.5 nm, 2.5 nm | the percent column; the minimum Mason et al. quote |
| `smith1981` | Smith & Baker, Appl. Opt. 20(2), 177-184, DOI `10.1364/AO.20.000177` | I, p. 182 | 200-800 nm, 10 nm | Eq. (6); Table II |
| `mason2016` | Mason, Cone & Fry, Appl. Opt. 55(25), 7163-7172, DOI `10.1364/AO.55.007163` | 2, p. 7170 | 250-550 nm | the minimum in the abstract |
| `lee2015`, `lee2015_smoothed` | Lee, Wei, Voss, Lewis, Bricaud & Huot, Appl. Opt. 54(3), 546-558, DOI `10.1364/AO.54.000546` | 1, p. 555 | 350-550 nm, 5 nm | the smoothing rule |

The DOIs were resolved at doi.org, each to the volume, issue and first
page above.

**What each is.** Pope & Fry and Mason et al. measured pure water in an
integrating cavity, at 22 and 23 degrees C. Smith & Baker derived aw from
the diffuse attenuation K of the clearest natural waters by their Eq. (6),
K = aw + bsw/2. Pope & Fry (p. 8720) find "significant disagreement below
490 nm" with Smith & Baker and put it down to their own purification, the
absence of scattering effects in their cavity, and its sensitivity. Lee
et al. inverted "pure"
seawater absorption from the remote sensing reflectance of the clearest
oceans; it is not a laboratory measurement.

**Pope & Fry.** Read from the text of the PDF and compared with the page
image. The percent column is the standard deviation combined in
quadrature with a 2 percent calibration error, rounded up to an integer
(p. 8719); all 140 rows satisfy that within the rounding of the printed
aw and sigma. The table's minimum, 0.00442 at 417.5 nm, is the "0.0044
m-1 at 418 nm" Mason et al. quote (p. 7164). The values beyond 700 nm are
printed, but the calibration constants were determined from data at 700
nm and below (p. 8717), and the title's range is 380-700 nm: they are
kept as `ok` with a note saying so.

The aw of the IOCCG synthetic data set (`tests/data/`), which IOCCG
Report 5 says "were taken from Pope and Fry (1997)" (p. 15), equals this
table at all 31 of its wavelengths, 400-700 nm; a test checks it.

**Smith & Baker: 710 nm (confirmed).** A 1981 scan, read from the page
images. Eq. (6) holds for every row within the rounding of K, aw and bsw,
except at 710 nm, where the page prints K = 0.834 and aw = 0.839: aw
above K, by 0.005 where bsw/2 is 0.00035. Which of the two is wrong
cannot be told from the paper; Table II, which repeats K and aw every 50
nm, does not include 710 nm. aw at 710 nm is kept as printed and marked
`suspect`, so any value resting on it warns. Table II agrees with Table I
at its 13 wavelengths.

**Mason et al.** Read from the text of the PDF. Table 2 prints values in
units of 1e-3 1/m; the CSV holds them in 1/m, converted by moving the
decimal point, not by floating-point arithmetic. The abstract gives the
minimum as 0.000811 +/- 0.000227 m-1 at 344 nm; the table's minimum is
0.81 and 0.23 (x 1e-3) there. From 310 to 550 nm a three-point moving
average was applied by the authors (p. 7169).

**Lee et al.** Read from the text of the PDF. Five wavelengths, 360,
370, 385, 395 and 400 nm, also carry a smoothed value, which the paper
describes as "a simple average between the shoulders" of dips it
attributes to imperfect removal of Raman scattering (p. 555). Each is the
mean of the unsmoothed values either side of its dip, within rounding:
355 and 365 nm for 360; 365 and 375 for 370; 380 and 390 for 385; 390 and
405 for the dip at 395-400. `lee2015` returns the aw column as printed,
`lee2015_smoothed` the smoothed values where there are any.

The QAA_v6 spreadsheet (DATA.md section 28) labels its aw "Lee et al
(2015)": 0.0031, 0.0048, 0.0132, 0.0302 and 0.0595 at 412, 443, 489, 510
and 555 nm. Against this table: 0.0031 at 410 and 415 nm; 0.0132 is the
value at 490 nm; 0.0302 at 510 nm as printed; at 443 nm the table gives
0.0050 by linear interpolation, not 0.0048; and 555 nm is outside the
table, which ends at 550. Not tested, only recorded.

**How far apart they are (an open question).** Which is right in the
violet and near ultraviolet is not settled, and the package does not
choose. From the shipped tables, Pope & Fry over Mason et al. is 7.95 at
380 nm, 2.99 at 400, 1.46 at 420 and 1.22 at 440, and between 0.97 and
1.08 from 460 to 550 nm; Lee et al. over Mason et al. is 2.59 at 380 nm
and 1.03 at 420. Smith & Baker, derived from natural waters, is above all
three below 450 nm. At 440 nm Pope & Fry and Mason et al. alone differ
by a fifth, and in the clearest Jerlov types pure water is much of a:
`radiative_transfer_inputs.py` shows a difference of 0.004 m-1 in aw,
between another pair, leaving IB's a short by 9.6 percent (DECISIONS.md
section 86). No laboratory measurement newer than Mason et al. (2016)
was found on 2026-11-15.

**Uncertainties (returned since 1.28.0, DECISIONS.md section 125).**
`pure_water_absorption_uncertainty` returns Pope & Fry's sigma and percent
error, Mason et al.'s sigma and Lee et al.'s Delta aw as printed, at the
printed wavelengths only, with what each is in the paper's terms: Pope &
Fry's sigma is a statistical standard deviation and their percent adds a
2 percent calibration error; Lee et al.'s Delta aw is propagated from an
assumed 15 percent uncertainty in each component (pp. 554-555), an
estimate rather than a measured spread. Smith & Baker and Morel et al.
print none. Pope & Fry and Mason et al. measured fresh water; no salinity
or temperature correction is applied.

**What the choice does to the reflectance (1.15.9, DECISIONS.md section
97).** With pure sea water alone (a = aw, bb = bw / 2, bw from Williamson &
Hollins's constants) and Lee et al.'s (2011) nadir relation, the five
spectra shipped here (the four above and `pure_water_absorption()`) give
remote sensing reflectances up to 6.85 times apart at 380 nm, 4.90 at 400,
4.28 at 412, 2.62 at 443, 1.47 at 490, 1.18 at 510 and 1.13 at 550, and
Rrs(443)/Rrs(550) of 10.73 to 24.75. For Williamson & Hollins's IB, its
contents laid on each spectrum and bb built from each of Petzold's eight
measured B/S, the spectra move Rrs by 1.12 to 1.34 times and the B/S by
1.88 to 2.61: the particles matter more at every wavelength from 412 to
550 nm. Pure sea water lies outside the bb / (a + bb) of Lee et al.'s fit
(above 0.37) with Mason et al.'s and Lee et al.'s spectra at 380 to 412 nm
and with Williamson & Hollins's at 380 nm; there Gordon et al.'s (1988)
relation gives spreads up to 26.4 percent different, and within 5.7
percent from 443 nm. `examples/ocean_colour_and_secchi.py`, part 8.

## 30. Removing Raman scattering from Rrs: Table 2 of Lee et al. (2013) (note)

`lee2013_raman_correction` (DECISIONS.md section 71) carries the six rows
of Table 2 of Lee et al. (2013), J. Geophys. Res. Oceans 118, 4241-4255,
DOI `10.1002/jgrc.20308`, p. 4245: alpha, beta1 and beta2 of their eq.
(11) at the MODIS bands 412, 443, 488, 531, 551 and 667 nm. They are
literals in `jerlov/qaa.py`, not a shipped table, and a test repeats them
and checks eq. (11) against them.

**The minus signs are not in the PDF's text.** The text extracted from
the PDF reads beta2 as 0.022 to 0.081; the page image prints -0.022 to
-0.081, and the paper's text calls beta2 negative (p. 4244). The values
were read from the image. alpha and beta2 have no unit; beta1 has "a unit
associated with Rrs" (the table's footnote), sr-1.

**What the coefficients rest on.** Hydrolight runs of the case 1 model of
Morel & Maritorena (2001) with chlorophyll 0.02, 0.05, 0.1, 0.2, 0.5, 1
and 3 mg m-3; the fit is within about 15 percent of Hydrolight's RF, and
RF is "generally less than 0.20" (p. 4244). The paper offers no worked
example to check against. On the IOCCG Report 5 synthetic data set,
which excludes inelastic scattering (Report 5, p. 17) and so is not a
validation, RF stays below 0.20 for all 500 spectra at 440-560 nm
(maximum 0.135, at 560 nm).

**What the paper did beyond the table, and the package does not.** For
its hyperspectral data (p. 4246) the paper computed RF at the six bands,
"interpolated and extrapolated" it to 350-550 nm every 2 nm, and set RF
to 0 below 400 nm "to represent the assumed low Raman-scattering
contribution". The package interpolates between 412 and 667 nm as the
paper does, and refuses outside: the extrapolation is not described, and
the zero is an assumption.

## 31. Chlorophyll to aph and bbp: Bricaud et al. (1995) Table 2, and Morel & Maritorena's eq. (10) (note)

`bricaud1995_aph` and `morel2001_bbp` (DECISIONS.md section 72).

**Bricaud et al. (1995)**, J. Geophys. Res. 100(C7), 13321-13332, DOI
`10.1029/95JC00463`. Table 2, pp. 13,326-13,327, gives A, B and r2 of
a*ph(l) = A(l) [Chl]^-B(l) every 2 nm from 400 to 700 nm, and at 675 nm
as well: 152 rows from 815 spectra spanning [Chl] 0.02-25 mg m-3. The PDF
is a scan with a text layer; all 456 numbers were read from the page
images and agree with the text layer, including the negative B at 698
and 700 nm. `tools/build_bricaud1995.py` carries them as literals and
checks them against the text:

- the 440 nm row is the a*ph(440) = 0.0403 [Chl]^-0.332 that the text
  gives twice (the caption of Figure 4, p. 13,327, and p. 13,330);
- halfway between 442 and 444 nm, A = 0.0394 and B = 0.3435, within the
  0.0394-0.0406 and 0.330-0.344 the text gives for 443 nm with and
  without 488 samples (p. 13,324).

r2 is below 0.01 from 556 to 578 nm and at 696 and 698 nm: there the
power law describes the data hardly at all. The values are used as
printed; the docstring says so.

**Bricaud et al. (1998)**, J. Geophys. Res. 103(C13), 31033-31044, DOI
`10.1029/98JC02712`, refit the same kind of relation to 1166 spectra, for
all particles as well as for phytoplankton, but print the spectral
coefficients only as a figure (Figure 4): the values "at 2-nm intervals
can be provided on request" (p. 31,037). The package does not use them.
Its 440 nm relations, which are printed, agree with the text's ratio of
the two (1.37 on average, 1.33 at 0.02 and 1.41 at 25 mg m-3). Its
nonalgal particles at 440 nm, 0.0124 [Chl]^0.724, and their mean slope,
0.011 per nm, are quoted in `ocean_colour_and_secchi.py` part 6 as stated
choices.

**Morel & Maritorena (2001), eq. (10) is not their model's bbp.** Eq.
(10), p. 7170, is printed with a maximum backscattering efficiency of
0.02 and a (550/l) dependence at every [Chl]. It is the 1988 form: the
text then modifies it "in two ways" (p. 7171), resetting the
maximum to 1 percent and letting the exponent vary with [Chl], which
gives their eqs. (13) and (14). The package follows (13) and (14). In
(14), v = (1/2)(log10 Chl - 0.3) is -0.9995 at 0.02 and +0.0005 at 2 mg
m-3, the "l^-1" and "neutral" the text describes; its unit is printed
"mg-3". Eq. (9), bp550 = 0.30 [Chl]^0.62, is used as printed; the
paper's (9'), which subtracts pure water's scattering, it calls
negligible.

## 32. Rrs with water and particles apart: seven of Lee et al.'s (2011) coefficient sets (note)

`lee2011_rrs` and `LEE2011_RRS_COEFFICIENTS` (DECISIONS.md section 73)
carry eq. (14) of Lee et al. (2011), Appl. Opt. 50(19), 3155-3167, DOI
`10.1364/AO.50.003155`, p. 3158, and the coefficients of its Table 2, p.
3159. They are literals in `jerlov/ocean_colour.py`, not a shipped
table; a test repeats them.

**Only seven geometries are printed.** The paper derived coefficients for
"(6 x 7 x 13 + 6)" geometries: six sun angles from 0 to 75 degrees,
seven viewing angles from 10 to 70 at thirteen azimuths from 0 to 180,
and nadir for each sun angle, which is the count the text gives. Table 2
prints "a few samples", seven columns. The paper does not say where the
others can be obtained; the package offers the seven and does not
interpolate.

**Checks.** The PDF has a text layer from typesetting; the table agrees
with the page image. Its nadir column, (0.0604, 0.0406, 0.0402, 0.1310),
is the set Lee et al. (2013) quote "for nadir-viewed Rrs" (p. 4244).
Two cells repeat a neighbour's value as printed: G1w is 0.0581, equal to
G0w, at (0, 40, 135), and 0.0524 at both (15, 40, 135) and (30, 40, 135).
Nothing in the paper says whether these are coincidences or errors; they
are used as printed.

**What the fit rests on.** Hydrolight runs on the 500 IOP sets of IOCCG
Report 5, bb/(a + bb) 0.0002-0.37, sun angles extended to 0-75 degrees,
with a particle phase function blended from Petzold's average and a
Fournier-Forand of backscattering ratio 1 percent (p. 3159). The
function warns outside that range of bb/(a + bb).

**Not claimed.** The notes this work started from said the form was
more accurate than Gordon et al.'s (1988) in clear water. Lee et al.
(2011) do not compare the two, and the package does not say so.

## 33. D0 and Kd at another sun angle: Gordon (1989), and a row of his Table 3 (note)

`gordon1989_d0` and `gordon1989_kd` (DECISIONS.md section 74) carry eq.
(12) of Gordon (1989), Limnol. Oceanogr. 34(8), 1389-1409, DOI
`10.4319/lo.1989.34.8.1389`, p. 1401, D0 = f / cos(theta_w) + 1.197 (1 -
f), and the rescaling by K/D0 the paper supports (pp. 1398-1399). The
PDF, from a university course site, is a scan with a text layer;
equation (12) and Table 3 were read from the page images.

**The refractive index, and the 40 degree row.** The text says the
ocean's refractive index is "about 1.33" (p. 1392). Table 3 (p. 1399)
prints 1/cos(theta_w) beside its D0 for seven sun angles. n = 1.333
reproduces six of them to their printed three decimals; at 40 degrees
it gives 1.14148 where the page prints 1.142. No index from 1.3200 to
1.3499 reproduces more than six rows, and every one that reproduces six
misses 40 degrees; 1.33 itself reproduces four. Whether the 40 degree
entry was rounded from a different computation or is a misprint, the
paper does not say. The package uses 1.333; a test checks all of this.

**Accuracy.** Against D0 computed with a model atmosphere (Table 3),
eq. (12) is within about 3 percent for the sun up to 60 degrees and 5-8
percent too low at 80 (p. 1402); the function warns above 60. K/D0
falls on single curves with an average error of 1.8 percent, and <K>/D0
with 2.2 (p. 1399).

**What the package cannot do.** Jerlov's Kd tables do not record the
sun angle or the sky they were measured under, so no D0 can be assigned
to them without an assumption; `gordon1989_kd` takes both D0 from the
caller.

## 34. A slanted line of sight: a sign misprinted in Duntley's (1963) eq. (12) (confirmed)

`Scene.observe_slant` (DECISIONS.md section 75) rests on Duntley, S. Q.
(1963), "Light in the sea", J. Opt. Soc. Am. 53(2), 214-233, DOI
`10.1364/JOSA.53.000214`, eqs. (8)-(16), pp. 229-231. The PDF is a scan
with a text layer that garbles the equations; they were read from the
page images at 300 dpi.

**The misprint.** Eq. (12), p. 230, gives the apparent radiance of a
target as its own radiance times exp[-alpha(z) r] plus

    N(zt,theta,phi) exp[+K(z,theta,phi) r cos(theta)]
        x {1 - exp[-alpha(z) r + K(z,theta,phi) r cos(theta)]}.

The sign of the first exponent is wrong. With it, a target that is the
water itself (tN0 = N(zt)) does not read as the background radiance that
eq. (9) gives at the observer, N(zt) exp[-K r cos(theta)], and eq. (14),
which the text says follows from eq. (12) and the definitions of
contrast, cannot be derived from it. With exp[-K r cos(theta)] both
hold, and eqs. (9), (13), (14), (15) and (16) agree. Checked numerically
(alpha 0.3, K 0.1, cos(theta) 0.6, r 7: printed sign 2.722, corrected
1.314, eq. (9) 1.314); `tests/test_slant.py` checks eqs. (13)-(15)
against the corrected form.

**Smaller things.** Eq. (16), p. 231, prints an unmatched parenthesis,
exp[-alpha + K cos(theta))]r; eq. (15) makes the meaning plain. The
relation r cos(theta) = zt - z (p. 229) comes from Duntley, Boileau and
Preisendorfer (1957), where z is altitude, and the 1963 paper does not
restate which way theta points with z as depth. The package takes the
two depths and the distance instead of an angle, and writes K r
cos(theta) as -K (zt - z), with K = -d ln Nw / dz positive when the
water's radiance falls with depth.

**What the package cannot supply.** The water's radiance along the line
of sight and its K depend on the light field as well as the water; both
are the caller's. Duntley takes K as constant along the path, which he
found seldom matters beyond the first metres below the surface, as
sighting ranges rarely exceed 2/K (p. 230).

## 35. The clear-sky irradiance at the sea surface: Gregg and Carder (1990) Table 1, and a misprint in eq. (44) (confirmed)

`gregg1990_irradiance` (DECISIONS.md section 76) is the model of Gregg,
W. W. and Carder, K. L. (1990), "A simple spectral solar irradiance model
for cloudless maritime atmospheres", Limnol. Oceanogr. 35(8), 1657-1675,
DOI `10.4319/lo.1990.35.8.1657`. The PDF is a scan with an OCR text
layer; the equations and Table 1 were read from the page images at 300
dpi.

**Table 1** (pp. 1662-1663) gives, at every nm from 350 to 700, the mean
extraterrestrial irradiance H0 (W m-2 nm-1), from the revised Neckel and
Labs (1984) spectrum corrected for overlap and interpolated to 1 nm, and
the ozone (Inn and Tanaka 1953), water vapour and oxygen (from the 5S
code) absorption coefficients, cm-1 (p. 1661). It is shipped as
`gregg1990_table1.csv`, 351 rows as printed, with status `transcribed`.

- Water vapour and oxygen are printed from 560 nm only. Below that the
  file holds 0, with a note on each row; eqs. (18) and (19) give a
  transmittance of 1 for a zero coefficient.
- The OCR layer reads the oxygen coefficient at 676, 677, 681 and 685 nm
  as "O.OO@", "o.ood" and "0.00;"; the page prints 0.000. It splits the
  689 nm row across two lines. Every value was compared with the page
  images, not only these.
- Against Bird and Riordan (1984), SERI/TR-215-2436, Table 2-1, the same
  Neckel and Labs revised spectrum in 122 bands: H0 averaged over the 11
  nm around each of their wavelengths from 350 to 690 nm lies within 5
  percent of theirs, and within 1.5 percent except at 350 nm (the end of
  the table, +4.5) and 430 nm (the G band, +4.0). A check that would catch
  a misplaced digit, not a small misreading; the page images are what the
  values rest on.

**The misprint.** Eq. (44), p. 1666, prints Fresnel's reflectance for the
direct sun as

    rho_d = 1/2 [ (1/2) sin2(theta - theta_r) / sin2(theta + theta_r)
                  + tan2(theta - theta_r) / tan2(theta + theta_r) ]

with a second 1/2 inside the bracket. As printed, it gives 0.0159 for the
sun overhead, where Fresnel's law gives ((n - 1)/(n + 1))^2 = 0.0212 with
the paper's n = 1.341, and 0.0143 at 40 degrees, where the paper's
eq. (46) takes over at 0.0253 (p. 1667). Without the inner 1/2 it gives
0.0254 at 40 degrees, continuous with eq. (46) to the paper's rounding.
The package uses Fresnel's law without it.

**Checks against the paper's own results.**

- Table 5 (p. 1670), the share of diffuse light in the global irradiance
  at 60 degrees under its standard conditions and at both ends of each of
  its eight ranges: all seventeen values reproduced to the printed whole
  percent (34 to 79).
- The same table's rms and largest deviations agree in sign and within
  25 percent in size (the model's are 0 to 3.6 points from the printed
  ones), and the wavelength of the largest within 10 nm, except for the
  24 h mean wind, whose deviation is 0.15 to 0.27 percent at every
  wavelength (printed 358 nm, the model's 381). The paper does not say
  how its rms was taken.
- Table 4 (p. 1669): direct to diffuse 59:41 at V = 16 km with air mass
  type 10 and 37:63 at V = 8 km with type 1, the Angstrom exponents 1.2
  and 0.2, and about 2 W m-2 less over 350-700 nm in the second, all
  reproduced with Table 5's other conditions, which the paper does not
  restate for Table 4.
- Foam reflectance at 20 m/s about 2.3 percent, as in Fig. 2 (p. 1667),
  with the air density as printed, 1.2 x 10^3 g m-3.

## 36. Coefficients for renderers: three RGB spaces, Petzold's integral, and one renderer's spectral range (note)

`rgb_attenuation`, `henyey_greenstein_fit` and `spectral_coefficients`
ship no table. What they rest on, besides the waters and Petzold's
stations already described, is recorded here (DECISIONS.md section 82).

**The RGB spaces.** Primaries and whites as chromaticities, the matrix
from XYZ derived from them as for sRGB (section 12):

- `linear_srgb`: IEC 61966-2-1, the primaries the package already used,
  without the transfer function.
- `acescg`: the AP1 primaries, red (0.713, 0.293), green (0.165, 0.830),
  blue (0.128, 0.044), and the ACES white (0.32168, 0.33767), from the
  Academy's ACEScg specification, read on docs.acescentral.com
  (2026-11-14).
- `rec2020`: Rec. ITU-R BT.2020-2 (10/2015), Table 3, p. 3: red (0.708,
  0.292), green (0.170, 0.797), blue (0.131, 0.046), D65 (0.3127,
  0.3290), read from the ITU's PDF.

Tested: each matrix sends its white to (1, 1, 1) and each primary to its
own axis, and the sRGB matrix is the one `xyz_to_srgb` uses. The
tabulated D65 comes out within 5 x 10^-4 of (1, 1, 1) in linear sRGB,
the difference between the table and its defined chromaticity.

**Petzold's integral, taken again.** The mean cosine integrates the vsf
between the report's 55 angles as a power law, as `vsf_at` interpolates
it. The same integral of the vsf alone, plus the report's share below
0.1 degree, gives back the printed s at all eight stations, low by 0.14
to 0.24 percent. The mean cosines are 0.869 (AUTEC 8) to 0.945 (HAOCE 5
and 11). Every one of them rests on the share below 0.1 degree, 3.4 to
14.5 percent of s, counted at a cosine of 1, which the report extended
with a power law at every station (section 21); they warn.

**One renderer's spectral range.** Mitsuba 3.9.1's spectral variants
sample 360 to 830 nm (its `MI_CIE_MIN` and `MI_CIE_MAX`), and a medium
whose spectrum stops short of either end renders NaN pixels: in a test
scene, a spectrum defined over 360-800 nm gave 765 of 768 values NaN,
400-700 nm all 768, 360-830 none. Williamson & Hollins stop at 800 nm,
so `examples/rendering_export.py` holds their 800 nm values to 830 nm,
stating it; beyond 800 nm the CIE x-bar has 1.1 x 10^-6 of its weight
and z-bar none. The package returns only what the source has.

**Two more renderers, run (1.11.1).** Each medium that
`examples/rendering_export.py` writes for Jerlov III was rendered by hand
in a test scene, outside CI: a slab of the water 5 m thick between a
camera and an emitting plane, the plane hidden from the volume's
scattering or the scattering left out, so that the image is the
transmitted light alone.

- Blender 5.3.0, the `bpy` module from PyPI, Cycles on the CPU, working
  space ACEScg and again Linear Rec. 709 (set with
  `bpy.ops.wm.set_working_color_space`; the property itself is read-only
  in 5.3), volume bounces off. With the example's Volume Absorption
  values the transmittance per channel was exp(-sigma_a r) to 7 digits;
  with its Volume Scatter values exp(-sigma_s r) within 0.2 percent at
  1024 samples per pixel, the Monte Carlo's noise. Only with Cycles'
  denoising off: on by default for a final render, it made a white
  emitter read 1.13 and moved every ratio by about 5 percent. Blender
  5.3.0 also has a Volume Coefficients node.
- pbrt-v4, built from github.com/mmp/pbrt-v4 (commit b0bdf46) on the
  CPU, without Wayland: the camera in the example's spectral medium, the
  default RGB film in sRGB. The transmittance per channel through a and
  through a + b, at 4096 samples per pixel and three seeds, agreed with
  the one computed from the same spectra and the CIE 1931 observer within 2
  percent in red and green; blue came out 3 to 4 percent high, a little
  more than the seeds spread, about 2 percent, and the cause was not
  found. One of the runs at 4096 samples crashed
  in pbrt and was repeated. The camera's medium must be named before
  the `Camera` directive, or the camera is in vacuum.

## 37. Measured reflectances of ten materials: the USGS Spectral Library (note)

`usgs2017_reflectance.csv` holds ten spectra from Kokaly, R. F., Clark,
R. N., Swayze, G. A., Livo, K. E., Hoefen, T. M., Pearson, N. C., Wise,
R. A., Benzel, W. M., Lowers, H. A., Driscoll, R. L., and Klein, A. J.
(2017), USGS Spectral Library Version 7 Data, U.S. Geological Survey data
release, DOI `10.5066/F7RR1WDJ`, which its metadata marks CC0 1.0; the
report is USGS Data Series 1035, DOI `10.3133/ds1035`.
`usgs2017_reflectance(material)` returns one (DECISIONS.md section 85).

**What was taken.** From `ASCIIdata_splib07a.zip` (21,812,828 bytes, on
ScienceBase under the DOI), the "splib07a" spectra, as measured, not
resampled. Each is an ASD spectrometer record of absolute reflectance
("ASDFRa AREF"): the reflectance relative to a Spectralon panel times the
panel's own reflectance, eq. (1) of Data Series 1035, p. 4; the ASD
instruments are described on p. 6. The ASD has a channel at every nm
from 350 to 2500; the 481 from 350 to 830 nm are shipped, the range of
the CIE observer and a little below. In that range the bandpass is 3.35
to 8.65 nm (FWHM), from the library's
`splib07a_Bandpass_(FWHM)_ASDFR_StandardResolution.txt`.

| Key | Record | Name as printed |
|---|---|---|
| `white_pvc` | 19775 | Plastic_PVC GDS338 White |
| `black_abs` | 19559 | Plastic_ABS GDS341 BlackPipe |
| `grey_concrete` | 18568 | Concrete GDS375 Lt Gry Road |
| `red_nylon` | 19080 | Nylon_Fabric GDS431 Red RpSt |
| `orange_cadmium` | 18413 | Cadmium_orange_0 GDS786 |
| `yellow_cadmium` | 18440 | Cadmium_yellow_6 med GDS788 |
| `green_tarp` | 19802 | Plastic_Tarp GDS339 Green |
| `blue_green_hdpe` | 19577 | Plastic_HDPE GDS391 Blu-Grn |
| `blue_nylon` | 19098 | Nylon_Fabric GDS433 Blu RpSt |
| `violet_cobalt` | 18485 | Cobalt_violet GDS803 |

**The modification**, as the release's use constraints ask to be
described: only the wavelength range is shortened, to 350-830 nm. Each
value is copied as the library prints it, in its own notation, and
`tools/build_usgs2017.py` checks the record line of each file, that the
wavelengths are the ASD's 1 nm channels, that no value in the range is
the library's deleted-channel marker, and that every value lies between
0 and 1. The release's metadata also asks that the data not be
misrepresented and that the USGS be acknowledged; the package's
docstrings and this section name it.

**Why these ten.** To span neutral and hue with materials found in and
around water: white, black and grey, and red to violet. None is
fluorescent: the library's fluorescent yellow webbing was left out,
since a fluorescent sample's measured reflectance includes light the
spectrometer's lamp made it emit, which the light under water would not.
The cadmium and cobalt entries are artists' pigments.

**What was not read.** The release describes each sample in HTML, with
photographs, in a 1.3 GB file behind a download page this environment
could not use, and the USGS's per-sample pages refused the request. The
names above are therefore the record lines as the ASCII files print
them, and nothing about a sample beyond its name is claimed: not how it
was prepared, and not whether a pigment was a powder. These are dry
samples measured in a laboratory; under water a surface is wet, which
changes its reflectance, and another sample of the same kind of
material would not reflect the same.

## 38. Input files for OSOAA and HydroLight: what was run and what was not (note)

`osoaa_user_profile`, `osoaa_phase_function` and `hydrolight_ac9_file`
write a water's absorption and scattering, and one of Petzold's phase
functions, in the input formats of two radiative transfer codes
(DECISIONS.md section 86). No table is shipped for them; this section
records how the files were checked against the codes.

**OSOAA**, run by hand outside CI. The code is CNES's
`RadiativeTransferCode-OSOAA` (GPL v3), commit `8e4914f` (2025-04-03),
built with GNU Fortran 13.3.0 from its own Makefile; the formats are
those of its User Manual V2.0, sections 3.6.3 and 3.6.4, pp. 80-82, and
its limits are `CTE_NZ_MAX_USER_PROFILE` (500) and `CTE_MAXNB_ANG_EXT`
(200) in `inc/OSOAA.h`. The pure seawater it adds back is the row for
440 nm of its `fic/OSOAA_SEA_MOL_COEFFS_JUNE_2013.txt`: a = 0.00635 and
b = 0.00501629 per m.

The files of `examples/radiative_transfer_inputs.py`, Jerlov III at 440
nm with depths 0, 10 and 50 m, and HAOCE 5 with -F12/F11 = 0 and F22/F11
= F33/F11 = 1, byte for byte, were run with `-OSOAA.Wa 0.440
-HYD.Model 3 -SEA.Depth 50.0`, a sun at 30 degrees, a black seabed and
the code's maritime aerosol. OSOAA read both without complaint, and its
sea profile (`PROFILE_SEA.txt`) gives an optical thickness of 21.64933
at 50 m, a total extinction of 0.4330 per m, and a share of scattering
of 0.01155 + 0.70899 = 0.72054. Williamson and Hollins's c and b/c for
Jerlov III at 440 nm are 0.433 and 0.72055. Before the functions were
written, two runs that differed only in the cross-section lines at the
head of the phase function file gave byte-identical radiances and
fluxes: `-HYD.Model 3` does not read them.

What was not checked: the radiances themselves against any other code
or measurement, other wavelengths, other stations, and polarization
ratios other than these.

**The phase function was written 4 pi too small (found later; fixed in
1.15.5).** OSOAA always truncates the forward peak of the hydrosols' phase
function (User Manual V2.0, section 4.2.3, p. 96), and each run reports the
truncation coefficient A in `Advanced_outputs/PM_PHYTO.txt`; A / 2 of the
hydrosols' scattering is treated as unscattered. For a phase function
given in a file, OSOAA splines F11 in the cosine and takes A from it
without normalising it (`OSOAA_HYDROSOLS.F`, `SOS_DECOMPO_LEGENDRE` in
`OSOAA_PARTICLES_RAD.F`): it expects F11 whose integral over the sphere is
4 pi. `osoaa_phase_function` wrote vsf / b, whose integral is 1, from
release 1.14.0 to 1.15.4, and OSOAA treated 96.5 to 97.8 percent of the
scattering as unscattered in every run of section 39's first version,
where Petzold's functions hold 84 to 89 percent within 23 degrees. Release
1.15.4 put this down to OSOAA (DECISIONS.md section 92); that was wrong,
and the fault was this package's (section 93). The runs were not checked
against the code's source until the user asked whether they had been.
Since 1.15.5 the function writes 4 pi vsf / b, and the runs here and in
section 39 were made again.

**HydroLight** was not available and was not run. `hydrolight_ac9_file`
follows the "standard format for ac-9 data" of the HydroLight 5.1
Technical Documentation (Mobley 2012), section 7.3, pp. 55-56; its tests
read the file back by that description and nothing more.

**OSOAA's results, read back (1.15.0).** The run above is kept in
`tests/data/osoaa_iii_440/`, for the tests and not in the wheel: its
`Flux.txt`, `RESLUM_vsZ.txt`, `RESLUM_vsVZA.txt` and `ListParam.txt`, as
OSOAA wrote them, and the two input files, which the package's writers
still produce byte for byte (DECISIONS.md section 87). OSOAA is GPL v3;
these are the results of a run, not its code. Besides the parameters
above, the run had a maritime aerosol (Shettle and Fenn, 98 percent
relative humidity) of optical thickness 0.1 at 550 nm, a wind of 7 m/s,
a black seabed at 50 m, and its radiances at 10 m depth and at nadir.
`ListParam.txt` names the files `je.txt` and `jp.txt`, the names they
were run under, and prints the user profile under the label
`-HYD.ExtData`.

What the readers recover from it:

- The direct flux at the top of the atmosphere is 2.72070, pi cos 30
  degrees: the extraterrestrial irradiance is pi, as OSOAA's manual
  says. Totals are direct plus diffuse, and the printed Eu/Ed is their
  ratio, to the printed digits.
- The surface is printed once above (0.00000) and twice below
  (-0.00000), the two levels of optical thickness 0 and 1e-4 in the sea.
  The radiance against depth has the same 81 levels.
- The reflectance of `RESLUM_vsZ.txt` is pi I / Ed with Ed from
  `Flux.txt`, to five digits.
- The nadir appears twice in `RESLUM_vsVZA.txt`, as -0.00 and 0.00, one
  row for each half-plane, with one value.
- OSOAA's direct flux in the sea falls at 0.235 per m, not at c /
  cos(theta_w) = 0.467: OSOAA truncates the forward peak of the hydrosols'
  phase function and counts the light so removed as transmitted (User
  Manual V2.0, section 4.2.3, p. 96). Its truncation coefficient for this
  run, in `PM_PHYTO.txt`, is 1.40215, and c (1 - (b/c) A/2) /
  cos(theta_w) is 0.231. Only the totals are fit for Kd.
- The mean Kd of Ed from 0 to 50 m is 0.1577 per m. Jerlov's Kd for type
  III at 440 nm is 0.129 in the first edition (1968) and 0.145 in the
  second (1976); the Kd that HydroLight made of Solonenko and Mobley's
  (2015) own a and b for the type, under a clear sky in deep water, is
  0.123. The run's sun, sky and surface are its own, and a Jerlov type
  does not fix them.
- Until release 1.15.5 this run was made with the phase function 4 pi too
  small (below), and OSOAA's Kd came out lower; release 1.15.4 keeps
  those files.

## 39. Williamson & Hollins's IOPs against Jerlov's Kd (note)

Does a Jerlov type's a and b, put through a radiative transfer
calculation, give back the Kd Jerlov printed for it, and which of the
conditions a type does not fix move the answer most? The first answer to
this, in release 1.15.3, was wrong; it is kept at the end of this section
with the reason (DECISIONS.md sections 90, 92 and 93).

**Williamson & Hollins's waters were chosen by their Kd.** Their code and
data (figshare `10.6084/m9.figshare.20290782`, `20221121-Dstl_MIOP_code_v3.py`
and `ip_jerlov.csv`) assign each measurement campaign the Jerlov type whose
Kd is nearest its own measured Kd in the upper 10 m, by mean absolute
percentage error, and keep it only within 25 percent (their paper, section
2.E). The reference Kd in `ip_jerlov.csv` equal `jerlov1976_kd.csv` at
every wavelength compared here. Their a and b are then averages over the
campaigns so chosen; they are not derived from Jerlov's Kd, but they are
selected by it. The paper itself tests the consistency (section 3.D,
Table 5): from the averaged a and b, through three analytic relations
whose parameters they fitted, Kd within 14 to 17 percent of Jerlov's, as
a mean absolute percentage error.

**The calculation.** `tools/kd_monte_carlo.py`, a Monte Carlo written for
this: homogeneous, infinitely deep water, a collimated beam at the
refracted sun, scattering angles drawn from a Petzold station's function,
no sky, no atmosphere, no surface reflection. With no scattering its Kd is
a / mu0 within the noise; against Morel and Loisel's relation for the
first optical depth, as Williamson & Hollins print it (their Eq. 2), it
agrees within 1 percent with NUC 2240's phase function for b/a from 0.5
to 10, within 4 percent with AUTEC 7's and up to 8 percent lower with
HAOCE 5's, following each function's backscattering. `tools/kd_closure.py`
made 240 runs, kept with their seeds and Kd in
`examples/data/kd_closure/runs.csv`: Williamson & Hollins's a and b for
IB, II, III, 1C, 3C and 5C at the twelve wavelengths Jerlov printed inside
their measured 412-715 nm, the Petzold station nearest each type's b at
530 nm, the sun 30 degrees from the zenith; then, on IB and III, the sun
at 0 and 60 degrees, the stations AUTEC 8, HAOCE 5 and NUC 2200, and the
pure water of Pope & Fry, Mason et al. or Lee et al. under the type's
contents. Kd is the mean over the first penetration depth.
`examples/closure_with_jerlov_kd.py` reads the runs and prints every
figure below.

**Against Jerlov.** The computed Kd over Jerlov's, at the twelve
wavelengths:

| Type | Over Jerlov (1976) | Over Jerlov (1968) |
|---|---|---|
| IB | 0.98 to 1.47 | 0.99 to 1.56 |
| II | 0.92 to 1.10 | 0.81 to 1.22 |
| III | 0.84 to 0.98 | 0.65 to 1.09 |
| 1C | 0.56 to 1.03 | 0.72 to 1.11 |
| 3C | 0.51 to 1.01 | 0.66 to 1.01 |
| 5C | 0.64 to 1.02 | 0.64 to 1.01 |

**What the unrecorded conditions can do**, on IB and III, each alone:

| Condition | Change in Kd |
|---|---|
| The sun, 0 or 60 degrees against 30 | -7.7 to +22.4 percent |
| The Petzold station's phase function | -6.4 to +14.5 percent |
| The pure water under the type's contents | -10.9 to +9.3 percent |

Taken to 10 percent of the surface light instead of the first penetration
depth, Kd moves by +0.3 to +8.0 percent.

**What it says.** Together the three conditions move Kd by 0.77 to 1.53
times. Against Jerlov (1976) the computed Kd lies outside that reach only
at the blue end: IB at 425, 450 and 475 nm (1.31 to 1.47 times Jerlov's),
1C at 425 nm (0.56), 3C at 425 and 450 nm (0.51 and 0.62) and 5C at 425 nm
(0.64). Elsewhere, Williamson & Hollins's IOPs and Jerlov's Kd are
consistent within the conditions neither records. At the blue end, the
clearest type's measured IOPs attenuate more than Jerlov's Kd, and the
coastal types' less. Why, the package cannot say.

**A second calculation: OSOAA (1.15.5).** The 408 runs of OSOAA (CNES,
commit `8e4914f`, section 38) of the first version, made again with the
phase function corrected, are kept in `examples/data/osoaa_closure/`:
the same a and b and the same stations, with OSOAA's own sky (a maritime
aerosol of optical thickness 0.1 at 550 nm), a surface under a 7 m/s wind
and a black seabed six of Jerlov's penetration depths down; on IB and
III, the sun, the station, the pure water, the aerosol and the wind are
varied. 46 runs cannot be made: from 650 nm OSOAA's own pure water is
above the aw Williamson & Hollins built a on, and OSOAA always adds its
own back.

- In the 62 base runs it can make, OSOAA's Kd is 1.007 to 1.096 times the
  Monte Carlo's, the higher the bluer the light and the clearer the
  water: 1.096 for IB at 425 nm, 1.007 for 1C at 675 nm. Section 40
  accounts for it: OSOAA scatters pure water's share of b by water's own
  phase function and has a sky, and the Monte Carlo here does neither.
- OSOAA treats 56.2 to 72.7 percent of the hydrosols' scattering as
  unscattered (`truncation.csv`, from each run's `PM_PHYTO.txt`).
- The station moves its Kd by -5.8 to +14.9 percent, against the Monte
  Carlo's -6.4 to +14.5; the aerosol and the wind by -0.3 to +0.8.
- Against Jerlov (1976), OSOAA's Kd lies outside the reach of the three
  conditions at the same places as the Monte Carlo's, but for 5C at
  425 nm, which it brings just inside.

**What 1.15.3 said, and why it was wrong.** Release 1.15.3 made this
comparison with OSOAA alone and concluded that the coastal types' IOPs
give down to half of Jerlov's Kd, that the phase function hardly matters
(under 1.5 percent), and that the backscatter ratio needed was beyond any
Petzold measured. The package had written OSOAA's phase function 4 pi too
small (section 38), and OSOAA treated 96.5 to 97.8 percent of the
scattering as unscattered. Its Kd were 0.7 to 23.1 percent below the
Monte Carlo's in the 62 base runs it could make, the more so the larger
b/a, and with the scattering truncated, the phase function could not show
its effect. Release 1.15.4 found the Kd too low but put the cause in
OSOAA; release 1.15.5 found it in the package. Those runs are kept in
`examples/data/osoaa_closure_f11_too_small/` as the record. The
conclusions above replace them.

## 40. Solonenko & Mobley's IOPs through the Monte Carlo and OSOAA, against their HydroLight Kd (note)

Solonenko & Mobley (2015) printed, beside the a and b they retrieved for
ten Jerlov types, the Kd HydroLight computed from them, K_d^H (section
19). That is a check on any other calculation given the same a and b,
and the only one the package ships against a widely used code
(DECISIONS.md section 94).

**What the paper says of the HydroLight runs.** The retrieved a and b,
"a Petzold average-particle phase function", a clear sky, infinitely deep
water and no inelastic scattering (p. 5396); the phase function as pure
water's and the particles' weighted by their shares of b, the particles'
the average of Petzold's coastal, harbor and ocean functions with a mean
cosine of 0.924 (p. 5394); pure water's b as 5.83e-3 (400 / lambda)^4.322
(Eq. 8a, p. 5395); a modelling depth of 10 scattering lengths, 6 for
Jerlov III (p. 5401). It does not print the sun, the average phase
function or the depth K_d^H belongs to.

**The calculation.** `tools/kd_monte_carlo.py` (section 39) with two
options added: pure water's share of b turned by water's own phase
function (the shape of `pure_water_vsf`), and a share of Ed below the
surface coming from a sky uniform in radiance in the air, weighted by
Fresnel's transmittance and refracted. Off, it draws the same random
numbers as before and reproduces section 39's runs bit for bit; its new
checks (`--check`) put a sky with no scattering within 0.2 percent of the
quadrature and water's phase function at a mean cosine of 0.
`tools/sm_closure.py` made 2457 runs, kept in
`examples/data/sm_closure/runs.csv`: the 143 cells of the ten types from
350 to 700 nm every 25 nm where a, b and K_d^H are all given, with the sun
of the paper's own Eq. (3) (15 degrees from the zenith for I to III, 45
for the coastal types), NUC 2240's phase function (mean cosine 0.926,
the nearest to 0.924), and the sky's share from `gregg1990_irradiance`
for an open-ocean aerosol of optical thickness 0.2 at 550 nm; on every
cell, the other seven stations, the sun at 0, 30 and 60 degrees and the
aerosol at 0.05 and 0.4. Then section 39's 240 runs of Williamson &
Hollins's IOPs again with the water's scattering and the sky. 30 of the
143 cells carry a b flagged suspect (section 6); they are kept and
marked. Kd is taken to 10 percent of the surface light.

**Against HydroLight.** The Monte Carlo's Kd over K_d^H:

| Monte Carlo | Median | Within 10 percent | Range |
|---|---|---|---|
| As section 39: one phase function, no sky | 0.945 | 79.7 percent | 0.769 to 1.110 |
| With pure water's own scattering | 0.951 | 90.2 percent | 0.852 to 1.138 |
| With it and a sky | 0.970 | 94.4 percent | 0.881 to 1.157 |

The criterion set before the runs, a median within 0.95 to 1.05 and 90
percent of the cells within 10 percent, is met by the last two rows. By
type, the ratio is 0.93 to 1.00 for I, IA, IB, 3C, 5C and 9C, 1.00 to 1.08
for 1C and 1.00 to 1.10 for 7C; II reaches 1.16 (1.13 to 1.16 from 425 to
500 nm), and III, the one type HydroLight ran to 6 scattering lengths,
stays at 0.88 to 0.96. The other stations move the Monte Carlo's Kd by
-12.7 to +26.0 percent, the sun by -12.7 to +21.5 and the aerosol by -1.8
to +2.0; K_d^H lies inside what they and the depth make of it at all 143
cells. With the average-particle phase function unknown, the Monte Carlo
and HydroLight agree as closely as can be told.

**OSOAA on the same cells**, with its own pure water taken off and added
back so that it runs Solonenko & Mobley's totals, NUC 2240, its own
aerosol and a 2 m/s wind (`tools/osoaa_sm_closure.py`,
`examples/data/osoaa_sm_closure/`): 29 of the 143 cells cannot be run,
where a or b is below OSOAA's own pure water. At the 114 it can run, its
Kd is 0.986 to 1.037 times the Monte Carlo's and 0.877 to 1.158 times
K_d^H (median 0.978). Given the same IOPs and the same phase function,
OSOAA and the Monte Carlo agree within 4 percent.

**Section 39 again.** With pure water's scattering and the sky,
Williamson & Hollins's Kd rise by +1.3 to +7.6 percent, and OSOAA's Kd
there is 0.991 to 1.018 times the Monte Carlo's instead of 1.007 to
1.096: that was the gap. The conditions now move Kd by 0.79 to 1.44
times; against Jerlov (1976) the Kd lie beyond that at the same blue
cells as before (IB at 425 to 475 nm, now 1.41 to 1.55 times Jerlov's; 1C
and 5C at 425 nm; 3C at 425 and 450 nm), and also IB at 500 nm (1.27),
just beyond.

## 41. The blue end: the Kd measured in the same waters (note)

Section 40 left the blue end unexplained: Williamson & Hollins's averaged
a and b give Kd 1.41 to 1.55 times Jerlov's (1976) for IB at 425 to 475
nm, and 0.53 to 0.66 for the coastal types at 425 nm (1C, 3C, 5C), beyond
what the sun, the phase function and the pure water can make. Their
figshare dataset keeps every step of their processing, and three of its
files answer most of it (DECISIONS.md section 95). Each was checked
against figshare's MD5 by `tools/blue_end.py`, which reduces them into
`examples/data/blue_end/`:

| File there | From | What |
|---|---|---|
| `kd_campaigns.csv` | `op_STEP_5_k.csv` | 15308 Kd values of the 2710 campaigns kept, upper 10 m, with the type each was given |
| `iop_campaigns.csv` | `op_STEP_5_a.csv`, `op_STEP_5_b.csv` | a and b of every campaign behind the averages, with its type |
| `matched.csv` | `op_STEP_7_kab.csv`, unchanged | 473 entries of a, b and Kd measured in the same campaign at 412, 510, 532 or 555 nm |
| `runs.csv` | the Monte Carlo | Kd from each matched entry's own a and b, 2365 runs |
| `closing_a.csv` | the Monte Carlo | the a that would close each blue cell |

Crown copyright (2022), Dstl; Open Government Licence v3.0. Not in the
wheel. Each campaign's type is Williamson & Hollins's: the Jerlov type
whose Kd (1976) is nearest the campaign's own over its wavelengths, by
mean absolute percentage error, kept within 25 percent (their section
2.E).

**The coastal types: the waters, not the IOPs.** The campaigns typed 1C,
3C and 5C measured Kd at 412 nm of a median 0.59, 0.53 and 0.56 of Jerlov's
(1976), and at 443 nm 0.78, 0.72 and 0.72; by 490 nm they are 0.91 to 1.03.
That is what their averaged IOPs gave (0.59, 0.53, 0.66 at 425 nm). And
where a, b and Kd were measured in the same campaign, the Monte Carlo from
the campaign's own a and b gives a median 0.90, 0.93 and 1.06 of its own
Kd at 412 nm (0.85 to 1.19 with the sun or the station varied). So the
IOPs and the radiative transfer agree with the Kd measured in the same
water; what disagrees is that water's blue Kd and the one Jerlov printed
in 1976. Against Jerlov's 1968 edition, whose coastal Kd at 425 nm are
0.65 (1C), 0.77 (3C) and 0.89 (5C) of the 1976 values, the measured Kd at
412 nm are a median 0.85, 0.66 and 0.62: for 1C most of the gap is the
revision Jerlov made between the editions, for 3C and 5C less of it. Why he raised the coastal blue
in 1976 is a question for his 1976 text, which this package has not seen.
To close the gap from the IOPs side, the coastal a would have to rise by
3.4 to 5.2 standard deviations of their measured points (1.7 for 5C).

**IB: the IOPs, not Jerlov.** The campaigns typed IB measured Kd of a
median 1.02, 1.12 and 1.03 of Jerlov's (1976) at 412, 443 and 490 nm: the
water agrees with Jerlov. It is IB's averaged a that does not. It rests on
six campaigns, and they disagree with themselves:

- in two (292 and 293, Sea of Japan, 1999) the measured a is at or above
  the Kd measured in the same campaign, at 440 and 510 nm (293 at 555 nm
  too), which no
  radiative transfer calculation can give back: by Gershun's law a = mu
  K_E with mu at most 1, and every Monte Carlo run of sections 39 and 40
  has Kd at least 1.012 times a;
- in two (1841 and 1845, near Japan, 2001) a at 412 nm is a third of their
  own Kd, and the Monte Carlo from their a and b gives a median 0.57 of
  the measured Kd at 412 nm;
- two (1642 and 1648) measured Kd, in the blue, only at 490 nm.

To close IB's blue cells, a would have to fall by 1.0 to 1.8 standard
deviations of IB's measured points (2.4 to 4.3 standard errors): within
the spread of six inconsistent campaigns. Which of them are right the
package cannot say.

**a at or above Kd is not rare.** In the matched set it holds in 3 of 11
entries for IB, 9 of 88 for II, 30 of 211 for III, 3 of 79 for 3C, 3 of 12
for 5C and none of 68 for 1C. Such entries cannot be closed by any phase
function, sun or sky, and they enter the averages as they are.

**The spread between types.** From one type to the next, IB to 5C, the
measured a at 412, 440 and 488 nm rises by 1.2 to 2.1 pooled standard
deviations and b by 0.9 to 1.4: the types overlap, and a single campaign
can sit nearer its neighbour's average than its own.

**What Jerlov and his colleagues wrote (1.15.8, DECISIONS.md section 96).**
Chapter 10 of both editions was read. Jerlov (1976, *Marine Optics*,
p. 133) states the changes from 1968 only for the oceanic types: higher at
600 nm for I, IA, IB and II, and for III lower at 550 and 575 nm and
"somewhat higher values around 425 nm which may be caused by chlorophyll
absorption". Of the coastal types he says (p. 137) that they "are derived
from observations along the coast of Scandinavia and western North
America. These northern water masses are characterized by a relatively
high amount of yellow substance. Some recent material (Aas, 1967, 1969 and
Højerslev, 1974a) has substantially fortified the basis for this special
classification." Jerlov (1968, *Optical Oceanography*, pp. 122 and 124)
gives the same origin, without yellow substance, and "evidence that
coastal waters which contain a variable amount of terrigeneous material
show divergent behaviour in the shortwave part of the spectrum". No reason
for the higher coastal blue of 1976 is stated in either.

Two later papers by Jerlov's Copenhagen colleagues bear on it. Aas,
Højerslev, Høkedal and Sørensen (2013), *Oceanologia* 55(2), 471-482,
doi:10.5697/oc.55-2.471, p. 477: in the open Nordic Seas "coastal types
from 1 to 5 occur frequently. These coastal types are not real coastal
waters with high contents of yellow substance and inorganic particles;
they are caused by algal blooms". Aas & Højerslev (2001), *Oceanologia*
43(2), 139-168, p. 146: the constants of the linear relations between
Kd at a wavelength and at 465 nm, on which the classification rests, "may
change from one oceanic area to another", and their own such relations for
the Norwegian Sea "appear to be valid only for the type of water from
which they were obtained". That is consistent with what was found above:
Williamson & Hollins typed campaigns by matching Kd over all wavelengths,
which a water of coastal turbidity but little yellow substance can do
while its blue Kd stays well below the yellow-substance-rich waters
Jerlov's coastal types came from. It is not shown to be the cause; the
campaigns' yellow substance is not in the data.

Three more papers, obtained by the user, add to this. Højerslev (1978),
*Limnol. Oceanogr.* 23(5), 1076-1079, doi:10.4319/lo.1978.23.5.1076,
writing from Jerlov's own institute, chose "Jerlov's classification of
coastal waters (Jerlov 1976) ... because it takes into consideration
average optical conditions for coastal waters rich in yellow substance"
(p. 1078), and found a daylight spectrum where the Baltic meets the
Kattegat "intermediate to and conforms with Jerlov's coastal types 3 and
5" (p. 1079). Højerslev & Aas (1991), *J. Geophys. Res.* 96(C9),
17003-17005, doi:10.1029/91JC01822, pp. 17,003-17,004, note that the
classification's values at 310 nm "seem to be based on six stations from
the western Pacific and the Indonesian seas and one from the
Mediterranean. These values were omitted in his last work [Jerlov,
1978], which may indicate that he doubted their representativity", and
that the waters of the Baltic, Kattegat, Skagerrak, German Bight and North
Sea "are characterized by high contents of yellow substance". Topliss,
Hunter & Simpson (1980), *Mar. Environ. Res.* 4, 65-79, p. 78, found "all
classes of coastal optical water type" at one near-shore site in North
Wales over a year. None states why the coastal blue of 1976 is higher
than that of 1968.

Not obtained, and the likeliest places for the answer: Jerlov (1978), *The
optical classification of sea water in the euphotic zone*, Rep. Dept.
Phys. Oceanogr. 36, Univ. Copenhagen, 46 pp., in which the coastal types
were reduced to 1, 3 and 5; Aas (1969), *On submarine irradiance
measurements*, Rep. 6 of the same series; Højerslev's reports of 1974
(Rep. 23, the Baltic, and Rep. 26, the Western Mediterranean, lettered a
and b differently by different authors); and what Jerlov cites as Aas
(1967), possibly Aas (1971), *Sarsia* 46, 59-78, "Irradiance in
Hardangerfjorden 1967". None has a DOI that was found.


## 42. Kd of the visible and the shortwave, and the euphotic depth, from a and bb (note)

Lee, Du, Arnone, Liew and Penta (2005), J. Geophys. Res. 110, C09019,
give the mean attenuation of the visible (350-700 nm) energy from the
surface to a depth z, K_VIS(z) = K1 + K2 / (1 + z)^0.5, with K1 and K2
from a(490), bb(490) and the sun, fitted to 300 HydroLight runs; that of
the infrared (700-2500 nm), K_IR(z), from z and the sun alone; and the
shortwave transmittance T(z) = F_VIS exp(-K_VIS z) + (1 - F_VIS) exp(-K_IR
z). Lee, Weidemann, Kindle, Arnone, Carder and Davis (2007), J. Geophys.
Res. 112, C03009, solve K_VIS(z) z = -ln f for the depth of a fraction f;
at 0.01, the euphotic depth. Since 1.16.0 these are `lee2005_kvis`,
`lee2005_kir`, `lee2005_shortwave_transmittance` and
`lee2007_depth_of_fraction` (DECISIONS.md section 98). They are set here
beside the two measured tables the package ships that they can be held to.

No source gives bb for a Jerlov type. a(490) and b(490) are Solonenko &
Mobley's (2015), for all ten types, and Williamson & Hollins's (2022), for
IB to 5C, each read at 490 nm between its tabulated wavelengths; bb = bw
/ 2 + r (b - bw), bw the source's own pure water term and r the B/S of
each of Petzold's eight stations (0.013 to 0.044). The base is NUC 2240,
r = 0.018. Solonenko & Mobley's b of I and IA rests on values flagged
suspect, and it warns.

**The depths of Jerlov's (1977) quanta levels.** Jerlov measured the
depths where 30, 10, 3 and 1 percent of the quanta (350-700 nm) are left,
for seven types (`jerlov1977_quanta`). Against them, Lee et al.'s depths,
with the sun at 15 degrees for the oceanic types and 45 for the coastal
(Jerlov's own is not recorded), are, as the ratio computed / measured
(`examples/euphotic_zone.py`, section 7):

| Type | Solonenko & Mobley, 30 / 10 / 3 / 1 % | Williamson & Hollins, 30 / 10 / 3 / 1 % |
|---|---|---|
| I | 1.13 / 1.06 / 1.14 / 1.23 | |
| IA | 1.18 / 1.13 / 1.21 / 1.28 | |
| IB | 1.25 / 1.24 / 1.29 / 1.38 | 0.89 / 0.84 / 0.86 / 0.91 |
| II | 1.13 / 1.08 / 1.08 / 1.11 | 0.91 / 0.87 / 0.88 / 0.90 |
| III | 1.06 / 1.01 / 0.97 / 0.97 | 1.01 / 1.01 / 0.99 / 1.00 |
| 1C | 1.18 / 1.13 / 1.11 / 1.12 | 0.92 / 0.87 / 0.85 / 0.86 |
| 3C | 1.15 / 1.03 / 1.00 / 0.99 | 1.04 / 0.96 / 0.94 / 0.94 |

The median is 1.13 with Solonenko & Mobley's a and b and 0.91 with
Williamson & Hollins's. Varying r over the eight stations and the sun
over 0, the base and 60 degrees moves a depth by up to a factor of 2.4
(III's 1 percent level with Solonenko & Mobley's IOPs, whose b(490), 1.20
per m, is the largest of these), and Jerlov's depth lies within that
reach in 38 of the 48 cells. The ten outside are, with Solonenko &
Mobley's IOPs, the 1 percent levels of IA and IB, deeper than Jerlov's
even at the largest r and the sun at 60 degrees (1.04 and 1.001); and,
with Williamson & Hollins's, all four levels of IB and of II, shallower
even at the smallest r and the sun at the zenith (0.90 to 0.97). For the
1 percent level, PAR's depth (400-700 nm) from Jerlov's (1976) Kd and D65,
as in section 2 of that example, is 1.62, 1.43, 1.35, 1.04, 1.04, 1.00 and
0.93 of Jerlov's for I, IA, IB, II, III, 1C and 3C (section 22 of this
file makes that comparison over his own band). For I and IA, Lee et al.'s
model from Solonenko & Mobley's a and b comes nearer his measurement than
that; for IB, it is Williamson & Hollins's a and b that do.

Lee et al.'s depth is of energy, Jerlov's of quanta, over the same 350-700
nm; Lee et al. (2007, p. 4) found depths in energy over 350-700 nm and in
PAR "less than 10%" apart. With Solonenko & Mobley's I and IA, and the sun
at 0 degrees, the model is used outside its fit: K_VIS below 0.04 per m at
the deeper levels, and a sun outside the 10 to 60 degrees it was fitted to.
Both warn.

**Jerlov's (1968) Table XXI.** The shortwave (300-2500 nm) left at depth,
for all ten types (`jerlov1968_solar_fraction`), with the sun at the zenith
for the oceanic types and at 45 degrees for the coastal, as the table's
footnote has it. Lee et al.'s T(z), F_VIS = 0.424, over the table
(`examples/solar_heating.py`, section 6):

| Depth | Solonenko & Mobley, ten types | Williamson & Hollins, six types | Paulson & Simpson, five oceanic |
|---|---|---|---|
| 1 m | 0.91 to 1.08, median 0.95 | 0.91 to 1.04, median 0.92 | 0.98 to 1.46 |
| 2 m | 0.91 to 1.16, median 0.99 | 0.90 to 1.12, median 0.93 | 0.97 to 1.18 |
| 5 m | 0.71 to 1.39, median 1.04 | 0.87 to 1.31, median 0.96 | 0.81 to 1.12 |
| 10 m | 0.34 to 1.75, median 1.07 | 0.79 to 1.63, median 0.97 | 0.80 to 1.22 |

Of the five oceanic types, with Solonenko & Mobley's a and b, Lee et al.'s
model misses the table by less than Paulson & Simpson's fit in 3, 3, 4 and
4 at 1, 2, 5 and 10 m, and in 1, 1 and 0 of five and 1 of four at 25, 50,
75 and 100 m. Paulson & Simpson fitted their numbers to this table (leaving
out its 10 m value, section 14); Lee et al.'s were fitted to HydroLight,
with an attenuation that changes with depth. The extremes at 5 and 10 m
are 9C (low) and 5C (high). F_VIS of 0.40 or 0.45 instead of 0.424 lowers
T by 4.3 to 5.7 percent or raises it by 4.7 to 6.1 percent, at every depth
of every type. The eight r move it by 3 percent or less at every depth for
Solonenko & Mobley's I and IA, and for the turbid types by more than F_VIS
does from 2 m down.

The 300-350 nm of Table XXI is not in Lee et al.'s 350-2500 nm; they put
it at about 1 percent of the shortwave (p. 7). It is not corrected for.

**What this does not settle.** Solonenko & Mobley retrieved their a and b
so that their model's Kd came within 15 percent of Jerlov's (1968)
(sections 2 and 19), so agreement with his 1968
shortwave table is not independent of him. The r of a Jerlov type is not
known, and of the factors tried here it moves the results most.

## 43. The sea surface's reflectance factor rho: Mobley's two tables (note)

Above the water, a radiometer pointed at the sea sees the water-leaving
radiance and the sky reflected by the surface, Lt = Lw + rho Lsky, and
Rrs = (Lt - rho Lsky) / Ed (Mobley 1999, Appl. Opt. 38, 7442, Eqs. 1, 2
and 4). Since 1.17.0 `mobley_rho` gives rho from Mobley's tables and
`rrs_from_above_water` the arithmetic (DECISIONS.md section 99).

**Where the tables come from.** Neither paper prints its table. The Ocean
Optics Web Book (Mobley's, "Surface Reflectance Factors", page updated
2021-02-11, under a Creative Commons Attribution licence) offers both;
`tools/build_mobley_rho.py` reads them from `sources/mobley_rho/`, checks
their MD5 and that every point of the grid is there once, and writes the
values as printed:

| File | Surfaces and sky | Grid |
|---|---|---|
| `rhoTable_AO1999.txt`, MD5 aefcb0da753be57f5e84cdd6951ba76a | Cox-Munk, unpolarised ray tracing, Harrison & Coombes's clear sky | wind 0-14 m/s every 2; sun 0-80 every 10 |
| `rhoTable_AO2015.txt`, MD5 b24599f57b205435eaf95c161d624cf9 | from wave spectra by FFT, polarised ray tracing, a single-scattering Rayleigh sky, the sun's rays along the wind | wind 0, 2, 4, 5, 6, 8, 10, 12, 14, 15 m/s; sun 0-80 every 10, and 87.5 |

Both are for 550 nm, and for 118 viewing directions: the nadir, and nadir
angles of 10 to 80 every 10 and 87.5 at azimuths of 0 to 180 from the sun
every 15, each the mean over a 10 by 15 degree quad (Mobley 1999, p.
7447). The 1999 file gives the direction of the reflected photons (Theta
from the zenith, which is the radiometer's angle from the nadir) and the
viewing azimuth from the sun (Phi-view); the shipped files use the
radiometer's angles for both.

**The 2015 table calls itself preliminary.** Its header: "NOTE: This is a
preliminary table for use during review of the above paper ... The final
table will be placed online once the above paper has been accepted for
publication." The Web Book offers it as "the revised rho table of the
2015 paper", and no other was found. It is shipped as distributed, and
`mobley_rho` gives a ProvenanceWarning for it.

**Against the papers.** The 2015 table gives 0.0179 to 0.0411 at 5 m/s,
nadir 40, the sun at 30 and 60 and the azimuth at 90 and 135, as the
paper's text says (p. 4846), and 0.0449 at 10 m/s, sun 40, (40, 135),
where Fig. 19 says 0.045. At 10 m/s the same four give 0.0199 to 0.0457,
where the text says 0.0195 to 0.0458: a small difference, perhaps of the
preliminary table. The 1999 table gives 0.0336 at 10 m/s, sun 30, (40,
135), where the paper's Table 1 prints 0.0337 for its clear sky; and its
winds are 0 to 14 every 2, where the paper's runs were at 0, 2, 5, 10 and
15 m/s. At (40, 135) and the sun at 30 it gives 0.0256, 0.0264 and 0.0276
at 0, 2 and 4 m/s, the 0.028 the paper's abstract calls acceptable below 5
m/s.

**The two disagree.** At the recommended (40, 135), sun 30 and 5 m/s, the
1999 table gives 0.0283 (between 4 and 6 m/s) and the 2015 table 0.0411;
Mobley (2015) found the 1999 values "not adequate for accurate estimation
of water-leaving radiance". In `examples/ocean_colour_and_secchi.py` part
9, Jerlov IB's Rrs is made into Lt with one table's rho and recovered with
the other's, Lsky / Ed being that of a uniform sky carrying Gregg &
Carder's diffuse irradiance (a stand-in). At (40, 135), recovering with
the 1999 rho what the 2015 rho made gives Rrs 16, 71 and 619 percent high
at 443, 555 and 670 nm, and QAA_v6's a(443) 37 percent high; the other way
round, Rrs(670) falls below zero, which QAA refuses. With 0.028 instead of
the 1999 table's own value the errors are 0, 2 and 15 percent. At (30, 90)
the two tables are closer (0.0287 and 0.0306) and the errors smaller.

**What it does not settle.** Both tables are for clear skies at 550 nm.
Clouds raise rho more than fivefold in Mobley's (1999) Table 1 (0.0337
to 0.1835 for a cloud bank on the horizon at 700-800 nm),
and Sun glint and the sky's colour make it depend on wavelength (Mobley
1999, section 4; Lee et al. 2010, Opt. Express 18, 26313). Which table is
nearer a real sky is not known here; the 2015 one is for a Rayleigh sky,
"at best an approximation to an extremely clear sky" (the Web Book).

## 44. Scatter correction of reflective-tube absorption meters (note)

An ac-9 or ac-s reads too much absorption, because its reflective tube
misses the light scattered beyond its angle, and too little attenuation,
because its c-meter catches the light within its acceptance angle.
Zaneveld, Kitchen & Moore (1994), Proc. SPIE 2258, 44-55: am = a + ea b,
cm = c - ec b (their Eq. 1). Since 1.18.0, `rottgers2013_scatter_correction`
gives the four corrections Röttgers, McKee & Woźniak (2013), Methods in
Oceanography 7, 21-39, compared, and `rottgers2013_a715` their estimate of
the true absorption at 715 nm (DECISIONS.md section 100).

**The methods, as printed.** Flat, a = am - am715 (Röttgers et al. Eq. 1);
proportional, a = am - am715 [(1/ec) cm - am] / [(1/ec) cm715 - am715]
(Eq. 2b; with ec = 1 it is Eq. 2a, which is Zaneveld et al.'s Eq. 21 with
their reference wavelength); flat+ and proportional+, the same with am715
- a715 for am715 (Eqs. 3 and 4), a715 the true absorption at 715 nm. Eq.
(4) puts a715 in the denominator where Eq. (2b) puts am715, so with a715
= 0 the two differ by the factor (cm715 - am715) / cm715 in the
correction; and its numerator has "ac", "either am or a", where am is
used here. Zaneveld et al. derived the proportional method with the
reference wavelength 712 nm (p. 50) and use 715 nm later; the function
takes the reference values, whatever the wavelength.

**Eq. (5)**, a715 = 0.212 am715^1.135, was fitted to 85 coastal samples,
cultures left out, against a PSICAM (r2 = 0.930); their Fig. 4 spans am715
of about 0.02 to 8 per m, and outside that the function warns.

**Zaneveld et al.'s errors from Petzold's data.** Their Table II gives,
for a tube 0.25 m long reflecting all it can up to 41 degrees and a = 0.4
per m, ea of 8.4, 5.7 and 9.2 percent from Petzold's scattering for
waters they call "Gyre deep", "Coastal mixed" and "Harbor", without
naming the stations, and say that "values from the first degree were not
included in b". From the package's eight stations, with their Eqs. (5)
and (6) for a perfect reflector and b from 0.1 degree (Petzold's measured
angles), `examples/from_one_measurement.py` part 7 gets 5.7 percent for
HAOCE 11, 5.9 for HAOCE 5, 8.1 to 8.9 for the three NUC stations and 9.8
to 12.5 for the AUTEC stations. HAOCE 11 matches their coastal value; the
others are not identified, and leaving out the first degree of b, as
their words may mean, raises every one (HAOCE 11 to 7.8). The share of b
within the ac-9's 0.93 degrees, ec, is 16 to 27 percent for these
stations, against the 1.12 to 16.90 percent of Zaneveld et al.'s six Mie
models at 0.9 degrees (their Table I).

**What the methods do with that.** For Jerlov III's water part
(Williamson & Hollins's a and b) and each station's ea and ec, the median
over the stations of the error in a at 440, 555 and 676 nm: with no
absorption at 715 nm, flat is off by 3.7, 7.5 and 1.3 percent and
proportional by nothing, since ea is the same at every wavelength in this
model; with a715 = 0.01 per m (Röttgers et al.'s Baltic and German Bight
samples had 0.01 to 0.23), flat by -5.3, -29.6 and -28.4 percent and
proportional by -10.7, -40.4 and -30.2. Given the true a715, flat+ is back
to flat's own error; proportional+ is off by 2.6, 9.9 and 7.4 percent even
with a715 = 0, the difference in its denominator above. Eq. (5) applied
to water this clear lies outside its fit. How Williamson & Hollins's
campaigns corrected their absorption is not recorded in this package.

## 45. Morel's (1988) Kd from the pigment concentration, and what 2001 kept of it (note)

Morel, A. (1988), "Optical modeling of the upper ocean in relation to its
biogenous matter content (case I waters)", *J. Geophys. Res.* 93(C9),
10749-10768, doi:10.1029/JC093iC09p10749, supplied by the user.
`morel1988_kd.csv` is Table 2 (p. 10,754), all 61 rows, 400-700 nm every 5
nm, read from the page image and checked against the text layer, which
agrees in every row; `tools/build_morel1988.py` carries them as literals
and checks Kw(450) = 0.0168 against Fig. 7a's ordinate, "K450 - 0.0168".
Since 1.19.0, `morel1988_kd` gives K = Kw + chi C^e (Eqs. 8 and 9)
(DECISIONS.md section 101).

- **C is not the same quantity as 2001's [Chl].** Morel's C is "the Chl a
  + Pheo a concentration" averaged over the layer; Morel & Maritorena
  (2001) use chlorophyll a and divinyl chlorophyll a by HPLC (section 27).
  The function's argument is named `pigment_mg_m3` for that reason.
- **The range.** The paper runs the model from 0.03 to 30 mg m^-3 (Figs.
  10, 12 and 13); outside that the function warns. Beyond 650 nm "the chi
  and e values ... are only extracted from the mesotrophic and eutrophic
  waters" (p. 10,755); those rows carry a note and the function warns.
- **What Morel & Maritorena (2001) kept.** Their chi and e are this
  table's, digit for digit, at every wavelength from 560 to 700 nm (29
  rows), checked by the build script against the shipped
  `morel2001_kd.csv`; at 555 nm and below they differ. Their Kw differs at
  every wavelength from 400 to 700 nm. Section 27, after their p. 7168,
  had put the unrevised range "beyond 590-600 nm"; it begins at 560 nm,
  and it is why chi and e are printed with fewer digits from there.
- **What the revision changes.** `examples/ocean_colour_and_secchi.py`
  part 10, with the same number for C and [Chl] (itself an assumption):
  2001's Kd over 1988's at 412, 443, 490, 555 and 670 nm is 0.69, 0.78,
  0.84, 0.89 and 1.02 at 0.03 mg m^-3, and 0.93, 0.95, 0.94, 0.91 and 1.02
  at 0.3. At 412 nm and 0.03 mg m^-3 the change in Kw is 1.23 times the
  whole change: the revised Kw alone lowers Kd by more than it falls, and
  the revised chi C^e raises it a little. The nearest Jerlov type (1976)
  differs only at 0.03 mg m^-3: IA from 1988, I from 2001.

## 46. The clearest natural waters: Morel et al. (2007) (note)

Morel, A., Gentili, B., Claustre, H., Babin, M., Bricaud, A., Ras, J. and
Tièche, F. (2007), "Optical properties of the 'clearest' natural waters",
*Limnol. Oceanogr.* 52(1), 217-229, doi:10.4319/lo.2007.52.1.0217,
supplied by the user. Measurements of the BIOSOPE cruise, South Pacific
gyre, November 2004. `tools/build_morel2007.py` carries both tables as
literals, read from the page images and checked against the text layer;
since 1.20.0 they are `morel2007_stations()` and
`pure_water_absorption_table(..., source="morel2007")` and
`"morel2007_aw2"` (DECISIONS.md section 102).

- **Table 2, pure water.** aw1, 300-500 nm: Buiteveld et al. (1994) from
  Boivin et al. (1986) below 366 nm, joined smoothly to Pope & Fry (1997)
  at 420 nm; aw2, 300-370 nm, from Quickenden & Irvin (1980), joined to
  aw1 at 366 nm (they are equal at 370). The authors give them as "a
  tentative upper bound" for pure water from in situ data. bsw is
  Buiteveld et al.'s scattering times 1.30 for salt; bbsw is half of it.
- **Not Pope & Fry's at every wavelength.** The caption says "the values
  beyond 420 nm are those of Pope and Fry (1997)". At 420, 430, ..., 500 nm
  they are, to the digit of the shipped `pope1997_aw.csv`; at 425, 435, 445
  and 455 nm they are the mean of Pope & Fry's values 5 nm either side,
  not Pope & Fry's own (at 435 nm 0.00565 against 0.00530). The build
  checks both.
- **Table 1, a likely misprint.** a_tot and a_p are shared by the two
  yellow substance estimates, so ay2 - ay1 at 310 nm must be aw1(310) -
  aw2(310) = 0.0183. It is 0.0182 at six stations and 0.0082 at GYR-5 and
  STB-14: one of the two values there is likely misprinted by 0.0100.
  They are kept as printed, the rows are `suspect`, and
  `morel2007_stations()` warns.
- **Against the models and Jerlov.** `examples/ocean_colour_and_secchi.py`
  part 11. The stations' Kd(420) is 0.0120 to 0.0230 per m; Jerlov's
  (1976) type I at 420 nm is 0.0232 on the package's 1 nm grid, so they
  are 0.52 to 0.99 of it; Austin & Petzold's (1986) type I, pure sea
  water's Kw, is 0.0191, and seven of the eight stations are below it.
  Their own pure sea water, aw1 + bsw / 2 at 420 nm, is 0.0073. Against
  Morel & Maritorena's (2001) Kd at each station's chlorophyll at 5 m, the
  measured Kd is 0.71 to 0.97 of it; the paper's Fig. 5 likewise shows the
  lowest-chlorophyll stations below that relation. Morel's (1988) edition
  gives more still, at chlorophyll below the range it was run over.
- The Fig. 5 caption quotes Morel & Maritorena's Kbio(420) = 0.1227
  [Chl]^0.659, their Table 2's chi and e at 420 nm (0.12269, 0.65917)
  rounded.
- The Kd and reflectance spectra are in figures only, and were not read.

## 47. f and Q for a nadir view: Morel et al. (2002), Appendix B (note)

Morel, A., Antoine, D. and Gentili, B. (2002), "Bidirectional reflectance
of oceanic waters: accounting for Raman emission and varying particle
scattering phase function", *Appl. Opt.* 41(30), 6289-6306,
doi:10.1364/AO.41.006289, supplied by the user. Since 1.21.0,
`morel2002_nadir_fq` gives f (R = Eu/Ed = f bb/a, their Eq. 11), Qn
(Eu/Lu for the radiance from the nadir, Eq. 10), their ratio and the
correction of Eq. (B3) (DECISIONS.md section 103).

- **Only the nadir view.** The full tables, f and f/Q for 7
  wavelengths, 6 sun angles, 6 Chl and 17 by 13 viewing directions, are
  distributed by anonymous ftp from oceane.obs-vlfr.fr (Appendix A),
  which did not answer from here (2026-11-16). The paper itself prints
  only Appendix B's linear fits for the nadir view: Tables 1-3, 252
  numbers, read from the text layer and checked against the page images;
  `tools/build_morel2002.py` carries them as literals.
- **The fits' ranges, as the paper gives them.** Eq. (B1), f: the sun at
  0-60 degrees, off by "less than 0.5% when theta_s < 45 deg" and up to
  2 percent at 60. Eq. (B2), Qn: 0-60 degrees, "below 1%". Eq. (B4), f/Qn:
  "even as great as theta_s = 75 deg", errors that "might reach +-3.4%".
  The function gives f and Q only to 60 degrees and the ratio to 75, and
  warns from 60.
- **Table 3 is a fit of its own.** Its f0/Q0 is within 1.37 percent of
  Table 1's f0 over Table 2's Q0 everywhere.
- **The text's ranges are rounded.** f0/Q0 "0.08 - 0.12": the table goes
  down to 0.078632 (660 nm, 10 mg m^-3). In the blue "between 0.086 and
  0.097": 0.086690 to 0.097576. Q0 "from approximately 3.1 to 4.4": 3.11668
  to 4.42719.
- **Against a measurement.** The paper's Eq. (17), Qn = 5.20 - 1.82 cos
  theta_s, is Aas & Højerslev's from Mediterranean waters at 465-474 nm;
  the paper compares it with its own values at 490 nm and Chl 0.1 mg m^-3
  and finds them in agreement over 0-45 degrees. Table 2 is within 2.6
  percent of it there (`examples/ocean_colour_and_secchi.py` part 12).
- **What the correction does.** The factor (f0/Q0) / (f/Qn) of Eq. (B3),
  from Eq. (B4): at 0.1 mg m^-3 within 0.22 percent of 1 at every sun
  angle at 412.5 and 560 nm (0.52 percent at the worst of the seven
  wavelengths); at 10 mg m^-3 and the sun at 75 degrees 0.903 at 412.5 nm and
  0.825 at 560 nm; at 0.03 mg m^-3 above 1, to 1.034 at 560 nm.

## 48. Morel et al.'s (2002) full f/Q tables: read from the user's copy, not shipped (note)

Section 47 shipped the nadir view only, from the paper's Appendix B. The
full tables are on the authors' anonymous ftp server, which did not answer
from where the package is built; the user fetched them from their own
machine on 2026-11-16:

| File at ftp://oceane.obs-vlfr.fr/pub/gentili/AppliedOptics2002/ | Bytes | MD5 |
|---|---|---|
| `DISTRIB_fQ_with_Raman.tar.gz` (18 June 2003) | 173,005 | 21c7afc6c6d3c1963311d6880456f7bc |
| `lin-approx.tar` (19 August 2002), also inside the first, byte for byte | 10,240 | f003e7f20a5d464ebbda2dcf21690c68 |

**Not shipped.** No file in the archive states a licence; README_FIRST
gives only a contact address. Since 1.22.0, `morel2002_fq_tables(path)`
reads the user's own copy, checks its MD5 and refuses another
(DECISIONS.md section 104). Put it at
`sources/morel2002/DISTRIB_fQ_with_Raman.tar.gz` to run the tests that
need it; they are skipped without it, in CI too.

**What is in it.** f.dat: f for 7 wavelengths, 6 sun angles (0-75) and 6
Chl (252 values). D_foQ_pa/: f/Q, one file per case, 17 nadir angles in
water (1.078 to 48.83 degrees) by 13 azimuths (0-180), four decimals; the
paper says the first nadir angle's values are "to be used for theta' =
0". The README's convention for the azimuth: 0 with the sensor and the sun
on opposite sides of the vertical, 180 on the same side. rgoth_Ebuchi.dat:
the surface factor R-gothic for nadir angles in water 0-90 every degree.
Only the tables with Raman emission are distributed, though the paper
describes two sets.

**Checked against the paper.**

- lin-approx.tar's six tables equal the paper's printed Appendix B, the
  shipped `morel2002_nadir_fq.csv`, in all 252 values.
- f.dat at the sun at the zenith is within 0.62 percent of Table 1's f0,
  and the first nadir row of f/Q there within 1.19 percent of Table 3's
  f0/Q0: the fits against the values they were fitted to.
- The paper gives R-gothic "for wind speeds W = 0, 4, 10, and 16 m s^-1";
  the file has 0, 4, 6, 8 and 16 m/s and a flat surface ("xx"), and no 10.
- **With the sun away from the zenith (1.22.1, DECISIONS.md section
  105).** The paper says Eq. (B1) departs from the f it was fitted to by
  "less than 0.5% when theta_s < 45 deg" and up to 2 percent at 60.
  Against f.dat, over the 42 cases of each sun angle, it departs by up to
  0.47 percent at 15 degrees, 1.10 at 30 (13 cases above 0.5), 2.70 at 45
  (26 above 0.5, 2 above 2; 660 nm, 0.03 mg m^-3) and 1.29 at 60. Eq.
  (B4) against the first nadir row of the f/Q tables, over the 42 cases
  by 13 azimuths: up to 1.20 percent at 0 degrees, 0.74 at 15, 0.43 at
  30, 3.34 at 45, 1.61 at 60 and 1.66 at 75, within the paper's "+-3.4%"
  but again largest at 45.
- **Where that comes from: f.dat itself at 45 degrees.** Against the
  straight line in 1 - cos theta_s between its own values at 30 and 60
  degrees, f.dat at 45 lies 3.44 percent below at 660 nm, 3.00 at 620 and
  2.25 at 560 (0.03 mg m^-3), below by more than 1 percent in 7 of the 42
  cases, and up to 1.22 percent above (412.5 nm, 10 mg m^-3). The linear
  fits have no such dip. Why the archive (June 2003) and the paper's fits
  (lin-approx.tar, August 2002) differ there was not known; since 1.26.5
  (below), the paper's own Fig. 13 shows the archive's values: the fits
  differ from what was computed.
- **Located: one run, suspect (1.26.3, DECISIONS.md section 116,
  OPEN_QUESTIONS.md question 6).** The dip belongs to the sun at 45
  degrees and 0.03 mg m^-3 alone. There f lies below the chord between 30
  and 60 degrees at all seven wavelengths, by 1.01 to 3.44 percent,
  growing with the wavelength, while every other Chl lies 0.51 to 1.22
  percent above it. f/Q there follows f (the median over the 221
  directions, -3.52 to -1.35 percent from its chord, the other Chl -0.16
  to +0.85); Q at the nadir has no dip. Divided by the same at 0.1 mg
  m^-3, f(theta_s)/f(0) at 0.03 falls out of order at 45 degrees at all 7
  wavelengths, and no other pair of Chl at any sun angle does. These
  values are kept as the archive has them and are **suspect**:
  `Morel2002FQTables.f` and `.f_over_q` give a ProvenanceWarning at that
  sun angle and Chl. What made them so is not known.
- **The authors' later tables do not have the dip (1.26.4, DECISIONS.md
  section 117).** NASA's OCSSW distributes `morel_fq.nc` (the archive's
  tables, equal to them) and `morel_fq_hyperspectral_2026.nc`, "f and Q
  tables derived hyperspectrally by Bernard Gentili", 70 wavelengths,
  the same sun angles and Chl. At the archive's wavelengths its nadir
  f/Q at 45 degrees and 0.03 mg m^-3 lies -0.19 to -0.13 percent from
  the chord between 30 and 60, as at 0.1 (-0.29 to -0.17); against the
  archive, along the sun angle, it departs at that one run only (+1.23
  to +3.47 percent against the chord of the ratio, every other Chl -1.44
  to +0.01). Not shipped; put the user's copies in `sources/ocssw/` for
  the tests and the example (`--ocssw DIR`), which need h5py.
- **The paper's own Fig. 13 has the dip (1.26.5, DECISIONS.md section
  118).** Fig. 13 (p. 6301) plots f(0)/f against Chl for the sun at 0,
  15, 30, 45 and 75 degrees. `tools/read_fig13.py` reads its filled
  symbols at 0.03 and 0.1 mg m^-3 from the user's copy of the paper (not
  shipped; MD5 1daf887204a1cb949ec62b15544f082e) into
  `examples/data/fq_at_45_degrees/fig13.csv`, numbers read from the
  figure. They hold all 60 of the archive's values there (six
  wavelengths, 442.5 nm being a cross, by five sun angles), a symbol on
  its own within 0.0006 of its value; where Eq. (B1) puts f(0)/f at 45
  degrees and 0.03 mg m^-3, at 560, 620 and 660 nm, no symbol stands
  within 0.0110 to 0.0164. The dip was in the values the paper plotted
  (October 2002), not brought in when the archive was packed (June 2003).
- **EUMETSAT's OLCI table does not have the dip (1.26.9, DECISIONS.md
  section 122).** The OLCI processor's auxiliary file `OL_2_OCP_AX`
  (Sentinel-3A, version MPC_O_AL_003, from the EOPF project's public
  bucket; MD5 2d080e4c1834281212e0583ad0f02e56) holds `f_over_q_LUT` at
  11 OLCI wavelengths, the archive's sun angles and Chl, three wind speeds
  and one aerosol optical thickness. Its nadir f/Q at 45 degrees and 0.03
  mg m^-3 lies -0.31 to -0.20 percent from the chord between 30 and 60
  over every wavelength and wind speed; against the archive, at the six
  wavelengths both have, it departs along the sun angle at that one run
  only (+1.09 to +2.96 percent against the chord of the ratio, every
  other Chl -0.64 to +0.29). Not shipped; put the user's copy in
  `sources/eumetsat_ocp/` for the tests and the example (`--olci PATH`),
  which need h5py.

## 49. The light kept within an angle: Petzold's forward scattering (note)

Since 1.23.0, `forward_scatter(scattering, half_angle_deg)` gives the share
f of one of Petzold's stations' scattering within a half-angle theta0, and
c - f b, the attenuation of the light that stays within theta0 of its
direction; `attenuation_within(water, wavelengths, forward=...)` applies
that f to a water's own b (DECISIONS.md section 107).

- **From the report's own integral.** Petzold prints the cumulative
  integral of the vsf at every tabulated angle. At those angles f is the
  printed value; between them it follows the vsf as a power law, scaled to
  meet the printed values at both ends. Integrating the printed vsf
  directly reproduces the printed integral within 0.33 percent at every
  angle and station. At 180 degrees f is 1 and c - f b is a.
- **What it says.** Within 1 degree lies 20.0 (AUTEC 8) to 37.5 percent
  (HAOCE 5) of b; within 5 degrees 45.8 to 64.1 percent; within 20
  degrees 75.3 to 87.1 percent. Every share includes the report's
  extension below 0.1 degree, 3.4 to 14.5 percent of b, and at AUTEC 7-9
  and HAOCE 5 and 11 its extrapolated angles to 0.159 degree.
- **Against a Monte Carlo** (`tools/forward_scatter_mc.py`, results in
  `examples/data/forward_scatter/monte_carlo.csv`): a collimated beam in
  AUTEC 8, HAOCE 11 and NUC 2200, the light crossing a plane at distance
  r within 0.5, 1, 5 or 20 degrees of the beam's direction, against
  single scattering, exp(-(c - b F) r). Where b r <= 0.5 they agree within
  0.36 percent (the criterion set beforehand was 3). At b r = 3 the Monte
  Carlo is 8.5 percent below at 20 degrees (AUTEC 8) and up to 3.1 percent
  above at the smaller angles: repeated small-angle scattering spreads
  light out of a wide cone and keeps a little more in a narrow one.
- **The extension below 0.1 degree is a choice.** The Monte Carlo's
  sampler continues the vsf below 0.1 degree with the slope of the first
  two printed angles; its share within theta0 differs from the report's
  by up to 1.1 percentage points (HAOCE 11 at 0.5 degree).
- **Not shown here:** that the light within theta0 forms an image blurred
  by theta0. That is the reading DECISIONS.md section 107 gives it, not a
  measurement, and the phase function of a Jerlov type is not known.

## 50. The reflectance of shallow water: Lee et al. (1998, 1999), and a Monte Carlo (note)

Since 1.26.0, `lee1999_shallow_rrs(a, bb, depth_m=, bottom_albedo=,
sun_zenith_deg=)` gives rrs just below the surface over a Lambertian
bottom, straight down, its water-column and bottom parts, the same water
with no bottom, and Rrs above the surface (DECISIONS.md section 113). No
table is shipped; the constants are in `jerlov/ocean_colour.py`.

- **Two sets of constants.** Lee et al. (1998), Appl. Opt. 37, 6329-6338,
  fitted g0 0.070, g1 0.155, g2 0.752, A0 1.03, A1 0.31, D0 1.2, D1 2.0,
  D0' 1.1, D1' 4.9 (Eqs. 16 and 19-21, pp. 6333-6334), and zeta 0.518,
  Gamma 1.562 for Rrs (Eq. 25, p. 6336). Lee et al. (1999), Appl. Opt. 38,
  3831-3843, Appendix A (p. 3842), replaced them "with more
  Hydrolight-simulated data, and correcting a calculation error in the
  earlier study": g0 0.084, g1 0.170, g2 = 1, A0 = 1, A1 = 1/pi, D0 1.03,
  D1 2.4, D0' 1.04, D1' 5.4, zeta 0.5, Gamma 1.5. The error is not
  described. Only the 1999 set is used. Read from page images of the
  copies in the University of Maine's course readings.
- **What the runs covered.** HydroLight 3.0, Petzold's average particle
  phase function, the sun at 0, 30 and 60 degrees, bottom albedos 0, 0.1,
  0.3 and 1 flat in wavelength, H 0.5 to 32 m and infinite, bb/a up to
  1.5, wind 5 m/s (1998, Table 1 and abstract). The 1999 paper does not
  give the ranges of its further runs; the warnings use the 1998 ones.
- **Against a Monte Carlo** (`tools/shallow_rrs_mc.py`, results in
  `examples/data/shallow_rrs_mc/monte_carlo.csv`): a flat surface that
  reflects light from below by Fresnel's law, a Lambertian bottom, the
  sun's beam only, NUC 2240's phase function for the particles and pure
  water's own for pure water; rrs straight up by a collision estimator.
  270 runs: a 0.05, 0.2 and 1.0 1/m, bp/a 0.3, 3 and 30 (u 0.006 to
  0.358), H 1, 4 and 16 m and no bottom, albedo 0, 0.3 and 1, the sun at
  0, 30 and 60 degrees. The standard error from ten batches is 1.4
  percent in the median run and 9.8 percent at the worst. Model over
  Monte Carlo: median 0.999, within 10 percent in 87.4 percent of the
  runs and within 5 percent in 67.4. The criterion set beforehand, 90
  percent within 10, was missed. Within 10 percent were 80 of the 81
  runs with a bottom of albedo 0.3, 75 of 81 with albedo 1, 58 of 81 with
  a black bottom and 23 of the 27 with no bottom.
- **Where it misses, and how.** The 34 runs outside 10 percent fall into
  three groups, each far outside the Monte Carlo's noise. 16 have bp/a =
  0.3, where pure water carries most of the backscattering: the model is
  low, 0.818 to 0.893 of the Monte Carlo. Lee et al. (2011) give water
  and particles separate coefficients because their reflectances per unit
  backscattering differ; whether that is the cause here is not tested.
  13 have a black bottom at 1 or 4 m and bp/a of 3 or 30: the model is
  high, 1.103 to 1.723. The 1998 paper did not fit black-bottom runs on
  their own, and wrote that fixing A0 = 1 and A1 = 1/pi, as the 1999
  update does, would need a negative D1 to fit all its runs, or a more
  complicated form (pp. 6334-6335); whether that is the cause is not
  tested.
  5 have a white bottom at 1 or 4 m and bp/a = 30: 0.879 to 1.113.
- **The 1998 constants against the same runs:** median 0.953, within 10
  percent in 70.7 percent. The update brings the model closer to this
  Monte Carlo.
- **Not the paper's runs.** The Monte Carlo has no sky, no waves and a
  different particle phase function (NUC 2240's bb/b 0.018 against the
  average particle's 0.019), and it counts scattering by less than 1
  degree as none, which bounds the estimator's variance (`petzold_phase`
  in the tool says why). Changing that cut to 0.5 or 2 degrees moved four
  trial runs by amounts comparable to their noise; those trials are not
  recorded.
- **The two groups, looked into (1.26.1, DECISIONS.md section 114,
  OPEN_QUESTIONS.md question 5).** The waters of the 1998 runs, rebuilt
  from Table 1 and Eqs. (12)-(15) (`tools/lee1998_runs.py`, Table 2's a0
  and a1 read from the page image), give pure water at most 0.46 of bb;
  the first group's runs have 0.48 and 0.79. With u held, model over
  Monte Carlo falls as pure water's share rises, in 12 of 12 cases. The
  black-bottom group lies among the rebuilt waters; no single change to
  the Monte Carlo (another of Petzold's phase functions, a sky) brought
  10 of its 13 runs within 10 percent, and the particles' phase function
  alone moves the ratio in a cell by a factor of up to 1.92. The runs are
  `examples/data/shallow_rrs_mc/water_share.csv`, `black_bottom.csv` and
  `lee1998_runs.csv`.
- **A separated form, and the order of the black-bottom miss (1.26.2,
  DECISIONS.md section 115).** Lee et al.'s (2011) published deep-water
  coefficients, water and particles apart, nothing fitted, move by 1.054
  to 1.079 times against the Monte Carlo across pure water's share where
  the 1999 model moves by 1.232 to 1.333 (`water_share_nadir.csv`, the
  sun at the zenith). Over a black bottom the miss rises with the
  particles' bb/b in 5 of 24 cells and falls in none. A cut of 0.5, 1 or
  2 degrees moves the ratio at any one station by a factor of 1.027 at
  most (`cut_check.csv`).

## 51. The refractive index of sea water: Quan & Fry (1995) (note)

Since 1.27.0, `quan1995_refractive_index(wavelength_nm, salinity_psu=,
temperature_c=)` gives Quan & Fry's (1995) Eq. (3), Appl. Opt. 34(18),
3477-3480, doi:10.1364/AO.34.003477 (DECISIONS.md section 124). No table
is shipped; the ten coefficients are in `jerlov/refraction.py`, read
from the page image, since the PDF's text layer garbles the minus signs.

- **The data behind it.** The equation is a fit to Austin & Halikas's
  (1976, SIO Ref. 76-1) selected data, reprinted as the paper's Table 1:
  11 wavelengths from 404.7 to 700 nm, salinity 0 and 34.998 per mil, 1 to
  30 C, 154 values. They were measured by Mehu & Johannin-Gilles (stated
  accuracy 3e-5), except those at 700 nm, which Austin & Halikas
  extrapolated. The function warns above 643.8 nm, the last measured
  wavelength.
- **The fit, recomputed.** Against Table 1 as transcribed (in
  `tests/test_quan1995.py`, checked against the page image) the rms
  deviation is 1.56e-5 over all 154 values and 1.47e-5 without the 700 nm
  extrapolations; the paper prints 1.5e-5. Every value is within 5e-5.
- **What it leaves out.** Pressure: the paper estimates that at 100 m it
  raises the index by less than 1.37e-4 (p. 3477). The paper's salinity
  is in per mil of Copenhagen standard water; the difference from
  practical salinity is not modelled.
- **Over its range** (400-700 nm, 0-35, 0-30 C) the index runs from
  1.3291 (fresh water, 30 C, 700 nm) to 1.3515 (35, 0 C, 400 nm); sea
  water at 35, 20 C and 550 nm has 1.3408. The two indices the package
  already uses, 1.333 for Gordon (1989) and 1.34 for Lee et al. (1998),
  are their papers' values and stay as they are.

## 52. The Fournier-Forand phase function: Mobley et al. (2002) (note)

Since 1.30.0, `fournier_forand(refractive_index=, junge_slope=)` and
`mobley2002_fournier_forand(backscatter_ratio)` give the Fournier-Forand
phase function as Mobley, Sundman & Boss (2002), "Phase function effects on
oceanic light fields", Appl. Opt. 41(6), 1035-1050,
doi:10.1364/AO.41.001035, print it: Eqs. (1)-(3), p. 1037, and the line of
Eqs. (7)-(8), p. 1042 (DECISIONS.md section 127). No table is shipped.

- **Where the equations were read.** From the page images of Mobley et
  al.'s paper (a copy on the University of Maine's course site, not
  shipped). They call it the "latest form", from Fournier & Jonasz (1999,
  Proc. SPIE 3761, 62-70); neither that paper nor Fournier & Forand (1994,
  Proc. SPIE 2258, 194-201) was obtained. Mobley's Ocean Optics Web Book
  page on the function (updated 2021-10-13) prints the same three
  equations.
- **Checked against themselves.** Eq. (1) integrates to one over the
  sphere and Eq. (3) is its integral over 90-180 degrees, both to 1e-6.
  The closed form of the cumulative share used by
  `FournierForand.cumulative` is not printed in either source; it was
  derived from Eq. (1) and is checked by differentiation.
- **Mobley et al.'s fit to Petzold's average,** n = 1.10 and mu = 3.5835
  (p. 1037), gives a backscatter ratio of 0.018313, the printed 0.0183.
  That point lies just off their own line, Eq. (7) (which gives n =
  1.099976 at that mu); solved on the line, 0.0183 gives mu = 3.5834.
- **The line is one choice.** Eqs. (7) and (8) are the same line, as the
  paper says. Of the five (n, mu) pairs in the Web Book's Table 1, which
  give its five ratios (0.0001 to 0.4) to their printed digits, four lie
  within 0.005 of the line in n; the one for 0.4 (n = 1.15, mu = 4.874)
  does not (the line gives 1.299 there).
- **Its range.** For mu = 5 the form is symmetric, with a backscatter
  ratio of 0.5 at any n; at mu = 3 it is 0/0. On the line, ratios from
  0.0001 to 0.5 (HydroLight's library, HydroLight 5.1 Technical
  Documentation, p. 22) take n from 1.021 to 1.318.

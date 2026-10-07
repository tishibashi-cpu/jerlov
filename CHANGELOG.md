# Changelog

Every release is archived on Zenodo under the concept DOI
[10.5281/zenodo.22321312](https://doi.org/10.5281/zenodo.22321312), which
always resolves to the latest version.

## 0.7.3 — 2026-10-07

**Fixed.** `ShortwaveParameters.fraction_at`, and so `solar_fraction`,
evaluated Paulson & Simpson's two exponentials at any depth without a word.
They were fitted to Jerlov's Table XXI in the upper 100 m, or 50 m for
`I_upper50`, as the paper's text says. Below that the result is
extrapolation, and it now raises a `ProvenanceWarning`. The values are
unchanged.

**Docs.** DECISIONS.md section 5, "No extrapolation", claimed more than the
package did. It now separates three cases:

- the package's own refusal to extrapolate;
- values that a source extrapolated, which are shipped, marked and warn;
- the axes that are not tables: the depth of a fitted formula, now warned
  about, and the wavelength of Morel's pure water formula, which is not
  range-checked.

The README's "will not extrapolate" says the same.

## 0.7.2 — 2026-10-07

Fixes from a review of the whole package. No shipped value changed.

**Fixed.**

- A NaN wavelength passed the range checks of `Water.a`, `b`, `c`, `kd`
  and `kd_hydrolight`, `kd_spectrum` and `b_from_c`, since `NaN < lo` is
  False. It came back as NaN, and `Water` warned about the last sample of
  the table, 800 nm or 715 nm, instead. It is now refused.
- `descend` froze the caller's wavelength array along with its own copy,
  so the caller could no longer write to it. It now copies first.
- `Scene` kept the caller's wavelength and downwelling arrays rather than
  copies. Changing them afterwards left the wavelengths out of step with
  c, which is evaluated once. It now copies them.
- The pure water scattering functions, and so `bb_from_vsf`, accepted a
  wavelength of zero or less and returned inf or NaN with only a NumPy
  RuntimeWarning. They now refuse it, as they already refused a bad
  salinity.

**Docs.** The README said the scattering coefficients of the two IOP sources
differ at 510 nm "by up to a factor of 2.6". The largest factor is 3.8, at
Jerlov III, as `examples/sources_disagree.py` already said. A test claimed to
check the README's figure but never read the README; one now does.

## 0.7.1 — 2026-10-07

Examples for what 0.6.0 and 0.7.0 added. No code or shipped value changed.

**Examples.** Three new scripts, and one extended; `examples/README.md` says
which to read.

- `light_at_depth.py`: `descend` through the typical depth profile. At 490
  nm and 60 m, Jerlov I receives a third less light than its surface Kd
  implies and 3C 530 times more; the 1 percent light level of I rises from
  197 to 133 m. It also shows where the profile runs out.
- `measured_scattering.py`: Petzold's eight stations, their B/S of 0.013 to
  0.044 and the shape of their phase functions, and what a measured ratio
  changes in a scene against a guessed one.
- `what_is_in_the_water.py`: a minus the pure water absorption the source
  built a on, the share of absorption that is the water, and the measured
  points behind it.
- `from_one_measurement.py` now marks a doubtful channel and attaches
  replicate uncertainties with `from_measurements(flags=, uncertainty=)`.

**Docs.** Writing the absorption example turned up something in the
Williamson & Hollins data, now in DATA.md section 20. The measured average a
at 715 nm is exactly 1.004 for 1C, 3C and 5C, with zero spread over 23, 28
and 6 campaigns. Identical values with no spread are not what independent
measurements give, and neither paper says why. The measured points lie 14
to 16 percent above the fitted a, which at 715 nm is pure water alone. Both
are shipped as published.

## 0.7.0 — 2026-10-07

**Added.** `petzold_scattering(station)`: the volume scattering functions
Petzold (1972) measured in eight ocean waters, from the Tongue of the Ocean,
Bahamas, to San Diego Harbor, at the report's 55 angles from 0.1 to 180
degrees and 530 nm, each with its c, b, a and backscatter ratio B/S. They are
shipped as `petzold1972_vsf.csv` and `petzold1972_stations.csv`, and
`PETZOLD_STATIONS` lists them clearest first.

- `vsf_at(angle)` interpolates in log-log within the table, and
  `phase_function()` is the vsf over b.
- `backscatter_ratio` is a measured bb/b, 0.013 to 0.044 across the eight,
  for `Water.bb` in place of a guess. It belongs to that water, not to a
  Jerlov type, and no station is mapped to one.
- Below 0.169 degree at the Bahamas and Catalina stations nothing was
  measured, and the report extended sigma with a power law. Those 15 values
  are `extrapolated` and warn.

Every value was read from the report's page images and compared with its
OCR text. `tools/build_petzold1972.py` carries them as literals and checks
them against the report's integrals, its second printing of sigma, its
summary pages and the smoothness of the curves. DATA.md section 21 and
DECISIONS.md section 27.

**Docs.** `tools/README.md` said two scripts need no input; seven do.

## 0.6.0 — 2026-10-07

**Added.**

- `pure_water_absorption(wavelength_nm, source="williamson2022")`: the
  absorption of pure water that the source built its a on, so that the part
  of a due to what is in the water is a minus this, from one source. Only
  Williamson & Hollins (2022) publish theirs, in their spreadsheet, 1 nm
  from 300 to 800 nm, now `williamson2022_aw.csv`. With it and their Table 6,
  their Eqs. (4)-(6) give back the shipped a to a median of 0.10-0.28
  percent, and `tools/build_williamson2022_aw.py` stops if that fails. From
  720 nm every type's a is this aw. Other sources raise
  `MissingQuantityError`, saying why: Solonenko & Mobley show theirs only as
  a figure, and the rest give Kd only. DATA.md section 20.
- `descend(surface_type, depth_m, wavelengths, source="jerlov1976")`:
  downwelling irradiance carried down through the typical profile of
  Williamson & Hollins (2023), each 10 m layer with the Kd of its own type.
  It returns the transmittance and the layers crossed, and stops with
  `MissingQuantityError` at a layer the paper declared no type for, rather
  than carrying the last type on. DECISIONS.md section 26.
- `Water.from_measurements(..., flags=..., uncertainty=...)`: a caller's own
  statuses, from the package's vocabulary, warn as published ones do; an
  unknown status is refused, so a misspelt one cannot silently never warn.
  Uncertainty is read back with `Water.uncertainty(quantity, wl)`.

**Fixed.**

- `Water.c` warned once for a and once for b, twice for a wavelength
  flagged in both. It now warns once, naming both.
- The pure water scattering functions accepted a negative or NaN salinity
  and returned a number. They now refuse it.
- `repr` of an `Observation` with no light anywhere raised a NumPy
  `RuntimeWarning`; it now says the veiling fraction is undefined.

**Not done.** Petzold's volume scattering functions are still planned. They
are to come from his report, SIO Ref. 72-78 (1972), which has not yet been
obtained.

## 0.5.2 — 2026-10-07

The two Dstl datasets behind five of the shipped tables were obtained and the
tables rebuilt from them: all five came out identical to the shipped files.
Doing so showed that one of them claims more than its source printed.

**Changed.** `jerlov1976_kd.csv` is at 1 nm from 300 to 715 nm, but Jerlov
(1976) Table XXVII has 16 wavelengths, 310 to 700 nm. The rest was filled in
by the Dstl dataset it comes through: 3672 values by linear interpolation
between printed wavelengths, and 230, at 300-309 and 701-715 nm, by linear
extrapolation from the two end values. All 4060 were marked `ok`, which
DATA.md defines as the published value. They are now `ok` (158, checked
against the table), `interpolated` and `extrapolated_by_dataset`, two new
statuses. The extrapolated ones raise a `ProvenanceWarning`, since the
package does not extrapolate; the interpolated ones do not. No value changed.

`tools/build_jerlov1976_and_solonenko2015.py` now carries Table XXVII as
printed and stops if the dataset departs from it, or stops being linear
between and beyond it.

**Docs.** The depth-profile dataset, figshare 21710252, is CC BY 4.0; its
download note said Open Government Licence, which is the 2022 dataset's. The
same script reported "19 layers from 0 to 200 m"; they are 10 to 200 m, below
the surface layer.

## 0.5.1 — 2026-10-07

Every paper this package draws on was read again against what it ships. No
shipped coefficient was wrong. Statements about the papers were, in several
places, and so was one of the checks.

**Checked against the papers.** All of: Jerlov (1968) Tables XX and XXI and
Jerlov (1976) Table XXVII; Austin & Petzold (1986) Tables IV and VI;
Solonenko & Mobley (2015) Tables 3 to 8, where the only cells that differ are
the duplicated rows already recorded; Williamson & Hollins (2022) Tables 3, 6
and 7, all 612 cells of the last; Williamson & Hollins (2023) Table 2;
Paulson & Simpson (1977) Table 2; Boss & Pegau (2001) Table 1 and Eqs. (4)
and (5); Smart (2007) Table 1; Haltrin (1999) Eqs. (4) to (7); and the
figures quoted from Austin & Petzold (1990), Hollins & Williamson (2023),
Oishi (1990), Maffione & Dana (1997), Woźniak & Pelevin (1991), Paglierani et
al. (2023), Jia et al. (2021) and Abd El-Mottaleb et al. (2024). DATA.md
records what was checked in each section.

**Fixed.** The check that Williamson & Hollins (2022) b follows from their
Eqs. (8)-(11) used the Table 6 of Hollins & Williamson (2023), a later refit
to the measured points, under the name of the 2022 table. With the 2022
table the agreement is 0.73 percent, not 5.3, and the build script and test
now require 1 percent. DATA.md had put the 5.3 down to a revision of Bl; the
cause was the wrong table. Only the check was affected.

The `williamson2022` source carried Haltrin's constants (0.005826, 1.151302,
0.341074) rather than the ones the paper prints and computed with (0.00583,
1.1513, 0.3411). The largest difference is 0.07 percent, in the pure water
term, and moves no result that matters; what it broke was the rule that a
source carries its own constants.

**Docs.** Statements the papers do not support, corrected:

- Boss & Pegau "made no measurement beyond 170 degrees": their instrument
  measured to 177.3; Table 1 stops at 170. In the error message, the CSV
  note, DATA.md, DECISIONS.md and an example.
- "Both papers recommend 110 to 160 degrees": that is Maffione & Dana. Boss
  & Pegau recommend near 117 degrees, or water removal from near 90 to 160.
- Paulson & Simpson excluded the 10 m point "because the two-exponential
  form does not capture the transition": the paper gives no reason.
- The spread of chi_p away from 170 degrees is 2.6 to 6.4 percent, not
  "3 to 6"; the test that pinned it checked only the upper end.
- DATA.md section 17 quoted Paglierani et al. about coefficients varying
  between works as if it concerned Jerlov types; it concerns Mobley's four.
- DATA.md section 13 said Williamson & Hollins (2023) do not say which three
  cells depart from their rule; they mark them with asterisks.

Added to the record: Jerlov (1968) Table XXI is for a solar altitude of 90
degrees (oceanic) and 45 (coastal), now in `jerlov1968_solar_fraction` and
DATA.md; the 8 percent accuracy of Austin & Petzold's model excludes 410 nm;
Hollins & Williamson (2023) Table 1 omits two a values that the 2022 paper's
own filter keeps, and this package follows the 2022 paper.

## 0.5.0 — 2026-10-06

Three tables that had been transcribed, checked against their papers and
shipped, but were reachable only through a private loader, now have public
entry points. No coefficient changed, and nothing existing behaves
differently.

**Added.** `water(t, source="jerlov1968")`: Kd from the first edition of the
classification, Jerlov (1968) Table XX, for all ten types from 310 to 700 nm.
It is also the Kd0 column of Solonenko & Mobley (2015), which reproduces it to
transcription accuracy. Its caveats say how far it is from the 1976 edition:
1 to 15 percent on average by type, up to 35 percent at single wavelengths.

`measured_points(t, quantity)`: the measured a and b points behind the
Williamson & Hollins (2022) spectra, with their standard deviation and the
number of campaigns behind each. Hollins & Williamson (2023) recommend these
over the fitted spectra for validation. The paper's own filter, five or more
campaigns, is applied unless `include_sparse=True`; Jerlov IA and 7C have no
point that passes it, and are refused rather than returned empty.

`jerlov1968_solar_fraction(t)`: Jerlov (1968) Table XXI, the broadband
irradiance with depth that Paulson & Simpson fitted, for all ten types. Blanks
stay NaN.

`pure_water_scattering(wavelength_nm)`: the total scattering coefficient of
pure sea water, from the same Morel formula as the rest of `backscattering`.
It is twice `pure_water_backscattering` by symmetry, and Morel's
`b_w = 16.06 beta_w(90)`, both checked. It is the `bw` that `b_from_c` asks
for, if that is what the c measurement was corrected with.

**Changed.** `examples/solar_heating.py` uses `jerlov1968_solar_fraction`
instead of the private loader; its output is unchanged. Tests now fail if a
shipped table is never read by the package, or if an example reaches into
`jerlov._data`.

`Water.kd_hydrolight(wl)`, for source `solonenko2015`: the paper's third Kd
column, K_d^H, which HydroLight computed from the retrieved a and b with the
Petzold average-particle phase function. It is the paper's check on its own
retrieval and a different quantity from `.kd()`, the Kd of its bio-optical
model. Its definition, from Section 4 and Appendix A of the paper, is now in
DATA.md section 19, with one finding: the paper says 90 percent of the points
in its Fig. 5 are within 20 percent of Jerlov's Kd, and the tabulated values
give 87 percent.

**Docs.** DATA.md has a nineteenth entry, so the count in DATA.md, the README
and `.zenodo.json` moves from eighteen to nineteen. The Solonenko & Mobley
caveat said only a is lost in the duplicated rows of Table 7; Kd and KdH are
lost there too.

The DOI of Paglierani et al. (2023) was given as `10.1155/2023.7185329`, which
resolves to nothing; it is `10.1155/2023/7185329`. It was wrong in DATA.md,
`sources/README.md` and `.zenodo.json`, so every Zenodo record from 0.2.2 on
carries the broken link in its related works; 0.5.0 will carry the right one.

## 0.4.1 — 2026-10-06

Inputs that used to slip past the package's own checks are now refused, and
two physically impossible results now say so. No coefficient changed, and
every valid call returns what it returned before.

**Fixed.** NaN passed every guard written as `value < 0`, since any comparison
with NaN is False. `Scene.observe` and `Scene.transmittance` with a NaN
distance, `Scene.at_depth` with a NaN depth, `attenuation_coefficients` with a
NaN in its range and `solar_fraction` with a NaN depth all returned results
made of NaN. They now raise. NaN inside a spectrum is still accepted, because
it marks a gap in the data, which the package keeps visible on purpose.

`Water` accepted NaN among its wavelengths, which passed the ascending check
for the same reason and broke interpolation afterwards. It also accepted
`flags` shorter than its wavelengths, which surfaced as `IndexError` only when
a value was asked for. Both are now refused when the `Water` is made.

`Scene.observe` and `attenuation_coefficients` accepted a negative veiling
radiance, and `veiling_radiance_estimate` a negative downwelling irradiance,
returning negative radiance. `Scene` itself already refused a negative
irradiance; all three now do.

`Scene.at_depth` given a surface spectrum of the wrong length failed inside
numpy with "operands could not be broadcast together"; it now names the
argument.

`b_from_c` with c below the pure water value cw returned a negative b without
comment. It now raises a `ProvenanceWarning`, as `kd_spectrum` already did in
the same situation.

**Changed.** `bb_from_vsf` warns of a reading below that of pure sea water
with a `ProvenanceWarning` rather than an `AngleWarning`. The angle is not
the problem, and a caller filtering out angle advice was silencing it too.

**Docs.** DECISIONS.md section 24 still listed the Akkaynak-Treibitz
coefficients as planned, though they arrived in 0.1.3, and section 12 still
listed `Scene` as planned and shortwave heating as out of scope, which
section 19 reversed. Both are annotated rather than rewritten, so the record
of each decision stays. The Solonenko & Mobley caveat said the Kd0 column is
not shipped; it is in the CSV, and what was meant is that `water()` does not
return it.

## 0.4.0 — 2026-10-06

Three calls that used to return an answer now raise instead, because the
answer was not one: hence 0.4 rather than 0.3.4. No coefficient changed.

**Changed.** `shortwave_parameters` refuses the three rows of Paulson &
Simpson's Table 2 that are not Jerlov types (the authors' composite
observations, their Run 1, and Kraus's Crater Lake value) unless called with
`include_non_types=True`. They used to come back like any type, so
`solar_fraction("run_1", 10.0)` gave a Jerlov-looking answer for one cruise.

**Fixed.** `water_type_at_depth` returned `None` for a NaN depth, which reads
as the paper declining to say; NaN and infinity now raise. 200 m, the bottom
of the paper's deepest layer, returned `None` as if beyond the profile; it now
belongs to the 190-200 m layer, since there is no layer below to own it.

`integrate_response`, and through it `spectrum_to_xyz` and `spectrum_to_srgb`,
integrated a spectrum given in descending wavelength order to a negative XYZ.
Both grids must now ascend.

**Docs.** `Observation.contrast` said the inherent contrast is reduced by the
transmittance. That holds only against a background as bright as the water's
own veiling light. Without veiling light the contrast is not reduced at all,
and against a darker background it falls faster than the transmittance. The
docstring now gives the formula and the three cases, and a test checks each.
The computation itself was right.

`integrate_response` now says how its accuracy depends on sampling. Moving
the integral onto the union of the two wavelength grids was tried and not
adopted: on five test spectra sampled at 25 nm it was better for a flat
spectrum and worse for the other four.

**Tools.** Three rebuild scripts printed their checks against the paper and
wrote the table whatever the checks said. `build_austin1986.py`,
`build_williamson2022_iop.py` and `build_williamson2022_measured.py` now stop
without writing when a check fails, as the others already did.

## 0.3.3 — 2026-10-05

**Fixed.** A `ProvenanceWarning` was raised for a wavelength that lands
exactly on a sound sample whenever the sample beside it was flagged:
`water("9C", source="jerlov1976").kd(350)` warned that 349 nm is missing,
though the answer at 350 nm rests on 350 nm alone. The NaN check has known
this since 0.2.1; the warning did not. Both now ask one function which
samples an answer rests on, so they cannot disagree again. The test suite,
which printed six such warnings, now prints none.

`kd_spectrum` given an array of Kd failed with numpy's "truth value of an
array is ambiguous". It now reconstructs one spectrum per measurement,
returning shape `kd.shape + at.shape`. Several measurement wavelengths are
refused with a message saying so.

**Added.** `kd_spectrum` warns when K(490), measured or implied by the
model, is not below 0.16 1/m, the limit Austin & Petzold give for their model.
It also warns when the answer rests on the values of M below 365 nm that the
paper itself flags as extrapolated. Both limits were stated in the docstring
and checked by nothing.

**Docs.** Error messages, docstrings and comments sent readers to "README
section 10" and the like. The README has no numbered sections; DATA.md does,
and every such reference now points there. The message raised by `Water.bb`
without a backscattering ratio, which every new user meets, was one of them.
A test now checks that every "DATA.md section N" cited in the code exists.

## 0.3.2 — 2026-10-01

**Fixed.** `b_from_c` given an array of c at a single wavelength returned
only the first element, silently. The shape of the answer was taken from the
wavelength alone; it now follows c and the wavelength together.

`pure_water_vsf` given one angle and several wavelengths returned the value at
the first wavelength only. Through it, `bb_from_vsf` with an array of
wavelengths subtracted the 450 nm water term from every reading, so its `bb`
and `particulate` were wrong at every wavelength but the first while `water`
looked right. Scalar calls, and every figure in the documentation, were not
affected.

`ProvenanceWarning` pointed at `water.py` rather than at the line that asked
for the value, and `CoverageWarning` and `GamutWarning` did the same when
reached through `spectrum_to_srgb`. A fixed `stacklevel` is right for one call
path only; warnings now point at the first frame outside the package.

The table loaders are cached, and `jerlov.water()` handed out the cached
arrays themselves. An in-place edit such as `w.wavelengths *= 2` changed the
table for every later caller in the process. The cached arrays are now
read-only, and `Water` copies what it is given, including a caller's own
measurements, which it previously shared.

## 0.3.1 — 2026-09-20

**Added.** `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, this changelog, and issue
templates. The contributing guide sets out what it takes to add a coefficient:
the paper itself rather than a table quoted from it, a script in `tools/` that
produces the table, checks inside that script against the paper's own
equations, an entry in `DATA.md`, and a regression test. It also says that a
coefficient disagreeing with a paper the reader has is the most useful report
this package can receive.

`py.typed`, so the annotations already in the package reach a caller's type
checker rather than being invisible to it.

`tests/test_quoted_figures.py` recomputes every figure the documentation
states: the factor of 3.8 between the two published scattering coefficients,
the 5.1 across three routes, the 46 percent by which the shortwave fit misses
its own source, the 34.8 percent spread at 170 degrees, the 116.9 degree
crossing, the 65 percent by which a guessed backscattering ratio overstates
contrast. Two of them read the number out of `README.md` and compare it
against the call printed beside it.

Those figures were each computed once and then written into prose, where
nothing was watching them. A reader cannot tell a stale number from a current
one, and the numbers are the reason to trust the package at all.

No coefficient and no function behaviour changed in this release.

## 0.3.0 — 2026-09-11

**Added.** `bb_from_vsf` converts a backscattering sensor's single-angle
reading into bb, following Boss & Pegau (2001). `Water.bb` still refuses to
guess a backscattering ratio, because the Jerlov classification still does not
determine one; what changed is that a caller with a HydroScat, an ECO-BB or a
VSF meter no longer has to.

The pure sea water half is analytic, so it is computed rather than
transcribed, and checked against the definition of bb: chi_w must give the
same bb_w at every angle and that value must equal the direct integral. Only
chi_p, resting on 41 measured scattering functions, is a table. Angles outside
90 to 170 degrees are refused, and 170 warns: its quoted spread is 34.8
percent against 3 to 6 in the middle.

Three examples, each aimed at a reader the existing two did not reach:
`from_one_measurement.py`, `solar_heating.py`, `what_an_eye_sees.py`. Before
these, half the public API appeared in no example at all.

**Changed.** `CoverageWarning` reports every channel rather than only the
worst. Integrating a 500-600 nm spectrum against the CIE 1931 observer used to
say "covers only 4.1%", which reads as if the whole observer were barely
covered; 4.1 percent is z-bar alone, and x-bar and y-bar are at 45 and 76.

**Fixed.** The NumPy compatibility shim moved from `colour.py` to `_data.py`.
It had been sitting in a module about colour, so two modules written
afterwards reached for `np.trapezoid` directly and broke the oldest supported
NumPy. A test now refuses the raw name anywhere in the repository.

**Data.** `boss2001_chi.csv`. `DATA.md` section 18 records that three
published values circulate for this conversion under two definitions differing
by 9 percent at 140 degrees, one including the water contribution and one not.

## 0.2.2 — 2026-09-10

**Added.** Examples became runnable scripts that CI executes on every push.

**Fixed.** Two examples made claims their own output contradicted: the
disagreement between the two published sources does not run in one direction,
and the depth-profile aside now finds the depth at which the water type
actually changes.

## 0.2.1 — 2026-09-10

**Fixed.** `kd(350)` for Jerlov 7C returned `nan` although 350 nm is
tabulated. The guard that stops interpolation bridging a gap was also firing
on queries that land exactly on a sample, which are not interpolated. Found by
checking the shipped 1976 table against the printed page cell by cell, which
had never been done before; 133 tests had not caught it.

**Data.** `DATA.md` gains two entries. Woźniak & Pelevin (1991) reprint
Jerlov's Kd spectra with the unit given as `[10⁻³ m⁻¹]` where the values are
in `10⁻² m⁻¹`, and with Jerlov IB at 700 nm printed as 59 where the original
has 58; read as published, Jerlov I at 475 nm comes out below the absorption
of pure sea water. Separately, a third route to a and b is in circulation —
assigning a chlorophyll concentration per Jerlov type — and at 532 nm the
three routes give beam attenuations differing by a factor of 5.1 for Jerlov
III. All three are peer reviewed.

## 0.2.0 — 2026-09-10

**Added.** `solar_fraction` and `shortwave_parameters`, the Paulson & Simpson
(1977) two-exponential parameters that ROMS, MITgcm, NEMO and CESM use. They
are usually copied from secondary sources; `tools/` refits them from the table
the paper fitted, Jerlov (1968) Table XXI, and reproduces R for all six rows.
Repeating the fit found that the published parameters miss their own source by
46 percent at 1 m for types II and III.

**Data.** Jerlov (1968) Tables XX and XXI. Obtaining the first edition settles
three questions that had been open in `DATA.md`:

- The Solonenko & Mobley reference column is Jerlov 1968, agreeing to 0.06 to
  0.25 percent. It was not an error; this file had said so on the strength of
  comparing their table against an edition they did not cite.
- The 600 nm anomaly for types I, IA, IB and II is a revision Jerlov made in
  1976 and documented in his own text.
- Coastal type 1 repeating oceanic III at eight wavelengths is in the original
  table, and survives the revision at seven.

**Changed.** Reverses the scope decision in `DECISIONS.md` section 12, which
had ruled shortwave heating out. The line had been drawn on similarity of
subject matter rather than on whether the provenance could be established.

## 0.1.4 — 2026-09-09

**Added.** Two runnable examples, `sources_disagree.py` and
`synthetic_underwater_images.py`, run by CI.

**Changed.** A scalar wavelength returns a float rather than a one-element
array, matching `numpy.interp`. `float(w.a(550))` raised under NumPy 2 before
this; writing the first example was what found it. Passing a sequence still
returns an array.

## 0.1.3 — 2026-09-07

**Added.** `Scene.attenuation_coefficients` returns beta_D, beta_B and B_inf
for the Akkaynak-Treibitz image formation model. `are_distinct` is False:
under single scattering both coefficients are the beam attenuation
coefficient. The limitation travels with the value rather than living in
documentation.

## 0.1.2 — 2026-09-06

**Added.** `water_type_at_depth`, the Jerlov type that typically applies in
each 10 m layer down to 200 m, from Williamson & Hollins (2023). Returns
`None` where fewer than ten measurement campaigns supported a declaration.

**Fixed.** 0.1.1 used `numpy.trapezoid`, a name added in NumPy 2.0, despite
declaring `numpy>=1.22`. It did not run on the versions it claimed to support,
and CI had not noticed because every job installed the newest NumPy. A job
pinned to the oldest declared version was added.

**Data.** `DATA.md` records that the depth-profile paper's Data Availability
Statement gives the DOI of an unrelated dataset — lake locations in the United
States — and identifies the three cells where the paper departed from its own
stated selection rule.

## 0.1.1 — 2026-09-05

**Changed.** Renamed from `uwlight`. The name now matches the term researchers
in this field search for; searching PyPI for `jerlov` was what established the
gap this package fills. Also modernises the licence metadata for setuptools
77 and later.

## 0.1.0 — 2026-09-05

First release. Absorption and scattering coefficients for the Jerlov optical
water types, from four sources, each carrying its own model constants and its
own caveats. Direct and veiling components along a horizontal underwater path.
CIE XYZ, sRGB, and arbitrary camera or photoreceptor responses. Every shipped
table regenerable from its primary source by `tools/`.

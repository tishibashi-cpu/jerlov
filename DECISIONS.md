# Design decisions

Why this package is shaped the way it is, and what was considered and
rejected. `DATA.md` records what is known about the data; this file records
what was decided about the code.

Entries are append-only. If a decision is reversed, add a new entry saying so
rather than editing the old one.

---

## 1. The source is part of the API

`jerlov.water("III")` alone would be a lie. The same Jerlov type has
different coefficients in different papers, and at 510 nm the scattering
coefficients of Solonenko & Mobley and of Williamson & Hollins differ by a
factor of 2.6. A function that returns one number for "Jerlov III" hides a
choice that changes the answer.

So `source` is an argument, `Water` carries the `Source` it came from, and
`Water.caveats()` reports what is doubtful about it.

**Rejected:** picking the best source and hiding the rest. That is what the
literature already does implicitly, and it is why two groups can publish
incompatible tables under the same names without anyone noticing.

## 2. The equations' constants belong to the source, not to the equations

Both papers use the scattering model of Haltrin (1999), but Solonenko &
Mobley print and compute with a small-particle coefficient of 1.513 where
Haltrin gives 1.151302. Reproducing their table needs 1.513; using the model
correctly needs 1.151302.

A single module-level constant would therefore be wrong for one of them.
`ScatteringConstants` is attached to each `Source`.

**Rejected:** correcting Solonenko & Mobley to 1.151302. Their published
tables were computed with 1.513, and silently changing it would mean the
package could no longer reproduce the paper it claims to ship.

## 3. Williamson & Hollins is the default source

It is the only published set in which a and b rest on measurement rather than
on inverting Kd. `Source.measured` records the distinction so a caller can
check rather than take our word for it.

The cost is coverage: it has six water types, not ten. That is the honest
trade. Jerlov I, IA, 7C and 9C are absent because too few measurements exist,
and inventing them would defeat the point.

## 4. `bb` has no default

The backscattering coefficient is not determined by the Jerlov
classification. Deriving it from the two sources' particle concentrations
gives answers differing by up to a factor of 31, and neither is inside the
range reported in the literature (DATA.md section 10).

`Water.bb` therefore raises unless `backscatter_ratio` is passed. The
docstring gives the ranges so the caller can choose, and refuses values
outside (0, 0.5).

**Rejected:** a default of 0.0183, the Petzold average-particle value. It
would be defensible and would be wrong for most water, and nobody would ever
see it. Making the caller state it is the only way the choice stays visible.

**Rejected:** deriving bb ourselves from the World-wide Ocean Optics
Database, which holds 1,200 bb profiles that nobody appears to have used for
this. That is a paper's worth of work and out of scope; it is recorded in
DATA.md section 10 so that someone can do it.

## 5. No extrapolation, and none that is silent

The package itself never extrapolates. Asking for a wavelength outside a
table raises `ValueError`, and so does an angle outside Petzold's or Boss &
Pegau's tables. `kd_spectrum` applies the same rule to the Austin & Petzold
model range, `b_from_c` to Smart's, and `water_type_at_depth` and `descend`
make no statement below 200 m. A silently extrapolated value is
indistinguishable from a measured one at the point of use, and the caller
has no way to find out afterwards.

**Values that a source extrapolated are another matter.** Some shipped tables
contain them, because the source printed them: Williamson & Hollins' model
spectra outside 412-715 nm, the Dstl dataset's extension of Jerlov (1976) to
300-309 and 701-715 nm, Austin & Petzold's M below 365 nm, Petzold's power
law below 0.169 degree. They are inside the table's range, so they are
returned, but each is marked in the `status` column and warns with
`ProvenanceWarning` when used. The rule is that no extrapolated value is
silent, not that none exists.

**Two kinds of axis are not tables.**

- *Depth in a fitted formula.* `ShortwaveParameters.fraction_at` evaluates
  Paulson & Simpson's two exponentials at any depth, but they were fitted to
  the upper 100 m (50 m for `I_upper50`). Until 0.7.3 it extrapolated below
  that without a word; it now warns. `Scene.at_depth` applies one Kd at any
  depth, which is an approximation it states, not an extrapolation of data.
- *Analytic formulas.* `pure_water_vsf`, `pure_water_backscattering` and
  `pure_water_scattering` evaluate Morel's formula at any positive
  wavelength. The formula has no table to fall outside, but it was not
  established at every wavelength either, and its range is not enforced
  here.

## 6. Gaps stay gaps

Where a published value is wrong and could not be recovered, the value is
`nan` and interpolation across it yields `nan`. `numpy.interp` will happily
bridge a gap if the NaN is not in the sampled interval, so `Water._interp`
checks the bracketing samples explicitly.

**Rejected:** filling by interpolation, as Williamson & Hollins did in their
spreadsheet for the absorption values they could not recover. Their choice is
reasonable for their purpose and is carried in the
`williamson2022_value_per_m` column, but a package cannot make it on the
caller's behalf.

## 7. Reconstruction used the source's own constant

The `b` values reconstructed for the duplicated rows of Solonenko & Mobley
Table 7 were computed with their 1.513, not Haltrin's 1.151302, because the
purpose is to fill a hole in *their* table. For Jerlov 5C this agrees with
the Williamson & Hollins substitution to three decimal places, which is
evidence that both parties made the same choice independently.

A test fixes this: `test_solonenko_reconstruction_used_its_own_constant`
asserts the values match 1.513 and do **not** match 1.151302.

## 8. Warnings, not silence and not errors

Interpolating across a value that a paper got wrong produces a number that
looks no different from a sound one. Raising would make the package unusable
for exploratory work; saying nothing would make it dangerous.

`ProvenanceWarning` is emitted when a returned value rests on a wavelength
flagged `suspect`, `missing`, `extrapolated`, `reconstructed` or
`model_extrapolation`. Callers who do not want them can filter them; the
point is that the information exists.

## 9. Named water types are only an entry point

`water("III")` builds a `Water` from arrays and returns it. Everything
downstream works on the arrays. `Water.from_measurements` produces an object
of exactly the same kind.

This is deliberate. Solonenko & Mobley's own code path — a function per water
type — is how `UWOpticalSystemsDesignTools` ended up with three of its eight
profiles wrong: a bug in one branch is invisible from the others. One code
path means a defect shows up everywhere or nowhere.

## 10. NumPy only

`jkibele/OpticalRS` has been broken since 2019 because scikit-learn moved a
module. Nobody noticed for seven years because nothing was watching.

Runtime dependencies are NumPy alone. Interpolation is `numpy.interp`; CSV
reading is the standard library. `openpyxl` is needed only by `tools/`,
`matplotlib` only by the optional `plot` extra. CI runs weekly as well as on
push, so a break is noticed even when nobody has touched the code.

## 11. Tables live in the package; the scripts that made them do not

`jerlov/data/` is the single copy of every CSV. `tools/` holds the scripts
that produce them from the primary sources, and `sources/` holds the inputs
and is not tracked.

Running the scripts must reproduce the shipped CSVs byte for byte. This is not
decoration: a drift was found this way, when a fix applied directly to a CSV
had not been applied to the script that generates it.

## 12. Scope

In:

- Inherent optical properties of the Jerlov water types, with provenance
- Conversions between them, where a published relation exists
- Enough of the light field to answer "what does an object at distance r,
  seen by an observer at depth z, look like" (planned when this was
  written; now `Scene`, see section 13)

Out:

- Solving the radiative transfer equation. That is HydroLight's job.
- Remote sensing reflectance, the view from above the surface. HYDROPT and
  OpticalRS occupy that ground.
- Shortwave heating for ocean circulation models, where the Jerlov type is an
  integer index and no spectrum is involved. (Reversed in section 19.)
- Machine-learning image restoration.
- Deriving new coefficients from primary observations.

## 13. The path model, and what was left out of it

`Scene.observe` implements the single-scattering form for a horizontal path:

```
L(r) = L_target * exp(-c*r) + B_inf * (1 - exp(-c*r))
```

The direct term is exact given c. `Scene.transmittance` exposes `exp(-c*r)`
on its own, because that is the part with no approximation in it.

**B_inf is a required argument.** The usual estimate is
`bb * Ed / (2 pi c)`, but the `2 pi` assumes the backscattered light is spread
uniformly over the backward hemisphere, which real phase functions are not.
Since bb is already undetermined (section 4), a default here would be a guess
resting on a guess. `veiling_radiance_estimate` provides the formula for
callers with nothing better, but they have to reach for it.

**Horizontal paths only.** Observer and target at the same depth, so one
downwelling spectrum suffices. A slanted path needs integration along a
changing depth, and the extra machinery would not buy accuracy the rest of
the model can support. The main uses — a diver looking sideways, an ROV
looking at a structure — are horizontal.

**No forward-scatter blur.** Convolving a point spread function needs the
full phase function. With bb undetermined, the whole phase function certainly
is. The line is drawn at "the radiance of this point", not "the sharpness of
this image".

**Depth is recorded, not used.** With a horizontal path the depth enters only
through the downwelling irradiance. `Scene.at_depth` applies
`Ed(z) = Ed(0) exp(-Kd z)` and requires Kd to be supplied, because the default
IOP source does not carry it.

## 14. Colour needs a stated white, and coverage needs checking

`spectrum_to_srgb` requires `white`. A radiance spectrum has no colour on its
own, and underwater the reference that makes a grey card grey is the
downwelling irradiance at that depth, not daylight. Choosing one silently
would answer a question the caller did not ask.

The adaptation divides XYZ by the white's XYZ and rescales onto the sRGB
white point: a von Kries transform performed in XYZ rather than cone space.
It is cruder than CAT02 for strongly coloured illumination, which underwater
illumination certainly is. The docstring says so and calls the result "what a
white-balanced camera would record" rather than a prediction of appearance.

**Rejected:** normalising by luminance alone. It leaves a cast whenever the
white is not D65, which underwater it never is. This was implemented first
and was wrong; the tests now pin the behaviour for three different whites
including a deliberately blue-green one.

`CoverageWarning` exists because integrating a 450-650 nm spectrum against
colour matching functions that run from 360 to 830 nm gives a plausible
number that is simply wrong. The integral is reported over the overlap and
the caller is told what fraction that was.

The CIE 1931 observer and the D65 illuminant are shipped as data with the
same provenance treatment as everything else (DATA.md section 12). They were
transcribed rather than approximated: an analytic fit to the colour matching
functions would have been smaller, but it would have put numbers in the
package that came from nowhere in particular.

## 15. A declared minimum must be tested, not asserted

`pyproject.toml` says `numpy>=1.22`. Version 0.1.1 shipped using
`numpy.trapezoid`, which was added in NumPy 2.0. The package therefore did not
run on the versions it claimed to support, and the CI did not notice because
every job installed the newest NumPy available.

Two changes followed.

`jerlov/colour.py` resolves the name once at import:

```python
_trapezoid = getattr(np, "trapezoid", None) or np.trapz
```

`np.trapz` is the pre-2.0 name and was removed in 2.0, so neither can be
assumed.

The test matrix now includes a job pinned to the oldest declared NumPy. A
lower bound nobody tests is a guess, and this one was wrong for a whole
release.

**Rejected:** raising the floor to the version that happened to work. That
would fix the symptom by narrowing the claim, and would leave the next
lower-bound claim just as untested.

**It then happened again.** Two modules written later reached for
`np.trapezoid` directly, and the oldest-NumPy job caught them before release.
The shim had been sitting in `colour.py`, where nobody writing about
scattering would look for it. It now lives in `jerlov/_data.py`, which every
module already imports, and `tests/test_packaging.py` refuses any file in the
repository that names either `np.trapezoid` or `np.trapz`.

That is the general shape: a rule kept in one module is a rule the next module
does not know about. Either move it somewhere shared, or make a test enforce
it. Here both were needed, because the shared location alone would not have
stopped a third module from reaching past it.

## 16. Coefficients that cannot be told apart still get names

`Scene.attenuation_coefficients` returns beta_D, beta_B and B_inf for the
Akkaynak-Treibitz image formation model. Under the single-scattering model in
section 13 both betas are the beam attenuation coefficient c, so on its own
this adds nothing that `Water.c` does not already give.

Three options were weighed.

**Return them, plainly equal.** Honest, but a caller sees two names for one
number and may reasonably conclude the package distinguishes them.

**Refuse to provide them.** Also defensible: naming quantities you cannot
separate suggests you can. Rejected because the need is real. Implementations
that fit these coefficients bound them by guesswork for want of any physical
starting point; one such fitting code bounds them with hard-coded sigmoid
ranges. Withholding c helps nobody.

**Return them with the limitation in the type.** Chosen. The result carries
`are_distinct = False` and a `note` saying why, so the limitation travels with
the value instead of living in documentation the caller may not read.

`distance_range_m` is a required argument even though single scattering does
not use it. Akkaynak & Treibitz's point is that these coefficients vary with
range, so a value quoted without its range is not a well-defined quantity.
Accepting the argument and recording it also means the signature does not have
to change if the model is ever refined.

A test rebuilds the Akkaynak-Treibitz expression from the returned
coefficients and requires it to match `Scene.observe` exactly, so the two
routes cannot drift apart.

## 17. Examples are executable, and CI runs them

`examples/` holds scripts rather than notebooks. A notebook stores its
outputs in the file, so the diff is noisy and the stored output can disagree
with what the code now produces. Scripts can simply be run, and CI runs both
on every push: an example that has stopped working is a failed build, not
something a reader finds out.

Writing the first one immediately exposed an API fault. `water("III").a(550)`
returned `array([0.0878])`, so `float(...)` on it raised under NumPy 2. Scalar
input now gives a float, matching `numpy.interp`, with the behaviour pinned by
tests. Nothing else surfaced that; a reader following the README would have
hit it on their first line.

Each example prints the version and file it imported before doing anything.
`python examples/foo.py` puts `examples/` on `sys.path` rather than the
current directory, so an installed copy of the package wins over the working
tree, and the failure that produces looks like a missing method rather than a
stale install. Naming the file makes that impossible to miss twice.

There are five, chosen so that each reaches a different reader rather than
re-showing the same API: why the source is an argument, what to do with an
instrument reading, synthetic imagery, shortwave heating for ocean models, and
arbitrary spectral sensitivities. Before they were written, half the public
API appeared in no example at all, including the whole of the shortwave
module and every route for bringing your own measurements.

**Two obvious examples were left out.** Restoring the colour of a photograph
and predicting a visibility range are the two things a reader most wants, and
both are things the README says this package does not claim to do. An example
that appears to do them would contradict the disclaimer more loudly than the
disclaimer states it. Examples here show what the API does, not how well it
performs.

Each ends with the assumptions it made — the
stated backscatter ratio, the approximate veiling geometry, the horizontal
path, the invented reflectance spectra — rather than opening with them. A
reader who has just watched a red patch turn black at 8 m is more likely to
read that list than one who met it before seeing anything.

## 18. The repository checks its own consistency

`tests/test_packaging.py` asserts things about the repository rather than
about the physics.

The version is written in three files and has drifted twice, both times found
by a person noticing a wrong number in output. That is not a method, so it is
a test now. It also refuses a version that is not a plain `x.y.z`, since a
`.dev` suffix is not something to release.

Two further checks close the gap between the data and its documentation: every
shipped CSV must be named in `DATA.md`, and every shipped CSV must be written
by some script in `tools/`. A table nobody documented is a table with no
provenance, which is the one thing this package exists not to have.

A fourth asserts that the tests import `jerlov` from the working tree. That is
the `sys.path` trap in section 17, and it produced a failure that looked like
a missing method rather than a stale install.

Two more close the gap between the modules and their data, in both
directions: every table a module reads must be present, and every table a
build script writes must have arrived. `boss2001_chi.csv` once failed to reach
a working copy, and the first sign was thirteen FileNotFoundErrors deep inside
the backscattering tests. The check now names the file and says which script
makes it.

Two more again keep `.zenodo.json` honest: the entry count it quotes must
match `DATA.md`, and every shipped module must be mentioned somewhere in the
description. That file is read only when Zenodo archives a release, so nothing
else notices when it goes stale, and it had gone stale four times.

All of these skip when `pyproject.toml` is absent, so running the suite against
an installed wheel does not fail on files that are deliberately not shipped.

## 19. Shortwave penetration is in scope after all, reversing section 12

Section 12 lists as out of scope: "Shortwave heating for ocean circulation
models, where the Jerlov type is an integer index and no spectrum is
involved." **That is reversed.** `jerlov/shortwave.py` provides the Paulson &
Simpson (1977) parameters.

The reasoning was that a broadband two-exponential fit has nothing in common
with the spectral quantities in the rest of the package. That is still true,
and it is not the criterion that matters. The criterion this package actually
applies is whether a number's provenance can be established and checked, and
obtaining Paulson & Simpson showed that it can: they fitted Jerlov (1968)
Table XXI, and `tools/build_paulson1977.py` repeats the fit and reproduces R
for all six rows.

Two things settled it.

It is the most widely used application of the Jerlov classification. ROMS,
MITgcm, NEMO and CESM all carry these six numbers, generally copied from a
secondary source. A checkable copy is worth having.

Repeating the fit found something. The published parameters miss Jerlov's own
table by 46 percent at 1 m for types II and III (DATA.md section 14). That is
exactly the class of fact this package exists to surface, and it was not
visible until the fit was repeated.

The scope line in section 12 was drawn on a similarity of subject matter
rather than on whether the work could be done properly. That was the wrong
test.

## 20. Checking against a printed table is worth the transcription

`tests/test_reproduces_papers.py` now carries Jerlov (1976) Table XXVII as a
literal and compares all 158 cells against the shipped file. That file reaches
us through the Dstl dataset, which is a second-hand route, and until the scan
was obtained there was nothing to check it against.

It came out exact. Two independent reprints of the same table were also
compared: one is exact, and one has its unit off by a factor of ten and one
digit wrong (DATA.md section 16).

The comparison also found a bug here. The guard that stops interpolation
bridging a gap was firing on queries that land exactly on a sample, which are
not interpolated. It had survived 133 tests because none of them asked for a
tabulated wavelength immediately beside a gap. Checking cell by cell against
a printed page is a different kind of test from checking a package against
itself, and it found something the other kind could not.

## 21. Experimental validation is out of scope

The README says this package does not claim to predict what a camera will
record underwater, and that closing that gap needs measurements which do not
appear to exist. **Making them here is ruled out.** The tank, the turbidity
control and the calibrated instruments are not available, and a validation
done badly would be worse than none: it would put a number on the accuracy
that nobody could defend.

So the claim stays where it is. The package implements published coefficients
correctly, the tests demonstrate that, and the limits are stated. Anyone with
the facilities to check it against photographs is welcome to, and `examples/`
gives them the starting point.

**Rejected:** a partial validation, clear water only, with equipment to hand.
It would produce a figure that reads as validation and is not one.

## 22. Measuring bb is in scope; guessing it is still not

`jerlov/backscattering.py` converts a single-angle volume scattering
measurement into bb, following Boss & Pegau (2001).

This does not weaken section 4. `Water.bb` still refuses to supply a
backscattering ratio, because the Jerlov classification still does not
determine one. What changed is that a caller with an instrument no longer has
to guess: the route from a HydroScat or ECO-BB reading to bb is published,
settled, and now checked.

Three things shaped the API.

**The water half is computed, not transcribed.** Morel's formula for the
scattering of pure sea water is exact, so chi_w must give the same bb_w at
every angle and that value must equal the direct integral of the definition of
bb. `tools/build_boss2001.py` asserts both. Only chi_p, which rests on 41
measured scattering functions, is a table.

**The angle range is enforced.** 90 to 170 degrees, the span of Boss &
Pegau's Table 1, and a warning above a 10 percent quoted spread. At 170 the
spread is 34.8 percent against 2.6 to 6.4 at the other angles, and a caller
who picked that angle should be told rather than handed a number. (This said
the range was what the measurements cover, and "3 to 6"; their instrument
measured to 177.3 degrees, and the table is what stops at 170. Corrected in
0.5.1 after reading the paper again.)

**chi and chi_p are kept apart.** They are printed under the same symbol by
different authors, and differ by 9 percent at 140 degrees because one includes
water. The shipped table marks the rows from other authors
`other_definition` rather than dropping them: a reader comparing against those
papers needs to see why the numbers differ, not wonder where they went.

## 23. The prose is tested against the code

`tests/test_quoted_figures.py` recomputes every figure the documentation
states: the factor of 3.8 between the two published scattering coefficients,
the 5.1 across three routes, the 46 percent by which the shortwave fit misses
its own source, the 34.8 percent spread at 170 degrees, the 116.9 degree
crossing, the 65 percent by which a guessed backscattering ratio overstates
contrast. Two of them read the number out of `README.md` and compare it
against the call printed beside it.

Those figures were each computed once and then written into prose, where
nothing was watching them. A reader has no way to tell a stale number from a
current one, and the numbers are the reason to trust the package at all.

The direction of the fix matters when one fails. **Usually the prose is what
needs updating**; the code changed on purpose and the sentence did not follow.
Occasionally it is the other way round and the change to the code was a
mistake, which is the case the test exists for.

**Rejected:** generating the prose from the code, or a doctest-style
mechanism. The figures appear inside sentences that explain what they mean,
and a sentence written around a number is not something to generate. Checking
is enough.

This came from revising something else entirely and finding two claims there
that the code contradicted. The lesson transferred: a number written into
running text is a number nothing checks.

## 24. Planned

Recorded so the shape of the API can be judged against where it is going.

- ~~**Akkaynak-Treibitz coefficients**~~: done in 0.1.3, as
  `Scene.attenuation_coefficients`; see section 16. The distance range is a
  required argument, as planned.
- ~~**Petzold phase functions**~~: done in 0.7.0, as `petzold_scattering`,
  transcribed from Petzold's own report; see section 27.

Validation is deliberately staged. The package can claim that it implements
published coefficients correctly, and the tests demonstrate that. It cannot
claim that it predicts what a camera will record underwater; that needs
measurements that have not been made. The README says so.

## 25. A table worth shipping is worth an entry point

Three tables had been transcribed, checked against their papers and shipped,
and then left where only the private loader could reach them:
`jerlov1968_kd.csv`, `jerlov1968_total_irradiance.csv` and
`williamson2022_measured.csv`. An example read one of them through
`jerlov._data`, which is what a user would have had to do too.

That is the worst of both: the work of establishing the provenance was done,
and the user who needed the numbers either went without or copied them from a
secondary source, which is the situation this package exists to end. All three
now have public entry points, and `tests/test_packaging.py` fails if a shipped
table is never read by the package or if an example reaches into `_data`.

The KdH column of Solonenko & Mobley (2015) was held back at first: its
definition was not recorded in DATA.md, and a quantity whose meaning has not
been established from the paper does not get a public name. Reading the paper
established it (DATA.md section 19), and it is now `Water.kd_hydrolight`.
Reading it also showed that the tabulated values reach 87 percent within 20
percent of Jerlov, not the 90 the paper states, which is now recorded rather
than repeated.

## 26. Deeper than one Kd, and the caller's own doubts

**`descend`.** `Scene.at_depth` uses one Kd from the surface down, and says
so. Williamson & Hollins (2023) give the type that is typical in each 10 m
layer, so a descent can use the right Kd for each layer instead. Two choices
were made in it.

Where the paper declared no type, the descent stops with
`MissingQuantityError`. Carrying the last declared type on would have given
an answer at every depth, which is what a user would want and exactly the
guess the paper declined to make. A coastal descent therefore ends early: 9C
at 10 m, 3C at 70 m.

Every layer's Kd comes from one source, Jerlov (1976) unless the caller says
otherwise. Mixing sources between layers would make the profile a profile of
sources as much as of water; a source that lacks a type the profile passes
through is refused, by the same `KeyError` as `water()`.

**Flags and uncertainty on measurements.** `from_measurements` used to accept
only values, so a user's doubtful point looked as sound as the rest, while a
published one with the same doubt warned. The caller's statuses are the
package's own vocabulary, not free text: a status the package does not know
would have no defined meaning, and a misspelt `"suspect"` would never warn,
so both are refused. Uncertainty is carried and interpolated, but not
propagated into c or anything derived from it; propagation needs the
correlation between a and b, which only the caller knows.

**`Water.c` warns once.** It used to warn for a and for b separately, so a
wavelength flagged in both produced two warnings about one value of c.

## 27. Petzold's stations, one at a time

The report's eight ocean stations are shipped as they are: eight measured
waters, each with its own c, b, a and B/S. Three things that are commonly
done with them were not.

**No average.** The Petzold "average particle" phase function that HydroLight
users know, which Solonenko & Mobley describe as the average of his coastal,
harbor and ocean phase functions, is a later construction. It is not in the
report, and the report is what was checked, so it is not shipped under
Petzold's name.

**No Jerlov mapping.** Petzold gives c at one wavelength and classifies
nothing. Assigning his stations to Jerlov types would mean inventing the
mapping, which is the kind of number this package exists to keep out.
`backscatter_ratio` is offered as a measured alternative to a guessed
bb/b, with the water it came from attached, not as the ratio of a type.

**The report's extension is marked.** In the clearer waters nothing below
0.169 degree was usable, and the 0.1 to 0.158 degree values there follow the
printed power law exactly. They are shipped, since the report prints them and
counts them in s, but as `extrapolated`, and `vsf_at` warns on them.

## 28. An extra is a claim too

Section 10 said `matplotlib` was needed "only by the optional `plot` extra".
Nothing needed it: no module, test or example has ever imported it. The extra
was declared in anticipation of plotting helpers that were never written, and
an extra that installs something unused tells the reader a feature exists.
It was removed in 0.8.0, and `tests/test_packaging.py` now fails if any extra
installs a distribution that nothing in the repository imports.

The classifiers are the same kind of claim and were wrong the other way:
"Pre-Alpha" and no Python version, on a package with a tested lower bound and
a four-version CI matrix. They now list exactly the versions CI runs, and a
test keeps them so, for the reason in section 15.

**Rejected:** keeping `plot` as an empty extra so that existing
`pip install "jerlov[plot]"` commands stay silent. pip already installs the
package and only warns, and a silent no-op extra is the same false claim.

## 29. PAR, a descent into a scene, and the nearest type

Three additions in 0.9.0, each with a choice that could have gone the other
way.

**`Scene.at_depth` takes a `Descent`.** Until now a descent reached a scene
only by multiplying the surface spectrum by hand. `kd=` now accepts the
descent itself, and refuses one computed to another depth or on other
wavelengths: either mismatch gave a scene whose downwelling irradiance
belonged somewhere else, with nothing to show it. The water along the path is
still the caller's, and is not checked against the descent's last layer. A
caller may know the water there better than the typical profile does, and the
check would refuse exactly that case.

**PAR counts photons, and the unit has no default.** `par_profile` requires
`unit="energy"` or `"photons"`. Guessing either is wrong for the other kind
of spectrum, and the error is not a factor that cancels: it reweights the
blue against the red, so it changes the 1 percent depth as well as the
value. It is planar PAR, from Ed, and says so; PAR on scalar irradiance is
larger by a factor that depends on the light field, which nothing here
determines. The 1 percent depth is found from the spectrum, not from
ln(100) / Kd at a chosen wavelength, which is how it is usually quoted.
With D65 at the surface, the spectral answer is shallower than that at 490
nm by 15 to 21 percent in the oceanic types, and the gap closes through the
coastal ones until, in 7C and 9C, it is deeper, by 12 and 45 percent: there
the light that gets furthest is yellow-green, not blue. A first draft of
the example said "shallower in every type", having checked only the types
down to 5C.

Below a descent, PAR has no answer. `depth_of_fraction` raises when the
light has not fallen far enough by the bottom of the descent, rather than
carrying the last layer's Kd on, for the reason in section 26.

**`classify_kd` reverses an example, not a decision.** `from_one_measurement.py`
said "there is no classify() here, deliberately": a single Kd does not pin a
type, and the boundaries differ between the 1968, 1976 and 1978 editions.
Both objections stand, and they are answered by what the function returns
rather than by not having one.

- It ranks every type by distance and returns the whole ranking, so an
  ambiguous measurement looks ambiguous. The distance is the root mean
  square of ln(measured / type), so that a relative difference counts the
  same in clear water as in the red.
- It draws no boundaries. It compares with the spectra of one edition, named
  by `source`, and the result carries it.
- `beyond` says when the measurement lies outside every type, where the
  nearest is only an end of the classification.
- Wavelengths at which any type has no Kd are left out of every distance,
  and recorded, since distances over different wavelengths cannot be
  compared.

**Rejected:** interpolating between types to report "40 percent of the way
from II to III". The types are points chosen by Jerlov, not samples of a
continuum, and a fractional type would be a quantity nobody defined.

**Rejected:** using Aas et al. (2013)'s K(475) boundaries. They are one
author's reading of one edition, and the edition they read, Jerlov (1978),
was not obtained (DATA.md section 2).

## 30. Keywords are claims too

The Zenodo record and `CITATION.cff` listed "underwater visibility" as a
keyword. The README says the package does not predict what a camera will
record underwater, and no function computes a visibility range: the
examples leave that out on purpose (section 17). A keyword is how a search
finds the package, so it is a claim about what the package does, the same
kind of claim as the extra in section 28. It was removed in 0.9.3.

Three were added for what the package now does: "diffuse attenuation
coefficient", "photosynthetically available radiation" and "euphotic zone".
"underwater imaging" stays, since `Scene` and the colour functions are
for exactly that.

## 31. Checking against published measurements is in scope

Section 21 rules out experimental validation: no tank, no instruments, and a
validation done badly would put an indefensible number on the accuracy.
That stands.

Comparing the package with measurements someone else made and published is
a different thing, and it is in scope. It is the same kind of work as
checking a coefficient table against the paper that printed it: the
measurements have a provenance, the comparison can be repeated by anyone,
and it says something definite about one part of the package without
claiming anything about the rest.

Jerlov's quanta tables (DATA.md section 22) were the first chance. They
were transcribed with the same care as any coefficient table, checked
against each other, and the comparison is a test. What it showed is
recorded as it came out, including where the package is a third too deep:
a check that only reports agreement is not a check.

What it does not license: describing the package as validated. It agrees
with Jerlov's measurements of quanta irradiance with depth, for the types
he measured, with D65 standing in for his skies. That is all the
comparison says, and all the README says about it.

## 32. PAR over another band

`par_profile` integrated over 400-700 nm and nothing else. Two things
needed another band, and both worked around it: the check against Jerlov's
quanta meters, which counted 350-700 nm, integrated by hand in the tests,
and `euphotic_zone.py` took the share of each colour by zeroing the
surface spectrum outside it. The second was wrong by a rounding: the light
between the last sample of one colour and the first of the next was
divided between them by a ramp rather than at the boundary, and the
example printed 87 percent violet-blue where the integral over 400-500 nm
gives 88. In 0.10.0 `band=(lo, hi)` does
both, with the ends interpolated as 400 and 700 nm always were.

**The band has a default, though the unit has none.** Section 29 refuses to
guess the unit because either guess is wrong for the other kind of
spectrum, silently. 400-700 nm is not a guess: it is what PAR means, and
the function is named for it. A caller who wants another band says so.

**The attribute is still `par`.** Over 350-700 nm the result is not PAR,
and a second name for the same number would make every caller choose
between two. `ParProfile.band_nm` records the band, and the repr names it
whenever it is not 400-700 nm, so a flux over another band does not pass
for PAR when printed.

**Nothing outside the band is required.** As for PAR since 0.9.1, only the
samples inside the band and the one either side of each end are read, so a
gap or a flagged Kd outside it neither refuses nor warns.

**Rejected:** a separate function for the quanta band. It would be the
same integral with another pair of numbers, and a shortcut for one
instrument's band would invite one for each.

## 33. The light on the target's face is the caller's

`Scene.observe` gave the radiance leaving a target as
`reflectance * Ed / pi`: the face the observer sees was taken to receive
the whole downwelling irradiance. That is true of a face turned straight
up. The observer looks horizontally, so the face is usually vertical, and
receives only part of Ed, how much depending on the light field and on how
the target is turned. `lure_colours.py` (0.9.5) found that this share and
the backscatter ratio together move where a finish's contrast starts by up
to a factor of 124 among the finishes that keep their sign, and change the
sign for three of the six. It worked
around the assumption by scaling Ed before building the scene.

**It is now an argument, `face_irradiance_ratio`**: the irradiance on the
face divided by Ed. A ratio rather than an irradiance, so that Ed stays
what `Scene.at_depth`, `descend` and `veiling_radiance_estimate` mean by it,
and the veiling light is not dimmed along with the target, which is the
mistake scaling Ed invites. It may be an array on the scene's wavelengths,
since the shares of direct and diffuse light change with wavelength. It has
no upper bound: a face turned towards the sun receives more than a
horizontal one.

**It will have no default, as `bb` has none (section 4)**, but not yet.
Every release up to 0.10.0 took it as 1 without saying so, and code
written against them should not stop without notice. Leaving it out still
takes it as 1, with a `FutureWarning` naming the argument; a later release
will make it required. The examples now pass it, 1.0 where they had relied
on the old behaviour, and say so among their assumptions.

**Rejected:** an angle instead of a ratio. Turning the orientation of a
face into the light it receives needs the radiance distribution, which
nothing here determines, for the same reason the veiling light needs a
phase function (section 13).

**Rejected:** a default other than 1, such as the 0.25 `lure_colours.py`
uses. It would be no less a guess, and would change every existing result
without a warning.

## 34. The face irradiance ratio is required

Section 33 added `face_irradiance_ratio` in 0.11.0 and, so that existing
code would not stop without notice, took it as 1 with a `FutureWarning`
when it was left out. From 0.12.0 it has no default, and leaving it out
raises `MissingQuantityError`.

What decided it is what the default does when it is wrong. In the setting
of `lure_colours.py`, Jerlov 1C at 3 m, a target 0.5 m away, the
single-scattering veiling light and bb/b = 0.02, a red, a blue and a black
finish come out brighter than the water behind them with a ratio of 1 and
darker with 0.05. A default of 1 therefore gives the wrong sign of the
contrast for a face that receives little light, with nothing to show it.
That is the kind of answer `bb` (section 4) and the veiling radiance
(section 13) have no default to avoid.

The cost was weighed: one more keyword, in a method that already requires
`veiling_radiance`, a quantity harder to choose. A caller who does not know
the ratio can still pass 1.0, and then the assumption is in their own code,
where they and their readers can see it. The error says so, and names 1.0
as what earlier releases assumed.

**Rejected:** keeping 1 as a documented default without a warning. It would
leave every result that rests on it unmarked, which is what section 33 set
out to end. **Rejected:** keeping the `FutureWarning` indefinitely. It
announces a change; never making the change would make it false, and code
that silences warnings never sees it.

## 35. The spectrum at depth, and Kd between two depths

`ParProfile` gave PAR at depths and the depth of a fraction. Two examples
needed more and computed it themselves: `seagrass_depth_limit.py` took the
effective Kd(PAR) over the top metre as `-ln(fraction)`, and `isolumes.py`
multiplied the surface spectrum by `Descent.transmittance_at` to find where
the light peaks. In 0.13.0 the profile answers both.

**`kd_par(z1, z2)` is `ln(PAR(z1) / PAR(z2)) / (z2 - z1)`**, the quantity
two PAR readings at two depths give. It takes the two depths
rather than one, because PAR has no single coefficient: near the surface,
while the red is still being removed, it is larger than further down, and
a Kd(PAR) quoted without its depths is not one number. The name keeps
"par" over another band too, for the reason in section 32.

**`spectrum_at(z)` is in photons, on `wavelengths_nm`**, the grid
`par` is integrated over: the samples inside the band and its two
interpolated ends. Photons whatever the surface spectrum was given in,
since that is what `par` counts, and on that grid rather than the caller's
wavelengths, so that integrating it gives `par` exactly. Below a descent
both refuse, as `depth_of_fraction` does (section 29).

**Rejected:** a Kd(PAR) at one depth, the derivative. Between two close
depths `kd_par` gives it to any accuracy wanted, and a second method would
be a second name for the same thing.

## 36. A weight for each photon

PAR counts every photon from 400 to 700 nm alike. Nothing that uses light
does: a pigment absorbs some wavelengths more than others (PUR, the
photosynthetically usable radiation, weights PAR by the absorption of the
algae), an eye by its pigment's sensitivity, a sensor by its own response.
`integrate_response` integrated one spectrum against such a
curve, but the depth profile, the depth of a fraction and Kd between two
depths were PAR's alone. In 0.14.0 `par_profile` takes `photon_weight=`,
and every one of them follows the weighted flux. PAR is the weight 1.

**It weights photons, and says so in its name.** PUR and a visual
pigment's catch are both counts of absorbed photons, so the photon spectrum
is the one to weight. A response per unit energy, as a thermopile's, is a
different curve: as a photon weight it must first be divided by the
wavelength. Section 29 refused to guess the unit of the spectrum because the
two choices reweight the blue against the red; naming the weight's basis in
the argument is the same refusal, without a second argument to pass.

**`spectrum_at` stays unweighted.** It is the light in the water, which
does not depend on who is counting it.

**Rejected:** a separate function, such as `irradiance_profile(weight=)`,
with PAR as its special case. It would be `par_profile` under another name,
and the band, the weight and the result's name would then be spread over
two functions (section 32).

**Rejected:** shipping an absorption spectrum for phytoplankton, for PUR.
Which spectrum applies is a property of the algae, not of the water type,
so the type cannot choose it, for the same reason it cannot choose `bb`
(section 4). A caller with a measured spectrum passes it.

## 37. An example does not silence a warning it does not explain

The package warns rather than refuses when a value rests on a flagged
datum (section 5), on a partly covered sensitivity, or on a colour outside
sRGB. Those warnings are the provenance made visible, and an example that
hides them shows the opposite habit. 0.14.2 found one doing so for a
quantity it never used. Running every example with each `ignore` filter
turned into a log, in 0.14.3, found the rest:

- Six places in four examples ignored `ProvenanceWarning` where nothing
  raised one. They hid nothing, but would have hidden whatever came next.
  They are removed.
- Four places in two examples ignored every warning. In
  `synthetic_underwater_images.py` that hid a `CoverageWarning` on every
  swatch, since the spectra stop at 412 nm, and a `GamutWarning` on 25 of
  the 30 surface-balanced ones, and the text said neither. It now counts
  them and says so under each table, as `lure_colours.py` already did. The
  other two places, one in each example, hid nothing and are removed.

What stays: catching a warning by its category and saying in the text what
it was (`lure_colours.py`, `ultraviolet.py`, `euphotic_zone.py`), and
turning one into an error to show it is not raised (`light_at_depth.py`,
`from_one_measurement.py`). A test now refuses `simplefilter("ignore")`
without a category in an example, and CI runs every example with
`ProvenanceWarning` as an error, as the local checks already did.

## 38. An example may solve what the package does not

Section 12 puts solving the radiative transfer equation out of scope, and
that stands: the package does not ship a solver, and nothing it returns
rests on one. But the questions that need the angular light field, the
radiance from each direction, the mean cosine, the ratio of scalar to
planar irradiance, keep arriving at what the package does carry: a and b,
Petzold's phase functions, pure water's, and a Kd to check against.
Section 33 refused an orientation angle for want of exactly this.

`radiance_distribution.py` (0.14.4) answers them in user code: a Monte
Carlo solution in about 150 lines of NumPy, in the example, not the
package. That keeps the line section 12 drew. The package supplies
coefficients with their provenance; what is done with them, here a
solver, is the caller's, and the example shows one caller's choices with
every one of them stated.

What it must do to be worth showing: check itself against something that
needs no measurement, and against something that does. Gershun's law
recovers the a put in from the model's own irradiances, to within 2
percent, which tests the bookkeeping; Jerlov's (1976) Kd tests the result,
and the example says where it disagrees (a fifth too high at 450 nm),
since the a and b are Williamson & Hollins's and the phase function
Petzold's, not Jerlov's own.

Its choices are its own and are stated: one water type; the Petzold
station whose b is nearest that type's at 530 nm, with the next nearest to
show what the choice moves; the phase function only from the first angle
Petzold measured, the rest taken as unscattered, rather than the report's
extension, which the package flags; and a sun alone or a uniform overcast,
not a clear sky, whose mix of the two the package does not determine.

**Rejected:** moving the solver into the package. It would make every
figure it returns rest on choices the Jerlov type does not fix, the phase
function above all, and would answer them with a default. Section 4 is
why there is none.

**Rejected:** comparing with a published radiance distribution in the
same release. It is in scope (section 31) and planned, but a measured
water's a is rarely published and would have to be fitted, and which
phase function is used moves the result; that needs its own care.


## 39. Comparing the Monte Carlo example with Tyler's lake

Section 38 put off a comparison with a measured radiance distribution.
Tyler's (1958) Lake Pend Oreille tables are the one taken here: seven
depths in water with no definite sign of stratification, a clear sky, a sun
altitude the tables are all adjusted to, and a full sphere of directions
(DATA.md section 23). They are shipped, as `tyler1958_radiance`, so the
comparison can be repeated without the report. As with Jerlov's quanta
(section 31), what the package carries is the measurement; the model it
is compared with stays in the example.

The report gives the water's c and not its a, b or phase function, so the
comparison needs choices, and all of them were fixed before the model was
run on the lake:

- a from the measurement, by Gershun's law, not fitted to it: K of the net
  irradiance between two depths times the mean cosine, with Ed, Eu and E0
  integrated from the tables. The mean of the values from the pairs of
  depth tables that carry no suspect cell, 41.3-53.7 and 53.7-66.1 m.
  b = c - a, with c the surface value.
- The phase function of the Petzold station whose b is nearest that b,
  and the next nearest, as in section 38; not chosen again after the
  result.
- The sun alone and a uniform overcast, to bracket a clear sky, rather
  than a sky model the package would have to choose.
- Fresh water for the surface and for pure water's scattering, at the
  middle of Tyler's band. The comparison is of mean cosine, Eu / Ed,
  E0 / Ed, Kd, and the radiance in the sun's plane relative to overhead,
  at the three deepest tables.

One choice was corrected before the run, not after it. The plan first
used the depth pairs below 28.95 m, the deepest depth at which Table XI
gives the sun's glitter; but 29.0 m is that depth, its table carries the
glitter flags, and the pairs were reduced to the two above. a moves from
0.114 to 0.112 1/m.

What came out is recorded as it came out: the model's mean cosine is
higher than Tyler's at every depth, its Eu / Ed and E0 / Ed lower, its Kd
lower, and its radiance 65 and 85 degrees from the zenith 0.28 to 0.90 of
his relative to overhead. Neither the second phase function nor the
second sky closes it. Which of the model's simplifications makes the
difference is not established, and the example says so rather than
tuning one away.

**Rejected:** fitting a, b or the phase function to the tables. A model
fitted to the measurement agrees with it by construction and tests
nothing.

## 40. Looking for the cause of the difference from Tyler

Section 39 recorded that the Monte Carlo example's light field in Tyler's
lake is gathered closer about the vertical than the one he measured, and
left the cause open. This is what was done about it, written down before
the lake was run again.

First, the engine, since an error there would explain anything. Two
checks that need no measurement, run before this section was written:

- Isotropic scattering in deep water has an exact asymptotic light field:
  K = k c, where k solves (w / 2k) ln((1 + k) / (1 - k)) = 1 for the
  single-scattering albedo w, the mean cosine is (1 - w) / k, and the
  radiance goes as 1 / (1 - k mu). The engine, given an isotropic phase
  function, reproduces K, the mean cosine, Eu / Ed and E0 / Ed within
  3 percent at w = 0.72, the albedo nearest the lake's, and at 0.9; at
  0.5, within 6 percent, the largest difference being Eu / Ed at the
  deepest depth. That tests the path lengths, the
  weights, the roulette and the estimators.
- The turning of a direction by a scattering angle was checked on its
  own. It was exact everywhere except for a direction exactly straight up
  or down, where the test for that case could never be true and the
  photon kept its direction. No photon in the example starts exactly
  vertical, and a scattering lands exactly on the vertical only by a
  floating-point coincidence, so no figure was expected to change, and
  none did; it is corrected all the same.

Then the lake, changing one thing at a time from section 39, with the
sun alone (part 6 shows the two skies giving the same light field at
these depths):

- c at depth. The beam transmittance rose with depth, to give c = 0.377
  1/m at 61 m against 0.396 at the surface; with the deeper value b falls
  to 0.265.
- Every one of Petzold's eight phase functions, not only the two nearest
  in b. This is not a choice of the best: section 39's comparison stands
  with HAOCE 5 and HAOCE 11, and the eight give the range the phase
  function alone can move the result.
- The b at which the model's mean cosine, averaged over the three depths,
  equals Tyler's, with a and the phase function (HAOCE 5) held, found by
  bisection. This fits one number to one measured figure; it is a
  diagnosis, not a model of the lake. What it tests is whether the other
  figures, Eu / Ed, E0 / Ed and the radiance near the horizontal, then
  follow without being fitted, and what c = a + b that b implies.

Not run, and why:

- The band. Tyler's light spans 430 to 546 nm, and the model uses one
  wavelength. Spreading it over the band needs the lake's a at each
  wavelength, which the report does not give and which would have to be
  invented.
- Petzold's extension of his curves below his first measured angle, in
  place of taking that scattering as straight on. It moves directions by
  less than 0.2 degree, against cells 10 degrees wide.
- The surface: waves, and the barge's shadow. At these depths two skies
  as different as the sun alone and a uniform overcast give the same
  mean cosine (part 6), so the light field no longer remembers how the
  light entered.

Whatever comes out is recorded as it comes out, below, and section 39's
comparison is not changed by it.

What came out (part 7 of the example). c at depth moves the model further
from Tyler, to a mean cosine of 0.773. The eight phase functions span
mean cosines of 0.710 to 0.767, and HAOCE 11 and HAOCE 5, the two section
39 chose for being nearest in b, have the two lowest backscatter ratios
and the two highest mean cosines of the eight. With AUTEC 8, NUC 2200 or
NUC 2040 the model comes within 0.002 of Tyler's mean cosine and within
0.007 of his E0 / Ed, its Eu / Ed 1.11 to 1.14 times his. Holding HAOCE 5,
the model reaches his mean cosine at b = 0.48 1/m, c = 0.60, 1.5 times
the report's, and its Eu / Ed, E0 / Ed and horizontal radiance then come
close to his without being fitted. Either a different phase function or a
larger b would do; these figures do not separate the two, and the report
gives no phase function for the lake. Section 39's choice of the station
nearest in b is not a good guide to the phase function, which is worth
knowing wherever it is used, section 38 included.

## 41. An example may turn a face any way

Section 33 refused an angle for the target's face, because turning an
orientation into the light a face receives needs the radiance
distribution, which the package does not determine. That stands for the
package. `radiance_distribution.py` (section 38) now computes a radiance
distribution in user code, so an example can do what section 33 refused,
on the same terms: in the example, with its choices stated.

`painted_sphere.py` (0.15.1) lights a sphere with it: every face receives
the radiance from the half of the directions it faces, and the sunbeam if
it faces the sun, and is seen from above, from below, and horizontally
towards and away from the sun. Looking horizontally it does what
`Scene.observe` does, with `face_irradiance_ratio` for each face computed
rather than passed; looking up or down, the eye and the sphere are at
different depths, and the water between adds the background's radiance at
the eye less its radiance at the sphere thinned by exp(-c r), both taken
from the Monte Carlo.

Its check is the one the package's own convention makes possible: a face
turned straight up must receive Ed, and the irradiance it computes from
the binned radiance and the sunbeam agrees with the Ed the Monte Carlo
counts directly within 2 percent.

The Monte Carlo is copied from `radiance_distribution.py` rather than
imported, so that each example runs alone, as every other does; a test
holds the two copies identical.

What section 40 found applies here: the phase function moves the result,
and the station nearest in b is not a guide to it. The example shows
the next nearest station alongside, and the sphere's luminance against
the water seen from above and with the sun behind moves by a quarter to a
third.

**Rejected:** a function in the package that lights an oriented face.
It would rest on the Monte Carlo's choices, the phase function above all,
and would answer them with a default (section 4).

## 42. Values read from figures, and the fluctuations under waves

DATA.md section 20 said that reading numbers off a figure is not done
here. That was right for what it was said about, a curve averaged from
three laboratories' pure water that the paper never gave as numbers and
that the package did not need. It is lifted, under conditions, for
measurements that exist nowhere else as numbers.

The occasion is the fluctuation of the light under a wavy surface. The
two field studies at hand, Darecki, Stramski & Sokolski (2011) and Gernez
& Antoine (2009), give their results only in figures. Without reading
them the package can say nothing at all about the subject, and a caller
who reads them for themselves gets no record of how.

**The conditions.** A value read from a figure carries
`status = read_from_figure`, never `ok`. Its section of DATA.md says how
it was read and how closely, and its accessor carries that precision.
The reading is done from the published article, by a method that someone
else can repeat: from the drawing commands where the figure is vector
graphics, which gives the markers' coordinates exactly; from the pixels
where it is an image, to the pixel. The build script carries the
coordinates as literals, calibrates each axis on its own tick marks,
and checks the values against whatever the text says about them in
words. What cannot be read to the stated precision is not shipped:
Gernez & Antoine's standard deviation of the period, whose dashed bars
end between dashes, is left out.

**What is shipped, and what is not.** The measurements, with the
conditions they were made under: the depth, the sun, the wind, the
water's c, the collector's size and the sampling rate, as each paper
gives them. Not a model. How strongly the light fluctuates depends on the
wind, the waves, the sky and the size of the collector, none of which the
Jerlov type fixes; a function returning a fluctuation for a type and a
depth would answer them with a default (section 4), and building one from
these few profiles would be deriving new coefficients from observations
(section 12). The same holds for Gernez & Antoine's equation (8), the
change with wind speed: it is a published relation, but as printed it
does not give 1 at zero wind as its definition requires, and it is
recorded in DATA.md section 25 rather than shipped.

**The figures are not reproduced.** The package carries numbers read
from them, cited to the page; it does not carry the images.

**Rejected:** reading the figures less carefully because they are only
figures. A value read to a stated precision by a stated method is as
usable as a printed one to that precision, and one read by eye with no
record is not usable at all.

## 43. Type checking and linting

The package ships `py.typed`, which tells every caller's type checker
to trust its annotations, and until now nothing checked them. The first
run of mypy found two that said less than the code does:
`Descent.transmittance` and the interpolation behind `Water.a` and the
rest are floats for a scalar wavelength, and were annotated as arrays.

**What runs.** `ruff check .` with its default rules, which find unused
names and statements that cannot run, and `mypy` on `jerlov/` with its
defaults. Both run in a CI job of their own, on Python 3.13 and the
newest NumPy, at pinned versions. The weekly run is there to catch the world
breaking this package (the comment in `test.yml`); a new ruff rule or a
stricter mypy is not that, and should arrive as a change someone makes
here, not as a red build.

**The line length is held in the package only.** 79 characters, in
`jerlov/`. The examples print their paragraphs from f-strings, so a
source line is long where the printed line is not, and breaking it would
change what the reader sees or bury the sentence in string pieces. The
build scripts carry transcribed rows one table row to a line, and six of
them write several short statements to a line; their style is left
alone, since every edit to them means rerunning all of them. The rules
ruff applies to them otherwise, unused imports included, are kept.

**Rejected:** mypy's strict mode. Most of the public functions take
`wavelength_nm` as anything array-like and return a float or an array as
NumPy does; annotating that precisely is a change of its own, not a
condition for checking what is already annotated.

## 44. Light under waves, and the check against Darecki

Written before the example was run; the choices below were not changed
after its results were seen.

The light under a wavy surface flickers, and the package carries what
Darecki et al. (2011) measured of it (section 42). Waves are not set by
the water type, so a model of the flicker belongs in an example
(sections 4 and 12): `wave_focusing.py` (0.18.0).

**The sea surface.** The directional spectrum of Elfouhaily et al.
(1997), equation (67), p. 15794, with B_l from equations (31), (32), (2),
(3) and (34), B_h from (40), (41) and (44), and the spreading Delta from
(57) and (59), as printed. The sea is taken as fully developed,
Omega_c = 0.84 (p. 15783), since no fetch was recorded; there gamma is
1.7, so the logarithm in the formula for gamma, whose base the paper does
not state, does not enter. The paper gives no formula for the friction
velocity (p. 15792 points to Garratt 1977 or Wu 1982); the example takes
Wu (1982), equation (1), p. 9704: C10 = (0.8 + 0.065 U10) x 10^-3 and
u* = sqrt(C10) U10, which gives the u* = 0.38 m/s at U10 = 10 m/s that
Elfouhaily's Figure 11 caption states (p. 15793). The wind blows along
the sun's vertical plane, as You et al. (2010) took it.

**Wind heights.** Elfouhaily's wind is at 10 m, Cox and Munk's at 41 ft
(12.5 m, p. 199), and Darecki does not give a height. Darecki's winds are
taken as U10. Other heights follow the logarithmic profile with
kappa = 0.4 and Charnock's constant 0.0185 (Wu 1982, p. 9704).

**The realization.** A linear surface with random phases on a periodic
square 4 m across, 4096 points a side. Waves longer than the square are
left out, and the slope variance they would carry is computed from the
spectrum and printed. The heights and the slopes both enter the ray
tracing. The surface is frozen: the coefficient of variation is taken
over the positions under three realizations, in place of Darecki's time
series at one point. The surface is checked twice: its mean square slope
against what the spectrum gives for the same wavenumbers, and the
spectrum's mean square slope over all wavenumbers against Cox and Munk's
(1954) clean surface, 0.003 + 5.12 x 10^-3 W with W in m/s at 12.5 m
(equation (42), p. 221, where W is in cm/s), within the 0.004 they state.

The first check was written as "within 1 percent", and was changed before
the example was run at full size, when a smaller trial showed it could
not be met: a few waves near 4 m long carry much of the slope, their
amplitudes are random, and the mean square slope of one realization
varies by about a tenth (over 200 realizations on a coarse grid its mean
is within a percent of the spectrum's, so the realization is not biased).
The check is now within three times the spread that the spectrum itself
gives for the mean of the three realizations. The checks against Darecki
below were not changed.

**The light.** The sun at 30 degrees from the zenith (Darecki: 30 to 33;
You et al.: 30), a uniform disc 0.53 degrees across. Each surface point
refracts the sunbeam (n = 1.34 at every wavelength) with the Fresnel
transmittance, and the ray goes straight down to the depth asked for,
where it is collected on a horizontal grid; rays that would meet the
surface again are not followed. The sun's disc and the 2.5 mm collector
are applied together as one blur of that pattern: to first order a small
change in the sun's direction moves the whole pattern, by an ellipse that
grows with depth. Only the light that arrives unscattered carries the
pattern, weighted by exp(-c s) along its path. The rest of the sunlight,
scattered on the way, is a uniform background, its size taken from the
example's Monte Carlo (section 38) with a flat surface. Light scattered
through small angles still carries some of the pattern, so this makes the
modelled variation too small, more so with depth. A sky model is not
chosen here, as section 39 did not choose one, and the sky is left out;
any sky adds to the uniform background and makes the variation smaller
still. The two omissions push opposite ways and are
reported, not balanced.

**The water.** You et al. (2010), Table 1, p. 1046, measured in the Santa
Barbara Channel on 11 September 2008, the day of Darecki's Figure 13a:
c and the single scattering albedo for pure sea water and for the rest at
443, 532 and 670 nm. At 532 nm that gives c = 0.698 per m, against the
c(555) = 0.68 per m Darecki states. The particles scatter with Petzold's
phase function at the station whose b at 530 nm is nearest, as in
section 39. These are the example's values, cited where they are used,
and are not shipped.

**The comparison**, fixed before running: `darecki2011_irradiance_cv()`
at its six depths and three wavelengths, against the model at
U10 = 4.1, 5.5 and 6.4 m/s (Darecki's range, and You et al.'s 5.5). For
every depth and wavelength the example prints the measured coefficient of
variation, the modelled one at each wind, and their ratio. Agreement
means:

1. the modelled variation falls with depth at every wavelength and wind;
2. at every depth it is higher at 670 nm than at 443 nm, as Darecki
   found (p. 12);
3. down to 2.84 m, the measured value lies between half and twice the
   modelled one, at 5.5 m/s.

Below 2.84 m the model is expected to fall short (above), and the ratios
are printed without a mark. Nothing is fitted to the measurements; a
check that fails is reported as it is.

**Rejected:** Pierson and Moskowitz (1964), which You et al. used. Its
spectrum, equation (12), p. 5187, stops at gravity waves, and near the
surface the flicker comes from the short waves (Gernez and Antoine 2009,
p. 7). Also rejected: copying You et al.'s wave model, whose equation (8)
has twice the coefficient that Pierson and Moskowitz's equation (12)
gives when written in wavenumber, for a reason the paper does not state.

## 45. Looking for the cause of the shortfall against Darecki

Written after section 44's run and before any of the runs below.

Section 44's model fell short of Darecki's measurement: down to 2.84 m
the measured coefficient of variation is 1.5 to 2.7 times the model's at
5.5 m/s, more with depth, and the third check failed. As with Tyler
(section 40), the example changes one thing at a time from section 44's
model, at 5.5 m/s, and prints what each does. Nothing is fitted.

**The candidates.**

1. *The scattered light.* Section 44 spread every scattered photon
   evenly. A photon scattered on its way down has followed the same path
   as an unscattered one until then, so it carries the same pattern,
   shifted by how far the scattering has moved it by the time it reaches
   the depth. The light at a depth is then the unscattered pattern
   blurred by the distribution of those shifts, which a Monte Carlo
   gives directly: photons are started along the refracted sunbeam, their
   sideways shift from the unscattered line is recorded where they cross
   the depth going down, and a photon that has met the surface from below
   is spread evenly, since a flat surface would reflect it in a way the
   waves would not. This uses the same scattering as the example's other
   Monte Carlo, from functions copied unchanged.
2. *The phase function.* With the scattered light carrying the pattern,
   how narrow the forward peak is matters. Petzold's other stations whose
   b at 530 nm is within a factor of 3 of You et al.'s, in place of the
   nearest.
3. *The longest waves.* The square 2 m across instead of 4, with the same
   spacing: how much the waves between 2 and 4 m move the result, as a
   guide to what the waves longer than 4 m would.
4. *The shortest waves.* A point every 2 mm instead of every 1 on the 4 m
   square: how much the waves between 2 and 4 mm move it.

Not run: the sky, which can only lower the modelled variation; the wind,
whose whole range was run already; and the instrument's own changes of
depth, about 0.14 m (You et al. 2010, p. 1043), which no fixed depth can
represent.

**What is decided now.** Candidate 1 removes a simplification section 44
named rather than changing a choice, so whatever it gives, it becomes the
example's model from here on, section 44's three checks are applied to it
and printed beside the first result, and section 44's own result stays
printed as it was. Candidates 2 to 4 are shown as sensitivities only and
do not replace a choice.

## 46. A picture of the light shafts

`wave_focusing.py --png` (0.18.1) draws what section 44's surface does
to the water seen from below: the bright lines of section 44's pattern,
seen edge on, are the shafts that seem to spread from the sun. It is a
picture, not a check, and its choices are stated rather than tested
against anything.

**What is drawn.** Looking up towards the refracted sun from 6 m, 70
degrees across, at 532 nm: the unscattered sunbeam at each depth, found
every 5 cm on the 4 m square and blurred by the sun's disc, scattered
once towards the eye by Petzold's volume scattering function scaled to
You et al.'s b, and thinned by exp(-c s) on the way. Below Petzold's first
measured angle the function is held at its first value rather than
extended, since the package warns there. Beside it, the same under a flat
surface, on the same scale, and the one divided by the other.

**For speed** the picture's surface has a point every 4 mm rather than
every 1, on the same square and at 5.5 m/s; section 45 found a 2 mm grid
moves the variation by a few percent, and the shafts are centimetres
across. Lines of sight that run far sideways cross the square more than
once, so far from the centre the pattern repeats every 4 m.

**Left out.** Light scattered more than once, the sky, the sun's own
image and Snell's window: the picture shows where the scattered light
comes from, not everything the eye would see.

**Rejected:** a colour picture from the three wavelengths. Three samples
are not a spectrum, and `painted_sphere.py` uses twelve for its colours.
Also rejected: adding the scattered light from the Monte Carlo as a
background, whose 10 by 45 degree cells are far coarser than the glow
around the sun.

## 47. The ten-minute example runs once in CI

`wave_focusing.py` (section 44) takes about ten minutes, and CI ran it
twice in every job: once in the loop over the examples and once in the
test that recomputes the numbers its documentation quotes. That doubled
each job from about six minutes to about fifteen.

**The test runs it, and the loop skips it.** The test's fixture runs it
as the loop runs the others, with `ProvenanceWarning` an error, so what
the loop checked is still checked. What is no longer exercised in CI is
the script's own `__main__` block, which only reads `--png` and calls
`main()`; `--png` itself is run by hand before each release.

**Rejected:** skipping the test in CI, which would let the quoted numbers
drift without a failed build, and caching the example's output between
jobs, which would tie the jobs together for a few minutes' saving.

## 48. The sky's light under waves

Written before the runs below; the choices and the marks were not changed
after their results were seen.

Sections 44 and 45 left the sky out, and named the omission: light from
the sky arrives from every direction, is hardly gathered by the waves, and
adds to the light that does not flicker, so any sky lowers every modelled
coefficient of variation. Darecki's sun was in a clear sky, which still
sends a fifth or more of the light (Gernez and Antoine 2009 print 21 to 28
percent with the sun 20 to 50 degrees from the zenith, DATA.md section
25). Section 45's model fits Darecki's measurement within a factor of 2
down to 2.84 m and falls to about 0.5 to 0.8 of it below; this section
asks how far the sky moves that.

**The share of the sky.** Gregg and Carder (1990), as Gernez and Antoine
used it, for the direct and diffuse irradiance on a horizontal surface
just above the sea: equations (2), (4) and (6) with (5) and (7), the air
mass (13), Rayleigh's transmittance (15) and (16), the aerosol from the
Navy model reduced to a Junge distribution, (20) to (26), its optical
thickness (27) to (29), its forward-scattering probability (31) to (35)
and its single-scattering albedo (36), as printed (pp. 1660-1666). The
ozone, water vapour and oxygen transmittances multiply the direct and the
diffuse light alike, so the share of the sky does not need them, nor the
extraterrestrial spectrum. The light reflected back and forth between the
sea and the sky, which the paper also leaves out (p. 1660), is left out.
The aerosol is set by its optical thickness at 550 nm rather than by the
visibility; with the paper's 1 km scale height, V = 3.91 / tau km.

**Its check.** With Gernez and Antoine's settings (p. 4): 80 percent
relative humidity, a marine air mass (AM = 1), tau(550) = 0.2, 1013.25
hPa, and, since they give none, a wind of 5 m/s for both of the paper's
winds. They used Shettle and Fenn's maritime aerosol, not the Navy model,
and do not say at what wavelength, so this checks the order, not the
digits: at 20 to 70 degrees each share they print must lie within the
model's range over 442 to 560 nm, widened by 3 points either way. At 80
degrees it is printed without a mark. If the check fails the runs below
still go ahead, and the failure is printed with them.

**Darecki's sky.** Not recorded beyond clear (Darecki et al. 2011, the
sun 30 to 33 degrees from the zenith). The atmosphere is bracketed rather
than chosen: tau(550) = 0.05, 0.1, 0.2 and 0.4, each with a marine (AM =
1) and a continental (AM = 10) air mass, 80 percent relative humidity,
1013.25 hPa, and the wind at 5.5 m/s, You et al.'s, for both winds. The
two lowest optical thicknesses lie below the visibilities Gregg and
Carder observed (8 to 24 km, their Table 2) and stand for a clean marine
sky. The sun is at 30 degrees, as in section 44.

**The sky under the water.** Its radiance is taken as uniform, and its
light under the waves as uniform too: the example's Monte Carlo with
`sun_zenith=None`, a uniform overcast, flat surface, the same water and
phase function as section 45, gives the planar irradiance at each depth
per unit irradiance of the sky above the sea, with the Fresnel loss at the
surface. Times the ratio of diffuse to direct light from above, that is
added to the light that does not flicker in section 45's model, at each
wavelength, depth and wind, and nothing else changes. A real clear sky is
brighter near the sun, and that light is gathered by the waves somewhat
as the sun's is; taking it as uniform gives the sky its largest effect,
so section 45's model without a sky and this one with it bracket the
model's answer.

**What is printed.** For each atmosphere the sky's share at 443, 532 and
670 nm; section 44's three checks applied to the model with that sky; and
the range of measured / model at 5.5 m/s down to 2.84 m and below it. The
full table for the atmospheres with the smallest and largest share.

**Read beforehand.** If with every atmosphere the ratios below 2.84 m
come within 0.8 to 1.25, the sky accounts for the shortfall there; if they
rise but some stay below 0.8, it accounts for part; if none rises by more
than 0.05, it does not. Whatever the result, section 45's model stays the
example's model without a sky; this one is printed beside it, and nothing
is fitted.

**Rejected:** a sky radiance distribution from a radiative transfer
model, which would choose for the reader what Darecki did not record and
the package does not determine (section 39); and adding the sky to
section 44's model, which section 45 replaced.

**The result** (0.19.0, written after the run). The check passed: with
Gernez and Antoine's settings the model gives 21.3 to 44.9 percent at 560
nm with the sun at 20 to 70 degrees, against their 21 to 45, and more at
shorter wavelengths. The sky's share at 443 to 670 nm runs from 6.1
percent (tau 0.05, continental air, 670 nm) to 46.4 (tau 0.4, continental,
443 nm). Every atmosphere passes section 44's three checks. Below 2.84 m
the ratios, 0.54 to 0.77 without a sky, rise to 0.64 to 0.88 with the
smallest share and 0.86 to 1.20 with the largest; down to 2.84 m they rise
from 0.69 to 1.24 to 0.83 to 1.32 and 1.16 to 1.87. By what was read
beforehand the sky accounts for part of the shortfall below 2.84 m: they
all rise, but not every atmosphere brings them within 0.8 to 1.25. The
sky that comes closest below 2.84 m lowers the model too far near the
surface, where at 0.86 m the measurement becomes 1.75 to 1.87 times it, so
no one uniform sky fits every depth.

## 49. The examples run beside the tests in CI

In 0.18.2's CI each test job ran the tests, about 4.5 to 7.75 minutes,
and then the examples, about 1.5 to 2.75; the slowest job (Python 3.10
with numpy 1.22) took about 10.75 minutes, and the run waits for the
slowest job. The examples now run in a job of their own, on the same
versions and with the same commands, which starts with the tests instead
of after them. Every check that ran before still runs, on every version;
a failure in either job fails the run as before. The run should take the
length of the tests, about 8 minutes. A test checks that the two jobs
cover the same versions.

**Rejected:** running the tests in parallel processes (pytest-xdist),
which might save a minute or two more but adds a dependency and changes
how the tests run, for which they would first have to be shown safe;
running the slow examples on fewer versions, which removes checks and
barely shortens a run whose jobs already run at the same time; and a
coarser grid or cached results in `wave_focusing.py`, which would change
or stop checking the numbers its documentation quotes.

## 50. The tests run away from the source tree in CI too

The release workflow runs the tests against the installed wheel from a
copy of `tests/` with nothing beside it, and the tests that need the
source tree (the examples, the README) are marked to skip there. Until
0.19.1 nothing else ran that copy, so a test that needed the source tree
but was not marked passed every CI run and failed only at the tag: two
tests added in 0.19.0 did, and 0.19.0 never reached PyPI. CI's test job
now runs the same copy, with the same command, after the ordinary run,
on every version. It takes a few seconds.

**Rejected:** a test that inspects the other tests for the mark, which
would have to guess from their fixtures what touches the source tree;
running the copy is the check itself.

## 51. The release workflow makes the GitHub Release

Until 0.19.2 a release was made by hand: the GitHub Release was published
with a new tag, its text written each time from CHANGELOG.md, and the tag
started the workflow that uploads to PyPI. Zenodo archives the Release
when it is published, before the upload has run, so when the upload
stopped at 0.19.0 that version was on Zenodo and not on PyPI. And the text
was written twice, once in CHANGELOG.md and once for the Release.

**Now.** The workflow is run by hand from the Actions tab, on main. It
takes the version from `pyproject.toml`, stops if that version is tagged
already, builds and tests as before, uploads to PyPI, and only then makes
the tag and the Release, whose text `tools/release_notes.py` takes from
the version's section of CHANGELOG.md. A version with no section stops it
before anything is uploaded. The text joins CHANGELOG.md's wrapped lines,
since GitHub shows each line break in a Release as a break. Pushing a tag
by hand still runs the workflow, and then a Release that already exists
for the tag is left as it is, so the old way still works.

**Not yet seen.** The Release is made with the workflow's own token.
GitHub does not start other workflows for what that token does, but it
does send the repository's webhooks, through which Zenodo learns of a
Release; the first release made this way will show whether Zenodo
archives it. If it does not, the Release can be republished by hand, and
this section will be followed by one saying so.

**Rejected:** writing the Release's text by hand as before, which is the
duplication this removes; making the Release first and uploading after,
the order that let 0.19.0 reach Zenodo alone; and a separate workflow that
only makes the tag, since a tag pushed with the workflow token would not
start the upload.

## 52. An attenuation coefficient from a Secchi depth

Many of the attenuation coefficients behind the seagrass depth limits
that `seagrass_depth_limit.py` quotes were not measured. Where a report
gave none, Duarte (1991, p. 364) estimated one from the Secchi depth as
K = 1.7 / Sd, citing Poole & Atkins (1929), without saying for how many
reports; Duarte et al. (2007, pp. 652-653) did the same for all but 27 of
424. The example's docstring said "most" of both papers' coefficients
were estimated this way, which Duarte (1991) does not support; it says
what each paper says now. A user with only a Secchi depth, or comparing
with those papers, needs the same step.

**The source.** Poole & Atkins (1929), J. Mar. Biol. Assoc. U.K. 16,
297-324, doi:10.1017/S0025315400029829. Duarte's reference list gives it
the title of their earlier papers ("... the penetration of light into sea
water"); the volume and first page are right, and the paper is
"Photo-electric measurements of submarine illumination throughout the
year". Its Table III (p. 310) compares the Secchi depth D, the deepest at
which the disc was seen from either side of the ship, with the attenuation
coefficient from 0 to 20 m on 14 occasions in 1928 at Station E1, off
Plymouth. That coefficient is natural-log, per metre, of the light on a
horizontal surface, measured with potassium photoelectric cells behind
opal glass, and assumes 15 percent of the light is lost at the surface
(pp. 297-298, 309). D times it ran from 1.32 to 2.18, mean 1.70, from
which "a very rough rule for finding the opacity is 1.7/D" (p. 310); the
scatter shows the method cannot be "anything more than a rough
approximation" (p. 310). The cells' spectral response is not given there
as a waveband, so K stands for whatever they responded to. The tests
transcribe the table and recompute every product, the mean and the range.
One printed percentage in the table, 15.9 for Series 30 and 31, does not
follow from its own D and coefficient (17.0); it is not used.

**Now.** `jerlov.k_from_secchi(secchi_depth_m, coefficient=...)` returns
coefficient / Sd. The coefficient has no default: it is an empirical
ratio, not a property of light in water, so the caller names it. Poole &
Atkins's value is `jerlov.POOLE1929_SECCHI_COEFFICIENT` (1.7). Every call
raises a `ProvenanceWarning`, because the result is not a measurement and
nothing in it says so: it names the coefficient, says the rule defines no
waveband, and gives the 1.32 to 2.18 behind 1.7 and the authors' "very
rough rule". Depths that are not finite and positive, and a coefficient
that is not a single finite positive number, are errors.

**Checks.** Besides the table, the tests recompute K for a few depths and
arrays, the shape of the result, the warning on every call and the
errors. The seagrass example gets a fifth part: K for Secchi depths of 2,
5 and 10 m and the 11 percent depth, which the rule puts at ln(1 / 0.11)
/ 1.7 = 1.30 Secchi depths in any water, and 1.01 to 1.67 across Poole &
Atkins's own range. The example catches the warning by its type and
prints it under the table, as `synthetic_underwater_images.py` does with
its own, so CI, which runs the examples with `ProvenanceWarning` as an
error, still sees any other.

**Rejected:** 1.7 as a default, which would hide the one choice the
result depends on; shipping Table III as data, when only its mean and
range are used; a table of coefficients from other studies, whose papers
have not been read here; and converting the other way, from K to a
Secchi depth, which needs the contrast of the disc against the water as
well as the attenuation and is a different model.

## 53. Why IB's 1 percent level comes out 33 percent too deep: the plan

DATA.md section 22 found the package's 1 percent level of quanta for IB at
93 m against the 70 m of Jerlov (1977, Table 2), and IA at 100 m against
87, while the top 10 m agree. It read Table 5's Kd rising with depth as the
IB stations becoming more turbid below 15 m, and left two things open: why,
and whether the sky's spectrum, for which D65 stands in, matters. This
section is written before the computations below are run.

**A reading of the paper to test first.** Jerlov fitted three equations to
the means over water masses, z(30) = 0.50 z(10) - 0.0023 z(10)^2,
z(3) = 1.65 z(10) and z(1) = 2.18 z(10), and says they "are also valid for
the optical water types defined by the existing classification in terms
of spectral transmittance. The characteristic values of the optical types
are presented in Table 2" (p. 285). If the oceanic rows of Table 2 were made from z(10) with those
equations, their 3 and 1 percent levels are the pooled fit for all water
masses, not measurements of each type, and Tables 3 and 5, which follow
Table 2 (section 22), inherit that. The rising Kd would then be a property
of the fit rather than of the water.

**Test 1, the paper against itself.** For the five oceanic types, I to
III, compute z(30), z(3) and z(1) from the printed z(10) with Jerlov's
equations. Passes if every z(30) is within the printed rounding (0.5 m)
and every z(3) and z(1) within 3 percent, the "slight trend (+-3%)" Jerlov
allows z(1) / z(10) (p. 284). Repeat for the coastal types 1 and 3 and
report, without a criterion.

**Test 2, the package's own ratio.** With the comparison of section 22
unchanged (Jerlov 1976 Kd, D65, 350-700 nm, layer by layer where the
profile goes), compute z(10), z(3), z(1) and z(1) / z(10) for every type.
If Test 1 passes, IB's excess is explained by the ratio when the package's
z(10) is within 2 m of 33 and its z(1) / z(10) is far enough above 2.18
to account for the 23 m: the package's z(10) times 2.18 must then come
within 3 m of 70.

**Test 3, the sky.** Tilt D65 by (wavelength / 550 nm)^n for n from -2 to
2 in steps of 1, a range that covers a reddened sun low in the sky and a
blue overcast, and recompute IB's levels. The sky explains the excess only
if some n brings z(1) within 3 m of 70 while z(10) stays within 2 m of 33.
The same tilt applied as the quanta meter's response, through
`photon_weight`, tests the meter in the same way, with the same criterion.
Jerlov does not give the meters' response here, so this bounds it rather
than models it.

**What follows from each outcome.** If Test 1 passes, DATA.md section 22
is corrected: the comparison below 10 m is with a fit, and the reading of
Table 5 as water becoming more turbid is withdrawn. If it fails, that
reading stands and Tests 2 and 3 say only how much the sky and the meter
could move the result. Either way the numbers quoted are recomputed in
`tests/test_quanta.py`.

**Result.** None of the three tests passes, so the reading of section 22
stands and the cause is still open; what changed is how much is ruled out.

- Test 1 fails, narrowly. Every oceanic z(30) is within 0.2 m of
  Jerlov's equation and every z(3) within 2.4 percent, but the 1 percent
  level of type I is 3.6 percent above the equation's (103 m against
  106.8), outside the 3 percent set above. The other four are within 2.7
  percent. So it is not shown that Table 2 was made from the equations,
  and nothing in section 22 is withdrawn. That z(30) follows the
  quadratic to 0.2 m for all five types is recorded as an observation; the
  coastal types miss it by 0.37 and 0.38 m.
- Test 2 fails at its first condition: the package puts IB's 10 percent
  level at 37.4 m, not within 2 m of 33. The excess does not start below
  the 10 percent level; it grows with depth, 4.4 m at 10 percent, 11.6 m
  at 3 percent and 23.0 m at 1 percent. IB's z(1) / z(10) is 2.49 in the
  package against 2.12 in Table 2.
- Test 3 fails. Over n from -2 to 2 IB's 1 percent level moves from 98.9
  to 84.7 m. At n = +1, the only tilt that keeps z(10) within 2 m of 33
  (34.2 m), it is 89.2 m, 19 m too deep. The sky's spectrum, over that
  range, is not the cause.
- An error in the plan: the same tilt as the meter's response is not a
  second test. A weight on the photons multiplies the spectrum at the
  surface and at depth alike, so it gives exactly the levels of the same
  tilt applied to the sky, as the run showed. What the run tests is the
  product of the two, and neither alone nor together does it explain the
  excess within that range.

The numbers are recomputed in `tests/test_quanta.py`. DATA.md section 22
now says that the sky and the meter were tested and in what range.

## 54. IB's 1 percent level with Austin & Petzold's Kd: the plan

Section 53 ruled out the sky's spectrum and the meter's response over a
wide range, and found the package's IB already 4.4 m too deep at the 10
percent level. Deep in clear water the light that is left is blue, so the
levels depend most on Kd near 475 nm, and that is Jerlov's (1976) table.
Austin & Petzold (1986) revised Jerlov's Kd for the oceanic types from
other measurements (DATA.md), and `jerlov.water(t, source="austin1986")`
carries their values for I to III and 1C at 350-700 nm. This section is
written before the computation is run.

**Test 4.** Repeat the comparison of section 53, Test 2 (D65, 350-700 nm,
layer by layer with `descend`) with `source="austin1986"`. Austin &
Petzold's Kd explains IB's excess if IB's 10 percent level is within 2 m
of 33 and its 1 percent level within 3 m of 70, while II and III stay
within 2 m of Table 2 at every level, as they are with Jerlov (1976).
IA, against 41 and 87 m, and I, against 49 and 103 m, are reported with
the same tolerances but are not part of the criterion.

**Reported without a criterion.** The same with `source="solonenko2015"`,
both its `kd` and its `kd_hydrolight`. Both are fitted to Jerlov's (1968)
values (DATA.md section 19), so they are not an independent check, but
they show how much a smooth model of the same types moves the levels.

**What follows.** If Test 4 passes, DATA.md section 22 says that the
difference lies in Jerlov's (1976) Kd for IB and not in the water below,
and the reading of Table 5 as water becoming more turbid is withdrawn.
If it fails, section 22 says that Austin & Petzold's Kd does not explain
it either, and by how much.

**Result.** Test 4 fails, and on both counts. With Austin & Petzold's Kd
IB's levels are 14.7, 38.5, 67.7 and 95.8 m, deeper than with Jerlov
(1976), not shallower: 5.5 m too deep at 10 percent and 25.8 m at 1
percent. II's 1 percent level moves to 54.6 m, 2.6 m from Table 2, and
III's to 33.2 m, 2.2 m, so the agreement from II down is also slightly
worse. IA is 102.9 m against 87 and I 109.2 m against 103.

The fits of Solonenko & Mobley put IB deeper still: 98.5 m with their
`kd`, 104.1 m with `kd_hydrolight` (IB keeps its type to 200 m in the
profile, so one Kd is the whole descent).

So every published set of spectral Kd for IB that the package carries,
from Jerlov's first and third editions to Austin & Petzold's revision and
a radiative transfer model of the same types, puts the 1 percent level of
quanta between 93 and 104 m (98.4 m with the first edition), against 70
in Jerlov (1977). The difference
is not in one table's values. What is left is the 1977 paper's own IB:
which stations it was formed from, and how, which the paper does not
give per type (section 22). The numbers are recomputed in
`tests/test_quanta.py`, and DATA.md section 22 says so.

## 55. IB's 1 percent level against Nygård's profiles: the plan

Sections 53 and 54 left the 1977 paper's own IB as the only candidate:
which profiles it was formed from, and how. Two of its sources are now at
hand, in Tyler, J. E. (ed.) (1973), Data Report, SCOR Discoverer
Expedition, May 1970, SIO Ref. 73-16, Visibility Laboratory, Scripps
Institution of Oceanography, two volumes, which has no DOI: Morel's
spectral and total irradiance (vol. I, section F) and Nygård's direct
measurements of quanta (vol. II, section I). Jerlov's Table 1 counts 11
of Nygård's observations off Ecuador and Panama, 7 in the Caribbean and 1
in the Sargasso Sea. This section is written before any profile is read.

**What is read.** Nygård's tables give, station by station, the time, the
depth and the downwelling quantum irradiance Q, with Q at 0 m derived
from the reading above the surface; they are not normalised to the deck
monitor (vol. II, p. I-3). From the page images, not the text layer,
every lowering is transcribed that starts at 0 m and has at least three
depths. The station positions are taken from vol. I. Nothing is shipped
in the package; the transcription stays with the analysis.

**What is computed.** For each lowering, Q(z) / Q(0), and the depths of
10 and 1 percent by linear interpolation of ln Q in depth between the
readings that bracket them. A lowering that does not reach a level gives
no value for it. Where Q was read several times at one depth, the mean
of ln Q is used. The deck monitor is not used for the main result, as
Nygård advises; the levels with each reading scaled by the monitor are
reported beside it.

**The test.** Jerlov's types are keyed on the 10 percent level, so a
lowering counts as IB-like if its 10 percent level lies between the
midpoints of Table 2's neighbours, above 28.5 m and at most 37 m (II at
24, IB at 33, IA at 41). For the IB-like lowerings that reach 1 percent,
the median of z(1) / z(10) is compared with Table 2's 2.12 and with the
package's 2.49 (section 53). If it is nearer 2.12, the water measured
did attenuate faster below the 10 percent level than any spectral Kd for
IB allows, and the difference lies in the water, as section 22 read it.
If it is nearer 2.49, the measurements agree with the package and the
difference lies in how the 1977 paper formed its IB. Fewer than three
IB-like lowerings that reach 1 percent decides nothing, and is reported
as such. Every lowering's levels are reported, whatever its class.

**Not in this test.** Morel's profiles in vol. I, which Jerlov also used,
and the region of each station; both are reported if the test is
undecided, without changing the criterion.

**Rules settled while transcribing, before any level was computed.** The
tables needed choices the plan did not make. All 79 pages (vol. II, pp.
I-7 to I-85) were compared with their images, with a draft made from the
text layer.

- A lowering starts at the last 0 m reading before readings below the
  surface, so that a 0 m reading closing the previous lowering, or one
  taken on deck, is not mixed in. It ends where the depth first falls
  more than 6 m below the deepest reading so far, or where the instrument
  changes; within that, every reading counts, including one printed a
  few metres out of order (p. I-18). This keeps the long stationary
  series of the FC 31 meter, which go down in steps and come back up,
  and the quick FC 5 casts, which go down and up, on the same footing.
- Values printed in parentheses (p. I-12) are left out.
- Two pages give upwelling irradiance (pp. I-77, I-84) and are left out.
- Where the printed depth is plainly a slip it is kept as printed and
  noted, since the plan reads the tables, not corrects them: 10.7 m
  between 94.2 and 100.4 m (p. I-14), 4.9 m between 9.9 and 19.8 m (p.
  I-41), and 46 between 159 and 120 at 43.0 m (p. I-66). The last
  brackets the 10 percent level of its lowering; its effect is reported.
- A range in the monitor column is taken as its midpoint, and a reading
  with no monitor value takes the last one given before it in the same
  lowering.

**Result.** The test is decided, and on the side of section 22: the
measured water lost its light faster below the 10 percent level than any
spectral Kd for IB in the package allows.

- From the 19 stations, 48 lowerings start at 0 m with at least three
  depths. 37 reach both levels; 10, at the clearest stations, turn back
  before 1 percent, at 68 to 89 m; one turns before 10 percent.
- Five are IB-like, at stations 3, 12 (two) and 15 (two). Their z(1) /
  z(10) are 2.51, 1.89, 2.01, 1.73 and 1.95, median 1.95: 0.17 from
  Table 2's 2.12 and 0.54 from the package's 2.49. With the monitor the
  median is 1.99 (the first monitor value in a lowering stands for its
  start when the 0 m reading has none).
- Over all 37 lowerings that reach both levels the ratio runs from 1.59
  to 2.51, median 2.05, beside Jerlov's 2.18 for all water masses. The
  package's ratio for IB, 2.49, is at the top of what was measured.
- The two printed slips do not change the test. With 146 for the 46 at
  43.0 m, its lowering's 10 percent level moves from 40.3 to 47.1 m, not
  IB-like either way; 14.9 for the 4.9 m changes nothing.
- A first run had four lowerings that were not: a 0 m reading closing one
  cast taken as the start of the next, which began 8 to 92 minutes later
  or far below the surface (pp. I-13, I-53, I-59, I-80). Every real start
  is followed within 5 minutes by a reading shallower than 11 m. They are
  marked in the table and left out; two of them had been IB-like, and with
  them the median was also 1.95.

What this does not settle. The five lowerings come from three stations.
The quanta meters' spectral response (vol. II, Fig. 3) was not read, but
section 53 found that no tilt of the spectrum within (wavelength /
550)^-2 to ^2 brings the package's IB ratio below 2.33. Why the water
attenuated faster below 10 percent is not shown by quanta alone: R. C.
Smith's spectral irradiance at the same stations (vol. II, section G)
would show whether Kd at each wavelength rose with depth. The
transcription and the analysis are `tools/nygard1973_quanta.csv` and
`tools/nygard1973_levels.py`; `tests/test_quanta.py` recomputes the numbers
above. DATA.md section 22 says so.

## 56. Does the blue light's attenuation rise with depth? The plan

Section 55 found that Nygård's IB-like profiles of quanta lose their light
below the 10 percent level faster than any spectral Kd for IB in the
package allows: z(1) / z(10) 1.95 against 2.49. Deep in clear water the
light that is left is blue, so a constant Kd can be wrong there only if
the blue's own attenuation rises with depth, or if the light is not as
blue as the model makes it. R. C. Smith measured spectral downwelling
irradiance at the same stations (Tyler, ed., 1973, SIO Ref. 73-16, vol.
II, section G), which can tell the first from the second. This section is
written before any of Smith's spectra or attenuation coefficients is read.

**What is read.** For stations 3, 12 and 15, the three with IB-like
lowerings in section 55, every downwelling spectral table: depth, and
irradiance at each printed wavelength, from the page images. Where a
depth was scanned more than once, the mean of ln E is used at each
wavelength. Upwelling tables are not used. Smith gives stations 3 as
measured in clear weather and 12 and 15 as normalised to the deck monitor
in variable weather, with errors that can reach a factor of two (vol. II,
pp. G3-G4); that is reported with the result.

**What is computed.** For each pair of consecutive depths, Kd at each
wavelength printed at both, ln(E(z1) / E(z2)) / (z2 - z1). The blue Kd of
a layer is the mean of those at 465 to 505 nm, the band that carries most
of the quanta deep in IB water.

**Test 1.** At each station with at least two layers, the blue Kd of the
deepest layer over that of the shallowest. It rises with depth at a
station if the ratio exceeds 1.2, and is taken as not rising if it is
below 1.2. Blue attenuation rises with depth in this water if it rises
at two or more of the three stations; it does not if it fails to at two
or more. A station with fewer than two layers is reported and does not
count.

**Test 2, reported without a criterion.** Each layer's blue Kd over that
of Jerlov's (1976) IB at the same wavelengths.

**What follows.** If blue Kd rises, section 22's reading, water becoming
more turbid with depth, has direct spectral support at these stations,
and a Kd that does not change with depth cannot describe them. If it does
not, the faster loss of quanta has another cause, and the spectra are
examined for where the light deep down lies.

**Result.** Test 1 passes by its rule: blue Kd rises with depth at two of
the three stations.

- Station 3, clear weather, two layers at 469-498 nm: 0.025 1/m from 28.9
  to 57.4 m, 0.041 from 57.4 to 85.4 m, a ratio of 1.63. With only 479
  and 498 nm, the wavelengths of the other two stations, 1.29.
- Station 12, five layers at 479 and 498 nm: 0.046 1/m from 9.8 to 18.9
  m, 0.072 from 49.3 to 62.6 m, a ratio of 1.56. The layers between do
  not rise steadily: 0.063, 0.037, 0.065.
- Station 15, five layers: 0.064 1/m from 10.2 to 19.2 m and 0.066 from
  48.3 to 61.3 m, a ratio of 1.03, so it does not rise; but between them
  it reaches 0.109 and 0.083, and at every depth it is above Jerlov's IB.
- Test 2: against Jerlov's (1976) IB at the same wavelengths, 0.037 to
  0.038 1/m, the layers run from 0.68 to 1.11 times it at station 3, 0.98
  to 1.89 at 12 and 1.16 to 2.87 at 15. Every deepest layer is above it.

So at these stations the blue light deep down was attenuated more than
Jerlov's IB attenuates it, and at two of them more than in their own upper
layers; a Kd that does not change with depth describes neither. That is
the spectral side of section 55's quanta, and it supports section 22's
reading that the water was more turbid below.

Cautions. Stations 12 and 15 were normalised to the deck monitor in
variable weather, where Smith puts the error as high as a factor of two,
and give only two wavelengths in the band; their layer-to-layer swings
are of that order. Station 3, the one measured in clear weather, rises
on either set of wavelengths. What made the deeper water more turbid
(chlorophyll, which the report also measured, or other particles) is not
examined here. The transcription and the analysis are
`tools/smith1973_blue.csv` and `tools/smith1973_blue.py`;
`tests/test_quanta.py` recomputes the numbers.

## 57. Carrying the uncertainty of a measured Kd through to PAR

`Water.from_measurements(..., uncertainty={"kd": sigma})` has stored a
standard uncertainty since section 26, but nothing used it: a 1 percent
depth from a measured Kd came out as one number however good the
measurement. Section 26 declined to propagate uncertainty into c because
that needs the correlation between a and b, which only the caller knows.
A calculation that starts from Kd alone does not meet that problem, but
it meets a smaller one of the same kind: the correlation of the errors
between wavelengths, which decides how they add up in an integral over
the spectrum, and which is also only the caller's to know.

**Now.** The errors are taken as fully correlated between wavelengths:
the range reported is that of Kd shifted by k standard uncertainties at
every wavelength together, k = 1 by default, and the calculation is
repeated exactly with Kd + k sigma and Kd - k sigma, not linearised.
That is the assumption `Water.uncertainty` already makes when it
interpolates between wavelengths. It is also the safe one. PAR at any
depth falls as Kd rises at any wavelength, so the two shifted spectra
give the shallowest and the deepest depth that any errors within k sigma
at every wavelength can give; errors correlated less than fully give a
narrower range. When they are fully correlated and normal, the range is
exactly the interval of plus and minus k standard deviations, 68 percent
for k = 1.

- `par_profile` takes the uncertainty from a `Water` that carries one for
  Kd, or as `kd_uncertainty=`, an array on the wavelengths, beside an
  array `kd`. A `Descent` and the packaged types carry none, since no
  source publishes one; asking them for a range raises
  `MissingQuantityError`, as does a gap (NaN) in the uncertainty within
  the band.
- `ParProfile.depth_of_fraction_bounds(fraction, k=1)` returns the
  shallower and the deeper depth; `ParProfile.par_bounds(k=1)` the lower
  and higher PAR at each depth asked for. The surface PAR does not depend
  on Kd and has no range. A Kd minus k sigma below zero at any wavelength
  in the band is refused, not clipped: the uncertainty is then larger
  than the value, and the deeper bound would rest on a Kd that cannot be.
- `classify_kd(..., uncertainty=sigma)` ranks the types again with the
  measurement shifted by plus and minus k sigma, and
  `KdClassification.nearest_within_uncertainty` lists every type that comes
  out nearest in any of the three, the measurement's own nearest first.
  A shift of the whole spectrum moves a measurement along the scale from
  clear to turbid, which is where the types lie, but not across it; a
  type that only an error in the spectrum's shape would make nearest is
  not found. The docstring says so.

**Checks.** With a Kd that is the same at every wavelength, the depth of
a fraction f is ln(1 / f) / Kd whatever the spectrum, so the bounds must
be ln(1 / f) / (Kd plus and minus k sigma); the tests compute it so.
Zero uncertainty gives bounds equal to the depth; the bounds bracket it;
k scales them; the refusals above are tested; and a `Water` built with an
uncertainty gives the same bounds as the array it was built from. The
README shows it on a measured Kd.

**Rejected:** a first-order formula, which is exact only for small
uncertainty and is no simpler to compute than the two shifted spectra; a
Monte Carlo over independent errors, whose answer depends on how finely
the spectrum is sampled, since independent errors average away over more
samples; and a correlation argument, which would ask the caller for a
matrix almost nobody has, to give a range narrower than the one here.

## 58. IB against Morel's profiles, and the chlorophyll at the IB-like stations: the plan

Sections 55 and 56 rest on Nygård's quanta and Smith's spectra. The 1977
paper also drew on Morel's measurements on the same cruise, and the data
report gives the chlorophyll at every station. This section asks two
questions of them, and is written before either is read; while finding
where they are in the report, Morel's table for station 22, set 1 (vol.
I, p. F82), and the size-fractionated chlorophyll of section E for
stations 13 to 21 were seen in passing. Neither is a measurement the
tests below are decided on, except that station 22's lowering counts in
Test A like any other.

**Test A: Morel's profiles of quanta.** Morel's downwelling quanta-meter
tables (vol. I, section F) give, for each station and experiment ("set"),
the quanta at each depth as a percentage of the value above the surface,
already corrected to a constant surface irradiance (p. F3). Every
downwelling set with at least three depths below the surface is read from
the page images; a depth printed twice, at two gain settings, is averaged
in ln. The value just below the surface is taken as t times the value
above it, with t = 0.96 for the light lost at the surface; the 10 and 1
percent levels are then found as in section 55, by linear interpolation
of ln Q in depth. A set is IB-like if its 10 percent level lies above
28.5 m and at most at 37 m. For the IB-like sets that reach 1 percent,
the median of z(1) / z(10) is compared with Table 2's 2.12 and the
package's 2.49, as in section 55, and the result is taken only if it is
the same for every t from 0.92 to 1.00; otherwise, or with fewer than
three such sets, Test A decides nothing. Every set's levels are reported.

**Test B: chlorophyll where the blue Kd rose.** From the routine
fluorometric chlorophyll a of section C (vol. I, Table I), for stations 3,
12 and 15: the mean of the samples whose depth lies within the shallowest
and within the deepest of Smith's layers at that station (section 56).
Chlorophyll rises with depth at a station if the deeper mean exceeds the
shallower by more than 1.2 times. It is consistent with section 56 if it
rises at both stations where the blue Kd rose, 3 and 12; at 15, where the
blue Kd did not, it is reported. A layer with no sample in it leaves its
station uncounted, and is reported.

**What follows.** If Test A agrees with section 55, Morel's instrument and
method, with its own surface correction, give the same answer as Nygård's,
and the result does not rest on one instrument. If Test B is consistent,
phytoplankton deeper down is a sufficient explanation for the rise of the
blue Kd; if not, it is not shown to be one. Neither test gives a cause by
itself; neither changes the package.

**Result, Test A.** It agrees with section 55. All 53 downwelling sets,
at 23 stations, were read (vol. I, pp. F33-F85); 41 reach both levels, 10
turn back before 1 percent and 2 before 10 percent. With t = 0.96 four
sets are IB-like and reach 1 percent: station 10 set 2, station 12 set 1
and station 17 sets 3 and 4, with z(1) / z(10) of 2.16, 2.08, 2.18 and
2.12, median 2.14, against 2.12 in Table 2 and 2.49 in the package. Over
t from 0.92 to 1.00 the median runs from 2.08 to 2.17; at 0.92 and 0.94
station 15 set 2 is IB-like too, with 1.83 and 1.84. Over all 41 sets
the ratio runs from 1.86 to 2.89, median 2.16. So Morel's quanta meter,
with its own correction for the light at the surface, gives the answer
Nygård's did: in water whose 10 percent level is IB's, the 1 percent
level lies about 2.1 times as deep, not 2.5.

**Result, Test B.** It decides nothing, by its own rule. At station 12
no chlorophyll sample lies within Smith's shallowest layer, 9.8 to
18.9 m (the nearest are at 9 and 21 m), so the station is not counted,
and consistency needed it. At station 3 the chlorophyll rose from 0.061
mg m-3 in the shallowest layer to 0.172 in the deepest, 2.80 times, where
the blue Kd rose too; at station 15 it rose from 0.141 to 0.200, 1.42
times, where the blue Kd did not. At station 12 the deepest layer, 49.3
to 62.6 m, holds 0.12 mg m-3 (one depth), below the 0.21 to 0.23 of the
samples at 36 and 45 m. So chlorophyll is higher deep down at both
stations that can be counted, including one where the blue Kd was not;
a subsurface maximum of chlorophyll is consistent with the deeper water
being more turbid, but these data do not show it is the cause.

The transcriptions and analyses are `tools/morel1973_quanta.csv`,
`tools/morel1973_levels.py`, `tools/baird1973_chlorophyll.csv` and
`tools/baird1973_chlorophyll.py`; `tests/test_quanta.py` recomputes the
numbers. DATA.md section 22 says so.

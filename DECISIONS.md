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

## 59. Scalar PAR, from a mean cosine the caller gives

`par_profile` integrates the planar irradiance Ed, and since section 29
its docstring has said that PAR on scalar irradiance E0, what a spherical
quantum sensor reads and what a cell suspended in the water receives, is
larger by a factor the package cannot supply. The factor depends on the
light field: the sun, the sky, the surface and the scattering of the
water, none of which the package models (sections 12 and 38). It can be
measured, or computed by radiative transfer, as
`examples/radiance_distribution.py` does. So the caller gives it, as the
backscatter ratio is given in section 4.

**Now.** `ParProfile.scalar_par(*, mean_cosine, reflectance)` returns
scalar PAR at `depths_m`, umol photons m-2 s-1, from the identity

    E0 = (Ed - Eu) / mu = Ed (1 - R) / mu

where `mu` is the mean cosine of the whole light field, (Ed - Eu) / E0,
and R the irradiance reflectance Eu / Ed, both of the photon flux over
`band_nm` (and of the weighted flux if a `photon_weight` was given). It
is the definition of the mean cosine rearranged, not an approximation, so
the only error in it is the caller's error in mu and R.

- Both are keyword-only and have no default. R is asked for, rather than
  dropped, because leaving out the upwelling light is a choice: passing
  `reflectance=0` makes it, and its cost, a result too high by a factor
  1 / (1 - R), is then one the caller knows they have accepted.
- Each is a number, or one value per depth, of the shape of `depths_m`.
  Nothing is interpolated between depths, and so there is no
  `depth_of_fraction` for scalar PAR: it would need mu and R between the
  depths given. With mu and R the same at every depth the depth of a
  fraction is the planar one, and the docstring says so.
- mu must lie in (0, 1] and R in [0, 1), and together they must satisfy
  mu <= (1 - R) / (1 + R). That is E0 >= Ed + Eu, which holds for any
  light field, since a radiance counts fully in E0 and by its cosine in
  Ed or Eu; equality is light travelling only straight up and down. A
  pair outside it describes no light field and is refused.
- The mean cosine of the downwelling light alone, Ed / E0d, is a
  different and larger number; given here with `reflectance=0` it gives
  the downwelling part of scalar PAR only. The docstring says so.
- The bounds of section 57 are not repeated: `par_bounds()` divided the
  same way gives them, for mu and R taken as exact.

**Checks.** The tests compute three light fields whose ratio is known
without the package: a beam straight down (mu = 1, R = 0, scalar equals
planar); downwelling radiance the same from every direction of the upper
hemisphere and none from below (Ed = pi L, E0 = 2 pi L, so mu = 0.5,
R = 0, scalar twice planar); and light travelling only straight up and
down (E0 = Ed + Eu, at the limit mu = (1 - R) / (1 + R)). Per-depth
values are applied depth by depth, and the refusals above are tested.

**Rejected:** a default mean cosine, such as a value typical of clear
water, for the reason of section 4: it would be defensible somewhere,
wrong elsewhere, and invisible. Taking E0 / Ed directly, which is what
the radiance example prints: it is the same number as (1 - R) / mu, but
the mean cosine is the quantity measured and published, and taking it
with R keeps the upwelling light a visible choice. Interpolating per-depth
values to give a depth of a fraction: it would guess at the light field
between the depths the caller described.

## 60. A review of 0.22.0: what is broadcast, warned or refused

The whole package was read, and every suspected fault was run before it
was listed. Most gave a wrong result, or a result with no sign that it was
wrong; the rest gave an unhelpful error or a misplaced docstring. One more
turned up while planning the third fix. All are fixed in one release.

**1. Salinity as an array.** `pure_water_backscattering`,
`pure_water_scattering` and `bb_from_vsf` returned the value for the first
salinity only when it was an array and the wavelength a number:
`pure_water_scattering(500, salinity_psu=[0, 37])` gave the fresh-water
value alone. `pure_water_vsf` already broadcast the two. All four now do,
and return a float only when every argument was a single number.

**2. A negative Kd in `Scene.at_depth`.** An array `kd` was used as given,
so `kd=-0.1` made the light at 10 m e times brighter than at the surface.
`par_profile` has refused that since it was written. `at_depth` now
refuses a negative or infinite Kd, from an array or from a `Water`, as
`par_profile` does. NaN is still allowed: it marks a gap, and the
downwelling there comes out NaN, visibly. `depth_m` must also be finite:
an infinite depth with a Kd of 0 gave 0 times infinity, NaN, with no word.

**3. An unknown status given to `Water(...)`.** `from_measurements`
refuses a status that is not in the table of DATA.md, since a misspelt
flag would never warn. The constructor, which is public and documents the
same `flags`, accepted any string. It now refuses one too. Planning this
showed the shipped Kd of Austin & Petzold (1986) carries three statuses
the table did not list, `model`, `jerlov_original` and `pure_seawater`,
none of which warns. They are added to the table and to the statuses a
spectrum can carry, so that the check accepts the shipped data. They are
not questionable, so nothing that warns changes.

**4. Negative a, b or Kd in a water.** a, b and Kd in a `Water` are the
total coefficients, pure water included, and none can be negative. A
measured value can come out negative, from noise near zero or, more often,
because a was passed with the pure water already subtracted from it, as
an absorption meter reports. Three ways to treat it were weighed:

- *Set it to zero.* Rejected: that repairs data without a word, which the
  package does not do (sections 6 and 8).
- *Refuse it when the water is built.* Rejected: a single noisy
  wavelength outside the band of interest would make the whole
  measurement unusable, and its values could not even be read back.
- *Accept it, say so, and refuse a result that rests on it.* Chosen, as
  section 8 chose a warning over silence and over an error.

So: building a `Water` with a negative a, b or Kd raises a
`ProvenanceWarning` that names the quantity and the wavelengths, keeps the
values as given, and says what a negative total coefficient usually
means. `a()`, `b()`, `c()`, `kd()` and `bb()` return the values, as they
return any flagged value. A calculation that would turn them into a
result refuses: `Scene` if c is negative at any of its wavelengths,
`veiling_radiance_estimate` if c or bb is, and `Scene.at_depth` and
`par_profile` if Kd is, at the wavelengths each uses. A wavelength that
cannot be trusted can be set to NaN, a gap, or marked `"suspect"`; both
exist already.

**5. Smaller things.**

- `spectrum_to_srgb` refused a white with no power in X, Y or Z, but NaN
  failed that test (NaN <= 0 is False), so a white with a gap gave NaN
  with no word. A NaN white now raises.
- `integrate_response` reported a response sampled at one wavelength as
  fully covered, since its integral is zero; the result was zero. It now
  needs two response wavelengths, as it already needed two spectrum
  wavelengths, and both grids must be finite.
- Arguments that take one number gave NumPy's "truth value of an array
  is ambiguous" when given several: `Scene.transmittance(distance_m)` and
  `Water.bb(backscatter_ratio=...)`. They now say what they take. The
  wavelength queries of `Water` take a number or a 1-D array, and a 2-D
  one, which failed the same way inside, is refused with a message.
- `kd_spectrum` promises an answer of shape `kd.shape + at.shape`, but a
  2-D `at` failed inside the flag check, and an array `kd` with a 2-D
  `at` would not have broadcast to that shape. Both now work as promised.
- In `ParProfile.__init__` the docstring of `band_nm` stood after the
  line setting `_weight`. It is moved back.

**Checks.** Each fault above becomes a test that failed before the fix:
the salinity values against those computed one at a time, a negative and
an infinite Kd and an infinite depth refused by `at_depth`, a misspelt
status refused by the constructor and the shipped Austin types still
built, the warning and each refusal of item 4, a NaN white, a
one-wavelength response, the three shape errors, and `kd_spectrum` on a
2-D `at` against the same values computed one at a time.

## 61. What 1.0 promises, and the changes made before it

1.0 is a promise not to break the way the package is used until 2.0. It
is worth making only once what is promised has been looked at, so the
whole public surface of 0.23.0 was listed, 75 names in `jerlov.__all__`
(38 functions, 22 types, four warnings, one error, ten constants), and
each doubtful point was run before it was listed. This section records
what will be promised, and the changes 0.24.0 makes so that the promise
is one worth keeping. 1.0.0 follows as its own release.

### What is promised

- **The names in `jerlov.__all__`**, imported from `jerlov` itself.
  `jerlov.<module>` is not promised: `import jerlov.water` already gives
  the function `water`, not the module, because the function is bound to
  the package under the module's name. The one example that imported from
  a module, `from jerlov.sources import HALTRIN1999`, did so because the
  name was not exported; `HALTRIN1999` and its type `ScatteringConstants`
  (the type of `Source.scattering`) are added to `__all__`.
- **Reading the attributes of the types the package returns.** Building
  them is not promised: `ParProfile`, `Observation`, `Descent` and the
  rest take their internal values as arguments, and `Descent` has a
  private field `_kd`. The types a caller builds are `Water` (and
  `Water.from_measurements`), `Scene` and `Source`.
- **The arguments, their defaults and the exceptions**, under the rules
  below. The behaviour at run time is promised, not the type annotations,
  which are incomplete and will be filled in during 1.x.
- **The default source of each function** (`williamson2022` for `water`
  and `pure_water_absorption`, section 3; `jerlov1976` for `descend` and
  `classify_kd`). Changing one would change the numbers a call returns
  with no change to the call, so it waits for 2.0.
- **`None` meaning "not given".** `Water.bb(backscatter_ratio=None)` and
  `Scene.observe(face_irradiance_ratio=None)` refuse the omission with a
  `MissingQuantityError` that says what to pass and what passing 1.0 or a
  typical ratio would assume. Removing the `None` would turn that into a
  bare `TypeError`, so it stays, and is the pattern for any argument with
  no defensible default.

Not promised: writing to `SOURCES` (a dict, so it can be written, and
`get_source` would then find the entry), and anything whose name starts
with an underscore.

### The compatibility policy

1. **Correcting a shipped value is not a breaking change.** A number or a
   status that is wrong against its source is corrected in a minor
   release, and the CHANGELOG says so at the top of that release's entry,
   where "No shipped value changed." otherwise stands. Fidelity to the
   source comes before keeping a wrong number stable. A status that
   becomes `suspect`, and so starts to warn, is treated the same way.
2. **No default is added to an argument that has none.** Adding one
   would not break a call, but it would put a guessed value where the
   package now refuses to guess. A new choice gets a new argument or a new
   function instead.
3. **Nothing public is removed or renamed in 1.x.** An old name or way of
   calling keeps working with a `FutureWarning` (shown to users, unlike
   `DeprecationWarning`) for at least one minor release before 2.0, and is
   removed only in 2.0.
4. **Raising the minimum Python or NumPy is not a breaking change.** It
   goes in a minor release, under Packaging in the CHANGELOG.

The policy is written for contributors in CONTRIBUTING.md, and README
points to it in one line.

### The changes in 0.24.0

**1. Salinity has no default.** `pure_water_vsf`,
`pure_water_backscattering`, `pure_water_scattering` and `bb_from_vsf`
defaulted to `salinity_psu=37.0`, and nothing said why. It is not a small
choice: Morel's factor (1 + 0.3 S / 37) makes pure sea water at 37 scatter
30 percent more than fresh water. It is the kind of default section 4
refused for bb. As sections 33 and 34 did for `face_irradiance_ratio`,
it is removed in two steps. In 0.24.0, omitting it still uses 37 and
raises a `FutureWarning` that says what the number does and to pass it;
in 1.0.0 the omission raises `MissingQuantityError`. It also becomes
keyword-only in all four, as it already was in `bb_from_vsf`; passing it
by position still works, with a `FutureWarning`, until 2.0. The three
examples that relied on the default (`radiance_distribution.py`,
`painted_sphere.py`, `wave_focusing.py`) pass 37 explicitly and list it
under "Before you use any of this".

**2. One rule for the type of error.** An unknown name of a *record*
(a water type, a source, a Petzold station, a panel of a figure, a depth
of Tyler's tables) raises `KeyError`, as a lookup does. An argument that
names a *quantity or an option* outside its fixed set (`unit`, `bound`,
`quantity`) raises `ValueError`. `gernez2009_cv_by` and
`gernez2009_band_cv` raised `KeyError` for an unknown `variable`, and
`gernez2009_cv_by` and `gernez2009_spectral_cv` for an unknown `sky` or
`irradiance`, though these name quantities and options; they now raise
`ValueError`. This is done before 1.0 because a changed exception breaks
an `except` clause with no warning that could have been given. The one
`RuntimeError`, for a shipped CSV whose wavelength grids disagree, stays:
it reports a fault in the package, not in the call.

**3. Gernez & Antoine's Figure 8a joins the other panels.**
`gernez2009_cv_by_sun_zenith()` was written in 0.16.0, before
`gernez2009_cv_by`, and stayed the only way to reach Figure 8a; the clear,
downwelling entry of `GERNEZ2009_PLOTS` left the sun's zenith angle out.
`gernez2009_cv_by("sun_zenith_deg")` now returns Figure 8a as a
`ConditionFluctuation` with the same values, and that entry of
`GERNEZ2009_PLOTS` gains `"sun_zenith_deg"` at the front, as the other two
entries have it. The old function keeps working, returning its
`SunZenithFluctuation`, with a `FutureWarning`, until 2.0.
`GERNEZ2009_VARIABLES` keeps its value, the variables of Figures 8b-8d.

**4. The wavelength and spectrum arguments are positional-only.** The
same thing has four names: `wavelengths`, `wl`, `wavelength_nm` and, for
the wavelengths `kd_spectrum` evaluates at, `at`. Renaming them would
break every caller who passes them by keyword, and so would leaving them,
since each name is then part of the promise. Making them positional-only
(`/`) takes the names out of the promise. The parameters before them in
each signature become positional-only with them, since `/` covers a
prefix. A caller passing one by keyword still gets the same answer, with
a `FutureWarning` naming the change, until 2.0. The functions are
`Water(...)`, `Water.from_measurements`, `Water.a`, `b`, `c`, `kd`,
`kd_hydrolight`, `bb` and `uncertainty`, `pure_water_absorption`,
`pure_water_vsf`, `pure_water_backscattering`, `pure_water_scattering`,
`bb_from_vsf`, `b_from_c`, `kd_spectrum`, `spectrum_to_xyz`,
`spectrum_to_srgb`, `integrate_response`, `Scene(...)`, `Scene.at_depth`,
`veiling_radiance_estimate`, `descend`, `par_profile` and `classify_kd`.
The attribute names (`wavelengths` on `Descent`, `wavelengths_nm` on the
fluctuation types) are left as they are: they differ, but each is
documented and none is ambiguous.

**Left as they are, and recorded here.** `Scene(water, downwelling,
wavelengths)` and `Scene.at_depth(water, depth_m, surface_downwelling,
wavelengths)` put the depth in different places; `Water.range_nm` and
`Source.wavelength_range_nm` name the same thing differently;
`Water.caveats()` is a method and `Source.caveats` an attribute.
`solar_fraction(t, z)` and `shortwave_parameters(t).fraction_at(z)` give
the same number, the first as a short way in. The attribute names that
follow a paper's symbols (`beta_D`, `B_inf`, `R`, `zeta1_m`) stay. None of
these is worth a deprecation.

### Checks

Planned before the code was written:

- **No number changes.** Every example's output is compared with its
  output under 0.23.0, captured before any change, and must be identical
  apart from the version in the banner. The examples must raise no
  `FutureWarning`, so they show the new way of calling, as well as no
  `ProvenanceWarning` as before.
- Each change becomes a test: the four salinity functions warn when it is
  omitted and give the value at 37, and warn when it is passed by
  position and give the same value; every function in item 4 has its
  wavelength positional-only in its signature, and a keyword call gives
  the same value as a positional one, with a `FutureWarning`; the
  `ValueError`s of item 2; `gernez2009_cv_by("sun_zenith_deg")` against
  `gernez2009_cv_by_sun_zenith()` value for value, and the old function's
  warning; `HALTRIN1999` and `ScatteringConstants` in `__all__`; and no
  example importing from a module of the package.

**Added while making the changes.** The three examples' new line under
"Before you use any of this" is new output, so the comparison with 0.23.0
allows it beside the banner. Its figure, that fresh water scatters 23
percent less than water at 37, is item 1's 30 percent seen the other way
round; a first draft wrote 30 for both, and the examples now compute it.
CI runs the examples with `FutureWarning` an error as well as
`ProvenanceWarning`, so that none comes to show a replaced way of calling.

## 62. 1.0.0

1.0.0 makes the promise of section 61, under the rules CONTRIBUTING.md
sets out under "Compatibility". It changes one thing and keeps the rest of
0.24.0 as it is.

**The salinity becomes required.** Section 61 item 1 removed the default
of 37 in two steps; this is the second. Leaving `salinity_psu` out of
`pure_water_vsf`, `pure_water_backscattering`, `pure_water_scattering` or
`bb_from_vsf` raises `MissingQuantityError`, which says what the number
does and that 37 is what was assumed up to 1.0. `None` stays in the
signatures, meaning "not given", as section 61 made the pattern for an
argument with no defensible default.

**What stays.** Every other `FutureWarning` that 0.24.0 added is kept
until 2.0, as rule 3 of section 61 requires: a wavelength passed by
keyword, a salinity passed by position, and `gernez2009_cv_by_sun_zenith()`.
They are part of what 1.0 promises to keep working.

**Rejected:** removing those as well in 1.0, on the grounds that 1.0
starts the promise rather than continuing one. They have been out for
one release only, and removing them buys nothing a user would notice.

**The classifier** in `pyproject.toml` moves from "4 - Beta" to
"5 - Production/Stable". It says only that the interface is now held
stable; it says nothing about the data, whose doubts stay where they
were, in DATA.md and in the flags.

**Checks.** No shipped value changes, so every example's output must be
identical to its output under 0.24.0 apart from the version in the
banner, with `ProvenanceWarning` and `FutureWarning` errors as CI runs
them. The four functions must refuse an omitted salinity with
`MissingQuantityError` and no warning, and still give 0.24.0's values
when it is given; the other old ways of calling must still warn and
still work.

## 63. A documentation site

README.md has grown to one long page, and nothing lists the 77 public
names with their arguments. A site on GitHub Pages
(`https://tishibashi-cpu.github.io/jerlov/`) adds guides by purpose and a
reference of the API. It is a change to the project, not to the package:
the wheel carries nothing new, and the release is 1.0.1.

**Sphinx**, pinned at 9.0.4 in the workflow as ruff and mypy are (section
43). The docstrings are already written for it, in its roles (`:func:`,
`:class:`, `:data:`) and NumPy's sections, which `sphinx.ext.napoleon`
reads; MkDocs would show the roles as text. Only the built-in theme is
used. Sphinx is needed to build the site, never to use the package, so
the package still depends on NumPy alone.

**The pages.**

- *Home*: what the package is for and what it will not do, how to install
  it, a first calculation, and where to go next.
- *Three guides*, each for one reader and one question: the colour of the
  light at depth in each water type; the euphotic zone, where PAR falls to
  1 percent; and how far apart two colours stay under water. They use only
  the public API, and every number they show is printed by a code block
  that runs as a test (below). A number in the prose is either avoided or
  tested with the rest of `tests/test_quoted_figures.py`.
- *API reference*, one entry for each name in `jerlov.__all__`, under
  `jerlov.` as section 61 promises, built from the docstrings. A test
  checks that it covers `__all__` exactly. The constants' docstrings live
  in the modules that define them, where autodoc does not look for
  `jerlov.SOURCES`; the configuration finds them there, so that a dict
  does not show the docstring of `dict`.
- *Examples*: the seventeen scripts, with what each is for, linking to
  their source.
- *About*: why the package was started, written by its author, and how to
  report a wrong number. The author chose the wording; it names lure
  fishing as the hobby the first question came from.
- Compatibility, DECISIONS.md, DATA.md and the CHANGELOG are linked, not
  copied: a copy would drift from the file it copies.

**README stays whole** for now. It is the page PyPI shows, and
`tests/test_quoted_figures.py` checks the numbers it quotes; shortening it
would move those checks for no gain to a reader of either. It gains a
link to the site near the top. Whether to cut it down to an introduction
is left until the site has been read for a while.

**The numbers in the guides are tested.** Each guide is a reStructuredText
file whose `>>>` blocks `tests/test_docs.py` runs with `doctest`, from the
source tree, as the other tests run the examples. The outputs are
formatted (`print(f"{x:.3f}")`) rather than left to NumPy's repr, which
changed between NumPy 1 and 2.

**The build fails on any warning** (`sphinx-build -W --keep-going`), so a
docstring that does not render is a failed build, as a broken example is.
Cross-references are not checked strictly ("nitpicky"): in that mode
NumPy's own types and the free text of NumPy-style sections give some 140
false alarms, and quieting them would mean rewriting docstrings for the
tool's sake. The four references that name a module path
(`~jerlov.water.Water` and the like), which the promise of section 61 no
longer stands behind, are changed to the top-level name, and the two
docstrings that do not render are mended. No text in a docstring
changes otherwise.

**The workflow** (`.github/workflows/docs.yml`) builds the site on every
pull request and push, and deploys it to Pages only from `main`, with
`actions/upload-pages-artifact@v5` and `actions/deploy-pages@v5`, the
versions that run on Node.js 24 (section 43). The repository's Pages
source was set to GitHub Actions by its owner.

**Checks.** The site builds with no warning; `tests/test_docs.py` runs the
guides' code and checks the API page against `__all__`; the full test
suite, the wheel's tests outside the source tree and the oldest NumPy
pass; and every example's output is identical to its output under 1.0.0
apart from the version in the banner.

**Added while building the site.** A third docstring did not render:
`ScatteringConstants`, whose formula's continuation lines begin with "+"
and became a bulleted list; it is now a literal block, its text
unchanged. Alabaster's default page, 940 px, cut the docstrings'
79-character lines, so the page is widened to 1140 px. `pyproject.toml`
gains `[project.urls]` (documentation, source, changelog, issues), which
changes the metadata PyPI shows and nothing in the wheel's files. In the
guide on colours, the backscatter ratio was first written as 0.015 and
called typical of the ocean; the package's own docstrings put 0.015 at the
bottom of the coastal range, so the guide uses 0.01, the top of the
open-ocean one, and says so.

## 64. Visual pigments and receptor noise

The direction agreed in 2026-10 was to take from pavo, the R package for
colour vision, only its core: a template for the absorbance of a visual
pigment, with the wavelength of its peak given by the caller, and the
receptor-noise model of colour discrimination, with the noise given by the
caller. Both come from the primary papers, which the author obtained, and
every constant below was read from the page images.

**The template.** Govardovskii, V. I., Fyhrquist, N., Reuter, T., Kuzmin,
D. G. and Donner, K. (2000), "In search of the visual pigment template",
Visual Neuroscience 17, 509-528, doi:10.1017/S0952523800174036.

- The alpha-band is Lamb's (1995) form, eq. (1), p. 515:
  S(x) = 1 / (exp[A(a - x)] + exp[B(b - x)] + exp[C(c - x)] + D), x =
  lambda_max / lambda.
  For A1 pigments, A = 69.7, B = 28, b = 0.922, C = -14.9, c = 1.104,
  D = 0.674, and a = 0.8795 + 0.0459 exp[-(lambda_max - 300)^2 / 11940],
  eq. (2), p. 515. For A2, B = 20.85, b = 0.9101, C = -10.37,
  c = 1.1123, D = 0.5343, A = 62.7 + 1.834 exp[(lambda_max - 625) / 54.2]
  and a = 0.875 + 0.0268 exp[(lambda_max - 665) / 40.7], eqs. (6a) and
  (6b), p. 517.
- The beta-band is a Gaussian, eq. (4), p. 516:
  A_beta exp{-[(lambda - lambda_mbeta) / b]^2}. For A1,
  lambda_mbeta = 189 + 0.315 lambda_max and b = -40.5 + 0.195 lambda_max,
  eqs. (5a) and (5b), with A_beta = 0.26 (p. 516). For A2,
  lambda_mbeta = 216.7 + 0.287 lambda_max and
  b = 317 - 1.149 lambda_max + 0.00124 lambda_max^2, eqs. (8a) and (8b),
  p. 517.
- **A2's beta amplitude has no equation.** The paper says it "shows no
  correlation with lambda_max" and that it was fixed at 0.37 where the
  beta-peak lay outside the recording (p. 517); its Fig. 10 fits 0.37 and
  0.38 where it could be fitted. The template uses 0.37, the value the
  authors used, and the docstring and DATA.md say that it is that value and
  not a regression (decided with the author).
- The function is `visual_pigment_template(wavelengths, /, *, lambda_max,
  chromophore)`. Neither `lambda_max` nor `chromophore` ("A1" or "A2") has
  a default: the first is the species' and the cell's, the second differs
  between fish and between seasons, and both change the answer. It returns
  the sum of the two bands, which the paper calls a complete description
  of the absorbance (p. 525); `beta=False` gives the alpha-band alone.
- **Limits.** The paper states the templates for wavelengths above 330 nm
  (p. 525) and the full template for lambda_max above 350 nm (abstract);
  outside either is refused. The paper's own measurements span lambda_max
  357 to 569 nm for A1 and 444 to 619 nm for A2 (Table 1, p. 519). It
  claims the A1 template for "the whole range of lambda_max" (p. 525), so
  a lambda_max outside the measured range is returned, as a value its
  source extrapolated, with a `ProvenanceWarning` (section 5).
- **Not renormalised.** The alpha-band as printed peaks within 0.2
  percent of 1, not at exactly 1, and within 0.5 nm of lambda_max. It is
  returned as printed, as the package returns any published value.

**The receptor noise model.** Vorobyev, M. and Osorio, D. (1998),
"Receptor noise as a determinant of colour thresholds", Proc. R. Soc. Lond.
B 265, 351-358, doi:10.1098/rspb.1998.0302.

- Quantum catches are scaled so that the background gives 1 in every
  receptor (eqs. 1 and 2, p. 353). Two stimuli are separated by a distance
  Delta S, in units of the receptor noise, given for two, three and four
  receptor types by eqs. (3) to (5) (p. 353), all of which follow from the
  general form (A7) (p. 356) with the opponent channels left unspecified
  (A8) and the noise independent between receptors (A9).
- The function is `receptor_noise_distance(catches_a, catches_b, /, *,
  noise)`: the catches already scaled to the background, and `noise` the
  standard deviation e_i of each receptor channel. The noise has no
  default; the paper derives it from the noise of a single cell and the
  number of cells, e_i = nu_i / sqrt(eta_i) (eq. 7), both of which are the
  species'. It computes (A7) in closed form for any number of receptor
  types, from two upwards.
- **A misprint in eq. (4).** The last term of the trichromat's equation is
  printed e_3^2 (Delta q_1 - q_2)^2, without the Delta on q_2. Computed
  from (A7), as the paper says it is, the term is e_3^2 (Delta q_1 - Delta
  q_2)^2: with the Delta the printed equation agrees with (A7) to 2e-9 for
  random catches and noise, and read as printed it is wrong by orders of
  magnitude. Eqs. (3) and (5) agree with (A7) as printed.
- **The paper's form only.** The model is linear in the differences of the
  scaled catches, valid for stimuli close to the background, in bright
  light, for large static targets on an achromatic background (p. 353).
  The logarithmic form that pavo and later papers use comes from later
  work, which the package does not have; it is not added under this
  citation. The docstring says what the paper says the model is for, and
  that the distance at threshold depends on the criterion adopted.
- Scaling the catches to the background is done with `integrate_response`,
  which already integrates a spectrum against sensitivities; the docstring
  shows how, rather than adding a function for a division.

**Not added.** No species' values. The fish of NEXT_STEPS (*Dicentrarchus
labrax*, Brill et al. 2019) is left for an example in a later release,
where its values are quoted, not shipped, with how much the conclusion
moves if lambda_max moves by 15 nm.

**Checks.** Planned before the code:

- Each constant is tested against the page it was read from, by
  reproducing a number the paper prints from them: eqs. (5a) and (5b) at
  lambda_max = 502.6 nm give the "most accurate point" of p. 516, 347.3 and
  57.5 nm; eqs. (3) (A1) and (7) (A2), the paper's relations between
  lambda_max and the long-wave half-maximum, hold for the template within
  0.5 nm across the measured ranges; the alpha-band peaks within 0.5 nm of
  lambda_max at a height within 0.2 percent of 1.
- `receptor_noise_distance` against eqs. (3) and (5) as printed and eq. (4)
  as corrected, for random catches and noise; against (A7) computed
  directly with random opponent matrices F; and it gives zero for stimuli
  that differ from each other only in intensity (assumption 2).
- Refusals: a wavelength at or below 330 nm, a lambda_max at or below 350
  nm, an unknown chromophore, a noise that is not positive and finite,
  fewer than two receptors, and catches and noise of different lengths. A
  warning outside the measured ranges.
- No example's output changes.

**Corrected while writing the tests.** The misprint was said above to be
wrong "by orders of magnitude" when read as printed. How far off it is
varies widely with the catches, and for some it is less than twice the
distance, so that overstated it. What is true in
every case is simpler: read as printed, the last term holds the catch q_2
itself, so two identical stimuli come out a positive distance apart. DATA.md
section 26 says that, and the test checks it.

## 65. An example: colour differences as a fish's cones count them

1.1.0 added a visual pigment template and the receptor-noise distance.
No example yet runs the chain they make: a pigment's absorbance, the
quantum catches of a fish's cones, and the distance between two colours
in units of receptor noise, through water. This is that example, for a
reader in fish vision or visual ecology. NEXT_STEPS has asked for it
since the fish data were first looked at; section 64 decided that the
species' values are quoted in an example, not shipped.

**The fish.** Brill, R. W., Horodysky, A. Z., Place, A. R., Larkin,
M. E. M. and Reimschuessel, R. (2019), "Effects of dietary taurine level
on visual function in European sea bass (*Dicentrarchus labrax*)", PLOS
ONE 14(6), e0214347, doi:10.1371/journal.pone.0214347, read from its PDF.
They fitted A1 templates, the chromophore assumed and not measured, to
the photopic spectral sensitivity of whole-animal corneal ERG from
hatchery-reared juveniles (pp. 3-5). For fish fed 0 and 1.5 percent
taurine, combined, three pigments fit best (Table 4, p. 12): with the
template of Govardovskii et al. (GFRKD), 388, 501 and 603 nm, alpha-band
only ("Tri, alpha"); with that of Stavenga et al. (SSH), which fitted
better, 389, 512 and 611 nm. The example uses the GFRKD values in the
GFRKD template, `visual_pigment_template(..., beta=False)`, since that is
how they were fitted; the SSH values in the same template are one of the
variants below. The ERG gives the sensitivity of the whole eye, not of
single cones, and the fish were juveniles on experimental diets. The
example says all of this. (The table prints -log(L) for the SSH
trichromat as +120.7 where every other row is negative; that column is
not used.) No cone ratio or receptor noise has been measured for the
species.

**The water.** A horizontal path at 5 m in Jerlov II, 1C and 7C, the
light brought down by Jerlov's (1976) Kd. Along the path, a and b are
Solonenko & Mobley's (2015), not Williamson & Hollins's: the short-wave
cone needs light from 332 nm, and Williamson & Hollins's coefficients
below 412 nm are their model's extrapolation, while Solonenko & Mobley's
cover 300-700 nm, unflagged in these three types, and are fitted to the
same Kd. They are inverted from Kd, not measured (section 3), and the
example says so. The long-wave cone's tail beyond 700 nm is cut off; at
5 m there is almost no light there, and the example says so too. The sky
is D65, converted to photons, since a catch counts photons.

**What is computed.** Two painted surfaces side by side at the same
distance d, their catches scaled to those of the water's own light, the
background a fish looking along the path sees. The receptor-noise
distance between them, Delta S(d), as a share of Delta S at 0.5 m, and
the distance at which it falls to half, d_half. Three pairs of smooth
reflectances: a red and a green; a blue and a green; and two whites that
differ only below 400 nm, which only the short-wave cone can tell apart.

Because both surfaces receive the same veiling light, and both catches
are divided by the water's own, Delta S(d) / Delta S(0.5 m) does not
depend on the backscatter ratio, nor on the light on the face. The two
values the package refuses to guess cancel. The example states the
values it uses and says that they cancel, and a test checks that they do.

**Only what holds is said.** Before running it, the variants are fixed:
the lambda_max sets are the GFRKD values, the SSH values, and each of the
three GFRKD values moved by -15 and +15 nm (eight sets); the noise is
equal in the three cones, or one of them twice as noisy as the others
(four settings), so 32 variants in all. The noise enters only through
its ratios, so no absolute level is assumed. The example reports, for
each water and pair, the range of d_half over the variants, and two
orderings: of the pairs within each water, and of the waters for each
pair. An ordering is stated as a finding only if it is the same in all 32
variants; otherwise the example says it depends on the assumptions, and
on which.

**What it does not say.** Nothing about what a fish notices, or at what
distance it can tell two colours apart: that is visibility, which the
package does not predict (sections 17 and 21), and it would need a
threshold Delta S and a noise level, neither of which is known for the
species. Vorobyev & Osorio's model is for stimuli near the background, in
bright light, for large static targets (p. 353); close to the surfaces the
first is not met, and the example says so. Nothing ties it to fishing;
the targets are painted surfaces.

**Warnings.** Every long-wave lambda_max here lies above 569 nm, the
longest A1 peak Govardovskii et al. measured, so the template warns. The
example catches that `ProvenanceWarning` by type and says why, as section
37 requires.

**Version.** An example changes no API: 1.1.1.

**Checks.** The example's own numbers come from f-strings. A test runs it
and checks: that d_half is the same for two backscatter ratios and two
face ratios, to rounding; that every ordering it calls a finding holds in
all 32 variants, and every one it calls assumption-dependent fails in at
least one; and the quoted Table 4 values against the script's constants.
No other example's output changes.

**Changed on the first run, before any result.** Jerlov's (1976) Kd for 7C,
and for 9C, has no values below 350 nm, so the light coming down cannot
reach the short-wave cone in either; the first run stopped there, before
it computed anything. The types complete in both Jerlov's Kd and Solonenko
& Mobley's a and b from 332 to 700 nm are IB, II, III and 1C. The example
uses II, III and 1C, from clear oceanic water to the clearest coastal
type, and says that turbid water is not covered.

## 66. Kd from chlorophyll and from a and bb, remote sensing reflectance, and the Secchi depth: the plan

Two ways into the package that do not start from a Jerlov type, and two
quantities seen from above the water. The 2026 Jerlov Medal went to Z.
Lee for the work on the Secchi depth and on Kd from a and bb used below;
the chlorophyll route was already planned. Every constant below was read
from a page image of the primary paper.

**Section 12 is narrowed.** It lists remote sensing reflectance as out of
scope. As in section 19, the line was drawn on subject matter rather
than on whether a number's provenance can be established and checked,
and here it can: each relation below is printed with its constants, and
each paper says for which conditions they were fitted. So:

- In, now: the forward relations, from a and bb (and the sun) to Kd and
  to Rrs, and from Kd and Rrs to the Secchi depth.
- In, next (1.3.0, a section of its own before the code): the inverse,
  from Rrs to a and bb, by the quasi-analytical algorithm of Lee, Carder
  & Arnone (2002) as the IOCCG documents it, with its empirical steps
  named by version and checked against a published data set.
- Still out: reading satellite files and atmospheric correction. They
  need dependencies beyond NumPy (section 10) and are SeaDAS's and
  ACOLITE's work. The caller reads Rrs and passes arrays; an example may
  show how.

**1. Kd from chlorophyll.** Morel, A. and Maritorena, S. (2001),
"Bio-optical properties of oceanic waters: A reappraisal", J. Geophys.
Res. 106(C4), 7163-7180, doi:10.1029/2000JC000319.

- Kd = Kw + chi [Chl]^e, eqs. (3) and (5), pp. 7166-7167, with Kw, e and
  chi from Table 2 (p. 7168), 350 to 700 nm every 5 nm. [Chl] is
  chlorophyll a plus divinyl chlorophyll a, mg m^-3, by HPLC (p. 7164).
  Kd is that of the upper layer, from the surface to the first good
  irradiance spectrum, about one penetration depth (pp. 7165-7166).
- `tools/build_morel2001.py` writes `morel2001_kd.csv` from literals, after
  checking them against the text: Kw(420) = 0.00758 (p. 7167); chi and e
  at 390 and 350 nm, 0.119 and 0.67, 0.153 and 0.778 (Figure 7 caption,
  p. 7170).
- Rows below 400 nm repeat the values Morel & Antoine (1994) extrapolated
  below 400 nm (pp. 7169-7170), which the authors call "a kind of lower
  limit" for oligotrophic water and not appropriate for their
  Mediterranean data. They carry the status `extrapolated`, so a request
  there warns. Above 590-600 nm the 1988 values are kept unrevised (p.
  7168); DATA.md says so, without a flag, since the paper presents them
  as its values. The text's own Pope & Fry Kw at 380 nm, 0.0167 (p.
  7169), is not the table's 0.01510; DATA.md records that too.
- `morel2001_kd(wavelengths, /, *, chlorophyll_mg_m3)` returns Kd at the
  wavelengths, interpolating Kd computed on the table's grid. Chlorophyll
  has no default and is a single finite positive number. Outside 350-700
  nm is refused. The pooled data spanned 0.02 to over 30 mg m^-3 (p.
  7164); outside 0.02-30 the result is returned with a warning. The
  docstring says it is for case 1 water only, a statistical mean about
  which individual waters scatter (p. 7164).

**2. Kd from a, bb and the sun.** Lee, Z.-P., Du, K.-P. and Arnone, R.
(2005), "A model for the diffuse attenuation coefficient of downwelling
irradiance", J. Geophys. Res. 110, C02016, doi:10.1029/2004JC002275; and
Lee, Z., Hu, C., Shang, S., Du, K., Lewis, M., Arnone, R. and Brewin, R.
(2013), "Penetration of UV-visible solar radiation in the global oceans:
Insights from ocean color remote sensing", J. Geophys. Res. Oceans 118,
4241-4255, doi:10.1002/jgrc.20308.

- Lee et al. (2005) eq. (11), p. 7 of 10: Kd(E10%) = (1 + 0.005 theta) a
  + 4.18 (1 - 0.52 exp(-10.8 a)) bb, theta the solar zenith angle above
  the surface in degrees; Kd(E10%) is the mean from the surface to the
  depth of 10 percent of the surface irradiance. Fitted to Hydrolight runs
  with the sun at 10 to 60 degrees; good for Kd of about 0.05 to 5.7 m^-1
  (p. 6 of 10).
- Lee et al. (2013) eqs. (3) and (5) and Table 1, pp. 4242-4243: Kd =
  (1 + 0.005 theta) a + (1 - 0.265 eta_w) 4.259 (1 - 0.52 exp(-10.8 a)) bb,
  eta_w = bbw / bb, the share of pure sea water in the backscattering; the
  same layer; fitted with the sun at 5, 30 and 60 degrees, 360-560 nm;
  good for Kd of about 0.02 to 5.0 m^-1 (p. 4243). It corrects the 2005
  model's overestimate in clear water and the UV (p. 4243).
- `lee2005_kd(a, bb, /, *, sun_zenith_deg)` and `lee2013_kd(a, bb, /, *,
  bb_water, sun_zenith_deg)`, one function per paper since their inputs
  differ (section 1). The sun has no default. bb_water has no default
  either; `pure_water_backscattering` gives one for a stated salinity.
  a, bb and bb_water broadcast; each must be finite, a and bb positive,
  bb_water not negative and not above bb. A sun outside 0-90 degrees is
  refused; outside the fitted angles, or a Kd outside the stated range,
  is returned with a warning.

**3. Remote sensing reflectance from a and bb.** Gordon, H. R., Brown,
O. B., Evans, R. H., Brown, J. W., Smith, R. C., Baker, K. S. and Clark,
D. K. (1988), "A semianalytic radiance model of ocean color", J. Geophys.
Res. 93(D9), 10909-10924, doi:10.1029/JD093iD09p10909; and Lee, Z.,
Carder, K. L. and Arnone, R. A. (2002), "Deriving inherent optical
properties from water color: a multiband quasi-analytical algorithm for
optically deep waters", Appl. Opt. 41, 5755-5772,
doi:10.1364/AO.41.005755.

- Below the surface, rrs = g0 u + g1 u^2, u = bb / (a + bb): Gordon et
  al. eq. (2), p. 10910, as R/Q with l1 = 0.0949 and l2 = 0.0794, error
  "significantly less than 10%" for realistic phase functions, and for a
  sun at 20 degrees or more from the zenith; Lee et al. (2002) eq. (1), p.
  5756, who average Gordon's with Lee et al.'s coastal values to g0 =
  0.0895, g1 = 0.1247 (p. 5756). The coefficients are a required argument,
  with the two pairs as constants `GORDON1988_RRS_COEFFICIENTS` and
  `LEE2002_RRS_COEFFICIENTS`; the third pair Lee et al. quote, for coastal
  water, is from a paper not read here and is not shipped.
- Above the surface, Rrs = 0.52 rrs / (1 - 1.7 rrs), the inverse of Lee et
  al. (2002) eq. (8), p. 5757, fitted to Hydrolight for optically deep
  water and a sensor looking straight down.
- `subsurface_rrs(a, bb, /, *, coefficients)` and
  `above_surface_rrs(rrs, /)`. The docstrings say what neither includes:
  a bottom, Raman scattering, fluorescence, and any view but nadir.

**4. The Secchi depth.** Lee, Z., Shang, S., Hu, C., Du, K., Weidemann,
A., Hou, W., Lin, J. and Lin, G. (2015), "Secchi disk depth: A new theory
and mechanistic model for underwater visibility", Remote Sens. Environ.
169, 139-149, doi:10.1016/j.rse.2015.08.002.

- Eq. (33), p. 146: Z_SD = ln(|0.14 - Rrs_tr| / 0.013) / (2.5 Kd_tr), with
  Kd_tr the smallest Kd in the visible, Rrs_tr the Rrs (sr^-1, above the
  surface) at that wavelength, 0.013 sr^-1 the eye's contrast threshold
  (p. 146-147), 2.5 = 1 + 1.5 for the upwelling path (p. 145), and 0.14
  for a white disc of reflectance 0.85 seen through the surface (0.85 /
  pi times 0.54, p. 146; that is 0.146, printed 0.14).
- `lee2015_secchi_depth(wavelengths, kd, rrs, /)`: one Kd and one Rrs
  spectrum on the same wavelengths, all inside 400-700 nm; the paper used
  443-665 nm. The validation spanned Z_SD of 0.1 to 30 m (N = 338, about
  18 percent, pp. 146-147); a result outside that is returned with a
  warning. |0.14 - Rrs_tr| at or below 0.013 gives no positive depth and
  is refused.
- Section 52 rejected converting K to a Secchi depth because that needs
  the contrast of the disc against the water. This model supplies the
  contrast from Rrs, which is the difference; section 52's rejection of a
  bare ratio stands. Unlike Poole & Atkins's 1.7, which carries no
  information beyond the Secchi depth, this is a model with a stated
  validation, so it warns only outside it.

**An example.** `ocean_colour_and_secchi.py`: for II, III and 1C (the
types complete from 400 to 700 nm in Williamson & Hollins's a and b),
bb from a stated bb/b of 0.005, 0.01 and 0.02 and Morel's pure water
backscattering at 35 psu, the sun at 30 degrees: Lee 2013 Kd against
Jerlov's (1976) Kd; Rrs; the Secchi depth by Lee 2015 and the K that
Poole & Atkins's 1.7 would give from it; and, from chlorophyll, Morel &
Maritorena's Kd and the Jerlov type `classify_kd` finds nearest. A
statement about the comparison is called a finding only if it holds for
all three bb/b; the rest is said to depend on bb/b.

**Version.** New public names: 1.2.0.

**Checks.** Planned before the code:

- The build script's checks above, and the CSV reproduced byte for byte.
- Each function against its equation written out by hand in the test,
  for scalars and arrays; `lee2013_kd` with bb_water = 0 against the same
  form with 4.259; `above_surface_rrs` round-tripped through eq. (8) as
  printed; `subsurface_rrs` round-tripped through Lee et al. (2002) eq.
  (3), which returns u.
- 0.85 / pi x 0.54 = 0.146, within rounding of the 0.14 used.
- Refusals and warnings at every limit stated above, with NaN, inf,
  negative, empty, scalar and array inputs.
- The example's numbers from f-strings, recomputed by a test; no other
  example's output changes.

**Changed while writing the code, before any result was read.**

- *0.14 is not within rounding of its derivation.* The plan said the
  paper's 0.85 / pi x 0.54 = 0.146 was "printed 0.14", as if rounded. It
  rounds to 0.15. The package keeps 0.14, as eq. (33) prints it and as the
  validation used it; DATA.md section 27 records the difference, and what
  0.146 would change (Z_SD 1.8 to 2.0 percent deeper), and a test checks
  both.
- *The example's a and b are Solonenko & Mobley's, not Williamson &
  Hollins's.* The latter flag their a at 400 nm as a model extrapolation,
  which warns, and CI runs the examples with that warning as an error.
  Solonenko & Mobley's are unflagged from 400 to 700 nm for IB, II, III and
  1C, so IB is added. Their a and b also come with the Kd Solonenko &
  Mobley computed from them with Hydrolight, using Petzold's
  average-particle phase function, which gives a check on Lee et al.'s Kd
  with nothing else changed: part 1 of the example.
- *bb is built from the particles' ratio.* bb/b applied to the total b, as
  `Water.bb` does, can give a bb below pure water's own backscattering in
  clear water, which `lee2013_kd` refuses. The example takes bb = bb_w +
  r (b - b_w), with b_w and bb_w Morel's at 35 psu and r = bbp/bp of
  0.005, 0.0183 (Petzold's average particle, Hydrolight's) and 0.03, and
  both pairs of reflectance coefficients: six variants for the Secchi
  depth.

## 67. The quasi-analytical algorithm, from Rrs to a and bb: the plan

Section 66 put the inverse in reach and left it to a section of its own.
This is it. Two versions, chosen by the author: the one IOCCG Report 5
documents and tested, which can be checked against its published
statistics, and the current one, QAA_v6, which can be checked against
its author's own spreadsheet.

**The sources.**

- IOCCG (2006), *Remote Sensing of Inherent Optical Properties:
  Fundamentals, Tests of Algorithms, and Applications*, Lee, Z.-P. (ed.),
  Reports of the International Ocean-Colour Coordinating Group No. 5,
  IOCCG, Dartmouth, Canada; chapter 10 (Lee, Carder and Arnone), pp.
  73-77, and the synthetic data set of chapter 2, pp. 15-18, distributed
  by the IOCCG as `IOP_AOP_Sun30.xls` and `IOP_AOP_Sun60.xls`.
- Lee, Z. P., "Steps and calculations of the Quasi-Analytical Algorithm
  (QAA_v6)", IOCCG, `qaa_v6_202011.pdf` (6 pp., 2020; the algorithm was
  updated in March 2009 and November 2014), and the spreadsheet the IOCCG
  distributes with it, `QAA_v6-202011.xlsm`: its formulas, its macro (read
  as text, never run) and the results it stored for 12 example stations.
- Lee, Carder & Arnone (2002), already cited in section 66, for the
  algorithm's form.

**What the documents disagree on.** The v6 document's table of steps and
its text, and the spreadsheet, give three versions of three things:

| | table of steps | text | spreadsheet |
|---|---|---|---|
| g0, g1 | 0.089, 0.1245 | 0.0895, 0.1247 (eq. 1) | 0.08945, 0.1247 |
| exponent of xi | S (442.5 - 415.5) | S (443 - 411) (eq. 12) | S (443 - 412) |
| h0, h1, h2 | -1.146, -1.366, -0.469 | same | the same to 16 digits |

The package follows the spreadsheet: it is the computation its author
distributes, its stored results can be reproduced exactly, and its h are
the table's to the digits the table prints. DATA.md records the three
versions. The spreadsheet's aw at 555 nm is 0.0596 on its QAA sheet and
0.0595 ("Lee et al. (2015)") on its decomposition sheet; a header reads
530 nm over a column computed at 510 nm.

**The functions.** `qaa_ioccg2006(wavelengths, rrs, /, *, bands,
pure_water)` and `qaa_v6(wavelengths, rrs, /, *, bands, pure_water)`, one
per source (section 1).

- `rrs` is the remote sensing reflectance above the surface, sr^-1, at
  `wavelengths`, along its last axis; other axes are spectra.
- `bands` names the wavelengths that play each role: for v6 "412",
  "443", "490", "55x" and "670"; for 2006 "410", "440", "490", "510",
  "555" and "670". Each must be one of `wavelengths`. No default: the
  sensor decides (the v6 table gives 547 nm for MODIS, the text 550 or 555;
  Report 5 averaged 550 and 560 nm for its 555). The formulas use these
  wavelengths, not their names, wherever a wavelength enters (the power
  law of bbp, xi).
- `pure_water` is `(wavelengths, aw, bbw)`, interpolated linearly, and
  must cover every wavelength used, including 640 nm for 2006. No
  default: Report 5 used Pope & Fry's aw and Morel's bbw, the
  spreadsheet its own values, and `pure_water_absorption` and
  `pure_water_backscattering` give the package's.
- It returns a `QAAResult`: `a`, `bbp`, `adg` and `aph` at `wavelengths`,
  `eta` (Report 5's Y), and `reference_nm`, the reference wavelength each
  spectrum used (for 2006, NaN where the 555 and 640 nm solutions were
  blended, eq. 10.11).
- v6: a(55x) from chi = log10((rrs443 + rrs490) / (rrs55x + 5 rrs670 /
  rrs490 rrs670)) when Rrs(670) < 0.0015 sr^-1, else a(670) = aw(670) +
  0.39 (rrs670 / (rrs443 + rrs490))^1.14; eta = 2.0 (1 - 1.2 exp(-0.9
  rrs443 / rrs55x)); zeta = 0.74 + 0.2 / (0.8 + ratio); S = 0.015 +
  0.002 / (0.6 + ratio); adg(lambda) = adg(443) exp(-S (lambda - 443)).
- 2006: a(555) from Kd(555), eqs. 10.2-10.3; a(640) from eq. 10.4 with
  Rrs(640) from eq. 10.5; Y = 2.2 (1 - 1.2 exp(-0.9 rrs440 / rrs555));
  the blend of eq. 10.11; zeta = 0.71 + 0.06 / (0.8 + ratio); S = 0.015;
  xi = exp(S (440 - 410)).
- Nothing is filtered. Report 5 counts 476 of 500 decompositions as valid
  without saying by what rule, so a negative or NaN result is returned as
  computed, and the docstring says so.

**Out, still.** Reading satellite files and atmospheric correction
(section 66). The Rrs(670) limits and estimate of the v6 text, eqs. 7-9,
which the spreadsheet does not apply and which are for satellite data.

**The test data.** `tests/data/ioccg2006_sun30.csv`: of the 500 synthetic
spectra with the sun at 30 degrees, Rrs at the wavelengths used, the true
a, bb, adg and aph where compared, and the pure water values of the data
set; and `tests/data/qaa_v6_spreadsheet.csv`: the 12 stations' Rrs and the
stored results. Written by `tools/build_qaa_test_data.py` from the IOCCG
files in `sources/`, which needs `xlrd` and `openpyxl`, for the tools only
(section 10). Not in the wheel. The IOCCG asks that the data set be cited
as Report 5; DATA.md and the test do. Shipping the subset in the repository
was the author's decision.

**Checks.** Planned before the code. A prototype of the 2006 version, the
equations above as printed, was run on the synthetic data before this
section was written, to see whether a check against Table 10.1 was
possible at all; its numbers are the ones quoted here.

- v6 reproduces the spreadsheet's stored eta, bbp(555) and a at five
  wavelengths for all 12 stations, both branches, to a relative 1e-12
  (the prototype: 4e-16), and its decomposition to the same.
- 2006 against Table 10.1 (p. 76), on the synthetic data with the sun at
  30 degrees, Rrs(555) the mean of 550 and 560 nm as the report did: RMSE
  and bias in log10 (eq. 2.1, p. 18) for a(410), a(440), a(490),
  bbp(440) and bbp(555) within 0.002 of the table (the prototype: 0.000
  to 0.002). Slope and intercept are not tested: "Type II" (p. 17) does not
  say which regression, and the geometric mean and ordinary least squares
  give results that straddle the table's by up to 0.005; DATA.md records
  them. The decomposition rows are reported, not tested: the prototype
  counts 475 valid where the table has 476, by a rule the report does not
  give.
- Each step against its equation written out in the test; refusals for a
  missing or unknown band, a band not among the wavelengths, pure water
  that does not cover them, and spectra of the wrong length; NaN in Rrs
  passes through.
- An example shows the round trip: Rrs from the package's forward relation
  (section 66) for known a and bb, inverted by both versions.

**Version.** New public names: 1.3.0.

**Changed while writing the code.**

- *The script is `tools/qaa_test_data.py`, not `build_qaa_test_data.py`.*
  A `build_` script must write a table into `jerlov/data/`, and a test
  checks that; this one writes `tests/data/`.
- *The regressions were misdescribed.* The plan said the geometric mean
  and ordinary least squares "straddle" Table 10.1's slopes and intercepts
  "by up to 0.005". Computed for all five rows, the geometric mean is
  within 0.004 of the table everywhere; ordinary least squares matches the
  a rows to 0.003 but is off by up to 0.015 for bbp. DATA.md section 28
  gives the numbers. Neither is tested, as planned.
- *The round trip is a fifth part of `ocean_colour_and_secchi.py`*, not a
  new example: it starts from that example's waters and reflectance.
- `tools/README.md` still said eleven scripts read no file; with
  `build_morel2001.py` (section 66) it is twelve, and it says so now.

## 68. bb from the particles' backscattering ratio: the plan

`Water.bb(wl, backscatter_ratio=r)` returns r b, with b the total
scattering, pure water's included. In clear water this can put bb below
pure water's own backscattering: Solonenko & Mobley's type I is nearly
all water, and r = 0.0183 gives bb at 450 nm of 7.0e-5 1/m where the
water alone backscatters 1.75e-3. `lee2013_kd` refuses such a bb.
Section 66 met this in its example, which built bb = bb_w + r (b - b_w)
by hand with Morel's b_w and bb_w at 35 psu. Measured and published
ratios (Petzold's average particle, 0.0183; the 0.005-0.03 ranges in the
docstring) are mostly ratios for the particles, bbp/bp, not for the
whole water.

**The meaning of `backscatter_ratio` does not change** (section 61, the
compatibility rules). A second keyword is added:
`Water.bb(wl, /, *, particle_backscatter_ratio=r)`, which returns

    bb = 0.5 b_w + r (b - b_w)

**b_w is the source's own.** Both sources that give b built it from
Haltrin's (1999) two-component model, whose first term is pure water,
b_w = bw_coeff (400/lambda)^bw_exponent, with the constants each source
prints (`Source.scattering`). Subtracting that, and not Morel's or a
salinity-dependent b_w, leaves the particles' part of the source's own
b, for the same reason `pure_water_absorption` returns the source's aw
(section 20 of DATA.md): the difference must be within one source, not
between two tabulations. Haltrin's Eq. (3) gives 0.5 b_w as the water's
backscattering; the model's water term is symmetric. No salinity is
asked for, because none enters the source's b_w.

Checked before writing this: b - b_w is positive at every wavelength,
1 nm apart, of every type in both sources. The smallest margin is
Solonenko & Mobley's type I at 300 nm, where b exceeds b_w by 2.9
percent; for Williamson & Hollins it is a factor of 8.8 (IB, 300 nm).

**Refusals.**

- Both keywords, or neither: neither raises `MissingQuantityError` as
  now, its message naming both; both raise `ValueError`.
- A `Water` with no scattering model, made by `Water(...)` or
  `Water.from_measurements`, raises `MissingQuantityError` for the new
  keyword: its b_w is unknown, and is not guessed. The caller who
  measured b knows which b_w they removed and can compute bb themselves.
- r must be one number in (0, 0.5), as for `backscatter_ratio`.
- b's own refusals and warnings (range, extrapolated values) pass
  through unchanged, since b is read the same way.

**Linear interpolation.** `Water.b` interpolates the tabulated b
linearly; b_w is the formula at the wavelength asked. Between Solonenko
& Mobley's 17 wavelengths the interpolated b of a convex spectrum lies
above the true curve, so the margin above stays positive; the test
checks it at 1 nm.

**Out.** The particles' ratio is still the caller's: nothing here
derives it from the water type (DATA.md section 10 stands). Haltrin's
own Bs and Bl are not used for the same reason.

**Version.** A new keyword, no new public name: 1.4.0.

**Checks.** Planned before the code:

- The formula written out in the test with the source's constants, for
  scalars and arrays, both sources, several types.
- With r equal to 0.5, bb = 0.5 b (the water and the particles both
  symmetric); bb is never below 0.5 b_w for r in (0, 0.5).
- `backscatter_ratio` returns exactly what it did in 1.3.0.
- The refusals above, with NaN, inf, negative, zero, 0.5, arrays.
- The section 66 example keeps its own Morel-based construction (it
  states its b_w and salinity); its output does not change.

**Changed while writing the code.**

- *The example of the problem was a flagged value.* The plan's
  opening figures, Solonenko & Mobley's type I at 450 nm (bb 7.0e-5 1/m
  against the water's 1.75e-3), are arithmetically right, but every b of
  their type I is flagged `suspect`. The CHANGELOG and the test use their
  type IB, unflagged, at 450 nm: 0.0183 of the whole b gives 1.24e-3 1/m,
  below the water's 1.75e-3; the particles' ratio gives 2.93e-3.
  Williamson & Hollins's IB is not an example: there 0.0183 b is 2.47e-3.
- *A water without b says so first.* For a Kd-only source the new
  keyword raises b's own `MissingQuantityError` ("'b' is not available"),
  not the one about the scattering model, which would have described it
  as made from measurements.

## 69. The particles' ratio for the veiling radiance estimate: the plan

`veiling_radiance_estimate(water, downwelling, wavelengths, /, *,
backscatter_ratio)` computes bb as `water.bb(wavelengths,
backscatter_ratio=...)`, so it has the defect section 68 removed from
`Water.bb`: a bb below pure water's own in clear water, and the veiling
radiance with it, since B_inf is proportional to bb. Section 68 left it
out of scope; the user asked for it on 2026-11-11, in the same 1.4.0.

**The change.** A second keyword, `particle_backscatter_ratio`, passed
to `Water.bb` unchanged. `backscatter_ratio` keeps its meaning. Both
become optional in the signature, and `Water.bb` enforces section 68's
rule: neither raises `MissingQuantityError`, both raise `ValueError`.

**What a caller sees change.** Omitting both used to raise `TypeError`
(a required keyword missing) and now raises `MissingQuantityError`,
saying what to pass. No call that worked behaves differently; the
compatibility rules (section 61) do not count a different exception for
a call that already failed.

**Version.** 1.4.0, with section 68.

**Checks.** Planned before the code:

- With the new keyword, the result equals bb * Ed / (2 pi c) with bb from
  `Water.bb(..., particle_backscatter_ratio=...)`, written out in the
  test.
- With `backscatter_ratio`, exactly the 1.3.0 result.
- Neither, both, and a measured `Water` refused as `Water.bb` refuses.
- No example's output changes (none passes the new keyword).

## 70. Published pure water absorption spectra: the plan

`pure_water_absorption(wl, source=...)` returns the aw a Jerlov source
built its a on, so that `w.a(l) - pure_water_absorption(l)` is a
difference within one source; only Williamson & Hollins publish theirs.
Since 1.3.0 `qaa_v6` and `qaa_ioccg2006` require `pure_water` and have no
default, but a caller who wants the aw IOCCG Report 5 used, Pope & Fry
(1997), cannot get it from the package. This section adds the published
laboratory and in-situ spectra.

**A separate function, not more keys** (the user's choice, 2026-11-11).
These are not Jerlov sources: `water(..., source="pope1997")` could never
work, and mixing the keys would break the meaning of the existing
function and its default, which section 61 keeps. The new function has
no default: which aw to use is the caller's choice, as for `qaa_v6`.

    pure_water_absorption_table(wavelength_nm, /, *, source)

**The sources.** All four obtained by the user as PDFs; the DOIs
resolved at doi.org to the volume, issue and first page below.

| key | paper | what | range |
|---|---|---|---|
| `pope1997` | Pope & Fry, Appl. Opt. 36(33), 8710-8723, 10.1364/AO.36.008710, Table 3 | pure water, integrating cavity, 22 C | 380-727.5 nm, 2.5 nm |
| `smith1981` | Smith & Baker, Appl. Opt. 20(2), 177-184, 10.1364/AO.20.000177, Table I | pure water, from K of the clearest natural waters | 200-800 nm, 10 nm |
| `mason2016` | Mason, Cone & Fry, Appl. Opt. 55(25), 7163-7172, 10.1364/AO.55.007163, Table 2 | pure water, integrating cavity, 23 C | 250-550 nm; 10 nm to 300, then 2 nm |
| `lee2015` | Lee et al., Appl. Opt. 54(3), 546-558, 10.1364/AO.54.000546, Table 1 | "pure" seawater, inverted from Rrs in the clearest oceans | 350-550 nm, 5 nm |
| `lee2015_smoothed` | the same, with its "Smoothed aw" column at the five wavelengths that have one | | |

Lee et al. smooth four dips between 350 and 400 nm that they attribute
to imperfect removal of Raman scattering, and print the result as a
separate column at 360, 370, 385, 395 and 400 nm. Both are offered as
keys rather than one chosen silently (section 1).

**Behaviour.** Linear interpolation between printed wavelengths, no
extrapolation (`ValueError`), NaN refused, a float for a scalar, as
`pure_water_absorption`. An unknown key raises `KeyError` naming the
others. A value with a questionable status warns.

**The tables.** One CSV per paper, transcribed by one script,
`tools/build_pure_water_aw.py`, with the numbers as literals as printed
(Pope & Fry's standard deviation and percent, Mason's sigma, Lee's
smoothed column and Delta aw are carried, not used). Smith & Baker's is
a 1981 scan: read from the page image; the other three from the text,
compared with the image for Pope & Fry.

**Checks inside the papers, run before anything is written.**

- Pope & Fry: the percent column is sigma combined in quadrature with a
  2 percent calibration error and rounded up (p. 8718). All 140 rows
  satisfy it within the rounding of the printed aw and sigma (checked
  before writing this). The minimum is 0.00442 at 417.5 nm; Mason et
  al. quote Pope & Fry's minimum as 0.0044 at 418 nm.
- Smith & Baker: their Eq. (6), K = aw + bsw/2, holds for every row
  within rounding except 710 nm, where aw (0.839) exceeds K (0.834) as
  printed on the page; aw at 710 nm is kept as printed and marked
  `suspect`. Table II repeats K and aw every 50 nm and must agree.
- Mason et al.: the abstract gives the minimum as 0.000811 +/- 0.000227
  at 344 nm; the table's minimum is 0.81e-3 +/- 0.23e-3 there.
- Lee et al.: each smoothed value is "a simple average between the
  shoulders" (p. 554): the mean of the unsmoothed values either side of
  the dip, within rounding.

**Checks against other documents, in the tests.**

- The aw of the IOCCG synthetic data set (`tests/data/`), which Report 5
  attributes to Pope & Fry, against `pope1997` at its 31 wavelengths,
  400-700 nm.
- The aw the QAA_v6 spreadsheet labels "Lee et al (2015)" (412, 443,
  489, 510, 555 nm) is recorded in DATA.md against `lee2015`, not
  asserted: 555 nm lies outside the table.

**Out.** The uncertainties are carried in the CSVs but not returned;
salinity and temperature corrections of aw are not applied. Pope &
Fry's values beyond 700 nm are printed in their Table 3 but their
calibration used 700 nm and below (p. 8716); they are kept as `ok` and
the docstring and DATA.md say so.

**Version.** A new public name: 1.4.0, with sections 68 and 69.

**Corrected before the code.** Three page numbers above were written
before they were checked against the page footers. Pope & Fry's
percent rule is on p. 8719, not 8718; their statement that the
calibration used 700 nm and below is on p. 8717, not 8716; Lee et al.'s
Table 1 and "a simple average between the shoulders" are on p. 555, not
554. Pope & Fry's Table 3 is on pp. 8718-8719, Smith & Baker's Table I
on p. 182 and Table II on p. 183, Mason et al.'s Table 2 on p. 7170.

## 71. Removing Raman scattering from Rrs: the plan

`subsurface_rrs` and `above_surface_rrs` (section 66) give the
reflectance of elastic scattering alone, and both QAA versions (section
67) invert that. A measured Rrs also holds light Raman-scattered by the
water, which in clear water is a sizeable share in the green and red;
inverted as it is, it biases a and bb. Lee et al. (2013), already a
source of section 66, give an empirical correction.

**The source.** Lee, Z., Hu, C., Shang, S., Du, K., Lewis, M., Arnone,
R. and Brewin, R. (2013), J. Geophys. Res. Oceans 118, 4241-4255, DOI
`10.1002/jgrc.20308`; section 3.2, p. 4244, and Table 2, p. 4245:

    RF(l) = alpha(l) Rrs_T(440) / Rrs_T(550) + beta1(l) Rrs_T(550)^beta2(l)   (11)
    Rrs = Rrs_T / (1 + RF)                                                (13)

Rrs_T is the reflectance as measured, Raman included; RF is the ratio of
the Raman part to the rest (eq. 12). Table 2 gives alpha, beta1 and
beta2 at the six MODIS bands 412, 443, 488, 531, 551 and 667 nm, from
Hydrolight runs of the case 1 model of Morel & Maritorena (2001) with
chlorophyll 0.02 to 3 mg m-3. beta1 carries the unit of Rrs (sr-1). The
signs of beta2 are lost from the PDF's text and were read from the page
image: all six are negative, as the text says (p. 4244).

**The function.** `lee2013_raman_correction(wavelengths, rrs, /, *,
bands)`, returning `RamanCorrection` with `wavelengths`,
`raman_factor` and `rrs` (corrected). Two public names (the user's
choice, 2026-11-12: both RF and the corrected Rrs).

- `rrs` is Rrs_T above the surface, sr-1, along the last axis, as for
  the QAA functions; `bands` names the wavelengths playing "440" and
  "550", each one of `wavelengths`. No default: MODIS has 443 and 547 or
  551 nm, other sensors other bands.
- RF is computed at the six bands and **interpolated linearly in
  wavelength between them**, as the paper does with hyperspectral data
  (p. 4246). Wavelengths outside 412-667 nm raise `ValueError`.
- **Not offered: the paper's extension** (the user's choice). For its
  hyperspectral validation the paper "interpolated and extrapolated" RF
  to 350-550 nm without saying how, and set RF to 0 below 400 nm "to
  represent the assumed low Raman-scattering contribution". The first
  would need an extrapolation rule the paper does not give, the second
  is an assumption rather than a result, and neither can be checked
  against a published number. The docstring says what the paper did, so
  a caller can do it explicitly.
- Rrs_T must not be negative or infinite (as for QAA); NaN passes
  through. Rrs_T at the "550" band must be positive: it is raised to a
  negative power and divides.
- No warning for chlorophyll outside 0.02-3 mg m-3: it cannot be told
  from Rrs. The docstring states the range of the simulations.

**Checks.** Planned before the code:

- Table 2 transcribed as printed, checked against the page image; at the
  six bands RF equals eq. (11) written out by hand.
- Between bands, RF is the linear interpolation of the RFs at the bands.
- eq. (13) and its inverse: Rrs (1 + RF) returns Rrs_T.
- A plausibility check, not a validation: on the 500 spectra of the
  IOCCG Report 5 synthetic data set (`tests/data/`), which exclude
  inelastic scattering (Report 5, p. 15), so are Rrs rather than Rrs_T,
  RF is below the paper's "generally less than 0.20" at every spectrum
  for 440, 490, 510, 550 and 560 nm (maximum 0.135 at 560 nm; computed
  before writing this) and rises with wavelength.
- Refusals at every limit above; NaN, inf, negative, zero, empty,
  scalar and array inputs.

**Version.** New public names: 1.5.0.

**Corrected before the code.** Report 5 says the synthetic data exclude
inelastic scattering on p. 17, not p. 15 (p. 15 is where it says their
aw "were taken from Pope and Fry (1997)").

## 72. Chlorophyll to aph and bbp, for case 1 water: the plan

Section 66 gave Kd from chlorophyll (Morel & Maritorena 2001) and Kd,
Rrs and the Secchi depth from a and bb, but nothing from chlorophyll to
a and bb. With that link the two routes to Kd can be compared, and
chlorophyll leads on to Rrs and the Secchi depth (NEXT_STEPS section
0b, item 4).

**The sources, and one that could not be used.**

- Bricaud, A., Babin, M., Morel, A. and Claustre, H. (1995), J. Geophys.
  Res. 100(C7), 13321-13332, DOI `10.1029/95JC00463`. Table 2 (pp.
  13,326-13,327): a*ph(l) = A(l) [Chl]^-B(l), with A, B and r2 every 2
  nm from 400 to 700 nm and at 675 nm, from 815 spectra spanning
  [Chl] 0.02-25 mg m-3 (abstract). Obtained by the user; a scan, so all
  456 numbers were read from the page images and agree with the text
  layer. The text twice gives a*ph(440) = 0.0403 [Chl]^-0.332, the
  table's 440 nm row.
- Morel, A. and Maritorena, S. (2001), section 66's source, eqs. (9),
  (13) and (14), pp. 7170-7171.
- Not used: Bricaud, A., Morel, A., Babin, M., Allali, K. and Claustre,
  H. (1998), J. Geophys. Res. 103(C13), 31033-31044, DOI
  `10.1029/98JC02712`, obtained by the user. It refits the same kind of
  power law to 1166 spectra, for all particles and for phytoplankton,
  but prints the spectral coefficients only as a figure (Figure 4); the
  values "at 2-nm intervals can be provided on request" (p. 31,038).
  Only the 440 nm relations are printed. The user chose the 1995 table
  over reading the figure or asking the authors.

**The functions.** One per source (section 1); the user's choice,
2026-11-12, of these two and no more.

- `bricaud1995_aph(wavelengths, /, *, chlorophyll_mg_m3)`, 1/m:
  aph = [Chl] a*ph = A [Chl]^(1 - B), computed at the table's
  wavelengths and interpolated linearly between them; outside 400-700 nm
  `ValueError`. Outside 0.02-25 mg m-3 a `ProvenanceWarning`.
- `morel2001_bbp(wavelengths, /, *, chlorophyll_mg_m3)`, 1/m: eq. (13)
  with (14) and (9),

      bbp(l) = {0.002 + 0.01 [0.50 - 0.25 log10 Chl] (l/550)^v} bp550
      v = (1/2)(log10 Chl - 0.3) for 0.02 < Chl < 2, v = 0 above 2
      bp550 = 0.30 Chl^0.62

  **Eq. (10), as printed, is not used.** It is the 1988 form (maximum
  efficiency 0.02, a (550/l) dependence throughout), which the next
  paragraph modifies "in two ways": the maximum reset to 1 percent, and
  the exponent varying with [Chl], giving (13) and (14) (the user's
  choice). Eq. (9) is the paper's; its (9'), which subtracts pure
  water's scattering, is called negligible by the paper and not used,
  so that the function is what the paper computed. Within the paper,
  (14) gives v = -0.9995 at 0.02 and +0.0005 at 2 mg m-3, the "l^-1 at
  0.02" and "neutral at 2" its text describes; (14)'s unit is printed
  "mg-3".
  350-700 nm, the model's domain, as `morel2001_kd`. Below 0.02 mg m-3
  the first branch of (14) is used and warns, as does anything above
  30 (section 66's data range). Above 100 mg m-3 the bracket, which the
  paper says becomes zero at 100, turns negative: refused.
- [Chl] is one positive finite number for both, as for `morel2001_kd`;
  wavelengths a number or an array, NaN and inf refused.

**Not given: nonalgal particles, CDOM, pure water.** The example takes
them as stated choices: pure water from `pure_water_absorption_table`
(section 70) and `pure_water_backscattering`; nonalgal particles from
Bricaud et al. (1998) eqs. (3) and (5) with their mean slope, 0.011
nm-1; CDOM varied, as Bricaud et al. (1998) do in their appendix.

**Checks.** Planned before the code:

- `tools/build_bricaud1995.py` carries Table 2 as literals and checks:
  400-700 nm every 2 nm plus 675; the 440 nm row against the text's
  equation; at 443 nm, interpolated A and B within the ranges the text
  gives (A 0.0394-0.0406, B 0.330-0.344, p. 13,325); r2 within 0-1.
- Each function against its equations written out in the test, scalar
  and array; the (14) branch at 2 mg m-3; refusals and warnings at every
  limit above.
- The example: a and bb from chlorophyll into `lee2013_kd`, against
  `morel2001_kd`, for several chlorophyll values and stated CDOM and
  nonalgal choices; a statement about the comparison is a finding only
  if it holds for every choice.

**Version.** New public names: 1.6.0.

**Corrected before the code.** Two page numbers above were written
before they were checked: the 443 nm ranges of A and B are on p. 13,324
of Bricaud et al. (1995), not 13,325, and "can be provided on request"
on p. 31,037 of Bricaud et al. (1998), not 31,038.

## 73. Rrs with water and particles apart, Lee et al. (2011): the plan

Section 66's reflectance, rrs = g0 u + g1 u^2 with u = bb/(a + bb), treats
all backscattering alike. Molecular and particle scattering have
different phase functions, so their shares of bb reach the sensor
differently. Lee et al. (2011) keep them apart, and give coefficients for
other viewing geometries than straight down (NEXT_STEPS section 0b,
item 3).

**The source.** Lee, Z. P., Du, K., Voss, K. J., Zibordi, G., Lubac, B.,
Arnone, R. and Weidemann, A. (2011), "An inherent-optical-property-
centered approach to correct the angular effects in water-leaving
radiance", Appl. Opt. 50(19), 3155-3167, DOI `10.1364/AO.50.003155`
(resolved at doi.org); obtained by the user. Eq. (14), p. 3158:

    Rrs(l, W) = (G0w(W) + G1w(W) bbw/k) bbw/k + (G0p(W) + G1p(W) bbp/k) bbp/k,
    k = a + bb

Rrs above the surface: the paper folds the crossing of the surface into
the coefficients. They were fitted to Hydrolight runs on the 500 IOP sets
of IOCCG Report 5, bb/(a + bb) 0.0002-0.37 (p. 3159), with particle phase
functions blended from Petzold's average and a Fournier-Forand of
backscattering ratio 1 percent.

**Only seven geometries are printed.** The paper derived (6 x 7 x 13 + 6)
sets, for sun zenith 0-75 degrees, viewing zenith 0-70 and relative
azimuth 0-180, but Table 2 (p. 3159) prints "a few samples": seven
columns, (sun, view, azimuth) = (0, 0, 0), (0, 30, 90), (15, 30, 90),
(30, 30, 90), (0, 40, 135), (15, 40, 135), (30, 40, 135). The user chose
all seven (2026-11-12). Its nadir column, 0.0604, 0.0406, 0.0402,
0.1310, is the set Lee et al. (2013) quote (p. 4244). The table agrees
with the page image. Not offered: interpolation between geometries,
which the paper does not describe.

**The function and the constant.** One per source (section 1), as
`subsurface_rrs` takes `GORDON1988_RRS_COEFFICIENTS`:

- `LEE2011_RRS_COEFFICIENTS`: a read-only mapping from (sun zenith,
  viewing zenith, relative azimuth), degrees, to (G0w, G1w, G0p, G1p),
  the seven columns as printed.
- `lee2011_rrs(a, bb, /, *, bb_water, coefficients)`: eq. (14), sr-1.
  bbp = bb - bb_water. `coefficients` is four positive numbers, no
  default; one of the mapping's values or the caller's own (the paper
  says they "can be easily revised/updated"). a and bb as for
  `lee2013_kd`: positive, NaN passes; bb_water not negative and not
  above bb.
- Outside bb/(a + bb) 0.0002-0.37 a `ProvenanceWarning`: the fit's data
  did not reach there.

**Not claimed.** NEXT_STEPS recorded that this form was said to be more
accurate than Gordon's in clear water. The paper makes no such
comparison, so neither does the package.

**Checks.** Planned before the code:

- The seven columns against the page image and the nadir column against
  Lee et al. (2013); the count (6 x 7 x 13 + 6) against the angular grid
  the text gives (six sun angles; seven viewing angles from 10 to 70 at
  thirteen azimuths, plus nadir for each sun).
- Eq. (14) written out in the test, scalars and arrays; bb_water = bb
  leaves only the water terms; refusals and the warning at its limits.

**Version.** New public names: 1.7.0.

## 74. The downwelling distribution function D0, and Kd at another sun angle: the plan

Kd depends on the light field as well as on the water: the same water
has a larger Kd with the sun low. Jerlov's tables do not say at what sun
angle, or under what sky, their Kd were measured. Gordon (1989) showed
that dividing Kd by D0, the downwelling distribution function just
beneath the surface (the reciprocal of the mean cosine of the downwelling
light), removes most of that dependence (NEXT_STEPS section 0b, item 6).
The user chose (2026-11-12) to take D0 and the rescaling now and to
leave the oblique-path Scene (section 0, item 4) to a release of its
own.

**The source.** Gordon, H. R. (1989), "Can the Lambert-Beer law be
applied to the diffuse attenuation coefficient of ocean water?", Limnol.
Oceanogr. 34(8), 1389-1409, DOI `10.4319/lo.1989.34.8.1389` (resolved at
doi.org). A scan with a text layer, from a university course site;
equations and the table were read from the page images.

- Eq. (12), p. 1401, for a sky of uniform radiance:
  D0 = f / cos(theta_w) + 1.197 (1 - f), with f the fraction of the
  irradiance transmitted through the surface that is direct sunlight,
  and theta_w the sun's zenith angle in the water.
- Table 3, p. 1399: D0 computed exactly beneath a flat surface with a
  model atmosphere, at 440, 480 and 550 nm, for sun zenith 0-80 degrees
  and a diffuse sky (1.197), with 1/cos(theta_w) beside it.
- Accuracy of eq. (12) against Table 3 (p. 1402): within about 3 percent
  for the sun up to 60 degrees; at 80 degrees 5-8 percent too low (with
  their eq. 13 for the direct part) or 0.5-4 percent too high (eq. 14).
- K/D0 as nearly an inherent property: K/(c D0) and <K>/(c D0) fall on
  single curves of (1 - w0 F) for every sun angle and wavelength
  computed, fitted with an average error of 1.8 and 2.2 percent (p.
  1399).

**The refractive index.** The text gives "about 1.33 for the ocean"
(p. 1392). Table 3's 1/cos(theta_w) column is reproduced to its printed
rounding at every angle by n = 1.333 (checked before writing this) but
not by 1.33 (25, 60 and 80 degrees miss). The package uses 1.333 and
says why.

**The functions.** One per source (section 1):

- `gordon1989_d0(sun_zenith_deg, /, *, direct_fraction)`: eq. (12) with
  Snell's law at n = 1.333. f has no default: it depends on the sky
  and is the caller's measurement or estimate (the paper's shadow
  method). The sun from 0 up to but not including 90 degrees; above 60 a
  `ProvenanceWarning` citing the accuracy above. f within 0-1.
- `gordon1989_kd(kd, /, *, d0_from, d0_to)`: kd * d0_to / d0_from,
  rescaling a Kd measured under one light field to another, on the
  strength of K/D0 being nearly independent of the light field. Both
  D0 are required: **Jerlov's tables do not record the conditions, so
  the package cannot supply d0_from for them**, and the docstring says
  so. The paper's K is Kd just beneath the surface and <K> its mean over
  the upper half of the euphotic zone; the docstring says the rescaling
  is for those, not for Kd at depth.

**Not done here.** The oblique path for `Scene`; rough-surface
corrections to D0 (the paper's Fig. 9, readable only from a figure);
anything requiring a model of the sky.

**Checks.** Planned before the code:

- Snell's law at 1.333 against Table 3's 1/cos(theta_w) column, all
  seven angles, to its rounding; f = 0 gives 1.197, the table's diffuse
  row; f = 1 gives 1/cos(theta_w).
- Eq. (12) written out in the test; the rescaling written out;
  refusals (sun negative or at or above 90, f outside 0-1, NaN, D0 not
  positive, Kd negative) and the warning above 60 degrees.

**Version.** New public names: 1.8.0.

**Corrected while writing the code, before any result was read.** The
plan says n = 1.333 reproduces Table 3's 1/cos(theta_w) column at every
angle. It does not: at 40 degrees it gives 1.14148, which rounds to
1.141, and the page image prints 1.142. No single index reproduces all
seven rows: searched from 1.3200 to 1.3499 in steps of 0.0001, the most
rows matched is six, by n from 1.3325 to 1.3332, every one of them
missing 40 degrees. 1.333 is among those, matches the text's "about
1.33" better than 4/3 (which misses 40 and 80 degrees), and is kept.
DATA.md records the 40 degree row.

## 75. A slanted line of sight for Scene, Duntley (1963): the plan

Section 13 kept `Scene` to horizontal lines of sight, saying a slanted
one would need integration along a changing depth. In uniform water it
does not: Duntley (1963) gives a closed form, and a diver or a camera
looking down at the bottom or up at the surface is not a rare case
(NEXT_STEPS section 0, item 4). Section 74 left this to a release of its
own; the user chose the design below on 2026-11-12.

**The source.** Duntley, S. Q. (1963), "Light in the sea", J. Opt. Soc.
Am. 53(2), 214-233, DOI `10.1364/JOSA.53.000214`. A scan with a text
layer; the equations were read from the page images, at 300 dpi, after
the text layer garbled them. The PDF's page n is the journal's page
213 + n, checked on each page used.

- Eq. (8), p. 229: Cr/C0 = Tr * bN0 / bNr, the contrast transmittance,
  "rigorously true despite any amount of nonuniformity".
- "Uniform water", p. 229: when the background radiance's profile is a
  straight line on a log scale, eq. (9) dN/dr = -K(z,theta,phi) cos(theta) N,
  "where r cos(theta) = zt - z", and eq. (10) dN/dr = N* - alpha N, with
  alpha the beam attenuation coefficient (c in this package).
- Eq. (12), p. 230: the apparent radiance of the target, its own
  radiance attenuated by exp(-alpha r) plus the path radiance.
- Eq. (13), p. 230: radiance differences fall as exp(-alpha r) along
  any path.
- Eqs. (14)-(16), p. 231: the contrast against any background, against
  the water itself, and with K constant (the asymptotic light field),
  Cr/C0 = exp[(-alpha + K cos(theta)) r].
- p. 230: alpha and K are taken as constant along the path; in uniform
  water alpha is, K is not unless the light field is asymptotic, but
  "because underwater sighting ranges rarely exceed 2/K, the effect of K
  variation is seldom appreciable, except near the surface of the sea".

**Two misprints, found before any code.** Eq. (12) prints the factor in
front of the path radiance as exp[+K r cos(theta)]. With that sign, a
"target" that is the water itself (tN0 = N(zt)) does not come back as
the background radiance eq. (9) gives at the observer, and eq. (14)
cannot be derived from eq. (12) as the text says it is. With
exp[-K r cos(theta)] both hold, and eqs. (9), (13), (14), (15) and (16)
agree with one another; checked numerically (alpha 0.3, K 0.1,
cos(theta) 0.6, r 7). Eq. (16) prints an unmatched parenthesis,
"exp[-alpha+K cos(theta))]r"; eq. (15) makes the meaning plain.

**Which way theta points.** "r cos(theta) = zt - z" comes from
Duntley, Boileau and Preisendorfer (1957), where z is altitude; the 1963
paper uses depth instead (p. 229) and the sign of cos(theta) for
looking up or down is not stated again. The package does not take an
angle. It takes the two depths and the distance, and writes the
result without theta:

    path radiance = Nw(z) * (1 - exp[-c r - K (zt - z)])
    direct        = Lt * exp(-c r)

with Nw(z) the radiance of open water seen from the observer along this
line of sight, and K = -d ln Nw / dz along it, positive when that
radiance falls with depth, as it does looking up or down in daylight.
This is eq. (12) corrected, with K r cos(theta) replaced by the change
of ln Nw between the two ends; it follows from eqs. (8)-(10) alone.
Looking down (zt > z) the contrast falls faster than exp(-c r), looking
up more slowly, as Duntley's Fig. 29 and text describe. A horizontal
line (zt = z) gives `Scene.observe` exactly.

**The method.** `Scene.observe_slant(reflectance, distance_m, *,
target_depth_m, kd, water_radiance, radiance_attenuation,
face_irradiance_ratio)`, returning an `Observation`:

- The observer is at the scene's `depth_m`; a scene without one raises
  `MissingQuantityError`. `target_depth_m` not negative; `distance_m`
  not less than the difference of the depths, which is refused.
- `water_radiance`, Nw(z), has no default. For a horizontal line it is
  B_inf; `veiling_radiance_estimate` is for that case and the
  docstring says it is not for a slanted one.
- `radiance_attenuation`, K, has no default (the user's choice). It is
  not Kd: it belongs to one direction and depends on the light field;
  only in the asymptotic field is it the same in every direction
  (p. 231). A number or an array on the wavelengths.
- The target is lit by Ed(zt) = Ed(z) exp(-Kd (zt - z)), with `kd` as
  `Scene.at_depth` takes it (a Water carrying Kd, or an array; not a
  Descent, which starts at the surface). The user's choice.
- `Observation.transmittance` is exp(-c r) and `veiling` the path
  radiance above, so `Observation.contrast` gives eqs. (13)-(15) with
  no change.
- Uniform water between the two depths, as for the horizontal path.

**Not done here.** K varying along the path (Preisendorfer's integral,
p. 230); a target's illumination other than by exponential Kd; anything
about the surface or a window ([n(z)/n(zt)]^2, p. 229, is 1 underwater).

**Checks.** Planned before the code:

- zt = z gives `observe` to the last bit.
- A target that is the water (Lt = Nw(zt)) reads Nw(z) at the observer.
- Eq. (13), eq. (14) and eq. (15)/(16) through `Observation.contrast`,
  with K (zt - z) = -K' r cos(theta) written out.
- Looking down loses contrast faster than horizontally, looking up
  more slowly.
- Refusals: no depth on the scene, r < |zt - z|, negative depths,
  missing or negative inputs, K not finite.

**Version.** A new method on `Scene`, no new top-level name: 1.9.0.
DATA.md gains a section for the source and the two misprints.

## 76. The clear-sky irradiance at the sea surface, Gregg and Carder (1990): the plan

Most examples stand in D65 for the light above the sea, and every
depth calculation starts from a surface spectrum the caller has to find
(NEXT_STEPS section 0b, item 5). Gregg and Carder (1990) give the
direct and diffuse irradiance just above and just below the sea surface
under a cloudless maritime sky, at 1 nm from 350 to 700 nm, with a table
of everything spectral the model needs. Section 48 already used its
diffuse share in `examples/wave_focusing.py`, leaving out the gases and
the sun's spectrum because they cancel in the share. This section ships
the whole model. The user chose the design below on 2026-11-12.

**The source.** Gregg, W. W. and Carder, K. L. (1990), "A simple
spectral solar irradiance model for cloudless maritime atmospheres",
Limnol. Oceanogr. 35(8), 1657-1675, DOI `10.4319/lo.1990.35.8.1657`. A
scan with an OCR text layer, supplied by the user; the equations and
Table 1 were read from the page images at 300 dpi. The PDF's page n is
the journal's page 1656 + n, checked on each page used.

- Eqs. (2)-(7), p. 1660: direct and diffuse (Rayleigh and aerosol)
  irradiance above the surface; the ground-air term (8) is left out by
  the paper itself (p. 1660-1661).
- Eqs. (9)-(11), p. 1660: the same just below the surface, through the
  direct and diffuse surface reflectances.
- Eqs. (12)-(19), p. 1661: the sun's distance, the air masses, Rayleigh,
  ozone, oxygen and water vapour.
- Eqs. (20)-(36), pp. 1664-1666: the Navy aerosol model reduced to a
  Junge distribution, the Angstrom exponent, the optical thickness from
  the visibility, and the aerosol's forward scattering and
  single-scattering albedo.
- Eqs. (37)-(47), pp. 1666-1667: the sea surface's reflectance, specular
  and foam, for the direct and the diffuse light.
- Table 1, pp. 1662-1663: H0, the mean extraterrestrial irradiance (W
  m-2 nm-1), and the ozone, water vapour and oxygen absorption
  coefficients (cm-1), at every nm from 350 to 700. Water vapour and
  oxygen are printed from 560 nm; below that the paper has none.

**Table 1, transcribed.** 351 rows, as printed, to
`jerlov/data/gregg1990_table1.csv` by `tools/build_gregg1990.py`, every
value read against the page images. The OCR layer misreads four oxygen
entries (676, 677, 681 and 685 nm), which the page prints as 0.000, and
splits 689 nm across two lines. Water vapour and oxygen below 560 nm are
written as 0, stated in the file's note, since the paper prints nothing
there and its eqs. (18) and (19) give a transmittance of 1 for a zero
coefficient.

Checked before writing: 351 consecutive wavelengths; every coefficient
not negative; H0 averaged over 11 nm against Bird and Riordan's (1984)
Table 2-1 (SERI/TR-215-2436, the same Neckel and Labs revised spectrum
in 122 bands), within 5 percent at each of their wavelengths from 350 to
690 nm (it is within 1.5 percent except at 350 nm, the edge, and 430 nm,
the G band).

**The misprint in eq. (44).** The Fresnel reflectance is printed as
1/2 [1/2 sin2(theta - theta_r) / sin2(theta + theta_r) + tan2(...) /
tan2(...)], with a second 1/2 inside the bracket. As printed it gives
0.0159 at normal incidence, where Fresnel's law gives ((n-1)/(n+1))^2 =
0.0212 for n = 1.341, and 0.0143 at 40 degrees, where eq. (46) takes
over at 0.0253; without the inner 1/2 it gives 0.0254 there. The
package uses Fresnel's law without it.

**The function.** `gregg1990_irradiance(wavelength_nm, /, *,
sun_zenith_deg, day_of_year, pressure_hpa, air_mass_type,
relative_humidity, precipitable_water_cm, wind_speed_24h,
wind_speed, ozone_du, visibility_km=None,
aerosol_optical_thickness_550=None)`, returning a `SurfaceIrradiance`
with the direct and diffuse irradiance just above and just below the
surface, in W m-2 nm-1, the Angstrom exponent and the aerosol optical
thickness at each wavelength.

- **No input has a default** (the user's choice). Exactly one of the
  visibility and the aerosol optical thickness at 550 nm (the user's
  choice): the paper uses the visibility, tau(550) = 3.91 / V with a 1
  km scale height (eqs. 28, 29); a measured tau(550) replaces that step
  and nothing else.
- Wavelengths: whole nanometres from 350 to 700, the rows of Table 1.
  Anything else is refused rather than interpolated, so that no
  absorption coefficient is invented; the caller can interpolate the
  result.
- No ozone climatology (Van Heuklon 1979) and no sun position from
  place and time: both are the caller's.
- Refused: a sun at or below the horizon, relative humidity of 100
  percent or more (eq. 24 divides by zero there), air-mass type outside
  1-10, negative amounts, NaN.
- The ranges the paper's observations covered (Table 2, p. 1667) are in
  the docstring; outside them nothing warns, as the paper states no
  limit of validity.

**Checks.** Planned before the code:

- Table 5 (p. 1670), at its standard conditions (sun at 60 degrees,
  1013.25 hPa, AM 1, RH 80, WV 1.5, WM 3, W 5, V 10 km, 300 DU): the
  share of diffuse light in the global irradiance above the surface,
  56 percent, and at both ends of each of the eight ranges (sixteen
  values, 34 to 79 percent), to the printed whole percent. The rms and
  largest deviations in the same table are checked for their sign, for
  the wavelength of the largest within 10 nm and their size within 25
  percent; the paper does not define its rms closely enough to do more
  (a prototype matches the shares exactly and the deviations to 0.1 to
  3 points).
- Table 4 (p. 1669): V = 16 km with AM = 10, and V = 8 km with AM = 1,
  at 60 degrees with the other conditions as in Table 5: direct and
  diffuse 59:41 and 37:63, the Angstrom exponent 1.2 and 0.2, and the
  global irradiance over 350-700 nm about 2 W m-2 lower in the second.
- Eq. (44) at normal incidence gives ((n-1)/(n+1))^2; the direct
  reflectance is continuous at 40 degrees to within the paper's own
  rounding (0.0254 against 0.0253); foam reflectance at 20 m/s about 2.3
  percent, as Fig. 2 shows.
- The equations written out in a test at one set of conditions.

**Not done here.** Clouds; the ground-air multiple reflections
(dropped by the paper); the radiance distribution of the sky; changing
`wave_focusing.py`, whose share of the sky section 48 already checked.

**Version.** New public names: 1.10.0. DATA.md gains a section for the
source, the transcription and the misprint.

**Changed after the first run of the tests.** The plan checks the
wavelength of Table 5's largest deviation within 10 nm for all eight
inputs. For the 24 h mean wind that failed: the paper prints 358 nm and
the model's largest is at 381 nm. The deviation lies between 0.15 and
0.27 percent at every wavelength, and at 358 nm it is 0.261 against the
largest, 0.269, so where its largest falls is not a property of the
model worth checking. Its wavelength is
no longer checked; its sign and size still are, and pass. The other
seven inputs pass as planned.

## 77. An example: the clear sky against D65

Twelve examples stand D65 in for the light above the sea, because until
1.10.0 there was nothing better to hand. `gregg1990_irradiance` (section
76) gives a modelled spectrum for a stated sun and sky. The user asked
(2026-11-12) for an example that compares the two rather than one that
swaps one for the other, so that the reader sees how much the choice
matters and where.

**`examples/sunlight_and_d65.py`.** One atmosphere, stated at the top and
printed: Gregg and Carder's Table 5 standard conditions (1013.25 hPa,
air mass type 1, 80 percent humidity, 1.5 cm of water, winds of 3 and 5
m/s, 300 DU) with a visibility of 10 km, on 21 June (day 172), and the
sun at 0, 30, 60 and 80 degrees from the zenith. Visibilities of 5 and 25
km, the ends of Table 5's range, where the visibility is the question.
Five parts:

1. **The shape.** D65 and each sky, scaled to the same energy over
   400-700 nm. The ratio of 450 to 650 nm (D65 1.46; the model's skies
   1.15 to 1.30 for the sun up to 60 degrees, so redder than D65, and
   bluer again as the sun nears the horizon and the sky's light takes
   over), and the CIE 1931 chromaticity. The model stops at 700 nm and
   the colour matching functions go on to 830, so every chromaticity,
   D65's included, is computed over 350-700 nm, and the example prints
   how far that moves D65's own (x by 0.0002) and the coverage the
   package's warning reports.
2. **The level.** PAR above the sea in W m-2 for each sun and
   visibility. D65 has no level; any absolute quantity needs a sky.
3. **The 1 percent depth of PAR**, with `par_profile` and Jerlov's
   (1976) Kd, below D65 and below each sky (`.below`, through the
   surface). It is a ratio, so only the shape matters. The prototype
   finds the model's skies put it up to about 3 m shallower in IB and
   within a few tenths of a metre in the coastal types.
4. **A white card at depth** in Jerlov III, as a camera white-balanced
   to D65 in air records it, lit by D65 and by each sky. The prototype
   finds the blue channel differs by up to about 7 percent of its
   value, the green by about 1.
5. **D0 and Kd.** The share of direct light just below the surface at
   490 nm, from the model, as Gordon's (1989) f; `gordon1989_d0` with it
   for each sun; and `gordon1989_kd` carrying Jerlov II's Kd(490) from a
   sun at 30 degrees to the others. The example says plainly that
   Jerlov's tables do not record the sun they were measured under, so
   30 degrees is an assumption made to show the size of the effect, not
   a property of the table.

**What it does not claim.** The model is one cloudless maritime sky; real
skies have clouds and other aerosols. Nothing here says D65 is wrong for
the examples that use it: the point is the size of the difference, which
part 3 and part 4 put in the reader's own units.

**Checks.** `tests/test_quoted_figures.py` recomputes every figure the
examples README quotes for it, runs it with `ProvenanceWarning` as an
error except where it reports a warning on purpose (the coverage), and
checks that the 1 percent depths are a function of the shape only
(scaling a sky by 3 changes nothing).

**Version.** An example only, nothing in the API: 1.10.1.

**Differences from the plan, noted after the example was written.**
The green channel in part 4 differs by up to 2 percent, not "about 1"
(the prototype's 1.4 rounded the other way). The warnings the example
reports are the coverage of the colour matching functions and, from
10 m, the sRGB gamut; and in part 5 the `ProvenanceWarning` that
`gordon1989_d0` gives above 60 degrees is silenced for the 80 degree
row, which the example labels as the formula's rather than a
measurement's. Everything else is as planned.

## 78. An example: looking up and looking down

`Scene.observe_slant` (section 75) takes the radiance of the water along
the line of sight, Nw, and how fast it falls with depth, K; neither has a
default. The package already ships a measurement of both: Tyler's (1958)
radiance distribution in Lake Pend Oreille (DATA.md section 23), at seven
depths and every direction, with the lake's beam attenuation. It is also
the lake whose measurements Duntley (1963) draws on. The user chose this
example on 2026-11-12, after section 77's, in the same release.

**`examples/looking_up_and_down.py`.** An observer at 41.3 m, one of
Tyler's depths, chosen so that the targets at the depths above (29.0 and
16.6 m) and below (53.7 and 66.1 m) lie at nearly the same distances,
12.3 to 12.4 m and 24.7 to 24.8 m. Directions: straight up (tilt 0),
40 degrees from it, horizontal, 40 degrees from straight down (tilt 140)
and straight down, at an azimuth of 80 degrees from the sun so that no
cell near the sun's direction is used. Along a tilted line the distance
to a target at another of Tyler's depths is the difference of the depths
over the cosine of the tilt.

- **Nw and K from the tables, not fitted.** Nw is Tyler's radiance at the
  observer in that direction; K over each path is ln(Nw(z) / Nw(zt)) / (zt
  - z), from his values at the two ends, so `observe_slant` reproduces
  the measured background radiance at the observer exactly. A table of K
  by direction and depth shows Duntley's statement (p. 231) that in the
  asymptotic light field K is the same in every direction: near the
  surface it differs by direction by a factor of about two, at depth the
  directions agree within about a tenth.
- **The target** is black, so its inherent contrast against the water
  behind it is -1 and its lighting does not enter; `kd` is still required
  and is given as 0, with a comment saying it cannot matter here. The
  contrast left at the observer is `Observation.contrast` against the
  water's own radiance at the target's depth (Duntley's eq. 15).
- **The water.** `Scene` needs a and b; only c = a + b enters a black
  target's contrast and the path. Tyler gives c (0.396 1/m at the
  surface, p. 8) and no split, so the example passes a = c and b = 0 and
  says that the split is not used. One wavelength, 488 nm, the middle of
  Tyler's band (430-546 nm); the band is broad and the example says so.
- **A yardstick.** The distance at which the contrast falls to 2 percent
  of its start, from Duntley's eq. (16) with K at the observer held
  constant, beside the horizontal 3.91 / c. A yardstick, not a claim about
  what an eye or a camera can see.
- **The misprint**, in one line: Duntley's eq. (12) as printed would make
  the open water, looked at upward over 12.3 m, read a stated factor away
  from Tyler's measured value, and the corrected form reads it exactly.

Tyler's tables at 4.24 to 29.0 m carry suspect cells in the sun's
direction, and loading them warns; the example catches those warnings,
reports them, and uses none of those cells.

**Checks.** The quoted figures in `examples/README.md` are recomputed;
the background radiance at the observer equals Tyler's to 1e-12; the
horizontal line gives exp(-c r); looking up the contrast exceeds the
horizontal's, looking down it falls short, at both distances.

**Version.** Part of 1.10.1, with section 77's example; nothing in the
API.

**Differences from the plan, noted after the example was written.** The
plan expected Tyler's K to agree across directions "within about a
tenth" at depth. From 16.6 to 53.7 m it agrees within 12 percent; in the
deepest interval, 53.7 to 66.1 m, the directions part again by 22
percent, and the example says so rather than choosing the interval that
agrees. The first draft of part 4 wrote the corrected eq. (12) with a
sign wrong inside the bracket and read 1452 for Tyler's 1380; caught by
the plan's own check that the corrected form gives the measurement, and
fixed before anything was committed. The tilted lines reach the same
target depths at 16.1 to 32.4 m.

## 79. The ocean colour example, part 7: the reflectance by geometry, and Raman scattering

Two relations added since `ocean_colour_and_secchi.py` was written are
used by no example: `lee2011_rrs` (section 73), the reflectance with
water and particles apart at the seven geometries Lee et al. (2011)
print, and `lee2013_raman_correction` (section 71). The user chose
(2026-11-12) to add them to that example as a seventh part, in the same
release as sections 77 and 78.

**Part 7.** For IB, II, III and 1C, with Solonenko and Mobley's a and b
and the particles' backscatter ratio of Hydrolight's own phase function
(0.0183), as in parts 1 and 2:

- **By geometry.** At the six MODIS bands of Lee et al.'s (2013) Table 2
  (412 to 667 nm; a and b interpolated linearly from Solonenko and
  Mobley's 25 nm grid, as the package does), Rrs by Lee et al. (2011) at
  each printed geometry, against the nadir one, and the nadir one against
  Gordon et al.'s (1988) reflectance taken above the surface as part 2
  takes it. The prototype finds the off-nadir geometries up to about 9
  percent above nadir, and nadir up to about 21 percent away from Gordon
  et al.'s.
- **Raman.** Lee et al.'s (2013) RF on the same reflectance. RF is
  defined on a measured reflectance, which contains Raman scattering;
  these are elastic, so the example presents RF as the size of the share
  a measured spectrum would carry, not as a correction of these. The
  prototype finds 2 to 11 percent, largest at 667 nm in IB.
- **The Secchi depth**, by Lee et al. (2015) on part 2's grid, from Lee
  et al.'s (2011) nadir reflectance against Gordon et al.'s, with part
  1's Kd: how much the choice of reflectance model moves it.

**Checks.** The figures quoted in `examples/README.md` for part 7 are
recomputed; the example still runs with `ProvenanceWarning` as an error
outside what it reports; and the nadir reflectance at one band is
written out from Table 2's coefficients.

**Version.** Part of 1.10.1, with sections 77 and 78.

**Differences from the plan, noted after the part was written.** The
plan calls RF a "share"; Lee et al.'s (2013) RF is the Raman part
relative to the elastic part, Rrs_T = Rrs (1 + RF), and the example and
the README say so. Everything else is as planned: off nadir up to 9
percent above nadir, nadir up to 21 percent from Gordon et al., RF 2 to
11 percent, and the Secchi depth moving by at most 2.4 percent.

**Changed after the first full run of the tests.** A test that every
warning the example raises is one it reports failed: `lee2011_rrs` warns
that Jerlov III, with Solonenko and Mobley's a and b, has bb/(a + bb)
above 0.37 at 412, 443 and 488 nm (and at 425-500 nm on part 2's grid),
outside the range Lee et al. fitted to. The plan's "up to about 9" and
"up to about 21 percent" come partly from those bands. The example now
says which bands lie outside, gives the figures within the range (8 and
14 percent) and with the rest (9 and 21), notes that III's Secchi depth
by Lee et al. (2011) rests partly on them, and reports the warning; the
test accepts that warning only when the example reports bands outside.

## 80. A slanted line that the inputs cannot describe, and a source distribution that carries what its tests read (1.10.2)

A review of the whole package at 1.10.1, asked for by the user on
2026-11-12, found two defects. This section is the plan, committed before
the code.

**1. `Scene.observe_slant` returns a negative path radiance.** Section 75
writes the path radiance as

    veiling = Nw * (1 - exp(-c r - K (zt - z)))

and refuses a negative `Nw` and a negative `K`, but not the combination
that makes the bracket negative: looking up (`zt < z`) with
`K (z - zt) > c r`. Jerlov IB from Solonenko and Mobley has c of about
0.09 1/m; straight up over 5 m with K = 0.15 1/m the call returns a
veiling of -0.34 Nw and a `veiling_fraction` of 1.6, with no warning.
Section 75 did not consider the case.

The inputs then contradict each other, and that can be said from the
formula alone. `K` says the water's radiance along the line at the
target's depth is `Nw exp(K (z - zt))`. A target that is that water,
seen through `exp(-c r)`, must read as `Nw` at the observer (the check
section 75 rests on, Duntley's eq. 9); with `K (z - zt) > c r` its
attenuated radiance alone already exceeds `Nw`, and the path would have
to remove light to make up the difference. No path radiance does that.
Either K is too large for this water or c too small.

- **The change.** `observe_slant` raises `ValueError` where
  `c r + K (zt - z)` is negative at any wavelength, naming the first
  wavelengths, as a negative coefficient is refused (section 60). Zero is
  allowed: the path then adds nothing. NaN in c or K, a gap, passes and
  gives NaN as before. Because `distance_m` may fall short of the
  difference of the depths by a part in 1e12 (section 75's tolerance on
  the geometry), the test is against `-1e-9 c r`, not against zero.
- **Not a warning.** A negative radiance is not a doubtful value; it is
  not a radiance. The package refuses a negative Kd and a negative c for
  the same reason.
- **Compatibility.** A call that returned a negative radiance now
  raises. Section 61 promises the exceptions of calls that worked; this
  one returned something that cannot be, as the calls section 60 closed
  did, and the CHANGELOG says so under Fixed. No call whose result was
  not negative changes, bit for bit: the horizontal case and the tests of
  section 75 are run unchanged.
- **Checks.** The example above is refused; K (z - zt) = c r exactly is
  accepted and gives a veiling of 0; looking down is never refused for
  it; one wavelength over the limit among several is named; NaN passes;
  `examples/looking_up_and_down.py` and the README's call still run.

**2. The source distribution cannot run its own tests.** The sdist on
PyPI holds `tests/*.py`, which setuptools adds by itself, but not
`tests/data/`, so `test_qaa.py`, `test_raman.py` and
`test_pure_water_table.py` fail there (2 failed, 12 errors, unpacking
1.10.1's sdist). It also lacks `DATA.md` and `DECISIONS.md`, which the
package's own warnings and docstrings send the reader to, the CHANGELOG,
`tools/` (the record of how each table was made), `examples/` and the
rest of what the tests read once they find a `pyproject.toml` beside
them and take the directory for a source tree. `publish.yml` tests the
wheel with the repository's tests, so nothing noticed. Whoever packages
from the sdist, or reads it as the archived source, gets less than the
repository and a failing suite.

- **The change.** A `MANIFEST.in` that puts every tracked file in the
  sdist: the top-level documents, `.zenodo.json`, `.github/`, `docs/`,
  `examples/`, `tests/` with its data, `tools/`, and `sources/README.md`.
  The wheel does not change: it is built from `jerlov/` and its tables
  alone, and the build is checked for that.
- **The guard.** `publish.yml` gains a step, before anything is
  uploaded, that fails if a file `git ls-files` names is missing from
  the sdist. A test keeps the step in the workflow, as one does for the
  wheel's tables. Building an sdist inside the test suite needs the
  network and a build backend, so the suite does not do it.
- **Checks, by hand before the release.** The sdist built from this
  tree holds every tracked file; unpacked, with that tree on the path,
  its whole test suite passes; the wheel's file list is the same as
  1.10.1's.

**Version.** 1.10.2: two fixes, no new name, no shipped value changed.
The other findings of the review are recorded outside the repository for
later versions.

**Differences from the plan, noted after the code was written.** Inside
the tolerance the bracket `1 - exp(-c r - K (zt - z))` can still be a
rounding error below zero (about -4e-13 with K = c and the rise a few
parts in 1e12 over the distance), so it is taken as zero there:
`max(bracket, 0)`. A bracket that is not negative, or is NaN, is
unchanged. The publish step counts tracked files against the sdist's
members with the top directory removed; the sdist also holds
`setup.cfg` and `jerlov.egg-info/`, which setuptools writes.

## 81. The rest of the review of 1.10.1: documents, results that copy and compare, inputs that cannot be (1.10.3)

Section 80 fixed the two defects of the review and left thirteen findings.
The user asked on 2026-11-13 for all of them, as 1.10.3. This is the
plan, committed before the code. No shipped value changes, and no name is
added or removed.

**Documents (no behaviour changes).**

- DATA.md's table of files lacks `gregg1990_table1.csv`, added in 1.10.0;
  the test only looked for the name anywhere in the file. The row goes in,
  and the test becomes: every shipped table has a row, with the number of
  rows it has.
- DATA.md's table of statuses lacks nine values the shipped tables use:
  `transcribed`, `identity`, `second_highest`, `undeclared`, `included`,
  `excluded_sparse`, `not_a_water_type`, `other_definition` and
  `above_axis`. Each gets a row saying what its build script means by it,
  and a test keeps every status of every shipped table in that table.
  These are statuses of rows that are not spectra a `Water` carries, so
  `_data.STATUSES`, what a caller's own flags may be, does not change.
- The README never mentions seven functions of 1.4.0 to 1.8.0:
  `pure_water_absorption_table`, `lee2013_raman_correction`,
  `bricaud1995_aph`, `morel2001_bbp`, `lee2011_rrs`, `gordon1989_d0` and
  `gordon1989_kd`. They go into its two sections of entry points. Its
  example for the quasi-analytical algorithm uses the name `bbw` for a
  number and then for an array; the array gets its own name. A test checks
  that every `jerlov.<name>` the README writes exists. It does not run the
  README's code, whose inputs are the reader's.
- Docstrings that later versions left behind: `Scene`'s `depth_m` ("not
  used", but `observe_slant` uses it), `Observation.veiling` and
  `contrast` (horizontal only), the head of `ocean_colour.py` ("four
  relations", "the inverse is not here"), and the `pure_water` of both
  QAA functions, which do not name `pure_water_absorption_table`.
  `descend` gains the `KeyError` it raises when `source` lacks a type the
  profile passes through.
- The README says every example ends with its assumptions.
  `sources_disagree.py` does not; it gets the closing list the others
  have. `.gitignore` names `.DS_Store` twice. The Zenodo description joins
  its list of defects with two "and"s.

**Results that compare and copy.**

- Five result types are dataclasses with the generated `==`:
  `Backscattering`, `AttenuationCoefficients`, `QAAResult`,
  `RamanCorrection` and `SurfaceIrradiance`. Two equal results made
  separately raise NumPy's "truth value of an array is ambiguous", and
  `hash` fails on an array. The other result types switch `==` off, but
  a `Backscattering` of numbers, or a `SurfaceIrradiance` at one
  wavelength, compares by value today, and switching it off would turn
  that `True` into `False`. So these five compare field by field with
  `numpy.array_equal`, NaN equal to NaN, and hash to match: what worked
  keeps its answer, and what raised gets one. `QAAResult` and
  `RamanCorrection` get a short `repr`; the generated one prints every
  array.
- `gregg1990_irradiance`, `qaa_v6` and `qaa_ioccg2006` return the
  caller's own wavelength array, against the rule that what is received
  is copied; they copy. `Observation` and `AttenuationCoefficients` hold
  the `Scene`'s wavelength array itself; they get copies, and the
  `Scene`'s own is made read-only, since c was evaluated on it once and a
  change would leave the two out of step. `Scene.downwelling` stays
  writable: nothing is derived from it ahead of time.
- `ParProfile` cannot be pickled, so cannot go to another process: its
  optical depth is a function defined inside `par_profile`. The functions
  become small classes holding the same arrays. Every number must come
  out bit for bit as before.

**Inputs that cannot be.** The package's rule is that NaN marks a gap and
infinity is refused. These did not follow it, or took something else no
measurement can be. Each now raises `ValueError`:

- `Water`: an infinite a, b, Kd or uncertainty. (A negative one still
  warns and is kept, section 60: a corrected measurement can be slightly
  negative; none is infinite.)
- `Scene`, `Scene.at_depth`, `veiling_radiance_estimate`: an infinite
  downwelling irradiance. `observe`, `observe_slant`,
  `attenuation_coefficients`: an infinite veiling or water radiance.
- `Observation.contrast`: a background that is negative, infinite, or of
  a shape that is neither a number nor the wavelengths'.
- `kd_spectrum`: an infinite or negative Kd. A Kd below pure sea water's
  still only warns, as Jerlov's own type I is.
- `b_from_c`: an infinite c, and a `bw` or `cw` that is infinite or
  negative.
- `bb_from_vsf`: an infinite beta. `pure_water_vsf`: an angle that is NaN,
  infinite or outside 0 to 180 degrees.
- `xyz_to_srgb`, `integrate_response`: infinity in the XYZ, the spectrum
  or the response. NaN in a spectrum still gives NaN, a gap, and the
  docstrings of `integrate_response` and `spectrum_to_srgb` say so.

As in sections 60 and 80, a call that returned infinity, NaN from
infinity, or a negative radiance now raises; no call with finite,
possible inputs changes.

**Exceptions that say what was wrong.**

- `gregg1990_irradiance` raises `TypeError` both when neither of
  `visibility_km` and `aerosol_optical_thickness_550` is given and when
  both are. The package's pattern (sections 61 and 69) is
  `MissingQuantityError` for the first and `ValueError` for the second,
  and it follows it now. Section 69 already holds that a different
  exception from a call that failed anyway is not a breaking change.
- A number given as text reached `numpy.isfinite` and raised its
  `TypeError` in `gregg1990_irradiance`, the chlorophyll of the three
  case 1 functions, and `visual_pigment_template`'s `lambda_max`; these
  raise the `ValueError` the same functions raise for any other bad
  value. `tyler1958_radiance("abc")` raises the `KeyError` of an unknown
  depth. `ScatteringFunction.vsf_at` with a 2-D array of angles raised
  "truth value of an array is ambiguous"; it says a number or a 1-D array
  is wanted, as `Water` does.

**Packaging.** Python 3.14 joins the CI matrix and the classifiers, which
a test keeps equal; the suite passes on 3.14.6 with NumPy 2.5.

**Tidying.** `Scene.observe` and `observe_slant` check the target with the
same helper; `lee2013_raman_correction` and the QAA functions check
wavelengths, Rrs and bands with the same helpers. Messages and results do
not change.

**Checks.** A test for each refusal and each exception above; the two
DATA.md tables; the README's names; equality, hashing and `repr` of the
five types; copies not shared; a `ParProfile` pickled and read back gives
the same `par`, depths, bounds and spectrum; every example's output
compared with 1.10.2's, expected identical apart from the banner and the
new closing list of `sources_disagree.py`.

**Version.** 1.10.3. The user chose a patch version for it; the CHANGELOG
lists every call that now raises under Fixed.

**Differences from the plan, noted after the code was written.**

- `Scene.at_depth` also refuses a negative surface irradiance itself.
  It used to pass it on, and `Scene` refused the product; the exception
  is the same `ValueError`, raised one step sooner with the check for
  infinity.
- The README test checks more than that each `jerlov.<name>` exists: the
  name must be in `jerlov.__all__`, and the seven functions must be
  among them.
- A test not in the plan holds every example to having its section of
  assumptions, under one of the four headings the examples use, since
  the README's sentence about them had been untrue with nothing to
  notice.
- The equality treats two fields as the same when both are NaN, for a
  number as for an array, so that a result is never unequal to a result
  made the same way; none of the five types has a field that is a single
  NaN today.
- The output of the twenty examples that run in under a few minutes was
  compared with 1.10.2's line by line: the banner's version differs in
  each, and `sources_disagree.py` has its new closing list. Nothing else.

## 82. Coefficients for renderers: RGB, a Henyey-Greenstein g, and spectra (1.11.0): the plan

People who render water, for film, games or simulation, need an
absorption and a scattering coefficient and a phase function, and
commonly pick them by eye (NEXT_STEPS section 0, item 6). The package
holds sourced values for all three. This section hands them over in the
forms renderers take, without solving the radiative transfer equation
(sections 12 and 38): the renderer does the light, the package says
where the numbers came from and how far a renderer's simplification
moves them. The user chose the design below on 2026-11-14.

**Three forms, in a new module `jerlov/rendering.py`.**

1. `rgb_attenuation(water, /, *, colour_space, illuminant,
   distance_range_m)`, returning an `RgbAttenuation`: one extinction,
   absorption and scattering coefficient per channel of a linear RGB
   space, for renderers that work in RGB (Blender, Arnold, RenderMan,
   Unreal, Unity, Mitsuba and pbrt in their RGB modes).
2. `henyey_greenstein_fit(scattering, /, *, method)`, returning a
   `HenyeyGreensteinFit`: the asymmetry parameter g of a
   Henyey-Greenstein phase function for one of Petzold's stations, the
   only phase function most renderers offer.
3. `spectral_coefficients(water, /, *, range_nm)`, returning a
   `SpectralCoefficients`: a, b and c at the water's own wavelengths, for
   spectral renderers (Mitsuba 3, pbrt-v4), with no RGB step to lose.

Each result has `as_dict()`, plain lists, strings and numbers ready for
`json.dump`, carrying units, the source's citation and what was assumed.
No file format of any one renderer is written by the package; the
example does that. New public names: these three functions, their three
result types and `RGB_COLOUR_SPACES`, 108 in all.

**Why RGB is not a sampling of the spectrum.** A renderer in RGB
attenuates each channel as exp(-sigma_k r). The light that has crossed r
metres of water has the spectrum S(lambda) exp(-c(lambda) r), and its
channel k in a linear RGB space is R_k(r) = M_k . XYZ[S exp(-c r)], with
M the space's XYZ-to-RGB matrix. The channel's transmittance T_k(r) =
R_k(r) / R_k(0) is not one exponential, because the spectrum inside a
channel is attenuated unevenly, and it depends on the light S that
enters the water. So:

- **The illuminant has no default.** It is passed as `(wavelengths,
  power)`, as `jerlov.d65()` returns it; above the sea D65 is one
  choice, `gregg1990_irradiance` another, and under water the light at
  that depth. Its RGB in the chosen space is returned, so the light in
  the scene can be set to match.
- **The distances have no default.** sigma_k is fitted over the caller's
  `(near, far)` in metres, by least squares in ln T_k at 201 evenly
  spaced distances, through T = 1 at r = 0 as the renderer's model is.
  The result carries the fitted range and the largest relative error
  |exp(-sigma_k r) / T_k(r) - 1| over it, per channel.
- **The colour space has no default.** One of `RGB_COLOUR_SPACES`:
  `"linear_srgb"` (IEC 61966-2-1, the primaries the package already
  has), `"acescg"` (the AP1 primaries and the ACES white, x = 0.32168, y
  = 0.33767, from the Academy's ACEScg specification, read on
  docs.acescentral.com), `"rec2020"` (Rec. ITU-R BT.2020-2 (10/2015),
  Table 3, p. 3). The matrix is derived from the primaries, as for sRGB.
  No chromatic adaptation is made: a ratio within one channel needs
  none, and the illuminant's own RGB tells the caller what white it is.
- **A channel that turns negative is refused.** Clear water leaves a
  blue-green light that lies outside the sRGB gamut after a few metres,
  and the red channel, whose matching function is negative in the
  blue-green, then goes below zero (the user chose to refuse,
  2026-11-14). The `ValueError` gives the channel and the largest
  distance at which every channel is still positive; a narrower range
  or a wider space is the caller's remedy. A first look, with D65,
  Williamson & Hollins IB, linear sRGB: the red channel's T reaches
  -0.013 within 20 m. ACEScg and Rec. 2020 keep it positive there.
- **Absorption and scattering.** sigma_t is fitted from c, sigma_a from
  a in the same way, and sigma_s = sigma_t - sigma_a, so that the three
  add up as a renderer assumes; the albedo is sigma_s / sigma_t. A
  negative sigma_s is refused. **Rejected:** fitting b on its own, since
  sigma_a + sigma_s would then not equal sigma_t.
- **Everything else is as elsewhere.** The spectra are integrated on 1
  nm steps where the water, the illuminant and the CIE 1931 observer
  overlap, through `integrate_response`, so a water that does not span
  the observer warns with `CoverageWarning`; flagged values warn with
  `ProvenanceWarning` through `Water.a` and `Water.c`; a gap (NaN) in a
  or c inside that overlap is refused, since no colour can be formed
  across it; an illuminant with no power in a channel is refused.

A first look at how far one exponential is from the truth, D65, 0.5 to
10 m: in ACEScg the red channel is off by up to 8 or 9 percent in every
Williamson & Hollins type, green and blue by 0.1 to 8 percent. The
result says so per channel rather than the docstring in general.

**The Henyey-Greenstein g.** HG is the phase function almost every
renderer has (Mitsuba's `hg`, pbrt-v4's homogeneous medium's `g`,
Blender's anisotropy), and it fits ocean water badly: at small angles
it falls short of Petzold's measurements by a factor of up to about
140 when g matches the mean cosine, 310 when it matches B/S. Which property it is made to match is a choice, so `method` has no
default (the user's choice):

- `"backscatter_ratio"`: g such that HG scatters the station's B/S, as
  printed, beyond 90 degrees: B(g) = (1 - g) / (2 g) [(1 + g) /
  sqrt(1 + g^2) - 1], solved by bisection. A first look gives g = 0.822
  (AUTEC 8) to 0.941 (HAOCE 11).
- `"mean_cosine"`: g equal to the station's mean cosine, 2 pi times the
  integral of the phase function times cos(theta) sin(theta), the vsf
  interpolated in log-log as `vsf_at` does, plus the share of s below
  0.1 degree at a cosine of 1. That share, 3.4 to 14.5 percent of s, is
  the report's power-law extension at every station and enters the mean
  cosine at full weight, so this method warns with `ProvenanceWarning`.
  A first look gives 0.877 to 0.954, and an HG backscattering 19 to 35
  percent below the measured B/S.

The result carries the station, 530 nm, the method, g, the HG's B/S
beside the measured one, and ln(p_HG / p) at the report's 55 angles,
the fit's error where it is. `ScatteringFunction.mean_cosine()` is added
for the second method, warning in the same way. Petzold measured one
band in the green, and nothing here gives g a wavelength dependence;
the renderer will apply one g to all wavelengths, and the docstring
says so. The vsf includes pure water, as Petzold measured it.

**The spectra.** `spectral_coefficients` returns a, b and c at the
water's own wavelengths inside `range_nm` (required, inside the water's
range): no resampling, so a spectral renderer interpolates them as it
does its own spectra, and nothing is interpolated here first. Gaps stay
NaN (`None` in `as_dict()`), each value carries its status, flagged
values warn when the result is made, and a water without a or b raises
`MissingQuantityError`.

**The example.** `examples/rendering_export.py`, the twenty-second, for
people who render water: the RGB coefficients of two water types in the
three spaces with their errors, and the refusal in linear sRGB caught
and shown; g by both methods for the eight stations; and the same water
written as a Mitsuba 3 scene's medium (RGB and spectral) and as a
pbrt-v4 `MakeNamedMedium`, printed, not rendered. The file formats are
taken from the two renderers' own documentation; whether the Mitsuba
text loads is checked by hand in a scratchpad environment with Mitsuba
installed, not in CI, which installs NumPy only. A renderer's scene
unit is not a metre unless the caller makes it one; both formats have a
scale for that, and the example says so. Blender's Principled Volume is
included only if its mapping from colours and density to coefficients
can be stated from Blender's own manual or source; otherwise it is left
out and the example says why.

**Checks.** The three matrices against the primaries and whites they
come from (each primary maps to its own unit vector, the white to
(1, 1, 1)), and linear sRGB against the matrix the package already
has. `rgb_attenuation` against a water whose c does not vary with
wavelength (every channel then gives exactly c, with no error) and
against a direct sum over the spectrum for one case; the refusal at
the distance it reports; the coefficients adding up. HG: the closed
form of B(g) against numerical integration; the backscatter method
reproducing each station's B/S; the mean cosine's integral of p sin
reproducing the report's own s within 1 percent, so that the
interpolation is the report's; g = 0 and the warnings. Spectra: values
identical to `Water.a`, `b` and `c` at the same wavelengths;
`as_dict()` through `json.dumps` with `allow_nan=False`. Every input
for NaN, infinity, negatives, the wrong shape and a missing argument.

**Version.** 1.11.0: new public names, nothing changed.

**Differences from the plan, noted after the code was written.**

- The plan's first look at the mean cosine integrated Petzold's samples
  by the trapezoid rule in angle. The package integrates the vsf as a
  power law between the printed angles, as `vsf_at` interpolates it,
  which gives back the printed s within 0.24 percent at every station.
  The mean cosines are then 0.869 to 0.945, not 0.877 to 0.954, and the
  HG matched to them backscatters 5 to 30 percent less than the station,
  not 19 to 35. At 0.1 degree HG falls 58 to 164 times short when matched
  to the mean cosine and 68 to 310 times when matched to B/S.
- **Changed after the first run of the tests.** The refusal of a channel
  that turns negative gave the distance through whichever of c and a
  failed first in the fitted range. For IB in linear sRGB the light
  through a alone turns negative sooner (8.62 m) than through c (9.11 m),
  so a range ending at 9 m, inside the distance reported, was refused
  too. The message now gives the distance up to which every channel
  stays positive through both.
- Mitsuba 3.9.1's spectral variants sample 360 to 830 nm and render NaN
  where a medium's spectrum stops short of either end (DATA.md section
  36), found when the spectral medium was loaded and rendered by hand.
  Williamson & Hollins stop at 800 nm, so the example holds their 800 nm
  values to 830 nm, says so in the files and in its list of
  assumptions, and gives pbrt-v4 the same spectra. The package still
  returns only what the source has.
- The example writes pbrt-v4 a spectral medium only: pbrt-v4 renders
  spectrally and turns RGB into a spectrum, and its RGB spaces do not
  include ACEScg. Mitsuba's RGB variants take linear sRGB, by its
  documentation, so its RGB medium uses that space; its documentation
  asks for RGB values in [0, 1], so sigma_t is divided by its largest
  value, which goes in `scale`.
- Blender is included. Its manual gives the Volume Absorption and Volume
  Scatter nodes as absorption = (1 - Color) x Density and scattering =
  Color x Density, and its working space as Linear Rec. 709 by default
  with Linear Rec. 2020 and ACEScg available; Cycles' source does the
  same. The example gives the node values for ACEScg, and a test turns
  them back into the fitted coefficients. Blender's newer Volume
  Coefficients node, which takes the coefficients themselves, is not
  used, since which release brought it was not established.
- `illuminant_rgb` is scaled so that the illuminant's luminance Y is 1.
  A water or a scattering function of the wrong type raises `TypeError`.
- Found on reading the code back, before the first full run: a channel
  whose matching function is negative where the water absorbs grows as
  the light crosses it, and the fit then gives a negative coefficient a
  renderer cannot take. A sigma_t or sigma_a that is not positive is
  refused, which the plan did not list; a test builds such a water.

## 83. Three examples for people who render water, and the renderers run (1.11.1): the plan

Section 82 gave renderers their coefficients and said what each
simplification costs in the package's own terms: a relative error in a
transmittance, ln(p_HG / p) at Petzold's angles. People who render water
judge in other terms: a colour that looks wrong, a table a game reads
every frame, a glow around the sun. The user asked for examples that use
the new functions (2026-11-14) and chose three, one per reader. They
need nothing beyond NumPy and run in CI like the others. 1.11.1 adds no
public name.

**1. `rgb_versus_spectral.py`, for people who make images.** A few
reflectances seen through water, rendered twice: spectrally, the light
S rho(lambda) exp(-c(lambda) r) taken to XYZ, and as a renderer in RGB
does it, RGB(S rho) exp(-sigma_t r) with `rgb_attenuation`'s
coefficients, taken back to XYZ through the space's matrix. The
difference as a CIE 1976 colour difference, Delta E*ab, for three water
types, the three spaces and distances inside and beyond the fitted
range. Two references are shown, since both are how images are looked
at: one white, the illuminant itself, so that far things are dark and
their difference small; and the white patch at the same distance,
rendered spectrally, as a camera that sets exposure and white balance on
the scene would. The reflectances are invented smooth curves, a grey,
a white and three broad bands, and the example says so; no measured
chart is shipped and none is brought in. A first look: up to Delta E*ab
of about 8 in linear sRGB and 5 in ACEScg at 5 m, with the illuminant as
white. CIEDE2000 is not used: Delta E*ab is a few lines anyone can check
against the CIE's definition, and the point is the size of the
difference between two renderings, not a threshold of perception, which
the example does not claim. It can write the two renderings side by side
as a small PPM image with `--write DIR`, by the standard library.

**2. `water_lookup_tables.py`, for games and real-time rendering.**
Tables of the kind a shader samples each frame (NEXT_STEPS section 0,
item 6 (c), as an example first, before deciding whether it belongs in
the package): for one water type, by depth and by distance along a
horizontal line, the transmittance per RGB channel, from the spectrum as
section 82 defines it, and the path radiance per channel, B_inf (1 -
exp(-c r)) from `Scene.at_depth` and `veiling_radiance_estimate`, taken
to RGB. Every choice that fills them is stated at the top and has no
default in the package: the surface light, the Kd that carries it down,
the particles' backscattering ratio for B_inf, the colour space, the
grid. The tables are written as CSV, and as PPM images, with `--write
DIR`. The example says what the tables leave out: a slanted line, the
sun's direction, anything but single scattering for B_inf, which the
package calls an order of magnitude.

**3. `phase_function_choice.py`, for simulation.** What choosing HG, and
choosing how to fit it, does to the light a renderer scatters, at
Petzold's eight stations. With the sun in the water at a stated zenith
angle, the single-scattered radiance along a line of sight is
proportional to the phase function at the scattering angle between the
sun's direction and the line of sight; the ratio HG / measured is shown
from looking towards the sun to looking away, for both ways of choosing
g. And the share of the scattered light within 1, 10 and 90 degrees of
the forward direction, measured and HG: the glow around the sun. The
measured shares integrate the vsf between Petzold's angles as a power
law, as section 82 did, in the example's own code from the public
`angles_deg`, `vsf` and `fraction_below_0_1_deg`, and count the report's
extension below 0.1 degree, which the example says.

**The renderers, run.** Section 82's example wrote a pbrt-v4 medium and
Blender's node values without running either. Both are now run by hand
outside CI, in the scratchpad, and DATA.md section 36 says how:

- Blender 5.3.0 (the `bpy` module from PyPI), Cycles on the CPU: a slab
  of water 5 m thick between an orthographic camera and an emitting
  plane hidden from the volume's scattering, absorption alone and
  scattering alone, with volume bounces off. The transmittance read from
  the EXR is to agree with exp(-sigma r) per channel, in ACEScg and in
  Linear Rec. 709. A first run: absorption agrees to 7 digits, and
  scattering within 0.2 percent at 1024 samples, the Monte Carlo's
  noise; but only with Cycles' denoising off, which by default changed
  the values by about 5 percent and made a white emitter read 1.13.
- pbrt-v4, built from its repository on the CPU: the example's spectral
  medium in a slab, the same arrangement, the transmittance compared
  with the spectrum's own.

`rendering_export.py` then says what was run instead of "not run", and
its Blender part mentions the Volume Coefficients node, which Blender
5.3.0 has.

**Checks.** Every number the three examples print is computed, and the
ones the README quotes are recomputed by `test_quoted_figures.py`; each
example's warnings are caught by type and reported, and a test holds
each to reporting only those. For the first, a grey water (c the same
at every wavelength) gives a Delta E of zero at every distance, which
tests the two renderings against each other. For the second, the table
at depth 0 and distance 0 is a transmittance of 1, and the RGB
transmittance at the fitted distances agrees with `rgb_attenuation`'s
own data. For the third, the measured shares reach 1 at 180 degrees to
within the 0.24 percent of section 82, and HG's shares agree with its
closed form.

**Version.** 1.11.1: examples and documents, no change to the package's
code or values.

**Differences from the plan, noted after the code was written.**

- The second example's check against `rgb_attenuation` could not be the
  plan's: the function does not return its transmittances, and its fit
  is made at 201 distances, the table's at 30. The test holds the
  table's transmittance to within the largest error the fit reports
  over the same range, and to 1 at distance 0.
- The second example takes Kd from Jerlov (1976), since Williamson &
  Hollins give none, so its colours are formed over 360-715 nm, where
  Jerlov's Kd ends; beyond lies 0.05 percent of the observer's x-bar.
- The third example's prose originally said the blur of what is seen
  through water lives in the forward cone, and that multiple scattering
  hides part of what a phase function gets wrong; neither is computed
  here, and both were taken out before the commit.
- pbrt-v4 needed its Wayland support turned off to build in the
  container, and its camera medium named before the camera; Blender's
  working space is set by an operator, its property being read-only.

## 84. The RGB transmittance as a table (1.12.0): the plan

Section 82 fitted one exponential per channel and reported how far it is
from the channel's true transmittance. A renderer that reads a table
instead, as games and real-time renderers do (NEXT_STEPS section 0,
item 6 (c)), needs that true transmittance itself, at distances it
chooses, with nothing fitted. `examples/water_lookup_tables.py` (section
83) computed it in the example's own code; the user chose on 2026-11-14
to bring the transmittance into the package and to leave the path
radiance in the example, since the package calls its single-scattering
estimate an order of magnitude and a table would make it look like a
value.

**The function.** `rgb_transmittance(water, distances_m, /, *,
colour_space, illuminant)`, returning an `RgbTransmittance`: for each
distance r, T_k(r) = R_k(S exp(-c r)) / R_k(S), the channel's
transmittance exactly as section 82 defines it, through c. The same
colour spaces, the same illuminant with no default, the same 1 nm grid
where the water, the illuminant and the observer overlap, the same
warnings (`ProvenanceWarning` from the water, `CoverageWarning` from the
observer's coverage).

- `distances_m`: a number or a 1-D array of them, finite and not
  negative, in any order; the result keeps its shape, with a last axis of
  three channels.
- A channel at zero or below at any requested distance is refused, as in
  `rgb_attenuation`, with the distance up to which every channel stays
  positive: a table with a negative transmittance is not one a renderer
  can use, and clipping it would hide that the colour left the space.
- A gap (NaN) in c where the colour is formed, and an illuminant with no
  power in a channel, are refused as there.
- The result carries the colour space, the distances, the
  transmittances, the illuminant's RGB (Y = 1), the wavelength range,
  the water and its source, and `as_dict()` for `json.dump`.
- Depth is not an argument. The light at a depth is the caller's
  illuminant: `Scene.at_depth(...).downwelling`, or a measurement, so
  that how the light got down (which Kd, constant or not) stays the
  caller's choice, as it is for `Scene`.

**Shared code.** `rgb_attenuation` and `rgb_transmittance` compute the
transmittance in one private helper, so the two cannot drift; every
result of `rgb_attenuation` is to stay bit for bit as in 1.11.1, which a
test checks against values recorded before the change.

**The example.** `water_lookup_tables.py` takes its transmittance from
`rgb_transmittance` instead of its own integration; its printed numbers
are to stay as they are, and its path radiance stays its own, with its
caveats.

**Checks.** A grey water gives exp(-c r) in every channel exactly. At
the 201 distances `rgb_attenuation` fits over, the fitted exponential
departs from `rgb_transmittance` by exactly the error `rgb_attenuation`
reports. T is 1 at r = 0. A refusal at the distance reported, and none
just inside it. The shape of the result for a number, a list and a 2-D
array. Every input for NaN, infinity, negatives and a missing argument.

**Version.** 1.12.0: two public names are added, `rgb_transmittance`
and `RgbTransmittance`, 110 in all.

**Differences from the plan, noted after the code was written.**

- T at r = 0 is 1 to rounding, about 2 x 10^-15, not exactly 1: the
  illuminant's R_k(S) is taken once through `integrate_response`, as
  `rgb_attenuation` takes it, and the table by the same sum done another
  way. Taking R_k(S) the table's way would have moved `rgb_attenuation`'s
  results in their last bits, which the plan ruled out; the test allows
  1 x 10^-13.
- A distance at which a channel is refused is the reach through c alone,
  since only c is evaluated: for IB in linear sRGB 9.11 m, where
  `rgb_attenuation`, which also fits a, reports 8.62 m.
- `water_lookup_tables.py` prints and writes the same numbers as in
  1.11.1, compared line by line and cell by cell.
- **Changed after the first run of the tests, on NumPy 1.22.** The test
  compared `rgb_attenuation`'s results with values recorded under NumPy 2
  bit for bit, and under NumPy 1.22 the last bit of some differed. The
  1.11.1 code and the new code were then run under NumPy 1.22 side by
  side and agreed bit for bit, as they had under NumPy 2: the difference
  is NumPy's own rounding, not this change. The test now allows a
  relative 1 x 10^-14 in the coefficients and the illuminant's RGB, and
  an absolute 1 x 10^-14 in the errors, which are differences from 1.

## 85. Measured reflectances of ten materials, and reference images (1.13.0): the plan

NEXT_STEPS section 0, item 6 (d) asks for reference images: how coloured
surfaces look through each water type, at each depth and distance, for
checking a renderer or a photograph against. Every example so far has
used invented reflectances, `synthetic_underwater_images.py` among them,
which says that real work should use measured ones. This section ships
measured ones. The user chose on 2026-11-14 to use measured materials
rather than invented curves, to leave the classic ColorChecker aside
(its spectra are copyrighted; a request for permission is deferred),
and left the choice of materials to this plan.

**The source.** Kokaly, R. F., Clark, R. N., Swayze, G. A., Livo, K. E.,
Hoefen, T. M., Pearson, N. C., Wise, R. A., Benzel, W. M., Lowers, H. A.,
Driscoll, R. L., and Klein, A. J. (2017), USGS Spectral Library Version 7
Data, U.S. Geological Survey data release, DOI `10.5066/F7RR1WDJ`,
marked CC0 1.0; the report is USGS Data Series 1035, DOI
`10.3133/ds1035`. The use constraints in the release's metadata ask that
modifications be described and the USGS be acknowledged; DATA.md does
both. From `ASCIIdata_splib07a.zip`, the spectra as measured (not
resampled), the ASD spectrometer's records ("ASDFRa AREF"): absolute
reflectance, the reflectance relative to a Spectralon panel times the
panel's own (eq. 1, p. 4), at one channel per nm from 350 to 2500 nm,
with a bandpass of 3.4 to 8.7 nm (FWHM) between 350 and 830.

**The ten.** Chosen to span neutral and hue, from materials found in and
around water, none fluorescent (a fluorescent sample's measured
reflectance includes light the lamp made it emit, which water's light
would not): white PVC (GDS338), black ABS pipe (GDS341), light grey road
concrete (GDS375), red and blue nylon fabric (GDS431, GDS433), green
plastic tarp (GDS339), blue-green HDPE (GDS391), and three artists'
pigments, cadmium orange (GDS786), cadmium yellow (GDS788) and cobalt
violet (GDS803). Shipped from 350 to 830 nm, the CIE observer's range
and a little below, as printed, 4810 values; none is deleted in that
range and all lie between 0 and 1.

**The table.** `jerlov/data/usgs2017_reflectance.csv`, written by
`tools/build_usgs2017.py` from the downloaded zip, which checks each
record's header line names the sample, the wavelengths are the ASD's 1
nm channels, no value is the library's deleted-channel marker, and every
value lies in (0, 1). The sample descriptions the release carries as
HTML (1.3 GB with photographs) are behind a download page this container
cannot use, so DATA.md gives each sample's record line and name as the
ASCII file prints them, and says the descriptions were not read.

**The function.** `usgs2017_reflectance(material)`, returning a
`MeasuredReflectance` (the material's key, the library's record number
and name, the wavelengths and reflectances, the citation);
`USGS2017_MATERIALS` lists the ten keys. Reflectance at another
wavelength is the caller's interpolation, as for any spectrum here; the
values are what the library measured with the ASD's bandpass, which is
recorded. Three public names, 113 in all.

**The example.** `examples/reference_images.py`, the twenty-sixth: the
ten materials as a chart, seen through Jerlov IB, III and 1C at 5 and
15 m, at 1, 3, 5 and 10 m, with the direct light from `Scene.at_depth`
and the path radiance from the package's single-scattering estimate,
every choice stated (the surface light, Kd, the face irradiance ratio,
the backscattering ratio), balanced on the downwelling irradiance at
depth. It prints the sRGB values and, with `--write DIR`, writes them
as CSV (linear and encoded) and the charts as PPM images. It says what
the images are not: a photograph, a validated rendering, or a view of
anything but a horizontal line in uniform water.

**Checks.** The CSV against the zip, value by value, in the build
script; the function's values against the CSV; the ten keys; refusal of
an unknown material. In the example, a chart at distance 0 with no path
radiance reproduces each material's colour under the downwelling light,
and a material's colour moves towards the water's as the distance grows.

**Version.** 1.13.0: three public names and one shipped table.

**Differences from the plan, noted after the code was written.**

- The example takes Kd from Jerlov (1976) for each type, as
  `water_lookup_tables.py` does, so its colours are formed over
  360-715 nm, where that Kd ends. Its face irradiance ratio is 0.3, as in
  `fish_colour_differences.py`, and its backscattering ratio that of the
  Petzold station whose b at 530 nm is nearest each type's (AUTEC 7 for
  IB, HAOCE 5 for III and 1C), all stated in its output.
- The check that a colour moves towards the water's is made against the
  water's own colour, the path radiance at infinite distance balanced the
  same way, at every step outwards. A first version of the test asked
  chroma to fall at every step, and failed: the green tarp in IB gains
  chroma from 0 to 1 m, the water's blue-green adding to its green.
- The three neutral materials are tested to be less saturated under D65
  than every coloured one, not grey within a fixed margin: the concrete
  is a little warm, as light grey road concrete is.

## 86. Input files for two radiative transfer codes, OSOAA and HydroLight (1.14.0): the plan

NEXT_STEPS section 0, item 5: a Jerlov type's a, b and a measured phase
function written in the input formats of the radiative transfer codes
that solve what this package does not (sections 12 and 38). The user
chose on 2026-11-14 the recommended course on four questions: OSOAA and
HydroLight as targets; the pure water each code adds back a required
argument; OSOAA's polarization ratios required arguments; input files
only, the codes' outputs left for later.

**PlanarRad is left out.** Its Python driver, planarradpy (GPL v2,
github.com/marrabld/planarradpy), runs PlanarRad's own executables,
which were distributed from planarrad.com; that domain now redirects to
a parked page, and no other source was found. Files for a program no
one can obtain, and that could not be run, would be untested promises.

**OSOAA** (CS Group and LOA for CNES, GPL v3,
github.com/CNES/RadiativeTransferCode-OSOAA, commit 8e4914f), its User
Manual V2.0 (2025-01-30). With `-HYD.Model 3` the hydrosols are a
user's Mueller matrix (`-HYD.ExtData`, §3.6.3, pp. 80-81) and a user's
depth profile of absorption and scattering (`-HYD.UserProfile`, §3.6.4,
pp. 81-82), from which "pure seawater absorption and scattering
coefficients need to be subtracted" (§3.2.4, p. 37), at the run's single
wavelength. Built here with gfortran
13.3 from its Makefile, and run by hand before this plan:

- Jerlov III at 440 nm, less a pure water of the test's choosing (Pope
  & Fry's a, 0.00635, and Morel's b at 35 PSU, 0.00494): OSOAA's sea
  profile gives a total extinction of 0.4331 per metre and a share of
  scattering of 0.7206. Jerlov III's c and b/c with OSOAA's own pure
  seawater added back (a 0.00635 and b 0.00501629 at 440 nm, from its
  `fic/OSOAA_SEA_MOL_COEFFS_JUNE_2013.txt`) are 0.4331 and 0.7206: OSOAA
  adds its own pure water to the profile, as its manual says.
- The extinction and scattering cross-sections at the head of the
  `-HYD.ExtData` file are not used under `-HYD.Model 3`: two runs that
  differed only in them gave byte-identical radiances and fluxes.

**HydroLight** (Sequoia Scientific; commercial). The "standard format
for ac-9 data", §7.3 of the HydroLight 5.1 Technical Documentation
(Mobley 2012, pp. 55-56, as published with a University of Maine
course): ten header records, a record giving the number of wavelengths
and the wavelengths, then one record per depth of the depth, a at each
wavelength and c at each, ended by the last record repeated with a
negative depth; a and c "with the water ... removed", HydroLight adding
pure water back. HydroLight was not available and was not run; the
files follow the document, and say so. The phase function stays
HydroLight's choice: it uses discretized phase functions made by its
own code, which this package cannot produce.

**The functions**, in a new module, each returning the file's text for
the caller to write:

- `osoaa_user_profile(water, wavelength_nm, /, *, depths_m,
  pure_water)`: OSOAA's five comment lines (the water, its source, the
  wavelength, what was subtracted), then depth, a - a_w and b - b_w.
  `pure_water` is `(a_w, b_w)` at the wavelength, the values OSOAA adds
  back, with no default. The depths start at 0, as OSOAA requires, and
  are fewer than its limit of 500 (`CTE_NZ_MAX_USER_PROFILE`).
- `osoaa_phase_function(scattering, /, *, minus_f12_over_f11,
  f22_over_f11, f33_over_f11)`: the `-HYD.ExtData` file for one of
  Petzold's stations: F11 = vsf / b at Petzold's 55 angles, from 180
  degrees down as the manual's example orders them, and the three
  ratios, which Petzold did not measure, with no default (a number for
  every angle, or 55 values). The two cross-section lines carry the
  station's c and b in 1/m, which `-HYD.Model 3` does not read; the
  comment line says so, and that the file is for that model. The angles
  below 0.169 degree at the clearer stations are the report's extension
  and warn, as `vsf_at` does.
- `hydrolight_ac9_file(water, wavelengths, /, *, depths_m,
  pure_water)`: the standard-format file, with `pure_water` as
  `(a_w, b_w)` on the wavelengths, the values HydroLight adds back, and
  at least two depths, ascending from 0, since HydroLight fits linear
  splines between them.

In each, a value that turns negative after the pure water is subtracted
is refused (`ValueError` naming the wavelength): a code would read it as
a negative absorption or scattering. NaN and infinity are refused, a
water without a or b raises `MissingQuantityError`, and flagged values
warn as they do from `Water`. A Jerlov type does not vary with depth, so
every depth carries the same values; the depths are the caller's, to
match the run. Three public names, 116 in all.

**The example.** `examples/radiative_transfer_inputs.py`, the
twenty-seventh, for people who run OSOAA or HydroLight: Jerlov III's
files at 440 nm for OSOAA, with the pure seawater OSOAA adds back as
the caller would read it from OSOAA's own table, and the HydroLight file
from 400 to 700 nm, with every choice stated; and the OSOAA command line
that uses them. It runs neither code.

**Checks.** Each file parsed back by the rules its document states (the
header counts, the column order, the end marker) and the values
recovered exactly; the subtraction added back gives `Water.a` and `c`;
the refusals; the warnings. The OSOAA runs above are recorded in DATA.md
with the commit, the compiler and the numbers, as a check made by hand
outside CI.

**Version.** 1.14.0: three public names.

**Differences from the plan, noted after the code was written.**

- The module is `jerlov/interop.py`. Passing the water or the
  wavelengths by keyword warns with `FutureWarning`, as every other
  function under `positional_only` does (section 61), rather than
  raising.
- The OSOAA profile's five comment lines are its manual's three column
  descriptions and two comments: the water, its source and the
  wavelength, then the pure water subtracted. The file ends without a
  newline, as the manual asks. Each of `pure_water`'s two values may be
  one number for every wavelength in `hydrolight_ac9_file`.
- The files of the example were run once more in OSOAA, byte for byte:
  its sea profile gives c = 0.4330 per m and b/c = 0.72054, Williamson
  and Hollins's 0.433 and 0.72055. The run before the plan gave 0.4331
  because its profile had Morel's 0.00494 subtracted from b while OSOAA
  added its own 0.00502 back: the very mismatch the required argument
  is for.
- The example's HydroLight file takes off the aw that Williamson and
  Hollins built a on and Morel's bw at 35 PSU, its stated choice, and
  shows the alternative: Pope and Fry's (1997) aw is larger in the red
  and is refused from 650 nm in IB. At 440 nm, taking off Williamson and
  Hollins's aw where OSOAA adds its own would leave a short by 9.6
  percent in IB.

## 87. Reading OSOAA's results (1.15.0): the plan

NEXT_STEPS section 0, item 5, its second half: the outputs of a
radiative transfer code read back, so that what the code made of a
Jerlov type's IOPs can be set beside what the type's own sources
measured. The user chose on 2026-11-15 the recommended course on four
questions: OSOAA's fluxes and both of its standard radiance files; the
values returned as OSOAA prints them, normalized, with no solar
irradiance supplied; one real run kept in `tests/data` and not shipped;
HydroLight's outputs not read.

**HydroLight is left out.** Neither HydroLight nor a file it wrote was
available, and a reader written from a description alone, never given a
real file, would be an untested promise (as PlanarRad was in section
86).

**What OSOAA writes**, from its User Manual V2.0 (2025-01-30) and its
source at commit 8e4914f, checked against the run of section 86:

- `Advanced_outputs/Flux.txt` (§3.5.6, pp. 75-76): five header lines,
  then for each level its number, its altitude (positive in the
  atmosphere, negative in the sea, in m), and the direct, diffuse and
  total downward fluxes, the direct, diffuse and total upward fluxes,
  and their ratio Eu/Ed. The fluxes are "normalized to the solar
  irradiance at TOA": the extraterrestrial irradiance is pi, so the
  direct flux at the top of the atmosphere is pi cos(theta_s) (2.72070
  for the run's sun at 30 degrees; pi cos 30 = 2.72070). The manual gives
  the format as `2X,I4,1X,F14.5,2X,7(2X,E14.6E3)`; the source writes
  F12.5 (`OSOAA_SOS.F`, FORMAT 600). Both are read by splitting on white
  space.
- The surface appears twice: a level at altitude 0 above it and, in the
  sea, two levels printed `-0.00000`, at optical thicknesses 0 and 1e-4
  (`PROFILE_SEA.txt`). The sign of the printed zero tells the sea from
  the air.
- "Direct" is not the unscattered beam. OSOAA always truncates the
  forward peak of the hydrosols' phase function, and counts the light
  so removed as transmitted (§4.2.3, p. 96): in the run, the direct flux
  in the sea falls at 0.144 per m, not at c / cos(theta_w) = 0.467. The
  totals Ed and Eu are not affected; the reader says so and computes Kd
  from the totals only.
- `Standard_outputs/RESLUM_vsZ.txt` and `RESLUM_vsVZA.txt` (§3.5.1,
  pp. 57-64): a header stating the relative azimuth, and the fixed viewing
  zenith angle or depth, then rows of the depth (m, negative) or the
  viewing zenith angle (degrees, signed by the half-plane, §3.5.1), the
  scattering angle, I = pi L / Esun (1/sr), the reflectance pi L / Ed,
  the degree of polarization (percent), the polarized intensity pi
  L_pol / Esun and the polarized reflectance.
- `ListParam.txt` lists the run's parameters; it prints the
  `-HYD.UserProfile` file under the label `-HYD.ExtData` (two lines of
  that label in the run). The package does not read it: the example
  does, for the wavelength and the sun.

**The functions**, each reading the text of one file, as the writers of
section 86 return text:

- `read_osoaa_flux(text, /)` -> `OsoaaFlux`: the levels, the altitudes
  as printed, a mask of the levels in the sea, and the seven columns as
  printed, normalized as OSOAA normalizes them. `OsoaaFlux.kd(upper_m,
  lower_m)`: the mean Kd of the total downward flux between two depths
  (positive, m) inside the sea's levels, ln Ed interpolated linearly
  between levels, the first sea level standing for depth 0; outside the
  levels, refused.
- `read_osoaa_radiance_vs_depth(text, /)` -> `OsoaaRadianceProfile`: the
  relative azimuth and viewing zenith angle of the header, and each row's
  depth (positive, m), scattering angle, normalized radiance,
  reflectance, degree of polarization, normalized polarized radiance and
  polarized reflectance.
- `read_osoaa_radiance_vs_vza(text, /)` -> `OsoaaRadianceScan`: the two
  relative azimuths and the altitude or depth of the header, and the
  same columns against the signed viewing zenith angle.

No conversion to W/m2 or W/m2/sr: the manual leaves Esun to the user,
and so does the package. A file whose first line is not the one its
reader expects, a row with the wrong number of values, a Fortran field
overflow (`***`) or a value that is not finite is refused, naming the
line.

**The data.** One run, the files of section 86's example run by OSOAA:
`Flux.txt`, both `RESLUM` files, `ListParam.txt`, and the two input
files, in `tests/data/osoaa_iii_440/`, for the tests only (about 45
kB). OSOAA is GPL v3; these are its results, not its code. DATA.md
section 38 gains the run's parameters and what the readers recover.

**The example.** `radiative_transfer_inputs.py` gains `--read DIR`, a
results directory: Kd from OSOAA's Ed over the run's depths at its
wavelength, beside Jerlov's (1976) Kd and Solonenko & Mobley's (2015) for
the type, the irradiance reflectance Eu/Ed and the Q factor just below
the surface. In the run: 0.138 per m from 0 to 50 m, against 0.145 and
0.130. Without `--read` it does what it did. The examples stay
twenty-seven.

**Checks.** The run read back: the totals equal direct plus diffuse to
the printed digits; the direct flux at the top of the atmosphere is pi
cos 30 degrees; the printed Eu/Ed is the ratio of the printed totals;
the reflectance column of `RESLUM_vsZ` is pi I / Ed with Ed from
`Flux.txt` at the same depth; the input files are what section 86's
functions write today, byte for byte; refusals of each kind.

**Version.** 1.15.0: three readers and three result classes, six public
names, 122 in all.

**Differences from the plan, noted after the code was written.**

- The example sets OSOAA's Kd beside Jerlov's in both editions (0.129
  in 1968, 0.145 in 1976) and beside Solonenko and Mobley's K_d^H
  (0.123), the Kd HydroLight made of their own a and b, rather than
  beside their `kd()`, which is their bio-optical model's (DATA.md
  section 19), not a radiative transfer result.
- `RESLUM_vsVZA.txt` prints the nadir twice, as -0.00 and 0.00, one row
  for each half-plane, with one value; the reader keeps both, as for the
  two surface levels in the sea.
- A reader given a path rather than text raises `TypeError` and says to
  pass `Path(...).read_text()`.
- The example finds its files either in OSOAA's own folders
  (`Advanced_outputs/`, `Standard_outputs/`) or all in one, as
  `tests/data` keeps them.

## 88. A review of 1.11.0-1.15.0: three defects (1.15.1): the plan

The user asked on 2026-11-15 for the code added since the review of
1.10.1 (sections 80 and 81) to be reviewed: `rendering.py`,
`ScatteringFunction.mean_cosine`, `materials.py` and `interop.py`. Each
function was given inputs at and past its edges, and the input formats
were read again against OSOAA's and HydroLight's documents. Three defects
were found, each reproduced; the user asked for all three to be fixed, as
1.15.1. No shipped value changes, and no name is added or removed. This
release was written by Claude at the user's request, and its commits and
pull request name Claude as their author.

**1. `rgb_transmittance` holds every distance's spectrum at once.** The
transmittance is formed from an array of distances by wavelengths by
three channels, so memory grows with the table: 20,000 distances took
678 MB, and a 256 x 256 table, 65,536 distances, would take about 2.2 GB.
The fix forms it in blocks of distances, each row computed exactly as
before, so the values are unchanged to the last bit. `rgb_attenuation`
uses at most 4001 distances and was never affected.

**2. The writers print depths and wavelengths to six digits.**
`osoaa_user_profile` and `hydrolight_ac9_file` format each depth, and
the HydroLight file each wavelength, with `.6g`. Depths 0, 100.0000001
and 100.0000002 m are accepted as strictly ascending and written as 0,
100 and 100: a profile OSOAA would read as not ascending. Wavelengths
440.0000001 and 440.0000002 nm are both written 440, and a depth of
1234.56789 m is written 1234.57. The fix prints them with `.15g`, which
writes 0, 10 and 50 as before, so the run of section 86 is unchanged
byte for byte, and refuses a list whose printed values, read back, are
not strictly ascending.

**3. `osoaa_phase_function` takes polarization ratios of any size.** It
wrote -F12/F11 = 5 and F22/F11 = -3 without complaint. No element of a
Mueller matrix of scattering exceeds F11 in magnitude, so each of the
three ratios lies in [-1, 1]; the fix refuses a value outside it, naming
the ratio and the angle.

**Not changed.** `pure_water=(True, 0.0)` is read as (1.0, 0.0), as a
boolean wavelength is elsewhere in the package (`Water.a(True)`): a
convention, not a defect of these functions.

**Checks.** Each defect's reproduction becomes a test that fails before
the fix: the transmittance of 20,000 distances equal, bit for bit, to
the same distances asked for one at a time, with the block size made
small in the test; the three cases of the writers refused or written in
full; the ratios outside [-1, 1] refused and 1 and -1 accepted.

**Version.** 1.15.1.

## 89. Two open questions recorded beside the data they bear on (1.15.2): the plan

The user asked on 2026-11-15 which questions in ocean optics have long
stayed open, and then for the recent literature on them. Two of them bear
directly on what the package ships, and the user asked for both to be
recorded in its documents. Nothing in the code changes; this is the plan,
committed before the text. Each statement is one that was read in the
source itself, not in a search engine's summary of it: two such
summaries, that turbulence outweighs particles in scattering "up to
0.1 degree" and that Mason et al. are "lower by a factor of up to 5"
than Pope & Fry, are not in those papers' abstracts and are not used.

**1. Pure water absorption in the violet and near ultraviolet (DATA.md
section 29).** Which of the published spectra is right below about 450
nm is unsettled. The package ships four, and their ratios can be computed
from the shipped tables rather than quoted: Pope & Fry over Mason et al.
is 7.95 at 380 nm, 2.99 at 400, 1.46 at 420 and 1.22 at 440, and between
0.97 and 1.08 from 460 to 550 nm; Lee et al. over Mason et al. is 2.59 at
380 nm. These go into section 29, with a test that recomputes them, and
the docstring of `pure_water_absorption_table` points there. The package
continues not to choose.

**2. Scattering below Petzold's first angle (DATA.md section 21).**
Bogucki, Domaradzki, Ecke and Truman (2004), "Light scattering on
oceanic turbulence", Appl. Opt. 43(30), 5662-5668, DOI
10.1364/AO.43.005662, measured the volume scattering function from 1e-7
to 1e-3 rad (about 6e-6 to 0.06 degree, below Petzold's first angle of
0.1 degree) and found that "the total scattering coefficient b, due to
scattering on turbulent inhomogeneities, is between 1 and 10 m-1 under
typical oceanographic conditions", and that "optical measurements at
small angles are affected by turbulence-related scattering" (the
abstract). Petzold's extension below 0.1 degree is a power law of the
measured particle and water scattering; scattering by turbulence is not
in it, and how much of it a given water has depends on the day's mixing,
not on its particles. This goes into section 21, beside the extension it
qualifies.

**Version.** 1.15.2: documents only.

## 90. Where the closure between IOPs and Kd fails: OSOAA runs, factor by factor (1.15.3): the plan

The user asked on 2026-11-15 for the closure between the package's
sources to be taken apart: Williamson & Hollins's a and b for a Jerlov
type, put through a radiative transfer code, against the Kd Jerlov
printed for the same type. A single run (section 87) gave 0.138 per m for
III at 440 nm against Jerlov's 0.129 (1968) and 0.145 (1976). This plan
asks which of the inputs a Jerlov type does not fix moves that number,
and by how much. It does not settle which source is right; it measures
how far each unrecorded choice reaches. The user chose on 2026-11-15:
six types by twelve wavelengths; varying the sun, the phase function,
the pure water and the sky and surface; Jerlov 1968 and 1976 both as the
comparison; the runs kept in `tests/data` with a script in `tools/` and a
new section of DATA.md, no new public name.

**Why it is not circular.** Williamson & Hollins's a and b are averages
of measured IOPs, grouped by Jerlov type (DATA.md section 9); they were
not derived from Jerlov's Kd. Their measured points lie from 412 to 715
nm, so the wavelengths are the twelve Jerlov printed inside that range,
425 to 700 nm every 25.

**The base runs**, 6 types (IB, II, III, 1C, 3C, 5C) by 12 wavelengths,
72 runs of OSOAA (commit 8e4914f, as in section 86), each set out so that
a Jerlov type's own values decide everything a type does decide:

- a and b: Williamson & Hollins's, less OSOAA's own pure seawater at the
  wavelength (its `fic/OSOAA_SEA_MOL_COEFFS_JUNE_2013.txt`), so that the
  total OSOAA runs is the type's.
- Phase function: the Petzold station whose b at 530 nm is nearest the
  type's, as `reference_images.py` chooses (section 85), with the
  polarization ratios of section 86's example. Petzold's is the total of
  water and particles; OSOAA adds the water's own Rayleigh-like
  scattering on top, so the particles' phase function is approximated by
  the total, more so in the clearest water. Recorded, not corrected.
- Sun at 30 degrees from the zenith, OSOAA's maritime aerosol of optical
  thickness 0.1 at 550 nm, wind 7 m/s, as in section 86's run; a black
  seabed deep enough that doubling its depth changes Kd by less than 0.1
  percent (checked on one run of the clearest and one of the most turbid).
- Kd: from OSOAA's Ed, the mean over the first penetration depth, from
  just below the surface to where Ed falls to 1/e of its value there, and
  as a second figure to where it falls to 10 percent. Jerlov's tables do
  not record the layer either.

**The factors**, each varied alone on IB and III at all twelve
wavelengths, the others at the base:

- the sun: 0 and 60 degrees from the zenith (Jerlov's tables do not record
  it; DATA.md section 33);
- the phase function: AUTEC 8 (the clearest), HAOCE 5 and NUC 2200 (the
  most turbid but one), whatever the base station was;
- the pure water: the total a made with Pope & Fry's, Mason et al.'s and
  Lee et al.'s aw in place of the aw Williamson & Hollins built a on
  (`pure_water_absorption`), that is a - aw_WH + aw_X, at the wavelengths
  each covers (to 550 nm for Mason and Lee);
- the sky and surface: aerosol optical thickness 0.05 and 0.3, and wind 2
  and 15 m/s.

About 300 runs; each takes about 15 s.

**What is kept.** `tools/osoaa_closure.py` writes each run's two input
files with the package's own writers, runs OSOAA where it is built (the
path is the caller's), and reads `Flux.txt` with `read_osoaa_flux`. It
keeps, in `tests/data/osoaa_closure/`, a table of every run's
parameters and a table of Ed at the sea's levels, the total downward flux
as OSOAA printed it; Kd is computed from them. The full outputs are not
kept. The tests recompute every figure DATA.md quotes from those tables;
they cannot rerun OSOAA, which is GPL Fortran outside the package and
not in CI, and the new section says so.

**What the section will report**, for each type and wavelength: OSOAA's Kd
against Jerlov 1968 and 1976, and, factor by factor, the range over which
each moves it, beside the gap between the two editions of Jerlov. Solonenko
& Mobley's K_d^H, HydroLight's Kd from their own a and b, is listed for
reference where it exists. The question the numbers answer: is the gap
between IOPs and Kd larger than what the unrecorded conditions alone can
make?

**Version.** 1.15.3: no package code changes; a tool, test data, tests
and DATA.md section 39.

**Differences from the plan, noted after the code was written.**

- The plan took for granted that a type's total could always be given to
  OSOAA. It cannot from 650 nm: OSOAA adds its own pure water, which
  there is above the aw Williamson & Hollins built a on (0.340 against
  0.3315 per m at 650 nm, 0.624 against 0.5722 at 700), so a profile of
  their total less OSOAA's water would be negative, and the writer
  refuses it. Those 46 runs are kept as `not_run`, and a further 72 were
  added: every type's contents on OSOAA's own water, which can always be
  run. 408 runs in all, not about 300.
- The pure water factor is "a - aw_WH + aw_X" as planned; the contents on
  OSOAA's water are the same factor with aw_X OSOAA's.
- The seabed check was made on IB at 425 nm and 5C at 675 nm, since 5C at
  700 nm cannot be run.
- A sentence of the first draft of DATA.md section 39, that the gap for
  II and III was within the conditions, held only against 1976, and now
  says so; a test checks it against both editions.

## 91. Open questions in a document of their own, and an example for each (1.15.4): the plan

The user asked on 2026-11-15 for the work of sections 89 and 90, putting
numbers on what is unsettled in the literature, to go on, and for what it
finds to be shown, with the code that found it in `examples/`. They left
the names and form to this plan, asked that every document of the package
stay in English, and asked for it in the next version. Nothing in the
package's code changes; this is the plan, committed before the text.

**Why a document of its own.** DATA.md records what each shipped table
is and what is wrong with it. What sections 21, 29 and 39 found is of a
different kind: not about one table, but about where two sources, or a
source and a code, disagree, and by how much the unrecorded conditions
can account for it. Kept inside DATA.md, it is found only by someone
already reading about that table.

**`OPEN_QUESTIONS.md`**, at the top of the repository beside DATA.md and
DECISIONS.md, one section per question, each in the same five parts:

- *The question*, in a sentence a reader outside the field can follow;
- *What was done*: the data, the code, how many runs;
- *What was found*, every figure recomputed by a test;
- *What is not known*, and what measurement or calculation would move it;
- *Where*: the DATA.md and DECISIONS.md sections, the example, the release.

It opens by saying what the package does and does not do here: it does
not settle these questions, which need new measurements; it states how far
apart the published values are and how much of that the conditions a
source leaves unrecorded can explain. Three questions to begin with:
pure water absorption in the violet (DATA.md section 29), scattering below
Petzold's first angle (section 21), and the closure between Williamson &
Hollins's IOPs and Jerlov's Kd (section 39). Where a first draft said more
than the numbers did, as section 90 records, the document says so.

**On the documentation site**, a page `open_questions` lists each question
with its finding in a line and links to `OPEN_QUESTIONS.md` on GitHub, as
the site already links to DATA.md and DECISIONS.md, so that the text is
kept in one place. A test checks that every question in the document has
its line on the page.

**`examples/closure_with_jerlov_kd.py`**, the twenty-eighth example: it
reads the OSOAA runs of section 90, needing neither OSOAA nor anything not
in the repository, and prints, computing each figure as it goes, OSOAA's
Kd beside Jerlov's in both editions, how far each condition moves it, the
backscatter ratio the coastal types would need, and the runs that could
not be made. The tables and conclusions in `OPEN_QUESTIONS.md` are the
example's output, and a test runs it and compares.

**The runs move to `examples/data/osoaa_closure/`.** The examples run
against the installed package, but this one needs the runs, which are
results of the package rather than data it ships and stay out of the
wheel. So the example reads them from beside itself, and says that it
needs the repository; CI runs the examples from the repository. The tests
of section 90 read the same files, and are skipped away from the source
tree. `tools/osoaa_closure.py` writes there. Section 90's paths are left
as written, this section moving them.

**Version.** 1.15.4: a document, a page, an example, and data moved.

## 92. Section 90 was wrong: OSOAA's truncation, a Monte Carlo instead, and the closure again (1.15.4): the plan

The closure of section 90 rested on OSOAA's Kd, and OSOAA's Kd were too
low. Found on 2026-11-15, when Williamson & Hollins's own paper (Appl.
Opt. 61, 9951-9961, section 3.D and Table 5) reported their averaged a
and b agreeing with Jerlov's Kd to a mean absolute error of 14 to 17
percent, where section 39 had the coastal types at half of Jerlov's. The
user asked for the cause to be found, a replacement to be checked, and
the closure to be done again, in this release, before 1.15.4 is merged.
This is the plan, committed before the code.

**What was wrong.** OSOAA always truncates the forward peak of the
hydrosols' phase function (its User Manual V2.0, section 4.2.3, p. 96).
Given Petzold's phase functions, it reported a truncation coefficient of
1.90 to 1.95 (`PM_PHYTO.txt`), that is 95 to 98 percent of the hydrosols'
scattering treated as unscattered, where Petzold's own functions hold 84 to
89 percent within 23 degrees and 52 to 64 within 5. The share stayed
there when OSOAA was rebuilt with its hydrosol truncation angles narrowed
from 32 and 23 degrees to 8 and 5 (`CTE_HYD_MU1_TRONCA`,
`CTE_HYD_MU2_TRONCA` in `inc/OSOAA.h`), and when a 0 degree row was added
to the phase function; Kd did not move either. The spreading of light by
many small-angle scatterings, which raises Kd with depth, was lost: its
Kd/a stayed at 1.12 to 1.20 to six optical depths whatever b/a was. Why
OSOAA treats these phase functions so was not traced further; it is
recorded, and the closure no longer rests on it. The writers of section
86 are not wrong, but `osoaa_phase_function`'s docstring will say this.

**The replacement.** `tools/kd_monte_carlo.py`, written for this: a
homogeneous, infinitely deep water lit by a collimated beam at the
refracted sun, photons on exponential paths with weight b/c kept at each
scattering and Russian roulette below a small weight, the scattering
angle drawn from Petzold's tabulated function (a power law between his
angles and, below 0.1 degree, his extension). It models no sky, no
atmosphere and no surface reflection. Checked on 2026-11-15:

- with no scattering, Kd is a / mu0 within the noise (0.996 of it);
- against the relation of Morel and Loisel for optical depth 1, as
  Williamson & Hollins print it (their Eq. 2), for b/a from 0.5 to 10:
  within 1 percent with NUC 2240's phase function (bb/b 0.018), within 4
  with AUTEC 7's (0.026) and up to 8 percent lower with HAOCE 5's
  (0.014), the departures following the phase function's backscattering,
  which that relation does not take;
- against Solonenko and Mobley's relation for optical depth about 2.3
  (their Eq. 3), 2 to 10 percent lower; recorded.

It is a tool, checked only as far as this; it is not part of the package.

**The closure again**, with it: the six types at the twelve wavelengths,
the base as in section 90 (the type's own total a, the nearest Petzold
station, the sun at 30 degrees); then on IB and III the sun at 0 and 60
degrees, the stations AUTEC 8, HAOCE 5 and NUC 2200, and the pure water of
Pope & Fry, Mason et al. and Lee et al. in place of Williamson &
Hollins's. The aerosol and the wind are dropped: the Monte Carlo has no
sky. With no OSOAA water underneath, every run can be made. Kd over the
first penetration depth and to 10 percent. The runs, their seeds and
their Kd are kept in `examples/data/kd_closure/`, made by
`tools/kd_closure.py`. The OSOAA runs of section 90 stay in
`examples/data/osoaa_closure/` as the record of what went wrong, and the
tests use them to show OSOAA's Kd against the Monte Carlo's.

**The documents.** DATA.md section 39 is rewritten: what was found, what
had been wrong and why, OSOAA's Kd beside the Monte Carlo's. Section 38
gains the truncation. `OPEN_QUESTIONS.md`'s third question is rewritten
from the new runs and says plainly that the version published in 1.15.3
was wrong, and why. `closure_with_jerlov_kd.py` reads the new runs. The
statements of section 90 stay as written, this section correcting them.

**Version.** Still 1.15.4: the correction goes into its pull request,
which has not been merged.

**Differences from the plan, noted after the code was written.**

- The truncated share is 96.5 to 97.8 percent over all 362 OSOAA runs of
  section 90, read from each run's `PM_PHYTO.txt` and kept in
  `examples/data/osoaa_closure/truncation.csv` so that a test can
  recompute it; the plan's 95 to 98 came from four runs. Likewise OSOAA's
  Kd are 0.7 to 23.1 percent below the Monte Carlo's over its 62 base
  runs, not the 7 to 29 of the four runs first compared (which were the
  Monte Carlo above OSOAA, the other way round).
- The result: against Jerlov (1976), Williamson & Hollins's IOPs give Kd
  within what the sun, the phase function and the pure water together can
  make (0.77 to 1.53 times) everywhere except at the blue end, IB at 425
  to 475 nm above and 1C, 3C and 5C at 425 nm (3C also at 450) below. The
  phase function moves Kd by -6.4 to +14.5 percent, not the under 1.5
  that OSOAA's truncation had shown.
- `tests/test_osoaa_closure.py`, which checked figures no document now
  quotes, is replaced by `tests/test_kd_closure.py`, which also runs the
  Monte Carlo's checks and makes one stored run again from its seed.

## 93. The fault was the package's: `osoaa_phase_function` wrote F11 4 pi too small (1.15.5): the plan

Section 92 put the low Kd of section 90 down to OSOAA truncating Petzold's
phase functions too far, and said why OSOAA did so had not been traced.
The user asked whether that had come from reading OSOAA's source; it had
not, and they asked for it to be traced. It was, on 2026-11-15, and the
fault is in this package.

**What OSOAA does.** For a user's phase function (`-HYD.ExtData`,
`OSOAA_HYDROSOLS.F`, the branch IMOD = 2), OSOAA splines F11 in the cosine
onto its Gauss angles and passes it, unnormalised, to
`SOS_DECOMPO_LEGENDRE` (`OSOAA_PARTICLES_RAD.F`), which truncates it and
takes the truncation coefficient as A = 2 (1 - beta_0), with beta_0 =
(1/2) sum of F11 times the Gauss weights. That holds only if F11 is
normalised so that (1/2) of its integral over the cosine is 1, that is
its integral over the sphere is 4 pi. The manual does not say so in words
(section 3.6.3, p. 81: "phase function in intensity P11"), but its
example, an aerosol's F11 of 0.419 at 180 degrees, is of that scale.

**What the package wrote.** `osoaa_phase_function` (1.14.0 to 1.15.4)
wrote F11 = vsf / b, whose integral over the sphere is 1: 4 pi times too
small. Section 86 had said OSOAA normalises it; it does not, before the
truncation coefficient is taken. With the file multiplied by 4 pi and
nothing else changed, OSOAA truncated 65 to 70 percent instead of 96.5 to
97.8, and its Kd came within 2 to 8 percent of the Monte Carlo's for 5C
at 550 nm, IB at 450, III at 550 and 3C at 450.

**The fix.** `osoaa_phase_function` writes F11 = 4 pi vsf / b, says so,
and a test checks the normalisation; the docstring's warning about
OSOAA's truncation, which blamed OSOAA, goes. This changes the files the
function writes, a fix to a defect, not a change of behaviour the package
promised; the CHANGELOG says so under "Fixed".

**What is done again with OSOAA, by hand outside CI.**

- The run of sections 86 and 87, kept in `tests/data/osoaa_iii_440/`,
  with the corrected phase function. The readers' tests and the figures
  quoted from it (Kd of 0.1381 per m, the example's `--read` part) are
  recomputed.
- The 408 runs of section 90, with the corrected files, kept in
  `examples/data/osoaa_closure/` in place of the old ones, with their
  truncation coefficients. They become a second, independent calculation
  beside the Monte Carlo of section 92, whose conclusions do not change.

**The documents.** DATA.md sections 38 and 39, `OPEN_QUESTIONS.md`, the
example `closure_with_jerlov_kd.py`, `radiative_transfer_inputs.py`'s
figures and the README are corrected: the first answer of 1.15.3 was
wrong because the package wrote the phase function 4 pi too small, not
because of OSOAA, and section 92's account of the cause was itself wrong.
Sections 86, 90 and 92 stay as written, this section correcting them.

**Version.** 1.15.5.

**Differences from the plan.**

- The plan put the new OSOAA runs "in place of the old ones". The old
  runs are kept instead, in `examples/data/osoaa_closure_f11_too_small/`,
  so that the figures the documents still quote from them (96.5 to 97.8
  percent, 0.7 to 23.1 percent) stay recomputed by a test, as the rest of
  this package's figures are. The single run in `tests/data/` is
  replaced; release 1.15.4 keeps its old files, and the documents quote
  no figure from them.
- `tests/data/osoaa_iii_440/` gains the run's `PM_PHYTO.txt`, so that its
  truncation coefficient, 1.40215, is read by a test, and
  `tools/osoaa_closure.py` writes `truncation.csv` itself instead of a
  script outside the repository.
- With the corrected file OSOAA's Kd is 1.007 to 1.096 times the Monte
  Carlo's over the 62 base runs; the four trial runs, 2 to 8 percent
  above, are among them, with the same results. It is the higher the bluer the light and the
  clearer the water. OSOAA's sky, which the Monte Carlo lacks, may account
  for it; that was not checked. The station moves OSOAA's Kd by -5.8 to
  +14.9 percent, against the Monte Carlo's -6.4 to +14.5. Against Jerlov
  (1976) OSOAA's Kd lies outside the reach of the three conditions at the
  same places as the Monte Carlo's but for 5C at 425 nm, which it brings
  just inside. The documents say so.
- The first rerun stopped when the disk filled (each run keeps about
  60 MB of OSOAA's own files); the bulky files of finished runs were
  deleted as the runs went, which does not change the results.

## 94. Solonenko & Mobley's IOPs through the Monte Carlo and OSOAA, against their HydroLight Kd (1.15.6): the plan

The Monte Carlo of section 92 has been checked against a relation (Morel
and Loisel's) and, since 1.15.5, against OSOAA, which gives Kd 1.007 to
1.096 times its own. It has not been checked against HydroLight, and
OSOAA's excess has not been explained. The package already ships what
such a check needs: Solonenko & Mobley's (2015) retrieved a and b for
ten Jerlov types, and the K_d^H that HydroLight computed from them
(`kd_hydrolight`, DATA.md section 19). The user agreed on 2026-11-15 to
put those a and b through the Monte Carlo and OSOAA and set the result
beside K_d^H.

**What the paper says of the HydroLight runs** (Appl. Opt. 54, 5392-5401;
journal page = PDF page + 5391, checked page by page):

- p. 5396 (section 4): the retrieved a and b, "a Petzold average-particle
  phase function and appropriate boundary conditions (sun zenith angle,
  clear sky, infinite water depth)", no inelastic scattering.
- p. 5394: the phase function is eta beta_w + (1 - eta) beta_p (Eq. 2),
  eta = bw / (bw + bp); beta_w's shape "can be found in" Morel & Loisel;
  beta_p is "the averaged Petzold phase function obtained by averaging the
  coastal, harbor, and ocean phase functions", mean cosine 0.924. The
  pure water absorption is an average of Pope & Fry, Buiteveld et al. and
  Pegau et al., not printed.
- p. 5395: bw = 5.83e-3 (400 / lambda)^4.322 (Eq. 8a), the coefficient
  and exponent the package's `ScatteringConstants` for this source hold.
- p. 5401 (Appendix A): HydroLight's modelling depth was 10 scattering
  lengths, 6 for Jerlov III.
- p. 5393: Jerlov measured the oceanic types at a sun elevation of 75
  degrees and the coastal at 45; p. 5394 uses those (mu_w 0.98 and 0.85)
  in the paper's own Kd relation, Eq. (3).

**What is not stated, and what is done about it.** Decided before any run.

- The sun of the HydroLight runs: not printed. The base takes the paper's
  own choice for Eq. (3), 15 degrees from the zenith for I to III and 45
  for the coastal types; 0, 30 and 60 degrees are run as a factor.
- The average-particle phase function: not shipped (section 27, "No
  average") and not in hand. The base takes the Petzold station whose mean
  cosine is nearest the paper's 0.924: NUC 2240 (0.9255; its bb/b is
  0.018). All eight stations are run as a factor; what they span stands in
  for not knowing the average's shape. If the user obtains the average's
  table, it can be run on the same cells.
- The sky: "clear sky", nothing more. The base takes the share of Ed just
  below the surface that is diffuse from `gregg1990_irradiance`, for the
  run's sun and wavelength, with the atmosphere of
  `examples/sunlight_and_d65.py` (day 172, 1013.25 hPa, air mass type 1,
  80 percent, 1.5 cm, winds 3 and 5 m/s, 300 DU) and tau_a(550) = 0.2;
  0.05 and 0.4 as a factor; and none at all, as section 92 ran. The sky's
  radiance is taken as uniform in the air.
- Which depth K_d^H belongs to: not stated (the modelling depth is not
  that). Kd is taken, as in section 92, from the surface to the first
  penetration depth and to 10 percent of Ed; the latter, which the
  paper's Eq. (3) uses (optical depth about 2.3), is the one compared, the
  other reported beside it.
- The pure water: the Monte Carlo needs only the totals a and b, which
  are what is shipped. OSOAA adds its own pure water back, so its own aw
  and bw are subtracted (`osoaa_user_profile(pure_water=...)`) and the
  totals it runs are S&M's; the share of b it scatters as water is then
  OSOAA's own bw, not Eq. (8a). Where S&M's a is below OSOAA's aw the run
  cannot be made and is recorded as not run, as in section 90.

**The Monte Carlo gains two options** (`tools/kd_monte_carlo.py`, not the
package), both off by default, and off it draws exactly the same random
numbers as before, so the 240 runs of section 92 are reproduced bit for
bit (checked on a run before and after):

- `water_share`, eta: at each scattering the photon is turned by pure
  water's phase function, 1 + 0.835 cos^2 (the shape of
  `pure_water_vsf`, Morel's delta = 0.09; whether it is the very shape of
  Morel & Loisel's paper is not checked), with probability eta, and by
  the station's otherwise. The station's function is Petzold's measured
  total, water included, as OSOAA was given it in sections 90 and 93;
  nothing is subtracted from it.
- `sky_share`: that fraction of Ed just below the surface enters as
  diffuse light, uniform in radiance in the air, weighted by Fresnel's
  transmittance (n = 1.34, unpolarised) and refracted; the rest is the
  sun's beam, as before.

New checks, in `--check`: with no scattering and only the sky, Kd equals
a over the mean cosine of the refracted, Fresnel-weighted uniform sky,
computed by quadrature, within the noise; with eta = 1 the sampled angles
have a mean cosine of 0 and half go backwards.

**The runs** (`tools/sm_closure.py`, written to
`examples/data/sm_closure/`): the 143 cells of the ten types from 350 to
700 nm every 25 nm where a, b and K_d^H are all given (flags kept in the
file). On every cell: (1) as section 92 (no water share, no sky, the
base sun and station); (2) the water share alone; (3) the base: water
share and sky. On the base, one at a time: the seven other stations, the
sun at 0, 30 and 60 degrees, tau_a(550) 0.05 and 0.4. About 2000 runs of
400 000 photons, seeded by run number.

Then Williamson & Hollins's 72 base cells of section 92 again with the
water share (their scattering constants hold the same Eq. 8a), and with
the water share and the sky (sun 30 degrees, tau_a 0.2), to see how far
section 92's figures and OSOAA's excess over the Monte Carlo move.

OSOAA (as built for section 93, by hand, outside CI): the 143 cells as the
base above, with OSOAA's own atmosphere (its maritime model of section 90
at an AOT of 0.2, and 0.05) and a wind of 2 m/s, the phase function of
NUC 2240 as `osoaa_phase_function` writes it since 1.15.5.

**What will be read off, decided now.**

1. The Monte Carlo against HydroLight, at the base, Kd to 10 percent:
   the ratio to K_d^H, per type and over all cells. It is called in
   agreement if the median lies within 0.95 to 1.05 and 90 percent of the
   cells within 0.90 to 1.10; otherwise the documents say it is not, and
   by how much.
2. The cells where K_d^H lies outside what the factors (station, sun,
   aerosol, the depth Kd is taken to) move the base's Kd: listed.
3. OSOAA against the Monte Carlo on the same inputs: the ratio, beside
   section 93's 1.007 to 1.096.
4. Whether the water share and the sky move the Monte Carlo toward OSOAA
   on Williamson & Hollins's runs, and by how much; and how far the
   figures of section 92 and `OPEN_QUESTIONS.md`'s third question move.
   If they move, the documents are corrected and say so.

None of this says anything about Jerlov's Kd: K_d^H and the Monte Carlo
are both computed from the same retrieved IOPs.

**The documents.** A fourth question in `OPEN_QUESTIONS.md` (and the
site's page), DATA.md section 40, a part of
`examples/closure_with_jerlov_kd.py` that reads the new runs, the README
of `tools/` and of the examples, the figures recomputed in
`tests/test_quoted_figures.py`. Nothing shipped changes.

**Version.** 1.15.6.

**Differences from the plan.**

- Seeds: the plan said "seeded by run number". Before the first run every
  run of one cell was given the same seed instead, so that the
  differences between them are not swamped by the noise; the runs of
  Williamson & Hollins's cells take the seeds of their runs in
  `examples/data/kd_closure/`.
- Added after the first run: section 92's 168 factor runs (sun, station,
  pure water) with the water share and the sky. The first run had only
  the base with them, and part 5 of the example needs the reach of the
  conditions taken from the same Monte Carlo. They were appended, so the
  first 2289 rows are byte for byte those of the first run (checked);
  2457 runs in all, not "about 2000".
- OSOAA: 286 runs (the base at an AOT of 0.2 and again at 0.05); at 29 of
  the 143 cells S&M's a or b is below OSOAA's own pure water, and those
  are recorded as not run.

**What was found** (2026-11-16), as read off in the plan:

1. The Monte Carlo with the water share and the sky over K_d^H, Kd to 10
   percent: median 0.970, 94.4 percent of the 143 cells within 10
   percent. The criterion is met. With the water share alone, 0.951 and
   90.2 percent (met); as section 92 ran it, 0.945 and 79.7 percent (not).
2. No cell lies outside what the stations, the sun, the aerosol and the
   depth make of the base's Kd.
3. OSOAA over the Monte Carlo on the same inputs: 0.986 to 1.037 at the
   114 cells it can run; over K_d^H, median 0.978.
4. On Williamson & Hollins's cells the water share moves the Monte
   Carlo's Kd by -0.1 to +4.7 percent, with the sky +1.3 to +7.6, and
   OSOAA over it goes from 1.007-1.096 to 0.991-1.018: section 93's
   excess is accounted for. The conditions' reach becomes 0.79 to 1.44
   (was 0.77 to 1.53); against Jerlov (1976) the same blue cells lie
   beyond it, and IB at 500 nm (1.27) just beyond. `OPEN_QUESTIONS.md`'s
   third question says so; its conclusion does not change. DATA.md
   section 39 and the example's parts 1 to 4 keep section 92's figures
   as what was first run.

**Caught before the commit, by reading the output.** The example's part 5
first printed "the same places as in section 3", because it looked only
for cells that came inside the reach, not for IB at 500 nm, which went
outside; it now reports both. DATA.md section 40's first draft said the
ratio was 0.93 to 1.00 "for most types" (it is six of ten) and that
"three codes" agree to a few percent (HydroLight was not given the same
phase function; only OSOAA and the Monte Carlo were); both were
corrected. A test first required the sky to raise Kd by more than 3
percent, a figure not taken from any calculation; it failed at 2.1
percent, and now requires only a rise.

## 95. Why the blue end disagrees: the Kd measured in the same waters (1.15.7): the plan

`OPEN_QUESTIONS.md`'s third question leaves one thing unexplained: at the
blue end, Williamson & Hollins's averaged IOPs give Kd 1.41 to 1.55 times
Jerlov's (1976) for IB and 0.53 to 0.66 for the coastal types, beyond
what the unrecorded conditions can make (section 94). The user chose this
on 2026-11-16, together with two smaller items it needs: how far Jerlov's
two editions differ (1968 against 1976, every type and wavelength), and
how the spread of the measured points compares with the gap.

**What is already in hand.** Williamson & Hollins's figshare dataset
(DOI 10.6084/m9.figshare.20290782, Version 3, Open Government Licence
v3.0) keeps every step of their processing. Three of its files, not read
until now, hold what the averaged IOPs hide (each downloaded and checked
against figshare's MD5 on 2026-11-16):

- `op_STEP_5_k.csv`: the Kd of each of the 2,710 measurement campaigns
  they kept, over the upper 10 m, each with the Jerlov type it was given
  (nearest Jerlov 1976 Kd by mean absolute percentage error over the
  campaign's own wavelengths, within 25 percent; their section 2.E);
- `op_STEP_5_a.csv` and `op_STEP_5_b.csv`: a and b of each campaign that
  went into the averages, with its type;
- `op_STEP_7_kab.csv`: a, b and Kd measured in the same campaign at the
  same wavelength, 412, 510, 532 and 555 nm (their section 2.H).

A look at them before this plan was written (and so, in the spirit of
section 92, recorded here rather than hidden): the campaigns typed 1C and
3C have measured Kd at 410 to 430 nm of about 0.53 to 0.59 times Jerlov's
(1976), the same as the IOPs give, while the campaigns typed IB have
measured Kd close to Jerlov's in the blue; and of the six campaigns behind
IB's averaged a, in two the a at 412 or 440 nm is about equal to or above
the Kd measured in the same campaign. The tests below were chosen after
that look; what they will count as an answer is fixed here, before they
are run.

**The parts** (`tools/blue_end.py`, which reads the three files from
`sources/20290782/` and writes `examples/data/blue_end/`; a new part of
`closure_with_jerlov_kd.py` prints every figure):

1. *The two editions.* Jerlov (1968) over Jerlov (1976), at the
   wavelengths both printed, for the ten types. Recorded.
2. *The Kd each type's waters measured.* For every campaign kept by
   Williamson & Hollins, its measured Kd over Jerlov's at the same
   wavelength (the 1 nm tables, which interpolate linearly between the
   printed values), grouped by type and by the nearest of Jerlov's printed
   wavelengths within 12.5 nm: median, quartiles and count, against both
   editions.
3. *The IOPs against the Kd of the same campaign.* For each entry of the
   matched set, the Monte Carlo's Kd from the campaign's own a and b
   (section 94's options: pure water's share by Williamson & Hollins's
   own Eq. 8a, the sky of Gregg & Carder at an aerosol of 0.2; the sun at
   30 degrees, which the data do not record, 0 and 60 as a factor;
   NUC 2240's phase function, HAOCE 11's and AUTEC 8's, the lowest and
   highest bb/b of the stations, as a factor), over the Kd measured in it.
   Kd over the first penetration depth. Where the campaign's a is not
   positive, or b is below Eq. 8a's bw, the entry is recorded and not run.
4. *A against Kd within a campaign.* For every campaign with a and Kd at
   the same wavelength (the matched set, and the IOP campaigns of each
   type whose Kd campaign has the wavelength within 3 nm), whether the
   measured a is at or above the measured Kd. No radiative transfer
   calculation returns Kd below a (Gershun's law, a = mu K_E with mu at
   most 1; every Monte Carlo run of sections 92 and 94 has Kd/a of at
   least 1.012), so such an entry cannot be closed by any phase function,
   sun or sky.
5. *The spread.* For each blue cell of section 94 beyond the reach, the
   change in a that would close it (by the Monte Carlo, b held), in units
   of the standard deviation of the type's measured points and of the
   standard error (SD over the square root of the campaign count); and the
   difference between neighbouring types' measured a and b in units of
   their pooled SD.

**What will be read off, decided now.**

- Coastal types: if, at 425 nm, the median measured Kd of the campaigns
  typed 1C, 3C and 5C over Jerlov (1976) lies within 0.10 of what their
  averaged IOPs give (section 94: 0.59, 0.53, 0.66), and part 3's median
  for those types at 412 nm lies within 0.85 to 1.15, the documents say
  that the coastal blue gap is between the waters typed and Jerlov's 1976
  values, not in the IOPs or the calculation; and say against the 1968
  edition how much of it remains.
- IB: if the campaigns typed IB measured Kd within 0.90 to 1.15 of Jerlov
  (1976) at 425 to 475 nm, the IB gap is in the averaged IOPs, not in
  Jerlov's Kd; parts 4 and 5 then say whether it is within their spread
  and whether some campaigns' a cannot be closed at all. Which campaigns
  are right is not something this package can settle.
- Otherwise the documents say what was found, as it is.

None of this decides why Jerlov's 1976 coastal blue values are what they
are: Jerlov (1976) is not in hand, and its text is the only place that
could say.

**The data shipped.** `examples/data/blue_end/` holds what the parts read,
reduced from the three files (the campaign, its type, the wavelength and
the value; for `op_STEP_7_kab.csv`, the file as it is), with the
licence's attribution; not in the wheel. `sources/README.md` lists the
three files.

**Documents.** `OPEN_QUESTIONS.md`'s third question; DATA.md section 41;
the example's new part; NEXT_STEPS's items 5, 7 and 9 of section 0d.

**Version.** 1.15.7.

**Differences from the plan.**

- Part 2 grouped the campaigns by the nearest of Jerlov's printed
  wavelengths within 12.5 nm. Run, that put the many measurements at
  412 nm with 400 nm (12 nm away) and left 425 nm all but empty. Before
  any figure was read off, the grouping was changed to the bands the
  measurement wavelengths cluster in (410-414, 440-445, 486-491, 508-512
  and 550-560 nm, named 412, 443, 490, 510 and 555), each campaign against
  Jerlov's 1 nm table at its own wavelength, and only 310 to 700 nm, which
  both editions cover. The coastal criterion's "at 425 nm" is therefore
  read at 412 nm, and IB's "425 to 475 nm" at 412, 443 and 490 nm.
- No matched entry had a not positive or b below pure water's: none was
  left unrun.
- The closing a converged to a residual below 1e-4 in the logarithm of
  Kd but for IB at 475 nm, 4e-4, after eight secant steps; recorded in
  `closing_a.csv`.
- Part 3's "factor" is reported as how far the sun and the stations move
  the median of each type, not the range over single entries, which spans
  the entries' own spread (0.51 to 3.01 at 412 nm for the coastal types)
  and says nothing about the conditions.

**What was found** (2026-11-16).

- Coastal types: the campaigns typed 1C, 3C and 5C measured Kd at 412 nm
  of a median 0.59, 0.53 and 0.56 of Jerlov (1976), within 0.10 of their
  averaged IOPs' 0.59, 0.53 and 0.66; part 3's median at 412 nm is 0.90,
  0.93 and 1.06. The criterion is met: the coastal blue gap is between the
  waters typed and Jerlov's 1976 values. Against 1968 the measured Kd are
  0.85, 0.66 and 0.62.
- IB: the campaigns typed IB measured Kd of 1.02, 1.12 and 1.03 of Jerlov
  (1976) at 412, 443 and 490 nm. The criterion is met: the IB gap is in
  the averaged IOPs. Of its six IOP campaigns, two have a at or above
  their own Kd and two have a at 412 nm a third of it; closing the blue
  cells needs a 1.0 to 1.8 SD lower.
- a at or above Kd in the matched set: IB 3 of 11, II 9 of 88, III 30 of
  211, 1C 0 of 68, 3C 3 of 79, 5C 3 of 12.

## 96. What the literature says of the coastal blue, and what rests on the extension below 0.1 degree (1.15.8): the plan

Two things, agreed with the user on 2026-11-16.

**1. Why Jerlov's coastal blue is what it is: the literature.** Section 95
found that the waters Williamson & Hollins typed 1C, 3C and 5C measured
blue Kd of about half Jerlov's (1976), and that his 1968 values are lower
than his 1976 ones there. The user supplied chapter 10 of both editions.
Read, with the page numbers checked page by page (1976: book page = PDF
page + 126):

- Jerlov (1976), p. 133: the changes from 1968 that he states are at
  600 nm (higher for I, IA, IB and II) and for type III (lower at 550 and
  575, somewhat higher around 425 nm). No change to the coastal types is
  stated.
- Jerlov (1976), p. 137: the coastal types "are derived from observations
  along the coast of Scandinavia and western North America. These northern
  water masses are characterized by a relatively high amount of yellow
  substance. Some recent material (Aas, 1967, 1969 and Højerslev, 1974a)
  has substantially fortified the basis for this special classification."
- Jerlov (1968), pp. 122 and 124: the same origin, with "evidence that
  coastal waters which contain a variable amount of terrigeneous material
  show divergent behaviour in the shortwave part of the spectrum", and no
  mention of yellow substance.
- Aas, Højerslev, Høkedal and Sørensen (2013), Oceanologia 55(2), 471-482,
  doi:10.5697/oc.55-2.471, p. 477: in the open Nordic Seas "coastal types
  from 1 to 5 occur frequently. These coastal types are not real coastal
  waters with high contents of yellow substance and inorganic particles;
  they are caused by algal blooms"; p. 472: Jerlov (1978) reduced the
  coastal types to 1, 3 and 5.
- Aas & Højerslev (2001), Oceanologia 43(2), 139-168, p. 146: Jerlov's
  classification rests on linear relations between Kd at a wavelength and
  at 465 nm, whose constants "may change from one oceanic area to
  another" and are "valid only for the type of water from which they were
  obtained".

Not obtained: Jerlov (1978), Rep. Dept. Phys. Oceanogr. 36, Univ.
Copenhagen; Aas (1969), Rep. 6 of the same series; Højerslev's 1974
reports (numbered 1974a and 1974b differently by different authors); and
whatever Jerlov meant by "Aas, 1967" (perhaps Aas 1971, Sarsia 46,
"Irradiance in Hardangerfjorden 1967").

What the documents will say: Jerlov states no reason for the 1976 coastal
blue; he describes the coastal types as a special classification of
northern waters rich in yellow substance, fortified by new data in 1976.
That, and Aas et al.'s remark that waters of coastal Kd at 465 or 475 nm
need not be yellow-substance-rich, is consistent with section 95's
finding, since Williamson & Hollins typed campaigns by matching Kd over
all wavelengths. It is not shown to be the cause: the yellow substance of
the campaigns is not in the data. A regional split of the campaigns by
latitude and longitude was looked at (2026-11-16) and is not used: the
boxes were the author's, the northern European groups had 4 to 8
campaigns, and it was not planned.

Documents: DATA.md section 41 and `OPEN_QUESTIONS.md`'s third question;
NEXT_STEPS's item 13 of section 0d.

**2. What rests on the extension below 0.1 degree** (`OPEN_QUESTIONS.md`'s
second question). Petzold's report extends each vsf below 0.1 degree by a
power law and counts it in s, 3.4 to 14.5 percent at the eight stations
(DATA.md section 21), and `ScatteringFunction.mean_cosine` counts it at a
cosine of 1. Without it, the phase function is renormalised over 0.1 to
180 degrees and b becomes b (1 - f), f the share below 0.1 degree. From
the public API: the mean cosine (g - f) / (1 - f), the backscatter ratio
B / (1 - f), and the Henyey-Greenstein g for each of
`henyey_greenstein_fit`'s two methods (for the backscatter ratio, the HG
g whose backscatter is B / (1 - f), solved by bisection on HG's closed
form). And Kd, by the Monte Carlo: `petzold_sampler` gains an option to
start at 0.1 degree, off by default (when it draws the same numbers as
before; checked on a stored run). For each station, a = 0.1 per m, b/a of
0.5, 1, 3 and 10, the sun at 30 degrees, no sky: Kd over the first
penetration depth (i) as shipped, (ii) without the extension and b (1 - f)
(the light below 0.1 degree treated as unscattered), (iii) without it and
b kept (that light spread over 0.1 to 180 degrees). The same seed for the
three of each case.

What will be read off, decided now: the shift in mean cosine, B/S and the
HG g at each station; and, if (ii) moves Kd by less than 1 percent in
every case, the documents say Kd does not rest on the extension while the
mean cosine and g do; otherwise by how much it does.

Documents: `OPEN_QUESTIONS.md`'s second question; DATA.md section 21; the
example `phase_function_choice.py` gains a part (it is the example for
the reader who chooses a phase function); NEXT_STEPS's item 6 of section
0d.

**Version.** 1.15.8. Nothing shipped changes.

**Differences from the plan.**

- The plan quoted Aas & Højerslev (2001, p. 146) as saying that the
  relations on which Jerlov's classification rests are "valid only for the
  type of water from which they were obtained". On the page, that sentence
  is about their own relations for the Norwegian Sea (their Eqs. 9 and 10);
  of the relations behind the classification they say that the constants
  "may change from one oceanic area to another". DATA.md section 41 quotes
  each for what it is.
- `phase_function_choice.py` did not read `examples/data/` before; part 3
  does, and prints a note instead of the Kd when the runs are not there.
  The READMEs say so.

**What was found** (2026-11-16).

- Without the extension, the mean cosine falls by 0.004 to 0.015, B/S
  rises by 3.5 to 17.0 percent and the HG g of the backscatter fit falls by
  0.004 to 0.016 at the eight stations.
- Kd, by Monte Carlo over 32 cases: treating the light below 0.1 degree as
  unscattered moves it by -0.63 to +0.13 percent, under the 1 percent of
  the plan, so the documents say Kd does not rest on the extension;
  spreading that light over 0.1 to 180 degrees, b kept, moves it by +0.11
  to +4.40 percent.
- The example's first wording said the mean cosine and g rest on the
  extension "only in the third figure"; AUTEC 7's mean cosine goes from
  0.914 to 0.900, a change in the second. It now gives the size of the
  change.

**Added after the PR was opened** (2026-11-16). The user obtained and
supplied seven papers: Højerslev (1978), Højerslev & Aas (1991), Aas et
al. (2013) and Aas & Højerslev (2001) (the last two already read), and,
as possibly related, Topliss, Hunter & Simpson (1980), Kampa (1970) and
Jorde & Klavestad (1963). Read with the pages checked:

- Højerslev (1978), Limnol. Oceanogr. 23(5), 1076-1079,
  doi:10.4319/lo.1978.23.5.1076, p. 1078: "Jerlov's classification of
  coastal waters (Jerlov 1976) was selected for the purpose because it
  takes into consideration average optical conditions for coastal waters
  rich in yellow substance"; p. 1079: a daylight spectrum measured where
  the Baltic meets the Kattegat "is intermediate to and conforms with
  Jerlov's coastal types 3 and 5".
- Højerslev & Aas (1991), J. Geophys. Res. 96(C9), 17003-17005,
  doi:10.1029/91JC01822, pp. 17,003-17,004: the classification's values
  at 310 nm "seem to be based on six stations from the western Pacific and
  the Indonesian seas and one from the Mediterranean. These values were
  omitted in his last work [Jerlov, 1978], which may indicate that he
  doubted their representativity"; the Baltic, Kattegat, Skagerrak,
  German Bight and North Sea "are characterized by high contents of
  yellow substance".
- Topliss, Hunter & Simpson (1980), Mar. Environ. Res. 4, 65-79, p. 78:
  at one near-shore site in North Wales "all classes of coastal optical
  water type were present at some time of the year".
- Kampa (1970) is about the oceanic types in the eastern North Atlantic,
  and Jorde & Klavestad (1963) is part 4 of the Hardangerfjord series, on
  benthic algae, not Aas (1971), which is part 9; neither is used.

They add a contemporary of Jerlov's, from his institute, describing the
1976 coastal types as average conditions for coastal waters rich in
yellow substance, and the record that Jerlov dropped values he may have
doubted in 1978. They still state no reason for the coastal blue of 1976.
DATA.md section 41 and `OPEN_QUESTIONS.md`'s third question say so.

## 97. What the choice of pure water absorption does to the colour of the clearest water (1.15.9): the plan

`OPEN_QUESTIONS.md`'s first question puts numbers on how far the published
absorption spectra of pure water disagree (Pope & Fry over Mason et al.,
7.95 at 380 nm) and on what that does to a Jerlov type's absorption. It
does not say what it does to anything measured from above. The user chose
on 2026-11-16 to put it into the remote sensing reflectance of the
clearest water, which is the quantity Lee et al. (2015) inverted to get
theirs.

**The spectra.** The five the package ships: `pure_water_absorption_table`
with `pope1997`, `smith1981`, `mason2016` and `lee2015`, and
`pure_water_absorption()`, the aw Williamson & Hollins built their a on.
At 380, 400, 412, 443, 490, 510 and 550 nm, inside every one's range.

**Two waters**, so that the answer does not rest on one guess:

- (A) Pure seawater and nothing else: a = aw, bb = bbw = bw / 2, bw from
  Williamson & Hollins's Eq. 8a constants (0.00583 (400 / lambda)^4.322,
  `Water.source.scattering`). No particle is assumed. 380 to 550 nm.
- (B) Williamson & Hollins's IB, its contents on each aw: a = a_IB -
  aw_WH + aw, bb = bw / 2 + r (b - bw), as `Water.bb(particle_backscatter_
  ratio=r)` builds it. r is not known for any Jerlov type (DATA.md section
  10); all eight of Petzold's measured B/S, 0.013 to 0.044, are used. 412
  to 550 nm, where IB's a and b were measured (section 95 found IB's
  averaged a high in the blue; it is used as published).

**Rrs.** `lee2011_rrs` with the nadir coefficients (0, 0, 0); and, as a
second relation, `subsurface_rrs` with Gordon et al.'s (1988)
coefficients and `above_surface_rrs`. Warnings (Lee et al.'s fitted range
of bb / (a + bb)) are caught by type and reported.

**What will be read off, decided now.**

1. At each wavelength, the largest over the smallest Rrs among the five
   spectra, for (A) and, for each r, for (B).
2. For (B), the largest over the smallest Rrs among the eight r with Pope &
   Fry's aw. At each wavelength the documents say the choice of pure water
   moves Rrs more than the particles' backscatter ratio if the ratio of 1
   exceeds that of 2 for every r, less if it falls below it for every r,
   and otherwise that it depends on r.
3. The band ratios Rrs(443)/Rrs(550) and Rrs(412)/Rrs(550), which
   chlorophyll algorithms read: their range among the five spectra, for (A)
   and (B).
4. Whether the two Rrs relations agree on 1 to 3 within 10 percent; the
   documents use Lee et al.'s and say if they do not.

Nothing here says which spectrum is right.

**Documents.** `OPEN_QUESTIONS.md`'s first question; DATA.md section 29;
a part 8 of `examples/ocean_colour_and_secchi.py`; the figures in
`tests/test_quoted_figures.py`. No Monte Carlo: every number comes from the
package's own functions.

**Version.** 1.15.9.

**What was found** (2026-11-16), as read off in the plan:

1. Pure sea water: the five spectra give Rrs up to 6.85 times apart at 380
   nm, 4.90 at 400, 4.28 at 412, 2.62 at 443, 1.47 at 490, 1.18 at 510 and
   1.13 at 550. IB: 1.12 to 1.34 times, about the same for every r.
2. IB with Pope & Fry's water: the eight B/S move Rrs by 1.88 to 2.61
   times. At every wavelength from 412 to 550 nm the particles' ratio moves
   Rrs more than the choice of pure water, for every r.
3. Rrs(443)/Rrs(550): 10.73 to 24.75 in pure sea water, 2.03 to 2.84 in IB
   over all eight B/S; Rrs(412)/Rrs(550): 13.13 to 49.56 and 1.95 to 3.21.
4. Not within 10 percent everywhere. Gordon et al.'s relation gives IB's
   spreads within 3.3 percent and the same verdict at every wavelength,
   and pure sea water's within 5.7 percent from 443 nm; at 380 to 412 nm
   they differ by up to 26.4 percent. There pure sea water lies outside the
   bb / (a + bb) Lee et al. fitted (above 0.37) for Mason et al.'s and Lee
   et al.'s spectra at 380 to 412 nm and Williamson & Hollins's at 380 nm,
   and the package warns. The documents use Lee et al.'s relation and say
   so.

**Caught before the commit, by reading the output.** The example's first
wording said the violet figures "rest on an extrapolation of either
relation"; the package gives no fitted range for Gordon et al.'s, so it
now says only that they rest on Lee et al.'s outside its data, where the
two part.

## 98. Kd of the visible and of the whole shortwave from a and bb, and the euphotic depth (1.16.0): the plan

The user chose (2026-11-16) NEXT_STEPS's item 10 of section 0b, and then to
put it in the package, infrared and shortwave included. The papers, which
the user supplied, were read from their page images:

- Lee, Du, Arnone, Liew and Penta (2005), "Penetration of solar radiation
  in the upper ocean: A numerical model for oceanic and coastal waters",
  J. Geophys. Res. 110, C09019, doi:10.1029/2004JC002780. Not the Lee, Du
  & Arnone (2005) of `lee2005_kd` (C02016), which Lee et al. (2007) call
  2005a; this one they call 2005b.
- Lee, Weidemann, Kindle, Arnone, Carder and Davis (2007), "Euphotic zone
  depth: Its derivation and implication to ocean-color remote sensing",
  J. Geophys. Res. 112, C03009, doi:10.1029/2006JC003802.

**What they give.** With z the depth in metres and theta the sun's zenith
angle above the surface:

- Visible, 350-700 nm, energy, downwelling planar irradiance (2005, Eq. 7
  p. 5; Eq. 9 p. 6; Table 2 p. 7): K_VIS(z) = K1 + K2 / (1 + z)^0.5, the
  mean attenuation from 0 to z, with K1 = [chi0 + chi1 a(490)^0.5 + chi2
  bb(490)] (1 + alpha0 sin theta), K2 = [zeta0 + zeta1 a(490) + zeta2
  bb(490)] (alpha1 + alpha2 cos theta); chi = -0.057, 0.482, 4.221; zeta
  = 0.183, 0.702, -2.567; alpha = 0.090, 1.465, -0.667. Fitted to 300
  HydroLight runs: Pope & Fry's pure water, Petzold's average phase
  function, Gregg & Carder's sky, wind 5 m/s, the sun at 10, 30 and 60
  degrees (pp. 4-5); K_VIS 0.04-1.6 per m (p. 5); T_VIS 0.001-0.8, average
  error 9 percent above 0.003 (p. 7).
- Infrared, 700-2500 nm (Eq. 4 p. 3): K_IR(z) = [0.560 + 2.304 / (0.001 +
  z)^0.65] (1 + 0.002 theta), theta in degrees, fitted over 0.01-3 m and
  the sun 0-60 degrees, independent of the water.
- Shortwave (Eq. 11 p. 7): T(z) = F_VIS exp(-K_VIS z) + (1 - F_VIS)
  exp(-K_IR z), F_VIS the visible share of the shortwave just below the
  surface, which Lee et al. take as 0.424 from Mobley (1994).
- The depth where E_VIS is a fraction f of its surface value (2007,
  Eqs. 5-9 p. 3): with tau = -ln f, the smaller positive root of z^3 + y1
  z^2 + y2 z + y3 = 0, y1 = (K1^2 - K2^2 - 2 tau K1) / K1^2, y2 = (tau^2 - 2
  tau K1) / K1^2, y3 = tau^2 / K1^2. (Squaring K_VIS(z) z = tau gives
  exactly this cubic; checked by hand before the plan.) The paper takes
  E_VIS's depths for PAR's: different band, units and kind of irradiance,
  "less than 10%" apart in z (p. 4).

**The functions** (public; with no defaults; 1.16.0, a minor version):

- `lee2005_kvis(a490, bb490, depth_m, /, *, sun_zenith_deg)` -> K_VIS;
- `lee2005_kir(depth_m, /, *, sun_zenith_deg)` -> K_IR;
- `lee2005_shortwave_transmittance(a490, bb490, depth_m, /, *,
  sun_zenith_deg, visible_fraction)` -> T; `visible_fraction` has no
  default (Lee et al.'s 0.424 is Mobley's, and the share changes with the
  sky and the sun);
- `lee2007_depth_of_fraction(a490, bb490, /, *, sun_zenith_deg, fraction)`
  -> z; the euphotic depth is `fraction=0.01`.

They refuse what is not a number, inf and negative input, a fraction not
in (0, 1), and a sun not in [0, 90). Where K1 or K2 come out negative (K1
does for very small a: chi0 is negative) K_VIS can fall to or below zero
and the depth has no root; that is refused, not clipped. ProvenanceWarning
(the paper's own ranges): the sun outside 10-60 degrees (VIS) or 0-60
(IR); K_VIS outside 0.04-1.6 per m; T_VIS below 0.001; K_IR at depths
outside 0.01-3 m.

Tests: the coefficients against Table 2; the cubic's root put back into
K_VIS(z) z = tau; K_VIS at the surface and at depth from K1 and K2 by hand;
Eq. 4 at the surface; the refusals and warnings; scalars and arrays.

**Against what is shipped.** Solonenko & Mobley's (2015) a and b for all
ten types (inverted from Jerlov 1968, the edition of Table XXI), and
Williamson & Hollins's for IB-5C; bb = bw / 2 + r (b - bw) from each of
Petzold's eight B/S, since no source gives r for a type.

1. Jerlov (1977) quanta, 350-700 nm, 7 types: the depths of 30, 10, 3 and
   1 percent against `lee2007_depth_of_fraction`, the sun at 15 degrees
   for the oceanic types and 45 for the coastal (Solonenko & Mobley's
   Eq. 3 convention; Jerlov 1977's own sun is not recorded) and 0 to 60 as
   a factor. Read off: the ratio of the computed to the measured depth,
   and whether Jerlov's depth lies within what r and the sun make.
2. Jerlov (1968) Table XXI, the shortwave fraction against depth
   (`jerlov1968_solar_fraction`), the sun at the zenith for the oceanic
   types and 45 degrees for the coastal, as its footnote says, against
   `lee2005_shortwave_transmittance` with F_VIS = 0.424 (Lee et al.'s) and
   0.40 and 0.45 as a factor; and Paulson & Simpson's fit
   (`shortwave_parameters`) on the oceanic types. Read off: the ratio at
   each tabulated depth; at each depth, whether Lee et al.'s model or
   Paulson & Simpson's misses Table XXI by less, median over the oceanic
   types.
3. `par_profile`'s 1 percent depth (400-700 nm, Jerlov 1976 Kd, D65 as in
   `euphotic_zone.py`) beside both.

The 300-350 nm in Table XXI and not in Lee et al.'s 350-2500 nm is about 1
percent of the shortwave (Lee et al., p. 7); it is noted, not corrected.

**Where.** The VIS and euphotic functions in `jerlov/ocean_colour.py`
beside `lee2005_kd`; the IR and shortwave in `jerlov/shortwave.py`; parts
in `euphotic_zone.py` (1) and `solar_heating.py` (2); DATA.md section 42;
README, `docs/api.rst`, the CHANGELOG.

**Version.** 1.16.0: four public names.

**Differences from the plan.**

- 490 nm is not one of Solonenko & Mobley's or Williamson & Hollins's
  wavelengths; a(490) and b(490) are read between the tabulated ones, as
  `water(...).a(490)` does. The plan did not say how.
- E_VIS is called Ed (downwelling irradiance) in the 2005 paper and the
  "downwelling vector irradiance" in 2007; the docstrings give both, not
  the "planar" the plan said.
- Text that NumPy reads as a number ("0.1") is accepted for a490, bb490,
  depth_m, the sun and the fraction, as `lee2005_kd` already accepts it;
  only `visible_fraction` refuses it, with the check `_single` uses. The
  plan said non-numbers are refused; the shared helpers were not changed
  for this.
- The shortwave function warns of K_IR's fitted depths only above 0.01 m
  (not at 0, where T is 1 whatever K_IR is), and not below 3 m, where the
  paper says E_IR "is negligible" (p. 3). `lee2005_kir` warns at both.
- Comparison 2 reads off, besides the plan's ratios, how much F_VIS and r
  each move T. The F_VIS factor and the eight r were run; the sun was held
  at Table XXI's footnote, as planned.
- Comparison 3 (PAR's 1 percent depth from Jerlov's 1976 Kd) is printed
  in `euphotic_zone.py` part 7 for the 1 percent level only.

**What was found** (DATA.md section 42).

- Jerlov's (1977) quanta levels: Lee et al.'s depths are a median 1.13 of
  his with Solonenko & Mobley's a and b, and 0.91 with Williamson &
  Hollins's; r and the sun together move a depth by up to 2.4 times, and
  his depth lies within that in 38 of 48 cells. Outside: with Solonenko &
  Mobley's IOPs, the 1 percent level of IA and IB (too deep); with
  Williamson & Hollins's, every level of IB and II (too shallow). For I
  and IA the model from a and bb is nearer his 1 percent depth than PAR
  from his own (1976) Kd and D65 (1.23 and 1.28 against 1.62 and 1.43).
- Table XXI: at 1 m Lee et al.'s T is 0.91 to 1.08 of the table over the
  ten types, against Paulson & Simpson's 0.98 to 1.46 over the oceanic
  five; the model misses less than the fit in 3 or 4 of the five oceanic
  types at 1 to 10 m, and in at most 1 below. F_VIS of 0.40 and 0.45 moves
  T by 4.3 to 6.1 percent; r moves it more, for the turbid types from 2 m.
- Solonenko & Mobley's b(490) of I and IA rests on values flagged suspect
  and warns; with their I and IA, the model's K_VIS falls below 0.04 per m
  at the deeper levels, outside its fit, and warns.

## 99. The sea surface's reflectance factor rho, and Rrs from above-water radiances (1.17.0): the plan

The user chose (2026-11-16) NEXT_STEPS's item 8 of section 0b, supplied
both papers, and chose to ship both tables and how to read between their
points:

- Mobley (1999), "Estimation of the remote-sensing reflectance from
  above-surface measurements", Appl. Opt. 38, 7442-7455,
  doi:10.1364/AO.38.007442.
- Mobley (2015), "Polarized reflectance and transmittance properties of
  windblown sea surfaces", Appl. Opt. 54, 4828-4849,
  doi:10.1364/AO.54.004828.

**What they give.** Rrs = Lw / Ed (Eq. 1), and Lw is estimated as Lt -
rho Ls, Lt the radiance the radiometer sees looking at the sea and Ls the
sky radiance in the mirror direction (Eq. 4); with Ed from a grey plaque,
Rrs = (Lt - rho Ls) / (pi Lg / Rg) (Eq. 6). rho is "not an IOP of the sea
surface": it depends on the sun, the viewing direction, the wind, the sky
and the wavelength. The 1999 paper recommends viewing 40 degrees from the
nadir and 135 from the sun, and says rho = 0.028 there is acceptable only
below 5 m/s. The 2015 paper redoes rho with surfaces from wave spectra and
polarised ray tracing, for a single-scattering Rayleigh sky, and finds a
factor of two spread where the 1999 method gave less than 20 percent.

**The tables.** Neither paper prints its table. Both are on the Ocean
Optics Web Book ("Surface Reflectance Factors", page updated 2021-02-11;
the site is under a Creative Commons Attribution licence), downloaded
2026-11-16:

- `rhoTable_AO1999.txt` (MD5 aefcb0da753be57f5e84cdd6951ba76a): 550 nm,
  Cox-Munk surfaces, unpolarised, the Harrison & Coombes clear sky; wind
  0-14 m/s every 2, sun 0-80 degrees every 10; 118 viewing directions
  (nadir angle 0, 10, ..., 80 and 87.5; azimuth from the sun 0-180 every
  15), each the mean over a 10 by 15 degree quad. Its Theta is the
  direction of travel of the reflected photons from the zenith, which is
  the radiometer's angle from the nadir, and its Phi-view the azimuth from
  the sun. 8496 values.
- `rhoTable_AO2015.txt` (MD5 b24599f57b205435eaf95c161d624cf9): FFT
  surfaces, polarised ray tracing, Rayleigh single-scattering sky at 550
  nm, fully developed sea, the sun's rays along the wind; wind 0, 2, 4, 5,
  6, 8, 10, 12, 14 and 15 m/s, sun 0-80 every 10 and 87.5; the same 118
  directions. 11800 values. Its header calls it "a preliminary table for
  use during review" whose "final table will be placed online once the
  above paper has been accepted"; the page offers it as the 2015 paper's
  revised table. That is recorded, not resolved.

Checks made before the plan: the 2015 table gives 0.0179-0.0411 at 5 m/s
for the conditions of the paper's Fig. 18 (sun 30 and 60, azimuth 90 and
135, nadir 40), as the paper's text says, and 0.0449 at 10 m/s, sun 40,
(40, 135), the paper's 0.045; at 10 m/s it gives 0.0199-0.0457 where the
text says 0.0195-0.0458. The 1999 table gives 0.0336 at 10 m/s, sun 30,
(40, 135), where the paper's Table 1 prints 0.0337 for its clear sky; the
paper's runs were at 0, 2, 5, 10 and 15 m/s, the table's at 0 to 14 every
2.

**Shipped** as `jerlov/data/mobley1999_rho.csv` and
`mobley2015_rho.csv` (wind_speed, sun_zenith_deg, view_nadir_deg,
view_azimuth_deg, rho, every value as printed), written by
`tools/build_mobley_rho.py` from `sources/mobley_rho/`, which checks the
MD5s and the counts above. NOTICE and DATA.md give the source and the
licence; the files themselves are not in version control (sources/).

**The functions** (public, 1.17.0):

- `mobley_rho(*, source, wind_speed, sun_zenith_deg, view_nadir_deg,
  view_azimuth_deg)`: rho from one table, `source` "mobley1999" or
  "mobley2015" with no default. Wind and sun are interpolated linearly
  between the table's points; the viewing direction must be one of the
  table's (each value is a mean over its quad, so a value between quads
  would mix two fields of view); at nadir 0 the azimuth is not used.
  Outside the table's wind and sun, refused. Numbers or arrays that
  broadcast. The 550 nm and the sky each table assumes are in the
  docstring. The 2015 table gives a ProvenanceWarning, as its own header
  calls it preliminary; the 1999 table does not.
- `rrs_from_above_water(lt, lsky, ed, /, *, rho)`: (Lt - rho Lsky) / Ed,
  Eq. (1) with Eq. (4); rho has no default; negative results are kept
  (they say the rho was too large) and NaN passes. Mobley's Eq. 7 (taking
  off Rrs at 750 nm) is not applied; the docstring says so.

**Tests.** The counts, grids and MD5-checked values above; the checks
above against the papers; interpolation equal to the table at its points
and between two points linear; refusals (direction not on the grid, wind
or sun outside, no source, unknown source); the Rrs arithmetic.

**Example.** A part of `ocean_colour_and_secchi.py`: for Jerlov IB with
section 97's IOPs, Lt / Ed made from its Rrs plus rho Lsky / Ed, with
Lsky / Ed that of a uniform sky carrying Gregg & Carder's diffuse
irradiance (Lsky = Ed,diffuse / pi; a stand-in, said as such), then Rrs
recovered with rho from the 1999 table, the 2015 table and 0.028, at
(40, 135) and at (30, 90), and what QAA makes of each. Read off: the
error in Rrs at 443, 555 and 670 nm and in QAA's a(443).

**Documents.** DATA.md section 43; README; docs/api.rst; NOTICE;
sources/README.md; .zenodo.json; CHANGELOG. Version 1.17.0: two public
names.

**Differences from the plan.**

- A viewing azimuth outside 0-180 degrees is refused, not folded: the
  tables give 0-180 only, and neither paper says the field is symmetric
  about the sun's plane for every case (the 2015 one has the wind along
  the sun's rays).
- The wind, sun and viewing angles refuse NaN (they are conditions, not
  spectra); `rrs_from_above_water` lets NaN through as a gap, as the
  package does for spectra.
- The 1999 file lists its azimuths from 180 down; the build checks that
  every grid point is there once rather than their order.
- The example's 5 m/s lies between the 1999 table's 4 and 6 m/s and is
  interpolated. Recovering with the 2015 rho what the 1999 rho made gives
  a negative Rrs(670), which QAA refuses; the example prints that rather
  than an a(443). Its atmosphere repeats that of `sunlight_and_d65.py`,
  with tools/sm_closure.py's aerosol, as an example may not import a tool.

**What was found** (DATA.md section 43).

- The 2015 table reproduces the paper's 0.0179-0.0411 at 5 m/s and its
  0.045 of Fig. 19, but at 10 m/s gives 0.0199-0.0457 against the text's
  0.0195-0.0458; its header calls it preliminary.
- The 1999 table gives 0.0336 where the paper's Table 1 prints 0.0337, and
  its winds (0-14 every 2) are not the paper's runs (0, 2, 5, 10, 15).
- At (40, 135), sun 30, 5 m/s: 0.0283 and 0.0411. In Jerlov IB, with a
  uniform sky's Lsky / Ed, the choice of table moves Rrs by 16, 71 and 619
  percent at 443, 555 and 670 nm and QAA_v6's a(443) by 37 percent, or
  makes Rrs(670) negative; at (30, 90) the tables differ by 0.0018, and
  recovering with one what the other made is off by 2 to 88 percent.

## 100. Scatter correction of reflective-tube absorption measurements (1.18.0): the plan

The user chose (2026-11-16) all four of NEXT_STEPS section 0b's B items
still open; this is item 9. Read: Röttgers, McKee & Woźniak (2013),
"Evaluation of scatter corrections for ac-9 absorption measurements in
coastal waters", Methods in Oceanography 7, 21-39,
doi:10.1016/j.mio.2013.11.001, which states the methods as equations and
tests them against a PSICAM. Zaneveld, Kitchen & Moore (1994), "The
scattering error correction of reflecting-tube absorption meters", Proc.
SPIE 2258, 44-55, doi:10.1117/12.190095, the origin of the proportional
method, has been asked of the user; what it adds is recorded when it is
read.

**What Röttgers et al. give** (their Table 1 and Eqs. 1-5; am and cm the
absorption and attenuation the instrument reads after its temperature,
salinity and pure-water corrections; 715 the ac-9's reference channel):

- flat (Eq. 1): a = am - am715
- proportional (Eq. 2b; 2a with ec = 1): a = am - am715 [(1/ec) cm - am]
  / [(1/ec) cm715 - am715]
- flat+ (Eq. 3): a = am - (am715 - a715)
- proportional+ (Eq. 4): a = am - (am715 - a715) [(1/ec) cm - ac] /
  [(1/ec) cm715 - a715], ac "either am or a" (they found the difference
  negligible)
- a715 estimated from am715 (Eq. 5): a715 = 0.212 am715^1.135 (n = 85,
  r2 = 0.930, natural samples, cultures left out)
- ec: 1 (no correction of the attenuation) or 0.56, which they took from
  Boss et al. (2009) for turbid water and the ac-9's 0.93-degree
  acceptance angle.

Eq. 4 with a715 = 0 does not become Eq. 2b: the denominators differ by
am715. Each is implemented as printed, under its own name, and the
difference is recorded (DATA.md section 44).

**The functions** (public; no defaults):

- `rottgers2013_scatter_correction(am, cm, am_ref, cm_ref, /, *, method,
  ec=None, a_ref=None)`: method one of "flat", "proportional", "flat+",
  "proportional+"; ec required for the proportional methods and refused
  for the flat ones; a_ref (the true absorption at the reference
  wavelength) required for the "+" methods and refused for the others.
  In proportional+, ac is am (measurable). The reference wavelength is
  the caller's: am_ref and cm_ref are values.
- `rottgers2013_a715(am715, /)`: Eq. 5, with a ProvenanceWarning where
  am715 lies outside the range of their natural samples' fit (read from
  their Fig. 4: about 0.02 to 8 per m), since the fit is theirs and for
  715 nm on an ac-9.

Refused: inf, a negative or zero denominator; NaN passes as a gap.

**Tests.** Each equation by hand; ec = 1 makes Eq. 2b into Eq. 2a; a715 =
0 in Eq. 3 gives Eq. 1; Eq. 4 with a715 = 0 is not Eq. 2b (the recorded
difference); Eq. 5 at points; refusals.

**Example.** `from_one_measurement.py` gains a part: with a and b of
Jerlov types and each of Petzold's eight VSFs, am and cm made by losing
the light scattered beyond the reflective tube's angle (from Zaneveld et
al. 1994, once read) and gaining that within the c-meter's 0.93 degrees,
and a(715) of the type; then a recovered by each method. If Zaneveld et
al. cannot be had, the example is left out and that is said.

**Documents.** DATA.md section 44; README; docs/api.rst; CHANGELOG;
.zenodo.json. 1.18.0: two public names.

**Differences from the plan.**

- Zaneveld et al. (1994) arrived before the code was finished (the user
  supplied it with three other papers). Their Eq. (21) is Röttgers et
  al.'s Eq. (2a); they derive it with the reference at 712 nm.
- The example's tube is Zaneveld et al.'s: 0.25 m, a perfect reflector up
  to 41 degrees (the R = 100 percent case of their Eqs. 5-6, so no
  reflection counts are needed), a = 0.4 per m. The c-meter's 0.93
  degrees is Röttgers et al.'s, after Boss et al. (2009). The true a(715)
  is set to 0, 0.002 and 0.01 per m, not taken from a type: Williamson &
  Hollins's a(715) is itself a corrected measurement.
- The example integrates with its own trapezoid rule, as numpy.trapezoid
  is NumPy 2 only, and passes on any warning but Eq. (5)'s.

**What was found** (DATA.md section 44).

- With a(715) = 0, Eq. (4) is not Eq. (2b): the correction differs by
  (cm715 - am715) / cm715, and in the example proportional+ is then off by
  2.6 to 9.9 percent where proportional is exact.
- From Petzold's stations, ea is 5.7 to 12.5 percent; HAOCE 11's 5.7
  matches Zaneveld et al.'s "Coastal mixed", the others are not
  identified. ec within 0.93 degrees is 16 to 27 percent, larger than any
  of Zaneveld et al.'s Mie models at 0.9 degrees.
- With a(715) = 0.01 per m in Jerlov III, the flat and proportional
  methods fall 28 to 40 percent short at 555 and 676 nm.

## 101. Morel's (1988) Kd from the pigment concentration, as a second edition beside 2001 (1.19.0): the plan

NEXT_STEPS section 0b, B, item 11, chosen by the user with the rest of B
(2026-11-16); the paper supplied by the user: Morel, A. (1988), "Optical
modeling of the upper ocean in relation to its biogenous matter content
(case I waters)", J. Geophys. Res. 93(C9), 10749-10768,
doi:10.1029/JC093iC09p10749.

**What it gives.** K(lambda) = Kw(lambda) + chi(lambda) C^e(lambda) (Eq. 9,
p. 10,753), Kw = aw + bw/2 for pure sea water (Eq. 8), with Table 2 (p.
10,754): Kw, chi and e every 5 nm from 400 to 700 nm, 61 rows, from 176
K spectra. C is the pigment concentration, Chl a + Pheo a, mg m^-3,
averaged over the layer; Morel & Maritorena (2001) use Chl a (+ divinyl
Chl a) by HPLC. The paper runs the model from 0.03 to 30 mg m^-3 (Figs.
10, 12, 13). Beyond 650 nm "the chi and e values ... are only extracted
from the mesotrophic and eutrophic waters" (p. 10,755), and Fig. 6 shows
the number of spectra falling from about 170 to few there.

Table 2 was read from the page image and the text layer, which agree in
all 61 rows. Checked before the plan: Kw(450) = 0.0168 is the 0.0168 of
Fig. 7a's ordinate, K450 - 0.0168. And: Morel & Maritorena's (2001) chi
and e are the 1988 values exactly from 560 nm to 700 nm (29 rows), where
DATA.md section 27 says, after their p. 7168, "beyond 590-600 nm"; their
Kw differs at every wavelength. This also explains section 27's
unexplained rounding of chi and e from 560 nm.

**Shipped.** `jerlov/data/morel1988_kd.csv` (wavelength_nm, Kw_per_m,
chi_per_m, e_exponent, status, note), from literals in
`tools/build_morel1988.py`, which checks the Fig. 7a value and that 560-
700 nm equal the shipped `morel2001_kd.csv`'s chi and e. Rows above 650 nm
carry a note.

**Function.** `morel1988_kd(wavelengths, /, *, pigment_mg_m3)`: as
`morel2001_kd`, linear between the 5 nm points, 400-700 nm, refused
outside; the argument named for what it is (Chl a + Pheo a), no default;
a ProvenanceWarning outside 0.03-30 mg m^-3, and beyond 650 nm.

**Example.** A part of `ocean_colour_and_secchi.py`: the two editions'
Kd at 0.03, 0.3, 3 and 30 mg m^-3, at 412, 443, 490, 555 and 670 nm,
their ratio, and where the difference lies (Kw below 560 nm; chi and e
also below 560 nm; only Kw above). The nearest Jerlov type for each, as
part 4 does for 2001.

**Documents.** DATA.md section 45, and section 27 corrected (its "590-600"
and its rounding note) with a pointer; README; docs/api.rst; CHANGELOG;
.zenodo.json. 1.19.0: one public name.

**Differences from the plan.**

- The example's split of the change at 412 nm takes Kw as each function
  at a vanishing C (1e-12 mg m^-3), under a suppressed warning, rather
  than reading the tables; the difference is below 1e-8 per m.
- The example records the 1988 function's own warning beyond 650 nm and
  says it in its text rather than adding it to part 8's list, which is of
  the warnings the other parts report.

**What was found** (DATA.md section 45).

- Morel & Maritorena's (2001) chi and e equal Morel's (1988) from 560 nm,
  29 rows; section 27's "beyond 590-600 nm" was their text, not their
  table, and is corrected there with a pointer.
- At 0.03 mg m^-3, 2001's Kd is 0.69 of 1988's at 412 nm; the change in
  Kw is 1.23 times the whole change. At 0.3 and above the editions agree
  within 9 percent from 412 to 670 nm, and give the same nearest Jerlov
  type; at 0.03 they give IA (1988) and I (2001).

## 102. The clearest natural waters: Morel et al. (2007) (1.20.0): the plan

NEXT_STEPS section 0b, B, item 12; the paper supplied by the user: Morel,
Gentili, Claustre, Babin, Bricaud, Ras and Tièche (2007), "Optical
properties of the 'clearest' natural waters", Limnol. Oceanogr. 52(1),
217-229, doi:10.4319/lo.2007.52.1.0217. Measurements in the South Pacific
gyre (BIOSOPE, November 2004).

**What it gives in tables** (the Kd and R spectra are figures only):

- Table 1 (p. 220): eight stations, STB-4 to STB-15: position and date;
  [Chl] at 5 m and at 30-40 m; Zeu; the depth and [Chl] of the deep
  maximum; Kd at 420 and 310 nm; ap at 420 and 310 nm; Rmax and its
  wavelength; derived atot at 420 and 310 nm and ay1 and ay2 at 310 nm.
- Table 2 (p. 224): aw1, 300-500 nm every 5 (Buiteveld et al. 1994 from
  Boivin et al. 1986 below 366 nm, Pope & Fry 1997 from 420 nm, a smooth
  join between); aw2, 300-370 nm (from Quickenden & Irvin 1980, joined
  at 366 nm); bsw, 300-500 nm (Buiteveld et al. times 1.30 for salt);
  bbsw = bsw / 2. They call aw1 and aw2 a "tentative upper bound" for pure
  water from in situ data.

Checks made before the plan: ay2 - ay1 at 310 nm should be aw1(310) -
aw2(310) = 0.0183 for every station, since atot and ap are shared; it is
0.0182 for six and 0.0082 for GYR-5 and STB-14, so one of their ay values
is likely misprinted by 0.0100. The Fig. 5 caption gives Morel &
Maritorena's (2001) Kbio(420) = 0.1227 [Chl]^0.659, which is their Table
2's chi and e at 420 nm rounded. Table 2's aw from 420 nm should be Pope
& Fry's: to be checked against the shipped pope1997_aw.csv.

**Shipped.** `jerlov/data/morel2007_aw.csv` (wavelength_nm, aw1_per_m,
aw2_per_m, bsw_per_m, status, note) and `morel2007_stations.csv`
(station, then the quantities of Table 1, one column each, with status
and note), from literals in `tools/build_morel2007.py`, which runs the
checks above. The two ay2 values are `suspect`, kept as printed.

**Public.**

- `pure_water_absorption_table` gains `"morel2007"` (aw1, 300-500 nm)
  and `"morel2007_aw2"` (aw2, 300-370 nm); bsw is in the table, not
  returned.
- `morel2007_stations()` -> a tuple of `ClearWaterStation` (frozen
  dataclass, the quantities of Table 1 as attributes, with units in the
  names); a flagged value comes with a ProvenanceWarning when read
  through the function's records' `statuses`.

**Example.** A part of `ocean_colour_and_secchi.py`: each station's
Kd(420) beside Morel & Maritorena's (2001) and Morel's (1988) Kd at its
[Chl] at 5 m, Jerlov's (1976) type I, Austin & Petzold's (1986) type I
and pure sea water (aw + bsw / 2, from each pure water table that covers
420 nm). Read off: how much lower the clearest waters are than Jerlov I.

**Documents.** DATA.md section 46; README; docs/api.rst; CHANGELOG;
.zenodo.json. 1.20.0: two public names.

**Differences from the plan.**

- The caption's "the values beyond 420 nm are those of Pope and Fry" was
  checked and does not hold at 425, 435, 445 and 455 nm, where aw1 is the
  mean of Pope & Fry's neighbours; the build checks that instead.
- `morel2007_stations()` warns on every call while two rows are suspect,
  as `water()` does for flagged values, rather than through the records.
- The example's pure sea water is the paper's own aw1 + bsw / 2 at 420 nm,
  not every pure water table: bsw is theirs, and the others would mix
  scattering of another salinity.

**What was found** (DATA.md section 46).

- ay2 - ay1 at 310 nm is 0.0100 short at GYR-5 and STB-14: a likely
  misprint, flagged.
- aw1 is Pope & Fry's at every 10 nm from 420 nm, and the mean of their
  neighbours at 425-455 nm.
- The stations' Kd(420) is 0.52 to 0.99 of Jerlov's type I, below Austin
  & Petzold's pure sea water at seven of eight, and 0.71 to 0.97 of Morel
  & Maritorena's Kd at the same chlorophyll.

## 103. The f and Q factors for a nadir view: Morel et al. (2002), Appendix B (1.21.0): the plan

NEXT_STEPS section 0b, B, item 7; the paper supplied by the user: Morel,
Antoine & Gentili (2002), "Bidirectional reflectance of oceanic waters:
accounting for Raman emission and varying particle scattering phase
function", Appl. Opt. 41(30), 6289-6306, doi:10.1364/AO.41.006289.

**What can be had.** The full tables of f and f/Q (7 wavelengths, 6 sun
angles, 6 Chl, 17 nadir angles by 13 azimuths) are on an anonymous ftp
server (oceane.obs-vlfr.fr, Appendix A) that does not answer from here.
Appendix B prints, for the radiance from the nadir (theta' = 0) and with
Raman emission included, linear fits in (1 - cos theta_s):

- Eq. (B1), Table 1: f(theta_s) = f0 + Sf (1 - cos theta_s), "within
  this domain" 0 < theta_s < 60, departure from linearity "less than 0.5%
  when theta_s < 45 deg and may reach 2% in some cases (when theta_s =
  60 deg)";
- Eq. (B2), Table 2: Qn(theta_s) = Q0 + SQ (1 - cos theta_s), 0-60
  degrees, "the relative error always remains below 1%";
- Eq. (B4), Table 3: (f/Qn)(theta_s) = f0/Q0 + Sf/Q (1 - cos theta_s),
  acceptable "even as great as theta_s = 75 deg", relative errors "might
  reach +-3.4%";
- Eq. (B3): [Lw]N^ex = [Lw]N (f0/Q0) (f/Qn)^-1, the exact normalised
  water-leaving radiance for the in-water (nadir) method.

Each for 412.5, 442.5, 490, 510, 560, 620 and 660 nm and Chl 0.03, 0.1,
0.3, 1, 3 and 10 mg m^-3, case 1 water. f is that of R = Eu/Ed = f bb/a
(Eq. 11), Q = Eu/Lu (Eq. 10). The 252 numbers were read from the text
layer and checked against the page images (including the minus signs of
Sf/Q at 0.03 and 0.1 mg m^-3).

**Checks the paper allows.** Table 3's f0/Q0 against Table 1's f0 over
Table 2's Q0 (separate fits, so close, not equal); the paper's ranges:
f0/Q0 "0.08-0.12", in the blue "between 0.086 and 0.097", Q0 "from
approximately 3.1 to 4.4"; and its Eq. (17), Qn = 5.20 - 1.82 cos theta_s
from measurements at 490 nm and Chl 0.1 mg m^-3, which the paper says
agrees with its predictions over 0-45 degrees.

**Shipped.** `jerlov/data/morel2002_nadir_fq.csv` (quantity, chl_mg_m3,
wavelength_nm, value; 6 quantities x 6 x 7 = 252 rows), from literals in
`tools/build_morel2002.py`, which runs the checks.

**Public.** `morel2002_nadir_fq(wavelength_nm, /, *, chlorophyll_mg_m3,
sun_zenith_deg)` -> `NadirFQ` (frozen dataclass: f, q, f_over_q (B4), and
`correction` = (f0/Q0) / (f/Qn) of Eq. B3 from B4). The wavelength and the
Chl must be the table's own (the paper fitted each separately and gives
no rule between them); the sun 0 to 75 degrees, with f and q NaN above 60
(not fitted there) and a ProvenanceWarning from 60 on. Scalar inputs.

**Example.** A part of `ocean_colour_and_secchi.py`: the correction of Eq.
(B3) for the sun at 0-75 degrees and each Chl, at 412.5 and 560 nm;
Eq. (17) against Table 2 at 490 nm; Table 3 against Tables 1 and 2.

**Documents.** DATA.md section 47; README; docs/api.rst; CHANGELOG;
.zenodo.json. 1.21.0: two public names.

**Differences from the plan.**

- The text's "0.08 - 0.12" for f0/Q0 is rounded: the table goes to
  0.078632. The build checks the table's own range, and DATA.md section
  47 says so.
- Eq. (17) is Aas & Højerslev's from 465-474 nm; the paper compares it
  with its values at 490 nm and 0.1 mg m^-3, and so does the example.

**What was found** (DATA.md section 47).

- Table 3's f0/Q0 is within 1.37 percent of Table 1 over Table 2.
- Table 2 is within 2.6 percent of Eq. (17) at 0-45 degrees.
- The correction of Eq. (B3) is within 0.22 percent of 1 at 0.1 mg m^-3
  at 412.5 and 560 nm (0.52 percent at the worst wavelength),
  falls to 0.825 at 560 nm, 10 mg m^-3 and the sun at 75 degrees, and
  rises to 1.034 at 0.03 mg m^-3 there.

## 104. Morel et al.'s (2002) full f/Q tables, read from the user's own copy (1.22.0): the plan

Section 103 left the views other than the nadir out: their tables are on
the authors' anonymous ftp server, which did not answer from the
container. The user fetched them from their own machine (2026-11-16):
`ftp://oceane.obs-vlfr.fr/pub/gentili/AppliedOptics2002/`, two files,
`DISTRIB_fQ_with_Raman.tar.gz` (173,005 bytes, MD5
21c7afc6c6d3c1963311d6880456f7bc, dated 18 June 2003) and
`lin-approx.tar` (10,240 bytes, MD5 f003e7f20a5d464ebbda2dcf21690c68). The
second is also inside the first, byte for byte.

**What is in it.** README_FIRST, foQ.info, f.dat, D_foQ_pa/ (252 files,
foQ_<wavelength>_<sun>_<Chl>, each 17 nadir angles by 13 azimuths, values
to four decimals), rgoth_Ebuchi.dat (the surface factor, 91 nadir angles
0-90 for winds 00, 04, 06, 08, 16 and "xx", a flat ocean), lin-approx.tar,
a Fortran reader and its reference output. Only the tables with Raman
emission are distributed, though the paper describes two sets. Nadir
angles in water 1.078, 3.411, ..., 48.83 degrees; "the value for the
first nadir angle (1.078 deg) is to be used for theta' = 0" (paper,
Appendix A); azimuths 0-180 every 15, with the README's convention:
0 when the sensor and the sun are on opposite sides of the vertical, 180
on the same side.

**Licence.** No file states one; the README gives only a contact
address. The user chose (2026-11-16) not to ship the tables: the package
reads the user's own copy of the archive, checks its MD5, and refuses
another. `sources/README.md` and DATA.md say how to get it.

**Checks made before the plan.** The six tables of lin-approx.tar equal
the shipped `morel2002_nadir_fq.csv` (the paper's printed Appendix B) in
all 252 values. f.dat at theta_s = 0 is within 0.62 percent of Table 1's
f0, and the f/Q of the first nadir row at theta_s = 0 within 1.19 percent
of Table 3's f0/Q0: fits against the values they were fitted to. The
paper says the surface factor was given "for wind speeds W = 0, 4, 10,
and 16 m s^-1"; the file has 0, 4, 6, 8 and 16 and a flat surface, and
no 10.

**Public.** `morel2002_fq_tables(path, /)` -> `Morel2002FQTables`, which
reads the archive (no extraction) and offers:

- `f(wavelength_nm, *, sun_zenith_deg, chlorophyll_mg_m3)`;
- `f_over_q(wavelength_nm, *, sun_zenith_deg, chlorophyll_mg_m3,
  nadir_deg, azimuth_deg)`; nadir_deg one of the table's or 0, which
  takes the 1.078 row as the paper says;
- `surface_factor(*, wind, nadir_deg)`, the R-gothic of rgoth_Ebuchi.dat,
  wind one of "flat", 0, 4, 6, 8, 16.

Every argument must be one of the table's own values (the paper gives no
rule between them), no defaults. A wrong MD5 is refused with how to get
the right file.

**Tests.** The reading and the checks above, on a small archive of the
same layout built in the test with its MD5 patched in; and, where
`sources/morel2002/DISTRIB_fQ_with_Raman.tar.gz` exists (never in CI),
the real archive against the figures quoted.

**Documents.** DATA.md section 48; sources/README.md; README;
docs/api.rst; CHANGELOG; .zenodo.json. 1.22.0: two public names.

**Differences from the plan.**

- No example: the archive is not in CI, and an example that needs a file
  the reader must fetch would not run there. The README shows the call.
- The test of the real archive reads lin-approx.tar from inside the
  archive and compares it with the shipped Appendix B, value by value.

**What was found** (DATA.md section 48).

- The paper's printed Appendix B equals the distributed lin-approx.tar in
  all 252 values.
- f.dat at a zenith sun is within 0.62 percent of Table 1's f0, and the
  nadir row of f/Q within 1.19 percent of Table 3's f0/Q0.
- R-gothic is for winds 0, 4, 6, 8 and 16 m/s and a flat sea; the paper
  says 0, 4, 10 and 16.

## 105. A review after 1.22.0: small inconsistencies, and Eq. (B1) against the archive's own f (1.22.1): the plan

A review of the functions added in 1.16.0-1.22.0 (the review of section
80 went up to 1.10.1, that of section 88 to 1.15.0) found no wrong value.
It found the inconsistencies below, and one thing about the data. No
shipped value changes; 1.22.1 is a patch release.

**1. `morel2002_nadir_fq` is the one positional-only public function
without `_data.positional_only()`.** All the others (50, of which those
added since 1.0 by the practice of section 86's "Differences from the
plan") take a keyword for the positional argument with a FutureWarning;
this one raises TypeError. It gets the decorator. Only calls that failed
now work, with the warning.

**2. Its docstring still says the full tables are "on a server this
package could not reach".** Since 1.22.0 they are read by
`morel2002_fq_tables`; the docstring says so.

**3. Its arguments are checked with `float()`**, which takes text
("412.5") and gives a NaN a message about the table's wavelengths. It
takes the check every other function of one number uses: one finite
number, else ValueError. Text, which the docstring never offered, is
refused from 1.22.1. A refusal of an input that was never offered is
what section 81 did with infinity in a patch release.

**4. One check, three copies.** `sky._number`, `absorption_meter._number`
and `fq_tables._one` are the same function. They become one,
`_data.finite_number`, with the same message; `morel2002_nadir_fq` uses
it too. As before it accepts what NumPy counts as a number, a bool among
them; refusing bools everywhere is not this release's change.

**5. The flat methods of `rottgers2013_scatter_correction` keep a gap in
cm.** `cm` is not used by Eqs. (1) and (3), but the result is NaN where
cm is NaN. The behaviour stays (a patch changes no value): a gap at one
wavelength of the measurement is a gap in what the measurement gives
there, whatever the method. The docstring says it, and a test pins it.

**6. A NaN wavelength is refused with a message about the range.**
`morel2001_kd`, `morel1988_kd`, `bricaud1995_aph` and `morel2001_bbp`
say "wavelengths must lie within 350-700 nm" for a NaN. They say
"wavelengths must be numbers, not NaN" first, the words of
`water._require_number`. Still ValueError.

**7. Eq. (B1) against the archive's own f.dat, with the sun away from
the zenith.** Found during the review, before this plan: the paper says
Eq. (B1) departs from the values it was fitted to by "less than 0.5%
when theta_s < 45 deg" and up to 2 percent at 60; section 104 compared
f.dat with it at a zenith sun only (0.62 percent). Over the 42 cases of
each sun angle, Eq. (B1), whose coefficients equal the archive's
lin-approx.tar, departs from f.dat by up to 0.47 percent at 15 degrees,
1.10 at 30 (13 of 42 above 0.5), 2.70 at 45 (26 of 42 above 0.5, 2 above
2; 660 nm, 0.03 mg m^-3) and 1.29 at 60. The largest is at 45, not at
60: not the shape of a linear fit's error growing with 1 - cos theta_s.
The same comparison for Eq. (B4) against the first nadir row of the f/Q
tables is made after this plan and recorded as it comes out. Recorded in
DATA.md section 48 (a new bullet, no new section) and in the docstring
of `morel2002_nadir_fq`; why they differ is not known (the archive is
dated June 2003, the paper October 2002), and is not guessed at.

**Tests.** Every public function with a positional-only parameter is
wrapped by `positional_only` (a test over `jerlov.__all__`, so that the
next one cannot be missed); `morel2002_nadir_fq` by keyword gives the
same value with a FutureWarning, and refuses text and NaN; the flat
methods keep a gap in cm; a NaN wavelength in the four functions; the
figures of item 7 where the real archive exists (never in CI, as in
section 104).

**Documents.** CHANGELOG; DATA.md section 48. No new public name; the
README and the Zenodo description are unchanged.

**Differences from the plan, noted after the code was written.**

- Eq. (B4) against the first nadir row of the f/Q tables, over the 42
  cases by 13 azimuths, came out as: up to 1.20 percent at 0 degrees,
  0.74 at 15, 0.43 at 30, 3.34 at 45, 1.61 at 60, 1.66 at 75; within
  the paper's "+-3.4%", but largest at 45, as for Eq. (B1).
- Not in the plan: since both fits depart most at 45, f.dat at 45 was
  compared with the straight line in 1 - cos theta_s between its own 30
  and 60 degree values. It lies 3.44 percent below at 660 nm, 3.00 at
  620 and 2.25 at 560 (0.03 mg m^-3), more than 1 percent below in 7 of
  42 cases, and up to 1.22 percent above (412.5 nm, 10 mg m^-3). The
  fits are linear in 1 - cos theta_s and cannot follow that. Recorded in
  DATA.md section 48 and tested with the rest.
- The plan's item 7 cited the 45-degree figure against the paper's
  "less than 0.5% when theta_s < 45 deg"; the case that bound covers is
  30 degrees, where Eq. (B1) departs by up to 1.10 percent. CHANGELOG
  and DATA.md say it that way.
- The tests of items 1, 3, 4, 5 and 6 are in a file of their own,
  tests/test_third_review.py (as test_review_fixes.py and
  test_second_review.py for the earlier reviews); those of item 7 in
  tests/test_fq_tables.py beside section 104's.
- The three modules keep their local names for the check (`_number`,
  `_one`), imported from `_data`, so that their calls are unchanged.

## 106. The README as an introduction, its topics on the site, and a map of which function to use (1.22.2): the plan

Since 1.0.1 (section 63) the README has grown with every release to 782
lines. Most of it is a tour of the package by topic, which the site
already renders better and which PyPI shows as one long page. There is
also no place that says, for a quantity a reader wants, which of the
functions gives it: Kd alone comes from `Water.kd`, `kd_spectrum`,
`morel2001_kd`, `morel1988_kd`, `lee2005_kd`, `lee2013_kd` and
`gordon1989_kd`, each for a different starting point. The user chose
(2026-11-17) to settle the documents before adding functions, leaving
the JOSS paper for later. 1.22.2 changes documents and tests only; no
code, value or public name changes.

**1. The README becomes an introduction.** It keeps what a reader needs
before installing: what the package is, what it claims and what not,
installing and a first call, why the source is an argument, what it will
not do, provenance warnings, the table of sources, a list by topic of
what it covers with a link to each topic's page on the site, the
examples, where provenance and design are recorded, contributing,
licence and citation. Every other section moves, with its text as it
stands, to the site.

**2. The topics go to `docs/topics/`, six pages** in reStructuredText,
converted from the README's Markdown without rewriting the text:

- `seeing_through_water`: looking at something through water, looking
  up or down, the Akkaynak-Treibitz coefficients, what colour is that,
  how far apart two colours are to an eye;
- `measurements`: measured backscattering, Petzold's scattering
  functions, the USGS reflectances, which type a water is nearest, other
  entry points;
- `depth_and_light`: the type changing with depth, light for
  photosynthesis, Jerlov's quanta, Tyler's radiance, the fluctuations;
- `ocean_colour`: without a water type (chlorophyll, a and bb, f/Q, Rrs,
  the Secchi depth, QAA), and the light at the surface under a clear sky;
- `other_software`: water for a renderer, water for a radiative transfer
  code;
- `solar_heating`: the upper ocean's heating.

They differ from the guides (section 63): a guide is a worked
calculation whose every printed number is a doctest; a topic page shows
the calls with the reader's own inputs, as the README did, and is not
run. The index lists them under their own heading.

**3. A map of which function to use, `docs/choosing.rst`.** Tables by
what the reader wants (the IOPs of a type, Kd, the light at depth, PAR
and the euphotic zone, reflectance and ocean colour, from a measurement,
colour and vision, for other software, the surface, heating, data to
check against), each row: what you have, the function, the paper. It
says how the functions for one quantity differ, from their docstrings,
and gives no number of its own other than years, so that it states
nothing a test does not check. Each name links to the API reference.

**4. Tests follow the text.** A test that reads a figure from the README
reads it from the page the text moved to; the figure and the regular
expression stay the same, except where Markdown's `code` becomes
reStructuredText's ``code``. `test_the_README_names_only_what_exists`
keeps its check that every `jerlov.<name>` in the README exists and is
public; its requirement of more than 40 names and of seven named
functions moves to the map, where it becomes stronger: every public
function, and `Water` and `Scene`, is on the map, and every name the map
or a topic page links to exists and is public. The topic pages are all
in the index, and the site builds with `-W` as before.

**Not done here.** The README is not otherwise rewritten; the topics'
text is not revised; no example changes. The JOSS paper waits (NEXT_STEPS
section 1).

**Differences from the plan, noted after the pages were written.**

- One sentence of the topics' text was changed: the solar heating page
  said "nothing to do with the spectral quantities above", which on a
  page of its own pointed at nothing; it says "on the other pages".
  The rest is as the README had it, including sketches that use names
  the README had set earlier (`w`, `wl`, `surface`).
- The README's check of names also takes the names it writes in
  backticks without `jerlov.`, since the list of topics names functions
  that way; it needs more than 5, not 40.
- The map's rows were checked against each function's docstring before
  they were written. Two were narrowed: `Water.bb` is from the source's
  b and, with bbp/bp, Haltrin's term for pure water (not "Haltrin as
  each source uses it"); and a sentence saying the Kd of a type and of
  Morel's models are "spectral values of the water itself" was dropped,
  since no docstring says it.
- The README is 213 lines.

## 107. The attenuation of light kept within an angle: forward scattering from Petzold's measurements (1.23.0): the plan

Section 13 left forward scattering out: c counts every scattered photon
as lost to the beam, and a blurred image needs the whole phase function,
which no Jerlov type determines. Since then the package ships Petzold's
measured volume scattering functions (section 27), and section 96 looked
at their extension below 0.1 degree. An experiment outside the package
(the user's, 2026-11-17, NEXT_STEPS section 5) put Jerlov types into a
real-time renderer's single-scattering fog, which attenuates with c, and
the water lost the look of clarity; part of that is that light scattered
by a small angle still reaches the eye near where it came from. The user
chose (2026-11-18) to add the lightest of the three options recorded
then: the attenuation of light kept within a half-angle.

**The quantity.** For a beam and a receiver that accepts light within a
half-angle theta0 of the beam's direction, single scattering gives

    c_within(theta0) = c - b(< theta0),
    b(< theta0) = 2 pi integral from 0 to theta0 of vsf(theta) sin(theta)

It is what a transmissometer with that acceptance angle reads, and it
lies between c (theta0 = 0) and a (theta0 = 180 degrees). For an image it
is the light from a target that arrives within theta0 of the target's
direction after one scattering: blurred by up to theta0, not lost. That
reading is an assumption the documentation states; nothing here tests
it on images.

**From Petzold, not from a type.** The vsf is a station's, at 530 nm,
water and particles together. b(< theta0) = (the report's share below
0.1 degree) b + 2 pi times the integral of the printed vsf from 0.1
degree to theta0, a power law between samples as `ScatteringFunction`
already integrates it. theta0 below 0.1 degree is refused: nothing was
measured there. Every result rests on the report's extension below 0.1
degree (3.4 to 14.5 percent of b) and, at AUTEC 7-9 and HAOCE 5 and 11,
on its three extrapolated angles to 0.159 degree, so it always warns, as
`ScatteringFunction.mean_cosine` does.

**To a water's spectrum, by a choice the caller states.** The share
f(theta0) = b(< theta0) / b of one station, applied to a water's own b at
every wavelength: c(lambda) - f b(lambda). This assumes the station's
phase function holds for that water and does not change with wavelength.
Neither is known; the caller names the station, and there is no default.

**Public.** `forward_scatter(scattering, half_angle_deg)` ->
`ForwardScatter` (the station, the half-angle, the share f, the share of
b from the extension below 0.1 degree, and c_within at 530 nm for the
station itself); `attenuation_within(water, wavelengths, /, *, forward)`
-> c - f b on the wavelengths. The half-angle is one number from 0.1 to
180 degrees. Three public names (137 to 140).

**Checks, with their criteria set now.**

1. At 180 degrees, f = 1 to within 0.3 percent at every station (the
   report's integral against its printed b; 0.9976 to 0.9986, computed
   before this plan), and c_within = a to the same.
2. f rises with theta0, and c_within falls, at every station.
3. An independent Monte Carlo (tools/forward_scatter_mc.py, using
   tools/kd_monte_carlo.py's Petzold sampler): a collimated beam in an
   unbounded water, the weight crossing the plane at distance r moving
   within theta0 of the beam's direction. Stations AUTEC 8, HAOCE 11 and
   NUC 2200; theta0 0.5, 1, 5 and 20 degrees; b r 0.1, 0.5, 1 and 3.
   Against exp(-(c - b F) r) with F the sampler's own share within
   theta0, the criterion is agreement within 3 percent wherever b r <=
   0.5. Beyond that multiple small-angle scattering matters; how much is
   recorded as found, not judged. The sampler continues the vsf below 0.1
   degree with its own power law, which differs from the report's share;
   the difference between F and f is recorded too.

**Documents.** DATA.md section 49 (the figures quoted, the Monte Carlo);
the map; the topic page on seeing through water; docs/api.rst;
CHANGELOG; the Zenodo description. The Monte Carlo's results go to
examples/data/forward_scatter/ (not in the wheel), and the tests read
them. Not done: a point spread function, a blurred image, or a default
station (NEXT_STEPS section 5, options 2 and 3).

**Differences from the plan, noted after the code was written.**

- The share is not integrated from 0 degrees by the package alone: the
  report prints its own cumulative integral at every tabulated angle, so
  at those angles the share is the printed value, and between two of them
  it follows the power-law vsf, scaled to meet both printed values, which
  keeps it rising. Criterion 1 therefore holds exactly: the printed
  integral is 1.0000 at 180 degrees at every station. Integrating the
  printed vsf directly reproduces the printed integral within 0.33
  percent (0.325 at the worst, AUTEC 8; an earlier note said 0.32,
  rounded down, and was corrected before the commit).
- `ForwardScatter` holds numbers only, so it is a plain frozen dataclass.
- Criterion 3 was met: within 0.36 percent wherever b r <= 0.5. At b r =
  3, from 8.5 percent below (AUTEC 8, 20 degrees) to 3.1 percent above.
  The sampler's share within theta0 differs from the report's by up to
  1.1 percentage points (HAOCE 11, 0.5 degree).
- The first draft of the topic page said "most of the scattering turns
  light by less than a few degrees"; at AUTEC 8 the share within 5
  degrees is 45.8 percent, so it says "46 to 64 percent", and a test
  reads it.

## 108. Python 3.11 and NumPy 1.23.2 as the lowest supported (1.24.0): the plan

Python 3.10 reached its end of support in October 2026 (NEXT_STEPS
section 1). The user chose (2026-11-18) to raise the floor to 3.11. Under
section 61, raising a lower bound of Python or NumPy is a minor change.
This plan first put it into 1.23.0 with section 107, in the same pull
request; that pull request had been merged before these commits were
pushed, so it is 1.24.0, a release of its own.

**NumPy follows.** NumPy 1.22 has no wheels for Python 3.11; 1.23.2
(14 August 2022) is the first release that has them (checked on PyPI:
1.23.0 and 1.23.1 have none). A claim of numpy>=1.22 on a package that
needs Python 3.11 could not be tested, so the floor becomes
`numpy>=1.23.2`, and the CI job pinned to the oldest NumPy runs Python
3.11 with numpy==1.23.2 exactly, so that the floor claimed is the one
tested.

**Changes.** pyproject.toml (requires-python, the dependency, the
classifiers); the test and examples matrices in test.yml; CONTRIBUTING.md;
docs/index.rst; the bug report template; the comment in `jerlov._data`
on trapezoid. Nothing in the code relies on 3.10 or on NumPy before
1.23.2, so no code changes; nothing is removed that worked on 3.11.

**Checks.** The existing test that CI's matrix, the classifiers and
requires-python agree; the full suite under Python 3.11 with NumPy 1.23.2,
locally before the push.

**Result.** As planned; no code needed changing. The full suite, 1401
tests, passed under Python 3.11.18 with NumPy 1.23.2 before the push, as it
does under NumPy 2.4. The CHANGELOG of 1.24.0 says so under "Changed".

**After the first CI run.** The job for the oldest NumPy failed on two
figures of `examples/painted_sphere.py` (the grey sphere 11.4 times the
water from above where 14.5 is printed) on one runner, and passed with the
same code on the run before. The Monte Carlo's light field matched the
local run to every printed digit; the difference arises in the picture,
whose large matrix products NumPy hands to its bundled OpenBLAS. Locally,
with NumPy 1.23.2, it did not reproduce with AVX-512 disabled, under four
OpenBLAS core types, or with 1, 2 and 8 threads. Every test job now prints
the runner's CPU and NumPy's BLAS configuration before the tests, so that
the next failure names the machine. Neither a test nor a figure is changed
to make the job pass.

## 109. Two pages to look at: daylight on the way down, and where the sources disagree (1.24.1): the plan

The user asked (2026-11-20) for something enjoyable to do with the package
that would also bring outside readers to it, the direction of 2026-11-18
(more readers before more functions). Two pages were first made as private
drafts outside the repository, from the package's own values; the user
asked for both on the site, in one release. Nothing in the package changes.

**The first page: the colour of daylight on the way down.** The ten Jerlov
types side by side from 0 to 100 m, each coloured by the sunlight left at
that depth, with the surface sunlight as white. Picking a type and a depth
gives the luminance and the PAR photons left, as a share of the surface,
the depths where PAR falls to 10, 1 and 0.1 percent, the spectrum, and ten
of the USGS materials lit at that depth. Its inputs are taken from the
package and embedded in the page: Kd of Jerlov (1976) at 1 nm from 380 to
700 nm; the irradiance just below the surface of `gregg1990_irradiance`,
with the sun 30 degrees from the zenith and the sky of
`examples/sunlight_and_d65.py` (Table 5 of Gregg & Carder, 21 June, a
visibility of 10 km); the CIE 1931 observer; `usgs2017_reflectance`
interpolated onto the same grid. The page's script only multiplies and
integrates, by the trapezoid rule, as `spectrum_to_srgb` and `par_profile`
do.

Every choice the page makes is printed on it: Kd constant with depth (and
what `descend` would do to the 1 percent depth of type I, computed when the
page is made), Kd not changed for the sun, 380 to 700 nm only, colours as
a camera white-balanced at the surface would record them and clipped to
sRGB, no light scattered towards the viewer and nothing about how far
anything can be seen (section 17). The materials are shown with the
exposure raised until the white PVC is as bright as at the surface, and
the white balance left at the surface; the page says so.

**The second page: where the sources disagree.** The four questions of
OPEN_QUESTIONS.md, one figure each: the published absorption spectra of
pure water; Petzold's phase functions with the region below 0.1 degree
that nobody measured, and the share of b his extension puts there; the
Monte Carlo Kd from Williamson & Hollins's a and b over Jerlov's (1976), by
type and wavelength, with the cells outside what the unrecorded conditions
can reach outlined; Jerlov's 1976 Kd over his 1968; and c = a + b of the
same type from Williamson & Hollins and from Solonenko & Mobley. The
closure figure uses the runs with pure water's own scattering and a sky
(`examples/data/sm_closure/runs.csv`, section 94), the latest, and the reach
is computed from them as `examples/closure_with_jerlov_kd.py` computes it.
The few figures the page quotes rather than draws (the reflectances of
question 1, Kd without the extension in question 2, the comparison with
HydroLight in question 4) are copied from OPEN_QUESTIONS.md, where tests
already recompute them.

**How they are made.** `tools/site_pages.py` writes both pages into
`docs/pages/` from templates in `tools/site_pages/`, embedding the values
as JSON; every number in the prose that is not quoted from
OPEN_QUESTIONS.md is computed by the script or by the page from those
values. `docs/conf.py` copies `docs/pages/` to the site's root with
`html_extra_path`; the index and the open questions page link to them. The
pages load nothing from elsewhere: system fonts, no library, so a reader of
the site makes no request to another host. They follow the reader's light
or dark setting. Neither page is in the wheel.

**Checks, written before the code.**

- The pages in `docs/pages/` are byte for byte what `tools/site_pages.py`
  writes now (a source-tree test), so the values embedded are the
  package's current ones.
- The arithmetic the first page's script does, done again in NumPy on the
  embedded values, gives jerlov's own `spectrum_to_srgb` and `par_profile`
  within 1e-5 in each sRGB component and in the relative PAR, and the
  depths of 1 percent PAR within 1 mm, for four types at four depths. In
  the drafts, the script itself, run with node, agreed within 2e-6. Where
  node is present, the test runs the page's own script too.
- Each figure the second page quotes appears in OPEN_QUESTIONS.md.
- The cells the second page outlines are those OPEN_QUESTIONS.md names for
  the runs with water and sky: IB at 425 to 500 nm, 1C and 5C at 425 nm,
  3C at 425 and 450 nm.

A release of documents and a tool, 1.24.1: no shipped value, code or
public name changes.

**Result.** As planned. The arithmetic of the first page, redone in NumPy
and run as the page's own script with node, agrees with `spectrum_to_srgb`
and `par_profile` within the 1e-5 set above; the 1 percent PAR depth of
type I is 162 m with one Kd and 105 m through `descend`. The second page
outlines the eight cells OPEN_QUESTIONS.md names, and its reach, 0.79 to
1.44 times, is that document's. The comparison of the embedded numbers
allows one unit in their last printed digit, in case a value rounds the
other way on another machine; the rest of each page must match byte for
byte. The full suite, 1421 tests, passed before the push.

**Differences from the plan.** None in what the pages show. Drafting
found that a CSS variable in an SVG presentation attribute
(`fill="var(--muted)"`) is not read by every browser, so the pages set
those colours through `style` instead.

## 110. NumPy 1.24.0 as the lowest supported (1.25.0): the plan

Section 108 recorded that CI's job for the oldest NumPy (1.23.2) failed on
two figures of `examples/painted_sphere.py` on one runner and passed on
others, and set every job to print the machine and NumPy's BLAS so that the
next failure would name it. It came on 2026-11-20, in the run of 1.24.1 on
`dev` (tests #502), with the same figures as before: the grey sphere 11.4
times the water from above where 14.5 is printed, 0.59 from below where 0.42
is, and 2.83 and 3.15 under the overcast where 2.17 and 2.19 are. The same
commit passed on `main` (tests #501). The runner was an Intel Xeon 6975P-C
(Granite Rapids, with AVX-512 and AVX512_BF16); NumPy 1.23.2 carries OpenBLAS
0.3.20.

**Reproduced.** On the local Sapphire Rapids machine OpenBLAS 0.3.20 does
not recognise the processor and runs its generic Prescott kernels, which is
why section 108 could not reproduce the failure. Forced with
`OPENBLAS_CORETYPE` to each of its kernels in turn, `painted_sphere.main()`
under NumPy 1.23.2 gives 14.48, 0.416 and 2.173 (from above, from below,
overcast towards the sun) with Prescott, Core2, Penryn, Dunnington,
Nehalem, Sandybridge, Haswell, SkylakeX, Zen, Atom and Barcelona, and
11.37, 0.586 and 2.826, the failing runner's figures, with CooperLake
alone. (Bulldozer and Excavator printed nothing; neither is chosen on an
Intel processor.) With CooperLake forced:

| NumPy | OpenBLAS | From above | From below | Overcast |
|---|---|---|---|---|
| 1.23.2 | 0.3.20 | 11.37 | 0.586 | 2.826 |
| 1.23.5 | 0.3.20 | 11.37 | 0.586 | 2.826 |
| 1.24.0 | 0.3.21 | 14.48 | 0.416 | 2.173 |
| 1.24.4 | 0.3.21 | 14.48 | 0.416 | 2.173 |
| 1.25.2 | 0.3.23.dev | 14.48 | 0.416 | 2.173 |
| 1.26.4 | 0.3.23.dev | 14.48 | 0.416 | 2.173 |

So OpenBLAS 0.3.20's CooperLake kernels give a wrong product here, the
processors on which 0.3.20 chooses them are where the job failed, and
OpenBLAS 0.3.21, first carried by NumPy 1.24.0, gives the right one. Which
routine in OpenBLAS is at fault was not traced. The figure and the test
were right; the test found it.

**The decision.** The floor becomes `numpy>=1.24.0`. A package that claims
a NumPy under which its own example gives a wrong answer on current
processors should stop claiming it; that a user's own matrix products are
equally affected is not the package's to fix, but it should not invite
them. NumPy 1.24.0 has wheels for Python 3.11, so the Python floor stays.
Under section 61 raising a lower bound is a minor change: 1.25.0.

**Changes.** pyproject.toml; the job pinned to the oldest NumPy in
test.yml (tests and examples) and its comments; CONTRIBUTING.md; the
comment in `jerlov._data`; the bug report template. A new test checks that
the NumPy CI pins for the oldest job is the floor pyproject.toml declares,
as the existing one does for Python. NEXT_STEPS's item on the failure is
closed.

**Checks.** The full suite under Python 3.11 with NumPy 1.24.0 before the
push, with the generic kernels and with CooperLake forced on the sphere
example; the full suite under the current NumPy.

**Result.** As planned. Under Python 3.11 with NumPy 1.24.0 the full
suite, 1422 tests, passed with the kernels OpenBLAS chooses on the local
machine, and the four tests of the sphere example passed with CooperLake
forced; under the current NumPy the full suite passed too. The failing
runner itself was not available to run again before the push; CI's job for
the oldest NumPy will show it when it lands on such a processor.

## 111. The spectrum on the first site page says how much it is enlarged (1.25.1): the plan

The user, reading `dive.html` on 2026-11-20, found that at depth the
spectrum's solid line can stand higher than the surface's dashed line, and
asked whether light at depth can be stronger. It cannot: Ed(z) = Ed(0)
exp(-Kd z) and every Kd of Jerlov (1976) is positive. Each curve is scaled
to its own peak, which the caption said, but the person who knows the page
best read it the other way, and the page is meant for readers who do not.

**Changes.** On the chart, under the peak's wavelength, the factor by
which the solid line is enlarged against the surface's scale, the
surface's peak over this depth's peak (shown once it exceeds 1.05, as
"drawn x 2.9 x 10^14" with superscript digits). The caption: both curves
show shape only, each scaled to its own peak, so their heights cannot be
compared; how much light is left is in the numbers above. No number the
page computes changes; the pages are regenerated and the version is
1.25.1.

**Checks.** `tests/test_site_pages.py` as it stands (the page is what the
tool writes), and a test that the factor the page's script computes is the
surface's peak over the depth's, run with node where it is present. A look
at the page at 0 m, where no factor is shown, and at 9C, 58.5 m.

**Also recorded here: section 110 confirmed on the runner.** After 1.25.0
was pushed, CI's job for the oldest NumPy (now 1.24.0) ran once on an
Intel Xeon 6975P-C, the processor of the failure in section 110, and the
four tests of the sphere example passed there; the other run of that job
was on an AMD EPYC 9V74.

**Found while doing it.** The look at 0 m showed the "outside sRGB, shown
clipped" chip under a white swatch. Two faults, both in 1.24.1, both in
the page rather than in its numbers:

- The drafts ran inside a viewer that adds `[hidden] { display: none
  !important; }`; the site's standalone pages lacked it, and the chip's own
  `display: inline-block` won over the `hidden` attribute, so the chip
  showed at every depth on the site. Both pages now carry the rule, and a
  test checks it.
- The chip's test was absolute (a channel below -1e-9), while deep down
  every linear channel is tiny (the largest about 7e-16 for 9C at 58.5 m,
  where blue is -0.077 of it). It is now relative to the largest channel
  and lives in the page's script core, and the node test checks it against
  jerlov's own `spectrum_to_srgb` at the sixteen cases, which include
  colours both in and out of sRGB.

**Changed after the first look.** Both labels moved into a margin above the
plotted area, with a halo in the panel's colour: under the peak's
wavelength the factor overlapped the curve when the peak was mid-chart.

## 112. Letting search engines find the site (1.25.2): the plan

On 2026-11-21 Google returned nothing for `site:tishibashi-cpu.github.io/jerlov`,
while the Zenodo record came fourth for "jerlov". The user filled in the
repository's About (description, website, topics) and began to register the
site with Google Search Console, by the HTML file method. Nothing in the
package changes.

**Changes.**

- `docs/extra/google8846fd1b128ec3b7.html`, the file Search Console asked
  for, one line, copied to the site's root by `html_extra_path`. A folder of
  its own, because `docs/pages/` holds what `tools/site_pages.py` writes.
- `html_baseurl = "https://tishibashi-cpu.github.io/jerlov/"`, which gives
  every page a canonical link, and a `sitemap.xml` written at the end of
  each HTML build by a hook in `docs/conf.py`: every page of the site that
  Sphinx builds from a source file, and the two pages of section 109. No
  new dependency (a sitemap extension exists but would be one).
- A description for the index page (`.. meta::`), which search engines may
  show under the title; the two pages of section 109 have one already.
- `.zenodo.json`: the site as a related identifier, relation
  `isDocumentedBy`, scheme `url`, without a resource type, so that the
  record that ranks well links to the documentation. Added by a string
  replacement, as the file's other edits are.

`robots.txt` is not added: a crawler reads it only at the host's root, which
is the account's site, not this project's; and none is needed, since nothing
is excluded.

**Checks.** Tests that the verification file holds exactly Google's line
and is copied to the root; that the sitemap hook lists the built pages
under the base URL, run on a small Sphinx build of the real configuration
or checked on the site build; that the Zenodo record links the site. A
local build with `-W`, and the sitemap read back.

## 113. The remote sensing reflectance of shallow water, with the bottom in view: Lee et al. (1998, 1999) (1.26.0): the plan

Every reflectance in the package so far is for optically deep water
(section 66 and section 73: no bottom). NEXT_STEPS listed shallow water as
outside the range until the range was widened on purpose; the user chose
on 2026-11-21 to widen it, for people who work over reefs and seagrass,
where the bottom is in view. As in sections 19 and 66, the line moves on
whether a relation's provenance can be stated and checked, and here it
can: the model is printed with its constants and the conditions it was
fitted for.

**What moves into the range.** The forward relation only: from a, bb, the
depth of the bottom, its albedo and the sun to the reflectance just below
and just above the surface, straight down. Still out: the inverse (Lee et
al. 1999's optimization, deriving depth, bottom albedo, a and bb from a
measured spectrum). It needs the spectral shapes of phytoplankton and
gelbstoff absorption, of particle backscattering and of the bottom's
albedo (their Eqs. 16-22, a sand albedo shape among them) to be assumed;
those would be defaults the package does not set (section 4). Still out
too: bottoms that are not Lambertian, layered water, and views off nadir
(below).

**The source.** Lee, Z., Carder, K. L., Mobley, C. D., Steward, R. G. and
Patch, J. S. (1998), "Hyperspectral remote sensing for shallow waters. I.
A semianalytical model", Appl. Opt. 37(27), 6329-6338,
doi:10.1364/AO.37.006329; and (1999), "Hyperspectral remote sensing for
shallow waters: 2. Deriving bottom depths and water properties by
optimization", Appl. Opt. 38(18), 3831-3843, doi:10.1364/AO.38.003831.
Both read from the copies in the University of Maine's course readings
(misclab.umeoce.maine.edu, OO2015/Readings), complete (10 and 13 pages);
PDF page + 6328 and + 3830 are the journal pages. The equations and
constants below were read from page images.

The 1998 paper fitted, to HydroLight 3.0 runs (Table 1, p. 6331: sun 0,
30 and 60 degrees; Petzold's average particle phase function, bbp/bp 1.9
percent, with pure sea water as its own component; bottom albedo 0, 0.1,
0.3 and 1.0, flat in wavelength; H 0.5, 1, 3, 8, 16, 32 m and infinite;
400-700 nm; wind 5 m/s, n = 1.34):

    rrs = (g0 + g1 u^g2) u {1 - A0 exp[-(1/cos(theta_w) + D0 (1 + D1 u)^0.5) kappa H]}
          + A1 rho exp[-(1/cos(theta_w) + D0' (1 + D1' u)^0.5) kappa H]       (11)
    u = bb / (a + bb),  kappa = a + bb,  theta_w the sun's zenith below the surface
    Rrs = zeta rrs / (1 - Gamma rrs)                                             (24)

with g0 0.070, g1 0.155, g2 0.752 (Eq. 16, p. 6333), A0 1.03, A1 0.31, D0
1.2, D1 2.0, D0' 1.1, D1' 4.9 (Eqs. 19-21, p. 6334), zeta 0.518 and
Gamma 1.562 (Eq. 25, p. 6336). The 1999 paper, Appendix A (pp. 3841-3842),
repeats these and says that "with more Hydrolight-simulated data, and
correcting a calculation error in the earlier study", they were updated
to g0 0.084, g1 0.170, g2 = 1; A0 = 1, A1 = 1/pi; D0 1.03, D1 2.4; D0'
1.04, D1' 5.4 (Eqs. A6, A7), with zeta 0.5 and Gamma 1.5 (Eq. A9). It
does not say which calculation was wrong.

**Only the 1999 constants are used.** The authors themselves replaced the
1998 set as containing an error; shipping it beside the correction would
offer a value its source has withdrawn. The 1998 set is recorded in
DATA.md, and the Monte Carlo below is run against both, to see how much
the update matters; the result is recorded, not used to choose.

**The view is straight down.** The 1999 paper adapts the model to views
off nadir (Eqs. 9-11) with an empirical change to bb that it gives only
"to first order" for the plane 90 degrees from the sun, with errors of 6.1
percent on average and 15 percent at most. That is left out; a caller
wanting other views needs a radiative transfer code (section 86).

**The sun.** The model takes theta_w below the surface; the function takes
the sun's zenith angle in air, as every other function does, and refracts
it by Snell's law with n = 1.34, the refractive index of the paper's runs
(p. 6331). D_d = 1/cos(theta_w) treats the downwelling light as the sun's
beam; the runs had a sky, and the docstring says so.

**Public.** `lee1999_shallow_rrs(a, bb, /, *, depth_m, bottom_albedo,
sun_zenith_deg)` returning `ShallowRrs` (a frozen dataclass compared by
value): `rrs`, the total just below the surface; its two terms `column`
and `bottom` (rrs_C and rrs_B of the 1999 paper's Eq. 3); `deep`, rrs_dp,
the same water with no bottom; and `above_surface`, Rrs by Eq. (A9). Two
public names (140 to 142).

- a and bb as for `lee2011_rrs`: positive, NaN a gap. bottom_albedo
  rho in [0, 1], depth_m positive and finite (no bottom is `deep`, so
  infinity is refused as everywhere), the sun in [0, 90). None has a
  default. All broadcast together, so a spectrum, a map of depths or both
  can be given.
- A ProvenanceWarning, not a refusal, outside what the runs covered: the
  sun beyond 60 degrees; H outside 0.5-32 m (the 1998 runs; the 1999
  paper does not give the ranges of its further runs); u above 0.6 (bb/a
  up to 1.5, the 1998 abstract, and Fig. 9's range). The bottom albedo's
  range 0-1 is the runs' and the physical one, so outside it is refused.
- Not applied to the result: Raman scattering and fluorescence, which the
  model leaves out (1999, p. 3832).

**Checks, with their criteria set now.**

1. Limits from the equations: H large gives `deep`; H small gives rho/pi
   plus a vanishing column term; with u = 0, rho = 1 and H -> 0, Rrs =
   0.5/pi / (1 - 1.5/pi) = 0.3046, against the 1998 paper's own check
   with its constants, 0.31 for both rrs and Rrs (p. 6336). Hand calculations of every
   field at one point.
2. An independent Monte Carlo, `tools/shallow_rrs_mc.py`, built on
   `tools/kd_monte_carlo.py`: a flat surface with Fresnel's reflection of
   light from below (n = 1.34), a Lambertian bottom, the sun's beam only;
   particles with NUC 2240's phase function (the stand-in for the average
   particle since section 94; bb/b 0.018 against 0.019), pure water with
   its own. rrs straight up just below the surface by a collision
   estimator; Ed just below the surface including the light reflected
   back down. Its own check first: without scattering and without the
   surface's reflection, rrs = (rho/pi) exp(-a H / cos(theta_w)) exp(-a
   H) to 1 percent.
   Grid: a 0.05, 0.2 and 1.0 1/m; bp/a 0.3, 3 and 30; bw 0.002 1/m; H 1,
   4 and 16 m and no bottom; rho 0, 0.3 and 1.0; the sun 0, 30 and 60
   degrees (270 runs). Criterion, over the runs with u <= 0.6: the median
   of model/MC within 5 percent of 1, and 90 percent of runs within 10
   percent. Not the same as the paper's runs (its phase function, a
   windy surface and a sky, which this does not model), so a miss would
   be recorded with its pattern, not hidden. The 1998 constants against
   the same runs are recorded, not judged.
3. Out-of-tree tests skip what reads examples/data (section 50).

**Documents.** DATA.md section 50 (both sets of constants, the update,
the Monte Carlo's results); the map; the topic page on ocean colour;
docs/api.rst; a part of `examples/ocean_colour_and_secchi.py` (the depth
at which the bottom stops showing, for a few Jerlov types over a bottom
whose albedo the example states); CHANGELOG; the Zenodo description.

**Differences from the plan, noted after the code was written.**

- The Monte Carlo's collision estimator first scored every scattering
  with Petzold's phase function as sampled, down to 0.001 degree. Its
  variance has no bound there (the phase function grows faster than
  1/Theta), and a trial deep-water run with the sun overhead gave 0.10 +-
  0.054. Scattering by less than 1 degree is now counted as none (b
  reduced by that share, 22.9 percent at NUC 2240, the rest
  renormalised); changing the cut to 0.5 or 2 degrees moved four trial
  runs by amounts comparable to their noise. This was changed before the
  grid was run, after the trial runs.
- Criterion 2 was missed: model over Monte Carlo has a median of 0.999
  (met), but 87.4 percent of the runs are within 10 percent, not 90. The
  34 runs outside fall into three groups (DATA.md section 50): pure water
  carrying most of the backscattering (model low, to 0.818), a black
  bottom at 1 or 4 m in turbid water (model high, to 1.723), and a white
  bottom at 1 or 4 m with bp/a = 30. The function is shipped as planned,
  with the misses stated in its docstring and in DATA.md; the constants
  are the paper's and are not adjusted.
- The 1998 constants against the same runs: median 0.953, 70.7 percent
  within 10 percent.
- Text given as a depth (`depth_m="5"`) is read as the number, as in
  the package's other functions that take arrays; no refusal was added.

## 114. Why the shallow-water model misses two groups of the Monte Carlo's runs (1.26.1): the plan

Section 113's Monte Carlo found the model of Lee et al. (1999) outside 10
percent in 34 of 270 runs, in three groups (DATA.md section 50). The user
asked on 2026-11-21 for the causes of the two larger ones to be looked
into: where pure water carries most of the backscattering (16 runs, model
low, to 0.818), and a black bottom 1 or 4 m down in turbid water (13
runs, model high, to 1.723). As in section 91, the package does not settle
this: HydroLight, which the model was fitted to, is not available here.
What can be done is to say which of the differences between the paper's
runs and the Monte Carlo moves each group, and by how much, with every
figure recomputed by a test. No value or code of the package changes.

**Step 1. Where the paper's runs lay.** Their IOPs are rebuilt from the
1998 paper: Table 1's chlorophyll (0.4, 1, 2, 5), ag(440) (0.05, 0.1,
0.3) and B (0.3, 1, 5) at 400-700 nm every 20 nm; Eq. (12) with Table 2's
a0 and a1 (p. 6331, read from the page image, the 16 rows used) and Eq.
(13), af(440) = 0.06 [chl]^0.65; Eq. (14) for ag; Eq. (15), bp = B
[chl]^0.62 550/lambda; Pope & Fry's pure water absorption and Morel's
pure sea water scattering, as the paper says (pure sea water taken at 35
psu, a choice: the paper gives no salinity); bbp = 0.019 bp (the phase
function's 1.9 percent, p. 6332). From these: the range of u, of a, and of
pure water's share of bb, and, for each depth of Table 1, the range of
kappa H. Each Monte Carlo run of section 113 is then placed inside or
outside that set, by its water share and, at its u, its kappa H.
`tools/lee1998_runs.py` writes the 576 rebuilt IOP sets to
`examples/data/shallow_rrs_mc/lee1998_runs.csv`.

**Step 2. Pure water's share, alone.** Deep water and a black bottom at 4
m, the sun at 30 degrees, u held at 0.01, 0.025 and 0.07 with a = 0.05 and
0.2 1/m, and pure water's share of bb set to 0, 0.2, 0.4, 0.6, 0.8 and
0.95 (bw from the share, bp from the rest; 72 runs). If model over Monte
Carlo falls with the share, and is within 5 percent at shares up to the
paper's largest, the first group is put down to pure water's share of
the backscattering, and so to its phase function, which the model, fitted
to runs where particles carried most of it, does not separate.

**Step 3. The black bottom.** Three changes to the Monte Carlo, each
alone, on the group's 13 runs and on the same cells with the sun at the
other angles (24 runs each):

- (a) the particles' phase function: AUTEC 8 (bb/b 0.044) and HAOCE 11
  (0.014) in place of NUC 2240, a, bb and pure water's part held, so bp
  changes;
- (b) a sky: 30 percent of the irradiance just below the surface as
  diffuse light, uniform in radiance in the air
  (`kd_monte_carlo.sky_cosines`), since the paper's runs had a sky and
  the model takes D_d = 1/cos theta_w;
- (c) none to the Monte Carlo, but to the model: the column's term with
  the 1998 constants (A0 1.03, D0 1.2, D1 2.0) beside the 1999 ones,
  since the 1998 paper wrote that fixing A0 = 1 would need another form
  (pp. 6334-6335).

And from the existing runs, the column's attenuation the Monte Carlo
implies: with a black bottom, rrs(H)/rrs_dp = 1 - exp(-D kappa H) gives D
= -ln(1 - rrs(H)/rrs_dp) / (kappa H), both rrs from the Monte Carlo, to set
beside the model's 1/cos theta_w + 1.03 (1 + 2.4 u)^0.5.

A change is said to account for the group if it alone brings most of the
group's runs (at least 10 of 13) within 10 percent. If none does, that is
what is recorded.

**Documents.** OPEN_QUESTIONS.md section 5, in the five parts; DATA.md
section 50 extended; the site's open_questions page a line; a new example
`examples/shallow_water_closure.py`, the twenty-ninth, for those who
model or invert shallow-water reflectance, reading the runs from
`examples/data/shallow_rrs_mc/` and printing every figure the document
quotes (it needs the repository, as `closure_with_jerlov_kd.py` does).
The new runs are written by `tools/shallow_rrs_mc.py`, given options for
the share, the station and the sky, with the default runs unchanged
bit for bit. Version 1.26.1.

**Differences from the plan, noted after the runs.**

- Step 2's test was missed: model over Monte Carlo falls with pure
  water's share in all 12 cases, but up to a share of 0.4 it is 0.927 to
  1.157, not within 5 percent. Recorded as accounting for the direction of
  the first group's miss, not all of it.
- Step 3's test was missed by every change: HAOCE 11 brought 8 of the 13
  within 10 percent, AUTEC 8 and the sky 3, the 1998 constants 6. What is
  recorded is how far each change moves the ratio in the same cell.
- "Within what the paper's runs covered" was first judged by kappa H
  where u is above 0.3 only; the second group has runs at u of 0.055 and
  0.069 too. It is now judged run by run, against the paper's runs within
  20 percent of its u, at the depths of Table 1: all 13 are covered.
- The first drafts of the example said the first group "lies on this
  trend" and that the column was attenuated "in the first tenth of an
  attenuation length"; neither was computed. The example now reads the
  trend off at the group's shares (0.823 to 1.003, against the misses'
  0.818 to 0.893) and states D's ratio by kappa H.
- In one cell the Monte Carlo gives more for a black bottom at 4 m than
  for deep water, by 0.9 times the standard error of the difference; no D
  is taken there.

## 115. Would water and particles apart, or the phase function, close the shallow model's two groups? (1.26.2): the plan

Section 114 left two things open (OPEN_QUESTIONS.md question 5): whether
a form with pure water and particles apart, as Lee et al. (2011) wrote
for deep water, would close the first group, and whether a form with the
phase function in it would close the second. The user asked on
2026-11-21 for this to go on. HydroLight is still not available, and no
coefficient is fitted here: fitting a model to this package's own Monte
Carlo would be deriving coefficients (section 12, out of scope) and would
show only that the Monte Carlo agrees with itself. What can be done
without fitting:

**Step 1. Lee et al. (2011), as published, against pure water's share.**
`lee2011_rrs` with the coefficients for the sun at the zenith and a
nadir view, (0, 0, 0), keeps water and particles apart and needs no
fitting. It gives Rrs above the surface; the Monte Carlo gives rrs below.
They are put on one footing by Lee et al.'s (2002) Eq. (8), rrs = Rrs /
(0.52 + 1.7 Rrs), which the package already uses (`above_surface_rrs`
inverts it), and which is a stated assumption for these waters. New
Monte Carlo runs: deep water, the sun at the zenith, u 0.01, 0.025 and
0.07, pure water's share of bb 0, 0.2, 0.4, 0.6, 0.8 and 0.95 (18 runs;
a does not matter in deep water at fixed u, which section 114's runs
showed to the last digit). For each u, the spread of model over Monte
Carlo across the shares (largest over smallest) is set beside the same
spread for Lee et al. (1999)'s deep term. The separated form is said to
follow pure water's share if its spread is at most a third of the 1999
model's at every u. Its level is not judged, since the surface
conversion is assumed.

**Step 2. What orders the black-bottom miss.** Section 114 ran the 24
black-bottom cells with three of Petzold's phase functions (NUC 2240,
AUTEC 8, HAOCE 11), a, bb and pure water's part held. For each cell, is
model over Monte Carlo monotonic in the particles' bb/b (0.018, 0.044,
0.014 by the sampler), and in the same direction? If it is in at least 20
of the 24 cells, bb/b (equivalently b at fixed bb) is recorded as ordering
the miss, which a form with the phase function or b in it would have to
take; if not, that is recorded. No new runs.

**Documents.** OPEN_QUESTIONS.md question 5 extended (what was done, what
was found, what is not known); DATA.md section 50; a fourth part of
`examples/shallow_water_closure.py`; the runs to
`examples/data/shallow_rrs_mc/water_share_nadir.csv`; tests that recompute
every figure. No value or code of the package changes. Version 1.26.2.

**Differences from the plan, noted after the runs.**

- Step 1's test, "a spread at most a third of the 1999 model's", is read
  as the spread's excess over 1 (largest over smallest, less 1): the
  separated form's is 0.20 to 0.24 of the 1999 model's, so the test is
  met. Read literally, a third of 1.232 to 1.333 is below 1 and no spread
  could meet it; that reading was not meant.
- Step 2's test was missed: model over Monte Carlo rises with bb/b in 5
  of the 24 cells and falls in none. In 16 the middle station, NUC 2240,
  gives the highest.
- Added after step 2, before writing it up: the Monte Carlo's cut at 1
  degree had been checked at NUC 2240 only (section 113). Since the three
  stations lose different shares to it (0.343, 0.229 and 0.199 below 1
  degree at HAOCE 11, NUC 2240 and AUTEC 8), the cell a 0.05 1/m, bp/a 3,
  H 1 m, sun overhead was run at each station with cuts of 0.5, 1 and 2
  degrees (`--cut-check`, 9 runs): the ratio at any station moves by a
  factor of 1.027 at most. The first draft of the example called that cell
  the one where the stations differ most; it is not (1.72 there, 1.92 at
  a 0.2 1/m), and the text now gives both.

## 116. The dip in Morel et al.'s (2002) archive at a sun of 45 degrees, located (1.26.3): the plan

Section 105 found f.dat, in the authors' archive that
`morel2002_fq_tables` reads (section 104), lying below the straight line
in 1 - cos theta_s between its own values at 30 and 60 degrees by up to
3.44 percent at 45 degrees (660 nm, 0.03 mg m^-3), which the paper's
linear fits cannot follow, and left the reason open (NEXT_STEPS section 3).
The user asked on 2026-11-21 for it to be taken up. The archive is the
user's own copy and is not shipped (no licence is stated); everything
below reads it, and its tests run only where it is present.

**Step 1. Where the dip is.** For f, for f/Q in every one of the 17 x 13
directions, and for Q at the nadir (f over the nadir f/Q): the departure
at each interior sun angle (15, 30, 45 and 60 degrees) from the chord
between its neighbours, in 1 - cos theta_s, for all 42 (wavelength, Chl)
cases. The question is whether the dip belongs to one or a few
(Chl, sun) runs or runs through the table.

**Step 2. Against its neighbours in Chl.** f(theta_s)/f(0) at one Chl
divided by the same at the next Chl, at each wavelength: smooth in
theta_s where the runs are consistent with each other. A sun angle where
this ratio falls out of order (lower than at the next larger angle) marks
that run as out of line with the rest of the table.

**What would follow.** If the dip is confined to one Chl at one sun
angle, at every wavelength and every direction alike, and nowhere else
exceeds what the other Chl show at the same angle, those values are
recorded in DATA.md section 48 as suspect: out of line with the table
they belong to, kept as the archive has them. `morel2002_fq_tables` then
gives a `ProvenanceWarning` when `f` or `f_over_q` is asked for at that
Chl and sun angle, naming DATA.md section 48; no value changes. What made
them so is not known and is not guessed (the paper describes Raman
emission computed for every run; nothing here can separate it). If the
dip is not so confined, that is recorded instead and no warning is added.

**Documents.** OPEN_QUESTIONS.md question 6, in the five parts; DATA.md
section 48; a new example `examples/fq_at_45_degrees.py` (the thirtieth)
that reads the archive from a path given as `--archive PATH` and, without
one, says so and does nothing else, so that CI, which has no archive,
runs it; tests that recompute every figure where the archive is present
and are skipped elsewhere, as section 104's are. Version 1.26.3.

**Differences from the plan, noted after the analysis.**

- Step 1's measure for f/Q was first the range over all 221 directions.
  It is wide at every sun angle (at 15 degrees already -4.53 to +4.26
  percent), so it could not show where the dip lies; the example takes,
  for each case, the median over the directions, which does (-3.52 to
  -1.35 at the suspect run, -0.16 to +0.85 elsewhere).
- At 30 degrees Chl 0.03 alone lies above its chord; that chord has the
  low value at 45 as an end, so this follows from the run at 45 and is
  not a second finding.
- The example first took its archive with argparse; run as CI runs the
  examples (runpy from "python -c"), sys.argv carries the script's own
  path and argparse refused it. It now reads only an explicit
  `--archive PATH`, as `radiative_transfer_inputs.py` reads `--read`.
- The first draft of OPEN_QUESTIONS.md question 6 said the dip grows with
  the wavelength "as Raman emission's share does at low Chl"; that share
  was not computed. It now quotes what the paper says (p. 6298).
- The existing tests in tests/test_fq_tables.py read every run and so
  now meet the new warning; they ignore that one message.

## 117. The dip at 45 degrees against the authors' own later tables, distributed by NASA (1.26.4): a record

Section 116 located the dip in one run of Morel et al.'s archive (the sun
at 45 degrees, 0.03 mg m^-3) and left its cause open. The user asked on
2026-11-21 whether it could be looked into, and chose the first of the
ways offered: find another distribution of the same tables. **This
section is a record, not a plan written beforehand:** the comparison
below was made first, as a look at whether the files could be reached and
read, and turned out to answer the question; it is written down here
with the method as it was run, before anything goes into the repository.

**The files.** NASA's Ocean Biology Processing Group distributes, in the
`common` bundle of OCSSW (the processing code behind SeaDAS), four
Morel f/Q files, listed in
https://oceandata.sci.gsfc.nasa.gov/manifest/tags/V2026.6/common/manifest.json
and fetched from https://oceandata.sci.gsfc.nasa.gov/manifest/tags/<tag>/common/
on 2026-11-21:

| File | Tag | Bytes | SHA-256 as fetched | Manifest's SHA-256 |
|---|---|---|---|---|
| morel_fq.dat | initial | 389,844 | 5d6e942f... | the same |
| morel_fq.nc | initial | 235,227 | 865c7b29... | the same |
| morel_fq_hyperspectral.nc | T2024.24 | 1,142,785 | 109aca43... | eb4a4bba..., not the same |
| morel_fq_hyperspectral_2026.nc | T2026.2 | 4,249,565 | 4342cddd... | 35c776f7..., not the same |

The two hyperspectral files have the sizes the manifest gives but not its
checksums; why is not known. Both are HDF5 and read without error, and
their nadir f/Q agree with each other to the last digit.

- `morel_fq.nc` (created 2015, by a script named cre_morel_ncfile.py):
  f/Q at the archive's 7 wavelengths, 6 sun angles, 6 Chl, 17 nadir
  angles and 13 azimuths, the archive's tables in another format.
- `morel_fq_hyperspectral_2026.nc` (created 2026-02-09): "f and Q tables
  derived hyperspectrally by Bernard Gentili", one of the paper's authors,
  at 70 wavelengths from 352.5 to 697.5 nm every 5 nm, the same 6 sun
  angles and 6 Chl, and 5 aerosol optical thicknesses (its `foq` is the
  slice at 0.2, the paper's value). `morel_fq_hyperspectral.nc` (2024)
  holds the same nadir values.

**What was compared.** f/Q at the nadir (the first nadir row; it does not
depend on the azimuth in any of the files). The departure at 45 degrees
from the chord between 30 and 60 degrees, in 1 - cos theta_s, as in
section 116; and, to set the recomputation against the archive without
its overall differences, the ratio hyperspectral/archive at each
wavelength, sun angle and Chl (the hyperspectral values interpolated to
the archive's wavelengths, linearly between the 5 nm neighbours), taken
at 45 degrees against the chord of the same ratio at 30 and 60.

**What was found.**

- `morel_fq.nc` has the archive's dip unchanged: nadir f/Q at 45 degrees
  and 0.03 mg m^-3 is 1.35 to 3.54 percent below its chord.
- The hyperspectral tables have no dip: at 0.03 mg m^-3, -0.25 to -0.13
  percent from the chord over their 70 wavelengths, in line with 0.1 mg
  m^-3 (-0.34 to -0.14).
- They differ from the archive by up to about 5 percent in every run (the
  recomputation is not a copy), but along the sun angle they follow it
  except at the one run: the ratio at 45 degrees against its own chord is
  +1.23 to +3.47 percent at 0.03 mg m^-3, largest at 660 nm as the dip
  is, and -1.44 to +0.01 at every other Chl.

So the authors' own later computation does not have the dip: it is not a
feature of the physics their model computes, and the archive's run is out
of line. What went wrong in it is still not known.

**What goes into the repository.** No NASA file is shipped: the
hyperspectral tables are described as Gentili's, and section 104 did not
ship the archive for want of a stated licence; the same caution is kept.
The user's copies go to `sources/ocssw/` (ignored by git), and the tests
that read them are skipped without them, and without h5py, which the
package does not depend on. `examples/fq_at_45_degrees.py` gains
`--ocssw DIR`, which reads them with h5py if it is installed and only
then. OPEN_QUESTIONS.md question 6 and DATA.md section 48 record the
finding; the run stays suspect, and its warning now says that the
authors' recomputation does not have the dip. Version 1.26.4.

## 118. The dip at 45 degrees in the paper's own Fig. 13 (1.26.5): the plan

Sections 116 and 117 found the dip in one run of Morel et al.'s archive
(the sun at 45 degrees, 0.03 mg m^-3), absent from the authors' later
tables, and left open what went wrong. The user asked on 2026-11-21 for
any mention of it by the authors; none was found (Voss et al. 2007,
which compares Q ratios only and could not see it; MERIS ATBD 2.9, Morel
& Antoine 2011; Mobley et al. 2016, NASA/TM-2016-217551; D'Alimonte et
al. 2025 and Pitarch et al. 2025, Remote Sensing of Environment 321 and
329, which say that Gentili revised the tables, 350-700 nm, and extended
them to OLCI's bands, without a reason; NASA's orm_morel issues 1 and 2,
which concern NASA's own code). EUMETSAT's OLCI table could not yet be
obtained. On that search a look by eye at the paper's Fig. 13 (p. 6301:
f0/f against Chl, the sun at 0, 15, 30, 45 and 75 degrees, one symbol
per wavelength) suggested that its symbols at 45 degrees and 0.03 mg
m^-3 sit where the archive's values are. The user asked on 2026-11-22
for that to be recorded first, as 1.26.5. **The look came first; the
measurement below is planned here, before it is made.**

**The source.** The user's copy of the paper as Optica distributes it,
`sources/morel2002/Morel_Antoine_Gentili_2002_AO.pdf` (536,070 bytes, MD5
1daf887204a1cb949ec62b15544f082e); not shipped. Fig. 13 is embedded in
page 13 as a one-bit image at 300 pixels per inch.

**The reading.** A new tool, `tools/read_fig13.py PDF`, takes the image
out with poppler's `pdfimages` and, with numpy only:

- calibrates f0/f from the left axis's tick marks labelled 1.0 and 0.6,
  linearly in pixels, and the Chl columns from the bottom axis's ticks
  at 0.1, 1 and 10 (logarithmic), so that 0.03 sits where the
  logarithm puts it;
- finds the filled symbols (circles, triangles, diamonds, squares: every
  wavelength but 442.5 nm, which is a cross) as what survives an erosion
  that removes the one-pixel hatching, and keeps those whose centres
  fall within the columns at 0.03 and 0.1 mg m^-3;
- writes the f0/f of each centre to
  `examples/data/morel2002_fig13.csv`: numbers read from the figure,
  nothing else from the paper.

Symbols are not told apart by shape; only the set of values in each
column is used. The reading's accuracy is judged from the 0 degree row,
which must read 1, and from how far the readings stand from the nearest
archive value at the sun angles other than 45 degrees.

**What is compared.** The readings at 0.03 and 0.1 mg m^-3 against: (a)
the archive's f(0)/f(theta_s) at the five plotted sun angles and seven
wavelengths; (b) the same from the paper's own linear fits, Eq. (B1)
(`morel2002_nadir_fq`), at 45 degrees.

**What would follow.**

- If at 0.03 mg m^-3 the readings that belong to 45 degrees stand at the
  archive's values, within the reading's accuracy, and none where Eq.
  (B1) puts them, the values the paper plotted already had the dip: it
  was in the computation the paper reported (October 2002), not brought
  in when the archive was packed (June 2003), and the August 2002 fits
  smoothed it out. DATA.md section 48's "why the archive (June 2003) and
  the paper's fits (lin-approx.tar, August 2002) differ there is not
  known" is then answered in part: the fits differ from the computed
  values, which the paper's own figure shows.
- If they stand where Eq. (B1) puts them, the dip came after the paper,
  and that is recorded.
- If the reading cannot tell the two apart, that is recorded, and
  nothing more is claimed.

In every case the run stays suspect, no value or warning changes, and
what went wrong in the run stays not known.

**Documents.** OPEN_QUESTIONS.md question 6 and DATA.md section 48 record
the result; `sources/README.md` lists the paper's copy.
`examples/fq_at_45_degrees.py` gains a fourth part that sets the shipped
readings against the archive and the fits. Tests check that the readings
are what the tool writes (where the paper's copy and pdfimages are
present) and recompute every figure quoted (where the archive is
present); both are skipped in CI, as before. Version 1.26.5.

**What was found.** The filled symbols at 0.03 and 0.1 mg m^-3 hold all
60 of the archive's values there (six wavelengths by the five plotted sun
angles); a symbol on its own, at a sun angle other than 45 degrees, lies
within 0.0006 of its value, and the 0 degree symbol at 0.1 mg m^-3,
which stands on its own, reads 1.0000. At 0.03 mg m^-3 and 45 degrees,
where Eq. (B1) puts f(0)/f at 560, 620 and 660 nm (0.9135, 0.9038 and
0.8984), no symbol stands within 0.0110 to 0.0164, more than ten times
that accuracy; the archive's values there (0.9312, 0.9282 and 0.9265)
lie within a span of symbols. The first case above holds: the values the
paper plotted were the archive's, dip included.

**Differences from the plan, noted after the reading.**

- The readings are in `examples/data/fq_at_45_degrees/fig13.csv`, one
  folder per example as `examples/data/shallow_rrs_mc/` is, not
  `examples/data/morel2002_fig13.csv`.
- The bottom axis's tick labels survive the erosion; the reading drops
  everything from three pixels above the bottom frame line down, as it
  drops the legend's box.
- At 0.03 mg m^-3 the 0 degree symbols touch the 15 degree ones; the 0
  degree check is made at 0.1 mg m^-3, where that symbol stands alone.
- `morel2002_nadir_fq`'s Notes said of Eq. (B1)'s departure from the
  archive "why is not known"; they now say that the largest is at the
  suspect run, which the paper's figure plots. No value changes.

## 119. Questions 5 and 6 on the page "Where the sources disagree" (1.26.6): the plan

`docs/pages/disagree.html` (section 109) gives the first four questions of
OPEN_QUESTIONS.md a figure each; questions 5 (1.26.1) and 6 (1.26.3) came
after it and are not there. The user asked on 2026-11-22 for both to be
added, with figures, as 1.26.6. For question 6 the user chose figures made
only of values the repository holds: Morel et al.'s archive states no
licence and is not shipped (section 104), so nothing computed from it is
put on the page. The page, like the rest of the site, is written by
`tools/site_pages.py` from the package and the repository; no browser
request leaves the site.

**Question 5, two figures from `examples/data/shallow_rrs_mc/`.**

- The 270 Monte Carlo runs (`monte_carlo.csv`): the 1999 model over the
  Monte Carlo, log scale, against pure water's share of bb, (bw/2)/bb, with
  the band within 10 percent shaded and the two groups of misses coloured
  as `examples/shallow_water_closure.py` defines them (its `groups`, read
  through runpy, so that the two cannot drift apart). The highest share
  among the paper's 576 rebuilt waters (`lee1998_runs.csv`) is marked.
- Pure water's share alone (`water_share.csv`): the ratio against the
  share for each of the 12 cases with u and a held, one line each.

The prose quotes OPEN_QUESTIONS.md question 5. The counts and ranges it
states (270 runs, 87.4 percent within 10 percent, 16 and 13 runs, 0.818 to
0.893, to 1.723, a share of at most 0.46) are also computed from the
embedded values by the tool, and a test checks the two agree.

**Question 6, one figure from what the package ships.** f(0)/f against
the chlorophyll column of the paper's Fig. 13, at 0.03 and 0.1 mg m^-3:

- the spans of the figure's filled symbols, as `tools/read_fig13.py` read
  them (`examples/data/fq_at_45_degrees/fig13.csv`, section 118), drawn as
  bands;
- f(0)/f from the paper's own linear fits, Eq. (B1) of Appendix B
  (`morel2002_nadir_fq`, shipped since 1.21.0), at 15, 30 and 45 degrees,
  for the six wavelengths whose symbols are filled, drawn as dots in three
  lanes, one per sun angle.

A dot inside a band is where the paper drew a symbol; one outside is not.
The page computes how far the fits at 45 degrees and 0.03 mg m^-3 stand
from the nearest band at 560, 620 and 660 nm, and a test checks that this
is OPEN_QUESTIONS.md's "0.0110 to 0.0164". The archive's own values, the
chord's departures and the 60 matches are quoted from OPEN_QUESTIONS.md as
words, not drawn.

**Also.** The lede, the description and the footer say six questions and
name the new sources and repository folders; question 4, which has no
figure, keeps none. Nothing in the package changes. A release of documents
and the site, 1.26.6.

**Checks.** The page is what the tool writes (the existing test); each
figure quoted is in OPEN_QUESTIONS.md (the existing list, extended); the
counts above are recomputed; the page asks nothing of another host (the
existing test).

**Added to the plan before its code: question 4's figure.** While the
above was being written, the user asked whether question 4 has nothing
to draw. It has: section 109 left it without a figure, not for want of
values. `examples/data/sm_closure/runs.csv` holds, for the 143 cells,
the Monte Carlo's Kd to 10 percent of the surface light with pure
water's own scattering and a clear sky (`set` solonenko2015, `factor`
base) beside K_d^H. The page draws their ratio as question 3's is drawn,
by type and wavelength with the same diverging colours, and computes the
median and the share within 10 percent; a test checks these are
OPEN_QUESTIONS.md's 0.970 and 94.4 percent. The reach of the unprinted
conditions is quoted, not drawn.

**Result.** As planned, with question 4's figure added before its code.
The page computes the 270 runs, 87.4 percent within 10 percent, the
groups of 16 and 13 runs (0.818 to 0.893; to 1.723) and the shares 0.46,
0.48 and 0.79 of question 5; the median 0.970 and 94.4 percent of
question 4; and 0.0110 to 0.0164 for question 6. Tests find each in
OPEN_QUESTIONS.md. The pages were looked at in Chromium, light and dark,
at 1200 and 390 pixels wide; no script error, no sideways scroll of the
page.

**Differences from the plan, noted after the code.**

- Question 6's dots were first drawn as outside a band whenever they
  missed it at all; one fit at 30 degrees misses by 0.0006, the reading's
  own accuracy. A dot is now drawn as on a symbol when it lies within that
  accuracy (OPEN_QUESTIONS.md's 0.0006). The caption says so, and gives
  the largest misses the page computes: up to 0.0044 at 0.1 mg m^-3 and
  0.0164 at 0.03 mg m^-3 and 45 degrees. The fits at 0.1 mg m^-3 also
  miss a few symbols, which the plan did not foresee.
- Question 4's heat map has 15 wavelengths; its cells are narrower than
  question 3's (38 pixels against 46) so that it fits beside the text.
- Question 4's sentence on the reach of the unprinted conditions now
  quotes OPEN_QUESTIONS.md's figures (-12.7 to +26.0 percent for the
  stations, -12.7 to +21.5 for the sun); the median and the share within
  10 percent are computed rather than quoted, and leave the list of
  quoted figures.

## 120. More to look at on the site: a figure on the front page, a gallery of the examples, a third page, and a card for sharing (1.26.7): the plan

The user asked on 2026-11-23 for all four of the proposals made after
1.26.6 (NEXT_STEPS section 1), to bring readers to the package (the
direction of 2026-11-18). Nothing in the package changes. Every figure
is made from the package's own values by `tools/site_pages.py`, as the two
pages of section 109 are, and a test checks that what is committed is
what the tool writes now. No page loads anything from another host.

**1. A figure on the front page.** `docs/figures/kd_types.svg`: Kd of the
ten types from Jerlov (1976), 350 to 700 nm, log scale, one line per
type, labelled at the right; and the same ten as a colour strip of the
daylight left at 10 m (`spectrum_to_srgb` of the surface irradiance of
`dive.html`, section 109, times exp(-Kd 10 m), white-balanced at the
surface). Placed in `docs/index.rst` under the first paragraph, with a
caption naming the source and the choices (sun 30 degrees, Kd constant
with depth).

**2. A gallery of the examples.** `docs/examples.rst` gains, above its
table, six cards, each a small figure from the package and the examples
it leads to:

- the light at depth: PAR left with depth, ten types (`par_profile` with
  the surface spectrum of `dive.html`) — `light_at_depth.py`,
  `euphotic_zone.py`, `isolumes.py`, `seagrass_depth_limit.py`;
- why the source is an argument: Kd of type II from Jerlov (1968, 1976),
  Austin & Petzold (1986) and Solonenko & Mobley (2015) —
  `sources_disagree.py`;
- colours through water: the daylight left at 0, 5, 10 and 20 m in IB,
  1C and 5C, as swatches — `lure_colours.py`, `what_an_eye_sees.py`,
  `painted_sphere.py`, `fish_colour_differences.py`;
- heating the upper ocean: the fraction of solar irradiance left with
  depth (`solar_fraction`), ten types — `solar_heating.py`;
- from chlorophyll: Kd from `morel2001_kd` at 0.03 to 10 mg m^-3 —
  `ocean_colour_and_secchi.py`, `what_is_in_the_water.py`;
- scattering: Petzold's phase functions (`petzold_scattering`) —
  `measured_scattering.py`, `phase_function_choice.py`.

Each card is a static SVG in `docs/figures/`, drawn by the tool, with the
quantity, the source and the axes on it. The table of all thirty stays.

**3. A third page: the waters side by side.** `docs/pages/waters.html`,
in the style of `disagree.html`: pick a type, and see every source the
package has for it on one set of axes: a and b (Williamson & Hollins
2022, Solonenko & Mobley 2015), c = a + b, and Kd (Jerlov 1968 and 1976,
Austin & Petzold 1986, Solonenko & Mobley's HydroLight Kd); or pick a
quantity and a source and see all its types. Values outside what a
source gives are not drawn; the page names each source's caveats as the
package states them (`SOURCES`). Linked from the index, the other two
pages and the sitemap.

**4. A card for sharing.** `docs/extra/og.png`, 1200 by 630 pixels,
rendered by a new tool, `tools/og_image.py`, from the front page's figure
with Playwright's Chromium (a tool's need, not the package's; the PNG is
committed). Every page of the site gets Open Graph and Twitter card tags
(title, description, image, address): the Sphinx pages through a
`docs/_templates/layout.html` that extends the theme's, the three pages
in their templates.

**Checks.** The figures and pages are what the tool writes (the existing
test, extended); the front-page strip and the swatches are
`spectrum_to_srgb` of the stated spectra; the third page draws only what
`water()` returns (a test compares its embedded values); the card is a
PNG of 1200 by 630 and every page names it; no page asks anything of
another host (the existing test, extended). A release of documents and
the site, 1.26.7.

**Result.** As planned. The site was built with `sphinx-build -W` and
looked at in Chromium: the front page's figure, the six cards, the third
page in light and dark at 1200 and 390 pixels wide (no script error, no
sideways scroll of the page) in both of its modes, and the card. Tests
check that the figures and the three pages are what the tools write
now, that the swatches and the strip are `spectrum_to_srgb` of the stated
spectra, that the third page's values are `water()`'s and its caveats
`SOURCES`', and that the card is a PNG of 1200 by 630 named by every page.

**Differences from the plan, noted after the code.**

- The figures are drawn by a module of their own, `tools/site_figures.py`,
  which `tools/site_pages.py` loads and writes into `docs/figures/`; the
  pages stay in `site_pages.py`.
- `tools/og_image.py` renders the card with a headless Chromium's
  `--screenshot`, not through Playwright's Python package, which is not
  installed where the tool was written; it finds Playwright's Chromium,
  or another named by CHROME or on the PATH.
- On the third page Williamson & Hollins's lines start at 415 nm: they
  measured from 412 nm, and their source's caveat says the values below
  are a model's. "Values outside what a source gives are not drawn" is
  read so.
- `spectrum_to_srgb` warns that 380-700 nm leaves 0.2 percent of the
  observer out and that some colours are clipped to sRGB; the figures
  silence both, as `dive.html` does, and the front page's caption now says
  the colours are clipped.
- The docs workflow also checks that the sitemap names `waters.html` and
  that `og.png` is in the built site.

## 121. A fourth page: when the bottom shows through (1.26.8): the plan

The user chose on 2026-11-25, of the proposals after 1.26.7, a page for
the shallow-water reflectance of 1.26.0 (section 113). Nothing in the
package changes. As with the three pages of sections 109 and 120, every
value is taken from jerlov by `tools/site_pages.py` and embedded; the
page's script only evaluates the published model on it, and a test
checks that script against the package's own function.

**The page.** `docs/pages/shallow.html`, "When the bottom shows through".
The reader picks a type, a bottom depth (0.5 to 32 m, the depths of Lee
et al.'s 1998 runs), a bottom albedo (0 to 1, flat in wavelength, like
those of the runs), the sun (0, 30 or 60 degrees, the angles of the runs)
and the particles' bbp/bp (0.005, 0.0183 or 0.03, the three of
`examples/ocean_colour_and_secchi.py`; 0.0183 is that of Petzold's
average-particle phase function, which the runs used, and is selected
first). The controls stop at the runs' limits, so the model's
ProvenanceWarnings for the sun and the depth cannot arise; if u = bb/(a +
bb) passes 0.6 anywhere, the page says so, as the function warns.

- **The water's a and bb.** a from Solonenko & Mobley (2015), the only
  source with a and b for all ten types, every 5 nm from 400 to 700 nm
  (the runs' range) by `Water.a`; bb by `Water.bb(...,
  particle_backscatter_ratio=r)`, embedded for each of the three r. The
  source tabulates every 25 nm; between, the values are the package's
  linear interpolation, and the page says so.
- **Three figures.** (1) Rrs above the surface against wavelength: with
  the bottom, the same water with no bottom, and the bottom's part. (2)
  The bottom's share of rrs against depth at 450, 550 and 650 nm (the
  wavelengths of the example's part 13), the chosen depth marked, and the
  10 percent line at which that part counts the bottom out of sight. (3)
  Two swatches, the colour seen straight down with the bottom and without
  it: the reflectance pi Rrs under Gregg & Carder's (1990) sky of
  `dive.html` above the surface (at the chosen sun), through
  `spectrum_to_srgb` with that sky as white, both scaled by one factor
  the page prints. Reflection of the sky at the surface is not in Rrs and
  not in the swatches; the page says so.
- **What the model is.** The model's equations, its source (Lee et al.
  1998, 1999, with DOIs) and what it leaves out (oblique views, Raman,
  fluorescence, a sky that is not the sun's beam), as the docstring says.
  How it fares against the Monte Carlo of section 113 (the median ratio,
  the share within 10 percent, and the number of runs), computed by the
  tool from the data of question 5 and linked to `disagree.html`.

**The script.** The model is `tools/site_pages/shallow_core.js`; the
colour reuses `dive_core.js`'s `linear`. Both are embedded in the page.

**Links.** From the index, the other three pages' navigation, and the
sitemap (`_EXTRA_PAGES`), with the Open Graph tags of section 120.

**Checks.** The page is what the tool writes; it asks nothing of another
host; its embedded a and bb are `water()`'s; the script, run by node,
gives `lee1999_shallow_rrs`'s rrs, column, bottom, deep and above_surface
within 1e-5 (relative) over types, depths, albedos, suns and ratios, and
`spectrum_to_srgb`'s colours within 1e-5; the Monte Carlo figures it
quotes are in OPEN_QUESTIONS.md; the index, the nav and the sitemap name
it. The site is built with `sphinx-build -W` and looked at in Chromium in
light and dark, at 1200 and 390 pixels wide. A release of the site,
1.26.8.

**Result.** As planned, with the differences below. The page was looked
at in Chromium in light and dark at 1200 and 390 pixels wide (no script
error, no sideways scroll of the page). Tests check that the page is what
the tool writes, that its a, bb, the model's constants (and the
equations as printed) and the warnings it shows are the package's, that
its script, run by node, gives `lee1999_shallow_rrs`'s five quantities to
1e-12 over 20 cases and `spectrum_to_srgb`'s colours to 1e-5, that the
Monte Carlo figures are those of OPEN_QUESTIONS.md question 5 and DATA.md
section 50, and that the index, the sitemap and every page's navigation
name it.

**Differences from the plan, noted after the code.**

- Solonenko & Mobley's values carry flags the plan did not foresee: b of
  I and IA is suspect at every wavelength (Table 3's Bs or Bl does not fit
  the b column), and a is missing for 3C at 675-700 nm and for 5C at
  600-700 nm (Table 7's duplicated rows, DATA.md section 1). The page
  shows, beside the type, the ProvenanceWarnings the package gives for it
  (read by the tool, word for word); it draws nothing where a is missing
  (with the package's linear interpolation, 3C beyond 650 nm and 5C beyond
  575 nm), and gives no colour for those two types, since a colour needs
  the whole spectrum.
- `Water.bb` refuses a particles' ratio of 0, so bb is embedded for each
  of the three ratios rather than as bb(0) and bp.
- A further test sets the page's values against
  `examples/ocean_colour_and_secchi.py` part 13: the depths at which the
  bottom's share falls to 10 percent agree within 3.6 percent, the
  difference being pure water's backscattering (the example takes
  `pure_water_backscattering`, the page `Water.bb`, the source's own
  model).

## 122. The dip at 45 degrees against EUMETSAT's OLCI table (1.26.9): a record

NEXT_STEPS left one comparison for the dip of section 116: the f/Q table
of the OLCI processor, in the auxiliary file `OL_2_OCP_AX`,
which the user could not obtain from EUMETSAT or from the Copernicus
reprocessing service. **This section is a record, as section 117 was:**
the file turned up on 2026-11-26, was read and compared before anything
went into the repository, and is written down here with the method as it
was run. The user asked on 2026-11-26 for it to be recorded as 1.26.9.

**The file.** The user found that the new processing framework (EOPF)
names the file `S03_ADF_OLOCP` (its OLCI documentation, version 0.3.0,
https://s3.pages.eopf.copernicus.eu/OLCI/s3olci/0.3.0/pdfs/ADFS_S3_OLCI.myst.html,
which lists the name and gives no detail). The EOPF project's ADF
documentation (`docs/adfs/access.md` of the public repository
cpm/adf-auxiliary-data-file on gitlab.eopf.copernicus.eu) says that
"The common ADFs generated in the EOPF format are available in the common
public read-only buckets" at endpoint https://s3.sbg.perf.cloud.ovh.net/,
bucket `dpr-common`. Listed without credentials, the bucket's folder
`S3AOLCIdataset/` holds the legacy OLCI Level-2 files, among them

    S3A_OL_2_OCP_AX_20160216T000000_20991231T235959_20170609T120000___________________MPC_O_AL_003.SEN3.zip

4,095,096 bytes, MD5 2d080e4c1834281212e0583ad0f02e56 (the bucket's
ETag), SHA-256 f0289859027e33fc0846b5fb9d40834774b66ac952d6628d7ff8aaf008dd2ea8,
fetched 2026-11-25 (UTC). It holds `OL_2_OCP_AX.nc` (netCDF-4, dated
2017-07-05 in the zip) and a manifest. This is version AL_003 of
Sentinel-3A's file, the one the reprocessing baseline lists
(RRPP-TN-0007, AUXIP); EUMETSAT's product notice of 2019 names AL_004 as
operational, and NEXT_STEPS records EUM_O_AL_008 as the latest. No
Sentinel-3B file is in the bucket. Which of these differ in f/Q is not
known.

**What the file holds.** `f_over_q_LUT`, "LUT for the bidirectional
factor f_over_q (case1 waters)", over an aerosol optical thickness of 0.1
(one value), wind speeds 0, 5 and 10 m/s, 11 OLCI wavelengths (400 to
708.75 nm), the sun at 0 to 75 degrees every 15, 30 refracted nadir
angles from 1.0785 degrees (the archive's first 17 to within 0.0005), 13
azimuths and the archive's six Chl, as EUMETSAT's format specification
(EUM/RSP/DOC/23/1380745, Table 8) describes it. At the first nadir angle
it does not depend on the azimuth.

**What was compared.** As in section 117: f/Q at the first nadir angle;
the departure at 45 degrees from the chord between 30 and 60 degrees, in
1 - cos theta_s; and the ratio EUMETSAT/archive at the six wavelengths
both have (412.5 to 620 nm; the archive's 660 is not an OLCI band), at 45
degrees against the chord of the same ratio. Each wind speed separately,
since the archive has no wind.

**What was found.**

- It is not the archive: over all runs at the shared wavelengths it
  differs by -6.8 to +5.2 percent. Nor is it NASA's recomputation of
  section 117 read at the same aerosol optical thickness: they differ by
  0.6 to 5.2 percent at the nadir (their nadir rows are not at the same
  angle, and the NASA file has no wind), so this is not followed further.
- It has no dip: at 0.03 mg m^-3 its nadir f/Q at 45 degrees lies -0.31
  to -0.20 percent from the chord over all 11 wavelengths and three wind
  speeds, as 0.1 mg m^-3 does (-0.28 to -0.05); every Chl, -0.31 to
  +0.84.
- Along the sun angle it follows the archive except at the one run: the
  ratio stands +1.09 to +2.96 percent above its chord at 0.03 mg m^-3,
  largest at 620 nm, the reddest shared wavelength, and -0.64 to +0.29 at
  every other Chl.

So this version of the OLCI processor's table does not have the dip, as
the authors' later tables do not; the archive's run stays the one out of
line.

**What goes into the repository.** The file is not shipped, for the
reason of section 117 (no licence stated with it). The user's copy goes
to `sources/eumetsat_ocp/` (ignored by git). `examples/fq_at_45_degrees.py`
gains `--olci PATH` (the zip or the .nc in it), read with h5py if it is
installed and only then; the tests that read it are skipped without it.
OPEN_QUESTIONS.md question 6 and DATA.md section 48 record the finding.
Nothing in the package changes; the run stays suspect. Version 1.26.9.

## 123. An example on Snell's window (1.26.10): the plan

NEXT_STEPS (section 2, polarisation) kept one thing within reach without
solving radiative transfer: the geometry of Snell's window, "in an
example". The user asked for it on 2026-11-26. Nothing in the package
changes; the example is the 31st, `examples/snells_window.py`, for those
who look up from under water: divers, underwater photographers, and those
who study what animals see from below.

**What it computes.** Parts 1 to 5 are geometry and Fresnel's equations
at a flat surface, written in the example (the package has no public
Fresnel function, and examples use only the public API). Part 6 is
measured.

1. The window's half-angle, arcsin(1/n). The package carries no
   refractive index of sea water as a function; it uses 1.333 (Gordon
   1989, section 74) and 1.34 (Lee et al. 1998, section 113). The example
   gives the half-angle for n from 1.33 to 1.35, a range that covers
   fresh to sea water across the visible, and says the value moves with
   wavelength, salinity and temperature; it puts no number on that.
2. The squeeze. Where in the window an object at elevation e above the
   horizon appears (theta_w = arcsin(cos e / n) from the zenith), and the
   solid angle: the whole sky, 2 pi sr, fills a cone of
   2 pi (1 - cos theta_c).
3. How bright the window is across its radius, for a sky of uniform
   radiance: n^2 (1 - rho(theta_a)), rho Fresnel's reflectance for
   unpolarised light; the darkening towards the rim.
4. Outside the window: the reflectance of light from below, which rises
   to 1 at the critical angle; outside it the surface is a mirror of the
   water below.
5. The window on the surface: radius d tan(theta_c) for an eye at depth d.
6. Measured: Tyler's (1958) radiance distribution
   (`tyler1958_radiance`, Lake Pend Oreille, clear sky, sun at 56.6
   degrees altitude), tilts every 10 degrees, acceptance 6.6 degrees.

**Part 6's test, set before it is run.** Already seen while planning:
the columns at azimuths 90 and 180 degrees at 4.24, 10.4 and 29.0 m,
where at 4.24 m the step from 40 to 50 degrees looked the steepest and at
10.4 m it did not. The test: at each depth and at each tabulated azimuth
from 90 to 180 degrees from the sun's (away from the sun and its glitter),
take the ratio of radiance between neighbouring tilts, L(t)/L(t + 10),
for t from 0 to 80 degrees (looking up). The window's edge, at 47.8 to
48.8 degrees, lies in the 40-50 step; the edge counts as seen at a depth
and azimuth where that step has the largest ratio. The example reports
at which depths and azimuths it is, and nothing about why beyond what
the numbers show. Tyler's cells marked suspect are not used.

**Before you use any of this** (the example's closing list): a flat
surface (waves break the window into moving pieces); a uniform sky in
part 3; one refractive index for all wavelengths; no scattering in parts
1 to 5, which is what part 6 shows blurring the edge with depth;
Tyler's lake, one day, one sun.

**Checks.** Every number the documents quote is the example's own output
(a new test file); the geometry is checked against identities (the
window's half-angle at e = 0 is theta_c; reflectance 0.02 at normal
incidence for n = 1.333 to within 0.001; transmittance plus reflectance
equal 1); the example uses only the public API. README.md,
examples/README.md and docs/examples.rst count and list it. A release of
an example, 1.26.10.

**Result.** Parts 1 to 5 as planned: the half-angle is 48.3 degrees at n
= 1.34 (47.8 to 48.8 from 1.33 to 1.35); the lowest 20 degrees of sky
crowd into the outer 3.7 degrees of the window; an even sky is seen 1.76
times as bright at the window's centre, and the transmitted share falls
below a half 0.4 degrees inside the rim; the window is a circle 1.121
times the eye's depth in radius.

Part 6, by the test set beforehand: Tyler tabulated azimuths every 20
degrees, so the azimuths tested are 100 to 180. Of the 5 at each depth,
the 40-50 step is the steepest at 3 at 4.24 m, 1 at 10.4 m, 2 at 16.6 m,
3 at 29 m, and at none from 41.3 m down. At the other 26 the steepest step
is near the zenith (0-10 degrees, 7), at 30-40 (1), or below the edge
(50 to 80, 18). So the edge stands out in the measurements at some
azimuths down to 29 m and nowhere deeper; at 10 degree steps with a 6.6
degree field of view, that is all they can say.

**Differences from the plan, noted after the code.**

- What was seen before the test: the column printed as "azimuth 90" was
  in fact azimuth 80 (the tenth of the ten azimuths, 0 to 180 every 20,
  is 180; the fifth is 80), so what was looked at was azimuths 80 and
  180. At 4.24 m both showed the 40-50 step as the steepest of the steps
  from 30 to 60 degrees, which suggested the edge would be seen there at
  every azimuth; the full test, which also counts the 0-10 step, finds it
  at 3 of 5.
- The table of part 3 stops at 48.2 degrees, inside the window at n =
  1.34; the half-transmission angle is found on a fine grid, not from the
  table's rows.

## 124. The refractive index of sea water: Quan & Fry (1995) (1.27.0): the plan

The package carries no refractive index of water as a function: two
functions hold the index their papers used (1.333 for Gordon 1989,
section 74; 1.34 for Lee et al. 1998, section 113), and the Snell's-window
example (section 123) had to take a range, 1.33 to 1.35, as a choice. The
user asked on 2026-11-26 for a function, built on Quan & Fry (1995).

**The source.** Quan, X. and Fry, E. S. (1995), "Empirical equation for
the index of refraction of seawater", Appl. Opt. 34(18), 3477-3480,
doi:10.1364/AO.34.003477 (the DOI resolves to this paper; the PDF read is
a copy on a university site, not shipped). Their Eq. (3), at atmospheric
pressure:

    n(S, T, l) = n0 + (n1 + n2 T + n3 T^2) S + n4 T^2
                 + (n5 + n6 S + n7 T) / l + n8 / l^2 + n9 / l^3

with S in per mil, T in degrees Celsius, l in nm, and n0 = 1.31405, n1 =
1.779e-4, n2 = -1.05e-6, n3 = 1.6e-8, n4 = -2.02e-6, n5 = 15.868, n6 =
0.01155, n7 = -0.00423, n8 = -4382, n9 = 1.1455e6 (p. 3479, read from the
page image: the text layer garbles the minus signs). "The ranges of
validity are 0 < T < 30 C, 0 < S < 35 per mil, and 400 nm < l < 700 nm."
The equation is a fit to Austin & Halikas's (1976, SIO Ref. 76-1) selected
data, reprinted as the paper's Table 1: 11 wavelengths (404.7 to 700 nm),
S = 0 and 34.998, T = 1 to 30 C, 154 values, measured by Mehu &
Johannin-Gilles (stated accuracy 3e-5), except those at 700 nm, which
"are extrapolations from the experimental data that were made by A&H".
The paper gives the fit's rms deviation from Table 1 as 1.5e-5; computed
here from the transcription, 1.56e-5 (seen while planning).

**The function.** `quan1995_refractive_index(wavelength_nm, /, *,
salinity_psu, temperature_c)`, in a new module `jerlov/refraction.py`.
Public names 142 -> 143.

- Salinity and temperature have no default (the package's rule: what the
  water does not fix is the caller's). The keyword is `salinity_psu`, as
  everywhere in the package; the paper's S is in per mil, from
  Copenhagen standard water, and the difference between that and
  practical salinity is not modelled; the docstring says so.
- The three inputs broadcast. Outside 400-700 nm, 0-35 and 0-30 C (the
  ends included, as Table 1 has them) is refused with ValueError, not
  extrapolated; inf is refused; NaN in the wavelength gives NaN.
- Above 643.8 nm the fit rests on the 700 nm values, which are Austin &
  Halikas's extrapolations, not measurements: a ProvenanceWarning there,
  as the package warns wherever a source extrapolated.
- Pressure is left out. The paper's own estimate (p. 3477): at 100 m the
  index rises by less than 1.37e-4; the docstring quotes it and adds
  nothing.
- Nothing else changes: Gordon's 1.333 and Lee's 1.34 are their papers'
  values and stay.

**Tests.** Table 1 transcribed into the test file as numbers written out
(checked against the page image), with the paper's own check: the rms
deviation of the function from it, 1.5e-5 to the digit the paper prints;
every value within 5e-5. The coefficients and range as printed; the
refusals; NaN; broadcasting; the warning only above 643.8 nm; the
caller's arrays not modified.

**Where it is used.** `examples/snells_window.py` part 1 takes its range
of indices from the function (fresh to sea water, 0 to 30 C, 400 to 700
nm) instead of the stated 1.33 to 1.35, and gives the half-angle at its
extremes; the rest of the example keeps n = 1.34, which the function
gives for sea water in the green (to be stated with the number it
gives). DATA.md gains section 51; docs/api.rst and docs/choosing.rst
list the function; `.zenodo.json` gains a line. A release with a new
public function, 1.27.0.

**Result.** As planned. The function reproduces Table 1 within 5e-5 at
every value; the index runs from 1.3291 to 1.3515 over the equation's
range, and sea water at 35, 20 C and 550 nm has 1.3408.
`examples/snells_window.py` part 1 now shows four waters from the
function and its extremes over the range (half-angle 47.7 to 48.8
degrees, against 47.8 to 48.8 from the fixed indices of 1.26.10); parts 2
to 6 keep n = 1.34, 0.04 degrees from sea water at 550 nm.

**Differences from the plan, noted after the code.**

- The plan expected the rms deviation from Table 1 to round to the
  paper's 1.5e-5. Over all 154 values it is 1.56e-5, which does not; over
  the 140 measured ones, without the 14 extrapolated at 700 nm, it is
  1.47e-5, which does. Why the paper's figure is the lower one is not
  known; the test checks both numbers and that the paper's lies within
  0.1e-5 of them.
- The example's part 1 shows the index at 700 nm, which warns; the
  example catches that warning by type and says why it shows the value
  all the same (it is the lowest the equation gives).

## 125. The uncertainties of the published pure water absorption spectra (1.28.0): the plan

Since 1.4.0 (section 70) the CSVs of `pure_water_absorption_table` carry
each paper's uncertainty column, transcribed and checked, but the function
does not return them (NEXT_STEPS section 6). The user asked on 2026-11-26
for them to be returned.

**What the columns are, by each paper's own words.** They are not the same
quantity, and the package does not make them one.

- Pope & Fry (1997), Table 3: sigma, "the statistical standard
  deviation", and a percent error that adds it "in quadrature with the
  error in the absolute value of the absorption coefficient for the
  calibration reference samples (estimated at 2%) ... rounding up to an
  integer percentage" (p. 8719, as quoted in `tools/build_pure_water_aw.py`,
  which checks all 140 rows against that rule).
- Mason, Cone & Fry (2016), Table 2: sigma, printed with every value in
  units of 1e-3 1/m; the abstract gives the minimum as 0.000811 +/-
  0.000227 1/m (DATA.md section 29). The paper was read for 1.4.0; it is
  not openly available and was not read again for this.
- Lee et al. (2015), Table 1: Delta aw, "the estimated uncertainty of
  aw_D, which is derived from the absorption properties of the gyre waters
  following the error propagation scheme", their Eq. (17), assuming "a 15%
  uncertainty for each component" (pp. 554-555, read from the PDF on
  2026-11-26). An estimate from a propagation with an assumed input, not a
  measured spread.
- Smith & Baker (1981) and Morel et al. (2007) print none.

**The function.** A new one, so that `pure_water_absorption_table` and
what it returns stay as they are (the 1.0 promise):
`pure_water_absorption_uncertainty(wavelength_nm, /, *, source)` returns
`PureWaterAbsorptionUncertainty`: `wavelengths_nm`, `aw` (as
`pure_water_absorption_table` gives it there), `uncertainty` (1/m, the
paper's column as printed), `percent_error` (Pope & Fry's printed
percent; None for the others), `meaning` (one sentence: which quantity
the column is, from the list above) and `source`. Public names 143 -> 145.

- **Only at the printed wavelengths.** Between them the package
  interpolates aw linearly, but an uncertainty is not a quantity whose
  value between two independent estimates is known; asking at another
  wavelength is refused with ValueError naming the nearest printed ones.
- **Sources without one** (`smith1981`, `morel2007`, `morel2007_aw2`):
  MissingQuantityError, the package's error for what the data do not
  give.
- **`lee2015_smoothed`**: the table prints one Delta aw per row, for
  aw_D; at the five wavelengths where the smoothed value replaces it, the
  Delta aw is returned with a ProvenanceWarning that it was not given for
  the smoothed value.
- Flagged rows warn as they do in `pure_water_absorption_table`.
- Scalars in, floats out; arrays in, arrays out (copies).

**Docs.** `pure_water_absorption_table`'s docstring points to the new
function; DATA.md section 29's "Not used" paragraph says what is now
returned (no new DATA section); docs/api.rst and docs/choosing.rst list
both names.

**Tests.** The values equal the CSV columns at every printed wavelength;
Pope & Fry's percent is returned as printed and follows from sigma and
2 percent (the build script's rule, recomputed); off-grid and
out-of-range wavelengths and the three sources without a column are
refused; the warning for `lee2015_smoothed` at exactly its five
wavelengths; scalar and array forms; the caller's array is not modified;
`pure_water_absorption_table` returns what it did. A release with new
public names, 1.28.0.

**Result.** As planned. The function returns each paper's column as
printed at all of its printed wavelengths (140 for Pope & Fry, 131 for
Mason et al., 41 for Lee et al.); Pope & Fry's percent error follows from
sigma and 2 percent at every row, as the build script already checks;
`lee2015_smoothed` warns at 360, 370, 385, 395 and 400 nm and nowhere
else; `pure_water_absorption_table` returns what it did.

**Difference from the plan.** The plan gave the page of Lee et al.'s
words as 556; they are on pp. 554 ("the estimated uncertainty") and 555
("a 15% uncertainty"), corrected before the code.

## 126. A review after 1.28.0, and what every public input must be (1.29.0): the plan

The user asked on 2026-11-26 for a review of the whole package, for bugs,
inconsistencies and what could be better, and with it two items of
NEXT_STEPS section 6: (1) one number's check accepts a bool, which section
105 left as it was; (2) the flat methods of
`rottgers2013_scatter_correction` keep a gap in cm, which section 105
made the documented behaviour.

**How the review was made.** Not every value was derived again: the
earlier reviews (sections 80, 88 and 105) and the tests against the
papers stand for that. This one (a) called every one of the 84 public
functions from a valid call, then with each numeric argument in turn
replaced by a bool, NaN, inf, numeric text ("1.0"), a negative value and
an empty array, recording what each did, and checked that no call
changed the caller's arrays; (b) checked that every warning points at
the caller (`caller_stacklevel`), that no module integrates with
`np.trapz` directly, that the parameters a docstring documents exist,
and that a single number in gives a float out; (c) read the code added
since section 105: `forward_scatter`, `attenuation_within` (1.23.0),
`lee1999_shallow_rrs` (1.26.0), the suspect-run warning of
`morel2002_fq_tables` (1.26.3), `quan1995_refractive_index` (1.27.0) and
`pure_water_absorption_uncertainty` (1.28.0). The harness is a script
kept out of the repository; what it found is below.

**Found.** No wrong value, no input modified, no warning pointing inside
the package, no documented parameter that does not exist.

- **A. A bool is taken as a number almost everywhere** (item 1): by 101
  of the numeric arguments probed (all but those that already refuse it
  through a range check), in arrays as well as alone, and by the
  methods (`Water.a(True)` is refused only because 1 nm is out of range).
- **B. Numeric text is taken as a number in many places**: 42 numeric
  arguments of functions, and methods such as `Water.a("500")`, convert
  "1.0" with `np.asarray(..., dtype=float)`. Since 1.22.1
  `_data.finite_number` refuses text (section 105, item 3); the rest of
  the package does not. The same input is refused in one function and
  read in the next.
- **C. `solar_fraction` takes an infinite depth** and returns 0 with a
  ProvenanceWarning, where the package's rule is that inf is refused.
- **D. IndexError where a ValueError is meant**:
  `pure_water_absorption_uncertainty` with an empty array (added in
  1.28.0; `pure_water_absorption_table` returns an empty array), and
  `par_profile` with no wavelengths, `xyz_to_srgb` with a single number
  and `integrate_response` with a single number for the spectrum, which
  fail inside the computation instead of saying what is wrong.
- **E. Item 2.**

**What changes.**

- **A and B, in one place.** Every public function and every public
  method of a public class (33 methods: `Water.a`, `Scene.observe`,
  `ParProfile.depth_of_fraction`, ...) checks its arguments on entry: a
  bool, alone or as an element of an array, list, tuple or dict's
  values, is refused with ValueError unless the parameter is a switch
  (annotated `bool`: `clip`, `beta`, `include_sparse`,
  `include_non_types`); text is refused the same way unless the
  parameter names something (annotated `str`, or one of the unannotated
  names that take a name: `source`, `method`, `colour_space`,
  `station`, `water_type`, `types`, `material`, `text`, `path`, ...).
  The check wraps the package's public names once, in
  `jerlov/__init__.py`, both where the package exports them and in the
  module that defines them, so that it cannot be missed by a new
  function, and a test calls every public function and method with a
  bool and with text in each numeric argument. `_data.finite_number`
  also refuses a bool itself. These are refusals of inputs no docstring
  offered, as in sections 81 and 105.
- **C.** `solar_fraction` (and `ShortwaveParameters.fraction_at`)
  refuse an infinite depth.
- **D.** `pure_water_absorption_uncertainty` returns empty arrays for an
  empty request, as `pure_water_absorption_table` does; the other three
  refuse with a ValueError naming what is wrong.
- **E.** The flat methods stop carrying cm's NaN into the result: they do
  not use cm, so a gap in cm says nothing about the result there. cm must
  still broadcast with am, and the result keeps the broadcast shape. This
  changes returned values (NaN becomes a number where only cm has a gap),
  so the docstring, the test of section 105 and the CHANGELOG say so.

Because values change (E) and inputs that were read are refused (A, B,
C), the release is 1.29.0, not a patch. Nothing a docstring documents
stops working.

**Tests.** A table of valid calls to every public function and method,
and with each numeric argument made a bool or text: refused, with the
parameter's name in the message; switches and names still accepted; the
public names are all wrapped (so a new one cannot escape); C, D and E as
above; the whole suite and the examples unchanged otherwise.

**Result.** As planned. The harness run again after the change: a bool or
text is refused at every numeric argument of every function it calls (it
was read at 101 and 42), no caller's array is modified, and every
function's valid call still works. The 31 examples run unchanged with
ProvenanceWarning as an error. The check costs nothing measurable:
`Water.a` over 301 wavelengths took 443 microseconds wrapped against 524
unwrapped, in one timing on one machine (within its noise).

**Differences from the plan, noted after the code.**

- A switch is recognised by its annotation alone (`bool`), not by name:
  `bb_from_vsf`'s first argument is also called `beta`, a number, and a
  list of switch names let a bool through there. The names that take
  text stay a list, since several are not annotated.
- The list also has `water` and `scattering`, which take a `Water` or a
  `ScatteringFunction` and already answer a name with their own
  `TypeError` (tests/test_rendering.py checks it), and `wind`, which
  `Morel2002FQTables.surface_factor` takes as "flat" or a speed. A bool
  is still refused at all three. Found when the tests were run outside
  the source tree, not by the harness, which passed numbers only.
- Two older tests asserted the error for text at a numeric argument:
  `tyler1958_radiance("abc")` gave a `KeyError` and
  `morel2002_nadir_fq("412.5", ...)` the message of `finite_number`. Both
  now get the check's `ValueError`, and the tests say so.
- `integrate_response` now asks for a one-dimensional spectrum and
  wavelengths in so many words, as its docstring describes them (one
  value per wavelength).
- The test of section 105 that pinned the flat methods' NaN
  (`test_the_flat_methods_keep_a_gap_in_cm`) is rewritten to the new
  behaviour and renamed, as the plan said it would be.

## 127. The Fournier-Forand phase function (1.30.0): the plan

Section 13 left out forward-scatter blur because it needs the whole phase
function, and section 27 shipped Petzold's eight stations as measured,
without the "average particle" phase function HydroLight users know.
Since then three things have needed a phase function the caller can set
by its backscatter ratio: the shallow-water closure (section 115, where
the phase function alone moved the model against the Monte Carlo by up
to 1.92 times), `lee2011_rrs`, whose coefficients were fitted to
HydroLight runs with a blend of Petzold's average and a Fournier-Forand
of bb/b = 1 percent (section 73), and the forward-scatter candidates of
NEXT_STEPS section 5. The user chose this on 2026-11-26.

**The sources.** The form used is the one Mobley, Sundman & Boss (2002),
"Phase function effects on oceanic light fields", Appl. Opt. 41(6),
1035-1050, doi:10.1364/AO.41.001035, print as Eqs. (1) and (2), p. 1037,
calling it the "latest form" of Fournier & Forand's phase function, from
Fournier & Jonasz (1999), "Computer-based underwater imaging analysis",
Proc. SPIE 3761, 62-70, doi:10.1117/12.366488:

    beta(psi) = 1 / (4 pi (1 - d)^2 d^nu)
                  [nu (1 - d) - (1 - d^nu)
                   + (d (1 - d^nu) - nu (1 - d)) sin^-2(psi / 2)]
              + (1 - d180^nu) / (16 pi (d180 - 1) d180^nu) (3 cos^2 psi - 1)

    nu = (3 - mu) / 2,  d = 4 / (3 (n - 1)^2) sin^2(psi / 2)

with n the particles' real index of refraction relative to water, mu the
slope of the hyperbolic (Junge) size distribution and d180 the d at 180
degrees; and Eq. (3), the backscatter fraction:

    B = 1 - (1 - d90^(nu + 1) - 0.5 (1 - d90^nu)) / ((1 - d90) d90^nu).

Neither 1999 paper nor Fournier & Forand (1994, Proc. SPIE 2258,
194-201) was obtained; the equations are read from Mobley et al.'s page
image (the PDF read is a copy on the University of Maine's course site,
misclab.umeoce.maine.edu, not shipped), and the docstring says they were
read there. Mobley's Ocean Optics Web Book page on the function
(oceanopticsbook.info, updated 2021-10-13) prints the same three
equations.

**What a backscatter ratio does not fix.** B depends on n and mu
together, and Mobley et al. say so (p. 1042: "there is no unique pair of
n and mu values corresponding to a given Bp"). For HydroLight they chose
a line, "for simplicity", through n = 1.01 at the smallest mu (3) and
their fit to Petzold's average (n = 1.10, mu = 3.5835):

    n = 1.01 + 0.1542 (mu - 3),               Eq. (7)
    2 / (3 d90) = (0.01 - 0.3084 nu)^2,       Eq. (8), the same line.

It is a choice, not a law: the Web Book's own Table 1 gives five (n, mu)
pairs for B = 0.0001 to 0.4, and none lies on it (at B = 0.4, n = 1.15
where the line gives 1.299). Seen while planning, with Eq. (3): those
five pairs give B = 0.000103, 0.00100, 0.0100, 0.1001 and 0.4005, the
printed values to their digits.

**The functions.** A new module `jerlov/fournier_forand.py`. Public names
145 -> 148.

1. `fournier_forand(*, refractive_index, junge_slope)` -> `FournierForand`:
   the phase function of a given n and mu, both required, no default.
2. `mobley2002_fournier_forand(backscatter_ratio, /)` -> `FournierForand`:
   n and mu on Mobley et al.'s line, Eq. (8) solved with Eq. (3) for nu
   (by bisection; B rises with mu along the line, to be checked by a
   test). The line is in the name, so that whoever calls it has chosen
   it, as with `qaa_v6` or `lee2011_rrs`.
3. `FournierForand`, a frozen result with `refractive_index`,
   `junge_slope`, `nu`, `backscatter_ratio` (Eq. 3), `relation` (None, or
   the line's citation when made by 2), and three methods:
   - `phase_function(angle_deg)`, 1/sr, Eq. (1). Refuses 0 degrees,
     where it is infinite, and anything outside (0, 180].
   - `cumulative(angle_deg)`: the share of scattering within angle_deg,
     2 pi integral from 0 of beta sin. Mobley et al. say a closed form
     exists in Fournier & Jonasz, which was not obtained. Derived here
     from Eq. (1), with s = sin^2(psi / 2):

         F(psi) = (1 - d^(nu + 1) - (1 - d^nu) s) / ((1 - d) d^nu)
                + (1 - d180^nu) / (8 (d180 - 1) d180^nu) cos(psi) sin^2(psi).

     F(0) = 0, F(90) = 1 - B of Eq. (3), F(180) = 1; seen while
     planning: its derivative matches 2 pi beta sin(psi) to 5e-7 at the
     Petzold fit. The same quantity as `ForwardScatter.fraction`, for
     this phase function.
   - `mean_cosine()`: -1 + integral from 0 to pi of F(psi) sin(psi), by
     the trapezoid on a fine grid (F is bounded, beta is not).

   Where d^nu would lose digits (nu near 0), 1 - d^nu is computed as
   -expm1(nu log d).

**The range accepted.** The form is for 3 < mu <= 5, the range the Web
Book gives for oceanic Junge slopes and Mobley et al.'s Fig. 2 axis: at
mu = 3 (nu = 0) it is 0/0, and at mu = 5 it is symmetric, B = 0.5 for any
n. n must exceed 1, and d180 must exceed 1 (n < 1 + 2/sqrt(3) = 2.155),
or the form divides by zero within 0-180 degrees. Seen while planning:
on a 120 x 120 grid over that region the function is positive at every
angle tried. Mobley et al.'s Fig. 2 shows n only to 1.20 and the Web
Book's pairs to 1.175; the line reaches 1.318 at B = 0.5. Values between
are accepted without a warning: the form is a formula, not a table, and
nothing is extrapolated from data (the docstring states where the
published pairs lie). For `mobley2002_fournier_forand`, B from 0.0001 to
0.5, the range of HydroLight's library of these functions (Mobley & Sundman, HydroLight 5.1
Technical Documentation, p. 22) and of the line within 3 < mu <= 5.

What is refused, as elsewhere: NaN and inf (one number each, so no gap
to mark), a bool or text (section 126), angles outside (0, 180], arrays
of angles of more than one dimension. The caller's array is not
modified.

**Not done here.** `forward_scatter`, `attenuation_within`,
`henyey_greenstein_fit` and `osoaa_phase_function` take a Petzold
`ScatteringFunction` only, and stay so; letting them take a
`FournierForand` is a later decision, with its own section. No average
Petzold phase function is added (section 27 stands). No example changes.

**Tests (the criteria).**
- Eq. (1) over the sphere integrates to 1 within 1e-6, numerically in
  log angle, at five (n, mu) pairs with mu >= 3.3 (nearer 3 the forward
  peak is too narrow for a numerical integral, and F is checked instead).
- `cumulative`: F(180) = 1 within 1e-12; 1 - F(90) equals Eq. (3) within
  1e-12; the central difference of F equals 2 pi beta sin within 1e-5
  relative at angles from 0.1 to 179 degrees.
- Eq. (3) equals the numerical integral over 90-180 degrees within 1e-6.
- Mobley et al.'s Petzold fit: n = 1.10, mu = 3.5835 gives B = 0.0183
  to the printed digits; `mobley2002_fournier_forand(0.0183)` gives
  mu = 3.5835 and n = 1.10 to the printed digits; Eqs. (7) and (8) agree.
- The Web Book's five pairs give its five B to the printed digits.
- Along the line B rises with mu; mu = 5 gives B = 0.5.
- The function is positive at every angle on a grid of (n, mu).
- The refusals; arrays and numbers; the caller's array untouched.

DATA.md gains section 52; docs/api.rst, docs/choosing.rst and the topic
page on measurements and scattering list the functions; `.zenodo.json`
gains a line. A release with new public functions, 1.30.0.

**Result.** As planned in the functions and their range. Eq. (1)
integrates to one and Eq. (3) is its integral over the back hemisphere,
both within 1e-6; the closed-form cumulative share meets 1 at 180 degrees
and 1 - B at 90 within 1e-12, and its derivative is Eq. (1) times 2 pi
sin within 1e-5. Mobley et al.'s fit to Petzold's average gives B =
0.018313. Along their line B rises with mu, from n = 1.021 at B = 0.0001
to n = 1.318 at 0.5. The function is positive at every angle tried over
the accepted (n, mu). Its mean cosine at the Petzold fit is 0.9300.

**Differences from the plan, noted after the code.**

- The plan said none of the Web Book's five (n, mu) pairs lies on
  Mobley et al.'s line. That was written from a glance at the numbers,
  not computed, and is wrong: four lie within 0.005 of it in n (at their
  mu the line gives 1.0214, 1.0410, 1.0845 and 1.1742 against 1.021,
  1.040, 1.08 and 1.175); only the one for B = 0.4 (n = 1.15, mu = 4.874,
  where the line gives 1.299) is far from it. The point the plan made
  stands on that one pair: the line is a choice, not what every author
  uses. The docstring, DATA.md section 52 and a test say it this way.
- The plan expected `mobley2002_fournier_forand(0.0183)` to give mu =
  3.5835 to the printed digits. It gives 3.5834: the fit (n = 1.10, mu =
  3.5835) lies just off the line (n = 1.099976 at that mu), and its B is
  0.018313, not 0.0183 exactly. From the fit's own B the line gives mu
  within 1e-4 of 3.5835, and the test checks that.
- The integral of Eq. (1) over the sphere could not be taken numerically
  right up to 0 degrees: below 1e-9 degree the forward peak is too narrow
  to sample, and at n = 1.05, mu = 3.3 that part is 0.12 percent of the
  whole. The tests take that part from the closed form (checked under 0.2
  percent) and the rest numerically, for the sphere and the mean cosine
  alike.
- `MOBLEY2002_RELATION` stayed private; the text of the line is in the
  result's `relation`.

## 128. Why the colour changes on the first site page, and forward scattering with a Fournier-Forand phase function (1.31.0): the plan

Two pieces of work, one release, as the user asked on 2026-11-27.

### A. The first site page says why the colour moves from blue to orange

The user, looking at `dive.html`, asked why the columns turn from blue
in type I to orange in 9C, and whether research explains it. The page
shows the colour but not the reason. It gains a panel, "Why the colour
changes", between the readouts and the materials.

**What it shows.** A chart of Kd against wavelength, 380-700 nm, on a
log scale: the ten types' Kd (Jerlov 1976, the values the page already
embeds) as thin lines, the selected type drawn heavily, with a dot at the
printed wavelength where its Kd is least; and pure water's absorption,
Pope & Fry (1997), dashed, from `pure_water_absorption_table(...,
source="pope1997")`, as the floor no water can go below at the red end.
It follows the type the reader picks.

**What it says,** every number computed by tools/site_pages.py from the
package and filled into the page, so that tests/test_site_pages.py checks
it, as the page's other figures are:

1. The window. Among the wavelengths Jerlov printed (400 to 700 nm,
   every 25 nm), Kd is least at 475 nm for I, IA, IB and II, at 500 nm
   for III, at 550 nm for 1C to 7C and at 575 nm for 9C (seen while
   planning). The window is where the light that is left lies, so its
   colour follows it.
2. The red end. At 650 nm pure water alone absorbs 0.34 /m (Pope & Fry),
   and Kd is 0.36 to 0.76 /m over the ten types: in the clearest water,
   almost all the red that is lost is lost to the water itself.
3. The blue end. At 400 nm Kd is 0.028 /m in I and 2.4 /m in 9C, 86 times
   as much; at 650 nm only 2.1 times. What is added to the water absorbs
   most in the blue.
4. What is in it, in the sources' own words. Jerlov (1976, *Marine
   Optics*, p. 137), quoted in DATA.md section 41 (read for 1.15.8): the
   coastal types "are derived from observations along the coast of
   Scandinavia and western North America. These northern water masses
   are characterized by a relatively high amount of yellow substance."
   And the model Williamson & Hollins (2022) fitted to the types IB to 5C:
   what their a holds beyond pure water's (a - aw, with the aw they used,
   DATA.md section 20) is 5.4 times as large at 412 nm as at 550 nm in IB
   and 4.3 times in 5C.
5. What is not known: which part of each type's blue loss is dissolved
   matter, which phytoplankton and which other particles was not recorded
   with the types, and the page says so. Nothing is said of what any one
   substance absorbs beyond what these sources print.

The colours themselves are already qualified on the page ("Many of them
lie outside sRGB and are clipped"); the panel adds that a narrow window
makes nearly monochromatic light, which is why the deeper colours are
the ones clipped. Sources: Pope & Fry (1997) and Williamson & Hollins
(2022) join the page's list.

**Tests.** The page is what the tool writes (as now); the windows, the
red and blue figures and the ratios are recomputed from the package in
tests/test_site_pages.py and found on the page; the quotation is found in
DATA.md as well as on the page; the page still asks nothing of another
host.

### B. Forward scattering with a Fournier-Forand phase function

1.30.0 added `FournierForand` and left `forward_scatter` and
`attenuation_within` taking Petzold's stations only (section 127, "Not
done here"). This lets them take a Fournier-Forand too.

**The difference that matters.** A Petzold station is the whole water,
pure water and particles. A Fournier-Forand phase function is the
particles' alone, so applying its share to a water's whole b would give
pure water the particles' forward peak. Pure water scatters almost
nothing forward of small angles: with the shape `pure_water_vsf` uses
(Morel's, depolarisation ratio 0.09), its share within 5 degrees is
0.27 percent and within 20 degrees 4.2 percent (seen while planning;
closed form below), against 56 and 84 percent for the Fournier-Forand of
Mobley et al.'s Petzold fit.

**The changes.**

1. `forward_scatter(scattering, half_angle_deg)` takes a
   `FournierForand` as well as a `ScatteringFunction`. For it, the share
   is `cumulative(half_angle_deg)`, exact, so there is no warning; the
   half-angle may be 0 to 180 degrees. The result is a `ForwardScatter`
   whose `station` names the phase function (n and mu), whose
   `extension_fraction` is 0, and whose `wavelength_nm`, `c` and
   `c_within` are NaN: the phase function has no water and no c of its
   own. A new field `particles_only` (default False, added at the end so
   existing constructions are unchanged) is True for it.
2. `attenuation_within(water, wavelengths, /, *, forward,
   pure_water_b=None)`. With a Petzold `forward`, as before, and
   `pure_water_b` must be left out (given, it is refused: the station
   already holds its water). With a particles-only `forward`,
   `pure_water_b` is required (`MissingQuantityError` without it, as the
   package does for what the data do not fix): the pure water scattering
   the water's b was built on, 1/m, one number or one per wavelength;
   for example `pure_water_scattering(wl, salinity_psu=...)`. Then

       c_within = c - F_p (b - b_w) - F_w b_w

   with F_p the Fournier-Forand share and F_w pure water's share within
   the same half-angle, from the shape of `pure_water_vsf`:

       F_w(theta0) = [(1 - cos theta0) + r (1 - cos^3 theta0) / 3]
                     / [2 (1 + r / 3)],   r = (1 - 0.09) / (1 + 0.09).

   Where b_w exceeds b, refused; NaN in the water stays NaN.

No new public name; one new keyword and one new field. The Petzold path
gives the same numbers as before, to the bit.

**Tests.** The Petzold path unchanged (its existing tests); for a
Fournier-Forand: the share equals `cumulative` and at 180 degrees
c_within = a; F_w against a numerical integral of `pure_water_vsf`
within 1e-8 at 1, 5, 20, 90 and 180 degrees; the formula against a
direct computation on a water; the refusals (pure_water_b missing,
given with Petzold, larger than b, a bool or text); the caller's array
not modified.

**For the record,** computed in the result, not judged: the share within
1, 5 and 20 degrees of the Fournier-Forand of Mobley et al.'s Petzold fit
against Petzold's stations with a similar B/S.

**Documents.** The topic page on seeing through water and the map gain
the Fournier-Forand path; CHANGELOG; the Zenodo description. A release
with a new keyword and a new page section, 1.31.0.

**Result.** As planned, for both parts.

A. The panel is on the page, between the readouts and the materials, and
follows the chosen type; it was looked at in Chromium at 1280 and 390 px
wide, in both themes, with no script error and no sideways scroll. Its
figures are the planned ones (windows 475, 500, 550 and 575 nm; 0.34 /m
of pure water at 650 nm against Kd 0.36 to 0.76; 86 and 2.1 times; 5.4
and 4.3 times), each recomputed by a test.

B. `forward_scatter` and `attenuation_within` take a Fournier-Forand as
planned; the Petzold path's tests pass unchanged. Pure water's share
within the half-angle meets a numerical integral of `pure_water_vsf`
within 1e-8. For the record, the share within 1, 5 and 20 degrees: 25, 56
and 84 percent for the Fournier-Forand of Mobley et al.'s Petzold fit (n
= 1.10, mu = 3.5835, particles alone), and 23, 51 and 82 percent for
NUC 2240 (B/S 0.018, water and particles together, with the report's
extension below 0.1 degree).

**Differences from the plan, noted after the code.**

- The panel's caption first called pure water's absorption the floor "no
  water can go below". Computed before the commit, that is not true of
  Jerlov's table: at 675 and 700 nm the Kd he printed for types I to II
  lies below Pope & Fry's absorption of pure water, by up to 10 percent
  (type I at 700 nm). The caption now says so and does not reconcile the
  two; a test finds the types and wavelengths. Why is not looked into
  here (NEXT_STEPS records it as a question).
- The red-end sentence first said "almost all the red that is lost is
  lost to the water"; Kd is not an absorption, so it now says that in the
  clearest water Kd at 650 nm is little more than what the water alone
  absorbs.
- The chart's lower limit is 0.003 /m, not 0.005, so that Pope & Fry's
  minimum (0.0044 /m at 417 nm) is drawn.
- Two equal `ForwardScatter`s of a Fournier-Forand compare equal. The
  first commit made their NaN fields one object, which works where a
  dataclass compares its fields as a tuple (identity first), up to Python
  3.12; from 3.13 it compares them one by one, NaN != NaN, and CI on 3.13
  failed (PR #110). `ForwardScatter` now takes `_data.compared_by_value`
  (section 81), which counts NaN equal to NaN on every version and gives
  the station results the answer the generated `==` gave them.

## 129. A correction to section 128: Jerlov's Kd below pure water was known (1.31.1): the plan

Section 128 recorded, as found while drawing the new panel of the first
site page, that at 675 and 700 nm the Kd Jerlov (1976) printed for types
I to II lies below Pope & Fry's absorption of pure water, by up to 10
percent, and said the cause was "not looked into here". The page said
"this page does not reconcile the two", and NEXT_STEPS listed it as a new
question, not recorded in DATA.md.

That was wrong. It has been known since Austin & Petzold (1986, Opt. Eng.
25(3), 471-479, section 7), who wrote that "at some wavelengths the values
given by Jerlov for K are less than the values of absorption alone
published by Morel and Prieur" and recommended replacing them; DATA.md
section 3 records it ("Jerlov's Kd falls below pure sea water (confirmed,
documented in 1986)"), the source 'jerlov1976' carries it as a caveat,
and the package ships Austin & Petzold's replacement as the source
'austin1986'. The search before section 128 was for "below pure", which
the heading's "falls below pure sea water" does not contain.

**The changes.** No value and no code change.

- The panel's caption keeps its computed figures and says instead that
  Austin & Petzold (1986) pointed this out and recommended replacing
  Jerlov's Kd, which jerlov ships as the source 'austin1986' (DATA.md
  section 3). Austin & Petzold join the page's list of sources. A test
  finds the quoted sentence in DATA.md and the citation on the page.
- This section corrects section 128, which stays as written (the file is
  appended to only).
- What is left open is why Jerlov's values lie there; that is the next
  release's work (OPEN_QUESTIONS.md, a seventh question), not this one.

A patch release, 1.31.1.

**Result.** As planned. The caption cites Austin & Petzold (1986) and
DATA.md section 3; the test that finds the figures also finds their
sentence in DATA.md (block quote markers taken out) and the DOI on the
page. The merged description of PR #110 cannot be changed; this section
and CHANGELOG 1.31.1 are the correction of record.

## 130. Why Jerlov's Kd lies below pure water's absorption: a seventh open question (1.31.2): the plan

DATA.md section 3 records, after Austin & Petzold (1986), that Jerlov's
type I Kd falls below the attenuation of pure sea water at several
wavelengths; section 129 corrected 1.31.0, which had taken it for new.
What DATA.md does not record is why. The user chose (2026-11-27) to make
it the seventh open question, and obtained Marshall & Smith (1990), the
paper that names the mechanisms.

**The sources, read for this.**

- Marshall, B. R. and Smith, R. C. (1990), "Raman scattering and in-water
  ocean optical properties", Appl. Opt. 29(1), 71-84,
  doi:10.1364/AO.29.000071 (the user's copy, not shipped). Raman
  scattering "along with excessive filter bandwidths in irradiance
  measurements accounts for observations of anomalous diffuse attenuation
  coefficients" (p. 71). Of Raman scattering: "deep in the water column
  Raman scattering causes the effective attenuation coefficient to
  decrease significantly below the value expected without Raman
  scattering, while near the surface, Raman scattering has relatively
  little effect on K" (p. 77), and "near surface effects on reflectance
  and attenuation coefficients, at most ~20%" (p. 83). Of filters: their
  Eq. (37) (p. 79), the attenuation a detector sees through a filter of
  transmission h,

      Ks(z) = integral K h exp(-K z) dl / integral h exp(-K z) dl,

  and "finite filter width can contribute a large portion of the decrease
  in attenuation coefficient which is observed at this wavelength"
  (589 nm, p. 79); their own Kd(589) lies below Smith & Baker's "due to
  the 10-nm filters used" (p. 81). They name "attenuation coefficients
  less than those of pure water" among the anomalies (p. 82). They do not
  discuss Jerlov's tables.
- Jerlov (1976), *Marine Optics*, chapter 10 (read for 1.15.8): "Most
  data result from sporadic observations with one to three colour
  filters having a broad band width" (p. 128); the types describe "the
  upper layers, 0-10 m" (p. 133); Table XXVII is Kd (0-10 m). His filters'
  widths are not given.

**What will be done.** An example, `examples/jerlov_kd_below_pure_water.py`,
prints every figure; no package code changes.

1. Where, and by how much: Jerlov's Kd (both editions, types I to II,
   at the 13 printed wavelengths from 400 to 700 nm) over the two pure
   water absorptions the package carries that reach the red, Smith &
   Baker (1981) and Pope & Fry (1997). Seen while planning, for type I:
   against Smith & Baker the 1968 edition's least ratio is 0.666 (600
   nm), the 1976 edition's 0.862 (700 nm); against Pope & Fry, 0.731 and
   0.897.
2. Whether rounding could do it: Kd is -ln of a transmittance per metre
   printed to two or three figures (57 percent at 700 nm for type I);
   the interval half a printed unit gives.
3. How much a broad filter alone can do: Eq. (37) as printed (no source
   spectrum, i.e. a flat one), with K = Smith & Baker's pure water
   absorption (to 800 nm, so a wide filter at 700 nm stays inside its
   table; Pope & Fry stops at 727.5), averaged over 0-10 m (the mean of
   Ks over the layer, which is -ln[E(10)/E(0)]/10), for Gaussian filters
   of 2, 10, 20, 40 and 60 nm full width at half maximum, at 600, 675 and
   700 nm. Seen while planning: at 700 nm 0.974, 0.921, 0.852, 0.798 of
   the absorption for 10, 20, 40, 60 nm; at 600 nm 0.954 to 0.759; 2 nm
   changes nothing.
4. What would follow, written now. If filters of a few tens of nm bring
   the apparent attenuation of pure water down by as much as Jerlov's
   values lie below it, broad filters are enough to account for the size
   of the deficit, which is all that can be said without his filters'
   widths. Where even 60 nm does not reach a deficit (to be computed),
   the filter alone cannot account for it there. Raman scattering is not
   computed: it needs the light field at the exciting wavelengths, which
   is a radiative transfer calculation with an inelastic source; its size
   is quoted from Marshall & Smith only.

**Documents.** OPEN_QUESTIONS.md gains question 7 (question, what was
done, found, not known, where); docs/open_questions.rst its line; the
page "Where the sources disagree" a figure (Jerlov's ratio and the
filter's at each width, for the three wavelengths); DATA.md section 3 a
paragraph pointing there; the example lists (thirty-two scripts).
Every figure recomputed by a test from the example's output. A release
with an example and no code change, 1.31.2.

**Result.** As planned in what was computed. Type I lies below Smith &
Baker's absorption at 7 of the 13 printed wavelengths in both editions,
least 0.666 (600 nm, 1968) and 0.862 (700 nm, 1976); below Pope & Fry's
at 4 and 2, least 0.731 and 0.897. Rounding moves Kd by at most 1.1
percent (1976) and 3.6 percent (1968) from 600 to 700 nm. Through
Gaussian filters, pure water over 0-10 m appears at 0.974, 0.922, 0.853
and 0.799 of its absorption at 700 nm for 10, 20, 40 and 60 nm (Smith &
Baker), and 0.954 to 0.706 at 600 nm. By the criterion written in the
plan: filters of 10 and 40 nm reach the 1976 deficits at 600 and 700 nm;
no filter up to 60 nm reaches either edition's value at 675 nm, nor the
1968 value at 600 nm against Smith & Baker (against Pope & Fry, 60 nm
does). The page "Where the sources disagree" draws it, from the example's
own output.

**Differences from the plan, noted after the code.**

- The plan's figures at 600 nm (0.954 to 0.759) came from a table that
  started at 560 nm, which cut a wide filter's short-wavelength tail. The
  example cuts each Gaussian at three standard deviations, and 60 nm then
  gives 0.706. The light that reaches 10 m through a filter comes mostly
  from that tail, where water absorbs less, so where it is cut moves the
  result; the example says so and quotes Marshall & Smith that real
  filters' tails are longer than a Gaussian's (p. 78).
- With Pope & Fry, whose table ends at 727.5 nm, filters wider than 40 nm
  at 675 nm and 20 nm at 700 nm leave the table and are not computed; the
  example says which widths were tried. At 675 nm their absorption makes
  the narrow filters' apparent attenuation slightly larger than the
  absorption (1.004 to 1.009), not smaller.
- A wide filter at 700 nm reaches Smith & Baker's 710 nm value, which the
  package marks suspect; the example catches that warning by type and
  reports it.
- The first draft of question 7 said the 2 nm filters stay "within 0.6
  percent"; the largest departure is 0.64 percent, and the test found it.
  It says 0.7. It also said that at 675 nm "the absorption of water
  changes little with wavelength", which was not shown (Smith & Baker's
  rises from 0.35 to 0.65 per metre between 650 and 700 nm); that clause
  was taken out before the commit.

## 131. Raman scattering in question 7, by Marshall & Smith's own model (1.31.3): the plan

Section 130 quoted Raman scattering as the second mechanism Marshall &
Smith (1990) name for an anomalously low Kd, and did not compute it. The
user asked (2026-11-27) whether it could be computed; it can, with the
paper's own model, which needs no radiative transfer code.

**The model, read from the page images (pp. 73-77).** A two-stream model
with a Raman source, for a homogeneous water. The total downward
irradiance at the emission wavelength l, Eq. (33) (the same as 21b):

    Ed(z) = Ed_solar(0) exp(-K z)
            + (b_r / 4) E0(l', 0) [ G- exp(-K' z) / (K_r + K')
                                   + G+ (exp(-K' z) - exp(-K_r z)) / (K_r - K') ]

with K and K' the diffuse attenuation at l and at the exciting wavelength
l', E0(l', 0) the scalar irradiance at l' just below the surface, b_r the
Raman scattering coefficient, a_r = 1.5 a (Table II, p. 74),
G+- = 1/2 [(1 + 2 b_b / a_r)^(1/2) +- 1] and K_r / a_r = (1 + 2 b_b /
a_r)^(1/2) (Eq. 17, p. 74). The shift is 3400 per cm (p. 72): 700 nm is
excited from 565.4 nm, 675 from 549.0, 600 from 498.3. b_r = 2.6e-4 per
m, from their cross section measured with excitation at 488 nm (Eq. 7,
p. 73); a second method of theirs gave a cross section about 35 percent
higher (p. 73). Their worked case at 589 nm (Eqs. 31-32 and 36, pp.
76-77) uses B = 4 Ed_solar(l, 0) / (b_r E0(l', 0)) of about 1.3e4.

**What will be computed,** in part 5 of
`examples/jerlov_kd_below_pure_water.py`: the Kd over 0-10 m,
-ln[Ed(10)/Ed(0)]/10, at 600, 675 and 700 nm, for pure water (K = a +
b_b, Eq. 14's K ~ a + b_b, p. 74, the absorption Smith & Baker's or Pope
& Fry's and b_b the package's pure water backscattering at 35), with the
surface light from Gregg & Carder (the site's sky: sun 30 degrees,
visibility 10 km) and E0(l', 0) = Ed(l', 0), as the paper takes the
light as nearly collimated (D ~ 1, p. 74). Pure water at the exciting
wavelength is the clearest case, so the most Raman light; any water
attenuates more there. As a check, B at 589 nm against the paper's 1.3e4.
The figures moved by: b_r 35 percent higher; a flat surface spectrum; the
layer to 20 and 30 m.

**What would follow, written now.** Seen while planning: over 0-10 m the
Raman light lowers Kd by about 0.1 to 0.4 percent at 675 and 700 nm. If
the computed reduction is under 1 percent at 675 and 700 nm with every
variation above, Raman scattering, in this model, cannot account for
deficits of 5 to 14 percent in Jerlov's 0-10 m values there; it would
need a deeper layer than his. If it reaches the deficits, it can. The
model's own assumptions (homogeneous water, isotropic Raman emission,
a_r = 1.5 a, two streams, one exciting wavelength per emitted one, b_r at
488 nm used at 498 to 565 nm) are listed, not tested.

**Documents.** OPEN_QUESTIONS.md question 7's findings and what is not
known; the site's line and the page "Where the sources disagree" (its
prose); CHANGELOG. Every figure recomputed by a test. A patch, 1.31.3.

**Result.** As planned. The paper's B at 589 nm comes out at 1.38e4
(about 1.3e4 in the paper). Over 0-10 m the Raman light lowers the Kd of
pure water by at most 0.59 percent at 675 and 700 nm, with b_r 35
percent higher or a flat sun, against type I's deficits there of 4.5 to
18.8 percent; by the criterion written above, in this model it cannot
account for them. Over 0-20 m it reaches 17.7 percent at 700 nm and over
0-30 m 40.7 percent (Smith & Baker's absorption).

**Differences from the plan, noted after the code.**

- The plan, and the first draft of CHANGELOG 1.31.3, gave the deficits
  as "5 to 14 percent", taken from the figures at hand rather than
  computed over both editions and both pure waters; they are 4.5 to 18.8
  (type I, 675 and 700 nm). Found before the commit; the example now
  prints the range and a test checks it.
- Gregg & Carder's table is given at whole nanometres only, so the
  surface ratio E0(l', 0)/Ed(l, 0) is interpolated from the table's own
  rows, as the package asks.
- Question 7's first update dropped the two quotations on near-surface
  Raman effects; the test of the quotations found it, and they are back,
  now beside the computed result they agree with.

## 132. A Fournier-Forand for a renderer's g and for OSOAA (1.32.0): the plan

Section 127 left four functions taking Petzold's stations only; section
128 opened `forward_scatter` and `attenuation_within` to a
`FournierForand`. This opens the other two, `henyey_greenstein_fit` and
`osoaa_phase_function`, as the user asked (2026-11-27). After it, every
public function that takes a phase function takes either.

**What differs from a station.** A Fournier-Forand is the particles'
phase function alone, has no c, b or wavelength, and is known in closed
form at every angle above 0 (section 127). The two functions handle each
of these as follows.

**`henyey_greenstein_fit(scattering, /, *, method)`.**

- `"backscatter_ratio"`: g whose HG scatters the Fournier-Forand's own
  backscatter ratio (Eq. 3) beyond 90 degrees, by the same bisection.
- `"mean_cosine"`: g = `FournierForand.mean_cosine()`, which rests on no
  extension and does not warn.
- `log_ratio` is ln(p_HG / p_FF) at Petzold's 55 angles, 0.1 to 180
  degrees (all eight stations share them), so that a Fournier-Forand's
  fit reads like a station's.
- The result: `station` names the Fournier-Forand (n and mu), as
  `ForwardScatter` does; `wavelength_nm` is NaN; `measured_backscatter_
  ratio` is the Fournier-Forand's own; a new field `particles_only`
  (default False, added at the end) is True; `as_dict` gives the
  Fournier-Forand's citation as its source and the new field. The g is
  the particles' g: pure water's scattering, which a renderer may add
  as its own medium, is not in it, and the docstring says so.

**`osoaa_phase_function(scattering, /, *, minus_f12_over_f11,
f22_over_f11, f33_over_f11)`.**

- F11 = 4 pi times the Fournier-Forand's phase function at Petzold's 55
  angles, from 180 degrees down, as for a station; the ratios as before
  (a number, or 55 values).
- Below 0.1 degree the spline is OSOAA's, as for a station; the share of
  the Fournier-Forand there is known exactly, `cumulative(0.1)` (6.83
  percent for Mobley et al.'s Petzold fit, seen while planning), and the
  docstring says the file's F11 integrates to 4 pi times one less it.
- OSOAA's hydrosols under `-HYD.Model 3` are the particles, with its own
  pure water added (section 86): a particles-only phase function is what
  that model describes, where a station's includes pure water.
- The two cross-section lines: a Fournier-Forand has no c or b, and
  `-HYD.Model 3` does not read them (section 86: two runs differing only
  in them gave byte-identical results). They are written as 1 and 1, and
  the comment line says they are placeholders, not read under that model.
- No warning: nothing in it is extrapolated from data.

**Checks, set now.**

1. The HG g from `"backscatter_ratio"` returns the Fournier-Forand's B
   within 1e-9; from `"mean_cosine"`, g equals its mean cosine.
2. `log_ratio` equals ln(HG / FF) recomputed at the 55 angles.
3. The OSOAA file has 55 rows from 180 down; F11 / 4 pi equals the
   phase function there; the cross-section lines are 1 and 1 and the
   comment says why.
4. A station gives byte-identical files and identical fits to 1.31.3.
5. OSOAA itself (the build of section 86, by hand, not in CI): a run of
   Jerlov III at 440 nm with the Fournier-Forand of Mobley et al.'s
   Petzold fit runs to the end; its truncation coefficient and Kd are
   recorded beside the same run with NUC 2240's phase function, as a
   record, not judged.

**Documents.** The map, docs/topics/other_software.rst and
seeing_through_water.rst where they name these functions, CHANGELOG, the
Zenodo description. A release with new behaviour of public functions,
1.32.0.

**Result.** As planned. Checks 1 to 4 hold (a station's files and fits
are byte-identical to 1.31.3's, `as_dict` aside, which gains
`particles_only`). For the Fournier-Forand on Mobley et al.'s line at a
backscatter ratio of 0.0183, the HG g is 0.91858; the paper (p. 1038)
says "a value of g = 0.9185 gives Bp = 0.0183", and a test holds both.
Check 5, OSOAA by hand (the build of section 86; one run each, Jerlov III
at 440 nm, the base conditions of tools/osoaa_closure.py): the
Fournier-Forand file was read and the run went to the end. Its
truncation coefficient was 1.40009 against 1.30648 with NUC 2240, and Kd
over 0-10 m 0.15594 against 0.15697 per metre, 0.66 percent lower
(Jerlov's own, 0.145). The share of the Fournier-Forand below 0.1 degree,
left to OSOAA's spline, is 6.83 percent. Recorded, not judged; the runs
are not kept in the repository, so CHANGELOG does not quote their
figures.

## 133. A Fournier-Forand in the example on choosing a phase function, and the record of question 7 in DATA.md (1.32.1): the plan

Two pieces, one release, as the user asked on 2026-11-27.

### A. `phase_function_choice.py` gains part 4: a Fournier-Forand

The example shows what Henyey-Greenstein does against Petzold's eight
stations. Since 1.30.0 the package has a second analytic choice, the
Fournier-Forand, and since 1.32.0 every function that takes a phase
function takes it. Part 4 sets it beside the stations.

**Against what.** A Fournier-Forand is the particles' phase function
alone (sections 127 and 128); a station is water and particles. So part
4 compares it with each station's particles: Petzold's vsf less pure
water's (`pure_water_vsf`), over b less pure water's
(`pure_water_scattering`), as `painted_sphere.py` already does. The
particles' backscatter ratio is

    Bp = (B/S b - bw / 2) / (b - bw),

B/S and b as printed (the extension below 0.1 degree counted, as in
parts 1 and 2), bw at 530 nm. Pure water's salinity is the example's
choice, 35, stated at the top; part 4 also prints how much Bp moves
between 0 and 37 (at the two clear Bahamas stations it is large: seen
while planning, Bp is 0.0152 at 35 and 0.0219 fresh at AUTEC 8).

**What is compared.** For each station, the Fournier-Forand on Mobley et
al.'s line at that Bp (`mobley2002_fournier_forand`, the HydroLight
choice), and, for the same Bp, the HG of `henyey_greenstein_fit(...,
method="backscatter_ratio")` on that Fournier-Forand:

1. the ratio to the particles' phase function at the angles of part 1;
2. the share within 1, 10 and 90 degrees of forward (the particles'
   share is the station's less pure water's, by the closed form section
   128 uses).

Seen while planning: within 1 degree the Fournier-Forand gives 0.95 to
1.13 of the particles' phase function and HG 0.27 to 1.10; within 1
degree of forward the particles scatter 0.21 to 0.38 of their light, the
Fournier-Forand 0.25 to 0.40 and HG 0.02 to 0.09; straight back the
Fournier-Forand gives 0.31 to 1.02 of it, least at the clear stations.
Every figure the documents quote is the example's own result, recomputed
by the tests.

**Not done.** No new public name; the example's own helpers. No fit of n
and mu to each station (one Bp does not fix them; the line is one choice,
as the docstring of `mobley2002_fournier_forand` says).

### B. DATA.md section 3 records the whole of question 7

NEXT_STEPS listed "why Jerlov's Kd lies below pure water's absorption" as
open in DATA.md's list. Question 7 (1.31.2, 1.31.3) is the record of it,
but DATA.md section 3's paragraph "Why, as far as it can be said" still
reads as of 1.31.2: broad filters only. It gains Raman scattering (1.31.3)
and what remains unexplained (675 nm in both editions, and 600 nm in 1968
against Smith & Baker), each figure the example's, checked by
tests/test_kd_below_pure_water.py as the others are.

**Documents.** examples/README.md and the site's list of examples where
they describe the example; CHANGELOG; the Zenodo description. An example
and a record, no change to the package's behaviour: 1.32.1.

## 134. The black-bottom miss with Fournier-Forand phase functions: the shape apart from bb/b (1.32.2): the plan

Section 115 found that over a black bottom the shallow model's miss is
not ordered by the particles' bb/b (OPEN_QUESTIONS.md question 5): with
a, bb and pure water's part held, Petzold's three stations (NUC 2240,
AUTEC 8, HAOCE 11) gave ratios that rise with bb/b in 5 of the 24 cells
and fall in none. But the stations differ in bb/b and in shape at once,
so the two could not be told apart. A Fournier-Forand can: at a given
bb/b it is one smooth shape, and on Mobley et al.'s line it changes
smoothly with bb/b. The user asked on 2026-11-27 for this to go on.

**The runs.** `tools/shallow_rrs_mc.py --fournier-forand OUT.csv`: the
same 24 black-bottom cells (a 0.05 and 0.2 1/m, bp/a 3 and 30 at NUC
2240, depth 1 and 4 m, the sun at 0, 30 and 60 degrees), and for each of
the three stations the Fournier-Forand on Mobley et al.'s line
(`mobley2002_fournier_forand`) whose backscatter share equals the
station's sampler's, with the same bp, so a, b, bb and pure water's part
are the station's run's and only the shape beyond bb/b differs. 72 runs,
the same photons, batches and seed, and the same cut at 1 degree, taken
from the Fournier-Forand's own closed-form cumulative share. The stations'
runs are the ones kept (monte_carlo.csv, black_bottom.csv). The sampler
is rebuilt from `FournierForand.cumulative` and `phase_function`; a
check: its backscatter share equals the station's within 1e-6, and a
station's run is reproduced bit for bit by the tool (it is not changed).

**Questions, with the measures set now.**

1. Does bb/b fix the rrs? For each of the 72 pairs, the Fournier-Forand's
   rrs over the station's. bb/b is said to fix it if at least 54 of the
   72 (three quarters) are within 5 percent or within three combined
   standard errors.
2. Within one smooth family, does bb/b order the miss? Model over Monte
   Carlo for the three Fournier-Forands, in order of bb/b: monotonic in
   at least 20 of the 24 cells.
3. What does order it? Seen while planning, in the cell a 0.05, bp/a 3,
   1 m, sun overhead: the Fournier-Forand's rrs is 0.96, 0.69 and 0.51
   of NUC 2240's, AUTEC 8's and HAOCE 11's, and its phase function at
   180 degrees is 0.97, 0.50 and 0.41 of theirs. So the measure: for
   each cell, the six phase functions (three stations, three
   Fournier-Forands) are ranked by the phase function per steradian at
   the angle of single scattering from the refracted sun to straight up
   (180 degrees less the sun's refracted angle), and by the Monte
   Carlo's rrs; the backward phase function is said to order the
   black-bottom rrs if Spearman's rank correlation is at least 0.9 in at
   least 20 of the 24 cells.

Every answer is recorded as found, whichever way.

**Documents.** OPEN_QUESTIONS.md question 5 (what was done, found, not
known); DATA.md section 50; a fifth part of
`examples/shallow_water_closure.py`, reading the runs from
`examples/data/shallow_rrs_mc/fournier_forand.csv`; tests that recompute
every quoted figure and reproduce a stored run. No value or code of the
package changes: 1.32.2.

**Result.** The 72 runs took about a minute. The check holds: each
Fournier-Forand's backscatter share is the station's to the digits
stored, and the station's run is the stored one. None of the three
measures is met.

1. 43 of the 72 pairs are within 5 percent or 3 standard errors (54
   needed): bb/b does not fix the rrs over a black bottom. The
   Fournier-Forand's rrs is 0.49 to 1.09 of the station's.
2. Within the Fournier-Forands, model over Monte Carlo rises with bb/b in
   8 cells and falls in 4 (20 needed).
3. A rank correlation of at least 0.9 in 1 of the 24 cells (20 needed).

Seen after the runs, recorded as such and not as measures: the three
Fournier-Forands in a cell differ by a factor of 1.11 in the median cell
(1.20 at most), about the size of their standard errors (up to 10
percent), so measure 2 cannot be read either way; the stations differ by
1.21. In the 12 cells with bp/a 3, the station's rrs over the
Fournier-Forand's follows the ratio of their phase functions at the angle
of single scattering, in logarithms, with a correlation of 0.96 with the
sun overhead, 0.91 at 30 degrees and 0.44 at 60. That fits the cell seen
while planning, and is a lead for the second group, not a finding: the
measure set for it (3) was not met over all 24 cells.

## 135. The black-bottom miss: the backward and forward halves of the phase function apart (1.32.3): the plan

Section 134 found, after its runs and not as a measure, a lead: in the
cells with less scattering the station's rrs over the Fournier-Forand's
followed the ratio of their phase functions at the angle of single
scattering. NEXT_STEPS proposed testing it with Fournier-Forands off
Mobley et al.'s line, the same bb/b with another backward shape. The
user asked on 2026-11-27 for this to go on.

**Why not that.** Seen while planning: at a fixed backscatter ratio a
Fournier-Forand's backward shape hardly moves with n and mu. For the
three stations' ratios, over every mu from 3.05 to 4.6 that has an n
(1 < n < 2.155), the phase function at 180 degrees spans a factor of
1.25 at most (0.0021 to 0.0026 per sr at 0.0136), where the stations'
own are 2.0 and 2.4 times the Fournier-Forand's at AUTEC 8 and HAOCE 11.
Another Fournier-Forand cannot make the stations' backward peak, so it
cannot test the lead.

**What instead: the halves exchanged.** For each station and its
Fournier-Forand of section 134 (the same backscatter share B), two
hybrids, each a proper phase function with the same B:

- H1: the station's phase function below 90 degrees, the
  Fournier-Forand's above. Its cumulative share is the station's up to
  90 degrees and the Fournier-Forand's beyond; both are 1 - B there.
- H2: the Fournier-Forand's below 90 degrees, the station's above.

The Monte Carlo's cut at 1 degree is taken from the forward half's
owner. With the station (S) and the Fournier-Forand (F) already run,
the four make a two-by-two design: the forward half from S or F, the
backward half from S or F. In each of the 72 (cell, station) pairs:

    backward effect = [ln(S / H1) + ln(H2 / F)] / 2
    forward effect  = [ln(S / H2) + ln(H1 / F)] / 2

144 new runs (`tools/shallow_rrs_mc.py --halves OUT.csv`), the same
cells, photons, batches and seed; a, b, bb and pure water's part as in
section 134.

**Measures, set now.**

1. The backward half is said to carry the difference if |backward
   effect| exceeds |forward effect| in at least 54 of the 72 pairs.
2. The lead itself, on these new runs: in the cells with bp/a 3 and the
   sun at 0 or 30 degrees (8 cells, 24 pairs), the backward effect
   against ln(p_S / p_F) at the angle of single scattering (above 90
   degrees, so in the backward half) has a correlation of at least 0.9.

Recorded, not judged: the interaction, ln S - ln H1 - ln H2 + ln F, which
is 0 where the two halves act separately; the effects by sun and bp/a.

**Checks.** Each hybrid's sampled share beyond 90 degrees is B within
0.002 (400 000 draws); its tabulated phase function integrates to 1
within 1e-3; the tool's station and Fournier-Forand runs still reproduce
their stored values bit for bit (the station's table is built by a
function shared with `petzold_phase`, which must not change it).

**Documents.** OPEN_QUESTIONS.md question 5; DATA.md section 50; part 5
of `examples/shallow_water_closure.py` extended; the runs in
`examples/data/shallow_rrs_mc/halves.csv`; tests that recompute every
quoted figure and reproduce a stored run. No value or code of the
package changes: 1.32.3.

**Result.** The 144 runs took about two minutes. The checks hold: each
hybrid integrates to 1 within 1e-5 and its share beyond 90 degrees is
B; the stored station and Fournier-Forand runs are reproduced bit for
bit with `petzold_phase` built on the shared table. One difference from
the plan's wording: the sampler draws only beyond the 1 degree cut, so
the sampled share beyond 90 degrees is B / (1 - f), f the share below
the cut, and the check is made against that.

1. The backward half's effect is the larger in 49 of the 72 pairs (54
   needed): not met.
2. In the 8 cells with bp/a 3 and the sun at 0 or 30 degrees, the
   backward half's effect against ln(p_S / p_F) at the angle of single
   scattering has a correlation of 0.977 (0.9 needed): met. The lead of
   section 134 holds on new runs, made to test it.

Seen after the runs, recorded as such: the 23 pairs that miss measure 1
are mostly NUC 2240's, whose backward half is close to its
Fournier-Forand's (their ratio at the angle of single scattering is 0.89
to 1.03), so neither half moves its rrs beyond the noise. Without it the
backward half's effect is the larger in 41 of 48 pairs. For AUTEC 8 and
HAOCE 11 the backward half raises the rrs by a median factor of 1.53
with the sun overhead, 1.21 at 30 degrees and 1.06 at 60; the forward
half moves ln rrs by a median of 0.043, 0.033 and 0.054. The interaction
is 0.035 in the median pair (0.171 at most).

## 136. Petzold's average-particle phase function, built from the three San Diego Harbor stations, in the shallow-water closure (1.32.4): the plan

Question 5 is left at this: which backward shape HydroLight's runs had is
not known, since the "average particle" phase function HydroLight uses
was not in hand (sections 27, 113). The user obtained the Ocean Optics
Web Book's page on Petzold's measurements, its data file
`Petzold_data.txt` (CC BY, "Data taken from Petzold (1972) and Light and
Water, Table 3.10"), and Mobley et al. (2002), and asked on 2026-11-27 to
go on as follows.

**What the sources say.** Mobley et al. (2002, p. 1037): the average
particle phase function "is derived from three measurements of the VSF
in San Diego Harbor; tabulated values are given in Mobley et al. [1993]
and Mobley [1994]", and "When numerically integrated over 90 <= psi <=
180 deg, this phase function gives a particle backscatter fraction of Bp
= 0.0183". The Web Book: subtract the pure sea water VSF at 514 nm from
each of the three, divide by each one's particle b, and average at each
angle; it is normalised with psi^-m below 0.1 degree, m = 1.346 "from the
two smallest measured scattering angles".

**Seen while planning (the file read whole, 55 rows).** The three NUC
stations shipped here (NUC 2040, 2200, 2240), each less `pure_water_vsf`
at 514 nm with salinity 35 and divided by b less `pure_water_scattering`,
averaged, give the file's `avg-part PF` within 0.43 percent at all 55
angles (median 0.34 percent; fresh water 1.1 percent at most). The
file's other columns are AUTEC 8, HAOCE 11 and NUC 2040 within 0.5
percent. Integrated with log-log interpolation and the power law below
0.1 degree, the file's function gives 0.9937 over the sphere and 0.01818
beyond 90 degrees.

**What is done.** Section 27 stands: nothing is shipped under Petzold's
name, and the package does not change. The tool builds the function from
the package's own stations, as the sources describe, so no table is
copied: `tools/shallow_rrs_mc.py`, `average_particle_table()` (the
salinity 35 a stated choice; the Web Book does not give one), and an
`average_particle_phase()` sampler on the same grid as `petzold_phase`,
normalised by its own integral, scattering below 1 degree counted as
none as for the stations. The Web Book's file is not added to the
repository; a test holds the reconstruction against twelve of its
values, transcribed with the citation (CC BY 2.0 asks for attribution).

**The runs.** `--average-particle OUT.csv`: the 24 black-bottom cells of
section 114, a, bb and pure water's part held, bp = (bb - bw/2) / B with
B the sampler's backscatter share. 24 runs, the same photons, batches
and seed; `examples/data/shallow_rrs_mc/average_particle.csv`.

**Measure, set now.** Section 114's: the model within 10 percent of the
Monte Carlo in at least 10 of the 13 runs of the black-bottom group. If
met, the second group is recorded as accounted for by HydroLight's own
phase function; if not, as not. Recorded beside it, not judged: the
average particle's rrs over NUC 2240's in each cell, and its phase
function at the angle of single scattering over NUC 2240's.

**Checks.** The reconstruction against the transcribed values within 0.5
percent; the sampler's backscatter share against 0.0183 (reported, with
the 0.6 percent the log-log integral of the file leaves); a stored run
reproduced bit for bit.

**Documents.** OPEN_QUESTIONS.md question 5; DATA.md sections 21 and 50
(what the average particle is, and where it was checked); a part 6 of
`examples/shallow_water_closure.py`; CHANGELOG. No value or code of the
package changes: 1.32.4.

**Result.** The 24 runs took about 20 seconds. The checks hold: the
reconstruction is the Web Book's table within 0.42 percent at the twelve
angles transcribed in the example; the sampler's backscatter share is
0.01825, the paper's 0.0183 to three figures (the function is
normalised by its own integral, which takes out the 0.9937 the file's
values gave over the sphere). The measure is not met: the
model is within 10 percent of the Monte Carlo in 1 of the group's 13
runs (0 with NUC 2240), and in 11 of the 24 cells; model over Monte
Carlo 0.895 to 1.593. The average particle's phase function at the angle
of single scattering is 0.96 to 1.06 times NUC 2240's, and its rrs 0.94
to 1.24 times. So NUC 2240 was a close stand-in for HydroLight's phase
function in the black-bottom cells, and the second group is not the
Monte Carlo's choice of phase function. No HydroLight output is in hand:
the comparison is between the model, fitted to HydroLight runs that
were not published, and this Monte Carlo. What remains cannot be told
apart here: either the model misses HydroLight in these cells (its fit
was judged on all runs together, and the 1998 paper wrote that fixing
A0 = 1 and A1 = 1/pi would need a negative D1 or a more complicated
form, pp. 6334-6335), or the Monte Carlo differs from those runs in what
it leaves out (waves at 5 m/s; a sky, which section 114 added at 30
percent without closing the group; scattering below 1 degree).

## 137. HydroLight's angular quads in the Monte Carlo: the nadir cap and the sun's quad (1.32.4): the plan

Section 136 left two candidates for the black-bottom group that cannot
be told apart here: the model missing HydroLight in those cells, or the
Monte Carlo leaving out something HydroLight's runs had. The user
obtained two documents on HydroLight, the Ocean Optics Web Book's page
and J. Hedley's IOCCG summer class lecture (2022), and asked on
2026-11-27 for one such difference to be tried in the same release.

**What the lecture says.** "HydroLight standard discretisation:
Resolution is 10 x 15 [degrees]. Full sphere of directions 18 x 24 quads
plus end-caps = 434 entries. Work with quad averaged radiances"; one band
is centred at 87.5 degrees; "The solar disc is smaller than one quad. So
one consequence is that the direct solar radiance is spread over the
quad." Eighteen bands of polar angle with an end-cap at each pole and a
band centred at 87.5 degrees fit polar caps of half-angle 5 degrees,
bands 10 degrees wide from 5 to 85, and 85 to 90 (inferred, not printed
in these documents). So HydroLight's radiance "straight up" is the mean
over the polar cap within 5 degrees of the nadir, and its sun is spread
over the quad that holds it. The Monte Carlo scores one direction and
starts every photon along one.

Section 135 found the black-bottom rrs with a high sun follows the phase
function near the angle of single scattering; averaging over a cap and a
quad smooths exactly that.

**What changes.** `rrs()` in `tools/shallow_rrs_mc.py` gains two options,
off by default, and off it draws exactly the same random numbers (stored
runs reproduced bit for bit):

- `cap_deg`: each score is for one direction drawn uniformly in solid
  angle within `cap_deg` of straight up (an unbiased estimate of the
  cap's mean radiance): the scattering angle to it, and the path to the
  surface z / mu along it; the bottom's term likewise exp(-c H / mu).
- `sun_quad`: each photon's direction in air is drawn uniformly in solid
  angle over HydroLight's quad holding the sun (the cap within 5 degrees
  for a sun at 0; 10 degrees of polar angle and 15 of azimuth centred on
  it for 30 and 60), then refracted.

**The runs.** `--quads OUT.csv`: the 24 black-bottom cells with the
average particle of section 136, both options on (cap 5 degrees), else
as in `average_particle.csv`. 24 runs.

**Measure, set now.** Section 114's: the model within 10 percent in at
least 10 of the group's 13 runs. Recorded beside it: the quad runs' rrs
over the point runs' in each cell.

**Checks.** With the options on and no scattering, the bottom term
against its closed form averaged over the cap and the sun's quad
(computed by quadrature) within three standard errors; with them off, a
stored run reproduced bit for bit.

**Documents.** As section 136's, in the same release (part 6 of the
example, question 5, DATA.md section 50, CHANGELOG).

**Result.** The 24 runs took about half a minute. The check holds: with
no scattering, the bottom term over the cap and the sun's quad is the
quadrature's within 0.9 standard errors in each of three cases; with the
options off the stored runs are reproduced bit for bit. The measure is
not met: the model is within 10 percent in 4 of the group's 13 runs (1
with a single direction), and in 14 of the 24 cells; model over Monte
Carlo 0.981 to 1.680. The quads move the rrs by 0.91 to 1.11 times, with
standard errors up to 9.2 percent. So the way HydroLight averages over
directions is not what sets the group apart either. Of the differences
named in section 136, waves remain untried; the model's own fit to
HydroLight in these cells cannot be tried without HydroLight's output.

## 138. A Monte Carlo light field in the package: the scope amended, and the plan (1.33.0)

Section 12 put solving the radiative transfer equation out of scope, and
section 38 rejected moving the example's Monte Carlo into the package:
"It would make every figure it returns rest on choices the Jerlov type
does not fix, the phase function above all, and would answer them with a
default." Since then the inputs such a solver needs have all become
public objects (Petzold's stations, a `FournierForand`, pure water's
scattering), and `examples/radiance_distribution.py`'s Monte Carlo has
been checked against the exact isotropic solution (section 40), Gershun's
law, Jerlov's Kd and Tyler's lake. The user asked on 2026-11-27 to make
it a public function, before an adjoint solver (planned after this), and
settled the name, the cut and the example.

### The scope, amended

Section 12 is amended, not dropped: the package may compute a light field
by this one method, where **every choice that sets the result is a
required argument**: the phase function, the scattering below which a
particle is taken to go straight on, the pure water inside b and its
salinity, the refractive index, the sun or an overcast sky, the depth and
the bottom, where and how finely the field is reported, the photons, the
batches and the seed. Nothing is defaulted; `MissingQuantityError` for a
choice left out. That meets section 38's objection rather than overruling
it. Out still: an atmosphere, waves, polarisation, inelastic scattering,
water that varies with depth; the result lists them.

### The function

    jerlov.monte_carlo_light_field(
        a, b, /, *, wavelength_nm, pure_water_b, salinity_psu,
        phase_function, cut_deg, refractive_index, sun_zenith_deg,
        depth_m, bottom_albedo, depths_m, slab_m,
        zenith_step_deg, azimuth_step_deg, photons, batches, seed)

- `a`, `b`: 1/m at `wavelength_nm`, b including `pure_water_b`.
- `phase_function`: a Petzold `ScatteringFunction` (water and particles:
  its vsf less `pure_water_vsf` at its own wavelength and `salinity_psu`
  is the particles', as the example does) or a `FournierForand` (the
  particles' alone). Pure water turns light by the shape of
  `pure_water_vsf`.
- `cut_deg`: the particles' scattering below it goes straight on. For a
  station it may not be below its first measured angle (below lies the
  report's extension, DATA.md section 21).
- `sun_zenith_deg`: in air, or None for an overcast sky of uniform
  radiance.
- `depth_m`: `math.inf` for no bottom, with `bottom_albedo` None; or a
  Lambertian bottom of `bottom_albedo` at that depth.
- `depths_m`, `slab_m`: where Ed, Eu, Eo and the radiance are reported,
  each over a slab of that thickness; `zenith_step_deg`,
  `azimuth_step_deg`: the radiance's cells.
- `photons` per batch, `batches`, `seed` (batch i uses seed + i).

It returns a `MonteCarloLightField` (frozen, compared by value): per
batch, Ed, Eu, Eo and the radiance at `depths_m`, and rrs straight up just
below the surface (a collision estimator, as tools/shallow_rrs_mc.py);
their means and standard errors, Kd between consecutive depths, the mean
cosine, Eu / Ed and Eo / Ed; every input; and what the method leaves out.
Everything is per unit planar irradiance just above the surface.

### What it is built from

`examples/radiance_distribution.py`'s `simulate` (sections 38 to 40),
moved, with two additions that draw no random number unless used: a
Lambertian bottom (reflection drawn only when the depth is finite) and
the rrs collision estimator (no draws). So with no bottom the package
gives the example's numbers bit for bit, and the example is rewritten to
call the package (the user's choice), keeping every figure it prints and
the tests hold. `painted_sphere.py` keeps its own copy, so that it stands
alone; the test that held the copies' sources equal now holds the copy's
results equal to the package's.

### Checks, set before writing it

1. The example's figures, unchanged: its tests pass as they are.
2. The exact isotropic solution (section 40's test), now on the package.
3. No scattering: Ed by Beer's law within three standard errors; with a
   bottom, rrs against the bottom term's closed form (section 113's
   check) within three standard errors.
4. With a bottom, rrs against `tools/shallow_rrs_mc.py`'s stored runs with
   the same water, phase function and sun, within the two standard
   errors combined (the transports differ in Fresnel thinning at entry
   and in the cut, said where they differ).
5. Every refusal: a required argument missing, NaN, a bool, text, out of
   range; a phase function of the wrong kind; a cut below a station's
   first measured angle; `bottom_albedo` with no bottom or without one.
6. CI time: the docstring's example runs in seconds.

### Documents

API reference; a section in the topic page on seeing through water (what
it computes, what it leaves out, and that OSOAA or HydroLight are the
codes for more); the map; `examples/radiance_distribution.py` rewritten;
CHANGELOG; the Zenodo description. A new public function and an amended
scope: 1.33.0.

### Result

**Differences from the plan.** The example's lake runs take pure sea
water out of Petzold's station at salinity 37 and give the lake's own
water salinity 0, so one salinity could not serve both: the function
gained `station_salinity_psu`, required with a Petzold station and
refused with a Fournier-Forand. The wavelength is the third positional
argument, `monte_carlo_light_field(a, b, wavelength_nm, /, ...)`, as the
package's other functions take wavelengths, not a keyword (a test keeps
`wavelength_nm=` out of the topic pages, where it was once an old way of
calling another function). The topic page that gained the section
is the one on depth and light, where Tyler's tables are, not the one on
seeing through water.

**The rrs estimator, corrected before release.** Written first with
exp(-c z) along the line of sight, it gave rrs up to 21 percent below the
shallow-water tool's. Scattering below the cut goes straight on, so it
does not turn light out of the line of sight; along it the attenuation
is c less that share, as the tool has it. Corrected; the module's
docstring says so.

**Checks.**

1. The example's figures are unchanged, and its tests pass as they were:
   with no bottom the package gives the example's former engine's Ed,
   Eu, Eo and radiance bit for bit, for the sun and for the overcast
   (checked while moving it, and held for painted_sphere.py's copy by a
   test).
2. The exact isotropic solution: met, as before (tests/test_monte_carlo.py).
3. Closed forms: met. Without scattering Ed follows Beer's law, and with
   a bottom rrs is the bottom's geometric series between bottom and
   surface, within three standard errors.
4. Against the tool's 243 runs with a bottom (tools/monte_carlo_check.py,
   examples/data/monte_carlo/against_shallow_tool.csv): **not met as set**.
   The package's rrs is 0.836 to 1.021 of the tool's, median 0.977;
   42.4 percent within 1 combined standard error, 71.2 percent within 2
   and 88.1 percent within 3. The cause is not the transport but an input
   the plan did not name: the tool turns particles by NUC 2240's whole
   vsf, which holds pure water's scattering as well, and adds pure water
   on its own, so it counts pure water twice; the package takes pure
   water out first. Its particles' backscatter ratio is then 0.0171
   against the whole station's 0.0180. With the tool's convention in the
   package's engine (`--same-phase`), the rrs is 0.887 to 1.131 of the
   tool's, median 0.999; 56.0 percent within 1 combined standard error,
   89.7 percent within 2 and 98.4 percent within 3, somewhat wider than
   two independent normal estimates would be (68, 95, 99.7), which ten
   batches' standard errors and the samplers' differing tables below 1
   degree may account for. The package's convention is kept: it is the
   one the example used, and the one the particles are.
5. Refusals: met (tests/test_monte_carlo.py).
6. CI time: the topic page's call takes under two seconds.

## 139. Waves in the Monte Carlo light field: Cox and Munk's isotropic slopes (1.34.0): the plan

1.33.0's `monte_carlo_light_field` has a flat surface. Waves are the one
condition of Lee et al.'s HydroLight runs (wind 5 m/s) that question 5
has not tried for the black-bottom group (sections 114 to 137), and a
wind-blown surface is what OSOAA (Chami et al. 2015, Opt. Express 23,
27829, the user's copy, not shipped) and HydroLight both model. The user
asked on 2026-11-27 for this next.

### The surface

Cox and Munk (1954), the isotropic, clean-surface form, as OSOAA uses it
(Chami et al. 2015, section 2.2.1) and as `examples/wave_focusing.py`
already cites: the facets' slopes are Gaussian in each direction with a
mean square slope (both directions together)

    sigma^2 = 0.003 + 5.12e-3 W,   W in m/s at 12.5 m (41 ft),

Cox & Munk's equation (42), p. 221, as transcribed in wave_focusing.py.

At each crossing of the surface (the sun's or sky's light entering, and
light from below reaching it), a facet is drawn from the slope
distribution and weighted by the share of the beam it intercepts,
|d . n| / (n_z |d_z|), facets facing away rejected and redrawn; Fresnel's
reflectance at the local angle decides the weight reflected and
transmitted, and the direction is reflected or refracted about the
facet's normal. Light reflected at the surface that still travels the
wrong way (from below: upward after reflection) is taken as having left;
a second interaction with another facet is not followed, as in OSOAA
(Chami et al. 2015, section 3.2, which puts the loss below 1 percent).
Light reflected away from the sea is lost, as now.

### The argument, and what it does to existing calls

`wind`: `"flat"`, or the wind speed in m/s at 12.5 m. It will have no
default, as every other choice; but 1.33.0 was released without it, so,
as section 33 did for the face irradiance ratio, leaving it out takes the
surface as flat, as 1.33.0 did, with a `FutureWarning` naming the
argument, and a later release makes it required (section 34). With
`"flat"` the transport is 1.33.0's, the same random numbers, bit for bit.
The result's `inputs` gain `wind`, and `left_out` says which wave effects
are not modelled (wind direction, whitecaps and foam, multiple facet
interactions).

### Checks, set now

1. `wind="flat"` and an omitted `wind` (with its warning) give 1.33.0's
   numbers bit for bit (the example's figures and the stored check runs).
2. The slopes: the sampled facets' mean square slope, over a million
   draws without the projection weight, within 1 percent of sigma^2.
3. Energy at the surface, Chami et al.'s check (section 3.2, Eq. 31):
   transparent water (b and a tiny), no bottom, the sun at 30 degrees,
   wind 7 m/s: Ed(0-) + Eu(0+) = Ed(0+) within 0.5 percent (OSOAA: 0.01
   percent); at 60 degrees within 1 percent (OSOAA: "less than 1%"). The
   result gains Eu(0+), the light reflected at the surface, to make it.
4. The surface's reflectance of the sun's beam, Eu(0+) / Ed(0+), against
   the same integral over the slope distribution by quadrature, within
   three standard errors, at 30 and 60 degrees and winds 2, 7 and 14 m/s.
5. Against OSOAA with wind, if a build of OSOAA (section 86) is at hand
   in the session; if not, recorded as not done.

### Question 5

The 13 runs of the black-bottom group (section 114) with the package's
function, NUC 2240 (the stand-in that section 136 found close to
HydroLight's average particle), flat and with wind 5 m/s, a, bb and pure
water's part as in section 114. Measure, as before: the model within 10
percent in at least 10 of the 13 with wind. Recorded beside it: the
count with the flat surface in the same function (its convention, water
taken out, differs from the tool's, section 138), and the ratio wind over
flat in each run.

### Documents

API reference (the new argument); the topic page; CHANGELOG; the Zenodo
description; question 5 and DATA.md section 50; an example part or a
tool for the question 5 runs, kept in examples/data/. A new argument and
a new field: 1.34.0.

### Result

Differences from the plan: the result gained four fields, not one,
`reflected_at_surface` and `transmitted_at_surface` with their standard
errors, so that check 3 is Eq. (31) term by term and check 4 has a
standard error; light that a facet refracts into the water upwards (a
second facet would be needed) is dropped, as light reflected the wrong
way is. Every call in the repository now passes `wind`.

1. Met: `wind="flat"` and an omitted `wind` give the same field, and the
   example's figures and the stored check runs are unchanged.
2. Met: the mean square slope of a million facets drawn for light
   straight down is sigma^2 within 1 percent, and their mean weight 1
   within 0.1 percent.
3. Met: transparent water, wind 7 m/s: transmitted plus reflected
   exceeds 1 by 0.008 percent at a sun of 30 degrees and 0.025 percent
   at 60 (200 000 photons in each of four batches, the test's runs). It
   rises to 0.186 percent at 60 degrees and 14 m/s, where facets turned
   away from the sun, which are drawn again, are no longer rare.
4. Met: the sun's reflectance against the quadrature over the slopes, at
   30 and 60 degrees and 2, 7 and 14 m/s, within three standard errors;
   0.0224 to 0.0238 at 30 degrees, 0.0633 to 0.0707 at 60, where a flat
   surface gives 0.0222 and 0.0610.
5. Not done: no build of OSOAA is in this session.

Question 5 (`tools/monte_carlo_check.py --waves`,
`examples/data/monte_carlo/waves_black_bottom.csv`): the model is within
10 percent of the Monte Carlo in 1 of the group's 13 runs with waves at
5 m/s, 0 with the same function's flat surface; the measure is not met.
Waves move the rrs by 0.900 to 1.029 times. Every difference between
this Monte Carlo and Lee et al.'s runs that sections 114 to 137 named has
now been tried; what is left is the model's own fit to HydroLight in
those cells, which needs HydroLight's output.

## 140. The Monte Carlo against Mobley et al.'s (1993) canonical problems (1.34.1): the plan

The user obtained Mobley, Gentili, Gordon, Jin, Kattawar, Morel,
Reinersman, Stamnes and Stavn (1993), "Comparison of numerical models for
computing underwater light fields", Appl. Opt. 32, 7484-7504,
doi:10.1364/AO.32.007484 (not shipped), in which seven codes, HydroLight
("II", invariant imbedding) among them, solved the same canonical
problems; and Tynes et al. (2001), Appl. Opt. 40, 400-412, the same
comparison with polarisation, kept for later. Section 139's notes asked
for a comparison with published HydroLight results whose inputs are
complete; these are, and Table 5 gives each quantity's mean over the
models and their spread. The user asked on 2026-11-27 for this.

### What is compared

Table 5 (p. 7496, read from the page image): the mean over the models
(N = 3 to 7) of Ed, Eou and Lu (the radiance seen looking straight
down) at optical depths 1, 5 and 10, and s/x, the models' sample standard
deviation over their mean, for problems 1 to 6. Problems this engine can
pose exactly:

- 1: a Rayleigh phase function, 3 (1 + cos^2 psi) / (16 pi), Eq. (3);
  omega0 = 0.9 and 0.2.
- 2: Table 2's particle phase function; omega0 = 0.9 and 0.2.
- 5: problem 2 with omega0 = 0.9 under a wind-blown surface of slope
  standard deviation 0.2 (sigma^2 = 0.04), the sun at 80 degrees.
- 6: problem 2 with omega0 = 0.2 over a Lambertian bottom of irradiance
  reflectance 0.5 at optical depth 5 (Ed, Eou, Lu at 1 and 5).

Common to all: flat surface (except 5), n = 1.340, no sky, the sun at 60
degrees (except 5), E = 1 W m-2 nm-1 on a plane normal to the sun, so
Ed(0+) = cos(sun). With c = 1 per metre, optical depth is metres.

Not posed: problem 3 (stratified water; the engine has one layer),
problem 4 (an atmosphere, "a more detailed specification ... is not
made"), problem 7 (Raman scattering).

### The phase function of problem 2, and a misprint

Table 2 (p. 7491, read from the page image) gives the particle phase
function at 55 angles. Against the Ocean Optics Web Book's table of the
same function (section 136), 54 of the 55 stand in one ratio, 0.9969 to
0.9972; at 0.50119 degree Table 2 prints 2.18839+2, 1.084 times the Web
Book's 2.018+2 and above the line through its neighbours, so it is taken
as a misprint, and the value used is the log-log interpolation between
its neighbours (recorded in DATA.md as a new entry, with the evidence).
Between the angles the paper prescribes linear interpolation, and below
0.12589 degree beta ~ psi^-1.346; the table is so used here, normalised
by its own integral.

### How

`tools/mobley1993_benchmark.py`, on the package's engine
(`jerlov.monte_carlo._simulate`, which takes a tabulated phase function;
the public function takes only Petzold's stations and Fournier-Forands),
writing `examples/data/mobley1993/runs.csv` with each quantity, its
standard error and Table 5's mean and s/x. Eou is the engine's scalar
irradiance of upward-travelling light, which `_simulate` gains (no new
random number, so every stored run repeats); Lu the mean radiance within
5 degrees of straight up (HydroLight's polar cap, section 137). The
values are scaled by cos(sun) for E on a plane normal to the beam.

### The measure, set now

An entry agrees if |x - mean| <= 2 s + 3 SE + 0.005 mean, s from Table
5's s/x, SE the engine's standard error, 0.005 for Table 5's three
figures. The engine is said to reproduce the published solutions if at
least 90 percent of the entries posed agree. Every entry is recorded,
agreeing or not.

### Documents

DATA.md (the misprint, and the result); OPEN_QUESTIONS.md is not
involved; a test that every quoted figure is the run's; the topic page
and `monte_carlo_light_field`'s docstring may say what it was checked
against; CHANGELOG. No public behaviour changes: 1.34.1.

### Result

**The measure is met: 46 of the 51 entries posed agree** (90.2 percent,
46 needed). Problems 1 and 2 with omega0 = 0.9 and problem 6 agree in
every entry. The five that do not:

- Lu at optical depth 10 in problems 1 and 2 with omega0 = 0.2: 0.044 and
  0.126 of the mean, with standard errors above 90 percent. Too few
  photons come back from there, even with 10 million per problem for
  the absorbing cases (`PHOTONS_ABSORBING`, a choice made after the first
  run gave none); three of the 1993 Monte Carlo codes had none either
  (p. 7495). The engine has no variance reduction for depth.
- Ed in problem 5 at optical depths 1, 5 and 10: 0.962, 0.970 and 0.976
  of the mean (Eou and Lu agree). The engine meets one facet per
  crossing, and light that a facet reflects the wrong way is dropped;
  the 1993 Monte Carlo codes followed repeated interactions with the
  surface (p. 7490). With the sun 80 degrees from the zenith that is the
  likely cause; it is not tested here.

**A fault in 1.34.0, found by problem 5 and corrected.** The first run
put problem 5's Ed 13 to 14 percent above the mean. 1.34.0 drew facets
from the slope distribution, redrew those facing away from the light,
and weighted each by the share of the beam it intercepts; the mean of
that weight over the facets facing the light exceeds 1 when the light
is low (1.164 at 80 degrees and sigma^2 = 0.04, by quadrature), so light
was created at the surface. Facets turned away are in shadow, and the
light that reaches the surface must equal what crosses a horizontal
plane; the weight is now divided by that mean, tabulated against the
cosine of the light's direction for each slope variance
(`_front_share_table`). Below 60 degrees the mean is within 0.002 of 1,
so section 139's checks at 30 and 60 degrees hardly move: transmitted
plus reflected now exceeds 1 by 0.008 percent at 30 degrees, 0.023 at 60
and 0.028 at 60 degrees and 14 m/s, and falls short of it by 0.345
percent at 80 degrees and 7 m/s; the sun's reflectance is 0.0224 to
0.0238 at 30 degrees and 0.0633 to 0.0706 at 60 against the slopes'
integral with each facet weighted by the share it intercepts, within
three standard errors. Question 5's runs with waves were made again:
still 1 of the 13 within 10 percent, the waves moving the rrs by 0.893
to 1.028 times.

Table 2's misprint at 0.50119 degree is DATA.md section 53.

## 141. Light that meets the wavy surface more than once (1.35.0): the plan

Section 140 left problem 5 of Mobley et al. (1993), the sun at 80
degrees over a surface of slope variance 0.04, with Ed 0.962, 0.970 and
0.976 of the models' mean at optical depths 1, 5 and 10, and named the
likely cause without testing it: the engine meets one facet per crossing
of the surface, and light that a facet sends the wrong way is dropped
(section 139 chose this, as OSOAA does, Chami et al. 2015, section 3.2).
The 1993 Monte Carlo codes followed repeated interactions (p. 7490). The
user chose on 2026-11-28 to test it next and, asked, to make it a choice
the caller states rather than a change of behaviour.

### Seen before the plan

A probe of the surface alone (`_facets` and `_fresnel_cos`, 400 000
beams, not kept): of the sun's beam at 80 degrees and slope variance
0.04, facets reflect 0.253, of which 0.031 travels downwards after the
reflection, towards the sea, and is now counted as reflected to the sky;
at 60 degrees 0.0039, at 30 degrees none. Light that a facet refracts
into the water upwards was none in the probe. If most of the 0.031
enters the water at a second facet, Ed below the surface rises by about
0.031 / 0.746, 4 percent, the size of problem 5's shortfall. That is
why this is expected to work; it is not yet a result.

### The surface, followed

At a crossing, a facet is drawn as now (section 139, with section 140's
shadowing). Each branch, reflected and refracted, either leaves the
surface (into the water travelling down, or into the air travelling up)
or meets the surface again (reflected light from the air still
travelling down; refracted light from the air travelling up; reflected
light from below still travelling up; refracted light from below
travelling down). When one branch leaves to the air and the other stays,
the weight is multiplied by the staying branch's share, as now; when
both stay (or both enter the water), one is chosen with its Fresnel
share as the probability and the weight is kept. A branch that meets the
surface again draws a new facet, independently of the last, for its own
direction. This repeats until the light leaves; after 50 interactions
what is left is dropped (it is not expected to happen).

What is still left out: the surface's shape between one facet and the
next (the facets are independent), so a ray's path along a real wave is
not traced.

### The argument

`surface_facets`: `"one"` (section 139's surface, as OSOAA: light that
would meet a second facet is dropped) or `"all"` (followed as above).
With `wind="flat"` it must be None (a flat surface sends nothing the
wrong way). With a wind, it will be required; as section 139 did for
`wind`, leaving it out with a wind takes `"one"`, as 1.34 did, with a
`FutureWarning` naming the argument, and a later release requires it.
`inputs` gain `surface_facets`; `left_out` says, for `"one"`, that light
meeting a second facet is dropped, and for `"all"`, that the facets are
independent. A new argument: 1.35.0.

### Checks, set now

1. `"one"` gives 1.34.1's numbers bit for bit: the stored waves runs and
   problem 5 in `examples/data/mobley1993/runs.csv` are reproduced, and
   an omitted `surface_facets` with a wind gives the same as `"one"`,
   with the warning. Flat is untouched.
2. Energy, transparent water: with `"all"`, transmitted plus reflected
   within 0.5 percent of 1 at the sun at 30, 60 and 80 degrees and winds
   7 and 14 m/s.
3. Problem 5 with `"all"`: the measure of section 140 met in all nine of
   its entries (Ed, Eou, Lu at optical depths 1, 5 and 10). Recorded with
   it: each ratio to the mean, beside `"one"`'s, and the count over the
   51 entries.
4. Recorded, not a measure: the share of the weight that met a second
   facet, entering and from below, at 30, 60 and 80 degrees; and question
   5's waves runs (section 139, wind 5 m/s, sun 0 to 60 degrees) again
   with `"all"`, the count within 10 percent and the ratio to `"one"`.

### Documents

API reference; the topic page; CHANGELOG; the Zenodo description; DATA.md
section 53 (problem 5's result); NEXT_STEPS. `tools/mobley1993_benchmark.py`
gains the choice, and its `"all"` run is kept beside the 1.34.1 run.

### Result

Differences from the plan: the share of the light that met a second
facet (check 4) is weighted by the light, not counted by photons; the
first version of the code counted photons, which at 80 degrees gives
0.139 (many facets that send the sun's light back down intercept little
of it), and was changed before any figure was recorded.

1. Met: with `"one"` problem 5's nine entries are those of 1.34.1's
   `runs.csv` digit for digit, the stored waves runs of question 5 are
   unchanged in every column they had, and an omitted `surface_facets`
   with a wind gives `"one"`'s field, with the warning (a test). A flat
   surface does not reach the new code.
2. Not met at one of the six points. Transmitted plus reflected, less 1,
   with `"all"` (with `"one"` beside it): at 7 m/s +0.008 percent at 30
   degrees (+0.008), +0.028 at 60 (+0.023), -0.086 at 80 (-0.345); at
   14 m/s +0.011 (+0.011), +0.043 (+0.028), and +0.689 at 80 (+0.469),
   above the 0.5 set. The light that enters with `"all"` is 1.0293 and
   1.0261 times `"one"`'s at 80 degrees and 7 and 14 m/s, 1.0027 and
   1.0093 at 60, and the same at 30.

   **Found: the cause is 1.34.1's shadowing table, not the following of
   the facets.** `"one"` misses by as much at 80 degrees, and facets
   alone show it: the mean weight of the facets drawn for the sun at 80
   degrees is 1 - 0.356 percent at 7 m/s and 1 + 0.475 percent at 14
   m/s (eight batches of 500 000, standard errors 0.04 percent), where
   section 140 meant it to be 1. `_front_share_table` gives 1.1620 and
   1.3454 at cos(80 degrees); the same quadrature at that cosine itself
   gives 1.1591 and 1.3574, and on a grid four times finer 1.1579 and
   1.3508. Both the interpolation between the table's cosines and the
   grid of slopes, which the edge between facets in light and in shadow
   crosses, are too coarse when the light is low. Up to 60 degrees the
   table is within 0.01 percent of the finer grid (winds 2 to 14 m/s,
   every 2.5 degrees). It is not corrected here: that changes
   every run with waves, and this release keeps `"one"` as 1.34.1 had
   it. It is the next item in NEXT_STEPS.
3. **Met: with `"all"` all nine of problem 5's entries agree.** Ed is
   0.992, 0.998 and 1.003 of the models' mean at optical depths 1, 5 and
   10 (with `"one"` 0.962, 0.970 and 0.976), Eou 0.985, 0.991 and 0.989
   (0.943, 0.963, 0.958), Lu 0.964, 0.896 and 0.941 (0.863, 0.955,
   0.970). With problem 5 so posed, 49 of the 51 entries agree; the two
   left are the radiance at optical depth 10 in absorbing water.
   (`examples/data/mobley1993/runs_all_facets.csv`; the other problems
   have a flat surface and their rows are 1.34.1's.) Section 140's
   likely cause is so confirmed as the cause of Ed's shortfall, within
   the models' spread.
4. Recorded. The share of the light that met a second facet, in problem
   5's water (omega0 = 0.9, Table 2, slope variance 0.04; four batches
   of 100 000): entering, none at 30 degrees, 0.0039 at 60 and 0.0310 at
   80; of the light reaching the surface from below, 0.0163, 0.0175 and
   0.0191. Question 5's waves runs with `"all"`
   (`examples/data/monte_carlo/waves_black_bottom.csv`, columns
   `all_facets`): the model is within 10 percent in 1 of the 13, as with
   `"one"`; `"all"` over `"one"` is 0.957 to 1.165, each within 2.7
   combined standard errors of 1. The waves still do not close question
   5.

Also fixed, found while writing the new warning: 1.34.0's
`FutureWarning` for a left-out `wind` was raised with `stacklevel=2`,
which through `_data.checked` pointed into `_data.py`; both warnings now
use `_data.caller_stacklevel()`, and a test checks that they name the
caller's file.

## 142. Publishing by itself after a merge (1.35.1): the plan

Until now a person started `publish.yml` from the Actions tab after each
merge (section 51). The user asked on 2026-11-28 that merges be done by
Claude once CI is green, and that publishing follow by itself, by a
change to the workflow rather than by a tag pushed from a session. Nothing
in the package changes.

### The trigger

`publish.yml` gains `workflow_run` on the `tests` workflow, `completed`,
on `main`. A first job, `decide`, runs only when that run's conclusion is
`success` and its event `push` (a merge; not the weekly schedule, not a
failure). It checks out the commit the tests passed on
(`workflow_run.head_sha`, not main's head when the workflow starts) and
reads the version from pyproject.toml; if that version is already tagged
it says so and publishes nothing, so a merge that does not raise the
version is harmless and a run by hand cannot be repeated by the merge.
Otherwise `build`, `publish` and `release` follow as before, on that
commit, and the Release's tag targets it. A run by hand and a pushed tag
work as before. `concurrency` keeps one publication at a time.

Trusted Publishing names the workflow file and the `pypi` environment,
both unchanged; `workflow_run` runs the workflow file on the default
branch, so the claims are main's.

### Checks, set now

1. Tests in `test_packaging.py`: the trigger names the `tests` workflow
   as `test.yml` names itself, on `main`; `decide` requires success and a
   push; an existing tag means no publication after a merge and an error
   by hand; `build` checks out `decide`'s commit; the Release targets it.
2. `decide`'s script, run here with each event's variables against this
   repository's tags: after a merge at 1.35.0 (tagged) it publishes
   nothing; at an untagged version it goes on; by hand on main at a
   tagged version it fails, on another branch it fails; a tag that does
   not match the version fails.
3. The first real test is this release: after its merge the workflow must
   publish 1.35.1 by itself (PyPI, Release, Zenodo). Recorded in the next
   section that touches this, with the run's number. If it fails, 1.35.1
   is published by hand and the cause recorded.

### Result

1. Met: `test_publishing_follows_a_merge_by_itself` checks each point by
   the workflow's text (PyYAML is not a dependency); breaking any of five
   of them by hand (the push condition, `go=false`, the Release's target,
   the branch, `build`'s checkout) makes it fail. The test that the
   Release needs PyPI first now names `decide` too.
2. Met: `decide`'s script, taken from the workflow and run with each
   event's variables against this repository's tags: after a merge at
   1.35.0 (tagged) `go=false` and exit 0; at 1.35.1 (untagged) `go=true`;
   by hand on main at 1.35.0 and on dev, and a tag v9.9.9, each fail;
   the tag v1.35.0 at 1.35.0 goes on.
3. Not yet: after this release's merge.

## 143. The facets' shadowing by its closed form (1.35.2): the plan

Section 141 found that `_front_share_table` (section 140) is too coarse
for a low sun: the mean weight of the facets drawn for the sun at 80
degrees is 1 - 0.356 percent at 7 m/s and 1 + 0.475 percent at 14 m/s,
where it should be 1, from the interpolation between its cosines and its
grid of slopes, which the edge between light and shadow crosses. The user
asked on 2026-11-28 for it to be corrected.

### Seen before the plan

The quantity has a closed form. With x along the light's horizontal
direction, light at zenith angle theta meets a facet of slopes (z_x, z_y)
with weight (-d . n) / (-n_z cos theta) = 1 - tan(theta) z_x, and the
facet faces the light when z_x < cot(theta), whatever z_y. With z_x
Gaussian of standard deviation s (s^2 = sigma^2 / 2), the mean over the
facets in light is the mean of a truncated Gaussian:

    share = 1 + tan(theta) s phi(a) / Phi(a),   a = cot(theta) / s,

phi and Phi the standard normal density and distribution. A probe (not
kept): the table's quadrature converges on it as its grid is refined; at
80 degrees and 14 m/s 1.35738 on 401 points (the table's), 1.35084 on
1601 and 1.35193 on 3201, the closed form 1.35193; at 85 degrees and 7
m/s 1.71596, 1.71212, 1.71022 against 1.70998. Tabulated on 2201 cosines
(geometric from 1e-4 to 0.3, linear to 1), interpolation is within 1e-5
of it up to 89.9 degrees, for slope variances 0.003 to 0.2.

### The change

`_front_share_table` tabulates the closed form on that grid (computed
with `math.erfc`; NumPy has no error function). The drawing of facets is
unchanged and draws the same random numbers, so every run with waves
changes only through the weights: a value change, a correction of a
fault (section 61), 1.35.2. `"one"` no longer gives 1.34.1's or 1.35.0's
numbers bit for bit; flat surfaces are untouched.

### Checks, set now

1. The table against the closed form within 1e-5 from 0 to 89.9 degrees
   and slope variances 0.003 to 0.2; the closed form against a quadrature
   on 3201 points within 0.05 percent at 30, 60, 80 and 85 degrees and 7
   and 14 m/s.
2. The mean weight of the facets drawn for the sun at 80 and 85 degrees,
   7 and 14 m/s (eight batches of 500 000), within three standard errors
   of 1.
3. Energy, transparent water: transmitted plus reflected within 0.1
   percent of 1 at 30, 60 and 80 degrees and 7 and 14 m/s, with `"one"`
   and with `"all"` (section 141's check 2, which `"all"` missed at 80
   degrees and 14 m/s by +0.689 percent, tightened from 0.5).
4. Problem 5 of Mobley et al. (1993) again, with `"one"` and `"all"`;
   recorded beside section 141's. Measure: with `"all"` all nine entries
   still agree.
5. Question 5's waves runs again (sun 0 to 60 degrees, where the table
   was within 0.01 percent): recorded, with the largest change in rrs.

### Documents

The stored runs (`examples/data/mobley1993/runs.csv` and
`runs_all_facets.csv`, `examples/data/monte_carlo/waves_black_bottom.csv`)
are made again with the corrected engine, and the tests that recomputed
sections 140's and 141's figures from the engine check this section's
instead; those sections stay as the record of what the code gave then.
CHANGELOG; DATA.md section 53 if problem 5's figures move; NEXT_STEPS.

### Result

1. Met. The table is within 7e-6 of the closed form from 0 to 89.9
   degrees for slope variances 0.003 to 0.2, and the closed form within
   0.044 percent of a quadrature on 3201 points at 30, 60, 80 and 85
   degrees and 7 and 14 m/s (the quadrature's own error: it moves by as
   much between 1601 and 3201 points).
2. Met. The mean weight of the facets drawn, less 1, at 80 and 85
   degrees and 7 and 14 m/s: -0.023 to -0.003 percent, each within three
   standard errors (0.04 percent) of 0; section 141 had -0.356 and +0.475
   at 80 degrees.
3. Met. Transmitted plus reflected less 1, transparent water, at 30, 60
   and 80 degrees and 7 and 14 m/s: `"one"` -0.018 to +0.032 percent,
   `"all"` -0.000 to +0.030 percent.
4. **Met: with `"all"` all nine of problem 5's entries agree**, Ed 0.990,
   0.996 and 1.001 of the models' mean at optical depths 1, 5 and 10,
   Eou 0.981, 0.982 and 0.983, Lu 0.919, 0.954 and 0.916 (section 141:
   Ed 0.992, 0.998, 1.003). With `"one"`, Ed is 0.962, 0.970 and 0.975,
   and the last now agrees: 47 of the 51 entries agree with `"one"`, 49
   with `"all"`, the two left the radiance at optical depth 10 in
   absorbing water. Only problem 5's rows changed. The radiances move by
   more than the table did (Lu with `"all"` at optical depth 5 from 0.896
   to 0.954): a weight changed by the correction changes which photons
   the roulette keeps, and the random numbers drawn after it, so the
   runs are new samples with the same spread.
5. Recorded. Question 5's waves runs again: with `"one"` the rrs moves by
   0.999893 to 1.000038 times, with `"all"` by 0.999925 to 1.003953; the
   flat runs are unchanged. The model is within 10 percent in 1 of the 13
   with either; waves over flat 0.893 to 1.028, `"all"` over `"one"` is
   0.958 to 1.165,
   each within 2.7 combined standard errors of 1. The share of the light
   that met a second facet in problem 5's water (section 141's check 4):
   entering, none at 30 degrees, 0.0039 at 60 and 0.0310 at 80; from
   below, 0.0162, 0.0175 and 0.0197.

## 144. The radiance looking straight down at depth by a collision estimator (1.36.0): the plan

Two of Mobley et al.'s (1993) values still do not agree (sections 140,
141 and 143): Lu at optical depth 10 in problems 1 and 2 with omega0 =
0.2, where the engine's estimate, the path length photons spend in the
cell within 5 degrees of straight up, has standard errors above 90
percent because almost no photon comes back up from there. The user
asked on 2026-11-28 for this next.

### The estimator

The engine already estimates the radiance travelling straight up just
below the surface without waiting for photons to arrive there (section
138): each scattering adds its weight times the phase function towards
straight up times exp(-c' z), and each arrival at the bottom its weight
times albedo / pi times exp(-c' H), c' being c less the particles'
scattering that goes straight on. The same sum, started at a depth z_k
instead of the surface (each scattering deeper than z_k adding its
weight times the phase function towards straight up times
exp(-c' (z - z_k)), and the bottom exp(-c' (H - z_k))), is the radiance
travelling straight up at z_k, per unit planar irradiance just above the
surface. Every scattering below z_k contributes to it, not only the rare
photon that climbs back, so the error falls where the cell's estimate
fails. It draws no random number.

`monte_carlo_light_field`'s result gains `lu` and `lu_se` at `depths_m`,
and `batch_lu`, the radiance travelling straight up (seen looking straight
down) by this estimator. Nothing else in the result changes, bit for bit.
A new field: 1.36.0. The cells' radiance stays as it is.

### Checks, set now

1. Every existing field of every stored run and example is unchanged
   bit for bit (no random number is drawn).
2. Against the exact solution the engine is already checked with
   (isotropic scattering, `test_the_engine_against_isotropic_scattering`):
   where that test checks the radiance, the new estimate agrees within the
   same tolerance.
3. Against the cells: where many photons come back (problems 1 and 2
   with omega0 = 0.9 at optical depth 1), the new estimate and the mean
   over the cap within 5 degrees agree within three combined standard
   errors plus 1 percent (the cap's mean is not the value at its centre).
4. Mobley et al. (1993) Table 5, all problems posed, Lu now by the new
   estimator (Ed and Eou as before): the measure of section 140 met in
   every one of the 51 entries with `surface_facets="all"` for problem
   5. Recorded: each Lu's ratio to the mean and its standard error,
   beside the cap's; and the count with `"one"`.

### Documents

API reference (the new fields), the topic page, CHANGELOG, the Zenodo
description, DATA.md section 53, NEXT_STEPS. `tools/mobley1993_benchmark.py`
takes Lu from the new estimator; its stored runs are made again (Ed and
Eou unchanged digit for digit).

### Result

Differences from the plan: check 2 named a radiance check that the
isotropic test did not make (it checks K, the mean cosine and the
ratios); the exact asymptotic radiance, L ~ 1 / (1 - k mu) with mu the
cosine to straight down, so L straight up over E0 = 1 / ((1 + k) 2 pi
integral of 1 / (1 - k mu) over mu from -1 to 1), was added to that test
in its place, at its tolerances.

1. Met. The estimator draws no random number: every stored check run is
   reproduced, and in the canonical problems' runs made again every Ed
   and Eou is the previous one digit for digit and the cap's Lu, kept as
   `lu_cap`, is the previous Lu digit for digit.
2. Met. The new estimate over the exact value, at the isotropic test's
   depths: 0.970 to 0.979 at omega0 = 0.5 (tolerance 6 percent), 0.989
   to 0.992 at 0.72 and 0.990 to 0.997 at 0.9 (3 percent); the cells of
   10 degrees there give 0.969 to 1.340.
3. Met. Problems 1 and 2, omega0 = 0.9, optical depth 1: the new estimate
   over the cap's mean is 0.959 and 0.957, the difference 0.84 and 0.32
   of three combined standard errors plus 1 percent.
4. **Met: with `surface_facets="all"` all 51 entries agree.** The two
   that did not, Lu at optical depth 10 in problems 1 and 2 with omega0 =
   0.2, are 1.183 and 1.034 of the mean with standard errors of 10.6 and
   3.0 percent, where the cap gave 0.044 and 0.126 with 92 percent. With
   `"one"`, 49 agree; the two left are problem 5's Ed at optical depths 1
   and 5. Every Lu, as a ratio to the mean with its standard error (the
   cap's in brackets): problem 1, omega0 0.9, 1.006 (0.1 percent), 1.033
   (0.2), 0.964 (0.6) at optical depths 1, 5, 10 [cap 1.049, 0.999,
   1.074]; omega0 0.2, 0.991 (0.1), 0.946 (0.6), 1.183 (10.6) [0.968,
   0.711, 0.044]; problem 2, omega0 0.9, 0.924 (1.9), 0.907 (2.4), 0.957
   (5.7) [0.966, 1.018, 0.961]; omega0 0.2, 1.000 (1.5), 1.235 (2.8),
   1.034 (3.0) [0.949, 1.214, 0.126]; problem 5 with `"all"`, 0.907
   (3.5), 0.913 (3.5), 0.920 (2.8) [0.919, 0.954, 0.916]; problem 6 at
   optical depth 1, 1.014 (1.4) [0.930]. The new estimate is not always
   nearer the mean than the cap was (problem 2 with omega0 = 0.9 is
   lower), but it is everywhere within the models' spread, and its
   errors are smaller in 15 of the 16 Lu set against the cap.

## 145. Polarisation, first step: a vector Monte Carlo in tools, against Natraj et al.'s (2009) Rayleigh tables (1.36.1): the plan

Section 2 of NEXT_STEPS and earlier choices left polarisation out, since
nothing in the package could carry it without solving the radiative
transfer equation; the package now has a Monte Carlo engine (sections
138 to 144). The user asked on 2026-11-28 to go on to polarisation. It
is done in steps, each checked before the next: (1) a vector Monte Carlo
in `tools/`, checked against published tables of the Stokes parameters;
(2) the air-water interface's Fresnel matrices, pure water's
depolarisation and the particles' scattering matrix as stated inputs; (3)
whether and how it enters the package, which revisits the scope (section
12) and is planned separately, with the user. This section is step 1;
the package does not change.

### The reference

Natraj, Li and Yung (2009), "Rayleigh scattering in planetary atmospheres:
corrected tables through accurate computation of X and Y functions",
Astrophys. J. 691, 1909-1920, doi:10.1088/0004-637X/691/2/1909, read from
the author's copy in the Caltech repository (not shipped). Tables 1 to 6
(pp. 1912-1913) give I, Q and U, eight decimals, of the diffuse light
leaving the top (upwelling) and the bottom (downwelling) of a
homogeneous Rayleigh layer of optical thickness 0.5 over a black surface
(A = 0), the sun at mu0 = 0.2, for 16 values of mu and 7 relative
azimuths: 672 values. Depolarisation is zero (p. 1910). Their
conventions (p. 1909): Q = Ir - Il (Coulson et al. 1960; Hansen and
Travis use the opposite sign), the incident flux pi F0 across a plane
normal to the beam, the azimuth counterclockwise looking down from the
sun's. The tables' normalisation (F0 = 1) and the sign of U in this
engine's frame are to be fixed by single scattering before the
comparison, and said.

This problem the engine can pose exactly: refractive index 1 (no
interface), a = 0, b = 1, the depth 0.5, a bottom of albedo 0.

### The method

`tools/polarised_mc.py`. Each photon carries a Stokes vector (I, Q, U, V)
and a reference direction in the plane normal to its travel. It is
scattered by Rayleigh's matrix: the angle drawn from the phase function
for unpolarised light, the azimuth uniformly, and the Stokes vector
rotated into the scattering plane and multiplied by the reduced matrix
(the (1,1) element 1), so that its I carries the weight (Tynes et al.
2001, Appl. Opt. 40, 400, section 2, the user's copy). The light leaving
the layer is estimated at each scattering for every tabulated direction
(a next-event estimate: the phase matrix towards that direction, the
attenuation to the boundary, over the cosine), rotated into the
direction's meridian plane; the engine's free paths and its scalar
parts are those of `jerlov.monte_carlo`.

### Checks, set now

1. Single scattering: in an optically thin layer (0.001) the estimate
   equals the analytic singly scattered Stokes vector within three
   standard errors in every tabulated direction (this is where the
   normalisation and the sign of U are fixed).
2. The tables: 672 values; a value agrees if |x - t| <= 3 SE + 2e-4
   (the tables' values run from about 0.03 to 0.44 for I). The engine is
   said to reproduce them if at least 95 percent agree; every value is
   recorded, agreeing or not.
3. Recorded: the scalar estimate of I (the matrix replaced by its (1,1)
   element) beside the vector one, the error of neglecting polarisation
   in this problem.

### Documents

DECISIONS only, a test that the quoted figures are the stored run's
(`examples/data/polarisation/natraj2009.csv`), and the tables
transcribed into the tool (from the text layer, each checked against the
page image). CHANGELOG. No package change: 1.36.1.

### Result

Differences from the plan: check 1 compares only the first order of
scattering (the tool gained `orders`), since even at optical thickness
0.001 the second order moved Q by 2e-6 to 7e-6, 0.1 to 0.3 percent of I,
which near the neutral points was several standard errors; and straight
up and down (mu = 1) the tables refer Q and U to the plane of the
azimuth phi, the limit of the meridian plane, which the tool takes there
(its first version took +x and missed those 18 values).

1. Met. Light scattered once, against the exact singly scattered Stokes
   vector in every tabulated direction (twenty batches of 100 000): at
   most 1.51 standard errors from it at optical thickness 0.001 and 1.11
   at 0.5, in I, Q and U; V is zero throughout.
2. **Met: all 672 values agree** (ten batches of 400 000 photons,
   `examples/data/polarisation/natraj2009.csv`), with the tables'
   normalisation (F0 = 1, an incident flux of pi across the beam, so the
   engine's I times pi mu0), Q = Ir - Il, which is the engine's Q
   (I1 - I2, e1 in the meridian plane) with the opposite sign as the
   definitions say, and U with the opposite sign, a convention of the
   azimuth's handedness that the tables fix: with the same signs for U,
   33 of the 112 at each boundary agree. The largest difference is
   0.00105 in I at the top for mu = 0.02, where the standard error is
   0.00046.
3. Recorded. I computed with the scalar equation (the matrix replaced by
   its (1,1) element, other random numbers) over the vector I: 0.927 to
   1.113 at the top and 0.868 to 1.120 at the bottom, more than 5
   percent off in 52 and 66 of the 112 directions, with standard errors
   below 0.5 percent. Neglecting polarisation in this problem moves the
   radiance by up to 13 percent.

## 146. Polarisation, a second reference: Kokhanovsky et al.'s (2010) Rayleigh benchmark (1.36.2): the plan

The user obtained Kokhanovsky et al. (2010), "Benchmark results in vector
atmospheric radiative transfer", J. Quant. Spectrosc. Radiat. Transfer
111, 1931-1946, doi:10.1016/j.jqsrt.2010.03.005 (the open copy in DLR's
elib, not shipped), which this session could not download, and asked on
2026-11-28 for it to be used as section 145 proposed: a second,
independent check of `tools/polarised_mc.py` before step 2.

### The reference

Seven vector codes compared on a homogeneous non-absorbing layer over a
black surface, the sun at 60 degrees, relative azimuths 0, 90 and 180
degrees (180 the backscattering direction at the sun's zenith angle),
viewing zenith angles 0, 20, 40, 60, 80 and 89 degrees from the outer
normal of either boundary. The benchmark is SCIATRAN's, correct to at
least six digits (Table A1's caption). For Rayleigh scattering without
depolarisation, optical thickness 0.3262: Table A1 gives I and Q of the
reflected and the transmitted light (72 values), Tables A4 and A5 U at
90 degrees (12 values, two of them 0 straight up and down): 84 values.
Their conventions: Eq. (6), the Stokes vector times pi over mu0 F0, F0
the irradiance across the beam, so pi times this engine's values per
unit planar irradiance; Eq. (2), Q from the components parallel and
perpendicular to the meridional plane, this engine's Q. U's sign is a
matter of the azimuth's handedness and is fixed by the table, as in
section 145, and must be the same at both boundaries.

The aerosol and cloud cases need the particles' scattering matrices,
which the paper gives only in a figure and on a web page
(www.iup.physik.uni-bremen.de/~alexk) that neither the user nor this
session could reach on 2026-11-28; they are not posed.

The tables' text layer drops the minus signs of values and exponents;
every value is transcribed from the page images (pp. 1943-1945).

### Checks, set now

1. The tool's geometry becomes arguments (the sun, the optical
   thickness, the directions); with Natraj et al.'s, it gives section
   145's stored run bit for bit.
2. The 84 values: a value agrees if |x - t| <= 3 SE + 2e-4; the engine is
   said to reproduce them if at least 95 percent agree. Every value is
   recorded.
3. Recorded: the scalar I beside the vector one, as in section 145.

### Documents

DECISIONS; the stored run (`examples/data/polarisation/kokhanovsky2010.csv`)
and a test that every quoted figure is its; CHANGELOG; NEXT_STEPS. No
package change: 1.36.2.

### Result

Differences from the plan, and a finding. **The tables' Q has the
opposite sign of the paper's Eq. (2).** Eq. (2) (p. 1932, read from the
page image) defines Q = <E_par E_par* - E_perp E_perp*>, parallel to the
meridional plane; with that, this tool's Q would be the tables' as it is.
A first run (ten batches of 30 000, made to fix the signs) agreed in 35
of the 84 so, and in 80 with Q reversed. Single scattering decides it
without this tool: light from the sun at 60 degrees scattered straight up
by Rayleigh scattering is polarised across the plane of the sun, so in
the reference plane of azimuth 0, the plane of the sun, I_perp > I_par
and Eq. (2) gives Q < 0, where Table A1 gives +0.07253129 at a viewing
zenith angle of 0. The tables' Q is I_perp - I_par, Coulson's and Natraj
et al.'s sign. U, as in section 145, has the sign opposite to this
tool's. The four values that first run missed were I and Q at the top at
89 degrees, about 2 percent low with 30 000 photons a batch; with the
planned 400 000 they agree.

1. Met. With the geometry as arguments, Natraj et al.'s problem gives
   section 145's stored run bit for bit (made again in full; a batch of
   20 000 and the single scattering were compared first).
2. **Met: all 84 values agree** (ten batches of 400 000 photons,
   `examples/data/polarisation/kokhanovsky2010.csv`). The largest
   difference is 0.00275 in I at the top at 89 degrees and azimuth 180,
   where the standard error is 0.00129.
3. Recorded. The scalar I over the vector I: 0.936 to 1.083 at the top
   and 0.933 to 1.085 at the bottom.

## 147. Polarisation, second step: the wavy surface's Fresnel matrices and a body of pure water, against Chowdhary et al.'s (2020) testbed (1.36.3): the plan

Section 145's step 2 is the air-water interface's Fresnel matrices, pure
water's depolarisation and the particles' scattering matrix as stated
inputs. The user asked on 2026-11-28 for references to be found (the
user has no copies at hand). This section is the interface and a body of
pure water; the particles' matrix and depolarisation other than zero
are a later section. The package does not change.

### The reference

Chowdhary, Zhai, Xu, Frouin and Ramon (2020), "Testbed results
for scalar and vector radiative transfer computations of light in
atmosphere-ocean systems", J. Quant. Spectrosc. Radiat. Transfer 242,
106717, doi:10.1016/j.jqsrt.2019.106717. The accepted manuscript is open
on NASA's NTRS (20190034124); the tables are in the supplementary
material (Elsevier's mmc2.docx, the text of the tables, not images),
from which they are read by script. Deterministic and Monte Carlo
codes agree to 1e-6 (2e-6 marked in bold) on:

- AOS-I: a molecular atmosphere (Rayleigh, depolarisation zero, single
  scattering albedo 1, optical thickness 0.63031, 0.22111, 0.097069 and
  0.049188 at 350, 450, 550 and 650 nm) over a wavy surface, the ocean
  black (Tables S2a, S2b: just above the surface);
- AOS-II: no atmosphere; a wavy surface over 100 m of pure seawater,
  Rayleigh with depolarisation zero, single scattering albedos
  0.39644970, 0.32846715, 0.03253425 and 0.002932551 and optical
  thicknesses 3.38, 1.37, 5.84 and 34.1 (Table 2), over a black bottom
  (Tables S3a, S3b: just above the surface).

The surface for both (Table 4, section 3.2): Cox and Munk's isotropic
Gaussian slopes, mean square slope 0.03884 (about 7 m/s), refractive
index 1.34; no shadowing, no second facet, no foam, and no
renormalisation of the reflection and transmission. The sun at 30 and
60 degrees; viewing zenith angles 0 to 60 degrees in steps of 5; relative
azimuths 0 (towards the glint), 180, 60 and 240. Each table gives
R = pi L / (mu0 S0) for I computed without polarisation and for I, Q and
U with it: 4 wavelengths x 2 suns x 50 directions (straight up once for
each pair of azimuths, Q and U in the plane of 0 or 60) x 3 = 1200
vector values for each model, and 400 scalar ones.

### The method

`tools/polarised_ocean.py`, on `tools/polarised_mc.py`'s photons
(Stokes vectors carried with a reference axis, Rayleigh's matrix). The
surface: a facet drawn for each photon as `jerlov.monte_carlo._facets`
does, the slopes Gaussian and the facet facing the light, with its weight
the share of the beam it intercepts (cos i / (mu_n mu)), not divided by
the mean share (no renormalisation, as the testbed). On the facet the
Stokes vector is turned into the plane of incidence (e1 = s x d, e2 = s,
s normal to that plane) and multiplied by Fresnel's reflection or
transmission matrix (the transmission's in power, so that I is the flux),
and the weight takes the branch's share; light the testbed has no
kernel for (reflected or refracted the wrong way for one facet) is
dropped.

The light just above the surface in each tabulated direction v is
estimated at every scattering, by reciprocity: a facet is drawn for the
light travelling against v, and the light the scattering sends along
the reversed path (reflected for AOS-I, refracted, with 1 / m^2 on the
radiance, for AOS-II) is estimated as in section 145 and carried
through that facet's matrix into v's meridian plane. The direct glint,
the sun reflected once, is added from its closed form,
pi p(n) R(n) / (4 mu mu0 mu_n^4) with the Fresnel matrix R and the
sun's attenuation through the atmosphere. The conventions (the
normalisation, the signs of Q and U) are fixed by that glint and by the
tables, and said.

### Checks, set now

1. Fresnel's matrices: reflection plus transmission conserve the flux
   of any polarised beam (the transmission in power), on 10 000 random
   facets and Stokes vectors, to 1e-12, from either side.
2. The glint by itself: at 650 nm in AOS-II (single scattering albedo
   0.003) the closed form alone is within 2 percent of the tables where
   it is more than 90 percent of them.
3. The tables, 2400 vector values (AOS-I and AOS-II): a value agrees if
   |x - t| <= 3 SE + 1e-5. The tool is said to reproduce them if at
   least 95 percent agree, for each model. Every value is recorded.
4. The 800 scalar values of I the same way, against the tool run with
   every matrix replaced by its (1,1) element.
5. Recorded: the scalar over the vector I, as in sections 145 and 146.

### Documents

DECISIONS; the tables read from the supplement
(`examples/data/polarisation/chowdhary2020_tables.csv`, with how they
were read), the stored run (`examples/data/polarisation/chowdhary2020.csv`)
and a test that every quoted figure is its; CHANGELOG; NEXT_STEPS. No
package change: 1.36.3.

### Result

Differences from the plan, and a finding. **A misprint in the
supplement: in Table S3b (AOS-II, the sun at 60 degrees) the 450 nm
column's R_U in the principal plane (azimuths 0 and 180, 25 values)
repeats R_I,Vector.** There U is zero by symmetry, as in every other
column of that plane in Tables S2 and S3; those 25 are left out, so
AOS-II has 1175 vector values. U's sign is the tables' as this tool
gives it (the glint fixes it: at azimuth 60 its U, from the plane of
incidence turned into the meridian plane, agrees with the tables' only
so; the first draft of `TO_TESTBED` had it reversed, as for sections 145
and 146, and missed all of U off the principal plane). The sign was
checked against a coherency matrix built in three dimensions for the
glint and for Rayleigh scattering, independent of the tool's frames.

1. Met. Reflection plus transmission keeps the flux of 10 000 random
   polarised beams on random facets, from either side (6658 of those
   from the water totally reflected), to 6.7e-16.
2. **Not met as set: 32 of 40.** At 650 nm in AOS-II the tables exceed
   the closed-form glint by 1.6e-4 to 3.0e-4 wherever the glint is more
   than 90 percent of them: the water's own light, of about that size
   everywhere. Where the glint is small (0.002 to 0.015) that is more than
   2 percent. The check should have bounded the remainder absolutely; the
   glint's own size and polarisation are checked by check 3.
3. **Met: AOS-I 1198 of 1200 values, AOS-II all 1175** (ten batches of
   100 000 photons, `examples/data/polarisation/chowdhary2020.csv`). The
   two AOS-I values that do not agree are I and Q of the glint's peak, at
   650 nm with the sun at 60 degrees, azimuth 0 and 60 degrees viewing,
   1.4322 and -1.3315, off by 1.4e-4 and 0.9e-4 (4.5 and 4.0 standard
   errors). The largest difference is 0.00016 in I for AOS-I at 450 nm,
   the sun at 60 degrees, azimuth 180 and 60 degrees viewing, where the
   standard error is 0.00006; for AOS-II 0.00010 in I at 350 nm, the sun
   at 30 degrees, azimuth 180 and 60 degrees viewing, where it is
   0.00004.
4. **Met: AOS-I 398 of 400, AOS-II all 400.** The two are at 450 nm with
   the sun at 60 degrees: 0.72806 for 0.72815 at the glint (azimuth 0,
   55 degrees) and 0.00519 for 0.00523 (azimuth 240, 45 degrees).
5. Recorded. The scalar I over the vector I: 0.595 to 1.462 for AOS-I,
   more than 5 percent off in 187 of its 400 directions, and 0.938 to 1.047 for AOS-II, off by more than
   5 percent in 22 of 400. The tables' own ratios agree (0.595 and 0.938
   at the same directions).

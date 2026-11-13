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

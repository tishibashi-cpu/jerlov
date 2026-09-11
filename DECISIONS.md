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

## 5. No extrapolation

Asking for a wavelength outside the data raises `ValueError`. A silently
extrapolated value is indistinguishable from a measured one at the point of
use, and the caller has no way to find out afterwards.

`kd_spectrum` applies the same rule to the Austin & Petzold model range.

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
  seen by an observer at depth z, look like" (planned; see below)

Out:

- Solving the radiative transfer equation. That is HydroLight's job.
- Remote sensing reflectance, the view from above the surface. HYDROPT and
  OpticalRS occupy that ground.
- Shortwave heating for ocean circulation models, where the Jerlov type is an
  integer index and no spectrum is involved.
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

**The angle range is enforced.** 90 to 170 degrees, which is what the
measurements cover, and a warning above a 10 percent quoted spread. At 170 the
spread is 34.8 percent against 3 to 6 in the middle, and a caller who picked
that angle should be told rather than handed a number.

**chi and chi_p are kept apart.** They are printed under the same symbol by
different authors, and differ by 9 percent at 140 degrees because one includes
water. The shipped table marks the rows from other authors
`other_definition` rather than dropping them: a reader comparing against those
papers needs to see why the numbers differ, not wonder where they went.

## 23. Planned

Recorded so the shape of the API can be judged against where it is going.

- **Akkaynak-Treibitz coefficients**: beta_D, beta_B and B_inf for a stated
  distance range. The range must be an argument, not hidden, because those
  coefficients are not constants.
- **Petzold phase functions**: measured volume scattering functions, so that
  a backscatter ratio can be chosen from a measurement rather than guessed
  when no instrument reading is available. Section 22 covers the case where
  there is one.

Validation is deliberately staged. The package can claim that it implements
published coefficients correctly, and the tests demonstrate that. It cannot
claim that it predicts what a camera will record underwater; that needs
measurements that have not been made. The README says so.

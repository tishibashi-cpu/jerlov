# Changelog

Every release is archived on Zenodo under the concept DOI
[10.5281/zenodo.22321312](https://doi.org/10.5281/zenodo.22321312), which
always resolves to the latest version.

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

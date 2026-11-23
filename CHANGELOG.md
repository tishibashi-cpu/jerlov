# Changelog

Every release is archived on Zenodo under the concept DOI
[10.5281/zenodo.22321312](https://doi.org/10.5281/zenodo.22321312), which
always resolves to the latest version.

## 1.26.7 — 2026-11-23

More to look at on the site (DECISIONS.md section 120). Nothing in the
package changed.

**Site.**

- The front page shows Kd of the ten types from Jerlov (1976), and the
  colour of the daylight left at 10 m in each.
- The examples page opens with six figures, each leading to the examples
  that print its numbers: the light at depth, why the source is an
  argument, colours through water, heating the upper ocean, Kd from
  chlorophyll, and scattering.
- A third page, "The waters side by side" (`waters.html`), puts every
  source of a type on one set of axes, for a, b, c and Kd, or every type
  of one source, with the caveats the package states for each.
- Links to the site now show a card when shared (`og.png`, with Open
  Graph and Twitter tags on every page).

**New tools.** `tools/site_figures.py` draws the figures (called by
`tools/site_pages.py`); `tools/og_image.py` renders the card with a
headless Chromium.

## 1.26.6 — 2026-11-22

The page "Where the sources disagree" gains questions 5 and 6, and a
figure for question 4 (DECISIONS.md section 119). Nothing in the package
changed.

**Site.** Question 4: the Monte Carlo's Kd over HydroLight's at the 143
cells, by type and wavelength. Question 5: the shallow-water model over
the Monte Carlo against pure water's share of the backscattering, for the
270 runs and for the 12 cases with only the share changed. Question 6:
where the paper's own Fig. 13 draws its symbols, against the paper's
straight-line fits; Morel et al.'s archive, which is not shipped, is not
drawn. Every figure is made by `tools/site_pages.py` from the package and
the repository's `examples/data/`, and the numbers the page computes are
checked against OPEN_QUESTIONS.md.

## 1.26.5 — 2026-11-22

The dip at 45 degrees in Morel et al.'s f/Q archive, in the paper's own
Fig. 13 (DECISIONS.md section 118). No value changed.

**Found.** Fig. 13 (p. 6301) plots f(0)/f against chlorophyll for five
sun angles. Read from the page image, its symbols at 0.03 and 0.1 mg
m^-3 hold all 60 of the archive's values there, a symbol on its own
within 0.0006 of its value; where the paper's linear fits put f(0)/f at
45 degrees and 0.03 mg m^-3, at 560, 620 and 660 nm, no symbol stands
within 0.0110 to 0.0164. The dip was in the values the paper plotted,
not brought in when the archive was packed. What went wrong in the run
is still not known. OPEN_QUESTIONS.md question 6, DATA.md section 48.

**New.** `tools/read_fig13.py PDF` reads the figure from your own copy of
the paper (not shipped) into
`examples/data/fq_at_45_degrees/fig13.csv`, which
`examples/fq_at_45_degrees.py` sets against the archive and the fits.

## 1.26.4 — 2026-11-21

The dip at 45 degrees in Morel et al.'s f/Q archive, against the
authors' own later tables (DECISIONS.md section 117). No value changed.

**Found.** NASA's OCSSW, the processing code behind SeaDAS, distributes
the archive's tables and f/Q tables recomputed by Bernard Gentili, one of
the authors, at 70 wavelengths for the same sun angles and chlorophylls.
The recomputation does not have the dip: at the sun of 45 degrees and
0.03 mg m^-3 its nadir f/Q lies -0.19 to -0.13 percent from the line
between 30 and 60 degrees, as at 0.1 mg m^-3, and against the archive,
along the sun angle, it departs at that one run only. The archive's run
stays suspect; what went wrong in it is not known. OPEN_QUESTIONS.md
question 6, DATA.md section 48.

**Changed.** The warning for that run says the later tables do not have
the dip.

**New.** `examples/fq_at_45_degrees.py --ocssw DIR` compares the archive
with NASA's copies, which you fetch and which need h5py; nothing of them
is shipped.

## 1.26.3 — 2026-11-21

The dip at a sun of 45 degrees in Morel et al.'s (2002) f/Q archive,
located: a sixth open question (DECISIONS.md section 116). No value
changed.

**Found.** The dip belongs to one run of the authors' archive, the sun at
45 degrees and 0.03 mg m^-3. There f lies below the line between its
values at 30 and 60 degrees at all seven wavelengths, by 1.01 to 3.44
percent, growing with the wavelength, where every other chlorophyll lies
above it; f/Q follows f, and the run is out of order against its
neighbour in chlorophyll at every wavelength, which no other run is. What
made it so is not known. OPEN_QUESTIONS.md question 6, DATA.md section
48.

**Changed.** `Morel2002FQTables.f` and `.f_over_q` give a
`ProvenanceWarning` at that sun angle and chlorophyll; the values are
returned as the archive has them.

**New.** `examples/fq_at_45_degrees.py`, the thirtieth example, which
reads your own copy of the archive given as `--archive PATH` and without
one only says so.

## 1.26.2 — 2026-11-21

The fifth open question taken further: would keeping water and particles
apart, or the phase function, close the shallow-water model's two groups
of misses (DECISIONS.md section 115)? No shipped value, code or public
name changed.

**Found.** Lee et al.'s (2011) deep-water form, which keeps water and
particles apart, used with its published coefficients and nothing
fitted, follows pure water's share of the backscattering where the 1999
model does not: it moves by 1.054 to 1.079 times against the Monte Carlo
across the shares, the 1999 model by 1.232 to 1.333. Over a black bottom
the miss is ordered neither by the particles' bb/b (it rises with bb/b in
5 of 24 cells) nor by the mean cosine, and the Monte Carlo's cut at 1
degree does not set the stations apart. OPEN_QUESTIONS.md question 5,
DATA.md section 50.

**New.** A fourth part of `examples/shallow_water_closure.py`, and the
runs it reads (`water_share_nadir.csv`, `cut_check.csv`, written by
`tools/shallow_rrs_mc.py`).

## 1.26.1 — 2026-11-21

Why the shallow-water reflectance model of 1.26.0 misses two groups of
Monte Carlo runs: a fifth open question, with numbers (DECISIONS.md
section 114). No shipped value, code or public name changed.

**Found.** With u held, the model over the Monte Carlo falls as pure
water's share of the backscattering rises, in 12 of 12 cases: the model,
a function of u alone in deep water, does not tell water from particles,
which accounts for the direction of the first group's miss but not all of
its size. The waters of Lee et al.'s own runs, rebuilt from their Table 1
and equations, have pure water at most 0.46 of bb. Over a black bottom in
shallow, turbid water no single change to the Monte Carlo (another of
Petzold's phase functions, a sky) brings the group back within 10
percent, and the particles' phase function alone moves the ratio in a
cell by a factor of up to 1.92: the model's column term depends on the
phase function, which it does not take. OPEN_QUESTIONS.md question 5,
DATA.md section 50.

**New.** `examples/shallow_water_closure.py`, the twenty-ninth example,
prints every figure from the runs kept in `examples/data/shallow_rrs_mc/`
(written by `tools/shallow_rrs_mc.py`, now with a sky option, and
`tools/lee1998_runs.py`).

**Docs.** OPEN_QUESTIONS.md question 5, its line on the site's open
questions page, DATA.md section 50 and the example lists.

## 1.26.0 — 2026-11-21

The remote sensing reflectance of shallow water, with the bottom in view
(DECISIONS.md section 113). No earlier value changed.

**New.** `lee1999_shallow_rrs(a, bb, /, *, depth_m, bottom_albedo,
sun_zenith_deg)` and `ShallowRrs`: the semianalytical model of Lee et al.
(1998), with the constants their 1999 paper updated, for a homogeneous
water over a Lambertian bottom seen straight down. It gives rrs just below
the surface, its water-column and bottom parts, the same water with no
bottom, and Rrs above the surface. The bottom's depth and albedo and the
sun have no default; outside the sun, depths and waters of the paper's
HydroLight runs the result comes with a `ProvenanceWarning`. The package's
range widens to optically shallow water for this forward relation only;
deriving depth and bottom albedo from a measured spectrum stays out.

**Found.** The 1999 paper replaced the 1998 constants after "correcting a
calculation error in the earlier study"; only the 1999 set is used. Against
a Monte Carlo with a flat surface, a Lambertian bottom and another of
Petzold's phase functions (`tools/shallow_rrs_mc.py`, 270 runs), the model
has a median ratio of 0.999, and 87.4 percent of the runs are within 10
percent, short of the 90 percent set beforehand. The model runs low, by up
to 18 percent, where pure water carries most of the backscattering, and
high, by up to 72 percent, over a black bottom a few metres down in turbid
water. The 1998 constants do worse against the same runs. DATA.md section
50.

**Docs.** The map, the page on ocean colour, the README, a part 13 of
`examples/ocean_colour_and_secchi.py` (how deep the bottom stays in view
for four Jerlov types), DATA.md section 50 and the Zenodo description.

## 1.25.2 — 2026-11-21

Letting search engines find the documentation site (DECISIONS.md section
112). No shipped value, code or public name changed.

**Docs.** The site now has a `sitemap.xml`, written at each build, with
every page including "Daylight on the way down" and "Where the sources
disagree"; a canonical address on every page; a description for the index
page; and the file Google Search Console asks for to confirm who maintains
the site. The Zenodo record links to the site.

**Tests.** The verification file, the sitemap hook and the Zenodo link are
checked, and the docs workflow reads the built sitemap back.

## 1.25.1 — 2026-11-20

The spectrum on the site's "Daylight on the way down" says how much it is
enlarged, and its colour chip works on the site (DECISIONS.md section 111).
No shipped value, code or public name changed.

**Docs.** Each curve of that page's spectrum is scaled to its own peak, so
at depth the solid line can stand above the surface's dashed one although
the light there is far weaker. The chart now gives the factor by which the
solid line is enlarged, which in turbid water at depth runs to many orders
of magnitude, and the caption says that the curves compare shape only and
that the numbers above give how much light is left.

**Fixed.** On the site, that page's "outside sRGB, shown clipped" chip showed
at every depth since 1.24.1: the standalone page lacked the rule that makes
the `hidden` attribute win over the chip's display. Its test for a colour
outside sRGB is now relative to the brightest channel, so deep, dim colours
outside sRGB are flagged too. Both pages carry the rule.

**Tests.** The factor the page's script computes is the surface's peak over
the depth's, and the chip agrees with jerlov's own `spectrum_to_srgb`, both
checked with node where it is installed; both pages carry the `hidden` rule.

## 1.25.0 — 2026-11-20

NumPy 1.24.0 as the lowest supported version (DECISIONS.md section 110). No
value, code or public name changed.

**Changed.** NumPy 1.24.0 or later is needed. NumPy 1.23, through its last
release 1.23.5, carries OpenBLAS 0.3.20, whose CooperLake kernels gave
wrong matrix products in `examples/painted_sphere.py` on an Intel Xeon
6975P-C (the grey sphere 11.4 times the water from above where 14.5 is
right). Forcing those kernels reproduces it on another processor under
NumPy 1.23.2 and 1.23.5; NumPy 1.24.0, with OpenBLAS 0.3.21, gives the
right figures. CI's job for the oldest NumPy now runs 1.24.0.

**Tests.** A test checks that the NumPy CI pins for that job is the floor
pyproject.toml declares.

## 1.24.1 — 2026-11-20

Two pages on the site made from the package's own values (DECISIONS.md
section 109). No shipped value, code or public name changed.

**Docs.** "Daylight on the way down" (`dive.html`) sets the ten Jerlov types
side by side from 0 to 100 m, each coloured by the sunlight left at that
depth, and gives, for a type and depth a reader picks, the luminance and
PAR left, the depths where PAR falls to 10, 1 and 0.1 percent, the spectrum,
and ten measured materials lit at that depth. "Where the sources disagree"
(`disagree.html`) gives the four questions of OPEN_QUESTIONS.md a figure
each: the published absorption spectra of pure water, Petzold's scattering
below 0.1 degree, the Monte Carlo Kd from Williamson & Hollins's a and b
over Jerlov's with the cells no unrecorded condition can reach outlined,
Jerlov's 1976 Kd over his 1968, and the beam attenuation of one type from
two sources. Both pages print what they assume, load nothing from another
host, and are linked from the index and the open questions page.

**Internal.** `tools/site_pages.py` writes both pages into `docs/pages/`
from templates in `tools/site_pages/`, embedding the values it takes from
the package; the docs build copies them to the site's root.

**Tests.** `tests/test_site_pages.py` checks that the pages are what the
tool writes now; that the first page's arithmetic, done again in NumPy and,
where node is installed, by the page's own script, gives `spectrum_to_srgb`
and `par_profile` within 1e-5 and the 1 percent depths within 1 mm; and
that every figure the second page quotes is in OPEN_QUESTIONS.md or DATA.md.

## 1.24.0 — 2026-11-18

Python 3.11 as the lowest supported version (DECISIONS.md section 108). No
value, code or public name changed.

**Changed.** Python 3.11 or later is needed, and NumPy 1.23.2 or later:
Python 3.10 reached its end of support in October 2026, and 1.23.2 is the
first NumPy with wheels for Python 3.11. CI's job for the oldest NumPy runs
Python 3.11 with NumPy 1.23.2 exactly.

## 1.23.0 — 2026-11-18

The attenuation of light that forward scattering turns rather than loses,
from Petzold's measured scattering (DECISIONS.md section 107). No earlier
value changed.

**New.** `forward_scatter(scattering, half_angle_deg)` and `ForwardScatter`:
for one of Petzold's stations, the share of the scattering within a
half-angle from 0.1 to 180 degrees, and c - b(< theta0), what a receiver
accepting light within that angle reads. At the report's printed angles the
share is the report's own cumulative integral. `attenuation_within(water,
wavelengths, /, *, forward)` applies that share to a water's own b, which
assumes the station's phase function holds for the water at every
wavelength; the station has no default. Within 5 degrees lies 46 to 64
percent of b at Petzold's eight stations.

**Found.** A Monte Carlo of a collimated beam (`tools/forward_scatter_mc.py`)
agrees with single scattering within 0.36 percent wherever b r <= 0.5. At
b r = 3 it is up to 8.5 percent below in a 20-degree cone and up to 3.1
percent above in the narrower ones. The share below 0.1 degree, the report's
extension, enters every result and always warns. DATA.md section 49.

**Docs.** The map and the page on seeing through water; DATA.md section 49;
the README; the Zenodo description.

## 1.22.2 — 2026-11-17

The README becomes an introduction, its topics move to the site, and the
site gains a map of which function to use (DECISIONS.md section 106). No
shipped value changed, no code changed and no public name was added.

**Docs.** The README, which PyPI shows as the project's page, had grown to
782 lines; it is now 213. It keeps what to read before installing: what is
claimed and what not, a first call, why the source is an argument, what
the package will not do, provenance warnings, the sources, the examples,
contributing, licence and citation, and lists the topics with a link to
each. The topics are six pages on the site, their text as the README had
it: seeing through water, light with depth, from a measurement, ocean
colour without a water type, water for other software, and solar heating.
A new page, "Which function to use", lists every public function by what
you want and what you have: Kd alone comes from seven functions, each for
a different starting point.

**Tests.** The figures the README quoted are read from the pages they
moved to. Every public function, and `Water` and `Scene`, must be on the
map, and every name the map and the topic pages give must exist and be
public.

## 1.22.1 — 2026-11-17

A review of what 1.16.0-1.22.0 added (DECISIONS.md section 105). No
shipped value changed and no public name was added.

**Fixed.** `morel2002_nadir_fq` was the one positional-only public
function that refused its wavelength by keyword; it now takes it with a
`FutureWarning`, as all the others do until 2.0. It checks each argument
as one finite number, as the other functions of one number do: text,
never offered, is refused, and a NaN is named as such. Its docstring
said the full tables were on a server the package could not reach; it
points to `morel2002_fq_tables`. A NaN wavelength given to
`morel2001_kd`, `morel1988_kd`, `bricaud1995_aph` or `morel2001_bbp` is
refused as "not NaN" rather than as outside the range (still
`ValueError`).

**Found.** Away from a zenith sun, Morel et al.'s (2002) Eq. (B1) departs
from the f of the authors' own archive by up to 1.10 percent at 30
degrees, where the paper says "less than 0.5%" below 45, and by up to 2.70
at 45; Eq. (B4) departs from the archive's f/Q by up to 3.34 percent, also
at 45 (within the paper's "+-3.4%"). What stands out is the archive's f at
45 degrees: in the red at 0.03 mg m^-3 it lies up to 3.44 percent below
the straight line between its own values at 30 and 60, which the linear
fits do not follow. Why is not known. DATA.md section 48; the docstring of
`morel2002_nadir_fq` says it.

**Documented.** The flat methods of `rottgers2013_scatter_correction`
give a gap where cm has one, though they do not use cm: a gap in the
measurement at a wavelength is a gap in what it gives there. Unchanged,
now said and tested.

**Internal.** The three copies of the one-number check (`sky`,
`absorption_meter`, `fq_tables`) are one, `_data.finite_number`. A test
checks that every positional-only public function carries the keyword
shim, so that the next one cannot be missed.

## 1.22.0 — 2026-11-16

Morel et al.'s (2002) full f/Q tables, read from the user's own copy of
the authors' archive (DECISIONS.md section 104). No earlier value changed.

**New.** `morel2002_fq_tables(path, /)` and `Morel2002FQTables`: f, f/Q
for 17 nadir angles in water by 13 azimuths, and the surface factor
R-gothic, at the archive's own values only. The archive states no licence
and is not shipped; the function checks its MD5 and says where to get it.

**Found.** The archive's linear approximations equal the paper's printed
Appendix B in all 252 values; its R-gothic is for 0, 4, 6, 8 and 16 m/s and
a flat sea, where the paper says 0, 4, 10 and 16.

**Documents.** DATA.md section 48, sources/README.md, the README, the API
reference. The Zenodo description, which had grown into one long paragraph,
is set out as short paragraphs and lists by topic; its content is unchanged.

## 1.21.0 — 2026-11-16

f and Q for an upward radiance from the nadir, Morel et al. (2002),
Appendix B (DECISIONS.md section 103). No earlier value changed.

**New.** `morel2002_nadir_fq(wavelength_nm, /, *, chlorophyll_mg_m3,
sun_zenith_deg)` and `NadirFQ`: f, Qn and f/Qn from their Eqs. (B1),
(B2) and (B4), and the correction of Eq. (B3) to a zenith sun. Only the
paper's seven wavelengths and six chlorophylls; f and Q to 60 degrees, the
ratio to 75, with a warning from 60. Other viewing directions need the
full tables, on a server that did not answer.

**Data.** `morel2002_nadir_fq.csv`, 252 values, from literals in
`tools/build_morel2002.py`.

**Examples.** `ocean_colour_and_secchi.py` part 12: the correction falls
to 0.83 at 560 nm, 10 mg m^-3 and the sun at 75 degrees; Aas &
Højerslev's measured Qn is within 2.6 percent of Table 2.

## 1.20.0 — 2026-11-16

The clearest natural waters, Morel et al. (2007) (DECISIONS.md section
102). No earlier value changed.

**New.** `morel2007_stations()` and `ClearWaterStation`: the eight
stations of their Table 1, South Pacific gyre, 2004. `pure_water_absorption_table`
gains `source="morel2007"` (aw1, 300-500 nm) and `"morel2007_aw2"` (aw2,
300-370 nm), their Table 2.

**Data.** `morel2007_aw.csv` and `morel2007_stations.csv`, from literals in
`tools/build_morel2007.py`.

**Found.** At GYR-5 and STB-14, ay2 - ay1 is 0.0100 short of what Table 2
requires: a likely misprint, kept and flagged. aw1 from 420 nm is Pope &
Fry's at every 10 nm, and the mean of their neighbours at 425-455 nm.

**Examples.** `ocean_colour_and_secchi.py` part 11: the stations' Kd(420)
is 0.52 to 0.99 of Jerlov's type I, and at seven of eight below Austin &
Petzold's pure sea water.

## 1.19.0 — 2026-11-16

Morel's (1988) Kd from the pigment concentration, beside the 2001 edition
(DECISIONS.md section 101). No earlier value changed.

**New.** `morel1988_kd(wavelengths, /, *, pigment_mg_m3)`: K = Kw + chi
C^e with Morel's (1988) Table 2, 400-700 nm; C is chlorophyll a plus
pheophytin a, not the HPLC chlorophyll of `morel2001_kd`, and has no
default. It warns outside 0.03-30 mg m^-3 and beyond 650 nm, where the
paper fitted chi and e to mesotrophic and eutrophic waters only.

**Data.** `morel1988_kd.csv`, 61 rows, from literals in
`tools/build_morel1988.py`.

**Found.** Morel & Maritorena (2001) kept the 1988 chi and e unchanged
from 560 nm, not only beyond 590-600 nm as DATA.md section 27 said from
their text; section 27 is corrected and points to section 45, which also
explains its unexplained rounding from 560 nm.

**Examples.** `ocean_colour_and_secchi.py` part 10: the two editions side
by side; at 0.03 mg m^-3 2001's Kd is 0.69 of 1988's at 412 nm, and the
revised Kw alone accounts for more than the whole change.

## 1.18.0 — 2026-11-16

Scatter correction of reflective-tube absorption meters (ac-9, ac-s);
DECISIONS.md section 100. No earlier value changed.

**New.** `rottgers2013_scatter_correction(am, cm, am_ref, cm_ref, /, *,
method, ec=None, a_ref=None)`: the flat, proportional, flat+ and
proportional+ corrections of Röttgers, McKee & Woźniak (2013), each as
printed, the method with no default, ec required by the proportional
methods and a_ref (the true absorption at the reference wavelength) by the
"+" methods. `rottgers2013_a715(am715, /)`: their estimate of a(715) from
the uncorrected reading, which warns outside the span of their samples.

**Examples.** `from_one_measurement.py` part 7: the absorption meter's
error from each of Petzold's eight scattering functions, as Zaneveld,
Kitchen & Moore (1994) computed it (HAOCE 11 gives their 5.7 percent),
and what each correction then recovers for Jerlov III: with a(715) of
0.01 per m, the proportional method falls 40 percent short at 555 nm.

**Documents.** DATA.md section 44, the README, the API reference.

## 1.17.0 — 2026-11-16

The sea surface's reflectance factor rho, and Rrs from radiances measured
above the water (DECISIONS.md section 99). No earlier value changed.

**New.**

- `mobley_rho(*, source, wind_speed, sun_zenith_deg, view_nadir_deg,
  view_azimuth_deg)`: rho from Mobley's (1999) table or his (2015) one,
  `source` with no default. Linear in the wind and the sun between the
  table's points; the viewing direction must be one of the table's, since
  each value is a mean over its band of directions; outside the table,
  refused. The 2015 table calls itself preliminary and warns.
- `rrs_from_above_water(lt, lsky, ed, /, *, rho)`: (Lt - rho Lsky) / Ed;
  rho has no default; a negative result is kept.

**Data.** `mobley1999_rho.csv` (8496 values) and `mobley2015_rho.csv`
(11800), from the Ocean Optics Web Book's files as printed, by
`tools/build_mobley_rho.py`; Creative Commons Attribution, in `NOTICE`.

**Examples.** `ocean_colour_and_secchi.py` part 9: at the recommended
view (40, 135), sun 30 and 5 m/s, the two tables give 0.0283 and 0.0411;
in Jerlov IB, Rrs made with one and recovered with the other is off by
16 percent at 443 nm and 619 percent at 670 nm, or below zero.

**Documents.** DATA.md section 43, the README, the API reference, NOTICE,
sources/README.md.

## 1.16.0 — 2026-11-16

The attenuation of the visible and of the whole shortwave from a and bb,
and the euphotic depth (DECISIONS.md section 98). No shipped value changed.

**New.** From Lee, Du, Arnone, Liew and Penta (2005), J. Geophys. Res.
110, C09019 (not the C02016 of `lee2005_kd`), and Lee, Weidemann, Kindle,
Arnone, Carder and Davis (2007), J. Geophys. Res. 112, C03009:

- `lee2005_kvis(a490, bb490, depth_m, /, *, sun_zenith_deg)`: the mean
  attenuation of the 350-700 nm energy from the surface to a depth;
- `lee2007_depth_of_fraction(a490, bb490, /, *, sun_zenith_deg,
  fraction)`: the depth where that energy falls to a fraction of its
  surface value, the euphotic depth at 0.01, from the paper's cubic, each
  root checked against the unsquared equation;
- `lee2005_kir(depth_m, /, *, sun_zenith_deg)`: the same for 700-2500 nm,
  from the depth and the sun alone;
- `lee2005_shortwave_transmittance(a490, bb490, depth_m, /, *,
  sun_zenith_deg, visible_fraction)`: the two together; the visible share
  of the surface shortwave has no default (the paper's 0.424 is
  Mobley's).

None has a default for the sun. Where K1 would not be positive or K2 would
be negative, the model has no meaning and is refused, not clipped. Outside
the sun, the K_VIS, the T_VIS or the depths the papers fitted, a
`ProvenanceWarning` says so.

**Examples.** `euphotic_zone.py` part 7 holds the depth of each of
Jerlov's (1977) quanta levels against the model from Solonenko & Mobley's
and Williamson & Hollins's a and b, with bb from each of Petzold's eight
B/S: a median of 1.13 and 0.91 of his depths, his within the reach of r
and the sun in 38 of 48 cells. `solar_heating.py` part 6 holds the
shortwave model against Jerlov's (1968) Table XXI beside Paulson &
Simpson's fit: in the top 10 m the model misses less for three or four of
the five oceanic types, below it the fit does.

**Documents.** DATA.md section 42, the README, the API reference.

## 1.15.9 — 2026-11-16

What the choice of pure water absorption does to the colour of the
clearest water. No shipped value changed, and no name changes
(DECISIONS.md section 97).

**Examples.** `ocean_colour_and_secchi.py` gains part 8. With pure sea water
alone, the five pure water absorption spectra the package ships give
remote sensing reflectances up to 6.85 times apart at 380 nm, 2.62 at 443
and 1.13 at 550, and Rrs(443)/Rrs(550) from 10.73 to 24.75. In Jerlov IB
they move Rrs by 1.12 to 1.34 times, less at every wavelength than the
particles' backscatter ratio does over Petzold's eight measured values.
Below 443 nm the pure sea water figures lie, for three spectra, outside the
data Lee et al.'s (2011) relation was fitted to, and the example says so.

**Documents.** `OPEN_QUESTIONS.md`'s first question, DATA.md section 29 and
the README of the examples.

## 1.15.8 — 2026-11-16

What the literature says of Jerlov's coastal blue, and what rests on
Petzold's extension below 0.1 degree. No shipped value changed, and no
name changes (DECISIONS.md section 96).

**Examples.** `phase_function_choice.py` gains part 3. Without the
report's power-law extension below 0.1 degree, which nobody measured, the
mean cosine at Petzold's eight stations falls by 0.004 to 0.015, B/S rises
by 3.5 to 17.0 percent and the Henyey-Greenstein g of the backscatter fit
falls by 0.004 to 0.016. Kd, by Monte Carlo, moves by -0.63 to +0.13
percent when the light scattered by less than 0.1 degree is treated as not
scattered: Kd does not rest on the extension. Part 3 reads Monte Carlo runs
kept in `examples/data/below_0_1/`.

**Documents.** Jerlov states no reason for raising the coastal blue Kd in
1976 (Marine Optics, pp. 133 and 137); he describes the coastal types as a
special classification of northern waters rich in yellow substance,
fortified by new data. Aas et al. (2013) note that waters of coastal Kd in
the open sea are often blooms, not yellow-substance-rich water, and
Højerslev (1978) describes Jerlov's 1976 coastal types as average
conditions for coastal waters rich in yellow substance. All are
recorded in DATA.md sections 21 and 41 and in `OPEN_QUESTIONS.md`'s second
and third questions, with the reports not obtained.

**Tools.** `tools/kd_monte_carlo.py`'s `petzold_sampler` can start at 0.1
degree, off by default, when nothing changes; new `tools/below_0_1.py`.

## 1.15.7 — 2026-11-16

Why IOPs and Jerlov's Kd disagree at the blue end, from the Kd measured in
the same waters. No shipped value changed, and no name changes
(DECISIONS.md section 95).

**Examples.** `closure_with_jerlov_kd.py` gains part 7. Williamson &
Hollins's dataset keeps the Kd of every campaign they typed, and, for
473 entries, a, b and Kd measured in the same campaign. The campaigns
typed 1C, 3C and 5C measured Kd at 412 nm of a median 0.59, 0.53 and 0.56
of Jerlov's (1976), what their averaged IOPs give, and the Monte Carlo
from each campaign's own a and b gives 0.90, 0.93 and 1.06 of its own Kd:
the coastal blue gap is between those waters and Jerlov's 1976 values,
not in the IOPs. Against his 1968 edition the measured Kd are 0.85, 0.66
and 0.62. The campaigns typed IB measured Kd of 1.02 to 1.12 of Jerlov's;
IB's high averaged a rests on six campaigns, in two of which a is at or
above the Kd measured in the same campaign. Part 7 also gives the two
editions' ratio at 425 nm, the a that would close each blue cell in
standard deviations of the measured points, and the separation of
neighbouring types.

**Data.** `examples/data/blue_end/`: four files reduced from the figshare
dataset (Crown copyright (2022), Dstl, Open Government Licence v3.0), and
2365 Monte Carlo runs; not in the wheel.

**Tools.** New: `tools/blue_end.py`, which checks the four source files
against figshare's MD5.

**Documents.** `OPEN_QUESTIONS.md`'s third question, the site's page,
DATA.md section 41, the READMEs and `sources/README.md`.

## 1.15.6 — 2026-11-16

A check of the Monte Carlo behind `OPEN_QUESTIONS.md`'s third question
against HydroLight, and a fourth question. No shipped value changed, and
no name changes (DECISIONS.md section 94).

**Examples.** `closure_with_jerlov_kd.py` gains two parts. Part 5 runs
Williamson & Hollins's IOPs again with pure water's share of the
scattering turned by water's own phase function and a clear sky: Kd rises
by 1.3 to 7.6 percent, and OSOAA's Kd, which had been 1.007 to 1.096 times
the Monte Carlo's, is 0.991 to 1.018 times it; the blue cells where the
IOPs and Jerlov (1976) disagree beyond the unrecorded conditions stay,
with IB at 500 nm added, just beyond. Part 6 puts Solonenko & Mobley's
(2015) retrieved a and b through the Monte Carlo and sets the result
beside the Kd HydroLight made of them: a median of 0.970 times, 94.4
percent of 143 cells within 10 percent, the criterion written down before
the runs met; OSOAA, given the same totals, agrees with the Monte Carlo
within 4 percent.

**Data.** 2457 Monte Carlo runs in `examples/data/sm_closure/` and 286
OSOAA runs in `examples/data/osoaa_sm_closure/`, neither in the wheel.

**Tools.** `tools/kd_monte_carlo.py` gains two options, pure water's own
scattering and a sky, both off by default, when it reproduces the runs of
1.15.4 bit for bit; `--check` checks both. New: `tools/sm_closure.py` and
`tools/osoaa_sm_closure.py`. `tools/osoaa_closure.py` takes another way of
making its inputs, which it does not use itself.

**Documents.** `OPEN_QUESTIONS.md` gains a fourth question and its third is
updated; the site's "Open questions" page; DATA.md section 40, and section
39 says where OSOAA's excess went; the READMEs.

## 1.15.5 — 2026-11-15

A fix: `osoaa_phase_function` wrote OSOAA's phase function 4 pi too small,
and the fault behind the low OSOAA Kd of 1.15.3 was the package's, not
OSOAA's (DECISIONS.md section 93). No name changes.

**Fixed.**

- `osoaa_phase_function` writes F11 = 4 pi vsf / b. OSOAA expects a phase
  function whose integral over the sphere is 4 pi and takes its truncation
  coefficient from it without normalising it. Releases 1.14.0 to 1.15.4
  wrote vsf / b, whose integral is 1; OSOAA then treated 96.5 to 97.8
  percent of the hydrosols' scattering as unscattered and gave Kd that
  were too low. The files it writes change; a test checks the
  normalisation at every station.
- 1.15.4 put the low Kd down to OSOAA truncating Petzold's phase
  functions too far (DECISIONS.md section 92), without reading OSOAA's
  source; that was wrong. The docstring's warning that blamed OSOAA is
  gone.

**Data.** The OSOAA run kept for the readers' tests,
`tests/data/osoaa_iii_440/`, made again with the corrected file, now with
its `PM_PHYTO.txt`: truncation coefficient 1.40215, mean Kd from 0 to 50 m
0.1577 per m (was 0.1381). The 408 OSOAA runs of DATA.md section 39 made
again in `examples/data/osoaa_closure/`: OSOAA's Kd is 1.007 to 1.096
times the Monte Carlo's, and against Jerlov (1976) it lies beyond what
the unrecorded conditions can explain at the same places, but for 5C at
425 nm. The old runs move to `examples/data/osoaa_closure_f11_too_small/`
as the record. The Monte Carlo's results and the conclusions of 1.15.4 do
not change.

**Documents.** DATA.md sections 38 and 39, `OPEN_QUESTIONS.md`, the
"Open questions" page, the README of the examples and of `tools/`.
`closure_with_jerlov_kd.py` prints OSOAA as a second calculation and the
old runs as the record; `radiative_transfer_inputs.py --read` prints the
new run. `tools/osoaa_closure.py` writes `truncation.csv` itself.

## 1.15.4 — 2026-11-15

Open questions in a document of their own, with an example; and the
closure of 1.15.3 corrected (DECISIONS.md sections 91 and 92). No package
code, value or name changes; one docstring gains a warning.

**Corrected.** The comparison of 1.15.3 between Williamson & Hollins's
IOPs and Jerlov's Kd rested on OSOAA, whose Kd were too low: it treated
96.5 to 97.8 percent of the scattering of Petzold's phase functions as
unscattered, and its Kd fell 0.7 to 23.1 percent below a Monte Carlo
checked against Morel and Loisel's relation. Done again with that Monte
Carlo (240 runs), the two sources are consistent within what the
unrecorded sun, phase function and pure water can explain, except at the
blue end: IB at 425-475 nm and the coastal types at 425-450 nm. 1.15.3's
conclusion that the coastal types' IOPs describe different water, and
that the phase function hardly matters, was wrong. DATA.md sections 38
and 39 say so.

**Documents.**

- `OPEN_QUESTIONS.md`: where the sources disagree, by how much, and how
  much of it the conditions a source leaves unrecorded could explain.
  Three questions so far: the absorption of pure water in the violet, the
  scattering below Petzold's first angle, and whether Williamson &
  Hollins's IOPs give back Jerlov's Kd. Each sets out the question, what
  was done, what was found, what is not known and where the details are;
  every figure is recomputed by a test.
- A page of the documentation site, "Open questions", lists them with
  their findings and links to the document.
- `osoaa_phase_function`'s docstring warns of OSOAA's truncation.

**Examples.** `closure_with_jerlov_kd.py`, the twenty-eighth: reads the
Monte Carlo runs and prints, computing every figure, the computed Kd
beside Jerlov's in both editions, how far each unrecorded condition moves
it, where the gap is larger, and OSOAA's Kd beside the Monte Carlo's. It
needs the repository, for those runs.

**Tools and data.** `tools/kd_monte_carlo.py` and `tools/kd_closure.py`;
the runs in `examples/data/kd_closure/`. The OSOAA runs of 1.15.3 move
from `tests/data/osoaa_closure/` to `examples/data/osoaa_closure/`, with
each run's truncation coefficient, as the record. None of it is in the
wheel.

## 1.15.3 — 2026-11-15

Where the closure between IOPs and Kd fails: Williamson & Hollins's a and b
for six Jerlov types, run through OSOAA, against the Kd Jerlov printed
(DECISIONS.md section 90). No package code, value or name changes.

**Data.** DATA.md section 39 (note), from 408 OSOAA runs kept in
`tests/data/osoaa_closure/` (not in the wheel) and made by
`tools/osoaa_closure.py`:

- OSOAA's Kd over Jerlov's (1976) is 1.00-1.36 for IB, 0.87-1.07 for II
  and 0.79-0.95 for III, but down to 0.48 for 3C and 0.54 for 1C and 5C.
- Of the conditions a type leaves open, the sun moves Kd most (-7.1 to
  +20.7 percent), then the pure water under the type's contents (-12.0 to
  +6.2); the Petzold station, the aerosol and the wind move it by under
  1.5 percent.
- Against 1976, II and III lie within what the sun and the pure water can
  make; IB in the blue and the coastal types do not.
- 46 runs could not be made: from 650 nm OSOAA's own pure water is above
  the aw Williamson & Hollins built a on, so their total a there cannot be
  given to OSOAA.

## 1.15.2 — 2026-11-15

Two open questions recorded beside the data they bear on (DECISIONS.md
section 89). Documents only: no code, value or name changes.

**Documents.**

- DATA.md section 29: how far apart the four published spectra of pure
  water absorption are, computed from the shipped tables. Pope & Fry over
  Mason et al. is 7.95 at 380 nm, 1.22 at 440, and within 0.97-1.08 from
  460 to 550 nm; which is right in the violet is not settled.
  `pure_water_absorption_table`'s docstring points there.
- DATA.md section 21: below Petzold's first angle, 0.1 degree, Bogucki et
  al. (2004) measured scattering on oceanic turbulence of 1 to 10 m-1 in
  total; Petzold's extension there is a power law of particle and water
  scattering and does not include it.

## 1.15.1 — 2026-11-15

Three defects found in a review of the code added in 1.11.0-1.15.0
(DECISIONS.md section 88). No shipped value changed, and no name is added
or removed.

**Fixed.**

- `rgb_transmittance` formed the spectra of every distance at once, so a
  long table took memory in proportion: 20,000 distances took 678 MB. The
  distances are now formed in blocks, each row exactly as before, so every
  value is unchanged to the last bit.
- `osoaa_user_profile` and `hydrolight_ac9_file` printed depths, and
  HydroLight's wavelengths, to six significant digits: distinct depths
  such as 100.0000001 and 100.0000002 m were written alike, a profile no
  longer ascending, and 1234.56789 m was written 1234.57. They are now
  printed to 15 digits, and a list whose printed values do not ascend
  strictly is refused. Depths such as 0, 10 and 50 are written as before.
- `osoaa_phase_function` accepted polarization ratios of any size. Each
  of -F12/F11, F22/F11 and F33/F11 must now lie in [-1, 1], since no
  element of a Mueller matrix of scattering exceeds F11 in magnitude.

## 1.15.0 — 2026-11-15

OSOAA's results read back (DECISIONS.md section 87). No shipped value
changed; six public names are added.

**Added.**

- `read_osoaa_flux(text)` → `OsoaaFlux`: OSOAA's `Flux.txt`, the direct,
  diffuse and total fluxes down and up at every level, as printed,
  normalized to an extraterrestrial irradiance of pi, with the sea's
  levels marked; `OsoaaFlux.kd(upper_m, lower_m)` gives the mean Kd of Ed
  between two depths.
- `read_osoaa_radiance_vs_depth(text)` → `OsoaaRadianceProfile` and
  `read_osoaa_radiance_vs_vza(text)` → `OsoaaRadianceScan`: OSOAA's
  `RESLUM_vsZ.txt` and `RESLUM_vsVZA.txt`, the normalized radiance, the
  reflectance and the polarization against depth or viewing zenith angle.
- Nothing is converted to W/m2: Esun is the caller's, as OSOAA leaves it.

**Examples.** `radiative_transfer_inputs.py --read DIR` reads the results
of an OSOAA run made with its files and sets the Kd OSOAA made of Jerlov
III beside Jerlov's own and HydroLight's.

**Data.** DATA.md section 38: the run kept in `tests/data/osoaa_iii_440`
for the tests, what its files hold, and that OSOAA's direct flux includes
the forward peak it truncates.

## 1.14.0 — 2026-11-15

Input files for two radiative transfer codes, OSOAA and HydroLight
(DECISIONS.md section 86). No shipped value changed; three public names
are added.

**Added.**

- `osoaa_user_profile(water, wavelength_nm, *, depths_m, pure_water)`:
  OSOAA's `-HYD.UserProfile` file, the water's a and b less the pure
  seawater OSOAA adds back, at one wavelength.
- `osoaa_phase_function(scattering, *, minus_f12_over_f11, f22_over_f11,
  f33_over_f11)`: OSOAA's `-HYD.ExtData` file from one of Petzold's
  stations, F11 = vsf / b at his 55 angles, with the polarization ratios
  he did not measure given by the caller.
- `hydrolight_ac9_file(water, wavelengths, *, depths_m, pure_water)`:
  HydroLight's standard-format file of a and c less pure water.
- The pure water to subtract has no default, and a coefficient that would
  turn negative is refused.

**Examples.** `radiative_transfer_inputs.py`, the twenty-seventh: Jerlov
III at 440 nm for OSOAA with Petzold's HAOCE 5, and from 400 to 700 nm for
HydroLight, with the OSOAA command line, written with `--write DIR`. It
runs neither code.

**Data.** DATA.md section 38 (note): the OSOAA files were run by hand in
OSOAA (commit 8e4914f) and its sea profile gives back Jerlov III's c and
b/c at 440 nm; HydroLight was not run.

## 1.13.0 — 2026-11-14

Measured reflectances of ten materials, and reference images
(DECISIONS.md section 85). No shipped value changed; three public names
and one table are added.

**Added.**

- `usgs2017_reflectance(material)`: the absolute reflectance of one of
  ten materials found in and around water, as the USGS Spectral Library
  Version 7 measured it with an ASD spectrometer, every nm from 350 to
  830: white PVC, black ABS, grey concrete, red and blue nylon fabric,
  green tarp, blue-green HDPE, and cadmium orange, cadmium yellow and
  cobalt violet pigments. Returns a `MeasuredReflectance`;
  `USGS2017_MATERIALS` lists the ten.
- `jerlov/data/usgs2017_reflectance.csv`, 4810 values, written by
  `tools/build_usgs2017.py` from the library's data release (DOI
  10.5066/F7RR1WDJ, CC0 1.0), copied as printed in a shorter range.

**Examples.** `reference_images.py`, the twenty-sixth: the ten materials
seen through Jerlov IB, III and 1C at 5 and 15 m depth and out to 10 m,
balanced on the light at depth, written as CSV and images with `--write
DIR`.

**Data.** DATA.md section 37 (note): the ten records, what was changed
(only the range), why these ten, and that the library's HTML sample
descriptions could not be read here.

## 1.12.0 — 2026-11-14

The RGB transmittance as a table, for renderers that read one
(DECISIONS.md section 84). No shipped value changed; two public names
are added.

**Added.**

- `rgb_transmittance(water, distances_m, colour_space=..., illuminant=...)`:
  the transmittance per channel of linear sRGB, ACEScg or Rec. 2020 at
  the distances given, computed from the spectrum with nothing fitted,
  the quantity `rgb_attenuation` fits one exponential to. The colour
  space and the illuminant have no default; for a table by depth, the
  illuminant is the light at each depth. A channel at zero or below at a
  requested distance is refused, with the distance up to which every
  channel stays positive. Returns an `RgbTransmittance`, with `as_dict()`.

**Changed.** `rgb_attenuation` computes its transmittance through the
same private code; its results are bit for bit as in 1.11.1, which a
test checks.

**Examples.** `water_lookup_tables.py` takes its transmittance from
`rgb_transmittance`; its output is unchanged.

## 1.11.1 — 2026-11-14

Three examples for people who render water, and the renderers of
1.11.0's example run (DECISIONS.md section 83). No shipped value
changed, and no name was added or removed; the package's code is as in
1.11.0.

**Examples.**

- `rgb_versus_spectral.py`: five invented surfaces seen through Jerlov
  IB, III and 1C, drawn spectrally and as an RGB renderer draws them with
  `rgb_attenuation`'s coefficients, compared as CIE 1976 colour
  differences, with D65 as white and balanced on the scene's own white.
  `--write DIR` writes the two renderings as an image.
- `water_lookup_tables.py`: the tables a shader reads, the transmittance
  and the path radiance per ACEScg channel of Jerlov III by depth and
  distance, with every choice that fills them stated. `--write DIR`
  writes them as CSV and preview images.
- `phase_function_choice.py`: Henyey-Greenstein against Petzold's eight
  measured phase functions, by scattering angle and in the share of
  light within 1, 10 and 90 degrees of forward, with g matched either
  way.
- `rendering_export.py` says what was run: the pbrt-v4 medium and
  Blender's node values were rendered by hand (below), and it names
  Blender 5.3's Volume Coefficients node.

**Data.** DATA.md section 36: pbrt-v4, built from its repository, and
Blender 5.3.0 (`bpy`), Cycles, render a slab of the example's water with
the transmittance the spectrum gives, Blender's absorption to 7 digits
once Cycles' denoising is off, which otherwise moved the values by about
5 percent.

## 1.11.0 — 2026-11-14

Coefficients for renderers: water for film, games and simulation, in the
forms renderers take (DECISIONS.md section 82). No shipped value changed;
seven public names are added.

**Added.**

- `rgb_attenuation(water, colour_space=..., illuminant=...,
  distance_range_m=...)`: one extinction, absorption and scattering
  coefficient per channel of linear sRGB, ACEScg or Rec. 2020, fitted to
  the colour of the light that has crossed the water, with the largest
  error of the fit over the stated distances. None of the three has a
  default. A channel that falls to zero or below inside the range, as the
  red of linear sRGB does after a few metres of clear water, is refused,
  and the message gives the distance up to which every channel stays
  positive. Returns an `RgbAttenuation`; `RGB_COLOUR_SPACES` names the
  spaces.
- `henyey_greenstein_fit(scattering, method=...)`: the g of a
  Henyey-Greenstein phase function for one of Petzold's stations, matched
  to its measured backscatter ratio or to its mean cosine, with no
  default, and ln(p_HG / p) at Petzold's 55 angles. Returns a
  `HenyeyGreensteinFit`.
- `spectral_coefficients(water, range_nm=...)`: a, b and c at the water's
  own wavelengths, with the status of each value, for spectral renderers.
  Returns a `SpectralCoefficients`.
- `ScatteringFunction.mean_cosine()`: the station's mean cosine. It
  always warns, since the report's extension below 0.1 degree enters it
  at full weight.
- Each new result has `as_dict()`, ready for `json.dump`, with units,
  the colour space or the source, and the fit.

**Examples.** `rendering_export.py`, the twenty-second: the coefficients
of Jerlov III and 1C in the three spaces and what one exponential per
channel costs, the refusal in linear sRGB, g for Petzold's eight stations
both ways, and Jerlov III written as a Mitsuba 3 medium (RGB and
spectral), a pbrt-v4 medium and the values of Blender's volume nodes.

**Data.** DATA.md section 36 (note): the primaries and whites of the
three spaces and where they were read, Petzold's integral taken again
(the printed s to within 0.24 percent), and Mitsuba 3.9.1's spectral
variants giving NaN where a medium's spectrum stops short of 830 nm.

## 1.10.3 — 2026-11-13

The rest of what the review of 1.10.1 found (DECISIONS.md section 81).
No shipped value changed, and no name was added or removed. Some calls
that returned something impossible, or failed with an unhelpful error,
now raise; they are listed under Fixed. No call with finite, possible
inputs gives a different number.

**Fixed.** Infinity is refused where it used to pass. The package's rule
is that NaN marks a gap and infinity is not a value; these did not follow
it, and now raise `ValueError`:

- `Water`, built directly or by `from_measurements`: an infinite a, b, Kd
  or uncertainty. In a `Scene` an infinite c came out as NaN at a distance
  of zero. A negative value still warns and is kept.
- `Scene`, `Scene.at_depth` and `veiling_radiance_estimate`: an infinite
  downwelling irradiance (and `at_depth` a negative one at the surface,
  which it left to `Scene` to refuse). `observe`, `observe_slant` and
  `attenuation_coefficients`: an infinite veiling or water radiance.
- `Observation.contrast`: a background radiance that is negative or
  infinite, or whose shape is neither a number's nor the wavelengths'.
- `kd_spectrum`: an infinite or negative Kd. A Kd below pure sea water's
  still only warns.
- `b_from_c`: an infinite c, and a `bw` or `cw` that is infinite or
  negative.
- `bb_from_vsf`: an infinite beta. `pure_water_vsf`: an angle that is
  NaN, infinite or outside 0-180 degrees.
- `xyz_to_srgb`: an infinite X, Y or Z, which clipping turned into a plain
  colour. `integrate_response`: infinity in the spectrum or the response.
  NaN in a spectrum still gives NaN, and the docstrings now say so.

Five result types can be compared. `Backscattering`,
`AttenuationCoefficients`, `QAAResult`, `RamanCorrection` and
`SurfaceIrradiance` raised NumPy's "truth value of an array is ambiguous"
when two equal results were compared, and could not be hashed. They now
compare field by field, NaN equal to NaN, and hash to match; a result of
plain numbers compares as it did. `QAAResult` and `RamanCorrection` have
a one-line `repr` instead of one printing every array.

Results no longer share arrays with the caller or with each other.
`gregg1990_irradiance`, `qaa_v6` and `qaa_ioccg2006` returned the
caller's own wavelength array; `Observation` and
`AttenuationCoefficients` held the `Scene`'s. They hold copies, and
`Scene.wavelengths` is read-only, since c is evaluated on it once.

A `ParProfile` can be pickled, and so sent to another process.

Exceptions that say what was wrong:

- `gregg1990_irradiance` raised `TypeError` when neither or both of
  `visibility_km` and `aerosol_optical_thickness_550` were given. Neither
  is now a `MissingQuantityError` and both a `ValueError`, as for the two
  ratios of `Water.bb`.
- Text given for a number raised NumPy's `TypeError` in
  `gregg1990_irradiance`, in the chlorophyll of `morel2001_kd`,
  `morel2001_bbp` and `bricaud1995_aph`, and in the `lambda_max` of
  `visual_pigment_template`; it is the `ValueError` those raise for any
  other bad value.
- `tyler1958_radiance` with something that is not a number raises the
  `KeyError` of an unknown depth, not `float`'s error.
- `ScatteringFunction.vsf_at` with a 2-D array of angles says it wants a
  number or a 1-D array, instead of "truth value of an array is
  ambiguous".

**Docs.** DATA.md's table of files gains `gregg1990_table1.csv`, shipped
since 1.10.0 without a row, and its table of statuses the nine values
shipped tables used without one: `transcribed`, `included`,
`excluded_sparse`, `identity`, `second_highest`, `undeclared`,
`not_a_water_type`, `other_definition` and `above_axis`. Tests now hold
both tables to what is shipped, row counts included.

The README shows seven functions of 1.4.0 to 1.8.0 it never mentioned:
`pure_water_absorption_table`, `bricaud1995_aph`, `morel2001_bbp`,
`gordon1989_d0`, `gordon1989_kd`, `lee2011_rrs` and
`lee2013_raman_correction`; its example for the quasi-analytical
algorithm no longer uses one name for a number and an array. A test
checks that every `jerlov.<name>` the README writes exists.

Docstrings that later versions had left behind: `Scene`'s `depth_m`
(used by `observe_slant`), `Observation.veiling` and `contrast` along a
slanted line, the head of the ocean colour module, the `pure_water` of
both QAA functions, and the `KeyError` of `descend` when its source lacks
a type the profile passes through.

**Examples.** `sources_disagree.py` ends with the list of what it assumed,
as the README says every example does; a test now checks it. No number in
any example changed.

**Packaging.** Python 3.14 is tested in CI and declared in the
classifiers. `.gitignore` named `.DS_Store` twice, and the Zenodo
description joined its list of defects with two "and"s.

## 1.10.2 — 2026-11-12

Two fixes from a review of the whole package (DECISIONS.md section 80).
No shipped value changed, and no name was added.

**Fixed.** `Scene.observe_slant` returned a negative path radiance when,
looking up, `radiance_attenuation` times the difference of the depths
exceeded c times the distance: straight up over 5 m in Jerlov IB (c about
0.09 1/m) with K = 0.15 1/m gave, at 450 nm, a veiling of -0.34 times the water's
radiance and a `veiling_fraction` of 1.6, with no warning. Such a K says
the water at the target's depth is brighter than the path could let
through, so the call now raises `ValueError`, naming the wavelengths, as
a negative coefficient is refused. K times the rise equal to c times the
distance is allowed and adds nothing. No call whose result was not
negative changes.

**Packaging.** The source distribution now carries every tracked file. Up
to 1.10.1 it had `tests/*.py` but not `tests/data/`, so three of its test
files failed when run from it, and it had none of `DATA.md`,
`DECISIONS.md`, `CHANGELOG.md`, `tools/` or `examples/`, though the
package's warnings point to the first two. `MANIFEST.in` lists what goes
in, and the publish workflow stops before uploading if a tracked file is
missing from the sdist. The wheel is unchanged.

## 1.10.1 — 2026-11-12

Two new examples, the clear sky against D65 (DECISIONS.md section 77) and
looking up and down (section 78), and a seventh part for the ocean colour
example (section 79). No shipped value changed, and nothing in the API.

**Examples.** `sunlight_and_d65.py` sets the surface irradiance of Gregg
& Carder (1990), for one stated maritime atmosphere and four suns, beside
CIE D65, which twelve of the examples use for the light above the sea.

- The shape: every one of the model's skies is redder than D65 (450 to
  650 nm, 1.20 to 1.29 against 1.46); the colours are computed over
  350-700 nm for both, and the example says how far that moves D65's.
- The level D65 does not have: PAR above the sea, 43 to 454 W m-2.
- Below the surface: the depth of 1 percent PAR moves by up to 2.9 m in
  IB and 0.5 m at most in the coastal types; a white card at depth in III,
  as a camera balanced for D65 records it, changes by up to 7 percent in
  its blue channel.
- Through Gordon's (1989) D0, Jerlov II's Kd(490) spans 17 percent
  between the sun overhead and 60 degrees from it under this sky. Jerlov's
  tables do not record their sun; the example says the 30 degrees it
  starts from is an assumption.

`looking_up_and_down.py` (DECISIONS.md section 78) sees a black target
from 41.3 m in Lake Pend Oreille along five lines, straight up to straight
down, with `Scene.observe_slant` and the water's radiance and K from
Tyler's (1958) measured radiance distribution in that lake.

- Over about 12 m, looking up leaves 7.0 times the contrast of a
  horizontal line, and looking down 1/7.5 of it.
- The distance at which the contrast falls to 2 percent: 16.4 m up, 9.9 m
  across, 7.0 m down.
- Tyler's K differs by direction by a factor of 2.0 near the surface and
  agrees within 12 percent from 16.6 to 53.7 m, Duntley's asymptotic light
  field.
- Duntley's eq. (12) as printed would make the open water read 46 times
  what Tyler measured; the corrected form reads it exactly.

`ocean_colour_and_secchi.py` gains a seventh part (DECISIONS.md section
79), using two relations no example used:

- Lee et al.'s (2011) reflectance at its seven printed geometries: off
  nadir up to 8 percent above nadir, and nadir up to 14 percent from
  Gordon et al.'s (1988), within the range of bb/(a + bb) the
  coefficients were fitted to. Jerlov III at 412-488 nm lies outside it
  (9 and 21 percent there); the example reports the warning.
- Lee et al.'s (2013) Raman correction: the Raman part a measured
  reflectance of these waters would carry, 2 to 11 percent of the elastic
  part, the most at 667 nm in IB.
- The Secchi depth moves by at most 2.4 percent between the two
  reflectance models.

**Docs.** README, `examples/README.md` and the site's examples page list
both; there are now twenty-one examples.

## 1.10.0 — 2026-11-12

The clear-sky irradiance at the sea surface, after Gregg and Carder
(1990) (DECISIONS.md section 76). No shipped value changed; two public
names are added.

**Added.**

- `gregg1990_irradiance(wavelength_nm, sun_zenith_deg=..., day_of_year=...,
  pressure_hpa=..., air_mass_type=..., relative_humidity=...,
  precipitable_water_cm=..., wind_speed_24h=..., wind_speed=...,
  ozone_du=..., visibility_km=... or aerosol_optical_thickness_550=...)`:
  the direct and diffuse downwelling irradiance just above and just below
  the sea surface under a cloudless sky, W m-2 nm-1, at whole nm from 350
  to 700. No input has a default. Returns a `SurfaceIrradiance`.
- `jerlov/data/gregg1990_table1.csv`: the paper's Table 1, the sun's
  spectrum and the ozone, water vapour and oxygen absorption, 351 rows,
  transcribed from the page images by `tools/build_gregg1990.py`.

**Data.** DATA.md section 35 (confirmed): eq. (44) prints a second 1/2
inside Fresnel's law; the package uses Fresnel's law. The model
reproduces the diffuse shares of Table 5 to the printed percent and the
direct-to-diffuse splits of Table 4.

## 1.9.0 — 2026-11-12

A slanted line of sight for `Scene`, after Duntley (1963) (DECISIONS.md
section 75). No shipped value changed and no top-level name is added.

**Added.**

- `Scene.observe_slant(reflectance, distance_m, target_depth_m=...,
  kd=..., water_radiance=..., radiance_attenuation=...,
  face_irradiance_ratio=...)`: a target above or below the observer in
  uniform water. The direct light falls as exp(-c r) and the path
  radiance is Nw (1 - exp[-c r - K (zt - z)]), Duntley's eq. (12) with
  its sign corrected. The observer is at the scene's `depth_m`; the
  target is lit by Kd from there. The water's radiance along the line
  of sight and its K have no default. A horizontal line gives `observe`
  exactly, and `Observation.contrast` gives eqs. (13)-(15).

**Data.** DATA.md section 34 (confirmed): eq. (12) prints the wrong sign
in front of the path radiance; the corrected form is the one the paper's
own eqs. (9), (14) and (15) need.

## 1.8.0 — 2026-11-12

The downwelling distribution function D0, and Kd under another light
field (DECISIONS.md section 74). No shipped value changed; two public
names are added.

**Added.**

- `gordon1989_d0(sun_zenith_deg, direct_fraction=...)`: Gordon's (1989)
  eq. (12), D0 = f / cos(theta_w) + 1.197 (1 - f), for a sky of uniform
  radiance, the sun refracted with n = 1.333. f, the share of direct
  sunlight, has no default. Above 60 degrees it warns: the paper finds
  the equation 5-8 percent low at 80.
- `gordon1989_kd(kd, d0_from=..., d0_to=...)`: kd * d0_to / d0_from, on
  the strength of Kd/D0 being nearly independent of the light field.
  Both D0 are the caller's: Jerlov's tables do not record the conditions
  of their Kd.

**Data.** DATA.md section 33: no refractive index reproduces all seven
rows of Gordon's Table 3 secant column; 1.333 reproduces six, and the
40 degree row is the one no index fits.

## 1.7.0 — 2026-11-12

The remote sensing reflectance with molecular and particle backscattering
kept apart, for seven viewing geometries (DECISIONS.md section 73). No
shipped value changed; two public names are added.

**Added.**

- `lee2011_rrs(a, bb, bb_water=..., coefficients=...)`: eq. (14) of Lee
  et al. (2011), Rrs above the surface from the water's and the
  particles' shares of bb, each with its own coefficients.
- `LEE2011_RRS_COEFFICIENTS`: the seven sets of (G0w, G1w, G0p, G1p) their
  Table 2 prints, by sun zenith, viewing zenith and relative azimuth,
  among them straight down with the sun overhead, the set Lee et al.
  (2013) quote. The paper derived many more geometries but prints only
  these; no interpolation is done.
- Outside the bb/(a + bb) of the data the coefficients were fitted to,
  0.0002-0.37, it warns.

**Data.** DATA.md section 32.

## 1.6.0 — 2026-11-12

From chlorophyll to absorption by phytoplankton and backscattering by
particles, for case 1 water (DECISIONS.md section 72). No shipped value
changed; one table and two public names are added.

**Added.**

- `bricaud1995_aph(wavelengths, chlorophyll_mg_m3=...)`: aph = A [Chl]^(1 -
  B), with A and B from Table 2 of Bricaud et al. (1995), every 2 nm from
  400 to 700 nm. Outside the 0.02-25 mg m-3 of their data it warns.
- `morel2001_bbp(wavelengths, chlorophyll_mg_m3=...)`: Morel & Maritorena's
  (2001) particle backscattering, eqs. (13), (14) and (9), 350-700 nm.
  Their eq. (10) is the 1988 form, which the paper itself modifies into
  (13) and (14); the package follows the modified form.
- `bricaud1995_aph.csv`, transcribed by `tools/build_bricaud1995.py` and
  checked against the paper's text.

**Data.** DATA.md section 31. Bricaud et al. (1995) is a scan; all 456
numbers of Table 2 were read from the page images. Bricaud et al. (1998)
prints its spectral coefficients only as a figure and is not used for
them.

**Examples.** `ocean_colour_and_secchi.py` gains a sixth part: a and bb
built from chlorophyll alone, with stated choices for nonalgal particles,
CDOM and pure water, and the Kd they give (Lee et al. 2013) against Morel
& Maritorena's. For 1, 3 and 10 mg m-3 it is below theirs at 440, 490 and
555 nm whatever the share of CDOM.

**Docs.** `tools/README.md` counts fourteen scripts that read no file.

## 1.5.0 — 2026-11-12

Removing Raman scattering from a measured reflectance (DECISIONS.md
section 71). No shipped value changed; two public names are added.

**Added.**

- `lee2013_raman_correction(wavelengths, rrs, bands=...)`: the empirical
  correction of Lee et al. (2013), eqs. (11)-(13). From Rrs as measured,
  Raman scattering included, it gives the Raman factor RF and the
  corrected Rrs, Rrs_T / (1 + RF), which is what the package's forward
  relations and both QAA versions describe. `bands` names the wavelengths
  playing 440 and 550 nm and has no default.
- `RamanCorrection`: the wavelengths, RF and the corrected Rrs.
- The coefficients are Table 2's, at the six MODIS bands 412-667 nm. RF is
  interpolated linearly between them, as the paper does; outside, the
  function refuses. The paper's own extension of RF to 350 nm, and its RF
  of 0 below 400 nm, are described in the docstring but not applied.

**Data.** DATA.md section 30: Table 2's minus signs are missing from the
PDF's text and were read from the page image.

## 1.4.0 — 2026-11-12

bb from the particles' backscattering ratio, and four published spectra
of the absorption of pure water (DECISIONS.md sections 68 to 70). No
shipped value changed; four tables and one public name are added, and
`backscatter_ratio` means what it did.

**Added.**

- `Water.bb(wl, particle_backscatter_ratio=r)`: r is bbp/bp, the
  particles' ratio, and bb is 0.5 b_w + r (b - b_w), with b_w the pure
  water term of the source's own scattering model (Haltrin 1999, as
  Williamson & Hollins 2022 and Solonenko & Mobley 2015 print it). The
  existing `backscatter_ratio` applies its ratio to the whole b, pure
  water included, which in clear water can give a bb below what the
  water alone backscatters: for Solonenko & Mobley's type IB at 450 nm,
  0.0183 gives 1.24e-3 1/m against the water's 1.75e-3, and the new
  keyword 2.93e-3. Published ratios,
  such as Petzold's average particle's 0.0183, are mostly the particles'.
- Exactly one of the two ratios must be given. A `Water` made from
  measurements has no scattering model to say which b_w its b contains,
  and the new keyword refuses it with `MissingQuantityError`.
- `veiling_radiance_estimate(..., particle_backscatter_ratio=r)`, passed
  to `Water.bb` (DECISIONS.md section 69). Calling it with neither ratio
  raised `TypeError` and now raises `MissingQuantityError`.

- `pure_water_absorption_table(wavelengths, source=...)`: a published
  absorption spectrum of pure water, for wherever one must be supplied,
  such as the `pure_water` of `qaa_v6` and `qaa_ioccg2006`. `source` has
  no default and is one of `pope1997` (Pope & Fry 1997, 380-727.5 nm, the
  aw of IOCCG Report 5), `smith1981` (Smith & Baker 1981, 200-800 nm),
  `mason2016` (Mason, Cone & Fry 2016, 250-550 nm), `lee2015` (Lee et
  al. 2015, "pure" seawater inverted from reflectance, 350-550 nm) and
  `lee2015_smoothed` (the same with the paper's smoothed values).
  `pure_water_absorption` is unchanged: it still returns the aw a Jerlov
  source built its a on.

**Data.** DATA.md section 29. Each table was checked against its paper
before it was written: Pope & Fry's percent errors follow from their
standard deviations, Smith & Baker's Eq. (6) holds in every row but one,
Mason et al.'s minimum is the one their abstract gives, and Lee et al.'s
smoothed values are the averages they describe. The exception is
confirmed: at 710 nm Smith & Baker print an aw of 0.839 1/m above a K of
0.834, which their Eq. (6) does not allow. It is kept as printed, marked
`suspect`, and warns. The aw of the IOCCG synthetic data set is Pope &
Fry's at all 31 of its wavelengths.

**Docs.** README's "Supply bb" names both ratios. `tools/README.md`
counts thirteen scripts that read no file.

## 1.3.0 — 2026-11-11

The inverse of 1.2.0's reflectance: the quasi-analytical algorithm, from
Rrs to a and bb (DECISIONS.md section 67). No shipped value changed; three
public names are added.

**Added.**

- `qaa_v6(wavelengths, rrs, bands=..., pure_water=...)`: QAA_v6 as the
  spreadsheet its author distributes through the IOCCG computes it. It
  reproduces the results the spreadsheet stored for its 12 example
  stations to a relative 1e-12.
- `qaa_ioccg2006(wavelengths, rrs, bands=..., pure_water=...)`: the
  version IOCCG Report 5 (2006), chapter 10, describes and tested. On the
  report's synthetic data it reproduces Table 10.1's RMSE and bias for a
  at 410, 440 and 490 nm and bbp at 440 and 555 nm to within 0.002.
- `QAAResult`: a, bbp, adg and aph at the wavelengths given, the exponent
  of bbp, and the reference wavelength each spectrum used.
- The bands that play each role, and pure water's aw and bbw, are the
  caller's: neither has a default.

**Data.** DATA.md section 28: the v6 document's table of steps, its text
and its spreadsheet give three different g0 and three different
wavelength spans for xi; the package follows the spreadsheet. Part of the
IOCCG synthetic data set, cited as Report 5, and the spreadsheet's stored
results are in `tests/data/` for the tests, written by
`tools/qaa_test_data.py`; they are not in the wheel.

**Examples.** `ocean_colour_and_secchi.py` gains a fifth part: Rrs from
known a and bb, inverted again by both versions, and the a they recover
set against the a it started from.

**Docs.** `tools/README.md` counted eleven scripts that read no file;
since 1.2.0 there are twelve.

## 1.2.0 — 2026-11-11

Ways in that do not start from a Jerlov type, the colour of the sea from
above, and the Secchi depth (DECISIONS.md section 66). No shipped value
changed; one table and eight public names are added.

**Added.**

- `morel2001_kd(wavelengths, chlorophyll_mg_m3=...)`: Kd of case 1 water
  from its chlorophyll, Kd = Kw + chi [Chl]^e, Morel & Maritorena (2001)
  Table 2, 350-700 nm, shipped as `morel2001_kd.csv`. Below 400 nm the
  values are Morel & Antoine's (1994) extrapolation and warn; so does a
  chlorophyll outside the 0.02-30 mg m^-3 of the data.
- `lee2005_kd(a, bb, sun_zenith_deg=...)` and `lee2013_kd(a, bb,
  bb_water=..., sun_zenith_deg=...)`: Kd from the absorption and
  backscattering coefficients and the sun, Lee et al. (2005) eq. (11) and
  Lee et al. (2013) eq. (5). A sun, or a Kd, outside what each was fitted
  to warns.
- `subsurface_rrs(a, bb, coefficients=...)`, with
  `GORDON1988_RRS_COEFFICIENTS` and `LEE2002_RRS_COEFFICIENTS`, and
  `above_surface_rrs(rrs)`: the remote sensing reflectance from a and bb,
  Gordon et al. (1988) eq. (2) and Lee et al. (2002) eqs. (1) and (8), for
  optically deep water seen from straight above.
- `lee2015_secchi_depth(wavelengths, kd, rrs)`: the Secchi depth by Lee
  et al.'s (2015) eq. (33), from the smallest Kd in the visible and the
  reflectance there; a depth outside the 0.1-30 m of their check warns.
- None of the new arguments has a default: chlorophyll, the sun, pure
  water's backscattering and the coefficients are the caller's.

**Changed.** Remote sensing reflectance was out of scope (DECISIONS.md
section 12); the forward relations are now in, on the test of section 19,
that their provenance can be traced and checked. The inverse, from Rrs to
a and bb, is planned for the next release. Reading satellite files and
atmospheric correction stay out.

**Data.** DATA.md section 27 records the sources and two notes: Table 2's
Kw at 380 nm is not the Pope & Fry value the text gives, and the 0.14 in
Lee et al.'s eq. (33) is less than the 0.146 its own figures give.

**Examples.** `ocean_colour_and_secchi.py` checks Lee et al.'s Kd against
the Kd Solonenko & Mobley computed with Hydrolight from the same a and b,
computes the reflectance and the Secchi depth for Jerlov IB, II, III and
1C and says which orderings hold whatever the backscatter ratio, sets the
model beside Poole & Atkins's 1.7, and finds the Jerlov type nearest to
Morel & Maritorena's Kd for six chlorophyll concentrations. Nineteen
examples now.

## 1.1.1 — 2026-11-05

A new example on fish vision, built on what 1.1.0 added (DECISIONS.md
section 65). No shipped value changed, and nothing in the API.

**Examples.** `fish_colour_differences.py` follows the difference between
two colours as the cones of *Dicentrarchus labrax* count it, by the receptor-noise model of Vorobyev & Osorio (1998), along a
horizontal path at 5 m in Jerlov II, III and 1C.

- The cones are the peaks Brill et al. (2019), PLOS ONE 14(6), e0214347,
  fitted to the whole eye's ERG (Table 4, p. 12), in the template they
  were fitted with; the values are quoted in the script, not shipped.
- It shows how fast the difference shrinks for three pairs of painted
  surfaces, one of which only the short-wave cone can tell apart, and
  calls an ordering a finding only if all 32 variants give it: the
  published peaks, the other template's peaks, each peak moved 15 nm
  either way, and one cone at a time twice as noisy. In this release every
  ordering it reports holds in all of them.
- The backscatter ratio and the light on the faces cancel from what it
  reports, and a test checks that they do.
- It says nothing about what a fish notices or at what distance. Turbid
  water is not covered: Jerlov's Kd for 7C and 9C has no values below
  350 nm, where the short-wave cone needs them.

**Docs.** README, `examples/README.md` and the site's examples page list
it; there are now eighteen examples.

## 1.1.0 — 2026-11-04

Visual pigments and receptor noise, the core of what pavo offers for colour
vision, each from its primary paper and with what belongs to a species left
to the caller (DECISIONS.md section 64). No shipped value changed.

**Added.**

- `visual_pigment_template(wavelengths, lambda_max=..., chromophore=...)`:
  the absorbance of a visual pigment, alpha- and beta-bands, by the A1 and
  A2 templates of Govardovskii et al. (2000), Visual Neuroscience 17,
  509-528. Neither the peak nor the chromophore has a default. Wavelengths
  at or below 330 nm and peaks at or below 350 nm, outside the range the
  paper made the templates for, are refused; a peak outside the range of
  the pigments the paper measured warns. A2's beta-band amplitude has no
  equation in the paper, and the 0.37 the authors fixed it at is used.
- `receptor_noise_distance(catches_a, catches_b, noise=...)`: the distance
  between two colours in units of receptor noise, by the model of
  Vorobyev & Osorio (1998), Proc. R. Soc. Lond. B 265, 351-358, for any
  number of receptor types, from quantum catches scaled to the background.
  The noise has no default. The model is the paper's, linear in the
  catches; the logarithmic form of later work is not included.

**Docs.**

- DATA.md section 26 records every constant with the page it was read
  from, and a confirmed misprint: Vorobyev & Osorio's eq. (4), for three
  receptor types, lacks a Delta in its last term. The package computes the
  general form the paper derives its equations from, which agrees with
  eqs. (3) and (5) as printed and with eq. (4) corrected.
- README has a section on the two functions, the API reference lists
  them, and the Zenodo record cites both papers.

## 1.0.1 — 2026-10-29

A documentation site, https://tishibashi-cpu.github.io/jerlov/, with three
guides and a reference of the whole API (DECISIONS.md section 63). No
shipped value changed, and nothing in the API.

**Docs.**

- The site is built from `docs/` with Sphinx and published to GitHub Pages
  from `main` by a new workflow, `docs.yml`, which also builds it on every
  pull request and fails on any warning.
- Three guides, each for one question: the colour of the light at depth,
  the euphotic zone against Jerlov's measurements, and how colours turn
  towards the water's own light along a horizontal path. Every number they
  print is computed by the package when `tests/test_docs.py` runs them.
- The API reference has an entry for each name in `jerlov.__all__`, built
  from the docstrings; a test checks that it covers `__all__` exactly.
- An About page, on why the package was started and how to report a wrong
  number.
- Three docstrings did not render, and are mended without changing their
  text: those of `Water.from_measurements` and `ParProfile.scalar_par`,
  whose closing paragraphs were read as part of their parameters, and that
  of `ScatteringConstants`, whose formula became a list. Four
  cross-references named a module path, `jerlov.water.Water` and the like,
  and now name the type as `jerlov` exports it.
- README and CONTRIBUTING.md point to the site; CONTRIBUTING.md says how to
  build it.

**Packaging.** `pyproject.toml` lists the documentation, source, changelog
and issues, which PyPI shows beside the description.

## 1.0.0 — 2026-10-29

From this release the way the package is used does not break until 2.0.
No shipped value changed (DECISIONS.md section 62).

**What 1.0 promises.** The rules are under "Compatibility" in
CONTRIBUTING.md, and DECISIONS.md section 61 says why each is as it is.

- What is promised: the names in `jerlov.__all__`, imported from `jerlov`
  itself (not from its modules); reading the attributes of what the
  functions return; the arguments, their defaults, each function's default
  source, and the exceptions raised.
- Correcting a shipped value or its status that is wrong against its
  source is not a breaking change. It goes in a minor release, and the
  release's entry here says so at the top.
- No default is added to an argument that has none.
- Nothing public is removed or renamed before 2.0. An old name or way of
  calling keeps working with a `FutureWarning`.

**Changed.** `pure_water_vsf`, `pure_water_backscattering`,
`pure_water_scattering` and `bb_from_vsf` raise `MissingQuantityError` when
`salinity_psu` is left out. 0.24.0 warned and used 37; pass
`salinity_psu=37.0` to keep that result. Pure sea water at 37 scatters 30
percent more than fresh water, so the package does not choose.

**Kept.** The other ways of calling that 0.24.0 replaced still work, with a
`FutureWarning`, until 2.0: a wavelength or spectrum passed by keyword, a
salinity passed by position, and `gernez2009_cv_by_sun_zenith()`.

**Packaging.** The classifier is "Development Status :: 5 -
Production/Stable", for the interface; the doubts about the data stay in
DATA.md and in the flags.

## 0.24.0 — 2026-10-29

The last changes before 1.0, so that what 1.0 promises is worth keeping
(DECISIONS.md section 61). No shipped value changed. Every old way of
calling that this release changes still works, with a `FutureWarning`
that says what to write instead; leaving out the salinity becomes an
error in 1.0, and the rest stop working in 2.0.

**Changed.**

- `pure_water_vsf`, `pure_water_backscattering`, `pure_water_scattering`
  and `bb_from_vsf` defaulted to a salinity of 37 with no reason given,
  though pure sea water at 37 scatters 30 percent more than fresh water.
  Leaving `salinity_psu` out now warns and still uses 37; from 1.0 it
  raises `MissingQuantityError`. It is keyword-only in all four; passing
  it by position warns.
- The wavelength and spectrum arguments are positional-only, with the
  arguments before them: `Water(...)`, `Water.from_measurements`, the
  wavelength queries of `Water` (`a`, `b`, `c`, `kd`, `kd_hydrolight`,
  `bb`, `uncertainty`), `pure_water_absorption`, the four functions
  above, `b_from_c`, `kd_spectrum`, `spectrum_to_xyz`, `spectrum_to_srgb`,
  `integrate_response`, `Scene(...)`, `Scene.at_depth`,
  `veiling_radiance_estimate`, `descend`, `par_profile` and
  `classify_kd`. Their names differed (`wavelengths`, `wl`,
  `wavelength_nm`, `at`), and positional-only takes them out of what 1.0
  promises. Passing one by keyword warns and gives the same answer.
- `gernez2009_cv_by`, `gernez2009_band_cv` and `gernez2009_spectral_cv`
  raise `ValueError`, not `KeyError`, for an unknown `variable`, `sky` or
  `irradiance`. The rule is now one for the whole package: `KeyError` for
  an unknown record (a water type, a source, a station, a panel, a
  depth), `ValueError` for an option outside its set.
- `gernez2009_cv_by("sun_zenith_deg")` returns Gernez & Antoine's Figure
  8a, the same values as `gernez2009_cv_by_sun_zenith()`, as a
  `ConditionFluctuation` like the other panels, and
  `GERNEZ2009_PLOTS[("clear", "Ed")]` lists it first.
  `gernez2009_cv_by_sun_zenith()` warns that it is replaced.

**Added.** `HALTRIN1999` and its type `ScatteringConstants`, the type of
`Source.scattering`, are exported. An example had imported them from
`jerlov.sources`.

**Examples.** `radiance_distribution.py`, `painted_sphere.py` and
`wave_focusing.py` pass the salinity of 37 they had taken from the
default, and list it under "Before you use any of this". The examples
call in the new way, so they raise no `FutureWarning`; their numbers are
unchanged.

**Docs.** CONTRIBUTING.md has a section on compatibility: what 1.0
promises (the names in `jerlov.__all__`, imported from `jerlov`; reading
what the functions return; the arguments, defaults and exceptions), that
correcting a shipped value is not a breaking change, that no default is
added where there is none, and that nothing public is removed or renamed
before 2.0. README points to it, and its calls are in the new form.

## 0.23.0 — 2026-10-28

Fixes from a review of the whole package: values that were silently
wrong, inputs that should have been refused, and errors that did not say
what was wrong. No shipped value changed (DECISIONS.md section 60).

**Fixed.**

- `pure_water_backscattering`, `pure_water_scattering` and `bb_from_vsf`
  returned the first salinity's value alone when `salinity_psu` was an
  array and the wavelength a number. They now broadcast every argument,
  as `pure_water_vsf` did, and return a float only when each was a single
  number.
- `Scene.at_depth` used a negative Kd as given, so the light grew with
  depth. It now refuses a negative or infinite Kd, from an array or a
  `Water`, as `par_profile` always has, and an infinite `depth_m`, which
  with a Kd of 0 gave NaN.
- `Water(...)` accepted any string as a status in `flags`, so a misspelt
  one never warned. It now refuses an unknown status, as
  `Water.from_measurements` does.
- `kd_spectrum` failed with a 2-D `at`, and would not have given the
  promised shape `kd.shape + at.shape` with an array `kd`. Both work now.
- `spectrum_to_srgb` returned NaN without a word for a white with a gap.
  It now raises.
- `integrate_response` reported a response sampled at one wavelength as
  fully covered and returned zero. It now needs two response
  wavelengths, and finite wavelengths on both grids.
- `Scene.transmittance`, `Water.bb` and the wavelength queries of `Water`
  raised NumPy's "truth value of an array is ambiguous" for an array
  where one number, or a 1-D array, is taken. They now say what they
  take.

**Changed.** A `Water` with a negative a, b or Kd, which as totals with
pure water included none can be, raises a `ProvenanceWarning` when it is
built and keeps the values as given. A calculation that would rest on
them refuses: `Scene` and `veiling_radiance_estimate` for a negative c or
bb, `Scene.at_depth` and `par_profile` for a negative Kd, at the
wavelengths each uses.

**Docs.** DATA.md's table of statuses lists `model`, `jerlov_original`
and `pure_seawater`, which the shipped Kd of Austin & Petzold (1986) has
always carried. They do not warn.

## 0.22.0 — 2026-10-25

Scalar PAR, from a mean cosine and a reflectance the caller gives, and the
IB result checked against a second instrument from the same cruise. No
shipped value changed.

**Added.** `ParProfile.scalar_par(mean_cosine=..., reflectance=...)`
returns PAR on scalar irradiance, what a spherical sensor reads, at each
depth, from E0 = Ed (1 - R) / mu: the definition of the mean cosine
(Ed - Eu) / E0 rearranged, with R = Eu / Ed. Neither has a default, since
both depend on the light field, which the package does not model;
`reflectance=0` leaves out the upwelling light as a stated choice. Each
is a number or one value per depth, and nothing is interpolated between
depths. A pair with mu above (1 - R) / (1 + R), which would make E0 less
than Ed + Eu, describes no light field and is refused (DECISIONS.md
section 59).

**Docs.** DECISIONS.md section 58 and DATA.md section 22: Morel's quanta
profiles from the Discoverer expedition of 1970, read from the data report
(SIO Ref. 73-16, vol. I, section F), agree with Nygård's. Where the 10
percent level is IB-like, z(1) / z(10) has a median of 2.14, and 2.08 to
2.17 over the range of surface corrections tried, against 2.12 in Jerlov
(1977) and 2.49 in the package. A comparison with the chlorophyll measured
at the same stations decides nothing by its own rule: it needed a station
that has no sample in its shallowest layer. The transcriptions and
analyses are in `tools/` and are not shipped.

## 0.21.0 — 2026-10-25

A measured Kd's uncertainty carried through to PAR and to the nearest
type, and the cause of the package's IB result looked for in the data of
the cruise behind it. No shipped value changed.

**Added.** `par_profile` takes the standard uncertainty of Kd from a
`Water` built with `uncertainty={"kd": ...}`, or as `kd_uncertainty=`
beside an array `kd`. `ParProfile.depth_of_fraction_bounds(fraction, k=1)`
and `ParProfile.par_bounds(k=1)` repeat the calculation exactly with Kd
plus and minus k uncertainties at every wavelength together: the widest
range that errors within k uncertainties can give, and plus and minus k
standard deviations if the errors are fully correlated and normal.
`classify_kd(..., uncertainty=..., k=1)` lists in
`nearest_within_uncertainty` every type that comes out nearest within
that shift. The published types and `descend` carry no uncertainty and
give no range; a Kd minus k uncertainties below zero is refused, not
clipped (DECISIONS.md section 57).

**Docs.** Why the package puts Jerlov IB's 1 percent level of quanta at
93 m against the 70 m of Jerlov (1977), DECISIONS.md sections 53 to 56
and DATA.md section 22:

- Neither the sky's spectrum nor the meter's response explains it, and
  neither does the Kd table: every set of spectral Kd for IB in the
  package, Austin & Petzold's included, gives 93 to 104 m.
- Nygård's measured profiles from the Discoverer expedition of 1970,
  transcribed from the data report (SIO Ref. 73-16), lose their light
  below the 10 percent level at least as fast as the 1977 table says:
  z(1) / z(10)
  has a median of 1.95 where the 10 percent level is IB-like, against
  2.12 in the table and 2.49 in the package.
- Smith's spectra at the same stations show the blue light's Kd rising
  with depth at two of three of them.

The measurements point to water that grew more turbid with depth, which
a Kd that does not change with depth cannot describe. The transcriptions
and analyses are in `tools/` and are not shipped.

## 0.20.0 — 2026-10-24

An attenuation coefficient from a Secchi depth, by a rule the caller names.
No shipped value changed.

**Added.** `k_from_secchi(secchi_depth_m, coefficient=...)` returns
coefficient / Secchi depth, in 1/m. The coefficient has no default.
`POOLE1929_SECCHI_COEFFICIENT` is 1.7, the rule of Poole & Atkins (1929):
the mean of K times the Secchi depth over their 14 comparisons off
Plymouth in 1928, which ran from 1.32 to 2.18. Their K is the attenuation
from 0 to 20 m of the light on a horizontal surface, measured with
potassium photocells, so it is not a spectral Kd or Kd(PAR). Every call
raises a `ProvenanceWarning` that gives this range and the authors' own
words, "a very rough rule" (DECISIONS.md section 52).

**Examples.** `seagrass_depth_limit.py` has a fifth part, for when all you
have is a Secchi depth. Duarte (1991) and Duarte et al. (2007) used K =
1.7 / Secchi depth where a report gave no attenuation coefficient. With
that rule the 11 percent depth is 1.30 Secchi depths in any water, and
anywhere from 1.01 to 1.67 across Poole & Atkins's range.

**Fixed.** The example's docstring said most of both Duarte papers'
attenuation coefficients came from Secchi depths. Duarte (1991) does not
say how many of his did; the docstring now says what each paper says.

## 0.19.2 — 2026-10-24

**Packaging.** The release workflow now makes the GitHub Release itself,
with the version's section of CHANGELOG.md as its text, and only after
PyPI has the version (DECISIONS.md section 51). Zenodo archives the
Release, so a version can no longer reach Zenodo without reaching PyPI, as
0.19.0 did. The workflow is run from the Actions tab on main, takes the
version from `pyproject.toml` and makes the tag; pushing a tag still runs
it, and a Release that already exists is left as it is.
`tools/release_notes.py` prints the text, and a version without a section
in CHANGELOG.md stops the run before anything is uploaded. Nothing in the
package, the data or the examples changed.

## 0.19.1 — 2026-10-24

**Packaging.** 0.19.0 did not reach PyPI. The release workflow runs the
tests against the installed wheel, from a copy of `tests/` away from the
source tree, where the tests that need the examples are skipped. Two tests
added in 0.19.0 for `wave_focusing.py`'s sky needed the example but were
not marked as needing the source tree, so they failed there and the
upload never ran. They are marked now. CI's test job now also runs the
tests from such a copy on every push, so that this is found before a tag
rather than at it. Nothing in the package, the data or the examples
changed from 0.19.0; its tag stays, and it is not on PyPI.

## 0.19.0 — 2026-10-24

The rest of Gernez & Antoine's (2009) figures that carry measurements, and
the sky's light in `wave_focusing.py`. No shipped value changed; four data
files are added.

**Added.**

- `gernez2009_cv_by(variable, sky=..., irradiance=...)`: besides the clear
  sky and Ed of Figure 8, the overcast subset (Figure 7) and the upwelling
  irradiance Eu under clear skies (Figure 13), each against the sun's
  zenith angle, the wave height, the wind speed and Kd(490).
  `GERNEZ2009_PLOTS` gives the variables for each. `ConditionFluctuation`
  carries the figure and the irradiance.
- `gernez2009_spectral_cv(irradiance)`: the average CV and period of the
  strongest fluctuation at 412 to 683 nm under clear and overcast skies, of
  Ed at the upper depth (Figure 11) or Eu at the lower, 8 to 8.7 m (Figure
  14), as a `SkySpectralFluctuation`.
- `gernez2009_band_cv(variable)`: the median CV of Ed at 443 to 683 nm,
  clear skies, against the sun's zenith angle, the wave height, the wind
  speed or Kd(490) (Figure 10), as a `BandConditionFluctuation`; its 510
  nm line is Figure 8's medians to within 0.2 percent. The periods, drawn
  in the same colours and crossing the CV lines, are not read.
- `gernez2009_diffuse_share()`: the share of diffuse light above the water
  that the paper prints along the top of Figures 8a and 10a, from 21
  percent with the sun at 20 degrees to 100 at the horizon. It comes from
  a model of the sky (Gregg and Carder, 1990), not a measurement.

**Examples.** `wave_focusing.py` adds the sky's light (DECISIONS.md
section 48, written before the run): its share above the sea from the
clear-sky model of Gregg and Carder (1990), checked against the shares
Gernez and Antoine print, for eight atmospheres since Darecki did not
record one, and its light under the waves taken as uniform. Every
atmosphere passes section 44's checks. Below 2.84 m measured / model,
0.54-0.77 without a sky, becomes 0.64-0.88 with the smallest share and
0.86-1.20 with the largest, which lowers the model too far near the
surface (1.16-1.87 down to 2.84 m): the sky accounts for part of the
shortfall, and no one uniform sky fits every depth. Section 45's model
without a sky is printed as before.

**CI.** The examples run in a job of their own, beside the tests rather
than after them, on the same versions and with the same commands
(DECISIONS.md section 49): every check still runs, and a run should take
about 8 minutes rather than 11. A test checks that the two jobs cover the
same versions.

**Docs.** DATA.md section 25: how they were read, and where the text and
the figures differ. Figure 14's text gives its two Tmax curves the
opposite skies from the figure's own labels and caption; the values follow
the figure. Figure 8's caption calls the top axis the ratio of direct to
total light; the axis label, Ediffuse / Etotal, and the numbers say
diffuse.

## 0.18.2 — 2026-10-23

**Packaging.** CI ran `wave_focusing.py` twice in every job, once in the
loop over the examples and once in the test that recomputes its quoted
numbers, which took each job from about six minutes to about fifteen. The
loop now skips it, and the test runs it with `ProvenanceWarning` an error,
as the loop does (DECISIONS.md section 47). Nothing in the package or the
examples changed.

## 0.18.1 — 2026-10-23

**Examples.** `wave_focusing.py --png` draws the light shafts seen looking
up towards the sun from 6 m at 532 nm: the unscattered sunbeam under the
5.5 m/s sea, scattered once towards the eye by Petzold's volume scattering
function, beside the same under a flat surface and the one divided by
the other, where the shafts spread from the sun across the whole field.
No value printed without `--png` changed.

**Docs.** DECISIONS.md section 46.

## 0.18.0 — 2026-10-23

A model of the flicker under waves, as an example, checked against the
measurement the package carries. No shipped value changed.

**Examples.** `wave_focusing.py`, for anyone working with the light just
below a sunlit sea. It draws a random sea surface from the wave spectrum
of Elfouhaily et al. (1997), with the friction velocity from Wu (1982),
traces the refracted sunbeam down to Darecki et al.'s (2011) six depths,
blurs it by the sun's disc and their 2.5 mm collector, and compares the
coefficient of variation with `darecki2011_irradiance_cv()`, using the
water You et al. (2010) measured on the same day. The surface's mean
square slope agrees with Cox and Munk (1954). The checks were written
down before the run (DECISIONS.md section 44). With the scattered light
spread evenly, the measurement is 1.5 to 2.7 times the model down to
2.84 m, and the third check fails. Looking for the cause (section 45):
light scattered on its way down still carries the pattern, shifted, and
with that the model passes all three checks, the measurement 0.69 to
1.24 times it down to 2.84 m and 0.54 to 0.77 below, where the model
leaves out the sky. Petzold's NUC 2240 phase function brings the deeper
values to 0.78 to 0.97; a smaller square or a coarser grid moves the
result by 5 percent at most. Takes about ten minutes.

**Docs.** DECISIONS.md sections 44 and 45.

## 0.17.0 — 2026-10-21

The rest of the two fluctuation studies' figures. No shipped value
changed; two data files are added.

**Added.**

- `darecki2011_spectral_cv()`: the coefficient of variation of the
  downwelling irradiance at about 1 m, at 410, 443, 488, 532, 610 and
  670 nm, on five days with winds from 3.9 to 10.3 m/s (Darecki et al.
  2011, Figure 13b), as a `SpectralFluctuation` with each day's date and
  time. Read from the figure's drawing commands, like 13a and 15.
- `gernez2009_cv_by(variable)`: under clear skies at about 3 m, the
  coefficient of variation of the downwelling irradiance at 510 nm, its
  standard deviation and the period of the strongest fluctuation, against
  the wave height, the square root of the wind speed or Kd(490) (Gernez &
  Antoine 2009, Figures 8b-8d), as a `ConditionFluctuation`;
  `GERNEZ2009_VARIABLES` names the three. Read from the figure's pixels.
  Where a bar cannot be told from the other series', its standard
  deviation is nan.

**Fixed.** The values of `gernez2009_cv_by_sun_zenith()` are the medians
of each class, as the caption of the paper's Figure 7 says for Figure 8;
0.16.0 called them means in its docstrings, in DATA.md section 25 and in
the build script. The numbers are unchanged.

**Docs.** DATA.md sections 24 and 25: the new readings, and where the
paper's text and its figure differ (CV "from 30%" with Kd(490), where the
figure's largest is 24 percent; the wind of the shortest period; the depth
of the upper radiometers).

## 0.16.1 — 2026-10-21

The package's type annotations and its source are now checked in CI. No
shipped value changed, and no code changed what it does.

**Fixed.**

- Two annotations said less than the code returns. `Descent.transmittance`
  is a float when the wavelength asked for is a scalar, as every other
  wavelength-indexed result is, but was annotated as an array; so was the
  internal interpolation behind `Water.a`, `b`, `c` and `kd`. The table of
  Figure 15's conditions behind `darecki2011_radiance_cv` is annotated so
  that its mixed values type-check.
- Unused imports in `examples/isolumes.py`,
  `tests/test_reproduces_papers.py` and one build script, and f-strings
  with nothing to format in four examples and a build script. The
  examples' output is unchanged.

**Changed.** Lines in `jerlov/` longer than 79 characters are wrapped.
The text of every message and docstring is unchanged apart from where its
lines break.

**Packaging.**

- A new CI job runs `ruff check .` and `mypy` on the package, at pinned
  versions (ruff 0.15.20, mypy 1.20.2), configured in `pyproject.toml`.
- `actions/checkout` v4 → v5, `actions/setup-python` v5 → v6,
  `actions/upload-artifact` v4 → v6 and `actions/download-artifact`
  v4 → v7, the first versions of each that run on Node.js 24; GitHub
  warned that Node.js 20 is deprecated. The artifact is downloaded by name,
  whose behaviour none of these versions changed.
- The build scripts' imports were split one to a line. Rerunning every
  script reproduces every shipped CSV byte for byte.

**Docs.** DECISIONS.md section 43; CONTRIBUTING.md.

## 0.16.0 — 2026-10-18

The fluctuations of the light under a wavy surface, as two field studies
measured them, read from their figures. No shipped value changed; three
data files are added.

**Added.**

- `darecki2011_irradiance_cv()`: the coefficient of variation of the
  downwelling irradiance, sampled at 1 kHz with a 2.5 mm collector, at six
  depths from 0.86 to 9.58 m and at 443, 532 and 670 nm (Darecki,
  Stramski & Sokolski 2011, Figure 13a), as an `IrradianceFluctuation`
  with the conditions the caption gives.
- `darecki2011_radiance_cv(panel)`: the coefficient of variation of the
  radiance at 532 nm at thirteen zenith angles in the plane of the sun, on
  the three occasions of their Figure 15, as a `RadianceFluctuation`;
  `DARECKI2011_PANELS` names them.
- `gernez2009_cv_by_sun_zenith()`: under clear skies at about 3 m, the
  coefficient of variation of the downwelling irradiance at 510 nm, its
  standard deviation, and the period of the strongest fluctuation, from
  20 to 85 degrees of sun zenith angle (Gernez & Antoine 2009, Figure 8a),
  as a `SunZenithFluctuation`.
- A status, `read_from_figure`, which every value in the three files
  carries.

**How they were read.** Darecki et al.'s figures are vector graphics, and
each marker's coordinates were taken from the PDF's drawing commands;
Gernez & Antoine's is an image, read to the pixel. Both build scripts,
`tools/build_darecki2011.py` and `tools/build_gernez2009.py`, carry the
coordinates as literals, calibrate on the axes' tick marks, and check the
values against what the papers say in words. The accessors carry the
precision of the reading.

**Docs.** DATA.md sections 24 and 25: the readings, their precision, the
conditions, and Gernez & Antoine's equation (8), which as printed does not
give 1 at zero wind and is not shipped. DECISIONS.md section 42: values
read from figures are allowed under stated conditions, and the package
ships the measurements, not a model of the fluctuations.

## 0.15.2 — 2026-10-18

The painted sphere under an overcast, with a gloss coat, and with its
shadow. No code or shipped value changed.

**Examples.** `painted_sphere.py` gains three parts.

- An overcast sky: the same Monte Carlo with a uniformly bright sky in
  place of the sun. The two horizontal views come together, the grey
  sphere 2.17 and 2.19 times the water against 0.92 and 6.46 under the
  sun; it is still 11.9 times the water from above and 0.34 from below.
- Gloss: a clear coat of refractive index 1.5, reflecting by Fresnel's
  equations the scattered light it mirrors, interpolated between the
  Monte Carlo's cells. It reflects 0.32 percent looking straight at it
  from water, against 4.0 from air, and changes the grey sphere's mean
  luminance by at most 8.9 percent, seen from below; its brightest point
  mirrors light within 9 degrees of the sunbeam from every direction.
- The shadow: a sphere 0.2 m across keeps the sunbeam from the water
  behind it, and the light that beam would have scattered once towards
  the eye is taken away. From none of the four directions does it show:
  the water in it is at most 0.4 percent darker.
- The picture holds the sun and the overcast, with the coat and, under
  the sun, the shadow. It takes about two minutes.

## 0.15.1 — 2026-10-18

The search for why the Monte Carlo example differs from Tyler's lake, one
correction to that example's engine, and an example that lights a painted
sphere and looks at it from four directions. No code or shipped value
changed.

**Fixed.** In `radiance_distribution.py`, turning a direction exactly
straight up or down by a scattering angle left it unturned: the test for
that case could never be true. No photon in the example starts exactly
vertical, and no printed figure changed.

**Examples.** `radiance_distribution.py` part 7 changes one thing at a time
from part 6, as set down before the runs (DECISIONS.md section 40):

- c at depth, 0.377 1/m, moves the model's mean cosine further from
  Tyler's, to 0.773.
- Petzold's eight phase functions give mean cosines of 0.710 to 0.767.
  HAOCE 11 and HAOCE 5, chosen in part 6 for being nearest in b, have the
  two lowest backscatter ratios and the two highest mean cosines; with
  AUTEC 8, NUC 2200 or NUC 2040 the model comes within 0.002 of Tyler's
  mean cosine and 0.007 of his E0 / Ed.
- Holding HAOCE 5, b = 0.48 1/m (c = 0.60, 1.5 times the report's) gives
  Tyler's mean cosine, and Eu / Ed, E0 / Ed and the radiance near the
  horizontal then come close to his without being fitted.
- The figures compared do not tell a different phase function from a
  larger b. The example now takes about two minutes.

`painted_sphere.py`, for anyone rendering, photographing or designing
objects seen under water: a sphere in four stand-in paints, 10 m deep in
Jerlov II, seen 2 m away from above, from below, and horizontally towards
and away from the sun (DECISIONS.md section 41).

- Every face receives the radiance from the directions it faces, from the
  Monte Carlo of `radiance_distribution.py`, copied into the script so
  that it runs alone, and the sunbeam if it faces the sun. A face turned
  up receives the Ed the Monte Carlo counts directly within 2 percent.
- Between the sphere and the eye the water thins its light by exp(-c r)
  and adds the background's radiance at the eye less its radiance at the
  sphere, thinned the same way; looking horizontally that is
  `Scene.observe`, which a test confirms.
- The grey sphere is 14.5 times as bright as the water seen from above and
  0.42 times seen from below. The four paints are 7.0 times apart from
  above and 1.06 from below.
- AUTEC 7's phase function in place of HAOCE 11's moves the grey sphere by
  32 percent with the sun behind and 26 percent from above, the two
  directions whose background is light scattered back.
- `--png` writes the picture, 160 pixels to a sphere with its edge
  smoothed, four paints down and, across, each paint in air under daylight
  followed by the four directions, with nothing beyond the standard
  library and NumPy. It takes about a minute.

**Tests.** The engine against the exact asymptotic light field of
isotropic scattering, within 3 percent at single-scattering albedos 0.72
and 0.9 and 6 percent at 0.5; the turn, at every direction. The two
copies of the Monte Carlo are held identical; the sphere example's colour
shortcut matches `spectrum_to_srgb`.

**Docs.** DECISIONS.md sections 40 and 41.

## 0.15.0 — 2026-10-17

Tyler's (1958) measured radiance distribution, shipped, and the Monte
Carlo example compared with it. No shipped value changed; one data file
is added.

**Added.** `tyler1958_radiance(depth_m)`, the radiance from every
direction that Tyler measured in Lake Pend Oreille, Idaho, at seven depths
from 4.24 to 66.1 m under a clear sky, as a `RadianceDistribution`: tilt
by 10 degrees, azimuth from the sun by 20, in his relative unit, with the
sun altitude, band, beam attenuation and acceptance angle the report
gives. `TYLER1958_DEPTHS` lists the depths; nothing is interpolated
between them. The nine cells the report gives reason to doubt, the sun's
direction where Table XI gives its glitter and one overstruck digit, are
flagged `suspect` and warn. `jerlov/data/tyler1958_radiance.csv` is built
by `tools/build_tyler1958.py`, which carries the 1330 values as printed
and checks them against each other.

**Examples.** `radiance_distribution.py` part 6 runs the model on the
lake, with every choice fixed before the run (DECISIONS.md section 39):
a = 0.1119 1/m from Tyler's three deepest tables by Gershun's law,
b = c - a = 0.2841, the phase functions of HAOCE 5 and HAOCE 11, the sun
alone and a uniform overcast, fresh water.

- The model's mean cosine is 0.762 to 0.774 against Tyler's 0.704 to
  0.715; Eu / Ed 0.0131 to 0.0151 against 0.0189 to 0.0233; E0 / Ed 1.27
  to 1.29 against 1.37 to 1.39; Kd 0.144 to 0.146 1/m against 0.163 and
  0.153.
- In the sun's plane, relative to overhead, Tyler's radiance lies between
  the two skies' at 5 and 25 degrees from the zenith and above both at 65
  and 85, where the model gives 0.28 to 0.90 of it.
- What causes the difference is not established, and the example lists
  what was not varied. It now takes about a minute.

**Docs.** DATA.md section 23: the measurement, the transcription and the
flags. DECISIONS.md section 39: the comparison's choices, including one
corrected before the run.

## 0.14.4 — 2026-10-17

An example that solves for the radiance distribution. No code or shipped
value changed.

**Examples.** `radiance_distribution.py`, for work that needs the light
arriving from each direction: a Monte Carlo solution of the radiative
transfer equation in about 150 lines of NumPy, in the example, from
the package's coefficients. The package still does not solve it
(DECISIONS.md section 38).

- Jerlov II, with Williamson & Hollins's (2022) a and b at 450, 500 and
  550 nm; the phase function of HAOCE 11, the Petzold station whose b is
  nearest II's at 530 nm, from his first measured angle, the 18 percent of
  the particles' scattering below it taken as unscattered; pure water's
  from `pure_water_vsf`. A sun 40 degrees from the zenith, and a uniform
  overcast.
- Gershun's law recovers the a put in to within 2 percent. Kd from 2 to 10
  m is within 6 percent of Jerlov's (1976) at 500 and 550 nm, and 20 to 24
  percent above it at 450.
- The radiance in the plane of the sun at four depths; the mean cosine;
  E0 / Ed, 1.24 to 1.37, the factor `par_profile` does not supply; Eu / Ed,
  which the next nearest station, AUTEC 7, raises by 48 percent at 10 m.
- It takes about half a minute, and its figures are recomputed in the
  tests.

**Docs.** DECISIONS.md section 38: why an example may solve what the
package does not.

## 0.14.3 — 2026-10-15

The examples no longer silence warnings they do not explain. No code or
shipped value changed; one example prints two more lines under each of two
tables.

**Fixed.**

- `synthetic_underwater_images.py` ignored every warning around its colour
  swatches. That hid a `CoverageWarning` on each of them, since the spectra
  stop at 412 nm where the CIE observer's blue channel still has 2 percent
  of its weight, and a `GamutWarning` on 25 of the 30 swatches balanced to
  the surface. It now catches only those two, by category, and says under
  each table how much of the observer was covered and how many swatches
  were clipped.
- `from_one_measurement.py`, `measured_scattering.py`, `sources_disagree.py`
  and `synthetic_underwater_images.py` ignored `ProvenanceWarning` in six
  places, and `from_one_measurement.py` every warning in one more, where
  nothing raised one. They are removed, so a flag added later reaches the
  reader. These examples' output is unchanged.

**Packaging.** CI now runs every example with `ProvenanceWarning` as an
error, as the local pre-push checks did. A test refuses an example that
ignores every warning.

**Docs.** DECISIONS.md section 37.

## 0.14.2 — 2026-10-15

An example that silenced a warning it had no need to raise. No code,
shipped value or printed figure changed.

**Fixed.** `what_an_eye_sees.py` built a `Scene` at each depth only to read
its downwelling irradiance. `Scene` evaluates the beam attenuation c of the
default IOPs, which for Jerlov II is extrapolated by their model at 350 to
410 nm and raises a `ProvenanceWarning`; the example caught and ignored
it, though it never uses c. It now computes `Ed(0) exp(-Kd z)` from Austin &
Petzold's (1986) Kd directly, which raises nothing, and no longer catches
any `ProvenanceWarning`. Its output is the same, character for character.

## 0.14.1 — 2026-10-15

An example that counted energy where it should have counted photons, and
three figures in it that were not tested. No code or shipped value changed.

**Fixed.** `what_an_eye_sees.py`:

- Photoreceptors absorb photons and camera pixels count them, but the
  example integrated its receptor and camera curves against the energy
  spectrum. It now converts to photons first. This changes the figures in
  parts 2 and 3: the S cone's surface catch is 46 percent of the largest,
  not 57, and the L and M cones now tie at the surface, within 0.1 percent,
  where counted as energy the M cone led. The 480 nm rod is still ahead at
  20 and 50 m. Part 2 now shows the energy figure beside the photon one.
- The red-to-blue ratio of the camera was said to change "by two orders of
  magnitude" over 50 m. It falls by a factor of 25 counted as energy and 29
  counted as photons.
- "By 50 m almost everything left is between 450 and 550 nm": it is 76
  percent of the photons.
- The example said the reversal with depth "is why deep-sea fish rod
  pigments cluster near 480 nm". That is a claim about evolution the
  package does not test, and it is removed.
- Every figure the example prints is now computed in the text and
  recomputed in `tests/test_quoted_figures.py`; none of them was before.

## 0.14.0 — 2026-10-15

A weight for each photon, for PUR, visual pigments and sensors. No shipped
value changed, and no existing figure in an example changed.

**Added.**

- `par_profile(..., photon_weight=...)`: weights each photon by its
  wavelength, on the given wavelengths, before integrating. `par`, the
  fractions, `depth_of_fraction` and `kd_par` then follow the weighted flux;
  `spectrum_at` stays the unweighted light. A weight of 1 is PAR. The
  weight must be finite and not negative inside the band, and a gap there
  raises `MissingQuantityError`; outside the band it is not read.
  `ParProfile.weighted` says whether one was given, and the repr says so.

**Examples.** `isolumes.py` has a new part 5: isolumes for three rods
rather than for PAR, as Gaussians at the peaks `what_an_eye_sees.py` uses.
A thousandth of the 480 nm rod's surface catch lies 26 m below PAR's in
Jerlov I and 13 m in II. In 1C the 500 and 530 nm rods are within 0.02 m of
each other and both below the 480 nm one, where the light left peaks at
530 nm rather than 475 nm.

**Docs.** DECISIONS.md section 36; the README mentions the argument.

## 0.13.0 — 2026-10-15

The spectrum at any depth, and Kd(PAR) between two depths. No shipped value
changed, and no example's output changed.

**Added.**

- `ParProfile.kd_par(z1, z2)`: the effective Kd of PAR between two depths,
  `ln(PAR(z1) / PAR(z2)) / (z2 - z1)`, in 1/m; over another band, the same
  for that band.
- `ParProfile.spectrum_at(z)`: the downwelling spectrum at a depth, or one
  row per depth, in umol photons m-2 s-1 nm-1, on the new
  `ParProfile.wavelengths_nm`, the grid PAR is integrated over. Integrating
  it gives `par`.
- Both refuse a depth below the bottom of a descent, a negative one, NaN
  and inf; `kd_par` also refuses `z1 >= z2` and a depth with no light.

**Changed.** `seagrass_depth_limit.py` takes its top-metre and whole-column
Kd(PAR) from `kd_par`, and `isolumes.py` the colour of the light at each
isolume from `spectrum_at`, instead of computing them by hand. Their output
is the same.

**Docs.** DECISIONS.md section 35; the README shows both.

## 0.12.1 — 2026-10-15

An example for ultraviolet light under water. No code or shipped value
changed.

**Examples.** `ultraviolet.py`, for work on ultraviolet exposure under
water: reefs, plankton and larvae near the surface, photochemistry. It
integrates UV-A, 315-400 nm as the CIE defines it, and PAR with
`par_profile(..., band=)`, layer by layer through `descend`.

- Jerlov's (1976) Kd covers UV-A for 8 of the 10 types. 7C and 9C have no
  Kd below 350 nm, and are left out rather than filled in. UV-B is not
  covered for any type.
- UV-A reaches 0.61 to 0.76 of PAR's 1 percent depth in the oceanic types
  and 0.22 to 0.25 in the coastal ones. The step is between III and 1C:
  the clearest UV-A is 1.6 times as attenuated as the clearest PAR in III,
  and 4.2 times in 1C.
- Where PAR is down to 10 percent, 3.3 to 7.0 percent of the surface UV-A
  is left in the oceanic types, and 0.04 to 0.05 percent in the coastal
  ones.

The READMEs count fourteen examples; the figures quoted are tested.

## 0.12.0 — 2026-10-15

`face_irradiance_ratio` is required. No shipped value changed, and no
example's output changed.

**Changed.**

- `Scene.observe` raises `MissingQuantityError` when `face_irradiance_ratio`
  is left out, instead of taking it as 1 with a `FutureWarning` as 0.11.0
  did. The message says what the ratio is and that 1.0 is what earlier
  releases assumed. Code that passed it in 0.11.0 is unaffected; code that
  relied on the warning's default must now pass 1.0 to get the same
  results. DECISIONS.md section 34.

## 0.11.0 — 2026-10-15

The light falling on a target's visible face is stated rather than assumed.
No shipped value changed, and no example's output changed.

**Added.**

- `Scene.observe(..., face_irradiance_ratio=...)`: the irradiance on the
  face of the target the observer sees, divided by the downwelling
  irradiance, as a number or an array on the scene's wavelengths. It scales
  the target's radiance and nothing else; the veiling light is unchanged.

**Changed.**

- Leaving `face_irradiance_ratio` out takes it as 1, a face turned
  straight up, as every earlier release did without saying so, and now
  warns with `FutureWarning`. A later release will require it. DECISIONS.md
  section 33.
- `lure_colours.py` passes its share of the light on the lure's side as
  `face_irradiance_ratio` instead of scaling the downwelling irradiance
  before building the scene; the output is the same.
- `from_one_measurement.py`, `measured_scattering.py` and
  `synthetic_underwater_images.py` pass 1.0, which keeps their output, and
  list it among their assumptions.

**Docs.** DECISIONS.md section 33; the README and the `jerlov.scene`
docstring describe the argument.

## 0.10.0 — 2026-10-15

PAR over another band. No shipped value changed; one figure an example
printed was off by a rounding, and is corrected.

**Added.**

- `par_profile(..., band=(lo, hi))`: the photon flux over any band, not
  only PAR's 400-700 nm, which stays the default. The ends are
  interpolated, and nothing outside the band is read, as before.
  `ParProfile.band_nm` records the band, and the repr names it when it is
  not 400-700 nm. `band=jerlov.QUANTA_BAND_NM` integrates over the band of
  Jerlov's quanta meters.

**Fixed.**

- `euphotic_zone.py` took the share of each colour of PAR by zeroing the
  surface spectrum outside it, which divided the light near each boundary
  between the two colours by a ramp rather than at the boundary. With
  `band=` each share is the integral over its colour, and violet-blue at
  the 1 percent depth is 88 percent, not 87.

**Changed.**

- `euphotic_zone.py` section 4 now compares with Jerlov's quanta tables
  over his own band, 350-700 nm, rather than over PAR's: within 1.8
  percentage points down to 10 m, and the 1 percent level at 100 m
  against his 87, 15 percent deeper, as DATA.md section 22 has it. Over
  PAR's band it was 101 m; the band is not what separates them.
- `tests/test_quanta.py` uses `band=` instead of integrating by hand.

**Docs.** DECISIONS.md section 32: why the band has a default when the
unit has none, and why the result is still called `par`.

## 0.9.6 — 2026-10-15

The euphotic-zone example checked against a measurement, and the year of
Jerlov's quanta paper settled. No code or shipped value changed.

**Examples.** `euphotic_zone.py` has a new section 4, which sets its PAR
profile beside the quanta irradiance Jerlov measured in water of the same
type, IA, using `jerlov1977_quanta`. Down to 10 m they agree within 3.1
percentage points; below, the computed profile keeps more of the light,
1.6 times as much at 80 m, and puts the 1 percent level at 101 m against
the measured 87. The example used to say that nothing in it had been
compared with a measured profile. The one `ProvenanceWarning` that IA
raises, for a Table 5 coefficient the example does not use, is caught and
printed rather than left to the caller.

**Docs.** 0.9.4 recorded that the pages of Jerlov's "Classification of sea
water in terms of quanta irradiance" print no year, and DATA.md section 16
gave 1977 as Woźniak & Pelevin's. The publisher's record settles it:
*Journal du Conseil* 37(3), September 1977, doi:10.1093/icesjms/37.3.281.
DATA.md sections 16 and 22, the docstring of `jerlov1977_quanta` and
`tools/build_jerlov1977.py` now say so. Rerunning every build script leaves
the shipped tables byte for byte as they were.

## 0.9.5 — 2026-10-09

An example for painted gear, and a DOI that was missing. No code or shipped
value changed.

**Examples.** `lure_colours.py`, for designing or testing painted fishing
lures and other gear: six finishes seen horizontally through 0.5 to 5 m of
water, as colour swatches and luminance contrast against the open water.
The first column of swatches is the paint in air, under daylight, for
reference. `--png PATH` also writes the swatches as an image, with nothing
beyond the standard library and NumPy.

It separates what the water decides from what it does not. At each
wavelength the contrast left at range r is exp(-c r), whatever the lure and
whatever the water's glow. Where the contrast starts is another matter: it
rests on the light falling on the lure's visible side and on the water's
backscatter ratio, neither of which the Jerlov type fixes. Across three
guesses at the first and two at the second, the same finish in Jerlov 1C
starts anywhere across a factor of 124, and three finishes change sign. The
example shows that table rather than ranking finishes by one guess.

**Metadata.** Jerlov's "Classification of sea water in terms of quanta
irradiance", the source of `jerlov1977_quanta.csv` since 0.9.4, is now in
the Zenodo record's related identifiers, doi:10.1093/icesjms/37.3.281, and
the DOI is in DATA.md section 22, the build script and the docstring.

## 0.9.4 — 2026-10-09

Jerlov's measured quanta irradiance, shipped and used as a check on the
package. No existing shipped value changed.

**Added.**

- `jerlov1977_quanta(water_type)` and `QuantaLevels`: Jerlov's tables of
  quanta irradiance, 350-700 nm, measured at stations in fourteen regions,
  for types I, IA, IB, II, III, 1C and 3C. Table 2, the depths of 30, 10, 3
  and 1 percent of the surface quanta; Table 3, the percentage at depth;
  Table 5, Kd for quanta layer by layer. `QUANTA_BAND_NM` is the band.
- `jerlov1977_quanta.csv`, all four of the paper's tables, transcribed by
  `tools/build_jerlov1977.py` from the page images, since the scan's text
  layer reads decimal points as hyphens.

**Found.** DATA.md section 22.

- The tables do not all follow from each other. Allowing for the rounding
  of every printed value, eight values fall outside what the tables they
  derive from give. Seven are near misses. Table 5's Kd for II at 5-10 m,
  0.099, cannot come from Table 3, which gives 0.076 to 0.086. All eight
  are shipped as printed and marked `suspect`; the three that
  `jerlov1977_quanta` returns warn.
- Against the measurements, the package agrees within 2 m at every level
  from II to 3C. For Jerlov I one Kd puts the 1 percent level at 165 m
  against a measured 103; through `descend` it is 106, which is independent
  support for the depth profile. IA and IB stay 15 and 33 percent too deep:
  Jerlov's own IB water grew more turbid below 15 m, which the profile of
  Williamson & Hollins (2023) does not show. Why is unresolved.

**Docs.** DATA.md section 16 no longer says this paper was not obtained,
and records that its pages print no year. DECISIONS.md section 31 says why
checking against a published measurement is in scope when experimental
validation is not. The Zenodo description now counts twenty-two entries,
nine of them confirmed defects, and mentions the quanta tables.

## 0.9.3 — 2026-10-09

Small additions that the examples were working around, and checks on
publishing. No shipped value changed.

**Added.**

- `profile_depth(water_type)`: how deep `descend` can go below a surface
  type, the top of the first layer Williamson & Hollins (2023) declared no
  type for, or 200 m. Three examples found this by trying `descend` every
  10 m.
- `Descent.transmittance_at(z)`: `Ed(z) / Ed(0)` at any depth down to the
  descent's own, from the layers already crossed, for one depth or an
  array of them. `par_profile` now uses the same layers rather than
  looking each type's Kd up again. A `Descent` built by hand, which
  carries no layer Kd, is refused by both rather than treated as clear
  water.
- `classify_kd(..., types=...)`: compare with some of a source's types
  only. A wavelength is left out wherever any compared type has no Kd, so
  leaving out Solonenko & Mobley's 3C and 5C keeps 600-700 nm for an
  oceanic measurement.

**Fixed.** `tests/test_petzold.py` read Petzold's table from the source
tree rather than from the installed package, so it failed against a wheel.
It reads it through `importlib.resources`, and a test refuses the pattern.

**Packaging.**

- Publishing now stops if the tag is not the version in `pyproject.toml`.
- Publishing runs the whole test suite against the installed wheel, from a
  directory with no source tree beside it, before uploading. Doing that
  for the first time found the test above.

**Metadata.** The keywords in `.zenodo.json` and `CITATION.cff` drop
"underwater visibility", which the README says this package does not
predict, and add "diffuse attenuation coefficient", "photosynthetically
available radiation" and "euphotic zone". DECISIONS.md section 30.

**Examples.** `light_at_depth.py`, `seagrass_depth_limit.py` and
`isolumes.py` use `profile_depth` and `transmittance_at`. Their output is
unchanged.

## 0.9.2 — 2026-10-09

Three examples, each for a field the others did not reach. No code or
shipped value changed.

**Examples.**

- `optical_link.py`, for underwater optical communication and lidar: beam
  attenuation at laser lines, the range a loss budget buys, how far the two
  published IOP sets disagree on it (a factor of 2.9 at 532 nm, Jerlov III),
  Petzold's measured waters, and the narrow-beam lidar depth. What a wide
  receiver gains from scattered light is stated and not computed.
- `seagrass_depth_limit.py`, for coastal ecology and restoration: the depth
  at which the bottom receives 25, 11 or 5 percent of the surface PAR, the
  higher requirement Duarte et al. (2007) found in turbid water, the depth
  lost per step along the coastal scale, and why a Kd(PAR) from the top
  metre puts the limit too shallow. The light requirements are quoted from
  the four primary papers, with pages and DOIs: Duarte (1991), Dennison et
  al. (1993), Kenworthy & Haunert (1991) and Duarte et al. (2007). They are
  not checked here.
- `isolumes.py`, for vertical migration: where light levels from 1e-1 to
  1e-5 of the surface lie, how far each moves for a tenfold dimming, the
  colour of the light there, and oceanic against coastal water.

Every figure `examples/README.md` quotes from them is checked by
`tests/test_quoted_figures.py`.

## 0.9.1 — 2026-10-09

Fixes from a review of what 0.9.0 added, and an example for it. No shipped
value changed.

**Fixed.**

- `par_profile` evaluated Kd at every wavelength it was given, though PAR
  uses only 400 to 700 nm. A radiometer's 300-800 nm spectrum with Jerlov
  (1976), which stops at 715 nm, was refused, and Kd flagged at 705 nm
  warned about light PAR does not count. Kd is now evaluated only on the
  samples PAR rests on.
- `par_profile` let an infinite surface irradiance or Kd through, and
  returned inf or NaN with only a NumPy RuntimeWarning. Both are refused.
  With no light at the surface, `ParProfile.fraction` is NaN without a
  warning.
- `classify_kd` treated an infinite Kd as a gap and dropped it, leaving the
  other wavelengths to decide alone. It is refused.

**Examples.** `euphotic_zone.py`, for phytoplankton ecology: from one
Kd(490) reading to the nearest type, its depth profile, PAR wavelength by
wavelength, the 1 percent depth four ways, the colour of the light left at
the bottom, and three editions of the classification compared. A test now
keeps the count of examples in the two READMEs equal to the files.

## 0.9.0 — 2026-10-09

Three additions. No shipped value changed.

**Added.**

- `Scene.at_depth` takes the result of `descend` as `kd`, and builds the
  downwelling irradiance from its layer-by-layer transmittance. A descent
  to another depth, or on other wavelengths, is refused.
- `par_profile`: PAR, the photon flux from 400 to 700 nm, at any depths
  below a surface spectrum, each wavelength attenuated by its own Kd. `kd`
  is a `Water`, an array or a `Descent`. `ParProfile.depth_of_fraction`
  gives the depth at which PAR falls to a fraction of its surface value, 1
  percent by default. `unit` (`"energy"` or `"photons"`) has no default.
  This is planar PAR, from Ed.
- `classify_kd`: ranks the Jerlov types of one source by their distance
  from a measured Kd spectrum, the root mean square of ln(measured / type).
  The result names the nearest type, gives every distance, says when the
  measurement is clearer or more turbid than every type, and records the
  wavelengths it left out. Flagged reference values give one
  `ProvenanceWarning`, not one per type.

**Examples.** `light_at_depth.py` adds PAR and its 1 percent depth, and
builds its scene with `Scene.at_depth(kd=descent)`. `from_one_measurement.py`
uses `classify_kd` where it used to say there was none.

**Docs.** DECISIONS.md section 29 records the choices, including why the
example's "no classify(), deliberately" was answered rather than kept.

## 0.8.0 — 2026-10-09

Fixes from the review that followed 0.7.3. No shipped value changed.

**Changed.**

- The `plot` extra is gone. It installed matplotlib, which nothing in the
  package, its tests or its examples imports. `pip install "jerlov[plot]"`
  now installs plain `jerlov`, with a warning from pip that the extra does
  not exist. A test now fails if an extra installs something nothing
  imports.
- `Water` refuses flags for a quantity it does not carry. They used to be
  kept and never consulted, so `flags={"b": ...}` on a water with no b, or
  `"kd"` for `"Kd"`, dropped the caller's doubt without a word.
  `from_measurements` already refused this; the constructor now does too,
  as it already did for `uncertainty`.

**Added.**

- `water_type_at_depth` accepts an array of depths and returns an object
  array of the same shape, `None` where the paper declared no type. A
  single depth still gives a string or `None`. One NaN or negative depth
  refuses the whole array.

**Fixed.**

- The repr of a `Descent` printed every wavelength and transmittance. It
  now shows the path: `<Descent 1C to 45 m: 1C 0-20, III 20-40, II 40-45 m;
  Kd from jerlov1976; 301 wavelengths>`.

**Packaging.** The PyPI classifiers said "Pre-Alpha" and named no Python
version. They now say Beta, list Python 3.10 to 3.13, and mark the package
as typed. A test keeps the listed versions equal to the ones CI runs.

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

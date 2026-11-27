# Open questions

Some things in ocean optics have stayed unsettled for decades: measurements
that disagree with each other, or with what theory and other measurements
say they should be. This package does not settle them. That takes new
measurements, at sea or in a laboratory. What it can do is put numbers on
how far apart the published values are, and on how much of the gap the
conditions a source leaves unrecorded could explain, using only data it
ships with their sources and code anyone can run.

Each question below is set out the same way: the question, what was done,
what was found, what is still not known, and where the details are. Every
figure is recomputed by a test. Where a first draft said more than the
numbers did, the entry says so.

DATA.md records what each shipped table is; DECISIONS.md records why the
package does what it does. This file gathers what was found by comparing
them.

## 1. How much do the published absorption spectra of pure water disagree?

**The question.** Pure water is one substance, so its absorption should be
the same in every careful laboratory. Below about 450 nm, in the violet and
near ultraviolet, it absorbs so little that the measurements are hard, and
the published values disagree. Which is right?

**What was done.** The package ships four published spectra: Pope & Fry
(1997) and Mason, Cone & Fry (2016), measured in an integrating cavity in
the laboratory; Lee et al. (2015), inverted from the colour of the
clearest oceans; and Smith & Baker (1981), derived from the attenuation of
the clearest natural waters. Their ratios were computed from the shipped
tables themselves, not quoted from elsewhere (release 1.15.2).

**What was found.**

- Pope & Fry over Mason et al. is 7.95 at 380 nm, 2.99 at 400, 1.46 at 420
  and 1.22 at 440, and between 0.97 and 1.08 from 460 to 550 nm: the two
  laboratory measurements agree in the blue-green and part in the violet.
- Lee et al. over Mason et al. is 2.59 at 380 nm and 1.03 at 420.
- Smith & Baker, derived from natural waters, is above all three below
  450 nm.
- The choice matters: in the clearest Jerlov types pure water is much of the
  total absorption. A difference of 0.004 per m in it leaves the absorption
  of Jerlov IB short by 9.6 percent at 440 nm.
- What it does to the colour seen from above (release 1.15.9): in pure sea
  water the five spectra the package ships give remote sensing
  reflectances up to 6.85 times apart at 380 nm, 4.28 at 412, 2.62 at 443
  and 1.13 at 550, and Rrs(443)/Rrs(550) from 10.73 to 24.75. In Jerlov IB,
  whose own contents absorb more, they move Rrs by only 1.12 to 1.34
  times, less at every wavelength than the particles' backscatter ratio,
  which no source gives, does over Petzold's eight measured values. Below
  443 nm the pure sea water figures lie, for three of the spectra,
  outside the data Lee et al.'s (2011) relation was fitted to, and Gordon
  et al.'s (1988) relation gives spreads up to 26.4 percent different
  there.

A search engine's summary said Mason et al. were "lower by a factor of up
to 5" than Pope & Fry; that is not in their abstract, and the ratio from
the tables is larger. It was not used.

**What is not known.** Which laboratory value is right below 450 nm. No
laboratory measurement newer than Mason et al. (2016) was found on
2026-11-15. The package does not choose: every function that needs a pure
water absorption takes it from the caller.

**Where.** DATA.md section 29; DECISIONS.md sections 89 and 97;
`pure_water_absorption_table`; `examples/ocean_colour_and_secchi.py`,
part 8.

## 2. What happens to light scattered at less than 0.1 degree?

**The question.** Most light scattered in the sea turns by only a small
angle. Petzold's measurements of 1971, still widely used, start at
0.1 degree; below it his report extends the curve by a power law. Is that
extension the water?

**What was done.** The literature was read for measurements below 0.1
degree. Bogucki, Domaradzki, Ecke and Truman (2004), "Light scattering on
oceanic turbulence", Appl. Opt. 43(30), 5662-5668, measured from 1e-7 to
1e-3 radian, about 6e-6 to 0.06 degree, all of it below Petzold's first
angle (release 1.15.2).

**What was found.**

- Their abstract: "The total scattering coefficient b, due to scattering on
  turbulent inhomogeneities, is between 1 and 10 m-1 under typical
  oceanographic conditions", and "optical measurements at small angles are
  affected by turbulence-related scattering".
- Petzold's extension below 0.1 degree is a power law of the scattering he
  measured. Scattering on turbulence, which depends on how the water is
  being mixed that day rather than on what is in it, is not in it. So the
  3.4 to 14.5 percent of the scattering that lies below 0.1 degree in his
  tables, and everything resting on it, such as the mean cosine, describes
  the extension, not the water.

- What rests on the extension (release 1.15.8): without it, the mean
  cosine at Petzold's eight stations falls by 0.004 to 0.015 and B/S rises
  by 3.5 to 17.0 percent, but Kd, by Monte Carlo, moves by -0.63 to +0.13
  percent when the light scattered by less than 0.1 degree is treated as
  not scattered at all. Light turned by so little goes on as if
  unscattered: the extension decides how much of b is counted, not how
  fast daylight fades.

A search engine's summary said turbulence outweighs particles in
scattering up to 0.1 degree; that is not in the abstract and was not used.

**What is not known.** How much of the light near the beam turbulence
takes, against particles, in a given sea.

**Where.** DATA.md section 21; DECISIONS.md sections 89 and 96;
`ScatteringFunction.mean_cosine`; `examples/phase_function_choice.py`,
part 3; `tools/below_0_1.py` and `examples/data/below_0_1/`.

## 3. Do Williamson & Hollins's measured IOPs give back Jerlov's own Kd?

**The question.** Williamson & Hollins (2022) measured the absorption a and
the scattering b of waters they grouped by Jerlov type. Jerlov printed, for
the same types, how fast daylight fades with depth, Kd. If the two describe
the same water, a radiative transfer calculation given the first should
give back the second. Does it, and if not, could the conditions neither
source records (the sun, the shape of the scattering, the pure water)
account for the difference?

**What was done.** Williamson & Hollins chose their waters by Kd: each
campaign was given the Jerlov type whose Kd (Jerlov 1976) was nearest its
own measured Kd, within 25 percent, and their a and b are averages over
the campaigns so chosen. A Monte Carlo written for this
(`tools/kd_monte_carlo.py`), checked against Morel and Loisel's relation,
computed Kd from their a and b in 240 runs: six types (IB, II, III, 1C,
3C, 5C) at twelve wavelengths from 425 to 700 nm, then the sun, the
Petzold phase function and the pure water varied one at a time on IB and
III. The same was done again with the radiative transfer code OSOAA.
`examples/closure_with_jerlov_kd.py` reads the runs and prints everything
below.

**What was found.**

- The computed Kd over Jerlov's:

  | Type | Over Jerlov (1976) | Over Jerlov (1968) |
  |---|---|---|
  | IB | 0.98 to 1.47 | 0.99 to 1.56 |
  | II | 0.92 to 1.10 | 0.81 to 1.22 |
  | III | 0.84 to 0.98 | 0.65 to 1.09 |
  | 1C | 0.56 to 1.03 | 0.72 to 1.11 |
  | 3C | 0.51 to 1.01 | 0.66 to 1.01 |
  | 5C | 0.64 to 1.02 | 0.64 to 1.01 |

- How far each unrecorded condition moves Kd, on IB and III:

  | Condition | Change in Kd |
  |---|---|
  | The sun, 0 or 60 degrees against 30 | -7.7 to +22.4 percent |
  | The Petzold station's phase function | -6.4 to +14.5 percent |
  | The pure water under the type's contents | -10.9 to +9.3 percent |

- Together they move Kd by 0.77 to 1.53 times. Against Jerlov (1976) the
  computed Kd lies outside that reach only at the blue end: IB at 425 to
  475 nm (1.31 to 1.47 times Jerlov's), 1C and 5C at 425 nm (0.56 and
  0.64) and 3C at 425 and 450 nm (0.51 and 0.62). Everywhere else the two
  sources are consistent within what the unrecorded conditions can make.
- This agrees with Williamson & Hollins's own test (their section 3.D,
  Table 5), in which their averaged a and b, through relations with fitted
  parameters, gave Jerlov's Kd within 14 to 17 percent on average.
- The radiative transfer code OSOAA, a second calculation made apart
  from the Monte Carlo, with a sky and a surface of its own, gives Kd 1.007
  to 1.096 times the Monte Carlo's in the 62 base runs it can make, and
  lies beyond the reach at the same places, but for 5C at 425 nm, which
  it brings just inside.
- The figures above are the Monte Carlo's as first run, with one phase
  function for all the scattering and no sky. Run again (release 1.15.6)
  with pure water's share of b turned by water's own phase function and a
  clear sky, Kd rises by +1.3 to +7.6 percent, and OSOAA's Kd comes to
  0.991 to 1.018 times it: that difference was the gap. Over Jerlov (1976)
  the Kd become 1.00 to 1.55 for IB, 0.86 to 1.03 for III and down to 0.53
  for 3C at 425 nm; the conditions move them by 0.79 to 1.44 times, and
  they lie beyond that at the same blue cells as before, 5C at 425 nm
  included, and also IB at 500 nm, just beyond. The conclusion does not
  change.
- Why the blue end disagrees (release 1.15.7), from the Kd that
  Williamson & Hollins's own campaigns measured, which their dataset
  keeps. The coastal types: the campaigns typed 1C, 3C and 5C measured Kd
  at 412 nm of a median 0.59, 0.53 and 0.56 of Jerlov's (1976), what their
  averaged IOPs give; and where a, b and Kd were measured in the same
  campaign, the Monte Carlo from its own a and b gives a median 0.90, 0.93
  and 1.06 of its own Kd. The IOPs and the calculation agree with the
  water; the water's blue Kd and Jerlov's 1976 values do not. Against his
  1968 edition, whose coastal blue is lower, the measured Kd are 0.85, 0.66
  and 0.62 of his. IB: the campaigns typed IB measured Kd of 1.02 to 1.12
  of Jerlov's (1976) in the blue; it is IB's averaged a that is high. It
  rests on six campaigns, in two of which the measured a is at or above
  the Kd measured in the same campaign, which no calculation can give
  back, and in two of which a at 412 nm is a third of their own Kd.
  Closing IB's blue cells needs a 1.0 to 1.8 standard deviations lower,
  within that spread.

**The first answer was wrong, and so was the first account of why.**
Release 1.15.3 made this comparison with OSOAA alone and concluded that
the coastal types' IOPs give down to half of Jerlov's Kd, that the phase
function hardly matters, and that the two sources describe different
water. The package had written OSOAA's phase function 4 pi too small:
OSOAA expects one whose integral over the sphere is 4 pi and does not
normalise it. So OSOAA treated 96.5 to 97.8 percent of the particles'
scattering as if it were not scattered at all, and its Kd came out 0.7 to
23.1 percent below the Monte Carlo's. Release 1.15.4 found the Kd too low
when Williamson & Hollins's paper, read in full, reported agreement where
1.15.3 reported none, but blamed OSOAA without reading its source.
Reading it found the fault in the package, fixed in 1.15.5. The old runs
are kept as the record.

**What is not known.** Why Jerlov's 1976 coastal blue Kd are higher than
both his 1968 values and the waters later typed by them. His 1976 text,
read in 1.15.8, states no reason: it calls the coastal types a special
classification of northern waters rich in yellow substance, fortified by
new data (Marine Optics, p. 137). Aas et al. (2013, p. 477) note that
waters of coastal Kd in the open sea are often blooms, not water rich in
yellow substance; that fits the gap but is not shown to cause it.
Højerslev (1978, p. 1078), from Jerlov's own institute, describes the 1976
coastal types as "average optical conditions for coastal waters rich in
yellow substance". Jerlov's 1978 report, where he reduced the coastal
types to three and, by Højerslev & Aas (1991, p. 17,004), dropped values he
may have doubted, has not been obtained. Which of IB's
six campaigns are right. Why a is at or above the Kd measured in the same
campaign in 30 of the 211 matched entries for Jerlov III, 9 of 88 for II,
3 of 11 for IB, 3 of 79 for 3C, 3 of 12 for 5C and none of 68 for 1C. HydroLight was not run on these waters; the
fourth question checks the Monte Carlo against it on Solonenko &
Mobley's.

**Where.** DATA.md sections 38 and 39; DECISIONS.md sections 90 to 93;
`examples/closure_with_jerlov_kd.py`; `tools/kd_monte_carlo.py`,
`tools/kd_closure.py` and `examples/data/kd_closure/`; OSOAA's runs in
`tools/osoaa_closure.py` and `examples/data/osoaa_closure/`, and the old
ones in `examples/data/osoaa_closure_f11_too_small/`; the runs with pure
water's scattering and the sky in `tools/sm_closure.py` and
`examples/data/sm_closure/` (DATA.md section 40, DECISIONS.md section 94);
the campaigns' own Kd, a and b in `tools/blue_end.py` and
`examples/data/blue_end/` (DATA.md section 41, DECISIONS.md section 95).

## 4. Does the Monte Carlo give back HydroLight's Kd from the same IOPs?

**The question.** The third question rests on a Monte Carlo written for
it. Checked against a relation and against OSOAA, it had not been checked
against HydroLight, the code most of the field uses. Solonenko & Mobley
(2015) printed, beside the a and b they retrieved for ten Jerlov types,
the Kd HydroLight made of them, K_d^H. Given the same a and b, does the
Monte Carlo give back K_d^H, and does OSOAA?

**What was done.** The paper states HydroLight's phase function (pure
water's and the particles', weighted by their shares of b, the particles'
an average of three of Petzold's with a mean cosine of 0.924), a clear sky
and infinitely deep water; it does not print the sun, the average phase
function itself, or the depth K_d^H belongs to. The Monte Carlo was given
pure water's own scattering and a sky, and run at the 143 cells from 350
to 700 nm where a, b and K_d^H are all given, with the sun of the paper's
own Kd relation, the Petzold station nearest a mean cosine of 0.924
(NUC 2240), and the sky of Gregg & Carder's model; then with the other
seven stations, other suns and other aerosols, in 2457 runs. OSOAA was run
on the same cells. What would count as agreement was written down before
any run (DECISIONS.md section 94).
`examples/closure_with_jerlov_kd.py` prints every figure below.

**What was found.**

- The Monte Carlo's Kd over K_d^H, to 10 percent of the surface light:

  | Monte Carlo | Median | Within 10 percent |
  |---|---|---|
  | One phase function, no sky (as first run) | 0.945 | 79.7 percent |
  | With pure water's own scattering | 0.951 | 90.2 percent |
  | With it and a clear sky | 0.970 | 94.4 percent |

  The criterion set beforehand, a median within 0.95 to 1.05 and 90
  percent of the cells within 10 percent, is met.
- K_d^H lies at every one of the 143 cells within what the unprinted
  conditions make of the Monte Carlo's Kd: the other stations move it by
  -12.7 to +26.0 percent, the sun by -12.7 to +21.5.
- OSOAA, given the same totals, phase function and a sky of its own,
  gives 0.986 to 1.037 times the Monte Carlo's Kd at the 114 cells it can
  run, and 0.877 to 1.158 times K_d^H.

**What is not known.** Which of the remaining differences are HydroLight's
average-particle phase function, its sun and its depth, and which the
codes: the paper prints none of the three, and the stations alone move Kd
more than the whole difference. Why II comes out up to 1.16 times K_d^H
at 425 to 500 nm, and III, the type HydroLight was run to 6 scattering
lengths instead of 10, at 0.88 to 0.96. 29 cells cannot be run in OSOAA,
whose own pure water exceeds Solonenko & Mobley's a or b there.

**Where.** DATA.md sections 19 and 40; DECISIONS.md section 94;
`examples/closure_with_jerlov_kd.py`, parts 5 and 6; `tools/sm_closure.py`
and `examples/data/sm_closure/`; `tools/osoaa_sm_closure.py` and
`examples/data/osoaa_sm_closure/`.

## 5. Why does the shallow-water reflectance model miss two groups of runs?

**The question.** Lee et al.'s (1998, 1999) model gives the remote
sensing reflectance of shallow water from a, bb, the depth and the
bottom's albedo, and was fitted to HydroLight. Against a Monte Carlo
(DATA.md section 50) it is within 10 percent in 87.4 percent of 270 runs,
and misses in two groups: where pure water carries most of the
backscattering (16 runs, the model low, 0.818 to 0.893 of the Monte
Carlo), and over a black bottom 1 or 4 m down in turbid water (13 runs,
the model high, to 1.723). Why?

**What was done.** HydroLight is not available, so the question is which
difference between the paper's runs and the Monte Carlo moves each group,
and by how much. The waters of the paper's runs were rebuilt from its
Table 1 and Eqs. (12)-(15), 576 sets of IOPs. Then 72 Monte Carlo runs
held u and a and varied pure water's share of bb from 0 to 0.95; and 72
more took the black-bottom cells and changed one thing each: the
particles' phase function (AUTEC 8 or HAOCE 11 for NUC 2240, a and bb
held) or a sky (30 percent of the light diffuse). The model's column term
with the 1998 constants was set beside the 1999 ones. What would count as
an explanation was written down before the runs (DECISIONS.md section
114). `examples/shallow_water_closure.py` prints every figure below.

**What was found.**

- Pure water's share of bb in the paper's runs is at most 0.46. The
  first group's runs have 0.48 and 0.79.
- Holding u, the model over the Monte Carlo falls as pure water's share
  rises, in 12 of 12 cases: from 1.023-1.157 with particles alone to
  0.783-0.902 with pure water nearly alone. In deep water the model is a
  function of u alone, whoever does the backscattering; the Monte Carlo
  is not. That accounts for the direction of the first group's miss. But
  up to a share of 0.4 the ratio is still 0.927 to 1.157, not within the
  5 percent the plan asked, so the share is not the whole of it.
- The second group lies among the paper's waters: for 13 of its 13 runs,
  the paper's runs of nearly the same u spanned its kappa H.
- With a black bottom, the attenuation D the Monte Carlo implies for the
  column is 0.61 to 0.92 of the model's where kappa H is below 0.1, and
  0.89 to 1.10 where it is above 0.5: the model's single exponential
  makes the column's part grow with depth faster than the Monte Carlo
  does while kappa H is small, and agrees once it is not.
- No single change brought 10 of the 13 within 10 percent, the measure set
  beforehand. HAOCE 11's phase function brought 8, AUTEC 8's 3, the sky 3,
  the 1998 constants 6. For the same cell, changing the particles' phase
  function alone changed the ratio by a factor of 1.21 in the median cell
  and 1.92 at the most; adding the sky, by 1.04 and 1.16.
- Lee et al.'s (2011) deep-water form, which keeps water and particles
  apart, used with its published coefficients (sun at the zenith, nadir
  view) and nothing fitted, follows pure water's share where the 1999
  model does not: across the shares it moves by 1.054 to 1.079 times
  against the Monte Carlo, the 1999 model by 1.232 to 1.333 (DECISIONS.md
  section 115; its Rrs taken below the surface by Lee et al.'s 2002 Eq.
  8, an assumption). It lies at 0.943 to 1.042 of the Monte Carlo.
- Over a black bottom the miss is not ordered by the particles' bb/b: it
  rises with bb/b in 5 of the 24 cells and falls in none, and in 16 the
  middle station, NUC 2240, gives the highest ratio. Nor by the mean
  cosine. The Monte Carlo's cut at 1 degree does not set the stations
  apart: 0.5 or 2 degrees moves the ratio at any one station by a factor
  of 1.027 at most.

**What is not known.** Which phase function HydroLight's runs are nearest
to (Petzold's average particle, whose table this package has not
obtained), and how much of the second group the paper's own runs would
show: its fits were judged on all runs together, and the 1999 refit's
runs are not described. For the first group, a separated form is
known for deep water only; no shallow-water form with water and particles
apart is in this package. For the second, neither bb/b nor the mean
cosine orders the miss, so a form taking one of them would not by itself
close it; what does order it is not found.

**Where.** DATA.md section 50; DECISIONS.md sections 113 to 115;
`examples/shallow_water_closure.py`; `tools/shallow_rrs_mc.py` and
`tools/lee1998_runs.py`, with their results in
`examples/data/shallow_rrs_mc/`.

## 6. Why does Morel et al.'s f/Q archive dip at a sun of 45 degrees?

**The question.** Morel, Antoine & Gentili (2002) computed f and f/Q,
the factors that turn the water-leaving radiance into the reflectance and
correct it for the sun and the view, for six sun angles from 0 to 75
degrees, and fitted them as straight lines in 1 - cos theta_s up to 60
degrees. Their archive's f at 45 degrees lies up to 3.44 percent below
the line between its own values at 30 and 60 (DATA.md section 48),
which the fits cannot follow. Where does the dip lie, and is it physics
or the table?

**What was done.** From the user's own copy of the archive (not shipped:
it states no licence), the departure of f, of f/Q in every one of the 221
directions and of Q at the nadir from the chord between neighbouring sun
angles, for all 42 (wavelength, Chl) cases; and f(theta_s)/f(0) at each
Chl divided by the same at the next Chl, which is smooth in theta_s
where the runs agree with each other. What would follow from each result
was written down first (DECISIONS.md section 116).
`examples/fq_at_45_degrees.py --archive PATH --ocssw DIR` prints every
figure below; `tools/read_fig13.py` reads the paper's Fig. 13.

**What was found.**

- The dip belongs to one run: the sun at 45 degrees and 0.03 mg m^-3.
  There f lies below the chord at all 7 wavelengths, by 1.01 to 3.44
  percent, growing with the wavelength; every other Chl lies 0.51 to
  1.22 percent above it.
- f/Q there follows f (median over the 221 directions -3.52 to -1.35
  percent from the chord, the other Chl -0.16 to +0.85), and Q at the
  nadir, their ratio, has no dip.
- Against the next Chl, f(theta_s)/f(0) at 0.03 over the same at 0.1 is
  out of order at 45 degrees at all 7 wavelengths (at 660 nm it reads
  0.9849 at 30, 0.9267 at 45 and 0.9425 at 60 degrees); no other pair of
  Chl is out of order at any sun angle.

- The authors' own later tables do not have it (1.26.4, DECISIONS.md
  section 117). NASA's OCSSW, the processing code behind SeaDAS,
  distributes the archive's tables (morel_fq.nc, equal to the archive)
  and "f and Q tables derived hyperspectrally by Bernard Gentili", one of
  the authors, at 70 wavelengths for the same sun angles and Chl
  (morel_fq_hyperspectral_2026.nc). There, at the archive's wavelengths,
  nadir f/Q at 45 degrees and 0.03 mg m^-3 lies -0.19 to -0.13 percent
  from its chord, as 0.1 mg m^-3 does (-0.29 to -0.17). The later tables
  differ from the archive by -5.2 to +5.3 percent over all runs, but along
  the sun angle follow it except at the one run, where their ratio to it
  stands +1.23 to +3.47 percent above its chord (every other Chl -1.44 to
  +0.01).

- The paper's own figure already has it (1.26.5, DECISIONS.md section
  118). Fig. 13 (p. 6301) plots f(0)/f against Chl for the sun at 0, 15,
  30, 45 and 75 degrees. Read from the page image, its filled symbols at
  0.03 and 0.1 mg m^-3 hold all 60 of the archive's values there, a
  symbol on its own within 0.0006 of its value; where the paper's linear
  fits (Eq. B1) put f(0)/f at 45 degrees and 0.03 mg m^-3, at 560, 620
  and 660 nm, no symbol stands within 0.0110 to 0.0164. The values the
  paper plotted were the archive's, dip included: it was in the
  computation the paper reported, not brought in when the archive was
  packed, and the fits smooth it out.

- The OLCI processor's table does not have it either (1.26.9,
  DECISIONS.md section 122). EUMETSAT's auxiliary file OL_2_OCP_AX
  (Sentinel-3A, one version, found in the public bucket of ESA's new
  processing framework) holds f/Q at 11 OLCI wavelengths for the
  archive's sun angles and Chl and three wind speeds. Its nadir f/Q at
  45 degrees and 0.03 mg m^-3 lies -0.31 to -0.20 percent from its
  chord, as 0.1 mg m^-3 does (-0.28 to -0.05). It differs from the
  archive by -6.8 to +5.2 percent at the six wavelengths both have, but
  along the sun angle follows it except at the one run, where their
  ratio stands +1.09 to +2.96 percent above its chord (every other Chl
  -0.64 to +0.29).

A physical cause would not single out one Chl at one sun angle while its
neighbours in both stay in line, and neither the authors' recomputation
nor the OLCI processor's table shows it. The values are kept and marked suspect; the package warns when
they are read.

**What is not known.** What went wrong in that run. The paper computes
Raman emission in every run and says that at 0.03 mg m^-3 "the influence
of the Raman scattering is important for the green and red radiations"
(p. 6298), where the dip is deepest; neither the archive nor the later
tables give it apart, so that is not tested.

**Where.** DATA.md section 48; DECISIONS.md sections 105, 116, 117, 118 and 122;
`examples/fq_at_45_degrees.py`; `jerlov.morel2002_fq_tables`.

## 7. Why does Jerlov's Kd lie below the absorption of pure water in places?

**The question.** A diffuse attenuation coefficient cannot be smaller
than the absorption of the water alone, yet some of Jerlov's Kd for the
clearest types are. Austin & Petzold (1986) pointed it out for type I and
recommended replacing his values (DATA.md section 3). Where does it
happen, by how much, and what could make a careful measurement come out
that low?

**What was done.** Jerlov's Kd for types I to II, in both editions, at
the 13 wavelengths he printed from 400 to 700 nm, over the two pure water
absorptions the package carries that reach the red, Smith & Baker (1981)
and Pope & Fry (1997). Marshall & Smith (1990, Appl. Opt. 29, 71-84)
name two mechanisms: Raman scattering "along with excessive filter
bandwidths in irradiance measurements accounts for observations of
anomalous diffuse attenuation coefficients" (p. 71). The second was
computed by their Eq. (37) (p. 79): the attenuation a detector sees
through a filter, here Gaussian filters of 2 to 60 nm, with pure water's
own absorption as K, a flat source, averaged over the 0-10 m layer
Jerlov's types describe (Jerlov 1976, p. 133). The first was computed by
their own two-stream model with a Raman source (Eq. 33, p. 77), for pure
water, which gives the most Raman light (1.31.3). What would follow from
each result was written down first (DECISIONS.md sections 130 and 131).
`examples/jerlov_kd_below_pure_water.py` prints every figure.

**What was found.**

- Type I lies below Smith & Baker's absorption at 7 of the 13 printed
  wavelengths in both editions, least 0.666 of it at 600 nm in 1968 and
  0.862 at 700 nm in 1976. Against Pope & Fry, the 1968 edition is below
  at 4 and the 1976 edition at 2 (675 and 700 nm), least 0.731 and 0.897.
  Jerlov's 1976 revision raised the 600 nm values of types I to II, which
  removed the largest deficit.
- Rounding cannot do it: half a printed step moves Kd by at most 1.1
  percent from 600 to 700 nm in 1976 (Kd in steps of 0.005 per metre) and
  3.6 percent in 1968 (transmittance in whole percent per metre).
- A broad filter can, at some wavelengths. Through Gaussian filters of
  10, 20, 40 and 60 nm the apparent attenuation of pure water over 0-10 m
  is 0.974, 0.922, 0.853 and 0.799 of its absorption at 700 nm (Smith &
  Baker), and 0.954 to 0.706 at 600 nm; through 2 nm, within 0.7 percent.
  A 40 nm filter reaches the 1976 deficit at 700 nm, and 10 nm the one at
  600 nm. At 675 nm no filter up to 60 nm reaches either edition's value
  with Smith & Baker's absorption (with Pope & Fry's, whose table ends at
  727.5 nm, none up to 40 nm does), and none reaches the 1968 value at
  600 nm with Smith & Baker's (with Pope & Fry's, 60 nm does). Jerlov wrote that "most data result from
  sporadic observations with one to three colour filters having a broad
  band width" (1976, p. 128), without the widths.
- Raman scattering cannot do it over 0-10 m, in Marshall & Smith's
  model. Their Raman light, excited at 549 and 565 nm, lowers the Kd of
  pure water over 0-10 m by at most 0.59 percent at 675 and 700 nm, with
  their coefficient 35 percent higher or a flat sun, where type I's
  deficits are 4.5 to 18.8 percent; their own case at
  589 nm is reproduced (B = 1.38e4 here, about 1.3e4 there). That agrees
  with their own words: near the surface Raman scattering "has relatively
  little effect on K" (p. 77), and they put near surface effects on
  reflectance and attenuation together "at most ~20%" (p. 83). It grows
  with depth: over 0-20 m it lowers Kd at 700 nm by 17.7 percent, and
  over 0-30 m by 40.7 percent (with Smith & Baker's absorption).

**What is not known.** The widths, shapes and tails of the filters behind
each of Jerlov's values; the result moves with where a filter's
short-wavelength tail ends, and "real filters have longer tails than
predicted by the Gaussian" (Marshall & Smith, p. 78). Whether Jerlov's red
values all come from the top 10 m, where Raman light is small, or some
from deeper, where it is not. How far Marshall & Smith's model, with its
two streams, isotropic Raman emission, a_r = 1.5 a and a coefficient
measured at 488 nm, holds at 549 and 565 nm; it is not checked against a
radiative transfer code here. So the deficit at 675 nm, and the 1968 one
at 600 nm against Smith & Baker, have no account here.

**Where.** DATA.md section 3; DECISIONS.md sections 129, 130 and 131;
`examples/jerlov_kd_below_pure_water.py`; the sources `jerlov1968`,
`jerlov1976` and `austin1986`.

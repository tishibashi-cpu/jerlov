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

A search engine's summary said Mason et al. were "lower by a factor of up
to 5" than Pope & Fry; that is not in their abstract, and the ratio from
the tables is larger. It was not used.

**What is not known.** Which laboratory value is right below 450 nm. No
laboratory measurement newer than Mason et al. (2016) was found on
2026-11-15. The package does not choose: every function that needs a pure
water absorption takes it from the caller.

**Where.** DATA.md section 29; DECISIONS.md section 89;
`pure_water_absorption_table`.

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

A search engine's summary said turbulence outweighs particles in
scattering up to 0.1 degree; that is not in the abstract and was not used.

**What is not known.** How much of the light near the beam turbulence
takes, against particles, in a given sea.

**Where.** DATA.md section 21; DECISIONS.md section 89;
`ScatteringFunction.mean_cosine`.

## 3. Do Williamson & Hollins's measured IOPs give back Jerlov's own Kd?

**The question.** Williamson & Hollins (2022) measured the absorption a and
the scattering b of waters they grouped by Jerlov type. Jerlov printed, for
the same types, how fast daylight fades with depth, Kd. If the two describe
the same water, a radiative transfer code given the first should give back
the second. Does it, and if not, could the conditions neither source
records (the sun, the sky, the pure water, the shape of the scattering)
account for the difference?

**What was done.** The radiative transfer code OSOAA (CNES, commit 8e4914f)
was run 408 times on six types (IB, II, III, 1C, 3C, 5C) at twelve
wavelengths from 425 to 700 nm, with the package's own writers for its
input files; then the sun, the pure water, the phase function, the aerosol
and the wind were varied one at a time on IB and III (release 1.15.3).
`examples/closure_with_jerlov_kd.py` reads the runs and prints everything
below.

**What was found.**

- OSOAA does what a simple estimate says: its Kd is within -7.5 to +5.5
  percent of (a + bb) / cos(theta_w). The gaps below are between the data.
- OSOAA's Kd over Jerlov's:

  | Type | Over Jerlov (1976) | Over Jerlov (1968) |
  |---|---|---|
  | IB | 1.00 to 1.36 | 0.99 to 1.46 |
  | II | 0.87 to 1.07 | 0.78 to 1.21 |
  | III | 0.79 to 0.95 | 0.61 to 1.05 |
  | 1C | 0.54 to 1.01 | 0.65 to 1.04 |
  | 3C | 0.48 to 0.98 | 0.61 to 0.98 |
  | 5C | 0.54 to 0.94 | 0.50 to 0.93 |

- How far each unrecorded condition moves Kd, on IB and III:

  | Condition | Change in Kd |
  |---|---|
  | The sun, 0 or 60 degrees against 30 | -7.1 to +20.7 percent |
  | The pure water under the type's contents | -12.0 to +6.2 percent |
  | The Petzold station | -0.6 to +1.4 percent |
  | Aerosol, 0.05 or 0.3 | -0.2 to +0.8 percent |
  | Wind, 2 or 15 m/s | -0.3 to +0.5 percent |

- The sun matters most; the shape of the scattering, the sky and the wind
  hardly at all.
- Together the sun and the pure water lift Kd by at most 1.28 times. Against
  Jerlov (1976) that covers the gap for II and III. It does not cover IB in
  the blue, nor the coastal types: for 5C at 550 nm to reach Jerlov's Kd,
  the backscattering would have to be 0.10 of the scattering, where the
  largest Petzold measured is 0.044.
- So Williamson & Hollins's coastal types and the waters Jerlov measured his
  coastal Kd in are different water, by more than the unrecorded conditions
  can make. Neither source should be taken as confirming the other there.
- Something not looked for: from 650 nm, OSOAA's own pure water absorbs more
  than the one Williamson & Hollins used (0.624 against 0.5722 per m at 700
  nm). Where a type's total absorption is below OSOAA's water, OSOAA cannot
  be given it at all: 46 of the 408 runs could not be made.

A first draft said the gap for II and III lay within the conditions without
saying against which edition. Against Jerlov (1968) it does not hold for
III, which falls to 0.61; the text was corrected and a test checks both
editions.

**What is not known.** Why the coastal types differ: both sources are
summaries of many waters under one name. Whether another code, such as
HydroLight, gives the same Kd from the same IOPs has not been checked.
Solonenko & Mobley (2015) computed Kd with HydroLight from their own IOPs;
running those through OSOAA would separate a difference between codes from
a difference between data.

**Where.** DATA.md section 39; DECISIONS.md sections 90 and 91;
`examples/closure_with_jerlov_kd.py`; `tools/osoaa_closure.py` and
`examples/data/osoaa_closure/`.

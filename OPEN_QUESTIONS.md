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

**What is not known.** Why the blue end disagrees: the clearest type's
measured IOPs attenuate more than Jerlov's Kd there, the coastal types'
less. Why OSOAA's Kd is up to 9.6 percent above the Monte Carlo's, the
more the bluer the light and the clearer the water; its sky, which the
Monte Carlo lacks, may account for it, but that was not checked. HydroLight was not
run.

**Where.** DATA.md sections 38 and 39; DECISIONS.md sections 90 to 93;
`examples/closure_with_jerlov_kd.py`; `tools/kd_monte_carlo.py`,
`tools/kd_closure.py` and `examples/data/kd_closure/`; OSOAA's runs in
`tools/osoaa_closure.py` and `examples/data/osoaa_closure/`, and the old
ones in `examples/data/osoaa_closure_f11_too_small/`.

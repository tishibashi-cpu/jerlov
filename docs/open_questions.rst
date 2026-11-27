Open questions
==============

Some measurements in ocean optics have disagreed for decades. This
package does not settle them; that takes new measurements. It puts
numbers on how far apart the published values are, and on how much of
the gap the conditions a source leaves unrecorded could explain.
OPEN_QUESTIONS.md_ sets out each question, what was done, what was found,
what is still not known, and where the details are. The page
`Where the sources disagree <disagree.html>`_ draws a figure for each. In a
line each:

1. **How much do the published absorption spectra of pure water
   disagree?** By a factor of 7.95 at 380 nm between two laboratory
   measurements, Pope & Fry (1997) and Mason et al. (2016), falling to
   within 8 percent above 460 nm. Which is right in the violet is not
   settled.
2. **What happens to light scattered at less than 0.1 degree?** Petzold's
   tables extend a power law there; scattering on turbulence, measured at
   1 to 10 per m by Bogucki et al. (2004), is not in it. The mean cosine
   rests on that extension only slightly, and Kd hardly at all.
3. **Do Williamson & Hollins's measured IOPs give back Jerlov's own Kd?**
   By Monte Carlo, within what the unrecorded sun, phase function and pure
   water can explain, except at the blue end: the clearest type's IOPs
   attenuate more than Jerlov's Kd there and the coastal types' less. The
   Kd the same waters measured settles most of it: the coastal waters'
   own blue Kd is as low as their IOPs give, about half Jerlov's 1976
   values (less far from his 1968 ones), and Jerlov drew his coastal
   types from northern waters rich in yellow substance; the clearest
   type's water agrees with Jerlov and its averaged absorption rests on six campaigns,
   two of which measured more absorption than attenuation. The
   code OSOAA, run as a second calculation, agrees with the Monte Carlo
   within 10 percent. A first answer, made with OSOAA alone, was wrong,
   because this package wrote OSOAA's phase function 4 pi too small. The
   example
   `closure_with_jerlov_kd.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/closure_with_jerlov_kd.py>`_
   prints every figure.
4. **Does the Monte Carlo give back HydroLight's Kd from the same IOPs?**
   From Solonenko & Mobley's (2015) a and b, with pure water's own
   scattering and a clear sky, its Kd is a median 0.970 of the Kd
   HydroLight made of them, 94.4 percent of 143 cells within 10 percent,
   which meets the criterion set before the runs; OSOAA agrees with the
   Monte Carlo within 4 percent. With one phase function and no sky, as
   first run, the Monte Carlo had come out a few percent low, which was
   also why OSOAA's Kd had been up to 9.6 percent above it in the third
   question.
5. **Why does the shallow-water reflectance model miss two groups of
   runs?** Where pure water carries most of the backscattering, the
   model, a function of u alone in deep water, comes out low, and the
   more so the larger pure water's share. Over a black bottom in shallow,
   turbid water it comes out high; there no single change to the Monte
   Carlo closes the gap, and the particles' phase function alone moves
   the ratio by a factor of up to 1.92. Two phase functions with the
   same bb/b give rrs 0.49 to 1.09 times apart, so bb/b alone does not
   fix it; with the sun high and little scattering, the backward half of
   the phase function carries most of that difference. HydroLight's own
   phase function, Petzold's average particle, does not close the gap,
   nor do its angular quads or waves at Lee et al.'s 5 m/s.
   The example
   `shallow_water_closure.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/shallow_water_closure.py>`_
   prints every figure.
6. **Why does Morel et al.'s f/Q archive dip at a sun of 45 degrees?**
   One run of the authors' archive, the sun at 45 degrees and 0.03 mg
   m-3, lies below the line between 30 and 60 degrees at every wavelength,
   by 1.01 to 3.44 percent, where every other chlorophyll lies above it;
   it is out of order against its neighbour in chlorophyll and nowhere
   else is. The authors' own later tables, which NASA distributes, do not
   have the dip, nor does the f/Q table of EUMETSAT's OLCI processor, and
   the paper's own Fig. 13 already plots it. Its values
   are kept, marked suspect, and warn. The example
   `fq_at_45_degrees.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/fq_at_45_degrees.py>`_
   prints every figure from your own copy of the archive.
7. **Why does Jerlov's Kd lie below the absorption of pure water in
   places?** Austin & Petzold (1986) pointed it out for type I: against
   Smith & Baker's absorption, his Kd is as low as 0.666 of it at 600 nm in
   1968 and 0.862 at 700 nm in 1976. Rounding cannot do it. By Marshall &
   Smith's (1990) Eq. (37), a broad filter can lower the attenuation a
   detector sees by that much at 600 and 700 nm, but not at 675 nm;
   Jerlov's filters' widths are not known. Raman scattering, by Marshall &
   Smith's own model, lowers Kd over Jerlov's 0-10 m by at most 0.59
   percent at 675 and 700 nm, too little to account for it; it matters
   only deeper. The example
   `jerlov_kd_below_pure_water.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/jerlov_kd_below_pure_water.py>`_
   prints every figure.

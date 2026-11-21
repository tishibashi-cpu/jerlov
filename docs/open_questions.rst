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
   the ratio by a factor of up to 1.92. The example
   `shallow_water_closure.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/shallow_water_closure.py>`_
   prints every figure.
6. **Why does Morel et al.'s f/Q archive dip at a sun of 45 degrees?**
   One run of the authors' archive, the sun at 45 degrees and 0.03 mg
   m-3, lies below the line between 30 and 60 degrees at every wavelength,
   by 1.01 to 3.44 percent, where every other chlorophyll lies above it;
   it is out of order against its neighbour in chlorophyll and nowhere
   else is. Its values are kept, marked suspect, and warn. The example
   `fq_at_45_degrees.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/fq_at_45_degrees.py>`_
   prints every figure from your own copy of the archive.

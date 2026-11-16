Open questions
==============

Some measurements in ocean optics have disagreed for decades. This
package does not settle them; that takes new measurements. It puts
numbers on how far apart the published values are, and on how much of
the gap the conditions a source leaves unrecorded could explain.
OPEN_QUESTIONS.md_ sets out each question, what was done, what was found,
what is still not known, and where the details are. In a line each:

1. **How much do the published absorption spectra of pure water
   disagree?** By a factor of 7.95 at 380 nm between two laboratory
   measurements, Pope & Fry (1997) and Mason et al. (2016), falling to
   within 8 percent above 460 nm. Which is right in the violet is not
   settled.
2. **What happens to light scattered at less than 0.1 degree?** Petzold's
   tables extend a power law there; scattering on turbulence, measured at
   1 to 10 per m by Bogucki et al. (2004), is not in it.
3. **Do Williamson & Hollins's measured IOPs give back Jerlov's own Kd?**
   By Monte Carlo, within what the unrecorded sun, phase function and pure
   water can explain, except at the blue end: the clearest type's IOPs
   attenuate more than Jerlov's Kd there and the coastal types' less. The
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

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
   Through the radiative transfer code OSOAA, for types II and III within
   what the unrecorded sun and pure water can explain; for the clearest
   type in the blue and the coastal types, not: there the two sources
   describe different water. The example
   `closure_with_jerlov_kd.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/closure_with_jerlov_kd.py>`_
   prints every figure.

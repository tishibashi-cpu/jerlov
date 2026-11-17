From a measurement
==================

If you measured backscattering
------------------------------

``Water.bb`` refuses to guess a backscattering ratio. If you have an instrument
you do not have to:

.. code-block:: python

   r = jerlov.bb_from_vsf(0.0021, 140, 532, salinity_psu=37.0)  # beta, angle, nm
   r.bb, r.particulate, r.water     # 1/m
   r.chi_p, r.quoted_error_percent  # 1.18, 3.5

Boss & Pegau (2001). The pure sea water terms are analytic and are checked
against the definition of bb rather than transcribed; only the particle
conversion is tabulated. The salinity has no default: pure sea water at
37 scatters 30 percent more than fresh water. Angles outside 90-170 degrees are refused, and 170
warns: its quoted spread is **34.8 percent** against 2.6-6.4 from 90 to 160.

This gives the bb of the water your instrument was in. It still gives no bb
for a Jerlov water type, because nothing does.

Measured scattering functions
-----------------------------

Without an instrument, the next best thing to a guess is a water that was
measured. Petzold (1972) measured the volume scattering function from 0.1 to
180 degrees in eight ocean waters, from the clear Tongue of the Ocean to San
Diego Harbor:

.. code-block:: python

   jerlov.PETZOLD_STATIONS                  # clearest first: 'AUTEC 8', ..., 'NUC 2040'
   f = jerlov.petzold_scattering("HAOCE 11")
   f.c, f.b, f.backscatter_ratio            # 0.398, 0.21933, 0.013  (1/m, 1/m, bb/b)
   f.vsf_at(120.0)                          # 1/(m sr), at 530 nm
   f.phase_function()                       # vsf / b, at f.angles_deg

   w.bb(532, backscatter_ratio=f.backscatter_ratio)   # bb/b of a measured water

The ratio spans **0.013 to 0.044** across the eight. These are eight waters
on eight days in 1971, at 530 nm, water and particles together; none of them
is a Jerlov type. Every value was transcribed from the report and checked
against its own integrals and its second printing; DATA.md section 21.

Measured reflectances of real materials
---------------------------------------

.. code-block:: python

   m = jerlov.usgs2017_reflectance("red_nylon")   # one of jerlov.USGS2017_MATERIALS
   m.wavelengths, m.reflectance                   # 350-830 nm, every nm

Ten materials found in and around water, from white PVC to cobalt violet,
as the USGS Spectral Library Version 7 measured them (CC0): something real
to put in front of ``Scene`` instead of an invented curve. They are dry
laboratory samples; wet, or another sample, they would reflect differently
(DATA.md section 37).

Which type is my water nearest?
-------------------------------

.. code-block:: python

   r = jerlov.classify_kd(wl, measured_kd)       # source="jerlov1976" by default
   r                 # <KdClassification II 0.064, then IB 0.412 (jerlov1976, 26 wavelengths)>
   r.distances       # every type, nearest first: rms of ln(measured / type)
   r.beyond          # "clearer" or "more turbid" than every type, or None
   jerlov.classify_kd(wl, measured_kd, uncertainty=sigma_kd
                      ).nearest_within_uncertainty   # ("II", "IB"): either, within 1 sigma

It ranks the types of one edition; it draws no boundaries, since those differ
between editions. A single wavelength is accepted, and ranks oceanic and
coastal types less well apart than a spectrum does. ``types=`` compares with
some of the types only, which keeps the wavelengths where only the others
have gaps.

Other entry points
------------------

.. code-block:: python

   # Reconstruct a Kd spectrum from one measured value (Austin & Petzold 1986).
   jerlov.kd_spectrum(0.06, 490, [440, 550, 650])   # Kd, its nm, the nm wanted

   # Estimate b from a transmissometer's c (Smart 2007).
   jerlov.b_from_c(0.5, 555, bw=0.0019, cw=0.0659)   # c, its nm
   jerlov.pure_water_scattering(555, salinity_psu=37.0)  # Morel's bw, if c was corrected with it

   # An attenuation coefficient from a Secchi depth, by a rule you name; warns.
   jerlov.k_from_secchi(4.0, coefficient=jerlov.POOLE1929_SECCHI_COEFFICIENT)  # 1.7 / 4 m

   # The measured points behind the williamson2022 spectra, with their spread.
   m = jerlov.measured_points("III", "a")   # m.wavelengths, m.values, m.std_dev

   # The pure water absorption williamson2022 built its a on (300-800 nm).
   jerlov.pure_water_absorption(440)        # 0.0104; other sources say why they have none

   # A published pure water absorption in its own right: "pope1997", "smith1981",
   # "mason2016", "lee2015" or "lee2015_smoothed". Which one is yours to say.
   jerlov.pure_water_absorption_table(440, source="pope1997")   # 0.00635

   # Use your own measurements; they take exactly the same path, flags included.
   w = jerlov.Water.from_measurements(
       wavelengths, a=..., b=...,
       flags={"a": statuses},             # "ok", "suspect", ...: as in DATA.md; flagged ones warn
       uncertainty={"a": sigma_a},        # 1/m; w.uncertainty("a", 532)
   )

Light with depth
================

The type changes with depth
---------------------------

The classification is defined on the top 10 m, but clarity does not stay put.
Water that is Jerlov I at the surface is typically IB below 40 m; turbid
coastal water clears as you go down.

.. code-block:: python

   jerlov.water_type_at_depth("I", 60.0)     # 'IB'
   jerlov.water_type_at_depth("3C", 45.0)    # 'II'
   jerlov.water_type_at_depth("9C", 15.0)    # None: the paper declined to say
   jerlov.water_type_at_depth("I", [0, 30, 60])   # array(['I', 'IA', 'IB'], dtype=object)

``None`` means fewer than ten measurement campaigns supported a declaration, so
nothing is asserted. This is a lookup, not a correction applied on your
behalf.

To carry the downwelling irradiance down through that profile, with each 10 m
layer attenuating by the Kd of its own type:

.. code-block:: python

   d = jerlov.descend("1C", 45.0, wl)        # source="jerlov1976" by default
   d.layers          # ((0, 10, '1C'), (10, 20, '1C'), (20, 30, 'III'), ..., (40, 45, 'II'))
   d                 # <Descent 1C to 45 m: 1C 0-20, III 20-40, II 40-45 m; Kd from jerlov1976; ...>
   scene = jerlov.Scene.at_depth(jerlov.water("II"), 45.0, surface, wl, kd=d)

It refuses to go through a layer the paper declared nothing for, rather than
carrying the last type on: 3C stops at 70 m, 9C at 10 m.
``jerlov.profile_depth("3C")`` says how far a descent can go, and
``d.transmittance_at(z)`` gives any depth above the descent's bottom without
descending again.

Light for photosynthesis
------------------------

PAR, the photon flux from 400 to 700 nm, attenuated wavelength by wavelength
rather than with one coefficient, and the depth at which it falls to 1
percent of its surface value:

.. code-block:: python

   p = jerlov.par_profile(surface, wl, [0, 25, 50], kd=d, unit="energy")
   p.par                      # umol photons m-2 s-1 at each depth
   p.fraction                 # PAR(z) / PAR(0)
   p.depth_of_fraction(0.01)  # m
   p.kd_par(0, 1)             # effective Kd(PAR) over the top metre, 1/m
   p.spectrum_at(25)          # photons per nm at 25 m, on p.wavelengths_nm

``kd`` is a ``Water`` carrying Kd, an array, or a ``Descent``. ``unit`` has no
default, because PAR counts photons and an energy spectrum read as photons is
weighted wrongly with no sign of it. This is planar PAR, from Ed. PAR on
scalar irradiance, what a spherical sensor reads, is larger by a factor that
depends on the light field, which the package does not model; give it as the
mean cosine (Ed - Eu) / E0 and the reflectance Eu / Ed, neither of which has
a default:

.. code-block:: python

   p.scalar_par(mean_cosine=0.75, reflectance=0.02)   # E0 = Ed (1 - R) / mu

``reflectance=0`` leaves out the upwelling light, as a choice you make
(DECISIONS.md section 59).
``band=(lo, hi)`` integrates over another band instead, such as part of PAR
for the share of one colour; outside 400-700 nm the result is a photon flux
in that band, not PAR, and ``p.band_nm`` says which. ``photon_weight=`` weights
each photon by its wavelength, for a pigment's absorption or a receptor's
sensitivity, and the depths and Kd then follow the weighted flux.

A measured Kd with a standard uncertainty gives a range as well:

.. code-block:: python

   w = jerlov.Water.from_measurements(wl, kd=measured_kd,
                                      uncertainty={"kd": sigma_kd})
   p = jerlov.par_profile(surface, wl, [0, 25, 50], kd=w, unit="energy")
   p.depth_of_fraction_bounds(0.01)   # (shallower, deeper), m, Kd +- 1 sigma
   p.par_bounds(k=2)                  # (lower, higher) PAR, Kd +- 2 sigma

``kd_uncertainty=`` does the same beside an array ``kd``. The errors are taken
as fully correlated between wavelengths, the widest range any errors within
k sigma can give (DECISIONS.md section 57). The published types carry no
uncertainty, so they and ``descend`` give no range.

Jerlov measured quanta irradiance, 350-700 nm, by water type, and his
tables are shipped for checking against, with
``band=jerlov.QUANTA_BAND_NM`` to integrate over his band:

.. code-block:: python

   jerlov.jerlov1977_quanta("II")   # <QuantaLevels II: 30% 10.5 m, 10% 24 m, 3% 39 m, 1% 52 m; ...>

From II to 3C the package agrees with them within 2 m at every level. For
Jerlov I it agrees only through ``descend``; for IB it puts the 1 percent
level a third too deep, because Jerlov's IB water grew more turbid below
15 m; the profiles of quanta and the spectra measured at the stations he
drew on show the same. DATA.md section 22; DECISIONS.md sections 53-56.

Tyler measured the radiance from every direction at seven depths in a deep
lake, and his tables are shipped too, for checking a radiative transfer
model against:

.. code-block:: python

   jerlov.tyler1958_radiance(41.3)  # <RadianceDistribution Tyler 1958, 41.3 m, 19 tilts x 10 azimuths>

Since 1.33.0 the package computes a light field by Monte Carlo,
:func:`~jerlov.monte_carlo_light_field`, with every choice that sets it a
required argument: the phase function, the sun or an overcast sky, the
depth and the bottom, the photons and the seed among them. It gives Ed, Eu,
Eo, Kd, the mean cosine, the radiance in cells and rrs, each with its
standard error over batches, and says what it leaves out (an atmosphere,
polarisation, inelastic scattering, layers). For those, use OSOAA
or HydroLight. Since 1.34.0 it takes a wind for a surface of Cox and
Munk's slopes, and since 1.35.0 ``surface_facets`` says whether light
that a facet sends back towards the surface is dropped, as OSOAA does
(``"one"``), or followed over every facet it meets (``"all"``); with the
sun 80 degrees from the zenith that is about 3 percent of the light that
enters (DECISIONS.md sections 139 and 141). ``examples/radiance_distribution.py`` compares it with
Tyler's tables, and it does not match them. DATA.md section 23; DECISIONS.md
section 138.

.. code-block:: python

   import math
   iii = jerlov.water("III")
   f = jerlov.monte_carlo_light_field(
       float(iii.a(500.0)), float(iii.b(500.0)), 500.0,
       pure_water_b=float(jerlov.pure_water_scattering(500.0, salinity_psu=35.0)),
       salinity_psu=35.0,
       phase_function=jerlov.petzold_scattering("NUC 2240"),
       station_salinity_psu=35.0, cut_deg=1.0, refractive_index=1.34,
       sun_zenith_deg=30.0, depth_m=math.inf, bottom_albedo=None,
       depths_m=[2.0, 5.0, 10.0], slab_m=1.0, zenith_step_deg=10.0,
       azimuth_step_deg=45.0, photons=20_000, batches=4, seed=0,
       wind="flat")    # or the wind speed in m/s, since 1.34.0
   f.kd, f.kd_se    # Kd from 2 to 5 m and from 5 to 10 m, and their errors

Under a wavy surface the light flickers. Two field studies that give it only
in figures are shipped as values read off those figures, each with its
conditions and the precision of the reading:

.. code-block:: python

   jerlov.darecki2011_irradiance_cv()     # CV of Ed, 0.86-9.58 m, 443/532/670 nm
   jerlov.darecki2011_radiance_cv("a")    # CV of radiance, 13 angles in the sun's plane
   jerlov.gernez2009_cv_by("sun_zenith_deg")  # CV of Ed at 510 nm against the sun's zenith angle
   jerlov.darecki2011_spectral_cv()       # CV of Ed at 410-670 nm on five days of wind
   jerlov.gernez2009_cv_by("kd490_per_m") # ... against wave height, wind or Kd(490)
   jerlov.gernez2009_cv_by("wind_m_s", sky="overcast")    # overcast; or irradiance="Eu"
   jerlov.gernez2009_spectral_cv("Eu")    # CV of Eu at 412-683 nm, clear and overcast
   jerlov.gernez2009_band_cv("wind_m_s")  # CV of Ed at six bands against the conditions
   jerlov.gernez2009_diffuse_share()      # the sky's share of the light, as printed

They carry ``status = read_from_figure``. The package does not model the
fluctuations, which depend on the wind, the waves and the collector as much
as on the water. DATA.md sections 24 and 25; DECISIONS.md section 42.

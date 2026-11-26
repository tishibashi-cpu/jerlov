Which function to use
=====================

Several functions often give the same quantity, each from a different
starting point and a different paper. This page lists them by what you
want, so that you can pick one by what you have. The details, ranges and
warnings of each are in the :doc:`api`; the topic pages show the calls.

Every function here takes its inputs without defaults where the data do
not decide them: a source, a ratio, a sun, a coefficient. The page says
which papers a function follows, not how well; that is in each docstring
and in DATA.md_.

The water of a Jerlov type
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 35 25

   * - You have, and want
     - Use
     - From
   * - A type's a, b, c or Kd
     - :func:`~jerlov.water`, then :meth:`~jerlov.Water.a`,
       :meth:`~jerlov.Water.b`, :meth:`~jerlov.Water.c`,
       :meth:`~jerlov.Water.kd`
     - the ``source=`` you name (default Williamson & Hollins 2022)
   * - A type's bb
     - :meth:`~jerlov.Water.bb`, with a ratio you give: no source
       determines it
     - the source's b; with bbp/bp, Haltrin's (1999) term for pure water
   * - What a source is and what is doubtful in it
     - :func:`~jerlov.get_source`, ``jerlov.SOURCES``,
       :meth:`~jerlov.Water.caveats`
     -
   * - The measured points behind a type's spectrum
     - :func:`~jerlov.measured_points`
     - Williamson & Hollins (2022)
   * - Your own a, b or Kd, treated like a type
     - :meth:`~jerlov.Water.from_measurements`
     - you
   * - The type that applies deeper down
     - :func:`~jerlov.water_type_at_depth`, :func:`~jerlov.profile_depth`
     - Williamson & Hollins (2023)
   * - The type a measured Kd spectrum is nearest
     - :func:`~jerlov.classify_kd`
     - the edition you name

Kd, from what you have
----------------------

.. list-table::
   :header-rows: 1
   :widths: 40 35 25

   * - You have
     - Use
     - From
   * - A Jerlov type
     - :meth:`~jerlov.Water.kd`; ``jerlov1976`` and the other Kd-only
       sources carry Jerlov's own
     - Jerlov (1968, 1976), Austin & Petzold (1986)
   * - One Kd at one wavelength
     - :func:`~jerlov.kd_spectrum`
     - Austin & Petzold (1986)
   * - Chlorophyll, in case 1 water
     - :func:`~jerlov.morel2001_kd`
     - Morel & Maritorena (2001)
   * - Chlorophyll a plus pheophytin a, in case 1 water
     - :func:`~jerlov.morel1988_kd`, the earlier edition of the same model
     - Morel (1988)
   * - a, bb and the sun
     - :func:`~jerlov.lee2005_kd`
     - Lee et al. (2005, C02016)
   * - a, bb, pure water's part of bb, and the sun
     - :func:`~jerlov.lee2013_kd`, which revises :func:`~jerlov.lee2005_kd`
       and lets molecular scattering count for less
     - Lee et al. (2013)
   * - A Kd measured under one sun and sky, wanted under another
     - :func:`~jerlov.gordon1989_kd`, with both D0 from
       :func:`~jerlov.gordon1989_d0` or your own
     - Gordon (1989)
   * - A Secchi depth
     - :func:`~jerlov.k_from_secchi`, by a rule you name, such as
       ``jerlov.POOLE1929_SECCHI_COEFFICIENT``
     - Poole & Atkins (1929)

The Kd of :func:`~jerlov.lee2005_kd` and :func:`~jerlov.lee2013_kd` is
the mean from the surface to where 10 percent of the light is left.

Light below the surface
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 40 35 25

   * - You want
     - Use
     - From
   * - The downwelling irradiance through the typical depth profile
     - :func:`~jerlov.descend`
     - Williamson & Hollins (2023), and the Kd source you name
   * - PAR at depth, and the depth of a fraction of it
     - :func:`~jerlov.par_profile`, from a surface spectrum and any Kd
     -
   * - The visible energy's attenuation, and the euphotic depth, from
       a(490) and bb(490)
     - :func:`~jerlov.lee2005_kvis`, :func:`~jerlov.lee2007_depth_of_fraction`
     - Lee et al. (2005, C09019), Lee et al. (2007)
   * - A target seen through water, horizontally or looking up or down
     - :class:`~jerlov.Scene`, :meth:`~jerlov.Scene.at_depth`,
       :meth:`~jerlov.Scene.observe`, :meth:`~jerlov.Scene.observe_slant`
     - Duntley (1963) for the slant
   * - The veiling radiance, if you have nothing better
     - :func:`~jerlov.veiling_radiance_estimate`
     - single scattering
   * - The attenuation of the light that stays within an angle of its
       direction: what a transmissometer of that acceptance reads, or
       light from a target blurred rather than lost
     - :func:`~jerlov.forward_scatter` for a measured water,
       :func:`~jerlov.attenuation_within` for a type, with a station you
       name
     - Petzold (1972)
   * - The irradiance at the surface under a clear sky
     - :func:`~jerlov.gregg1990_irradiance`
     - Gregg & Carder (1990)

Reflectance and ocean colour
----------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 35 25

   * - You have, and want
     - Use
     - From
   * - a and bb; rrs just below the surface
     - :func:`~jerlov.subsurface_rrs`, with
       ``jerlov.GORDON1988_RRS_COEFFICIENTS`` or
       ``jerlov.LEE2002_RRS_COEFFICIENTS``
     - Gordon et al. (1988), Lee et al. (2002)
   * - rrs below; Rrs above
     - :func:`~jerlov.above_surface_rrs`
     - Lee et al. (2002)
   * - a, bb and pure water's part of bb; Rrs above at one of seven
       viewing geometries
     - :func:`~jerlov.lee2011_rrs`, with
       ``jerlov.LEE2011_RRS_COEFFICIENTS``; not followed by
       :func:`~jerlov.above_surface_rrs`
     - Lee et al. (2011)
   * - a, bb, the depth of the bottom and its albedo; rrs and Rrs of
       shallow water, straight down, with the bottom's part apart
     - :func:`~jerlov.lee1999_shallow_rrs`
     - Lee et al. (1998, 1999)
   * - f and Q for the radiance from the nadir
     - :func:`~jerlov.morel2002_nadir_fq`
     - Morel et al. (2002), Appendix B
   * - f and Q for other views
     - :func:`~jerlov.morel2002_fq_tables`, from your own copy of the
       authors' archive
     - Morel et al. (2002), Appendix A
   * - Radiances measured above the water; Rrs
     - :func:`~jerlov.rrs_from_above_water`, with rho from
       :func:`~jerlov.mobley_rho` or your own
     - Mobley (1999, 2015)
   * - A measured Rrs; the same without Raman scattering
     - :func:`~jerlov.lee2013_raman_correction`
     - Lee et al. (2013)
   * - Rrs; a and bbp
     - :func:`~jerlov.qaa_v6`, or :func:`~jerlov.qaa_ioccg2006`, the
       version IOCCG Report 5 tested
     - Lee (QAA_v6), IOCCG (2006)
   * - Kd and Rrs; the Secchi depth
     - :func:`~jerlov.lee2015_secchi_depth`
     - Lee et al. (2015)
   * - Chlorophyll; aph or bbp
     - :func:`~jerlov.bricaud1995_aph`, :func:`~jerlov.morel2001_bbp`
     - Bricaud et al. (1995), Morel & Maritorena (2001)

From an instrument
------------------

.. list-table::
   :header-rows: 1
   :widths: 40 35 25

   * - You measured
     - Use
     - From
   * - The volume scattering function at one angle; bb
     - :func:`~jerlov.bb_from_vsf`, :func:`~jerlov.particulate_chi`
     - Boss & Pegau (2001)
   * - c with a transmissometer; b
     - :func:`~jerlov.b_from_c`
     - Smart (2007)
   * - a and c with an ac-9 or ac-s; a corrected for scattering
     - :func:`~jerlov.rottgers2013_scatter_correction`, and
       :func:`~jerlov.rottgers2013_a715` for the absorption at the
       reference wavelength
     - Röttgers et al. (2013), Zaneveld et al. (1994)

Pure water
----------

.. list-table::
   :header-rows: 1
   :widths: 40 35 25

   * - You want
     - Use
     - From
   * - The aw a source built its a on
     - :func:`~jerlov.pure_water_absorption`
     - that source
   * - A published aw, by your choice
     - :func:`~jerlov.pure_water_absorption_table`
     - the ``source=`` you name
   * - Its scattering, backscattering or volume scattering function
     - :func:`~jerlov.pure_water_scattering`,
       :func:`~jerlov.pure_water_backscattering`,
       :func:`~jerlov.pure_water_vsf`, at a salinity you give
     -
   * - The refractive index of sea water, at a salinity and temperature
       you give
     - :func:`~jerlov.quan1995_refractive_index`
     - Quan & Fry (1995)

Colour and vision
-----------------

.. list-table::
   :header-rows: 1
   :widths: 40 35 25

   * - You want
     - Use
     - From
   * - CIE XYZ or sRGB of a spectrum, against a white you name
     - :func:`~jerlov.spectrum_to_xyz`, :func:`~jerlov.spectrum_to_srgb`,
       :func:`~jerlov.xyz_to_srgb`
     - CIE 1931
   * - The colour matching functions, or D65
     - :func:`~jerlov.cie_1931_cmf`, :func:`~jerlov.d65`
     - CIE
   * - A spectrum against any sensitivity: camera channels or receptors
     - :func:`~jerlov.integrate_response`
     -
   * - A visual pigment's absorbance
     - :func:`~jerlov.visual_pigment_template`
     - Govardovskii et al. (2000)
   * - The distance between two colours to an eye
     - :func:`~jerlov.receptor_noise_distance`
     - Vorobyev & Osorio (1998)
   * - Real materials to look at
     - :func:`~jerlov.usgs2017_reflectance`
     - USGS Spectral Library 7

For other software
------------------

.. list-table::
   :header-rows: 1
   :widths: 40 35 25

   * - You want
     - Use
     - From
   * - Coefficients per RGB channel, or the transmittance itself
     - :func:`~jerlov.rgb_attenuation`, :func:`~jerlov.rgb_transmittance`
     -
   * - A Henyey-Greenstein g
     - :func:`~jerlov.henyey_greenstein_fit`
     - Petzold (1972)
   * - a, b and c for a spectral renderer
     - :func:`~jerlov.spectral_coefficients`
     -
   * - Input files for OSOAA or HydroLight
     - :func:`~jerlov.osoaa_user_profile`,
       :func:`~jerlov.osoaa_phase_function`,
       :func:`~jerlov.hydrolight_ac9_file`
     -
   * - OSOAA's results read back
     - :func:`~jerlov.read_osoaa_flux`,
       :func:`~jerlov.read_osoaa_radiance_vs_depth`,
       :func:`~jerlov.read_osoaa_radiance_vs_vza`
     -

Heating of the upper ocean
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 35 25

   * - You want
     - Use
     - From
   * - The shortwave left at a depth, by type, as ocean models write it
     - :func:`~jerlov.solar_fraction`, :func:`~jerlov.shortwave_parameters`
     - Paulson & Simpson (1977)
   * - The table those were fitted to
     - :func:`~jerlov.jerlov1968_solar_fraction`
     - Jerlov (1968)
   * - The shortwave left at a depth, from a(490), bb(490) and the sun
     - :func:`~jerlov.lee2005_shortwave_transmittance`,
       :func:`~jerlov.lee2005_kir` for the infrared
     - Lee et al. (2005, C09019)

Measurements to check against
-----------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 35 25

   * - Measured
     - Use
     - From
   * - Volume scattering functions of eight waters
     - :func:`~jerlov.petzold_scattering`
     - Petzold (1972)
   * - Quanta irradiance by type
     - :func:`~jerlov.jerlov1977_quanta`
     - Jerlov (1977)
   * - The radiance from every direction in a lake
     - :func:`~jerlov.tyler1958_radiance`
     - Tyler (1958)
   * - The clearest ocean water measured
     - :func:`~jerlov.morel2007_stations`
     - Morel et al. (2007)
   * - The flicker of the light under waves, read off figures
     - :func:`~jerlov.darecki2011_irradiance_cv`,
       :func:`~jerlov.darecki2011_radiance_cv`,
       :func:`~jerlov.darecki2011_spectral_cv`,
       :func:`~jerlov.gernez2009_cv_by`,
       :func:`~jerlov.gernez2009_spectral_cv`,
       :func:`~jerlov.gernez2009_band_cv`,
       :func:`~jerlov.gernez2009_diffuse_share`;
       :func:`~jerlov.gernez2009_cv_by_sun_zenith` is the name before
       0.24.0, kept until 2.0
     - Darecki et al. (2011), Gernez & Antoine (2009)

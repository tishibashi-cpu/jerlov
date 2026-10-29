API reference
=============

Every name in ``jerlov.__all__``, which is what 1.0 promises to keep
working until 2.0 ("Compatibility" in `CONTRIBUTING.md`_). Import them from
``jerlov`` itself; the modules inside the package are not part of the
promise. The entries are built from the docstrings.

.. module:: jerlov

Water types and their coefficients
----------------------------------

.. autofunction:: water

.. autoclass:: Water
   :members:

.. autofunction:: pure_water_absorption

.. autofunction:: measured_points

.. autoclass:: MeasuredPoints
   :members:
   :undoc-members:

.. autofunction:: classify_kd

.. autoclass:: KdClassification
   :members:
   :undoc-members:

From a measurement
------------------

.. autofunction:: kd_spectrum

.. autofunction:: b_from_c

.. autofunction:: k_from_secchi

.. autodata:: POOLE1929_SECCHI_COEFFICIENT

The type changes with depth
---------------------------

.. autofunction:: water_type_at_depth

.. autofunction:: profile_depth

.. autofunction:: descend

.. autoclass:: Descent
   :members:
   :undoc-members:
   :exclude-members: _kd

Light for photosynthesis
------------------------

.. autofunction:: par_profile

.. autoclass:: ParProfile
   :members:

.. autodata:: PAR_RANGE_NM

.. autofunction:: jerlov1977_quanta

.. autoclass:: QuantaLevels
   :members:
   :undoc-members:

.. autodata:: QUANTA_BAND_NM

Looking at something through water
----------------------------------

.. autoclass:: Scene
   :members:

.. autoclass:: Observation
   :members:

.. autoclass:: AttenuationCoefficients
   :members:
   :undoc-members:

.. autofunction:: veiling_radiance_estimate

Colour
------

.. autofunction:: spectrum_to_xyz

.. autofunction:: spectrum_to_srgb

.. autofunction:: xyz_to_srgb

.. autofunction:: integrate_response

.. autofunction:: cie_1931_cmf

.. autofunction:: d65

.. autoexception:: GamutWarning

.. autoexception:: CoverageWarning

Scattering and backscattering
-----------------------------

.. autofunction:: pure_water_vsf

.. autofunction:: pure_water_backscattering

.. autofunction:: pure_water_scattering

.. autofunction:: bb_from_vsf

.. autoclass:: Backscattering
   :members:
   :undoc-members:

.. autofunction:: particulate_chi

.. autoexception:: AngleWarning

.. autofunction:: petzold_scattering

.. autoclass:: ScatteringFunction
   :members:
   :undoc-members:

.. autodata:: PETZOLD_STATIONS

Measured light fields
---------------------

.. autofunction:: tyler1958_radiance

.. autoclass:: RadianceDistribution
   :members:
   :undoc-members:

.. autodata:: TYLER1958_DEPTHS

.. autofunction:: darecki2011_irradiance_cv

.. autoclass:: IrradianceFluctuation
   :members:
   :undoc-members:

.. autofunction:: darecki2011_radiance_cv

.. autoclass:: RadianceFluctuation
   :members:
   :undoc-members:

.. autodata:: DARECKI2011_PANELS

.. autofunction:: darecki2011_spectral_cv

.. autoclass:: SpectralFluctuation
   :members:
   :undoc-members:

.. autofunction:: gernez2009_cv_by

.. autoclass:: ConditionFluctuation
   :members:
   :undoc-members:

.. autodata:: GERNEZ2009_PLOTS

.. autodata:: GERNEZ2009_VARIABLES

.. autofunction:: gernez2009_cv_by_sun_zenith

.. autoclass:: SunZenithFluctuation
   :members:
   :undoc-members:

.. autofunction:: gernez2009_spectral_cv

.. autoclass:: SkySpectralFluctuation
   :members:
   :undoc-members:

.. autofunction:: gernez2009_band_cv

.. autoclass:: BandConditionFluctuation
   :members:
   :undoc-members:

.. autodata:: GERNEZ2009_BAND_VARIABLES

.. autofunction:: gernez2009_diffuse_share

.. autoclass:: DiffuseShare
   :members:
   :undoc-members:

Solar heating
-------------

.. autofunction:: shortwave_parameters

.. autoclass:: ShortwaveParameters
   :members:
   :undoc-members:

.. autofunction:: solar_fraction

.. autofunction:: jerlov1968_solar_fraction

Sources
-------

.. data:: SOURCES
   :type: dict[str, Source]

   Every published set of coefficients the package ships, by the key that
   ``source=`` takes. :func:`get_source` looks one up and names the others
   when the key is unknown. Writing to it is not part of what 1.0 promises.

.. autoclass:: Source
   :members:
   :undoc-members:

.. autofunction:: get_source

.. autoclass:: ScatteringConstants
   :members:
   :undoc-members:

.. autodata:: HALTRIN1999

Warnings and errors
-------------------

.. autoexception:: ProvenanceWarning

.. autoexception:: MissingQuantityError

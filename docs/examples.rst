Examples
========

Thirty-two scripts, each for one kind of reader. Each runs against the
installed package, needs nothing beyond NumPy, and prints what it
computes; ``closure_with_jerlov_kd.py`` and ``shallow_water_closure.py``
also read results kept beside them, and so does part 3 of ``phase_function_choice.py``. CI runs every one of them, so an example that has stopped working is
a failed build rather than something a reader discovers. They are in the
repository, not in the installed package; from a clone:

.. code-block:: console

   python examples/sources_disagree.py

`examples/README.md <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/README.md>`_ says what each shows in more detail.

Six things they show
--------------------

Each figure is drawn from the package by ``tools/site_figures.py``; the
examples below it print the numbers.

.. list-table::
   :widths: 50 50

   * - .. image:: figures/card_par.svg
          :alt: PAR left with depth in the ten Jerlov types
          :width: 100%

       **The light at depth.** PAR left with depth in the ten types.
       `light_at_depth.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/light_at_depth.py>`_,
       `euphotic_zone.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/euphotic_zone.py>`_,
       `isolumes.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/isolumes.py>`_,
       `seagrass_depth_limit.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/seagrass_depth_limit.py>`_
     - .. image:: figures/card_sources.svg
          :alt: Kd of type II from four sources
          :width: 100%

       **Why the source is an argument.** Kd of one type, four sources.
       `sources_disagree.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/sources_disagree.py>`_
   * - .. image:: figures/card_colours.svg
          :alt: The colour of the daylight left at four depths in three types
          :width: 100%

       **Colours through water.** The daylight left at 0 to 20 m.
       `lure_colours.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/lure_colours.py>`_,
       `what_an_eye_sees.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/what_an_eye_sees.py>`_,
       `painted_sphere.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/painted_sphere.py>`_,
       `fish_colour_differences.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/fish_colour_differences.py>`_
     - .. image:: figures/card_heating.svg
          :alt: Solar irradiance left with depth in the oceanic types
          :width: 100%

       **Heating the upper ocean.** The solar irradiance left with depth.
       `solar_heating.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/solar_heating.py>`_
   * - .. image:: figures/card_chlorophyll.svg
          :alt: Kd of case 1 water from its chlorophyll
          :width: 100%

       **From chlorophyll.** Kd of case 1 water, 0.03 to 10 mg/m3.
       `ocean_colour_and_secchi.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/ocean_colour_and_secchi.py>`_,
       `what_is_in_the_water.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/what_is_in_the_water.py>`_
     - .. image:: figures/card_scattering.svg
          :alt: Phase functions of Petzold's eight stations
          :width: 100%

       **Scattering.** Petzold's eight phase functions.
       `measured_scattering.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/measured_scattering.py>`_,
       `phase_function_choice.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/phase_function_choice.py>`_

All thirty-two
--------------


.. list-table::
   :header-rows: 1
   :widths: 60 40

   * - If you
     - Start with
   * - wonder why ``water()`` asks for a source
     - `sources_disagree.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/sources_disagree.py>`_
   * - have measurements from an instrument, including a backscattering sensor
     - `from_one_measurement.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/from_one_measurement.py>`_
   * - need synthetic underwater imagery
     - `synthetic_underwater_images.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/synthetic_underwater_images.py>`_
   * - write an ocean circulation model
     - `solar_heating.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/solar_heating.py>`_
   * - study vision, or design a sensor
     - `what_an_eye_sees.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/what_an_eye_sees.py>`_
   * - need the light at depth, below the top 10 m
     - `light_at_depth.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/light_at_depth.py>`_
   * - need a backscatter ratio and have no instrument
     - `measured_scattering.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/measured_scattering.py>`_
   * - work with absorption, or with phytoplankton and CDOM
     - `what_is_in_the_water.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/what_is_in_the_water.py>`_
   * - need the depth of the euphotic zone, or the light phytoplankton get
     - `euphotic_zone.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/euphotic_zone.py>`_
   * - design an underwater optical link or a lidar
     - `optical_link.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/optical_link.py>`_
   * - work on seagrass, or on restoring a meadow
     - `seagrass_depth_limit.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/seagrass_depth_limit.py>`_
   * - study vertical migration, or where animals sit in the light
     - `isolumes.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/isolumes.py>`_
   * - design or test painted fishing lures or other gear
     - `lure_colours.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/lure_colours.py>`_
   * - study ultraviolet exposure under water, of reefs, plankton or chemistry
     - `ultraviolet.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/ultraviolet.py>`_
   * - need the radiance distribution, the mean cosine or scalar irradiance
     - `radiance_distribution.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/radiance_distribution.py>`_
   * - render or photograph objects under water, from any direction
     - `painted_sphere.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/painted_sphere.py>`_
   * - work with the flicker of light under waves, near the surface
     - `wave_focusing.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/wave_focusing.py>`_
   * - study fish vision, or how water changes colour differences for an animal
     - `fish_colour_differences.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/fish_colour_differences.py>`_
   * - have a chlorophyll concentration, or a and bb, rather than a water type; or want a Secchi depth
     - `ocean_colour_and_secchi.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/ocean_colour_and_secchi.py>`_
   * - have used D65 as the light above the sea, or need the sun's spectrum at the surface
     - `sunlight_and_d65.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/sunlight_and_d65.py>`_
   * - see under water along a slanted line, looking up or down
     - `looking_up_and_down.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/looking_up_and_down.py>`_
   * - look up from under water, or study what animals see from below
     - `snells_window.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/snells_window.py>`_
   * - render water, in film, games or simulation
     - `rendering_export.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/rendering_export.py>`_
   * - make images of water in RGB, and wonder what it costs the colours
     - `rgb_versus_spectral.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/rgb_versus_spectral.py>`_
   * - draw water every frame from a precomputed table, in a game or simulator
     - `water_lookup_tables.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/water_lookup_tables.py>`_
   * - choose a phase function for light in water
     - `phase_function_choice.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/phase_function_choice.py>`_
   * - need reference colours to check a rendering or photograph against
     - `reference_images.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/reference_images.py>`_
   * - run OSOAA or HydroLight with a Jerlov type as the water
     - `radiative_transfer_inputs.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/radiative_transfer_inputs.py>`_
   * - see whether one source of a Jerlov type confirms another
     - `closure_with_jerlov_kd.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/closure_with_jerlov_kd.py>`_
   * - see why a shallow-water reflectance model misses where it does
     - `shallow_water_closure.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/shallow_water_closure.py>`_
   * - see where Morel et al.'s f/Q archive dips at a 45-degree sun (needs your copy)
     - `fq_at_45_degrees.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/fq_at_45_degrees.py>`_
   * - see why some of Jerlov's Kd lies below the absorption of pure water
     - `jerlov_kd_below_pure_water.py <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/jerlov_kd_below_pure_water.py>`_

Examples
========

Seventeen scripts, each for one kind of reader. Each runs against the
installed package, needs nothing beyond NumPy, and prints what it
computes. CI runs every one of them, so an example that has stopped
working is a failed build rather than something a reader discovers. They
are in the repository, not in the installed package; from a clone:

.. code-block:: console

   python examples/sources_disagree.py

`examples/README.md <https://github.com/tishibashi-cpu/jerlov/blob/main/examples/README.md>`_ says what each shows in more detail.

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

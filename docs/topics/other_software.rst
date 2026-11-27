Water for other software
========================

Water for a renderer
--------------------

.. code-block:: python

   rgb = jerlov.rgb_attenuation(
       jerlov.water("III"), colour_space="acescg",   # or linear_srgb, rec2020
       illuminant=jerlov.d65(), distance_range_m=(0.5, 10.0))
   rgb.sigma_t, rgb.sigma_s, rgb.albedo       # 1/m, one per channel
   rgb.max_relative_error_t                   # what one exponential costs
   table = jerlov.rgb_transmittance(jerlov.water("III"), [1.0, 5.0, 10.0],
                                    colour_space="acescg",
                                    illuminant=jerlov.d65())
   table.transmittance                        # (3 distances, 3 channels), unfitted
   hg = jerlov.henyey_greenstein_fit(jerlov.petzold_scattering("HAOCE 5"),
                                     method="backscatter_ratio")  # or mean_cosine
   hg.g, hg.log_ratio                         # and where HG misses Petzold
   spectra = jerlov.spectral_coefficients(jerlov.water("III"),
                                          range_nm=(400, 700))
   spectra.as_dict()                          # for json.dump, as are the others

For film, games and simulation. A renderer in RGB attenuates each channel
as one exponential, which the spectrum is not, and the answer depends on
the light entering the water and on the distances in the scene, so both
are yours to state and the error over them comes back with the fit; a
renderer that reads a table can have the transmittance itself, unfitted. A
channel that turns negative, as the red of linear sRGB does after a few
metres of clear water, is refused rather than clipped. The
Henyey-Greenstein g is matched to Petzold's measured B/S or to his mean
cosine, which you choose; neither matches sea water's forward peak. It can
be matched to a Fournier-Forand as well (since 1.32.0), for particles of a
backscatter ratio you choose rather than a measured water; that g is the
particles' alone, with no pure water in it. The
spectra go to Mitsuba 3 or pbrt-v4 without an RGB step.
``examples/rendering_export.py`` writes all three for Mitsuba 3, pbrt-v4
and Blender (DECISIONS.md section 82).

Water for a radiative transfer code
-----------------------------------

.. code-block:: python

   iii = jerlov.water("III")
   profile = jerlov.osoaa_user_profile(       # OSOAA's -HYD.UserProfile
       iii, 440.0, depths_m=[0, 10, 50],
       pure_water=(0.00635, 0.00501629))      # what OSOAA adds back at 440 nm
   phase = jerlov.osoaa_phase_function(       # OSOAA's -HYD.ExtData
       jerlov.petzold_scattering("NUC 2200"), minus_f12_over_f11=0.0,
       f22_over_f11=1.0, f33_over_f11=1.0)    # Petzold measured none of these
   wl = [440.0, 550.0]
   ac9 = jerlov.hydrolight_ac9_file(          # HydroLight's standard ac-9 format
       iii, wl, depths_m=[0, 50],
       pure_water=(jerlov.pure_water_absorption(wl),     # the aw under III's a
                   jerlov.pure_water_scattering(wl, salinity_psu=35.0)))

This package solves the radiative transfer equation only by one Monte
Carlo method, for one homogeneous layer under a flat surface
(:func:`~jerlov.monte_carlo_light_field`, since 1.33.0); OSOAA and
HydroLight do much more. Each function returns the text of an input file for one of
them. Both codes add their own pure water back, so the pure water to take
off is the one the run will add: there is no default, and a coefficient
that turns negative without it is refused. Petzold measured no
polarization, so OSOAA's ratios are yours too. The phase function can be a
Fournier-Forand instead of a station (since 1.32.0): the particles alone,
which is what OSOAA's hydrosols are. The OSOAA files were run in
OSOAA by hand and gave back Jerlov III's c and b/c; HydroLight was not
available, and its file follows the documentation (DATA.md section 38).
``examples/radiative_transfer_inputs.py`` writes all three.

.. code-block:: python

   from pathlib import Path
   run = Path("results")                                 # OSOAA's -OSOAA.ResRoot
   flux = jerlov.read_osoaa_flux((run / "Advanced_outputs/Flux.txt").read_text())
   flux.kd(0.0, 50.0)                        # mean Kd of Ed, 1/m
   flux.total_down, flux.total_up            # normalized: the sun above is pi
   lu = jerlov.read_osoaa_radiance_vs_depth(
       (run / "Standard_outputs/RESLUM_vsZ.txt").read_text())
   lu.radiance, lu.reflectance               # pi L / Esun and pi L / Ed

OSOAA's results read back, as it prints them, normalized to the sun
above the atmosphere, which OSOAA leaves to you and so does this package.
``read_osoaa_radiance_vs_vza`` reads the radiance against the viewing angle.
OSOAA's "direct" flux is not the unscattered beam: it counts the forward
peak it truncates from the phase function as transmitted. HydroLight's
outputs are not read; no file from it was available to test against.

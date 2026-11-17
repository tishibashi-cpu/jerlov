Seeing through water
====================

Looking at something through water
----------------------------------

For a horizontal path, the observed radiance splits into the target's light
that survived and the light the water added along the way:

.. code-block:: python

   import numpy as np, jerlov

   wl   = np.arange(450., 651., 50.)
   iops = jerlov.water("III")
   kd   = jerlov.water("III", source="austin1986")

   scene = jerlov.Scene.at_depth(iops, 10.0, np.ones_like(wl), wl, kd=kd)
   b_inf = jerlov.veiling_radiance_estimate(
       iops, scene.downwelling, wl, backscatter_ratio=0.015
   )

   obs = scene.observe(np.full_like(wl, 0.8), distance_m=5.0,
                       veiling_radiance=b_inf, face_irradiance_ratio=0.3)
   obs.direct, obs.veiling, obs.radiance
   obs.veiling_fraction        # how much of what you see is just water
   obs.contrast(background)    # against another target down the same path

``veiling_radiance`` has no default. B_inf depends on the backscattering
coefficient and the phase function, and neither follows from the water type.
``veiling_radiance_estimate`` gives the usual single-scattering approximation
for callers with nothing better, but it has to be asked for.

``face_irradiance_ratio`` is the light on the face of the target the observer
sees, as a fraction of the downwelling irradiance: 1 for a face turned
straight up, less for one turned towards a horizontal line of sight. The
water type does not fix it either, so it has no default; pass 1.0 for what
releases before 0.12.0 assumed.

Deliberate limits, all recorded in ``DECISIONS.md``:

- **Slanted paths in uniform water only.** ``observe`` is horizontal;
  ``observe_slant`` takes a target above or below (see below).
- **No forward-scatter blur.** This is the radiance of one point, not the
  sharpness of an image.
- **Lambertian targets.**

Looking up or down
~~~~~~~~~~~~~~~~~~

``Scene.observe_slant`` takes a target at another depth, after Duntley
(1963). The observer is at the scene's depth; nothing about the angle is
needed beyond the two depths and the distance:

.. code-block:: python

   # n_w and k_l are yours: measured, or from a model of the light field
   obs = scene.observe_slant(np.full_like(wl, 0.8), 8.0, target_depth_m=15.0,
                             kd=kd, water_radiance=n_w,
                             radiance_attenuation=k_l,
                             face_irradiance_ratio=1.0)

``water_radiance`` is the radiance of the water itself seen along that line
from the observer, and ``radiance_attenuation`` how fast it falls with depth.
Neither has a default: the second is not Kd, and is the same in every
direction only in the asymptotic light field. Looking down, contrast
falls faster than along a horizontal line; looking up, more slowly.
Duntley's eq. (12) prints the wrong sign in front of the path radiance
(DATA.md section 34).

Coefficients for the Akkaynak-Treibitz form
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Underwater vision work usually writes the same physics as

.. code-block:: text

   I = J * exp(-beta_D * r) + B_inf * (1 - exp(-beta_B * r))

.. code-block:: python

   p = scene.attenuation_coefficients((0.5, 5.0), veiling_radiance=b_inf)
   p.beta_D, p.beta_B, p.B_inf
   p.are_distinct      # False
   p.note              # why

``are_distinct`` **is False, and that is the honest answer.** Under single
scattering both coefficients are the beam attenuation coefficient c. The
central claim of Akkaynak & Treibitz (2018) is that in reality they differ and
vary with range, depth and target reflectance; separating them needs
measurements this package does not have.

It is still useful. Implementations that fit these coefficients often bound
them by guesswork for want of a physical starting point. This gives them one,
and says how far it can be trusted.

``distance_range_m`` is required and recorded. A coefficient quoted without the
range it describes is not a well-defined quantity, so the API does not let you
omit it.

What colour is that
-------------------

.. code-block:: python

   white = scene.downwelling / np.pi          # a perfect diffuser at that depth
   rgb   = jerlov.spectrum_to_srgb(obs.radiance, wl, white=white)

   jerlov.spectrum_to_xyz(spectrum, wl)      # unnormalised CIE XYZ
   jerlov.integrate_response(spectrum, wl, sensitivity, sensitivity_wl)

``white`` has no default. A radiance spectrum has no colour until something is
called white, and underwater the useful reference is usually the downwelling
irradiance at that depth rather than daylight. Both are legitimate and they
answer different questions:

.. list-table::
   :header-rows: 1

   * - white
     - question answered
   * - downwelling at depth
     - what a diver's adapted eye, or a camera white-balanced *there*, sees
   * - daylight at the surface
     - what a camera set at the surface records

``integrate_response`` takes any spectral sensitivity: three camera channels,
or a set of photoreceptor absorbances.

Two silent errors are checked rather than assumed:

- **Coverage.** A spectrum spanning 450-650 nm integrated against colour
  matching functions spanning 360-830 nm quietly drops the ends. Every
  integration reports how much of the observer it actually covered and warns
  when it is not essentially all of it.
- **Gamut.** Underwater colours often fall outside sRGB. Clipping changes
  them, so ``GamutWarning`` says so.

How far apart two colours are to an eye
---------------------------------------

Two pieces of visual ecology, each from its primary paper, with what
belongs to a species left to you:

.. code-block:: python

   wl = np.arange(331.0, 701.0, 1.0)
   # Govardovskii et al. (2000): the absorbance of a pigment with its peak at
   # lambda_max, for an A1 or A2 chromophore. Neither has a default.
   s = jerlov.visual_pigment_template(wl, lambda_max=500.0, chromophore="A1")

   # Vorobyev & Osorio (1998): the distance between two colours in units of
   # receptor noise, from quantum catches scaled to the background. The noise
   # of each receptor channel has no default either.
   catch = (jerlov.integrate_response(target, wl, sensitivities, wl)
            / jerlov.integrate_response(background, wl, sensitivities, wl))
   jerlov.receptor_noise_distance(catch, other_catch, noise=noise)

The model is the paper's: linear in the catches, for colours close to the
background, in bright light. Its eq. (4) is misprinted; the package computes
the general form the paper derives it from (DATA.md section 26).

Colours through water
=====================

Look at a painted surface across a few metres of water and two things
happen to its light on the way to you. The water absorbs and scatters it,
so less of it arrives, and the water adds light of its own, scattered into
the line of sight from the daylight above. With distance the second takes
over, and every colour turns towards the colour of the water. This guide
follows a red and a blue surface along a horizontal path.

It computes radiance, the light arriving from one direction. It does not
say at what distance a colour can no longer be told apart: that depends on
the eye or camera looking, and the package does not claim to predict it.

The scene
---------

A :class:`jerlov.Scene` needs the water's absorption and scattering, a and b,
along the path, and the light arriving at the depth of the path. Here the
water is Jerlov III from Williamson & Hollins (2022), the default source,
and the light comes down 5 m through Jerlov's Kd for the same type, from a
surface spectrum with the shape of CIE illuminant D65:

>>> import numpy as np
>>> import jerlov
>>> wl = np.arange(412.0, 701.0, 2.0)
>>> d65_wl, d65 = jerlov.d65()
>>> surface = np.interp(wl, d65_wl, d65)
>>> water = jerlov.water("III")
>>> scene = jerlov.Scene.at_depth(water, 5.0, surface, wl,
...                               kd=jerlov.water("III", source="jerlov1976"))

The light the water adds along a long path, B_inf, depends on how much it
scatters backwards, which the water type does not fix. The package refuses
to guess it. This guide states a backscatter ratio bb/b of 0.01, the top of
the range reported for open ocean (0.005 to 0.01; 0.015 to 0.03 for coastal
water), and uses the single-scattering estimate, which its docstring calls
an order of magnitude rather than a value:

>>> water_light = jerlov.veiling_radiance_estimate(
...     water, scene.downwelling, wl, backscatter_ratio=0.01)

Two paints
----------

Two smooth spectra stand in for paints: a red that reflects above about
600 nm and a blue that reflects below about 500 nm. Real paints are
measured; these only show the behaviour.

>>> def step(edge_nm):
...     return 1.0 / (1.0 + np.exp(-(wl - edge_nm) / 15.0))
>>> red = 0.05 + 0.75 * step(600.0)
>>> blue = 0.05 + 0.75 * (1.0 - step(500.0))

The light falling on a painted face that looks along the path is less than
the downwelling irradiance on a face turned up. How much less depends on the
light field, which the package does not model, so it has no default; this
guide takes 0.3.

>>> def shares(radiance):
...     bands = [wl < 500, (wl >= 500) & (wl < 600), wl >= 600]
...     return [radiance[band].sum() / radiance.sum() for band in bands]
>>> blue_share, green_share, red_share = shares(water_light)
>>> print(f"the water's own light   blue {blue_share:.2f}"
...       f"   green {green_share:.2f}   red {red_share:.2f}")
the water's own light   blue 0.46   green 0.49   red 0.06
>>> for name, paint in (("red", red), ("blue", blue)):
...     for distance in (0.0, 1.0, 2.0, 4.0, 8.0):
...         seen = scene.observe(paint, distance, veiling_radiance=water_light,
...                              face_irradiance_ratio=0.3)
...         b, g, r = shares(seen.radiance)
...         print(f"{name:>4} at {distance:3.0f} m   blue {b:.2f}   green {g:.2f}"
...               f"   red {r:.2f}   water's share {seen.veiling_fraction.mean():.2f}")
 red at   0 m   blue 0.17   green 0.36   red 0.47   water's share 0.00
 red at   1 m   blue 0.20   green 0.40   red 0.40   water's share 0.06
 red at   2 m   blue 0.23   green 0.44   red 0.33   water's share 0.13
 red at   4 m   blue 0.30   green 0.49   red 0.20   water's share 0.31
 red at   8 m   blue 0.41   green 0.51   red 0.08   water's share 0.73
blue at   0 m   blue 0.81   green 0.18   red 0.01   water's share 0.00
blue at   1 m   blue 0.80   green 0.19   red 0.01   water's share 0.06
blue at   2 m   blue 0.79   green 0.20   red 0.01   water's share 0.15
blue at   4 m   blue 0.76   green 0.23   red 0.01   water's share 0.36
blue at   8 m   blue 0.64   green 0.34   red 0.03   water's share 0.68

"Water's share" is :attr:`jerlov.Observation.veiling_fraction`, the part of
the light reaching the eye that the water added, averaged over wavelength.

What the numbers show
---------------------

- Even right at the paint, less than half of the red paint's light is
  red. At 5 m the daylight falling on it has already lost most of its red,
  so there is little red for the paint to reflect.
- With distance, both turn towards the water's own light. By 8 m most of
  what arrives from either paint is light the water added, and the red's
  shares are close to the water's own.
- Over the same distances, the blue paint's largest share, blue, falls
  much less than the red paint's largest share, red. The water's own light
  is itself mostly blue and green.

Every one of the choices above, the surface spectrum, the depth, the
backscatter ratio, the light on the face and the paints, changes the
numbers, and each can be replaced by a measurement.

Where to go next
----------------

- :meth:`jerlov.Observation.contrast` gives the contrast against another
  target down the same path, and :meth:`jerlov.Scene.attenuation_coefficients`
  the coefficients of the Akkaynak-Treibitz image formation model.
- :func:`jerlov.spectrum_to_srgb` turns a radiance into a colour on screen,
  relative to a white you state.
- ``examples/lure_colours.py`` and ``examples/painted_sphere.py`` do this for
  painted gear and for a sphere seen from every side, and
  ``examples/synthetic_underwater_images.py`` for whole images.

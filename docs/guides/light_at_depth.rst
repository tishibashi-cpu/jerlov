The colour of the light at depth
================================

Sunlight loses its red within the first few metres of any water. What it
keeps after that depends on the water: clear ocean water passes blue best,
and coastal water, with more dissolved and suspended matter, passes green.
This guide follows the downwelling light down through four Jerlov types and
shows how the share of blue, green and red changes.

The light at the surface
------------------------

The calculation needs a spectrum to start from. Here it is daylight with the
shape of CIE illuminant D65, which the package ships for colour work. That is
an assumption, not a measurement: the real spectrum depends on the sun's
height, the sky and the surface, and a measured one should replace it when
there is one.

>>> import numpy as np
>>> import jerlov
>>> wl = np.arange(400.0, 701.0, 1.0)
>>> d65_wl, d65 = jerlov.d65()
>>> surface = np.interp(wl, d65_wl, d65)

The shares of three bands, blue 400-500 nm, green 500-600 nm and red
600-700 nm, of the light at each depth:

>>> def shares(ed):
...     bands = [(wl >= 400) & (wl < 500), (wl >= 500) & (wl < 600), wl >= 600]
...     return [ed[band].sum() / ed.sum() for band in bands]

Down through one water type
---------------------------

The diffuse attenuation coefficient Kd sets how fast the downwelling
irradiance falls: ``Ed(z) = Ed(0) exp(-Kd z)`` at each wavelength. Jerlov's
own Kd, from his 1976 book, is ``source="jerlov1976"``:

>>> for water_type in ("I", "III", "1C", "5C"):
...     kd = jerlov.water(water_type, source="jerlov1976").kd(wl)
...     for depth in (0.0, 5.0, 20.0):
...         blue, green, red = shares(surface * np.exp(-kd * depth))
...         print(f"{water_type:>3} {depth:4.0f} m   blue {blue:.2f}"
...               f"   green {green:.2f}   red {red:.2f}")
  I    0 m   blue 0.36   green 0.35   red 0.29
  I    5 m   blue 0.53   green 0.39   red 0.08
  I   20 m   blue 0.70   green 0.30   red 0.00
III    0 m   blue 0.36   green 0.35   red 0.29
III    5 m   blue 0.47   green 0.45   red 0.09
III   20 m   blue 0.49   green 0.50   red 0.00
 1C    0 m   blue 0.36   green 0.35   red 0.29
 1C    5 m   blue 0.35   green 0.54   red 0.11
 1C   20 m   blue 0.23   green 0.77   red 0.00
 5C    0 m   blue 0.36   green 0.35   red 0.29
 5C    5 m   blue 0.23   green 0.60   red 0.17
 5C   20 m   blue 0.07   green 0.90   red 0.03

The red has all but gone by 20 m in every type. In the clearest oceanic
water, Jerlov I, what is left is mostly blue; in the coastal types it is
mostly green, and more so the more turbid the water.

The water changes on the way down
---------------------------------

Jerlov classified the water by its top 10 m, and the water below is
typically different: turbid coastal water clears with depth, and the
clearest oceanic water turns a little less clear. Treating 1C as 1C all the
way to 45 m is therefore a choice. :func:`jerlov.descend` changes the type
every 10 m, following the types Williamson & Hollins (2023) found typical
at each depth across more than 2500 measurement campaigns, with Jerlov's Kd
for each, and stops where those profiles stop:

>>> descent = jerlov.descend("1C", 45.0, wl)
>>> for top, bottom, water_type in descent.layers:
...     print(f"{top:4.0f} to {bottom:4.0f} m: {water_type}")
   0 to   10 m: 1C
  10 to   20 m: 1C
  20 to   30 m: III
  30 to   40 m: III
  40 to   45 m: II

The light at 45 m, both ways:

>>> kd_1c = jerlov.water("1C", source="jerlov1976").kd(wl)
>>> for name, ed in (("1C all the way", surface * np.exp(-kd_1c * 45.0)),
...                  ("descend", surface * descent.transmittance)):
...     blue, green, red = shares(ed)
...     print(f"{name:>15}   blue {blue:.2f}   green {green:.2f}   red {red:.2f}")
 1C all the way   blue 0.12   green 0.88   red 0.00
        descend   blue 0.26   green 0.74   red 0.00

The clearer water below lets more blue through, so the light at depth is
less green than a single type would say.

Where to go next
----------------

- :func:`jerlov.water_type_at_depth` gives the type at a depth on its own,
  and :func:`jerlov.profile_depth` how deep a descent can go.
- ``examples/light_at_depth.py`` goes further down, and
  ``examples/what_an_eye_sees.py`` counts the light as photoreceptors would.
- The colour of the light as an RGB value weighs the spectrum by the CIE
  observer, which runs from 360 to 830 nm. Jerlov's Kd ends at 715 nm, so
  :func:`jerlov.spectrum_to_srgb` warns with a
  :class:`jerlov.CoverageWarning` that says how much was left out.

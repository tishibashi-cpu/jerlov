The euphotic zone
=================

Photosynthesis runs on photosynthetically available radiation, PAR: the
photons between 400 and 700 nm. The depth where PAR falls to 1 percent of
its value just below the surface is the conventional bottom of the euphotic
zone. This guide finds that depth for the Jerlov types, and compares it
with the depths Jerlov measured.

The calculation
---------------

:func:`jerlov.par_profile` attenuates a surface spectrum down to each depth,
counts the photons in the band, and finds where a given fraction is left.
The surface spectrum here has the shape of CIE illuminant D65, an assumption
that a measured spectrum should replace. Only its shape matters for the
fraction, but the package needs to know whether it is energy or photons,
since PAR counts photons:

>>> import numpy as np
>>> import jerlov
>>> wl = np.arange(400.0, 701.0, 1.0)
>>> d65_wl, d65 = jerlov.d65()
>>> surface = np.interp(wl, d65_wl, d65)
>>> depths = np.arange(0.0, 201.0, 1.0)
>>> for water_type in ("I", "IB", "II", "III", "1C", "3C", "5C"):
...     kd = jerlov.water(water_type, source="jerlov1976")
...     profile = jerlov.par_profile(surface, wl, depths, kd=kd,
...                                  unit="energy")
...     ten = profile.depth_of_fraction(0.10)
...     one = profile.depth_of_fraction(0.01)
...     print(f"{water_type:>3}   10 percent at {ten:5.1f} m"
...           f"   1 percent at {one:5.1f} m")
  I   10 percent at  60.9 m   1 percent at 166.5 m
 IB   10 percent at  37.5 m   1 percent at  94.1 m
 II   10 percent at  23.0 m   1 percent at  54.2 m
III   10 percent at  14.1 m   1 percent at  32.3 m
 1C   10 percent at  11.2 m   1 percent at  27.0 m
 3C   10 percent at   7.7 m   1 percent at  17.7 m
 5C   10 percent at   5.4 m   1 percent at  11.7 m

Each type's Kd is applied unchanged all the way down here. That is what
the type describes only in the top 10 m.

Against what Jerlov measured
----------------------------

Jerlov (1977) measured the quanta from 350 to 700 nm, the band of his
meters, and tabulated the depths of 30, 10, 3 and 1 percent for each type
in his Table 2 (:func:`jerlov.jerlov1977_quanta`). For a fair comparison
the band is his. The calculation is made two ways: with one type all the
way down, as above, and letting the type change with depth as it does in
the sea (:func:`jerlov.descend`, from the profiles of Williamson & Hollins;
see :doc:`light_at_depth`):

>>> wl = np.arange(350.0, 701.0, 1.0)
>>> surface = np.interp(wl, d65_wl, d65)
>>> for water_type in ("I", "IA", "IB", "II", "III", "1C", "3C"):
...     bottom = min(200.0, jerlov.profile_depth(water_type))
...     down = depths[depths <= bottom]
...     one_type = jerlov.par_profile(
...         surface, wl, down, kd=jerlov.water(water_type, source="jerlov1976"),
...         unit="energy", band=jerlov.QUANTA_BAND_NM)
...     changing = jerlov.par_profile(
...         surface, wl, down, kd=jerlov.descend(water_type, bottom, wl),
...         unit="energy", band=jerlov.QUANTA_BAND_NM)
...     levels = jerlov.jerlov1977_quanta(water_type)
...     measured = levels.level_depth_m[levels.level_percent.index(1.0)]
...     print(f"{water_type:>3}"
...           f"   one type {one_type.depth_of_fraction(0.01):5.1f} m"
...           f"   descend {changing.depth_of_fraction(0.01):5.1f} m"
...           f"   Jerlov {measured:5.1f} m")
  I   one type 164.4 m   descend 106.2 m   Jerlov 103.0 m
 IA   one type 122.9 m   descend 100.2 m   Jerlov  87.0 m
 IB   one type  93.0 m   descend  93.0 m   Jerlov  70.0 m
 II   one type  53.5 m   descend  53.5 m   Jerlov  52.0 m
III   one type  31.9 m   descend  31.9 m   Jerlov  31.0 m
 1C   one type  26.5 m   descend  27.4 m   Jerlov  27.0 m
 3C   one type  17.4 m   descend  17.4 m   Jerlov  19.0 m

:func:`jerlov.jerlov1977_quanta` raises a :class:`jerlov.ProvenanceWarning`
for IA, II and 1C. It is about Jerlov's Table 5, which for one layer of
each prints a Kd that does not follow from his Table 3; the depths compared
here are from Table 2 (DATA.md_ section 22).

From II to 3C the computed depths agree closely with the measured ones. For Jerlov I, one type all the way down
puts the 1 percent level far too deep; through the depth profile, in which I
typically turns IA and then IB, it comes close to what Jerlov measured.

IA and IB still come out too deep. Why IB does is recorded in DATA.md_
section 22 and DECISIONS.md_ sections 53 to 58. The measurements of the
SCOR Discoverer Expedition of 1970, two of the 1977 paper's sources, show
the light falling faster below the 10 percent level than above it, so the
difference is in the water measured, and a Kd that does not change with
depth, from any of the published tables, does not reproduce it.

Where to go next
----------------

- :meth:`jerlov.ParProfile.kd_par` gives the Kd of PAR between two depths,
  and :meth:`jerlov.ParProfile.spectrum_at` the spectrum at a depth.
- A measured Kd with its uncertainty gives a range for each depth:
  ``kd_uncertainty=`` and :meth:`jerlov.ParProfile.depth_of_fraction_bounds`.
- PAR on a spherical sensor needs a mean cosine and a reflectance that the
  caller gives: :meth:`jerlov.ParProfile.scalar_par`.
- ``examples/euphotic_zone.py``, ``examples/seagrass_depth_limit.py`` and
  ``examples/isolumes.py`` go further.

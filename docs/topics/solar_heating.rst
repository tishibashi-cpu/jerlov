Solar heating of the upper ocean
================================

Ocean circulation models absorb shortwave radiation as a sum of two
exponentials, with parameters per Jerlov type from Paulson & Simpson (1977):

.. code-block:: python

   jerlov.solar_fraction("IB", 10.0)        # 0.183 of the surface irradiance
   p = jerlov.shortwave_parameters("IB")    # R, zeta1_m, zeta2_m
   depths, fraction = jerlov.jerlov1968_solar_fraction("IB")   # the table itself

Broadband, 300-2500 nm; nothing to do with the spectral quantities on the other
pages. The parameters are usually copied from secondary sources, so ``tools/``
refits them from the table the paper fitted, Jerlov (1968) Table XXI, and
reproduces R for every row.

**They miss their own source by 46 percent at 1 m** for types II and III. Two
exponentials cannot follow the near-surface decay. ``DATA.md`` section 14 has
the numbers; anyone heating a thin surface layer should read it.

Only the five oceanic types were fitted. Asking for a coastal type raises
rather than substituting a neighbour.

Lee et al. (2005, C09019) let the attenuation change with depth, the
visible part's from a(490), bb(490) and the sun, the infrared's from the
depth and the sun; the visible share of the surface shortwave has no
default:

.. code-block:: python

   jerlov.lee2005_shortwave_transmittance(0.03, 0.004, [1.0, 10.0],
                                          sun_zenith_deg=30.0, visible_fraction=0.424)
   jerlov.lee2005_kir(1.0, sun_zenith_deg=30.0)    # 700-2500 nm, 1/m

Against Table XXI it misses less than the two exponentials in the top 10 m
for most oceanic types, and more below; ``DATA.md`` section 42.

Ocean colour, without a water type
==================================

Without a water type: chlorophyll, a and bb, the Secchi depth
-------------------------------------------------------------

.. code-block:: python

   # Kd of case 1 water from its chlorophyll, mg m^-3 (Morel & Maritorena 2001).
   jerlov.morel2001_kd([443, 490, 555], chlorophyll_mg_m3=0.3)
   # The 1988 edition, whose C is chlorophyll a plus pheophytin a.
   jerlov.morel1988_kd([443, 490, 555], pigment_mg_m3=0.3)

   # The clearest ocean water measured (Morel et al. 2007): eight stations of the
   # South Pacific gyre, and their pure water absorption.
   stations = jerlov.morel2007_stations()
   jerlov.pure_water_absorption_table([310, 420], source="morel2007")

   # f and Q for an upward radiance from the nadir (Morel et al. 2002, Appendix B),
   # at the paper's own wavelengths and chlorophylls only.
   fq = jerlov.morel2002_nadir_fq(490.0, chlorophyll_mg_m3=0.3, sun_zenith_deg=40.0)
   fq.f, fq.q, fq.correction

   # Other views need the authors' full tables, which are not shipped: fetch
   # DISTRIB_fQ_with_Raman.tar.gz from ftp://oceane.obs-vlfr.fr/pub/gentili/AppliedOptics2002/
   tables = jerlov.morel2002_fq_tables("DISTRIB_fQ_with_Raman.tar.gz")
   tables.f_over_q(560.0, sun_zenith_deg=45.0, chlorophyll_mg_m3=1.0, nadir_deg=36.64, azimuth_deg=135.0)

   # From the same chlorophyll: absorption by phytoplankton (Bricaud et al. 1995)
   # and backscattering by particles (Morel & Maritorena 2001). Water, and the
   # rest of what absorbs, are not included.
   jerlov.bricaud1995_aph([443, 490, 555], chlorophyll_mg_m3=0.3)
   jerlov.morel2001_bbp([443, 490, 555], chlorophyll_mg_m3=0.3)

   # Kd from a, bb and the sun (Lee et al. 2005, 2013); bb has no default.
   bbw_490 = jerlov.pure_water_backscattering(490, salinity_psu=35.0)
   jerlov.lee2013_kd(0.03, 0.004, bb_water=bbw_490, sun_zenith_deg=30.0)

   # The visible (350-700 nm) energy's attenuation from the surface to a depth,
   # and the depth where 1 percent of it is left, from a(490) and bb(490)
   # (Lee et al. 2005, C09019; Lee et al. 2007).
   jerlov.lee2005_kvis(0.03, 0.004, 20.0, sun_zenith_deg=30.0)
   jerlov.lee2007_depth_of_fraction(0.03, 0.004, sun_zenith_deg=30.0, fraction=0.01)

   # A Kd under another sun and sky, by Gordon's (1989) D0. Both D0 are yours:
   # Jerlov's tables do not record the light they were measured under.
   d0 = jerlov.gordon1989_d0(30.0, direct_fraction=0.8)
   jerlov.gordon1989_kd(0.05, d0_from=d0, d0_to=jerlov.gordon1989_d0(60.0, direct_fraction=0.7))

   # The remote sensing reflectance, below and above the surface.
   rrs = jerlov.subsurface_rrs(a, bb, coefficients=jerlov.GORDON1988_RRS_COEFFICIENTS)
   Rrs = jerlov.above_surface_rrs(rrs)

   # From above-water radiances: Rrs = (Lt - rho Lsky) / Ed, with rho from one
   # of Mobley's tables (1999 or 2015; no default) or a value you choose.
   rho = jerlov.mobley_rho(source="mobley1999", wind_speed=5.0, sun_zenith_deg=30.0,
                           view_nadir_deg=40.0, view_azimuth_deg=135.0)
   jerlov.rrs_from_above_water(lt, lsky, ed, rho=rho)

   # An ac-9's absorption corrected for the light its tube misses, by one of the
   # four methods Röttgers et al. (2013) compared; the method has no default.
   jerlov.rottgers2013_scatter_correction(am, cm, am715, cm715, method="proportional", ec=1.0)

   # Or above the surface with water and particles apart, at one of the seven
   # viewing geometries Lee et al. (2011) print; (0, 0, 0) is straight down.
   jerlov.lee2011_rrs(a, bb, bb_water=bb_water,
                      coefficients=jerlov.LEE2011_RRS_COEFFICIENTS[(0.0, 0.0, 0.0)])

   # Take Raman scattering out of a measured Rrs first (Lee et al. 2013), 412-667 nm.
   jerlov.lee2013_raman_correction(bands_nm, measured_Rrs,
                                   bands={"440": 443, "550": 555}).rrs

   # The Secchi depth from one Kd and one Rrs spectrum, 400-700 nm (Lee et al. 2015).
   jerlov.lee2015_secchi_depth(wavelengths, kd, Rrs)

   # And back: a and bbp from Rrs by the quasi-analytical algorithm, either version.
   q = jerlov.qaa_v6(bands_nm, Rrs, bands={"412": 412, "443": 443, "490": 490,
                                           "55x": 555, "670": 670},
                     pure_water=(pw_nm, aw, bbw))      # q.a, q.bbp, q.adg, q.aph
   # pw_nm, aw and bbw are arrays covering the bands: for instance
   # pure_water_absorption_table(pw_nm, source="pope1997") and
   # pure_water_backscattering(pw_nm, salinity_psu=35.0).
   jerlov.qaa_ioccg2006(...)   # the version IOCCG Report 5 tested; same arguments

These are forward relations, each from its paper and each with the
conditions it was fitted for: Morel & Maritorena's for case 1 water only,
the reflectance for deep water seen from straight above. A result outside
what the paper fitted or checked comes with a ``ProvenanceWarning``. The
inverse comes in two versions: QAA_v6 reproduces the results its author's
spreadsheet stored, and the IOCCG Report 5 version reproduces that report's
statistics on its synthetic data (DATA.md section 28). Nothing here reads
satellite files; pass the Rrs you have read (DECISIONS.md sections 66 and
67).

The light at the sea surface under a clear sky
----------------------------------------------

.. code-block:: python

   sky = jerlov.gregg1990_irradiance(
       np.arange(350, 701), sun_zenith_deg=40.0, day_of_year=172,
       pressure_hpa=1013.25, air_mass_type=1, relative_humidity=80.0,
       precipitable_water_cm=1.5, wind_speed_24h=3.0, wind_speed=5.0,
       ozone_du=300.0, visibility_km=15.0)   # or aerosol_optical_thickness_550
   sky.direct_above, sky.diffuse_above       # W m-2 nm-1, just above the sea
   sky.below                                 # just below: Scene.at_depth, par_profile

The model of Gregg & Carder (1990), with its table of the sun's spectrum
and the gases' absorption at every nm from 350 to 700. Every input that
describes the sky is yours; none has a default. It reproduces the paper's
own diffuse shares (Table 5) to the printed percent. The paper prints a
second 1/2 inside Fresnel's law (DATA.md section 35).

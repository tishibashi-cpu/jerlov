"""Every public input that is meant to be a number refuses a bool and text
(DECISIONS.md section 126), with the rest of the review of 1.28.0: an
infinite depth in solar_fraction, empty and malformed inputs that ended
in IndexError, and the flat methods of Rottgers et al. and cm's gaps."""

from __future__ import annotations

import inspect
import pathlib
import warnings

import numpy as np
import pytest

import jerlov
from jerlov import _data

#: A valid call to every public function but morel2002_fq_tables, which
#: needs the user's own archive: name -> (args, kwargs).
WL = np.array([450.0, 500.0, 550.0])
W = jerlov.water("II")
WS = jerlov.water("II", source="solonenko2015")
SKY = jerlov.gregg1990_irradiance(
    np.arange(380.0, 701.0), sun_zenith_deg=30.0, day_of_year=172,
    pressure_hpa=1013.25, air_mass_type=1, relative_humidity=80.0,
    precipitable_water_cm=1.5, wind_speed_24h=3.0, wind_speed=5.0,
    ozone_du=300.0, visibility_km=10.0)
V6_NM = np.array([412.0, 443.0, 489.0, 510.0, 555.0, 670.0])
V6_RRS = np.array([0.0060, 0.0055, 0.0045, 0.0035, 0.0020, 0.0002])
V6_WATER = (V6_NM,
            np.array([0.0031, 0.0048, 0.0132, 0.0302, 0.0596, 0.439]),
            np.array([0.0034, 0.0025, 0.00158, 0.00133, 0.0009, 0.00034]))
R5_NM = np.array([410.0, 440.0, 490.0, 510.0, 555.0, 670.0])
R5_RRS = V6_RRS
V6_WATER5 = (R5_NM, V6_WATER[1], V6_WATER[2])
HWL = np.array([412.0, 440.0, 488.0, 510.0, 555.0, 650.0])
A_W = np.array([0.0046, 0.0064, 0.0145, 0.0357, 0.0596, 0.34])
B_W = np.array([0.0067, 0.0049, 0.0033, 0.0027, 0.0019, 0.0010])
P = jerlov.petzold_scattering("NUC 2240")
with warnings.catch_warnings():
    warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
    FORWARD = jerlov.forward_scatter(P, 1.0)


def RUN(name):
    """One of the OSOAA outputs kept in tests/data."""
    return (pathlib.Path(__file__).resolve().parent / "data"
            / "osoaa_iii_440" / name).read_text()


def calls():
    G = dict(sun_zenith_deg=30.0, day_of_year=172, pressure_hpa=1013.25,
             air_mass_type=1, relative_humidity=80.0,
             precipitable_water_cm=1.5, wind_speed_24h=3.0, wind_speed=5.0,
             ozone_du=300.0, visibility_km=10.0)
    return {
        "veiling_radiance_estimate": ((W, np.array([1.0, 1.0, 1.0]), WL), dict(particle_backscatter_ratio=0.0183)),
        "spectrum_to_xyz": ((np.ones(321), np.arange(380.0, 701.0)), {}),
        "spectrum_to_srgb": ((np.ones(321), np.arange(380.0, 701.0)), dict(white=np.ones(321))),
        "xyz_to_srgb": ((np.array([0.5, 0.5, 0.5]),), {}),
        "integrate_response": ((np.ones(3), WL, np.ones(3), WL), {}),
        "cie_1931_cmf": ((), {}),
        "d65": ((), {}),
        "get_source": (("williamson2022",), {}),
        "water": (("II",), {}),
        "water_type_at_depth": (("II", 20.0), {}),
        "descend": (("II", 50.0, WL), {}),
        "profile_depth": (("II",), {}),
        "classify_kd": ((WL, np.array([0.05, 0.06, 0.08])), {}),
        "par_profile": ((SKY.below, SKY.wavelengths, np.array([0.0, 10.0])), dict(kd=jerlov.water("II", source="jerlov1976"), unit="energy")),
        "jerlov1977_quanta": (("II",), {}),
        "tyler1958_radiance": ((41.3,), {}),
        "darecki2011_irradiance_cv": ((), {}),
        "darecki2011_radiance_cv": ((jerlov.DARECKI2011_PANELS[0],), {}),
        "gernez2009_cv_by_sun_zenith": ((), {}),
        "darecki2011_spectral_cv": ((), {}),
        "gernez2009_cv_by": ((jerlov.GERNEZ2009_VARIABLES[0],), {}),
        "gernez2009_spectral_cv": ((), {}),
        "gernez2009_band_cv": ((jerlov.GERNEZ2009_BAND_VARIABLES[0],), {}),
        "gernez2009_diffuse_share": ((), {}),
        "pure_water_absorption": ((WL,), {}),
        "pure_water_absorption_table": ((WL,), dict(source="pope1997")),
        "pure_water_absorption_uncertainty": ((np.array([450.0, 500.0]),), dict(source="pope1997")),
        "petzold_scattering": (("NUC 2240",), {}),
        "forward_scatter": ((P, 1.0), {}),
        "attenuation_within": ((W, WL), dict(forward=FORWARD)),
        "shortwave_parameters": (("II",), {}),
        "solar_fraction": (("II", 10.0), {}),
        "jerlov1968_solar_fraction": (("II",), {}),
        "lee2005_kir": ((1.0,), dict(sun_zenith_deg=30.0)),
        "lee2005_shortwave_transmittance": ((0.03, 0.002, 10.0), dict(sun_zenith_deg=30.0, visible_fraction=0.5)),
        "bb_from_vsf": ((0.001, 117.0, 532.0), dict(salinity_psu=35.0)),
        "particulate_chi": ((117.0,), {}),
        "pure_water_vsf": ((90.0, 500.0), dict(salinity_psu=35.0)),
        "pure_water_backscattering": ((WL,), dict(salinity_psu=35.0)),
        "pure_water_scattering": ((WL,), dict(salinity_psu=35.0)),
        "quan1995_refractive_index": ((WL,), dict(salinity_psu=35.0, temperature_c=20.0)),
        "fournier_forand": ((), dict(refractive_index=1.10, junge_slope=3.5835)),
        "mobley2002_fournier_forand": ((0.0183,), {}),
        "monte_carlo_light_field": ((0.1, 0.3, 500.0), dict(pure_water_b=0.003, salinity_psu=35.0, phase_function=P, station_salinity_psu=35.0, cut_deg=1.0, refractive_index=1.34, sun_zenith_deg=30.0, depth_m=float("inf"), bottom_albedo=None, depths_m=[1.0], slab_m=1.0, zenith_step_deg=10.0, azimuth_step_deg=45.0, photons=200, batches=2, seed=0)),
        "kd_spectrum": ((0.05, 490.0, WL), {}),
        "k_from_secchi": ((10.0,), dict(coefficient=1.44)),
        "b_from_c": ((np.array([0.3, 0.25, 0.2]), WL), dict(bw=np.array([0.004, 0.003, 0.002]), cw=np.array([0.02, 0.03, 0.06]))),
        "measured_points": (("II", "a"), {}),
        "visual_pigment_template": ((WL,), dict(lambda_max=500.0, chromophore="A1")),
        "receptor_noise_distance": ((np.array([1.0, 2.0]), np.array([1.1, 2.1])), dict(noise=np.array([0.05, 0.05]))),
        "morel1988_kd": ((WL,), dict(pigment_mg_m3=0.3)),
        "morel2007_stations": ((), {}),
        "morel2002_nadir_fq": ((560.0,), dict(chlorophyll_mg_m3=0.3, sun_zenith_deg=30.0)),
        "morel2001_kd": ((WL,), dict(chlorophyll_mg_m3=0.3)),
        "morel2001_bbp": ((WL,), dict(chlorophyll_mg_m3=0.3)),
        "bricaud1995_aph": ((WL,), dict(chlorophyll_mg_m3=0.3)),
        "gordon1989_d0": ((30.0,), dict(direct_fraction=0.8)),
        "gordon1989_kd": ((np.array([0.05, 0.06]),), dict(d0_from=1.1, d0_to=1.2)),
        "lee2005_kd": ((np.array([0.03, 0.05]), np.array([0.002, 0.002])), dict(sun_zenith_deg=30.0)),
        "lee2005_kvis": ((0.03, 0.002, 10.0), dict(sun_zenith_deg=30.0)),
        "lee2007_depth_of_fraction": ((0.03, 0.002), dict(sun_zenith_deg=30.0, fraction=0.01)),
        "lee2013_kd": ((np.array([0.03, 0.05]), np.array([0.002, 0.002])), dict(bb_water=np.array([0.0015, 0.001]), sun_zenith_deg=30.0)),
        "subsurface_rrs": ((np.array([0.03, 0.05]), np.array([0.002, 0.002])), dict(coefficients=jerlov.GORDON1988_RRS_COEFFICIENTS)),
        "above_surface_rrs": ((np.array([0.004, 0.003]),), {}),
        "mobley_rho": ((), dict(source="mobley1999", wind_speed=5.0, sun_zenith_deg=30.0, view_nadir_deg=40.0, view_azimuth_deg=135.0)),
        "rottgers2013_scatter_correction": ((np.array([0.1, 0.05]), np.array([0.3, 0.2]), 0.01, 0.1), dict(method="flat")),
        "rottgers2013_a715": ((0.01,), {}),
        "rrs_from_above_water": ((np.array([0.01, 0.01]), np.array([0.05, 0.05]), np.array([1.0, 1.0])), dict(rho=0.028)),
        "lee2011_rrs": ((np.array([0.03, 0.05]), np.array([0.002, 0.002])), dict(bb_water=np.array([0.0015, 0.001]), coefficients=next(iter(jerlov.LEE2011_RRS_COEFFICIENTS.values())))),
        "lee1999_shallow_rrs": ((np.array([0.03, 0.05]), np.array([0.002, 0.002])), dict(depth_m=5.0, bottom_albedo=0.3, sun_zenith_deg=30.0)),
        "lee2015_secchi_depth": ((WL, np.array([0.05, 0.06, 0.08]), np.array([0.005, 0.004, 0.002])), {}),
        "qaa_ioccg2006": ((R5_NM, R5_RRS), dict(bands={"410": 410, "440": 440, "490": 490, "510": 510, "555": 555, "670": 670}, pure_water=V6_WATER5)),
        "lee2013_raman_correction": ((np.array([412.0, 443.0, 488.0, 531.0, 551.0, 667.0]), np.array([0.0080, 0.0070, 0.0050, 0.0025, 0.0018, 0.0002])), dict(bands={"440": 443.0, "550": 551.0})),
        "qaa_v6": ((V6_NM, V6_RRS), dict(bands={"412": 412, "443": 443, "490": 489, "55x": 555, "670": 670}, pure_water=V6_WATER)),
        "gregg1990_irradiance": ((WL,), G),
        "rgb_attenuation": ((W,), dict(colour_space="linear_srgb", illuminant=jerlov.d65(), distance_range_m=(0.5, 3.0))),
        "henyey_greenstein_fit": ((P,), dict(method="backscatter_ratio")),
        "spectral_coefficients": ((W,), dict(range_nm=(400.0, 700.0))),
        "rgb_transmittance": ((W, np.array([1.0, 5.0])), dict(colour_space="linear_srgb", illuminant=jerlov.d65())),
        "usgs2017_reflectance": ((jerlov.USGS2017_MATERIALS[0],), {}),
        "osoaa_user_profile": ((WS, 500.0), dict(depths_m=np.array([0.0, 10.0]), pure_water=(0.0204, 0.0034))),
        "osoaa_phase_function": ((P,), dict(minus_f12_over_f11=0.0, f22_over_f11=1.0, f33_over_f11=1.0)),
        "hydrolight_ac9_file": ((jerlov.water("III"), HWL), dict(depths_m=np.array([0.0, 10.0]), pure_water=(A_W, B_W))),
        "read_osoaa_flux": ((RUN("Flux.txt"),), {}),
        "read_osoaa_radiance_vs_depth": ((RUN("RESLUM_vsZ.txt"),), {}),
        "read_osoaa_radiance_vs_vza": ((RUN("RESLUM_vsVZA.txt"),), {}),
    }


CALLS = calls()


def _numeric(value):
    if isinstance(value, (bool, np.bool_)):
        return False
    if isinstance(value, (int, float, np.integer, np.floating)):
        return True
    return isinstance(value, np.ndarray) and value.dtype.kind in "fi"


def _cases():
    for name, (args, kwargs) in CALLS.items():
        for i, value in enumerate(args):
            if _numeric(value):
                yield name, i, None
        for key, value in kwargs.items():
            if _numeric(value):
                yield name, None, key


def _call(name, args, kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return getattr(jerlov, name)(*args, **kwargs)


def test_the_table_covers_every_public_function():
    functions = {n for n in jerlov.__all__
                 if inspect.isfunction(getattr(jerlov, n))}
    assert functions - set(CALLS) == {"morel2002_fq_tables"}
    for name, (args, kwargs) in CALLS.items():
        _call(name, args, kwargs)        # the valid call works


@pytest.mark.parametrize("name,position,keyword", list(_cases()))
@pytest.mark.parametrize("bad", ["bool", "text"])
def test_a_bool_or_text_is_refused_where_a_number_is_meant(
        name, position, keyword, bad):
    args, kwargs = CALLS[name]
    args, kwargs = list(args), dict(kwargs)
    value = args[position] if keyword is None else kwargs[keyword]
    if isinstance(value, np.ndarray):
        replacement = (np.ones(value.shape, bool) if bad == "bool"
                       else value.astype(str))
    else:
        replacement = True if bad == "bool" else str(value)
    if keyword is None:
        args[position] = replacement
    else:
        kwargs[keyword] = replacement
    with pytest.raises(ValueError, match="bool" if bad == "bool" else "text"):
        _call(name, args, kwargs)


def test_every_public_function_and_method_is_checked():
    for name in jerlov.__all__:
        obj = getattr(jerlov, name)
        if inspect.isfunction(obj):
            assert getattr(obj, "_jerlov_checked", False), name
            module = __import__(obj.__module__, fromlist=["_"])
            assert getattr(module, name) is obj, name
        elif inspect.isclass(obj) and not issubclass(obj, BaseException):
            for attr, value in vars(obj).items():
                if not attr.startswith("_") and inspect.isfunction(value):
                    assert getattr(value, "_jerlov_checked", False), \
                        f"{name}.{attr}"


def test_methods_refuse_a_bool_and_text_too():
    water = jerlov.water("II")
    for bad in (True, "500", np.array([True]), np.array(["500"])):
        with pytest.raises(ValueError, match="wl must be"):
            water.a(bad)
    tables = jerlov.shortwave_parameters("II")
    with pytest.raises(ValueError, match="depth_m"):
        tables.fraction_at(True)


def test_switches_and_names_are_still_taken():
    assert jerlov.visual_pigment_template(
        [500.0], lambda_max=500.0, chromophore="A1", beta=False)[0] > 0.99
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.CoverageWarning)
        out = jerlov.spectrum_to_srgb(np.ones(321), np.arange(380.0, 701.0),
                                      white=np.ones(321), clip=False)
    assert np.allclose(out, 1.0)
    jerlov.measured_points("II", "a", include_sparse=True)
    jerlov.shortwave_parameters("II", include_non_types=True)
    jerlov.classify_kd(WL, np.array([0.05, 0.06, 0.08]), types=["II", "III"])
    # bb_from_vsf's beta is a number, not visual_pigment_template's switch.
    with pytest.raises(ValueError, match="beta must be a number"):
        jerlov.bb_from_vsf(True, 117.0, 532.0, salinity_psu=35.0)


def test_finite_number_refuses_a_bool():
    for bad in (True, False, np.bool_(True)):
        with pytest.raises(ValueError, match="one finite number"):
            _data.finite_number(bad, "x")
    assert _data.finite_number(1, "x") == 1.0


@pytest.mark.parametrize("depth", [np.inf, [1.0, np.inf]])
def test_solar_fraction_refuses_an_infinite_depth(depth):
    with pytest.raises(ValueError, match="finite"):
        jerlov.solar_fraction("II", depth)


def test_empty_and_malformed_inputs_say_what_is_wrong():
    r = jerlov.pure_water_absorption_uncertainty(np.array([]),
                                                 source="pope1997")
    assert r.aw.size == r.uncertainty.size == r.percent_error.size == 0
    assert jerlov.pure_water_absorption_table(
        np.array([]), source="pope1997").size == 0
    with pytest.raises(ValueError, match="wavelengths is empty"):
        jerlov.par_profile(np.ones(3), np.array([]), [0.0, 1.0],
                           kd=jerlov.water("II", source="jerlov1976"),
                           unit="energy")
    with pytest.raises(ValueError, match="axis of three"):
        jerlov.xyz_to_srgb(0.5)
    with pytest.raises(ValueError, match="one-dimensional"):
        jerlov.integrate_response(1.0, 500.0, np.ones(3), WL)


def test_object_arguments_answer_a_name_themselves_and_refuse_a_bool():
    """water, scattering and wind take a name or an object; a bool is
    still refused there (DECISIONS.md section 126)."""
    with pytest.raises(TypeError, match="jerlov.Water"):
        jerlov.rgb_transmittance("III", [1.0], colour_space="acescg",
                                 illuminant=jerlov.d65())
    with pytest.raises(TypeError, match="ScatteringFunction"):
        jerlov.henyey_greenstein_fit("HAOCE 11", method="mean_cosine")
    with pytest.raises(ValueError, match="bool"):
        jerlov.rgb_transmittance(True, [1.0], colour_space="acescg",
                                 illuminant=jerlov.d65())
    with pytest.raises(ValueError, match="bool"):
        jerlov.forward_scatter(False, 5.0)

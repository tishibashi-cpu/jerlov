"""What the review of 1.10.1 found, after its two defects (DECISIONS.md
section 81): results that compare and copy, inputs that cannot be, and
exceptions that say what was wrong."""

from __future__ import annotations

import pickle
import warnings

import numpy as np
import pytest

import jerlov
from jerlov import MissingQuantityError

WL = np.array([450.0, 500.0, 550.0])
ONES = np.ones(3)
SKY = dict(sun_zenith_deg=30.0, day_of_year=100, pressure_hpa=1013.0,
           air_mass_type=1, relative_humidity=80.0,
           precipitable_water_cm=2.0, wind_speed_24h=4.0, wind_speed=5.0,
           ozone_du=300.0, visibility_km=20.0)
V6_BANDS = {"412": 412, "443": 443, "490": 490, "55x": 555, "670": 670}
BANDS_NM = np.array([412.0, 443.0, 490.0, 555.0, 670.0])
RRS = np.array([0.005, 0.004, 0.004, 0.002, 0.0002])
PURE = (np.array([400.0, 700.0]), np.array([0.01, 0.6]),
        np.array([0.003, 0.0003]))


def _water():
    return jerlov.water("II", source="solonenko2015")


def _scene(depth=10.0):
    return jerlov.Scene(_water(), ONES, WL, depth_m=depth)


def _results():
    """One maker for each of the five types, called twice by the tests."""
    return {
        "Backscattering (arrays)": lambda: jerlov.bb_from_vsf(
            [0.002, 0.003], 120, 532, salinity_psu=35.0),
        "Backscattering (numbers)": lambda: jerlov.bb_from_vsf(
            0.002, 120, 532, salinity_psu=35.0),
        "AttenuationCoefficients": lambda: _scene().attenuation_coefficients(
            (0.0, 5.0), veiling_radiance=ONES),
        "AttenuationCoefficients (no B_inf)":
            lambda: _scene().attenuation_coefficients((0.0, 5.0)),
        "QAAResult": lambda: jerlov.qaa_v6(
            BANDS_NM, RRS, bands=V6_BANDS, pure_water=PURE),
        "RamanCorrection": lambda: jerlov.lee2013_raman_correction(
            [443.0, 551.0], [0.005, 0.002], bands={"440": 443, "550": 551}),
        "SurfaceIrradiance": lambda: jerlov.gregg1990_irradiance(WL, **SKY),
        "SurfaceIrradiance (one wavelength)":
            lambda: jerlov.gregg1990_irradiance(500, **SKY),
    }


# -- results compare by value ------------------------------------------------

@pytest.mark.parametrize("name", list(_results()))
def test_two_equal_results_compare_equal_and_hash_alike(name):
    """Up to 1.10.2 the comparison raised "truth value of an array is
    ambiguous" for the ones holding arrays, and hash() failed."""
    make = _results()[name]
    first, second = make(), make()
    assert first is not second
    assert first == second
    assert not (first != second)
    assert hash(first) == hash(second)
    assert len({first, second}) == 1


def test_results_that_differ_compare_unequal():
    a = jerlov.bb_from_vsf([0.002, 0.003], 120, 532, salinity_psu=35.0)
    b = jerlov.bb_from_vsf([0.002, 0.004], 120, 532, salinity_psu=35.0)
    c = jerlov.bb_from_vsf([0.002, 0.003, 0.004], 120, 532, salinity_psu=35.0)
    assert a != b and a != c
    sky = jerlov.gregg1990_irradiance(WL, **SKY)
    other = jerlov.gregg1990_irradiance(WL, **{**SKY, "ozone_du": 350.0})
    assert sky != other
    assert sky != "a string" and sky != a


def test_a_gap_does_not_make_a_result_unequal_to_itself():
    rrs = np.array([np.nan, 0.004, 0.004, 0.002, 0.0002])
    first = jerlov.qaa_v6(BANDS_NM, rrs, bands=V6_BANDS, pure_water=PURE)
    second = jerlov.qaa_v6(BANDS_NM, rrs, bands=V6_BANDS, pure_water=PURE)
    assert np.isnan(first.a).any()
    assert first == second and hash(first) == hash(second)


def test_the_reprs_of_qaa_and_raman_are_one_line():
    q = jerlov.qaa_v6(BANDS_NM, RRS, bands=V6_BANDS, pure_water=PURE)
    assert repr(q) == "<QAAResult v6, 1 spectrum at 5 bands, 412-670 nm>"
    many = jerlov.qaa_v6(BANDS_NM, np.tile(RRS, (3, 1)), bands=V6_BANDS,
                         pure_water=PURE)
    assert "3 spectra" in repr(many)
    r = jerlov.lee2013_raman_correction(
        [443.0, 551.0], [0.005, 0.002], bands={"440": 443, "550": 551})
    assert repr(r).startswith("<RamanCorrection 1 spectrum, 443-551 nm, RF ")
    assert "array(" not in repr(q) + repr(r)
    gap = jerlov.lee2013_raman_correction(
        [443.0, 551.0], [np.nan, np.nan], bands={"440": 443, "550": 551})
    assert "RF undefined" in repr(gap)


# -- results do not share arrays ---------------------------------------------

def test_results_do_not_carry_the_callers_wavelength_array():
    wl = WL.copy()
    sky = jerlov.gregg1990_irradiance(wl, **SKY)
    bands = BANDS_NM.copy()
    v6 = jerlov.qaa_v6(bands, RRS, bands=V6_BANDS, pure_water=PURE)
    r5 = jerlov.qaa_ioccg2006(
        np.array([410.0, 440.0, 490.0, 510.0, 555.0, 670.0]),
        [0.005, 0.004, 0.004, 0.003, 0.002, 0.0002],
        bands={"410": 410, "440": 440, "490": 490, "510": 510, "555": 555,
               "670": 670}, pure_water=PURE)
    assert sky.wavelengths is not wl and v6.wavelengths is not bands
    wl[0] = 0.0
    bands[0] = 0.0
    assert sky.wavelengths[0] == 450.0 and v6.wavelengths[0] == 412.0
    assert r5.wavelengths[0] == 410.0


def test_an_observation_does_not_share_the_scenes_wavelengths():
    scene = _scene()
    obs = scene.observe(ONES * 0.5, 2.0, veiling_radiance=ONES,
                        face_irradiance_ratio=1.0)
    slant = scene.observe_slant(ONES * 0.5, 2.0, target_depth_m=11.0,
                                kd=ONES * 0.05, water_radiance=ONES,
                                radiance_attenuation=0.05,
                                face_irradiance_ratio=1.0)
    att = scene.attenuation_coefficients((0.0, 5.0))
    for result in (obs, slant, att):
        assert result.wavelengths is not scene.wavelengths
        result.wavelengths[0] = 0.0
    assert scene.wavelengths[0] == 450.0


def test_a_scenes_wavelengths_cannot_be_changed_under_its_c():
    scene = _scene()
    with pytest.raises(ValueError, match="read-only"):
        scene.wavelengths[0] = 600.0
    scene.downwelling[0] = 2.0          # nothing is derived from it ahead


# -- a ParProfile can be pickled ---------------------------------------------

def _profiles():
    wl = np.arange(350.0, 701.0, 10.0)
    flat = np.ones_like(wl)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        descent = jerlov.descend("I", 200.0, wl)
    measured = jerlov.Water.from_measurements(
        wl, kd=np.full(wl.shape, 0.05),
        uncertainty={"kd": np.full(wl.shape, 0.005)})
    return {
        "a published type": dict(kd=jerlov.water("II", source="jerlov1976")),
        "a descent": dict(kd=descent),
        "a measured Kd": dict(kd=measured),
        "an array and its uncertainty": dict(
            kd=np.full(wl.shape, 0.07),
            kd_uncertainty=np.full(wl.shape, 0.01)),
        "a weight and another band": dict(
            kd=jerlov.water("II", source="jerlov1976"), photon_weight=flat,
            band=jerlov.QUANTA_BAND_NM),
    }, wl, flat


@pytest.mark.parametrize("name", list(_profiles()[0]))
def test_a_par_profile_survives_pickling(name):
    cases, wl, flat = _profiles()
    p = jerlov.par_profile(flat, wl, [0.0, 10.0, 50.0], unit="energy",
                           **cases[name])
    q = pickle.loads(pickle.dumps(p))
    assert np.array_equal(p.par, q.par)
    assert p.surface_par == q.surface_par and repr(p) == repr(q)
    assert p.depth_of_fraction(0.01) == q.depth_of_fraction(0.01)
    assert p.kd_par(1.0, 20.0) == q.kd_par(1.0, 20.0)
    assert np.array_equal(p.spectrum_at(7.0), q.spectrum_at(7.0))
    try:
        expected = p.depth_of_fraction_bounds(0.01)
    except MissingQuantityError as error:
        with pytest.raises(MissingQuantityError, match=str(error)[:30]):
            q.depth_of_fraction_bounds(0.01)
    else:
        assert q.depth_of_fraction_bounds(0.01) == expected
        for a, b in zip(p.par_bounds(k=2), q.par_bounds(k=2)):
            assert np.array_equal(a, b)


def test_the_uncertainty_refusals_still_name_the_band_and_the_wavelength():
    wl = np.arange(400.0, 701.0, 50.0)
    flat = np.ones_like(wl)
    sigma = np.full(wl.shape, 0.01)
    sigma[2] = np.nan
    p = jerlov.par_profile(flat, wl, [0.0], kd=np.full(wl.shape, 0.05),
                           kd_uncertainty=sigma, unit="photons")
    with pytest.raises(MissingQuantityError, match="between 400 and 700 nm"):
        p.par_bounds()
    p = jerlov.par_profile(flat, wl, [0.0], kd=np.full(wl.shape, 0.05),
                           kd_uncertainty=np.full(wl.shape, 0.03),
                           unit="photons")
    with pytest.raises(ValueError, match="negative at 400 nm"):
        p.par_bounds(k=2)


# -- infinity is refused; NaN still marks a gap ------------------------------

@pytest.mark.parametrize("quantity", ["a", "b", "kd", "kd_hydrolight"])
def test_a_water_refuses_an_infinite_coefficient(quantity):
    values = {"a": ONES.copy(), "b": ONES.copy()}
    values[quantity] = np.array([np.inf, 1.0, 1.0])
    with pytest.raises(ValueError, match="must not be infinite"):
        jerlov.Water(WL, **values)
    if quantity != "kd_hydrolight":
        with pytest.raises(ValueError, match="must not be infinite"):
            jerlov.Water.from_measurements(WL, **values)
    values[quantity] = np.array([np.nan, 1.0, 1.0])     # a gap is welcome
    assert jerlov.Water(WL, **values).has("a")


def test_a_water_refuses_an_infinite_uncertainty():
    with pytest.raises(ValueError, match="negative or infinite"):
        jerlov.Water(WL, kd=ONES, uncertainty={"Kd": [np.inf, 0.0, 0.0]})
    w = jerlov.Water(WL, kd=ONES, uncertainty={"Kd": [np.nan, 0.0, 0.0]})
    assert np.isnan(w.uncertainty("kd", 450.0))


def test_a_scene_refuses_infinite_light():
    w = _water()
    with pytest.raises(ValueError, match="negative or infinite"):
        jerlov.Scene(w, [np.inf, 1.0, 1.0], WL)
    with pytest.raises(ValueError, match="negative or infinite"):
        jerlov.Scene.at_depth(w, 5.0, [np.inf, 1.0, 1.0], WL, kd=ONES * 0.1)
    with pytest.raises(ValueError, match="negative or infinite"):
        jerlov.Scene.at_depth(w, 5.0, [-1.0, 1.0, 1.0], WL, kd=ONES * 0.1)
    with pytest.raises(ValueError, match="negative or infinite"):
        jerlov.veiling_radiance_estimate(w, [np.inf, 1.0, 1.0], WL,
                                         backscatter_ratio=0.02)
    scene = _scene()
    infinite = np.array([np.inf, 1.0, 1.0])
    with pytest.raises(ValueError, match="veiling_radiance"):
        scene.observe(ONES * 0.5, 2.0, veiling_radiance=infinite,
                      face_irradiance_ratio=1.0)
    with pytest.raises(ValueError, match="veiling_radiance"):
        scene.attenuation_coefficients((0.0, 5.0), veiling_radiance=infinite)
    with pytest.raises(ValueError, match="water_radiance"):
        scene.observe_slant(ONES * 0.5, 2.0, target_depth_m=11.0,
                            kd=ONES * 0.05, water_radiance=infinite,
                            radiance_attenuation=0.05,
                            face_irradiance_ratio=1.0)
    # A gap still passes, and stays a gap.
    gap = scene.observe(ONES * 0.5, 2.0,
                        veiling_radiance=[np.nan, 1.0, 1.0],
                        face_irradiance_ratio=1.0)
    assert np.isnan(gap.radiance[0]) and np.all(np.isfinite(gap.radiance[1:]))


def test_contrast_wants_a_radiance_on_the_wavelengths():
    obs = _scene().observe(ONES * 0.5, 2.0, veiling_radiance=ONES * 0.01,
                           face_irradiance_ratio=1.0)
    assert obs.contrast(0.05).shape == (3,)
    assert obs.contrast(ONES * 0.05).shape == (3,)
    for bad in (-1.0, np.inf, [-0.1, 0.1, 0.1]):
        with pytest.raises(ValueError, match="negative or infinite"):
            obs.contrast(bad)
    with pytest.raises(ValueError, match="same shape as wavelengths"):
        obs.contrast([0.1, 0.2])


def test_kd_spectrum_refuses_a_kd_that_cannot_be():
    for bad in (np.inf, -0.01, [0.05, -0.01], [0.05, np.inf]):
        with pytest.raises(ValueError, match="finite and not negative"):
            jerlov.kd_spectrum(bad, 490, 550)
    assert np.isnan(jerlov.kd_spectrum(np.nan, 490, 550))
    # Below pure sea water's is still only a warning, as Jerlov's type I is.
    with pytest.warns(jerlov.ProvenanceWarning, match="below the pure sea"):
        jerlov.kd_spectrum(0.01, 490, 550)


def test_b_from_c_refuses_what_no_water_has():
    with pytest.raises(ValueError, match="c must be finite"):
        jerlov.b_from_c(np.inf, 500, bw=0.002, cw=0.02)
    for bw, cw in ((-5.0, 0.02), (0.002, -0.02), (np.inf, 0.02),
                   (0.002, np.inf)):
        with pytest.raises(ValueError, match="finite and not negative"):
            jerlov.b_from_c(1.0, 500, bw=bw, cw=cw)
    assert np.isnan(jerlov.b_from_c(np.nan, 500, bw=0.002, cw=0.02))
    assert jerlov.b_from_c(1.0, 500, bw=0.0, cw=0.0) > 0


def test_scattering_functions_refuse_what_cannot_be():
    with pytest.raises(ValueError, match="negative or infinite"):
        jerlov.bb_from_vsf(np.inf, 120, 532, salinity_psu=35.0)
    for bad in (np.nan, np.inf, -1.0, 180.5, [90.0, 400.0]):
        with pytest.raises(ValueError, match="0-180 degrees"):
            jerlov.pure_water_vsf(bad, 500, salinity_psu=35.0)
    for fine in (0.0, 90.0, 180.0):
        assert jerlov.pure_water_vsf(fine, 500, salinity_psu=35.0) > 0


def test_colour_refuses_infinity_and_keeps_a_gap():
    with pytest.raises(ValueError, match="must not be infinite"):
        jerlov.xyz_to_srgb([np.inf, 1.0, 1.0])
    assert np.all(np.isnan(jerlov.xyz_to_srgb([np.nan, 1.0, 1.0])))
    grid = [400.0, 500.0, 600.0]
    with pytest.raises(ValueError, match="must not be infinite"):
        jerlov.integrate_response([1.0, np.inf, 1.0], grid, [1, 1, 1], grid)
    with pytest.raises(ValueError, match="must not be infinite"):
        jerlov.integrate_response([1.0, 1.0, 1.0], grid, [1, np.inf, 1], grid)
    assert np.isnan(jerlov.integrate_response(
        [1.0, np.nan, 1.0], grid, [1, 1, 1], grid)).all()


# -- exceptions that say what was wrong --------------------------------------

def test_the_aerosol_follows_the_rule_for_a_choice_of_two():
    """MissingQuantityError for neither, ValueError for both, as Water.bb's
    two ratios; TypeError for either up to 1.10.2."""
    neither = {k: v for k, v in SKY.items() if k != "visibility_km"}
    with pytest.raises(MissingQuantityError, match="exactly one"):
        jerlov.gregg1990_irradiance(500, **neither)
    with pytest.raises(ValueError, match="not both"):
        jerlov.gregg1990_irradiance(
            500, **SKY, aerosol_optical_thickness_550=0.2)
    assert not issubclass(MissingQuantityError, (TypeError, ValueError))


def test_text_for_a_number_is_a_value_error():
    with pytest.raises(ValueError, match="sun_zenith_deg"):
        jerlov.gregg1990_irradiance(500, **{**SKY, "sun_zenith_deg": "30"})
    for function in (jerlov.morel2001_kd, jerlov.morel2001_bbp,
                     jerlov.bricaud1995_aph):
        with pytest.raises(ValueError, match="chlorophyll_mg_m3"):
            function(500, chlorophyll_mg_m3="1")
    with pytest.raises(ValueError, match="lambda_max"):
        jerlov.visual_pigment_template(500, lambda_max="500",
                                       chromophore="A1")


def test_an_unknown_tyler_depth_is_a_key_error_whatever_it_is():
    for bad in ("abc", None, 5.0):
        with pytest.raises(KeyError, match="no table"):
            jerlov.tyler1958_radiance(bad)


def test_vsf_at_says_what_shape_it_wants():
    station = jerlov.petzold_scattering("AUTEC 8")
    with pytest.raises(ValueError, match="1-D array"):
        station.vsf_at([[1.0, 2.0], [3.0, 4.0]])
    assert station.vsf_at([1.0, 2.0]).shape == (2,)


def test_descend_names_the_type_a_source_lacks():
    """A KeyError, which the docstring now lists: Austin & Petzold stop at
    1C, and the profile below 3C passes through 3C itself."""
    with pytest.raises(KeyError, match="does not cover"):
        jerlov.descend("3C", 5.0, [500.0], source="austin1986")

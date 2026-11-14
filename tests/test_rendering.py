"""Coefficients for renderers: RGB, a Henyey-Greenstein g, and spectra
(DECISIONS.md section 82)."""

from __future__ import annotations

import json
import math
import warnings

import numpy as np
import pytest

import jerlov
from jerlov import rendering
from jerlov.colour import XYZ_TO_LINEAR_SRGB, _xy_to_xyz


def _quiet(function, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        warnings.simplefilter("ignore", jerlov.CoverageWarning)
        return function(*args, **kwargs)


def _flat_water(c=0.3, a=0.1):
    wl = np.arange(300.0, 851.0, 5.0)
    return jerlov.Water.from_measurements(
        wl, a=np.full(wl.shape, a), b=np.full(wl.shape, c - a), name="flat")


ARGS = dict(colour_space="acescg", illuminant=jerlov.d65(),
            distance_range_m=(0.5, 10.0))


# -- the colour spaces --------------------------------------------------------

@pytest.mark.parametrize("space", jerlov.RGB_COLOUR_SPACES)
def test_each_matrix_maps_its_primaries_and_white(space):
    primaries, white, _ = rendering._SPACES[space]
    m = rendering._xyz_to_rgb(space)
    white_xyz = _xy_to_xyz(np.array(white))
    np.testing.assert_allclose(m @ white_xyz, [1, 1, 1], atol=1e-12)
    for k, xy in enumerate(primaries):
        rgb = m @ _xy_to_xyz(np.array(xy))
        rgb = rgb / rgb[k]
        np.testing.assert_allclose(rgb, np.eye(3)[k], atol=1e-12)


def test_linear_srgb_is_the_packages_own_matrix():
    np.testing.assert_allclose(rendering._xyz_to_rgb("linear_srgb"),
                               XYZ_TO_LINEAR_SRGB, rtol=0, atol=1e-15)


def test_the_spaces_as_printed():
    """ACEScg: the Academy's ACEScg specification; Rec. 2020: ITU-R
    BT.2020-2 (10/2015), Table 3, p. 3."""
    assert rendering._SPACES["acescg"][:2] == (
        ((0.713, 0.293), (0.165, 0.830), (0.128, 0.044)), (0.32168, 0.33767))
    assert rendering._SPACES["rec2020"][:2] == (
        ((0.708, 0.292), (0.170, 0.797), (0.131, 0.046)), (0.3127, 0.3290))
    assert jerlov.RGB_COLOUR_SPACES == ("linear_srgb", "acescg", "rec2020")


# -- rgb_attenuation ------------------------------------------------------------

@pytest.mark.parametrize("space", jerlov.RGB_COLOUR_SPACES)
def test_a_grey_water_gives_its_own_coefficients_exactly(space):
    water = _flat_water(c=0.3, a=0.1)
    out = jerlov.rgb_attenuation(water, colour_space=space,
                                 illuminant=jerlov.d65(),
                                 distance_range_m=(0.0, 25.0))
    np.testing.assert_allclose(out.sigma_t, 0.3, rtol=1e-12)
    np.testing.assert_allclose(out.sigma_a, 0.1, rtol=1e-12)
    np.testing.assert_allclose(out.sigma_s, 0.2, rtol=1e-11)
    np.testing.assert_allclose(out.albedo, 2 / 3, rtol=1e-11)
    assert np.all(out.max_relative_error_t < 1e-12)
    assert np.all(out.max_relative_error_a < 1e-12)


def test_against_a_direct_sum_over_the_spectrum():
    water = jerlov.water("III")
    out = _quiet(jerlov.rgb_attenuation, water, **ARGS)
    wl = np.arange(out.wavelength_range_nm[0],
                   out.wavelength_range_nm[1] + 1)
    cmf_wl, cmf = jerlov.cie_1931_cmf()
    d_wl, d = jerlov.d65()
    light = np.interp(wl, d_wl, d)
    c = _quiet(water.c, wl)
    m = rendering._xyz_to_rgb("acescg")
    bar = np.stack([np.interp(wl, cmf_wl, cmf[:, k]) for k in range(3)], 1)

    def rgb(spectrum):
        y = spectrum[:, None] * bar
        xyz = ((y[1:] + y[:-1]) / 2 * np.diff(wl)[:, None]).sum(0)
        return m @ xyz

    r = np.linspace(0.5, 10.0, 201)
    t = np.array([rgb(light * np.exp(-c * x)) / rgb(light) for x in r])
    sigma = np.array([np.polyfit(r, np.log(t[:, k]), 1, w=None)[0]
                      for k in range(3)])
    # The package fits through T = 1 at r = 0; a free intercept does not.
    through_origin = -(r[:, None] * np.log(t)).sum(0) / (r * r).sum()
    np.testing.assert_allclose(out.sigma_t, through_origin, rtol=1e-12)
    assert not np.allclose(-sigma, through_origin, rtol=1e-6)
    error = np.abs(np.exp(-np.outer(r, through_origin)) / t - 1).max(0)
    np.testing.assert_allclose(out.max_relative_error_t, error, rtol=1e-10)


def test_the_coefficients_add_up_and_are_read_only():
    out = _quiet(jerlov.rgb_attenuation, jerlov.water("1C"), **ARGS)
    np.testing.assert_array_equal(out.sigma_s, out.sigma_t - out.sigma_a)
    for name in ("sigma_t", "sigma_a", "sigma_s", "illuminant_rgb",
                 "max_relative_error_t", "max_relative_error_a"):
        with pytest.raises(ValueError):
            getattr(out, name)[0] = 0.0
    assert out.water == "Jerlov 1C"
    assert "Williamson" in out.source
    assert out == _quiet(jerlov.rgb_attenuation, jerlov.water("1C"), **ARGS)


def test_d65_is_white_in_linear_srgb():
    """D65 is the sRGB white, so its RGB there is (1, 1, 1) to within the
    difference between the tabulated D65 and its defined chromaticity."""
    out = _quiet(jerlov.rgb_attenuation, jerlov.water("III"),
                 colour_space="linear_srgb", illuminant=jerlov.d65(),
                 distance_range_m=(0.5, 5.0))
    np.testing.assert_allclose(out.illuminant_rgb, 1.0, atol=5e-4)


def test_a_channel_that_turns_negative_is_refused_where_it_does():
    water = jerlov.water("IB")
    kwargs = dict(colour_space="linear_srgb", illuminant=jerlov.d65())
    with pytest.raises(ValueError, match="red channel") as info:
        _quiet(jerlov.rgb_attenuation, water, distance_range_m=(0.5, 20.0),
               **kwargs)
    reach = float(str(info.value).split("up to about ")[1].split(" m")[0])
    # Just inside the reported distance it works; just past it, not.
    _quiet(jerlov.rgb_attenuation, water,
           distance_range_m=(0.5, reach * 0.99), **kwargs)
    with pytest.raises(ValueError, match="red channel"):
        _quiet(jerlov.rgb_attenuation, water,
               distance_range_m=(0.5, reach * 1.01), **kwargs)
    # A wider space keeps it positive.
    _quiet(jerlov.rgb_attenuation, water, colour_space="acescg",
           illuminant=jerlov.d65(), distance_range_m=(0.5, 20.0))


def test_a_channel_that_grows_is_refused():
    """Absorbing only where the red matching function of sRGB is negative
    makes the red channel grow across the water."""
    wl = np.arange(300.0, 851.0)
    a = np.where((wl >= 470) & (wl <= 520), 5.0, 1e-4)
    water = jerlov.Water.from_measurements(
        wl, a=a, b=np.full(wl.shape, 1e-3), name="notch")
    with pytest.raises(ValueError, match="not positive in the red channel"):
        jerlov.rgb_attenuation(water, colour_space="linear_srgb",
                               illuminant=jerlov.d65(),
                               distance_range_m=(0.5, 10.0))


def test_warnings_come_from_the_water():
    with pytest.warns(jerlov.ProvenanceWarning):
        jerlov.rgb_attenuation(jerlov.water("III"), **ARGS)
    # Solonenko & Mobley stop at 700 nm, short of the observer.
    with pytest.warns(jerlov.CoverageWarning):
        _quiet_provenance(jerlov.rgb_attenuation,
                          jerlov.water("III", source="solonenko2015"), **ARGS)


def _quiet_provenance(function, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        return function(*args, **kwargs)


def test_a_gap_is_refused():
    water = jerlov.water("5C", source="solonenko2015")
    with pytest.raises(ValueError, match="gap"):
        _quiet(jerlov.rgb_attenuation, water, **ARGS)


@pytest.mark.parametrize("change, message", [
    (dict(colour_space=None), "no default"),
    (dict(colour_space="srgb"), "unknown colour_space"),
    (dict(illuminant=None), "no default"),
    (dict(illuminant=np.ones(5)), "pair"),
    (dict(illuminant=([400.0, 500.0], [1.0])), "same length"),
    (dict(illuminant=([400.0, 500.0], [1.0, np.nan])), "finite"),
    (dict(illuminant=([400.0, 500.0], [1.0, np.inf])), "finite"),
    (dict(illuminant=([500.0, 400.0], [1.0, 1.0])), "ascending"),
    (dict(illuminant=([400.0, 500.0], [1.0, -1.0])), "negative"),
    (dict(illuminant=([200.0, 300.0], [1.0, 1.0])), "do not overlap"),
    (dict(illuminant=([400.0, 700.0], [0.0, 0.0])), "no positive power"),
    (dict(distance_range_m=None), "no default"),
    (dict(distance_range_m=5.0), "pair"),
    (dict(distance_range_m=(1.0, 1.0)), "near < far"),
    (dict(distance_range_m=(-1.0, 1.0)), "near < far"),
    (dict(distance_range_m=(0.0, np.inf)), "finite"),
    (dict(distance_range_m=(np.nan, 1.0)), "NaN"),
])
def test_rgb_inputs_are_checked(change, message):
    with pytest.raises(ValueError, match=message):
        _quiet(jerlov.rgb_attenuation, jerlov.water("III"),
               **{**ARGS, **change})


def test_rgb_needs_a_water_with_a_and_b():
    with pytest.raises(TypeError, match="jerlov.Water"):
        jerlov.rgb_attenuation("III", **ARGS)
    kd_only = jerlov.Water.from_measurements([400.0, 700.0], kd=[0.1, 0.5])
    with pytest.raises(jerlov.MissingQuantityError):
        jerlov.rgb_attenuation(kd_only, **ARGS)
    with pytest.raises(TypeError):
        jerlov.rgb_attenuation(jerlov.water("III"), colour_space="acescg")


def test_rgb_as_dict_is_json():
    out = _quiet(jerlov.rgb_attenuation, jerlov.water("III"), **ARGS)
    d = json.loads(json.dumps(out.as_dict(), allow_nan=False))
    assert d["colour_space"]["name"] == "acescg"
    assert d["colour_space"]["white_xy"] == [0.32168, 0.33767]
    assert d["units"] == "1/m"
    assert d["sigma_t"] == out.sigma_t.tolist()
    assert d["distance_range_m"] == [0.5, 10.0]


# -- Henyey-Greenstein ----------------------------------------------------------

def _integrated_backscatter(g):
    theta = np.linspace(np.pi / 2, np.pi, 200001)
    p = (1 - g * g) / (4 * np.pi * (1 + g * g - 2 * g * np.cos(theta)) ** 1.5)
    y = p * np.sin(theta)
    return 2 * np.pi * float(((y[1:] + y[:-1]) / 2 * np.diff(theta)).sum())


@pytest.mark.parametrize("g", [0.0, 0.1, 0.5, 0.8, 0.9, 0.95])
def test_hg_backscatter_closed_form(g):
    assert rendering._hg_backscatter(g) == pytest.approx(
        _integrated_backscatter(g), rel=1e-6)


@pytest.mark.parametrize("station", jerlov.PETZOLD_STATIONS)
def test_backscatter_method_reproduces_each_stations_ratio(station):
    f = jerlov.petzold_scattering(station)
    with warnings.catch_warnings():
        warnings.simplefilter("error")      # this method does not warn
        fit = jerlov.henyey_greenstein_fit(f, method="backscatter_ratio")
    assert fit.backscatter_ratio == pytest.approx(f.backscatter_ratio,
                                                  rel=1e-9)
    assert fit.measured_backscatter_ratio == f.backscatter_ratio
    assert 0.8 < fit.g < 0.95
    assert fit.wavelength_nm == 530.0
    np.testing.assert_array_equal(fit.angles_deg, f.angles_deg)
    # HG falls short at small angles at every station.
    assert fit.log_ratio[0] < -3


@pytest.mark.parametrize("station", jerlov.PETZOLD_STATIONS)
def test_the_integral_is_the_reports(station):
    """The power law between printed angles, integrated, plus the share
    below 0.1 degree, gives back the printed s."""
    f = jerlov.petzold_scattering(station)
    s = f._integral(np.ones_like) + f.fraction_below_0_1_deg * f.b
    assert s == pytest.approx(f.b, rel=0.01)


@pytest.mark.parametrize("station", jerlov.PETZOLD_STATIONS)
def test_mean_cosine_method_warns_and_backscatters_less(station):
    f = jerlov.petzold_scattering(station)
    with pytest.warns(jerlov.ProvenanceWarning, match="below 0.1 degree"):
        fit = jerlov.henyey_greenstein_fit(f, method="mean_cosine")
    with pytest.warns(jerlov.ProvenanceWarning):
        assert fit.g == f.mean_cosine()
    by_ratio = jerlov.henyey_greenstein_fit(f, method="backscatter_ratio")
    assert fit.g > by_ratio.g
    assert fit.backscatter_ratio < f.backscatter_ratio


def test_hg_inputs_are_checked():
    f = jerlov.petzold_scattering("HAOCE 11")
    with pytest.raises(ValueError, match="no default"):
        jerlov.henyey_greenstein_fit(f, method=None)
    with pytest.raises(ValueError, match="unknown method"):
        jerlov.henyey_greenstein_fit(f, method="g")
    with pytest.raises(TypeError):
        jerlov.henyey_greenstein_fit(f)
    with pytest.raises(TypeError, match="ScatteringFunction"):
        jerlov.henyey_greenstein_fit("HAOCE 11", method="mean_cosine")


def test_hg_as_dict_is_json():
    fit = jerlov.henyey_greenstein_fit(jerlov.petzold_scattering("AUTEC 7"),
                                       method="backscatter_ratio")
    d = json.loads(json.dumps(fit.as_dict(), allow_nan=False))
    assert d["g"] == fit.g and d["method"] == "backscatter_ratio"
    assert len(d["log_ratio"]) == 55


# -- spectra --------------------------------------------------------------------

def test_spectra_are_the_waters_own_values():
    water = jerlov.water("III")
    out = _quiet(jerlov.spectral_coefficients, water, range_nm=(400, 700))
    np.testing.assert_array_equal(out.wavelengths,
                                  np.arange(400.0, 701.0))
    np.testing.assert_array_equal(out.a, _quiet(water.a, out.wavelengths))
    np.testing.assert_array_equal(out.b, _quiet(water.b, out.wavelengths))
    np.testing.assert_array_equal(out.c, _quiet(water.c, out.wavelengths))
    assert len(out.a_status) == len(out.b_status) == 301
    # Williamson & Hollins model their values outside 412-715 nm.
    assert out.a_status[0] != "ok" and out.a_status[150] == "ok"


def test_spectra_keep_a_sources_spacing_and_its_gaps():
    water = jerlov.water("5C", source="solonenko2015")
    out = _quiet(jerlov.spectral_coefficients, water, range_nm=(350, 700))
    np.testing.assert_array_equal(
        out.wavelengths, water.wavelengths[water.wavelengths >= 350])
    gaps = np.isnan(out.c)
    assert gaps.any()
    d = json.loads(json.dumps(out.as_dict(), allow_nan=False))
    assert [v is None for v in d["c"]] == gaps.tolist()


def test_spectra_warn_for_flagged_values():
    with pytest.warns(jerlov.ProvenanceWarning):
        jerlov.spectral_coefficients(jerlov.water("III"),
                                     range_nm=(400, 450))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        jerlov.spectral_coefficients(jerlov.water("III"),
                                     range_nm=(450, 700))


@pytest.mark.parametrize("range_nm, message", [
    (None, "no default"),
    (500.0, "pair"),
    ((250.0, 500.0), "inside"),
    ((500.0, 400.0), "inside"),
    ((500.0, np.inf), "inside"),
    ((np.nan, 500.0), "NaN"),
    ((500.0, 500.5), "at least two"),
])
def test_spectral_inputs_are_checked(range_nm, message):
    with pytest.raises(ValueError, match=message):
        _quiet(jerlov.spectral_coefficients, jerlov.water("III"),
               range_nm=range_nm)


def test_spectra_need_a_and_b():
    kd_only = jerlov.Water.from_measurements([400.0, 700.0], kd=[0.1, 0.5])
    with pytest.raises(jerlov.MissingQuantityError):
        jerlov.spectral_coefficients(kd_only, range_nm=(400, 700))
    with pytest.raises(TypeError, match="jerlov.Water"):
        jerlov.spectral_coefficients(None, range_nm=(400, 700))


def test_a_caller_water_has_no_citation():
    water = _flat_water()
    out = jerlov.spectral_coefficients(water, range_nm=(400, 700))
    assert out.source == "" and out.water == "'flat'"
    assert set(out.a_status) == {"ok"}
    assert math.isclose(float(out.albedo[0]), 2 / 3)


# -- rgb_transmittance (DECISIONS.md section 84) -------------------------------

#: rgb_attenuation's results recorded in 1.11.1, before its transmittance
#: moved into the helper rgb_transmittance shares with it: sigma_t,
#: sigma_a, both errors and the illuminant's RGB, as hexadecimal floats.
RECORDED_1_11_1 = {
    ("III", "williamson2022", "acescg", (0.5, 10.0)): [
        '0x1.e49c2e858a333p-2', '0x1.861a9c0836143p-2', '0x1.a904e2001fb63p-2',
        '0x1.89387c6e90fe6p-3', '0x1.7cf2700d5bfe1p-4', '0x1.b99ce34d1cd50p-4',
        '0x1.4ed0546295f28p-4', '0x1.525282b091d80p-8', '0x1.47848888a6280p-8',
        '0x1.627bca1734168p-4', '0x1.e820b8cb53d80p-8', '0x1.6360a988f6d00p-9',
        '0x1.f47c6685b51e8p-1', '0x1.00b692621a2d4p+0', '0x1.143c91db83b17p+0'],
    ("1C", "williamson2022", "linear_srgb", (0.5, 10.0)): [
        '0x1.780bab0ffdb2fp-1', '0x1.0cc2389f14932p-1', '0x1.3520332abff34p-1',
        '0x1.7718ce5b51024p-2', '0x1.891638f9c7a39p-4', '0x1.2b180bfe25e4ap-3',
        '0x1.d7167d1f09550p-4', '0x1.62b15b78a1380p-7', '0x1.1de43f93d9800p-10',
        '0x1.b3065cac2f7e8p-1', '0x1.298ceae9f6980p-7', '0x1.7cb59a2553a00p-10',
        '0x1.000a232fec10dp+0', '0x1.fffd2b95ed7bep-1', '0x1.ffe0505dd5ab0p-1'],
    ("IB", "williamson2022", "rec2020", (0.0, 25.0)): [
        '0x1.103541a38ded4p-2', '0x1.80381acd6dfafp-3', '0x1.63f20c45acd98p-3',
        '0x1.277e72047711bp-3', '0x1.079c5863e8664p-4', '0x1.46e1323ce7ce4p-5',
        '0x1.fa2cc3bb041c0p-3', '0x1.15318a3b94aa0p-5', '0x1.2f0d754ad5c00p-10',
        '0x1.0d415a67becd0p-2', '0x1.3ab6112e59670p-5', '0x1.bdc58cef2e800p-11',
        '0x1.0005354ac1ff0p+0', '0x1.fffe705879d5ep-1', '0x1.ffe3b4944529bp-1'],
    ("III", "solonenko2015", "acescg", (1.0, 5.0)): [
        '0x1.0ede2a33e5ea1p+0', '0x1.0ff21a17bf7e4p+0', '0x1.5f731d92c3f93p+0',
        '0x1.8e12304e9bb9ap-3', '0x1.217fbc4f7a381p-4', '0x1.45bd51b338b91p-5',
        '0x1.78468bfaa46c0p-7', '0x1.df0173334d800p-10', '0x1.5e8f287b200e0p-5',
        '0x1.a5bcbe132c6e0p-6', '0x1.1770fa13e6d00p-8', '0x1.8ef81a88e9800p-12',
        '0x1.f3d419617a5d4p-1', '0x1.00d66013dc0edp+0', '0x1.1457f36516daap+0'],
}


@pytest.mark.parametrize("case", sorted(RECORDED_1_11_1))
def test_rgb_attenuation_is_unchanged_bit_for_bit(case):
    water_type, source, space, distances = case
    out = _quiet(jerlov.rgb_attenuation, jerlov.water(water_type,
                                                      source=source),
                 colour_space=space, illuminant=jerlov.d65(),
                 distance_range_m=distances)
    got = [float(v).hex() for array in (
        out.sigma_t, out.sigma_a, out.max_relative_error_t,
        out.max_relative_error_a, out.illuminant_rgb) for v in array]
    assert got == RECORDED_1_11_1[case]


@pytest.mark.parametrize("space", jerlov.RGB_COLOUR_SPACES)
def test_a_grey_water_transmits_exp_minus_c_r(space):
    r = np.array([0.0, 0.5, 3.0, 25.0])
    out = jerlov.rgb_transmittance(_flat_water(c=0.3, a=0.1), r,
                                   colour_space=space,
                                   illuminant=jerlov.d65())
    np.testing.assert_allclose(out.transmittance,
                               np.exp(-0.3 * r)[:, None] * np.ones(3),
                               rtol=1e-12)


def test_the_fit_departs_from_the_table_by_the_reported_error():
    water = jerlov.water("III")
    fit = _quiet(jerlov.rgb_attenuation, water, **ARGS)
    r = np.linspace(*ARGS["distance_range_m"], 201)
    table = _quiet(jerlov.rgb_transmittance, water, r,
                   colour_space=ARGS["colour_space"],
                   illuminant=ARGS["illuminant"])
    departure = np.abs(np.exp(-np.outer(r, fit.sigma_t))
                       / table.transmittance - 1).max(axis=0)
    np.testing.assert_allclose(departure, fit.max_relative_error_t,
                               rtol=1e-12)
    np.testing.assert_array_equal(table.illuminant_rgb, fit.illuminant_rgb)
    assert table.wavelength_range_nm == fit.wavelength_range_nm


def test_the_table_keeps_the_shape_asked_for():
    kwargs = dict(colour_space="acescg", illuminant=jerlov.d65())
    water = jerlov.water("1C")
    one = _quiet(jerlov.rgb_transmittance, water, 2.0, **kwargs)
    assert one.transmittance.shape == (3,)
    grid = np.array([[0.0, 1.0], [5.0, 2.0]])
    table = _quiet(jerlov.rgb_transmittance, water, grid, **kwargs)
    assert table.transmittance.shape == (2, 2, 3)
    # 1 to rounding: R_k(S) is taken once, through integrate_response, as
    # rgb_attenuation takes it, and the table by the same sum another way.
    np.testing.assert_allclose(table.transmittance[0, 0], 1.0, rtol=1e-13)
    np.testing.assert_array_equal(table.transmittance[1, 1],
                                  _quiet(jerlov.rgb_transmittance, water,
                                         [2.0], **kwargs).transmittance[0])
    with pytest.raises(ValueError):
        table.transmittance[0, 0, 0] = 0.0
    d = json.loads(json.dumps(table.as_dict(), allow_nan=False))
    assert d["distances_m"] == grid.tolist()
    assert np.array(d["transmittance"]).shape == (2, 2, 3)


def test_a_negative_channel_is_refused_where_it_turns():
    water = jerlov.water("IB")
    kwargs = dict(colour_space="linear_srgb", illuminant=jerlov.d65())
    with pytest.raises(ValueError, match="red channel") as info:
        _quiet(jerlov.rgb_transmittance, water, [1.0, 20.0], **kwargs)
    reach = float(str(info.value).split("up to about ")[1].split(" m")[0])
    _quiet(jerlov.rgb_transmittance, water, [reach * 0.99], **kwargs)
    with pytest.raises(ValueError, match="red channel"):
        _quiet(jerlov.rgb_transmittance, water, [reach * 1.01], **kwargs)


@pytest.mark.parametrize("distances, message", [
    (None, "no default"), ("far", "numbers"), ([1.0, np.nan], "NaN"),
    ([1.0, np.inf], "finite"), ([-1.0], "negative"), ([], "empty"),
])
def test_transmittance_inputs_are_checked(distances, message):
    with pytest.raises(ValueError, match=message):
        _quiet(jerlov.rgb_transmittance, jerlov.water("III"), distances,
               colour_space="acescg", illuminant=jerlov.d65())


def test_transmittance_needs_its_arguments():
    with pytest.raises(ValueError, match="no default"):
        jerlov.rgb_transmittance(jerlov.water("III"), [1.0],
                                 colour_space=None, illuminant=jerlov.d65())
    with pytest.raises(TypeError):
        jerlov.rgb_transmittance(jerlov.water("III"), [1.0],
                                 colour_space="acescg")
    with pytest.raises(TypeError, match="jerlov.Water"):
        jerlov.rgb_transmittance("III", [1.0], colour_space="acescg",
                                 illuminant=jerlov.d65())
    with pytest.raises(ValueError, match="gap"):
        _quiet(jerlov.rgb_transmittance,
               jerlov.water("5C", source="solonenko2015"), [1.0],
               colour_space="acescg", illuminant=jerlov.d65())

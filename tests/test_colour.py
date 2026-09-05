"""Colorimetry, and the two mistakes it is easy to make silently."""

from __future__ import annotations

import warnings

import numpy as np
import pytest

import uwlight
from uwlight.colour import (
    SRGB_PRIMARIES,
    SRGB_WHITEPOINT_XY,
    XYZ_TO_LINEAR_SRGB,
    CoverageWarning,
    GamutWarning,
    cie_1931_cmf,
    d65,
    integrate_response,
    spectrum_to_srgb,
    spectrum_to_xyz,
    xyz_to_srgb,
)

FULL = np.arange(360.0, 831.0, 1.0)


# -- the reference data --------------------------------------------------


def test_cmf_covers_the_published_range():
    wl, cmf = cie_1931_cmf()
    assert wl[0] == 360 and wl[-1] == 830
    assert cmf.shape == (471, 3)
    assert wl[int(np.argmax(cmf[:, 1]))] == 555  # photopic peak


def test_d65_is_normalised_at_560nm():
    wl, power = d65()
    assert power[int(np.argmin(np.abs(wl - 560)))] == pytest.approx(100.0, abs=0.5)


def test_derived_matrix_matches_the_published_one():
    """IEC 61966-2-1 prints the matrix; we derive it from the primaries."""
    published = np.array([
        [3.2406, -1.5372, -0.4986],
        [-0.9689, 1.8758, 0.0415],
        [0.0557, -0.2040, 1.0570],
    ])
    assert np.allclose(XYZ_TO_LINEAR_SRGB, published, atol=5e-4)


def test_the_white_point_maps_to_equal_rgb():
    wx, wy = SRGB_WHITEPOINT_XY
    white_xyz = np.array([wx / wy, 1.0, (1 - wx - wy) / wy])
    linear = XYZ_TO_LINEAR_SRGB @ white_xyz
    assert np.allclose(linear, 1.0, atol=1e-9)


def test_each_primary_lights_only_its_own_channel():
    for i in range(3):
        x, y = SRGB_PRIMARIES[i]
        xyz = np.array([x / y, 1.0, (1 - x - y) / y])
        linear = XYZ_TO_LINEAR_SRGB @ xyz
        others = [j for j in range(3) if j != i]
        assert linear[i] > 0
        assert np.allclose(linear[others], 0.0, atol=1e-9)


# -- coverage, the silent bias -------------------------------------------


def test_a_narrow_spectrum_warns():
    """450-650 nm looks like a full spectrum but is not."""
    wl = np.arange(450.0, 651.0, 1.0)
    with pytest.warns(CoverageWarning, match="covers only"):
        spectrum_to_xyz(np.ones_like(wl), wl)


def test_a_full_spectrum_does_not_warn():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        spectrum_to_xyz(np.ones_like(FULL), FULL)


def test_the_warning_states_what_was_missed():
    wl = np.arange(500.0, 601.0, 1.0)
    with pytest.warns(CoverageWarning) as caught:
        spectrum_to_xyz(np.ones_like(wl), wl)
    message = str(caught[0].message)
    assert "500-600 nm" in message
    assert "CIE 1931" in message


# -- white, the other one ------------------------------------------------


def test_white_has_no_default():
    with pytest.raises(TypeError):
        spectrum_to_srgb(np.ones_like(FULL), FULL)
    with pytest.raises(ValueError, match="no default"):
        spectrum_to_srgb(np.ones_like(FULL), FULL, white=None)


def _on(grid):
    wl, power = d65()
    return np.interp(grid, wl, power, left=0.0, right=0.0)


def test_any_spectrum_is_white_against_itself():
    for spectrum in (_on(FULL), np.ones_like(FULL), np.exp(-FULL / 500.0)):
        rgb = spectrum_to_srgb(spectrum, FULL, white=spectrum)
        assert np.allclose(rgb, 1.0, atol=1e-9)


def test_a_blue_green_white_still_comes_out_neutral():
    """The point of stating the white: underwater it is not daylight."""
    greenish = _on(FULL) * np.exp(-0.5 * ((FULL - 500) / 120.0) ** 2)
    rgb = spectrum_to_srgb(greenish, FULL, white=greenish)
    assert np.allclose(rgb, 1.0, atol=1e-9)


def test_a_grey_target_stays_grey():
    illumination = _on(FULL)
    rgb = spectrum_to_srgb(0.18 * illumination, FULL, white=illumination)
    assert np.allclose(rgb, rgb[0], atol=1e-9)   # neutral
    assert 0.3 < rgb[0] < 0.7                    # mid grey after the transfer


def test_halving_the_spectrum_darkens_without_shifting_hue():
    illumination = _on(FULL)
    bright = spectrum_to_srgb(0.6 * illumination, FULL, white=illumination)
    dim = spectrum_to_srgb(0.3 * illumination, FULL, white=illumination)
    assert np.all(dim < bright)
    assert np.allclose(dim, dim[0], atol=1e-9)


# -- gamut ---------------------------------------------------------------


def test_out_of_gamut_warns_and_clips():
    monochromatic = np.zeros_like(FULL)
    monochromatic[np.argmin(np.abs(FULL - 480))] = 1.0
    xyz = spectrum_to_xyz(monochromatic, FULL)
    with pytest.warns(GamutWarning):
        rgb = xyz_to_srgb(xyz / max(xyz[1], 1e-12))
    assert np.all(rgb >= 0.0) and np.all(rgb <= 1.0)


def test_clipping_can_be_declined():
    monochromatic = np.zeros_like(FULL)
    monochromatic[np.argmin(np.abs(FULL - 480))] = 1.0
    xyz = spectrum_to_xyz(monochromatic, FULL)
    with pytest.warns(GamutWarning):
        unclipped = xyz_to_srgb(xyz / xyz[1], clip=False)
    assert np.any(unclipped < 0) or np.any(unclipped > 1)


# -- arbitrary sensors and eyes ------------------------------------------


def test_a_camera_with_three_channels():
    centres, width = [450.0, 550.0, 620.0], 30.0
    sensitivity = np.stack(
        [np.exp(-0.5 * ((FULL - c) / width) ** 2) for c in centres], axis=1
    )
    blue_light = np.exp(-0.5 * ((FULL - 450) / 10.0) ** 2)
    response = integrate_response(blue_light, FULL, sensitivity, FULL,
                                  name="camera")
    assert response.shape == (3,)
    assert response[0] > response[1] > response[2]


def test_a_single_channel_receptor():
    receptor = np.exp(-0.5 * ((FULL - 500) / 25.0) ** 2)
    out = integrate_response(np.ones_like(FULL), FULL, receptor, FULL)
    assert out.shape == (1,)
    assert out[0] > 0


def test_response_may_be_given_on_its_own_grid():
    grid = np.arange(400.0, 701.0, 5.0)
    receptor = np.exp(-0.5 * ((grid - 550) / 30.0) ** 2)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", CoverageWarning)
        out = integrate_response(np.ones_like(FULL), FULL, receptor, grid)
    assert out.shape == (1,)


def test_mismatched_shapes_are_refused():
    with pytest.raises(ValueError, match="same shape"):
        spectrum_to_xyz(np.ones(5), FULL)


# -- the point of all this -----------------------------------------------


def test_water_reddens_nothing_and_blues_everything():
    """A grey target seen through water must lose its red first."""
    wl = np.arange(412.0, 701.0, 4.0)   # inside the measured band
    iops = uwlight.water("III")
    kd = uwlight.water("III", source="austin1986")
    illumination = _on(wl)

    scene = uwlight.Scene.at_depth(iops, 15.0, illumination, wl, kd=kd)
    b_inf = uwlight.veiling_radiance_estimate(
        iops, scene.downwelling, wl, backscatter_ratio=0.015
    )
    obs = scene.observe(np.full_like(wl, 0.5), 3.0, veiling_radiance=b_inf)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        surface = spectrum_to_srgb(0.5 * illumination, wl, white=illumination)
        underwater = spectrum_to_srgb(
            obs.radiance, wl, white=scene.downwelling / np.pi
        )
    # At the surface the target is neutral; underwater it is not.
    assert np.allclose(surface, surface[0], atol=1e-6)
    assert underwater[2] > underwater[0], "blue should survive better than red"

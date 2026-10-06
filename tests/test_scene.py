"""The path model, and the limits it must respect."""

from __future__ import annotations

import warnings

import numpy as np
import pytest

import jerlov
from jerlov import MissingQuantityError, ProvenanceWarning, Scene


WL = np.arange(450.0, 651.0, 25.0)


def scene(water_type="III", source="williamson2022", downwelling=None):
    w = jerlov.water(water_type, source=source)
    ed = np.ones_like(WL) if downwelling is None else downwelling
    return Scene(w, ed, WL, depth_m=8.0)


def flat(value=0.5):
    return np.full_like(WL, value)


# -- the part with no approximation --------------------------------------


def test_transmittance_is_exp_minus_c_r():
    s = scene()
    r = 3.0
    assert np.allclose(s.transmittance(r), np.exp(-s.water.c(WL) * r))


def test_transmittance_is_one_at_zero_distance():
    assert np.allclose(scene().transmittance(0.0), 1.0)


def test_negative_distance_is_refused():
    with pytest.raises(ValueError, match="cannot be negative"):
        scene().transmittance(-1.0)


# -- the path model ------------------------------------------------------


def test_at_zero_distance_only_the_target_is_seen():
    s = scene()
    obs = s.observe(flat(), 0.0, veiling_radiance=flat(0.01))
    assert np.allclose(obs.veiling, 0.0)
    assert np.allclose(obs.radiance, 0.5 * s.downwelling / np.pi)


def test_far_away_only_the_water_is_seen():
    s = scene()
    b_inf = flat(0.01)
    obs = s.observe(flat(), 500.0, veiling_radiance=b_inf)
    assert np.allclose(obs.radiance, b_inf, rtol=1e-9)
    assert np.allclose(obs.veiling_fraction, 1.0)


def test_components_sum_to_the_total():
    s = scene()
    obs = s.observe(flat(0.8), 4.0, veiling_radiance=flat(0.02))
    assert np.allclose(obs.direct + obs.veiling, obs.radiance)


def test_veiling_fraction_grows_with_distance():
    s = scene()
    previous = -1.0
    for r in (0.5, 1.0, 2.0, 5.0, 10.0):
        obs = s.observe(flat(), r, veiling_radiance=flat(0.01))
        current = float(np.mean(obs.veiling_fraction))
        assert current > previous
        previous = current


def test_contrast_decays_with_distance():
    s = scene()
    bright, dark = flat(0.8), flat(0.1)
    contrasts = []
    for r in (0.5, 2.0, 8.0, 30.0):
        obs = s.observe(bright, r, veiling_radiance=flat(0.02))
        background = dark * s.downwelling / np.pi
        contrasts.append(float(np.mean(np.abs(obs.contrast(background)))))
    assert contrasts == sorted(contrasts, reverse=True)
    # Far enough out, the target is indistinguishable from the background.
    assert contrasts[-1] < 0.01


def test_contrast_follows_the_formula_in_its_docstring():
    """The docstring used to say the inherent contrast is simply reduced by
    the transmittance. That holds only against a background as bright as the
    water's own veiling light."""
    s = scene()
    target = flat(0.8) * s.downwelling / np.pi
    background = flat(0.1) * s.downwelling / np.pi
    inherent = (target - background) / background
    veil = flat(0.02)
    for r in (0.5, 2.0, 8.0):
        t = s.transmittance(r)
        obs = s.observe(flat(0.8), r, veiling_radiance=veil)
        expected = inherent * background * t / (background * t + veil * (1 - t))
        assert np.allclose(obs.contrast(background), expected)
        # No veiling light: dimming target and background alike leaves the
        # contrast where it was.
        bare = s.observe(flat(0.8), r, veiling_radiance=flat(0.0))
        assert np.allclose(bare.contrast(background), inherent)
        # A background that is the water itself gives the classic C_0 * t.
        water = s.observe(flat(0.8), r, veiling_radiance=background)
        assert np.allclose(water.contrast(background), inherent * t)
        # Darker than the water, it falls faster than that; brighter, slower.
        assert np.all(np.abs(s.observe(flat(0.8), r, veiling_radiance=2 * background)
                             .contrast(background)) < np.abs(inherent * t))
        assert np.all(np.abs(s.observe(flat(0.8), r, veiling_radiance=background / 2)
                             .contrast(background)) > np.abs(inherent * t))


def test_turbid_water_veils_faster_than_clear():
    clear = scene("IB").observe(flat(), 3.0, veiling_radiance=flat(0.01))
    turbid = scene("5C").observe(flat(), 3.0, veiling_radiance=flat(0.01))
    assert np.mean(turbid.veiling_fraction) > np.mean(clear.veiling_fraction)


# -- what the package refuses to guess -----------------------------------


def test_veiling_radiance_has_no_default():
    s = scene()
    with pytest.raises(MissingQuantityError, match="no default"):
        s.observe(flat(), 3.0, veiling_radiance=None)


def test_observe_requires_the_keyword():
    with pytest.raises(TypeError):
        scene().observe(flat(), 3.0)


def test_estimate_requires_a_backscatter_ratio():
    w = jerlov.water("III")
    with pytest.raises(TypeError):
        jerlov.veiling_radiance_estimate(w, np.ones_like(WL), WL)
    with pytest.raises(MissingQuantityError):
        jerlov.veiling_radiance_estimate(
            w, np.ones_like(WL), WL, backscatter_ratio=None
        )


def test_estimate_is_usable_when_asked_for_deliberately():
    w = jerlov.water("III")
    ed = np.ones_like(WL)
    b_inf = jerlov.veiling_radiance_estimate(
        w, ed, WL, backscatter_ratio=0.02
    )
    assert np.all(b_inf > 0)
    # bb * Ed / (2 pi c)
    expected = w.b(WL) * 0.02 * ed / (2 * np.pi * w.c(WL))
    assert np.allclose(b_inf, expected)


def test_water_without_scattering_is_refused():
    w = jerlov.water("III", source="jerlov1976")  # Kd only
    with pytest.raises(MissingQuantityError, match="both a and b"):
        Scene(w, np.ones_like(WL), WL)


# -- input checking ------------------------------------------------------


def test_reflectance_must_be_physical():
    s = scene()
    for bad in (-0.1, 1.5):
        with pytest.raises(ValueError, match="between 0 and 1"):
            s.observe(flat(bad), 1.0, veiling_radiance=flat(0.01))


def test_shapes_must_agree():
    s = scene()
    with pytest.raises(ValueError, match="same shape"):
        s.observe(np.ones(3), 1.0, veiling_radiance=flat(0.01))
    with pytest.raises(ValueError, match="same shape"):
        s.observe(flat(), 1.0, veiling_radiance=np.ones(3))


def test_negative_downwelling_is_refused():
    with pytest.raises(ValueError, match="cannot be negative"):
        Scene(jerlov.water("III"), -np.ones_like(WL), WL)


def test_scene_refuses_wavelengths_outside_the_data():
    w = jerlov.water("III")  # 300-800 nm
    with pytest.raises(ValueError, match="does not extrapolate"):
        Scene(w, np.ones(2), np.array([250.0, 900.0]))


# -- depth ---------------------------------------------------------------


def test_at_depth_attenuates_the_surface_spectrum():
    iops = jerlov.water("III")
    kd_water = jerlov.water("III", source="austin1986")
    surface = np.ones_like(WL)
    s = Scene.at_depth(iops, 10.0, surface, WL, kd=kd_water)
    expected = surface * np.exp(-kd_water.kd(WL) * 10.0)
    assert np.allclose(s.downwelling, expected)
    assert s.depth_m == 10.0


def test_at_depth_accepts_a_plain_array():
    s = Scene.at_depth(
        jerlov.water("III"), 5.0, np.ones_like(WL), WL,
        kd=np.full_like(WL, 0.1),
    )
    assert np.allclose(s.downwelling, np.exp(-0.5))


def test_at_depth_refuses_negative_depth():
    with pytest.raises(ValueError, match="cannot be negative"):
        Scene.at_depth(
            jerlov.water("III"), -1.0, np.ones_like(WL), WL,
            kd=np.full_like(WL, 0.1),
        )


def test_zero_depth_leaves_the_surface_spectrum_alone():
    surface = np.linspace(1.0, 2.0, WL.size)
    s = Scene.at_depth(
        jerlov.water("III"), 0.0, surface, WL, kd=np.full_like(WL, 0.1)
    )
    assert np.allclose(s.downwelling, surface)


# -- provenance ----------------------------------------------------------


def test_flagged_water_still_warns_through_the_scene():
    w = jerlov.water("5C", source="solonenko2015")
    with pytest.warns(ProvenanceWarning):
        Scene(w, np.ones_like(WL), WL)


def test_sound_water_does_not_warn():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        s = scene("III")
        s.observe(flat(), 2.0, veiling_radiance=flat(0.01))


# -- Akkaynak-Treibitz coefficients --------------------------------------


def test_coefficients_are_the_beam_attenuation():
    s = scene()
    p = s.attenuation_coefficients((0.5, 5.0))
    assert np.allclose(p.beta_D, s.water.c(WL))
    assert np.allclose(p.beta_B, s.water.c(WL))


def test_the_coefficients_say_they_are_not_distinct():
    """The whole point of Akkaynak & Treibitz is that these differ."""
    p = scene().attenuation_coefficients((0.5, 5.0))
    assert p.are_distinct is False
    assert "single scattering" in p.note
    assert "Akkaynak" in p.note


def test_the_distance_range_is_required_and_recorded():
    with pytest.raises(TypeError):
        scene().attenuation_coefficients()
    p = scene().attenuation_coefficients((1.0, 8.0))
    assert p.distance_range_m == (1.0, 8.0)


def test_a_backwards_or_negative_range_is_refused():
    s = scene()
    for bad in ((5.0, 1.0), (-1.0, 5.0)):
        with pytest.raises(ValueError, match="0 <= low <= high"):
            s.attenuation_coefficients(bad)


def test_veiling_radiance_is_carried_through_if_given():
    s = scene()
    assert s.attenuation_coefficients((0.5, 5.0)).B_inf is None
    b_inf = flat(0.02)
    p = s.attenuation_coefficients((0.5, 5.0), veiling_radiance=b_inf)
    assert np.allclose(p.B_inf, b_inf)


def test_the_coefficients_reproduce_observe():
    """I = J exp(-beta_D r) + B_inf (1 - exp(-beta_B r)) must match observe."""
    s = scene()
    b_inf = flat(0.02)
    r = 3.0
    obs = s.observe(flat(0.8), r, veiling_radiance=b_inf)
    p = s.attenuation_coefficients((0.0, 10.0), veiling_radiance=b_inf)

    target = 0.8 * s.downwelling / np.pi
    rebuilt = (target * np.exp(-p.beta_D * r)
               + p.B_inf * (1 - np.exp(-p.beta_B * r)))
    assert np.allclose(rebuilt, obs.radiance)


def test_the_result_does_not_alias_the_scene():
    s = scene()
    p = s.attenuation_coefficients((0.5, 5.0))
    p.beta_D[0] = 999.0
    assert not np.allclose(s.water.c(WL)[0], 999.0)
    assert not np.allclose(p.beta_B[0], 999.0)

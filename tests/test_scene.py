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

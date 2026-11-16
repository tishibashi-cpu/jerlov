"""Lee et al. (2005, C09019) K_VIS, K_IR and the shortwave transmittance,
and Lee et al.'s (2007) depth of a fraction: DECISIONS.md section 98."""

import math
import warnings

import numpy as np
import pytest

import jerlov
from jerlov import ocean_colour, shortwave


def _quiet(f, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        return f(*args, **kwargs)


def test_coefficients_are_table_2_and_eq_4():
    assert ocean_colour.LEE2005_KVIS_CHI == (-0.057, 0.482, 4.221)
    assert ocean_colour.LEE2005_KVIS_ZETA == (0.183, 0.702, -2.567)
    assert ocean_colour.LEE2005_KVIS_ALPHA == (0.090, 1.465, -0.667)
    assert shortwave.LEE2005_KIR_COEFFICIENTS == (0.560, 2.304, 0.001,
                                                  0.65, 0.002)


def _k1_k2(a, bb, sun):
    """Eq. (9) written out by hand."""
    s = math.radians(sun)
    k1 = (-0.057 + 0.482 * math.sqrt(a) + 4.221 * bb) * (1 + 0.090 * math.sin(s))
    k2 = (0.183 + 0.702 * a - 2.567 * bb) * (1.465 - 0.667 * math.cos(s))
    return k1, k2


@pytest.mark.parametrize("a,bb", [(0.03, 0.002), (0.1, 0.005), (0.6, 0.03)])
@pytest.mark.parametrize("sun", [10.0, 30.0, 60.0])
@pytest.mark.parametrize("z", [0.0, 1.0, 8.0, 35.0])
def test_kvis_is_eq_7_and_9(a, bb, sun, z):
    k1, k2 = _k1_k2(a, bb, sun)
    assert _quiet(jerlov.lee2005_kvis, a, bb, z, sun_zenith_deg=sun) \
        == pytest.approx(k1 + k2 / math.sqrt(1 + z), rel=1e-12)


def test_kvis_one_case_by_hand():
    # a = 0.1, bb = 0.005, sun 30: K1 = (-0.057 + 0.482 * 0.316228 +
    # 0.021105) * 1.045 = 0.121770; K2 = (0.183 + 0.0702 - 0.012835) *
    # (1.465 - 0.577350) = 0.213291; at 3 m, K1 + K2 / 2 = 0.228416.
    assert jerlov.lee2005_kvis(0.1, 0.005, 3.0, sun_zenith_deg=30.0) \
        == pytest.approx(0.228416, abs=2e-6)


@pytest.mark.parametrize("z,sun", [(0.01, 0.0), (0.5, 30.0), (3.0, 60.0)])
def test_kir_is_eq_4(z, sun):
    want = (0.560 + 2.304 / (0.001 + z) ** 0.65) * (1 + 0.002 * sun)
    assert jerlov.lee2005_kir(z, sun_zenith_deg=sun) \
        == pytest.approx(want, rel=1e-12)


def test_shortwave_is_eq_11():
    a, bb, sun, f = 0.05, 0.003, 30.0, 0.424
    z = np.array([0.0, 0.5, 2.0, 10.0])
    kv = _quiet(jerlov.lee2005_kvis, a, bb, z, sun_zenith_deg=sun)
    ki = _quiet(jerlov.lee2005_kir, z, sun_zenith_deg=sun)
    want = f * np.exp(-kv * z) + (1 - f) * np.exp(-ki * z)
    got = _quiet(jerlov.lee2005_shortwave_transmittance, a, bb, z,
                 sun_zenith_deg=sun, visible_fraction=f)
    np.testing.assert_allclose(got, want, rtol=1e-12)
    assert got[0] == 1.0


@pytest.mark.parametrize("a,bb", [(0.03, 0.002), (0.1, 0.005), (0.6, 0.03),
                                  (2.0, 0.1)])
@pytest.mark.parametrize("sun", [10.0, 45.0])
@pytest.mark.parametrize("fraction", [0.5, 0.1, 0.01])
def test_depth_of_fraction_solves_k_vis_z_equals_tau(a, bb, sun, fraction):
    z = _quiet(jerlov.lee2007_depth_of_fraction, a, bb, sun_zenith_deg=sun,
               fraction=fraction)
    kv = _quiet(jerlov.lee2005_kvis, a, bb, z, sun_zenith_deg=sun)
    assert kv * z == pytest.approx(-math.log(fraction), rel=1e-9)
    # And it is the first depth to reach it: E_VIS falls monotonically.
    shallower = _quiet(jerlov.lee2005_kvis, a, bb, 0.999 * z,
                       sun_zenith_deg=sun) * 0.999 * z
    assert shallower < -math.log(fraction)


def test_depth_of_fraction_is_a_root_of_the_cubic():
    a, bb, sun, fraction = 0.1, 0.005, 30.0, 0.01
    k1, k2 = _k1_k2(a, bb, sun)
    tau = -math.log(fraction)
    y1 = (k1 ** 2 - k2 ** 2 - 2 * tau * k1) / k1 ** 2
    y2 = (tau ** 2 - 2 * tau * k1) / k1 ** 2
    y3 = tau ** 2 / k1 ** 2
    z = jerlov.lee2007_depth_of_fraction(a, bb, sun_zenith_deg=sun,
                                         fraction=fraction)
    assert z ** 3 + y1 * z ** 2 + y2 * z + y3 == pytest.approx(0, abs=1e-9)


def test_arrays_broadcast_and_scalars_are_floats():
    z = _quiet(jerlov.lee2007_depth_of_fraction, np.array([0.05, 0.1]),
               0.004, sun_zenith_deg=np.array([[20.0], [40.0]]),
               fraction=0.1)
    assert z.shape == (2, 2)
    one = _quiet(jerlov.lee2007_depth_of_fraction, 0.1, 0.004,
                 sun_zenith_deg=40.0, fraction=0.1)
    assert isinstance(one, float) and z[1, 1] == one
    assert isinstance(jerlov.lee2005_kir(1.0, sun_zenith_deg=30.0), float)
    k = jerlov.lee2005_kvis(0.1, 0.005, [1.0, 2.0], sun_zenith_deg=30.0)
    assert isinstance(k, np.ndarray) and k.shape == (2,)


def test_nan_in_a_or_bb_is_a_gap():
    k = _quiet(jerlov.lee2005_kvis, [0.1, np.nan], 0.005, 2.0,
               sun_zenith_deg=30.0)
    assert np.isnan(k[1]) and not np.isnan(k[0])
    z = _quiet(jerlov.lee2007_depth_of_fraction, [np.nan, 0.1], 0.005,
               sun_zenith_deg=30.0, fraction=0.01)
    assert np.isnan(z[0]) and not np.isnan(z[1])


@pytest.mark.parametrize("call", [
    lambda: jerlov.lee2005_kvis(0.1, 0.005, -1.0, sun_zenith_deg=30.0),
    lambda: jerlov.lee2005_kvis(0.1, 0.005, np.nan, sun_zenith_deg=30.0),
    lambda: jerlov.lee2005_kvis(0.1, 0.005, np.inf, sun_zenith_deg=30.0),
    lambda: jerlov.lee2005_kvis(np.inf, 0.005, 1.0, sun_zenith_deg=30.0),
    lambda: jerlov.lee2005_kvis(-0.1, 0.005, 1.0, sun_zenith_deg=30.0),
    lambda: jerlov.lee2005_kvis(0.1, 0.0, 1.0, sun_zenith_deg=30.0),
    lambda: jerlov.lee2005_kvis(0.1, 0.005, 1.0, sun_zenith_deg=90.0),
    lambda: jerlov.lee2005_kvis(0.1, 0.005, 1.0, sun_zenith_deg=-1.0),
    lambda: jerlov.lee2005_kir(-0.5, sun_zenith_deg=30.0),
    lambda: jerlov.lee2005_kir(1.0, sun_zenith_deg=95.0),
    lambda: jerlov.lee2007_depth_of_fraction(0.1, 0.005, sun_zenith_deg=30.0,
                                             fraction=0.0),
    lambda: jerlov.lee2007_depth_of_fraction(0.1, 0.005, sun_zenith_deg=30.0,
                                             fraction=1.0),
    lambda: jerlov.lee2007_depth_of_fraction(0.1, 0.005, sun_zenith_deg=30.0,
                                             fraction=np.nan),
    lambda: jerlov.lee2005_shortwave_transmittance(
        0.1, 0.005, 1.0, sun_zenith_deg=30.0, visible_fraction=1.2),
    lambda: jerlov.lee2005_shortwave_transmittance(
        0.1, 0.005, 1.0, sun_zenith_deg=30.0, visible_fraction=[0.4, 0.5]),
    lambda: jerlov.lee2005_shortwave_transmittance(
        0.1, 0.005, 1.0, sun_zenith_deg=30.0, visible_fraction="0.4"),
])
def test_refusals(call):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        with pytest.raises(ValueError):
            call()


@pytest.mark.parametrize("a,bb", [(0.01, 0.001),    # K1 < 0: tiny a
                                  (0.05, 0.1)])     # K2 < 0: bb large
def test_k1_or_k2_of_the_wrong_sign_is_refused(a, bb):
    with pytest.raises(ValueError, match="K1 must be positive"):
        _quiet(jerlov.lee2005_kvis, a, bb, 1.0, sun_zenith_deg=30.0)
    with pytest.raises(ValueError, match="K1 must be positive"):
        _quiet(jerlov.lee2007_depth_of_fraction, a, bb, sun_zenith_deg=30.0,
               fraction=0.01)


def test_no_default_for_the_sun_the_fraction_or_f_vis():
    with pytest.raises(TypeError):
        jerlov.lee2005_kvis(0.1, 0.005, 1.0)
    with pytest.raises(TypeError):
        jerlov.lee2007_depth_of_fraction(0.1, 0.005, sun_zenith_deg=30.0)
    with pytest.raises(TypeError):
        jerlov.lee2005_shortwave_transmittance(0.1, 0.005, 1.0,
                                               sun_zenith_deg=30.0)
    with pytest.raises(TypeError):
        jerlov.lee2005_kir(1.0)


def _messages(f, *args, **kwargs):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", jerlov.ProvenanceWarning)
        f(*args, **kwargs)
    return [str(w.message) for w in caught
            if issubclass(w.category, jerlov.ProvenanceWarning)]


def test_inside_the_fit_nothing_warns():
    assert _messages(jerlov.lee2005_kvis, 0.1, 0.005, 5.0,
                     sun_zenith_deg=30.0) == []
    assert _messages(jerlov.lee2005_kir, 1.0, sun_zenith_deg=0.0) == []
    assert _messages(jerlov.lee2007_depth_of_fraction, 0.1, 0.005,
                     sun_zenith_deg=30.0, fraction=0.01) == []
    assert _messages(jerlov.lee2005_shortwave_transmittance, 0.1, 0.005,
                     [0.0, 1.0, 10.0], sun_zenith_deg=30.0,
                     visible_fraction=0.424) == []


@pytest.mark.parametrize("call,needle", [
    (lambda: jerlov.lee2005_kvis(0.1, 0.005, 5.0, sun_zenith_deg=5.0),
     "10-60 degrees"),
    (lambda: jerlov.lee2005_kvis(0.1, 0.005, 5.0, sun_zenith_deg=70.0),
     "10-60 degrees"),
    (lambda: jerlov.lee2005_kvis(0.02, 0.001, 100.0, sun_zenith_deg=30.0),
     "K_VIS of 0.04 to 1.6"),
    (lambda: jerlov.lee2005_kvis(3.0, 0.2, 0.0, sun_zenith_deg=30.0),
     "K_VIS of 0.04 to 1.6"),
    (lambda: jerlov.lee2005_kvis(0.1, 0.005, 60.0, sun_zenith_deg=30.0),
     "T_VIS of 0.001"),
    (lambda: jerlov.lee2007_depth_of_fraction(
        0.1, 0.005, sun_zenith_deg=30.0, fraction=0.0005), "T_VIS of 0.001"),
    (lambda: jerlov.lee2005_kir(0.005, sun_zenith_deg=30.0), "0.01 to 3 m"),
    (lambda: jerlov.lee2005_kir(5.0, sun_zenith_deg=30.0), "0.01 to 3 m"),
    (lambda: jerlov.lee2005_kir(1.0, sun_zenith_deg=65.0), "0-60 degrees"),
    (lambda: jerlov.lee2005_shortwave_transmittance(
        0.1, 0.005, 0.005, sun_zenith_deg=30.0, visible_fraction=0.424),
     "0.01 m and more"),
])
def test_outside_the_fit_warns(call, needle):
    messages = _messages(call)
    assert any(needle in m for m in messages), messages


def test_shortwave_below_3_m_does_not_warn_of_k_ir():
    # "for z deeper than 3 m, E_IR is negligible" (p. 3).
    assert _messages(jerlov.lee2005_shortwave_transmittance, 0.1, 0.005,
                     20.0, sun_zenith_deg=30.0, visible_fraction=0.424) == []


# -- the figures DATA.md section 42 quotes ----------------------------------

_OCEANIC = ("I", "IA", "IB", "II", "III")


def _iops(water_type, source):
    water = jerlov.water(water_type, source=source)
    constants = water.source.scattering
    bw = constants.bw_coeff * (400.0 / 490.0) ** constants.bw_exponent
    a, b = float(water.a(490.0)), float(water.b(490.0))
    return a, {s: bw / 2 + jerlov.petzold_scattering(s).backscatter_ratio
               * (b - bw) for s in jerlov.PETZOLD_STATIONS}


def test_data_42_quanta_levels():
    sets = (("solonenko2015", ("I", "IA", "IB", "II", "III", "1C", "3C")),
            ("williamson2022", ("IB", "II", "III", "1C", "3C")))
    base, within, widest, outside = {}, 0, 0.0, []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        for source, types in sets:
            for t in types:
                a, bbs = _iops(t, source)
                q = jerlov.jerlov1977_quanta(t)
                sun = 15.0 if t in _OCEANIC else 45.0
                for level, z_m in zip(q.level_percent, q.level_depth_m):
                    f = level / 100
                    base.setdefault(source, []).append(
                        jerlov.lee2007_depth_of_fraction(
                            a, bbs["NUC 2240"], sun_zenith_deg=sun,
                            fraction=f) / z_m)
                    reach = [jerlov.lee2007_depth_of_fraction(
                        a, bb, sun_zenith_deg=s, fraction=f) / z_m
                        for bb in bbs.values() for s in (sun, 0.0, 60.0)]
                    widest = max(widest, max(reach) / min(reach))
                    if min(reach) <= 1 <= max(reach):
                        within += 1
                    else:
                        outside.append((source, t, level))
    assert round(float(np.median(base["solonenko2015"])), 2) == 1.13
    assert round(float(np.median(base["williamson2022"])), 2) == 0.91
    assert within == 38 and round(widest, 1) == 2.4
    assert sorted(outside) == sorted(
        [("solonenko2015", "IA", 1.0), ("solonenko2015", "IB", 1.0)]
        + [("williamson2022", t, lv) for t in ("IB", "II")
           for lv in (30.0, 10.0, 3.0, 1.0)])


def test_data_42_table_xxi():
    ratios, closer = {1.0: [], 2.0: [], 5.0: [], 10.0: []}, {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        for t in ("I", "IA", "IB", "II", "III", "1C", "3C", "5C", "7C",
                  "9C"):
            a, bbs = _iops(t, "solonenko2015")
            depths, table = jerlov.jerlov1968_solar_fraction(t)
            keep = (depths > 0) & ~np.isnan(table) & (depths <= 100)
            lee = jerlov.lee2005_shortwave_transmittance(
                a, bbs["NUC 2240"], depths[keep],
                sun_zenith_deg=0.0 if t in _OCEANIC else 45.0,
                visible_fraction=0.424)
            for z, x, w in zip(depths[keep], lee, table[keep]):
                if z in ratios:
                    ratios[z].append(x / w)
            if t in _OCEANIC:
                ps = jerlov.solar_fraction(t, depths[keep])
                for z, x, y, w in zip(depths[keep], lee, ps, table[keep]):
                    n, of = closer.get(z, (0, 0))
                    closer[z] = (n + (abs(np.log(x / w)) < abs(np.log(y / w))),
                                 of + 1)
    assert (round(min(ratios[1.0]), 2), round(max(ratios[1.0]), 2),
            round(float(np.median(ratios[1.0])), 2)) == (0.91, 1.08, 0.95)
    assert (round(min(ratios[10.0]), 2), round(max(ratios[10.0]), 2)) \
        == (0.34, 1.75)
    assert closer == {1.0: (3, 5), 2.0: (3, 5), 5.0: (4, 5), 10.0: (4, 5),
                      25.0: (1, 5), 50.0: (1, 5), 75.0: (0, 5),
                      100.0: (1, 4)}

"""The light fluctuations read from Darecki et al. (2011) and Gernez &
Antoine (2009); DATA.md sections 24 and 25.

The readings are made in tools/build_darecki2011.py and
tools/build_gernez2009.py, which also check them against the papers'
text. These tests hold the shipped values to what the build produced and
to what the text says.
"""

from __future__ import annotations

import numpy as np
import pytest

import jerlov
from jerlov import _data


def test_darecki_irradiance_as_read():
    f = jerlov.darecki2011_irradiance_cv()
    assert f.depth_m.tolist() == [0.86, 1.70, 2.84, 3.78, 6.73, 9.58]
    assert f.wavelengths_nm.tolist() == [443.0, 532.0, 670.0]
    assert f.cv[0].tolist() == [0.4954, 0.5414, 0.6536]
    assert f.cv[-1].tolist() == [0.0481, 0.0513, 0.0815]
    assert f.collector_mm == 2.5 and f.beam_attenuation_555 == 0.68
    assert repr(f) == ("<IrradianceFluctuation Darecki 2011, 6 depths "
                       "0.86-9.58 m, 443, 532, 670 nm>")
    for array in (f.depth_m, f.wavelengths_nm, f.cv):
        with pytest.raises(ValueError):
            array[0] = 0.0


def test_darecki_irradiance_falls_with_depth_and_is_highest_in_the_red():
    """'the CV is higher in the red compared with the blue' (p. 12), and
    'less than 10% at depths below 6-8 m depending on light wavelength'."""
    cv = jerlov.darecki2011_irradiance_cv().cv
    assert np.all(np.diff(cv, axis=0) < 0)
    assert np.all(np.diff(cv, axis=1) > 0)
    assert np.all(cv[-1] < 0.10)
    assert cv[-2, -1] > 0.10 > cv[-2, 0]


def test_darecki_radiance_panels():
    """Thirteen whole angles; the largest CV round the refracted sunbeam,
    6 to 11 degrees beyond it; over 3 in panels b and c (p. 14)."""
    peaks = {}
    for panel in jerlov.DARECKI2011_PANELS:
        r = jerlov.darecki2011_radiance_cv(panel)
        assert r.zenith_deg.tolist() == [-90, -60, -30, -15, 0, 15, 20, 25,
                                         30, 35, 40, 60, 90]
        assert np.all(r.cv > 0)
        peaks[panel] = float(r.zenith_deg[np.argmax(r.cv)]) \
            - r.refracted_sun_zenith_deg
    assert peaks == {"a": 6.0, "b": 11.0, "c": 10.0}
    b = jerlov.darecki2011_radiance_cv("b")
    assert b.cv[b.zenith_deg.tolist().index(40)] == 3.0054
    assert b.depth_m == 0.59 and b.wind_m_s == 5.4
    assert jerlov.darecki2011_radiance_cv("c").cv.max() > 3.0
    with pytest.raises(KeyError, match="known: a, b, c"):
        jerlov.darecki2011_radiance_cv("d")


def test_gernez_as_read():
    """'maximal at 25% ... down to 5% when the sun approaches the horizon',
    Tmax 'from 1s to 3s' (p. 7)."""
    g = jerlov.gernez2009_cv_by_sun_zenith()
    assert g.sun_zenith_deg.tolist() == list(range(20, 90, 5))
    assert round(g.cv[0], 4) == 0.2445 and round(g.cv[-1], 4) == 0.0481
    assert round(100 * g.cv[0]) in (24, 25) and round(100 * g.cv[-1]) == 5
    assert (round(g.tmax_s[0]), round(g.tmax_s[-1])) == (1, 3)
    assert np.all(np.diff(g.cv[3:]) < 0)
    assert np.all(np.diff(g.tmax_s[1:]) > 0)
    assert round(g.cv_reading, 4) == 0.0011
    assert set(np.round(g.tmax_reading_s, 3)) == {0.013, 0.026}
    assert g.wavelength_nm == 510.0 and g.depth_m == (2.7, 3.7)


@pytest.mark.parametrize("name", ["darecki2011_irradiance_cv.csv",
                                  "darecki2011_radiance_cv.csv",
                                  "gernez2009_sun_zenith.csv"])
def test_every_value_says_it_was_read_from_a_figure(name):
    assert {r["status"] for r in _data._rows(name)} == {"read_from_figure"}


def test_darecki_spectral_as_read():
    """Figure 13b: higher in the red on every day, lowest on the windiest
    (p. 12); the caption's days."""
    s = jerlov.darecki2011_spectral_cv()
    assert s.wind_m_s.tolist() == [3.9, 5.4, 6.3, 7.2, 10.3]
    assert s.wavelengths_nm.tolist() == [410, 443, 488, 532, 610, 670]
    assert s.cv[0].tolist() == [0.3983, 0.4216, 0.4341, 0.4518, 0.5143,
                                0.5609]
    assert np.all(s.cv[:, -1] > s.cv[:, 0])
    assert np.all(s.cv[-1] == s.cv.min(axis=0))
    assert s.days[0] == "20 September 2008, 09:42"
    assert repr(s) == ("<SpectralFluctuation Darecki 2011, wind 3.9-10.3 "
                       "m/s, 410-670 nm>")


def test_gernez_conditions_as_read():
    """Figures 8b-8d: CV peaks near 22% at about 3 m/s of wind (p. 7);
    from 24% down to about 12% with Kd(490); Tmax 1 to 1.5 s by 0.065
    (p. 8); the standard deviation left out where the bar is not clear."""
    assert jerlov.GERNEZ2009_VARIABLES == ("wave_height_m", "sqrt_wind",
                                          "kd490_per_m")
    w = jerlov.gernez2009_cv_by("sqrt_wind")
    k = int(np.argmax(w.cv))
    assert round(w.x[k], 1) == 1.6 and round(100 * w.cv[k], 1) == 22.8
    assert np.isnan(w.cv_sd).sum() == 1
    d = jerlov.gernez2009_cv_by("kd490_per_m")
    assert d.x.size == 13 and round(d.x[0], 3) == 0.025
    assert round(100 * d.cv[0], 1) == 24.0
    assert round(100 * d.cv.min()) == 12
    assert 0.95 <= d.tmax_s[0] <= 1.1 and 1.4 <= d.tmax_s[4] <= 1.6
    assert np.isnan(d.cv_sd).sum() == 2
    h = jerlov.gernez2009_cv_by("wave_height_m")
    assert h.x.tolist() == [0.25 * i for i in range(10)]
    assert not np.any(np.isnan(h.cv_sd))
    with pytest.raises(KeyError, match="known: wave_height_m"):
        jerlov.gernez2009_cv_by("wind")


@pytest.mark.parametrize("name", ["darecki2011_spectral_cv.csv",
                                  "gernez2009_conditions.csv"])
def test_the_new_files_say_they_were_read_from_a_figure(name):
    assert {r["status"] for r in _data._rows(name)} == {"read_from_figure"}


def test_gernez_overcast_and_upwelling_as_read():
    """Figures 7 and 13 (DATA.md section 25): overcast CV steadily around
    3 percent but for the last Kd class, 1.6; Eu's CV from 1 to 3 percent
    with the sun, Tmax 3.2 s at 20 degrees and 4.3 s at 85; and the
    standard deviations left out where the bar is not at its symbol."""
    assert jerlov.GERNEZ2009_PLOTS[("clear", "Ed")] \
        == jerlov.GERNEZ2009_VARIABLES
    for key in (("overcast", "Ed"), ("clear", "Eu")):
        assert jerlov.GERNEZ2009_PLOTS[key] == (
            "sun_zenith_deg", "wave_height_m", "wind_m_s", "kd490_per_m")
    over = jerlov.gernez2009_cv_by("sun_zenith_deg", sky="overcast")
    assert over.figure == "7" and over.sky.startswith("overcast")
    assert over.x.tolist() == list(range(20, 90, 5))
    assert np.all((over.cv >= 0.025) & (over.cv <= 0.04))
    kd = jerlov.gernez2009_cv_by("kd490_per_m", sky="overcast")
    assert round(100 * kd.cv[-1], 1) == 1.6
    assert np.all(kd.cv[:-1] >= 0.025)
    up = jerlov.gernez2009_cv_by("sun_zenith_deg", irradiance="Eu")
    assert up.figure == "13" and up.irradiance == "Eu"
    assert (round(100 * up.cv[0]), round(100 * up.cv[-1])) == (1, 3)
    assert (round(up.tmax_s[0], 1), round(up.tmax_s[-1], 1)) == (3.2, 4.3)
    assert np.isnan(up.cv_sd[-1]) and np.isnan(up.cv_sd).sum() == 1
    assert np.isnan(jerlov.gernez2009_cv_by(
        "kd490_per_m", irradiance="Eu").cv_sd).sum() == 1
    assert round(100 * up.cv_reading, 3) == 0.026
    with pytest.raises(KeyError, match="known: clear/Ed"):
        jerlov.gernez2009_cv_by("wind_m_s", sky="overcast", irradiance="Eu")
    with pytest.raises(KeyError, match="known: sun_zenith_deg"):
        jerlov.gernez2009_cv_by("sqrt_wind", sky="overcast")


def test_gernez_spectral_as_read():
    """Figures 11 and 14: clear-sky CV of Ed from 15 to 26.5 percent; Eu's
    largest CV 5.4 percent; the clear-sky Tmax of Eu 4.6 s at 412 nm and
    4.2 at 442; overcast standard deviations not read; one pixel 0.125
    and 0.030 percent of CV."""
    ed = jerlov.gernez2009_spectral_cv("Ed")
    assert ed.wavelengths_nm.tolist() == [412, 442, 490, 510, 560, 665, 683]
    assert ed.figure == "11" and ed.depth_m == (2.7, 3.7)
    assert round(100 * ed.cv[0, 0]) == 15 and 25 <= 100 * ed.cv[0, -1] <= 27
    assert np.all(np.isnan(ed.cv_sd[1])) and not np.any(np.isnan(ed.cv_sd[0]))
    assert [round(t) for t in ed.tmax_s[1, 5:]] == [6, 6]
    assert round(100 * ed.cv_reading, 3) == 0.125
    eu = jerlov.gernez2009_spectral_cv("Eu")
    assert eu.figure == "14" and eu.depth_m == (8.0, 8.7)
    assert round(100 * eu.cv.max(), 1) == 5.4
    assert (round(eu.tmax_s[0, 0], 1), round(eu.tmax_s[0, 1], 1)) == (4.6, 4.2)
    assert round(100 * eu.cv_reading, 3) == 0.030
    assert repr(eu) == ("<SkySpectralFluctuation Gernez 2009 Figure 14, Eu, "
                        "412-683 nm>")
    with pytest.raises(KeyError, match="known: Ed, Eu"):
        jerlov.gernez2009_spectral_cv("Lu")


@pytest.mark.parametrize("name", ["gernez2009_more_conditions.csv",
                                  "gernez2009_spectral.csv"])
def test_the_0_19_files_say_they_were_read_from_a_figure(name):
    assert {r["status"] for r in _data._rows(name)} == {"read_from_figure"}

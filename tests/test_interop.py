"""Input files for OSOAA and HydroLight (DECISIONS.md section 86).

Each file is read back by its format's own description: the OSOAA User
Manual V2.0, sections 3.6.3 and 3.6.4, and the HydroLight 5.1 Technical
Documentation, section 7.3. The pure water subtracted, added back, must give
the water's own a, b and c.
"""

from __future__ import annotations

import warnings

import numpy as np
import pytest

import jerlov

#: OSOAA's pure seawater at 440 nm, fic/OSOAA_SEA_MOL_COEFFS_JUNE_2013.txt.
OSOAA_440 = (0.00635, 0.00501629)
WL = np.array([412.0, 440.0, 488.0, 510.0, 555.0, 650.0])
#: Pure water on WL for the HydroLight tests: any numbers below the water's.
A_W = np.array([0.0046, 0.0064, 0.0145, 0.0357, 0.0596, 0.34])
B_W = np.array([0.0067, 0.0049, 0.0033, 0.0027, 0.0019, 0.0010])


def _quiet(function, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return function(*args, **kwargs)


def _profile(text):
    """Parse a -HYD.UserProfile file: five comment lines, then rows."""
    lines = text.split("\n")
    rows = np.array([[float(v) for v in line.split()] for line in lines[5:]])
    return lines[:5], rows


def _ext(text):
    """Parse a -HYD.ExtData file."""
    lines = text.splitlines()
    head = {}
    for line in lines[:3]:
        key, value = line.split(":")
        head[key.strip()] = float(value)
    rows = np.array([[float(v) for v in line.split()] for line in lines[4:]])
    assert len(rows) == head["NB_LINES"]
    return head, lines[3], rows


def _ac9(text):
    """Parse HydroLight's standard ac-9 format: ten header records, n and
    the wavelengths, depth records, a final record at depth -1."""
    lines = text.splitlines()
    record11 = lines[10].split()
    n = int(record11[0])
    wl = np.array([float(v) for v in record11[1:]])
    assert wl.size == n
    rows = np.array([[float(v) for v in line.split()] for line in lines[11:]])
    assert rows.shape[1] == 1 + 2 * n
    return lines[:10], wl, rows


def test_user_profile_adds_back_to_the_water():
    water = jerlov.water("III")
    text = _quiet(jerlov.osoaa_user_profile, water, 440.0,
                  depths_m=[0, 5, 20, 50], pure_water=OSOAA_440)
    comments, rows = _profile(text)
    assert comments[0].startswith("Column 1") and "Jerlov III" in comments[3]
    assert not text.endswith("\n")       # the manual: no blank last line
    np.testing.assert_array_equal(rows[:, 0], [0, 5, 20, 50])
    a, b = float(water.a(440.0)), float(water.b(440.0))
    np.testing.assert_allclose(rows[:, 1] + OSOAA_440[0], a, rtol=1e-9)
    np.testing.assert_allclose(rows[:, 2] + OSOAA_440[1], b, rtol=1e-9)
    # What OSOAA reported for this file: c 0.4330 and b/c 0.72054 (DATA.md
    # section 38).
    assert a + b == pytest.approx(0.433, abs=5e-4)
    assert b / (a + b) == pytest.approx(0.72054, abs=5e-5)


def test_phase_function_is_vsf_over_b_from_180_down():
    scattering = jerlov.petzold_scattering("NUC 2200")
    text = jerlov.osoaa_phase_function(
        scattering, minus_f12_over_f11=0.0, f22_over_f11=1.0,
        f33_over_f11=1.0)
    head, comment, rows = _ext(text)
    assert head == {"EXTINCTION_COEF": scattering.c,
                    "SCATTERING_COEF": scattering.b, "NB_LINES": 55}
    assert comment.startswith("Angle F11 -F12/F11 F22/F11 F33/F11")
    assert "Model 3" in comment
    np.testing.assert_allclose(rows[:, 0], scattering.angles_deg[::-1],
                               rtol=1e-6)
    np.testing.assert_allclose(rows[:, 1], scattering.vsf[::-1]
                               / scattering.b, rtol=1e-8)
    np.testing.assert_array_equal(rows[:, 2:], [[0, 1, 1]] * 55)


def test_phase_function_ratios_per_angle():
    scattering = jerlov.petzold_scattering("NUC 2200")
    ratio = np.linspace(0.0, 0.5, 55)
    _, _, rows = _ext(jerlov.osoaa_phase_function(
        scattering, minus_f12_over_f11=ratio, f22_over_f11=1.0,
        f33_over_f11=ratio[::-1]))
    np.testing.assert_allclose(rows[:, 2], ratio[::-1])
    np.testing.assert_allclose(rows[:, 4], ratio)


def test_phase_function_warns_on_the_extension():
    with pytest.warns(jerlov.ProvenanceWarning, match="0.169"):
        jerlov.osoaa_phase_function(
            jerlov.petzold_scattering("AUTEC 7"), minus_f12_over_f11=0.0,
            f22_over_f11=1.0, f33_over_f11=1.0)


@pytest.mark.parametrize("name", ["minus_f12_over_f11", "f22_over_f11",
                                  "f33_over_f11"])
def test_phase_function_ratios_have_no_default(name):
    kwargs = dict(minus_f12_over_f11=0.0, f22_over_f11=1.0,
                  f33_over_f11=1.0)
    scattering = jerlov.petzold_scattering("NUC 2200")
    for bad in (None, [0.0] * 54, np.nan):
        with pytest.raises(ValueError, match=name):
            jerlov.osoaa_phase_function(scattering, **{**kwargs, name: bad})
    with pytest.raises(TypeError):
        jerlov.osoaa_phase_function(scattering)
    with pytest.raises(TypeError):
        jerlov.osoaa_phase_function(jerlov.water("III"), **kwargs)


def test_hydrolight_file_adds_back_to_the_water():
    water = jerlov.water("1C")
    text = _quiet(jerlov.hydrolight_ac9_file, water, WL,
                  depths_m=[0, 10, 30], pure_water=(A_W, B_W))
    header, wl, rows = _ac9(text)
    assert len(header) == 10 and "Jerlov 1C" in header[0]
    np.testing.assert_array_equal(wl, WL)
    np.testing.assert_array_equal(rows[:, 0], [0, 10, 30, -1])
    np.testing.assert_array_equal(rows[-1, 1:], rows[-2, 1:])
    n = WL.size
    a = np.asarray(water.a(WL))
    c = np.asarray(water.c(WL))
    for row in rows:
        np.testing.assert_allclose(row[1:1 + n] + A_W, a, rtol=1e-8)
        np.testing.assert_allclose(row[1 + n:] + A_W + B_W, c, rtol=1e-8)


def test_hydrolight_one_number_of_pure_water():
    water = jerlov.water("III")
    _, _, rows = _ac9(_quiet(jerlov.hydrolight_ac9_file, water, WL,
                             depths_m=[0, 1], pure_water=(0.004, 0.001)))
    np.testing.assert_allclose(rows[0, 1:7] + 0.004, water.a(WL), rtol=1e-8)


def test_pure_water_has_no_default():
    water = jerlov.water("III")
    with pytest.raises(ValueError, match="pure_water has no default"):
        jerlov.osoaa_user_profile(water, 440.0, depths_m=[0],
                                  pure_water=None)
    with pytest.raises(TypeError):
        jerlov.osoaa_user_profile(water, 440.0, depths_m=[0])
    with pytest.raises(TypeError):
        jerlov.hydrolight_ac9_file(water, WL, depths_m=[0, 1])
    for bad in ((0.1,), (np.nan, 0.0), (-0.01, 0.0), (A_W[:3], B_W)):
        with pytest.raises(ValueError, match="pure_water"):
            jerlov.hydrolight_ac9_file(water, WL, depths_m=[0, 1],
                                       pure_water=bad)


def test_negative_after_subtraction_is_refused():
    water = jerlov.water("IB")
    with pytest.raises(ValueError, match="negative at 440 nm"):
        jerlov.osoaa_user_profile(water, 440.0, depths_m=[0],
                                  pure_water=(1.0, 0.0))
    with pytest.raises(ValueError, match="c less the pure water"):
        jerlov.hydrolight_ac9_file(water, WL, depths_m=[0, 1],
                                   pure_water=(0.0, B_W + 1.0))


@pytest.mark.parametrize("depths", [None, [], [1, 2], [0, 0], [0, 2, 1],
                                    [0, np.inf], [[0, 1]], ["a"],
                                    list(range(500))])
def test_bad_depths_are_refused(depths):
    with pytest.raises((ValueError, TypeError)):
        jerlov.osoaa_user_profile(jerlov.water("III"), 440.0,
                                  depths_m=depths, pure_water=OSOAA_440)


def test_hydrolight_needs_two_depths_and_ascending_wavelengths():
    water = jerlov.water("III")
    with pytest.raises(ValueError, match="at least 2"):
        jerlov.hydrolight_ac9_file(water, WL, depths_m=[0],
                                   pure_water=(0.0, 0.0))
    with pytest.raises(ValueError, match="ascending"):
        jerlov.hydrolight_ac9_file(water, WL[::-1], depths_m=[0, 1],
                                   pure_water=(0.0, 0.0))
    with pytest.raises(ValueError, match="one number"):
        jerlov.osoaa_user_profile(water, [440.0, 550.0], depths_m=[0],
                                  pure_water=OSOAA_440)


def test_without_a_or_b_is_missing_quantity():
    water = jerlov.water("III", source="jerlov1976")
    with pytest.raises(jerlov.MissingQuantityError):
        jerlov.osoaa_user_profile(water, 440.0, depths_m=[0],
                                  pure_water=OSOAA_440)
    with pytest.raises(jerlov.MissingQuantityError):
        jerlov.hydrolight_ac9_file(water, WL, depths_m=[0, 1],
                                   pure_water=(0.0, 0.0))
    with pytest.raises(TypeError):
        jerlov.hydrolight_ac9_file("III", WL, depths_m=[0, 1],
                                   pure_water=(0.0, 0.0))


def test_positional_only():
    water = jerlov.water("III")
    with pytest.warns(FutureWarning, match="by position"):
        jerlov.osoaa_user_profile(water=water, wavelength_nm=440.0,
                                  depths_m=[0], pure_water=OSOAA_440)

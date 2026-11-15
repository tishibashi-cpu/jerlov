"""Input files for OSOAA and HydroLight (DECISIONS.md section 86), and
OSOAA's results read back (section 87).

Each file is read back by its format's own description: the OSOAA User
Manual V2.0, sections 3.6.3 and 3.6.4, and the HydroLight 5.1 Technical
Documentation, section 7.3. The pure water subtracted, added back, must give
the water's own a, b and c.
"""

from __future__ import annotations

import math
import pathlib
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


# -- OSOAA's results read back (DECISIONS.md section 87) -------------------

#: One OSOAA run: Jerlov III at 440 nm, HAOCE 5, sun at 30 degrees, from
#: the files of examples/radiative_transfer_inputs.py (DATA.md section 38).
RUN = pathlib.Path(__file__).resolve().parent / "data" / "osoaa_iii_440"


def _read(name):
    return (RUN / name).read_text()


@pytest.fixture(scope="module")
def flux():
    return jerlov.read_osoaa_flux(_read("Flux.txt"))


def test_the_run_is_the_examples_files():
    """The inputs OSOAA ran are what the writers write today."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        assert jerlov.osoaa_user_profile(
            jerlov.water("III"), 440.0, depths_m=[0, 10, 50],
            pure_water=OSOAA_440) == _read("profile_III_440.txt")
        assert jerlov.osoaa_phase_function(
            jerlov.petzold_scattering("HAOCE 5"), minus_f12_over_f11=0.0,
            f22_over_f11=1.0, f33_over_f11=1.0) == _read("phase_HAOCE5.txt")


def test_flux_levels(flux):
    np.testing.assert_array_equal(flux.level, np.arange(108))
    assert flux.altitude_m[0] == 300000.0
    # The surface: once above, twice below, then the sea down to 50 m.
    assert not flux.in_sea[26] and flux.altitude_m[26] == 0
    assert flux.in_sea[27] and flux.in_sea[28] and flux.in_sea.sum() == 81
    np.testing.assert_array_equal(flux.sea_depths_m[:2], [0.0, 0.0])
    assert flux.sea_depths_m[-1] == 50.0
    assert np.all(np.diff(flux.sea_depths_m) >= 0)


def test_flux_is_normalized_to_pi(flux):
    """The direct flux at the top of the atmosphere is pi cos 30 degrees:
    an extraterrestrial irradiance of pi."""
    assert flux.direct_down[0] == pytest.approx(
        math.pi * math.cos(math.radians(30.0)), abs=1e-5)
    assert flux.diffuse_down[0] == 0


def test_flux_totals_and_ratio(flux):
    np.testing.assert_allclose(flux.direct_down + flux.diffuse_down,
                               flux.total_down, rtol=1e-5, atol=1e-6)
    np.testing.assert_allclose(flux.direct_up + flux.diffuse_up,
                               flux.total_up, rtol=1e-5, atol=1e-6)
    ok = flux.total_down > 0
    ratio = np.where(ok, flux.total_up / np.where(ok, flux.total_down, 1), 0)
    np.testing.assert_allclose(flux.up_over_down, ratio, rtol=2e-5,
                               atol=1e-6)


def test_direct_is_not_the_unscattered_beam(flux):
    """OSOAA's truncation counts the forward peak as transmitted: its
    direct flux falls far slower than c / cos(theta_w)."""
    z = flux.sea_depths_m[1:]
    direct = flux.direct_down[flux.in_sea][1:]
    k_direct = math.log(direct[0] / direct[1]) / (z[1] - z[0])
    theta_w = math.asin(math.sin(math.radians(30.0)) / 1.34)
    assert k_direct == pytest.approx(0.144, abs=5e-4)
    assert 0.433 / math.cos(theta_w) == pytest.approx(0.467, abs=5e-4)


def test_kd(flux):
    z = flux.sea_depths_m
    ed = flux.total_down[flux.in_sea]
    # Between two levels Kd is the printed ratio, the first surface level
    # standing for 0.
    expected = math.log(ed[0] / ed[-1]) / 50.0
    assert flux.kd(0, 50) == pytest.approx(expected, rel=1e-12)
    assert flux.kd(0, 50) == pytest.approx(0.1381, abs=5e-5)
    k = 10
    assert flux.kd(z[k], z[k + 1]) == pytest.approx(
        math.log(ed[k] / ed[k + 1]) / (z[k + 1] - z[k]), rel=1e-12)
    # Between levels ln Ed is linear.
    mid = 0.5 * (z[k] + z[k + 1])
    assert flux.kd(z[k], mid) == pytest.approx(flux.kd(z[k], z[k + 1]),
                                               rel=1e-12)
    for upper, lower in ((0, 50.1), (10, 10), (20, 10), (-1, 5),
                         (0, np.nan)):
        with pytest.raises(ValueError):
            flux.kd(upper, lower)


@pytest.fixture(scope="module")
def profile():
    return jerlov.read_osoaa_radiance_vs_depth(_read("RESLUM_vsZ.txt"))


def test_radiance_vs_depth(profile, flux):
    assert profile.direction == "upward"
    assert profile.relative_azimuth_deg == 0
    assert profile.viewing_zenith_deg == 0
    # The same levels as the sea's in Flux.txt.
    np.testing.assert_allclose(profile.depth_m, flux.sea_depths_m,
                               atol=1e-5)
    # The reflectance is pi I / Ed, Ed from the other file.
    ed = flux.total_down[flux.in_sea]
    np.testing.assert_allclose(profile.reflectance,
                               math.pi * profile.radiance / ed, rtol=2e-5)
    assert profile.radiance[0] == pytest.approx(0.588088e-2, rel=1e-9)
    assert np.all(profile.scattering_angle_deg == 158.09)


def test_radiance_vs_vza():
    scan = jerlov.read_osoaa_radiance_vs_vza(_read("RESLUM_vsVZA.txt"))
    assert scan.altitude_m == -10.0
    assert scan.level.startswith("Value of the depth selected")
    assert (scan.azimuth_negative_deg, scan.azimuth_positive_deg) == (
        180.0, 0.0)
    assert scan.viewing_zenith_deg[0] == -89.07
    # The nadir is printed twice, as -0 (one half-plane) and 0 (the
    # other), with one value.
    step = np.diff(scan.viewing_zenith_deg)
    assert np.sum(step == 0) == 1 and np.all(step >= 0)
    k = int(np.argmin(step))
    assert scan.radiance[k] == scan.radiance[k + 1]
    assert scan.radiance.size == 102
    np.testing.assert_allclose(
        scan.polarized_radiance / scan.radiance,
        scan.polarization_percent / 100, atol=5e-4)


@pytest.mark.parametrize("line, altitude", [
    (" TOA level - Altitude (km) :   300.0", 300000.0),
    (" Sea bottom level - Depth (m) :  -50.0 (limited to the maximum "
     "computed depth)", -50.0),
    (" Above sea surface level 0+ - Altitude (km) :   0.0", 0.0),
    (" Under sea surface level 0- - Depth (m) :  -0.0", 0.0),
    (" Altitude (km) :   2.5", 2500.0),
    (" Altitude (km) :   400.0  limited to the maximum altitude   300.0",
     300000.0),
    (" Requested value of the depth for the output(m) :  -80.0 ==> "
     "limited to the max computed depth :  -50.0", -50.0),
])
def test_every_form_of_the_output_level(line, altitude):
    """The forms OSOAA_SOS.F can print; the run had only one."""
    text = _read("RESLUM_vsVZA.txt").replace(
        " Value of the depth selected for the output (m) :  "
        "-10.000000000000000", line)
    assert jerlov.read_osoaa_radiance_vs_vza(text).altitude_m == altitude


def test_readers_refuse():
    text = _read("Flux.txt")
    lines = text.splitlines()
    first_row = next(k for k, line in enumerate(lines)
                     if line.split()[:1] == ["0"])
    for bad, match in (
            (text.replace("0.272070E+001", "**************", 1), r"\*\*\*"),
            (text.replace("0.272070E+001", "NaN", 1), "not finite"),
            ("\n".join(lines[:first_row] + [lines[first_row] + " 1.0"]
                       + lines[first_row + 1:]), "10 values"),
            (_read("RESLUM_vsZ.txt"), "expects a file"),
            ("", "expects a file")):
        with pytest.raises(ValueError, match=match):
            jerlov.read_osoaa_flux(bad)
    with pytest.raises(TypeError, match="read_text"):
        jerlov.read_osoaa_flux(RUN / "Flux.txt")
    with pytest.raises(ValueError, match="viewing zenith"):
        jerlov.read_osoaa_radiance_vs_vza(_read("RESLUM_vsZ.txt"))
    with pytest.raises(ValueError, match="against depth"):
        jerlov.read_osoaa_radiance_vs_depth(_read("RESLUM_vsVZA.txt"))
    with pytest.raises(ValueError, match="no output level"):
        jerlov.read_osoaa_radiance_vs_vza(_read("RESLUM_vsVZA.txt").replace(
            "Value of the depth selected", "Something else"))


def test_results_are_read_only(flux, profile):
    for array in (flux.total_down, flux.in_sea, profile.radiance,
                  profile.depth_m):
        assert not array.flags.writeable

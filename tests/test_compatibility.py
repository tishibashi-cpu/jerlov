"""The changes 0.24.0 made before 1.0, and the old ways of calling that
still work until 2.0 (DECISIONS.md section 61)."""

from __future__ import annotations

import inspect
import pathlib
import re
import warnings

import numpy as np
import pytest

import jerlov

ROOT = pathlib.Path(__file__).resolve().parent.parent
source_tree = pytest.mark.skipif(
    not (ROOT / "pyproject.toml").exists(),
    reason="not running from a source tree",
)

WL = np.arange(400.0, 701.0, 10.0)
FLAT = np.ones_like(WL)


def _quietly(call):
    """The value, with every FutureWarning it raised."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        value = call()
    return value, [w for w in caught if w.category is FutureWarning]


# -- 1. salinity ---------------------------------------------------------------

SALINITY = [
    (jerlov.pure_water_vsf, (120.0, 500.0)),
    (jerlov.pure_water_backscattering, (500.0,)),
    (jerlov.pure_water_scattering, (500.0,)),
]


@pytest.mark.parametrize("function, args", SALINITY)
def test_leaving_out_the_salinity_warns_and_uses_37(function, args):
    value, caught = _quietly(lambda: function(*args))
    assert value == function(*args, salinity_psu=37.0)
    assert len(caught) == 1
    assert "salinity_psu was not given, so 37 was used" in str(
        caught[0].message)
    assert caught[0].filename == __file__


def test_leaving_out_the_salinity_of_bb_from_vsf_warns_and_uses_37():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.AngleWarning)
        value, caught = _quietly(
            lambda: jerlov.bb_from_vsf(0.002, 140.0, 532.0))
        given = jerlov.bb_from_vsf(0.002, 140.0, 532.0, salinity_psu=37.0)
    assert value.bb == given.bb and len(caught) == 1
    assert caught[0].filename == __file__


@pytest.mark.parametrize("function, args", SALINITY)
def test_a_salinity_by_position_still_works_with_a_warning(function, args):
    value, caught = _quietly(lambda: function(*args, 0.0))
    assert value == function(*args, salinity_psu=0.0)
    assert len(caught) == 1 and "by keyword" in str(caught[0].message)
    assert caught[0].filename == __file__
    with pytest.raises(TypeError, match="multiple values"):
        function(*args, 0.0, salinity_psu=0.0)
    with pytest.raises(TypeError, match="positional arguments"):
        function(*args, 0.0, 1.0)


def test_bb_from_vsf_still_takes_its_salinity_by_keyword_only():
    with pytest.raises(TypeError):
        jerlov.bb_from_vsf(0.002, 140.0, 532.0, 37.0)


def test_sea_water_at_37_scatters_30_percent_more_than_fresh_water():
    """The figure the warning, the docstrings, README and section 61 give;
    the examples compute the other way round, 23 percent less."""
    sea = jerlov.pure_water_scattering(500.0, salinity_psu=37.0)
    fresh = jerlov.pure_water_scattering(500.0, salinity_psu=0.0)
    assert sea / fresh == pytest.approx(1.30, abs=1e-12)
    assert round(100 * (1 - fresh / sea)) == 23


# -- 2 and 3. the error types, and Figure 8a -------------------------------------

def test_an_unknown_option_is_a_value_error():
    with pytest.raises(ValueError, match="not plotted against 'wind'"):
        jerlov.gernez2009_cv_by("wind")
    with pytest.raises(ValueError, match="no Ed under a cloudy sky"):
        jerlov.gernez2009_cv_by("wind_m_s", sky="cloudy")
    with pytest.raises(ValueError, match="no spectral figure"):
        jerlov.gernez2009_spectral_cv("Lu")
    with pytest.raises(ValueError, match="Figure 10"):
        jerlov.gernez2009_band_cv("wind")


def test_an_unknown_record_is_still_a_key_error():
    for call in (lambda: jerlov.water("XX"),
                 lambda: jerlov.get_source("nope"),
                 lambda: jerlov.petzold_scattering("HAOCE 99"),
                 lambda: jerlov.darecki2011_radiance_cv("d"),
                 lambda: jerlov.tyler1958_radiance(5.0)):
        with pytest.raises(KeyError):
            call()


def test_figure_8a_through_gernez2009_cv_by_is_the_old_function():
    new = jerlov.gernez2009_cv_by("sun_zenith_deg")
    old, caught = _quietly(jerlov.gernez2009_cv_by_sun_zenith)
    assert len(caught) == 1 and "gernez2009_cv_by" in str(caught[0].message)
    assert caught[0].filename == __file__
    assert isinstance(old, jerlov.SunZenithFluctuation)
    assert isinstance(new, jerlov.ConditionFluctuation)
    assert (new.variable, new.irradiance, new.figure) == (
        "sun_zenith_deg", "Ed", "8")
    assert np.array_equal(new.x, old.sun_zenith_deg)
    for name in ("cv", "cv_sd", "tmax_s", "tmax_reading_s"):
        assert np.array_equal(getattr(new, name), getattr(old, name)), name
    for name in ("cv_reading", "place", "wavelength_nm", "depth_m",
                 "collector_mm", "sampling_hz", "sky"):
        assert getattr(new, name) == getattr(old, name), name


def test_figure_8_lists_all_four_panels():
    assert jerlov.GERNEZ2009_PLOTS[("clear", "Ed")] == (
        "sun_zenith_deg", "wave_height_m", "sqrt_wind", "kd490_per_m")
    assert jerlov.GERNEZ2009_VARIABLES == (
        "wave_height_m", "sqrt_wind", "kd490_per_m")


# -- 4. positional-only wavelengths ---------------------------------------------

def _water():
    return jerlov.water("III")


def _kd_water():
    return jerlov.water("III", source="solonenko2015")


def _measured():
    return jerlov.Water.from_measurements(
        [400.0, 500.0, 600.0], a=[0.1, 0.2, 0.3],
        uncertainty={"a": [0.01, 0.02, 0.03]})


def _same(x, y):
    if hasattr(x, "transmittance") and hasattr(x, "layers"):
        x, y = x.transmittance, y.transmittance
    elif isinstance(x, jerlov.Water):
        x, y = x.a(450.0), y.a(450.0)
    elif isinstance(x, jerlov.Scene):
        x, y = x.downwelling, y.downwelling
    elif isinstance(x, jerlov.ParProfile):
        x, y = x.fraction, y.fraction
    elif isinstance(x, jerlov.KdClassification):
        x, y = x.distances, y.distances
    elif isinstance(x, jerlov.Backscattering):
        x, y = x.bb, y.bb
    return np.array_equal(np.asarray(x), np.asarray(y))


KD = jerlov.water("III", source="austin1986")
CASES = {
    # name: (function, positional-only names, positional args, keyword args)
    "Water": (lambda *a, **k: jerlov.Water(*a, a=[0.1, 0.2], **k),
              ["wavelengths"], ([400.0, 500.0],),
              dict(wavelengths=[400.0, 500.0])),
    "Water.from_measurements": (
        jerlov.Water.from_measurements, ["wavelengths"],
        ([400.0, 500.0], [0.1, 0.2]),
        dict(wavelengths=[400.0, 500.0], a=[0.1, 0.2])),
    "Water.a": (lambda *a, **k: _water().a(*a, **k), ["wl"],
                (500.0,), dict(wl=500.0)),
    "Water.b": (lambda *a, **k: _water().b(*a, **k), ["wl"],
                (500.0,), dict(wl=500.0)),
    "Water.c": (lambda *a, **k: _water().c(*a, **k), ["wl"],
                (500.0,), dict(wl=500.0)),
    "Water.kd": (lambda *a, **k: _kd_water().kd(*a, **k), ["wl"],
                 (500.0,), dict(wl=500.0)),
    "Water.kd_hydrolight": (
        lambda *a, **k: _kd_water().kd_hydrolight(*a, **k), ["wl"],
        (500.0,), dict(wl=500.0)),
    "Water.bb": (lambda *a, **k: _water().bb(*a, backscatter_ratio=0.01,
                                             **k),
                 ["wl"], (500.0,), dict(wl=500.0)),
    "Water.uncertainty": (
        lambda *a, **k: _measured().uncertainty(*a, **k),
        ["quantity", "wl"], ("a", 450.0), dict(quantity="a", wl=450.0)),
    "pure_water_absorption": (jerlov.pure_water_absorption,
                              ["wavelength_nm"], (500.0,),
                              dict(wavelength_nm=500.0)),
    "pure_water_vsf": (
        lambda *a, **k: jerlov.pure_water_vsf(*a, salinity_psu=37.0, **k),
        ["angle_deg", "wavelength_nm"], (120.0, 500.0),
        dict(angle_deg=120.0, wavelength_nm=500.0)),
    "pure_water_backscattering": (
        lambda *a, **k: jerlov.pure_water_backscattering(
            *a, salinity_psu=37.0, **k),
        ["wavelength_nm"], (500.0,), dict(wavelength_nm=500.0)),
    "pure_water_scattering": (
        lambda *a, **k: jerlov.pure_water_scattering(
            *a, salinity_psu=37.0, **k),
        ["wavelength_nm"], (500.0,), dict(wavelength_nm=500.0)),
    "bb_from_vsf": (
        lambda *a, **k: jerlov.bb_from_vsf(*a, salinity_psu=37.0, **k),
        ["beta", "angle_deg", "wavelength_nm"], (0.002, 140.0, 532.0),
        dict(beta=0.002, angle_deg=140.0, wavelength_nm=532.0)),
    "b_from_c": (lambda *a, **k: jerlov.b_from_c(*a, bw=0.0019, cw=0.0659,
                                                 **k),
                 ["c", "wavelength_nm"], (0.5, 555.0),
                 dict(c=0.5, wavelength_nm=555.0)),
    "kd_spectrum": (jerlov.kd_spectrum, ["kd", "wavelength_nm", "at"],
                    (0.06, 490.0, [440.0, 550.0]),
                    dict(kd=0.06, wavelength_nm=490.0, at=[440.0, 550.0])),
    "spectrum_to_xyz": (jerlov.spectrum_to_xyz, ["spectrum", "wavelengths"],
                        (FLAT, WL), dict(spectrum=FLAT, wavelengths=WL)),
    "spectrum_to_srgb": (
        lambda *a, **k: jerlov.spectrum_to_srgb(*a, white=FLAT, **k),
        ["spectrum", "wavelengths"], (FLAT, WL),
        dict(spectrum=FLAT, wavelengths=WL)),
    "integrate_response": (
        jerlov.integrate_response,
        ["spectrum", "wavelengths", "response", "response_wavelengths"],
        (FLAT, WL, FLAT, WL),
        dict(spectrum=FLAT, wavelengths=WL, response=FLAT,
             response_wavelengths=WL)),
    "Scene": (lambda *a, **k: jerlov.Scene(_water(), *a, **k),
              ["water", "downwelling", "wavelengths"], (FLAT, WL),
              dict(downwelling=FLAT, wavelengths=WL)),
    "Scene.at_depth": (
        lambda *a, **k: jerlov.Scene.at_depth(_water(), 10.0, *a, kd=KD,
                                              **k),
        ["water", "depth_m", "surface_downwelling", "wavelengths"],
        (FLAT, WL), dict(surface_downwelling=FLAT, wavelengths=WL)),
    "veiling_radiance_estimate": (
        lambda *a, **k: jerlov.veiling_radiance_estimate(
            _water(), *a, backscatter_ratio=0.01, **k),
        ["water", "downwelling", "wavelengths"], (FLAT, WL),
        dict(downwelling=FLAT, wavelengths=WL)),
    "descend": (jerlov.descend,
                ["surface_water_type", "depth_m", "wavelengths"],
                ("III", 20.0, [500.0]),
                dict(surface_water_type="III", depth_m=20.0,
                     wavelengths=[500.0])),
    "par_profile": (
        lambda *a, **k: jerlov.par_profile(*a, depths_m=[0.0, 10.0], kd=KD,
                                           unit="energy", **k),
        ["surface_downwelling", "wavelengths"], (FLAT, WL),
        dict(surface_downwelling=FLAT, wavelengths=WL)),
    "classify_kd": (jerlov.classify_kd, ["wavelengths", "kd"],
                    ([490.0], [0.03]), dict(wavelengths=[490.0], kd=[0.03])),
}

FUNCTIONS = {
    "Water": jerlov.Water.__init__,
    "Water.from_measurements": jerlov.Water.from_measurements,
    "Water.a": jerlov.Water.a, "Water.b": jerlov.Water.b,
    "Water.c": jerlov.Water.c, "Water.kd": jerlov.Water.kd,
    "Water.kd_hydrolight": jerlov.Water.kd_hydrolight,
    "Water.bb": jerlov.Water.bb, "Water.uncertainty": jerlov.Water.uncertainty,
    "Scene": jerlov.Scene.__init__, "Scene.at_depth": jerlov.Scene.at_depth,
}


@pytest.mark.parametrize("name", sorted(CASES))
def test_the_wavelengths_are_positional_only(name):
    function = FUNCTIONS.get(name) or getattr(jerlov, name)
    parameters = inspect.signature(function).parameters.values()
    positional_only = [p.name for p in parameters
                       if p.kind is p.POSITIONAL_ONLY]
    assert [n for n in positional_only if n not in ("self", "cls")] \
        == CASES[name][1]


@pytest.mark.parametrize("name", sorted(CASES))
def test_a_keyword_still_gives_the_same_answer_with_a_warning(name):
    function, names, args, kwargs = CASES[name]
    with warnings.catch_warnings():
        warnings.simplefilter("error", FutureWarning)
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        # 400-700 nm leaves a little of the colour matching functions out.
        warnings.simplefilter("ignore", jerlov.CoverageWarning)
        expected = function(*args)
    value, caught = _quietly(lambda: function(**kwargs))
    assert _same(value, expected)
    assert len(caught) == 1
    message = str(caught[0].message)
    assert "by position, not by keyword" in message
    assert all(n in message for n in names if n in kwargs)
    assert caught[0].filename == __file__


def test_only_the_keywords_after_the_positions_given_are_moved():
    value, caught = _quietly(
        lambda: jerlov.kd_spectrum(0.06, 490.0, at=[440.0, 550.0]))
    assert np.array_equal(value, jerlov.kd_spectrum(0.06, 490.0,
                                                    [440.0, 550.0]))
    assert len(caught) == 1 and "pass at by position" in str(
        caught[0].message)
    with pytest.raises(TypeError):
        jerlov.kd_spectrum(0.06, 490.0, [440.0], at=[550.0])


# -- what is exported -------------------------------------------------------

def test_haltrins_constants_are_exported():
    assert {"HALTRIN1999", "ScatteringConstants"} <= set(jerlov.__all__)
    assert isinstance(jerlov.HALTRIN1999, jerlov.ScatteringConstants)
    assert isinstance(jerlov.get_source("williamson2022").scattering,
                      jerlov.ScatteringConstants)


def test_every_exported_name_exists():
    missing = [n for n in jerlov.__all__ if not hasattr(jerlov, n)]
    assert not missing
    assert len(jerlov.__all__) == len(set(jerlov.__all__)) == 77


@source_tree
def test_examples_import_only_from_the_package_itself():
    """`jerlov.<module>` is not promised; one example imported Haltrin's
    constants from `jerlov.sources` because they were not exported."""
    pattern = re.compile(r"^\s*(from\s+jerlov\.\w+|import\s+jerlov\.\w+)",
                         re.MULTILINE)
    offenders = [p.name for p in sorted(ROOT.glob("examples/*.py"))
                 if pattern.search(p.read_text())]
    assert not offenders, offenders


@source_tree
def test_the_readme_shows_no_old_way_of_calling():
    readme = (ROOT / "README.md").read_text()
    for old in ("gernez2009_cv_by_sun_zenith", "wavelength_nm=", "at=[",
                "angle_deg="):
        assert old not in readme, old

"""Which Jerlov type a measured Kd spectrum is nearest."""

from __future__ import annotations

import warnings

import numpy as np
import pytest

import jerlov

WL = np.arange(400.0, 701.0, 10.0)


def _kd(water_type, source="jerlov1976", wl=WL):
    return jerlov.water(water_type, source=source).kd(wl)


@pytest.mark.parametrize("water_type", jerlov.get_source("jerlov1976").water_types)
def test_every_type_classifies_as_itself(water_type):
    result = jerlov.classify_kd(WL, _kd(water_type))
    assert result.water_type == water_type
    assert result.distances[0] == (water_type, 0.0)
    assert result.beyond is None


def test_the_distance_is_the_rms_of_the_log_ratio():
    result = jerlov.classify_kd(WL, _kd("II") * 1.1)
    assert result.water_type == "II"
    assert dict(result.distances)["II"] == pytest.approx(np.log(1.1))
    distances = [d for _, d in result.distances]
    assert distances == sorted(distances)


def test_beyond_the_ends_of_the_classification_is_said():
    clear = jerlov.classify_kd(WL, _kd("I") * 0.5)
    assert (clear.water_type, clear.beyond) == ("I", "clearer")
    murky = jerlov.classify_kd(WL, _kd("9C") * 2.0)
    assert (murky.water_type, murky.beyond) == ("9C", "more turbid")
    assert "more turbid than every type" in repr(murky)


def test_gaps_are_left_out_and_recorded():
    kd = _kd("III", wl=np.array([320.0, 400.0, 500.0, 600.0]))
    kd[2] = np.nan
    # 7C and 9C have no Kd below 350 nm in Jerlov (1976).
    result = jerlov.classify_kd([320.0, 400.0, 500.0, 600.0], kd)
    assert result.water_type == "III"
    assert result.excluded_nm == (320.0, 500.0)
    assert result.wavelengths.tolist() == [400.0, 600.0]


def test_one_wavelength_is_allowed():
    result = jerlov.classify_kd(490.0, float(_kd("IB", wl=490.0)))
    assert result.water_type == "IB"
    assert repr(result).endswith("(jerlov1976, 1 wavelength)>")


def test_other_sources_compare_with_their_own_types():
    result = jerlov.classify_kd(WL, _kd("1C", "austin1986"), source="austin1986")
    assert result.water_type == "1C"
    assert {t for t, _ in result.distances} == set(
        jerlov.get_source("austin1986").water_types)


def test_flagged_reference_values_warn_once():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        jerlov.classify_kd([500.0, 705.0], [0.05, 0.6])
    assert len(caught) == 1
    assert issubclass(caught[0].category, jerlov.ProvenanceWarning)
    assert "705 nm for I, IA, IB" in str(caught[0].message)
    assert caught[0].filename == __file__
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        jerlov.classify_kd([500.0, 600.0], [0.05, 0.3])


def test_what_cannot_be_compared_is_refused():
    with pytest.raises(jerlov.MissingQuantityError, match="no Kd"):
        jerlov.classify_kd(WL, _kd("II"), source="williamson2022")
    with pytest.raises(ValueError, match="does not extrapolate"):
        jerlov.classify_kd([250.0, 500.0], [1.0, 0.05])
    with pytest.raises(ValueError, match="positive"):
        jerlov.classify_kd([450.0, 500.0], [0.0, 0.05])
    with pytest.raises(ValueError, match="finite"):
        jerlov.classify_kd([450.0, 500.0], [np.inf, 0.05])
    with pytest.raises(ValueError, match="one value per wavelength"):
        jerlov.classify_kd(WL, [0.05])
    with pytest.raises(jerlov.MissingQuantityError, match="no wavelength"):
        jerlov.classify_kd([500.0], [np.nan])


def test_types_narrows_the_comparison_and_keeps_more_wavelengths():
    """Solonenko & Mobley's 3C and 5C have no Kd from 600 nm on, which
    took those wavelengths out of every comparison."""
    wl = np.arange(400.0, 701.0, 25.0)
    oceanic = ("I", "IA", "IB", "II", "III")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        kd = jerlov.water("II", source="solonenko2015").kd(wl)
        every = jerlov.classify_kd(wl, kd, source="solonenko2015")
        some = jerlov.classify_kd(wl, kd, source="solonenko2015",
                                  types=oceanic)
    assert every.excluded_nm == (600.0, 625.0, 650.0, 675.0, 700.0)
    assert some.excluded_nm == ()
    assert some.water_type == "II"
    assert {t for t, _ in some.distances} == set(oceanic)


def test_types_must_be_types_of_the_source():
    with pytest.raises(KeyError, match="does not cover Jerlov '3C'"):
        jerlov.classify_kd(WL, _kd("II"), source="austin1986",
                           types=("II", "IA", "3C"))
    with pytest.raises(ValueError, match="at least one"):
        jerlov.classify_kd(WL, _kd("II"), types=())
    with pytest.raises(ValueError, match="more than once"):
        jerlov.classify_kd(WL, _kd("II"), types=("II", "II"))
    # A string is one type, not a sequence of letters.
    alone = jerlov.classify_kd(WL, _kd("III"), types="III")
    assert alone.distances == (("III", 0.0),)

"""Morel et al. (2007), the clearest waters: DECISIONS.md section 102."""

import warnings

import numpy as np
import pytest

import jerlov


def _stations():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        return jerlov.morel2007_stations()


def test_table_1_as_printed():
    st = _stations()
    assert [s.station for s in st] == ["STB-4", "STB-5", "STB-7", "STB-8",
                                       "GYR-4", "GYR-5", "STB-14", "STB-15"]
    stb7 = st[2]
    assert (stb7.chl_5m_mg_m3, stb7.kd_420_per_m, stb7.kd_310_per_m,
            stb7.zeu_m, stb7.r_max_percent) == (0.022, 0.0134, 0.068, 172.0,
                                                13.5)
    assert st[-1].ay2_310_per_m == 0.0482 and st[0].date_2004 == "06-Nov"


def test_the_likely_misprint_is_flagged_and_warns():
    aw1 = jerlov.pure_water_absorption_table(310.0, source="morel2007")
    aw2 = jerlov.pure_water_absorption_table(310.0, source="morel2007_aw2")
    st = _stations()
    off = [s.station for s in st
           if abs(s.ay2_310_per_m - s.ay1_310_per_m - (aw1 - aw2)) > 2e-4]
    assert off == ["GYR-5", "STB-14"]
    assert [s.station for s in st if s.status == "suspect"] == off
    with pytest.warns(jerlov.ProvenanceWarning, match="GYR-5 and STB-14"):
        jerlov.morel2007_stations()


def test_table_2_and_pope_fry():
    aw = jerlov.pure_water_absorption_table(np.arange(420.0, 501.0, 10.0),
                                            source="morel2007")
    pope = jerlov.pure_water_absorption_table(
        np.arange(420.0, 501.0, 10.0), source="pope1997")
    np.testing.assert_allclose(aw, pope, atol=5e-6)
    at_435 = jerlov.pure_water_absorption_table(435.0, source="morel2007")
    assert at_435 == 0.00565
    assert jerlov.pure_water_absorption_table(
        435.0, source="pope1997") == 0.00530
    assert jerlov.pure_water_absorption_table(
        370.0, source="morel2007") == jerlov.pure_water_absorption_table(
        370.0, source="morel2007_aw2") == 0.00602
    with pytest.raises(ValueError):
        jerlov.pure_water_absorption_table(375.0, source="morel2007_aw2")
    with pytest.raises(ValueError):
        jerlov.pure_water_absorption_table(505.0, source="morel2007")


def test_fig_5_quotes_morel_maritorena_at_420():
    from jerlov import _data
    wl, kw, e, chi, _ = _data.morel2001()
    i = list(wl).index(420.0)
    assert (round(chi[i], 4), round(e[i], 3)) == (0.1227, 0.659)

"""Mobley's rho tables and Rrs from above-water radiances: DECISIONS.md
section 99, DATA.md section 43."""

import csv
import importlib.resources
import io
import warnings

import numpy as np
import pytest

import jerlov


def _rho(source, wind, sun, nadir, azimuth):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        return jerlov.mobley_rho(source=source, wind_speed=wind,
                                 sun_zenith_deg=sun, view_nadir_deg=nadir,
                                 view_azimuth_deg=azimuth)


def _rows(source):
    text = (importlib.resources.files("jerlov.data")
            / f"{source}_rho.csv").read_text()
    return list(csv.DictReader(io.StringIO(text)))


@pytest.mark.parametrize("source,count,winds,suns", [
    ("mobley1999", 8496, [0, 2, 4, 6, 8, 10, 12, 14],
     [0, 10, 20, 30, 40, 50, 60, 70, 80]),
    ("mobley2015", 11800, [0, 2, 4, 5, 6, 8, 10, 12, 14, 15],
     [0, 10, 20, 30, 40, 50, 60, 70, 80, 87.5]),
])
def test_the_shipped_grids(source, count, winds, suns):
    rows = _rows(source)
    assert len(rows) == count
    assert sorted({float(r["wind_speed"]) for r in rows}) == winds
    assert sorted({float(r["sun_zenith_deg"]) for r in rows}) == suns
    # 118 directions per block: the nadir cap and nine rings of 13.
    assert count == len(winds) * len(suns) * 118


@pytest.mark.parametrize("source", ["mobley1999", "mobley2015"])
def test_every_tabulated_value_comes_back(source):
    for r in _rows(source)[::37]:
        got = _rho(source, float(r["wind_speed"]), float(r["sun_zenith_deg"]),
                   float(r["view_nadir_deg"]), float(r["view_azimuth_deg"]))
        assert got == float(r["rho"])


def test_against_mobley_1999():
    # Table 1 (p. 7451): clear sky, 10 m/s, sun 30, view (40, 135), 0.0337.
    # The distributed table gives 0.0336 (DATA.md section 43).
    assert _rho("mobley1999", 10.0, 30.0, 40.0, 135.0) == 0.0336
    # The abstract: rho = 0.028 is acceptable at (40, 135) below 5 m/s.
    assert [_rho("mobley1999", w, 30.0, 40.0, 135.0)
            for w in (0.0, 2.0, 4.0)] == [0.0256, 0.0264, 0.0276]


def test_against_mobley_2015():
    # p. 4846: at nadir 40, "0.0179-0.0411 for 5 m/s" over the sun at 30
    # and 60 and the azimuth at 90 and 135 (Fig. 18).
    five = [_rho("mobley2015", 5.0, s, 40.0, a)
            for s in (30.0, 60.0) for a in (90.0, 135.0)]
    assert (round(min(five), 4), round(max(five), 4)) == (0.0179, 0.0411)
    # The same for 10 m/s the text gives as 0.0195-0.0458; the
    # distributed table, which calls itself preliminary, 0.0199-0.0457.
    ten = [_rho("mobley2015", 10.0, s, 40.0, a)
           for s in (30.0, 60.0) for a in (90.0, 135.0)]
    assert (round(min(ten), 4), round(max(ten), 4)) == (0.0199, 0.0457)
    # Fig. 19: 10 m/s, sun 40, (40, 135): "rho = 0.045".
    assert round(_rho("mobley2015", 10.0, 40.0, 40.0, 135.0), 3) == 0.045


@pytest.mark.parametrize("source", ["mobley1999", "mobley2015"])
def test_linear_between_wind_and_sun_points(source):
    # 6 and 8 m/s, 30 and 40 degrees are neighbours in both tables.
    a = _rho(source, 6.0, 30.0, 40.0, 135.0)
    b = _rho(source, 8.0, 30.0, 40.0, 135.0)
    c = _rho(source, 6.0, 40.0, 40.0, 135.0)
    d = _rho(source, 8.0, 40.0, 40.0, 135.0)
    assert _rho(source, 6.5, 30.0, 40.0, 135.0) == pytest.approx(
        0.75 * a + 0.25 * b, rel=1e-12)
    assert _rho(source, 7.0, 35.0, 40.0, 135.0) == pytest.approx(
        (a + b + c + d) / 4, rel=1e-12)


def test_nadir_ignores_the_azimuth_and_arrays_broadcast():
    assert _rho("mobley1999", 6.0, 30.0, 0.0, 0.0) \
        == _rho("mobley1999", 6.0, 30.0, 0.0, 77.0)
    out = _rho("mobley1999", np.array([2.0, 6.0]), 30.0,
               np.array([[30.0], [40.0]]), 135.0)
    assert out.shape == (2, 2)
    assert out[1, 1] == _rho("mobley1999", 6.0, 30.0, 40.0, 135.0)
    assert isinstance(_rho("mobley1999", 6.0, 30.0, 40.0, 135.0), float)


def test_only_the_2015_table_warns():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", jerlov.ProvenanceWarning)
        jerlov.mobley_rho(source="mobley1999", wind_speed=5.0,
                          sun_zenith_deg=30.0, view_nadir_deg=40.0,
                          view_azimuth_deg=135.0)
    assert not caught
    with pytest.warns(jerlov.ProvenanceWarning, match="preliminary"):
        jerlov.mobley_rho(source="mobley2015", wind_speed=5.0,
                          sun_zenith_deg=30.0, view_nadir_deg=40.0,
                          view_azimuth_deg=135.0)


@pytest.mark.parametrize("kwargs", [
    dict(source=None), dict(source="mobley"),
    dict(wind_speed=15.0), dict(wind_speed=-1.0),
    dict(sun_zenith_deg=85.0), dict(sun_zenith_deg=np.nan),
    dict(view_nadir_deg=45.0), dict(view_nadir_deg=90.0),
    dict(view_azimuth_deg=140.0), dict(view_azimuth_deg=225.0),
    dict(wind_speed=np.inf),
])
def test_refusals(kwargs):
    args = dict(source="mobley1999", wind_speed=5.0, sun_zenith_deg=30.0,
                view_nadir_deg=40.0, view_azimuth_deg=135.0)
    args.update(kwargs)
    with pytest.raises(ValueError):
        jerlov.mobley_rho(**args)


def test_no_source_is_chosen_for_you():
    with pytest.raises(TypeError):
        jerlov.mobley_rho(wind_speed=5.0, sun_zenith_deg=30.0,
                          view_nadir_deg=40.0, view_azimuth_deg=135.0)


def test_rrs_from_above_water():
    assert jerlov.rrs_from_above_water(0.012, 0.1, 1.5, rho=0.028) \
        == pytest.approx((0.012 - 0.0028) / 1.5, rel=1e-12)
    out = jerlov.rrs_from_above_water([0.01, np.nan], 0.5, 1.0, rho=0.028)
    assert out[0] == pytest.approx(-0.004) and np.isnan(out[1])
    with pytest.raises(TypeError):
        jerlov.rrs_from_above_water(0.01, 0.1, 1.0)
    for bad in (dict(ed=0.0), dict(rho=-0.01), dict(lt=np.inf)):
        args = dict(lt=0.01, lsky=0.1, ed=1.0, rho=0.028)
        args.update(bad)
        with pytest.raises(ValueError):
            jerlov.rrs_from_above_water(args["lt"], args["lsky"],
                                        args["ed"], rho=args["rho"])

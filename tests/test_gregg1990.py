"""The clear-sky irradiance at the sea surface, Gregg and Carder (1990)
(DECISIONS.md section 76).

Table 1 is transcribed in tools/build_gregg1990.py, which checks it
against Bird and Riordan (1984) before writing.
"""

from __future__ import annotations

import csv
import io
import math
from importlib.resources import files

import numpy as np
import pytest

import jerlov

WL = np.arange(350.0, 701.0)
# Table 5's standard conditions (p. 1670). The day is not printed; it
# cancels from every share and every relative deviation below.
STANDARD = dict(sun_zenith_deg=60.0, day_of_year=172, pressure_hpa=1013.25,
                air_mass_type=1, relative_humidity=80.0,
                precipitable_water_cm=1.5, wind_speed_24h=3.0,
                wind_speed=5.0, ozone_du=300.0, visibility_km=10.0)
# Table 5, as printed: (low, high), rms %, largest %, its wavelength, and
# the diffuse share of the global irradiance at the low and the high end.
TABLE5 = {
    "pressure_hpa": ((1013.25 - 15, 1013.25 + 15), 0.5, 0.8, 397, 56, 56),
    "air_mass_type": ((1, 10), 7.4, 11.2, 366, 56, 54),
    "relative_humidity": ((0, 99), -3.7, -4.7, 365, 55, 56),
    "precipitable_water_cm": ((0, 5), 3.9, 20.0, 590, 56, 56),
    "wind_speed_24h": ((0, 10), -0.2, -0.3, 358, 56, 56),
    "wind_speed": ((0, 20), -5.0, -7.3, 377, 55, 56),
    "visibility_km": ((5, 25), -12.0, -15.5, 381, 79, 34),
    "ozone_du": ((100, 600), 7.0, 13.2, 602, 56, 56),
}


def _model(**changes):
    kw = dict(STANDARD)
    kw.update(changes)
    return jerlov.gregg1990_irradiance(WL, **kw)


def _share(result):
    return 100 * result.diffuse_above.sum() / result.above.sum()


def _table():
    text = files("jerlov.data").joinpath("gregg1990_table1.csv").read_text(
        encoding="utf-8")
    return list(csv.DictReader(io.StringIO(text)))


def test_the_table_rows():
    rows = _table()
    assert [int(r["wavelength_nm"]) for r in rows] == list(range(350, 701))
    by = {int(r["wavelength_nm"]): r for r in rows}
    # A few rows as printed (pp. 1662-1663), including the four oxygen
    # entries the OCR layer misreads and the split 689 nm row.
    assert [by[350][k] for k in ("H0_W_m2_nm", "a_ozone_per_cm")] == [
        "0.961", "0.009"]
    assert [by[590][k] for k in ("a_water_vapour_per_cm",
                                 "a_oxygen_per_cm")] == ["0.700", "0.000"]
    assert [by[w]["a_oxygen_per_cm"] for w in (676, 677, 681, 685)] == [
        "0.000"] * 4
    assert [by[689][k] for k in ("H0_W_m2_nm", "a_ozone_per_cm",
                                 "a_water_vapour_per_cm",
                                 "a_oxygen_per_cm")] == [
        "1.444", "0.030", "0.001", "0.505"]
    assert by[687]["a_oxygen_per_cm"] == "0.810"


def test_table_5_diffuse_shares_to_the_printed_percent():
    assert round(_share(_model())) == 56
    for name, ((lo, hi), _, _, _, s_lo, s_hi) in TABLE5.items():
        assert round(_share(_model(**{name: lo}))) == s_lo, name
        assert round(_share(_model(**{name: hi}))) == s_hi, name


@pytest.mark.parametrize("name", sorted(TABLE5))
def test_table_5_deviations_to_their_order(name):
    """The paper does not define its rms closely enough to reproduce it;
    the sign, the size within 25 percent and the wavelength of the largest
    deviation within 10 nm are checked (DECISIONS.md section 76). The mean
    wind changes the irradiance by 0.15-0.27 percent at every wavelength,
    so where the largest change falls is not checked for it."""
    (lo, hi), rms, largest, at, _, _ = TABLE5[name]
    low = _model(**{name: lo}).above
    high = _model(**{name: hi}).above
    rel = 100 * (low - high) / low
    got_rms = math.copysign(np.sqrt(np.mean(rel ** 2)), np.sum(low - high))
    i = int(np.argmax(np.abs(rel)))
    assert np.sign(got_rms) == np.sign(rms)
    assert abs(got_rms) == pytest.approx(abs(rms), rel=0.25)
    assert abs(rel[i]) == pytest.approx(abs(largest), rel=0.25)
    if name != "wind_speed_24h":
        assert abs(WL[i] - at) <= 10


def test_table_4():
    """At 60 degrees: V 16 km with AM 10, then V 8 km with AM 1, direct
    against diffuse 59:41 and 37:63, alpha 1.2 and 0.2, and the global
    irradiance over 350-700 nm about 2 W m-2 less in the second (p. 1669).
    The other conditions are not printed; Table 5's are used."""
    continental = _model(visibility_km=16.0, air_mass_type=10)
    marine = _model(visibility_km=8.0, air_mass_type=1)
    for result, direct, alpha in ((continental, 59, 1.2), (marine, 37, 0.2)):
        assert round(100 * result.direct_above.sum()
                     / result.above.sum()) == direct
        assert round(result.angstrom_exponent, 1) == alpha
    loss = continental.above.sum() - marine.above.sum()
    assert 1.0 < loss < 3.0


def test_the_sea_surface():
    calm = _model(sun_zenith_deg=0.0, wind_speed=0.0)
    n = 1.341
    assert calm.direct_reflectance == pytest.approx(((n - 1) / (n + 1)) ** 2,
                                                    rel=1e-12)
    assert calm.diffuse_reflectance == 0.066
    # Fresnel just short of 40 degrees against eq. (46) taking over there,
    # with a wind (3 m/s) that makes no foam.
    just_below = _model(sun_zenith_deg=40.0 - 1e-9,
                        wind_speed=3.0).direct_reflectance
    assert just_below == pytest.approx(0.0253, abs=0.0002)
    assert _model(sun_zenith_deg=40.0,
                  wind_speed=3.0).direct_reflectance == 0.0253
    # Foam at 20 m/s is about 2.3 percent (Fig. 2, p. 1667).
    windy = _model(sun_zenith_deg=20.0, wind_speed=20.0)
    foam = windy.diffuse_reflectance - 0.057
    assert 0.021 < foam < 0.024
    assert np.allclose(windy.direct_below,
                       windy.direct_above * (1 - windy.direct_reflectance),
                       rtol=1e-14, atol=0)


def test_written_out_at_one_wavelength():
    wl = 600.0
    r = jerlov.gregg1990_irradiance(wl, **STANDARD)
    rows = {int(x["wavelength_nm"]): x for x in _table()}[600]
    h0, a_oz, a_w, a_o = (float(rows[k]) for k in (
        "H0_W_m2_nm", "a_ozone_per_cm", "a_water_vapour_per_cm",
        "a_oxygen_per_cm"))
    th, d = 60.0, 172
    lam = 0.6
    f0 = h0 * (1 + 0.0167 * math.cos(2 * math.pi * (d - 3) / 365)) ** 2
    c = math.cos(math.radians(th))
    m = 1 / (c + 0.15 * (93.885 - th) ** -1.253)
    mp = m
    moz = 1.0035 / (c ** 2 + 0.007) ** 0.5
    tr = math.exp(-mp / (115.6406 * lam ** 4 - 1.335 * lam ** 2))
    toz = math.exp(-a_oz * 0.3 * moz)
    to = math.exp(-1.41 * a_o * mp / (1 + 118.3 * a_o * mp) ** 0.45)
    tw = math.exp(-0.2385 * a_w * 1.5 * m / (1 + 20.07 * a_w * 1.5 * m)
                  ** 0.45)
    alpha = r.angstrom_exponent
    tau = 0.391 * 0.55 ** alpha * lam ** -alpha
    omega = (-0.0032 + 0.972) * math.exp(3.06e-4 * 80)
    taa = math.exp(-(1 - omega) * tau * m)
    tas = math.exp(-omega * tau * m)
    g = -0.1417 * alpha + 0.82
    b3 = math.log(1 - g)
    b1 = b3 * (1.459 + b3 * (0.1595 + 0.4129 * b3))
    b2 = b3 * (0.0783 + b3 * (-0.3824 - 0.5874 * b3))
    fa = 1 - 0.5 * math.exp((b1 + b2 * c) * c)
    direct = f0 * c * tr * math.exp(-tau * m) * toz * to * tw
    diffuse = f0 * c * toz * to * tw * taa * (
        (1 - tr ** 0.95) * 0.5 + tr ** 1.5 * (1 - tas) * fa)
    assert float(r.direct_above) == pytest.approx(direct, rel=1e-12)
    assert float(r.diffuse_above) == pytest.approx(diffuse, rel=1e-12)
    foam = 2.2e-5 * 1.2e3 * (0.62 + 1.56 / 5) * 1e-3 * 25 - 4.0e-4
    rho_d = 0.0253 * math.exp((-7.14e-4 * 5 + 0.0618) * 20) + foam
    assert r.direct_reflectance == pytest.approx(rho_d, rel=1e-12)
    assert r.diffuse_reflectance == pytest.approx(0.057 + foam, rel=1e-12)


def test_the_aerosol_by_optical_thickness():
    by_v = _model()
    by_tau = _model(visibility_km=None, aerosol_optical_thickness_550=0.391)
    assert np.allclose(by_v.above, by_tau.above, rtol=1e-12, atol=0)
    clear = _model(visibility_km=None, aerosol_optical_thickness_550=0.0)
    assert np.all(clear.aerosol_optical_thickness == 0)


def test_shapes():
    one = jerlov.gregg1990_irradiance(500, **STANDARD)
    assert one.above.shape == ()
    grid = jerlov.gregg1990_irradiance(np.array([[400, 500], [600, 700]]),
                                       **STANDARD)
    assert grid.below.shape == (2, 2)


def test_refusals():
    f = jerlov.gregg1990_irradiance
    for wl in (349, 701, 500.5, np.nan):
        with pytest.raises(ValueError, match="wavelength"):
            f(wl, **STANDARD)
    bad = {"sun_zenith_deg": (-1, 90, np.nan), "day_of_year": (0, 367),
           "pressure_hpa": (0, -5), "air_mass_type": (0.5, 11),
           "relative_humidity": (-1, 100), "precipitable_water_cm": (-0.1,),
           "wind_speed_24h": (-1,), "wind_speed": (-1,), "ozone_du": (-1,),
           "visibility_km": (0, -1, np.inf)}
    for name, values in bad.items():
        for value in values:
            with pytest.raises(ValueError, match=name):
                f(500, **{**STANDARD, name: value})
    # Both is a ValueError and neither a MissingQuantityError, as for
    # Water.bb's two ratios (DECISIONS.md section 81; TypeError to 1.10.2).
    with pytest.raises(ValueError, match="exactly one"):
        f(500, **{**STANDARD, "aerosol_optical_thickness_550": 0.2})
    with pytest.raises(jerlov.MissingQuantityError, match="exactly one"):
        f(500, **{**STANDARD, "visibility_km": None})
    without = dict(STANDARD)
    del without["ozone_du"]
    with pytest.raises(TypeError):
        f(500, **without)

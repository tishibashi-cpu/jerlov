"""The quasi-analytical algorithm (DECISIONS.md section 67).

QAA_v6 is checked against the results its author's spreadsheet stored for
12 stations; the IOCCG Report 5 version against the report's own statistics
on its synthetic data, Table 10.1. The data are in tests/data/, written by
tools/qaa_test_data.py from files the IOCCG distributes. The synthetic
data set is cited as: IOCCG (2006), Remote Sensing of Inherent Optical
Properties: Fundamentals, Tests of Algorithms, and Applications, Lee, Z.-P.
(ed.), Reports of the International Ocean-Colour Coordinating Group No. 5,
IOCCG, Dartmouth, Canada."""

from __future__ import annotations

import csv
import math
import pathlib

import numpy as np
import pytest

import jerlov

DATA = pathlib.Path(__file__).resolve().parent / "data"

#: The spreadsheet's bands and pure water: aw at 555 and 670 nm and bbw on
#: its QAA_v6 sheet, aw at 412-510 nm on its decomposition sheet.
V6_NM = [412.0, 443.0, 489.0, 510.0, 555.0, 670.0]
V6_BANDS = {"412": 412, "443": 443, "490": 489, "55x": 555, "670": 670}
V6_WATER = (np.array(V6_NM), np.array([0.0031, 0.0048, 0.0132, 0.0302,
                                       0.0596, 0.439]),
            np.array([0.0034, 0.0025, 0.00158, 0.00133, 0.0009, 0.00034]))

R5_NM = [410.0, 440.0, 490.0, 510.0, 555.0, 670.0]
R5_BANDS = {"410": 410, "440": 440, "490": 490, "510": 510, "555": 555,
            "670": 670}

#: Table 10.1, p. 76: RMSE and bias in log10 for the synthetic data,
#: sun at 30 degrees.
TABLE_10_1 = {"a(410)": (0.061, 0.016), "a(440)": (0.060, 0.016),
              "a(490)": (0.062, -0.005), "bbp(440)": (0.081, 0.008),
              "bbp(555)": (0.079, -0.029)}


def _rows(name):
    with open(DATA / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _column(rows, key):
    return np.array([float(r[key]) for r in rows])


@pytest.fixture(scope="module")
def spreadsheet():
    return _rows("qaa_v6_spreadsheet.csv")


@pytest.fixture(scope="module")
def v6(spreadsheet):
    rrs = np.stack([_column(spreadsheet, f"Rrs_{w:g}") for w in V6_NM], -1)
    return jerlov.qaa_v6(V6_NM, rrs, bands=V6_BANDS, pure_water=V6_WATER)


@pytest.fixture(scope="module")
def synthetic():
    rows = _rows("ioccg2006_sun30.csv")
    water = _rows("ioccg2006_pure_water.csv")
    pw = tuple(_column(water, k)
               for k in ("wavelength_nm", "aw_per_m", "bbw_per_m"))
    # Report 5, p. 76: Rrs(555) is the mean of Rrs(550) and Rrs(560).
    r555 = 0.5 * (_column(rows, "Rrs_550") + _column(rows, "Rrs_560"))
    rrs = np.stack([_column(rows, "Rrs_410"), _column(rows, "Rrs_440"),
                    _column(rows, "Rrs_490"), _column(rows, "Rrs_510"),
                    r555, _column(rows, "Rrs_670")], -1)
    result = jerlov.qaa_ioccg2006(R5_NM, rrs, bands=R5_BANDS, pure_water=pw)
    return rows, pw, result


def _log_stats(model, true):
    """RMSE as IOCCG Report 5 eq. 2.1 (p. 18), in log10 over N - 2, and
    the mean log10 difference."""
    ok = np.isfinite(model) & (model > 0)
    d = np.log10(model[ok]) - np.log10(true[ok])
    return math.sqrt(np.sum(d ** 2) / (ok.sum() - 2)), float(np.mean(d))


# -- QAA_v6 against its spreadsheet -----------------------------------------

def test_v6_reproduces_the_spreadsheet(spreadsheet, v6):
    for j, w in enumerate(V6_NM[:5]):
        np.testing.assert_allclose(v6.a[:, j],
                                   _column(spreadsheet, f"a_{w:g}"),
                                   rtol=1e-12)
    np.testing.assert_allclose(v6.eta, _column(spreadsheet, "eta"),
                               rtol=1e-12)
    np.testing.assert_allclose(v6.bbp[:, 4], _column(spreadsheet, "bbp_555"),
                               rtol=1e-12)


def test_v6_uses_both_references(spreadsheet, v6):
    """The 12 stations take both branches: 555 nm where Rrs(670) is below
    0.0015, 670 nm elsewhere."""
    r670 = _column(spreadsheet, "Rrs_670")
    np.testing.assert_array_equal(v6.reference_nm,
                                  np.where(r670 < 0.0015, 555.0, 670.0))
    assert set(v6.reference_nm) == {555.0, 670.0}


def test_v6_decomposition_reproduces_the_spreadsheet(spreadsheet, v6):
    np.testing.assert_allclose(v6.adg[:, 1], _column(spreadsheet, "adg_443"),
                               rtol=1e-12)
    for j, w in enumerate(V6_NM[:5]):
        stored = _column(spreadsheet, f"aph_{w:g}")
        if w == 555:
            # The decomposition sheet subtracts aw(555) = 0.0595; the QAA
            # sheet, whose value the test passes, uses 0.0596.
            stored = stored + 0.0595 - 0.0596
        np.testing.assert_allclose(v6.aph[:, j], stored, rtol=0, atol=1e-14)


def test_v6_steps_written_out_for_one_station(spreadsheet, v6):
    r = {w: float(spreadsheet[0][f"Rrs_{w:g}"]) for w in V6_NM}
    rr = {w: x / (0.52 + 1.7 * x) for w, x in r.items()}
    g0, g1 = 0.08945, 0.1247
    u = {w: (-g0 + math.sqrt(g0 ** 2 + 4 * g1 * x)) / (2 * g1)
         for w, x in rr.items()}
    assert r[670] >= 0.0015           # the 670 nm reference
    a670 = 0.439 + 0.39 * (rr[670] / (rr[443] + rr[489])) ** 1.14
    bbp670 = u[670] * a670 / (1 - u[670]) - 0.00034
    eta = 2.0 * (1 - 1.2 * math.exp(-0.9 * rr[443] / rr[555]))
    bbp443 = bbp670 * (670 / 443) ** eta
    a443 = (1 - u[443]) * (0.0025 + bbp443) / u[443]
    assert v6.a[0, 1] == pytest.approx(a443, rel=1e-12)
    assert v6.eta[0] == pytest.approx(eta, rel=1e-12)


def test_v6_constants_are_the_spreadsheets():
    """h0-h2 print as -1.146, -1.366, -0.469 in the document."""
    from jerlov import qaa
    assert qaa._V6_G == (0.08945, 0.1247)
    assert [round(h, 3) for h in qaa._V6_H] == [-1.146, -1.366, -0.469]


# -- IOCCG Report 5 against Table 10.1 -------------------------------------

def test_ioccg2006_reproduces_table_10_1(synthetic):
    rows, pw, q = synthetic
    bbw = {w: np.interp(w, pw[0], pw[2]) for w in (440, 550, 560)}
    bbp555_true = (0.5 * (_column(rows, "bb_550") + _column(rows, "bb_560"))
                   - 0.5 * (bbw[550] + bbw[560]))
    cases = {
        "a(410)": (q.a[:, 0], _column(rows, "a_410")),
        "a(440)": (q.a[:, 1], _column(rows, "a_440")),
        "a(490)": (q.a[:, 2], _column(rows, "a_490")),
        "bbp(440)": (q.bbp[:, 1], _column(rows, "bb_440") - bbw[440]),
        "bbp(555)": (q.bbp[:, 4], bbp555_true),
    }
    for name, (model, true) in cases.items():
        assert np.all(np.isfinite(model) & (model > 0)), name   # N = n = 500
        rmse, bias = _log_stats(model, true)
        table_rmse, table_bias = TABLE_10_1[name]
        assert abs(rmse - table_rmse) <= 0.002 + 1e-9, (name, rmse)
        assert abs(bias - table_bias) <= 0.002 + 1e-9, (name, bias)


def test_ioccg2006_blends_as_eq_10_11(synthetic):
    _, _, q = synthetic
    ref = q.reference_nm
    assert set(ref[np.isfinite(ref)]) <= {555.0, 640.0}
    assert np.all(np.isfinite(q.a))


def test_ioccg2006_steps_written_out_for_one_spectrum(synthetic):
    rows, pw, q = synthetic
    k = int(np.flatnonzero(q.reference_nm == 555.0)[0])
    row = rows[k]
    R = {w: float(row[f"Rrs_{w}"]) for w in (410, 440, 490, 510, 670)}
    R[555] = 0.5 * (float(row["Rrs_550"]) + float(row["Rrs_560"]))
    rr = {w: x / (0.52 + 1.7 * x) for w, x in R.items()}
    u = {w: (-0.0895 + math.sqrt(0.008 + 0.499 * x)) / 0.249
         for w, x in rr.items()}
    rho = math.log10(max(R[440], R[490], R[510]) / R[555])
    kd = 0.0605 + 10 ** (-1.163 - 1.969 * rho + 1.239 * rho ** 2
                         + 0.417 * rho ** 3 - 0.984 * rho ** 4)
    a555 = 0.9 * kd * (1 - 6.8 * R[555]) / (1 + 15.3 * R[555])
    bbw = {w: float(np.interp(w, pw[0], pw[2])) for w in (440, 555)}
    bbp555 = u[555] * a555 / (1 - u[555]) - bbw[555]
    Y = 2.2 * (1 - 1.2 * math.exp(-0.9 * rr[440] / rr[555]))
    a440 = (1 - u[440]) * (bbw[440] + bbp555 * (555 / 440) ** Y) / u[440]
    assert q.a[k, 1] == pytest.approx(a440, rel=1e-12)
    assert q.eta[k] == pytest.approx(Y, rel=1e-12)


# -- what both refuse, and what passes through ------------------------------

@pytest.mark.parametrize("function,nm,bands", [
    (jerlov.qaa_v6, V6_NM, V6_BANDS), (jerlov.qaa_ioccg2006, R5_NM, R5_BANDS)])
def test_bands_must_be_named_and_present(function, nm, bands):
    rrs = np.full(len(nm), 0.003)
    water = (np.array([400.0, 700.0]), np.array([0.01, 0.6]),
             np.array([0.004, 0.0003]))
    function(nm, rrs, bands=bands, pure_water=water)
    missing = dict(bands)
    missing.popitem()
    for bad in (missing, {**bands, "extra": 500}, {**bands,
                                                   next(iter(bands)): 401},
                None):
        with pytest.raises(ValueError):
            function(nm, rrs, bands=bad, pure_water=water)
    with pytest.raises(ValueError, match="cover"):
        function(nm, rrs, bands=bands,
                 pure_water=(np.array([420.0, 700.0]),
                             np.array([0.01, 0.6]),
                             np.array([0.004, 0.0003])))
    with pytest.raises(ValueError):
        function(nm, rrs[:-1], bands=bands, pure_water=water)
    with pytest.raises(ValueError):
        function(nm, np.where(np.arange(len(nm)) == 0, -0.001, rrs),
                 bands=bands, pure_water=water)


def test_2006_needs_pure_water_at_640_nm():
    rrs = np.full(len(R5_NM), 0.003)
    short = (np.array([400.0, 630.0, 680.0]), np.array([0.01, 0.3, 0.46]),
             np.array([0.004, 0.0005, 0.0003]))
    jerlov.qaa_ioccg2006(R5_NM, rrs, bands=R5_BANDS, pure_water=short)
    with pytest.raises(ValueError):
        jerlov.qaa_ioccg2006(
            [410.0, 440.0, 490.0, 510.0, 555.0, 620.0], rrs,
            bands={**R5_BANDS, "670": 620},
            pure_water=(np.array([400.0, 630.0]), np.array([0.01, 0.3]),
                        np.array([0.004, 0.0005])))


def test_nan_in_one_spectrum_stays_in_that_spectrum(spreadsheet):
    rrs = np.stack([_column(spreadsheet, f"Rrs_{w:g}") for w in V6_NM], -1)
    rrs[3, 1] = np.nan
    q = jerlov.qaa_v6(V6_NM, rrs, bands=V6_BANDS, pure_water=V6_WATER)
    assert np.all(np.isnan(q.a[3]))
    assert np.all(np.isfinite(np.delete(q.a, 3, axis=0)))


def test_one_spectrum_gives_one_dimensional_results(spreadsheet, v6):
    rrs = np.array([float(spreadsheet[5][f"Rrs_{w:g}"]) for w in V6_NM])
    q = jerlov.qaa_v6(V6_NM, rrs, bands=V6_BANDS, pure_water=V6_WATER)
    assert q.a.shape == (6,) and q.eta.shape == ()
    np.testing.assert_allclose(q.a, v6.a[5], rtol=1e-14)


def test_no_defaults():
    with pytest.raises(TypeError):
        jerlov.qaa_v6(V6_NM, np.full(6, 0.003))  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        jerlov.qaa_ioccg2006(R5_NM, np.full(6, 0.003),  # type: ignore
                             bands=R5_BANDS)


# -- DATA.md section 28 ----------------------------------------------------

DATA_MD_TABLE = {"a(410)": (0.060, 0.016), "a(440)": (0.059, 0.015),
                 "a(490)": (0.062, -0.007), "bbp(440)": (0.081, 0.007),
                 "bbp(555)": (0.079, -0.030)}


def _cases(synthetic):
    rows, pw, q = synthetic
    bbw = {w: np.interp(w, pw[0], pw[2]) for w in (440, 550, 560)}
    return {
        "a(410)": (q.a[:, 0], _column(rows, "a_410"), (0.971, -0.001)),
        "a(440)": (q.a[:, 1], _column(rows, "a_440"), (0.971, -0.004)),
        "a(490)": (q.a[:, 2], _column(rows, "a_490"), (0.959, -0.041)),
        "bbp(440)": (q.bbp[:, 1], _column(rows, "bb_440") - bbw[440],
                     (0.945, -0.099)),
        "bbp(555)": (q.bbp[:, 4],
                     0.5 * (_column(rows, "bb_550") + _column(rows, "bb_560"))
                     - 0.5 * (bbw[550] + bbw[560]), (0.983, -0.063)),
    }


def test_DATA_md_section_28_rmse_and_bias(synthetic):
    for name, (model, true, _) in _cases(synthetic).items():
        rmse, bias = _log_stats(model, true)
        assert (round(rmse, 3), round(bias, 3)) == DATA_MD_TABLE[name], name


def test_DATA_md_section_28_regressions(synthetic):
    """Geometric mean within 0.004 of Table 10.1's slope and intercept for
    all five rows; least squares within 0.003 for a, up to 0.015 off for
    bbp."""
    gm_worst, ols_a, ols_bbp = 0.0, 0.0, 0.0
    for name, (model, true, (slope, intercept)) in _cases(synthetic).items():
        x, y = np.log10(true), np.log10(model)
        sxy = np.cov(x, y)[0, 1]
        for kind, s in (("gm", np.sign(sxy) * y.std(ddof=1) / x.std(ddof=1)),
                        ("ols", sxy / x.var(ddof=1))):
            i = y.mean() - s * x.mean()
            off = max(abs(round(s, 3) - slope), abs(round(i, 3) - intercept))
            if kind == "gm":
                gm_worst = max(gm_worst, off)
            elif name.startswith("a"):
                ols_a = max(ols_a, off)
            else:
                ols_bbp = max(ols_bbp, off)
    assert round(gm_worst, 3) == 0.004
    assert round(ols_a, 3) == 0.003
    assert round(ols_bbp, 3) == 0.015


def test_DATA_md_section_28_valid_decompositions(synthetic):
    _, _, q = synthetic
    valid = (q.adg[:, 1] > 0) & (q.aph[:, 1] > 0) & (q.aph[:, 2] > 0)
    assert int(valid.sum()) == 475

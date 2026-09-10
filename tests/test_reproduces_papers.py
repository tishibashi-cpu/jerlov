"""Each shipped table must be reproducible from its own paper's equations.

These are not tests of the physics. They test that the numbers in this package
are the numbers in the papers, and that nothing was mistyped on the way in.
"""

from __future__ import annotations

import warnings

import numpy as np
import pytest

import jerlov
from jerlov import _data
from jerlov.sources import HALTRIN1999, SOLONENKO2015_SCATTERING

WL17 = [300, 310, 350, 375, 400, 425, 450, 475, 500,
        525, 550, 575, 600, 625, 650, 675, 700]

# Solonenko & Mobley (2015) Table 3: (Chl, Cl, Cs, eta, M, alpha).
# Cl and Cs are printed as Bl and Bs in that paper; see sources.py.
SM_TABLE3 = {
    "I": (0.010, 2e-4, 8e-5, 0.93), "IA": (0.027, 0.005, 0.002, 0.44),
    "IB": (0.037, 0.083, 0.03, 0.06), "II": (0.044, 0.011, 0.401, 0.007),
    "III": (0.177, 0.006, 1.1, 0.003), "1C": (1.00, 0.004, 0.402, 0.005),
    "3C": (1.28, 0.005, 1.21, 0.003), "5C": (3.95, 0.022, 1.50, 0.001),
    "7C": (8.4, 0.067, 2.64, 0.0005), "9C": (9.1, 0.016, 3.54, 0.0005),
}
OCEANIC = {"I", "IA", "IB", "II", "III"}

# Williamson & Hollins (2022) Table 6: (Cs, Cl).
WH_TABLE6 = {
    "IB": (0.010, 0.37), "II": (0.022, 0.52), "III": (0.00, 0.90),
    "1C": (0.02, 1.32), "3C": (0.00, 2.07), "5C": (0.00, 3.8),
}


def scattering(constants, wl, cs, cl):
    """Two-component scattering model, Haltrin (1999) Eqs. (5)-(7)."""
    wl = np.asarray(wl, dtype=float)
    k = constants
    return (
        k.bw_coeff * (400 / wl) ** k.bw_exponent
        + cs * k.small_coeff * (400 / wl) ** k.small_exponent
        + cl * k.large_coeff * (400 / wl) ** k.large_exponent
    )


def series(filename, water_type, quantity):
    wl, values, statuses = _data.spectrum(
        filename, water_type, quantity, "value_per_m"
    )
    return wl, values, statuses


# -- Solonenko & Mobley (2015) ------------------------------------------


@pytest.mark.parametrize("water_type", sorted(SM_TABLE3))
def test_solonenko_kd_follows_from_its_own_a_and_b(water_type):
    """Eq. (3) applied to the shipped a and b must give the shipped Kd."""
    _, a, _ = series("solonenko2015_iop.csv", water_type, "a")
    _, b, _ = series("solonenko2015_iop.csv", water_type, "b")
    _, kd, _ = series("solonenko2015_iop.csv", water_type, "Kd")

    _, _, _, eta = SM_TABLE3[water_type]
    mu = 0.98 if water_type in OCEANIC else 0.85
    g = (0.451 + 2.584 * eta) * mu - (0.205 + 0.521 * eta)
    predicted = (a / mu) * np.sqrt(1 + (b / a) * g)

    ok = ~np.isnan(predicted) & ~np.isnan(kd)
    assert ok.sum() >= 12
    error = 100 * (predicted[ok] - kd[ok]) / kd[ok]
    assert np.max(np.abs(error)) < 8.0


@pytest.mark.parametrize(
    "water_type", ["IB", "II", "III", "1C", "3C", "5C", "7C", "9C"]
)
def test_solonenko_b_follows_from_its_own_table3(water_type):
    """Eq. (8) with the paper's own constants must give the shipped b.

    Jerlov I and IA are excluded: their Table 3 entries are not consistent
    with their b column. See README section 4.
    """
    wl, b, statuses = series("solonenko2015_iop.csv", water_type, "b")
    _, cl, cs, _ = SM_TABLE3[water_type]
    predicted = scattering(SOLONENKO2015_SCATTERING, wl, cs, cl)

    # Rows we reconstructed were computed with this very equation, so
    # including them would test nothing.
    published = np.array([s == "ok" for s in statuses]) & ~np.isnan(b)
    error = 100 * (predicted[published] - b[published]) / b[published]
    assert np.max(np.abs(error)) < 3.0


@pytest.mark.parametrize("water_type", ["I", "IA"])
def test_solonenko_table3_is_inconsistent_for_the_clearest_types(water_type):
    """Guard the known defect of README section 4, so a fix is noticed."""
    wl, b, _ = series("solonenko2015_iop.csv", water_type, "b")
    _, cl, cs, _ = SM_TABLE3[water_type]
    predicted = scattering(SOLONENKO2015_SCATTERING, wl, cs, cl)
    error = 100 * (predicted - b) / b
    assert np.max(np.abs(error)) > 5.0


def test_solonenko_reconstruction_used_its_own_constant():
    """The reconstructed 5C values must match Eq. (8) with 1.513, not 1.1513."""
    wl, b, statuses = series("solonenko2015_iop.csv", "5C", "b")
    _, cl, cs, _ = SM_TABLE3["5C"]
    fixed = np.array([s == "reconstructed" for s in statuses])
    assert fixed.sum() == 5

    own = scattering(SOLONENKO2015_SCATTERING, wl[fixed], cs, cl)
    haltrin = scattering(HALTRIN1999, wl[fixed], cs, cl)
    assert np.allclose(b[fixed], own, rtol=1e-3)
    assert not np.allclose(b[fixed], haltrin, rtol=0.05)


def test_corrupted_rows_have_no_absorption_value():
    """a could not be recovered for the duplicated rows; it must stay absent."""
    for water_type, bad in (("3C", [675, 700]), ("5C", [600, 625, 650, 675, 700])):
        wl, a, statuses = series("solonenko2015_iop.csv", water_type, "a")
        for nm in bad:
            i = int(np.where(wl == nm)[0][0])
            assert statuses[i] == "missing"
            assert np.isnan(a[i])


# -- Williamson & Hollins (2022) ----------------------------------------


@pytest.mark.parametrize("water_type", sorted(WH_TABLE6))
def test_williamson_b_follows_from_haltrin_constants(water_type):
    wl, b, _ = series("williamson2022_iop.csv", water_type, "b")
    cs, cl = WH_TABLE6[water_type]
    predicted = scattering(HALTRIN1999, wl, cs, cl)
    error = 100 * (predicted - b) / b
    assert np.max(np.abs(error)) < 6.0


def test_williamson_matches_published_table7():
    """Spot check against Table 7 as printed, at the paper's own wavelengths."""
    published = {
        ("a", 300): [0.149, 0.219, 0.349, 0.566, 0.572, 1.91],
        ("a", 500): [0.0398, 0.0529, 0.0835, 0.104, 0.144, 0.199],
        ("a", 700): [0.573, 0.575, 0.581, 0.585, 0.598, 0.614],
        ("b", 300): [0.178, 0.258, 0.374, 0.531, 0.791, 1.45],
        ("b", 500): [0.128, 0.185, 0.297, 0.44, 0.664, 1.23],
        ("b", 700): [0.111, 0.159, 0.264, 0.396, 0.599, 1.11],
    }
    types = ["IB", "II", "III", "1C", "3C", "5C"]
    for (quantity, nm), expected in published.items():
        for water_type, value in zip(types, expected):
            wl, arr, _ = series("williamson2022_iop.csv", water_type, quantity)
            i = int(np.where(wl == nm)[0][0])
            assert arr[i] == pytest.approx(value, rel=0.005), (
                f"{quantity} {water_type} {nm} nm"
            )


def test_measured_points_match_the_papers_own_filter():
    """The paper kept averages built from five or more measurements: 53 each."""
    rows = _data._rows("williamson2022_measured.csv")
    kept = [r for r in rows if r["status"] == "included"]
    for quantity in ("a", "b"):
        assert sum(1 for r in kept if r["quantity"] == quantity) == 53
    # IA and 7C rest on a single campaign and are excluded throughout.
    for water_type in ("IA", "7C"):
        assert all(
            r["status"] == "excluded_sparse"
            for r in rows if r["water_type"] == water_type
        )


# -- Austin & Petzold (1986) --------------------------------------------


def test_austin_table6_follows_from_its_own_model():
    """Eq. (6) anchored at 475 nm must reproduce the replacement table."""
    wl_m, m, kw = _data.austin_model()
    for water_type in ("I", "IA", "IB", "II", "III", "1C"):
        wl, kd, _ = _data.spectrum(
            "austin1986_kd.csv", water_type, None, "Kd_downwelling_per_m"
        )
        k475 = float(kd[np.where(wl == 475)[0][0]])
        m1 = float(np.interp(475, wl_m, m))
        kw1 = float(np.interp(475, wl_m, kw))
        predicted = (
            np.interp(wl, wl_m, m) / m1 * (k475 - kw1) + np.interp(wl, wl_m, kw)
        )
        error = 100 * (predicted - kd) / kd
        assert np.max(np.abs(error)) < 0.5, water_type


def test_austin_475nm_column_equals_jerlov():
    """Austin & Petzold state that only 475 nm is taken from Jerlov."""
    for water_type in ("IA", "IB", "II", "III", "1C"):
        wl_a, kd_a, _ = _data.spectrum(
            "austin1986_kd.csv", water_type, None, "Kd_downwelling_per_m"
        )
        wl_j, kd_j, _ = _data.spectrum(
            "jerlov1976_kd.csv", water_type, None, "Kd_downwelling_per_m"
        )
        a = float(kd_a[np.where(wl_a == 475)[0][0]])
        j = float(kd_j[np.where(wl_j == 475)[0][0]])
        assert a == pytest.approx(j, rel=1e-3), water_type


def test_jerlov_type_I_falls_below_pure_sea_water():
    """The defect Austin & Petzold (1986) reported, as a standing check."""
    wl_m, _, kw = _data.austin_model()
    wl_j, kd_j, _ = _data.spectrum(
        "jerlov1976_kd.csv", "I", None, "Kd_downwelling_per_m"
    )
    checked = [w for w in range(350, 701, 25)]
    below = 0
    for nm in checked:
        j = float(kd_j[np.where(wl_j == nm)[0][0]])
        if j < float(np.interp(nm, wl_m, kw)):
            below += 1
    assert below == 9, f"{below} of {len(checked)} wavelengths below Kw"


# -- checked against independent transcriptions ---------------------------

#: Jerlov (1976) Table XXVII, Kd x 100 in 1/m, as reprinted by Paglierani et
#: al. (2023) Table 10 and by Wozniak & Pelevin (1991) Table 1. The two agree
#: with each other and with the original scan except at IB 700 nm, where
#: Wozniak & Pelevin print 59; see DATA.md section 16.
JERLOV1976_TABLE_XXVII = {
    "I": [15, 6.2, 3.8, 2.8, 2.2, 1.9, 1.8, 2.7, 4.3, 6.3, 8.9, 23.5, 30.5,
          36, 42, 56],
    "IA": [18, 7.8, 5.2, 3.8, 3.1, 2.6, 2.5, 3.2, 4.8, 6.7, 9.4, 24, 31, 37,
           43, 57],
    "IB": [22, 10, 6.6, 5.1, 4.2, 3.6, 3.3, 4.2, 5.4, 7.2, 9.9, 24.5, 31.5,
           37.5, 43.5, 58],
    "II": [37, 17.5, 12.2, 9.6, 8.1, 6.8, 6.2, 7.0, 7.6, 8.9, 11.5, 26, 33.5,
           40, 46.5, 61],
    "III": [65, 32, 22, 18.5, 16, 13.5, 11.6, 11.5, 11.6, 12.0, 14.8, 29.5,
            37.5, 44.5, 52, 66],
    "1C": [180, 120, 80, 51, 36, 25, 17, 14, 13, 12, 15, 30, 37, 45, 51, 65],
    "3C": [240, 170, 110, 78, 54, 39, 29, 22, 20, 19, 21, 33, 40, 46, 56, 71],
    "5C": [350, 230, 160, 110, 78, 56, 43, 36, 31, 30, 33, 40, 48, 54, 65, 80],
    "7C": [None, 300, 210, 160, 120, 89, 71, 58, 49, 46, 46, 48, 54, 63, 78,
           92],
    "9C": [None, 390, 300, 240, 190, 160, 123, 99, 78, 63, 58, 60, 65, 76, 92,
           110],
}
TABLE_XXVII_WAVELENGTHS = [310, 350, 375, 400, 425, 450, 475, 500, 525, 550,
                           575, 600, 625, 650, 675, 700]


def test_the_shipped_1976_file_matches_the_printed_table():
    """The Dstl file reaches us second-hand; the printed table does not."""
    w = {t: jerlov.water(t, source="jerlov1976")
         for t in JERLOV1976_TABLE_XXVII}
    checked = 0
    for water_type, row in JERLOV1976_TABLE_XXVII.items():
        for nm, printed in zip(TABLE_XXVII_WAVELENGTHS, row):
            if printed is None:
                continue
            got = w[water_type].kd(float(nm))
            assert got == pytest.approx(printed / 100.0, rel=0.005), (
                f"{water_type} at {nm} nm: shipped {got}, printed "
                f"{printed / 100.0}"
            )
            checked += 1
    assert checked == 158


def test_the_wozniak_pelevin_reprint_differs_at_exactly_one_cell():
    """DATA.md section 16. A standing record of what that reprint got wrong."""
    reprint = {k: list(v) for k, v in JERLOV1976_TABLE_XXVII.items()}
    reprint["IB"][TABLE_XXVII_WAVELENGTHS.index(700)] = 59      # as printed
    differing = [
        (t, nm)
        for t, row in reprint.items()
        for nm, value in zip(TABLE_XXVII_WAVELENGTHS, row)
        if value is not None
        and value != JERLOV1976_TABLE_XXVII[t][
            TABLE_XXVII_WAVELENGTHS.index(nm)]
    ]
    assert differing == [("IB", 700)]


def test_the_stated_unit_of_that_reprint_is_impossible():
    """Its header says 1e-3 m^-1, which puts Jerlov I below pure sea water."""
    printed = JERLOV1976_TABLE_XXVII["I"][TABLE_XXVII_WAVELENGTHS.index(475)]
    as_stated = printed * 1e-3
    correct = printed * 1e-2
    pure_water_absorption_at_475 = 0.011    # Austin & Petzold Kw, 1/m
    assert as_stated < pure_water_absorption_at_475
    assert correct > pure_water_absorption_at_475

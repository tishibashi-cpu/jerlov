"""Petzold's measured volume scattering functions, as the report prints them."""

from __future__ import annotations

import csv
import re
from importlib import resources
import warnings
from pathlib import Path

import numpy as np
import pytest

import jerlov
from jerlov import ProvenanceWarning
from jerlov._data import trapezoid

ROOT = Path(__file__).resolve().parent.parent


def _table(station):
    # The installed package's own copy, not the source tree's: the suite is
    # also run against the wheel, where there is no source tree to read.
    path = resources.files("jerlov.data").joinpath("petzold1972_vsf.csv")
    with path.open(encoding="utf-8") as handle:
        return [r for r in csv.DictReader(handle) if r["station"] == station]


def test_every_station_has_the_reports_55_angles():
    for station in jerlov.PETZOLD_STATIONS:
        f = jerlov.petzold_scattering(station)
        assert f.angles_deg.size == 55
        assert f.angles_deg[0] == 0.1 and f.angles_deg[-1] == 180.0
        assert np.all(np.diff(f.angles_deg) > 0)
        assert f.wavelength_nm == 530.0


def test_the_stations_are_listed_clearest_first():
    b = [jerlov.petzold_scattering(s).b for s in jerlov.PETZOLD_STATIONS]
    assert b == sorted(b)


def test_the_phase_function_integrates_to_one_with_what_lies_below_0_1_deg():
    for station in jerlov.PETZOLD_STATIONS:
        f = jerlov.petzold_scattering(station)
        theta = np.radians(f.angles_deg)
        sampled = trapezoid(2 * np.pi * f.phase_function() * np.sin(theta),
                            theta)
        assert sampled + f.fraction_below_0_1_deg == pytest.approx(1.0,
                                                                    abs=0.01)


def test_the_share_below_0_1_deg_is_the_reports_3_to_15_percent():
    shares = [jerlov.petzold_scattering(s).fraction_below_0_1_deg
              for s in jerlov.PETZOLD_STATIONS]
    assert min(shares) == pytest.approx(0.034, abs=0.001)
    assert max(shares) == pytest.approx(0.145, abs=0.001)


def test_the_printed_backscatter_ratio_follows_from_the_table():
    for station in jerlov.PETZOLD_STATIONS:
        f = jerlov.petzold_scattering(station)
        rows = {float(r["angle_deg"]): r for r in _table(station)}
        beyond_90 = 1.0 - float(rows[90.0]["normalized_integral"])
        assert round(beyond_90, 3) == pytest.approx(f.backscatter_ratio,
                                                    abs=0.0011)


def test_the_backscatter_ratio_spans_the_quoted_range():
    """README, DATA.md section 21 and Water.bb all say 0.013 to 0.044."""
    ratios = [jerlov.petzold_scattering(s).backscatter_ratio
              for s in jerlov.PETZOLD_STATIONS]
    assert (min(ratios), max(ratios)) == (0.013, 0.044)


def test_a_is_c_minus_b():
    for station in jerlov.PETZOLD_STATIONS:
        f = jerlov.petzold_scattering(station)
        assert f.a == pytest.approx(f.c - f.b)
        assert f.a > 0


def test_vsf_at_a_printed_angle_is_the_printed_value():
    f = jerlov.petzold_scattering("AUTEC 8")
    assert f.vsf_at(120.0) == 2.3392e-04
    assert isinstance(f.vsf_at(120.0), float)


def test_vsf_between_angles_is_interpolated_in_log_log():
    f = jerlov.petzold_scattering("NUC 2240")
    lo, hi = f.vsf_at(1.0), f.vsf_at(1.2589)
    mid = f.vsf_at(np.sqrt(1.0 * 1.2589))
    assert mid == pytest.approx(np.sqrt(lo * hi), rel=1e-6)


def test_vsf_outside_the_table_is_refused():
    f = jerlov.petzold_scattering("HAOCE 5")
    for angle in (0.05, 180.5):
        with pytest.raises(ValueError, match="does not extrapolate"):
            f.vsf_at(angle)
    with pytest.raises(ValueError, match="NaN"):
        f.vsf_at(float("nan"))


def test_the_reports_own_extension_warns_and_measured_angles_do_not():
    clear, harbor = (jerlov.petzold_scattering(s)
                     for s in ("AUTEC 8", "NUC 2040"))
    with pytest.warns(ProvenanceWarning, match="0.169 degree"):
        clear.vsf_at(0.12)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        clear.vsf_at(0.2)
        harbor.vsf_at(0.12)        # measured at 0.0859 degree there
    assert clear.statuses[:3] == ("extrapolated",) * 3
    assert "extrapolated" not in harbor.statuses


def test_an_unknown_station_names_the_eight():
    with pytest.raises(KeyError, match="AUTEC 8"):
        jerlov.petzold_scattering("AUTEC 10")


def test_the_arrays_cannot_be_changed_underneath_the_package():
    f = jerlov.petzold_scattering("AUTEC 9")
    with pytest.raises(ValueError):
        f.vsf[0] = 1.0
    assert jerlov.petzold_scattering("AUTEC 9").vsf[0] == 7.5181e01


def test_a_measured_ratio_goes_straight_into_water_bb():
    f = jerlov.petzold_scattering("HAOCE 11")
    w = jerlov.water("1C")
    assert w.bb(532, backscatter_ratio=f.backscatter_ratio) == \
        pytest.approx(w.b(532) * 0.013)


@pytest.mark.skipif(not (ROOT / "README.md").exists(),
                    reason="needs the source tree")
def test_the_readme_quotes_a_station_the_package_returns():
    readme = (ROOT / "README.md").read_text()
    match = re.search(r'petzold_scattering\("HAOCE 11"\)\n'
                      r'f\.c, f\.b, f\.backscatter_ratio\s*#\s*([\d.]+), '
                      r'([\d.]+), ([\d.]+)', readme)
    assert match, "the README no longer shows that station with its values"
    f = jerlov.petzold_scattering("HAOCE 11")
    assert (f.c, f.b, f.backscatter_ratio) == tuple(
        float(g) for g in match.groups())

"""Jerlov's measured quanta irradiance, and the package checked against it.

The tables are transcribed in tools/build_jerlov1977.py, which also checks
them against each other. Here: that they are read back as printed, and the
comparison DATA.md section 22 makes between them and what `descend` and
Jerlov's (1976) Kd predict.
"""

from __future__ import annotations

import math
import warnings

import numpy as np
import pytest

import jerlov
from jerlov._data import trapezoid

TYPES = ("I", "IA", "IB", "II", "III", "1C", "3C")
BAND = np.arange(350.0, 701.0, 5.0)          # Jerlov's quanta band
PHOTONS = np.interp(BAND, *jerlov.d65()) * BAND


def _quanta(water_type):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        return jerlov.jerlov1977_quanta(water_type)


def _level_depths(transmittance_at, deepest):
    """Depths of 30, 10, 3 and 1 percent of surface quanta, 350-700 nm."""
    surface = trapezoid(PHOTONS, BAND)

    def fraction(z):
        return trapezoid(PHOTONS * transmittance_at(z), BAND) / surface

    out = []
    for level in (0.30, 0.10, 0.03, 0.01):
        low, high = 0.0, deepest
        if fraction(high) > level:
            out.append(None)
            continue
        for _ in range(60):
            middle = 0.5 * (low + high)
            if fraction(middle) > level:
                low = middle
            else:
                high = middle
        out.append(0.5 * (low + high))
    return out


def _one_kd(water_type):
    kd = jerlov.water(water_type, source="jerlov1976").kd(BAND)
    return _level_depths(lambda z: np.exp(-kd * z), 1000.0)


def _layered(water_type):
    d = jerlov.descend(water_type, jerlov.profile_depth(water_type), BAND)
    return _level_depths(d.transmittance_at, d.depth_m)


# -- the tables as printed ---------------------------------------------------

def test_table_2_is_read_back_as_printed():
    q = _quanta("I")
    assert q.level_percent == (30.0, 10.0, 3.0, 1.0)
    assert q.level_depth_m.tolist() == [19, 49, 79, 103]
    assert _quanta("3C").level_depth_m.tolist() == [3.7, 8.5, 14, 19]
    assert repr(_quanta("II")) == (
        "<QuantaLevels II: 30% 10.5 m, 10% 24 m, 3% 39 m, 1% 52 m; "
        "1 suspect>")


def test_tables_3_and_5_go_as_deep_as_the_paper():
    q = _quanta("I")
    assert q.profile_depth_m[-1] == 100 and q.profile_percent[-1] == 1.14
    assert q.layer_m[-1] == (90.0, 100.0) and q.layer_kd[-1] == 0.048
    q = _quanta("3C")
    assert q.profile_depth_m.tolist() == [0, 2, 5, 10, 15, 20]
    assert len(q.layer_kd) == 5
    for array in (q.level_depth_m, q.profile_percent, q.layer_kd):
        with pytest.raises(ValueError):
            array[0] = 0.0


def test_the_suspect_layers_warn_and_the_others_do_not():
    for water_type, layer in (("IA", "20.0-30.0"), ("II", "5.0-10.0"),
                              ("1C", "10.0-15.0")):
        with pytest.warns(jerlov.ProvenanceWarning, match="Table 5"):
            q = jerlov.jerlov1977_quanta(water_type)
        assert len(q.suspect) == 1 and layer.replace(".0", "") in \
            q.suspect[0].replace(".0", "")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        for water_type in ("I", "IB", "III", "3C"):
            assert jerlov.jerlov1977_quanta(water_type).suspect == ()


def test_an_unknown_type_names_the_known_ones():
    with pytest.raises(KeyError, match="known: I, IA, IB, II, III, 1C, 3C"):
        jerlov.jerlov1977_quanta("5C")


# -- the package against the measurements: DATA.md section 22 ---------------

def test_from_II_to_3C_one_kd_agrees_within_2_m_at_every_level():
    for water_type in ("II", "III", "1C", "3C"):
        model = _one_kd(water_type)
        printed = _quanta(water_type).level_depth_m
        assert max(abs(m - p) for m, p in zip(model, printed)) < 2.0, \
            water_type


def test_jerlov_I_needs_the_depth_profile():
    """One Kd puts the 1 percent level of I at 165 m; Jerlov measured 103;
    layer by layer it is 106."""
    assert round(_one_kd("I")[3]) == 165
    assert round(_layered("I")[3]) == 106
    assert round(_layered("I")[1]) == 49          # 10 percent: 49 printed


def test_IA_and_IB_stay_too_deep():
    """Layer by layer IA reaches 1 percent at 100 m against 87, and IB at
    93 m against 70: 15 and 33 percent too deep."""
    ia, ib = _layered("IA")[3], _layered("IB")[3]
    assert (round(ia), round(ib)) == (100, 93)
    assert round(100 * (ia / 87 - 1)) == 15
    assert round(100 * (ib / 70 - 1)) == 33


def test_IB_agrees_in_its_own_10_m_and_departs_below():
    """Kd for quanta in IB, Jerlov (1976) against Table 5: within 0.004 1/m
    above 10 m; below 15 m one falls from 0.051 to 0.041, the other rises
    from 0.056 to 0.069."""
    kd = jerlov.water("IB", source="jerlov1976").kd(BAND)

    def quanta(z):
        return trapezoid(PHOTONS * np.exp(-kd * z), BAND)

    q = _quanta("IB")
    model = np.array([math.log(quanta(a) / quanta(b)) / (b - a)
                      for a, b in q.layer_m])
    top = [i for i, (a, b) in enumerate(q.layer_m) if b <= 10]
    deep = [i for i, (a, b) in enumerate(q.layer_m) if a >= 15]
    assert np.max(np.abs(model[top] - q.layer_kd[top])) < 0.004
    assert (round(model[deep[0]], 3),
            round(model[deep[-1]], 3)) == (0.051, 0.041)
    assert (q.layer_kd[deep[0]], q.layer_kd[deep[-1]]) == (0.056, 0.069)
    assert np.all(np.diff(model[deep]) < 0)
    assert np.all(np.diff(q.layer_kd[deep]) >= 0)


def test_DATA_md_figures_for_the_tables_against_each_other():
    """The recomputed ranges in DATA.md section 22, and integrating Table 5
    down to 10 m for II gives 29 percent against Table 3's 32."""
    def ratio_range(z, z10):
        r = [(z + a) / (z10 + b) for a in (-0.5, 0.5) for b in (-0.5, 0.5)]
        return f"{min(r):.2f}-{max(r):.2f}"
    assert ratio_range(79, 49) == "1.59-1.64"
    assert ratio_range(103, 49) == "2.07-2.13"
    assert ratio_range(66, 41) == "1.58-1.64"
    q = _quanta("II")
    tau = sum(k * (b - a) for (a, b), k in zip(q.layer_m, q.layer_kd)
              if b <= 10)
    assert round(100 * math.exp(-tau)) == 29
    assert q.profile_percent[q.profile_depth_m.tolist().index(10)] == 32

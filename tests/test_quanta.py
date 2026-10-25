"""Jerlov's measured quanta irradiance, and the package checked against it.

The tables are transcribed in tools/build_jerlov1977.py, which also checks
them against each other. Here: that they are read back as printed, and the
comparison DATA.md section 22 makes between them and what `descend` and
Jerlov's (1976) Kd predict.
"""

from __future__ import annotations

import importlib.util
import math
import pathlib
import statistics
import warnings

import numpy as np
import pytest

import jerlov

ROOT = pathlib.Path(__file__).resolve().parent.parent
source_tree = pytest.mark.skipif(
    not (ROOT / "tools" / "nygard1973_quanta.csv").exists(),
    reason="not running from a source tree",
)

TYPES = ("I", "IA", "IB", "II", "III", "1C", "3C")
BAND = np.arange(350.0, 701.0, 5.0)          # Jerlov's quanta band
SURFACE = np.interp(BAND, *jerlov.d65())


def _quanta(water_type):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        return jerlov.jerlov1977_quanta(water_type)


def _quanta_profile(kd):
    return jerlov.par_profile(SURFACE, BAND, 0.0, kd=kd, unit="energy",
                              band=jerlov.QUANTA_BAND_NM)


def _level_depths(profile):
    """Depths of 30, 10, 3 and 1 percent of surface quanta, 350-700 nm."""
    out = []
    for level in (0.30, 0.10, 0.03, 0.01):
        try:
            out.append(profile.depth_of_fraction(level))
        except jerlov.MissingQuantityError:
            out.append(None)
    return out


def _one_kd(water_type):
    return _level_depths(_quanta_profile(
        jerlov.water(water_type, source="jerlov1976")))


def _layered(water_type):
    return _level_depths(_quanta_profile(jerlov.descend(
        water_type, jerlov.profile_depth(water_type), BAND)))


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
    q = _quanta("IB")
    edges = np.array(q.layer_m)
    quanta = jerlov.par_profile(SURFACE, BAND, edges, unit="energy",
                                kd=jerlov.water("IB", source="jerlov1976"),
                                band=jerlov.QUANTA_BAND_NM).par
    model = np.log(quanta[:, 0] / quanta[:, 1]) / (edges[:, 1] - edges[:, 0])
    top = [i for i, (a, b) in enumerate(q.layer_m) if b <= 10]
    deep = [i for i, (a, b) in enumerate(q.layer_m) if a >= 15]
    assert np.max(np.abs(model[top] - q.layer_kd[top])) < 0.004
    assert (round(model[deep[0]], 3),
            round(model[deep[-1]], 3)) == (0.051, 0.041)
    assert (q.layer_kd[deep[0]], q.layer_kd[deep[-1]]) == (0.056, 0.069)
    assert np.all(np.diff(model[deep]) < 0)
    assert np.all(np.diff(q.layer_kd[deep]) >= 0)


def test_table_2_against_jerlovs_own_equations():
    """DECISIONS.md section 53, Test 1: every oceanic z(30) within 0.2 m of
    0.50 z(10) - 0.0023 z(10)^2, every z(3) within 2.4 percent of
    1.65 z(10); z(1) of I 3.6 percent above 2.18 z(10), the other oceanic
    types within 2.7; the coastal z(30) 0.37 and 0.38 m off."""
    z30_off, z3_off, z1_off = {}, {}, {}
    for t in TYPES:
        z30, z10, z3, z1 = _quanta(t).level_depth_m
        z30_off[t] = abs(z30 - (0.50 * z10 - 0.0023 * z10 ** 2))
        z3_off[t] = abs(z3 / (1.65 * z10) - 1)
        z1_off[t] = abs(z1 / (2.18 * z10) - 1)
    oceanic = ("I", "IA", "IB", "II", "III")
    assert max(z30_off[t] for t in oceanic) < 0.2
    assert round(100 * max(z3_off[t] for t in oceanic), 1) == 2.4
    assert round(100 * z1_off["I"], 1) == 3.6
    assert round(100 * max(z1_off[t] for t in oceanic if t != "I"), 1) \
        == 2.7
    assert (round(z30_off["1C"], 2), round(z30_off["3C"], 2)) == (0.37, 0.38)


def test_IB_is_too_deep_from_the_10_percent_level_down():
    """Section 53, Test 2: IB's 10 percent level is 37.4 m against 33; the
    excess is 4.4, 11.6 and 23.0 m at 10, 3 and 1 percent; z(1) / z(10) is
    2.49 against 2.12."""
    _, z10, z3, z1 = _layered("IB")
    _, p10, p3, p1 = _quanta("IB").level_depth_m
    assert round(z10, 1) == 37.4
    assert [round(m - p, 1) for m, p in ((z10, p10), (z3, p3), (z1, p1))] \
        == [4.4, 11.6, 23.0]
    assert (round(z1 / z10, 2), round(p1 / p10, 2)) == (2.49, 2.12)


def test_neither_the_sky_nor_the_meter_explains_IB():
    """Section 53, Test 3: tilting D65 by (wavelength / 550)^n, n from -2 to
    2, puts IB's 1 percent level between 98.9 and 84.7 m; at n = +1, the
    only tilt keeping z(10) within 2 m of 33 (34.2 m), it is 89.2 m. The
    same tilt as the meter's response gives the same levels."""
    descent = jerlov.descend("IB", jerlov.profile_depth("IB"), BAND)

    def levels(surface, weight=None):
        return _level_depths(jerlov.par_profile(
            surface, BAND, 0.0, kd=descent, unit="energy",
            band=jerlov.QUANTA_BAND_NM, photon_weight=weight))

    sky, meter = {}, {}
    for n in (-2, -1, 0, 1, 2):
        tilt = (BAND / 550.0) ** n
        sky[n] = levels(SURFACE * tilt)
        meter[n] = levels(SURFACE, tilt)
        np.testing.assert_allclose(meter[n], sky[n], rtol=1e-9)
    assert (round(sky[-2][3], 1), round(sky[2][3], 1)) == (98.9, 84.7)
    within = [n for n in sky if abs(sky[n][1] - 33) <= 2]
    assert within == [1]
    assert (round(sky[1][1], 1), round(sky[1][3], 1)) == (34.2, 89.2)
    assert all(abs(z[3] - 70) > 3 for z in sky.values())


def test_no_spectral_kd_for_IB_reaches_jerlovs_70_m():
    """DECISIONS.md section 54: with Austin & Petzold's Kd IB's levels are
    14.7, 38.5, 67.7 and 95.8 m; II's 1 percent level 54.6 m and III's
    33.2 m; IA 102.9 and I 109.2 m. Solonenko & Mobley put IB at 98.5 m
    (kd) and 104.1 m (kd_hydrolight), Jerlov (1968) at 98.4 m. Every set
    gives 93 to 104 m."""
    def layered(water_type, source):
        return _level_depths(_quanta_profile(jerlov.descend(
            water_type, jerlov.profile_depth(water_type), BAND,
            source=source)))

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        austin = {t: layered(t, "austin1986")
                  for t in ("I", "IA", "IB", "II", "III")}
        fitted = layered("IB", "solonenko2015")
        hydrolight = _level_depths(_quanta_profile(
            jerlov.water("IB", source="solonenko2015").kd_hydrolight(BAND)))
    assert [round(z, 1) for z in austin["IB"]] == [14.7, 38.5, 67.7, 95.8]
    assert (round(austin["II"][3], 1), round(austin["III"][3], 1)) \
        == (54.6, 33.2)
    assert (round(austin["IA"][3], 1), round(austin["I"][3], 1)) \
        == (102.9, 109.2)
    assert (round(fitted[3], 1), round(hydrolight[3], 1)) == (98.5, 104.1)
    assert set(jerlov.water_type_at_depth(
        "IB", np.arange(0.0, 200.0, 10.0))) == {"IB"}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        jerlov1968 = layered("IB", "jerlov1968")[3]
    every = [_layered("IB")[3], jerlov1968, austin["IB"][3], fitted[3],
             hydrolight[3]]
    assert round(jerlov1968, 1) == 98.4
    assert (round(min(every)), round(max(every))) == (93, 104)


def _tool(name):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _nygard():
    return _tool("nygard1973_levels")


@source_tree
def test_nygards_ib_like_profiles_follow_table_2_not_the_package():
    """DECISIONS.md section 55: 48 lowerings at 19 stations, 37 reaching
    both levels and 10 turning back before 1 percent at 68 to 89 m; five
    IB-like, z(1) / z(10) 2.51, 1.89, 2.01, 1.73 and 1.95, median 1.95, at
    stations 3, 12, 12, 15 and 15; 1.99 with the monitor; 1.59 to 2.51,
    median 2.05, over all 37."""
    nygard = _nygard()
    found = nygard.lowerings(nygard.read())
    assert len(found) == 48
    assert len({lowering[0]["station"] for lowering in found}) == 19
    plain = [nygard.levels(lowering) for lowering in found]
    both = [(lv[0.10], lv[0.01]) for lv in plain
            if lv[0.10] is not None and lv[0.01] is not None]
    assert len(both) == 37
    short = [max(r["depth"] for r in lowering)
             for lowering, lv in zip(found, plain)
             if lv[0.10] is not None and lv[0.01] is None]
    assert (len(short), round(min(short)), round(max(short))) == (10, 68, 89)
    ib = [(lowering[0]["station"], lv[0.01] / lv[0.10])
          for lowering, lv in zip(found, plain)
          if nygard.ib_like(lv[0.10]) and lv[0.01] is not None]
    assert [s for s, _ in ib] == [3, 12, 12, 15, 15]
    assert [round(r, 2) for _, r in ib] == [2.51, 1.89, 2.01, 1.73, 1.95]
    median = statistics.median(r for _, r in ib)
    assert round(median, 2) == 1.95
    assert abs(median - 2.12) < abs(median - 2.49)
    assert (round(abs(median - 2.12), 2), round(abs(median - 2.49), 2)) \
        == (0.17, 0.54)
    scaled = [nygard.levels(lowering, monitor=True) for lowering in found]
    with_monitor = [lv[0.01] / lv[0.10] for lv in scaled
                    if lv and nygard.ib_like(lv[0.10]) and lv[0.01]]
    assert (len(with_monitor), round(statistics.median(with_monitor), 2)) \
        == (5, 1.99)
    ratios = [z1 / z10 for z10, z1 in both]
    assert (round(min(ratios), 2), round(max(ratios), 2),
            round(statistics.median(ratios), 2)) == (1.59, 2.51, 2.05)


@source_tree
def test_nygards_slips_and_false_starts_do_not_change_the_test():
    """Section 55: 146 for the 46 at 43.0 m moves its lowering's 10 percent
    level from 40.3 to 47.1 m; counting the four false starts adds two
    IB-like lowerings and leaves the median at 1.95."""
    nygard = _nygard()
    rows = nygard.read()

    def ib_median(rows):
        ratios = []
        for lowering in nygard.lowerings(rows):
            lv = nygard.levels(lowering)
            if nygard.ib_like(lv[0.10]) and lv[0.01] is not None:
                ratios.append(lv[0.01] / lv[0.10])
        return len(ratios), round(statistics.median(ratios), 2)

    def z10_of_station_17_from(page, rows):
        for lowering in nygard.lowerings(rows):
            if lowering[0]["station"] == 17 and lowering[0]["page"] == page:
                return round(nygard.levels(lowering)[0.10], 1)

    assert z10_of_station_17_from("I-66", rows) == 40.3
    mended = [dict(r, q=146.0) if (r["page"], r["depth"], r["q"])
              == ("I-66", 43.0, 46.0) else r for r in rows]
    assert z10_of_station_17_from("I-66", mended) == 47.1
    assert ib_median(mended) == (5, 1.95)
    every_start = [dict(r, not_a_start=False) for r in rows]
    assert sum(r["not_a_start"] for r in rows) == 4
    assert ib_median(every_start) == (7, 1.95)


@source_tree
def test_smiths_blue_kd_rises_with_depth_at_two_of_three_stations():
    """DECISIONS.md section 56: deepest over shallowest blue Kd 1.63, 1.56
    and 1.03 at stations 3, 12 and 15 (1.29 at station 3 on 479 and 498 nm
    only); 0.025 and 0.041 1/m at station 3, 0.046 and 0.072 at 12, 0.064
    and 0.066 at 15, with 0.109 and 0.083 between; against Jerlov's IB,
    0.037-0.038 1/m, 0.68-1.11, 0.98-1.89 and 1.16-2.87, every deepest
    layer above."""
    smith = _tool("smith1973_blue")
    spectra = smith.read()
    found = {s: smith.layers(depths) for s, depths in spectra.items()}
    ratio = {s: layers[-1][3] / layers[0][3] for s, layers in found.items()}
    assert {s: round(r, 2) for s, r in ratio.items()} \
        == {3: 1.63, 12: 1.56, 15: 1.03}
    assert sum(r > smith.RISES for r in ratio.values()) == 2
    two = smith.layers(spectra[3], wavelengths=(479, 498))
    assert round(two[-1][3] / two[0][3], 2) == 1.29
    ends = {s: (round(layers[0][3], 3), round(layers[-1][3], 3))
            for s, layers in found.items()}
    assert ends == {3: (0.025, 0.041), 12: (0.046, 0.072),
                    15: (0.064, 0.066)}
    assert [round(layer[3], 3) for layer in found[15][2:4]] == [0.109, 0.083]
    ib = jerlov.water("IB", source="jerlov1976")
    spans = {}
    for s, layers in found.items():
        reference = [float(np.mean(ib.kd(np.array(layer[2], dtype=float))))
                     for layer in layers]
        assert all(round(r, 3) in (0.037, 0.038) for r in reference)
        relative = [layer[3] / r for layer, r in zip(layers, reference)]
        spans[s] = (round(min(relative), 2), round(max(relative), 2))
        assert relative[-1] > 1
    assert spans == {3: (0.68, 1.11), 12: (0.98, 1.89), 15: (1.16, 2.87)}


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

"""The numbers the prose quotes must still be the numbers the code gives.

README.md, DATA.md and the examples all state figures: a factor of 3.8 here, 46
percent there. Those were computed once. Nothing has been stopping them from
drifting away from what the package now returns, and a reader has no way to
tell when they have.

Each test below recomputes one quoted figure. When one fails, the prose is
what needs fixing, not the test — unless the change to the code was a mistake,
in which case it is the other way round and the test has done its job.
"""

from __future__ import annotations

import math
import pathlib
import re
import warnings

import numpy as np
import pytest

import jerlov

ROOT = pathlib.Path(__file__).resolve().parent.parent
source_tree = pytest.mark.skipif(
    not (ROOT / "README.md").exists(),
    reason="not running from a source tree",
)


def quiet():
    return warnings.catch_warnings()


# -- the sources disagree, and by how much --------------------------------


def test_scattering_at_510nm_differs_by_the_stated_factor():
    """sources_disagree.py says 3.8 for Jerlov III."""
    with quiet():
        warnings.simplefilter("ignore")
        measured = float(jerlov.water("III").b(510))
        inverted = float(jerlov.water("III", source="solonenko2015").b(510))
    assert inverted / measured == pytest.approx(3.8, abs=0.05)


@source_tree
def test_the_readme_states_the_largest_disagreement_at_510nm():
    """The README said "up to a factor of 2.6" while this test's docstring
    claimed it said 3.8; nothing read the README, so nothing noticed."""
    from jerlov.sources import SOURCES

    readme = (ROOT / "README.md").read_text()
    match = re.search(r"differ by up to a factor of ([\d.]+), at Jerlov (\w+)",
                      readme)
    assert match, "the README no longer states the factor at 510 nm"
    common = set(SOURCES["williamson2022"].water_types) & set(
        SOURCES["solonenko2015"].water_types)
    with quiet():
        warnings.simplefilter("ignore")
        factors = {}
        for t in common:
            one = float(jerlov.water(t).b(510))
            other = float(jerlov.water(t, source="solonenko2015").b(510))
            factors[t] = max(one, other) / min(one, other)
    worst = max(factors, key=factors.get)
    assert worst == match.group(2)
    assert factors[worst] == pytest.approx(float(match.group(1)), abs=0.05)


def test_the_disagreement_does_not_run_one_way():
    """sources_disagree.py claims Jerlov IB goes the other direction."""
    with quiet():
        warnings.simplefilter("ignore")
        measured = float(jerlov.water("IB").b(510))
        inverted = float(jerlov.water("IB", source="solonenko2015").b(510))
    assert inverted / measured < 0.5


def test_the_three_routes_span_the_stated_factor_at_532nm():
    """DATA.md section 17 says 5.1 for Jerlov III."""
    chlorophyll_model = 1.8998          # Abd El-Mottaleb et al. (2024)
    with quiet():
        warnings.simplefilter("ignore")
        measured = float(jerlov.water("III").c(532))
        inverted = float(jerlov.water("III", source="solonenko2015").c(532))
    assert measured == pytest.approx(0.371, abs=0.001)
    assert inverted == pytest.approx(1.092, abs=0.001)
    assert chlorophyll_model / measured == pytest.approx(5.1, abs=0.05)


# -- the scattering model constants ---------------------------------------


def test_the_small_particle_coefficients_differ_by_the_stated_amount():
    """DATA.md section 6: 1.513 is 31 percent larger than 1.151302."""
    from jerlov.sources import HALTRIN1999

    haltrin = HALTRIN1999.small_coeff
    solonenko = jerlov.get_source("solonenko2015").scattering.small_coeff
    assert haltrin == pytest.approx(1.151302)
    assert solonenko == pytest.approx(1.513)
    assert solonenko / haltrin - 1 == pytest.approx(0.31, abs=0.005)


# -- shortwave penetration ------------------------------------------------


def test_the_shortwave_fit_misses_its_source_by_the_stated_amount():
    """README, DATA.md section 14 and solar_heating.py all say 46 percent."""
    worst = 0.0
    for water_type in ("I", "IA", "IB", "II", "III"):
        depths, measured = jerlov.jerlov1968_solar_fraction(water_type)
        for depth, want in zip(depths, measured):
            if depth == 0 or depth > 100 or np.isnan(want):
                continue
            got = jerlov.solar_fraction(water_type, depth)
            worst = max(worst, abs(got - want) / want)
    assert worst == pytest.approx(0.46, abs=0.01)


def test_the_published_R_values_are_what_the_docs_print():
    published = {"I": 0.58, "IA": 0.62, "IB": 0.67, "II": 0.77, "III": 0.78}
    for water_type, value in published.items():
        assert jerlov.shortwave_parameters(water_type).R == pytest.approx(value)


# -- backscattering -------------------------------------------------------


def test_the_worst_chi_p_spread_is_the_stated_figure():
    """README and DATA.md section 18 both say 34.8 percent at 170 degrees."""
    with pytest.warns(jerlov.AngleWarning, match="34.8"):
        result = jerlov.bb_from_vsf(0.002, 170.0, 532.0)
    assert result.quoted_error_percent == pytest.approx(34.8)
    # The other tabulated angles. This once said "3-6" and checked only the
    # upper end, which let the 2.6 at 100 degrees through.
    others = [jerlov.bb_from_vsf(0.002, a, 532.0).quoted_error_percent
              for a in np.arange(90.0, 161.0, 10.0)]
    assert min(others) == pytest.approx(2.6)
    assert max(others) == pytest.approx(6.4)


def test_chi_w_and_chi_p_cross_where_the_docs_say():
    """DATA.md section 18 quotes 116.9 degrees against the paper's ~118."""
    r = (1 - jerlov.backscattering.DEPOLARISATION_RATIO) / (
        1 + jerlov.backscattering.DEPOLARISATION_RATIO)
    angles = np.linspace(90.0, 170.0, 80001)
    gap = [(1 + r / 3) / (1 + r * math.cos(math.radians(a)) ** 2)
           - jerlov.particulate_chi(a) for a in angles]
    crossing = float(angles[int(np.argmin(np.abs(gap)))])
    assert crossing == pytest.approx(116.9, abs=0.1)


# -- the example that argues against defaults -----------------------------


def test_the_guess_overstates_contrast_by_the_stated_amount():
    """from_one_measurement.py computes 65 percent and the prose repeats it.

    The example computes this rather than hard-coding it, so this test is
    what stops the *prose* around it from going stale.
    """
    wl = np.arange(420.0, 681.0, 20.0)
    a = 0.02 + 0.35 * np.exp(-(wl - 420.0) / 90.0) + 0.30 * (wl > 600)
    b = 0.45 * (550.0 / wl) ** 0.8
    water = jerlov.Water.from_measurements(wl, a=a, b=b)

    measured = jerlov.bb_from_vsf(0.0021, 140.0, 532.0, salinity_psu=35.0)
    ratio = measured.bb / water.b(532.0)
    assert ratio == pytest.approx(0.033, abs=0.001)

    surface = np.interp(wl, *jerlov.d65(), left=0.0, right=0.0)
    with quiet():
        warnings.simplefilter("ignore")
        scene = jerlov.Scene.at_depth(
            water, 8.0, surface, wl,
            kd=jerlov.water("II", source="austin1986"))
        white = scene.downwelling / np.pi
        contrasts = {}
        for label, value in (("guess", 0.015), ("measured", ratio)):
            b_inf = jerlov.veiling_radiance_estimate(
                water, scene.downwelling, wl, backscatter_ratio=value)
            observed = scene.observe(np.full_like(wl, 0.5), 5.0,
                                     veiling_radiance=b_inf,
                                     face_irradiance_ratio=1.0)
            contrasts[label] = float(
                np.mean(np.abs(observed.contrast(0.1 * white))))
    overstatement = contrasts["guess"] / contrasts["measured"] - 1
    assert overstatement == pytest.approx(0.65, abs=0.03)


# -- the prose and the code are checked against each other ----------------


@source_tree
def test_the_readme_quotes_a_transmittance_the_package_produces():
    """`solar_fraction("IB", 10.0)` appears in the README with its answer."""
    readme = (ROOT / "README.md").read_text()
    match = re.search(
        r'solar_fraction\("IB", 10\.0\).*?#\s*([\d.]+)', readme)
    assert match, "the README no longer shows that call with its result"
    assert jerlov.solar_fraction("IB", 10.0) == pytest.approx(
        float(match.group(1)), abs=0.0005)


@source_tree
def test_the_readme_quotes_a_chi_p_the_package_produces():
    readme = (ROOT / "README.md").read_text()
    match = re.search(r"r\.chi_p, r\.quoted_error_percent\s*#\s*([\d.]+),\s*([\d.]+)",
                      readme)
    assert match, "the README no longer shows chi_p with its value"
    result = jerlov.bb_from_vsf(0.0021, 140.0, 532.0)
    assert result.chi_p == pytest.approx(float(match.group(1)))
    assert result.quoted_error_percent == pytest.approx(float(match.group(2)))


def test_the_two_editions_differ_by_the_stated_amounts():
    """The jerlov1968 caveat says 1 to 15 percent on average, and up to 35
    at single wavelengths, against Jerlov (1976)."""
    from jerlov.sources import ALL_TYPES

    means, worst = [], 0.0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for t in ALL_TYPES:
            old = jerlov.water(t, source="jerlov1968")
            new = jerlov.water(t, source="jerlov1976")
            x, y = old.kd(old.wavelengths), new.kd(old.wavelengths)
            ok = np.isfinite(x) & np.isfinite(y)
            rel = np.abs(x[ok] - y[ok]) / y[ok]
            means.append(rel.mean())
            worst = max(worst, rel.max())
    assert 0.01 <= min(means) < 0.02
    assert 0.14 < max(means) <= 0.15
    assert 0.34 < worst <= 0.35


def test_kd_hydrolight_agrees_with_jerlov_as_data_md_says():
    """DATA.md section 19: 86.5 percent of all cells within 20 percent of
    K_d^0, 87.9 percent of unflagged ones, against the paper's 90."""
    from jerlov import _data
    from jerlov.sources import ALL_TYPES

    every, sound = [], []
    for t in ALL_TYPES:
        _, k0, s0 = _data.spectrum("solonenko2015_iop.csv", t, "Kd0",
                                   "value_per_m")
        _, kh, sh = _data.spectrum("solonenko2015_iop.csv", t, "KdH",
                                   "value_per_m")
        for x, y, a, b in zip(k0, kh, s0, sh):
            if np.isfinite(x) and np.isfinite(y):
                within = abs(x - y) / x <= 0.20
                every.append(within)
                if a not in _data.QUESTIONABLE and b not in _data.QUESTIONABLE:
                    sound.append(within)
    assert len(every) == 163 and len(sound) == 141
    assert np.mean(every) == pytest.approx(0.865, abs=0.001)
    assert np.mean(sound) == pytest.approx(0.879, abs=0.001)


@source_tree
def test_the_readme_quotes_a_pure_water_absorption_the_package_produces():
    readme = (ROOT / "README.md").read_text()
    match = re.search(r"pure_water_absorption\(440\)\s*#\s*([\d.]+)", readme)
    assert match, "the README no longer shows that call with its result"
    assert jerlov.pure_water_absorption(440) == pytest.approx(
        float(match.group(1)))


@source_tree
def test_the_readme_shows_the_layers_descend_crosses():
    readme = (ROOT / "README.md").read_text()
    match = re.search(r"d\.layers\s*#\s*\((.*)\)\n", readme)
    assert match, "the README no longer shows the layers of a descent"
    shown = re.findall(r"\((\d+), (\d+), '(\w+)'\)", match.group(1))
    layers = jerlov.descend("1C", 45.0, 500.0).layers
    assert [(float(a), float(b), t) for a, b, t in shown] == \
        [layers[0], layers[1], layers[2], layers[-1]]


def test_DATA_md_section_13_states_where_the_coastal_profiles_end():
    """DATA.md section 13 says 3C reaches only 70 m; the descend docstring
    adds 9C below 10 m and 5C and 7C below 20 m."""
    jerlov.descend("3C", 70.0, 500.0)
    jerlov.descend("9C", 10.0, 500.0)
    for t, depth in (("3C", 70.5), ("9C", 10.5), ("5C", 20.5), ("7C", 20.5)):
        with pytest.raises(jerlov.MissingQuantityError):
            jerlov.descend(t, depth, 500.0)


def test_DATA_md_section_20_on_the_measurements_at_715_nm():
    """1.004 with no spread for 1C, 3C, 5C; 1.018 for III; 14 to 16 percent
    above the fit, which is aw there."""
    import numpy as np

    excess = []
    for t in ("III", "1C", "3C", "5C"):
        m = jerlov.measured_points(t, "a")
        k = int(np.where(m.wavelengths == 715.0)[0][0])
        if t == "III":
            assert m.values[k] == pytest.approx(1.018, abs=0.0005)
        else:
            assert m.values[k] == 1.004
            assert m.std_dev[k] < 1e-12
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
            fitted = jerlov.water(t).a(715.0)
        assert fitted == pytest.approx(jerlov.pure_water_absorption(715.0),
                                       rel=0.01)
        excess.append(100 * (m.values[k] / fitted - 1))
    assert 13.5 < min(excess) and max(excess) < 16.0


def test_examples_README_figures_for_the_depth_profile():
    """3C receives 530 times more light at 60 m, I a third less; the 1
    percent level of I rises from 197 to 133 m (all at 490 nm)."""
    import math

    def one_kd(t, z):
        return math.exp(-jerlov.water(t, source="jerlov1976").kd(490.0) * z)

    ratio_3c = jerlov.descend("3C", 60.0, 490.0).transmittance / one_kd("3C", 60.0)
    ratio_i = jerlov.descend("I", 60.0, 490.0).transmittance / one_kd("I", 60.0)
    assert round(ratio_3c, -1) == 530
    assert ratio_i == pytest.approx(2 / 3, abs=0.02)

    def depth_of_one_percent(t, layered):
        for z in [k / 2 for k in range(1, 401)]:
            t_z = (jerlov.descend(t, z, 490.0).transmittance if layered
                   else one_kd(t, z))
            if t_z <= 0.01:
                return z

    assert depth_of_one_percent("I", False) == 197.0
    assert depth_of_one_percent("I", True) == 133.0


def test_examples_README_figures_for_absorption_by_the_contents():
    """Twelve times at 412 nm; pure water 78 to 98 percent at 600 nm."""
    aw412, aw600 = (jerlov.pure_water_absorption(nm) for nm in (412, 600))
    ratio = ((jerlov.water("5C").a(412) - aw412)
             / (jerlov.water("IB").a(412) - aw412))
    assert round(ratio) == 12
    shares = [aw600 / jerlov.water(t).a(600)
              for t in jerlov.get_source("williamson2022").water_types]
    assert (round(100 * min(shares)), round(100 * max(shares))) == (78, 98)


def test_examples_README_figure_for_measured_backscatter_ratios():
    """measured_scattering.py: contrast at 5 m from 4.0 to 2.6 at 550 nm
    across the coastal and harbor stations' ratios."""
    import numpy as np

    wl = np.arange(450.0, 651.0, 50.0)
    w = jerlov.water("1C")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        scene = jerlov.Scene.at_depth(
            w, 10.0, np.interp(wl, *jerlov.d65()), wl,
            kd=jerlov.water("1C", source="austin1986"))
    contrasts = []
    for s in jerlov.PETZOLD_STATIONS:
        if s.startswith("AUTEC"):
            continue
        ratio = jerlov.petzold_scattering(s).backscatter_ratio
        b_inf = jerlov.veiling_radiance_estimate(
            w, scene.downwelling, wl, backscatter_ratio=ratio)
        seen = scene.observe(np.full(wl.size, 0.3), 5.0,
                             veiling_radiance=b_inf, face_irradiance_ratio=1.0)
        contrasts.append(seen.contrast(b_inf)[2])
    assert (round(max(contrasts), 1), round(min(contrasts), 1)) == (4.0, 2.6)


def test_figures_for_the_PAR_depth_against_490nm():
    """light_at_depth.py, its README and DECISIONS.md section 29: with D65,
    PAR reaches 1 percent 15 to 21 percent shallower than 490 nm light in
    the oceanic types, shallower down to 5C, and 12 and 45 percent deeper
    in 7C and 9C. Jerlov I, layer by layer, rises from 167 m to 107 m."""
    band = np.arange(400.0, 701.0, 5.0)
    surface = np.interp(band, *jerlov.d65())
    shallower = {}
    with quiet():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        for t in jerlov.get_source("jerlov1976").water_types:
            w = jerlov.water(t, source="jerlov1976")
            par = jerlov.par_profile(surface, band, 0.0, kd=w, unit="energy")
            at_490 = math.log(100) / w.kd(490.0)
            shallower[t] = 1 - par.depth_of_fraction() / at_490
        layered = jerlov.par_profile(surface, band, 0.0, unit="energy",
                                     kd=jerlov.descend("I", 200.0, band))
        flat = jerlov.par_profile(surface, band, 0.0, unit="energy",
                                  kd=jerlov.water("I", source="jerlov1976"))
    oceanic = [100 * shallower[t] for t in ("I", "IA", "IB", "II", "III")]
    assert (round(min(oceanic)), round(max(oceanic))) == (15, 21)
    assert all(shallower[t] > 0 for t in ("1C", "3C", "5C"))
    assert (round(-100 * shallower["7C"]), round(-100 * shallower["9C"])) \
        == (12, 45)
    assert (round(flat.depth_of_fraction()),
            round(layered.depth_of_fraction())) == (167, 107)


@source_tree
def test_README_figures_for_classify_kd():
    """README.md prints the repr of a classification; this is the
    reconstructed spectrum of from_one_measurement.py, Kd(490) = 0.060."""
    readme = (ROOT / "README.md").read_text()
    quoted = re.search(r"# (<KdClassification [^>]+>)", readme).group(1)
    band = np.arange(400.0, 651.0, 10.0)
    with quiet():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        result = jerlov.classify_kd(band, jerlov.kd_spectrum(0.060, 490, band))
    assert repr(result) == quoted


def test_figures_for_the_euphotic_zone_example():
    """examples/README.md: IA with IB close behind; 154 m by the shortcut,
    101 m layer by layer; 88 percent violet-blue there; the editions agree
    at Kd(490) = 0.030 and not at 0.045."""
    band = np.arange(400.0, 701.0, 5.0)
    surface = np.interp(band, *jerlov.d65())
    measured = jerlov.kd_spectrum(0.030, 490.0, band)
    r = jerlov.classify_kd(band, measured)
    assert [t for t, _ in r.distances[:2]] == ["IA", "IB"]
    assert round(math.log(100) / 0.030) == 154
    d = jerlov.descend("IA", 200.0, band)
    assert d.layers[3][2] == "IB" and d.layers[2][2] == "IA"
    layered = jerlov.par_profile(surface, band, 0.0, kd=d, unit="energy")
    z1 = layered.depth_of_fraction()
    assert round(z1) == 101
    one_kd = jerlov.par_profile(surface, band, 0.0, unit="energy",
                                kd=jerlov.water("IA", source="jerlov1976"))
    spectral = jerlov.par_profile(surface, band, 0.0, kd=measured,
                                  unit="energy")
    # "The shortcut is the deepest."
    assert math.log(100) / 0.030 > max(one_kd.depth_of_fraction(),
                                       spectral.depth_of_fraction(), z1)
    blue = jerlov.par_profile(surface, band, [0.0, z1], kd=d,
                              unit="energy", band=(400, 500)).par
    total = jerlov.par_profile(surface, band, [0.0, z1], kd=d,
                               unit="energy").par
    assert round(100 * blue[1] / total[1]) == 88
    editions = {s: jerlov.classify_kd(band, measured, source=s).water_type
                for s in ("jerlov1976", "jerlov1968", "austin1986")}
    assert set(editions.values()) == {"IA"}
    other = jerlov.kd_spectrum(0.045, 490.0, band)
    assert (jerlov.classify_kd(band, other).water_type,
            jerlov.classify_kd(band, other, source="jerlov1968").water_type
            ) == ("IB", "II")



def test_figures_for_the_euphotic_zone_example_against_jerlov():
    """examples/euphotic_zone.py section 4, over Jerlov's 350-700 nm: within
    1.8 points down to 10 m; 1.5 times his light at 80 m; 1 percent at
    100 m against 87, 15 percent deeper; IB below 30 m; over PAR's band
    101 m."""
    wide = np.arange(350.0, 701.0, 5.0)
    d = jerlov.descend("IA", 200.0, wide)
    with quiet():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        q = jerlov.jerlov1977_quanta("IA")
    z = q.profile_depth_m[1:]
    p = jerlov.par_profile(np.interp(wide, *jerlov.d65()), wide, z, kd=d,
                           unit="energy", band=jerlov.QUANTA_BAND_NM)
    here = 100 * p.fraction
    top = z <= 10
    assert round(np.max(np.abs(q.profile_percent[1:][top] - here[top])),
                 1) == 1.8
    assert np.all(here[z >= 15] > q.profile_percent[1:][z >= 15])
    assert z[-1] == 80 and round(here[-1] / q.profile_percent[-1], 1) == 1.5
    z1 = p.depth_of_fraction(0.01)
    assert (round(z1), q.level_depth_m[-1]) == (100, 87)
    assert round(100 * (z1 / 87 - 1)) == 15
    assert next(lo for lo, _, t in d.layers if t != "IA") == 30
    band = np.arange(400.0, 701.0, 5.0)
    par = jerlov.par_profile(np.interp(band, *jerlov.d65()), band, 0.0,
                             kd=jerlov.descend("IA", 200.0, band),
                             unit="energy")
    assert round(par.depth_of_fraction()) == 101

BAND = np.arange(400.0, 701.0, 5.0)


def _d65():
    return np.interp(BAND, *jerlov.d65())


def test_figures_for_the_optical_link_example():
    """4.34 dB per attenuation length, 9.2 in 40 dB; clearest at 494 nm in
    IB and 564 nm in 5C; the sources' ranges at 532 nm differ by up to 2.9,
    in III."""
    per_length = 10 * math.log10(math.e)
    assert round(per_length, 2) == 4.34
    assert round(40 / per_length, 1) == 9.2
    grid = np.arange(420.0, 651.0, 1.0)
    for t, nm in (("IB", 494), ("5C", 564)):
        assert grid[np.argmin(jerlov.water(t).c(grid))] == nm
    ratios = {}
    for t in ("IB", "II", "III", "1C", "3C", "5C"):
        a = jerlov.water(t).c(532.0)
        b = jerlov.water(t, source="solonenko2015").c(532.0)
        ratios[t] = max(a, b) / min(a, b)
    assert max(ratios, key=ratios.get) == "III"
    assert round(ratios["III"], 1) == 2.9


def _layered_limit(water_type, fraction):
    for depth in np.arange(200.0, 0.0, -10.0):
        try:
            d = jerlov.descend(water_type, depth, BAND)
        except jerlov.MissingQuantityError:
            continue
        p = jerlov.par_profile(_d65(), BAND, 0.0, kd=d, unit="energy")
        return p.depth_of_fraction(fraction)


def test_figures_for_the_seagrass_example():
    """At 11 percent: 13.4 m in III, 2.7 m in 9C, 3.3 m lost from 1C to 3C;
    the top-metre Kd(PAR) puts III at 9.4 m. 5 percent in 3C goes as deep
    as 11 percent in 1C."""
    limit = {t: _layered_limit(t, 0.11) for t in ("III", "1C", "3C", "9C")}
    assert round(limit["III"], 1) == 13.4
    assert round(limit["9C"], 1) == 2.7
    assert round(limit["1C"] - limit["3C"], 1) == 3.3
    top = jerlov.par_profile(_d65(), BAND, 1.0, unit="energy",
                             kd=jerlov.water("III", source="jerlov1976"))
    assert round(math.log(1 / 0.11) / -math.log(top.fraction), 1) == 9.4
    assert round(_layered_limit("3C", 0.05), 1) == round(limit["1C"], 1)


def test_figures_for_the_isolumes_example():
    """Steps of 58 and 61 m in I, 106 and 114 m with one Kd; steps grow with
    depth in every oceanic type; 1e-3 lies 9 times shallower in 9C than in
    II; the light peaks at 475 nm below, 550 nm at the surface."""
    def steps(kd, n):
        p = jerlov.par_profile(_d65(), BAND, 0.0, kd=kd, unit="energy")
        z = []
        for level in (1e-1, 1e-2, 1e-3, 1e-4, 1e-5)[:n]:
            try:
                z.append(p.depth_of_fraction(level))
            except jerlov.MissingQuantityError:
                break
        return np.diff(z)

    deepest = {"I": 200.0, "IA": 200.0, "IB": 200.0, "II": 200.0,
               "III": 170.0}
    layered_i = steps(jerlov.descend("I", 200.0, BAND), 3)
    assert [round(s) for s in layered_i] == [58, 61]
    flat_i = steps(jerlov.water("I", source="jerlov1976"), 3)
    assert [round(s) for s in flat_i] == [106, 114]
    for t, depth in deepest.items():
        s = steps(jerlov.descend(t, depth, BAND), 5)
        assert np.all(np.diff(s) > 0), t
    milli = {t: jerlov.par_profile(_d65(), BAND, 0.0, unit="energy",
                                   kd=jerlov.water(t, source="jerlov1976")
                                   ).depth_of_fraction(1e-3)
             for t in ("II", "9C")}
    assert round(milli["II"] / milli["9C"]) == 9
    photons = _d65() * BAND
    assert BAND[np.argmax(photons)] == 550.0
    t23 = jerlov.descend("II", 23.0, BAND).transmittance
    assert BAND[np.argmax(photons * t23)] == 475.0


def test_figures_for_the_turbid_seagrass_section():
    """Kd(PAR) to the 11 percent depth is above 0.27 1/m from 3C on and
    below it to 1C; there 33.3 percent puts the limit 2.1 to 2.2 times
    shallower than 11 percent."""
    kd_column, ratio = {}, {}
    for t in ("II", "III", "1C", "3C", "5C", "7C", "9C"):
        z11 = _layered_limit(t, 0.11)
        kd_column[t] = math.log(1 / 0.11) / z11
        if kd_column[t] > 0.27:
            ratio[t] = z11 / _layered_limit(t, 0.333)
    assert set(ratio) == {"3C", "5C", "7C", "9C"}
    assert kd_column["1C"] < 0.27
    assert (round(min(ratio.values()), 1), round(max(ratio.values()), 1)) \
        == (2.1, 2.2)


def test_figures_for_the_lure_example():
    """examples/README.md: 22 to 35 percent of the contrast is left at 2 m
    in Jerlov 1C; the start spans a factor of 124 across the six guesses, and
    red, blue and black change sign."""
    wl = np.arange(412.0, 701.0, 2.0)
    kept = np.exp(-jerlov.water("1C").c(np.array([450.0, 500.0, 550.0,
                                                  600.0, 650.0])) * 2.0)
    assert (round(100 * kept.min()), round(100 * kept.max())) == (22, 35)

    def sigmoid(w, edge, width):
        return 1.0 / (1.0 + np.exp(-(w - edge) / width))

    finishes = {
        "white": np.full_like(wl, 0.80),
        "chartreuse": 0.06 + 0.78 * sigmoid(wl, 500, 12)
        * (1 - 0.35 * sigmoid(wl, 625, 18)),
        "orange": 0.05 + 0.75 * sigmoid(wl, 580, 14),
        "red": 0.04 + 0.70 * sigmoid(wl, 610, 12),
        "blue": 0.05 + 0.45 * np.exp(-0.5 * ((wl - 460) / 35) ** 2),
        "black": np.full_like(wl, 0.04),
    }
    iops = jerlov.water("1C")
    ed = (np.interp(wl, *jerlov.d65())
          * np.exp(-jerlov.water("1C", source="jerlov1976").kd(wl) * 3.0))

    def y(spectrum):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", jerlov.CoverageWarning)
            return jerlov.spectrum_to_xyz(spectrum, wl)[1]

    start = {}
    for name, rho in finishes.items():
        values = []
        for side in (1.0, 0.25, 0.05):
            for ratio in (0.01, 0.02):
                water = jerlov.veiling_radiance_estimate(
                    iops, ed, wl, backscatter_ratio=ratio)
                seen = jerlov.Scene(iops, ed, wl).observe(
                    rho, 0.5, veiling_radiance=water,
                    face_irradiance_ratio=side)
                values.append((y(seen.radiance) - y(water)) / y(water))
        start[name] = values
    flips = {n for n, v in start.items() if min(v) < 0 < max(v)}
    assert flips == {"red", "blue", "black"}
    spread = max(max(v) / min(v) for v in start.values() if min(v) > 0)
    assert round(spread) == 124


def test_DECISIONS_figures_for_requiring_the_face_ratio():
    """DECISIONS.md section 34: in lure_colours.py's setting, Jerlov 1C at
    3 m, 0.5 m away, bb/b = 0.02, the red, blue and black finishes are
    brighter than the water with a ratio of 1 and darker with 0.05."""
    wl = np.arange(412.0, 701.0, 2.0)

    def sigmoid(w, edge, width):
        return 1.0 / (1.0 + np.exp(-(w - edge) / width))

    finishes = {
        "red": 0.04 + 0.70 * sigmoid(wl, 610, 12),
        "blue": 0.05 + 0.45 * np.exp(-0.5 * ((wl - 460) / 35) ** 2),
        "black": np.full_like(wl, 0.04),
    }
    iops = jerlov.water("1C")
    ed = (np.interp(wl, *jerlov.d65())
          * np.exp(-jerlov.water("1C", source="jerlov1976").kd(wl) * 3.0))
    water = jerlov.veiling_radiance_estimate(iops, ed, wl,
                                             backscatter_ratio=0.02)

    def y(spectrum):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", jerlov.CoverageWarning)
            return jerlov.spectrum_to_xyz(spectrum, wl)[1]

    for rho in finishes.values():
        def start(ratio):
            seen = jerlov.Scene(iops, ed, wl).observe(
                rho, 0.5, veiling_radiance=water,
                face_irradiance_ratio=ratio)
            return y(seen.radiance) - y(water)
        assert start(1.0) > 0 > start(0.05)


def test_figures_for_the_ultraviolet_example():
    """examples/README.md: 8 of 10 types covered, 7C and 9C not; UV-A
    reaches 0.61-0.76 of PAR's 1 percent depth in the oceanic types and
    0.22-0.25 in the coastal; at PAR's 10 percent depth 3.3-7.0 percent of
    the UV-A is left against 0.04-0.05; the step is between III and 1C,
    where the clearest UV-A goes from 1.6 to 4.2 times the clearest PAR."""
    wl = np.arange(310.0, 701.0, 5.0)
    surface = np.interp(wl, *jerlov.d65())
    share, left, gaps = {}, {}, []
    for t in ("I", "IA", "IB", "II", "III", "1C", "3C", "5C", "7C", "9C"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
            d = jerlov.descend(t, jerlov.profile_depth(t), wl)
            try:
                uva = jerlov.par_profile(surface, wl, 0.0, kd=d,
                                         unit="energy", band=(315, 400))
            except jerlov.MissingQuantityError:
                gaps.append(t)
                continue
        par = jerlov.par_profile(surface, wl, 0.0, kd=d, unit="energy")
        share[t] = uva.depth_of_fraction(0.01) / par.depth_of_fraction(0.01)
        z = par.depth_of_fraction(0.1)
        left[t] = jerlov.par_profile(surface, wl, [0.0, z], kd=d,
                                     unit="energy",
                                     band=(315, 400)).fraction[1]
    assert gaps == ["7C", "9C"] and len(share) == 8
    oceanic, coastal = ("I", "IA", "IB", "II", "III"), ("1C", "3C", "5C")

    def span(values, digits):
        return (round(min(values), digits), round(max(values), digits))
    assert span([share[t] for t in oceanic], 2) == (0.61, 0.76)
    assert span([share[t] for t in coastal], 2) == (0.22, 0.25)
    assert span([100 * left[t] for t in oceanic], 1) == (3.3, 7.0)
    assert span([100 * left[t] for t in coastal], 2) == (0.04, 0.05)
    names = list(share)
    steps = [share[a] - share[b] for a, b in zip(names, names[1:])]
    assert names[int(np.argmax(steps))] == "III"
    uv, vis = (wl >= 315) & (wl <= 400), (wl >= 400) & (wl <= 700)
    ratio = {t: (lambda k: k[uv].min() / k[vis].min())(
        jerlov.water(t, source="jerlov1976").kd(wl)) for t in ("III", "1C")}
    assert (round(ratio["III"], 1), round(ratio["1C"], 1)) == (1.6, 4.2)
    assert round(min(left[t] for t in oceanic)
                 / max(left[t] for t in coastal)) == 67


def test_figures_for_the_isolumes_example_by_eye():
    """examples/isolumes.py part 5, a thousandth of each eye's surface
    catch: the 480 nm rod's isolume is the deepest in I and II, 26 and 13 m
    below PAR's; in 1C the 500 and 530 nm rods are within 0.02 m and both
    below the 480 nm one; the light at PAR's isolume peaks at 530 nm in 1C
    and 475 nm in II."""
    def depth(t, peak):
        d = jerlov.descend(t, jerlov.profile_depth(t), BAND)
        w = None if peak is None else np.exp(-0.5 * ((BAND - peak) / 40.0) ** 2)
        return jerlov.par_profile(_d65(), BAND, 0.0, kd=d, unit="energy",
                                  photon_weight=w).depth_of_fraction(1e-3)
    z = {(t, k): depth(t, k) for t in ("I", "II", "1C")
         for k in (None, 480.0, 500.0, 530.0)}
    for t, below in (("I", 26), ("II", 13)):
        assert max((480.0, 500.0, 530.0), key=lambda k: z[t, k]) == 480.0
        assert round(z[t, 480.0] - z[t, None]) == below
    assert round(abs(z["1C", 500.0] - z["1C", 530.0]), 2) == 0.02
    assert min(z["1C", 500.0], z["1C", 530.0]) > z["1C", 480.0]
    for t, nm in (("1C", 530.0), ("II", 475.0)):
        p = jerlov.par_profile(_d65(), BAND, 0.0, unit="energy",
                               kd=jerlov.descend(t, jerlov.profile_depth(t),
                                                 BAND))
        assert p.wavelengths_nm[np.argmax(p.spectrum_at(z[t, None]))] == nm


def test_figures_for_the_eye_example():
    """examples/what_an_eye_sees.py, counting photons: 76 percent of them
    between 450 and 550 nm at 50 m in II; the L and M cones within 0.1
    percent at the surface and the 480 nm rod ahead at 20 and 50 m; the S
    cone at 46 percent of the largest catch, 57 counted as energy; the
    camera's red-to-blue ratio falls by a factor of 29 over 50 m."""
    wl = np.arange(350.0, 701.0, 2.0)
    iops = jerlov.water("II")
    kd = jerlov.water("II", source="austin1986")
    day = np.interp(wl, *jerlov.d65(), left=0.0, right=0.0)

    def gauss(peak, width):
        return np.exp(-0.5 * ((wl - peak) / width) ** 2)

    def ed(z):
        with quiet():
            warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
            return jerlov.Scene.at_depth(iops, z, day, wl, kd=kd).downwelling

    def flux(band, z):
        return jerlov.par_profile(day, wl, z, kd=kd, unit="energy",
                                  band=band).par
    assert round(100 * flux((450, 550), 50.0) / flux((350, 700), 50.0)) == 76
    receptors = {"L": (564, 45), "M": (534, 45), "S": (420, 30),
                 "r480": (480, 40), "r500": (500, 40), "r530": (530, 40)}

    def catch(spectrum):
        return {n: float(jerlov.integrate_response(spectrum, wl, gauss(*pw),
                                                   wl)[0])
                for n, pw in receptors.items()}
    surface = catch(ed(0.0) * wl)
    assert sorted(surface, key=surface.get)[-2:] in (["M", "L"], ["L", "M"])
    assert round(100 * abs(1 - surface["M"] / surface["L"]), 1) == 0.1
    for z in (20.0, 50.0):
        at = catch(ed(z) * wl)
        assert max(at, key=at.get) == "r480"
    energy = catch(ed(0.0))
    assert round(100 * surface["S"] / max(surface.values())) == 46
    assert round(100 * energy["S"] / max(energy.values())) == 57
    camera = np.stack([gauss(c, 35.0) for c in (450, 550, 620)], axis=1)
    rb = {z: (lambda ch: ch[2] / ch[0])(
        jerlov.integrate_response(ed(z) * wl, wl, camera, wl, name="camera"))
        for z in (0.0, 50.0)}
    assert round(rb[0.0] / rb[50.0]) == 29


@pytest.fixture(scope="module")
def radiance_example():
    """examples/radiance_distribution.py, run once: its figures as returned
    by main(). About two minutes."""
    import contextlib
    import io
    import runpy
    path = ROOT / "examples" / "radiance_distribution.py"
    module = runpy.run_path(str(path), run_name="radiance_distribution")
    with contextlib.redirect_stdout(io.StringIO()):
        return module["main"]()


@source_tree
def test_figures_for_the_radiance_example(radiance_example):
    """examples/README.md: HAOCE 11 nearest II's b; Gershun's law recovers
    a within 2 percent; Kd within 6 percent of Jerlov (1976) at 500 and 550
    nm and 20 to 24 percent above at 450; overcast Kd above the sun's at
    every wavelength; E0 / Ed 1.24 to 1.37; AUTEC 7's phase function raises
    Eu / Ed at 10 m by about half."""
    r = radiance_example
    assert (r["station"], r["other"]) == ("HAOCE 11", "AUTEC 7")
    assert round(100 * r["straight"]) == 18
    assert max(abs(g) for g in r["gershun"]) < 0.02
    for wl in (500.0, 550.0):
        assert max(abs(x - 1) for x in r["kd_ratio"][wl]) < 0.065
    low, high = sorted(r["kd_ratio"][450.0])
    assert (round(100 * (low - 1)), round(100 * (high - 1))) == (20, 24)
    f = r["fields"]
    for wl in (450.0, 500.0, 550.0):
        assert f[wl, None]["kd"] > f[wl, 40.0]["kd"]
        # "its mean cosine stays lower"
    sun, sky = f[500.0, 40.0], f[500.0, None]
    mu = {k: (v["ed"] - v["eu"]) / v["e0"] for k, v in (("sun", sun),
                                                         ("sky", sky))}
    assert np.all(mu["sky"] < mu["sun"])
    assert (round((sun["e0"] / sun["ed"]).min(), 2),
            round((sky["e0"] / sky["ed"]).max(), 2)) == (1.24, 1.37)
    other = r["other_field"]
    change = (other["eu"][2] / other["ed"][2]) / (sun["eu"][2] / sun["ed"][2]) - 1
    assert round(100 * change) == 48


@source_tree
def test_the_radiance_example_brightest_cell_is_the_sunbeam(radiance_example):
    """Part 4: the brightest scattered light is in the cell around the
    refracted sunbeam at every depth; 57 times overhead at 2 m and 11 at
    20 m; straight down 15 percent of overhead at 2 m, 2.3 at 20 m; the
    direct share of Ed falls with depth."""
    r = radiance_example
    sun = r["fields"][500.0, 40.0]["radiance"]
    refracted = np.degrees(np.arcsin(np.sin(np.radians(40.0)) / 1.34))
    cell = int(refracted // 10.0)
    for k in range(sun.shape[0]):
        assert np.unravel_index(np.argmax(sun[k]), sun[k].shape) == (cell, 0)
    assert (round(r["peak"][0]), round(r["peak"][-1])) == (57, 11)
    assert (round(100 * r["down"][0]), round(100 * r["down"][-1], 1)) == (15, 2.3)
    assert np.all(np.diff(r["direct_share"]) < 0)


@source_tree
def test_the_radiance_example_against_tyler(radiance_example):
    """Part 6: a from Tyler's tables by Gershun's law, 0.1149 and 0.1089,
    mean 0.1119, b 0.2841; HAOCE 5 nearest, HAOCE 11 next; the model's mean
    cosine 0.762 to 0.774 against 0.704 to 0.715; Eu / Ed 0.0131 to 0.0151
    against 0.0189 to 0.0233; E0 / Ed 1.27 to 1.29 against 1.37 to 1.39; Kd
    0.144 to 0.146 against 0.163 and 0.153; Tyler between the two skies at
    5 and 25 degrees, above both at 65 and 85, where the model gives 0.28 to
    0.90 of his; standard errors at most 6 and 22 percent."""
    lake = radiance_example["lake"]
    assert [round(x, 4) for x in lake["found"]] == [0.1149, 0.1089]
    assert (round(lake["a"], 4), round(lake["b"], 4)) == (0.1119, 0.2841)
    assert (lake["near"], lake["second"]) == ("HAOCE 5", "HAOCE 11")
    assert round(lake["sun_zenith"], 1) == 33.4
    model = {k: np.concatenate([f[k] for f in lake["fields"].values()])
             for k in ("mu", "R", "ratio", "kd")}
    tyler = lake["tyler"]
    assert (round(model["mu"].min(), 3), round(model["mu"].max(), 3)) \
        == (0.762, 0.774)
    assert (round(tyler["mu"].min(), 3), round(tyler["mu"].max(), 3)) \
        == (0.704, 0.715)
    assert (round(model["R"].min(), 4), round(model["R"].max(), 4)) \
        == (0.0131, 0.0151)
    assert (round(tyler["R"].min(), 4), round(tyler["R"].max(), 4)) \
        == (0.0189, 0.0233)
    assert (round(model["ratio"].min(), 2), round(model["ratio"].max(), 2)) \
        == (1.27, 1.29)
    assert (round(tyler["ratio"].min(), 2), round(tyler["ratio"].max(), 2)) \
        == (1.37, 1.39)
    assert (round(model["kd"].min(), 3), round(model["kd"].max(), 3)) \
        == (0.144, 0.146)
    assert [round(x, 3) for x in tyler["kd"]] == [0.163, 0.153]
    # "a mean cosine too high has to come with a K too low"
    assert model["mu"].min() > tyler["mu"].max()
    assert model["kd"].max() < tyler["kd"].min()
    assert lake["between"] == [5, 25] and lake["above"] == [65, 85]
    assert (round(lake["side"].min(), 2), round(lake["side"].max(), 2)) \
        == (0.28, 0.90)
    assert (round(100 * lake["noise"]), round(100 * lake["cell_se"])) \
        == (6, 22)
    assert round(100 * lake["grid_error"], 1) == 1.0
    # examples/README.md: 0.76 to 0.77 against 0.70 to 0.72; Eu / Ed 0.56
    # to 0.80 of his
    assert (round(model["mu"].min(), 2), round(model["mu"].max(), 2)) \
        == (0.76, 0.77)
    assert (round(tyler["mu"].min(), 2), round(tyler["mu"].max(), 2)) \
        == (0.70, 0.72)
    share = np.array([f["R"] / tyler["R"] for f in lake["fields"].values()])
    assert (round(share.min(), 2), round(share.max(), 2)) == (0.56, 0.80)


@source_tree
def test_the_tyler_tables_give_back_what_the_example_says():
    """Part 6's Tyler rows, from the tables directly: the integration is
    the example's, the numbers are the package's."""
    import runpy
    module = runpy.run_path(str(ROOT / "examples" / "radiance_distribution.py"),
                            run_name="radiance_distribution")
    m = {d: module["measured_irradiances"](jerlov.tyler1958_radiance(d))
         for d in (41.3, 53.7, 66.1)}
    mu = [(x["ed"] - x["eu"]) / x["e0"] for x in m.values()]
    assert [round(v, 3) for v in mu] == [0.704, 0.708, 0.715]
    cells = module["measured_cells"](jerlov.tyler1958_radiance(41.3))
    assert cells.shape == (18, 4)
    # a uniform table averages to itself
    flat = type("T", (), dict(tilt_deg=np.arange(0.0, 181, 10),
                              azimuth_deg=np.arange(0.0, 181, 20),
                              radiance=np.ones((19, 10))))
    assert np.allclose(module["measured_cells"](flat), 1.0)
    e = module["measured_irradiances"](flat)
    # the trapezoid rule on a 10 degree grid is within 2 percent
    assert abs(e["e0"] / (4 * np.pi) - 1) < 0.02
    assert abs(e["ed"] / np.pi - 1) < 0.02


@pytest.fixture(scope="module")
def radiance_module():
    import runpy
    return runpy.run_path(str(ROOT / "examples" / "radiance_distribution.py"),
                          run_name="radiance_distribution")


@source_tree
def test_the_radiance_engine_turns_by_the_angle_asked(radiance_module):
    """DECISIONS.md section 40: the turn is exact, straight up and down
    included, and its azimuth is uniform."""
    turn = radiance_module["turn"]
    rng = np.random.default_rng(1)
    v = rng.normal(size=(3, 20000))
    v /= np.linalg.norm(v, axis=0)
    v[:, :5] = [[0.0], [0.0], [1.0]]
    v[:, 5:10] = [[0.0], [0.0], [-1.0]]
    cos_t = rng.uniform(-1, 1, v.shape[1])
    new = np.array(turn(*v, cos_t, rng))
    assert np.allclose(np.sum(new * v, axis=0), cos_t, atol=1e-9)
    assert np.allclose(np.linalg.norm(new, axis=0), 1.0)
    old = np.array([0.3, -0.5, 0.81]) / np.linalg.norm([0.3, -0.5, 0.81])
    n = 200_000
    new = np.array(turn(*(np.full(n, x) for x in old), np.full(n, 0.5), rng))
    # uniform azimuth: the mean new direction is cos_t times the old one
    assert np.allclose(new.mean(axis=1), 0.5 * old, atol=0.005)


@source_tree
@pytest.mark.parametrize("w, depths, rtol", [
    (0.5, (4.0, 6.0, 8.0), 0.06),
    (0.72, (4.0, 6.0, 8.0), 0.03),
    (0.9, (8.0, 11.0, 14.0), 0.03)])
def test_the_radiance_engine_against_isotropic_scattering(
        radiance_module, w, depths, rtol):
    """DECISIONS.md section 40: with isotropic scattering, deep water has an
    exact asymptotic light field; the engine reproduces its K, mean cosine,
    Eu / Ed and E0 / Ed within 3 percent at w = 0.72 and 0.9, and within 6
    at 0.5."""
    m = radiance_module
    lo, hi = 1e-9, 1 - 1e-12
    for _ in range(200):
        k = 0.5 * (lo + hi)
        if w / (2 * k) * np.log((1 + k) / (1 - k)) < 1:
            lo = k
        else:
            hi = k
    mu = np.linspace(0.0, 1.0, 100_001)
    ed = m["trapezoid"](mu / (1 - k * mu), mu)
    eu = m["trapezoid"](mu / (1 + k * mu), mu)
    e0 = m["trapezoid"](1 / (1 - k * mu) + 1 / (1 + k * mu), mu)
    iso = dict(cdf=np.linspace(0, 1, 2001), cos=np.linspace(1, -1, 2001),
               straight=0.0)
    depths = np.array(depths)
    runs = [m["simulate"](1 - w, w, 0.0, iso, iso, None, seed=seed,
                          photons=200_000, depths=depths, half_slab=0.25)
            for seed in range(4)]
    f = m["summary"](runs, depths)
    assert np.allclose(f["kd"], k, rtol=rtol)
    assert np.allclose(f["mu"], (1 - w) / k, rtol=rtol)
    assert np.allclose(f["R"], eu / ed, rtol=rtol)
    assert np.allclose(f["ratio"], e0 / ed, rtol=rtol)


@source_tree
def test_the_radiance_example_looking_for_the_cause(radiance_example):
    """Part 7, as printed: the phase function moves the mean cosine from
    0.710 to 0.767; AUTEC 8, NUC 2200 and NUC 2040 within 0.002 of Tyler's;
    HAOCE 11 and HAOCE 5 the lowest bb/b and the highest mean cosines; c at
    depth 0.773; b = 0.48 needed, c = 0.60, 1.5 times; then Eu / Ed 0.0238,
    E0 / Ed 1.380, side 1.01; AUTEC 9 backscatters more than NUC 2200 and
    has the higher mean cosine."""
    r = radiance_example["cause"]
    st = r["stations"]
    assert (round(r["span"]["mu"][0], 3), round(r["span"]["mu"][1], 3)) \
        == (0.710, 0.767)
    assert r["closest"] == ["AUTEC 8", "NUC 2200", "NUC 2040"]
    assert round(r["gap"], 3) <= 0.002
    assert r["lowest"] == ["HAOCE 11", "HAOCE 5"]
    assert set(r["order"][-2:]) == {"HAOCE 11", "HAOCE 5"}
    assert round(r["deep"]["mu"], 3) == 0.773
    assert round(r["b_needed"], 2) == 0.48
    lake = radiance_example["lake"]
    assert round(lake["a"] + r["b_needed"], 2) == 0.60
    # examples/README.md: "a b about 1.7 times larger"
    assert round(r["b_needed"] / lake["b"], 1) == 1.7
    assert round((lake["a"] + r["b_needed"]) / 0.396, 1) == 1.5
    f = r["fitted"]
    assert (round(f["R"], 4), round(f["ratio"], 3), round(f["side"], 2)) \
        == (0.0238, 1.380, 1.01)
    bb = {s: jerlov.petzold_scattering(s).backscatter_ratio
          for s in ("AUTEC 9", "NUC 2200")}
    assert bb["AUTEC 9"] > bb["NUC 2200"]
    assert st["AUTEC 9"]["mu"] > st["NUC 2200"]["mu"]

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
                                     veiling_radiance=b_inf)
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
                             veiling_radiance=b_inf)
        contrasts.append(seen.contrast(b_inf)[2])
    assert (round(max(contrasts), 1), round(min(contrasts), 1)) == (4.0, 2.6)

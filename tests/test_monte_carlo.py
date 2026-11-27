"""jerlov.monte_carlo_light_field: DECISIONS.md sections 38 to 40 and 138.

The engine's own checks (the turn, the exact solution for isotropic
scattering, moved here from tests of examples/radiance_distribution.py),
closed forms, the comparison with tools/shallow_rrs_mc.py, and every
refusal."""

from __future__ import annotations

import csv
import math
import pathlib

import numpy as np
import pytest

import jerlov
from jerlov import monte_carlo as mc

ROOT = pathlib.Path(__file__).resolve().parent.parent
source_tree = pytest.mark.skipif(
    not (ROOT / "pyproject.toml").exists(),
    reason="not running from a source tree")


def _trapezoid(y, x):
    return float(np.sum(0.5 * (y[1:] + y[:-1]) * np.diff(x)))


def _call(**changes):
    station = jerlov.petzold_scattering("NUC 2240")
    kwargs = dict(
        pure_water_b=0.003, salinity_psu=35.0,
        phase_function=station, station_salinity_psu=35.0, cut_deg=1.0,
        refractive_index=1.34, sun_zenith_deg=30.0, depth_m=math.inf,
        bottom_albedo=None, depths_m=[1.0, 3.0], slab_m=1.0,
        zenith_step_deg=10.0, azimuth_step_deg=45.0, photons=2000,
        batches=2, seed=0, wind="flat")
    a = changes.pop("a", 0.1)
    b = changes.pop("b", 0.3)
    wavelength = changes.pop("wavelength_nm", 500.0)
    kwargs.update(changes)
    return jerlov.monte_carlo_light_field(a, b, wavelength, **kwargs)


# -- the engine (DECISIONS.md section 40) ------------------------------------

def test_the_turn_is_by_the_angle_asked():
    """The turn is exact, straight up and down included, and its azimuth
    is uniform."""
    rng = np.random.default_rng(1)
    v = rng.normal(size=(3, 20000))
    v /= np.linalg.norm(v, axis=0)
    v[:, :5] = [[0.0], [0.0], [1.0]]
    v[:, 5:10] = [[0.0], [0.0], [-1.0]]
    cos_t = rng.uniform(-1, 1, v.shape[1])
    new = np.array(mc._turn(*v, cos_t, rng))
    assert np.allclose(np.sum(new * v, axis=0), cos_t, atol=1e-9)
    assert np.allclose(np.linalg.norm(new, axis=0), 1.0)
    old = np.array([0.3, -0.5, 0.81]) / np.linalg.norm([0.3, -0.5, 0.81])
    n = 200_000
    new = np.array(mc._turn(*(np.full(n, x) for x in old), np.full(n, 0.5),
                            rng))
    assert np.allclose(new.mean(axis=1), 0.5 * old, atol=0.005)


@pytest.mark.parametrize("w, depths, rtol", [
    (0.5, (4.0, 6.0, 8.0), 0.06),
    (0.72, (4.0, 6.0, 8.0), 0.03),
    (0.9, (8.0, 11.0, 14.0), 0.03)])
def test_the_engine_against_isotropic_scattering(w, depths, rtol):
    """With isotropic scattering, deep water has an exact asymptotic light
    field; the engine reproduces its K, mean cosine, Eu / Ed and E0 / Ed
    within 3 percent at w = 0.72 and 0.9, and within 6 at 0.5."""
    lo, hi = 1e-9, 1 - 1e-12
    for _ in range(200):
        k = 0.5 * (lo + hi)
        if w / (2 * k) * np.log((1 + k) / (1 - k)) < 1:
            lo = k
        else:
            hi = k
    mu = np.linspace(0.0, 1.0, 100_001)
    ed = _trapezoid(mu / (1 - k * mu), mu)
    eu = _trapezoid(mu / (1 + k * mu), mu)
    e0 = _trapezoid(1 / (1 - k * mu) + 1 / (1 + k * mu), mu)
    iso = dict(cdf=np.linspace(0, 1, 2001), cos=np.linspace(1, -1, 2001),
               straight=0.0, angles=np.linspace(0, np.pi, 3),
               per_sr=np.full(3, 1 / (4 * np.pi)))
    depths = np.array(depths)
    runs = [mc._simulate(1 - w, w, 0.0, iso, iso, None, seed,
                         photons=200_000, depths=depths, half_slab=0.25,
                         n_water=1.34, d_zenith=10.0, d_azimuth=45.0)
            for seed in range(4)]
    kd = np.mean([np.log(r["ed"][:-1] / r["ed"][1:]) / np.diff(depths)
                  for r in runs], axis=0)
    mean = {key: np.mean([r[key] for r in runs], axis=0)
            for key in ("ed", "eu", "e0")}
    assert np.allclose(kd, k, rtol=rtol)
    assert np.allclose((mean["ed"] - mean["eu"]) / mean["e0"], (1 - w) / k,
                       rtol=rtol)
    assert np.allclose(mean["eu"] / mean["ed"], eu / ed, rtol=rtol)
    assert np.allclose(mean["e0"] / mean["ed"], e0 / ed, rtol=rtol)


# -- closed forms (DECISIONS.md section 138, check 3) ------------------------

def _fresnel_below(mu, n=1.34):
    return mc._fresnel(np.asarray(mu, dtype=float), n, 1.0)


def test_without_scattering_ed_follows_beer():
    a, sun = 0.2, 30.0
    f = _call(a=a, b=1e-9, pure_water_b=1e-9, sun_zenith_deg=sun,
              depths_m=[1.0, 3.0, 6.0], slab_m=0.5, photons=40_000,
              batches=4)
    mu_air = math.cos(math.radians(sun))
    t = 1 - float(mc._fresnel(np.array([mu_air]), 1.0, 1.34)[0])
    mu_w = math.sqrt(1 - (1 - mu_air ** 2) / 1.34 ** 2)
    want = t * np.exp(-(a + 1e-9) * f.depths_m / mu_w)
    se = np.std(f.batch_ed, axis=0, ddof=1) / 2
    assert np.all(np.abs(f.ed - want) <= 3 * se + 1e-12)
    assert np.allclose(f.eu, 0.0)


@pytest.mark.parametrize("a, depth, albedo, sun", [
    (0.1, 3.0, 0.5, 30.0), (0.5, 1.0, 1.0, 0.0), (0.05, 10.0, 0.3, 60.0)])
def test_without_scattering_the_bottom_gives_its_closed_form(a, depth,
                                                             albedo, sun):
    """With no scattering, rrs is the bottom's alone, the light going back
    and forth between the bottom and the surface summed as a geometric
    series."""
    f = _call(a=a, b=1e-9, pure_water_b=1e-9, sun_zenith_deg=sun,
              depth_m=depth, bottom_albedo=albedo, depths_m=[depth / 2],
              slab_m=depth / 4, photons=40_000, batches=8)
    c = a + 1e-9
    mu_air = math.cos(math.radians(sun))
    t = 1 - float(mc._fresnel(np.array([mu_air]), 1.0, 1.34)[0])
    mu_w = math.sqrt(1 - (1 - mu_air ** 2) / 1.34 ** 2)
    mu = np.linspace(1e-6, 1.0, 200_001)
    r = _fresnel_below(mu)
    q = _trapezoid(2 * mu * r * np.exp(-2 * c * depth / mu), mu)
    r1 = _trapezoid(2 * mu * r * np.exp(-c * depth / mu), mu)
    arrivals = t * math.exp(-c * depth / mu_w) / (1 - albedo * q)
    lu = arrivals * albedo / math.pi * math.exp(-c * depth)
    ed0 = t + arrivals * albedo * r1
    assert abs(f.rrs - lu / ed0) <= 3 * f.rrs_se


# -- against the shallow-water tool (check 4) --------------------------------

@source_tree
def test_against_the_shallow_water_tool():
    """tools/monte_carlo_check.py's runs: the package's rrs over the
    tool's, for the 243 runs with a bottom, in combined standard errors.
    The figures are quoted in DECISIONS.md section 138."""
    path = ROOT / "examples" / "data" / "monte_carlo" / \
        "against_shallow_tool.csv"
    with path.open() as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 243
    z = np.abs([float(r["z"]) for r in rows])
    within = {k: float(np.mean(z <= k)) for k in (1, 2, 3)}
    ratio = [float(r["package"]) / float(r["tool"]) for r in rows]
    decisions = " ".join((ROOT / "DECISIONS.md").read_text().split())
    section = decisions.split("## 138. ")[1]
    assert (f"{100 * within[1]:.1f} percent within 1 combined standard "
            f"error, {100 * within[2]:.1f} percent within 2 and "
            f"{100 * within[3]:.1f} percent within 3") in section
    assert (f"{min(ratio):.3f} to {max(ratio):.3f} of the tool's, median "
            f"{float(np.median(ratio)):.3f}") in section
    same_z = np.abs([float(r["same_phase_z"]) for r in rows])
    same = {k: float(np.mean(same_z <= k)) for k in (1, 2, 3)}
    same_ratio = [float(r["same_phase"]) / float(r["tool"]) for r in rows]
    assert (f"{100 * same[1]:.1f} percent within 1 combined standard "
            f"error, {100 * same[2]:.1f} percent within 2 and "
            f"{100 * same[3]:.1f} percent within 3") in section
    assert (f"{min(same_ratio):.3f} to {max(same_ratio):.3f} of the "
            f"tool's, median {float(np.median(same_ratio)):.3f}") in section
    assert same[3] > 0.95 and abs(np.median(same_ratio) - 1) < 0.01
    changelog = " ".join((ROOT / "CHANGELOG.md").read_text().split())
    log = changelog.split("## 1.33.0")[1].split("## 1.32.4")[0]
    assert f"{float(np.median(ratio)):.3f} of the tool's" in log
    assert f"convention in the same engine, {float(np.median(same_ratio)):.3f}" in log
    station = jerlov.petzold_scattering("NUC 2240")
    bw = float(jerlov.pure_water_scattering(530.0, salinity_psu=37.0))
    bp = (station.backscatter_ratio * station.b - bw / 2) / (station.b - bw)
    assert (f"ratio is then {bp:.4f} against the whole station's "
            f"{station.backscatter_ratio:.4f}") in section


@source_tree
def test_a_stored_check_run_is_reproduced():
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import monte_carlo_check as check
    finally:
        sys.path.pop(0)
    path = ROOT / "examples" / "data" / "monte_carlo" / \
        "against_shallow_tool.csv"
    with path.open() as handle:
        row = next(csv.DictReader(handle))
    station = jerlov.petzold_scattering("NUC 2240")
    value, error = check.run(row, station)
    assert f"{value:.6e}" == row["package"]
    assert f"{error:.2e}" == row["package_se"]
    value, error = check.run_same_phase(row, station)
    assert f"{value:.6e}" == row["same_phase"]
    assert f"{error:.2e}" == row["same_phase_se"]


# -- the result --------------------------------------------------------------

def test_the_result_holds_its_batches_and_says_what_it_leaves_out():
    f = _call()
    assert f.batch_ed.shape == (2, 2)
    assert np.array_equal(f.ed, f.batch_ed.mean(axis=0))
    assert f.radiance.shape == (2, 18, 4)
    assert np.array_equal(f.zenith_edges_deg, np.arange(0.0, 181.0, 10.0))
    assert f.inputs["phase_function"] == "NUC 2240"
    assert 0 < f.inputs["straight_share"] < 1
    assert any("waves" in s for s in f.left_out)
    d = f.as_dict()
    assert d["inputs"]["seed"] == 0 and d["method"].endswith("138 and 139")
    assert f == _call()                    # the same seed, the same field
    assert f != _call(seed=1)


def test_a_fournier_forand_is_the_particles_alone():
    ff = jerlov.mobley2002_fournier_forand(0.0183)
    f = _call(phase_function=ff, station_salinity_psu=None, cut_deg=0.5)
    assert f.inputs["straight_share"] == pytest.approx(
        float(ff.cumulative(0.5)))
    assert f.inputs["phase_function"].startswith("Fournier-Forand")


# -- refusals (check 5) ------------------------------------------------------

@pytest.mark.parametrize("name", [
    "pure_water_b", "salinity_psu", "phase_function",
    "cut_deg", "refractive_index", "depths_m", "slab_m", "zenith_step_deg",
    "azimuth_step_deg", "photons", "batches", "seed", "depth_m"])
def test_every_choice_is_required(name):
    with pytest.raises(jerlov.MissingQuantityError):
        _call(**{name: None})


def test_the_sun_the_bottom_and_the_station_salinity_are_required():
    station = jerlov.petzold_scattering("NUC 2240")
    base = dict(
        pure_water_b=0.003, salinity_psu=35.0,
        phase_function=station, station_salinity_psu=35.0, cut_deg=1.0,
        refractive_index=1.34, sun_zenith_deg=30.0, depth_m=math.inf,
        bottom_albedo=None, depths_m=[1.0], slab_m=1.0, zenith_step_deg=10.0,
        azimuth_step_deg=45.0, photons=100, batches=2, seed=0, wind="flat")
    for name in ("sun_zenith_deg", "bottom_albedo"):
        kwargs = {k: v for k, v in base.items() if k != name}
        with pytest.raises(jerlov.MissingQuantityError):
            jerlov.monte_carlo_light_field(0.1, 0.3, 500.0, **kwargs)
    with pytest.raises(jerlov.MissingQuantityError):
        _call(station_salinity_psu=None)
    with pytest.raises(jerlov.MissingQuantityError):
        _call(depth_m=5.0, bottom_albedo=None, depths_m=[1.0])


@pytest.mark.parametrize("changes", [
    dict(a=-0.1), dict(b=0.0), dict(a=float("nan")),
    dict(pure_water_b=0.5), dict(salinity_psu=50.0),
    dict(cut_deg=0.05), dict(cut_deg=11.0), dict(refractive_index=1.6),
    dict(sun_zenith_deg=90.0), dict(depth_m=-1.0),
    dict(depth_m=5.0, bottom_albedo=1.2, depths_m=[1.0]),
    dict(bottom_albedo=0.5), dict(depths_m=[3.0, 1.0]),
    dict(depths_m=[0.2]), dict(depth_m=2.0, bottom_albedo=0.5,
                               depths_m=[1.8]),
    dict(zenith_step_deg=7.0), dict(batches=1), dict(photons=0),
    dict(photons=10.0), dict(seed=-1),
    dict(phase_function=jerlov.mobley2002_fournier_forand(0.0183)),
    dict(phase_function="NUC 2240")])
def test_what_is_refused(changes):
    with pytest.raises((ValueError, TypeError)):
        _call(**changes)


@pytest.mark.parametrize("name", ["a", "cut_deg", "photons", "seed"])
def test_a_bool_or_text_is_refused(name):
    for bad in (True, "1"):
        with pytest.raises((ValueError, TypeError)):
            _call(**{name: bad})


# -- waves (DECISIONS.md section 139) ----------------------------------------

def test_wind_left_out_is_flat_with_a_future_warning():
    import warnings
    station = jerlov.petzold_scattering("NUC 2240")
    kwargs = dict(
        pure_water_b=0.003, salinity_psu=35.0, phase_function=station,
        station_salinity_psu=35.0, cut_deg=1.0, refractive_index=1.34,
        sun_zenith_deg=30.0, depth_m=math.inf, bottom_albedo=None,
        depths_m=[1.0, 3.0], slab_m=1.0, zenith_step_deg=10.0,
        azimuth_step_deg=45.0, photons=2000, batches=2, seed=0)
    with pytest.warns(FutureWarning, match="wind"):
        old = jerlov.monte_carlo_light_field(0.1, 0.3, 500.0, **kwargs)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        flat = jerlov.monte_carlo_light_field(0.1, 0.3, 500.0, wind="flat",
                                              **kwargs)
    assert old == flat
    assert flat.inputs["wind"] == "flat"
    assert any("the surface is flat" in s for s in flat.left_out)


def test_the_slopes_are_cox_and_munk_s():
    rng = np.random.default_rng(0)
    s2 = mc.COX_MUNK_MEAN_SQUARE_SLOPE[0] \
        + mc.COX_MUNK_MEAN_SQUARE_SLOPE[1] * 7.0
    # straight down onto the surface every facet faces the light, so the
    # drawn normals are the distribution's own
    d = np.tile([[0.0], [0.0], [1.0]], 1_000_000)
    normal, _, w = mc._facets(d, s2, rng)
    slopes = (normal[0] / normal[2]) ** 2 + (normal[1] / normal[2]) ** 2
    assert float(np.mean(slopes)) == pytest.approx(s2, rel=0.01)
    assert float(np.mean(w)) == pytest.approx(1.0, rel=1e-3)


def _transparent(sun, wind, photons=200_000, surface_facets="one"):
    ff = jerlov.mobley2002_fournier_forand(0.0183)
    return _call(a=1e-3, b=1e-9, pure_water_b=1e-9, phase_function=ff,
                 station_salinity_psu=None, sun_zenith_deg=sun,
                 depths_m=[1.0], photons=photons, batches=4, wind=wind,
                 surface_facets=None if wind == "flat" else surface_facets)


@pytest.mark.parametrize("sun, tolerance", [(30.0, 0.005), (60.0, 0.01)])
def test_energy_is_kept_at_a_wavy_surface(sun, tolerance):
    """Chami et al. (2015), section 3.2, Eq. (31): with transparent water,
    the sun at 30 degrees and wind 7 m/s, Ed(0-) + Eu(0+) = Ed(0+)."""
    f = _transparent(sun, 7.0)
    total = f.transmitted_at_surface + f.reflected_at_surface
    assert abs(total - 1) <= tolerance


def _reflectance_by_quadrature(sun, wind, n=1.34):
    s2 = mc.COX_MUNK_MEAN_SQUARE_SLOPE[0] \
        + mc.COX_MUNK_MEAN_SQUARE_SLOPE[1] * wind
    sd = math.sqrt(s2 / 2)
    g = np.linspace(-7 * sd, 7 * sd, 1201)
    zx, zy = np.meshgrid(g, g)
    p = np.exp(-(zx ** 2 + zy ** 2) / (2 * sd * sd))
    mu = math.cos(math.radians(sun))
    d = np.array([math.sqrt(1 - mu * mu), 0.0, mu])
    norm = np.sqrt(1 + zx ** 2 + zy ** 2)
    nx, ny, nz = zx / norm, zy / norm, -1 / norm
    dn = d[0] * nx + d[1] * ny + d[2] * nz
    front = dn < 0
    cos_i = np.where(front, -dn, 1.0)
    w = cos_i / (np.abs(nz) * abs(d[2]))
    r, _ = mc._fresnel_cos(cos_i, 1.0, n)
    # the facets in sunlight, each by the share of the beam it intercepts
    return float(np.sum(p * front * w * r) / np.sum(p * front * w))


@pytest.mark.parametrize("sun", [30.0, 60.0])
@pytest.mark.parametrize("wind", [2.0, 7.0, 14.0])
def test_the_sun_s_reflectance_is_the_slopes_integral(sun, wind):
    f = _transparent(sun, wind)
    want = _reflectance_by_quadrature(sun, wind)
    assert abs(f.reflected_at_surface - want) \
        <= 3 * f.reflected_at_surface_se + 1e-6
    assert any("whitecaps" in s for s in f.left_out)
    assert f.inputs["wind"] == wind


def test_waves_against_a_flat_surface_in_the_limit():
    """With almost no slope the wavy surface reflects the sun as a flat
    one does."""
    flat = _transparent(30.0, "flat", photons=20_000)
    calm = mc._facets(np.tile([[0.5], [0.0], [math.sqrt(0.75)]], 10),
                      1e-12, np.random.default_rng(0))
    assert np.allclose(calm[2], 1.0)
    r, _ = mc._fresnel_cos(np.array([math.sqrt(0.75)]), 1.0, 1.34)
    assert flat.reflected_at_surface == pytest.approx(float(r[0]), rel=1e-9)


@pytest.mark.parametrize("bad", ["windy", -1.0, float("nan"), True])
def test_a_bad_wind_is_refused(bad):
    with pytest.raises((ValueError, TypeError)):
        _call(wind=bad)


@source_tree
def test_the_surface_figures_after_the_correction_are_quoted_as_computed():
    """1.34.0's figures (DECISIONS.md section 139) were made before the
    correction of section 140; section 140 quotes them as they are now."""
    decisions = " ".join((ROOT / "DECISIONS.md").read_text().split())
    section = decisions.split("## 140. ")[1]
    total = {(s, w): (lambda f: f.reflected_at_surface
                      + f.transmitted_at_surface - 1)(_transparent(s, w))
             for s, w in ((30.0, 7.0), (60.0, 7.0), (60.0, 14.0),
                          (80.0, 7.0))}
    assert (f"exceeds 1 by {100 * total[30.0, 7.0]:.3f} percent at 30 "
            f"degrees, {100 * total[60.0, 7.0]:.3f} at 60 and "
            f"{100 * total[60.0, 14.0]:.3f} at 60 degrees and 14 m/s") in section
    assert (f"falls short of it by {-100 * total[80.0, 7.0]:.3f} percent at "
            "80 degrees") in section
    assert abs(total[80.0, 7.0]) < 0.005
    for sun in (30.0, 60.0):
        r = [_transparent(sun, w).reflected_at_surface
             for w in (2.0, 7.0, 14.0)]
        assert f"{min(r):.4f} to {max(r):.4f} at {sun:.0f}" in section


@source_tree
def test_question_5_with_waves_is_quoted_as_computed():
    import contextlib
    import io
    import runpy
    with contextlib.redirect_stdout(io.StringIO()):
        module = runpy.run_path(str(ROOT / "examples" /
                                    "shallow_water_closure.py"), run_name="q")
        w = module["main"]()["waves"]
    assert (w["group"], w["within_flat"], w["within_wind"]) == (13, 0, 1)
    flat = lambda name: " ".join((ROOT / name).read_text().split())  # noqa
    ratio = f"{w['ratio'][0]:.3f} to {w['ratio'][1]:.3f} times"
    for name in ("OPEN_QUESTIONS.md", "DATA.md"):
        assert ratio in flat(name), name
    assert f"waves moving the rrs by {ratio}" in \
        flat("DECISIONS.md").split("## 140. ")[1]
    assert "in 1 of the group's 13 runs with waves" in \
        flat("DECISIONS.md")
    assert "bring 1 of the black-bottom group's 13 runs" in \
        flat("CHANGELOG.md")
    assert "`monte_carlo_light_field`: 1 of the 13" in \
        flat("examples/README.md")


@source_tree
def test_a_stored_waves_run_is_reproduced():
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import monte_carlo_check as check
    finally:
        sys.path.pop(0)
    path = ROOT / "examples" / "data" / "monte_carlo" / \
        "waves_black_bottom.csv"
    with path.open() as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 13
    row = rows[0]
    station = jerlov.petzold_scattering("NUC 2240")
    value, error = check.run(row | {"albedo": "0.0"}, station,
                             float(row["wind_m_s"]))
    assert f"{value:.6e}" == row["wind"]
    assert f"{error:.2e}" == row["wind_se"]


# -- Mobley et al. (1993), DECISIONS.md section 140 --------------------------

def _benchmark_tool():
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import mobley1993_benchmark as tool
    finally:
        sys.path.pop(0)
    return tool


@source_tree
def test_table_2_s_misprint_and_its_replacement():
    tool = _benchmark_tool()
    angles = np.array([a for a, _ in tool.TABLE2])
    printed = np.array([v for _, v in tool.TABLE2])
    assert len(angles) == 55
    k = int(np.flatnonzero(angles == tool.TABLE2_MISPRINT)[0])
    assert printed[k] == 2.18839e2
    used = tool.table2()["values"][k]
    assert used == pytest.approx(1.9973e2, rel=1e-4)
    assert printed[k] / used == pytest.approx(1.0957, rel=1e-3)
    data = " ".join((ROOT / "DATA.md").read_text().split())
    section = data.split("## 53. ")[1]
    assert "2.18839+2" in section and "1.9973+2" in section
    # every other value stands in one ratio to the Web Book's (section 136's
    # average particle, built from three of Petzold's stations, agrees with
    # that table within 0.43 percent; here the shipped stations stand in)
    mc_tool = _tool_module("shallow_rrs_mc")
    built_angles, built = mc_tool.average_particle_table()
    ratio = np.delete(printed, k) / np.delete(built, k)
    assert ratio.max() / ratio.min() < 1.01
    assert printed[k] / built[k] / np.median(ratio) > 1.08


def _tool_module(name):
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        return __import__(name)
    finally:
        sys.path.pop(0)


@source_tree
def test_the_phase_functions_of_the_problems_are_normalised():
    tool = _benchmark_tool()
    for table in (tool.rayleigh(), tool.table2()):
        theta = table["angles"]
        y = table["per_sr"] * 2 * np.pi * np.sin(theta)
        assert _trapezoid(y, theta) == pytest.approx(1.0, abs=2e-3)


@source_tree
def test_the_canonical_problems_are_quoted_as_run():
    tool = _benchmark_tool()
    path = ROOT / "examples" / "data" / "mobley1993" / "runs.csv"
    with path.open() as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 51
    good = []
    for r in rows:
        means, spreads = tool.TABLE5[(int(r["problem"]),
                                      float(r["omega0"]))][int(r["tau"])]
        q = ("Ed", "Eou", "Lu").index(r["quantity"])
        assert float(r["table5"]) == pytest.approx(means[q], rel=1e-9)
        x, se = float(r["jerlov"]), float(r["jerlov_se"])
        m, s = means[q], spreads[q] * means[q]
        good.append(abs(x - m) <= 2 * s + 3 * se + 0.005 * m)
    assert sum(good) == 46 and sum(good) >= 0.9 * len(rows)
    misses = {(r["problem"], r["omega0"], r["tau"], r["quantity"])
              for r, g in zip(rows, good) if not g}
    assert misses == {("1", "0.2", "10", "Lu"), ("2", "0.2", "10", "Lu"),
                      ("5", "0.9", "1", "Ed"), ("5", "0.9", "5", "Ed"),
                      ("5", "0.9", "10", "Ed")}
    decisions = " ".join((ROOT / "DECISIONS.md").read_text().split())
    section = decisions.split("## 140. ")[1]
    assert "46 of the 51 entries posed agree** (90.2 percent" in section
    ratio = {key: float(r["jerlov"]) / float(r["table5"])
             for r in rows for key in [(r["problem"], r["tau"],
                                        r["quantity"], r["omega0"])]}
    assert (f"{ratio['1', '10', 'Lu', '0.2']:.3f} and "
            f"{ratio['2', '10', 'Lu', '0.2']:.3f} of the mean") in section
    assert (f"{ratio['5', '1', 'Ed', '0.9']:.3f}, "
            f"{ratio['5', '5', 'Ed', '0.9']:.3f} and "
            f"{ratio['5', '10', 'Ed', '0.9']:.3f} of the mean") in section
    log = " ".join((ROOT / "CHANGELOG.md").read_text().split())
    assert "46 of 51 values agree" in log
    data = " ".join((ROOT / "DATA.md").read_text().split())
    assert "agrees in 46 of 51 entries" in data
    assert (f"{ratio['5', '1', 'Ed', '0.9']:.3f} to "
            f"{ratio['5', '10', 'Ed', '0.9']:.3f} of the mean") in data


# -- light meeting the wavy surface more than once (DECISIONS.md section 141)

def test_surface_facets_left_out_with_a_wind_is_one_with_a_future_warning():
    import warnings
    with pytest.warns(FutureWarning, match="surface_facets") as caught:
        old = _call(wind=5.0)
    # both warnings point at the caller's line, not into the package
    assert caught[0].filename == __file__
    with pytest.warns(FutureWarning, match="wind") as caught:
        jerlov.monte_carlo_light_field(
            0.1, 0.3, 500.0, pure_water_b=0.003, salinity_psu=35.0,
            phase_function=jerlov.mobley2002_fournier_forand(0.0183),
            cut_deg=1.0, refractive_index=1.34, sun_zenith_deg=30.0,
            depth_m=math.inf, bottom_albedo=None, depths_m=[1.0],
            slab_m=1.0, zenith_step_deg=10.0, azimuth_step_deg=45.0,
            photons=100, batches=2, seed=0)
    assert caught[0].filename == __file__
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        one = _call(wind=5.0, surface_facets="one")
        flat = _call(wind="flat")
        also_flat = _call(wind="flat", surface_facets=None)
    assert old == one
    assert one.inputs["surface_facets"] == "one"
    assert flat == also_flat and flat.inputs["surface_facets"] is None
    assert any("light meeting a second facet" in s for s in one.left_out)
    every = _call(wind=5.0, surface_facets="all")
    assert every.inputs["surface_facets"] == "all"
    assert any("drawn independently" in s for s in every.left_out)
    assert not any("second facet" in s for s in every.left_out)


@pytest.mark.parametrize("wind, bad", [
    ("flat", "one"), ("flat", "all"), (5.0, None), (5.0, "two"),
    (5.0, True), (5.0, 1)])
def test_a_bad_surface_facets_is_refused(wind, bad):
    with pytest.raises((ValueError, TypeError)):
        _call(wind=wind, surface_facets=bad)


def test_light_followed_over_the_facets_is_light_kept():
    """Every branch at every facet: what stays in the water and what goes
    to the air add to what arrived, in the mean over the facets."""
    rng = np.random.default_rng(3)
    s2 = mc.COX_MUNK_MEAN_SQUARE_SLOPE[0] \
        + mc.COX_MUNK_MEAN_SQUARE_SLOPE[1] * 7.0
    for from_air, mu in ((True, math.cos(math.radians(60.0))),
                         (False, -math.cos(math.radians(40.0)))):
        n = 200_000
        d = np.tile([[math.sqrt(1 - mu * mu)], [0.0], [mu]], n)
        out, stay, gone, second = mc._follow_surface(
            d, np.full(n, from_air), s2, 1.34, rng)
        assert np.all(out[2] > 0)        # what stays travels down
        assert np.all((stay >= 0) & (gone >= 0) & (second >= 0))
        total = float(np.mean(stay + gone))
        assert total == pytest.approx(1.0, abs=0.01)


def test_all_facets_and_one_differ_only_where_light_meets_another():
    """At the sun at 30 degrees no facet sends sunlight back towards the
    sea, so what enters is the same; at 80 degrees more enters."""
    one, every = (_transparent(30.0, 7.0, 20_000, f) for f in ("one", "all"))
    assert every.transmitted_at_surface == pytest.approx(
        one.transmitted_at_surface, rel=1e-3)
    one, every = (_transparent(80.0, 7.0, 20_000, f) for f in ("one", "all"))
    ratio = every.transmitted_at_surface / one.transmitted_at_surface
    assert 1.02 < ratio < 1.04      # "about 3 percent", the docstring


def _section_141():
    decisions = " ".join((ROOT / "DECISIONS.md").read_text().split())
    return decisions.split("## 141. ")[1]


@source_tree
def test_section_141_s_energy_figures_are_quoted_as_computed():
    section = _section_141()
    total, entering = {}, {}
    for w in (7.0, 14.0):
        for s in (30.0, 60.0, 80.0):
            for f in ("one", "all"):
                r = _transparent(s, w, surface_facets=f)
                total[w, s, f] = 100 * (r.transmitted_at_surface
                                        + r.reflected_at_surface - 1)
                entering[w, s, f] = r.transmitted_at_surface

    def pair(w, s):
        return total[w, s, "all"], total[w, s, "one"]
    assert ("at 7 m/s {:+.3f} percent at 30 degrees ({:+.3f}), {:+.3f} at 60 "
            "({:+.3f}), {:+.3f} at 80 ({:+.3f})").format(
        *pair(7.0, 30.0), *pair(7.0, 60.0), *pair(7.0, 80.0)) in section
    assert ("14 m/s {:+.3f} ({:+.3f}), {:+.3f} ({:+.3f}), and {:+.3f} at 80 "
            "({:+.3f}), above the 0.5 set").format(
        *pair(14.0, 30.0), *pair(14.0, 60.0), *pair(14.0, 80.0)) in section
    met = [abs(total[w, s, "all"]) <= 0.5 for w in (7.0, 14.0)
           for s in (30.0, 60.0, 80.0)]
    assert met.count(False) == 1 and not met[-1]
    ratio = {k: entering[k[0], k[1], "all"] / entering[k[0], k[1], "one"]
             for k in [(7.0, 80.0), (14.0, 80.0), (7.0, 60.0), (14.0, 60.0),
                       (7.0, 30.0), (14.0, 30.0)]}
    assert (f"{ratio[7.0, 80.0]:.4f} and {ratio[14.0, 80.0]:.4f} times "
            f"`\"one\"`'s at 80 degrees and 7 and 14 m/s, "
            f"{ratio[7.0, 60.0]:.4f} and {ratio[14.0, 60.0]:.4f} at 60") \
        in section
    assert abs(ratio[7.0, 30.0] - 1) < 2e-4 and abs(ratio[14.0, 30.0] - 1) < 2e-4


def _share_by_quadrature(mu, slope_variance, points):
    sd = math.sqrt(slope_variance / 2)
    g = np.linspace(-8 * sd, 8 * sd, points)
    zx, zy = np.meshgrid(g, g)
    p = np.exp(-(zx * zx + zy * zy) / (2 * sd * sd))
    norm = np.sqrt(1 + zx * zx + zy * zy)
    nx, nz = zx / norm, -1 / norm
    dn = math.sqrt(1 - mu * mu) * nx + mu * nz
    front = dn < 0
    return float(np.sum(p * front * (-dn) / (-nz * mu)) / np.sum(p * front))


@source_tree
def test_section_141_s_finding_on_the_shadowing_table():
    section = _section_141()
    mu = math.cos(math.radians(80.0))
    d = np.tile([[math.sqrt(1 - mu * mu)], [0.0], [mu]], 500_000)
    means, table, here, fine = [], [], [], []
    for wind in (7.0, 14.0):
        s2 = mc.COX_MUNK_MEAN_SQUARE_SLOPE[0] \
            + mc.COX_MUNK_MEAN_SQUARE_SLOPE[1] * wind
        m = np.array([float(np.mean(mc._facets(
            d, s2, np.random.default_rng(100 + k))[2])) for k in range(8)])
        means.append((100 * (m.mean() - 1),
                      100 * m.std(ddof=1) / math.sqrt(8)))
        mus, share = mc._front_share_table(s2)
        table.append(float(np.interp(mu, mus, share)))
        here.append(_share_by_quadrature(mu, s2, 401))
        fine.append(_share_by_quadrature(mu, s2, 1601))
    assert (f"1 - {-means[0][0]:.3f} percent at 7 m/s and 1 + "
            f"{means[1][0]:.3f} percent at 14 m/s") in section
    assert max(se for _, se in means) < 0.05
    log = " ".join((ROOT / "CHANGELOG.md").read_text().split())
    log = log.split("## 1.35.0 ")[1].split("## 1.34.1 ")[0]
    assert (f"{-means[0][0]:.2f} percent short of what falls on it at 7 m/s "
            f"and {means[1][0]:.2f} percent over at 14 m/s") in log
    assert (f"gives {table[0]:.4f} and {table[1]:.4f} at cos(80 degrees); "
            f"the same quadrature at that cosine itself gives {here[0]:.4f} "
            f"and {here[1]:.4f}, and on a grid four times finer "
            f"{fine[0]:.4f} and {fine[1]:.4f}") in section
    # the sampled mean is the finer quadrature's over the table's
    for (m, se), t, f in zip(means, table, fine):
        assert abs(100 * (f / t - 1) - m) < 4 * se + 0.05
    for wind in (2.0, 5.0, 7.0, 14.0):
        s2 = mc.COX_MUNK_MEAN_SQUARE_SLOPE[0] \
            + mc.COX_MUNK_MEAN_SQUARE_SLOPE[1] * wind
        mus, share = mc._front_share_table(s2)
        for deg in np.arange(0.0, 60.01, 2.5):
            c = math.cos(math.radians(deg))
            assert abs(float(np.interp(c, mus, share))
                       / _share_by_quadrature(c, s2, 1601) - 1) < 1e-4
    assert "within 0.01 percent of the finer grid" in section


def _rows(name):
    path = ROOT / "examples" / "data" / "mobley1993" / name
    with path.open() as handle:
        return list(csv.DictReader(handle))


@source_tree
def test_problem_5_with_every_facet_is_quoted_as_run():
    tool = _benchmark_tool()
    one, every = _rows("runs.csv"), _rows("runs_all_facets.csv")
    assert len(every) == 51
    for a, b in zip(one, every):
        assert [a[k] for k in ("problem", "omega0", "tau", "quantity")] == \
            [b[k] for k in ("problem", "omega0", "tau", "quantity")]
        if a["problem"] != "5":
            assert a == b

    def agree(r):
        means, spreads = tool.TABLE5[(int(r["problem"]),
                                      float(r["omega0"]))][int(r["tau"])]
        q = ("Ed", "Eou", "Lu").index(r["quantity"])
        x, se = float(r["jerlov"]), float(r["jerlov_se"])
        m, s = means[q], spreads[q] * means[q]
        return abs(x - m) <= 2 * s + 3 * se + 0.005 * m
    assert sum(map(agree, every)) == 49
    assert all(agree(r) for r in every if r["problem"] == "5")
    assert {(r["problem"], r["omega0"], r["tau"], r["quantity"])
            for r in every if not agree(r)} == {("1", "0.2", "10", "Lu"),
                                               ("2", "0.2", "10", "Lu")}
    section = _section_141()

    def ratios(rows, quantity):
        return [float(r["jerlov"]) / float(r["table5"]) for r in rows
                if r["problem"] == "5" and r["quantity"] == quantity]
    for q in ("Ed", "Eou", "Lu"):
        a, b = ratios(every, q), ratios(one, q)
        assert (f"{q} {a[0]:.3f}, {a[1]:.3f} and {a[2]:.3f}"
                f"{' of the models' if q == 'Ed' else ''}") in section \
            or (f"{q} is {a[0]:.3f}, {a[1]:.3f} and {a[2]:.3f}") in section
        assert (f"{b[0]:.3f}, {b[1]:.3f}" in section)
    assert "49 of the 51 entries agree" in section
    ed, ed_one = ratios(every, "Ed"), ratios(one, "Ed")
    log = " ".join((ROOT / "CHANGELOG.md").read_text().split())
    log = log.split("## 1.35.0 ")[1].split("## 1.34.1 ")[0]
    assert (f"Ed is {min(ed):.3f} to {max(ed):.3f} of the 1993 codes' mean, "
            f"where one facet gave {min(ed_one):.3f} to {max(ed_one):.3f}") \
        in log
    assert "in 49 of 51 values" in log
    data = " ".join((ROOT / "DATA.md").read_text().split())
    assert (f"Ed {ed[0]:.3f}, {ed[1]:.3f} and {ed[2]:.3f} of the mean") in data
    assert "agrees in 49 of 51 entries" in data


@source_tree
def test_the_second_facet_shares_are_quoted_as_computed():
    tool = _benchmark_tool()
    ray, table = tool.rayleigh(), tool.table2()
    section = _section_141()
    entering, below = [], []
    for sun in (30.0, 60.0, 80.0):
        runs = [mc._simulate(0.1, 0.9, 0.0, table, ray, sun, 141 + k,
                             photons=100_000, depths=np.array([1.0]),
                             half_slab=0.1, n_water=1.34, d_zenith=5.0,
                             d_azimuth=45.0, slope_variance=0.04,
                             surface_facets="all") for k in range(4)]
        entering.append(np.mean([r["second_facet_entering"] for r in runs]))
        below.append(np.mean([r["second_facet_below"] for r in runs]))
    assert entering[0] == 0.0
    assert (f"none at 30 degrees, {entering[1]:.4f} at 60 and "
            f"{entering[2]:.4f} at 80") in section
    assert f"{below[0]:.4f}, {below[1]:.4f} and {below[2]:.4f}" in section


@source_tree
def test_question_5_with_every_facet_is_quoted_as_computed():
    path = ROOT / "examples" / "data" / "monte_carlo" / \
        "waves_black_bottom.csv"
    with path.open() as handle:
        rows = list(csv.DictReader(handle))
    model = np.array([float(r["model"]) for r in rows])
    one = np.array([float(r["wind"]) for r in rows])
    every = np.array([float(r["all_facets"]) for r in rows])
    z = [(float(r["all_facets"]) - float(r["wind"]))
         / math.hypot(float(r["wind_se"]), float(r["all_facets_se"]))
         for r in rows]
    within = int(np.sum(np.abs(model / every - 1) <= 0.1))
    assert within == int(np.sum(np.abs(model / one - 1) <= 0.1)) == 1
    section = _section_141()
    assert f"within 10 percent in {within} of the 13" in section
    log = " ".join((ROOT / "CHANGELOG.md").read_text().split())
    assert f"still {within} of the 13 within 10 percent" in log
    ratio = every / one
    assert (f"is {ratio.min():.3f} to {ratio.max():.3f}, each within "
            f"{math.ceil(10 * max(map(abs, z))) / 10:.1f} combined standard "
            "errors of 1") in section


@source_tree
def test_a_stored_every_facet_waves_run_is_reproduced():
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import monte_carlo_check as check
    finally:
        sys.path.pop(0)
    path = ROOT / "examples" / "data" / "monte_carlo" / \
        "waves_black_bottom.csv"
    with path.open() as handle:
        row = next(csv.DictReader(handle))
    station = jerlov.petzold_scattering("NUC 2240")
    value, error = check.run(row | {"albedo": "0.0"}, station,
                             float(row["wind_m_s"]), "all")
    assert f"{value:.6e}" == row["all_facets"]
    assert f"{error:.2e}" == row["all_facets_se"]

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
        batches=2, seed=0)
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
    assert d["inputs"]["seed"] == 0 and d["method"].endswith("section 138")
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
        azimuth_step_deg=45.0, photons=100, batches=2, seed=0)
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

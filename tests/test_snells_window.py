"""examples/snells_window.py (DECISIONS.md section 123): the geometry
checked against identities, and every figure the documents quote checked
against the example's own output."""

from __future__ import annotations

import contextlib
import io
import pathlib
import runpy

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "examples" / "snells_window.py"
pytestmark = pytest.mark.skipif(not EXAMPLE.exists(),
                                reason="not running from a source tree")


@pytest.fixture(scope="module")
def module():
    return runpy.run_path(str(EXAMPLE), run_name="snells_window")


@pytest.fixture(scope="module")
def result(module):
    with contextlib.redirect_stdout(io.StringIO()):
        return module["main"]()


def _flat(name):
    return " ".join((ROOT / name).read_text().split())


def test_fresnel_at_normal_incidence_and_beyond_the_critical_angle(module):
    fresnel = module["fresnel"]
    assert fresnel(1.0, 1.0, 1.333) == pytest.approx(0.02, abs=0.001)
    # Both ways through the surface at normal incidence reflect the same.
    assert fresnel(1.0, 1.333, 1.0) == pytest.approx(fresnel(1.0, 1.0, 1.333))
    c = np.radians(module["critical_deg"](1.34))
    assert fresnel(np.cos(c + 1e-4), 1.34, 1.0) == 1.0
    assert fresnel(np.cos(c - 1e-2), 1.34, 1.0) < 1.0


def test_the_horizon_is_seen_at_the_window_s_edge(module, result):
    seen = result["squeeze"]["seen"]
    elevations = module["ELEVATIONS"]
    assert seen[list(elevations).index(0)] == pytest.approx(
        module["critical_deg"](module["N_WATER"]))
    assert seen[list(elevations).index(90)] == pytest.approx(0.0)
    assert np.all(np.diff(seen) < 0)


def test_the_window_s_brightness_is_n_squared_times_the_transmittance(
        module, result):
    n = module["N_WATER"]
    assert result["bright"]["centre"] == pytest.approx(
        n ** 2 * (1 - module["fresnel"](1.0, 1.0, n)))


def test_the_measured_part_follows_the_plan(module, result):
    m = result["measured"]
    rows = m["rows"]
    assert {r["azimuth"] for r in rows} == {100.0, 120.0, 140.0, 160.0, 180.0}
    assert m["edge"][0] < 50 and m["edge"][1] > 40   # the edge is in 40-50
    for r in rows:
        assert r["seen"] == (r["steepest"] == 40.0)
        assert r["ratio"] >= r["at_edge"]


def test_examples_readme_quotes_the_example(result):
    text = _flat("examples/README.md").split("**`snells_window.py`**")[1]
    text = text.split("**`")[0]
    size, sq, br = result["size"], result["squeeze"], result["bright"]
    m = result["measured"]
    assert f"half-angle **{size[1.34]:.1f}** degrees at n = 1.34" in text
    assert f"({size[1.35]:.1f} to {size[1.33]:.1f} from 1.33 to 1.35)" in text
    assert (f"lowest {sq['low']} degrees of sky crowd within its outer "
            f"**{sq['outer']:.1f}** degrees") in text
    assert f"**{br['centre']:.2f}** times as bright" in text
    assert f"half as bright {br['rim_width']:.1f} degrees inside its rim" in text
    assert f"{result['footprint']['factor']:.3f} times the eye's depth" in text
    c = m["counts"]
    assert c[4.24] == c[29.0] == 3 and (c[10.4], c[16.6]) == (1, 2)
    assert f"at {c[4.24]} of {m['n_az']} azimuths" in text
    assert (f"at {c[10.4]} and {c[16.6]} at 10.4 and 16.6 m, and at none "
            f"from {min(m['none']):g} m down") in text
    assert max(m["seen_at"]) < min(m["none"])


def test_decisions_and_changelog_quote_the_example(result):
    m = result["measured"]
    decisions = _flat("DECISIONS.md").split("## 123. ")[1]
    log = _flat("CHANGELOG.md").split("## 1.26.10")[1].split("## 1.26.9")[0]
    counts = ", ".join(f"{k} at {d:g} m" for d, k in m["counts"].items() if k)
    assert counts in decisions
    others = sum(1 for r in m["rows"] if not r["seen"])
    assert f"At the other {others} the steepest step" in decisions
    assert f"{result['size'][1.34]:.1f} degrees" in log

"""Why Jerlov's Kd lies below pure water's absorption: DECISIONS.md section
130, OPEN_QUESTIONS.md question 7, DATA.md section 3. Every figure the
documents quote is recomputed here from the example's own results."""

from __future__ import annotations

import contextlib
import io
import pathlib
import re
import runpy

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.skipif(
    not (ROOT / "pyproject.toml").exists(),
    reason="not running from a source tree")


@pytest.fixture(scope="module")
def result():
    with contextlib.redirect_stdout(io.StringIO()):
        module = runpy.run_path(
            str(ROOT / "examples" / "jerlov_kd_below_pure_water.py"),
            run_name="jerlov_kd_below_pure_water")
        return module["main"]()


def _flat(name):
    return " ".join(re.sub(r"^> ?", "", (ROOT / name).read_text(),
                           flags=re.M).split())


def _q7():
    text = _flat("OPEN_QUESTIONS.md")
    return text[text.index("## 7."):]


def test_where_and_how_much(result):
    below = result["where"]["below"]
    least = result["where"]["least"]
    q7 = _q7()
    sb68 = below[("smith1981", "jerlov1968", "I")]
    sb76 = below[("smith1981", "jerlov1976", "I")]
    assert len(sb68) == len(sb76) == 7
    assert "at 7 of the 13 printed wavelengths in both editions" in q7
    w68, r68 = least[("smith1981", "jerlov1968")]
    w76, r76 = least[("smith1981", "jerlov1976")]
    assert (f"least {r68:.3f} of it at {w68:.0f} nm in 1968 and {r76:.3f} at "
            f"{w76:.0f} nm in 1976") in q7
    pf68 = below[("pope1997", "jerlov1968", "I")]
    pf76 = below[("pope1997", "jerlov1976", "I")]
    assert (len(pf68), sorted(pf76)) == (4, [675.0, 700.0])
    p68 = least[("pope1997", "jerlov1968")][1]
    p76 = least[("pope1997", "jerlov1976")][1]
    assert f"least {p68:.3f} and {p76:.3f}" in q7
    # The 1976 revision at 600 nm removed the largest deficit.
    assert 600.0 in sb68 and sb68[600.0] == min(sb68.values())
    assert 600.0 not in pf76


def test_rounding_cannot_do_it(result):
    r = result["rounding"]
    q7 = _q7()
    assert (f"at most {100 * r['worst76']:.1f} percent from 600 to 700 nm in "
            f"1976") in q7
    assert f"{100 * r['worst68']:.1f} percent in 1968" in q7
    assert max(r["worst76"], r["worst68"]) < 0.04


def test_what_a_broad_filter_does(result):
    table = result["filters"]["table"]
    q7 = _q7()
    sb700 = table[("smith1981", 700.0)]
    figures = ", ".join(f"{sb700[w]:.3f}" for w in (10.0, 20.0, 40.0))
    assert f"is {figures} and {sb700[60.0]:.3f} of its absorption at 700 nm" \
        in q7
    sb600 = table[("smith1981", 600.0)]
    assert f"and {sb600[10.0]:.3f} to {sb600[60.0]:.3f} at 600 nm" in q7
    narrow = [row[2.0] for row in table.values()]
    assert 0.006 < max(abs(x - 1) for x in narrow) <= 0.007
    assert "through 2 nm, within 0.7 percent" in q7


def test_which_deficits_a_filter_reaches(result):
    reach = result["filters"]["reach"]
    q7 = _q7()
    assert reach[("smith1981", "jerlov1976", 700.0)][1] == 40.0
    assert reach[("smith1981", "jerlov1976", 600.0)][1] == 10.0
    assert "A 40 nm filter reaches the 1976 deficit at 700 nm, and 10 nm the " \
           "one at 600 nm" in q7
    for edition in ("jerlov1968", "jerlov1976"):
        assert reach[("smith1981", edition, 675.0)][1] is None
        assert reach[("pope1997", edition, 675.0)][1] is None
    assert reach[("smith1981", "jerlov1968", 600.0)][1] is None
    assert reach[("pope1997", "jerlov1968", 600.0)][1] == 60.0
    assert "with Pope & Fry's, 60 nm does" in q7
    # Pope & Fry's table ends at 727.5 nm: no 60 nm filter at 675 nm.
    assert result["filters"]["table"][("pope1997", 675.0)][60.0] is None
    assert result["filters"]["table"][("pope1997", 675.0)][40.0] is not None


def test_the_other_documents_quote_the_same(result):
    least = result["where"]["least"]
    r68 = least[("smith1981", "jerlov1968")][1]
    r76 = least[("smith1981", "jerlov1976")][1]
    site = _flat("docs/open_questions.rst")
    assert (f"as low as {r68:.3f} of it at 600 nm in 1968 and {r76:.3f} at "
            "700 nm in 1976") in site
    table = result["filters"]["table"]
    readme = _flat("examples/README.md")
    assert f"**{table[('smith1981', 700.0)][40.0]:.3f}**" in readme


def test_the_quotations_are_the_papers(result):
    """Each quotation is checked against the paper's text layer where it
    was read (DECISIONS.md section 130); here, that the example and
    OPEN_QUESTIONS.md quote the same words."""
    q7 = _q7()
    for phrase in (
            "along with excessive filter bandwidths in irradiance "
            "measurements accounts for observations of anomalous diffuse "
            "attenuation coefficients",
            "relatively little effect on K",
            "at most ~20%",
            "real filters have longer tails than predicted by the Gaussian",
            "most data result from sporadic observations with one to three "
            "colour filters having a broad band width"):
        assert phrase in q7, phrase
    printed = " ".join(text for _, text in
                       runpy.run_path(str(ROOT / "examples" /
                                          "jerlov_kd_below_pure_water.py"),
                                      run_name="q")["QUOTES"])
    for phrase in ("excessive filter bandwidths", "relatively little effect",
                   "at most ~20%", "longer tails"):
        assert phrase in printed


def test_only_the_suspect_smith_and_baker_value_warns(result):
    assert result["caught"] == [
        "Smith & Baker (1981), Appl. Opt. 20, 177-184, Table I: suspect at "
        "710 nm"]


# -- Raman scattering by Marshall & Smith's model (DECISIONS.md section 131) --

def test_the_papers_own_case_at_589_nm(result):
    # B = 4 Ed(589, 0) / (b_r E0(491, 0)), about 1.3e4 in the paper (p. 77).
    assert 1.2e4 < result["raman"]["check_b"] < 1.45e4
    assert "B = 1.38e4 here, about 1.3e4 there" in _q7()
    assert f"{result['raman']['check_b']:.3g}" == "1.38e+04"


def test_raman_light_is_small_over_ten_metres(result):
    r = result["raman"]
    q7 = _q7()
    assert f"by at most {100 * (1 - r['worst']):.2f} percent at 675 and 700 nm" \
        in q7
    assert 1 - r["worst"] < 0.01                     # the plan's criterion
    lo, hi = r["deficits"]
    assert f"deficits are {100 * lo:.1f} to {100 * hi:.1f} percent" in q7
    changelog = " ".join((ROOT / "CHANGELOG.md").read_text().split())
    assert f"at most {100 * (1 - r['worst']):.2f} percent" in changelog
    assert f"{100 * lo:.1f} to {100 * hi:.1f} percent in either edition" \
        in changelog
    for name in ("docs/open_questions.rst", "examples/README.md"):
        assert f"{100 * (1 - r['worst']):.2f}" in _flat(name), name


def test_raman_light_grows_with_depth(result):
    row = result["raman"]["rows"][("smith1981", 700.0)]
    q7 = _q7()
    assert (f"over 0-20 m it lowers Kd at 700 nm by {100 * (1 - row['to20']):.1f} "
            f"percent, and over 0-30 m by {100 * (1 - row['to30']):.1f} "
            "percent") in q7
    changelog = " ".join((ROOT / "CHANGELOG.md").read_text().split())
    assert (f"to {100 * (1 - row['to20']):.1f} percent over 0-20 m and "
            f"{100 * (1 - row['to30']):.1f} percent over 0-30 m") in changelog
    for (source, centre), r in result["raman"]["rows"].items():
        assert r["to30"] < r["to20"] < r["base"] < 1, (source, centre)


def test_the_exciting_wavelengths_follow_the_shift(result):
    rows = result["raman"]["rows"]
    got = {c: round(rows[("smith1981", c)]["exciting"], 1)
           for c in (600.0, 675.0, 700.0)}
    assert got == {600.0: 498.3, 675.0: 549.0, 700.0: 565.4}
    assert "excited at 549 and 565 nm" in _q7()

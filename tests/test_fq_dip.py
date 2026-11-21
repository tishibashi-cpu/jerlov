"""The dip at a sun of 45 degrees in Morel et al.'s (2002) archive:
DECISIONS.md section 116, OPEN_QUESTIONS.md question 6, DATA.md section
48. Everything that reads the archive is skipped where the user's copy is
not at sources/morel2002/ (in CI too), as tests/test_fq_tables.py is."""

from __future__ import annotations

import contextlib
import io
import pathlib
import runpy
import warnings

import pytest

import jerlov

ROOT = pathlib.Path(__file__).resolve().parent.parent
REAL = ROOT / "sources" / "morel2002" / "DISTRIB_fQ_with_Raman.tar.gz"
EXAMPLE = ROOT / "examples" / "fq_at_45_degrees.py"
needs_archive = pytest.mark.skipif(
    not REAL.exists() or not EXAMPLE.exists(),
    reason="needs the user's own copy of the archive and the source tree")
source_tree = pytest.mark.skipif(not EXAMPLE.exists(),
                                 reason="not running from a source tree")


def _flat(name):
    return " ".join((ROOT / name).read_text().split())


@pytest.fixture(scope="module")
def tables():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        return jerlov.morel2002_fq_tables(REAL)


@pytest.fixture(scope="module")
def result():
    module = runpy.run_path(str(EXAMPLE), run_name="fq_at_45_degrees")
    with contextlib.redirect_stdout(io.StringIO()):
        return module["main"](str(REAL))


@source_tree
def test_without_the_archive_the_example_only_says_so():
    module = runpy.run_path(str(EXAMPLE), run_name="fq_at_45_degrees")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        assert module["main"](None) is None
    assert "--archive PATH" in out.getvalue()


@needs_archive
def test_the_suspect_run_warns_and_no_other_does(tables):
    for wl in tables.wavelengths_nm:
        for sun in tables.sun_zenith_deg:
            for chl in tables.chlorophyll_mg_m3:
                suspect = (sun, chl) == (45.0, 0.03)
                with warnings.catch_warnings(record=True) as seen:
                    warnings.simplefilter("always")
                    tables.f(wl, sun_zenith_deg=sun, chlorophyll_mg_m3=chl)
                    tables.f_over_q(wl, sun_zenith_deg=sun,
                                    chlorophyll_mg_m3=chl, nadir_deg=0,
                                    azimuth_deg=90)
                caught = [w for w in seen
                          if issubclass(w.category, jerlov.ProvenanceWarning)]
                assert len(caught) == (2 if suspect else 0), (wl, sun, chl)
                for w in caught:
                    assert w.filename == __file__
                    assert "DATA.md section 48" in str(w.message)


@needs_archive
def test_the_suspect_values_are_returned_as_the_archive_has_them(tables):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
        assert tables.f(660.0, sun_zenith_deg=45.0,
                        chlorophyll_mg_m3=0.03) == 0.403971   # f.dat
        assert tables.f_over_q(660.0, sun_zenith_deg=45.0,
                               chlorophyll_mg_m3=0.03, nadir_deg=0,
                               azimuth_deg=0) == 0.1134     # D_foQ_pa


@needs_archive
def test_the_dip_is_one_run_as_the_documents_say(result):
    w, n = result["where"], result["neighbours"]
    assert w["dip_columns"] == [0.03]
    assert w["growing"] and w["alone_at_30"]
    assert n["pairs"] == [(0.03, 0.1, 45.0)] and n["count"] == 7
    low, high = -w["dip_range"][1], -w["dip_range"][0]
    dip = f"by {low:.2f} to {high:.2f} percent"
    others = f"{w['others'][0]:.2f} to {w['others'][1]:.2f}"
    assert w["others"][0] > 0
    med = w["foq_median_at_dip"]
    med_o = w["foq_median_others"]
    data = _flat("DATA.md").split("## 48. ")[1].split("## 49. ")[0]
    oq = _flat("OPEN_QUESTIONS.md").split("## 6. ")[1]
    assert f"seven wavelengths, {dip}" in data
    assert f"7 wavelengths, {dip}" in oq
    for text in (data, oq):
        assert f"{others} percent above it" in text
    assert (f"the 221 directions, {med[0]:+.2f} to {med[1]:+.2f} percent from "
            f"its chord, the other Chl {med_o[0]:+.2f} to {med_o[1]:+.2f}"
            ).replace("+", "") in data.replace("+", "")
    assert (f"median over the 221 directions {med[0]:+.2f} to {med[1]:+.2f} "
            f"percent from the chord, the other Chl {med_o[0]:+.2f} to "
            f"{med_o[1]:+.2f}").replace("+", "") in oq.replace("+", "")
    ex = n["example"]
    assert (f"{ex[2]:.4f} at 30, {ex[3]:.4f} at 45 and {ex[4]:.4f} at 60"
            ) in oq
    assert ex[3] < ex[4] < ex[2]
    for name in ("docs/open_questions.rst", "examples/README.md"):
        text = _flat(name).replace("**", "")
        assert f"by {low:.2f} to {high:.2f} percent" in text, name
    log = _flat("CHANGELOG.md").split("## 1.26.3")[1].split("## 1.26.2")[0]
    assert f"by {low:.2f} to {high:.2f} percent" in log
    source = (ROOT / "jerlov" / "fq_tables.py").read_text()
    assert f"(by {low:.1f} to {high:.1f} " in source

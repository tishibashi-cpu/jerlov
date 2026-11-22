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


# -- DECISIONS.md section 117: the authors' later tables, via NASA's OCSSW --

OCSSW = ROOT / "sources" / "ocssw"
try:
    import h5py  # noqa: F401  (only for these tests; not a dependency)
    _H5PY = True
except ImportError:
    _H5PY = False
needs_ocssw = pytest.mark.skipif(
    not (_H5PY and REAL.exists() and EXAMPLE.exists()
         and (OCSSW / "morel_fq.nc").exists()
         and (OCSSW / "morel_fq_hyperspectral_2026.nc").exists()),
    reason="needs h5py, the archive and NASA's OCSSW files in sources/ocssw")


@pytest.fixture(scope="module")
def later():
    module = runpy.run_path(str(EXAMPLE), run_name="fq_at_45_degrees")
    with contextlib.redirect_stdout(io.StringIO()):
        return module["main"](str(REAL), str(OCSSW))["later"]


@needs_ocssw
def test_the_ocssw_files_are_the_ones_recorded():
    import hashlib
    text = _flat("DECISIONS.md").split("## 117. ")[1]
    for name in ("morel_fq.nc", "morel_fq_hyperspectral_2026.nc"):
        digest = hashlib.sha256((OCSSW / name).read_bytes()).hexdigest()
        row = [r for r in text.split("| ") if r.startswith(name)]
        assert row, name
        assert f"{digest[:8]}..." in text.split(name, 1)[1].split("|")[3], name


@needs_ocssw
def test_the_later_tables_are_quoted_as_computed(later):
    assert later["same"] < 1e-6         # morel_fq.nc is the archive
    assert later["red"]
    oq = _flat("OPEN_QUESTIONS.md").split("## 6. ")[1]
    data = _flat("DATA.md").split("## 48. ")[1].split("## 49. ")[0]
    log = _flat("CHANGELOG.md").split("## 1.26.4")[1].split("## 1.26.3")[0]
    own = (f"{later['own_dip'][0]:+.2f} to {later['own_dip'][1]:+.2f} percent "
           "from its chord")
    nxt = f"({later['own_next'][0]:+.2f} to {later['own_next'][1]:+.2f})"
    against = (f"+{later['against'][0]:.2f} to +{later['against'][1]:.2f} "
               "percent")
    rest = (f"{later['against_rest'][0]:+.2f} to "
            f"{later['against_rest'][1]:+.2f}")
    level = f"{later['level'][0]:+.1f} to {later['level'][1]:+.1f} percent"
    assert later["own_next"][0] < later["own_dip"][1] < 0.5
    assert later["against"][0] > 1 and later["against_rest"][1] < 0.1
    for text in (oq, data):
        assert against in text and rest in text, text[:80]
    assert own in oq and nxt.replace("(", "").replace(")", "") in oq
    assert level in oq
    assert (f"lies {later['own_dip'][0]:+.2f} to {later['own_dip'][1]:+.2f} "
            "percent from the chord between 30 and 60") in data
    assert (f"its nadir f/Q lies {later['own_dip'][0]:+.2f} to "
            f"{later['own_dip'][1]:+.2f} percent from the line") in log


# -- DECISIONS.md section 118: the paper's own Fig. 13 --------------------------

PAPER = ROOT / "sources" / "morel2002" / "Morel_Antoine_Gentili_2002_AO.pdf"
FIG13 = ROOT / "examples" / "data" / "fq_at_45_degrees" / "fig13.csv"


def _pdfimages():
    import shutil
    return shutil.which("pdfimages") is not None


@pytest.mark.skipif(not (PAPER.exists() and EXAMPLE.exists() and _pdfimages()),
                    reason="needs the user's copy of the paper and pdfimages")
def test_the_fig13_readings_are_what_the_tool_writes(tmp_path):
    import subprocess
    import sys
    out = tmp_path / "fig13.csv"
    subprocess.run([sys.executable, str(ROOT / "tools" / "read_fig13.py"),
                    str(PAPER), str(out)], check=True)
    assert out.read_text() == FIG13.read_text()


@source_tree
def test_the_fig13_readings_are_well_formed():
    import csv
    with FIG13.open() as f:
        rows = list(csv.DictReader(f))
    assert {float(r["chl_mg_m3"]) for r in rows} == {0.03, 0.1}
    for r in rows:
        assert (float(r["bottom_f0_over_f"]) <= float(r["centre_f0_over_f"])
                <= float(r["top_f0_over_f"]))
    # The 0 degree symbol at 0.1 mg/m3 stands alone and must read 1.
    top = max(rows, key=lambda r: (float(r["chl_mg_m3"]) == 0.1,
                                   float(r["top_f0_over_f"])))
    assert f"{float(top['centre_f0_over_f']):.4f}" == "1.0000"
    assert "reads 1.0000" in _flat("DECISIONS.md").split("## 118. ")[1]


@needs_archive
def test_the_fig13_figures_are_quoted_as_computed(result):
    g = result["figure"]
    assert g["drawn"] == g["total"] == 60
    assert g["off"] == [412.5, 510.0, 560.0, 620.0, 660.0]
    assert g["far_waves"] == [560.0, 620.0, 660.0]
    assert g["far"][0] > 10 * g["accuracy"]
    acc = f"within {g['accuracy']:.4f} of its value"
    far = f"within {g['far'][0]:.4f} to {g['far'][1]:.4f}"
    oq = _flat("OPEN_QUESTIONS.md").split("## 6. ")[1]
    data = _flat("DATA.md").split("## 48. ")[1].split("## 49. ")[0]
    decisions = _flat("DECISIONS.md").split("## 118. ")[1]
    log = _flat("CHANGELOG.md").split("## 1.26.5")[1].split("## 1.26.4")[0]
    for text in (oq, data, decisions, log):
        assert acc in text, text[:60]
        assert far in text, text[:60]
        assert "560, 620 and 660 nm" in text, text[:60]
    for text in (oq, data):
        assert "all 60 of the archive's values" in text
    assert "all 60 of the archive's values" in decisions
    fits = ", ".join(f"{v:.4f}" for v in g["fits"][4:6]) + \
        f" and {g['fits'][6]:.4f}"
    arch = ", ".join(f"{v:.4f}" for v in g["archive45"][4:6]) + \
        f" and {g['archive45'][6]:.4f}"
    assert f"({fits})" in decisions and f"({arch})" in decisions

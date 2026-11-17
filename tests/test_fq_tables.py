"""Morel et al.'s (2002) full f/Q tables, read from the user's copy:
DECISIONS.md section 104, DATA.md section 48."""

import csv
import hashlib
import importlib.resources
import io
import pathlib
import tarfile
import warnings

import numpy as np
import pytest

import jerlov
from jerlov import fq_tables

ROOT = pathlib.Path(__file__).resolve().parent.parent
REAL = ROOT / "sources" / "morel2002" / "DISTRIB_fQ_with_Raman.tar.gz"
NADIR = ("1.078 3.411 6.289 9.278 12.300 15.330 18.370 21.410 24.450 27.500 "
         "30.540 33.590 36.640 39.690 42.730 45.780 48.830")
AZIMUTH = "0 15 30 45 60 75 90 105 120 135 150 165 180"


def _small_archive(tmp_path):
    """An archive of the authors' layout, two cases, made-up numbers."""
    files = {"foQ.info": "\n".join(["x"] * 10 + [NADIR, "x", AZIMUTH]) + "\n",
             "f.dat": "412.5 00 00.03 0.297986\n412.5 15 00.03 0.299979\n",
             "rgoth_Ebuchi.dat": "xx 00 0.528716\n04 48 0.23983\n"}
    for sun, base in (("00", 0.09), ("15", 0.10)):
        rows = [" ".join(f"{base + 0.001 * i + 0.0001 * j:.4f}"
                         for j in range(13)) for i in range(17)]
        files[f"D_foQ_pa/foQ_412.5_{sun}_00.03"] = "\n".join(rows) + "\n"
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, text in files.items():
            data = text.encode("ascii")
            info = tarfile.TarInfo("DISTRIB_fQ_with_Raman/" + name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    path = tmp_path / "small.tar.gz"
    path.write_bytes(buffer.getvalue())
    return path, hashlib.md5(buffer.getvalue()).hexdigest()


def test_reads_the_layout(tmp_path, monkeypatch):
    path, digest = _small_archive(tmp_path)
    monkeypatch.setattr(fq_tables, "MOREL2002_FQ_MD5", digest)
    t = jerlov.morel2002_fq_tables(path)
    assert t.wavelengths_nm == (412.5,) and t.sun_zenith_deg == (0.0, 15.0)
    assert len(t.nadir_deg) == 17 and t.nadir_deg[0] == 1.078
    assert t.azimuth_deg[-1] == 180.0
    assert t.f(412.5, sun_zenith_deg=15.0, chlorophyll_mg_m3=0.03) \
        == 0.299979
    kw = dict(sun_zenith_deg=0.0, chlorophyll_mg_m3=0.03)
    # Nadir 0 takes the 1.078 degree row (Appendix A).
    assert t.f_over_q(412.5, nadir_deg=0.0, azimuth_deg=0.0, **kw) \
        == t.f_over_q(412.5, nadir_deg=1.078, azimuth_deg=0.0, **kw) == 0.09
    assert t.f_over_q(412.5, nadir_deg=48.83, azimuth_deg=180.0, **kw) \
        == pytest.approx(0.09 + 0.016 + 0.0012)
    assert t.surface_factor(wind="flat", nadir_deg=0.0) == 0.528716
    assert t.surface_factor(wind=4, nadir_deg=48) == 0.23983
    for bad in (dict(nadir_deg=2.0, azimuth_deg=0.0),
                dict(nadir_deg=0.0, azimuth_deg=10.0)):
        with pytest.raises(ValueError, match="table's own"):
            t.f_over_q(412.5, **kw, **bad)
    with pytest.raises(ValueError):
        t.f(490.0, **kw)
    with pytest.raises(ValueError):
        t.surface_factor(wind="rough", nadir_deg=0.0)
    with pytest.raises(TypeError):
        t.f(412.5, sun_zenith_deg=0.0)


def test_another_archive_is_refused(tmp_path):
    path, _ = _small_archive(tmp_path)
    with pytest.raises(ValueError, match="oceane.obs-vlfr.fr"):
        jerlov.morel2002_fq_tables(path)


needs_archive = pytest.mark.skipif(
    not REAL.exists(), reason="the authors' archive is not shipped; "
    "sources/morel2002/ (DATA.md section 48)")


def _appendix_b():
    text = (importlib.resources.files("jerlov.data")
            / "morel2002_nadir_fq.csv").read_text()
    return {(r["quantity"], float(r["chl_mg_m3"]),
             float(r["wavelength_nm"])): float(r["value"])
            for r in csv.DictReader(io.StringIO(text))}


@needs_archive
def test_the_real_archive_against_appendix_b():
    t = jerlov.morel2002_fq_tables(REAL)
    assert len(t.wavelengths_nm) == 7 and len(t.chlorophyll_mg_m3) == 6
    assert t.sun_zenith_deg == (0.0, 15.0, 30.0, 45.0, 60.0, 75.0)
    b = _appendix_b()
    f_off = max(abs(t.f(w, sun_zenith_deg=0.0, chlorophyll_mg_m3=c)
                    / b[("f0", c, w)] - 1)
                for w in t.wavelengths_nm for c in t.chlorophyll_mg_m3)
    q_off = max(abs(t.f_over_q(w, sun_zenith_deg=0.0, chlorophyll_mg_m3=c,
                               nadir_deg=0.0, azimuth_deg=0.0)
                    / b[("f0_over_Q0", c, w)] - 1)
                for w in t.wavelengths_nm for c in t.chlorophyll_mg_m3)
    assert (round(100 * f_off, 2), round(100 * q_off, 2)) == (0.62, 1.19)
    assert t.surface_winds == (0.0, 4.0, 6.0, 8.0, 16.0, "flat")
    assert 10.0 not in t.surface_winds
    with tarfile.open(REAL) as archive:
        inner = archive.extractfile("DISTRIB_fQ_with_Raman/lin-approx.tar")
        lin = tarfile.open(fileobj=io.BytesIO(inner.read()))
        names = {"f0": "table.f0", "Sf": "table.Sf", "Q0": "table.Q0",
                 "SQ": "table.SQn", "f0_over_Q0": "table.fOQ0",
                 "S_f_over_Q": "table.SfOQn"}
        same = 0
        for q, member in names.items():
            lines = lin.extractfile(member).read().decode().splitlines()
            wl = [float(v) for v in lines[0].split()]
            for line in lines[1:]:
                fields = line.split()
                for w, v in zip(wl, fields[1:]):
                    assert float(v) == b[(q, float(fields[0]), w)]
                    same += 1
    assert same == 252
    values = [t.f_over_q(w, sun_zenith_deg=s, chlorophyll_mg_m3=c,
                         nadir_deg=n, azimuth_deg=a)
              for w in t.wavelengths_nm for s in t.sun_zenith_deg
              for c in t.chlorophyll_mg_m3 for n in t.nadir_deg[::8]
              for a in t.azimuth_deg[::6]]
    assert np.all(np.isfinite(values))


@needs_archive
def test_eq_b1_and_b4_against_the_archive_away_from_the_zenith():
    # DATA.md section 48, DECISIONS.md section 105.
    t = jerlov.morel2002_fq_tables(REAL)
    cases = [(w, c) for w in t.wavelengths_nm for c in t.chlorophyll_mg_m3]

    def fit(w, c, s):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", jerlov.ProvenanceWarning)
            return jerlov.morel2002_nadir_fq(w, chlorophyll_mg_m3=c,
                                             sun_zenith_deg=s)

    for sun, worst, above in ((15.0, 0.47, 0), (30.0, 1.10, 13),
                              (45.0, 2.70, 26), (60.0, 1.29, 5)):
        d = [abs(fit(w, c, sun).f
                 / t.f(w, sun_zenith_deg=sun, chlorophyll_mg_m3=c) - 1)
             for w, c in cases]
        assert round(100 * max(d), 2) == worst
        assert sum(x > 0.005 for x in d) == above
        if sun == 45.0:
            assert sum(x > 0.02 for x in d) == 2
            assert cases[int(np.argmax(d))] == (660.0, 0.03)
    for sun, worst in ((0.0, 1.20), (15.0, 0.74), (30.0, 0.43),
                       (45.0, 3.34), (60.0, 1.61), (75.0, 1.66)):
        d = [abs(fit(w, c, sun).f_over_q
                 / t.f_over_q(w, sun_zenith_deg=sun, chlorophyll_mg_m3=c,
                              nadir_deg=0.0, azimuth_deg=az) - 1)
             for w, c in cases for az in t.azimuth_deg]
        assert round(100 * max(d), 2) == worst
    # f.dat at 45 degrees against the line in 1 - cos between 30 and 60.
    x = {s: 1 - np.cos(np.radians(s)) for s in (30.0, 45.0, 60.0)}
    dip = {}
    for w, c in cases:
        f30, f45, f60 = (t.f(w, sun_zenith_deg=s, chlorophyll_mg_m3=c)
                         for s in (30.0, 45.0, 60.0))
        line = f30 + (f60 - f30) * (x[45.0] - x[30.0]) / (x[60.0] - x[30.0])
        dip[(w, c)] = 100 * (f45 / line - 1)
    assert [round(dip[(w, 0.03)], 2) for w in (660.0, 620.0, 560.0)] \
        == [-3.44, -3.00, -2.25]
    assert sum(v < -1 for v in dip.values()) == 7
    assert round(max(dip.values()), 2) == 1.22
    assert max(dip, key=dip.get) == (412.5, 10.0)

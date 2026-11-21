"""Morel, Antoine & Gentili's (2002) full f/Q tables, read from the user's
own copy of the authors' archive: DECISIONS.md section 104, DATA.md
section 48.

The archive has no stated licence, so this package does not ship it. Get
``DISTRIB_fQ_with_Raman.tar.gz`` from
``ftp://oceane.obs-vlfr.fr/pub/gentili/AppliedOptics2002/`` and pass its
path to :func:`morel2002_fq_tables`.
"""

from __future__ import annotations

import hashlib
import io
import pathlib
import tarfile
import warnings

import numpy as np

from . import _data
from ._data import finite_number as _one
from .water import ProvenanceWarning

#: The MD5 of the archive this package was checked against (DATA.md
#: section 48): DISTRIB_fQ_with_Raman.tar.gz, 173,005 bytes, 18 June 2003.
MOREL2002_FQ_MD5 = "21c7afc6c6d3c1963311d6880456f7bc"
_WHERE = ("ftp://oceane.obs-vlfr.fr/pub/gentili/AppliedOptics2002/"
          "DISTRIB_fQ_with_Raman.tar.gz")
_PREFIX = "DISTRIB_fQ_with_Raman/"
#: The run out of line with the rest of the table (DATA.md section 48,
#: DECISIONS.md section 116): (sun zenith angle, Chl).
_SUSPECT = (45.0, 0.03)


def _warn_suspect(case: tuple[float, float, float]) -> None:
    if (case[1], case[2]) == _SUSPECT:
        warnings.warn(
            "f and f/Q at a sun of 45 degrees and 0.03 mg/m3 are suspect: "
            "at every wavelength they lie below the line between 30 and 60 "
            "degrees where every other Chl lies above it (by 1.0 to 3.4 "
            "percent in f), out of line with the rest of the table; they "
            "are returned as the archive has them. DATA.md section 48",
            ProvenanceWarning, stacklevel=_data.caller_stacklevel())


def _pick(value: float, grid: tuple[float, ...], name: str) -> float:
    for g in grid:
        if abs(value - g) < 1e-9:
            return g
    raise ValueError(f"{name} must be one of the table's own values, "
                     f"{', '.join(f'{g:g}' for g in grid)}, not {value:g}; "
                     "Morel et al. (2002) give no rule between them")


class Morel2002FQTables:
    """The tables of Morel et al.'s (2002) archive, read by
    :func:`morel2002_fq_tables`.

    Attributes ``wavelengths_nm``, ``sun_zenith_deg``, ``chlorophyll_mg_m3``,
    ``nadir_deg`` (17, in water) and ``azimuth_deg`` (13) give the grid.
    Azimuth 0 is the sensor and the sun on opposite sides of the vertical,
    180 on the same side (the archive's README_FIRST).
    """

    def __init__(self, foq: dict, f: dict, nadir: tuple, azimuth: tuple,
                 surface: dict):
        self._foq, self._f, self._surface = foq, f, surface
        keys = list(foq)
        self.wavelengths_nm = tuple(sorted({k[0] for k in keys}))
        self.sun_zenith_deg = tuple(sorted({k[1] for k in keys}))
        self.chlorophyll_mg_m3 = tuple(sorted({k[2] for k in keys}))
        self.nadir_deg = nadir
        self.azimuth_deg = azimuth
        self.surface_winds = tuple(sorted({w for w, _ in surface},
                                          key=lambda w: (w == "flat", w)))
        self.surface_nadir_deg = tuple(sorted({n for _, n in surface}))

    def _case(self, wavelength_nm, sun_zenith_deg, chlorophyll_mg_m3):
        return (_pick(_one(wavelength_nm, "wavelength_nm"),
                      self.wavelengths_nm, "wavelength_nm"),
                _pick(_one(sun_zenith_deg, "sun_zenith_deg"),
                      self.sun_zenith_deg, "sun_zenith_deg"),
                _pick(_one(chlorophyll_mg_m3, "chlorophyll_mg_m3"),
                      self.chlorophyll_mg_m3, "chlorophyll_mg_m3"))

    def f(self, wavelength_nm, /, *, sun_zenith_deg, chlorophyll_mg_m3):
        """f of R = Eu/Ed = f bb/a (their Eq. 11), from f.dat.

        At a sun of 45 degrees and 0.03 mg/m3 the value is suspect and
        comes with a :class:`ProvenanceWarning` (DATA.md section 48)."""
        case = self._case(wavelength_nm, sun_zenith_deg, chlorophyll_mg_m3)
        _warn_suspect(case)
        return self._f[case]

    def f_over_q(self, wavelength_nm, /, *, sun_zenith_deg,
                 chlorophyll_mg_m3, nadir_deg, azimuth_deg):
        """f/Q for the upward radiance in water at ``nadir_deg`` (one of
        the 17, or 0, which takes the 1.078 degree row as the paper says)
        and ``azimuth_deg`` (0 to 180 every 15). At a sun of 45 degrees
        and 0.03 mg/m3 the value is suspect and comes with a
        :class:`ProvenanceWarning` (DATA.md section 48)."""
        case = self._case(wavelength_nm, sun_zenith_deg, chlorophyll_mg_m3)
        nadir = _one(nadir_deg, "nadir_deg")
        row = 0 if nadir == 0 else self.nadir_deg.index(
            _pick(nadir, self.nadir_deg, "nadir_deg"))
        col = self.azimuth_deg.index(
            _pick(_one(azimuth_deg, "azimuth_deg"), self.azimuth_deg,
                  "azimuth_deg"))
        value = float(self._foq[case][row, col])
        _warn_suspect(case)
        return value

    def surface_factor(self, *, wind, nadir_deg):
        """The R-gothic of rgoth_Ebuchi.dat for ``wind`` ("flat", or 0, 4,
        6, 8 or 16 m/s) and the nadir angle in water, 0 to 90 every 1."""
        if isinstance(wind, str):
            if wind != "flat":
                raise ValueError('wind must be "flat" or one of 0, 4, 6, 8, '
                                 "16 m/s")
            key = "flat"
        else:
            numbers = tuple(w for w in self.surface_winds if w != "flat")
            key = _pick(_one(wind, "wind"), numbers, "wind")
        nadir = _pick(_one(nadir_deg, "nadir_deg"), self.surface_nadir_deg,
                      "nadir_deg")
        return self._surface[(key, nadir)]


def _read(archive: tarfile.TarFile, name: str) -> str:
    member = archive.extractfile(_PREFIX + name)
    if member is None:              # pragma: no cover - a directory
        raise ValueError(f"{name} is not a file in the archive")
    return member.read().decode("ascii")


@_data.positional_only()
def morel2002_fq_tables(path, /):
    """Read Morel, Antoine & Gentili's (2002) full f and f/Q tables from
    the user's own copy of the authors' archive.

    Morel, A., Antoine, D. and Gentili, B. (2002), Appl. Opt. 41(30),
    6289-6306, doi:10.1364/AO.41.006289, Appendix A: f and f/Q for seven
    wavelengths, six sun angles and six Chl, f/Q for 17 nadir angles in
    water by 13 azimuths, Raman emission included, case 1 water; and the
    surface factor R-gothic. The archive states no licence, so this
    package does not ship it: get ``DISTRIB_fQ_with_Raman.tar.gz`` from
    ftp://oceane.obs-vlfr.fr/pub/gentili/AppliedOptics2002/ and pass its
    path. It is read as it is, without extracting.

    Parameters
    ----------
    path:
        The archive. Its MD5 must be :data:`MOREL2002_FQ_MD5`, the copy
        this package was checked against; another is refused.

    Returns
    -------
    :class:`Morel2002FQTables`.

    Notes
    -----
    The nadir view alone, as the paper prints it, is
    :func:`morel2002_nadir_fq`, which needs no file. DECISIONS.md section
    104, DATA.md section 48.
    """
    raw = pathlib.Path(path).read_bytes()
    digest = hashlib.md5(raw).hexdigest()
    if digest != MOREL2002_FQ_MD5:
        raise ValueError(
            f"{path} has MD5 {digest}, not {MOREL2002_FQ_MD5}, the archive "
            f"this package was checked against; get it from {_WHERE}")
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        info = _read(archive, "foQ.info").splitlines()
        nadir = tuple(float(v) for v in info[10].split())
        azimuth = tuple(float(v) for v in info[12].split())
        foq = {}
        for member in archive.getmembers():
            name = member.name
            if not name.startswith(_PREFIX + "D_foQ_pa/foQ_"):
                continue
            _, wl, sun, chl = name.rsplit("/", 1)[1].split("_")
            table = np.loadtxt(io.StringIO(_read(
                archive, name[len(_PREFIX):])))
            if table.shape != (len(nadir), len(azimuth)):
                raise ValueError(f"{name} is {table.shape}, not "
                                 f"{len(nadir)} by {len(azimuth)}")
            table.setflags(write=False)
            foq[(float(wl), float(sun), float(chl))] = table
        f = {}
        for line in _read(archive, "f.dat").splitlines():
            wl, sun, chl, value = line.split()
            f[(float(wl), float(sun), float(chl))] = float(value)
        surface = {}
        for line in _read(archive, "rgoth_Ebuchi.dat").splitlines():
            wind, angle, value = line.split()
            key = "flat" if wind == "xx" else float(wind)
            surface[(key, float(angle))] = float(value)
    if set(f) != set(foq):
        raise ValueError("f.dat and D_foQ_pa do not cover the same cases")
    return Morel2002FQTables(foq, f, nadir, azimuth, surface)

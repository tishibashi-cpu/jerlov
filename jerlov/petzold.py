"""Measured volume scattering functions: Petzold (1972).

``Water.bb`` refuses to guess a backscattering ratio, and ``bb_from_vsf``
needs an instrument reading. Between the two sits the most cited set of
measured volume scattering functions in ocean optics: eight ocean stations
measured by Petzold in 1971, from the clear Tongue of the Ocean in the
Bahamas to turbid San Diego Harbor, at 0.1 to 180 degrees and 530 nm, each
with its own c, b, a and B/S.

    T. J. Petzold, 'Volume scattering functions for selected ocean waters',
    SIO Ref. 72-78, Scripps Institution of Oceanography, Visibility
    Laboratory (1972). DTIC AD0753474.

These are what eight particular waters did, not properties of a Jerlov type:
Petzold classified nothing, and gives c only at 530 nm. Choosing a station
is choosing which measured water yours most resembles. See DATA.md
section 21.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np

from . import _data
from .water import (ProvenanceWarning, _as_array, _like_input,
                    _require_number, _support)

CITATION = (
    "Petzold, T. J. (1972), 'Volume scattering functions for selected ocean "
    "waters', SIO Ref. 72-78, Scripps Institution of Oceanography, "
    "Visibility Laboratory, San Diego"
)


@dataclass(frozen=True, eq=False)   # == on arrays has no single answer
class ScatteringFunction:
    """One station of Petzold (1972), as the report prints it.

    Every scattering quantity is total: pure water and particles together,
    as the instruments measured them.
    """

    station: str
    locale: str
    date: str
    wavelength_nm: float
    """530 nm, at which c was measured. The scattering meters share one
    spectral response, a band through the green (the report's Fig. 3)."""
    angles_deg: np.ndarray
    """The report's 55 angles: 0.1 to 10 degrees evenly in log angle, then
    every 5 degrees to 180."""
    vsf: np.ndarray
    """The volume scattering function, 1/(m sr)."""
    statuses: tuple[str, ...]
    """``"extrapolated"`` below the first measured angle, else ``"ok"``."""
    c: float
    """Beam attenuation, 1/m, measured with a transmissometer."""
    b: float
    """Scattering coefficient s, 1/m: the vsf integrated over all angles,
    including the report's extension below 0.1 degree."""
    a: float
    """Absorption, 1/m: c - b."""
    backscatter_ratio: float
    """B/S, the share of b scattered beyond 90 degrees, as printed."""
    fraction_below_0_1_deg: float
    """The share of b that lies below 0.1 degree, where nothing was
    measured and the report extended the vsf with a power law."""

    def phase_function(self) -> np.ndarray:
        """The vsf divided by b, 1/sr.

        Over the whole sphere it integrates to one, but only with the part
        below 0.1 degree that the samples do not show:
        :attr:`fraction_below_0_1_deg` of it, 3 to 15 percent.
        """
        return self.vsf / self.b

    def vsf_at(self, angle_deg):
        """The vsf at ``angle_deg``, interpolated linearly in log-log.

        Refuses angles outside 0.1 to 180 degrees. Below 0.169 degree at the
        Bahamas and Catalina stations the values are the report's own
        extension, and a :class:`ProvenanceWarning` says so.
        """
        query = _as_array(angle_deg)
        _require_number(query, "angle_deg")
        lo, hi = float(self.angles_deg[0]), float(self.angles_deg[-1])
        if np.any(query < lo) or np.any(query > hi):
            raise ValueError(
                f"Petzold tabulates {lo:g} to {hi:g} degrees, and this "
                "package does not extrapolate"
            )
        flagged = sorted({
            f"{self.angles_deg[j]:g} deg"
            for samples in _support(self.angles_deg, query) for j in samples
            if self.statuses[j] in _data.QUESTIONABLE
        })
        if flagged:
            warnings.warn(
                f"the vsf of {self.station} at {', '.join(flagged)} is "
                "extrapolated: nothing was measured below 0.169 degree there. "
                "See DATA.md section 21.",
                ProvenanceWarning,
                stacklevel=_data.caller_stacklevel(),
            )
        out = np.exp(np.interp(np.log(query), np.log(self.angles_deg),
                               np.log(self.vsf)))
        # A printed angle gives the printed value, not its exp(log()).
        exact = np.isin(query, self.angles_deg)
        out[exact] = self.vsf[np.searchsorted(self.angles_deg, query[exact])]
        return _like_input(out, angle_deg)

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return (f"<ScatteringFunction {self.station} ({self.locale}), "
                f"c={self.c:g} b={self.b:g} 1/m, B/S={self.backscatter_ratio:g}>")


def _stations() -> dict[str, dict[str, str]]:
    return {r["station"]: r for r in _data._rows("petzold1972_stations.csv")}


#: The eight ocean stations, clearest first by b.
PETZOLD_STATIONS = ("AUTEC 8", "AUTEC 9", "AUTEC 7", "HAOCE 11", "HAOCE 5",
                    "NUC 2240", "NUC 2200", "NUC 2040")


def petzold_scattering(station: str) -> ScatteringFunction:
    """The volume scattering function measured at one of Petzold's stations.

    ``station`` is one of :data:`PETZOLD_STATIONS`: the Tongue of the Ocean
    in the Bahamas (``"AUTEC 7"``, ``"AUTEC 8"``, ``"AUTEC 9"``), off
    southern California (``"HAOCE 5"``, ``"HAOCE 11"``) and San Diego Harbor
    (``"NUC 2200"``, ``"NUC 2040"``, ``"NUC 2240"``).

    Its ``backscatter_ratio`` is a measured bb/b that can be passed to
    :meth:`Water.bb` in place of a guess, which is what most users of this
    report want from it. It is the ratio of that water, at 530 nm, with pure
    water included; it spans 0.013 to 0.044 across the eight.
    """
    info = _stations().get(station)
    if info is None:
        raise KeyError(f"unknown station {station!r}; Petzold's ocean "
                       f"stations are {', '.join(PETZOLD_STATIONS)}")
    rows = sorted((r for r in _data._rows("petzold1972_vsf.csv")
                   if r["station"] == station),
                  key=lambda r: float(r["angle_deg"]))
    angles = np.array([float(r["angle_deg"]) for r in rows])
    vsf = np.array([float(r["vsf_per_m_sr"]) for r in rows])
    for array in (angles, vsf):
        array.setflags(write=False)
    return ScatteringFunction(
        station=station,
        locale=info["locale"],
        date=info["date"],
        wavelength_nm=float(info["wavelength_nm"]),
        angles_deg=angles,
        vsf=vsf,
        statuses=tuple(r["status"] for r in rows),
        c=float(info["c_per_m"]),
        b=float(rows[-1]["integral_per_m"]),
        a=float(info["c_per_m"]) - float(rows[-1]["integral_per_m"]),
        backscatter_ratio=float(info["bb_over_b"]),
        fraction_below_0_1_deg=float(rows[0]["normalized_integral"]),
    )

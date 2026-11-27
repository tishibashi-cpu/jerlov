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
from .water import (MissingQuantityError, ProvenanceWarning, _as_array,
                    _like_input, _require_number, _support)

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

    def mean_cosine(self) -> float:
        """The mean cosine of the scattering angle, the asymmetry g.

        2 pi times the integral of the phase function times cos(theta)
        sin(theta) from 0.1 to 180 degrees, the vsf taken as a power law
        between the printed angles as :meth:`vsf_at` takes it, plus
        :attr:`fraction_below_0_1_deg` at a cosine of 1.

        That share, 3.4 to 14.5 percent of b, is the report's power-law
        extension at every station, and it enters at full weight, so this
        always warns with :class:`ProvenanceWarning`. Normalised by the
        printed b, which includes the same extension.
        """
        warnings.warn(
            f"the mean cosine of {self.station} rests on the report's "
            "power-law extension below 0.1 degree, "
            f"{self.fraction_below_0_1_deg:.1%} of b, counted at a cosine "
            "of 1. See DATA.md section 21.",
            ProvenanceWarning,
            stacklevel=_data.caller_stacklevel(),
        )
        return self._integral(np.cos) / self.b + self.fraction_below_0_1_deg

    def _integral(self, weight) -> float:
        """2 pi times the integral of vsf * weight(theta) * sin(theta),
        from 0.1 to 180 degrees, the vsf a power law between samples."""
        log_angle = np.log(self.angles_deg)
        log_vsf = np.log(self.vsf)
        total = 0.0
        for i in range(self.angles_deg.size - 1):
            theta = np.linspace(self.angles_deg[i], self.angles_deg[i + 1],
                                257)
            vsf = np.exp(np.interp(np.log(theta), log_angle, log_vsf))
            rad = np.radians(theta)
            total += float(_data.trapezoid(
                vsf * weight(rad) * np.sin(rad), rad))
        return 2 * np.pi * total

    def vsf_at(self, angle_deg):
        """The vsf at ``angle_deg``, interpolated linearly in log-log.

        Refuses angles outside 0.1 to 180 degrees. Below 0.169 degree at the
        Bahamas and Catalina stations the values are the report's own
        extension, and a :class:`ProvenanceWarning` says so.
        """
        query = _as_array(angle_deg)
        if query.ndim > 1:
            raise ValueError(
                "angle_deg must be a number or a 1-D array of them, not an "
                f"array of shape {query.shape}")
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
                f"c={self.c:g} b={self.b:g} 1/m, "
                f"B/S={self.backscatter_ratio:g}>")


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


# -- forward scattering: the light kept within an angle (DECISIONS.md
# section 107) --------------------------------------------------------------


@dataclass(frozen=True)
class ForwardScatter:
    """The share of a phase function's scattering within a half-angle, from
    :func:`forward_scatter`: one of Petzold's stations, or a
    :class:`FournierForand` (since 1.31.0)."""

    station: str
    """The Petzold station, or the Fournier-Forand's n and mu."""
    half_angle_deg: float
    """theta0, degrees: light turned by less than this is counted as kept."""
    fraction: float
    """b(< theta0) / b: the share of the scattering within theta0."""
    extension_fraction: float
    """The share of b below 0.1 degree, the report's extension, included
    in :attr:`fraction` at every theta0."""
    wavelength_nm: float
    """530 nm, Petzold's."""
    c: float
    """The station's beam attenuation, 1/m, as measured."""
    c_within: float
    """c - b(< theta0), 1/m: the attenuation of the light that stays
    within theta0 of its direction, for the station itself at 530 nm."""
    particles_only: bool = False
    """True for a Fournier-Forand, which describes the particles alone:
    :func:`attenuation_within` then asks for pure water's scattering apart.
    Its ``wavelength_nm``, ``c`` and ``c_within`` are NaN, since a phase
    function has no water and no c of its own."""


#: One NaN object, so that two equal results compare equal (a tuple
#: compares its items by identity first).
_NAN = float("nan")


def _printed_cumulative(station: str) -> np.ndarray:
    rows = sorted((r for r in _data._rows("petzold1972_vsf.csv")
                   if r["station"] == station),
                  key=lambda r: float(r["angle_deg"]))
    return np.array([float(r["normalized_integral"]) for r in rows])


def forward_scatter(scattering, half_angle_deg) -> ForwardScatter:
    """The share of a measured water's scattering within a half-angle, and
    the attenuation of the light that stays within it.

    A receiver that accepts light within theta0 of a beam's direction,
    as a transmissometer does, reads, in single scattering::

        c_within = c - b(< theta0),
        b(< theta0) = 2 pi integral from 0 to theta0 of vsf sin(theta)

    between c (theta0 = 0) and a (180 degrees). For an image, light from a
    target turned by less than theta0 arrives within theta0 of the
    target's direction: blurred, not lost. That reading, and single
    scattering, are assumptions; DECISIONS.md section 107.

    Parameters
    ----------
    scattering:
        One of Petzold's stations, from :func:`petzold_scattering`, or a
        :class:`FournierForand` (since 1.31.0). No default: which water,
        or which particles, yours resemble is your choice.
    half_angle_deg:
        theta0, one number from 0.1 to 180 degrees for a station (below 0.1
        degree nothing was measured, and it is refused), from 0 to 180 for
        a Fournier-Forand.

    Returns
    -------
    :class:`ForwardScatter`. At the report's printed angles the share is
    the report's own cumulative integral; between them it follows the
    vsf as a power law, as :meth:`ScatteringFunction.vsf_at` takes it,
    scaled to meet the printed values at both ends.

    Notes
    -----
    For a station, every share includes the report's power-law extension
    below 0.1 degree, 3.4 to 14.5 percent of b, and at AUTEC 7-9 and
    HAOCE 5 and 11 its extrapolated angles to 0.159 degree; a
    :class:`ProvenanceWarning` says so. DATA.md section 49.

    For a Fournier-Forand the share is its closed-form
    :meth:`FournierForand.cumulative`, with no warning. It is the
    particles' share alone, and the result has ``particles_only`` set, no
    c, and NaN for ``wavelength_nm``, ``c`` and ``c_within``. DECISIONS.md
    section 128.
    """
    from .fournier_forand import FournierForand
    if isinstance(scattering, FournierForand):
        theta0 = _data.finite_number(half_angle_deg, "half_angle_deg")
        if not 0.0 <= theta0 <= 180.0:
            raise ValueError("half_angle_deg must lie in 0 to 180 degrees")
        nan = _NAN
        return ForwardScatter(
            station=(f"Fournier-Forand, n = {scattering.refractive_index:g}"
                     f", mu = {scattering.junge_slope:g}"),
            half_angle_deg=theta0,
            fraction=float(scattering.cumulative(theta0)),
            extension_fraction=0.0, wavelength_nm=nan, c=nan, c_within=nan,
            particles_only=True)
    if not isinstance(scattering, ScatteringFunction):
        raise TypeError("scattering must be a ScatteringFunction, from "
                        "petzold_scattering(), or a FournierForand; there "
                        "is no default")
    theta0 = _data.finite_number(half_angle_deg, "half_angle_deg")
    angles = scattering.angles_deg
    if not angles[0] <= theta0 <= angles[-1]:
        raise ValueError(
            f"half_angle_deg must lie in {angles[0]:g} to {angles[-1]:g} "
            "degrees: below 0.1 degree nothing was measured, and this "
            "package does not extrapolate")
    printed = _printed_cumulative(scattering.station)
    i = int(np.searchsorted(angles, theta0, side="right")) - 1
    if i >= angles.size - 1 or theta0 == angles[i]:
        fraction = float(printed[min(i, angles.size - 1)])
    else:
        log_angle, log_vsf = np.log(angles), np.log(scattering.vsf)

        def segment(top):
            theta = np.linspace(angles[i], top, 257)
            vsf = np.exp(np.interp(np.log(theta), log_angle, log_vsf))
            rad = np.radians(theta)
            return float(_data.trapezoid(vsf * np.sin(rad), rad))

        share = segment(theta0) / segment(angles[i + 1])
        fraction = float(printed[i] + share * (printed[i + 1] - printed[i]))
    extrapolated = sum(1 for s in scattering.statuses
                       if s in _data.QUESTIONABLE)
    warnings.warn(
        f"the share of {scattering.station}'s scattering within a "
        f"half-angle of {theta0:g} deg includes the report's power-law "
        f"extension below 0.1 degree, "
        f"{scattering.fraction_below_0_1_deg:.1%} of b"
        + (f", and {extrapolated} extrapolated angles to 0.159 degree"
           if extrapolated else "")
        + ". See DATA.md sections 21 and 49.",
        ProvenanceWarning,
        stacklevel=_data.caller_stacklevel(),
    )
    return ForwardScatter(
        station=scattering.station,
        half_angle_deg=theta0,
        fraction=fraction,
        extension_fraction=float(scattering.fraction_below_0_1_deg),
        wavelength_nm=float(scattering.wavelength_nm),
        c=float(scattering.c),
        c_within=float(scattering.c - fraction * scattering.b),
    )


def _pure_water_share(theta0_deg: float) -> float:
    """Pure water's share of scattering within theta0, for the shape of
    :func:`pure_water_vsf`, 1 + r cos^2: 2 pi integral of (1 + r cos^2)
    sin from 0 to theta0, over the same from 0 to 180 degrees."""
    from .backscattering import _ratio
    r = _ratio()
    c = np.cos(np.radians(theta0_deg))
    return float(((1.0 - c) + r * (1.0 - c ** 3) / 3.0)
                 / (2.0 * (1.0 + r / 3.0)))


@_data.positional_only()
def attenuation_within(water, wavelengths, /, *, forward: ForwardScatter,
                       pure_water_b=None):
    """A water's attenuation of the light that stays within a half-angle,
    with the forward scattering of one of Petzold's stations::

        c_within(lambda) = c(lambda) - f b(lambda),  f = forward.fraction

    or, since 1.31.0, of a Fournier-Forand, which describes the particles
    alone, so that pure water's scattering is taken apart::

        c_within = c - f (b - b_w) - f_w b_w

    with f_w pure water's own share within the same half-angle, from the
    shape of :func:`pure_water_vsf` (Morel's, depolarisation ratio 0.09).

    Between the water's c and its a. It assumes that the phase function
    holds for this water and does not change with wavelength; neither is
    known, which is why ``forward`` has no default. DECISIONS.md sections
    107 and 128.

    Parameters
    ----------
    water:
        A :class:`Water` with a and b.
    wavelengths:
        nm, a number or an array, within the water's range.
    forward:
        From :func:`forward_scatter`: the station or Fournier-Forand, and
        the half-angle.
    pure_water_b:
        Only with a Fournier-Forand, and then required: the scattering of
        pure water that the water's b includes, 1/m, one number or one per
        wavelength; for example :func:`pure_water_scattering` at the
        water's salinity. With a station it must be left out: the station
        is the whole water.

    Returns
    -------
    1/m, a float for a number, an array otherwise. NaN where the water
    has a gap.
    """
    if not isinstance(forward, ForwardScatter):
        raise TypeError("forward must be a ForwardScatter, from "
                        "forward_scatter(); there is no default")
    c = np.atleast_1d(np.asarray(water.c(wavelengths), dtype=float))
    b = np.atleast_1d(np.asarray(water.b(wavelengths), dtype=float))
    if not forward.particles_only:
        if pure_water_b is not None:
            raise ValueError(
                f"pure_water_b is for a Fournier-Forand only: "
                f"{forward.station} is the whole water, pure water "
                "included")
        return _like_input(c - forward.fraction * b, wavelengths)
    if pure_water_b is None:
        raise MissingQuantityError(
            "a Fournier-Forand describes the particles alone, so "
            "attenuation_within needs pure_water_b, the pure water "
            "scattering in the water's b (for example "
            "pure_water_scattering(wavelengths, salinity_psu=...)); there "
            "is no default")
    bw = np.array(pure_water_b, dtype=float)       # a copy
    if bw.ndim > 1 or (bw.ndim == 1 and bw.shape != b.shape):
        raise ValueError(
            "pure_water_b must be one number or one per wavelength, not "
            f"an array of shape {bw.shape}")
    if not np.all(np.isfinite(bw)) or np.any(bw < 0):
        raise ValueError("pure_water_b must be finite and not negative")
    bw = np.broadcast_to(bw, b.shape)
    if np.any(bw > b):
        raise ValueError(
            "pure_water_b exceeds the water's b at "
            f"{np.atleast_1d(wavelengths)[bw > b][:3].tolist()} nm; it must "
            "be the pure water that b includes")
    share_w = _pure_water_share(forward.half_angle_deg)
    out = c - forward.fraction * (b - bw) - share_w * bw
    return _like_input(out, wavelengths)

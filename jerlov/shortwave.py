"""How much solar radiation is left at depth.

Ocean circulation models heat the upper ocean by absorbing shortwave radiation
according to a sum of two exponentials, with parameters per Jerlov type from
Paulson & Simpson (1977)::

    I(z) / I(0) = R exp(-z/zeta1) + (1 - R) exp(-z/zeta2)

This is broadband, 300-2500 nm, and has nothing to do with the spectral
quantities in the rest of the package. It is here because it is the most
widely used application of the Jerlov classification and the parameters are
usually copied from secondary sources; `tools/build_paulson1977.py` refits
them from Jerlov (1968) Table XXI and reproduces R for every row.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np

from . import _data
from .ocean_colour import (_KVIS_PAPER, _KVIS_SUN, _check_iops, _finite,
                           _kvis_check, _kvis_k1_k2, _result, _sun, _warn)
from .water import ProvenanceWarning, _like_input, _require_number

CITATION = (
    "Paulson, C. A. and Simpson, J. J. (1977), 'Irradiance measurements in "
    "the upper ocean', J. Phys. Oceanogr. 7, 952-956"
)
DOI = "10.1175/1520-0485(1977)007<0952:IMITUO>2.0.CO;2"


@dataclass(frozen=True)
class ShortwaveParameters:
    """One row of Paulson & Simpson (1977) Table 2."""

    key: str
    water_type: str
    R: float
    """Share of the surface irradiance in the fast-decaying term."""
    zeta1_m: float
    """Attenuation length of the fast term, metres. Red light."""
    zeta2_m: float
    """Attenuation length of the slow term, metres. Blue-green light."""
    fit_depth_m: float | None
    """Depth the row was fitted down to: 100 m, or 50 m for ``I_upper50``.
    The paper's text says so; the table does not. None for the rows that are
    not Jerlov types."""
    note: str

    def fraction_at(self, depth_m):
        """``I(z)/I(0)`` at one or more depths.

        Below :attr:`fit_depth_m` the two exponentials are extrapolated
        beyond the data they were fitted to, and a
        :class:`~jerlov.ProvenanceWarning` says so. Jerlov's own Table XXI
        goes deeper for the clearer types; see
        :func:`jerlov1968_solar_fraction`.
        """
        z = np.atleast_1d(np.asarray(depth_m, dtype=float))
        _require_number(z, "depth_m")
        if np.any(z < 0):
            raise ValueError("depth_m cannot be negative")
        if self.fit_depth_m is not None and np.any(z > self.fit_depth_m):
            warnings.warn(
                f"{self.key}: Paulson & Simpson (1977) fitted these "
                f"parameters to the upper {self.fit_depth_m:g} m; at "
                f"{float(np.max(z)):g} m the two exponentials are "
                "extrapolated. See DATA.md section 14.",
                ProvenanceWarning,
                stacklevel=_data.caller_stacklevel(),
            )
        out = (self.R * np.exp(-z / self.zeta1_m)
               + (1 - self.R) * np.exp(-z / self.zeta2_m))
        return _like_input(out, depth_m)

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return (f"<ShortwaveParameters {self.key} R={self.R} "
                f"zeta1={self.zeta1_m} m zeta2={self.zeta2_m} m>")


def _rows():
    return _data._rows("paulson1977_shortwave.csv")


def shortwave_parameters(
        water_type: str, *,
        include_non_types: bool = False) -> ShortwaveParameters:
    """Paulson & Simpson parameters for a Jerlov water type.

    Only the five oceanic types I, IA, IB, II and III were fitted; the paper
    covers no coastal type, and this raises rather than substituting one.

    ``water_type="I_upper50"`` selects the paper's alternative fit for type I
    over the upper 50 m, which it gives because ``ln I`` against depth changes
    slope below that. The plain ``"I"`` row is the 100 m fit.

    Table 2 also prints three rows that are not water types: the authors'
    composite observations, their Run 1, and a Kraus (1972) value from Crater
    Lake (keys ``"composite_observations"``, ``"run_1"`` and
    ``"kraus_1972_very_clear"``). They are refused unless
    ``include_non_types=True`` is passed, so that one cannot be mistaken for
    a Jerlov type; their ``water_type`` is empty. See DATA.md section 14.
    """
    rows = _rows()
    for row in rows:
        if row["key"] == water_type:
            if row["status"] == "not_a_water_type" and not include_non_types:
                raise KeyError(
                    f"{water_type!r} is a row of Paulson & Simpson (1977) "
                    f"Table 2 but not a Jerlov water type: {row['note']}. "
                    "Pass include_non_types=True to get it anyway."
                )
            return ShortwaveParameters(
                key=row["key"],
                water_type=row["water_type"],
                R=float(row["R"]),
                zeta1_m=float(row["zeta1_m"]),
                zeta2_m=float(row["zeta2_m"]),
                fit_depth_m=(float(row["fit_depth_m"])
                             if row["fit_depth_m"] else None),
                note=row["note"],
            )
    available = [r["key"] for r in rows if r["status"] == "ok"]
    raise KeyError(
        f"Paulson & Simpson (1977) give no parameters for {water_type!r}. "
        f"They fitted the oceanic types only: {', '.join(available)}. "
        "The coastal types are not covered and this package will not "
        "substitute a neighbouring one."
    )


def solar_fraction(water_type: str, depth_m):
    """Fraction of surface solar irradiance surviving to ``depth_m``.

    Broadband, 300-2500 nm.

        >>> round(solar_fraction("IB", 10.0), 3)
        0.183

    Jerlov's own Table XXI gives 16.9 percent for IB at 10 m. The difference
    is expected: Paulson & Simpson fitted the table "neglecting the 10 m
    value", and say that "the fit is least accurate in the upper 10 m" and
    "could be improved by including the value at 10 m". They give no reason
    for leaving it out.
    """
    return shortwave_parameters(water_type).fraction_at(depth_m)


def jerlov1968_solar_fraction(
        water_type: str) -> tuple[np.ndarray, np.ndarray]:
    """Jerlov (1968) Table XXI: ``(depths_m, fraction)`` of surface irradiance.

    Broadband, 300-2500 nm, as measured and tabulated by Jerlov, for all ten
    types including the coastal ones. These are the values Paulson & Simpson
    fitted, for the oceanic types, to obtain :func:`shortwave_parameters`,
    so they are what to compare the fit against.

    ``fraction`` is 0 to 1, not percent. Depths the table leaves blank are
    kept, as NaN, so that a gap stays visible.

    The table's footnote gives the conditions: a solar altitude of 90
    degrees for the oceanic types and 45 degrees for the coastal ones. The
    Paulson & Simpson parameters, fitted to the oceanic columns, carry the
    first of these with them.
    """
    rows = [r for r in _data._rows("jerlov1968_total_irradiance.csv")
            if r["water_type"] == water_type]
    if not rows:
        known = sorted({
            r["water_type"]
            for r in _data._rows("jerlov1968_total_irradiance.csv")})
        raise KeyError(f"Table XXI has no water type {water_type!r} "
                       f"(known: {', '.join(known)})")
    rows.sort(key=lambda r: float(r["depth_m"]))
    depths = np.array([float(r["depth_m"]) for r in rows])
    fraction = np.array([float(r["percent_of_surface"]) / 100
                         if r["percent_of_surface"] else np.nan for r in rows])
    return depths, fraction


#: Lee, Du, Arnone, Liew and Penta (2005), J. Geophys. Res. 110, C09019,
#: Eq. (4): K_IR = [c0 + c1 / (c2 + z)^c3] (1 + c4 theta), theta in degrees.
LEE2005_KIR_COEFFICIENTS = (0.560, 2.304, 0.001, 0.65, 0.002)
#: The depths and suns Eq. (4) was fitted over (p. 3).
_KIR_DEPTH, _KIR_SUN = (0.01, 3.0), (0.0, 60.0)
_KIR_PAPER = "Lee et al. (2005, C09019)"


def _kir(depth, sun):
    c0, c1, c2, c3, c4 = LEE2005_KIR_COEFFICIENTS
    return (c0 + c1 / (c2 + depth) ** c3) * (1 + c4 * sun)


def _depths(depth_m) -> np.ndarray:
    depth = _finite(depth_m, "depth_m")
    if np.any(depth < 0):
        raise ValueError("depth_m must not be negative")
    return depth


@_data.positional_only()
def lee2005_kir(depth_m, /, *, sun_zenith_deg):
    """The attenuation of infrared solar energy, from the surface to a depth.

    Lee, Z., Du, K., Arnone, R., Liew, S. and Penta, B. (2005),
    "Penetration of solar radiation in the upper ocean: A numerical model
    for oceanic and coastal waters", J. Geophys. Res. 110, C09019,
    doi:10.1029/2004JC002780, Eq. (4)::

        K_IR(z) = [0.560 + 2.304 / (0.001 + z)^0.65] (1 + 0.002 theta)

    theta in degrees (``jerlov.shortwave.LEE2005_KIR_COEFFICIENTS``). E_IR(z) =
    E_IR(0) exp(-K_IR(z) z), E_IR the energy of 700-2500 nm, whose
    attenuation "is almost completely dominated by water absorption" (p.
    1): nothing of what is in the water enters.

    Parameters
    ----------
    depth_m:
        z, metres below the surface, not negative; a number or an array.
    sun_zenith_deg:
        theta, degrees, in [0, 90). No default.

    Returns
    -------
    K_IR(z), 1/m. A float if both inputs are numbers, an array otherwise.

    Notes
    -----
    Fitted for z of 0.01 to 3 m and the sun 0 to 60 degrees from the
    zenith (p. 3), with an average error of 3.0 percent; "for z deeper
    than 3 m, E_IR is negligible". Outside these a
    :class:`ProvenanceWarning` is given. DECISIONS.md section 98.
    """
    depth = _depths(depth_m)
    sun = _sun(sun_zenith_deg, _KIR_SUN, _KIR_PAPER)
    lo, hi = _KIR_DEPTH
    if np.any(depth < lo) or np.any(depth > hi):
        _warn(f"{_KIR_PAPER} fitted K_IR for depths of {lo:g} to {hi:g} m; "
              "some of these depths lie outside that.")
    return _result(_kir(depth, sun), depth, sun)


@_data.positional_only()
def lee2005_shortwave_transmittance(a490, bb490, depth_m, /, *,
                                    sun_zenith_deg, visible_fraction):
    """The share of the shortwave solar energy at the surface that is left
    at a depth.

    Lee et al. (2005, C09019; see :func:`lee2005_kir`), Eq. (11)::

        T(z) = F_VIS exp(-K_VIS(z) z) + (1 - F_VIS) exp(-K_IR(z) z)

    with K_VIS of :func:`lee2005_kvis` and K_IR of :func:`lee2005_kir`.

    Parameters
    ----------
    a490, bb490:
        As for :func:`lee2005_kvis`.
    depth_m:
        z, metres, not negative.
    sun_zenith_deg:
        degrees, in [0, 90). No default.
    visible_fraction:
        F_VIS = E_VIS(0) / E_SR(0), the share of 350-700 nm in the
        350-2500 nm energy just below the surface, one number in (0, 1).
        The paper gives "around 0.424 [Mobley, 1994]" (p. 7); it depends on
        the sun and the sky, so it has no default here.

    Returns
    -------
    T(z), 0 to 1. A float if every input is a number, an array otherwise.

    Notes
    -----
    The warnings of :func:`lee2005_kvis` apply. Those of
    :func:`lee2005_kir` apply above 0.01 m only (at z = 0, T is 1 by
    construction): below 3 m the paper calls E_IR negligible. DECISIONS.md
    section 98.
    """
    a, bb = _check_iops(a490, bb490)
    depth = _depths(depth_m)
    try:
        # isfinite has no answer for text, so "0.4" is refused too.
        ok = (np.ndim(visible_fraction) == 0
              and bool(np.isfinite(visible_fraction))
              and 0 < float(visible_fraction) < 1)
    except TypeError:
        ok = False
    if not ok:
        raise ValueError("visible_fraction must be one number in (0, 1), "
                         f"not {visible_fraction!r}")
    # K_VIS's sun (10-60 degrees) lies within K_IR's (0-60).
    sun = _sun(sun_zenith_deg, _KVIS_SUN, _KVIS_PAPER)
    k1, k2 = _kvis_k1_k2(a, bb, sun)
    kvis = k1 + k2 / np.sqrt(1 + depth)
    _kvis_check(np.asarray(kvis, dtype=float), depth)
    lo = _KIR_DEPTH[0]
    if np.any((depth > 0) & (depth < lo)):
        _warn(f"{_KIR_PAPER} fitted K_IR for depths of {lo:g} m and more; "
              "some of these depths lie above that.")
    f = float(visible_fraction)
    t = f * np.exp(-kvis * depth) + (1 - f) * np.exp(-_kir(depth, sun) * depth)
    return _result(t, a, bb, depth, sun)

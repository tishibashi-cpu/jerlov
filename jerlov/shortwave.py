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


def shortwave_parameters(water_type: str, *,
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


def jerlov1968_solar_fraction(water_type: str) -> tuple[np.ndarray, np.ndarray]:
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
        known = sorted({r["water_type"]
                        for r in _data._rows("jerlov1968_total_irradiance.csv")})
        raise KeyError(f"Table XXI has no water type {water_type!r} "
                       f"(known: {', '.join(known)})")
    rows.sort(key=lambda r: float(r["depth_m"]))
    depths = np.array([float(r["depth_m"]) for r in rows])
    fraction = np.array([float(r["percent_of_surface"]) / 100
                         if r["percent_of_surface"] else np.nan for r in rows])
    return depths, fraction

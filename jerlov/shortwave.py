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

from dataclasses import dataclass

import numpy as np

from . import _data
from .water import _like_input

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
    """Depth range the row was fitted over. Not printed in the table."""
    note: str

    def fraction_at(self, depth_m):
        """``I(z)/I(0)`` at one or more depths."""
        z = np.atleast_1d(np.asarray(depth_m, dtype=float))
        if np.any(z < 0):
            raise ValueError("depth_m cannot be negative")
        out = (self.R * np.exp(-z / self.zeta1_m)
               + (1 - self.R) * np.exp(-z / self.zeta2_m))
        return _like_input(out, depth_m)

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return (f"<ShortwaveParameters {self.key} R={self.R} "
                f"zeta1={self.zeta1_m} m zeta2={self.zeta2_m} m>")


def _rows():
    return _data._rows("paulson1977_shortwave.csv")


def shortwave_parameters(water_type: str) -> ShortwaveParameters:
    """Paulson & Simpson parameters for a Jerlov water type.

    Only the five oceanic types I, IA, IB, II and III were fitted; the paper
    covers no coastal type, and this raises rather than substituting one.

    ``water_type="I_upper50"`` selects the paper's alternative fit for type I
    over the upper 50 m, which it gives because ``ln I`` against depth changes
    slope below that. The plain ``"I"`` row is the 100 m fit.
    """
    rows = _rows()
    for row in rows:
        if row["key"] == water_type:
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
    is expected: Paulson & Simpson deliberately excluded the 10 m point from
    the fit, saying the two-exponential form does not capture the transition
    there.
    """
    return shortwave_parameters(water_type).fraction_at(depth_m)

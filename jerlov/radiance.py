"""A measured radiance distribution: Tyler (1958), Lake Pend Oreille.

The radiance from every direction at seven depths in a deep lake Tyler
judged homogeneous, under a clear sky, as he tabulated it. The package does
not compute radiance distributions (DECISIONS.md sections 12 and 38); this
is the measurement one can be compared with.
``examples/radiance_distribution.py`` does.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass

import numpy as np

from . import _data
from .water import ProvenanceWarning

TYLER1958_DEPTHS = (4.24, 10.4, 16.6, 29.0, 41.3, 53.7, 66.1)
"""The depths of Tyler's Tables IV to X, m, as the tables print them."""


@dataclass(frozen=True, eq=False, repr=False)
class RadianceDistribution:
    """Tyler's radiance distribution at one depth.

    Built by :func:`tyler1958_radiance`. ``radiance[i, j]`` is the radiance
    seen looking at tilt ``tilt_deg[i]`` from straight up (0 up, 180 down)
    and azimuth ``azimuth_deg[j]`` from the sun's, in one relative unit
    shared by all seven depths. The distribution is taken as symmetric
    about the sun's vertical plane, as Tyler tabulated only one side.
    """

    depth_m: float
    tilt_deg: np.ndarray
    azimuth_deg: np.ndarray
    radiance: np.ndarray
    suspect: tuple[str, ...]
    """The cells marked suspect, with the reason: DATA.md section 23."""
    sun_altitude_deg: float = 56.6
    """The sun altitude every table is adjusted to (pp. 14-15)."""
    band_nm: tuple[float, float] = (430.0, 546.0)
    """The extreme limits of the measured band; its half width is 64 nm
    (p. 5)."""
    beam_attenuation: float = -math.log(0.673)
    """c, 1/m: beam transmittance 67.3 percent per metre at the surface,
    29 April 1957 (p. 8). The transmissometer's band is not given."""
    acceptance_deg: float = 6.6
    """The radiance tubes' full angle of acceptance (p. 7)."""

    def __repr__(self) -> str:
        flag = f"; {len(self.suspect)} suspect" if self.suspect else ""
        return (f"<RadianceDistribution Tyler 1958, {self.depth_m:g} m, "
                f"{self.tilt_deg.size} tilts x {self.azimuth_deg.size} "
                f"azimuths{flag}>")


def tyler1958_radiance(depth_m: float) -> RadianceDistribution:
    """Tyler's measured radiance distribution at one of his seven depths.

    Tyler, J. E. (1958), "Radiance distribution as a function of depth in
    the submarine environment", SIO Reference 58-25, Visibility Laboratory,
    Scripps Institution of Oceanography, Tables IV-X. Lake Pend Oreille,
    Idaho, 28 April 1957, clear sky, sun altitude 56.6 degrees.

    ``depth_m`` is one of :data:`TYLER1958_DEPTHS`. Nothing is
    interpolated between them.

    Notes
    -----
    The report warns that the reading in the sun's direction "could be low
    by a factor of 2 in the worst case" (p. 16), from the glitter of the
    sun on the surface, whose noise Table XI gives down to 28.95 m. Those
    cells, at the four depths it lists, are marked suspect, as is one cell
    with an overstruck digit at 4.24 m; asking for a depth that has any
    warns. The measurement includes the clear sky's light and the barge's
    shadow, which Tyler read around (pp. 12-13).
    """
    rows = [r for r in _data._rows("tyler1958_radiance.csv")
            if float(r["depth_m"]) == float(depth_m)]
    if not rows:
        raise KeyError(f"Tyler (1958) has no table at {depth_m!r} m (known: "
                       f"{', '.join(f'{d:g}' for d in TYLER1958_DEPTHS)})")
    tilts = sorted({float(r["tilt_deg"]) for r in rows})
    azimuths = sorted({float(r["azimuth_deg"]) for r in rows})
    radiance = np.empty((len(tilts), len(azimuths)))
    suspect = []
    for r in rows:
        i = tilts.index(float(r["tilt_deg"]))
        j = azimuths.index(float(r["azimuth_deg"]))
        radiance[i, j] = float(r["value"])
        if r["status"] in _data.QUESTIONABLE:
            suspect.append(f"tilt {float(r['tilt_deg']):g}, azimuth "
                           f"{float(r['azimuth_deg']):g}: {r['note']}")
    if suspect:
        warnings.warn(
            f"Tyler's table at {float(depth_m):g} m has {len(suspect)} "
            "suspect cell(s): " + "; ".join(suspect)
            + ". See DATA.md section 23.",
            ProvenanceWarning,
            stacklevel=_data.caller_stacklevel(),
        )
    return RadianceDistribution(
        depth_m=float(depth_m),
        tilt_deg=_data._frozen(np.array(tilts)),
        azimuth_deg=_data._frozen(np.array(azimuths)),
        radiance=_data._frozen(radiance),
        suspect=tuple(suspect),
    )

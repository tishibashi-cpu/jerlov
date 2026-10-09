"""Photosynthetically available radiation down through the water column.

PAR is the photon flux between 400 and 700 nm. Given a downwelling
spectrum just below the surface and a Kd for every wavelength, each
wavelength is attenuated on its own and the result integrated::

    PAR(z) = integral over 400-700 nm of Eq(0, lambda) exp(-tau(z, lambda))

where ``Eq`` is the spectrum in photons and ``tau`` the optical depth: ``Kd z``
for one Kd, or the layer-by-layer sum of :func:`~jerlov.descend`. Because
the blue-green survives and the red does not, PAR does not fall off
exponentially with any single coefficient, and the depth at which it reaches
1 percent of its surface value is not ``ln(100) / Kd`` at any one wavelength.

Three things are stated rather than hidden:

- **This is planar PAR.** It integrates the downwelling *planar* irradiance
  Ed. PAR is often defined on scalar irradiance E0, which counts light from
  every direction equally and is larger, by a factor that depends on the
  light field and is not determined here.
- **The surface spectrum is the caller's.** No solar spectrum is assumed:
  the sky, the sun's elevation and the surface all change it.
- **The Kd of a type is applied unchanged with depth**, as in
  :meth:`Scene.at_depth <jerlov.Scene.at_depth>`, or layer by layer, as in
  :func:`~jerlov.descend`. Both are approximations.
"""

from __future__ import annotations

import numpy as np

from . import _data
from .water import Descent, MissingQuantityError, Water, _require_number

#: Planck constant (J s), speed of light (m/s) and Avogadro constant (1/mol),
#: exact by the 2019 definition of the SI.
_H = 6.62607015e-34
_C = 299792458.0
_NA = 6.02214076e23

PAR_RANGE_NM = (400.0, 700.0)
"""The waveband of PAR, nm."""

_UNITS = {
    "energy": "W m-2 nm-1",
    "photons": "umol m-2 s-1 nm-1",
}


def _photons(spectrum: np.ndarray, wavelengths: np.ndarray, unit: str):
    """Spectral irradiance in umol photons m-2 s-1 nm-1."""
    if unit == "photons":
        return spectrum
    # E / (h c / lambda) photons per second, / N_A for moles, * 1e6 for umol.
    return spectrum * wavelengths * 1e-9 / (_H * _C) / _NA * 1e6


class ParProfile:
    """PAR at a set of depths, and the depth at which it falls to a fraction.

    Built by :func:`par_profile`. ``par`` is in umol photons m-2 s-1, whatever
    unit the surface spectrum was given in.
    """

    __slots__ = ("depths_m", "par", "surface_par", "kd_from", "_band",
                 "_surface_q", "_tau", "_deepest")

    def __init__(self, depths_m, band, surface_q, tau, deepest, kd_from):
        self._band = band
        self._surface_q = surface_q
        self._tau = tau
        self._deepest = deepest
        self.kd_from = kd_from
        """What the Kd came from, in words."""
        self.surface_par = self._par_at(0.0)
        """PAR just below the surface, umol photons m-2 s-1."""
        self.depths_m = depths_m
        """The depths asked for, m."""
        self.par = np.array([self._par_at(z) for z in depths_m.ravel()]
                            ).reshape(depths_m.shape)
        """PAR at each depth, umol photons m-2 s-1."""
        for array in (self.depths_m, self.par):
            array.setflags(write=False)

    def _par_at(self, depth: float) -> float:
        return float(_data.trapezoid(
            self._surface_q * np.exp(-self._tau(depth)), self._band))

    @property
    def fraction(self) -> np.ndarray:
        """``PAR(z) / PAR(0)``, 0 to 1. NaN if there is no light at the
        surface."""
        return np.divide(self.par, self.surface_par,
                         out=np.full_like(self.par, np.nan),
                         where=self.surface_par != 0)

    def depth_of_fraction(self, fraction: float = 0.01) -> float:
        """The depth, in m, at which PAR falls to ``fraction`` of its surface value.

        The default, 1 percent, is the usual convention for the bottom of
        the euphotic zone. It is a convention: phytoplankton grow below it,
        and in clear water a good deal below it.

        Raises
        ------
        MissingQuantityError
            If the Kd came from a :class:`~jerlov.Descent` and PAR has not
            fallen that far by the bottom of it. Descend further, or, if
            the descent cannot go further, there is no answer here: the
            typical profile says nothing about the water below.
        """
        _require_number(fraction, "fraction")
        fraction = float(fraction)
        if not 0.0 < fraction < 1.0:
            raise ValueError("fraction must lie strictly between 0 and 1")
        if self.surface_par == 0:
            raise ValueError("there is no PAR at the surface to take a fraction of")
        target = fraction * self.surface_par

        low, high = 0.0, 1.0
        if self._deepest is not None:
            high = self._deepest
            if self._par_at(high) > target:
                raise MissingQuantityError(
                    f"PAR is still {self._par_at(high) / self.surface_par:.2%} "
                    f"of its surface value at {high:g} m, the bottom of the "
                    f"descent, so the depth of {fraction:.2%} is below it"
                )
        else:
            while self._par_at(high) > target:
                low, high = high, high * 2.0
                if high > 1e6:
                    raise ValueError(
                        f"PAR does not fall to {fraction:.2%} within 1000 km; "
                        "Kd is zero or close to it throughout 400-700 nm"
                    )
        # PAR falls monotonically with depth, so bisection cannot miss.
        for _ in range(100):
            middle = 0.5 * (low + high)
            if self._par_at(middle) > target:
                low = middle
            else:
                high = middle
            if high - low < 1e-9 * max(high, 1.0):
                break
        return 0.5 * (low + high)

    def __repr__(self) -> str:
        return (
            f"<ParProfile surface {self.surface_par:.4g} umol m-2 s-1, "
            f"{self.depths_m.size} depth{'s' if self.depths_m.size != 1 else ''}; "
            f"Kd from {self.kd_from}>"
        )


def par_profile(surface_downwelling, wavelengths, depths_m, *, kd,
                unit: str) -> ParProfile:
    """PAR at ``depths_m`` below a surface downwelling spectrum.

    Parameters
    ----------
    surface_downwelling:
        Downwelling planar irradiance just below the surface, on
        ``wavelengths``.
    wavelengths:
        nm, ascending, covering at least 400 to 700 nm. Values between the
        samples are interpolated linearly at 400 and 700 nm.
    depths_m:
        A depth or an array of depths, in m.
    kd:
        A :class:`~jerlov.Water` carrying Kd, such as
        ``jerlov.water("II", source="jerlov1976")``, or an array on
        ``wavelengths``; either is applied unchanged with depth. Or a
        :class:`~jerlov.Descent` on the same wavelengths, which changes the
        type layer by layer and stops at the descent's depth.
    unit:
        ``"energy"`` if the spectrum is in W m-2 nm-1, ``"photons"`` if it
        is in umol m-2 s-1 nm-1. There is no default: PAR counts photons,
        and an energy spectrum read as photons would weight the blue and
        the red wrongly without any sign that it had.

    Example
    -------
    ::

        d = jerlov.descend("I", 200.0, wl)
        p = jerlov.par_profile(surface, wl, [0, 50, 100], kd=d, unit="energy")
        p.fraction                 # PAR(z) / PAR(0) at each depth
        p.depth_of_fraction(0.01)  # the 1 percent depth, m

    See the module docstring for what this assumes.
    """
    if unit not in _UNITS:
        raise ValueError(
            f"unit must be one of {', '.join(map(repr, sorted(_UNITS)))} "
            f"({'; '.join(f'{k}: {v}' for k, v in sorted(_UNITS.items()))})"
        )
    wl = np.array(wavelengths, dtype=float, ndmin=1)
    if wl.ndim != 1 or not np.all(np.isfinite(wl)) or np.any(np.diff(wl) <= 0):
        raise ValueError("wavelengths must be finite and strictly ascending")
    lo, hi = PAR_RANGE_NM
    if wl[0] > lo or wl[-1] < hi:
        raise ValueError(
            f"wavelengths cover {wl[0]:g}-{wl[-1]:g} nm; PAR needs "
            f"{lo:g}-{hi:g} nm, and the rest of the band is not extrapolated"
        )
    surface = np.array(surface_downwelling, dtype=float)
    if surface.shape != wl.shape:
        raise ValueError(
            "surface_downwelling must have the same shape as wavelengths")
    if np.any(surface < 0) or np.any(np.isinf(surface)):
        # NaN, a gap, passes here and is refused below only if PAR rests on it.
        raise ValueError(
            "downwelling irradiance must be finite and not negative")

    # Only the samples that PAR rests on: those inside 400-700 nm and the
    # one either side of each end. Kd is evaluated on these alone, so that
    # a spectrum running past the Kd table, or a flagged Kd beyond 700 nm,
    # neither refuses nor warns about light that PAR does not count.
    near = np.zeros(wl.shape, dtype=bool)
    near[np.searchsorted(wl, lo, side="right") - 1:
         np.searchsorted(wl, hi, side="left") + 1] = True
    sub_wl = wl[near]

    depths = np.array(depths_m, dtype=float)
    if not np.all(np.isfinite(depths)):
        raise ValueError("depths_m must be finite numbers")
    if np.any(depths < 0):
        raise ValueError("depths_m cannot be negative")

    deepest = None
    if isinstance(kd, Descent):
        if not np.array_equal(kd.wavelengths, wl):
            raise ValueError(
                "the descent was computed on other wavelengths; pass the "
                "same wavelengths to descend() and par_profile()"
            )
        deepest = kd.depth_m
        if np.any(depths > deepest):
            raise MissingQuantityError(
                f"the descent stops at {deepest:g} m, above the deepest depth "
                f"asked for ({depths.max():g} m)"
            )
        if len(kd._kd) != len(kd.layers):
            raise MissingQuantityError(
                "this Descent was not made by descend(), so it does not "
                "carry the Kd of its layers"
            )
        kd_from = (f"a descent from Jerlov {kd.surface_water_type} "
                   f"({kd.source})")
        descent = kd

        def optical_depth(z):
            # The descent's own layers, on the samples PAR rests on only.
            return descent._optical_depth(z, near)

        kd_values = (np.vstack([v[near] for v in kd._kd]) if kd._kd
                     else np.zeros_like(sub_wl))
    else:
        if isinstance(kd, Water):
            kd_values = np.asarray(kd.kd(sub_wl), dtype=float)
            kd_from = f"Jerlov {kd.name}" if kd.name else "the given water"
            if kd.source is not None:
                kd_from += f" ({kd.source.key})"
        else:
            kd_values = np.array(kd, dtype=float)
            kd_from = "the given Kd"
            if kd_values.shape != wl.shape:
                raise ValueError("kd must have the same shape as wavelengths")
            kd_values = kd_values[near]
        if np.any(kd_values < 0) or np.any(np.isinf(kd_values)):
            # inf times a depth of 0 is NaN, so PAR at the surface came out
            # NaN with only a NumPy RuntimeWarning.
            raise ValueError("kd must be finite and not negative")

        def optical_depth(z):
            return kd_values * z

    # The band: every sample inside 400-700 nm, plus the two ends.
    inside = (wl > lo) & (wl < hi)
    band = np.concatenate(([lo], wl[inside], [hi]))
    for name, values in (("surface_downwelling", surface[near]),
                         ("Kd", kd_values)):
        if np.any(np.isnan(values)):
            raise MissingQuantityError(
                f"{name} has a gap between {lo:g} and {hi:g} nm, so PAR, "
                "which integrates over all of it, is not determined"
            )
    surface_q = np.interp(band, sub_wl,
                          _photons(surface[near], sub_wl, unit))

    def tau(z):
        return np.interp(band, sub_wl, optical_depth(z))

    return ParProfile(depths, band, surface_q, tau, deepest, kd_from)

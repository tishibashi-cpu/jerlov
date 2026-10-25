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

The band is 400-700 nm unless the caller names another with ``band=``:
Jerlov's quanta meters counted 350-700 nm (:data:`QUANTA_BAND_NM`), and a
share of PAR is the same integral over part of it. Outside 400-700 nm the
result is a photon flux over that band, not PAR, though the attribute
keeps the name ``par``.

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

import warnings
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from . import _data
from .water import (
    Descent,
    MissingQuantityError,
    ProvenanceWarning,
    Water,
    _require_number,
)

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
    unit the surface spectrum was given in, integrated over
    :attr:`band_nm`: PAR when that is 400-700 nm, the photon flux in that
    band otherwise.
    """

    __slots__ = ("depths_m", "par", "surface_par", "kd_from", "band_nm",
                 "weighted", "wavelengths_nm", "_grid", "_surface_q",
                 "_weight", "_tau", "_deepest", "_shifted")

    def __init__(self, depths_m, band_nm, grid, surface_q, tau, deepest,
                 kd_from, weight=None, shifted=None):
        self.band_nm = band_nm
        self.weighted = weight is not None
        """True if ``par`` was integrated against a ``photon_weight``."""
        self._weight = np.ones_like(grid) if weight is None else weight
        """``(lo, hi)``, nm: the band integrated over."""
        self._grid = grid
        self.wavelengths_nm = grid.copy()
        """The wavelengths integrated over, nm: every sample inside
        :attr:`band_nm` and its two ends. :meth:`spectrum_at` is on these."""
        self.wavelengths_nm.setflags(write=False)
        self._surface_q = surface_q
        self._tau = tau
        self._deepest = deepest
        self._shifted = shifted
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

    def _par_at(self, depth: float, tau=None) -> float:
        tau = self._tau if tau is None else tau
        return float(_data.trapezoid(
            self._weight * self._surface_q * np.exp(-tau(depth)),
            self._grid))

    def _depth(self, depth_m, name: str) -> float:
        """One depth, checked against what the profile can answer."""
        _require_number(depth_m, name)
        depth = float(depth_m)
        if not np.isfinite(depth):
            raise ValueError(f"{name} must be finite, not {depth_m!r}")
        if depth < 0:
            raise ValueError(f"{name} cannot be negative")
        if self._deepest is not None and depth > self._deepest:
            raise MissingQuantityError(
                f"the descent stops at {self._deepest:g} m, above {name} "
                f"= {depth:g} m; descend further to go deeper"
            )
        return depth

    def spectrum_at(self, depth_m) -> np.ndarray:
        """The downwelling spectrum at ``depth_m``, in umol photons m-2 s-1
        nm-1, on :attr:`wavelengths_nm`.

        Photons whatever unit the surface spectrum was given in, since that
        is what :attr:`par` integrates. A single depth gives one spectrum;
        an array of depths gives one row per depth. ``par`` at a depth is
        the trapezoid integral of this over :attr:`wavelengths_nm`, times
        the ``photon_weight`` if one was given; the spectrum itself is not
        weighted.

        Raises
        ------
        MissingQuantityError
            Below the bottom of a :class:`~jerlov.Descent`.
        """
        depths = np.asarray(depth_m, dtype=float)
        if depths.ndim > 1:
            raise ValueError(
                "depth_m must be a depth or a 1-D array of depths")
        rows = [self._surface_q * np.exp(-self._tau(self._depth(z, "depth_m")))
                for z in np.atleast_1d(depths)]
        return rows[0] if depths.ndim == 0 else np.array(rows)

    def kd_par(self, z1_m, z2_m) -> float:
        """The effective Kd of PAR between two depths, 1/m:
        ``ln(PAR(z1) / PAR(z2)) / (z2 - z1)``.

        PAR does not fall off with one coefficient, so this depends on the
        two depths, not only on the water: near the surface it is larger,
        while the red is still being removed. Over a band other than
        400-700 nm it is the same quantity for that band.

        Raises
        ------
        ValueError
            Unless ``z1_m < z2_m``, or if there is no light at either depth.
        MissingQuantityError
            Below the bottom of a :class:`~jerlov.Descent`.
        """
        z1, z2 = self._depth(z1_m, "z1_m"), self._depth(z2_m, "z2_m")
        if not z1 < z2:
            raise ValueError(
                f"z1_m must be above z2_m, not {z1:g} and {z2:g} m")
        top, bottom = self._par_at(z1), self._par_at(z2)
        if top <= 0 or bottom <= 0:
            raise ValueError(
                f"there is no light at {z1 if top <= 0 else z2:g} m to take "
                "a ratio of"
            )
        return float(np.log(top / bottom) / (z2 - z1))

    @property
    def fraction(self) -> np.ndarray:
        """``PAR(z) / PAR(0)``, 0 to 1. NaN if there is no light at the
        surface."""
        return np.divide(self.par, self.surface_par,
                         out=np.full_like(self.par, np.nan),
                         where=self.surface_par != 0)

    def depth_of_fraction(self, fraction: float = 0.01) -> float:
        """The depth, in m, at which PAR falls to ``fraction`` of its
        surface value.

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
        return self._depth_of(fraction, self._tau)

    def _depth_of(self, fraction, tau) -> float:
        _require_number(fraction, "fraction")
        fraction = float(fraction)
        if not 0.0 < fraction < 1.0:
            raise ValueError("fraction must lie strictly between 0 and 1")
        if self.surface_par == 0:
            raise ValueError(
                "there is no PAR at the surface to take a fraction of")
        target = fraction * self.surface_par

        low, high = 0.0, 1.0
        if self._deepest is not None:
            high = self._deepest
            if self._par_at(high) > target:
                raise MissingQuantityError(
                    f"PAR is still "
                    f"{self._par_at(high) / self.surface_par:.2%} "
                    f"of its surface value at {high:g} m, the bottom of the "
                    f"descent, so the depth of {fraction:.2%} is below it"
                )
        else:
            while self._par_at(high, tau) > target:
                low, high = high, high * 2.0
                if high > 1e6:
                    raise ValueError(
                        f"PAR does not fall to {fraction:.2%} within 1000 km; "
                        "Kd is zero or close to it throughout "
                        f"{self.band_nm[0]:g}-{self.band_nm[1]:g} nm"
                    )
        # PAR falls monotonically with depth, so bisection cannot miss.
        for _ in range(100):
            middle = 0.5 * (low + high)
            if self._par_at(middle, tau) > target:
                low = middle
            else:
                high = middle
            if high - low < 1e-9 * max(high, 1.0):
                break
        return 0.5 * (low + high)

    def _taus(self, k) -> tuple:
        """The optical depth with Kd plus and minus k uncertainties."""
        _require_number(k, "k")
        k = float(k)
        if not np.isfinite(k) or k < 0:
            raise ValueError("k must be a finite number, not negative")
        if isinstance(self._shifted, str):
            raise MissingQuantityError(self._shifted)
        return self._shifted(k)

    def depth_of_fraction_bounds(self, fraction: float = 0.01, *,
                                 k: float = 1.0) -> tuple[float, float]:
        """The depth of ``fraction`` with Kd shifted by ``k`` standard
        uncertainties at every wavelength together: ``(shallower, deeper)``,
        in m.

        The errors are taken as fully correlated between wavelengths, so
        this is the widest range any errors within ``k`` uncertainties at
        every wavelength can give, and exactly plus and minus ``k`` standard
        deviations if they are fully correlated and normal. DECISIONS.md
        section 57.

        Raises
        ------
        MissingQuantityError
            If the Kd carries no uncertainty, as no published type does, or
            has a gap in it within the band.
        ValueError
            If Kd minus ``k`` uncertainties is negative anywhere in the band.
        """
        more, less = self._taus(k)
        return self._depth_of(fraction, more), self._depth_of(fraction, less)

    def par_bounds(self, *, k: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
        """``(lower, higher)`` PAR at :attr:`depths_m`, with Kd shifted by
        ``k`` standard uncertainties at every wavelength together, as in
        :meth:`depth_of_fraction_bounds`. The surface has no range: PAR
        there does not depend on Kd."""
        more, less = self._taus(k)

        def at_depths(tau) -> np.ndarray:
            return np.array([self._par_at(z, tau)
                             for z in self.depths_m.ravel()]
                            ).reshape(self.depths_m.shape)

        return at_depths(more), at_depths(less)

    def __repr__(self) -> str:
        lo, hi = self.band_nm
        band = ("" if self.band_nm == PAR_RANGE_NM
                else f" over {lo:g}-{hi:g} nm")
        if self.weighted:
            band += ", weighted"
        return (
            f"<ParProfile surface {self.surface_par:.4g} umol m-2 s-1{band}, "
            f"{self.depths_m.size} "
            f"depth{'s' if self.depths_m.size != 1 else ''}; "
            f"Kd from {self.kd_from}>"
        )


def par_profile(surface_downwelling, wavelengths, depths_m, *, kd,
                unit: str, band=PAR_RANGE_NM,
                photon_weight=None, kd_uncertainty=None) -> ParProfile:
    """PAR at ``depths_m`` below a surface downwelling spectrum.

    Parameters
    ----------
    surface_downwelling:
        Downwelling planar irradiance just below the surface, on
        ``wavelengths``.
    wavelengths:
        nm, ascending, covering at least ``band``. Values between the
        samples are interpolated linearly at its two ends.
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
    band:
        ``(lo, hi)``, nm, the band to integrate over. 400-700 nm, the
        definition of PAR, by default. Another band gives the photon flux
        in it: :data:`QUANTA_BAND_NM` for Jerlov's quanta meters, or part
        of PAR for the share of one colour. Nothing outside it counts,
        so the spectrum and Kd may have gaps there.
    photon_weight:
        Optional, on ``wavelengths``: a weight for each photon by its
        wavelength, such as the absorption spectrum of a pigment or the
        quantum sensitivity of a photoreceptor. ``par`` is then the
        integral of the photon spectrum times the weight, in the weight's
        units times umol m-2 s-1, and :meth:`ParProfile.depth_of_fraction`
        and :meth:`ParProfile.kd_par` follow it. Finite and not negative
        inside the band; its scale cancels from every fraction. A response
        per unit energy, as a thermopile's, is not a photon weight: divide
        it by the wavelength first, since a photon of wavelength l carries
        an energy proportional to 1 / l.
    kd_uncertainty:
        Optional, on ``wavelengths``, beside an array ``kd``: the standard
        uncertainty of Kd, 1/m. A :class:`~jerlov.Water` built with
        ``uncertainty={"kd": ...}`` carries its own and takes none here.
        It is used only by :meth:`ParProfile.depth_of_fraction_bounds` and
        :meth:`ParProfile.par_bounds`, which take the errors as fully
        correlated between wavelengths (DECISIONS.md section 57).

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
    band_nm = _band(band)
    wl = np.array(wavelengths, dtype=float, ndmin=1)
    if wl.ndim != 1 or not np.all(np.isfinite(wl)) or np.any(np.diff(wl) <= 0):
        raise ValueError("wavelengths must be finite and strictly ascending")
    lo, hi = band_nm
    if wl[0] > lo or wl[-1] < hi:
        what = "PAR" if band_nm == PAR_RANGE_NM else "the band"
        raise ValueError(
            f"wavelengths cover {wl[0]:g}-{wl[-1]:g} nm; {what} needs "
            f"{lo:g}-{hi:g} nm, and what is missing is not extrapolated"
        )
    surface = np.array(surface_downwelling, dtype=float)
    if surface.shape != wl.shape:
        raise ValueError(
            "surface_downwelling must have the same shape as wavelengths")
    if np.any(surface < 0) or np.any(np.isinf(surface)):
        # NaN, a gap, passes here and is refused below only if the band
        # rests on it.
        raise ValueError(
            "downwelling irradiance must be finite and not negative")

    # Only the samples the band rests on: those inside it and the one
    # either side of each end. Kd is evaluated on these alone, so that a
    # spectrum running past the Kd table, or a flagged Kd beyond the band,
    # neither refuses nor warns about light that is not counted.
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
    sigma: np.ndarray | None = None
    no_range = ""
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
            # The descent's own layers, on the samples the band rests on only.
            return descent._optical_depth(z, near)

        kd_values = (np.vstack([v[near] for v in kd._kd]) if kd._kd
                     else np.zeros_like(sub_wl))
        if kd_uncertainty is not None:
            raise ValueError(
                "kd_uncertainty goes with an array kd; the Kd of a descent "
                "is from published types, which publish no uncertainty")
        no_range = ("the Kd of a descent is from published types, which "
                    "publish no uncertainty; build a Water from your own "
                    "measurements with one to get a range")
    else:
        if isinstance(kd, Water):
            kd_values = np.asarray(kd.kd(sub_wl), dtype=float)
            kd_from = f"Jerlov {kd.name}" if kd.name else "the given water"
            if kd.source is not None:
                kd_from += f" ({kd.source.key})"
            if kd_uncertainty is not None:
                raise ValueError(
                    "kd_uncertainty goes with an array kd; a Water carries "
                    "its own: Water.from_measurements(..., "
                    "uncertainty={'kd': ...})")
            try:
                sigma = np.asarray(kd.uncertainty("kd", sub_wl), dtype=float)
            except MissingQuantityError as error:
                no_range = f"{error}, so Kd has no range"
        else:
            kd_values = np.array(kd, dtype=float)
            kd_from = "the given Kd"
            if kd_values.shape != wl.shape:
                raise ValueError("kd must have the same shape as wavelengths")
            kd_values = kd_values[near]
            if kd_uncertainty is None:
                no_range = "no kd_uncertainty was given, so Kd has no range"
            else:
                given = np.array(kd_uncertainty, dtype=float)
                if given.shape != wl.shape:
                    raise ValueError(
                        "kd_uncertainty must have the same shape as "
                        "wavelengths")
                sigma = given[near]
        if sigma is not None and (
                np.any(sigma < 0) or np.any(np.isinf(sigma))):
            raise ValueError(
                "the uncertainty of Kd must be finite and not negative "
                "(NaN marks a gap)")
        if np.any(kd_values < 0) or np.any(np.isinf(kd_values)):
            # inf times a depth of 0 is NaN, so PAR at the surface came out
            # NaN with only a NumPy RuntimeWarning.
            raise ValueError("kd must be finite and not negative")

        def optical_depth(z):
            return kd_values * z

    # The grid: every sample inside the band, plus its two ends.
    inside = (wl > lo) & (wl < hi)
    grid = np.concatenate(([lo], wl[inside], [hi]))
    for name, values in (("surface_downwelling", surface[near]),
                         ("Kd", kd_values)):
        if np.any(np.isnan(values)):
            raise MissingQuantityError(
                f"{name} has a gap between {lo:g} and {hi:g} nm, so the "
                "photon flux, which integrates over all of it, is not "
                "determined"
            )
    surface_q = np.interp(grid, sub_wl,
                          _photons(surface[near], sub_wl, unit))
    weight = None
    if photon_weight is not None:
        values = np.array(photon_weight, dtype=float)
        if values.shape != wl.shape:
            raise ValueError(
                "photon_weight must have the same shape as wavelengths")
        values = values[near]
        if np.any(np.isnan(values)):
            raise MissingQuantityError(
                f"photon_weight has a gap between {lo:g} and {hi:g} nm, so "
                "the weighted flux, which integrates over all of it, is not "
                "determined"
            )
        if np.any(np.isinf(values)) or np.any(values < 0):
            raise ValueError("photon_weight must be finite and not negative")
        weight = np.interp(grid, sub_wl, values)

    def tau(z):
        return np.interp(grid, sub_wl, optical_depth(z))

    shifted: str | Callable
    if sigma is None:
        shifted = no_range
    else:
        def shifted(k):
            if np.any(np.isnan(sigma)):
                raise MissingQuantityError(
                    f"the uncertainty of Kd has a gap between {lo:g} and "
                    f"{hi:g} nm, so its effect on the integral over all of "
                    "it is not determined")
            more, less = kd_values + k * sigma, kd_values - k * sigma
            if np.any(less < 0):
                worst = sub_wl[np.argmin(less)]
                raise ValueError(
                    f"Kd minus {k:g} uncertainties is negative at "
                    f"{worst:g} nm: the uncertainty is larger than the "
                    "value, and a Kd below zero cannot be")
            return (lambda z: np.interp(grid, sub_wl, more * z),
                    lambda z: np.interp(grid, sub_wl, less * z))

    return ParProfile(depths, band_nm, grid, surface_q, tau, deepest,
                      kd_from, weight, shifted)


def _band(band) -> tuple[float, float]:
    """``(lo, hi)`` as two floats, lo below hi, both finite and positive."""
    try:
        values = np.array(band, dtype=float)
    except (TypeError, ValueError):
        raise ValueError(
            f"band must be (lo, hi) in nm, not {band!r}") from None
    if values.shape != (2,):
        raise ValueError(f"band must be (lo, hi) in nm, not {band!r}")
    _require_number(values, "band")
    lo, hi = float(values[0]), float(values[1])
    if not (np.isfinite(lo) and np.isfinite(hi)) or lo <= 0 or hi <= lo:
        raise ValueError(
            f"band must be (lo, hi) with 0 < lo < hi, finite, not {band!r}")
    return lo, hi


QUANTA_BAND_NM = (350.0, 700.0)
"""The waveband of Jerlov's quanta meters, nm. Not that of PAR."""


@dataclass(frozen=True, eq=False, repr=False)
class QuantaLevels:
    """Jerlov's measured profiles of quanta irradiance for one water type.

    Built by :func:`jerlov1977_quanta`. Every depth is in m, every
    coefficient in 1/m, and the band is 350-700 nm, :data:`QUANTA_BAND_NM`,
    not the 400-700 nm of PAR. To compare, pass ``band=QUANTA_BAND_NM`` to
    :func:`par_profile`.
    """

    water_type: str
    level_percent: tuple[float, ...]
    """30, 10, 3 and 1: the levels of Table 2."""
    level_depth_m: np.ndarray
    """The depth of each level, Table 2."""
    profile_depth_m: np.ndarray
    """Table 3's depths, as far as the table goes for this type."""
    profile_percent: np.ndarray
    """Percent of surface quanta at :attr:`profile_depth_m`, Table 3."""
    layer_m: tuple[tuple[float, float], ...]
    """``(top, bottom)`` of each layer of Table 5."""
    layer_kd: np.ndarray
    """Kd for quanta in each layer, Table 5."""
    suspect: tuple[str, ...]
    """The layers of :attr:`layer_kd` whose printed Kd does not follow from
    Table 3, even allowing for rounding; DATA.md section 22."""

    def __repr__(self) -> str:
        levels = ", ".join(f"{p:g}% {z:g} m" for p, z in
                           zip(self.level_percent, self.level_depth_m))
        flag = f"; {len(self.suspect)} suspect" if self.suspect else ""
        return f"<QuantaLevels {self.water_type}: {levels}{flag}>"


def jerlov1977_quanta(water_type: str) -> QuantaLevels:
    """Jerlov's measured quanta irradiance, 350-700 nm, by water type.

    From profiles measured with quanta meters in fourteen regions, Jerlov
    tabulated the depth at which 30, 10, 3 and 1 percent of the surface
    quanta remain (Table 2), the percentage at depth (Table 3) and Kd for
    quanta layer by layer (Table 5), for types I, IA, IB, II, III, 1C and 3C.
    They are measurements, so they are what to compare :func:`par_profile`
    against; DATA.md section 22 does, and finds agreement within 2 m at
    every level from II to 3C, and a 1 percent depth 33 percent too deep
    for IB.

    Jerlov, N. G. (1977), "Classification of sea water in terms of quanta
    irradiance", J. Cons. int. Explor. Mer 37(3), 281-287,
    doi:10.1093/icesjms/37.3.281.

    Notes
    -----
    The band is 350-700 nm, wider than PAR's. The profiles are of real
    water at real stations, so they include whatever changed with depth
    there; Jerlov says so himself (p. 286). Three of the Kd values in Table
    5 do not follow from Table 3, even allowing for rounding: for IA, II
    and 1C, one layer each. They are listed in :attr:`QuantaLevels.suspect`,
    and asking for those types warns. Table 2's normalised column and Table
    4, which have five more such values, are in the shipped table
    ``jerlov1977_quanta.csv`` but not returned here, since both follow from
    the depths that are.
    """
    rows = [r for r in _data._rows("jerlov1977_quanta.csv")
            if r["water_type"] == water_type]
    if not rows:
        known = []
        for r in _data._rows("jerlov1977_quanta.csv"):
            if r["water_type"] not in known:
                known.append(r["water_type"])
        raise KeyError(f"Jerlov's quanta tables have no water type "
                       f"{water_type!r} (known: {', '.join(known)})")

    def table(name):
        return [r for r in rows if r["table"] == name]

    layers = table("5")
    suspect = tuple(
        f"Kd {r['value']} 1/m at {r['depth_top_m']}-{r['depth_bottom_m']} m"
        for r in layers if r["status"] in _data.QUESTIONABLE
    )
    if suspect:
        warnings.warn(
            f"Jerlov's Table 5 for {water_type} prints a Kd that does not "
            f"follow from his Table 3: " + "; ".join(suspect)
            + ". See DATA.md section 22.",
            ProvenanceWarning,
            stacklevel=_data.caller_stacklevel(),
        )
    levels = table("2")
    profile = table("3")
    return QuantaLevels(
        water_type=water_type,
        level_percent=tuple(float(r["percent_top"]) for r in levels),
        level_depth_m=_data._frozen(np.array([float(r["value"])
                                              for r in levels])),
        profile_depth_m=_data._frozen(np.array([float(r["depth_top_m"])
                                                for r in profile])),
        profile_percent=_data._frozen(np.array([float(r["value"])
                                                for r in profile])),
        layer_m=tuple((float(r["depth_top_m"]), float(r["depth_bottom_m"]))
                      for r in layers),
        layer_kd=_data._frozen(np.array([float(r["value"]) for r in layers])),
        suspect=suspect,
    )

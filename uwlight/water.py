"""Inherent optical properties of a body of water.

Named Jerlov water types are only an entry point: they are turned into a
:class:`Water` immediately, and every calculation works on the resulting
spectra. Measured coefficients can be supplied directly and take exactly the
same path.
"""

from __future__ import annotations

import warnings

import numpy as np

from . import _data
from .sources import Source, get_source


class ProvenanceWarning(UserWarning):
    """Raised when a returned value rests on something the caller should know.

    Interpolating across a wavelength that a published table got wrong, or
    that was itself extrapolated, gives a number that looks no different from
    a sound one. This warning is the only thing that distinguishes them.
    """


class MissingQuantityError(LookupError):
    """Raised when a quantity is not determined by the available data."""


def _as_array(x) -> np.ndarray:
    return np.atleast_1d(np.asarray(x, dtype=float))


class Water:
    """Absorption and scattering coefficients as functions of wavelength.

    Parameters
    ----------
    wavelengths:
        Wavelengths in nm, ascending.
    a, b:
        Absorption and scattering coefficients in 1/m. Use ``nan`` for
        wavelengths where the value is unknown.
    kd:
        Downwelling diffuse attenuation coefficient in 1/m, if known.
    name:
        Jerlov water type, when the object came from one.
    source:
        The :class:`~uwlight.sources.Source` the coefficients came from.
    flags:
        Per-wavelength status strings, parallel to ``wavelengths``.
    """

    def __init__(
        self,
        wavelengths,
        a=None,
        b=None,
        *,
        kd=None,
        name: str | None = None,
        source: Source | None = None,
        flags: dict[str, tuple[str, ...]] | None = None,
    ) -> None:
        self.wavelengths = np.asarray(wavelengths, dtype=float)
        if self.wavelengths.ndim != 1 or self.wavelengths.size == 0:
            raise ValueError("wavelengths must be a non-empty 1-D array")
        if np.any(np.diff(self.wavelengths) <= 0):
            raise ValueError("wavelengths must be strictly ascending")

        self._series: dict[str, np.ndarray] = {}
        for key, value in (("a", a), ("b", b), ("Kd", kd)):
            if value is None:
                continue
            arr = np.asarray(value, dtype=float)
            if arr.shape != self.wavelengths.shape:
                raise ValueError(f"{key} must have the same shape as wavelengths")
            self._series[key] = arr
        if not self._series:
            raise ValueError("at least one of a, b, kd must be given")

        self.name = name
        self.source = source
        self._flags = flags or {}

    # -- construction ----------------------------------------------------

    @classmethod
    def from_measurements(cls, wavelengths, a=None, b=None, *, kd=None,
                          name: str | None = None) -> "Water":
        """Build a :class:`Water` from the caller's own measurements."""
        return cls(wavelengths, a=a, b=b, kd=kd, name=name, source=None)

    # -- access ----------------------------------------------------------

    @property
    def range_nm(self) -> tuple[float, float]:
        return float(self.wavelengths[0]), float(self.wavelengths[-1])

    def has(self, quantity: str) -> bool:
        return quantity in self._series

    def _interp(self, quantity: str, wl) -> np.ndarray:
        if quantity not in self._series:
            available = ", ".join(sorted(self._series)) or "none"
            raise MissingQuantityError(
                f"{quantity!r} is not available for this water "
                f"(available: {available})"
            )
        query = _as_array(wl)
        lo, hi = self.range_nm
        if np.any(query < lo) or np.any(query > hi):
            raise ValueError(
                f"wavelength outside the range of the data ({lo:g}-{hi:g} nm). "
                "This package does not extrapolate."
            )
        self._warn_if_flagged(quantity, query)
        values = self._series[quantity]
        out = np.interp(query, self.wavelengths, values)
        # np.interp happily bridges a NaN-free path around a NaN, so check the
        # bracketing samples explicitly.
        idx = np.searchsorted(self.wavelengths, query)
        for k, i in enumerate(idx):
            neighbours = values[max(i - 1, 0):min(i + 1, values.size) + 1]
            if np.any(np.isnan(neighbours)):
                out[k] = np.nan
        return out

    def _warn_if_flagged(self, quantity: str, query: np.ndarray) -> None:
        statuses = self._flags.get(quantity)
        if not statuses:
            return
        hit: set[str] = set()
        idx = np.searchsorted(self.wavelengths, query)
        for i in idx:
            for j in (max(i - 1, 0), min(i, len(statuses) - 1)):
                status = statuses[j]
                if status in _data.QUESTIONABLE:
                    hit.add(f"{status} at {self.wavelengths[j]:g} nm")
        if hit:
            warnings.warn(
                f"{quantity} for Jerlov {self.name} rests on flagged values: "
                + "; ".join(sorted(hit))
                + ". See the package README for what is known about them.",
                ProvenanceWarning,
                stacklevel=3,
            )

    def a(self, wl) -> np.ndarray:
        """Absorption coefficient in 1/m."""
        return self._interp("a", wl)

    def b(self, wl) -> np.ndarray:
        """Scattering coefficient in 1/m."""
        return self._interp("b", wl)

    def c(self, wl) -> np.ndarray:
        """Beam attenuation coefficient ``a + b`` in 1/m."""
        return self.a(wl) + self.b(wl)

    def kd(self, wl) -> np.ndarray:
        """Downwelling diffuse attenuation coefficient in 1/m."""
        return self._interp("Kd", wl)

    def bb(self, wl, *, backscatter_ratio: float | None = None) -> np.ndarray:
        """Backscattering coefficient in 1/m.

        ``backscatter_ratio`` is bb/b and has no default. It is not determined
        by the Jerlov classification: deriving it from the particle
        concentrations of Solonenko & Mobley and of Williamson & Hollins gives
        answers that differ by up to a factor of 31. See README section 10.

        Reported ranges are roughly 0.005-0.01 for open ocean and 0.015-0.03
        for coastal water; the Petzold average-particle phase function gives
        about 0.0183.
        """
        if backscatter_ratio is None:
            raise MissingQuantityError(
                "bb is not determined by the water type. Pass "
                "backscatter_ratio=... explicitly (bb/b; roughly 0.005-0.01 "
                "for open ocean, 0.015-0.03 for coastal water). "
                "See README section 10."
            )
        if not 0.0 < backscatter_ratio < 0.5:
            raise ValueError("backscatter_ratio must lie in (0, 0.5)")
        return self.b(wl) * backscatter_ratio

    # -- description -----------------------------------------------------

    def caveats(self) -> tuple[str, ...]:
        """Return what is known to be doubtful about this water's data."""
        out: list[str] = []
        if self.source is not None:
            out.extend(self.source.caveats)
        for quantity, statuses in self._flags.items():
            flagged = {s for s in statuses if s in _data.QUESTIONABLE}
            for status in sorted(flagged):
                count = sum(1 for s in statuses if s == status)
                out.append(f"{quantity}: {count} wavelength(s) marked {status!r}")
        return tuple(out)

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        lo, hi = self.range_nm
        src = self.source.key if self.source else "user"
        return (
            f"<Water {self.name or 'unnamed'} source={src} "
            f"{lo:g}-{hi:g} nm, {', '.join(sorted(self._series))}>"
        )


# -- factories -----------------------------------------------------------

_IOP_FILES = {
    "williamson2022": ("williamson2022_iop.csv", ("a", "b")),
    "solonenko2015": ("solonenko2015_iop.csv", ("a", "b", "Kd")),
}

_KD_FILES = {
    "jerlov1976": ("jerlov1976_kd.csv", "Kd_downwelling_per_m"),
    "austin1986": ("austin1986_kd.csv", "Kd_downwelling_per_m"),
}


def water(water_type: str, source: str = "williamson2022") -> Water:
    """Return the :class:`Water` for a named Jerlov type.

    The default source is Williamson & Hollins (2022) because it is the only
    published set in which a and b rest on measurements rather than on an
    inversion of Kd.
    """
    src = get_source(source)
    if water_type not in src.water_types:
        available = ", ".join(src.water_types)
        raise KeyError(
            f"source {source!r} does not cover Jerlov {water_type!r} "
            f"(available: {available})"
        )

    if source in _IOP_FILES:
        filename, quantities = _IOP_FILES[source]
        series: dict[str, np.ndarray] = {}
        flags: dict[str, tuple[str, ...]] = {}
        wavelengths = None
        for quantity in quantities:
            wl, values, statuses = _data.spectrum(
                filename, water_type, quantity, "value_per_m"
            )
            if wavelengths is None:
                wavelengths = wl
            elif not np.array_equal(wavelengths, wl):
                raise RuntimeError(f"inconsistent wavelength grid in {filename}")
            series[quantity] = values
            flags[quantity] = statuses
        return Water(
            wavelengths,
            a=series.get("a"),
            b=series.get("b"),
            kd=series.get("Kd"),
            name=water_type,
            source=src,
            flags=flags,
        )

    filename, column = _KD_FILES[source]
    wl, values, statuses = _data.spectrum(filename, water_type, None, column)
    return Water(
        wl, kd=values, name=water_type, source=src, flags={"Kd": statuses}
    )


def kd_spectrum(kd, wavelength_nm: float, at) -> np.ndarray:
    """Reconstruct a Kd spectrum from a single measured value.

    Uses the model of Austin & Petzold (1986), Eq. (6)::

        K(l2) = [M(l2)/M(l1)] * [K(l1) - Kw(l1)] + Kw(l2)

    Parameters
    ----------
    kd:
        Measured Kd in 1/m.
    wavelength_nm:
        Wavelength at which ``kd`` was measured.
    at:
        Wavelength(s) at which to evaluate the spectrum.

    Notes
    -----
    The authors state the model holds for K(490) < 0.16 1/m. Accuracy is about
    8 percent at wavelengths up to 590 nm and degrades to about 31 percent at
    670 nm; M below 365 nm is itself extrapolated.
    """
    wl, m, kw = _data.austin_model()
    lo, hi = float(wl[0]), float(wl[-1])
    query = _as_array(at)
    for value, label in ((wavelength_nm, "wavelength_nm"), (query, "at")):
        if np.any(np.asarray(value) < lo) or np.any(np.asarray(value) > hi):
            raise ValueError(f"{label} outside the model range ({lo:g}-{hi:g} nm)")

    m1 = float(np.interp(wavelength_nm, wl, m))
    kw1 = float(np.interp(wavelength_nm, wl, kw))
    if kd < kw1:
        warnings.warn(
            f"Kd={kd:g} is below the pure sea water value {kw1:g} at "
            f"{wavelength_nm:g} nm, which is not physically possible. "
            "Austin & Petzold (1986) reported exactly this problem in "
            "Jerlov's own type I values.",
            ProvenanceWarning,
            stacklevel=2,
        )
    return np.interp(query, wl, m) / m1 * (kd - kw1) + np.interp(query, wl, kw)


def b_from_c(c, wavelength_nm, *, bw, cw, bound: str = "average"):
    """Estimate the scattering coefficient from the beam attenuation.

    Uses the measured ratios of Smart (2007) Table 1::

        b = (c - cw) * ratio + bw

    ``bound`` selects ``"average"``, ``"min"`` or ``"max"``. Smart recommends
    the upper bound for turbid water (c at 488 nm above 1.0 1/m) and the lower
    bound for clear water; the average is accurate to about 10 percent.
    Ratios are lower than tabulated in CDOM-rich water below about 488 nm.
    """
    wl, ratios = _data.b_from_c_ratio()
    if bound not in ratios:
        raise ValueError(f"bound must be one of {sorted(ratios)}")
    query = _as_array(wavelength_nm)
    if np.any(query < wl[0]) or np.any(query > wl[-1]):
        raise ValueError(
            f"wavelength outside the measured range ({wl[0]:g}-{wl[-1]:g} nm)"
        )
    ratio = np.interp(query, wl, ratios[bound])
    return (np.asarray(c, dtype=float) - cw) * ratio + bw

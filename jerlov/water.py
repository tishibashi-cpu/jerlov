"""Inherent optical properties of a body of water.

Named Jerlov water types are only an entry point: they are turned into a
:class:`Water` immediately, and every calculation works on the resulting
spectra. Measured coefficients can be supplied directly and take exactly the
same path.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

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


#: The quantities a caller can supply, by the names from_measurements takes.
_MEASURED_KEYS = {"a": "a", "b": "b", "kd": "Kd", "Kd": "Kd"}


def _as_array(x) -> np.ndarray:
    return np.atleast_1d(np.asarray(x, dtype=float))


def _require_number(value, name: str) -> None:
    """Refuse NaN in a distance, depth or range.

    A check such as ``value < 0`` is False for NaN, so NaN used to pass every
    such guard and come out as a result made of NaN, or as an answer that
    looked deliberate. Spectra are not checked here: NaN in a spectrum marks
    a gap in the data, which the package keeps visible on purpose.
    """
    if np.any(np.isnan(np.asarray(value, dtype=float))):
        raise ValueError(f"{name} must be a number, not NaN")


def _like_input(result: np.ndarray, original) -> np.ndarray | float:
    """Return a float for scalar input, an array otherwise.

    This is what ``numpy.interp`` does. Returning a one-element array for a
    scalar wavelength invites ``float(w.a(550))``, which numpy 2 refuses.
    """
    if np.ndim(original) == 0:
        return float(result[0])
    return result


def _support(grid: np.ndarray, query: np.ndarray) -> list[tuple[int, ...]]:
    """The indices of the samples of ``grid`` each query's answer rests on.

    A query that lands exactly on a sample rests on that sample alone: it is
    not interpolated, so its neighbours are no part of the answer. Otherwise
    it rests on the samples either side. The NaN check and the provenance
    warnings all use this, so that they cannot disagree about what a value
    depends on.
    """
    n = grid.size
    out: list[tuple[int, ...]] = []
    for i, w_query in zip(np.searchsorted(grid, query), query):
        if i < n and grid[i] == w_query:
            out.append((int(i),))
        else:
            out.append((max(int(i) - 1, 0), min(int(i), n - 1)))
    return out


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
    kd_hydrolight:
        Kd recomputed by a radiative transfer model from ``a`` and ``b``, as
        Solonenko & Mobley (2015) publish it. See :meth:`kd_hydrolight`.
    name:
        Jerlov water type, when the object came from one.
    source:
        The :class:`~jerlov.sources.Source` the coefficients came from.
    flags:
        Per-wavelength status strings, parallel to ``wavelengths``, keyed by
        quantity (``"a"``, ``"b"``, ``"Kd"``, ``"KdH"``).
    uncertainty:
        Per-wavelength standard uncertainty in 1/m, keyed the same way. NaN
        where it is not known. See :meth:`uncertainty`.
    """

    def __init__(
        self,
        wavelengths,
        a=None,
        b=None,
        *,
        kd=None,
        kd_hydrolight=None,
        name: str | None = None,
        source: Source | None = None,
        flags: dict[str, tuple[str, ...]] | None = None,
        uncertainty: dict[str, np.ndarray] | None = None,
    ) -> None:
        # Copied, so that neither the caller's arrays nor the packaged tables
        # can change underneath this object, and it cannot change them.
        self.wavelengths = np.array(wavelengths, dtype=float)
        if self.wavelengths.ndim != 1 or self.wavelengths.size == 0:
            raise ValueError("wavelengths must be a non-empty 1-D array")
        if not np.all(np.isfinite(self.wavelengths)):
            # np.diff gives NaN next to a NaN, and NaN <= 0 is False, so the
            # ascending check below would let it through.
            raise ValueError("wavelengths must all be finite numbers")
        if np.any(np.diff(self.wavelengths) <= 0):
            raise ValueError("wavelengths must be strictly ascending")

        self._series: dict[str, np.ndarray] = {}
        for key, value in (("a", a), ("b", b), ("Kd", kd),
                           ("KdH", kd_hydrolight)):
            if value is None:
                continue
            arr = np.array(value, dtype=float)
            if arr.shape != self.wavelengths.shape:
                raise ValueError(f"{key} must have the same shape as wavelengths")
            self._series[key] = arr
        if not self._series:
            raise ValueError("at least one of a, b, kd must be given")

        self.name = name
        self.source = source
        self._flags = dict(flags or {})
        for key, statuses in self._flags.items():
            if len(statuses) != self.wavelengths.size:
                raise ValueError(
                    f"flags[{key!r}] has {len(statuses)} entries; it needs one "
                    f"per wavelength ({self.wavelengths.size})"
                )
        self._uncertainty: dict[str, np.ndarray] = {}
        for key, value in (uncertainty or {}).items():
            if key not in self._series:
                raise ValueError(
                    f"uncertainty given for {key!r}, which this water does "
                    f"not carry (it has {', '.join(sorted(self._series))})"
                )
            arr = np.array(value, dtype=float)
            if arr.shape != self.wavelengths.shape:
                raise ValueError(
                    f"uncertainty[{key!r}] must have the same shape as "
                    "wavelengths"
                )
            if np.any(arr < 0):
                # NaN < 0 is False, so NaN, "not known", passes.
                raise ValueError(f"uncertainty[{key!r}] cannot be negative")
            arr.setflags(write=False)
            self._uncertainty[key] = arr

    # -- construction ----------------------------------------------------

    @classmethod
    def from_measurements(cls, wavelengths, a=None, b=None, *, kd=None,
                          name: str | None = None, flags=None,
                          uncertainty=None) -> "Water":
        """Build a :class:`Water` from the caller's own measurements.

        Parameters
        ----------
        flags:
            Optional ``{quantity: statuses}``, one status per wavelength,
            for ``"a"``, ``"b"`` or ``"kd"``. The statuses are those of the
            packaged tables (DATA.md, "The status column"), so that a value
            you mark ``"suspect"`` or ``"extrapolated"`` warns exactly as a
            published one does. An unknown status is refused rather than
            ignored, since a misspelt flag would otherwise never warn.
        uncertainty:
            Optional ``{quantity: standard uncertainty}`` in 1/m, one value
            per wavelength, NaN where unknown. Read it back with
            :meth:`uncertainty`.
        """
        def keyed(mapping, what):
            out = {}
            for key, value in (mapping or {}).items():
                if key not in _MEASURED_KEYS:
                    raise ValueError(
                        f"{what} for {key!r}: expected one of "
                        f"{', '.join(sorted(_MEASURED_KEYS))}"
                    )
                out[_MEASURED_KEYS[key]] = value
            return out

        statuses = {}
        for key, values in keyed(flags, "flags").items():
            values = tuple(str(v) for v in values)
            unknown = sorted(set(values) - _data.STATUSES)
            if unknown:
                raise ValueError(
                    f"unknown status {', '.join(map(repr, unknown))} in "
                    f"flags; the statuses are {', '.join(sorted(_data.STATUSES))}"
                )
            statuses[key] = values
        given = {"a": a, "b": b, "Kd": kd}
        for key in statuses:
            if given[key] is None:
                raise ValueError(f"flags given for {key!r}, but no {key} values")
        return cls(wavelengths, a=a, b=b, kd=kd, name=name, source=None,
                   flags=statuses, uncertainty=keyed(uncertainty, "uncertainty"))

    # -- access ----------------------------------------------------------

    @property
    def range_nm(self) -> tuple[float, float]:
        return float(self.wavelengths[0]), float(self.wavelengths[-1])

    def has(self, quantity: str) -> bool:
        return quantity in self._series

    def _interp(self, quantity: str, wl, *, warn: bool = True,
                values: np.ndarray | None = None) -> np.ndarray:
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
        support = _support(self.wavelengths, query)
        if warn:
            self._warn_if_flagged(quantity, support)
        if values is None:
            values = self._series[quantity]
        out = np.interp(query, self.wavelengths, values)
        # np.interp happily bridges a NaN-free path around a NaN, so check the
        # samples the answer actually rests on.
        for k, samples in enumerate(support):
            if any(np.isnan(values[j]) for j in samples):
                out[k] = np.nan
        return _like_input(out, wl)

    def _label(self) -> str:
        if self.source is not None:
            return f"Jerlov {self.name}"
        return repr(self.name) if self.name else "this water"

    def _flag_hits(self, quantity: str,
                   support: list[tuple[int, ...]]) -> set[str]:
        statuses = self._flags.get(quantity)
        hit: set[str] = set()
        if not statuses:
            return hit
        for samples in support:
            for j in samples:
                status = statuses[j]
                if status in _data.QUESTIONABLE:
                    hit.add(f"{status} at {self.wavelengths[j]:g} nm")
        return hit

    def _warn(self, what: str, hit) -> None:
        if hit:
            warnings.warn(
                f"{what} for {self._label()} rests on flagged values: "
                + "; ".join(sorted(hit))
                + ". See DATA.md for what is known about them.",
                ProvenanceWarning,
                stacklevel=_data.caller_stacklevel(),
            )

    def _warn_if_flagged(self, quantity: str,
                         support: list[tuple[int, ...]]) -> None:
        self._warn(quantity, self._flag_hits(quantity, support))

    def a(self, wl):
        """Absorption coefficient in 1/m."""
        return self._interp("a", wl)

    def b(self, wl):
        """Scattering coefficient in 1/m."""
        return self._interp("b", wl)

    def c(self, wl):
        """Beam attenuation coefficient ``a + b`` in 1/m.

        One warning covers both terms: a wavelength flagged in a and in b
        is one fact about c, not two.
        """
        a = self._interp("a", wl, warn=False)
        b = self._interp("b", wl, warn=False)
        support = _support(self.wavelengths, _as_array(wl))
        self._warn("c", {f"{q} {h}" for q in ("a", "b")
                         for h in self._flag_hits(q, support)})
        return a + b

    def kd(self, wl):
        """Downwelling diffuse attenuation coefficient in 1/m."""
        return self._interp("Kd", wl)

    def kd_hydrolight(self, wl):
        """Kd recomputed by HydroLight from this water's a and b, in 1/m.

        Only Solonenko & Mobley (2015) publish it, as K_d^H in Tables 4-8.
        It is their check that the a and b they retrieved reproduce Jerlov's
        Kd: HydroLight run with those a and b, the Petzold average-particle
        phase function, a clear sky, infinitely deep water and no inelastic
        scattering, to an optical depth of 10 scattering lengths, or 6 for
        Jerlov III, where that matched Jerlov better (Section 4 and Appendix
        A). The paper says 90 percent of the points in its Fig. 5 lie within
        20 percent of Jerlov's; the tabulated values give 87 percent. See
        DATA.md section 19.

        It is not the same quantity as :meth:`kd`, which for this source is
        the Kd of the paper's own bio-optical model, fitted to Jerlov to
        within 15 percent. Comparing the two shows how much the retrieved
        IOPs depend on the model they were retrieved with.
        """
        return self._interp("KdH", wl)

    def uncertainty(self, quantity: str, wl):
        """The standard uncertainty of ``quantity`` at ``wl``, in 1/m.

        Only measurements carry one: pass it to :meth:`from_measurements`.
        Between measured wavelengths it is interpolated linearly, as the
        values are, which assumes the errors at neighbouring wavelengths are
        fully correlated. NaN where it was not given.
        """
        quantity = _MEASURED_KEYS.get(quantity, quantity)
        if quantity not in self._uncertainty:
            raise MissingQuantityError(
                f"no uncertainty was given for {quantity!r}"
                + ("" if self.source is None else
                   f"; source {self.source.key!r} publishes none")
            )
        return self._interp(quantity, wl, warn=False,
                            values=self._uncertainty[quantity])

    def bb(self, wl, *, backscatter_ratio: float | None = None):
        """Backscattering coefficient in 1/m.

        ``backscatter_ratio`` is bb/b and has no default. It is not determined
        by the Jerlov classification: deriving it from the particle
        concentrations of Solonenko & Mobley and of Williamson & Hollins gives
        answers that differ by up to a factor of 31. See DATA.md section 10.

        Reported ranges are roughly 0.005-0.01 for open ocean and 0.015-0.03
        for coastal water; the Petzold average-particle phase function gives
        about 0.0183.
        """
        if backscatter_ratio is None:
            raise MissingQuantityError(
                "bb is not determined by the water type. Pass "
                "backscatter_ratio=... explicitly (bb/b; roughly 0.005-0.01 "
                "for open ocean, 0.015-0.03 for coastal water). "
                "See DATA.md section 10."
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
    "solonenko2015": ("solonenko2015_iop.csv", ("a", "b", "Kd", "KdH")),
}

_KD_FILES = {
    "jerlov1976": ("jerlov1976_kd.csv", "Kd_downwelling_per_m"),
    "jerlov1968": ("jerlov1968_kd.csv", "Kd_downwelling_per_m"),
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
            kd_hydrolight=series.get("KdH"),
            name=water_type,
            source=src,
            flags=flags,
        )

    filename, column = _KD_FILES[source]
    wl, values, statuses = _data.spectrum(filename, water_type, None, column)
    return Water(
        wl, kd=values, name=water_type, source=src, flags={"Kd": statuses}
    )


def water_type_at_depth(surface_water_type: str, depth_m: float) -> str | None:
    """The Jerlov type that typically applies at ``depth_m``.

    The classification is defined on the top 10 m, but clarity changes with
    depth: water that is Jerlov I at the surface is typically IB below about
    40 m, and turbid coastal water typically clears with depth. Williamson &
    Hollins (2023) derived these profiles from more than 2500 measurement
    campaigns.

    Returns ``None`` where the paper declined to declare a type, which is
    wherever fewer than ten campaigns supported one. Coastal types run out
    quickly: 3C is declared only to 70 m, and 9C not at all below 10 m.

    This is a lookup, not a correction applied on your behalf. To use it::

        deeper = jerlov.water_type_at_depth("I", 60.0)      # "IB"
        w = jerlov.water(deeper) if deeper else jerlov.water("I")

    Notes
    -----
    The profile is what was *typical* across the campaigns, not what holds at
    any particular place or season. The paper says so explicitly, and gives
    per-cell cruise and month counts for anyone who needs to judge that.
    """
    depth_m = float(depth_m)
    if not np.isfinite(depth_m):
        # NaN fails every comparison below, so it would otherwise fall
        # through to "no statement" and look like a deliberate answer.
        raise ValueError(f"depth_m must be a finite number, not {depth_m!r}")
    if depth_m < 0:
        raise ValueError("depth_m cannot be negative")
    rows = _data._rows("williamson2023_depth.csv")
    known = {r["surface_water_type"] for r in rows}
    if surface_water_type not in known:
        raise KeyError(
            f"unknown water type {surface_water_type!r} "
            f"(known: {', '.join(sorted(known))})"
        )
    own = [r for r in rows if r["surface_water_type"] == surface_water_type]
    deepest = max(float(r["depth_max_m"]) for r in own)
    for row in own:
        top, bottom = float(row["depth_min_m"]), float(row["depth_max_m"])
        # A boundary belongs to the layer below it, except at the bottom of
        # the deepest layer, which has no layer below: 200 m is still
        # inside the paper's profile.
        if top <= depth_m < bottom or depth_m == bottom == deepest:
            return row["water_type"] or None
    # Beyond 200 m the paper makes no statement at all.
    return None


@dataclass(frozen=True, eq=False)   # == on arrays has no single answer
class Descent:
    """Downwelling irradiance carried down through changing water types."""

    surface_water_type: str
    depth_m: float
    source: str
    """The source of every layer's Kd."""
    wavelengths: np.ndarray
    """nm, as asked for."""
    layers: tuple[tuple[float, float, str], ...]
    """``(top, bottom, water type)`` of each layer crossed, in metres; the
    last stops at ``depth_m``."""
    transmittance: np.ndarray
    """``Ed(depth) / Ed(0)``: ``exp(-sum(Kd_i * thickness_i))``."""


def descend(surface_water_type: str, depth_m: float, wavelengths, *,
            source: str = "jerlov1976") -> Descent:
    """Attenuate downwelling irradiance through the typical depth profile.

    :meth:`Scene.at_depth` uses one Kd all the way down, but water clears or
    darkens with depth. This takes the type of each 10 m layer from
    :func:`water_type_at_depth`, Williamson & Hollins (2023), and the Kd of
    that type from ``source``::

        Ed(z) / Ed(0) = exp(-sum over layers of Kd_type(layer) * thickness)

    The top 10 m are the surface type itself. To build a scene from the
    result::

        d = jerlov.descend("1C", 45.0, wl)
        scene = jerlov.Scene(w, surface * d.transmittance, wl, depth_m=45.0)

    Parameters
    ----------
    source:
        Where every layer's Kd comes from. Jerlov (1976), the default, covers
        all ten types; the profile can pass through any of them.

    Raises
    ------
    MissingQuantityError
        Where the descent reaches a layer for which Williamson & Hollins
        declared no type, too few campaigns supporting one, or below 200 m,
        where they make no statement. A coastal profile runs out quickly:
        Jerlov 9C below 10 m, 5C and 7C below 20 m, 3C below 70 m.

    Notes
    -----
    Two approximations, both stated rather than hidden. The Kd of a type is
    that of its surface layer, applied unchanged at depth, since that is
    how the classification is defined. And the profile is what was typical
    across more than 2500 campaigns, not what holds at a given place or
    season; see :func:`water_type_at_depth`.
    """
    depth_m = float(depth_m)
    if not np.isfinite(depth_m):
        raise ValueError(f"depth_m must be a finite number, not {depth_m!r}")
    if depth_m < 0:
        raise ValueError("depth_m cannot be negative")
    get_source(source)
    rows = sorted(
        (r for r in _data._rows("williamson2023_depth.csv")
         if r["surface_water_type"] == surface_water_type),
        key=lambda r: float(r["depth_min_m"]),
    )
    if not rows:
        water_type_at_depth(surface_water_type, 0.0)   # raises, naming types
    deepest = float(rows[-1]["depth_max_m"])
    if depth_m > deepest:
        raise MissingQuantityError(
            f"Williamson & Hollins (2023) make no statement below "
            f"{deepest:g} m, so there is no type to descend through to "
            f"{depth_m:g} m"
        )
    query = _as_array(wavelengths)
    optical_depth = np.zeros_like(query)
    layers: list[tuple[float, float, str]] = []
    kd: dict[str, np.ndarray] = {}
    for row in rows:
        top, bottom = float(row["depth_min_m"]), float(row["depth_max_m"])
        if top >= depth_m:
            break
        water_type = row["water_type"]
        if not water_type:
            raise MissingQuantityError(
                f"Williamson & Hollins (2023) declare no type between "
                f"{top:g} and {bottom:g} m below Jerlov {surface_water_type} "
                f"water: fewer than ten campaigns supported one. The "
                f"descent can go no deeper than {top:g} m."
            )
        if water_type not in kd:
            kd[water_type] = _as_array(
                water(water_type, source).kd(query))
        bottom = min(bottom, depth_m)
        optical_depth += kd[water_type] * (bottom - top)
        layers.append((top, bottom, water_type))
    query.setflags(write=False)
    return Descent(
        surface_water_type=surface_water_type,
        depth_m=depth_m,
        source=source,
        wavelengths=query,
        layers=tuple(layers),
        transmittance=_like_input(np.exp(-optical_depth), wavelengths),
    )


#: Why each source without a pure water absorption has none.
_NO_AW = {
    "solonenko2015": (
        "Solonenko & Mobley (2015) used the average of Pope & Fry (1997), "
        "Buiteveld et al. (1994) and Pegau et al. (1997), which they show "
        "only as a curve in their Fig. 2"
    ),
    "jerlov1976": "Jerlov (1976) gives Kd only",
    "jerlov1968": "Jerlov (1968) gives Kd only",
    "austin1986": (
        "Austin & Petzold (1986) give Kd only. Their Kw is the diffuse "
        "attenuation of pure sea water, not its absorption"
    ),
}


def pure_water_absorption(wavelength_nm, source: str = "williamson2022"):
    """The absorption of pure water that ``source`` computed its a with, 1/m.

    A Jerlov type's a is that of pure water plus what is dissolved and
    suspended in it, and each source started from its own pure water
    spectrum. This returns that spectrum, so that the part of a due to the
    water's contents is ``w.a(l) - pure_water_absorption(l)`` for the same
    source, and not a difference between two tabulations.

    Only Williamson & Hollins (2022) publish theirs, in the spreadsheet that
    accompanies the paper: 1 nm from 300 to 800 nm. The paper attributes it
    to Buiteveld et al. (1994); it has not been compared with Buiteveld's
    table here, but it is the aw their a was built on, which the build
    script checks. From 720 nm their model gives the water's contents no
    absorption at all, so every type's a is this. See DATA.md section 20.

    Other sources raise :class:`MissingQuantityError`, saying why.
    """
    get_source(source)          # an unknown key says which ones exist
    if source != "williamson2022":
        raise MissingQuantityError(
            f"source {source!r} publishes no pure water absorption: "
            f"{_NO_AW[source]}. Only 'williamson2022' does."
        )
    wl, values, _ = _data.spectrum("williamson2022_aw.csv", None, None,
                                   "aw_per_m")
    query = _as_array(wavelength_nm)
    _require_number(query, "wavelength_nm")
    if np.any(query < wl[0]) or np.any(query > wl[-1]):
        raise ValueError(
            f"wavelength outside the range of the data ({wl[0]:g}-"
            f"{wl[-1]:g} nm). This package does not extrapolate."
        )
    return _like_input(np.interp(query, wl, values), wavelength_nm)


#: Austin & Petzold (1986) state their model holds below this K(490), 1/m.
AUSTIN_KD490_LIMIT = 0.16


def kd_spectrum(kd, wavelength_nm: float, at):
    """Reconstruct a Kd spectrum from a single measured value.

    Uses the model of Austin & Petzold (1986), Eq. (6)::

        K(l2) = [M(l2)/M(l1)] * [K(l1) - Kw(l1)] + Kw(l2)

    Parameters
    ----------
    kd:
        Measured Kd in 1/m. A scalar, or an array of measurements all made at
        ``wavelength_nm`` (several stations, say); each is reconstructed
        separately.
    wavelength_nm:
        Wavelength at which ``kd`` was measured. A single value.
    at:
        Wavelength(s) at which to evaluate the spectrum.

    Returns
    -------
    A float for scalar ``kd`` and ``at``. Otherwise an array of shape
    ``kd.shape + at.shape``: one spectrum per measurement.

    Notes
    -----
    The authors state the model holds for K(490) < 0.16 1/m, and a
    :class:`ProvenanceWarning` is raised for any measurement whose K(490),
    measured or implied by the model, is not below that. Austin & Petzold
    (1990) put its accuracy, as a coefficient of variation over 83 stations,
    under 8 percent at wavelengths up to 590 nm except at 410 nm, where yellow
    substance makes it worse, and 9 percent or more beyond, reaching 31
    percent at 670 nm. M below 365 nm is itself extrapolated, and a result
    that rests on it also warns.
    """
    wl, m, kw = _data.austin_model()
    lo, hi = float(wl[0]), float(wl[-1])
    if np.ndim(wavelength_nm) != 0:
        raise ValueError(
            "wavelength_nm must be a single wavelength; for measurements at "
            "different wavelengths, call kd_spectrum once for each"
        )
    wavelength_nm = float(wavelength_nm)
    query = _as_array(at)
    for value, label in ((wavelength_nm, "wavelength_nm"), (query, "at")):
        if np.any(np.asarray(value) < lo) or np.any(np.asarray(value) > hi):
            raise ValueError(f"{label} outside the model range ({lo:g}-{hi:g} nm)")
    kd_values = np.asarray(kd, dtype=float)

    m1 = float(np.interp(wavelength_nm, wl, m))
    kw1 = float(np.interp(wavelength_nm, wl, kw))
    below = kd_values < kw1
    if np.any(below):
        shown = ", ".join(f"{v:g}" for v in np.atleast_1d(kd_values)[
            np.atleast_1d(below)][:5])
        warnings.warn(
            f"Kd={shown} is below the pure sea water value {kw1:g} at "
            f"{wavelength_nm:g} nm, which is not physically possible. "
            "Austin & Petzold (1986) reported exactly this problem in "
            "Jerlov's own type I values.",
            ProvenanceWarning,
            stacklevel=_data.caller_stacklevel(),
        )

    kd490 = (float(np.interp(490.0, wl, m)) / m1 * (kd_values - kw1)
             + float(np.interp(490.0, wl, kw)))
    outside = kd490 >= AUSTIN_KD490_LIMIT
    if np.any(outside):
        shown = ", ".join(f"{v:.3g}" for v in np.atleast_1d(kd490)[
            np.atleast_1d(outside)][:5])
        warnings.warn(
            f"K(490) = {shown} 1/m"
            + (" (implied by the model)" if wavelength_nm != 490.0 else "")
            + f" is not below {AUSTIN_KD490_LIMIT:g} 1/m, the limit Austin & "
            "Petzold (1986) give for their model. The reconstruction is "
            "outside the range it was fitted to.",
            ProvenanceWarning,
            stacklevel=_data.caller_stacklevel(),
        )

    statuses = _data.austin_model_status()
    flagged: set[str] = set()
    for samples in _support(wl, np.concatenate(([wavelength_nm], query))):
        for j in samples:
            if statuses[j] in _data.QUESTIONABLE:
                flagged.add(f"{statuses[j]} at {wl[j]:g} nm")
    if flagged:
        warnings.warn(
            "the result rests on values of M that Austin & Petzold (1986) "
            "flag as " + "; ".join(sorted(flagged)) + ", and say should be "
            "used with caution",
            ProvenanceWarning,
            stacklevel=_data.caller_stacklevel(),
        )

    ratio = np.interp(query, wl, m) / m1
    result = (ratio * (kd_values[..., None] - kw1)
              + np.interp(query, wl, kw))
    if np.ndim(at) == 0:
        result = result[..., 0]
    if np.ndim(result) == 0:
        return float(result)
    return result


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
    if np.ndim(wavelength_nm) == 0:
        ratio = ratio[0]
    c_values = np.asarray(c, dtype=float)
    if np.any(c_values < cw):
        warnings.warn(
            "c is below the pure water value cw, which is not "
            "physically possible, so the particle term (c - cw) is negative "
            "and so may b be. Check the calibration of c and the value of cw.",
            ProvenanceWarning,
            stacklevel=_data.caller_stacklevel(),
        )
    result = (c_values - cw) * ratio + bw
    # c and the wavelength broadcast against each other; the answer is a
    # float only when neither of them was an array.
    if np.ndim(result) == 0:
        return float(result)
    return result


@dataclass(frozen=True, eq=False)   # == on arrays has no single answer
class MeasuredPoints:
    """Measured a or b of one Jerlov type, before any spectral fitting."""

    water_type: str
    quantity: str
    wavelengths: np.ndarray
    """nm, ascending."""
    values: np.ndarray
    """1/m: the average over campaigns."""
    std_dev: np.ndarray
    """1/m, across campaigns; NaN where none was given."""
    n_campaigns: np.ndarray
    """How many campaigns each average rests on."""
    included: np.ndarray
    """True where the paper kept the point (five or more campaigns)."""


def measured_points(water_type: str, quantity: str, *,
                    include_sparse: bool = False) -> MeasuredPoints:
    """The measured a or b points behind Williamson & Hollins (2022).

    The smooth spectra returned by ``water(..., source="williamson2022")``
    were fitted to these. Hollins & Williamson (2023) say the fitting would
    bias some analyses and that the individual points are preferable for
    validation; they come with their spread and their campaign count.

    The paper kept only averages built from five or more campaigns, 53 each
    for a and b. Points below that are left out unless
    ``include_sparse=True``. Jerlov IA and 7C rest on a single campaign
    throughout, so without it they have no points at all, and this raises
    rather than returning nothing. See DATA.md section 9.
    """
    if quantity not in ("a", "b"):
        raise ValueError("quantity must be 'a' or 'b'")
    rows = [r for r in _data._rows("williamson2022_measured.csv")
            if r["water_type"] == water_type and r["quantity"] == quantity]
    if not rows:
        known = sorted({r["water_type"]
                        for r in _data._rows("williamson2022_measured.csv")})
        raise KeyError(f"no measured points for Jerlov {water_type!r} "
                       f"(known: {', '.join(known)})")
    kept = [r for r in rows if include_sparse or r["status"] == "included"]
    if not kept:
        raise KeyError(
            f"every measured point for Jerlov {water_type} rests on fewer "
            "than five campaigns, and the paper excluded them all. Pass "
            "include_sparse=True to get them anyway."
        )
    kept.sort(key=lambda r: float(r["wavelength_nm"]))
    return MeasuredPoints(
        water_type=water_type,
        quantity=quantity,
        wavelengths=np.array([float(r["wavelength_nm"]) for r in kept]),
        values=np.array([float(r["value_per_m"]) for r in kept]),
        std_dev=np.array([_data._to_float(r["std_dev_per_m"]) for r in kept]),
        n_campaigns=np.array([int(r["n_campaigns"]) for r in kept]),
        included=np.array([r["status"] == "included" for r in kept]),
    )

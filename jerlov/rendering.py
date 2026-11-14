"""Coefficients for renderers: RGB, a Henyey-Greenstein g, and spectra.

Renderers of water, for film, games or simulation, need an absorption and
a scattering coefficient and a phase function. This module hands over the
package's sourced values in the forms renderers take, without solving the
radiative transfer equation: the renderer does the light (DECISIONS.md
sections 12, 38 and 82).

- :func:`rgb_attenuation`: one extinction, absorption and scattering
  coefficient per channel of a linear RGB space, fitted over distances the
  caller states, with the error of the fit.
- :func:`henyey_greenstein_fit`: the g of a Henyey-Greenstein phase
  function for one of Petzold's stations, matched to a property the caller
  chooses, with the error of the shape.
- :func:`spectral_coefficients`: a, b and c at the water's own wavelengths,
  for spectral renderers.

Each result has ``as_dict()``, ready for :func:`json.dump`. No renderer's
own file format is written here; ``examples/rendering_export.py`` shows
three.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from . import _data
from .colour import _rgb_matrix, cie_1931_cmf, integrate_response
from .petzold import ScatteringFunction
from .water import Water, _require_number

#: The linear RGB spaces :func:`rgb_attenuation` works in. Each is its
#: primaries and white, as chromaticities: no transfer function is applied,
#: since renderers take coefficients in linear values.
RGB_COLOUR_SPACES = ("linear_srgb", "acescg", "rec2020")

_SPACES: dict[str, tuple[tuple[tuple[float, float], ...],
                         tuple[float, float], str]] = {
    "linear_srgb": (
        ((0.6400, 0.3300), (0.3000, 0.6000), (0.1500, 0.0600)),
        (0.3127, 0.3290),
        "IEC 61966-2-1:1999, sRGB (the Rec. ITU-R BT.709 primaries and "
        "D65), without the transfer function"),
    "acescg": (
        ((0.713, 0.293), (0.165, 0.830), (0.128, 0.044)),
        (0.32168, 0.33767),
        "Academy of Motion Picture Arts and Sciences, ACEScg specification "
        "(the AP1 primaries and the ACES white), docs.acescentral.com"),
    "rec2020": (
        ((0.708, 0.292), (0.170, 0.797), (0.131, 0.046)),
        (0.3127, 0.3290),
        "Rec. ITU-R BT.2020-2 (10/2015), Table 3, p. 3, without the "
        "transfer function"),
}

#: The distances at which a channel's transmittance is fitted.
_FIT_POINTS = 201


def _xyz_to_rgb(colour_space: str) -> np.ndarray:
    primaries, white, _ = _SPACES[colour_space]
    return _rgb_matrix(np.array(primaries), np.array(white))


def _space(colour_space) -> str:
    if colour_space is None:
        raise ValueError(
            "colour_space has no default: a coefficient per channel means "
            "something only in a stated RGB space. Choose one of "
            f"{', '.join(RGB_COLOUR_SPACES)}")
    if colour_space not in _SPACES:
        raise ValueError(
            f"unknown colour_space {colour_space!r}; the spaces are "
            f"{', '.join(RGB_COLOUR_SPACES)}")
    return colour_space


def _distances(distance_range_m) -> tuple[float, float]:
    if distance_range_m is None:
        raise ValueError(
            "distance_range_m has no default: one exponential per channel "
            "fits the true transmittance only over a range of distances, "
            "and which range matters is the scene's")
    try:
        near, far = (float(v) for v in distance_range_m)
    except (TypeError, ValueError):
        raise ValueError(
            "distance_range_m must be a pair of numbers, (near, far), in "
            "metres") from None
    _require_number([near, far], "distance_range_m")
    if not (math.isfinite(near) and math.isfinite(far)):
        raise ValueError("distance_range_m must be finite")
    if near < 0 or far <= near:
        raise ValueError(
            "distance_range_m must be (near, far) with 0 <= near < far, in "
            f"metres; got ({near:g}, {far:g})")
    return near, far


def _illuminant(illuminant) -> tuple[np.ndarray, np.ndarray]:
    if illuminant is None:
        raise ValueError(
            "illuminant has no default: the colour of the light that has "
            "crossed the water depends on the light that entered it. Pass "
            "(wavelengths, power), as jerlov.d65() returns it, or the "
            "irradiance at the depth in question")
    try:
        wl, power = illuminant
    except (TypeError, ValueError):
        raise ValueError(
            "illuminant must be a pair (wavelengths, power), as "
            "jerlov.d65() returns it") from None
    wl = np.array(wl, dtype=float)
    power = np.array(power, dtype=float)
    if wl.ndim != 1 or wl.shape != power.shape:
        raise ValueError(
            "the illuminant's wavelengths and power must be 1-D arrays of "
            "the same length")
    if wl.size < 2:
        raise ValueError("the illuminant needs at least two wavelengths")
    if not np.all(np.isfinite(wl)) or not np.all(np.isfinite(power)):
        raise ValueError(
            "the illuminant's wavelengths and power must be finite numbers: "
            "a gap in the light leaves the colour undetermined")
    if np.any(np.diff(wl) <= 0):
        raise ValueError(
            "the illuminant's wavelengths must be strictly ascending")
    if np.any(power < 0):
        raise ValueError("the illuminant's power must not be negative")
    return wl, power


@_data.compared_by_value
@dataclass(frozen=True, eq=False)
class RgbAttenuation:
    """Coefficients per channel of a linear RGB space, 1/m.

    Each is the exponent of one exponential fitted to the channel's true
    transmittance over :attr:`distance_range_m`; the true transmittance is
    not one exponential, and :attr:`max_relative_error_t` and
    :attr:`max_relative_error_a` say how far the fit is from it.
    """

    colour_space: str
    """One of :data:`RGB_COLOUR_SPACES`."""
    distance_range_m: tuple[float, float]
    """The distances the fit was made over, (near, far) in metres."""
    wavelength_range_nm: tuple[float, float]
    """Where the water, the illuminant and the CIE 1931 observer overlap,
    integrated at 1 nm."""
    illuminant_rgb: np.ndarray
    """The illuminant's RGB in this space, scaled so that its luminance Y
    is 1: the colour to give the light in the scene."""
    sigma_t: np.ndarray
    """Extinction per channel, fitted from c."""
    sigma_a: np.ndarray
    """Absorption per channel, fitted from a."""
    sigma_s: np.ndarray
    """Scattering per channel, sigma_t - sigma_a, so that the three add
    up as a renderer assumes."""
    max_relative_error_t: np.ndarray
    """The largest ``abs(exp(-sigma_t r) / T(r) - 1)`` over the range,
    per channel, with T the channel's transmittance through c."""
    max_relative_error_a: np.ndarray
    """The same for sigma_a and the transmittance through a alone."""
    water: str
    """Which water the coefficients came from."""
    source: str
    """The source's citation, or an empty string for the caller's own."""

    @property
    def albedo(self) -> np.ndarray:
        """Single-scattering albedo per channel, sigma_s / sigma_t."""
        return self.sigma_s / self.sigma_t

    def as_dict(self) -> dict[str, Any]:
        """Plain numbers, lists and strings, for :func:`json.dump`."""
        primaries, white, citation = _SPACES[self.colour_space]
        return {
            "kind": "jerlov.rgb_attenuation",
            "water": self.water,
            "source": self.source,
            "colour_space": {
                "name": self.colour_space,
                "primaries_xy": [list(p) for p in primaries],
                "white_xy": list(white),
                "linear": True,
                "reference": citation,
            },
            "units": "1/m",
            "distance_range_m": list(self.distance_range_m),
            "wavelength_range_nm": list(self.wavelength_range_nm),
            "illuminant_rgb": self.illuminant_rgb.tolist(),
            "sigma_t": self.sigma_t.tolist(),
            "sigma_a": self.sigma_a.tolist(),
            "sigma_s": self.sigma_s.tolist(),
            "albedo": self.albedo.tolist(),
            "max_relative_error_t": self.max_relative_error_t.tolist(),
            "max_relative_error_a": self.max_relative_error_a.tolist(),
            "fit": ("least squares in ln T at 201 evenly spaced distances "
                    "over distance_range_m, through T = 1 at r = 0"),
        }

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        lo, hi = self.distance_range_m
        return (f"<RgbAttenuation {self.water} in {self.colour_space}, "
                f"{lo:g}-{hi:g} m, sigma_t "
                f"{', '.join(f'{v:.4g}' for v in self.sigma_t)} 1/m>")


def _first_nonpositive(channel_rgb, grid: np.ndarray) -> float | None:
    """The largest distance up to which every channel stays positive, or
    None if every channel stays positive at every distance of ``grid``."""
    r = np.union1d(np.linspace(0.0, float(grid[-1]), 4001), grid)
    bad = np.flatnonzero(np.any(channel_rgb(r) <= 0, axis=1))
    if bad.size == 0:
        return None
    lo, hi = r[bad[0] - 1], r[bad[0]]
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if np.any(channel_rgb(np.array([mid])) <= 0):
            hi = mid
        else:
            lo = mid
    return lo


@_data.positional_only()
def rgb_attenuation(water, /, *, colour_space, illuminant,
                    distance_range_m) -> RgbAttenuation:
    """Extinction, absorption and scattering per channel of an RGB space.

    A renderer in RGB attenuates each channel as exp(-sigma r). Light of
    spectrum S that has crossed r metres of water has the spectrum
    S exp(-c r), and its channel k is R_k(r) = M_k . XYZ, with M the
    space's matrix from XYZ. The channel's transmittance T_k(r) =
    R_k(r) / R_k(0) is not one exponential, and depends on S. So sigma_k
    is fitted, by least squares in ln T_k at 201 evenly spaced distances
    over ``distance_range_m``, through T = 1 at r = 0, and the result says
    how far the fit is from T_k.

    Parameters
    ----------
    water:
        A :class:`Water` with ``a`` and ``b``.
    colour_space:
        One of :data:`RGB_COLOUR_SPACES`, linear: ``"linear_srgb"``,
        ``"acescg"`` or ``"rec2020"``. No default.
    illuminant:
        ``(wavelengths, power)``, the light entering the water, as
        :func:`jerlov.d65` returns it. No default: above the sea D65 is one
        choice and :func:`jerlov.gregg1990_irradiance` another; under water,
        the light at that depth.
    distance_range_m:
        ``(near, far)`` in metres, ``0 <= near < far``. No default.

    Returns
    -------
    :class:`RgbAttenuation`. sigma_t is fitted from c, sigma_a from a, and
    sigma_s = sigma_t - sigma_a.

    Raises
    ------
    ValueError
        When a channel's transmittance falls to zero or below inside the
        range. Clear water leaves a blue-green light outside the sRGB
        gamut after a few metres, and the red channel, whose matching
        function is negative there, goes below zero. The message gives the
        largest distance at which every channel is still positive; a
        narrower range or a wider space is the remedy. Also for a gap (NaN)
        in a or c where the colour is formed, an illuminant with no power
        in a channel, a sigma_t or sigma_a that is not positive (a
        channel that grows across the water), and a negative sigma_s.
    MissingQuantityError
        When the water has no a or no b.

    Notes
    -----
    The spectra are integrated at 1 nm where the water, the illuminant and
    the CIE 1931 observer overlap; a :class:`CoverageWarning` says when
    that leaves part of the observer out. Flagged values of a, b or c warn
    with :class:`ProvenanceWarning`, as they do from :class:`Water`.
    No chromatic adaptation is made: a ratio within one channel needs
    none. :attr:`RgbAttenuation.illuminant_rgb` gives the illuminant's own
    colour in the space, for the light in the scene.
    """
    if not isinstance(water, Water):
        raise TypeError(
            f"water must be a jerlov.Water, not {type(water).__name__}")
    colour_space = _space(colour_space)
    near, far = _distances(distance_range_m)
    ill_wl, ill_power = _illuminant(illuminant)

    cmf_wl, cmf = cie_1931_cmf()
    lo = math.ceil(max(water.range_nm[0], ill_wl[0], cmf_wl[0]))
    hi = math.floor(min(water.range_nm[1], ill_wl[-1], cmf_wl[-1]))
    if hi - lo < 1:
        raise ValueError(
            f"the water ({water.range_nm[0]:g}-{water.range_nm[1]:g} nm), the "
            f"illuminant ({ill_wl[0]:g}-{ill_wl[-1]:g} nm) and the CIE "
            "observer (360-830 nm) do not overlap")
    wl = np.arange(lo, hi + 1, 1.0)
    a = np.asarray(water.a(wl), dtype=float)
    c = np.asarray(water.c(wl), dtype=float)
    for name, values in (("a", a), ("c", c)):
        gaps = wl[np.isnan(values)]
        if gaps.size:
            raise ValueError(
                f"{name} of {water._label()} has a gap (NaN) at "
                f"{gaps[0]:g}-{gaps[-1]:g} nm, inside the {lo:g}-{hi:g} nm "
                "where the colour is formed; no colour can be made across it")
    light = np.interp(wl, ill_wl, ill_power)

    m = _xyz_to_rgb(colour_space)
    # The coverage warning, and the illuminant's XYZ, once.
    xyz = integrate_response(light, wl, cmf, cmf_wl,
                             name="CIE 1931 2-degree observer")
    cmf_on = np.stack([np.interp(wl, cmf_wl, cmf[:, k]) for k in range(3)],
                      axis=1)
    response = cmf_on @ m.T                 # (n, 3): RGB matching functions
    rgb0 = m @ xyz
    if np.any(rgb0 <= 0):
        raise ValueError(
            f"the illuminant has no positive power in the "
            f"{_CHANNELS[int(np.argmin(rgb0))]} channel of {colour_space}, "
            "so a transmittance cannot be formed")

    def transmittance(coefficient: np.ndarray):
        def at(r: np.ndarray) -> np.ndarray:
            spectra = light[None, :] * np.exp(-np.outer(r, coefficient))
            rgb = _data.trapezoid(spectra[:, :, None] * response[None, :, :],
                                  wl, axis=1)
            return rgb / rgb0
        return at

    r = np.linspace(near, far, _FIT_POINTS)
    curves = {name: transmittance(coefficient)
              for name, coefficient in (("c", c), ("a", a))}
    observed = {name: at(r) for name, at in curves.items()}
    failing = [name for name, t in observed.items() if np.any(t <= 0)]
    if failing:
        name = failing[0]
        reach = min(found for found in (_first_nonpositive(at, r)
                                        for at in curves.values())
                    if found is not None)
        channel = _CHANNELS[int(np.argmin(np.min(observed[name], axis=0)))]
        raise ValueError(
            f"through {name}, the {channel} channel of {colour_space} "
            f"falls to zero or below within {far:g} m: the light left "
            "after that lies outside the space's gamut. Through a and c, "
            f"every channel stays positive only up to about {reach:.3g} m. "
            "Narrow distance_range_m, or use a wider space")
    fitted = {}
    for name, t in observed.items():
        sigma = -np.sum(r[:, None] * np.log(t), axis=0) / np.sum(r * r)
        error = np.max(np.abs(np.exp(-np.outer(r, sigma)) / t - 1), axis=0)
        fitted[name] = (sigma, error)

    sigma_t, error_t = fitted["c"]
    sigma_a, error_a = fitted["a"]
    for name, sigma in (("extinction", sigma_t), ("absorption", sigma_a)):
        # A channel whose matching function is negative where the water
        # absorbs grows as the light crosses it, and a renderer cannot take
        # the negative coefficient that fits.
        if np.any(sigma <= 0):
            raise ValueError(
                f"the fitted {name} of {water._label()} is not positive in "
                f"the {_CHANNELS[int(np.argmin(sigma))]} channel of "
                f"{colour_space} ({float(np.min(sigma)):.3g} 1/m): that "
                "channel does not fall as the light crosses the water, and "
                "no exponential a renderer can take fits it")
    sigma_s = sigma_t - sigma_a
    if np.any(sigma_s < 0):
        raise ValueError(
            f"the fitted scattering of {water._label()} is negative in the "
            f"{_CHANNELS[int(np.argmin(sigma_s))]} channel "
            f"({float(np.min(sigma_s)):.3g} 1/m): one exponential for a and "
            "one for c do not leave a scattering coefficient over this range")
    for array in (sigma_t, sigma_a, sigma_s, error_t, error_a):
        array.setflags(write=False)
    illuminant_rgb = rgb0 / xyz[1]
    illuminant_rgb.setflags(write=False)
    return RgbAttenuation(
        colour_space=colour_space,
        distance_range_m=(near, far),
        wavelength_range_nm=(float(lo), float(hi)),
        illuminant_rgb=illuminant_rgb,
        sigma_t=sigma_t,
        sigma_a=sigma_a,
        sigma_s=sigma_s,
        max_relative_error_t=error_t,
        max_relative_error_a=error_a,
        water=water._label(),
        source=water.source.citation if water.source is not None else "",
    )


_CHANNELS = ("red", "green", "blue")


# -- Henyey-Greenstein -----------------------------------------------------

#: The ways :func:`henyey_greenstein_fit` can choose g.
_HG_METHODS = ("backscatter_ratio", "mean_cosine")


def _hg_backscatter(g: float) -> float:
    """The share of a Henyey-Greenstein phase function beyond 90 degrees."""
    if g == 0:
        return 0.5
    return (1 - g) / (2 * g) * ((1 + g) / math.sqrt(1 + g * g) - 1)


def _hg(g: float, angle_deg: np.ndarray) -> np.ndarray:
    mu = np.cos(np.radians(angle_deg))
    return (1 - g * g) / (4 * np.pi * (1 + g * g - 2 * g * mu) ** 1.5)


@_data.compared_by_value
@dataclass(frozen=True, eq=False)
class HenyeyGreensteinFit:
    """A Henyey-Greenstein g for one of Petzold's stations, and its error.

    The phase function is p(theta) = (1 - g^2) / (4 pi (1 + g^2 -
    2 g cos theta)^(3/2)). It fits ocean water badly at small angles, and
    :attr:`log_ratio` shows where.
    """

    station: str
    wavelength_nm: float
    """530 nm, the wavelength of Petzold's c. One g serves every
    wavelength in a renderer; nothing here varies it."""
    method: str
    """What g was made to match, ``"backscatter_ratio"`` or
    ``"mean_cosine"``."""
    g: float
    backscatter_ratio: float
    """The HG's share beyond 90 degrees."""
    measured_backscatter_ratio: float
    """The station's B/S, as printed."""
    angles_deg: np.ndarray
    """Petzold's 55 angles."""
    log_ratio: np.ndarray
    """ln(p_HG / p) at each angle, p the measured phase function, vsf / b.
    Negative where HG falls short of the measurement."""

    def as_dict(self) -> dict[str, Any]:
        """Plain numbers, lists and strings, for :func:`json.dump`."""
        return {
            "kind": "jerlov.henyey_greenstein_fit",
            "phase_function": "Henyey-Greenstein",
            "station": self.station,
            "source": _PETZOLD,
            "wavelength_nm": self.wavelength_nm,
            "method": self.method,
            "g": self.g,
            "backscatter_ratio": self.backscatter_ratio,
            "measured_backscatter_ratio": self.measured_backscatter_ratio,
            "angles_deg": self.angles_deg.tolist(),
            "log_ratio": self.log_ratio.tolist(),
        }

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return (f"<HenyeyGreensteinFit {self.station} by {self.method}: "
                f"g={self.g:.4f}, B/S {self.backscatter_ratio:.4f} against "
                f"{self.measured_backscatter_ratio:.4f}>")


_PETZOLD = (
    "Petzold, T. J. (1972), 'Volume scattering functions for selected "
    "ocean waters', SIO Ref. 72-78, Scripps Institution of Oceanography, "
    "Visibility Laboratory, San Diego")


@_data.positional_only()
def henyey_greenstein_fit(scattering, /, *, method) -> HenyeyGreensteinFit:
    """The g of a Henyey-Greenstein phase function for a Petzold station.

    Parameters
    ----------
    scattering:
        A :class:`ScatteringFunction`, from :func:`petzold_scattering`.
    method:
        What g is made to match. No default:

        - ``"backscatter_ratio"``: the HG scatters the station's printed
          B/S beyond 90 degrees. B(g) = (1 - g) / (2 g) [(1 + g) /
          sqrt(1 + g^2) - 1] is solved by bisection.
        - ``"mean_cosine"``: g is the station's mean cosine,
          :meth:`ScatteringFunction.mean_cosine`. It rests at full weight
          on the report's extension below 0.1 degree and warns with
          :class:`ProvenanceWarning`.

    Notes
    -----
    HG has one parameter and cannot match both: matched to B/S, its mean
    cosine is lower than the station's; matched to the mean cosine, it
    backscatters less than the station. At small angles it falls short of
    the measurement by tens to hundreds of times whichever is matched;
    :attr:`HenyeyGreensteinFit.log_ratio` gives the shortfall at each of
    Petzold's angles. Petzold measured in one band in the green, total
    scattering of water and particles; a renderer will apply the one g at
    every wavelength.
    """
    if not isinstance(scattering, ScatteringFunction):
        raise TypeError(
            "scattering must be a jerlov.ScatteringFunction, from "
            f"jerlov.petzold_scattering, not {type(scattering).__name__}")
    if method is None:
        raise ValueError(
            "method has no default: a Henyey-Greenstein function cannot "
            "match both a water's backscattering and its mean cosine. "
            f"Choose one of {', '.join(_HG_METHODS)}")
    if method not in _HG_METHODS:
        raise ValueError(f"unknown method {method!r}; the methods are "
                         f"{', '.join(_HG_METHODS)}")
    measured = float(scattering.backscatter_ratio)
    if method == "mean_cosine":
        g = scattering.mean_cosine()
    else:
        if not 0 < measured < 0.5:
            raise ValueError(
                f"a backscatter ratio of {measured:g} has no Henyey-"
                "Greenstein g in (0, 1)")
        lo, hi = 0.0, 1.0
        for _ in range(100):
            mid = 0.5 * (lo + hi)
            if _hg_backscatter(mid) > measured:
                lo = mid
            else:
                hi = mid
        g = 0.5 * (lo + hi)
    angles = np.array(scattering.angles_deg, dtype=float)
    log_ratio = np.log(_hg(g, angles) / scattering.phase_function())
    for array in (angles, log_ratio):
        array.setflags(write=False)
    return HenyeyGreensteinFit(
        station=scattering.station,
        wavelength_nm=float(scattering.wavelength_nm),
        method=method,
        g=float(g),
        backscatter_ratio=_hg_backscatter(float(g)),
        measured_backscatter_ratio=measured,
        angles_deg=angles,
        log_ratio=log_ratio,
    )


# -- spectra -----------------------------------------------------------------

@_data.compared_by_value
@dataclass(frozen=True, eq=False)
class SpectralCoefficients:
    """a, b and c at a water's own wavelengths, 1/m, for spectral
    renderers. Nothing is resampled: a renderer interpolates them as it
    does its own spectra."""

    wavelengths: np.ndarray
    a: np.ndarray
    b: np.ndarray
    c: np.ndarray
    """a + b."""
    a_status: tuple[str, ...]
    """The status of each value of a, as in "The status column" of
    DATA.md."""
    b_status: tuple[str, ...]
    water: str
    source: str
    """The source's citation, or an empty string for the caller's own."""

    @property
    def albedo(self) -> np.ndarray:
        """Single-scattering albedo, b / c."""
        return self.b / self.c

    def as_dict(self) -> dict[str, Any]:
        """Plain numbers, lists and strings, for :func:`json.dump`.

        A gap (NaN) becomes ``None``, JSON's ``null``.
        """
        def listed(values: np.ndarray) -> list[float | None]:
            return [None if math.isnan(v) else float(v) for v in values]

        return {
            "kind": "jerlov.spectral_coefficients",
            "water": self.water,
            "source": self.source,
            "units": {"wavelengths": "nm", "a": "1/m", "b": "1/m",
                      "c": "1/m"},
            "wavelengths": self.wavelengths.tolist(),
            "a": listed(self.a),
            "b": listed(self.b),
            "c": listed(self.c),
            "a_status": list(self.a_status),
            "b_status": list(self.b_status),
        }

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return (f"<SpectralCoefficients {self.water}, "
                f"{self.wavelengths[0]:g}-{self.wavelengths[-1]:g} nm, "
                f"{self.wavelengths.size} wavelengths>")


@_data.positional_only()
def spectral_coefficients(water, /, *, range_nm) -> SpectralCoefficients:
    """a, b and c at the water's own wavelengths inside ``range_nm``.

    Parameters
    ----------
    water:
        A :class:`Water` with ``a`` and ``b``.
    range_nm:
        ``(low, high)`` in nm, inside the water's range. No default: a
        spectral renderer samples where its observer or camera is
        sensitive, and the water's range may run past that into flagged
        values.

    Notes
    -----
    Gaps stay NaN; flagged values warn with :class:`ProvenanceWarning`
    when the result is made, and each value carries its status.
    """
    if not isinstance(water, Water):
        raise TypeError(
            f"water must be a jerlov.Water, not {type(water).__name__}")
    if range_nm is None:
        raise ValueError(
            "range_nm has no default: choose the wavelengths the renderer "
            "samples, inside the water's range")
    try:
        lo, hi = (float(v) for v in range_nm)
    except (TypeError, ValueError):
        raise ValueError("range_nm must be a pair of numbers, (low, high), "
                         "in nm") from None
    _require_number([lo, hi], "range_nm")
    w_lo, w_hi = water.range_nm
    if not (w_lo <= lo < hi <= w_hi):
        raise ValueError(
            f"range_nm must lie inside the water's {w_lo:g}-{w_hi:g} nm with "
            f"low < high; got ({lo:g}, {hi:g}). This package does not "
            "extrapolate")
    inside = (water.wavelengths >= lo) & (water.wavelengths <= hi)
    wl = np.array(water.wavelengths[inside], dtype=float)
    if wl.size < 2:
        raise ValueError(
            f"the water has {wl.size} wavelength(s) in {lo:g}-{hi:g} nm; a "
            "spectrum needs at least two")
    # a and b warn for their own flags; c is their sum and adds nothing.
    a = np.array(water.a(wl), dtype=float)
    b = np.array(water.b(wl), dtype=float)
    c = a + b

    def statuses(quantity: str) -> tuple[str, ...]:
        flags = water._flags.get(quantity)
        if not flags:
            return ("ok",) * wl.size
        return tuple(s for s, keep in zip(flags, inside) if keep)

    for array in (wl, a, b, c):
        array.setflags(write=False)
    return SpectralCoefficients(
        wavelengths=wl, a=a, b=b, c=c,
        a_status=statuses("a"), b_status=statuses("b"),
        water=water._label(),
        source=water.source.citation if water.source is not None else "",
    )


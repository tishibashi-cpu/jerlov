"""From a spectrum to a colour, or to whatever a sensor or an eye would see.

Two things are easy to get wrong here and are checked rather than assumed.

**Coverage.** Integrating a spectrum that only spans 450-650 nm against
colour matching functions that span 360-830 nm silently drops the ends and
shifts the result. Every integration reports how much of the observer's
sensitivity the spectrum actually covered, and warns when the answer is not
essentially all of it.

**White.** A radiance spectrum has no colour until something is called white.
There is no default; the caller states the reference. Underwater the sensible
reference is usually the downwelling irradiance at that depth, which is what
makes a grey card look grey there rather than blue.
"""

from __future__ import annotations

import warnings

import numpy as np

from . import _data

# numpy.trapezoid is the name from NumPy 2.0; before that it was numpy.trapz.
# The package claims to work from NumPy 1.22, so it must not assume either.
_trapezoid = getattr(np, "trapezoid", None) or np.trapz

#: sRGB primaries and white point, IEC 61966-2-1.
SRGB_PRIMARIES = np.array([
    [0.6400, 0.3300],   # red
    [0.3000, 0.6000],   # green
    [0.1500, 0.0600],   # blue
])
SRGB_WHITEPOINT_XY = np.array([0.3127, 0.3290])   # D65


def _xy_to_xyz(xy: np.ndarray) -> np.ndarray:
    """Chromaticity to XYZ with Y = 1."""
    x, y = xy
    return np.array([x / y, 1.0, (1 - x - y) / y])


#: XYZ of the sRGB white, Y = 1. Adaptation maps a stated white onto this.
SRGB_WHITEPOINT_XYZ = _xy_to_xyz(SRGB_WHITEPOINT_XY)


class GamutWarning(UserWarning):
    """A colour fell outside the range the display can show.

    Underwater colours often do. Clipping changes them, so the caller is told
    rather than left to wonder.
    """


class CoverageWarning(UserWarning):
    """The spectrum did not span the observer's sensitivity.

    The integral is then over the overlap only, and the result is biased by
    however much was left out.
    """


def _rgb_matrix(primaries: np.ndarray, whitepoint_xy: np.ndarray) -> np.ndarray:
    """Derive the XYZ to linear RGB matrix from chromaticities."""
    x, y = primaries[:, 0], primaries[:, 1]
    m = np.vstack([x / y, np.ones(3), (1 - x - y) / y])
    scale = np.linalg.solve(m, _xy_to_xyz(whitepoint_xy))
    return np.linalg.inv(m * scale)


#: Derived here rather than hard-coded, so the primaries stay the source of
#: truth. `tests/test_colour.py` checks it against the published matrix.
XYZ_TO_LINEAR_SRGB = _rgb_matrix(SRGB_PRIMARIES, SRGB_WHITEPOINT_XY)


def cie_1931_cmf() -> tuple[np.ndarray, np.ndarray]:
    """Return ``(wavelengths, cmf)`` for the CIE 1931 2-degree observer.

    ``cmf`` has shape ``(n, 3)``, columns x-bar, y-bar, z-bar, at 1 nm from
    360 to 830 nm.
    """
    rows = _data._rows("cie1931_2deg_cmf.csv")
    wl = np.array([float(r["wavelength_nm"]) for r in rows])
    cmf = np.array([
        [float(r["x_bar"]), float(r["y_bar"]), float(r["z_bar"])] for r in rows
    ])
    return wl, cmf


def d65() -> tuple[np.ndarray, np.ndarray]:
    """Return ``(wavelengths, relative power)`` for CIE illuminant D65.

    This is the sRGB reference white, tabulated at 5 nm from 300 to 780 nm.

    It is a daylight phase, so it is a reasonable stand-in for the solar
    spectrum above the surface, but it is not a measurement of the light at
    any particular place or time: the real spectrum depends on solar
    elevation, atmosphere and the state of the surface.
    """
    rows = _data._rows("cie_d65.csv")
    wl = np.array([float(r["wavelength_nm"]) for r in rows])
    power = np.array([float(r["relative_spectral_power"]) for r in rows])
    return wl, power


def _resample(values, source_wl, target_wl) -> np.ndarray:
    """Interpolate onto ``target_wl``, leaving zeros outside the source."""
    return np.interp(target_wl, source_wl, values, left=0.0, right=0.0)


def _coverage(spectrum_wl, weight_wl, weight) -> float:
    """Fraction of the weight that the spectrum's range actually spans."""
    total = _trapezoid(weight, weight_wl)
    if total == 0:
        return 1.0
    inside = (weight_wl >= spectrum_wl[0]) & (weight_wl <= spectrum_wl[-1])
    if not inside.any():
        return 0.0
    return float(_trapezoid(weight[inside], weight_wl[inside]) / total)


def integrate_response(spectrum, wavelengths, response, response_wavelengths,
                       *, name: str = "response") -> np.ndarray:
    """Integrate a spectrum against one or more spectral sensitivities.

    Parameters
    ----------
    spectrum:
        Spectral radiance or irradiance, on ``wavelengths``.
    response:
        Shape ``(m,)`` for a single channel or ``(m, k)`` for ``k`` channels,
        on ``response_wavelengths``. Camera sensitivities and photoreceptor
        absorbances both fit here.

    Returns
    -------
    Array of shape ``(k,)``: the integral of spectrum times each channel over
    wavelength, in the units of the spectrum times nm.
    """
    spectrum = np.asarray(spectrum, dtype=float)
    wavelengths = np.asarray(wavelengths, dtype=float)
    response = np.atleast_2d(np.asarray(response, dtype=float))
    if response.shape[0] != np.size(response_wavelengths):
        response = response.T
    response_wavelengths = np.asarray(response_wavelengths, dtype=float)
    if spectrum.shape != wavelengths.shape:
        raise ValueError("spectrum must have the same shape as wavelengths")
    if response.shape[0] != response_wavelengths.shape[0]:
        raise ValueError("response must be aligned with response_wavelengths")
    if wavelengths.size < 2:
        raise ValueError("at least two wavelengths are needed to integrate")

    worst = min(
        _coverage(wavelengths, response_wavelengths, response[:, k])
        for k in range(response.shape[1])
    )
    if worst < 0.999:
        warnings.warn(
            f"the spectrum spans {wavelengths[0]:g}-{wavelengths[-1]:g} nm and "
            f"covers only {worst:.1%} of the {name}; the integral is over the "
            "overlap and is biased by what was left out",
            CoverageWarning,
            stacklevel=2,
        )

    resampled = np.stack(
        [_resample(response[:, k], response_wavelengths, wavelengths)
         for k in range(response.shape[1])],
        axis=1,
    )
    return _trapezoid(spectrum[:, None] * resampled, wavelengths, axis=0)


def spectrum_to_xyz(spectrum, wavelengths) -> np.ndarray:
    """Integrate a spectrum against the CIE 1931 2-degree observer.

    The result is unnormalised: it carries the units of the spectrum. Divide
    by the XYZ of whatever counts as white before converting to a display
    colour, or use :func:`spectrum_to_srgb`, which requires that reference.
    """
    cmf_wl, cmf = cie_1931_cmf()
    return integrate_response(
        spectrum, wavelengths, cmf, cmf_wl, name="CIE 1931 2-degree observer"
    )


def xyz_to_srgb(xyz, *, clip: bool = True) -> np.ndarray:
    """Convert XYZ, normalised so that white is Y = 1, to sRGB.

    Applies the sRGB transfer function of IEC 61966-2-1. Warns if any channel
    falls outside the display gamut, which underwater colours often do.
    """
    xyz = np.asarray(xyz, dtype=float)
    linear = np.tensordot(xyz, XYZ_TO_LINEAR_SRGB.T, axes=([-1], [0]))

    outside = np.any(linear < -1e-9) or np.any(linear > 1 + 1e-9)
    if outside:
        warnings.warn(
            "the colour lies outside the sRGB gamut"
            + (" and has been clipped" if clip else ""),
            GamutWarning,
            stacklevel=2,
        )
    if clip:
        linear = np.clip(linear, 0.0, 1.0)

    a = 0.055
    with np.errstate(invalid="ignore"):
        return np.where(
            linear <= 0.0031308,
            12.92 * linear,
            (1 + a) * np.power(np.maximum(linear, 0.0), 1 / 2.4) - a,
        )


def spectrum_to_srgb(spectrum, wavelengths, *, white, clip: bool = True):
    """Convert a spectrum to sRGB, relative to a stated white.

    Parameters
    ----------
    white:
        The spectrum that should come out white, on the same wavelengths.
        There is no default: a radiance spectrum has no colour until
        something is called white, and underwater the answer is usually the
        downwelling irradiance at that depth rather than a surface daylight.

    Notes
    -----
    The spectrum's XYZ is scaled component by component so that the stated
    white lands on the sRGB white point, which makes it come out exactly
    neutral. This is a von Kries-type adaptation carried out in XYZ rather
    than in cone space: transparent, and less accurate than CAT02 or Bradford
    for strongly coloured illumination.
    Underwater illumination is strongly coloured, so treat the result as
    "what a white-balanced camera would record" rather than as a prediction
    of appearance.

    Absolute brightness is lost: a perfect diffuser under the stated white
    maps to white whatever the light level.
    """
    if white is None:
        raise ValueError(
            "white has no default: a spectrum has no colour until something "
            "is called white. Underwater this is usually the downwelling "
            "irradiance at that depth."
        )
    white = np.asarray(white, dtype=float)
    if white.shape != np.shape(spectrum):
        raise ValueError("white must have the same shape as the spectrum")

    xyz = spectrum_to_xyz(spectrum, wavelengths)
    white_xyz = spectrum_to_xyz(white, wavelengths)
    if np.any(white_xyz <= 0):
        raise ValueError(
            "the white reference has no power in one of X, Y or Z, so it "
            "cannot serve as a white"
        )
    return xyz_to_srgb(xyz / white_xyz * SRGB_WHITEPOINT_XYZ, clip=clip)

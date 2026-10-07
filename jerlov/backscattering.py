"""From a backscattering sensor's reading to the backscattering coefficient.

`Water.bb` refuses to guess a backscattering ratio, because the Jerlov
classification does not determine one. If you have an instrument, you do not
have to guess: a HydroScat, an ECO-BB or a VSF meter measures the volume
scattering function at one angle in the backward hemisphere, and there is a
published relation from that to bb.

    bb = 2 pi chi_p(theta) [beta(theta) - beta_w(theta)] + bb_w

Boss & Pegau (2001) Eq. (10). The water terms are analytic, from Morel's
formula for the volume scattering function of pure sea water; only chi_p is
tabulated, from 41 measured scattering functions.

This does not tell you the bb of a Jerlov water type. Nothing does. It tells
you the bb of the water your instrument was in.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass

import numpy as np

from . import _data
from .water import ProvenanceWarning, _like_input

CITATION = (
    "Boss, E. and Pegau, W. S. (2001), 'Relationship of light scattering at "
    "an angle in the backward direction to the backscattering coefficient', "
    "Appl. Opt. 40, 5503-5507"
)
DOI = "10.1364/AO.40.005503"

#: Depolarisation ratio of pure sea water. Morel gives a range of 0.07 to
#: 0.11 and suggests 0.09, which is what Boss & Pegau use.
DEPOLARISATION_RATIO = 0.09

#: The angles the tabulation covers. Outside this the relation is not defined.
MIN_ANGLE_DEG, MAX_ANGLE_DEG = 90.0, 170.0

#: Above this the tabulated error exceeds 10 percent and a warning is raised.
_ERROR_WARN_PERCENT = 10.0


class AngleWarning(UserWarning):
    """The conversion is poorly constrained at the requested angle.

    The shape of the volume scattering function varies most near 90 and 180
    degrees, so a single-angle measurement there pins bb least well. Maffione
    & Dana (1997) recommend sensors covering roughly 110 to 160 degrees. Boss
    & Pegau (2001) recommend measuring near 117 degrees, and otherwise
    removing the water contribution first, which they support from near 90
    to 160 degrees.
    """


def _amplitude(wavelength_nm, salinity_psu) -> np.ndarray:
    """Morel's A(lambda, S), Boss & Pegau Eq. (4), in 1/(m sr)."""
    salinity = np.asarray(salinity_psu, dtype=float)
    if not np.all(np.isfinite(salinity)) or np.any(salinity < 0):
        # A negative salinity made pure water scatter less than fresh water,
        # without complaint.
        raise ValueError(
            f"salinity_psu must be a finite number, 0 or more, not "
            f"{salinity_psu!r}"
        )
    return (1.38 * (np.asarray(wavelength_nm, dtype=float) / 500.0) ** -4.32
            * (1 + 0.3 * salinity / 37.0) * 1e-4)


def _ratio() -> float:
    return (1 - DEPOLARISATION_RATIO) / (1 + DEPOLARISATION_RATIO)


def pure_water_vsf(angle_deg, wavelength_nm, salinity_psu: float = 37.0):
    """Volume scattering function of pure sea water, 1/(m sr).

    Morel's formula as given by Boss & Pegau Eqs. (4) and (5)::

        A(lambda, S) = 1.38 (lambda / 500 nm)^-4.32 (1 + 0.3 S / 37) 1e-4
        beta_w(theta) = A [1 + cos^2(theta) (1 - delta) / (1 + delta)]

    The amplitude carries about 15 percent uncertainty, which the authors give
    as the agreement between measurement and theory.
    """
    angle = np.asarray(angle_deg, dtype=float)
    amplitude = _amplitude(wavelength_nm, salinity_psu)
    out = amplitude * (1 + _ratio() * np.cos(np.radians(angle)) ** 2)
    # Angle and wavelength broadcast against each other; the answer is a
    # float only when neither of them was an array.
    if np.ndim(out) == 0:
        return float(out)
    return out


def pure_water_backscattering(wavelength_nm, salinity_psu: float = 37.0):
    """``bb_w``, the backscattering coefficient of pure sea water, 1/m.

    Obtained by integrating :func:`pure_water_vsf` over the backward
    hemisphere, which for this angular shape is analytic.
    """
    r = _ratio()
    amplitude = _amplitude(wavelength_nm, salinity_psu)
    # integral of (1 + r cos^2) sin over 90..180 degrees is 1 + r/3
    out = 2.0 * math.pi * amplitude * (1 + r / 3.0)
    return _like_input(np.atleast_1d(out), wavelength_nm)


def pure_water_scattering(wavelength_nm, salinity_psu: float = 37.0):
    """``b_w``, the total scattering coefficient of pure sea water, 1/m.

    :func:`pure_water_vsf` integrated over all directions. Its shape is
    symmetric about 90 degrees, so this is exactly twice
    :func:`pure_water_backscattering`; it is Morel's ``b_w = 16.06 beta_w(90)``
    with the depolarisation ratio used here.

    It is the ``bw`` that :func:`~jerlov.b_from_c` asks for, from the same
    formula as the rest of this module. Other tabulations of pure water
    scattering differ from Morel's by several percent; pass whichever one
    your c measurement was corrected with.
    """
    return 2.0 * pure_water_backscattering(wavelength_nm, salinity_psu)


def _chi_table():
    rows = [r for r in _data._rows("boss2001_chi.csv")
            if r["source"] == "boss2001"]
    angles = np.array([float(r["angle_deg"]) for r in rows])
    order = np.argsort(angles)
    return (angles[order],
            np.array([float(rows[i]["chi"]) for i in order]),
            np.array([float(rows[i]["percent_error"]) for i in order]))


def particulate_chi(angle_deg):
    """``chi_p`` at one angle, interpolated within Boss & Pegau Table 1.

    Refuses outside 90 to 170 degrees, the range their Table 1 covers.
    """
    angle = float(angle_deg)
    if not MIN_ANGLE_DEG <= angle <= MAX_ANGLE_DEG:
        raise ValueError(
            f"chi_p is tabulated from {MIN_ANGLE_DEG:g} to {MAX_ANGLE_DEG:g} "
            f"degrees and {angle:g} is outside that. Boss & Pegau tabulate no "
            "angle beyond 170 degrees, although their instrument reached "
            "177.3, and this package does not extrapolate."
        )
    angles, values, _ = _chi_table()
    return float(np.interp(angle, angles, values))


def _quoted_error(angle_deg: float) -> float:
    angles, _, errors = _chi_table()
    return float(np.interp(angle_deg, angles, errors))


@dataclass(frozen=True)
class Backscattering:
    """``bb`` recovered from a single-angle measurement."""

    bb: float | np.ndarray
    """Total backscattering coefficient, 1/m."""
    particulate: float | np.ndarray
    """The particle contribution, ``bb - bb_w``."""
    water: float | np.ndarray
    """``bb_w``, from Morel's formula rather than from your instrument."""
    angle_deg: float
    chi_p: float
    quoted_error_percent: float
    """Boss & Pegau's own spread for chi_p at this angle. Not a total error."""

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return (f"<Backscattering bb={np.mean(self.bb):.5f} 1/m at "
                f"{self.angle_deg:g} deg, chi_p={self.chi_p:.3f} "
                f"+-{self.quoted_error_percent:.1f}%>")


def bb_from_vsf(beta, angle_deg: float, wavelength_nm, *,
                salinity_psu: float = 37.0) -> Backscattering:
    """Convert a measured volume scattering function to ``bb``.

    Parameters
    ----------
    beta:
        The measured volume scattering function at ``angle_deg``, in
        1/(m sr). This is what the instrument reports once calibrated; it
        includes scattering by the water itself.
    angle_deg:
        The instrument's nominal scattering angle. 90 to 170 degrees.
    wavelength_nm, salinity_psu:
        Needed for the pure sea water terms, which are subtracted and then
        added back as ``bb_w``.

    Notes
    -----
    Boss & Pegau's water-removal route, their Eq. (10). Removing the water
    first matters because chi differs between water and particles everywhere
    except near 118 degrees, where the two curves cross; that is why
    instruments cluster near 120.

    The quoted error on the result is the spread of chi_p alone. The amplitude
    of the water term carries a further 15 percent, and your instrument's own
    calibration is on top of both.
    """
    angle = float(angle_deg)
    chi_p = particulate_chi(angle)
    error = _quoted_error(angle)
    if error > _ERROR_WARN_PERCENT:
        warnings.warn(
            f"chi_p at {angle:g} degrees carries a quoted spread of "
            f"{error:.1f}%, against 2.6-6.4% from 90 to 160 degrees. The "
            "scattering function varies steeply here and a single-angle "
            "measurement pins bb poorly.",
            AngleWarning,
            stacklevel=_data.caller_stacklevel(),
        )

    scalar = np.ndim(beta) == 0 and np.ndim(wavelength_nm) == 0
    beta = np.atleast_1d(np.asarray(beta, dtype=float))
    if np.any(beta < 0):
        raise ValueError("a volume scattering function cannot be negative")
    beta_w = np.atleast_1d(pure_water_vsf(angle, wavelength_nm, salinity_psu))
    bb_w = np.atleast_1d(pure_water_backscattering(wavelength_nm, salinity_psu))

    particulate = 2.0 * math.pi * chi_p * (beta - beta_w)
    if np.any(particulate < 0):
        warnings.warn(
            "the measured scattering is below that of pure sea water alone, "
            "so the particle contribution came out negative. Check the "
            "calibration, the wavelength and the salinity.",
            # Not an AngleWarning: the angle is not the problem, and a caller
            # filtering out angle advice must still be told about this.
            ProvenanceWarning,
            stacklevel=_data.caller_stacklevel(),
        )

    def shape(values):
        values = np.atleast_1d(values)
        return float(values[0]) if scalar else values

    return Backscattering(
        bb=shape(particulate + bb_w),
        particulate=shape(particulate),
        water=shape(np.broadcast_to(bb_w, particulate.shape)),
        angle_deg=angle,
        chi_p=chi_p,
        quoted_error_percent=error,
    )

"""The refractive index of sea water: Quan & Fry (1995). DECISIONS.md
section 124, DATA.md section 51."""

from __future__ import annotations

import warnings

import numpy as np

from . import _data
from .water import ProvenanceWarning

#: Quan & Fry's Eq. (3) coefficients, n0 to n9, as printed (p. 3479).
_QUAN1995 = (1.31405, 1.779e-4, -1.05e-6, 1.6e-8, -2.02e-6,
             15.868, 0.01155, -0.00423, -4382.0, 1.1455e6)
#: Their ranges of validity (p. 3479), ends included as Table 1 has them.
_QUAN1995_NM = (400.0, 700.0)
_QUAN1995_SALINITY = (0.0, 35.0)
_QUAN1995_TEMPERATURE = (0.0, 30.0)
#: Beyond the last measured wavelength of Table 1 the fit rests on Austin &
#: Halikas's values at 700 nm, which are their extrapolations (p. 3477).
_QUAN1995_LAST_MEASURED_NM = 643.8


def _within(value, name: str, bounds, unit: str, nan_ok: bool = False):
    array = np.array(value, dtype=float)      # a copy: never the caller's
    if np.any(np.isinf(array)) or (not nan_ok and np.any(np.isnan(array))):
        raise ValueError(f"{name} must be finite numbers"
                         + ("; NaN marks a gap" if nan_ok else ""))
    known = array[~np.isnan(array)] if array.ndim else (
        array if not np.isnan(array) else np.array([]))
    low, high = bounds
    if np.any(known < low) or np.any(known > high):
        raise ValueError(
            f"{name} must lie within {low:g}-{high:g}"
            f"{' ' + unit if unit else ''}, the range of "
            "Quan & Fry's equation (1995, p. 3479); it is not extrapolated")
    return array


@_data.positional_only()
def quan1995_refractive_index(wavelength_nm, /, *, salinity_psu,
                              temperature_c):
    """The refractive index of sea water at atmospheric pressure.

    Quan, X. and Fry, E. S. (1995), "Empirical equation for the index of
    refraction of seawater", Appl. Opt. 34(18), 3477-3480,
    doi:10.1364/AO.34.003477, Eq. (3)::

        n = n0 + (n1 + n2 T + n3 T^2) S + n4 T^2
            + (n5 + n6 S + n7 T) / l + n8 / l^2 + n9 / l^3

    with l the wavelength in nm, S the salinity and T the temperature in
    degrees Celsius; n0 to n9 as printed on p. 3479.

    Parameters
    ----------
    wavelength_nm:
        400 to 700 nm. NaN marks a gap and gives NaN.
    salinity_psu:
        0 to 35. No default: the water type does not fix it. The paper's S
        is in parts per thousand, from Copenhagen standard sea water and its
        dilutions; the difference between that and practical salinity is
        not modelled.
    temperature_c:
        0 to 30 degrees Celsius. No default.

    The three broadcast together. Values outside those ranges, the ranges
    of validity the paper states, are refused, not extrapolated.

    Returns
    -------
    The index, a float for scalar inputs, else an array.

    Notes
    -----
    The equation is a fit to the data Austin & Halikas (1976, SIO Ref.
    76-1) selected, reprinted as the paper's Table 1: 11 wavelengths from
    404.7 to 700 nm, fresh water and a salinity of 34.998, 1 to 30 C,
    measured by Mehu & Johannin-Gilles to a stated 3e-5, except the values
    at 700 nm, which are Austin & Halikas's extrapolations. The paper gives
    the fit's rms deviation from Table 1 as 1.5e-5. Above 643.8 nm, the
    last measured wavelength, the result rests on those extrapolations,
    and a :class:`ProvenanceWarning` says so.

    Pressure is not in the equation. The paper estimates (p. 3477) that
    at 100 m it raises the index by less than 1.37e-4.
    """
    wl = _within(wavelength_nm, "wavelength_nm", _QUAN1995_NM, "nm",
                 nan_ok=True)
    s = _within(salinity_psu, "salinity_psu", _QUAN1995_SALINITY, "")
    t = _within(temperature_c, "temperature_c", _QUAN1995_TEMPERATURE, "C")
    if np.any(wl > _QUAN1995_LAST_MEASURED_NM):
        warnings.warn(
            f"Above {_QUAN1995_LAST_MEASURED_NM:g} nm Quan & Fry's equation "
            "rests on Austin & Halikas's values at 700 nm, which are "
            "extrapolations, not measurements (Quan & Fry 1995, p. 3477).",
            ProvenanceWarning, stacklevel=_data.caller_stacklevel())
    n0, n1, n2, n3, n4, n5, n6, n7, n8, n9 = _QUAN1995
    n = (n0 + (n1 + n2 * t + n3 * t ** 2) * s + n4 * t ** 2
         + (n5 + n6 * s + n7 * t) / wl + n8 / wl ** 2 + n9 / wl ** 3)
    if all(np.ndim(x) == 0 for x in (wavelength_nm, salinity_psu,
                                     temperature_c)):
        return float(n)
    return n

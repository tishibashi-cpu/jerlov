"""Input files for radiative transfer codes: OSOAA and HydroLight.

This package does not solve the radiative transfer equation (DECISIONS.md
sections 12 and 38). These functions write a Jerlov type's absorption and
scattering, and a measured phase function, in the input formats of two
codes that do, for the caller to run (DECISIONS.md section 86):

- OSOAA (CS Group and LOA for CNES, GPL v3), run with ``-HYD.Model 3``:
  :func:`osoaa_user_profile` for ``-HYD.UserProfile`` and
  :func:`osoaa_phase_function` for ``-HYD.ExtData`` (OSOAA User Manual
  V2.0, 2025, sections 3.6.3 and 3.6.4, pp. 80-82).
- HydroLight (Sequoia Scientific): :func:`hydrolight_ac9_file`, the
  "standard format for ac-9 data" for its IOP DATA option (HydroLight 5.1
  Technical Documentation, Mobley 2012, section 7.3, pp. 55-56). HydroLight
  was not available here and its files were not run.

Both codes add pure water back to what they are given, their own pure
water, so the pure water to subtract is the caller's, with no default:
with the values the code will add, the code's total is the Jerlov type.
Each function returns the file's text; writing it is the caller's.
"""

from __future__ import annotations

import warnings

import numpy as np

from . import _data
from .petzold import ScatteringFunction
from .water import ProvenanceWarning, Water, _require_number

#: OSOAA's limit on the lines of a user profile, CTE_NZ_MAX_USER_PROFILE
#: in its OSOAA.h ("must be lower than").
_OSOAA_MAX_PROFILE = 500
#: OSOAA's limit on the angles of an external phase function,
#: CTE_MAXNB_ANG_EXT in its OSOAA.h.
_OSOAA_MAX_ANGLES = 200


def _water(water) -> Water:
    if not isinstance(water, Water):
        raise TypeError(
            f"water must be a jerlov.Water, not {type(water).__name__}")
    return water


def _source(water: Water) -> str:
    return water.source.citation if water.source is not None else (
        "the caller's own measurements")


def _depths(depths_m, *, minimum: int, limit: int | None) -> np.ndarray:
    if depths_m is None:
        raise ValueError("depths_m has no default: the depths are the run's")
    try:
        z = np.array(depths_m, dtype=float)
    except (TypeError, ValueError):
        raise ValueError("depths_m must be an array of numbers, in metres"
                         ) from None
    if z.ndim != 1 or z.size < minimum:
        raise ValueError(
            f"depths_m must be a 1-D array of at least {minimum} depths")
    _require_number(z, "depths_m")
    if not np.all(np.isfinite(z)):
        raise ValueError("depths_m must be finite")
    if z[0] != 0 or np.any(np.diff(z) <= 0):
        raise ValueError(
            "depths_m must start at 0, just below the surface, and ascend "
            "strictly")
    if limit is not None and z.size >= limit:
        raise ValueError(
            f"depths_m has {z.size} depths; the code takes fewer than "
            f"{limit}")
    return z


def _pure_water(pure_water, shape, label: str):
    if pure_water is None:
        raise ValueError(
            f"pure_water has no default: {label} adds its own pure water "
            "back to what it is given, so the pure water to subtract is the "
            "one it will add, (a_w, b_w)")
    try:
        a_w, b_w = pure_water
    except (TypeError, ValueError):
        raise ValueError("pure_water must be a pair (a_w, b_w)") from None
    out = []
    for name, values in (("a_w", a_w), ("b_w", b_w)):
        v = np.array(values, dtype=float)
        if v.ndim == 0:
            v = np.full(shape, float(v))
        elif v.shape != shape:
            raise ValueError(
                f"pure_water's {name} must be a number or have the shape of "
                "the wavelengths")
        if not np.all(np.isfinite(v)) or np.any(v < 0):
            raise ValueError(
                f"pure_water's {name} must be finite and not negative")
        out.append(v)
    return out


def _subtract(total, water_part, wl, name: str) -> np.ndarray:
    gaps = wl[np.isnan(total)]
    if gaps.size:
        raise ValueError(
            f"{name} has a gap (NaN) at {', '.join(f'{w:g}' for w in gaps)} "
            "nm; a code cannot be given a gap")
    rest = total - water_part
    negative = wl[rest < 0]
    if negative.size:
        raise ValueError(
            f"{name} less the pure water given is negative at "
            f"{', '.join(f'{w:g}' for w in negative)} nm: the code would "
            "read a negative coefficient. The water's own value is below "
            "the pure water's there")
    return rest


@_data.positional_only()
def osoaa_user_profile(water, wavelength_nm, /, *, depths_m,
                       pure_water) -> str:
    """OSOAA's ``-HYD.UserProfile`` file for a water at one wavelength.

    Five comment lines, then for each depth: the depth (m), the hydrosols'
    absorption a - a_w and their scattering b - b_w (1/m), the format of
    the OSOAA User Manual V2.0, section 3.6.4, pp. 81-82. OSOAA runs at
    one wavelength (``-OSOAA.Wa``), adds its own pure seawater back, and
    takes this file with ``-HYD.Model 3``.

    Parameters
    ----------
    water:
        A :class:`Water` with a and b.
    wavelength_nm:
        The run's wavelength, a number, inside the water's range.
    depths_m:
        Starting at 0, just below the surface, ascending, fewer than 500
        (OSOAA's limit). A Jerlov type does not vary with depth, so every
        depth carries the same values; OSOAA repeats the deepest to the
        seabed.
    pure_water:
        ``(a_w, b_w)`` at the wavelength, 1/m: the pure seawater OSOAA will
        add back, which its file ``fic/OSOAA_SEA_MOL_COEFFS_JUNE_2013.txt``
        tabulates. No default.

    Raises
    ------
    ValueError
        When a - a_w or b - b_w is negative, and for any input that is not
        a number, finite, or in range.
    """
    water = _water(water)
    wl = np.array(wavelength_nm, dtype=float)
    if wl.ndim != 0:
        raise ValueError("wavelength_nm must be one number: OSOAA runs at "
                         "one wavelength")
    _require_number(wl, "wavelength_nm")
    wl = wl.reshape(1)
    z = _depths(depths_m, minimum=1, limit=_OSOAA_MAX_PROFILE)
    a_w, b_w = _pure_water(pure_water, (1,), "OSOAA")
    a = _subtract(np.atleast_1d(np.asarray(water.a(wl), dtype=float)), a_w,
                  wl, "a")
    b = _subtract(np.atleast_1d(np.asarray(water.b(wl), dtype=float)), b_w,
                  wl, "b")
    lines = [
        "Column 1: Depth (in m)",
        "Column 2: Hydrosols absorption coefficient (in m-1)",
        "Column 3: Hydrosols scattering coefficient (in m-1)",
        f"Comment: {water._label()} at {wl[0]:g} nm from jerlov; source: "
        f"{_source(water)}",
        f"Comment: less pure water a_w = {a_w[0]:.9g}, b_w = {b_w[0]:.9g} "
        "per m, which OSOAA adds back",
    ]
    lines += [f"{d:.6g} {a[0]:.9g} {b[0]:.9g}" for d in z]
    # The manual: no blank line at the end of the file.
    return "\n".join(lines)


@_data.positional_only()
def osoaa_phase_function(scattering, /, *, minus_f12_over_f11,
                         f22_over_f11, f33_over_f11) -> str:
    """OSOAA's ``-HYD.ExtData`` file from one of Petzold's stations.

    F11 is the station's vsf / b at Petzold's 55 angles, from 180 degrees
    down, as the OSOAA User Manual V2.0 orders its example (section 3.6.3,
    pp. 80-81). OSOAA fits it with a spline in the cosine of the angle and
    normalises it; below Petzold's first angle, 0.1 degree, the spline is
    OSOAA's.

    Parameters
    ----------
    scattering:
        A :class:`ScatteringFunction`, from :func:`petzold_scattering`.
    minus_f12_over_f11, f22_over_f11, f33_over_f11:
        The polarization ratios -F12/F11, F22/F11 and F33/F11 of the
        Mueller matrix, each a number for every angle or one value per
        angle in Petzold's order (0.1 to 180 degrees). Petzold measured
        intensity only, so they have no default.

    Notes
    -----
    The file's first two lines are cross-sections in square micrometres
    in OSOAA's format. They carry the station's c and b in 1/m, which
    ``-HYD.Model 3`` does not read: two runs differing only in them gave
    identical results (DECISIONS.md section 86). The file is for that
    model, with :func:`osoaa_user_profile`, and its comment line says so.
    At the Bahamas and southern California stations the values below
    0.169 degree are the report's extension, and warn.
    """
    if not isinstance(scattering, ScatteringFunction):
        raise TypeError(
            "scattering must be a jerlov.ScatteringFunction, from "
            f"jerlov.petzold_scattering, not {type(scattering).__name__}")
    angles = np.asarray(scattering.angles_deg, dtype=float)
    n = angles.size
    if n > _OSOAA_MAX_ANGLES:      # pragma: no cover - Petzold has 55
        raise ValueError(f"OSOAA takes at most {_OSOAA_MAX_ANGLES} angles")
    ratios = []
    for name, values in (("minus_f12_over_f11", minus_f12_over_f11),
                         ("f22_over_f11", f22_over_f11),
                         ("f33_over_f11", f33_over_f11)):
        if values is None:
            raise ValueError(
                f"{name} has no default: Petzold measured the intensity of "
                "scattering only, not its polarization")
        v = np.array(values, dtype=float)
        if v.ndim == 0:
            v = np.full(n, float(v))
        if v.shape != (n,):
            raise ValueError(
                f"{name} must be a number or {n} values, one per Petzold "
                "angle")
        if not np.all(np.isfinite(v)):
            raise ValueError(f"{name} must be finite")
        ratios.append(v)
    flagged = [f"{a:g}" for a, s in zip(angles, scattering.statuses)
               if s in _data.QUESTIONABLE]
    if flagged:
        warnings.warn(
            f"the vsf of {scattering.station} at {', '.join(flagged)} "
            "degrees is the report's extension: nothing was measured below "
            "0.169 degree there. See DATA.md section 21.",
            ProvenanceWarning,
            stacklevel=_data.caller_stacklevel(),
        )
    f11 = scattering.phase_function()
    lines = [
        f"EXTINCTION_COEF : {scattering.c:.9g}",
        f"SCATTERING_COEF : {scattering.b:.9g}",
        f"NB_LINES : {n}",
        f"Angle F11 -F12/F11 F22/F11 F33/F11 | jerlov: Petzold (1972) "
        f"{scattering.station}, F11 = vsf/b (1/sr); the two lines above are "
        "c and b (1/m), not cross-sections, for -HYD.Model 3 only",
    ]
    for k in range(n - 1, -1, -1):
        lines.append(f"{angles[k]:.6g} {f11[k]:.9g} {ratios[0][k]:.9g} "
                     f"{ratios[1][k]:.9g} {ratios[2][k]:.9g}")
    return "\n".join(lines) + "\n"


@_data.positional_only()
def hydrolight_ac9_file(water, wavelengths, /, *, depths_m,
                        pure_water) -> str:
    """HydroLight's standard-format file of a and c, for its IOP DATA
    option.

    Ten header records, a record of the number of wavelengths and the
    wavelengths, then one record per depth of the depth, a - a_w at each
    wavelength and c - c_w at each, ended by the last record repeated with
    a depth of -1: the format of the HydroLight 5.1 Technical
    Documentation (Mobley 2012), section 7.3, pp. 55-56. HydroLight adds
    its own pure water back. It was not available here, and files written
    by this function have not been run.

    Parameters
    ----------
    water:
        A :class:`Water` with a and b.
    wavelengths:
        The wavelengths, nm, inside the water's range, strictly ascending.
    depths_m:
        At least two, from 0, ascending: HydroLight fits linear splines in
        depth. Every depth carries the same values, a Jerlov type not
        varying with depth.
    pure_water:
        ``(a_w, b_w)`` on ``wavelengths``, 1/m: the pure water HydroLight
        will add back. c_w = a_w + b_w. No default.

    Raises
    ------
    ValueError
        When a - a_w or c - c_w is negative, and for any input that is not
        a number, finite, or in range.
    """
    water = _water(water)
    wl = np.array(wavelengths, dtype=float)
    if wl.ndim != 1 or wl.size < 1:
        raise ValueError("wavelengths must be a 1-D array of numbers")
    _require_number(wl, "wavelengths")
    if np.any(np.diff(wl) <= 0):
        raise ValueError("wavelengths must be strictly ascending")
    z = _depths(depths_m, minimum=2, limit=None)
    a_w, b_w = _pure_water(pure_water, wl.shape, "HydroLight")
    a = _subtract(np.asarray(water.a(wl), dtype=float), a_w, wl, "a")
    c = _subtract(np.asarray(water.c(wl), dtype=float), a_w + b_w, wl, "c")
    header = [
        f"{water._label()}: absorption a and beam attenuation c, 1/m, less "
        "pure water, from jerlov",
        f"Source: {_source(water)}",
        "Pure water subtracted (HydroLight adds its own back): a_w and "
        "c_w = a_w + b_w as the caller gave them",
        "HydroLight 5.1 Technical Documentation section 7.3 standard format "
        "for ac-9 data (Mobley 2012)",
        "A Jerlov type does not vary with depth: every depth record is the "
        "same",
        "Record 11: the number of wavelengths and the wavelengths",
        "Records 12 on: depth, a(wavelength 1..n), c(wavelength 1..n)",
        "The last record repeats the previous one with depth -1",
        "Written by jerlov; not run in HydroLight",
        "depth " + " ".join(f"a({w:g})" for w in wl) + " "
        + " ".join(f"c({w:g})" for w in wl),
    ]
    records = [f"{wl.size} " + " ".join(f"{w:g}" for w in wl)]
    values = " ".join(f"{v:.9g}" for v in np.concatenate([a, c]))
    records += [f"{d:.6g} {values}" for d in z]
    records.append(f"-1.0 {values}")
    return "\n".join(header + records) + "\n"

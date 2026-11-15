"""Input files for radiative transfer codes, OSOAA and HydroLight, and
OSOAA's results read back.

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

OSOAA's results are read back by :func:`read_osoaa_flux`,
:func:`read_osoaa_radiance_vs_depth` and :func:`read_osoaa_radiance_vs_vza`
(DECISIONS.md section 87), each from the text of one file, the values as
OSOAA prints them: normalized to the extraterrestrial solar irradiance,
which OSOAA leaves to the user and so does this package.
"""

from __future__ import annotations

import math
import re
import warnings
from dataclasses import dataclass

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


def _printed(values: np.ndarray, name: str) -> list[str]:
    """Each value as written to a file, in full; refused if, read back, the
    printed values do not ascend strictly (DECISIONS.md section 88)."""
    text = [f"{float(v):.15g}" for v in values]
    back = np.array([float(s) for s in text])
    if np.any(np.diff(back) <= 0):
        raise ValueError(
            f"{name} must be strictly ascending as written: two of them "
            "print alike to 15 significant digits")
    return text


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
    lines += [f"{d} {a[0]:.9g} {b[0]:.9g}"
              for d in _printed(z, "depths_m")]
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
        angle in Petzold's order (0.1 to 180 degrees), each in [-1, 1]:
        no element of the Mueller matrix exceeds F11 in magnitude. Petzold
        measured intensity only, so they have no default.

    Notes
    -----
    The file's first two lines are cross-sections in square micrometres
    in OSOAA's format. They carry the station's c and b in 1/m, which
    ``-HYD.Model 3`` does not read: two runs differing only in them gave
    identical results (DECISIONS.md section 86). The file is for that
    model, with :func:`osoaa_user_profile`, and its comment line says so.
    At the Bahamas and southern California stations the values below
    0.169 degree are the report's extension, and warn.

    OSOAA truncates the forward peak of the hydrosols' phase function.
    With Petzold's it treated 96.5 to 97.8 percent of the hydrosols'
    scattering as unscattered, more than Petzold's functions hold within
    23 degrees, and its Kd came out 0.7 to 23 percent below that of a
    Monte Carlo checked against Morel and Loisel's relation, the more so
    the larger b/a (DATA.md section 38, DECISIONS.md section 92). Check
    the truncation coefficient in ``PM_PHYTO.txt`` before trusting a run.
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
        outside = np.flatnonzero(np.abs(v) > 1)
        if outside.size:
            raise ValueError(
                f"{name} is {v[outside[0]]:g} at {angles[outside[0]]:g} "
                "degrees: no element of a Mueller matrix of scattering "
                "exceeds F11 in magnitude, so the ratio lies in [-1, 1]")
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
    wl_text = _printed(wl, "wavelengths")
    z_text = _printed(z, "depths_m")
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
        "depth " + " ".join(f"a({w})" for w in wl_text) + " "
        + " ".join(f"c({w})" for w in wl_text),
    ]
    records = [f"{wl.size} " + " ".join(wl_text)]
    values = " ".join(f"{v:.9g}" for v in np.concatenate([a, c]))
    records += [f"{d} {values}" for d in z_text]
    records.append(f"-1.0 {values}")
    return "\n".join(header + records) + "\n"


# -- OSOAA's results (DECISIONS.md section 87) ------------------------------


def _text(text, name: str) -> list[str]:
    if not isinstance(text, str):
        raise TypeError(
            f"{name} reads the text of the file, not "
            f"{type(text).__name__}: pass pathlib.Path(...).read_text()")
    return text.splitlines()


def _expect(lines: list[str], first: str, name: str) -> None:
    head = lines[0].strip() if lines else ""
    if not head.startswith(first):
        raise ValueError(
            f"{name} expects a file whose first line starts {first!r}; "
            f"this one starts {head[:60]!r}")


def _numbers(line: str, k: int, n: int) -> list[float]:
    fields = line.split()
    if len(fields) != n:
        raise ValueError(
            f"line {k + 1} has {len(fields)} values, not {n}: "
            f"{line.strip()!r}")
    if any("*" in f for f in fields):
        raise ValueError(
            f"line {k + 1} has a field OSOAA could not print (***): "
            f"{line.strip()!r}")
    try:
        values = [float(f) for f in fields]
    except ValueError:
        raise ValueError(
            f"line {k + 1} is not all numbers: {line.strip()!r}") from None
    if not all(math.isfinite(v) for v in values):
        raise ValueError(f"line {k + 1} has a value that is not finite: "
                         f"{line.strip()!r}")
    return values


def _rows(lines: list[str], column_head: str, n: int, name: str):
    """The numeric rows after the line of column names."""
    starts = [k for k, line in enumerate(lines)
              if line.split()[:1] == [column_head]]
    if not starts:
        raise ValueError(f"{name}: no line of column names starting "
                         f"{column_head!r}")
    start = starts[-1] + 1
    rows = [(k, line) for k, line in enumerate(lines[start:], start)
            if line.strip()]
    if not rows:
        raise ValueError(f"{name}: no values after the column names")
    return [(k, line, _numbers(line, k, n)) for k, line in rows]


def _frozen(*arrays) -> None:
    for array in arrays:
        array.setflags(write=False)


def _header_value(lines: list[str], label: str, name: str) -> float:
    for line in lines:
        if line.strip().startswith(label):
            try:
                return float(line.split(":", 1)[1].split()[0])
            except (IndexError, ValueError):
                break
    raise ValueError(f"{name}: no {label!r} line with a value")


@_data.compared_by_value
@dataclass(frozen=True, eq=False)
class OsoaaFlux:
    """OSOAA's profile of fluxes, ``Flux.txt``, as it prints them.

    The fluxes are normalized so that the extraterrestrial solar irradiance
    is pi: multiply by Esun / pi for W/m2 (OSOAA User Manual V2.0, section
    3.5.6). "Direct" is not the unscattered beam: OSOAA truncates the
    forward peak of the hydrosols' phase function and counts the light so
    removed as transmitted (section 4.2.3). The totals are unaffected.
    """

    level: np.ndarray
    """OSOAA's level numbers, from the top of the atmosphere down."""
    altitude_m: np.ndarray
    """As printed: positive in the atmosphere, negative in the sea."""
    in_sea: np.ndarray
    """True for the levels in the sea, the sign of the printed altitude,
    -0.00000 included: OSOAA prints the surface once above (0.00000) and
    twice below."""
    direct_down: np.ndarray
    """The direct downward flux, normalized, after OSOAA's truncation."""
    diffuse_down: np.ndarray
    """The diffuse downward flux, normalized."""
    total_down: np.ndarray
    """Ed, normalized."""
    direct_up: np.ndarray
    """The direct upward flux, normalized."""
    diffuse_up: np.ndarray
    """The diffuse upward flux, normalized."""
    total_up: np.ndarray
    """Eu, normalized."""
    up_over_down: np.ndarray
    """Eu / Ed as OSOAA prints it."""

    @property
    def sea_depths_m(self) -> np.ndarray:
        """The depths of the sea's levels, positive, from the surface."""
        return -self.altitude_m[self.in_sea]

    def kd(self, upper_m: float, lower_m: float) -> float:
        """The mean Kd of Ed between two depths, 1/m.

        ``ln(Ed(upper) / Ed(lower)) / (lower - upper)``, with ln Ed
        interpolated linearly between OSOAA's levels and the first level
        below the surface standing for depth 0. Depths outside the levels
        are refused.
        """
        upper = float(upper_m)
        lower = float(lower_m)
        z = self.sea_depths_m
        ed = self.total_down[self.in_sea]
        # Keep the first of levels at equal depth: the two at the surface.
        keep = np.concatenate([[True], np.diff(z) > 0])
        z, ed = z[keep], ed[keep]
        if not (math.isfinite(upper) and math.isfinite(lower)):
            raise ValueError("the depths must be finite")
        if not 0 <= upper < lower:
            raise ValueError("need 0 <= upper_m < lower_m")
        if lower > z[-1]:
            raise ValueError(
                f"lower_m = {lower:g} m is below the deepest level, "
                f"{z[-1]:g} m")
        if np.any(ed <= 0):
            raise ValueError("Ed is not positive at every level")
        log_ed = np.interp([upper, lower], z, np.log(ed))
        return float((log_ed[0] - log_ed[1]) / (lower - upper))


@_data.positional_only()
def read_osoaa_flux(text, /) -> OsoaaFlux:
    """Read OSOAA's ``Advanced_outputs/Flux.txt``.

    ``text`` is the file's text. Five header lines, then for each level
    its number, altitude and the seven columns of the OSOAA User Manual
    V2.0, section 3.5.6, pp. 75-76. Lines that are not nine numbers, and
    fields OSOAA could not print, are refused.
    """
    name = "read_osoaa_flux"
    lines = _text(text, name)
    _expect(lines, "Profile of downward and upward fluxes", name)
    rows = _rows(lines, "Level", 9, name)
    values = np.array([r[2] for r in rows])
    sea = np.array([line.split()[1].startswith("-") for _, line, _ in rows])
    level = values[:, 0].astype(int)
    columns = [np.ascontiguousarray(values[:, k]) for k in range(1, 9)]
    _frozen(level, sea, *columns)
    return OsoaaFlux(level, columns[0], sea, *columns[1:])


@_data.compared_by_value
@dataclass(frozen=True, eq=False)
class OsoaaRadianceProfile:
    """OSOAA's radiance against depth, ``RESLUM_vsZ.txt``, as it prints
    it.

    The radiances are normalized, I = pi L / Esun in 1/sr (multiply by
    Esun / pi for W/m2/sr), and the reflectances are pi L / Ed (OSOAA User
    Manual V2.0, section 3.5.1). Angles are in degrees.
    """

    direction: str
    """``"upward"`` or ``"downward"``, as the header says."""
    relative_azimuth_deg: float
    """The relative azimuth of the header (180: sensor and sun in the same
    half-plane)."""
    viewing_zenith_deg: float
    """The viewing zenith angle of the header."""
    depth_m: np.ndarray
    """Positive, from the surface; OSOAA prints them negative."""
    scattering_angle_deg: np.ndarray
    """The scattering angle of each row."""
    radiance: np.ndarray
    """I = pi L / Esun, 1/sr."""
    reflectance: np.ndarray
    """pi L / Ed."""
    polarization_percent: np.ndarray
    """The degree of polarization, percent."""
    polarized_radiance: np.ndarray
    """pi L_pol / Esun, 1/sr."""
    polarized_reflectance: np.ndarray
    """pi L_pol / Ed."""


@_data.compared_by_value
@dataclass(frozen=True, eq=False)
class OsoaaRadianceScan:
    """OSOAA's radiance against the viewing zenith angle,
    ``RESLUM_vsVZA.txt``, as it prints it.

    The radiances are normalized, I = pi L / Esun in 1/sr (multiply by
    Esun / pi for W/m2/sr), and the reflectances are pi L / Ed (OSOAA User
    Manual V2.0, section 3.5.1). Angles are in degrees.
    """

    level: str
    """The header's line naming the output level, as printed."""
    altitude_m: float
    """That level's altitude, m: negative in the sea."""
    azimuth_negative_deg: float
    """The relative azimuth for negative viewing zenith angles."""
    azimuth_positive_deg: float
    """The relative azimuth for positive viewing zenith angles."""
    viewing_zenith_deg: np.ndarray
    """Signed by the half-plane, as OSOAA prints them; the angle 0
    appears twice, as -0 and 0, one row for each half-plane."""
    scattering_angle_deg: np.ndarray
    """The scattering angle of each row."""
    radiance: np.ndarray
    """I = pi L / Esun, 1/sr."""
    reflectance: np.ndarray
    """pi L / Ed."""
    polarization_percent: np.ndarray
    """The degree of polarization, percent."""
    polarized_radiance: np.ndarray
    """pi L_pol / Esun, 1/sr."""
    polarized_reflectance: np.ndarray
    """pi L_pol / Ed."""


def _radiance_columns(rows) -> list[np.ndarray]:
    values = np.array([r[2] for r in rows])
    columns = [np.ascontiguousarray(values[:, k]) for k in range(7)]
    _frozen(*columns)
    return columns


@_data.positional_only()
def read_osoaa_radiance_vs_depth(text, /) -> OsoaaRadianceProfile:
    """Read OSOAA's ``Standard_outputs/RESLUM_vsZ.txt``.

    ``text`` is the file's text: the header's relative azimuth and viewing
    zenith angle, then for each depth the six columns of the OSOAA User
    Manual V2.0, section 3.5.1. The two rows at depth 0 are OSOAA's two
    levels just below the surface.
    """
    name = "read_osoaa_radiance_vs_depth"
    lines = _text(text, name)
    _expect(lines, "STANDARD RESULTS", name)
    if not any("RADIANCE FIELD VERSUS THE SEA DEPTH" in line
               for line in lines[:3]):
        raise ValueError(f"{name}: not a file of radiance against depth")
    azimuth = _header_value(lines, "Simulated relative azimuth", name)
    for label, direction in (("Upward direction VZA", "upward"),
                             ("Downward direction VZA", "downward")):
        if any(line.strip().startswith(label) for line in lines):
            vza = _header_value(lines, label, name)
            break
    else:
        raise ValueError(f"{name}: no viewing zenith angle in the header")
    z, *columns = _radiance_columns(_rows(lines, "Z", 7, name))
    depth = np.abs(z)
    if np.any(z > 0):
        raise ValueError(f"{name}: a depth is printed positive")
    _frozen(depth)
    return OsoaaRadianceProfile(direction, azimuth, vza, depth, *columns)


#: The forms of the output level in RESLUM_vsVZA.txt's header (OSOAA's
#: OSOAA_SOS.F), and the factor from the printed value to metres.
_LEVELS = (
    ("TOA level - Altitude (km) :", 1000.0),
    ("Sea bottom level - Depth (m) :", 1.0),
    ("Above sea surface level 0+ - Altitude (km) :", 1000.0),
    ("Under sea surface level 0- - Depth (m) :", 1.0),
    ("Requested value of the depth for the output(m) :", None),
    ("Value of the depth selected for the output (m) :", 1.0),
    ("Altitude (km) :", 1000.0),
)


def _level(lines: list[str], name: str) -> tuple[str, float]:
    for line in lines:
        stripped = line.strip()
        for label, factor in _LEVELS:
            if not stripped.startswith(label):
                continue
            rest = stripped[len(label):]
            numbers = re.findall(r"-?\d+\.?\d*(?:[Ee][-+]?\d+)?", rest)
            if not numbers:
                break
            if factor is None:
                # "... ==> limited to the max computed depth : Z": the last.
                return stripped, float(numbers[-1])
            if label == "Altitude (km) :" and len(numbers) > 1:
                # "Altitude (km) : asked limited to the maximum altitude Z".
                return stripped, float(numbers[-1]) * factor
            return stripped, float(numbers[0]) * factor
    raise ValueError(f"{name}: no output level in the header")


@_data.positional_only()
def read_osoaa_radiance_vs_vza(text, /) -> OsoaaRadianceScan:
    """Read OSOAA's ``Standard_outputs/RESLUM_vsVZA.txt``.

    ``text`` is the file's text: the header's two relative azimuths and the
    output level, then for each viewing zenith angle the six columns of
    the OSOAA User Manual V2.0, section 3.5.1.
    """
    name = "read_osoaa_radiance_vs_vza"
    lines = _text(text, name)
    _expect(lines, "STANDARD RESULTS", name)
    if not any("RADIANCE FIELD VERSUS THE VIEWING ZENITH ANGLE" in line
               for line in lines[:3]):
        raise ValueError(
            f"{name}: not a file of radiance against viewing zenith angle")
    negative = _header_value(lines, "for VZA < 0", name)
    positive = _header_value(lines, "for VZA > 0", name)
    level, altitude = _level(lines, name)
    vza, *columns = _radiance_columns(_rows(lines, "VZA", 7, name))
    return OsoaaRadianceScan(level, altitude, negative, positive, vza,
                             *columns)

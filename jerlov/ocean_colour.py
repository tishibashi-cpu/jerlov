"""Kd without a water type, the colour of the sea from above, and the
Secchi depth.

Four published relations, each from its primary paper, with the quantities
the papers do not fix left to the caller (DECISIONS.md section 66):

- Kd from the chlorophyll concentration of case 1 water, Morel &
  Maritorena (2001);
- Kd from the absorption and backscattering coefficients and the sun, Lee,
  Du & Arnone (2005) and Lee et al. (2013);
- the remote sensing reflectance from a and bb, Gordon et al. (1988) and
  Lee, Carder & Arnone (2002);
- the Secchi depth from Kd and the remote sensing reflectance, Lee et al.
  (2015).

All are forward relations. None reads satellite data, and the inverse, from
the reflectance to a and bb, is not here.
"""

from __future__ import annotations

import warnings

import numpy as np

from . import _data
from .water import ProvenanceWarning, _like_input, _support

MOREL2001 = (
    "Morel, A. and Maritorena, S. (2001), 'Bio-optical properties of "
    "oceanic waters: A reappraisal', J. Geophys. Res. 106(C4), 7163-7180, "
    "doi:10.1029/2000JC000319"
)
LEE2005 = (
    "Lee, Z.-P., Du, K.-P. and Arnone, R. (2005), 'A model for the diffuse "
    "attenuation coefficient of downwelling irradiance', J. Geophys. Res. "
    "110, C02016, doi:10.1029/2004JC002275"
)
LEE2013 = (
    "Lee, Z., Hu, C., Shang, S., Du, K., Lewis, M., Arnone, R. and Brewin, "
    "R. (2013), 'Penetration of UV-visible solar radiation in the global "
    "oceans: Insights from ocean color remote sensing', J. Geophys. Res. "
    "Oceans 118, 4241-4255, doi:10.1002/jgrc.20308"
)
GORDON1988 = (
    "Gordon, H. R., Brown, O. B., Evans, R. H., Brown, J. W., Smith, R. C., "
    "Baker, K. S. and Clark, D. K. (1988), 'A semianalytic radiance model "
    "of ocean color', J. Geophys. Res. 93(D9), 10909-10924, "
    "doi:10.1029/JD093iD09p10909"
)
LEE2002 = (
    "Lee, Z., Carder, K. L. and Arnone, R. A. (2002), 'Deriving inherent "
    "optical properties from water color: a multiband quasi-analytical "
    "algorithm for optically deep waters', Appl. Opt. 41, 5755-5772, "
    "doi:10.1364/AO.41.005755"
)
LEE2015 = (
    "Lee, Z., Shang, S., Hu, C., Du, K., Weidemann, A., Hou, W., Lin, J. "
    "and Lin, G. (2015), 'Secchi disk depth: A new theory and mechanistic "
    "model for underwater visibility', Remote Sens. Environ. 169, 139-149, "
    "doi:10.1016/j.rse.2015.08.002"
)

#: g0 and g1 of rrs = g0 u + g1 u^2, as Gordon et al. (1988) eq. (2) gives
#: them (l1 and l2, p. 10910).
GORDON1988_RRS_COEFFICIENTS = (0.0949, 0.0794)
#: g0 and g1 of Lee, Carder & Arnone (2002, p. 5756): the mean of Gordon et
#: al.'s pair and a pair for coastal water from another paper.
LEE2002_RRS_COEFFICIENTS = (0.0895, 0.1247)

#: Chlorophyll concentrations, mg m^-3, that Morel & Maritorena's pooled
#: data spanned: 0.02 to more than 30 (p. 7164).
_MOREL_CHL = (0.02, 30.0)
#: Sun zenith angles, degrees, of the Hydrolight runs each Kd model was
#: fitted to, and the range of Kd, 1/m, it is stated to be good for.
_LEE2005_SUN, _LEE2005_KD = (10.0, 60.0), (0.05, 5.7)
_LEE2013_SUN, _LEE2013_KD = (5.0, 60.0), (0.02, 5.0)
#: Lee et al. (2015): the white disc seen through the surface, the eye's
#: threshold contrast (sr^-1), and the factor for the two-way path.
_DISC, _THRESHOLD, _PATH = 0.14, 0.013, 2.5
#: The Secchi depths of their validation, m (pp. 146-147).
_LEE2015_DEPTHS = (0.1, 30.0)


def _warn(message: str) -> None:
    warnings.warn(message, ProvenanceWarning,
                  stacklevel=_data.caller_stacklevel())


def _single(value, name: str, unit: str) -> float:
    if np.ndim(value) != 0 or not np.isfinite(value) or float(value) <= 0:
        raise ValueError(f"{name} must be one finite positive number, "
                         f"{unit}, not {value!r}")
    return float(value)


def _finite(value, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite numbers")
    return array


def _spectral(value, name: str) -> np.ndarray:
    """A spectral quantity: NaN marks a gap and passes through, as it does
    everywhere in the package; infinity is refused."""
    array = np.asarray(value, dtype=float)
    if np.any(np.isinf(array)):
        raise ValueError(f"{name} must not be infinite; NaN marks a gap")
    return array


def _sun(sun_zenith_deg, fitted: tuple[float, float], paper: str
         ) -> np.ndarray:
    sun = _finite(sun_zenith_deg, "sun_zenith_deg")
    if np.any(sun < 0) or np.any(sun >= 90):
        raise ValueError("sun_zenith_deg must lie in [0, 90) degrees")
    lo, hi = fitted
    if np.any(sun < lo) or np.any(sun > hi):
        _warn(f"a sun at {lo:g}-{hi:g} degrees from the zenith is what "
              f"{paper} fitted the model to; outside that the result is "
              "the model's, not its fit.")
    return sun


def _kd_range(kd: np.ndarray, stated: tuple[float, float], paper: str
              ) -> None:
    lo, hi = stated
    known = kd[~np.isnan(kd)]
    if known.size and (np.min(known) < lo or np.max(known) > hi):
        _warn(f"{paper} state the model good for Kd of about {lo:g} to "
              f"{hi:g} 1/m; some of these values lie outside that.")


def _result(value: np.ndarray, *inputs):
    if all(np.ndim(x) == 0 for x in inputs):
        return float(value)
    return value


@_data.positional_only()
def morel2001_kd(wavelengths, /, *, chlorophyll_mg_m3: float):
    """Kd of case 1 water from its chlorophyll concentration.

    Morel, A. and Maritorena, S. (2001), "Bio-optical properties of oceanic
    waters: A reappraisal", J. Geophys. Res. 106(C4), 7163-7180,
    doi:10.1029/2000JC000319. Eqs. (3) and (5)::

        Kd = Kw + chi [Chl]^e

    with Kw, chi and e from their Table 2, 350-700 nm every 5 nm. Kd is
    computed on that grid and interpolated linearly between.

    Parameters
    ----------
    wavelengths:
        nm, a number or an array, within 350-700 nm.
    chlorophyll_mg_m3:
        [Chl], mg m^-3: chlorophyll a plus divinyl chlorophyll a, as by
        HPLC (p. 7164). One number; no default.

    Returns
    -------
    Kd, 1/m: a float for a number, an array otherwise. It is the Kd of the
    upper layer, from the surface to about one penetration depth (pp.
    7165-7166).

    Notes
    -----
    The relation is a statistical mean for case 1 water, whose optical
    properties follow its phytoplankton; individual waters scatter about it
    (p. 7164), and coastal water with sediment or dissolved matter of other
    origin is not case 1. The data spanned 0.02 to more than 30 mg m^-3
    (p. 7164); outside 0.02-30 the result comes with a
    :class:`ProvenanceWarning`.

    Below 400 nm Table 2 repeats the chi and e that Morel & Antoine (1994)
    extrapolated, which the authors call a lower limit for oligotrophic
    water and found unsuited to their Mediterranean data (p. 7170); those
    wavelengths warn too. Beyond 590-600 nm the values are Morel's (1988),
    not revised (p. 7168). DATA.md section 27, DECISIONS.md section 66.
    """
    chl = _single(chlorophyll_mg_m3, "chlorophyll_mg_m3", "mg m^-3")
    query = np.atleast_1d(np.asarray(wavelengths, dtype=float))
    grid, kw, e, chi, statuses = _data.morel2001()
    if (not np.all(np.isfinite(query)) or np.any(query < grid[0])
            or np.any(query > grid[-1])):
        raise ValueError(
            f"wavelengths must lie within {grid[0]:g}-{grid[-1]:g} nm, the "
            "range of Morel & Maritorena's Table 2. This package does not "
            "extrapolate.")
    lo, hi = _MOREL_CHL
    if not lo <= chl <= hi:
        _warn(f"[Chl] = {chl:g} mg m^-3 is outside the {lo:g}-{hi:g} that "
              "Morel & Maritorena's data spanned; the result is their "
              "relation carried beyond its data.")
    flagged = sorted({grid[j] for samples in _support(grid, query.ravel())
                      for j in samples if statuses[j] in _data.QUESTIONABLE})
    if flagged:
        _warn("below 400 nm Morel & Maritorena (2001) repeat the chi and e "
              "that Morel & Antoine (1994) extrapolated, a lower limit for "
              "oligotrophic water (p. 7170); the result rests on them at "
              + ", ".join(f"{w:g}" for w in flagged) + " nm.")
    kd = kw + chi * chl ** e
    out = np.interp(query.ravel(), grid, kd).reshape(query.shape)
    return _like_input(out, wavelengths)


#: The [Chl] range of Bricaud et al. (1995), mg m^-3 (abstract).
_BRICAUD_CHL = (0.02, 25.0)


@_data.positional_only()
def bricaud1995_aph(wavelengths, /, *, chlorophyll_mg_m3: float):
    """Absorption by phytoplankton, aph, from the chlorophyll concentration.

    Bricaud, A., Babin, M., Morel, A. and Claustre, H. (1995),
    "Variability in the chlorophyll-specific absorption coefficients of
    natural phytoplankton: Analysis and parameterization", J. Geophys. Res.
    100(C7), 13321-13332, doi:10.1029/95JC00463. Table 2::

        a*ph = A [Chl]^-B,    aph = [Chl] a*ph = A [Chl]^(1 - B)

    with A and B every 2 nm from 400 to 700 nm and at 675 nm. aph is
    computed at those wavelengths and interpolated linearly between them;
    outside 400-700 nm it raises :class:`ValueError`.

    Parameters
    ----------
    wavelengths:
        nm, a number or an array, within 400-700 nm.
    chlorophyll_mg_m3:
        [Chl], mg m^-3: chlorophyll a plus divinyl chlorophyll a. One
        number; no default.

    Returns
    -------
    aph, 1/m: a float for a number, an array otherwise.

    Notes
    -----
    A statistical mean of 815 spectra from many oceans, spanning [Chl]
    0.02-25 mg m^-3; outside that range the result comes with a
    :class:`ProvenanceWarning`. Individual waters scatter widely about it,
    and the fit is poor where phytoplankton absorb little: r2 on the
    log-transformed data is below 0.01 from 556 to 578 nm and at 696 and
    698 nm (Table 2). Only
    phytoplankton: nonalgal particles, dissolved matter and water are not
    included. Bricaud et al. (1998) refit the relation to 1166 spectra
    but print the spectral coefficients only as a figure. DATA.md section
    31, DECISIONS.md section 72.
    """
    chl = _single(chlorophyll_mg_m3, "chlorophyll_mg_m3", "mg m^-3")
    query = np.atleast_1d(np.asarray(wavelengths, dtype=float))
    grid, a, b = _data.bricaud1995()
    if (not np.all(np.isfinite(query)) or np.any(query < grid[0])
            or np.any(query > grid[-1])):
        raise ValueError(
            f"wavelengths must lie within {grid[0]:g}-{grid[-1]:g} nm, the "
            "range of Bricaud et al.'s Table 2. This package does not "
            "extrapolate.")
    lo, hi = _BRICAUD_CHL
    if not lo <= chl <= hi:
        _warn(f"[Chl] = {chl:g} mg m^-3 is outside the {lo:g}-{hi:g} that "
              "Bricaud et al.'s (1995) data spanned; the result is their "
              "relation carried beyond its data.")
    aph = a * chl ** (1.0 - b)
    out = np.interp(query.ravel(), grid, aph).reshape(query.shape)
    return _like_input(out, wavelengths)


#: Morel & Maritorena (2001) eq. (13): the bracket 0.50 - 0.25 log10 [Chl]
#: is zero here and negative above.
_BBP_CHL_LIMIT = 100.0


@_data.positional_only()
def morel2001_bbp(wavelengths, /, *, chlorophyll_mg_m3: float):
    """Backscattering by particles, bbp, from the chlorophyll concentration.

    Morel, A. and Maritorena, S. (2001), J. Geophys. Res. 106(C4),
    7163-7180, doi:10.1029/2000JC000319, eqs. (13), (14) and (9)::

        bbp = {0.002 + 0.01 [0.50 - 0.25 log10 Chl] (l/550)^v} bp550
        v = (1/2)(log10 Chl - 0.3)    for Chl < 2 mg m^-3
        v = 0                         above 2
        bp550 = 0.30 Chl^0.62

    Parameters
    ----------
    wavelengths:
        nm, a number or an array, within 350-700 nm, the model's domain.
    chlorophyll_mg_m3:
        [Chl], mg m^-3. One number; no default.

    Returns
    -------
    bbp, 1/m: a float for a number, an array otherwise. Add pure water's
    backscattering for the total bb (their eq. 11).

    Notes
    -----
    This is the form the paper's model uses. Its eq. (10) is the 1988
    form (a maximum efficiency of 0.02 and a (550/l) dependence at every
    [Chl]), which the paper then modifies "in two ways" into (13) and (14)
    (p. 7171). Eq. (9) is the paper's; its (9'), which subtracts
    pure water's scattering at 550 nm, is called negligible there and is
    not applied. (14) is written for 0.02-2 mg m^-3 and is used as written
    below 0.02, with a :class:`ProvenanceWarning`, as is anything above
    30; above 100 mg m^-3, where the bracket turns negative, it raises
    :class:`ValueError`. DATA.md section 31, DECISIONS.md section 72.
    """
    chl = _single(chlorophyll_mg_m3, "chlorophyll_mg_m3", "mg m^-3")
    query = np.atleast_1d(np.asarray(wavelengths, dtype=float))
    lo_nm, hi_nm = 350.0, 700.0
    if (not np.all(np.isfinite(query)) or np.any(query < lo_nm)
            or np.any(query > hi_nm)):
        raise ValueError(
            f"wavelengths must lie within {lo_nm:g}-{hi_nm:g} nm, the "
            "domain of Morel & Maritorena's model. This package does not "
            "extrapolate.")
    if chl > _BBP_CHL_LIMIT:
        raise ValueError(
            f"[Chl] = {chl:g} mg m^-3 is above {_BBP_CHL_LIMIT:g}, where the "
            "term 0.50 - 0.25 log10 [Chl] of eq. (13) is negative")
    lo, hi = _MOREL_CHL
    if not lo <= chl <= hi:
        _warn(f"[Chl] = {chl:g} mg m^-3 is outside the {lo:g}-{hi:g} that "
              "Morel & Maritorena's data spanned; the result is their "
              "relation carried beyond its data.")
    v = 0.5 * (np.log10(chl) - 0.3) if chl < 2.0 else 0.0
    bp550 = 0.30 * chl ** 0.62
    out = (0.002 + 0.01 * (0.50 - 0.25 * np.log10(chl))
           * (query / 550.0) ** v) * bp550
    return _like_input(out, wavelengths)


def _check_iops(a, bb) -> tuple[np.ndarray, np.ndarray]:
    a = _spectral(a, "a")
    bb = _spectral(bb, "bb")
    if np.any(a <= 0) or np.any(bb <= 0):
        raise ValueError("a and bb must be positive, in 1/m; NaN marks a "
                         "gap and gives NaN")
    return a, bb


@_data.positional_only()
def lee2005_kd(a, bb, /, *, sun_zenith_deg):
    """Kd from the absorption and backscattering coefficients and the sun.

    Lee, Z.-P., Du, K.-P. and Arnone, R. (2005), "A model for the diffuse
    attenuation coefficient of downwelling irradiance", J. Geophys. Res.
    110, C02016, doi:10.1029/2004JC002275. Eq. (11)::

        Kd = (1 + 0.005 theta) a + 4.18 (1 - 0.52 exp(-10.8 a)) bb

    Parameters
    ----------
    a, bb:
        Absorption and backscattering coefficients, 1/m, positive; numbers
        or arrays that broadcast together and with the sun. NaN marks a
        gap and gives NaN.
    sun_zenith_deg:
        theta, the sun's zenith angle above the surface, degrees, in
        [0, 90). No default.

    Returns
    -------
    Kd(E10%), 1/m: the mean from the surface to the depth where the
    downwelling irradiance is 10 percent of its value at the surface. A
    float if every input is a number, an array otherwise.

    Notes
    -----
    Fitted to Hydrolight runs with the sun 10 to 60 degrees from the zenith
    and stated good for Kd of about 0.05 to 5.7 1/m (pp. 6-7 of 10); outside
    either the result comes with a :class:`ProvenanceWarning`. Lee et al.
    (2013) found it overestimates Kd in clear water and the UV, and revised
    it: :func:`lee2013_kd`. DECISIONS.md section 66.
    """
    a, bb = _check_iops(a, bb)
    sun = _sun(sun_zenith_deg, _LEE2005_SUN, "Lee et al. (2005)")
    kd = (1 + 0.005 * sun) * a + 4.18 * (1 - 0.52 * np.exp(-10.8 * a)) * bb
    _kd_range(np.asarray(kd), _LEE2005_KD, "Lee et al. (2005)")
    return _result(kd, a, bb, sun)


@_data.positional_only()
def lee2013_kd(a, bb, /, *, bb_water, sun_zenith_deg):
    """Kd from a, bb, the backscattering of pure water, and the sun.

    Lee, Z., Hu, C., Shang, S., Du, K., Lewis, M., Arnone, R. and Brewin,
    R. (2013), "Penetration of UV-visible solar radiation in the global
    oceans: Insights from ocean color remote sensing", J. Geophys. Res.
    Oceans 118, 4241-4255, doi:10.1002/jgrc.20308. Eqs. (3) and (5) with
    Table 1::

        Kd = (1 + 0.005 theta) a
             + (1 - 0.265 bb_water / bb) 4.259 (1 - 0.52 exp(-10.8 a)) bb

    Parameters
    ----------
    a, bb:
        Absorption and total backscattering coefficients, 1/m, positive;
        numbers or arrays that broadcast together and with the rest. NaN
        marks a gap and gives NaN.
    bb_water:
        The backscattering coefficient of pure sea water, 1/m, part of
        ``bb``: not negative and not above it. No default;
        :func:`pure_water_backscattering` gives one for a stated salinity.
    sun_zenith_deg:
        theta, the sun's zenith angle above the surface, degrees, in
        [0, 90). No default.

    Returns
    -------
    Kd, 1/m, of the same layer as :func:`lee2005_kd`: from the surface to
    10 percent of the surface irradiance. A float if every input is a
    number, an array otherwise.

    Notes
    -----
    The term in bb_water lets molecular scattering, whose phase function
    differs from that of particles, count for less (p. 4242). Fitted to
    Hydrolight runs with the sun at 5, 30 and 60 degrees, 360-560 nm, and
    stated good for Kd of about 0.02 to 5.0 1/m (p. 4243); outside the
    angles or the range the result comes with a :class:`ProvenanceWarning`.
    DECISIONS.md section 66.
    """
    a, bb = _check_iops(a, bb)
    bbw = _spectral(bb_water, "bb_water")
    if np.any(bbw < 0) or np.any(bbw > bb):
        raise ValueError("bb_water must not be negative, and is part of bb, "
                         "so cannot exceed it")
    sun = _sun(sun_zenith_deg, _LEE2013_SUN, "Lee et al. (2013)")
    kd = ((1 + 0.005 * sun) * a
          + (1 - 0.265 * bbw / bb) * 4.259
          * (1 - 0.52 * np.exp(-10.8 * a)) * bb)
    _kd_range(np.asarray(kd), _LEE2013_KD, "Lee et al. (2013)")
    return _result(kd, a, bb, bbw, sun)


@_data.positional_only()
def subsurface_rrs(a, bb, /, *, coefficients):
    """The remote sensing reflectance just below the surface, from a and bb.

    rrs = g0 u + g1 u^2, u = bb / (a + bb): Gordon, H. R. et al. (1988), "A
    semianalytic radiance model of ocean color", J. Geophys. Res. 93(D9),
    10909-10924, doi:10.1029/JD093iD09p10909, eq. (2), there written as
    R/Q; and Lee, Z., Carder, K. L. and Arnone, R. A. (2002), Appl. Opt. 41,
    5755-5772, doi:10.1364/AO.41.005755, eq. (1).

    Parameters
    ----------
    a, bb:
        Absorption and backscattering coefficients, 1/m, positive; numbers
        or arrays that broadcast together. NaN marks a gap and gives NaN.
    coefficients:
        (g0, g1). No default: :data:`GORDON1988_RRS_COEFFICIENTS`, (0.0949,
        0.0794), Gordon et al.'s for case 1 water; or
        :data:`LEE2002_RRS_COEFFICIENTS`, (0.0895, 0.1247), Lee et al.'s
        mean of those and a pair for more turbid coastal water.

    Returns
    -------
    rrs, sr^-1: upwelling radiance over downwelling irradiance just below
    the surface. A float if both inputs are numbers, an array otherwise.

    Notes
    -----
    Gordon et al. give the error as significantly less than 10 percent for
    realistic phase functions, with the sun 20 degrees or more from the
    zenith; nearer the zenith it depends on the phase function (p. 10910).
    The values of g0 and g1 vary with the phase function (Lee et al. 2002,
    p. 5756). The relation is for optically deep water: no bottom, and no
    Raman scattering or fluorescence. DECISIONS.md section 66. To remove
    Raman scattering from a measured Rrs before comparing, see
    :func:`~jerlov.lee2013_raman_correction`.
    """
    a, bb = _check_iops(a, bb)
    g = _finite(coefficients, "coefficients")
    if g.shape != (2,) or np.any(g <= 0):
        raise ValueError("coefficients must be (g0, g1), two positive "
                         "numbers, such as GORDON1988_RRS_COEFFICIENTS")
    u = bb / (a + bb)
    return _result(g[0] * u + g[1] * u ** 2, a, bb)


@_data.positional_only()
def above_surface_rrs(rrs, /):
    """The remote sensing reflectance above the surface, from that below.

    Rrs = 0.52 rrs / (1 - 1.7 rrs), the inverse of Lee, Z., Carder, K. L.
    and Arnone, R. A. (2002), "Deriving inherent optical properties from
    water color: a multiband quasi-analytical algorithm for optically deep
    waters", Appl. Opt. 41, 5755-5772, doi:10.1364/AO.41.005755, eq. (8):
    rrs = Rrs / (0.52 + 1.7 Rrs).

    Parameters
    ----------
    rrs:
        The reflectance just below the surface, sr^-1, as from
        :func:`subsurface_rrs`; not negative, and below 1/1.7.

    Returns
    -------
    Rrs, sr^-1: water-leaving radiance over downwelling irradiance above
    the surface. A float for a number, an array otherwise.

    Notes
    -----
    0.52 stands for the transmission of the surface both ways over the
    square of the refractive index, and 1.7 for the reflection of upwelling
    light back down; Lee et al. found these from Hydrolight for optically
    deep water and a sensor looking straight down (p. 5757).
    DECISIONS.md section 66.
    """
    r = _spectral(rrs, "rrs")
    if np.any(r < 0) or np.any(r >= 1 / 1.7):
        raise ValueError("rrs must be at least 0 and below 1/1.7 sr^-1")
    return _result(0.52 * r / (1 - 1.7 * r), r)


@_data.positional_only()
def lee2015_secchi_depth(wavelengths, kd, rrs, /):
    """The Secchi depth from Kd and the remote sensing reflectance.

    Lee, Z., Shang, S., Hu, C., Du, K., Weidemann, A., Hou, W., Lin, J. and
    Lin, G. (2015), "Secchi disk depth: A new theory and mechanistic model
    for underwater visibility", Remote Sens. Environ. 169, 139-149,
    doi:10.1016/j.rse.2015.08.002. Eq. (33)::

        Z_SD = ln(|0.14 - Rrs_tr| / 0.013) / (2.5 Kd_tr)

    where Kd_tr is the smallest Kd of the spectrum, at the wavelength where
    the water is most transparent, and Rrs_tr the reflectance there.

    Parameters
    ----------
    wavelengths:
        nm, one spectrum within the visible, 400-700 nm; Lee et al. used
        443-665 nm.
    kd:
        Kd at those wavelengths, 1/m, positive. Lee et al. used Kd from a
        and bb for a sun 30 degrees from the zenith (p. 146), as
        :func:`lee2013_kd` gives.
    rrs:
        The remote sensing reflectance above the surface at those
        wavelengths, sr^-1, not negative, as :func:`above_surface_rrs`
        gives.

    Neither ``kd`` nor ``rrs`` may have gaps: the smallest Kd of a spectrum
    could lie in one, so NaN is refused here.

    Returns
    -------
    Z_SD, m, the depth at which a white disc disappears from the view of
    someone above the surface.

    Notes
    -----
    0.14 is a white disc of reflectance 0.85 seen through the surface
    (p. 146; the paper's own 0.85 / pi times 0.54 is 0.146, and eq. (33)
    uses 0.14), 0.013 sr^-1 the contrast the eye needs
    to see it (p. 147), and 2.5 counts the attenuation of the light on
    its way down and up (p. 145). The model was checked against 338
    measured depths from 0.1 to 30 m, to about 18 percent (pp. 146-147);
    outside that range the result comes with a :class:`ProvenanceWarning`.
    DECISIONS.md section 66.
    """
    wl = _finite(wavelengths, "wavelengths")
    k = _finite(kd, "kd")
    r = _finite(rrs, "rrs")
    if wl.ndim != 1 or wl.size == 0 or k.shape != wl.shape \
            or r.shape != wl.shape:
        raise ValueError("wavelengths, kd and rrs must be one spectrum each, "
                         "of the same length")
    if np.any(wl < 400) or np.any(wl > 700):
        raise ValueError("wavelengths must lie within the visible, 400-700 "
                         "nm, where the model looks for the most transparent "
                         "wavelength")
    if np.any(k <= 0) or np.any(r < 0):
        raise ValueError("kd must be positive and rrs not negative")
    i = int(np.argmin(k))
    contrast = abs(_DISC - r[i]) / _THRESHOLD
    if contrast <= 1:
        raise ValueError(
            f"Rrs {r[i]:g} sr^-1 at the most transparent wavelength leaves "
            "the disc no contrast above the eye's threshold, so the model "
            "gives no depth")
    depth = float(np.log(contrast) / (_PATH * k[i]))
    lo, hi = _LEE2015_DEPTHS
    if not lo <= depth <= hi:
        _warn(f"Lee et al. (2015) checked the model against Secchi depths "
              f"of {lo:g} to {hi:g} m; {depth:.3g} m is outside them.")
    return depth

"""Kd without a water type, the colour of the sea from above, and the
Secchi depth.

Published relations, each from its primary paper, with the quantities the
papers do not fix left to the caller (DECISIONS.md sections 66 and 72 to
74):

- Kd from the chlorophyll concentration of case 1 water, Morel &
  Maritorena (2001);
- the absorption by phytoplankton and the backscattering by particles
  from the same concentration, Bricaud et al. (1995) and Morel &
  Maritorena (2001);
- Kd from the absorption and backscattering coefficients and the sun, Lee,
  Du & Arnone (2005) and Lee et al. (2013);
- the remote sensing reflectance from a and bb, Gordon et al. (1988) and
  Lee, Carder & Arnone (2002), and with water and particles apart at seven
  viewing geometries, Lee et al. (2011);
- the downwelling distribution function D0 and a Kd under another light
  field, Gordon (1989);
- the Secchi depth from Kd and the remote sensing reflectance, Lee et al.
  (2015).

All are forward relations, and none reads satellite data. The inverse, from
the reflectance to a and bb, is in :mod:`jerlov.qaa`.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from functools import lru_cache
from types import MappingProxyType

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
#: (G0w, G1w, G0p, G1p) of Lee et al. (2011), Table 2 (p. 3159), sr^-1, by
#: (sun zenith, viewing zenith, relative azimuth) in degrees: the seven
#: geometries the paper prints, of the many it derived. Read-only.
LEE2011_RRS_COEFFICIENTS = MappingProxyType({
    (0.0, 0.0, 0.0): (0.0604, 0.0406, 0.0402, 0.1310),
    (0.0, 30.0, 90.0): (0.0596, 0.0516, 0.0408, 0.1420),
    (15.0, 30.0, 90.0): (0.0590, 0.0562, 0.0411, 0.1461),
    (30.0, 30.0, 90.0): (0.0584, 0.0601, 0.0418, 0.1492),
    (0.0, 40.0, 135.0): (0.0581, 0.0581, 0.0414, 0.1458),
    (15.0, 40.0, 135.0): (0.0614, 0.0524, 0.0425, 0.1408),
    (30.0, 40.0, 135.0): (0.0624, 0.0524, 0.0434, 0.1406),
})
#: bb/(a + bb) of the IOCCG Report 5 data the coefficients were fitted to
#: (p. 3159).
_LEE2011_U = (0.0002, 0.37)

#: Chlorophyll concentrations, mg m^-3, that Morel & Maritorena's pooled
#: data spanned: 0.02 to more than 30 (p. 7164).
_MOREL_CHL = (0.02, 30.0)
#: Sun zenith angles, degrees, of the HydroLight runs each Kd model was
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
    try:
        ok = (np.ndim(value) == 0 and bool(np.isfinite(value))
              and float(value) > 0)
    except TypeError:               # text, say: isfinite has no answer
        ok = False
    if not ok:
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


#: The pigment range Morel (1988) runs his model over (Figs. 10, 12 and
#: 13), mg m^-3; and the wavelength beyond which chi and e were fitted to
#: mesotrophic and eutrophic waters only (p. 10,755).
_MOREL1988_C, _MOREL1988_RED = (0.03, 30.0), 650.0


@_data.positional_only()
def morel1988_kd(wavelengths, /, *, pigment_mg_m3: float):
    """Kd of case 1 water from its pigment concentration, Morel's (1988)
    edition.

    Morel, A. (1988), "Optical modeling of the upper ocean in relation to
    its biogenous matter content (case I waters)", J. Geophys. Res.
    93(C9), 10749-10768, doi:10.1029/JC093iC09p10749. Eqs. (8) and (9)::

        K = Kw + chi C^e,    Kw = aw + bw / 2

    with Kw, chi and e from Table 2, 400-700 nm every 5 nm; K is computed
    on that grid and interpolated linearly between. :func:`morel2001_kd`
    is the revision of Morel & Maritorena (2001), which keeps this
    edition's chi and e from 560 nm on and changes Kw everywhere (DATA.md
    section 45).

    Parameters
    ----------
    wavelengths:
        nm, a number or an array, within 400-700 nm.
    pigment_mg_m3:
        C, mg m^-3: chlorophyll a plus pheophytin a, averaged over the
        layer, not the HPLC chlorophyll a of :func:`morel2001_kd`. One
        number; no default.

    Returns
    -------
    Kd, 1/m: a float for a number, an array otherwise.

    Notes
    -----
    Fitted to 176 spectra of case 1 water; the paper uses the model from
    0.03 to 30 mg m^-3 and outside that range the result comes with a
    :class:`ProvenanceWarning`. Beyond 650 nm "the chi and e values ...
    are only extracted from the mesotrophic and eutrophic waters" (p.
    10,755), and those wavelengths warn too. DECISIONS.md section 101.
    """
    c = _single(pigment_mg_m3, "pigment_mg_m3", "mg m^-3")
    query = np.atleast_1d(np.asarray(wavelengths, dtype=float))
    grid, kw, chi, e = _data.morel1988()
    if (not np.all(np.isfinite(query)) or np.any(query < grid[0])
            or np.any(query > grid[-1])):
        raise ValueError(
            f"wavelengths must lie within {grid[0]:g}-{grid[-1]:g} nm, the "
            "range of Morel's (1988) Table 2. This package does not "
            "extrapolate.")
    lo, hi = _MOREL1988_C
    if not lo <= c <= hi:
        _warn(f"C = {c:g} mg m^-3 is outside the {lo:g}-{hi:g} Morel (1988) "
              "runs his model over; the result is the relation carried "
              "beyond it.")
    if np.any(query > _MOREL1988_RED):
        _warn("beyond 650 nm Morel's (1988) chi and e were fitted to "
              "mesotrophic and eutrophic waters only (p. 10,755).")
    kd = kw + chi * c ** e
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
    Fitted to HydroLight runs with the sun 10 to 60 degrees from the zenith
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


#: Lee, Du, Arnone, Liew and Penta (2005), J. Geophys. Res. 110, C09019,
#: Table 2 (p. 7): chi0 (1/m), chi1, chi2; zeta0 (1/m), zeta1, zeta2;
#: alpha0, alpha1, alpha2.
LEE2005_KVIS_CHI = (-0.057, 0.482, 4.221)
LEE2005_KVIS_ZETA = (0.183, 0.702, -2.567)
LEE2005_KVIS_ALPHA = (0.090, 1.465, -0.667)
#: The sun of the HydroLight runs (10, 30 and 60 degrees, p. 4), the range
#: of K_VIS they spanned (0.04-1.6 1/m, p. 5), and the smallest T_VIS the
#: fit was judged on (0.001, p. 7).
_KVIS_SUN, _KVIS_RANGE, _KVIS_T_MIN = (10.0, 60.0), (0.04, 1.6), 0.001
_KVIS_PAPER = "Lee et al. (2005, C09019)"


def _kvis_k1_k2(a490, bb490, sun):
    """K1 and K2 of Lee et al.'s (2005, C09019) Eq. (9), refusing values
    that would let K_VIS fall to zero or below."""
    chi0, chi1, chi2 = LEE2005_KVIS_CHI
    zeta0, zeta1, zeta2 = LEE2005_KVIS_ZETA
    alpha0, alpha1, alpha2 = LEE2005_KVIS_ALPHA
    theta = np.radians(sun)
    k1 = (chi0 + chi1 * np.sqrt(a490) + chi2 * bb490) * (
        1 + alpha0 * np.sin(theta))
    k2 = (zeta0 + zeta1 * a490 + zeta2 * bb490) * (
        alpha1 + alpha2 * np.cos(theta))
    with np.errstate(invalid="ignore"):
        if np.any(k1 <= 0) or np.any(k2 < 0):
            raise ValueError(
                "the model's K1 must be positive and K2 not negative; for "
                "these a(490) and bb(490) they are not (K1's constant "
                "term is negative, so very small a(490) gives K1 <= 0, and "
                "bb(490) large against a(490) gives K2 < 0), and K_VIS "
                "could then fall to zero or below; it is refused, not "
                "clipped. DECISIONS.md section 98.")
    return k1, k2


def _kvis_check(kvis, depth):
    lo, hi = _KVIS_RANGE
    known = kvis[~np.isnan(kvis)]
    if known.size and (np.min(known) < lo or np.max(known) > hi):
        _warn(f"{_KVIS_PAPER}'s HydroLight runs spanned K_VIS of {lo:g} "
              f"to {hi:g} 1/m; some of these values lie outside that.")
    with np.errstate(invalid="ignore"):
        t = np.exp(-kvis * depth)
    if np.any(t[~np.isnan(t)] < _KVIS_T_MIN):
        _warn(f"{_KVIS_PAPER} judged the fit for T_VIS of {_KVIS_T_MIN:g} "
              "and above; at some of these depths less than that is left.")


@_data.positional_only()
def lee2005_kvis(a490, bb490, depth_m, /, *, sun_zenith_deg):
    """The attenuation of visible solar energy, from the surface to a depth.

    Lee, Z., Du, K., Arnone, R., Liew, S. and Penta, B. (2005),
    "Penetration of solar radiation in the upper ocean: A numerical model
    for oceanic and coastal waters", J. Geophys. Res. 110, C09019,
    doi:10.1029/2004JC002780 (not the C02016 of :func:`lee2005_kd`). Eqs.
    (7) and (9), Table 2::

        K_VIS(z) = K1 + K2 / (1 + z)^0.5
        K1 = [chi0 + chi1 a(490)^0.5 + chi2 bb(490)] (1 + alpha0 sin theta)
        K2 = [zeta0 + zeta1 a(490) + zeta2 bb(490)] (alpha1 + alpha2 cos theta)

    with the constants ``jerlov.ocean_colour.LEE2005_KVIS_CHI``,
    ``LEE2005_KVIS_ZETA`` and ``LEE2005_KVIS_ALPHA``. E_VIS(z) = E_VIS(0)
    exp(-K_VIS(z) z).

    Parameters
    ----------
    a490, bb490:
        The total absorption and backscattering coefficients at 490 nm,
        1/m, positive; numbers or arrays that broadcast together and with
        the rest. NaN marks a gap and gives NaN.
    depth_m:
        z, metres below the surface, not negative.
    sun_zenith_deg:
        theta, the sun's zenith angle above the surface, degrees, in
        [0, 90). No default.

    Returns
    -------
    K_VIS(z), 1/m: the mean attenuation from just below the surface to z
    of the downwelling irradiance Ed, in energy, summed over 350-700 nm
    (Lee et al. 2007 call it the "downwelling vector irradiance"). A
    float if every input is a number, an array otherwise.

    Raises
    ------
    ValueError
        For input that is not a number, infinite or out of range, and where
        K1 would not be positive or K2 would be negative.

    Notes
    -----
    Fitted to 300 HydroLight runs (pp. 4-5): Pope & Fry's pure water,
    Petzold's average-particle phase function, Gregg & Carder's clear sky,
    wind 5 m/s, the sun at 10, 30 and 60 degrees, K_VIS 0.04 to 1.6 1/m;
    the average error of T_VIS was 9 percent above 0.003 (p. 7). Outside
    the sun, the K_VIS or a T_VIS of 0.001 the result comes with a
    :class:`ProvenanceWarning`. This is energy over 350-700 nm; PAR is
    quanta over 400-700 nm. Lee et al. (2007, p. 4) found "the difference
    between zx% measured by either EVIS or PAR is small (less than 10%)".
    DECISIONS.md section 98.
    """
    a, bb = _check_iops(a490, bb490)
    depth = _finite(depth_m, "depth_m")
    if np.any(depth < 0):
        raise ValueError("depth_m must not be negative")
    sun = _sun(sun_zenith_deg, _KVIS_SUN, _KVIS_PAPER)
    k1, k2 = _kvis_k1_k2(a, bb, sun)
    kvis = k1 + k2 / np.sqrt(1 + depth)
    _kvis_check(np.asarray(kvis, dtype=float), depth)
    return _result(kvis, a, bb, depth, sun)


def _smaller_root(k1: float, k2: float, tau: float) -> float:
    """The depth of Lee et al.'s (2007) Eq. (8), the cubic got by squaring
    K1 z + K2 z / (1 + z)^0.5 = tau: its smaller positive root that is a
    root of the unsquared equation too."""
    if np.isnan(k1) or np.isnan(k2) or np.isnan(tau):
        return float("nan")
    y1 = (k1 * k1 - k2 * k2 - 2 * tau * k1) / (k1 * k1)
    y2 = (tau * tau - 2 * tau * k1) / (k1 * k1)
    y3 = tau * tau / (k1 * k1)
    roots = np.roots([1.0, y1, y2, y3])
    found = []
    for root in roots:
        if abs(root.imag) > 1e-9 * max(1.0, abs(root.real)):
            continue
        z = float(root.real)
        if z <= 0:
            continue
        # Squaring admits roots of K1 z - K2 z / (1 + z)^0.5 = tau too.
        if abs(k1 * z + k2 * z / np.sqrt(1 + z) - tau) <= 1e-8 * tau:
            found.append(z)
    if not found:                   # pragma: no cover - not seen
        raise ValueError("no positive depth solves Lee et al.'s (2007) "
                         f"Eq. (8) for K1={k1}, K2={k2}, tau={tau}")
    return min(found)


@_data.positional_only()
def lee2007_depth_of_fraction(a490, bb490, /, *, sun_zenith_deg, fraction):
    """The depth where visible solar energy falls to a fraction of its
    surface value; at 0.01, the euphotic depth.

    Lee, Z., Weidemann, A., Kindle, J., Arnone, R., Carder, K. L. and
    Davis, C. (2007), "Euphotic zone depth: Its derivation and implication
    to ocean-color remote sensing", J. Geophys. Res. 112, C03009,
    doi:10.1029/2006JC003802. Eqs. (5)-(9): with tau = -ln(fraction), z
    solves K_VIS(z) z = tau, K_VIS of :func:`lee2005_kvis`; squared, the
    cubic z^3 + y1 z^2 + y2 z + y3 = 0 with::

        y1 = (K1^2 - K2^2 - 2 tau K1) / K1^2
        y2 = (tau^2 - 2 tau K1) / K1^2
        y3 = tau^2 / K1^2

    of whose roots the smaller positive one is the depth (p. 3). Here each
    root is also put back into the unsquared equation, and only one that
    satisfies it is returned.

    Parameters
    ----------
    a490, bb490:
        As for :func:`lee2005_kvis`.
    sun_zenith_deg:
        As for :func:`lee2005_kvis`. No default.
    fraction:
        E_VIS(z) / E_VIS(0), in (0, 1): 0.01 for the euphotic depth, 0.1
        and 0.5 as the paper also uses. No default.

    Returns
    -------
    z, metres. A float if every input is a number, an array otherwise.

    Notes
    -----
    The paper takes this depth for that of PAR, 400-700 nm in quanta: "the
    difference between zx% measured by either EVIS or PAR is small (less
    than 10%)" (p. 4).
    The warnings of :func:`lee2005_kvis` apply at the depth found.
    DECISIONS.md section 98.
    """
    a, bb = _check_iops(a490, bb490)
    f = _finite(fraction, "fraction")
    if np.any(f <= 0) or np.any(f >= 1):
        raise ValueError("fraction must lie in (0, 1)")
    sun = _sun(sun_zenith_deg, _KVIS_SUN, _KVIS_PAPER)
    k1, k2 = _kvis_k1_k2(a, bb, sun)
    tau = -np.log(f)
    k1b, k2b, taub = np.broadcast_arrays(np.asarray(k1, dtype=float),
                                         np.asarray(k2, dtype=float), tau)
    depth = np.vectorize(_smaller_root, otypes=[float])(k1b, k2b, taub)
    _kvis_check(np.asarray(k1b + k2b / np.sqrt(1 + depth), dtype=float),
                depth)
    return _result(depth, a, bb, sun, f)


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
    HydroLight runs with the sun at 5, 30 and 60 degrees, 360-560 nm, and
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
def lee2011_rrs(a, bb, /, *, bb_water, coefficients):
    """The remote sensing reflectance above the surface, water and
    particles apart, Lee et al. (2011).

    Lee, Z. P., Du, K., Voss, K. J., Zibordi, G., Lubac, B., Arnone, R. and
    Weidemann, A. (2011), "An inherent-optical-property-centered approach to
    correct the angular effects in water-leaving radiance", Appl. Opt.
    50(19), 3155-3167, doi:10.1364/AO.50.003155, eq. (14)::

        Rrs = (G0w + G1w bbw/k) bbw/k + (G0p + G1p bbp/k) bbp/k,
        k = a + bb,  bbp = bb - bbw

    Parameters
    ----------
    a, bb:
        Absorption and backscattering coefficients, 1/m, positive; numbers
        or arrays of one shape. NaN marks a gap and gives NaN.
    bb_water:
        Pure water's part of bb, 1/m: not negative and not above bb.
    coefficients:
        (G0w, G1w, G0p, G1p), sr^-1, four positive numbers; no default.
        :data:`LEE2011_RRS_COEFFICIENTS` holds the seven sets Table 2
        prints, by (sun zenith, viewing zenith, relative azimuth); its
        (0, 0, 0) is straight down with the sun overhead.

    Returns
    -------
    Rrs above the surface, sr^-1: the coefficients include the crossing of
    the surface, so :func:`above_surface_rrs` is not applied to it.

    Notes
    -----
    The coefficients were fitted to HydroLight runs on the IOP sets of
    IOCCG Report 5, with bb/(a + bb) from 0.0002 to 0.37 (p. 3159);
    outside that range the result comes with a :class:`ProvenanceWarning`.
    The particle phase function was a blend of Petzold's average and a
    Fournier-Forand of backscattering ratio 1 percent. The paper derived
    coefficients for many more geometries but prints only these seven; it
    describes no interpolation between them, and none is done here.
    Optically deep water; no Raman scattering. DECISIONS.md section 73.
    """
    a, bb = _check_iops(a, bb)
    bbw = _spectral(bb_water, "bb_water")
    if np.any(bbw < 0) or np.any(bbw > bb):
        raise ValueError("bb_water must not be negative, and is part of bb, "
                         "so cannot exceed it")
    g = _finite(coefficients, "coefficients")
    if g.shape != (4,) or np.any(g <= 0):
        raise ValueError("coefficients must be (G0w, G1w, G0p, G1p), four "
                         "positive numbers, such as a value of "
                         "LEE2011_RRS_COEFFICIENTS")
    k = a + bb
    u = bb / k
    lo, hi = _LEE2011_U
    known = u[~np.isnan(u)] if np.ndim(u) else u
    if np.any(known < lo) or np.any(known > hi):
        _warn(f"bb/(a + bb) outside {lo:g}-{hi:g}, the range of the data "
              "Lee et al. (2011) fitted their coefficients to (p. 3159)")
    xw = bbw / k
    xp = (bb - bbw) / k
    rrs = (g[0] + g[1] * xw) * xw + (g[2] + g[3] * xp) * xp
    return _result(rrs, a, bb, bbw)


#: The refractive index of sea water used for Gordon's (1989) D0: it
#: reproduces six of the seven rows of his Table 3's 1/cos column, the most
#: any index does (DECISIONS.md section 74); his text says "about 1.33".
_GORDON1989_N = 1.333
#: D0 of a sky of uniform radiance just beneath a flat surface (eq. 12).
_GORDON1989_DIFFUSE_D0 = 1.197


@_data.positional_only()
def gordon1989_d0(sun_zenith_deg, /, *, direct_fraction):
    """D0, the downwelling distribution function just beneath the surface.

    Gordon, H. R. (1989), "Can the Lambert-Beer law be applied to the
    diffuse attenuation coefficient of ocean water?", Limnol. Oceanogr.
    34(8), 1389-1409, doi:10.4319/lo.1989.34.8.1389, eq. (12)::

        D0 = f / cos(theta_w) + 1.197 (1 - f)

    for a sky of uniform radiance. D0 is the reciprocal of the mean cosine
    of the downwelling light: 1 for the sun overhead, more as it slants.

    Parameters
    ----------
    sun_zenith_deg:
        The sun's zenith angle in air, degrees, 0 up to but not including
        90; a number or an array. It is refracted into the water by
        Snell's law with n = 1.333, which reproduces six of the seven rows
        of the paper's Table 3 secant column, the most any index does (its
        text says "about 1.33"; DECISIONS.md section 74).
    direct_fraction:
        f, the share of the irradiance transmitted through the surface
        that is direct sunlight, 0-1. No default: it depends on the sky,
        and the paper estimates it by shading the sun from an irradiance
        meter (p. 1401). A number, or an array of the sun's shape.

    Returns
    -------
    D0: a float for numbers, an array otherwise.

    Notes
    -----
    Against D0 computed exactly with a model atmosphere (Table 3), eq. (12)
    is within about 3 percent for the sun up to 60 degrees and 5-8 percent
    too low at 80 (p. 1402); above 60 degrees the result comes with a
    :class:`ProvenanceWarning`. A flat surface; the paper's correction for
    waves is given only as a figure. See :func:`gordon1989_kd` for its use.
    """
    sun = _finite(sun_zenith_deg, "sun_zenith_deg")
    f = _finite(direct_fraction, "direct_fraction")
    if np.any(sun < 0) or np.any(sun >= 90):
        raise ValueError("sun_zenith_deg must be from 0 up to, not "
                         "including, 90 degrees")
    if np.any(f < 0) or np.any(f > 1):
        raise ValueError("direct_fraction must lie within 0-1")
    if np.any(sun > 60):
        _warn("Gordon's (1989) eq. (12) is within about 3 percent of the "
              "exact D0 up to a sun 60 degrees from the zenith; at 80 it is "
              "5-8 percent too low (p. 1402)")
    cos_w = np.sqrt(1 - (np.sin(np.radians(sun)) / _GORDON1989_N) ** 2)
    d0 = f / cos_w + _GORDON1989_DIFFUSE_D0 * (1 - f)
    return _result(d0, sun_zenith_deg, direct_fraction)


@_data.positional_only()
def gordon1989_kd(kd, /, *, d0_from, d0_to):
    """Kd under one light field rescaled to another: kd * d0_to / d0_from.

    Gordon (1989) found Kd/D0 nearly independent of the light field for a
    given water: computed for many sun angles and wavelengths, K/(c D0)
    fell on single curves with an average error of 1.8 percent, and the
    mean over the upper half of the euphotic zone with 2.2 (p. 1399). So a
    Kd measured when D0 was ``d0_from`` becomes, under ``d0_to``, about
    ``kd * d0_to / d0_from``.

    Parameters
    ----------
    kd:
        Kd, 1/m, not negative; a number or an array. The paper's K is Kd
        just beneath the surface, and <K> its mean over the upper half of
        the euphotic zone (p. 1398); the rescaling is for those, not for
        Kd at depth, where the light field has changed.
    d0_from, d0_to:
        D0 when ``kd`` was measured, and D0 wanted, both positive; numbers
        or arrays broadcasting with ``kd``. Both are required. **Jerlov's
        Kd tables do not record the sun angle or the sky they were
        measured under, so this package cannot supply d0_from for them**;
        a caller who rescales them states an assumption.
        :func:`gordon1989_d0` gives D0 from the sun and the sky.

    Returns
    -------
    Kd, 1/m: a float for numbers, an array otherwise. DECISIONS.md section
    74.
    """
    k = _finite(kd, "kd")
    d_from = _finite(d0_from, "d0_from")
    d_to = _finite(d0_to, "d0_to")
    if np.any(k < 0):
        raise ValueError("kd must not be negative")
    if np.any(d_from <= 0) or np.any(d_to <= 0):
        raise ValueError("d0_from and d0_to must be positive")
    return _result(k * d_to / d_from, kd, d0_from, d0_to)


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
    light back down; Lee et al. found these from HydroLight for optically
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


# -- the sea surface's reflectance factor rho, and Rrs above the water ------

#: The tables of Mobley's rho as shipped (DATA.md section 43).
MOBLEY_RHO_SOURCES = ("mobley1999", "mobley2015")
_RHO_FILES = {"mobley1999": "mobley1999_rho.csv",
              "mobley2015": "mobley2015_rho.csv"}
_RHO_NADIR = (0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 87.5)
_RHO_AZIMUTH = tuple(15.0 * k for k in range(13))


@lru_cache(maxsize=None)
def _rho_table(source: str):
    """(winds, suns, values[wind, sun, nadir, azimuth]) of one table; the
    nadir cap's one value is repeated over the azimuths."""
    rows = _data._rows(_RHO_FILES[source])
    winds = sorted({float(r["wind_speed"]) for r in rows})
    suns = sorted({float(r["sun_zenith_deg"]) for r in rows})
    values = np.full((len(winds), len(suns), len(_RHO_NADIR),
                      len(_RHO_AZIMUTH)), np.nan)
    for r in rows:
        i = winds.index(float(r["wind_speed"]))
        j = suns.index(float(r["sun_zenith_deg"]))
        k = _RHO_NADIR.index(float(r["view_nadir_deg"]))
        rho = float(r["rho"])
        if k == 0:
            values[i, j, 0, :] = rho
        else:
            values[i, j, k, _RHO_AZIMUTH.index(
                float(r["view_azimuth_deg"]))] = rho
    if np.isnan(values).any():      # pragma: no cover - the build checks
        raise RuntimeError(f"{source}_rho.csv does not fill its grid")
    return np.array(winds), np.array(suns), values


def _bracket(x: np.ndarray, grid: np.ndarray):
    """Lower index and weight of linear interpolation; x within grid."""
    i = np.clip(np.searchsorted(grid, x, side="right") - 1, 0,
                len(grid) - 2)
    w = (x - grid[i]) / (grid[i + 1] - grid[i])
    return i, w


def mobley_rho(*, source, wind_speed, sun_zenith_deg, view_nadir_deg,
               view_azimuth_deg):
    """The sea surface's reflectance factor rho for an above-water
    radiometer, from Mobley's tables.

    rho = Lr / Ls: the sky radiance the sea surface reflects into the
    radiometer, over the sky radiance measured in the mirror direction
    (Mobley 1999, Eq. 4). It is "not an IOP of the sea surface": it
    depends on the sun, the viewing direction, the wind, the sky and the
    wavelength. Rrs = (Lt - rho Ls) / Ed (:func:`rrs_from_above_water`).

    Parameters
    ----------
    source:
        No default. ``"mobley1999"``: Mobley, C. D. (1999), "Estimation of
        the remote-sensing reflectance from above-surface measurements",
        Appl. Opt. 38, 7442-7455, doi:10.1364/AO.38.007442; Cox-Munk
        surfaces, unpolarised ray tracing, the clear sky of Harrison &
        Coombes; wind 0-14 m/s, sun 0-80 degrees. ``"mobley2015"``:
        Mobley, C. D. (2015), "Polarized reflectance and transmittance
        properties of windblown sea surfaces", Appl. Opt. 54, 4828-4849,
        doi:10.1364/AO.54.004828; surfaces from wave spectra, polarised
        ray tracing, a single-scattering Rayleigh sky, a fully developed
        sea with the sun's rays along the wind; wind 0-15 m/s, sun 0-87.5
        degrees. Both are for 550 nm, as the Ocean Optics Web Book
        distributes them; neither paper prints its table.
    wind_speed:
        m/s, within the table's range; linear between its points.
    sun_zenith_deg:
        Degrees, within the table's range; linear between its points.
    view_nadir_deg:
        The radiometer's angle from the nadir, one of 0, 10, ..., 80 and
        87.5: each value is the mean over a 10-degree band of nadir angle
        (a polar cap at 0), the field of view of a typical radiometer, so
        no value between two is given.
    view_azimuth_deg:
        The radiometer's azimuth from the sun's, one of 0, 15, ..., 180
        (a 15-degree band each); not used at nadir 0. Mobley (1999)
        recommends 40 degrees from the nadir and 135 from the sun.

    All four take numbers or arrays that broadcast together. Returns a
    float if every input is a number, an array otherwise.

    Raises
    ------
    ValueError
        For an unknown or missing source, a wind or sun outside the table,
        or a viewing direction that is not one of its own.

    Notes
    -----
    The 2015 table's own header calls it "a preliminary table for use
    during review"; the Web Book offers it as the paper's revised table.
    It gives a :class:`ProvenanceWarning`. The two tables differ by up to
    a factor of two at the same conditions; Mobley (2015) found the 1999
    method "not adequate for accurate estimation of water-leaving
    radiance". The value for a real sky, with clouds or aerosol, is
    neither (Mobley 1999, section 5). DECISIONS.md section 99, DATA.md
    section 43.
    """
    if source not in MOBLEY_RHO_SOURCES:
        raise ValueError(f"source must be one of {MOBLEY_RHO_SOURCES}, "
                         f"not {source!r}; there is no default")
    winds, suns, values = _rho_table(source)
    wind = _finite(wind_speed, "wind_speed")
    sun = _finite(sun_zenith_deg, "sun_zenith_deg")
    nadir = _finite(view_nadir_deg, "view_nadir_deg")
    azimuth = _finite(view_azimuth_deg, "view_azimuth_deg")
    for name, x, grid, unit in (("wind_speed", wind, winds, "m/s"),
                                ("sun_zenith_deg", sun, suns, "degrees")):
        if np.any(x < grid[0]) or np.any(x > grid[-1]):
            raise ValueError(f"{name} must lie within {source}'s table, "
                             f"{grid[0]:g} to {grid[-1]:g} {unit}")
    on_nadir = np.isin(nadir, _RHO_NADIR)
    if not np.all(on_nadir):
        raise ValueError("view_nadir_deg must be one of the table's own, "
                         f"{', '.join(f'{v:g}' for v in _RHO_NADIR)}: each "
                         "value is a mean over its band of directions, and "
                         "none is given between two")
    at_nadir = nadir == 0
    on_azimuth = np.isin(azimuth, _RHO_AZIMUTH) | at_nadir
    if not np.all(on_azimuth):
        raise ValueError("view_azimuth_deg must be one of 0, 15, ..., 180 "
                         "degrees from the sun (not used at nadir 0)")
    if source == "mobley2015":
        _warn("Mobley's 2015 table calls itself 'a preliminary table for "
              "use during review'; it is the one the Ocean Optics Web Book "
              "distributes as the paper's revised table. DATA.md section "
              "43.")
    wind, sun, nadir, azimuth = np.broadcast_arrays(wind, sun, nadir,
                                                    azimuth)
    k = np.searchsorted(_RHO_NADIR, nadir)
    m = np.where(nadir == 0, 0,
                 np.searchsorted(_RHO_AZIMUTH, np.where(nadir == 0, 0.0,
                                                        azimuth)))
    i, wi = _bracket(wind, winds)
    j, wj = _bracket(sun, suns)
    rho = ((1 - wi) * (1 - wj) * values[i, j, k, m]
           + wi * (1 - wj) * values[i + 1, j, k, m]
           + (1 - wi) * wj * values[i, j + 1, k, m]
           + wi * wj * values[i + 1, j + 1, k, m])
    return _result(rho, wind_speed, sun_zenith_deg, view_nadir_deg,
                   view_azimuth_deg)


@_data.positional_only()
def rrs_from_above_water(lt, lsky, ed, /, *, rho):
    """The remote sensing reflectance from above-water radiances.

    Mobley, C. D. (1999), Appl. Opt. 38, 7442-7455, Eqs. (1), (2) and
    (4)::

        Rrs = (Lt - rho Lsky) / Ed

    Lt is the radiance seen looking at the sea, Lsky the sky radiance in
    the mirror direction, Ed the downwelling irradiance above the surface.
    With a grey plaque of reflectance Rg read as Lg, Ed = pi Lg / Rg (Eq.
    6). Mobley's Eq. (7), taking off Rrs(750 nm), is not applied.

    Parameters
    ----------
    lt, lsky, ed:
        In consistent units (or raw counts of one instrument, which divide
        out); numbers or arrays that broadcast. Ed must be positive. NaN
        marks a gap and gives NaN.
    rho:
        The reflectance factor, no default: :func:`mobley_rho`, or a value
        you choose. Not negative.

    Returns
    -------
    Rrs, 1/sr. A float if every input is a number, an array otherwise.
    A negative value is kept: it says rho Lsky was more than Lt, so rho
    was too large or Lsky not from the mirror direction.
    """
    lt = _spectral(lt, "lt")
    lsky = _spectral(lsky, "lsky")
    ed = _spectral(ed, "ed")
    r = _spectral(rho, "rho")
    if np.any(ed <= 0):
        raise ValueError("ed must be positive; NaN marks a gap")
    if np.any(r < 0):
        raise ValueError("rho must not be negative")
    return _result((lt - r * lsky) / ed, lt, lsky, ed, r)


# -- f and Q for a nadir view, Morel et al. (2002), Appendix B --------------

_FQ_WAVELENGTHS = (412.5, 442.5, 490.0, 510.0, 560.0, 620.0, 660.0)
_FQ_CHL = (0.03, 0.1, 0.3, 1.0, 3.0, 10.0)
#: Eqs. (B1) and (B2) hold to 60 degrees, Eq. (B4) to 75 (pp. 6304-6305).
_FQ_SUN_FQ, _FQ_SUN_RATIO = 60.0, 75.0


@lru_cache(maxsize=None)
def _fq_table():
    out: dict = {}
    for r in _data._rows("morel2002_nadir_fq.csv"):
        out[(r["quantity"], float(r["chl_mg_m3"]),
             float(r["wavelength_nm"]))] = float(r["value"])
    return out


@dataclass(frozen=True)
class NadirFQ:
    """Morel et al.'s (2002) f and Q for the radiance from the nadir.

    ``f`` relates the irradiance reflectance below the surface to the
    IOPs, Eu/Ed = f bb/a (their Eq. 11); ``q`` is Qn = Eu/Lu for the
    upward radiance from the nadir (Eq. 10); both from Eqs. (B1) and
    (B2), NaN with the sun beyond 60 degrees. ``f_over_q`` is Eq. (B4),
    fitted to 75 degrees. ``correction`` is (f0/Q0) / (f/Qn), the factor
    of Eq. (B3) that takes a normalised water-leaving radiance measured
    with the sun at ``sun_zenith_deg`` to the sun at the zenith, from Eq.
    (B4).
    """

    wavelength_nm: float
    chlorophyll_mg_m3: float
    sun_zenith_deg: float
    f: float
    q: float
    f_over_q: float
    correction: float


def morel2002_nadir_fq(wavelength_nm, /, *, chlorophyll_mg_m3,
                       sun_zenith_deg):
    """f, Q and their ratio for an upward radiance from the nadir.

    Morel, A., Antoine, D. and Gentili, B. (2002), "Bidirectional
    reflectance of oceanic waters: accounting for Raman emission and
    varying particle scattering phase function", Appl. Opt. 41(30),
    6289-6306, doi:10.1364/AO.41.006289, Appendix B, Tables 1-3, Raman
    emission included, case 1 water::

        f(theta_s)   = f0 + Sf (1 - cos theta_s)            (B1)
        Qn(theta_s)  = Q0 + SQ (1 - cos theta_s)            (B2)
        f/Qn         = f0/Q0 + Sf/Q (1 - cos theta_s)       (B4)

    Only the nadir view is tabulated in the paper; the full tables, for
    other views, are on a server this package could not reach (DATA.md
    section 47).

    Parameters
    ----------
    wavelength_nm:
        One of 412.5, 442.5, 490, 510, 560, 620 and 660, the paper's
        own. No value between them is given: each was fitted on its own.
    chlorophyll_mg_m3:
        One of 0.03, 0.1, 0.3, 1, 3 and 10, the paper's own. No default.
    sun_zenith_deg:
        The sun's zenith angle above the surface, 0 to 75 degrees. No
        default. Eqs. (B1) and (B2) hold to 60 degrees ("may reach 2%" off
        at 60 for B1), and beyond it ``f`` and ``q`` are NaN; Eq. (B4)
        holds to 75 with errors that "might reach +-3.4%". From 60
        degrees on a :class:`ProvenanceWarning` is given.

    Returns
    -------
    :class:`NadirFQ`.

    Raises
    ------
    ValueError
        For a wavelength or chlorophyll that is not one of the table's, or
        a sun outside 0 to 75 degrees.

    Notes
    -----
    DECISIONS.md section 103, DATA.md section 47.
    """
    try:
        wl = float(wavelength_nm)
        chl = float(chlorophyll_mg_m3)
        sun = float(sun_zenith_deg)
    except (TypeError, ValueError):
        raise ValueError("wavelength_nm, chlorophyll_mg_m3 and "
                         "sun_zenith_deg must each be one number") from None
    if wl not in _FQ_WAVELENGTHS:
        raise ValueError(
            f"wavelength_nm must be one of {_FQ_WAVELENGTHS}, the "
            "wavelengths of Morel et al.'s (2002) Tables 1-3; each was "
            "fitted on its own and none is given between them")
    if chl not in _FQ_CHL:
        raise ValueError(
            f"chlorophyll_mg_m3 must be one of {_FQ_CHL}, those of Morel "
            "et al.'s (2002) Tables 1-3; none is given between them")
    if not 0.0 <= sun <= _FQ_SUN_RATIO:
        raise ValueError("sun_zenith_deg must lie in 0 to 75 degrees, the "
                         "range of Morel et al.'s (2002) Eq. (B4)")
    if sun >= _FQ_SUN_FQ:
        _warn("Morel et al.'s (2002) Eqs. (B1) and (B2) hold to 60 degrees "
              "(B1 'may reach 2%' off there), and Eq. (B4) to 75 with "
              "errors that 'might reach +-3.4%'; f and Q are NaN beyond "
              "60.")
    t = _fq_table()
    x = 1.0 - np.cos(np.radians(sun))
    ratio = t[("f0_over_Q0", chl, wl)] + t[("S_f_over_Q", chl, wl)] * x
    if sun <= _FQ_SUN_FQ:
        f = t[("f0", chl, wl)] + t[("Sf", chl, wl)] * x
        q = t[("Q0", chl, wl)] + t[("SQ", chl, wl)] * x
    else:
        f = q = float("nan")
    return NadirFQ(wavelength_nm=wl, chlorophyll_mg_m3=chl,
                   sun_zenith_deg=sun, f=float(f), q=float(q),
                   f_over_q=float(ratio),
                   correction=float(t[("f0_over_Q0", chl, wl)] / ratio))

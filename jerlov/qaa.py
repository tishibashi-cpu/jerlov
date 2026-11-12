"""The quasi-analytical algorithm: from the remote sensing reflectance to
the absorption and backscattering coefficients.

The inverse of the forward relations in :mod:`jerlov.ocean_colour`, in two
versions, each from the document its author published (DECISIONS.md
section 67):

- :func:`qaa_ioccg2006`, as IOCCG Report 5 (2006), chapter 10, describes
  and tested it;
- :func:`qaa_v6`, QAA_v6, as its author's spreadsheet computes it.

Both take Rrs at the bands of a sensor and return a, bbp, and the split of
a into phytoplankton and the rest. Neither reads satellite data.

Both invert the reflectance of elastic scattering alone;
:func:`lee2013_raman_correction` removes Raman scattering from a measured
Rrs first (DECISIONS.md section 71).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import _data

IOCCG2006 = (
    "IOCCG (2006), Remote Sensing of Inherent Optical Properties: "
    "Fundamentals, Tests of Algorithms, and Applications, Lee, Z.-P. (ed.), "
    "Reports of the International Ocean-Colour Coordinating Group No. 5, "
    "IOCCG, Dartmouth, Canada, chapter 10"
)
QAA_V6 = (
    "Lee, Z. P., 'Steps and calculations of the Quasi-Analytical Algorithm "
    "(QAA_v6)', IOCCG, qaa_v6_202011.pdf, with its spreadsheet "
    "QAA_v6-202011.xlsm"
)

_V6_BANDS = ("412", "443", "490", "55x", "670")
_R5_BANDS = ("410", "440", "490", "510", "555", "670")

#: QAA_v6 as its spreadsheet has them (DECISIONS.md section 67).
_V6_G = (0.08945, 0.1247)
_V6_H = (-1.145902927834082, -1.365828264291757, -0.4692660279445807)


@dataclass(frozen=True)
class QAAResult:
    """What the quasi-analytical algorithm derives from one or more
    spectra of Rrs.

    ``a``, ``bbp``, ``adg`` and ``aph`` are in 1/m, at ``wavelengths``
    along the last axis, with the other axes those of the Rrs given.
    """

    #: nm, the wavelengths of the Rrs given.
    wavelengths: np.ndarray
    #: Total absorption coefficient.
    a: np.ndarray
    #: Backscattering coefficient of particles, bb minus pure water's.
    bbp: np.ndarray
    #: Absorption by dissolved and detrital matter.
    adg: np.ndarray
    #: Absorption by phytoplankton: a - adg - aw.
    aph: np.ndarray
    #: The exponent of the power law of bbp with wavelength (Y in Report
    #: 5, eta in QAA_v6), one per spectrum.
    eta: np.ndarray
    #: The reference wavelength each spectrum used, nm. For
    #: :func:`qaa_ioccg2006`, NaN where its 555 and 640 nm solutions were
    #: blended (eq. 10.11).
    reference_nm: np.ndarray
    #: ``"ioccg2006"`` or ``"v6"``.
    version: str


def _inputs(wavelengths, rrs, bands, pure_water, roles, extra_nm=()):
    wl = np.asarray(wavelengths, dtype=float)
    if (wl.ndim != 1 or wl.size == 0 or not np.all(np.isfinite(wl))
            or np.any(np.diff(wl) <= 0)):
        raise ValueError("wavelengths must be one ascending list of finite "
                         "numbers, nm")
    r = np.asarray(rrs, dtype=float)
    if r.ndim == 0 or r.shape[-1] != wl.size:
        raise ValueError("rrs must have one value for each wavelength along "
                         "its last axis")
    if np.any(np.isinf(r)) or np.any(r < 0):
        raise ValueError("rrs must not be negative or infinite; NaN marks a "
                         "gap and gives NaN")
    if not isinstance(bands, dict) or set(bands) != set(roles):
        raise ValueError(f"bands must name the wavelength of each of "
                         f"{', '.join(repr(k) for k in roles)}, and nothing "
                         "else")
    index = {}
    for role in roles:
        hit = np.flatnonzero(wl == float(bands[role]))
        if hit.size != 1:
            raise ValueError(f"band {role!r} = {bands[role]!r} nm is not one "
                             "of wavelengths")
        index[role] = int(hit[0])
    try:
        pw_wl, aw, bbw = (np.asarray(x, dtype=float) for x in pure_water)
    except (TypeError, ValueError):
        raise ValueError("pure_water must be (wavelengths, aw, bbw), three "
                         "arrays") from None
    if (pw_wl.ndim != 1 or aw.shape != pw_wl.shape
            or bbw.shape != pw_wl.shape or pw_wl.size < 2
            or np.any(np.diff(pw_wl) <= 0)
            or not (np.all(np.isfinite(aw)) and np.all(np.isfinite(bbw)))):
        raise ValueError("pure_water must be (wavelengths, aw, bbw): three "
                         "arrays of the same length, ascending, finite")
    needed = np.concatenate((wl, np.asarray(extra_nm, dtype=float)))
    if np.min(needed) < pw_wl[0] or np.max(needed) > pw_wl[-1]:
        raise ValueError(
            f"pure_water covers {pw_wl[0]:g}-{pw_wl[-1]:g} nm; it must cover "
            f"{np.min(needed):g}-{np.max(needed):g} nm. This package does not "
            "extrapolate.")

    def water(nm):
        return np.interp(nm, pw_wl, aw), np.interp(nm, pw_wl, bbw)

    return wl, r, index, water


def _below(rrs):
    """rrs below the surface, Lee et al. (2002) eq. (8), step 1 of both."""
    return rrs / (0.52 + 1.7 * rrs)


def _u(rrs_below, g0, g1):
    """bb / (a + bb) from rrs, the root of rrs = g0 u + g1 u^2."""
    return (-g0 + np.sqrt(g0 ** 2 + 4 * g1 * rrs_below)) / (2 * g1)


def _decompose(wl, a, aw, i_short, i_long, zeta, xi, slope):
    """adg and aph from a at two short wavelengths (step 9, eq. 10.14)."""
    nm_long = wl[i_long]
    adg_long = ((a[..., i_short] - zeta * a[..., i_long])
                - (aw[i_short] - zeta * aw[i_long])) / (xi - zeta)
    adg = adg_long[..., None] * np.exp(-slope[..., None]
                                       * (wl - nm_long))
    return adg, a - adg - aw


@_data.positional_only()
def qaa_v6(wavelengths, rrs, /, *, bands, pure_water):
    """a and bbp from Rrs by QAA_v6.

    Lee, Z. P., "Steps and calculations of the Quasi-Analytical Algorithm
    (QAA_v6)", IOCCG (qaa_v6_202011.pdf), computed as the spreadsheet the
    IOCCG distributes with it computes it, QAA_v6-202011.xlsm, where the two
    differ (DATA.md section 28).

    Steps: rrs = Rrs / (0.52 + 1.7 Rrs); u = bb / (a + bb) from rrs = g0 u
    + g1 u^2, g0 = 0.08945, g1 = 0.1247. If Rrs(670) < 0.0015 sr^-1 the
    reference is 55x nm::

        chi = log10[(rrs443 + rrs490) / (rrs55x + 5 rrs670^2 / rrs490)]
        a(55x) = aw(55x) + 10^(h0 + h1 chi + h2 chi^2)

    else it is 670 nm, a(670) = aw(670) + 0.39 [rrs670 / (rrs443 +
    rrs490)]^1.14. Then bbp(ref) = u a / (1 - u) - bbw at the reference,
    eta = 2.0 [1 - 1.2 exp(-0.9 rrs443 / rrs55x)], bbp(l) = bbp(ref)
    (ref / l)^eta and a(l) = (1 - u)(bbw + bbp) / u. The split of a takes
    zeta = 0.74 + 0.2 / (0.8 + rrs443 / rrs55x) for aph(412) / aph(443),
    S = 0.015 + 0.002 / (0.6 + rrs443 / rrs55x) and xi = exp[S (443 -
    412)], with 443 and 412 the bands' own wavelengths.

    Parameters
    ----------
    wavelengths:
        nm, the bands of the Rrs, ascending.
    rrs:
        The remote sensing reflectance above the surface, sr^-1, one value
        per band along the last axis; other axes are spectra. NaN gives NaN.
    bands:
        A dict naming which of ``wavelengths`` plays each role: ``"412"``,
        ``"443"``, ``"490"``, ``"55x"`` and ``"670"``. No default: it is the
        sensor's. The document gives 547 nm (MODIS), 555 (SeaWiFS, VIIRS)
        or 560 (MERIS, OLCI) for 55x in its table of steps, and 550 for
        MODIS in its text.
    pure_water:
        ``(wavelengths, aw, bbw)``: pure water's absorption and
        backscattering, 1/m, interpolated linearly; it must cover the
        bands. No default: the spreadsheet uses its own values;
        :func:`pure_water_absorption` and :func:`pure_water_backscattering`
        give the package's.

    Returns
    -------
    A :class:`QAAResult`. Nothing is filtered: a spectrum the algorithm
    cannot invert gives a negative or NaN value, returned as computed.

    Notes
    -----
    The document's table of steps prints g0 = 0.089 and g1 = 0.1245, its
    text 0.0895 and 0.1247, and the spreadsheet 0.08945 and 0.1247; for xi
    the table has 442.5 - 415.5 nm, the text 443 - 411 and the spreadsheet
    443 - 412. This follows the spreadsheet, whose stored results it
    reproduces. The limits and the estimate of Rrs(670) in the text (eqs. 7
    to 9) are for satellite data and are not applied. DECISIONS.md
    section 67.
    """
    wl, r, i, water = _inputs(wavelengths, rrs, bands, pure_water,
                              _V6_BANDS)
    aw, bbw = water(wl)
    below = _below(r)
    u = _u(below, *_V6_G)
    rr = {k: below[..., i[k]] for k in _V6_BANDS}
    ratio = rr["443"] / rr["55x"]
    use_55x = r[..., i["670"]] < 0.0015
    h0, h1, h2 = _V6_H
    with np.errstate(divide="ignore", invalid="ignore"):
        chi = np.log10((rr["443"] + rr["490"])
                       / (rr["55x"] + 5 * rr["670"] / rr["490"] * rr["670"]))
    a_55x = aw[i["55x"]] + 10.0 ** (h0 + h1 * chi + h2 * chi ** 2)
    a_670 = aw[i["670"]] + 0.39 * (rr["670"]
                                   / (rr["443"] + rr["490"])) ** 1.14
    ref = np.where(use_55x, i["55x"], i["670"])
    a_ref = np.where(use_55x, a_55x, a_670)
    u_ref = np.take_along_axis(u, ref[..., None], axis=-1)[..., 0]
    bbp_ref = u_ref * a_ref / (1 - u_ref) - bbw[ref]
    eta = 2.0 * (1 - 1.2 * np.exp(-0.9 * ratio))
    ref_nm = wl[ref]
    bbp = bbp_ref[..., None] * (ref_nm[..., None] / wl) ** eta[..., None]
    a = (1 - u) * (bbw + bbp) / u
    zeta = 0.74 + 0.2 / (0.8 + ratio)
    slope = 0.015 + 0.002 / (0.6 + ratio)
    xi = np.exp(slope * (wl[i["443"]] - wl[i["412"]]))
    adg, aph = _decompose(wl, a, aw, i["412"], i["443"], zeta, xi, slope)
    return QAAResult(wavelengths=wl, a=a, bbp=bbp, adg=adg, aph=aph,
                     eta=eta, reference_nm=np.asarray(ref_nm, dtype=float),
                     version="v6")


@_data.positional_only()
def qaa_ioccg2006(wavelengths, rrs, /, *, bands, pure_water):
    """a and bbp from Rrs by the QAA of IOCCG Report 5 (2006).

    IOCCG (2006), Remote Sensing of Inherent Optical Properties:
    Fundamentals, Tests of Algorithms, and Applications, Lee, Z.-P. (ed.),
    Reports of the International Ocean-Colour Coordinating Group No. 5,
    chapter 10 (Lee, Carder and Arnone), pp. 73-77: the version that report
    tested on its synthetic and in situ data.

    Two references. At 555 nm, with rho = log10[max(Rrs440, Rrs490,
    Rrs510) / Rrs555], Kd(555) = 0.0605 + 10^(-1.163 - 1.969 rho + 1.239
    rho^2 + 0.417 rho^3 - 0.984 rho^4) and a(555) = 0.9 Kd(555) (1 - 6.8
    Rrs555) / (1 + 15.3 Rrs555) (eqs. 10.2, 10.3). At 640 nm, Rrs(640) =
    0.01 Rrs555 + 1.4 Rrs670 - 0.0005 Rrs670 / Rrs490 and a(640) = 0.31 +
    0.07 (rrs640 / rrs440)^1.1 (eqs. 10.4, 10.5). rrs = Rrs / (0.52 + 1.7
    Rrs); u = (-0.0895 + sqrt(0.008 + 0.499 rrs)) / 0.249; Y = 2.2 [1 - 1.2
    exp(-0.9 rrs440 / rrs555)]; bb(l) = bbw(l) + bbp(ref) (ref / l)^Y; a =
    (1 - u) bb / u (eqs. 10.6 to 10.10). The two solutions are blended by
    a(440) from 555 nm: that one below 0.3, the 640 nm one above 0.5, and
    linearly between (eq. 10.11); bbp follows from u and the blended a. The
    split of a takes zeta = 0.71 + 0.06 / (0.8 + rrs440 / rrs555), S = 0.015
    and xi = exp[S (440 - 410)] (eqs. 10.12 to 10.14), with 440 and 410 the
    bands' own wavelengths.

    Parameters
    ----------
    wavelengths:
        nm, the bands of the Rrs, ascending.
    rrs:
        The remote sensing reflectance above the surface, sr^-1, one value
        per band along the last axis; other axes are spectra. NaN gives NaN.
    bands:
        A dict naming which of ``wavelengths`` plays each role: ``"410"``,
        ``"440"``, ``"490"``, ``"510"``, ``"555"`` and ``"670"``. No
        default. The report used 410, 440, 490, 510 and 670 nm of its
        synthetic data, and for 555 the mean of 550 and 560 (p. 76).
    pure_water:
        ``(wavelengths, aw, bbw)``, 1/m, interpolated linearly; it must
        cover the bands and 640 nm. No default: the report used Pope & Fry
        (1997) for aw and Morel (1974) for bbw (pp. 73-75).

    Returns
    -------
    A :class:`QAAResult`. Nothing is filtered: the report counts 476 of its
    500 synthetic decompositions as valid without saying by what rule, so
    negative and NaN values are returned as computed.

    Notes
    -----
    The report's results on its synthetic data, Table 10.1 (p. 76), are
    reproduced to within 0.002 in RMSE and bias (DATA.md section 28).
    DECISIONS.md section 67.
    """
    wl, r, i, water = _inputs(wavelengths, rrs, bands, pure_water,
                              _R5_BANDS, extra_nm=(640.0,))
    aw, bbw = water(wl)
    _, bbw_640 = water(640.0)
    below = _below(r)

    def u_of(rrs_below):
        return (-0.0895 + np.sqrt(0.008 + 0.499 * rrs_below)) / 0.249

    u = u_of(below)
    R = {k: r[..., i[k]] for k in _R5_BANDS}
    rr = {k: below[..., i[k]] for k in _R5_BANDS}
    Y = 2.2 * (1 - 1.2 * np.exp(-0.9 * rr["440"] / rr["555"]))

    def solve(ref_nm, a_ref, u_ref, bbw_ref):
        bbp_ref = u_ref * a_ref / (1 - u_ref) - bbw_ref
        bb = bbw + bbp_ref[..., None] * (ref_nm / wl) ** Y[..., None]
        return (1 - u) * bb / u

    with np.errstate(divide="ignore", invalid="ignore"):
        rho = np.log10(np.maximum(np.maximum(R["440"], R["490"]), R["510"])
                       / R["555"])
    kd_555 = 0.0605 + 10.0 ** (-1.163 - 1.969 * rho + 1.239 * rho ** 2
                               + 0.417 * rho ** 3 - 0.984 * rho ** 4)
    a_555 = 0.9 * kd_555 * (1 - 6.8 * R["555"]) / (1 + 15.3 * R["555"])
    nm_555 = wl[i["555"]]
    from_555 = solve(nm_555, a_555, u[..., i["555"]], bbw[i["555"]])

    rrs_640 = (0.01 * R["555"] + 1.4 * R["670"]
               - 0.0005 * R["670"] / R["490"])
    below_640 = _below(rrs_640)
    a_640 = 0.31 + 0.07 * (below_640 / rr["440"]) ** 1.1
    from_640 = solve(640.0, a_640, u_of(below_640), bbw_640)

    weight = np.clip((from_555[..., i["440"]] - 0.3) / 0.2, 0.0, 1.0)
    a = (1 - weight[..., None]) * from_555 + weight[..., None] * from_640
    bbp = u * a / (1 - u) - bbw
    reference = np.where(weight == 0, nm_555,
                         np.where(weight == 1, 640.0, np.nan))
    reference = np.where(np.isnan(weight), np.nan, reference)

    zeta = 0.71 + 0.06 / (0.8 + rr["440"] / rr["555"])
    slope = np.full(np.shape(zeta), 0.015)
    xi = np.exp(slope * (wl[i["440"]] - wl[i["410"]]))
    adg, aph = _decompose(wl, a, aw, i["410"], i["440"], zeta, xi, slope)
    return QAAResult(wavelengths=wl, a=a, bbp=bbp, adg=adg, aph=aph,
                     eta=Y, reference_nm=np.asarray(reference, dtype=float),
                     version="ioccg2006")


# -- Raman scattering (DECISIONS.md section 71) ---------------------------

LEE2013_RAMAN = (
    "Lee, Z., Hu, C., Shang, S., Du, K., Lewis, M., Arnone, R. and Brewin, "
    "R. (2013), J. Geophys. Res. Oceans 118, 4241-4255, "
    "doi:10.1002/jgrc.20308, eqs. (11)-(13) and Table 2"
)

#: Lee et al. (2013) Table 2, p. 4245, as printed: (MODIS band nm, alpha,
#: beta1 in the unit of Rrs, beta2). The minus signs were read from the
#: page image; the PDF's text drops them.
_LEE2013_RAMAN_TABLE = (
    (412.0, 0.003, 0.014, -0.022),
    (443.0, 0.004, 0.015, -0.023),
    (488.0, 0.011, 0.010, -0.051),
    (531.0, 0.015, 0.010, -0.070),
    (551.0, 0.017, 0.010, -0.080),
    (667.0, 0.018, 0.010, -0.081),
)


@dataclass(frozen=True)
class RamanCorrection:
    """Rrs with the light Raman-scattered by the water removed.

    Arrays have the shape of the Rrs given, wavelengths along the last
    axis.
    """

    #: nm, the wavelengths of the Rrs given.
    wavelengths: np.ndarray
    #: RF, the Raman part of the measured Rrs over the rest (eq. 12).
    raman_factor: np.ndarray
    #: The corrected Rrs, Rrs_T / (1 + RF), sr^-1 (eq. 13).
    rrs: np.ndarray


@_data.positional_only()
def lee2013_raman_correction(wavelengths, rrs, /, *, bands):
    """Remove Raman scattering from a measured Rrs, Lee et al. (2013).

    ::

        RF(l) = alpha(l) Rrs_T(440) / Rrs_T(550)
                + beta1(l) Rrs_T(550) ** beta2(l)       (11)
        Rrs(l) = Rrs_T(l) / (1 + RF(l))                  (13)

    Rrs_T is the remote sensing reflectance as measured above the
    surface, sr^-1, Raman scattering included; the corrected Rrs is what
    the forward relations of this package and both QAA versions describe.
    ``rrs`` holds Rrs_T at ``wavelengths``, along its last axis. ``bands``
    names the wavelengths that play "440" and "550", each one of
    ``wavelengths``; there is no default (for MODIS, 443 and 547 or 551
    nm).

    alpha, beta1 and beta2 are Table 2's, at the MODIS bands 412, 443,
    488, 531, 551 and 667 nm, fitted to Hydrolight runs of the case 1
    model of Morel & Maritorena (2001) with chlorophyll from 0.02 to 3 mg
    m^-3; the paper puts the fit within about 15 percent of Hydrolight's
    RF. RF is computed at those six bands and interpolated linearly in
    wavelength between them, as the paper does for hyperspectral data
    (p. 4246). Outside 412-667 nm it raises :class:`ValueError`. For its
    own hyperspectral data the paper also extrapolated RF to 350 nm,
    without saying how, and set it to 0 below 400 nm, an assumption; this
    function does neither (DECISIONS.md section 71).

    NaN in Rrs_T passes through. Rrs_T must not be negative or infinite,
    and at the "550" band must be positive.
    """
    wl = np.asarray(wavelengths, dtype=float)
    if (wl.ndim != 1 or wl.size == 0 or not np.all(np.isfinite(wl))
            or np.any(np.diff(wl) <= 0)):
        raise ValueError("wavelengths must be one ascending list of finite "
                         "numbers, nm")
    table = np.array(_LEE2013_RAMAN_TABLE)
    lo, hi = table[0, 0], table[-1, 0]
    if wl[0] < lo or wl[-1] > hi:
        raise ValueError(
            f"Lee et al. (2013) give the correction at {lo:g}-{hi:g} nm; "
            f"wavelengths span {wl[0]:g}-{wl[-1]:g} nm. This package does "
            "not extrapolate.")
    r = np.asarray(rrs, dtype=float)
    if r.ndim == 0 or r.shape[-1] != wl.size:
        raise ValueError("rrs must have one value for each wavelength along "
                         "its last axis")
    if np.any(np.isinf(r)) or np.any(r < 0):
        raise ValueError("rrs must not be negative or infinite; NaN marks a "
                         "gap and gives NaN")
    roles = ("440", "550")
    if not isinstance(bands, dict) or set(bands) != set(roles):
        raise ValueError("bands must name the wavelength of '440' and '550', "
                         "and nothing else")
    index = {}
    for role in roles:
        hit = np.flatnonzero(wl == float(bands[role]))
        if hit.size != 1:
            raise ValueError(f"band {role!r} = {bands[role]!r} nm is not one "
                             "of wavelengths")
        index[role] = int(hit[0])
    r440 = r[..., index["440"]]
    r550 = r[..., index["550"]]
    if np.any(r550 == 0):
        raise ValueError("Rrs at the '550' band must be positive: eq. (11) "
                         "divides by it and raises it to a negative power")
    alpha, beta1, beta2 = table[:, 1], table[:, 2], table[:, 3]
    at_bands = (alpha * (r440 / r550)[..., None]
                + beta1 * r550[..., None] ** beta2)
    flat = at_bands.reshape(-1, table.shape[0])
    rf = np.array([np.interp(wl, table[:, 0], row) for row in flat])
    rf = rf.reshape(r.shape[:-1] + (wl.size,))
    return RamanCorrection(wavelengths=wl.copy(), raman_factor=rf,
                           rrs=r / (1.0 + rf))

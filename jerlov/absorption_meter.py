"""Scatter correction of reflective-tube absorption measurements (ac-9,
ac-s): DECISIONS.md section 100, DATA.md section 44.

Röttgers, R., McKee, D. and Woźniak, S. B. (2013), "Evaluation of scatter
corrections for ac-9 absorption measurements in coastal waters", Methods
in Oceanography 7, 21-39, doi:10.1016/j.mio.2013.11.001: their Table 1 and
Eqs. (1)-(5). The proportional method is that of Zaneveld, Kitchen and
Moore (1994), Proc. SPIE 2258, 44-55, doi:10.1117/12.190095.
"""

from __future__ import annotations

import numpy as np

from . import _data
from ._data import finite_number as _number
from .ocean_colour import _result, _spectral, _warn

#: The methods of Röttgers et al.'s (2013) Table 1, by their names.
ROTTGERS2013_METHODS = ("flat", "proportional", "flat+", "proportional+")
#: The span of am715 their Eq. (5) was fitted over, read from their Fig. 4
#: (natural samples; the cultures were left out): about 0.02 to 8 1/m.
_A715_FIT = (0.02, 8.0)


@_data.positional_only()
def rottgers2013_scatter_correction(am, cm, am_ref, cm_ref, /, *, method,
                                    ec=None, a_ref=None):
    """Absorption corrected for the scattering error of a reflective-tube
    absorption meter, by one of the methods Röttgers et al. (2013)
    compared.

    With am and cm the absorption and attenuation the instrument reads
    (after its temperature, salinity and pure-water corrections), and
    ``_ref`` their values at the reference wavelength (715 nm on an ac-9):

    - ``"flat"``, Eq. (1): a = am - am_ref
    - ``"proportional"``, Eq. (2b): a = am - am_ref [(1/ec) cm - am] /
      [(1/ec) cm_ref - am_ref]; with ec = 1 it is Eq. (2a), the method of
      Zaneveld et al. (1994)
    - ``"flat+"``, Eq. (3): a = am - (am_ref - a_ref)
    - ``"proportional+"``, Eq. (4): a = am - (am_ref - a_ref) [(1/ec) cm -
      am] / [(1/ec) cm_ref - a_ref]. The paper writes ac, "either am or
      a"; am is used here, since a is what is sought.

    The first two assume that nothing absorbs at the reference
    wavelength; Röttgers et al. found that "generally not valid", and the
    "+" methods take the true absorption there, ``a_ref``, measured or
    estimated (:func:`rottgers2013_a715`). Eq. (4) with a_ref = 0 is not
    Eq. (2b): the denominators differ by am_ref.

    Parameters
    ----------
    am, cm:
        The measured absorption and attenuation, 1/m, at the wavelengths
        to correct; numbers or arrays that broadcast. NaN marks a gap,
        and a gap in either is a gap in the result, by the flat methods
        too, which do not use cm: a wavelength the measurement has a gap
        at gives nothing there (DECISIONS.md section 105).
    am_ref, cm_ref:
        The same at the reference wavelength, 1/m; ``cm_ref`` is not used
        by the flat methods but must still be a number.
    method:
        One of :data:`ROTTGERS2013_METHODS`. No default.
    ec:
        The proportional methods only: the factor the attenuation is
        divided by, 1 for none; Röttgers et al. used 0.56, after Boss et
        al. (2009), for the ac-9's acceptance angle. No default.
    a_ref:
        The "+" methods only: the true absorption at the reference
        wavelength, 1/m. No default.

    Returns
    -------
    The corrected absorption, 1/m: a float if am and cm are numbers, an
    array otherwise.

    Raises
    ------
    ValueError
        For an unknown method, ec or a_ref given where the method does not
        use it or missing where it does, input that is not finite, and a
        denominator that is not positive.
    """
    if method not in ROTTGERS2013_METHODS:
        raise ValueError(f"method must be one of {ROTTGERS2013_METHODS}, "
                         f"not {method!r}; there is no default")
    proportional = method.startswith("proportional")
    plus = method.endswith("+")
    if proportional and ec is None:
        raise ValueError(f"{method!r} needs ec, the attenuation's correction "
                         "factor (1 for none, 0.56 in Röttgers et al.); "
                         "there is no default")
    if not proportional and ec is not None:
        raise ValueError(f"{method!r} does not use ec")
    if plus and a_ref is None:
        raise ValueError(f"{method!r} needs a_ref, the true absorption at "
                         "the reference wavelength")
    if not plus and a_ref is not None:
        raise ValueError(f"{method!r} assumes no absorption at the "
                         "reference wavelength and takes no a_ref; use "
                         f"{method + '+'!r}")
    am_arr = _spectral(am, "am")
    cm_arr = _spectral(cm, "cm")
    am_r = _number(am_ref, "am_ref")
    cm_r = _number(cm_ref, "cm_ref")
    offset = am_r - (_number(a_ref, "a_ref") if plus else 0.0)
    if not proportional:
        out = am_arr - offset + 0.0 * cm_arr
        return _result(out, am, cm)
    ec_value = _number(ec, "ec")
    if ec_value <= 0:
        raise ValueError("ec must be positive")
    factor = 1.0 / ec_value
    below = factor * cm_r - (float(a_ref) if plus else am_r)
    if below <= 0:
        raise ValueError("the denominator (1/ec) cm_ref - "
                         f"{'a_ref' if plus else 'am_ref'} is {below:g}; it "
                         "must be positive, the scattering at the "
                         "reference wavelength")
    out = am_arr - offset * (factor * cm_arr - am_arr) / below
    return _result(out, am, cm)


@_data.positional_only()
def rottgers2013_a715(am715, /):
    """The true absorption at 715 nm estimated from an ac-9's uncorrected
    reading there, Röttgers et al. (2013), Eq. (5)::

        a715 = 0.212 am715^1.135

    fitted to 85 natural samples from coastal European waters (r2 =
    0.930), algal cultures left out, against a PSICAM. For the
    ``a_ref`` of :func:`rottgers2013_scatter_correction`.

    Parameters
    ----------
    am715:
        1/m, positive; a number or an array. NaN marks a gap.

    Returns
    -------
    The estimated absorption at 715 nm, 1/m: a float for a number, an
    array otherwise.

    Notes
    -----
    Outside about 0.02 to 8 1/m, the span of their Fig. 4, a
    :class:`ProvenanceWarning` is given. They found it "most useful when
    am715 >~ 0.1 1/m", and their further work required "to establish the
    general applicability of Eq. (5)". It is for 715 nm on an ac-9.
    """
    am = _spectral(am715, "am715")
    if np.any(am <= 0):
        raise ValueError("am715 must be positive; NaN marks a gap")
    lo, hi = _A715_FIT
    known = am[~np.isnan(am)]
    if known.size and (known.min() < lo or known.max() > hi):
        _warn(f"Röttgers et al.'s (2013) Eq. (5) was fitted to am715 of "
              f"about {lo:g} to {hi:g} 1/m (their Fig. 4); some of these "
              "values lie outside that.")
    return _result(0.212 * am ** 1.135, am715)

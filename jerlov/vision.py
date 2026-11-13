"""Visual pigments, and how far apart two colours are to an eye.

Two pieces of visual ecology, each from its primary paper, with the values
that belong to a species left to the caller (DECISIONS.md section 64):

- the absorbance of a visual pigment, from the template of Govardovskii et
  al. (2000), given the wavelength of its peak and its chromophore;
- the distance between two colours in units of receptor noise, from the
  model of Vorobyev & Osorio (1998), given the noise in each receptor.

The quantum catches the second needs are integrals of a spectrum against the
first, which :func:`~jerlov.integrate_response` already computes.
"""

from __future__ import annotations

import warnings

import numpy as np

from . import _data
from .water import ProvenanceWarning, _like_input

GOVARDOVSKII2000 = (
    "Govardovskii, V. I., Fyhrquist, N., Reuter, T., Kuzmin, D. G. and "
    "Donner, K. (2000), 'In search of the visual pigment template', Visual "
    "Neuroscience 17, 509-528, doi:10.1017/S0952523800174036"
)
VOROBYEV1998 = (
    "Vorobyev, M. and Osorio, D. (1998), 'Receptor noise as a determinant "
    "of colour thresholds', Proc. R. Soc. Lond. B 265, 351-358, "
    "doi:10.1098/rspb.1998.0302"
)

#: The templates hold above this wavelength, nm (Govardovskii et al. 2000,
#: p. 525).
_SHORTEST_NM = 330.0
#: and for a peak above this, nm (their abstract).
_LOWEST_LAMBDA_MAX = 350.0
#: The peaks of the pigments the paper measured, nm (its Table 1, p. 519).
#: Outside these the template is the paper's claim, not its fit.
_MEASURED = {"A1": (357.0, 569.0), "A2": (444.0, 619.0)}


def _alpha(x, lambda_max, chromophore):
    """The alpha-band, eq. (1), with A1's constants from p. 515 and eq.
    (2), or A2's from p. 517 and eqs. (6a) and (6b)."""
    if chromophore == "A1":
        A, B, b, C, c, D = 69.7, 28.0, 0.922, -14.9, 1.104, 0.674
        a = 0.8795 + 0.0459 * np.exp(-(lambda_max - 300.0) ** 2 / 11940.0)
    else:
        B, b, C, c, D = 20.85, 0.9101, -10.37, 1.1123, 0.5343
        A = 62.7 + 1.834 * np.exp((lambda_max - 625.0) / 54.2)
        a = 0.875 + 0.0268 * np.exp((lambda_max - 665.0) / 40.7)
    return 1.0 / (np.exp(A * (a - x)) + np.exp(B * (b - x))
                  + np.exp(C * (c - x)) + D)


def _beta(wavelength, lambda_max, chromophore):
    """The beta-band, eq. (4): eqs. (5a) and (5b) with A_beta = 0.26 for
    A1 (p. 516), eqs. (8a) and (8b) for A2 (p. 517). A2's amplitude has no
    equation; 0.37 is the value the authors fixed it at (p. 517)."""
    if chromophore == "A1":
        amplitude = 0.26
        peak = 189.0 + 0.315 * lambda_max
        width = -40.5 + 0.195 * lambda_max
    else:
        amplitude = 0.37
        peak = 216.7 + 0.287 * lambda_max
        width = 317.0 - 1.149 * lambda_max + 0.00124 * lambda_max ** 2
    return amplitude * np.exp(-(((wavelength - peak) / width) ** 2))


@_data.positional_only()
def visual_pigment_template(wavelengths, /, *, lambda_max: float,
                            chromophore: str, beta: bool = True):
    """The absorbance of a visual pigment, relative to its peak.

    Govardovskii, V. I., Fyhrquist, N., Reuter, T., Kuzmin, D. G. and
    Donner, K. (2000), "In search of the visual pigment template", Visual
    Neuroscience 17, 509-528, doi:10.1017/S0952523800174036.

    The alpha-band is Lamb's (1995) form, eq. (1)::

        S(x) = 1 / (exp[A(a - x)] + exp[B(b - x)] + exp[C(c - x)] + D)

    with x = lambda_max / wavelength and the constants of p. 515 and eq. (2)
    for A1 pigments, of p. 517 and eqs. (6a) and (6b) for A2. The beta-band
    is the Gaussian of eq. (4), from eqs. (5a) and (5b) for A1 and (8a)
    and (8b) for A2.

    Parameters
    ----------
    wavelengths:
        nm, a number or an array; each above 330 nm, the range the paper
        gives its templates for (p. 525).
    lambda_max:
        The wavelength of the alpha-band's peak, nm, above 350 nm (the
        paper's abstract). It belongs to the species and the cell, so it has
        no default.
    chromophore:
        ``"A1"`` or ``"A2"``, the pigment's chromophore. The two have
        different templates, and the paper measured both in fish and
        amphibians (Table 1), so it has no default either.
    beta:
        ``True`` for the sum of the two bands, which the paper calls a
        complete description of the absorbance (p. 525); ``False`` for the
        alpha-band alone.

    Returns
    -------
    A float for a number, an array otherwise. The alpha-band as printed
    peaks within 0.2 percent of 1, not at exactly 1, and within 0.5 nm of
    ``lambda_max``; it is returned as printed.

    Notes
    -----
    The amplitude of A2's beta-band has no equation in the paper, which
    says it "shows no correlation with lambda_max" and fixed it at 0.37
    where the beta-peak lay outside the recording (p. 517). This uses that
    0.37.

    The paper's own measurements have peaks from 357 to 569 nm for A1 and
    from 444 to 619 nm for A2 (Table 1). A ``lambda_max`` outside those
    gives the template the paper claims for it, with a
    :class:`ProvenanceWarning`. DECISIONS.md section 64.
    """
    if chromophore not in _MEASURED:
        raise ValueError(f"chromophore must be 'A1' or 'A2', not "
                         f"{chromophore!r}")
    try:
        ok = (np.ndim(lambda_max) == 0 and bool(np.isfinite(lambda_max))
              and lambda_max > _LOWEST_LAMBDA_MAX)
    except TypeError:               # text, say: isfinite has no answer
        ok = False
    if not ok:
        raise ValueError(
            f"lambda_max must be one number above {_LOWEST_LAMBDA_MAX:g} nm, "
            f"the range the template was made for, not {lambda_max!r}")
    lambda_max = float(lambda_max)
    wl = np.asarray(wavelengths, dtype=float)
    if not np.all(np.isfinite(wl)) or np.any(wl <= _SHORTEST_NM):
        raise ValueError(
            f"wavelengths must be finite and above {_SHORTEST_NM:g} nm, the "
            "range the template was made for. This package does not "
            "extrapolate.")
    lo, hi = _MEASURED[chromophore]
    if not lo <= lambda_max <= hi:
        warnings.warn(
            f"lambda_max {lambda_max:g} nm is outside the {lo:g}-{hi:g} nm "
            f"of the {chromophore} pigments Govardovskii et al. (2000) "
            "measured. The template there is their claim that it holds for "
            "any lambda_max, not their fit.",
            ProvenanceWarning,
            stacklevel=_data.caller_stacklevel(),
        )
    out = _alpha(lambda_max / wl, lambda_max, chromophore)
    if beta:
        out = out + _beta(wl, lambda_max, chromophore)
    return _like_input(np.atleast_1d(out), wavelengths)


@_data.positional_only()
def receptor_noise_distance(catches_a, catches_b, /, *, noise):
    """The distance between two colours in units of receptor noise.

    Vorobyev, M. and Osorio, D. (1998), "Receptor noise as a determinant of
    colour thresholds", Proc. R. Soc. Lond. B 265, 351-358,
    doi:10.1098/rspb.1998.0302.

    Colour is taken to be coded by n - 1 opponent channels whose form does
    not matter, with the achromatic signal disregarded, and discrimination
    to be limited by noise in the receptors, independent between them
    (p. 352). The distance between two stimuli is then their general form
    (A7), p. 356, which this computes for any number of receptor types; for
    two, three and four it is their eqs. (3) to (5), p. 353.

    Parameters
    ----------
    catches_a, catches_b:
        The quantum catch of each receptor type, scaled so that the
        background gives 1 in every receptor (eqs. 1 and 2). With
        sensitivities ``r`` on ``r_wl``, shape ``(m, k)`` for ``k``
        receptor types,
        ``integrate_response(spectrum, wl, r, r_wl) /
        integrate_response(background, wl, r, r_wl)``, with both spectra
        in photons: a catch counts photons, and an energy spectrum would
        weight each wavelength differently. The receptor types run along
        the last axis; other axes broadcast.
    noise:
        The standard deviation of the noise in each receptor channel, e_i,
        in the same scaled units, one for each receptor type. No default:
        the paper derives it from the noise of one cell and the number of
        cells, e_i = nu_i / sqrt(eta_i) (eq. 7), and both belong to the
        species.

    Returns
    -------
    Delta S: a float for one pair of stimuli, an array otherwise. Stimuli
    are indistinguishable when it is below a threshold distance, which
    depends on the criterion adopted (p. 353).

    Notes
    -----
    The model holds for stimuli close to the background, in bright light,
    for large static targets on an achromatic background (p. 353), and is
    linear in the differences of the scaled catches, as the paper gives it.
    The logarithmic form used in later work is not this paper's, and is
    not included.

    The paper's eq. (4), for three receptor types, prints its last term as
    ``e_3^2 (Delta q_1 - q_2)^2``; computed from (A7), as the paper says it
    is, it is ``e_3^2 (Delta q_1 - Delta q_2)^2`` (DECISIONS.md section 64).
    """
    a = np.asarray(catches_a, dtype=float)
    b = np.asarray(catches_b, dtype=float)
    e = np.asarray(noise, dtype=float)
    if e.ndim != 1 or e.size < 2:
        raise ValueError("noise must be one value for each of two or more "
                         "receptor types")
    if not np.all(np.isfinite(e)) or np.any(e <= 0):
        raise ValueError("noise must be finite and positive for every "
                         "receptor")
    if a.ndim == 0 or b.ndim == 0:
        raise ValueError("catches_a and catches_b need one value for each "
                         "receptor type")
    if a.shape[-1] != e.size or b.shape[-1] != e.size:
        raise ValueError(
            f"catches_a and catches_b must have one value for each of the "
            f"{e.size} receptor types along their last axis, as noise does")
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        raise ValueError("catches must be finite numbers")
    delta = a - b
    # (A7) does not depend on the opponent matrix F (A8), only on the
    # inverse noise W = diag(1/e^2) with the achromatic direction, the
    # vector of ones, projected out: Delta q . (W - W 1 1' W / 1'W1) Delta q.
    # Written as the weighted spread about the weighted mean, which is the
    # same quantity without subtracting two nearly equal sums: that form
    # gave 1e-7, not 0, for a change of intensity alone.
    w = 1.0 / e ** 2
    mean = np.sum(w * delta, axis=-1, keepdims=True) / np.sum(w)
    distance = np.sqrt(np.sum(w * (delta - mean) ** 2, axis=-1))
    if np.ndim(distance) == 0:
        return float(distance)
    return distance

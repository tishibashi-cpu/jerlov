"""The Fournier-Forand phase function. DECISIONS.md section 127, DATA.md
section 52.

An analytic phase function for particles with a hyperbolic (Junge) size
distribution, each scattering in the anomalous diffraction approximation,
set by the particles' index of refraction relative to water and the slope
of the distribution. It is what HydroLight uses when it is given a
particle backscatter ratio. The form is the one Mobley et al. (2002)
print as the "latest form", from Fournier & Jonasz (1999):

    C. D. Mobley, L. K. Sundman and E. Boss (2002), "Phase function
    effects on oceanic light fields", Appl. Opt. 41(6), 1035-1050,
    doi:10.1364/AO.41.001035, Eqs. (1)-(3) and (7)-(8).

Fournier & Jonasz (1999, Proc. SPIE 3761, 62-70) and Fournier & Forand
(1994, Proc. SPIE 2258, 194-201) were not obtained; the equations were
read from Mobley et al.'s page images.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import _data
from .water import _as_array, _like_input

CITATION = (
    "Mobley, C. D., Sundman, L. K. and Boss, E. (2002), 'Phase function "
    "effects on oceanic light fields', Appl. Opt. 41(6), 1035-1050, "
    "doi:10.1364/AO.41.001035, Eqs. (1)-(3), after Fournier, G. R. and "
    "Jonasz, M. (1999), Proc. SPIE 3761, 62-70"
)

# Mobley et al.'s line through n and mu, Eq. (7) (p. 1042).
_MOBLEY2002_RELATION = (
    "n = 1.01 + 0.1542 (mu - 3), Mobley et al. (2002), Eq. (7)")

#: The Junge slopes the form is used for: the paper's Fig. 2 axis, and the
#: range the Ocean Optics Web Book gives for oceanic waters.
_MU_RANGE = (3.0, 5.0)
#: d180 = 4 / (3 (n - 1)^2) must exceed 1, or the form divides by zero.
_N_MAX = 1.0 + 2.0 / np.sqrt(3.0)
#: The backscatter ratios of HydroLight's library of these functions
#: (Mobley & Sundman, HydroLight 5.1 Technical Documentation, p. 22).
_B_RANGE = (0.0001, 0.5)


def _one_minus_power(d, nu):
    """1 - d**nu, without losing digits when nu is near 0."""
    return -np.expm1(nu * np.log(d))


def _backscatter_ratio(n: float, nu: float) -> float:
    """Eq. (3)."""
    d90 = 2.0 / (3.0 * (n - 1.0) ** 2)
    one_minus = _one_minus_power(d90, nu)
    return float(1.0 - (1.0 - d90 ** (nu + 1.0) - 0.5 * one_minus)
                 / ((1.0 - d90) * d90 ** nu))


@dataclass(frozen=True)
class FournierForand:
    """A Fournier-Forand phase function, from :func:`fournier_forand` or
    :func:`mobley2002_fournier_forand`.

    The form describes the particles alone and does not change with
    wavelength; pure water's scattering is not in it.
    """

    refractive_index: float
    """n, the particles' real index of refraction relative to water."""
    junge_slope: float
    """mu, the slope of the hyperbolic size distribution: the number of
    particles larger than r goes as r to the power -mu."""
    nu: float
    """(3 - mu) / 2, Eq. (2)."""
    backscatter_ratio: float
    """The share of scattering beyond 90 degrees, Eq. (3)."""
    relation: str | None
    """How n and mu were chosen from a backscatter ratio, or None when
    they were given."""

    def _delta(self, psi_rad: np.ndarray):
        k = 4.0 / (3.0 * (self.refractive_index - 1.0) ** 2)
        s = np.sin(psi_rad / 2.0) ** 2
        return k, s, k * s

    def _angles(self, angle_deg, *, zero: bool) -> np.ndarray:
        query = _as_array(angle_deg)
        if query.ndim > 1:
            raise ValueError(
                "angle_deg must be a number or a 1-D array of them, not an "
                f"array of shape {query.shape}")
        if not np.all(np.isfinite(query)):
            raise ValueError("angle_deg must be finite numbers")
        low_ok = query >= 0 if zero else query > 0
        if not np.all(low_ok & (query <= 180)):
            raise ValueError(
                "angle_deg must lie in "
                + ("0 to 180 degrees" if zero else
                   "(0, 180] degrees: at 0 the phase function is infinite"))
        return np.radians(query)

    def phase_function(self, angle_deg):
        """The phase function at ``angle_deg``, 1/sr, Mobley et al.'s Eq.
        (1)::

            beta(psi) = 1 / (4 pi (1 - d)^2 d^nu)
                          [nu (1 - d) - (1 - d^nu)
                           + (d (1 - d^nu) - nu (1 - d)) sin^-2(psi / 2)]
                      + (1 - d180^nu) / (16 pi (d180 - 1) d180^nu)
                          (3 cos^2 psi - 1)

            d = 4 / (3 (n - 1)^2) sin^2(psi / 2)

        Over the sphere it integrates to one. Multiply by the particles'
        scattering coefficient for their volume scattering function.

        ``angle_deg`` is a number or a 1-D array in (0, 180] degrees; at 0
        the function is infinite and is refused.
        """
        psi = self._angles(angle_deg, zero=False)
        nu = self.nu
        k, s, d = self._delta(psi)
        one_minus = _one_minus_power(d, nu)
        first = ((nu * (1.0 - d) - one_minus
                  + (d * one_minus - nu * (1.0 - d)) / s)
                 / (4.0 * np.pi * (1.0 - d) ** 2 * d ** nu))
        second = (_one_minus_power(k, nu)
                  / (16.0 * np.pi * (k - 1.0) * k ** nu)
                  * (3.0 * np.cos(psi) ** 2 - 1.0))
        return _like_input(first + second, angle_deg)

    def cumulative(self, angle_deg):
        """The share of scattering within ``angle_deg`` of the forward
        direction: 2 pi times the integral of the phase function times
        sin(psi) from 0 to ``angle_deg``.

        In closed form, derived from Eq. (1) (DECISIONS.md section 127),
        with s = sin^2(psi / 2)::

            F(psi) = (1 - d^(nu + 1) - (1 - d^nu) s) / ((1 - d) d^nu)
                   + (1 - d180^nu) / (8 (d180 - 1) d180^nu)
                       cos(psi) sin^2(psi)

        0 at 0 degrees, ``1 - backscatter_ratio`` at 90 and 1 at 180. It is
        what :attr:`ForwardScatter.fraction` is for a Petzold station.
        ``angle_deg`` is a number or a 1-D array in 0 to 180 degrees.
        """
        psi = self._angles(angle_deg, zero=True)
        out = np.zeros_like(psi)
        inside = psi > 0
        out[inside] = self._cumulative(psi[inside])
        return _like_input(out, angle_deg)

    def _cumulative(self, psi: np.ndarray) -> np.ndarray:
        nu = self.nu
        k, s, d = self._delta(psi)
        first = ((1.0 - d ** (nu + 1.0) - _one_minus_power(d, nu) * s)
                 / ((1.0 - d) * d ** nu))
        second = (_one_minus_power(k, nu) / (8.0 * (k - 1.0) * k ** nu)
                  * np.cos(psi) * np.sin(psi) ** 2)
        return first + second

    def mean_cosine(self) -> float:
        """The mean cosine of the scattering angle, the asymmetry g.

        Integrated by parts, ``-1 + integral from 0 to pi of F(psi)
        sin(psi)``, with F from :meth:`cumulative`, which is bounded where
        the phase function is not; the trapezoid on 20001 angles.
        """
        psi = np.linspace(0.0, np.pi, 20001)
        f = np.zeros_like(psi)
        f[1:] = self._cumulative(psi[1:])
        return float(-1.0 + _data.trapezoid(f * np.sin(psi), psi))

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return (f"<FournierForand n={self.refractive_index:.4g} "
                f"mu={self.junge_slope:.5g} "
                f"bb/b={self.backscatter_ratio:.4g}>")


def _make(n: float, mu: float, relation: str | None) -> FournierForand:
    nu = (3.0 - mu) / 2.0
    return FournierForand(refractive_index=n, junge_slope=mu, nu=nu,
                          backscatter_ratio=_backscatter_ratio(n, nu),
                          relation=relation)


def fournier_forand(*, refractive_index, junge_slope) -> FournierForand:
    """The Fournier-Forand phase function of a given index of refraction
    and Junge slope.

    Parameters
    ----------
    refractive_index:
        n, the particles' real index of refraction relative to water.
        Above 1 and below 1 + 2/sqrt(3) = 2.155, beyond which the form
        divides by zero. No default. Mobley et al.'s Fig. 2 shows 1.00 to
        1.20, their line, Eq. (7), runs from 1.01 to 1.318, and the Ocean
        Optics Web Book's pairs from 1.021 to 1.175.
    junge_slope:
        mu, the slope of the hyperbolic size distribution. Above 3 (at 3
        the form is 0/0) and at most 5 (where it becomes symmetric, with a
        backscatter ratio of 0.5): the range of the paper's Fig. 2 and of
        oceanic waters. No default.

    Returns
    -------
    :class:`FournierForand`.

    Notes
    -----
    A backscatter ratio alone does not fix n and mu: many pairs give the
    same ratio, with somewhat different shapes (Mobley et al. 2002,
    p. 1042). :func:`mobley2002_fournier_forand` chooses one pair, on their
    line. DECISIONS.md section 127.
    """
    n = _data.finite_number(refractive_index, "refractive_index")
    mu = _data.finite_number(junge_slope, "junge_slope")
    if not 1.0 < n < _N_MAX:
        raise ValueError(
            f"refractive_index must lie above 1 and below {_N_MAX:.4f}, "
            f"where the form is defined, not {n!r}")
    if not _MU_RANGE[0] < mu <= _MU_RANGE[1]:
        raise ValueError(
            "junge_slope must lie above 3 and at most 5, the range the form "
            f"is used for, not {mu!r}")
    return _make(n, mu, None)


def mobley2002_fournier_forand(backscatter_ratio, /) -> FournierForand:
    """The Fournier-Forand phase function of a backscatter ratio, with n
    and mu on Mobley et al.'s (2002) line, as HydroLight makes it.

    Mobley et al. (p. 1042) chose, "for simplicity", a line through n =
    1.01 at the smallest mu and their fit to Petzold's average-particle
    phase function (n = 1.10, mu = 3.5835)::

        n = 1.01 + 0.1542 (mu - 3),                Eq. (7)
        2 / (3 d90) = (0.01 - 0.3084 nu)^2,        Eq. (8)

    and Eq. (3) is solved with Eq. (8) for nu, here by bisection. It is
    one choice among many: of the five pairs in the Ocean Optics Web Book's
    table, four lie within 0.005 of it in n, and the one for a ratio of 0.4
    (n = 1.15, mu = 4.874) far from it (1.299 at that mu). For another
    pair, use :func:`fournier_forand`.

    Parameters
    ----------
    backscatter_ratio:
        bb/b of the particles, 0.0001 to 0.5, the range of HydroLight's
        library of these functions (HydroLight 5.1 Technical
        Documentation, p. 22). Not a total bb/b with pure water in it.

    Returns
    -------
    :class:`FournierForand`, with :attr:`~FournierForand.relation` naming
    the line.
    """
    b = _data.finite_number(backscatter_ratio, "backscatter_ratio")
    if not _B_RANGE[0] <= b <= _B_RANGE[1]:
        raise ValueError(
            f"backscatter_ratio must lie in {_B_RANGE[0]:g} to "
            f"{_B_RANGE[1]:g}, the range of HydroLight's library of these "
            f"functions, not {b!r}")

    def on_line(nu: float) -> float:
        return _backscatter_ratio(1.01 - 0.3084 * nu, nu)

    # B rises as nu falls from 0 (mu = 3) to -1 (mu = 5, B = 0.5).
    low, high = -1.0, -1e-12
    for _ in range(200):
        mid = 0.5 * (low + high)
        if on_line(mid) > b:
            low = mid
        else:
            high = mid
    nu = 0.5 * (low + high)
    if b == _B_RANGE[1]:
        nu = -1.0
    return _make(1.01 - 0.3084 * nu, 3.0 - 2.0 * nu, _MOBLEY2002_RELATION)

"""What an object at distance r looks like to an observer at the same depth.

The model is the standard single-scattering form for a horizontal path::

    L(r) = L_target * exp(-c*r) + B_inf * (1 - exp(-c*r))

The first term is exact given c. The second is not something this package can
supply: the veiling radiance B_inf depends on the backscattering coefficient
and on the shape of the phase function, neither of which is determined by the
Jerlov classification (DATA.md section 10). The caller provides it.

`veiling_radiance_estimate` offers the usual single-scattering estimate for
callers who have nothing better, but it must be called deliberately and it
still needs a backscattering ratio.

Deliberate limitations, recorded in DECISIONS.md section 13:

- **Horizontal paths only.** Observer and target are at the same depth, so
  the downwelling irradiance is a single spectrum. A slanted path would need
  integration along a changing depth.
- **No forward-scatter blur.** This gives the radiance of one point, not the
  sharpness of an image. Blur needs the full phase function.
- **Lambertian targets.**

The light falling on the target's visible face is stated, not assumed.
The observer looks horizontally, so that face is usually vertical and
receives only part of the downwelling irradiance Ed; how much depends on
the light field and on how the target is turned, and the water type does
not fix it. :meth:`Scene.observe` takes it as ``face_irradiance_ratio``,
the irradiance on the face divided by Ed, and has no default
(DECISIONS.md sections 33 and 34).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import _data
from .water import (
    Descent,
    MissingQuantityError,
    Water,
    _as_array,
    _require_number,
)


@dataclass(frozen=True)
class AttenuationCoefficients:
    """The three coefficients of the Akkaynak-Treibitz image formation model.

    That model, widely used in underwater vision, writes the observed radiance
    as::

        I = J * exp(-beta_D * r) + B_inf * (1 - exp(-beta_B * r))

    and its central point is that ``beta_D`` and ``beta_B`` are **not** equal
    and **not** constant: both depend on range, depth and the reflectance of
    the target.

    Under the single-scattering model this package implements, they are both
    simply the beam attenuation coefficient c, and :attr:`are_distinct` is
    False. Separating them needs measurements that this package does not have.

    This is still worth having. Implementations that fit these coefficients
    commonly bound them by guesswork for want of a physical starting point;
    ``c`` is that starting point, and :attr:`are_distinct` says plainly how far
    it can be trusted.
    """

    wavelengths: np.ndarray
    beta_D: np.ndarray
    """Attenuation of the direct signal, 1/m."""
    beta_B: np.ndarray
    """Attenuation governing the growth of backscatter, 1/m."""
    B_inf: np.ndarray | None
    """Veiling radiance at infinite range, if the caller supplied one."""
    distance_range_m: tuple[float, float]
    """The range the caller asked about. Recorded, not used: see the note."""
    are_distinct: bool
    """False when beta_D and beta_B could not be told apart."""
    note: str

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        lo, hi = self.distance_range_m
        return (
            f"<AttenuationCoefficients {lo:g}-{hi:g} m, "
            f"beta_D {'!=' if self.are_distinct else '=='} beta_B>"
        )


class Observation:
    """The result of looking at a target through water.

    All radiances are in whatever unit the caller used for the downwelling
    irradiance and the veiling radiance; the package does not impose one, but
    the two must agree.
    """

    __slots__ = ("wavelengths", "direct", "veiling", "transmittance",
                 "distance_m", "_target")

    def __init__(self, wavelengths, direct, veiling, transmittance,
                 distance_m, target_radiance) -> None:
        self.wavelengths = wavelengths
        self.direct = direct
        """Target radiance surviving the path: L_target * exp(-c*r)."""
        self.veiling = veiling
        """Path radiance added by scattering: B_inf * (1 - exp(-c*r))."""
        self.transmittance = transmittance
        """exp(-c*r). Free of approximation, given c."""
        self.distance_m = distance_m
        self._target = target_radiance

    @property
    def radiance(self) -> np.ndarray:
        """Total radiance reaching the observer."""
        return self.direct + self.veiling

    @property
    def veiling_fraction(self) -> np.ndarray:
        """Share of the observed radiance that is path radiance, 0 to 1.

        Near 1 the target contributes almost nothing and the observed colour
        is that of the water.
        """
        total = self.radiance
        return np.divide(
            self.veiling, total,
            out=np.full_like(total, np.nan), where=total != 0,
        )

    def contrast(self, background_radiance) -> np.ndarray:
        """Apparent contrast against a background seen through the same path.

        ``background_radiance`` is the radiance leaving the background, on
        the scene's wavelengths and in the unit of the target radiance
        (``reflectance * face_irradiance_ratio * downwelling / pi``, with
        the background's own ratio), not a reflectance.

        With ``L_t`` and ``L_b`` the radiances leaving target and background,
        ``t`` the transmittance and ``B`` the veiling radiance at infinity::

            C(r) = (L_t - L_b) t / (L_b t + B (1 - t))
                 = C_0 * L_b t / (L_b t + B (1 - t)),   C_0 = (L_t - L_b) / L_b

        The path radiance is common to both and cancels from the numerator,
        but not from the denominator, so the loss of contrast is the veiling
        light's doing rather than the transmittance's:

        - With no veiling radiance (``B = 0``) the contrast is not reduced at
          all; target and background are dimmed by the same factor.
        - Against a background that is the water itself (``L_b = B``, a
          horizontal line of sight into open water) it is ``C_0 * t``, the
          classic result.
        - It falls faster than that against a background darker than ``B``,
          and more slowly against a brighter one.
        """
        background = _as_array(background_radiance)
        observed_background = (
            background * self.transmittance
            + self.veiling
        )
        return np.divide(
            self.direct - background * self.transmittance,
            observed_background,
            out=np.full_like(observed_background, np.nan),
            where=observed_background != 0,
        )

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        lo, hi = self.wavelengths[0], self.wavelengths[-1]
        fraction = self.veiling_fraction
        if np.all(np.isnan(fraction)):
            # nanmin of nothing warns; NaN everywhere means nothing reached
            # the observer, or c was unknown at every wavelength.
            veiling = "undefined"
        else:
            veiling = (f"{np.nanmin(fraction):.0%}"
                       f"-{np.nanmax(fraction):.0%}")
        return (
            f"<Observation r={self.distance_m:g} m, {lo:g}-{hi:g} nm, "
            f"veiling {veiling}>"
        )


class Scene:
    """An observer and a target at the same depth in one body of water.

    Parameters
    ----------
    water:
        The :class:`~jerlov.water.Water` between them. Must carry both a
        and b, since the beam attenuation c = a + b drives everything.
    downwelling:
        Downwelling irradiance at that depth, on ``wavelengths``. Any unit;
        the veiling radiance passed to :meth:`observe` must use the same one.
    wavelengths:
        Wavelengths in nm at which everything is evaluated.
    depth_m:
        Recorded for reference. Not used in the calculation: with a
        horizontal path the depth enters only through ``downwelling``.
    """

    @_data.positional_only()
    def __init__(self, water: Water, downwelling, wavelengths, /,
                 *, depth_m: float | None = None) -> None:
        if not (water.has("a") and water.has("b")):
            raise MissingQuantityError(
                "the water must carry both a and b; c = a + b drives the path"
            )
        self.water = water
        # Copies, so that changing the caller's arrays afterwards cannot
        # leave the wavelengths out of step with c, evaluated once below.
        self.wavelengths = np.array(wavelengths, dtype=float)
        if self.wavelengths.ndim != 1 or self.wavelengths.size == 0:
            raise ValueError("wavelengths must be a non-empty 1-D array")
        self.downwelling = np.array(downwelling, dtype=float)
        if self.downwelling.shape != self.wavelengths.shape:
            raise ValueError(
                "downwelling must have the same shape as wavelengths")
        if np.any(self.downwelling < 0):
            raise ValueError("downwelling irradiance cannot be negative")
        self.depth_m = depth_m
        # Evaluated once; Water raises for wavelengths outside its data and
        # warns for any that rest on flagged values.
        self._c = water.c(self.wavelengths)
        _refuse_negative(self._c, self.wavelengths, "c = a + b")

    @classmethod
    @_data.positional_only()
    def at_depth(cls, water: Water, depth_m: float, surface_downwelling,
                 wavelengths, /, *, kd) -> "Scene":
        """Build a scene by attenuating a surface spectrum down to ``depth_m``.

        ``kd`` says how the light got there. Either:

        - a :class:`~jerlov.water.Water` carrying Kd, such as
          ``jerlov.water("III", source="austin1986")``, or an array on
          ``wavelengths``. Then ``Ed(z) = Ed(0) * exp(-Kd * z)``, which
          assumes Kd is constant with depth. Jerlov's classification is
          defined over the upper 10 m, so this is reasonable there and
          increasingly rough below it. The default IOP source has no Kd of
          its own, so it must come from somewhere explicit.
        - a :class:`~jerlov.water.Descent` to ``depth_m`` on the same
          wavelengths, from :func:`~jerlov.descend`, which changes the type
          layer by layer::

              d = jerlov.descend("1C", 45.0, wl)
              scene = jerlov.Scene.at_depth(jerlov.water("II"), 45.0,
                                            surface, wl, kd=d)

        ``water`` is the water along the horizontal path at ``depth_m``,
        and nothing checks it against the descent: there it is the type of
        the last layer, ``d.layers[-1][2]``, unless you know better.
        """
        wavelengths = np.asarray(wavelengths, dtype=float)
        _require_number(depth_m, "depth_m")
        if not np.isfinite(depth_m):
            # An infinite depth with a Kd of 0 gave 0 * inf, NaN.
            raise ValueError(f"depth_m must be finite, not {depth_m!r}")
        if depth_m < 0:
            raise ValueError("depth_m cannot be negative")
        surface = np.asarray(surface_downwelling, dtype=float)
        if surface.shape != wavelengths.shape:
            raise ValueError(
                "surface_downwelling must have the same shape as wavelengths"
            )
        if isinstance(kd, Descent):
            if kd.depth_m != float(depth_m):
                raise ValueError(
                    f"the descent goes to {kd.depth_m:g} m, but the scene is "
                    f"at {float(depth_m):g} m"
                )
            if not np.array_equal(kd.wavelengths, np.atleast_1d(wavelengths)):
                raise ValueError(
                    "the descent was computed on other wavelengths; pass the "
                    "same wavelengths to descend() and at_depth()"
                )
            downwelling = surface * kd.transmittance
        else:
            kd_values = kd.kd(wavelengths) if isinstance(kd, Water) else (
                np.asarray(kd, dtype=float)
            )
            if np.shape(kd_values) != wavelengths.shape:
                raise ValueError("kd must have the same shape as wavelengths")
            if np.any(np.isinf(kd_values)):
                raise ValueError("kd must be finite (NaN marks a gap)")
            # A negative Kd made the light brighter with depth; par_profile
            # has always refused one. DECISIONS.md section 60.
            _refuse_negative(kd_values, wavelengths, "Kd")
            downwelling = surface * np.exp(-kd_values * depth_m)
        return cls(water, downwelling, wavelengths, depth_m=depth_m)

    # -- the path --------------------------------------------------------

    def transmittance(self, distance_m: float) -> np.ndarray:
        """``exp(-c*r)``. No approximation beyond the value of c itself."""
        if np.size(distance_m) != 1:
            raise ValueError(
                f"distance_m must be a single distance, in m, not "
                f"{distance_m!r}; call once for each distance")
        _require_number(distance_m, "distance_m")
        if distance_m < 0:
            raise ValueError("distance_m cannot be negative")
        return np.exp(-self._c * distance_m)

    def attenuation_coefficients(
        self,
        distance_range_m: tuple[float, float],
        *,
        veiling_radiance=None,
    ) -> AttenuationCoefficients:
        """Coefficients for the Akkaynak-Treibitz form, from this scene.

        Parameters
        ----------
        distance_range_m:
            The range of distances the coefficients are meant to describe.
            Required, and recorded on the result. Under single scattering the
            coefficients do not depend on it, but Akkaynak & Treibitz (2018)
            showed that in reality they do, so a value quoted without its
            range is not a well-defined quantity.
        veiling_radiance:
            Optional B_inf, carried through unchanged. There is no default;
            see :meth:`observe`.

        Notes
        -----
        ``beta_D`` and ``beta_B`` both come out equal to the beam attenuation
        coefficient c, because that is what the single-scattering model says.
        Check :attr:`~AttenuationCoefficients.are_distinct` before treating
        them as two independent quantities.
        """
        low, high = (float(v) for v in distance_range_m)
        _require_number((low, high), "distance_range_m")
        if low < 0 or high < low:
            raise ValueError(
                "distance_range_m must be (low, high) with 0 <= low <= high"
            )
        b_inf = None
        if veiling_radiance is not None:
            b_inf = np.asarray(veiling_radiance, dtype=float)
            if b_inf.shape != self.wavelengths.shape:
                raise ValueError(
                    "veiling_radiance must have the same shape as wavelengths"
                )
            if np.any(b_inf < 0):
                raise ValueError("veiling_radiance cannot be negative")
        c = self._c.copy()
        return AttenuationCoefficients(
            wavelengths=self.wavelengths,
            beta_D=c,
            beta_B=c.copy(),
            B_inf=b_inf,
            distance_range_m=(low, high),
            are_distinct=False,
            note=(
                "beta_D and beta_B are both the beam attenuation coefficient "
                "c, because this package implements single scattering. "
                "Akkaynak & Treibitz (2018) show that in reality they differ "
                "and vary with range, depth and target reflectance. Use these "
                "as a physical starting point, not as two measured "
                "quantities."
            ),
        )

    def observe(self, reflectance, distance_m: float, *,
                veiling_radiance, face_irradiance_ratio=None) -> Observation:
        """Look at a Lambertian target ``distance_m`` away.

        The radiance leaving the target is
        ``reflectance * face_irradiance_ratio * downwelling / pi``.

        Parameters
        ----------
        reflectance:
            Spectral reflectance of the target, 0 to 1, on the scene's
            wavelengths.
        distance_m:
            Horizontal distance to the target.
        veiling_radiance:
            The path radiance at infinite distance, B_inf, on the scene's
            wavelengths and in the same unit as the downwelling irradiance.
            There is no default: see DECISIONS.md section 4.
        face_irradiance_ratio:
            The irradiance on the face of the target that the observer sees,
            divided by the downwelling irradiance: 1 for a face turned
            straight up, less for one turned towards a horizontal line of
            sight. A number, or an array on the scene's wavelengths, finite
            and not negative. It can exceed 1, for a face turned towards
            the sun. The water type does not determine it.

            Required: there is no default, for the reason ``bb`` has none.
            Releases up to 0.10.0 took it as 1 without saying so, and 0.11.0
            did so with a ``FutureWarning``. See DECISIONS.md sections 33
            and 34.
        """
        rho = np.asarray(reflectance, dtype=float)
        if rho.shape != self.wavelengths.shape:
            raise ValueError(
                "reflectance must have the same shape as wavelengths")
        if np.any(rho < 0) or np.any(rho > 1):
            raise ValueError("reflectance must lie between 0 and 1")
        if veiling_radiance is None:
            raise MissingQuantityError(
                "veiling_radiance (B_inf) has no default: it depends on the "
                "backscattering coefficient and the phase function, neither "
                "of which follows from the Jerlov water type. Measure it, or "
                "call jerlov.veiling_radiance_estimate() deliberately. "
                "See DATA.md section 10."
            )
        b_inf = np.asarray(veiling_radiance, dtype=float)
        if b_inf.shape != self.wavelengths.shape:
            raise ValueError(
                "veiling_radiance must have the same shape as wavelengths"
            )
        if np.any(b_inf < 0):
            raise ValueError("veiling_radiance cannot be negative")
        if face_irradiance_ratio is None:
            raise MissingQuantityError(
                "face_irradiance_ratio has no default: it is the irradiance "
                "on the face of the target the observer sees, divided by the "
                "downwelling irradiance, and the water type does not fix it. "
                "Pass 1.0 for a face turned straight up, which is what "
                "releases before 0.12.0 assumed; a face turned towards a "
                "horizontal line of sight receives less, and how much less "
                "can change the sign of the contrast. See DECISIONS.md "
                "section 34."
            )
        ratio = _face_ratio(face_irradiance_ratio, self.wavelengths.shape)

        target = rho * ratio * self.downwelling / np.pi
        t = self.transmittance(distance_m)
        return Observation(
            wavelengths=self.wavelengths,
            direct=target * t,
            veiling=b_inf * (1.0 - t),
            transmittance=t,
            distance_m=float(distance_m),
            target_radiance=target,
        )

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        lo, hi = self.wavelengths[0], self.wavelengths[-1]
        depth = (f"{self.depth_m:g} m" if self.depth_m is not None
                 else "unstated")
        return (
            f"<Scene {self.water.name or 'unnamed'} depth={depth} "
            f"{lo:g}-{hi:g} nm>"
        )


def _refuse_negative(values, wavelengths, name: str) -> None:
    """Refuse a negative coefficient where a result would rest on it.

    A water built with one has already warned (DECISIONS.md section 60);
    this is where it would turn into a light that grows along the path.
    NaN, a gap, passes.
    """
    negative = np.atleast_1d(values) < 0
    if np.any(negative):
        shown = ", ".join(f"{w:g}" for w in
                          np.atleast_1d(wavelengths)[negative][:5])
        raise ValueError(
            f"{name} is negative at {shown} nm, which no water can be: the "
            "light would grow along its path. A total "
            "coefficient includes pure water; set a wavelength you cannot "
            "trust to NaN to leave it out")


def _face_ratio(value, shape) -> np.ndarray | float:
    """The face irradiance ratio, checked: a number or an array of ``shape``,
    finite and not negative."""
    try:
        ratio = np.array(value, dtype=float)
    except (TypeError, ValueError):
        raise ValueError(
            f"face_irradiance_ratio must be a number or an array on the "
            f"scene's wavelengths, not {value!r}") from None
    if ratio.ndim != 0 and ratio.shape != shape:
        raise ValueError(
            "face_irradiance_ratio must be a number or have the same shape "
            "as wavelengths")
    _require_number(ratio, "face_irradiance_ratio")
    if np.any(np.isinf(ratio)) or np.any(ratio < 0):
        raise ValueError(
            "face_irradiance_ratio must be finite and not negative")
    return float(ratio) if ratio.ndim == 0 else ratio


@_data.positional_only()
def veiling_radiance_estimate(water: Water, downwelling, wavelengths, /, *,
                              backscatter_ratio: float) -> np.ndarray:
    """Single-scattering estimate of the veiling radiance B_inf.

    ::

        B_inf = bb * Ed / (2 * pi * c)

    **This is an approximation, not a derivation.** It assumes the
    backscattered light is spread uniformly over the backward hemisphere,
    which is why the factor is 2*pi. Real phase functions are strongly peaked,
    so the result should be treated as an order of magnitude rather than a
    value.

    It also inherits everything uncertain about ``backscatter_ratio``, which
    is not determined by the Jerlov water type; reported ranges are roughly
    0.005-0.01 for open ocean and 0.015-0.03 for coastal water.

    Provided so that a caller with no measurement is not stuck, but it must be
    called deliberately: :meth:`Scene.observe` will not reach for it.
    """
    wavelengths = np.asarray(wavelengths, dtype=float)
    ed = np.asarray(downwelling, dtype=float)
    if ed.shape != wavelengths.shape:
        raise ValueError("downwelling must have the same shape as wavelengths")
    if np.any(ed < 0):
        # Scene refuses this too; a negative irradiance gave a negative B_inf.
        raise ValueError("downwelling irradiance cannot be negative")
    bb = water.bb(wavelengths, backscatter_ratio=backscatter_ratio)
    c = water.c(wavelengths)
    _refuse_negative(c, wavelengths, "c = a + b")
    _refuse_negative(bb, wavelengths, "bb")
    return bb * ed / (2.0 * np.pi * c)

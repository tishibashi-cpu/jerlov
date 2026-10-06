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
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .water import MissingQuantityError, Water, _as_array, _require_number


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
        (``reflectance * downwelling / pi``), not a reflectance.

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
        return (
            f"<Observation r={self.distance_m:g} m, {lo:g}-{hi:g} nm, "
            f"veiling {np.nanmin(self.veiling_fraction):.0%}"
            f"-{np.nanmax(self.veiling_fraction):.0%}>"
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

    def __init__(self, water: Water, downwelling, wavelengths,
                 *, depth_m: float | None = None) -> None:
        if not (water.has("a") and water.has("b")):
            raise MissingQuantityError(
                "the water must carry both a and b; c = a + b drives the path"
            )
        self.water = water
        self.wavelengths = np.asarray(wavelengths, dtype=float)
        if self.wavelengths.ndim != 1 or self.wavelengths.size == 0:
            raise ValueError("wavelengths must be a non-empty 1-D array")
        self.downwelling = np.asarray(downwelling, dtype=float)
        if self.downwelling.shape != self.wavelengths.shape:
            raise ValueError("downwelling must have the same shape as wavelengths")
        if np.any(self.downwelling < 0):
            raise ValueError("downwelling irradiance cannot be negative")
        self.depth_m = depth_m
        # Evaluated once; Water raises for wavelengths outside its data and
        # warns for any that rest on flagged values.
        self._c = water.c(self.wavelengths)

    @classmethod
    def at_depth(cls, water: Water, depth_m: float, surface_downwelling,
                 wavelengths, *, kd) -> "Scene":
        """Build a scene by attenuating a surface spectrum down to ``depth_m``.

        ``Ed(z) = Ed(0) * exp(-Kd * z)``, which assumes Kd is constant with
        depth. Jerlov's own classification is defined over the upper 10 m, so
        this is reasonable there and increasingly rough below it.

        ``kd`` is either a :class:`~jerlov.water.Water` carrying Kd, such as
        ``jerlov.water("III", source="austin1986")``, or an array on
        ``wavelengths``. The default IOP source has no Kd of its own, so it
        must come from somewhere explicit.
        """
        wavelengths = np.asarray(wavelengths, dtype=float)
        _require_number(depth_m, "depth_m")
        if depth_m < 0:
            raise ValueError("depth_m cannot be negative")
        surface = np.asarray(surface_downwelling, dtype=float)
        if surface.shape != wavelengths.shape:
            raise ValueError(
                "surface_downwelling must have the same shape as wavelengths"
            )
        kd_values = kd.kd(wavelengths) if isinstance(kd, Water) else (
            np.asarray(kd, dtype=float)
        )
        if kd_values.shape != wavelengths.shape:
            raise ValueError("kd must have the same shape as wavelengths")
        return cls(
            water,
            surface * np.exp(-kd_values * depth_m),
            wavelengths,
            depth_m=depth_m,
        )

    # -- the path --------------------------------------------------------

    def transmittance(self, distance_m: float) -> np.ndarray:
        """``exp(-c*r)``. No approximation beyond the value of c itself."""
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
                veiling_radiance) -> Observation:
        """Look at a Lambertian target ``distance_m`` away.

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
        """
        rho = np.asarray(reflectance, dtype=float)
        if rho.shape != self.wavelengths.shape:
            raise ValueError("reflectance must have the same shape as wavelengths")
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

        target = rho * self.downwelling / np.pi
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
        depth = f"{self.depth_m:g} m" if self.depth_m is not None else "unstated"
        return (
            f"<Scene {self.water.name or 'unnamed'} depth={depth} "
            f"{lo:g}-{hi:g} nm>"
        )


def veiling_radiance_estimate(water: Water, downwelling, wavelengths, *,
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
    return bb * ed / (2.0 * np.pi * c)

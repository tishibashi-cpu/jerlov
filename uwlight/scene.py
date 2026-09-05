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

import numpy as np

from .water import MissingQuantityError, Water, _as_array


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

        The path radiance is common to target and background and cancels, so
        this is the inherent contrast reduced by the transmittance.
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
        The :class:`~uwlight.water.Water` between them. Must carry both a
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

        ``kd`` is either a :class:`~uwlight.water.Water` carrying Kd, such as
        ``uwlight.water("III", source="austin1986")``, or an array on
        ``wavelengths``. The default IOP source has no Kd of its own, so it
        must come from somewhere explicit.
        """
        wavelengths = np.asarray(wavelengths, dtype=float)
        if depth_m < 0:
            raise ValueError("depth_m cannot be negative")
        kd_values = kd.kd(wavelengths) if isinstance(kd, Water) else (
            np.asarray(kd, dtype=float)
        )
        if kd_values.shape != wavelengths.shape:
            raise ValueError("kd must have the same shape as wavelengths")
        surface = np.asarray(surface_downwelling, dtype=float)
        return cls(
            water,
            surface * np.exp(-kd_values * depth_m),
            wavelengths,
            depth_m=depth_m,
        )

    # -- the path --------------------------------------------------------

    def transmittance(self, distance_m: float) -> np.ndarray:
        """``exp(-c*r)``. No approximation beyond the value of c itself."""
        if distance_m < 0:
            raise ValueError("distance_m cannot be negative")
        return np.exp(-self._c * distance_m)

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
                "call uwlight.veiling_radiance_estimate() deliberately. "
                "See DATA.md section 10."
            )
        b_inf = np.asarray(veiling_radiance, dtype=float)
        if b_inf.shape != self.wavelengths.shape:
            raise ValueError(
                "veiling_radiance must have the same shape as wavelengths"
            )

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
    bb = water.bb(wavelengths, backscatter_ratio=backscatter_ratio)
    c = water.c(wavelengths)
    return bb * ed / (2.0 * np.pi * c)

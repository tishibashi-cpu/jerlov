"""The irradiance at the sea surface under a cloudless sky.

Gregg, W. W. and Carder, K. L. (1990), "A simple spectral solar irradiance
model for cloudless maritime atmospheres", Limnol. Oceanogr. 35(8),
1657-1675, doi:10.4319/lo.1990.35.8.1657: the direct and diffuse
downwelling irradiance just above and just below the sea surface, at every
nm from 350 to 700, from the sun's position and the state of the
atmosphere and the sea (DECISIONS.md section 76).

The sun's spectrum and the gases' absorption coefficients are the paper's
Table 1, transcribed from the page images (DATA.md section 35). Every input
describing the atmosphere is the caller's; none has a default.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import _data

GREGG1990 = (
    "Gregg, W. W. and Carder, K. L. (1990), 'A simple spectral solar "
    "irradiance model for cloudless maritime atmospheres', Limnol. "
    "Oceanogr. 35(8), 1657-1675, doi:10.4319/lo.1990.35.8.1657"
)

#: Standard pressure, hPa (the paper's list of symbols, p. 1659).
_P0 = 1013.25
#: The aerosol scale height, km, eq. (29) (p. 1665).
_AEROSOL_SCALE_HEIGHT_KM = 1.0
#: Orbital eccentricity, eq. (12).
_ECCENTRICITY = 0.0167
#: The Navy aerosol model's mode radii, um, and the factor R on the large
#: particles (p. 1664).
_MODE_RADII = (0.03, 0.24, 2.0)
_R = 0.05
#: Seawater's refractive index for the sea surface's reflectance (p. 1667).
_N_SEAWATER = 1.341
#: Density of air, g m^-3, and the foam coefficients D1-D4 (p. 1666).
_AIR_DENSITY = 1.2e3
_D = (2.2e-5, 4.0e-4, 4.5e-5, 4.0e-5)


@dataclass(frozen=True)
class SurfaceIrradiance:
    """Downwelling irradiance at the sea surface, W m-2 nm-1.

    "Above" is just above the surface (eqs. 2, 4 and 6 of Gregg and Carder
    1990, without the ground-air term the paper drops); "below" is just
    beneath it, after the surface's reflection (eqs. 9 and 10).
    """

    wavelengths: np.ndarray
    direct_above: np.ndarray
    diffuse_above: np.ndarray
    direct_below: np.ndarray
    diffuse_below: np.ndarray
    angstrom_exponent: float
    """alpha of eq. (26), from the aerosol model."""
    aerosol_optical_thickness: np.ndarray
    """tau_a at each wavelength, eq. (27)."""
    direct_reflectance: float
    """rho_d, eq. (37): specular and foam."""
    diffuse_reflectance: float
    """rho_s, eq. (38): specular and foam."""

    @property
    def above(self) -> np.ndarray:
        """Global irradiance just above the surface."""
        return self.direct_above + self.diffuse_above

    @property
    def below(self) -> np.ndarray:
        """Global irradiance just below the surface, eq. (11)."""
        return self.direct_below + self.diffuse_below

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        lo, hi = self.wavelengths.min(), self.wavelengths.max()
        return (f"<SurfaceIrradiance {lo:g}-{hi:g} nm, "
                f"alpha {self.angstrom_exponent:.2f}>")


def _number(value, name: str) -> float:
    if np.ndim(value) != 0 or not np.isfinite(value):
        raise ValueError(f"{name} must be one finite number, not {value!r}")
    return float(value)


def _at_least(value, name: str, low: float) -> float:
    number = _number(value, name)
    if number < low:
        raise ValueError(f"{name} must be at least {low:g}, not {number:g}")
    return number


def _wavelength_rows(wavelength_nm) -> tuple[np.ndarray, np.ndarray]:
    query = np.asarray(wavelength_nm, dtype=float)
    if np.any(np.isnan(query)):
        raise ValueError("wavelength_nm must be numbers, not NaN")
    if np.any(query < 350) or np.any(query > 700) or np.any(
            query != np.round(query)):
        raise ValueError(
            "wavelength_nm must be whole nanometres from 350 to 700, the "
            "rows of Gregg and Carder's Table 1; the package does not "
            "interpolate the absorption coefficients. Interpolate the "
            "result instead.")
    return query, (query - 350).astype(int)


def _angstrom(air_mass_type, relative_humidity, wind_24h, wind) -> float:
    """Eqs. (20)-(26): the Navy aerosol model's size distribution at 0.1,
    1 and 10 um, fitted by a Junge distribution."""
    a1 = 2000.0 * air_mass_type ** 2
    a2 = max(5.866 * (wind_24h - 2.2), 0.5)
    a3 = max(0.01527 * (wind - 2.2) * _R, 1.4e-5)
    growth = ((2 - relative_humidity / 100)
              / (6 * (1 - relative_humidity / 100))) ** (1 / 3)
    radius = np.array([0.1, 1.0, 10.0])
    dn_dr = sum(a * np.exp(-np.log(radius / (growth * r0)) ** 2)
                for a, r0 in zip((a1, a2, a3), _MODE_RADII)) / growth
    gamma = np.polyfit(np.log(radius), np.log(dn_dr), 1)[0]
    return float(-(gamma + 3))


def _fresnel(sun_zenith_deg: float) -> float:
    """Eq. (44), Fresnel's law for unpolarized light, without the second
    1/2 the paper prints inside the bracket (DATA.md section 35)."""
    if sun_zenith_deg == 0:
        return ((_N_SEAWATER - 1) / (_N_SEAWATER + 1)) ** 2
    t = np.radians(sun_zenith_deg)
    tr = np.arcsin(np.sin(t) / _N_SEAWATER)
    return float(0.5 * (np.sin(t - tr) ** 2 / np.sin(t + tr) ** 2
                        + np.tan(t - tr) ** 2 / np.tan(t + tr) ** 2))


def _foam(wind: float) -> float:
    """Eqs. (39)-(43)."""
    d1, d2, d3, d4 = _D
    if wind <= 4:
        return 0.0
    if wind <= 7:
        drag = (0.62 + 1.56 / wind) * 1e-3
        return d1 * _AIR_DENSITY * drag * wind ** 2 - d2
    drag = (0.49 + 0.065 * wind) * 1e-3
    return (d3 * _AIR_DENSITY * drag - d4) * wind ** 2


def _surface_reflectance(sun_zenith_deg: float, wind: float
                         ) -> tuple[float, float]:
    """Eqs. (37)-(47): rho_d and rho_s."""
    if sun_zenith_deg >= 40 and wind > 2:
        b = -7.14e-4 * wind + 0.0618
        specular = 0.0253 * float(np.exp(b * (sun_zenith_deg - 40)))
    else:
        specular = _fresnel(sun_zenith_deg)
    foam = _foam(wind)
    diffuse_specular = 0.057 if wind > 4 else 0.066
    return specular + foam, diffuse_specular + foam


@_data.positional_only()
def gregg1990_irradiance(wavelength_nm, /, *, sun_zenith_deg, day_of_year,
                         pressure_hpa, air_mass_type, relative_humidity,
                         precipitable_water_cm, wind_speed_24h, wind_speed,
                         ozone_du, visibility_km=None,
                         aerosol_optical_thickness_550=None,
                         ) -> SurfaceIrradiance:
    """Direct and diffuse irradiance at the sea surface under a clear sky.

    The model of Gregg and Carder (1990), Limnol. Oceanogr. 35(8),
    1657-1675, doi:10.4319/lo.1990.35.8.1657, eqs. (2)-(47), with the sun's
    spectrum and the ozone, water vapour and oxygen absorption of its
    Table 1. Section 76 of DECISIONS.md gives the design.

    Parameters
    ----------
    wavelength_nm:
        Whole nanometres from 350 to 700, the rows of Table 1; a number or
        an array. Nothing is interpolated.
    sun_zenith_deg:
        The sun's zenith angle, degrees, 0 up to but not including 90.
    day_of_year:
        1-366, for the earth's distance from the sun, eq. (12).
    pressure_hpa:
        Air pressure at the surface, hPa (mb).
    air_mass_type:
        1 (open-ocean aerosol) to 10 (continental), eq. (21).
    relative_humidity:
        Percent, 0 up to but not including 100 (eq. 24 divides by zero
        there).
    precipitable_water_cm:
        Total precipitable water vapour, cm.
    wind_speed_24h:
        Wind speed averaged over the previous 24 hours, m/s, eq. (22).
    wind_speed:
        The wind speed now, m/s: the large aerosol particles, eq. (23),
        and the sea surface's reflectance, eqs. (39)-(47).
    ozone_du:
        Total ozone, Dobson units.
    visibility_km, aerosol_optical_thickness_550:
        Exactly one. The paper takes the visibility V and sets tau_a(550)
        = 3.91 / V with a 1 km scale height (eqs. 28, 29); a measured
        tau_a(550) replaces that step and nothing else.

    No input has a default: each describes the sky at one place and time.
    The paper's observations spanned (Table 2, p. 1667) 1002-1019 hPa, air
    mass type 1-10, humidity 46-91 percent, 1.8-4.7 cm of water, mean wind
    1.7-4.2 and wind 0-5.7 m/s, visibility 8-24 km, 263-313 DU and the sun
    29-82 degrees from the zenith; it states no limit beyond which the
    model fails, and nothing here warns.

    Returns
    -------
    SurfaceIrradiance
        In W m-2 nm-1, shaped like ``wavelength_nm``.

    Notes
    -----
    Clouds are not modelled, nor the light reflected between the sea and
    the sky, which the paper drops (p. 1661). Eq. (44) is printed with a
    second 1/2 inside Fresnel's law; it is used without it (DATA.md
    section 35).
    """
    query, index = _wavelength_rows(wavelength_nm)
    theta = _number(sun_zenith_deg, "sun_zenith_deg")
    if not 0 <= theta < 90:
        raise ValueError("sun_zenith_deg must be from 0 up to, not "
                         "including, 90 degrees")
    day = _number(day_of_year, "day_of_year")
    if not 1 <= day <= 366:
        raise ValueError(f"day_of_year must be 1-366, not {day:g}")
    pressure = _number(pressure_hpa, "pressure_hpa")
    if pressure <= 0:
        raise ValueError("pressure_hpa must be positive")
    am = _number(air_mass_type, "air_mass_type")
    if not 1 <= am <= 10:
        raise ValueError(f"air_mass_type must be 1-10, not {am:g}")
    rh = _number(relative_humidity, "relative_humidity")
    if not 0 <= rh < 100:
        raise ValueError("relative_humidity must be from 0 up to, not "
                         "including, 100 percent")
    water = _at_least(precipitable_water_cm, "precipitable_water_cm", 0)
    wind_24h = _at_least(wind_speed_24h, "wind_speed_24h", 0)
    wind = _at_least(wind_speed, "wind_speed", 0)
    ozone = _at_least(ozone_du, "ozone_du", 0)
    if (visibility_km is None) == (aerosol_optical_thickness_550 is None):
        raise TypeError("give exactly one of visibility_km and "
                        "aerosol_optical_thickness_550")
    if visibility_km is not None:
        visibility = _number(visibility_km, "visibility_km")
        if visibility <= 0:
            raise ValueError("visibility_km must be positive")
        tau550 = 3.91 / visibility * _AEROSOL_SCALE_HEIGHT_KM
    else:
        tau550 = _at_least(aerosol_optical_thickness_550,
                           "aerosol_optical_thickness_550", 0)

    _, h0_all, a_oz_all, a_w_all, a_o_all = _data.gregg1990()
    h0, a_oz = h0_all[index], a_oz_all[index]
    a_w, a_o = a_w_all[index], a_o_all[index]
    lam = query / 1000.0

    f0 = h0 * (1 + _ECCENTRICITY * np.cos(2 * np.pi * (day - 3) / 365)) ** 2
    cos_t = np.cos(np.radians(theta))
    m = 1 / (cos_t + 0.15 * (93.885 - theta) ** -1.253)
    m_p = m * pressure / _P0
    m_oz = 1.0035 / (cos_t ** 2 + 0.007) ** 0.5

    t_r = np.exp(-m_p / (115.6406 * lam ** 4 - 1.335 * lam ** 2))
    t_oz = np.exp(-a_oz * (ozone / 1000) * m_oz)
    t_o = np.exp(-1.41 * a_o * m_p / (1 + 118.3 * a_o * m_p) ** 0.45)
    t_w = np.exp(-0.2385 * a_w * water * m
                 / (1 + 20.07 * a_w * water * m) ** 0.45)

    alpha = _angstrom(am, rh, wind_24h, wind)
    beta = tau550 * 0.55 ** alpha
    tau = beta * lam ** -alpha
    t_a = np.exp(-tau * m)
    omega = (-0.0032 * am + 0.972) * np.exp(3.06e-4 * rh)
    t_aa = np.exp(-(1 - omega) * tau * m)
    t_as = np.exp(-omega * tau * m)
    if alpha < 0:
        asymmetry = 0.82
    elif alpha > 1.2:
        asymmetry = 0.65
    else:
        asymmetry = -0.1417 * alpha + 0.82
    b3 = np.log(1 - asymmetry)
    b1 = b3 * (1.459 + b3 * (0.1595 + 0.4129 * b3))
    b2 = b3 * (0.0783 + b3 * (-0.3824 - 0.5874 * b3))
    forward = 1 - 0.5 * np.exp((b1 + b2 * cos_t) * cos_t)

    gases = f0 * cos_t * t_oz * t_o * t_w
    direct = gases * t_r * t_a
    rayleigh = gases * t_aa * (1 - t_r ** 0.95) * 0.5
    aerosol = gases * t_aa * t_r ** 1.5 * (1 - t_as) * forward
    diffuse = rayleigh + aerosol
    rho_d, rho_s = _surface_reflectance(theta, wind)

    return SurfaceIrradiance(
        wavelengths=query,
        direct_above=direct,
        diffuse_above=diffuse,
        direct_below=direct * (1 - rho_d),
        diffuse_below=diffuse * (1 - rho_s),
        angstrom_exponent=alpha,
        aerosol_optical_thickness=tau,
        direct_reflectance=rho_d,
        diffuse_reflectance=rho_s,
    )

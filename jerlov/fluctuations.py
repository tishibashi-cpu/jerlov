"""Measured fluctuations of the light under a wavy surface.

Waves focus and spread the sunlight that crosses the surface, and the light
under it flickers. Two field studies are shipped as they were published,
in figures: Darecki, Stramski & Sokolski (2011), with the fluctuations of
the downwelling irradiance against depth, against wavelength on five days
of different wind, and of the radiance against direction; and Gernez &
Antoine (2009), with those of the irradiance against the sun's zenith
angle, the wave height, the wind and the water's clarity. Neither printed
a table, so the values are read off the figures; DATA.md sections 24 and
25 say how, and how closely.

The package does not model the fluctuations (DECISIONS.md section 42): how
strong they are depends on the wind, the waves, the sky and the size of the
collector, none of which the Jerlov type fixes. These are measurements to
compare with, with the conditions they were made under.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from . import _data

DARECKI2011_PANELS = ("a", "b", "c")
"""The three panels of Darecki et al.'s (2011) Figure 15."""

GERNEZ2009_VARIABLES = ("wave_height_m", "sqrt_wind", "kd490_per_m")
"""What Gernez & Antoine's (2009) Figures 8b, 8c and 8d are plotted
against: the wave height, m; the square root of the wind speed, the wind in
m/s; and Kd at 490 nm, 1/m."""

GERNEZ2009_PLOTS = {
    ("clear", "Ed"): GERNEZ2009_VARIABLES,
    ("overcast", "Ed"): ("sun_zenith_deg", "wave_height_m", "wind_m_s",
                         "kd490_per_m"),
    ("clear", "Eu"): ("sun_zenith_deg", "wave_height_m", "wind_m_s",
                      "kd490_per_m"),
}
"""For each sky and irradiance that Gernez & Antoine (2009) plot against
the conditions, what they plot them against: Figure 8b-d (clear sky,
downwelling), Figure 7 (overcast, downwelling) and Figure 13 (clear sky,
upwelling), all at the upper depth. ``wind_m_s`` is the wind speed itself,
in m/s."""

_FIGURE = {("clear", "Ed"): "8", ("overcast", "Ed"): "7",
           ("clear", "Eu"): "13"}
_SKY = {"clear": ("clear: above-water irradiance at least 0.85 of the "
                  "clear-sky model"),
        "overcast": ("overcast: above-water irradiance below 0.6 of the "
                     "clear-sky model")}


@dataclass(frozen=True, eq=False, repr=False)
class IrradianceFluctuation:
    """Darecki et al.'s (2011) Figure 13a: the coefficient of variation,
    standard deviation over mean, of the downwelling irradiance, sampled at
    1 kHz, at six depths and three wavelengths. Built by
    :func:`darecki2011_irradiance_cv`; ``cv[i, j]`` is at ``depth_m[i]`` and
    ``wavelengths_nm[j]``, a ratio, not a percentage."""

    depth_m: np.ndarray
    wavelengths_nm: np.ndarray
    cv: np.ndarray
    cv_reading: float = 0.0002
    """How closely ``cv`` is read: the axis's own tick marks lie up to
    0.0001 off a straight line, and the values are kept to four places."""
    place: str = ("Santa Barbara Channel, 11 September 2008, "
                  "11:35-12:56 local time")
    sun_zenith_deg: tuple[float, float] = (30.0, 33.0)
    wind_m_s: tuple[float, float] = (4.1, 6.4)
    beam_attenuation_555: float = 0.68
    """c at 555 nm, 1/m, as the caption gives it."""
    collector_mm: float = 2.5
    """The diameter of the irradiance collector (p. 12): larger ones
    average the flashes away and read a smaller CV."""

    def __repr__(self) -> str:
        return (f"<IrradianceFluctuation Darecki 2011, "
                f"{self.depth_m.size} depths {self.depth_m[0]:g}-"
                f"{self.depth_m[-1]:g} m, "
                f"{', '.join(f'{w:g}' for w in self.wavelengths_nm)} nm>")


@dataclass(frozen=True, eq=False, repr=False)
class RadianceFluctuation:
    """One panel of Darecki et al.'s (2011) Figure 15: the coefficient of
    variation of the radiance at 532 nm, at thirteen zenith angles in the
    plane of the sun, positive towards the sun. Built by
    :func:`darecki2011_radiance_cv`."""

    panel: str
    zenith_deg: np.ndarray
    cv: np.ndarray
    place: str
    depth_m: float
    sun_zenith_deg: float
    refracted_sun_zenith_deg: float
    """The mean zenith angle of the sunbeam in the water, as the caption
    gives it."""
    wind_m_s: float
    beam_attenuation_555: float
    cv_reading: float = 0.002
    """How closely ``cv`` is read: the tick marks lie up to 0.001 off a
    straight line."""
    wavelength_nm: float = 532.0
    field_of_view_deg: float = 4.5
    """The radiance sensors' field of view in water (p. 4)."""

    def __repr__(self) -> str:
        return (f"<RadianceFluctuation Darecki 2011 Fig. 15{self.panel}, "
                f"{self.depth_m:g} m, sun {self.sun_zenith_deg:g} deg, "
                f"peak CV {self.cv.max():.2f}>")


@dataclass(frozen=True, eq=False, repr=False)
class SunZenithFluctuation:
    """Gernez & Antoine's (2009) Figure 8a: under clear skies, the median
    coefficient of variation of the downwelling irradiance at 510 nm, its
    standard deviation, and the median period of the strongest
    fluctuation, against the sun's zenith angle. Built by
    :func:`gernez2009_cv_by_sun_zenith`; CV as a ratio."""

    sun_zenith_deg: np.ndarray
    cv: np.ndarray
    cv_sd: np.ndarray
    """The standard deviation of CV among the minutes in each class."""
    tmax_s: np.ndarray
    tmax_reading_s: np.ndarray
    """How closely ``tmax_s`` is read, one or two pixels of the figure."""
    cv_reading: float = 0.0011
    """How closely ``cv`` and ``cv_sd`` are read: one pixel of the
    figure."""
    place: str = "BOUSSOLE buoy, Ligurian Sea"
    wavelength_nm: float = 510.0
    depth_m: tuple[float, float] = (2.7, 3.7)
    """The nominal depth of the upper radiometers, which changed between
    deployments (p. 3)."""
    collector_mm: float = 8.0
    sampling_hz: float = 6.0
    """Fluctuations shorter than a third of a second are not resolved
    (p. 4)."""
    sky: str = ("clear: above-water irradiance at least 0.85 of the "
                "clear-sky model")

    def __repr__(self) -> str:
        return (f"<SunZenithFluctuation Gernez 2009, sun "
                f"{self.sun_zenith_deg[0]:g}-{self.sun_zenith_deg[-1]:g} deg, "
                f"CV {self.cv.max():.1%} to {self.cv.min():.1%}>")


@dataclass(frozen=True, eq=False, repr=False)
class SpectralFluctuation:
    """Darecki et al.'s (2011) Figure 13b: the coefficient of variation of
    the downwelling irradiance at about 1 m, at six wavelengths, on five
    days of different wind. Built by :func:`darecki2011_spectral_cv`;
    ``cv[i, j]`` is at ``wind_m_s[i]`` and ``wavelengths_nm[j]``."""

    wind_m_s: np.ndarray
    wavelengths_nm: np.ndarray
    cv: np.ndarray
    days: tuple[str, ...]
    """The date and local time of each wind's measurement, as the caption
    gives them."""
    cv_reading: float = 0.0002
    place: str = "Santa Barbara Channel, September 2008"
    depth_m: tuple[float, float] = (0.91, 1.25)
    sun_zenith_deg: tuple[float, float] = (42.0, 46.0)
    beam_attenuation_555: tuple[float, float] = (0.55, 0.78)
    collector_mm: float = 2.5

    def __repr__(self) -> str:
        return (f"<SpectralFluctuation Darecki 2011, wind "
                f"{self.wind_m_s[0]:g}-{self.wind_m_s[-1]:g} m/s, "
                f"{self.wavelengths_nm[0]:g}-{self.wavelengths_nm[-1]:g} "
                f"nm>")


@dataclass(frozen=True, eq=False, repr=False)
class ConditionFluctuation:
    """One panel of Gernez & Antoine's (2009) Figures 7, 8 or 13: the
    median coefficient of variation of the irradiance at 510 nm at the
    upper depth, its standard deviation, and the median period of the
    strongest fluctuation, against one of the conditions in
    :data:`GERNEZ2009_PLOTS`. Built by :func:`gernez2009_cv_by`."""

    variable: str
    x: np.ndarray
    """The class, in the unit the variable's name gives."""
    irradiance: str
    """``"Ed"``, downwelling, or ``"Eu"``, upwelling."""
    figure: str
    """The paper's figure: ``"8"``, ``"7"`` or ``"13"``."""
    cv: np.ndarray
    cv_sd: np.ndarray
    """The standard deviation of CV among the minutes in each class; nan
    where the figure's bar cannot be told from the other series'."""
    tmax_s: np.ndarray
    tmax_reading_s: np.ndarray
    cv_reading: float = 0.0011
    place: str = "BOUSSOLE buoy, Ligurian Sea"
    wavelength_nm: float = 510.0
    depth_m: tuple[float, float] = (2.7, 3.7)
    collector_mm: float = 8.0
    sampling_hz: float = 6.0
    sky: str = ("clear: above-water irradiance at least 0.85 of the "
                "clear-sky model")

    def __repr__(self) -> str:
        return (f"<ConditionFluctuation Gernez 2009 Figure {self.figure}, "
                f"{self.irradiance} against {self.variable}, "
                f"{self.x.size} classes>")


def darecki2011_irradiance_cv() -> IrradianceFluctuation:
    """The coefficient of variation of the downwelling irradiance against
    depth, at 443, 532 and 670 nm.

    Darecki, M., Stramski, D. and Sokolski, M. (2011), "Measurements of
    high-frequency light fluctuations induced by sea surface waves with an
    Underwater Porcupine Radiometer System", J. Geophys. Res. 116, C00H09,
    doi:10.1029/2011JC007338, Figure 13a, p. 12.

    Read off the figure's drawing commands, not printed: DATA.md section
    24. The three wavelengths were measured at the same six depths.
    """
    rows = _data._rows("darecki2011_irradiance_cv.csv")
    depths = sorted({float(r["depth_m"]) for r in rows})
    wls = sorted({float(r["wavelength_nm"]) for r in rows})
    cv = np.empty((len(depths), len(wls)))
    for r in rows:
        cv[depths.index(float(r["depth_m"])),
           wls.index(float(r["wavelength_nm"]))] = float(r["cv"])
    return IrradianceFluctuation(depth_m=_data._frozen(np.array(depths)),
                                 wavelengths_nm=_data._frozen(np.array(wls)),
                                 cv=_data._frozen(cv))


_PANELS: dict[str, dict[str, Any]] = {
    "a": dict(place="Santa Barbara Channel, 18 September 2008, 12:20 local "
                    "time", depth_m=0.93, sun_zenith_deg=33.0,
              refracted_sun_zenith_deg=24.0, wind_m_s=7.0,
              beam_attenuation_555=0.65),
    "b": dict(place="Adriatic Sea, 12 June 2009, 09:21", depth_m=0.59,
              sun_zenith_deg=41.0, refracted_sun_zenith_deg=29.0,
              wind_m_s=5.4, beam_attenuation_555=0.31),
    "c": dict(place="Adriatic Sea, 12 June 2009, 09:58", depth_m=0.54,
              sun_zenith_deg=35.0, refracted_sun_zenith_deg=25.0,
              wind_m_s=3.6, beam_attenuation_555=0.31),
}


def darecki2011_radiance_cv(panel: str) -> RadianceFluctuation:
    """The coefficient of variation of the radiance against zenith angle,
    in the plane of the sun, from one panel of Figure 15.

    ``panel`` is one of :data:`DARECKI2011_PANELS`. Darecki et al. (2011),
    as for :func:`darecki2011_irradiance_cv`, Figure 15, p. 14; the
    conditions are the caption's. Read off the figure's drawing commands:
    DATA.md section 24.
    """
    if panel not in _PANELS:
        raise KeyError(f"Figure 15 has no panel {panel!r} (known: "
                       f"{', '.join(DARECKI2011_PANELS)})")
    rows = [r for r in _data._rows("darecki2011_radiance_cv.csv")
            if r["panel"] == panel]
    return RadianceFluctuation(
        panel=panel,
        zenith_deg=_data._frozen(np.array([float(r["zenith_deg"])
                                           for r in rows])),
        cv=_data._frozen(np.array([float(r["cv"]) for r in rows])),
        **_PANELS[panel])


def gernez2009_cv_by_sun_zenith() -> SunZenithFluctuation:
    """The coefficient of variation of the downwelling irradiance at 510 nm,
    and the period of its strongest fluctuation, against the sun's zenith
    angle, under clear skies.

    Gernez, P. and Antoine, D. (2009), "Field characterization of
    wave-induced underwater light field fluctuations", J. Geophys. Res. 114,
    C06025, doi:10.1029/2008JC005059, Figure 8a, p. 9.

    Read off the figure's pixels, not printed: DATA.md section 25. The
    standard deviation of the period is in the figure but cannot be read:
    its dashed bars end between dashes.
    """
    rows = _data._rows("gernez2009_sun_zenith.csv")

    def column(name, scale=1.0):
        return _data._frozen(np.array([float(r[name]) * scale for r in rows]))

    return SunZenithFluctuation(
        sun_zenith_deg=column("sun_zenith_deg"),
        cv=column("cv_percent", 0.01), cv_sd=column("cv_sd_percent", 0.01),
        tmax_s=column("tmax_s"), tmax_reading_s=column("tmax_reading_s"),
        cv_reading=float(rows[0]["cv_reading_percent"]) / 100)


def darecki2011_spectral_cv() -> SpectralFluctuation:
    """The coefficient of variation of the downwelling irradiance against
    wavelength, 410 to 670 nm, at about 1 m on five days of different wind.

    Darecki et al. (2011), as for :func:`darecki2011_irradiance_cv`, Figure
    13b, p. 12; the conditions are the caption's. Read off the figure's
    drawing commands: DATA.md section 24.
    """
    rows = _data._rows("darecki2011_spectral_cv.csv")
    winds = sorted({float(r["wind_m_s"]) for r in rows})
    wls = sorted({float(r["wavelength_nm"]) for r in rows})
    cv = np.empty((len(winds), len(wls)))
    days = {}
    for r in rows:
        w = float(r["wind_m_s"])
        cv[winds.index(w), wls.index(float(r["wavelength_nm"]))] = \
            float(r["cv"])
        days[w] = r["day"]
    return SpectralFluctuation(
        wind_m_s=_data._frozen(np.array(winds)),
        wavelengths_nm=_data._frozen(np.array(wls)),
        cv=_data._frozen(cv), days=tuple(days[w] for w in winds))


def gernez2009_cv_by(variable: str, sky: str = "clear",
                     irradiance: str = "Ed") -> ConditionFluctuation:
    """The coefficient of variation of the irradiance at 510 nm at the upper
    depth, and the period of its strongest fluctuation, against one of the
    conditions: the wave height, the wind, Kd(490) or, for ``sky`` and
    ``irradiance`` other than the defaults, the sun's zenith angle.

    ``sky`` is ``"clear"`` or ``"overcast"`` and ``irradiance`` ``"Ed"`` or
    ``"Eu"``; :data:`GERNEZ2009_PLOTS` gives the variables for each pair
    the paper plots. Gernez & Antoine (2009), as for
    :func:`gernez2009_cv_by_sun_zenith`: Figures 8b-8d (clear, Ed, p. 9), 7
    (overcast, Ed, p. 8) and 13 (clear, Eu, p. 12). Read off the figures'
    pixels: DATA.md section 25. The values are the medians of each class;
    the period's standard deviation is not read, and that of CV only where
    its bar is clear.
    """
    key = (sky, irradiance)
    if key not in GERNEZ2009_PLOTS:
        known = ", ".join(f"{a}/{b}" for a, b in GERNEZ2009_PLOTS)
        raise KeyError(f"the paper plots no {irradiance} under a {sky} sky "
                       f"against the conditions (known: {known})")
    if variable not in GERNEZ2009_PLOTS[key]:
        raise KeyError(f"Figure {_FIGURE[key]} is not plotted against "
                       f"{variable!r} (known: "
                       f"{', '.join(GERNEZ2009_PLOTS[key])})")
    if key == ("clear", "Ed"):
        rows = [r for r in _data._rows("gernez2009_conditions.csv")
                if r["variable"] == variable]
    else:
        rows = [r for r in _data._rows("gernez2009_more_conditions.csv")
                if r["figure"] == _FIGURE[key] and r["variable"] == variable]

    def column(name, scale=1.0):
        return _data._frozen(np.array(
            [float(r[name]) * scale if r[name] else np.nan for r in rows]))

    return ConditionFluctuation(
        variable=variable, x=column("x"), irradiance=irradiance,
        figure=_FIGURE[key], cv=column("cv_percent", 0.01),
        cv_sd=column("cv_sd_percent", 0.01), tmax_s=column("tmax_s"),
        tmax_reading_s=column("tmax_reading_s"),
        cv_reading=float(rows[0]["cv_reading_percent"]) / 100,
        sky=_SKY[sky])


@dataclass(frozen=True, eq=False, repr=False)
class SkySpectralFluctuation:
    """Gernez & Antoine's (2009) Figure 11 (downwelling irradiance, upper
    depth) or 14 (upwelling, lower depth): the average coefficient of
    variation and period of the strongest fluctuation at seven wavelengths,
    under clear and overcast skies. Built by :func:`gernez2009_spectral_cv`;
    ``cv[i, j]`` is for ``skies[i]`` at ``wavelengths_nm[j]``."""

    irradiance: str
    figure: str
    wavelengths_nm: np.ndarray
    cv: np.ndarray
    cv_sd: np.ndarray
    """The standard deviation among the minutes; nan for the overcast sky,
    whose dotted bars are not read."""
    tmax_s: np.ndarray
    tmax_sd_s: np.ndarray
    cv_reading: float
    tmax_reading_s: float
    depth_m: tuple[float, float]
    skies: tuple[str, str] = ("clear", "overcast")
    place: str = "BOUSSOLE buoy, Ligurian Sea"
    collector_mm: float = 8.0
    sampling_hz: float = 6.0

    def __repr__(self) -> str:
        return (f"<SkySpectralFluctuation Gernez 2009 Figure {self.figure}, "
                f"{self.irradiance}, {self.wavelengths_nm[0]:g}-"
                f"{self.wavelengths_nm[-1]:g} nm>")


def gernez2009_spectral_cv(irradiance: str = "Ed") -> SkySpectralFluctuation:
    """The average coefficient of variation and period of the strongest
    fluctuation at 412 to 683 nm, under clear and overcast skies: of the
    downwelling irradiance at the upper depth (``"Ed"``, Figure 11, p. 11)
    or of the upwelling at the lower depth, 8 to 8.7 m (``"Eu"``, Figure 14,
    p. 13).

    Gernez & Antoine (2009), as for :func:`gernez2009_cv_by_sun_zenith`.
    Read off the figures' pixels: DATA.md section 25. The captions call
    these averages, not medians. The overcast standard deviations are
    drawn dotted and not read.
    """
    figure = {"Ed": "11", "Eu": "14"}.get(irradiance)
    if figure is None:
        raise KeyError(f"no spectral figure for {irradiance!r} "
                       f"(known: Ed, Eu)")
    rows = [r for r in _data._rows("gernez2009_spectral.csv")
            if r["figure"] == figure]
    wls = sorted({float(r["wavelength_nm"]) for r in rows})
    skies = ("clear", "overcast")

    def grid(name, scale=1.0):
        out = np.full((2, len(wls)), np.nan)
        for r in rows:
            if r[name]:
                out[skies.index(r["sky"]), wls.index(float(
                    r["wavelength_nm"]))] = float(r[name]) * scale
        return _data._frozen(out)

    return SkySpectralFluctuation(
        irradiance=irradiance, figure=figure,
        wavelengths_nm=_data._frozen(np.array(wls)),
        cv=grid("cv_percent", 0.01), cv_sd=grid("cv_sd_percent", 0.01),
        tmax_s=grid("tmax_s"), tmax_sd_s=grid("tmax_sd_s"),
        cv_reading=float(rows[0]["cv_reading_percent"]) / 100,
        tmax_reading_s=float(rows[0]["tmax_reading_s"]),
        depth_m=(2.7, 3.7) if irradiance == "Ed" else (8.0, 8.7))

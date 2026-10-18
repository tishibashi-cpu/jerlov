"""Measured fluctuations of the light under a wavy surface.

Waves focus and spread the sunlight that crosses the surface, and the light
under it flickers. Two field studies are shipped as they were published,
in figures: Darecki, Stramski & Sokolski (2011), with the fluctuations of
the downwelling irradiance against depth and of the radiance against
direction, and Gernez & Antoine (2009), with those of the irradiance
against the sun's zenith angle. Neither printed a table, so the values are
read off the figures; DATA.md sections 24 and 25 say how, and how
closely.

The package does not model the fluctuations (DECISIONS.md section 42): how
strong they are depends on the wind, the waves, the sky and the size of the
collector, none of which the Jerlov type fixes. These are measurements to
compare with, with the conditions they were made under.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import _data

DARECKI2011_PANELS = ("a", "b", "c")
"""The three panels of Darecki et al.'s (2011) Figure 15."""


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
    """Gernez & Antoine's (2009) Figure 8a: under clear skies, the mean
    coefficient of variation of the downwelling irradiance at 510 nm, its
    standard deviation, and the mean period of the strongest fluctuation,
    against the sun's zenith angle. Built by
    :func:`gernez2009_cv_by_sun_zenith`; CV as a ratio."""

    sun_zenith_deg: np.ndarray
    cv: np.ndarray
    cv_sd: np.ndarray
    """The standard deviation of CV among the minutes averaged."""
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
    sky: str = "clear: above-water irradiance at least 0.85 of the clear-sky model"

    def __repr__(self) -> str:
        return (f"<SunZenithFluctuation Gernez 2009, sun "
                f"{self.sun_zenith_deg[0]:g}-{self.sun_zenith_deg[-1]:g} deg, "
                f"CV {self.cv.max():.1%} to {self.cv.min():.1%}>")


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


_PANELS = {
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

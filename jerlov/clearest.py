"""The clearest natural waters measured: Morel et al. (2007). DECISIONS.md
section 102, DATA.md section 46."""

from __future__ import annotations

from dataclasses import dataclass

from . import _data
from .ocean_colour import _warn


@dataclass(frozen=True)
class ClearWaterStation:
    """One station of Morel et al.'s (2007) Table 1, as printed.

    Observed: chlorophyll a at 5 m and at 30-40 m, the euphotic depth, the
    depth and chlorophyll of the deep maximum, Kd and the particles'
    absorption at 420 and 310 nm, and the largest irradiance reflectance
    below the surface with its wavelength. Derived by the authors: the
    total absorption at 420 and 310 nm, and yellow substance at 310 nm with
    their two pure water absorptions (aw1 and aw2 of their Table 2).
    """

    station: str
    latitude_deg_s: float
    longitude_deg_w: float
    date_2004: str
    chl_5m_mg_m3: float
    chl_30_40m_mg_m3: float
    zeu_m: float
    z_chl_max_m: float
    chl_max_mg_m3: float
    kd_420_per_m: float
    kd_310_per_m: float
    ap_420_per_m: float
    ap_310_per_m: float
    r_max_percent: float
    r_max_nm: float
    atot_420_per_m: float
    atot_310_per_m: float
    ay1_310_per_m: float
    ay2_310_per_m: float
    status: str
    note: str


def morel2007_stations() -> tuple[ClearWaterStation, ...]:
    """The eight stations of the clearest waters Morel et al. (2007)
    measured, in the South Pacific gyre in November 2004.

    Morel, A., Gentili, B., Claustre, H., Babin, M., Bricaud, A., Ras, J.
    and Tièche, F. (2007), "Optical properties of the 'clearest' natural
    waters", Limnol. Oceanogr. 52(1), 217-229,
    doi:10.4319/lo.2007.52.1.0217, Table 1. Their pure water absorption,
    Table 2, is ``pure_water_absorption_table(..., source="morel2007")``.

    Returns
    -------
    A tuple of :class:`ClearWaterStation`, in the table's order.

    Notes
    -----
    At GYR-5 and STB-14 the printed ay2 - ay1 at 310 nm is 0.0082, where it
    should be aw1(310) - aw2(310) = 0.0183 and is 0.0182 at the other six
    stations: one of the two is likely misprinted by 0.0100. They are kept
    as printed, marked ``suspect``, and a :class:`ProvenanceWarning` says
    so. DATA.md section 46.
    """
    out = []
    for r in _data._rows("morel2007_stations.csv"):
        values: dict = {}
        for name, field in ClearWaterStation.__dataclass_fields__.items():
            text = r[name]
            values[name] = text if field.type in ("str", str) else float(text)
        out.append(ClearWaterStation(**values))
    suspect = [s.station for s in out if s.status != "ok"]
    if suspect:
        _warn("in Morel et al.'s (2007) Table 1, ay2 - ay1 at 310 nm is "
              "0.0100 short at " + " and ".join(suspect)
              + "; one of the two is likely misprinted. DATA.md section 46.")
    return tuple(out)

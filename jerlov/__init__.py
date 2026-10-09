"""Inherent optical properties of Jerlov water types.

Every coefficient carries its source, and values that a published table got
wrong are flagged rather than quietly repaired.
"""

from .backscattering import (
    AngleWarning,
    Backscattering,
    bb_from_vsf,
    particulate_chi,
    pure_water_backscattering,
    pure_water_scattering,
    pure_water_vsf,
)
from .colour import (
    CoverageWarning,
    GamutWarning,
    cie_1931_cmf,
    d65,
    integrate_response,
    spectrum_to_srgb,
    spectrum_to_xyz,
    xyz_to_srgb,
)
from .par import (
    PAR_RANGE_NM,
    QUANTA_BAND_NM,
    ParProfile,
    QuantaLevels,
    jerlov1977_quanta,
    par_profile,
)
from .petzold import PETZOLD_STATIONS, ScatteringFunction, petzold_scattering
from .scene import (
    AttenuationCoefficients,
    Observation,
    Scene,
    veiling_radiance_estimate,
)
from .shortwave import (
    ShortwaveParameters,
    jerlov1968_solar_fraction,
    shortwave_parameters,
    solar_fraction,
)
from .sources import SOURCES, Source, get_source
from .water import (
    Descent,
    KdClassification,
    MeasuredPoints,
    MissingQuantityError,
    ProvenanceWarning,
    Water,
    b_from_c,
    classify_kd,
    descend,
    kd_spectrum,
    measured_points,
    profile_depth,
    pure_water_absorption,
    water,
    water_type_at_depth,
)

__all__ = [
    "SOURCES",
    "Scene",
    "Observation",
    "AttenuationCoefficients",
    "veiling_radiance_estimate",
    "spectrum_to_xyz",
    "spectrum_to_srgb",
    "xyz_to_srgb",
    "integrate_response",
    "cie_1931_cmf",
    "d65",
    "GamutWarning",
    "CoverageWarning",
    "Source",
    "get_source",
    "Water",
    "water",
    "water_type_at_depth",
    "descend",
    "profile_depth",
    "Descent",
    "classify_kd",
    "KdClassification",
    "par_profile",
    "ParProfile",
    "PAR_RANGE_NM",
    "jerlov1977_quanta",
    "QuantaLevels",
    "QUANTA_BAND_NM",
    "pure_water_absorption",
    "petzold_scattering",
    "PETZOLD_STATIONS",
    "ScatteringFunction",
    "shortwave_parameters",
    "solar_fraction",
    "jerlov1968_solar_fraction",
    "bb_from_vsf",
    "particulate_chi",
    "pure_water_vsf",
    "pure_water_backscattering",
    "pure_water_scattering",
    "Backscattering",
    "AngleWarning",
    "ShortwaveParameters",
    "kd_spectrum",
    "b_from_c",
    "measured_points",
    "MeasuredPoints",
    "ProvenanceWarning",
    "MissingQuantityError",
]

__version__ = "0.9.5"

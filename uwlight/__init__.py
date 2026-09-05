"""Inherent optical properties of Jerlov water types.

Every coefficient carries its source, and values that a published table got
wrong are flagged rather than quietly repaired.
"""

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
from .scene import Observation, Scene, veiling_radiance_estimate
from .sources import SOURCES, Source, get_source
from .water import (
    MissingQuantityError,
    ProvenanceWarning,
    Water,
    b_from_c,
    kd_spectrum,
    water,
)

__all__ = [
    "SOURCES",
    "Scene",
    "Observation",
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
    "kd_spectrum",
    "b_from_c",
    "ProvenanceWarning",
    "MissingQuantityError",
]

__version__ = "0.0.1.dev0"

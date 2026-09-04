"""Inherent optical properties of Jerlov water types.

Every coefficient carries its source, and values that a published table got
wrong are flagged rather than quietly repaired.
"""

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

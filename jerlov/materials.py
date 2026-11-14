"""Measured reflectances of ten materials: the USGS Spectral Library.

    Kokaly, R. F., Clark, R. N., Swayze, G. A., Livo, K. E., Hoefen, T. M.,
    Pearson, N. C., Wise, R. A., Benzel, W. M., Lowers, H. A., Driscoll,
    R. L., and Klein, A. J. (2017), USGS Spectral Library Version 7 Data,
    U.S. Geological Survey data release, doi:10.5066/F7RR1WDJ (CC0 1.0).
    Report: USGS Data Series 1035, doi:10.3133/ds1035.

Ten materials found in and around water, chosen to span neutral and hue
(DECISIONS.md section 85): white, black and grey, and seven colours. Each
is the library's ASD spectrometer record of absolute reflectance, as
measured, at every nm from 350 to 830 (DATA.md section 37). They are
these particular samples, measured in a laboratory, dry; a wet surface,
or another sample of the same kind of material, reflects differently.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import _data

CITATION = (
    "Kokaly, R. F. and others (2017), 'USGS Spectral Library Version 7 "
    "Data', U.S. Geological Survey data release, doi:10.5066/F7RR1WDJ "
    "(CC0 1.0); USGS Data Series 1035, doi:10.3133/ds1035"
)

#: The library's record for each material: its record number and the
#: name the ASCII file prints, ``ASDFRa AREF`` being the ASD's absolute
#: reflectance.
_RECORDS = {
    "white_pvc": (19775, "Plastic_PVC GDS338 White"),
    "black_abs": (19559, "Plastic_ABS GDS341 BlackPipe"),
    "grey_concrete": (18568, "Concrete GDS375 Lt Gry Road"),
    "red_nylon": (19080, "Nylon_Fabric GDS431 Red RpSt"),
    "orange_cadmium": (18413, "Cadmium_orange_0 GDS786"),
    "yellow_cadmium": (18440, "Cadmium_yellow_6 med GDS788"),
    "green_tarp": (19802, "Plastic_Tarp GDS339 Green"),
    "blue_green_hdpe": (19577, "Plastic_HDPE GDS391 Blu-Grn"),
    "blue_nylon": (19098, "Nylon_Fabric GDS433 Blu RpSt"),
    "violet_cobalt": (18485, "Cobalt_violet GDS803"),
}

#: The ten materials, neutral first, then by hue from red to violet.
USGS2017_MATERIALS = tuple(_RECORDS)


@_data.compared_by_value
@dataclass(frozen=True, eq=False)
class MeasuredReflectance:
    """One material's reflectance, as the USGS Spectral Library measured
    it."""

    material: str
    """The key, one of :data:`USGS2017_MATERIALS`."""
    record: int
    """The library's record number (splib07a)."""
    sample: str
    """The sample's name as the library's ASCII file prints it."""
    wavelengths: np.ndarray
    """350 to 830 nm, every nm: the ASD's channels, each with a bandpass
    of 3.4 to 8.7 nm (FWHM) in this range."""
    reflectance: np.ndarray
    """Absolute reflectance, 0 to 1: relative to a Spectralon panel, times
    the panel's own reflectance (Data Series 1035, eq. 1, p. 4)."""
    citation: str = CITATION

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return (f"<MeasuredReflectance {self.material}: {self.sample}, "
                f"record {self.record}>")


def usgs2017_reflectance(material: str) -> MeasuredReflectance:
    """The measured reflectance of one of ten materials.

    ``material`` is one of :data:`USGS2017_MATERIALS`: ``"white_pvc"``,
    ``"black_abs"``, ``"grey_concrete"``, ``"red_nylon"``,
    ``"orange_cadmium"``, ``"yellow_cadmium"``, ``"green_tarp"``,
    ``"blue_green_hdpe"``, ``"blue_nylon"``, ``"violet_cobalt"``. The
    three ``cadmium`` and ``cobalt`` entries are artists' pigments.

    The values are the library's, at its own wavelengths. Interpolating
    them onto another grid is the caller's choice, as for any spectrum in
    this package; they were measured with a bandpass of a few nm, so
    finer structure is not in them.
    """
    if material not in _RECORDS:
        raise KeyError(
            f"unknown material {material!r}; the materials are "
            f"{', '.join(USGS2017_MATERIALS)}")
    rows = [r for r in _data._rows("usgs2017_reflectance.csv")
            if r["material"] == material]
    wavelengths = np.array([float(r["wavelength_nm"]) for r in rows])
    reflectance = np.array([float(r["reflectance"]) for r in rows])
    for array in (wavelengths, reflectance):
        array.setflags(write=False)
    record, sample = _RECORDS[material]
    return MeasuredReflectance(material=material, record=record,
                               sample=sample, wavelengths=wavelengths,
                               reflectance=reflectance)

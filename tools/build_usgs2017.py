"""Build jerlov/data/usgs2017_reflectance.csv from the USGS Spectral Library.

Kokaly, R. F. and others (2017), USGS Spectral Library Version 7 Data,
U.S. Geological Survey data release, DOI 10.5066/F7RR1WDJ (CC0 1.0); report
USGS Data Series 1035, DOI 10.3133/ds1035. From ASCIIdata_splib07a.zip, the
spectra as measured, ten records of the ASD spectrometer's absolute
reflectance ("ASDFRa AREF"), 350-830 nm (DECISIONS.md section 85, DATA.md
section 37).

The values are copied as the library prints them, in a shorter wavelength
range; nothing else is changed. Every check below must pass before the file
is written.
"""

from __future__ import annotations

import csv
import io
import zipfile

from _common import DATA_DIR, report, require

ORIGIN = (
    "USGS ScienceBase, 'USGS Spectral Library Version 7 Data', DOI\n"
    "  10.5066/F7RR1WDJ: the child item 'Spectra of materials in ASCII\n"
    "  format', file ASCIIdata_splib07a.zip (21,812,828 bytes)."
)
ZIP = "usgs2017/ASCIIdata_splib07a.zip"
PREFIX = "ASCIIdata_splib07a/"
WAVELENGTHS = PREFIX + "splib07a_Wavelengths_ASD_0.35-2.5_microns_2151_ch.txt"
BANDPASS = PREFIX + "splib07a_Bandpass_(FWHM)_ASDFR_StandardResolution.txt"

#: The key the package uses, the file, and the record line the file must
#: start with, as the library prints it.
MATERIALS = (
    ("white_pvc", "ChapterA_ArtificialMaterials/"
     "splib07a_Plastic_PVC_GDS338_White_ASDFRa_AREF.txt",
     "splib07a Record=19775: Plastic_PVC GDS338 White     ASDFRa AREF"),
    ("black_abs", "ChapterA_ArtificialMaterials/"
     "splib07a_Plastic_ABS_GDS341_BlackPipe_ASDFRa_AREF.txt",
     "splib07a Record=19559: Plastic_ABS GDS341 BlackPipe ASDFRa AREF"),
    ("grey_concrete", "ChapterA_ArtificialMaterials/"
     "splib07a_Concrete_GDS375_Lt_Gry_Road_ASDFRa_AREF.txt",
     "splib07a Record=18568: Concrete GDS375 Lt Gry Road  ASDFRa AREF"),
    ("red_nylon", "ChapterA_ArtificialMaterials/"
     "splib07a_Nylon_Fabric_GDS431_Red_RpSt_ASDFRa_AREF.txt",
     "splib07a Record=19080: Nylon_Fabric GDS431 Red RpSt ASDFRa AREF"),
    ("orange_cadmium", "ChapterA_ArtificialMaterials/"
     "splib07a_Cadmium_orange_0_GDS786_ASDFRa_AREF.txt",
     "splib07a Record=18413: Cadmium_orange_0 GDS786      ASDFRa AREF"),
    ("yellow_cadmium", "ChapterA_ArtificialMaterials/"
     "splib07a_Cadmium_yellow_6_med_GDS788_ASDFRa_AREF.txt",
     "splib07a Record=18440: Cadmium_yellow_6 med GDS788  ASDFRa AREF"),
    ("green_tarp", "ChapterA_ArtificialMaterials/"
     "splib07a_Plastic_Tarp_GDS339_Green_ASDFRa_AREF.txt",
     "splib07a Record=19802: Plastic_Tarp GDS339 Green    ASDFRa AREF"),
    ("blue_green_hdpe", "ChapterA_ArtificialMaterials/"
     "splib07a_Plastic_HDPE_GDS391_Blu-Grn_ASDFRa_AREF.txt",
     "splib07a Record=19577: Plastic_HDPE GDS391 Blu-Grn  ASDFRa AREF"),
    ("blue_nylon", "ChapterA_ArtificialMaterials/"
     "splib07a_Nylon_Fabric_GDS433_Blu_RpSt_ASDFRa_AREF.txt",
     "splib07a Record=19098: Nylon_Fabric GDS433 Blu RpSt ASDFRa AREF"),
    ("violet_cobalt", "ChapterA_ArtificialMaterials/"
     "splib07a_Cobalt_violet_GDS803_ASDFRa_AREF.txt",
     "splib07a Record=18485: Cobalt_violet GDS803         ASDFRa AREF"),
)
#: The channels kept: 350 to 830 nm, the first 481 of the ASD's 2151.
KEEP = 481
#: The library's marker for a deleted channel (DS 1035).
DELETED = -1.23e34


def lines(archive: zipfile.ZipFile, name: str) -> list[str]:
    with archive.open(name) as handle:
        return io.TextIOWrapper(handle, encoding="ascii").read().splitlines()


def main() -> None:
    path = require(ZIP, ORIGIN)
    with zipfile.ZipFile(path) as archive:
        wl_lines = lines(archive, WAVELENGTHS)
        bp_lines = lines(archive, BANDPASS)
        wavelengths = [float(v) * 1000 for v in wl_lines[1:]]
        bandpass = [float(v) * 1000 for v in bp_lines[1:]]
        assert len(wavelengths) == len(bandpass) == 2151
        # The ASD's channels are every nm from 350 to 2500, printed in
        # microns to single precision.
        for k, w in enumerate(wavelengths):
            assert abs(w - (350 + k)) < 1e-3, (k, w)
        kept_bp = bandpass[:KEEP]
        print(f"channels 350-830 nm: bandpass {min(kept_bp):.2f}-"
              f"{max(kept_bp):.2f} nm FWHM")
        rows = []
        for key, member, header in MATERIALS:
            text = lines(archive, PREFIX + member)
            assert text[0].strip() == header.strip(), (key, text[0])
            values = text[1:]
            assert len(values) == 2151, (key, len(values))
            kept = values[:KEEP]
            numbers = [float(v) for v in kept]
            assert all(v > DELETED / 10 for v in numbers), key
            assert all(0 < v < 1 for v in numbers), (key, min(numbers),
                                                     max(numbers))
            print(f"{key:16s} {header.split(':')[0]}  "
                  f"{min(numbers):.4f}-{max(numbers):.4f}")
            for k, text_value in enumerate(kept):
                # The value as printed, without reformatting.
                rows.append([key, 350 + k, text_value.strip(), "ok", ""])
    out = DATA_DIR / "usgs2017_reflectance.csv"
    with open(out, "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["material", "wavelength_nm", "reflectance",
                         "status", "note"])
        writer.writerows(rows)
    report(out.name, len(rows))


if __name__ == "__main__":
    main()

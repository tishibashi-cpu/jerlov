"""Extract the CIE colorimetric reference data.

The CIE 1931 2-degree colour matching functions and the D65 illuminant are
standard reference data, not something this project measured or can derive.
They are transcribed here from `colour-science`, which is a convenient and
widely used carrier; the underlying values are the CIE tabulations.

`colour-science` is needed to run this script and is not a dependency of the
package.
"""

import csv
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import DATA_DIR, report

try:
    import colour
except ImportError:
    print(
        "this script needs colour-science:\n"
        "  pip install colour-science\n"
        "It is a build-time dependency only; the package itself does not use it.",
        file=sys.stderr,
    )
    raise SystemExit(1)

CMF_NAME = "CIE 1931 2 Degree Standard Observer"
cmfs = colour.MSDS_CMFS[CMF_NAME]
wavelengths = np.asarray(cmfs.wavelengths, dtype=float)
values = np.asarray(cmfs.values, dtype=float)

# Sanity: y-bar integrates to the same as x-bar and z-bar by construction of
# the 1931 observer, to within the rounding of the published table.
totals = values.sum(axis=0)
print(f"check: sums of xbar, ybar, zbar = {np.round(totals, 3)}")
assert abs(totals[0] - totals[1]) / totals[1] < 0.01, "xbar and ybar disagree"
assert abs(totals[2] - totals[1]) / totals[1] < 0.02, "zbar and ybar disagree"

# Sanity: ybar peaks at 555 nm, the definition of the photopic maximum.
peak = float(wavelengths[np.argmax(values[:, 1])])
print(f"check: ybar peaks at {peak:g} nm (expected 555)")
assert peak == 555.0, f"ybar peaks at {peak} nm"

path = DATA_DIR / "cie1931_2deg_cmf.csv"
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["wavelength_nm", "x_bar", "y_bar", "z_bar"])
    for i, nm in enumerate(wavelengths):
        writer.writerow([f"{nm:g}"] + [f"{v:.6g}" for v in values[i]])
report("cie1931_2deg_cmf.csv", len(wavelengths))

d65 = colour.SDS_ILLUMINANTS["D65"]
d65_wl = np.asarray(d65.wavelengths, dtype=float)
d65_values = np.asarray(d65.values, dtype=float)

# Sanity: the relative SPD is normalised to 100 at 560 nm.
at560 = float(d65_values[np.argmin(np.abs(d65_wl - 560))])
print(f"check: D65 relative power at 560 nm = {at560:g} (expected 100)")
assert abs(at560 - 100.0) < 0.5, f"D65 is not normalised at 560 nm: {at560}"

path = DATA_DIR / "cie_d65.csv"
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["wavelength_nm", "relative_spectral_power"])
    for nm, value in zip(d65_wl, d65_values):
        writer.writerow([f"{nm:g}", f"{value:.6g}"])
report("cie_d65.csv", len(d65_wl))

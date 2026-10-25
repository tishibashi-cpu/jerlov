"""Blue attenuation by layer at the IB-like stations, from Smith's spectra.

The analysis of DECISIONS.md section 56: does Kd at 465-505 nm, where most
of the quanta deep in IB water lie, rise with depth at the stations whose
quanta profiles were IB-like in section 55?

    python tools/smith1973_blue.py

`smith1973_blue.csv`, beside this script, is the downwelling spectral
irradiance (microwatts cm-2 nm-1) printed at 465-505 nm for stations 3, 12
and 15, read from the page images; a wavelength scanned twice has two rows.
Station 3 was measured in clear weather and gives 469 to 498 nm; 12 and 15
were normalised to the deck monitor in variable weather and give 479 and
498 nm only. The table is not part of the package.

    Smith, R. C. (1973), Scripps spectroradiometer data, in Tyler, J. E.
    (ed.), Data Report, SCOR Discoverer Expedition, May 1970, vol. II,
    section G, SIO Ref. 73-16, Visibility Laboratory, Scripps Institution
    of Oceanography.
"""

from __future__ import annotations

import csv
import math
import pathlib

TABLE = pathlib.Path(__file__).resolve().parent / "smith1973_blue.csv"
#: The blue Kd of the deepest layer over the shallowest's above which it
#: rises with depth at a station.
RISES = 1.2


def read(path=TABLE) -> dict[int, dict[float, dict[int, float]]]:
    """station -> depth -> wavelength -> mean ln E."""
    logs: dict[int, dict[float, dict[int, list[float]]]] = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            (logs.setdefault(int(r["station"]), {})
                 .setdefault(float(r["depth_m"]), {})
                 .setdefault(int(r["wavelength_nm"]), [])
                 .append(math.log(float(r["irradiance"]))))
    return {s: {z: {w: sum(v) / len(v) for w, v in by_w.items()}
                for z, by_w in by_z.items()}
            for s, by_z in logs.items()}


def layers(depths: dict[float, dict[int, float]], wavelengths=None):
    """(top, bottom, wavelengths, blue Kd) for each pair of depths."""
    zs = sorted(depths)
    out = []
    for top, bottom in zip(zs, zs[1:]):
        common = sorted(set(depths[top]) & set(depths[bottom]))
        if wavelengths is not None:
            common = [w for w in common if w in wavelengths]
        kd = [(depths[top][w] - depths[bottom][w]) / (bottom - top)
              for w in common]
        out.append((top, bottom, common, sum(kd) / len(kd)))
    return out


def main() -> None:
    import numpy as np

    import jerlov

    ib = jerlov.water("IB", source="jerlov1976")
    rising = 0
    for station, depths in sorted(read().items()):
        found = layers(depths)
        for top, bottom, common, kd in found:
            jerlov_ib = float(np.mean(ib.kd(np.array(common, dtype=float))))
            print(f"station {station:2d} {top:5.1f}-{bottom:5.1f} m: "
                  f"blue Kd {kd:.4f} 1/m, {kd / jerlov_ib:.2f} x Jerlov IB")
        ratio = found[-1][3] / found[0][3]
        rising += ratio > RISES
        print(f"  deepest over shallowest: {ratio:.2f}")
    print(f"rises at {rising} of 3 stations")


if __name__ == "__main__":
    main()

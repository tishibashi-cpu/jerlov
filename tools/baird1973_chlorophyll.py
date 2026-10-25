"""Chlorophyll in Smith's shallowest and deepest layers at the IB-like stations.

Test B of DECISIONS.md section 58: did chlorophyll rise with depth where
the blue light's Kd did (section 56)?

    python tools/baird1973_chlorophyll.py

`baird1973_chlorophyll.csv`, beside this script, is the routine
fluorometric chlorophyll a (mg m-3) of stations 3, 12 and 15, read from the
page images of Table I; two samples at a depth have two rows. The 3 m
samples filtered from 1 litre at station 12 are a different series and are
left out. The table is not part of the package.

    Baird, I. E. (1973), Chlorophyll a and phaeopigments, in Tyler, J. E.
    (ed.), Data Report, SCOR Discoverer Expedition, May 1970, vol. I,
    section C, SIO Ref. 73-16, Visibility Laboratory, Scripps Institution
    of Oceanography.
"""

from __future__ import annotations

import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import smith1973_blue  # noqa: E402

TABLE = pathlib.Path(__file__).resolve().parent / "baird1973_chlorophyll.csv"
RISES = 1.2


def read(path=TABLE) -> dict[int, list[tuple[float, float]]]:
    out: dict[int, list[tuple[float, float]]] = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            out.setdefault(int(r["station"]), []).append(
                (float(r["depth_m"]), float(r["chlorophyll_a_mg_m3"])))
    return out


def in_layer(samples, top, bottom):
    """The mean of the samples within the layer, None if there are none."""
    values = [c for z, c in samples if top <= z <= bottom]
    return sum(values) / len(values) if values else None


def compare():
    """station -> (shallowest mean, deepest mean), from Smith's layers."""
    chlorophyll = read()
    out = {}
    for station, depths in smith1973_blue.read().items():
        layers = smith1973_blue.layers(depths)
        shallow = in_layer(chlorophyll[station], layers[0][0], layers[0][1])
        deep = in_layer(chlorophyll[station], layers[-1][0], layers[-1][1])
        out[station] = (shallow, deep)
    return out


def main() -> None:
    for station, (shallow, deep) in sorted(compare().items()):
        if shallow is None or deep is None:
            print(f"station {station}: a layer has no sample; not counted "
                  f"(shallowest {shallow}, deepest {deep})")
        else:
            print(f"station {station}: {shallow:.3f} -> {deep:.3f} mg m-3, "
                  f"{deep / shallow:.2f} times")


if __name__ == "__main__":
    main()

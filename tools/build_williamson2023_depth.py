"""Derive the typical depth profiles of Williamson & Hollins (2023) Table 2.

The dataset gives, for every 10 m layer down to 200 m, how many measurement
campaigns classified as each Jerlov type, cross-tabulated against the type
that was seen in the top 10 m. The published table takes, for each
near-surface type and layer, the deeper type with the largest campaign count.

The paper notes that in 3 of 119 cases it chose the second-highest count
instead, "as this count was close to the maximum and more consistent with the
surrounding depth layers". Those three are hard-coded below and checked: the
derivation must disagree with the published table at exactly those cells and
nowhere else.
"""

import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import DATA_DIR, require, report

FIGSHARE_DEPTH = (
    "figshare DOI 10.6084/m9.figshare.21710252\n"
    "  Williamson, C. A. and Hollins, R. C. (2023), 'Dataset to accompany\n"
    "  paper: Depth profiles of Jerlov water types'.\n"
    "  Crown copyright, Dstl. Open Government Licence v3.0.\n"
    "  NOTE: the Data Availability Statement of the paper gives\n"
    "  10.6084/m9.figshare.24128862, which is a different dataset entirely\n"
    "  (lake locations in the United States). Use the DOI above, which is\n"
    "  the one in the paper's reference list. See DATA.md section 13."
)

# Column prefixes in the dataset, in the order the paper uses.
LABEL = {"a_I": "I", "b_IA": "IA", "c_IB": "IB", "d_II": "II", "e_III": "III",
         "f_1C": "1C", "g_3C": "3C", "h_5C": "5C", "i_7C": "7C", "j_9C": "9C"}
TYPES = list(LABEL.values())

#: The paper's three documented departures from "take the largest count",
#: keyed by (near-surface type, layer) and giving the type it published.
SECOND_HIGHEST = {
    ("I", "90-100"): "IB",
    ("I", "180-190"): "IB",
    ("IA", "190-200"): "IB",
}

#: A declaration needs at least this many campaigns behind it.
MINIMUM_CAMPAIGNS = 10

rows = list(csv.DictReader(open(require("21710252/op_STEP_6_FINAL.csv",
                                        FIGSHARE_DEPTH))))
layers = []
for r in rows:
    if r["Layer"] not in layers:
        layers.append(r["Layer"])
# The dataset carries a catch-all layer beyond 200 m; the paper stops there.
layers = [x for x in layers if "10000000" not in x]

out = []
departures = []
for surface in TYPES:
    # By definition the near-surface layer is the type itself.
    out.append([surface, 0, 10, surface, "", "identity",
                "the near-surface layer defines the type"])
    for layer in layers:
        low, high = (int(v) for v in layer.split("-"))
        counts = {
            LABEL[r["Jerlov"]]: int(r[f"{surface}_cmp"])
            for r in rows if r["Layer"] == layer
        }
        largest = max(counts, key=counts.get)
        published = SECOND_HIGHEST.get((surface, layer))

        if counts[largest] < MINIMUM_CAMPAIGNS:
            out.append([surface, low, high, "", "", "undeclared",
                        f"fewer than {MINIMUM_CAMPAIGNS} campaigns "
                        f"({counts[largest]}); the paper leaves this blank"])
            continue

        if published is not None:
            departures.append((surface, layer, largest, published))
            out.append([surface, low, high, published, counts[published],
                        "second_highest",
                        f"the paper chose this over {largest} "
                        f"({counts[largest]} campaigns) as being closer to the "
                        "surrounding layers"])
        else:
            out.append([surface, low, high, largest, counts[largest], "ok", ""])

print(f"check: {len(layers)} layers of 10 m from 0 to 200 m")
print(f"check: departures from 'largest count' = {len(departures)}, "
      f"the paper states 3")
for surface, layer, largest, published in departures:
    print(f"    {surface:>3} at {layer:>8} m: largest {largest}, "
          f"published {published}")
if len(departures) != 3:
    raise SystemExit(f"expected 3 departures, found {len(departures)}")

path = DATA_DIR / "williamson2023_depth.csv"
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["surface_water_type", "depth_min_m", "depth_max_m",
                     "water_type", "n_campaigns", "status", "note"])
    writer.writerows(out)
report("williamson2023_depth.csv", len(out))

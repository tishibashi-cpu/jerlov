"""The IOPs of Lee et al.'s (1998) HydroLight runs, rebuilt: DECISIONS.md
section 114, step 1.

Lee, Z., Carder, K. L., Mobley, C. D., Steward, R. G. and Patch, J. S.
(1998), Appl. Opt. 37(27), 6329-6338, doi:10.1364/AO.37.006329, Table 1
and Eqs. (12)-(15), p. 6331:

- chlorophyll 0.4, 1, 2 and 5 mg/m3; ag(440) 0.05, 0.1 and 0.3 1/m; B 0.3,
  1 and 5; 400-700 nm every 20 nm;
- af(lambda) = (a0(lambda) + a1(lambda) ln af(440)) af(440), Eq. (12), with
  Table 2's a0 and a1, and af(440) = 0.06 [chl]^0.65, Eq. (13);
- ag(lambda) = ag(440) exp(-0.014 (lambda - 440)), Eq. (14);
- bp(lambda) = B [chl]^0.62 550 / lambda, Eq. (15);
- pure water's absorption from Pope & Fry and pure sea water's scattering
  from Morel (the package's `pure_water_absorption_table(...,
  source="pope1997")` and `pure_water_scattering`, at 35 psu, a choice:
  the paper gives no salinity);
- bbp = 0.019 bp, the average particle phase function's 1.9 percent
  (p. 6332), and bbw = bw / 2.

    python tools/lee1998_runs.py OUT.csv

writes one row per chlorophyll, ag(440), B and wavelength (576 rows).
"""

from __future__ import annotations

import csv
import itertools
import sys

import numpy as np

import jerlov

#: Table 2 (p. 6331), read from the page image: a0 and a1 at the
#: wavelengths of Table 1.
TABLE2 = {
    400: (0.6843, 0.0205), 420: (0.8637, 0.006), 440: (1.0, 0.0),
    460: (0.9311, 0.0109), 480: (0.789, 0.0152), 500: (0.7333, 0.0559),
    520: (0.6327, 0.0981), 540: (0.5046, 0.09), 560: (0.3433, 0.0659),
    580: (0.2784, 0.0581), 600: (0.2389, 0.0495), 620: (0.3197, 0.0674),
    640: (0.3331, 0.0685), 660: (0.561, 0.1128), 680: (0.7485, 0.1388),
    700: (0.136, 0.0317),
}
CHL = (0.4, 1.0, 2.0, 5.0)
AG440 = (0.05, 0.1, 0.3)
B = (0.3, 1.0, 5.0)
BBP_RATIO = 0.019
SALINITY_PSU = 35.0


def rows():
    wl = np.array(sorted(TABLE2), dtype=float)
    aw = np.asarray(jerlov.pure_water_absorption_table(wl, source="pope1997"))
    bw = np.asarray(jerlov.pure_water_scattering(wl,
                                                 salinity_psu=SALINITY_PSU))
    out = []
    for chl, ag440, b in itertools.product(CHL, AG440, B):
        af440 = 0.06 * chl ** 0.65
        for i, lam in enumerate(wl):
            a0, a1 = TABLE2[int(lam)]
            af = (a0 + a1 * np.log(af440)) * af440
            ag = ag440 * np.exp(-0.014 * (lam - 440.0))
            a = aw[i] + af + ag
            bp = b * chl ** 0.62 * 550.0 / lam
            bb = bw[i] / 2 + BBP_RATIO * bp
            out.append({
                "chl_mg_m3": chl, "ag440": ag440, "B": b,
                "wavelength_nm": int(lam),
                "a": f"{a:.6g}", "bp": f"{bp:.6g}", "bw": f"{bw[i]:.6g}",
                "bb": f"{bb:.6g}", "u": f"{bb / (a + bb):.6g}",
                "water_share": f"{bw[i] / 2 / bb:.6g}",
            })
    return out


def main(path: str) -> None:
    data = rows()
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])

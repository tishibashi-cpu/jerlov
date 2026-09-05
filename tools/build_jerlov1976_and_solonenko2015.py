# -*- coding: utf-8 -*-
"""Build the Jerlov (1976) and Solonenko & Mobley (2015) tables.

The Jerlov Kd spectra are taken from the Dstl dataset. The Solonenko & Mobley
coefficients are transcribed literals below, checked against that paper's own
equations before anything is written; the duplicated rows in its Table 7 were
found by exactly these checks.
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import DATA_DIR, require, report


import csv, numpy as np

WL = [300,310,350,375,400,425,450,475,500,525,550,575,600,625,650,675,700]
N = None  # a published value that is wrong and is not used

# --- Solonenko & Mobley (2015) Table 4-8 : Kd0, Kd, KdH, a, b -----------------
SM = {
"I":  [(0.173,0.186,0.200,0.163,2.08e-2),(0.151,0.154,0.167,0.134,1.81e-2),
       (0.0619,0.059,0.063,0.048,1.08e-2),(0.0377,0.038,0.040,0.030,8.11e-3),
       (0.0284,0.028,0.029,0.022,6.20e-3),(0.0222,0.022,0.023,0.017,4.82e-3),
       (0.0192,0.022,0.023,0.018,3.81e-3),(0.0182,0.021,0.023,0.019,3.06e-3),
       (0.0284,0.029,0.030,0.026,2.49e-3),(0.0398,0.049,0.051,0.046,2.05e-3),
       (0.0598,0.065,0.068,0.062,1.70e-3),(0.0834,0.085,0.089,0.082,1.43e-3),
       (0.163,0.233,0.242,0.228,1.22e-3),(0.301,0.302,0.312,0.295,1.04e-3),
       (0.357,0.341,0.359,0.334,8.99e-4),(0.416,0.444,0.471,0.434,7.82e-4),
       (0.528,0.595,0.653,0.582,6.85e-4)],
"IA": [(0.223,0.241,0.266,0.221,2.55e-2),(0.186,0.199,0.218,0.181,2.26e-2),
       (0.078,0.0776,0.085,0.0673,1.45e-2),(0.050,0.0490,0.053,0.0413,1.14e-2),
       (0.0377,0.0356,0.038,0.0295,9.20e-3),(0.0294,0.0274,0.029,0.0225,7.55e-3),
       (0.0263,0.0264,0.027,0.0221,6.31e-3),(0.0253,0.0253,0.026,0.0216,5.36e-3),
       (0.0346,0.0316,0.033,0.0282,4.61e-3),(0.0460,0.0503,0.052,0.0468,4.02e-3),
       (0.0661,0.0658,0.068,0.0622,3.54e-3),(0.0943,0.0858,0.089,0.0821,3.15e-3),
       (0.174,0.234,0.242,0.228,2.83e-3),(0.308,0.303,0.312,0.295,2.56e-3),
       (0.364,0.342,0.359,0.334,2.34e-3),(0.423,0.445,0.471,0.435,2.14e-3),
       (0.536,0.595,0.653,0.582,1.98e-3)],
"IB": [(0.288,0.301,0.333,0.273,0.125),(0.223,0.246,0.271,0.221,0.118),
       (0.0998,0.0986,0.106,0.0810,0.0968),(0.0619,0.0629,0.065,0.0481,0.0872),
       (0.0460,0.0460,0.046,0.0331,0.0795),(0.0367,0.0360,0.035,0.0246,0.0732),
       (0.0336,0.0342,0.032,0.0235,0.0680),(0.0325,0.0325,0.030,0.0225,0.0635),
       (0.0408,0.0386,0.036,0.0287,0.0597),(0.0513,0.0572,0.056,0.0469,0.0565),
       (0.0726,0.0726,0.072,0.0623,0.0536),(0.0998,0.0926,0.093,0.0822,0.0511),
       (0.186,0.241,0.248,0.2278,0.0488),(0.315,0.310,0.319,0.296,0.0468),
       (0.371,0.349,0.364,0.334,0.0450),(0.431,0.452,0.475,0.435,0.0434),
       (0.545,0.602,0.653,0.582,0.0420)],
"II": [(0.439,0.464,0.475,0.343,1.014),(0.371,0.384,0.393,0.273,0.957),
       (0.174,0.171,0.163,0.095,0.776),(0.116,0.114,0.100,0.0540,0.689),
       (0.0834,0.0846,0.071,0.0355,0.616),(0.0672,0.0671,0.053,0.0257,0.555),
       (0.0619,0.0620,0.048,0.0241,0.504),(0.0619,0.0579,0.044,0.0228,0.459),
       (0.0672,0.0641,0.050,0.0288,0.421),(0.0780,0.0845,0.070,0.0469,0.387),
       (0.0998,0.0999,0.085,0.0622,0.358),(0.134,0.120,0.107,0.0821,0.332),
       (0.223,0.270,0.261,0.228,0.309),(0.342,0.337,0.339,0.296,0.288),
       (0.393,0.375,0.389,0.334,0.270),(0.454,0.476,0.494,0.436,0.253),
       (0.580,0.624,0.651,0.582,0.238)],
"III":[(0.837,0.860,0.924,0.568,2.76),(0.693,0.719,0.774,0.452,2.61),
       (0.342,0.343,0.355,0.164,2.12),(0.236,0.234,0.235,0.094,1.88),
       (0.174,0.175,0.172,0.0615,1.69),(0.139,0.140,0.134,0.0449,1.52),
       (0.122,0.124,0.116,0.0388,1.38),(0.117,0.110,0.101,0.0335,1.26),
       (0.116,0.109,0.099,0.0358,1.152),(0.122,0.129,0.118,0.0507,1.06),
       (0.145,0.144,0.133,0.0646,0.980),(0.192,0.164,0.154,0.0838,0.908),
       (0.288,0.324,0.328,0.229,0.845),(0.386,0.390,0.401,0.297,0.788),
       (0.431,0.426,0.444,0.336,0.737),(0.494,0.528,0.559,0.439,0.692),
       (0.616,0.672,0.742,0.583,0.650)],
"1C": [(3.244,3.294,2.984,2.686,1.037),(2.577,2.576,2.373,2.083,0.979),
       (1.204,0.947,0.895,0.721,0.793),(0.616,0.539,0.512,0.386,0.704),
       (0.371,0.340,0.320,0.227,0.630),(0.236,0.236,0.219,0.147,0.567),
       (0.174,0.179,0.162,0.105,0.514),(0.134,0.139,0.123,0.077,0.469),
       (0.119,0.120,0.103,0.064,0.429),(0.122,0.121,0.105,0.068,0.395),
       (0.145,0.129,0.112,0.076,0.365),(0.192,0.146,0.128,0.092,0.338),
       (0.288,0.317,0.288,0.236,0.314),(0.386,0.395,0.360,0.304,0.293),
       (0.431,0.439,0.401,0.344,0.274),(0.494,0.568,0.517,0.455,0.257),
       (0.616,0.721,0.688,0.586,0.242)],
"3C": [(5.705,5.934,5.449,4.733,3.00),(4.507,4.659,4.353,3.668,2.83),
       (1.772,1.781,1.707,1.287,2.30),(1.079,1.032,0.997,0.685,2.04),
       (0.635,0.648,0.625,0.388,1.83),(0.416,0.439,0.421,0.236,1.65),
       (0.288,0.319,0.302,0.154,1.50),(0.223,0.240,0.225,0.105,1.36),
       (0.198,0.197,0.183,0.081,1.25),(0.198,0.187,0.172,0.078,1.15),
       (0.211,0.187,0.172,0.082,1.06),(0.248,0.201,0.184,0.095,0.985),
       (0.342,0.380,0.358,0.239,0.916),(0.431,0.456,0.430,0.307,0.855),
       (0.478,0.498,0.469,0.346,0.800),(N,N,N,N,N),(N,N,N,N,N)],
"5C": [(6.42,6.75,6.232,5.36,3.73),(5.33,5.53,5.176,4.34,3.53),
       (2.43,2.42,2.320,1.78,2.87),(1.56,1.52,1.466,1.05,2.55),
       (1.02,1.02,0.989,0.660,2.28),(0.693,0.729,0.703,0.437,2.06),
       (0.511,0.535,0.514,0.297,1.87),(0.400,0.401,0.382,0.204,1.71),
       (0.342,0.319,0.301,0.151,1.56),(0.315,0.277,0.260,0.127,1.44),
       (0.329,0.255,0.238,0.117,1.33),(0.357,0.252,0.234,0.119,1.23),
       (N,N,N,N,N),(N,N,N,N,N),(N,N,N,N,N),(N,N,N,N,N),(N,N,N,N,N)],
"7C": [(6.92,6.67,6.303,5.11,6.56),(5.91,5.80,5.471,4.40,6.20),
       (3.00,3.05,2.874,2.17,5.04),(2.12,2.13,1.994,1.45,4.49),
       (1.51,1.59,1.453,1.03,4.02),(1.14,1.21,1.080,0.753,3.63),
       (0.868,0.924,0.812,0.542,3.30),(0.693,0.710,0.614,0.388,3.01),
       (0.580,0.560,0.481,0.290,2.76),(0.494,0.470,0.399,0.233,2.54),
       (0.462,0.409,0.347,0.195,2.35),(0.462,0.371,0.320,0.175,2.18),
       (0.478,0.527,0.481,0.301,2.03),(0.545,0.600,0.551,0.367,1.89),
       (0.635,0.635,0.588,0.403,1.77),(0.777,0.815,0.744,0.559,1.66),
       (0.916,0.874,0.850,0.621,1.56)],
"9C": [(8.11,7.44,7.066,5.466,8.76),(7.01,6.72,6.416,4.900,8.28),
       (4.30,4.11,3.958,2.856,6.73),(3.06,3.13,3.021,2.103,5.99),
       (2.41,2.48,2.391,1.613,5.36),(1.90,1.97,1.907,1.242,4.84),
       (1.56,1.56,1.510,0.943,4.39),(1.24,1.24,1.192,0.709,4.01),
       (1.00,1.00,0.958,0.543,3.67),(0.777,0.826,0.792,0.430,3.38),
       (0.635,0.696,0.667,0.348,3.12),(0.580,0.603,0.576,0.291,2.89),
       (0.598,0.720,0.691,0.390,2.69),(0.654,0.763,0.735,0.436,2.51),
       (0.755,0.775,0.747,0.456,2.35),(0.916,0.945,0.911,0.604,2.20),
       (1.11,0.990,0.953,0.651,2.07)]}

# Table 3: Chl, Bl, Bs, eta, M, alpha
T3 = {"I":(0.010,2e-4,8e-5,0.93,2.34,0.018), "IA":(0.027,0.005,0.002,0.44,1.69,0.020),
      "IB":(0.037,0.083,0.03,0.06,1.49,0.022), "II":(0.044,0.011,0.401,0.007,1.31,0.023),
      "III":(0.177,0.006,1.1,0.003,0.95,0.024), "1C":(1.00,0.004,0.402,0.005,1.22,0.027),
      "3C":(1.28,0.005,1.21,0.003,2.02,0.026), "5C":(3.95,0.022,1.50,0.001,1.89,0.022),
      "7C":(8.4,0.067,2.64,0.0005,2.25,0.017), "9C":(9.1,0.016,3.54,0.0005,4.32,0.015)}
OCEANIC = {"I","IA","IB","II","III"}
CORRUPT = {"3C":[675,700], "5C":[600,625,650,675,700]}
EXTRAP  = {"1C","3C","5C","7C","9C"}   # 300 and 310 nm extrapolated (parenthesised in the paper)

# Values Williamson & Hollins (2022) substituted in their figshare spreadsheet.
WH = {("a","3C",675):0.477, ("a","3C",700):0.592,
      ("b","3C",675):0.745, ("b","3C",700):0.690,
      ("a","5C",600):0.259, ("a","5C",625):0.327, ("a","5C",650):0.367,
      ("a","5C",675):0.499, ("a","5C",700):0.598,
      ("b","5C",600):1.147, ("b","5C",625):1.070, ("b","5C",650):1.002,
      ("b","5C",675):0.940, ("b","5C",700):0.883}

def b_eq8(lam, Bs, Bl):
    """Solonenko & Mobley Eq. (8). Uses their own 1.513, not Haltrin's 1.151302."""
    lam = np.asarray(lam, float)
    return (5.83e-3*(400/lam)**4.322 + Bs*1.513*(400/lam)**1.7 + Bl*0.3411*(400/lam)**0.3)

def kd_eq3(a, b, eta, mu):
    """Solonenko & Mobley Eq. (3)."""
    return (a/mu)*np.sqrt(1 + (b/a)*((0.451+2.584*eta)*mu - (0.205+0.521*eta)))

# --- Jerlov 1976 (Dstl ip_jerlov.csv, 1 nm) -----------------------------------
COL = {"I":"a_I","IA":"b_IA","IB":"c_IB","II":"d_II","III":"e_III",
       "1C":"f_1C","3C":"g_3C","5C":"h_5C","7C":"i_7C","9C":"j_9C"}
src = [r for r in csv.DictReader(open(require("20290782/ip_jerlov.csv")))
       if r["Wavelength"].strip()]
JWL = [int(r["Wavelength"]) for r in src]
def jerlov(t, w):
    if w not in JWL: return None
    s = src[JWL.index(w)][COL[t]]
    return float(s) if s and s.strip() else None

# ------------------------------- self-checks --------------------------------
print("check 1: does Eq. (3) reproduce the Kd column? (catches transcription errors)")
worst = []
for t, rows in SM.items():
    eta = T3[t][3]; mu = 0.98 if t in OCEANIC else 0.85
    for i, w in enumerate(WL):
        kd0, kd, kdh, a, b = rows[i]
        if a is None: continue
        e = 100*(kd_eq3(a, b, eta, mu) - kd)/kd
        if abs(e) > 8: worst.append((t, w, round(e,1)))
print("  error > 8%:", worst if worst else "none")
if worst:
    raise SystemExit(f"Eq. (3) does not reproduce the Kd column: {worst}")

# Types I and IA are known not to reproduce: their Table 3 entries are
# inconsistent with their own b column. See DATA.md section 4.
KNOWN_BAD_B = {"I", "IA"}
print("check 2: does Eq. (8) reproduce the b column?")
unexpected = []
for t, rows in SM.items():
    Bl, Bs = T3[t][1], T3[t][2]
    worst = 0.0
    for i, w in enumerate(WL):
        b = rows[i][4]
        if b is None: continue
        e = 100*(b_eq8(w, Bs, Bl) - b)/b
        worst = max(worst, abs(e))
    tag = "known defect, DATA.md section 4" if t in KNOWN_BAD_B else ""
    if t not in KNOWN_BAD_B and worst > 3:
        unexpected.append((t, round(worst, 1)))
        tag = "UNEXPECTED"
    print(f"  {t:>4}: max {worst:5.1f}%  {tag}")
if unexpected:
    raise SystemExit(f"unexpected disagreement with Eq. (8): {unexpected}")

# The Kd0 column is a reference spectrum from Jerlov (1951, 1968), not from
# Jerlov (1976), so it is not expected to agree; the size of the disagreement
# could not be explained because those editions were not obtainable. See
# DATA.md sections 2, 3 and 5. This check therefore reports rather than fails,
# but the count is fixed so that a change is noticed.
EXPECTED_KD0_MISMATCHES = 30
print("check 3: how far is the Kd0 column from Jerlov 1976?")
mismatch = []
for t, rows in SM.items():
    for i, w in enumerate(WL):
        kd0 = rows[i][0]; jv = jerlov(t, w)
        if kd0 is None or jv is None: continue
        if w in (300, 310) and t in EXTRAP: continue   # extrapolated; not comparable
        e = 100*(kd0 - jv)/jv
        if abs(e) > 10: mismatch.append((t, w, kd0, jv, round(e,1)))
print(f"  {len(mismatch)} of the compared points differ by more than 10%")
print("  expected: the two columns come from different editions of Jerlov")
print("  see DATA.md sections 2, 3 and 5")
if len(mismatch) != EXPECTED_KD0_MISMATCHES:
    raise SystemExit(
        f"expected {EXPECTED_KD0_MISMATCHES} mismatches, found {len(mismatch)}: "
        f"{mismatch}"
    )

# ============================= CSV 1: Jerlov 1976 =============================
with open(DATA_DIR / "jerlov1976_kd.csv", "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["water_type","wavelength_nm","Kd_downwelling_per_m","status","note"])
    for t in COL:
        for w in JWL:
            v = jerlov(t, w)
            if v is None:
                wr.writerow([t, w, "", "missing", "Jerlov 1976 has no value at this wavelength"])
            else:
                wr.writerow([t, w, f"{v:.6g}", "ok", ""])

# ============================= CSV 2: S&M 2015 ================================
CORRUPT_NOTE = "the published value is wrong: the row was duplicated from another wavelength"
rows_out = []
for t, rows in SM.items():
    Bl, Bs = T3[t][1], T3[t][2]
    for i, w in enumerate(WL):
        vals = rows[i]
        for qi, q in enumerate(["Kd0","Kd","KdH","a","b"]):
            pub = vals[qi]
            val, status, src_of, wh, note = pub, "ok", "solonenko2015", "", ""

            if w in CORRUPT.get(t, []):
                wh = WH.get((q, t, w), "")
                if q == "b":
                    val = round(float(b_eq8(w, Bs, Bl)), 4); status = "reconstructed"
                    src_of = "solonenko2015_eq8"
                    note = (CORRUPT_NOTE + ". Reconstructed from Eq. (8) with the Bs, Bl of "
                            "Table 3, using the paper's own small-particle coefficient 1.513 "
                            "(not Haltrin's 1.151302; see DATA.md section 6). The linear "
                            "extrapolation of Williamson & Hollins is given for comparison")
                else:
                    val = ""; status = "missing"; src_of = ""
                    note = CORRUPT_NOTE + ". Not recoverable" + (". Williamson & Hollins filled the gap by interpolation" if wh else "")
                rows_out.append([t, w, q, val, "1/m", status, "", wh, src_of, note]); continue

            if q == "Kd0" and w in (300,310) and t in EXTRAP:
                status = "extrapolated"
                note = "extrapolated from Jerlov's data at longer wavelengths; parenthesised in the paper"
            elif q == "Kd0" and w == 600 and t in {"I","IA","IB","II"}:
                status = "suspect"
                note = ("below a=%.3f in the same table, which is not physically possible: "
                        "Kd must exceed a. Also differs by %+.0f%% from the modelled Kd=%.3f "
                        "in the same table" % (vals[3], 100*(pub-vals[1])/vals[1], vals[1]))
            elif q == "Kd0" and t == "1C" and w >= 525:
                status = "suspect"
                note = "identical to Jerlov III in the same table at all eight wavelengths from 525 to 700 nm; possibly a duplicated column"
            elif q == "b" and t == "IA":
                status = "suspect"
                note = ("Table 3 gives Bl=0.005 for IA, which is inconsistent with the b "
                        "column of the same paper: fitting the b column gives Bl of about 0.001 "
                        "(Bs=0.002 does agree). The b column appears to be the correct one")
            elif q == "b" and t == "I":
                status = "suspect"
                note = ("Table 3 gives Bs=8e-5 for I, which is inconsistent with the b column "
                        "of the same paper (fitting it gives Bs of about 2.1e-4). The values "
                        "themselves are very small")
            rows_out.append([t, w, q, val, "1/m", status, val, "", src_of, note])

import io
with open(DATA_DIR / "solonenko2015_iop.csv","w",newline="",encoding="utf-8") as f:
    wr = csv.writer(f)
    wr.writerow(["water_type","wavelength_nm","quantity","value_per_m","unit","status",
                 "published_value_per_m","williamson2022_value_per_m","value_source","note"])
    wr.writerows(rows_out)

from collections import Counter
print("  status counts:", dict(Counter(r[5] for r in rows_out)))
report("solonenko2015_iop.csv", len(rows_out))

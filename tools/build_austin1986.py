# -*- coding: utf-8 -*-
"""Transcribe Austin & Petzold (1986) Tables IV and VI.

Table VI replaces Jerlov's published Kd values, which fall below the
attenuation of pure sea water at several wavelengths. Table IV gives the
slope M and the pure sea water Kw that drive the authors' model.

No input file is needed: the values are literals below, checked against the
paper's own Eq. (6) before anything is written.
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import DATA_DIR, report

import csv
WL=[350,375,400,425,450,475,500,525,550,575,600,625,650,675,700]
# Table VI: replacement K(lambda) for the Jerlov water types.
T6={"I":  [0.0510,0.0302,0.0217,0.0185,0.0176,0.0184,0.0280,0.0504,0.0640,0.0931,0.2408,0.3174,0.3559,0.4372,0.6513],
    "IA": [0.0632,0.0412,0.0316,0.0280,0.0257,0.0250,0.0332,0.0545,0.0674,0.0960,0.2437,0.3206,0.3601,0.4410,0.6530],
    "IB": [0.0782,0.0546,0.0438,0.0395,0.0355,0.0330,0.0396,0.0596,0.0715,0.0995,0.2471,0.3245,0.3652,0.4457,0.6550],
    "II": [0.1325,0.1031,0.0878,0.0814,0.0714,0.0620,0.0627,0.0779,0.0863,0.1122,0.2595,0.3389,0.3837,0.4626,0.6623],
    "III":[0.2335,0.1935,0.1697,0.1594,0.1381,0.1160,0.1056,0.1120,0.1139,0.1359,0.2826,0.3655,0.4181,0.4942,0.6760],
    "1C": [0.3345,0.2839,0.2516,0.2374,0.2048,0.1700,0.1486,0.1461,0.1415,0.1596,0.3057,0.3922,0.4525,0.5257,0.6896]}
# Table IV: slope M(lambda) and pure sea water Kw(lambda), every 5 nm.
T4=[(350,2.1442,0.0510),(355,2.0968,0.0453),(360,2.0504,0.0405),(365,2.0051,0.0365),
(370,1.9610,0.0331),(375,1.9183,0.0302),(380,1.8772,0.0278),(385,1.8379,0.0258),
(390,1.8009,0.0242),(395,1.7671,0.0228),(400,1.7383,0.0217),(405,1.7463,0.0208),
(410,1.7591,0.0200),(415,1.7312,0.0194),(420,1.6974,0.0189),(425,1.6550,0.0185),
(430,1.6108,0.0182),(435,1.5648,0.0180),(440,1.5169,0.0178),(445,1.4673,0.0176),
(450,1.4158,0.0176),(455,1.3627,0.0175),(460,1.3077,0.0176),(465,1.2521,0.0177),
(470,1.1982,0.0179),(475,1.1460,0.0184),(480,1.0955,0.0193),(485,1.0469,0.0206),
(490,1.0000,0.0224),(495,0.9550,0.0248),(500,0.9118,0.0280),(505,0.8704,0.0320),
(510,0.8310,0.0369),(515,0.7934,0.0428),(520,0.7578,0.0498),(525,0.7241,0.0504),
(530,0.6924,0.0526),(535,0.6627,0.0550),(540,0.6350,0.0577),(545,0.6094,0.0607),
(550,0.5860,0.0640),(555,0.5647,0.0678),(560,0.5457,0.0723),(565,0.5289,0.0776),
(570,0.5146,0.0842),(575,0.5027,0.0931),(580,0.4935,0.1065),(585,0.4871,0.1341),
(590,0.4840,0.1578),(595,0.4853,0.2043),(600,0.4903,0.2409),(605,0.4983,0.2688),
(610,0.5090,0.2892),(615,0.5223,0.3040),(620,0.5380,0.3124),(625,0.5659,0.3174),
(630,0.6231,0.3196),(635,0.6683,0.3227),(640,0.7001,0.3290),(645,0.7201,0.3397),
(650,0.7300,0.3559),(655,0.7323,0.3789),(660,0.7301,0.4105),(665,0.7205,0.4208),
(670,0.7008,0.4278),(675,0.6693,0.4372),(680,0.6245,0.4521),(685,0.5651,0.4755),
(690,0.4901,0.5116),(695,0.3984,0.5671),(700,0.2891,0.6514)]
M={w:m for w,m,_ in T4}; KW={w:k for w,_,k in T4}

# Check: Eq. (6), anchored at Jerlov's K(475), must reproduce Table VI.
print("check: K(l) = [M(l)/M(475)] * [K(475) - Kw(475)] + Kw(l) vs Table VI")
print(f"{'type':>5} {'K(475)':>9} {'max error %':>13}")
for t,vals in T6.items():
    k475=vals[WL.index(475)]
    e=[100*((M[w]/M[475])*(k475-KW[475])+KW[w]-vals[i])/vals[i] for i,w in enumerate(WL)]
    print(f"{t:>4} {k475:>8.4f} {max(e,key=abs):>+12.2f}")

with open(DATA_DIR / "austin1986_kd.csv","w",newline="",encoding="utf-8") as f:
    wr=csv.writer(f); wr.writerow(["water_type","wavelength_nm","Kd_downwelling_per_m","status","note"])
    for t,vals in T6.items():
        for i,w in enumerate(WL):
            if t=="I":
                st,nt="pure_seawater","the type I row is pure sea water Kw; Jerlov's own values fall below it"
            elif w==475:
                st,nt="jerlov_original","475 nm is identical to Jerlov (1976) Table XXVII"
            else:
                st,nt="model","computed from K(475) by Austin & Petzold Eq. (6)"
            wr.writerow([t,w,f"{vals[i]:.4f}",st,nt])

with open(DATA_DIR / "austin1986_model.csv","w",newline="",encoding="utf-8") as f:
    wr=csv.writer(f); wr.writerow(["wavelength_nm","M_slope","Kw_pure_seawater_per_m","status","note"])
    for w,m,k in T4:
        st="extrapolated" if w in (350,355,360) else "ok"
        nt="the paper states this M was extrapolated and should be used with caution" if st=="extrapolated" else ""
        wr.writerow([w,f"{m:.4f}",f"{k:.4f}",st,nt])
report("austin1986_kd.csv", 90); report("austin1986_model.csv", 71)

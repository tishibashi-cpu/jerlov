# -*- coding: utf-8 -*-
"""Rebuild the packaged CSV tables from the primary sources.

Run from the repository root. See tools/README.md for the inputs each script
needs and where to obtain them; they are not redistributed here.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES_DIR = ROOT / "sources"
DATA_DIR = ROOT / "uwlight" / "data"

import csv
MAP={'b_IA':'IA','c_IB':'IB','d_II':'II','e_III':'III','f_1C':'1C','g_3C':'3C','h_5C':'5C','i_7C':'7C'}
out=[]; cnt={'included':0,'excluded_sparse':0}
for fn,q in [("op_STEP_6_a.csv","a"),("op_STEP_6_b.csv","b")]:
    for r in csv.DictReader(open(SOURCES_DIR / f"20290782/{fn}")):
        if not r['Wavelength']: continue
        t=MAP[r['Jerlov']]; w=int(float(r['Wavelength']))
        v=float(r[q]); n=int(r['Averaged2']); sd=r['StdDev2']
        st='included' if n>=5 else 'excluded_sparse'
        nt='' if st=='included' else '寄与した測定が5点未満のため論文の最終平均から除外された'
        cnt[st]+=1
        out.append([t,w,q,f"{v:.6g}","1/m",(f"{float(sd):.6g}" if sd else ""),n,st,nt])

# 検証: 論文 (2023) Table 1, 2 と照合
PUB={('a','IB',412):0.0434,('a','II',412):0.0712,('a','III',412):0.128,('a','1C',412):0.180,
     ('a','3C',412):0.235,('a','5C',412):0.437,('a','II',676):0.465,('a','III',715):1.02,
     ('b','IB',412):0.141,('b','II',412):0.205,('b','III',412):0.320,('b','1C',412):0.462,
     ('b','3C',412):0.663,('b','5C',412):1.10,('b','III',715):0.243,('b','5C',650):1.24}
idx={(r[2],r[0],r[1]):float(r[3]) for r in out}
print("=== 検証: Hollins & Williamson (2023) Table 1, 2 との照合 ===")
bad=[k for k,v in PUB.items() if k not in idx or abs(idx[k]-v)/v>0.01]
print("  不一致:", bad if bad else f"なし ({len(PUB)}点すべて1%以内)")
print(f"\n採用 (n>=5): a と b 合わせて {cnt['included']} 点  → 論文は各53点、計106点")
print(f"除外 (n<5) : {cnt['excluded_sparse']} 点")

with open(DATA_DIR / "williamson2022_measured.csv","w",newline="",encoding="utf-8") as f:
    wr=csv.writer(f)
    wr.writerow(["water_type","wavelength_nm","quantity","value_per_m","unit",
                 "std_dev_per_m","n_campaigns","status","note"])
    wr.writerows(sorted(out,key=lambda r:(r[0],r[2],r[1])))
print(f"\nwilliamson2022_measured.csv: {len(out)} 行")

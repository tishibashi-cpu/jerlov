# -*- coding: utf-8 -*-
"""Extract the pure water absorption that Williamson & Hollins (2022) used.

Their a spectra are a = aw + aChl + aCDOM, Eqs. (4)-(6), and the paper says
only that aw "was taken from Buiteveld et al." The spreadsheet holds the aw
that was actually used, at 1 nm from 300 to 800 nm, in the lookup table of
the sheet 'a,b measured and model' (columns AK to AN: wavelength, aw, A, E).

This reads it and checks that it is the aw behind the shipped a: with it and
the paper's Table 6, Eqs. (4)-(6) must give back the a of the sheet
'a,b JIB-5C'. It is not checked against Buiteveld et al. (1994), which has
not been obtained; see DATA.md section 20.
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import DATA_DIR, require, report

import openpyxl, csv, numpy as np
wb=openpyxl.load_workbook(require("20290782/20221121-Dstl_MIOP_analysis_v3.xlsx"),data_only=True)

ws=wb['a,b measured and model']
head=[ws.cell(4,c).value for c in range(37,41)]
if head!=['λ','aw','A','E']:
    raise SystemExit(f"the lookup table has moved: AK4:AN4 reads {head}")
ref={}
for r in range(5,506):
    w,aw,A,E=(ws.cell(r,c).value for c in range(37,41))
    ref[int(w)]=(float(aw),float(A),float(E))
wls=sorted(ref)
print(f"read {len(wls)} wavelengths, {wls[0]}-{wls[-1]} nm")

# Check 1: the grid, and nothing absurd in it.
print("\ncheck 1: 1 nm from 300 to 800 nm, every aw positive")
if wls!=list(range(300,801)):
    raise SystemExit("the aw table is not at 1 nm from 300 to 800 nm")
if not all(np.isfinite(ref[w][0]) and ref[w][0]>0 for w in wls):
    raise SystemExit("an aw value is not a positive number")
print("  ok")

# The a spectra this aw went into, as shipped.
wa=wb['a,b JIB-5C']
T=["IB","II","III","1C","3C","5C"]
a={t:{} for t in T}
for r in range(6, wa.max_row+1):
    w=wa.cell(r,2).value
    if not isinstance(w,(int,float)): continue
    for i,t in enumerate(T):
        v=wa.cell(r,3+i).value
        if v is not None: a[t][int(w)]=float(v)

# Check 2: Eqs. (4)-(6) with the printed Table 6 give back a. Table 6 is
# printed to two or three figures, which is what limits the agreement; the
# median is the real test, the maximum a guard against a gross change.
TABLE6={"IB":(0.134,1.20,0.012),"II":(0.271,1.45,0.011),"III":(1.679,0.53,0.012),
        "1C":(2.832,0.52,0.014),"3C":(4.890,0.47,0.009),"5C":(9.937,0.56,0.017)}
print("\ncheck 2: a = aw + A Chl^E + aChl(440) M exp(-alpha (l - 440)), Table 6")
print(f"{'type':>5} {'median %':>9} {'max %':>8}")
_,A440,E440=ref[440]
for t,(chl,M,alpha) in TABLE6.items():
    e=[]
    for w in wls:
        aw,A,E=ref[w]
        pred=aw + A*chl**E + A440*chl**E440*M*np.exp(-alpha*(w-440))
        e.append(100*(pred-a[t][w])/a[t][w])
    e=np.array(e)
    med,worst=float(np.median(np.abs(e))),float(e[np.argmax(np.abs(e))])
    print(f"{t:>5} {med:>9.2f} {worst:>+8.2f}")
    if med>0.5 or abs(worst)>5.0:
        raise SystemExit(f"aw no longer reproduces the a of Jerlov {t}")

# Check 3: no water type absorbs less than pure water, beyond the rounding
# of a to three significant figures. Where A is zero, from 720 nm on, every
# type's a is aw itself.
print("\ncheck 3: aw <= a for every type, within the rounding of a")
over=[(t,w) for t in T for w in wls if ref[w][0]>a[t][w]*1.005]
if over:
    raise SystemExit(f"aw exceeds a: {over[:5]}")
flat=[w for w in wls if ref[w][1]==0]
print(f"  ok; A is zero from {flat[0]} nm, where a is aw for every type")

with open(DATA_DIR / "williamson2022_aw.csv","w",newline="",encoding="utf-8") as f:
    wr=csv.writer(f)
    wr.writerow(["wavelength_nm","aw_per_m","unit","status","note"])
    for w in wls:
        wr.writerow([w,repr(ref[w][0]),"1/m","ok",""])
report("williamson2022_aw.csv", len(wls))

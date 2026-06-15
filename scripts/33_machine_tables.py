#!/usr/bin/env python
"""
33_machine_tables.py -- Build the machine-readable tables promised in the paper:
  paper/two_break_tables/table_sample_full.csv  (one row per burst)
  paper/two_break_tables/table_fits_full.csv    (one row per time bin, key columns)
Pure catalog reformatting; deterministic.
"""
import os, collections
import numpy as np
from astropy.table import Table

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = f"{ROOT}/paper/two_break_tables"; os.makedirs(OUT, exist_ok=True)

T = Table.read(f"{ROOT}/results/clean_sample_all_models.ecsv", format="ascii.ecsv")
T = T[T["BLOCK"] >= 0]
SP = Table.read(f"{ROOT}/results/single_pulse_grbs.ecsv", format="ascii.ecsv")
trig = np.array(T["TRIGGER"])
cnt = collections.Counter(trig)
def tier(n): return "Gold" if n >= 10 else ("Silver" if n >= 5 else "Bronze")

BM = {"Band":"BAND","CPL":"CPL","SBPL":"SBPL","DSBPL":"DSBPL","Band+BB":"BANDBB","CPL+BB":"CPLBB"}

# ---------- per-burst table ----------
rows = []
for bn in sorted(cnt):
    s = T[trig == bn]
    best = [str(r["BEST_AIC_MODEL"]) for r in s
            if str(r["BEST_AIC_MODEL"]) in BM and bool(r[BM[str(r["BEST_AIC_MODEL"])]+"_VALID"])]
    mc = collections.Counter(best).most_common(1)
    spr = SP[SP["TRIGGER_NAME"] == bn]
    nbb = int(np.sum((np.array(s["BANDBB_VALID"],bool) & (np.array(s["LRT_BANDBB_BAND"],float) >= 14)) |
                     (np.array(s["CPLBB_VALID"],bool) & (np.array(s["LRT_CPLBB_CPL"],float) >= 14))))
    n2b = int(np.sum(np.array(s["DSBPL_VALID"],bool) & (np.array(s["LRT_DSBPL_SBPL"],float) >= 14)))
    rows.append(dict(
        trigger=bn,
        t90=float(spr["T90"][0]) if len(spr) else np.nan,
        fluence=float(spr["FLUENCE"][0]) if len(spr) else np.nan,
        brightest_nai=str(spr["DETECTOR"][0]) if len(spr) else "",
        has_lat=bool(spr["HAS_LAT"][0]) if len(spr) else False,
        n_bins=int(cnt[bn]), grade=tier(cnt[bn]),
        preferred_model=(mc[0][0] if mc else ""),
        n_bb_decisive=nbb, n_twobreak_decisive=n2b))
Table(rows=rows).write(f"{OUT}/table_sample_full.csv", format="ascii.csv", overwrite=True)
print(f"wrote table_sample_full.csv ({len(rows)} bursts)")

# ---------- per-bin table (key columns) ----------
keep = ["TRIGGER","BLOCK","T_START","T_STOP","N_DETS",
        "BAND_VALID","BAND_ALPHA","BAND_ALPHA_ERR","BAND_EP","BAND_EP_ERR",
        "BAND_BETA","BAND_BETA_ERR","BAND_AIC",
        "CPL_VALID","CPL_AIC","SBPL_VALID","SBPL_AIC",
        "DSBPL_VALID","DSBPL_XB","DSBPL_XB_ERR","DSBPL_XP","DSBPL_XP_ERR","DSBPL_AIC",
        "BANDBB_VALID","BANDBB_KT","BANDBB_KT_ERR","BANDBB_AIC",
        "CPLBB_VALID","CPLBB_KT","CPLBB_KT_ERR","CPLBB_AIC",
        "BEST_AIC_MODEL","LRT_BANDBB_BAND","LRT_CPLBB_CPL","LRT_DSBPL_SBPL"]
T[keep].write(f"{OUT}/table_fits_full.csv", format="ascii.csv", overwrite=True)
print(f"wrote table_fits_full.csv ({len(T)} bins, {len(keep)} cols)")

#!/usr/bin/env python
"""
38_build_manifest.py -- one human-readable master table of all 106 bursts:
detector selection, source (analysis) interval, background windows, N bins.
Output: results/master_manifest.csv  (per-burst; full per-detector backgrounds
live in results/background_intervals_clean.ecsv).
"""
import os, json, glob, collections
import numpy as np
from astropy.table import Table

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda p: Table.read(os.path.join(ROOT, "results", p), format="ascii.ecsv")

sp  = R("single_pulse_grbs.ecsv")
bk  = R("background_intervals_clean.ecsv")
spd = {str(r["TRIGGER_NAME"]): r for r in sp}

rows = []
for trig in sorted(spd):
    s = spd[trig]
    bb = bk[bk["TRIGGER_NAME"] == trig]
    # Detector selection + reference detector come from the ACTUAL production fit
    # (per-burst JSON), NOT the catalog row: the engine falls back to the
    # highest-significance approved NaI when the catalog detector is unavailable,
    # so the catalog DETECTOR can disagree with what was actually fitted.
    jf = os.path.join(os.environ.get("FIT_ROOT", os.path.join(ROOT, "results/clean_per_burst")), trig, "spectral_fits.json")
    fit_dets, ref = None, str(s["DETECTOR"]).strip()
    if os.path.exists(jf):
        jd = json.load(open(jf))
        ref = str(jd.get("canonical_det", ref)).strip()
        fit_dets = [str(d) for d in jd.get("fit_dets", [])]
    if fit_dets:
        nai = [d for d in fit_dets if d.startswith("n")]
        bgo = [d for d in fit_dets if d.startswith("b")]
    else:  # no production JSON yet: fall back to the background-table detectors
        nai = [str(r["DETECTOR"]) for r in bb if str(r["DETECTOR"]).startswith("n")]
        bgo = [str(r["DETECTOR"]) for r in bb if str(r["DETECTOR"]).startswith("b")]
    # source (analysis) interval = the Bayesian-block span
    bf = os.path.join(ROOT, "results", f"clean_blocks/bb_blocks_spectral_{trig}.ecsv")
    src_t1 = src_t2 = nbins = None
    if os.path.exists(bf):
        t = Table.read(bf, format="ascii.ecsv")
        t = t[t["DETECTOR"] == t["DETECTOR"][0]]
        src_t1, src_t2, nbins = float(t["T_START"].min()), float(t["T_STOP"].max()), len(t)
    # reference-detector background windows (full set in the ECSV)
    rb = bb[bb["DETECTOR"] == ref]
    if len(rb):
        rb = rb[0]
        pre = (float(rb["BKG_NEG_START"]), float(rb["BKG_NEG_STOP"]))
        post = (float(rb["BKG_POS_START"]), float(rb["BKG_POS_STOP"]))
    else:
        pre = post = (np.nan, np.nan)
    rows.append(dict(
        trigger=trig, name=str(s["NAME"]),
        T90=round(float(s["T90"]), 2), fluence=float(s["FLUENCE"]),
        has_lat=bool(s["HAS_LAT"]),
        reference_nai=ref,
        nai_dets="|".join(nai), bgo_det="|".join(bgo),
        lle=bool(os.path.exists(bf) and len(glob.glob(os.path.join(ROOT,'data',trig,'*lle*')))>0),
        n_bins=nbins,
        source_t1=None if src_t1 is None else round(src_t1, 2),
        source_t2=None if src_t2 is None else round(src_t2, 2),
        bkg_pre_start=round(pre[0], 2), bkg_pre_stop=round(pre[1], 2),
        bkg_post_start=round(post[0], 2), bkg_post_stop=round(post[1], 2),
    ))

Table(rows=rows).write(os.path.join(ROOT, "results", "master_manifest.csv"),
                       format="ascii.csv", overwrite=True)
print(f"wrote results/master_manifest.csv  ({len(rows)} bursts)")
print("columns:", list(rows[0].keys()))

#!/usr/bin/env python
"""
35_variability_bb.py -- Fine-grid variability pass for all 106 bursts.
Bayesian Blocks in the Poisson 'events' fitness (valid at any counts/cell) on a
1-ms grid over each burst's pulse core (clean-blocks span +/- 1 s), canonical
detector, 8-900 keV. Records the finest block structure at p0=0.01 and the
stricter p0=1e-3 (robustness), so the sub-128-ms structure is quantified per
burst. Grid degrades to 2 ms for very long cores to cap the O(M^2) cost.
Output: results/variability_bb.ecsv
NOTE: single-detector pass; sub-10-ms claims should later be cross-confirmed on
a second NaI and against the LATBright Haar-MVT tool (s02k_mvt_golkhou).
"""
import glob, json, os, time
import numpy as np
from astropy.io import fits
from astropy.table import Table
from astropy.stats import bayesian_blocks

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_CELLS = 80_000
# env-overridable roots (authoritative consensus run points these at the fresh dirs)
_CPB = os.environ.get("FIT_ROOT", os.path.join(ROOT, "results/clean_per_burst"))
_BLK = os.environ.get("BLK_ROOT", os.path.join(ROOT, "results/clean_blocks"))

def core_window(trig):
    t = Table.read(f"{_BLK}/bb_blocks_spectral_{trig}.ecsv", format="ascii.ecsv")
    d = t[t["DETECTOR"] == t["DETECTOR"][0]]
    return float(d["T_START"].min()) - 1.0, float(d["T_STOP"].max()) + 1.0

rows = []
t_all = time.time()
for f in sorted(glob.glob(f"{_CPB}/*/spectral_fits.json")):
    trig = f.split("/")[-2]
    try:
        det = json.load(open(f))["canonical_det"]
        tte = sorted(glob.glob(f"{ROOT}/data/{trig}/glg_tte_{det}_*.fit*"))[0]
        with fits.open(tte) as h:
            ev = h["EVENTS"].data
            t0 = next(hh.header["TRIGTIME"] for hh in h if "TRIGTIME" in hh.header)
            eb = h["EBOUNDS"].data
            emid = 0.5 * (np.asarray(eb["E_MIN"]) + np.asarray(eb["E_MAX"]))
            tt = np.asarray(ev["TIME"]) - t0
            tt = tt[(emid[ev["PHA"]] >= 8) & (emid[ev["PHA"]] <= 900)]
        lo, hi = core_window(trig)
        tt = tt[(tt >= lo) & (tt <= hi)]
        span = hi - lo
        dt = 0.001 if span / 0.001 <= MAX_CELLS else span / MAX_CELLS
        edges = np.arange(lo, hi + dt, dt)
        ctr = 0.5 * (edges[:-1] + edges[1:])
        cnt, _ = np.histogram(tt, bins=edges)
        out = dict(TRIGGER_NAME=trig, DETECTOR=det, T_LO=lo, T_HI=hi, DT_GRID=dt,
                   N_EVENTS=len(tt))
        for tag, p0 in (("P01", 0.01), ("P001", 0.001)):
            t1 = time.time()
            e = bayesian_blocks(ctr, cnt, fitness="events", p0=p0)
            w = np.diff(e)
            out[f"NBLOCKS_{tag}"] = len(w)
            out[f"WMIN_{tag}"] = float(w.min()) if len(w) else np.nan
            out[f"NSUB128_{tag}"] = int(np.sum(w < 0.128))
            out[f"PINNED_{tag}"] = bool(len(w) and abs(w.min() - dt) < 1e-9)
            out[f"RUNTIME_{tag}"] = round(time.time() - t1, 2)
        rows.append(out)
        print(f"{trig} [{det}] dt={dt*1000:.1f}ms cells={len(ctr)}: "
              f"wmin={out['WMIN_P001']*1000:.1f}ms nsub128={out['NSUB128_P001']} (p0=1e-3)")
    except Exception as exc:
        print(f"{trig}: FAIL {type(exc).__name__}: {exc}")
        rows.append(dict(TRIGGER_NAME=trig, DETECTOR="", T_LO=np.nan, T_HI=np.nan,
                         DT_GRID=np.nan, N_EVENTS=0))
T = Table(rows=rows)
T.write(f"{ROOT}/results/variability_bb.ecsv", format="ascii.ecsv", overwrite=True)
ok = np.isfinite(np.array(T["DT_GRID"], float))
w = np.array([r.get("WMIN_P001", np.nan) for r in rows], float)
ns = np.array([r.get("NSUB128_P001", 0) for r in rows], float)
print(f"\n=== SUMMARY (p0=1e-3) over {ok.sum()} bursts, {time.time()-t_all:.0f}s total ===")
print(f"bursts with sub-128ms blocks: {int(np.sum(ns>0))}")
print(f"finest-block distribution (ms): median={np.nanmedian(w)*1000:.0f} "
      f"p10={np.nanpercentile(w,10)*1000:.1f} min={np.nanmin(w)*1000:.1f}")
print(f"bursts pinned at the grid floor: {int(np.sum([r.get('PINNED_P001',False) for r in rows]))}")

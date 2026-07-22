#!/usr/bin/env python
"""
40_temporal_survey.py -- run the temporal chain (T90/T50, pulse shapes, spectral
lag, MVT-Haar) over the human-reviewed sample, from the SAME approved selections
that drove the spectroscopy. One row per burst -> results/temporal_catalog_human.ecsv.

Uses the vendored handbook temporal chain (grb_pipeline.analysis.temporal.
analyze_single_pulse: T90 -> MVT -> lag -> pulse fits) on the reference NaI, with
a per-band polynomial background from the approved windows. The CANONICAL Bala
MVT is produced separately by the handbook mvt_runner (this MVT is the Haar
cross-check). Light tier (base env); no threeML needed.
"""
import glob
import os
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
from astropy.io import fits
from astropy.table import Table

warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RES = os.path.join(ROOT, "results")
sys.path.insert(0, os.path.expanduser("~/Desktop/Projects/GRB_Handbook_Project"))
from grb_pipeline.analysis.lightcurve import LightCurveData
from grb_pipeline.analysis.temporal import analyze_single_pulse

# energy bands (keV): total NaI, and the lag soft/hard pair (docstring example)
E_TOTAL = (8.0, 900.0)
E_SOFT = (25.0, 50.0)
E_HARD = (100.0, 300.0)


def _events(trig, det):
    f = sorted(glob.glob(f"{DATA}/{trig}/glg_tte_{det}_*.fit*"))
    if not f:
        return None
    with fits.open(f[-1]) as h:
        ev = h["EVENTS"].data
        t0 = next(hh.header["TRIGTIME"] for hh in h if "TRIGTIME" in hh.header)
        tt = np.asarray(ev["TIME"], float) - t0
        eb = h["EBOUNDS"].data
        emid = 0.5 * (np.asarray(eb["E_MIN"]) + np.asarray(eb["E_MAX"]))
        en = emid[np.asarray(ev["PHA"])]
    return tt, en


def _binned(tt, en, band, edges, dt):
    m = (en >= band[0]) & (en <= band[1])
    cnt, _ = np.histogram(tt[m], bins=edges)
    return cnt / dt


def _poly_bkg(tc, rate, pre, post, deg=2):
    """Polynomial background rate on the grid, fit over the pre+post windows."""
    m = ((tc >= pre[0]) & (tc <= pre[1])) | ((tc >= post[0]) & (tc <= post[1]))
    if m.sum() < deg + 2:
        return np.full_like(rate, np.median(rate[m]) if m.any() else 0.0)
    c = np.polyfit(tc[m], rate[m], deg)
    return np.polyval(c, tc)


def survey_one(row):
    trig = row["trigger"]
    tt, en = row["_ev"]
    src = (row["src1"], row["src2"])
    pre = (row["pre1"], row["pre2"])
    post = (row["post1"], row["post2"])
    # grid: full pre..post extent, fine binning scaled to duration
    t_lo, t_hi = pre[0], post[1]
    span = src[1] - src[0]
    dt = float(np.clip(round(span / 200.0, 3), 0.008, 0.256))  # ~ms..0.25s
    edges = np.arange(t_lo, t_hi + dt, dt)
    tc = 0.5 * (edges[:-1] + edges[1:])
    tot = _binned(tt, en, E_TOTAL, edges, dt)
    cnt_tot, _ = np.histogram(tt[(en >= E_TOTAL[0]) & (en <= E_TOTAL[1])], bins=edges)
    bkg = _poly_bkg(tc, tot, pre, post)
    lc = LightCurveData(time=tc, rate=tot, rate_err=np.sqrt(np.maximum(cnt_tot, 1)) / dt,
                        binsize=dt)
    # band LCs (background-subtracted) for the lag
    soft = _binned(tt, en, E_SOFT, edges, dt)
    hard = _binned(tt, en, E_HARD, edges, dt)
    soft_net = soft - _poly_bkg(tc, soft, pre, post)
    hard_net = hard - _poly_bkg(tc, hard, pre, post)
    lc_soft = LightCurveData(time=tc, rate=soft_net,
                             rate_err=np.sqrt(np.maximum(soft * dt, 1)) / dt, binsize=dt)
    lc_hard = LightCurveData(time=tc, rate=hard_net,
                             rate_err=np.sqrt(np.maximum(hard * dt, 1)) / dt, binsize=dt)
    out = analyze_single_pulse(lc, background=bkg, lc_soft=lc_soft, lc_hard=lc_hard,
                               n_mc_mvt=0, n_ccf_sims=400, n_lag_sims=150,
                               data_type="fermi")
    t90 = out.get("t90") or (np.nan,) * 4
    t50 = out.get("t50") or (np.nan,) * 4
    mvt = out.get("mvt") or {}
    lag = out.get("lag")                     # SpectralLagResult or None
    lag_s = float(lag.lag) if lag is not None else np.nan
    lag_err = float(lag.lag_err) if lag is not None else np.nan
    lag_sig = out.get("lag_peak_sig")
    pf = out.get("pulse_fits") or {}
    # best pulse model by reduced chi2
    best, best_chi = None, np.inf
    for m, f in pf.items():
        if isinstance(f, dict) and "error" not in f and np.isfinite(f.get("chi_sq", np.inf)):
            rc = f["chi_sq"] / max(f.get("dof", 1), 1)
            if rc < best_chi:
                best, best_chi = m, rc
    phi = pf.get("gowri", {}).get("phi") if isinstance(pf.get("gowri"), dict) else None
    return {
        "TRIGGER_NAME": trig, "REF_DET": row["ref"], "BIN_MS": dt * 1000,
        "T90": float(t90[0]), "T90_ERR": float(t90[1]),
        "T90_START": float(t90[2]), "T90_STOP": float(t90[3]),
        "T50": float(t50[0]),
        "MVT_S": mvt.get("mvt_s", np.nan), "MVT_ERR_S": mvt.get("mvt_err_s", np.nan),
        "MVT_TYPE": str(mvt.get("type", "")),
        "LAG_S": lag_s, "LAG_ERR_S": lag_err,
        "LAG_SIG": float(lag_sig) if lag_sig is not None and np.isfinite(lag_sig) else np.nan,
        "LAG_ACCEPTED": bool(out.get("lag_accepted", False)),
        "BEST_PULSE": str(best), "PULSE_REDCHI": float(best_chi) if np.isfinite(best_chi) else np.nan,
        "GOWRI_PHI": float(phi) if phi is not None else np.nan,
    }


def main():
    cat = Table.read(os.path.join(RES, "background_intervals_human_clean.ecsv"),
                     format="ascii.ecsv")
    rows = []
    for trig in sorted(set(str(x) for x in cat["TRIGGER_NAME"])):
        sub = cat[[str(x) == trig for x in cat["TRIGGER_NAME"]]]
        nai = [r for r in sub if str(r["DETECTOR"]).startswith("n")]
        if not nai:
            continue
        ref = min(nai, key=lambda r: float(r["DET_ANGLE"]) if str(r["DET_ANGLE"]) not in ("nan", "--") else 999)
        ev = _events(trig, str(ref["DETECTOR"]).strip())
        if ev is None:
            continue
        rows.append({"trigger": trig, "ref": str(ref["DETECTOR"]).strip(), "_ev": ev,
                     "src1": float(ref["SRC_START"]), "src2": float(ref["SRC_STOP"]),
                     "pre1": float(ref["BKG_NEG_START"]), "pre2": float(ref["BKG_NEG_STOP"]),
                     "post1": float(ref["BKG_POS_START"]), "post2": float(ref["BKG_POS_STOP"])})
    print(f"temporal survey over {len(rows)} bursts (T90/MVT-Haar/lag/pulse) ...")
    results = []
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(survey_one, r): r["trigger"] for r in rows}
        for fut in as_completed(futs):
            trig = futs[fut]
            try:
                results.append(fut.result())
                print(f"  [{len(results)}/{len(rows)}] {trig} ok")
            except Exception as e:
                print(f"  {trig}: FAILED {type(e).__name__}: {str(e)[:80]}")
    if results:
        t = Table(rows=results)
        out = os.path.join(RES, "temporal_catalog_human.ecsv")
        t.write(out, format="ascii.ecsv", overwrite=True)
        print(f"\nwrote {out} ({len(results)} bursts)")
        # quick medians
        for c in ("T90", "MVT_S", "LAG_S"):
            v = np.array([r[c] for r in results], float)
            v = v[np.isfinite(v)]
            if len(v):
                print(f"  median {c} = {np.median(v):.3g}  (N={len(v)})")


if __name__ == "__main__":
    main()

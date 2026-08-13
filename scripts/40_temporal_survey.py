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


def _tx_core(tc, net_counts, frac):
    """T_x from a cumulative net-count curve with an EXPLICIT first-crossing
    convention (the curve is NOT monotonic -- background-subtracted bins go
    negative -- so np.interp is invalid here).  Returns (tx, t_lo, t_hi)."""
    cs = np.cumsum(np.asarray(net_counts, float))
    tot = cs[-1]
    if not np.isfinite(tot) or tot <= 0:
        return np.nan, np.nan, np.nan
    y = cs / tot
    lo_f, hi_f = 0.5 * (1.0 - frac), 1.0 - 0.5 * (1.0 - frac)

    def cross(f):
        hit = np.flatnonzero(y >= f)
        if hit.size == 0:
            return tc[-1]
        i = hit[0]
        if i == 0:
            return tc[0]
        y0, y1 = y[i - 1], y[i]
        if y1 == y0:
            return tc[i]
        return tc[i - 1] + (f - y0) * (tc[i] - tc[i - 1]) / (y1 - y0)

    a, b = cross(lo_f), cross(hi_f)
    return b - a, a, b


def _tx_with_mc(tc, raw_counts, bkg_counts, src, frac=0.90, n_mc=1000, seed=0):
    """Point estimate AND uncertainty from the SAME estimator (Codex audit
    2026-08-13, item A4).

    The previous implementation computed the point value from SIGNED net counts
    but sampled the MC from RECTIFIED counts (max(net,0)) -- a different,
    positively biased estimator: on bn081224887 the point value was 18.9 s while
    the MC distribution sat at 116.6 s, so the quoted sigma described something
    that was not T90.  Here:
      * the search window is the APPROVED SOURCE WINDOW (declared, not implicit);
      * realizations are Poisson draws of the RAW counts (non-negative by
        construction), from which the SAME fitted background is subtracted --
        no rectification of a residual anywhere;
      * point and MC call the identical `_tx_core`.
    Background-model uncertainty is NOT propagated (the polynomial is held
    fixed); that is a stated limitation, not a hidden one.
    """
    m = (tc >= src[0]) & (tc <= src[1])
    if m.sum() < 8:
        return np.nan, np.nan, np.nan, np.nan
    tcw = tc[m]
    raw_w = np.asarray(raw_counts, float)[m]
    bkg_w = np.asarray(bkg_counts, float)[m]
    tx, a, b = _tx_core(tcw, raw_w - bkg_w, frac)
    # WINDOW-TRUNCATION flag: t5/t95 landing within one bin of the search-window
    # edge means the duration is bounded by our approved window, not by the
    # burst -- a LOWER LIMIT, and not comparable to a catalog T90 (T9/D4).
    _dtb = float(np.median(np.diff(tcw))) if len(tcw) > 1 else 0.0
    truncated = bool(np.isfinite(a) and np.isfinite(b) and
                     ((a - tcw[0]) <= _dtb or (tcw[-1] - b) <= _dtb))
    rng = np.random.default_rng(int(seed) & 0xFFFFFFFF)
    lam = np.maximum(raw_w, 0.0)          # RAW rate is >= 0 by construction
    vals = []
    for _ in range(int(n_mc)):
        v, _a, _b = _tx_core(tcw, rng.poisson(lam) - bkg_w, frac)
        if np.isfinite(v):
            vals.append(v)
    err = float(np.std(vals)) if len(vals) >= 50 else np.nan
    return tx, err, a, b, truncated


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
    # --- A4 (Codex 2026-08-13): recompute T90/T50 with the audited estimator.
    # `tot` is the RAW rate and `bkg` the fitted background rate, both on `tc`;
    # counts = rate * dt.  Deterministic per-trigger seed (not one global seed).
    _seed = abs(hash(trig)) % (2 ** 32)
    _raw_c, _bkg_c = tot * dt, bkg * dt
    _t90, _t90e, _a90, _b90, _trunc90 = _tx_with_mc(tc, _raw_c, _bkg_c, src, 0.90, 1000, _seed)
    _t50, _t50e, _a50, _b50, _trunc50 = _tx_with_mc(tc, _raw_c, _bkg_c, src, 0.50, 1000, _seed + 1)
    if np.isfinite(_t90):
        t90 = (_t90, _t90e, _a90, _b90)
    if np.isfinite(_t50):
        t50 = (_t50, _t50e, _a50, _b50)
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
        "T90_WINDOW_TRUNCATED": bool(_trunc90),
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

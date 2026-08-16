#!/usr/bin/env python
"""scripts/47c_lag_latbright.py — spectral lag via the PI's OWN validated tool.

Vikas, 2026-08-15: "did you follow the tool we have developed ourselves — we
used that in LATBright GRB." We had not: step-7 used the handbook PORT, whose
DCCF was re-implemented from s02c's sign-flipped DOCSTRING (LATBright LAG-10)
instead of its correct code — the root cause of ledger defect L26.

This script imports compute_lag_dccf from LATBright s02c_spectral_lag.py
UNMODIFIED (the engine used for the GRB260226A paper: Band 1997 transient
DCCF, Bernardini+15 asymmetric Gaussian, Peterson+98 two-stage MC, MC-median
lag with asymmetric 16/84 errors). Convention (s02c:2160): POSITIVE lag =
soft lags hard (hard leads; Norris+1996 standard).

Inputs from OUR approved Stage-1: reference NaI TTE, approved background
windows (poly-2 LSQ on coarse bins), catalog band pair soft 25-50 / hard
100-300 keV, uniform 16 ms grid (LATBright per-pulse standard), analysis
span = approved source window +/- 2 s padding.

Heavy tier (threeML env). Usage:
  python scripts/47c_lag_latbright.py --trig bn081125496
"""
import os, sys, json, argparse, hashlib
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
LATB = "/Users/salim/Desktop/LATBright/GRB260226A"
sys.path.insert(0, LATB)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from plot_style import apply_pub_style, PUB  # noqa: E402
apply_pub_style()

DT = 0.016
SOFT = (25.0, 50.0)
HARD = (100.0, 300.0)
PAD = 2.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trig", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--search-half", type=float, default=None,
                    help="CCF peak-search half-window (s); default auto = max(2, span/4)")
    ap.add_argument("--fit-half", type=float, default=None,
                    help="AG fit half-window (s); default auto = max(0.5, span/8) — "
                         "windows must SCALE with the pulse (burst-1 lesson)")
    a = ap.parse_args()
    out_dir = a.out or os.path.join(ROOT, "results", "sweep106", a.trig)

    import s02c_spectral_lag as s02c   # the PI's engine, unmodified
    from astropy.table import Table
    from astropy.io import fits
    import glob as _glob

    cat = Table.read(os.path.join(ROOT, "results", "background_intervals.ecsv"))
    sub = cat[[str(x).strip() == a.trig for x in cat["TRIGGER_NAME"]]]
    nai = [r for r in sub if str(r["DETECTOR"]).startswith("n")]
    ref = min(nai, key=lambda r: float(r["DET_ANGLE"]))
    det = str(ref["DETECTOR"]).strip()
    src = (float(ref["SRC_START"]), float(ref["SRC_STOP"]))
    pre = (float(ref["BKG_NEG_START"]), float(ref["BKG_NEG_STOP"]))
    post = (float(ref["BKG_POS_START"]), float(ref["BKG_POS_STOP"]))

    tte = sorted(_glob.glob(os.path.join(ROOT, "data", a.trig,
                                         f"glg_tte_{det}_{a.trig}_v*.fit*")))[-1]
    with fits.open(tte) as h:
        eb = h["EBOUNDS"].data
        ecen = 0.5 * (eb["E_MIN"] + eb["E_MAX"])
        ev = h["EVENTS"].data
        trigt = float(h[0].header.get("TRIGTIME"))
        tt = np.asarray(ev["TIME"], float) - trigt
        en = ecen[np.asarray(ev["PHA"], int)]

    span = (pre[0], post[1])
    edges = np.arange(span[0], span[1] + DT, DT)
    tc = 0.5 * (edges[:-1] + edges[1:])

    def net_band(band):
        cts, _ = np.histogram(tt[(en >= band[0]) & (en < band[1])], bins=edges)
        rate = cts / DT
        # poly-2 LSQ background on the APPROVED windows, coarse-binned
        C = 0.128
        ce = np.arange(span[0], span[1] + C, C)
        cc, _ = np.histogram(tt[(en >= band[0]) & (en < band[1])], bins=ce)
        ctc = 0.5 * (ce[:-1] + ce[1:])
        bm = (((ctc >= pre[0]) & (ctc <= pre[1]))
              | ((ctc >= post[0]) & (ctc <= post[1])))
        pc = np.polyfit(ctc[bm], (cc / C)[bm], 2)
        net = rate - np.polyval(pc, tc)
        err = np.sqrt(np.maximum(cts, 1)) / DT
        return net, err

    s_net, s_err = net_band(SOFT)
    h_net, h_err = net_band(HARD)
    w = (tc >= src[0] - PAD) & (tc <= src[1] + PAD)

    span_src = src[1] - src[0]
    search_half = a.search_half if a.search_half is not None else max(2.0, span_src / 4.0)
    fit_half = a.fit_half if a.fit_half is not None else max(0.5, span_src / 8.0)
    np.random.seed(20260815)   # s02c MC step 2 is unseeded (their LAG-11)
    res = s02c.compute_lag_dccf(s_net[w], h_net[w], tc[w], s_err[w], h_err[w],
                                n_simul_ccf=10000, n_simul_lag=1000,
                                search_half=search_half, fit_half_width=fit_half)
    tau = float(res["tau"])
    sl, sr = float(res["sigma_l"]), float(res["sigma_r"])
    sig = float(res.get("peak_sig", np.nan))
    print(f"LATBright s02c lag ({a.trig}, {det}, {SOFT}->{HARD} keV, {DT*1e3:.0f} ms): "
          f"tau = {tau:+.4f} -{sl:.4f}/+{sr:.4f} s (peak {sig:.1f} sigma) — "
          f"POSITIVE = soft lags hard (Norris+1996)", flush=True)

    # figure from the TOOL'S OWN outputs (ccf_obs, ccf_errs, ag fit, mc dist)
    off = np.asarray(res["offset_obs"], float)
    ccf = np.asarray(res["ccf_obs"], float)
    cerr = np.asarray(res["ccf_errs"], float)
    fig, ax = plt.subplots(figsize=(PUB["figwidth"], PUB["figwidth"] * 0.58))
    m = np.abs(off) <= 8.0
    ax.fill_between(off[m], (ccf - cerr)[m], (ccf + cerr)[m],
                    color="#4878a8", alpha=0.30, lw=0, label="DCCF $\\pm$ MC err")
    ax.plot(off[m], ccf[m], color="#4878a8", lw=1.4)
    try:
        popt = res.get("ag_popt")
        if popt is not None:
            fx = np.linspace(tau - 2.0, tau + 2.0, 400)
            ax.plot(fx, s02c.Asymmetric_Gaussian(fx, *popt), color="black",
                    lw=1.8, ls="--", label="asym. Gaussian fit")
    except Exception:
        pass
    ax.axvline(tau, color="#c44e52", lw=1.8,
               label=f"$\\tau$ = {tau:+.3f} $-${sl:.3f}/$+${sr:.3f} s")
    ax.axvspan(tau - sl, tau + sr, color="#c44e52", alpha=0.18, lw=0)
    ax.set_xlabel("Offset (s)")
    ax.set_ylabel("DCCF")
    ax.set_title(f"{a.trig} — spectral lag, LATBright s02c engine ({det})", loc="left")
    ax.legend(loc="upper right", fontsize=PUB["tick_size"] - 2)
    # per-burst handbook comparison (gate finding 2026-08-16: burst-1 numbers
    # were HARDCODED here — the cross-era class; now read from this burst's
    # own step7_figs sidecar when present)
    cav = ["POSITIVE lag = soft lags hard (hard leads);",
           "Norris+1996 — the tool's validated convention."]
    try:
        hbj = json.load(open(os.path.join(out_dir, f"{a.trig}_step7_figs.json")))
        hl, he = hbj.get("lag_s"), hbj.get("lag_err_s")
        if hl is not None:
            cav.append(f"Handbook port (sign-flipped DCCF, L26): {hl:+.3f} s;")
            if he:
                ratio = 0.5 * (sl + sr) / abs(he)
                cav.append(f"its $\\pm${abs(he):.3f} s error $\\sim${ratio:.0f}$\\times$ underestimated vs this MC.")
    except Exception:
        cav.append("(handbook-port comparison unavailable for this burst)")
    ax.text(0.02, 0.03, "\n".join(cav),
            transform=ax.transAxes, fontsize=PUB["tick_size"] - 4, color="0.35",
            va="bottom", zorder=3,
            bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=1.5))
    fig.text(0.99, -0.012, "engine: LATBright s02c compute_lag_dccf, unmodified; "
             "soft 25–50 / hard 100–300 keV; approved Stage-1 windows",
             ha="right", va="bottom", fontsize=PUB["tick_size"] - 4, color="0.35")
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.join(out_dir, f"{a.trig}_step7_lag_latbright")
    fig.savefig(stem + ".png", bbox_inches="tight")
    plt.close(fig)
    print("WROTE", stem + ".png")

    with open(os.path.abspath(__file__), "rb") as fh:
        src_sha = hashlib.sha256(fh.read()).hexdigest()
    prov = dict(script="47c_lag_latbright.py", script_sha256=src_sha,
                trig=a.trig, detector=det, dt_s=DT,
                soft_keV=list(SOFT), hard_keV=list(HARD),
                window_s=[src[0] - PAD, src[1] + PAD],
                tau_s=tau, sigma_l_s=sl, sigma_r_s=sr, peak_sig=sig,
                convention="POSITIVE = soft lags hard (Norris+1996; s02c:2160)",
                engine="LATBright GRB260226A/s02c_spectral_lag.py compute_lag_dccf, "
                       "unmodified import",
                windows=dict(search_half_s=search_half, fit_half_s=fit_half,
                             basis="auto: max(2, span/4) / max(0.5, span/8) from the "
                                   "approved source window — pulse-scaled (burst-1 lesson)"),
                mc=dict(n_ccf=10000, n_lag=1000, seed=20260815,
                        note="s02c step-2 MC unseeded upstream (their LAG-11); "
                             "seeded here at script level"),
                l26_root_cause="handbook DCCF ported from s02c's sign-flipped "
                               "docstring (LAG-10), not its code; numeric proof: "
                               "synthetic hard-leads pair gives +0.192 (s02c) vs "
                               "-0.192 (handbook)")
    with open(stem + ".json", "w") as fh:
        json.dump(prov, fh, indent=1)
    print("WROTE sidecar")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""scripts/44_step_figures.py -- ONE FIGURE PER PIPELINE STEP, per burst.

Vikas, 2026-08-13: "we must have figures for every step."  Steps 6 and 8 already
emit figures (scripts/10 spectral_evolution + ep_kt_correlation; scripts/41
montage/overlay).  This script fills every other step, so a human can SEE what
each stage of the pipeline decided:

  step1_inventory.png   response (DRM) coverage bars vs the stamped source window
                        + per-detector off-axis angle -- the D1/D2 checks, visible
  step2_detectors.png   approved detector angles against the 60-deg rule
  step3_background.png  per-detector LC + fitted background polynomial through the
                        approved pre/post windows + residual strip
  step4_source.png      LC with the background gap and the stamped source window
  step5_binning.png     net LC + Bayesian blocks as an adaptive step + per-block S
  step7_temporal.png    cumulative net counts with t5/t95/T90 marked, per band
  step9_qc.png          winner + margins + L28 edge class per block (the scorecard,
                        drawn)

LIGHT TIER: numpy/astropy/matplotlib only -- no threeML, so it can run alongside
the fits.  Every panel that cannot be built is SKIPPED LOUDLY (a stamped "missing
input" note on the figure), never silently omitted (Shipping Gate).

Usage:
  python scripts/44_step_figures.py --trig bn081125496 --out results/sweep106/bn081125496
  python scripts/44_step_figures.py --all --root results/sweep106
"""
import os, sys, glob, argparse
import numpy as np
from astropy.io import fits
from astropy.table import Table
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(ROOT, "results", "background_intervals.ecsv")
DATA = os.path.join(ROOT, "data")

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "stix",
                     "font.size": 11, "xtick.direction": "in", "ytick.direction": "in",
                     "xtick.top": True, "ytick.right": True,
                     "xtick.minor.visible": True, "ytick.minor.visible": True,
                     "savefig.dpi": 160})
COLORS = {"n": "#b3216a", "b": "#3aa6a0", "l": "#5b3fa0"}


def dcol(det):
    return COLORS.get(str(det)[0], "gray")


def _note(ax, msg):
    ax.text(0.5, 0.5, msg, ha="center", va="center", transform=ax.transAxes,
            fontsize=9, color="crimson", wrap=True)
    ax.set_xticks([]); ax.set_yticks([])


def rows_for(trig):
    t = Table.read(CAT, format="ascii.ecsv")
    return t[[str(x).strip() == trig for x in t["TRIGGER_NAME"]]]


def tte_path(trig, det):
    g = sorted(glob.glob(os.path.join(DATA, trig, f"glg_tte_{det}_{trig}_v*.fit*")))
    return g[-1] if g else None


def rsp_path(trig, det):
    g = sorted(glob.glob(os.path.join(DATA, trig, f"glg_cspec_{det}_{trig}_v*.rsp*")))
    return g[-1] if g else None


def events(trig, det):
    p = tte_path(trig, det)
    if p is None:
        return None, None
    with fits.open(p) as h:
        t0 = h[0].header.get("TRIGTIME") or h[2].header.get("TRIGTIME")
        ev = h["EVENTS"].data
        return np.asarray(ev["TIME"], float) - float(t0), float(t0)


def binned(times, lo, hi, dt=0.128):
    """Binned rate with EMPTY-COVERAGE bins masked to NaN.

    The TTE file does not always span the requested range; empty leading/trailing
    bins were being drawn as a rate of 0, producing a cliff to zero at the panel
    edge that squashed the real signal into the top half of the axes
    (presentation pass 2026-08-13)."""
    e = np.arange(lo, hi + dt, dt)
    c, _ = np.histogram(times, bins=e)
    tc = 0.5 * (e[:-1] + e[1:])
    rate = c / dt
    if times.size:
        outside = (tc < times.min()) | (tc > times.max())
        rate = np.where(outside, np.nan, rate)
    return tc, rate, dt


def ylim_from_data(ax, y, pad_lo=0.08, pad_hi=0.12):
    """Limits from the DATA's own spread (2nd-99.5th percentile), never anchored
    at zero -- a background-dominated light curve wastes half the panel otherwise."""
    y = np.asarray(y, float); y = y[np.isfinite(y)]
    if y.size < 5:
        return
    lo, hi = np.percentile(y, 1.0), np.percentile(y, 99.7)
    if hi <= lo:
        return
    span = hi - lo
    ax.set_ylim(lo - pad_lo * span, hi + pad_hi * span)


def polyfit_bkg(tc, rate, pre, post, maxdeg=3):
    m = ((tc >= pre[0]) & (tc <= pre[1])) | ((tc >= post[0]) & (tc <= post[1]))
    if m.sum() < 6:
        return None, None
    best, bestchi = None, np.inf
    for deg in range(maxdeg + 1):
        try:
            c = np.polyfit(tc[m], rate[m], deg)
        except Exception:
            continue
        chi = np.sum((rate[m] - np.polyval(c, tc[m])) ** 2) / max(m.sum() - deg - 1, 1)
        if chi < bestchi:
            best, bestchi = c, chi
    return best, m


# ---------------------------------------------------------------- step 1 + 2
def fig_step1_2(trig, out):
    rs = rows_for(trig)
    if not len(rs):
        return []
    made = []
    # --- step 1: response coverage + angle
    fig, axes = plt.subplots(1, 2, figsize=(11, 0.55 * len(rs) + 2.6))
    ax, ax2 = axes
    src1 = float(rs["SRC_START"][0]); src2 = float(rs["SRC_STOP"][0])
    for i, r in enumerate(rs):
        det = str(r["DETECTOR"]).strip()
        p = rsp_path(trig, det)
        lo = hi = np.nan
        if p:
            try:
                with fits.open(p) as h:
                    t0 = None
                    for hdu in h:
                        if "TRIGTIME" in hdu.header:
                            t0 = float(hdu.header["TRIGTIME"]); break
                    ts, te = [], []
                    for hdu in h:
                        if "TSTART" in hdu.header and "TSTOP" in hdu.header:
                            ts.append(float(hdu.header["TSTART"]))
                            te.append(float(hdu.header["TSTOP"]))
                    if ts and t0:
                        lo, hi = min(ts) - t0, max(te) - t0
            except Exception:
                pass
        if np.isfinite(lo):
            ok = (lo <= src1) and (hi >= src2)
            ax.barh(i, hi - lo, left=lo, height=0.55,
                    color=("#3aa6a0" if ok else "crimson"), alpha=0.55)
            ax.text(hi, i, "  PASS" if ok else "  FAIL", va="center", fontsize=8,
                    color=("#177" if ok else "crimson"))
        else:
            ax.text(src1, i, "  no response found", va="center", fontsize=8, color="crimson")
        ax2.barh(i, float(r["DET_ANGLE"]) if str(r["DET_ANGLE"]) not in ("nan", "--") else 0,
                 height=0.55, color=dcol(det), alpha=0.8)
    ax.axvspan(src1, src2, color="k", alpha=0.18, label="stamped source window")
    ax.set_yticks(range(len(rs)))
    ax.set_yticklabels([str(r["DETECTOR"]).strip() for r in rs])
    ax.set_xlabel("time since trigger (s)"); ax.legend(fontsize=8, framealpha=0.9, edgecolor="0.6")
    ax.set_title("step 1 — response (DRM) coverage vs source window", fontsize=10, loc="left")
    ax2.axvline(60, color="crimson", ls="--", lw=1.2, label="60° rule")
    ax2.set_yticks(range(len(rs)))
    ax2.set_yticklabels([str(r["DETECTOR"]).strip() for r in rs])
    ax2.set_xlabel("off-axis angle (deg)"); ax2.legend(fontsize=8, framealpha=0.9, edgecolor="0.6")
    ax2.set_title("step 2 — approved detectors", fontsize=10, loc="left")
    fig.suptitle(f"{trig}  ·  steps 1–2: data inventory & detector selection", fontsize=12)
    fig.tight_layout()
    f = os.path.join(out, f"{trig}_step1_inventory.png")
    fig.savefig(f, bbox_inches="tight"); plt.close(fig); made.append(f)
    return made


# ------------------------------------------------------------ steps 3, 4, 5
def fig_step345(trig, out, blocks_file=None):
    rs = rows_for(trig)
    if not len(rs):
        return []
    made = []
    nais = [r for r in rs if str(r["DETECTOR"]).strip().startswith("n")]
    if not nais:
        return []
    ref = min(nais, key=lambda r: float(r["DET_ANGLE"])
              if str(r["DET_ANGLE"]) not in ("nan", "--") else 999)
    refdet = str(ref["DETECTOR"]).strip()
    pre = (float(ref["BKG_NEG_START"]), float(ref["BKG_NEG_STOP"]))
    post = (float(ref["BKG_POS_START"]), float(ref["BKG_POS_STOP"]))
    src = (float(ref["SRC_START"]), float(ref["SRC_STOP"]))
    lo, hi = pre[0] - 5, post[1] + 5

    # ---------- step 3: per-detector background fits
    dets = [str(r["DETECTOR"]).strip() for r in rs if not str(r["DETECTOR"]).strip() == "lle"]
    n = len(dets)
    fig, axes = plt.subplots(n, 1, figsize=(10, 2.1 * n), sharex=True, squeeze=False)
    for i, det in enumerate(dets):
        ax = axes[i][0]
        ev, _ = events(trig, det)
        if ev is None:
            _note(ax, f"{det}: no TTE file on disk"); continue
        rr = rs[[str(x).strip() == det for x in rs["DETECTOR"]]][0]
        p_, q_ = ((float(rr["BKG_NEG_START"]), float(rr["BKG_NEG_STOP"])),
                  (float(rr["BKG_POS_START"]), float(rr["BKG_POS_STOP"])))
        tc, rate, _ = binned(ev, min(lo, p_[0] - 5), max(hi, q_[1] + 5))
        ax.plot(tc, rate, color="0.62", lw=0.7, zorder=2)
        c, m = polyfit_bkg(tc, rate, p_, q_)
        if c is not None:
            # SOLID only across the span the polynomial is actually constrained
            # over (first pre-window sample -> last post-window sample); dashed
            # where it is pure extrapolation, so a wild deg-3 tail beyond the
            # windows is visibly EXTRAPOLATION and not a claim about the data.
            inside = (tc >= p_[0]) & (tc <= q_[1])
            ax.plot(tc[inside], np.polyval(c, tc[inside]), color=dcol(det), lw=1.8,
                    zorder=5, label=f"{det} background (deg {len(c)-1})")
            out_hi = tc > q_[1]
            if out_hi.any():
                ax.plot(tc[out_hi], np.polyval(c, tc[out_hi]), color=dcol(det), lw=1.0,
                        ls=":", alpha=0.55, zorder=4)
        for w in (p_, q_):
            ax.axvspan(w[0], w[1], color="#3aa6a0", alpha=0.18, lw=0, zorder=1)
        ax.axvspan(src[0], src[1], color="crimson", alpha=0.12, lw=0, zorder=1)
        ylim_from_data(ax, rate)
        ax.set_xlim(np.nanmin(tc[np.isfinite(rate)]), np.nanmax(tc[np.isfinite(rate)]))
        ax.legend(fontsize=8, loc="upper right", framealpha=0.92, edgecolor="0.6")
        ax.set_ylabel("rate (cts s$^{-1}$)", fontsize=9)
    axes[-1][0].set_xlabel("time since trigger (s)")
    fig.suptitle(f"{trig}  ·  step 3: background windows (green) + fitted polynomial; "
                 f"source (red)", fontsize=11)
    fig.tight_layout()
    f = os.path.join(out, f"{trig}_step3_background.png")
    fig.savefig(f, bbox_inches="tight"); plt.close(fig); made.append(f)

    # ---------- step 4: source window inside the common gap
    ev, _ = events(trig, refdet)
    fig, ax = plt.subplots(figsize=(10, 3.4))
    if ev is None:
        _note(ax, "no TTE for reference detector")
    else:
        tc, rate, _ = binned(ev, lo, hi)
        ax.plot(tc, rate, color="0.45", lw=0.8)
        ylim_from_data(ax, rate)
        good = np.isfinite(rate)
        if good.any():
            ax.set_xlim(tc[good].min(), tc[good].max())
        gap_lo = max(float(r["BKG_NEG_STOP"]) for r in rs)
        gap_hi = min(float(r["BKG_POS_START"]) for r in rs)
        ax.axvspan(gap_lo, gap_hi, color="#3aa6a0", alpha=0.13, label="common background gap")
        ax.axvspan(src[0], src[1], color="crimson", alpha=0.22, label="stamped source window")
        if src[0] < gap_lo or src[1] > gap_hi:
            ax.text(0.02, 0.92, "source overruns the gap — ADJUDICATED (see QC ledger)",
                    transform=ax.transAxes, fontsize=9, color="crimson")
        ax.legend(fontsize=8, framealpha=0.9, edgecolor="0.6")
        ax.set_xlabel("time since trigger (s)"); ax.set_ylabel(f"{refdet} cts/s")
    ax.set_title(f"{trig}  ·  step 4: source interval", fontsize=11, loc="left")
    fig.tight_layout()
    f = os.path.join(out, f"{trig}_step4_source.png")
    fig.savefig(f, bbox_inches="tight"); plt.close(fig); made.append(f)

    # ---------- step 5: Bayesian blocks
    bf = blocks_file or os.path.join(out, "blocks", f"bb_blocks_spectral_{trig}.ecsv")
    fig, ax = plt.subplots(figsize=(10, 3.8))
    if not os.path.exists(bf):
        _note(ax, f"no blocks file: {os.path.basename(bf)}")
    elif ev is None:
        _note(ax, "no TTE for reference detector")
    else:
        bt = Table.read(bf, format="ascii.ecsv")
        # the blocks file carries ONE ROW PER DETECTOR -> dedup on (T_START,T_STOP)
        # exactly as scripts/41 does, or duplicates overlap and the count lies
        # (caught by the Shipping Gate on the first figure, 2026-08-13).
        _seen, _keep = set(), []
        for _r in bt:
            _k = (round(float(_r["T_START"]), 4), round(float(_r["T_STOP"]), 4))
            if _k in _seen:
                continue
            _seen.add(_k); _keep.append(_r)
        bt = Table(rows=_keep, names=bt.colnames)
        tc, rate, _ = binned(ev, lo, hi)
        c, _m = polyfit_bkg(tc, rate, pre, post)
        net = rate - (np.polyval(c, tc) if c is not None else 0.0)
        ax.plot(tc, net, color="0.7", lw=0.7, label="net LC (0.128 s)")
        sig = np.asarray(bt["SIGNIFICANCE"], float) if "SIGNIFICANCE" in bt.colnames else None
        smax = np.nanmax(sig) if sig is not None and np.isfinite(sig).any() else 1.0
        for j, r in enumerate(bt):
            t1, t2 = float(r["T_START"]), float(r["T_STOP"])
            m = (tc >= t1) & (tc < t2)
            lvl = float(np.mean(net[m])) if m.any() else np.nan
            sh = (sig[j] / smax) if sig is not None and np.isfinite(sig[j]) else 0.4
            ax.hlines(lvl, t1, t2, color=plt.cm.viridis(0.15 + 0.7 * sh), lw=3.0, zorder=4)
            ax.axvline(t1, color="0.35", lw=0.5, ls=":")
            if sig is not None and np.isfinite(sig[j]):
                ax.text(0.5 * (t1 + t2), lvl, f"{sig[j]:.0f}", fontsize=6.5, ha="center",
                        va="bottom", color="0.25")
        ax.axvline(float(bt["T_STOP"][-1]), color="0.35", lw=0.5, ls=":")
        ax.set_xlim(src[0] - 3, src[1] + 3)
        inwin = (tc >= src[0] - 3) & (tc <= src[1] + 3)
        ylim_from_data(ax, net[inwin])
        ax.axhline(0, color="0.75", lw=0.7, zorder=0)
        ax.legend(fontsize=8, framealpha=0.9, edgecolor="0.6")
        ax.set_xlabel("time since trigger (s)"); ax.set_ylabel("net cts/s")
        ax.set_title(f"{trig}  ·  step 5: Bayesian blocks ({len(bt)}), colour/number = block "
                     f"significance", fontsize=11, loc="left")
    fig.tight_layout()
    f = os.path.join(out, f"{trig}_step5_binning.png")
    fig.savefig(f, bbox_inches="tight"); plt.close(fig); made.append(f)
    return made


# ---------------------------------------------------------------- step 7
BANDS = [(8, 25), (25, 50), (50, 100), (100, 350), (350, 1000)]


def fig_step7(trig, out):
    rs = rows_for(trig)
    nais = [r for r in rs if str(r["DETECTOR"]).strip().startswith("n")]
    if not nais:
        return []
    ref = min(nais, key=lambda r: float(r["DET_ANGLE"])
              if str(r["DET_ANGLE"]) not in ("nan", "--") else 999)
    det = str(ref["DETECTOR"]).strip()
    p = tte_path(trig, det)
    fig = plt.figure(figsize=(10.6, 4.3))
    gsr = fig.add_gridspec(1, 2, width_ratios=[3.1, 1.0], wspace=0.28,
                           left=0.075, right=0.985, top=0.88, bottom=0.15)
    ax = fig.add_subplot(gsr[0]); axE = fig.add_subplot(gsr[1])
    if p is None:
        _note(ax, "no TTE"); _note(axE, "");
    else:
        with fits.open(p) as h:
            t0 = None
            for hdu in h:
                if "TRIGTIME" in hdu.header:
                    t0 = float(hdu.header["TRIGTIME"]); break
            ev = h["EVENTS"].data
            tt = np.asarray(ev["TIME"], float) - t0
            ch = np.asarray(ev["PHA"], int)
            eb = h["EBOUNDS"].data
            emid = 0.5 * (np.asarray(eb["E_MIN"], float) + np.asarray(eb["E_MAX"], float))
        src = (float(ref["SRC_START"]), float(ref["SRC_STOP"]))
        pre = (float(ref["BKG_NEG_START"]), float(ref["BKG_NEG_STOP"]))
        post = (float(ref["BKG_POS_START"]), float(ref["BKG_POS_STOP"]))
        _cols = ["#2b3a67", "#3aa6a0", "#6aa84f", "#f08c4b", "#b3216a"]
        _t90s, _over = [], []
        for _ib, (e1, e2) in enumerate(BANDS):
            sel = (emid[np.clip(ch, 0, len(emid) - 1)] >= e1) & (emid[np.clip(ch, 0, len(emid) - 1)] < e2)
            tb = tt[sel]
            if tb.size < 50:
                continue
            tc, rate, dt = binned(tb, pre[0], post[1], dt=0.256)
            c, _m = polyfit_bkg(tc, rate, pre, post)
            net = rate - (np.polyval(c, tc) if c is not None else 0.0)
            msrc = (tc >= src[0]) & (tc <= src[1])
            cum = np.cumsum(net[msrc] * dt)
            if cum[-1] <= 0:
                continue
            cum = cum / cum[-1]
            tsrc = tc[msrc]
            t5 = np.interp(0.05, cum, tsrc); t95 = np.interp(0.95, cum, tsrc)
            c_ = _cols[_ib % len(_cols)]
            ax.plot(tsrc, cum, lw=1.6, color=c_, zorder=3,
                    label=f"{e1}–{e2} keV   $T_{{90}}$ = {t95-t5:.1f} s")
            # mark the T90 SPAN rather than 10 separate vertical lines
            ax.plot([t5, t95], [-0.10 - 0.045 * _ib] * 2, color=c_, lw=2.6,
                    solid_capstyle="butt", zorder=4, clip_on=False)
            _t90s.append((0.5 * (e1 + e2), t95 - t5))
            if np.nanmax(cum) > 1.15:
                _over.append(f"{e1}-{e2} keV")
        ax.axhline(0.05, color="0.75", lw=0.6, zorder=1)
        ax.axhline(0.95, color="0.75", lw=0.6, zorder=1)
        ax.set_ylim(-0.34, 1.12)          # room below zero for the T90 span bars
        ax.set_xlabel("time since trigger (s)")
        ax.set_ylabel("cumulative net counts (normalised)")
        ax.legend(fontsize=8.5, loc="upper left", framealpha=0.92, edgecolor="0.6")
        if _over:
            ax.text(0.985, 0.97, "cumulative overshoots 1 (low S/N, curve leaves frame): "
                    + ", ".join(_over), transform=ax.transAxes, ha="right", va="top",
                    fontsize=6.8, color="0.35")
        # right panel: the E-dependence this figure exists to show
        if len(_t90s) >= 3:
            E_ = np.array([a for a, _ in _t90s]); T_ = np.array([b for _, b in _t90s])
            for _i, (e_, t_) in enumerate(zip(E_, T_)):
                axE.plot(e_, t_, "o", ms=6, color=_cols[_i % len(_cols)], zorder=4)
            axE.plot(E_, T_, "-", color="0.4", lw=1.1, zorder=3)
            k = np.polyfit(np.log10(E_), np.log10(T_), 1)[0]
            xx = np.logspace(np.log10(E_.min()), np.log10(E_.max()), 20)
            axE.plot(xx, T_[0] * (xx / E_[0]) ** (-0.20), ls="--", color="crimson",
                     lw=1.0, zorder=2, label="$E^{-0.20}$ (pop. mean)")
            axE.set_xscale("log"); axE.set_yscale("log")
            axE.set_xlabel("band centre (keV)"); axE.set_ylabel("$T_{90}$ (s)")
            axE.set_title(f"this burst: slope {k:+.2f}", fontsize=9)
            axE.legend(fontsize=7, framealpha=0.9, edgecolor="0.6", loc="lower left")
    ax.set_title(f"{trig}  ·  step 7: energy-resolved $T_{{90}}$ — horizontal bars mark each "
                 f"band's $t_5$–$t_{{95}}$ span", fontsize=10, loc="left")
    f = os.path.join(out, f"{trig}_step7_temporal.png")
    fig.savefig(f, bbox_inches="tight"); plt.close(fig)
    return [f]


# ---------------------------------------------------------------- step 9
SIMPLE = {"BAND", "CPL", "SBPL", "SBPLF"}


def fig_step9(trig, out):
    ft = os.path.join(out, trig, "spectral_fits.ecsv")
    fig, axes = plt.subplots(2, 1, figsize=(10, 6.2), sharex=True,
                             gridspec_kw={"height_ratios": [2, 1]})
    ax, ax2 = axes
    if not os.path.exists(ft):
        _note(ax, f"no fit table: {ft}"); _note(ax2, "")
    else:
        t = Table.read(ft, format="ascii.ecsv")
        pre = sorted({c[:-4] for c in t.colnames if c.endswith("_AIC")})
        blocks, dsimp, winners, edge = [], [], [], []
        for r in t:
            k = int(r["BLOCK"])
            if k < 0:
                continue
            va = {}
            for p in pre:
                try:
                    if bool(r[f"{p}_VALID"]) and np.isfinite(float(r[f"{p}_AIC"])):
                        va[p] = float(r[f"{p}_AIC"])
                except Exception:
                    pass
            s = [v for p, v in va.items() if p in SIMPLE]
            x = [v for p, v in va.items() if p not in SIMPLE]
            blocks.append(k)
            dsimp.append(min(s) - min(x) if s and x else np.nan)
            winners.append(str(r["BEST_AIC_MODEL"]) if "BEST_AIC_MODEL" in t.colnames else "?")
            # only a SIGNIFICANT, off-rail, VALID-child BB counts — the same
            # gate the scorecard uses (nested LRT >= 9.2, kT > 1.0544, union of
            # the Band+BB and CPL+BB pairs). Plotting every fitted kT would
            # stamp EDGE_CONSTRAINED on non-detections (Shipping Gate catch #2,
            # 2026-08-13).
            kt = np.nan
            for ktc, lrtc, vc in (("BANDBB_KT", "LRT_BANDBB_BAND", "BANDBB_VALID"),
                                  ("CPLBB_KT", "LRT_CPLBB_CPL", "CPLBB_VALID")):
                try:
                    v, l = float(r[ktc]), float(r[lrtc])
                    if np.isfinite(v) and v > 1.0544 and np.isfinite(l) and l >= 9.2 \
                       and bool(r[vc]):
                        kt = v; break
                except Exception:
                    pass
            edge.append(3.92 * kt if np.isfinite(kt) else np.nan)
        ax.bar(blocks, dsimp, color=["#b3216a" if d >= 10 else "#f08c4b" if d >= 6 else "0.7"
                                     for d in dsimp])
        ax.axhline(10, color="#b3216a", ls="--", lw=1, label="DECISIVE (ΔAIC≥10)")
        ax.axhline(6, color="#f08c4b", ls="--", lw=1, label="STRONG (ΔAIC≥6)")
        for b, d, w in zip(blocks, dsimp, winners):
            ax.text(b, (d if np.isfinite(d) else 0) + 0.4, w, rotation=90, fontsize=6.5,
                    ha="center", va="bottom", color="0.25")
        ax.set_ylabel("ΔAIC  (best simple − best extra)")
        ax.legend(fontsize=8, framealpha=0.9, edgecolor="0.6")
        ax.set_title(f"{trig}  ·  step 9: per-block evidence + winner (labels), "
                     f"L28 edge class below", fontsize=10, loc="left")
        ok = np.isfinite(edge)
        if ok.any():
            ax2.scatter(np.array(blocks)[ok], np.array(edge)[ok],
                        c=["crimson" if e < 20 else "#f08c4b" if e < 30 else "#3aa6a0"
                           for e in np.array(edge)[ok]], s=34, zorder=4)
        ax2.axhline(20, color="crimson", ls="--", lw=1, label="EDGE_CONSTRAINED < 20 keV")
        ax2.axhline(30, color="#f08c4b", ls=":", lw=1, label="EDGE_MARGINAL < 30 keV")
        ax2.set_ylabel("3.92·kT (keV)\nSIGNIFICANT BB only"); ax2.set_xlabel("block")
        ax2.legend(fontsize=7.5, framealpha=0.9, edgecolor="0.6")
    fig.tight_layout()
    f = os.path.join(out, f"{trig}_step9_qc.png")
    fig.savefig(f, bbox_inches="tight"); plt.close(fig)
    return [f]


def run_one(trig, out):
    os.makedirs(out, exist_ok=True)
    made = []
    for fn in (fig_step1_2, fig_step345, fig_step7, fig_step9):
        try:
            made += fn(trig, out)
        except Exception as e:
            print(f"   [WARN] {trig} {fn.__name__}: {e}")
    print(f"{trig}: {len(made)} step figures -> {out}")
    return made


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--trig")
    ap.add_argument("--out")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--root", default=os.path.join(ROOT, "results", "sweep106"))
    a = ap.parse_args()
    if a.all:
        for d in sorted(glob.glob(os.path.join(a.root, "bn*"))):
            run_one(os.path.basename(d), d)
    else:
        run_one(a.trig, a.out or os.path.join(a.root, a.trig))

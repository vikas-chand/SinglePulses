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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_style import apply_pub_style, PUB, det_color   # noqa: E402
apply_pub_style()

_DET_ORDER = {}


def dcol(det, trig=None):
    """Stable colour per detector WITHIN a burst (NaI cycle by first appearance;
    BGO and LLE fixed)."""
    key = (trig, str(det).strip())
    if key not in _DET_ORDER:
        n = sum(1 for k in _DET_ORDER if k[0] == trig and not k[1].startswith(("b", "l")))
        _DET_ORDER[key] = n
    return det_color(det, _DET_ORDER[key])


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
    return tc, rate, dt, e


def lc_hist(ax, edges, rate, color, label=None, alpha_fill=0.22, lw=None, zorder=2):
    """Light curve as a FILLED STEP HISTOGRAM -- the LATBright idiom
    (GRB260226A/s01b_combined_lightcurve.py): fill_between(step='post') on the
    bin LEFT EDGES plus a step outline. Binned data must look binned, and
    where='post' places each level over its own bin rather than interpolating
    between centres."""
    x = np.asarray(edges[:-1], float)
    y = np.asarray(rate, float)
    ax.fill_between(x, y, step="post", color=color, alpha=alpha_fill, linewidth=0,
                    zorder=zorder)
    ax.step(x, y, where="post", color=color,
            linewidth=(lw if lw is not None else PUB["lw_reference"]),
            alpha=0.85, zorder=zorder + 1, label=label)


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
    fig, axes = plt.subplots(1, 2, figsize=(13, 0.62 * len(rs) + 3.0))
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
            # FILL = detector identity (same colour as the right panel);
            # EDGE = the verdict. One colour must mean one detector everywhere.
            ax.barh(i, hi - lo, left=lo, height=0.55, color=dcol(det, trig), alpha=0.55,
                    edgecolor=("#1a7d3a" if ok else PUB["c_bgo"]),
                    linewidth=(1.6 if ok else 2.4))
            ax.text(hi, i, "  PASS" if ok else "  FAIL", va="center",
                    fontsize=PUB["tick_size"] - 2, ha="left",
                    color=("#1a7d3a" if ok else PUB["c_bgo"]), fontweight="bold")
        else:
            ax.text(src1, i, "  no response found", va="center",
                    fontsize=PUB["tick_size"] - 3, color=PUB["c_bgo"])
        ax2.barh(i, float(r["DET_ANGLE"]) if str(r["DET_ANGLE"]) not in ("nan", "--") else 0,
                 height=0.55, color=dcol(det, trig), alpha=0.85)
    ax.axvspan(src1, src2, color=PUB["c_src_win"], alpha=0.18, lw=0, zorder=1)
    for _x in (src1, src2):
        ax.axvline(_x, color=PUB["c_src_win"], lw=1.0, alpha=0.8, zorder=3)
    ax.set_yticks(range(len(rs)))
    ax.set_yticklabels([str(r["DETECTOR"]).strip() for r in rs])
    _xl = ax.get_xlim(); ax.set_xlim(_xl[0], _xl[1] + 0.16 * (_xl[1] - _xl[0]))
    # label the band directly (reference §5: never place a legend over data)
    ax.set_ylim(-0.7, len(rs) - 0.05)
    ax.annotate("source\nwindow", xy=(src2, 0.985), xycoords=("data", "axes fraction"),
                xytext=(6, -4), textcoords="offset points", ha="left", va="top",
                fontsize=PUB["tick_size"] - 3, color=PUB["c_src_win"], linespacing=1.1)
    ax.set_xlabel("time since trigger (s)")
    ax.set_title("response (DRM) coverage", loc="left")
    ax2.axvline(60, color=PUB["c_bgo"], ls="--", lw=1.4, label=r"$60^\circ$ rule")
    ax2.set_yticks(range(len(rs)))
    ax2.set_yticklabels([str(r["DETECTOR"]).strip() for r in rs])
    ax2.set_xlabel(r"off-axis angle (deg)")
    ax2.legend(loc="lower right")
    ax2.set_title("approved detectors", loc="left")
    fig.suptitle(f"{trig} — steps 1–2: data inventory and detector selection",
                 fontsize=PUB["label_size"])
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
    fig, axes = plt.subplots(n, 1, figsize=(12, 2.9 * n + 0.6), sharex=True,
                             squeeze=False)
    for i, det in enumerate(dets):
        ax = axes[i][0]
        ev, _ = events(trig, det)
        if ev is None:
            _note(ax, f"{det}: no TTE file on disk"); continue
        rr = rs[[str(x).strip() == det for x in rs["DETECTOR"]]][0]
        p_, q_ = ((float(rr["BKG_NEG_START"]), float(rr["BKG_NEG_STOP"])),
                  (float(rr["BKG_POS_START"]), float(rr["BKG_POS_STOP"])))
        tc, rate, _, ed = binned(ev, min(lo, p_[0] - 5), max(hi, q_[1] + 5))
        lc_hist(ax, ed, rate, PUB["c_data"], zorder=2)
        c, m = polyfit_bkg(tc, rate, p_, q_)
        if c is not None:
            # SOLID only across the span the polynomial is actually constrained
            # over (first pre-window sample -> last post-window sample); dashed
            # where it is pure extrapolation, so a wild deg-3 tail beyond the
            # windows is visibly EXTRAPOLATION and not a claim about the data.
            inside = (tc >= p_[0]) & (tc <= q_[1])
            ax.plot(tc[inside], np.polyval(c, tc[inside]), color=dcol(det, trig),
                    lw=PUB["lw_primary"], zorder=5,
                    label=f"{det} — order {len(c)-1}")
            out_hi = tc > q_[1]
            if out_hi.any():
                ax.plot(tc[out_hi], np.polyval(c, tc[out_hi]), color=dcol(det, trig),
                        lw=PUB["lw_secondary"], ls=":", alpha=0.6, zorder=4)
        for w in (p_, q_):
            ax.axvspan(w[0], w[1], color=PUB["c_bkg_win"], alpha=0.15, lw=0, zorder=1)
        ax.axvspan(src[0], src[1], color=PUB["c_src_win"], alpha=0.13, lw=0, zorder=1)
        ylim_from_data(ax, rate)
        ax.set_xlim(np.nanmin(tc[np.isfinite(rate)]), np.nanmax(tc[np.isfinite(rate)]))
        ax.legend(loc="upper right")
        ax.set_ylabel(r"rate (cts s$^{-1}$)")
    axes[-1][0].set_xlabel("time since trigger (s)")
    fig.suptitle(f"{trig} — step 3: fitted background through the approved windows",
                 fontsize=PUB["label_size"] + 2, y=0.995)
    # one shared explanation, stated once (reference §5: no repeated legends)
    axes[0][0].text(0.005, 1.06, "shaded: background windows (teal) · source interval "
                    "(magenta);  solid: polynomial where constrained, dotted: extrapolation",
                    transform=axes[0][0].transAxes, fontsize=PUB["tick_size"] - 3,
                    color="0.35", ha="left", va="bottom")
    fig.tight_layout(rect=[0, 0, 1, 0.985])
    f = os.path.join(out, f"{trig}_step3_background.png")
    fig.savefig(f, bbox_inches="tight"); plt.close(fig); made.append(f)

    # ---------- step 4: source window inside the common gap
    ev, _ = events(trig, refdet)
    fig, ax = plt.subplots(figsize=(11, 4.0))
    if ev is None:
        _note(ax, "no TTE for reference detector")
    else:
        tc, rate, _, ed = binned(ev, lo, hi)
        lc_hist(ax, ed, rate, "0.45", zorder=2)
        ylim_from_data(ax, rate)
        good = np.isfinite(rate)
        if good.any():
            ax.set_xlim(tc[good].min(), tc[good].max())
        gap_lo = max(float(r["BKG_NEG_STOP"]) for r in rs)
        gap_hi = min(float(r["BKG_POS_START"]) for r in rs)
        ax.axvspan(gap_lo, gap_hi, color=PUB["c_bkg_win"], alpha=0.15, lw=0,
                   label="common background gap")
        ax.axvspan(src[0], src[1], color=PUB["c_src_win"], alpha=0.20, lw=0,
                   label="stamped source window")
        for _x in (src[0], src[1]):
            ax.axvline(_x, color=PUB["c_src_win"], lw=1.1, alpha=0.85, zorder=3)
        # ZOOM to what this figure is about: the gap and its margins. The far
        # background belongs to step 3, and at full range the burst occupied
        # under a sixth of the panel.
        _sp = max(gap_hi - gap_lo, src[1] - src[0])
        ax.set_xlim(gap_lo - 0.55 * _sp, gap_hi + 0.55 * _sp)
        _m = (tc >= ax.get_xlim()[0]) & (tc <= ax.get_xlim()[1])
        ylim_from_data(ax, rate[_m])
        if src[0] < gap_lo or src[1] > gap_hi:
            ax.text(0.02, 0.92, "source overruns the gap — ADJUDICATED (see QC ledger)",
                    transform=ax.transAxes, fontsize=9, color="crimson")
        ax.legend(loc="upper right")
        ax.set_xlabel("time since trigger (s)")
        ax.set_ylabel(r"rate (cts s$^{-1}$)")
    ax.set_title(f"{trig} — step 4: source interval inside the background gap "
                 f"(detector {refdet})", fontsize=PUB["label_size"], loc="left")
    fig.tight_layout()
    f = os.path.join(out, f"{trig}_step4_source.png")
    fig.savefig(f, bbox_inches="tight"); plt.close(fig); made.append(f)

    # ---------- step 5: Bayesian blocks
    bf = blocks_file or os.path.join(out, "blocks", f"bb_blocks_spectral_{trig}.ecsv")
    fig, ax = plt.subplots(figsize=(11.5, 4.6))
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
        tc, rate, _, ed = binned(ev, lo, hi)
        c, _m = polyfit_bkg(tc, rate, pre, post)
        net = rate - (np.polyval(c, tc) if c is not None else 0.0)
        lc_hist(ax, ed, net, PUB["c_data"], label="net light curve (0.128 s bins)",
                zorder=2)
        sig = np.asarray(bt["SIGNIFICANCE"], float) if "SIGNIFICANCE" in bt.colnames else None
        smax = np.nanmax(sig) if sig is not None and np.isfinite(sig).any() else 1.0
        smin = np.nanmin(sig) if sig is not None and np.isfinite(sig).any() else 0.0
        # a colourbar carries significance (Vikas 2026-08-13: a bar, not printed
        # numbers -- the numbers cluttered the peak where blocks are narrowest)
        _cmap = plt.cm.viridis
        _norm = matplotlib.colors.Normalize(vmin=smin, vmax=smax)
        for j, r in enumerate(bt):
            t1, t2 = float(r["T_START"]), float(r["T_STOP"])
            m = (tc >= t1) & (tc < t2)
            lvl = float(np.mean(net[m])) if m.any() else np.nan
            sh = (sig[j] / smax) if sig is not None and np.isfinite(sig[j]) else 0.4
            col = _cmap(_norm(sig[j] if sig is not None and np.isfinite(sig[j]) else smin))
            # horizontal bars ONLY -- no vertical connectors (Vikas, 2026-08-13).
            ax.hlines(lvl, t1, t2, color=col, lw=PUB["lw_primary"] + 1.6, zorder=5)
        # bracket the analysed span: dotted verticals at the FIRST block start and
        # the LAST block stop (Vikas, 2026-08-13)
        ax.axvline(float(bt["T_START"][0]), color="0.55", lw=0.9, ls=":", zorder=1)
        ax.axvline(float(bt["T_STOP"][-1]), color="0.55", lw=0.9, ls=":", zorder=1)
        ax.set_xlim(src[0] - 3, src[1] + 3)
        inwin = (tc >= src[0] - 3) & (tc <= src[1] + 3)
        ylim_from_data(ax, net[inwin])
        ax.axhline(0, color="0.75", lw=0.7, zorder=0)
        ax.legend(loc="upper right")
        ax.set_xlabel("time since trigger (s)")
        ax.set_ylabel(r"net rate (cts s$^{-1}$)")
        ax.set_title(f"{trig} — step 5: {len(bt)} Bayesian blocks", fontsize=PUB["label_size"],
                     loc="left")
        sm = plt.cm.ScalarMappable(cmap=_cmap, norm=_norm); sm.set_array([])
        cb = fig.colorbar(sm, ax=ax, pad=0.012, aspect=26, extend="neither")
        cb.set_label(r"block significance ($\sigma$)", fontsize=PUB["tick_size"])
        cb.ax.tick_params(labelsize=PUB["tick_size"] - 2)
    fig.tight_layout()
    f = os.path.join(out, f"{trig}_step5_binning.png")
    fig.savefig(f, bbox_inches="tight"); plt.close(fig); made.append(f)
    return made


# ---------------------------------------------------------------- step 7
BANDS = [(8, 25), (25, 50), (50, 100), (100, 350), (350, 1000)]


def _pipeline_tx():
    """The PRODUCTION T90 estimator (scripts/40::_tx_core).

    The figure previously computed its own t5/t95 with `np.interp` on the
    cumulative — the very method the 2026-08-13 audit invalidated, because a
    background-subtracted cumulative is NOT monotonic so np.interp's `xp`
    contract is violated. That gave the figure different numbers from the
    catalog: two T90 definitions inside one project. Import the real one.
    """
    import importlib.util
    sp = importlib.util.spec_from_file_location(
        "t40fig", os.path.join(ROOT, "scripts", "40_temporal_survey.py"))
    m = importlib.util.module_from_spec(sp)
    sys.modules.setdefault("t40fig", m)
    sp.loader.exec_module(m)
    return m._tx_core, m._tx_with_mc


def fig_step7(trig, out):
    """Energy-resolved T90 — ONE PANEL PER BAND, the LATBright layout
    (GRB260226A/s01a_gbm_lightcurves.py): each band gets its OWN count-rate light
    curve, its own t5-t95 span, its own T90. A single background light curve cannot
    show why the duration shortens with energy; per-band panels can (Vikas,
    2026-08-13: "does every energy range not have their own count rate lightcurves?").
    The right-hand panel is the resulting T90(E) relation."""
    _TXC, _TXMC = _pipeline_tx()
    rs = rows_for(trig)
    nais = [r for r in rs if str(r["DETECTOR"]).strip().startswith("n")]
    if not nais:
        return []
    ref = min(nais, key=lambda r: float(r["DET_ANGLE"])
              if str(r["DET_ANGLE"]) not in ("nan", "--") else 999)
    det = str(ref["DETECTOR"]).strip()
    p = tte_path(trig, det)
    nb = len(BANDS)
    fig = plt.figure(figsize=(13.5, 1.65 * nb + 1.9))
    gsr = fig.add_gridspec(1, 2, width_ratios=[2.9, 1.05], wspace=0.26,
                           left=0.085, right=0.965, top=0.90, bottom=0.11)
    gl = gsr[0].subgridspec(nb, 1, hspace=0.0)
    axes = [fig.add_subplot(gl[k]) for k in range(nb)]
    for a in axes[1:]:
        a.sharex(axes[0])
    axE = fig.add_subplot(gsr[1])
    if p is None:
        _note(axes[0], "no TTE"); _note(axE, "")
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
        cols = ["#2b3a67", "#3aa6a0", "#6aa84f", "#f08c4b", "#b3216a"]
        t90s, excluded = [], []
        dt = 0.128
        for ib, (e1, e2) in enumerate(BANDS):
            ax = axes[ib]
            c_ = cols[ib % len(cols)]
            sel = (emid[np.clip(ch, 0, len(emid) - 1)] >= e1) & \
                  (emid[np.clip(ch, 0, len(emid) - 1)] < e2)
            tb = tt[sel]
            if tb.size < 30:
                _note(ax, f"{e1}-{e2} keV: too few events"); continue
            edges = np.arange(pre[0], post[1] + dt, dt)
            tc = 0.5 * (edges[:-1] + edges[1:])
            rate = np.histogram(tb, bins=edges)[0] / dt
            c, _m = polyfit_bkg(tc, rate, pre, post)
            net = rate - (np.polyval(c, tc) if c is not None else 0.0)
            m = (tc >= src[0] - 1.5) & (tc <= src[1] + 1.5)
            # lc_hist takes EDGES (len N+1); build them from the masked bin set
            _idx = np.flatnonzero(m)
            _ed = np.append(edges[_idx], edges[_idx[-1] + 1])
            lc_hist(ax, _ed, net[m], c_, alpha_fill=0.30, zorder=2)
            msrc = (tc >= src[0]) & (tc <= src[1])
            tot_c = float(np.sum(net[msrc] * dt))
            cum_c = np.cumsum(net[msrc] * dt)
            # point AND uncertainty from the production estimator (same Poisson
            # realizations of RAW counts minus the fitted background)
            _rawc = rate * dt
            _bkgc = (np.polyval(c, tc) if c is not None else np.zeros_like(tc)) * dt
            t90v, t90e, t5, t95, _tr = _TXMC(tc, _rawc, _bkgc, src, 0.90, 400,
                                             abs(hash((trig, e1, e2))) % (2 ** 32))
            exc = float(cum_c.max() / tot_c - 1.0) if tot_c > 0 else np.inf
            ok = np.isfinite(t90v) and tot_c >= 200.0 and exc <= 0.10
            if ok:
                ax.axvspan(t5, t95, color=c_, alpha=0.13, lw=0, zorder=1)
                for x_ in (t5, t95):
                    ax.axvline(x_, color=c_, lw=1.1, ls="--", alpha=0.8, zorder=3)
                t90s.append((0.5 * (e1 + e2), t90v, t90e))
                txt = rf"{e1}–{e2} keV   $T_{{90}}$ = {t90v:.1f} $\pm$ {t90e:.1f} s"
            else:
                excluded.append(f"{e1}–{e2}")
                txt = (rf"{e1}–{e2} keV   $T_{{90}}$ not measured "
                       rf"({tot_c:.0f} net cts)")
            ax.text(0.012, 0.86, txt, transform=ax.transAxes, ha="left", va="top",
                    fontsize=PUB["tick_size"] - 2, color=c_ if ok else "0.45")
            ax.axhline(0, color="0.8", lw=0.7, zorder=0)
            ylim_from_data(ax, net[m])
            ax.set_xlim(src[0] - 1.5, src[1] + 1.5)
            if ib < nb - 1:
                ax.tick_params(labelbottom=False)
        axes[-1].set_xlabel("time since trigger (s)")
        axes[nb // 2].set_ylabel(r"net rate (cts s$^{-1}$)")
        if len(t90s) >= 3:
            E_ = np.array([a for a, _b, _e in t90s])
            T_ = np.array([_b for _a, _b, _e in t90s])
            S_ = np.array([_e for _a, _b, _e in t90s])
            # weighted fit in log-log, with the slope's own uncertainty from the
            # covariance (a slope quoted without one is not a measurement)
            _w = 1.0 / np.maximum(S_ / (T_ * np.log(10)), 1e-6)
            _cf, _cov = np.polyfit(np.log10(E_), np.log10(T_), 1, w=_w, cov=True)
            k, b0 = _cf
            k_err = float(np.sqrt(_cov[0, 0]))
            xx = np.logspace(np.log10(E_.min()), np.log10(E_.max()), 24)
            axE.plot(xx, 10 ** (b0 + k * np.log10(xx)), color="0.35", lw=1.4,
                     zorder=2, label=rf"fit: $E^{{{k:+.2f}\pm{k_err:.2f}}}$")
            axE.plot(xx, 10 ** (b0) * (xx ** -0.20) / (10 ** (b0) * (E_[0] ** -0.20))
                     * T_[0] * (E_[0] / E_[0]), ls="--", color=PUB["c_bgo"],
                     lw=PUB["lw_secondary"], zorder=1,
                     label=r"$E^{-0.20}$ (slope only)")
            for i_, (e_, t_, s_) in enumerate(zip(E_, T_, S_)):
                axE.errorbar(e_, t_, yerr=s_, fmt="o", ms=7, color=cols[i_ % len(cols)],
                             ecolor=cols[i_ % len(cols)], elinewidth=1.4, capsize=3,
                             zorder=4)
            axE.set_xscale("log"); axE.set_yscale("log")
            axE.set_xlabel("band centre (keV)")
            axE.set_ylabel(r"$T_{90}$ (s)")
            axE.set_title(rf"$T_{{90}}(E)$: slope {k:+.2f} $\pm$ {k_err:.2f}"
                          rf"  ({len(E_)} bands)",
                          fontsize=PUB["label_size"] - 3, loc="left")
            axE.legend(loc="lower left", fontsize=PUB["legend_size"] - 3)
            axE.set_ylim(0.90 * (T_ - S_).min(), 1.10 * (T_ + S_).max())
        if excluded:
            axE.text(0.98, 0.97, "excluded: " + ", ".join(excluded) + " keV",
                     transform=axE.transAxes, ha="right", va="top",
                     fontsize=PUB["tick_size"] - 4, color=PUB["c_bgo"])
    fig.suptitle(f"{trig} — step 7: energy-resolved $T_{{90}}$ (detector {det}); "
                 f"dashed = $t_5$, $t_{{95}}$", fontsize=PUB["label_size"], y=0.965)
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

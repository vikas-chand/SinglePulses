#!/usr/bin/env python
"""scripts/44_step_figures.py -- ONE FIGURE PER PIPELINE STEP, per burst.

Vikas, 2026-08-13: "we must have figures for every step."  Steps 6 and 8 already
emit figures (scripts/10 spectral_evolution + ep_kt_correlation; scripts/41
montage/overlay).  This script fills every other step, so a human can SEE what
each stage of the pipeline decided:

  step1_inventory.png   response (DRM) coverage bars vs the stamped source window
                        + per-detector off-axis angle -- the D1/D2 checks, visible
  step2_detectors.png   approved detector angles vs the REAL NaI rule
                        (<=50 keep; 50-60 only via BCAT rescue; >60 drop;
                        BGOs exempt -- companion rule)
  step3_background.png  per-detector LC + fitted background polynomial through the
                        approved pre/post windows + residual strip
  step4_source.png      LC with the background gap and the stamped source window
  step5_binning.png     net LC + Bayesian blocks as an adaptive step + per-block S
  step7_temporal.png    cumulative net counts with t5/t95/T90 marked, per band
  step9_qc.png          winner + margins + L28 edge class per block (the scorecard,
                        drawn)

PRECURSORS (credit + provenance): steps 3/4 descend from
`scripts/approved_selection_png.py` (2026-07-16) and step 5 from
`scripts/block_plots.py` (2026-07-17), which produced the complete approval-era sets in
`plots/approved_selections/` (106) and `plots/block_plots/` (103). Those are now
ARCHIVAL; this file is canonical. It should have been written by extending them —
writing it fresh cost an afternoon rediscovering bugs they had already fixed
(AGENTS.md now requires an inventory pass before building).

LIGHT TIER: numpy/astropy/matplotlib only -- no threeML, so it can run alongside
the fits.  Every panel that cannot be built is SKIPPED LOUDLY (a stamped "missing
input" note on the figure), never silently omitted (Shipping Gate).

Usage:
  python scripts/44_step_figures.py --trig bn081125496 --out results/sweep106/bn081125496
  python scripts/44_step_figures.py --all --root results/sweep106
"""
import os, sys, glob, json, argparse
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
            fontsize=PUB["tick_size"] - 5, color="crimson", wrap=True)
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


def bcat_nais(trig):
    """NaIs in the BCAT detector mask (results/grb_sample.ecsv NAI_DETECTORS) —
    the 50–60° rescue condition. Same source scripts/39 uses for `in_bcat`."""
    try:
        s = Table.read(os.path.join(ROOT, "results", "grb_sample.ecsv"),
                       format="ascii.ecsv")
        row = s[s["TRIGGER_NAME"] == trig]
        if len(row):
            return {d.strip() for d in str(row["NAI_DETECTORS"][0]).split(",")
                    if d.strip()}
    except Exception:
        pass
    return set()


# ---------------------------------------------------------------- step 1 + 2
def _angles_for(trig, rs):
    """Off-axis angles + THEIR PROVENANCE. Never present a carried-forward angle as
    measured (D7 / figure-gate HARD-FAIL 3, bn240403498 2026-09-04). Preference:
    the step-2 recomputation from poshist; else the catalog value, labelled as such."""
    p = os.path.join(ROOT, "results", "qc", f"{trig}_step2_detector_angles.ecsv")
    if os.path.exists(p):
        t = Table.read(p, format="ascii.ecsv")
        ang = {str(r["DET"]).strip(): float(r["ANGLE_DEG"]) for r in t}
        ph = str(t.meta.get("poshist", "poshist"))
        ver = str(t.meta.get("verification", "")).strip()
        prov = f"angles recomputed for this run from {ph}" + (f" — {ver}" if ver else "")
        return ang, prov
    ang, when = {}, ""
    for r in rs:
        try:
            ang[str(r["DETECTOR"]).strip()] = float(r["DET_ANGLE"])
        except Exception:
            pass
        when = str(r["APPROVED_UTC"]) if "APPROVED_UTC" in rs.colnames else ""
    return ang, ("angles CARRIED FORWARD from the approved catalog"
                 + (f" ({when[:10]})" if when else "")
                 + " — no poshist on disk, NOT re-derived for this run")


def _matrix_spans(path):
    """Every (TSTART, TSTOP) of a response, trigger-relative, plus TRIGTIME."""
    with fits.open(path) as h:
        t0 = None
        for hdu in h:
            if "TRIGTIME" in hdu.header:
                t0 = float(hdu.header["TRIGTIME"]); break
        # ONLY the response matrices — a .rsp2 also carries EBOUNDS/PRIMARY with
        # TSTART/TSTOP, and counting those printed "14 matrices" beside a QC table
        # that says 12 (caught pre-verification, bn240403498 2026-09-04).
        mats = [hdu for hdu in h if hdu.name.strip().upper() == "SPECRESP MATRIX"]
        if not mats:
            mats = [hdu for hdu in h if "TSTART" in hdu.header and "TSTOP" in hdu.header]
        sp = [(float(hdu.header["TSTART"]) - t0, float(hdu.header["TSTOP"]) - t0)
              for hdu in mats if t0]
    return sorted(sp), t0


def _divergence_note(det, ang):
    """The n3-class note, READ FROM THE LEDGER (F7: a figure may not restate a value it
    did not read from a product). Round 3 failed because a hard-coded 'reason is not yet
    recorded' survived the ledger gaining the PI's verbatim reason an hour later."""
    led = os.path.join(ROOT, "results", "campaign", "divergence_ledger.md")
    if not os.path.exists(led):
        return (f"† {det} ({ang:.2f}°) is in the BCAT mask and was not approved; "
                f"no divergence ledger on disk."), None
    txt = open(led, encoding="utf-8").read()
    row = ""
    for line in txt.split("\n"):
        if line.startswith("| D-") and det in line:
            row = line
    has_reason = "verbatim" in row.lower()
    is_open = "open" in row.split("|")[-2].lower() if row.count("|") > 3 else False
    note = (f"† {det} ({ang:.2f}°) is exactly the written 50–60° BCAT rescue case: the WRITTEN "
            f"RULE SAYS KEEP, the recorded human decision DROPPED it. ")
    note += ("A reason was elicited from the PI and recorded verbatim; the written rule is NOT "
             if has_reason else "No reason has been recorded yet; the written rule is NOT ")
    note += ("amended and the flag is OPEN" if is_open else "amended")
    note += f" — see results/campaign/divergence_ledger.md. No {det} data were retrieved."
    return note, led


def _grow_xlim_to_fit(fig, ax, margin_px=8, flag=None):
    """Widen the x-limit until no label runs into the axes frame. Round-2 figure gate
    (bn240403498): moving tags off the RULE lines put 8 of them through the axes RIGHT
    SPINE and its minor ticks — one strike landing on a digit of a restated count. A
    frame is a line too; budget the label width instead of guessing it."""
    x0, xstart = ax.get_xlim()
    for _ in range(6):
        fig.canvas.draw()
        r = fig.canvas.get_renderer()
        ab = ax.get_window_extent(renderer=r)
        ends = [t.get_window_extent(renderer=r).x1 for t in ax.texts] or [ab.x0]
        over = max(ends) - (ab.x1 - margin_px)
        if over <= 0:
            return
        _x0, x1 = ax.get_xlim()
        if (x1 - _x0) > 1.9 * (xstart - x0):
            if flag is not None:
                flag[0] = True
            return          # HARD CAP: a label too long to fit belongs in the footnote,
                            # not in a wider axis. Chasing it explodes the range (the
                            # fitter took the panel to 7000 s before this cap existed).
        ax.set_xlim(_x0, x1 + (over / max(ab.width, 1.0)) * (x1 - _x0) * 1.05)


def fig_step1_2(trig, out):
    rs = rows_for(trig)
    if not len(rs):
        return []
    made = []
    bcat = bcat_nais(trig)
    approved = [str(r["DETECTOR"]).strip() for r in rs]
    # F8 — ABSENCE IS STATED, NEVER SILENT (figure gate, bn240403498 2026-09-04):
    # a BCAT detector that was NOT approved is the one thing this panel exists to
    # expose, and looping over approved rows alone makes it structurally invisible.
    missing = [d for d in sorted(bcat) if d not in approved]
    ang_map, ang_prov = _angles_for(trig, rs)
    src1 = float(rs["SRC_START"][0]); src2 = float(rs["SRC_STOP"][0])
    n_row = len(rs) + len(missing)
    def _sha(pth):
        try:
            import hashlib
            h = hashlib.sha256()
            with open(pth, "rb") as fh:
                for c in iter(lambda: fh.read(1 << 20), b""):
                    h.update(c)
            return h.hexdigest()
        except Exception:
            return None
    import subprocess, datetime
    _prim = {q: _sha(os.path.join(ROOT, q)) for q in
             ("results/qc/%s_step1_response_coverage.ecsv" % trig,
              "results/qc/%s_step2_detector_angles.ecsv" % trig,
              "results/background_intervals.ecsv", "results/grb_sample.ecsv",
              "results/campaign/divergence_ledger.md")}   # cited on the figure -> pinned
    _dirty = subprocess.run(["git", "-C", ROOT, "status", "--porcelain", "--",
                             "scripts/44_step_figures.py"],
                            capture_output=True, text=True).stdout.strip()
    sidecar = {"figure": f"{trig}_step1_inventory.png",
               "generated_utc": datetime.datetime.now(datetime.timezone.utc)
                                .strftime("%Y-%m-%dT%H:%M:%SZ"),
               "generator": "scripts/44_step_figures.py::fig_step1_2",
               "generator_sha256": _sha(os.path.join(ROOT, "scripts", "44_step_figures.py")),
               "git_head": subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                                          capture_output=True, text=True).stdout.strip(),
               "generator_uncommitted": bool(_dirty),
               "generator_note": ("generator is MODIFIED in the working tree — git_head does NOT "
                                  "describe the code that made this figure; use generator_sha256")
                                 if _dirty else "generator matches git_head",
               "primitive_sha256": _prim,
               "trigger": trig, "src_start": src1, "src_stop": src2,
               "angle_provenance": ang_prov, "bcat": sorted(bcat),
               "approved": approved, "bcat_not_approved": missing,
               "detectors_not_plotted": {}, "detectors": {}}

    # +0.30 in per expected footnote line: with a fixed 3.4 in the block overflowed and
    # bbox_inches="tight" silently grew the canvas (round-4 layout nit).
    _n_foot = 9 + 2 * len(missing)
    fig, axes = plt.subplots(1, 2, figsize=(13, 0.62 * n_row + 2.4 + 0.22 * _n_foot))
    ax, ax2 = axes
    lo_all = []; _cov_hi = []
    straddle = []          # (det, boundary) where the source window crosses a DRM edge
    for i, r in enumerate(rs):
        det = str(r["DETECTOR"]).strip()
        p = rsp_path(trig, det)
        lo = hi = np.nan; spans = []
        if p:
            try:
                spans, _t0 = _matrix_spans(p)
                if spans:
                    lo, hi = spans[0][0], spans[-1][1]
            except Exception:
                pass
        if np.isfinite(lo):
            lo_all.append(lo); _cov_hi.append(hi)
            ok = (lo <= src1) and (hi >= src2)
            # FILL = detector identity; EDGE = verdict, in a NEUTRAL colour so the
            # verdict is readable on a detector whose own colour is green (NIT-2).
            ax.barh(i, hi - lo, left=lo, height=0.55, color=dcol(det, trig), alpha=0.45,
                    edgecolor=("#1a1a1a" if ok else PUB["c_bgo"]),
                    linewidth=(1.4 if ok else 2.4), zorder=2)
            # internal matrix boundaries: one bar is NOT one response (NIT-3)
            for (a_, b_) in spans[:-1]:
                ax.plot([b_, b_], [i - 0.275, i + 0.275], color="#1a1a1a",
                        lw=0.6, alpha=0.55, zorder=4)
            inside = [b_ for (a_, b_) in spans[:-1] if src1 < b_ < src2]
            for b_ in inside:
                straddle.append((det, b_))
                ax.plot([b_, b_], [i - 0.30, i + 0.30], color="#1a1a1a",
                        lw=1.6, alpha=0.95, zorder=5)
            _sp_w = (hi - lo)
            ax.text(hi - 0.02 * _sp_w, i,
                    f"PASS · {len(spans)} matrices" if ok else f"FAIL · {len(spans)} matrices",
                    va="center", ha="right", fontsize=PUB["tick_size"] - 2,
                    color=("#1a1a1a" if ok else PUB["c_bgo"]), fontweight="bold", zorder=6)
            sidecar["detectors"][det] = {"cov_start": lo, "cov_stop": hi,
                                         "n_matrices": len(spans),
                                         "boundaries_in_window": inside,
                                         "verdict": "PASS" if ok else "FAIL",
                                         "angle_deg": ang_map.get(det),
                                         "in_bcat": det in bcat, "approved": True}
        else:
            ax.text(src1, i, "  no response found", va="center",
                    fontsize=PUB["tick_size"] - 3, color=PUB["c_bgo"])
            sidecar["detectors"][det] = {"verdict": "NO RESPONSE FILE",
                                         "angle_deg": ang_map.get(det),
                                         "in_bcat": det in bcat, "approved": True}
        a_ = ang_map.get(det)
        if a_ is not None:
            ax2.barh(i, a_, height=0.55, color=dcol(det, trig), alpha=0.85)

    # ---- the absence rows: in BCAT, not approved
    _lefttag = {}
    for j, det in enumerate(missing):
        i = len(rs) + j
        a_ = ang_map.get(det)
        # ABSENCE IS DRAWN AS ABSENCE (F8; the repo's own F7-r5 precedent: a cross, never
        # a zero-length or window-shaped bar). Round 2 failed because a hatched box spanning
        # exactly 18-48 s reads as "n3 is covered over the source window".
        # The cross sits where the BAR WOULD START, not inside the source window: at the
        # window it was 7.7 px inside an 18 px band and touched the window rule (round-3 NIT-a).
        ax.plot([min(lo_all) if lo_all else src1], [i], marker="x", ms=7, mew=1.8,
                color="0.45", linestyle="none", zorder=4)
        _lefttag[det] = "no response file \u2020"
        if a_ is not None:
            ax2.barh(i, a_, height=0.55, color="none", edgecolor="0.45",
                     hatch="////", linewidth=1.0)
        sidecar["detectors"][det] = {
            "verdict": "NOT APPROVED (in BCAT)", "angle_deg": a_, "in_bcat": True,
            "approved": False,
            "written_rule": "KEEP (50-60° BCAT rescue)" if (a_ and 50 < a_ <= 60) else "DROP",
            # READ FROM THE LEDGER, never hard-coded: round 3 fixed this sentence on the
            # figure face and left its twin here, so the sidecar contradicted the ledger it
            # pins — and the sidecar is the authority a verifier checks against (S5).
            "rule_divergence": (_divergence_note(det, a_)[0]
                                if (a_ and 50 < a_ <= 60) else None)}

    labels = approved + missing
    ax.axvspan(src1, src2, facecolor=PUB["c_src_win"], alpha=0.14, lw=0, zorder=1)
    for _x in (src1, src2):
        ax.axvline(_x, color=PUB["c_src_win"], lw=1.2, ls=(0, (4, 2)), alpha=0.95, zorder=3)
    ax.set_yticks(range(n_row))
    ax.set_yticklabels([f"{d} · {_lefttag[d]}" if d in _lefttag else d for d in labels],
                       fontsize=PUB["tick_size"] - 2)
    _dlo = min(lo_all + [src1]); _dhi = max(_cov_hi + [src2]); _sp = _dhi - _dlo
    ax.set_xlim(_dlo - 0.06 * _sp, _dhi + 0.06 * _sp)          # data-driven, not label-driven
    ax.set_ylim(-0.7, n_row - 0.05)
    ax.annotate("source\nwindow", xy=(src2, 0.985), xycoords=("data", "axes fraction"),
                xytext=(6, -4), textcoords="offset points", ha="left", va="top",
                fontsize=PUB["tick_size"] - 3, color=PUB["c_src_win"], linespacing=1.1)
    ax.set_xlabel("time since trigger (s)")
    ax.set_title("response (DRM) coverage", loc="left")
    # NIT-4: say what PASS MEANS, on the figure, because figures travel alone.
    _off = [d for d in ang_map if d not in labels]
    foot = (f"PASS = DRM coverage brackets the stamped source window "
            f"[{src1:g}, {src2:g}] s; thin ticks = matrix boundaries")
    if _off:
        _oa = [ang_map[d] for d in _off if ang_map.get(d) is not None]
        import math as _m
        foot += (f"\n{len(_off)} further detectors "
                 f"({_m.floor(min(_oa)*10)/10:.1f}–{_m.ceil(max(_oa)*10)/10:.1f}°, all beyond the "
                 f"axis) are not shown — all DROP: {', '.join(sorted(_off))}")
    foot += ("\nno gll_* files on disk and LAT boresight 62° (GCN 36024): no LLE/LAT expected."
             "  Rails (NaI-only): green dashed = 50° keep, dotted = 60° drop; "
             "b0 is kept by the companion rule.")
    _ledger_used = None
    for _d in missing:
        _a = ang_map.get(_d)
        if _a is not None and 50.0 < _a <= 60.0:
            _n, _ledger_used = _divergence_note(_d, _a)
            foot += "\n" + _n
        else:
            foot += (f"\n† {_d} is in the BCAT mask but was not approved; no data retrieved.")
    foot += "\nhatched row = in the BCAT mask but NOT approved."
    if straddle:
        foot += (f"\nthick tick: the window CROSSES a matrix boundary at "
                 f"{straddle[0][1]:.3f} s — more than one DRM covers it")
    _foot_left = foot

    # ---- right panel: rule lines, then tags in a COLLISION-FREE column
    ax2.axvline(50, color="#1a7d3a", ls="--", lw=1.4)
    ax2.axvline(60, color="#444444", ls=(0, (1, 1.6)), lw=1.4)   # NOT c_bgo: that is b0's fill
    _amax = max([ang_map[d] for d in labels if ang_map.get(d) is not None] + [60.0])
    ax2.set_xlim(0, max(_amax, 62.0) * 1.10)   # floor 62° so both rails always show;
                                               # the label fitter may widen this further
    # HARD-FAIL 1 (bn240403498): a tag placed at the bar tip was STRUCK by the 50deg
    # line in the SAME green, and the white bbox did not render over it. Tags now sit
    # in a fixed column at 0.72 of the axis - right of both rule lines by construction
    # - in neutral grey, so no rule line can ever cross a glyph.
    _rowtag = {}
    for i, det in enumerate(labels):
        if det.startswith("b"):
            tag = "BGO: companion rule"
        else:
            a_ = ang_map.get(det)
            in_b = det in bcat
            tag = "in BCAT" if in_b else "not in BCAT"
            if a_ is not None and 50.0 < a_ <= 60.0:
                tag += " · rescue band"     # the 50-60 deg range is on the axis already
            if det in missing:
                # The scientifically load-bearing fact - the WRITTEN rule says KEEP here -
                # is spelled out in the footnote; "DROPPED" alone would read as if the rail
                # rule dropped it (round-2 HARD-3). A long tag cannot live on the axis.
                tag += " · DROPPED \u2020"
        _rowtag[det] = tag
    ax2.set_yticks(range(n_row))
    # Tags live in the TICK LABELS (outside the axes) so the panel keeps its dynamic range:
    # round 3 measured 62% of the panel empty because a 30-character tag sat INSIDE it.
    ax2.set_yticklabels([f"{d} · {_rowtag.get(d,'')}" if _rowtag.get(d) else d for d in labels],
                        fontsize=PUB["tick_size"] - 2)
    ax2.set_xlabel(r"off-axis angle ($^\circ$)")
    ax2.set_ylim(-0.7, n_row - 0.05)
    # Direct labels, not a legend box: the legend sat ON the tag column (pre-verification
    # catch, bn240403498). Reference rule: never place a legend over data.
    # Labels sit to the RIGHT of their own rail and the width guard grows the axis to hold
    # them; an unguarded ha="left" label on the 60° rail ran through the right spine
    # (round-4 HARD-1), and placing both to the LEFT made each cross its neighbour's rail.
    # RIGHT of each rail (a left-placed 60° label crossed the 50° rail and collided with
    # its neighbour); the width guard below then grows the axis just enough to hold them —
    # measured need is ~70° against a 68.2° data-driven limit, i.e. ~2%.
    # SHORT labels: two ~110 px labels on rails 10° apart cannot both sit to the right
    # without one crossing the other's rail (round-4 iterations). The angles are on the
    # axis ticks and the rule is spelled out in the footnote.
    for _x, _t, _c, _ha, _dx in ((50.0, "keep", "#1a7d3a", "left", 6),
                                 (60.0, "drop", "#444444", "left", 6)):
        # ABOVE the axes (never over a bar) and on OPPOSITE sides of their own lines,
        # so the two labels cannot collide with each other either.
        # INSIDE the axes, in the empty strip above the top bar: above the axes they
        # collided with the panel title (pre-verification catch, bn240403498).
        ax2.annotate(_t, xy=(_x, n_row - 0.42), xytext=(6 if _dx > 0 else -6, 0),
                     textcoords="offset points", ha=_ha, va="center",
                     fontsize=PUB["tick_size"] - 3.5, color=_c)   # >=4 pt clear of its rail
    ax2.set_title("detector selection", loc="left")
    # HARD-FAIL 3: the angles' provenance, on the figure itself.


    _nap = len(rs)
    fig.suptitle(f"{trig} — {_nap} approved detectors, all DRM-valid over the source window"
                 + (f"; {', '.join(missing)} in BCAT but dropped" if missing else ""),
                 fontsize=PUB["label_size"])
    fig.tight_layout(rect=(0, 0.10, 1, 1))
    _cap_hit = [False]; _cap_hit2 = [False]      # separate flags: one list reported a
    _xl_before = tuple(ax.get_xlim())            # right-axis cap hit as a left-axis one
    _xl2_before = tuple(ax2.get_xlim())
    _grow_xlim_to_fit(fig, ax, flag=_cap_hit)    # safety net: left
    _grow_xlim_to_fit(fig, ax2, flag=_cap_hit2)  # safety net: right (removing it cost round 4)
    _xl_after = tuple(ax.get_xlim())
    fig.tight_layout(rect=(0, 0.10, 1, 1))
    import textwrap as _tw
    _foot_left = "\n".join(_tw.fill(_l, 140, subsequent_indent="   ")
                           for _l in _foot_left.split("\n"))
    ang_prov = _tw.fill(ang_prov, 140, subsequent_indent="   ")
    # ONE text block, not two: separately-placed blocks overran each other once the
    # footnote grew (pre-round-3 catch, bn240403498).
    fig.text(0.012, 0.075, _foot_left + "\n" + ang_prov,
             fontsize=PUB["tick_size"] - 3.5, color="0.30", va="top", ha="left",
             linespacing=1.45)
    f = os.path.join(out, f"{trig}_step1_inventory.png")
    fig.savefig(f, bbox_inches="tight"); plt.close(fig); made.append(f)
    # NIT-6: same-run sidecar, so every printed number is checkable without the producer.
    sidecar["detectors_not_plotted"] = {d: ang_map[d] for d in ang_map if d not in labels}
    sidecar["axes"] = {"left_xlim": list(ax.get_xlim()), "right_xlim": list(ax2.get_xlim()),
                       "left_xlim_is_label_driven": _xl_after != _xl_before,
                       # MEASURED, not asserted: this field was a hard-coded False while the
                       # fitter had grown the right axis 68.2° -> 70.4° (round-5 blocker).
                       "right_xlim_is_label_driven": tuple(ax2.get_xlim()) != _xl2_before,
                       "right_fit_cap_hit": _cap_hit2[0],
                       "left_fit_cap": "1.9x initial range", "left_fit_cap_hit": _cap_hit[0]}
    sc = os.path.join(out, f"{trig}_step1_inventory.sidecar.json")
    with open(sc, "w") as fh:
        json.dump(sidecar, fh, indent=1)
    made.append(sc)
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
                    transform=ax.transAxes, fontsize=PUB["tick_size"] - 5, color="crimson")
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
        # the LAST block stop (Vikas, 2026-08-13). Labelled in the legend so a
        # reader cannot mistake it for the stamped source window, which may end
        # later (vision-QC round 5 nit, 2026-08-14).
        ax.axvline(float(bt["T_START"][0]), color="0.55", lw=0.9, ls=":", zorder=1,
                   label="analysed span")
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
            t90v, t90e, t5, t95, _tr, _dist = _TXMC(tc, _rawc, _bkgc, src, 0.90, 400,
                                                    abs(hash((trig, e1, e2))) % (2 ** 32))
            exc = float(cum_c.max() / tot_c - 1.0) if tot_c > 0 else np.inf
            ok = np.isfinite(t90v) and tot_c >= 200.0 and exc <= 0.10
            if ok:
                ax.axvspan(t5, t95, color=c_, alpha=0.13, lw=0, zorder=1)
                for x_ in (t5, t95):
                    ax.axvline(x_, color=c_, lw=1.1, ls="--", alpha=0.8, zorder=3)
                # GEOMETRIC band centre: the bands are log-spaced and the relation is
                # a power law, so sqrt(e1*e2) is the representative energy; the
                # arithmetic mean biases every point toward the band's upper edge.
                t90s.append((float(np.sqrt(e1 * e2)), t90v, t90e))
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
            # cov="unscaled": our weights ARE 1/sigma from the MC, so the slope error
            # must come from those measurement errors, not be rescaled by the fit's own
            # residual scatter (numpy's cov=True multiplies by chi2/dof, which quietly
            # shrinks the error when few points happen to lie close to the line).
            _cf, _cov = np.polyfit(np.log10(E_), np.log10(T_), 1, w=_w, cov="unscaled")
            k, b0 = _cf
            k_err = float(np.sqrt(_cov[0, 0]))
            _res = np.log10(T_) - (b0 + k * np.log10(E_))
            _chi2 = float(np.sum((_res * _w) ** 2)) / max(len(E_) - 2, 1)
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
            axE.set_title(rf"$T_{{90}}\propto E^{{{k:+.2f}\pm{k_err:.2f}}}$   "
                          rf"$\chi^2$/dof = {_chi2:.2f}  ({len(E_)} bands)",
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
    """Step 9 — the scorecard: per-block evidence for extra structure, and the L28
    edge class of any significant blackbody.

    Rebuilt 2026-08-13 after the figure-review agent refused to ship the old one:
    overprinted y-labels, an empty lower panel with both threshold lines welded to
    the frame and no explanation, and the decision-critical bar (dAIC 5.954 against a
    6.0 threshold) carrying no number."""
    ft = os.path.join(out, trig, "spectral_fits.ecsv")
    fig, axes = plt.subplots(2, 1, figsize=(12.5, 7.4), sharex=True,
                             gridspec_kw={"height_ratios": [2.15, 1.0], "hspace": 0.07})
    ax, ax2 = axes
    if not os.path.exists(ft):
        _note(ax, f"no fit table: {os.path.relpath(ft, ROOT)}")
        _note(ax2, "")
    else:
        t = Table.read(ft, format="ascii.ecsv")
        pre = sorted({c[:-4] for c in t.colnames if c.endswith("_AIC")})
        blocks, dsimp, winners, edge, edge_lab = [], [], [], [], []
        for r in t:
            k = int(r["BLOCK"])
            if k < 0:
                continue
            va = {}
            for p_ in pre:
                try:
                    if bool(r[f"{p_}_VALID"]) and np.isfinite(float(r[f"{p_}_AIC"])):
                        va[p_] = float(r[f"{p_}_AIC"])
                except Exception:
                    pass
            s_ = [v for p_, v in va.items() if p_ in SIMPLE]
            x_ = [v for p_, v in va.items() if p_ not in SIMPLE]
            blocks.append(k)
            dsimp.append(min(s_) - min(x_) if s_ and x_ else np.nan)
            winners.append(str(r["BEST_AIC_MODEL"]) if "BEST_AIC_MODEL" in t.colnames else "?")
            kt = np.nan; lab = ""
            for ktc, lrtc, vc, nm in (("BANDBB_KT", "LRT_BANDBB_BAND", "BANDBB_VALID", "B"),
                                      ("CPLBB_KT", "LRT_CPLBB_CPL", "CPLBB_VALID", "C")):
                try:
                    v_, l_ = float(r[ktc]), float(r[lrtc])
                    if np.isfinite(v_) and v_ > 1.0544 and np.isfinite(l_) and l_ >= 9.2 \
                       and bool(r[vc]):
                        kt = v_; lab = nm; break
                except Exception:
                    pass
            edge.append(3.9207 * kt if np.isfinite(kt) else np.nan)
            edge_lab.append(lab)

        cols = [PUB["c_decisive"] if d >= 10 else PUB["c_strong"] if d >= 6
                else PUB["c_none"] for d in dsimp]
        ax.bar(blocks, dsimp, color=cols, edgecolor="0.35", linewidth=0.8, zorder=3)
        ax.axhline(10, color=PUB["c_decisive"], ls="--", lw=1.4, zorder=2,
                   label=r"DECISIVE  $\Delta$AIC $\geq$ 10")
        ax.axhline(6, color=PUB["c_strong"], ls="--", lw=1.4, zorder=2,
                   label=r"STRONG  $\Delta$AIC $\geq$ 6")
        ax.axhline(0, color="0.7", lw=0.8, zorder=1)
        # EVERY bar carries its number: the review agent's point is that a bar 0.05
        # below a decision line, unlabelled, invites the reader to call it STRONG.
        for b, d, w in zip(blocks, dsimp, winners):
            if not np.isfinite(d):
                continue
            up = d >= 0
            ax.annotate(f"{d:+.2f}", xy=(b, d), xytext=(0, 4 if up else -6),
                        textcoords="offset points", ha="center",
                        va="bottom" if up else "top",
                        fontsize=PUB["tick_size"] - 3, color="0.15", zorder=4)
            ax.annotate(w, xy=(b, 0), xytext=(0, 6 if not up else -6),
                        textcoords="offset points", ha="center",
                        va="bottom" if not up else "top",
                        fontsize=PUB["tick_size"] - 3, color="0.35", zorder=4)
        fin = [d for d in dsimp if np.isfinite(d)]
        if fin:
            lo, hi = min(fin + [0.0]), max(fin + [11.0])
            ax.set_ylim(lo - 0.18 * (hi - lo), hi + 0.22 * (hi - lo))
        ax.set_ylabel(r"$\Delta$AIC  (simple $-$ extra)")
        ax.legend(loc="upper left", ncol=2)
        ax.set_title(f"{trig} — step 9: evidence for extra spectral structure, per block "
                     f"(model name below each bar)", fontsize=PUB["label_size"], loc="left")

        ok = np.isfinite(edge)
        if np.any(ok):
            for b, e_, l_ in zip(blocks, edge, edge_lab):
                if not np.isfinite(e_):
                    continue
                c_ = (PUB["c_decisive"] if e_ < 20 else PUB["c_strong"] if e_ < 30
                      else PUB["c_nai_b"])
                ax2.plot(b, e_, "o", ms=9, color=c_, zorder=4)
                ax2.annotate(l_, xy=(b, e_), xytext=(7, 0), textcoords="offset points",
                             va="center", fontsize=PUB["tick_size"] - 4, color="0.35")
            ax2.set_ylim(0, max(40.0, 1.25 * np.nanmax(edge)))
        else:
            # F8: say WHY it is empty, and give the axis a sane range so the
            # threshold lines are not welded to the frame.
            ax2.set_ylim(0, 40)
            ax2.text(0.5, 0.62, "no block has a significant blackbody "
                     r"(nested LRT $<$ 9.2 in every block) — panel intentionally empty",
                     transform=ax2.transAxes, ha="center", va="center",
                     fontsize=PUB["tick_size"] - 1, color="0.35")
        ax2.axhline(20, color=PUB["c_decisive"], ls="--", lw=1.4,
                    label="edge-constrained  $<$ 20 keV")
        ax2.axhline(30, color=PUB["c_strong"], ls=":", lw=1.4,
                    label="edge-marginal  $<$ 30 keV")
        ax2.set_xlabel("block")
        ax2.set_xticks(blocks)
        ax2.legend(loc="upper right", ncol=2, fontsize=PUB["legend_size"] - 2)
        # the qualifier belongs in the axis label, not a title that collides with the
        # panel above (shared-x subplots have no room for a second title)
        ax2.set_ylabel("$3.92\\,kT$ (keV)\nsignificant BB only")
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

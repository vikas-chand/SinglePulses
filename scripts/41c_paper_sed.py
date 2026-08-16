#!/usr/bin/env python
"""scripts/41c_paper_sed.py — THE STANDARD SED FIGURE, one bin, one model.

STRICT XSPEC data semantics (Vikas, 2026-08-15: "plot the datapoints as XSPEC
does and also rebin as XSPEC does for setp rebin 5 5" — these are diagnostics;
the community convention IS the spec): every rebin group is a point with an
error bar (XSPlot has NO upper-limit machinery — grep=0 — so none is invented;
--ul-arrows restores the exploratory 2-sigma arrows), points in RAW calibration
(the dataset constant cancels in PlotUnfolded's ratio, so each detector
scatters about its OWN k*F(E) curve), arithmetic group midpoints
(PlotGroupCreator.cxx:50-54), group-integrated eeufspec numerator via
converged adaptive quadrature (Codex audit 2026-08-14: a fixed 16-pt grid
erred 86.85% in the CPL high-BGO tail). The 68% band is threeML's NATIVE
FittedPointSourceSpectralHandler (internal-coordinate variates — the custom
external-coordinate sampler was statistically invalid, Codex item 6),
suppressed with disclosure when native draws rail at bounds. Fit is LIVE
(fresh JointLikelihood, engine conventions) and HARD-GUARDED against the
stored engine solution when a fit table is present (|dAIC| <= 0.1 or abort);
a provenance sidecar JSON is written next to every figure.

Usage (heavy tier):
  python scripts/41c_paper_sed.py --trig bn081125496 --bin 4 --model CPL \
         --out results/convention_check
  python scripts/41c_paper_sed.py --trig bn081125496 --bin tint --model BAND \
         --out results/convention_check
"""
import os, sys, argparse, importlib.util, hashlib, json
import numpy as np
from scipy.integrate import quad

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from plot_style import apply_pub_style, PUB, det_color  # noqa: E402
apply_pub_style()


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "scripts", path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


P41 = _load("p41", "41_nuFnu_panels.py")     # build_plugins, _plugin_counts, _rebin_for_plot, model_error_band


def unfold_all_points(pl, photon_fn, sig, maxch):
    """STRICT XSPEC ratio-unfold: every group is a POINT with an error bar —
    XSPlot has no upper-limit path anywhere, so low-significance groups stay
    points and negative-net groups simply cannot render on the log axis,
    exactly as in XSPEC (Vikas, 2026-08-15). The rebin loop IS setplot rebin
    SIG MAXCH (CreateBinnedPlotGroups.cxx:675-676: close on net>0 &&
    net^2 >= var*sig^2, or at the channel cap; emit regardless), applied per
    contiguous noticed run so groups never bridge an ignored range."""
    ene_lo, ene_hi, obs, bkg, bkg_var, predicted = P41._plugin_counts(pl)
    # BREAK groups at every mask discontinuity (K-edge etc.) — the legacy
    # rebin runs over the COMPRESSED masked arrays and would happily merge
    # channels across an exclusion, planting a point visually inside the
    # ignored range (Vikas, 2026-08-14: 'how come there are data points in
    # the ignored energy ranges'). 41b's contiguous grouping was immune.
    breaks = np.flatnonzero(ene_lo[1:] > ene_hi[:-1] * (1 + 1e-9)) + 1
    parts = []
    for seg in np.split(np.arange(len(ene_lo)), breaks):
        if not len(seg):
            continue
        s = slice(seg[0], seg[-1] + 1)
        parts.append(P41._rebin_for_plot(ene_lo[s], ene_hi[s], obs[s], bkg[s],
                                         predicted[s], bkg_var[s], sig, maxch))
    if not parts:
        raise RuntimeError(f"{getattr(pl, 'name', '?')}: no active channels")
    g = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    if not np.all(np.isfinite(g["pred"])) or np.any(g["pred"] < 0):
        raise RuntimeError(f"{getattr(pl, 'name', '?')}: non-finite or negative folded model")
    emid = 0.5 * (g["lo"] + g["hi"])   # ARITHMETIC midpoint — XSPEC's plot X
    half = 0.5 * (g["hi"] - g["lo"])   # (PlotGroupCreator.cxx:50-54)
    net = g["obs"] - g["bkg"]
    se = np.sqrt(g["var"])
    # XSPEC eeufspec numerator (PlotUnfolded.cxx:114-129 + CreateBinnedPlot
    # Groups.cxx:792-857): E_lo*E_hi * integral(F dE)/(E_hi-E_lo), the group-
    # integrated photon model, by CONVERGED adaptive quadrature in log E
    # (Codex audit 2026-08-14: fixed 16-pt trapezoid erred 86.85% in the
    # 28-36 MeV CPL tail). NOTE: ratio-unfolded points remain conditional on
    # the assumed model + response — group integration is XSPEC's exact
    # construction, NOT a model-independence theorem; between our fitted
    # shapes the drift is ~0.5% max, but it can be severe where pred -> 0.
    nfm = np.empty(len(emid))
    for i, (lo, hi) in enumerate(zip(g["lo"], g["hi"])):
        val, _ = quad(lambda z: np.exp(z) * float(photon_fn(np.exp(z))),
                      np.log(lo), np.log(hi), epsabs=0.0, epsrel=1e-7, limit=200)
        if not np.isfinite(val) or val < 0:
            raise RuntimeError(f"invalid model integral in [{lo:.3g}, {hi:.3g}]: {val}")
        nfm[i] = lo * hi * val / (hi - lo)
    # XSPEC's rule (PlotUnfolded.cxx): a group is dropped ONLY when the folded
    # model is zero. The old pred>0.5-counts filter silently erased every
    # sparse high-BGO group — channels that ARE in the fit (Vikas, 2026-08-14:
    # "I don't know who asked you to ignore the whole energy range we are
    # using the data in").
    good = g["pred"] > 0.0
    nf = np.where(good, nfm * net / np.where(good, g["pred"], 1.0), np.nan)
    nfe = np.where(good, nfm * se / np.where(good, g["pred"], 1.0), np.nan)
    resid = np.where(good, (net - g["pred"]) / se, np.nan)
    # STRICT XSPEC (Vikas, 2026-08-15: "plot them exactly as XSPEC does" —
    # these are diagnostics; the community convention IS the spec):
    # every group is a point with its error bar, negative-net groups simply
    # cannot render on the log axis (PlotUnfolded emits them; log drops them).
    # NO invented upper-limit arrows in strict mode — kept only behind
    # --ul-arrows for exploratory use.
    is_ul = good & (net < 2.0 * se)                     # zero-consistent (arrow mode only)
    ul_val = nfm * (np.maximum(net, 0.0) + 2.0 * se) / np.where(good, g["pred"], 1.0)
    return dict(emid=emid, xlo=half, xhi=half,
                nf=nf, nfe=nfe, resid=resid, is_ul=is_ul, ul=ul_val, good=good,
                glo=g["lo"], ghi=g["hi"])


def fit_intervals(plugins, dets):
    """Per-detector fitted energy intervals from the plugin channel masks —
    the SAME source that shades the figure, and now also the bound for the
    model curve/axis (Vikas, 2026-08-14: 'why have you plotted below the
    energy range we never used')."""
    out = []
    for det, pl in zip(dets, plugins):
        try:
            eb = np.asarray(pl.response.ebounds, float)
            mask = np.asarray(pl.mask, bool)
        except Exception:
            continue
        idx = np.flatnonzero(mask)
        for seg in np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1):
            out.append((det, float(eb[seg[0]]), float(eb[seg[-1] + 1])))
    return out


def shade_ranges(ax_list, intervals):
    tints = {"n": "#e8985e", "b": "#8172b3", "l": "#8c8c8c"}
    for det, lo, hi in intervals:
        for ax in ax_list:
            ax.axvspan(lo, hi, color=tints.get(det[0], "0.8"), alpha=0.05, lw=0, zorder=0)


def native_band(jl, model, src_name, E):
    """68% band via threeML's OWN machinery — MLEResults samples the covariance
    in the minimizer's INTERNAL coordinates, rejects at bounds, transforms back
    (analysis_results.py:1571-1659), and FittedPointSourceSpectralHandler forms
    equal-tail nuFnu intervals from the correlated variates. The previous custom
    sampler applied the internal-coordinate covariance in EXTERNAL coordinates —
    statistically invalid (Codex audit 2026-08-14, item 6). threeML's OWN policy
    at high bound-rejection is WARN AND DRAW (analysis_results.py:1645) — so we
    draw, and print the retained fraction on the figure instead of suppressing
    (Vikas, 2026-08-15: the threeML-like band IS the requested product; an
    invented suppression threshold overrode that)."""
    try:
        from threeML.utils.fitted_objects.fitted_point_sources import (
            FittedPointSourceSpectralHandler,
        )
        first = next(iter(model.free_parameters))
        n_kept = len(jl.results.get_variates(first))
        frac = n_kept / 5000.0
        if frac < 0.05:
            # PI ruling (Vikas, 2026-08-15, F2): at >=95% railed the "band" is
            # the shape of the parameter bounds, not a credible interval —
            # suppress with the reason, never draw bounds geometry.
            return None, (f"68% band suppressed: {1.0 - frac:.0%} of draws railed "
                          f"at bounds (bounds geometry)"), frac
        h = FittedPointSourceSpectralHandler(jl.results, src_name, E, "keV",
                                             "keV/(cm2 s)", confidence_level=0.68,
                                             equal_tailed=True)
        blo = np.asarray(getattr(h.lower_error, "value", h.lower_error), float).ravel()
        bhi = np.asarray(getattr(h.upper_error, "value", h.upper_error), float).ravel()
        if blo.shape != np.shape(E) or not np.all(np.isfinite(bhi)):
            return None, "68% band unavailable: handler returned malformed interval", frac
        note = (f"68% band: native threeML; {1.0 - frac:.0%} of draws railed at "
                f"bounds (truncated Gaussian)" if frac < 0.99 else "")
        return (blo, bhi), note, frac
    except Exception as exc:
        return None, f"68% band unavailable: {exc}", None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trig", required=True)
    ap.add_argument("--bin", required=True, help="block index or 'tint'")
    ap.add_argument("--model", default="BAND", help="registry model name (BAND, CPL, ...)")
    ap.add_argument("--rebin", nargs=2, type=float, default=[5, 5], metavar=("SIG", "MAXCH"))
    ap.add_argument("--ul-arrows", action="store_true",
                    help="non-XSPEC exploratory mode: zero-consistent groups as 2-sigma arrows")
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "figures"))
    ap.add_argument("--fit-root", default=None,
                    help="root holding <trig>/spectral_fits.ecsv for seeding + the "
                         "AIC guard (default: --out)")
    a = ap.parse_args()

    from astropy.table import Table
    from threeML import DataList, JointLikelihood, Model, PointSource

    # --- bin edges from the blocks product; approved rows for dets/backgrounds
    appr = Table.read(os.path.join(ROOT, "results", "background_intervals.ecsv"))
    rows = appr[[str(x).strip() == a.trig for x in appr["TRIGGER_NAME"]]]
    dets = [str(r["DETECTOR"]).strip() for r in rows if str(r["DETECTOR"]).strip() != "lle"]
    nais = [d for d in dets if d.startswith("n")]
    ang = {str(r["DETECTOR"]).strip(): float(r["DET_ANGLE"]) for r in rows}
    # reference detector: ALWAYS the ENGINE'S stored choice when available.
    # Codex independent finding #2, materialized on burst 2 (2026-08-16):
    # engine ref n0 vs min-angle n1 reshuffles which detectors carry free
    # EACs -> a different likelihood parameterization -> systematic
    # |dAIC| ~ 0.1-0.5 guard refusals across ALL 168 pairs.
    ref = None
    _meta_p = os.path.join(a.fit_root or a.out, a.trig, "spectral_fits.json")
    if os.path.exists(_meta_p):
        try:
            _m = json.load(open(_meta_p))
            ref = _m.get("reference_det") or _m.get("canonical_det")
            _fd = _m.get("fit_dets")
            if _fd:
                dets = [d for d in dets if d in _fd]
        except Exception:
            ref = None
    if ref is None or ref not in dets:
        ref = min(nais, key=lambda d: ang.get(d, 999))
    blocks = Table.read(os.path.join(ROOT, "results", "sweep106", a.trig, "blocks",
                                     f"bb_blocks_spectral_{a.trig}.ecsv"))
    bt = blocks[[str(x).strip() == ref for x in blocks["DETECTOR"]]]
    if a.bin == "tint":
        t1, t2 = float(bt["T_START"][0]), float(bt["T_STOP"][-1]); tag = "TINT"
    else:
        r = bt[int(a.bin)]; t1, t2 = float(r["T_START"]), float(r["T_STOP"]); tag = f"bin{int(a.bin)}"

    bkg = {str(r["DETECTOR"]).strip(): ((float(r["BKG_NEG_START"]), float(r["BKG_NEG_STOP"])),
                                        (float(r["BKG_POS_START"]), float(r["BKG_POS_STOP"])))
           for r in rows}
    live, live_dets = P41.build_plugins(a.trig, dets, ref, t1, t2, bkg)
    if set(live_dets) != set(dets):
        raise RuntimeError(f"plugin set {live_dets} != approved detector set {dets}")
    # fail-loud EAC state check (Codex item 7: build_plugins swallows activation
    # errors — a figure must never run on a silently wrong nuisance state)
    for d, p in zip(live_dets, live):
        cons = {pk: pv for pk, pv in getattr(p, "nuisance_parameters", {}).items()
                if "cons" in pk.lower()}
        n_free = sum(1 for pv in cons.values() if pv.free)
        if d == ref and n_free:
            raise RuntimeError(f"reference {d} has a free EAC constant")
        if d != ref and n_free != 1:
            raise RuntimeError(f"{d}: EAC not active (free cons: {n_free}) — "
                               "build_plugins failed silently")

    # --- model from the ENGINE's own spec table (same builders, bounds, seeds)
    eng = P41.eng
    all_specs = (list(eng.MODEL_SPECS) + list(eng.SHAPE_MODEL_SPECS)
                 + list(eng.HIGHE_MODEL_SPECS) + list(eng.THREECOMP_MODEL_SPECS))
    want = a.model.upper().replace("+", "").replace(" ", "")
    spec = next(s for s in all_specs if s["prefix"] == want)

    # stored row (Codex item 9 steps 1-3): read BEFORE fitting — the engine's
    # solution seeds the live fit so the guard compares like with like (the
    # engine may have reached its solution via multistart; a default-seed live
    # fit can land in a different local minimum and be refused spuriously)
    stored_aic, srow = None, None
    blk = -1 if a.bin == "tint" else int(a.bin)
    fit_table = os.path.join(a.fit_root or a.out, a.trig, "spectral_fits.ecsv")
    if os.path.exists(fit_table):
        st = Table.read(fit_table)
        row = st[st["BLOCK"] == blk]
        if len(row):
            srow = row[0]
            colname = f"{spec['prefix']}_AIC"
            if colname in st.colnames and np.isfinite(float(srow[colname])):
                stored_aic = float(srow[colname])

    shape = spec["build"]({})          # engine defaults...
    if srow is not None and spec.get("pmap"):
        # ...overridden by the ENGINE's own serialized solution via its pmap
        for colsuf, pshort in spec["pmap"].items():
            col = f"{spec['prefix']}_{colsuf}"
            if col in srow.colnames and np.isfinite(float(srow[col])):
                for pk, pp in shape.free_parameters.items():
                    if pk.split(".")[-1] == pshort:
                        v = float(srow[col])
                        if pp.min_value is not None:
                            v = max(v, float(pp.min_value))
                        if pp.max_value is not None:
                            v = min(v, float(pp.max_value))
                        pp.value = v
    model = Model(PointSource(a.trig, 0.0, 0.0, spectral_shape=shape))
    # EAC already activated on non-reference detectors by build_plugins
    jl = JointLikelihood(model, DataList(*live))
    if srow is not None:
        for d in live_dets:
            col = f"{spec['prefix']}_EAC_{d.upper()}"
            if col in srow.colnames and np.isfinite(float(srow[col])):
                for pk, pp in model.free_parameters.items():
                    if f"cons_{d}" in pk.lower() and pp.free:
                        pp.value = min(max(float(srow[col]), float(pp.min_value)),
                                       float(pp.max_value))
    # threeML's MLEResults draws its bounded samples from the GLOBAL numpy
    # RNG — unseeded, the band-suppression percentage jittered between
    # renders (round-11: 52%->50%, 46%->43%). Seed = deterministic figure.
    np.random.seed(20260814)
    fit_error = None
    try:
        jl.fit(quiet=True)
        n2ll = float(jl.results.get_statistic_frame()["-log(likelihood)"]["total"]) * 2.0
    except Exception as exc:
        # Class-B: deeply railed fits crash threeML's own error propagation
        # INSIDE jl.fit (empty variates -> percentile IndexError). Route to
        # frozen replay instead of dying (NO-MODEL-DROPPED rule).
        fit_error = f"{type(exc).__name__}: {str(exc)[:60]}"
        n2ll = np.nan
    kfree = len(model.free_parameters)
    aic = n2ll + 2.0 * kfree

    # STORED-SOLUTION GUARD (Codex item 9 step 5) + PI RULING (Vikas,
    # 2026-08-16: "we are not dropping any models"): a drifted live fit does
    # NOT exile the model — fall back to a FROZEN REPLAY of the stored
    # solution (params set exactly, NO minimization), which must reproduce
    # the stored AIC or the figure is refused as a STRUCTURAL mismatch.
    fit_mode = "live"
    if fit_error is not None and stored_aic is None:
        raise RuntimeError(f"fit crashed ({fit_error}) and no stored reference exists")
    if (fit_error is not None) or (stored_aic is not None and abs(aic - stored_aic) > 0.1):
        if srow is not None and spec.get("pmap"):
            for colsuf, pshort in spec["pmap"].items():
                col = f"{spec['prefix']}_{colsuf}"
                if col in srow.colnames and np.isfinite(float(srow[col])):
                    for pk, pp in shape.free_parameters.items():
                        if pk.split(".")[-1] == pshort:
                            v = float(srow[col])
                            if pp.min_value is not None: v = max(v, float(pp.min_value))
                            if pp.max_value is not None: v = min(v, float(pp.max_value))
                            pp.value = v
        for d in live_dets:
            col = f"{spec['prefix']}_EAC_{d.upper()}"
            if srow is not None and col in srow.colnames and np.isfinite(float(srow[col])):
                for pk, pp in model.free_parameters.items():
                    if f"cons_{d}" in pk.lower() and pp.free:
                        pp.value = min(max(float(srow[col]), float(pp.min_value)),
                                       float(pp.max_value))
        n2ll = -2.0 * sum(float(p.get_log_like()) for p in live)
        aic_frozen = n2ll + 2.0 * kfree
        if abs(aic_frozen - stored_aic) <= 0.1:
            fit_mode = "frozen_replay"
            aic = aic_frozen
        else:
            raise RuntimeError(
                f"STRUCTURAL mismatch: frozen replay AIC {aic_frozen:.4f} != "
                f"stored {stored_aic:.4f} (live: "
                f"{'crashed ' + fit_error if fit_error else f'drift {abs(aic - stored_aic):.4f}'}) "
                "— data/mask difference, refused")

    comp = shape
    nufnu = lambda E: np.asarray(E, float) ** 2 * np.asarray(comp(np.asarray(E, float)), float)

    # --- figure
    fig = plt.figure(figsize=(PUB["figwidth"], PUB["figwidth"] * 1.05))
    gs = fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.0,
                          top=0.93, bottom=0.10, left=0.13, right=0.97)
    ax = fig.add_subplot(gs[0]); rax = fig.add_subplot(gs[1], sharex=ax)
    ax.set_xscale("log"); ax.set_yscale("log"); rax.set_xscale("log")
    ivals = fit_intervals(live, live_dets)
    fit_lo = min(lo for _, lo, _ in ivals)
    fit_hi = max(hi for _, _, hi in ivals)
    shade_ranges([ax, rax], ivals)

    DET_COL = {"na": "#1b7a8c", "nb": "#e2a13d", "b1": "#b23a6b",
               "n0": "#1b7a8c", "n1": "#2f6b9e", "n2": "#e2a13d", "b0": "#b23a6b"}
    e_all, y_all, ks, group_counts = [], [], {}, {}
    for d, p in zip(live_dets, live):
        # each plugin's own EAC constant (1 for the reference, fitted otherwise)
        k = 1.0
        for pk, pv in getattr(p, "nuisance_parameters", {}).items():
            if "cons" in pk.lower() and pv.free:
                k = float(pv.value)
        ks[d] = k
        u = unfold_all_points(p, comp, a.rebin[0], int(a.rebin[1]))
        # SINGLE-CURVE DISPLAY (Vikas, 2026-08-15): XSPEC draws k*F(E) per
        # dataset, so its curves split; we draw ONE model, so the constants
        # move to the DATA — non-reference points are divided by their fitted
        # k onto the k=1 frame. The plain ratio nfm*net/pred does exactly
        # this automatically (pred contains k, the numerator does not).
        # k values are disclosed in the legend labels.
        col = DET_COL.get(d) or (det_color(d) if callable(det_color) else None) or "0.4"
        pts = u["good"] if not a.ul_arrows else (u["good"] & ~u["is_ul"])
        lab = d if d == ref else f"{d} (k={k:.3f})"
        ax.errorbar(u["emid"][pts], u["nf"][pts], yerr=u["nfe"][pts],
                    xerr=[u["xlo"][pts], u["xhi"][pts]], fmt="o", ms=4.5, lw=1.1,
                    color=col, label=lab, zorder=4)
        if a.ul_arrows and u["is_ul"].any():
            ul = u["is_ul"]
            ax.errorbar(u["emid"][ul], u["ul"][ul], xerr=[u["xlo"][ul], u["xhi"][ul]],
                        yerr=u["ul"][ul] * 0.25, uplims=True, fmt="none", lw=1.0,
                        color=col, alpha=0.8, zorder=3)
        rax.errorbar(u["emid"][u["good"]], u["resid"][u["good"]],
                     yerr=np.ones(int(u["good"].sum())),
                     xerr=[u["xlo"][u["good"]], u["xhi"][u["good"]]],
                     fmt="o", ms=3.5, lw=0.9, color=col, zorder=3)
        e_all += [u["glo"][u["good"]].min(), u["ghi"][u["good"]].max()]
        group_counts[d] = {"groups": int(len(u["emid"])), "plotted": int(pts.sum()),
                           "eac": k}
        y_all += [v for v in u["nf"][pts] if np.isfinite(v) and v > 0]

    # model/band/axis span the FULL FITTED RANGE — every fitted channel is in
    # the likelihood, so every fitted channel is on the figure; nothing beyond
    # either fitted edge (Vikas, 2026-08-14, both directions)
    E = np.geomspace(fit_lo, fit_hi, 400)
    if fit_mode == "frozen_replay":
        band, note, band_frac = None, "68% band n/a: frozen replay of the stored solution", None
    else:
        band, note, band_frac = native_band(jl, model, a.trig, E)
    band_out_frac = None
    if band is not None:
        # F3 guard (Vikas, 2026-08-15: "the shaded band ... is nowhere close to
        # the modeled curve"): around a railed solution the truncated draw
        # cloud is one-sided, so the 16/84 interval can EXCLUDE the best-fit
        # curve. Such an interval is malformed — suppress it with the reason
        # (notes-review fix queue F3; same doctrine as the >=95%-railed rule).
        _mle = nufnu(E)
        band_out_frac = float(np.mean((_mle < band[0]) | (_mle > band[1])))
        if band_out_frac > 0.10:
            band = None
            note = (f"68% band suppressed: interval excludes the best-fit curve "
                    f"over {band_out_frac:.0%} of the range (railed solution)")
    if band is not None:
        ax.fill_between(E, band[0], band[1], color="0.55", alpha=0.35, lw=0, zorder=2)
    if note:
        # zorder=3: BELOW points (4) and curve (5), above band (2) — round-14
        # B2: an above-data backing box always ends up washing out some
        # marker/bar; below-data, the data simply draws over the white box.
        # y=0.085: round-10 N1 (run-on footer at y=0.02).
        ax.text(0.02, 0.085, note, transform=ax.transAxes,
                fontsize=PUB["tick_size"] - 4, color="0.4", zorder=3,
                bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=1.5))
    ax.plot(E, nufnu(E), color="black", lw=2.4, zorder=5,
            label=f"{spec['name']} fit")
    # MODEL COMPONENTS, XSPEC-style dotted (Vikas, 2026-08-16: "plot the model
    # components also ... like XSPEC does / my GRB 190114C figure" — threeML's
    # plot_spectra has no native component mode; astromodels' CompositeFunction
    # .functions supplies the additive terms directly)
    _comps = getattr(shape, "functions", None)
    if _comps and len(_comps) > 1:
        _ccol = ["#7a5195", "#3d8f6e", "#b07714"]
        for _i, _fn in enumerate(_comps):
            try:
                _cy = np.asarray(E, float) ** 2 * np.asarray(_fn(np.asarray(E, float)), float)
                ax.plot(E, _cy, ls=":", lw=1.5, color=_ccol[_i % 3], zorder=4,
                        label=getattr(_fn, "name", f"component {_i+1}"))
            except Exception as _ce:
                print(f"  [warn] component {_i}: {_ce}")
    # cross-normalization disclosure (Codex item 7): short, left, stamp-row —
    # vertically separated from the band note at y=0.085 (round-10 N1)
    ax.text(0.02, 0.02, f"{', '.join(d for d in live_dets if d != ref)} points / k "
            f"(k=1 frame, ref {ref})", transform=ax.transAxes,
            fontsize=PUB["tick_size"] - 4, color="0.4", zorder=3,
            bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=1.5))

    ax.set_xlim(fit_lo / 1.02, fit_hi * 1.02)       # fitted range, minimal pad (round-9 N4)
    # y-range from the DATA, exactly XSPEC's rule (PlotUnfolded::setRanges,
    # lines 247-264): y2 = 2*yMax, y1 = max(yMin, 1e-5*y2). Without this a
    # cutoff model drawn to 38 MeV drags the autoscale to 1e-115 and
    # flattens every data point (caught on bin-4 CPL, 2026-08-14).
    if y_all:
        y2 = 2.0 * max(y_all)
        # /1.8 headroom below the lowest datum (round-9 N3: XSPEC's literal
        # y1=yMin bisected the lowest marker on the frame)
        y1 = max(min(y_all) / 1.8, 1.0e-5 * y2)
        ax.set_ylim(y1, y2)
    rax.axhline(0, color="black", ls="--", lw=1.0)
    ax.set_ylabel(r"$\nu F_\nu$ (keV$^2$ s$^{-1}$ cm$^{-2}$ keV$^{-1}$)")
    # honest label (Codex item 8): Gaussian standardized count residual —
    # NOT pgstat delchi (XSPEC's PGstat delchi uses the Cstat-family
    # model-error rule, queued as the exact upgrade)
    rax.set_ylabel(r"(net$-$model)/$\sigma$"); rax.set_xlabel("Energy (keV)")
    plt.setp(ax.get_xticklabels(), visible=False)
    # upper LEFT: round-10 B3 — with the arrow forest gone the y-ceiling
    # dropped and an upper-right legend occluded the 8-25 MeV b1 points;
    # the low-energy corner of a rising spectrum is empty
    ax.legend(loc="upper left")
    ax.set_title(f"{a.trig} — {tag} [{t1:.2f}, {t2:.2f}] s ({spec['name']})", loc="left")
    # stamp lives in the TOP MARGIN, outside the axes (round-13 B1: any in-axes
    # backing box eventually hides a data point near the floor — occlusion is
    # impossible by construction out here, and no bbox is needed).
    # plain text, not U+2713: round-10 B2 — STIX serif has no checkmark glyph
    guard = ("FROZEN REPLAY of stored solution" if fit_mode == "frozen_replay"
             else "matches stored" if stored_aic is not None
             else "no stored ref (diagnostic)")
    # F1 (burst-2 notes): near-degenerate EAC plateaus — live EACs can differ
    # from the engine's railed values at |dAIC|<0.1; disclose, never hide
    if srow is not None:
        for d in live_dets:
            col = f"{spec['prefix']}_EAC_{d.upper()}"
            if col in srow.colnames and np.isfinite(float(srow[col]))                and abs(ks.get(d, 1.0) - float(srow[col])) > 0.01:
                guard += " | EAC plateau (live≠stored, dAIC<0.1)"
                break
    # y=1.07: own row ABOVE the title line (round-14 B1: same-row right
    # alignment overprinted the title's trailing "(Model)").
    # PGstat/dof printed with AIC (Vikas, 2026-08-15: the statistic is read as
    # a SUPPLEMENT to the residual panel) — dof = active channels − free params
    nchan = sum(int(np.asarray(p.mask, bool).sum()) for p in live)
    dof = nchan - kfree
    ax.text(1.0, 1.07,
            f"PGstat/dof={n2ll:.1f}/{dof} | AIC={aic:.1f} ({kfree} free) | {guard}",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=PUB["tick_size"] - 4, color="0.35")

    os.makedirs(a.out, exist_ok=True)
    stem = os.path.join(a.out, f"{a.trig}_SED_{tag}_{spec['name'].replace('+','')}")
    fig.savefig(stem + ".png", bbox_inches="tight")
    fig.savefig(stem + ".pdf", bbox_inches="tight")
    # machine-readable provenance next to the figure (Codex independent finding
    # 3: a PNG must be able to prove which source/inputs/solution produced it)
    with open(os.path.abspath(__file__), "rb") as fh:
        src_sha = hashlib.sha256(fh.read()).hexdigest()
    prov = dict(script="41c_paper_sed.py", script_sha256=src_sha,
                argv=sys.argv[1:], trig=a.trig, bin=str(a.bin),
                model=spec["name"], detectors=list(live_dets), reference=ref,
                interval_s=[t1, t2], eac=ks, groups=group_counts,
                fit_mode=fit_mode, live_fit_error=fit_error,
                aic_live=aic, aic_stored=stored_aic, n2ll_live=n2ll,
                pgstat=n2ll, dof=dof, n_active_channels=nchan,
                band=("drawn" if band is not None else (note or "none")),
                band_native_keep_frac=band_frac,
                band_curve_outside_frac=band_out_frac,
                rebin=[a.rebin[0], int(a.rebin[1])], ul_arrows=bool(a.ul_arrows),
                x_display=[fit_lo / 1.02, fit_hi * 1.02],
                fitted_range_keV=[fit_lo, fit_hi],
                display_frame="k1_cross_normalized (points / k; Vikas 2026-08-15)",
                rng_seed=20260814,
                ranges_convention="Chand2020_ApJ903_9")
    with open(stem + ".json", "w") as fh:
        json.dump(prov, fh, indent=1)
    print("WROTE", stem + ".png")


if __name__ == "__main__":
    main()

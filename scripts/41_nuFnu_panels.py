#!/usr/bin/env python
"""scripts/41_nuFnu_panels.py -- DIAGNOSTIC nuFnu panels for a burst.

Each panel = ratio-unfolded nuFnu data (per detector, XSPEC-rebinned, with 2-sigma
UPPER LIMITS for faint groups) + fitted model with a native-3ML-style 68% error
band (covariance -> MVN via SVD -> quantiles) + a count-space sigma-residual strip
with unit (+/-1) error bars, 1:1 with the data points.

This mirrors LATBright GRB260226A/s05a_spectral_plots.py (proven, verified) --
counts-based XSPEC rebin (Xspec/src/XSPlot/Plot/CreateBinnedPlotGroups.cxx), the
model_error_band native-propagation recipe, and the eeufspec unfolding. It is the
scripts/41 generalization to ANY of our models (engine MODEL/SHAPE/HIGHE specs).

Modes (the point is DIAGNOSIS -- see every model on every bin):
  --mode bin   --bin N          ONE bin, ALL models       (which model fits bin N?)
  --mode model --model NAME     ONE model, ALL bins       (evolution under a model)
  --mode best                   best-AIC model per bin     (evolution montage)

Heavy env (conda activate threeML + CALDB). Run from repo root, e.g.:
  python scripts/41_nuFnu_panels.py --trig bn081125496 --mode bin --bin 5 \
      --dets na,nb,b1 --ref na --rebin 5 5 --out results/figures/

Skill: dev/ai_guides/SpectralFitting.md L10 (nuFnu eye-diagnostic) + L11 (residual
grammar). Data points are ratio-unfolded (model-dependent); inference is count-space.
"""
import os, sys, argparse, importlib.util
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from astropy.table import Table

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("engine10", os.path.join(ROOT, "scripts", "10_spectral_fit_burst.py"))
eng = importlib.util.module_from_spec(_spec); sys.modules["engine10"] = eng; _spec.loader.exec_module(eng)
from threeML import Model, PointSource, JointLikelihood, DataList

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "stix", "font.size": 11,
    "xtick.direction": "in", "ytick.direction": "in", "xtick.top": True, "ytick.right": True,
    "xtick.minor.visible": True, "ytick.minor.visible": True, "savefig.dpi": 180})

COLORS = {"na": "#b3216a", "n0": "#b3216a", "n1": "#f08c4b", "n3": "#f5c518", "nb": "#f08c4b",
          "b0": "#3aa6a0", "b1": "#3aa6a0", "lle": "#5b3fa0", "lat": "#5b8fd6"}
def detlabel(d): return {"lle": "LLE", "lat": "LAT"}.get(d, d.upper())

ALL_SPECS = list(eng.MODEL_SPECS) + list(eng.SHAPE_MODEL_SPECS) + list(eng.HIGHE_MODEL_SPECS)
SPEC_BY_NAME = {s['name']: s for s in ALL_SPECS}
SPEC_BY_PREFIX = {s['prefix']: s for s in ALL_SPECS}

# rebin defaults: pyXSPEC 'setplot rebin 5 5' (group to 5 sigma OR <=5 channels)
REBIN_SIG, REBIN_MAX = 5.0, 5

# ---------------- plotting helpers (LATBright-faithful) ------------------------
def _rebin_for_plot(ene_lo, ene_hi, obs, bkg, predicted, bkg_var, sig_floor, max_group):
    """XSPEC-style plotting rebin (verified vs HEASoft 6.30.1
    Xspec/src/XSPlot/Plot/CreateBinnedPlotGroups.cxx): group adjacent channels
    until net significance >= sig_floor OR max_group channels. Significance
    denominator = data Poisson var (max(obs,1)) + background var, in quadrature.
    Sub-floor groups become 2-sigma UPPER LIMITS. Display only; fit untouched."""
    if bkg_var is None: bkg_var = np.zeros_like(np.asarray(obs, float))
    g = {k: [] for k in ("lo", "hi", "obs", "bkg", "pred", "var", "ul")}
    i, n = 0, len(obs)
    while i < n:
        o = b = p = v = 0.0; j = i
        while j < n:
            o += obs[j]; b += bkg[j]; p += predicted[j]; v += bkg_var[j]; j += 1
            var = max(o, 1.0) + v; sig = (o - b) / np.sqrt(var)
            if sig >= sig_floor or (j - i) >= max_group: break
        var = max(o, 1.0) + v; sig = (o - b) / np.sqrt(var)
        g["lo"].append(ene_lo[i]); g["hi"].append(ene_hi[j-1]); g["obs"].append(o)
        g["bkg"].append(b); g["pred"].append(p); g["var"].append(var); g["ul"].append(sig < sig_floor)
        i = j
    return {k: np.array(v) for k, v in g.items()}

def _plugin_counts(pl):
    mask = np.array(pl.mask, bool)
    eb = np.array(pl.response.ebounds, float)
    ene_lo, ene_hi = eb[:-1][mask], eb[1:][mask]
    obs = np.array(pl.observed_counts, float)[mask]
    bkg = np.array(pl.background_counts, float)[mask]
    berr = getattr(pl, "background_count_errors", None)
    bkg_var = (np.array(berr, float)[mask] ** 2) if berr is not None else None
    predicted = np.array(pl.get_model(), float)   # active channels only
    return ene_lo, ene_hi, obs, bkg, bkg_var, predicted

def _ev(f, E):
    try: return np.asarray(f(E), float)
    except Exception: return np.array([float(f(e)) for e in np.atleast_1d(E)])

def unfold_detector(pl, nufnu_fn, sig_floor, max_group):
    """Ratio-unfolded nuFnu data + count-space sigma residual for ONE plugin, on
    the SAME XSPEC-rebin groups (1:1 points). nuFnu_data = nuFnu_model*(obs-bkg)/pred;
    residual = (net-pred)/sqrt(var) (unit error bar). Faint groups -> 2-sigma UL."""
    if not hasattr(pl, "observed_counts"): return None       # LAT unbinned: skip
    try:
        ene_lo, ene_hi, obs, bkg, bkg_var, predicted = _plugin_counts(pl)
        if len(predicted) != len(obs): return None
        g = _rebin_for_plot(ene_lo, ene_hi, obs, bkg, predicted, bkg_var, sig_floor, max_group)
        emid = np.sqrt(g["lo"] * g["hi"]); net = g["obs"] - g["bkg"]; se = np.sqrt(g["var"])
        nfm = _ev(nufnu_fn, emid)
        good = g["pred"] > 0.5
        nf = np.full_like(emid, np.nan); nfe = np.full_like(emid, np.nan); resid = np.full_like(emid, np.nan)
        nf[good] = nfm[good] * net[good] / g["pred"][good]
        nfe[good] = nfm[good] * se[good] / g["pred"][good]
        resid[good] = (net[good] - g["pred"][good]) / se[good]
        ul = g["ul"] & good
        nf[ul] = nfm[ul] * (np.maximum(net[ul], 0.0) + 2.0 * se[ul]) / g["pred"][ul]
        xerr = np.array([emid - g["lo"], g["hi"] - emid])
        return dict(emid=emid, xerr=xerr, nufnu=nf, nufnu_err=nfe, is_ul=g["ul"], resid=resid)
    except Exception as e:
        print("   [WARN] unfold %s: %s" % (getattr(pl, "name", "?"), e)); return None

def data_range(plugins):
    dlo, dhi = np.inf, 0.0
    for pl in plugins:
        if not hasattr(pl, "observed_counts"): continue
        eb = np.array(pl.response.ebounds, float); mask = np.array(pl.mask, bool)
        if mask.any():
            dlo = min(dlo, eb[:-1][mask][0]); dhi = max(dhi, eb[1:][mask][-1])
    return dlo, dhi

def model_error_band(jl, comp, E, n_samples=400, cl=0.68):
    """68% nuFnu band the native-3ML way (AnalysisResults covariance -> MVN via SVD
    -> per-energy quantiles; symmetrize+jitter for PSD). Model-agnostic: mutates
    jl's own free SOURCE params (skips EAC 'cons_*' norms), evaluates comp(E),
    restores. Returns (lo, hi) or None (e.g. railed/ill-conditioned covariance)."""
    try:
        fp = jl.likelihood_model.free_parameters; names = list(fp.keys())
        mean = np.array([fp[n].value for n in names], float)
        cov = np.asarray(jl.covariance_matrix, float)
        if cov.shape != (len(names), len(names)) or not np.all(np.isfinite(cov)): return None
        cov = 0.5 * (cov + cov.T) + 1e-12 * np.eye(len(names))
        rng = np.random.default_rng(42)
        samples = rng.multivariate_normal(mean, cov, size=n_samples, method="svd")
        curves = []
        for s in samples:
            ok = True
            for n, v in zip(names, s):
                if 'cons' in n.lower(): continue
                p = fp[n]
                if (p.min_value is not None and v < p.min_value) or (p.max_value is not None and v > p.max_value):
                    ok = False; break
            if not ok: continue
            for n, v in zip(names, s):
                if 'cons' in n.lower(): continue
                fp[n].value = v
            curves.append(E**2 * _ev(comp, E))
        for n, v in zip(names, mean): fp[n].value = v
        if len(curves) < 10: return None
        C = np.array(curves); qlo, qhi = 50*(1-cl), 50*(1+cl)
        return np.nanpercentile(C, qlo, axis=0), np.nanpercentile(C, qhi, axis=0)
    except Exception as e:
        print("   [WARN] band: %s" % e); return None

# ---------------- context, build, fit ------------------------------------------
def load_ctx(trig):
    gs = Table.read(os.path.join(ROOT, "results", "grb_sample.ecsv"), format="ascii.ecsv")
    row = gs[[str(x["TRIGGER_NAME"]).strip() == trig for x in gs]][0]
    eng.SRC_RA, eng.SRC_DEC = float(row["RA"]), float(row["DEC"])
    # BKG_FILE: same reasoning as BLOCKS_ROOT below -- the panels must use the SAME
    # background windows as the fits they display. A run made with corrected/alternative
    # windows (e.g. a walkthrough arm) otherwise gets panels drawn on the gated catalog's
    # windows and silently disagrees with its own fit. Default = the gated catalog.
    bk = Table.read(os.environ.get("BKG_FILE",
                                   os.path.join(ROOT, "results", "background_intervals.ecsv")),
                    format="ascii.ecsv")
    bk = bk[bk["TRIGGER_NAME"] == trig]
    appr = {str(r["DETECTOR"]).strip(): ((float(r["BKG_NEG_START"]), float(r["BKG_NEG_STOP"])),
            (float(r["BKG_POS_START"]), float(r["BKG_POS_STOP"]))) for r in bk}
    # BLOCKS_ROOT: read the SAME block set the plotted fits came from (see scripts/34, /38).
    # Default = results/clean_blocks (scripts/27 output); set BLOCKS_ROOT=results/
    # clean_blocks_human_final for the human-reviewed arm, or the panels are drawn on a
    # DIFFERENT run's bins than the fits they display.
    blocks_root = os.environ.get("BLOCKS_ROOT", os.path.join(ROOT, "results", "clean_blocks"))
    t = Table.read(os.path.join(blocks_root, "bb_blocks_spectral_%s.ecsv" % trig), format="ascii.ecsv")
    # de-duplicate per-detector rows -> unique (T_START, T_STOP) bins, order preserved
    seen, ts, te, sg = set(), [], [], []
    for r in t:
        k = (round(float(r["T_START"]), 4), round(float(r["T_STOP"]), 4))
        if k in seen:
            continue
        seen.add(k); ts.append(k[0]); te.append(k[1]); sg.append(float(r["SIGNIFICANCE"]))
    return appr, ts, te, sg

def build_plugins(trig, dets, ref, t1, t2, appr):
    plugins, names = [], []
    for det in dets:
        if det not in appr: continue
        sl = eng.build_spectrumlike_per_block(trig, det, appr[det][0], appr[det][1], [t1], [t2])
        if sl and sl[0] is not None:
            pl = sl[0]
            if det != ref:
                try: pl.use_effective_area_correction(*eng.EFFAREA_BOUNDS)
                except Exception: pass
            plugins.append(pl); names.append(det)
    return plugins, names

def fit_spec(spec, plugins, seed=None):
    comp = spec['build'](seed or {})
    ps = PointSource("grb", eng.SRC_RA, eng.SRC_DEC, spectral_shape=comp)
    jl = JointLikelihood(Model(ps), DataList(*plugins)); jl.set_minimizer("minuit")
    try:
        jl.fit(quiet=True)
        n2ll = 2.0 * jl.current_minimum; k = len(jl.likelihood_model.free_parameters)
        return jl, comp, n2ll + 2*k, True
    except Exception as ex:
        print("   fit failed for %s: %s" % (spec['name'], ex)); return None, comp, float('inf'), False

# ---------------- one diagnostic panel -----------------------------------------
def draw_panel(fig, gs_cell, plugins, names, jl, comp, title, ok, rebin, show_comp=True):
    inner = gs_cell.subgridspec(2, 1, height_ratios=[3, 1], hspace=0.0)
    ax = fig.add_subplot(inner[0]); axr = fig.add_subplot(inner[1], sharex=ax)
    if not ok or not plugins:
        ax.text(0.5, 0.5, "FIT FAILED", ha="center", va="center", transform=ax.transAxes, color="red")
        ax.set_title(title, fontsize=9, loc="left"); return
    sig_floor, max_group = rebin
    dlo, dhi = data_range(plugins)
    if not (np.isfinite(dlo) and np.isfinite(dhi)) or dhi <= dlo: dlo, dhi = 8.0, 4.0e4
    E = np.logspace(np.log10(dlo), np.log10(dhi), 200)
    nufnu_fn = lambda ee: np.asarray(ee, float)**2 * _ev(comp, np.asarray(ee, float))
    comp_h = []
    subs = getattr(comp, "functions", None)
    if show_comp and subs is not None and len(subs) > 1:
        cls = [":", "--", "-."]
        for k, sf in enumerate(subs):
            try: nuc = E**2 * _ev(sf, E)
            except Exception: continue
            ln, = ax.loglog(E, nuc, ls=cls[k % 3], lw=1.2, color="#222222", alpha=0.9, zorder=3, label="Component %d" % (k+1))
            comp_h.append(ln)
    band = model_error_band(jl, comp, E)
    if band is not None:
        ax.fill_between(E, band[0], band[1], color="0.55", alpha=0.32, lw=0, zorder=2, label="68% band")
    med = E**2 * _ev(comp, E)
    ax.loglog(E, med, color="0.15", lw=1.8, zorder=5, label="Model")
    data_max = 0.0                        # y-limits are set by the DATA, not the model:
    for pl, det in zip(plugins, names):   # a railed fit then shoots off-scale (honest) instead of hiding the data
        ud = unfold_detector(pl, nufnu_fn, sig_floor, max_group)
        if ud is None: continue
        c = COLORS.get(det, "gray")
        det_ok = (~ud["is_ul"]) & np.isfinite(ud["nufnu"]) & np.isfinite(ud["nufnu_err"]) & (ud["nufnu"] > 0)
        if np.any(det_ok):
            ax.errorbar(ud["emid"][det_ok], ud["nufnu"][det_ok], yerr=ud["nufnu_err"][det_ok],
                        xerr=ud["xerr"][:, det_ok], fmt="o", ms=3, color=c, alpha=0.85,
                        elinewidth=0.8, capsize=0, lw=0, label=detlabel(det), zorder=4)
            v = (ud["nufnu"][det_ok] + ud["nufnu_err"][det_ok]); v = v[np.isfinite(v)]
            if len(v): data_max = max(data_max, float(v.max()))
        ul = ud["is_ul"] & np.isfinite(ud["nufnu"]) & (ud["nufnu"] > 0)
        if np.any(ul):
            ax.errorbar(ud["emid"][ul], ud["nufnu"][ul], yerr=ud["nufnu"][ul]*0.35,
                        xerr=ud["xerr"][:, ul], uplims=True, fmt="none", color=c, alpha=0.5,
                        elinewidth=0.8, capsize=0, zorder=3)
            v = ud["nufnu"][ul][np.isfinite(ud["nufnu"][ul])]
            if len(v): data_max = max(data_max, float(v.max()))
        rd = np.isfinite(ud["resid"]) & (~ud["is_ul"])
        if np.any(rd):
            axr.errorbar(ud["emid"][rd], ud["resid"][rd], yerr=1.0, xerr=ud["xerr"][:, rd],
                         fmt="o", ms=2.5, color=c, alpha=0.75, elinewidth=0.6, capsize=0, lw=0)
    if data_max <= 0:                     # no data: fall back to the median model's peak
        mf = med[np.isfinite(med)]; data_max = float(mf.max()) if len(mf) else 1.0
    if not np.isfinite(data_max) or data_max <= 0: data_max = 1.0
    ax.set_ylim(data_max*3e-4, data_max*4); ax.set_xlim(dlo*0.9, dhi*1.1)
    ax.set_xscale("log"); ax.set_yscale("log")
    axr.axhline(0, color="k", lw=0.7); axr.set_ylim(-5, 5); axr.set_xscale("log")
    axr.set_xlim(dlo*0.9, dhi*1.1); axr.set_yticks([-4, 0, 4])
    plt.setp(ax.get_xticklabels(), visible=False)
    ax.set_title(title, fontsize=9, loc="left")
    if comp_h: ax.legend(handles=comp_h, fontsize=6.5, loc="lower left", framealpha=0.9, edgecolor="0.7")

# ---------------- modes --------------------------------------------------------
def _grid_shape(n):
    ncol = min(4, n); return int(np.ceil(n / ncol)), ncol

def run(trig, dets, ref, mode, which, out, rebin):
    appr, starts, stops, sigs = load_ctx(trig)
    dets = [d for d in dets if d in appr]; os.makedirs(out, exist_ok=True)

    if mode == "bin":
        # --bin tint (or -1): the TIME-INTEGRATED interval = the block union, i.e. the
        # same window scripts/10 uses for its T_INT row ("fallback to BB block union").
        # Without this, T_INT -- the row most often quoted against the literature -- is
        # the ONE interval that can never be diagnosed with a panel.
        is_tint = str(which).strip().lower() in ("tint", "t_int", "-1")
        if is_tint:
            b, t1, t2 = -1, float(min(starts)), float(max(stops))
        else:
            b = int(which); t1, t2 = starts[b], stops[b]
        plugins, names = build_plugins(trig, dets, ref, t1, t2, appr)
        specs = ALL_SPECS; nrow, ncol = _grid_shape(len(specs))
        fig = plt.figure(figsize=(4.2*ncol, 3.6*nrow))
        gs = fig.add_gridspec(nrow, ncol, hspace=0.42, wspace=0.26, top=0.93, bottom=0.06, left=0.06, right=0.99)
        for i, spec in enumerate(specs):
            jl, comp, aic, ok = fit_spec(spec, plugins)
            draw_panel(fig, gs[i // ncol, i % ncol], plugins, names, jl, comp,
                       "%s   AIC=%.0f" % (spec['name'], aic) if ok else "%s (failed)" % spec['name'], ok, rebin)
        _lab = "T_INT (block union)" if is_tint else "bin %d" % b
        _sig = "" if is_tint else "  S=%.0f" % sigs[b]
        fig.suptitle("%s  %s  [%.2f,%.2f]s%s  -- ALL models (diagnostic)" % (trig, _lab, t1, t2, _sig), fontsize=13)
        fname = os.path.join(out, "%s_nuFnu_%s_allmodels.png" % (trig, "TINT" if is_tint else "bin%d" % b))

    elif mode == "model":
        spec = SPEC_BY_NAME.get(which) or SPEC_BY_PREFIX.get(which)
        if spec is None: raise SystemExit("unknown model %s; choose from %s" % (which, list(SPEC_BY_NAME)))
        nrow, ncol = _grid_shape(len(starts))
        fig = plt.figure(figsize=(4.2*ncol, 3.6*nrow))
        gs = fig.add_gridspec(nrow, ncol, hspace=0.42, wspace=0.26, top=0.93, bottom=0.06, left=0.06, right=0.99)
        for i, (t1, t2) in enumerate(zip(starts, stops)):
            plugins, names = build_plugins(trig, dets, ref, t1, t2, appr)
            jl, comp, aic, ok = fit_spec(spec, plugins)
            draw_panel(fig, gs[i // ncol, i % ncol], plugins, names, jl, comp,
                       "bin%d [%.2f,%.2f] S=%.0f AIC=%.0f" % (i, t1, t2, sigs[i], aic), ok, rebin)
        fig.suptitle("%s  -- model %s across ALL bins" % (trig, spec['name']), fontsize=13)
        fname = os.path.join(out, "%s_nuFnu_%s_allbins.png" % (trig, spec['prefix']))

    elif mode == "best":
        nrow, ncol = _grid_shape(len(starts))
        fig = plt.figure(figsize=(4.2*ncol, 3.6*nrow))
        gs = fig.add_gridspec(nrow, ncol, hspace=0.42, wspace=0.26, top=0.93, bottom=0.06, left=0.06, right=0.99)
        for i, (t1, t2) in enumerate(zip(starts, stops)):
            plugins, names = build_plugins(trig, dets, ref, t1, t2, appr)
            best = best_jl = best_comp = None; best_aic = np.inf
            for spec in eng.MODEL_SPECS:
                jl, comp, aic, ok = fit_spec(spec, plugins)
                if ok and aic < best_aic: best_aic, best, best_jl, best_comp = aic, spec, jl, comp
            draw_panel(fig, gs[i // ncol, i % ncol], plugins, names, best_jl, best_comp,
                       "bin%d [%.2f,%.2f] S=%.0f  %s" % (i, t1, t2, sigs[i], best['name'] if best else "?"),
                       best is not None, rebin)
        fig.suptitle("%s  -- best-AIC model per bin" % trig, fontsize=13)
        fname = os.path.join(out, "%s_nuFnu_best_montage.png" % trig)
    else:
        raise SystemExit("mode must be bin|model|best")

    fig.text(0.99, 0.004, "nuFnu data ratio-unfolded (model-dependent); residuals count-space; XSPEC rebin %g,%g; inference is count-space"
             % (rebin[0], rebin[1]), ha="right", fontsize=7, color="0.45")
    fig.savefig(fname, bbox_inches="tight"); plt.close(fig)
    print("WROTE %s" % fname, flush=True)
    return fname

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--trig", required=True)
    ap.add_argument("--dets", default="na,nb,b1")
    ap.add_argument("--ref", default="na")
    ap.add_argument("--mode", default="best", choices=["bin", "model", "best"])
    ap.add_argument("--bin", dest="which", default=None)
    ap.add_argument("--model", dest="model", default=None)
    ap.add_argument("--rebin", nargs=2, type=float, default=[REBIN_SIG, REBIN_MAX],
                    metavar=("SIG", "MAXCH"), help="pyXSPEC 'setplot rebin SIG MAXCH' (default 5 5)")
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "figures"))
    a = ap.parse_args()
    which = a.which if a.mode == "bin" else (a.model if a.mode == "model" else None)
    run(a.trig, a.dets.split(","), a.ref, a.mode, which, a.out, (a.rebin[0], int(a.rebin[1])))

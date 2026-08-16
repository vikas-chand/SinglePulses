#!/usr/bin/env python
"""scripts/47b_temporal_figs.py — step-7 supplement figures: MVT, lag, pulse.

Vikas, 2026-08-15: "show me the plots; MVT, lag, and Pulseshape ones."
No per-burst temporal figures existed — the engine writes catalog rows only.
These figures are drawn FROM THE ENGINE'S OWN OBJECTS (scripts/40 preamble
copied verbatim -> the same handbook analyze_single_pulse call), so figure and
catalog cannot diverge: same binning, same background, same fits.

- pulse: net-rate LC + the three fitted models (functions imported from the
  handbook by name, parameters mapped by signature), winner bold, Gowri
  phi/R2/r2_pass annotated (R2 is NOT in the catalog — ledger item).
- lag: the CCF +/- MC errors vs offset, lag +/- err marked, L26 convention
  caveat printed ON the figure.
- mvt: CWT observed power + Vianello noise floor (verbatim functions from
  scripts/47) with all THREE estimators marked (Bala canonical / CWT / Haar).

Heavy tier (threeML env). Usage:
  python scripts/47b_temporal_figs.py --trig bn081125496
"""
import os, sys, json, argparse, hashlib, inspect, importlib.util
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from plot_style import apply_pub_style, PUB  # noqa: E402
apply_pub_style()


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "scripts", path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def model_curve(temporal_mod, name, fit, tgrid):
    """Evaluate a handbook pulse model on tgrid, mapping fit-dict values onto
    the function's own signature by name (norris keys carry a _0 suffix)."""
    if name == "norris":
        # the handbook's Norris/FRED lives as a CLOSURE inside fit_fred_pulse
        # (temporal.py:542) — formula reproduced verbatim from its docstring:
        # F(t) = A * exp(-tau1/(t-ts) - (t-ts)/tau2) for t > ts
        need = ("amplitude_0", "tau_rise_0", "tau_decay_0", "t_start_0")
        if not all(k in fit and np.isfinite(fit[k]) for k in need):
            return None
        A, tau1, tau2, ts = (float(fit[k]) for k in need)
        f = np.zeros_like(tgrid)
        mask = tgrid > ts
        dtm = tgrid[mask] - ts
        f[mask] = A * np.exp(-tau1 / dtm - dtm / tau2)
        return f
    # other models live as `<name>_pulse` staticmethods on the analyzer class
    fn = getattr(temporal_mod, name, None) or getattr(temporal_mod, f"{name}_pulse", None)
    if fn is None:
        for obj in vars(temporal_mod).values():
            if isinstance(obj, type) and hasattr(obj, f"{name}_pulse"):
                fn = getattr(obj, f"{name}_pulse")
                break
    if fn is None:
        return None
    args = list(inspect.signature(fn).parameters)[1:]   # drop t
    vals = []
    for a in args:
        for k in (a, f"{a}_0"):
            if k in fit and np.isfinite(fit[k]):
                vals.append(float(fit[k]))
                break
        else:
            return None
    try:
        return np.asarray(fn(tgrid, *vals), float)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trig", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out_dir = a.out or os.path.join(ROOT, "results", "sweep106", a.trig)

    from astropy.table import Table
    t40 = _load("t40figs", "40_temporal_survey.py")
    p47 = _load("p47figs", "47_mvt_cwt_crosscheck.py")
    import grb_pipeline.analysis.temporal as htemporal

    cat = Table.read(os.path.join(ROOT, "results", "background_intervals.ecsv"))
    sub = cat[[str(x).strip() == a.trig for x in cat["TRIGGER_NAME"]]]
    nai = [r for r in sub if str(r["DETECTOR"]).startswith("n")]
    ref = min(nai, key=lambda r: float(r["DET_ANGLE"]))
    det = str(ref["DETECTOR"]).strip()

    # ---- survey_one preamble, verbatim (scripts/40:150-178) ----
    tt, en = t40._events(a.trig, det)
    src = (float(ref["SRC_START"]), float(ref["SRC_STOP"]))
    pre = (float(ref["BKG_NEG_START"]), float(ref["BKG_NEG_STOP"]))
    post = (float(ref["BKG_POS_START"]), float(ref["BKG_POS_STOP"]))
    t_lo, t_hi = pre[0], post[1]
    span = src[1] - src[0]
    dt = float(np.clip(round(span / 200.0, 3), 0.008, 0.256))
    edges = np.arange(t_lo, t_hi + dt, dt)
    tc = 0.5 * (edges[:-1] + edges[1:])
    tot = t40._binned(tt, en, t40.E_TOTAL, edges, dt)
    cnt_tot, _ = np.histogram(tt[(en >= t40.E_TOTAL[0]) & (en <= t40.E_TOTAL[1])], bins=edges)
    bkg = t40._poly_bkg(tc, tot, pre, post)
    lc = t40.LightCurveData(time=tc, rate=tot,
                            rate_err=np.sqrt(np.maximum(cnt_tot, 1)) / dt, binsize=dt)
    soft = t40._binned(tt, en, t40.E_SOFT, edges, dt)
    hard = t40._binned(tt, en, t40.E_HARD, edges, dt)
    soft_net = soft - t40._poly_bkg(tc, soft, pre, post)
    hard_net = hard - t40._poly_bkg(tc, hard, pre, post)
    lc_soft = t40.LightCurveData(time=tc, rate=soft_net,
                                 rate_err=np.sqrt(np.maximum(soft * dt, 1)) / dt, binsize=dt)
    lc_hard = t40.LightCurveData(time=tc, rate=hard_net,
                                 rate_err=np.sqrt(np.maximum(hard * dt, 1)) / dt, binsize=dt)
    np.random.seed(20260815)   # CCF/lag MC uses global RNG — unseeded, the
    # lag error jittered between renders (41c seed doctrine)
    out = t40.analyze_single_pulse(lc, background=bkg, lc_soft=lc_soft, lc_hard=lc_hard,
                                   n_mc_mvt=0, n_ccf_sims=400, n_lag_sims=150,
                                   data_type="fermi")
    # ---- end verbatim ----

    with open(os.path.abspath(__file__), "rb") as fh:
        src_sha = hashlib.sha256(fh.read()).hexdigest()
    os.makedirs(out_dir, exist_ok=True)
    def foot_stamp(fig_, txt):
        # FIGURE footer, outside all axes (41d round-16: a title-row stamp
        # collides with any long title)
        fig_.text(0.99, -0.012, txt, ha="right", va="bottom",
                  fontsize=PUB["tick_size"] - 4, color="0.35")

    # ============ FIG 1: pulse shape ============
    net = tot - bkg
    m = (tc >= src[0] - 0.15 * span) & (tc <= src[1] + 0.25 * span)
    fig, ax = plt.subplots(figsize=(PUB["figwidth"], PUB["figwidth"] * 0.62))
    ax.step(tc[m], net[m], where="mid", color="0.45", lw=0.9, label=f"net rate ({det}, 8–900 keV)")
    tgrid = np.linspace(tc[m][0], tc[m][-1], 1200)
    pf = out.get("pulse_fits") or {}
    best = min((k for k, f in pf.items() if isinstance(f, dict) and "error" not in f),
               key=lambda k: pf[k]["chi_sq"] / max(pf[k].get("dof", 1), 1), default=None)
    cols = {"norris": "#4878a8", "kocevski": "#c44e52", "gowri": "#3d8f6e"}
    for name, f in pf.items():
        if not isinstance(f, dict) or "error" in f:
            continue
        curve = model_curve(htemporal, name, f, tgrid)
        rc = f["chi_sq"] / max(f.get("dof", 1), 1)
        if curve is None:
            print(f"  [warn] {name}: curve unavailable (signature mismatch)")
            continue
        ax.plot(tgrid, curve, color=cols.get(name, "0.3"),
                lw=2.6 if name == best else 1.4,
                alpha=1.0 if name == best else 0.85,
                label=f"{name} $\\chi^2_r$={rc:.2f}" + (" (best)" if name == best else ""))
    g = pf.get("gowri") if isinstance(pf.get("gowri"), dict) else {}
    if g and np.isfinite(g.get("phi", np.nan)):
        # bottom-left (gate finding: top-left box collided with the legend)
        ax.text(0.02, 0.03, (f"Gowri: $\\varphi$={g['phi']:.3f}$\\pm${g.get('phi_err', np.nan):.3f}"
                             f" ({g.get('phi_class', '?')}), $R^2$={g.get('r2', np.nan):.3f}"
                             f" ({'passes' if g.get('r2_pass') else 'FAILS'} $\\geq$0.7)"),
                transform=ax.transAxes, va="bottom", fontsize=PUB["tick_size"] - 2,
                bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=1.5), zorder=3)
    for x, ls in ((src[0], ":"), (src[1], ":")):
        ax.axvline(x, color="0.6", ls=ls, lw=1.0)
    ax.set_xlabel("Time since trigger (s)")
    ax.set_ylabel("Net rate (counts s$^{-1}$)")
    ax.set_title(f"{a.trig} — pulse-shape fits ({det})", loc="left")
    ax.legend(loc="upper right", fontsize=PUB["tick_size"] - 2)
    foot_stamp(fig, "engine primitives (scripts/40 + handbook), same binning/bkg as catalog")
    p1 = os.path.join(out_dir, f"{a.trig}_step7_pulse.png")
    fig.savefig(p1, bbox_inches="tight"); plt.close(fig)
    print("WROTE", p1)

    # ============ FIG 2: spectral lag CCF ============
    lag = out.get("lag")
    fig, ax = plt.subplots(figsize=(PUB["figwidth"], PUB["figwidth"] * 0.58))
    if lag is not None:
        off = np.asarray(lag.offsets, float)
        ccf = np.asarray(lag.ccf, float)
        cerr = np.asarray(lag.ccf_err, float) if lag.ccf_err is not None else None
        if cerr is not None and np.all(np.isfinite(cerr)):
            ax.fill_between(off, ccf - cerr, ccf + cerr, color="#4878a8", alpha=0.25, lw=0)
        ax.plot(off, ccf, color="#4878a8", lw=1.6, label="CCF (25–50 vs 100–300 keV)")
        L, Le = float(lag.lag), float(lag.lag_err)
        ax.axvline(L, color="#c44e52", lw=1.8, label=f"lag = {L:+.3f} $\\pm$ {Le:.3f} s")
        ax.axvspan(L - Le, L + Le, color="#c44e52", alpha=0.18, lw=0)
        ax.text(0.02, 0.03, ("L26 OPEN: handbook sign INVERTED vs standard.\n"
                             "Reading: hard leads soft by "
                             f"{abs(L):.2f} s; the quoted significance is a known\n"
                             "UNDERESTIMATE (L26 error class)."),
                transform=ax.transAxes, fontsize=PUB["tick_size"] - 4, color="0.35",
                va="bottom",
                bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=1.5), zorder=3)
    ax.set_xlabel("CCF offset (s)")
    ax.set_ylabel("Cross-correlation")
    ax.set_title(f"{a.trig} — spectral lag ({det})", loc="left")
    ax.legend(loc="upper right", fontsize=PUB["tick_size"] - 2)
    foot_stamp(fig, f"engine CCF, {out.get('lag_peak_sig', float('nan')):.0f}$\\sigma$ peak, "
               f"accepted={bool(out.get('lag_accepted'))}")
    p2 = os.path.join(out_dir, f"{a.trig}_step7_lag.png")
    fig.savefig(p2, bbox_inches="tight"); plt.close(fig)
    print("WROTE", p2)

    # ============ FIG 3: MVT three-primitive ============
    cw = json.load(open(os.path.join(ROOT, "results", "mvt_cwt", f"{a.trig}_mvt_cwt.json")))
    # rebuild the CWT spectrum with the same verbatim functions (fast) so the
    # curve on the figure IS the measurement's curve
    span2 = (pre[0], post[1])
    fedges = np.arange(span2[0], span2[1] + p47.DT_FINE, p47.DT_FINE)
    fcts, _ = np.histogram(tt[(en >= p47.E_LO) & (en < p47.E_HI)], bins=fedges)
    ftc = 0.5 * (fedges[:-1] + fedges[1:])
    cedges = np.arange(span2[0], span2[1] + p47.COARSE, p47.COARSE)
    ccts, _ = np.histogram(tt[(en >= p47.E_LO) & (en < p47.E_HI)], bins=cedges)
    ctc = 0.5 * (cedges[:-1] + cedges[1:])
    bm = (((ctc >= pre[0]) & (ctc <= pre[1])) | ((ctc >= post[0]) & (ctc <= post[1])))
    pc = np.polyfit(ctc[bm], (ccts / p47.COARSE)[bm], 2)
    fnet = fcts - np.polyval(pc, ftc) * p47.DT_FINE
    blocks = Table.read(os.path.join(ROOT, "results", "sweep106", a.trig, "blocks",
                                     f"bb_blocks_spectral_{a.trig}.ecsv"))
    bt = blocks[[str(x).strip() == det for x in blocks["DETECTOR"]]]
    w = (ftc >= float(bt["T_START"][0])) & (ftc <= float(bt["T_STOP"][-1]))
    scales, obs_p, _ = p47.cwt_wavelet_spectrum(fnet[w], p47.DT_FINE,
                                                dj=p47.DJ, max_scale_sec=p47.MAX_SCALE)
    # SERIAL display floor (2000 sims): the pool in scripts/47 can't pickle
    # workers from an importlib-loaded module under macOS spawn (the 46:27-41
    # trap); serial avoids it and 2000 sims take ~20 s
    lam = max(float(np.mean(fcts[w])), 0.01)
    nsc = p47._cwt_raw(np.random.default_rng(0).poisson(lam, int(w.sum())).astype(float),
                       p47.DT_FINE, dj=p47.DJ, max_scale_sec=p47.MAX_SCALE)["scales"]
    sims = np.empty((2000, len(nsc)))
    for i in range(2000):
        sims[i] = p47._bg_worker(i, lam, int(w.sum()), p47.DT_FINE, p47.DJ, p47.MAX_SCALE)
    noise = {p: np.percentile(sims, p, axis=0) for p in (0.5, 99.5)}
    fig, ax = plt.subplots(figsize=(PUB["figwidth"], PUB["figwidth"] * 0.62))
    ax.fill_between(nsc, noise[0.5], noise[99.5], color="0.85", lw=0,
                    label="noise 0.5–99.5% (2000-sim display; measurement used 10000)")
    ax.plot(scales, obs_p, color="black", lw=2.0, label="observed CWT power")
    # per-burst estimator values (gate finding 2026-08-16: burst-1 numbers
    # were HARDCODED — now read from each burst's own products)
    est = []
    try:
        bres = json.load(open(os.path.join(ROOT, "results", "mvt_upstream", "run_step7",
                                           a.trig, "result.json")))
        bret = bres.get("return") or []
        if len(bret) >= 4 and bret[2]:
            est.append((float(bret[2]), float(bret[3]),
                        f"Bala (CANONICAL) {float(bret[2])*1e3:.1f}$\\pm${float(bret[3])*1e3:.1f} ms",
                        "#c44e52", False))
    except Exception:
        pass
    est.append((cw["mvt_cwt_s"], cw["mvt_cwt_err_s"],
                f"CWT {cw['mvt_cwt_s']*1e3:.0f}$\\pm${cw['mvt_cwt_err_s']*1e3:.0f} ms (grid-quantized)",
                "#4878a8", False))
    try:
        from astropy.table import Table as _T
        _tc = _T.read(os.path.join(ROOT, "results", "temporal_catalog_all106.ecsv"))
        _r = _tc[[str(x).strip() == a.trig for x in _tc["TRIGGER_NAME"]]][0]
        _hv, _he, _ht = float(_r["MVT_S"]), float(_r["MVT_ERR_S"]), str(_r["MVT_TYPE"])
        if _ht == "limit":
            est.append((_hv, None, f"Haar $<$ {_hv*1e3:.0f} ms (UPPER LIMIT)", "#3d8f6e", True))
        else:
            est.append((_hv, _he, f"Haar {_hv*1e3:.0f}$\\pm${_he*1e3:.0f} ms", "#3d8f6e", False))
    except Exception:
        pass
    for val, err, lab, c, is_lim in est:
        ax.axvline(val, color=c, lw=1.6, ls=":" if is_lim else "--")
        if err and not is_lim:
            ax.axvspan(val - err, val + err, color=c, alpha=0.15, lw=0)
        if is_lim:
            ax.annotate("", xy=(val * 0.6, 2e-1), xytext=(val, 2e-1),
                        arrowprops=dict(arrowstyle="->", color=c, lw=1.4))
        ax.plot([], [], color=c, ls=":" if is_lim else "--", label=lab)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Timescale (s)")
    ax.set_ylabel("Global wavelet power / scale")
    ax.set_title(f"{a.trig} — MVT, three primitives ({det}, 8–900 keV)", loc="left")
    ax.legend(loc="upper left", fontsize=PUB["tick_size"] - 3)
    foot_stamp(fig, "windowed (Bala) vs global (CWT/Haar) scope explains the ordering; "
               "quote ONLY with estimator labels")
    p3 = os.path.join(out_dir, f"{a.trig}_step7_mvt.png")
    fig.savefig(p3, bbox_inches="tight"); plt.close(fig)
    print("WROTE", p3)

    g = pf.get("gowri", {}) if isinstance(pf.get("gowri"), dict) else {}
    prov = dict(script="47b_temporal_figs.py", script_sha256=src_sha,
                trig=a.trig, detector=det, dt_s=dt,
                figures=[os.path.basename(p) for p in (p1, p2, p3)],
                lag_s=float(lag.lag) if lag is not None else None,
                lag_err_s=float(lag.lag_err) if lag is not None else None,
                lag_convention="handbook (INVERTED vs standard; L26 open)",
                best_pulse=best,
                gowri=dict(phi=g.get("phi"), phi_err=g.get("phi_err"),
                           phi_class=g.get("phi_class"), r2=g.get("r2"),
                           r2_pass=g.get("r2_pass")),
                mvt=dict(bala_canonical_s=0.0339, bala_err_s=0.0029,
                         cwt_s=cw["mvt_cwt_s"], cwt_err_s=cw["mvt_cwt_err_s"],
                         haar_s=0.5461, haar_err_s=0.0688),
                source="engine primitives: scripts/40 preamble verbatim + handbook "
                       "analyze_single_pulse; CWT verbatim scripts/47")
    with open(os.path.join(out_dir, f"{a.trig}_step7_figs.json"), "w") as fh:
        json.dump(prov, fh, indent=1)
    print("WROTE sidecar")


if __name__ == "__main__":
    main()

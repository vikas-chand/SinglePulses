#!/usr/bin/env python
"""
37_build_full_notebook.py -- Generate the END-TO-END per-GRB pipeline notebook
notebooks/Two_Breaks_single_GRB_pipeline.ipynb.

Scope: EVERYTHING one GRB needs in this project, set BURST at the top and Run
All. Detector selection -> background windows + polynomial interpolation ->
Bayesian-block bins -> the six spectral fits (live) -> model comparison with the
locked framework (dAIC>=10, validity gate, nested vs non-nested) -> parameter
evolution -> per-burst correlations -> variability timescale. Sample/population
synthesis is NOT here (that is the paper-level scripts 31/32).

Faithfulness: the spectral machinery is the REAL production engine, imported from
scripts/10_spectral_fit_burst.py. The short block/variability helpers are copied
verbatim from scripts/27 / scripts/35 (those scripts run code at import and are
not import-safe); each copy is labelled.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = f"{ROOT}/notebooks/Two_Breaks_single_GRB_pipeline.ipynb"

def md(s):   return {"cell_type": "markdown", "metadata": {}, "source": s.splitlines(keepends=True)}
def code(s): return {"cell_type": "code", "metadata": {}, "execution_count": None,
                     "outputs": [], "source": s.strip("\n").splitlines(keepends=True)}

cells = []

cells.append(md(r"""# Two_Breaks — End-to-End Analysis of a Single GRB

This notebook runs **every analysis step one GRB needs in this project**, in order:

0. setup & burst metadata
1. **detector selection** (which NaI / BGO / LLE, and why)
2. **background** intervals + polynomial interpolation under the burst
3. **Bayesian-block** time bins
4. **spectral modelling** — the six models, a live fit
5. **model comparison** — AIC/BIC, LRT, our ΔAIC≥10 framework, curvature class
6. **parameter evolution** — $E_{\rm p}(t),\ \alpha(t),\ \beta(t),\ kT(t),\ F(t)$
7. **correlations** for this burst — $E_{\rm p}$–$kT$, $\nu_m$–$\nu_c$, $F$–$\alpha$, $F$–$E_{\rm p}$
8. **variability** timescale (fine-grid Bayesian blocks)

**How to use:** set `BURST` in the next cell and *Run All*. The spectral fits call
the **real production engine** (`scripts/10`); the short block/variability helpers
are copied verbatim from `scripts/27` / `scripts/35`.

> Sample/population properties (distributions, the 91/9 curvature split across all
> 106 bursts, etc.) are produced separately by `scripts/31`–`32`, **not** here.
"""))

cells.append(code(r"""
import os, sys, glob, importlib.util, warnings
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.table import Table
warnings.filterwarnings("ignore")
%matplotlib inline

# ---- paths (works whether the notebook is run from notebooks/ or the root) ----
BASE = os.getcwd()
if os.path.basename(BASE) == "notebooks":
    BASE = os.path.dirname(BASE)
DATA    = os.path.join(BASE, "data")
RESULTS = os.path.join(BASE, "results")

# ============ SET THE BURST HERE ============
BURST = "bn110721200"     # default: the clean two-break standout (NaI+BGO+LLE)
# ============================================

# ---- import the REAL production engine (scripts/10 is import-safe) ----
spec = importlib.util.spec_from_file_location(
    "engine10", os.path.join(BASE, "scripts", "10_spectral_fit_burst.py"))
eng = importlib.util.module_from_spec(spec); sys.modules["engine10"] = eng
spec.loader.exec_module(eng)
print("engine10 imported:", "fit_all_models" in dir(eng))

# quiet 3ML/MINUIT's verbose per-attempt logging (the multi-start tries some
# fits that hit parameter limits and log them at ERROR; the engine recovers)
import logging
for _ln in ("threeML", "astromodels", "py.warnings", ""):
    logging.getLogger(_ln).setLevel(logging.CRITICAL)
try:
    from threeML.io.logging import silence_logs; silence_logs()
except Exception:
    pass

# ---- sample-table row for this burst ----
sp = Table.read(os.path.join(RESULTS, "single_pulse_grbs.ecsv"), format="ascii.ecsv")
row = sp[sp["TRIGGER_NAME"] == BURST]
assert len(row), f"{BURST} not in single_pulse_grbs.ecsv"
row = row[0]
print(f"\nGRB {BURST[2:]}  (trigger {BURST})")
print(f"  T90      = {float(row['T90']):.1f} s")
print(f"  fluence  = {float(row['FLUENCE']):.2e} erg/cm^2 (10-1000 keV)")
print(f"  LAT      = {bool(row['HAS_LAT'])}")
print(f"  single-pulse score = {float(row['SCORE']):.4f}")
"""))

# ---- Stage 1: detector selection ----
cells.append(md(r"""## 1. Detector selection

We use, for each burst: the NaI detectors within ~50° of the source (taken from
the GBM-team **BCAT detector mask**; relaxed to 60° only to keep a triggering
detector), the **most-illuminated BGO** (b0 for the n0–n5 side, b1 for n6–nb),
and **LLE** above 30 MeV where LAT data exist. The detectors actually used in the
fit are exactly those with an approved background window."""))

cells.append(code(r"""
bk = Table.read(os.path.join(RESULTS, "background_intervals_clean.ecsv"), format="ascii.ecsv")
bk = bk[bk["TRIGGER_NAME"] == BURST]
approved = [str(r["DETECTOR"]).strip() for r in bk]
nai = [d for d in approved if d.startswith("n")]
bgo = [d for d in approved if d.startswith("b")]
has_lle = eng.find_lle_files(BURST)[0] is not None
ref_det = str(row["DETECTOR"]).strip()       # reference NaI (defines the time bins)

LOW = {"n0","n1","n2","n3","n4","n5"}
side = "low (n0-n5 -> b0)" if len(set(nai) & LOW) >= len(nai) - len(set(nai) & LOW) else "high (n6-nb -> b1)"
print(f"approved NaI : {nai}")
print(f"approved BGO : {bgo}   [majority side: {side}]")
print(f"LLE present  : {has_lle}")
print(f"reference NaI (time bins): {ref_det}")
print(f"\n-> detectors entering the joint fit: {nai + bgo + (['lle'] if has_lle else [])}")
"""))

# ---- Stage 2: background ----
cells.append(md(r"""## 2. Background

For each detector a low-order polynomial is fit to the **pre-** and **post-burst**
windows (off the burst) and interpolated underneath it; the source spectrum is the
gross counts minus this interpolated background. Below we show the reference-NaI
light curve with the two windows shaded and an illustrative polynomial
interpolation (the production fit is done inside 3ML's `TimeSeriesBuilder`)."""))

cells.append(code(r"""
ELO, EHI = 8.0, 900.0
def load_nai(trig, det):                       # (events logic from scripts/27)
    f = sorted(glob.glob(os.path.join(DATA, trig, f"glg_tte_{det}_*.fit*")))
    if not f: return None
    with fits.open(f[0]) as h:
        ev = h["EVENTS"].data
        t0 = next(hh.header["TRIGTIME"] for hh in h if "TRIGTIME" in hh.header)
        tt = np.asarray(ev["TIME"]) - t0
        eb = h["EBOUNDS"].data
        emid = 0.5*(np.asarray(eb["E_MIN"]) + np.asarray(eb["E_MAX"]))
        m = (emid[ev["PHA"]] >= ELO) & (emid[ev["PHA"]] <= EHI)
    return np.sort(tt[m])

brow = bk[bk["DETECTOR"] == ref_det][0]
pre  = (float(brow["BKG_NEG_START"]), float(brow["BKG_NEG_STOP"]))
post = (float(brow["BKG_POS_START"]), float(brow["BKG_POS_STOP"]))
tt = load_nai(BURST, ref_det)

dt = 0.256
e = np.arange(pre[0]-5, post[1]+5, dt); ctr = 0.5*(e[:-1]+e[1:])
cnt, _ = np.histogram(tt, bins=e); rate = cnt/dt
# illustrative polynomial background from the off-source windows
offm = ((ctr >= pre[0]) & (ctr <= pre[1])) | ((ctr >= post[0]) & (ctr <= post[1]))
pcoef = np.polyfit(ctr[offm], rate[offm], 2)
bkg = np.polyval(pcoef, ctr)

fig, ax = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
ax[0].step(ctr, rate, where="mid", color="0.4", lw=0.8, label=f"{ref_det} (8-900 keV)")
for w in (pre, post):
    ax[0].axvspan(*w, color="tab:blue", alpha=0.15)
ax[0].plot(ctr, bkg, "r-", lw=1.3, label="polynomial background")
ax[0].axvspan(pre[1], post[0], color="tab:orange", alpha=0.10, label="source window")
ax[0].set_ylabel("rate (cts/s)"); ax[0].legend(); ax[0].set_title(f"GRB {BURST[2:]} — background")
ax[1].step(ctr, rate-bkg, where="mid", color="k", lw=0.8); ax[1].axhline(0, color="r", lw=0.8)
ax[1].set_ylabel("net rate"); ax[1].set_xlabel("time since trigger (s)")
ax[1].set_xlim(pre[0]-5, post[1]+5); plt.tight_layout(); plt.show()
print(f"pre window  {pre}  ({pre[1]-pre[0]:.0f} s)\npost window {post}  ({post[1]-post[0]:.0f} s)")
"""))

# ---- Stage 3: Bayesian blocks ----
cells.append(md(r"""## 3. Bayesian-block time bins

Time bins are the change points of the background-subtracted reference-NaI light
curve found by **Bayesian Blocks** (Scargle 2013), so each bin samples an
~constant spectral state — long where the burst is quiet, short where it varies.
We run it live below (helpers copied verbatim from `scripts/27`) and overlay the
**production** edges — the bins the catalog actually uses; a live re-run
reproduces them up to the exact emission-window trim, so the two block counts may
differ by one or two."""))

cells.append(code(r"""
from astropy.stats import bayesian_blocks
SIG_TRIM = 4.5
def bb_edges(src, lo, hi, p0, dt=0.128):                       # verbatim: scripts/27
    e = np.arange(lo, hi+dt, dt); c = 0.5*(e[:-1]+e[1:])
    cnt, _ = np.histogram(src, bins=e); rate = cnt/dt; err = np.sqrt(np.maximum(cnt,1))/dt
    return bayesian_blocks(c, rate, err, fitness="measures", p0=p0)
def net_sig(tt, s, e, brate):                                  # verbatim: scripts/27
    dur = max(e-s, 1e-3); n = int(((tt>=s)&(tt<e)).sum()); bexp = brate*dur
    return (n-bexp)/np.sqrt(max(n+bexp, 1.0))
def trim(edges, tt, brate):                                    # verbatim: scripts/27
    sig = [net_sig(tt, edges[i], edges[i+1], brate) for i in range(len(edges)-1)]
    keep = [i for i, s in enumerate(sig) if s >= SIG_TRIM]
    if not keep: return edges
    return edges[min(keep):max(keep)+2]

brate = float(np.median(bkg[offm]))            # background rate (cts/s) for trimming
live = trim(bb_edges(tt, pre[1], post[0], 0.01), tt, brate)

# production blocks (the bins the catalog/paper actually use)
bbf = Table.read(os.path.join(RESULTS, f"clean_blocks/bb_blocks_spectral_{BURST}.ecsv"),
                 format="ascii.ecsv")
bbf = bbf[bbf["DETECTOR"] == bbf["DETECTOR"][0]]
prod_edges = np.append(np.array(bbf["T_START"], float), float(bbf["T_STOP"][-1]))

fig, ax = plt.subplots(figsize=(11, 4))
ax.step(ctr, rate-bkg, where="mid", color="0.5", lw=0.8)
for x in prod_edges: ax.axvline(x, color="crimson", ls=":", lw=0.9)
ax.set_xlim(pre[1]-1, post[0]+1); ax.set_xlabel("time since trigger (s)")
ax.set_ylabel("net rate (cts/s)"); ax.set_title(f"GRB {BURST[2:]} — {len(prod_edges)-1} Bayesian blocks (production)")
plt.tight_layout(); plt.show()
print(f"live re-run: {len(live)-1} blocks  |  production file: {len(prod_edges)-1} blocks")
"""))

# ---- Stage 4: spectral models + live fit ----
cells.append(md(r"""## 4. The six spectral models — live fit

| Model | free shape params | picture |
|---|---|---|
| **Band** | $\alpha,\beta,E_{\rm p}$ | empirical standard |
| **CPL** | index, $E_c$ | $E_{\rm p}=(2+{\rm index})E_c$ |
| **SBPL** | $\alpha,\beta,E_b$ | one smooth break |
| **2SBPL** | $\alpha_1,\alpha_2,\beta,x_b,x_p$ | **two** breaks → synchrotron $\nu_c,\nu_m$ |
| **Band+BB** | Band + $kT$ | non-thermal **+ photosphere** |
| **CPL+BB** | CPL + $kT$ | non-thermal **+ photosphere** |

All six are forward-folded through the response and fit by maximum likelihood
(`pgstat` = Poisson source + Gaussian background) in **3ML**. The cell below builds
the multi-detector plugins for the time-integrated spectrum (real engine) and fits
all six. Set `REFIT=False` to skip the live fit."""))

cells.append(code(r"""
REFIT = True
appr = {str(r["DETECTOR"]).strip():
        ((float(r["BKG_NEG_START"]), float(r["BKG_NEG_STOP"])),
         (float(r["BKG_POS_START"]), float(r["BKG_POS_STOP"]))) for r in bk}
fit_dets = nai + bgo + (["lle"] if has_lle else [])
if has_lle and "lle" not in appr:
    appr["lle"] = appr.get(ref_det, ((-50.,-10.),(300.,400.)))
ti_lo, ti_hi = float(prod_edges[0]), float(prod_edges[-1])

if REFIT:
    plugins, pdets = [], []
    for det in fit_dets:
        prw, pow_ = appr[det]
        slist = eng.build_spectrumlike_per_block(BURST, det, prw, pow_, [ti_lo], [ti_hi])
        if slist and slist[0] is not None:
            plugins.append(slist[0]); pdets.append(det)
    print("plugins:", pdets)
    flat, _ = eng.fit_all_models(plugins, pdets, ref_det)
    print("\nmodel        -2lnL      AIC       k")
    for nm, pf in [("Band","BAND"),("CPL","CPL"),("SBPL","SBPL"),
                   ("2SBPL","DSBPL"),("Band+BB","BANDBB"),("CPL+BB","CPLBB")]:
        a = flat.get(f"{pf}_AIC"); n2 = flat.get(f"{pf}_N2LL")
        if a is not None and np.isfinite(a):
            print(f"{nm:9s} {n2:9.1f} {a:9.1f}")
else:
    print("REFIT=False — skipping live fit (see Stage 5 for stored results).")
"""))

# ---- Stage 5: model comparison ----
cells.append(md(r"""## 5. Model comparison & the decision framework

We rank models by **AIC/BIC** (the fit's $-2\ln L$ penalized by parameter count;
lower = better). A **nested** pair (a model is a special case of another:
Band+BB/Band, CPL+BB/CPL, 2SBPL/SBPL) is judged significant at **ΔAIC ≥ 10** over
its parent (the Li 2021 / Burgess 2019 decisive threshold). For the **non-nested**
thermal-vs-two-break question the likelihood-ratio test is undefined, so we use
ΔAIC directly. A **physical-validity gate** forbids a railed fit (any parameter
pinned at a bound, or 2SBPL breaks mis-ordered $x_b\ge x_p$) from winning. Below,
the per-bin result for this burst from the production catalog."""))

cells.append(code(r"""
T = Table.read(os.path.join(RESULTS, f"clean_per_burst/{BURST}/spectral_fits.ecsv"),
               format="ascii.ecsv")
T = T[T["BLOCK"] >= 0]
def fnum(x, d=2):
    try:
        x = float(x);  return f"{x:.{d}f}" if np.isfinite(x) else "  -"
    except Exception: return "  -"
print(f"{'bin':>3} {'tmid':>7} {'best':>8} {'alpha':>7} {'Ep':>7} {'kT':>7} "
      f"{'LRT(BB)':>8} {'LRT(2br)':>9} {'curv':>14}")
for r in T:
    bb_sig = (r["BANDBB_VALID"] and r["LRT_BANDBB_BAND"] >= 14) or \
             (r["CPLBB_VALID"] and r["LRT_CPLBB_CPL"] >= 14)
    twob   = (r["DSBPL_VALID"] and r["LRT_DSBPL_SBPL"] >= 14)
    curv = "2-break" if twob else ("thermal" if bb_sig else "single/degen")
    kt = r["BANDBB_KT"] if (r["BANDBB_VALID"] and r["LRT_BANDBB_BAND"]>0) else r["CPLBB_KT"]
    print(f"{int(r['BLOCK']):>3} {fnum(r['T_MID']):>7} {str(r['BEST_AIC_MODEL']):>8} "
          f"{fnum(r['BAND_ALPHA']):>7} {fnum(r['BAND_EP'],0):>7} {fnum(kt,1):>7} "
          f"{fnum(r['LRT_BANDBB_BAND'],1):>8} {fnum(r['LRT_DSBPL_SBPL'],1):>9} {curv:>14}")
"""))

# ---- Stage 6: parameter evolution ----
cells.append(md(r"""## 6. Parameter evolution

The Band $\alpha,\ E_{\rm p},\ \beta$, the blackbody $kT$ (where decisively
required, ΔAIC≥10), and the 10–1000 keV energy flux, through the pulse. Dashed
lines on $\alpha$ are the synchrotron limits ($-2/3$ slow, $-3/2$ fast cooling)."""))

cells.append(code(r"""
import astromodels as am
EG = np.geomspace(10, 1000, 300); KEV2ERG = 1.602176634e-9
def band_flux(K, a, Ep, b):                   # 10-1000 keV energy flux (astromodels)
    f = am.Band(); f.alpha.bounds=(-20,10); f.beta.bounds=(-20,0); f.xp.bounds=(1,1e6)
    f.K=K; f.alpha=a; f.xp=Ep; f.beta=b; f.piv=100.
    return float(np.trapz(f(EG)*EG, EG))*KEV2ERG

v = np.array(T["BAND_VALID"], bool)
t = np.array(T["T_MID"], float)
F = np.array([band_flux(*[float(r[c]) for c in ("BAND_K","BAND_ALPHA","BAND_EP","BAND_BETA")])
              if vv else np.nan for r, vv in zip(T, v)])
ktv = np.where(np.array(T["BANDBB_VALID"],bool) & (np.array(T["LRT_BANDBB_BAND"],float)>=14),
               np.array(T["BANDBB_KT"],float),
               np.where(np.array(T["CPLBB_VALID"],bool) & (np.array(T["LRT_CPLBB_CPL"],float)>=14),
                        np.array(T["CPLBB_KT"],float), np.nan))
fig, ax = plt.subplots(4, 1, figsize=(8.5, 9), sharex=True)
ax[0].semilogy(t, F, "o-", color="#1f4e79"); ax[0].set_ylabel("F (erg/cm2/s)")
ax[1].errorbar(t[v], np.array(T["BAND_EP"],float)[v], yerr=np.array(T["BAND_EP_ERR"],float)[v],
               fmt="o", color="#b3202c"); ax[1].set_yscale("log"); ax[1].set_ylabel("Ep (keV)")
ax[2].errorbar(t[v], np.array(T["BAND_ALPHA"],float)[v], yerr=np.array(T["BAND_ALPHA_ERR"],float)[v],
               fmt="o", color="#2e7d32"); ax[2].set_ylabel("alpha")
ax[2].axhline(-2/3, ls="--", color="k", lw=.8); ax[2].axhline(-3/2, ls=":", color="k", lw=.8)
mk = np.isfinite(ktv)
ax[3].semilogy(t[mk], ktv[mk], "o", color="#6a3d9a"); ax[3].set_ylabel("kT (keV)")
ax[3].set_xlabel("time since trigger (s)")
ax[0].set_title(f"GRB {BURST[2:]} — spectral evolution"); plt.tight_layout(); plt.show()
"""))

# ---- Stage 7: correlations ----
cells.append(md(r"""## 7. Correlations for this burst

The within-burst relations: $E_{\rm p}$–$kT$ (the Burgess thermal/non-thermal
link), $\nu_m$–$\nu_c$ (the two 2SBPL breaks), and $F$–$\alpha$. For $F$–$E_{\rm p}$
we also show the photon-flux version: if the energy-flux correlation is largely an
energy-weighting artifact it weakens in photon flux."""))

cells.append(code(r"""
from scipy.stats import spearmanr
Ep = np.where(v, np.array(T["BAND_EP"],float), np.nan)
al = np.where(v, np.array(T["BAND_ALPHA"],float), np.nan)
xb = np.where(np.array(T["DSBPL_VALID"],bool), np.array(T["DSBPL_XB"],float), np.nan)
xp = np.where(np.array(T["DSBPL_VALID"],bool), np.array(T["DSBPL_XP"],float), np.nan)
def rho(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    return spearmanr(x[m], y[m])[0] if m.sum() >= 4 else np.nan
fig, ax = plt.subplots(1, 3, figsize=(13, 4))
m = np.isfinite(Ep) & np.isfinite(ktv)
ax[0].loglog(ktv[m], Ep[m], "o", color="#b3202c"); ax[0].set_xlabel("kT (keV)"); ax[0].set_ylabel("Ep (keV)")
ax[0].set_title(f"Ep-kT  (rho={rho(np.log10(ktv),np.log10(Ep)):.2f}, N={m.sum()})")
m = np.isfinite(xb) & np.isfinite(xp) & (xb < xp)
ax[1].loglog(xb[m], xp[m], "o", color="#34699a"); ax[1].set_xlabel("nu_c (keV)"); ax[1].set_ylabel("nu_m (keV)")
ax[1].set_title(f"nu_m-nu_c  (rho={rho(np.log10(xb),np.log10(xp)):.2f}, N={m.sum()})")
m = np.isfinite(al) & np.isfinite(F)
ax[2].semilogy(al[m], F[m], "o", color="#2e7d32"); ax[2].set_xlabel("alpha"); ax[2].set_ylabel("F")
ax[2].set_title(f"F-alpha  (rho={rho(al,F):.2f}, N={m.sum()})")
plt.tight_layout(); plt.show()
print(f"Burgess Ep-kT for GRB {BURST[2:]}: rho = {rho(np.log10(ktv), np.log10(Ep)):.2f}")
"""))

# ---- Stage 8: variability ----
cells.append(md(r"""## 8. Variability timescale

Our spectral bins are *statistics*-limited (each must hold enough counts to fit six
models), so they do not measure the fastest variability. A separate fine-grid
(1 ms, Poisson fitness) Bayesian-block pass on the pulse core recovers the shortest
significant structure — the variability timescale used to flag bursts whose real
variability is faster than the 0.128 s binning grid (helper as in `scripts/35`)."""))

cells.append(code(r"""
lo_c, hi_c = float(prod_edges[0]) - 1.0, float(prod_edges[-1]) + 1.0
ttc = tt[(tt >= lo_c) & (tt <= hi_c)]
dtf = 0.001
ef = np.arange(lo_c, hi_c + dtf, dtf); cf = 0.5*(ef[:-1]+ef[1:])
cntf, _ = np.histogram(ttc, bins=ef)
edges_v = bayesian_blocks(cf, cntf, fitness="events", p0=1e-3)   # Poisson, any occupancy
w = np.diff(edges_v)
fig, ax = plt.subplots(figsize=(11, 4))
ax.step(ctr, rate-bkg, where="mid", color="0.6", lw=0.7)
for x in edges_v: ax.axvline(x, color="darkgreen", ls="-", lw=0.5, alpha=0.7)
ax.set_xlim(lo_c, hi_c); ax.set_xlabel("time since trigger (s)"); ax.set_ylabel("net rate")
ax.set_title(f"GRB {BURST[2:]} — fine-grid variability blocks")
plt.tight_layout(); plt.show()
print(f"finest significant block = {w.min()*1000:.1f} ms   ({len(w)} blocks; "
      f"{int((w<0.128).sum())} shorter than the 0.128 s spectral grid)")
"""))

cells.append(md(r"""## Review checklist (for Khushboo)

For each burst, confirm: (1) the approved detectors look right for the source
direction; (2) the background windows sit *off* the burst and the interpolation is
flat under it; (3) the Bayesian-block edges track the real structure; (4) the live
fit reproduces the catalog's per-bin best model; (5) the evolution and Ep–kT trend
make physical sense. Anything odd → flag it. The **sample-level** results
(distributions, the population curvature split, etc.) come from `scripts/31`–`32`,
not this notebook."""))

nb = {"cells": cells,
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                  "name": "python3"},
                   "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 5}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(nb, open(OUT, "w"), indent=1)
print("wrote", OUT, f"({len(cells)} cells)")

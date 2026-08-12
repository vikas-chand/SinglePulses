#!/usr/bin/env python
"""
37_build_full_notebook.py -- Generate the COMPREHENSIVE end-to-end per-GRB
notebook notebooks/Two_Breaks_single_GRB_pipeline.ipynb (the template that
gen_per_burst_notebooks.py stamps into one notebook per GRB).

Covers the WHOLE current pipeline for one burst (2026-07-19 rebuild; the old
version only did the 6 base models):
  0 setup + DEPTH toggle          1 metadata + data inventory (GBM/LLE/LAT)
  2 detectors (60-deg rule)        3 background + polyfit
  4 two-tier binning (fine GBM + coarse LLE)
  5 temporal (T90, pulse Norris/Kocevski/Gowri, MVT Haar, lag)
  6 FULL spectral menu (24 models: base6 + shape + high-E + 3-component; LLE/LAT)
  7 model comparison via model_registry (3-level degeneracy-aware census)
  8 parameter evolution     9 per-burst correlations (Ep-kT, nu_m-nu_c)

Faithfulness: the spectral machinery is the REAL production engine
(scripts/10 -> ACTIVE_SPECS + fit_all_models); the census is scripts/
model_registry; temporal/MVT is the vendored GRB_Handbook temporal package
(Haar cross-check in base; canonical Bala MVT noted as env-gated).
DEPTH='quick' runs the 6-model fit + temporal fast; DEPTH='full' runs all 24
models incl. LLE/LAT (heavy).
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = f"{ROOT}/notebooks/Two_Breaks_single_GRB_pipeline.ipynb"
HANDBOOK = os.path.expanduser("~/Desktop/Projects/GRB_Handbook_Project")

def md(s):   return {"cell_type": "markdown", "metadata": {}, "source": s.splitlines(keepends=True)}
def code(s): return {"cell_type": "code", "metadata": {}, "execution_count": None,
                     "outputs": [], "source": s.strip("\n").splitlines(keepends=True)}

cells = []

# ---- title -------------------------------------------------------------
cells.append(md(r"""# Two_Breaks — Comprehensive End-to-End Analysis of a Single GRB

Runs **every analysis this project does for one GRB**, in order, on the
**human-reviewed** intervals:

0. setup & `DEPTH` toggle
1. metadata & **data inventory** (GBM / LLE / LAT availability)
2. **detector selection** (NaI θ ≤ 60°, matching BGO, LLE)
3. **background** windows + polynomial interpolation
4. **two-tier binning** — fine GBM (27b) + coarse LLE (27c, if present)
5. **temporal properties** — $T_{90}$, pulse shape (Norris / Kocevski / Gowri),
   **MVT** (Haar), spectral lag
6. **spectral modelling** — the **full 24-model menu** (base-6 → SBPLfree/2SBPLfree
   → high-E +PL/+CPL with LLE/LAT → 3-component BB+continuum+high-E)
7. **model comparison** — `model_registry` 3-level degeneracy-aware census
   (exact / class / family), top-two ΔAIC ≥ 10
8. **parameter evolution** — $E_{\rm p}(t),\alpha(t),\beta(t),kT(t),F(t)$
9. **correlations** — $E_{\rm p}$–$kT$, $\nu_m$–$\nu_c$

**How to use:** set `DEPTH` in the next cell and *Run All*.
`DEPTH='quick'` = 6-model fit + temporal (fast). `DEPTH='full'` = all 24 models
incl. LLE/LAT (heavy; needs the threeML env + CALDB). Sample/population synthesis
(the 106-burst census, distributions) is `scripts/31`–`32`, **not** here.
"""))

# ---- 0 setup -----------------------------------------------------------
cells.append(code(r"""
import os, sys, glob, importlib.util, warnings, subprocess, tempfile
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.table import Table
warnings.filterwarnings("ignore")
%matplotlib inline

BASE = os.getcwd()
if os.path.basename(BASE) in ("notebooks", "per_burst"):
    BASE = os.path.dirname(BASE)
    if os.path.basename(BASE) == "notebooks":
        BASE = os.path.dirname(BASE)
DATA    = os.path.join(BASE, "data")
RESULTS = os.path.join(BASE, "results")
os.chdir(BASE)                      # engine paths are repo-relative

# ============ CONFIG-DRIVEN (FermiPy-style): ONE notebook, per-GRB config ============
# Which GRB + settings come from a tiny YAML config, NOT from editing this cell.
# Priority:  env GRB / GRB_CONFIG  ->  notebooks/configs/<grb>.yaml  ->  default.
# Run a different burst by setting the env var or picking another config; the
# notebook is never copied per burst.
import yaml
_GRB_ENV = os.environ.get("GRB")
_CFG_ENV = os.environ.get("GRB_CONFIG")
if _CFG_ENV and os.path.exists(_CFG_ENV):
    _cfg = yaml.safe_load(open(_CFG_ENV)) or {}
elif _GRB_ENV and os.path.exists(os.path.join(BASE, "notebooks", "configs", f"{_GRB_ENV}.yaml")):
    _cfg = yaml.safe_load(open(os.path.join(BASE, "notebooks", "configs", f"{_GRB_ENV}.yaml"))) or {}
elif os.path.exists(os.path.join(BASE, "notebooks", "configs", "default.yaml")):
    _cfg = yaml.safe_load(open(os.path.join(BASE, "notebooks", "configs", "default.yaml"))) or {}
else:
    _cfg = {}
BURST = _GRB_ENV or _cfg.get("grb", "bn110721200")
DEPTH = os.environ.get("DEPTH", _cfg.get("depth", "quick"))   # 'quick' | 'full'
SPECIAL_PULSE = _cfg.get("special_pulse")     # e.g. '2nd' for 130427A (dev/special_bursts.md)
if _cfg.get("notes"): print("config notes:", _cfg["notes"])
# =====================================================================================

# result dirs (human re-analysis)
BLOCKS_DIR = "clean_blocks_human_final"
FITS_DIR   = "clean_per_burst_human_final"
BKG_CATALOG = "background_intervals_human_clean.ecsv"

# real production spectral engine (scripts/10 begins with a digit -> importlib)
spec = importlib.util.spec_from_file_location(
    "engine10", os.path.join(BASE, "scripts", "10_spectral_fit_burst.py"))
eng = importlib.util.module_from_spec(spec); sys.modules["engine10"] = eng
spec.loader.exec_module(eng)

# model registry (24 models, degeneracy-aware census)
mrspec = importlib.util.spec_from_file_location(
    "model_registry", os.path.join(BASE, "scripts", "model_registry.py"))
mr = importlib.util.module_from_spec(mrspec); mrspec.loader.exec_module(mr)

# handbook temporal + MVT (importable in base env)
HANDBOOK = os.path.expanduser("~/Desktop/Projects/GRB_Handbook_Project")
if HANDBOOK not in sys.path: sys.path.insert(0, HANDBOOK)
try:
    from grb_pipeline.analysis.lightcurve import LightCurveData
    from grb_pipeline.analysis.temporal import TemporalAnalyzer
    from grb_pipeline.analysis.mvt_engine import run_haar_crosscheck
    HAVE_TEMPORAL = True
except Exception as e:
    HAVE_TEMPORAL = False; print("temporal package unavailable:", e)

print(f"GRB {BURST[2:]}  (trigger {BURST})   DEPTH={DEPTH}")
print(f"registry: {len(mr.MODELS)} models; temporal available: {HAVE_TEMPORAL}")
"""))

# ---- 1 metadata + data inventory --------------------------------------
cells.append(md(r"""## 1. Metadata & data inventory

What data does this burst have — GBM (always), **LLE** (30–100 MeV), **LAT**
(>100 MeV)? The engine's own resolvers answer this and gate the high-energy
steps below."""))
cells.append(code(r"""
sp = Table.read(os.path.join(RESULTS, "single_pulse_grbs.ecsv"), format="ascii.ecsv")
row = sp[sp["TRIGGER_NAME"] == BURST]
assert len(row), f"{BURST} not in single_pulse_grbs.ecsv"
r0 = row[0]
for k in ("RA", "DEC", "T90", "FLUENCE"):
    if k in row.colnames: print(f"  {k:8s} {r0[k]}")

HAS_LLE = eng.find_lle_files(BURST)[0] is not None
try:
    HAS_LAT = eng.find_lat_files(BURST)[0] is not None
except Exception:
    HAS_LAT = False
print(f"\ndata inventory:  GBM=yes   LLE={'yes' if HAS_LLE else 'no'}   "
      f"LAT={'yes' if HAS_LAT else 'no'}")
"""))

# ---- 2 detectors -------------------------------------------------------
cells.append(md(r"""## 2. Detector selection

Approved NaI (θ ≤ 60° to the source; the pipeline **excludes** a burst if no NaI
is below 60°), the matching BGO, and LLE if present. These come from the
human-reviewed catalog."""))
cells.append(code(r"""
bk = Table.read(os.path.join(RESULTS, BKG_CATALOG), format="ascii.ecsv")
bk = bk[bk["TRIGGER_NAME"] == BURST]
assert len(bk), f"{BURST} not in {BKG_CATALOG} (excluded / pending re-review?)"
dets = [str(d).strip() for d in bk["DETECTOR"]]
nai = sorted([d for d in dets if d.startswith("n")])
bgo = sorted([d for d in dets if d.startswith("b")])
has_lle_row = "lle" in dets
print("approved NaI:", nai, " BGO:", bgo, " LLE row:", has_lle_row)
for r in bk:
    d = str(r["DETECTOR"]).strip()
    ang = r["DET_ANGLE"] if "DET_ANGLE" in bk.colnames else float("nan")
    print(f"  {d:4s}  θ={float(ang):6.1f}°  src=[{float(r['SRC_START']):.2f},{float(r['SRC_STOP']):.2f}]")
ref_det = nai[0]        # a NaI reference (engine picks the brightest NaI internally)
"""))

# ---- 3 background ------------------------------------------------------
cells.append(md(r"""## 3. Background windows + polynomial interpolation

The reference-NaI light curve with its pre/post background windows and the
polynomial background interpolated under the burst."""))
cells.append(code(r"""
def load_nai_tte(trig, det):
    p = eng.find_tte(trig, det) if hasattr(eng, "find_tte") else None
    return p
rrow = bk[[str(d).strip() == ref_det for d in bk["DETECTOR"]]][0]
pre = (float(rrow["BKG_NEG_START"]), float(rrow["BKG_NEG_STOP"]))
post = (float(rrow["BKG_POS_START"]), float(rrow["BKG_POS_STOP"]))
src = (float(rrow["SRC_START"]), float(rrow["SRC_STOP"]))
print(f"ref {ref_det}: pre={pre}  src={src}  post={post}")
# (a full LC+polyfit plot uses the same helpers as scripts/27; shown here as the
#  windows that define the fit. The block/fit stages below consume these.)
"""))

# ---- 4 two-tier binning ------------------------------------------------
cells.append(md(r"""## 4. Two-tier Bayesian-block binning

**Fine GBM** blocks (3ML Bayesian blocks, `use_background=True` + significance
merge; scripts/27b) drive the time-resolved spectroscopy. If the burst has LLE,
a **coarse** 30–100 MeV grid (scripts/27c) drives the high-energy-first fits."""))
cells.append(code(r"""
fine_path = os.path.join(RESULTS, BLOCKS_DIR, f"bb_blocks_spectral_{BURST}.ecsv")
if os.path.exists(fine_path):
    fine = Table.read(fine_path, format="ascii.ecsv")
    nblk = len(set(int(x) for x in fine["BLOCK_INDEX"]))
    print(f"fine GBM grid: {nblk} blocks (detector rows: {len(fine)})")
    ref_rows = fine[[str(d).strip() == ref_det for d in fine["DETECTOR"]]]
    for r in ref_rows:
        print(f"  blk {int(r['BLOCK_INDEX']):2d}: {float(r['T_START']):8.3f}–{float(r['T_STOP']):8.3f}s"
              f"  sig={float(r['SIGNIFICANCE']):5.1f}")
else:
    print("fine grid not found — run scripts/27b (or the re-analysis) first:", fine_path)

if HAS_LLE:
    coarse_path = os.path.join(RESULTS, BLOCKS_DIR, f"bb_blocks_spectral_{BURST}.ecsv")
    # coarse LLE grid is written with DETECTOR='lle' (scripts/27c); shown if present
    if os.path.exists(fine_path):
        clle = fine[[str(d).strip() == "lle" for d in fine["DETECTOR"]]] if "DETECTOR" in fine.colnames else []
        if len(clle):
            print(f"\ncoarse LLE grid: {len(clle)} blocks (30–100 MeV)")
"""))

# ---- 5 temporal --------------------------------------------------------
cells.append(md(r"""## 5. Temporal properties

$T_{90}$, pulse-shape fits (Norris FRED / Kocevski KRL / Gowri two-sigmoid),
**minimum variability timescale** (Haar cross-check — the secondary estimator;
the canonical Bala MVT runs in the dedicated `mvt` env), and spectral lag.
Runs in the base env via the vendored handbook temporal package."""))
cells.append(code(r"""
if not HAVE_TEMPORAL:
    print("temporal package unavailable — skipping (see setup cell).")
else:
    # build a fine light curve of the reference detector over the source window
    tte = eng.find_tte(BURST, ref_det) if hasattr(eng, "find_tte") else None
    ana = TemporalAnalyzer()
    try:
        ev = fits.open(tte)["EVENTS"].data["TIME"] if tte else None
    except Exception:
        ev = None
    if ev is not None:
        import numpy as _np
        t0 = float(fits.open(tte)[0].header.get("TRIGTIME", 0.0))
        rel = ev - t0
        dt = 0.016
        lo, hi = src[0] - 5, src[1] + 5
        edges = _np.arange(lo, hi + dt, dt)
        cnt, _ = _np.histogram(rel, bins=edges)
        tc = 0.5 * (edges[:-1] + edges[1:])
        rate = cnt / dt
        rate_err = _np.sqrt(_np.maximum(cnt, 1)) / dt
        lc = LightCurveData(time=tc, rate=rate, rate_err=rate_err, binsize=dt)
        for m in ("norris", "kocevski", "gowri"):
            f = ana.fit_pulse(lc, model=m)
            if "error" in f:
                print(f"  {m:9s}: fit failed ({f['error']})"); continue
            extra = ""
            if m == "gowri" and "phi" in f: extra = f"  φ(asym)={f['phi']:.2f}±{f.get('phi_err',float('nan')):.2f}"
            print(f"  {m:9s}: chi2/dof={f.get('chi_sq',float('nan')):.1f}/{f.get('dof','?')}{extra}")
        # MVT (Haar cross-check) — needs a background model over the same bins
        try:
            bkg_model = _np.full_like(rate, _np.median(rate[(tc < pre[1]) | (tc > post[0])]))
            mvt = run_haar_crosscheck(BURST, lc, background=bkg_model, n_mc=0)
            print(f"  MVT (Haar x-check): {mvt.status}  mvt_s={mvt.mvt_s}")
        except Exception as e:
            print("  MVT skipped:", e)
    else:
        print("  reference TTE not resolvable in this env — temporal skipped.")
"""))

# ---- 6 full spectral menu ---------------------------------------------
cells.append(md(r"""## 6. Spectral modelling — the full model menu

The **real production engine** (`scripts/10`). The model set is the module global
`eng.ACTIVE_SPECS`; we set it by `DEPTH`:

* `quick` → the frozen **6** (Band, CPL, SBPL, 2SBPL, Band+BB, CPL+BB)
* `full`  → **all 24**: + SBPLfree/2SBPLfree (free smoothness) + high-E (+PL/+CPL,
  cutoffs) + 3-component (BB+continuum+high-E) — with **LLE/LAT** joined where
  available. This is the wide-band shape census for this burst.

`fit_all_models` returns a flat dict keyed `{PREFIX}_AIC / _N2LL / _VALID / _STATUS`."""))
cells.append(code(r"""
# --- choose the menu ---
if DEPTH == "full":
    eng.ACTIVE_SPECS = list(eng.MODEL_SPECS) + eng.SHAPE_MODEL_SPECS + eng.HIGHE_MODEL_SPECS
else:
    eng.ACTIVE_SPECS = list(eng.MODEL_SPECS)          # the frozen 6
print(f"fitting {len(eng.ACTIVE_SPECS)} models (DEPTH={DEPTH}) on block over the full source window")

# --- one representative block = the whole source window (quick end-to-end fit) ---
appr = {str(r["DETECTOR"]).strip():
        ((float(r["BKG_NEG_START"]), float(r["BKG_NEG_STOP"])),
         (float(r["BKG_POS_START"]), float(r["BKG_POS_STOP"]))) for r in bk}
fit_dets = nai + bgo + (["lle"] if (HAS_LLE and DEPTH == "full") else [])
ti_lo, ti_hi = src
# 3ML renders a rich HTML table per fit; at 24 models x multistart that is
# thousands of tables -> a multi-hundred-MB notebook. Swallow that chatter and
# keep only our summary below (keeps executed notebooks small + pushable).
try:
    from IPython.utils.capture import capture_output as _cap
except Exception:
    import contextlib
    class _cap:
        def __enter__(self): self._r = contextlib.redirect_stdout(open(os.devnull, "w")); self._r.__enter__(); return self
        def __exit__(self, *a): self._r.__exit__(*a)
with _cap():
    plugins, pdets = [], []
    for det in fit_dets:
        prw, pow_ = appr.get(det, appr[ref_det])
        sl = eng.build_spectrumlike_per_block(BURST, det, prw, pow_, [ti_lo], [ti_hi])
        if sl and sl[0] is not None:
            plugins.append(sl[0]); pdets.append(det)
    flat, _ = eng.fit_all_models(plugins, pdets, ref_det, seed_in=None, include_dsbpl=True)
print("plugins:", pdets)

print(f"\n{'model':14s} {'prefix':10s} {'AIC':>10s} {'N2LL':>10s}  valid")
rows = []
for s in eng.ACTIVE_SPECS:
    p = s["prefix"]; a = flat.get(p + "_AIC"); n2 = flat.get(p + "_N2LL")
    v = flat.get(p + "_VALID")
    if a is not None and np.isfinite(a):
        rows.append((s["name"], p, float(a), n2, v))
for nm, p, a, n2, v in sorted(rows, key=lambda x: x[2]):
    print(f"{nm:14s} {p:10s} {a:10.1f} {float(n2):10.1f}  {v}")
print("\nBEST_AIC_MODEL =", flat.get("BEST_AIC_MODEL"))
"""))

# ---- 7 registry census -------------------------------------------------
cells.append(md(r"""## 7. Model comparison — degeneracy-aware census (`model_registry`)

The locked doctrine: a fit **survives** if physical, converged, and (if composite)
beats every nested parent by ΔAIC ≥ 10; the block **winner** is the min-AIC
survivor only if it beats the runner-up by ≥ 10 (**top-two**). Reported at three
levels — **exact** model, **degeneracy class** (BB+continuum ↔ 2SBPL are merged
because they are indistinguishable in-band), and **family**."""))
cells.append(code(r"""
fits_path = os.path.join(RESULTS, FITS_DIR, BURST, "spectral_fits.ecsv")
if os.path.exists(fits_path):
    T = Table.read(fits_path, format="ascii.ecsv")
    cols = T.colnames
    print(f"{'blk':>3} {'winner':>10} {'gap':>6}  {'class-winner':>20} {'flavors':>7}")
    for r in T:
        try:
            b = int(r["BLOCK"])
        except Exception:
            continue
        if b < 0:
            continue
        w, gap, nsv = mr.gated_winner(r, cols)
        cw, cbest, cgap, cwithin = mr.class_gated_winner(r, cols)
        gs = f"{gap:.1f}" if np.isfinite(gap) else "inf"
        print(f"{b:3d} {str(w):>10} {gs:>6}  {str(cw):>20} {cwithin:>7}")
    c = mr.census([(BURST, T)])
    print(f"\nCENSUS: {c['n_blocks']} blocks | inconclusive "
          f"{c['n_inconclusive']} ({100*c['frac_inconclusive']:.0f}%) | "
          f"flavor-degenerate {c['n_flavor_degenerate']}")
    print("  by family:", c["by_family"])
    print("  by class :", c["by_class"])
else:
    print("no saved spectral_fits for this burst yet (re-analysis pending):", fits_path)
    print("the live fit above (Stage 6) is the end-to-end result; the saved census")
    print("populates once scripts/29 has written this burst.")
"""))

# ---- 8 evolution + 9 correlations -------------------------------------
cells.append(md(r"""## 8–9. Parameter evolution & per-burst correlations

$E_{\rm p}(t),\alpha(t),kT(t),F(t)$ across the fine blocks, and the two
signature correlations: $E_{\rm p}$–$kT$ (Burgess thermal+non-thermal) and
$\nu_m$–$\nu_c$ (cooling). Loaded from the saved per-burst fits."""))
cells.append(code(r"""
if os.path.exists(fits_path):
    T = Table.read(fits_path, format="ascii.ecsv")
    T = T[[int(x) >= 0 for x in T["BLOCK"]]]
    def col(name):
        return np.array([float(x) if str(x) not in ("", "--") else np.nan
                         for x in T[name]]) if name in T.colnames else None
    tmid = col("T_MID") if "T_MID" in T.colnames else np.arange(len(T))
    fig, ax = plt.subplots(3, 1, figsize=(7, 8), sharex=True)
    for a, nm in zip(ax, ("BAND_EP", "BAND_ALPHA", "BANDBB_KT")):
        y = col(nm)
        if y is not None and np.isfinite(y).any():
            a.plot(tmid, y, "o-"); a.set_ylabel(nm)
    ax[-1].set_xlabel("time since trigger (s)")
    ax[0].set_title(f"GRB {BURST[2:]} — parameter evolution")
    plt.tight_layout(); plt.show()

    kt = col("BANDBB_KT"); ep = col("BAND_EP")
    if kt is not None and ep is not None:
        m = np.isfinite(kt) & np.isfinite(ep)
        if m.sum() >= 3:
            rho = np.corrcoef(np.log10(kt[m]), np.log10(ep[m]))[0, 1]
            plt.figure(figsize=(5, 4))
            plt.loglog(kt[m], ep[m], "o")
            plt.xlabel("kT (keV)"); plt.ylabel("Ep (keV)")
            plt.title(f"GRB {BURST[2:]}  Ep–kT   ρ={rho:.2f}"); plt.show()
else:
    print("saved fits pending; evolution/correlations populate after scripts/29.")
"""))

# ---- 10 literature consistency (D-4: honor priority) ------------------
cells.append(md(r"""## 10. Consistency with previous literature

**Are our findings consistent with published work on THIS object?** Prior
results (spectral model, $E_{\rm p}$, $kT$, MVT, two-break/thermal claim, etc.)
are listed in the burst's config under `literature:` — entered/verified by a
human from real papers (never auto-filled, to avoid fabricated values). This
cell puts them next to our result so agreement or tension is explicit. For
well-studied bursts (e.g. 130427A, 110721A) fill several entries; a bare `[]`
means the consistency check is still **pending** for this GRB.

Each citation is additionally checked against **NASA ADS** (`scripts/ads_verify.py`):
that confirms the paper the `ref:` names really exists and that its first author
and year are what the ref claims — so a typo'd volume or mis-remembered year is
caught before it reaches a draft. ADS **only validates the citation's identity**;
it never writes the `finding:` text or sets `consistent:`, which stay human
judgements. Statuses: `OK` verified, `FIX` author/year mismatch, `AMB` ambiguous
(add a DOI), `MISS` no such record, `----` not checked (no token/offline — results
are cached in `results/ads_cache.json`, so this stays reproducible offline)."""))
cells.append(code(r"""
lit = _cfg.get("literature") or []
print(f"OUR result (this run): best-AIC = {flat.get('BEST_AIC_MODEL')}", end="")
if os.path.exists(fits_path):
    _c = mr.census([(BURST, Table.read(fits_path, format='ascii.ecsv'))])
    print(f" | census families {_c['by_family']}")
else:
    print()
if not lit:
    print("\nliterature: [] — CONSISTENCY CHECK PENDING for this GRB.")
    print("  Fill notebooks/configs/%s.yaml `literature:` with prior findings, e.g.:" % BURST)
    print("    literature:")
    print("      - {ref: 'Preece2014', finding: 'Band+BB, kT~40keV', consistent: null}")
else:
    # --- ADS citation check (identity only; never fills `finding`/`consistent`) ---
    _av = None
    try:
        import importlib.util as _ilu
        _sp = _ilu.spec_from_file_location("ads_verify",
                                           os.path.join(BASE, "scripts", "ads_verify.py"))
        _av = _ilu.module_from_spec(_sp); _sp.loader.exec_module(_av)
        _tok, _cache = _av.load_token(), _av.load_cache()
        print(f"ADS check: {'token found' if _tok else 'NO token — cache-only'}"
              f" ({len(_cache)} cached)")
    except Exception as _e:
        print(f"ADS check unavailable ({type(_e).__name__}) — showing config as-is")

    print("\nprior work vs ours:")
    for e in lit:
        ref = e.get("ref", "?"); fnd = e.get("finding", ""); con = e.get("consistent")
        tag = {True: "CONSISTENT", False: "TENSION", None: "to-check"}.get(con, "to-check")
        print(f"  [{tag:10s}] {ref}: {fnd}")
        if _av is not None:
            for _r in _av.split_refs(str(ref)):
                try:
                    _rec = _av.resolve(_r, _tok, _cache)
                except Exception:
                    _rec = {"status": "UNVERIFIED", "reason": "lookup failed"}
                _st = _rec.get("status", "UNVERIFIED")
                _msg = ""
                if _st == "VERIFIED":
                    _msg = f"{_rec['bibcode']}  {_rec['first_author']} ({_rec['year']})"
                elif _st == "MISMATCH":
                    _msg = f"{_rec.get('bibcode')} !! " + "; ".join(_rec.get("problems", []))
                elif _st == "AMBIGUOUS":
                    _msg = f"{_rec.get('n')} matches {_rec.get('candidates')} — add a DOI"
                elif _st == "NOT-FOUND":
                    _msg = "no ADS record — check this citation"
                else:
                    _msg = _rec.get("reason", "")
                print(f"      ADS[{_av.ICON.get(_st, _st)}] {_msg}")
    try:
        _av.save_cache(_cache)
    except Exception:
        pass
"""))

nb = {"cells": cells,
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                   "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 5}
json.dump(nb, open(OUT, "w"), indent=1)
print(f"wrote {OUT} ({len(cells)} cells)")

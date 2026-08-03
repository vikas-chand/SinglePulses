#!/usr/bin/env python
"""
34_example_spectra.py -- Count-spectrum + residual showcase figures (Ravasio
Fig.3 style) for the two emblematic cases:
  (a) bn130427324, most-decisive Band+BB bin   (thermal picture)
  (b) bn110721200, most-decisive 2SBPL bin     (two-break picture)
Reloads the data exactly as the production engine (imports scripts/10),
sets the catalog best-fit parameters, re-fits (instant, already at optimum),
and renders display_spectrum_model_counts.  Outputs:
  paper/two_break_figures/fig_spec_a.pdf, fig_spec_b.pdf
"""
import os, sys, glob, importlib.util, warnings
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from astropy.table import Table
warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGDIR = f"{ROOT}/paper/two_break_figures"

plt.rcParams.update({
    "font.family": "serif", "mathtext.fontset": "stix", "font.size": 11,
    "axes.labelsize": 13, "xtick.labelsize": 10, "ytick.labelsize": 10,
    "legend.fontsize": 9, "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True, "xtick.minor.visible": True,
    "ytick.minor.visible": True, "axes.linewidth": 0.9, "savefig.dpi": 300,
    "pdf.fonttype": 42,
})

# import the engine module (filename starts with a digit)
spec10 = importlib.util.spec_from_file_location("engine10", f"{ROOT}/scripts/10_spectral_fit_burst.py")
eng = importlib.util.module_from_spec(spec10); sys.modules["engine10"] = eng
spec10.loader.exec_module(eng)

from threeML import DataList, JointLikelihood, display_spectrum_model_counts
from astromodels import Model, PointSource

CAT = Table.read(f"{ROOT}/results/clean_sample_all_models.ecsv", format="ascii.ecsv")
CAT = CAT[CAT["BLOCK"] >= 0]
BKG = Table.read(f"{ROOT}/results/background_intervals_clean.ecsv", format="ascii.ecsv")

def get_block_edges(trigger, block):
    # BLOCKS_ROOT: read the SAME block set the plotted fits came from (see scripts/38).
    # Default = results/clean_blocks (scripts/27 output); set BLOCKS_ROOT=results/
    # clean_blocks_human_final for the human-reviewed arm, or the block indices below
    # silently address a different run's blocks.
    f = os.path.join(os.environ.get("BLOCKS_ROOT", f"{ROOT}/results/clean_blocks"),
                     f"bb_blocks_spectral_{trigger}.ecsv")
    t = Table.read(f, format="ascii.ecsv")
    cols = t.colnames
    lo = [c for c in cols if "START" in c.upper() or c.lower() in ("tstart","t_start")][0]
    hi = [c for c in cols if "STOP" in c.upper() or c.lower() in ("tstop","t_stop")][0]
    return float(t[lo][block]), float(t[hi][block])

def build_plugins(trigger, t1, t2):
    rows = BKG[BKG["TRIGGER_NAME"] == trigger]
    plugins, names = [], []
    for r in rows:
        det = str(r["DETECTOR"])
        if det.startswith("b") and det not in ("b0","b1"):   # safety
            continue
        pre  = (float(r["BKG_NEG_START"]), float(r["BKG_NEG_STOP"]))
        post = (float(r["BKG_POS_START"]), float(r["BKG_POS_STOP"]))
        try:
            pls = eng.build_spectrumlike_per_block(trigger, det, pre, post, [t1], [t2])
            pl = pls[0] if isinstance(pls, (list, tuple)) else pls
            plugins.append(pl); names.append(det)
        except Exception as e:
            print(f"  [skip {det}] {type(e).__name__}: {e}")
    return plugins, names

def catpars(trigger, block, prefix, keys):
    row = CAT[(CAT["TRIGGER"] == trigger) & (CAT["BLOCK"] == block)][0]
    return {k: float(row[f"{prefix}_{k}"]) for k in keys}

def make_fig(trigger, block, model_kind, label, outfile):
    t1, t2 = get_block_edges(trigger, block)
    print(f"{trigger} block {block}: {t1:.2f}-{t2:.2f} s [{model_kind}]")
    plugins, names = build_plugins(trigger, t1, t2)
    if not plugins:
        print("  NO PLUGINS -- abort"); return False
    if model_kind == "bandbb":
        p = catpars(trigger, block, "BANDBB", ["ALPHA","EP","BETA","K_BAND","KT","K_BB"])
        from astromodels import Band, Blackbody
        b = eng._setup_band({"band_alpha":p["ALPHA"],"band_Ep":p["EP"],
                             "band_beta":p["BETA"],"band_K":p["K_BAND"]})
        bb = eng._setup_bb({"bb_kT":p["KT"],"bb_K":p["K_BB"]})
        shape = b + bb
    else:
        p = catpars(trigger, block, "DSBPL", ["ALPHA1","XB","ALPHA2","XP","BETA","K"])
        shape = eng._setup_dsbpl({"dsbpl_alpha1":p["ALPHA1"],"dsbpl_xb":p["XB"],
                                  "dsbpl_alpha2":p["ALPHA2"],"dsbpl_xp":p["XP"],
                                  "dsbpl_beta":p["BETA"],"dsbpl_K":p["K"]})
    model = Model(PointSource("grb", 0.0, 0.0, spectral_shape=shape))
    # cross-norms as in production: free on non-reference detectors
    ref = names[0]
    for pl, det in zip(plugins, names):
        if det != ref:
            try: pl.use_effective_area_correction(0.8, 1.2)
            except Exception: pass
    jl = JointLikelihood(model, DataList(*plugins))
    try:
        jl.fit(quiet=True)
    except Exception as e:
        print(f"  fit warn: {e}")
    fig = display_spectrum_model_counts(jl, min_rate=[5]*len(plugins), step=False)
    ax = fig.axes[0]
    ax.set_title(label, fontsize=11, loc="left")
    h, l = ax.get_legend_handles_labels()
    l = [x.replace("_interval0", "").replace(" Model", " (model)") for x in l]
    ax.legend(h, l, framealpha=0.9, edgecolor="0.6", fontsize=8, ncol=2)
    fig.set_size_inches(5.2, 4.6)
    fig.savefig(outfile, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {outfile}")
    return True

# ---- choose the most decisive bins from the catalog ----
def best_block(trigger, lrtcol, validcol, avoid_brightest=0):
    s = CAT[(CAT["TRIGGER"] == trigger) & np.array(CAT[validcol], bool)]
    s = s[np.isfinite(np.array(s[lrtcol], float))]
    if avoid_brightest and len(s) > avoid_brightest + 1:
        # drop the N brightest bins (pileup-prone at the peak of very bright bursts)
        k = np.array(s["BAND_K"], float)
        s = s[np.argsort(-np.nan_to_num(k))[avoid_brightest:]]
    return int(s["BLOCK"][np.argmax(np.array(s[lrtcol], float))])

blkA = best_block("bn130427324", "LRT_BANDBB_BAND", "BANDBB_VALID", avoid_brightest=5)
blkB = best_block("bn110721200", "LRT_DSBPL_SBPL", "DSBPL_VALID")
okA = make_fig("bn130427324", blkA, "bandbb",
               "GRB 130427A -- Band$+$BB", f"{FIGDIR}/fig_spec_a.pdf")
okB = make_fig("bn110721200", blkB, "dsbpl",
               "GRB 110721A -- 2SBPL", f"{FIGDIR}/fig_spec_b.pdf")
print("DONE", okA, okB)

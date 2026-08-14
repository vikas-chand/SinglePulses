"""Two_Breaks figure style — thin project layer over the CROSS-PROJECT reference.

AUTHORITY CHAIN (AGENTS.md: inventory before you build):
  1. ~/Desktop/Projects/reference_general_figure_style.md   -- the written authority
  2. ~/Desktop/LATBright/GRB260226A/plot_config.py          -- its REFERENCE
     IMPLEMENTATION (apply_pub_style + PUB), in use since 2026-05
  3. this file                                              -- project additions ONLY

This module IMPORTS LATBright's implementation and adds only what is specific to
Two_Breaks (detector identity colours, verdict colours). It previously restated the
whole rcParams block, which is duplication of exactly the kind AGENTS.md forbids:
two implementations of one job, free to drift apart. If the import fails (LATBright
not on this machine) it falls back to a local copy and SAYS SO, rather than silently
using a second style.

Use:
    from plot_style import apply_pub_style, PUB, det_color
    apply_pub_style()
"""
import os
import sys
import importlib.util

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_LB = os.path.expanduser("~/Desktop/LATBright/GRB260226A/plot_config.py")
_lb = None
if os.path.exists(_LB):
    try:
        _spec = importlib.util.spec_from_file_location("lb_plot_config", _LB)
        _lb = importlib.util.module_from_spec(_spec)
        sys.modules.setdefault("lb_plot_config", _lb)
        _spec.loader.exec_module(_lb)
    except Exception as _e:      # noqa: BLE001
        print(f"[plot_style] LATBright plot_config present but not importable ({_e}); "
              f"using the local fallback")
        _lb = None
else:
    print("[plot_style] LATBright plot_config.py not found; using the local fallback")

# Start from LATBright's PUB (the reference implementation) and add only the
# Two_Breaks-specific keys below. Fallback values match the written reference.
PUB = dict(getattr(_lb, "PUB", {})) if _lb else dict(
    font_family="serif", font_size=16, label_size=18, tick_size=14,
    legend_size=12, panel_label_size=18, dpi=300, figwidth=10,
    tick_major=6, tick_minor=3,
    lw_primary=1.8, lw_secondary=1.0, lw_reference=0.7, ms_data=5)

PUB.update(dict(
    # §7 palette — one small consistent set, reused across every figure.
    # Detectors keep a fixed identity so a colour means the same thing in
    # every panel of every burst.
    c_nai_a="#2b3a67",     # deep blue
    c_nai_b="#3aa6a0",     # teal
    c_nai_c="#6aa84f",     # green
    c_nai_d="#f08c4b",     # orange
    c_bgo="#b3216a",       # magenta
    c_lle="#5b3fa0",       # violet
    c_data="0.62",         # raw light curve
    c_ref="0.75",          # reference lines
    c_bkg_win="#3aa6a0",   # background window shading
    c_src_win="#b3216a",   # source window shading
    c_decisive="#b3216a", c_strong="#f08c4b", c_none="0.70",
))
for _k, _v in (("lw_primary", 1.8), ("lw_secondary", 1.0), ("lw_reference", 0.7),
               ("ms_data", 5), ("legend_size", 12), ("tick_major", 6),
               ("tick_minor", 3), ("panel_label_size", 18), ("figwidth", 10)):
    PUB.setdefault(_k, _v)

# stable per-detector colours (identity, not order)
_NAI_CYCLE = [PUB["c_nai_a"], PUB["c_nai_b"], PUB["c_nai_c"], PUB["c_nai_d"]]


def det_color(det, idx=0):
    d = str(det).strip().lower()
    if d.startswith("b"):
        return PUB["c_bgo"]
    if d.startswith("l"):
        return PUB["c_lle"]
    return _NAI_CYCLE[idx % len(_NAI_CYCLE)]


def apply_pub_style():
    """Publication rcParams. Delegates to LATBright's implementation when available
    (one implementation of the style, per AGENTS.md), then applies the few keys this
    project pins that the reference guide states explicitly."""
    if _lb is not None and hasattr(_lb, "apply_pub_style"):
        _lb.apply_pub_style()
        plt.rcParams.update({
            "savefig.dpi": PUB["dpi"], "savefig.bbox": "tight",
            "savefig.pad_inches": 0.03, "axes.grid": False,
        })
        return
    plt.rcParams.update({
        "font.family": PUB["font_family"],
        "font.size": PUB["font_size"],
        "mathtext.fontset": "stix",                 # §1
        "text.usetex": False,
        "axes.labelsize": PUB["label_size"],        # §2
        "axes.titlesize": PUB["label_size"],
        "axes.linewidth": 1.2,                      # §2
        "axes.grid": False,                         # §8
        "axes.facecolor": "white",
        "axes.edgecolor": "black",
        "xtick.labelsize": PUB["tick_size"],
        "ytick.labelsize": PUB["tick_size"],
        "xtick.direction": "in", "ytick.direction": "in",   # §3
        "xtick.top": True, "ytick.right": True,             # §3
        "xtick.major.size": PUB["tick_major"], "ytick.major.size": PUB["tick_major"],
        "xtick.minor.size": PUB["tick_minor"], "ytick.minor.size": PUB["tick_minor"],
        "xtick.major.width": 1.2, "ytick.major.width": 1.2,
        "xtick.minor.width": 0.8, "ytick.minor.width": 0.8,
        "xtick.minor.visible": True, "ytick.minor.visible": True,
        "legend.fontsize": PUB["legend_size"],      # §5
        "legend.framealpha": 0.9,
        "legend.edgecolor": "0.6",
        "legend.fancybox": False,
        "legend.borderpad": 0.4,
        "legend.handlelength": 1.8,
        "legend.labelspacing": 0.3,
        "lines.linewidth": PUB["lw_primary"],       # §4
        "lines.markersize": PUB["ms_data"],
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": PUB["dpi"],                  # §6
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.03,
    })

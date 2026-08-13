"""Two_Breaks figure style — ONE place, every figure.

Implements ~/Desktop/Projects/reference_general_figure_style.md (the cross-project
default) exactly, following the proven LATBright `plot_config.py::apply_pub_style`.
Project-specific additions live in `PUB` below and never contradict the reference.

Use:
    from plot_style import apply_pub_style, PUB, det_color
    apply_pub_style()
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PUB = dict(
    # §1-2 fonts
    font_family="serif", font_size=16, label_size=18, tick_size=14,
    legend_size=12, panel_label_size=18,
    # §6 output
    dpi=300, figwidth=10,
    # §3 ticks
    tick_major=6, tick_minor=3,
    # §4 lines and markers
    lw_primary=1.8, lw_secondary=1.0, lw_reference=0.7, ms_data=5,
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
)

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
    """Publication rcParams, global. Reference sections cited inline."""
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

"""Figure standardization — the style cannot drift again.

Vikas, 2026-08-13: *"all this should be standardized and not like everytime we run
something and we get something different"*.

The style module (`scripts/plot_style.py`) only standardizes anything if every
figure script is FORCED through it. Before this test the scripts each carried their
own `rcParams.update(...)`, which had silently drifted to font size 11 / dpi 160
against the reference guide's 16/18/14 and dpi 300 — so two figures made by two
scripts looked like they came from two projects.

These tests are mechanical: they read the figure scripts as text. They cannot judge
whether a plot is *good* (that is the Shipping Gate's vision pass); they guarantee it
is CONSISTENT.

Rules enforced here — all from `dev/ai_guides/Figures.md`:
  1. every figure script imports the style and calls apply_pub_style()
  2. no figure script sets rcParams itself (single source of truth)
  3. no figure script hard-codes a font size / dpi that the style owns
  4. light curves are histograms: a figure script that draws binned rates must use
     the shared `lc_hist` helper (or `fill_between(step=...)`/`step(where=...)`),
     never a bare `plot()` of rate vs time (F1)
  5. the style module itself matches the cross-project reference on the values that
     the reference states explicitly
"""
import os
import re

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")

# figure-producing scripts governed by the style
FIGURE_SCRIPTS = ["44_step_figures.py", "41_nuFnu_panels.py",
    "../dev/build_learning_curve.py",
]


def _src(name):
    p = os.path.join(SCRIPTS, name)
    if not os.path.exists(p):
        pytest.skip(f"{name} not present")
    return open(p).read()


@pytest.mark.parametrize("name", FIGURE_SCRIPTS)
def test_figure_script_uses_the_shared_style(name):
    s = _src(name)
    assert "plot_style" in s, (
        f"{name} does not import scripts/plot_style.py — the project style is not "
        f"optional (dev/ai_guides/Figures.md)")
    assert "apply_pub_style()" in s, f"{name} imports the style but never applies it"


@pytest.mark.parametrize("name", FIGURE_SCRIPTS)
def test_no_local_rcparams(name):
    """A second rcParams block is how the drift happened the first time."""
    s = _src(name)
    hits = re.findall(r"rcParams\s*(?:\.update|\[)", s)
    assert not hits, (
        f"{name} sets rcParams directly ({len(hits)} occurrence(s)). Style belongs in "
        f"scripts/plot_style.py only — otherwise two scripts render the same quantity "
        f"differently.")


@pytest.mark.parametrize("name", FIGURE_SCRIPTS)
def test_no_hardcoded_style_numbers(name):
    """Sizes/dpi must come from PUB, so changing the reference changes every figure."""
    s = _src(name)
    bad = []
    for m in re.finditer(r"\bdpi\s*=\s*(\d+)", s):
        bad.append(f"dpi={m.group(1)}")
    # fontsize= is allowed ONLY as an arithmetic offset from PUB (e.g. PUB[...] - 2)
    for m in re.finditer(r"fontsize\s*=\s*(\d+)", s):
        bad.append(f"fontsize={m.group(1)}")
    assert not bad, (
        f"{name} hard-codes style values {bad} — derive them from PUB "
        f"(e.g. PUB['tick_size'] - 2) so the reference guide stays the single source.")


def test_light_curves_are_histograms():
    """F1: binned counts are drawn as a histogram, never an interpolated line."""
    s = _src("44_step_figures.py")
    assert "def lc_hist" in s, "the shared light-curve histogram helper is missing"
    assert 'step="post"' in s or "step='post'" in s, (
        "the LATBright idiom is fill_between(step='post') on bin LEFT EDGES; "
        "not found in 44_step_figures.py")
    # a bare plot() of a rate array against time is the defect this rule exists for
    offenders = re.findall(r"\.plot\(\s*tc\s*,\s*(?:rate|net)\b", s)
    assert not offenders, (
        f"{len(offenders)} bare .plot(tc, rate/net) call(s) — binned data must use "
        f"lc_hist() (dev/ai_guides/Figures.md F1)")


def test_style_module_matches_the_reference_guide():
    """The values the cross-project reference states explicitly."""
    import importlib.util
    p = os.path.join(SCRIPTS, "plot_style.py")
    spec = importlib.util.spec_from_file_location("plot_style", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    PUB = m.PUB
    assert PUB["font_family"] == "serif"          # §1
    assert PUB["font_size"] == 16                 # §1
    assert PUB["label_size"] == 18                # §2
    assert PUB["tick_size"] == 14                 # §2
    assert PUB["legend_size"] == 12               # §5
    assert PUB["dpi"] == 300                      # §6
    assert PUB["tick_major"] == 6 and PUB["tick_minor"] == 3   # §3
    import matplotlib.pyplot as plt
    m.apply_pub_style()
    rc = plt.rcParams
    assert rc["mathtext.fontset"] == "stix"       # §1
    assert rc["xtick.direction"] == "in" and rc["ytick.direction"] == "in"   # §3
    assert rc["xtick.top"] and rc["ytick.right"]  # §3
    assert rc["xtick.minor.visible"] and rc["ytick.minor.visible"]           # §3
    assert rc["axes.grid"] is False               # §8


def test_style_survives_a_hostile_stylesheet():
    """apply_pub_style() must be AUTHORITATIVE, not merely applied.

    2026-08-13: the νFν montage rendered with no top/right spine and a grey
    #3D3D3D frame even though the script called apply_pub_style(). threeML runs
    plt.style.use('threeml.mplstyle') at MODULE SCOPE in seven modules, so
    importing the fit engine rewrites 29 rcParams. Our style named 17 of them and
    inherited the rest from matplotlib's defaults — which were no longer
    matplotlib's defaults. The font came back (we set it); the frame did not.

    This test does NOT import threeML: a test that skips when a heavy dependency
    is absent reports green while checking nothing (audit C1, the L18–L28 suite
    parametrizing over an empty list on CI). Instead it applies threeML's actual
    stylesheet if it is on disk, and otherwise an equivalent hostile one inline,
    so the invariant is exercised on every machine.
    """
    import glob
    import importlib.util
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    hostile = {
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.spines.left": False, "axes.spines.bottom": False,
        "axes.edgecolor": "#3D3D3D", "axes.labelcolor": "#3D3D3D",
        "xtick.color": "#3D3D3D", "ytick.color": "#3D3D3D",
        "font.size": 12, "axes.labelsize": 14, "legend.fontsize": 8,
        "xtick.labelsize": 12, "ytick.labelsize": 12, "lines.linewidth": 2,
    }
    real = glob.glob(os.path.expanduser(
        "~/anaconda3/envs/*/lib/python*/site-packages/threeML/data/threeml.mplstyle"))
    plt.rcParams.update(hostile)
    if real:                       # prefer the genuine article when present
        plt.style.use(real[0])
    assert plt.rcParams["axes.spines.top"] is False, "the hostile state did not take"

    p = os.path.join(SCRIPTS, "plot_style.py")
    spec = importlib.util.spec_from_file_location("plot_style_hostile", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.apply_pub_style()

    rc = plt.rcParams
    for side in ("top", "right", "left", "bottom"):
        assert rc[f"axes.spines.{side}"] is True, (
            f"axes.spines.{side} not reclaimed — a figure drawn after importing "
            f"threeML would lose that spine (reference guide §3 needs all four)")
    for key in ("axes.edgecolor", "axes.labelcolor", "xtick.color", "ytick.color"):
        assert matplotlib.colors.to_hex(rc[key]) == "#000000", (
            f"{key} is {rc[key]!r}, not black — threeML's #3D3D3D leaked through")
    assert rc["font.size"] == 16 and rc["axes.labelsize"] == 18
    assert rc["xtick.direction"] == "in" and rc["xtick.top"]


def test_detector_colour_is_identity_not_order():
    """F2: a detector's colour must not depend on how many others are plotted."""
    import importlib.util
    p = os.path.join(SCRIPTS, "plot_style.py")
    spec = importlib.util.spec_from_file_location("plot_style", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.det_color("b0") == m.det_color("b1") == m.PUB["c_bgo"], \
        "every BGO must share the BGO colour"
    assert m.det_color("lle") == m.PUB["c_lle"]
    # NaI colours are assigned by index and must be stable for a given index
    assert m.det_color("n3", 0) == m.det_color("na", 0)
    assert m.det_color("n3", 1) != m.det_color("n3", 0)

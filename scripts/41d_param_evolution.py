#!/usr/bin/env python
"""scripts/41d_param_evolution.py — parameter evolution across bins for models
that win at least one bin (Vikas, 2026-08-15: "if a model was preferred in any
bin then its parameter evolution ... should be there in every bin").

NO REFITS: every value, asymmetric error, and AIC comes from the engine's own
serialized table (<fit-root>/<trig>/spectral_fits.ecsv). The engine's spec
`pmap` is the parameter authority (same map that seeds 41c). Blocks render as
HORIZONTAL BARS spanning [T_START, T_STOP] (the project figure standard) with
vertical asymmetric error bars at the bar centre; bins where THIS model is the
AIC winner are accented; the T_INT value is a dotted reference line. A
provenance sidecar JSON is written next to every figure.

Usage (heavy tier — imports the engine for pmap):
  python scripts/41d_param_evolution.py --trig bn081125496 \
         --fit-root results/convention_check --out results/convention_check/param_evolution
"""
import os, sys, argparse, importlib.util, hashlib, json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from plot_style import apply_pub_style, PUB  # noqa: E402
apply_pub_style()

LOGGY = ("K", "EP", "XC", "XB", "XP", "KT", "BREAK", "ENERGY")


def _is_log(colsuf, vals):
    v = vals[np.isfinite(vals)]
    if len(v) == 0 or np.any(v <= 0):
        return False
    return any(tok in colsuf.upper() for tok in LOGGY)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trig", required=True)
    ap.add_argument("--fit-root", default=os.path.join("results", "convention_check"))
    ap.add_argument("--out", default=os.path.join("results", "convention_check",
                                                  "param_evolution"))
    ap.add_argument("--models", nargs="*", default=None,
                    help="prefixes; default = union of per-bin AIC winners")
    a = ap.parse_args()

    from astropy.table import Table

    def _load(name, path):
        s = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "scripts", path))
        m = importlib.util.module_from_spec(s)
        s.loader.exec_module(m)
        return m

    eng = _load("eng41d", "10_spectral_fit_burst.py")
    all_specs = (list(eng.MODEL_SPECS) + list(eng.SHAPE_MODEL_SPECS)
                 + list(eng.HIGHE_MODEL_SPECS) + list(eng.THREECOMP_MODEL_SPECS))

    t = Table.read(os.path.join(a.fit_root, a.trig, "spectral_fits.ecsv"))
    prefixes = sorted({c[:-4] for c in t.colnames if c.endswith("_AIC")})

    # per-bin AIC winners (blocks AND T_INT)
    winners = {}
    for row in t:
        blk = int(row["BLOCK"])
        aics = {p: float(row[f"{p}_AIC"]) for p in prefixes
                if np.isfinite(row[f"{p}_AIC"])}
        if aics:
            winners[blk] = min(aics, key=aics.get)
    models = a.models or sorted(set(winners.values()))

    blocks = t[t["BLOCK"] >= 0]
    tint = t[t["BLOCK"] == -1]
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.abspath(__file__), "rb") as fh:
        src_sha = hashlib.sha256(fh.read()).hexdigest()

    for prefix in models:
        spec = next(s for s in all_specs if s["prefix"] == prefix)
        pmap = spec["pmap"]
        psufs = list(pmap.keys())
        n = len(psufs)
        fig, axes = plt.subplots(n, 1, sharex=True,
                                 figsize=(PUB["figwidth"], 1.35 * n + 1.2),
                                 gridspec_kw=dict(hspace=0.08, top=1 - 0.5 / (1.35 * n + 1.2),
                                                  bottom=0.9 / (1.35 * n + 1.2),
                                                  left=0.16, right=0.97))
        axes = np.atleast_1d(axes)
        win_bins = sorted(b for b, w in winners.items() if w == prefix and b >= 0)
        n_invalid = 0
        for ax, suf in zip(axes, psufs):
            col = f"{prefix}_{suf}"
            rows = []
            for r in blocks:
                v = float(r[col]) if col in t.colnames else np.nan
                if not np.isfinite(v):
                    continue
                lo = abs(float(r.get(f"{col}_NEG_ERR", np.nan)))
                hi = abs(float(r.get(f"{col}_POS_ERR", np.nan)))
                if not np.isfinite(lo):
                    lo = hi = abs(float(r.get(f"{col}_ERR", 0.0)))
                valid = bool(r[f"{prefix}_VALID"]) if f"{prefix}_VALID" in t.colnames else True
                rows.append((int(r["BLOCK"]), float(r["T_START"]), float(r["T_STOP"]),
                             v, lo, hi, valid))
            vals = np.array([x[3] for x in rows])
            tint_v = (float(tint[0][col]) if len(tint) and col in t.colnames
                      and np.isfinite(float(tint[0][col])) else None)
            use_log = _is_log(suf, vals)
            # y-range from VALID values (+T_INT) ONLY — railed INVALID fits
            # must not dictate the axis (vision QC: PL_K stretched ~8 decades
            # by railed near-zero values); invalid bars simply clip.
            span = [x for x in rows if x[6]] or rows
            svals = [x[3] for x in span] + ([tint_v] if tint_v is not None else [])
            swhisk = ([x[3] - x[4] for x in span if np.isfinite(x[4])]
                      + [x[3] + x[5] for x in span if np.isfinite(x[5])])
            allv = np.array(svals + swhisk, float)
            allv = allv[np.isfinite(allv)]
            if use_log:
                allv = allv[allv > 0]
            if len(allv):
                if use_log:
                    ax.set_yscale("log")
                    ax.set_ylim(allv.min() / 1.8, allv.max() * 1.8)
                else:
                    pad = 0.08 * (allv.max() - allv.min() or abs(allv.max()) or 1.0)
                    ax.set_ylim(allv.min() - pad, allv.max() + pad)
            for b, t1, t2, v, lo, hi, valid in rows:
                if not valid:
                    n_invalid += 1
                is_win = b in win_bins
                c = PUB.get("accent", "#c44e52") if is_win else "#4878a8"
                # block = horizontal bar (project standard); errors vertical
                ax.plot([t1, t2], [v, v], color=c, lw=2.6 if is_win else 1.8,
                        alpha=1.0 if valid else 0.35, solid_capstyle="butt", zorder=4)
                ax.errorbar([0.5 * (t1 + t2)], [v], yerr=[[lo], [hi]], fmt="none",
                            ecolor=c, elinewidth=1.1, capsize=2.0,
                            alpha=1.0 if valid else 0.35, zorder=3)
            if tint_v is not None:
                ax.axhline(tint_v, color="0.45", ls=":", lw=1.2, zorder=2)
            ax.set_ylabel(suf, fontsize=PUB["tick_size"])
        axes[-1].set_xlabel("Time since trigger (s)")
        axes[0].set_title(f"{a.trig} — {spec['name']} parameter evolution", loc="left")
        # footer row, FIGURE coordinates: stamp right, legend left — outside
        # every axes, so collision with title/data is impossible (vision QC:
        # the axes-fraction stamp offset landed on the title in short panels)
        fig.text(0.99, 0.002,
                 f"stored engine table, no refit | winner in "
                 f"{len(win_bins)}/{len(blocks)} bins"
                 + (f" | {n_invalid // max(len(psufs), 1)} INVALID bins faded"
                    if n_invalid else ""),
                 ha="right", va="bottom", fontsize=PUB["tick_size"] - 4, color="0.35")
        import matplotlib.lines as mlines
        h = ([mlines.Line2D([], [], color=PUB.get("accent", "#c44e52"), lw=2.6,
                            label="AIC winner bin")] if win_bins else []) \
            + [mlines.Line2D([], [], color="#4878a8", lw=1.8, label="other bins"),
               mlines.Line2D([], [], color="0.45", ls=":", lw=1.2, label="T_INT fit")]
        fig.legend(handles=h, loc="lower left", bbox_to_anchor=(0.01, -0.005),
                   ncol=3, frameon=False, fontsize=PUB["tick_size"] - 4)

        stem = os.path.join(a.out, f"{a.trig}_paramevo_{prefix}")
        fig.savefig(stem + ".png", bbox_inches="tight")
        fig.savefig(stem + ".pdf", bbox_inches="tight")
        plt.close(fig)
        prov = dict(script="41d_param_evolution.py", script_sha256=src_sha,
                    argv=sys.argv[1:], trig=a.trig, model=spec["name"],
                    prefix=prefix, params=psufs, winner_bins=win_bins,
                    n_blocks=len(blocks), n_invalid_bar_draws=n_invalid,
                    n_invalid_bins=n_invalid // max(len(psufs), 1),
                    source_table=os.path.join(a.fit_root, a.trig, "spectral_fits.ecsv"),
                    no_refit=True)
        with open(stem + ".json", "w") as fh:
            json.dump(prov, fh, indent=1)
        print("WROTE", stem + ".png")


if __name__ == "__main__":
    main()

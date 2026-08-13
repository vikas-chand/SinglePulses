#!/usr/bin/env python
"""scripts/47_compare_systems.py -- CROSS-SYSTEM DIFF: two independent runs of
the same pipeline, on the same 106 bursts, on different machines/operators.

Vikas, 2026-08-13: "she will eventually run all 106 in her system so that we can
then finally check what differences we get in different systems."

This is the paper's replication arm (§5). It answers, per burst and per block:
does an independent execution of the SAME Skill Library reproduce the same
decisions -- and where it does not, WHICH KIND of divergence is it?

  bin 1  UNDERSPECIFICATION  the skill left a fork undefined; two operators
                             legitimately chose differently -> fix the DOCUMENT
  bin 2  JUDGMENT            both defensible under the method as written; this
                             has a FLOOR -- it is the method's intrinsic width
  bin 3  EXECUTION ERROR     one run is wrong by the method's own rules ->
                             tests/QC should have caught it

Reported quantities (per burst):
  - block count and edges (binning reproducibility)
  - per-block AIC winner agreement (the DECISION, not the number)
  - Ep / alpha / beta agreement in sigma for the shared winner
  - DECISIVE/STRONG verdict agreement
  - T90 agreement in sigma (if both temporal catalogs given)

Usage:
  python scripts/47_compare_systems.py --a results/sweep106 --b /path/to/khushboo_results \\
      --label-a claude-mac --label-b khushboo-linux --out notes/CROSS_SYSTEM_DIFF.md
"""
import os, glob, argparse
import numpy as np
from astropy.table import Table

SIMPLE = {"BAND", "CPL", "SBPL", "SBPLF"}


def fit_table(root, trig):
    for p in (os.path.join(root, trig, trig, "spectral_fits.ecsv"),
              os.path.join(root, trig, "spectral_fits.ecsv")):
        if os.path.exists(p):
            return Table.read(p, format="ascii.ecsv")
    return None


def g(r, c):
    try:
        v = float(r[c]); return v if np.isfinite(v) else np.nan
    except Exception:
        return np.nan


def verdicts(t):
    """per-block: (winner, dAIC_simple_vs_extra), keyed by rounded interval."""
    pre = sorted({c[:-4] for c in t.colnames if c.endswith("_AIC")})
    out = {}
    for r in t:
        k = int(r["BLOCK"])
        if k < 0:
            key = "TINT"
        else:
            key = (round(float(r["T_START"]), 2), round(float(r["T_STOP"]), 2))
        va = {}
        for p in pre:
            try:
                if bool(r[f"{p}_VALID"]) and np.isfinite(float(r[f"{p}_AIC"])):
                    va[p] = float(r[f"{p}_AIC"])
            except Exception:
                pass
        s = [v for p, v in va.items() if p in SIMPLE]
        x = [v for p, v in va.items() if p not in SIMPLE]
        out[key] = dict(
            winner=str(r["BEST_AIC_MODEL"]) if "BEST_AIC_MODEL" in t.colnames else "?",
            dsimp=(min(s) - min(x)) if (s and x) else np.nan,
            ep=g(r, "BAND_EP"), ep_e=g(r, "BAND_EP_ERR"),
            al=g(r, "BAND_ALPHA"), al_e=g(r, "BAND_ALPHA_ERR"),
            be=g(r, "BAND_BETA"), be_e=g(r, "BAND_BETA_ERR"))
    return out


def nsig(v1, e1, v2, e2):
    if not all(np.isfinite([v1, e1, v2, e2])):
        return np.nan
    d = np.hypot(e1, e2)
    return abs(v1 - v2) / d if d > 0 else np.nan


def grade(sig, same_winner, same_verdict):
    """The 3-bin decomposition. Conservative: only obvious cases are auto-graded;
    everything else is flagged for human adjudication (never silently binned)."""
    if same_winner and same_verdict and (not np.isfinite(sig) or sig < 1.0):
        return "AGREE"
    if same_verdict and not same_winner:
        return "bin2 JUDGMENT (degenerate winner, same verdict)"
    if np.isfinite(sig) and sig >= 3.0:
        return "bin3? EXECUTION (>=3 sigma on a shared model) -- ADJUDICATE"
    return "bin1/2? -- ADJUDICATE"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True); ap.add_argument("--b", required=True)
    ap.add_argument("--label-a", default="A"); ap.add_argument("--label-b", default="B")
    ap.add_argument("--temporal-a"); ap.add_argument("--temporal-b")
    ap.add_argument("--out", default="notes/CROSS_SYSTEM_DIFF.md")
    x = ap.parse_args()

    trigs = sorted({os.path.basename(p) for p in glob.glob(os.path.join(x.a, "bn*"))} &
                   {os.path.basename(p) for p in glob.glob(os.path.join(x.b, "bn*"))})
    L = [f"# Cross-system diff — `{x.label_a}` vs `{x.label_b}`", "",
         "Same Skill Library, same approved Stage-1 selections, independent execution.",
         "Divergence bins: **1 underspecification** (fix the document) · **2 judgment**",
         "(the method's intrinsic width) · **3 execution error** (tests should have caught it).",
         "Nothing is auto-binned unless it is unambiguous; the rest says ADJUDICATE.", "",
         f"bursts present in both: **{len(trigs)}**", ""]
    tot_blocks = agree_win = agree_verd = 0
    rows = []
    for trig in trigs:
        ta, tb = fit_table(x.a, trig), fit_table(x.b, trig)
        if ta is None or tb is None:
            rows.append(f"| `{trig}` | — | — | — | missing fit table in "
                        f"{'A' if ta is None else 'B'} |")
            continue
        va, vb = verdicts(ta), verdicts(tb)
        keys = sorted(set(va) & set(vb), key=lambda k: (k == "TINT", k))
        nb = len(keys)
        onlyA, onlyB = len(set(va) - set(vb)), len(set(vb) - set(va))
        w = sum(1 for k in keys if va[k]["winner"] == vb[k]["winner"])
        vv = 0
        worst = ("", 0.0)
        for k in keys:
            da, db = va[k]["dsimp"], vb[k]["dsimp"]
            cls = lambda d: ("DEC" if d >= 10 else "STR" if d >= 6 else "none") \
                if np.isfinite(d) else "na"
            if cls(da) == cls(db):
                vv += 1
            s = max([nsig(va[k]["ep"], va[k]["ep_e"], vb[k]["ep"], vb[k]["ep_e"]),
                     nsig(va[k]["al"], va[k]["al_e"], vb[k]["al"], vb[k]["al_e"]),
                     nsig(va[k]["be"], va[k]["be_e"], vb[k]["be"], vb[k]["be_e"])] + [0.0])
            if np.isfinite(s) and s > worst[1]:
                worst = (str(k), s)
        tot_blocks += nb; agree_win += w; agree_verd += vv
        note = "" if not (onlyA or onlyB) else f"binning differs: +{onlyA}A/+{onlyB}B blocks (bin1?)"
        rows.append(f"| `{trig}` | {nb} | {w}/{nb} | {vv}/{nb} | "
                    f"max {worst[1]:.1f}σ @{worst[0]} {note} |")
    L += ["| burst | blocks | winner agree | verdict agree | worst param σ / notes |",
          "|---|---|---|---|---|"] + rows
    if tot_blocks:
        L += ["", "## Summary", "",
              f"- blocks compared: **{tot_blocks}**",
              f"- AIC-winner agreement: **{agree_win}/{tot_blocks} "
              f"({100*agree_win/tot_blocks:.1f}%)**",
              f"- DECISIVE/STRONG verdict agreement: **{agree_verd}/{tot_blocks} "
              f"({100*agree_verd/tot_blocks:.1f}%)**", "",
              "Winner disagreement with matching verdict is **bin 2** (degeneracy — adequacy",
              "is not identity, L12/L25) and is EXPECTED at some rate; verdict disagreement is",
              "the number that must be small. Anything ≥3σ on a shared model is a bin-3",
              "candidate and needs adjudication at the primitive, not by argument."]
    # temporal
    if x.temporal_a and x.temporal_b and os.path.exists(x.temporal_a) and os.path.exists(x.temporal_b):
        A = {str(r["TRIGGER_NAME"]): r for r in Table.read(x.temporal_a, format="ascii.ecsv")}
        B = {str(r["TRIGGER_NAME"]): r for r in Table.read(x.temporal_b, format="ascii.ecsv")}
        L += ["", "## Temporal (T90)", "", "| burst | A | B | σ |", "|---|---|---|---|"]
        for t in sorted(set(A) & set(B)):
            s = nsig(g(A[t], "T90"), g(A[t], "T90_ERR"), g(B[t], "T90"), g(B[t], "T90_ERR"))
            L.append(f"| `{t}` | {g(A[t],'T90'):.2f}±{g(A[t],'T90_ERR'):.2f} | "
                     f"{g(B[t],'T90'):.2f}±{g(B[t],'T90_ERR'):.2f} | {s:.1f} |")
    os.makedirs(os.path.dirname(x.out) or ".", exist_ok=True)
    open(x.out, "w").write("\n".join(L) + "\n")
    print(f"WROTE {x.out}: {len(trigs)} bursts, {tot_blocks} blocks compared")


if __name__ == "__main__":
    main()

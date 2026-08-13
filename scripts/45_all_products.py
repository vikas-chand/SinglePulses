#!/usr/bin/env python
"""scripts/45_all_products.py -- THE COMPLETE PRODUCT SET for one burst.

Vikas, 2026-08-13: "every product must be there, like the plots we made for
background selections with their selected areas, the source selection; the
Bayesian blocks, the models fit and the way I told in this afternoon, because
these all figures will be important for diagnosis."

One command produces every diagnostic artifact for a burst, and PRINTS A
MANIFEST of what was made and what is missing (Shipping Gate: an absent product
is stated, never silently skipped).

  PRODUCT                                     step   maker
  --------------------------------------------------------------------------
  <trig>_step1_inventory.png                  1,2    scripts/44
  <trig>_step3_background.png                 3      scripts/44   (windows + polyfit)
  <trig>_step4_source.png                     4      scripts/44   (gap + source)
  <trig>_step5_binning.png                    5      scripts/44   (BB blocks + S)
  blocks/bb_blocks_spectral_<trig>.ecsv       5      scripts/27b
  <trig>/spectral_fits.ecsv + .json           6      scripts/10
  <trig>/spectral_evolution.png               6      scripts/10
  <trig>/ep_kt_correlation.png                6      scripts/10
  <trig>_step7_temporal.png                   7      scripts/44   (E-resolved T90)
  <trig>_nuFnu_bin<N>_allmodels_overlay.png   8      scripts/41 --mode binall
        ^^ ONE PER TIME BIN: every VALID model overlaid, ENGINE winner marked
           (the LATBright idiom Vikas specified 2026-08-13)
  <trig>_nuFnu_TINT_allmodels_overlay.png     8      scripts/41 --mode binall --bin tint
  <trig>_nuFnu_best_montage.png               8      scripts/41 --mode best
  <trig>_step9_qc.png                         9      scripts/44   (evidence + L28)
  PRODUCTS.md                                 --     this script (the manifest)

Heavy tier (the overlays refit per bin): conda activate threeML + CALDB.
  python scripts/45_all_products.py --trig bn081125496 --out results/sweep106/bn081125496
  python scripts/45_all_products.py --trig ... --skip-overlays     # light tier only
"""
import os, sys, glob, argparse, subprocess
import numpy as np
from astropy.table import Table

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable


def sh(cmd, env=None, log=None):
    e = dict(os.environ); e.update(env or {})
    with open(log, "a") if log else open(os.devnull, "w") as fh:
        return subprocess.call(cmd, env=e, stdout=fh, stderr=subprocess.STDOUT)


def approved(trig):
    t = Table.read(os.path.join(ROOT, "results", "background_intervals.ecsv"),
                   format="ascii.ecsv")
    rs = t[[str(x).strip() == trig for x in t["TRIGGER_NAME"]]]
    dets = [str(r["DETECTOR"]).strip() for r in rs if str(r["DETECTOR"]).strip() != "lle"]
    nais = [d for d in dets if d.startswith("n")]
    ref = None
    if nais:
        ang = {str(r["DETECTOR"]).strip(): (float(r["DET_ANGLE"])
               if str(r["DET_ANGLE"]) not in ("nan", "--") else 999) for r in rs}
        ref = min(nais, key=lambda d: ang.get(d, 999))
    return dets, ref


def nbins(out, trig):
    bf = os.path.join(out, "blocks", f"bb_blocks_spectral_{trig}.ecsv")
    if not os.path.exists(bf):
        return 0
    t = Table.read(bf, format="ascii.ecsv")
    seen = set()
    for r in t:
        seen.add((round(float(r["T_START"]), 4), round(float(r["T_STOP"]), 4)))
    return len(seen)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trig", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip-overlays", action="store_true",
                    help="light tier: no per-bin refits (no threeML needed)")
    ap.add_argument("--log", default=None)
    a = ap.parse_args()
    trig, out = a.trig, a.out
    os.makedirs(out, exist_ok=True)
    log = a.log or os.path.join(out, f"{trig}_products.log")
    dets, ref = approved(trig)
    made, missing = [], []

    # ---- steps 1-5,7,9 (light tier)
    sh([PY, os.path.join(ROOT, "scripts", "44_step_figures.py"),
        "--trig", trig, "--out", out], log=log)

    # ---- step 8: montage + per-bin overlays (heavy)
    n = nbins(out, trig)
    have_fits = os.path.exists(os.path.join(out, trig, "spectral_fits.ecsv"))
    if not a.skip_overlays and ref and n and have_fits:
        env = {"BLOCKS_ROOT": os.path.join(out, "blocks")}
        base = [PY, os.path.join(ROOT, "scripts", "41_nuFnu_panels.py"),
                "--trig", trig, "--dets", ",".join(dets), "--ref", ref, "--out", out]
        sh(base + ["--mode", "best"], env=env, log=log)
        for b in list(range(n)) + ["tint"]:
            sh(base + ["--mode", "binall", "--bin", str(b)], env=env, log=log)
    elif not have_fits:
        missing.append("step 8 overlays + montage: no spectral_fits.ecsv "
                       "(fit produced no rows -- see the fit log)")
    elif a.skip_overlays:
        missing.append("step 8 per-bin overlays: --skip-overlays requested")

    # ---- manifest
    want = [
        (f"{trig}_step1_inventory.png", "1-2 inventory + detectors"),
        (f"{trig}_step3_background.png", "3 background windows + polyfit"),
        (f"{trig}_step4_source.png", "4 source interval in the gap"),
        (f"{trig}_step5_binning.png", "5 Bayesian blocks + significance"),
        (os.path.join("blocks", f"bb_blocks_spectral_{trig}.ecsv"), "5 block table"),
        (os.path.join(trig, "spectral_fits.ecsv"), "6 fit table"),
        (os.path.join(trig, "spectral_evolution.png"), "6 parameter evolution"),
        (os.path.join(trig, "ep_kt_correlation.png"), "6 Ep-kT"),
        (f"{trig}_step7_temporal.png", "7 energy-resolved T90"),
        (f"{trig}_nuFnu_best_montage.png", "8 winner-per-bin montage"),
        (f"{trig}_nuFnu_TINT_allmodels_overlay.png", "8 T_INT all models"),
        (f"{trig}_step9_qc.png", "9 evidence + L28 edge class"),
    ]
    for b in range(n):
        want.append((f"{trig}_nuFnu_bin{b}_allmodels_overlay.png",
                     f"8 bin {b}: all models, winner marked"))
    lines = [f"# PRODUCTS — {trig}", "",
             f"approved detectors: {', '.join(dets)}  (eff-area ref {ref})",
             f"time bins: {n}", ""]
    for rel, what in want:
        p = os.path.join(out, rel)
        if os.path.exists(p):
            made.append(rel); lines.append(f"- [x] `{rel}` — {what}")
        else:
            missing.append(f"{rel} ({what})"); lines.append(f"- [ ] **MISSING** `{rel}` — {what}")
    lines += ["", f"**{len(made)} present / {len(want)} expected**"]
    if missing:
        lines += ["", "## Missing (stated, not hidden — Shipping Gate)"] + \
                 [f"- {m}" for m in missing]
    with open(os.path.join(out, "PRODUCTS.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"{trig}: {len(made)}/{len(want)} products -> {out}/PRODUCTS.md")
    if missing:
        for m in missing[:6]:
            print(f"   MISSING: {m}")


if __name__ == "__main__":
    main()

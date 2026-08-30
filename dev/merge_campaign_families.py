#!/usr/bin/env python3
"""Adopt/merge a burst's pool fit table into the canonical 24-model table.

v2 (post NR-11 operations audit):
  PREFERRED: results/campaign20_fam/<TRIG>_highe/spectral_fits.ecsv already
  holds all 24 models (the highe invocation is a cumulative superset) — adopt
  it directly. No column merge, no cross-family metadata risk.
  LEGACY: if only v1 per-family dirs exist (_default/_shape/_highe partial),
  column-merge them with structural AND metadata equality asserts.

Guards (audit defects 6 & 8): unreadable/truncated tables fail loudly with a
delete-and-rerun instruction; metadata columns (N_DETS, PLUGIN_DETS) must agree
across families in the legacy path — silent default-wins is forbidden.
Idempotent: exits 0 untouched if the canonical table already has 24 models.
"""
import argparse, json, os, sys
import numpy as np
from astropy.table import Table

STRUCT = {"BLOCK", "T_START", "T_STOP"}
# Published baselines — the pool must NEVER overwrite these canonical tables.
PROTECTED = {"bn081125496", "bn081222204"}
META_EQ = ("N_DETS", "PLUGIN_DETS")
FAMILIES = ("default", "shape", "highe")


def read_or_die(p):
    try:
        return Table.read(p)
    except Exception as exc:
        print(f"CORRUPT TABLE {p}: {exc}\n"
              f"-> delete '{os.path.dirname(p)}' and rerun that burst's fit")
        sys.exit(5)


def models_of(t):
    return {c[:-4] for c in t.colnames if c.endswith("_AIC")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trig", required=True)
    ap.add_argument("--fam-root", default="results/campaign20_fam")
    ap.add_argument("--out-root", default="results/convention_check")
    a = ap.parse_args()

    if a.trig in PROTECTED:
        print(f"{a.trig}: PROTECTED baseline (papers #1/#2) — refusing to touch")
        return 0

    out_dir = os.path.join(a.out_root, a.trig)
    out_ecsv = os.path.join(out_dir, "spectral_fits.ecsv")
    if os.path.exists(out_ecsv):
        if len(models_of(read_or_die(out_ecsv))) == 24:
            print(f"{a.trig}: canonical table already has 24 models — no-op")
            return 0
        print(f"{a.trig}: canonical table incomplete — rebuilding")

    # v2 fast path: the highe table alone carries all 24. Where legacy v1
    # family tables ALSO exist, graft the better minimum per (row, model):
    # two invocations of the same model can land in different local minima
    # (observed max|dAIC| 8.7 on composites, 2026-08-16) — canonical is the
    # BEST fit found, never the most recent.
    hp = os.path.join(a.fam_root, f"{a.trig}_highe", "spectral_fits.ecsv")
    if os.path.exists(hp):
        t = read_or_die(hp)
        if len(models_of(t)) == 24:
            grafts = 0
            for fam in ("default", "shape"):
                lp = os.path.join(a.fam_root, f"{a.trig}_{fam}",
                                  "spectral_fits.ecsv")
                if not os.path.exists(lp):
                    continue
                lt = read_or_die(lp)
                if len(lt) != len(t):
                    continue
                for m in models_of(lt) & models_of(t):
                    la = np.asarray(lt[f"{m}_AIC"], float)
                    ha = np.asarray(t[f"{m}_AIC"], float)
                    better = np.isfinite(la) & (
                        ~np.isfinite(ha) | (la < ha - 0.001))
                    if not better.any():
                        continue
                    cols = [c for c in lt.colnames
                            if c == m or c.startswith(m + "_")]
                    for i in np.where(better)[0]:
                        for c in cols:
                            if c in t.colnames:
                                t[c][i] = lt[c][i]
                        grafts += 1
            if grafts:
                print(f"{a.trig}: grafted {grafts} better (row,model) minima "
                      f"from legacy invocations")
            os.makedirs(out_dir, exist_ok=True)
            t.write(out_ecsv, overwrite=True)
            sj = os.path.join(a.fam_root, f"{a.trig}_highe", "spectral_fits.json")
            if os.path.exists(sj):
                meta = json.load(open(sj))
                meta["adopted_from"] = "highe (all-24 superset invocation)"
                json.dump(meta, open(os.path.join(out_dir, "spectral_fits.json"),
                                     "w"), indent=1)
            print(f"{a.trig}: ADOPTED highe table (24 models x {len(t)} rows)")
            return 0
        print(f"{a.trig}: highe table has {len(models_of(t))} models — "
              f"falling back to legacy merge")

    # legacy v1 merge
    tabs = {}
    for fam in FAMILIES:
        p = os.path.join(a.fam_root, f"{a.trig}_{fam}", "spectral_fits.ecsv")
        if not os.path.exists(p):
            print(f"{a.trig}: family '{fam}' missing and no all-24 highe table "
                  f"— burst not ready")
            return 2
        tabs[fam] = read_or_die(p)

    base = tabs["default"]
    for fam in ("shape", "highe"):
        t = tabs[fam]
        if len(t) != len(base):
            print(f"{a.trig}: row-count mismatch default={len(base)} "
                  f"{fam}={len(t)}")
            return 3
        for col in ("BLOCK", "T_START", "T_STOP"):
            if not np.allclose(np.asarray(base[col], float),
                               np.asarray(t[col], float), atol=1e-6):
                print(f"{a.trig}: {col} misalignment default vs {fam}")
                return 3
        for col in META_EQ:
            if col in base.colnames and col in t.colnames:
                if any(str(x) != str(y) for x, y in zip(base[col], t[col])):
                    print(f"{a.trig}: {col} DIFFERS between default and {fam} "
                          f"— plugin sets diverged (e.g. LAT build failure in "
                          f"one family); resolve before merging")
                    return 6
        for col in t.colnames:
            if col in STRUCT or col in base.colnames:
                continue
            base[col] = t[col]

    models = models_of(base)
    if len(models) != 24:
        print(f"{a.trig}: merged table has {len(models)} models, need 24")
        return 4
    os.makedirs(out_dir, exist_ok=True)
    base.write(out_ecsv, overwrite=True)
    sj = os.path.join(a.fam_root, f"{a.trig}_default", "spectral_fits.json")
    if os.path.exists(sj):
        meta = json.load(open(sj))
        meta["merged_from_families"] = list(FAMILIES)
        json.dump(meta, open(os.path.join(out_dir, "spectral_fits.json"), "w"),
                  indent=1)
    print(f"{a.trig}: MERGED legacy families (24 x {len(base)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

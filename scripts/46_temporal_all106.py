#!/usr/bin/env python
"""scripts/46_temporal_all106.py -- temporal properties for ALL 106, not just the roster.

`scripts/40_temporal_survey.py` sweeps the 89-burst human_clean roster. The
approved catalog holds 106, so 17 bursts (including bn090530760, bn180723757,
bn190401139, bn200524211) get no temporal row from that sweep -- a silent gap.
This script runs the SAME production estimator (`survey_one` imported from
scripts/40, never a fork) over every burst in results/background_intervals.ecsv
and writes one catalog.

T90 errors use the FIXED Monte-Carlo estimator (handbook temporal.py, 2026-08-13:
Poisson mock light curves in place, T90 = t95 - t5 formed per realization so the
t5/t95 covariance is included). Rows produced before that fix are not comparable.

  python scripts/46_temporal_all106.py                 # all 106
  python scripts/46_temporal_all106.py --only bn0905307 60 ...
"""
import os, sys, argparse, importlib.util
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from astropy.table import Table

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_T40_PATH = os.path.join(ROOT, "scripts", "40_temporal_survey.py")


def _load_t40():
    """Load scripts/40 and REGISTER it in sys.modules, so that worker processes
    (spawn start method on macOS) can unpickle functions that belong to it.
    Without the registration the pool dies with
    "Can't pickle <function survey_one>: import of module 't40' failed"."""
    if "t40mod" in sys.modules:
        return sys.modules["t40mod"]
    sp = importlib.util.spec_from_file_location("t40mod", _T40_PATH)
    m = importlib.util.module_from_spec(sp)
    sys.modules["t40mod"] = m
    sp.loader.exec_module(m)
    return m


t40 = _load_t40()


def _work(row):
    """Top-level worker: picklable, and re-loads the engine inside the child."""
    return _load_t40().survey_one(row)

OUT = os.path.join(ROOT, "results", "temporal_catalog_all106.ecsv")


def build_rows(only=None):
    cat = Table.read(os.path.join(ROOT, "results", "background_intervals.ecsv"),
                     format="ascii.ecsv")
    rows, skipped = [], []
    for trig in sorted({str(x).strip() for x in cat["TRIGGER_NAME"]}):
        if only and trig not in only:
            continue
        sub = cat[[str(x).strip() == trig for x in cat["TRIGGER_NAME"]]]
        nai = [r for r in sub if str(r["DETECTOR"]).strip().startswith("n")]
        if not nai:
            skipped.append((trig, "no approved NaI")); continue
        ref = min(nai, key=lambda r: float(r["DET_ANGLE"])
                  if str(r["DET_ANGLE"]) not in ("nan", "--") else 999)
        ev = t40._events(trig, str(ref["DETECTOR"]).strip())
        if ev is None:
            skipped.append((trig, "no TTE on disk")); continue
        rows.append({"trigger": trig, "ref": str(ref["DETECTOR"]).strip(), "_ev": ev,
                     "src1": float(ref["SRC_START"]), "src2": float(ref["SRC_STOP"]),
                     "pre1": float(ref["BKG_NEG_START"]), "pre2": float(ref["BKG_NEG_STOP"]),
                     "post1": float(ref["BKG_POS_START"]), "post2": float(ref["BKG_POS_STOP"])})
    return rows, skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--workers", type=int, default=10)
    a = ap.parse_args()
    rows, skipped = build_rows(set(a.only) if a.only else None)
    print(f"temporal over {len(rows)} bursts ({len(skipped)} skipped) ...")
    res = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(_work, r): r["trigger"] for r in rows}
        for i, f in enumerate(futs, 1):
            pass
        for f, trig in futs.items():
            try:
                res.append(f.result())
                print(f"  {trig} ok", flush=True)
            except Exception as e:
                skipped.append((trig, f"failed: {e}"))
                print(f"  {trig} FAILED: {e}", flush=True)
    if res:
        t = Table(rows=res)
        t.write(OUT, format="ascii.ecsv", overwrite=True)
        bad = sum(1 for r in t if np.isfinite(float(r["T90_ERR"]))
                  and float(r["T90_ERR"]) > float(r["T90"]))
        print(f"WROTE {OUT}: {len(t)} rows; T90_ERR>T90 in {bad} "
              f"(must be ~0 with the fixed estimator)")
    if skipped:
        print("SKIPPED (stated, not hidden):")
        for s in skipped:
            print("   ", *s)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
36_progress_check.py -- Background-selection progress + continuous QC.
Run anytime (Khushboo or Salim):  python scripts/36_progress_check.py
Compares results/background_intervals.ecsv (the human selections, appended by
scripts/30_background_picker.py) against results/background_starting_points.ecsv
(the full burst x detector manifest). Pure numpy/astropy -- portable.
"""
import os, sys
import numpy as np
from astropy.table import Table

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(BASE, "results", "background_starting_points.ecsv")
OUTPUT   = os.path.join(BASE, "results", "background_intervals.ecsv")
PRIORITY = ["bn090620400","bn090719063","bn100612726","bn100614498",
            "bn110920546","bn200524211"]

man = Table.read(MANIFEST, format="ascii.ecsv")
need = {(str(r["TRIGGER_NAME"]), str(r["DETECTOR"])) for r in man}
bursts = sorted({t for t, d in need})

if not os.path.exists(OUTPUT):
    print(f"progress: 0/{len(need)} detector windows (0.0%) -- output file not created yet")
    print(f"bursts complete: 0/{len(bursts)}")
    print('next: run  python scripts/30_background_picker.py --approver "<your name>"  and Accept the first burst')
    sys.exit(0)

out = Table.read(OUTPUT, format="ascii.ecsv")
done_pairs = [(str(r["TRIGGER_NAME"]), str(r["DETECTOR"])) for r in out]
done = set(done_pairs)

# ---- QC checks (continuous, not just at the end) ----
problems = []
if len(done_pairs) != len(done):
    from collections import Counter
    dups = [k for k, v in Counter(done_pairs).items() if v > 1]
    problems.append(f"DUPLICATE rows (picker append bug / stale file?): {dups[:5]}")
stray = done - need
if stray:
    problems.append(f"rows not in the manifest (wrong burst/detector?): {sorted(stray)[:5]}")
for r in out:
    w1 = float(r["BKG_NEG_STOP"]) - float(r["BKG_NEG_START"])
    w2 = float(r["BKG_POS_STOP"]) - float(r["BKG_POS_START"])
    if w1 <= 0 or w2 <= 0:
        problems.append(f"zero/negative-width window: {r['TRIGGER_NAME']} {r['DETECTOR']}")
    elif max(w1, w2) > 200:
        problems.append(f"very wide window (>200 s): {r['TRIGGER_NAME']} {r['DETECTOR']} ({w1:.0f}/{w2:.0f} s)")

# ---- approval-stamp QC (auditability gate: every row must record who approved it) ----
if "APPROVED_BY" not in out.colnames:
    problems.append("NO approval stamp columns (old picker?) — re-run scripts/30 with --approver")
else:
    unattributed = [(r["TRIGGER_NAME"], r["DETECTOR"]) for r in out
                    if str(r["APPROVED_BY"]).strip() in ("", "unknown")]
    if unattributed:
        problems.append(f"rows with no APPROVED_BY: {len(unattributed)} (e.g. {unattributed[:3]})")

# ---- progress ----
nb_done = [t for t in bursts if all((t, d) in done for td, d in
           [(x, y) for x, y in need if x == t])]
frac = 100 * len(done & need) / len(need)
print(f"progress: {len(done & need)}/{len(need)} detector windows ({frac:.1f}%)")
print(f"bursts complete: {len(nb_done)}/{len(bursts)}")
prio_done = [t for t in PRIORITY if t in nb_done]
print(f"priority-6 (once-broken) complete: {len(prio_done)}/6 {prio_done}")
pending = [t for t in bursts if t not in nb_done]
print(f"next pending bursts: {pending[:8]}")
if "APPROVED_BY" in out.colnames and len(out):
    from collections import Counter
    who = Counter(str(r["APPROVED_BY"]).strip() for r in out)
    src = Counter(str(r["WINDOW_SOURCE"]).strip() for r in out) if "WINDOW_SOURCE" in out.colnames else {}
    print(f"approved by: {dict(who)}")
    print(f"window source: {dict(src)}  (accepted_seed = took the pre-drawn window unchanged)")
if problems:
    print("\n!! QC PROBLEMS (tell Vikas/Claude):")
    for p in problems[:12]:
        print("   -", p)
else:
    print("\nQC: clean (no duplicates, no stray rows, all widths sane)")

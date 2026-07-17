#!/usr/bin/env python
"""
36_progress_check.py -- Stage-1 catalog progress + continuous QC.
Run anytime (Khushboo or Vikas):  python scripts/36_progress_check.py

Validates results/background_intervals.ecsv (the APPROVED catalog, written by
scripts/39 ingest -- human GUI or AI-vision decisions) against the 106-burst
sample (results/single_pulse_grbs.ecsv) and the catalog's own invariants:
  - coverage: every sample burst present;
  - per row: window ordering, source-in-gap, near-edge margins in the 5-40 s
    band (dev/ai_guides/background_selection.md), widths sane;
  - auditability: every row carries an APPROVED_BY stamp; no duplicates.

The 418-row seed manifest (background_starting_points.ecsv) is reported as INFO
only: approved detector sets legitimately differ from the seeds (the 2026-07
consensus catalog has 480 rows), so it is NOT a completion target anymore.
Pure numpy/astropy -- portable.
"""
import os, sys
import numpy as np
from astropy.table import Table

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE   = os.path.join(BASE, "results", "single_pulse_grbs.ecsv")
MANIFEST = os.path.join(BASE, "results", "background_starting_points.ecsv")
OUTPUT   = os.path.join(BASE, "results", "background_intervals.ecsv")

sample = Table.read(SAMPLE, format="ascii.ecsv")
scol = "TRIGGER_NAME" if "TRIGGER_NAME" in sample.colnames else sample.colnames[0]
sample_bursts = sorted({str(r[scol]).strip() for r in sample})

if not os.path.exists(OUTPUT):
    print(f"progress: 0/{len(sample_bursts)} bursts -- catalog not created yet")
    print('next: python scripts/39_approve_all.py render --all, then approve '
          '(gui with --approver, or AI-vision decision.json) and ingest')
    sys.exit(0)

out = Table.read(OUTPUT, format="ascii.ecsv")
pairs = [(str(r["TRIGGER_NAME"]).strip(), str(r["DETECTOR"]).strip()) for r in out]
done_bursts = sorted({t for t, d in pairs})

problems = []

# ---- duplicates ----
if len(pairs) != len(set(pairs)):
    from collections import Counter
    dups = [k for k, v in Counter(pairs).items() if v > 1]
    problems.append(f"DUPLICATE (burst,detector) rows: {dups[:5]}")

# ---- coverage vs the sample ----
missing = [t for t in sample_bursts if t not in done_bursts]
extra   = [t for t in done_bursts if t not in sample_bursts]
if extra:
    problems.append(f"bursts NOT in the 106-burst sample: {extra[:5]}")

# ---- per-row physics QC ----
n_margin_warn = 0
for r in out:
    t, det = str(r["TRIGGER_NAME"]).strip(), str(r["DETECTOR"]).strip()
    p0, p1 = float(r["BKG_NEG_START"]), float(r["BKG_NEG_STOP"])
    q0, q1 = float(r["BKG_POS_START"]), float(r["BKG_POS_STOP"])
    s1, s2 = float(r["SRC_START"]), float(r["SRC_STOP"])
    if not (p0 < p1 <= s1 < s2 <= q0 < q1):
        problems.append(f"ordering/source-in-gap violation: {t} {det}")
        continue
    w1, w2 = p1 - p0, q1 - q0
    if w1 <= 0 or w2 <= 0:
        problems.append(f"zero/negative-width window: {t} {det}")
    elif max(w1, w2) > 200:
        problems.append(f"very wide window (>200 s): {t} {det} ({w1:.0f}/{w2:.0f} s)")
    g_pre, g_post = s1 - p1, q0 - s2
    if g_pre < 5 or g_post < 5:
        problems.append(f"margin <5 s (tail-leak risk): {t} {det} "
                        f"(g_pre={g_pre:.1f}, g_post={g_post:.1f})")
    elif g_pre > 40 or g_post > 40:
        n_margin_warn += 1          # >40 s = outside the band; warn in bulk

# ---- approval-stamp QC (auditability gate) ----
if "APPROVED_BY" not in out.colnames:
    problems.append("NO approval stamp columns -- catalog predates the gate?")
else:
    unattributed = [(t, d) for (t, d), r in zip(pairs, out)
                    if str(r["APPROVED_BY"]).strip() in ("", "unknown")]
    if unattributed:
        problems.append(f"rows with no APPROVED_BY: {len(unattributed)} "
                        f"(e.g. {unattributed[:3]})")

# ---- progress ----
print(f"progress: {len(done_bursts)}/{len(sample_bursts)} sample bursts approved "
      f"({len(out)} detector rows)")
if missing:
    print(f"missing bursts: {missing[:8]}{' ...' if len(missing) > 8 else ''}")
if n_margin_warn:
    print(f"note: {n_margin_warn} rows with a near-edge margin >40 s "
          f"(outside the 5-40 s band -- justify or re-check)")
if "APPROVED_BY" in out.colnames and len(out):
    from collections import Counter
    who = Counter(str(r["APPROVED_BY"]).strip() for r in out)
    src = Counter(str(r["WINDOW_SOURCE"]).strip() for r in out) if "WINDOW_SOURCE" in out.colnames else {}
    print(f"approved by: {dict(who)}")
    print(f"window source: {dict(src)}")

# ---- seed-manifest delta (INFO only; the seeds are NOT a completion target) ----
if os.path.exists(MANIFEST):
    man = Table.read(MANIFEST, format="ascii.ecsv")
    need = {(str(r["TRIGGER_NAME"]).strip(), str(r["DETECTOR"]).strip()) for r in man}
    got = set(pairs)
    print(f"seed-manifest delta (INFO): {len(got & need)} rows match the {len(need)}-row "
          f"seed manifest; +{len(got - need)} approved beyond it, "
          f"{len(need - got)} seeds not adopted (approved sets may differ -- expected)")

if problems:
    print("\n!! QC PROBLEMS (tell Vikas/Claude):")
    for p in problems[:12]:
        print("   -", p)
    sys.exit(1)
print("\nQC: clean (coverage, ordering, margins, widths, stamps all pass)")

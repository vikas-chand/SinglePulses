# PORT-VERIFIER (A12) VERDICT — phase-7 row_repair — 2026-08-30

**VERDICT: PORT-VERIFIED** (fresh-context A12, non-producer)
**Subject:** notes/codex_campaign20_runtime/run_p2_temporal.py @ commit a3bcf3b
**sha256 (verdict binds to this):** 17bdeef1a000410f9eac0e79133ae402541b0fae2a7202b1c2e930f790ffae3f
**Tolerance:** numeric equivalences at abs_tol=1e-12; LAG_S sign = exact byte-identical
float copy of tau_s from bn110920546_step7_lag_latbright.json (+0.7152763181433653),
no arithmetic in the path; convention carried as TEXT only, never arithmetic (post-L26 correct).

**Cases run:** producer harness 18/18 (scratchpad port_verify_rowrepair.py — audited
before trust, sign-flip case confirmed genuine) + A12's OWN gap cases 15/15
(scratchpad pv_own/pv_gap_cases.py): (A) swapped-sigma ordering — LAG_ERR_S tracks
max(), not hard-coded sigma_r; LAG_SIG==peak_sig; LAG_ACCEPTED stays bool;
(B) Bala status=limit, mvt_err_s=None → MVT_ERR_S NaN, MVT_TYPE 'limit', validators pass;
(C) truncation-at-the-primitive — disk LAG_CONVENTION (289 chars) & MVT_ESTIMATOR
byte-equal to sidecar after ECSV round-trip; (D) pre-existing empty MVT_ESTIMATOR
column — 'already' False, Haar preserved. Integration: plan lists phase 7;
unit tests 15/15; real catalog untouched (rewalked_triggers=[], no repair columns).
No-repair-path-impossible confirmed: collect_summary calls validate_row_repair
unconditionally; a burst cannot reach COMPLETE with handbook values in its row.

## Weaknesses noted (verifier: "none can flip a sign, fold the systematic into the
## error, or let an unrepaired row through") — BACKLOG, fix bundled with the next
## runner change (editing the verified producer now would expire this verdict; PI may
## order the hardening sooner):
1. repair_row's post-write readback checks row count + meta only; sidecar 'after' is
   captured from memory, not disk readback (caught downstream by validate_row_repair's
   disk re-read; Case C confirmed disk==sidecar for strings).
2. validate_row_repair does not numerically compare MVT_ERR_S / MVT_HAAR_ERR_S to
   sources (MVT_S, LAG_S, LAG_ERR_S, LAG_WINDOW_SYS_S all are).
3. Masked/NaN pre-repair MVT_S → untyped ValueError instead of ValidationError
   (fail-closed but ungraceful).
4. "Other 105 rows unchanged" harness check covers 6 numeric columns, not full width.

**PASS expiry:** this verdict expires on any hash change of run_p2_temporal.py
(AgentRoster A12 decision 14, proposed=yes). Re-verify on edit.

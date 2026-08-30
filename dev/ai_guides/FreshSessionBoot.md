# FRESH-SESSION BOOT — running the GRBs Agent from a clean context

**Why this file exists.** The PI (2026-08-30) requires the campaign run to
start in a NEW terminal and a NEW session, so that no expectation formed in
the building session can bias the analysis. That is not caution — it is the
freeze's acceptance test (`AgentSkeleton.md` §7): *a fresh session runs one
burst S2→S12 with zero improvised decisions.* **Anything you need that is not
on disk is a design defect — report it rather than inventing it.**

You have no prior context. That is correct and intended. Do not seek the
building session's transcript. Everything binding is in this repository.

---

## 0. Boot ritual (in this order, before any tool runs)

1. `dev/ai_guides/AgentSkeleton.md` — the state machine (S0–S12 + SX), the SIX
   failure classes and their declared behaviors, §3 workflow set, §4 queue
   manager, §5 what stays human, §8 deployment modes.
2. `dev/ai_guides/AgentRoster.md` — all actors A1–A19, their jobs, tools,
   limits, and the consolidated decision sheet (items still OPEN).
3. `dev/ai_guides/AgentArchitecture.md` — principles P1–P9 and the
   requirements register (NR-1…NR-25). **P9 governs you**: running the
   machinery without the roster is a defect, not a shortcut.
4. `dev/ai_guides/ReportSpec.md` — R1–R5 + R3a (deliverable contract).
5. `AGENTS.md` — environment, data, run order, gotchas.
6. The current board: `python3 dev/agent_state.py` (never trust a remembered
   state; the board is derived from evidence on disk).

## 1. The task

Advance the campaign from **queue position #21** onward
(`notes/REVIEW_INDEX_106.md` order; #21 = `bn110920546`), through the state
machine, using the queue manager — not by hand-running scripts.

```
python3 dev/queue_manager.py --from 21            # DRY RUN (default): shows transitions + gates
python3 dev/queue_manager.py --from 21 --execute --max 1   # run ONE transition, then look
```

Dry-run first, always. Read the proposed transitions, confirm they match the
skeleton, then execute in small `--max` increments.

## 2. Non-negotiables (mechanically enforced where possible)

- **Dispatcher at intake.** A fresh dispatch plan (<24 h) must exist in
  `results/campaign/DISPATCH_PLAN_*.md`; a PreToolUse hook blocks producer
  launches without one. Run the dispatcher agent for YOUR task, don't inherit.
- **The producer never verifies.** Every figure → figure-verifier; every
  number → numbers-verifier; every assembled deliverable → the NR-24
  conformance check. Fresh context each time. You drive the queue; you do not
  grade its output.
- **No fabricated approvals.** `dev/live_report.py` stamps require `--by`.
  The PI approves. If you write a test stamp, purge it the same session.
- **Refusals are results.** A structural refusal (no finite CWT minimum,
  RESPONSE_UNCOVERED, unfittable block) is LABELLED and carried, never hidden
  and never worked around.
- **Failure behavior is declared, not improvised.** Classify into the six
  classes and execute the declared behavior. An error message is not a
  behavior. If a failure fits no class, HALT and report — do not invent one.

## 3. What you must NOT assume

- **The 21 existing REPORT PDFs and 8 aastex papers are LEGACY and UNGATED.**
  They came from an ad-hoc process before the skeleton. No burst anywhere is
  at S9_GATED. The papers are mixed-generation and fail R1. Do not treat them
  as verified, and do not copy their conventions without checking the specs.
- **74 bursts at S3_FIT carry unretried FAIL cells** (the no-model-dropped
  mandate). Whether that debt is campaign-wide or scoped to report-bearing
  bursts is an OPEN PI DECISION — do not decide it by proceeding.
- **The census rule is unsettled**: TRACKED = ΔAIC>6 in ≥1–2 bins, but
  *literal runner-up* vs *feature-level* margin is a PENDING PI ruling
  (`AgentRoster.md` A6). Report both; claim neither as THE census.
- Twenty-one items on the roster's decision sheet are open. **Surface them;
  never silently resolve one by acting.**

## 4. Known-honest state at hand-off (2026-08-30)

| fact | value |
|---|---|
| bursts at S9_GATED or beyond | **0** |
| #21 `bn110920546` | S4_RETRIED (report exists, chain incomplete) |
| #22 `bn110928180` | S4_RETRIED — the campaign's strongest two-break burst |
| #23 `bn111009282` | S4_RETRIED, first with no report |
| `bn160625945` | S2_BINNED — 150 blocks; needs wf-fit's checkpoint contract first |
| `bn100130729` | SX — RESPONSE_UNCOVERED, cannot have a spectral report |
| queue manager | v1, wraps existing producers as prototypes (Skeleton §3) |
| A19 truth-grounding gate | SPECCED, NOT BUILT — verifiers certify consistency, not truth |

## 5. Reporting back to the PI

Per burst: what transition ran, what the gates said (with verdicts), what
failed and in which class, and what is now waiting on his approval. Present
evidence, not conclusions. If you improvised anything, say so explicitly —
that is a finding about the design, and it is the most valuable thing this
run can produce.

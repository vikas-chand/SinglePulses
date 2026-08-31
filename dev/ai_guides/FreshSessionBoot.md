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

## 1. The task — WALKTHROUGH MODE, one burst at a time

The PI's instruction (2026-08-30): *walk through burst #21, see whether it
works, then #22, and keep going — reading in detail.* **This is not an
autonomous queue drain.** It is the gated per-burst protocol of
`dev/ai_guides/BurstWalkthrough.md`: RUN → **PRESENT** → **GATE (the PI)** →
LITERATURE → DISTILL, at every step. You stop at each gate. He reads. He
approves or feeds back. Only then does the next step run.

Start at **#21 `bn110920546`** (`notes/REVIEW_INDEX_106.md` order), currently
S4_RETRIED. Advance it through the state machine one transition at a time,
presenting evidence at each stop.

**DELIVERABLES PER BURST — both, per the PI (2026-08-30): "create reports
too."**
1. the **REPORT** (`REPORT_<trig>.md` + PDF) — the per-burst analysis record;
2. the **aastex paper** (`paper/GRB<name>/`) — assembled at the pinned
   campaign commit with a staging manifest (R1).
Both are UNGATED PRODUCER ARTIFACTS until figure-verifier + numbers-verifier
+ the NR-24 conformance check have returned sha-bound verdicts (R4). Neither
reaches the PI, a bundle, or a collaborator before that.

**On tooling:** `dev/queue_manager.py` (A17) does **not exist yet**. Either
build it first to `AgentSkeleton.md` §4 (the sanctioned first move — ask the
PI), or advance the burst on the §3 prototype chains under the dispatch
plan's gates. Whichever you choose, say which, and never launch a producer
outside the plan.

## 2. Non-negotiables (mechanically enforced where possible)

- **Dispatcher at intake.** A fresh dispatch plan (<24 h) must exist in
  `results/campaign/DISPATCH_PLAN_*.md`; a PreToolUse hook blocks producer
  launches without one. **You may READ an existing fresh plan as evidence
  (§6), but the plan binding YOUR run must be issued for YOUR task** — if the
  task differs in scope, mode, or burst set from the plan on disk, run the
  dispatcher yourself. *(Corrected 2026-08-30: §2 previously said "don't
  inherit" while §6 said "read the existing plan" — a self-contradiction in
  the law, found by the first fresh session. Inheriting a plan issued for a
  different task is the defect; reading it is not.)*
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

---

## 6. Dispatch findings you inherit (2026-08-30, from the dispatcher agent)

**Your dispatch plan already exists**: `results/campaign/DISPATCH_PLAN_campaign21plus.md`
— read it. It names the roster per transition for #21–#23, the unguarded
debt, and the producer/verifier separation rules for a session driving the
queue. It is <24 h old, so the P9 hook will pass; if it ages out, run the
dispatcher yourself rather than reusing a stale plan.

**RESOLVED before hand-off:** the R1 hard blocker. `scripts/41e_sed_montage.py`
and `results/temporal_catalog_all106.ecsv` were modified-uncommitted, which
would have made every paper from this run carry "no commit". Both are now
committed; **the campaign commit is pinned. Do not edit a producer mid-run —
that is F-CONTRACT: stop, then regenerate whatever was already assembled.**

**BLOCKED — no census sentence may ship from this run.** 333 unretried FAIL
cells across 79 S3 bursts are NOT randomly distributed: BANDRCPL 121 cells /
59 bursts, DSBPLF 53/28, BANDCPL 45/27, SBPLCPL 31/20. They concentrate in
the two-component and free-break families that carry the two-break and
hard-tail claims, and `results/campaign/model_preference.ecsv` (104 trigs,
518 rows) is built on those incomplete sets. Per-burst rows may be written.
**Any cross-burst census statement is blocked until the retry debt is
terminal and a missing-cell companion census exists.** The direction of the
bias is NOT established — do not assume "lower limit"; measure it.

**Retro-gating exposure (highest-priority backlog, does not block #21+):**
21 REPORT PDFs shipped but only ~9 VISION_QC ledgers exist, and
`handoff_background_approval/KHUSHBOO_REPORTS_20260817.zip` sits in the tree.
Those are delivered-ungated artifacts. Per R1 they are regenerated, never
hand-patched. Run them in a RETRO lane at low RAM priority between #21+
transitions; `bn081224887` (the only manifest-stamped paper) is also the
queue's only available regression test.

**Run-order question for the PI — do not decide alone.** REVIEW_INDEX order
(canonical) puts #21 `bn110920546` first: 11 blocks, 8 DECISIVE, 10 BB
blocks, 3 residual FAILs, and an existing report to reconcile — the hardest
of the three through an unvalidated path. Engineering argues #23
`bn111009282` first as the control (7 blocks, 0 FAIL cells, no prior report),
then #21, then #22 (12 residual FAILs; manifest already 15/16 — the
NO-MODEL-DROPPED and NR-16 stress case). Ask the PI; canonical order stands
unless he grants the exception.

**Not built yet:** `dev/queue_manager.py` (A17) and `.claude/workflows/`.
Every transition therefore runs on the §3 PROTOTYPE chains under the dispatch
plan's gates. Building the queue manager to `AgentSkeleton.md` §4 is the
sanctioned first move if you prefer the machinery before the mileage — that
is a PI call too.

**Live evidence for decision-sheet item 1:** the P9 hook blocked read-only
calls whose command TEXT merely named producer scripts. A command-position
fix is drafted but unapplied. Strip Bash from the dispatcher/readers and this
class disappears.

---

## 7. TWO LANES — both ends of the mission (PI, 2026-08-30)

The queue is chronological, so **every lesson the agent has learned so far
came from 2008–2011 bursts** (#1–#22). The PI's instruction: also run a batch
of recent bursts *"so that we have skills on both ends, new and old."* This
is a skill-transfer test, and the project has already been bitten once by the
cross-era hardcode class (constants tuned on one era's burst silently applied
to another — the per-burst parameterized temporal figures exist because of
it).

**LANE A — walkthrough, old era.** #21 `bn110920546` → #22 `bn110928180` →
onward, one burst at a time, PI reading each step, both deliverables.

**LANE B — batch, recent era: queue #80–#100 (2021–2025).** Same gates, less
step-by-step narration; the PI reads the finished deliverables rather than
each step. Composition to expect:

| | |
|---|---|
| era | 2021, 2022, 2023, 2024, 2025 |
| states | mostly **S3_FIT** — they need `wf-retry` first, so this lane also pays down the 333-cell debt |
| size range | 2 blocks (#81) to 108 (#92 `bn230812790`) and 96 (#100) |
| claim-bearing members | **#100 `bn250313607`** — one of only three two-break TRACKED bursts; **#91 `bn230802285`** — a thermal candidate (2 bins, ΔAIC 48.9/25.3) currently flagged EDGE-SUSPECT |

**What Lane B is actually testing.** Any skill, constant, or contract that
works on Lane A and fails on Lane B is a **cross-era defect**, and that
finding is worth more than the burst itself — route it to the distiller as a
register row, not as a one-off fix. Specifically watch: detector
configurations and EAC behavior on modern multi-NaI sets, response
(`rsp2`) versions and slew handling, LAT availability, background-window
conventions across the mission, and whether pulse-scaled parameters
(lag windows, MVT settings) transfer.

**Ordering:** run Lane A first far enough to know the path works (the PI's
"see if it works"), then interleave Lane B rather than serializing — the
16 GB temporal claim means only one burst occupies that transition at a time
anyway, so a second lane costs little wall-clock and doubles the evidence.

---

## 8. PLAIN LANGUAGE AT EVERY GATE (PI catch, 2026-08-30 — binding)

The PI could not understand a gate presentation ("everything has suddenly
become a complicated language"). That is a presentation FAILURE, never a
reader failure. Standing project rule (audience = first-year PhD student;
every concept gets one plain-language explanation) applies to gate
presentations, not just manuscripts.

EVERY presentation to the PI MUST open with exactly four plain sentences,
before any technical content, codes, or file paths:

  WHAT I DID:            (one sentence, no jargon)
  WHAT I FOUND:          (one sentence; the single most important thing)
  WHAT I NEED FROM YOU:  (one sentence; a yes/no or a choice, stated simply)
  WHAT HAPPENS NEXT:     (one sentence; after your answer)

Rules: no register numbers, no state codes, no acronyms in these four lines
(spell things out: "the list of failed fits", not "FAIL cells"). The
technical detail follows BELOW the four lines for when the PI wants depth.
The PI may always reply in plain language; translating his words into the
machinery is the session's job, never his. If the PI says he does not
understand, re-present in simpler words — that costs nothing and is always
the correct move.

## 9. GATES AS STRUCTURED CHOICES (PI ruling, 2026-08-30)

Present every gate the way Claude Code presents its own questions: use the
AskUserQuestion tool — a small set of options, one marked "(Recommended)"
where a recommendation is honest (see below), and the PI can always pick
"Other" and type in plain words. The four plain sentences (§8) form the
question text; each option's description says in one line what choosing it
does. Multi-select where choices are independent.

WHO may recommend — the one safeguard:
- At DECISION gates (rulings, orderings, conventions — e.g. "which numbering
  is official?"): the session may recommend, with its reason in the option
  description.
- At APPROVAL gates (approve this step's own products): the recommendation
  must come from the VERIFIER VERDICTS, never from the producer's own
  preference — "Approve (all three gates passed)" is honest; a producer
  recommending approval of its own work is the self-approval pressure the
  axiom forbids. If any gate failed or was skipped, NO option carries
  "(Recommended)".

EVERY choice the PI clicks still becomes a real identity-bound stamp
(dev/live_report.py --by VIKAS ...) — the click is the interface, the stamp
is the record. "Other" answers in plain language are translated into the
machinery by the session, then read back to the PI in one sentence for
confirmation before stamping.

## 10. DIVERGENCE LEARNING — when the human and the AI disagree and neither failed
(PI directive, 2026-08-31: "there must be a mechanism where, after validation
of the reason where AI and human were diverging, what makes them converge is
added as a skill and taken forward.")

Failures feed the distiller; PI feedback feeds the routing protocol. This is
the THIRD learning trigger: a recorded human choice differs from what the
pipeline/AI passes recommended, and no one is in error — the human knew
something unwritten. The step-2 detector case of bn110920546 is the founding
instance (human kept 4 of the recommended 7; reason: the TRIGGERED set plus
the same-side BGO; validated against the BCAT mask and the side rule).

The protocol, exactly as the founding instance ran it:
1. DETECT — any presentation of a recorded human decision must compare it
   against what the machinery recommended at the time; an unexplained
   divergence is surfaced, never smoothed over.
2. ELICIT — ask the human for the reason, in their words. NEVER write a
   guessed reason into a record ("I won't put words in the record you didn't
   say" is the standard). A candidate reason may be OFFERED for confirmation,
   clearly labeled as the machine's guess.
3. VALIDATE — check the stated reason against the data. A reason that checks
   out is knowledge; one that doesn't is a discussion to have with the human,
   not a silent correction in either direction.
4. GENERALIZE — test whether the reason is a RULE: run a read-only census
   across other bursts. One-off preference → record locally and stop.
   Pattern → write it into the OWNING SKILL as a decision rule, so future AI
   passes converge with the human by default.
5. LEDGER — every case, one row in results/campaign/divergence_ledger.md:
   what diverged, the human's validated reason, one-off or rule, where the
   rule now lives. The ledger's CONVERGENCE RATE over time (how often AI
   passes now match the human first try) is a first-class campaign metric —
   and it is the readiness measure for the fully-AI approver question (A16):
   an AI may hold a gate alone only where its convergence with the human is
   demonstrated, never before.

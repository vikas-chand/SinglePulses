# GRBs AGENT — SKELETON (freeze candidate v1.1, 2026-08-27)

Named by the PI 2026-08-27: **GRBs Agent**. v1.1 folds in 32 gaps from the
two fresh-agent coverage verifications (register sweep + 12-incident replay).

PI directive (verbatim): "we have to finalize the skeleton of the Agent and
then make it concretely doing things so that it doesn't do unexpected and
buggy things again and again." This file IS that skeleton: every state a
burst can be in, every transition, and — the part that kills the surprises —
every FAILURE CLASS with its declared behavior. Nothing here is advisory;
after PI approval this freezes and the campaign runs it.

## 1. The per-burst state machine

A burst is ALWAYS in exactly one state, recorded machine-readably in
results/campaign/burst_state/<trig>.json {state, since_utc, evidence, holds}.
No implicit states: "I think it ran" is not a state.

| # | state | entered when | evidence required |
|---|---|---|---|
| S0 | REGISTERED | in the approved catalog | background_intervals.ecsv row |
| S1 | STAGE1_APPROVED | detectors+bkg+source stamped | human_gui/AI stamp + WINDOW_SOURCE |
| S2 | BINNED | block table exists | bb_blocks_spectral ecsv |
| S3 | FIT | 24-model table complete | spectral_fits.ecsv, 24-model census assert |
| S4 | RETRIED | mandated retry terminal (NR-6/no-model-dropped) | retry artifact/log in CONTRACT layout |
| S5 | PROMOTED | hash-bound receipt, HASH-CURRENT (NR-22) | promotion_receipts/<fingerprint>.json |
| S6 | TEMPORAL_DONE | P2 six phases receipted | p2_temporal_summary.json |
| S7 | PRODUCTS_DONE | SED grids + montages + evolution rendered | sweep_status + montage census |
| S8 | ASSEMBLED | paper compiled at THE campaign commit (R1) | staging_manifest.json + PDF |
| S9 | GATED | figure-verifier + numbers-verifier + NR-24 pass | sha-bound verdicts in VISION_QC.md |
| S10 | PRESENTED | live report carries the step w/ evidence | APPROVALS.json PRESENTED stamp |
| S11 | APPROVED | PI (or independent approver) stamp | APPROVALS.json APPROVED + identity |
| S12 | BUNDLED | in a released bundle w/ R5 manifest row | release manifest |
| SX | STRUCTURAL_EXCLUSION | a structural refusal blocks the path | labeled reason (e.g. RESPONSE_UNCOVERED) |

Transitions run ONLY through their workflow (§3). A workflow refuses to run
if the burst is not in its entry state. Skipping states is impossible, not
forbidden (P8: code > protocol).

THE MACHINE IS NOT MONOTONIC. On invalidation (NR-19: upstream approval
change, or an F-SILENT discovery) a burst DEMOTES to the last state whose
evidence is still hash-current; wf-invalidate wraps
dev/invalidate_downstream.py, records the demotion + reason in
burst_state/<trig>.json, and re-queues. S4's mandate is NEVER vacuous-dead:
wf-retry always runs, and "zero FAIL cells" is itself a first-class evidence
artifact (the census), so the majority path has a real terminal.
CROSS-BURST STATE: bundles, releases, and campaign accumulators have ONE
campaign-level state object owned by the queue manager — a release declares
its intended member roster and gates on every member's state (kills the
shipped-reports-while-papers-sat-unbundled class).

## 2. The failure taxonomy — the anti-surprise core

Every failure in this campaign belonged to one of FOUR classes. The skeleton
declares the class AND the behavior; a failure outside the taxonomy HALTS the
burst and pages the operator — never improvise.

| class | definition | declared behavior | this week's instances |
|---|---|---|---|
| F-TRANSIENT | environment pressure; retry succeeds later | HOLD + RESUME: job parks, re-admits when the watchdog clears; NEVER self-terminate | swap-spike killed every waiting chain + the retry pool (queue drained silently) |
| F-STRUCTURAL | the data/estimator genuinely cannot produce the value | LABEL + CONTINUE: first-class refusal rides the products; absence always reasoned | CWT no-finite-minimum (3/25); RESPONSE_UNCOVERED; LLE row nan |
| F-CONTRACT | a producer violated a standing contract | STOP THE BURST + register row, same session | retry-layout mismatch; 24-model census break (NR-8); stale generator (R1) |
| F-ORDER | work arrived out of declared sequence | WAIT, not fail: queue-order guard blocks and the queue manager reorders | assembler queue-order guard on bn081224887 |

| F-SILENT | invalid/stale/wrong evidence discovered AFTER acceptance (the register's dominant born-from class: hidden ties, seed non-propagation, stale panels, md-only "success", report/figure source split) | DEMOTE + CASCADE (NR-19) + a new guard that converts this instance to a LOUD class forever | NR-1/2/3/4/7/10/14/16/22/23; L26; the lag re-derivation |
| F-GUARD | the CHECKING machinery itself is wrong | fix at the primitive; RE-RUN every gate it adjudicated; never patch the producer to satisfy a broken guard | NR-13 false HOLD; stale-contract false-FAILs (vision rounds 11/13) |

Rule of the taxonomy: an ERROR MESSAGE is never a behavior. The behavior is
HOLD, LABEL, STOP, WAIT, DEMOTE, or FIX-THE-GUARD — chosen by class.
CLASSIFICATION AUTHORITY: the queue manager (advised by the dispatcher) is
the SOLE classifier; workflow-internal validators emit TYPED refusals, never
bare errors. EVERY class's behavior ends the same way: ... then DISTILL —
prior-art-reader sweeps the family notes first, the distiller closes the
incident into a lesson at the correct layer + a register row, same session.
The RAM clause is machine-wide: ANY process expected to exceed 1 GB holds a
ram_slots claim — notebooks included (they were in the 140 GB mix).

## 3. The workflow set (.claude/workflows/) — one per transition

Each transition S(n)→S(n+1) = one saved workflow file, deterministic,
resumable, arbiter-budgeted (NR-12: GB claims from measured RSS), invoking
the roster as typed stages: skill-reader (open) → producers → verifiers →
stamps. The dispatcher (NR-17) selects workflows; the P9 hook blocks bare
producer launches. My ad hoc shell chains (paper_chain.sh & co.) are the
PROTOTYPES; they retire when their workflow lands.

EVERY producer stage's required evidence includes a PROVENANCE SIDECAR
(argv + env + input hashes + script sha — NR-7); a product without one is
F-SILENT by definition.

wf-bin(S1→S2: 27b, arbiter-budgeted) ·
wf-fit(S2→S3: CHECKPOINT CONTRACT — append-only per-block partials + atomic
finalize, resume keyed on block hash; kills the 12.75h-loss class and unlocks
bn160625945; admission-gate screens every row; code guards NR-1/NR-9 + the
NR-10 name authority bind here) ·
wf-retry(S3→S4: always terminal, zero-FAILs census counts) ·
wf-promote(S4→S5: hash-CURRENT, never existence — NR-22) ·
wf-temporal(S5→S6: 16 GB claim; seed-auditor on every MC product;
admission-gate on catalog rows) ·
wf-products(S6→S7: seed-auditor, tie-reporter, notes-reviewers fan-out per
SpectralResidualReview.md) ·
wf-assemble(S7→S8: queue-ordered; NR-23 same-source; LITERATURE stage with
freeze-before-read as a stage precondition) ·
wf-gate(S8→S9: figure-verifier + numbers-verifier + NR-24 conformance) ·
wf-present(S9→S10: the armed sha-hook — only VISION_QC-ledgered figures can
reach the PI; live report stamps) ·
wf-bundle(S11→S12: R5 manifest + NR-16 absence-fails + EXTERNAL AUDIT
checkpoint before any release; campaign-level state object gates the roster) ·
wf-invalidate(any Sn → last hash-current state; NR-19).

## 4. The queue manager — one loop instead of N racing scripts

ONE process owns campaign sequencing: reads all burst states, picks the next
legal transition per queue order, runs its workflow, writes the new state.
Holds (F-TRANSIENT) live in the state file, not in dying processes. The
16 GB temporal claim serializes THROUGH the manager, not through racing
ram_admit loops. Kill -9 the manager: states are on disk; restart resumes.

## 4b. Session hygiene (Mode B ops — adopted 2026-08-30, context-engineering talk)

- **The smart zone.** Quality degrades well before the context window fills
  (~40% utilization is a working heuristic). Fan-outs return SUMMARIES, never
  transcripts; heavy reading happens in subagents; the driving session stays
  lean. Subagents exist for CONTEXT CONTROL — in our roster their names
  encode CONTRACTS (what evidence they may see), not personas; the fresh
  context is the mechanism, independence is the purpose.
- **Trajectory hygiene.** A thread that accumulates failure-scolding predicts
  more failure ("I did wrong, was corrected, did wrong…"). After repeated
  FAIL rounds on one artifact, restart the PRODUCER from a compacted state
  (the findings list, not the argument history). Verifiers already get
  evidence-only for this reason.
- **Status is derived, never stored as prose.** Static status text rots into
  F-SILENT bait — the "8 DECISIVE" REVIEW_INDEX line contradicting the table
  and the stale dispatch-plan git claims were both this class. The board
  (dev/agent_state.py) derives from disk on demand; any status sentence in a
  document is a cache, and caches carry staleness risk the reader cannot see.
  LAW files (skills, contracts) are the exception: maintained, distiller-
  disciplined, read end-to-end.

## 5. What stays human
Stage-1 approvals; APPROVED stamps; contract amendments (PI's quoted words);
the freeze itself. Everything else is the machine's, through the skeleton.

## 6. Freeze procedure
PI approves this file → states backfilled for all 106 from existing evidence
→ workflows land one at a time, each validated by re-deriving a known burst
→ chains retire → register rows become workflow stages → amendments only by
PI-approved change to THIS file. Any CODE PORT enters the frozen pipeline
only through the port-verifier (numeric equivalence vs the source's CODE on
a synthetic case — L26); any root-cause/redo starts with the
prior-art-reader sweep. External audit (Codex/cloud review) is a standing
milestone hook: advisory, adjudicated at the primitive.

## 7. The 3-day build (PI, 2026-08-27: "We have 3 days to finalize it; build it strong")

DAY 1 (2026-08-27): skeleton verified (fresh-agent coverage vs register +
12 incidents) and PI-APPROVED; state backfill for all 106 bursts from disk
evidence (dev/agent_state.py -> results/campaign/burst_state/); queue manager
v1 with the four failure behaviors (HOLD/LABEL/STOP/WAIT) — kill-9-able,
resumes from state files.
DAY 2 (2026-08-28): workflows land in dependency order — wf-gate first (the
three verifiers; papers are arriving), then wf-assemble, wf-temporal,
wf-promote, wf-retry; the 14-paper recovery COMPLETES THROUGH the skeleton
(its own validation run); ad hoc chains retire.
DAY 3 (2026-08-29): strength pass — kill-tests on the manager mid-transition;
F-TRANSIENT hold/resume demonstrated under an induced memory spike; engineer
onboarding doc from this file + the register backlog; bundle rebuilt with R5
manifest; commit + PR; design page synced to the frozen skeleton.
Definition of DONE: a fresh session (or the engineer) runs one burst
S2->S12 with ZERO improvised decisions — every failure lands in a declared
class, every product is gated, every stamp is real.

## 8. Deployment modes (PI, 2026-08-28)

PI ruling (after the community-structure paper completes): GRBs Agent ships in
TWO modes over ONE skeleton —

**Mode A — API-coded agents.** The roster is code: agents implemented on the
model API (Claude Agent SDK), entering workflows either dynamically
(dispatcher-selected) or hardcoded (frozen wf-* set). Deterministic,
deployable, per-token billing; the queue manager IS the application.

**Mode B — subscription harness.** A subscription AI coding harness (today:
Claude Code) acts as the harness and PLAYS the agents: the .claude/agents/*
definitions, hooks, and skills are consumed natively; humans gate in-session.
This is the mode the discovery campaign runs in.

INVARIANT that makes both possible: everything that defines the agent —
skills, contracts, registers, state machine, failure taxonomy, verifier
definitions (markdown-as-system-prompt), hooks — is TEXT AND CODE IN THE
REPO, never harness state. A mode is an execution substrate, not a fork of
the design; the same burst must reach S12 with the same gates in either.
Mode A tool contracts are STRICTER than function-calling schemas (adopted
2026-08-29, 3rd external review): every tool declares input/output schema,
units, determinism, seed_behavior, side_effect_class (read-only -> sandboxed
compute -> durable internal write -> external write -> costly action),
known_failure_modes, and typed errors — never vague text. The dispatcher's
artifact classes map onto this autonomy ladder; authorization strengthens
left to right.
Mode A CLAIM-EVIDENCE GRAPH (design ruling 2026-08-30): the claim graph is
a KNOWLEDGE GRAPH, not a graph DATABASE — a typed semantic layer (claims,
artifacts, runs, sources; edges = derived-from / verified-by / cites) built
as views OVER the existing storage (sidecars, receipts, VISION_QC ledgers,
git), never a second copy of the data in a graph engine. Zero-ETL: the
files stay canonical; the graph is schema-on-read. This keeps R1/NR-22
provenance in ONE place and avoids the pipeline-maintenance tax of a
duplicated store. If traversal ever needs speed, layer a query engine over
the same files — do not migrate the truth into it.
Mode A LOOP DISCIPLINE (adopted 2026-08-30, CCA field-guide talk): the agent
loop must BRANCH ON stop_reason — the model never executes tools, it only
returns parameters your code runs; and a max_tokens stop means the answer in
hand is PARTIAL (an F-SILENT vector: confident, truncated, wrong) — it must
be treated as a typed failure, never consumed. Mode A ECONOMICS: the Batches
API runs latency-tolerant work at ~50% token cost (24 h window) — verifier
sweeps, notes-reviewer fan-outs, retro-gating are batch-shaped; interactive
gates are not. Price both paths in the queue manager.
Mode A REQUIRES sandboxed execution (container/isolated env) — it runs
generated code outside the harness's permission model (adopted 2026-08-29).
Mode A is the natural Zenodo/community artifact; Mode B is the natural
PI-supervised research instrument. The engineer's build target is Mode A's
queue manager + workflow set; the campaign keeps validating the design in
Mode B meanwhile.

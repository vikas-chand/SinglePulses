# GRBs AGENT — THE COMPLETE ACTOR ROSTER (freeze-review spec, 2026-08-29)

Purpose: the PI's discussion document for finalizing every actor in the GRBs
Agent — role, tools, creations, position, enforcement, deployment modes,
honest limits, and the open decisions. Written to be discussed OUTSIDE this
project's sessions (e.g., with ChatGPT or a fresh Claude): §0 is the context
capsule an external reader needs. SKIP NOTHING was the instruction; nothing
is skipped. Companion files: AgentSkeleton.md (state machine + failure
taxonomy), AgentArchitecture.md (register, 34 rows), ReportSpec.md (R1–R5).

STANDING RULE for external feedback (feedback_absorb_chatgpt_packages_critically):
suggestions from outside chats are ADVISORY — verify against this repo,
accept/park/reject by judgment, never adopt their proposed root instruction
files, and wire accepted ideas into the EXISTING authority files above.

---

## §0 CONTEXT CAPSULE (for readers with no project context)

GRBs Agent is an AI analysis agent for gamma-ray bursts built on one
experimentally-earned axiom: **an actor must never verify its own work.**
It runs a 13-step gated pipeline per burst (state machine S0→S12 +
structural-exclusion SX; states are evidence-backed files on disk, demotion
is mechanical). Every failure lands in one of SIX declared classes
(F-TRANSIENT hold/resume · F-STRUCTURAL label/continue · F-CONTRACT stop +
register row · F-ORDER wait · F-SILENT demote + make-loud-forever ·
F-GUARD fix checker, re-run its gates); an error message is never a
behavior. A requirements register (34 rows, NR-1..NR-24 + unnumbered) grew
one row per real caught failure; principles P1–P9 govern (P8: prose is the
weakest enforcement layer — code > hook > artifact > agent > prose; P9:
running the machinery without the roster is a defect). Two deployment modes
share one repo-defined agent: Mode A (API-coded agents; the queue manager is
the application) and Mode B (a subscription AI-coding harness plays the
agents; humans gate in-session — the mode the discovery campaign runs in).
The humans: the PI holds Stage-1 approvals, APPROVED stamps, contract
amendments (his quoted words only), lesson acceptance, and the freeze.

Actor template used throughout: One sentence · Position · Job (specific) ·
Tools (current → proposed) · May create · Enforcement around it · Mode A/B ·
Honest limits · DECISIONS ON THE TABLE.

Execution order of this document = boot order, then pipeline order, then
the incident path, then oversight, then the orchestrator.

---

## A1. SKILL-READER — first actor of any session and of every step

**One sentence:** makes the system read its own book before touching
anything — converts the accumulated written law (skills, ledgers,
contracts) into a binding checklist parameterized to THIS burst.

**Position:** Layer 0 position one; re-invoked at every step open. Law
before staffing: it determines *under what rules* work happens before the
dispatcher decides *who* works. Born from P8 and the s02c-defaults incident
(constants tuned to one burst's pulse width silently applied to another)
and the hand-re-derived step-1 incident (protocol ignored under momentum).

**Job:**
- Reads the step's owning skill file END-TO-END (Temporal.md for step 7;
  SpectralFitting.md + FigureVisionQC.md for steps 6/8; BurstWalkthrough.md
  for gates; detector_selection.md / background_selection.md /
  source_selection.md for Stage-1; ReportSpec.md for assembly/gate steps).
- Reads the defect ledgers (L-series L1..L30+, temporal LAG ledger) and the
  burst's own VISION_QC.md history.
- Sweeps the register's OPEN rows against THIS burst's configuration:
  detector count (multi-NaI EAC asserts?), redshift (rest-frame layer?),
  block count, pulse width (lag-window scaling), structural exclusions.
- Emits the BINDING CHECKLIST: caveats that ride every number, estimator
  labels, parameter-scaling rules, matching open debts.
- Never runs analysis, never produces artifacts, never legislates.

**Tools:** current Read, Grep, Glob, Bash → PROPOSED: strip Bash (a reader
that can execute can drift into producing). Read/Grep/Glob suffice.

**May create:** nothing today. PROPOSED addition: a CONFLICT flag to the
distiller when two skill files disagree (the 60°-rule caption vs the real
≤50°/BCAT rule was this class) — reading the law includes noticing the law
disagreeing with itself.

**Enforcement:** the roster's weakest — invocation rests on protocol
(session-open ritual + dispatch plans listing it first). Mode A closes it
structurally (stage 1 of every workflow IS a skill-reader call). Mode B:
socially enforced, audited after the fact by wf-gate.

**Mode A:** first typed stage of every wf-*; checklist becomes a structured
object producers must acknowledge item-by-item. **Mode B:** agent invoked at
step opens; checklist pastes into working context.

**Honest limits:** (1) checklist compliance unverified downstream — closing
option: wf-gate verifies each checklist item's trace in the products;
(2) end-to-end reading is expensive every step — deliberate (skimming is
how lessons die), but a cheaper repeat-tier is possible; (3) it reads only
what exists — its guarantee is bounded by the distiller's upstream
discipline.

**DECISIONS:** (a) strip Bash? (b) CONFLICT-flag duty? (c) wf-gate
checklist-compliance verification? (d) accept protocol-enforcement in Mode
B / structural in Mode A?

---

## A2. DISPATCHER — the intake officer (NR-17)

**One sentence:** given any task, decides WHO must run, in what order, with
what gates — and never does the work itself.

**Position:** Layer 0 position two, after the skill-reader, before any
producer. The hinge between "a task exists" and "work begins". Born from
P9's founding incident: the paper-recovery run executed without the roster
(2026-08-26, PI: "it should have respect for the design").

**Job:**
- Consumes: the task description; AgentArchitecture.md (per-step roster +
  full register); the task's owning skill file.
- Classifies the task's ARTIFACT CLASSES: figures / numbers / catalog
  writes / code ports / stochastic (MC) products / heavy compute / redos /
  external claims.
- Maps classes → binding agents: figures→figure-verifier (no exceptions);
  numbers→numbers-verifier; catalog write→admission-gate;
  port→port-verifier; MC→seed-auditor; model selection→tie-reporter;
  redo/root-cause→prior-art-reader; heavy compute→RAM-arbiter sizing from
  measured RSS; every step→skill-reader first, approver gate last.
- Emits the DISPATCH PLAN: ordered {agent, purpose, gate position, evidence
  it must receive} + UNGUARDED DEBT (register rows matching the task whose
  status is still PROPOSED — named before work starts).
- Structurally refuses any plan in which a producer approves itself.

**Tools:** current Read, Grep, Glob, Bash → PROPOSED: strip Bash (planner
must not be able to produce; flagged independently by the external audit).

**May create:** dispatch plans (results/campaign/DISPATCH_PLAN_*.md).
PROPOSED addition: CANDIDATE REGISTER ROWS when a task matches no existing
row — the forward-looking half of the register (dispatcher spots missing
guards before failures; distiller after).

**Enforcement:** the P9 dispatch hook (.claude/hooks/require_dispatch.py,
ARMED): pipeline producers are mechanically BLOCKED from launching without
a fresh (<24 h) plan on disk. Smoke-tested on pass/block/benign paths.

**Mode A:** becomes the queue manager's planning function — same prompt +
register, called before each workflow; "hardcoded workflows" = its output
pinned for the frozen 13 transitions. **Mode B:** agent invocation, hook-
enforced existence.

**Honest limits:** (1) plan-COMPLIANCE unenforced — hook checks existence,
not obedience; Mode A closes structurally (manager launches agents FROM the
plan); Mode B interim: wf-gate cross-checks agents-that-ran vs plan;
(2) the 24 h freshness window is arbitrary — alternative: bind plan to a
task-id; (3) unguarded debt is surfaced, not blocking — probably correct
(else PROPOSED rows freeze all work) but a policy call: should some debt
classes hard-block (e.g., missing seed-audit on an MC product)?
(4) [2026-08-30, NR-35] a plan's per-burst FAIL/exposure list must be
DERIVED from that burst's fit table at plan time, never pooled across the
bursts in the plan — DISPATCH_PLAN_campaign21plus.md scoped NR-10 exposure
to "DSBPLF / BANDRCPL / SBPLCPL / CPLCPL", a #21∪#22 union; #21's actual
FAIL families are DSBPL/DSBPLF/BANDRCPL and SBPLCPL is its T_INT winner.

**DECISIONS:** (a) strip Bash? (b) candidate-register-row drafting?
(c) adopt plan-compliance-via-queue-manager as the Mode A design?
(d) any hard-blocking debt classes?

---

## A3. THE MECHANICAL ENFORCERS (not LLM agents; armed at boot, act always)

**One sentence:** the layer that has never broken — code that makes
violations impossible rather than forbidden.

**E1 — the NO-SHIP HOOK** (.claude/hooks/no_unverified_figures.py, ARMED,
PreToolUse on file delivery): blocks delivery of any .png whose sha256
appears in no VISION_QC ledger. Scope: .png only (PDFs carry their own
trail) — the scope ruling is PI-open (widen to all figure formats?).
KNOWN GAP (external audit): GitHub releases / bundles are a delivery path
OUTSIDE this hook — the bundle path rests on the wf-bundle audit checkpoint
and the PI gate. DECISION: accept procedural coverage there, or build a
release-side hook?

**E2 — the DISPATCH HOOK** (require_dispatch.py, ARMED): see A2.

**E3 — the RAM ARBITER** (dev/ram_slots.sh + ram_watchdog.sh): machine-wide
admission of heavy jobs in GB against MEASURED peak RSS (fit 0.9 · SED 0.5 ·
temporal 0.4 · CWT 3.7 · Bala MVT ~15 GB/burst), fixed shared slot names so
mkdir is a true mutex, owner-PID self-healing reaping (survives SIGKILL —
verified by killing it), HOLD brake, swap-abort. Born from the real 140 GB /
64 GB shutdown that cost 12.75 h of fits. Hardened by an external
multi-agent review (2 real bugs + 1 broken invariant found and fixed) and
by kill-testing (which found a deeper flaw the review missed: zsh defers
signal traps; SIGKILL runs none). KNOWN GAPS: PID-reuse hardening and a
tracked concurrency regression harness (engineer backlog); abort-vs-resume
semantics for waiting jobs (the 06:00 swap spike made every WAITING job
self-terminate and silently drained the queue — the skeleton's F-TRANSIENT
now declares hold+resume; the arbiter's waiters need that retrofit).
DECISION: approve the F-TRANSIENT retrofit (waiters hold under the HOLD
brake instead of aborting)?

---

## A4. ADMISSION-GATE (NR-4) — no unsanitized row enters a catalog

**One sentence:** screens every row before it lands in a committed catalog;
refuses with a reason; a refused row never rides in as silent NaN.

**Position:** inside wf-fit (engine output rows), wf-promote (hash-bound
promotion — paired with NR-22 hash-currency: promotion must compare
provenance hashes, never no-op on existence), wf-temporal (temporal catalog
rows). Born from bn130310840's bad row sitting committed for weeks, and the
literal-nan rows that reached three shipped reports.

**Job (specific):** type/range screens (finite where required, errors
positive, err≤value where the estimator guarantees it, units per column
spec); identity screens (trigger in master sample, no duplicate key,
estimator label present); cross-field sanity (T90>0, MVT<T90, |lag|<T90,
kT inside the fitted band); verdict ADMIT(n)/REFUSE(rows+reasons); never
edits values — refusal routes to the producer.

**Tools:** Read, Grep, Glob, Bash (Bash JUSTIFIED here: it recomputes
screens with astropy). Carries the fresh-context/non-producer precondition.

**May create:** refusal reports; nothing else.

**Enforcement:** invoked by workflows at write-stages; Mode A hardcodes it
as the stamp-stage precondition of wf-fit/wf-temporal/wf-promote.

**Honest limits:** screens are enumerated, not exhaustive — new column
classes need new screens (distiller wires them in); it validates rows, not
scientific correctness (that is the verifiers' job).

**DECISIONS:** (a) screen list sign-off; (b) should REFUSE hard-stop the
workflow (F-CONTRACT) or label-and-continue (F-STRUCTURAL)? Current design:
producer-side refusal = STOP for engine rows, LABEL for estimator refusals.

---

## A5. SEED-AUDITOR (NR-2) — stochastic products must be replayable

**One sentence:** verifies every Monte-Carlo product records AND honors a
seed — a rerun must reproduce bit-identically; a recorded-but-unused seed is
"deceptive provenance", the worst verdict.

**Position:** wf-temporal (T90/T50 MC, CWT 10k sims, Bala runner) and
wf-products (SED band draws). Born from the temporal-MC wobble and the Bala
--seed non-propagation catch.

**Job:** find the seed in the sidecar (missing = FAIL, full stop); trace it
into the code path — is it consumed by EVERY RNG (numpy, python random,
subprocess workers)?; where cheap, rerun the smallest stochastic unit twice
and diff; verdict SEEDED-REPRODUCIBLE or FAIL at the exact break point.

**Tools:** Read, Grep, Glob, Bash (justified: reruns the smallest unit).
Fresh-context/non-producer precondition attached.

**May create:** audit verdicts only.

**Mode A:** typed verifier stage after each MC producer. **Mode B:** agent
invocation per dispatch plan.

**Honest limits:** "smallest unit rerun" is a spot-check, not a proof over
the full product; deep nondeterminism (thread scheduling in 3ML) can pass a
unit and fail a full run — full-product replays are milestone-level, not
per-run.

**DECISIONS:** (a) is the spot-check tier acceptable per-run with full
replays at milestones? (b) seed policy for NEW estimators (mandatory sidecar
field name)?

---

## A6. TIE-REPORTER (NR-3) — preference is not argmin

**One sentence:** enforces that ΔAIC<2 heads are reported as TIE SETS,
never single winners, and that preference language tracks the PI's rule
(TRACKED = winner by ΔAIC>6 in ≥1–2 bins; feature-level census variant
computed alongside).

**Position:** wf-products (winners tables, montage labels, evolution figs)
and via NR-24 in wf-gate (tie language in assembled papers). Born from bin8:
ΔAIC<1 "winners" hiding an order-of-magnitude 30-MeV flux spread.

**Job:** recompute ΔAIC heads from the run's stored table (never refit);
every bin with ΔAIC<2 → name the tie set; physical quantities quoted from a
tie carry the across-tie spread; flag every superlative attached to a tie;
verdict TIE-CLEAN or list {bin, tie set, offending claim, rewording}.
The thresholds are the PI's, never the agent's.
Companion tool it drives: dev/model_preference.py →
results/campaign/model_preference.ecsv (the TRACKED census; PI decision
pending: literal runner-up margin vs feature-level margin as THE census
statement — current recommendation: feature-level for census, literal for
model attribution).

**Tools:** Read, Grep, Glob, Bash (justified: recomputes from tables).

**Honest limits:** operates on stored AICs — inherits any engine-side AIC
bug (that class is guarded by code screens + external audit, not by this
agent); model-FAMILY grouping requires the name-canon authority (NR-10,
alias map interim).

**DECISIONS:** (a) literal vs feature-level TRACKED for the census;
(b) the ΔAIC∈[2,6) middle band's reporting language (currently plain number,
no status word).

---

## A7. NOTES-REVIEWERS (fan-out) — per-bin scientific commentary

**One sentence:** a fan-out of fresh reviewers, one per time-bin/product
set, writing residual/adequacy commentary and escalating defects — the
layer that found the edge-blackbody census and the tie-hidden spread.

**Position:** wf-products (steps 6/8 product sets). Contract:
SpectralResidualReview.md. NOT a single agent file — a workflow PATTERN
(N fresh contexts, one per bin) whose outputs feed the report's per-bin
notes and the science accumulators.

**Job:** per bin: residual structure by band, model adequacy, cross-model
consistency, defect escalation (anything smelling of F-SILENT goes to the
distiller). Adversarial stance: look for what the fit hides.

**Tools (per reviewer):** Read + the bin's own products; no cross-bin state
(independence is the point — agreeing reviewers who shared context count
once, per the independence-at-the-primitive doctrine).

**Honest limits:** commentary quality varies with bin S/N; escalation
discipline depends on prompt fidelity — the pattern is only as adversarial
as its brief.

**DECISIONS:** (a) freeze the per-bin brief text as a contract file?
(b) reviewer count cap for very-many-bin bursts (150-block class)?

---

## A8. FIGURE-VERIFIER — the vision gate (deployed longest, most catches)

**One sentence:** fresh-context vision inspection of EVERY figure against
the standing product contract before the PI ever sees it — the single
largest catch channel in the discovery run (~55 catches).

**Position:** wf-gate (papers) and every figure-producing step; verdicts
sha256-bound in the burst's VISION_QC.md; the no-ship hook then makes an
unledgered figure undeliverable. Contract: FigureVisionQC.md S-items
(the PI's quoted rulings, e.g. S1 error-band policy "WARN AND DRAW") +
G-items for third-party figures.

**Job:** load the PNG, check against EVERY standing contract item (bands,
labels, units, blocks-as-bars, σ-units, pixel collisions NR-5, tofu,
occlusion, on-figure numbers bound to same-run sidecars per
gate-verifies-PI-spec); verdict PASS / PASS-w-nits / FAIL with the exact
defect; NEVER verify a figure it produced (fresh context mandatory).

**Tools:** Read (vision), Grep, Glob, Bash (sidecar cross-checks).

**May create:** VISION_QC ledger entries (sha-bound verdicts) only.

**Honest limits:** contract-bound — it catches violations of WRITTEN
S-items; a defect class with no item yet lands on the PI once, then becomes
an item (that loop already ran ~13 rounds on burst 1); vision has pixel
limits (NR-5's descender-graze needed pixel maps).

**DECISIONS:** (a) S-item list sign-off as frozen contract; (b) FAIL
adjudication path when the verifier itself is suspected wrong (F-GUARD:
two stale-contract false-FAILs exist — current protocol: PI adjudicates,
contract updated with his words).

---

## A9. NUMBERS-VERIFIER — every printed number recomputed

**One sentence:** independently recomputes every number a deliverable
prints, from the run's own products — the agent that caught the Table-1
bin transposition in the first paper.

**Position:** wf-gate (assembled papers/reports), plus any numeric artifact
per dispatch plan. Paired rule NR-23: the deliverable must read the SAME
fit table its figures were built from (promoted convention_check), so
report-numbers and figure-numbers cannot fork.

**Job:** parse the deliverable's numbers; recompute each from
spectral_fits/temporal catalog/sidecars; estimator labels present; no raw
nan (em-dash + stated reason only); rounding honesty (the "+6.0 across the
STRONG threshold" class); verdict per number CONFIRMED/NOT with derivation.

**Tools:** Read, Grep, Glob, Bash (recomputation is the job).

**Honest limits:** recomputes from PRODUCTS — if the product itself is
stale (F-SILENT class), it certifies a consistent falsehood; that class is
covered by hash-currency (NR-22) and the state machine, not this agent.

**DECISIONS:** (a) tolerance policy for recomputation (exact vs rounding
band) — propose: exact at printed precision; (b) does it also verify
BUNDLE manifests (currently yes, as the independent manifest pass)?

---

## A10. NR-24 CONFORMANCE GATE — reports alike and top quality

**One sentence:** verifies an assembled deliverable against ReportSpec
R1–R5 — one generator at one commit (manifest-stamped), exemplar structure,
same-source numbers, tie language, gates logged — born from the PI's catch
"you didn't make all reports alike and top quality".

**Position:** wf-gate, third verdict beside figure- and numbers-verifier.
STATUS: the spec exists (ReportSpec.md); the dedicated agent file is the
one roster member NOT YET WRITTEN (dispatched ad hoc as a fresh-context
verifier bound to the spec). Writing it is part of today's freeze.

**Job:** R1 generator+commit check via staging manifest; R2 structure vs
the PI-approved exemplar (bn081125496 paper); R3 numbers discipline
(delegating to A9's verdict); R4 all three gate verdicts sha-bound before
delivery; R5 bundle-completeness manifest with reasoned absences.

**DECISIONS:** (a) approve creating .claude/agents/report-conformance.md
today; (b) the acceptance test stands? (assembler's regenerated burst-1
paper diffed against the hand-built exemplar the PI graded).

---

## A11. LITERATURE AGENT — blind-first harvester + diff attributor

**One sentence:** reads the published record ONLY after our numbers are
frozen, then attributes every mismatch (frame / method / band) before the
word "discrepancy" is permitted — with LITVERIFY adversarial citation
checking (the pattern that forced retraction of two of our own criticisms).

**Position:** wf-assemble's literature stage (freeze-before-read is a stage
PRECONDITION); Layer 3 generally (GCN intelligence, ADS harvest with
Scholar as finding-channel-only, prior-art first). Protocol exists
(LiteratureHarvest.md + P3); runs as an agent per burst at step 9;
no dedicated file — candidate for one at freeze.

**Job:** P0 freeze check → harvest (every citation resolved to a bibcode —
hallucinated citations have reached drafts; the Nava 2011 wrong-bibcode
catch is the standing example) → frame-alignment → diff → attribution
{we-wrong: fix engine + test · they-wrong: document with evidence ·
frame-difference: normalization rule} → lesson to skill library.

**DECISIONS:** (a) dedicated agent file at freeze? (b) LITVERIFY quorum
(how many independent checks per load-bearing citation)?

---

## A12. PORT-VERIFIER — code ports are guilty until proven equivalent

**One sentence:** any code port enters the frozen pipeline only after
numeric equivalence against the SOURCE'S CODE on a synthetic case — born
from L26, the lag routine ported from a docstring that carried a sign flip
for weeks.

**Position:** development-time, not pipeline-time: the freeze procedure's
port clause (Skeleton §6). Fresh-context/non-producer precondition attached.

**Job:** locate source CODE (never docstring/paper formula alone); build a
synthetic case with a known answer; run both; require equivalence to stated
tolerance; check sign/units/axis-order/edge conventions explicitly; verdict
PORT-VERIFIED (tolerance + case attached) or PORT-REFUSED (diff attached).

**DECISIONS:** (a) default tolerance; (b) does a PASS expire if the source
upstream changes (propose: yes — re-verify on source-hash change)?

---

## A13. PRIOR-ART-READER — never re-derive what the family already proved

**One sentence:** before any root-cause or redo, sweeps the project
family's notes for existing proofs — born from re-deriving, from scratch,
a lag-sign result the family had proven two weeks earlier.

**Position:** stage 1 of the incident path (before the distiller), and
before any redo per dispatch plan. Sweeps THIS repo (notes/, ledgers,
VISION_QC, reconciliation) AND the family (SinglePulse_Temporal, LATBright,
PulsewiseLag, the handbook).

**Job:** return every existing proof/partial/standing decision touching the
question, each with file+date; verdict ALREADY ANSWERED / PARTIALLY
(what remains) / OPEN.

**DECISIONS:** (a) family scope list frozen as written? (b) strip Bash
(Read/Grep/Glob likely suffice)?

---

## A14. DISTILLER — every incident ends in a lesson at the right layer

**One sentence:** closes EVERY failure — all six classes — into a lesson at
the correct enforcement layer (code > hook > artifact > agent > prose) and
a register row, same session; owns the register.

**Position:** terminal stage of every failure behavior (…then DISTILL);
after every PI catch (a PI catch means an agent was missing — standing
rule); owner of AgentArchitecture's register and the PI_REVIEW_PROTOCOL
routing table (writing→prose rules · figure→contract · result→L-series ·
method→skill+code · process→register).

**Job:** root-cause to the PRIMITIVE (not the symptom); place the lesson at
the STRONGEST layer that can carry it; preserve the PI's verbatim words
when a ruling is involved; same-session or it didn't happen.

**Honest limits:** placement judgment is the craft — a lesson placed in
prose when a code guard was possible will fail again (P8); the register
only grows from CAUGHT failures — the dispatcher's candidate rows (A2) are
the forward-looking complement.

**DECISIONS:** (a) same-session rule mechanically checked (wf-gate refuses
if an incident this burst has no register/lesson entry)? (b) distiller as
the sole register writer (others only draft candidates)?

---

## A15. EXTERNAL AUDITOR — the independent platform, adjudicated

**One sentence:** whole-scope adversarial review by a DIFFERENT AI system
(Codex ultra; cloud multi-agent reviews) at milestones — advisory only,
every finding adjudicated at the primitive before action.

**Position:** milestone hook + wf-bundle checkpoint before any release.
Track record in this project: SED-conventions audit (do-not-sign-off, all
majors adopted); the arbiter review (2 real bugs + broken invariant); the
v3 architecture audit (14 findings, all in-scope fixed, NR-20..23 born).
~27 catches in the discovery-run ledger.

**Job:** briefed via notes/CODEX_BRIEF_* (facts pinned by sha, deliberate
conventions pre-declared so they are not relitigated, output contract
VERDICT/CONFIRMED/DISCREPANCIES/COULD-NOT-VERIFY + the independent-judgment
question that has repeatedly been the most valuable part). Quota is PAID —
probe cheap first, never auto-relaunch (standing rule).

**DECISIONS:** (a) audit cadence for the frozen campaign (per-N-bursts?
per-release?); (b) budget ceiling per audit.

---

## A16. THE APPROVER — the identity question (PENDING, the PI's alone)

**One sentence:** the gate-decision maker at every step — the PI in
walkthrough mode; in fully-AI mode an independent agent/platform that
produced NOTHING in the burst; the identity in fully-AI mode is the one
roster seat only the PI can fill.

**Position:** last position of every step (S10→S11 especially). Rules
already standing: never a producer; stamps identity-bound (a stamp without
identity is rejected by code; test stamps are purged same-session —
fabricated approval is the cardinal sin).
**Clarification pending the PI's word (2026-08-30, I-13):** the gate-1
instruction read "stamping each step PRESENTED via dev/live_report.py --by
VIKAS". In the tool, `--by` on `--present` is the PRESENTER's identity
(live_report.py:136-141: "PRESENTED must carry identity + real evidence");
a stamp bearing an identity that did not act is a fabricated stamp under
the rule above. The session therefore stamps PRESENTED under its own
identity and leaves APPROVED `--by VIKAS` to the PI, reporting the
deviation. Decision sheet item 24.

**DECISIONS (all PI's):** (a) fully-AI approver identity (Codex? fresh
Claude? both-quorum?); (b) which steps may EVER be AI-approved vs
PI-only-forever (proposal: Stage-1 and S11 stay PI-only in the campaign;
fully-AI mode is for the Mode-A replication arm).

---

## A17. THE QUEUE MANAGER — the orchestrator (to be built TODAY)

**One sentence:** the one loop that owns campaign sequencing — reads all
burst states, picks the next legal transition per queue order, runs its
workflow, writes the new state — replacing N racing shell scripts.

**Position:** above the workflows, below the humans. Sole classification
authority for the failure taxonomy (validators emit TYPED refusals; the
manager chooses the behavior: HOLD/LABEL/STOP/WAIT/DEMOTE/FIX-GUARD).
Holds ALL arbiter claims (the 16 GB temporal claim serializes THROUGH the
manager — no more racing ram_admit waiters). Kill -9 safe: states are on
disk; restart resumes (the property whose absence cost the overnight queue).

**Job spec (v1, Mode B):** single python process; scans
results/campaign/burst_state/; a transition table {state → workflow script,
budget, gates}; executes one transition at a time per burst with global
concurrency from the arbiter; on failure classifies + executes the declared
behavior + logs to the live report; HOLD ledger in the state files.

**Honest limits (v1):** workflows initially wrap the existing chain scripts
(prototypes per Skeleton §3) — the typed agent stages land per-workflow as
they are codified; v1's guarantee is sequencing + failure behaviors +
resume, not yet full stage-typing.

**DECISIONS:** (a) approve building v1 today to this spec; (b) queue order
authority (REVIEW_INDEX vs board-derived) — propose REVIEW_INDEX stays
canonical.

---

## A18. SUPPORTING CAST (tools with actor-like duties, for completeness)

- **live report** (dev/live_report.py): per-burst evidence-linked document;
  PRESENTED requires identity+evidence; feedback renders PENDING until
  routed; -O-proof runtime checks; markdown-injection hardened.
- **invalidation cascade** (dev/invalidate_downstream.py): NR-19 demotion;
  dry-run default; markers/stamps only, never products; trig-validated.
- **campaign board** (dev/agent_state.py): evidence-derived states for all
  106; the anti-"I think it ran" instrument.
- **preference census** (dev/model_preference.py): the PI's ΔAIC>6 tracking
  rule, literal + feature-level.
- **RSS sampler / watchdog**: measurement + HOLD-brake instruments.

---

## §CONSOLIDATED DECISION SHEET (everything above, one list for the chat)

1. Bash-stripping: skill-reader, dispatcher, prior-art-reader (keep Bash:
   admission-gate, seed-auditor, tie-reporter, figure/numbers-verifier).
2. Skill-reader CONFLICT-flag duty; checklist-compliance check at wf-gate.
3. Dispatcher candidate-register-rows; plan-compliance via queue manager;
   hard-blocking debt classes (if any); freshness window vs task-id.
4. No-ship hook scope (.png-only vs all formats); release-path hook vs
   procedural coverage.
5. RAM arbiter F-TRANSIENT retrofit (waiters HOLD, never self-terminate).
6. Admission-gate REFUSE semantics (STOP vs LABEL by row class).
7. Seed-auditor spot-check tier per-run + full replay at milestones.
8. Tie census: literal vs feature-level TRACKED; ΔAIC∈[2,6) language.
   → RESOLVED 2026-08-30 (gate 1, Lane-A #21 bn110920546), PI verbatim:
   "ΔAIC reference: BOTH constructs stay, with mandatory labels — "DECISIVE"
   = chain-gate vs best simpler ancestor (structure claims, ΔAIC≥10);
   "TRACKED" = vs runner-up (preference, ΔAIC>6 in 1–2 bins). Never print
   either word without its reference. Fix model_preference.py's validity
   gate before its output is quoted for THIS burst." The feature-level
   margin is NOT addressed by the ruling — it stays a computed-alongside
   diagnostic, never a census construct. Law: SpectralFitting.md PREFERENCE
   section, ReportSpec R3; NR-26 status FIX APPLIED; NR-27 first instance.
9. Notes-reviewers: freeze the per-bin brief; reviewer cap for 100+ bins.
10. Figure-verifier: S-item contract freeze; F-GUARD adjudication path.
11. Numbers-verifier: exact-at-printed-precision tolerance; manifest pass.
12. NR-24: create the agent file today; burst-1 exemplar acceptance test.
13. Literature agent: dedicated file at freeze; LITVERIFY quorum.
14. Port-verifier: default tolerance; PASS expiry on source-hash change.
15. Prior-art-reader: family scope list; Bash strip.
16. Distiller: same-session mechanical check; sole-register-writer rule.
17. External audit cadence + budget for the frozen campaign.
18. APPROVER identity in fully-AI mode; PI-only-forever steps.
19. Queue manager v1 build approval; queue-order authority.
   → DEFERRED 2026-08-30 (gate 1, #21), PI verbatim: "Tooling: prototype
   chains for #21, under the dispatch plan's gates. State so in every
   stamp." No queue-manager build for #21; every #21 stamp states
   "prototype chains under the dispatch plan's gates".
20. The 74-burst retry debt (campaign-wide mandate vs report-bursts-only).
   → RESOLVED 2026-08-30 as PER-WALKED-BURST REPAIR, no campaign-wide sweep.
   PI preamble, verbatim: "one burst at a time, repairs included: each burst
   fixes its own rows as it's walked, no campaign-wide sweeps." and "Gate
   decisions — we work ONE burst at a time; nothing campaign-wide:". For
   #21, verbatim: "Promote the 08-27 retry table (newer, terminal, winners
   identical). Its tier-3 cell list governs downstream." Temporal rows
   likewise (ruling 5, NR-31): each burst regenerates and REPLACES its own
   rows as it is walked; un-walked rows stay STALE-PENDING-REWALK.
21. The 21 never-human-reviewed bursts: census eligibility (open Q4).
22. [NEW 2026-08-30, NR-27 instance I-12] STEP NUMBERING: dev/live_report.py
   STEP_NAMES + AgentArchitecture's per-step roster (0b identity/boot, 0
   inventory, 1 detectors, 2 background, 3 source, 4 binning, 5 stage-1
   adopt) vs BurstWalkthrough.md's ledger + scripts/44 PNG names (0b
   literature, 0 identity/GCN, 1 inventory, 2 detectors, 3 background, 4
   source, 5 binning) — shifted by one for 0b–5, 6–9 agree. Which numbering
   is law? (The distiller picked none.)
   **RESOLVED 2026-08-30 (PI, verbatim):** "The BurstWalkthrough ledger numbering is official: 0b = literature harvest, 0 = identity & GCN, 1 = data inventory, and so on. Fix the live-report tool's step names to match; existing figure filenames keep their names — record the mapping once, do not rename products mid-campaign."
   THE CANONICAL MAPPING RECORD: old live_report keys -> official ledger:
   '0b' identity/boot -> 0b literature harvest (+ 0 identity/GCN, separate);
   '0' inventory -> 1 data inventory; '1' detectors -> 2; '2' background -> 3;
   '3' source -> 4; '4' binning -> 5; '5' stage-1 adopt -> folded into 2–5
   (ADOPT); 6–9 unchanged. scripts/44 PNG names already match the official
   ledger and KEEP their names. live_report.py fixed same day; the one
   pre-ruling stamp ('0b' PRESENTED 05:22:05Z) is identical in meaning.
23. [NEW 2026-08-30, NR-29] PIN LOCATION: ruling 4 ordered a re-pin but no
   designated location existed; results/campaign/CAMPAIGN_COMMIT_PIN.json
   was improvised by the operating session. Bless or relocate.
24. [NEW 2026-08-30, NR-18/A16] `--by` SEMANTICS: on `--present` the tool
   records the PRESENTER; the instruction "stamping each step PRESENTED …
   --by VIKAS" would put the PI's identity on an act he did not perform.
   Session stamps PRESENTED as itself, APPROVED --by VIKAS stays the PI's.
   Confirm or overrule.
25. [NEW 2026-08-31, NR-38 instance I-14] DETECTOR RULE vs YOUR PRACTICE:
   dev/ai_guides/detector_selection.md says "NaI theta <= 50 deg -> KEEP",
   with BCAT membership mattering only in the 50-60 deg rescue band. Measured
   over the 105 human_gui bursts: your kept-NaI set equals the BCAT-TRIGGERED
   set in 82/105 (78%) and the geometry(<=50 deg) set in 50/105 (48%); in
   19/105 you DROPPED a NaI that passes <=50 deg. At the #21 gate your reason
   was, VERBATIM (one line, unedited):
   "I must have selected the ones those are on same side and probaly the triggered ones too"
   — a recollection, stated with uncertainty ("must have", "probaly"), which
   the session verified holds exactly for bn110920546. QUESTION: should
   BCAT membership gate NaI selection BELOW 50 deg too, or is the geometry
   rule right as written and the 19 drops are per-burst visual judgements?
   Until you rule, the written rule STANDS and the divergence is presented,
   not normalized. Benchmark consequence either way: an arm that obeyed the
   written rule is scored as a SPECIFICATION defect, never an arm error.
26. [NEW 2026-08-31, NR-39 instance I-15] RATIONALE CAPTURE: the human GUI
   path writes no `reasoning` at all (scripts/39_approve_all.py:817-819; the
   docstring at :52 calls it "optional free text"), so 1 of 105 human_gui
   decisions carries a reason — and that one was back-filled 6 weeks late.
   Proposed as dev/GUI_REQUIREMENTS.md R-GL-8: the GUI asks for one line at
   decision time and ingest refuses a blank `reasoning`. Approve the
   requirement (it touches the frozen approval instrument, so it is yours to
   allow), and confirm the standing rule that the 104 historical blanks are
   NEVER back-filled.

## ADDENDUM 2026-08-29 — adjudication of the second external review

Their status table accepted with ONE correction: items 5 and 6 were adopted
hours before their read (NR-25 + Mode-A sandbox + critic questions + MET
tests) — "Absent" was stale on arrival. Their five "you have what nobody
has" items (taxonomy+distiller, mechanical enforcement, seed-auditor/
tie-reporter/board, blind-first attribution) are confirmed differentiators
for the paper. ADOPTED from their four leverage items:
- A19 TRUTH-GROUNDING GATE (new actor, spec in NR-25's sharpened row):
  verifiers certify CONSISTENCY, A19 certifies TRUTH — full-engine synthetic
  recovery + published-burst fixtures, at freeze + on engine-hash change.
- Admission-gate FAILURE-TRANSPARENCY SCREENS (boundary-e, width=range,
  pathological stat, undisclosed multimodality) — now in its contract.
- TRUTH METRIC for the agent per release: recovery rate on held-out
  published bursts + self-flagged-pathology rate (extends the catch-ledger,
  which measures verifier ACTIVITY, not pipeline ACCURACY). Feeds A16:
  no fully-AI approver approval without an accuracy number.
- CROSS-MODEL QUORUM at the load-bearing gate (S10->S11 numbers pass,
  Codex or second model) — PENDING PI (Codex quota is paid; cost per burst
  must be priced first). Their A16 read: different-model quorum beats any
  single-model approver.
- Raw-data PreToolUse guard ARMED (.claude/hooks/protect_rawdata.py) as
  minimal Mode-B sandboxing; the real sandbox stays Mode A's.
Their caution accepted verbatim: build the queue manager BEFORE adding
actors — A19 is the LAST actor admitted before freeze.
DECISION SHEET updates: items 1 (strip Bash) and 2 (checklist-compliance at
wf-gate) now carry supporting evidence from both external reviews.

## ADDENDUM 2 (2026-08-29) — third external package (systems-engineering)
Triangulation complete: three independent external designs now converge on
our architecture. Third package's distinctive convergences: "dynamic outside,
deterministic inside" = Mode A dispatcher+frozen workflows; TWO ENGINES
(durable agent state machine + scientific workflow engine) = queue manager +
wf-* — third independent derivation of the §3/§4 split; "failure is allowed
everywhere except in provenance" = our F-taxonomy + NR-7/22 in one sentence.
ADOPTED (terms/fields into existing rows, NO new machinery per the pkg-2
caution): tool-contract fields + autonomy ladder (Skeleton §8); claim typing
+ CLAIM-REPLAY CI test (ReportSpec R3a); clean-room challenge +
reproducibility envelope + property-based tests as A19's acceptance
(register). PARKED for Mode-A engineering: W3C PROV/RO-Crate/Arrow/Nextflow
stack choices (engineer's call); typed claim-evidence GRAPH as the Mode-A
north star (our figure sidecars are the embryo); U_science metric + ablation
studies -> agentic-paper material. REJECTED: nothing (no root-file proposals;
citations as always unverified until ADS).

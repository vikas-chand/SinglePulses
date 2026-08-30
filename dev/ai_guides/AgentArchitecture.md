# Agent Architecture — who acts, who checks, who approves, at every step

**Born 2026-08-15** (Vikas, after the fourth producer-eyes-only shipping violation):
*"there is a lesson there that we have to make this pipeline truly agentic by
customizing it, but truly deciding what every step will have as agents and for
what purpose."* This document is that decision — the deliberate roster, replacing
gates improvised after each failure.

## Design principles (each one paid for by a recorded failure)

P1. **Producer never verifies its own work.** Every artifact is checked by a
    fresh-context agent that did not make it. (ShippingGate.md origin; 4
    producer-eyes-only incidents on 2026-08-14/15 alone.)
P2. **Contracts derive from PI rulings, never from producer intent.** Verifiers
    check the STANDING PRODUCT CONTRACT (FigureVisionQC.md, PI words quoted +
    dated). A producer-authored contract is structurally blind to the producer's
    own wrong decisions (the missing-errorband round).
P3. **Numbers bind to same-run machine-readable sidecars**, never to values a
    producer types into a prompt (two stale-contract false-FAIL rounds).
P4. **No exceptions without the PI's word.** The producer inventing an exemption
    ("third-party figure", "just a caption change") IS the violation
    (NO-EXCEPTION DELIVERY RULE, 2026-08-15).
P5. **Every incident ends in a distilled lesson at the right layer** — code
    guard > standing contract item > skill L-entry > memory — because prose
    rules broke 3× in one day while code rules held.
P6. **External audit at milestones, adjudicated at the primitive** (Codex ultra;
    right about the invalid band, wrong about nothing that survived re-check).
P7. **Understand before running.** A tool import is not a method transfer:
    parameters scale with the burst, ports copy CODE not docstrings (L26 root
    cause), and the operator reads the skill file BEFORE invoking the tool
    (the s02c defaults incident).
P8. **Prose instructions to the ACTOR are the weakest layer and will be ignored
    under momentum** (Vikas, 2026-08-15: "simple instructions in skills files
    will always end up being ignored" — proven 4× in one day while every code
    guard held). The enforcement hierarchy, strongest first: (a) code that
    fails closed; (b) a hook that blocks the action; (c) an artifact that
    carries its own caveats (on-figure disclosures, sidecars); (d) a dedicated
    agent whose ONLY job is the rule — including a SKILL-READER agent that
    opens each step by reading the skill and returning the binding checklist.
    Skill files are the source those agents read, never a runtime constraint
    on the actor. Any rule found living only as actor-prose is a defect: push
    it down the hierarchy.

### P9 — Respect for the design (PI, 2026-08-26, verbatim: "it should have respect for the design")
The running system must BE the designed system. Running the pipeline's machinery
without its roster — no dispatcher at intake, no skill-reader at step opens, no
gates on produced figures, no stamps — is a DEFECT, not a shortcut, even when
the products come out correct. Caught live during the paper-recovery run: the
session executed retries/receipts/P2 under momentum with zero roster
invocations while the agent files sat deployed on disk. Enforcement: dispatcher
at task intake and skill-reader at step opens are MANDATORY protocol for any
pipeline-running session; produced figures/papers are UNGATED-PRODUCER-ARTIFACTS
until their verifiers run; a session that discovers itself mid-run without the
roster invokes it retroactively and says so. P8 named prose-to-actor the weakest
layer; P9 is its consequence for the RUNNER, not just the author.

## The agent roster (cross-cutting)

| agent | single purpose | binding contract | trigger |
|---|---|---|---|
| PRODUCER | build one artifact class; emit provenance sidecar (script sha, inputs, numbers, seeds) | code guards (AIC ≤0.1, EAC asserts, convention guard) | step execution |
| FIGURE VERIFIER | fresh-context vision check of figures vs standing contract (S-items) or third-party G-items; verdict sha256-bound in VISION_QC.md | FigureVisionQC.md | EVERY figure, before the PI sees it — no exceptions |
| NUMBERS VERIFIER | recompute printed/claimed numbers from the run's own products; fail loudly | sidecars + engine tables | any artifact carrying numbers |
| RESIDUAL/NOTES REVIEWERS | per-bin scientific commentary (residual structure by band, model adequacy, defect escalation) | SpectralResidualReview.md | step 6/8 product sets (workflow fan-out) |
| APPROVER | the gate decision. Walkthrough mode: the PI. Fully-AI mode: an independent agent/platform that produced NOTHING in the burst | BurstWalkthrough.md gate-role rule (2026-08-14) | every step gate |
| EXTERNAL AUDITOR | independent whole-scope review (Codex ultra), advisory-only, adjudicated finding-by-finding at the primitive | codex-review skill + brief protocol | milestones / on demand |
| DISTILLER | root-cause each incident to its primitive; write the lesson into the correct layer (P5); amend contracts only with PI wording | SpectralFitting.md L-series, Temporal.md ledger, FigureVisionQC.md | every incident, same session |
| MECHANICAL ENFORCER | hooks that make violations impossible rather than forbidden: PreToolUse on SendUserFile blocks any figure whose sha256 is not in a VISION_QC ledger | settings.json hook | **PENDING the PI's go** — the only layer that has never broken |

## Per-step roster (walkthrough ledger 0b, 0, 1–9)

- **0b/0 (identity, inventory):** producer = session (reads REPORT/PRODUCTS
  first — never re-derives); approver = PI. No figures, no verifier.
- **1 (detector/BCAT):** producer scripts/44 step-1 panel; FIGURE VERIFIER;
  NUMBERS VERIFIER vs grb_sample.ecsv (the BCAT mask lives there — the false
  "not checkable" claim class); approver = PI.
- **2–5 (Stage-1, ADOPT mode):** PRESENTER only — the PI's recorded human_gui
  decisions are presented, never re-adjudicated. Flags in
  human_review_qc_flags.txt ARE decisions. Approver = PI.
- **6 (spectral fits):** producer = engine (scripts/10 via 29); artifact
  verifiers = AIC/validity guards in code; presentation figures gate as step 8.
  Approver = PI.
- **7 (temporal):** producer = scripts/46→40 engine + 44/47b/47c figures.
  MANDATORY pre-step: the presenter reads Temporal.md's defect ledger and the
  banner — every quoted number carries its estimator label and ledger caveats
  (MVT: Bala canonical / Haar / CWT, each named; lag: convention + L26 status;
  T90: windowed lower limit, L29). FIGURE + NUMBERS verifiers; approver = PI.
- **8 (products):** producers 41c/41d/41e + tables + montages; every figure
  through the FIGURE VERIFIER; NOTES REVIEWERS fan out per bin (workflow);
  BEST_FITS/REFUSALS ledgers enumerate everything not rendered — absence is
  always labeled, never silent. Approver = PI.
- **9 (report, literature, distill):** producer 48/45 report rebuild; LITERATURE
  agent runs blind-first (products frozen before reading published values, then
  the P3 diff attributes mismatches); DISTILLER closes the burst's lessons;
  final approver = PI (or independent AI in fully-AI mode) on the assembled
  REPORT — the burst's single deliverable.

## Fully-AI mode (the "truly agentic" target)

Same roster, two substitutions: APPROVER = an independent agent or alternate
platform (never a producer in that burst; Codex or a fresh-context Claude with
only the presented evidence), and the PI receives the finished REPORT plus the
gate trail (VISION_QC.md + approval stamps) instead of per-step questions.
Nothing else changes: the contracts, sidecars, and ledgers are identical in
both modes — that is what makes the mode switch safe.

## AGENT REQUIREMENTS REGISTER (running — "keep noting where we require an agent and its purpose", Vikas 2026-08-15)

Rule: whenever work reveals a missing agent — especially when the PI catches a
defect (feedback: that MEANS an agent was missing) — a row lands here IN THE SAME
SESSION. The DISTILLER owns this register. One purpose per row; a row with two
purposes is two rows.

| where | purpose (single job) | status |
|---|---|---|
| every figure delivery | fresh-context vision verify vs standing contract / G-items, sha-bound verdict | DEPLOYED |
| every numeric artifact | recompute printed numbers from the run's own products | DEPLOYED (code guards + sidecar-bound contract checks) |
| step 6/8 product sets | per-bin residual/adequacy notes + defect escalation | DEPLOYED (workflow fan-out) |
| milestones | external whole-scope audit, advisory, adjudicated at the primitive | DEPLOYED (Codex, on demand) |
| every incident | root-cause to primitive; lesson to correct layer; register upkeep | DEPLOYED (distiller practice) |
| each step opening | SKILL-READER: read the step's skill/ledger, return the binding checklist + parameter-scaling rules for THIS burst (kills the ignored-prose class AND the s02c-defaults class) | DEPLOYED (.claude/agents/skill-reader.md, 2026-08-16) |
| SendUserFile | MECHANICAL ENFORCER: block any figure whose sha256 is not in a VISION_QC ledger | DEPLOYED — hook ARMED in .claude/settings.json (2026-08-16) |
| any code port | PORT-VERIFIER: numeric equivalence vs the SOURCE'S CODE on a synthetic case before the port is trusted (L26: the docstring is a bug vector) | DEPLOYED (.claude/agents/port-verifier.md, 2026-08-21) |
| fully-AI mode gates | APPROVER: independent non-producer (Codex / fresh Claude / both) | IDENTITY PENDING PI |
| step 9 literature | blind-first harvester + P3 diff attributor (frame/method/band before "discrepancy") | DEPLOYED (protocol; agent per burst at step 9) |
| before any root-cause / redo | PRIOR-ART READER: sweep the PROJECT FAMILY's notes (SinglePulse_Temporal, LATBright, PulsewiseLag…) for existing proofs before re-deriving — the lag-sign inversion was PROVEN in LAG_SIGN_VERIFICATION.md (2026-07-31, two-skeptic) and re-derived from scratch on 2026-08-15 | DEPLOYED (.claude/agents/prior-art-reader.md, 2026-08-21) |
| SED band drawing | NR-1 BAND-VALIDITY GUARD: containment + railed-fraction checks before any band ships (landed in 41c 2026-08-15; keep as frozen code) | DEPLOYED |
| any MC product | NR-2 SEED AUDITOR: verify every stochastic product records + honors a seed (caught: temporal MC wobble, Bala runner --seed non-propagation) | DEPLOYED (.claude/agents/seed-auditor.md, 2026-08-21) |
| model-selection reporting | NR-3 TIE-REPORTER: dAIC<2 heads reported as ties, never single winners (bin8's dAIC<1 hides 10x 30-MeV spread) | DEPLOYED (.claude/agents/tie-reporter.md; tracking rule = SpectralFitting.md PREFERENCE section, PI 2026-08-26) |
| catalog writes | NR-4 ADMISSION GATE: no row enters a committed catalog without sanity screens (bn130310840 bad row sat for weeks) | DEPLOYED (.claude/agents/admission-gate.md, 2026-08-21) |
| figure text layout | NR-5 PIXEL-COLLISION CHECK in gates (descender-graze class needed pixel maps to catch) | DEPLOYED (verifier practice) |
| sweep refusals | NR-6 REFUSAL TRIAGE | CLOSED 2026-08-16: superseded by the NO-MODEL-DROPPED rule — three-tier panel provenance (live-verified / frozen replay / structural-refusal-as-bug-report) in 41c; burst-2 = 168/168 panels |
| every producer run | NR-7 INVOCATION RECORDER: every producer stores its full argv + env in the product sidecar (41c does; scripts/29 does NOT — its burst-1 invocation had to be reverse-engineered and the --models flag was misread, costing a partial refit) | PROPOSED (fix queued: argv into 29's sidecar) |
| SED display fits | NR-9 STORED-REF BINDING: display fits read reference_det/fit_dets from the ENGINE sidecar, never recompute (Codex #2 queued 08-14, MATERIALIZED 08-16 on the first multi-NaI burst: 152/168 systematic refusals; fixed in 41c same-session) | DEPLOYED |
| model name mapping | NR-10 NAME-CANON AUTHORITY: prefix<->figure-name mapping read from the ENGINE spec table only (regex canon missed DSBPLfree/SBPLfree/BandxCut/SBPLxCut -> stale panels survived purges AND montages showed phantom-missing cells, burst-2 2026-08-16) | PROPOSED (alias map deployed as interim) |
| engine family merge | NR-8 MERGE-INTEGRITY GUARD: scripts/10's per-family save is ORDER-FRAGILE — the threecomp save dropped previously merged families AND a default-family model (burst-2, 2026-08-15: 976→742 cols, 6 models lost incl DSBPL; burst-1 dodged it by run order). Frozen refit workflow must run families in ONE process or via explicit column-merge, and a post-save model-count assert (==24) must fail loudly | PROPOSED (repair path used: scratch refit + explicit astropy column merge) |
| every heavy launcher | NR-12 RESOURCE ARBITER: concurrency budgeted in GB via one machine-wide semaphore (dev/ram_slots.sh); the 2026-08-17 shutdown was 5 product chains x the 15 GB MVT step + a 16-way fit pool + notebooks, ~140 GB on a 64 GB box, 12.75 h of compute lost | DEPLOYED (PR #1, ultrareview-fixed 2026-08-18) |
| any health monitor | NR-13 METRIC CROSS-CHECK: a gating metric must be validated against an independent measure before it gates anything (macOS `Pages free` read 0.1 GB while memory_pressure said 89% free -> false HOLD, 2026-08-18) | LESSON DEPLOYED in ram_slots/watchdog; general rule PROPOSED |
| any cleanup path | NR-14 CLEANUP-PATH TESTER: cleanup must be verified by KILLING the process, never by reading the code (zsh `trap RETURN` never fired -> claim dirs leaked silently on every burst; found only under test, 2026-08-18) | PRACTICE (proved 2026-08-18); regression test PROPOSED |
| any shared-resource release | NR-15 SELF-HEALING RELEASE: release must survive SIGKILL/shutdown -- traps are deferred by zsh during a foreground child and never run under SIGKILL; slots record owner PID and admission reaps dead owners (ultrareview bug_002 fix was necessary but NOT sufficient) | DEPLOYED (ram_slots.sh reaper, verified under SIGKILL 2026-08-18) |
| every declared product | NR-16 PRODUCT-ABSENCE = STEP FAILURE: a step whose declared product is missing must FAIL, not warn into a log (pandoc off PATH -> 4 md-only reports shipped as success, 2026-08-18) | PROPOSED (PATH fixed; general assert queued for 48 + driver) |
| task intake | NR-17 DISPATCHER: on-the-fly assessment -- read the task + register, return the agent roster and gate plan REQUIRED for this task (PI directive 2026-08-21: dynamic assignment, not static prose) | DEPLOYED; INVOCATION GAP found 2026-08-26 (recovery run started without it -> P9); enforcement = mandatory protocol line, P9 |
| every burst, continuously | NR-18 LIVE REPORT: per-burst live document assembled after every step -- gate status, stamps, evidence links; PI approves/feeds back on the document, feedback routes via distiller, approvals propagate via the invalidation cascade | DEPLOYED (dev/live_report.py + APPROVALS.json, 2026-08-21) |
| any upstream approval change | NR-19 INVALIDATION CASCADE: when an approved step changes, downstream phase markers are cleared and products regenerate -- accommodation is mechanical, not remembered (PI directive 2026-08-21) | DEPLOYED (dev/invalidate_downstream.py, 2026-08-21) |
| every report/paper delivery | NR-24 REPORT-CONFORMANCE GATE: verify the assembled deliverable against dev/ai_guides/ReportSpec.md R1-R5 (one generator+commit, exemplar structure, no raw nan, tie language, gates logged) — born from the PI catch 2026-08-26 'not all reports alike and top quality'; figures had a contract, the deliverable containing them did not | PROPOSED (spec written; gate agent next) |
| any detection/claim pipeline | NR-25 INJECTION-RECOVERY + NULL GATE: before a pipeline's claims are trusted, it must (a) recover a synthetic spectrum/light-curve of known parameters within stated uncertainty and (b) return no spurious signal on background-only intervals — a GATING battery, not a one-off (adopted 2026-08-29 from the external design survey; converges with our planned fault-injection; the seed-poisoning bug is the class it catches) | PROPOSED -> SHARPENED 2026-08-29 (2nd external review): generalize beyond ports to a TRUTH-GROUNDING GATE (A19): synthetic bursts with known Band/CPL/T90/lag/MVT through the FULL engine, recovery within stated tolerance + a fixture set of well-studied published bursts; runs at FREEZE and on every engine-hash change. Verifiers certify consistency; A19 certifies truth at the primitive. Acceptance = CLEAN-ROOM CHALLENGE (destroy workspace, rebuild from the archived object, rerun, compare within the declared REPRODUCIBILITY ENVELOPE — what must stay invariant + tolerance; our |dAIC|<0.1 frozen-replay guard is the existing instance). Formulation = property-based scientific tests (null data -> controlled false-positive rate; known effects -> stated coverage). Engineer backlog. |
| any census/preference tool | NR-26 GATE-BEFORE-ARGMIN: a tool that selects or ranks models MUST apply the engine's own validity columns (*_VALID / *_STATUS / BOUND_CAPPED) before taking an argmin — dev/model_preference.py did not, so results/campaign/model_preference.ecsv (and every figure quoting it) ranked over invalid fits. Found 2026-08-30 by the first fresh session; the figure gate had certified those numbers CONSISTENT with the file, which is exactly the consistency-vs-truth gap A19 exists to close | PROPOSED (fix + rerun before any census quote) |
| any law/skill file set | NR-27 LAW-CONFLICT FLAG: when two binding documents disagree, the skill-reader must raise a CONFLICT rather than pick one (FreshSessionBoot §2 said "don't inherit the dispatch plan" while §6 said "read the existing plan" — the fresh session obeyed one and could not know it had chosen) | PROPOSED (skill-reader duty, A1) |
| approval/cascade tools | NR-20 INPUT-AS-TRUST-BOUNDARY: the trig reaches os paths + a subprocess; validate against a trig grammar and fail loud, never os.system a raw arg (Codex 2026-08-21: a crafted trig turned a "markers only" tool into arbitrary-path removal + command exec) | DEPLOYED (validator in live_report.py + invalidate_downstream.py; os.system->argv) |
| any safety check | NR-21 NO-ASSERT-FOR-SAFETY: a security/authorization check must be a runtime check, never `assert` -- `python -O` strips asserts and the --by guard wrote by:null (Codex 2026-08-21) | DEPLOYED (live_report.py) |
| any doc→product claim | NR-22 SKIP-BY-EXISTENCE IS NOT SKIP-BY-CURRENCY: a marker/PNG/24-model no-op certifies existence, not which inputs it was built from; resume decisions on existence alone leave stale products (Codex 2026-08-21: bn090530760 canonical vs highe tables differ by hash yet promotion no-ops) | PROPOSED (provenance-hash generations) |
| report assembly | NR-23 SAME-SOURCE REPORT+FIGURES: the report must read the SAME fit table the SED products are built from (convention_check promoted), not the nested sweep copy (Codex 2026-08-21) | DEPLOYED (48 reads convention_check first, 2026-08-21) |

## Freeze plan (Vikas, 2026-08-15): discovery through burst #10, then codify

Bursts #1–#10 of the walkthrough are the architecture's DISCOVERY phase: the
register above grows row-by-row as real work reveals real needs; rosters and
contracts iterate as practice. **At burst #10 the register FREEZES and gets
coded**: each row becomes a customized agent definition (fixed role prompt =
its contract, nothing else), wired into the pipeline as code — hooks, skill-
reader stages, workflow templates per step — so bursts #11–#106 run on the
frozen agentic pipeline. After the freeze, changes happen only by PI-approved
amendment with the incident that motivated them attached. The frozen
architecture + its incident-derived register IS methods material for the
agentic paper: the design was discovered under load, not invented on a
whiteboard.

**The end state (Vikas, 2026-08-15): "to create actual AI Agent that can
analyze GRBs."** Not a pipeline with AI bolted on — an agent whose roster is
this document frozen, whose knowledge is the Handbook + skill files (read by
its skill-reader, per P8), whose memory is the ledgers and sidecars, whose
conscience is the gate agents and hooks, and whose accountability is the
sha-bound trail a human PI can audit at any depth. The 106-burst campaign is
simultaneously the science product and the discovery run for that agent.

## What keeps this honest

The ledger (VISION_QC.md per burst) records every round, every verdict, every
violation, sha256-bound. The contracts change only with the PI's quoted word.
And the one decision that closes the remaining hole — the mechanical hook that
makes un-gated delivery impossible instead of forbidden — is the PI's to make.

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

> ✔ NR-27 numbering conflict RESOLVED 2026-08-30 (PI, verbatim): "The BurstWalkthrough ledger numbering is official: 0b = literature harvest, 0 = identity & GCN, 1 = data inventory, and so on. Fix the live-report tool's step names to match; existing figure filenames keep their names — record the mapping once, do not rename products mid-campaign."
> The roster below now follows the OFFICIAL BurstWalkthrough ledger (0b literature, 0 identity/GCN,
> 1 data inventory, 2 detectors, 3 background, 4 source, 5 binning; 6–9 unchanged). Canonical
> mapping record: AgentRoster.md decision sheet item 22. Figure filenames keep their names.

- **0b/0 (literature harvest; identity & GCN):** producer = session (reads REPORT/PRODUCTS
  first — never re-derives); approver = PI. No figures, no verifier.
- **1 (data inventory; the scripts/44 step-1 panel incl. BCAT):** producer scripts/44 step-1 panel; FIGURE VERIFIER;
  NUMBERS VERIFIER vs grb_sample.ecsv (the BCAT mask lives there — the false
  "not checkable" claim class); approver = PI.
- **2–5 (detectors, background, source, binning — Stage-1 + blocks, ADOPT mode):** PRESENTER only — the PI's recorded human_gui
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
| every burst, continuously | NR-18 LIVE REPORT: per-burst live document assembled after every step -- gate status, stamps, evidence links; PI approves/feeds back on the document, feedback routes via distiller, approvals propagate via the invalidation cascade | DEPLOYED (dev/live_report.py + APPROVALS.json, 2026-08-21). GAP found + closed 2026-08-30 (I-12): evidence() knew on-disk evidence only for steps 1,6,7,8,9, so PRESENTED was mechanically impossible for 0b,0,2,3,4,5 — the PI ordered those stamps, so by rule an agent was missing: the per-step EVIDENCE RULE itself; extended same session with real paths (0b dossier/harvest/P0_frozen; 0 qc response-coverage + data dir; 1–3 decision.json + step PNGs; 4 blocks ecsv + binning PNG; 5 decision.json + human_review_qc_flags). CLARIFICATION PENDING PI (I-13): the PI's instruction read "stamping each step PRESENTED via dev/live_report.py --by VIKAS", but --by on --present is the PRESENTER's identity and a stamp bearing an identity that did not act is a fabricated stamp — the session stamps PRESENTED under its own identity and leaves APPROVED --by VIKAS to the PI (decision sheet item 24) |
| any upstream approval change | NR-19 INVALIDATION CASCADE: when an approved step changes, downstream phase markers are cleared and products regenerate -- accommodation is mechanical, not remembered (PI directive 2026-08-21) | DEPLOYED (dev/invalidate_downstream.py, 2026-08-21) |
| every report/paper delivery | NR-24 REPORT-CONFORMANCE GATE: verify the assembled deliverable against dev/ai_guides/ReportSpec.md R1-R5 (one generator+commit, exemplar structure, no raw nan, tie language, gates logged) — born from the PI catch 2026-08-26 'not all reports alike and top quality'; figures had a contract, the deliverable containing them did not | PROPOSED (spec written; gate agent next) |
| any detection/claim pipeline | NR-25 INJECTION-RECOVERY + NULL GATE: before a pipeline's claims are trusted, it must (a) recover a synthetic spectrum/light-curve of known parameters within stated uncertainty and (b) return no spurious signal on background-only intervals — a GATING battery, not a one-off (adopted 2026-08-29 from the external design survey; converges with our planned fault-injection; the seed-poisoning bug is the class it catches) | PROPOSED -> SHARPENED 2026-08-29 (2nd external review): generalize beyond ports to a TRUTH-GROUNDING GATE (A19): synthetic bursts with known Band/CPL/T90/lag/MVT through the FULL engine, recovery within stated tolerance + a fixture set of well-studied published bursts; runs at FREEZE and on every engine-hash change. Verifiers certify consistency; A19 certifies truth at the primitive. Acceptance = CLEAN-ROOM CHALLENGE (destroy workspace, rebuild from the archived object, rerun, compare within the declared REPRODUCIBILITY ENVELOPE — what must stay invariant + tolerance; our |dAIC|<0.1 frozen-replay guard is the existing instance). Formulation = property-based scientific tests (null data -> controlled false-positive rate; known effects -> stated coverage). Engineer backlog. |
| any census/preference tool | NR-26 GATE-BEFORE-ARGMIN: a tool that selects or ranks models MUST apply the engine's own validity columns (*_VALID / *_STATUS / BOUND_CAPPED) before taking an argmin — dev/model_preference.py did not, so results/campaign/model_preference.ecsv (and every figure quoting it) ranked over invalid fits. Found 2026-08-30 by the first fresh session; the figure gate had certified those numbers CONSISTENT with the file, which is exactly the consistency-vs-truth gap A19 exists to close | FIX APPLIED 2026-08-30 (per-burst use only; campaign-wide rerun blocked by the no-sweep ruling). Fix: the engine's own *_VALID + *_STATUS columns gate every argmin; the prefix→figure-name map is read from scripts/10's spec tables via ast (NR-10-conformant); the tool REFUSES TO WRITE on any mismatch vs the engine's BEST_AIC_MODEL column. PI ruling 3 (2026-08-30, verbatim): "Fix model_preference.py's validity gate before its output is quoted for THIS burst." results/campaign/model_preference.ecsv and every figure quoting it remain SUSPECT for every un-walked burst |
| any law/skill file set | NR-27 LAW-CONFLICT FLAG: when two binding documents disagree, the skill-reader must raise a CONFLICT rather than pick one (FreshSessionBoot §2 said "don't inherit the dispatch plan" while §6 said "read the existing plan" — the fresh session obeyed one and could not know it had chosen) | PROPOSED (skill-reader duty, A1) → FIRST INSTANCE CLOSED WITH A PI RULING 2026-08-30: CONFLICT-1 (I-4) — "DECISIVE" had no declared reference model (SpectralFitting.md:467 reference unnamed; PREFERENCE section = runner-up; ReportSpec R3 ties imply runner-up; the shipped #21 report + REVIEW_INDEX_106 "8 DECISIVE" measured vs the best simple model — one table read "8 DECISIVE" or "3 TRACKED / 5 ties") → ruling 3, written into SpectralFitting.md PREFERENCE section, ReportSpec R3, REVIEW_INDEX_106 caption. Further instances raised the same day: CONFLICT-3 MVT estimators → NR-32; CONFLICT-4 truncation flags → NR-33; CONFLICT-5 qc_flagging.md:22 still listed bn110920546 as a LIVE source-on-background burst (June-2026 misplacement era, since fixed; stamped Stage-1 yields 11 blocks) → dated resolved annotation, history kept; STEP-NUMBERING (I-12) live_report.py STEP_NAMES + this file's per-step roster vs BurstWalkthrough.md ledger + scripts/44 PNG names, shifted by one for 0b–5 — PENDING PI, no numbering picked (decision sheet item 22) |
| approval/cascade tools | NR-20 INPUT-AS-TRUST-BOUNDARY: the trig reaches os paths + a subprocess; validate against a trig grammar and fail loud, never os.system a raw arg (Codex 2026-08-21: a crafted trig turned a "markers only" tool into arbitrary-path removal + command exec) | DEPLOYED (validator in live_report.py + invalidate_downstream.py; os.system->argv) |
| any safety check | NR-21 NO-ASSERT-FOR-SAFETY: a security/authorization check must be a runtime check, never `assert` -- `python -O` strips asserts and the --by guard wrote by:null (Codex 2026-08-21) | DEPLOYED (live_report.py) |
| any doc→product claim | NR-22 SKIP-BY-EXISTENCE IS NOT SKIP-BY-CURRENCY: a marker/PNG/24-model no-op certifies existence, not which inputs it was built from; resume decisions on existence alone leave stale products (Codex 2026-08-21: bn090530760 canonical vs highe tables differ by hash yet promotion no-ops) | PROPOSED (provenance-hash generations). 2nd instance 2026-08-30 (I-6): scripts/47_mvt_cwt_crosscheck.py sha 5452cb2169… has drifted from the sha its own #21 sidecar recorded (abf1290f92…) — the sidecar certifies which code existed, not which code exists (see NR-32) |
| report assembly | NR-23 SAME-SOURCE REPORT+FIGURES: the report must read the SAME fit table the SED products are built from (convention_check promoted), not the nested sweep copy (Codex 2026-08-21) | DEPLOYED (48 reads convention_check first, 2026-08-21) — NECESSARY, NOT SUFFICIENT (I-1, 2026-08-30): the rule lived as prose+code in the reader but the deliverable never RECORDED which table it read, so a pre-rule report (08-18) built from the nested copy was indistinguishable from a conforming one → NR-28 |
| every report/figure that reads a fit table | NR-28 FIT-TABLE SHA BINDING: every report and every figure sidecar records the sha256 of the fit table it read, and the NR-24 conformance gate checks report-sha == figure-sha == promoted-sha (I-1, 2026-08-30: results/sweep106/bn110920546/REPORT_bn110920546.md (08-18) and its 12 nuFnu_bin*_allmodels_overlay.png were built from the nested copy results/sweep106/bn110920546/bn110920546/spectral_fits.ecsv (08-12, sha 4705a820…) while the promoted results/convention_check/bn110920546/spectral_fits.ecsv (08-17, sha 3b938990…) differs in 6/12 winners — T_INT, 4, 6, 7, 8, 9; PI ruling 2 (2026-08-30, verbatim): "Promote the 08-27 retry table (newer, terminal, winners identical). Its tier-3 cell list governs downstream." so the binding target for #21 is the 08-27 table). Missing agent: the A10 conformance gate with a sha-EQUALITY item — a same-source rule without a recorded source is unverifiable | PROPOSED (code: `fit_table_sha256` field in 48/41c/41e sidecars + gate item) |
| every gate presentation | NR-36 PLAIN-LANGUAGE OPENER: four jargon-free sentences (WHAT I DID / WHAT I FOUND / WHAT I NEED FROM YOU / WHAT HAPPENS NEXT) before ANY technical content — no register numbers, no state codes, no acronyms in those lines; a presentation the PI cannot understand is a FAILED presentation (PI catch 2026-08-30: "everything has suddenly become a complicated language"); the PI always replies in plain words and translation into the machinery is the session's job | DEPLOYED (FreshSessionBoot §8 + §9: gates presented as structured choices via AskUserQuestion — recommended option honest-only (decision gates: session may recommend; approval gates: only the verifier verdicts may recommend), "Other"/plain-text always available, every click becomes an identity-bound stamp (PI ruling 2026-08-30) |
| any recorded human decision presented | NR-37 DIVERGENCE LEARNER: when a human choice differs from the machinery's recommendation and neither failed, run DETECT-ELICIT-VALIDATE-GENERALIZE-LEDGER (FreshSessionBoot §10) — the reason is the human's words or a confirmed candidate, never a guess; validated patterns become decision rules in the owning skill; results/campaign/divergence_ledger.md tracks the convergence rate, which is ALSO the A16 fully-AI-approver readiness metric (PI directive 2026-08-31; founding instance = bn110920546 step 2, executed spontaneously by the fresh session before the rule existed) | DEPLOYED (protocol §10 + ledger; duty shared: presenting session detects/elicits/validates, distiller places the rule) |
| report/paper assembly | NR-29 ASSEMBLER SELF-PIN GUARD: the assembler refuses to run if its own file is not tracked-and-clean at HEAD, and writes {commit, tree_dirty_list, product_sha256s} into the staging manifest (I-2, 2026-08-30: all 12 campaign producers — notes/codex_campaign20_runtime/{assemble_report_paper,campaign_products,run_p2_temporal,run_p4_products,run_sed_sweep}.py, dev/{paper_chain.sh,campaign_retry_pool.sh,merge_campaign_families.py,gen_param_tables.py,make_repro_record.py,rebuild_step9_canonical.py,verify_burst_invariants.py} — were UNTRACKED while the boot brief said the campaign commit was pinned; .gitignore:41 `results/*` means products can never be commit-bound). PI ruling 4 (2026-08-30, verbatim): "R1: commit the campaign generators and re-pin now (before anything is assembled). Manifest records: generator pinned by commit, products bound by hash — products are untracked by design." DESIGN GAP: there was NO designated location for the pin; results/campaign/CAMPAIGN_COMMIT_PIN.json is IMPROVISED by the operating session — PI to bless or relocate (decision sheet item 23) | PROPOSED (ruling 4 executed by the operating session 2026-08-30: generators committed + re-pinned; the refuse-if-dirty guard is queued code) |
| every campaign transition launcher | NR-30 DISPATCH-HOOK TRANSITION COVERAGE: .claude/hooks/require_dispatch.py's GATED regex covers campaign_products_driver.sh and "assemble_report_paper.py … build" but NOT direct invocations of campaign_products.py, run_p2_temporal.py, run_p4_products.py, run_sed_sweep.py — four of five transitions could run with no dispatch plan (I-3, 2026-08-30; the P9 class, at the hook layer this time) | PROPOSED regex extension (operating session applies + smoke-tests; distiller does not edit hooks) |
| every consumer of results/temporal_catalog_all106.ecsv | NR-31 STALE-COLUMN CONSUMER GUARD: before quoting any LAG_* or MVT_* value the consumer (scripts/48, the paper assembler, accumulators, the numbers-verifier contract) reads meta.stale_pending_rewalk and REFUSES unless TRIGGER_NAME is in meta.rewalked_triggers — the label is enforced by code, never by memory. PI ruling 5 (2026-08-30, verbatim): "Temporal: NO all-106 sweep. #21's wf-temporal regenerates its own T90/MVT/lag with the validated tools and REPLACES its rows in the catalog, keyed to the new receipt. The two campaign-wide wrong columns (lag sign, MVT) get a STALE-PENDING-REWALK label in the catalog header + a register row — every later burst repairs its own rows the same way, as it is walked." PI caveat (verbatim): "the committed catalog keeps its proven-wrong lag sign and MVT for every burst not yet walked, so nothing downstream may quote temporal_catalog_all106.ecsv for an un-walked burst — that's what the STALE label enforces mechanically rather than by memory." Instance (I-7): #21 LAG_S=−5.250, LAG_ACCEPTED=True, printed in the shipped report with the STANDARD-convention text — a mislabel; the validated 47c value is +0.715 s (−0.215/+0.244, window sys 0.387; POSITIVE = soft lags hard) and Lu+2018 tabulates +1.22±1.27 s (Temporal.md L26 validation). Header label written by the operating session (verified on disk 2026-08-30: meta.stale_pending_rewalk present, rewalked_triggers=[]) | PROPOSED (code guard in 48 + assembler + numbers-verifier contract; header label DEPLOYED) |
| catalog admission (A4), MVT rows | NR-32 PUBLISHED-LIMIT CONSISTENCY SCREEN: where a Golkhou+2015 Table 2 row exists for the TRIGGER NUMBER (never the name — rows 801/802 of golkhou2015_table2.tsv list both 110920338 and 110920546 as "110920A"), an MVT DETECTION above the published upper limit is an admission REFUSE with reason. Instance (I-6, CONFLICT-3, 2026-08-30): #21 catalog MVT_S=5.342 s (Haar, MVT_TYPE=detection) vs published dt_min<2.096 s — 2.5× over; CWT 0.724±0.058 s (results/mvt_cwt/bn110920546_mvt_cwt.json, "grid-quantized", verbatim s02g, role EXTENSION) is consistent; Bala never run (results/mvt_upstream/run_step7/bn110920546/ = empty logs/); Temporal.md described only Haar + Bala while products shipped CWT; scripts/47 sha drift = NR-22. Estimator precedence now law in Temporal.md L32: Bala canonical > CWT cross-check > Haar; MVT_TYPE=detection is Haar-only | PROPOSED (admission-gate screen at the code layer; Temporal.md L32 written 2026-08-30) |
| any T90 quote | NR-33 TRUNCATION-FLAG UNION: lower-limit language is triggered by the UNION of T90_WINDOW_TRUNCATED (t5/t95 on the window edge) and TAIL_OUTSIDE_WINDOW_SIG ≥ 3σ (L29) — Temporal.md carried both flags with no precedence (I-8, CONFLICT-4): #21 has T90_WINDOW_TRUNCATED=False and TAIL_OUTSIDE_WINDOW_SIG=11.95σ, so a consumer reading only the first quotes 88.67 s as a measurement. Code layer: a derived T90_IS_LOWER_LIMIT column in scripts/40 that the R3 numbers rule keys on | PROPOSED pending PI (Temporal.md L31) |
| every FAIL cell | NR-34 FAIL-CELL SEED REPLICATION (candidate row — hypothesis, NOT established): #21's promoted (08-17) and retry (08-27) tables have IDENTICAL winners 12/12 but DIFFERENT FAIL sets ({blk0 DSBPL, blk0 BANDRCPL, blk6 DSBPLF} vs {blk0 BANDRCPL, blk2 DSBPLF, blk7 DSBPLF}); results/convention_check/sed_grid_bn110920546/sweep_status.txt records ONE genuine refusal in 288 cells (DSBPL@bin0) and two of the three FAIL cells already have live fits with sidecars (I-10, 2026-08-30). HYPOTHESIS: the campaign's 333-cell FAIL concentration in BANDRCPL/DSBPLF/BANDCPL/SBPLCPL is multistart fragility, not data. RULE IF CONFIRMED: a FAIL cell is F-STRUCTURAL only if it fails under ≥2 independent seeds, else retry-class. SETTLING MEASUREMENT: rerun each #21 FAIL cell under 3 independent seeds (NR-2 recorded); ≥2/3 FAIL = structural, else retry-class — per-burst, under the no-sweep preamble | PROPOSED (candidate; do not resolve without the measurement) |
| dispatch-plan authoring (A2) | NR-35 PER-BURST FAIL-LIST DERIVATION: a plan's per-burst FAIL/exposure list is derived from THAT burst's fit table at plan time, never pooled across bursts (I-11, 2026-08-30: results/campaign/DISPATCH_PLAN_campaign21plus.md:111-112 scoped NR-10 exposure to "DSBPLF / BANDRCPL / SBPLCPL / CPLCPL" — a #21∪#22 union; #21's actual FAIL families are DSBPL/DSBPLF/BANDRCPL and SBPLCPL is its T_INT winner) | PROPOSED (plan generator reads the table; recorded as A2 honest limit (4)) |
| every written decision rule vs the recorded expert decisions (CODE/CONTRACT layer) | NR-37 SPEC-VS-PRACTICE DIVERGENCE: a written rule the expert does not follow is a defect in the RULE, not in the arm that obeyed it; and any arm scored against the expert must be scored against the rule the EXPERT ACTUALLY USED. Missing agent: RULE-CONFORMANCE AUDITOR — replay every written decision rule against ALL recorded human decisions, report the agreement fraction, and raise a SPEC DEFECT below 100%. Instance (I-14, 2026-08-31, step-2 gate of the Lane-A #21 walkthrough, bn110920546): `dev/ai_guides/detector_selection.md:20-24` makes BCAT membership matter ONLY in the 50–60° rescue band (“NaI θ ≤ 50° → KEEP” regardless of trigger); the pipeline pre-ticked {n0,n1,n3,n6,n7,b0,b1} and BOTH independent AI passes (`results/approval/bn110920546_claude.json`, `_codex.json`) kept all 7, each citing the ≤50° prior plus visible excess in n6/n7 — while the PI’s recorded `human_gui` decision kept only {n0,n1,n3,b0}; n6 (25.33°) and n7 (47.68°) pass ≤50° but are NOT in the BCAT mask (`_pending.json` `in_bcat=false`). MEASURED, read-only, over the 105 human_gui bursts having both a `_pending.json` and a `_decision.json`: kept-NaI set == BCAT-triggered NaI set **82/105 (78%)**; kept-NaI set == geometry(≤50°) set **50/105 (48%)**; a NaI passing ≤50° was DROPPED by the human in **19/105** (bn081224887 n0,n1; bn100130729 n6; bn110920546 n6,n7; bn110928180 n6; bn120130938 n9,na; bn120624933 na; bn130215063 na; bn130427324 n0; +11 more). NEITHER candidate rule reproduces the expert 100% of the time — neither is adopted here. WHY IT REACHES BEYOND ONE BURST: Part 1 is an AI-vs-human benchmark (PROJECT.md), so a systematic divergence in which the AI arms faithfully follow a written rule that does not describe the expert’s practice is a BENCHMARK CONFOUND — scored as AI error when it is a SPECIFICATION defect; and because the Stage-1 detector set fixes every downstream signal-to-noise, block significance and bin-adequacy number, the two arms differ systematically on ~1 burst in 5 | PROPOSED — THE RULE TEXT STANDS UNAMENDED. The PI’s reason is a RECOLLECTION stated with uncertainty, verbatim 2026-08-31: “I must have selected the ones those are on same side and probaly the triggered ones too” — P2 forbids amending a contract without the PI’s ruling, and a recollection is not a contemporaneous record. The session VERIFIED both halves at the primitive (kept NaI == BCAT-triggered set exactly; all kept NaIs low-side ⇒ companion rule takes b0, drops b1). OPEN QUESTION FOR THE PI: should BCAT membership gate NaI selection BELOW 50° too? Recorded as a dated OBSERVED-PRACTICE note (not a rule change) in detector_selection.md §“Observed practice”, and as an ADOPT-mode presentation duty (ADOPT-1) in BurstWalkthrough.md |
| every Stage-1 approval write, human path (code layer) | NR-38 DECISION-RATIONALE CAPTURE: a recorded decision that overrides the tool’s own pre-tick set MUST carry its reason AT WRITE TIME — the GUI asks for it and ingest REFUSES a `decision.json` whose `reasoning` is absent or empty. Missing agent: RATIONALE-CAPTURE GUARD at the code layer (not prose): `scripts/39_approve_all.py:817-819` builds the human_gui decision dict with keys trigger/approver/mode/detectors/source/windows/angles and NO `reasoning`, and the module docstring `scripts/39_approve_all.py:52` calls it “optional free text” — while `dev/ai_guides/detector_selection.md` lists it in the output contract and the AI path fills it. MEASURED 2026-08-31 over `results/approval/*_decision.json`: **1 of 105** human_gui decisions carries a non-empty `reasoning`, and that one is the retroactive amendment written today; the other 104 are silent. Instance (I-15, same gate as I-14): bn110920546’s human decision overrode the pipeline pre-ticks AND both AI passes and sat UNEXPLAINED on disk from 2026-07-19 to 2026-08-31 (6 weeks); the reason had to be reconstructed from the PI’s memory, which is exactly why it is stamped RETROACTIVE in `results/approval/bn110920546_decision.json` (`reasoning` + `reasoning_provenance`). Without the reason on disk, NR-37’s divergence class is undetectable burst-by-burst — it only shows up as an unexplained set difference. Spec home: `dev/GUI_REQUIREMENTS.md` R-GL-8 | PROPOSED (code: GUI capture prompt + non-empty-`reasoning` check in scripts/39 ingest; the 104 historical blanks STAY BLANK — a reconstructed reason is never a contemporaneous record, and back-filling them would manufacture evidence for the very benchmark they are the ground truth of) |

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

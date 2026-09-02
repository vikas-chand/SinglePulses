# OUR HARNESS vs "How to Build an Effective Agent Harness" (Bowne-Anderson) — 2026-09-02

**Source:** https://hugobowne.substack.com/p/how-to-build-an-effective-agent-harness (fetched
2026-09-02). The PI: *"something important for us from here, can you compare what we have and
have not"*. Our side is read from disk: `notes/AGENTS_REVIEW_20260902.md` (10 agents, 3 hooks,
orchestrators), `notes/SKILLS_REVIEW_20260902.md`, `dev/ai_guides/AgentSkeleton.md`,
`AgentRoster.md`, `AgentArchitecture.md`, `results/campaign/`, `tests/`, and the Codex
skill-graph verdicts of 2026-09-01. Verdict column: HAVE / PARTIAL / MISSING.

## §0 The article in one paragraph
An agent is "an LLM with tools in a loop"; the harness is "the runtime system around the model
call that lets the system act". It has five runtime jobs: run the reasoning loop, execute
tools, assemble and manage context, persist state, enforce boundaries. Match the harness to
the job's CONTEXT complexity and ACTION complexity, not to a generic template. Start with four
tools (Read, Write, Edit, Bash); "the repeatability comes from the skills, approval points,
verification criteria, and connections around it". Long-running agents manage context by
REDUCE / OFFLOAD / ISOLATE. Choose the control structure per problem: single call, fixed
workflow (chaining), routing, or a BOUNDED loop with a retry limit inside a deterministic
workflow step. "Every harness feature is a bet on what the model can't do" and the bet expires
when the model changes: retest scaffolding on every model change against a stable eval set.
Improve from real failures: start simple, capture traces (inputs, decisions, tool calls,
errors, tokens, latency, cost, outcome), build evals from real work, keep TWO harnesses
(runtime and eval), change one hypothesis at a time, set the release bar by the cost of being
wrong. Five rules: simplest architecture; match the job; workflows and loops each where
useful; failures and evals decide what to add; retest when the model changes.

## §1 The five runtime jobs

| job | what we HAVE (evidence) | what we do NOT | verdict |
|---|---|---|---|
| 1 run the reasoning loop | Mode B: the Claude Code session IS the loop (AgentSkeleton §8); every step runs as skill-reader → producers → verifiers → stamps by protocol | Mode A (SDK, queue manager as the application) unbuilt; `dev/queue_manager.py` and `.claude/workflows/` absent (FreshSessionBoot.md:160) | PARTIAL |
| 2 execute tools | exactly the article's minimal core: Read/Write/Edit/Bash; 9 of 10 agents carry Read/Grep/Glob/Bash only; the scripts are the domain tools | — | HAVE |
| 3 assemble / manage context | skill-reader returns a burst-bound checklist at every step open; MEMORY.md + memory files; notes/ handoffs; per-burst REPORT/PRODUCTS read first; fresh-context sub-agents | reading the whole law every step is expensive (AgentRoster A1 honest limits); no persisted checklist per step (Codex r1 asked for it) | HAVE, with the known cost |
| 4 persist state | `dev/agent_state.py` derives S0–S12/SX from DISK evidence (the anti-"I think it ran" board); APPROVALS.json identity stamps; provenance sidecars; `CAMPAIGN_COMMIT_PIN.json`; promotion receipts | no durable queue; kill-9-safe sequencing spec'd (A17) not built; NR-7 run provenance not written for the last two refits | PARTIAL |
| 5 enforce boundaries | three PreToolUse hooks (no-ship on SendUserFile, P9 dispatch on Bash, raw-data guard); permission modes; P1–P9; the register of 47 rows | hooks cover 1 of 5 transitions (NR-30); the dispatch hook matches command TEXT (three false blocks today); most rules are prose, "nothing makes it fire" (Codex r1) | PARTIAL |

## §2 Matching the harness to the job
Our job is HIGH on both axes: long-running (a burst = 11 steps, dozens of gates, 24-model
menus, 106 bursts), high action complexity (heavy producers, catalogs, figures, releases).
The article's prescription for that profile is exactly reduce/offload/isolate plus strict
permissions, guardrails and handoffs.

| move | HAVE | note |
|---|---|---|
| REDUCE | harness compaction; LIVE_REPORT rebuilt from stamps; per-burst REPORT as the single deliverable | — |
| OFFLOAD | notes/, memory files, VISION_QC ledgers, dossiers, provenance sidecars; "long explanations go to a file" rule | — |
| ISOLATE | fresh-context verifiers (figure, numbers, seed, tie, admission), Explore agents for inventories, the referee clean room (`dev/referee/`) | matches the article's deep-research pattern: focused sub-agents, main agent synthesizes |

Verdict: HAVE. This is the part of the article we already live by.

## §3 Control structures

| article pattern | ours | verdict |
|---|---|---|
| fixed workflow (chaining) | the pipeline spine: Stage-1 → 27b blocks → engine → products → report; prototype shell chains | HAVE as shell prototypes; the `wf-*` workflow files that were to replace them do not exist |
| routing (constrained decision) | the dispatcher returns the roster, gates and order for a task (NR-17); Maven-style "lead router to bounded domains" = our per-step roster | HAVE (as an agent, invoked by protocol) |
| bounded loop inside a workflow step | RefereeLoop.md: reviewer → revision → reviewer, **cap 2**; reconciliation P4 "one change at a time"; engine multistarts | figure-verifier rounds are UNBOUNDED (28 rounds on burst #1); numbers-verifier re-runs have no cap; no retry limit written for any gate but the referee | PARTIAL |
| evaluator-optimizer | producer ≠ verifier ≠ approver (P1, ShippingGate); fresh-context verdicts sha-bound | same missing retry limit | PARTIAL |
| hybrid: deterministic spine, reasoning inside steps | AgentSkeleton §3 is precisely this design (typed stages per transition) | design only; execution is session protocol | PARTIAL |

## §4 "Every harness feature is a bet on model limitations" — retest when the model changes

| article item | ours | verdict |
|---|---|---|
| each feature is a recorded bet | the register: 47 rows, each born from a real incident or PI directive, with WHY (AgentArchitecture.md:112–125) | HAVE, better than most: the bet's origin is written |
| the bet has an expiry / retest condition | no register row carries "retest when the model changes" or a measurable keep-condition | MISSING |
| the model that made each product is recorded | NO product records a model id: `generated_by` says "campaign doc-layer worker"; APPROVALS stamps say "Claude session"; the commit pin has no model field; sidecars carry engine sha, not model | MISSING |
| retest on model change against a stable eval set | none; models changed under us (Opus → Fable sessions; Codex gpt-5.6-sol) with no rerun | MISSING |
| old scaffolding becoming friction | live example TODAY: the β floor −5 and the (0.8, 1.2) EAC box — bounds set once, found manufacturing "undefined" rows on #21, widened by PI ruling 82737c9; the −5 floor was a workaround that became a constraint | instance recorded |

This is the largest gap, and it is cheap to close at the provenance layer.

## §5 The improvement loop

| article step | ours | verdict |
|---|---|---|
| start with one real task, define good | burst #1 (bn081125496) end-to-end, then the 106; the PI's case-study item is exactly this | HAVE |
| capture telemetry (inputs, decisions, tool calls, errors, tokens, latency, cost, outcome) | script logs under `logs/`; VISION_QC round ledgers; the catch ledger in BURST1_LESSONS (hand-kept: ~55 vision, ~27 Codex, 12 PI…); no per-invocation trace of agents; no token/latency/cost record anywhere on disk | MISSING (the Codex r2 ACTION_EVENT envelope is the same object; converge them) |
| evals from real work, labeled | `tests/test_lessons.py`: lessons-as-tests on real fit tables (11 tests, xfail ledger for known-stale debt) — this IS "evals from real failures"; 33 tests in 8 files; the Stage-1 human-vs-AI benchmark (`scripts/40_benchmark.py`, `results/benchmark/`, expert 2 never delivered); the known-results battery (Burgess 130427A, 110721A, 160625B) in the paper | PARTIAL: real and labeled, but not one stable SET run on every change |
| two harnesses: runtime + eval | runtime = the campaign; eval = tests + benchmark + reconciliation records, not unified, not run per change | PARTIAL |
| change one hypothesis at a time | rule exists for science (P4 reconciliation) and for verification (delta re-verify); harness commits bundle many changes (today's 1dc41c1 changed six things) | PARTIAL |
| release bar by cost of being wrong | PI gate on every step, shipping gate, no-ship hook, referee panel for milestones, "no product ships unverified" | HAVE (deliberately high) |
| inspection surface fits the product | per-burst REPORT + LIVE_REPORT table + VISION_QC ledger; the PI reads reports, not dashboards | HAVE |

## §6 Anti-patterns the article names, checked against us

| anti-pattern | us |
|---|---|
| over-engineering from a template | guarded: Codex r1 refused a skill-graph actor; agents are born from incidents, never from a framework diagram |
| premature complexity | mixed: 10 agents and 47 rows from 21 bursts is incident-driven (rule 4 satisfied); but the skeleton's 11 workflows + queue manager were specified before any of them was needed by a failure — and are still unbuilt, which is the article's point |
| model-agnostic harness | GUILTY: no model pinning, no retest protocol |
| evaluation debt ("today's workaround becomes tomorrow's constraint") | instances: the β floor, the EAC box, the 24-model menu's ancestor map (four models with no ancestor, L31) |
| ignoring irreversibility | guarded: raw-data hook; invalidation clears markers never products; backup-before-mutate; approvals never fabricated |
| automated promotion without review | guarded: P1 no self-approval; producer never verifies its own work |

## §7 What this means for the program (items 2–6 of 2026-09-02)

1. **Agent merge by roles (item 2)** is the article's rule 1 and its OpenClaw lesson: keep the
   loop small, grow the product harness only in response to real requirements. The merge
   candidates C1–C5 in `notes/AGENTS_REVIEW_20260902.md` §5 reduce ten files to five places
   without removing a single incident-born duty.
2. **The case study (item 4)** is "start with one real task and define what a good result looks
   like" — and it should double as the seed of the STABLE EVAL SET: the burst's gates, verdicts
   and numbers become labeled cases rerun on every harness change and every model change.
3. **Provenance must carry the model** (closes §4): add `MODEL_ID` (and harness version) to the
   NR-7 run record, to APPROVALS stamps, to harvest/P0 manifests; add a "keep-condition /
   retest-on-model-change" column to the register. Candidate row NR-48.
4. **Telemetry = the ACTION_EVENT envelope** Codex already specified: one record per agent
   invocation (agent, role, inputs' hashes, verdict, tokens, wall time, cost). Land it inside
   the queue manager when built; until then a one-line append per invocation is enough.
5. **Retry limits on every verification loop** (the referee loop is the model: cap 2, then the
   PI). Figure and numbers rounds get a cap and an escalation rule.
6. **The eval harness as a unit**: `tests/` (lessons-as-tests) + the known-results battery +
   the case-study cases, one command, run on every commit and on every model change, results
   sha-bound like everything else.

## §8 One-line scorecard
HAVE: minimal tool core · skills as files · isolate/offload/reduce · disk-derived state ·
producer≠verifier · incident-born features with recorded WHY · high release bar · routing ·
irreversibility guards.
PARTIAL: deterministic spine as code · bounded loops (no retry caps) · hook coverage ·
eval set as one unit · one-hypothesis commits.
MISSING: model identity on products · retest-on-model-change · per-invocation telemetry
(tokens, latency, cost, decisions).

---

# PART 2 — vs "Harness Engineering for Coding Agent Users" (Böckeler, martinfowler.com, 2026-04-02)

**Source:** https://martinfowler.com/articles/harness-engineering.html (fetched 2026-09-02; the PI's
second article). Her frame: the harness is everything except the model, built by the USER around
the agent; controls are GUIDES (feedforward, steer before the act) and SENSORS (feedback, observe
after); each is COMPUTATIONAL (deterministic, fast, reliable) or INFERENTIAL (LLM judgement, slow,
probabilistic); humans run a STEERING LOOP (an issue that recurs → improve a guide or a sensor);
keep quality LEFT (fast sensors pre-commit, expensive ones post-integration, drift monitored
continuously); regulate three things separately (maintainability, architecture fitness,
behaviour); HARNESSABILITY is a property of the codebase (ambient affordances); harness
TEMPLATES per topology; Ashby's law (commit to a topology = variety reduction; the regulator must
have a model of the system); the human's job is what the agent cannot do (accountability,
aesthetic judgement, "we don't do it that way here", knowing which convention is load-bearing);
open questions: coherence as guides and sensors grow, conflicting guide vs sensor, "if sensors
never fire, is that quality or blindness", harness coverage testing, tooling to reason about the
controls as a system. Closing advice: computational sensors first; inferential guides where
prediction matters; steering loops from repeated failures; design for harnessability early.

## §9 Guides and sensors, computational and inferential — our census

| kind | ours (evidence) | count |
|---|---|---|
| GUIDES, inferential | CLAUDE.md/AGENTS.md; 27 skill files; skill-reader checklist at every step open; dispatcher plan; FreshSessionBoot ritual; standing contracts (FigureVisionQC S-items, ReportSpec R-items, count coordinates) | ~30 files, ~100 rules |
| GUIDES, computational | fixed model menu (24); fixed ledger (11 steps); engine constants block (PI convention cited); `PARAM_BOUNDS`; `NESTED_PARENTS`; the three notebook templates | a handful, inside code |
| SENSORS, computational | 33 tests in 8 files (lessons-as-tests on real fit tables, figure-style structural test = the ArchUnit analogue, catalog QC, compile); 3 PreToolUse hooks (no-ship sha check, dispatch, raw data); engine guards (validity gate, LRT guard, band-validity NR-1, stored-ref binding NR-9, gate-before-argmin NR-26, stored-AIC hard guard in 41b); `scripts/43` catalog validator, `scripts/36` progress/invariants; `tests/test_register_ids.py`, `tests/test_lesson_ids.py` (today) | ~50 checks |
| SENSORS, inferential | figure-verifier, numbers-verifier, tie-reporter, seed-auditor, admission-gate, prior-art-reader, port-verifier (fresh context); Codex supervisor audits; the blind referee panel; the PI at every gate | 7 agents + Codex + PI |
| PROPOSED but unbuilt, would be computational | NR-7 run record, NR-8 merge integrity, NR-16 product-absence assert, NR-22 hash currency, NR-30 hook coverage, NR-31/32/33 screens, NR-39 rationale guard, NR-46 read-path vacancy; and four of the five step-6 auditors born on #21 (basis-set label, rail stamps, margins-only lint, count triple) | ≥ 12 |

**Finding 1 (her closing advice, "computational sensors first"): our growth is inferential-heavy.**
Incidents land as prose rules and agent duties; the code-layer guards they call for stay PROPOSED.
Of the five auditors born at the #21 step-6 gate, four are countable from the fit table and need no
judgement. **Verdict: PARTIAL, and the direction is wrong.**

**Finding 2 (feedforward-only "encodes rules never tested for effectiveness"):** ~100 skill rules
have no sensor that would fire on a recurrence and no measure that the guide changed behaviour.
The register names the incident behind each row (good), not the sensor that would catch it again.
**Verdict: PARTIAL.**

## §10 The steering loop, timing, drift

| her item | ours | verdict |
|---|---|---|
| steering loop: recurring issue → better guide or sensor | the distiller + register, same session; doctrine "a lesson is not learned until it exists as a CLAIM and a TEST" (`tests/test_lessons.py` docstring); AI writes the tests and skills; Codex audits | HAVE — but it closes into prose ~4 times out of 5 |
| pre-commit sensors (Stripe "shift feedback left") | none: no pre-commit hook; CI runs only on push/PR to main; `results/` is gitignored so the science tests are VACUOUS in CI (labelled UNVERIFIED-IN-CI, honestly) | MISSING |
| in-session self-correction loop | skill-reader → produce → verify before the PI sees anything; the no-ship hook sits left of delivery | HAVE |
| post-integration expensive sensors | Codex whole-project audits, referee panel, ultrareview on milestones | HAVE |
| continuous drift monitoring (OpenAI "garbage collection") | `scripts/36` and `43` exist but run "anytime" by hand; stale artefacts on read paths (NR-22/28: 12 overlays + a REPORT from August still where a reader looks) were found by an inventory agent, not a monitor; no scheduler | MISSING |
| runtime feedback | n/a (no service); the analogue = campaign accumulators + the disk state board | HAVE in kind |

## §11 Regulation categories, harnessability, templates, Ashby, the human

| her category | ours | verdict |
|---|---|---|
| MAINTAINABILITY harness (code quality) | no linter, no type checker, no complexity/duplication sensor; 3,444-line assembler and 1,821-line runtime scripts unguarded; `scripts/legacy/` beside live code; only `test_scripts_compile` | MISSING — the one category with nothing |
| ARCHITECTURE FITNESS (fitness functions) | invariants that ARE fitness functions: fail-closed orchestrator, same-source rule (NR-23), sha binding (NR-28), no-fallback read paths (NR-46), every figure through `plot_style` (structural test) | PARTIAL (several still prose) |
| BEHAVIOUR harness (does it do the right thing) | the science sensors: verifiers; the known-results battery (Burgess 130427A, Ravasio 160625B, 110721A); the **approved-fixture pattern** in her exact sense: the assembler's output for bn081125496 is diffed against the hand-built exemplar the PI graded; "correctness needs a human spec" = PI rulings quoted verbatim into the S- and R-contracts | HAVE, stronger than typical because the PI defines "good" per step |
| HARNESSABILITY / ambient affordances | trigger-in-filename (G1); ECSV headers with meta + amendment trails; sidecar JSON per product; sha-bound verdicts; state derivable from disk. Weak: untyped Python; a 976-column table with per-model suffixes and no schema file (numbers-verifier transcribed n_params by hand, NR-10); the two legacy roots | PARTIAL |
| harness TEMPLATES per topology | the walkthrough (11 steps × roster) + dispatch plan per lane + per-step notebooks; sibling projects re-instantiate it — and her versioning risk already bit us: the FBOT port inherited three pre-audit bugs by copying files (memory) | HAVE the pattern and its failure mode |
| Ashby: commit to a topology; the regulator needs a model of the system | one topology (single-pulse, GBM, fixed menu, fixed ledger); the register + per-step roster + state machine ARE the regulator's model | HAVE |
| the human where the agent cannot substitute | 11 PI gates per burst (every step) — more supervision than her criterion asks; NR-38 (the expert does not follow the written rule) is her "which convention is load-bearing" found empirically; the fully-AI approver identity (A16) is exactly her question, pending | PARTIAL: gates are everywhere, not yet only where judgement is irreplaceable |

## §12 Her open questions, our state

| open question | ours |
|---|---|
| coherence as guides and sensors grow | live: two step-8 definitions, L31–L33 collisions, NR-41 minted twice (all today); NR-27 law-conflict flag unimplemented; two id tests now guard part of it | PARTIAL |
| guide vs sensor disagree — how far to trust the agent | CONFLICT-n items go to the PI gate; RefereeLoop OPEN-DISAGREEMENT class | HAVE a rule |
| sensors that never fire | the instance: `BOUND_CAPPED` never fired on the −5 rail (L9 guard silent) while it manufactured 4 of 5 undefined rows; no "last fired" ledger for any guard | MISSING |
| harness coverage testing (mutation testing for the harness) | none; Codex r2 proposed mutation-testing the action detector | MISSING |
| tooling to reason about the controls as a system | the register + ledger + two id tests are the seed; no single view of guides, sensors, and which rule has which sensor | PARTIAL |

## §13 Actions the two articles point at together (PROPOSALS)
1. **Computational first**: turn the four countable step-6 auditors (basis label, rail stamps as columns, margins-only lint, count triple) into code over the fit table; keep agents for judgement only. Same for the ≥12 PROPOSED code-layer rows.
2. **Pre-commit sensor**: the fast suite (6 s) as a pre-commit hook; CI stays for catalogs and imports; a LOCAL run over products is the science gate.
3. **"Did it fire" ledger**: for every guard, hook, test and agent duty, last-fired date and count; a never-fired sensor after N bursts is a review item (the BOUND_CAPPED lesson). This is also Bowne-Anderson's telemetry.
4. **Drift janitor**: scheduled `36 + 43 + read-path currency scan` (NR-22), computational.
5. **Sensor-for-every-rule**: each register row names the sensor that catches a recurrence; rows with none are the untested-feedforward class, counted (Codex's coverage lint).
6. **Human input where irreplaceable**: classify the 11 gates into PI-only (Stage-1 judgement, rulings, contract amendments) and sensor-closable with an independent approver — the A16 design, now with her criterion.
7. **A minimal maintainability harness** for `scripts/`: ruff + complexity threshold + a legacy quarantine off the import path.
8. **Model pinning + retest + eval set** (Part 1) stay the top three.

---

# PART 3 — vs Palantir's ONTOLOGY (platform page + Foundry docs, fetched 2026-09-02)

**Sources:** https://www.palantir.com/platforms/ontology/ (page text read through Chrome; the
fetcher only saw the shell) and the Foundry docs (Ontology overview; core concepts; action types;
AIP chatbot studio). The page's claim, verbatim: *"The Ontology System encodes the data, logic,
action, and security of the enterprise to automate decisions across your operations."* Its
language has four parts: **encode the data** (objects, properties, links); **capture the logic**
(functions, "built to evolve as that reasoning changes"); **model the actions** ("real-world
actions as first-class primitives", multi-step workflows that write back); **govern the
human-agent labor force** ("granular controls across data, logic, and action simultaneously,
whether the actor is a human or an agent"). The engine: "millions of reads, millions of writes,
one unified reality"; continuous sync so decisions "are reflected where actions take effect".
The toolchain: the Ontology as a backend; a **"tool factory"** for humans and agents; **Ontology
MCP** exposing primitives to external agents under the same security; "turn specialized expertise
into shared infrastructure". Docs add: object type / property / link type / action type (with
rules, validations, submission criteria, side effects, a writeback dataset, "actions capture user
decisions and insights as Ontology edits"); functions; interfaces (polymorphism); roles;
branching and change-proposal review of the ontology itself; schema migration.

## §14 Their primitives, our counterparts

| primitive | ours (evidence) | verdict |
|---|---|---|
| Object types + properties (the data) | typed on disk: bursts (`grb_sample`, `single_pulse_grbs`), selections (`background_intervals.ecsv`, 13 cols, meta `amendments`), blocks (`bb_blocks_*.ecsv`), fits (`spectral_fits.ecsv`, 976 cols), temporal rows (26 cols, meta `stale_pending_rewalk`), redshifts, harvest paper records (14 keys), P0 predictions, approval stamps (`{by, feedback, status, utc}`), promotion receipts (14 keys incl. sha and input fingerprint), fit sidecars, burst state (`{trig, state, evidence, derived_utc}`) | HAVE the objects; **no schema file for any of them** (zero on disk); the fit table is one 976-column row per block, not normalised into fit objects |
| Links (relations) | by convention only: `TRIGGER_NAME` keys, sha256 binding verdict→figure and product→generator, commit pin | PARTIAL: links exist as keys and hashes, never declared |
| Actions as first-class primitives, with rules, validations, submission criteria, side effects, writeback, decision capture | `dev/live_report.py --present/--approve` (identity required, evidence linked, feedback routed = side effect); `dev/invalidate_downstream.py` (the cascade = a rule); promote / quarantine (receipts); hooks as submission criteria for two actions (ship a PNG; launch a producer). Everything else that changes state is a script run — not declared, not validated, not captured | PARTIAL: two or three actions are first-class; ~all producer runs and file writes are not. Codex r2's ACTION_EVENT envelope (intent → preflight → commit → finalize) is exactly the missing action primitive |
| Functions (logic that evolves) | scripts, `dev/model_preference.py`, `dev/agent_state.py`, the engine; the PI's rulings as prose in skills; the register as the "why" | HAVE the logic; the rulings that determine actions live in markdown, not as callable rules |
| Interfaces (polymorphism) | none: each product type has its own ad-hoc shape; the 24 models share column suffixes by naming convention (NR-10 name canon PROPOSED) | MISSING |
| Roles / security across data, logic, action, for humans AND agents | `APPROVED_BY` + `APPROVAL_MODE` (human_gui / ai_vision / ai_auto) on Stage-1 rows; stamps carry identity; producer ≠ verifier ≠ approver; the fully-AI approver identity (A16) pending; permission modes and three hooks | PARTIAL: the human/agent actor distinction exists on decisions, not on every action |
| "One unified reality", continuous sync | NOT one: products live in TWO roots (`sweep106` vs `convention_check`) resolved by `REVIEW_INDEX_106.md`; stale copies on read paths (NR-22/46); state is re-derived from disk on demand, not kept in sync | MISSING as a property; HAVE the resolver |
| Branching / change review of the ontology itself; schema migration | git for generators; superseded/quarantine dirs for products; the register's ID guard; no branch or migration for a table schema (columns grew by suffix; the R1 amendment forbids silent generations) | PARTIAL |
| Tool factory: tools for any human or any agent | the scripts + agent tool grants + skills; no tool that lets an agent QUERY our objects (an agent reads files) | PARTIAL |
| Ontology MCP: external agents read objects and execute predefined actions under the same controls | none: Codex gets a clean-room COPY of files (`dev/referee/`); no MCP over our catalogs, verdicts, register | MISSING — and the cleanest fit: an MCP server exposing burst / selection / block / fit / verdict / stamp / register objects and the few declared actions (present, approve, promote, invalidate) to Codex, referees, and Mode-A agents |
| Specialized expertise as shared infrastructure | the skills, the register, the lessons-as-tests, the PI rulings quoted verbatim | HAVE — this is what the whole project is |
| Decisions captured as edits | stamps + rulings + instances I-nn in the register; not a decision object with its inputs' hashes and the rule it discharged | PARTIAL |

## §15 What this adds to the two harness articles
Bowne-Anderson asked for telemetry; Böckeler for a view of guides and sensors as a system; the
Ontology page names the missing layer: **a typed object-and-action model of our own campaign**,
with actions as first-class, permissioned, captured primitives, and one reality that agents read
through tools rather than through file paths. Codex r2 already reached the same design from the
failures ("a relational action-rule registry rendered as schema-on-read views over canonical
files", typed edges applies-when / requires-before / verified-by / derived-from / invalidates).
So three independent sources point at one build: **the campaign ontology** = schemas for the
objects we already write, declared links, a handful of first-class actions with preflight and
receipts, roles on every action for human and agent actors, and an MCP over it for external
agents. It is the substrate the queue manager (A17) and the eval harness both need, and it is what
"turn specialized expertise into shared infrastructure" means for a physics pipeline.

## §16 Actions (PROPOSALS, in order)
1. **Schemas for what exists**: one JSON schema per object type we already write (selection,
   block, fit row, temporal row, stamp, receipt, sidecar, state, harvest paper, P0 item); a test
   that every file on disk validates (computational sensor, Böckeler).
2. **Declared links**: trigger, sha, commit — written as fields, not inferred; the state board
   reads them.
3. **First-class actions**: present, approve, promote, quarantine, invalidate, launch-producer,
   deliver — each with intent → preflight → commit → finalize, an actor (human | agent, model id),
   and a receipt (the ACTION_EVENT). This is also the telemetry (Part 1) and the did-it-fire ledger
   (Part 2).
4. **One reality**: retire the two-root split behind a single resolver object; stale copies become
   impossible by construction (NR-22/46).
5. **Ontology MCP for us**: expose objects + the declared actions to Codex, referees and Mode-A
   agents; the clean-room copy becomes a query.
6. **Roles on actions**: who may present, approve, promote — human or agent — the A16 decision
   made concrete.

---

# PART 4 — vs "Agent Harness: What It Is and How to Build One" (Sa Wang, PuppyGraph, 2026-07-01)

**Source:** https://www.puppygraph.com/blog/agent-harness (a graph-database vendor; the graph
claims are product positioning, noted as such). Its spine: the harness is "the software layer
around a large language model that turns it into a working agent"; five components that are
"not a menu" — context management (compaction, scoping, retrieval), tool execution in a sandbox,
filesystem/durable state, memory and search, guardrails/hooks/human-in-the-loop ("the strongest
guardrail of all"); four failure modes of long runs — error compounding (answer: verification
after consequential steps against an external signal), state loss (persist plans), no access to
ground truth ("treat a claim of success as a hypothesis to test, not a fact to accept"),
invisibility ("structured traces of every decision, tool call, and result"); the data layer:
relational questions are graph traversals, an ontology is "the schema the agent queries against"
AND "a grounding contract" — queries validated against it fail with "structured, machine-readable
feedback" the agent can repair; design backwards from "done"; an eval set with checkable outcomes
run on every change, "regressions as bugs rather than noise".

## §17 Their five components and four failure modes, ours

| item | ours | verdict |
|---|---|---|
| context management | compaction, scoping by skill-reader checklist, retrieval by reading the product first | HAVE |
| tool execution in a SANDBOX | producers run on the host; containment = permission modes + the raw-data hook; the Skeleton reserves "the real sandbox" for Mode A | PARTIAL |
| filesystem / durable state | the disk IS the state; state board derived from evidence | HAVE |
| memory and search | MEMORY.md + memsync, notes, grep, the prior-art-reader; corpus index by bibcode + theme; no vector store, no graph | HAVE for facts; relational questions ("which products derive from table X after amendment Y", "which rule has which sensor") are answered by grep and inventory agents | PARTIAL |
| guardrails, hooks, human-in-the-loop | three hooks; the PI at every gate; no fabricated approvals | HAVE |
| error compounding → verify consequential steps | verifier gates, sha-bound verdicts, the count-triple rule | HAVE |
| state loss → persist plans | dispatch plans, live report, stamps, receipts | HAVE |
| no ground truth → success is a hypothesis | our doctrine verbatim: never "I think it ran"; fresh-context verification; the anti-"I think it ran" state board | HAVE, stronger |
| invisibility → structured traces | none per decision/tool call/agent invocation | MISSING (fourth source to say so) |
| ontology as grounding contract with machine-readable validation | no schemas; contracts are prose (S-items, R-items) validated by humans or fresh agents, not by a validator | MISSING (= Part 3) |
| graph database / Graph RAG | Codex r1/r2 ruled tables + typed edges suffice at our scale (106 bursts, 47 rows, ~100 rules); a graph engine is the vendor's pitch, not our need. The one place the "connective structure, not similar passages" point is right for us is the LITERATURE (AstroGraph, Scholar bridging), not the pipeline | NOT NEEDED for the pipeline |
| design backwards from "done" | PRESENT→GATE per step; acceptance tests; ReportSpec | HAVE |
| eval set on every change, regressions as bugs | lessons-as-tests exist; not run as a unit on every change | PARTIAL |

# PART 5 — vs "How to Build a Custom Agent Harness" (Sydney Runkle, LangChain, 2026-06-03)

**Source:** https://www.langchain.com/blog/how-to-build-a-custom-agent-harness (product post
for `create_agent`; the middleware catalogue is marketing, the capability matrix is generic).
Spine: agent = model + harness; "the job of a harness is to provide context to the model at every
step"; product harnesses (Deep Agents, the Claude Agent SDK) vs a minimal loop + MIDDLEWARE at
six interception points (before/after model call, before/after tool call, startup, teardown);
four levers (deterministic logic at loop points, tool lifecycle, custom state, stream handlers
for audit logs/monitoring); a capability matrix (context overflow, memory read/writeback, act in
the environment, delegate + todo list, transient-failure retries/fallbacks, policies on every
call, steer/HITL, cost control: call limits + prompt caching); task-harness fit; reuse
battle-tested middleware across agents.

## §18 Their levers and matrix, ours

| item | ours | verdict |
|---|---|---|
| product harness + custom layer | Mode B = Claude Code (product) + our skills/agents/hooks on top; Mode A = the custom harness on the SDK, planned | HAVE (B), PLANNED (A) |
| middleware at six interception points | we use ONE: PreToolUse on Bash and SendUserFile; nothing after a tool call, around a model call, at startup or teardown | PARTIAL |
| deterministic logic at loop points | hooks only; the rest is prose | PARTIAL |
| tool lifecycle | per-agent tool grants; scripts | HAVE |
| custom state across hooks | burst state on disk; nothing in-loop | PARTIAL |
| stream handlers → audit log of tool calls, latency monitoring | none | MISSING (= telemetry, fifth source) |
| context overflow | compaction (harness) | HAVE |
| memory load at start, writeback at end | MEMORY.md at boot; memsync; skills | HAVE |
| act in the environment | shell + filesystem | HAVE |
| delegate + todo list | fresh-context sub-agents; the live report / state board as the todo list | HAVE |
| transient failures: retries, backoff, fallbacks | engine multistarts, the fit retry pool; no harness-level model retry/fallback (harness-provided) | PARTIAL |
| policies on every call | three hooks; PI approval; nothing for the other transitions | PARTIAL |
| steer / HITL | heavily | HAVE |
| cost control: call limits, tool-call limits, caching | none: unbounded verifier rounds; the paid Codex quota protected by a prose rule after a $100 burn | MISSING |
| task-harness fit | the harness is the walkthrough's shape | HAVE |
| reuse across agents/projects | skills + hooks copied to siblings; the FBOT copy inherited three pre-audit bugs | PARTIAL (copies, not versioned packages) |

---

# SYNTHESIS — across all five sources

## §19 What we ABSOLUTELY need and do not have (ranked by how many sources demand it and how cheap it is)

| # | need | asked by | our state | first move |
|---|---|---|---|---|
| 1 | **Structured traces per action and per agent invocation** (actor, model id, inputs' hashes, decision, verdict, tokens, wall time, cost) | all 5 (telemetry; did-it-fire; decision capture; invisibility; audit stream) | none on disk | the ACTION_EVENT record Codex specified: one line per invocation, appended by the session, later by the queue manager |
| 2 | **Model identity on every product + retest on model change** | Bowne-Anderson explicitly; implied by the other four ("the model is a fixed artifact you call") | no product names its model | `MODEL_ID` + harness version in stamps, sidecars, manifests; a keep-condition column in the register |
| 3 | **One eval battery run on every harness change and every model change** | 4 of 5 | tests + benchmark + known-results exist, never as one unit | one command over lessons-as-tests + known-results + the case-study cases; results sha-bound |
| 4 | **The campaign ontology**: schemas for the objects we already write, declared links, first-class actions with preflight → commit → receipt, roles for human and agent actors | Palantir, PuppyGraph (grounding contract), Böckeler (computational sensors), Codex r2 | objects typed, no schema; 2–3 actions first-class | JSON schema per object + a validation test; then the seven actions |
| 5 | **Caps and cost limits on every loop** | Bowne-Anderson, LangChain, PuppyGraph | only the referee loop is capped; Codex quota is prose | retry cap + escalation on figure/numbers rounds; a spend ledger for paid calls |
| 6 | **Computational sensors before inferential agents; a pre-commit gate; a drift janitor** | Böckeler, PuppyGraph | growth is inferential-heavy; no pre-commit; drift by hand | code the four countable step-6 auditors; pre-commit runs the 6-s suite; scheduled 36+43+read-path scan |
| 7 | **A sandbox for producers** | PuppyGraph, LangChain | host execution + raw-data hook | Mode A's container; until then, the raw-data hook stays the only containment |
| 8 | **Interception points beyond PreToolUse** | LangChain, Böckeler | one of six | PostToolUse for the audit line (= #1), Stop for the state board refresh |

Not needed at our scale, despite the sources: a graph database or Graph RAG for the pipeline
(Codex ruled; 106 bursts), a vector store (239 PDFs indexed by bibcode and theme), a managed
runtime. The graph point stands only for the literature side (AstroGraph).

## §20 What we have that is BETTER than any of the five

1. **Blind-first with reconciliation as a scientific method**: predictions frozen before the
   literature is read; every difference explained by ONE changed analysis choice; "the deliverable
   is a tested explanation, not an agreement score". No article has an equivalent.
2. **Verdicts bound to the artifact's hash and expiring on edit**, from a fresh-context verifier
   that never produced the thing it judges. The articles have verification loops and HITL; none
   binds the verdict to a sha.
3. **The human's words as the contract, quoted and dated**: S-items, R-items, rulings verbatim.
   Böckeler says correctness needs a human specification; we do it per step, systematically.
4. **The register**: every guard and agent carries the incident that bore it; distillation the
   same session; "a lesson is not learned until it exists as a claim and a test". Their steering
   loop, with provenance for every control — and 47 rows from 21 real bursts.
5. **Disk-derived state and identity-stamped approvals**: never "I think it ran"; a chat-only
   approval is recorded as a defect; approvals are never fabricated. Stricter than any HITL text.
6. **The blind three-referee panel with fixed temperaments and the two-hat separation**
   (supervisor with context vs cold referee without). Beyond "LLM as judge".
7. **A numbers discipline the articles do not know**: count coordinates (denominator, basis set,
   model), margins never absolutes, rails disclosed, four symbols (detection / estimate / upper
   limit / unconstrained), ties reported as ties. This is the science-specific behaviour harness.
8. **Honest limits stated on every gate**: UNVERIFIED-IN-CI, "consistency not truth", provisional
   by definition, the NO-EXCEPTION delivery rule, the register's PROPOSED vs DEPLOYED status.
9. **A mechanical no-ship gate at delivery** on top of the product harness's permission modes
   (PuppyGraph cites Claude Code's modes as the example; we added the product-specific gate).
10. **Design from 21 bursts of observed failure** rather than from a component list — the thing
    every one of the five articles says to do, done at scale.

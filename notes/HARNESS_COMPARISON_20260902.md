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

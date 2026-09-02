# THE WHOLE WORKFLOW AND THE NEED FOR EACH AGENT — 2026-09-02

**Why this document exists.** PI, 2026-09-02, verbatim: *"finally understand the whole
workflow and need of agents and merge some of them if they can act at same place with some
roles"*. This is program item 2, discussed AFTER the skills (item 1,
`notes/SKILLS_REVIEW_20260902.md`). Facts from a read-only inventory (fresh-context agent:
10 agent files, 3 hooks, settings.json, the three architecture docs, every orchestrator);
every fact carries a file:line. §5 holds the merge CANDIDATES; nothing is applied.

---

## §1 The ten agents on disk (`.claude/agents/`)

Nine of ten have identical tool grants (Read, Grep, Glob, Bash); only distiller adds
Edit + Write. All ten map to a lettered roster actor; there are no orphan files.

| agent | duty | fires at | register | reads | returns | fresh-context? | size / commit |
|---|---|---|---|---|---|---|---|
| skill-reader (A1) | opens every step with the binding checklist | every step open, MANDATORY (P9, AgentArchitecture.md:51) | unnumbered :134; NR-27 conflict-flag duty :161 **(no clause in the file)** | step skill, ledgers, VISION_QC, OPEN register rows | checklist only ("you produce nothing else" :14) | not stated | 1.0 KB / 08-16 |
| dispatcher (A2) | returns roster + gates + order for a task | task intake, MANDATORY (P9 :50) | NR-17 :155 | per-step roster + full register | DISPATCH_PLAN file in results/campaign/ | not stated | 1.6 KB / 08-21 |
| figure-verifier (A8) | fresh-context vision gate on every figure | steps 1, 7, 8; wf-gate | :129; NR-5 :144 | FigureVisionQC contract, same-run sidecar FIRST, the PNG | PASS / PASS-WITH-NITS / FAIL; orchestrator sha-binds into VISION_QC.md | YES | 1.5 KB / 08-29 |
| numbers-verifier (A9) | recomputes every number from the run's products | steps 1, 7; wf-gate; any numeric deliverable | :130; NR-44 screen :182 | tables + sidecars + catalogs, never prose | discrepancy report | **not stated** | 1.1 KB / 08-29 |
| tie-reporter (A6) | dAIC<2 heads reported as TIES | any model-selection reporting; wf-products | NR-3 :142; NR-42 basis label :180 | the run's spectral_fits table, stored AICs | TIE-CLEAN or rewording list | YES | 1.0 KB / 08-21 |
| seed-auditor (A5) | stochastic product records AND honours a seed | any MC product; wf-temporal, wf-products | NR-2 :141 | sidecar seed field, the RNG code path | SEEDED-REPRODUCIBLE / FAIL / DECEPTIVE PROVENANCE | YES | 1.0 KB / 08-21 |
| admission-gate (A4) | screens every row before a committed catalog | every catalog write; wf-fit, wf-promote | NR-4 :143; NR-32 :172 | candidate rows + engine diagnostics | ADMIT / REFUSE | YES | 1.7 KB / 08-29 |
| prior-art-reader (A13) | sweeps notes for existing proofs before any redo | before any root-cause; incident stage 1 | :139 | notes/, L-series, VISION_QC, sibling repos | ALREADY / PARTIALLY / OPEN | not stated | 1.0 KB / 08-21 |
| distiller (A14) | closes every incident into a lesson + register row | every incident; step 9; terminal stage of every failure class | :133; **owns the register** :119 | incident evidence, ledgers | **edits** skills, ledgers, contracts, register | no | 0.8 KB / 08-16 |
| port-verifier (A12) | numeric port check vs the SOURCE code | development / freeze time only | :136 (born L26) | source code + port | PORT-VERIFIED / PORT-REFUSED | YES | 1.0 KB / 08-21 |

Verbatim duplication: the four-question critic block is byte-identical in
figure-verifier.md:19–24 and numbers-verifier.md:13–18. The fresh-context precondition
sentence is byte-identical in four files and absent from five. No orchestrator invokes
any agent programmatically; all invocation is in-session (Mode B).

---

## §2 Named in the law, not on disk

| actor | where named | status |
|---|---|---|
| A7 NOTES-REVIEWERS (per-bin residual reading, steps 6/8) | AgentRoster.md:304–330; AgentArchitecture.md:94,131 | "workflow fan-out", no file |
| A10 NR-24 REPORT-CONFORMANCE GATE | AgentRoster.md:394–415 ("the one roster member NOT YET WRITTEN") | decision (a) approved creating it "today" (08-29); not created |
| A11 LITERATURE AGENT (step 9, blind-first) | AgentRoster.md:417–439 | protocol only |
| A15 EXTERNAL AUDITOR | AgentRoster.md:508–540 | Codex + dev/referee/ (NR-47), no file |
| A16 APPROVER (fully-AI mode) | AgentRoster.md:542–567; AgentArchitecture.md:137 | IDENTITY PENDING PI |
| A17 QUEUE MANAGER | AgentRoster.md:569–597 | "to be built TODAY" (08-29); FreshSessionBoot.md:160: not built |
| `.claude/workflows/` (11 wf-* files) | AgentSkeleton.md:78–109 | directory absent; every transition runs on the prototype shell chains |

Eleven register rows name a further "Missing agent": NR-28 (sha-equality item in A10),
NR-38 RULE-CONFORMANCE AUDITOR, NR-39 rationale guard (code), NR-40 METRIC-VALIDITY
AUDITOR, NR-41 CONSTRUCT-COVERAGE AUDITOR, NR-42 (folded into tie-reporter), NR-43
RAILED-PARAMETER DISCLOSURE AUDITOR, NR-44 (folded into numbers-verifier), NR-45
COUNT-TRIPLE VERIFIER, NR-46 read-path guard (code), NR-47 (none new).
AgentArchitecture.md:166–185.

---

## §3 Hooks (`.claude/settings.json`, three PreToolUse entries)

| hook | matcher | checks | enforces | known defects |
|---|---|---|---|---|
| no_unverified_figures.py | SendUserFile | sha of each .png vs every results/**/VISION_QC.md | :135, P1/P4, A3-E1 | .png only; exits 0 on malformed stdin; GitHub-release path uncovered (AgentRoster.md:174–177) |
| require_dispatch.py | Bash | regex on the COMMAND TEXT (line 9) + any DISPATCH_PLAN* newer than 24 h | P9 :44–55, NR-17, A3-E2 | **matches on mention, not execution**: blocked three read-only or write commands of the building session today (a git commit, a stat, a notes write) and one of the inventory agent's; fix "drafted but unapplied" (FreshSessionBoot.md:166–169). Under-covers four of five transitions (NR-30 :170). Freshness not task-bound: one plan opens every gate |
| protect_rawdata.py | Bash | rm / > / >> / mv on paths containing data/bn, unless the command also matches download/curl/wget/fetch | no register row; A3 addendum only (AgentRoster.md:730) | not in the A3 enforcer list E1–E3 |

Note: settings.json holds two separate blocks with the same "Bash" matcher (:13–21, :22–30).

---

## §4 The workflow as it actually runs (Mode B, prototype chains)

State machine S0–S12 + SX (AgentSkeleton.md:13–38), derived from disk by
`dev/agent_state.py`. Transitions run on shell/python prototypes, none of which invokes
an agent: the per-burst paper chain, `run_burst_agentic.sh`, the campaign products
driver, the campaign refit and retry-pool scripts, the 21-burst binner, and the five
runtime scripts under `notes/codex_campaign20_runtime/`. Agents are invoked only by the
session, by protocol. Stamps: `dev/live_report.py` (NR-18) writes APPROVALS.json and
routes feedback to the distiller; `dev/invalidate_downstream.py` (NR-19) demotes stamps
downstream of a change. The referee panel launcher (`dev/referee/`) is the one
orchestrator that calls an external actor, and it is PI-triggered.

### 4a Agent × moment matrix (● per roster/register; ○ per workflow position; ◍ incident-triggered; ✎ dev-time)

| agent | 0b | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | every delivery | every catalog write |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| skill-reader | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | | |
| dispatcher | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | | |
| figure-verifier | | | ● | | | | | ○ | ● | ● | ○ | ● | |
| numbers-verifier | | | ● | | | | | | ● | ○ | ○ | ● | |
| tie-reporter | | | | | | | | ○ | | ○ | ○ | | |
| seed-auditor | | | | | | | | | ○ | ○ | | | |
| admission-gate | | | | | | | | ○ | ○ | | | | ● |
| prior-art-reader | ◍ | ◍ | ◍ | ◍ | ◍ | ◍ | ◍ | ◍ | ◍ | ◍ | ◍ | | |
| distiller | ◍ | ◍ | ◍ | ◍ | ◍ | ◍ | ◍ | ◍ | ◍ | ◍ | ● | | |
| port-verifier | ✎ | ✎ | ✎ | ✎ | ✎ | ✎ | ✎ | ✎ | ✎ | ✎ | ✎ | | |
| notes-reviewers (no file) | | | | | | | | ● | | ● | | | |
| literature agent (no file) | | | | | | | | | | | ● | | |
| NR-24 gate / A10 (no file) | | | | | | | | | | | ○ | ● | |
| approver A16 (no file) | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | |

### 4b Same moment, several agents (facts)

| moment | agents |
|---|---|
| every step open / task intake | skill-reader AND dispatcher (both mandatory, P9) |
| step 1, step 7, wf-gate | figure-verifier AND numbers-verifier (+ NR-24 gate at wf-gate) |
| step 8 / wf-products | figure-verifier, notes-reviewers, tie-reporter, seed-auditor |
| wf-fit, wf-temporal | admission-gate + seed-auditor (+ code guards NR-1/9/10) |
| any incident | prior-art-reader THEN distiller |
| step 9 | literature agent, distiller, final approver |

### 4c Same input, several agents (facts)

| artifact | readers |
|---|---|
| spectral_fits.ecsv / stored AICs | tie-reporter, numbers-verifier, admission-gate, dev/model_preference.py, and the proposed NR-42/43/44/45 auditors |
| same-run sidecar JSON | figure-verifier, numbers-verifier, seed-auditor |
| the register | dispatcher, skill-reader, distiller |
| results/*/VISION_QC.md | figure-verifier (via orchestrator), skill-reader, prior-art-reader, the no-ship hook |
| engine rail/validity diagnostics | admission-gate, both verifiers' critic Q1, NR-43, model_preference.py |

---

## §5 Merge CANDIDATES — "act at the same place, with roles" (PROPOSALS, PI decides)

The facts in §4b–4c group the ten files plus the seven unbuilt actors into five
places. Each candidate is one agent definition with named ROLES (the PI's word); a role
is a section of the prompt the orchestrator selects, not a separate file. Where
independence matters (producer ≠ verifier), it is preserved because the merged agent is
never the producer.

| candidate | roles (from today's agents and unbuilt actors) | place | what it preserves | what changes |
|---|---|---|---|---|
| **C1 STEP-OPENER** | checklist (skill-reader) · roster/plan (dispatcher) · law-conflict flag (NR-27, unimplemented) | every step open / task intake | both mandatory P9 duties in one invocation | one file, one call per step instead of two; the plan and the checklist are written together |
| **C2 ARTIFACT-VERIFIER** | vision (figure-verifier) · numbers (numbers-verifier) · provenance/seed (seed-auditor; + NR-7 argv/sha) · report-conformance (A10/NR-24, unbuilt) · per-bin notes review (A7, unbuilt) | every delivery, wf-gate, steps 1/7/8 | fresh context; the byte-identical critic block becomes one block; same-run sidecar read once | five duties, one agent; the NR-24 gate finally exists as a role |
| **C3 FIT-TABLE AUDITOR** | admission (admission-gate) · tie/basis (tie-reporter + NR-42) · rails (NR-43) · margins (NR-44) · count-triple (NR-45) · construct coverage (NR-41) · metric validity (NR-40) | every read of spectral_fits.ecsv: wf-fit, wf-products, every catalog write, every PRESENT block with counts | all read the same table; none refits | the five PROPOSED step-6 auditors born on #21 become roles of one existing agent instead of five new files |
| **C4 INCIDENT AGENT** | prior-art (prior-art-reader) · distil (distiller) · rule-conformance audit (NR-38, unbuilt) | any incident, step 9 | the sequence prior-art → distil is the file's own order; Codex's condition "distiller separate from the failing actor" holds | write powers stay confined to the distil role |
| **C5 REFEREE PANEL** | T0 constructive · T1 standard · T2 adversary (already roles, dev/referee/BRIEF_T*.md) | milestones, PI-triggered | already the PI's design (NR-47) | nothing; listed to show the pattern is already in use |
| keep separate | port-verifier (dev-time, not pipeline); approver A16 (identity is the PI's decision); queue manager A17 (a process, not an agent) | | | |

Consequences to weigh (facts, not verdicts): (i) one agent with roles fires once per
place → fewer invocations, but a role omitted by the orchestrator is invisible unless
the role list is a mechanical checklist; (ii) Codex r2 §5 asks each obligation be pinned
to a PHASE (preflight/commit/finalize/present/approve) — roles map onto phases
naturally; (iii) the `.claude/agents` format allows one file per agent; role selection
is by prompt text, so the queue manager (unbuilt) or the session must name the role.

## §6 Decision log (appended as we go)
| when | item | PI ruling (verbatim) | applied in |
|---|---|---|---|

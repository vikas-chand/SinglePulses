# CODEX SUPERVISOR REVIEW — paper v3 spine and draft §3

**Review date:** 2026-09-02  
**Hat:** A15 SUPERVISOR (full-context auditor + brainstormer), not a blind-referee firing  
**Artifact reviewed:** `paper_agentic/v3/sec3_harness.tex`  
**Comparison baseline:** `paper_agentic/agentic_grb_v2.tex:202-504`  
**Repository inspected:** branch `memory-guard`, HEAD `1fc7a17f6560`; the draft/census references their own earlier provenance commits below

## VERDICT — DO NOT SIGN OFF

The new spine is the right one. “The harness, component by component” is clearer and more auditable for an ApJ/ApJS astronomy audience than v2’s interleaved “Agentic Workflow,” especially because the approved outline now separates anatomy (§3), lifecycle (§4), learning (§5), verification (§6), and actions (§7) (`paper_agentic/REWRITE_OUTLINE_v3.md:70-97`). The draft is also materially more legible than v2.

I would nevertheless **not sign off this version of §3**. Before it proceeds, five things must change:

1. Convert protocol requirements into requirement language and proposed controls into proposed language. The draft repeatedly says “is,” “every,” “never,” “automatically,” or “in production” where the evidence is a law file, an operator-invoked helper, a partial implementation, or a coarse roster status (`paper_agentic/v3/sec3_harness.tex:43-64,91-108,112-134,141-160`).
2. Correct the authority table. The fitting code—not the AI—computes fit validity and the validity-gated AIC/BIC winner (`scripts/10_spectral_fit_burst.py:1038-1082,1104-1128,1157-1163`), while Stage-1 selections may be human **or** AI-approved (`paper_agentic/T1_component_roster_DRAFT.md:49`).
3. Replace “at the census commit” with a reproducible **working-tree census** or add a hash manifest. Several counted products are under ignored `results/*` and therefore cannot be reconstructed from commit `4df6884` (`.gitignore:37-44`; `dev/ai_guides/ReportSpec.md:13-27`).
4. Correct the five-item proposed list and the definition of DEPLOYED. The roster’s five PROPOSED rows are not the five named by the prose (`paper_agentic/T1_component_roster_DRAFT.md:40,75,91-92,115`; `paper_agentic/v3/sec3_harness.tex:188-193`).
5. Define the nested product/repository harness and the agent/subagent relation before Figure 1, and give all five engineering sources explicit, accessible citations (`paper_agentic/v3/sec3_harness.tex:13-27`; `notes/HARNESS_COMPARISON_20260902.md:313-324,328-335`).

Those are repairable defects in the draft, not defects in the approved spine.

## Recomputed census used in this review

I did not accept the printed census as self-authenticating. I reran direct file/count queries and inspected the primary definitions.

| item | result | qualification and primary evidence |
|---|---:|---|
| Agent files | 10 | Nine declare `Read, Grep, Glob, Bash`; only the distiller adds `Edit, Write` (`.claude/agents/admission-gate.md:4`; `.claude/agents/dispatcher.md:4`; `.claude/agents/figure-verifier.md:4`; `.claude/agents/numbers-verifier.md:4`; `.claude/agents/port-verifier.md:4`; `.claude/agents/prior-art-reader.md:4`; `.claude/agents/seed-auditor.md:4`; `.claude/agents/skill-reader.md:4`; `.claude/agents/tie-reporter.md:4`; `.claude/agents/distiller.md:4`). |
| Armed hooks | 3 | All are `PreToolUse` entries (`.claude/settings.json:2-31`). Their actual scopes are PNG delivery, a regex-selected Bash producer set, and regex-selected raw-data shell writes (`.claude/hooks/no_unverified_figures.py:2-35`; `.claude/hooks/require_dispatch.py:2-22`; `.claude/hooks/protect_rawdata.py:2-15`). |
| Guide files | 27 | This is the count of Markdown files directly under `dev/ai_guides/`, not 27 per-step skills. The roster identifies ten step skills and records step 8’s `SEDPanels.md` as unwritten (`paper_agentic/T1_component_roster_DRAFT.md:59`). |
| Register rows | 49 numbered + 11 unnumbered | NR-11 is retired; the roster records this result and the earlier outlier (`paper_agentic/T1_component_roster_DRAFT.md:188-191`). |
| Schemas | 10 | Ten `*.schema.json` files exist, but the generic instance test covers seven file globs plus the action trace, skips absent classes, and exempts four known files (`tests/test_schemas.py:45-63,66-80,89-109`). |
| Tests under `tests/` | 134 items collected from 11 modules in the reviewed working tree | Recomputed with `/Users/salim/anaconda3/bin/python3 -m pytest --collect-only -q tests`. Repository-wide default collection is 199 items from 16 modules because five tracked modules under `notes/codex_campaign20_runtime/` contribute 65 more. The historical collected total is working-tree/product-dependent: the roster records four different same-day totals (`paper_agentic/T1_component_roster_DRAFT.md:183-187`), and a clean tree at `4df6884` does not reconstruct the ignored product population. |
| Burst-state files | 106 in the reviewed working tree | The board writes these files on invocation (`dev/agent_state.py:64-72`), while `results/*` is ignored (`.gitignore:37-44`); zero such files are in the commit tree at `4df6884`. This is not a commit-bound count. |
| Declared states | S0–S12 + SX = 14 | The skeleton declares all fourteen (`dev/ai_guides/AgentSkeleton.md:19-34`). The board implementation does not derive all fourteen: it starts at S1, approximates S9, jumps to S11 on any approved stamp, never returns S0 or S12, and labels receipt currency unverified (`dev/agent_state.py:17-62`). |
| Named workflows | 11 | The skeleton names eleven workflow files, covering S1→S10, S11→S12, and invalidation; it does not name S0→S1 or S10→S11 (`dev/ai_guides/AgentSkeleton.md:78-109`). `.claude/workflows/` and `dev/queue_manager.py` are absent (`paper_agentic/T1_component_roster_DRAFT.md:147-160`). |
| Spectral-model menu | 24 | The code defines 6 default + 2 shape + 16 high-energy specifications (`scripts/10_spectral_fit_burst.py:474-540,542-708`). The default is six; the 24-model menu is selected only by `--models highe`, DSBPL can be skipped, and unusable T_INT/bin plugins cause a skip (`scripts/10_spectral_fit_burst.py:723-725,1535-1580,1717-1761,1763-1815`). |
| T1 component rows | 49 total: 44 DEPLOYED + 5 PROPOSED under T1’s coarse convention | “DEPLOYED” means merely that a file **or product/ledger** exists, including protocol-only actors (`paper_agentic/T1_component_roster_DRAFT.md:20-25`). The five PROPOSED rows are queue manager + workflows, first-class actions, report-conformance gate, queued boundary build, and queued science-guard code (`paper_agentic/T1_component_roster_DRAFT.md:40,75,91-92,115`). |

## 1. Is the spine right?

### Answer

**Yes. Keep the new spine.** It carries the argument better than v2 because it lets an astronomer ask the operational questions in a natural order: what drives the loop, what code touches the data, what context constrains judgment, what persists, and what can stop an action. The outline then restores the temporal story in §4 rather than asking one section to be both a parts diagram and a lifecycle (`paper_agentic/REWRITE_OUTLINE_v3.md:70-83`).

V2 makes the reader alternate among the eleven-step science path, blind comparison, convergence, fitting methodology, role definitions, fan-out, authority, two planes, doctrine, and state machinery (`paper_agentic/agentic_grb_v2.tex:262-502`). That contains valuable material, but it is not a clean architecture explanation. The v3 partition is the better architecture.

The risk is that §3 becomes a software inventory. Prevent that with a short opening paragraph that defines the two nested harness layers and then gives the astronomer a two-sentence orientation to the eleven-step burst analysis. Each component subsection should close with one GRB-specific consequence (“this prevents an invalid fit from becoming a population count,” not merely “this component exists”). V2 already contains useful concrete scientific examples: the soft-burst validity-gate failure and the lag-sign/ported-routine episode (`paper_agentic/agentic_grb_v2.tex:547-576`).

The figure allocation supports this split: F1 is the §3 anatomy, F2 the §4 lifecycle, F4 the §5 steering loop, and F5 the §7 object/action topology (`paper_agentic/REWRITE_OUTLINE_v3.md:30-41`). Keep only F1 and a compact pointer to T1 in §3; otherwise the component spine will repeat the same inventory in prose, diagram, and table.

### What must survive from v2, and where it belongs

1. **The scientific meaning of the eleven steps** belongs primarily in §4, with a two-sentence preview in §3.1. V2 explains identity/circulars, literature harvest, data inventory, selection, binning, fitting, temporal analysis, SED panels, and QC in astronomer-readable terms (`paper_agentic/agentic_grb_v2.tex:264-288`). The current §3 names the eleven-step ledger but does not tell a first-year PhD what scientific journey it governs (`paper_agentic/v3/sec3_harness.tex:43-50`).

2. **P0 freezing and three-way mismatch attribution** belong in §6, not the component inventory. They are verification doctrine: freeze before comparison, then classify mismatch as we-wrong, they-wrong, or frame-difference (`paper_agentic/agentic_grb_v2.tex:290-301`; `paper_agentic/REWRITE_OUTLINE_v3.md:90-92`). The conversion of an attributed failure into a lesson/test then belongs in §5 (`paper_agentic/REWRITE_OUTLINE_v3.md:85-88`).

3. **The K-clean/freeze/full-sweep rule** belongs in §5/F4 as a design and exit condition, with an explicit “not yet exercised” label. V2 states it as an operating condition (`paper_agentic/agentic_grb_v2.tex:303-310`), while the approved v3 decision log expressly says K/freeze remains unexercised (`paper_agentic/REWRITE_OUTLINE_v3.md:133-134`).

4. **The detailed fitting rules and fit-step figure** belong in §4/F3: inclusion by data quality, unconditional multistarts, physical-validity gates, and evidence-margin semantics (`paper_agentic/agentic_grb_v2.tex:312-340`; `paper_agentic/REWRITE_OUTLINE_v3.md:79-83`). §3.2 should only identify the engine and its deterministic/interpretive boundary.

5. **The operational specialist definition** should survive near the start of §3.3: role contract + required skill material + tool grant, followed by the point that specialization lies in interpreting domain outputs, not merely invoking code (`paper_agentic/agentic_grb_v2.tex:342-357,390-400`). This is clearer for physicists than starting with “context is what the model sees” (`paper_agentic/v3/sec3_harness.tex:89-108`).

6. **Fan-out, fresh-context verification, hash-bound verdict, and reassembly** should be split: the sequence belongs in §4; the epistemic reason and artifact-currency rule belong in §6 (`paper_agentic/agentic_grb_v2.tex:359-371,401-404`; `paper_agentic/REWRITE_OUTLINE_v3.md:79-92`).

7. **Failure behavior** needs one plain sentence in §3.1 (“failures have typed outcomes; warnings alone do not count as handling”), with the full taxonomy held for §10 as the outline specifies (`paper_agentic/agentic_grb_v2.tex:464-476`; `paper_agentic/REWRITE_OUTLINE_v3.md:101-108`).

### Doctrine, two planes, and operating skeleton

- **Doctrine:** the draft comment says “The doctrine → §5” (`paper_agentic/v3/sec3_harness.tex:6-9`), but the approved outline assigns Verification Doctrine to §6 (`paper_agentic/REWRITE_OUTLINE_v3.md:90-92`). Split it by function: fit inclusion/model rules → §4; lessons-as-tests and enforcement hierarchy → §5; blind-first, source verification, primitive-level comparison, and fresh-context verdicts → §6; no-silent-approval authority → §3.5. That is more coherent than moving all seven v2 rules together (`paper_agentic/agentic_grb_v2.tex:447-462`).

- **Two planes:** the authority table currently uses “discovery plane” before defining it (`paper_agentic/v3/sec3_harness.tex:162-182`). Put a two- or three-sentence production-plane/discovery-plane definition immediately before that table, because the term affects who may promote a claim. Put the full post-selection/calibration/promotion logic in §6 and the typed action mechanics in §7. V2’s concise explanation is worth preserving (`paper_agentic/agentic_grb_v2.tex:436-445`).

- **Operating skeleton:** retain the state model in §3.1, live stamps/receipts/invalidation in §3.4, hooks and approval authority in §3.5, and move the register, enforcement hierarchy, and lessons-as-tests to §5. The full failure taxonomy belongs in §10 (`paper_agentic/agentic_grb_v2.tex:464-502`; `paper_agentic/REWRITE_OUTLINE_v3.md:70-108`).

One readability defect remains: the tools paragraph is effectively a catalogue-length sentence (`paper_agentic/v3/sec3_harness.tex:68-87`). Split it into one sentence per producer class, with the status qualifier adjacent to the producer it qualifies.

## 2. OVERCLAIMS

Below, each quoted claim is stronger than the primary evidence permits. The replacement text is intended to be paste-ready.

### O1 — the bare model is described too absolutely

**Draft (`paper_agentic/v3/sec3_harness.tex:13-16`):**

> “The model is the language model we call; it reasons, and it has no memory between calls and no way to check its own claims against the world.”

The relevant distinction is between a bare call and the context/tools supplied around it. The current deployment’s hosted harness does manage and compact conversational context (`paper_agentic/v3/sec3_harness.tex:43-46`); the repository comparison likewise attributes compaction and memory interfaces to the product/custom harness combination (`notes/HARNESS_COMPARISON_20260902.md:313-324,328-337`). “No way” is therefore false unless “bare call” and “directly” are explicit.

**Exact rewording:**

> “A bare language-model call does not retain project state across calls or directly observe external state; it can test external claims only through the context and tools supplied by a harness.”

### O2 — five sources are said to converge on Bowne-Anderson’s exact five jobs

**Draft (`paper_agentic/v3/sec3_harness.tex:16-22`):**

> “Recent engineering accounts of agent harnesses … converge on five runtime jobs: run the reasoning loop, execute tools, assemble and manage context, persist state, and enforce boundaries.”

The five-job list is Bowne-Anderson’s taxonomy (`notes/HARNESS_COMPARISON_20260902.md:10-25`). Böckeler contributes guides/sensors and computational/inferential controls (`notes/HARNESS_COMPARISON_20260902.md:128-144`); LangChain contributes model–harness layering and lifecycle interception points (`notes/HARNESS_COMPARISON_20260902.md:313-324`). Palantir supplies an object/action/security analogy, not the same five-job taxonomy. Calling this convergence erases genuine differences among the sources.

**Exact rewording:**

> “We organize the section with Bowne-Anderson’s five-job runtime taxonomy—reasoning loop, tool execution, context management, persistent state, and boundaries—and use complementary concepts from Böckeler (guides and sensors), Palantir (typed objects and actions), PuppyGraph (long-horizon failure modes), and Runkle (model–harness layering and lifecycle interception points).”

### O3 — Figure 1/T1 status and provenance are stronger than the census convention

**Draft (`paper_agentic/v3/sec3_harness.tex:22-27`):**

> “Figure 1 lays our system out under those five jobs, drawing each component solid where it exists on disk and dashed where it is only proposed. Table T1 … states the work of every component in one sentence, with its origin quoted and dated. The counts in this section are taken at one commit … and will move; the roster says which commit.”

T1 defines DEPLOYED permissively: a file **or product/ledger** may suffice, including protocol actors without agent files (`paper_agentic/T1_component_roster_DRAFT.md:20-25`). Four origins are explicitly missing or undated (`paper_agentic/T1_component_roster_DRAFT.md:192-194`), and the generated TeX omits the origin column entirely (`paper_agentic/v3/tab_T1_roster.tex:3-6`). Product counts under ignored `results/*` cannot be reconstructed from the commit alone (`.gitignore:37-44`).

**Exact rewording:**

> “Figure 1 uses T1’s census convention: solid means that a corresponding file or recorded product existed in the 2026-09-02 working tree; dashed means proposed. Table T1 summarizes every roster row; its source roster records an origin where one is known. Code was pinned at commit 4df6884; counts of ignored products require the accompanying census manifest and hashes.”

### O4 — the figure caption universalizes gate coverage

**Draft (`paper_agentic/v3/sec3_harness.tex:32-37`):**

> “Solid boxes exist on disk at the census commit; dashed boxes are proposed in the requirements register but not yet built. The human gate stamps every step with an identity; approvals are never generated on the human’s behalf.”

The commit qualification fails for ignored products, as above. More importantly, T1 records that only one of two live reports has an `APPROVALS.json` file (`paper_agentic/T1_component_roster_DRAFT.md:69-70`), so “stamps every step” is a protocol requirement, not demonstrated universal coverage. Stage 1 may be human- or AI-approved (`paper_agentic/T1_component_roster_DRAFT.md:49`).

**Exact rewording:**

> “Solid boxes satisfy T1’s file-or-recorded-product convention in the census working tree; dashed boxes are proposed. The protocol requires every gate to carry an approver identity, but current stamp coverage is incomplete and Stage-1 approval may be human or AI.”

### O5 — Mode B is called disk-only stateful, and protocol invocation is presented as mechanism

**Draft (`paper_agentic/v3/sec3_harness.tex:43-56`):**

> “The per-burst protocol drives that loop: each of the eleven steps … is run, presented … gated, compared with the literature … and distilled before the next step starts. A dispatcher reads each task and the requirements register at intake and returns the agents, gates, and order the task requires … The loop is stateful only through the disk: a burst occupies one of fourteen typed states … and the state is derived from the products on disk at read time, never asserted by the session.”

The protocol specifies the sequence, but in Mode B its invocation is socially enforced and checklist compliance is unaudited (`dev/ai_guides/AgentRoster.md:81-99`). It requires PRESENT to contain four **things**, not four sentences (`dev/ai_guides/BurstWalkthrough.md:23-35`). The hosted harness itself carries conversational context (`paper_agentic/v3/sec3_harness.tex:43-46`), so only **durable cross-session scientific state** is intended to be disk-backed. The skeleton specifies fourteen states (`dev/ai_guides/AgentSkeleton.md:19-34`), but the current board implements a partial heuristic and leaves currency unverified (`dev/agent_state.py:17-62`).

**Exact rewording:**

> “The protocol requires each ledger step to follow RUN→PRESENT→GATE→LITERATURE→DISTILL, and it calls for a dispatcher at task intake. In the current interactive deployment these invocations are procedural rather than automatically scheduled. The hosted harness retains and compacts in-session context; durable cross-session scientific state is intended to reside on disk. The skeleton specifies S0–S12 plus SX, while the present board derives a partial operational state from selected disk evidence and does not yet implement every declared state or verify product currency.”

### O6 — eleven workflows do not cover every state transition

**Draft (`paper_agentic/v3/sec3_harness.tex:58-64`):**

> “the eleven typed workflows … would run each state transition as a fixed sequence … transitions run today on prototype shell chains that invoke no agent.”

The skeleton names eleven workflows for S1→S10, S11→S12, and invalidation, omitting S0→S1 and S10→S11 (`dev/ai_guides/AgentSkeleton.md:91-109`). The “no agent” statement is supported for the prototype-chain roster row (`paper_agentic/T1_component_roster_DRAFT.md:40-41`).

**Exact rewording:**

> “The skeleton specifies eleven workflow files for S1→S10, S11→S12, and invalidation; these files and the queue manager are not built. The corresponding computational stages currently run through prototype shell/Python chains that invoke no agent.”

### O7 — the engine does not fit 24 models to every bin and T_INT unconditionally

**Draft (`paper_agentic/v3/sec3_harness.tex:68-74`):**

> “the spectral engine, which fits twenty-four models to every time bin and to the integrated window and writes a validity flag, the bound-pinning diagnostics, and the information criteria for each”

The 24-model menu exists as 6 default + 2 shape + 16 high-energy specifications (`scripts/10_spectral_fit_burst.py:474-540,542-708`), but the default is six and 24 requires `--models highe`; DSBPL may be skipped (`scripts/10_spectral_fit_burst.py:723-725,1535-1580`). T_INT and bins with no usable plugins are skipped (`scripts/10_spectral_fit_burst.py:1717-1761,1763-1815`). Per-model status, validity, AIC, and BIC are written (`scripts/10_spectral_fit_burst.py:834-856`), while some rail diagnostics are row-level and nuisance-rail coverage remains partial (`scripts/10_spectral_fit_burst.py:1452-1508`; `paper_agentic/T1_component_roster_DRAFT.md:112`). Figure 1 repeats the same overclaim (`paper_agentic/figures/fig_F1_harness_anatomy.tex:39`).

**Exact rewording:**

> “The engine defines a 24-model menu (six default, two shape variants, and sixteen high-energy extensions). With `--models highe`, it attempts that menu for each usable time bin and, when plugins can be built, for the integrated interval; it writes per-model status, validity, AIC, and BIC together with selected row-level rail diagnostics.”

### O8 — “brightest detector” omits the approved-detector fallback

**Draft (`paper_agentic/v3/sec3_harness.tex:74-76`):**

> “the adaptive binning tool, which cuts the brightest detector’s light curve into Bayesian blocks”

The implementation uses the catalog-brightest detector only if it is among the approved NaIs; otherwise it chooses the approved NaI with the most TTE counts between its own approved pre- and post-background intervals (`scripts/27b_reblock_3ml.py:158-193`).

**Exact rewording:**

> “the adaptive binning tool, which forms Bayesian blocks from the catalog-brightest approved NaI, or otherwise from the approved NaI with the most TTE counts between its own approved pre- and post-background intervals”

### O9 — the lag routine’s direct import does not establish validation or revision identity

**Draft (`paper_agentic/v3/sec3_harness.tex:79-82`):**

> “the temporal chain, which measures durations, the minimum variability timescale, and the spectral lag from the same approved selections and imports the lag routine we validated in an earlier project unmodified”

The implementation directly imports `s02c_spectral_lag` from a mutable absolute path in the earlier project (`scripts/47c_lag_latbright.py:26-29,44-56`). That proves a direct import rather than a copied port; it does not prove that the imported revision was the validated revision or that it remains unchanged, because no source hash is pinned here.

**Exact rewording:**

> “the temporal chain, which measures durations, the minimum variability timescale, and spectral lag from the approved selections and directly imports the earlier-project lag routine; the reproducibility record should pin the imported file’s revision”

### O10 — the entire SED “family” does not refuse every mismatch

**Draft (`paper_agentic/v3/sec3_harness.tex:82-85`):**

> “the spectral-energy panel family, which renders each bin under the display semantics of the standard X-ray fitting package and refuses any panel that disagrees with the stored fit”

The current `41c` path retries a live fit, then a frozen replay, and refuses only if neither reproduces the stored AIC within 0.1 (`scripts/41c_paper_sed.py:315-351`). The legacy panel path merely prints a mismatch stamp above a threshold (`scripts/41_nuFnu_panels.py:303-308`), and the montage makes explicit placeholders for missing/refused panels (`scripts/41e_sed_montage.py:62-71,117-140`).

**Exact rewording:**

> “the current paper-SED producer, which renders each usable bin under XSPEC-like display semantics, retries a drifted live solution as a frozen replay, and refuses the panel if neither reconstruction agrees with the stored AIC within 0.1; legacy and montage paths instead stamp or display the mismatch explicitly.”

### O11 — 27 guides are conflated with ten step skills, and automatic reading is overstated

**Draft (`paper_agentic/v3/sec3_harness.tex:91-108`):**

> “durable knowledge lives in files the model reads on demand, chiefly twenty-seven skill documents indexed by the burst ledger, each carrying its criteria, its checklist, and its numbered lessons with a prefix unique to the file … every verification runs in a fresh context … The skill reader … opens every step by reading the step’s skill document, its defect ledger, and the open register rows … Cross-session memory is … read at the start of every session and updated by a consolidation step”

There are 27 guide files but ten ledger-indexed step skills; step 8’s intended `SEDPanels.md` is absent (`paper_agentic/T1_component_roster_DRAFT.md:59,160`). The skill-reader and fresh-context rules are Mode-B protocol whose invocation/compliance is socially enforced, not an automatic workflow property (`dev/ai_guides/AgentRoster.md:81-99`). Durable memory files exist, but the cited roster does not establish universal read/writeback on every session (`paper_agentic/T1_component_roster_DRAFT.md:61`).

**Exact rewording:**

> “Durable guidance lives in 27 files under `dev/ai_guides/`, including ten step skills indexed by the ledger; the intended step-8 SED skill is not yet written. The protocol requires fresh-context verification and calls the skill-reader at each step opening to return the applicable checklist, although automatic invocation and downstream checklist auditing await the typed workflows. Cross-session facts are stored in indexed files that the fresh-session protocol instructs the operator to read and consolidate.”

### O12 — the state board is not proof that all declared state semantics held

**Draft (`paper_agentic/v3/sec3_harness.tex:112-116`):**

> “Its state board is computed from the files on disk for all one hundred and six bursts, so the board cannot say a step ran when its products are absent. Every step gate leaves an approval stamp … and the live report is assembled only from stamps and products it can link.”

The board checks selected path existence and uses approximations; for example S9 is inferred from the string `NR-24`, S11 from any approved stamp, and receipt currency is explicitly unverified (`dev/agent_state.py:38-62`). It also creates/refreshes the 106 state files itself (`dev/agent_state.py:64-72`). T1 records incomplete approval-file coverage (`paper_agentic/T1_component_roster_DRAFT.md:69-70`).

**Exact rewording:**

> “The current board computes a working status index for 106 catalogued bursts from selected files on disk; it is useful for finding absent evidence but does not yet implement every declared state or prove hash currency. The protocol requires identity-bound gate stamps, and the live-report tool links the stamps and evidence it knows how to locate; stamp coverage is not yet complete.”

### O13 — invalidation is operator-invoked, coarse, and not an automatic dependency graph

**Draft (`paper_agentic/v3/sec3_harness.tex:117-124`):**

> “Approvals are revocable by machine: when an upstream decision is amended, a cascade demotes every downstream approval that depended on it, and reinstatement requires a human ruling with evidence. Both directions have operated in production. The cascade exposed an approval that had been given in conversation but never stamped … a demoted binning approval was reinstated only on proof … its block table byte-identical.”

The tool is explicitly invoked, dry-run by default, and clears selected markers while marking **all later** approved steps stale rather than resolving an encoded dependency graph (`dev/invalidate_downstream.py:1-10,17-43,45-84`). The live report prints a reminder to run it (`dev/live_report.py:127-131`). Reapproval requires a supplied identity string, but the code does not validate an evidence object for approval (`dev/live_report.py:155-160`). The two historical incidents cannot be verified from the permitted artifact set for this review.

**Exact rewording:**

> “An operator-invoked invalidation tool can mark later approvals STALE and clear selected downstream completion markers; it is dry-run by default and does not yet encode a complete dependency graph. The protocol requires evidence before reinstatement. Two reported walkthrough cases—a delayed stamp and an evidence-based reinstatement—belong in §9 and should be retained only if the underlying approval record and both compared hashes are cited.”

Remove `\prov` from “byte-identical” unless it points to the two actual hashes and comparison record; `\prov` is being used there as a generic authority marker rather than a census count (`paper_agentic/v3/sec3_harness.tex:124`).

### O14 — content-hash/generator binding is not universal

**Draft (`paper_agentic/v3/sec3_harness.tex:126-130`):**

> “Products bind to their inputs by content hash and to their generators by commit: a promotion receipt records the hash of the staged and promoted tables, a sidecar beside every fit table records the detectors, ranges, and convention in force, and a commit pin fixes the generator code for the campaign.”

T1 records seven promotion receipts across six bursts and says argv/environment recording and fit-table-sha binding remain proposed (`paper_agentic/T1_component_roster_DRAFT.md:27,69-73`). The report contract also describes generator cleanliness, fit-table binding, and pin location as incomplete or queued (`dev/ai_guides/ReportSpec.md:13-27`).

**Exact rewording:**

> “For covered products, promotion receipts record staged and promoted table hashes, fit sidecars record selected run metadata, and a campaign commit pin records the intended generator revision. Coverage is partial: only six bursts currently have promotion receipts, and complete argv/environment and report-to-fit-table hash binding remain proposed.”

### O15 — schema validation is narrower than “every instance on disk”

**Draft (`paper_agentic/v3/sec3_harness.tex:130-134`):**

> “ten of the object types the pipeline writes carry a JSON schema, and a test validates every instance on disk against it; the first run of that test found the literature-harvest manifests spelling their paper list under four different keys and two malformed bibliographic codes”

Ten schemas exist, but the generic test enumerates seven globbed object classes plus an action-trace test, skips classes with no instances, and permits four named deviations (`tests/test_schemas.py:45-63,66-80,89-109`). The harvest schemas record four legacy list keys and the measured field census, while the test names the two malformed bibliography records; write-time harvest validation remains proposed (`dev/schemas/harvest_manifest.schema.json:68-82`; `dev/schemas/harvest_paper.schema.json:94-100`; `tests/test_schemas.py:45-53`; `dev/ai_guides/AgentArchitecture.md:192`).

**Exact rewording:**

> “Ten JSON schemas are present. The current test validates seven globbed object classes and the action trace when instances exist, while ledgering four known legacy deviations. That audit exposed four harvest-list key spellings and two malformed bibliographic identifiers; write-time validation of new harvest manifests remains proposed.”

### O16 — the hook descriptions omit their matcher and regex limits

**Draft (`paper_agentic/v3/sec3_harness.tex:141-151`):**

> “Boundaries are enforced at the strongest layer that can hold them. … no figure reaches the human unless its hash appears in a verification ledger; no pipeline producer launches without a dispatch plan younger than a day; and raw data cannot be deleted or overwritten by a shell command. … Everything the hooks do not cover is enforced by fresh-context agents and, weakest of all, by prose.”

The first hook sees only PNG files passed through `SendUserFile` (`.claude/settings.json:3-12`; `.claude/hooks/no_unverified_figures.py:2-20`). The dispatch hook matches a finite regex over Bash command text (`.claude/hooks/require_dispatch.py:2-22`) and currently covers one of five pipeline transitions (`dev/ai_guides/AgentArchitecture.md:175`; `paper_agentic/T1_component_roster_DRAFT.md:82`); the boot guide records false blocks caused by textual matching (`dev/ai_guides/FreshSessionBoot.md:167-169`). The raw-data hook is a regex with acquisition exemptions, not a filesystem policy (`.claude/hooks/protect_rawdata.py:2-15`). Several uncovered controls are merely proposed, so “is enforced” is not supportable (`paper_agentic/T1_component_roster_DRAFT.md:91-92,115`).

**Exact rewording:**

> “The design principle is to place each boundary at the strongest feasible layer; current controls range from hooks to role prompts and prose, with explicit gaps. Three PreToolUse hooks inspect selected calls. One checks PNGs passed through `SendUserFile` against VISION_QC hashes; one checks a regex-selected subset of Bash producer commands for a dispatch plan younger than 24 h; and one rejects regex-matched delete/overwrite commands under `data/bn*`, with acquisition commands exempt. Outside those matchers, controls range from fresh-context review to prose requirements, and several planned boundaries are not yet implemented.”

### O17 — role separation is procedural in Mode B, and the approver is not always human

**Draft (`paper_agentic/v3/sec3_harness.tex:153-160`):**

> “Roles are separated by construction. The producer of an artifact never verifies it, the verifier never approves it, and the approver is the human at every step gate. Four kinds of actor appear in the action record …”

In Mode B, roster invocation is socially enforced and audited after the fact (`dev/ai_guides/AgentRoster.md:81-99`), so separation is a protocol design, not always construction. Stage-1 approval can be human or AI (`paper_agentic/T1_component_roster_DRAFT.md:49`). The action schema permits four actor kinds (`dev/action_event.py:48-51`), but automatic event emission is not wired (`dev/action_event.py:29-31`), and provenance fields may honestly be `unknown` (`dev/provenance_stamp.py:38-49`).

**Exact rewording:**

> “The protocol assigns production, verification, and approval to separate roles; typed workflows would enforce that separation structurally, but the current interactive deployment invokes it procedurally. Stage-1 approval may be human or AI and is stamped accordingly. In the current human-gated walkthrough, the PI approves later gates; in a fully AI-run report, the documented protocol assigns them to an independent non-producer AI. The action-event schema permits human, agent, hook, and script actors, although automatic capture is not yet wired and unavailable identity fields are recorded as `unknown`.”

### O18 — the authority table assigns deterministic code decisions to the AI

**Draft (`paper_agentic/v3/sec3_harness.tex:162-182`):**

> “the AI decides … model winner via the gated comparison … fit-validity verdicts”

The engine computes physical validity and selects the validity-gated AIC/BIC winner (`scripts/10_spectral_fit_burst.py:1038-1082,1104-1128,1157-1163`). The AI may audit, interpret margin language, attribute mismatches, or escalate anomalies; it does not decide those stored engine fields. The table also says the human decides every Stage-1 selection, contrary to the Stage-1 human-or-AI path (`paper_agentic/T1_component_roster_DRAFT.md:49`). “Discovery plane” is used before it is defined (`paper_agentic/v3/sec3_harness.tex:170`).

**Exact fix:** replace the first two AI cells with “audits the code-computed comparison; frames supported interpretation” and “checks validity outputs and flags anomalies”; replace the Stage-1 human cell with “Stage-1 selection when run in the human arm; acceptance of AI-arm selection”; define production/discovery planes immediately before the table using the logic at `paper_agentic/agentic_grb_v2.tex:436-445`.

Replace the following prose (`paper_agentic/v3/sec3_harness.tex:174-182`) with:

> “The workflow and deterministic engine decide what has been fixed in advance: step order, energy selections, fit statistic, multistart seeds, physical-validity flags, and the validity-gated AIC/BIC ranking. The AI audits those outputs, verifies sources and frames, proposes mismatch attributions, drafts lessons, and escalates anomalies within declared bounds. In the current human-gated walkthrough, the PI sets scope, gates each step, decides whether lessons enter the library, declares convergence and freeze, and owns every released scientific claim; in a fully AI-run report, the documented protocol assigns intermediate gates to an independent non-producer AI.”

### O19 — the approval-history universal is unaudited and `\prov` cannot support it

**Draft (`paper_agentic/v3/sec3_harness.tex:183-186`):**

> “In all operation to date, no approval has been generated by the system on the human’s behalf; the reverse, the human overruling the agent’s proposal, occurred repeatedly and is part of the record.”

The live-report CLI requires a nonempty `--by`, but it accepts an unauthenticated string (`dev/live_report.py:155-160`). The allowed artifacts do not establish “all operation to date” or the frequency “repeatedly.” `\prov` is not a substitute for a ledger census here. One founding human–agent divergence is recorded for the divergence learner (`paper_agentic/T1_component_roster_DRAFT.md:104`).

**Exact rewording:**

> “The protocol forbids fabricating a human approval, and the live-report CLI refuses an approval without a supplied identity. At least one human–agent divergence is recorded in the requirements register; §9 should report the full override count only after a ledger-defined census with denominator and date.”

### O20 — the 44/49 count is coarse, and the five missing components are named incorrectly

**Draft (`paper_agentic/v3/sec3_harness.tex:188-193`):**

> “forty-four of forty-nine components exist on disk and five are proposed … The queue manager, the workflows, the report-conformance gate, the first-class actions, and the loop caps are all of that kind.”

Under T1’s coarse convention, 44/49 is reproducible. But queue manager + workflow set is **one** roster row, and “loop caps” is only one part of the broader queued-boundary row. The omitted fifth row is queued science-guard code (`paper_agentic/T1_component_roster_DRAFT.md:40,75,91-92,115`). Several DEPLOYED rows also contain proposed subfeatures (`paper_agentic/T1_component_roster_DRAFT.md:51,53,71,73,82,110,112`).

**Exact rewording:**

> “Under T1’s file-or-recorded-product convention, 44 of 49 roster rows are classified DEPLOYED and five PROPOSED. The five proposed rows are: queue manager plus typed workflows; first-class action wrappers; the report-conformance gate; the queued boundary package (loop caps, spend ledger, additional hook points, pre-commit checks, and sandbox); and queued science guards. Several DEPLOYED rows remain partial, as T1 records in their status notes.”

## 3. Vocabulary

“Agent = model + harness” is a useful engineering slogan, but it is not a sufficiently precise governing definition for this astronomy paper. The repository has a hosted product harness, a repository-specific harness nested inside it, named agent roles, and subagent invocations; using “agent” for their sum and again for a child role creates recursion rather than clarity. The project’s own comparison already distinguishes product harness + custom layer (`notes/HARNESS_COMPARISON_20260902.md:313-324,328-335`), while the skeleton says subagents are fresh-context, bounded contract instances rather than personas (`dev/ai_guides/AgentSkeleton.md:119-131`).

I recommend replacing the first paragraph with:

> “We distinguish the **language model** from the **spectral models** fitted to the data. The hosted coding product supplies the runtime loop, tool calls, context compaction, and permissions; the repository adds GRB-specific tools, instructions, state records, and gates. We call the combination the **GRB analysis harness**. An **agent invocation** is the language model executing one named role with specified context and tool permissions. A **subagent** is a separately invoked, fresh-context role instance that returns a bounded result to the supervising session.”

That paragraph must appear before Figure 1; at present the nested layers are introduced only later through Mode B (`paper_agentic/v3/sec3_harness.tex:13-31,43-46`).

Term-by-term judgment:

- **model:** use “language model” on every potentially ambiguous first mention and “spectral model” in the science sections. Astronomy readers will otherwise read “model winner” as the spectral model, while “model identity” elsewhere means the LLM (`paper_agentic/v3/sec3_harness.tex:13-15,166-179`).
- **harness:** keep. Define both layers once: hosted/product harness and repository/GRB harness. The project’s source synthesis explicitly identifies that nesting (`notes/HARNESS_COMPARISON_20260902.md:313-324,328-335`).
- **agent:** keep only after defining it as an invocation in a named role. Avoid treating it as an enduring autonomous scientist; the operational unit is a role contract + skills + tool grant (`paper_agentic/agentic_grb_v2.tex:342-357`).
- **subagent:** define as a separate fresh-context invocation with a bounded return, not as an “independent opinion.” The skeleton states that fresh contexts are a context-control mechanism (`dev/ai_guides/AgentSkeleton.md:119-131`), and v2 itself warns that shared primitives can make many agents one correlated opinion (`paper_agentic/agentic_grb_v2.tex:640-651`).
- **Mode B:** replace in the paper with “the current interactive deployment (internal label Mode B)” on first use. T1 currently names Claude Code explicitly (`paper_agentic/T1_component_roster_DRAFT.md:37`); whether the manuscript names the vendor should be a reproducibility decision, not an unexplained internal mode label.
- **guide:** keep; define as a pre-action instruction or feed-forward control. **Sensor:** first use should be “verification check (‘sensor’)” because an astronomer will initially expect an instrument detector. Böckeler’s guide/sensor and computational/inferential distinction is the actual source of this vocabulary (`notes/HARNESS_COMPARISON_20260902.md:128-144`).
- **computational / inferential:** in running prose prefer “code-based check” and “language-model judgment” (or “human judgment”). Retain the compact labels in tables after defining them once. “Inferential” otherwise overlaps with scientific inference.
- **action:** until §7, use “recorded operation.” The generic first-class action wrapper is still PROPOSED (`paper_agentic/T1_component_roster_DRAFT.md:75`); calling every operation an action beforehand makes the proposed ontology sound deployed.
- **receipt:** define as “a machine-readable change or promotion record containing input/output hashes.” Do not imply universal coverage; only six bursts have promotion receipts in the roster census (`paper_agentic/T1_component_roster_DRAFT.md:27,71`).
- **stamp:** reserve for an identity-bound gate decision. Use “flag” or “annotation” for fit rails, edge conditions, or panel mismatches (`paper_agentic/T1_component_roster_DRAFT.md:112`). That separation prevents a diagnostic mark from sounding like an approval.

## 4. Citing blog posts

AAS permits mutable posts of this kind to be cited in footnotes at first mention, but the footnote must give each URL and date last accessed. If a stable online source is instead placed in the bibliography, give author or agency, title, host, version or access date, and URL; use DOI-bearing scholarship in the bibliography ([AAS references guidance, “Other Online Sources”](https://journals.aas.org/references/)). The outline’s choice to treat the posts as engineering provenance rather than scholarly authority is therefore reasonable (`paper_agentic/REWRITE_OUTLINE_v3.md:20-24,56-66`).

The current footnote is not adequate: it names only Bowne-Anderson, Böckeler, and Palantir, calls the remaining two “vendor posts,” gives no URLs, and delegates accessibility to an unspecified provenance manifest (`paper_agentic/v3/sec3_harness.tex:17-20`). List all five explicitly, with “accessed 2026-09-02”:

1. Hugo Bowne-Anderson, [“How to Build an Effective Agent Harness”](https://hugobowne.substack.com/p/how-to-build-an-effective-agent-harness), 2026-07-28.
2. Birgitta Böckeler, [“Harness Engineering for Coding Agent Users”](https://martinfowler.com/articles/harness-engineering.html), 2026-04-02.
3. Palantir, [“The Ontology system”](https://www.palantir.com/docs/foundry/architecture-center/ontology-system), plus the exact Foundry pages used for [Ontology concepts](https://www.palantir.com/docs/foundry/ontology/overview), [action types](https://www.palantir.com/docs/foundry/action-types/overview), and [submission criteria](https://www.palantir.com/docs/foundry/action-types/submission-criteria); living documentation, so give the access date for each.
4. Sa Wang/PuppyGraph, [“Agent Harness: What It Is and How to Build One”](https://www.puppygraph.com/blog/agent-harness), 2026-07-01.
5. Sydney Runkle/LangChain, [“How to Build a Custom Agent Harness”](https://www.langchain.com/blog/how-to-build-a-custom-agent-harness), 2026-06-03.

Do not cite the five as evidence that this system is reliable. Use them to explain the engineering vocabulary and design grammar. Palantir in particular supports typed objects/actions/security, not the exact five-part harness taxonomy; the repository comparison records the distinct Böckeler, Palantir, PuppyGraph, and LangChain contributions (`notes/HARNESS_COMPARISON_20260902.md:128-144,211-228,279-293,313-324`).

Add peer-reviewed or archival literature for the scientific/agent claims. These identifiers were checked against publisher or arXiv records in this review:

- Wang et al., “A Survey on Large Language Model based Autonomous Agents,” *Frontiers of Computer Science* 18, 186345 (2024), DOI [10.1007/s11704-024-40231-1](https://doi.org/10.1007/s11704-024-40231-1). Use for standard agent architecture, planning, memory, tools, and evaluation—not for the exact five-job taxonomy.
- Yao et al., “ReAct: Synergizing Reasoning and Acting in Language Models,” ICLR 2023, [arXiv:2210.03629](https://arxiv.org/abs/2210.03629). Use for interleaved reasoning/action with external tools.
- Chen et al., “ScienceAgentBench: Toward Rigorous Assessment of Language Agents for Data-Driven Scientific Discovery,” ICLR 2025, [arXiv:2410.05080](https://arxiv.org/abs/2410.05080). Use for scientific-agent evaluation and the gap between plausible trajectories and correct science.
- Kapoor et al., “AI Agents That Matter,” *Transactions on Machine Learning Research* (2025), [arXiv:2407.01502](https://arxiv.org/abs/2407.01502). Use for reproducible evaluation, cost, and the distinction between benchmark claims and operational utility.
- Souza et al., “LLM Agents for Interactive Workflow Provenance: Reference Architecture and Evaluation Methodology,” DOI [10.1145/3731599.3767582](https://doi.org/10.1145/3731599.3767582), [arXiv:2509.13978](https://arxiv.org/abs/2509.13978). This is the closest direct scholarly support for provenance-aware LLM agents in scientific workflows.

Two science-domain exemplars are relevant but should not be presented as harness standards: Boiko et al., “Autonomous chemical research with large language models,” *Nature* (2023), DOI [10.1038/s41586-023-06792-0](https://doi.org/10.1038/s41586-023-06792-0), and Bran et al., “Augmenting large language models with chemistry tools,” *Nature Machine Intelligence* (2024), DOI [10.1038/s42256-024-00832-8](https://doi.org/10.1038/s42256-024-00832-8).

I found no peer-reviewed work that standardizes Bowne-Anderson’s exact five-part “agent harness” decomposition. Treat that absence as **COULD NOT VERIFY**, not as a claim of nonexistence.

## 5. Referee’s attack

### Objection 1 — “Reliability is not a property of the harness alone, and this paper has not isolated a causal effect.”

The outline’s thesis is presently absolute: “reliability over a long scientific run is a property of the harness” (`paper_agentic/REWRITE_OUTLINE_v3.md:65-66`). But §3 itself describes a composite system: hosted coding product, repository controls, deterministic science engine, and human gates (`paper_agentic/v3/sec3_harness.tex:43-50,66-87,153-160`). A skeptical referee will ask which layer caused each improvement and whether the same model/task without the added control would have failed.

**Evidence already on disk:** v2 documents concrete catches with scientific consequences, including the soft-burst validity-gate bias and the lag-port/sign episode (`paper_agentic/agentic_grb_v2.tex:547-576`). The figure-verification ledger records errors caught across successive fresh-context visual gates, including a science-error class (`results/campaign/agentfigs/VISION_QC.md:14-23`).

**Evidence missing:** no fixed-task, fixed-language-model ablation is reported in the permitted architecture artifacts or manuscript. The known-results replay is still proposed (`paper_agentic/T1_component_roster_DRAFT.md:102`), and automatic action capture is not wired (`paper_agentic/T1_component_roster_DRAFT.md:73`).

**Answer/rewording:** frame reliability as a property of the **combined model–harness–workflow–human system under the tested GRB/data regime**, and make the causal status observational: “Model capability alone did not determine operational reliability; in this campaign, errors were caught or propagated according to the combined control system under the tested GRB/data regime.” Reserve a stronger causal claim for an ablation or controlled replay.

### Objection 2 — “Fresh context and role labels do not create epistemic independence or truth.”

The draft says every verification uses fresh context and that roles are separated (`paper_agentic/v3/sec3_harness.tex:100-106,153-160`). A referee will point out that producer and verifier may share the same model family, prompts, code, data transformations, and mistaken primitive. V2 already states the key limitation: multiple agents using the same primitive can be “one opinion repeated N times” (`paper_agentic/agentic_grb_v2.tex:640-651`).

**Evidence already on disk:** the intended defense is stronger than generic multi-agent voting: frozen predictions and a known-results battery are articulated in v2 (`paper_agentic/agentic_grb_v2.tex:614-638`), followed by primitive-level independence and four verification channels (`paper_agentic/agentic_grb_v2.tex:640-676`).

**Evidence missing:** the human-vs-agent benchmark/second-expert comparison remains a design rather than a completed result (`paper_agentic/agentic_grb_v2.tex:685-697`). The queued science-guard row is only partly implemented: the ancestor audit is coded, while its synthetic-truth, stale-temporal, vacant-read-path, and engine/report fail-closed controls remain proposed (`paper_agentic/T1_component_roster_DRAFT.md:115`).

**Answer/rewording:** call fresh-context roles “correlated error-detection channels,” not independent reviewers. Reserve “independent” for tests that use a disjoint primitive, source, implementation, or human expert.

### Objection 3 — “The architecture is aspirational; where is the completed long-run reliability result?”

The draft openly admits that the queue manager and typed workflows are absent (`paper_agentic/v3/sec3_harness.tex:58-64`), that hook coverage is narrow (`paper_agentic/v3/sec3_harness.tex:141-151`), and it closes by naming five missing mechanisms, although that list does not match T1’s five PROPOSED rows (`paper_agentic/v3/sec3_harness.tex:188-193`; `paper_agentic/T1_component_roster_DRAFT.md:40,75,91-92,115`). A skeptical referee will therefore argue that a component inventory plus selected incidents is not evidence of reliability over 106 bursts.

**Evidence already on disk:** Stage-1 has a 106/106 stamped selection catalog under T1’s census (`paper_agentic/T1_component_roster_DRAFT.md:49`), and v2 reports that an engine run was performed while acknowledging retry debt (`paper_agentic/agentic_grb_v2.tex:728-735`).

**Evidence missing:** the frozen end-to-end run, complete stamp/receipt coverage, known-results/model-change evaluation, and portability test. The fresh-session acceptance test described in v2 had accepted only 7/11 steps for its first burst, and its portability test remained pending (`paper_agentic/agentic_grb_v2.tex:750-774,849-862`). The current T1 also marks the report gate, extra boundary controls, and science guards as proposed (`paper_agentic/T1_component_roster_DRAFT.md:91-92,115`).

**Answer:** present the paper’s current result as a **partly exercised architecture and reliability hypothesis with documented interventions**, not as a finished proof of long-run reliability. A strong final paper needs a version-pinned full run with denominators: completion/refusal rates, gate interventions, stale-artifact detections, false-positive and missed-error rates, rework cost, and outcomes after every model/harness change.

## 6. Process

For this rewrite, use a **hybrid block review**, not six more strictly serial line-by-line gates and not draft-all-then-review. The outline already fixes the global structure and explicitly groups the new construction as §3/§4/§7 before the recuts and final framing (`paper_agentic/REWRITE_OUTLINE_v3.md:117-124`). Gate the architecture block (§3 + §4 + §7) now because its definitions and DEPLOYED/PROPOSED distinctions constrain everything downstream; then draft §5 + §6 + §10 together and review them as one claims/evidence block; write §1 and §11 last and perform one assembled-PDF coherence gate. The PI should receive a short decision sheet of high-consequence claims and status changes at each block, not every sentence in isolation. This preserves his authority while avoiding local approvals that later lock contradictory vocabulary or status claims into six separate sections.

## DISCREPANCIES

1. **T1 approval metadata contradicts the decision log.** The source roster still says “producer draft, UNGATED,” “Nothing here is PI-approved,” and “re-gate pending” (`paper_agentic/T1_component_roster_DRAFT.md:5-8`), while the approved outline says T1 passed four rounds and was PI-approved at `427fdc5` (`paper_agentic/REWRITE_OUTLINE_v3.md:133`). **Fix:** update the Markdown source header to the actual approved state and regenerate `paper_agentic/v3/tab_T1_roster.tex`; do not edit the generated TeX by hand (`paper_agentic/v3/tab_T1_roster.tex:1`). A metadata-only correction can preserve the recorded content gate, but the substantive cell corrections below require fresh verification and PI re-approval.

2. **The prose’s five PROPOSED components do not match T1’s five rows.** The exact rows are queue manager + workflows, first-class actions, report-conformance gate, queued boundary build, and queued science-guard code (`paper_agentic/T1_component_roster_DRAFT.md:40,75,91-92,115`). **Fix:** use the replacement under O20.

3. **The authority table assigns engine outputs to AI and makes Stage 1 human-only.** Fit validity and the AIC/BIC winners are computed in code (`scripts/10_spectral_fit_burst.py:1038-1082,1104-1128,1157-1163`); Stage 1 permits human or AI selection (`paper_agentic/T1_component_roster_DRAFT.md:49`). **Fix:** apply O18 and define the two planes before the table.

4. **The manuscript cites a gated PNG hash while embedding PDFs, and the gate ledger is not commit-recoverable.** The draft comment identifies F1 as gated with PNG hash prefix `d355cbec` and the TeX embeds `fig_F1_harness_anatomy.pdf` (`paper_agentic/v3/sec3_harness.tex:4,29-38`). The ledger records hashes for the four PNGs and separately declares that verdicts expire on TeX-source edits (`results/campaign/agentfigs/VISION_QC.md:25-34`); it does not hash the embedded PDFs or source TeX. Moreover, the ledger itself falls under ignored `results/*` (`.gitignore:37-44`), although the outline points to it as the approval record (`paper_agentic/REWRITE_OUTLINE_v3.md:133-134`). The embedded PDF SHA-256 values I recomputed are F1 `f85927943925…`, F2 `4aae2ec1d6d3…`, F4 `dd0829ac72ac…`, and F5 `19b58a149d23…`; none is the ledgered PNG hash. **Fix:** track or manifest the approval ledger, then gate and ledger the exact embedded PDFs plus source-TeX hashes, or embed the exact verified PNG derivatives.

5. **“At commit 4df6884” cannot reproduce ignored-product counts.** `results/*` is ignored except for a small allowlist (`.gitignore:37-47`), while state files, receipts, action events, eval records, and VISION_QC ledgers contribute to the census (`paper_agentic/T1_component_roster_DRAFT.md:27`). **Fix:** say “working tree measured on 2026-09-02 with tracked code at 4df6884” and ship a path/hash/count manifest plus the exact census commands.

6. **DEPLOYED conflates presence, invocation, enforcement, coverage, and effectiveness.** T1’s definition is only file-or-product presence (`paper_agentic/T1_component_roster_DRAFT.md:20-25`). Thus a report with fail-closed guards proposed, an action trace without automatic wiring, a partial dispatch hook, and incomplete rails can all appear simply DEPLOYED in the generated table (`paper_agentic/T1_component_roster_DRAFT.md:51,53,71,73,82,110,112`; `paper_agentic/v3/tab_T1_roster.tex:19-20,30-32,37,57,59`). **Fix:** either add a PARTIAL status or add separate columns for PRESENT / INVOKED / ENFORCED / EVALUATED. At minimum, preserve the source roster’s parenthetical limitations in the paper table.

7. **The section-movement comment conflicts with the approved outline.** It says doctrine → §5 (`paper_agentic/v3/sec3_harness.tex:6-9`); the outline says Verification Doctrine → §6 (`paper_agentic/REWRITE_OUTLINE_v3.md:90-92`). **Fix:** use the split specified in Question 1.

8. **Figure 1 repeats two textual overclaims.** It says “24 models × every block” and presents all 27 guides as ledger-indexed skills (`paper_agentic/figures/fig_F1_harness_anatomy.tex:39,44-47`). **Fix:** revise F1 to “24-model menu; attempted on usable bins in the highe run” and “27 guide files; ten ledger-indexed step skills,” then re-render and re-gate because the ledger says verdicts expire on source edits (`results/campaign/agentfigs/VISION_QC.md:34`).

9. **`\prov` is used for claims that are not census counts.** The byte-identical incident and “in all operation to date” are qualitative/historical claims, not counts tied to a component census (`paper_agentic/v3/sec3_harness.tex:120-124,183-186`). **Fix:** cite the incident record and hashes directly, or remove the claims until §9 establishes them; reserve `\prov` for values actually reproducible under a stated basis.

10. **The current web footnote is incomplete.** It omits two titles/authors, all URLs, and access dates (`paper_agentic/v3/sec3_harness.tex:17-20`). **Fix:** list all five sources explicitly as specified in Question 4; do not rely on an off-page provenance manifest for basic citation recovery.

11. **“That burst’s own numbers” does not establish current authoritative provenance.** The phrase is not literally a wrong-burst claim, because the fallback table uses the same trigger. The defect is currency: the assembler prefers the promoted table but silently falls back to another tree when the canonical table is absent (`scripts/48_burst_report.py:68-73`), precisely the stale-copy path the standing contract says must fail closed (`dev/ai_guides/ReportSpec.md:35-41`). **Fix:** replace `paper_agentic/v3/sec3_harness.tex:85-86` with: “the report assembler, which draws on per-burst products but does not yet fail closed when the canonical fit table is absent or bind every report to the fit-table hash.”

12. **The generated T1 repeats claims corrected in §3.** It still says the engine fits every menu model to every block, the whole SED family refuses mismatches, the board derives every state, the live report stamps every step and automatically clears downstream markers, every product is hash/commit bound, every instance is schema-validated, and hook/PI-gate scopes are absolute (`paper_agentic/v3/tab_T1_roster.tex:14,19,28-31,36-40`). **Fix:** correct the Markdown source rows using the same qualifications as O7, O10, O12–O17, regenerate the TeX, and send the substantively changed roster through a new verifier and PI gate; the approval at `427fdc5` cannot silently cover changed cells (`paper_agentic/REWRITE_OUTLINE_v3.md:133`).

## COULD NOT VERIFY

- I could not verify the conversational-approval, late-stamp, or byte-identical-reinstatement history without opening the prohibited burst products/approval records. The operator-invoked cascade’s behavior is verifiable (`dev/invalidate_downstream.py:45-84`); the historical narrative in `paper_agentic/v3/sec3_harness.tex:120-124` is not verifiable from the allowed record set.
- I could not verify the universal claim that no human approval was ever fabricated or count how often the human overruled an agent. The CLI requires a supplied identity but does not authenticate it (`dev/live_report.py:155-160`), and the allowed artifacts do not constitute a complete approval ledger.
- I could verify that 106 state JSON files exist in the present working tree and that the board writes them (`dev/agent_state.py:64-72`), but not that those exact contents existed at commit `4df6884`; `results/*` is ignored (`.gitignore:37-44`).
- I recomputed 134 collected items in 11 modules under `tests/` and 199 items in 16 modules repository-wide in the present working tree. I could not reconstruct the historical “134 at `4df6884`” collection solely from that commit because parametrization depends on ignored products; the roster’s changing same-day totals show that dependence (`paper_agentic/T1_component_roster_DRAFT.md:183-187`; `.gitignore:37-44`).
- I could not verify an exhaustive negative claim that no peer-reviewed paper uses the exact five-job harness taxonomy. I found no such work in the searches performed; absence from those searches is not proof of nonexistence.
- I could not verify production-level freshness, end-to-end stamp coverage, or effectiveness rates from this architecture-only artifact set. T1 itself records partial receipts, action wiring, report enforcement, and science guards (`paper_agentic/T1_component_roster_DRAFT.md:69-75,91-92,102,115`).

## Independent judgment beyond the six questions

The most fragile issue is not any single false count; it is the one-dimensional status vocabulary. “DEPLOYED” currently means that some file or product exists (`paper_agentic/T1_component_roster_DRAFT.md:20-25`), but readers will naturally hear “invoked on every eligible event, mechanically enforced, covered, and evaluated.” That gap is large enough to undermine the architecture figure even after the prose corrections. The paper should report at least four distinct states—**present, invoked, enforced, evaluated**—or use DEPLOYED/PARTIAL/PROPOSED with explicit coverage. This is the central precondition for making T1 scientifically interpretable.

Second, §3 needs an astronomy-facing causal thread. Each subsection should connect one harness component to a concrete error class and scientific consequence: invalid-fit promotion, stale temporal values, wrong detector/background provenance, or sign-convention drift. V2 already supplies suitable worked examples (`paper_agentic/agentic_grb_v2.tex:547-576`). Without that thread, a referee can dismiss §3 as a repository tour.

Third, the thesis should be made system-level and empirical. The defensible conclusion at this stage is that reliability was shaped by the interaction of language model, hosted harness, repository controls, deterministic engine, and human authority; the project has documented interventions and remaining coverage gaps. The stronger assertion that “reliability … is a property of the harness” (`paper_agentic/REWRITE_OUTLINE_v3.md:65-66`) should be presented as the design hypothesis tested by the eventual frozen run, not as an already isolated result.

Finally, name and version the hosted harness and language model in reproducibility metadata. The draft says only “commercial coding harness” (`paper_agentic/v3/sec3_harness.tex:43-46`), T1 names Claude Code (`paper_agentic/T1_component_roster_DRAFT.md:37`), and the provenance module permits `unknown` model/harness fields (`dev/provenance_stamp.py:38-49`). Since the paper’s thesis concerns harness-dependent behavior, an unidentified or unversioned outer harness is a load-bearing reproducibility omission.

# Skill: The Burst Walkthrough — step-gated, skill-improving, freeze-then-rerun

**Purpose:** The master working protocol for the burst-by-burst campaign
(Vikas, 2026-07-29). One burst at a time, EVERY pipeline step is presented,
approved, compared against literature, and its lessons distilled into that
step's skills file. Skills accumulate burst over burst; when they converge, the
IMPROVED pipeline is frozen and freshly applied to ALL 106 bursts in one go.
**Precedent: the GCN helper was built exactly this way** (fields discovered
per-burst → schema stabilized → applied to all in one sweep). It is also the
dev→freeze→production discipline the external architecture reviews demanded
(scaffold hardening on dev cases; one clean frozen run; no test-set leakage).

**Roles:** the AI runs each step and NARRATES it; **Vikas approves every single
step** before the next one runs (autonomy dial = gated_steps). Nothing advances
on silence.
**Fully-AI mode (Vikas, 2026-08-14, at the bn081125496 step-0b gate):** when a
burst report is produced end-to-end by AI, the gate is held by an **independent
AI approver — a different agent or platform (e.g. Codex) — never the producer
itself** (same producer≠verifier rule as ShippingGate.md), and the approver's
stamp is recorded like any gate stamp. In both modes the final deliverable is
the per-burst REPORT (`REPORT_<trig>.md/.pdf`).

## Per-burst loop (for burst B)
For each step S in the ledger below:
1. **RUN** step S on burst B (background where heavy; 12-core cap).
2. **PRESENT** — four things, always:
   (a) *what the pipeline does here* (the step's job, inputs, its skill file);
   (b) *what actually ran* (commands, decisions the AI made, seeds/settings);
   (c) *conclusions* (the numbers/products, with the honest flags);
   (d) *what's going on* (anomalies, check failures, open questions).
3. **GATE** — Vikas approves / corrects / redirects. A correction is treated as
   a candidate lesson.
4. **LITERATURE** — where published work bears on this step for this burst,
   diff against it (SpectralFitting.md P1–P5 discipline: verified sources only,
   frames aligned, tested explanations).
5. **DISTILL** — anything learned becomes a new Lxx in THAT STEP's skills file
   (deduped). Every lesson **attributes the mismatch** — *we*-wrong (fix code) /
   *they*-wrong (document why ours is better-supported) / *frame*-difference
   (a normalization rule). The attribution IS the lesson (SpectralFitting P6).
   Code-hardenable lessons get implemented + verified before the next burst uses them.
6. Next step; at burst end, write `notes/reconciliation/<trig>.md` (the record).

## ADOPT mode (Vikas 2026-07-29)
Steps 2–5 are ALREADY DONE for the sample (human-reviewed Stage-1 selections +
27b/27c blocks). In the walkthrough they are **ADOPTED**: presented briefly
(what was selected, by whom, provenance stamp) for context — NOT re-run. They
re-open only if a downstream check implicates them (e.g. response coverage,
BOUND_CAPPED tracing to a window, a residual anomaly pointing at background).

## The step ledger (each step = its skill file; ✎ = to be created on first use)

> ✔ RESOLVED 2026-08-30 — THIS LEDGER'S NUMBERING IS OFFICIAL (PI, verbatim): "The BurstWalkthrough ledger numbering is official: 0b = literature harvest, 0 = identity & GCN, 1 = data inventory, and so on. Fix the live-report tool's step names to match; existing figure filenames keep their names — record the mapping once, do not rename products mid-campaign."
> dev/live_report.py and AgentArchitecture's per-step roster were fixed the same day; figure
> filenames keep their names; canonical mapping record: AgentRoster.md decision sheet item 22.
| # | step | what the pipeline does | skill file |
|---|---|---|---|
| 0b | **Literature harvest** | find/fetch/mine the REFEREED papers for this burst (ADS 4-form query, published version, frame-align, file to the dossier) — the step that must become automatic by burst #20 | `LiteratureHarvest.md` |
| 0 | Identity & GCN intelligence | resolve burst identity; fetch+read GCN circulars; extract position, T90, **redshift** (with circular as source), instrument notes, **and the published spectral/temporal values** — harvest once, file under "PUBLISHED VALUES (for the P3 diff)". Blindness lives in the FIT, not in what Step 0 may read. | ✎ `GCNIntelligence.md` (seed from LATBright `gcn_intelligence.md`) |
| 1 | Data acquisition & inventory | TTE/CSPEC/RSP2/POSHIST (+LLE triplet, +LAT FT1/FT2) with versions; manifest; **response-coverage check vs source window** (the bn100130729 lesson) | ✎ `DataInventory.md` |
| 2 | Detector selection | geometry/angles, occultation, BGO companion rule | `detector_selection.md` (exists) |
| 3 | Background | pre/post windows hugging the burst; polyfit order; residual QC | `background_selection.md` (exists) |
| 4 | Source interval | emission window in the common background gap | `source_selection.md` (exists) |
| 5 | Binning (two-tier) | 27b fine GBM Bayesian blocks + significance merge; 27c coarse LLE grid (gated); **bin adequacy for the band that constrains each component** (L3/L6) | `Binning.md` (exists) |
| 6 | Spectral fitting & selection | the full menu, multistarts, chain gates, classes, admission, evolution tracks — THE DISCOVERY LOOP | `SpectralFitting.md` (flagship, L1–L13) |
| 7 | Temporal | T90/T50, MVT, lag, pulse fits | `Temporal.md` (exists — carries the DEFECT LEDGER; check before quoting) |
| 8 | νFν panels & residual reading | ratio-unfolded panels + residual grammar (feeds step 6's loop) | in `SpectralFitting.md` (L10/L11) |
| 9 | QC & flags | cross-step sanity, literature-consistency verdict | `qc_flagging.md` (exists) |

## ⭐ THIS IS THE PRIORITY PROJECT (Vikas, 2026-08-08 — stated plainly)
> *"the most important project at the moment is this one, where our goal is to analyze these all
> one by one along with reading the literature papers and doing full pipeline sweep on them and
> improving our skills files that will assist us better and better — and then once we build all
> 106, all the skills, then run again full sweep with all learning and complete the project."*

**The loop, and the reason it is not wasteful:** each burst is analysed end-to-end AND read about
in the literature; what is learned hardens into the skill files; the next burst is analysed by a
better pipeline. The per-burst numbers are NOT the product — **the matured skills are**. The
product arrives at the end, when the frozen pipeline is run once over all 106 with every lesson
applied.

**Consequences for how we work — these override the temptation to start new things:**
1. **Complete projects one by one; do not jump between them.** (Vikas, same day: *"let's do things
   systematically and complete projects one by one rather than jumping to infinite many
   projects"*.) As of 2026-08-08 the registry holds 10 projects: 1 running, 0 complete.
2. **BUT bank everything.** (*"all possibilities and all new projects has to be banked and all the
   important ideas related to them has to be deposited to their files"*.) Ideas are recorded in
   `notes/PROJECTS_registry.md` the moment they appear — banking is cheap, and losing an idea is
   not. Banking ≠ starting: a registered project is parked until this one finishes.
3. **Every other project depends on this one.** #34 needs the census; #35 needs the fits; #37/#38
   need the temporal catalog; #42 needs the shape results; the agentic paper needs the benchmark.
   Finishing the walkthrough unblocks all of them; starting them first unblocks nothing.
4. **A burst is not "done" for the paper — it is done for the SKILLS.** All walkthrough-era numbers
   are provisional by definition (below); quoting them as results is a category error.

## Convergence & freeze
- A burst that completes ALL steps with **zero new lessons** is a *clean pass*.
- After **K consecutive clean passes** (Vikas sets K; suggest 2–3), the skills
  are declared CONVERGED: freeze the scaffold (commit hash recorded), then the
  **fresh full-sample run of the frozen pipeline over all 106** — one go, fresh
  out-root, provenance-stamped. This production run subsumes every pending
  re-run debt (L8/L9 census re-derivation, the 4 RSP2-repair bursts, 130427A
  2nd pulse, stale fits).
- Until freeze, ALL numbers are provisional-by-definition; no headline is
  quoted from walkthrough-era outputs.

## Rules of the campaign
- **THE SHIPPING GATE (Vikas, 2026-08-12):** no product ships unverified — figures,
  tables, records, citations, code. Product-typed checklists + the generator≠adjudicator
  independence rule live in `ShippingGate.md`. Born from the bn200524211 montage incident
  (a delivered figure contradicting the engine table). Machine stamps inline; vision and
  judgment checks in a FRESH subagent context.
- **SCOPE: the ANALYSIS is prompt-only; the LITERATURE is FREE (Vikas, 2026-08-11):**
  this Agent is the prompt-emission module — analysis targets, P0 predictions, and
  reconciliation items are prompt-phase only. But *"the literature should be free"*
  (Vikas, verbatim): read, fetch, and catalog the WHOLE record of each burst —
  afterglow, associated SN, cosmology, multimessenger — summarized in the dossier
  under BEYOND-PROMPT CONTEXT and corpus-tagged `module-future;*` (LiteratureHarvest
  Phase 3c). That material is groundwork the future sibling modules inherit and raw
  material for the discovery plane; it just never becomes a target here. Same shape
  as blind-first: the lock binds the analysis, never the reading.
- **Blind-first ORDERING (Vikas, 2026-07-31; CLARIFIED 2026-08-03) — the
  non-negotiable order:** we ANALYSE first, then compare to published, then diagnose
  the mismatch, then *attribute* it (were WE wrong or were THEY wrong), then write
  the skill.
  **What "blind" governs is the ANALYSIS, not what the agent is allowed to read.**
  Vikas, 2026-08-03: *"you can of course take them, only that when you do spectral
  analysis start blindly."* So:
  - **Step 0 MAY collect everything**, including the published spectral/temporal
    RESULTS (Ep, α, β, model preference, T90, lag, fluence). They are needed for the
    P1/P3 diff anyway, and harvesting them twice is waste. Record them in the dossier
    under a clearly-labelled **PUBLISHED VALUES (for the P3 diff)** heading.
  - **The FIT starts blind and stays un-tuned.** Never seed a parameter, restrict a
    model, widen a bound, pick a binning, or choose a detector set *because* it moves
    us toward a published number. The winner is the engine's gated AIC, full stop.
  - **Freeze P0 BEFORE diffing** (SpectralFitting Phase 0): our table is written and
    immutable before any comparison. If our number and theirs disagree, that is a
    result to explain (P4), never a reason to re-fit toward theirs.
  - **Interpretation bias is a REAL residual risk, and the mitigation is disclosure,
    not abstinence** — the bn081125496 "saw Yu first" caveat. If a paper's claim was
    known before the fit, say so in the record; the clean test of the DECISION is the
    blind Challenge Lab, not agent self-restraint.
  ⚠ Superseded: an earlier version of this rule said the papers' spectral results
  must stay SEALED through Step 0. That was over-strict and cost a second fetch on
  bn120624933 — do not reinstate it.
- **Filenames carry the trigger ID** (lesson G1, 2026-07-29): every per-burst
  product is `<trigger>_<content>.ext` — directories organize, filenames are
  the search surface; 106 identical basenames are unfindable.
- Discuss-first stands: no burst starts without Vikas choosing it.
- Every lesson names its burst + date + evidence (as in SpectralFitting.md).
- A skipped check is a fake pass (the Discovery Loop rule) — applies to steps.
- Corrections from Khushboo's arm are lessons too (two-arm convergence is
  evidence, and divergence is a finding — record both).

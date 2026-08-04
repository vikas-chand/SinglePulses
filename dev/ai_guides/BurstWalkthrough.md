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
| # | step | what the pipeline does | skill file |
|---|---|---|---|
| 0 | Identity & GCN intelligence | resolve burst identity; fetch+read GCN circulars; extract position, T90, **redshift** (with circular as source), instrument notes, **and the published spectral/temporal values** — harvest once, file under "PUBLISHED VALUES (for the P3 diff)". Blindness lives in the FIT, not in what Step 0 may read. | ✎ `GCNIntelligence.md` (seed from LATBright `gcn_intelligence.md`) |
| 1 | Data acquisition & inventory | TTE/CSPEC/RSP2/POSHIST (+LLE triplet, +LAT FT1/FT2) with versions; manifest; **response-coverage check vs source window** (the bn100130729 lesson) | ✎ `DataInventory.md` |
| 2 | Detector selection | geometry/angles, occultation, BGO companion rule | `detector_selection.md` (exists) |
| 3 | Background | pre/post windows hugging the burst; polyfit order; residual QC | `background_selection.md` (exists) |
| 4 | Source interval | emission window in the common background gap | `source_selection.md` (exists) |
| 5 | Binning (two-tier) | 27b fine GBM Bayesian blocks + significance merge; 27c coarse LLE grid (gated); **bin adequacy for the band that constrains each component** (L3/L6) | ✎ `Binning.md` |
| 6 | Spectral fitting & selection | the full menu, multistarts, chain gates, classes, admission, evolution tracks — THE DISCOVERY LOOP | `SpectralFitting.md` (flagship, L1–L13) |
| 7 | Temporal | T90/T50, MVT, lag, pulse fits | ✎ `Temporal.md` |
| 8 | νFν panels & residual reading | ratio-unfolded panels + residual grammar (feeds step 6's loop) | in `SpectralFitting.md` (L10/L11) |
| 9 | QC & flags | cross-step sanity, literature-consistency verdict | `qc_flagging.md` (exists) |

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

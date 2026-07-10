# The GRB "AI Scientist" — block-by-block design

> Working design doc, started 2026-07-10 from Vikas's dictated walk-through.
> **This is paper material**: the structure here feeds `paper_agentic/agentic_grb.tex`
> ("Can AI Do GRB Data Analysis?"). It accretes one block per discussion; each block
> section is stamped when designed. Code home: `grb_pipeline` in the GRB_Handbook repo
> (`~/Desktop/Projects/GRB_Handbook_Project`); consolidation mechanics in
> `dev/CONSOLIDATION_PLAN.md`; benchmark mechanics in `dev/BENCHMARK_PLAN.md`.

## Program scope (decided 2026-07-10)
- **Round 1 (now): single-pulse GRBs only** — the Busby–Lazzati 106-burst sample
  (benchmark subset: the 25 of `dev/benchmark_sample.ecsv`). The full Fermi/GBM
  catalog is thousands of bursts — too many for the demonstration. Round 1 is the
  demonstration: begin simple, on the sample we already have frozen, downloaded, and
  under expert approval.
- **Round 2 (later): the full Fermi/GBM catalog** (~3000+ GRBs), after Round 1
  validates the method.
- **Instrument phasing**: Fermi GBM (+LAT/LLE) first → Swift BAT → XRT/UVOT →
  joint Fermi+Swift → AstroSat. Nothing beyond Fermi is designed until Fermi is done.

## Architecture — three strictly separated layers
1. **Deterministic instruments** — the physics code (fetchers, geometry, binning,
   fitting, statistics). Boring, verified, version-stamped. *LLMs never do arithmetic
   here.*
2. **Agent judgement** — what a scientist *judges* (selections, QC, model sanity,
   interpretation). LLMs do this, always through written task guides + the approval
   gate + stamps (`APPROVED_BY`/`APPROVAL_MODE`/`tool_commit`).
3. **Orchestration + verification** — the workflow chaining 1↔2, with adversarial
   self-checks and the benchmark harness scoring the judgement layer.

Proven end-to-end in Two_Breaks Stage-1; the AI scientist is this pattern extended to
the whole workflow.

## The block template
Every block is the same shape, instantiated with different physics:

> **tool** (deterministic) · **judgement** (what a scientist decides) · **guide**
> (.md the agent reads = the benchmark's fairness control) · **gate**
> (stamp/provenance) · **benchmark** (how the judgement is scored)

## Reference hierarchy (decided 2026-07-10)
**Trust order: published papers ≻ our expert panel ≻ GCN circulars.**
The panel is *considered* human analysis; GCNs are preliminary first-look (hours,
often semi-automated) — our careful work outranks a quick-look number. This is a
**trust** ordering, not a **coverage** ordering (they invert):

| Baseline | Trust | Coverage | Role |
|---|---|---|---|
| Published papers | highest (refereed) | medium | gold standard where it exists |
| Expert panel (Vikas/Khushboo) | high (considered) | low (25 bursts) | controlled experiment on *selections* |
| GCN circulars | lower (preliminary) | high (hundreds) | free population-scale check |

**Arbitration rule (Block 8):** per burst + quantity, score against the
highest-trust reference available: paper if published → else panel if in the 25 →
else GCN. GCN-vs-us disagreement on a panel burst is more likely a GCN
preliminary-value artifact than our error — itself a reportable finding.

---

## Block decomposition

Tags: **[⚖]** scored judgement block (the paper's evidence) · **[⚙]** deterministic
plumbing · **[🧠]** LLM interpretation (highest hallucination risk).

| # | Block | Contract (in → out) | Where the judgement is | Status |
|---|---|---|---|---|
| 0 | **Event intake / GCN+lit intelligence** [⚖] | trigger → dossier + reproduction card | which values to trust; tiering; conflict resolution | designed below |
| 1 | Data acquisition [⚙] | trigger+instruments → TTE/CSPEC/RSP/POSHIST (+LLE/LAT) | *which* data (LAT-detected → pull LLE) | FermiFetcher + Pulsewise resolver |
| 2 | Detector selection [⚖] | position+POSHIST → detector set, gated | borderline angles, occultation, contamination | built (39 + guide + Jaccard) |
| 3 | Background modeling [⚖] | LC+detector → pre/post windows + polyfit, gated | **hardest block** — windows vs orbital trends; most inter-human scatter | built; LRT≤3 convention pending |
| 4 | Source/emission interval [⚖] | bkg-subtracted LC → source window, gated | emission boundaries | built (guide + edge-Δ/IoU) |
| 5 | Temporal analysis [⚖/⚙] | interval+bkg → BB+σ bins, T90, MVT, lag, pulses | SIGMA_FLOOR, merges, pulse count | 27b; LATBright MVT/lag/MEPSA |
| 6 | Spectral analysis [⚖] | bins+data-prep → 6-model fits, AIC/LRT+validity, fluxes, Ep(t) | model doctrine, validity gating, degenerate BB | engine-10 |
| 7 | Derived science [🧠] | all above → Amati/Yonetoku, classification, correlations | interpretation, population placement | handbook AnalysisEngine |
| 8 | Cross-check & QC [⚖] | our outputs + reproduction card → convention-matched agreement report | real disagreement vs convention mismatch? | qc guide + arbitration rule above |
| 9 | Report + provenance [⚙] | everything → re-runnable paper-grade report | none (mechanical) | handbook report_generator |

**Cross-cutting layers** (span all blocks): the **gate** (stamp/decision.json —
exists in Two_Breaks only, must ship in the package) · **orchestrator**
(`PipelineStage.execute(context)→context` — handbook has it) · **verification
harness** (adversarial refute-panels — the thing humans don't do; a defensible
"better-than" axis) · **benchmark harness** (`scripts/40` leaderboard + the three
baselines) · **env/platform** (`ensure_analysis_env()` — DONE, handbook `1bfdd4a`).

Two structural observations:
- **Judgement concentrates in blocks 2/3/6.** Background (3) is where humans
  disagree most → hardest for the agent AND the easiest bar ("within the
  inter-human band"). That asymmetry is a gift.
- **Blocks 0 and 8 are a designed pair**: if Block 0 doesn't capture conventions
  ("this Ep is a Band-Ep over 10–1000 keV"), every Block-8 "disagreement" is noise.

---

## Block 0 — Event intake / GCN + literature intelligence  **[DESIGNED 2026-07-10]**

*The first thing a scientist does with a GRB: search for it.* Three regimes, three
benchmark modes:

| Regime | Block 0 fetches | Human baseline | Benchmark mode |
|---|---|---|---|
| **Published** | the paper's *whole analysis* (see reproduction card) | the refereed paper | AI vs published method+results |
| **GCN-only** | circulars, then **an expert (Vikas/Khushboo) looks + approves** | *expert-approved-GCN* — raw GCNs never enter the benchmark unvetted | AI vs vetted first-look |
| **We're first** | nothing upstream exists | none — **we produce the first analysis**; the person posting the results approves them | production; forward validation when others publish |

### Output = a *reproduction card*, not a measurements row
For the published regime we extract the **method level**, because we benchmark
method vs method, not just final numbers. Fields (each later checked block-by-block:
their §temporal ↔ our Block 5, their §spectral ↔ our Block 6...):
- data used / instruments; **which bands** the light curves were produced in
- how the data were analyzed: binning approach, background method
- how the spectrum was built; the **spectral model(s)** fit; the **fit statistic**
- the **parameter evolution** (which parameters, what trend)
- the **physics conclusion** claimed
- for every value: its **conventions** (time interval, energy band, model that
  defines it) + **source tier** + citation locus (table/figure/page)

### The firewall (blinding) — the load-bearing constraint
The same paper cannot both inform the analysis and score it: if the analysis agent
has read "they fit Band, Ep decayed 300→80 keV", the AI-vs-human test is
contaminated. Block 0 therefore splits into two roles:
- **Reference extractor** (reads papers/GCNs) → feeds **Block 8 scoring only**.
- **Analysis pipeline** (Blocks 1–7) → sees only raw data + the generic guides.

Dividing line: **factual inputs cross** the firewall (position, trigger time, z,
which instruments triggered — legitimately needed). **Methodological choices and
result values do not** (model, intervals, statistic, Ep/fluence, evolution,
interpretation) — quarantined as the answer key. In the we're-first regime there is
nothing to be blind to (pure production).

### Grounding discipline (mandatory)
Paper extraction is an LLM-judgement task with a known failure mode (hallucinated
citations/values — has bitten us before). **Every extracted field quotes its source**
(paper table/figure/page, or GCN circular number). No ungrounded values in the card.

### Tooling
- **New capability**: literature search (ADS API / arXiv / web) to *find* the
  publication — handbook `GCNIntelligence` only does GCNs.
- **Merge three existing assets** into one Stage-0: handbook
  `ai/gcn_intelligence.py` + `data/gcn_parser.py`, the LATBright
  `skills/gcn_intelligence.md` workflow (its `gcn_measurements.csv` schema is the
  seed — extend with `source_tier` + convention columns), and the FXT GCN workflow.

### DECIDED 2026-07-10 (Vikas): uniform-first, reconcile-on-disagreement
- **(a) is the headline**: the pipeline analyzes every burst **uniformly with our
  correct statistical methods**, blind to the paper (firewall above); outcomes are
  compared at Block 8. This is both the honest "can AI do GRB analysis" test and
  what keeps Round-1 population statistics coherent.
- **(b) is the diagnostic, triggered by disagreement**: when Block 8 finds a real
  (convention-matched) difference, re-run with *their* choices — bands, intervals,
  model, statistic — and ask **"can we reconcile to them?"** Two outcomes, both
  reportable: *reconciled* → the difference was method-choice, now quantified
  (systematic method-sensitivity across the literature); *not reconciled* → an
  execution discrepancy to investigate (theirs or ours). In-house precedent: the
  Burgess 130427A reproduction (`notes/burgess_reproduction_findings.md`).
- Extractor consequence: the reproduction card must capture choices at
  re-run fidelity (exact intervals/bands/model parametrization/statistic), since
  any card may later drive a reconciliation run.

### The literature model registry (Vikas, 2026-07-10)
Block 0's extractor also **harvests every spectral model encountered across the
published works** into a growing registry — model name, parametrization,
conventions (e.g. Ep-vs-E0 form), and which papers used it. Block 6 draws on this
registry: our core set + literature-harvested models **+ combinations** (Band+BB,
CPL+BB, SBPL+BB, 2SBPL, cutoff variants, ...).
- **Seeds that already exist**: engine-10 `MODEL_SPECS` (6 models, Two_Breaks) and
  the LATBright 17-model engine variant (+ LLE/LAT joint) — registry entries #1.
- **Guard (statistical discipline)**: a bigger model zoo must not become
  model-fishing. Registry models run under the SAME selection doctrine — ΔAIC≥10,
  physical-validity gates, nested/non-nested LRT rules — and additions to the
  *default* comparison set are a deliberate, documented decision, not automatic.

### The model-space sweep is a PHASE-0 task, done BEFORE any fitting (Vikas, 2026-07-10)
The registry is built **up front, in one sweep, before the pipeline models anything**
— not accreted burst-by-burst. Reason: uniformity. If the registry grows mid-run,
burst #1 is fit with fewer models than burst #106 and every population fraction is
incoherent. The model space is the **third freeze** (alongside the frozen sample and
the frozen tool commit).
1. **Sweep**: papers on the 106 single-pulse bursts + the canonical prompt-emission
   model literature → every model, with parametrization, bounds/seeds, nesting
   relations, and the combination rules (which components may combine, e.g. +BB) —
   enumerated up front, not ad hoc.
2. **Freeze registry v1** (dated, versioned). ALL Round-1 fits use v1 identically.
   New models published mid-run → v2, applied only in a documented re-run or
   Round 2 — never mid-sample.
3. **Implementability tier per model**: (i) in astromodels/3ML now, (ii) trivially
   composable, (iii) needs real implementation (e.g. physical synchrotron). The
   sweep records ALL; the frozen *fit set* = the implementable subset with the
   deferred models explicitly listed — an auditable claim with stated exclusions.
The sweep itself is a pure Block-0-type agentic literature task (search + grounded
extraction, no instrument code) → **the program's first deliverable** and an early
end-to-end demonstration of the agent doing scientist-work.

---

## Block 1 — Data acquisition  **[DESIGNED 2026-07-10]**

**Contract**: trigger + dossier *facts* (position; instruments; LAT FoV geometry) →
complete, versioned, locally resolved dataset + a frozen **data manifest**.

### Rules (Vikas, 2026-07-10)
1. **Availability first**: discover what exists for this burst, then fetch.
2. **Most-recent versions, always** — especially response files (RSP/RSP2 updates
   fix real bugs). Version-resolution rule: highest v## of each product.
3. **TTE is the primary data** — event mode → arbitrary re-binning, which the
   time-resolved analysis (Blocks 5–6) requires. CSPEC/CTIME are cross-checks and
   the tail-fallback (below), not the primary.
4. **LLE whenever available** → LLE time-resolved analysis (LATBright paradigm:
   LLE BB blocks, cutoff evolution).
5. **LAT utilized even when upper-limits-only** — standard likelihood in time bins;
   ULs still constrain the broadband SED and cutoff/Ep evolution. Pull rule is
   **geometric, not sociological**: fetch LAT/LLE whenever the burst was in the LAT
   FoV at trigger (from FT2/trigdat), not only when a LAT detection was announced —
   the ULs matter precisely for bursts nobody wrote a LAT GCN about.

### The gate here = the manifest freeze (no human approval; it's plumbing)
Acquisition ends by writing a **data manifest**: every file, version, checksum,
source server, download timestamp — stamped into provenance. Re-analysis either
reproduces the manifest or documents the version diff. (Closes the response-version
reproducibility leak.) Completeness QC runs here too: all requested detectors' TTE
present; RSP2 matrices span the analysis interval (the rsp2-collapse gotcha —
handled in engine-10, must ship with the package).

### Edge rules
- TTE spans ~T0−25 → +300 s. Emission beyond that (rare in single-pulse; real in
  Round 2) → **CSPEC continues the tail** — documented fallback, not improvisation.
- Judgement content is near-zero by design; the one soft spot ("is this dataset
  complete enough to proceed?") is a checklist in the guide, not free judgement.

### Benchmark metric
Not scored as judgement — scored as **operational reliability** across agentic
systems: complete unaided acquisition, correct versions, sane failure handling.
(The Codex trial already showed systems differ exactly here: env friction, path
assumptions. Paper material for the operational-failure-modes section.)

### Tooling
Handbook `FermiFetcher` (TTE/CSPEC/RSP/trigdat + LAT dir) is the base. Extend with:
POSHIST fetch (Two_Breaks `download_poshist`), LLE products (`gll_lle_*`,
`gll_cspec_*lle` rsp), LAT FT1/FT2, the version-resolution rule, the Pulsewise
multi-location resolver, and the manifest writer. `ensure_analysis_env()` already
handles the platform side.

---

## Block 2 — Detector selection  **[DESIGNED 2026-07-10]**

**Contract**: position + POSHIST pointing → detector set, gated + stamped.

### The rule source (Vikas, 2026-07-10): the Fermi GBM team's own published criteria
Detector selection is deliberately **straightforward**: adopt the selection rules
stated in the official GBM burst/spectral **catalog papers** (the Goldstein / Gruber
/ von Kienlin / Poolakkil catalog series) as-is, with citations. Not our invention —
the instrument team's prescription. Referee-proof by construction.

- **Phase-0 extraction task** (small; same grounded-extraction machinery as the
  model sweep): pull the exact selection text from each catalog generation —
  angle threshold, max-N-detectors, blockage/occultation exclusions, BGO choice —
  verbatim + cited. Catalog generations differ in details; the extraction decides
  ONE documented convention. *No rule goes into the guide from memory — quote the
  paper.*
- **Known delta to resolve in that extraction**: our implemented rule
  (NaI ≤50° pre-tick, code-cited to Goldstein+2012 conservative cut; BCAT rescue
  50–60°; closest-BCAT fallback; same-side BGO; hemisphere GUI) vs the catalogs'
  prescriptions — the catalogs also apply **blockage exclusions**
  (spacecraft/LAT/solar-panel) that we do not compute; BCAT membership only
  proxies it. Adopt exactly or document the deviation.

### Judgement (shrunk by design)
Rule application + a thin confirmation gate: borderline angles, suspected blockage,
contaminating sources. The picker (hemisphere GUI / ai_vision) remains the approval
instrument; seeds = the catalog rule's output.

### Benchmark role: the CONTROL block
Rule-based ⇒ inter-human scatter should be near-zero ⇒ if an agentic system can't
match experts here, the failure is *operational*, not judgement — calibrates the
whole leaderboard. Metric: detector-set Jaccard (scripts/40, built).

### Freeze discipline
The 25-burst benchmark keeps its frozen instrument (current Two_Breaks rules)
regardless. The catalog-literal rule is frozen for the handbook pipeline's Round-1
production; any delta vs the benchmark-era rule is documented, never silently
harmonized mid-campaign.

### Tooling
POSHIST quaternion geometry (Two_Breaks `00_prototype`, verbatim across projects —
pure library material) + hemisphere picker + gate: all built; port per
`CONSOLIDATION_PLAN.md` (POSHIST canonical, TRIGDAT fallback). New: the blockage
check *if* the extraction says the catalogs require it.

### Addenda (Vikas, 2026-07-10)
- **The pass-through flag, polished to perfect**: the user chooses per run whether
  AI-preselected detectors **auto-pass** (stamped `ai_vision`, no GUI opens) or must
  go through the GUI (`human_gui`). The mechanism exists (scripts/39
  `APPROVAL_MODE`); it needs polish until it "just works" — the user asks for a
  mode, the AI runs that mode, the stamp records it. Applies to Blocks 2–4 alike.
- **gtburst parity in the picker**: the detector panel must also offer **LLE and
  LAT** as selectable entries (gtburst's detector list has them; ours stops at
  n0–nb/b0/b1). Pairs with Block 1's geometric LAT pull rule.

---

## Block 3 — Background modeling  **[DESIGNED 2026-07-10]**

**Contract**: per-detector LC (+ manifest) → pre/post background windows +
polynomial background, gated + stamped. **The judgement-heaviest block** — window
placement against orbital trends is where inter-human scatter concentrates.

### Current mechanism (built, benchmark-frozen)
Render LC PNGs → **AI vision** proposes windows (or human draws them in the
BackgroundSelector GUI) → gate stamps `ai_vision`/`human_gui` + `WINDOW_SOURCE` →
3ML two-stage polyfit + residual panel for the approval judgement. Same
pass-through flag as Block 2: user picks the mode, stamp records it.

### Three-tier design (Vikas, 2026-07-10)
**Tier 1 — the expert rulebook (the guide).** `dev/ai_guides/background_selection.md`
grows into a real skill: *what a background is* (pedagogy for the agent), then
concrete expert-authored placement rules — how the pre-GRB interval is chosen,
where the burst is expected to be, how the post interval is chosen, what widths
(~50–150 s/side). The archetype rule (already field-proven): **"if the light curve
cuts off abruptly at the end, never place a window there"** — written down once,
and the AI applied it correctly thereafter. That is the guide mechanism working:
human expertise enters the pipeline as written rules, versioned in git.

**Tier 2 — the phenomenology atlas (Phase-0 extraction task #3).** The GBM
*physical* background literature (candidate ref: the Biltzinger et al. physical
background model for GBM — verify in extraction) describes what real backgrounds
look like: orbital modulation, SAA proximity, cosmic-ray components, source
occultation steps. Extract the **shapes** into the guide so the agent can
*recognize* background behavior from the LC/arrays **without fitting the physical
model** — "this ramp is orbital, don't fight it with a wide window"; "that step is
an occultation, exclude it." Pattern recognition grounded in published physics.

**Tier 3 — future robust upgrade (explicitly NOT Round 1).** Actually *fit* the
physical background model to derive the background, replacing interval
interpolation entirely. Roadmap item for later rounds; Round 1 stays
interval-selection + polynomial — the method the papers, the benchmark, and the
expert panel all use.

### Convention DECIDED 2026-07-10 (Vikas): follow gtburst
Background polynomial order = **whatever gtburst does** — same inheritance move as
Block 2 (adopt the instrument-standard tool's convention, don't invent one).
**Source-verified** (bundled gtburst, `GtBurst/dataHandling.py:2996–3043`,
`_fitGlobalAndDetermineOptimumGrade`): fit channel-summed counts over the bkg
intervals with grades **0–4**; successive-grade **LRT** `2·ΔlogL ≥ 9.0` (Wilks
≈3σ/1 dof); best grade = highest justified, else 0. Consequences: the handbook's
`utils/gtburst_bkg.py` (`select_grade_lrt`, threshold 9.0) is already the faithful
implementation → becomes THE convention; `gbm_analysis.py`'s BIC(0–4) path is
retired/relabeled at the consolidation Phase-3 port. (Supersedes the imprecise
"LRT ≤3" note in CONSOLIDATION_PLAN.)

### Benchmark metric
Edge-Δ + IoU per window vs the expert panel (scripts/40, built) with inter-human
scatter as the denominator; plus the downstream-impact check — does the bkg choice
shift fitted parameters beyond their uncertainties? Papers rarely publish exact bkg
windows ⇒ for the published regime, background is scored mostly *through* its
downstream effect (Blocks 5–6 agreement), not window-vs-window.

### Tooling
BackgroundSelector GUI + render/ai_vision + gate: built (post-fix commit e4ee786).
Merge in Pulsewise `bkg_select.py` best features (χ²ᵣ overlay, dropout detection —
the "abrupt cut" rule's algorithmic sibling) per CONSOLIDATION_PLAN. Guide
enrichment (Tiers 1–2) is doc work, no code risk, can start now.

---

## Block 4 — Source / emission interval  **[DESIGNED 2026-07-10]**

**Contract**: background-subtracted LC (+ Block-3 background) → emission window
[t1, t2], gated + stamped; feeds binning (Block 5) and fitting (Block 6).

### Selection logic (Vikas, 2026-07-10) — inherit the instrument's own detection logic
- **Start**: the **GBM trigger-algorithm logic itself** — rate exceeds background by
  the trigger threshold — plus a safety margin before it. (Same inheritance move as
  Blocks 2–3: the instrument team's logic, not our invention.)
- **End**: where the emission **merges back into the background** — signal within
  the last ~2–3σ of the background level.
- **Re-emission rule**: emission recurring later above the σ-threshold → extend the
  window to include it (multi-pulse / extended emission).
- **Built and field-proven**: the T_INT algorithm (smoothed-rate threshold + Fermi
  4.5σ noise floor + multi-pulse extension) — implementations exist in BOTH
  Two_Breaks and PulsewiseAmatiYonetoku, one did "a pretty good job".
  **Consolidation action: head-to-head the two, keep the better** (added to
  CONSOLIDATION_PLAN matrix).

### Approval loop
Selected window rendered over the LC **with the background-subtracted residuals**
→ human approves/adjusts in the GUI (source-marker rebuild per GUI_REQUIREMENTS
R-SM-2..6, incl. real-time gap validation), or ai_vision pass-through (flag,
stamped). AI-selected vs human-adjusted is exactly what the benchmark scores
(edge-Δ/IoU, scripts/40 — built).

### The guide
Expert-authored rules markdown (Block-3 rulebook mechanism): margin sizes, σ
thresholds, precursor and late-pulse handling, when the re-emission rule fires,
slow-riser suspicion flags.

### Tier 2 — future (explicitly NOT Round 1)
**Slow-rising bursts** defeat threshold-crossing logic. Published approach exists:
automatic burst detection via **physical background modeling + multi-detector,
higher-dimensional LC analysis** (candidate reference to pin down in the Phase-0
literature sweep — not named from memory). Rare in the single-pulse sample; real
for Round 2. Pairs with Block 3's Tier-3 physical background.

---

## Blocks 5–9 — to be designed (walk in progress)
Each gets its own section here as we discuss it, same depth as Blocks 0–1:
regimes/contract → judgement points → guide contents → gate → benchmark metric →
tooling (existing asset to port vs new) → OPEN items.

## Open decisions ledger
| Decision | Owner | Blocks |
|---|---|---|
| ~~(a) vs (b) for published regime~~ **DECIDED**: uniform-first headline; reconcile-on-disagreement diagnostic + literature model registry | — | 0, 6, 8 |
| ~~Background polynomial convention~~ **DECIDED**: follow gtburst — successive-grade LRT 2·ΔlogL≥9, grades 0–4 (source-verified `dataHandling.py:2996–3043`); retire the BIC path at Phase-3 port | — | 3 |
| R-BG-18 width rule warn-vs-block (GUI_REQUIREMENTS) | Vikas | 3 |
| GUI OPEN items (R-GL-7, R-DP-7, R-BG-19, R-SM-3/6) | Khushboo | 2–4 |

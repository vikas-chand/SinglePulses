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

---

## Blocks 1–9 — to be designed (walk in progress)
Each gets its own section here as we discuss it, same depth as Block 0:
regimes/contract → judgement points → guide contents → gate → benchmark metric →
tooling (existing asset to port vs new) → OPEN items.

## Open decisions ledger
| Decision | Owner | Blocks |
|---|---|---|
| ~~(a) vs (b) for published regime~~ **DECIDED**: uniform-first headline; reconcile-on-disagreement diagnostic + literature model registry | — | 0, 6, 8 |
| Background polynomial convention **LRT ≤3** vs BIC(0–4) | Vikas | 3 (+ consolidation Phase 3) |
| R-BG-18 width rule warn-vs-block (GUI_REQUIREMENTS) | Vikas | 3 |
| GUI OPEN items (R-GL-7, R-DP-7, R-BG-19, R-SM-3/6) | Khushboo | 2–4 |

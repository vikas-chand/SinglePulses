# Benchmark plan — per-task AI guides + human-vs-AI scoring

Goal (V. Chand, 2026-06-27): make the whole pipeline a set of **AI-executable tasks**,
each with (1) an `.md` that guides an AI to do the job, and (2) a **metric** that scores
how well the AI did it against a human baseline. This operationalizes the agentic-AI
methods paper (`paper_agentic/agentic_grb.tex`); the `APPROVAL_MODE` stamp
(`human_gui` vs `ai_vision`) on every selection is the experimental control.

## Principle
For every task: **guide → do (both modes) → score.** Run the task in `human_gui` and
`ai_vision` mode on a common benchmark subset, then measure (a) task-level agreement
and (b) the downstream impact on the physics. "How well the AI did" = both numbers.

## Which tasks carry real AI *judgement* (and so are benchmarkable)
Stage 1 selections are genuine visual judgements; Stages 2--3 are deterministic code
the agent merely runs (no judgement to score, but still get a run-guide).

| # | Task | AI judgement? | AI-guide `.md` | Benchmark metric (AI vs human) |
|---|------|---------------|----------------|--------------------------------|
| 1 | Detector selection | yes | `dev/ai_guides/detector_selection.md` | approved-set Jaccard; missed/extra dets; angle of disagreements |
| 2 | Background windows | yes | `dev/ai_guides/background_selection.md` | pre/post edge Δ (s); window IoU; polynomial-fit residual χ²/dof; baseline-flatness |
| 3 | Source / emission interval | yes | `dev/ai_guides/source_selection.md` | source edge Δ (s); IoU; fractional duration error |
| 4 | Binning (3ML BB + sig) | no (deterministic given source) | covered by `AGENTS.md` | induced block-count & edge agreement (consequence of #3) |
| 5 | Spectral fitting + model selection | no (deterministic AIC) | covered by `AGENTS.md` | n/a directly; see downstream-impact |
| 6 | QC / bad-fit flagging (optional) | yes | `dev/ai_guides/qc_flagging.md` | agreement on flagged-bad bins/bursts (precision/recall vs human) |

## Downstream-impact metric (the decisive test, shared by all tasks)
Run the identical Stage 2--3 on the human-mode and AI-mode catalogs and compare, per
bin and per burst: $E_{\rm p}$, low-energy index $\alpha$, blackbody $kT$ (where
preferred), and the thermal-vs-double-break classification. Report per-parameter
scatter + correlation + intrinsic scatter, and classification concordance. The headline
question: **do the scientific conclusions survive the human→AI swap?**

## AI-guide `.md` shape (follows the project skill convention)
Each guide is self-contained and tells an AI exactly how to make that one judgement:
prerequisites → inputs (which PNG/manifest) → the decision criteria (what to look for in
the light curve) → output contract (what to write into the `decision.json` fields) →
QC checklist → common pitfalls. They complement the `scripts/39` `decision.json`
schema by giving the *judgement criteria*, not just the data format.

## Benchmark harness (BUILT: `scripts/40_benchmark.py`)
- inputs: **>=2 per-rater catalogs** (each expert + the AI), produced by running
  `scripts/39` with `--out`/`--approval-dir` so each rater writes a SEPARATE catalog
  (distinguished by `APPROVED_BY` + `APPROVAL_MODE`). `--catalog-dir` or `--catalogs`.
- computes, over every rater PAIR on common bursts: detector Jaccard; bkg pre/post edge
  Δ + window IoU; source edge Δ + IoU + fractional-duration error. Pairs split into
  **HUMAN-vs-HUMAN (the denominator)** and AI-vs-HUMAN; per metric it reports whether
  AI-vs-human falls within the human-vs-human band.
- pure numpy/astropy (light), deterministic, re-runnable; `--csv` dumps per-item metrics.
- downstream parameter-impact is stubbed (fill once the dual-mode fits exist).
- QC-flagging (task #6) scoring (precision/recall vs human flag sets) is specified in
  `dev/ai_guides/qc_flagging.md`; harness support to be added when flag files exist.

## AI task-guides (BUILT: `dev/ai_guides/`)
One per judgement task, grounded in the real code/criteria, telling an AI exactly how
to make the call (and how it will be scored): `detector_selection.md`,
`background_selection.md`, `source_selection.md`, `qc_flagging.md`.

## Protocol
1. Pick $N_{\rm bench}$ bursts (~20--30; include faint + complex-background cases).
2. Run `scripts/39` Stage 1 in **both** modes → two catalogs (out-paths kept separate).
3. Run Stage 2--3 on each → two fit catalogs (fresh out-roots).
4. `scripts/40_benchmark.py` → agreement + impact report + figures.
5. Fill `paper_agentic/agentic_grb.tex` §5 Results from the report (no fabrication).

## Decisions (locked 2026-06-27/28, Vikas)
- **Baseline = multiple experts.** Inter-human scatter is the denominator; a system is
  "good" if it matches each human about as well as humans match each other. Needs
  >=2 human approvers on the benchmark subset; the harness handles N catalogs.
- **Task list includes #6 (QC flagging).** All four guides built.
- **Benchmark MULTIPLE agentic SYSTEMS** (2026-06-28): OpenAI Codex (GPT-5.6), Google
  Antigravity (Agy), Anthropic Claude Code -- each runs the WHOLE pipeline (data
  download -> detectors -> background -> source -> Bayesian blocks + significance bins
  -> 3ML fits) reading the SAME `.md` guides (AGENTS.md + dev/ai_guides/). The guides
  are the fair-comparison control: differences = the model, not the prompt. Each system
  writes its own stamped catalog (`APPROVED_BY`="Codex/Antigravity/Claude Code (AI)",
  `APPROVAL_MODE=ai_vision`). `scripts/40_benchmark.py` reports a per-SYSTEM leaderboard
  vs the human band + system-vs-system agreement.
- Guides live in `dev/ai_guides/`.

## Experts (DECIDED 2026-06-30, Vikas)
The human panel is **two experts, labelled `Expert1` and `Expert2`** in the catalogs
and the paper: Expert1 = V. Chand, Expert2 = K. Sharma (mapping recorded here; the
paper reports only the labels). Each approves the same 25 benchmark bursts
independently — no discussing selections until both catalogs are written. With two
experts the inter-human band is the distribution of the single Expert1–Expert2
pair-metric over the 25 bursts.

Per-rater isolation (each rater = own approval dir + own catalog; run from repo root):
```bash
# Expert1 (Vikas, macOS — no MPLBACKEND prefix needed)
python scripts/39_approve_all.py gui --approver "Expert1" \
    --approval-dir results/benchmark/expert1_approval --out results/benchmark/expert1.ecsv \
    --trigger <bn...>            # once per burst in dev/benchmark_sample.ecsv

# Expert2 (Khushboo, Linux)
MPLBACKEND=TkAgg python scripts/39_approve_all.py gui --approver "Expert2" \
    --approval-dir results/benchmark/expert2_approval --out results/benchmark/expert2.ecsv \
    --trigger <bn...>

# Each AI system (Claude Code / Codex / Antigravity), same guides, own catalog:
#   render + judge + ingest with
#   --approval-dir results/benchmark/<system>_approval --out results/benchmark/<system>.ecsv
#   stamped APPROVED_BY="<System> (AI)", APPROVAL_MODE=ai_vision

# Score everything:
python scripts/40_benchmark.py --catalog-dir results/benchmark
```
NOTE: the benchmark catalogs are SEPARATE from the production Stage-1 approval
(Khushboo's 106-burst job under her real name -> results/background_intervals.ecsv);
don't mix the two. AI raters must not read the expert approval dirs (isolation is the
blinding).

## Benchmark sample (DECIDED 2026-06-30): `dev/benchmark_sample.ecsv`
$N_{\rm bench}=25$, deterministic (code-generated, no random draws):
- **6 hard-background bursts** — the deterministic-selector source-window failures
  (bn090620400, bn090719063, bn100612726, bn100614498, bn110920546, bn200524211);
- **4 anchors** — bn110721200 (standout two-break), bn130427324 (brightest, Ep–kT
  anchor), bn150902733 (top decile), bn260105973 (median fluence);
- **15 stratified fills** — faintest/median/brightest of each fluence quintile.
Spans 245× in fluence, T90 7–453 s, 5 LAT/LLE bursts, all quintiles populated.
Every rater (≥2 experts + each AI system) approves exactly these 25 via scripts/39
with `--approval-dir`/`--out` per-rater isolation.

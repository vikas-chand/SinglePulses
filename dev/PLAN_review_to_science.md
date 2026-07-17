# Plan: from reviewed selections → science (applies to ALL bursts)

What happens to a burst once its Stage-1 selections (detectors + backgrounds + source)
are approved. Identical for Vikas's LLE bursts and Khushboo's remaining bursts; the
only difference is whether a burst has **real LLE signal** (adds the high-E arm).

## Two catalogs, kept separate (the benchmark)
- **AI arm** — `results/background_intervals.ecsv` (Claude+Codex consensus, all 106).
- **Human arm** — `results/background_intervals_human.ecsv` (ingested from the
  `human_gui` `*_decision.json`). *Same fitting engine both sides*, so any physics
  difference traces only to the Stage-1 selections — the downstream-impact test.

## Phase A — Approve (Stage 1)  [in progress]
- Human review → `results/approval/<trig>_decision.json` (mode=human_gui). Vikas: the
  13 LLE bursts (12–13 valid). Khushboo: the remaining ~93 non-LLE bursts + any fixes.
- Special bursts follow `dev/special_bursts.md` (e.g. **130427A → 2nd pulse**).
- Gate: source must sit in every detector's background gap (R-SM-4 warns in the GUI;
  ingest is the hard backstop).

## Phase B — Ingest (build the human arm)
- `scripts/39 ingest` the human decisions → `background_intervals_human.ecsv`
  (whole-trigger replacement — no stale rows from deselected detectors; audit-fixed).
- Keep the AI catalog untouched.

## Phase C — Bin (two-tier, per burst)
1. **Fine GBM grid** — `scripts/27b` on each burst from *its* source + backgrounds
   (brightest-NaI Bayesian blocks + significance merge) → `clean_blocks_human/`.
2. **Coarse LLE grid** — `scripts/27c` ONLY for bursts with real 30–100 MeV LLE
   signal (≥3σ; ~10 of the 13) → `clean_blocks_lle_human/`. Background-only LLE
   bursts get no LLE grid and use the GBM bins.

## Phase D — Fit  [BLOCKED on task #21 for the LLE arm]
1. **Fine GBM** — `scripts/10` (6 base models + shape/highe) on the fine grid →
   `clean_per_burst_human/`. Standard time-resolved spectroscopy.
2. **Coarse LLE (high-E arm)** — `scripts/10 --blocks-file clean_blocks_lle_*
   --models highe --include-lat` on the COARSE grid FIRST → the high-E shape census
   (cutoff above the peak / Band+CPL saddle / extra hard PL), where LLE+LAT actually
   constrain >30 MeV. Then the fine GBM grid for detailed GBM evolution.
- **Must land first (Codex audit, task #21):** scripts/10 (a) keep a NaI fixed as the
  effective-area reference even on an LLE-driven grid; (b) skip / raise on all-failed
  LLE instead of silently GBM-only; (c) stamp grid-type/inputs and use unique
  output/tem/ filenames so coarse & fine don't collide.
- Run the AI arm through the SAME Phases C–D into parallel dirs
  (`clean_per_burst_ai/`) for the comparison.

## Phase E — Products + benchmark
- Best-model selection (ΔAIC≥10 + valid-parent), census, correlations, figures,
  tables — `scripts/31–38`. (Extend `scripts/31` to the high-E models first.)
- **Benchmark** — `scripts/40`: AI-dir vs human-dir per (burst, block); does the
  physics survive the human→AI swap? Inter-expert scatter (Vikas vs Khushboo) is the
  denominator. Vikas leads the agentic paper; Khushboo leads the science paper.

## The shortcut hypothesis (Vikas)
Because the engine is identical both arms, if we can *characterise* how a selection
difference (a shifted background / detector / source) propagates to Ep, α, kT, and the
model verdict, we may be able to BOUND the AI-vs-human effect without a full second
spectral run. Test on the 13 LLE bursts first (both arms), then decide.

## Status snapshot (2026-07-17)
- LLE Stage-1: 12/13 valid (130427A pending its b1/na background fix).
- 27c (coarse LLE blocks) built + validated, 30–100 MeV, signal-gated.
- Codex audit criticals fixed; remainder in task #21 (blocks Phase D LLE fits).

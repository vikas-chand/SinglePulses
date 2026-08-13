# AI Guide: Source / emission interval selection
> Part of the benchmark framework (dev/BENCHMARK_PLAN.md). Complements the decision.json schema in scripts/39_approve_all.py by giving the JUDGEMENT CRITERIA.

**Purpose** — Mark the burst's emission interval `[t1, t2]`: the single contiguous span on the light curve where there is genuine prompt gamma-ray signal above background, from the first rise to the last decay back into the noise. This is the time region Bayesian Blocks runs over in Stage 2 (scripts/27b), so it sets which counts ever become spectral bins.

**When to use** — Stage 1, after you have approved detectors and background windows for a burst. You judge from the rendered NaI light-curve PNG(s), then write the `source` field of `<trigger>_decision.json`.

**Which decision.json field this fills** — the `"source": {"t1": <float>, "t2": <float>}` object (both floats, trigger-relative seconds, `t2 > t1`). This is shared across all approved detectors; it is the per-burst emission window, not per-detector.

## SPECIAL BURSTS — check first
**Before selecting the source, consult `dev/special_bursts.md` for per-burst overrides.**
For multi-episode bursts the default peak-find grabs the brightest spike, which is the
WRONG pulse. Known override: **bn130427324 (GRB 130427A) → analyse the SECOND pulse
(~105–185 s), not the bright 0–40 s spike.** If a burst is listed there, follow that
instruction over the peak-find suggestion, and set the post-background AFTER the target
pulse so the other episode falls in the excluded gap.

## Inputs (what to read)
- `plots/approval_lc/<trigger>_<det>.png` — one per approved detector. **Judge the source on the brightest / lowest-angle approved NaI.** Each is a 1.024-s binned LC, NaI band 8–900 keV, linear y-axis, x = "Time since trigger (s)". Deliberately **no T90 shading** — identify the burst region from the data alone.
- `results/approval/<trigger>_pending.json` — the candidate manifest. Read `suggested_source` (`{t1, t2}`): a peak-find estimate already tightened inside the brightest NaI's background gap. Treat it as a starting proposal to confirm or adjust, not ground truth.
- The background windows you just approved: `pre = [t1,t2]`, `post = [t3,t4]` per detector. The source MUST fall in the gap `[pre_stop, post_start]` (see Output contract). *(Parity note: the human GUI source marker draws these same windows in green with dashed gap-boundary lines — R-SM-7 — so both raters judge the source against identical background context.)*

## Decision criteria (the heart)
You are drawing the smallest contiguous interval that still contains **all** of the burst emission. Concretely, on the brightest-NaI 1.024-s LC:

1. **Find the peak.** Locate the highest sustained count-rate excess above the flat background level (the level set by your pre/post windows). A real peak rises clearly above the Poisson scatter of the baseline (the heuristic threshold is ~4.5σ of the smoothed background noise; visually: a bump several times the bin-to-bin baseline jitter).
2. **Set t1 (rise edge).** Walk LEFT from the peak. Stop where the rate falls back to roughly background — about **1σ of the noise above baseline** is the code's walk-out criterion (scripts/27b `emission_window`). Put `t1` just *before* the first clearly-elevated bin (the heuristic pads ~0.5 s outward). Do not start in the flat pre-burst baseline.
3. **Set t2 (decay edge).** Walk RIGHT from the peak the same way; stop where the rate has decayed back to ~1σ above baseline and stays there. Include the full tail of a long, slow decay — under-cutting the tail throws away real soft late-time emission.
4. **Keep it ONE contiguous span.** For a single-pulse burst this is one rise–peak–decay. If there are several sub-pulses close together (a multi-peak but still-single complex), span from the first rise to the last decay — do NOT split, and do NOT exclude a brief inter-pulse dip if emission resumes (the code's secondary-peak extension re-extends across dips while a nearby peak exceeds ~2× threshold).
5. **Tightness matters.** A window much wider than the emission lets Bayesian Blocks run over mostly-quiet time and collapse to one block, which merging cannot undo. Err toward tight-but-complete: every elevated bin in, baseline bins out. (27b will re-tighten inside your window with the same peak-find, so an over-wide window is partly self-correcting — but an over-*narrow* window that clips real emission is not recoverable.)
6. **Faint / no clear peak.** If no bin clearly clears the noise floor, you may keep the full background gap as the source (this is the heuristic's fallback) — but prefer the `suggested_source` if it isolated a marginal bump. Flag low confidence in `reasoning`.

## Output contract (exact JSON to write into `<trigger>_decision.json`)
Add the `source` object to the decision file (alongside `detectors`, `windows`, etc.):
```json
{
  "trigger": "bn110721200",
  "approver": "Claude (AI)",
  "mode": "ai_vision",
  "source": {"t1": -0.30, "t2": 9.80},
  "windows": { "...": "per-detector pre/post" },
  "reasoning": "single FRED pulse; rise ~ -0.3s, decay tail back to baseline by ~9.8s"
}
```
- `t1`, `t2` are floats in trigger-relative seconds; require `t2 > t1`.
- HARD CONSTRAINT (validated by `_validate_decision`): for **every** approved detector with windows `pre=[a,b]`, `post=[c,d]`, you must have `b <= t1` and `t2 <= c`. The source must lie strictly inside every approved detector's background gap, or ingest rejects the whole burst as INVALID.

## QC checklist (self-check before approving)
- [ ] `t2 > t1`, both finite floats, trigger-relative seconds.
- [ ] `pre_stop <= t1` and `t2 <= post_start` for EVERY detector in `windows` (the tightest gap wins).
  ⚠ **This rule is a Stage-1 WARNING, not an invariant of the shipped catalog** (2026-08-12,
  after TWO operators independently re-flagged adjudicated rows): the human gate may ACCEPT an
  overrun (GUI soft-warn + override), and accepted overruns are recorded in
  `results/human_review_qc_flags.txt` (20 detector-rows across 16 bursts as of 2026-08-12,
  BGO-dominated). Any validator of the shipped catalog MUST join that ledger and report only
  UNADJUDICATED violations — `scripts/43_catalog_validator.py` is the reference implementation.
  A QC check that ignores the decisions ledger manufactures alarms (the F-2 class).
- [ ] `t1` sits just before the first clearly-elevated bin; the rate at `t1` is near baseline, not mid-rise.
- [ ] `t2` is past the last elevated bin; the tail has returned to baseline (no truncated decay).
- [ ] Exactly one contiguous interval — no real emission excluded between t1 and t2.
- [ ] Window is not grossly wider than the visible emission (no long quiet flanks inside).
- [ ] Cross-checked against `suggested_source`; large deviations are intentional and noted in `reasoning`.

## Common pitfalls (failure modes a human reviewer would catch)
- **Clipping the soft tail** — stopping `t2` at the visual "knee" of an FRED instead of where it merges into noise; loses real late-time bins.
- **Starting in the baseline** — putting `t1` tens of seconds before the rise (e.g. trusting a catalog T90 start); inflates the quiet fraction and risks the BB-collapse-to-one-block failure.
- **Over-wide source = the whole gap** — using `[pre_stop, post_start]` verbatim for a bright burst; defeats the tightening and weakens binning.
- **Splitting a multi-pulse complex** — emitting two intervals or excising an inter-pulse dip; the schema is a single [t1,t2] and sub-pulses belong to one window.
- **Wrong reference detector** — judging the edges on a high-angle or BGO PNG where the pulse is weak; always use the brightest NaI.
- **Gap violation** — setting `t1`/`t2` that overlap any approved detector's pre/post window; silently rejected at ingest.
- **Confusing precursor/extended emission with background** — a faint precursor or a low-level extended tail is still emission; include it if it is real (above noise), exclude it if it is baseline scatter.

## How this is scored vs humans (benchmark metric)
From dev/BENCHMARK_PLAN.md (Task 3), run in `human_gui` and `ai_vision` modes on the common benchmark subset and compare AI's `[t1,t2]` to the human's:
- **Source edge Δ (s)** — `|t1_ai − t1_human|` and `|t2_ai − t2_human|` (rise and decay separately; report median + spread).
- **IoU** — intersection-over-union of the two intervals (1.0 = identical span).
- **Fractional duration error** — `(dur_ai − dur_human) / dur_human`, where `dur = t2 − t1`.
- **Downstream impact (decisive test)** — run identical Stage 2–3 on both catalogs; compare induced block count and edges (Task 4) and the per-bin/per-burst Ep, α, kT and thermal-vs-double-break classification. The headline question: do the scientific conclusions survive the human→AI swap? Inter-human scatter (if multiple experts) is the denominator: the AI is "good" if it matches humans about as well as humans match each other.

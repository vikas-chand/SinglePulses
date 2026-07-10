# Project structure — two parts

This project has two parts, run **in order**. Part 1 validates the analysis *method*;
Part 2 uses the validated method to do the *science*. (Operational how-to for running
anything is in `AGENTS.md`; this file is the map of *what the project is*.)

> **Longer-term frame (2026-07-10):** both parts are Round 1 (single-pulse sample) of
> the broader "GRB AI Scientist" program — block-by-block design in
> `dev/AI_SCIENTIST_BLOCKS.md` (feeds `paper_agentic/`); Round 2 scales to the full
> GBM catalog; the consolidated pipeline lives in the GRB_Handbook repo.

```
                shared pipeline + data
  scripts/39 (gated approval) -> 27b (binning) -> 29/10 (fits) -> 31-38 (products)
        |                                                              |
   PART 1 benchmarks these steps                              PART 2 reports the physics
```

## Part 1 — Benchmark: the AI does the work, compared with humans
**Paper:** `paper_agentic/agentic_grb.tex` — *"Agentic AI Analysis of Single-Pulse
Fermi/GBM GRBs"* — **lead: V. Chand.**
**Question:** can AI agents reproduce expert selections (detectors, background,
source, QC), and do the scientific conclusions survive the human→AI swap? We benchmark
**several agentic systems** — OpenAI Codex, Google Antigravity, Anthropic Claude Code —
each running the *whole* pipeline (download → detectors → background → source → Bayesian
blocks + significance bins → 3ML fits) from the *same* `.md` guides (so differences are
the model, not the prompt), scored against human experts **and against each other**.
**How:** every judgement step has an AI-guide in `dev/ai_guides/` and a metric; the
gated approval (`scripts/39`) stamps each selection `human_gui` vs `ai_vision`;
`scripts/40_benchmark.py` scores AI-vs-human with **inter-human scatter as the
denominator** (the AI is "good" if it matches experts as well as experts match each
other). Framework: `dev/BENCHMARK_PLAN.md`.
**Needs:** a dual-mode run — ≥2 human experts + the AI each approve the same
~20–30 benchmark bursts, then `scripts/40` + the downstream-impact check.
**Status:** scaffolding built (guides + harness + per-rater plumbing); awaiting the
dual-mode approvals.

## Part 2 — Science: our own analysis of single-pulse GRBs
**Paper:** `paper/two_break.tex` — the single-pulse time-resolved spectroscopy
results (curvature / two-break, $E_{\rm p}$–$kT$, spectral evolution) — **lead:
K. Sharma.**
**Question:** the physics of single-pulse GRB prompt emission across the 106-burst
sample.
**How:** the same pipeline, run on the full sample, using selections that are
**validated by Part 1** — i.e. we can trust AI selections at scale (with human
approvals as the gold standard) *because* Part 1 showed they match experts.
**Status:** draft filled with provisional numbers; the authoritative numbers await
the clean run on the approved backgrounds (see the science-paper section of memory /
`dev/AUTHORITATIVE_PIPELINE.md`).

## Why the order matters
Part 2's selections are the usual soft target for a referee ("why these detectors /
this background / this source window?"). Part 1 answers that *quantitatively* before
Part 2 leans on it: the same agentic selections that produce the science have been
benchmarked against multiple human experts. Validate the tool, then trust it.

## Shared infrastructure (used by both parts)
- `AGENTS.md` / `CLAUDE.md` — agent-legible run guide (env, data, the 3 stages).
- `scripts/39_approve_all.py` — gated approval (detectors + background + source).
- `scripts/27b_reblock_3ml.py` — binning (BB + significance hybrid).
- `scripts/29_refit_clean.py` → `scripts/10_spectral_fit_burst.py` — fits (6 models).
- `scripts/31`–`38` — products (numbers, figures, tables, manifest).
- `handoff_background_approval/` — collaborator handoff for the approval step.

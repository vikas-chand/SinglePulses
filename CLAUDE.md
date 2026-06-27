# CLAUDE.md

This repository's agent guide lives in **`AGENTS.md`** — read it first. It is the
single, tool-agnostic source of truth for running this pipeline (environment + CALDB
setup, data acquisition, the Stage 1→2→3 run order with exact commands, the
human-or-AI approval gate, products, gotchas, and audit items).

Quick orientation (full detail in `AGENTS.md`):
- **Pipeline:** Approve (detectors + background + source, gated & stamped) → Bin
  (`scripts/27b_reblock_3ml.py`, 3ML Bayesian-Blocks + significance hybrid) → Fit
  (`scripts/29_refit_clean.py` → `scripts/10`, 6 models, AIC selection) → Products
  (`scripts/31`–`38`).
- **Environment:** heavy tier = `conda activate threeML` + CALDB exports (binning,
  fitting, download); light tier = numpy/astropy/matplotlib (approval picker, tables).
- **Approval gate:** a human (interactive GUI) **or** you (AI-vision on the LC PNGs)
  may approve — always record the stamp (`APPROVED_BY/APPROVED_UTC/WINDOW_SOURCE`).
  Never fabricate an approval silently.
- **Run from the repo root.** Current catalog is provisional until the approved
  `results/background_intervals.ecsv` exists.

See also: `dev/AUTHORITATIVE_PIPELINE.md` (locked plan + the Stage-1 build spec).

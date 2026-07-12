# Two_Breaks inherits from GRB_Handbook (`import grb_pipeline as grb`)

Two_Breaks no longer duplicates the shared analysis logic — it **inherits** it from
the consolidated `grb_pipeline` package (the GRB_Handbook repo), the end-state of
`dev/CONSOLIDATION_PLAN.md`. This is done in **phases**, gated by the benchmark freeze.

## Install (both envs; `--no-deps` so the threeML stack is untouched)
```bash
/Users/salim/anaconda3/envs/threeML/bin/pip install -e ~/Desktop/Projects/GRB_Handbook_Project --no-deps
/Users/salim/anaconda3/bin/pip           install -e ~/Desktop/Projects/GRB_Handbook_Project --no-deps
python -c "import grb_pipeline as grb; print(grb.__version__)"   # 0.1.0
```

## Phase A — DONE (2026-07-11): the science path inherits
`scripts/pipeline_grb.py` runs Stage 2–3 (binning + spectral fitting) through
`grb_pipeline` — `grb.HybridBinner` (= frozen `scripts/27b`) and
`grb.SpectralEngine` (= frozen `scripts/10`, registry v1). Verified end-to-end on
real bn110721200 data.

**Parity with the frozen canon (the trust basis):**
- **Binning — bit-identical.** `scripts/parity_grb.py` feeds canon `scripts/27b`
  and the handbook the same synthetic significance profile → identical block edges
  (trim-edges + significance-merge). Run it as a regression guard.
- **Fitting inputs — verified.** The 2026-07-11 handbook audit confirmed all 6
  models' bounds/seeds/multistart match `scripts/10` line-by-line; energy bands were
  matched to canon (NaI 8.1–900 ∖ 33–40 K-edge; BGO 300–40000 — the handbook's
  `test_energy_ranges_match_canon` pins this).
- **Next**: a full numerical fit-output parity across the sample (canon `scripts/10`
  vs handbook), runnable as a per-burst fan-out.

## Phase B — NOT YET: the Stage-1 selection path stays FROZEN
The Stage-1 selection instrument (`scripts/39` gui + `scripts/00` picker /
BackgroundSelector / source marker) is the **benchmark's fixed tool** — routing it
through the handbook mid-campaign would change what the raters used and invalidate
the human-vs-AI comparison (the tool-freeze rule in `dev/BENCHMARK_PLAN.md`). It
migrates only **after** the 25-burst benchmark data collection is complete (or the
benchmark is explicitly re-based on a handbook commit and re-collected). The
handbook also still lacks the GUIs and Block-4 T_INT (task #11) that a full Stage-1
migration needs.

## What did NOT change
The frozen scripts (`00`, `10`, `27b`, `39`) are untouched — they remain the canon
(parity reference + the benchmark instrument). `pipeline_grb.py` is an **additional**
authoritative driver, not a rewrite. Provenance: pin the handbook commit used for
any authoritative run (the `tool_commit` stamp already carries it).

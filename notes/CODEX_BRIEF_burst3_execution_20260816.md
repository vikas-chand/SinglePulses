# EXECUTION BRIEF — burst #3 (bn081224887) end-to-end analysis

Run mode: GPT-5.6, Sol, Ultra. Working directory:
/Users/salim/Desktop/Projects/SingleRest/Two_Breaks (run everything from here).
THIS IS AN EXECUTION RUN, not an advisory review: you are the PRODUCER for
burst #3 of the single-pulse campaign. Claude-side agents will verify your
products afterward (producer/verifier separation with roles inverted vs the
earlier audits you performed on this repo). Write access: workspace-write.

## Hard rules
1. Touch ONLY burst bn081224887's products + your own logs/notes. Never modify
   other bursts' outputs, scripts/, dev/ai_guides/, or the catalogs beyond the
   documented merge steps below.
2. NO git commits, NO pushes, NO deliveries to the PI. Figures you produce are
   UNGATED until Claude's figure-verifier passes them.
3. Every rule in handoff_background_approval/KHUSHBOO_AGENTIC_PIPELINE_2026-08-16.md
   binds you — read it FIRST, fully. Also read dev/ai_guides/AgentArchitecture.md
   (P1–P8) and the STANDING PRODUCT CONTRACT + NO-MODEL-DROPPED sections of
   dev/ai_guides/FigureVisionQC.md.
4. Maintain a continuous progress log at notes/CODEX_BURST3_PROGRESS.md —
   append after EVERY completed step (so an interrupted session can resume).
   Final report: notes/CODEX_BURST3_RUN_20260816.md.
5. Open a fresh ledger results/sweep106/bn081224887/VISION_QC.md and record
   your own producer-side entries (what ran, seeds, anomalies) — verdicts will
   be appended by Claude verifiers later.
6. If a fit FAILs: retry that family once (transient multistart failures
   usually converge); if it still fails, record it and move on — never fake.
7. Cap parallelism at 12 cores (8 parallel fit jobs).

## Environment (every shell)
```bash
source /Users/salim/anaconda3/etc/profile.d/conda.sh
conda activate threeML
export FERMI_DIR=$CONDA_PREFIX/share/fermitools
export CALDB=$FERMI_DIR/data/caldb
export CALDBCONFIG=$CALDB/software/tools/caldb.config
export CALDBALIAS=$CALDB/software/tools/alias_config.fits
export CALDBROOT=$CALDB
export EXTFILESSYS=$FERMI_DIR/refdata/fermi
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd /Users/salim/Desktop/Projects/SingleRest/Two_Breaks
TRIG=bn081224887
```

## Phase 0 — boot (read, never derive)
- notes/REVIEW_INDEX_106.md row #3 (products dir, blocks, manifest).
- results/sweep106/$TRIG/ existing products; results/background_intervals.ecsv
  rows for $TRIG (approved selections — they are DECISIONS).
- notes/reconciliation/$TRIG.md if present.
- Record the burst configuration (detectors, z if any, block count) and sweep
  AgentArchitecture's register for open items matching it. Log to progress.

## Phase 1 — new-convention refit (all 4 families → ONE 24-model table)
```bash
SCR=$(mktemp -d)
ln -s $PWD/results/sweep106/$TRIG/blocks/bb_blocks_spectral_${TRIG}.ecsv $SCR/
python scripts/29_refit_clean.py --bkg-file results/background_intervals.ecsv \
  --blocks-dir $SCR --out-root results/convention_check --nproc 12
for fam in shape highe threecomp; do
  python scripts/10_spectral_fit_burst.py --trigger $TRIG --include-bgo --no-log \
    --blocks-file $SCR/bb_blocks_spectral_${TRIG}.ecsv \
    --bkg-file results/background_intervals.ecsv \
    --out-dir results/convention_check/$TRIG --models $fam
done
```
MANDATORY after: assert the table has 24 models (known order-fragility, NR-8):
`python3 -c "from astropy.table import Table; t=Table.read('results/convention_check/$TRIG/spectral_fits.ecsv'); n=len({c[:-4] for c in t.colnames if c.endswith('_AIC')}); print(n); assert n==24"`
If <24: refit the missing families into a scratch dir and column-merge (the
exact recipe is in results/sweep106/bn081222204/VISION_QC.md, NR-8 entry).
Then census winners per block (log the table). Retry any STATUS=FAIL cell once
per rule 6 and merge the fixed row (recipe also in that ledger).

## Phase 2 — temporal suite
```bash
python scripts/46_temporal_all106.py --only $TRIG --workers 1
python scripts/44_step_figures.py --trig $TRIG
python scripts/47_mvt_cwt_crosscheck.py --trig $TRIG
cd /Users/salim/Desktop/Projects/GRB_Handbook_Project && python -m grb_pipeline.pipeline.mvt_runner \
  --catalog /Users/salim/Desktop/Projects/SingleRest/Two_Breaks/results/background_intervals.ecsv \
  --data-root /Users/salim/Desktop/Projects/SingleRest/Two_Breaks/data \
  --output-root /Users/salim/Desktop/Projects/SingleRest/Two_Breaks/results/mvt_upstream/run_step7 \
  --mvt-python /Users/salim/anaconda3/envs/mvt/bin/python --workers 1 --triggers $TRIG
cd /Users/salim/Desktop/Projects/SingleRest/Two_Breaks
python scripts/47b_temporal_figs.py --trig $TRIG
python scripts/47c_lag_latbright.py --trig $TRIG
```
Record in progress: the engine row (T90/T50/MVT-Haar/lag/phi), the Bala
canonical value FROM result.json (mvt_s/delta_s — the ENGINE'S selection, never
a CSV row you prefer), the CWT value, the lag window-scan taus.

## Phase 3 — SED grid (24 × all bins) + no-model-dropped closure
Write your own sweep script (model list and loop pattern: copy from
results/sweep106/bn081222204/VISION_QC.md context or the Khushboo doc §3) to
dev/tmp_sweep_b3.sh: for every (model, bin) run
`python scripts/41c_paper_sed.py --trig $TRIG --bin <b> --model <M>
 --out results/convention_check/sed_grid_$TRIG --fit-root results/convention_check`
8 jobs at a time; OK/FAIL per pair to sweep_status.txt. THEN rerun the FAIL
list once — 41c's frozen-replay fallback recovers optimizer-drift and Class-B
crashes automatically. Log final tally (expect ~all pairs as panels; any
STRUCTURAL result is a real finding — investigate before proceeding).

## Phase 4 — products
```bash
python3 scripts/41e_sed_montage.py --trig $TRIG
python scripts/41d_param_evolution.py --trig $TRIG \
  --fit-root results/convention_check --out results/convention_check/param_evolution
```
Tables: generate per-bin all-model parameter tables into
results/convention_check/sed_grid_$TRIG/tables/ following EXACTLY the format of
results/convention_check/sed_grid_bn081222204/tables/ (winner rows marked,
EAC columns, dAIC). Verify montage sidecars: n_missing must equal the number
of pairs without panels (0 if the frozen rerun recovered everything).

## Phase 5 — producer report
Write notes/CODEX_BURST3_RUN_20260816.md:
- per-phase status + wall-clock;
- the winners census table + key parameters;
- temporal numbers WITH estimator labels + ledger caveats (Temporal.md defect
  ledger applies — read it before quoting; lag sign convention; T90 windowed
  vs catalog; MVT three-primitive labels);
- every anomaly, retry, or deviation from this brief (deviations must be
  DECLARED, never silent);
- science one-paragraph: how burst #3 sits vs the burst-1/2 contrast
  (alpha range vs line of death; thermal candidates with 3.92kT vs 8 keV edge
  check; tail phases) — provisional, N=3;
- what you could not complete and exactly where you stopped.
Finally: your own independent judgement — anything in this pipeline you
executed that you consider wrong or fragile, as producer rather than auditor.

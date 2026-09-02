# EXECUTION BRIEF — CAMPAIGN RUN (scaled to the full sample, 2026-08-16)

**SCOPE CHANGE (PI ruling): run the campaign over ALL bursts that have a block
table (85 of the 106; the other 21 lack `bb_blocks_spectral_*.ecsv` and are out
of scope until binned). Queue order still governs reporting.**

**REPORTS ARE STAGED — this matters.** Write the full per-burst REPORT + paper
for bursts #3–#22 ONLY (the 20 the PI will grade first). For bursts beyond #22:
produce the ANALYSIS PRODUCTS (merged 24-model table, temporal suite, SED grid,
montages, tables, evolution figures) and a SHORT per-burst summary in the
manifest — but do NOT write full papers yet. Reason: the PI reviews the first 20
and gives feedback on writing, figures, and results; his corrections then
propagate into the remaining papers instead of forcing 86 rewrites.

Run mode: GPT-5.6, Sol, Ultra. Working directory:
/Users/salim/Desktop/Projects/SingleRest/Two_Breaks — run everything from here.
You are the **PRODUCER** for bursts #3–#22 of the single-pulse campaign.
Claude-side verifier agents check your products afterwards (producer/verifier
separation, roles inverted vs your earlier audits of this repo). The PI reads
the per-burst reports like a teacher reading student reports — so every report
must stand on its own and never overstate.

## Read FIRST, in this order
1. `handoff_background_approval/KHUSHBOO_AGENTIC_PIPELINE_2026-08-16.md` — the
   runbook; every rule in it binds you.
2. `dev/ai_guides/AgentArchitecture.md` — P1–P8 and the register.
3. `dev/ai_guides/FigureVisionQC.md` — STANDING PRODUCT CONTRACT +
   NO-MODEL-DROPPED rule.
4. `dev/ai_guides/Temporal.md` — the defect ledger; it binds every temporal
   number you quote.
5. The two completed examples: `paper/GRB081125496/main.tex` and
   `paper/GRB081222/main.tex` (the latter is your structural template), plus
   `results/sweep106/bn081222204/VISION_QC.md` (recipes for the known traps).

## Hard rules
1. Touch only these bursts' products, your logs, your notes, and the new
   `paper/<GRBNAME>/` directories. Never modify `scripts/`, `dev/ai_guides/`,
   other bursts' outputs, or the approved catalogs.
2. NO git commits, NO pushes, NO delivery to the PI. Your figures are UNGATED
   until Claude's figure-verifier passes them — say so in every report.
3. Never fabricate. A missing/failed product is reported as missing, with the
   reason. Provisional-flag every number.
4. Deviations from this brief must be DECLARED in the progress log and the
   report — never silent.
5. Parallelism: **16 concurrent jobs** (PI ruling 2026-08-16: the machine is now
   free — use all 16 cores). Use `--nproc 16` wherever a script takes it, and a
   16-slot shell job pool in your own loops. Do NOT drop below this: earlier
   briefs said 8 then 12; both are superseded. Measured baseline for comparison:
   ONE engine family on ONE core took 4204 s — if you find yourself running one
   fit at a time, you are violating this rule.
6. **Known sandbox constraint + THE PARALLELISM RULE THAT FOLLOWS FROM IT.**
   Your sandbox blocks Python multiprocessing (`ProcessPoolExecutor` →
   `SC_SEM_NSEMS_MAX` PermissionError), so `scripts/29_refit_clean.py` dies AND
   `scripts/10`'s internal parallelism is unavailable: **each engine call runs
   on ONE core**. Measured consequence on burst #3: 4204 s for a single family,
   ~1 core of 16 busy. THEREFORE: get your parallelism at the SHELL level, never
   from Python. Build the full work list up front — every (burst, family) pair
   for P1, every (burst, bin, model) triple for P3 — and run **16 jobs
   concurrently** with shell background jobs (`&` + a 16-slot wait loop).
   Sequential per-burst execution is a brief violation.
   (The former example P1 pool was removed: you never fit — DESIGN v2.)
   Adoption of the pool's 24-model table is via
   `python3 dev/merge_campaign_families.py --trig <TRIG>` — never by hand.

## Bursts and their data (EVERY BAND RULE)
The table below is the first 20 (report-bearing). For every OTHER burst in the
85: the same rules apply — LLE is auto-added when `data/<trig>/gll_lle_*.fit*`
exists, and `--include-lat` is required whenever `data/<trig>/LAT/` exists
(11 bursts have LLE, 13 have LAT directories; check per burst, never assume).

The campaign rule is: **use every band that has data, gated on data quality —
never on detection significance.** Concretely for this batch:

| # | trigger | GBM dets (approved) | LLE | LAT | extra flags |
|---|---|---|---|---|---|
| 3 | bn081224887 | n6,n7,n9,b1 (+lle row) | YES | YES (EV+SC) | `--include-lat` |
| 4 | bn090530760 | n1,n2,n5,b0 | – | – | |
| 5 | bn090620400 | n6,n7,n8,nb,b1 | – | – | |
| 6 | bn090719063 | n7,n8,b1 | – | – | |
| 7 | bn090804940 | n3,n4,n5,b0 | – | – | |
| 8 | bn090809978 | n3,n4,n5,b0 | – | – | |
| 9 | bn090829672 | n6,n9,na,b1 | – | – | |
| 10 | bn091209001 | n4,b0 | – | – | |
| 11 | bn100122616 | n6,n9,na,b1 | – | – | |
| 12 | bn100130729 | n0,n3,n4,b0 | – | – | |
| 13 | bn100612726 | n3,n4,b0,n7,n8,b1 | – | – | |
| 14 | bn100614498 | n6,n7,n9,nb,b1 | – | – | |
| 15 | bn100707032 | n7,n8,b1 | – | – | |
| 16 | bn101126198 | n6,n7,n8,nb,b1 | – | – | |
| 17 | bn101225377 | n7,n8,nb,b1 | – | – | |
| 18 | bn110605183 | n2,n5,b0 | – | – | |
| 19 | bn110618366 | n2,b0 | – | – | |
| 20 | bn110721200 | n6,n7,n9,nb,b1 (+lle row) | YES | YES (EV+SC) | `--include-lat` |
| 21 | bn110920546 | n0,n1,n3,b0 | – | – | |
| 22 | bn110928180 | n0,n1,n3,n4,b0 | – | – | |

LLE is added AUTOMATICALLY by the engine whenever `data/<trig>/gll_lle_*.fit*`
exists (never pass `--skip-lle`); verify in the engine's stdout that it prints
`LLE data present — using APPROVED LLE bkg window` for #3 and #20 and that the
sidecar `fit_dets` contains `lle`. For LAT, pass `--include-lat` on EVERY
`scripts/10` call for #3 and #20; if the LAT plugin fails to build, record the
exact error and continue GBM(+LLE)-only for that burst — a declared, reported
degradation, never a silent one.

## DIVISION OF LABOUR (PI ruling 2026-08-16): CLAUDE FITS, YOU DO THE REST
The spectral REFITS (P1) are being run by a Claude-side 16-way pool because
your session gets terminated every ~20 minutes and in-flight fits are lost.
**Do not run P1 fits yourself** unless a family is still missing after the pool
finishes. Your job is everything else: merge the family tables, P2 temporal,
P3 SED grid, P4 products, P5 reports + papers, P6 bookkeeping — and the science.
CORE BUDGET while the Claude pool is running: keep your own concurrency to **4
jobs**; when the Claude pool's fitting is complete (the FITS-COMPLETE announcements
cover all 85, or no `10_spectral_fit_burst` processes remain), scale up to 16.

## AS-YOU-GO RULE (PI ruling, tonight): a burst is processed THE MOMENT its
three family tables exist in `results/campaign20_fam/` — never wait for the
whole pool. Merge with the provided tool (idempotent, asserts 24 models):
`python3 dev/merge_campaign_families.py --trig <TRIG>`
then run that burst's P2–P6 immediately. Sweep for newly-complete bursts
between tasks. NOTHING is skipped per burst: full temporal suite, grids per
the staging rule, montages, tables, evolution, ledger entries — and every
product remains UNGATED until the Claude verifier agents pass it.

## PRE-COMPUTED REFITS — check before fitting anything
DESIGN v2 (post operations-audit): the Claude pool runs ONE engine invocation
per burst — `--models highe`, which fits ALL 24 models in one process — into
`results/campaign20_fam/<TRIG>_highe/spectral_fits.ecsv`. When that file
exists, adopt it: `python3 dev/merge_campaign_families.py --trig <TRIG>`
(idempotent; copies the 24-model table into
results/convention_check/<TRIG>/ and asserts 24). Legacy per-family dirs
(_default/_shape) from v1 may also exist; the tool prefers the _highe table.
**YOU NEVER RUN P1 FITS — under any circumstances.** A missing or failed
burst is REPORTED in the manifest, never self-fitted: a single family costs
~70 min on one core and your session dies at ~20 min, so a self-run fit is
guaranteed lost work. This supersedes anything in the Khushboo runbook §1:
never run scripts/29_refit_clean.py, never fit threecomp, never fit at all.

## Resuming
A previous launch of this exact campaign was stopped ~10 minutes in (during
burst #3 P1) solely to correct the core count. Read
`notes/CODEX_CAMPAIGN20_MANIFEST.md` and `notes/CODEX_CAMPAIGN20_PROGRESS.md`
if they exist, reuse any complete, valid family output already on disk for
burst #3, and continue. Nothing else about that attempt was wrong.

## Per-burst sequence (repeat for each burst, in queue order)

```bash
source /Users/salim/anaconda3/etc/profile.d/conda.sh && conda activate threeML
export FERMI_DIR=$CONDA_PREFIX/share/fermitools CALDB=$FERMI_DIR/data/caldb
export CALDBCONFIG=$CALDB/software/tools/caldb.config
export CALDBALIAS=$CALDB/software/tools/alias_config.fits
export CALDBROOT=$CALDB EXTFILESSYS=$FERMI_DIR/refdata/fermi
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export MPLBACKEND=Agg        # MANDATORY: without it every engine call ends in a
                             # Tk/AppKit SIGABRT (exit 134) after saving
cd /Users/salim/Desktop/Projects/SingleRest/Two_Breaks
TRIG=<trigger>; EXTRA=""      # EXTRA="--include-lat" for #3 and #20
```

**P0 — boot.** Read `notes/REVIEW_INDEX_106.md` row, the burst's existing
`results/sweep106/$TRIG/` products, its `notes/reconciliation/$TRIG.md` if any,
and its approved rows in `results/background_intervals.ecsv`. Never re-derive
approved selections. Log the configuration (detectors, z if known, blocks).

**P1 — DO NOT FIT (see DESIGN v2 above). Adopt the pool's 24-model table:**
```bash
python scripts/10_spectral_fit_burst.py --trigger $TRIG --include-bgo --no-log \
  --blocks-file results/sweep106/$TRIG/blocks/bb_blocks_spectral_${TRIG}.ecsv \
  --bkg-file results/background_intervals.ecsv \
  --out-dir results/convention_check/$TRIG $EXTRA [--models $fam]
```
Then ASSERT 24 models (order-fragility NR-8):
```bash
python3 -c "from astropy.table import Table; t=Table.read('results/convention_check/$TRIG/spectral_fits.ecsv'); n=len({c[:-4] for c in t.colnames if c.endswith('_AIC')}); print(n); assert n==24"
```
If <24: refit the missing family into a scratch `--out-dir` and column-merge
into the main table (recipe: `results/sweep106/bn081222204/VISION_QC.md`, NR-8
entry). If any `<MODEL>_STATUS == FAIL`: retry that family once, merge the
fixed row; if it fails again, record it.

**P2 — temporal suite.**
```bash
python scripts/46_temporal_all106.py --only $TRIG --workers 1
python scripts/44_step_figures.py --trig $TRIG
python scripts/47_mvt_cwt_crosscheck.py --trig $TRIG
( cd /Users/salim/Desktop/Projects/GRB_Handbook_Project && \
  python -m grb_pipeline.pipeline.mvt_runner \
   --catalog $PWD/results/background_intervals.ecsv --data-root $PWD/data \
   --output-root $PWD/results/mvt_upstream/run_step7 \
   --mvt-python /Users/salim/anaconda3/envs/mvt/bin/python \
   --workers 1 --triggers $TRIG )
python scripts/47b_temporal_figs.py --trig $TRIG
python scripts/47c_lag_latbright.py --trig $TRIG
```
Quote MVT only with estimator labels (Bala windowed = CANONICAL, read
`mvt_s`/`delta_s` from `results/mvt_upstream/run_step7/$TRIG/result.json` — the
ENGINE's own selection, never a CSV row you prefer; CWT = global,
grid-quantized; Haar = in-chain, often an upper limit). The lag figure scans
fit windows and reports a window systematic — quote both.

**P3 — SED grid (STAGED, measured 2026-08-16: ~20,500 renders for 85 bursts =
11–20 h, so full grids everywhere do not fit in one night).**
- Bursts #3–#22 (the report-bearing 20): FULL 24-model grid + frozen-replay
  closure — the PI's no-model-dropped rule applies in full for every burst that
  gets a paper.
- Bursts beyond #22: render ONLY the AIC winner and any model within
  dAIC < 2 of it (the ties) per bin, plus the T_INT winner. Record in the
  manifest that the grid is PARTIAL-BY-DESIGN for those bursts, with the exact
  rule; full grids get filled in after the PI's review, when the report
  conventions are settled.

**P3 mechanics — no-model-dropped closure.** Loop all 24 models × all bins
(`tint` plus each `BLOCK >= 0`):
```bash
python scripts/41c_paper_sed.py --trig $TRIG --bin <b> --model <M> \
  --out results/convention_check/sed_grid_$TRIG --fit-root results/convention_check
```
16 jobs at a time, OK/FAIL per pair into `sweep_status.txt`. Then rerun the FAIL
list once — 41c's frozen-replay fallback recovers optimizer drift and
error-propagation crashes. A remaining STRUCTURAL failure is a real finding:
investigate and report it, do not paper over it.

**P4 — products.**
```bash
python3 scripts/41e_sed_montage.py --trig $TRIG
python scripts/41d_param_evolution.py --trig $TRIG \
  --fit-root results/convention_check --out results/convention_check/param_evolution
```
Per-bin all-model parameter tables into
`results/convention_check/sed_grid_$TRIG/tables/`, EXACTLY the format of
`results/convention_check/sed_grid_bn081222204/tables/`. Check every montage
sidecar's `n_missing` equals the number of pairs still without panels.

**P5 — per-burst report + paper.**
- Markdown report: `python scripts/48_burst_report.py --trig $TRIG` (if it
  errors, record the error and write the report by hand from the products).
- Paper: create `paper/GRB<NAME>/` (IAU-style name, e.g. GRB 081224 →
  `paper/GRB081224/`), copy `paper/GRB081222/refs.bib`, stage every figure into
  `figs/`, and write `main.tex` following `paper/GRB081222/main.tex` section
  for section: title = the GRB name only; author line exactly
  `Agentic AI Report by Vikas Chand, Khushboo Sharma, and Jagdish C. Joshi`
  with `\noaffiliation`; temporal BEFORE spectral; one section per pipeline
  step; the winners table; SED + montage + evolution figures; a provenance
  section; a numbered summary. Compile with
  `pdflatex → bibtex → pdflatex → pdflatex` and save a copy as
  `paper/GRB<NAME>/GRB<NAME>.pdf` (searchable filename).
- NEVER hand-write BibTeX. Only cite what is already in `refs.bib`; if a
  burst-specific reference is missing, omit the claim and note the omission.
- For #3 and #20, the paper MUST state the broadband coverage explicitly
  (GBM+LLE(+LAT)), the LLE/LAT energy ranges used, and what the extra bands
  changed (or did not change) in the fits.

**P6 — bookkeeping (after EVERY burst).**
- Append a per-burst block to `notes/CODEX_CAMPAIGN20_PROGRESS.md`: burst,
  phases completed, wall-clock, winners census, temporal numbers with labels,
  anomalies/retries/deviations, products written, what remains.
- Open/append `results/sweep106/$TRIG/VISION_QC.md` with your producer-side
  entries (what ran, seeds, anomalies). Verdict lines are appended later by
  Claude verifiers — leave them empty.
- Update `notes/CODEX_CAMPAIGN20_MANIFEST.md`: one row per burst with status
  (DONE / PARTIAL / FAILED) and the reason. This is what makes the campaign
  resumable — a relaunched session must read it and skip completed bursts.

## Final deliverable
`notes/CODEX_CAMPAIGN20_RUN_20260816.md`:
- the manifest table (20 rows, status + what exists);
- a cross-burst science section: α ranges vs the −2/3 line of death; thermal
  candidates with the 3.92·kT-vs-8 keV edge check and residual evidence;
  tail phases; T90/MVT/lag with labels; and for #3/#20 what LLE(+LAT) added —
  all provisional at N≤22;
- every deviation, failure, and unfinished item, explicitly;
- closing: your own independent judgement as PRODUCER (not auditor) — what in
  this pipeline is wrong, fragile, or slower than it should be.

Queue order governs REPORTING and the manifest; compute may be pooled across
bursts as above (that is the point of the 16-slot pool). Report each burst at
its boundary in queue order.

Work bursts strictly in queue order for reporting. If you run out of time or context, stop
cleanly at a burst boundary with the manifest current — a fresh session will
resume from it.

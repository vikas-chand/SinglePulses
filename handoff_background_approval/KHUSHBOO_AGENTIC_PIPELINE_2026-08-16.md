# Khushboo — the agentic pipeline as of 2026-08-16: what it does now, and how to run one burst

This replaces the earlier per-step notes for the *analysis* part of your
replication arm. It reflects the pipeline after bursts #1 (bn081125496) and #2
(bn081222204) were run end-to-end under the new agent architecture. Read this
top to bottom once before running anything.

## What this version IS (the 3-minute orientation)

The pipeline is now explicitly **agentic**: every product is made by a
*producer* (a script), checked by *guards* (code that fails loudly), and — when
run with an AI session — reviewed by *verifier agents* that never produced the
thing they check. Three documents are the law:

- `AGENTS.md` — the operating guide (start here always).
- `dev/ai_guides/AgentArchitecture.md` — who acts / checks / approves at every
  step, and the running register of agents we still need.
- `dev/ai_guides/FigureVisionQC.md` — the figure contracts. Two rules matter
  even when you run scripts by hand:
  1. **NO-EXCEPTION DELIVERY**: no figure is shown/used before someone who
     didn't make it has looked at it against the contract.
  2. **NO-MODEL-DROPPED** (PI ruling): every (model, bin) pair gets a panel —
     live-verified, or a stamped FROZEN REPLAY of the stored solution, or (only
     for true data mismatches) a labeled refusal that doubles as a bug report.

Every figure writes a **sidecar JSON** next to itself (inputs, seeds, numbers,
script hash). If you ever quote a number, quote it from the sidecar or the
engine table — never from a figure by eye.

## What changed since your last instructions (highlights)

- **Energy ranges** are now the published convention (Chand et al. 2020):
  NaI 8–900 keV with 30–40 keV K-edge excluded; BGO 0.2–38 MeV. The engine
  records the convention in each fit table's sidecar; displays refuse to mix
  conventions.
- **SED figures** (`scripts/41c`) are strict-XSPEC: every rebin group is a
  point (no invented arrows), `rebin 5 5` semantics, single model curve with
  points brought to the k=1 frame, native-3ML 68% band with validity guards
  (railed-draw and curve-containment suppression, reasons printed on-figure).
- **Live display fits are hard-guarded**: they must reproduce the stored
  engine solution to |ΔAIC| ≤ 0.1, else they fall back to a frozen replay.
- **Temporal quantities carry estimator labels** — MVT has three estimators
  (Bala windowed = canonical; CWT global — grid-quantized, its ±err is grid
  spacing; Haar — often only an upper limit and must be labeled so). The lag
  uses the validated LATBright s02c engine with pulse-scaled windows;
  positive lag = soft lags hard (Norris). T90 is windowed — check
  TAIL_OUTSIDE_WINDOW_SIG before calling it a full duration.
- **The two big pitfalls we hit so you don't**: (1) scripts/10's per-family
  save is order-fragile — always run the four families as below and CHECK the
  model count is 24 afterward; (2) figure/name mismatches (DSBPLfree vs
  DSBPLF etc.) are handled by an alias map — if you add a model, add its
  alias in `scripts/41e`.

## How to run ONE burst end-to-end (copy-paste sequence)

Environment (every terminal):
```bash
conda activate threeML
export FERMI_DIR=$CONDA_PREFIX/share/fermitools
export CALDB=$FERMI_DIR/data/caldb
export CALDBCONFIG=$CALDB/software/tools/caldb.config
export CALDBALIAS=$CALDB/software/tools/alias_config.fits
export CALDBROOT=$CALDB
export EXTFILESSYS=$FERMI_DIR/refdata/fermi
cd ~/Desktop/Projects/SingleRest/Two_Breaks     # ALWAYS run from repo root
TRIG=bn081222204                                 # your burst
```

**0. Boot (read, don't derive).** Open `notes/REVIEW_INDEX_106.md` (your burst's
row + products dir), the burst's `REPORT_*.md`/`PRODUCTS.md` if present, and
`notes/reconciliation/<trig>.md` if present. The approved Stage-1 selections
live in `results/background_intervals.ecsv` — they are decisions, never
re-derive them.

**1. New-convention refit (all 4 model families → one 24-model table):**
```bash
SCR=$(mktemp -d); ln -s $PWD/results/sweep106/$TRIG/blocks/bb_blocks_spectral_${TRIG}.ecsv $SCR/
python scripts/29_refit_clean.py --bkg-file results/background_intervals.ecsv \
  --blocks-dir $SCR --out-root results/convention_check --nproc 12
for fam in shape highe threecomp; do
  python scripts/10_spectral_fit_burst.py --trigger $TRIG --include-bgo --no-log \
    --blocks-file $SCR/bb_blocks_spectral_${TRIG}.ecsv \
    --bkg-file results/background_intervals.ecsv \
    --out-dir results/convention_check/$TRIG --models $fam
done
# MANDATORY check (the order-fragility pitfall):
python3 -c "from astropy.table import Table; t=Table.read('results/convention_check/$TRIG/spectral_fits.ecsv'); \
n=len({c[:-4] for c in t.colnames if c.endswith('_AIC')}); print(n,'models'); assert n==24"
```
If the assert fails: rerun the missing family into a scratch dir and
column-merge (ask, or see burst-2's ledger for the exact recipe). If any
STATUS=FAIL cell remains: **retry that family once** (fits are multistart;
transient failures usually converge on retry), then merge the fixed row.

**2. Temporal suite:**
```bash
python scripts/46_temporal_all106.py --only $TRIG --workers 1     # engine row
python scripts/44_step_figures.py --trig $TRIG                    # step figures
python scripts/47_mvt_cwt_crosscheck.py --trig $TRIG              # CWT MVT
cd ~/Desktop/Projects/GRB_Handbook_Project && python -m grb_pipeline.pipeline.mvt_runner \
  --catalog ~/Desktop/Projects/SingleRest/Two_Breaks/results/background_intervals.ecsv \
  --data-root ~/Desktop/Projects/SingleRest/Two_Breaks/data \
  --output-root ~/Desktop/Projects/SingleRest/Two_Breaks/results/mvt_upstream/run_step7 \
  --mvt-python ~/anaconda3/envs/mvt/bin/python --workers 1 --triggers $TRIG
cd ~/Desktop/Projects/SingleRest/Two_Breaks
python scripts/47b_temporal_figs.py --trig $TRIG                  # pulse/lag/MVT figures
python scripts/47c_lag_latbright.py --trig $TRIG                  # validated-lag figure
```

**3. SED grid (24 models × all bins, seeded + guarded):** use the sweep
pattern in `<scratchpad>/sed_sweep_b2.sh` as your template — it loops
`scripts/41c_paper_sed.py --trig $TRIG --bin <b> --model <M> --out
results/convention_check/sed_grid_$TRIG --fit-root results/convention_check`
over every pair, 8 jobs at a time, and logs OK/FAIL per pair. Then rerun the
FAIL list once — the frozen-replay fallback recovers them (three-tier rule).

**4. Products:**
```bash
python3 scripts/41e_sed_montage.py --trig $TRIG      # per-bin montages (winner framed)
python scripts/41d_param_evolution.py --trig $TRIG \
  --fit-root results/convention_check --out results/convention_check/param_evolution
```
Tables: per-bin all-model parameter tables generate from the fit table (see
`results/convention_check/sed_grid_bn081222204/tables/` for the format).

**5. Checks you must do before believing anything:**
- montage sidecars: `n_missing` must be 0 (every model visible);
- every +BB "detection": compute 3.92·kT — if below the 8 keV fitted edge it
  is an EDGE ARTIFACT, not a photosphere (L28);
- ΔAIC < 2 is a TIE — report ties as ties;
- quote MVT/lag only with estimator labels and ledger caveats
  (`dev/ai_guides/Temporal.md` — read its defect ledger first, always).

**6. Ledger.** Every burst has `results/sweep106/<trig>/VISION_QC.md` — every
figure look, every defect, every fix goes there with the date. If YOU catch a
defect the pipeline missed, that is (by standing rule) a missing agent — write
it in the ledger AND tell Vikas/the session so it lands in the architecture
register.

## Products map (where everything lands)

```
results/convention_check/<trig>/spectral_fits.ecsv      # THE 24-model table
results/convention_check/sed_grid_<trig>/               # per-pair SEDs + sidecars + logs
results/convention_check/sed_grid_<trig>/montage/       # per-bin montages
results/convention_check/sed_grid_<trig>/tables/        # all-model parameter tables
results/convention_check/sed_grid_<trig>/notes/         # AI reviewer notes (if run)
results/convention_check/param_evolution/               # winner-model evolution figures
results/sweep106/<trig>/                                # step figures + temporal + VISION_QC.md
results/mvt_upstream/run_step7/<trig>/                  # canonical MVT (Bala) products
paper/<GRBNAME>/                                        # the per-burst ApJ draft (burst 1 example)
```

Questions → the ledgers first, then Vikas. Do not "fix" a defect quietly:
note it, fix it, and record both. That's the whole method.

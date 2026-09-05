#!/bin/zsh
# THE SINGLE ENTRY POINT — one burst, end to end, fail-closed.
#
# PI, 2026-08-17: "consolidate and complete the agentic pipeline … a customized
# agentic system that runs as we run the whole pipeline."
#
# Everything the campaign learned, in the order it must happen. Each stage is
# idempotent and skippable-on-resume; the run STOPS if an invariant fails, so a
# defective burst can never reach a paper.
#
#   usage: dev/run_burst_agentic.sh <trigger> [--from <stage>] [--no-fit]
#   stages: fit -> merge -> products -> tables -> invariants -> handoff
#
# What this script does NOT do, deliberately: write the paper, or pass the
# figure/number gates. Those are AGENT steps — a fresh context must do them
# (producer never verifies own work). The script ends by printing the exact
# agent tasks that remain, so the human or the orchestrator can dispatch them.
set -u
TRIG=${1:?usage: run_burst_agentic.sh <trigger>}
shift 2>/dev/null || true
FROM="fit"; DOFIT=1
while [ $# -gt 0 ]; do
  case "$1" in
    --from) FROM=$2; shift 2;;
    --no-fit) DOFIT=0; shift;;
    *) shift;;
  esac
done

source /Users/salim/anaconda3/etc/profile.d/conda.sh
conda activate threeML
export FERMI_DIR=$CONDA_PREFIX/share/fermitools CALDB=$FERMI_DIR/data/caldb
export CALDBCONFIG=$CALDB/software/tools/caldb.config
export CALDBALIAS=$CALDB/software/tools/alias_config.fits
export CALDBROOT=$CALDB EXTFILESSYS=$FERMI_DIR/refdata/fermi
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PATH="/Users/salim/anaconda3/bin:/opt/homebrew/bin:$PATH"  # pandoc+xelatex for the report PDF
# NR-12/NR-20: single-burst runner still admits its fit + MVT to the arbiter
source "$(dirname $0)/ram_slots.sh" 2>/dev/null || source dev/ram_slots.sh
export MPLBACKEND=Agg TQDM_DISABLE=1
cd /Users/salim/Desktop/Projects/SingleRest/Two_Breaks
mkdir -p logs/agentic
LOG=logs/agentic/${TRIG}.log
say() { echo "[$(date -u +%H:%M:%SZ)] $*" | tee -a $LOG; }

say "=== agentic pipeline: $TRIG (from=$FROM)"

# ---------------------------------------------------------------- 1. FIT ----
# 24 models in ONE invocation (--models highe is a cumulative superset; the
# multi-family pool was 58% redundant and caused a LAT cache race).
BLK=results/sweep106/$TRIG/blocks/bb_blocks_spectral_${TRIG}.ecsv
if [ ! -f "$BLK" ]; then
  say "STOP: no block table ($BLK). Run scripts/27b_reblock_3ml.py first."
  exit 2
fi
OUT=results/campaign20_fam/${TRIG}_highe
if [ "$DOFIT" -eq 1 ] && [ ! -f "$OUT/spectral_fits.ecsv" ]; then
  EXTRA=""; [ -d "data/$TRIG/LAT" ] && EXTRA="--include-lat"   # every-band rule
  say "fit: 24 models $EXTRA (LLE auto-included when present)"
  mkdir -p $OUT
  ram_admit ${TB_FIT_SLOT_GB:-3} || { say "RAM ABORT — paging"; exit 1; }
  python scripts/10_spectral_fit_burst.py --trigger $TRIG --include-bgo --no-log \
    --blocks-file $BLK --bkg-file results/background_intervals.ecsv \
    --out-dir $OUT $EXTRA --models highe 2>&1 | python3 dev/logfilter.py \
    > logs/campaign20/${TRIG}_highe.log || { say "STOP: fit failed"; exit 3; }
fi
[ -f "$OUT/spectral_fits.ecsv" ] || { say "STOP: no fit table"; exit 3; }

# -------------------------------------------------------------- 2. MERGE ----
say "merge: adopt into canonical table (best minimum per bin+model)"
python3 dev/merge_campaign_families.py --trig $TRIG >> $LOG 2>&1 \
  || { say "STOP: merge failed"; exit 4; }

# ----------------------------------------------------------- 3. PRODUCTS ----
if [ ! -f "results/campaign20_products_done/$TRIG" ]; then
  say "products: temporal suite + SED grid + montages + evolution (may take ~1h)"
  ./dev/campaign_products_driver.sh $TRIG >> $LOG 2>&1
fi

# ------------------------------------------------------------- 4. TABLES ----
say "tables: per-bin all-model parameter tables"
python3 dev/gen_param_tables.py --trig $TRIG >> $LOG 2>&1

# --------------------------------------------------------- 5. INVARIANTS ----
# Fail-closed: every check here exists because something actually broke.
say "invariants: mechanical checks (I1-I10)"
python3 dev/verify_burst_invariants.py --trig $TRIG 2>&1 | tee -a $LOG
if [ ${pipestatus[1]} -ne 0 ]; then
  say "STOP: invariants FAILED — fix before any paper is written."
  exit 5
fi

# ------------------------------------------------------- 6. REPRODUCTION ----
say "reproduction record: script hashes + argv + bounds + inputs"
python3 dev/make_repro_record.py --trig $TRIG >> $LOG 2>&1

# ----------------------------------------------------------- 7. HANDOFF ----
cat <<EOF | tee -a $LOG

=== $TRIG: mechanical stages COMPLETE. Remaining work is AGENT work.

Dispatch these, each in a FRESH context (producer never verifies own work):

  1. REPORT WRITER  — write paper/GRB<name>/main.tex from the products only:
       results/convention_check/$TRIG/spectral_fits.ecsv   (all numbers)
       results/convention_check/sed_grid_$TRIG/tables/     (per-bin tables)
       results/sweep106/$TRIG/*_step7_*.json               (temporal + labels)
       results/mvt_upstream/run_step7/$TRIG/result.json    (canonical MVT)
     Template + conventions: paper/GRB090809/main.tex (latest accepted form).

  2. NUMBERS VERIFIER — recompute EVERY quantitative claim from the products;
     report PASS / PASS-WITH-CORRECTIONS / FAIL with the recomputed value.

  3. FIGURE VERIFIER — read every staged PNG against
     dev/ai_guides/FigureVisionQC.md; check stamped AIC vs the table.

  4. DISTILLER — append the round to results/sweep106/$TRIG/VISION_QC.md:
     what was found, what was fixed, what remains; and route any new rule to
     the layer that can enforce it (dev/ai_guides/PI_REVIEW_PROTOCOL.md).

  5. NOTEBOOK — python notebooks/run_grb.py $TRIG --depth full --execute
     (ships with the report; contains no LLM calls by design).

EOF
say "=== done"

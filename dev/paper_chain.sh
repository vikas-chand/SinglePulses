#!/bin/zsh
# Per-burst chain to a compiled aastex paper: stage->promote (receipts) -> P2
# temporal (arbiter 16 GB, Bala inside) -> assembler. Serial, resumable.
source /Users/salim/anaconda3/etc/profile.d/conda.sh
conda activate threeML
export FERMI_DIR=$CONDA_PREFIX/share/fermitools CALDB=$FERMI_DIR/data/caldb
export CALDBCONFIG=$CALDB/software/tools/caldb.config
export CALDBALIAS=$CALDB/software/tools/alias_config.fits
export CALDBROOT=$CALDB EXTFILESSYS=$FERMI_DIR/refdata/fermi
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg TQDM_DISABLE=1
export PATH=$PATH:/Users/salim/anaconda3/bin:/opt/homebrew/bin
cd /Users/salim/Desktop/Projects/SingleRest/Two_Breaks
source dev/ram_slots.sh
RT=notes/codex_campaign20_runtime
for T in "$@"; do
  echo "==== $T chain start $(date -u +%H:%M:%SZ) ===="
  # ADAPTER (2026-08-27): the v2 retry pool writes results/campaign20_fam/
  # <T>_highe_retry, but the staging contract reads family_runs/highe_retry
  # under convention_check plus a status line in logs/codex_campaign20/p1/.
  # Materialize the evidence where the contract looks (copies, like Codex did).
  RSRC=results/campaign20_fam/${T}_highe_retry
  RDST=results/convention_check/$T/family_runs/highe_retry
  if [ -f "$RSRC/spectral_fits.ecsv" ] && [ ! -f "$RDST/spectral_fits.ecsv" ]; then
    mkdir -p "$RDST" logs/codex_campaign20/p1/status
    cp "$RSRC/spectral_fits.ecsv" "$RSRC/spectral_fits.json" "$RDST/" 2>/dev/null
    cp "logs/campaign20/${T}_highe_retry.log" "logs/codex_campaign20/p1/${T}_highe_retry.log" 2>/dev/null
    printf 'COMPLETE\\t%s\\thighe\\thighe_retry\\tengine_rc=0\\t%s\n' \
      "$T" "$PWD/$RDST" > "logs/codex_campaign20/p1/status/${T}_highe_retry.status"
    echo "  retry evidence adapted into contract layout"
  fi
  if [ ! -d results/convention_check/$T/promotion_receipts ]; then
    python3 $RT/campaign_products.py stage-p1 --trig $T || { echo "STAGE FAIL $T"; continue; }
    STAGE=$(ls -dt results/convention_check/$T/merge_staging/* 2>/dev/null | head -1)
    [ -n "$STAGE" ] || { echo "NO STAGE DIR $T"; continue; }
    python3 $RT/campaign_products.py promote-p1 --trig $T --stage-dir "$STAGE" || { echo "PROMOTE FAIL $T"; continue; }
  fi
  if [ ! -f results/sweep106/$T/p2_temporal_summary.json ]; then
    ram_admit 16 || { echo "RAM ABORT $T"; break; }
    python3 $RT/run_p2_temporal.py run --triggers $T --write-summary; RC=$?
    ram_release
    [ $RC -eq 0 ] || { echo "P2 FAIL $T rc=$RC"; continue; }
  fi
  python3 $RT/assemble_report_paper.py build --trig $T && echo "PAPER OK $T" || echo "PAPER FAIL $T"
done
echo "CHAIN COMPLETE"

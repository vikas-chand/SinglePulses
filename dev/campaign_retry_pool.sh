#!/bin/zsh
# Mandated highe_retry fits (no-model-dropped contract): one full-family rerun
# per burst with FAIL cells and no retry evidence. Arbiter-paced (NR-12).
source /Users/salim/anaconda3/etc/profile.d/conda.sh
conda activate threeML
export FERMI_DIR=$CONDA_PREFIX/share/fermitools CALDB=$FERMI_DIR/data/caldb
export CALDBCONFIG=$CALDB/software/tools/caldb.config
export CALDBALIAS=$CALDB/software/tools/alias_config.fits
export CALDBROOT=$CALDB EXTFILESSYS=$FERMI_DIR/refdata/fermi
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg TQDM_DISABLE=1
cd /Users/salim/Desktop/Projects/SingleRest/Two_Breaks
source dev/ram_slots.sh
: ${TB_FIT_SLOT_GB:=3}
PIDFILE=/tmp/two_breaks_retry_pool.pid
if [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then
  echo "retry pool already running"; exit 0
fi
echo $$ > $PIDFILE; trap 'rm -f $PIDFILE' EXIT INT TERM
mkdir -p logs/campaign20
for TRIG in "$@"; do
  OUT=results/campaign20_fam/${TRIG}_highe_retry
  [ -f "$OUT/spectral_fits.ecsv" ] && continue
  mkdir -p $OUT
  ram_admit $TB_FIT_SLOT_GB || { echo "RAM ABORT"; break; }
  MY=(${TB_MY_SLOTS[@]})
  EXTRA=""; [ -d "data/$TRIG/LAT" ] && EXTRA="--include-lat"
  ( trap 'for t in ${MY[@]}; do rm -f $t/pid 2>/dev/null; rmdir $t 2>/dev/null; done' EXIT
    python scripts/10_spectral_fit_burst.py --trigger $TRIG --include-bgo --no-log \
      --blocks-file results/sweep106/$TRIG/blocks/bb_blocks_spectral_${TRIG}.ecsv \
      --bkg-file results/background_intervals.ecsv \
      --out-dir $OUT $EXTRA --models highe 2>&1 | python3 dev/logfilter.py > logs/campaign20/${TRIG}_highe_retry.log \
    && echo "OK $TRIG highe_retry" >> logs/campaign20/status.txt \
    || echo "FAIL $TRIG highe_retry" >> logs/campaign20/status.txt ) &
done
wait
echo "RETRY POOL COMPLETE"

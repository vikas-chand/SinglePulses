#!/bin/zsh
# Campaign refits v2 (post NR-11 audit): ONE invocation per burst.
# --models highe fits ALL 24 models in one process (verified: ACTIVE_SPECS is
# cumulative, scripts/10 lines 1556-1566) -> no merge, no NR-8 exposure, no
# concurrent-family LAT cache race, 24 fits/bin instead of 38.
source /Users/salim/anaconda3/etc/profile.d/conda.sh
conda activate threeML
export FERMI_DIR=$CONDA_PREFIX/share/fermitools CALDB=$FERMI_DIR/data/caldb
export CALDBCONFIG=$CALDB/software/tools/caldb.config
export CALDBALIAS=$CALDB/software/tools/alias_config.fits
export CALDBROOT=$CALDB EXTFILESSYS=$FERMI_DIR/refdata/fermi
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg
# tqdm \r-frame spam made single engine logs 200 MB (2.9 GB total by burst 8)
export TQDM_DISABLE=1
cd /Users/salim/Desktop/Projects/SingleRest/Two_Breaks
mkdir -p logs/campaign20 results/campaign20_fam
# RAM ARBITER (PI 2026-08-17): budget in GB, not cores. A fit process
# measured 0.87 GB flat on a 4-block LAT burst; 3 GB/slot is the
# headroom-inclusive claim for big-block bursts.
source dev/ram_slots.sh
: ${TB_FIT_SLOT_GB:=3}

# SELF-GUARD (2026-08-17): duplicate pools once drove the machine into swap.
# `pgrep -f` cannot distinguish this script from its own backgrounded
# subshells (they inherit the parent cmdline), so external duplicate-detection
# is unreliable — the guard belongs HERE.
PIDFILE=/tmp/two_breaks_refit_pool.pid
if [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then
  echo "pool already running (pid $(cat $PIDFILE)) — refusing to start a second"
  exit 0
fi
echo $$ > $PIDFILE
trap 'rm -f $PIDFILE' EXIT INT TERM
for TRIG in $(python3 -c "
from astropy.table import Table
import os
t = Table.read('results/background_intervals.ecsv')
for b in sorted({str(x).strip() for x in t['TRIGGER_NAME']}):
    if os.path.exists(f'results/sweep106/{b}/blocks/bb_blocks_spectral_{b}.ecsv'):
        print(b)"); do
  OUT=results/campaign20_fam/${TRIG}_highe
  [ -f "$OUT/spectral_fits.ecsv" ] && continue                       # done
  ps -A -o command | grep -q "[1]0_spectral_fit_burst.py --trigger $TRIG " && continue  # in flight
  EXTRA=""; [ -d "data/$TRIG/LAT" ] && EXTRA="--include-lat"
  mkdir -p $OUT
  ram_admit $TB_FIT_SLOT_GB || { echo 'RAM ABORT — machine is paging'; break; }
  MY=(${TB_MY_SLOTS[@]})
  ( trap 'for t in ${MY[@]}; do rm -f $t/pid 2>/dev/null; rmdir $t 2>/dev/null; done' EXIT
    python scripts/10_spectral_fit_burst.py --trigger $TRIG --include-bgo --no-log \
      --blocks-file results/sweep106/$TRIG/blocks/bb_blocks_spectral_${TRIG}.ecsv \
      --bkg-file results/background_intervals.ecsv \
      --out-dir $OUT $EXTRA --models highe 2>&1 | python3 dev/logfilter.py > logs/campaign20/${TRIG}_highe.log \
    && echo "OK $TRIG highe" >> logs/campaign20/status.txt \
    || echo "FAIL $TRIG highe" >> logs/campaign20/status.txt ) &
done
wait
echo "REFITS v2 PASS COMPLETE"

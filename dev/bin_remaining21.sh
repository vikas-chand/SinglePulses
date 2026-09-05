#!/bin/zsh
# Bin the 21 bursts that never got a Bayesian-block table, so the campaign can
# reach all 106 (PI 2026-08-17: "you can run all the fits of 106").
# Writes into each burst's own blocks/ dir in the canonical layout.
source /Users/salim/anaconda3/etc/profile.d/conda.sh
conda activate threeML
export FERMI_DIR=$CONDA_PREFIX/share/fermitools CALDB=$FERMI_DIR/data/caldb
export CALDBCONFIG=$CALDB/software/tools/caldb.config
export CALDBALIAS=$CALDB/software/tools/alias_config.fits
export CALDBROOT=$CALDB EXTFILESSYS=$FERMI_DIR/refdata/fermi
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg
cd /Users/salim/Desktop/Projects/SingleRest/Two_Breaks
mkdir -p logs/bin21
# NR-12/NR-20: 3ML binning is heavy — go through the machine-wide RAM arbiter
source dev/ram_slots.sh
: ${TB_BIN_SLOT_GB:=3}
i=0
while read -r T; do
  [ -z "$T" ] && continue
  DEST=results/sweep106/$T/blocks
  [ -f "$DEST/bb_blocks_spectral_${T}.ecsv" ] && continue
  mkdir -p $DEST logs/bin21
  ram_admit $TB_BIN_SLOT_GB || { echo "RAM ABORT — paging"; break; }
  MY=(${TB_MY_SLOTS[@]})
  ( trap 'for t in ${MY[@]}; do rm -f $t/pid 2>/dev/null; rmdir $t 2>/dev/null; done' EXIT
    SCR=$(mktemp -d)
    python scripts/27b_reblock_3ml.py --burst $T --out $SCR \
      > logs/bin21/${T}.log 2>&1
    f=$(ls $SCR/bb_blocks_spectral_${T}.ecsv 2>/dev/null || ls $SCR/*${T}*.ecsv 2>/dev/null | head -1)
    if [ -n "$f" ]; then cp "$f" "$DEST/bb_blocks_spectral_${T}.ecsv"; echo "OK $T" >> logs/bin21/status.txt
    else echo "FAIL $T" >> logs/bin21/status.txt; fi
    rm -rf $SCR ) &
  i=$((i+1))   # arbiter paces admission; no manual job cap needed
done < /tmp/unbinned.txt
wait
echo "BIN21 DONE: $(grep -c '^OK' logs/bin21/status.txt 2>/dev/null) ok, $(grep -c '^FAIL' logs/bin21/status.txt 2>/dev/null) failed"

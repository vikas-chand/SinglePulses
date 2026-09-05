#!/bin/zsh
# Execute the pipeline notebook for bursts that have a report but no notebook.
# Paced by the machine-wide RAM arbiter (PI 2026-08-17: GB, not cores).
source /Users/salim/anaconda3/etc/profile.d/conda.sh
conda activate threeML
export FERMI_DIR=$CONDA_PREFIX/share/fermitools CALDB=$FERMI_DIR/data/caldb
export CALDBCONFIG=$CALDB/software/tools/caldb.config
export CALDBALIAS=$CALDB/software/tools/alias_config.fits
export CALDBROOT=$CALDB EXTFILESSYS=$FERMI_DIR/refdata/fermi
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg TQDM_DISABLE=1
cd /Users/salim/Desktop/Projects/SingleRest/Two_Breaks
source dev/ram_slots.sh
: ${TB_NB_SLOT_GB:=5}
mkdir -p notebooks/outputs logs/nb
PY=/Users/salim/anaconda3/envs/threeML/bin/python
NB=notebooks/Two_Breaks_single_GRB_pipeline.ipynb
for B in "$@"; do
  [ -f notebooks/outputs/$B.ipynb ] && { echo "skip $B (exists)"; continue; }
  ram_admit $TB_NB_SLOT_GB || { echo "RAM ABORT before $B"; exit 1; }
  MY=(${TB_MY_SLOTS[@]})
  ( trap 'for t in ${MY[@]}; do rm -f $t/pid 2>/dev/null; rmdir $t 2>/dev/null; done' EXIT
    echo "########## $B ##########"
    GRB=$B DEPTH=full $PY -m jupyter nbconvert --to notebook --execute --allow-errors \
      --ExecutePreprocessor.timeout=1800 \
      --output outputs/$B.ipynb "$NB" > logs/nb/$B.log 2>&1 \
      && echo "OK $B" || echo "FAIL $B" ) &
done
wait
echo "NOTEBOOKS PASS COMPLETE"

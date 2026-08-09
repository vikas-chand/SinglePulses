#!/bin/zsh
set -e
source /tmp/heavy_env.sh
export MPLBACKEND=Agg
cd /Users/salim/Desktop/Projects/SingleRest/Two_Breaks
echo "########## STAGE 2 (refit) resume: 6-model + BGO, 12 cores ##########"
python scripts/29_refit_clean.py \
  --bkg-file results/background_intervals_human_clean.ecsv \
  --blocks-dir results/clean_blocks_human_final \
  --out-root results/clean_per_burst_human_final \
  --nproc 12 --models default
echo "########## RE-ANALYSIS COMPLETE ##########"
echo "fits: $(ls results/clean_per_burst_human_final/*/spectral_fits*.ecsv 2>/dev/null | wc -l) bursts"

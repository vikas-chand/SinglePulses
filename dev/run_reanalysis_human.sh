#!/bin/zsh
# Full re-analysis on the human-reviewed intervals (89 clean bursts).
# Excludes bn210812699 (no NaI < 60 deg) + the 16 pending Khushboo re-review.
# Fine GBM re-block (3ML Bayesian blocks, use_background=True + significance)
# -> 6-model AIC re-fit (NaI+BGO). Fresh out-roots (provenance-separated).
set -e
source /tmp/heavy_env.sh
export MPLBACKEND=Agg
cd /Users/salim/Desktop/Projects/SingleRest/Two_Breaks

CAT=results/background_intervals_human_clean.ecsv
BLK=results/clean_blocks_human_final
OUT=results/clean_per_burst_human_final

echo "########## STAGE 1: re-block (27b) 89 bursts -> $BLK ##########"
python scripts/27b_reblock_3ml.py --bkg $CAT --out $BLK
echo "########## re-block done: $(ls $BLK/bb_blocks_spectral_*.ecsv 2>/dev/null | wc -l) block files ##########"

echo "########## STAGE 2: re-fit (29 -> 10) 6-model + BGO, 12 cores -> $OUT ##########"
python scripts/29_refit_clean.py \
  --bkg-file $CAT --blocks-dir $BLK --out-root $OUT \
  --nproc 12 --models default --include-bgo

echo "########## RE-ANALYSIS COMPLETE ##########"
echo "fits: $(ls $OUT/*/spectral_fits*.ecsv 2>/dev/null | wc -l) bursts"

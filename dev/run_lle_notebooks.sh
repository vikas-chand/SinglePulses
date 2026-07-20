#!/bin/zsh
source /tmp/heavy_env.sh
export MPLBACKEND=Agg
cd /Users/salim/Desktop/Projects/SingleRest/Two_Breaks
mkdir -p notebooks/outputs
PY=/Users/salim/anaconda3/envs/threeML/bin/python
NB=notebooks/Two_Breaks_single_GRB_pipeline.ipynb
for B in bn110721200 bn130427324 bn150902733 bn160625945 bn130310840 bn151006413 bn180703876 bn201104001; do
  echo "########## executing $B (full depth) ##########"
  GRB=$B DEPTH=full $PY -m jupyter nbconvert --to notebook --execute --allow-errors \
    --ExecutePreprocessor.timeout=1500 \
    --output outputs/$B.ipynb "$NB" 2>&1 | tail -2
done
echo "########## LLE NOTEBOOKS DONE ##########"
ls -la notebooks/outputs/*.ipynb 2>/dev/null | wc -l

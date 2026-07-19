#!/bin/zsh
# Stage-1 HUMAN GUI review environment (INTERACTIVE — not headless).
# Sets the threeML env + CALDB (needed for the in-GUI 3ML background refit
# overlay) but leaves matplotlib on the native macOS GUI backend so the
# window actually appears. Source this, then run scripts/39 gui.
source /Users/salim/anaconda3/bin/activate threeML
export CALDB=$FERMI_DIR/data/caldb
export CALDBCONFIG=$CALDB/software/tools/caldb.config
export CALDBALIAS=$CALDB/software/tools/alias_config.fits
export CALDBROOT=$CALDB
unset MPLBACKEND        # let matplotlib pick the interactive macOS backend
cd /Users/salim/Desktop/Projects/SingleRest/Two_Breaks

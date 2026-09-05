#!/bin/zsh
# Campaign-owned P3 launcher. The authoritative --campaign path builds one
# cross-trigger worklist before launching anything, then uses a shared 16-token
# FIFO pool for attempt 1 and one shared retry list for attempt 2.

REPO=/Users/salim/Desktop/Projects/SingleRest/Two_Breaks
RUNTIME=$REPO/notes/codex_campaign20_runtime
HELPER=$RUNTIME/run_sed_sweep.py
PYTHON=/Users/salim/anaconda3/envs/threeML/bin/python
POOL_SIZE=16
CAMPAIGN_TRIGGERS=(
  bn081224887 bn090530760 bn090620400 bn090719063 bn090804940
  bn090809978 bn090829672 bn091209001 bn100122616 bn100130729
  bn100612726 bn100614498 bn100707032 bn101126198 bn101225377
  bn110605183 bn110618366 bn110721200 bn110920546 bn110928180
)

if (( $# == 0 )); then
  print -u 2 -- "usage: zsh run_sed_sweep.zsh --campaign | --triggers-file FILE | TRIGGER [TRIGGER ...]"
  exit 2
fi
if [[ $1 == --campaign ]]; then
  TRIGGERS=(${CAMPAIGN_TRIGGERS[@]})
  RUN_LABEL=campaign20
elif [[ $1 == --triggers-file ]]; then
  (( $# == 2 )) || { print -u 2 -- "--triggers-file requires exactly one file"; exit 2; }
  [[ -f $2 ]] || { print -u 2 -- "trigger file missing: $2"; exit 2; }
  TRIGGERS=("${(@f)$(awk 'NF && $1 !~ /^#/ {print $1}' "$2")}")
  RUN_LABEL=provided_list
else
  TRIGGERS=($@)
  RUN_LABEL=$([[ $# == 1 ]] && print $1 || print provided_list)
fi
(( ${#TRIGGERS[@]} > 0 )) || { print -u 2 -- "no triggers selected"; exit 2; }

RUNROOT=$REPO/logs/codex_campaign20/p3/$RUN_LABEL

source /Users/salim/anaconda3/etc/profile.d/conda.sh
conda activate threeML
set -u
unsetopt BG_NICE

export FERMI_DIR=$CONDA_PREFIX/share/fermitools
export CALDB=$FERMI_DIR/data/caldb
export CALDBCONFIG=$CALDB/software/tools/caldb.config
export CALDBALIAS=$CALDB/software/tools/alias_config.fits
export CALDBROOT=$CALDB
export EXTFILESSYS=$FERMI_DIR/refdata/fermi
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export MPLBACKEND=Agg
export PYTHONUNBUFFERED=1
export PYTHONPATH=$RUNTIME${PYTHONPATH:+:$PYTHONPATH}

cd $REPO
mkdir -p $RUNROOT /private/tmp/codex_campaign20_sed

run_one() {
  local trig=$1
  local bin_arg=$2
  local model=$3
  local attempt=$4
  local grid=$REPO/results/convention_check/sed_grid_$trig
  local tag=$([[ $bin_arg == tint ]] && print TINT || print bin$bin_arg)
  local logfile=$grid/logs/${tag}_${model}_attempt${attempt}.log
  local statusfile=$grid/logs/status/${tag}_${model}_attempt${attempt}.status
  local scratch=/private/tmp/codex_campaign20_sed/${trig}_${tag}_${model}_attempt${attempt}
  local engine_rc=0
  local check_rc=0

  mkdir -p $grid/logs/status $scratch/pfiles $scratch/mpl $scratch/numba $scratch/xdg
  export PFILES=$scratch/pfiles
  export MPLCONFIGDIR=$scratch/mpl
  export NUMBA_CACHE_DIR=$scratch/numba
  export XDG_CACHE_HOME=$scratch/xdg

  {
    print -r -- "STARTED_UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    print -r -- "CAMPAIGN_RUN_LABEL: $RUN_LABEL"
    print -r -- "POOL_SIZE: $POOL_SIZE"
    print -r -- "THREAD_LIMITS: OMP=1 OPENBLAS=1 MKL=1 NUMEXPR=1 VECLIB=1"
    print -r -- "MPLBACKEND: $MPLBACKEND"
    print -r -- "COMMAND: $PYTHON scripts/41c_paper_sed.py --trig $trig --bin $bin_arg --model $model --out $grid --fit-root results/convention_check"
    $PYTHON scripts/41c_paper_sed.py \
      --trig $trig --bin $bin_arg --model $model \
      --out $grid --fit-root results/convention_check
    engine_rc=$?
    print -r -- "ENGINE_EXIT_CODE: $engine_rc"
    print -r -- "FINISHED_UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > $logfile 2>&1

  $PYTHON $HELPER --mode check --workers $POOL_SIZE --trig $trig \
    --grid $grid --bin $bin_arg --model $model >> $logfile 2>&1
  check_rc=$?
  if (( check_rc == 0 )); then
    print -r -- "OK"$'\t'"$model"$'\t'"$bin_arg"$'\t'"attempt=$attempt"$'\t'"engine_rc=$engine_rc" > $statusfile
    print -r -- "attempt=$attempt OK $trig $model $bin_arg engine_rc=$engine_rc"
  else
    print -r -- "FAIL"$'\t'"$model"$'\t'"$bin_arg"$'\t'"attempt=$attempt"$'\t'"engine_rc=$engine_rc"$'\t'"log=$logfile" > $statusfile
    print -r -- "attempt=$attempt FAIL $trig $model $bin_arg engine_rc=$engine_rc"
  fi
  return 0
}

run_attempt() {
  local attempt=$1
  local worklist=$RUNROOT/worklist_attempt${attempt}.tsv
  local plan_summary=$RUNROOT/plan_attempt${attempt}.json
  local closure_summary=$RUNROOT/closure_attempt${attempt}.json

  # This call preflights every non-blocked canonical table before writing the
  # full cross-trigger list. No engine starts until it succeeds.
  $PYTHON $HELPER --mode campaign-plan --workers $POOL_SIZE \
    --triggers ${TRIGGERS[@]} --attempt $attempt --quarantine-invalid \
    --worklist $worklist --campaign-summary-out $plan_summary || return 2
  local pending=$(wc -l < $worklist | tr -d ' ')
  print -r -- "P3_ATTEMPT_START $(date -u +%Y-%m-%dT%H:%M:%SZ) run=$RUN_LABEL attempt=$attempt triggers=${#TRIGGERS[@]} pending=$pending pool=$POOL_SIZE"

  if (( pending > 0 )); then
    local pooldir=$(mktemp -d /private/tmp/codex_campaign20_p3_pool.XXXXXX)
    local fifo=$pooldir/tokens
    mkfifo $fifo
    exec 9<>$fifo
    # Arithmetic form makes the PI-mandated token count explicit and directly
    # probeable; this pool contains exactly sixteen tokens.
    local slot
    for (( slot=1; slot<=POOL_SIZE; slot++ )); do
      print -u 9 token
    done

    while IFS=$'\t' read -r trig bin_arg model; do
      [[ -z $trig ]] && continue
      read -r -u 9 token
      (
        run_one $trig $bin_arg $model $attempt
        print -u 9 token
        exit 0
      ) &
    done < $worklist
    wait
    exec 9>&-
    exec 9<&-
    rm -f $fifo
    rmdir $pooldir
  fi

  $PYTHON $HELPER --mode campaign-finalize --workers $POOL_SIZE \
    --triggers ${TRIGGERS[@]} --attempt $attempt \
    --campaign-summary-out $closure_summary
  local snapshot_rc=$?
  print -r -- "P3_ATTEMPT_END $(date -u +%Y-%m-%dT%H:%M:%SZ) run=$RUN_LABEL attempt=$attempt validation_rc=$snapshot_rc"
  return 0
}

print -r -- "P3_SWEEP_START $(date -u +%Y-%m-%dT%H:%M:%SZ) run=$RUN_LABEL triggers=${#TRIGGERS[@]} pool=$POOL_SIZE"
run_attempt 1 || exit 2
run_attempt 2 || exit 2
$PYTHON $HELPER --mode campaign-finalize --workers $POOL_SIZE \
  --triggers ${TRIGGERS[@]} \
  --campaign-summary-out $RUNROOT/campaign_summary.json
final_rc=$?
print -r -- "P3_SWEEP_END $(date -u +%Y-%m-%dT%H:%M:%SZ) run=$RUN_LABEL validation_rc=$final_rc"
exit $final_rc

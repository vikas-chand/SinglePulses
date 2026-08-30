#!/bin/zsh
# Campaign-owned shell-level pool for the 20-burst P1 fit family worklist.
# Each scripts/10 invocation is a one-core process; the FIFO token bucket keeps
# exactly 16 independent engine calls in flight whenever at least 16 remain.

REPO=/Users/salim/Desktop/Projects/SingleRest/Two_Breaks
PYTHON=/Users/salim/anaconda3/envs/threeML/bin/python
WORKLIST=${1:-$REPO/notes/codex_campaign20_runtime/p1_worklist.tsv}
RUNTIME=$REPO/notes/codex_campaign20_runtime
LOGROOT=$REPO/logs/codex_campaign20/p1
STATUSROOT=$LOGROOT/status
POOL_SIZE=16

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
mkdir -p $LOGROOT $STATUSROOT /private/tmp/codex_campaign20_threeml_logs

expected_models() {
  case "$1" in
    default) print 6 ;;
    shape) print 8 ;;
    highe) print 24 ;;
    threecomp) print 18 ;;
    *) return 2 ;;
  esac
}

valid_family_output() {
  local trig=$1
  local family=$2
  local outdir=$3
  local expected=$(expected_models $family)
  $PYTHON - "$trig" "$family" "$outdir" "$expected" <<'PY'
import json
import sys
from pathlib import Path
from astropy.table import Table

trig, family, root, expected = sys.argv[1], sys.argv[2], Path(sys.argv[3]), int(sys.argv[4])
high = (
    "BAND", "CPL", "SBPL", "DSBPL", "BANDBB", "CPLBB",
    "SBPLF", "DSBPLF", "BANDPL", "BANDCPL", "CPLPL", "CPLCPL",
    "BANDRCPL", "BANDCUT", "SBPLCUT", "SBPLPL", "SBPLCPL",
    "BANDBBPL", "BANDBBCPL", "CPLBBPL", "CPLBBCPL", "SBPLBB",
    "SBPLBBPL", "SBPLBBCPL",
)
display = {
    "BAND": "Band", "CPL": "CPL", "SBPL": "SBPL", "DSBPL": "DSBPL",
    "BANDBB": "Band+BB", "CPLBB": "CPL+BB", "SBPLF": "SBPLfree",
    "DSBPLF": "DSBPLfree", "BANDPL": "Band+PL", "BANDCPL": "Band+CPL",
    "CPLPL": "CPL+PL", "CPLCPL": "CPL+CPL", "BANDRCPL": "BandR+CPL",
    "BANDCUT": "BandxCut", "SBPLCUT": "SBPLxCut", "SBPLPL": "SBPL+PL",
    "SBPLCPL": "SBPL+CPL", "BANDBBPL": "Band+BB+PL",
    "BANDBBCPL": "Band+BB+CPL", "CPLBBPL": "CPL+BB+PL",
    "CPLBBCPL": "CPL+BB+CPL", "SBPLBB": "SBPL+BB",
    "SBPLBBPL": "SBPL+BB+PL", "SBPLBBCPL": "SBPL+BB+CPL",
}
expected_prefixes = {
    "default": high[:6],
    "shape": high[:8],
    "highe": high,
    "threecomp": tuple(p for p in high if p not in {
        "DSBPL", "SBPLF", "DSBPLF", "BANDRCPL", "BANDCUT", "SBPLCUT"}),
}[family]
ecsv, sidecar = root / "spectral_fits.ecsv", root / "spectral_fits.json"
if not (ecsv.is_file() and sidecar.is_file()):
    raise SystemExit(1)
try:
    table = Table.read(ecsv, format="ascii.ecsv")
    meta = json.loads(sidecar.read_text())
    models = tuple(c[:-4] for c in table.colnames if c.endswith("_AIC"))
    blocks = sorted(int(v) for v in table["BLOCK"])
    assert len(models) == expected
    assert models == expected_prefixes, (models, expected_prefixes)
    assert meta["trigger"] == trig
    assert meta.get("models") == [display[p] for p in expected_prefixes]
    assert len(table) == int(meta["n_blocks"]) + 1
    assert blocks == [-1] + list(range(int(meta["n_blocks"])))
    if trig in {"bn081224887", "bn110721200"}:
        assert "lle" in meta.get("fit_dets", [])
        assert all("lle" in str(v).split(",") for v in table["PLUGIN_DETS"])
except Exception:
    raise SystemExit(1)
raise SystemExit(0)
PY
}

run_one() {
  local trig=$1
  local family=$2
  local label=$3
  local outdir=$REPO/results/convention_check/$trig/family_runs/$label
  local logfile=$LOGROOT/${trig}_${label}.log
  local statusfile=$STATUSROOT/${trig}_${label}.status
  local blocks=$REPO/results/sweep106/$trig/blocks/bb_blocks_spectral_${trig}.ecsv
  local pfiles=/private/tmp/codex_campaign20_pfiles/${trig}_${label}
  local mplconfig=/private/tmp/codex_campaign20_mpl/${trig}_${label}
  local numbacache=/private/tmp/codex_campaign20_numba/${trig}_${label}
  local xdgcache=/private/tmp/codex_campaign20_xdg/${trig}_${label}
  local engine_rc=0
  local extra=()
  local modelarg=()

  if valid_family_output $trig $family $outdir; then
    printf 'REUSED\t%s\t%s\t%s\t%s\n' "$trig" "$family" "$label" "$outdir" > $statusfile
    print -r -- "REUSED $trig $family ($label)"
    return 0
  fi

  if [[ -e $outdir/spectral_fits.ecsv || -e $outdir/spectral_fits.json ]]; then
    printf 'BLOCKED_INVALID_EXISTING\t%s\t%s\t%s\t%s\n' "$trig" "$family" "$label" "$outdir" > $statusfile
    print -r -- "BLOCKED_INVALID_EXISTING $trig $family ($label)"
    return 3
  fi

  mkdir -p $outdir $pfiles $mplconfig $numbacache $xdgcache
  # Keep a private writable PIL directory per engine process, while retaining
  # the read-only Fermitools system parameter fallback.  A bare private path
  # makes LAT tools fail with ``ParFileError: gtbin.par not found``.
  export PFILES="$pfiles;$FERMI_DIR/syspfiles"
  export MPLCONFIGDIR=$mplconfig
  export NUMBA_CACHE_DIR=$numbacache
  export XDG_CACHE_HOME=$xdgcache

  if [[ $trig == bn081224887 || $trig == bn110721200 ]]; then
    extra=(--include-lat)
  fi
  if [[ $family != default ]]; then
    modelarg=(--models $family)
  fi

  local started=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  {
    print -r -- "STARTED_UTC: $started"
    print -r -- "POOL_SIZE: $POOL_SIZE"
    print -r -- "THREAD_LIMITS: OMP=1 OPENBLAS=1 MKL=1 NUMEXPR=1 VECLIB=1"
    print -r -- "MPLBACKEND: $MPLBACKEND"
    print -r -- "COMMAND: $PYTHON scripts/10_spectral_fit_burst.py --trigger $trig --include-bgo --no-log --blocks-file $blocks --bkg-file results/background_intervals.ecsv --out-dir $outdir ${extra[*]} ${modelarg[*]}"
    $PYTHON scripts/10_spectral_fit_burst.py \
      --trigger $trig --include-bgo --no-log \
      --blocks-file $blocks \
      --bkg-file results/background_intervals.ecsv \
      --out-dir $outdir ${extra[@]} ${modelarg[@]}
    engine_rc=$?
    local finished=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    print -r -- "ENGINE_EXIT_CODE: $engine_rc"
    print -r -- "FINISHED_UTC: $finished"
  } > $logfile 2>&1

  if valid_family_output $trig $family $outdir; then
    printf 'COMPLETE\t%s\t%s\t%s\tengine_rc=%s\t%s\n' "$trig" "$family" "$label" "$engine_rc" "$outdir" > $statusfile
    print -r -- "COMPLETE $trig $family ($label) engine_rc=$engine_rc"
    return 0
  fi

  printf 'FAILED\t%s\t%s\t%s\tengine_rc=%s\t%s\t%s\n' "$trig" "$family" "$label" "$engine_rc" "$outdir" "$logfile" > $statusfile
  print -r -- "FAILED $trig $family ($label) engine_rc=$engine_rc"
  return 1
}

pooldir=$(mktemp -d /private/tmp/codex_campaign20_p1_pool.XXXXXX)
fifo=$pooldir/tokens
mkfifo $fifo
exec 9<>$fifo
for _ in {1..$POOL_SIZE}; do
  print -u 9 token
done

print -r -- "P1_POOL_START $(date -u +%Y-%m-%dT%H:%M:%SZ) pool=$POOL_SIZE worklist=$WORKLIST"
while IFS=$'\t' read -r trig family label; do
  [[ -z $trig || $trig == \#* ]] && continue
  read -r -u 9 token
  (
    run_one $trig $family $label
    local rc=$?
    print -u 9 token
    exit $rc
  ) &
done < $WORKLIST

wait
pool_rc=$?
exec 9>&-
exec 9<&-
rm -f $fifo
rmdir $pooldir

print -r -- "P1_POOL_END $(date -u +%Y-%m-%dT%H:%M:%SZ) wait_rc=$pool_rc"
exit 0

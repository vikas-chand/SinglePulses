#!/bin/zsh
# Products driver (Codex-out fallback, 2026-08-16 night): for every burst whose
# canonical 24-model table exists and that has no DONE marker, run the full
# product chain. One burst at a time (the fit pool owns most cores); renders
# 4-way inside a burst. Usage: campaign_products_driver.sh [TRIG]  (no arg =
# queue mode over all ready bursts, queue order).
source /Users/salim/anaconda3/etc/profile.d/conda.sh
conda activate threeML
export FERMI_DIR=$CONDA_PREFIX/share/fermitools CALDB=$FERMI_DIR/data/caldb
export CALDBCONFIG=$CALDB/software/tools/caldb.config
export CALDBALIAS=$CALDB/software/tools/alias_config.fits
export CALDBROOT=$CALDB EXTFILESSYS=$FERMI_DIR/refdata/fermi
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg
# `conda activate threeML` drops anaconda3/bin from PATH, which is where
# pandoc lives; xelatex is under homebrew. Without both, scripts/48 writes
# the .md and warns 'No such file or directory: pandoc' -- md-only reports
# (caught 2026-08-18 on 4 bursts). Appended, so threeML's python stays first.
export PATH=$PATH:/Users/salim/anaconda3/bin:/opt/homebrew/bin
# PROGRESS-BAR SPAM: threeML's tqdm writes ~15 MB of \r frames per burst log
# (2.9 GB of logs by the 8th burst, PI noticed disk/app-memory pressure).
export TQDM_DISABLE=1
cd /Users/salim/Desktop/Projects/SingleRest/Two_Breaks
mkdir -p logs/campaign20/products results/campaign20_products_done
# RAM ARBITER (PI 2026-08-17). Measured peaks on this machine:
#   41c SED render 0.52 GB | 47 CWT tree 3.74 GB (12 workers) | 46 0.44 GB
# The 140 GB shutdown was NESTED pools: N driver instances x 12 CWT
# workers x 2 renders, none aware of the others. Every instance now
# claims its burst-sized share from ONE machine-wide budget.
source dev/ram_slots.sh
: ${TB_BURST_SLOT_GB:=6}
# nested pools stay small; the arbiter owns machine-wide concurrency
export TB_CWT_WORKERS=${TB_CWT_WORKERS:-4}
CLAIMDIR=results/campaign20_products_claim
mkdir -p $CLAIMDIR

# The 20 report-bearing bursts (#3-#22): full 24-model grids. Others: winner+ties.
REPORT20=(bn081224887 bn090530760 bn090620400 bn090719063 bn090804940
          bn090809978 bn090829672 bn091209001 bn100122616 bn100130729
          bn100612726 bn100614498 bn100707032 bn101126198 bn101225377
          bn110605183 bn110618366 bn110721200 bn110920546 bn110928180)

run_burst() {
  local TRIG=$1
  local LOG=logs/campaign20/products/${TRIG}.log
  local MARK=results/campaign20_products_done/${TRIG}
  [ -f "$MARK" ] && return 0
  # atomic claim: mkdir succeeds for exactly one worker
  mkdir "$CLAIMDIR/$TRIG" 2>/dev/null || return 0
  ram_admit $TB_BURST_SLOT_GB || { rmdir "$CLAIMDIR/$TRIG" 2>/dev/null; return 1; }
  local MYSLOTS=(${TB_MY_SLOTS[@]})
  # zsh has NO RETURN trap ('undefined signal: RETURN' -- verified 2026-08-18);
  # in zsh an EXIT trap set inside a function fires when the FUNCTION returns.
  # The RETURN form silently never ran, so claim dirs leaked and every
  # already-processed burst silently no-op'd on re-run (mkdir claim fails).
  trap 'rmdir "$CLAIMDIR/$TRIG" 2>/dev/null; for t in ${MYSLOTS[@]}; do rmdir $t 2>/dev/null; done' EXIT
  local PH=logs/campaign20/products/${TRIG}
  echo "== $TRIG products start $(date -u +%H:%M:%SZ)" >> $LOG

  python3 dev/merge_campaign_families.py --trig $TRIG >> $LOG 2>&1 || return 1
  [ -f results/convention_check/$TRIG/spectral_fits.ecsv ] || return 1

  # temporal suite — phase markers make every step skip-on-resume
  step() { local name=$1; shift; [ -f "$PH.$name" ] && return 0; \
           "$@" >> $LOG 2>&1 && touch "$PH.$name"; }
  step t46 python scripts/46_temporal_all106.py --only $TRIG --workers 1
  step t44 python scripts/44_step_figures.py --trig $TRIG
  # step9 MUST come from the canonical campaign table, not the stale sweep106
  # one (figure-verifier BLOCKING find 2026-08-17): rebuild it via the shim.
  step t44b python dev/rebuild_step9_canonical.py --trig $TRIG
  step t47 python scripts/47_mvt_cwt_crosscheck.py --trig $TRIG
  # THE 15 GB STEP (measured 2026-08-18: 15.5 + 14.3 GB for two concurrent
  # bursts). Five of these ran at once on 2026-08-17 = ~75 GB, which is what
  # drove the machine to ~140 GB and shut it down. It now claims its own
  # oversized share from the machine-wide budget, so at a 32 GB budget only
  # ONE burst can be in this step at a time.
  if [ ! -f "$PH.bala" ]; then
    local KEEP=(${TB_MY_SLOTS[@]})
    ram_admit ${TB_MVT_SLOT_GB:-16}
    local MVTSLOTS=(${TB_MY_SLOTS[@]})
    ( cd /Users/salim/Desktop/Projects/GRB_Handbook_Project && \
      python -m grb_pipeline.pipeline.mvt_runner \
        --catalog /Users/salim/Desktop/Projects/SingleRest/Two_Breaks/results/background_intervals.ecsv \
        --data-root /Users/salim/Desktop/Projects/SingleRest/Two_Breaks/data \
        --output-root /Users/salim/Desktop/Projects/SingleRest/Two_Breaks/results/mvt_upstream/run_step7 \
        --mvt-python /Users/salim/anaconda3/envs/mvt/bin/python \
        --workers 1 --triggers $TRIG ) >> $LOG 2>&1 && touch "$PH.bala"
    for t in ${MVTSLOTS[@]}; do rmdir $t 2>/dev/null; done
    TB_MY_SLOTS=(${KEEP[@]})
  fi
  step t47b python scripts/47b_temporal_figs.py --trig $TRIG
  step t47c python scripts/47c_lag_latbright.py --trig $TRIG

  # BROADBAND GUARD (2026-08-17): 12 bursts were fitted with a LAT plugin, but
  # the panel renderer has no LAT support, so every replay is refused by the
  # fidelity guard (measured gap 72.4 AIC on bn081224887). Skip the grid and
  # disclose, rather than burn hours producing refusals.
  if grep -q "LAT plugin ON" logs/campaign20/${TRIG}_highe.log 2>/dev/null; then
    mkdir -p results/convention_check/sed_grid_$TRIG
    cat > results/convention_check/sed_grid_$TRIG/BROADBAND_NO_PANELS.txt <<NOTE
SED panels are NOT available for this burst.
It was fitted with a LAT plugin (see logs/campaign20/${TRIG}_highe.log).
scripts/41_nuFnu_panels.build_plugins has no LAT support, so a replay of the
stored solution has a different likelihood and the frozen-replay guard refuses
to draw the panel (panel-engine fidelity rule). Fits and tables are complete
and canonical; only the SED grid is missing. Fix = add LAT to the panel plugin
builder; decision pending PI review.
NOTE
    echo "  BROADBAND: SED grid skipped (LAT in fit) — disclosure written" >> $LOG
  else
  # SED grid: full for the report 20, winner+ties otherwise
  local FULL=0
  for r in $REPORT20; do [ "$r" = "$TRIG" ] && FULL=1; done
  python3 - "$TRIG" "$FULL" << 'PYEOF' > /tmp/sed_jobs_$TRIG.txt
import sys
import numpy as np
from astropy.table import Table
trig, full = sys.argv[1], sys.argv[2] == "1"
t = Table.read(f"results/convention_check/{trig}/spectral_fits.ecsv")
models = sorted({c[:-4] for c in t.colnames if c.endswith("_AIC")})
for row in t:
    b = int(row["BLOCK"]); tag = "tint" if b == -1 else str(b)
    aics = {m: float(row[f"{m}_AIC"]) for m in models
            if np.isfinite(row[f"{m}_AIC"])}
    if not aics:
        continue
    best = min(aics.values())
    todo = models if full else [m for m, v in aics.items() if v < best + 2.0]
    import glob as _g
    for m in todo:
        btag = "TINT" if tag == "tint" else f"bin{tag}"
        if _g.glob(f"results/convention_check/sed_grid_{trig}/"
                   f"{trig}_SED_{btag}_*.png"):
            hits = {p.rsplit("_", 1)[-1][:-4].upper()
                    for p in _g.glob(f"results/convention_check/"
                                     f"sed_grid_{trig}/{trig}_SED_{btag}_*.png")}
            if m.upper() in hits or m.upper().replace("+", "") in hits:
                continue
        print(trig, tag, m)
PYEOF
  local i=0
  while read -r T B M; do
    [ -z "$T" ] && continue
    ( python scripts/41c_paper_sed.py --trig $T --bin $B --model $M \
        --out results/convention_check/sed_grid_$T \
        --fit-root results/convention_check >> $LOG 2>&1 \
      && echo "OK $T $B $M" >> results/convention_check/sed_grid_$T/sweep_status.txt \
      || { echo "SEDFAIL $T $B $M" >> $LOG; \
           echo "FAIL $T $B $M" >> results/convention_check/sed_grid_$T/sweep_status.txt; } ) &
    i=$((i+1)); (( i % 2 == 0 )) && wait   # 8-core cap (PI 2026-08-17: memory)
  done < /tmp/sed_jobs_$TRIG.txt
  wait
  # one retry pass for failures (frozen-replay usually recovers)
  grep "^SEDFAIL" $LOG | sort -u | while read -r _ T B M; do
    python scripts/41c_paper_sed.py --trig $T --bin $B --model $M \
      --out results/convention_check/sed_grid_$T \
      --fit-root results/convention_check >> $LOG 2>&1 \
      && { echo "SEDRECOVERED $T $B $M" >> $LOG; \
           echo "OK $T $B $M (retry)" >> results/convention_check/sed_grid_$T/sweep_status.txt; }
  done

  fi
  python3 scripts/41e_sed_montage.py --trig $TRIG >> $LOG 2>&1
  python scripts/41d_param_evolution.py --trig $TRIG \
    --fit-root results/convention_check \
    --out results/convention_check/param_evolution >> $LOG 2>&1
  # per-burst REPORT (md + PDF) — every burst gets one, papered or not
  python scripts/48_burst_report.py --trig $TRIG \
      --out results/sweep106/$TRIG >> $LOG 2>&1
  [ -f "results/sweep106/$TRIG/REPORT_${TRIG}.pdf" ] \
      && echo "  report PDF ok" >> $LOG \
      || echo "  WARN: no report PDF for $TRIG" >> $LOG

  # executable notebook — ships with the report (PI: "I hope we will get
  # analysis notebooks too"). Pure computation, no LLM calls by design.
  if [ ! -f "notebooks/outputs/${TRIG}.ipynb" ]; then
    python notebooks/run_grb.py $TRIG --depth full --execute >> $LOG 2>&1 \
      && echo "  notebook executed" >> $LOG \
      || echo "  WARN: notebook failed for $TRIG" >> $LOG
  fi

  # mechanical gate: a burst is only marked DONE if its invariants hold, so a
  # defective product set can never silently enter the report queue.
  if python3 dev/verify_burst_invariants.py --trig $TRIG >> $LOG 2>&1; then
    date -u +%Y-%m-%dT%H:%M:%SZ > $MARK
    echo "== $TRIG products DONE (invariants pass) $(date -u +%H:%M:%SZ)" >> $LOG
  else
    echo "== $TRIG products BUILT but INVARIANTS FAILED $(date -u +%H:%M:%SZ)" >> $LOG
    echo "$TRIG" >> logs/campaign20/invariants_failed.txt
  fi
}

if [ -n "$1" ]; then
  run_burst "$1"
else
  while true; do
    launched=0
    for d in results/campaign20_fam/*_highe; do
      [ -f "$d/spectral_fits.ecsv" ] || continue
      b=$(basename $d _highe)
      case "$b" in bn081125496|bn081222204) continue;; esac
      [ -f "results/campaign20_products_done/$b" ] && continue
      run_burst "$b"; launched=1
    done
    nfits=$(pgrep -f "10_spectral_fit_burst" | wc -l | tr -d ' ')
    ndone=$(ls results/campaign20_products_done 2>/dev/null | wc -l | tr -d ' ')
    [ "$launched" -eq 0 ] && [ "${nfits:-0}" -eq 0 ] && \
      [ "${ndone:-0}" -ge 1 ] && break
    sleep 120
  done
  echo "PRODUCTS QUEUE DRAINED ($(ls results/campaign20_products_done | wc -l | tr -d ' ') bursts)"
fi

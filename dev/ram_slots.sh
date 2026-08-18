#!/bin/zsh
# ------------------------------------------------------------------
# Machine-wide RAM semaphore.  PI ruling 2026-08-17: concurrency is
# budgeted in GB against 64 GB physical, never in cores, never into swap.
#
# The 2026-08-17 shutdown was caused by NESTED, UNCOORDINATED pools:
# 5 products-driver instances x 12 forked CWT workers (47:96) x a
# 16-way fit pool, each layer sized as if it owned the machine.
# Cores are shared by the OS; RAM is not.  Every heavy job must pass
# through here so there is exactly ONE arbiter.
#
#   source dev/ram_slots.sh
#   ram_admit 4        # blocks until 4 GB of budget AND 4 GB of real free RAM
#   ...work...
#   ram_release        # always, via trap
# ------------------------------------------------------------------
: ${TB_RAM_BUDGET_GB:=32}     # total budget handed out to jobs
: ${TB_RAM_FLOOR_GB:=8}       # never admit if real free RAM would drop below this
: ${TB_RAM_WAIT_S:=20}
TB_SLOTDIR=${TB_SLOTDIR:-/tmp/two_breaks_ram_slots}
mkdir -p $TB_SLOTDIR

# AVAILABLE memory, not "free". macOS parks reclaimable pages in `inactive`
# and `speculative`; `Pages free` alone reads ~0 on a healthy busy machine and
# produced a false LOW that set the HOLD brake (caught 2026-08-18 mid-run,
# cross-checked against `memory_pressure`: 89% free while "free" said 0.1 GB).
_ram_avail_gb() {
  vm_stat | awk '/Pages free/ {gsub(/\./,"",$3); f=$3}
                 /Pages inactive/ {gsub(/\./,"",$3); i=$3}
                 /Pages speculative/ {gsub(/\./,"",$3); s=$3}
                 /Pages purgeable/ {gsub(/\./,"",$3); p=$3}
                 END {printf "%d", (f+i+s+p)*16384/1073741824}'
}
_ram_free_gb() { _ram_avail_gb; }
_ram_swapouts() { vm_stat | awk '/Swapouts/ {gsub(/\./,"",$2); print $2}'; }
_ram_held_gb() { ls $TB_SLOTDIR 2>/dev/null | wc -l | tr -d ' '; }

ram_admit() {
  local need=${1:-2}
  TB_MY_SLOTS=()
  local base=$(_ram_swapouts)
  while true; do
    local held=$(_ram_held_gb) free=$(_ram_free_gb) swo=$(_ram_swapouts)
    # HARD ABORT: the machine is already paging. Swap is not a warning, it is
    # the failure mode (PI, after the 140 GB shutdown).
    if [ "$swo" -gt "$base" ]; then
      echo "[ram_slots] ABORT: $((swo-base)) swapouts since admission opened" >&2
      return 2
    fi
    # manual/automatic brake: `touch $TB_SLOTDIR/HOLD` pauses ALL admission
    # (the watchdog sets it; you can set it by hand to stop a run growing)
    if [ -e $TB_SLOTDIR/HOLD ]; then sleep $TB_RAM_WAIT_S; continue; fi
    if [ $((held + need)) -le $TB_RAM_BUDGET_GB ] && \
       [ $((free - need)) -ge $TB_RAM_FLOOR_GB ]; then
      local ok=1 i
      for i in $(seq 1 $need); do
        local tok=$TB_SLOTDIR/$$_${i}_$RANDOM
        mkdir $tok 2>/dev/null && TB_MY_SLOTS+=($tok) || { ok=0; break; }
      done
      [ $ok -eq 1 ] && { echo "[ram_slots] admitted ${need}GB (held $(_ram_held_gb)/$TB_RAM_BUDGET_GB, free ${free}GB)"; return 0; }
      ram_release
    fi
    sleep $TB_RAM_WAIT_S
  done
}

ram_release() { local t; for t in $TB_MY_SLOTS; do rmdir $t 2>/dev/null; done; TB_MY_SLOTS=(); }
ram_reset() { rm -rf $TB_SLOTDIR; mkdir -p $TB_SLOTDIR; echo "[ram_slots] budget cleared"; }

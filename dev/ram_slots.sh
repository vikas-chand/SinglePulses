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
#
# NEVER hold slots while waiting for more (hold-and-wait deadlocks N callers).
# Release what you hold, then admit the larger claim.
# ------------------------------------------------------------------
: ${TB_RAM_BUDGET_GB:=32}     # total budget handed out to jobs
: ${TB_RAM_FLOOR_GB:=8}       # never admit if real free RAM would drop below this
: ${TB_RAM_WAIT_S:=20}
TB_SLOTDIR=${TB_SLOTDIR:-/tmp/two_breaks_ram_slots}
# Tokens live in their own subdir so control files (HOLD) are never counted
# as budget -- ram_watchdog.sh excluded HOLD but _ram_held_gb did not, and a
# stray file silently shrank the budget by 1 GB apiece.
TB_SLOTS=$TB_SLOTDIR/slots
mkdir -p $TB_SLOTS

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
_ram_held_gb() { ls $TB_SLOTS 2>/dev/null | wc -l | tr -d ' '; }

# Reclaim slots whose owner is gone. Traps CANNOT be relied on for this:
#   * zsh defers a signal trap until the foreground child returns, so a kill
#     during the multi-minute MVT step is handled minutes later;
#   * SIGKILL and a machine shutdown run no trap at all -- which is exactly
#     how the 2026-08-17 crash ended.
# Every slot records its owner PID, and admission reaps dead owners first, so
# a leak heals itself instead of permanently shrinking the budget. (/tmp is
# cleared on reboot, so PID reuse across boots cannot resurrect a stale slot.)
_ram_reap() {
  local d pid
  for d in $TB_SLOTS/slot_*(N/); do
    pid=$(cat $d/pid 2>/dev/null)
    if [ -z "$pid" ] || ! kill -0 $pid 2>/dev/null; then
      rm -f $d/pid 2>/dev/null; rmdir $d 2>/dev/null
    fi
  done
}

ram_admit() {
  local need=${1:-2}
  TB_MY_SLOTS=()
  local base=$(_ram_swapouts) waited=0
  while true; do
    # manual/automatic brake: `touch $TB_SLOTDIR/HOLD` pauses ALL admission
    # (the watchdog sets it; you can set it by hand to stop a run growing)
    if [ -e $TB_SLOTDIR/HOLD ]; then sleep $TB_RAM_WAIT_S; continue; fi
    _ram_reap
    local swo=$(_ram_swapouts)
    # HARD ABORT: the machine is already paging. Swap is not a warning, it is
    # the failure mode (PI, after the 140 GB shutdown).
    if [ "$swo" -gt "$base" ]; then
      echo "[ram_slots] ABORT: $((swo-base)) swapouts since admission opened" >&2
      return 2
    fi
    local free=$(_ram_avail_gb)
    if [ $((free - need)) -ge $TB_RAM_FLOOR_GB ]; then
      # ATOMIC CLAIM. Slot names are FIXED and shared, so `mkdir` is a real
      # mutex: exactly one caller can create slot_007. The previous scheme
      # named tokens $$_${i}_$RANDOM, which never collide -- mkdir always
      # succeeded, so a check-then-create race let two callers both pass
      # `held+need <= budget` and overshoot the budget (ultrareview bug_007).
      local got=() i
      for i in $(seq 0 $((TB_RAM_BUDGET_GB - 1))); do
        [ ${#got[@]} -ge $need ] && break
        if mkdir $TB_SLOTS/slot_$i 2>/dev/null; then
          echo $$ > $TB_SLOTS/slot_$i/pid; got+=($TB_SLOTS/slot_$i)
        fi
      done
      if [ ${#got[@]} -ge $need ]; then
        TB_MY_SLOTS=(${got[@]})
        echo "[ram_slots] admitted ${need}GB (held $(_ram_held_gb)/$TB_RAM_BUDGET_GB, avail ${free}GB)"
        return 0
      fi
      # Not enough free slots: give back every one we took before sleeping.
      # Holding a partial claim across the wait is hold-and-wait -- the
      # deadlock class that wedges 3+ drivers (ultrareview bug_009).
      for i in ${got[@]}; do rm -f $i/pid 2>/dev/null; rmdir $i 2>/dev/null; done
    fi
    waited=$((waited + TB_RAM_WAIT_S))
    (( waited % 300 == 0 )) && \
      echo "[ram_slots] still waiting for ${need}GB after ${waited}s (held $(_ram_held_gb)/$TB_RAM_BUDGET_GB)" >&2
    sleep $TB_RAM_WAIT_S
  done
}

ram_release() { local t; for t in ${TB_MY_SLOTS[@]}; do rm -f $t/pid 2>/dev/null; rmdir $t 2>/dev/null; done; TB_MY_SLOTS=(); }
ram_reset() { rm -rf $TB_SLOTDIR; mkdir -p $TB_SLOTS; echo "[ram_slots] budget cleared"; }

#!/bin/zsh
# Machine-wide memory watchdog (PI 2026-08-17). Emits one line per state
# change; sets the HOLD brake the moment the machine starts paging, so no
# NEW job is admitted while we are in trouble. Never kills running science.
SLOT=${TB_SLOTDIR:-/tmp/two_breaks_ram_slots}
# tokens live in slots/, control files (HOLD) at the top level, so the
# held count needs no HOLD exclusion any more (ultrareview bug_003)
SLOTS=$SLOT/slots
mkdir -p $SLOTS
FLOOR=${TB_RAM_FLOOR_GB:-8}
base=$(vm_stat | awk '/Swapouts/ {gsub(/\./,"",$2); print $2}')
last=""
while true; do
  # AVAILABLE, not free (see dev/ram_slots.sh) — `Pages free` reads ~0 on a
  # healthy busy Mac because reclaimable pages sit in inactive/speculative.
  read free comp swo <<< $(vm_stat | awk '
    /Pages free/ {gsub(/\./,"",$3); f=$3}
    /Pages inactive/ {gsub(/\./,"",$3); i=$3}
    /Pages speculative/ {gsub(/\./,"",$3); v=$3}
    /Pages purgeable/ {gsub(/\./,"",$3); p=$3}
    /occupied by compressor/ {gsub(/\./,"",$5); c=$5}
    /Swapouts/ {gsub(/\./,"",$2); s=$2}
    END {printf "%.1f %.1f %d", (f+i+v+p)*16384/1073741824, c*16384/1073741824, s}')
  # macOS pgrep has no -c
  nproc=$(pgrep -f "scripts/10_|scripts/41c|scripts/46_|scripts/47_" 2>/dev/null | wc -l | tr -d " ")
  state=OK
  if [ "$swo" -gt "$base" ]; then state=PAGING
  elif (( $(echo "$free < $FLOOR" | bc -l) )); then state=LOW
  fi
  if [ "$state" != "OK" ]; then touch $SLOT/HOLD; else rm -f $SLOT/HOLD; fi
  if [ "$state$nproc" != "$last" ]; then
    echo "$(date -u +%H:%M:%SZ) $state free=${free}GB compressor=${comp}GB swapouts=$((swo-base)) jobs=$nproc held=$(ls $SLOTS 2>/dev/null | wc -l | tr -d " ")GB"
    last="$state$nproc"
  fi
  sleep 15
done

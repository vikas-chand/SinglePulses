#!/bin/zsh
# Sample RSS of a process tree + system-wide swap/compressor every 2 s.
# usage: rss_sampler.sh <root_pid> <outfile>
PID=$1; OUT=$2
echo "elapsed_s tree_rss_GB nproc sys_free_GB compressor_GB swapouts" > $OUT
T0=$(date +%s)
while kill -0 $PID 2>/dev/null; do
  ALL=$(ps -A -o pid=,ppid=,rss= | awk -v r=$PID '
    { rss[$1]=$3; par[$1]=$2 }
    END { for (p in rss) { q=p; d=0; while (q!="" && q!=0 && d<12) { if (q==r) { s+=rss[p]; n++; break } q=par[q]; d++ } } printf "%.3f %d", s/1048576, n }')
  VM=$(vm_stat)
  FREE=$(echo "$VM" | awk '/Pages free/ {gsub(/\./,"",$3); printf "%.2f", $3*16384/1073741824}')
  COMP=$(echo "$VM" | awk '/occupied by compressor/ {gsub(/\./,"",$5); printf "%.2f", $5*16384/1073741824}')
  SWO=$(echo "$VM" | awk '/Swapouts/ {gsub(/\./,"",$2); print $2}')
  echo "$(( $(date +%s) - T0 )) $ALL $FREE $COMP $SWO" >> $OUT
  sleep 2
done

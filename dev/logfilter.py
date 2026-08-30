#!/usr/bin/env python3
"""Collapse repeated engine-log lines: keep first 3 of each signature + a count.
Usage: <engine> | python3 dev/logfilter.py > burst.log"""
import re, sys
from collections import Counter
sig_re = re.compile(r"[0-9]+\\.?[0-9]*")
seen = Counter()
tail = []
for line in sys.stdin:
    sig = sig_re.sub("#", line.strip())[:120]
    seen[sig] += 1
    if seen[sig] <= 3:
        sys.stdout.write(line)
    tail.append(sig)
sys.stdout.write("\\n=== SUPPRESSED REPEATS (signature: count) ===\\n")
for sig, n in seen.most_common(40):
    if n > 3:
        sys.stdout.write(f"{n:9d}  {sig}\\n")

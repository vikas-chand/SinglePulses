#!/usr/bin/env python3
"""Minimal sandboxing (adopted 2026-08-29): raw TTE/response dirs are
read-only to the pipeline. Blocks Bash commands that delete or overwrite
under data/bn* unless they are the acquisition path (download scripts).
Honest limit: pattern-based, not a filesystem jail — Mode A gets the real
sandbox (Skeleton §8)."""
import sys, json, re
d=json.load(sys.stdin)
cmd=(d.get('tool_input') or {}).get('command','')
danger = re.search(r'(rm\s+(-\w+\s+)*|>\s*|>>\s*|mv\s+\S+\s+)(\S*data/bn)', cmd)
acquire = re.search(r'(download|acquire|curl|wget|fetch)', cmd)
if danger and not acquire:
    print("RAW-DATA GUARD: data/bn* is read-only to the pipeline "
          "(delete/overwrite blocked; acquisition scripts exempt).", file=sys.stderr)
    sys.exit(2)
sys.exit(0)

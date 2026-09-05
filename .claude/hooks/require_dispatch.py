#!/usr/bin/env python3
"""P9 MECHANICAL ENFORCEMENT (PI 2026-08-27: 'do we have to hard code it in a
customized way' -> yes, this file). PreToolUse on Bash: any command that
launches a pipeline producer is BLOCKED unless a dispatch plan exists and is
fresh (<24 h). The design is load-bearing, not advisory."""
import sys, json, os, re, time
data = json.load(sys.stdin)
cmd = (data.get('tool_input') or {}).get('command', '')
GATED = r'(scripts/10_spectral_fit_burst\.py|paper_chain\.sh|campaign20_refits\.sh|campaign_products_driver\.sh|assemble_report_paper\.py .*build|bin_remaining21\.sh)'
if not re.search(GATED, cmd):
    sys.exit(0)
plan = os.path.join(os.environ.get('CLAUDE_PROJECT_DIR','.'),
                    'results','campaign','DISPATCH_PLAN_paper_recovery.md')
plans = [plan] + [os.path.join(os.path.dirname(plan), f)
                  for f in os.listdir(os.path.dirname(plan))
                  if f.startswith('DISPATCH_PLAN')] if os.path.isdir(os.path.dirname(plan)) else []
fresh = any(os.path.exists(f) and time.time()-os.path.getmtime(f) < 86400 for f in plans)
if not fresh:
    print("P9 GATE: pipeline producer launch without a fresh dispatch plan "
          "(<24 h) in results/campaign/DISPATCH_PLAN_*.md. Run the dispatcher "
          "agent first — the roster is not optional.", file=sys.stderr)
    sys.exit(2)
sys.exit(0)

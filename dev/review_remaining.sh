#!/bin/zsh
# Resumable human review of the bursts still lacking a human_gui stamp.
# Recomputes the "still AI-only" list from the LIVE catalog each run, so you
# can Ctrl-C anytime and re-run this to continue where you left off. Each
# burst opens pre-loaded with the current (AI) selection (--seed-from-catalog);
# review/adjust/Accept and it re-stamps as human_gui / "Vikas Chand".
source /Users/salim/Desktop/Projects/SingleRest/Two_Breaks/dev/gui_review_env.sh

REMAIN=$(python - <<'PY'
from astropy.table import Table
t = Table.read('results/background_intervals.ecsv', format='ascii.ecsv')
out = []
for tr in sorted(set(str(x) for x in t['TRIGGER_NAME'])):
    m = [str(r['APPROVAL_MODE']) for r in t if str(r['TRIGGER_NAME']) == tr]
    if not any('human' in x for x in m):
        out.append(tr)
print(' '.join(out))
PY
)

N=$(echo $REMAIN | wc -w | tr -d ' ')
echo "=== $N bursts still need human review ==="
i=0
for B in ${(z)REMAIN}; do
  i=$((i+1))
  echo ""
  echo "########## [$i/$N] $B ##########  (Ctrl-C to stop; re-run to resume)"
  python scripts/39_approve_all.py gui --trigger $B --approver "Vikas Chand" --seed-from-catalog
done
echo ""
echo "=== done: all bursts in the catalog now carry a human_gui stamp ==="

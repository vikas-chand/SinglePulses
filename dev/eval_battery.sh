#!/usr/bin/env bash
# eval_battery.sh -- ONE command that measures the harness (harness need #3, 2026-09-02).
#
# "You cannot improve a harness you cannot measure" (PuppyGraph); "retest scaffolding whenever
# the model changes against a stable eval set" (Bowne-Anderson); "computational sensors first"
# (Böckeler). Until today the pieces existed -- lessons-as-tests, schema validation, the
# fit-table auditor, the Stage-1 benchmark -- but nothing ran them as one battery or recorded
# the result with the model and commit that produced it. This script does, and nothing else:
#
#   1. the full test suite over the products on disk (light tier);
#   2. the fit-table auditor over every promoted table (invariants; argmin == BEST_AIC_MODEL);
#   3. a known-results FROZEN REPLAY placeholder: it lists the reconciliation records that anchor
#      the engine (130427A, 110721A, 160625B) and reports UNBUILT loudly -- the replay compares
#      stored solutions, never refits, and is the next increment (dispatch plan A5);
#   4. writes results/campaign/eval/EVAL_<utc>.json with the provenance stamp (model_id, git head,
#      dirty flag), the sha256 of every table audited, and per-part PASS/FAIL, and appends one
#      ACTION_EVENT (primitive=verify) so the run is in the trace.
#
# Run it on every harness change and on every model change:   bash dev/eval_battery.sh
# Set TB_MODEL_ID=<model> so the record names the model (else it says "unknown", honestly).
# Exit 0 = every built part passed; 1 = a part failed; the UNBUILT replay never changes the exit.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
UTC="$(date -u +%Y%m%dT%H%M%SZ)"; OUT="results/campaign/eval"; mkdir -p "$OUT"
REPORT="$OUT/EVAL_${UTC}.json"; LOG="$OUT/EVAL_${UTC}.log"
status=0; parts=()

part() {  # name, exit code, detail
  local name="$1" rc="$2" detail="$3" verdict
  if [ "$rc" = "UNBUILT" ]; then verdict="UNBUILT"; elif [ "$rc" -eq 0 ]; then verdict="PASS"; else verdict="FAIL"; status=1; fi
  parts+=("{\"part\":\"$name\",\"verdict\":\"$verdict\",\"detail\":$(python3 -c 'import json,sys;print(json.dumps(sys.argv[1]))' "$detail")}")
  printf '%-22s %s  %s\n' "$name" "$verdict" "$detail" | tee -a "$LOG"
}

echo "EVAL BATTERY $UTC  (git $(git rev-parse --short=12 HEAD 2>/dev/null))" | tee "$LOG"

# 1. the suite
python3 -m pytest tests/ -q -p no:cacheprovider >"$OUT/pytest_${UTC}.txt" 2>&1; rc=$?
part "tests" "$rc" "$(tail -1 "$OUT/pytest_${UTC}.txt")"

# 2. fit-table auditor over every promoted table. Exit 0 = clean; 2 = FINDING (the gated argmin
#    differs from the engine's BEST_AIC_MODEL -- a PRODUCT finding, listed, not a harness failure);
#    anything else = the auditor crashed (a harness failure).
audited=(); arc=0; nfind=0; ncrash=0
for t in results/convention_check/bn*/spectral_fits.ecsv; do
  [ -f "$t" ] || continue
  python3 dev/fit_table_audit.py --table "$t" --out-dir "$OUT/audits_${UTC}" --quiet >>"$LOG" 2>&1; trc=$?
  v="OK"; if [ $trc -eq 2 ]; then v="FINDING"; nfind=$((nfind+1)); elif [ $trc -ne 0 ]; then v="CRASH"; ncrash=$((ncrash+1)); arc=1; fi
  audited+=("{\"table\":\"$t\",\"sha256\":\"$(shasum -a 256 "$t" | cut -c1-64)\",\"audit\":\"$v\"}")
done
part "fit_table_audit" "$arc" "${#audited[@]} promoted tables audited; $nfind with findings (argmin != engine winner); $ncrash crashes"

# 3. known-results frozen replay -- UNBUILT, said loudly (dispatch plan A5; never a refit)
part "known_results_replay" "UNBUILT" "anchors: notes/reconciliation/{bn130427324,bn110721200,bn160625945}.md; replay of stored solutions not yet coded"

# 4. the record
PROV="$(python3 dev/provenance_stamp.py)"
python3 - "$REPORT" "$PROV" "$(IFS=,; echo "${parts[*]}")" "$(IFS=,; echo "${audited[*]}")" "$status" <<'EOF'
import json, sys
report, prov, parts, audited, status = sys.argv[1:6]
doc = {'schema': 'two_breaks.eval_battery.v1', 'provenance': json.loads(prov),
       'parts': json.loads('[' + parts + ']'), 'audited_tables': json.loads('[' + audited + ']') if audited else [],
       'overall': 'PASS' if status == '0' else 'FAIL'}
json.dump(doc, open(report, 'w'), indent=1)
print('written', report, '->', doc['overall'])
EOF
python3 dev/action_event.py --primitive verify --phase finalize --actor script --identity dev/eval_battery.sh \
  --output "$REPORT" --rule "harness-need-3" --verdict "$([ $status -eq 0 ] && echo PASS || echo FAIL)" >/dev/null 2>>"$LOG"; erc=$?
[ $erc -eq 0 ] || { echo "trace event REFUSED (rc=$erc) -- see $LOG" | tee -a "$LOG"; status=1; }
exit $status

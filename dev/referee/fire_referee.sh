#!/bin/bash
# fire_referee.sh — clean-room launcher for the blind referee panel
# (RefereeLoop.md, NR-47 — was NR-41 until 2026-09-02). PAID Codex quota: PI-TRIGGERED ONLY, never
# auto-relaunched. Blindness by construction: the referee's workspace is a
# staged directory holding ONLY the product (+ optional response letter and
# diff for round 2). Report comes back sha-bound to the product.
# Usage: fire_referee.sh <product.(pdf|tex)> <T0|T1|T2> [response_letter diff]
set -euo pipefail
PRODUCT="${1:?usage: fire_referee.sh <product> <T0|T1|T2> [response_letter diff]}"
ROLE="${2:?role T0|T1|T2}"
case "$ROLE" in T0|T1|T2) ;; *) echo "role must be T0|T1|T2" >&2; exit 1;; esac
[ -f "$PRODUCT" ] || { echo "no such product: $PRODUCT" >&2; exit 1; }
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
BRIEF="$REPO/dev/referee/BRIEF_${ROLE}.md"
[ -f "$BRIEF" ] || { echo "missing brief $BRIEF" >&2; exit 1; }
SHA=$(shasum -a 256 "$PRODUCT" | cut -c1-16)
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
ROOM=$(mktemp -d "/tmp/referee_${ROLE}_XXXXXX")
cp "$PRODUCT" "$ROOM/"
[ $# -ge 3 ] && cp "$3" "$ROOM/RESPONSE_LETTER.md"   # round 2
[ $# -ge 4 ] && cp "$4" "$ROOM/DIFF.patch"           # round 2
OUT="$REPO/notes/referee/$(basename "${PRODUCT%.*}")_${ROLE}_${STAMP}.md"
echo "CLEAN ROOM: $ROOM  (contents: $(ls -m "$ROOM"))"
echo "PRODUCT sha256[0:16]=$SHA  ROLE=$ROLE  -> report will land at $OUT"
echo "This spends PAID Codex quota. Ctrl-C now to abort; starting in 10 s."
sleep 10
( cd "$ROOM" && codex exec -m gpt-5.6-sol -c model_reasoning_effort="ultra" \
    -s workspace-write "$(cat "$BRIEF")" < /dev/null )
REPORT="$ROOM/REPORT_${ROLE}.md"
if [ -f "$REPORT" ]; then
  { echo "# BLIND REFEREE $ROLE — $(basename "$PRODUCT") @ sha $SHA — $STAMP"
    echo "# clean room: only the product was staged; verdict expires if the product's sha changes"
    echo; cat "$REPORT"; } > "$OUT"
  echo "REPORT SAVED: $OUT"
else
  echo "NO REPORT PRODUCED (referee failed or wrote nothing) — do NOT auto-relaunch; diagnose first. Clean room kept: $ROOM" >&2
  exit 2
fi
rm -rf "$ROOM"

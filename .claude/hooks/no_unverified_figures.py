#!/usr/bin/env python3
"""MECHANICAL ENFORCER (AgentArchitecture register; armed 2026-08-16 on the
PI's 'we must complete whatever is there' instruction): blocks SendUserFile
delivery of any .png figure whose sha256 appears in NO VISION_QC ledger.
Scope: .png only (papers/PDFs carry their own verification trail).
Disable: remove the hook entry from .claude/settings.json."""
import sys, json, hashlib, glob, os

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)                      # malformed input: never block blindly
    files = (payload.get("tool_input") or {}).get("files") or []
    pngs = [f for f in files if str(f).lower().endswith(".png")]
    if not pngs:
        sys.exit(0)
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ledgers = glob.glob(os.path.join(root, "results", "**", "VISION_QC.md"), recursive=True)
    corpus = "".join(open(l, errors="ignore").read() for l in ledgers)
    missing = []
    for f in pngs:
        try:
            h = hashlib.sha256(open(f, "rb").read()).hexdigest()
        except Exception:
            missing.append(f"{f} (unreadable)")
            continue
        if h not in corpus and h[:16] not in corpus:
            missing.append(f"{os.path.basename(f)} sha256 {h[:16]}…")
    if missing:
        print("BLOCKED by the no-ship gate: figure(s) not found in any VISION_QC "
              "ledger — run the figure-verifier and record the sha256-bound verdict "
              "first:\n  " + "\n  ".join(missing), file=sys.stderr)
        sys.exit(2)
    sys.exit(0)

main()

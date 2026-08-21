# CODEX BRIEF — v3 agent-architecture build audit — 2026-08-21

Run mode: GPT-5.6, Sol, **Ultra**. Working directory:
/Users/salim/Desktop/Projects/SingleRest/Two_Breaks (git branch: memory-guard).
READ-ONLY except your report. Write only notes/CODEX_AGENTARCH_V3_20260821.md.
ONE exception, item 4 below, gives you a sandboxed write path with mandatory cleanup.

Environment: /Users/salim/anaconda3/bin/python3 has numpy/pandas/astropy/scipy/pymupdf.
No fits or heavy compute are needed for this review; do NOT launch pipeline scripts.

## Artefacts of record (sha256 prefix pinned; ignore any other copy on disk)

| artefact | sha256[:12] |
|---|---|
| dev/ai_guides/AgentArchitecture.md | b3d2e548cd86 |
| docs/GRB_AGENT_FLOWCHART.md | 6d34f1eeea37 |
| dev/live_report.py | 37d462755024 |
| dev/invalidate_downstream.py | 2632628d358c |
| .claude/agents/dispatcher.md | 0646b42cdac2 |
| .claude/agents/port-verifier.md | 769ea95b2c93 |
| .claude/agents/seed-auditor.md | 773ea19315f4 |
| .claude/agents/tie-reporter.md | 44f91506305a |
| .claude/agents/admission-gate.md | 1fec9b632b03 |
| .claude/agents/prior-art-reader.md | 4fa42da773ae |
| docs/grb_agent_design_v3.html | db3eed87f62a |

docs/grb_agent_design_v3.html is a review copy of the published design page; the
markdown flowchart is its declared source of record. A near-duplicate of the html
exists under /private/tmp/...scratchpad/ — ignore it.

## Deliberate conventions — do not relitigate

- NR-11 is a RETIRED number (consumed by an operations audit, see
  dev/campaign20_refits.sh:2); the register intentionally jumps NR-10 → NR-12.
- invalidate_downstream.py is DRY-RUN BY DEFAULT and never deletes products —
  markers and stamps only. That asymmetry is designed, not an oversight.
- STALE demotion keeps the old stamp fields (audit trail), only status changes.
- The 6 new agent files + 2 scripts are deliberately uncommitted pending PI
  commit approval; the page says "4 committed, 6 pending commit" on purpose.
- The SED-conventions queue from your 2026-08-14 report (PGstat delchi, LLE
  generality, silent EAC except, EBOUNDS guard) is tracked elsewhere; out of
  scope here. NR-9 stored-ref binding from that report is DEPLOYED.

## What changed (one session, 2026-08-21)

Register grew NR-12..NR-19; two stale rows corrected; six agent definitions
created; a live-report + approval-stamp mechanism and an invalidation cascade
were built; the design page and flowchart were synced to v3.

## Verify — recompute from the artefacts; trust NO printed value

1. REGISTER INTEGRITY. Count the AGENT REQUIREMENTS REGISTER data rows yourself
   (claim: 29, excluding the header). For every row whose status says DEPLOYED,
   verify the deployment exists on disk and does what the row says: skill-reader/
   figure-verifier/numbers-verifier/distiller/dispatcher files in .claude/agents/;
   the SendUserFile hook in .claude/settings.json calling
   .claude/hooks/no_unverified_figures.py; NR-12 = dev/ram_slots.sh; NR-15 =
   the owner-PID reaper inside it; NR-18/NR-19 = the two scripts. Any DEPLOYED
   claim without a matching artefact is a discrepancy.
2. AGENT DEFINITIONS. For each of the six new files: frontmatter parses
   (name/description/tools); the stated single purpose matches its register row;
   the instructions cannot be read as granting approval power to a producer
   (the dispatcher explicitly forbids self-approval — check the other five for
   loopholes); tool lists are the minimum the job needs.
3. LIVE REPORT — STATIC. Read dev/live_report.py end to end. Claims: (a) a stamp
   without --by raises (the no-fabricated-approver rule); (b) the document links
   only evidence that exists on disk, asserting nothing; (c) unrouted feedback
   renders as "PENDING — protocol defect"; (d) approving/feeding back a step with
   later APPROVED steps prints the NR-19 warning naming exactly those steps.
   Hunt for paths that break (a)–(d): e.g. can --present fabricate progress? can
   a crafted --feedback string corrupt the JSON or the markdown table?
4. LIVE REPORT + CASCADE — DYNAMIC (your one write exception). Create
   results/sweep106/bnTEST000/ and exercise the full loop there with --by CODEX:
   present → approve 7 → approve 8 → feedback on 7 → confirm the warning names
   step 8 → run the cascade WITHOUT --execute (nothing may change) → with
   --execute (step 8 must demote to STALE; no file outside bnTEST000 and no
   logs/campaign20/products/bnTEST000.* marker of a REAL burst may be touched —
   verify by listing logs/campaign20/products/ before and after). THEN DELETE
   results/sweep106/bnTEST000 ENTIRELY and state in your report that you did:
   a surviving CODEX-stamped approval would itself violate the architecture.
5. CASCADE MAP. Check the step→phase dependency table in
   invalidate_downstream.py against the actual phase markers the driver writes
   (dev/campaign_products_driver.sh: t46, t44, t44b, t47, bala, t47b, t47c).
   Two specific questions: is clearing ONLY t44b on a step-6 change actually
   sufficient to make the driver regenerate SED grids/montages/report, given
   how the driver decides what to (re)run? And does 'ALL' on steps 2–5 cover
   everything a Stage-1 change invalidates, or do promoted tables under
   results/convention_check/<trig>/ survive stale?
6. PAGE ↔ FLOWCHART ↔ DISK SYNC. The html and the markdown must make identical
   claims (dispatcher in boot; approval rail; 29 rows; NR-11 retired; 10 agent
   files, 4 committed + 6 pending — verify with git ls-files/status yourself;
   v3 dated 2026-08-21). Mermaid in both must be syntactically valid.
7. STRESS-TEST NARRATIVE. Both documents recount: an external review found 2
   normal-severity bugs + 1 broken invariant in the RAM arbiter, and the fix
   revealed zsh trap deferral / SIGKILL immunity, closed by owner-PID reaping.
   Verify against the code and history: dev/ram_slots.sh (_ram_reap, fixed
   slot names slot_0..N-1 as a real mkdir mutex), git log on this branch
   (commit b82fc9c). Confirm the narrative claims nothing the code does not do.

## Verification rules

- Check against the artefacts and git history, never against a derived summary.
- An invariant that cannot find its reference must FAIL LOUDLY, not skip.
- Prefer a demonstration (run it, diff it) over an argument.

## Output contract

VERDICT — SIGN OFF or DO NOT SIGN OFF (state plainly)
Per item 1–7: CONFIRMED / NOT CONFIRMED, with the derivation shown
DISCREPANCIES: each with the exact fix
COULD NOT VERIFY: what and why
Confirmation that bnTEST000 was deleted.

Finally, your own independent judgement: anything wrong or fragile that this
brief did not ask about.

# Background review request — AI consensus catalog (for Khushboo)

**2026-07-13.** The full Stage-1 selection (detectors + background + source) for all
**106 GRBs** has been done by a **two-AI consensus** (Claude + Codex, each reading the
same rule guides in `dev/ai_guides/`) and is now the authoritative catalog:
`results/background_intervals.ecsv` (pushed, commit `6a96a2b`). **We'd like your human
review / approval before we lock the science numbers.**

## What to look at (fastest path)
`plots/approved_selections/` has **one overlay PNG per burst**. Each shows, on the
reference detector's light curve:
- the **fitted background** (orange polynomial) through the approved **pre/post
  windows** (green),
- the approved **source interval** (red),
- a **background-subtracted net** panel underneath,
- the title carries the **detectors** used and the **approver stamp**.

Flip through them (or view on GitHub). If a window or source looks wrong, note the
trigger — that's all we need.

## How the consensus was built (context)
- Claude (vision) and Codex each independently picked detectors + windows + source.
- **~90% auto-approved** where both agreed (detector-Jaccard ≥ 0.8 **and** source-IoU
  ≥ 0.5). Detector selection was near-identical between the two AIs.
- **14 bursts disagreed on the source extent** and were resolved by an independent
  third vision pass. Please give these extra scrutiny:
  `bn090530760, bn100122616, bn100130729, bn110920546, bn111009282, bn120420858,
   bn130215063, bn130427324, bn181212693, bn210803497, bn210812699, bn230802285,
   bn240403498, bn241223506`.
  (Codex tended to over-extend the tail into background; we kept the tighter window
  except where a genuine extended episode was present — bn090530760, bn110920546.)
- One detector-set question: **bn100130729** — Codex added a weak high-side n6+b1;
  we kept the conservative low-side set. Your call.

## How to approve or override
Pick whichever:
1. **Accept as-is** — the catalog already carries an `ai_vision` consensus stamp;
   if you're happy, nothing to do, just tell us.
2. **Re-review any burst yourself** — `python scripts/39_approve_all.py gui --trigger <bn...>`
   re-stamps that row `human_gui` with your name (see `INSTRUCTIONS_KHUSHBOO.md` for
   setup). Your stamp supersedes the AI one for that burst.
3. **Just flag them** — send us the list of triggers you'd redo and we'll re-run.

## Known defect to re-check (found by Vikas, 2026-07-13)
The **pre** background window on ~15 bursts sits **too far before the burst** (it should
*hug* the burst — inner edge ~5–20 s before it — not stop 20–40 s short). The rule has
been strengthened (`dev/ai_guides/background_selection.md`, HUG-THE-BURST). These 15
need the pre window moved closer (and, where a data gap precedes the burst, anchored on
the settled baseline near the burst, not the post-gap edge):
`bn201104001, bn090829672, bn191125206, bn210410037, bn191129141, bn241117845,
 bn140608153, bn210812699, bn230802285, bn240403498, bn160330827, bn120420858,
 bn150202999, bn170114833, bn151021791`.

## Why now
The Stage 2–3 re-fit (binning + 6-model spectral fits) has already been run on this
consensus catalog, so the paper numbers are ready — they just need your sign-off on
the selections underneath. Nothing is locked until you've looked.

Thank you! — questions to Vikas.

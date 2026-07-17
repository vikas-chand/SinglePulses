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
2. **Re-review any burst yourself** — `MPLBACKEND=TkAgg python scripts/39_approve_all.py gui --trigger <bn...> --approver "Khushboo Sharma"`
   re-stamps that row `human_gui` with your name (see `INSTRUCTIONS_KHUSHBOO.md` for
   setup). Your stamp supersedes the AI one for that burst.
3. **Just flag them** — send us the list of triggers you'd redo and we'll re-run.

## Near-edge MARGIN — found by Vikas 2026-07-13, now FIXED (please CONFIRM)
The background inner edge should sit in a **~5–20 s band** from the burst — near enough
to interpolate, but with a safe margin so the burst's soft tail doesn't leak in. The
rule was strengthened (`dev/ai_guides/background_selection.md`, "HUG THE BURST" + the
5–20 s band). **49 bursts fell outside the band and have been RE-SELECTED** under the new
rule (a vision pass that keeps inner edges outside data gaps/SAA steps and clears the
soft tail): **15 too-far-pre + 22 too-tight + 12 too-far-post.** The catalog is now
**fully band-consistent: g_pre median 10 s, g_post median 15 s, 0 too-far, 0 too-tight,
0 source-in-gap violations.**

So these are **DONE — please just CONFIRM they look right** (montages:
`plots/reselect_montages/reselect_bunch1–5.png` for the pre/tight fixes,
`reselect_farpost.png` for the 12 post fixes), and flag any you'd still change. The
re-selected rows are stamped `... + margin-reselect`.

## Independent Codex review (gpt-5.6-sol, 2026-07-14) — structural fixes applied
A second AI (Codex, ultra effort) did a final adversarial QA (`notes/codex_bkg_review.md`).
Its **structural findings were fixed** (montage `plots/reselect_montages/codex_fixes.png`):
- **bn081125496** — its pre window was on a NO-DATA segment (0 events); re-anchored onto
  real data (`[-23.5,-8]`, now ~20k events).
- **10 sub-5 s margins widened** to ≥5 s (bn081222204, bn090530760, bn100122616,
  bn131113483, bn150902733, bn160625945, bn201016019, bn210723615, bn230614424,
  bn231030832). bn081222204's outer edge (past data start) also clipped.
- **bn090719063** — added the required **b1** companion (both NaIs are high-side).

Catalog after fixes: **106 bursts, 0 source-in-gap violations, every margin in [5,40] s.**

### Human judgment queue (Codex flagged; YOUR call — reasons in `notes/codex_bkg_review.md`)
Codex ran an adversarial pass (it over-flags by design). These are **source-extent /
precursor / tail** judgment calls, NOT structural errors — please eyeball and confirm or
override. **Several were already adjudicated** in the consensus (source-extent), so many
will just confirm:
`bn090829672, bn100130729, bn130427324, bn180728728, bn230802285, bn240403498,
 bn110618366, bn110928180, bn120119170, bn120624933, bn160330827, bn171210493,
 bn200607921, bn221201517, bn241117845, bn180426549`.
One detector call: **bn210812699** — its only NaI (nb) is at 60.1°, 0.1° over the hard
60° cut; kept with a boundary exception, and Codex also sees a bump in its post window —
your decision to keep/redo/exclude. (Codex's 26 lower-priority "questionable" cases are
listed in the review doc.)

## Why now
The Stage 2–3 re-fit (binning + 6-model spectral fits) was run on an earlier version of
this catalog; it will be **re-run on the final catalog after your sign-off**, so the
paper numbers follow your approval. Nothing is locked until you've looked.

Thank you! — questions to Vikas.

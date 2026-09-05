# DIVERGENCE LEDGER

The third learning trigger (`FreshSessionBoot.md` §10 / NR-37): a recorded human decision
differs from what the written rule or the AI pass would produce, **and no one is in error** —
the human knew something unwritten. Detect → elicit → validate → generalize → ledger.
One row per case. The CONVERGENCE RATE over time is a first-class campaign metric.

| # | burst / step | what diverged | human's reason (verbatim) | one-off or rule | where the rule now lives | status |
|---|---|---|---|---|---|---|
| D-1 | bn110920546 (#21) / step 2 detectors | pipeline pre-ticked {n0,n1,n3,n6,n7,b0,b1} and both AI passes kept all 7 per the ≤50° rule; the recorded human decision kept {n0,n1,n3,b0}. n6 (25.33°) and n7 (47.68°) pass ≤50° but are not in the BCAT mask | *"I must have selected the ones those are on same side and probaly the triggered ones too"*; then, after the census: *"it's that when we have plenty of them then we check which one are triggered otherwise when we have scarcity we try to get atleast 1"* | rule (measured: BCAT 78%, geometry 48%, neither 100%) | `detector_selection.md` OBSERVED PRACTICE note (2026-08-31), rule NOT amended | ledgered |
| D-2 | bn240403498 (#96) / step 2 detectors | **n3 at 57.94°, IN the BCAT mask**, is exactly the written 50–60° rescue case — the rule says KEEP. The recorded human decision (Vikas Chand, human_gui, 2026-07-19) DROPPED it, keeping n0 (43.08°), n1 (22.59°), n2 (41.80°), n5 (35.27°) + b0. Four NaI already pass ≤50°. The #21 reason (BCAT) does not resolve it: n3 *is* in BCAT | PI, 2026-09-04, verbatim: *"if there is already three nai detectors then why we need n3, isn't 50-60 degree range needs to be taken when there is not enough (3) NAi detector?"* | **UNDECIDED — flagged for discussion at the PI's instruction**, verbatim: *"just write it as a flag or thing to discuss and then we change it later. for this burst continue with spproved selection"* | NOWHERE YET — `detector_selection.md` is deliberately UNAMENDED; see OPEN FLAG below | **OPEN — do not codify** |

## OPEN FLAG (D-2) — the rescue clause may be a SCARCITY remedy, not a bonus

**The question to settle later.** `detector_selection.md` states the rescue with no scarcity
condition: *"NaI 50° < θ ≤ 60° AND in BCAT mask → KEEP (rescue: it triggered, borderline
geometry)"*. The only scarcity language in the section is the fallback for when **nothing**
qualifies (*"keep the SINGLE closest BCAT NaI"*) — i.e. it covers zero, not "fewer than three".
The PI's practice on bn240403498 implies the rescue should fire only when the ≤50° set is too
small. Candidate forms, NOT adopted:
  (a) rescue only when fewer than 3 NaI pass ≤50°;
  (b) same, with BCAT membership still required of the rescued detector;
  (c) no threshold — a per-burst judgement made at the light curve.

**Evidence NOT gathered — census STOPPED at the PI's instruction, 2026-09-04.** A read-only
census over all 106 recorded decisions was started (recompute every detector's angle from that
day's poshist; score the WRITTEN rule and form (a) against the human's approved NaI set). The PI
stopped it at 22/106, verbatim: *"why did you check for 22 burst, please first check this burst
only"* — the rule decision was already deferred, so a 106-burst sweep was premature work on a
question nobody had asked to settle yet. **No output file was written** (the script wrote only at
the end) and the downloaded poshist files were deleted; the only surviving trace is the run log in
this session's scratch. One observation worth keeping from the partial run: **bn090530760 matched
NEITHER the written rule nor form (a)**, so whenever this flag is taken up, expect a percentage
rather than a clean sweep, and expect the census to cost ~1 h of downloads.

**Binding for now:** the written rule stands unamended, and **bn240403498 proceeds with the
approved selection {n0, n1, n2, n5, b0}** — PI instruction, 2026-09-04. Nothing downstream in
this burst depends on resolving the flag.

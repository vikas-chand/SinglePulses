# Walkthrough notebooks — burst #21 `bn110920546` (GRB 110920A)

**These are the SOURCE of the results, not summaries of them.** Every number recomputes from
the repository's own products when the notebook runs; nothing is typed in. If a notebook and a
report disagree, the report is wrong.

Structure (PI, 2026-09-01): *"once a step is finalized, everything should go to a notebook which
is numbered and we will in the end ship them together with every result as source of the results
and one can investigate them"* and *"there can be one for each products and at the end when a
report is made, then one notebook can be there which is combination of all"*.

So: **one notebook per finalized step**, numbered by the official BurstWalkthrough ledger
(PI ruling 2026-08-30), plus **one combined notebook built at step 9** with the report.

| step | notebook | status |
|---|---|---|
| 0b literature harvest | `bn110920546_step0b_literature.ipynb` | FINALIZED |
| 0 identity & GCN | `bn110920546_step0_identity.ipynb` | FINALIZED |
| 1 data inventory | `bn110920546_step1_inventory.ipynb` | FINALIZED |
| 2 detector selection | `bn110920546_step2_detectors.ipynb` | FINALIZED |
| 3 background | `bn110920546_step3_background.ipynb` | FINALIZED |
| 4 source window | `bn110920546_step4_source.ipynb` | FINALIZED |
| 5 binning | `bn110920546_step5_binning.ipynb` | FINALIZED |
| 6 fitting | `bn110920546_step6_fitting.ipynb` | PRESENTED — gate pending (widened-bounds table sha 45104924…; A9 numbers PASS / claim promotion CONDITIONAL FAIL folded in §3, §6b, §7) |
| 6 spectral fitting | — | refit done, gate pending |
| 7 temporal · 8 products · 9 report | — | not reached |
| ALL | `bn110920546_combined.ipynb` | built at step 9 |

## Conventions
- **Filenames carry the trigger ID** (lesson G1, `BurstWalkthrough.md`): every per-burst
  product is `<trigger>_<content>.ext`. Directories organise; filenames are the search
  surface, and 106 identical basenames are unfindable. Corrected 2026-09-01 after the PI
  caught these notebooks shipped without the prefix.
- A notebook is written when its step is **finalized** (PI-approved), not before.
- Every figure's sha256 is checked **inside the notebook** against the recorded gate verdict;
  the cell prints `matches the verified artifact? True`. If a figure is regenerated without
  re-verification, that line goes False.
- PI rulings appear **verbatim**, read from the catalogue's own amendment log where possible.
- Each notebook closes with **what may NOT be claimed** from that step.
- Failed attempts are kept (step 3's −18.21 cut that did not work), because the failure is
  usually the instructive part.

## Not to be confused with
`notebooks/outputs/bn110920546.ipynb` — a single whole-pipeline notebook from 2026-08-18,
predating all three background amendments and the refit. It is STALE and will mislead;
regenerate before use.

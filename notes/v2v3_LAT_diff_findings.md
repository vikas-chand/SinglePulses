# Phase A.1 — LLE prototype census + "what LAT adds" (v2 GBM+LLE ↔ v3 +LAT)

Written 2026-07-21. Closes the un-gated tail of Phase A.1 (`dev/PLAN_ship_the_paper.md`).
No re-fitting, no MC: the locked registry doctrine (`scripts/model_registry.py`,
ΔAIC≥10 top-two + chain-gated parents + degeneracy classes) applied to the existing
fit tables. Per-block table: `lle_census_v2v3.csv` (60 rows = 30 blocks × 2 arms).

## What the two arms are
Both arms are the SAME **coarse LLE grid** (`clean_blocks_lle_v2`), same detectors
(n6,n7,n9,nb,b1,lle for 110721A etc.), on the **10 LLE-signal bursts** (30 blocks total).
The only difference is the LAT plugin:
- **v2** = GBM + LLE. `PLUGIN_DETS = …,lle`
- **v3** = GBM + LLE + **LAT** (FermiLATLike >100 MeV). `PLUGIN_DETS = …,lle,LAT`
So every v2→v3 change traces to adding the LAT high-energy band — the clean "what LAT adds" test.

## Headline census (strict ΔAIC≥10 doctrine)

| | v2 (GBM+LLE) | v3 (+LAT) |
|---|---|---|
| blocks | 30 | 30 |
| exact INCONCLUSIVE | 27 (90%) | **22 (73%)** |
| class INCONCLUSIVE | 23 (77%) | **20 (67%)** |
| flavor-degenerate (class decisive, exact not) | 4 | 2 |
| exact winners | Band+BB×2, CPL+PL×1 | Band+BB×3, SBPLfree×3, SBPL+BB×1, CPL+BB×1 |
| class winners | extra_lowE_curvature×6, CPLPL×1 | extra_lowE_curvature×7, SBPLF×3 |

**LAT's net effect (exact level): +6 blocks decided, −1 un-decided, 1 flip → INCONCLUSIVE 27→22.**
Class level: +5 decided, 1 flip → class-INCONCLUSIVE 23→20.

Note the strict gate makes most blocks INCONCLUSIVE — this is the *locked* top-two
doctrine, NOT the min-AIC "winner" tallies quoted in older pilot notes (e.g. the
memory's "SBPL 23% / Band+BB 17% …" is min-AIC, not gated). Don't conflate the two.

## Per-block changes (the 8 blocks LAT moves)

| burst | blk | v2 exact | v2 gap | v3 exact | v3 gap | verdict |
|---|---|---|---|---|---|---|
| 110721200 | 0 | CPL+PL | 34.5 | INCONCLUSIVE | 0.1 | LAT **un-decides** |
| 110721200 | 1 | INCONCLUSIVE | 8.6 | Band+BB | 14.0 | LAT decides |
| 130518580 | 0 | Band+BB | 48.4 | SBPLfree | 16.5 | **flip** |
| 150902733 | 0 | INCONCLUSIVE | 8.9 | Band+BB | 14.2 | LAT decides |
| 160625945 | 10 | INCONCLUSIVE | 5.2 | SBPLfree | 31.4 | LAT decides |
| 160625945 | 11 | INCONCLUSIVE | 1.3 | SBPLfree | 17.2 | LAT decides |
| 160625945 | 15 | INCONCLUSIVE | 2.4 | SBPL+BB | 13.7 | LAT decides |
| 160910722 | 1 | INCONCLUSIVE | 0.2 | CPL+BB | 10.1 | LAT decides |

### The one un-decide (110721A blk0) is honest, not a regression
- v2 survivors: CPL+PL 2254.3, CPL+BB 2288.8, CPL 2306.1 → CPL+PL wins by 34.5.
- v3 survivors: CPL+PL **2367.3**, CPL+BB **2367.5**, CPL 2402.1 → gap **0.1**.
- Adding LAT lifts CPL+BB level with CPL+PL. These sit in *different* degeneracy classes
  (CPLPL vs extra_lowE_curvature), so the block is genuinely ambiguous between a high-E
  PL and low-E curvature once the >100 MeV band is included. v2's decisive CPL+PL was
  over-confident; LAT reveals the ambiguity. Report as an honest example, not a loss.

### The one flip (130518580 blk0)
Band+BB (v2, gap 48.4) → SBPLfree (v3, gap 16.5). Both survive both arms; LAT reweights
toward a single smoothly-broken continuum over thermal+continuum.

## Answering the plan's 160625B question ("does LAT break the flavor tie?")
Yes, in 3 previously-inconclusive tail blocks:
- blk10 → **SBPLfree** decisively (gap 31.4; runner-up SBPL+BB at +31).
- blk11 → **SBPLfree** decisively (gap 17.2; runner-up SBPL at +17).
- blk15 → **SBPL+BB** decisively (gap 13.7; runner-up SBPLfree at +14).
So on this grid LAT pulls 160625B's tail toward a single smoothly-broken continuum
(2 blocks) or thermal+continuum (1 block).

### ⚠ Discrepancy to reconcile: the "3-component" result is NOT reproduced here
Memory (`project_lle_two_tier_2026-07-17`) records a standout **CPL+BB+PL decisive at
160625945 blk15** on the *human arm* (`clean_per_burst_lle_human`). On THIS grid/arm
(v3), under the strict chain gate, no three-component model wins any 160625B block:
- blk15: SBPL+BB+PL *is* valid (AIC 6044.96) but is **worse than its own parent
  SBPL+BB (6042.8)** → fails the chain gate. CPL+BB+PL sits far back at 6079.9.
- blk10/11 similarly: the 3-comp fits are valid but never beat their 2-comp parents by
  the gate, so the extra hard PL does not earn its parameters.
Two candidate explanations, un-adjudicated: (a) the human-arm Stage-1 selections
(different backgrounds/source) genuinely change the tail, or (b) the human-arm 3-comp
tally used min-AIC, not the strict top-two chain gate. **Needs a direct human-arm ↔
v3 comparison on 160625B before either the 3-comp result or its absence goes in the paper.**

## Takeaways for the paper (Methods + Results)
1. LAT is not cosmetic: it lifts the decisive-block fraction from 10%→27% (exact) /
   23%→33% (class) on the prototype, and it does so by *breaking* GBM-band degeneracies
   in the high-E regime — the physical motivation for the two-tier LLE/LAT arm.
2. The dominant decisive shape once LAT is in is the smoothly-broken continuum
   (SBPLfree, 3 blocks) and low-E-curvature class (thermal/2SBPL, 7 blocks class-level).
3. Three-component models do not survive the strict gate on this grid — flag the
   human-arm discrepancy above; do not headline a 3-comp detection until reconciled.

## Files
- `notes/v2v3_LAT_diff_findings.md` (this note)
- `lle_census_v2v3.csv` (per-block, both arms — currently in scratchpad, awaiting a home)
- Diff script: `scratchpad/v2v3_diff.py`

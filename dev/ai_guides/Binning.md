# Skill: Binning (Step 5) — two-tier 3ML-native time bins

**Purpose:** produce the time bins Step 6 fits in — fine GBM Bayesian blocks for spectral
evolution, plus a separate coarse LLE grid where the high-energy band actually has counts.
**Audience:** anyone running Stage 2 (`scripts/27b`, `scripts/27c`).
**Reusable:** any GBM(-like) burst with an approved Stage-1 selection.

## Inputs
```yaml
trigger:        bn<XXXXXXXXX>
stage1:         results/background_intervals.ecsv   # approved dets + bkg + source, stamped
data:           data/<trigger>/glg_tte_*            # newest version per detector (audit #19)
env:            threeML conda env + CALDB exports (heavy tier)
```

## Outputs
```
results/<root>/bb_blocks_spectral_<trigger>.ecsv    # fine GBM grid, one row per (det, block)
results/<root>/bb_blocks_lle_<trigger>.ecsv         # coarse LLE grid (only if gate passes)
```
Same schema for both, so `scripts/10 --blocks-file` reads either unchanged. Merged edges are
replicated for every approved NaI. Filenames carry the trigger (lesson G1).

## Tier 1 — fine GBM blocks (`scripts/27b_reblock_3ml.py`)
3ML-native throughout (no custom BB implementation):
1. `TimeSeriesBuilder.from_gbm_tte` on the **reference (brightest) NaI**, 8–900 keV;
   `set_background_interval(pre, post)` with `poly_order=-1` (auto via LRT).
2. **Tighten to the emission window first** (`emission_window`, ported from `scripts/27`):
   BB over a wide, mostly-quiet approved window collapses to one block, and merging cannot
   undo a collapse. ⚠ This means Stage 2 fits a WINDOW INSIDE the human-approved source
   interval — deliberate, but it must be REPORTED per burst (audit 2026-08: the tightening was
   silent in 78/89 bursts; presenting it is Step-5's PRESENT duty, not optional).
3. `create_time_bins(method='bayesblocks', p0=0.01, use_background=True)` — the 3ML tutorial
   values (Burgess convention: p0=0.01, brightest-NaI).
4. Per-block significance via 3ML's own `Significance` class
   (`li_and_ma_equivalent_for_gaussian_background`, Vianello 2018 — the modeled-background
   case, exactly what `bin_by_significance` uses).
5. **Trim then merge** (the BB+significance hybrid): drop leading/trailing blocks below
   `SIG_TRIM = 4.5σ` (pure-background edges), then merge any INTERIOR block below
   `SIGMA_FLOOR = 5σ` into its neighbour until every survivor clears the floor
   (floor user-set 2026-06-24; cf. Burgess ≥3σ, 3ML default `sigma_level=10`).

```bash
# one burst (validation):
python scripts/27b_reblock_3ml.py --burst bn110721200 --out /tmp/cb3
# full sample (authoritative, FRESH out-root):
python scripts/27b_reblock_3ml.py --out <root>/clean_blocks
```

## Tier 2 — coarse LLE blocks (`scripts/27c_lle_blocks.py`, LLE bursts only)
Why a second grid: in the fine NaI-driven bins, 30–100 MeV LLE counts are ~zero per bin, so
the high-energy shape (cutoff, Band+CPL saddle, extra PL) is unconstrainable bin-by-bin —
the **bin-adequacy lesson (L6): the band that constrains a component must have counts in the
bins you fit it in.**
- `astropy.stats.bayesian_blocks(fitness='events', p0=0.01)` on 30–100 MeV events STRICTLY
  (the blocks must reflect the band that gets fit), inside the approved source window;
  off-source rate from the approved pre/post windows.
- 3σ floor (LLE is sparse), same trim-then-merge scheme.
- **GATE:** peak block < 3σ ⇒ NO LLE grid — the burst uses fine GBM blocks only. The gate
  withholds a *grid*, never the *data*: LLE still enters the joint fit (L17) on the GBM grid.

## PI RULING 2026-08-31 — a near-threshold edge block is KEPT (bn110920546 block 0)

**PI, VERBATIM:** "it's ok to have block 0 of that 5.38 sigma value"

**Context.** Block 0 of #21 clears the edge-trim threshold ACTUALLY APPLIED (5.0 sigma,
see the SIG_TRIM note below) by only **+0.382 sigma (7.6%)**; it is also **below the L6
adequacy floor of 10**, and it hosts 2 of the burst's 3 failed model fits. The alternative
was trimming it, which would have started the analysed span at +0.779 s instead of
-2.076 s. The PI ruled it KEPT.

**Operative consequences.**
1. A retained edge block is NOT thereby an adequate block. Block 0 stays in the analysis and
   stays flagged under L6/L6b: report per-block statistics BOTH ways (all blocks / S>=10
   subset), and never let a near-threshold block carry a claim on its own.
2. The quoted significance is the REFERENCE detector's (here n0), replicated across the
   approved-NaI rows by scripts/27b — it is not a combined-detector value and, per L6b,
   understates constraining power (~x2 for 4 plugins). Label it as such wherever quoted.
3. Presentation duty: a block whose margin over the applied trim threshold is < 1 sigma is
   DISCLOSED as near-threshold at the step-5 gate. Silence about it is the defect, not the
   block.

**Open, NOT resolved by this ruling — SIG_TRIM is dead as documented.** `Binning.md` (this
file, above) and `scripts/27b_reblock_3ml.py:45` both document `SIG_TRIM = 4.5` as the
"leading/trailing-edge drop threshold", but `trim_edges` is called with `SIGMA_FLOOR` (5.0)
at `:235`; `SIG_TRIM` is used only for peak detection at `:78`. The APPLIED rule is stricter
than the DOCUMENTED one. Verified 2026-08-31. Block 0's margin is +0.382 sigma against what
runs and +0.882 sigma against what is written. Which is intended is a PI decision; neither
this file's text nor the code has been changed pending it.

## Quality checklist
- [ ] Reference detector is a NaI, never LLE (an LLE-driven grid would free every GBM
      cross-norm — normalization degeneracy).
- [ ] Emission-window tightening REPORTED (original approved window vs tightened window).
- [ ] Every surviving block ≥ SIGMA_FLOOR; edge blocks ≥ SIG_TRIM.
- [ ] Newest TTE version used (`find_tte` sorts; audit #19).
- [ ] **External validation where published edges exist:** Li & Zhang 2021 publish BB counts +
      edges for many of our bursts; bn081224887 reproduces their 9 blocks and edges
      1.896 / 5.424 / 12.502 s to 3 decimals — guarded by
      `tests/test_lessons.py::test_L13_binning_edges_bn081224887`. Extend the check when a
      new burst has published edges.
- [ ] Fresh out-root for any authoritative re-run — never overwrite a gated product.

## Common pitfalls
- **BB collapse over quiet windows** — always tighten to the emission window first (above).
- **Extreme bursts OOM in events-mode BB** — use measures-mode BB (the bn130427A-class fix;
  memory `project_bb_oom_extreme_bursts`).
- **Railed upstream seeds poison blocks** (the historical T_INT/BB seed-poisoning class):
  binning itself is seed-free, but block COUNTS differ 250× across the sample (fluence range)
  — never assume a fixed block budget per burst.
- **A one-block result is a symptom**, not a burst property: check the window, the reference
  detector, and the background fit before believing it.
- **Different vintages don't co-register:** a 19-bin table and a 21-bin figure of the same
  burst are different binnings — never compare bin-by-bin across vintages (four-channel
  audit, bn130518580).

## Hand-off
Step 6 (`SpectralFitting.md`): `scripts/10 --blocks-file <fine or coarse ecsv>`. Joint
NaI+BGO+LLE(+LAT) high-E fits run on the COARSE grid first, then the fine grid separately
(two-tier doctrine, Vikas 2026-07-17). Step 8 reads the same blocks for νFν panels.

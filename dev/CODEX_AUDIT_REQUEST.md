# Codex Audit Request — Two_Breaks T_INT + BB pipeline (2026-05-22, round 2)

## Background

Round 1 audit (2026-05-21) found 4 MAJOR + 4 MINOR issues; we've patched
the 4 MAJOR ones. Since then we iterated on the T_INT-determination
algorithm. This is a focused re-audit on what changed.

## Files in scope (changed since round 1)

- `scripts/08_plot_multiband_bb.py` — `compute_t_int_cumsum_saturation()`
  + call site. Now uses ADAPTIVE plateau: `median(cumsum[argmax+1:])` as
  saturation target (replaces strict-argmax and fixed-`frac` versions).
  Also: TINT_BIN_S = 0.064 (was 0.256), TINT_FRAC = 0.95 (legacy constant,
  no longer passed since adaptive doesn't take frac).
- `scripts/09_review_time_integrated.py` — same adaptive plateau algorithm,
  same 64 ms binning. Has interactive GUI with arrow-key micro-adjust
  (shift+arrow = 16 bins ≈ 1 s).
- `scripts/00_prototype_one_burst.py` — removed Phase-3 catalog-T90 gate
  (the previous `raise SystemExit('Phase 3 BB step needs an active-time
  window...')` block); active-time interval now derived from approved bkg
  edges `(pre_interval[1], post_interval[0])`.

## Reference materials

- `~/Downloads/Fermi_lightcurve_autoselect.ipynb` cells 16+18 — Maccary/Salim
  original cumsum-saturation algorithm we riffed off
- Round-1 audit: `CODEX_AUDIT_REPORT.md` (in this dir; treat as known-good
  baseline, don't re-flag fixed items)
- `memory/feedback_no_catalog_t90_in_gui.md` — the rule that catalog T90
  must not enter any numerical step

## Specific things to check

### 1. Adaptive plateau threshold soundness

The current `_adaptive_first_reach` does:
```python
i_arg = argmax(cum)
if (n - i_arg - 1) >= min_post:
    plateau = median(cum[i_arg + 1:])
else:
    plateau = median(cum[-max(min_post, n//4):])
return argmax(cum >= plateau)
```

Concerns to verify:
- (a) Is `median(cumsum[argmax+1:])` a sound estimator of the random-walk
  plateau? For zero-mean noise after the burst, mean=plateau but median is
  more robust to outliers — confirm the choice.
- (b) On bn150902733 n0 it gave T_INT = [−7.21, 45.53] s (auto), which
  visibly over-extends past the burst (real burst ~0 to ~25 s). The user
  had to override to [−1.38, 27.29]. Diagnose why adaptive is overshooting:
  is `median(post_argmax)` running below the true burst total because
  random-walk excursions DOWN pull it down? Suggest a fix (use mean? use
  upper-quartile? clip negative excursions?) but DON'T implement.
- (c) The argmax-at-edge fallback (`plateau = median(cum[-max(5, n//4):])`)
  — is the n//4 window a defensible choice, or arbitrary?
- (d) The "argmax could be anywhere in the cumsum" assumption — what if
  the cumsum is non-monotonic? (It shouldn't be, since cumsum of net is
  monotone non-decreasing in the burst region and random-walks after.
  But Poisson resampling in the MC step could break monotonicity. Verify.)

### 2. MC bootstrap correctness

- Each Poisson draw resamples `counts_per_bin`, then subtracts the SAME
  fixed polyfit. Is this the right Bayesian / frequentist interpretation
  of "counting-only uncertainty"?
- Random seed is fixed at 42 in both scripts. Should it instead be per-run?
  Per-burst? Per-detector? Does this matter for downstream reproducibility?

### 3. The Phase-3 catalog-T90 gate removal

- Verify the `if t90 is None: raise SystemExit(...)` block in
  `phase3_post_ai` is fully gone.
- Verify that `t90_start`/`t90` are still threaded through to
  `review_one_detector()` ONLY for non-numerical purposes (legend labels,
  plot framing — NOT for click-routing per
  `memory/feedback_no_catalog_t90_in_gui.md`).
- `run_bb_for_detector` signature still takes `t90_start, t90`. Are those
  parameters actually used anymore? If not, can they be dropped?

### 4. Interactive GUI correctness in `09_review_time_integrated.py`

- The Adj START / Adj STOP buttons toggle `self._adjust_mode`. Verify
  that keypress handling only fires when adjust mode is active.
- The Reset button restores `self._auto_start` / `self._auto_stop`. Verify
  these are captured BEFORE any user clicks/keypresses.
- Save logic: when result == 'accept', saves with `OVERRIDDEN=self.overridden`.
  Verify this flag is set correctly by both keyboard arrows (adjust mode)
  AND by the legacy click-to-override path.
- macosx vs TkAgg: verify the try/except fallback for matplotlib backend
  doesn't break in headless environments.

### 5. Cross-script consistency

`compute_t_int_cumsum_saturation` exists in BOTH 08 and 09 (duplicated).
- Are the two copies byte-equivalent? If they've diverged, flag it.
- Suggest (don't implement) refactoring to a shared `lib/tint.py` so the
  algorithm has a single source of truth.

### 6. End-to-end sanity on the demo burst bn150902733

A worked-example burst:
- 4 detectors approved (n3, n0, n1, b0) with per-det bkg windows
  (see `results/background_intervals_prototype.ecsv`)
- BB output at `results/bb_blocks_prototype_bn150902733.ecsv`: 64 total
  blocks, all ≥ 3σ post-Phase-A merge. Detectors show poly_order 1-2
  (i.e. 3ML auto-selected polynomial > 0, makes sense for a 13-s burst
  with EE/orbital drift across the windows).
- T_INT (n0 only) reviewed and saved to
  `results/time_integrated_windows_reviewed.ecsv` (OVERRIDDEN=True).

Quick spot-check this is self-consistent: do the BB block boundaries in
the ECSV cover the user's overridden T_INT [−1.38, 27.29] s? Are any
blocks tagged IS_MERGED that shouldn't have been (e.g., a clearly-bright
block merged into a dim neighbor)?

## Out of scope

- The notebook's MC procedure literal port (round-1 minor #1 — we know
  it differs intentionally)
- The 8-900 keV "fully contained" channel-mask convention (round-1 minor
  #3 — we know and it's intentional)
- Stale comments updated since round 1

## Output format

Same as round 1: severity-ranked findings with file:line citations + a
PASS/FAIL spot-check table + 1-paragraph overall assessment.

Write to: `/Users/salim/Desktop/Projects/SingleRest/Two_Breaks/CODEX_AUDIT_REPORT_R2.md`

Don't modify any source files. Claude will read the report and patch.

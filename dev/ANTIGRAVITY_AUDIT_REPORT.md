# Antigravity Audit Report — Two_Breaks T_INT + BB pipeline (2026-05-22, round 2)

## Severity summary
- 0 critical bugs found
- 2 major issues
- 4 minor issues / suggestions

## Findings (in order of severity)

### [MAJOR] Click-to-override in review GUI is completely blocked and fails to set OVERRIDDEN flag
- File: [scripts/09_review_time_integrated.py:392](file:///Users/salim/Desktop/Projects/SingleRest/Two_Breaks/scripts/09_review_time_integrated.py#L392)
- File: [scripts/09_review_time_integrated.py:501-516](file:///Users/salim/Desktop/Projects/SingleRest/Two_Breaks/scripts/09_review_time_integrated.py#L501-L516)
- Issue: In the GUI mouse click-release handler `_on_release()`, the mouse clicks on the plot are ignored via `if not self.overridden: return` because `self.overridden` starts as `False`. However, there is no button or interactive control to toggle `self.overridden` to `True` before clicking. Clicks are therefore permanently ignored. Furthermore, even if this check were bypassed, the click handler `_add_click()` never sets `self.overridden = True` upon registering two clicks.
- Why it matters: This completely breaks the legacy click-to-override path. Users cannot define a new T_INT window using mouse clicks. While users can adjust endpoints using arrow keys in adjust mode, they cannot click-to-redraw intervals.
- Suggested fix: Remove `if not self.overridden: return` check in `_on_release()` (or only block clicks if adjust mode is active). Ensure that `self.overridden = True` is set inside `_add_click()` once a user clicks to override the interval.

### [MAJOR] Adaptive plateau threshold algorithm overshoots due to random-walk peaks in post-burst background
- File: [scripts/08_plot_multiband_bb.py:207-224](file:///Users/salim/Desktop/Projects/SingleRest/Two_Breaks/scripts/08_plot_multiband_bb.py#L207-L224)
- File: [scripts/09_review_time_integrated.py:129-143](file:///Users/salim/Desktop/Projects/SingleRest/Two_Breaks/scripts/09_review_time_integrated.py#L129-L143)
- Issue: The `_adaptive_first_reach()` helper determines the saturation threshold `plateau` by looking at the values after `i_arg = argmax(cum)`. For a zero-mean background after the burst, the cumulative net count is a random walk. Due to random-walk fluctuations, the absolute maximum `argmax(cum)` is highly likely to occur late in the post-burst background rather than at the true end of the burst. Because `i_arg` is located deep in the background, the plateau value (computed as the median of the few points after `i_arg`) is set very high. The `first_reach` check (searching for where `cum >= plateau`) then returns an index close to `i_arg`, causing the T_INT interval to over-extend deep into the background.
- Why it matters: On `bn150902733 n0`, this caused the auto-selected interval to over-extend to `[-7.21, 45.53]` s (real burst ends around ~25 s). Because the background random walk has large excursions, the auto-selected interval overshot the burst by 20+ seconds, requiring manual override.
- Suggested fix: Do not search for `argmax` over the entire range. Instead, define the plateau using a region known to be pure background (e.g. the last N seconds or the background interval) to estimate the true total net count. Alternatively, bound the search region or use a robust quantile (e.g., 90% or 95% of the total net counts estimated from the end of the LC) as the saturation target.

### [MINOR] Unused stale parameters `t90_start` and `t90` in detector review and BB signatures
- File: [scripts/00_prototype_one_burst.py:869](file:///Users/salim/Desktop/Projects/SingleRest/Two_Breaks/scripts/00_prototype_one_burst.py#L869)
- File: [scripts/00_prototype_one_burst.py:954](file:///Users/salim/Desktop/Projects/SingleRest/Two_Breaks/scripts/00_prototype_one_burst.py#L954)
- Issue: The parameters `t90_start` and `t90` are still present in the signatures of `review_one_detector()` and `run_bb_for_detector()`, but they are completely unused in their function bodies. In `review_one_detector()`, `BackgroundSelector` is instantiated with explicit `t90_start=None, t90=None` to ensure a T90-free GUI, and `run_bb_for_detector()` derives its active interval entirely from the background edges without using these parameters.
- Why it matters: Keeping dead parameters in the signature creates confusion and violates clean code principles, making it seem like catalog T90 is still playing a role in these steps.
- Suggested fix: Remove `t90_start` and `t90` from the signatures of `review_one_detector()` and `run_bb_for_detector()`, and clean up their call sites in `scripts/00_prototype_one_burst.py`.

### [MINOR] Matplotlib backend selection fails to degrade gracefully in headless environments
- File: [scripts/09_review_time_integrated.py:54-57](file:///file:///Users/salim/Desktop/Projects/SingleRest/Two_Breaks/scripts/09_review_time_integrated.py#L54-L57)
- Issue: The backend fallback try-except chain only tries `macosx` first, and if that fails, falls back to `TkAgg`. In headless environments where no display server is running (e.g., CI/CD or remote SSH), `TkAgg` will also fail to initialize, raising a `TclError` or display error when importing or using `pyplot`.
- Why it matters: This will crash the script during execution in headless environments or automated testing pipelines.
- Suggested fix: Add `Agg` as a final fallback in the backend selection chain:
  ```python
  try:
      matplotlib.use('macosx')
  except Exception:
      try:
          matplotlib.use('TkAgg')
      except Exception:
          matplotlib.use('Agg')
  ```

### [MINOR] Seed-reproducibility and correlated MC fluctuations across runs
- File: [scripts/08_plot_multiband_bb.py:175](file:///Users/salim/Desktop/Projects/SingleRest/Two_Breaks/scripts/08_plot_multiband_bb.py#L175)
- File: [scripts/09_review_time_integrated.py:113](file:///Users/salim/Desktop/Projects/SingleRest/Two_Breaks/scripts/09_review_time_integrated.py#L113)
- Issue: The random seed in `compute_t_int_cumsum_saturation` is hardcoded to `seed=42`. While this ensures reproducibility for a single run, it means that runs across different detectors or energy bands will use the exact same sequence of pseudo-random numbers if they have the same number of bins, leading to perfectly correlated MC fluctuations.
- Why it matters: This can introduce artificial correlation in the statistical error estimates of downstream multi-detector or multi-band combinations.
- Suggested fix: Derive a run-specific or detector-specific seed (e.g. hashing the detector name and trigger name) rather than using a static constant seed of 42.

### [MINOR] Dead constant `TINT_FRAC` passed but ignored by `compute_t_int_cumsum_saturation()`
- File: [scripts/08_plot_multiband_bb.py:415](file:///Users/salim/Desktop/Projects/SingleRest/Two_Breaks/scripts/08_plot_multiband_bb.py#L415)
- File: [scripts/09_review_time_integrated.py:724](file:///Users/salim/Desktop/Projects/SingleRest/Two_Breaks/scripts/09_review_time_integrated.py#L724)
- Issue: The constant `TINT_FRAC = 0.95` is defined in both scripts and passed to `compute_t_int_cumsum_saturation(..., frac=TINT_FRAC)`. However, the function signature has `**kwargs` and never references `frac` (or any kwarg) because the old fraction-of-max logic was replaced by `_adaptive_first_reach()`.
- Why it matters: Dead code and unused configuration values clutter the codebase and can mislead developers into thinking they are adjusting the saturation threshold when changing `TINT_FRAC`.
- Suggested fix: Remove `frac=TINT_FRAC` from the call sites and remove the unused `TINT_FRAC` constant from both scripts.

## Spot checks (PASS/FAIL)
- Energy-band mask applied at all get_total_poly_count call sites: PASS. The silent broadband fallback has been removed and replaced with a loud `RuntimeError` fallback in both scripts 08 and 09.
- No catalog T90 in numerical use: PASS. The `phase3_post_ai()` SystemExit gate has been removed and the BB active-time interval is now derived strictly from the approved background edges. Catalog T90 is only used optionally for non-numerical metadata.
- Phase-A merge not called in T_INT path: PASS. Scripts 08 and 09 use raw Scargle BB significance bins without any sub-threshold merging.
- Cumsum-saturation matches notebook algorithm: FAIL. The core point cumsum logic is equivalent, but the adaptive plateau threshold in `_adaptive_first_reach` has diverged, causing overshooting due to random-walk background peaks.
- MC procedure statistically sound: PASS for counting-only uncertainty; FAIL if interpreted as total T_INT uncertainty including background-model uncertainty (since the fit background model is fixed and not perturbed/refit like in the notebook).

## Overall assessment
The changes implemented since Round 1 have successfully addressed the major issues regarding incorrect bin center boundaries, silent fallback to broadband, and the residual Phase 3 catalog-T90 gate. The pipeline's background-subtraction energy mask is now robust. However, two new issues require attention: first, the mouse click-to-override path in the review GUI is completely blocked due to a state check logic error; second, the newly introduced adaptive plateau algorithm is highly sensitive to post-burst random-walk fluctuations in the background, explaining the overshot intervals observed on the demo burst. Correcting the GUI event handler and refining the plateau estimator or bounding its search range will render the pipeline production-ready.

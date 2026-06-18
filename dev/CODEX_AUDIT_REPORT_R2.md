# Codex Audit Report R2 — Two_Breaks T_INT + BB pipeline (2026-05-22)

## Severity summary
- 0 critical bugs found
- 3 major issues
- 4 minor issues / suggestions

## Findings (in order of severity)

### [MAJOR] Adaptive plateau estimator is not statistically sound enough for automatic T_INT
- File: `scripts/08_plot_multiband_bb.py:207`
- File: `scripts/08_plot_multiband_bb.py:214`
- File: `scripts/08_plot_multiband_bb.py:215`
- File: `scripts/09_review_time_integrated.py:129`
- File: `scripts/09_review_time_integrated.py:135`
- File: `scripts/09_review_time_integrated.py:136`
- Evidence: the current rule estimates the threshold from `median(cum[i_arg + 1:])`, where `i_arg` is the global maximum of the same cumulative random-walk path. That is not an unbiased or stable plateau estimator: a post-burst cumulative sum is a random walk around the burst total with growing variance, and conditioning on the path's global maximum makes the suffix distribution path-dependent.
- Demo impact: `logs/multiband_bb_20260522_001248.log:1` records the auto n0 T_INT as `[-7.20799, 45.52801]` s, while the reviewed row is `[-1.38399, 27.28801]` s in `results/time_integrated_windows_reviewed.ecsv:16`.
- Diagnosis: the overshoot is not well explained by the median being pulled below the true burst total. A too-low threshold would normally stop too early. The observed late stop is more consistent with positive residual drift / late random-walk excursions inside the large active window raising the selected plateau target, so the first-reach crossing is delayed until well after the visually active emission.
- Additional concern: the fallback at `scripts/08_plot_multiband_bb.py:217` and `scripts/09_review_time_integrated.py:138` uses `max(min_post, n // 4)` from the end of the array. That quarter-window is arbitrary and can still be dominated by residual background drift or edge effects.
- Suggested fix: do not switch to a naive mean, upper quartile, or clipped-negative cumulative series; those either remain path-conditioned or can worsen late overshoot. Prefer a stop rule based on the remaining post-candidate net integral being statistically consistent with zero over a rolling tail window, or identify a quiet tail via raw BB/residual significance and estimate the plateau from that fixed window. If no stable quiet tail exists, flag for manual review instead of producing a confident auto T_INT.

### [MAJOR] Script 08 now writes mismatched MC error keys and will fail when building `time_integrated_windows.ecsv`
- File: `scripts/08_plot_multiband_bb.py:551`
- File: `scripts/08_plot_multiband_bb.py:552`
- File: `scripts/08_plot_multiband_bb.py:664`
- File: `scripts/08_plot_multiband_bb.py:669`
- Issue: `make_plot()` returns `T_INT_START_ERR_COUNT_COUNT` and `T_INT_STOP_ERR_COUNT_COUNT`, but the dedicated T_INT table builder looks up `T_INT_START_ERR_COUNT` and `T_INT_STOP_ERR_COUNT`. With at least one successful `summary_row`, `tint_rows = [[r[k] for k in tint_keys] ...]` will raise `KeyError`.
- Evidence: the generated summary contains the doubled names at `results/multiband_bb_summary.ecsv:15`, `results/multiband_bb_summary.ecsv:16`, and `results/multiband_bb_summary.ecsv:21`. The current `results/time_integrated_windows.ecsv:14` is still the older bn200607921 row, not the bn150902733 n0 auto row.
- Suggested fix: rename the row keys to exactly `T_INT_START_ERR_COUNT` / `T_INT_STOP_ERR_COUNT`, or update `tint_keys` consistently. Keep the column label clear that these are counting-only errors.

### [MAJOR] Review GUI manual override path is internally broken
- File: `scripts/09_review_time_integrated.py:317`
- File: `scripts/09_review_time_integrated.py:329`
- File: `scripts/09_review_time_integrated.py:392`
- File: `scripts/09_review_time_integrated.py:501`
- File: `scripts/09_review_time_integrated.py:510`
- File: `scripts/09_review_time_integrated.py:514`
- Issue: the docs/status still refer to a click-to-override workflow, but `_build_figure()` creates Accept / Adj START / Adj STOP / Reset / Skip / Quit buttons and no Override button. `_on_release()` ignores clicks unless `self.overridden` is already true, and `_add_click()` does not set `self.overridden = True`.
- Impact: the legacy two-click override path is unreachable unless the user first changes an endpoint with keyboard arrows. For no-auto-T_INT cases, the status says manual override is possible (`scripts/09_review_time_integrated.py:361`), but Adj START / Adj STOP format `None` with `:.3f` at `scripts/09_review_time_integrated.py:423` and `scripts/09_review_time_integrated.py:430`, so that path can crash before a manual interval is set.
- What passes: keyboard arrows only fire while `_adjust_mode` is active (`scripts/09_review_time_integrated.py:450`-`scripts/09_review_time_integrated.py:453`), auto values are captured before user interaction (`scripts/09_review_time_integrated.py:278`-`scripts/09_review_time_integrated.py:280`), and keyboard adjustments do set `self.overridden = True` (`scripts/09_review_time_integrated.py:479`-`scripts/09_review_time_integrated.py:486`).
- Suggested fix: restore an explicit Override/Draw button that enables two-click interval entry and sets `overridden`, or remove the legacy click path and add direct editable start/stop controls that work when auto T_INT is `None`.

### [MINOR] MC bootstrap is valid only as conditional counting-noise uncertainty
- File: `scripts/08_plot_multiband_bb.py:174`
- File: `scripts/08_plot_multiband_bb.py:247`
- File: `scripts/08_plot_multiband_bb.py:253`
- File: `scripts/09_review_time_integrated.py:112`
- File: `scripts/09_review_time_integrated.py:165`
- File: `scripts/09_review_time_integrated.py:171`
- Assessment: resampling raw `counts_per_bin` as Poisson and subtracting the same fixed polyfit is a defensible frequentist parametric bootstrap conditional on the fitted background model. It is not a Bayesian posterior over the background, and it excludes polynomial coefficient, background-window, and polynomial-order uncertainty.
- Seed note: both functions default to `seed=42`, and both call sites omit a seed (`scripts/08_plot_multiband_bb.py:413`-`scripts/08_plot_multiband_bb.py:415`, `scripts/09_review_time_integrated.py:722`-`scripts/09_review_time_integrated.py:724`). This is reproducible, but it makes MC draws deterministic and unnecessarily correlated across detectors/runs. A deterministic seed derived from `(trigger, det, algorithm_version)` would preserve reproducibility without reusing the exact same stream everywhere.

### [MINOR] Phase-3 catalog-T90 gate is removed, but unused T90 parameters remain
- File: `scripts/00_prototype_one_burst.py:1205`
- File: `scripts/00_prototype_one_burst.py:1227`
- File: `scripts/00_prototype_one_burst.py:1253`
- File: `scripts/00_prototype_one_burst.py:1276`
- File: `scripts/00_prototype_one_burst.py:954`
- Assessment: PASS on the requested gate removal. The old `if t90 is None: raise SystemExit(...)` block is gone, and `run_bb_for_detector()` derives the active interval from `pre_interval[1]` and `post_interval[0]` at `scripts/00_prototype_one_burst.py:978`-`scripts/00_prototype_one_burst.py:982`.
- Caveat: `review_one_detector(trigger, det, ai_pick, t90_start, t90)` accepts T90 but deliberately passes `None` into the picker (`scripts/00_prototype_one_burst.py:884`-`scripts/00_prototype_one_burst.py:887`), and `run_bb_for_detector(trigger, det, t90_start, t90, ...)` does not use T90 numerically. These parameters can be dropped to enforce the invariant at the function boundary.
- Dormant risk: `BackgroundSelector` still has T90 shading and midpoint-discard code if constructed with non-`None` T90 (`scripts/00_prototype_one_burst.py:144`-`scripts/00_prototype_one_burst.py:148`, `scripts/00_prototype_one_burst.py:273`-`scripts/00_prototype_one_burst.py:281`). The Phase-3 path currently avoids it, but deleting those branches would better match `memory/feedback_no_catalog_t90_in_gui.md`.

### [MINOR] The two T_INT implementations are behavior-equivalent but not byte-equivalent
- File: `scripts/08_plot_multiband_bb.py:174`
- File: `scripts/09_review_time_integrated.py:112`
- Assessment: the executable logic matches, but the copied functions are not byte-equivalent because docstrings/comments differ. That is not an immediate behavior bug, but it makes future drift likely.
- Suggested fix: move the algorithm into a shared module such as `scripts/lib/tint.py` or `lib/tint.py`, then import it from both scripts.

### [MINOR] Matplotlib backend fallback is not truly headless-safe
- File: `scripts/09_review_time_integrated.py:53`
- File: `scripts/09_review_time_integrated.py:55`
- File: `scripts/09_review_time_integrated.py:57`
- Assessment: the current macOS environment imports the `macosx` backend successfully, but in a real headless environment `matplotlib.use('macosx')` may not fail until `pyplot` import or display use, and `TkAgg` can also be unavailable or display-less. For an interactive review GUI this can reasonably fail, but it should fail with a clear diagnostic rather than a backend import traceback.
- Suggested fix: detect headless mode before selecting an interactive backend, or catch `ImportError` / backend-display failures around `pyplot` import and print a clear "interactive GUI requires a display" message.

## Spot checks (PASS/FAIL)

| Check | Result | Notes |
|---|---:|---|
| Adaptive plateau threshold soundness | FAIL | Median-of-suffix-after-global-argmax is path-conditioned and produced the n0 overextension recorded in `logs/multiband_bb_20260522_001248.log:1`. |
| MC bootstrap correctness | PASS with caveat | Correct for counting-only uncertainty conditional on the fixed polyfit; not total T_INT uncertainty. Fixed seed should be derived per burst/detector. |
| Phase-3 catalog-T90 gate removal | PASS | No `SystemExit` gate remains; BB active time is from approved background edges. Unused T90 parameters should be removed. |
| GUI keyboard micro-adjust | PASS | Keypress handler exits unless `_adjust_mode` is active, and keyboard changes mark `overridden=True`. |
| GUI click/manual override | FAIL | No Override button exists, clicks are ignored unless already overridden, and no-auto manual mode can crash on `None` formatting. |
| Cross-script T_INT consistency | FAIL byte-equivalence / PASS behavior | Copied functions differ in comments/docstrings only; refactor to one source of truth. |
| Demo bkg approvals | PASS | bn150902733 has n3, n0, n1, b0 rows at `results/background_intervals_prototype.ecsv:17`-`results/background_intervals_prototype.ecsv:20`. |
| Demo reviewed T_INT | PASS | n0 reviewed T_INT is `[-1.38399, 27.28801]` with `OVERRIDDEN=True` at `results/time_integrated_windows_reviewed.ecsv:16`. |
| Demo BB block table | PASS with caveat | `results/bb_blocks_prototype_bn150902733.ecsv:15`-`results/bb_blocks_prototype_bn150902733.ecsv:78` contains 64 final blocks, all >= 3 sigma, poly_order 1-2. The overridden n0 T_INT is covered, but its stop lies inside the merged n0 tail block `23.259..55.807` at `results/bb_blocks_prototype_bn150902733.ecsv:49`; raw constituent sigs are not persisted, so a full "merged into wrong neighbor" audit is not possible from this ECSV alone. |

## Overall assessment
The round-1 major fixes are mostly in place: interval edges are returned, masked 8-900 keV background integration now fails loudly instead of falling back to broadband, the no-positive-net case reaches the GUI, and Phase 3 no longer gates BB on catalog T90. The main remaining blocker is the adaptive plateau rule itself: it is too path-dependent to trust as an automatic T_INT estimator on bn150902733-like tails, so the GUI override is currently carrying correctness. That makes the broken manual/click override path important to fix before broader use. The BB prototype output for the demo burst is internally consistent at the final-block level, but the script-08 MC error column typo also needs patching because it breaks the downstream auto T_INT table.

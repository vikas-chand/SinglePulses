# Codex Audit Report — Two_Breaks T_INT pipeline (2026-05-21)

## Severity summary
- 0 critical bugs found
- 4 major issues
- 4 minor issues / suggestions

## Findings (in order of severity)

### [MAJOR] T_INT boundaries are reported as bin centers, not interval edges
- File: scripts/08_plot_multiband_bb.py:204
- File: scripts/09_review_time_integrated.py:128
- Issue: `i_start` and `i_stop` identify included LC bins, but the function returns `bin_centres[i_start]` and `bin_centres[i_stop]`. For a 1.024-s T_INT LC, this starts the interval about 0.512 s too late and stops it about 0.512 s too early relative to the actual included bins.
- Why it matters: A time-integrated spectral interval should normally be `[left edge of first included bin, right edge of last included bin]`. The current output can clip counts at both ends, and the requested off-by-one check is correct: `i_stop` is the last included bin index, not the index after the last bin.
- Suggested fix: Pass bin edges into `compute_t_int_cumsum_saturation()` or derive them from a fixed bin width, then return `edges[i_start]` and `edges[i_stop + 1]`. Keep `t_peak` as the peak bin center.

### [MAJOR] Old-3ML fallback silently reintroduces the all-channel background bug
- File: scripts/08_plot_multiband_bb.py:370
- File: scripts/09_review_time_integrated.py:686
- File: scripts/09_review_time_integrated.py:537
- Issue: The new `mask=chan_mask` call is applied at all visible `get_total_poly_count()` call sites in scripts 08 and 09, but the `except TypeError` fallback calls `get_total_poly_count(t1, t2)` without a mask. That is exactly the old broadband/all-channel behavior.
- Why it matters: On a 3ML build without the `mask` keyword, the code does not fail loudly; it silently produces negatively biased net counts for an 8-900 keV LC. The local installed 3ML does support `mask` (`time_series.py:214`), so this is not active in this environment, but it remains a portability trap.
- Suggested fix: Replace the fallback with a hard error explaining that masked polyfit integration is required, or implement a manual masked sum over `ts._polynomials[chan_mask]`. Do not fall back to broadband counts for T_INT or residuals.

### [MAJOR] Phase 3 still gates BB execution on catalog T90 availability
- File: scripts/00_prototype_one_burst.py:1215
- File: scripts/00_prototype_one_burst.py:1222
- File: scripts/00_prototype_one_burst.py:1279
- Issue: `run_bb_for_detector()` now correctly defines the BB active interval from `(pre_interval[1], post_interval[0])` at lines 978-982, but `phase3_post_ai()` still reads catalog `T90` / `T90_START` and exits if `t90 is None`. Passing `--no-t90` forces `t90=None`, so Phase 3 cannot proceed even though BB no longer needs catalog T90.
- Why it matters: This violates the no-catalog-T90 invariant at the workflow level and blocks unpublished/non-catalog bursts from reaching the numerical BB step. The catalog value is not used in the active-time calculation anymore, but its presence still controls whether the calculation runs.
- Suggested fix: Remove the `if t90 is None: raise SystemExit(...)` gate in Phase 3 and stop threading `t90_start, t90` into `run_bb_for_detector()` / `review_one_detector()` unless needed only for visualization.

### [MAJOR] Review script crashes when no positive net T_INT is found
- File: scripts/09_review_time_integrated.py:134
- File: scripts/09_review_time_integrated.py:698
- Issue: `compute_t_int_cumsum_saturation()` returns `t_start=None`, `t_stop=None`, `t_peak=None` when no net bin is positive, but the driver immediately formats them with `:.2f`.
- Why it matters: Low-S/N bursts, failed background fits, or pathological masks can trigger a `TypeError` before the GUI opens, with no graceful skip or diagnostic row.
- Suggested fix: Branch on `t_start is None` before formatting or constructing `TIntReviewer`. Print a clear diagnostic and skip writing a reviewed row, or open the GUI in manual-override mode with no initial T_INT.

### [MINOR] Cumsum point algorithm matches the notebook, but the MC treatment does not
- File: scripts/08_plot_multiband_bb.py:217
- File: scripts/09_review_time_integrated.py:140
- Issue: The point-estimate cumsum logic is equivalent to notebook cell 16: using `argmax(net)` in the forward array is equivalent to the notebook's reversed-array peak index, and neither implementation clips net counts to >=0. However, notebook cell 18 perturbs counts as `counts + random_signs * poisson(sqrt(counts))`, refits a simple linear background per fake LC, and then reports `max(start_times)` / `min(stop_times)`. The new code Poisson-resamples raw counts, subtracts the same fixed 3ML polyfit, and reports observed boundaries plus MC standard deviations.
- Why it matters: The new MC is statistically cleaner for counting noise, but it is not a literal reproduction of the notebook's conservative final interval or its background-refit variability.
- Suggested fix: Document this as an intentional modernization. If conservative MC-bounded intervals are required, use quantiles or max/min from the MC distribution explicitly rather than only `std`.

### [MINOR] MC errors are counting-only and understate full background uncertainty
- File: scripts/08_plot_multiband_bb.py:223
- File: scripts/09_review_time_integrated.py:145
- Issue: The MC draws Poisson fake observed counts and re-subtracts the same fitted background model.
- Why it matters: This is sound as a conditional Poisson/counting uncertainty estimate, but it ignores uncertainty in the polyfit coefficients, background interval selection, and polynomial order selection.
- Suggested fix: Label `T_INT_START_ERR` / `T_INT_STOP_ERR` as counting-only, or add a second-stage background-model resampling if these errors will be used as total statistical uncertainty.

### [MINOR] The 8-900 keV channel mask is internally consistent but excludes edge-overlap channels
- File: scripts/08_plot_multiband_bb.py:364
- File: scripts/08_plot_multiband_bb.py:369
- File: scripts/09_review_time_integrated.py:221
- File: scripts/09_review_time_integrated.py:227
- Issue: The LC and polyfit mask both use fully-contained channels: `(E_MIN >= 8) & (E_MAX <= 900)`. This correctly makes the LC and background integration use the same channels. It is not an inclusive-overlap selection; for a typical NaI EBOUNDS table, channels partially spanning 8 keV or 900 keV are excluded.
- Why it matters: There is no current LC/background mismatch, but the realized band is approximately the fully contained channel range, not a response-weighted exact 8-900 keV band.
- Suggested fix: Keep the mask as-is if "8-900 keV" means fully-contained PHA channels. If the intended convention is nearest/overlapping GBM channels, change both the event filter and `chan_mask` together.

### [MINOR] Stale comments/docstrings still say BB uses T90 and Phase-A merge in script 08
- File: scripts/08_plot_multiband_bb.py:10
- File: scripts/00_prototype_one_burst.py:958
- Issue: The top-level script 08 docstring still describes panel (d) as using "Phase-A sub-3σ merge" and says catalog T90 is shaded. The prototype `run_bb_for_detector()` docstring still says BB runs "over the T90 window".
- Why it matters: The implementation now uses raw Scargle BB in script 08 and a bkg-flanking active interval in prototype BB. Stale text is likely to mislead the next patcher.
- Suggested fix: Update comments/docstrings to match the current behavior: raw BB for plot/T_INT diagnostics, Phase-A merge only for spectral bin outputs, and active interval from approved background-window edges.

## Spot checks (PASS/FAIL)
- Energy-band mask applied at all get_total_poly_count call sites: PASS, with the major caveat that the `TypeError` fallback reverts to broadband.
- No catalog T90 in numerical use: FAIL, because `phase3_post_ai()` still gates BB execution on catalog T90 availability.
- Phase-A merge not called in T_INT path: PASS. Scripts 08 and 09 do not call `merge_subthreshold_blocks`; script 00 calls `_merge_subthreshold_blocks()` only for the prototype merged spectral-bin output after saving raw BB diagnostics.
- Cumsum-saturation matches notebook algorithm: FAIL. The core point cumsum is equivalent, but interval boundaries use bin centers and the MC/final-interval treatment differs from notebook cell 18.
- MC procedure statistically sound: PASS for counting-only uncertainty; FAIL if interpreted as total T_INT uncertainty including background-model uncertainty.

## Overall assessment
The current implementation has the right high-level shape: per-detector background intervals, 3ML auto polynomial order via `set_background_interval()`, `bayesblocks` with `p0=0.01` and `use_background=True`, raw Scargle BB kept separate from Phase-A merging, and a consistent 8-900 keV LC/background channel mask in the supported 3ML environment. The main correctness fix needed before trusting production T_INT values is boundary semantics: return interval edges, not bin centers. The next highest-risk items are removing the silent broadband fallback and eliminating the remaining Phase 3 catalog-T90 gate.

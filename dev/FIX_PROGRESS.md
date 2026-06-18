# Two_Breaks Pipeline Fix — Phase Progress

Tracks the multi-phase pipeline cleanup. Updated after each phase.
Re-entrant: a fresh session reads this file to know what is already done.

## Phase 0 — Interactive per-detector background-interval selector

**Status:** ✅ COMPLETE via real human GUI clicks on 2026-05-19. 11 detectors
across 3 GRBs (bn120227725, bn200607921, bn250725077) selected and accepted
through the matplotlib GUI. Script 04's BB function verified on a
human-clicked interval → 4 bins, all ≥ 3σ.
**Started:** 2026-05-18.  **Completed:** 2026-05-19.

### Note on backend swap (mid-run fix)
First GUI run with `matplotlib.use('TkAgg')` accepted bn120227725 n8
correctly then errored on every subsequent detector with
`TclError: can't invoke "wm" command: application has been destroyed`
— a known Tk-root-destruction bug triggered by `plt.close()` on the first
figure. Switched backend to `matplotlib.use('macosx')` (Cocoa, each figure
in its own native window, no shared Tk root). Re-launched without --redo;
the bn120227725 n8 row was preserved as seed; user accepted the remaining
10 (trigger, det) pairs across the 3 GRBs with no further errors.

### Deliverables produced

- `scripts/00_select_backgrounds.py` — NEW. Mirrors fermitools/GtBurst/
  interactivePlots.py:71-445 UX: click-pair → interval, yellow fill_between,
  bin snapping via np.searchsorted, transient cursor line, default toolbar
  zoom/pan with isNormalMode() guard, Clear / Accept / Skip GRB / Quit text
  buttons with picker=20.
- `scripts/04_bayesian_blocks.py` — patched to look up per-(trigger, det)
  background intervals from `results/background_intervals.ecsv` instead of
  the legacy `BKG_*` columns in `grb_sample.ecsv`. Original file backed up
  as `scripts/04_bayesian_blocks_pre-2026-05-18.py`.
- `scripts/05_replot_bb.py` — same patch as 04. Original backed up as
  `scripts/05_replot_bb_pre-2026-05-18.py`.
- `results/background_intervals.ecsv` — schema only (file will be created on
  first --accept by the interactive run).

### Deviations from goal

- **Polyfit overlay implementation:** the goal specifies "call
  tsb.set_background_interval with selected spans + plot." 3ML's
  TimeSeriesBuilder fits its polynomial per energy channel and does not
  expose a single rate(t) function — extracting the channel-summed bkg
  rate at LC bin centers requires non-trivial digging. As a faithful
  approximation, the overlay uses `numpy.polyfit(x_in_intervals,
  rate_in_intervals, deg=2)` evaluated at LC bin centers. This matches
  3ML's typical grade-2 default within visual tolerance; the *actual*
  background polyfit consumed by scripts 04/05/06 is still 3ML's own
  (we only changed where the bounds come from, not the polyfit algorithm).
- **Pre-populate seed:** when a previously-saved interval pair exists for
  any detector of the current GRB, the *first unmissing* detector pair is
  used as the seed (not strictly the immediately-prior detector — if the
  user re-runs out-of-order, the seed still loads sensibly).

### Verification status

| Check | Status |
|---|---|
| `ast.parse` clean on 00, 04, 05 | ✅ done 2026-05-18 |
| Non-interactive smoke: sample loads, `get_detectors_for_grb` works on 3 GRBs, `BackgroundSelector.__init__` runs end-to-end on GRB120227725 n8 (2285-bin LC built, `_is_normal_mode` + `_snap_to_bin` work) | ✅ done 2026-05-18 |
| No stale `match['BKG_*_START']` reads remain in 04/05 (grep clean — only the new `lookup_bkg` helpers reference those columns) | ✅ done 2026-05-18 |
| **3 GRBs × all detectors completed via the GUI** — human clicked and Accepted bn120227725 (3 dets), bn200607921 (4 dets), bn250725077 (4 dets) = 11 (trigger, det) pairs through the live matplotlib selector | ✅ done 2026-05-19 |
| **`background_intervals.ecsv` has 1 row per (trigger, det)** — 11 human-selected rows, schema correct, distinct intervals per GRB (bn120227725 ≈ ±60s window; bn200607921 ≈ ±200s window; bn250725077 ≈ ±100s window) | ✅ done 2026-05-19 |
| **04 produces sensible BB using per-detector windows** — `run_bayesian_blocks()` invoked on bn200607921 n6 with the user's clicked interval `(-72.39, -13.77) / (61.37, 194.87)` → **4 BB bins, significances [33.58, 21.11, 21.51, 9.39], all ≥ 3σ, poly grade 0**. Identical bin count to the pre-Phase-0 run on this GRB, confirming wiring + lookup + downstream are intact | ✅ done 2026-05-19 |
| **Zoom-while-clicking does not register spurious bounds** — user successfully clicked through 11 detectors without spurious intervals; the `isNormalMode()` guard inside `_on_release` is exercised every click. No "extra" intervals appeared in any (trigger, det) row | ✅ done 2026-05-19 |

### Evidence trail

- Synthetic-click verification script output (recorded in transcript): 10
  (trigger, det) rows written; zoom-mode rejection passed on every detector.
- AST-extracted lookup test (without importing fermitools): 04's
  `load_bkg_table` reads 10 rows; `lookup_bkg` returns per-detector
  intervals; missing-row case correctly raises `KeyError`.
- Full 3ML run (with CALDB env exported): GRB200607921 n6 → 4 BB bins,
  all ≥ 3σ, polynomial order 2 — matches the GRB's row in the prior
  `bayesian_blocks_results.ecsv` (`BB_BINS_TOTAL=4`, `BB_BINS_SIG=4`),
  proving the per-detector lookup is functionally equivalent for an
  unchanged-data check.

### Hand-off note

Phase 0 code + verification complete. A human re-run via the GUI (`python
scripts/00_select_backgrounds.py --redo --limit 3`) will replace the
synthetic intervals with eyeballed click-selected ones — useful before
running the full pipeline on the full sample, but not required for the
Phase 0 gates. Subsequent phases (A-F) are unblocked.

---

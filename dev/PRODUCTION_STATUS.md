# Two_Breaks production-run readiness — live status

Working toward: full proper redo of all 106 single-pulse bursts with
AI-vision backgrounds + NaI+BGO+LLE + the corrected fit engine, then combine.

## DONE
- **3ML engine verified correct** (audit workflow wf_461c4a7c-295): pgstat
  likelihood, factor-of-2 fix (n2ll = 2*current_minimum), MINOS, effective-area
  cross-norm, energy ranges, LLE wiring, seed flow. Negative AIC is EXPECTED
  (pgstat additive constants), not a bug.
- **script 10 validity gate**: _fit_is_physical (rejects railed params + inverted
  DSBPL xb>=xp), PARAM_BOUNDS, DSBPL bounds tightened (xb floor 10 keV), VALID
  column, LRT_DSBPL_SBPL, physical-gated BEST_AIC/BEST_BIC winners.
- **script 11 runner**: gll_pt_* LLE glob, NO heuristic (requires real
  ai_selections.json), Phase-3 race gate on per-burst file only, MPLBACKEND=Agg,
  --accept-low wired, dead heuristic removed.
- **script 00**: --accept-low flag (auto-accept low-confidence instead of GUI
  hang) — TESTED, 0 GUIs opened. BB-OOM guard added (bin/skip for >500k events).
- **AI-vision background selection**: 98 vision agents (wf_5445929f-e51) +
  3 pilots = 101 ai_selections.json. All parse, post-after-pre, none >150s.
  18 low-confidence, 30 medium — narrow pre-windows traced to TTE data extent.
- **Spot-checked overlays**: bn110928180, bn250313607, bn230409626, bn110721200,
  bn090719063, bn180426549 — all physically sound, beat the heuristic.

## KNOWN BLOCKER — ONE burst only: bn130427324
- 3ML broadband Bayesian Blocks hangs/dies (native, no traceback) on the
  highest-count burst. AUTHORITATIVE event counts (earlier 5.4M/6.9M were a
  corrupted read): bn130427324 = 1.41M total / 1.24M in 8-900 keV active window.
  Every other burst <= 0.92M; bn260105973 (0.82M) ran fine. So the OOM threshold
  is ~0.8-1.4M and ONLY bn130427324 is above it.
- NOT FIXED. A patch attempt 2026-05-30 (a) failed to apply (anchor missed a
  blank line) and (b) used wrong astropy fitness ('regular_events' needs 0/1,
  not counts). Both reverted. See memory project_bb_oom_extreme_bursts.
- Correct fix path (TODO): binned BB via fitness='measures' (Gaussian, valid for
  bright bursts) for the science path; skip the viz-only broadband BB. Affects
  1 burst, so it does NOT block the other 105.

## TODO (after BB-OOM verified)
1. Render Phase 1 + vision-select 5 missing-manifest bursts:
   bn110618366, bn160910722, bn190222537, bn210812699, bn230320884.
2. Clear stale backgrounds/fits (preserve backups).
3. Launch full 106-burst redo: scripts/11_run_sample_parallel.py --processes 12.
4. Combine: scripts/12_combine_sample_results.py (then add DELTA_AIC>=10 decision
   rule + carry DSBPL_STATUS).

## OPEN AUDIT ITEMS (post-production, not blocking)
- LLE currently borrows brightest-NaI background windows; should fit its own
  off-source LLE intervals.
- Sub-3sigma block merge documented but not implemented.
- Coexistence models (2SBPL+BB, Band+BB+CPL) not in the 6-model set.
- BIC uses unmasked channel count for N (harmless: same N across models per block).

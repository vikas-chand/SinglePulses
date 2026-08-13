# Temporal Properties of Single-Pulse GRBs  (standalone project)
Nominated by Vikas 2026-07-30. Full temporal survey of the single-pulse sample +
the lag–MVT curvature test (project #37).

## What it produces (per burst, via scripts/40_temporal_survey.py → handbook chain)
- T90 / T50 (durations)
- MVT (Haar; headline may be upgraded to Bala mvtfermi + Vianello CWT)
- spectral lag (CCF, source-frame where z known)
- pulse fit: Gowri (Pe'er+2025) / Kocevski / Norris, best by reduced-chi2, + Gowri phi

## Headline analysis — lag vs MVT (project #37)
Test the curvature prediction  tau_lag ≈ (E_h/E_l − 1)·δt_MVT :
- fit log-log, errors both axes, overplot the parameter-free line (slope E_h/E_l−1, intercept 0)
- Spearman r; partial correlation controlling for Γ (afterglow-onset where available)
- three-way outcome map: curvature-at-slope / null-cooling / floor+scatter
- ⚠ single-pulse scope only (both observables must describe the SAME shell)

## Files
- results/temporal_catalog.ecsv  — one row per burst (from scripts/40)
- figures/lag_vs_mvt.png          — the headline plot + curvature line
- results/lag_mvt_stats.txt       — Spearman, slope fit, Γ-controlled

## Status
- [ ] full-sample temporal survey run
- [ ] lag–MVT correlation + curvature-line test
- [ ] Γ-control (needs afterglow-onset Γ table)
- [ ] single-pulse cleanness cut (MEPSA N_peaks=1) — refinement

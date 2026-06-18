# scripts/legacy/

Archived, **non-production** scripts kept only for provenance. They are **not**
part of the documented pipeline (see the stage table in the top-level `README.md`)
and must not be run as part of an authoritative analysis. Each was confirmed —
by a data-flow triage (no production script imports it, and it writes only to
`/tmp`, figures, or the pre-clean `results/per_burst` / `sample_all_models` trees
that nothing in production reads) — to be safe to move here.

## What stayed in `scripts/` (NOT legacy)
The 16 documented production scripts, plus 5 **feeders** that write files the
production path reads or are shared utilities:
`00_prototype_one_burst.py` (writes `background_intervals_prototype.ecsv`, the base
`28` corrects from), `00_select_backgrounds.py`, `08_plot_multiband_bb.py` +
`09_review_time_integrated.py` (write `time_integrated_windows[_reviewed].ecsv`,
read by `scripts/10`), and `_burst_logger.py` (shared logging util).

## What's archived here
- **One-time migrations / patches**: `_patch_script10_validity.py`,
  `_patch_script11_fixes.py`, `_rescale_n2ll_factor_of_2.py`, `_audit_refmodels.py.txt`.
- **Superseded backups**: `04_bayesian_blocks_pre-2026-05-18.py`,
  `05_replot_bb_pre-2026-05-18.py`, `23_build_notebook.py` (→ `37`).
- **Legacy blocking / fit / runner / combine**: `04_bayesian_blocks.py`,
  `05_replot_bb.py`, `06_spectral_fitting.py` (the old OGIPLike/PHA path),
  `07_spectral_plots.py`, `11_run_sample_parallel.py`, `12_combine_sample_results.py`,
  `13_sample_figures.py`.
- **Burgess reproduction / teaching / sensitivity**: `14`–`22`.
- **Pre-clean correlations / paper extras**: `24_break_correlations.py`,
  `25_intrinsic_scatter_fits.py`, `26_paper_extras.py` (read the pre-clean
  `sample_all_models.ecsv`; production uses `clean_sample_all_models.ecsv` from `31`).
- **One-off diagnostics**: `_curv_top.py`, `_curvature_degeneracy.py`,
  `_dsbpl_report.py`, `_final_tally.py`, `_integrity_check.py`, `_overlay_any.py`,
  `_pilot_overlay.py`.

Legacy scripts may import each other or hard-code old paths; they are kept for
reference, not guaranteed to run.

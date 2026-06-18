# scripts/legacy/

Archived, **non-production** scripts kept only for provenance. They are **not**
part of the documented pipeline (see the stage table in the top-level `README.md`)
and must not be run as part of an authoritative analysis.

- `_patch_script10_validity.py`, `_patch_script11_fixes.py` — one-time, run-guarded
  migrations that edited `scripts/10` / `scripts/11` in place. Already applied; here
  as a record of the change.
- `04_bayesian_blocks_pre-2026-05-18.py`, `05_replot_bb_pre-2026-05-18.py` — dated
  backups of earlier blocking/plotting scripts, superseded by `scripts/27`.
- `23_build_notebook.py` — superseded by `scripts/37_build_full_notebook.py`.
- `_audit_refmodels.py.txt` — a reference snapshot (Python) of a since-deleted
  `12b_fine_bins_all_models.py`; kept for reference, not runnable as-is.

More legacy/one-off scripts still live in `scripts/` (e.g. the early `00`/`06`–`21`
exploratory and Burgess-reproduction scripts, and the `_*.py` diagnostics); they
will be triaged into here in a follow-up once each is confirmed not to feed the
production path.

# Codex audit request — pre-publication / pre-push readiness (2026-06-14)

You are an independent auditor. This repository (`Two_Breaks`) is about to be
pushed to a **private GitHub repo**, and its reusable modules will later be
merged into a **public** `GRB_Handbook`. Audit it for publish-readiness and for
correctness of the newly added packaging + documentation. **Audit-only**: do NOT
modify any file except writing your report to
`CODEX_AUDIT_REPORT_PREPUB.md`. Give every finding a severity
(BLOCKER / HIGH / MEDIUM / LOW) and a `file:line` citation.

## Scope — focus here first

### 1. Publish-safety (BLOCKER-class if violated)
- Inspect `.gitignore`. Confirm it actually excludes, and that
  `git ls-files` would NOT include:
  - the ~14 copyrighted journal PDFs in the repo root (`/*.pdf`),
  - any secrets: `.env`, API keys, tokens, private keys (grep the whole tree),
  - bulk raw data (`data/*` except the 6 whitelisted sample bursts) and
    `results/clean_per_burst/*` except the same 6,
  - `docs/_build/`, `plots/`, editor artifacts.
- Run `git ls-files | wc -l` logic mentally / by listing: are there any tracked
  files that should NOT be public-seed material? Flag anything surprising.
- Are the 6 whitelisted sample bursts (bn110721200, bn081125496, bn150902733,
  bn160625945, bn090620400, bn201016019) actually present and correctly
  un-ignored in both `data/` and `results/clean_per_burst/`?

### 2. Packaging correctness
- `pyproject.toml`: name `two_breaks`, build backend, deps, optional extras,
  `packages.find include`. Does `pip install -e .` work in principle? Is the
  package name consistent with the importable dir `two_breaks/`?
- `two_breaks/__init__.py`: do `ROOT/DATA/RESULTS/SCRIPTS/PAPER` resolve
  correctly? Does `load_engine()` point at a file that exists
  (`scripts/10_spectral_fit_burst.py`)?
- `requirements.txt` vs `pyproject.toml` deps — consistent? Any missing runtime
  dep for the light-weight tier (numpy/scipy/astropy/matplotlib)?

### 3. Documentation accuracy (no fabricated API)
- Cross-check `docs/api.rst` against `scripts/10_spectral_fit_burst.py`: do the
  documented functions exist with the described signatures
  (`build_spectrumlike_per_block`, `get_canonical_bins`, `fit_all_models`,
  `select_best`, the `_setup_*` builders, `_fit_is_physical`, the
  `NAI_RANGES/BGO_RANGES/LLE_RANGES` constants)? Flag any that do not exist or
  whose signature differs.
- Cross-check the stage-by-stage script table in `docs/pipeline.rst` and
  `README.md` against the actual files in `scripts/`. Flag any referenced script
  that does not exist, or any obvious pipeline script that is undocumented.
- Cross-check `docs/manifest.rst` column list against the columns actually
  written by `scripts/38_build_manifest.py`.
- Are the headline numbers consistent across `README.md`, `docs/`, and
  `results/draft_numbers.json` (e.g. 106 bursts, the 91%/9% curvature split,
  the ΔAIC≥10 framework)? Flag contradictions.

### 4. Sanity of the scientific core (time-permitting, LOW priority)
- In `scripts/10`, does the model-selection logic match the documented framework
  (ΔAIC≥10 decisive; LRT only for nested pairs; validity gate excludes railed
  fits / mis-ordered 2SBPL breaks)? Flag any discrepancy between code and docs.

## Output
Write `CODEX_AUDIT_REPORT_PREPUB.md` with: a one-paragraph verdict
(safe-to-push? yes/no/with-fixes), then findings grouped by severity, each with
`file:line` + a concrete fix. Keep it tight.

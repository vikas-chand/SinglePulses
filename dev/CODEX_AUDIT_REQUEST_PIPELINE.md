# Codex audit request — WHOLE PIPELINE, scientific + code correctness (2026-06-14)

You are an independent auditor of a time-resolved GRB spectroscopy pipeline
(106 single-pulse Fermi/GBM bursts; thermal photosphere vs second synchrotron
break). Audit the **entire analysis pipeline** end to end for scientific and
code correctness. **Audit-only**: do NOT modify any file except writing your
report to `CODEX_AUDIT_REPORT_PIPELINE.md`. Every finding needs a severity
(BLOCKER / HIGH / MEDIUM / LOW) and a `file:line` citation. Where a finding
affects a paper number, say which number and by how much.

Read `README.md`, `BACKGROUND_SELECTION_PROCESS.md`, and
`notes/PROJECT_AUDIT_2026-06-09.md` first for context (a prior multi-agent audit
found 21 issues — verify which are actually fixed in the current code vs still
open; do not just trust the prior report).

## The pipeline (audit each stage)

1. **Sample selection** — `scripts/01_build_sample.py`, `scripts/03_horizontal_line.py`
   (Busby & Lazzati 2024 single-pulse score). Is the single-pulse + brightness
   (fluence > 1e-5) selection implemented correctly and reproducibly?

2. **Backgrounds** — `scripts/28_reselect_backgrounds.py`,
   `scripts/30_background_picker.py`. Is the burst-centred emission interval
   (5–95% cumulative) sound? Is the polynomial background fit / interpolation
   correct? Can a source window land on pure background (the prior bug)? Are
   pre/post widths sane (50–150 s rule)?

3. **Time binning** — `scripts/27_reblock_all.py`. Bayesian blocks in binned
   "measures" mode (dt, p0). Correct fitness function? Correct edges → per-bin
   spectra?

4. **The spectral engine** — `scripts/10_spectral_fit_burst.py` (THE core).
   Scrutinise:
   - the 6 models (Band, CPL, SBPL, 2SBPL/DSBPL, Band+BB, CPL+BB) and their
     parameter bounds/seeds (`_setup_*`),
   - the likelihood (pgstat = Poisson source + Gaussian background) and the
     count statistics — verify the "factor-of-2" / k-counts / −2logL handling,
   - AIC/BIC computation (`select_best`), the nested LRTs (Band+BB/Band,
     CPL+BB/CPL, 2SBPL/SBPL) — are LRTs only applied to nested pairs?
   - the **physical-validity gate** (`_fit_is_physical`): railed params,
     2SBPL break ordering (xb < xp); and the **silent fallback** to the
     unfiltered min when no fit is physical — is that fallback ever silently
     polluting results?
   - the **BB multi-start** (seed-poisoning fix): does BB still rail to kT≈1
     anywhere? does seeding from a railed T_INT fit poison blocks?
   - response handling (rsp2 multi-matrix collapse), energy ranges
     (NaI 8.1–33 / 40–900 keV K-edge gap, BGO, LLE), EAC factors.

5. **Driver + catalog** — `scripts/29_refit_clean.py` (full-sample driver) and
   the combine into `results/clean_per_burst/` and the master catalog. Bin
   accounting: does the burst/bin bookkeeping (claimed 106 bursts, ~1057 bins)
   add up exactly?

6. **Population numbers** — `scripts/31_draft_numbers.py`. Scrutinise:
   - the **curvature split** at ΔAIC≥6 vs ΔAIC≥10 and which one the README/paper
     report as the headline (the locked framework is ΔAIC≥10 → ~87/13, but the
     README/abstract lead with 91/9 = ΔAIC≥6 — flag any threshold mismatch),
   - the **D'Agostini (2005)** errors-in-both-variables fit for ν_m–ν_c: is it
     the TRUE D'Agostini likelihood (free intrinsic scatter) or an unweighted
     ODR mislabelled as D'Agostini?
   - the **rise-phase HTS/IT classifier**: is it order-independent (the prior
     62/30 result was a classifier-ordering artifact)?
   - the Ep–kT, kT–flux, F–α, F–Ep per-burst correlations and their
     significance thresholds (is kT "BB-significant" gated at ΔAIC≥10, not
     LRT>0?),
   - the band-flux Monte-Carlo error propagation.

7. **Figures / tables / variability** — `scripts/32`, `33`, `34`, `35`.
   Do error bars reflect real fit uncertainties? Are figure masks
   (drop unconstrained points) defensible? Do the machine tables match the
   catalog? Is the fine-grid variability (sub-128 ms) Bayesian-block estimate
   statistically valid?

8. **Manifest** — `scripts/38_build_manifest.py`. Does the master manifest
   faithfully record detector/background/source-interval selections?

## Cross-cutting checks
- Any **stale/duplicated logic** between numbered scripts and their `.bak`
  variants or legacy scripts (24/25/26) that could be silently used?
- Any place where a **provisional/auto background** is mixed with clean data
  without provenance (stale-mix risk)?
- Reproducibility: hardcoded absolute paths, env assumptions (CALDB), random
  seeds.
- Statistical soundness overall: are the model-selection and correlation claims
  defensible for an ApJ referee?

## Output
Write `CODEX_AUDIT_REPORT_PIPELINE.md`: a one-paragraph overall verdict, then
findings grouped by severity with `file:line` + concrete fix + paper-number
impact. Distinguish "confirmed-correct" (briefly) from "needs-fix". Be specific;
cite line numbers.

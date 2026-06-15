# Gor Review Status (2026-05-16)

## What I looked for and did not find

- No `.tex` files, no `paper/`, no `draft/`, no `manuscript/` directory in
  the project tree.
- No `notes/` directory.
- No `comments_from_gor.md`, no email/Slack export, no `review_*.md`.
- No `TODO.md`, no checklist file.
- No mention of "Gor" or "review" in any of the only two text files in the
  project (`PLAN.md`, `results/download_status.txt`).

The only planning document is `PLAN.md`, last touched 2026-02-24, which
predates almost all of the actual results. So the "what's awaiting Gor"
list below is **inferred** from the state of the pipeline outputs and the
unmade decisions encoded in `06_spectral_fitting.py` and
`07_spectral_plots.py` — not from a prior message log.

If a real review thread exists in email, Slack, or a notebook elsewhere,
this document should be updated against it before sending anything to Gor.

---

## Inferred decisions awaiting Gor

### 1. Single-pulse threshold — confirm 0.9983

Currently `single_pulse_grbs.ecsv` uses the Busby & Lazzati (2024) cut of
score ≥ 0.9983 (≤ 3 unnormalised failures), yielding **106 single-pulse
GRBs** from 858 with TTE data. `PLAN.md` says this is "Busby & Lazzati's
0.9983" — Gor should confirm we adopt their threshold verbatim rather than
calibrating to our brighter fluence cut.

**Artifact to show Gor:** `plots/score_histogram.png`,
`plots/failures_histogram.png`, `results/single_pulse_grbs.ecsv` (106
entries).

### 2. BB-detection criterion — choose a ΔBIC cut

`spectral_fit_results.ecsv` records ΔBIC = BIC(Band) − BIC(BB+Band) per
bin but **no `BB_DETECTED` boolean is stored**. Of the 837 successful bins:

- ΔBIC < −6  → **620 bins (74%)** — "positive" BB preference (Kass & Raftery)
- ΔBIC < −10 → **126 bins (15%)** — "strong" BB preference
- ΔBIC >  0  → 92 bins (11%) — Band-only preferred

Burgess et al. (2014) used a likelihood-ratio test; Burgess (2019) uses
Bayes factors. Gor should pick the published threshold and we should
freeze it in a results table.

**Artifact to show Gor:** a 4-row summary of these ΔBIC counts (per above);
`plots/ep_kt_combined.png` and `plots/ep_kt_combined_with_fits.png`.

### 3. Parameter-tying / seed propagation between bins

`06_spectral_fitting.py:230-231, 253-259` seeds each bin's BB+Band fit
from the **previous bin's best-fit values**, clamped to the bounds.
Burgess (2014) instead uses Bayesian priors per bin (independent draws).
Gor should sign off on either:

- (a) keep the previous-bin seeding (faster, but introduces bin-to-bin
  correlation that may bias the Ep–kT slope), or
- (b) switch to per-bin independent fits with Burgess-style priors (slower,
  cleaner inference; requires nontrivial code change).

This decision is what produced the two `FAILED` bins documented in
`FAILED_FITS.md`, so it has a concrete consequence.

**Artifact to show Gor:** the relevant 30-line block of
`06_spectral_fitting.py` (lines 230–340); the 8+2 failure cases in
`FAILED_FITS.md`.

### 4. Inclusion criteria for the Ep–kT scatter

The plot script currently includes every `FIT_STATUS=OK` bin with a finite
Ep and KT. But 33% of OK bins have ALPHA railed at a bound and 8% have KT
railed at the lower bound (1 keV) — see `FAILED_FITS.md`. We need a stated
filter for the publication scatter. Candidates:

- (i) drop bins with any of ALPHA, EP, KT, BETA within 1% of a bound;
- (ii) drop bins with KT < 3 keV (below the NaI 8 keV threshold the BB is
  unconstrained);
- (iii) require ΔBIC < −6 (i.e. "BB detected") in addition to FIT_STATUS=OK.

The combination (i)+(ii)+(iii) is the cleanest but will roughly halve the
sample. Gor should pick.

**Artifact to show Gor:** `plots/alpha_histogram.png`,
`plots/ep_kt_combined_with_fits.png`, and the table at the bottom of
`FAILED_FITS.md`.

### 5. Per-GRB α slopes (baryonic vs magnetic classification)

`plots/ep_kt_correlations/` contains 90 per-GRB power-law fits. The plan
calls for α ≈ 1 → baryonic, α ≈ 2 → magnetic. We have not produced a
results table summarising α-per-GRB, the formal Spearman r/p across the
sample, or the histogram split into baryonic/magnetic populations beyond
`plots/alpha_histogram.png`. Gor should confirm whether the paper presents:

- a single α-distribution histogram (status quo), or
- a per-GRB α table with errors + classification column.

**Artifact to show Gor:** `plots/alpha_histogram.png`,
`plots/ep_kt_correlations/` (representative subset, e.g. 3–4 highest- and
3–4 lowest-significance cases).

### 6. Handling of the 10 problem fits

8 BAND_ONLY_OK + 2 FAILED bins (see `FAILED_FITS.md`). Drop silently?
List in an appendix? Re-fit with a different seeding strategy and report
both results? Gor should call it.

---

## What is NOT awaiting Gor (work the PI can complete unilaterally first)

These are not blocked by Gor — knocking them out before pinging him
strengthens the message:

- Persist per-bin Band and BB fluxes (Phase 4.2 of PLAN), and a per-bin
  `BB_DETECTED` boolean using whatever ΔBIC threshold is chosen.
- Generate a per-GRB α-results ECSV (alongside the per-GRB plots).
- Verify the N_DATA_POINTS column is being written correctly
  (`06_spectral_fitting.py:366` — see schema notes in FAILED_FITS.md).
- Re-run only the 10 failed/marginal bins with the seed-fallback fix
  suggested in FAILED_FITS.md (no global re-run needed).

---

## Suggested follow-up note for the PI to send Gor

> **Subject:** Two_Breaks single-pulse Ep–kT — figures and numbers ready,
> looking for your call on 3 model-selection questions
>
> Hi Gor — quick status on the Busby-style single-pulse + Burgess BB+Band
> project. We have 106 single-pulse GRBs from 858 with Fermi GBM TTE data
> (Busby & Lazzati 2024 threshold of 0.9983). Of those, 99 have Bayesian-
> blocks PHA files and produced 848 time-resolved BB+Band joint fits
> (NaI+BGO), of which 837 converged cleanly (98.7%). I can send the Ep–kT
> combined scatter, the α-distribution histogram, and the per-GRB Ep–kT
> plots — happy to push them to a Dropbox folder if that's easier than
> attachments. Before I draft text I'd like your call on three things:
> **(i)** what ΔBIC threshold do we use to declare a BB component
> detected — ΔBIC < −6 keeps 620 bins, ΔBIC < −10 keeps 126; **(ii)** do
> we cut bins with ALPHA or KT railed at the fit bounds (33% / 8% of OK
> bins respectively) from the published Ep–kT scatter, and what's the
> stated criterion; **(iii)** are we OK with seeding each bin's fit from
> the previous bin's best-fit, or do you want the Burgess-2014 per-bin
> Bayesian-prior treatment? Two bins hard-failed because of bad seed
> propagation — easy fix once you've decided on the seeding policy. The
> νFν decompositions and per-GRB Ep–kT correlation plots are in
> `plots/spectral_fits/` and `plots/ep_kt_correlations/`. Best, Salim.

Lightly tighten phrasing/length to match your usual register before sending.

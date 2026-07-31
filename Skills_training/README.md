# Skills_training — the paper corpus we mine for AI-scientist skills

Papers we read in the reading-group campaign (Vikas annotates → we distill skills,
projects, and reconciliation targets). Aiming for ~200 papers. Each entry logs what
the paper YIELDED, so this dir is both the corpus and its index.

Convention: PDFs named `Author_YYYY_Journal_Vol_Page.pdf`. New training papers land
here (not the repo root). The mined skills live in `dev/ai_guides/*.md` (per-step
skill files) and `notes/skills_from_<paper>.md`; projects in
`notes/PROJECTS_registry.md`; per-question answers in `notes/<paper>_reading_group_
answers.md`.

## Corpus index

### Yu, Dereli-Bégué & Ryde 2019, ApJ 886, 20 — "Bayesian Time-resolved Spectroscopy of GRB Pulses"
`Yu_2019_ApJ_886_20.pdf` (published, canonical) + `Yu_2019_ApJ_886_20_arxiv.pdf`
(preprint — pagination for the p.8/9 refs). **First fully-mined paper (2026-07-30).**
- **Skills yielded:** the full A/M/C table in `notes/skills_from_Yu2019.md` (35
  skills); B1 (fit-statistic auto-select) → `SpectralFitting.md §METHODS BOX`;
  L6b (significance = joint-fit quantity, S≥10 floor, quality-flag-not-cut).
- **Projects yielded:** #34 cutoff genuine-vs-count, #35 soft-p rescue via wind
  absorption, #36 revisit Burgess-2014 binning. Feeds Astrograph (niche map).
- **Answer sheet:** `notes/Yu2019_reading_group_answers.md` (~55 Qs, keyed to
  Vikas's numbering; all citations grounded).
- **Reconciliation target (burst #1 bn081125496):** Yu NAMES it — α–Ep nonmonotonic
  with break at α_max, h.t.s. (p.9). Tested in Step 6 (2026-07-30).

### Meng et al. 2019, ApJ 882, 26 — "Time-resolved Spectra of Photospheric Emission from a Structured Jet"
`Meng_2019_ApJ_882_26.pdf`. Physical FORWARD model (not a per-burst fit).
Read top+bottom 2026-07-30 (abstract p.1 + intro + Figs).
- **Explores:** photosphere from a structured jet (inner-constant + outer-
  decreasing angular Γ profile) + continuous wind (time-dependent L_w).
- **Gap attacked (intro's 4 synchrotron/IS failures):** (1) low-E slopes harder
  than the α=−2/3 death line, (2) spectral width too narrow for synchrotron
  (Axelsson & Borgonovo 2015), (3) narrow ~few-100-keV Ep distribution, (4)
  internal-shock efficiency too low.
- **Claims to solve:** reproduces CPL-like peak spectra, α≈−1 (−2≲α≲0 spread),
  and BOTH Ep-evolution types (h.t.s./i.t.) split by core width θ_c (multi- vs
  single-pulse).
- **Tension:** labels bn081125496 MULTI-pulse — but that is MODEL-driven (θ_c),
  not observational; our Busby single-pulse selection is observational. Footnote
  5: the cutoff was FIXED, so "no empirical model fits 4.3–6.3 s" is not a proper
  fit.
- **What they LEFT for us (gap-map):** a demonstration model with fixed params;
  never statistically fit per burst. Our Step-6 supplies the empirical fact their
  model is built to explain — bn081125496: CPL wins 6/8 blocks, every bin
  α>−2/3, Ep h.t.s. 358→38 keV. Empirical↔physical handshake: we measure the
  shape, they propose the mechanism. Fork = Intro-Q3 (empirical-first vs physical
  -first).

## How a paper flows through the campaign
1. Step 0 GCN/ADS sweep finds it → PDF here.
2. Vikas annotates → questions + skill/project nominations.
3. We answer per-question (grounded), distill skills (deduped into the step files),
   register projects, and set reconciliation targets for any burst it names.
4. Burst walkthrough Step 6 tests the paper's specific claims against our fits.

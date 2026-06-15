# Two_Breaks — Time-Resolved Spectroscopy of Single-Pulse GRBs

Uniform time-resolved empirical spectral survey of **106 bright single-pulse
Fermi/GBM gamma-ray bursts**, asking one question: is the spectral curvature
beyond a single break a **sub-dominant thermal photosphere** or a **second
synchrotron break**?

Each burst is fit, in every Bayesian-block time bin, with six photon models
(Band, CPL, SBPL, 2SBPL, Band+BB, CPL+BB) and the two pictures are compared with
information criteria. Manuscript: `paper/two_break.tex` (K. Sharma et al.).

> **Status: provisional.** All numbers below use an automatically-selected
> background catalogue; a human-verified background pass is in progress and the
> authoritative re-fit follows it. The qualitative conclusions are not expected
> to change. See *Status & caveats*.

**Headline (provisional):** at the locked **ΔAIC ≥ 10** threshold, of the bins
requiring curvature **87 % are thermal-or-degenerate** vs **13 % a decisive
two-break** — a lower limit (94/14 of 108; the looser ΔAIC ≥ 6 cut gives
91 %/9 %, reported as a sensitivity check); the Burgess $E_{\rm p}$–$kT$
correlation is recovered in most testable bursts (GRB 130427A: $\rho=0.93$); the
two 2SBPL breaks $\nu_m$–$\nu_c$ are positively correlated within and between
bursts; spectral evolution is HTS-dominated.

> **Relation to GRB_Handbook.** This repo is the single-pulse-spectroscopy study;
> its reusable, burst-agnostic machinery — background selection
> (`28`/`30`/`36`), Bayesian blocking (`27`), the spectral engine (`10`), the
> per-GRB end-to-end notebook, and the master-manifest schema — are the candidate
> modules for the planned **GRB_Handbook**, a full GRB-analysis pipeline to be
> released publicly. Kept private until the paper is out; structured so these
> pieces merge cleanly upstream.

---

## What's in this repo

```
scripts/      the pipeline (numbered in execution order; see "Pipeline" below)
paper/        two_break.tex + .bib + .bbl, figures/, machine-readable tables/
notebooks/    Two_Breaks_single_GRB_pipeline.ipynb  <- run one GRB end to end
results/      catalogues + the master manifest (large per-burst outputs gitignored)
data/         raw GBM TTE — only 6 sample bursts are committed (rest re-downloadable)
notes/        the audit report, the Li-2021 writing template, findings memos
BACKGROUND_SELECTION_PROCESS.md   the authoritative detector+background ruleset
KHUSHBOO_BACKGROUNDS.md           the background-verification task brief
```

**The 6 bundled sample bursts** (so the notebook runs out of the box):
`bn110721200` (clean 2SBPL standout, NaI+BGO+LLE), `bn160625945` (bright Band+BB),
`bn150902733`, `bn081125496` (faint Silver), `bn090620400` (a once-broken
background, now fixed), `bn201016019` (fast variability).

---

## The sample & the master manifest

`results/master_manifest.csv` — one row per burst with the full selection record:

| column | meaning |
|---|---|
| `trigger`, `name`, `T90`, `fluence`, `has_lat` | burst identity & GBM-catalog properties |
| `reference_nai` | NaI whose light curve defines the time bins |
| `nai_dets`, `bgo_det`, `lle` | **detector selection** (all detectors entering the fit) |
| `source_t1`, `source_t2`, `n_bins` | **source/analysis interval** (Bayesian-block span) and bin count |
| `bkg_pre_*`, `bkg_post_*` | reference-detector **background windows** |

Full per-detector background windows: `results/background_intervals_clean.ecsv`.

---

## Environment

Spectral fitting needs the **threeML** conda env (3ML + fermitools); set CALDB to
the env before importing astromodels:

```bash
conda activate threeML
export CALDB=$CONDA_PREFIX/share/fermitools/data/caldb
export CALDBCONFIG=$CALDB/software/tools/caldb.config
export CALDBALIAS=$CALDB/software/tools/alias_config.fits
```

Light-weight steps (catalogues, manifest, the background picker, figures) need
only `numpy`, `astropy`, `scipy`, `matplotlib`.

---

## Quickstart — analyse one GRB end to end

```bash
jupyter notebook notebooks/Two_Breaks_single_GRB_pipeline.ipynb
```

Set `BURST` at the top (default `bn110721200`) and *Run All*. It walks through
**every step one GRB needs**, calling the real production engine:

1. **detector selection** (NaI/BGO/LLE and why)
2. **background** windows + polynomial interpolation → net light curve
3. **Bayesian-block** time bins
4. **six-model fit** (live) with count-spectrum + residuals
5. **model comparison** — AIC/BIC, ΔAIC≥10, validity gate, curvature class
6. **parameter evolution** — $E_{\rm p}(t),\alpha(t),\beta(t),kT(t),F(t)$
7. **correlations** — $E_{\rm p}$–$kT$, $\nu_m$–$\nu_c$, $F$–$\alpha$
8. **variability** timescale (fine-grid Bayesian blocks)

Works on any of the 106 bursts once that burst's `data/<trigger>/` is present.

---

## The pipeline, stage by stage (what we did)

| stage | script | does |
|---|---|---|
| sample | `01_build_sample.py` | GBM catalog → single-pulse, bright cut (fluence > 1e-5) |
| selection | `03_horizontal_line.py` (Busby & Lazzati 2024) | single-pulse shape score |
| download | `02_download_data.py` | fetch TTE + responses (HEASARC) |
| backgrounds | `28_reselect_backgrounds.py` → `30_background_picker.py` | auto windows, then human review |
| binning | `27_reblock_all.py` | Bayesian blocks (binned/measures mode) per burst |
| **fitting** | `10_spectral_fit_burst.py` | the engine: 6 models, AIC/BIC, LRT, validity gate, BB multi-start |
| driver | `29_refit_clean.py` | run the engine over all bursts → `results/clean_per_burst/` |
| numbers | `31_draft_numbers.py` | population statistics → `results/draft_numbers.json` |
| figures | `32_make_figures.py` | the paper figures |
| variability | `35_variability_bb.py` | per-burst variability timescale |
| manifest | `38_build_manifest.py` | the master manifest CSV |

(Helpers `33`/`34`/`36`/`37` build the machine tables, example spectra, the
progress checker, and this notebook.)

---

## Decision framework (locked)

- **Significance:** a blackbody or second break is decisive at **ΔAIC ≥ 10** over
  its parent (the Li 2021 / Burgess 2019 threshold); **ΔBIC** is the conservative
  cross-check. The LRT is used only for **nested** pairs; the central
  thermal-vs-2SBPL comparison is **non-nested**, so information criteria decide it.
- **Validity gate:** a railed fit (parameter at a bound, or 2SBPL breaks
  mis-ordered) cannot win model selection.
- **Correlations:** Spearman $\rho$ + least-squares log slope; the $\nu_m$–$\nu_c$
  relation uses the D'Agostini (2005) errors-in-both-variables fit.
- **Two-break fraction is a lower limit** (the 2SBPL has no convergence restart in
  this provisional run; added at the authoritative re-fit).

Model descriptions follow Ravasio et al. 2018 (2SBPL) and Guiriec et al.
(multi-component); see `notes/` and the paper §2.

---

## Background selection (the human-verified pass)

```bash
python scripts/30_background_picker.py      # GUI: review/adjust per detector
python scripts/36_progress_check.py         # progress + continuous QC
```

The picker is seeded from `results/background_starting_points.ecsv` (so it is
*review*, not from scratch) and writes `results/background_intervals.ecsv`.

---

## The paper

```bash
cd paper
pdflatex two_break && bibtex two_break && pdflatex two_break && pdflatex two_break
```

(Two BibTeX passes are required — the bibliography is external,
`two_break.bib` + `aasjournal` style.)

---

## Status & caveats

- Numbers are **provisional** (auto backgrounds). The authoritative re-fit, on the
  human-verified backgrounds, goes to a **fresh output root** and adds: a 2SBPL
  convergence restart, Ravasio smoothness ($n_1{=}5.38,n_2{=}2.69$), the
  Ravasio K-edge mask, provenance stamps, and an explicit background-file argument
  so the human-reviewed catalogue actually drives the fit.
- Two independent audits verified the catalogue reproduces exactly (106 bursts,
  1057 bins): `notes/PROJECT_AUDIT_2026-06-09.md` (multi-agent) and
  `CODEX_AUDIT_REPORT_PIPELINE.md` (whole-pipeline). **Open items the second audit
  flags for the authoritative pass / paper:** (1) the sample-selection code adds
  an undocumented `T90>2 s` cut and does not run the two-brightest-detector Busby
  procedure as stated; (2) the $E_{\rm p}$–$kT$ pairing should take both from the
  *same* composite fit (re-pairing shifts the Burgess result modestly); (3) the
  $\nu_m$–$\nu_c$ relation should make the *decisive-second-break* subset primary;
  (4) the sub-128 ms variability claim needs a calibrated false-alarm test.
- Roadmap to submission: see the execution plan in the project notes.

## Data availability

Raw GBM data are public (HEASARC) and re-downloadable via `scripts/02`; only 6
sample bursts are committed here. The derived `results/clean_per_burst/`
(per-burst fits) is regenerable by `scripts/29`; the 6 sample bursts' outputs are
included so the notebook runs without re-fitting.

---

## References

The PDFs are not redistributed here; full BibTeX is in `paper/two_break.bib`.
Each entry below notes its role in this analysis.

**Instruments, methods & tools**
- Meegan et al. 2009, ApJ 702, 791 — Fermi/GBM instrument.
- Atwood et al. 2009, ApJ 697, 1071 — Fermi/LAT (LLE data).
- Vianello et al. 2015, arXiv:1507.08343 — **3ML**, the fitting framework.
- Scargle et al. 2013, ApJ 764, 167 — **Bayesian Blocks** (time binning).
- Akaike 1974, IEEE TAC 19, 716 / Schwarz 1978, Ann. Stat. 6, 461 — **AIC / BIC** model selection.
- Wilks 1938, Ann. Math. Stat. 9, 60 — likelihood-ratio test (nested pairs only).
- D'Agostini 2005, arXiv:physics/0511182 — errors-in-both-variables correlation fit.
- Busby & Lazzati 2024, ApJ 972, 83 — single-pulse "horizontal-line" selection.
- Kaneko et al. 2006, ApJS 166, 298; Gruber et al. 2014, ApJS 211, 12; Yu et al. 2016, A&A 588, A135 — GBM time-resolved spectral catalogues (comparison + SBPL smoothness).

**Spectral models**
- Band et al. 1993, ApJ 413, 281 — the Band function.
- Ravasio et al. 2018, A&A 613, A16; Ravasio et al. 2019, A&A 625, A60 — **2SBPL** functional form + smoothness ($n_1{=}5.38,n_2{=}2.69$) and synchrotron break interpretation.
- Guiriec et al. 2010 (ApJ 725, 225), 2011 (ApJL 727, L33), 2015 (ApJ 807, 148) — multi-component (non-thermal + blackbody) decomposition.
- Sari, Piran & Narayan 1998, ApJL 497, L17 — synchrotron cooling/injection breaks.
- Preece et al. 1998, ApJL 506, L23; Crider et al. 1997, ApJL 479, L39 — synchrotron "lines of death" ($-2/3,-3/2$).

**Science comparison (single-pulse / curvature)**
- Burgess et al. 2014a, ApJL 784, L43 — the $E_{\rm p}$–$kT$ correlation we test at scale.
- Burgess et al. 2014b, ApJ 784, 17 — physical synchrotron fits to single pulses.
- Burgess et al. 2019, MNRAS 490, 927 — Bayesian short-GRB catalogue (Bayes-factor threshold).
- Basak & Rao 2013 (MNRAS 436, 3082), 2014 (MNRAS 442, 419) — single-pulse BBPL/2BBPL, HTS/IT.
- Lu et al. 2012, ApJ 756, 112 — HTS/IT $E_{\rm p}$-evolution classes.
- Ryde 2004 (ApJ 614, 827); Ryde & Pe'er 2009 (ApJ 702, 1211) — photospheric BBPL lineage.
- Oganesyan et al. 2017 (ApJ 846, 137), 2018 (A&A 616, A138) — low-energy synchrotron breaks.
- Ravasio et al. 2023, arXiv:2303.16223 — 2SBPL second break only at highest S/N (GRB 221009A).
- Ronchi et al. 2020, A&A 636, A55 — time-resolved physical synchrotron ($E_c$,$E_m$ co-evolution).
- Mei et al. 2025, A&A 693, A156 — $\nu_c$–$L_{\rm iso}$ vs no $E_{\rm p}$–$L$; cooling-regime ratio.
- Acuner et al. 2020, ApJ 893, 128 — when $\alpha$ discriminates photosphere vs synchrotron.
- Li et al. 2021, ApJS 254, 35 — the writing-style + selection-threshold template.
- Mészáros & Rees 2000 (ApJ 530, 292); Pe'er et al. 2007 (ApJL 664, L1); Kumar & Zhang 2015 (Phys. Rep. 561, 1); Yonetoku et al. 2004 (ApJ 609, 935) — photosphere theory, review, Yonetoku relation.

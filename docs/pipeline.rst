========================
The Pipeline & Methodology
========================

This page documents what the analysis does, stage by stage, the locked decision
framework, the instruments currently used, and how the reusable pieces feed the
planned broadband **GRB_Handbook**.

The scientific question
=======================

For a uniform sample of **106 bright single-pulse Fermi/GBM GRBs**, fit every
Bayesian-block time bin with six photon models and ask, where the data require
curvature beyond a single spectral break, whether that curvature is a
**sub-dominant thermal (photospheric) component** or a **second synchrotron
break**.

The six models
==============

.. list-table::
   :header-rows: 1
   :widths: 18 18 64

   * - Model
     - Components
     - Role
   * - Band
     - smoothly-broken PL
     - the canonical empirical baseline
   * - CPL
     - cut-off PL
     - Band with :math:`\beta \to -\infty` (one fewer parameter)
   * - SBPL
     - sharply-broken PL
     - single-break alternative
   * - 2SBPL
     - doubly-broken PL
     - the **two-break** picture (Ravasio et al. 2018 form)
   * - Band+BB
     - Band + blackbody
     - the **thermal** picture on a Band continuum
   * - CPL+BB
     - CPL + blackbody
     - the **thermal** picture on a CPL continuum

Stage by stage
==============

.. list-table::
   :header-rows: 1
   :widths: 14 30 56

   * - Stage
     - Script
     - Does
   * - sample
     - ``01_build_sample.py``
     - GBM catalogue → single-pulse, bright cut (fluence > 1e-5)
   * - selection
     - ``03_horizontal_line.py``
     - single-pulse shape score (Busby & Lazzati 2024)
   * - download
     - ``02_download_data.py``
     - fetch TTE + responses (HEASARC)
   * - backgrounds
     - ``28_reselect_backgrounds.py`` → ``30_background_picker.py``
     - auto burst-centred windows, then human review
   * - binning
     - ``27_reblock_all.py``
     - Bayesian blocks (binned ``measures`` mode) per burst
   * - **fitting**
     - ``10_spectral_fit_burst.py``
     - the engine: 6 models, AIC/BIC, LRT, validity gate, BB multi-start
   * - driver
     - ``29_refit_clean.py``
     - run the engine over all bursts → ``results/clean_per_burst/``
   * - numbers
     - ``31_draft_numbers.py``
     - population statistics → ``results/draft_numbers.json``
   * - figures
     - ``32_make_figures.py``
     - the paper figures
   * - variability
     - ``35_variability_bb.py``
     - per-burst variability timescale
   * - manifest
     - ``38_build_manifest.py``
     - the master manifest CSV

Helpers ``33`` / ``34`` / ``36`` / ``37`` build the machine tables, the example
spectra, the progress/QC checker, and the end-to-end notebook.

The decision framework (locked)
===============================

* **Significance.** A blackbody or a second break is *decisive* at
  **ΔAIC ≥ 10** over its parent model (the Li et al. 2021 / Burgess et al. 2019
  threshold; equivalently LRT ≥ 14 for the two extra degrees of freedom).
  **ΔBIC** is reported as the conservative cross-check.
* **Nested vs non-nested.** The likelihood-ratio test is applied only to
  **nested** pairs (Band+BB/Band, CPL+BB/CPL, 2SBPL/SBPL). The central
  thermal-vs-two-break comparison is **non-nested**, so it is decided by the
  information criteria, not the LRT.
* **Validity gate.** A railed fit — any parameter pinned at a bound, or 2SBPL
  breaks mis-ordered (:math:`x_b \ge x_p`) — cannot win model selection.
* **Correlations.** Spearman :math:`\rho` plus a least-squares log slope; the
  :math:`\nu_m`–:math:`\nu_c` relation uses the D'Agostini (2005)
  errors-in-both-variables likelihood with free intrinsic scatter.
* **The two-break fraction is a lower limit** — the provisional run has no 2SBPL
  convergence restart; one is added at the authoritative re-fit.

Model functional forms follow Ravasio et al. 2018 (2SBPL smoothness
:math:`n_1{=}5.38,\ n_2{=}2.69`) and Guiriec et al. (multi-component); see the
paper §2 and ``notes/``.

Backgrounds (the human-verified pass)
=====================================

.. code-block:: bash

   python scripts/30_background_picker.py    # GUI: review/adjust per detector
   python scripts/36_progress_check.py       # progress + continuous QC

The picker mirrors ``gtburst``'s two-panel light-curve-with-residuals layout and
is seeded from ``results/background_starting_points.ecsv`` (so it is *review*,
not from scratch); it writes ``results/background_intervals.ecsv``. The full
ruleset is in ``BACKGROUND_SELECTION_PROCESS.md``; the verification brief is
``KHUSHBOO_BACKGROUNDS.md``.

Instruments used here
=====================

This study is **Fermi-only**, joint-fitting the prompt emission across:

* **Fermi/GBM NaI** — 8–900 keV (the reference light curve and the soft band)
* **Fermi/GBM BGO** — 0.3–40 MeV (the hard band, constraining :math:`\beta`)
* **Fermi/LAT-LLE** — 30–100 MeV (where available; extends the high-energy lever
  arm)

Status & caveats
================

* Numbers are **provisional** (automatically-selected backgrounds). The
  authoritative re-fit, on the human-verified backgrounds, goes to a **fresh
  output root** and adds: a 2SBPL convergence restart, the Ravasio smoothness
  values, the Ravasio K-edge mask, and provenance stamps.
* An independent multi-agent audit (``notes/PROJECT_AUDIT_2026-06-09.md``)
  verified that every headline number reproduces from the catalogue.
* The qualitative conclusions are not expected to change across the re-fit.

Toward GRB_Handbook
===================

Two_Breaks is the single-pulse spectroscopy *study*; it stays private until the
paper is out. Its **burst-agnostic** modules are the seed for a planned, public
**GRB_Handbook** — a full GRB-analysis pipeline. The pieces designed to merge
upstream:

* background selection (``28`` / ``30`` / ``36``)
* Bayesian blocking (``27``)
* the spectral engine (``10``) and its model registry
* the per-GRB end-to-end notebook
* the master-manifest schema

The Handbook broadens the instrument coverage from this Fermi-only study to the
full prompt-to-afterglow chain, **wherever each is available** per burst:

* **Swift-XRT** (soft X-ray afterglow / late prompt)
* **Swift-BAT** (15–150 keV)
* **Fermi/GBM** (NaI + BGO, 8 keV–40 MeV)
* **Fermi/LAT-LLE** (30–100 MeV)
* **Fermi/LAT** (> 100 MeV)

New reusable code is kept modular and instrument-agnostic so it transfers to the
Handbook without rework.

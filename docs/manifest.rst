=============================
The Sample & Master Manifest
=============================

The sample
==========

**106 bright single-pulse Fermi/GBM GRBs**, selected by single-pulse light-curve
shape (Busby & Lazzati 2024 "horizontal-line" score) above a brightness cut
(fluence > :math:`10^{-5}` erg cm\ :sup:`-2`). The selection picks *shape*, not
*brightness*: the sample fluence spans ~250× across its range.

The master manifest
===================

``results/master_manifest.csv`` is the human-readable selection record — one row
per burst, built by ``scripts/38_build_manifest.py``:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Column
     - Meaning
   * - ``trigger``, ``name``
     - GBM trigger id (``bnYYMMDDfff``) and GRB name
   * - ``T90``, ``fluence``, ``has_lat``
     - GBM-catalogue properties; whether LAT/LLE data exist
   * - ``reference_nai``
     - the NaI detector whose light curve defines the time bins
   * - ``nai_dets``, ``bgo_det``, ``lle``
     - **detector selection** — every detector entering the fit
   * - ``source_t1``, ``source_t2``, ``n_bins``
     - **source / analysis interval** (Bayesian-block span) and bin count
   * - ``bkg_pre_start/stop``, ``bkg_post_start/stop``
     - reference-detector **background windows**

The full per-detector background windows (all NaI + BGO, not just the reference)
live in ``results/background_intervals_clean.ecsv``.

The six bundled sample bursts
=============================

These bursts are committed whole (``data/`` + ``results/clean_per_burst/``) so
the notebook runs out of the box; they span the regimes the study cares about:

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Trigger
     - Why it is in the sample set
   * - ``bn110721200``
     - the clean **2SBPL standout** (a genuine two-break burst); NaI+BGO+LLE
   * - ``bn160625945``
     - a bright **Band+BB** (thermal) case
   * - ``bn150902733``
     - a bright mid-sample burst
   * - ``bn081125496``
     - a faint "Silver"-tier burst (low-S/N regime)
   * - ``bn090620400``
     - a once-broken background (source window had landed on pure background),
       now fixed — illustrates the background-verification fix
   * - ``bn201016019``
     - fast variability (fine-grid Bayesian-block timescale)

The remaining 100 bursts' raw data are re-downloadable via ``scripts/02``, and
their per-burst fits are regenerable via ``scripts/29``.

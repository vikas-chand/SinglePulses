.. _api:

=============
API Reference
=============

The importable surface of this repository is small by design: the ``two_breaks``
package exposes version + path metadata and a loader for the production spectral
engine, which itself lives in the numbered ``scripts/`` and is run as a pipeline
(see :doc:`pipeline`). This page documents the package and the engine's public
functions.

two_breaks
==========

Package metadata, repository paths, and the engine loader.

.. automodule:: two_breaks
   :members:

The spectral engine (``scripts/10_spectral_fit_burst.py``)
==========================================================

Loaded via :func:`two_breaks.load_engine`. Because the file has a digit-prefixed
name it cannot be imported with a normal ``import`` statement, so it is not
auto-documented here; its public functions are summarised below. Run inside the
``threeML`` environment with CALDB exported (see :doc:`installation`).

``build_spectrumlike_per_block(trigger, det, pre, post, bin_starts, bin_stops)``
   Build the 3ML ``SpectrumLike`` / ``DispersionSpectrumLike`` plugins for one
   detector across the Bayesian-block bins, using the given pre/post background
   windows for the polynomial background fit. Returns the per-bin plugins.

``get_canonical_bins(...)``
   Return the canonical (reference-detector) Bayesian-block bin edges that define
   the time-resolved spectra for a burst.

``fit_all_models(plugins, plugin_dets, canonical_det, seed_in=None, include_dsbpl=True)``
   Fit all six models (Band, CPL, SBPL, 2SBPL, Band+BB, CPL+BB) to one time bin's
   joint plugins. Handles BB multi-start (to avoid the seed-poisoning local
   minimum), the nested LRT guard, and per-model parameter seeding. Returns the
   per-model fit results (parameters, errors, −2 log L, AIC, BIC, k).

``select_best(per_spec_results, n_data)``
   Return, for one time bin, the lowest-AIC and lowest-BIC model among the fits
   that pass the physical-validity gate (``_fit_is_physical``: no railed
   parameters, 2SBPL breaks ordered ``xb < xp``), plus the three nested-pair LRTs
   (Band+BB/Band, CPL+BB/CPL, 2SBPL/SBPL). If *no* fit is physical it falls back
   to the unfiltered minimum (those bins are filtered downstream). **Note:** this
   function does *not* apply the ΔAIC ≥ 10 threshold or assign a curvature class
   — that thresholding/classification is done in ``scripts/31_draft_numbers.py``,
   which also discards the no-physical-fallback winners.

Model builders
--------------

Internal helpers that construct each ``astromodels`` spectral shape with its
parameter bounds and seeds: ``_setup_band``, ``_setup_cpl``, ``_setup_bb``,
``_setup_sbpl``, ``_setup_dsbpl``. The validity gate is ``_fit_is_physical``.

Energy ranges (module constants)
--------------------------------

.. code-block:: text

   NAI_RANGES = ('8.1-33', '40-900')      # keV, K-edge gap excluded
   BGO_RANGES = ('300-40000',)            # keV
   LLE_RANGES = ('30000-100000',)         # keV  (30-100 MeV)

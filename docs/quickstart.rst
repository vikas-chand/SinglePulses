==========
Quickstart
==========

The fastest way to see the whole method is to analyse **one GRB end to end** with
the bundled notebook, which calls the real production engine at every step.

Analyse one GRB end to end
==========================

.. code-block:: bash

   conda activate threeML            # the fit step needs 3ML (see Installation)
   jupyter notebook notebooks/Two_Breaks_single_GRB_pipeline.ipynb

Set ``BURST`` at the top (default ``bn110721200``) and *Run All*. The notebook
walks through **every step a single GRB needs** for this study:

#. **detector selection** — which NaI/BGO/LLE detectors enter the fit, and why
   (NaI within 50° of the source; the brightest as the reference light curve).
#. **background** — pre/post windows and the polynomial interpolation across the
   burst, giving the net (background-subtracted) light curve.
#. **Bayesian-block** time bins (binned ``measures`` mode, ``dt = 0.128`` s,
   ``p0 = 0.01``).
#. **six-model fit** (live) — Band, CPL, SBPL, 2SBPL, Band+BB, CPL+BB — with the
   count spectrum and fit residuals shown per bin.
#. **model comparison** — AIC/BIC, the ΔAIC ≥ 10 decision, the physical-validity
   gate, and the resulting curvature class (thermal / two-break / degenerate).
#. **parameter evolution** — :math:`E_{\rm p}(t),\ \alpha(t),\ \beta(t),\
   kT(t),\ F(t)`.
#. **correlations** — :math:`E_{\rm p}`–:math:`kT`,
   :math:`\nu_m`–:math:`\nu_c`, :math:`F`–:math:`\alpha`.
#. **variability** timescale from fine-grid Bayesian blocks.

It works on any of the 106 bursts once that burst's ``data/<trigger>/`` is
present; the six sample bursts (see :doc:`manifest`) are committed so it runs out
of the box.

Calling the engine directly
===========================

The ``two_breaks`` package can load the spectral engine
(``scripts/10_spectral_fit_burst.py``) as an importable module — useful for
scripting one burst, or for re-using the fitter in another project:

.. code-block:: python

   import two_breaks

   eng = two_breaks.load_engine()      # imports scripts/10 via importlib

   # The engine exposes (see the API reference):
   #   build_spectrumlike_per_block(trigger, det, pre, post, bin_starts, bin_stops)
   #   fit_all_models(plugins, plugin_dets, canonical_det, seed_in=None, ...)
   #   get_canonical_bins(...)
   #   select_best(...)         # AIC/BIC + validity gate -> winning model

   print("data root:   ", two_breaks.DATA)
   print("results root:", two_breaks.RESULTS)

.. note::

   ``load_engine()`` triggers the engine's module-level imports (3ML /
   ``astromodels``), so it must be run inside the ``threeML`` environment with
   CALDB exported (see :doc:`installation`).

Reproduce the population numbers
================================

Once the per-burst fits exist under ``results/clean_per_burst/`` (the six sample
bursts are committed; the rest are regenerable with ``scripts/29``), the
population statistics and figures regenerate with the light-weight tier:

.. code-block:: bash

   python scripts/31_draft_numbers.py     # -> results/draft_numbers.json
   python scripts/32_make_figures.py      # -> the paper figures
   python scripts/38_build_manifest.py    # -> results/master_manifest.csv

Where to go next
================

* :doc:`pipeline` — the full methodology, the stage-by-stage script map, the
  locked decision framework, and the broadband GRB_Handbook roadmap.
* :doc:`manifest` — the master manifest schema and the sample bursts.
* :doc:`api` — the ``two_breaks`` package and the engine's public functions.

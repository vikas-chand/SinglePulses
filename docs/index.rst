Two_Breaks
==========

Time-resolved empirical spectroscopy of **106 bright single-pulse Fermi/GBM
gamma-ray bursts**, asking one question: is the spectral curvature beyond a
single break a **sub-dominant thermal photosphere** or a **second synchrotron
break**?

Each burst is fit, in every Bayesian-block time bin, with six photon models
(Band, CPL, SBPL, 2SBPL, Band+BB, CPL+BB), and the two pictures are compared
with information criteria. The accompanying manuscript is ``paper/two_break.tex``
(K. Sharma et al.).

.. note::

   **Status: provisional.** All numbers in these pages use an
   automatically-selected background catalogue; a human-verified background pass
   is in progress and the authoritative re-fit follows it. The qualitative
   conclusions are not expected to change. See :doc:`pipeline` (*Status &
   caveats*).

   **Relation to GRB_Handbook.** This repository is the single-pulse
   spectroscopy study; its reusable, burst-agnostic machinery (background
   selection, Bayesian blocking, the spectral engine, the per-GRB notebook, the
   master-manifest schema) is the seed for the planned, public **GRB_Handbook**
   full GRB-analysis pipeline. See :doc:`pipeline` (*Toward GRB_Handbook*).

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   pipeline
   manifest
   references
   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

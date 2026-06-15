============
Installation
============

``two_breaks`` is a thin importable package (version + repository paths + a
loader for the spectral engine) wrapping a numbered ``scripts/`` pipeline. The
*analysis* — detector selection, backgrounds, Bayesian blocking, and the
six-model spectral fit — is driven by those scripts and the end-to-end notebook;
see :doc:`pipeline`.

Two environments
================

The repository has a deliberate two-tier dependency structure:

**1. Light-weight tier (base Python).** Catalogue building, the master manifest,
the background picker, the machine tables, and figure generation need only:

* `numpy <https://numpy.org/>`_
* `scipy <https://scipy.org/>`_
* `astropy <https://www.astropy.org/>`_
* `matplotlib <https://matplotlib.org/>`_ (figures only; optional)

**2. Fitting tier (``threeML`` conda env).** The spectral engine
(``scripts/10``) needs the `Multi-Mission Maximum Likelihood framework (3ML)
<https://threeml.readthedocs.io/>`_ and ``astromodels``, alongside the Fermi
science tools. These are installed via conda, not pip.

Install the package
===================

Clone the repository and install in editable (development) mode so that source
changes are picked up without reinstalling:

.. code-block:: bash

   git clone https://github.com/vikas-chand/Two_Breaks.git
   cd Two_Breaks
   pip install -e .

Optional dependency groups are declared in ``pyproject.toml``:

.. code-block:: bash

   pip install -e ".[figures]"   # adds matplotlib
   pip install -e ".[docs]"      # adds sphinx, furo, myst-parser, nbsphinx

To verify the install:

.. code-block:: bash

   python -c "import two_breaks; print('two_breaks', two_breaks.__version__)"

The fitting environment (3ML + Fermi tools)
===========================================

Spectral fitting runs inside the ``threeML`` conda environment, and the Fermi
CALDB **must** be pointed at that environment before ``astromodels`` is imported,
or response loading fails:

.. code-block:: bash

   conda activate threeML
   export CALDB=$CONDA_PREFIX/share/fermitools/data/caldb
   export CALDBCONFIG=$CALDB/software/tools/caldb.config
   export CALDBALIAS=$CALDB/software/tools/alias_config.fits

.. note::

   The CALDB export is the single most common cause of a broken fitting run. Set
   it in every shell (or in the conda activate hook) before invoking any script
   that imports the engine. The light-weight tier does not need it.

Next steps
==========

See the :doc:`quickstart` to analyse one GRB end to end with the notebook, and
:doc:`pipeline` for the full methodology and stage-by-stage script map.

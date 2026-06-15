"""Two_Breaks -- time-resolved spectral analysis of single-pulse Fermi/GBM GRBs.

This package exposes version + path metadata and a loader for the production
spectral engine. The pipeline itself is the numbered ``scripts/`` (run in order);
see the documentation. The reusable, instrument-agnostic machinery is the seed
for the planned broadband GRB_Handbook pipeline.
"""
import os

__version__ = "0.1.0"

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA    = os.path.join(ROOT, "data")
RESULTS = os.path.join(ROOT, "results")
SCRIPTS = os.path.join(ROOT, "scripts")
PAPER   = os.path.join(ROOT, "paper")


def load_engine():
    """Import and return the production spectral engine (``scripts/10``).

    The file ``scripts/10_spectral_fit_burst.py`` has a digit-prefixed name, so
    it is loaded via :mod:`importlib` rather than a normal import. Returns the
    module, exposing ``build_spectrumlike_per_block``, ``fit_all_models``,
    ``get_canonical_bins``, the model builders, and the validity gate.
    """
    import importlib.util
    import sys
    path = os.path.join(SCRIPTS, "10_spectral_fit_burst.py")
    spec = importlib.util.spec_from_file_location("two_breaks_engine", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["two_breaks_engine"] = module
    spec.loader.exec_module(module)
    return module

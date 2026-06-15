# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# -- Path setup --------------------------------------------------------------
# Insert the repository root onto sys.path so that autodoc can import the
# `two_breaks` package. conf.py lives in <repo>/docs, so the repo root is one
# level up from this file's directory.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# -- Project information -----------------------------------------------------
project = "Two_Breaks"
author = "Khushboo Sharma & Vikas Chand"
copyright = f"2026, {author}"

try:
    from two_breaks import __version__ as release
except Exception:  # pragma: no cover - docs build should not hard-fail on import
    release = "0.1.0"
version = release

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "nbsphinx",
    "myst_parser",
]

# Generate autosummary stub pages automatically.
autosummary_generate = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]

# Do not execute notebooks at build time (they need the threeML conda env and
# the raw data); render the stored cell outputs instead.
nbsphinx_execute = "never"

# Source file suffixes (reStructuredText, Markdown via MyST, notebooks via nbsphinx).
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# -- Options for HTML output -------------------------------------------------
html_theme = "furo"
html_static_path = ["_static"]
html_title = "Two_Breaks"

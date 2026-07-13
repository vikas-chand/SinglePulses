"""Robust polynomial baseline fitters for the burst-extent pipeline.

`imodpoly_mad` is a standalone re-implementation of pybaselines.imodpoly
with one surgical change: the residual scale is the MAD-based robust
sigma (1.4826 * median(|r - median(r)|)) instead of `np.std(r)`. The
iteration scheme — initial peak masking, monotone clip at
baseline + num_std*deviation, weighted polyfit via Vandermonde
pseudo-inverse, relative-tolerance convergence — is identical.

Why MAD: `np.std(r)` is itself inflated by the peaks we are trying to
clip, so pybaselines.imodpoly under-clips on iteration 0 and slowly
tightens. MAD is robust to those peaks from iteration 0, so the very
first clip is already at the right scale.

This module is dependency-free beyond numpy.
"""
from __future__ import annotations
import numpy as np


def _mad_scale(r):
    """Robust 1-sigma estimator for residuals: 1.4826 * MAD."""
    med = np.median(r)
    mad = np.median(np.abs(r - med))
    return 1.4826 * float(mad)


def imodpoly_mad(t, y, poly_order=5, num_std=1.0, max_iter=250, tol=1e-3,
                 mask_initial_peaks=True):
    """imodpoly with MAD-based residual scale (std → MAD swap).

    Returns the smoothed baseline on the same grid as `t`.

    Parameters
    ----------
    t, y      : 1-D arrays, same length.
    poly_order: polynomial order (default 5, matches s03k).
    num_std   : multiplier on the residual scale for the iterative clip
                (default 1.0 — same as pybaselines.imodpoly default).
    max_iter  : max iterations (default 250).
    tol       : convergence tol on relative change in deviation
                (default 1e-3 — same as pybaselines).
    mask_initial_peaks : if True, zero-weight samples above
                baseline+deviation after the first fit before iterating
                (matches pybaselines default).
    """
    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float).copy()
    n = len(y)
    if n < poly_order + 2:
        return y.copy()

    # Vandermonde, weight array, weighted pseudo-inverse — same as pybaselines
    V = np.vander(t, poly_order + 1)
    weights = np.ones(n)
    sqrt_w = np.sqrt(weights)
    pinv = np.linalg.pinv(sqrt_w[:, None] * V)

    coef = pinv @ (sqrt_w * y)
    baseline = V @ coef
    deviation = max(_mad_scale(y - baseline), 1e-9)

    if mask_initial_peaks:
        weights[baseline + deviation < y] = 0.0
        sqrt_w = np.sqrt(weights)
        pinv = np.linalg.pinv(sqrt_w[:, None] * V)

    for _ in range(max_iter):
        y = np.minimum(y, baseline + num_std * deviation)
        coef = pinv @ (sqrt_w * y)
        baseline = V @ coef
        new_dev = max(_mad_scale(y - baseline), 1e-9)
        rel = abs(new_dev - deviation) / max(new_dev, 1e-9)
        if rel < tol:
            break
        deviation = new_dev

    return baseline

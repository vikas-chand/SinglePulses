# Handoff: orange baseline-aid diagnosis (from the LAT-loc terminal, 2026-07-17)

Vikas showed two approval-GUI screenshots (bn150630223 b0, bn171013350 b0) in another
Claude session; diagnosis was done there. **Action needed in THIS session.**

## Symptom
The orange `imodpoly_mad` selection-aid curve dives catastrophically (~1270 → ~550
counts/s) at the right edge of the light curve, and sags ~50–100 below the data
mid-range. The red 3ML window polyfit and its residuals are FINE — science output is
not corrupted; only the rater-facing aid is wrong.

## Root cause (three compounding factors)
1. **Partial-exposure final bin** — both bursts show an off-scale negative residual
   spike at the very last bin (end-of-file/binning-remainder artifact, rate collapses).
2. **imodpoly's one-sided clip** (`scripts/robust_baseline.py`) only rejects points
   ABOVE baseline+num_std·σ; low outliers keep full weight forever — the algorithm
   treats the broken last bin as gospel baseline.
3. **poly_order=5 edge leverage** (call sites `scripts/00_prototype_one_burst.py:208`
   and `:1104`) — degree-5 Vandermonde on raw t (uncentered, t^5 ~ 1e13) with a
   fully-weighted low point AT the boundary → the dive.

## Fix (bang-for-buck order)
1. Trim/mask partial bins before the aid fit (drop last bin, or exclude bins with
   exposure < bin width) at both call sites.
2. Add low-side rejection to `imodpoly_mad`: zero-weight points below baseline−5σ.
3. `poly_order=3` and center/scale t in the Vandermonde.
4. `num_std≈2–3` (with the MAD scale, 1.0 clips into the noise core → low bias).

## After fixing
**Re-open bn171013350** — Vikas hit Quit without selecting on it, so it needs to go
back through the approval GUI once the aid renders sanely.

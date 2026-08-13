# Approval sheet — GRB `<bnXXXXXXXXX>`

**Reviewer:** Khushboo Sharma  **Date (UTC):** `<YYYY-MM-DD>`  **Commit:** `<git rev-parse --short HEAD>`
**Products dir:** `<path>`  **PRODUCTS.md says:** `<N>/<M>` present

> Copy this file to `notes/approvals/<trigger>_approval.md`, fill it in as you go, and commit it.
> One burst at a time. **Approve each step before moving to the next** — if a step is not OK,
> stop there and write why; do not carry a doubt forward into the next step.
> Verdicts: **OK** / **OK-with-note** / **NOT OK** (say what you saw, not just that you disliked it).

---

## Step 1–2 · Data inventory & detectors — `<trig>_step1_inventory.png`
- [ ] every approved detector's DRM bar **brackets** the source window (PASS on each)
- [ ] angles sensible (NaI ≲ 60°; a BGO companion present)
- [ ] no "no response found" rows

**Verdict:** ______  **Note:** 

## Step 3 · Background — `<trig>_step3_background.png`
- [ ] the polynomial tracks the data **inside** both green windows
- [ ] its extrapolation **under the burst** is sane (no runaway curl, no crossing zero)
- [ ] no detector shows a coherent one-sided residual against the others (blockage signature, D5)

**Verdict:** ______  **Note:** 

## Step 4 · Source interval — `<trig>_step4_source.png`
- [ ] the source window covers the emission you can see
- [ ] if it overruns the background gap, the figure says so — that is an **accepted decision**, not a defect

**Verdict:** ______  **Note:** 

## Step 5 · Binning — `<trig>_step5_binning.png`
- [ ] blocks follow real structure (not splitting noise, not merging an obvious peak)
- [ ] per-block significance numbers are plausible for the light curve shown

**Verdict:** ______  **Note:** 

## Step 6 · Fits — `<trig>/spectral_evolution.png`, `ep_kt_correlation.png`, `spectral_fits.ecsv`
- [ ] parameter tracks evolve smoothly; no jump that no emission mechanism could make
- [ ] no Band α > 0 in a winning fit (collapsed-fit signature, L18)
- [ ] Ep values inside the fitted band (a railed Ep is stamped, not a measurement)

**Verdict:** ______  **Note:** 

## Step 7 · Temporal — `<trig>_step7_temporal.png`
- [ ] cumulative curves rise monotonically; t5/t95 land where the emission is
- [ ] T90 **shortens** toward higher energy (the expected band dependence)

**Verdict:** ______  **Note:** 

## Step 8 · Spectra — `<trig>_nuFnu_bin<N>_allmodels_overlay.png` (EVERY bin) + `_nuFnu_best_montage.png`
- [ ] data points and the winner curve agree; residual strip within ±3σ with no coherent run
- [ ] **no `[! PANEL!=ENGINE]` stamp** anywhere (if present: trust the table, flag it here)
- [ ] where several models overlie each other, the winner's **identity** is undetermined — note it

Per-bin quick table (add rows as needed):

| bin | winner | looks like a real preference? | note |
|---|---|---|---|
| 0 |  |  |  |
| 1 |  |  |  |

**Verdict:** ______  **Note:** 

## Step 9 · QC — `<trig>_step9_qc.png`
- [ ] blocks above the DECISIVE/STRONG lines are genuinely above them
- [ ] any blackbody with `3.92·kT` below 20 keV is treated as **edge-constrained** (L28), not a detection

**Verdict:** ______  **Note:** 

---

## Burst verdict

- **Overall:** OK / OK-with-note / NOT OK
- **Is the "winner" a real preference or a tie?** (a margin of ΔAIC ≈ 2 is a tie — say so)
- **Anything that looks like an artifact rather than physics:**
- **Anything the pipeline should have flagged and did not:**
- **Products missing** (from `PRODUCTS.md`) and whether the stated reason is acceptable:

## For the cross-system comparison
- [ ] I did **not** look at the other system's result for this burst before finishing mine
- [ ] Stage-1 selections were **adopted unchanged** (no re-picking)

**Signed:** Khushboo Sharma  **UTC:** ____________

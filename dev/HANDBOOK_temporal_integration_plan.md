# Integrating the LATBright temporal pipeline into grb_pipeline (temporally organized)

Source: survey of LATBright GRB260226A (workflow wve0kb6yq 2026-07-17) + direct code
inspection. Goal: port the VALIDATED temporal analyses into
`GRB_Handbook_Project/grb_pipeline/analysis/temporal.py` in the same ordered, data-flow
way, so Two_Breaks inherits them. **Foundation (Vikas's point): Stage-1 selection
(detectors + background windows + source/pulse interval) is locked first; every temporal
step consumes it.** T90 falls straight out of the source interval + background; lag / ACF
/ MVT / pulse-fit then apply to the selected pulse in the selected bands.

## The ordered temporal chain (LATBright → handbook)
Numbered as it runs; each row = one handbook method, keyed on the Stage-1 selection.

| # | Step | LATBright script | Method to port | Handbook status |
|---|---|---|---|---|
| 1 | **T90 / T50 / duration** (per energy band) | s02a | cumulative-count fractions (Kouveliotou 1993), bkg-subtracted on the approved windows | `calculate_t90/t50` exist ✓ — wire to the source+bkg selection |
| 2 | **Hardness ratio** (HR, HID) | s02b | band ratios (8-50/50-300/300-900) on BB bins | `hardness_ratio` exists ✓ |
| 3 | **MVT (GBM bands)** | s02g | **Bala `haar_power_mod`** (Haar structure fn) + MC S/N model + limit-aware UL | ⚠ REPLACE the ACF-0.5 placeholder with MVTfermi |
| 4 | **MVT (LLE) + phase-resolved** | s02h, s02i | same Haar method on 20-100 MeV | to add |
| 5 | **MVT sample context** | s02k | Golkhou+2015 (938 GRBs) MVT-vs-T90 overlay | to add (figure) |
| 6 | **Spectral lag — whole-burst DCCF + lag-energy** | s02c | **our DCCF** (Band-1997 CCF + asymmetric-Gaussian peak + MC), Liu+22 log bands | handbook has a DCCF — VERIFY it == s02c |
| 7 | **Cross-instrument HE lag** (NaI↔BGO/LLE/LAT) | s02c_he_lag_only | same DCCF across instruments | to add |
| 8 | **Channelwise lag (Shao 2017)** — t_peak(E), FWHM(E) | s02d | per-channel Gowri-pulse fit → Shao power law | to add |
| 9 | **Pulse-shape fitting** | s02f | **Gowri** 5-param profile (+ Norris/Kocevski options) width-vs-energy | `fit_fred_pulse` exists (Norris) — add Kocevski/Gowri |
| 10 | **HE rapid variability** | s02j | Aldrich & Nemiroff 2024 photon-bunching (LLE/LAT) | optional (bright LLE/LAT only) |
| 11 | **QPO search** | s02l | Lomb-Scargle / FFT periodogram (LLE/LAT) | optional |

**NOT ported for single pulses (Vikas):** MEPSA pulse identification (s02m) and per-pulse
lag (s02o) are multi-peak decomposition — a single pulse is already one pulse. These are
reserved for the LATER multi-pulse project.

## Figure sequence (mirror LATBright's temporal-figure order)
LATBright locks the foundation, THEN runs the chain:
Fig1 2D count map → Fig2 extended-emission/background window (t_safe) → Fig3 T90/T50
cumulative → Fig4 T90-vs-energy → Fig5 FAP calibration → **[foundation locked]** → MVT(GBM)
→ whole-burst lag → lag-energy → cross-instrument HE lag → pulse fit → (HE variability/QPO).
For Two_Breaks single pulses the same order applies, minus the MEPSA step.

## The port (what to actually do)
1. **Drop MVTfermi (Bala's) into grb_pipeline** — `haar_power_mod.py`, `mvt_mc_parallel.py`,
   the S/N model `.npz`, denoise helpers — and REPLACE `minimum_variability_timescale`
   (the ACF-0.5 placeholder) with a call to it (Haar + MC + limit-aware UL).
2. **Verify** the handbook `discrete_cross_correlation`/`compute_spectral_lag` reproduces
   LATBright s02c on a test burst (Band-1997 DCCF + asymmetric-Gaussian + MC); if not,
   port s02c's implementation.
3. **Add Kocevski (KRL) and Gowri profiles** to the pulse-fit menu alongside Norris.
4. **Wire the chain to the Stage-1 selection**: each method takes the approved
   detectors + background windows + source interval (from `background_intervals*.ecsv`),
   so T90 → lag/MVT/pulse all flow from one selection — exactly the Two_Breaks Stage-1 output.
5. Mirror `METHODS_pulses_mvt_lag.md` into a handbook methods doc.

## Timing
Temporal analysis is a LATER phase (the current prototype is spectral). Do this port when
we reach the temporal Results — OR now in parallel if going full-force. Not blocking.

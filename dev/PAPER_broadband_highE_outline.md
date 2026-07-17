# Paper outline — a spectral-SHAPE HUNT across single-pulse Fermi GRBs

**Thesis (Vikas 2026-07-17):** ONE paper. We **hunt for all kinds of spectral SHAPES**
single pulses take, across the **WIDEST energy band we can build for each burst**
(NaI+BGO always; +LLE +LAT wherever the data exist — joint fit). We fit the full
empirical-model menu and let the data pick. **Two-breaks are NOT the target — they are
one shape that appears as a CONSEQUENCE if present.** Burgess-style Ep–kT was the OLD
main focus; demote it to one possible finding. "Do our own analysis with all empirical
models, report what we find. That's it." This RE-FRAMES the existing `paper/two_break.
tex` (do NOT rewrite it until this outline is approved — propose-outline-first rule).

Two organizing principles:
1. **Shape-first, model-agnostic** — the deliverable is the census of shapes (sharp vs
   broad peak, single vs double break, thermal bump, high-E cutoff/saddle/extra-PL),
   not a defense of any one model.
2. **Widest band per burst** — every fit uses every instrument that has usable data for
   that burst/interval; LLE/LAT are pulled in exactly where they help.

Working title (options):
- "The spectral shapes of single Fermi GRB pulses: a wide-band empirical survey"
- "Hunting spectral shapes in single-pulse GRBs with the widest achievable band
  (Fermi GBM + LLE + LAT)"

## 1. Introduction
- Single-pulse GRBs = the clean laboratory: one rise–peak–decay, so a spectral
  shape/evolution is unambiguous (Basak & Rao, Lu, Yu lineage).
- We do NOT assume a model. We fit a broad menu of EMPIRICAL models and let the data
  pick — Band, CPL, SBPL, the free-smoothness SBPL, the double-break 2SBPL, thermal
  (+BB) variants, and — where LLE/LAT extend the band — high-E combos (extra PL / cutoff
  / Guiriec saddle). Report the empirical picture: which shapes, how often, how they
  evolve, what correlates.
- Frame two-break curvature and Ep–kT as *among the findings*, not the thesis.

## 2. Sample + data
- The 106 single-pulse Busby-selected Fermi/GBM sample. NaI (8–900 keV, K-edge mask)
  + BGO (0.3–40 MeV) for all; **LLE (30–100 MeV) + LAT (>100 MeV) for the subset that
  has them** (13 with LLE, 10 with real ≥3σ signal; N with LAT). Table flags who has what.

## 3. Methods
- Human Stage-1 selection (detectors θ≤50°, per-detector backgrounds, source interval),
  gated + stamped. (One line: the AI-vs-human benchmark is a *separate* methods paper.)
- Binning: fine GBM Bayesian blocks for all; **for LLE bursts, an extra coarse
  LLE-driven grid** so the high-E component has counts (two-tier). Joint NaI+BGO+LLE(+LAT).
- **Full empirical-model menu** (15): Band, CPL, SBPL, DSBPL, SBPLfree, DSBPLfree,
  Band+BB, CPL+BB, + high-E combos (Band+PL, Band+CPL, CPL+PL, CPL+CPL, BandR+CPL,
  Band×Cut, SBPL×Cut). MINOS errors, NaI eff-area reference, AIC/BIC with ΔAIC≥10 +
  valid-parent gate. νFν AND N(E) shown; peak-sharpness W_HM.

## 4. Results (report empirically — no forced story)
1. **Best-model census** — what wins, per block and per burst, gated.
2. **Spectral shape** — Band vs SBPL vs CPL; peak sharpness (W_HM, SBPLfree smoothness);
   curvature / low-E break (2SBPL) vs thermal (+BB).
3. **High-energy component** (LLE/LAT bursts) — how often a cutoff / extra-PL / saddle
   is required above the peak; cutoff energies; which bursts.
4. **Parameter evolution** across the pulse (Ep, α, β, kT).
5. **Correlations** as findings (Ep–kT if it appears, ν_m–ν_c, flux–index) — reported,
   not assumed.
6. **Case studies** — 160625B, 130427A (2nd pulse), 110721A.

## 5. Comparison to the literature
Ravasio, Guiriec, Oganesyan/Ronchi, Vianello/Ajello — fit independently, then compare
(verify bibcodes before citing).

## 6. Discussion (light) + 7. Summary
What the empirical shapes suggest (synchrotron curvature limit, thermal fraction, a
distinct high-E zone) — stated as implications, not claims. Numbers PENDING the
human-arm two-tier fits now running on the 13-burst prototype; flag all provisional.

## Mapping to the existing two_break.tex
Existing draft is already Li-style, 14pp, 6-model, curvature/Ep–kT-framed. Reframe =
(a) broaden the model menu to 15, (b) fold in LLE/LAT joint analysis, (c) soften
"two-break is THE story"/Burgess-reproduction into "here is the empirical census."
Propose the section-by-section edit list AFTER this outline is approved.

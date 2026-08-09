# Burgess+2014 physical model — exact formulas (transcribed from the PDFs)

Sources on disk: `Michael_Burgess_2014_ApJL_784_L43.pdf` (Letter, Eq. 1) and
`Burgess_2014_ApJ_784_17_companion.pdf` (companion, Eqs. 3–12, §2, p.3–4).
Transcribed 2026-07-27; page images read directly. Purpose: the spec for a
construction-faithful Ep–kT reproduction (always-on BB, rigid continuum).

## 1. Electron distribution (slow-cooling parameterization)
Letter Eq. (1) (= companion Eq. 2):

    n_e(γ) = n_0 [ (γ/γ_th)² e^(−γ/γ_th)  +  ε (γ/γ_th)^(−δ) Θ(γ/γ_min) ]

with Θ(x) a step function: Θ(x)=0 for x<1, Θ(x)=1 for x>1.
(A relativistic Maxwellian + a high-energy power-law tail.)

## 2. Photon spectrum: convolution with the synchrotron kernel
Companion Eq. (3):

    F_ν(ℰ) ∝ ∫₁^∞ n_e(γ) 𝓕(ℰ/ℰ_c) dγ

Companion Eq. (4) — single-particle synchrotron emissivity:

    𝓕(w) = w ∫_w^∞ K_{5/3}(x) dx          (K_{5/3}: modified Bessel, 2nd kind)

Companion Eq. (5) — characteristic synchrotron photon energy scale:

    ℰ_c = E★ γ² ,   E★ ≡ [3ΓB/(2B_cr)] m_e c² ,   B_cr = 4.41×10¹³ G

## 3. Parameter freezing (THE key construction choice)
Six spectral parameters in principle: n_0, E★, δ, ε, γ_th, γ_min. Quoting §2:
- "we fix γ_th, γ_min, and ε due to fitting correlations"
- "The parameters E★, γ_th, and γ_min all directly scale the peak energy of the
  spectrum but do not alter its shape and thus cannot be independently
  determined. For this reason we chose values of **γ_th = 300 and γ_min = 900**
  for all fits and **left E★ free to be constrained from the fit**."
- ε "numerically fix[ed] … to the small value of (γ_min/γ_th)² × e^(−γ_min/γ_th)"
  → (900/300)² e⁻³ ≈ 0.448 — chosen "so that there is no discernible
  discontinuity between the thermal and non-thermal parts."
  ⚠ Note an apparent textual tension: earlier on p.3 the viability condition
  (citing Baring & Braby 2004) is stated with the power-law component
  dominating; transcribe-don't-resolve — read p.3 before leaning on ε.
- Fitting is "insensitive to the exact value of the product ΓBγ²" given the
  Appendix constraints.

**⇒ Three free parameters: E★ (peak scale — UNBOUNDED), δ, n_0.**
"Compared with the Band function's four fit parameters this model is simpler
yet tied to actual physical processes." E★ is "linearly related to the Band
function's Ep".

## 4. Fast-cooling variant (tested and rejected for these bursts)
Companion Eq. (6) — injected distribution:

    N_e^inj(γ) = n_e (δ−1) γ_min^(δ−1) γ^(−δ) ,   γ_min ≤ γ

Eq. (7) — continuity equation (Blumenthal & Gould 1970):

    ∂n_e(γ,t)/∂t + ∂/∂γ[ γ̇ n_e(γ,t) ] + n_e(γ,t)/t_esc = N_e^inj(γ)

Eq. (8) — steady-state solution (γ/γ̇ ≪ t_esc):

    n_e(γ,t) ≈ (1/γ̇) ∫_γ^∞ N_e^inj(γ′) dγ′

Eq. (9) — synchrotron cooling rate:

    γ̇ = −(4/9)(r_0 c / r_g²) γ² ,   r_g = m_e c²/(eB) ,  r_0 = e²/(m_e c²)

Eq. (10) — cooled broken-power-law electron distribution:

    n_e^cool ∝ (n_e γ_min / γ²) · min{ (γ/γ_min)^(−(δ−1)), 1 } ,  γ_cool ≤ γ

Asymptotic low-energy photon index −3/2 ("second line of death"); rejected
because GBM/BATSE spectra are mostly harder AND the fast-cooled curvature
around the νFν peak is "much broader than that observed".

## 5. Blackbody component
Companion Eq. (11):

    F_BB(ℰ) = A ℰ³ · 1/( e^(ℰ/kT) − 1 )

"A is the normalization and kT scales the energy" — **both free, no stated
range.** Physical relations used for INTERPRETATION only (not constraints):
kT decay T ∝ r_ph^(−2/3), T ∝ t^(−2/3) (coasting), broken power-law kT(t) with
post-break index ≈ −2/3 (Ryde & Pe'er 2009), and Eq. (12):

    F_BB = N σ_sb T⁴

## 6. The fitted relation (Letter §3)
Power law fit to the per-bin (Ep, kT) pairs of each burst:

    Ep ∝ kT^α

Per-burst α (Letter Table 1): 081224A 1.01±0.14 (baryonic) · 090719A 2.33±0.27
(magnetic, μ=0.39±0.01) · 100707A 1.77±0.07 (μ=0.42±0.01) · **110721A 1.24±0.11
(baryonic)** · 110920A 1.97±0.11 (μ=0.4±0.01) · 130427A 1.02±0.05 (baryonic).
F_BB/F_tot: 0.29, 0.27, 0.33, **0.01 (110721A!)**, 0.39, 0.22.
Letter Fig. 3 caption: "The relatively fewer data points for GRB 110721A
(panel d) make the correlation difficult to measure."

## Fitting protocol (companion §3, p.5 — verified 2026-07-29)
- Tool: **RMFIT v4.1** + the custom synchrotron module from B11. Four photon
  models compared per bin: Band, Band+BB, synchrotron, synchrotron+BB.
- **BB inclusion rule — BURST-level, not per-bin:** "If the addition of
  blackbody component did not make a significant improvement of at least
  **10 units of C-stat** … for any time bins of a particular GRB, then we did
  not include the blackbody component in the analyzed fits for that burst."
  → 5 of the 8 sample GRBs kept the BB; within an included burst the BB is fit
  in EVERY bin (no per-bin significance cut). (Note the family resemblance to
  our locked ΔAIC≥10 doctrine.)
- **No ordering constraint kT < Ep and no published parameter ranges** —
  nothing in the text restricts where kT may sit relative to the synchrotron
  peak (RMFIT-internal defaults unpublished).
- Binning: Bayesian blocks (Scargle 2013) on brightest-NaI + BGO TTE combined,
  **prior of 8**; change points mapped to the other detectors. Sample: peak
  flux > 5 ph/s/cm² (10 keV–40 MeV), single-peaked; 081224A & 110721A included
  LLE.

## Implementation notes (for a faithful reproduction in 3ML)
- Continuum: Eqs. (1)+(3–5) with γ_th=300, γ_min=900, ε=(γ_min/γ_th)²e^(−γ_min/γ_th)
  frozen; free = {E★ (or equivalently the νFν peak), δ, n_0}. NO bounds on the
  peak scale (native-threeML route: astromodels custom function or a table model).
- Thermal: Eq. (11) Planck, A and kT free, no bounds.
- Fit BOTH components in EVERY bin (always-on BB; no significance selection);
  the (Ep, kT) pair enters the relation wherever both are constrained.
- Bins: Bayesian blocks on the brightest NaI, 8–300 keV (Letter Fig. 1 caption).

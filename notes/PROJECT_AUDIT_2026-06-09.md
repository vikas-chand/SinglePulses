# Two_Breaks — Full Systematic Audit (2026-06-09)

**Method.** 6 parallel audit dimensions (spectral engine, background/binning,
statistics, data integrity, paper-vs-Li-style, presentation), 28 agents, 411
tool calls. Every critical/major finding was **adversarially re-derived by an
independent verifier** with code+data access. Score: **22 verified findings →
21 confirmed REAL, 1 REFUTED** (in our favor). Findings below quote the
verifier's *corrected* assessment, not the original claim.

---

## 1. Executive verdict (your six questions)

| Question | Verdict |
|---|---|
| Systematic? | **Yes** — pipeline accounting is exact (1057 bins provably from clean blocks ← clean bkgs; 6 broken bursts genuinely fixed). One gap: no provenance stamps → stale-mix risk in the Khushboo re-run. |
| Faithful to methods/docs/tools? | **Mostly** — the statistical core is verified correct (factor-of-2, AIC k-counts, LRT dof, pgstat, poly-order-by-LRT all exactly right). But **~8 Methods-text sentences do not match what the code does** (list in §3). None invalidates the science; all must be reconciled. |
| Analysis correct, highest standards? | **Core is sound and conservative**, with 3 real gaps: kT-significance rule mismatch (results *strengthen* when done as stated), DSBPL convergence guard missing (two-break 11% = lower limit), IT/HTS classifier ordering artifact (conclusion-reversing). |
| Results well collected? | **Yes** — catalog complete, deterministic, every paper number reproduces to the digit; BB-OOM worry settled (130427A's 65 Band+BB fits are genuine; the old memory was stale). |
| Presentable in Li style? | **Structure & voice faithful** (dedicated reviewer confirmed section-by-section). Missing: bin-accounting paragraph, (n/N) on the 92% claim, a real curvature table. |
| Paper written well? | **Strong base, honest abstract**, but 1 false sentence (§2.2), several wording fixes, and **figures are NOT submission-ready** (4 confirmed majors). |

---

## 2. CRITICAL (fix before showing anyone)

### 2.1 kT "BB-significant" uses LRT>0, not the paper's own ≥9.2 [stats/critical]
`scripts/31` takes kT/F_BB from any bin with LRT>0 → 900/1057 bins (85%)
"significant", internally contradicting the 166-curvature-bins narrative.
Re-run under the stated LRT≥9.2 rule (verifier confirmed, both implementations):

| quantity | printed | LRT≥9.2 (branch-kept) | LRT≥9.2 (re-gated) |
|---|---|---|---|
| N kT bins | 900/732 | 271 | 396 |
| median kT | 14.8 keV | 21.5 | 26.2 |
| kT–F_ph ρ | 0.22 | **0.40** | 0.30 |
| Ep–kT ρ | 0.27 | **0.55** | 0.60 |
| Burgess positive | 69% of 70 | 88% of 17 | 91% of 32 |
| 130427A ρ | 0.62 | 0.75 | 0.71 |
| F_BB/F_tot med | 0.049 | 0.058 | **0.0092 (!)** |

→ Claims **strengthen** under the stated rule, but every printed "significant"
number is computed under a different rule than defined. Decision needed:
which implementation (F_BB/F_tot differs 6×). Then regenerate + refill.

### 2.2 §2.2 "visually verified by eye" is currently false [paper/critical]
Past-tense claim contradicted by its own footnote (numbers are auto-bkg).
Rewrite to describe the actual automated peak-centered selection with human
verification *in progress*; restore the sentence only after Khushboo's pass.

---

## 3. Methods-text ↔ code mismatches (all verified REAL)

1. **§2.3 "background-subtracted light curve"** — BB actually runs on the RAW
   rate (constant bkg + measures fitness ⇒ same change points, so a
   documentation error, not a results error). Unmentioned: emission-window
   pre-trim, 4.5σ end-trim, p0=0.05/64 ms retry (2 bursts).
2. **"Brightest NaI"** — actually the first BCAT-masked NaI; not the brightest
   in **79/106** bursts (fits use all detectors; affects bin sharpness only).
3. **"Backgrounds each ~50–150 s"** — auto catalog caps at **80 s**; 114/418
   pre-windows <50 s; bn100614498 has a zero-width pre-window on all 5 dets.
4. **Validity gate** — silent fallback lets a railed model win BEST_AIC in
   **43/1057** bins (census + machine-readable table affected; 4 bursts flip
   modal model; printed rows + headline numbers unaffected).
5. **BB multi-start** — conditional in code (skips strong detections),
   described as unconditional.
6. **K-edge mask** — code masks 33–40 keV; paper says 30–40.
7. **"D'Agostini errors-in-both-variables"** — actually **unweighted scipy ODR**
   with rms scatter (4 places in tex incl. acknowledgments). Materially
   consequential: true D'Agostini with the available per-point errors gives
   **slope 0.46±0.05, σ_sc 0.38** vs published 1.05±0.06/0.50 (OLS: 0.56).
   → Decide: implement the real method (weakens "slope ≈ 1") or relabel as ODR
   and justify. **This is the biggest scientific decision in the audit.**
8. **§2.6 kT rule** — see §2.1.

---

## 4. Analysis-quality findings

### 4.1 IT/HTS split is an ordering artifact [stats/major — conclusion-reversing]
41 of the 47 "IT" bursts ALSO satisfy the HTS criterion (4 have perfectly
monotonic Ep decay, r=−1.0, yet are labeled IT). IT-first ordering → 62%/30%;
HTS-first → **8%/84%** — a complete reversal. Threshold 0.2/0.3/0.4 moves IT
57/47/39. The §5.1 claim "IT more common than Lu/Basak" rests entirely on the
ordering. Fix: rise-phase classifier (Lu-style: Ep rising WITH flux during the
rise) or report both orderings and drop the comparative claim.

### 4.2 DSBPL has no convergence guard [engine/major]
132/992 bins have LRT_DSBPL_SBPL < −1 (min −395; 67 below −9.2 are clear
optimizer failures). Since genuine-two-break requires LRT>9.2, the **11%
two-break fraction is a lower limit** (say so in the paper, or add a DSBPL
restart seeded from the SBPL solution and re-fit). ν_m–ν_c itself is robust:
gating entrants at LRT≥0 moves ρ only 0.568→0.580, slope 1.049→1.060.

### 4.3 "92% of all bins … six models indistinguishable" [stats/major]
It's a **top-2 gap** statistic over 950 bins with ≥2 valid fits (875/950 =
92.1%); the literal all-six statement holds in only **58%**; "of all bins"
(1057) would be 83%. Fix: "no single model is decisively preferred over the
next-best (ΔAIC<10) in 92% (875/950) of bins with ≥2 valid fits."

### 4.4 Smaller items
- Within-burst ν_m–ν_c pooled Spearman is dof-inflated, but the cluster-honest
  per-burst test **confirms** the claim (median per-burst ρ=0.50, 41/54
  positive, sign-test p=2×10⁻⁴) — report it this way.
- Constrained ν_m–ν_c (both breaks <100% error): **ρ=0.674, N=253, slope
  0.97±0.06** — robust to threshold (0.68–0.69 at 30–50% cuts). A free
  robustness sentence; currently unmentioned.
- Curvature-split design asymmetry: empirically negligible (symmetric rule →
  85/11; 0 bins affected by the BB pre-filter). 89/11 robust.
- Basak & Rao comparison is apples-to-oranges: our like-for-like per-bin
  fraction is **44%** vs their 63.4% (mild disagreement); our 74% is per-burst
  α_max. Quote both honestly; replace "coincides".
- BIC's N uses all 128 channels instead of active ones (ΔBIC shift <0.4 —
  negligible; fix at next refit).

### 4.5 REFUTED finding (good news)
"130427A Ep∝kT^0.67 not reproducible" — **refuted**: ODR on the clean catalog
gives 0.669±0.099. Residual: persist the slope in draft_numbers.json and state
the estimator in the text (OLS gives 0.46).

---

## 5. Data integrity

- **Catalog chain verified end-to-end**; every checked number reproduces.
- **BB-OOM memory STALE**: bn130427324 has 65 genuine Band+BB fits (53 valid,
  83 logged multistart recoveries) — the Burgess anchor is solid. (Memory updated.)
- Fit failures are not random: CPL failures cluster in the 4 brightest Gold
  anchors; DSBPL failures remove two-break testability exactly where S/N is best.
- **Provenance gap [major]**: scripts/29 resume-skip + no input hashes ⇒ a
  partial re-run after Khushboo's backgrounds would silently mix old/new fits.
  **Mitigation: write the re-run to a fresh out-root** (+ stamp input hashes).
- MINOS asymmetry on Ep is real (39% of bins >20%, skewed +) but all headline
  stats are rank-based — figure-quality nicety only.

---

## 6. Paper & figures

**Li fidelity:** structure mirrors Li exactly; abstract follows the template
shape; tense/voice/(n/N) discipline largely good. Gaps: bin-accounting sentence
(792/732/890/950/100/70/68 all undefined), (n/N) on the 92% claim, §3.4 cites
Table 5/Fig 3 for a curvature classification that appears in **no** table or
figure (and the promised 3-way split is only ever computed 2-way), five
remaining (n/N) violations, "thermal proxy (BB+SBPL)" names a model never fit
(we fit Band+BB/CPL+BB), median±std mixing.

**Figures (4 confirmed majors — referee-bounce level):**
1. fig_evol right column: severe label/title collisions (shared hspace=0.08
   gridspec); two panels have NO visible x-label.
2. fig_dist: 9.6-in figure in a single column → ~3.5 pt effective fonts.
   Promote to `figure*` or rebuild at column size.
3. fig_corr (b): the highlighted 130427A series skips the constrained-error
   mask → a red bar spanning the full panel width (2 offending bins).
4. fig_corr (c)/(d): twiny dual-x design — interleaved unrelated scales; the
   figure cannot visually demonstrate the collapse it exists to show. Split
   into side-by-side subpanels sharing y.
Minor: −2/3 labels under the legend; legend-N confusion; ν_c pile-up near the
8-keV edge (26% of breaks <15 keV — add a robustness sentence); α_max up to
+1.9 unexplained; Type 3 fonts (set pdf.fonttype=42); stale docstring.

---

## 7. Verified strengths (what the audit confirmed is RIGHT)

- 3ML factor-of-2, AIC/BIC formulas, per-model k counts, LRT dof, pgstat path:
  **all independently verified correct** against installed 3ML/astromodels.
- clean_blocks provably derived from background_intervals_clean.ecsv
  (deterministic recompute matches all 106); block accounting exact (1057).
- Poly-order-by-LRT claim **exactly** matches installed 3ML (grades 0–3, 2ΔlnL≥9).
- band_flux_mc matches astromodels to 6.7×10⁻¹⁶.
- BB seed-poisoning fix verified operating (0 railed bins in 130427A).
- Every cross-referenced number in the paper reproduces; internal consistency
  of 89%/11% across abstract/§3.4/Summary/Table 7 exact.
- Abstract honesty (curvature-absorption caveat), within/between decomposition
  attempted at all, both ΔAIC thresholds reported: good practice.

---

## 8. Action plan

**A. Now (no refit needed — scripts/31/32 + tex):**
fix kT gate to ≥9.2 (after choosing implementation) and refill; fix IT/HTS
(rise-phase or dual-report); rephrase 92%; resolve D'Agostini (relabel-as-ODR
or implement; refresh 4 tex sites); rewrite §2.2/§2.3 honestly; add bin
accounting; add curvature table + fix §3.4 cross-ref; Basak comparison fix;
add constrained-ν_m–ν_c sentence; all 4 figure majors; minor figure/caption items.

**B. At the Khushboo re-run (engine, task #27):**
DSBPL restart seeded from SBPL; BEST_AIC `NONE_PHYSICAL` label (or
BEST_AIC_VALID column); BIC active-channel N; K-edge text/code alignment;
provenance stamps; **fresh out-root**.

**C. Decisions for the 5 pm discussion:**
1. kT-significance implementation (branch-kept vs re-gated → F_BB/F_tot 0.058 vs 0.009).
2. ν_m–ν_c estimator to publish: OLS 0.56 / ODR 1.05 / D'Agostini-with-errors 0.46.
3. IT/HTS classifier definition (rise-phase vs dual-report).
4. Whether 11% two-break is published as a lower limit or after a DSBPL-guard re-fit.

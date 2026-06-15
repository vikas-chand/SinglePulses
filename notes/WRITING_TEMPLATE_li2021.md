# Writing template — write the Two_Breaks paper like Li et al. (2021, ApJS 254, 35)

Li+2021 ("Bayesian Time-resolved Spectroscopy of Multipulse GRBs") is our style
model: same instrument (Fermi/GBM), same empirical-model, time-resolved approach,
same kind of correlations (F–α, F–Eₚ, α–Eₚ), and the same Gold/Silver/Bronze
tiering we already use. This file encodes its voice + structure so Phase 6 can be
written directly. (Source PDF: `Li_2021_ApJS_254_35.pdf`; full text `/tmp/li2021.txt`.)

## A. Voice / style fingerprints (imitate these exactly)
1. **Percentage-then-(n/N), always.** Every quantitative population claim:
   *"We find that about two-thirds (63/103 = 61%) of the pulses show a
   flux-tracking pattern."* → write *"…78% (64/82) of the curved bins are
   thermal-or-degenerate."* This is the paper's single biggest fingerprint.
2. **Tense/voice:** Methods & Results in **present-tense first-person-plural
   active** — "We use", "We find", "We adopt", "We compare". **Summary** flips to
   past — "In this paper, we performed… we found…".
3. **Uncertainties:** value ± 1σ, convention stated once ("uncertainties at the
   1σ (68%) Bayesian credible level"); populations as **mean ± sd**
   (*α = −0.84 ± 0.35*).
4. **Topic-sentence paragraphs:** short declarative topic sentence → the
   numbers/fits → an interpretive close ("This indicates/implies…").
5. **Graded hedging:** indicates / appears to / could / might / it can be argued
   that. Strong claims only where the data warrant; isolate caveats in their own
   sentences, often opened with **"However,"**.
6. **Citations:** author-year natbib, dense, grouped, almost always prefaced
   "e.g.,": *(e.g., Kaneko et al. 2006; Yu et al. 2019)*.
7. **Signposting:** liberal self-cross-references — "see Section 5.2",
   "as discussed in the main text". Subsections open with turn-of-attention
   phrases — "We now investigate…", "Turning to the parameter correlations…".
8. **Method-then-justification:** state a choice, immediately justify with
   since/because/in order to ("…we only select bins with S ≥ 20, since
   Dereli-Bégué et al. 2020 show S ≈ 15–20 is needed to constrain the shape").
9. **Enumeration:** inline (i)…(ii)…(iii) for implications; First,/Second,/Third,
   for multi-point arguments; numbered lists for categorical definitions
   (Gold/Silver/Bronze).
10. **Figure/table refs** parenthetically at sentence end ("…softening is again
    revealed (Figure 3)") or as the subject ("Figure 2 shows…").

## B. Section-by-section outline (our paper, Li structure)
**Abstract** (~1 dense paragraph, ~14 lines): field one-liner → method (large
uniform single-pulse sample, time-resolved, empirical models) → headline results
in percentage-(n/N) form → one honest-limitation clause → one implication.

**1. Introduction** (~8–13 paragraphs): (a) phenomenology — variability +
hard-to-soft spectral evolution; (b) the two emission pictures laid out
**symmetrically**: photosphere/quasi-thermal (BB) vs optically-thin synchrotron
(2SBPL, ν_c & ν_m); (c) why single pulses are the cleanest probe; (d) what *this*
paper does — a large uniform single-pulse sample, empirical models as the
model-agnostic probe, asking whether Burgess+2014's thermal–non-thermal relation
appears at scale and what other properties emerge; (e) roadmap paragraph.

**2. Methodology** (6 subsections, present-tense recipe):
- 2.1 Initial Burst Selection — Busby & Lazzati single-pulse score ≥ 0.9983,
  fluence cut, → 106 bursts.
- 2.2 Detector, Source & Background Selections — NaI ≤ 50–60°, brightest BGO, LLE
  where present; **backgrounds human-selected (Khushboo)**; polynomial order via LRT.
- 2.3 Light-curve Binning — Bayesian Blocks (Scargle 2013) on the brightest NaI,
  + significance cut; justify time-resolved.
- 2.4 Block/Sample Definition — **Gold/Silver/Bronze** tiers as a numbered list,
  carried as a Table 2 column (used later for a robustness check).
- 2.5 Spectral Fitting — the **six empirical models** (Band, CPL, SBPL, 2SBPL,
  Band+BB, CPL+BB) with equations; ML (pgstat) [+ priors if Bayesian]; the BB
  multi-start. **MODEL DESCRIPTIONS sourced from:** Band → Band et al. 1993;
  2SBPL functional form → **Ravasio et al. 2018** + synchrotron ν_c/ν_m
  interpretation (slopes −2/3 slow, −3/2 fast) → **Ravasio et al. 2019**;
  Band+BB / CPL+BB multi-component thermal+non-thermal (sub-dominant Planck,
  simultaneous fit, F_BB/F_tot) → **Guiriec et al. 2011, 2015**; BB photosphere →
  Ryde/Pe'er. A ready demonstration draft is in
  `notes/draft_section_2.5_models.tex` (Li voice + these sources). On disk:
  Ravasio_CutoffInsights.pdf (confirms 2SBPL framing), Guiriec_2015.pdf.
- 2.6 Model Selection — AIC/BIC + nested LRT + physical-validity gate; state the
  ΔAIC ≥ 10 (inconclusive) threshold and **justify with a citation** (the DIC
  analog of Li's ΔDIC > 10 ≈ 99%, Acuner+2020).

**3. Observational Properties** (results core, organized by quantity):
- 3.1 Parameter Distributions — α (median ≈ −0.75), Eₚ, kT, flux, duration;
  per-tier; K-S tests between tiers (Table). Best-fit Gaussian overlays.
- 3.2 Spectral Evolution — classify Eₚ(t) and α(t) vs the count light curve into
  hard-to-soft / flux-tracking / other; report fractions percentage-(n/N); per-burst.
- 3.3 Parameter Correlations — 3.3.1 F–α, 3.3.2 F–Eₚ, 3.3.3 α–Eₚ (individual +
  global), each with the intrinsic-scatter fit.
- 3.4 Curvature & the two pictures (OUR addition) — thermal-proxy vs two-break
  split (78%/22%); Eₚ–kT (Burgess); the two 2SBPL breaks ν_m–ν_c (with the
  within/between-burst decomposition, honestly); kT vs brightness (Mei analog).

**4. Assessment of Compatibility with Emission Models** (theory recap → tests):
- 4.1 Spectral Shape — α vs the synchrotron lines-of-death (−2/3, −3/2) and the
  α_max–Eₚ plane with SCS/NDP limiting lines; "photospheric preference only for
  α > −0.5" (Acuner+2020); F_BB/F_tot.
- 4.2 Spectral Evolution & Correlations — which picture the F–α / α–Eₚ / Eₚ–kT /
  ν_m–ν_c trends favor; illustrative Bayesian-evidence on one or two bins rather
  than full physical fits everywhere.

**5. Discussion**:
- 5.1 Comparison with the Burgess+2014 single-pulse sample (Eₚ–kT) and Mei+2025
  (ν_c–L); isolate the cleanest subsample (Gold; bn110721200/bn130427324) to show
  a result holds — Li's robustness-defense pattern.
- 5.2 The two-break relation, honestly (within- vs between-burst; cooling-regime
  ν_m/ν_c).
- 5.3 Implication for the radiation process — jet composition from the Eₚ–kT slope
  (μ; baryonic/magnetic); the empirical-model caveat (continuum can absorb the BB).

**6. Summary** (past tense, ~7 paragraphs): restate sample size, then one
paragraph per main result in the same order derived, bulleted-prose.

**Appendices:** A — per-burst atlas (Eₚ, α, F, β evolution; F–α, F–Eₚ, α–Eₚ per
burst). B — machine-readable per-block fit table (all 6 models' params + selection
statistic, one example burst shown as a template).

## C. Figures (Li conventions: fixed per-tier color code stated once; dashed lines
connecting same-burst points; Gaussian overlays on distributions; dual y-axes for
tier-vs-full-sample)
- F1: sample/tier counts (bursts per tier | blocks per tier).
- F2: distributions of α, Eₚ, kT, F, duration, one curve per tier.
- F3: α_max and Eₚ,max evolution (same-burst dashed) + vs duration.
- F4: one **example burst** — Eₚ(t), α(t), kT(t), νFν with the LC overlaid; below,
  its F–α, F–Eₚ, α–Eₚ scatters. (Replaces the teaching cartoons.)
- F5: classification histograms (Eₚ-evolution, α-evolution, correlation types).
- F6: α_max vs Eₚ with the SCS/NDP + (−2/3, −3/2) lines — the emission-model test.
- F7: the curvature split + Eₚ–kT + ν_m–ν_c (intrinsic-scatter fits annotated).
- F8: comparison to Burgess (Eₚ–kT) / Mei.
- Appendix A1–A7: per-burst evolution + correlation atlas.

## D. Tables (Li-style)
- T1 Global per-burst properties: GRB, (z if any), T90±, detectors (brightest in
  parens), source interval, background intervals, N_bins, tier.
- T2 Per-block/per-burst: GRB, block/tier, ΔT, N(S≥…), tier grade, preferred model.
- T3 Parameter means ± sd per tier (best model): tier, model, N_spec, α, Eₚ, kT, F.
- T4 K-S P-value matrix between tiers for α and Eₚ.
- T5 Spectral-evolution classification stats (hard-to-soft / tracking / other, n & %).
- T6 Correlation results (D'Agostini): relation, N, ρ, p, slope m±, intrinsic
  scatter σ_sc — for F–α, F–Eₚ, α–Eₚ, Eₚ–kT, ν_m–ν_c, kT–flux.
- TB1 machine-readable per-block all-model fit table + selection statistic.

## E. Statistical-presentation conventions to adopt
3ML (Vianello+2015); pgstat (Poisson source + Gaussian background). Bayesian
Blocks (Scargle 2013) for binning with a stated p0 and significance cut, each
justified inline with a citation. Model selection on **−2lnL → AIC/BIC + nested
LRT** (Wilks) + physical-validity gate; state the ΔAIC ≥ 10 inconclusive threshold
and justify it (Li use ΔDIC > 10 ≈ 99%, Acuner+2020). Report MAP/best-fit ± 1σ
(68%). Correlations fit with the **D'Agostini (2005) errors-in-both-variables
intrinsic-scatter** method (report slope m, normalization, σ_sc, Spearman ρ, p).
Every population claim in **% (n/N)** form.

## F. Model abstract (Li voice; our planned results — fill final numbers after the
clean re-run)
> Gamma-ray bursts (GRBs) are highly variable and exhibit strong spectral
> evolution. Here we present a time-resolved spectral analysis of a uniform sample
> of NN single-pulse bright Fermi/GBM bursts, comprising NNNN time-resolved
> spectra, fit with a family of empirical models (Band, cutoff power law, smoothly
> broken power law, a double smoothly broken power law, and each non-thermal model
> with an added blackbody). We use empirical models as a model-agnostic probe and
> ask whether the thermal–non-thermal Eₚ–kT correlation reported by Burgess et al.
> (2014) for six bursts appears in a large sample, and what additional spectral
> properties emerge. We find that the low-energy index peaks at α ≈ −0.75, between
> the slow- and fast-cooled synchrotron limits; that X% (n/N) of the bins requiring
> curvature beyond a single break are equally or better described by a thermal
> proxy than by an explicit second break; and that the Eₚ–kT correlation is
> recovered cleanly only in the highest-S/N bursts. We further find a correlation
> between the two synchrotron break energies, ν_m ∝ ν_c^m. We discuss the
> implications for jet composition, noting that empirical continua can absorb a
> sub-dominant thermal component.

## F2. Precise Li conventions to mirror (from the full mine)
- **Correlation functional forms** they fit (mirror these): F–α as
  **F = F₀ exp(k α)** (Li find k ≈ 3.37); F–Eₚ as a **power law** (index ≈ 1.50);
  α–Eₚ as **α = k₂ log Eₚ + c** (k₂ ≈ −2.01). Report ours in the same forms.
- **Correlation TYPE classification (Yu et al. 2019)** — adopt for §3.3: type 1
  monotonic (1p positive / 1n negative / 1f flat), type 2 broken (2p/2n), type 3
  no trend; report the % (n/N) of each type and how often the type changes
  between adjacent epochs. (Li: F–α 84% type 1; the three relations are *rarely*
  all strong at once — 13/103.)
- **Model-selection number** stated Li-style: "Band is preferred in 29% (274/944)
  of bins and 66% (77/117) of pulses." Give ours as "model X wins in N% (n/N)…".
- **Distribution averages** quoted as α = −0.84 ± 0.35, Eₚ = log₁₀(214) ± 0.42
  (log space for Eₚ). Match (ours: α ≈ −0.75).
- **SCS/NDP limiting lines** for §4.1 from Burgess (2015, Fig. 4) and Acuner et al.
  (2019, Fig. 3); fraction-above reported as % (n/N) (Li: 67% above SCS, 21% above
  NDP). Add our synchrotron lines-of-death (−2/3, −3/2).
- **Energy ranges / housekeeping** stated once: NaI 10–900 keV (K-edge 30–40 keV
  ignored), BGO 0.3–30 MeV; cosmology if needed Planck 2020 (H₀=67.4, Ω_M=0.315).
- **Machine-readable Table** (Zenodo/DOI) of per-bin fits — Li deposit it; we do too.

## G. Example Introduction opening (Li voice)
> Gamma-ray bursts (GRBs) are highly variable and exhibit strong spectral
> evolution, with the νFν peak energy Eₚ and the low-energy photon index α
> typically tracking the prompt light curve (e.g., Norris et al. 1996; Kaneko et
> al. 2006). The radiative origin of this emission, however, remains debated. Two
> pictures dominate: a quasi-thermal photosphere superposed on a non-thermal
> continuum (e.g., Ryde 2004; Pe'er et al. 2007), and optically-thin synchrotron
> from a cooling electron population, which imprints two break energies — the
> cooling frequency ν_c and the injection frequency ν_m (e.g., Oganesyan et al.
> 2017; Ravasio et al. 2019). Because both produce similar curvature near the
> peak, distinguishing them from GBM data alone is difficult, and single-pulse
> bursts — with the simplest spectral evolution — offer the cleanest test.

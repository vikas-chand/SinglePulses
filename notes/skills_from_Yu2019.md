# Skills distilled from reading Yu+2019 (annotations + reading-group Q&A)
Compiled 2026-07-30. Goal: turn what a scientist NOTICES while reading a paper into
explicit, reusable AI skills — the library the autonomous pipeline draws on.
Status: ✓ HAVE (in a skill file) · ◐ PARTIAL (implicit / half-covered) · ✗ MISSING.
"Autonomy payoff" = what having it as a skill lets the AI do unsupervised.

Grouped as Vikas asked: ANALYSIS (make the measurement) · METHODS (set up & decide)
· INTERPRETATION (read results for physics). Each MISSING/PARTIAL row is a concrete
next skill-file task; the ✓ rows are cross-checks that our existing skills already
encode what a careful reader would demand.

═══════════════════════════════════════════════════════════════════
## A. ANALYSIS SKILLS (perform the measurement)
═══════════════════════════════════════════════════════════════════
| # | skill (from the annotation) | status | lives in / → goes in | autonomy payoff |
|---|---|---|---|---|
| A1 | Per-channel polynomial background (order 0–4 auto-selected per channel) | ✓ | background_selection.md, 27b | AI fits background without a human picking order |
| A2 | Bayesian blocks on brightest-NaI TTE with false-alarm p (ncp_prior) | ✓ | Binning/27b | AI bins by real intensity changes, not fixed grid |
| A3 | Significance S per bin (Vianello 2018, Poisson+Gaussian) + S≥20 gate | ◐ | 27b has merge; **→ Binning.md** formalize S-gate | AI knows which bins are trustworthy vs noise |
| A4 | Background-variability regime check (when λ(t) corrupts the blocks) | ✗ | **→ Binning.md** | AI refuses to block through a varying background |
| A5 | Non-homogeneous-Poisson correction before blocking | ✗ | **→ Binning.md** | AI normalizes exposure/background before BB |
| A6 | K-edge (33.17 keV): EXCLUDE for spectra, KEEP for timing | ◐ | spectra done (2026-07-24); **timing-keep NEW → DataInventory/Temporal** | AI applies the right mask per task, not blanket |
| A7 | Overflow-channel handling (drop top NaI/BGO edge for spectra) | ◐ | implicit in ranges; **→ DataInventory.md** | AI never fits an unbounded overflow channel |
| A8 | ≤60° NaI angle cut (A_eff + angular-systematic rationale) | ✓ | detector_selection.md | AI selects detectors on geometry autonomously |
| A9 | Joint GBM+LLE+LAT fit — never extrapolate GBM to claim high-E truth | ✓ | broadband; SpectralFitting | AI adds high-E data instead of assuming the tail |
| A10 | Multi-detector significance boost (S∝√counts; 3 NaI+1 BGO) | ✗ | **→ detector_selection.md** (quantify) | AI trades detector count vs cross-cal cost knowingly |
| A11 | Channel-combining to raise S (quantified) | ✗ | **→ Binning.md** | AI recovers evolution in count-starved bins |
| A12 | α_max-per-pulse extraction (one hardest bin, avoids many-bin bias) | ✗ | **→ SpectralFitting (L14)** | AI reports the mechanism-diagnostic bin, not a biased histogram |
| A13 | Cutoff-genuineness test (fit α below Ep → extrapolate → count photons) | ✗ | **→ SpectralFitting (L15) + Proj#34** | AI decides cutoff = intrinsic vs count-limited by itself |
| A14 | Energy-chunked fit-statistic decomposition (ΔC-stat per band) | ✗ | **→ SpectralFitting (L16), extends L4/L11** | AI localizes WHERE a model fails → what to add |

═══════════════════════════════════════════════════════════════════
## B. METHODS SKILLS (set up the analysis & choose the machinery)
═══════════════════════════════════════════════════════════════════
| # | skill | status | lives in / → | autonomy payoff |
|---|---|---|---|---|
| B1 | Likelihood chosen by data+background NATURE (pgstat/cstat, never χ²) | ✓ | **DONE 2026-07-30: SpectralFitting.md §METHODS BOX** | threeML auto-selects it (probes is_poisson at construction → PGSTAT). Our skill = don't override the noise-model setters, keep the polynomial-Gaussian bkg path, verify per-plugin, treat LAT separately. Verified vs installed source (7-agent workflow). |
| B2 | Single-pulse selection (avoid overlapping-pulse averaging) | ✓ | sample def / PAPER_THEME | AI screens contaminated pulses out |
| B3 | Time-resolved-over-integrated doctrine (integrated = superposition artifact) | ◐ | implicit; **→ SpectralFitting (methods box)** | AI never infers physics from a time-integrated shape |
| B4 | Model-comparison criterion choice (AIC/BIC/DIC/WAIC/Bayes-factor) + when each | ◐ | we use ΔAIC≥10; **→ SpectralFitting** add the map | AI justifies its selection statistic, not just applies one |
| B5 | Bayesian-vs-frequentist decision (nuisance marginalization payoff) | ✗ | **→ SpectralFitting (methods box)** | AI knows WHEN the expensive Bayesian route buys something |
| B6 | Bin-adequacy floor (≥N bins at S for an evolution study) | ◐ | L6 | AI declares a burst evolution-capable or integrated-only |
| B7 | Response/effective-area trust (flat good; structured must be modeled) | ✗ | **→ DataInventory.md** | AI weights a fit by how trustworthy the RSP is there |
| B8 | Response-coverage-vs-source-window check (native, no fake collapse) | ✓ | DataInventory (bn100130729 lesson) | AI skips a detector honestly instead of fabricating a response |
| B9 | Known-systematics ledger (GBM: K-edge, angle, cross-cal, SAA, overflow; Connaughton+2015) | ✗ | **→ DataInventory.md** | AI carries a systematic budget into every fit |

═══════════════════════════════════════════════════════════════════
## C. INTERPRETATION SKILLS (read results for the physics)
═══════════════════════════════════════════════════════════════════
| # | skill | status | lives in / → | autonomy payoff |
|---|---|---|---|---|
| C1 | Line-of-death test (α>−2/3 rejects optically-thin synchrotron) | ◐ | validity-gate does the mechanics; **→ SpectralFitting (L17) as an INTERP skill** | AI flags a burst as non-synchrotron → routes to photosphere models |
| C2 | α_max mechanism-ID criterion (one bin violates → mechanism rejected) | ✗ | **→ SpectralFitting (L14, pairs A12)** | AI makes the mechanism call per pulse |
| C3 | Parameter-relation typing: α–Ep, F–Ep (Golenetskii), F–α with Spearman r; h.t.s./i.t./nonmonotonic/break | ◐ | we track evolution; **adopt Yu's TYPING scheme → SpectralFitting/Temporal** | AI classifies each pulse's evolution automatically |
| C4 | Golenetskii correlation as a physics probe (F∝Ep^~1.5; rest-frame Burgess+2019) | ◐ | measured; **→ interpretation note** | AI reads flux-hardness coupling as engine physics |
| C5 | Model-dependence of parameters (α biased HARD by an unmodeled BB) | ◐ | L5/L12 adjacent; **make explicit** | AI distrusts a single-model α before quoting it |
| C6 | Noise-artifact recognition (the Ec≈5 MeV pileup that vanishes at S≥20) | ✗ | **→ SpectralFitting (L18)** | AI recognizes a parameter pileup as noise, not a discovery |
| C7 | Cutoff-mimicry recognition (β≲−3 = Band faking a cutoff) | ◐ | L4 covers degeneracy; **add the β-signature** | AI reads a runaway β as "add a real cutoff" |
| C8 | Degeneracy-breaking strategy menu (wideband / spectral-timing / polarization / SSA) | ✗ | **→ SpectralFitting (interp) + Projects** | AI proposes the NEXT observation to break a tie |
| C9 | Evidence triangulation for emission mechanism (never one line alone) | ✗ | **→ a new `Interpretation.md`** | AI builds a physical picture from converging evidence |
| C10 | Empirical→physical mapping discipline (shape census first, then map; know the 'if') | ◐ | PAPER_THEME; **→ Interpretation.md** | AI keeps model-agnostic until the shape earns a mechanism |
| C11 | Additive-component vs continuum-saddle awareness (the Guiriec/Oganesyan lesson) | ✓ | L12 | AI won't over-split one shape into two "components" |
| C12 | Component evolution tracks under burst-level admission (kT(t), Ep(t), Ec(t)) | ✓ | L13 | AI tracks a weak component across all bins honestly |

═══════════════════════════════════════════════════════════════════
## SUMMARY — what the reading taught us about our library
═══════════════════════════════════════════════════════════════════
**We already have (✓ or strong ◐):** the whole Stage-1→fit→select→evolve spine —
background, blocks, detectors, joint wideband, the Discovery Loop (L1–L13),
admission, class-degeneracy. A careful reader's demands are largely met.

**The real GAPS this paper exposed (priority order):**
1. **B1 — likelihood-by-data-nature (pgstat, never χ²)**: foundational, currently
   assumed not stated. Write it as the methods box of SpectralFitting.md.
2. **A14 / Stats-2 — energy-chunked ΔC-stat**: the highest-leverage NEW analysis
   skill; generalizes L4/L11; makes the Discovery Loop energy-aware. Implementable.
3. **C6 — noise-artifact recognition** + **A13/C7 — cutoff genuine-vs-count** (Proj
   #34): Yu's own unresolved degeneracy; recognizing the 5 MeV pileup is a named
   skill that stops false discoveries.
4. **A12/C2 — α_max mechanism criterion** + **C1 line-of-death as interpretation**:
   Yu's central method; adopt as the mechanism-ID skill.
5. **C3 — evolution-relation TYPING** (α–Ep, Golenetskii, F–α with Spearman): adopt
   Yu's scheme so the AI classifies each pulse's evolution.
6. **C9 + new `Interpretation.md`** — evidence-triangulation + degeneracy-breaking
   (C8): the missing INTERPRETATION skill file (we have analysis/methods well, but
   "how to reason to a mechanism" is under-documented). This is the frontier for
   "AI does it all itself" — it's the judgment layer.
7. Housekeeping skills: A4/A5 background-variability, A6 K-edge-keep-for-timing,
   A7 overflow, A10/A11 significance-boosting, B7/B9 systematics ledger.

**Meta-lesson:** our ANALYSIS + METHODS skills are near-complete; the INTERPRETATION
layer (C-column) is the thin one — exactly the "reason like a scientist" capability
the AI needs to close the autonomy gap. The next skill-building push should be an
`Interpretation.md` that turns C1–C10 into an explicit reasoning protocol.

**Proposed immediate additions (as lessons/files):** SpectralFitting L14 (α_max),
L15 (cutoff-genuine), L16 (energy-chunk), L17 (line-of-death interp), L18
(noise-artifact) + a methods box (B1/B3/B4/B5); new `Interpretation.md` (C3/C8/C9);
Binning.md gains A3/A4/A5/A11; DataInventory.md gains A6/A7/B7/B9.

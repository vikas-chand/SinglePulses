# Paper shaping — Codex (gpt-5.6-sol) independent review, 2026-07-17

Codex reviewed the reframed intro + theme + the full existing `two_break.tex` + the
on-disk PDFs. It caught real citation errors and gave a disciplined structure. Actionable
items below. **No citation goes into the paper until re-verified against a real source.**

## A. CITATION CORRECTIONS (critical — several current cites are WRONG)
| Intended claim | Current (WRONG) | Correct (Codex-found, re-verify) |
|---|---|---|
| pulse superposition → intensity tracking | `Preece1998` | **Hakkila & Preece 2011** (+ Lu 2012 simulation) |
| "~95% synchrotron" | Burgess2014b/2019 | **Burgess et al. 2020, arXiv:1810.06965** — and it is ~95% of the analysed GBM *spectra*, NOT 95% of all GRBs |
| proton synchrotron | `Ronchi2020` | **Ghisellini et al. 2020, arXiv:1912.02185** — and it belongs in DISCUSSION, not the shape paragraph |
| fast-cooling −3/2 + cutoff | (Varun, unspecified) | **Varun et al. 2025, GRB 241030A, arXiv:2510.24864** (SBPL×Cut). Do NOT conflate fast-cooling with external MeV absorption — keep as separate motivations |
| Amati / second-component energetics | Mei2025+Yonetoku2004 | **UNUSABLE as written.** If pulse-wise Amati: Basak & Rao arXiv:1202.3089. Else delete the aim until fully defined |
| Ravasio2018 | called "Nature" | it is **A&A 613, A16**; verifies a 2SBPL in 160625B — NOT "a population of narrow peaks" |
| **Ravasio2023** (in bib) | used for "narrow peaks"/"low-E break" | **arXiv:2303.16223 = GRB 221009A MeV emission-LINE paper — SERIOUS misattribution, remove that use** |
| Bayesian-block vs S/N binning | (generic) | **Burgess 2014, arXiv:1408.3973** (BB/Knuth recover evolution; S/N fails) |
| Burgess2019 | (implied synchrotron) | 321 SHORT GRBs, 513/525 CPL — does NOT support the 95% claim |
| LLE analysis technique | Atwood2009 only | Atwood is the LAT *instrument*; add a proper LLE-method reference |

## B. STRUCTURE (Codex-recommended)
**Results order** (population BEFORE case studies):
1. Yield/QC (bursts, intervals, coverage, valid/ambiguous fraction)
2. **Primary fine-grid shape census** — per spectrum + per burst; exact-model AND family
   counts; WITH and WITHOUT ambiguous bins; sensitivity to threshold + data quality
3. Peak shape/curvature (W_HM; fixed vs free SBPL smoothness; conditional on S/N)
4. Low-energy departures (decisive 2nd break; thermal-like add; their degeneracy)
5. High-energy tier (SEPARATE census; eligible sample pre-defined; LLE availability ≠
   signal; GBM-only vs joint on identical intervals; LAT NON-detections reported; require
   the component CONSTRAINED not just lower-AIC; simulate false positives; don't auto-call
   >100 MeV "prompt")
6. Evolution through NORMALISED pulse phase (family transitions; Ep/indices/breaks/kT/Ecut;
   burst-level not naive pooled significance)
7. Conditional secondary (Ep–kT from the SAME composite fit; break–break only in
   decisive-2break bins; energetics only for a prespecified redshift subset)
8. Case studies LAST

**Discussion order**: what the census establishes → comparison (Kaneko/Gruber/Yu/Poolakkil/
Burgess/Li) → what the high-E band actually added → evolution → conditional physics
(synchrotron/photospheric/proton-synch/pair-opacity/extra zone) → limitations.
**DELETE/absorb** the standalone "Assessment of Compatibility with Emission Models" §
(it puts physics ahead of the empirical contribution).

**Notation discipline**: in Results use empirical `E_b,low`/`E_b,high`; introduce νc/νm
ONLY in Discussion, conditionally. "BB" = fitted Planck shape; "photosphere" = an
interpretation (Discussion only). Ep–kT must be same-fit.

**Figures**: (1) coverage + a single-pulse LC showing BOTH binning tiers; (2) a SHAPE
ATLAS (N(E) + νFν per family); (3) central census figure (per-bin + per-burst family
fractions incl. ambiguous); (4) family vs normalised pulse phase; (5) peak-width/
curvature; (6) low-E degeneracy examples (one decisive 2SBPL, one decisive BB); (7)
high-E GBM-only vs joint; (8) secondary correlation panel only if mature.

## C. DEFENSIBLE NOVELTY (use ~verbatim)
"...combining a reproducible single-pulse morphology selection with a prespecified
hierarchy of empirical shape families on common time-resolved intervals, and adding a
separately defined joint GBM–LLE/LAT analysis for high-energy structure."
**Do NOT claim:** largest catalog / first Bayesian-block catalog / first single-pulse
study / first multi-model / uniformly 8 keV–LAT for ALL bursts / "all possible" shapes.

## D. OVERCLAIM FIXES (highest-risk, before submission)
- "No T90 restriction" is FALSE for the current sample (matches the 2026-06-14 audit H1).
- "Busby-selected" without faithfully reproducing the Busby algorithm.
- Any provisional number / "the refit won't change conclusions" assurance.
- Empirical BB called a "photosphere"; fitted breaks called νc/νm — in RESULTS.
- Dominant photospheric origin claimed from AIC preference.
- All valid 2SBPL used for a break correlation when the 2nd break isn't decisive.
- Pooling hundreds of within-burst bins as independent.
- Mixing Ep and kT from different fitted models.
- Calling LAT emission "prompt" without temporal/morphological evidence.
- "all shapes" → "all prespecified candidate shapes"; "uniform" needs the two tiers explained.

> Codex's closing: "The paper has a potentially strong and distinct contribution, but its
> strongest version is a disciplined empirical census with explicitly reported ambiguity —
> not a new physical verdict hidden inside a larger model menu."

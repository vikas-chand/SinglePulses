# PROJECTS registry — spin-off projects surfaced during the paper-reading campaign
Numbered projects Vikas nominates while we read (~200 papers planned). Each = a
self-contained study our single-pulse pipeline + sample can deliver, often as a
byproduct of the main survey. Status: 💡 idea · 🔬 scoped · ▶ running · ✅ done.
Citations grounded before entry (house rule).

Numbering continues an existing sequence (#33/#34 first appeared in the Yu+2019
reading notes). Earlier #1–#32 live elsewhere / historically; this file owns #33+.

───────────────────────────────────────────────────────────────────
## #33 — SSA in prompt emission  💡
**Source:** Varun, Zhang & Zhao 2026 ApJ 998,90 (GRB241030A, fast-cooling
synchrotron, simultaneous Swift UV, z=1.411); idea from Binbin's student.
**Question:** can synchrotron self-absorption (SSA) be constrained at the low-energy
end of prompt spectra, and is it distinguishable from ν_m? Vikas's caveat: "low-E
SSA — it's still ν_m I guess" → the SSA-turnover vs ν_m-break distinction is the
crux. Simultaneous UV/optical is the lever.
**Deliverable:** search our wideband (+ any simultaneous low-E) fits for an SSA
signature; where models differ (low-E or high-E).

───────────────────────────────────────────────────────────────────
## #34 — Is a high-energy cutoff GENUINE or count-limited?  🔬
*(nominated 2026-07-29, formally registered 2026-07-30)*
**Source:** Yu+2019 stated this exact degeneracy and left it unresolved (p.9:
"BAND mimicking a cutoff OR poor count statistics"; their Ec≈5 MeV cloud is a NOISE
artifact that vanishes at S≥20).
**Question:** for bursts showing a cutoff above Ep, is it intrinsic or just low
counts at high E?
**Method (Vikas):** fit α FAR below Ep → extrapolate that power-law ABOVE Ep →
predict the expected photon counts → compare to observed. Observed ≈ predicted
(within Poisson) ⇒ count-limited; observed ≪ predicted ⇒ INTRINSIC cutoff. Doable
with Band-only (β + Ep capture the rollover) on the bright, high-count bins.
**Byproduct of:** the full-sample run (some bursts will show cutoffs). Empirical.
**Links:** L4 (cutoff continuum-degeneracy), C6 noise-artifact skill, #35 (physical
twin), Oganesyan+2026 (the absorption mechanism).

───────────────────────────────────────────────────────────────────
## #35 — Rescue the SOFT-p problem in cool-synchrotron fits with wind ABSORPTION  🔬
*(nominated 2026-07-30, Vikas)*
**Source:** Burgess, Bégué et al. 2020 NatAs 4,174 "GRBs as cool synchrotron
sources" — ~95% of single-peaked-GRB time-resolved spectra fit by time-dependent-
cooling synchrotron, BUT a minority require **unphysically SOFT electron index p**.
**Vikas's hypothesis:** the soft p is driven by the region ABOVE the peak being
low — i.e. it may be a real **cutoff/absorption above Ep** being absorbed into an
artificially steep high-energy synchrotron tail (soft p), NOT intrinsic electron
softness. Candidate mechanism = **wind-medium absorption** (Oganesyan+2026 A&A
710,L37: prompt photons traverse the circumburst wind; electrons back-scatter
X-rays; γγ pair-production carves an MeV absorption feature). The low-energy slope
below Ep is correlated with the presence of that cutoff.
**Method:** add an ABSORPTION / cutoff term to the PHYSICAL synchrotron model and
re-fit the soft-p bursts. If p returns to normal (~2.2–2.5) once absorption is
included → the soft p was an absorption artifact, problem alleviated. Also test the
predicted α_below ↔ cutoff correlation. "Saddle vs cutoff" ambiguity (our L12).
**Relation to #34:** #34 is the EMPIRICAL test (is the cutoff real?); #35 is the
PHYSICAL twin (does modeling the cutoff as wind-absorption fix the synchrotron
fit?). Together they attack the same feature from data-space and model-space.
**Needs:** the physical synchrotron model in 3ML (Burgess table model / astromodels
custom) + an absorption component. Heavier than #34; a real modeling project.
**Links:** Burgess+2014/2020, Oganesyan+2026, Guiriec saddle-vs-additive history
(L12), #34, the empirical→physical mapping fork (Intro-Q3).

───────────────────────────────────────────────────────────────────
## #36 — Revisit & extend Burgess 2014: does temporal binning PRESERVE spectral evolution?  🔬
*(nominated 2026-07-30, Vikas)*
**Source & gap:** Burgess 2014 is the SINGLE work demonstrating that Bayesian-block
bins are the bins that preserve spectral (Ep) evolution — done by ONE person, on
SIMULATED data. Unknown whether it holds for GRBs evolving FAST vs SLOWLY, or for
other transient classes; unknown whether HYBRID bins (Bayesian blocks + then
combining low-significance bins with neighbours to raise S) preserve evolution as
well while giving better-CONSTRAINED parameters.
**Question:** how does temporal binning affect recovered spectral evolution across
transient types (fast- vs slow-evolving; possibly other transients)? Does our
hybrid Bayesian-blocks+significance-merge scheme preserve Ep(t) while improving
parameter constraints vs pure BB (where low-S bins give unreliable, wide-error
params)?
**Method:** revisit Burgess 2014 — adopt simulations (as he did) PLUS a real GRB
sample spanning evolution rates; compare pure-BB vs hybrid-merged binning on
recovered Ep(t) fidelity and parameter constraint. Extend to demonstrate more
broadly than one 2014 simulated study.
**Motivation from the data:** our own significance table (notes/significance_table)
shows only 70/106 bursts reach ≥5 bins at S≥20 — the low-S bins near the background
(already background-subtracted → inflated, unreliable uncertainties) are exactly
what hybrid merging targets. Also: for bn081125496 Yu report 6 strong bins vs our 3
(their na+nb+b1 combination vs our binning) — direct evidence that combining
raises S; quantify it.
**Links:** L6 (bin adequacy), A3/A11/B6 (significance skills), project_binning_
methodology_3ml, Burgess 2014, Scargle+2013.
**Numbering note:** Vikas said "project 35" for this; #35 was already taken by the
soft-p absorption project earlier this session, so this is #36 (renumber if preferred).

───────────────────────────────────────────────────────────────────
## Not a numbered physics project — feeds the ASTROGRAPH project
- **Literature niche-map / research-gap extraction** (Abstract-Q1): Vikas clarified
  this is NOT a new physics project — gap-identification after reading is the
  **Astrograph project** (finding gaps via the citation/reference network). Reading
  these ~200 papers is the groundwork for learning how to execute Astrograph. So:
  every paper's "what they left for us" is logged as INPUT to Astrograph, not as a
  standalone physics study. (Yu+2019's contribution: composites + wideband + bigger
  shape-selected sample + physical mapping + α>−2/3 + cutoff-genuineness.)

───────────────────────────────────────────────────────────────────
## #37 — Lag–MVT curvature test on CLEAN single-pulse GRBs  🔬
*(brief developed in a separate session (ChatGPT/other), imported by Vikas
2026-07-30; NATURAL OUTPUT of the Two_Breaks pipeline — we already produce
per-burst lag + MVT + Ep(t) on clean single pulses.)*

**Hypothesis (falsifiable, with a PARAMETER-FREE prediction):** under pure
high-latitude curvature, both the spectral lag and the MVT come from the SAME
angular timescale R/(2cΓ²), so:
    τ_lag ≈ (E_h/E_l − 1) · δt_MVT
→ the DISCRIMINANT is the SLOPE = E_h/E_l − 1 (~0.8 for typical bands), intercept
≈0 — NOT the correlation coefficient (a bare correlation is half-expected and
uninteresting, see Γ-confound).

**Three-way outcome map (each is a distinct physical conclusion):**
- correlated at slope ≈ E_h/E_l−1, intercept ≈0 → **curvature origin of lags** confirmed.
- decoupled / null / steep-scattered → lags are **spectral (cooling), not geometric**
  (publishable: contradicts a leaned-on model).
- floor at the curvature line + scatter above (Peng combined picture) → curvature
  sets the minimum lag, cooling adds on top; the RESIDUAL
  τ − (E_h/E_l−1)δt_MVT becomes a new observable to correlate with the h.t.s. rate.

**Why clean single-pulse (Vikas's scope):** the relation is derived for ONE
emitting shell. Multi-pulse → MVT set by the narrowest spike, lag is burst-averaged
→ they come from different pulses, ratio meaningless. Single-pulse = both observables
describe the SAME episode (the only regime where the slope has a right to hold); also
removes the pulse-ID / K-correction-for-overlap problem; and MVT of a smooth single
pulse ≈ its rise time = exactly the curvature-predicted quantity. OUR Busby
single-pulse sample is purpose-built for this.

**Design refinement (Hakkila+2015, #39):** don't just correlate lag vs MVT — track
SIMULTANEOUSLY per pulse: κ (asymmetry), hardness-evolution RATE, spectral form, and
the three-peaked re-hardening structure. The lag-MVT SCATTER may correlate with these:
if curvature dominates the relation should be CLEAN; if spectral evolution matters,
scatter increases with the re-hardening/evolution-rate. So the residual off the
curvature line becomes a probe of spectral-evolution vs geometry (ties to #37's
three-way outcome map). Also: Hakkila's "single pulse" is partly semantic (3 peaks
may be nested shocks) — our MEPSA N_peaks=1 cut must be explicit about this.

**Design (build in from the start):**
1. Define "clean single pulse" QUANTITATIVELY, pre-registered: peak-detection
   (MEPSA — Guidorzi-group standard, comparable) require N_peaks=1 above S/N.
2. Fit LOG-LOG with errors on BOTH axes; overplot the parameter-free curvature line
   (slope E_h/E_l−1, intercept 0); a slope-consistent + intercept≈0 = clean detection.
3. **Partial correlation controlling for Γ** (afterglow-onset where available) —
   report BOTH raw and Γ-controlled. THE key guard: MVT∝Γ⁻² AND lag∝R/cΓ² both track
   Γ, so a bare correlation can be Γ leaking through both axes. Slope is what no
   confound can fake.
4. Yield estimate EARLY: clean-single-pulse ∩ known-z ∩ measurable-positive-lag ∩
   measurable-MVT may be ~couple dozen. If thin, the burst-level version IS the paper.

**Pipeline fit:** we ALREADY emit per-burst: lag (compute_spectral_lag), MVT (Bala
mvtfermi + Vianello CWT), Ep(t), pulse-shape/N_peaks (Gowri/MEPSA). Burst #1
(bn081125496): lag −1.09s, MVT (mvtfermi), Gowri φ=0.33 single FRED → first point.

**⚠ VERIFICATION DEBTS (imported citations, NOT yet checked by us — house rule):**
Camisasca+2023 (MVT∝Γ⁻², MVT–L_iso anti-corr); Guidorzi+2024 (V_f–L_iso p≲2%,
V_f–MVT done); Peng et al. (combined curvature+cooling); and the "lag–MVT direct
population correlation is UNCLAIMED" status → needs an AIRTIGHT ADS/arXiv
title+abstract pass ("spectral lag" AND "minimum variability"/"MVT") before we
commit. Move with some urgency — the Camisasca/Guidorzi (Ferrara/Bologna) group is
working through the MVT-correlation space methodically; lag is the obvious next square.

───────────────────────────────────────────────────────────────────
## #38 — Temporal properties of single-pulse GRBs (standalone survey)  ▶
*(nominated 2026-07-30, Vikas; dir: `temporal_properties/`)*
Full-sample temporal survey (T90/T50, MVT, spectral lag, Gowri/Koc/Norris pulse
fits) over the single-pulse sample, run via scripts/40_temporal_survey.py (handbook
chain, 10 workers). UMBRELLA for #37 (lag–MVT curvature test) — the survey IS the
data collection. Deliverables: results/temporal_catalog.ecsv (per burst) + the
lag–MVT plot with the parameter-free curvature line + Spearman/slope/Γ-controlled
stats. Refinements: Bala mvtfermi + Vianello CWT MVT upgrade; MEPSA N_peaks=1
cleanness cut; source-frame lag via z table (redshifts.ecsv). Standalone-paper
potential: "Temporal properties of Fermi single-pulse GRBs".

───────────────────────────────────────────────────────────────────
## #39 — Hakkila pulse-shape lineage review (reading/scoping)  💡
*(nominated 2026-07-31, Vikas, after reading Hakkila+2015 ApJ 815,134)*
**Task:** map the Hakkila pulse-shape lineage 2011→2024, identify gaps, assess
whether updating the analysis with modern methods/data is viable. Feeds
SinglePulse_Temporal (pulse shape) + refines #37 (lag-MVT, see below).

**Key takeaways from Hakkila+2015 (Vikas's read):**
1. THREE-PEAKED residual structure is UNIVERSAL across energies (BATSE high / GBM
   mid / Swift low); fainter at soft E but present. S/N-dependent detectability,
   NOT an instrumental artifact.
2. Method: Norris+2005 empirical pulse + Hakkila&Preece 2014 Bessel-function
   residual-wave fit; params t0, a, Ω, s; normalized amplitude ⟨R⟩≈0.23 universal.
3. κ-correlations robust across Swift/BATSE/GBM: Ω-κ, s-κ, t0-κ; asymmetry links to
   residual-structure timing.
4. Hard-to-soft AND intensity-tracking COEXIST in every pulse (not separate classes):
   hard pulses re-harden at decay peak; soft pulses re-harden at central peak.
5. Spectral evolution tied to STRUCTURE: re-hardening at three peaks ⇒ THREE energy
   injections, not one smooth cooling → single-component models insufficient.
6. Open questions: physical mechanism unknown (curvature alone insufficient;
   synchrotron needs ad-hoc tweaks); internal-shock plausible but unresolved;
   background-subtraction systematics (esp. GBM — need physical bkg modeling to
   confirm structure); "three peaks vs distinct pulses" — the definition of "single
   pulse" is partly semantic.
7. Lineage to track: 2015 (Swift shapes) → 2018 (short GRBs) → 2021 (temporal
   symmetry, 86% success) → 2024 (lateral jet-motion connection). ⚠ verify bibcodes.
9. Speculative mechanism: three shocks in rapid succession, each re-brightening the
   previous (nested structure in one outflow) — explore for ultra-bright bursts
   (221009A).
**⚠ house rule:** verify the 2018/2021/2024 Hakkila bibcodes before the review.

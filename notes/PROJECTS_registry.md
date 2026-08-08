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

**🔴🔴 NOVELTY CORRECTION — Sonbas+2013 READ IN FULL (2026-07-31; PDF in Skills_training/,
arXiv:1210.6850). The lag-vs-MVT idea is LESS novel than a first pass suggested — be honest.**
Sonbas et al. 2013, ApJ 767, L28 (2013ApJ...767L..28S; title is about X-ray FLARES, which is
why a title-only search misses it — its Fig 3 IS the lag-vs-MVT plot) ALREADY:
(a) plots spectral lag vs MVT (MTS) directly; (b) finds a strong correlation (Spearman 0.96,
Kendall 0.86); (c) fits a log-log slope 1.44±0.07 (observer frame, arguing z-dilation cancels
— OUR argument too); and (d) INVOKES CURVATURE explicitly — Kocevski rise-time δR/2cΓ² + Zhang
decay (R/c)(θ²/2), "if the decay time scale is the spectral lag due to curvature … a
correlation between the lag and [MVT]," calling it "speculative" and warranting "detailed
theoretical investigation." ⇒ We are NOT first to plot lag-vs-MVT, find the correlation, OR
propose curvature. **Cite Sonbas as the ORIGINATING result, up front.**

**What #37 still genuinely owns (= the investigation Sonbas explicitly left open):**
1. PARAMETER-FREE test, not a free fit. Pure curvature ⇒ a LINEAR law (log-log slope 1,
   normalization E_h/E_l−1 ≈ 0.8). Sonbas fit a FREE slope and got 1.44 ≠ 1 — an un-remarked
   hint the raw relation ISN'T pure curvature (or is contaminated). #37 tests the FIXED
   slope-1 / norm-0.8 prediction and treats the deviation as the signal (three-way outcome
   map). Their 1.44 is our MOTIVATION, not our scoop.
2. CLEAN SINGLE PULSES (one shell — the only regime the slope law is derived for), vs Sonbas's
   MIXED long+short prompt + XRF sample spanning >3 decades. That huge dynamic range is exactly
   what makes r=0.96 half-trivial (the Γ / dynamic-range confound #37 already flags).
3. Γ-CONTROLLED partial correlation + REST-FRAME bands (known-z). Sonbas: observer frame, no Γ
   control, z-dilation waved away.
So #37 = turn Sonbas's speculative, observer-frame, mixed-sample correlation into a FALSIFIABLE
parameter-free test on clean single pulses. Real, but narrower than "a new correlation" — sell
the DISCRIMINANT, not the correlation.
- The two MacLachlan papers are MVT-vs-rise-time (2012MNRAS.425L..32M) and MVT-vs-duration
  (2013MNRAS.432..857M) — NOT lag; do not miscite them as lag-MVT.
- MVT estimator to standardize on: Golkhou & Butler 2014 (2014ApJ...787...90G).
**Still-unverified imported citations (check before committing):** Camisasca+2023
(MVT∝Γ⁻², MVT–L_iso anti-corr); Guidorzi+2024 (V_f–L_iso p≲2%, V_f–MVT); Peng et al.
(combined curvature+cooling). Position vs the Camisasca/Guidorzi (Ferrara/Bologna) MVT programme.
**LESSON (verification):** the workflow agent's one-line verdict mis-framed this ("done — bare
correlation"); the paper's TITLE (X-ray flares) hid its lag-MVT + curvature content. A
novelty-deciding claim must be checked by OPENING THE PAPER, not the abstract-agent's summary.
[feeds SpectralFitting P6 attribution rule.]

───────────────────────────────────────────────────────────────────
### #37 RESTRUCTURED — discovery ➜ CONTROLLED REDO
*(Vikas's line-by-line read of Sonbas+2013, 2026-07-31 evening handoff. That handoff is
the RECORD — a human read + discussion, not an automated summary; do not re-derive it.
My independent read the same day reached the same verdict = convergent, two primitives.)*

**THE NEW RESEARCH QUESTION (replaces "is there a lag–MVT correlation?", which is answered):**
> The published lag–MVT correlation (Sonbas+2013) rests on an OBSERVER-frame,
> RANGE-INFLATED, BAND-HETEROGENEOUS measurement over ~19 flares + an unstated number of
> prompt pulses, with NO single-pulse requirement and NO k-correction. **Does it survive a
> rest-frame, single-pulse, fixed-band, k-corrected analysis on a modern sample — and is its
> SLOPE consistent with the parameter-free curvature prediction?**
This is a stronger paper than the original scope: a definite hypothesis TEST at its centre
instead of a correlation hunt.

**WHY THE REDO IS JUSTIFIED — Sonbas's 8 weaknesses (Vikas's §2; these become our contribution):**
1. **Observer frame — the central problem.** Their stated defence is that "the (1+z) dilation
   is the SAME for both variables." That is exactly BACKWARDS: a shared multiplicative (1+z)
   injected into BOTH axes GUARANTEES part of ρ=0.96 by construction. First thing a modern
   referee asks. (They never even list redshifts — the z info may never have been assembled.)
2. **Dynamic range does the heavy lifting.** ρ=0.96 "spans >3 decades" because two CLUMPS
   (prompt at ms–s, XRF at s–tens of s) are stapled together on log–log. Two separated clumps
   give near-unity rank correlation almost regardless of internal behaviour. **The meaningful
   number — the correlation WITHIN the prompt sample alone — is never reported.** Neither is
   within-XRF. Only the combined statistic is quoted.

🔴 **RETRACT 1 AND 2 AS WRITTEN — both are REFUTABLE (measured 2026-07-31, SinglePulse_Temporal
terminal). DO NOT put either in a draft.** Sonbas p.3 verbatim: *"a Spearman correlation of
0.96 ± 0.05 and a Kendall correlation of 0.86 ± 0.05"* — these are **RANK** statistics, which
kills both criticisms:
- vs (1): a shared (1+z) on both axes induces only **ρ≈0.11–0.25** at the observed scatter
  (0.45 dex MVT, 0.60 dex lag); reaching 0.96 would need intrinsic scatter ≤0.03 dex. The
  co-scaling cannot manufacture their correlation.
- vs (2): two stapled clumps **CAP Spearman at ≈0.75** at any separation. Pearson-on-logs
  would reach 0.96, but they report Spearman AND Kendall 0.86 — that escape is closed.
⇒ Levelling either at Sonbas invites an immediate referee refutation. **The surviving — and
much stronger — criticism is the CCF pulse-width artifact** (the only mechanism that CAN
produce ρ≈0.96 *with* slope 1): see `SinglePulse_Temporal/notes/FEASIBILITY_GATE.md`.
Criticisms 3–8 below (bands, MVT band, k-correction, single-pulse, errors, age) **stand**.
3. **Heterogeneous energy bands on the lag axis.** Prompt lags "for various observer-frame
   energy bands"; XRF lags 0.3–1 vs 3–10 keV. Not apples to apples (γ-band vs soft-X band
   separations), and the prompt set may not even be internally homogeneous. Since curvature
   predicts τ ∝ (E_h/E_l − 1), varying band pairs SMEAR the predicted scaling — so their
   slope 1.44±0.07 has **no clean interpretation** and cannot be compared to a prediction.
4. **MVT is itself energy-dependent** and they don't state or control the prompt MTS band
   (inherited from MacLachlan). [ref confirm in flight — wf whkt5d73d]
5. **No k-correction on the lag** (contrast Ukwatta+2018 source-frame treatment). Combined
   with 1+3: the lag axis is observer-frame, band-heterogeneous AND uncorrected.
6. **Single-pulse selection never addressed.** Bhat+2012 is a pulse catalogue, but no
   requirement of ONE emission episode. Matters because the curvature prediction only holds
   when lag and MVT describe the SAME pulse: in a multi-pulse burst the CCF lag is
   burst-integrated (contaminated by pulse-to-pulse spacing) while MVT is set by the sharpest
   structure anywhere. **Our clean-single-pulse cut is a genuine, defensible difference.**
7. **Small sample, errors discarded.** 19 XRFs with large ASYMMETRIC errors (e.g. 050822:
   5.83 −2.13/+7.99); rank correlations throw those away entirely.
8. **Age.** 2013 paper on 2005–2007 Swift + then-current GBM catalogues; 13 more years exist.

**KEEP from Sonbas (credit, don't reinvent):** the WAVELET MTS method (MacLachlan) assumes NO
temporal profile and does NOT require identifying distinct pulses — a real advantage over
pulse-fitting, and why wavelets + pulse-fitting are INDEPENDENT estimators of the same
timescale. Retain it. Also CITE their curvature derivation rather than re-deriving (see
`SinglePulse_Temporal/notes/curvature_theory.md`).

**NEW REQUIREMENTS added by this read (§3.2) — all six are now design constraints:**
1. **Rest-frame both axes**; ALSO report the observer-frame version explicitly, to quantify
   how much of Sonbas's signal the (1+z) co-scaling accounts for. (That comparison is itself
   a result.)
2. **Fixed energy bands throughout** — ONE band pair for lag across the whole sample; MVT in a
   stated fixed band; justify the choice against the curvature band-ratio prediction.
3. **k-correction on the lag** (Ukwatta+2018 source-frame treatment).
4. **Report within-population correlations FIRST** (prompt-only; XRF-only if included), with
   any combined figure flagged as range-inflated.
5. **Errors-in-both-variables fit** with asymmetric uncertainties + injection/recovery to
   characterise the measurement floor.
6. **Decide explicitly on XRFs.** Including them reproduces the range inflation.
   **RECOMMENDED: (a) prompt-only as the main analysis** (clean test, no inflation), with
   (b) prompt+XRF as a secondary section, within-population stats first.

**SAMPLE (§3.3) — bottleneck is z, and it is PARTLY SOLVED already:**
- GBM single-pulse with z = **13** (`Two_Breaks/results/redshifts.ecsv`) — NOT enough alone.
- Swift extension **already built**: `SinglePulse_Temporal/data/zhang_swift_singlepulse.csv`
  = **85 Zhang single-pulse Swift bursts with z** (⚠ mix of MEASURED vs PSEUDO-z — must be
  split; only measured-z bursts can enter the rest-frame test).
- **Estimate the JOINT yield early** — single-pulse ∩ measured-z ∩ measurable-lag ∩
  measurable-MVT. If only a few dozen, that shapes the statistics AND the paper BEFORE any
  code is written. [BAT lag+MVT feasibility under check — wf whkt5d73d]

**AUTHOR ENGAGEMENT (Vikas §6):** Eda Sonbas (Adıyaman Univ. + NASA GSFC). Vikas contacted her
once re: postdoc, no reply. There is now a CONCRETE reason to make contact — a substantive
methodological engagement with her 2013 result + a proposal to extend it. Worth deciding
BEFORE the redo is public: collaboration vs being scooped-adjacent. **⚠ NOW URGENT — her group
published a partial rest-frame redo in 2025 (below). She is actively working this exact square.**

### 🔴🔴 VERIFIED 2026-07-31 (wf whkt5d73d — citation-lineage trace + ADVERSARIAL refutation, both read the PDF)
**A. THE FIELD MOVED — Sonbas's OWN GROUP already did a partial rest-frame redo.**
**Göktaş, Nasıroğlu & Sonbaş 2025, JARNAS 11, 27 (`2025JARNA..11...27G`,
doi:10.28979/jarnas.1612952)** — 162 Swift/BAT GRBs with known z, 2011–2019:
- **SOURCE-FRAME lag bands** (100–150 vs 200–250 keV *in the source frame*), light curves
  rebinned by 1/(1+z) — i.e. they fixed Sonbas 2013's central flaw (§2.1).
- **Result: lag-vs-MTS best-fit slope = 1.01 ± 0.04**, interpreted as curvature evidence.
- ⚠⚠ **That is OUR parameter-free prediction (log-log slope = 1) — already measured, by them.**
**What they did NOT do (the surviving gap, confirmed by an INDEPENDENT adversarial agent that
tried to refute it and failed):**
- **No single-pulse selection** — all 162 regardless of morphology, so lag mixes pulses and MVT
  is set by the narrowest spike anywhere (exactly the §2.6 contamination).
- **No rank statistic at all** — no Spearman/Kendall/p-value anywhere in the text; only an OLS slope.
- **MTS in the OBSERVER band** (15–150 keV, 200 μs bins) while the lag is source-frame → the two
  axes are not band-matched, and MVT is energy-dependent (Golkhou+2015), so the rest-frame energy
  the MTS refers to still drifts with z. **No k-correction.**
- **BAT-only** (15–150 keV) — no wide-band leverage; only 8 short GRBs.
- **Figure 6 axes ambiguous** about which frame each is in.
- Published in a Turkish regional open-access journal; **currently uncited on ADS** → invisible
  to the field, which is both an opportunity and a scoop risk.
**⇒ CONSEQUENCE FOR #37 (framing shifts AGAIN, and gets sharper):** we are no longer "testing
whether the slope is 1" in a vacuum — **a published number (1.01±0.04) already matches the
curvature prediction.** Our contribution becomes: (i) do it on CLEAN SINGLE PULSES, the only
regime the law is derived for; (ii) BAND-MATCH both axes in the rest frame + k-correct;
(iii) report the RANK STATISTIC they omit; (iv) **test the NORMALIZATION, which nobody has ever
tested** — the prediction fixes slope=1 AND intercept≈0 AND norm=E_h/E_l−1; Göktaş reports only
a slope, so the normalization test is still entirely ours; (v) wide-band (GBM+LLE+LAT) vs BAT-only.
**Confirm-or-refute framing:** if we reproduce slope 1 with proper controls we become the
definitive version of a currently-invisible result; if clean single pulses do NOT give slope 1,
that is a striking result against them. Either outcome is publishable.
**⚠ MUST cite Göktaş+2025 as prior art and differentiate explicitly.**

**B. Other verified anchors (fold into the design):**
- **MVT energy dependence → cite Golkhou, Butler & Littlejohns 2015, ApJ 811, 93
  (`2015ApJ...811...93G`)** "The Energy Dependence of GRB Minimum Variability Timescales".
  Do NOT cite Golkhou & Butler 2014 for energy dependence (single 15–350 keV BAT band); cite
  **`2014ApJ...787...90G`** for the Haar-wavelet MVT definition + first source-frame Δt_min/(1+z).
  **Golkhou+2015 §3.6 is our template for doing it right: fixed REST-FRAME bandpass
  (they use 89–299 keV) AND division by (1+z).** ⇒ adopt a fixed rest-frame band, not just a
  (1+z) division — this is precisely what Göktaş omitted on the MTS axis.
- **⚠ INSTRUMENT SYSTEMATIC (critical for our GBM+Swift merge): Golkhou+2015 find Swift/BAT MVTs
  run 2–3× LONGER than Fermi hard-channel MVTs for the SAME bursts.** Merging our 13 GBM + Zhang's
  Swift bursts without correcting this injects a factor-of-a-few systematic straight onto the MVT
  axis — i.e. onto the slope. Must be calibrated (our **9 GBM∩BAT overlap bursts are exactly the
  calibration set**).
- **Swift extension viable:** Zhang et al. 2026 = **`2026A&A...707A.392Z`** (85 single-pulse FRED,
  **39 spectroscopic z**); ~465 Swift GRBs have z total; BAT event data supports both Haar MVT
  (Golkhou used 100 μs bins) and CCF lag (Ukwatta `2010ApJ...711.1073U`, `2012MNRAS.419..614U`).
  Realistic yield surviving an S/N cut for BOTH observables: **~20–30 bursts** → triples our 13.
- **Sonbas 2013's XRF arm is half-dead in the rest frame:** only **9 of the 19** flares have secure
  spectroscopic z (10 with a tentative). Kocevski-parameter arm survives at N=9; the
  Margutti-parameter arm collapses to **N=2**. Pulse-param sources verified: Margutti+2010
  `2010MNRAS.406.2149M`, Kocevski+2007 `2007ApJ...667.1024K`. ⇒ reinforces **prompt-only** as the
  main analysis (§3.2.6).
- **Zhang & Yan 2011 ICMART = `2011ApJ...726...90Z`** — §5.1: **SLOW/broad component = central-engine
  time history** (one broad pulse = one ICMART event); **FAST component = relativistic magnetic
  turbulence** (mini-emitters). This is the theory motivating a lag–variability link.
  ⚠ **Uhm & Zhang 2016 (`2016ApJ...825...97U`, "The Origin of Spectral Lags") is the likely genuine
  bridge from geometry to lag and may CHALLENGE the pure-curvature null — verify before citing.**
  [under check — wf w83xb2n74]
- **Near-misses — ✅ BOTH CLEARED (wf w83xb2n74, full texts read):**
  - **Li et al. 2026, ApJS 283, 47** (`2026ApJS..283...47L`, arXiv:2601.21693) "Pulse-resolved
    Classification… I. Precursors versus Main Bursts" = **PARTIAL-OVERLAP, gap survives.** They DO
    measure MVT (Haar, 1 ms) *and* lag (CCF, 25–50 vs 15–25 keV) on the same pulse-resolved
    episodes of **22 z-known Swift/BAT bursts** — but they **never correlate lag against MVT**
    (no plot, no fit, no rank statistic; Fig 4 is T90-vs-MVT, Fig 5 shows them as separate CDFs,
    the only rank stat is MVT-vs-peak-flux). Lags are **observer-frame, not k-corrected**, and the
    sample is **precursor+main two-episode** bursts, not single-pulse. ⚠ It is "Paper I" of a
    series that promises to "extend this pulse-level analysis to other complex temporal
    structures" — **watch the series.**
  - **Della Casa et al. 2026** (`2026arXiv260531566D`, arXiv:2605.31566) "Insights on the GRB
    variability in their cosmological rest frame" = **NOT a lag paper.** Rest-frame Haar-MVT survey
    of Fermi-GBM correlating MVT with z, E_iso, E_p,z and the Reichart V; **no spectral lag, no
    single-pulse cut.** Still useful as a modern rest-frame-MVT methods reference (⚠ arXiv-only,
    NOT refereed, submitted to A&A).
  - Also noted: Maraventano+2025 `2025A&A...697A.161M` (70 GBM+LLE, lags vs prompt properties);
    Peng+2024 `2024ApJ...969...26P`.
- **✅ MacLachlan MTS band RECOVERED** (the band Sonbas never states): **Fermi/GBM NaI only
  (brightest ~three), summed over the FULL NaI acceptance 8 keV – 1 MeV *including the >1 MeV
  overflow*, 200 μs bins, NO background subtraction.** Stated only in MacLachlan+2013
  (`2013MNRAS.432..857M` = arXiv:**1201.4431**); the 2012 Letter (`2012MNRAS.425L..32M` =
  arXiv:1205.0055) inherits it. ⚠ **Consequence: Sonbas's MVT axis is band-heterogeneous TOO** —
  prompt MVT over 8 keV–1 MeV (GBM NaI) vs XRF MVT from Swift/XRT 0.3–10 keV. So BOTH axes of
  her Fig 3 mix bands, not just the lag axis (§2.3 is worse than stated). Add: no background
  subtraction on the MVT light curves.

### 🔴🔴🔴 THE PHYSICS CHANGED — the curvature NULL is CHALLENGED (verified 2026-07-31)
**Uhm & Zhang 2016, ApJ 825, 97** (`2016ApJ...825...97U`, arXiv:1511.08807) — full title
*"Toward an Understanding of GRB Prompt Emission Mechanism. I. The Origin of Spectral Lags"*
(the short form is only the subtitle — cite the full one). Full text read; §2.2 is titled
**"Curvature effect cannot interpret the observed spectral lags."**
- **Their result: for any realistically CURVED (Band-like) co-moving spectrum, the high-latitude
  curvature effect produces ZERO spectral lag.**
- **Their alternative:** lags come from the spectral peak SWEEPING DOWN through the observing
  bands, driven by magnetic-field decay B ∝ r^−b (b ≥ 1) plus rapid bulk acceleration Γ ∝ r^s
  (s ≈ 0.35) in an optically-thin, expanding, Poynting-flux-dominated shell.
**⇒ This is a competing, quantitative, high-profile prediction that our null must confront.**
It is NOT a footnote: our null hypothesis ("lags are curvature-produced ⇒ slope 1, norm
E_h/E_l−1") is exactly what Uhm & Zhang argue cannot happen.

**THE THREE-WAY TENSION = THE PAPER.** Three verified, mutually-straining results:
| source | claim |
|---|---|
| Göktaş+2025 (`2025JARNA..11...27G`) | source-frame lag vs MTS, **slope 1.01±0.04** → "curvature" |
| Uhm & Zhang 2016 (`2016ApJ...825...97U`) | **curvature gives ZERO lag** for a curved spectrum |
| Li+2026 (`2026ApJS..283...47L`) §IV.2 | "**the spectral lag appears to trace the radiative evolution** … while **the MVT is primarily linked to the geometric scale** of the emission region" |
If curvature produces no lag (U&Z), why does lag track MVT with slope ≈1 (Göktaş)? And if lag is
radiative while MVT is geometric (Li), why do they correlate at all? **Exactly three ways out,
and our design can separate them:**
 (a) Göktaş's slope-1 is an ARTIFACT — (1+z) co-scaling + range inflation + observer-band MTS;
     our rest-frame, band-matched, single-pulse redo would expose it;
 (b) U&Z's zero-lag result doesn't apply in the relevant regime (their assumptions on the
     co-moving spectrum / shell dynamics);
 (c) **both axes track Γ and R** → correlation without causation — **which is precisely the
     Γ-confound our partial-correlation control was built to catch.**
⇒ Reframe the three-way outcome map as a test between NAMED MODELS (curvature-Kocevski/Zhang06
vs Uhm&Zhang-2016 sweeping-peak), not between vague "geometry vs cooling". That is a
significantly stronger paper, and the Γ-control moves from a guard to a HEADLINE result.

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
**Actionable robustness tests (Vikas — these decide intrinsic vs instrumental):**
- **T-a GBM physical-background test:** redo the Hakkila triple-peak fit on GBM but
  with a PHYSICAL background model (Earth albedo + cosmic rays + detector intrinsics)
  instead of the polynomial — the polynomial likely absorbs the soft power-law tail.
  Peaks survive → intrinsic; wash out → partly instrumental. (Our GBM backgrounds are
  polynomial today — a real, buildable discriminator.)
- **T-b NCP-prior / forced-single-pulse robustness:** Hakkila raised the Bayesian-
  Blocks NCP prior to FORCE one pulse per burst; some may be two overlapping pulses.
  Re-run across NCP values; report which "single pulses" are prior-dependent. Directly
  bears on #37's N_peaks=1 cut (a nested-shock triple-peak is one pulse by MEPSA but
  three injections physically).
**Model gap (crisp):** curvature + single-episode models predict NEITHER multi-peaked
shapes NOR re-hardenings; Kino+2004 internal shocks (FS/RS/CD) overlap too much to
disentangle; Bošnjak&Daigne 2014 synchrotron fits only with ad-hoc microphysics;
multi-component spectral models (Burgess+2011) EXIST but are NOT tied to specific
light-curve features. That un-bridged LC-feature ↔ spectral-component gap is the opening.
**AstroGraph watch (epistemic-debt example):** Hakkila documents the 3-peak
phenomenology meticulously, but theorists tend to CITE it without treating the
structure as a model CONSTRAINT. Track: does anyone use the triple-peak as a test, or
cite-and-ignore? (mirrors the Atteia beaming gap in #40.)
**✅ Lineage bibcodes VERIFIED 7/7 (wf w6wsz2vqm, 2026-07-31):**
- Hakkila & Preece **2011**, ApJ 740, 104 — `2011ApJ...740..104H`
- Hakkila & Preece **2014**, ApJ 783, 88 — `2014ApJ...783...88H` (Bessel residual-wave method)
- Hakkila, Lien, Sakamoto+ **2015**, ApJ 815, 134 — `2015ApJ...815..134H` (Swift; this read)
- Hakkila, Horvath, Hofesmann & Lesage **2018**, ApJ 855, 101 — `2018ApJ...855..101H` (short GRBs)
- **Hakkila & Nemiroff 2019**, ApJ 883, 70 — `2019ApJ...883...70H` (⚠ handoff called it "Nemiroff
  2019" but **Hakkila is first author**)
- Hakkila **2021**, ApJ 919, 37 — `2021ApJ...919...37H` (temporal symmetry, ~86% of BATSE)
- Hakkila, Pendleton, Preece & Giblin **2024**, ApJ 966, 13 — `2024ApJ...966...13H` (lateral jet motion)

───────────────────────────────────────────────────────────────────
## #40 — GRB bright-end energy & luminosity functions (Atteia-style)  💡
*(nominated 2026-07-31, Vikas, after reading Atteia et al. 2017 arXiv:1702.02961)*
**⚠ PLACEMENT: reading-nominated here; may graduate to the lab-wide idea bank
(~/Desktop/Projects/Projects_Details.md) — NOT yet added there. Ask Vikas.**

**Core of Atteia+2017:** the GRB E_iso distribution needs a SHARP cutoff above
1–3e54 erg, confirmed independently by Fermi/GBM (52 GRBs) and Konus-Wind (69),
z=1–5; Konus (more energetic events) drives it; cutoff required at >99.8% under all
3 world models (SFR-only / +density-evol / +lum-evol). The 8 most energetic (>2.3e54)
are longer & higher-Ep but NOT specially distant → the cutoff is not a redshift
artifact; LAT-detected ones are E_iso LOWER LIMITS. Physical origin UNRESOLVED — max
jet energy budget vs max radiative efficiency vs min opening angle — because beaming
factors are scattered and the energetic sample lacks the radio calorimetry to measure E_j.

**The project (Vikas's scope):** build cumulative N(>X) distributions in the Atteia
style for E_iso, L_iso, L_p, AND E_k (beaming-corrected), possibly peak flux. Ask
which SATURATE, which don't, and whether the cutoffs are physically COUPLED (E_iso =
total budget vs L_iso = peak power — a burst can be brief-intense or long-moderate, so
cutoffs need NOT coincide). For E_k: test Ghirlanda-type "beaming-corrected E ≳1e52 ⇒
black-hole engine" claims — but as a DISTRIBUTION SHAPE, not a threshold assertion
(ties to idea-bank #25 "don't collapse a distribution when the distribution is the physics").

**Highest-priority check (staleness) — ✅ VERIFIED 2026-07-31 (wf w6wsz2vqm):** GRB 221009A
(the BOAT) has E_iso ≈ **1.0–1.5×10⁵⁵ erg** (Konus Frederiks+2023 `2023ApJ...949L...7F`
1.2e55; GBM Lesage+2023 `2023ApJ...952L..42L` 1.0e55; HXMT/GECAM An+2023 `2303.01203`
1.5e55) — **~4–15× ABOVE** Atteia's 1–3e54 max. BUT z=0.15095 is OUTSIDE Atteia's z=1–5
sample, and Burns+2023 (`2023ApJ...946L..31B`) call it a **once-per-~10,000-yr** event →
a rare nearby tail draw, NOT a hard-limit violation; collimation-corrected E_γ plausibly
ordinary. **➡ START HERE: Atteia HIMSELF revisited this — Atteia 2025, ApJ 980, 241
(`2025ApJ...980..241A`), "GRB 221009A and the Apparently Most Energetic GRBs."** Read that
FIRST; our value-add is the multi-quantity distribution shape (below), not re-deriving 221009A.

**Faint-end counterpart — ✅ paper identified:** Atteia is z-selected → biased bright; the
faint end & the MINIMUM-GRB-energy question are unconstrained. **O'Connor+2025, ApJL 993,
L37 (`2025ApJ...993L..37O`, arXiv:2509.07141)** places Einstein Probe transients on the
Ep–Eiso plane from EP fluxes + z and finds an **"extension at the faint end of the Eiso
distribution"** — the faint-end population we want. Also Guo+2025 (FXT rate + LF,
arXiv:2510.13533), Li+2025 (arXiv:2510.10267). Links to idea-bank #2 (FXT+EP, Partha) & #20.

**AstroGraph gap examples this paper hands us (feed idea-bank #8):**
- (A, inherited claim) — **✅ gap CONFIRMED REAL:** Atteia leans on Turpin+2016
  (`2016ApJ...831...28T`: z/optical-selection doesn't bias the ENERGY distribution). Verified
  it has only **12 citers** and was **never independently re-tested** on a larger joint
  Fermi–Swift sample 2016–2026 (cited/built-on by the same Toulouse group only). A clean,
  buildable re-test.
- (B, author-acknowledged gap) Atteia says the cutoff's origin (E_j vs η_j vs f_b) can't be
  decided without accurate beaming angles + jet energy budgets, specifically RADIO
  CALORIMETRY of energetic-GRB afterglows. Open: did anyone do that follow-up, or cite-and-move-on?

**Companion paper — ✅ ANSWERED = NO:** Atteia did NOT publish a max-L_iso / max-L_p companion
(ADS first-author 2017–2026, 36 records, none on max luminosity). So max-L_iso / max-L_p is
**open ground** — our Liso/Lp distributions are a genuine gap, not a duplicate. Standard-candle
angle (§4.4): ~5 energetic GRBs/yr; Hubble diagram at z≳1.5 IF the cutoff doesn't evolve — speculative.

───────────────────────────────────────────────────────────────────
## #41 — Einstein Probe flare TIMING (lag / rise-time / MVT)  ⏸ CONDITIONAL — GATED
*(nominated 2026-07-31, Vikas, Sonbas+2013 reading session §5)*
**STATUS: GATED ON DATA AVAILABILITY. DO NOT SCOPE THE ANALYSIS until the three gates below
are answered.** Registered so the idea is banked, not so work starts.

**Idea:** repeat the lag / rise-time / MVT analysis (#37 machinery, Sonbas+2013 lineage) on
**Einstein Probe** flares/transients. EP reaches FAINTER events than Swift and — unlike Swift's
faint end — EP events ARE getting redshifts, so the population may be usable where Swift's is not.

**THE THREE GATES (answer factually before any scoping):**
1. Has EP released **public light curves** with sufficient **timing resolution** for MVT
   extraction? (WXT/FXT time resolution; public archive + data-release policy.)
2. Are **redshifts** available for a usable number of EP transients?
3. Is EP's **energy coverage** sufficient to define **two bands** for a CCF spectral lag?
   (WXT ~0.5–4 keV, FXT ~0.3–10 keV — can either be split?)
**✅ GATES ANSWERED 2026-07-31 (wf whkt5d73d) → VERDICT: WAIT, do not scope.**
1. **Timing — PARTIAL-YES on paper, NO in practice.** WXT instrumental resolution 50 ms; FXT
   reaches 44 μs in timing mode (`2025RAA....25a5002Z`); an EPSA/NADC public archive with L2
   event files + L3 light curves exists (first batch 2025-12-11, **FXT-only**; WXT "planned early
   2026", release status as of mid-2026 UNCONFIRMED). **But WXT's 2–3 cm² effective area forces
   ~seconds-scale binning even for the brightest events ⇒ sub-second MVT is NOT extractable.**
   This is the gate that fails, and it fails on photon statistics, not policy.
2. **Redshifts — PARTIAL-YES.** 26 secure spectroscopic z out of ~113 publicly reported EP/WXT
   transients as of 2025-08-29 (~23%), growing at ~70–80 extragalactic transients/yr
   (O'Connor+2025 `2025ApJ...993L..37O`). Usable and improving.
3. **Two bands for a CCF lag — YES formally, WEAK physically** (WXT 0.5–4 keV; FXT ~0.3–10 keV
   — splittable, but the lever arm is short). Mission refs: `2025SCPMA..6839501Y`, `2022hxga.book...86Y`.
→ **DECISION: WAIT.** Revisit when (a) WXT L2 event data is confirmed public AND (b) a bright-event
subset with enough counts for sub-second timing is identified. The redshift side is the healthy
part; the timing side is the blocker. **FXT (44 μs) is the workaround worth watching** — if FXT
catches flares with counts, gate 1 flips.

**Why it is attractive if the gates open:** it is the faint-end counterpart of the SAME timing
test, on a population that (uniquely) has redshifts at low luminosity — the regime where the
curvature-vs-cooling discriminant has never been tested.
**Links:** #37 (method + curvature test), #40 (EP as the faint-end energy population —
O'Connor+2025 `2025ApJ...993L..37O`), idea-bank #2 (FXT+EP, Partha) & #20 (blind FXT search).

───────────────────────────────────────────────────────────────────
## #42 — TWO-ARM pulse/shape physics: Gowri (photosphere) vs Rahaman-Granot-Beniamini (FS+RS internal shocks)  🔬
*(Vikas, 2026-08-03: "this is their method; so yes we can adopt that exactly and reproduce
their results on single pulse GRBs; on the other hand we will ourselves be using
Rahaman, Granot, Beniamini work and see how is it.")*

**⚠ THIS IS NOT A SIDE PROJECT — RGB2024 speaks to the CORE Two_Breaks question.**

### ARM A — reproduce Gowri+2025 EXACTLY on our single-pulse sample
**Gowri, Pe'er, Ryde & Dereli-Bégué 2025, ApJ 991, 230** (`2025ApJ...991..230G`,
arXiv:2409.17860). Their protocol is now IMPLEMENTED VERBATIM in the handbook
(`grb_pipeline/analysis/temporal.py`, 2026-08-03):
- two-sigmoid pulse `I(t) = (A/4)[1−tanh((t−r_r)/s_r)][1+tanh((t−r_l)/s_l)]`, **φ = s_l/s_r**;
- **`r_l ≤ r_r` enforced exactly** via reparameterisation `r_r = r_l + dr`, `dr ≥ 0`
  (⚠ the circulated summary said `r_l ≥ r_r` — INVERTED; that would collapse the pulse to ~0.
  Paper §2.2 verbatim: *"we always require rl ≤ rr"*);
- **≤300 bins** before curve_fit (paper §2.2); **r² = 1 − RSS/TSS**, keep r² > 0.7 (§2.1),
  reported as a flag not a hard reject;
- φ classes from their Fig 2: **<0.3 FRED-like | 0.3–1 mixed | >1 symmetric-like**.
**Their physics claim to test:** pulses get more asymmetric AND spectrally softer with pulse
number ⇒ a transition from **photospheric** (symmetric-like + hard) to non-thermal emission
above the photosphere; implies **low Γ ~ few tens** (τ ~ R/Γ²c), colliding with canonical Γ~100s.
**Our angle:** Gowri's trend is defined over MULTI-pulse bursts (φ vs pulse-number, ≥2 pulses).
**Our sample is single-pulse** — so we cannot reproduce the ordinal trend directly; what we CAN
do is (a) reproduce the φ distribution (their 26% symmetric / 51% FRED / 23% mixed) on clean
single pulses, and (b) test α_max vs φ, α_max vs duration, φ vs duration per-pulse. **State
that limitation up front — do not silently re-map their pulse-number axis onto our sample.**

### ARM B — our own: Rahaman, Granot & Beniamini 2024, MNRAS 528, L45
**`2024MNRAS.528L..45R`, arXiv:2308.00403**, *"Prompt gamma-ray burst emission from internal
shocks — new insights"* (⚠ author is **Rahaman**, S. k. Minhajur — not "Rahman").
Each shell collision makes a **shock PAIR**: a forward shock (FS) into the slower leading shell
and a **stronger reverse shock (RS)** into the faster trailing shell. Optically-thin synchrotron
from **both** reproduces pulse shapes, the νFν peak-flux/peak-energy evolution, and the spectrum.

**WHY THIS IS THE CORE OF OUR PROJECT — it predicts BOTH shapes our census hunts:**
> abstract: *"it can account for two features commonly observed in GRB spectra: (i) a
> sub-dominant low-energy spectral component (often interpreted as 'photospheric'-like), or
> (ii) a **doubly-broken power-law** spectrum with the low-energy spectral slope approaching the
> slow cooling limit. Both features can be obtained while maintaining high overall radiative
> efficiency **without any fine tuning**."*
> §4: *"the low frequency bump is due to FS while the high energy emission is due to RS. While
> observationally, the low-energy bump is typically interpreted to be of photospheric origin,
> **our model suggests a weaker FS as a natural alternative candidate**."*
⇒ **Our `+BB` winners (Band+BB, CPL+BB, SBPL+BB) may be a weaker FORWARD SHOCK, not a
photosphere.** ⇒ **Our `DSBPL`/two-break winners are exactly their "doubly-broken power law".**
The project name is *Two_Breaks*; RGB2024 is a one-mechanism physical origin for the two-break
shape AND for the low-energy excess — from the SAME collision, no fine tuning, no photosphere.

**THE TWO ARMS GENUINELY DISAGREE — that is the point:**
| observable | Gowri+2025 reads it as | RGB2024 reads it as |
|---|---|---|
| low-E excess (`+BB`) | photospheric component | **weaker FS** synchrotron bump |
| symmetric + hard early pulse | photosphere, low Γ (~tens) | FS/RS hydrodynamics, no photosphere needed |
| two-break spectrum | (not addressed) | **FS+RS doubly-broken PL**, low-E slope → slow-cooling limit |
| pulse-shape change with frequency | radial transition of dissipation site | hydrodynamic: *"accounts for the change of pulse shape at a fixed frequency"* |
**Do not inherit one side.** The census is empirical (paper theme 2026-07-17: hunt ALL shapes, no
model preference); ARM A and ARM B are two physical readings applied AFTER the shapes are measured.

### Concrete first tests on our data
1. **Every `+BB` bin we have** (burst #3 blk3: kT=44.8 keV, LRT=7.7): does the FS interpretation
   fit as well as a blackbody? RGB predicts a synchrotron BUMP, not a Planck function — that is
   a **shape-level discriminant** we can fit (add an FS+RS-motivated component to the menu).
2. **Every `DSBPL` winner** in the census: is the low-energy slope consistent with the
   **slow-cooling limit** RGB predicts? That is a falsifiable number, not a narrative.
3. **Pulse shape vs frequency** (RGB: shape changes with energy band at fixed burst): measure
   φ and the KRL slopes **per energy band** on our single pulses — RGB predicts a specific
   change; Gowri's φ is measured in one band only.
4. Γ constraints (afterglow onset / MVT / opacity) to referee Gowri's low-Γ requirement.

**Links:** the empirical census IS the input to both arms (`results/clean_per_burst_*`);
`GRB_InternalShocks` (RA-1) — RGB2024 is that project's theory backbone; idea-bank **#9**
(synchrotron modeling algorithm) and **#17** (Gowri is a collaborator there);
SinglePulse_Temporal correlation #2 (KRL d / φ → engine); #39/#30 Hakkila lineage — Gowri's
26% symmetric population directly revises Hakkila's universal-FRED claim.
**Both PDFs in `Skills_training/` and indexed (read=N).**

───────────────────────────────────────────────────────────────────
### #42 UPDATE — Arm B now has a SKILL, and its central test is already ANSWERED (2026-08-07)

**Installed:** `.claude/skills/grb-two-shock-analysis/` — a Claude Skill built by ChatGPT with
Vikas after reading RGB2024 (SKILL.md + 7 reference notes + 2 report templates). Kept in its
native skill layout so it is INVOCABLE, not flattened into `dev/ai_guides/`.
**Its best features, adopted as doctrine:** a **source hierarchy** (PAPER / PROPOSAL / INFERENCE /
EXTENSION — *"never silently promote an inference into a published result"*), and constraint #1:
*"Do not fit two independent arbitrary components and call that the physical two-shock model"* —
the FS and RS must be **hydrodynamically coupled**, which is what separates Arm B from just adding
another additive component to the menu.

**Its case study is OUR burst #5 (GRB 130310A), and we independently reproduce every Qin number:**
| Qin/skill | our blind fit |
|---|---|
| early Band Ep 7.4–11.1 MeV | blk1 8.26, blk2 12.37, blk3 7.41 MeV ✓ |
| early BB kT 5–7 keV | blk2 5.53, blk3 5.64 keV ✓ |
| later Ep ~1 MeV | blk5 0.82, blk6 0.80, blk7 0.93 MeV ✓ |
| T90 ~2.4 s | 2.09 s ✓ |

**⭐ Their §3.1 central question — *"does the low-energy component remain necessary as a thermal BB
after physically allowed nonthermal curvature is included?"* — is ALREADY ANSWERED by our
walkthrough fit.** blk2 [4.107,4.131] s, the only block that decisively needs extra structure
(ΔAIC = 26.0 vs the best simple continuum):
| model | ΔAIC | VALID |
|---|---|---|
| **SBPL+PL** | **0.0** | ✓ |
| CPL+BB+PL | 0.8 | ✓ |
| CPL+PL | 1.1 | ✓ |
| Band+PL | 1.1 | ✓ |
| SBPL+BB | 1.8 | ✓ |
| Band+BB | 4.0 | ✓ |
| SBPL / 2SBPL / CPL / Band | 26.0 / 28.3 / 29.7 / 31.8 | — |
⇒ **"Extra component necessary?" YES, decisively. "Necessary as a BLACKBODY?" NO** — a purely
nonthermal `SBPL+PL` wins outright and `CPL+BB+PL` trails by 0.8 AIC (~1.5:1, indistinguishable).
**Qin's photospheric interpretation is not required by the data.** This is the strongest empirical
result the walkthrough has produced, and it is exactly the FS-vs-photosphere question RGB2024 poses.

**What is still MISSING (the real Arm-B work):** their §3.1 list also needs a **single-zone
synchrotron** model and the **coupled FS+RS** model. We have neither in the menu — everything above
is still empirical additive components. The skill's §3.5 warns explicitly that RGB2024 explains
*relative* structure and normalized evolution, and does **not** by itself prove the baseline
microphysics can make an absolute 5–11 MeV RS peak: *"Do not claim that the two-shock model solves
the extreme E_pk problem until this absolute scaling is checked."* Honour that.
**Next:** implement the coupled FS+RS spectral model as an astromodels component and refit blk2.

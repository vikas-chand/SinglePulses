# Reading-group answer sheet — Yu+2019 (ApJ 886, 20), COMPLETE & keyed to Vikas's numbering
Rewritten 2026-07-30 against the full chat (~55 numbered Qs). Legend: ✓ confident ·
⚠ citation to verify · ？ needs Vikas · ★ project. Grounded by Vikas's 125 PDF marks.

**Verified citations this pass:** Golenetskii+1983 Nat 306,451 (L∝T; "time profile
reflects spectral variability"); Nappo+2014 MNRAS 445,1625 (precursor afterglows);
Nappo+2017 A&A "Some like it thermal" GRB151027A ⚠(the aa28801-16 link — verify
bibcode); **Gor = Oganesyan+2026 A&A 710,L37** (back-scattered X-rays γγ-absorb MeV
→ pairs → broad absorption feature whose profile depends on α); SSA burst = **Varun,
Zhang & Zhao 2026 ApJ 998,90** (GRB241030A fast-cooling synchrotron, joint
Swift-Fermi, z=1.411); Golenetskii UPDATE = Burgess+2019 MNRAS 485,1262 (rest-frame,
hierarchical Bayes) + Borgonovo & Ryde 2001. Guiriec+2011 ApJ 727 L33 (Band+BB).

═══════════════════════════════════════════════════════════════════
## ABSTRACT — Q1–7
═══════════════════════════════════════════════════════════════════
**1. What did they leave for us?** ✓ Composites (no BB/2-break/explicit cutoff —
they fit only CPL+Band); wideband (GBM-only, no LLE/LAT); bigger+shape-selected
sample (ours: 70/106 pass their own S≥20 bar); physical-model mapping; the α>−2/3
photosphere cases uninterpreted; cutoff genuineness untested (their own open Q).

**2. Why only two models (CPL + Band)?** ✓ Bayesian/MCMC-per-bin is expensive →
few models; single functions keep parameters comparable across bins for clean
evolution tracks (composites add degeneracy). CPL preferred by DIC (your p.1 mark).

**3. Why DIC?** ✓ Bayesian analog of AIC/BIC when you have MCMC samples:
`DIC = D(θ̄)+2p_D`, `p_D = mean-deviance − deviance-at-mean` (effective #params).
Cheap from MCMC output. Caveats: not reparam-invariant, poor for non-normal
posteriors (WAIC/LOO now preferred). Ours = ΔAIC≥10 (MLE); ΔDIC≳10 ≈ same bar.

**4. Are α>−2/3 bursts useful?** ✓ They're the payload: α>−2/3 breaks the
synchrotron line-of-death → demand photospheric/thermal/subphotospheric models.
Yu: **60% of pulses inconsistent with synchrotron** (α_max test, p.7–8). Our
burst #1 (bn081125496) opens at α=+0.14 — one of these.

**5. Studies where BB softens the >−2/3 hardness; why didn't Yu try?** ✓/⚠
Physics: fitting Band/CPL to (steep synch + BB bump) returns an artificially HARD
α; an explicit BB absorbs the bump → α relaxes to physical (softer). Support:
Guiriec+2011 ✓, Guiriec+2015 ⚠, Axelsson+2012 (on disk) ⚠, Burgess+2014 ✓, Ryde
2004/05 ⚠. Why not Yu: single-function scope (comparability+cost). = our extension.

**6. Does α–F change under a different preferred model? Gor's pair-wind cutoff →
α<−1 — will we see it?** ✓/★ α is model-dependent (Li+19) → α–F shifts with the
preferred model. Gor = **Oganesyan+2026 A&A 710 L37**: γγ-absorption by
back-scattered X-rays makes a broad absorption feature whose profile depends on α;
his picture ties MeV-cutoff bursts to softer α. **★ TESTABLE (=Result-Q1/Proj#34):
cross-tabulate cutoff/absorption-preferring bins vs α, predict α<−1 there.**

**7. Posterior/likelihood; why Bayesian with flat priors?** ✓ Posterior ∝
likelihood×prior. Likelihood is CORRECT (your p.3 mark): S "suitable for Poisson
source + Gaussian background (Vianello 2018)" = pgstat, not χ². Payoff even with
flat priors (your p.2 mark): "background incorporated as a nuisance parameter,
marginalized out" — plus asymmetric errors, honest multimodality (our L5/L8!),
model evidence. Our MLE+multistart+MINOS = brute-force version of MCMC exploration.

═══════════════════════════════════════════════════════════════════
## INTRODUCTION — Q1–3
═══════════════════════════════════════════════════════════════════
**1. BB+SBPL = two processes; as PI break the degeneracy (no polarimeter)?** ✓
Yes (thermal photosphere + non-thermal synch), or one Comptonized photosphere
faking both. Existing-telescope handles: wideband lever arm (RJ +2 vs synch −2/3 at
low-E; GeV at high-E), spectral-timing (kT∝t^−2/3 vs Ep∝flux evolve differently),
the sub-BB-peak slope, and SSA (→ Proj#33). Polarization cleanest but not the only.

**2. Combine temporal+spectral? What evidence for emission mechanisms?** ✓ Not
naively (binning smears evolution — the reason for BB). Triangulate: spectral shape
(α vs line-of-death, curvature, breaks) · evolution (h.t.s./i.t., Golenetskii) ·
polarization · MVT/variability (dissipation R) · lag · Ep evolution · low-E index
(cooling regime) · high-E cutoff (pair opacity→Γ) · afterglow · z→E_iso · multi-λ.

**3. Empirical→physical map vs start physical (the 'if')? problems?** ✓ Start-
physical problems: assumes mechanism before testing (confirmation bias); expensive
(Burgess table models); own degeneracies (many params/few constraints); misses
out-of-menu shapes. Empirical-first = model-agnostic shape census (OUR theme) then
map. Genuine fork: we empirical-first, Burgess physical-first. Jagdish's instinct
(data first, models are observation-inspired) = the pragmatic standard.

═══════════════════════════════════════════════════════════════════
## I1P3P4 (intro p.1, para 3–4) — Q1–3
═══════════════════════════════════════════════════════════════════
**1. Why is Ryde's BB rare; GRB or MGF; if GRB uniquely interesting?** ✓/⚠
Rare because most GRBs are synch-dominated; pure Planck = exception. MGFs mimic
short GRBs with thermal spectra → some "thermal GRBs" may be misclassified MGFs.
If genuine GRB: cleanest photosphere views (direct Γ, R_ph) — uniquely worth it.
⚠ Ryde 2005 = "Planck+PL" (your p.1 mark); Guiriec+2015b = "pure blackbody".
★ **Project #33 — SSA in prompt emission** (Varun+2026 ApJ 998,90, simultaneous UV;
Binbin's student's idea): search the low-E synchrotron self-absorption break. NB
Vikas: "low-E SSA — it's still ν_m I guess" — the SSA turnover vs ν_m distinction
is the subtlety to nail.

**2. All Guiriec models; why additive Band+CPL not a SADDLE; did that delay Gor 15
yr?** ✓/⚠ — THE SHARPEST. Guiriec: Band+BB (2011) → 3-component Band+BB+PL (2015).
He read the extra hard feature as a **separate additive component** not a **saddle/
concavity within one continuum**. Had it been modeled as a saddle in Band's β
region, the later low-E-break work (Oganesyan+2017) could have come earlier. **This
is exactly our L12 degeneracy** (additive-BB vs continuum-reshape-2SBPL are one
shape) — the historical instance of what we now name and merge.

**3. Who was Nappo; "Fireball Reborn"; why did he leave?** ✓/⚠ Nappo+2014 MNRAS
445,1625 = precursor afterglows (precursor gets its own fireball — "Fireball Reborn"
theme). Nappo+2017 A&A "Some like it thermal" GRB151027A (the aa28801-16 link ⚠
verify). Deeper Q "does it resolve the degeneracy?": Khushboo — "obviously False" ✓;
stays unsolved without independent info. (Why he left academia = human, not physics.)

═══════════════════════════════════════════════════════════════════
## I2P1P2 (intro p.2, para 1–2) — Q1–9
═══════════════════════════════════════════════════════════════════
**1. What is the Golenetskii correlation?** ✓ Golenetskii+1983: instantaneous
L∝T-ish → flux and Ep (hardness) track each other within a burst; "time profile
reflects spectral variability." Modern form F∝Ep^~1.5 (Borgonovo&Ryde 2001;
rest-frame hierarchical version Burgess+2019). Our F–Ep relation IS this.

**2. T/F: time-INTEGRATED spectra fingerprint the mechanism; skip time-resolved?**
✓ FALSE. Integrated spectra are averages over evolving states → the shape is a
superposition artifact (a Band-looking integrated spectrum can hide evolving
CPL+BB). Only time-resolved directly infers physics (Yu p.2 mark). Ryde&Svensson
1999 show integrated can be used only indirectly.

**3. Most important importance of time-resolved; resolve degeneracy or not?** ✓
It removes the averaging artifact and reveals parameter EVOLUTION (the discriminant
between mechanisms — h.t.s. vs i.t., Golenetskii tracks). But it does NOT uniquely
resolve the per-bin model degeneracy (BB vs 2-break still degenerate in one bin) —
degeneracy stays; evolution + wideband + other evidence break it. (Same as our
L12/L13.)

**4. What limits time-resolved analysis?** ✓ Counts: finer bins → lower S/N →
parameters unconstrained. The binning trade-off (Yu p.2 mark: too coarse = evolution
smeared; too fine = no signal). Also detector energy coverage + response quality.

**5. Why not uniform / uniform-significance bins vs Bayesian blocks; only Burgess?**
✓/⚠ Uniform bins mix evolving states or waste S/N; uniform-significance bins ignore
where the LC actually changes. BB puts edges at genuine intensity changes (≈
spectral changes, via Golenetskii). Support: Scargle+2013 (method, general), Burgess
2014 (the GRB evolution-preservation claim). ⚠ is there a 2nd evolution-preservation
demo beyond Burgess? — worth a check.

**6. Why did Binbin & Michela write their own BB from scratch; should AI write one
solving every Scargle+2013 equation?** ✓/★ Because the "preserves Ep evolution"
use needs control over the fitness function + ncp_prior that off-the-shelf BB
doesn't expose; likely Burgess too. ★ YES — I can produce
`notes/scargle2013_derivation.md`: event/binned/measures fitness, ncp_prior, the
O(N²) DP recursion, each equation solved. (Michela = ⚠ confirm surname.)

**7. When does background variability start affecting the bins; when ignorable?** ✓
When the background's rate-of-change over the burst is comparable to the source's
intensity changes, BB edges get driven by background not source. Ignorable when
background is flat on the burst timescale (short bright bursts) — the usual case
after polynomial subtraction.

**8. Resolution when a varying background is present + we build BB?** ✓ Model/subtract
the background FIRST (Scargle assumes the blocked rate IS the signal) — polynomial
per channel (our 27b; Yu p.3), or block on background-subtracted counts. Never block
raw counts through a varying background.

**9. Non-homogeneous Poisson series; correction; MVT impact if uncorrected?** ✓ A
Poisson process whose rate λ(t) varies in time. Correction: normalize by the
exposure/background rate (Scargle's "cell" weighting handles variable exposure) so
the fitness reflects source only. MVT: uncorrected background variability injects
spurious power across timescales → biases MVT low/high. Ties to our MVT-audit memo.

═══════════════════════════════════════════════════════════════════
## METHODS / DATA — Q1–11
═══════════════════════════════════════════════════════════════════
**1. Effective areas of hard/soft X-ray telescopes compared?** ✓ Soft-X (Swift-XRT
0.3–10 keV, ~110 cm²; focusing) → high A_eff, narrow band. Hard-X/γ (GBM NaI
8–1000 keV ~126 cm² geometric, non-focusing; BGO to 40 MeV; LAT >100 MeV, ~m²
effective but tiny photon flux). Trade band vs collecting area; γ-detectors are
non-focusing so A_eff = physical area × response, angle-dependent.

**2. T/F: curvy (structured) A_eff curves preferred over flat?** ✓ FALSE (for
calibration) — a flat A_eff means the response doesn't imprint features on the
spectrum; sharp A_eff structure (edges, dips) can create/hide spectral features and
must be modeled precisely. Flat is cleaner; structured needs a trustworthy RSP.

**3. Known GBM systematics?** ✓ Energy-response/calibration uncertainty, the NaI
K-edge (~33.17 keV) dip, effective-area vs incidence angle, detector-to-detector
cross-calibration (→ our EAC), scattering off spacecraft/Earth, overflow high
channel, background variability. (Full list = Connaughton+2015, Q11.)

**4. T/F: with LAT available we will NOT fit jointly, just say true spectrum =
GBM-extrapolation?** ✓ FALSE — we DO fit jointly (our --include-lat, FermiLATLike).
Extrapolating GBM alone hides high-E breaks/cutoffs/extra components that only LAT
reveals (160625B!). Joint fit is the whole point of wideband.

**5. NaI K-edge — energy, channels, ok for temporal?** ✓ Iodine K-edge at
33.17 keV → a response discontinuity; we exclude the containing channels
(exclude 33–40 keV natively — the 2026-07-24 fix). For TEMPORAL analysis (counts,
not spectra) the K-edge doesn't bias timing → the channels are FINE to keep for
light curves/MVT/T90. (Good distinction: exclude for spectra, keep for timing.)

**6. Overflow channels — spectral? temporal?** ✓ The highest channel accumulates
all overflow energy → no defined upper bound → NOT usable for spectral fits (exclude
top NaI ~900 keV / BGO edge). For temporal (total counts) they can be kept but add
little. Standard: drop overflow in spectra, optional in timing.

**7. Why 60° not 80° NaI angle cut?** ✓ A_eff falls and angular systematics grow
steeply beyond ~60°; Goldstein+2012 convention. At 80° the response is poorly
calibrated and grazing → detector included would add more systematic than signal.
Trade coverage vs response reliability.

**8. Pulse shapes beyond Norris with theoretical roots?** ✓/⚠ Norris (FRED) is
empirical. Beyond: Genet & Granot (2009) analytic high-latitude pulse (curvature
effect — physical), Hakkila pulse-triplet, Kocevski et al. shapes; the
curvature-effect tail (t^−2−β) has a real emission-physics root. ⚠ pin exact refs.

**9. More same-energy detectors — 3>2, 4>3?** ✓ Yes, marginally — combining
independent detectors increases total counts → significance ∝ √N_counts, so more
detectors = higher S per bin (diminishing returns; cross-calibration cost via EAC).
Yu caps at 3 NaI + 1 BGO. Quantitative: S scales as √(added area).

**10. Data types (CSPEC/CTIME/TTE, GBM+LAT); purpose?** ✓ TTE = event list, full
time + 128-ch spectral res (best for fine BB + spectra). CTIME = 8 coarse channels,
high time res (timing/T90). CSPEC = 128 channels, 4.096 s (long/background spectra).
LAT: FT1 (events) + FT2 (spacecraft pointing/livetime). Purpose = trade time vs
spectral resolution vs file size; use TTE for our spectroscopy.

**11. Connaughton+2015 systematics?** ✓/⚠ The GBM localization/systematic paper:
location-dependent systematic (~3–4°), response/effective-area uncertainty vs
source position, the systematic error model added in quadrature. ⚠ read for the
exact enumerated list before quoting.

═══════════════════════════════════════════════════════════════════
## BACKGROUND — Q1–7
═══════════════════════════════════════════════════════════════════
**1. Background fit per channel — combined then channelwise, or channelwise
throughout?** ✓ CHANNELWISE throughout: a separate polynomial (order 0–4) is fit to
EACH energy channel's rate vs time (Yu p.3: "128 channels for TTE"), independently.
Not combined-then-split. Our 27b/3ML does the same (per-channel polyfit).

**2. Sources adding to background + how they vary?** ✓ Diffuse γ background, Earth
albedo/limb (orbital, ~90 min), particle background (geomagnetic latitude, SAA),
other sources in FoV, activation. Vary on orbital + geomagnetic timescales → the
polynomial captures the slow trend under the burst.

**3. Our bursts done with single intervals or difficult selections?** ✓ OUR
catalog schema = fixed 2 intervals (pre+post); all 435 detector-rows have both →
we used NO single-interval cases (unlike Yu's SAA 3-interval bursts). Difficult
cases exist in our notes (the 6 source-on-background fixes, 15 hug-rule offenders)
but the final catalog is uniformly 2-interval.

**4. Did we allow >2 intervals; helpful?** ✓ NO — our schema caps at 2 (neg+pos).
This is a real LIMITATION vs Yu (who used 3 near SAA). ？ Worth deciding whether to
extend the schema for SAA-adjacent bursts.

**5. How can we help AI select background + handle difficult cases?** ✓ Our
`dev/ai_guides/background_selection.md` (hug rule, width 50–150 s, QC). Difficult
cases (SAA, bright long tails, gaps) → the soft-warn GUI + provenance stamps. Room:
a 3rd-interval option; auto-flag SAA proximity.

**6. Same background intervals for all detectors or per-detector?** ✓ Per-detector
in principle (each has its own orbital/particle background), BUT Yu (p.3) picks the
brightest NaI to DEFINE the intervals, then applies to others. Our pipeline: same
time windows across detectors, per-detector polynomial fit. ？ per-detector window
selection is a possible refinement.

**7. OK if our source interval lands in another detector's background window?** ✓
NO — that's the source-on-background error we already caught + fixed (6 bursts,
background_intervals_clean). The hard gate at ingest prevents it. So: not OK, and
we enforce against it.

═══════════════════════════════════════════════════════════════════
## BAYESIAN BLOCKS — Q1–8
═══════════════════════════════════════════════════════════════════
**1. Why is BB-from-TTE slow; why binning faster?** ✓ Scargle's exact algorithm is
O(N²) in cells; TTE = one cell per photon → N huge → N² explodes. Pre-binning
collapses many photons into few voxels → small N → fast, at the cost of finest time
resolution. (The 27b design tension.)

**2. p-value vs significance; p=0.01 vs 0.001?** ✓ p = tolerated false-positive
rate for a spurious change point (sets ncp_prior). Smaller p = more conservative =
fewer blocks. 0.001 → very clean, risk merging real fast evolution; 0.01 → more
blocks, risk a spurious split. Sensitivity vs purity.

**3. Cited support that variability is dominated by lowest energy + high-E
variability missed due to counts?** ✓/⚠ Yu p.3: "spectral changes in high-energy
channels could be missed due to lower signal (Guiriec+2015a)." Physically low-E has
the most counts → drives the LC + BB edges; high-E is count-starved. ⚠ Guiriec+2015a
is the cite.

**4. Do dissipation-radiation models support energy-dependent variability
(R_diss↔cutoff, optical depth, radial/angular)?** ✓ Yes — in photospheric/internal-
shock models the variability timescale ties to R_diss (δt ~ R/2cΓ²); the MeV cutoff
(pair opacity) constrains R_diss and Γ; angular (high-latitude) vs radial
(shell-crossing) variability have different energy signatures. This is exactly the
cutoff→Γ→R_diss chain we can run.

**5. How does variability arise in the internal-shock model?** ✓ Central engine
emits shells of varying Γ; faster shells catch slower ones → internal shocks at
R_IS ~ Γ²cδt_eng; the engine's variability timescale δt_eng sets the LC spikes →
prompt variability reflects central-engine activity, not external medium.

**6. How does Golenetskii+1983 link spectral change ↔ variability; an update?** ✓
Answered (I2P1P2-1): L∝T → flux tracks hardness → fast flux change ↔ fast spectral
change. UPDATE = Burgess+2019 MNRAS 485,1262 (rest-frame Golenetskii, hierarchical
Bayes); also Borgonovo & Ryde 2001; a structured-jet photospheric version 2022
MNRAS 512,5693.

**7. Why S=20, ≥5 bins; do our bursts satisfy? channel-combining raise S? BB-
preserves-Ep GRB-specific?** ✓ S=20 = a bin bright enough for constrained CPL
params (Vianello 2018 S); ≥5 bins to see evolution. **OUR SAMPLE: 70/106 pass ≥5
bins at S≥20; 102/106 have ≥1; 4 time-integrated-only; median 8, max 224
(130427A).** Channel-combining DOES raise S (∝√counts) — quantifiable. BB-preserves-
Ep is Burgess-2014-specific advocacy; the METHOD (Scargle) is general across
astronomy (not GRB-only — answers Liz).

**8. End of §2 they promised more models for a complete study — did they deliver?**
✓/⚠ Your p.5 marks flag "a more sophisticated [selection]… out of scope of the
current paper." ⚠ Need to check whether a Yu follow-up ever did the full-menu study
(I can search their later papers). Likely NOT fully — which is our opening.

═══════════════════════════════════════════════════════════════════
## RESULTS — Q1–2  (both are PROJECTS)
═══════════════════════════════════════════════════════════════════
**★ Result-1 (Proj, Gor test):** are α<−1 the cutoff/absorption bursts? Predicted by
Oganesyan+2026 (absorption feature profile depends on α). Method: compute flux above
Ep, correlate with α; expect softer α where the cutoff/absorption is real. Yu's data
already usable + our full sample.

**★ Result-2 = PROJECT #34 (cutoff: intrinsic vs count-limited):** fit α FAR below
Ep, extrapolate above Ep, predict photon counts, compare to observed. Observed ≈
predicted → count-limited; observed ≪ predicted → INTRINSIC cutoff. Band-only (β +
Ep capture the rollover) on bright bins. **Yu STATED this exact degeneracy and left
it unresolved** (p.9: "BAND mimicking a cutoff OR poor count statistics"; their
Ec≈5 MeV cloud is a NOISE artifact that vanishes at S≥20, p.6–7). Our test resolves
it — byproduct of the full-sample run.

═══════════════════════════════════════════════════════════════════
## STATISTICS / §3.1 — Q1–2
═══════════════════════════════════════════════════════════════════
**1. Beyond DIC — what did Burgess use, how does it work?** ✓/⚠ Burgess uses
Bayesian evidence / WAIC-style and posterior predictive checks (⚠ confirm exact:
Burgess favors the marginal likelihood / Bayes factor and PPC over point-IC). Bayes
factor = ratio of marginal likelihoods (integrates over the prior) — the fully-
Bayesian model comparison DIC approximates.

**★ 2. Do IC's hide WHERE in energy the fit is good/bad; compare piecewise in 4
chunks?** ✓ — BRILLIANT + IMPLEMENTABLE. The fit statistic is SUMMED over energy →
decomposable. Per-energy-chunk ΔC-stat localizes where each model wins/fails → tells
the AI which component to add and WHERE. = our L11 residual-grammar + L4 per-plugin
decomposition generalized to per-energy-band. Concrete next engine feature.
(Reduced-χ²~1 goodness-of-fit comes first, yes — but it's a single number that hides
the energy structure; the chunked ΔC-stat is the fix.)

**Jagdish — DIC = "difference IC"?** ✓ No: DEVIANCE IC. Deviance = −2 lnL; DIC
penalizes by the effective # params p_D (not a model−data difference). See Q3 above.

═══════════════════════════════════════════════════════════════════
## PROJECTS surfaced (capture)
═══════════════════════════════════════════════════════════════════
- **#33 SSA in prompt emission** (Varun+2026 ApJ 998,90; simultaneous UV) — search
  the low-E SSA break; distinguish from ν_m.
- **#34 Cutoff intrinsic-vs-count-limited** (extrapolation test) — resolves Yu's
  own stated open degeneracy.
- **Gor test** (Result-1) — α<−1 ↔ cutoff/absorption, vs Oganesyan+2026.
- **Energy-chunked model comparison** (Stats-2) — implementable Discovery-Loop
  upgrade (L11/L4 generalized).
- **Saddle-vs-additive** (I1P3P4-2) — reframe L12 as the Guiriec/Oganesyan history.
- **Scargle+2013 full derivation** (I2P1P2-6) — `notes/scargle2013_derivation.md`.
- **α_max photosphere sub-sample** (Abstract-4) — 60%-non-synchrotron cut.

═══════════════════════════════════════════════════════════════════
## Verification debts before quoting
═══════════════════════════════════════════════════════════════════
⚠ Nappo+2017 A&A bibcode (aa28801-16); Guiriec+2015 3-comp; Ryde 2005 id;
Axelsson+2012 (read — on disk); Connaughton+2015 systematic list; pulse-shape refs
(Genet&Granot, Kocevski); Michela surname; Burgess's exact model-comparison
statistic; whether a Yu follow-up did the full-menu "complete study".

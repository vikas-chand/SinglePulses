# Skill: SpectralFitting — learn to fit like the published experts
> **PRECEDENCE (Vikas, 2026-08-10): read lessons NEWEST-FIRST, and on any conflict the LATEST
> lesson governs.** Numbering is chronological (L1 oldest), but maturity runs the other way —
> later lessons refine or supersede earlier ones (L18 refined L9; L27 refined the L9-era rail
> test). When consulting this file for a decision, start from the highest Lxx and work back.

## (blind-reproduce → diff → reconcile → distill)

**Purpose:** For a burst we have ALREADY analysed blind, compare our results with the
published arXiv literature, *explain* every difference by testing which analysis
choice causes it, and distill the learning into reusable rules. This is how the
pipeline learns to analyse like the published experts — without ever copying them.

**Audience:** AI agent (Claude/Codex) driving the Two_Breaks pipeline; humans check.
**Time required:** ~2–5 h per burst (dominated by P4 re-fits).
**Reusable:** every burst with a fit + literature; later, every new instrument.

**Why blind-first matters (the leakage answer):** our numbers exist BEFORE the paper
is read — the pipeline computed them from photons under the stamped catalog. The
deliverable is not an agreement score (memorizable) but a TESTED EXPLANATION of each
difference (a re-fit with one changed choice — not recallable from any PDF).

## Inputs
```yaml
trigger:        bn######### (must have a completed fit in results/clean_per_burst_*)
our_fits:       results/clean_per_burst_lle_v3/<trig>/ (or human_final for GBM-only)
lit_card:       notes/literature_tier1/<trig>.md   # candidate refs — UNVERIFIED
papers:         the actual arXiv PDFs (fetch; do NOT work from the card alone)
```

## Outputs
- `notes/reconciliation/<trig>.md` — the per-burst reconciliation record (P0–P5)
- an appended, deduped entry in **§Distilled lessons** below (P6)
- any pipeline fix the reconciliation forces (committed separately, with tests)

## Phase 0 — FREEZE the blind result
Extract from our ecsv (registry doctrine, `scripts/model_registry.py`): per-block
gated winner + class, key parameters (Ep, kT, α, break energies, cutoff EC) with
errors, and the qualitative verdicts (thermal? two-break? cutoff? extra PL?).
Record fit provenance (catalog stamp, blocks file, PLUGIN_DETS). **Do this before
opening any paper.** This table is immutable for the rest of the loop.

## Phase 1 — VERIFY the literature (house rule: no card-only claims)
Fetch each paper (arXiv). Extract into the card, with section/page quotes:
- which EPISODE and time intervals they analysed (trigger ≠ episode — see L1);
- detectors, energy range, binning, statistic (pgstat/χ²/Bayesian), CL convention;
- model menu they fit + any PRESCRIPTIONS (e.g. fixed smoothness n1/n2);
- best model per interval + parameters + errors, and their stated conclusions.
Mark anything not verbatim-verifiable as PENDING. Never invent values.

## Phase 2 — ALIGN the frames
Map their intervals onto our blocks (overlap table). Note every frame difference:
episode, detector set, energy band, binning resolution, parameterization,
selection statistic, validity conventions, Ep definition (νFν-peak vs E0),
CL convention (1σ vs 90%). Output: the COMPARABLE subset + a normalization map.
Blocks/quantities with no comparable counterpart are INCOMPARABLE, not tension.

## Phase 3 — DIFF
Per comparable quantity: ours vs theirs (convention-normalized). Classify
AGREE / TENSION / INCOMPARABLE, with numbers. Verdict-level too (their headline
conclusion vs our gated census for the overlapping blocks). If the literature
disagrees with itself, diff against EACH camp separately (see L2).

## Phase 4 — RECONCILE (the scientific core: one change at a time)
For each TENSION, hypothesize the responsible analysis-choice difference, then
TEST it by re-running our fit with THEIR choice adopted — one change per run:
coarser/finer bins; their time intervals verbatim; their energy band; their
detector set; their model prescription (e.g. fixed-smoothness 2SBPL); their
statistic. Record: did ours move toward theirs? By how much? Which single change
closes the gap? Diagnostics that have proven decisive: per-plugin likelihood
decomposition (whose data drive a component), per-bin LAT photon counts,
parameter-rail inspection. If no admissible choice closes the gap → genuine
disagreement: state which result is better-supported and why.

## Phase 5 — VERDICT + DOMAIN
One of: EXPLAINED(choice X) / GENUINE-DISAGREEMENT(evidence) / UNRESOLVED.
State the domain: where does our result hold, where does theirs, what data would
discriminate. UNRESOLVED is an honest, reportable outcome.

## Phase 6 — DISTILL into lessons
Append to §Distilled lessons (dedupe against existing entries — GCN-helper style):
each lesson = a reusable RULE with its trigger condition and its verification hook
("when X, check Y before claiming Z"). Lessons that harden into code (a gate, a
multistart, a floor) get implemented + tested + committed, and the lesson cites
the commit.

**Every lesson NAMES ITS ATTRIBUTION (Vikas, 2026-07-31 — the pivot of the loop).**
The order is strict: analyse blind → diff vs published → *if mismatch, why* →
**attribute** → write the skill. A difference is one of exactly three things, and
which one it is IS the lesson:
- **WE were wrong** → a bug/method error in our pipeline → fix code/method + test +
  cite the commit. (e.g. handbook spectral-lag SIGN inverted vs Ukwatta — a tool
  bug; the SinglePulse_Temporal flip is the interim fix, the source fix is pending.)
- **THEY were wrong** (or their result is an artifact of a forced choice) → document
  WHY our result is better-supported, with the discriminating test. (e.g. Meng+2019's
  "no empirical model fits 4.3–6.3 s" dissolves under a FREE fit — their fixed-cutoff
  PL is the artifact; our all-models diagnostic refutes it.)
- **NEITHER — a frame difference** → a normalization/convention rule, not a fix.
  (e.g. the three integrated-α anchors for 081222 span 2–3σ among themselves because
  integrated α is band-dependent near the death line → use TIME-RESOLVED α for the
  synchrotron verdict; and our T90 < published because the single-pulse source window
  truncates the tail → a window-definition rule.)
Never skip the attribution to "we agree/disagree" — an un-attributed diff teaches
nothing and can't harden into code.

## Quality checklist
- [ ] P0 frozen before any paper was opened (provenance stamped)
- [ ] every literature number quotes the actual paper (not the card, not memory)
- [ ] episode/interval alignment explicit; INCOMPARABLE separated from TENSION
- [ ] every TENSION has a tested (not narrated) explanation, one change at a time
- [ ] conventions normalized (Ep definition, CL, statistic) before any diff
- [ ] lessons appended + deduped; code-hardened lessons cite their commit

## Common pitfalls
- Comparing against the wrong episode (the trigger's pulse ≠ the paper's pulse).
- Treating the literature-card summaries as verified sources (they are candidates).
- Scoring agreement instead of explaining difference (agreement can be recall;
  a tested explanation cannot).
- Multi-change re-fits (explains nothing — one choice per run).
- Trusting a decisive-looking AIC in an under-populated bin (see L4/L5).

## Hand-off
Feeds: the check-library / verification scaffold (each lesson's hook becomes a
promotable check) and the agentic paper's methods. This file IS the general
spectral-fitting skill — general fitting guidance and new lessons both land here
(§Distilled lessons), not in a separate document.

---

# §The DISCOVERY LOOP — how the fitting agent operates
*(Vikas 2026-07-29: "every rule must be checked, and once things don't pass, a
new thing is either hypothesized because the oldies didn't work, or hypothesized
anyway — the philosophy of science discoveries." This is the
hypothetico-deductive loop; the §Distilled lessons below are its CHECKS.)*

**0. FIT** the full menu in every bin (multistarts on; nothing pre-excluded).

**1. CHECK EVERYTHING — every lesson is a gate, and every gate must actually RUN**
(a skipped check is a fake pass):
seeds not railed (L8) · no shared-bound railing / BOUND_CAPPED (L9) · bin
adequacy (L6) · winner not a railed artifact (L5) · cross-band components
confirmed per-plugin (L4) · high-E claims have per-bin high-E statistics (L3) ·
residual RUNS read per detector (L11) · νFν panel rendered and eyeballed (L10) ·
class-aware selection only (L12) · evolution via burst admission (L13) · frames
aligned before any literature diff (L1, L2, L7).

**2. ALL PASS → report** — winner/class verdict + parameters + domain of
validity + caveats + admitted-component tracks. Stop honestly.

**3. A CHECK FAILS → the failure NAMES the next hypothesis** (this is the
engine of discovery — diagnosis is generation):
- residual monotonic run → hypothesize a BREAK at the run's onset;
- residual mode (up-down/down-up) → hypothesize a PEAKED component there
  (BB if on the shoulder; GAUSSIAN LINE if localized — the 221009A case);
- terminal negative run → hypothesize a CUTOFF beyond that energy;
- terminal positive run → hypothesize an EXTRA hard PL;
- BOUND_CAPPED → the machinery was wrong, not the data: widen bounds, refit;
- railed / impossible-nested fit → reseed (our fit was wrong, not the model);
- suspicious joint minimum → per-plugin decomposition to find WHOSE data
  demand the feature, then act on that term's answer.

**4. TEST the hypothesis in count space** — chain gate vs its parents,
ΔAIC≥10, validity, and the L1-checks again. The panel/residuals only propose;
the likelihood disposes. Never adopt from the picture.

**5. ITERATE 1–4** until a model passes, or the candidates are exhausted.

**6. EXHAUSTED → declare it, loudly and specifically:** `OUT_OF_MENU` /
`MODEL_INADEQUATE` / `UNDERIDENTIFIED` / `BOUND_CAPPED` are RESULTS, not
failures — the menu being wrong is exactly how new physics announces itself.
Hypothesize BEYOND the menu (a new component shape justified by the residual
grammar), test it the same way; if it passes, that is a discovery — record it
as a menu-extension candidate and a new lesson.

**7. EXPLORATION CLAUSE** — bold conjectures are allowed even when everything
passes (e.g. a line scan on a bright burst with clean residuals); exploration
is legitimate science, but its findings pass the SAME gates as everything else.

**Every cycle appends what was learned.** If the lesson generalizes, it becomes
a new Lxx below — the loop is how this file grows itself.

---

# §METHODS BOX — the fit statistic is threeML's, not ours (B1)
*(verified 2026-07-30 against installed threeML 2.5.0 source: a 7-agent
source-read + 3-lens adversarial workflow; all three verdicts = PARTIALLY_TRUE —
the CONCLUSION is right, the folk MECHANISM is wrong. Vikas's claim: "threeML
takes care of the likelihood by itself — it probes the nature of the data and
background and takes the statistic accordingly.")*

**What is TRUE (do not re-implement this):** we never choose or pass a fit
statistic. At plugin construction `SpectrumLike.__init__` calls
`_probe_noise_models()` (SpectrumLike.py:144), reads the `is_poisson` flag on the
observed and background spectra (lines 379/387/421) + the python TYPE of any
`background=` plugin, maps to (`observation_noise_model`,`background_noise_model`),
and FREEZES the evaluator once: `_likelihood_evaluator =
statistic_lookup[obs][bkg](self)` (lines 293–295). `get_log_like` (line 1858) is
then a pure cached call — no re-checking. For our GBM path this lands
deterministically on `statistic_lookup['poisson']['gaussian']` =
`PoissonObservedGaussianBackgroundStatistic` → `poisson_observed_gaussian_
background` = **PGSTAT** (Poisson source + profiled Gaussian background;
spectrum_likelihood.py:289). Correct, automatic, no χ².

**The MECHANISM nuance (why "probes the nature" overstates it):** despite the
method name `_probe_noise_models`, threeML does NOT measure the physical count
distribution. It reads a data-format FLAG (`is_poisson`) that was stamped
UPSTREAM: `BinnedSpectrumWithDispersion.from_time_series` sets `is_poisson=True`
by default and flips it to False **only** when `use_poly=True` (binned_spectrum.py
~773–776) — i.e. the polynomial background is what makes the background "Gaussian".
For externally-loaded PHA, `is_poisson` comes from the OGIP **POISSERR** header.
So: the statistic is fixed by DATA CONSTRUCTION, then dict-dispatched — not by a
runtime physical probe. (Both the claim and my first hedge were half-right: it IS
automatic and there IS a "probe" method — Vikas; but it probes a flag, not the
physics — the nuance.)

**Therefore OUR responsibility — the actual skill (guard the flags 3ML trusts):**
1. **Never pass a statistic / never touch the noise-model setters**
   (`observation_noise_model` / `background_noise_model`, SpectrumLike.py:~1792) —
   they silently rebuild the evaluator and could swap PGSTAT → χ²/Cash. scripts/10
   and lat_pipeline must not set them.
2. **Keep the background on the polynomial/Gaussian path** (`use_poly=True` →
   `is_poisson=False` → Gaussian → PGSTAT). A raw *measured* off-source background
   would instead give the Poisson+Poisson profile stat — a different (also valid)
   statistic. This is a USER CHOICE disguised as a default; know which one we're on.
3. **Source must stay `is_poisson=True`** (never coerce GBM counts to carry errors).
4. **Externally-loaded PHA: verify POISSERR** — a missing keyword silently drops to
   the non-Poisson/χ² branch.
5. **FermiLATLike is OUTSIDE this machinery** — it carries its own likelihood, so a
   joint GBM+LAT fit SUMS two different (each correct) statistics; verify the LAT
   plugin's stat separately, never assume the SpectrumLike probe covers it.
6. **Verify per-plugin, per burst**: log the chosen `observation_noise_model` /
   `background_noise_model` (or ERROR_METHOD-style stamp) so a silent wrong-branch
   is caught. (Cheap: read the attributes after construction.)

Bottom line: B1 was mis-scoped in skills_from_Yu2019 as "implement statistic
selection." It is **"understand + verify + don't break threeML's auto-selection"** —
a lighter, correct skill. The paper's methods §can state: *"the fit statistic
(PGSTAT: Poisson source with profiled Gaussian background) is selected by threeML
from the data representation; we verified the polynomial-background path yields it
for every plugin."*

---

# §Distilled lessons (cumulative, deduped)

### L1 — Episode identity before any comparison  *(source: bn160625945, 2026-07-22)*
A trigger is not an episode. bn160625945 is the PRECURSOR trigger of GRB 160625B;
the famous 2SBPL/thermal results concern the main episode (~185–220 s, re-trigger
bn160625952). **Rule:** map the paper's analysed intervals onto our blocks before
any diff; a mismatch makes the comparison INCOMPARABLE, not a tension.

### L2 — "The literature" can disagree with itself; diff per camp
On 160625B: Ravasio+18 (2SBPL synchrotron, BB disfavored) vs Lü+17/Wang+17/Zhang+18
(thermal/photospheric) vs Wang+17 (tens-of-MeV cutoff). **Rule:** never score
"consistency with the literature" as one number; reconcile against each camp,
per block, and report which camp our blind result lands in and why.

### L3 — High-energy components need per-bin high-energy statistics
Our LLE-significance-only merge shredded 160625B's peak into 0.12–0.5 s bins with
4–20 LAT photons — enough to detect flux, never enough to locate a cutoff, so the
joint fit railed EC to a bound. **Rule:** before claiming a high-energy component's
absence, check the per-bin LAT photon count and max photon energy; the coarse grid
must be driven by the statistics of the band that constrains the component.

### L4 — The multiplicative cutoff is continuum-degenerate below the GBM/LLE band
A free joint fit drove xc to the low bound (≈39–50 MeV) with a hardened continuum —
"winning" by ΔAIC hundreds while predicting ~zero flux where LAT photons exist.
The LAT term ALONE preferred xc ≈ 200–400 MeV (TS≈90). **Rule:** for any
cross-band component, run the per-plugin likelihood decomposition (fix continuum,
scan the component parameter, read each plugin's logL separately) before believing
the joint minimum. Fix applied: xc multistart across the band + 10 MeV floor
(scripts/10, 2026-07-22–23); physical validity vs max-LAT-photon energy pending.

### L5 — A railed fit can BEAT its parent and dodge the rescue machinery
The railed-cutoff minimum beat the no-cutoff parent, so the nested-parent
multistart (which only fires when the child is WORSE) never re-explored it — and
the validity gate then discarded a real preference instead of relocating it.
**Rule:** models with a known degenerate rail need an UNCONDITIONAL multistart
(keep-best), not only the worse-than-parent trigger. (Implemented for the cutoffs.)

### L6 — Bin adequacy gates the census
A 0.12 s bin with total N2LL≈6 crowned a 5-parameter model "decisive" (ΔAIC 31) —
pure overfitting; model AICs spread by ~280 on a near-empty bin. **Rule:** a
decisive winner requires a minimally-populated bin; add a bin-adequacy floor
(counts / N2LL scale) to the census before quoting any per-block verdict.

### L6b — Significance is the JOINT-fit quantity, a QUALITY FLAG not a hard cut; floor S≥10 (single-det) ≈ Yu's combined S≥20  *(Vikas, 2026-07-30, from Yu+2019)*
Two facts settled against Yu+2019 + installed threeML: (1) Yu compute S over the
COMBINED joint fit (all fitted detectors, Vianello 2018), blocks on the single
brightest; our 27b `bin_significance` computes it on the SINGLE brightest NaI only
→ our S is understated. For bn081125496 we got 3 bins at S≥20 vs Yu's 6 — purely
single-vs-combined. (2) Scaling: `S_combined ≈ √M · S_single` for M comparable
detectors (validated: bn081125496 scaled 3→5 vs Yu's 6). **Doctrine (adopted):**
- **Significance = the joint-fit significance** over all fitted detectors (what
  actually constrains the parameters), NOT one detector. Single-detector S is not
  literature-comparable and understates constraining power.
- **Floor = S≥10 (single-detector), a round stand-in for the combined S≥20 bar**
  (√M≈2–4 → 20/√M≈10). On our current merged-to-5 blocks: 97/106 bursts have ≥5
  bins at S≥10 (vs 70 at the mis-measured single-det S≥20); 0 bursts empty.
- **It is a QUALITY FLAG, not a hard exclusion.** FIT EVERY bin, report every
  parameter; then flag the S≥10 subset and check whether parameters are
  constrained. Report stats both ways (all bins / S≥10), exactly as Yu reported
  with-and-without the S≥20 constraint.
- **Tail-merge, don't discard.** Toward the fading tail where S drops, MERGE bins
  to keep them above ~5 and reach >10 (near-background bins are already
  background-subtracted → inflated, unreliable uncertainties). Merge floor stays
  ~5; target >10. (This is the in-pipeline miniature of Project #36 — does merging
  preserve Ep(t) while tightening constraints.)
- **Genuinely faint bursts** (091209001, 210812699, 250814432, 120420858) stay
  marginal even merged — that is honest domain-of-validity, flag it, don't force it.
**Pending code:** compute per-bin joint-fit S over approved detectors (rigorous,
replaces the single-det column); optionally raise the tail-merge target toward 10.

### L7 — Paper prescriptions: check, but they're often NOT the cause  *(resolved 2026-07-24, bn160625945)*
Hypothesis was that Ravasio's FIXED smoothness (n1=5.38, n2=2.69) was needed for our
two-break to converge. Test (blk11, 186–208 s, inside their window): a plain
engine-default DSBPL with a SENSIBLE SEED already gives a VALID two-break beating
SBPLfree by ΔAIC=24, xp≈534 keV ≈ Ravasio E_peak 673 keV — Ravasio's smoothness was
NOT required. **Rule:** do test the paper's prescription, but first rule out the more
common cause (L8, seed railing) — a "we can't reproduce their model" is usually our
fit, not their prescription. (blk15 is past their 207.91 s cutoff → INCOMPARABLE, not
a tension; single-break is correct there.)

### L8 — Degenerate-rail models need a DEFAULT-SEED restart, not only parent/T_INT seeds  *(source: bn160625945 blk11, 2026-07-24)*
The production DSBPL railed (xp=5000/K=9999 bounds) from a bad T_INT-derived seed and
was gated INVALID, hiding a real two-break; the DSBPL multistart only re-seeds from
T_INT + the converged SBPL, so it never escaped. A single plain-default seed
(xp=DEFAULT_PARAMS['Ep'], ordered xb<xp) dropped straight into the physical basin
(ΔAIC=+24, valid). **Rule:** any model with a known degenerate rail (DSBPL/DSBPLF,
the cutoffs) must include a plain-default-seed restart AND ordered physical seeds in
its keep-best multistart — not only parent-derived seeds. **Consequence:** the current
two-break census is a LOWER LIMIT until this lands (echoes the standing "two-break =
lower limit" caveat). Fix: extend the DSBPL/nested multistart seed grid in scripts/10
(pending; one-line change + a regression bin).

### L9 — Parameter bounds are physics decisions; simultaneous railing = BOUND_CAPPED, not INCONCLUSIVE  *(source: bn110721200 blk0, 2026-07-24)*
Our Ep/EBREAK/XP caps (5000 keV) sat BELOW the literature-record peak of 110721A
(Axelsson+12: 15±2 MeV first bin; Yu+16 catalog: 7409±597 keV). In blk0 every peaked
model railed at exactly 5000 keV, the validity gate removed them all, and the CPL
family "won" by survival — a false INCONCLUSIVE that mischaracterized the spectrum.
Widening the cap to 50 MeV un-railed all three into VALID fits at Ep≈8.5–12.6 MeV
(Band ΔAIC −37), reconciling with the literature; the control block (peak ≪ cap) was
bit-identical, so generous bounds cost nothing. **Rule:** when SEVERAL models rail at
the SAME shared bound in the same bin, diagnose BOUND_CAPPED: widen and refit — never
let the validity gate silently discard them and promote the next-surviving family
(that is the "gate removes an underidentified fit and silently promotes the next
model" failure mode the architecture review warned about). Tight bounds are implicit
priors; prefer physically generous bounds + railing diagnostics. Pairs with L8:
seeds and bounds are the two ways OUR machinery (not the data) manufactures a wrong
verdict. **Independently confirmed 2026-07-26:** Khushboo, on her own notebook-
verification arm, flagged the same railed bins and — reading Axelsson 2012 herself —
asked for the same bound-widening before seeing our work (two-arm convergence;
fix implemented + verified in the 2026-07-26 engine bundle, blk0 → Ep=8.2 MeV valid).

### L10 — The ratio-unfolded νFν panel is a mandatory eye-diagnostic (hypothesis-GENERATION, never the test)  *(Vikas's addition, 2026-07-24)*
3ML deliberately ships no unfolded-data plotting (model-dependence purism); we built
our own: νFν_data(E) = νFν_model(E) × source_rate/expected_model_rate per channel
group (S/N≥3), per detector, model curve + count-space σ-residual strip, caveat
stamped on the figure. **Unfold under a SIMPLE model** (Band or best single
component) so missing structure stands off the curve instead of being absorbed.
What the eye catches that tables/residuals do not:
- **rollover** of the highest-band points below the curve → cutoff (Wang+17's
  160625B panels; our own 160625B demo shows the LLE rollover at a glance);
- **shoulder/excess** above the peak (BGO 2–4 MeV riding high) → second component /
  saddle / high-energy break;
- **weave** around ~100 keV → low-energy break (Ravasio 2SBPL);
- **localized narrow cluster** off the curve at one energy → LINE candidate —
  cf. Ravasio et al. 2024 (Science): ~10 MeV emission line in GRB 221009A (BGO band,
  1–2 MeV FWHM, centroid 12→6 MeV, blueshifted annihilation interpretation;
  web-verified 2026-07-24). Invisible in N(E), ambiguous in residuals, recognizable
  in νFν.
**Rules:** (1) render the νFν panel for every reconciliation block (protocol P3 —
diff by eye as well as by numbers); (2) a localized cluster triggers a count-space
Gaussian-line test — our 24-model menu has NO line component, so a 221009A-style
feature is an OUT-OF-MENU shape the census would otherwise misfit or miss; (3) the
panel never decides — any structure it suggests is then tested in count space.
Plotter: scratchpad nufnu_plotter.py → to be formalized as scripts/41.

### L11 — Residual GRAMMAR: the correlation structure names the missing component  *(taught by Vikas, 2026-07-24)*
Residuals of an adequate model scatter up/down around 0, uncorrelated. STRUCTURED
runs are not noise — their SHAPE says what is missing and their LOCATION says where:
- **monotonic trend** over an energy range → the slope is wrong on one side →
  a BREAK belongs at the onset of the drift;
- **a mode** (up-then-down / down-then-up) → a PEAKED component is missing there —
  in νFν a curved hump (CPL-like) or a Gaussian LINE;
- **terminal one-directional NEGATIVE run** → the model OVERPREDICTS at the end →
  CUTOFF/rollover beyond that energy;
- **terminal POSITIVE run** → an extra hard component rising above (e.g. +PL).
Worked retrospective: 160625B's no-cutoff fits had the LLE/LAT-end residuals
trending uniformly negative — the cutoff's signature in plain sight; reading that
run locates the cutoff in minutes (the per-plugin decomposition then PROVES it —
pointer first, proof second). **Rules:** (1) after every fit, read the residuals
for RUNS per detector (not just amplitudes/χ²); (2) mechanize: a sign-runs/CUSUM
scan over energy-ordered residuals per detector emitting suggestions
{BREAK@E | PEAKED@E | CUTOFF beyond E | EXTRA-PL above E} — turns the model menu
from brute-force into GUIDED search (the agent knows which model to try next and
why); candidate check-library promotion + a scripts/10 post-fit diagnostic;
(3) grammar suggestions are hypotheses — every one is then tested in count space
(chain gate + ΔAIC as always).

### L12 — Shape-similar models compete as ONE class; a win is a SHAPE verdict  *(doctrine, Vikas 2026-07-18/29)*
Band+BB, CPL+BB, SBPL+BB, 2SBPL, 2SBPLfree all add EXTRA CURVATURE ON THE
LOW-ENERGY SHOULDER of a one-peak continuum — over the GBM band their νFν shapes
are near-identical (physics: E_break and ~3.9·kT are the same shoulder; Burgess's
electron γ_min cutoff = Ravasio's photon E_break in different clothes). An AIC gap
BETWEEN them is structurally impossible, so they are declared one degeneracy class
(`extra_lowE_curvature` in scripts/model_registry.py) and the census reports THREE
tiers: exact winner (strict top-two) / CLASS winner ("low-energy-shoulder
structure detected — flavor degenerate", with the flavor count) / family.
**Rules:** (1) never report Band+BB "beating" 2SBPL (or vice versa) from GBM data
alone — that is an intra-class non-statement; (2) the class BREAKS only with data
outside the GBM band (LLE/LAT above — where our v3 fits genuinely split it;
XRT/optical below); (3) the high-E menu (X+PL / X+CPL / ×Cut) is deliberately NOT
merged — above the peak the shapes genuinely differ and LLE/LAT resolve them.

### L13 — Burst-level component ADMISSION for evolution studies (the Burgess rule)  *(adopted by Vikas 2026-07-29; Burgess+2014 §3.4)*
Burgess admitted the blackbody at the BURST level — >=1 bin improving C-stat by
>=10 — then fit it in EVERY bin of that burst (no per-bin significance cut),
which is what makes kT(t) tracks and a 1%-flux BB measurable, and avoids per-bin
re-selection. Adopted for us: **a composite component is ADMITTED for a burst
when >= 1 bin has it as a chain-gated survivor at ΔAIC>=10 (valid + beats every
nested parent); in admitted bursts the component is tracked in ALL bins, each
bin flagged constrained/unconstrained. Evolution and correlation analyses
(kT(t), Ep–kT, EC(t)) use admitted-burst tracks; the strict per-bin census is
unchanged.** Why: per-bin significance selection conditions on detectability,
whose window slides with Ep — it can imprint spurious parameter correlations
from uncorrelated physics (test: injection-recovery with uncorrelated (Ep,kT)).
Implementation: `model_registry.burst_admission()` + `component_track()`
(2026-07-29). Ep–kT comparisons must report BOTH constructions: admitted-track
(Burgess-faithful) and BB-significant-only (flagged as detection-conditioned).

### L15 — A RAILED shape parameter does NOT invalidate a DERIVED physical quantity  *(Vikas, 2026-08-04, bn130310840 blk2)*
Our validity gate marks a fit `VALID=False` when a shape parameter rails. Correct for the FIT —
but do not therefore discard the MEASUREMENT. Test whether the derived quantity is stable.

Worked case (blk2 [4.107,4.131] s): Band railed at our `beta.bounds=(-5.0,-1.6)` floor, so
`BAND_VALID=False`, and both I and the Codex audit retracted "Ep = 12.4 MeV". **Both retractions
were wrong.** Vikas: *"XSPEC used to allow beta go to -10."* Re-fitting with the floor widened to
-10 gives:
| beta floor | fitted beta | Ep | AIC |
|---|---|---|---|
| -5 (ours) | -5.000 railed | 12278 keV | -2052.03 |
| -10 (XSPEC-like) | -9.999 railed | 12301 keV | -2052.11 |
ΔAIC = -0.08, Ep moves 0.2%. So (a) it is NOT a bound artifact — the likelihood wants beta → -inf,
which physically means *no measurable high-energy power-law tail* (Band degenerates to CPL); and
(b) **the peak energy is bound-independent**. Confirmed by the model comparison: **CPL, which is
`VALID=True`, gives 12499 keV — agreeing with the railed Band to 0.3%.**
**RULE:** when the winner is railed, (1) check the derived quantity across the whole menu, (2) quote
it from a VALID model, (3) report the spread when composites shift it. Here the honest statement is
*"peak = 12.4 MeV for a single-component continuum (valid CPL); 7.7–9.7 MeV when an additive
component is included"* — a range that BRACKETS Qin+2021's 8.5–11 MeV instead of contradicting it.
Also record: our `beta` floor of -5 is OUR choice and is tighter than XSPEC's grbm (~-10); widening
does not help here, but the floor must be stated in the methods.

### L16 — ΔAIC is an EVIDENCE RATIO; grade it, don't threshold it — and our two gates were inconsistent  *(Vikas, 2026-08-04)*
ΔAIC means `exp(ΔAIC/2)` : 1 odds. A bare "≥10 or nothing" throws away real evidence.
| ΔAIC | evidence ratio | grade | ≈σ (2 extra par) |
|---|---|---|---|
| 2 | 2.7:1 | indistinguishable | 2.0 |
| 4 | 7.4:1 | positive | 2.4 |
| **6** | **20:1** | **STRONG** | 2.7 |
| 8 | 55:1 | very strong | 3.0 |
| 10 | 148:1 | decisive | 3.3 |
| 26 | 4.4e5:1 | overwhelming | 5.1 |
(Consistent with the Burnham & Anderson rule of thumb: Δ≤2 substantial support, 4–7 considerably
less, >10 essentially none. ⚠ verify the exact wording against the source before a draft.)
**ADOPTED:** ΔAIC ≥ 6 = STRONG, ≥ 10 = DECISIVE; **always report the evidence ratio**, never a bare
verdict. This reclassifies bn130310840 as blk2 DECISIVE (26.0, 4.4e5:1), blk4 VERY STRONG (9.0,
91:1), blk3 STRONG (8.0, 54:1) — not "one success, two failures".

**⚠ CONFLICT-1 (NR-27 first instance, found 2026-08-30 on #21 bn110920546): the line above
never named the REFERENCE model.** The PREFERENCE section below measured vs the runner-up;
ReportSpec R3's tie rule implied runner-up; the shipped #21 report and REVIEW_INDEX_106
("8 DECISIVE") measured vs the best simple model — the same table read "8 DECISIVE" or
"3 TRACKED / 5 ties" depending on the reader. **RESOLVED by PI ruling 3 (2026-08-30,
gate 1 of the #21 walkthrough), verbatim:** "ΔAIC reference: BOTH constructs stay, with
mandatory labels — "DECISIVE" = chain-gate vs best simpler ancestor (structure claims,
ΔAIC≥10); "TRACKED" = vs runner-up (preference, ΔAIC>6 in 1–2 bins). Never print either
word without its reference." So the grades in this table are the CHAIN-GATE construct:
ΔAIC of a model vs its best simpler ANCESTOR in the nesting chain. Every printed
"DECISIVE"/"STRONG" names that ancestor.

**⚠ DOCTRINE BUG this exposed:** our `+BB` gate `LRT ≥ 9.2` is p=0.010 (~2.6σ) for 2 extra
parameters ⇒ **equivalent to ΔAIC ≈ 5.2**, while we simultaneously demanded **ΔAIC ≥ 10**
(⇒ LRT = 14). The two gates disagree by ~5 AIC, so a component can pass one and fail the other on
the same data. Make them consistent — ΔAIC ≥ 6 ↔ LRT ≈ 10 is the natural pairing.

**⚠ CALIBRATION CAVEAT (limits BOTH gates):** for an ADDITIVE component the normalization is bounded
at zero, so the LRT is **not** asymptotically chi-square and both LRT and ΔAIC are OPTIMISTIC at the
boundary (Protassov, van Dyk, Connors, Kashyap & Siemiginowska 2002, "Statistics: Handle with Care"
— ⚠ bibcode UNVERIFIED, check before citing). Any "a thermal component is required at Nσ" claim
needs **Monte-Carlo / posterior-predictive calibration**, not the analytic p-value. Until that is
done, all component-significance numbers stay provisional.

### L17 — DETECTION significance is the WRONG gate for INCLUDING a detector in a joint fit  *(Vikas, 2026-08-05, bn120624933)*
**"We are supposed to take the data in any case."** Two different questions were being conflated:
- *Is there signal?* → a DETECTION question, answered by significance.
- *Should this detector be in the joint fit?* → a CONSTRAINT question, answered by data quality.

For bn120624933 the LLE band gives **2.60σ with 96 source events**, below a 3σ threshold, so Stage 1
stamped only `n0,n1,n2,b0`. That is the wrong criterion. A 2.6σ band is **not** a null measurement —
it is an upper limit that constrains any high-energy component, and in a joint likelihood it
contributes real information (this is exactly why we fit, rather than count).

**Why it actively BIASES the census (the decisive argument):** if LLE enters the fit only when it
clears a detection threshold, then high-energy components preferentially appear in bursts where LLE
happened to fluctuate UP. That manufactures spurious `+PL` / high-E detections and silently deletes
every burst where LLE says *no*. A shape census that conditions inclusion on the outcome is not a census.

**RULE — the inclusion gate is DATA QUALITY, never significance:**
1. a valid response over the source window (the **D1 off-axis check**, `DataInventory.md`);
2. a **reviewed and stamped** background for THAT detector — never silently inherited;
3. correct event/pointing/response triplet versions.
If those pass, the detector goes in the fit whatever its significance, and a non-detection is
REPORTED as a constraint, not dropped.

**The real defect at bn120624933 was the background, not the inclusion.** Stage 3 auto-added LLE and
copied `n0`'s windows with no review. LLE particle backgrounds differ from NaI (see `scripts/10`
find_lle_files: an approved `lle` row is authoritative precisely for this reason). So the fix is
**review + stamp the LLE background, then include** — NOT exclude.
⚠ Corollary: my earlier justification ("include LLE because the LAT detection is 10σ") was WRONG —
that 10σ is >100 MeV LAT, a different band from 30–100 MeV LLE. Inclusion needs no such excuse.

**EXTENSION (Vikas, same day): "we have to take data everywhere where it is possible for both LLE
AND LAT."** The rule is not LLE-specific — it applies to every band with usable data.
- **Binning:** LLE/LAT never need to DRIVE the bins. *"If we didn't make bins from LLE, then we can
  just analyze on the bins we have from GBM."* The joint fit uses the GBM-fine blocks and each
  higher-energy plugin contributes whatever counts fall in them. (The coarse 27c LLE grid is a
  SEPARATE mode, for LLE-driven binning — not for joint fits.) This is already what
  `scripts/10` does: `Canonical bins from det <NaI> (gbm_fine)`.
- **⚠ SELF-AUDIT, 2026-08-05:** every walkthrough fit so far ran `--include-bgo --models highe` with
  **NO `--include-lat`**. bursts #3/#4/#5/130427324/130518580 ALL have FT1+FT2 in `data/<trig>/LAT/`,
  and bursts #3 and #5 have published LAT detections — yet the fits stopped at 100 MeV
  (`fit_dets: n*,b*,lle`). The >100 MeV data that would break burst #3's composite degeneracy was
  sitting unused on disk. **Same error as the LLE one, one band higher.**
- **RULE:** for every burst, attempt EVERY band with data + a valid response — GBM NaI/BGO, LLE
  (30–100 MeV), LAT (>100 MeV, `--include-lat`). Drop a band only on a DATA-QUALITY failure (D1
  response geometry, unreviewed background, missing triplet), never on significance, and RECORD
  which bands were attempted and why any was excluded.

**PUBLISHED EXAMPLE — the error is not hypothetical (added 2026-08-07).**
**Duan & Wang 2020, ApJ 890, 90 (`2020ApJ...890...90D`), "A Spectral Analysis of Fermi-LLE
Gamma-Ray Bursts"** — 36 GRBs detected by GBM **and LAT and LLE**. Their §2, verbatim:
> *"we perform the detailed time-resolved spectral analysis by using the TTE event data files of
> two NaI detectors and the corresponding BGO detector(s) on Fermi/GBM, **but the use of LAT and
> LLE data was abandoned because of their lower impact for peak energy Ep and low energy spectral
> index α**."*
The sample is **selected by LLE brightness** — i.e. exactly the bursts where LLE carries the most
signal — and then the LLE and LAT data are discarded. The title describes an LLE *sample*, not an
LLE *analysis*.

Why the stated reason fails, and what it costs:
1. **It is circular.** LLE/LAT have "lower impact for Ep and α" *because Ep and α are low-energy /
   peak parameters*. The high-energy data constrains **β** and any high-E component — which is then
   not measured. That is a statement about the chosen parameter list, not about the data.
2. **It biases the parameter it claims not to affect.** **Ravasio, Ghirlanda & Ghisellini 2024,
   A&A 685, A166 (`2024A&A...685A.166R`)**, on 22 bright GRBs with simultaneous GBM+LAT:
   *"with the inclusion of the LAT data, the spectral index β is **softer** than what is typically
   inferred from the analysis of Fermi/GBM data alone."* In a Band fit β and Ep are covariant, so a
   systematically hard β pulls Ep. The claim "low impact on Ep" is testable and was not tested.
3. **They were careful about a different artifact.** Their own headline caution is that some α–F and
   Ep–α correlations are *"non-physical selection effects"* shown by simulation — genuinely good
   practice — while a systematic β bias was introduced by construction. Guarding one artifact class
   does not license ignoring another.

**What WOULD have been defensible:** *"we exclude LLE because its response validity varies across
the sample (single-matrix DRMs, geometry-dependent — see D1) and we require uniform treatment."*
That is a DATA-QUALITY reason and it passes L17. "Lower impact on our parameters" does not.

⇒ **This is L17 made in a refereed paper by people doing otherwise careful work.** Treat the
inclusion gate as a field-wide failure mode, not local bookkeeping — and when we exclude a band,
state the data-quality reason explicitly so the exclusion is auditable.
⚠ Applies to US too: bursts #3 and #5 were fitted GBM+LLE with **LAT unused on disk**, so their β
values carry exactly the bias Ravasio measured. Re-fit with `--include-lat` before quoting β.


### L18 — EVERY model family needs an unconditional multistart — a bound-widening fix must be re-validated on the FAINTEST blocks  *(bn110721200 blk9, 2026-08-08)*
The L9 fix (widen the 5 MeV Ep cap) correctly un-railed blk0's 19 MeV peak — and silently destroyed
blk9. The cap had been *incidentally anchoring* the faint late blocks; with it gone, blk9 (sig 7.8,
seeded by the chain from a bright block) fell into a soft local minimum: **α = +0.82, Ep = 42 keV**
against α ∈ [−1.26, −0.93], Ep 373–424 keV across **9 archival runs**. The gate auto-invalidated it
(Ep near the 30 keV bound), so the winner stayed sane (CPL) — but the collapsed α sat in the table
and got quoted in the Step-9 narrative.

Root cause: **the simple models were the ONLY family without a multistart.** BB, DSBPL, cutoff and
every nested composite had restarts; Band/CPL/SBPL/SBPLfree fit once from the chained seed with
nothing to rescue them.

**RULE:** (a) every family gets an unconditional restart from pure defaults + canonical seeds,
keep-best validity-preferring (`SIMPLE_RESTART_SEEDS` in `scripts/10`, runs BEFORE the composite
multistarts so children seed from corrected parents); (b) any fix that moves or removes a bound is
re-validated on the LOWEST-significance blocks of the burst that motivated it, not just the block
that motivated it; (c) a collapsed-but-invalidated fit is still a defect — its parameters pollute
narratives and tracks.
**TEST:** `tests/test_lessons.py::test_L18_*` — no OK Band fit with α > 0 in guarded tables; demo
blk9 must recover the archival minimum. *A lesson is not learned until it is a claim + a test.*

### L19 — a nested LRT ≤ −0.5 is not a non-detection; NaN it and stamp it  *(demo blk1 + blk0 of demo/b4, 2026-08-08)*
A nested child strictly worse than its parent is impossible at the true optimum (parent + null
component reproduces the parent's likelihood). LRT ≈ 0 is legal — the component pinned to zero.
LRT < −0.5 means either a failed child fit **or** an approximately-nested pair (DSBPL vs SBPL:
fixed-smoothness conventions differ, so exact nesting fails — demo/b4 blk0 gave −1.66/−1.12).
Either way the number is **not χ²-distributed** and reporting it as a clean null is wrong.
**RULE:** `select_best` NaNs any nested LRT < −0.5 and stamps `LRT_INVALID`; downstream logic sees
a missing measurement, never a clean non-detection.
**TEST:** `test_L19_no_impossible_negative_lrt`.

### L20 — restore the model to the best fit BEFORE evaluating derived curves  *(bn130518580 blk8/blk14 + 13/19 blocks, four-channel audit 2026-08-08)*
`jl.get_errors()` (MINOS scans) can leave the live astromodels object DISPLACED from the minimum.
`EPK_CURVE`/`WIDTH_HM` were computed from that displaced curve: blk8 stored 184.8 keV — the BB bump
(3.92 kT = 186.2) at an inflated K_BB — while the composite at the stored best-fit parameters peaks
at **839 keV** (BB bump only 0.65× the Band peak). Systemic: 13/19 blocks of bn130518580, every
walkthrough out-root affected.
**RULE:** call the native `jl.restore_best_fit()` before evaluating anything from the live model.
Derived quantities come from the FIT, not from wherever the error scan parked the parameters.
⚠ **Consequence for #34 (AbovePeakShape):** every walkthrough-era `*_WIDTH_HM`/`*_EPK_CURVE` for
composite models is unreliable until regenerated — including the blk8 "width 0.54→1.61" demo
numbers. The argument survives (width spans stay wide); the specific values do not.
**TEST:** `test_L20_epk_curve_not_displaced` (fails on stale tables by design — that is the test
localizing which products need regeneration).

### L21 — FRAME-ALIGN before you diff: "Ep" in a table may be Ec, and a sign may be flipped  *(bn081224887 reconciliation, 2026-08-08)*
Li 2019 (`2019ApJS..245....7L`) and Yu 2019 (`2019ApJ...886...20Y`) tabulate **Ec — the CPL
e-folding energy — not Epeak**: `Ep = (2+α)·Ec`. Verified on Yu Table 6, where both appear:
α=−0.13, Ec=344.76 → Ep=644.75 = 1.87×344.76. Naively diffing our Ep against their "Ec" column
fakes a factor-1.9 discrepancy. Same burst, same trap in sign: Suzaku-WAM quotes α=+0.83 in
`dN/dE ∝ E^−α` — that is **−0.83** in our convention.
**RULE — the P2 frame-alignment checklist, applied before ANY number is diffed:**
(1) Ep convention (νFν peak vs e-folding vs break energy); (2) index sign convention;
(3) energy band of the quoted fluence/flux; (4) time interval AND its T0 (Konus/WAM T0 ≠ GBM T0);
(5) detector set. A diff without the checklist is not a diff.

### L22 — a published component claim is a claim about the CONTINUUM it was measured against — and citation chains lie  *(bn081224887, Burgess 2014 vs our null, 2026-08-08)*
Burgess+2014 (`2014ApJ...784...17B`) report a "significant" blackbody in 081224 at ΔC-stat>10 —
**measured against a synchrotron-only continuum**, and say so verbatim: *"the Band function has
more freedom in the shape below Ep"*, and the BB was added *"when Band α was much harder than
zero [and] the synchrotron fit was poor"*. 081224's α is harder than −2/3 in 11/15 bins — the BB
repairs synchrotron's rigidity, and vanishes against Band/CPL. **Our null and their detection are
both correct**; they answer different questions. The apparent contradiction dissolved only when
the continuum was named.
**Chained claims rot:** Li 2019 Table 1 lists "Best Model = Band+BB" for 081224 citing Iyyani
2016 — which fitted synchrotron+BB, never Band+BB, for this burst.
**RULE:** before recording a literature entry as CONTRADICTING ours, (a) name the continuum the
published component was measured against; (b) verify any chained claim at its PRIMARY source.
"X requires a blackbody" with no continuum named is not yet a claim.

### L23 — agreement can be a SHARED BAD MINIMUM; independence counts at the PRIMITIVE  *(bn130310840 slice c + the four-channel experiment, 2026-08-08/09)*
Our kT = 52.0 keV and Qin+2021's kT = 54.6 agree to 5% — and **both are statistically
unnecessary** (our ΔAIC₂ = 1.1, their ΔAIC = −0.8). Agreement from a shared unnecessary minimum
looks exactly like corroboration. The FXT bug catalogue's B-49 (astropy Sun-angle) is the same
disease; the four-channel experiment reproduced it on demand — two channels sharing one broken
ECSV column corroborated a void claim, while the one REAL corroboration (NaI cross-norm offset)
was seen at two genuinely different primitives (pixels vs railed EAC parameters).
**Corollary — verify the adversary too:** the same experiment's adversary claimed the +BB
multistart was non-deterministic; 5 identical runs gave spread 0.000 — its variance was its own
invocations.
**RULE:** before counting agreement as verification, name the deepest primitive the two paths
SHARE (minimiser, table, column, skill file, response model). Agreement above that primitive is
one opinion; agreement below it is evidence. N identical lookers are one look.

### L24 — an EVOLVING component rails in the INTEGRATED fit; a railed T_INT BB with valid resolved kT is a BROKEN fit, not an absence  *(bn130518580, 2026-08-08)*
Resolved blocks 6–16 return VALID kT = 30.7–50.3 keV (cooling, LRT up to 34.7). The T_INT
Band+BB and SBPL+BB **railed at kT = 1.0 keV despite 30/80 keV multistart seeds**, were gated
VALID=False — and "no integrated thermal" was then read as a result. It is an optimiser failure:
one static Planck cannot track a cooling, fading component, and the deep minimum the resolved
blocks find has no counterpart in the integrated likelihood. The converse also happened in the
same burst: integrated DSBPL is decisive (ΔAIC 82) while resolved shows the cooling BB — time
integration both destroys real components and manufactures static ones.
**RULE:** if ANY resolved block has a VALID, significant kT and the T_INT BB rails → the T_INT
fit is broken; report "T_INT: not measurable (railed)", never "no thermal component".
**ENGINE (pending):** second-pass T_INT re-fit seeding kT from the flux-weighted resolved-block
value. **TEST:** `test_L24_tint_bb_rail_vs_resolved` (xfail on b6 until the seeding fix lands).

### L25 — the DSBPL low break and the blackbody are frequently ONE feature; test xb vs 3.92·kT every time  *(bn130518580, 2026-08-08)*
Across 11 blocks of bn130518580, the DSBPL low break tracks the Band+BB blackbody peak:
Pearson r = 0.87, median xb/(3.92 kT) = 1.13. The four-channel panel saw the same thing from the
outside: the winning flavor flips Band+BB → DSBPL between consecutive 0.7-s blocks whose total
νFν curves are visually identical — the LABEL alternates on timescales no emission mechanism can,
because both models are fitting the same low-energy shoulder (the L12 degeneracy class made
visible).
**RULE:** whenever a burst shows both flavors, compute xb/(3.92 kT) block-by-block. If it sits
near 1 with high correlation, report ONE spectral feature whose identity is undetermined — never
a "blackbody" in some blocks and a "second break" in others.

### L27 — the rail test must respect parameter GEOMETRY: linear margins on log-spanning bounds disqualify soft bursts  *(bn090530760, 2026-08-10)*
`_fit_is_physical` flagged a parameter railed when `(v − lo) < 0.001·(hi − lo)`. On log-spanning
bounds — Band Ep (30, 5×10⁴), CPL xc (10, 5×10⁴) — that linear margin is an absolute **~50 keV
dead zone above the LOW bound**: every Ep < 80 keV / xc < 60 keV was auto-invalidated however
well-constrained. Consequence on the first genuinely SOFT burst of the campaign (Ep 36–136 keV):
**blocks 2–5 lost every simple model to false rails**, winners defaulted to BB-composites, one
block went INCONCLUSIVE, and the ΔAIC-vs-simplest margins were incomputable. Uncorrected, the
census would systematically prefer extra components in soft bursts — a selection bias
masquerading as physics. No previous burst felt it (all had Ep ≳ 250 keV): **the defect was
invisible until serial ordering delivered a soft burst.**
**RULE:** bounds spanning > 2 decades (lo > 0) are tested in **log space** — margin = 1% of the
log-span (30 → 32.3 keV; 5×10⁴ → 4.6×10⁴). Only genuinely narrow/linear bounds (indices) keep
the linear rule. ⚠ CORRECTED (Codex audit 2026-08-11): kT's bounds (1, 200) span 200× > 2
decades, so **kT is log-ruled too** — its rail zone is kT < 1.0544 keV (an earlier version of
this text wrongly listed kT with the linear-rule parameters; the code always applied the
hi/lo > 100 test). More generally: any threshold applied to a parameter must live in the
parameter's natural geometry.
**TEST:** `test_L27_rail_margin_respects_log_geometry` (unit-level, imports the gate directly).

### L28 — a feature below ~20 keV is EDGE-CONSTRAINED: stamp it and earn it, never quote it bare  *(the low-kT night class, 2026-08-11; anchors: Tierney+2013 `2013A&A...550A.102T` [local copy = arXiv v1 PREPRINT, not VoR — A&A site blocks fetch], Ravasio+2019 `2019A&A...625A..60R` [VoR on disk]; audit-corrected same day, Codex gpt-5.6-sol)*
A component is constrained by its **in-band νFν turnover** (3.92·kT for a blackbody — an
ANALYTIC result, max of E²·N(E) for a Planck spectrum, x = 3.9207, not a value from either
paper — xb for a low break), not by data at its nominal energy — so kT ≈ 4–6 keV from NaI data
starting at 8 keV is legitimate *in principle* (Tierney's Table 4 publishes Band+BB with
kT = 4.99 +0.53/−0.52 keV for GRB 090323). But the literature brackets the edge from both sides:
- **Ravasio+2019 App. B (the trust boundary):** GBM fits with Ebreak < 20 keV produce
  unphysically hard, ill-constrained α₁ (their 171010: Ebreak = 12.39 ± 0.13 keV,
  α₁ = **+1.16 ± 0.13**), splitting the Ebreak–α₁ plane at ~20 keV with *almost* no overlap
  between the two populations — "strongly suggests an instrumental effect"; their population
  statistics retain only the > 20 keV subset. ⚠ The boundary is an empirical **2SBPL**
  result; transferring it to BB peaks via 3.92·kT is OUR inference (project policy, to be
  calibrated by model-specific simulations).
- **Tierney+2013 (how to earn an edge feature):** full-band C-stat *smears* deviations through
  the model; their extrapolated-fit method fits a Band function above a Low-Energy Threshold
  scanned over **LET ∈ {15, 20, 25, 30, 50, 100} keV**, extrapolates down to 8 keV, and tests
  the **summed residuals below the LET, averaged across detectors**, against ~1000
  response-folded simulations per parameter set. Both excesses AND deficits occur (a component
  between LET and Ep flattens α → deficit). Reading the *coherent residual run* (rather than
  the summed statistic) is OUR project extension of their method, not their procedure.
- **The unresolved two-costume tension (OUR observation, neither paper makes the
  cross-identification):** Ravasio's "instrumental" α₁ ≈ +1.16 at a ~12 keV break is
  numerically the Rayleigh–Jeans photon index (+1) — what one lineage quarantines as artifact
  is what the other would call a photosphere. Tierney's 090424 is fit both as Band+BB
  (kT = 9.20 +0.55/−0.44) and as a double-broken PL (Ebreak1 = 32.74 keV). The identity
  question is OPEN in the literature; we must not close it by labeling.
- **Artifacts come in two classes** (Vikas, 2026-08-11): *detector-level* (blockage, bad
  response — lives in ONE NaI; killed by per-NaI coherence, D5 pointed in reverse) and
  *shared-primitive* (common DRM generator, background family, fit statistic — coherent across
  ALL NaIs, like the Ravasio pathology; killed only by simulations or a different instrument).
  Per-NaI coherence ACQUITS the first class only.

**RULE — any significant component/break with turnover (3.92·kT or xb) below 30 keV:**
1. stamp via `edge_feature_class`: **EDGE_CONSTRAINED** (< 20 keV) / **EDGE_MARGINAL**
   (20–30 keV); stamped values never enter population statistics unstamped — we *report*
   (data-dropping hierarchy), Ravasio-style quarantine is for the stats, not the record;
2. rail check on the paired low index (α₁ > −0.2 = the Fig. B.1 signature);
3. **LET-extrapolation localization** (Tierney): continuum fit above ~30 keV only, extrapolate
   down, coherent residual run 8→LET; simulation-calibrated before any promoted claim;
4. **per-NaI coherence, amplitude-weighted**: the excess in EVERY NaI at the amplitude its own
   DRM predicts; per-detector kT consistency where counts allow; a low-S/N detector's silence
   is NOT incoherence;
5. background-fit sanity specifically in 8–30 keV over the source window;
6. **L25 identity pair**: report BB margin AND DSBPL-low-break margin side by side; if both
   adequate the record says "a low-energy spectral feature at ~E keV" — never "a blackbody";
7. cross-instrument (BAT/XRT overlap) where it exists — the strongest available test of the
   shared-response class (Tierney-style response-folded simulations probe it too, within the
   fidelity of the DRM model).
**RECORD POLICY (standardized per Codex audit 2026-08-11):** stamped values are RETAINED and
reported in burst records (data-dropping hierarchy — we never hide a measurement); they are
EXCLUDED from population statistics and from claim promotion until checks 2–7 pass. Neither
"suppressed everywhere" nor "quoted bare" — stamped-and-quarantined.
Cuts BOTH ways: a census DSBPL with **xb < 20 keV** carries the same stamp — this lesson
protects the two-break count itself, not just the BB class. Mirrored HET version for the
above-peak project lives in the #34 registry entry.
**ENGINE:** `edge_feature_class(kt=, xb=)` in scripts/10 (EDGE_TRUST_KEV = 20 from Ravasio
App. B; EDGE_CLEAR_KEV = 30 is PROJECT POLICY — a heuristic sitting just below the 33–40 keV
K-edge exclusion, to be simulation-calibrated; BB_PEAK_FACTOR = 3.9207 analytic) — pure
classifier; wiring into scorecards/population products is the enforcement point (open engine
item: serialize the class into fit tables).
**TEST:** `test_L28_edge_feature_class` (unit-level; includes the L25 consistency property —
kt and xb = 3.92·kt must classify identically).

### L30 — The energy-range convention is the PI's PUBLISHED convention, cited, not an inherited default  *(Vikas, 2026-08-14: "use that")*
The engine ran 106 bursts with `BGO 300–40000 / LLE 30–100 MeV / K-edge 33–40` — three
low-edge choices carrying NO comment, citation, or date, while the NaI line above them
documented its K-edge lesson properly. Vikas's question ("did we not use the recommended
BGO range?") exposed it: the instrument nominal is 200 keV–40 MeV (Meegan+09), our own
Stage-1 picker LCs showed 250+, and HIS OWN paper — Chand et al. 2020, ApJ 903, 9
(GRB 190114C), p.3 verbatim — used **NaI 8–900 keV, BGO ∼0.2–38 MeV, LLE 20–100 MeV,
K-edge 30–40 keV (33.17 keV feature)**. ADOPTED as the engine convention 2026-08-14
(`scripts/10` constants now cite it; sidecar serializes NAI_EXCLUDE/LLE_RANGES/
RANGES_CONVENTION). Consequences: (1) NEW fits only — every pre-change row carries its
fit-time ranges in the sidecar, and `scripts/41b::_assert_range_convention` REFUSES to
replay a row under mismatched live constants (forensic override env, never shippable);
(2) the frozen full-sample re-run inherits the new convention — walkthrough-era numbers
were provisional by doctrine anyway; (3) prediction to check at the first new-convention
fit: the added BGO 200–300 keV overlap should better constrain the EAC constants — watch
whether bn081125496's EAC_B1 comes off its 1.2 rail. The transferable rule: **every
selection constant in the engine carries a citation or a dated decision — an
undocumented constant is a latent audit finding.**

## PREFERENCE vs BEST-AIC — the tracking rule (PI ruling, 2026-08-26)
best_AIC is the argmin; PREFERENCE is a separate claim. PI, verbatim: "best_AIC
model is one thing, but if it is preferred over others or not is another thing"
and "keep delta AIC more than 6 at least in 1 or 2 bins and then we can track
them". Operational rule: a model enters a burst's TRACKED set when it is the
bin winner with margin ΔAIC > 6 over the runner-up in ≥1 bin (STRONG tier;
≥2 bins = the stricter tier). Everything else is reported as argmin-only or a
tie (NR-3). The census follows TRACKED models, not bin argmins. Tool:
dev/model_preference.py → results/campaign/model_preference.ecsv. WHERE a
preference lives in energy: dev/model_discrimination.py (Basak&Rao-style).

### Amendment — the two ΔAIC constructs and their mandatory labels (PI ruling 3, 2026-08-30, gate 1 of the Lane-A #21 bn110920546 walkthrough)
Verbatim: "ΔAIC reference: BOTH constructs stay, with mandatory labels — "DECISIVE" =
chain-gate vs best simpler ancestor (structure claims, ΔAIC≥10); "TRACKED" = vs runner-up
(preference, ΔAIC>6 in 1–2 bins). Never print either word without its reference. Fix
model_preference.py's validity gate before its output is quoted for THIS burst."

| word | construct | reference model | threshold | claim type |
|---|---|---|---|---|
| **DECISIVE** (and STRONG per L16) | chain-gate | the best SIMPLER ANCESTOR in the nesting chain | ΔAIC ≥ 10 (STRONG ≥ 6) | STRUCTURE — "an extra component is required" |
| **TRACKED** | preference | the RUNNER-UP (whatever it is) | ΔAIC > 6 in 1–2 bins | PREFERENCE — "this model is tracked through the burst" |

Rules that follow: (1) neither word is ever printed without its reference model beside
it (ReportSpec R3); (2) a bin can be DECISIVE and a tie at once — DECISIVE vs the
ancestor, tie vs the runner-up (NR-3) — both are stated, neither replaces the other;
(3) the feature-level margin (decision-sheet item 8) is NOT addressed by the ruling: it
stays a computed-alongside diagnostic, never a census construct; (4) NR-26: the validity
gate was applied to dev/model_preference.py on 2026-08-30 (engine *_VALID + *_STATUS
gate every argmin; name map from scripts/10's spec tables via ast; refuses to write on
any mismatch vs BEST_AIC_MODEL) — per-burst use only, the campaign-wide table is NOT
rerun under the no-sweep preamble ("one burst at a time, repairs included: each burst
fixes its own rows as it's walked, no campaign-wide sweeps."), so
results/campaign/model_preference.ecsv stays SUSPECT for every un-walked burst.

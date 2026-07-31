# Skill: SpectralFitting — learn to fit like the published experts
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

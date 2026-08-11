# Deep Reading Notes — Li & Zhang (2021)

## Paper

**Testing the High-latitude Curvature Effect of Gamma-Ray Bursts with Fermi Data: Evidence of Bulk Acceleration in Prompt Emission**  
Liang Li & Bing Zhang, *The Astrophysical Journal Supplement Series*, 253, 43 (2021).

## Reading classification

```text
CORE / TEMPORAL / CURVATURE / METHOD / JET PHYSICS / WRITING MODEL
```

## Direct relevance

```text
- 106-single-pulse GRB catalog
- pulse-wise spectral-lag project
- detector-response temporal-bias project
- structured-jet high-latitude-emission project
- coupled forward-shock/reverse-shock model
- hybrid/Poynting-flux jet interpretation
- physical interpretation of prompt-pulse decay wings
```

Keep four layers separate:

```text
SOURCE:
    what Li & Zhang actually calculate and claim

CRITIQUE:
    assumptions, ambiguities, limitations, and possible biases

PROJECT ACTION:
    concrete analyses to implement

DISCOVERY:
    new physical or methodological questions
```

---

# 1. One-line scientific takeaway

Li & Zhang isolate bright single-pulse Fermi/GBM bursts, test whether their decay wings satisfy high-latitude-emission predictions, infer characteristic emission-radius scales of roughly \(10^{15}\)–\(10^{16}\) cm under assumed Lorentz factors and redshifts, and interpret decay behavior steeper than the constant-\(\Gamma\) curvature prediction as evidence for bulk acceleration and Poynting-flux-dominated prompt emission.

This is a conditional interpretation. A violation of the simplest closure relation establishes tension with that model; it is not automatically unique proof of magnetic acceleration.

---

# 2. Physical logic of the paper

The argument has two stages.

## Stage A — identify high-latitude emission

After a relativistic emitter ceases radiation abruptly, photons emitted at larger angles relative to the line of sight arrive later because of their longer path and smaller Doppler factor.

For a constant bulk Lorentz factor and a local power-law spectrum, with convention

\[
F_\nu(t)\propto t^{-\hat{\alpha}}\nu^{-\hat{\beta}},
\]

the standard closure relation is

\[
\hat{\alpha}=2+\hat{\beta}.
\]

The authors operationally treat:

```text
alpha approximately 2 + beta:
    constant-Gamma curvature effect

alpha greater than 2 + beta:
    curvature tail from an accelerating emitter

alpha below 2 + beta:
    HLE not yet dominant, continuing emission, deceleration,
    contamination, or failure of the simple assumptions
```

## Stage B — infer physical scale and composition

If an observed interval of duration \(t_{\rm HLE}\) in the source frame is identified as HLE, the paper uses

\[
R_{\rm GRB}
\gtrsim
\Gamma^2 c t_{\rm HLE}
=
3\times 10^{14}\ {\rm cm}\,
\Gamma_2^2
\left(\frac{t_{\rm HLE}}{1\ {\rm s}}\right),
\]

where \(\Gamma_2=\Gamma/100\).

The source-frame duration is:

\[
t_{\rm HLE}
=
\frac{t_{\rm HLE,obs}}{1+z}.
\]

Large radii plus continued acceleration are then interpreted as evidence for dissipation of magnetic energy in a Poynting-flux-dominated region.

---

# 3. Jet-composition framing

## Fireball baseline

The introduction contrasts:

```text
thermally accelerated, matter-dominated fireball
photospheric and internal-shock emission at comparatively small radii
coasting after rapid thermal acceleration
```

with:

```text
Poynting-flux-dominated outflow
gradual magnetic acceleration
suppressed photospheric component when sigma remains high
large-radius ICMART-type magnetic dissipation
```

It then acknowledges hybrid jets parameterized by a hot component and an initial magnetization.

## Writing strength

This is a useful introduction architecture:

```text
open physical problem
-> two limiting jet models
-> hybrid reality
-> one observational diagnostic
-> two physical inferences from that diagnostic
-> why a clean sample is required
```

## Scientific caution

The statement that magnetic acceleration is the “only possibility” at \(10^{15}\)–\(10^{16}\) cm is stronger than the analysis itself establishes. Other effects must be tested before treating the inference as unique.

---

# 4. Sample selection

## Source procedure

The authors inspect the first ten years of GBM TTE light curves.

Pipeline:

```text
more than 2000 GBM triggers
-> visual inspection
-> about 300 well-defined single-pulse candidates
-> Bayesian-block rebinning
-> significance calculated for every block
-> require at least five decay-phase bins with S > 15
-> final sample: 24 pulses
```

Composition:

```text
23 long GRBs
1 short GRB
```

Small spikes are allowed on the broad pulse because the specific large-radius magnetic-dissipation picture being tested permits minijet variability superposed on a broad pulse.

## Metadata recorded in Table 1

```text
GRB name
T90
10–1000 keV fluence
selected detectors
source interval
background intervals
total number of Bayesian blocks
number of decay-wing blocks with S > 15
brightest detector used for background and Bayesian blocks
```

## Critical issue: model-informed sample definition

Allowing small spikes specifically because ICMART predicts minijets makes the sample definition partly informed by the preferred interpretation.

That does not invalidate the sample, but it creates a risk of circularity.

### Better project rule

Define pulse acceptance through model-neutral morphology criteria first:

```text
dominant-envelope fraction
number and amplitude of residual subpeaks
interpeak separation
decomposition uncertainty
pulse-isolation probability
```

Then separately ask which physical model explains the accepted substructure.

---

# 5. Comparison with our 106-pulse sample

Our sample and their sample are not directly comparable without harmonizing the selection function.

## Li & Zhang

```text
first 10 years of GBM
visual single-pulse selection
small spikes permitted
no initial requirement that the envelope be selected by Busby–Lazzati
at least five decay blocks with S > 15
final N = 24
```

## Our catalog

```text
larger mission time span, extending through later GBM years
brightness/fluence screening
Busby–Lazzati-based single-pulse selection
final N = 106 before applying the Li–Zhang decay-tail criterion
```

## Immediate cross-match project

For each of the 106 pulses calculate:

```text
number of Bayesian blocks after the peak
number with S > 15
whether at least five qualify
whether the final three are usable
whether a clean Phase I/II tail exists
```

Then report:

```text
N_106 passing Li–Zhang selection
overlap with their 24 bursts
new post-2018 candidates
selection-driven versus time-baseline-driven differences
```

This gives a clean route to extending the study with a larger and more reproducible parent catalog.

---

# 6. Pulse model and peak-time determination

## Source procedure

The authors call the Kocevski et al. profile an asymmetric fast-rising and exponential-decay **FRED** model.

**Terminology correction from the spoken reading:** it is **FRED**, not “FRAD.”

Parameters:

```text
I_p     amplitude
t_0     zero time
t_p     model peak time
r       rise-timescale parameter
d       decay-timescale parameter
```

They fix:

\[
t_0=0
\]

for every pulse.

They also compare the FRED model with a smoothly broken power-law temporal model in the appendix.

## Peak-time decision

Two cases:

### Case 1

If the FRED peak visually matches the true pulse peak, use the fitted \(t_p\).

### Case 2

If the FRED peak does not describe the observed peak, choose the peak by eye from the light curve/Bayesian-block energy-flux history.

The paper notes that the visually observed peak is often later than the FRED peak for non-ideal pulses.

## Project critique

Peak selection by eye is a major reproducibility bottleneck.

The start of the decay affects:

```text
Phase I duration
Phase II selection
temporal slope
HLE duration
emission-radius estimate
candidate classification
```

## Project action

Implement and compare:

```text
FRED posterior peak
Bayesian-block maximum
smoothed count-rate maximum
energy-flux maximum
change-point estimate
model-averaged peak
human-selected peak with audit trail
```

Propagate peak uncertainty rather than selecting one exact time without uncertainty.

---

# 7. Phase I and Phase II

## Phase I — entire decay wing

Start:

```text
FRED peak when accepted
or visually selected peak
```

Stop:

```text
end of the last Bayesian block satisfying S > 15
```

## Phase II — conservative late decay

Use only:

```text
the final three decay bins with S > 15
```

The authors motivate this because intrinsic spectral evolution can shift pulse peaks across energy bands, so curvature emission may not dominate immediately after the observed pulse peak.

## Strength

The two-phase hierarchy is conceptually useful:

```text
broad test:
    use the whole decay

conservative test:
    use only the late tail
```

## Weakness

A two-parameter temporal power law fitted to three points has only one residual degree of freedom. It is mathematically possible but scientifically fragile.

Sensitivity can be dominated by:

```text
one flux point
one underestimated error
one block boundary
one background fluctuation
one uncertain peak time
```

## Project action

Replace the fixed “last three” rule with a change-point or mixture model that estimates when HLE becomes dominant.

At minimum compare:

```text
last 3 bins
last 4 bins
last 5 bins
all suffixes satisfying minimum S/N
model-selected transition time
```

---

# 8. NaI–BGO peak-shift diagnostic

The paper compares:

```text
NaI: approximately 8 keV–1 MeV
BGO: approximately 200 keV–40 MeV
```

and identifies peak times by eye.

Six cited bursts show clear peak shifts:

```text
081224887
110721200
120426090
160216801
170921168
171210493
```

The interpretation is that temporal peaks can correspond to the evolving characteristic energy crossing detector bands. For these events, curvature emission should not be assumed to dominate immediately after the broadband pulse peak.

Other bursts are described as having approximately coincident NaI and BGO peaks, making immediate HLE more plausible.

## Important connection to Lu et al.

This paper explicitly uses the lag/spectral-evolution picture from Uhm & Zhang and is a natural follow-up to Lu et al. (2018):

```text
Lu:
    quantify energy-dependent lag and E_p evolution

Li & Zhang:
    use energy-dependent peak shifts to decide when curvature
    may begin to dominate the decay
```

## Detector-response critique

These peak times are measured in different detectors with different energy responses. A NaI–BGO peak shift can contain:

```text
true spectral evolution
different true-energy coverage
effective-area differences
energy redistribution
background differences
time-resolution differences
```

This is a high-priority use case for the detector-response transfer-function project.

---

# 9. Energy-flux light curves

## Source procedure

For each Bayesian block with \(S>15\):

1. fit the spectrum with the Band function;
2. estimate parameters by maximum likelihood;
3. calculate energy flux;
4. apply a 1–\(10^4\) keV k-correction.

The resulting energy-flux history, rather than the raw count-rate curve, is used to fit the temporal decay index.

## Strength

Energy flux is more directly comparable with the physical curvature predictions than an arbitrary count-band light curve.

## Questions for reproduction

```text
Which likelihood/statistic was used?
How was the background uncertainty handled?
Which detector cross-normalizations were free?
Was redshift known for the k-correction?
How was the k-correction handled for unknown redshift?
How were spectral posterior uncertainties propagated into energy-flux errors?
```

The source text does not fully answer all of these within the inspected section; the referenced Li data-reduction papers may be needed.

---

# 10. Simple power-law closure test

## Temporal model

The energy-flux decay is fitted as a power law with the zero time fixed to the beginning of the pulse:

\[
F(t)\propto (t-t_0)^{-\hat{\alpha}},
\qquad t_0=0.
\]

Two temporal indices are measured:

```text
alpha_PL,I     Phase I
alpha_PL,II    Phase II
```

## Spectral model

A single power law is fitted to the spectrum integrated over each phase:

\[
F_\nu\propto\nu^{-\hat{\beta}}.
\]

Two spectral indices are measured:

```text
beta_PL,I
beta_PL,II
```

The spectral fit is performed in 3ML using a Bayesian analysis, and DIC/pDIC are reported.

## Closure plane

The paper compares:

\[
\hat{\alpha}
\quad\hbox{against}\quad
2+\hat{\beta}.
\]

In Figure 2:

```text
orange:
    Phase I

blue:
    Phase II

green line:
    alpha = 2 + beta

shaded region:
    alpha > 2 + beta, interpreted as requiring acceleration
```

## Major methodological question

The temporal slope is obtained from time-resolved energy-flux points, but the spectral index is obtained from a time-integrated spectrum over the whole selected phase.

The strict closure relation is local in time and frequency. A time-integrated \(\beta\) can be biased when the spectrum evolves.

## Project action

Test three approaches:

```text
A. source replication:
    integrated beta over the phase

B. local closure:
    beta(t) paired with local alpha(t)

C. forward physical model:
    fit all time-energy data jointly without reducing to two slopes
```

---

# 11. Results of the power-law test

## Phase I

Eight of 24 initially satisfy:

\[
\hat{\alpha}\ge 2+\hat{\beta}.
\]

The paper later treats three Phase-I-only cases as spurious:

```text
090719063
130305486
150213001
```

The conclusion therefore describes roughly five robust Phase I cases.

## Phase II

Eleven of 24 satisfy the criterion:

```text
090620400
090804940
120426090
131231198
141028455
150314205
150510139
150902733
160530667
170921168
180305393
```

The authors interpret the increase from Phase I to Phase II as evidence that HLE often dominates only the late decay.

## Classification caution

The condition

\[
\hat{\alpha}\ge2+\hat{\beta}
\]

mixes two cases:

```text
approximately equal:
    constant-Gamma HLE

significantly greater:
    acceleration under the adopted model
```

A statistically principled analysis should calculate posterior probabilities for:

```text
Delta_HLE = alpha - (2 + beta)

P(Delta_HLE approximately 0)
P(Delta_HLE > 0)
P(Delta_HLE < 0)
```

rather than using a hard visual classification.

---

# 12. General non-power-law curvature test

The authors recognize that a real prompt tail is often curved and that the characteristic energy can remain inside the GBM band.

They therefore use a cutoff power law:

\[
N(E,t)
=
N_0(t)
\left(\frac{E}{E_{\rm piv}}\right)^{-\hat{\Gamma}}
\exp\left[-\frac{E}{E_c(t)}\right],
\]

with:

```text
E_piv = 100 keV
Gamma_hat = beta_hat + 1
```

For a constant bulk Lorentz factor, the curvature model predicts:

\[
E_c(t)
=
E_{c,p}
\left(
\frac{t-t_0}{t_p-t_0}
\right)^{-1},
\]

\[
F_{\nu,c}(t)
=
F_{\nu,c,p}
\left(
\frac{t-t_0}{t_p-t_0}
\right)^{-2},
\]

and therefore

\[
F_{\nu,c}(t)
=
\frac{N_{c,p}}{E_{c,p}}
E_c^2(t).
\]

## Three observational tests

For every selected pulse, Figure 3 compares:

```text
E_c(t) versus time
F_nu,c(t) versus time
F_nu,c(t) versus E_c(t)
```

This is stronger than relying only on the \(\alpha\)–\(\beta\) closure plane.

## Source result

The paper reports that CPL fits are much better than PL fits for the candidate intervals under DIC.

---

# 13. Results of the CPL test

## Approximately constant-\(\Gamma\) HLE

The source identifies:

```text
090620400
120426090
150510139
```

as matching the constant-\(\Gamma\) predictions well.

## Consistent with acceleration

The source identifies:

```text
131231198
141028455
150314205
160530667
180305393
```

as having \(E_c(t)\) or \(F_{\nu,c}(t)\) below the constant-\(\Gamma\) prediction, consistent with bulk acceleration in the adopted framework.

## Apparent violations

The source lists:

```text
090719063
090804940
130305486
150213001
150902733
170921168
```

as apparent cases that violate one or more time-evolution predictions.

The three Phase-I-only candidates:

```text
090719063
130305486
150213001
```

also fail the \(F_{\nu,c}\)–\(E_c\) test, supporting their classification as spurious.

## Important nuance

The paper states that

\[
F_{\nu,c}\propto E_c^2
\]

may remain valid regardless of bulk-Lorentz-factor evolution, based partly on unpublished and in-preparation work cited in the paper.

Therefore:

```text
F_nu,c–E_c consistency:
    supports curvature-like spectral-temporal coupling

deviation of E_c(t) or F_nu,c(t) from constant-Gamma time laws:
    carries the acceleration information
```

Do not use Equation 9 alone as evidence for acceleration.

---

# 14. Emission-radius estimates

The paper reports characteristic scales of:

\[
R_{\rm GRB}\sim10^{15}-10^{16}\ {\rm cm}.
\]

But Table 4 adopts:

```text
Gamma = 100 for every case
z = 1 for most bursts without measured redshift
```

Only a few bursts use measured redshifts.

## Correct interpretation

These are not direct radius measurements. They are scaling estimates:

\[
R_{\rm GRB}
\propto
\Gamma^2
\frac{t_{\rm HLE,obs}}{1+z}.
\]

A factor of two uncertainty in \(\Gamma\) produces a factor of four uncertainty in radius.

## Project requirement

Report a surface or posterior:

\[
p(R_{\rm GRB}\mid
t_{\rm HLE},\Gamma,z,\hbox{model}),
\]

not a single exact number.

For unknown redshift, use a population prior rather than fixing all bursts to \(z=1\).

---

# 15. Thermal-component subset

The paper notes that several bursts have previously required additional thermal components:

```text
081224887
090719063
100707032
110721200
110920546
```

These do not qualify for Phase II; only 090719063 enters Phase I, and it is later treated as spurious.

The authors interpret this as consistent with lower magnetization and possible photospheric dominance.

## Alternative explanations

This pattern might reflect:

```text
real physical difference
thermal-component selection effects
difficulty obtaining a long high-S/N tail
spectral-model bias
pulse morphology differences
different E_p evolution
```

A population analysis is needed before treating it as evidence of distinct jet composition.

---

# 16. What the figures teach

## Figure 1, pages 5–7

Each panel overlays:

```text
orange:
    Bayesian-block energy-flux points

gray:
    count-rate light curve

cyan:
    FRED fit

yellow vertical line:
    FRED peak

black vertical line:
    visually selected peak

purple:
    Phase I decay fit

green:
    Phase II late-tail fit
```

This is an excellent audit figure because it exposes the difference between:

```text
count-space morphology
energy-flux history
empirical pulse fit
human peak choice
two decay definitions
```

## Figure 2, page 12

The closure plane visually separates constant-\(\Gamma\) compatibility from the acceleration region.

Improvement for our project:

```text
plot full joint posterior ellipses
show Delta_HLE posterior
distinguish equality from significantly greater
mark thermal-component and peak-shift subclasses
```

## Figure 3, pages 13–16

The three-plane test is the scientific center of the paper:

```text
time evolution of E_c
time evolution of F_nu,c
direct F_nu,c–E_c relation
```

Our physical models should be evaluated in exactly these observable spaces.

## Figure A3, pages 22–25

NaI and BGO count curves are used to judge energy-dependent peak shifts by eye.

This should be replaced or supplemented by:

```text
posterior peak-time differences
CCF/DCCF lags
detector-response simulations
same-energy-band cross-detector comparisons
```

---

# 17. Critical assumptions and possible confounders

The simple inference

```text
alpha > 2 + beta
-> bulk acceleration
-> Poynting-flux dissipation
```

depends on many assumptions.

## Geometry

```text
uniform/top-hat angular emissivity
no structured jet
no off-axis viewing complication
no jet-edge steepening
```

## Emission

```text
abrupt cessation
single emitting surface
one dominant spectral component
isotropic comoving radiation
no continued weak emission
```

## Dynamics

```text
specific relation between angular arrival time and Doppler factor
constant or smoothly evolving bulk Lorentz factor
```

## Measurement

```text
correct zero time
correct start of HLE
adequate spectral model
time-integrated beta representative of the decay
unbiased energy-flux estimates
correct background
negligible detector-response timing bias
```

## Statistical

```text
three-point Phase II fit is stable
no important multiple-testing effect
DIC comparison is reliable
candidate selection does not inflate significance
```

Failure of the simplest closure relation proves that at least one assumption fails. It does not identify which assumption failed without further tests.

---

# 18. Structured-jet high-latitude-emission project

## Question

> How do angular structure and viewing angle modify the standard high-latitude closure relations, and can a structured jet mimic the acceleration signature \(\alpha>2+\beta\)?

## Models

```text
top-hat jet
Gaussian structured jet
power-law structured jet
two-component core+sheath jet
finite jet edge
off-axis observer
```

Parameterize:

\[
\epsilon(\theta),
\qquad
\Gamma(\theta),
\qquad
\theta_v,
\qquad
\theta_c,
\qquad
\theta_j.
\]

For an emitting surface, integrate over the equal-arrival-time surface using:

\[
\delta(\theta,\phi)
=
\left[
\Gamma(1-\beta\cos\psi)
\right]^{-1},
\]

with \(\psi\) the angle between local velocity and line of sight.

## Outputs

Derive or simulate:

```text
F_nu(t)
alpha(t)
beta(t)
Delta_HLE(t) = alpha - (2 + beta)
E_c(t)
F_nu,c(t)
F_nu,c–E_c relation
```

## Central test

Can structured angular emissivity, a jet edge, or off-axis viewing produce:

```text
alpha > 2 + beta
```

without actual bulk acceleration?

Before novelty claims, perform a targeted literature survey and identify exactly what existing structured-jet HLE derivations already cover.

---

# 19. Coupled FS+RS internal-shock test

The Rahaman–Granot–Beniamini model includes:

```text
finite shock-crossing duration
two emitting regions
different FS and RS shock-front Lorentz factors
shared shocked-fluid Lorentz factor
equal-arrival-time integration
continued emission before shock crossing ends
component crossover
```

The Li–Zhang closure assumes a much simpler switched-off, effectively single-component tail.

## Project question

Can the sum

\[
F_\nu^{\rm tot}
=
F_\nu^{\rm FS}
+
F_\nu^{\rm RS}
\]

produce an apparent

\[
\alpha>2+\beta
\]

even when neither component undergoes magnetic bulk acceleration?

## Required tests

Measure from synthetic FS+RS pulses:

```text
Phase I alpha and beta
Phase II alpha and beta
E_c(t)
F_nu,c(t)
F_nu,c–E_c
NaI/BGO peak shifts
t_p(E)
W(E)
tau(E)
```

Then pass the simulations through the exact Li–Zhang selection pipeline.

This directly tests whether the source inference is unique.

---

# 20. Curvature versus intrinsic evolution versus response

Combine the Lu et al. and Li–Zhang programs.

## Competing ingredients

```text
intrinsic E_p evolution
curvature/high-latitude emission
structured jet
bulk acceleration
continued emission
FS+RS component superposition
detector response
```

## Unified observables

\[
E_p(t),\quad
E_c(t),\quad
F_{\nu,c}(t),\quad
\tau(E),\quad
t_p(E),\quad
W(E),\quad
\alpha(t),\quad
\beta(t).
\]

## Analysis principle

Do not infer geometry from one closure plane when the full time-energy data are available.

Fit or forward-model the complete count data whenever feasible.

---

# 21. Statistical improvements

## Replace hard thresholds with probabilities

Calculate:

\[
\Delta_{\rm HLE}
=
\alpha-(2+\beta).
\]

Report:

```text
P(|Delta_HLE| < epsilon)
P(Delta_HLE > 0)
P(Delta_HLE < 0)
```

## Account for covariance

Energy-flux and spectral-index estimates arise from the same photons and are not necessarily independent.

Use joint posterior samples where possible.

## Phase-transition inference

Infer the onset of HLE as a latent change point rather than fixing Phase II to the last three bins.

## Hierarchical population model

Estimate population fractions:

```text
constant-Gamma HLE
accelerating HLE
non-HLE/continued emission
ambiguous
```

while accounting for selection and measurement uncertainty.

## Simulation-calibrated false-positive rate

Inject non-accelerating pulses with:

```text
spectral evolution
background
response
structured geometry
two components
```

and run the full source pipeline to measure how often it falsely reports acceleration.

---

# 22. Reproduction workflow

## Stage 0 — exact source replication

Select one strong case, preferably:

```text
090620400:
    approximately constant-Gamma benchmark

or

160530667:
    acceleration-consistent benchmark
```

Reproduce:

```text
detectors
background intervals
Bayesian blocks
S values
Band fits
energy-flux history
FRED fit
Phase I and Phase II
PL spectral fit
alpha–beta location
CPL time evolution
radius scaling
```

## Stage 1 — robustness

Vary:

```text
background intervals
Bayesian-block prior
S threshold
pulse peak
Phase II length
spectral model
time zero
detector set
```

## Stage 2 — cross-match the 106 sample

Apply the complete pipeline to our catalog.

## Stage 3 — physical alternatives

Forward-model:

```text
constant-Gamma top-hat HLE
accelerating shell
structured jet
intrinsic evolution
FS+RS internal shock
```

---

# 23. Required catalog additions

For every single pulse add:

```text
N_BBlocks_total
N_decay_S15
passes_LiZhang_selection
peak_FRED
peak_energy_flux
peak_count
peak_visual, if any
peak_uncertainty
Phase_I_start/stop
Phase_II_start/stop
alpha_I, beta_I, Delta_HLE_I
alpha_II, beta_II, Delta_HLE_II
CPL_Ec_evolution_class
CPL_Fnuc_evolution_class
Fnuc_Ec_relation_class
HLE_duration
assumed/measured redshift
Gamma prior
radius posterior/scaling
structured-jet sensitivity flag
FSRS sensitivity flag
response-bias flag
```

---

# 24. Writing lessons

## 24.1 Two-step physical motivation

The introduction explains that HLE can constrain:

```text
emission radius
and
bulk acceleration
```

and then connects both to composition.

This is an effective way to motivate a diagnostic: state exactly which physical quantities it can unlock.

## 24.2 Simple test followed by realistic test

The paper uses:

```text
simple PL closure relation
-> identify candidates
-> time-dependent CPL curvature test
```

This is a strong manuscript architecture.

Use it when the simple test is clearly labeled as screening rather than final proof.

## 24.3 Conservative phase hierarchy

Phase I versus Phase II allows the paper to show how conclusions change under a stricter definition.

A good general writing pattern is:

```text
broad operational definition
conservative definition
compare conclusions
```

## 24.4 Method as an explicit numbered pipeline

The methodology is organized into operational steps and each output is mapped to tables and figures.

This is excellent for reproducibility.

## 24.5 Conclusion mirrors the workflow

The conclusion restates:

```text
sample
phase definitions
simple test
complex test
radius
physical interpretation
```

A conclusion is strongest when it mirrors the evidential chain rather than merely repeating headline claims.

## 24.6 Language caution

Avoid “the only possibility” unless all important alternatives have actually been tested.

Prefer:

```text
is consistent with
is favored within the adopted model
would require
remains an alternative
cannot be distinguished with this test alone
```

## 24.7 Selection and interpretation must be separated

Do not justify sample morphology solely using the model the sample will later be used to support.

State model-neutral selection first; discuss model compatibility afterward.

---

# 25. Source audit and terminology

Preserve these details:

```text
FRED, not FRAD
t0 fixed to zero
Phase I = entire selected decay
Phase II = last three S > 15 bins
energy-flux temporal fits
PL phase-integrated spectral fits
CPL time-resolved spectral test
```

Potential source-level issues to record:

```text
- several peak times are selected by eye;
- most radii use assumed z = 1 and Gamma = 100;
- Phase II uses only three points;
- the acceleration argument partly invokes unpublished/in-preparation work;
- the paper uses alpha >= 2 + beta as an HLE candidate condition,
  but equality and significant excess have different meanings;
- DIC/pDIC behavior should be audited for weakly identified fits;
- the local closure relation is compared with a phase-integrated beta.
```

---

# 26. Immediate Claude Code actions

```text
1. Register Li & Zhang (2021) as CORE/CURVATURE/TEMPORAL.
2. Cross-match the 24-source sample with the 106-pulse catalog.
3. Implement the exact Li–Zhang selection:
       Bayesian blocks
       S > 15
       at least five decay blocks
4. Reproduce one constant-Gamma case and one acceleration case.
5. Implement FRED and alternative pulse-peak estimators.
6. Store Phase I and Phase II with uncertainty.
7. Reproduce the PL alpha–beta closure plot.
8. Reproduce the CPL E_c(t), F_nu,c(t), and F_nu,c–E_c plots.
9. Replace hard classifications with Delta_HLE posteriors.
10. Propagate redshift and Lorentz-factor uncertainty into radius.
11. Run threshold and phase-length sensitivity tests.
12. Add NaI–BGO peak-shift measurements with uncertainty.
13. Forward-fold synthetic pulses through real GBM responses.
14. Implement a structured-jet HLE prototype.
15. Pass coupled FS+RS synthetic data through the same pipeline.
16. Record every source assumption and visual decision in a manifest.
```

---

# 27. Final project takeaway

The paper provides a valuable observational pipeline:

\[
\text{single pulse}
\rightarrow
\text{late decay}
\rightarrow
(\alpha,\beta)
\rightarrow
(E_c,F_{\nu,c})
\rightarrow
R_{\rm GRB}
\rightarrow
\text{jet interpretation}.
\]

Our opportunity is to make every arrow probabilistic and model-comparative.

The key research question is not only:

> Does the decay violate the constant-\(\Gamma\) curvature relation?

It is:

> Which combination of intrinsic spectral evolution, angular jet structure, finite emission duration, FS+RS superposition, detector response, and bulk acceleration best explains the complete time-energy data?

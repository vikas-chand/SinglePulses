# Deep Reading Notes — Qin et al. (2013)

## Paper

**A Comprehensive Analysis of Fermi Gamma-Ray Burst Data. III. Energy-dependent \(T_{90}\) Distributions of GBM GRBs and Instrumental Selection Effect on Duration Classification**  
Ying Qin et al., *The Astrophysical Journal*, 763, 15 (2013).

## Reading classification

```text
CORE / DURATION / HARDNESS / BAYESIAN BLOCKS /
INSTRUMENT RESPONSE / POPULATION CLASSIFICATION / METHODS
```

## Direct relevance

```text
- detector-response temporal-observable project;
- response-corrected T90–hardness classification;
- energy-dependent pulse-duration work;
- Bayesian-block methodology and validation;
- single-pulse GRB catalog;
- literature survey of operational definitions;
- central-engine-duration versus prompt-duration studies.
```

Keep four levels separate:

```text
SOURCE:
    what Qin et al. explicitly calculate or conclude

SOURCE AUDIT:
    internal inconsistencies, typographical issues, and missing details

METHODOLOGICAL CRITIQUE:
    statistical or instrumental limitations

PROJECT ACTION:
    an executable extension for our pipeline
```

---

# 1. Scientific gap and question

The conventional \(T_{90}=2\) s boundary is observationally useful but does not map cleanly onto physical progenitor classes. Long-duration events can arise from compact-object mergers with soft extended emission, while some short-duration events are associated with massive-star environments.

The paper asks:

> **Is the familiar bimodal \(T_{90}\) distribution intrinsic to the GRB population, or is its appearance strongly modified by detector energy range and analysis method?**

The same broad-band GBM instrument is divided into several sub-bands so that the energy-selection effect can be studied without relying only on comparisons among different missions.

---

# 2. Source sample

The source uses:

```text
315 Fermi/GBM GRBs
detected through 2011 September
```

For each burst:

```text
TTE data
most illuminated NaI detector
64 ms light curves
RMFIT 3.7 for data reduction
```

Energy bands:

```text
8–15 keV
15–25 keV
25–50 keV
50–100 keV
100–350 keV
350–1000 keV
8–1000 keV
```

## Project critique

Using only the most illuminated NaI detector makes the procedure simple, but:

```text
- it discards information from other well-viewing detectors;
- the response varies with source angle;
- spacecraft motion changes the response during long bursts;
- energy redistribution differs among detectors;
- count-space duration becomes detector-specific.
```

The authors themselves explicitly state that their calculation is purely in count space and that GBM slewing could bias long-GRB durations.

---

# 3. Background treatment

## Source procedure

Two intervals far before and after the burst are selected manually.

The source:

```text
selects background intervals by eye;
fits the background linearly;
tests higher-order polynomials;
reports that resulting T90 values agree within errors.
```

The use of visually selected intervals is motivated by:

```text
pre-trigger emission in some GRBs
long post-trigger tails in others
```

Three examples are used to show that changing the chosen background intervals does not strongly change \(T_{90}\) within reported errors.

## Methodological issue

The authors correctly note that subtracting an estimated background changes the probability assumptions used by Bayesian Blocks and introduces propagated uncertainty.

After subtraction, a light-curve bin is not simply a Poisson random variable. It contains uncertainty from both:

```text
source-plus-background counts
and
the fitted background model
```

## Project action

Compare:

```text
A. source replication:
    subtract fitted background, then apply Bayesian Blocks

B. event/source-background likelihood:
    model background and source jointly

C. posterior predictive light curves:
    sample background parameters and source counts together
```

The background intervals and polynomial order must be part of the run manifest.

---

# 4. Source \(T_{90}\) procedure

For every energy-band light curve:

1. bin TTE data at 64 ms;
2. subtract the fitted background;
3. apply the Scargle (1998) Bayesian-block algorithm;
4. accumulate the block-derived count fluence;
5. define \(t_5\) and \(t_{95}\) as the epochs containing 5% and 95% of total count fluence;
6. calculate
   \[
   T_{90}=t_{95}-t_5.
   \]

## Source uncertainty procedure

The paper generates \(10^3\) mock light curves under a Poisson-error assumption.

For every mock curve it obtains \(t_5\) and \(t_{95}\). It then:

```text
fits the t5 distribution with a Gaussian;
fits the t95 distribution with a Gaussian;
uses the fitted standard deviations as errors;
combines them in quadrature.
```

The reported uncertainty is:

\[
\sigma_{T_{90}}
=
\sqrt{
\sigma_{t_{95}}^2+
\sigma_{t_5}^2
}.
\]

---

# 5. Important uncertainty correction

The direct Monte Carlo quantity is:

\[
T_{90}^{(j)}
=
t_{95}^{(j)}-t_5^{(j)}
\]

for realization \(j\).

The correct variance identity is:

\[
{\rm Var}(T_{90})
=
{\rm Var}(t_{95})
+
{\rm Var}(t_5)
-
2\,{\rm Cov}(t_{95},t_5).
\]

The source quadrature expression implicitly assumes:

\[
{\rm Cov}(t_{95},t_5)=0.
\]

That assumption is generally not guaranteed because both quantiles are calculated from the same cumulative light curve.

## Preferred procedure

For each mock:

```text
calculate t5
calculate t95
calculate T90 = t95 - t5
```

Then report the posterior/Monte Carlo distribution of \(T_{90}\) directly:

```text
median
16th–84th percentiles
possibly highest-density interval
```

Do not force Gaussian distributions when the quantiles are skewed, multimodal, or censored.

This is a small but real methodological improvement.

---

# 6. Count-space versus photon-fluence \(T_{90}\)

The paper explicitly compares two operational definitions.

## Qin et al. count-space duration

```text
background-subtracted count light curve
Bayesian blocks
count fluence
most illuminated NaI detector
```

## GBM catalog duration

The GBM catalog method:

```text
splits the burst into time bins;
fits a photon model in each bin;
accumulates model-derived photon fluence;
uses the detector response;
accounts for changing source-detector angle.
```

The paper finds that the two \(T_{90}\) measurements in 50–300 keV are generally consistent.

## Correct interpretation

This is useful validation, but it does not establish exact equivalence.

The Figure 2 comparison shows:

```text
a strong one-to-one trend
plus substantial scatter and outliers
```

Questions that remain:

```text
Which bursts are the outliers?
Are deviations correlated with duration?
Are they correlated with slew angle?
Are they correlated with spectral evolution?
Are weak or multi-episode bursts affected more strongly?
```

## Project action

For each burst calculate:

\[
\Delta T_{90}
=
T_{90}^{\rm photon}
-
T_{90}^{\rm count},
\]

and:

\[
\delta_T
=
\frac{
T_{90}^{\rm photon}
-
T_{90}^{\rm count}
}{
T_{90}^{\rm photon}
}.
\]

Regress these quantities against response geometry, \(E_{\rm p}\), fluence, morphology, and spectral-evolution class.

---

# 7. Figure 1 and Bayesian-block visual audit

Figure 1 displays:

```text
black:
    background-subtracted count-rate light curves

red:
    Bayesian-block step representation

dashed/dotted vertical lines:
    alternative background selections
```

for a bright, weak, and short GRB.

## User observation

Some red blocks visually appear to:

```text
remain high through an internal dip;
cover broad intervals containing sharp substructure;
look offset from visually obvious peaks.
```

## Caution

A Bayesian-block height is the block-average rate, not the local maximum. A valid block can therefore remain flat through smaller variations when the evidence for an additional change point does not exceed the prior penalty.

The image alone is not enough to conclude that the algorithm or plotting is wrong.

## Required audit

Reproduce the three events from raw TTE data and determine:

```text
- which Bayesian-block fitness function was used;
- which prior/penalty was used;
- whether blocks were fit to events, binned counts, or subtracted rates;
- whether the red height is a block mean or another statistic;
- whether the plotted red curve uses the same time coordinate as the data;
- how background subtraction was incorporated.
```

The exact three-source reproduction is necessary before making a figure-error claim.

---

# 8. Source audit: Figure 1 identity

The text names the bright example as:

```text
GRB 091010
```

and the plotted panel is labeled similarly.

The Figure 1 caption appears to call it:

```text
GRB 090910
```

Treat this as a probable source typo and verify the event ID before downloading data.

The caption also says “Bayesian Blacks,” an obvious typographical error for “Bayesian Blocks.”

---

# 9. Cross-mission \(T_{90}\) comparison

The paper compares distributions from:

```text
HETE-2/FREGATE
Swift/BAT
BeppoSAX/GRBM
CGRO/BATSE
Fermi/GBM
INTEGRAL/SPI-ACS
```

The mission analyses do not all use the same duration method:

```text
several:
    accumulated count rate

Swift:
    Bayesian Blocks

GBM catalog:
    response-corrected photon fluence
```

## Source result

The long-GRB peaks are broadly similar among missions, while the short-GRB distributions and short-to-long ratios vary substantially.

Examples:

```text
GBM 8–1000:
    39:253 ≈ 1:6.5

BATSE 50–300:
    500:1541 ≈ 1:3

HETE-2/FREGATE:
    no T90 < 2 s events in the cited sample
```

## Interpretation

This demonstrates that the observed duration distribution depends on:

```text
trigger sensitivity
energy band
soft-tail visibility
duration algorithm
detector response
sample selection
```

It does **not** by itself demonstrate that the underlying physical population has no bimodality.

Preferred wording:

> The observed strength and location of \(T_{90}\) bimodality are strongly instrument- and energy-dependent.

---

# 10. KMM mixture analysis

The paper uses the KMM algorithm:

```text
one Gaussian versus two Gaussian components
maximum-likelihood estimation
expectation-maximization
P_KMM as a reported significance measure
```

The text says:

```text
small P_KMM rejects a single Gaussian;
P_KMM < 0.05 conventionally rejects one component.
```

It also acknowledges that an unpenalized likelihood ratio does not account for the extra parameters of a two-component model.

## Modern replacement

For every energy band compare:

```text
one log-normal
two log-normal
three-component alternatives if justified
skewed or nonparametric density models
```

using:

```text
parametric bootstrap likelihood-ratio calibration
BIC as one diagnostic
Bayesian marginal likelihood or model probability
posterior predictive checks
cross-validation
selection-function-aware hierarchical mixture modeling
```

---

# 11. Serious internal inconsistency in the KMM reporting

Table 2 lists:

```text
8–15 keV:
    P_KMM = 2.25 × 10^-2

15–25 keV:
    P_KMM = 5.9 × 10^-4
```

According to the paper's own stated rule, both values are below 0.05 and should reject a single Gaussian.

Yet the abstract and main text state that bimodality is rejected in these two soft bands.

This cannot be silently reconciled.

Possible explanations include:

```text
- the table quantity was interpreted oppositely;
- a transcription error;
- a mismatch between histogram fit and KMM test;
- a coding/reporting error;
- “bimodality rejected” was intended to mean a different criterion.
```

## Project action

Re-run the mixture analysis from the machine-readable \(T_{90}\) catalog and report exactly what the likelihood, bootstrap, BIC, and posterior predictive tests imply.

---

# 12. Hardness-ratio definition

## Main text

The paper states that the BATSE hardness ratio is:

\[
{\rm HR}
=
\frac{
{\rm fluence}(100\!-\!350\,{\rm keV})
}{
{\rm fluence}(25\!-\!50\,{\rm keV})
}.
\]

For its GBM sample, the source says it derives observed fluence in the bands using spectral parameters reported in GCN circulars.

Therefore the GBM hardness is **model-derived from spectral parameters**, not merely a raw count ratio.

## Figure 4 caption

The caption instead defines:

\[
{\rm HR}
=
\frac{
{\rm fluence}(100\!-\!350\,{\rm keV})
}{
{\rm fluence}(50\!-\!100\,{\rm keV})
}.
\]

This is an unresolved source inconsistency.

## Project action

Before reproducing Figure 4:

```text
1. inspect machine-readable data if available;
2. reproduce both denominator choices;
3. compare with the plotted points;
4. inspect Qin et al. (2000), cited in the caption;
5. record which definition matches the figure.
```

Never cite “the Qin et al. hardness ratio” without giving the explicit bands.

---

# 13. Energy dependence of duration

The source calculates \(T_{90}\) independently in six bands.

## Population result

For long GRBs:

\[
\overline{T}_{90}
\propto
E^{-0.20\pm0.02}.
\]

This is derived by:

```text
fitting the log T90 population distribution in each band;
taking a typical/central duration;
fitting that population statistic against band-center energy.
```

It is not a universal per-burst law.

## Source result on classification

Some events classified as short in the broad or high-energy band move into the long category in softer bands.

Physical/instrumental reasons include:

```text
short GRBs are spectrally hard and trigger less efficiently in soft instruments;
soft extended emission increases duration at low energy;
pulse widths commonly broaden toward lower energy;
weak late components disappear at high energy.
```

## Project action

Measure two distinct relations:

### Population-level relation

\[
\overline{T}_{90}(E).
\]

### Per-burst relation

\[
T_{90,i}(E)
=
A_iE^{k_{T,i}}
\]

or a more flexible curved relation.

Then ask whether \(k_{T,i}\) correlates with:

```text
E_p
spectral-evolution class
lag-energy slope
pulse-width-energy slope
thermal fraction
morphology
viewing angle/response
```

---

# 14. Bimodality by band

Source qualitative conclusions:

```text
50–100 keV:
    clear bimodality

100–350 keV:
    strongest bimodality

25–50 keV:
    described as marginal

350–1000 keV:
    described as marginal

8–15 keV:
    described as not bimodal

15–25 keV:
    described as not bimodal
```

Because the KMM table conflicts with the prose for the two soft bands, these classifications must be treated as source claims pending reproduction.

---

# 15. Central-engine duration \(T_f\)

The paper defines:

\[
T_f
=
\hbox{peak time of the last significant X-ray flare}.
\]

Flare selection:

```text
Delta F / F > 5

and either:
    BAT and XRT connect without a gap
or:
    a significant flare appears after a gap
```

Sample:

```text
159 Swift GRBs
49 with no significant flare after T90
110 with significant flares after T90
```

The source interprets \(T_f>T_{90}\) as evidence that the central engine remains active after the prompt gamma-ray duration.

## Methodological caution

\(T_f\) is an operational proxy, not a direct engine clock.

Assumptions include:

```text
X-ray flare is internally powered;
the final detected flare is the final engine episode;
no later flare is missed by coverage or sensitivity;
external-shock variability is not mistaken for engine activity;
flare peak is an appropriate end-time proxy.
```

## Modern extension

Infer an engine-activity interval using:

```text
joint BAT–XRT segmentation
flare decomposition
coverage censoring
probability of internal origin
last-flare posterior rather than one peak point
```

Treat no-late-flare cases as censored by observation sensitivity and cadence.

---

# 16. Figure guide

## Figure 1

Background choices and Bayesian-block steps for three representative bursts.

Use as a reproduction/audit figure, not proof that the implementation is correct.

## Figure 2

Count-space Bayesian-block \(T_{90}\) versus GBM catalog response-corrected photon-fluence \(T_{90}\).

Main message:

```text
strong overall agreement
with non-negligible scatter and outliers
```

## Figure 3

Cross-mission duration distributions.

Main message:

```text
long-burst population comparatively stable;
short-burst fraction and bimodality strongly instrument-dependent.
```

## Figure 4

Hardness versus \(T_{90}\).

Main message:

```text
short-hard / long-soft behavior broadly resembles BATSE;
hardness-band definition is internally inconsistent in the source.
```

## Figure 5

\(T_{90}\) histograms in six energy bands.

Main message:

```text
appearance of the short-duration component changes with energy.
```

## Figure 6

Broad-band \(T_{90}\) versus sub-band \(T_{90}\) event by event.

Main message:

```text
individual bursts cross the two-second classification boundary
when the energy band changes.
```

## Figure 7

Population-average long-GRB duration versus energy.

Main result:

\[
\overline{T}_{90}\propto E^{-0.20\pm0.02}.
\]

## Figure 8

Examples of BAT–XRT light curves with and without late X-ray flares.

## Figure 9

\(T_f\) versus \(T_{90}\).

Main message:

```text
many inferred engine-activity proxies lie far above prompt T90.
```

---

# 17. Additional source inconsistencies

Preserve rather than silently correct:

```text
1. Main text hardness denominator:
       25–50 keV
   Figure 4 caption:
       50–100 keV

2. Text/figure label:
       GRB 091010
   Figure 1 caption:
       GRB 090910

3. Abstract/table:
       GBM short-to-long ratio 1:6.5
   conclusion:
       written as 1:5

4. Figure/cross-mission discussion usually gives BATSE 50–300 keV,
   while one comparison sentence lists a different BATSE range.

5. KMM P-values for the two soft bands appear inconsistent
   with the paper's verbal conclusion and its own P-value rule.

6. “Bayesian Blacks” in the Figure 1 caption is a typo.
```

---

# 18. Response-corrected duration–hardness project

The paper provides direct motivation for calculating temporal and spectral classification quantities in parallel spaces.

## Space A — count space

```text
T90_count
HR_count
```

Instrumental and operational but minimally model dependent.

## Space B — photon-fluence space

```text
T90_photon
HR_photon
```

Response-corrected but dependent on spectral model and binning.

## Space C — energy-fluence space

```text
T90_energy
HR_energy
```

Tracks energy output rather than photon number.

## Central project question

> How far does an individual GRB move in duration–hardness space when the observable is transformed from detector counts to response-corrected photon or energy fluence?

Measure:

\[
\Delta\log T_{90},
\qquad
\Delta\log {\rm HR},
\]

and classification changes.

---

# 19. Detector-response transfer function

Use injected photon models:

\[
F(E,t)
\]

and real time-dependent responses:

\[
R(c,E,\theta,t)
\]

to generate count data:

\[
C(c,t)
=
\int R(c,E,\theta,t)F(E,t)\,dE.
\]

Then compare:

```text
true photon-space T90(E)
recovered count-space T90(channel)
spectrally inferred T90
true photon hardness
count hardness
spectrally inferred hardness
```

Vary:

```text
incidence angle
spacecraft slew
E_p evolution
pulse width
soft extended emission
signal-to-background
detector combination
spectral model
```

---

# 20. Writing lessons

## 20.1 Strong gap sentence

The introduction moves from classification anomalies to one precise question:

> Is the observed \(T_{90}\) bimodality intrinsic or instrumental?

That is a clean scientific funnel.

## 20.2 Within-instrument energy test

Using several bands of one instrument is a strong design choice because it reduces some cross-mission confounding.

## 20.3 Validate a simple method against a standard product

Figure 2 provides credibility before the paper uses the count-space method for population inference.

Reusable structure:

```text
introduce simpler method
validate against accepted standard
identify residual differences
apply at scale
```

## 20.4 Calibrate causal language

The data show that energy range strongly changes observed bimodality.

Safer wording:

```text
instrumental selection modulates or may contribute to bimodality
```

Stronger wording such as:

```text
bimodality is caused by instrumental selection
```

requires population and selection-function modeling beyond what is shown.

## 20.5 Operational definitions belong in the prose

Always write:

```text
count-space T90 in 50–300 keV
photon-fluence T90 in 50–300 keV
model-derived HR(100–350 / 25–50)
```

rather than only \(T_{90}\) or hardness.

---

# 21. Immediate Claude Code actions

```text
1. Register Qin et al. (2013) as CORE/DURATION/INSTRUMENT.
2. Reproduce Figure 1 for all three example events.
3. Identify the exact Bayesian-block fitness and prior.
4. Reproduce the source count-space T90 procedure.
5. Replace quadrature uncertainty with direct Monte Carlo T90.
6. Compare both uncertainty procedures quantitatively.
7. Reproduce Figure 2 against the GBM catalog.
8. Identify and inspect the largest Figure 2 outliers.
9. Reproduce all six energy-band T90 values.
10. Re-run one/two-component mixture tests with modern calibration.
11. Resolve the contradictory KMM statements.
12. Resolve the Figure 4 hardness denominator.
13. Reproduce Figure 4 under both candidate HR definitions.
14. Calculate count-, photon-, and energy-space duration/hardness.
15. Add time-dependent GBM responses and spacecraft geometry.
16. Apply the full analysis to the modern GBM catalog.
17. Connect T90(E) with lag, width, and E_p evolution.
18. Add an assumption and source-inconsistency ledger.
```

---

# 22. Final takeaway

Qin et al. establish three crucial facts:

\[
T_{90}
\quad\hbox{depends on energy},
\]

\[
\hbox{observed duration bimodality depends on the instrument},
\]

and

\[
T_{90}
\quad\hbox{need not equal the full engine-activity timescale}.
\]

The next methodological step is to define a common response-aware framework in which duration and hardness are measured consistently in count, photon-fluence, and energy-fluence space, with uncertainty propagated through the detector response and spectral model.

---

## SOURCE AUDITS RESOLVED AGAINST THE PUBLISHED PDF (Claude Code, 2026-08-13)
`Skills_training/Qin_2013_2013ApJ76315Q_PUB.pdf`. Four of the handoff's six mandatory audits
close here; two require the #46 reproduction.

**A1. GRB 091010 vs 090910 — RESOLVED: the CAPTION is the typo.**
Main text: *"For GRB 091010, a bright burst, the derived T90 values are 7.616 ± 0.580 s and
7.552 ± 0.516..."*; the Figure-1 top panel is labelled `GRB091010`. Only the caption says
*"a bright burst (GRB 090910, top)"*. Text + panel agree ⇒ the benchmark is **GRB 091010**.

**A2. HR denominator 25–50 vs 50–100 keV — RESOLVED, and the package's "unresolved
inconsistency" framing is TOO STRONG.** The main text sentence defines the *historical BATSE*
ratio and attributes it: *"the spectral hardness ratio (HR) is defined as the fluence ratio of
the 100–350 keV band to that of the 25–50 keV band **of BATSE (Kouveliotou et al. 1993)**"* —
then immediately: *"The GBM-NaI energy band is similar to that of BATSE, but extends to lower
energies. Therefore, we **also** derive the observed fluence in the two energy bands with the
spectral parameters reported in the GCN circulars."* Figure 4's caption states the ratio
actually plotted: 100–350 / **50–100** keV. Reading: one sentence quotes the legacy BATSE
definition, the figure states the definition used for GBM; the bands are never explicitly
reconciled, so it is **under-signposted, not self-contradictory**. Still reproduce Fig. 4 under
both denominators (#46) — but do not cite it as an internal contradiction.
⚠ Confirmed regardless: their GBM hardness is **model-derived from GCN spectral parameters**,
not a raw count ratio.

**A3. Short:long ratio 1:6.5 vs 1:5 — RESOLVED: 1:6.5 is correct and internally consistent.**
Table 2 gives GBM 8–1000 keV as `39:253`, and the text states *"This ratio becomes 39:253
(1:6.5) in the GBM sample"* (against BAT 51:557 = 1:11, GRBM 111:892 = 1:8, SPI-ACS 195:724 =
1:3.7, BATSE 500:1541 = 1:3). No "1:5" appears anywhere; 39/253 = 1:6.49. No defect.

**A4. Bayesian-block fitness function and prior — RESOLVED AS A REPRODUCIBILITY GAP: the paper
never states them.** Zero occurrences of a fitness/prior/ncp_prior/p0/false-alarm specification
anywhere in the text. Consequence: Figure 1's blocks **cannot be reproduced from the paper
alone** — any reproduction must scan the prior and report which choice reproduces the published
blocks. This also means the handoff's rule *"do not call the Figure-1 blocks wrong before
reproduction"* is doubly right: with the prior unspecified, apparent block anomalies are
unfalsifiable from the figure.

**Still OPEN (need the #46 reproduction, not a PDF read):**
- A5. Re-run the soft-band KMM tests (Table 2 `GBM-1` 2.25e−2, `GBM-2` 5.9e−4 both satisfy
  their own stated `P_KMM < 0.05` rejection rule while the text reports bimodality rejected).
- A6. Reproduce Fig. 1 blocks + T90 for GRB 091010 / 090126B / 090227B, and compare the
  quadrature σ_T90 against a direct per-realization Monte-Carlo T90 distribution.

**Already actioned outside #46:** the σ_T90 covariance lesson triggered an audit of OUR OWN
estimator and closed a campaign-wide defect — see `dev/ai_guides/Temporal.md` defect ledger
(T90 errors, fixed 2026-08-13).

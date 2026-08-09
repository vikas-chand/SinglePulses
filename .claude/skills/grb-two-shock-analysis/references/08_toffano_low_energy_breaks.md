# Toffano et al. (2021): low-energy breaks and hidden-break simulations

## 1. Source and role in this project

**Paper:** M. Toffano, G. Ghirlanda, L. Nava, G. Ghisellini, M. E. Ravasio & G. Oganesyan, *The slope of the low-energy spectrum of prompt gamma-ray burst emission*, A&A 652, A123 (2021).

This paper supplies the **measurement and detectability layer** of the single-pulse project:

- How should a low-energy spectral break be searched for?
- When can a true break be hidden by the GBM response, limited signal-to-noise ratio, or proximity to another characteristic energy?
- How does a Band fit distort the recovered low-energy index when the true spectrum is doubly broken?

The Rahaman–Granot–Beniamini model supplies a possible **physical interpretation layer**:

- a weaker forward shock (FS) can produce the lower-energy structure;
- a stronger reverse shock (RS) can dominate the higher-energy peak;
- the two components are hydrodynamically coupled.

Do not reverse this order. First establish what the data support and what the detector can resolve. Then test the FS+RS hypothesis.

Use the following labels in all reports:

- **PAPER:** directly reported by Toffano et al.;
- **PROJECT INFERENCE:** our interpretation of the paper for the 106-pulse analysis;
- **PROJECT DECISION:** a method we choose for our pipeline;
- **FUTURE IDEA:** work that is not required for the main analysis.

---

## 2. Scientific hypothesis of Toffano et al.

### PAPER

Prompt GRB spectra are commonly fitted with Band, whose low-energy photon index is typically around:

```text
alpha_Band ~ -1
```

In some bright long GRBs, the low-energy segment is resolved into two photon-index segments separated by a break:

```text
alpha_1,2SBPL  below E_break
alpha_2,2SBPL  between E_break and E_peak
beta_2SBPL     above E_peak
```

The observed typical values are near:

```text
alpha_1,2SBPL ~ -0.6
alpha_2,2SBPL ~ -1.5
```

These are close to the synchrotron slow-cooling and fast-cooling asymptotes in photon-index notation.

The paper tests the hypothesis that many spectra fitted by Band may still contain a low-energy break. In that case, `alpha_Band` is not necessarily a fundamental emission slope. It can be an effective average over two unresolved segments.

Define:

```math
R_E = E_{\rm break}/E_{\rm peak}.
```

The central qualitative result is:

```text
R_E -> 1:
    E_break approaches E_peak
    Band returns a harder alpha_Band, approaching alpha_1,2SBPL

R_E -> small:
    E_break moves toward the detector's low-energy boundary
    Band returns a softer alpha_Band, approaching alpha_2,2SBPL
```

`alpha_Band` therefore contains information about where an unresolved break may lie, but the mapping also depends on absolute energies, slopes, fluence, background, and response.

---

## 3. Sample construction

### PAPER

The parent Fermi catalog contained 2669 GRBs through April 2020.

The selected sample was:

```text
Long GRBs:
    fluence(10–1000 keV) > 1e-4 erg cm^-2
    catalog E_peak > 300 keV

Short GRBs:
    fluence(10–1000 keV) > 5e-6 erg cm^-2
    catalog E_peak > 300 keV
```

The final sample contained:

```text
27 long GRBs
9 short GRBs
```

The large-fluence and large-`E_peak` cuts were chosen to increase the probability that a lower-energy break would be both statistically measurable and separated from `E_peak` within the GBM band.

GRB 090902B was excluded because its additional power-law component plus multitemperature-blackbody structure makes isolation of the low-energy break ambiguous.

### PROJECT INFERENCE: why the long- and short-burst fluence cuts differ

The paper reports the cuts but does not fully develop the following rationale.

For a short burst, even a moderate fluence accumulated over a very brief duration usually implies a large instantaneous flux and therefore useful count statistics. For a long burst, a moderate fluence may result from a long integration of a relatively faint signal. Such a burst can have many total counts while still having weak local spectral information or severe time-averaging.

This is a plausible rationale, not a statement to attribute to the authors.

### PROJECT DECISION

Do **not** impose the Toffano fluence cuts on the entire 106 single-pulse catalog after the sample has already been defined.

Instead:

1. analyze all 106 pulses consistently;
2. calculate a break-detectability quality metric;
3. define a high-information subset for population-level break claims;
4. retain lower-information pulses for upper/lower limits and hidden-break simulations.

A low-quality non-detection is not evidence that the break is absent.

### Critical-reading note on exclusions

Treat GRB 090902B as a **complexity-control case**, not evidence of misconduct or ideological selection. The paper's stated reason is methodological: additional components impede clean measurement of the break. A separate analysis can ask whether the FS+RS model can handle such complex spectra, but that is beyond the clean primary sample.

---

## 4. Data reduction and spectral setup

### PAPER

For each burst, Toffano et al. used:

```text
2 NaI detectors
1 BGO detector
```

selected by viewing geometry.

They used time-integrated CSPEC spectra, normally over catalog `T90`. For two long, highly structured bursts, they selected the brightest portion instead:

```text
GRB 130427A: 3–15 s
GRB 160625B: 188–210 s
```

Background was estimated from intervals before and after the burst. The latest response matrices were generated through `gtburst`.

Energy selections were:

```text
NaI: 8–900 keV
BGO: 0.3–40 MeV
```

The interval:

```text
30–40 keV
```

was excluded because of inaccurate response modeling around the iodine K edge at 33.17 keV.

The two NaI and one BGO spectra were fitted jointly with an intercalibration constant.

### PROJECT DECISION for our pipeline

Use the paper's energy selections and K-edge exclusion as a reproducible benchmark, but allow a configuration file to define instrument- and response-version-specific cuts.

For the 106-pulse project:

```text
Primary source interval:
    the objectively defined single-pulse interval,
    not automatically catalog T90

Background:
    at least two clean off-source intervals
    validate polynomial/order stability

Detector selection:
    viewing geometry + data-quality checks
    document every exclusion

Cross-calibration:
    fit constants with stated priors
    do not silently fix them unless required for identifiability
```

### Methods-writing pattern

A concise methods sentence can be adapted as follows:

> We jointly fitted the selected NaI and BGO detectors over 8–900 keV and 0.3–40 MeV, respectively. Channels from 30–40 keV were excluded to reduce systematic residuals associated with imperfect modeling of the NaI iodine K edge near 33.17 keV. Relative detector normalizations were included as nuisance parameters.

Do not copy this sentence blindly; make it match the actual software, data type, and response version.

---

## 5. Spectral models

### PAPER

The two main models are:

```text
Band
2SBPL
```

The 2SBPL contains:

```text
alpha_1
alpha_2
beta
E_break
E_peak
normalization
```

The curvature parameters were fixed to:

```text
n1 = n2 = 2
```

following earlier work.

### PROJECT DECISION: model set for single pulses

Use a wider, ordered comparison:

```text
CPL
Band
SBPL
2SBPL
Band + BB
SBPL + BB
single-zone synchrotron
coupled FS + RS analytic model
```

Potential later models:

```text
full-kernel coupled synchrotron
photosphere + FS + RS
magnetized shocks
additional LAT power law
```

Never equate:

```text
2SBPL = two-shock model
```

A 2SBPL is an empirical shape. It can be consistent with several physical scenarios.

---

## 6. Statistical treatment

### PAPER

The authors state that the spectra have enough counts to use chi-square minimization. They compare Band and 2SBPL with:

```math
\Delta {\rm AIC}
=
{\rm AIC}_{\rm Band}
-
{\rm AIC}_{\rm 2SBPL}.
```

Their operational rule is:

```text
Delta AIC >= 6:
    prefer 2SBPL
    classify the break as significant in their analysis
```

### Important interpretation

AIC is a relative information criterion. `Delta AIC >= 6` is a useful model-ranking convention, but it is not a universal law and should not be described as a literal posterior probability that a model is true.

### PROJECT DECISION

For GBM source-plus-background count spectra, use the Poisson-appropriate likelihood supported by the analysis framework, such as PG-statistic when the background uncertainty is treated as Gaussian.

Do not choose chi-square solely because the **total** spectrum has many counts. The approximation must be adequate for the actual channel grouping and error model, including the high-energy tail.

Recommended hierarchy:

```text
Primary:
    count-space likelihood / PG-statistic
    posterior predictive checks

Model-ranking summaries:
    Delta AIC
    Delta BIC
    Bayesian evidence or predictive criteria when reliable

Component calibration:
    parametric bootstrap / forward simulations
```

For continuity with Toffano et al., report `Delta AIC >= 6` as a **replication threshold**, while also reporting the primary count-likelihood and simulation-based result.

---

## 7. Direct fit results

### PAPER

For the 27 long GRBs:

```text
12 preferred 2SBPL with Delta AIC >= 6
15 were adequately fitted by Band
```

For the 9 short GRBs:

```text
none required a resolved low-energy break
```

The detected long-GRB breaks were approximately:

```text
E_break ~ 80–280 keV
```

The characteristic photon-index distributions for the 12 break detections peaked near:

```text
alpha_1,2SBPL ~ -0.71
alpha_2,2SBPL ~ -1.71
```

For several short GRBs, the high-energy Band index was only bounded, so a simpler cutoff power law could also describe the data.

### Interpretation offered by the paper

The relatively hard short-GRB `alpha_Band` distribution may indicate:

```text
E_break ~ E_peak
```

rather than physical absence of a break.

For long GRBs fitted only by Band, `alpha_Band` lies between the typical `alpha_1` and `alpha_2` distributions, motivating the hidden-break interpretation.

### PROJECT CAUTION

These are time-integrated spectra. Time integration can:

- mix changing `E_break` and `E_peak`;
- broaden curvature;
- soften fitted indices;
- merge two components;
- produce an apparent Band shape even when each instantaneous spectrum is different.

Our single-pulse project must compare time-integrated and time-resolved results rather than treating them as interchangeable.

---

## 8. The 160509A multi-instrument lesson

### PAPER

For GRB 160509A:

- GBM constrained a low-energy break near 80 keV;
- GBM alone did not constrain the high-energy peak adequately;
- LLE was added to constrain the high-energy index and `E_peak`;
- the joint fit covered approximately 10 keV–300 MeV;
- the LLE-to-NaI intercalibration normalization was fixed to one in that analysis.

### PROJECT DECISION

Create an inventory for all 106 pulses:

```text
has_GBM
has_LLE
has_LAT_prompt
has_Swift_BAT
has_Swift_XRT_prompt_or_early
has_optical_prompt
```

Use:

```text
GBM-only baseline for every pulse
GBM+LLE/LAT extension for the available subset
```

LLE is especially valuable when:

```text
E_peak is high
beta is weakly constrained
BGO alone cannot locate the high-energy turnover
```

Prefer to fit cross-normalization constants with informative priors where the data allow. Fixing a constant should be documented and stress-tested.

---

## 9. Simulation program in Toffano et al.

## 9.1 Generic response of Band to a moving break

### PAPER

The input 2SBPL was chosen to resemble a typical long GRB:

```text
alpha_1 = -0.65
alpha_2 = -1.67
E_peak = 1000 keV
beta = -2.5
```

Only `E_break` was moved.

The authors:

1. generated spectra through a real GBM background and response;
2. fitted every simulated spectrum with both 2SBPL and Band;
3. repeated each `E_break` setting 200 times;
4. studied a high-S/N and a roughly ten-times-lower-S/N case.

Representative levels were:

```text
high S/N ~ 21, fluence ~ 3.5e-4 erg cm^-2
lower S/N ~ 2.7, fluence ~ 3.5e-5 erg cm^-2
```

At lower S/N, Band can remain acceptable over much of the break-position range. Even at high S/N, breaks become difficult to identify when they are very near the low-energy boundary or close to `E_peak`.

### PROJECT LESSON

Detectability is a function of at least:

```text
E_break
E_peak
R_E
alpha_1
alpha_2
beta
fluence / source counts
background
detector response
viewing geometry
time interval
```

A population plot of detected versus non-detected breaks is biased unless the detection efficiency over this space is modeled.

---

## 9.2 Template simulations for the 12 detected-break bursts

### PAPER

For each of the 12 long GRBs with a detected break:

1. retain the fitted spectral parameters;
2. vary only `E_break` from roughly `0.01 E_peak` to `E_peak`;
3. use that burst's background and response;
4. renormalize to preserve the real burst's integrated energy flux;
5. fit the simulations with Band and 2SBPL.

This produces a burst-specific track in:

```text
R_E versus alpha_Band
```

### PROJECT LESSON

Do not rely on one universal `R_E -> alpha_Band` calibration. Generate a response-aware track for each pulse or for well-defined groups of similar pulses.

---

## 9.3 Hidden-break simulations for the 15 Band-only long GRBs

### PAPER

The underlying model was assumed to be 2SBPL and scanned over:

```text
alpha_1:
    approximately -0.3 to -1.05 in steps of 0.03

alpha_2:
    approximately -1.1 to -1.9 in steps of 0.03

E_break:
    2 keV to E_peak in steps of 2 keV

beta:
    fixed to the Band-fit value
```

For each parameter combination, ten spectra were simulated using the real background and response, then fitted with both Band and 2SBPL.

A simulated hidden-break case was accepted when:

```text
Delta AIC < 6
Band alpha and beta agree with the real fit within 1 sigma
Band E_peak agrees with the real fit within 3 sigma
```

The accepted grid gave upper or lower constraints on where an unresolved break could lie.

### PROJECT DECISION: adapt and strengthen this test

For every pulse classified as Band-only:

1. use posterior samples rather than a single best-fit Band spectrum;
2. simulate candidate 2SBPL or FS+RS spectra through the exact responses;
3. preserve the observed source fluence or expected source counts;
4. refit with the complete model set;
5. estimate:
   - probability of detecting the break;
   - allowed hidden-break interval;
   - false-positive rate;
   - bias in recovered `alpha_Band` and `E_peak`;
6. classify the result as:
   - break excluded over a stated range;
   - break allowed but unresolved;
   - data non-informative;
   - break detected.

This distinction is essential:

```text
no detected break != no physical break
```

---

## 10. Connection to the Rahaman–Granot–Beniamini model

### PAPER CONNECTION

Rahaman et al. show that:

```text
fast-cooling FS + fast-cooling RS:
    can resemble a doubly broken spectrum

marginally fast-cooling FS + fast-cooling RS:
    can resemble a dominant Band-like peak plus a weaker BB-like bump
```

The RS generally produces the higher-energy peak; the weaker FS produces the lower-energy structure.

### PROJECT INFERENCE

The Toffano ratio:

```math
R_E = E_{\rm break}/E_{\rm peak}
```

is an observational morphology parameter.

The Rahaman coupling uses intrinsic FS and RS characteristic frequencies:

```math
r_\nu = \nu_{0,\rm FS}/\nu_{0,\rm RS}.
```

These quantities may be related, but they are **not automatically identical**. In a summed spectrum, the fitted 2SBPL break can be a transition created by overlapping components rather than the exact FS `nu F_nu` peak.

Therefore:

```text
Do not insert fitted E_break/E_peak directly into Equation 7
without calibrating the mapping through the full forward model.
```

The correct procedure is:

1. fit empirical models to describe the observed morphology;
2. fit the coupled FS+RS model;
3. forward-simulate it through the detector;
4. fit those simulated counts with 2SBPL;
5. determine how fitted `E_break/E_peak` maps onto intrinsic `nu_0,FS/nu_0,RS`;
6. infer shock properties only from the physical-model posterior.

---

## 11. What this paper changes in the 106-pulse project

The project is now a three-layer inference problem.

### Layer A — empirical measurement

For every single pulse, measure:

```text
pulse shape
energy-dependent timing
Band/CPL/SBPL/2SBPL/BB+continuum parameters
E_break
E_peak
spectral slopes
model support
```

### Layer B — detector identifiability

For every detected or undetected break, ask:

```text
Could GBM have resolved the break if it were present?
What ranges of E_break are excluded?
What ranges remain hidden?
How are alpha_Band and E_peak biased?
```

### Layer C — physical interpretation

Only after Layers A and B, test:

```text
coupled FS+RS internal shock
single-zone synchrotron
photosphere + nonthermal
magnetic/reconnection alternatives
```

This protects the project from interpreting an instrumental non-detection as a physical absence.

---

## 12. Reproducibility checklist

For every pulse, save:

```text
event and pulse identifier
source interval
background intervals
detectors and viewing angles
response versions
energy cuts
K-edge treatment
cross-normalization priors/results
binning/grouping
fit statistic
model priors
optimizer/sampler settings
posterior samples
count-space residuals
AIC/BIC/evidence summaries
simulation seeds
hidden-break detection efficiency
plots and machine-readable tables
```

Never publish only a preferred-model table. Publish enough information to reproduce why alternatives were rejected.

---

## 13. Claims that the project must avoid

Do not claim:

```text
Band-only means no cooling break
Delta AIC >= 6 proves the physical origin
alpha_Band is a direct synchrotron slope
2SBPL proves synchrotron
Band+BB proves a photosphere
a fitted break is automatically the FS peak
no short GRB has a physical low-energy break
time-integrated parameters equal instantaneous physics
```

Preferred wording:

```text
The data prefer...
The break is resolved over...
A break remains allowed but unresolved over...
The observed morphology is consistent with...
The coupled model is supported/disfavored/non-identifiable under...
```

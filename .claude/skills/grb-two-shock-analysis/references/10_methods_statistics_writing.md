# Methods, statistics, and writing patterns for the GRB pipeline

## 1. Purpose

This file is a reusable methods-writing and review checklist. It records practices learned while reading Toffano et al. and related papers, while distinguishing source practice from our preferred pipeline.

---

## 2. Detector and response paragraph

Required content:

```text
data type
detectors selected
selection criterion
source interval
background intervals
response generation
energy bounds
excluded channels
cross-calibration constants
```

Template:

> We analyzed Fermi/GBM data from the selected NaI and BGO detectors with favorable source-viewing geometry and stable background. Source spectra were extracted over the objectively defined pulse interval, and background was modeled using off-source intervals bracketing the event. Detector responses were generated for the source interval. Fits used the validated energy ranges for each detector; channels affected by known response systematics were excluded. Relative detector normalizations were included as nuisance parameters.

Replace every generic phrase with the actual implementation.

---

## 3. Iodine K-edge sentence

Template:

> Channels between 30 and 40 keV were excluded because residual calibration uncertainty around the NaI iodine K edge near 33.17 keV can introduce artificial spectral structure.

Before using this sentence, verify that the exclusion is still required for the response version and analysis stack.

---

## 4. Likelihood paragraph

Preferred template:

> Spectral models were forward-folded through the detector responses and fitted in count space using a Poisson-appropriate source-plus-background likelihood. We report PG-statistic values and inspect posterior predictive residuals. Information criteria are provided as model-ranking summaries but are not treated as component-significance probabilities.

Avoid:

```text
The burst was bright, therefore chi-square is valid.
```

Brightness of the total spectrum does not guarantee Gaussian behavior in every fitted channel.

---

## 5. AIC paragraph

Template:

> We define `Delta AIC = AIC_simple - AIC_complex`, so positive values favor the more flexible model. For direct comparison with Toffano et al. (2021), `Delta AIC >= 6` is recorded as a strong-preference benchmark. Our physical conclusions additionally require stable parameters, acceptable posterior predictive checks, and simulation-calibrated recovery of the added structure.

Do not write:

```text
Delta AIC = 6 means the complex model is 95% true.
```

---

## 6. Break-detection statement

Preferred categories:

```text
resolved break
break allowed but unresolved
break excluded over a stated interval
non-informative
```

Template:

> The absence of a formally preferred 2SBPL fit does not by itself exclude a low-energy break. We therefore used response-folded simulations to determine the range of `E_break` values that would remain hidden while reproducing the observed Band parameters and model ranking.

---

## 7. Time-integrated versus time-resolved caveat

Template:

> Time-integrated spectra maximize photon statistics but can mix spectral evolution and bias the recovered slopes and characteristic energies. We therefore repeat the analysis in time-resolved bins and test whether the inferred break persists, evolves, or arises from temporal averaging.

---

## 8. Multi-instrument extension paragraph

Template:

> GBM-only fits provide the uniform baseline. LLE/LAT data are added for bursts in which the high-energy index or peak energy is poorly constrained within the GBM band. Cross-normalization parameters and any additional high-energy component are introduced under predeclared rules and tested through posterior predictive checks.

---

## 9. Physical-interpretation paragraph

Template:

> Empirical models are used to characterize spectral morphology and do not uniquely identify the radiation mechanism. We subsequently test whether the observed break or low-energy bump can be reproduced by the coupled FS+RS internal-shock model, a one-zone synchrotron spectrum, or a photospheric-plus-nonthermal model. The FS+RS interpretation is accepted only when its hydrodynamic coupling and temporal predictions are simultaneously supported.

---

## 10. Review checklist for every draft result

Before writing a claim, answer:

1. Is this directly measured or model-derived?
2. Is it time-integrated or time-resolved?
3. Is the parameter constrained or prior-limited?
4. Was the result stable to background and detector selection?
5. Was the extra component calibrated with simulations?
6. Does the claim distinguish morphology from physical origin?
7. Could the detector have resolved the predicted feature?
8. Does the temporal behavior support the same interpretation?
9. Are all uncertainty intervals propagated?
10. What observation would falsify the claim?

---

## 11. Detector-exclusion paragraph

Template:

> Detector X was initially included but displayed a coherent residual trend not seen in the other selected detectors. Because the source geometry indicated a plausible blockage/calibration issue, we excluded it under the predeclared detector-quality rule. Fits with and without detector X are retained in the reproducibility archive.

Do not state only that the fit improved after removal.

## 12. LAT field-model paragraph

Template:

> The LAT source model included catalog point and extended sources within the model region together with the Galactic and isotropic diffuse components. Because the burst lies near the Galactic plane, we explicitly inspected nearby extended emission and allowed relevant nuisance normalizations to vary.

## 13. Component-flux paragraph

Template:

> For intervals in which the added component was supported, we calculated its energy flux and fractional contribution over a common energy range. Intervals without a significant component are reported as conditional estimates or limits and are visually distinguished from detections.

## 14. Conditional physical-inference paragraph

Template:

> The following outflow parameters are conditional on identifying the low-energy component as photospheric and on the assumptions of the adopted hybrid-jet framework. We therefore report their dependence on the launch radius, radiative efficiency, and alternative spectral decomposition rather than quoting a single model-independent value.


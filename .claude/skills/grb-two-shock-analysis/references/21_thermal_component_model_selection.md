# Skill Reference — Model Selection for Weak Thermal Components in GRB Spectra

## Purpose

Provide a statistically defensible workflow for comparing:

```text
nonthermal model
versus
nonthermal + blackbody
```

in time-resolved Fermi/GBM spectra.

## Do not use this rule

```text
AIC for non-nested models
BIC for nested models
```

Nestedness does not determine whether AIC or BIC is valid.

## Distinguish the goals

```text
AIC:
    predictive information criterion

BIC:
    asymptotic approximation connected to marginal likelihood
    under regularity assumptions

Bayes factor:
    ratio of marginal likelihoods

likelihood-ratio statistic:
    improvement in maximum likelihood
```

## Minimum comparison set

```text
PL
CPL
Band
PL+BB
CPL+BB
Band+BB
```

Add SBPL/2SBPL or physical models when the data justify them.

## Required output per model

```text
parameter count
number of fitted spectral bins
fit statistic and sign convention
maximum log likelihood
AIC
BIC
Delta AIC
Delta BIC
posterior predictive residuals
prior definitions
convergence diagnostics
```

## Thermal claim levels

### Level 0 — unsupported

```text
BB normalization unconstrained
temperature at prior boundary
no predictive improvement
```

### Level 1 — suggestive

```text
one criterion favors +BB
but base-model dependence or prior dependence is substantial
```

### Level 2 — robust within empirical models

```text
+BB favored across viable baselines
temperature and flux constrained
result survives response/background/time-bin changes
```

### Level 3 — simulation-calibrated detection

```text
false-positive rate measured under nonthermal truth
power measured under injected thermal truth
observed statistic lies in a calibrated tail
```

## Boundary problem

For base versus base+BB:

```text
normalization = 0 is a parameter-space boundary
temperature is undefined under the null
```

Do not assume Wilks theorem without calibration.

## Preferred calibration

```text
parametric bootstrap
posterior predictive simulation
simulation-based calibration
Bayes factor with documented priors
PSIS-LOO/WAIC for predictive comparison
```

## Type I experiment

```text
simulate from PL/CPL/Band
forward fold through DRM
add background and Poisson noise
fit all models
apply decision rule
measure false BB detections
```

## Type II experiment

```text
simulate from base+BB
vary kT and thermal fraction
fit all models
measure missed detections
```

## Report model uncertainty

When two models have:

```text
Delta AIC < 2
or
Delta BIC < 2
```

describe them as statistically indistinguishable under that criterion.

Do not force a unique baseline.

## Physical inference rule

Only calculate a blackbody radius after the thermal component passes the adopted detection/robustness standard.

Propagate the full posterior of:

```text
F_BB
kT
redshift
geometry/color factor
```

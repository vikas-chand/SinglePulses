# Validation, model comparison, and failure modes

## 1. Reproducibility gates

Do not apply the model to a population until all gates pass.

### Gate 1: mathematical reproduction

- Equation 6 spectral function matches analytic limits.
- Equation 7 ratios are recovered numerically.
- EATS geometry and crossing times are consistent.
- Figure 2 morphology is reproduced.
- Figure 3 tracks are reproduced.
- Figure 4 spectra are reproduced.

### Gate 2: synthetic identifiability

- Known parameters are recovered from noiseless spectra.
- Known parameters are recovered from response-folded counts.
- Coverage of credible intervals is calibrated.
- Component label switching is absent.
- Weak FS cases are correctly identified as unconstrained rather than spuriously detected.

### Gate 3: model discrimination

Quantify confusion between:

```text
Band+BB  <->  marginal-FS + RS
2SBPL    <->  fast-FS + RS
one-zone synchrotron <-> coupled FS+RS
overlapping pulses <-> two shocks in one collision
```

### Gate 4: pilot bursts

Analyze a small set of flagship bursts before the full sample.

---

## 2. Statistical practice

### Likelihood

Use Poisson or PG-statistic count likelihoods appropriate to source and background data. Forward-fold every spectral model through the same response.

### Model comparison

Use several diagnostics:

- posterior predictive checks;
- residual structure in count space;
- Bayesian evidence when computationally reliable;
- approximate predictive criteria such as LOO where valid;
- BIC/AIC as secondary summaries;
- simulation-based false-component tests.

Do not declare a physical component solely because `Delta BIC` exceeds a threshold.

### Component testing

For a weak FS or BB-like component, generate data under the simpler/null model, refit with and without the added component, and measure the empirical false-positive distribution.

This is important because:

- component normalization is bounded at zero;
- component location may be undefined under the null;
- asymptotic likelihood-ratio assumptions may fail.

---

## 3. Selection effects

### Hard-to-soft selection

The proposal's primary sample selects hard-to-soft single pulses, which are already closer to the model prediction.

Use a negative-control intensity-tracking sample to avoid circular confirmation.

### Brightness selection

Detecting a low-energy FS component requires high statistics and broad energy coverage. Report detection efficiency as a function of:

```text
fluence
E_pk
FS/RS ratio
component separation
detector angle
background
```

### Time-bin selection

Coarse bins can mix evolving spectra and create artificial breaks or bumps. Fine bins can become prior-dominated.

Repeat the result under multiple binning schemes.

---

## 4. Major degeneracies

### 4.1 Two similar spectral components

If the FS and RS peaks overlap, the sum can resemble a single broad component. Temporal evolution is essential.

### 4.2 Peak ratio versus geometry

Observed time-integrated peak ratios contain `R_f/R0` corrections and cannot be mapped directly to shock strength without the full model.

### 4.3 Efficiency versus beta ratio

Equation 7 couples radiative efficiency to `beta_21/beta_34`. These relative velocities must be inferred from the hydrodynamics.

### 4.4 Microphysics versus hydrodynamics

Allowing independent `epsilon_e`, `epsilon_B`, `xi_e`, and `p` in both zones can absorb hydrodynamic signatures and destroy identifiability.

Start with equal microphysics and relax one assumption at a time.

### 4.5 Additional LAT component

An extra LAT power law may represent early afterglow or another prompt component, but it may also absorb model failure.

Use a predeclared inclusion rule:

1. fit GBM;
2. predict LAT;
3. add the component only if posterior predictive checks fail systematically;
4. repeat the prompt-model comparison after marginalization.

---

## 5. Physical failure modes

The model may fail because:

- the outflow is strongly magnetized and shocks are weak;
- magnetic reconnection dominates;
- a real photosphere dominates the low-energy component;
- shell geometry is strongly spherical;
- the emitting region has finite radial thickness;
- the shell-speed contrast is outside the modeled regime;
- the pulse contains multiple collisions;
- microphysics differs substantially between FS and RS;
- inverse-Compton emission modifies the spectrum;
- pair opacity or self-absorption matters.

A failure of the baseline does not identify which alternative is correct. Report the specific violated prediction.

---

## 6. Coding failure modes

Watch for:

- confusing shock-front Lorentz factor with downstream Lorentz factor;
- confusing bulk `beta_1, beta_4` with relative `beta_21, beta_34`;
- using photon indices where `F_nu` slopes are required;
- normalizing at the wrong peak definition;
- treating `F_0` as `nu_0 F_0`;
- wrong observer/rest-frame redshift factor;
- discontinuity at the Band join;
- integration bounds outside the active shock region;
- continuing on-axis emission after `R_f`;
- losing the HLE contribution;
- arbitrary FS/RS label swapping;
- fitting unfolded data rather than response-folded counts;
- silently clipping unphysical parameters.

---

## 7. Success criteria

### Baseline software success

- published curves reproduced within documented tolerance;
- all unit and regression tests pass;
- synthetic posterior coverage is acceptable.

### Burst-level scientific success

A burst supports the baseline only when:

1. the coupled model gives adequate count-space predictions;
2. the same parameter set explains temporal and spectral behavior;
3. Equation 7 coupling is respected;
4. inferred efficiency ratios are physically allowed;
5. hard-to-soft and decay tracks are consistent;
6. competing models are not predictively superior;
7. the result survives background, binning, and detector choices.

### Population-level success

Report:

- fraction of pulses supported;
- fraction disfavored;
- fraction non-identifiable;
- dependence on brightness and energy coverage;
- association with hard-to-soft versus intensity-tracking classes.

Do not collapse non-identifiable cases into successes or failures.

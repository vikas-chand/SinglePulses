# Observables needed to test the two-shock model

## 1. Guiding principle

The strongest test is not:

```text
Does FS + RS fit the spectrum?
```

It is:

```text
Can one hydrodynamically coupled FS+RS model explain the pulse morphology,
time-resolved spectra, component ratios, and decay evolution simultaneously?
```

Use a joint hierarchy of temporal, spectral, and coupling tests.

---

## 2. Minimum data products for each pulse

### 2.1 Event and detector metadata

Record:

```text
burst_id
trigger_time
redshift, if known
detectors used
energy ranges
response versions
background intervals and polynomial order
source interval
pulse start and end
data quality flags
```

### 2.2 Multi-band light curves

Construct background-subtracted or likelihood-modeled light curves in several bands spanning the available response. A typical GBM layout might include:

```text
8–20 keV
20–50 keV
50–100 keV
100–300 keV
300–1000 keV
1–10 MeV
```

Adapt bands to detector statistics and the fitted peak energy.

For each band measure:

```text
onset time
peak time
rise time
decay time
FWHM
pulse asymmetry
plateau or shoulder duration
number of local maxima
post-peak decay index
uncertainty on every quantity
```

Also measure cross-band:

```text
spectral lag
energy dependence of width
energy dependence of peak time
energy dependence of pulse asymmetry
```

### 2.3 Time-resolved spectral products

For each statistically justified time bin, record:

```text
bin start and stop
model
nu_pk or E_pk
nu_pk F_nu,pk
low-energy slope
high-energy slope
low-energy component peak or break
low/high component amplitude ratio
fit statistic
posterior uncertainty and covariance
```

Use multiple binning schemes to test robustness:

- constant signal-to-noise;
- Bayesian blocks;
- pulse-phase bins;
- progressively finer bins near the peak;
- coarser bins for time-integrated comparison.

---

## 3. Temporal tests

### T1. One or two hydrodynamically linked pulse contributions

**Paper prediction:** FS and RS each produce a pulse that peaks near its shock-crossing arrival time and then develops a high-latitude tail.

**Measure:**

- whether the total pulse has a shoulder, plateau, or two-stage peak;
- whether a two-component temporal decomposition is stable across energy bands;
- whether the lower-energy contribution is temporally associated with the FS prediction.

**Failure signal:** independent pulse components require unrelated start times, arbitrary shapes, or inconsistent ordering.

### T2. Plateau and pulse-width morphology

**Paper prediction:** varying `t_on,1`, `t_off`, and `t_on,4` alters the relative FS/RS widths and peak times. Separated shock-completion times can create plateaus and complex morphology.

**Measure:**

- plateau duration relative to total pulse width;
- time separation between inferred FS and RS peaks;
- whether the same time-ratio parameters explain all energy bands.

**Important:** do not treat every flat peak as proof of two shocks. Compare against standard pulse templates and overlapping single-component alternatives.

### T3. High-latitude-emission tail

**Paper prediction:** after shock crossing, the tail is dominated by high-latitude emission.

**Primary test from the paper:**

```text
(nu F_nu)_pk ∝ nu_pk^3
```

during the decay branch, because the model gives:

```text
(nu F_nu)_pk ∝ T_eff^-3
nu_pk          ∝ T_eff^-1
```

**Measure:**

- fit the decay-phase slope in log peak-flux versus log peak-energy space;
- infer the collision-width parameter `Delta R / R0` using the full model, not only the asymptotic cubic slope;
- check where the decay branch begins relative to the fitted shock-crossing time.

**Extension:** test channel-specific curvature-effect closure relations, but label these as an additional test rather than a result derived in the Letter.

### T4. Hard-to-soft evolution

**Paper prediction:** `nu_pk` decreases monotonically with observer time for both shocks.

**Measure:**

- monotonicity of `E_pk(t)`;
- posterior probability of a negative derivative after onset;
- deviations near pulse overlap;
- whether the FS and RS peaks both obey the same qualitative trend.

**Negative control:** intensity-tracking pulses. These may favor other dissipation physics, including magnetic reconnection.

### T5. Energy-dependent timing

Because the FS and RS dominate different spectral regions, the model can generate energy-dependent pulse shapes.

**Measure:**

- whether the low-energy band peaks closer to the FS peak time;
- whether high-energy bands are more RS-dominated;
- whether observed lags match the fitted EATS model;
- whether pulse width narrows with energy in the predicted manner.

This is a particularly useful way to reduce spectral-component degeneracy.

---

## 4. Spectral tests

### S1. Low-energy break versus low-energy bump

The FS cooling regime changes the observed form.

#### Fast-cooling FS

Expected total shape:

```text
low-energy spectral break + high-energy peak
```

Compare primarily with:

```text
2SBPL
coupled FS+RS
single-zone synchrotron with a cooling break
```

#### Marginally fast-cooling FS

Expected total shape:

```text
subdominant low-energy bump + dominant high-energy peak
```

Compare primarily with:

```text
Band+BB
SBPL+BB
coupled FS+RS
two independent nonthermal components
```

### S2. Spectral-slope consistency

For the paper's simplified synchrotron prescription:

```text
slow/marginal FS low-energy F_nu slope: +1/3
fast-cooling low-energy F_nu slope:     -1/2
high-energy F_nu slope:                 -p/2
```

Convert carefully between `F_nu` slopes and photon indices before comparing with catalog values.

Test whether:

- the low-energy segment is consistent with the assumed FS regime;
- the intermediate segment between FS and RS peaks is reproduced;
- the high-energy slope is consistent with the RS electron index.

### S3. Component ordering

The physical baseline expects:

```text
nu_pk,FS < nu_pk,RS
```

and an RS-dominated high-energy spectral-energy peak.

Impose ordered priors or a hydrodynamic parameterization to avoid label switching.

### S4. Spectral sharpness and photosphere alternative

A true photosphere is expected by the paper to have a sharper peak and harder low-energy photon index.

Quantify rather than judge by eye:

- spectral width;
- curvature;
- low-energy asymptotic index;
- residuals around the low-energy component;
- onset timing relative to the main pulse.

---

## 5. Coupling tests

### C1. Peak-frequency ratio

Use the intrinsic characteristic frequencies:

```text
r_nu = nu_0,FS / nu_0,RS
```

to constrain the ratio of shock strengths:

```text
(Gamma_21 - 1) / (Gamma_34 - 1) = sqrt(r_nu)
```

This gives a ratio, not two absolute strengths.

### C2. Flux-density ratio and radiative-efficiency ratio

With:

```text
r_F = F_0,FS / F_0,RS
```

Equation 7 gives:

```text
epsilon_rad,FS / epsilon_rad,RS
    = r_F * r_nu * (beta_34 / beta_21)
```

Do not drop the beta factor without verifying it.

### C3. Spectral-energy peak ratio

The quantity relevant to energy dominance is approximately:

```text
(nu_0 F_0)_FS / (nu_0 F_0)_RS = r_nu * r_F
```

This can be less than one even when `F_0,FS / F_0,RS > 1`, because the FS peaks at much lower frequency.

### C4. Time-dependent corrections

Do not insert observed time-integrated peaks directly into Equation 7 unless the radial and arrival-time corrections have been included. Prefer fitting the complete model and inferring `nu_0` and `F_0` as latent physical parameters.

---

## 6. Model-comparison set

At minimum compare:

```text
Band
CPL
SBPL
2SBPL
Band + BB
SBPL + BB
single-zone synchrotron
published analytic coupled FS + RS
```

Later extensions:

```text
full-kernel coupled synchrotron
magnetized FS + RS
photosphere + coupled shocks
additional LAT power law
```

All models must use:

- the same detector selection;
- the same background treatment;
- the same time intervals;
- the same response matrices;
- comparable priors;
- the same likelihood definition.

---

## 7. Strong falsification outcomes

The baseline two-shock model is disfavored when one or more of the following remain robust after uncertainty and selection effects are included:

1. The pulse is dominated by intensity tracking rather than hard-to-soft evolution.
2. No coupled parameter set reproduces both timing and spectrum.
3. The inferred frequency and flux ratios violate Equation 7.
4. The required radiative-efficiency ratio is unphysical or inconsistent with the assumed cooling regimes.
5. The inferred FS/RS peak ordering reverses.
6. The low-energy feature turns on substantially before the collision pulse, is much sharper, and has a harder index consistent with a photosphere.
7. The HLE decay track is incompatible with the model.
8. The model requires extreme shell contrast that predicts an unobserved peak-energy ratio.
9. Posterior predictive residuals show systematic structure despite a good scalar fit statistic.
10. Synthetic tests show the data cannot identify the two components; in that case the correct conclusion is non-identifiability, not model confirmation.

---

## 8. Recommended sample design

Use at least three groups:

### Primary sample

Bright, isolated, single pulses with hard-to-soft evolution and sufficient statistics.

### Negative-control sample

Single pulses with clear intensity tracking.

### Complexity-control sample

Multi-pulse or overlapping events, analyzed to quantify how superposition can mimic the two-shock signatures.

This prevents selecting only events already known to resemble the model.

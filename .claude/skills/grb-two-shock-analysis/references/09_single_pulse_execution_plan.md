# Execution plan for the 106 single-pulse GRB project

## 1. Project decision

The immediate priority is to complete one coherent project rather than continue an unbounded literature sweep.

The primary dataset is the existing sample of:

```text
106 single-pulse GRBs
```

The analysis must be completed consistently, pulse by pulse, with temporal and spectral products that can be interpreted empirically and then tested against the coupled internal-shock framework.

Targeted reading continues, but only when it resolves a concrete analysis decision or interpretation.

---

## 2. Central scientific question

Can the observed temporal and spectral diversity of isolated GRB pulses be explained by a hydrodynamically coupled forward-shock plus reverse-shock internal collision?

The strongest version is:

> Can one parameter set reproduce the pulse morphology, energy-dependent timing, time-resolved spectral evolution, low-energy break or bump, high-energy peak, and decay track?

The FS+RS interpretation is a hypothesis, not a sample-selection assumption.

---

## 3. Tiered project design

## Tier 1 — all 106 pulses: uniform empirical catalog

Complete for every pulse:

```text
temporal morphology
multi-band light curves
spectral lag
energy-dependent width
time-integrated spectrum
time-resolved spectral evolution
empirical model comparison
break/bump classification
data-quality and detectability metrics
```

This tier must be publishable even if the physical model implementation takes longer.

## Tier 2 — high-information physical-test subset

Select pulses with:

```text
good statistics
broad energy coverage
stable background
resolved or strongly constrained low-energy structure
hard-to-soft evolution or a clearly measured alternative
minimal overlap
```

Fit the coupled FS+RS model jointly in time and energy.

## Tier 3 — multi-instrument subset

For pulses with LLE/LAT and/or Swift coverage:

```text
extend E_peak and beta constraints
search for additional high-energy components
improve low-energy break coverage
test cross-instrument consistency
```

---

## 4. Master catalog schema

Create one machine-readable master table with one row per pulse.

Suggested columns:

```text
identity:
    grb_name
    trigger_id
    pulse_id
    class_long_short
    redshift
    pulse_start
    pulse_stop

coverage:
    nai_detectors
    bgo_detector
    has_lle
    has_lat
    has_bat
    has_xrt
    energy_min
    energy_max

quality:
    source_counts
    background_counts
    peak_flux
    fluence
    snr_global
    snr_low
    snr_high
    response_quality_flag
    overlap_flag

temporal:
    t_onset
    t_peak
    t_rise
    t_decay
    fwhm
    asymmetry
    plateau_duration
    shoulder_flag
    lag_low_high
    width_energy_index
    hard_to_soft_score
    intensity_tracking_score
    hle_decay_score

spectral integrated:
    preferred_empirical_model
    delta_aic_2sbpl_band
    delta_bic_2sbpl_band
    alpha_band
    beta_band
    epeak_band
    alpha1_2sbpl
    alpha2_2sbpl
    beta_2sbpl
    ebreak
    epeak_2sbpl
    re_break_peak
    bb_kT
    low_component_flux_fraction

detectability:
    break_detection_probability
    hidden_break_min
    hidden_break_max
    classification_detected_hidden_excluded_noninformative

physical:
    two_shock_fit_status
    nu0_fs_nu0_rs
    f0_fs_f0_rs
    shock_strength_ratio
    epsilon_rad_ratio
    delta_r_r0
    fs_rs_fluence_ratio
    physical_classification
```

Use explicit missing-value codes. Do not silently use zero for unavailable quantities.

---

## 5. Temporal analysis module

For each pulse:

1. create background-subtracted or likelihood-modeled light curves;
2. use fixed, documented energy bands;
3. also create adaptive bands around the fitted `E_peak` when useful;
4. fit a standard pulse model, such as a Norris-type profile;
5. measure model-independent quantiles as a robustness check.

Required outputs:

```text
rise time
decay time
FWHM
asymmetry
peak time
onset time
plateau or shoulder
energy-dependent peak shift
spectral lag
width-energy relation
```

### Internal-shock-specific tests

Measure:

```text
whether one or two coupled pulse contributions are required
whether low-energy emission peaks at a different time than the MeV peak
whether a plateau is consistent with separated FS/RS crossing times
whether the decay follows a high-latitude branch
whether E_peak decreases monotonically
whether peak flux versus peak energy approaches the cubic decay track
```

Do not force every pulse into hard-to-soft. Label intensity-tracking pulses as a physically important comparison class.

---

## 6. Spectral analysis module

## 6.1 Time-integrated analysis

Use the full isolated-pulse interval.

Fit:

```text
CPL
Band
SBPL
2SBPL
Band + BB
SBPL + BB
```

Record count-space residuals and parameter covariance.

The time-integrated fit is useful for:

```text
maximum S/N
initial break search
comparison with Toffano et al.
population summary
```

It is not sufficient for physical interpretation.

## 6.2 Time-resolved analysis

Use at least two binning schemes:

```text
constant S/N
Bayesian blocks or pulse-phase bins
```

Track:

```text
E_peak(t)
E_break(t)
alpha(t)
beta(t)
component fluxes
BB kT(t), if relevant
```

Test whether a time-integrated break is:

```text
persistent
transient
created by spectral evolution
created by overlapping intervals
```

## 6.3 Statistical rule

Primary:

```text
PG-statistic / Poisson-appropriate count likelihood
```

Secondary summaries:

```text
Delta AIC
Delta BIC
posterior predictive checks
simulation-calibrated component significance
```

Use `Delta AIC >= 6` as the Toffano replication benchmark for Band versus 2SBPL, not as the only decision criterion.

---

## 7. Hidden-break simulation module

This module is mandatory, not optional.

### For a Band-only pulse

1. use the fitted Band posterior as the observed target;
2. create candidate 2SBPL grids or samples over:
   - `alpha_1`;
   - `alpha_2`;
   - `E_break`;
   - `E_peak`;
   - `beta`;
3. fold through the exact detector responses;
4. simulate source and background counts;
5. refit with Band and 2SBPL;
6. retain cases reproducing the observed Band posterior and model ranking;
7. infer the range of hidden breaks.

### For a detected-break pulse

1. use the fitted 2SBPL posterior;
2. move `E_break` while preserving an explicitly chosen invariant:
   - energy flux;
   - source counts;
   - or physical-model normalization;
3. calculate the break-detection efficiency;
4. determine the pulse-specific relation between `R_E` and recovered `alpha_Band`.

### Population output

Build a detection-efficiency surface:

```math
P(\mathrm{detect\ break} |
E_{\rm break}, E_{\rm peak}, R_E,
\alpha_1,\alpha_2,\beta,
\mathrm{fluence}, \mathrm{response}, \mathrm{background}).
```

Use this surface before comparing detection fractions across classes.

---

## 8. Physical FS+RS module

Do not begin by fitting two arbitrary independent spectral components.

Fit the coupled analytic model with:

```text
shared collision geometry
hydrodynamic FS/RS ordering
linked characteristic frequencies
linked amplitudes
shock-crossing times
EATS evolution
cooling-regime choice
```

Primary outputs:

```text
nu_0,FS / nu_0,RS
F_0,FS / F_0,RS
shock-strength ratio
radiative-efficiency ratio
FS/RS fluence partition
Delta R/R0
```

### Critical mapping calibration

The empirical `E_break/E_peak` from 2SBPL is not automatically equal to the intrinsic FS/RS frequency ratio.

For posterior samples from the physical model:

1. generate count spectra;
2. fit them with 2SBPL;
3. learn the mapping:
   ```text
   physical parameters -> empirical E_break/E_peak
   ```
4. use that mapping to interpret the catalog.

---

## 9. Decision tree for one pulse

### Case A — 2SBPL preferred

Ask:

```text
Is the break robust to background, binning, and detector selection?
Does it persist in time-resolved spectra?
Could FS+RS reproduce both break and temporal evolution?
Could one-zone synchrotron reproduce it?
```

### Case B — Band+BB or SBPL+BB preferred

Ask:

```text
Is the bump temporally earlier and spectrally sharper, as expected for a photosphere?
Can a marginally fast-cooling FS reproduce it?
Can a more flexible nonthermal continuum absorb it?
```

### Case C — Band preferred, alpha_Band > -1

Test a hidden break near `E_peak`.

### Case D — Band preferred, alpha_Band < -1

Test a hidden break near the low-energy boundary.

### Case E — intensity tracking

Treat as a negative or alternative-physics control for the baseline hard-to-soft two-shock model.

### Case F — non-identifiable

Report non-identifiability. Do not force a physical label.

---

## 10. First executable sprint

### Sprint 1 — freeze and audit the sample

- finalize the 106 pulse list;
- define pulse boundaries;
- inventory detectors and LLE/LAT availability;
- flag overlap and background problems;
- create the master table.

### Sprint 2 — pilot ten representative pulses

Choose:

```text
2 clear 2SBPL-like
2 Band+BB-like
2 hard Band-only
2 soft Band-only
1 intensity-tracking
1 LLE/LAT-bright
```

Run the entire empirical and simulation pipeline.

### Sprint 3 — automate and scale

- lock configuration format;
- write unit and regression tests;
- run all 106 pulses;
- generate standard reports;
- review outliers manually.

### Sprint 4 — physical interpretation

Fit the coupled model first to the high-information subset, then expand only where parameters are identifiable.

---

## 11. Main-paper structure

A coherent first paper can be:

### Results first

1. the 106-pulse sample and data-quality map;
2. temporal diversity of isolated pulses;
3. empirical spectral model distribution;
4. detected and hidden low-energy breaks;
5. relation between break morphology and pulse evolution;
6. physical FS+RS tests on the constrained subset.

### Interpretation

- synchrotron cooling;
- coupled FS+RS shocks;
- photospheric alternatives;
- intensity tracking and magnetic alternatives;
- instrumental selection effects.

### Methods later

- event selection;
- background and responses;
- temporal measurements;
- spectral models;
- likelihood and model comparison;
- forward simulations.

This ordering follows the preference to lead with observations, significance, and physical implications.

---

## 12. Completion rule

The project is complete when:

```text
all 106 pulses have a standard report
the master catalog is frozen
the pipeline is reproducible
detected and hidden breaks are simulation-calibrated
temporal and spectral results are linked
the physical subset has an honest supported/disfavored/non-identifiable label
the manuscript figures and tables are generated from the frozen catalog
```

New literature should be added only when it changes one of these decisions or helps interpret a specific result.

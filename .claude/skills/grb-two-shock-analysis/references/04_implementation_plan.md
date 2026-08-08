# Implementation plan

## 1. Principle: reproduce before extending

The first software target is the published analytic model, not a generalized physical model.

The source paper combines:

- hydrodynamically derived FS and RS properties;
- a normalized Band-shaped comoving spectrum with synchrotron-motivated slopes;
- EATS integration;
- time-dependent sum of the two shock contributions.

Only after reproducing the paper should the project replace the analytic spectral kernel with a full synchrotron calculation or add magnetization.

---

## 2. Recommended software layers

### Layer A: hydrodynamic state

Suggested object:

```python
HydroState(
    u1,
    u4,
    t_on1,
    t_off,
    t_on4,
    luminosity=None,
    redshift=None,
)
```

Derived quantities:

```text
a_u
Gamma_1, Gamma_4
R0
downstream u and Gamma
u_FS, u_RS
Gamma_21, Gamma_34
beta_21, beta_34
t_FS, t_RS
R_f,FS, R_f,RS
g_FS, g_RS
rarefaction completion flags
```

Validate the allowed shell-duration ratio and explicitly report if rarefaction stalls a shock.

### Layer B: radiation state

Suggested object:

```python
RadiationState(
    p=2.5,
    epsilon_rad_FS=0.5,
    epsilon_rad_RS=1.0,
    cooling_FS="marginal",
    cooling_RS="fast",
)
```

Baseline spectral slopes:

```text
FS marginal: b1 = +1/3
FS fast:     b1 = -1/2
RS fast:     b1 = -1/2
all:         b2 = -p/2
```

### Layer C: normalized spectral function

Implement Equation 6 exactly:

```python
S(x, b1, b2)
```

Tests:

- continuity at `x_b`;
- normalization at the spectral peak;
- asymptotic slopes;
- valid behavior near `b1 = -1`;
- no negative or nonfinite values;
- vectorized evaluation.

### Layer D: EATS flux integral

Implement Equation 5 for each shock:

```python
F_nu_i(nu, T, hydro, radiation, normalization)
```

Requirements:

- correct `y_min` and `y_max`;
- separate shock-front Lorentz factor from downstream Lorentz factor;
- stable numerical integration near boundaries;
- high-latitude branch after `T_f,i`;
- caching of geometry terms;
- unit-safe input/output.

### Layer E: two-shock model

```python
F_total(nu, T) = F_RS(nu, T) + F_FS(nu, T)
```

Impose physical ordering through the hydrodynamics rather than arbitrary component labels.

### Layer F: instrument interface

Wrap the photon spectrum for threeML/astromodels and forward-fold it through:

- GBM NaI responses;
- GBM BGO responses;
- LAT/LLE when appropriate;
- Swift instruments for selected low-energy coverage.

Do not compare unfolded spectra as the primary likelihood analysis.

---

## 3. Tiered fitting models

### Tier 0: paper reproduction

Fix the fiducial values and reproduce:

- Table 1;
- Figure 2 light curves and time-resolved spectra;
- Figure 3 peak-flux and peak-energy evolution;
- Figure 4 time-integrated spectra.

This is the mandatory acceptance test.

### Tier 1: coupled analytic fit

Use a compact parameterization close to the paper:

```text
overall normalization
nu_0,RS
T_0,RS or global time scale
t_on1 / t_off
t_on4 / t_off
u1
a_u
FS cooling regime
possibly epsilon_rad,FS / epsilon_rad,RS
```

Derive the FS quantities using hydrodynamic coupling and Equation 7.

This tier is the best first model for real data.

### Tier 2: flexible microphysics

Allow selected differences between FS and RS:

```text
epsilon_e
epsilon_B
xi_e
p
```

Use strong priors and only add parameters when synthetic tests show they are identifiable.

### Tier 3: full synchrotron kernel

Replace the Band-shaped kernel with integration over electron distributions.

Possible distributions:

- power law;
- Maxwellian plus tail;
- broken power law.

Keep the hydrodynamic coupling.

### Tier 4: magnetized shocks

Introduce shell magnetization `sigma_1` and `sigma_4`, modifying:

- jump conditions;
- shock formation and strength;
- dissipation efficiency;
- post-shock magnetic field;
- particle acceleration assumptions.

This is a separate model extension. Do not mix it into baseline verification.

---

## 4. Parameter constraints and priors

Recommended constraints:

```text
u4 > u1
t_on1 > 0
t_off > 0
t_on4 > 0
nu_0,FS < nu_0,RS
0 <= epsilon_rad <= 1
R_f,i >= R0
p > 2 for the baseline formula
```

Prefer log parameters for positive scales.

Avoid independently sampling both component peak frequencies and both fluxes without coupling; that recreates an arbitrary two-component fit.

---

## 5. Numerical validation suite

### 5.1 Unit tests

- Lorentz/proper-speed conversions.
- Collision radius.
- shock-strength equations.
- Equation 7 ratios.
- EATS arrival-time mapping.
- `S(x)` continuity and slopes.
- high-latitude asymptotics.
- time-integrated approximation.
- rarefaction boundary behavior.

### 5.2 Regression tests

Store digitized or generated reference curves for Figures 2–4 and compare within tolerance.

### 5.3 Synthetic parameter recovery

Generate source spectra and event counts with known parameters, fold through realistic responses, add background, and recover:

```text
time ratios
nu_0 ratio
F_0 ratio
shock-strength ratio
radiative-efficiency ratio
Delta R / R0
```

Map where the parameters become non-identifiable.

### 5.4 Model-confusion simulations

Simulate from:

- Band;
- 2SBPL;
- Band+BB;
- one-zone synchrotron;
- coupled FS+RS;
- photosphere+nonthermal.

Fit all candidate models and measure false classification rates.

---

## 6. Real-data workflow

1. Select an isolated pulse.
2. Choose detectors and validate response coverage.
3. Fit background.
4. Create multi-band light curves.
5. Measure temporal morphology independently of the physical fit.
6. Define time bins with at least two robust schemes.
7. Fit empirical spectral models.
8. Fit the coupled analytic model.
9. Perform joint or hierarchically linked time-resolved inference.
10. Run posterior predictive checks in count space.
11. Compare predictive performance.
12. Produce the standard burst report.

---

## 7. Joint likelihood strategy

### Minimum viable approach

Fit each time-resolved spectrum while sharing global hydrodynamic parameters and allowing the model's time evolution to determine component peaks and amplitudes.

### Preferred approach

Use a joint event/count likelihood over time and energy:

```math
\log L_{\rm total}
=
\sum_{\rm detector}
\sum_{\rm time\ bin}
\sum_{\rm channel}
\log P(n | s_{\rm FS+RS} + b).
```

This directly uses the temporal and spectral information that breaks component degeneracy.

### Practical compromise

If full 2D event modeling is too costly:

- fit fine time bins;
- tie hydrodynamic parameters across bins;
- derive predicted temporal tracks;
- compare the resulting light curves with independent temporal measurements.

---

## 8. Performance considerations

- Precompute dimensionless EATS grids.
- Vectorize frequency and time evaluation.
- Cache hydrodynamic quantities.
- Interpolate validated grids during sampling.
- Keep a slow exact path for regression tests.
- Profile before approximating.
- Record approximation errors relative to the exact integral.

---

## 9. Deliverables

### Software

- `SynchrotronMicrophysics`;
- `TwoShockSynchrotron`;
- reproducible figure-generation scripts;
- simulation and recovery suite;
- Fermi analysis pipeline;
- documented parameter conventions.

### Scientific

- empirical versus physical model comparison;
- pulse-level observables catalog;
- inferred FS/RS fluence partition;
- shock-strength ratio;
- radiative-efficiency ratio;
- `Delta R / R0`;
- clear list of successes, failures, and non-identifiable cases.

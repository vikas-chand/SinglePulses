# Li & Zhang (2021) HLE Reproduction Workflow

## Goal

Reproduce the source analysis exactly before introducing structured jets, FS+RS emission, or statistical upgrades.

## Recommended benchmark pair

```text
GRB 090620400:
    reported as consistent with constant-Gamma HLE

GRB 160530667:
    reported as consistent with acceleration
```

## Reproduction stages

### 1. Retrieve inputs

```text
TTE
responses
catalog localization
detectors
source interval
background intervals
```

### 2. Reproduce the Bayesian blocks

Store:

```text
algorithm implementation
fitness function
false-positive prior
background handling
block boundaries
S value per block
```

### 3. Reproduce spectral fits

For every \(S>15\) block:

```text
Band fit
energy flux
fit statistic
parameter covariance/posterior
```

### 4. Reproduce count-light-curve morphology

```text
time resolution
FRED fit
BKPL comparison
peak decision
peak discrepancy
```

### 5. Define phases

```text
Phase I:
    peak to final S>15 block

Phase II:
    final three S>15 blocks
```

### 6. Reproduce temporal fits

Return:

```text
alpha_I
alpha_II
AIC/BIC
residuals
```

### 7. Reproduce PL spectral fits

Return:

```text
beta_I
beta_II
DIC/pDIC
posterior samples
```

### 8. Reproduce closure classification

Calculate:

\[
\Delta_{\rm HLE}=\alpha-(2+\beta).
\]

### 9. Reproduce CPL fits

For each candidate time bin return:

```text
N0
Gamma_hat
E_c
F_nu,c
posterior/covariance
```

### 10. Reproduce the three model tests

```text
E_c(t)
F_nu,c(t)
F_nu,c versus E_c
```

### 11. Reproduce radius scaling

Keep:

```text
observed HLE duration
redshift source
bulk Lorentz-factor assumption
radius as a scaling relation
```

## Acceptance criteria

```text
block boundaries agree within one native time bin
peak and phase boundaries match
alpha/beta values agree within reported uncertainty
closure classification matches
CPL evolution figure is visually and numerically recovered
radius table is reproduced
```

## Robustness layer after reproduction

```text
vary peak
vary t0
vary Phase II length
vary S threshold
vary background
vary spectral model
propagate full posterior
```

# Reproduction Workflow — Bayesian Blocks and \(T_{90}\) in Qin et al. (2013)

## Goal

Reproduce the Qin et al. count-space \(T_{90}\) calculation before introducing improved background or response treatments.

## Benchmark events

```text
GRB 091010:
    bright case; verify probable caption typo

GRB 090126B:
    weak case

GRB 090227B:
    short case
```

## Stage 1 — retrieve inputs

```text
TTE data
NaI detector used
response files
trigger time
source interval
two background interval pairs
```

## Stage 2 — light curves

Reproduce:

```text
64 ms binning
all-band and sub-band curves
linear background fit
higher-order comparison
```

## Stage 3 — Bayesian Blocks

Record:

```text
input data type:
    events, counts, rates, or background-subtracted rates

fitness function
prior or ncp_prior
false-positive probability
block-edge convention
block-height convention
software/version
```

## Stage 4 — Figure 1

Overlay:

```text
raw/source counts
background model
background-subtracted curve
Bayesian-block steps
background selections
```

Audit apparent dips and broad blocks.

## Stage 5 — fluence quantiles

For every block representation:

```text
integrate count fluence
calculate t5
calculate t95
calculate T90
```

## Stage 6 — source Monte Carlo

Replicate:

```text
1000 mock curves
Gaussian fits to t5 and t95
quadrature T90 error
```

## Stage 7 — improved Monte Carlo

For each realization calculate:

\[
T_{90}^{(j)}=t_{95}^{(j)}-t_5^{(j)}.
\]

Compare:

```text
source quadrature uncertainty
direct T90 distribution
covariance term
coverage on injected simulations
```

## Stage 8 — catalog comparison

Compare with GBM photon-fluence \(T_{90}\):

```text
one-to-one plot
residual plot
outlier table
duration dependence
angle/slew dependence
```

## Stage 9 — synthetic validation

Inject known source intervals and test:

```text
edge recovery
soft-tail recovery
false blocks
missed blocks
T90 bias
uncertainty coverage
```

## Acceptance criteria

```text
Figure-1 block edges reproduced or discrepancy explained
source T90 values recovered within quoted uncertainty
catalog comparison recreated
direct-MC method validated
all priors and visual choices logged
```

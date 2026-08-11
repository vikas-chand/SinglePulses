> ⚠ **PARKED — reference only (Two_Breaks, 2026-08-09).** This module derives Gamma, R_ph and
> sigma *downstream of identifying the BB as photospheric* — which principle 15 of this same
> skill forbids assuming. For this project it is **registry #42 territory, parked** until the
> empirical shape census is done. Do NOT run it as part of the walkthrough; read it when #42
> starts.

# Hybrid-jet inference and BB-origin comparison workflow

## Objective

Convert a statistically supported low-energy component into outflow constraints without hiding the dependence on spectral decomposition, launch radius, efficiency, or framework.

## Stage 0 — establish whether a component exists

Fit under identical data treatment:

```text
Band
SBPL
2SBPL
Band + BB
SBPL + BB
Band/SBPL + multicolor BB
single-zone synchrotron
coupled FS + RS
```

Use a source-plus-background count likelihood. Calibrate added-component significance through response-folded null simulations.

Terminal classifications:

```text
thermal-shaped component detected
nonthermal low-energy structure detected
component allowed but unresolved
component excluded over a stated range
non-identifiable
```

## Stage 1 — temporal discrimination

Measure for the lower-energy component:

```text
onset offset relative to the main continuum
peak-time offset
width
spectral sharpness
kT or characteristic-frequency evolution
flux-fraction evolution
association with a precursor
```

Interpretive tests:

```text
photosphere:
    potentially earlier, sharper, harder at low energy

FS component:
    tied to the same collision and to the RS temporal evolution

spectral-evolution artifact:
    disappears in sufficiently fine bins
```

## Stage 2 — conditional hybrid-jet inference

Only for posterior samples in which a photospheric component is supported, evaluate:

```text
H2013/G2013
G2015
```

Required sampled nuisance parameters:

```text
R0
f_NT
f_gamma
cross-normalization
redshift, if uncertain
cosmology, if needed
```

Do not quote a single value when the result is a parameter surface.

## Stage 3 — model-dependence comparison

Repeat outflow inference under every viable spectral decomposition that includes a photospheric component.

Report:

```text
within-model statistical uncertainty
between-model systematic variation
prior sensitivity
regime changes
undefined quantities
```

## Stage 4 — physical mechanism classification

Use explicit rules and label them as framework-dependent:

```text
sigma at emission radius below threshold:
    internal shocks compatible

sigma at emission radius above threshold:
    magnetic reconnection compatible
```

Do not infer the radiation mechanism from `sigma_0` alone; use the magnetization at the relevant dissipation radius when the framework permits it.

## Stage 5 — reproducibility outputs

For each burst, save:

```text
observed-posterior samples
assumed-parameter samples
regime classification
outflow posterior table
parameter maps
mechanism classification
assumption ledger
model-dependence summary
```

## Acceptance tests

1. Reproduce the published GRB 130518A scaling results.
2. Recover synthetic injected parameters.
3. Confirm unit consistency.
4. Confirm regime boundaries continuously across parameter grids.
5. Verify that quantities unavailable in a regime are not silently extrapolated.
6. Demonstrate how an FS-like synthetic bump biases hybrid-jet inference when fitted as a BB.

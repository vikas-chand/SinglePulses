# Claude Code Handoff — Qin et al. (2013)

## Objective

Reproduce Qin et al.'s energy-dependent \(T_{90}\) analysis, audit its Bayesian-block and mixture-model implementation, and integrate it into the response-corrected duration–hardness project.

## Read first

```text
references/22_qin_2013_energy_dependent_t90.md
references/23_response_corrected_duration_hardness_project.md
references/24_bayesian_blocks_t90_audit.md
templates/grb_duration_hardness_report.md
```

## First benchmark

Reproduce Figure 1 for:

```text
GRB 091010
GRB 090126B
GRB 090227B
```

Do not assume the caption event ID is correct.

## First deliverable

One reproducible run containing:

```text
64 ms light curve
background fits
Bayesian-block configuration
block overlay
t5/t95/T90
source quadrature uncertainty
direct Monte Carlo T90 uncertainty
comparison with GBM catalog T90
assumption ledger
```

## Mandatory source audits

```text
1. Resolve GRB 091010 versus 090910.
2. Resolve HR denominator 25–50 versus 50–100 keV.
3. Re-run the soft-band KMM tests.
4. Resolve 1:6.5 versus 1:5 short/long ratio.
5. Determine the exact block fitness and prior.
6. Do not call the Figure-1 blocks wrong before reproduction.
```

## Modules

```text
duration_hardness/
    backgrounds.py
    bayesian_blocks.py
    fluence_quantiles.py
    monte_carlo.py
    photon_history.py
    hardness.py
    mixture_models.py
    response_transfer.py
    diagnostics.py
```

## Do not

```text
do not mix count and photon fluence silently
do not assume t5 and t95 are independent
do not treat KMM P-values as self-explanatory
do not use an unspecified hardness ratio
do not conclude physical bimodality is absent from energy dependence alone
```

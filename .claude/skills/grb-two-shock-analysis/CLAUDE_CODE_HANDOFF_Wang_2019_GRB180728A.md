# Claude Code Handoff — Wang et al. (2019), GRB 180728A Prompt Emission

## Objective

Reproduce and audit the precursor/main-spike spectroscopy and weak-blackbody model selection for GRB 180728A.

## Read first

```text
references/20_wang_2019_grb180728a_prompt_emission.md
references/21_thermal_component_model_selection.md
templates/grb_thermal_component_report.md
```

## Exact intervals

```text
precursor:
    -1.57–1.18 s

main A:
    8.72–10.80 s

main B:
    10.80–12.30 s

main C:
    12.30–22.54 s

combined early main:
    8.72–12.30 s
```

## Models

```text
PL
CPL
Band
PL+BB
CPL+BB
Band+BB
```

## First deliverable

A reproducible report containing:

```text
light curve and Bayesian blocks
spectral fits
fit-statistic convention
AIC/BIC and deltas
posterior diagnostics
thermal evolution
R_BB and velocity posterior
Type I/II injection-recovery design
assumption ledger
```

## Critical checks

```text
1. Verify whether Table 3 stores -logL rather than logL.
2. Reproduce the near-perfect tie between CPL+BB and Band+BB
   for 10.80–12.30 s.
3. Confirm that CPL is preferred in 12.30–22.54 s.
4. Do not encode “AIC non-nested, BIC nested” as a rule.
5. Do not call the BdHN interpretation data-unique.
6. Do not expand to a population before one event reproduces.
```

# Claude Code Handoff — Li & Zhang (2021)

## Objective

Integrate Li & Zhang's high-latitude-emission method into the GRB single-pulse program, reproduce it exactly, and then test whether structured jets or coupled FS+RS emission can mimic its acceleration signatures.

## Do first

```text
1. Read:
   references/17_li_2021_high_latitude_curvature.md
   references/18_structured_jet_hle_project.md
   references/19_li_2021_hle_reproduction_workflow.md

2. Cross-match the paper's 24 GRBs with the 106-pulse catalog.

3. Select two benchmarks:
   090620400
   160530667

4. Reproduce the source pipeline before modifying it.
```

## Implementation modules

```text
hle/
    sample.py
    bayesian_blocks.py
    significance.py
    pulse_models.py
    phase_selection.py
    temporal_fit.py
    spectral_pl.py
    spectral_cpl.py
    closure.py
    radius.py
    structured_jet.py
    diagnostics.py
```

## Mandatory tests

```text
top-hat constant-Gamma simulation recovers alpha = 2 + beta
identity-response timing test
source benchmark reproduction
three-bin Phase II sensitivity
t0 sensitivity
peak-time sensitivity
redshift/Gamma radius scaling
```

## Do not

```text
do not call alpha > 2 + beta unique proof of magnetic acceleration
do not fix unknown redshift and Gamma without labeling assumptions
do not hide visual peak decisions
do not mix count-space and photon-space peak times silently
do not expand to all 106 before benchmark reproduction passes
```

## First deliverable

One reproducible notebook/CLI run for GRB 090620400 producing:

```text
Bayesian blocks
FRED fit
Phase I/II
alpha–beta closure point
CPL time evolution
F_nu,c–E_c plot
radius scaling
assumption ledger
```

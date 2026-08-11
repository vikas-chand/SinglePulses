# Detector-quality and LAT photon-association checklist

## GBM detector QA

For every candidate detector, record:

```text
viewing angle
spacecraft blockage / occultation flags
energy range used
response version
background fit quality
cross-normalization
residual trend by model
fit result with and without detector
final decision and rationale
```

A residual-based exclusion requires a repeatable detector-specific pattern and a plausible instrument/geometric cause.

## Galactic-field QA for LAT

Record:

```text
galactic coordinates
ROI
source-model radius
catalog version
extended sources
diffuse templates
event class / type
IRFs
zenith cut
time range
energy range
```

## `gtsrcprob` protocol

1. Fit the relevant interval with a complete source and background model.
2. Save the fitted XML/model.
3. Run `gtsrcprob` using that model.
4. Store every event's:
   - time;
   - energy;
   - angular separation;
   - source probability;
   - probabilities for major background/source alternatives.
5. Recompute if the interval or spectral model changes materially.
6. Do not convert probability thresholds into hard event cuts unless the rule is predeclared and tested.
7. For extremely sparse bins, report that event-level probabilities are model-dependent and may be unstable.

## Prompt versus afterglow question

When LAT photons continue after GBM fades:

```text
fit prompt-only hypothesis
fit prompt + additional power law
fit early-afterglow hypothesis
compare temporal onset and decay
check consistency with GBM extrapolation
```

Do not force one broadband component across GBM and LAT merely because the data are analyzed jointly.

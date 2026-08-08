# Burst analysis report

## 1. Identification

```text
Burst:
Pulse:
Trigger:
Redshift:
Data version:
Analyst/code commit:
Date:
```

## 2. Data selection

```text
Detectors:
Energy ranges:
Source interval:
Background intervals:
Response files:
Excluded channels:
Cross-calibration constants:
```

## 3. Pulse morphology

| Quantity | Full band | Low band | Mid band | High band |
|---|---:|---:|---:|---:|
| Onset | | | | |
| Peak time | | | | |
| Rise time | | | | |
| Decay time | | | | |
| FWHM | | | | |
| Asymmetry | | | | |
| Plateau duration | | | | |
| Post-peak slope | | | | |

Additional notes:

- Shoulder or double peak:
- Spectral lag:
- Width-energy relation:
- Evidence of overlapping pulses:

## 4. Time binning

Describe all schemes tested and justify the primary one.

## 5. Empirical spectral fits

| Time bin | Model | E_pk | Low slope | High slope | Extra component | Statistic | Notes |
|---|---|---:|---:|---:|---|---:|---|

## 6. Coupled two-shock fit

### Fitted parameters

| Parameter | Posterior median | Credible interval | Prior | Status |
|---|---:|---:|---|---|

### Derived parameters

| Quantity | Value | Uncertainty | Equation | Caveat |
|---|---:|---:|---|---|
| `nu_0,FS/nu_0,RS` | | | Eq. 7 | |
| shock-strength ratio | | | Eq. 7 | |
| `F_0,FS/F_0,RS` | | | Eq. 7 | |
| `epsilon_rad,FS/epsilon_rad,RS` | | | Eq. 7 | retain beta factor |
| `Delta R/R0` | | | peak track | |
| FS/RS fluence ratio | | | model integral | |

## 7. Temporal predictions

- Predicted FS peak time:
- Predicted RS peak time:
- Observed low/high-energy peak times:
- Hard-to-soft test:
- Decay-phase cubic peak-track slope:
- HLE onset:
- Plateau/shoulder prediction:
- Residual temporal structure:

## 8. Photosphere comparison

- Earlier precursor present:
- Low-energy feature onset:
- Spectral width:
- Low-energy index:
- Band+BB predictive performance:
- FS+RS predictive performance:
- Is a real photosphere still allowed:

## 9. Model comparison

Use `model_comparison_matrix.md`.

## 10. Robustness tests

- Background:
- Detector selection:
- Energy cuts:
- Time binning:
- Priors:
- Cross-calibration:
- Null simulations:
- Synthetic recovery:
- Additional LAT power law:

## 11. Conclusion classification

Choose one:

```text
Supported
Disfavored
Non-identifiable
Mixed / photosphere + shocks
Requires model extension
```

Explain the classification in one paragraph.

## 12. Falsification statement

State the strongest observation that could overturn the conclusion.

## 13. Open issues and next action

-

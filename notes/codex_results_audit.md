# Independent adversarial audit — consensus catalog

## Bottom line

I independently reimplemented the requested statistics from
`clean_sample_all_models_consensus.ecsv`; I did not import or execute
`scripts/31_draft_numbers.py`. The catalog has 974 unique `(TRIGGER, BLOCK)` rows
from 106 bursts after `BLOCK >= 0` (all input rows pass that filter).

The curvature arithmetic is reproducible, but two paper-level interpretations are
not secure:

1. **POSSIBLE_BUG — Ep–kT definition mismatch.** The requested same-fit Band+BB
   correlation is Spearman rho = **0.2943** (`n=666`), not 0.8099. The pipeline's
   0.8099 value uses standalone `BAND_EP` plus an LRT-selected kT drawn from either
   Band+BB or CPL+BB (`n=217`). This is a different, significance-conditioned,
   mixed-model estimand.
2. **The 33.0% two-break result is exact but burst-clustered.** Two bursts supply
   22/35 = **62.9%** of the numerator. It is defensible as a block-weighted catalog
   statistic, not as an unqualified population fraction.
3. **The primary nu_m–nu_c fit is not a decisive-two-break fit.** It uses 455 fits
   with valid ordered DSBPL breaks. Restricting to the 35 genuine `dAIC>10` cases
   changes the D'Agostini slope from **0.528** to **0.754**.

## Headline-number reproduction and diff

| Quantity | Independent result | Pipeline JSON | Assessment |
|---|---:|---:|---|
| Blocks with curvature test | 853 | 853 | Exact |
| `dAIC>6`: two-break / selected | 36/161 = 0.223602 | 36/161 = 0.223602 | Exact |
| `dAIC>10`: two-break / selected | 35/106 = 0.330189 | 35/106 = 0.330189 | Exact |
| `dAIC>=10` | 35/106 = 0.330189 | Not stored | Same as strict `>`; no row equals 10 |
| Band+BB Ep–kT Spearman | **0.294263**, `n=666` | **0.809941**, `n=217` | **POSSIBLE_BUG:** delta rho = -0.515678, delta n = +449 |
| Band+BB Ep–kT Pearson | 0.220330, `n=666` | Not stored | Newly computed |
| nu_m–nu_c D'Agostini slope | 0.528435 +/- 0.042253 | 0.528435 +/- 0.042262 | Match; error delta -8.64e-6 is Hessian noise |
| nu_m–nu_c intrinsic scatter | 0.336357 dex, `n=455` | 0.336357 dex, `n=455` | Match within 3.2e-9 |
| Band alpha median | -0.708541, `n=746` | -0.708541, `n=746` | Exact |
| Band alpha fraction > -2/3 | 0.447721 | 0.447721 | Exact |

The validity-gated model census also matches exactly: CPL 202, SBPL 200, Band
166, Band+BB 158, CPL+BB 130, DSBPL 95 (951 total). A literal counter of the
catalog column is instead CPL 213, SBPL 203, Band 167, Band+BB 159, CPL+BB 136,
DSBPL 96, because 23 rows carry an invalid fallback winner.

### Ep–kT anchor and selection tests

Using the requested `BANDBB_VALID` and finite `BANDBB_EP`, `BANDBB_KT` definition:

- Full sample: Pearson r = 0.220330; Spearman rho = 0.294263 (`n=666`).
- Drop `bn130427324`: r = 0.203131; rho = 0.251804 (`n=603`). The rho fall is
  only 0.042459.
- Among 65 bursts with at least four pairs, 37 have positive rho and only 13 have
  a significant positive correlation at p<0.05.
- Trigger-centered log-energy Spearman rho is 0.2565.

I also reconstructed what `scripts/31` actually does. It reproduces the JSON
exactly: rho = 0.809941 (`n=217`), falling only to 0.790883 (`n=176`) after
removing `bn130427324`. Thus **0.81 is not primarily anchor-dominated**. It is
primarily definition/selection-driven: even the same-fit Band+BB pair rises from
rho = 0.2943 over all valid fits to 0.7459 after imposing Band+BB LRT>=14.

### nu_m–nu_c definition and sensitivities

The pipeline maps `DSBPL_XB -> nu_c` and `DSBPL_XP -> nu_m`, fitting
`log10(XP) = m log10(XB) + c` with variance
`sigma_sc^2 + sigma_y^2 + m^2 sigma_x^2`. The primary set requires
`DSBPL_VALID` and `0 < XB < XP`; it does **not** require `XB>=15 keV` or a decisive
DSBPL preference. There are 460 break pairs, but five zero `XP_ERR` values leave
455 in the D'Agostini fit.

| Subset | Fit n | Slope | Intrinsic scatter (dex) |
|---|---:|---:|---:|
| Primary valid/ordered | 455 | 0.528435 +/- 0.042253 | 0.336357 |
| Both relative errors <1 | 354 | 0.671370 +/- 0.036914 | 0.327007 |
| `XB>=15 keV` | 348 | 0.600685 +/- 0.048672 | 0.319463 |
| DSBPL LRT>=14 | 59 | 0.697172 +/- 0.087182 | 0.301942 |
| LRT>=14 and DSBPL curvature winner | 36 | 0.779508 +/- 0.086261 | 0.249928 |
| Genuine DSBPL winner with `dAIC>10` | 35 | 0.753705 +/- 0.089366 | 0.249638 |

The stored primary slope is numerically correct, but a paper description implying
that it characterizes decisive two-break spectra would be wrong. Also, 109/460
primary pairs have `XB<15 keV`; seven remain in the 35-bin headline subset.

## Fit-quality pathology scan

### Bounds and validity gate

“Railed” below means within 0.1% of a fitted shape-parameter bound, exactly matching
the fitter's validity gate. “Pegged” means within 1e-6 of the bound span.

| Model | Status OK | Valid | Railed | Pegged |
|---|---:|---:|---:|---:|
| BAND | 964 | 746 | 218 | 123 |
| CPL | 932 | 849 | 83 | 20 |
| SBPL | 973 | 753 | 220 | 78 |
| DSBPL | 968 | 460 | 432 | 186 |
| BANDBB | 974 | 666 | 308 | 144 |
| CPLBB | 974 | 770 | 204 | 57 |

- 640/974 blocks across 105/106 bursts contain at least one railed alternative;
  372 blocks across 97 bursts contain a machine-pegged alternative.
- DSBPL has `XB>=XP` in 160 blocks. Parameter rails include `DSBPL_XB` 134,
  `DSBPL_XP` 155, `BANDBB_KT` 61, and `CPLBB_KT` 75.
- Recomputing `VALID` from status, bounds, and DSBPL ordering gives **zero
  mismatches** for every model. No officially railed fit is marked valid. The
  gate therefore quarantines these failures as designed; the failures are
  widespread rather than confined to a few bursts.

### Nested LRT failures

| Nested LRT | Negative | `<-1` | `<-10` | Minimum |
|---|---:|---:|---:|---:|
| Band+BB vs Band | 38 | 5 | 3 | -96.84 |
| CPL+BB vs CPL | 41 | 7 | 3 | -103.86 |
| DSBPL vs SBPL | 63 | 35 | 10 | -243.36 |

Overall, 135 blocks in 71 bursts have at least one negative nominally nested LRT.
Every stored LRT exactly equals the relevant N2LL difference, so this is an
optimizer/convergence pathology, not a bookkeeping error. No negative-LRT child
is a curvature winner, so these failures do not directly create the 35 two-break
cases. They should still be refit or invalidated.

The nested gates do not require a valid parent. Among the 106 `dAIC>10` blocks,
11/42 Band+BB winners have invalid Band parents, and 2/36 DSBPL winners have
invalid SBPL parents. One of the latter (`bn130427324`, block 59) is in the 35-bin
genuine numerator.

### BEST_AIC and uncertainty failures

- For all 951 rows with at least one valid finite AIC, `BEST_AIC_MODEL` agrees
  with the valid-model AIC argmin. AIC is exactly `N2LL+2k` for every finite fit.
- **POSSIBLE_BUG:** 23 blocks in 15 bursts have no valid model, but the fitter
  assigns an invalid fallback winner instead of `INCONCLUSIVE`.
- The validity gate changes the raw ungated AIC winner in 150 rows.
- Symmetric errors are never negative or nonfinite on status-OK fits, but 77
  blocks have at least one exactly zero error. Ten otherwise-valid declared
  winners are affected. `bn150202999`, `bn150902733`, and `bn130518580` provide
  39/77 = 50.6% of the zero-error blocks.
- 236 blocks have at least one valid model whose energy/break/kT error is at least
  as large as the estimate. This affects 42 valid declared winners in 30 bursts;
  one winning `CPLBB_XC` error exceeds the estimate by more than 10x.
- MINOS failed for 154 valid declared winners. At the model level, 305/666 valid
  Band+BB fits and 419/770 valid CPL+BB fits lack MINOS errors.
- Sixteen blocks have sign-inverted MINOS intervals; 11 occur on valid fits, but
  none is the declared winner.

These uncertainty failures are not part of `M_VALID`. They therefore need a
separate quality flag before parameter-distribution or correlation claims.

## Robustness verdict

The strict and inclusive threshold results are identical: 35/106 = 33.0%.
Threshold-edge arithmetic is not the problem; burst weighting is.

- `bn130427324`: 15/35 genuine cases and 30/106 selected blocks.
- `bn160625945`: 7/35 genuine cases and 10/106 selected blocks.
- Remove `bn130427324`: 20/76 = 26.3%.
- Remove both leading bursts: 13/66 = 19.7%.
- Only 10 of the 31 bursts represented in the denominator contribute any genuine
  two-break block. The equal-trigger mean is 21.8% and the median is zero.
- A descriptive trigger-resampled 95% interval is approximately 14.1%–44.4%.

The prompt's “22 DSBPL blocks” for `bn130427324` refers to raw DSBPL best-model
labels, not the final genuine definition; only 15 survive the curvature-winner,
LRT, and `dAIC>10` gates.

**Verdict:** quote 33% only as a block-weighted descriptive fraction and accompany
it with trigger-clustered/burst-level sensitivity. Do not quote rho=0.81 as the
global Band+BB Ep–kT relation. It is not anchor-dominated, but it is a different,
selection-conditioned statistic.

## Fix before publication

1. Choose and document one Ep–kT estimand; pair parameters from the same composite
   fit and state any LRT selection explicitly.
2. Write `INCONCLUSIVE` when no model is valid.
3. Require valid parent and child fits for nested LRT claims; enforce child
   `N2LL <= parent N2LL + tolerance`, otherwise refit/invalidate.
4. Add uncertainty-quality flags for zero errors, MINOS failures/sign inversions,
   and energy-scale errors at least as large as their estimates.
5. Restrict the nu_m–nu_c claim to decisive, error-constrained, boundary-clean
   DSBPL fits and report the sensitivity slopes above.
6. Use trigger-clustered uncertainty and burst-level weighting for the two-break
   population claim.

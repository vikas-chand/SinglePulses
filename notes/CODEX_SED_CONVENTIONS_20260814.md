# CODEX audit — νFν/SED conventions versus XSPEC and threeML

Date: 2026-08-14  
Scope: `scripts/41c_paper_sed.py` and the two regenerated `bn081125496` demonstration PNGs  
Mode: advisory and read-only, except for this report

## VERDICT — DO NOT SIGN OFF

**DO NOT SIGN OFF** on “41c's conventions are correct and rooted in XSPEC/threeML, subject to the listed fixes” in its present form.

The core XSPEC ratio-unfolding construction is substantially right: XSPEC multiplies the plotted data by `unfoldedModel/foldedModel`, and `eeufspec` multiplies by the product of the group edges. XSPEC's `unfoldedModel` is a continuous, group-integrated photon model divided by group width, not a channel-weighted average. Thus 41c chose the right mathematical numerator.

There are, however, sign-off blockers:

1. The fixed 16-point log-trapezoid is not a safe implementation of that integral. In the bin-4 CPL high-BGO tail its largest error versus adaptive quadrature is **86.85%**.
2. The asserted exact effective-area cancellation/model-invariance is false for a multi-channel group whenever effective area varies within the group. In the requested CPL-versus-Band demonstration the integrated construction changes the largest regular-point difference only from **0.50797% to 0.50524%**, not visibly; the particular fitted Band is nearly the CPL because `beta` is pinned near -5. Sparse BGO arrows can differ by enormous factors.
3. The corrected `pred > 0` rule retains all 97 bin-4 groups numerically, but the y-axis clips two valid high-energy BGO arrows. The literal full-fitted-range x-axis rule is also violated by the 6% x-padding.
4. `live_band` is statistically invalid: threeML's covariance matrix is in transformed/internal parameter coordinates, while 41c centers and applies it in external/physical coordinates. For the T_INT Band fit, threeML's native bounded sampling rejects **50.6%**, not the displayed 2.7%, so even the correct Hessian approximation is unsuitable for this band without a stronger method.
5. The figure fit has no stored-solution/provenance guard, does not use the engine's multistart path, and can silently build a detector subset. It also drops LLE unconditionally and therefore cannot be a generally faithful figure of the engine likelihood.

The two current demo fits themselves reproduced their stored AIC values very closely. That is evidence that these two optimizations landed at the stored solutions; it does not remove the design failures above.

## Artefacts independently identified

Hashes were recomputed rather than taken from the brief:

| Artefact | SHA-256 |
|---|---|
| `scripts/41c_paper_sed.py` | `fbe506d937331eba3df295b037023b50266de4fda4157d487f006c98fe42e174` |
| `scripts/41_nuFnu_panels.py` | `21d36b2449148e938a7988cefbf224be239201b09e0acd37daa1a3a7637f810f` |
| `scripts/10_spectral_fit_burst.py` | `f501b11a8519c96b38b096b5597e3d04ccc605a954c39ff5625a51fd117563db` |
| demo `spectral_fits.ecsv` | `ef96e8eaaba03defffd8bc387b1d1f4f4151e90eae83405db0267d9b6320d7e3` |
| T_INT Band PNG | `2d6edd16706de0e6721e650a81aa611db176eef653955d1a83131d20317fc6a7` |
| bin-4 CPL PNG | `ba5130291d6a46c4256cf30823604c6e7138cf13bf370b15cb75da68f3dd821d` |

The supplied hash prefix for 41c therefore does **not** identify the file audited here. The support and engine hashes do match the supplied prefixes.

The installed threeML source audited was 2.5.0 under `/Users/salim/anaconda3/envs/threeML/lib/python3.9/site-packages/threeML`. The XSPEC source audited was `/Users/salim/Downloads/heasoft-6.30.1/Xspec/src`.

## Status summary

| Item | Status | Short finding |
|---:|---|---|
| 1 | **NEEDS-CHANGE** | XSPEC semantics confirmed; 41c's fixed numerical integral is unsafe and its x coordinate differs from XSPEC. |
| 2 | **NOT CONFIRMED** | Exact diagonal-response cancellation is false; the requested demo does not show a visible improvement. |
| 3 | **NEEDS-CHANGE** | XSPEC rebin clauses confirmed; 41c arrows are a declared non-XSPEC display statistic and need explicit labeling/fail-loud checks. |
| 4 | **NEEDS-CHANGE** | Legacy gap bridge reproduced and current PNGs are gap-clean; 41c is not airtight for empty masks or descending EBOUNDS. |
| 5 | **NEEDS-CHANGE** | All groups survive `pred > 0`, but two bin-4 arrows are clipped and x-limits extend beyond fitted edges. |
| 6 | **NEEDS-CHANGE** | Custom band misuses internal covariance; threeML has a native correlated propagation path. |
| 7 | **NEEDS-CHANGE** | EAC arithmetic is confirmed; the normalization convention is not disclosed clearly and activation can fail silently. |
| 8 | **NEEDS-CHANGE** | Current residual matches its own data error but is only a Gaussian approximation, not pgstat or XSPEC PGstat `delchi`. |
| 9 | **NEEDS-CHANGE** | Demo live fits match stored AIC, but there is no seed/provenance/solution guard. |
| 10 | **CONFIRMED** | threeML has no ratio-unfolded data plot; expected-model-rate display grouping and the counts-array helper are present, with a private-API qualification. |

## 1. `eeufspec` algorithm — NEEDS-CHANGE

### Source derivation

`PlotUnfolded` constructs `CreateBinnedPlotGroups(true, false)` and sets `isDivisibleByArea(false)` in `XSPlot/Commands/PlotUnfolded.cxx:21-28`. During manipulation it obtains the group's folded and unfolded model arrays and applies

```text
yData[j] *= unfoldedModel[j] / foldedModel[j]
```

when the folded model is nonzero and the unfolded model is not `NO_VAL` (`PlotUnfolded.cxx:60-81`). For `eeufspec`, it then multiplies both data and model by

```text
(X-dX)(X+dX) = E_lo E_hi
```

(`PlotUnfolded.cxx:114-129`). `PlotGroupCreator.cxx:50-54` defines the ordinary plot coordinate as the arithmetic midpoint and half-width, so the edge product is exact.

For a contiguous single-spectrum group, `CreateBinnedPlotGroups.cxx:718-773` builds the inverse displayed width. It calls `Model::integrateFlux` over the displayed energy interval and divides the photon-flux result by `E_max-E_min` (`CreateBinnedPlotGroups.cxx:792-857`). `Model.cxx:984-993` delegates to the numerical integration kernel; `Numerics/Integrate.cxx:42-103` integrates/fractionates the model's internal photon-flux bins. Therefore

```text
unfoldedModel[group] = integral(E_lo,E_hi) F(E) dE / (E_hi-E_lo)
```

in photon-flux-density units. It is **not** a channel-weighted sum and it is not response folded. The `cm^-2` is part of this intrinsic photon model. `isDivisibleByArea(false)` only disables XSPEC's optional extra plot-area normalization (`PlotDirector.cxx:152-158`; `PlotSettings.h:267-270`); it does not remove the physical area unit.

Thus the 41c expression

```text
E_lo E_hi * integral(F dE)/(E_hi-E_lo)
```

is the correct continuous XSPEC `eeufspec` numerator. No channel-weight correction should be added.

### Numerical check of 41c

I compared 41c's 16-point log-trapezoid to adaptive quadrature for every reconstructed bin-4 group. Largest relative numerator errors were:

| Detector | CPL | Band |
|---|---:|---:|
| `na` | 0.02863% | 0.02086% |
| `nb` | 0.02429% | 0.02207% |
| `b1` | **86.8475%** | 0.10844% |

The CPL maximum occurs in the approximately 28.5–36.48 MeV group, where exponential curvature is extreme. This is exactly the sparse regime whose ratio-unfolded arrows are already ill-conditioned.

41c also plots a group at the geometric center (`scripts/41c_paper_sed.py:66`), whereas XSPEC uses the arithmetic midpoint. The vertical value and horizontal edges implement the intended log-plot convention, but the point location is not strict XSPEC fidelity.

### Exact suggested fix

Replace the fixed sample count with converged adaptive integration in log energy:

```python
from scipy.integrate import quad

def photon_integral(photon_fn, lo, hi):
    val, err = quad(
        lambda z: np.exp(z) * float(photon_fn(np.exp(z))),
        np.log(lo), np.log(hi),
        epsabs=0.0, epsrel=1e-7, limit=200,
    )
    if not np.isfinite(val) or val < 0:
        raise RuntimeError(f"invalid model integral in [{lo}, {hi}]: {val}")
    return val

nfm = lo * hi * photon_integral(photon_fn, lo, hi) / (hi - lo)
```

For speed, use an analytic model integral where available or double the log-grid until successive results agree. Do not accept a fixed grid without a convergence assertion. Use the arithmetic midpoint if the caption claims exact XSPEC plotting coordinates; otherwise explicitly state that a geometric display center is used.

## 2. Model-invariance claim — NOT CONFIRMED

### Why exact cancellation is false

For a diagonal response over more than one channel,

```text
unfolded/folded = sum_i f_i / sum_i A_i f_i .
```

This depends on the assumed spectrum whenever `A_i` changes across the group. Exact cancellation holds only for a single channel or effectively constant response normalization over the grouped channels. Redistribution adds further dependence. Group integration removes the additional error caused by replacing an integral with a center evaluation; it does not make ratio-unfolded data model-independent.

### Requested threeML demonstration

I rebuilt the exact bin-4 `na`, `nb`, and `b1` plugins in the threeML environment, used the stored CPL and Band parameters including each model's stored EAC constants, kept the same observed/background arrays and reconstructed the same 5-sigma/5-channel display groups. There were 59 ordinary plotted points (`net >= 2 sigma`). The maximum absolute CPL-versus-Band change relative to the CPL point was:

| Construction | Maximum over ordinary points | Median over ordinary points |
|---|---:|---:|
| old point evaluation | **0.507965%** | about 0.0125% |
| 41c 16-point group integral | **0.505194%** | about 0.0125% |
| adaptive group integral | **0.505239%** | about 0.0125% |

Per detector, adaptive-integral maxima were `na` 0.50524%, `nb` 0.18718%, and `b1` 0.45995%. The requested prediction that point evaluation would be visibly worse is therefore refuted for this product.

This is not a strong two-shape stress test: the fitted Band has `beta=-4.999997`, essentially on its lower bound, and its N2LL differs from CPL by only about 0.00247. It behaves almost like the CPL over the measured region.

The sparse arrows are emphatically not invariant. For integrated 16-point arrows the ordinary NaI maxima were about 10–11%, while the largest BGO relative change was about `1.44e8` because a top-tail CPL folded prediction was about `1.84e-107` while Band predicted about `2.97e-7` counts. This is mathematical instability of ratio unfolding when the denominator approaches zero, not a physical upper-limit comparison.

### Exact suggested fix

Replace the claim with:

> The numerator follows XSPEC's group-integrated `eeufspec` construction and avoids a center-evaluation approximation. Like all ratio-unfolded data, the points remain conditional on the assumed spectral model and detector response; the dependence can be severe where the folded prediction is very small.

If a model-sensitivity diagnostic is desired, compare at least two materially different fixed shapes—not two nearly identical best fits—and report ordinary points and display arrows separately.

## 3. `setplot rebin` semantics — NEEDS-CHANGE

The source clauses in the brief are confirmed, with one nuance about the channel cap:

- `CreateBinnedPlotGroups.cxx:288-297` copies the rebin controls.
- It accumulates the net plotted datum and variance, including background uncertainty, at `:571-618`.
- The group ends at the channel boundary, or when the net datum is positive and `datapt^2 >= errorpt*critVar`, exactly at `:675-676`.
- `m_critNumChans` supplies the maximum channel-span stop initialized at `:553-559`. This is a span in original channel indices, including ignored indices; it is not necessarily a count of noticed/active channels.
- A group is skipped only when it contains no noticed channel (`:681-683`). Otherwise a terminal, maximum-span, or significant group is finalized and returned (`:710-800`) even if it never reaches the requested significance.
- `PlotUnfolded.cxx:67-80` rejects a group only for folded model zero or unfolded `NO_VAL`.
- An exhaustive search of `XSPlot` found no upper-limit/arrow state or rendering path. `PlotUnfolded` uses the standard data-dot style (`PlotUnfolded.cxx:31-39`; `PlotVector.h:13-28`; `PlotStyle.h:12-24`).

Therefore low-significance groups would still be XSPEC points. 41c instead removes them from the ordinary-point call and draws one-sided arrows when `net < 2 sigma` (`scripts/41c_paper_sed.py:88-89,239-253`). That is allowed as an explicitly declared publication convention, but these are neither XSPEC products nor statistical 95% confidence limits. The current visual language can be mistaken for the latter.

### Exact suggested fix

Add an in-panel legend item and caption text such as:

> Downward arrows are display-only Gaussian `net+2 sigma` indicators for groups with `net<2 sigma`; they are not XSPEC rendering and are not likelihood confidence limits.

Also validate every group before division:

```python
if not np.all(np.isfinite(pred)) or np.any(pred < 0):
    raise RuntimeError("non-finite or negative folded model")
zero = pred == 0
if np.any(zero):
    log_or_stamp_exact_dropped_groups(...)
good = ~zero
```

Do not silently turn NaNs into dropped points or describe arrows as “points.”

## 4. Group/mask interaction — NEEDS-CHANGE

The legacy flaw is confirmed and was reproduced. `_plugin_counts` in `scripts/41_nuFnu_panels.py:96-105` first compresses EBOUNDS, counts, background, and prediction by the active mask. `_rebin_for_plot` at `:75-94` then treats the compressed rows as adjacent. A low-significance synthetic pair spanning active intervals 28–29 and 40–41 keV was merged into one 28–41 keV group with a displayed center near 33.88 keV—inside the excluded K-edge region.

41c's discontinuity split (`scripts/41c_paper_sed.py:57-65`) fixes this for the current products. Reconstructed active intervals are:

- `na`: 7.310–29.292 and 40.065–922.928 keV
- `nb`: 7.955–28.248 and 40.418–905.225 keV
- `b1`: 174.651–38461.598 keV

Neither regenerated figure has a group center or horizontal group interval inside the open 30–40 keV gap. Direct PNG inspection agrees. A small anti-aliased cap just below 40 keV is rasterization of the post-gap error bar, not an extra group.

The fix is not airtight in all requested edge cases:

- A one-channel run works.
- An empty active mask makes `parts` empty and then dereferences `parts[0]`; `fit_intervals` likewise assumes a nonempty segment.
- The one-sided floating comparison is reasonable for the current ascending EBOUNDS, but adjacency is more robustly detected from original channel indices.
- Descending EBOUNDS are not supported or rejected. XSPEC explicitly detects energy direction (`CreateBinnedPlotGroups.cxx:518-531`) and handles ordering (`:561-569,685-690`). All current demo EBOUNDS are finite, positive, and strictly ascending, so this did not affect the PNGs.

### Exact suggested fix

Split on original mask indices and validate EBOUNDS before compression:

```python
eb = np.asarray(pl.observed_spectrum.edges, float)
mask = np.asarray(pl.mask, bool)
if eb.size != mask.size + 1 or not np.all(np.isfinite(eb)) or np.any(eb <= 0):
    raise RuntimeError("invalid EBOUNDS")

direction = np.sign(np.diff(eb))
if np.all(direction < 0):
    # Reverse edges and every aligned channel array together.
    ...
elif not np.all(direction > 0):
    raise RuntimeError("non-monotonic EBOUNDS")

active = np.flatnonzero(mask)
if active.size == 0:
    raise RuntimeError(f"{pl.name}: no active channels")
breaks = np.flatnonzero(np.diff(active) != 1) + 1
runs = np.split(np.arange(active.size), breaks)
```

Use the same validated run list for grouping and `fit_intervals`; never catch and silently skip a malformed detector.

## 5. Full-fitted-range axis rule — NEEDS-CHANGE

The code implements the new detector conventions it claims:

- NaI active 8.1–900 keV with 30–40 keV excluded
- BGO active 200–38000 keV
- LLE constants 20000–100000 keV

These constants are in `scripts/10_spectral_fit_burst.py:84-88` and are applied at `:236-239`. The demo sidecar records the same convention. The selected whole-channel edges extend beyond the nominal thresholds, as expected: the reconstructed global fitted range is **7.30999994–38461.597656 keV** in both products.

41c's source curve and band grid starts and stops exactly at those fitted edges (`scripts/41c_paper_sed.py:228-230,258`), and `unfold_all_points` now accepts every strictly positive folded prediction (`:84`). Reconstructed product accounting is:

| Product | Groups | `pred > 0` | Display arrows | Zero-prediction drops |
|---|---:|---:|---:|---:|
| T_INT Band | 140 | 140 | 35 | 0 |
| bin-4 CPL | 97 | 97 | 38 | 0 |

Two code/display facts nevertheless violate the stated rule:

1. `set_xlim(fit_lo/1.06, fit_hi*1.06)` (`:267`) displays 6.896–40769 keV, beyond the fitted range.
2. The y-floor `max(min(y_all), 1e-5*y2)` (`:268-275`) clips two valid bin-4 BGO arrows from the upper panel. Their approximate group centers and arrow values are 32.244 MeV / `2.86e-3` and 37.457 MeV / `2.00e-4` in the plotted units. They remain visible only as residual points below. Thus all groups survive the arrays, but not all are shown in the SED panel.

At the other extreme, the last BGO CPL arrow ratios grow roughly through `1e59`, `1e74`, `1e94`, and `1e109` above the source curve because `pred` approaches zero. The arithmetic is finite but the value is not a useful flux bound. XSPEC ratio-unfolding can produce the same forest because it also divides by a tiny folded model; this is not a reason to cap the numbers silently.

### Exact suggested fix

- Use exact `ax.set_xlim(fit_lo, fit_hi)` if the literal rule is retained.
- Set the lower y-limit below the smallest finite positive point/arrow/band/curve value, or draw explicit boundary markers for off-scale values and stamp their count. Do not silently omit groups.
- Do not numerically cap high arrows. Add a caption/legend warning that ratio-unfolded display indicators become ill-conditioned where the assumed folded model is near zero. A count-space companion panel is the clearest alternative for the sparse tail.
- Combine this with adaptive model integration and finite/nonnegative assertions from items 1 and 3.

## 6. The 68% band — NEEDS-CHANGE

### Statistical assessment

Bounded rejection sampling from a local multivariate-normal approximation can be defensible as a display approximation when it is performed in the optimizer's coordinates, the covariance approximation is credible, and the rejected mass is demonstrably small. It samples the local Gaussian conditional on the bounds; it is not a profile-likelihood interval. Even a few-percent rejection can narrow correlated tails modestly and must be disclosed.

41c does not perform that calculation correctly. threeML minimizes in internal/transformed parameter coordinates (`threeML/minimizer/minimization.py:431-445`) and computes the covariance there (`:575-587`; `minuit_minimizer.py:205-236`). 41c instead builds its mean vector from each parameter's external `.value`, adds draws from `jl.covariance_matrix`, checks external bounds, and assigns the results back as external values (`scripts/41c_paper_sed.py:120-169`). Band/CPL scale parameters use logarithmic transformations in astromodels (`astromodels/functions/functions_1D/powerlaws.py:284-312,773-793`). The custom samples therefore do not have the claimed distribution. It also skips EAC `cons_*` bounds and assignments while their covariance correlations remain in the matrix.

The test on the live T_INT Band fit illustrates the impact:

- 41c reports 2.7% spill.
- threeML's native internal-coordinate sampling retained 2470 of 5000 draws, i.e. rejected **50.6%** once all parameter bounds, including EAC, were respected.
- As a diagnostic only, 41c's wrong-coordinate band width divided by the native truncated-Gaussian width had median **4.20**, 5th–95th percentile about **1.62–23.10**, and maximum about **24.99** over a 30-energy grid. Here the coordinate error dominates any generic inward-bias discussion.

At 50.6% rejection, the native Hessian Gaussian itself warns that the approximation is not suitable for a publication confidence band. The current band should be suppressed or replaced with a constrained bootstrap/profile/posterior calculation.

There is also an exception-safety problem: 41c restores the best fit only on its normal completion path. An exception during sampling/evaluation can leave `jl.likelihood_model` at a sampled parameter vector, after which the nominal black curve can be wrong.

### Native threeML path

threeML already provides the better rooted implementation:

- `MLEResults` centers the multivariate normal on `_get_internal_value`, samples the internal covariance, rejects against internal bounds, transforms accepted draws back to external values, and warns when rejection exceeds 1% (`threeML/analysis_results.py:1571-1659`).
- `AnalysisResults.get_variates` and `.propagate` expose correlated fitted variates (`threeML/analysis_results.py:559-627`).
- `FittedPointSourceSpectralHandler` evaluates the optimized point-source spectrum and converts the differential spectrum to `E^2 F(E)` for νFν (`threeML/utils/fitted_objects/fitted_point_sources.py:121-151,234-354`). Its fitted-source handler forms equal-tail intervals from correlated variates (`:103-209,329-347`).
- Public `plot_spectra` uses this machinery for confidence contours (`threeML/io/plotting/model_plot.py:29-65,149-166,321-352`). Its central displayed curve is a propagated median, so 41c may still draw the explicit MLE curve separately.

### Exact suggested fix

For a live MLE band, use the fitted result rather than `jl.covariance_matrix` directly:

```python
from threeML.utils.fitted_objects.fitted_point_sources import (
    FittedPointSourceSpectralHandler,
)

handler = FittedPointSourceSpectralHandler(
    jl.results,
    source_name,
    energy_grid,
    "keV",
    "keV/(cm2 s)",
    confidence_level=0.68,
    equal_tailed=True,
)
lo = handler.lower_error.value
hi = handler.upper_error.value
```

Keep the separately evaluated MLE black curve if that is the intended center. Record the requested sample count and retained sample count. Preserve the existing conservative policy: if native rejection exceeds the allowed threshold, suppress the Hessian band and say why. For this T_INT fit, use a constrained parametric bootstrap, profile construction, or posterior sampling before publishing a 68% band. If any manual temporary parameter mutation remains, restore in `finally`, not only on success.

## 7. EAC/constant conventions — NEEDS-CHANGE

The arithmetic in the brief is confirmed. `SpectrumLike` creates an effective-area nuisance constant with value 1 and bounds 0.8–1.2 (`threeML/plugins/SpectrumLike.py:165-178`). `use_effective_area_correction` activates it (`:2196-2240`), JointLikelihood attaches plugin nuisances as model parameters (`threeML/classicMLE/joint_likelihood.py:144-168`), and `SpectrumLike.get_model()` multiplies the folded source model by that nuisance (`SpectrumLike.py:1931-1952`). `expected_model_rate` includes the result (`:2354-2356`). `DispersionSpectrumLike` applies the detector response before this plugin-level normalization (`threeML/plugins/DispersionSpectrumLike.py:115-133`).

Therefore `_plugin_counts` obtains an EAC-scaled detector prediction. Dividing each detector's counts by its own prediction cancels that detector's fitted `k`, while multiplying by the bare `k=1` photon numerator places every detector's ratio-unfolded points on the reference normalization. The single black curve is also the bare `k=1` source model. For the demo, the reference is `na`; stored bin-4 constants are approximately `k_nb=0.8134` and `k_b1=1.0765`.

This differs from drawing one `k F(E)` model curve per dataset, which is the more literal XSPEC-style presentation. It is a defensible cross-normalized display, but the present detector-only legend does not make it unambiguous.

There is a fail-loud defect: `build_plugins` catches every exception while activating non-reference EACs and silently continues (`scripts/41_nuFnu_panels.py:212-223`). A figure can therefore use the wrong nuisance state without an invariant firing.

### Exact suggested fix

Add caption/legend language:

> Detector points are ratio-unfolded with each detector's own fitted EAC-scaled prediction and cross-normalized to the `k=1` reference detector `na`; the black curve and band show the intrinsic `k=1` source model.

Prefer also stamping each fitted `k`. Remove the broad exception handler. After plugin construction assert that the reference constant is fixed at exactly 1 and every requested non-reference constant is free with bounds `(0.8,1.2)`; abort on mismatch.

## 8. Residuals — NEEDS-CHANGE

41c's residual

```text
(net - pred) / sqrt(max(observed,1) + background_variance)
```

uses the same Gaussian error bar as its paired data point. It is therefore internally consistent as a standardized count residual under the plot's approximation. It is not an exact pgstat residual.

The brief's description of XSPEC `plot delchi` as universally using the data-plot error is not correct for PGstat. `PlotDelchi.cxx:46-70` delegates each bin to the active statistic's `deltaSigmaForSingleBin`. Chi-square uses `(observed-model)/error` (`XSFit/StatMethod/ChiSquare/ChiSquare.cxx:267-273`), but `FitStatMethod.cxx:203-210` maps PGstat to the C-statistic family, whose residual rule is model-error based with observed-count fallbacks (`XSFit/StatMethod/Cstat/Cstat.h:293-315`). It is not 41c's `observed + background_variance` denominator.

threeML's fit statistic is genuinely Poisson observed counts plus a profiled Gaussian background (`threeML/utils/statistics/likelihood_functions.py:205-274`; `SpectrumLike.py:283-298`). Its native count-residual display compares observed counts with background plus source and uses the Vianello likelihood-ratio significance (`SpectrumLike.py:3349-3389`; `threeML/utils/statistics/stats_tools.py:310-339`). That is closer to the likelihood than 41c's Gaussian standardization, although the implementation deserves a zero-count safety check before reuse.

### Exact suggested fix

Either:

1. retain the current formula and label the axis/caption **“standardized count residual (Gaussian approximation)”**, explicitly not “pgstat residual” or “XSPEC delchi”; or
2. for publication, use a signed square root of the per-group profile-likelihood difference, profiling the Gaussian background under the fitted and saturated source hypotheses. Implement zero-count terms with a zero-safe `xlogy`/explicit branch, and unit-test zero observed counts, zero background variance, and negative net counts.

The second option is the more standard statistic-rooted choice. Do not silently substitute a generic `(data-model)/error` and call it pgstat.

## 9. Live-fit-at-figure-time design — NEEDS-CHANGE

The current two demonstrations landed at the stored solution:

| Fit | Stored AIC | Rebuilt live AIC | Difference |
|---|---:|---:|---:|
| T_INT Band | 4245.160325016929 | 4245.160325016929 | 0 |
| bin-4 CPL | 1374.165086983202 | 1374.165142608256 | `+5.56e-5` |

This is excellent numerical agreement for these two cases. It does not establish robustness. 41c creates the requested model at default seeds, performs one fit, and stamps only the resulting live AIC (`scripts/41c_paper_sed.py:204-217,282`). It does not read the stored row's validity/status, seed values, EAC values, detector list, block/source interval, convention metadata, or stored AIC. It also does not explicitly pin the minimizer. The engine's stored candidate can have come from DSBPL multistart and physical-validity gates (`scripts/10_spectral_fit_burst.py:1218-1257` and following). A local minimum, silently missing plugin, or provenance mismatch can therefore yield a polished figure of a different likelihood.

### Exact suggested fix

The cheapest reliable guard is:

1. Require an explicit fit table and metadata sidecar, not a hardcoded current catalog/blocks root.
2. Resolve the exact model and block row; assert its status/validity, interval, fitted detector set, reference detector, and range convention.
3. Seed every source parameter and EAC constant from that row before fitting.
4. Explicitly select MINUIT, matching the engine.
5. Assert `abs(AIC_live-AIC_stored) < 0.1` (or a documented statistic tolerance) and fail, not merely warn, when violated.
6. Stamp `AIC_live`, `AIC_stored`, their difference, the minimizer/status, and the complete detector/provenance information. If there is no stored reference, require an explicit `--allow-unverified-live-fit` mode and label the output diagnostic.
7. For models whose authoritative result used multistart, either call the same engine routine or use the stored solution as the first seed and retain the AIC guard.

The current one-decimal AIC text is not enough to prove equivalence.

## 10. threeML rooting — CONFIRMED, with qualification

The three claims were spot-verified against the installed 2.5.0 source:

1. A case-insensitive search of all installed threeML Python files found no `unfold`, `eeufspec`, or `eufspec` implementation. `display_spectrum_model_counts` is a folded count-spectrum display (`threeML/io/plotting/post_process_data_plots.py:41-75`), while `plot_spectra` draws source-model curves/contours, not ratio-unfolded detector data.
2. `_construct_counts_arrays` obtains `expected_model_rate` (`SpectrumLike.py:3218-3220`) and supplies that vector to `Rebinner` (`:3241-3246`), then applies the resulting grouping consistently (`:3252-3259`). `Rebinner` accumulates the supplied expected vector to its threshold (`threeML/utils/binner.py:19-37,64-128`). This is expected-model-rate grouping, not observed significance grouping.
3. `_construct_counts_arrays` is deliberately separated as the common extraction helper (`SpectrumLike.py:3192-3209`) and returns the plot arrays at `:3425-3455`.

The qualification is that its leading underscore makes `_construct_counts_arrays` a **private** internal API, not a stable public contract. “Sanctioned extraction point” is too strong if it implies compatibility guarantees.

threeML does make parts of 41c redundant:

- `jl.results` plus `FittedPointSourceSpectralHandler`/`plot_spectra` supplies correlated source curves and confidence contours.
- `_construct_counts_arrays` supplies consistently grouped folded count data/model/residual arrays if expected-model-rate grouping is acceptable.

It does **not** supply XSPEC ratio-unfolded data, XSPEC's observed-significance plus channel-cap grouping, the custom 2-sigma arrows, detector-class shading, or this layout.

## DISCREPANCIES and exact fixes

### Sign-off blockers

1. **Wrong numerical integrator in an otherwise correct XSPEC numerator.** Replace fixed 16-point trapezoids with adaptive/analytic integration and a convergence/finite assertion. The measured CPL error reaches 86.85%.
2. **False exact model-invariance claim.** State that ratio-unfolded points remain model and response dependent. Do not use this nearly-degenerate CPL/Band pair as evidence of a visible improvement.
3. **Invalid confidence-band sampling.** Delete the external-coordinate covariance sampler. Use `jl.results` native internal-coordinate variates/`FittedPointSourceSpectralHandler`; suppress the T_INT Hessian band at its measured 50.6% native rejection or replace it with bootstrap/profile/posterior sampling. Restore parameters in `finally` if mutation remains.
4. **Full-display rule is not met.** Remove x-padding under the literal rule and fix the y-limit/off-scale representation so both clipped BGO arrows are visibly accounted for. Never cap the extreme high arrows silently.
5. **No stored-solution guard.** Seed from the stored row, match provenance/detectors/convention, pin MINUIT, and hard-fail on an AIC mismatch. Record machine-readable provenance next to the image.
6. **Silent detector/EAC failures.** Remove `except Exception: pass`; assert the requested plugin set and every reference/non-reference EAC state.

### Required clarity and robustness fixes

7. Label arrows as custom display-only Gaussian indicators, not XSPEC or confidence upper limits.
8. Split channel runs by original active indices; fail on empty masks and reject or normalize descending/non-monotonic EBOUNDS.
9. State the EAC cross-normalization convention and reference detector in the figure/caption; preferably list fitted constants.
10. Relabel the current residual as a Gaussian standardized count residual, or replace it with a zero-safe signed profile-likelihood residual.
11. If claiming exact XSPEC horizontal placement, use arithmetic group centers. If retaining geometric centers for log display, disclose that convention.

## Independent findings outside the ten questions

### 1. 41c cannot yet reproduce the full engine detector likelihood

`scripts/41c_paper_sed.py:187` removes every LLE detector unconditionally. The engine can include LLE at 20–100 MeV and may include LAT components. The approved catalog contains LLE cases, so this is not hypothetical. For such bursts the “live fit” would be a different fit, not merely a display subset. Include every detector/plugin used by the stored likelihood, or fail explicitly and restrict 41c's supported scope. LAT data need not be ratio-unfolded into these GBM points, but if LAT participated in the fit it must participate in the live likelihood and be disclosed.

### 2. Reference-detector selection can drift from the engine

41c chooses the minimum-angle detector. The engine has canonical/brightest-NaI logic and stores the chosen reference. They coincide for this demo (`na`) but need not in general. Read and assert the stored reference detector rather than recomputing it independently.

### 3. Input provenance is hardcoded and incomplete

41c hardcodes `results/sweep106` blocks while reading the current approved background catalog. That can silently combine products from different selection/range eras. It also cannot prove that the PNG was generated by the audited untracked source file; no machine-readable figure sidecar records source hash, inputs, parameters, EACs, covariance method, group edges, or retained/dropped groups. Require explicit CLI inputs and write such a sidecar with the figure.

### 4. Detector colors are incomplete

The plotting loop computes a detector-class color and then replaces it with a hardcoded map containing only `na`, `nb`, and `b1`; other detectors fall back to gray. Use the detector-class color consistently or a complete deterministic detector map.

### 5. A stale engine comment contradicts the new LLE constant

The executable constant is correctly `20000-100000`, but an older comment near `scripts/10_spectral_fit_burst.py:211` still describes LLE as 30–100 MeV. Correct that comment when code edits are authorized; the runtime range implementation itself is confirmed.

## COULD NOT VERIFY

- I could not cryptographically prove that the two PNGs were generated by the exact audited 41c bytes because the figure has no provenance sidecar and the supplied 41c hash does not match the file. I did verify the current PNG hashes, reconstructed their detector masks/groups/ranges, reproduced their stored/live fit statistics, and matched their visible features.
- I did not execute XSPEC itself. Per the brief, the supplied XSPEC source tree was treated as ground truth; all XSPEC conclusions above are source-derived.
- The current demonstration contains no LLE or LAT plugin, so the global detector-completeness issue was established statically from 41c and the engine rather than with a second LLE-bearing runtime example.

## Conditions for a later sign-off

At minimum: use a converged XSPEC-equivalent group integral; correct the model-dependence claim; replace/suppress the invalid live band through threeML's result machinery; make every retained group visibly accounted for; and bind the live fit to the stored solution, detector set, reference detector, and convention with hard assertions. After those changes, rerun this same bin-4 test plus one materially different spectral-shape stress test and one LLE-bearing burst.

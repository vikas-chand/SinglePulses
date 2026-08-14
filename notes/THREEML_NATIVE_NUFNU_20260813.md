# Does threeML give us nuFnu data and a display rebin? — adjudicated decision

**Date:** 2026-08-13
**threeML version:** 2.5.0 (`/Users/salim/anaconda3/envs/threeML/lib/python3.9/site-packages/threeML`)
**astromodels:** same env, checked alongside.
**Question from the PI:** *"are we not using threeml, does threeml not have itself something
for plotting with rebin, and all we wanted is get nuFnu data like XSPEC"*
**Rule under test:** 3ML code must use threeML's own capabilities; custom stand-ins ONLY
where threeML ships nothing.

**How this was produced.** Three independent source searches of the *installed* package were
run first — one enumerating the public API (`by-api`), one searching by XSPEC/3ML vocabulary
(`by-vocab`), one working backwards from the task "put a data point in flux space" (`by-task`).
This document adjudicates them. Every claim below that changes a decision was then
**re-verified by me directly**, either by reading the cited line or by running a live probe on a
simulated `SpectrumLike` in the threeML env (probe script:
`<scratchpad>/probe.py`; outputs quoted inline as `PROBE`). Nothing here rests on the web,
on memory, or on an unchecked search result. The installed package ships **no** notebooks,
`.rst` or `.md` docs (`find` returns nothing), so "what the library intends" is read off its
source and its shipped tests only.

---

## 1. Does threeML ship an XSPEC `eeufspec` equivalent — nuFnu DATA points?

**NO.** Unambiguously, and this is the one point all three searches agreed on.

A recursive case-insensitive grep over the installed `threeML` **and** `astromodels` for
`eeufspec|ufspec|unfold|deconvolv|setplot|grppha` returns **exactly one hit in the entire
tree**, and it is a docstring describing the *problem*, not a solution:

```
utils/spectrum/binned_spectrum.py:713
    """A binned spectrum that must be deconvolved via a dispersion or response matrix."""
```

There is no function anywhere in threeML 2.5.0 that returns or plots per-channel **data**
in any physical flux unit — not nuFnu, not dN/dE, not E²dN/dE. The complete exported
spectral-plotting surface is `plot_spectra`, `plot_point_source_spectra`,
`display_spectrum_model_counts`, `display_photometry_model_magnitudes`,
`calculate_point_source_flux`, `plot_tte_lightcurve` (`threeML/__init__.py:247-256`).
None of them unfolds data.

### The three closest native things, and exactly what each is missing

| Native thing | What it gives | What it is missing |
|---|---|---|
| `plot_spectra(*results, flux_unit="erg2/(cm2 s keV)")`<br>`io/plotting/model_plot.py:29` | Real nuFnu — `flux_unit` resolves through `_flux_lookup` to `'nufnu_flux'` with builder `lambda x: x*x*flux_model(x)` (`utils/fitted_objects/fitted_point_sources.py:135, 148-150`) — **plus** a properly propagated confidence contour. | **All the data.** The module never touches a plugin; the renderer `SpectralContourPlot` (`model_plot.py:672`) exposes only `add_model`, `add_dimensionless_model`, `finalize`. There is no `add_data` and no `errorbar` call in the class. The squaring is applied to the model *function*, never to counts. |
| `display_spectrum_model_counts` → `SpectrumLike.display_model`<br>`post_process_data_plots.py:41` → `SpectrumLike.py:3457` | Real data + model + residual, with a genuine display-only rebin. | **Flux space.** The y-label is a hard-coded literal, `'Net rate\n(counts s$^{-1}$ keV$^{-1}$)'` (`SpectrumLike.py:3634`) / `'Observed rate…'` (`:3647`). PROBE: `inspect.signature(SpectrumLike.display_model)` has **no** `flux_unit` parameter. This is XSPEC `ldata`, full stop. The same hard-coded label appears in `FermiLATLike.py:888` and `FermipyLike.py:1220`, so it is a package-wide rule, not a `SpectrumLike` quirk. |
| `SpectrumLike._construct_counts_arrays(min_rate)`<br>`SpectrumLike.py:3192` | The rebinned display arrays as a plain dict — `new_observed_rate(+err)`, `new_background_rate(+err)`, `new_model_rate`, `new_energy_min/max`, count-weighted `mean_energy`, asymmetric `delta_energy`, and `residuals` **already in sigma**. Its own docstring (`:3198-3200`) says it was deliberately factored out of the plotting code "because it is cleaner and allows us to extract these quantites independently". | **One multiplication.** It stops precisely at the response boundary: it never applies `nuFnu_model(E) × net/predicted`. That step — the unfolding — is the thing that does not exist in threeML. |

So the honest sentence for the paper's methods section is: *threeML hands back the rebinned
display arrays natively and stops one multiplication short of nuFnu; the multiplication
(the response unfolding) is not implemented anywhere in the package.*

The only in-source usage examples of nuFnu at all are two tests —
`test/test_FermiLATLike.py:121` (`plot_spectra(..., flux_unit="erg2/(cm2 s keV)")`) and
`test/test_fitted_point_sources.py:28` (the accepted unit strings). Both are model-only.
There is no shipped test, example or config anywhere in threeML that puts a data point in
flux space.

**Honest escape hatch, for the record:** `OGIPLike.write_pha` (`plugins/OGIPLike.py:182`)
exports observation + background + response to OGIP files. If we ever want a *canonical*
`eeufspec` rather than our emulation of one, we export and let XSPEC/pyXSPEC run
`setplot rebin 5 5; plot eeufspec` with its own code. Worth naming in the docstring as the
reference implementation our emulation is checked against.

---

## 2. Does threeML ship display-only rebinning we should be using instead of `_rebin_for_plot`?

**Yes — it ships both kinds, and the distinction is the whole answer.** My prior belief
("threeML's rebinners mutate the plugin") was too pessimistic and the docstring in
`scripts/41_nuFnu_panels.py` should be corrected on that point.

### (ii) Rebinning that changes the LIKELIHOOD — never for a figure

`SpectrumLike.rebin_on_source(min_number_of_counts)` (`:1644`) and `rebin_on_background`
(`:1602`) build a `Rebinner` on the observed / background counts, call
`PHASpectrum.set_ogip_grouping` (`:1635-1636`, `:1662-1666`, setter at
`pha_spectrum.py:794`), and go through `_apply_rebinner` (`:1674`), which overwrites
`_current_observed_counts`, `_current_background_counts`, `_current_scaled_background_counts`
and the error arrays (`:1682-1704`). Those are exactly the attributes the likelihood
evaluator reads live (`utils/spectrum/spectrum_likelihood.py:54, 108-109, 156, 211,
239-240, 290-291`), and `get_model` reroutes the folded model too (`:1938-1943`).

> **PROBE (measured, not read):** logL = **-313.9986** on 120 channels →
> **-90.1950** on 19 groups after `rebin_on_source(50)`. `remove_rebinning()` restores
> **-313.9986** exactly.

These are fit-time tools wearing a plotting name. They must never be used to make a picture.

### A REAL HAZARD found along the way — worth acting on regardless of the plotting question

`SpectrumLike.get_number_of_data_points()` (`:3177-3182`) returns `self._mask.sum()` and
**ignores the rebinner entirely**. The rebin-aware property `n_data_points` (`:2602-2610`)
*does* return `self._rebinner.n_bins` — but a full-tree grep shows **that property is consumed
nowhere in the statistics path**. What the statistics path actually calls is the method:
`classicMLE/joint_likelihood.py:384` sums `get_number_of_data_points()` and feeds it to
`aic()`/`bic()` at `:400` (`utils/statistics/stats_tools.py:16-28`); `bayesian/sampler_base.py:231`
does the same.

> **PROBE:** after `rebin_on_source(50)` — `n_data_points` property = **19**,
> `get_number_of_data_points()` (the one that feeds AIC) = **120**.

Consequence: if a rebinner is ever applied to a plugin before a fit, the log-likelihood is
computed over N_rebinned bins while the AICc small-sample correction `2k(k+1)/(N−k−1)` uses
the *un-rebinned* channel count. Our entire model selection is ΔAIC-based.

**ACTION (independent of this whole nuFnu question):** add an assertion in
`scripts/10_spectral_fit_burst.py` that `plugin._rebinner is None` for every plugin before
any fit. Cheap, and it closes a silent-corruption path.

### (i) Rebinning that only changes the PICTURE — it exists and it is good code

`SpectrumLike._construct_counts_arrays(min_rate, ...)` (`:3192`) builds a **local**
`Rebinner(expected_model_rate, min_rate, self._mask)` at `:3245` and never assigns
`self._rebinner`. Nothing mutates.

> **PROBE:** before/after a `_construct_counts_arrays(min_rate=5.0)` call —
> `_rebinner` stays `None`; `n_data_points` 120 → 120; logL **-313.9986 → -313.9986**.
> Returned dict keys: `new_observed_rate`, `new_observed_rate_err`, `new_background_rate`,
> `new_background_rate_err`, `new_model_rate`, `new_energy_min/max`, `new_chan_width`,
> `mean_energy`, `delta_energy`, `residuals`, `residual_errors`, `expected_model_rate`,
> `energy_min/max`, `chan_width`.

Its residuals are proper sigma: `Significance(Non=obs, Noff=bkg + model/scale, alpha=scale)`
(`:3349-3355`) then `li_and_ma()` / `li_and_ma_equivalent_for_gaussian_background()` /
`known_background()` by noise model (`:3378-3400`). That is a **better** residual than our
Gaussian `(net−pred)/sqrt(var)`.

### Would adopting its grouping semantics be scientifically acceptable for a plot whose job is to show which channels are DETECTED?

**No. Two independent reasons, either one sufficient.**

**Reason 1 — the criterion answers the wrong question.** The grouping vector is
`expected_model_rate` (`:3245`), i.e. a group closes when the **model** predicts enough
counts/s. A group therefore means *"the model says there is signal here"*, not *"the data
are detected here"*. On a figure whose entire job is to show which channels are detected,
that begs the question. XSPEC's `setplot rebin S,N` groups on the **data**; that difference
is not cosmetic.

**Reason 2 — and this is the decisive one — the data points MOVE when the model changes.**

> **PROBE, identical dataset, three fitted models:**
> PL → **71** groups, CPL → **70** groups, Band → **76** groups, with different group edges.

Our `--mode bin` panel shows ONE time bin against ALL 24 models. Under native grouping,
every panel would display a differently-binned version of the same data. A
model-comparison figure in which the data change with the model is not a model-comparison
figure. This alone disqualifies wholesale adoption.

**Two further gaps, stated for completeness.** `Rebinner.__init__(vector_to_rebin_on,
min_value_per_bin, mask=None)` (`utils/binner.py:26`) takes **no** max-group-size argument
at all, so XSPEC's `N` has no expression; and no upper-limit machinery exists anywhere in
the spectral path (`uplims=True` appears once, in the experimental time-domain
`plugins/experimental/CastroLike.py:309`).

**And the structural reason the RULE can never be delegated.** `Rebinner`'s rule is a pure
additive accumulator — `n += b` (`binner.py:101`) then close when `n >= min_value_per_bin`
(`:107`). Significance, `(Σo − Σb)/sqrt(Σvar)`, is a *ratio of accumulated sums* and is not
additive. **No choice of input vector** makes an additive threshold equal to a significance
threshold. This is the source-cited justification for keeping our own loop, and it is much
stronger than "threeML groups on counts not significance".

Confirming the gap from the other side: threeML **does** know how to accumulate to a
significance threshold — `TemporalBinner.bin_by_significance` (`binner.py:229`, `sigma_level`
kwarg) — but only on the **time** axis. `binner.py` contains exactly two grouping classes:
`Rebinner` (additive, energy) and `TemporalBinner` (significance/Bayesian-Blocks, time).
There is no energy-axis significance grouper. That asymmetry is the cleanest possible
statement that this is a genuine "threeML ships nothing" condition.

---

## 3. ACTIONABLE — verdict per function

### `unfold_detector()` — **KEEP-AS-BLESSED-EXCEPTION** (core), **BUILD-ON-NATIVE** (plumbing)

`scripts/41_nuFnu_panels.py:111-132`.

The unfolding line itself, `nufnu_data = nufnu_model(E) × (obs−bkg)/predicted`
(`:124-125`), is a legitimate blessed exception: threeML ships nothing that maps counts into
flux space, established in §1 to the limit of a source search.

But the exception is **narrower than the function**. `_plugin_counts` (`:96-105`) hand-derives
quantities threeML already exposes. Replace with the native accessors:

| Our hand-roll | Native |
|---|---|
| `obs − bkg` arithmetic | `pl.source_rate` (`SpectrumLike.py:2500`) — its own docstring says "only for visual purposes" |
| our propagated net error | `pl.source_rate_error` (`:2535`) |
| `pl.get_model()` | `pl.expected_model_rate` (`:2354`) — rate, not counts; use consistently |
| `pl.response.ebounds[:-1][mask]` | `pl.energy_boundaries` (`:2575`, mask/rebin-aware at `:2586`) |
| our `(o−b)/sqrt(max(o,1)+bkg_var)` | `Significance(...)` (`utils/statistics/stats_tools.py:213`), branch `li_and_ma_equivalent_for_gaussian_background` (`:310`) for our polynomial backgrounds |

> ⚠ **Do not swap in `Significance` naively.** PROBE:
> `Significance(Non=[172,180,5], Noff=[0,3,0], alpha=10).li_and_ma()` → **`[nan, 4.25, nan]`**.
> `li_and_ma` evaluates `Noff·log(Noff/(Non+Noff))` = `0·log(0)` = NaN for any empty-background
> channel — common at the top of BGO, i.e. exactly the faint channels we currently turn into
> upper limits. Also `known_background()` asserts `0 < alpha ≤ 1` and will raise on our
> `alpha > 1`. Use the gaussian-background branch and guard `Noff == 0`.

Note our ratio uses counts rather than rates; exposure cancels in `net/predicted`, so the
numbers are unaffected by the switch — this is a provenance cleanup, not a numerical change.
**Re-run one burst before/after and diff the points to prove that.**

### `_rebin_for_plot()` — **KEEP-AS-BLESSED-EXCEPTION**, with the justification rewritten

`scripts/41_nuFnu_panels.py:75-94`.

Keep it. But the current docstring's implied premise — that threeML has no display-only
rebinning — is **false**, and this document must supersede it. The correct, defensible
justification is threefold and every leg is source-cited:

1. `Rebinner`'s rule is additive (`binner.py:101, 107`); significance is a ratio of sums and
   is not additive. No input vector makes them equivalent.
2. `Rebinner.__init__` (`binner.py:26`) has **no** max-channels-per-group parameter, so XSPEC's
   `N` cannot be expressed.
3. No upper-limit concept exists in any spectral display path.

Plus the scientific objection from §2: the one native display-rebinner groups on the
**model**, so its groups move between models (PROBE: 71/70/76), which is disqualifying for a
figure whose panels compare models on identical data.

**Edit the docstring at `:76-80`** to say this, and to state plainly that threeML *does* ship
`_construct_counts_arrays` and that we deliberately do not use it, with the reason. A blessed
exception that misstates why it exists is not blessed, it is unaudited.

**Do NOT adopt `_construct_counts_arrays`** — it is attractive (non-mutating, sigma residuals,
count-weighted bin centres, asymmetric x-errors) and it was the strongest candidate from two
of the three searches, but it does the grouping itself, so we cannot feed it our groups. Borrow
its *ideas* instead, both of which are free improvements we currently lack:
- **count-weighted mean energy** within a group (`:3270-3309`) instead of our geometric mean
  `sqrt(lo·hi)` (`:120`). This is what threeML and XSPEC both do, and it matters for wide
  groups at the band edges.
- **asymmetric `delta_energy`** x-errors from the weighted centre (`:3305-3307`) — our `xerr`
  at `:129` already does this, so we match; good.

### `model_error_band()` — **DELETE-AND-USE-NATIVE**. This is the finding the PI is after.

`scripts/41_nuFnu_panels.py:143-182`.

This function is **not** a stand-in for something threeML lacks. It is a line-for-line
reimplementation of threeML's own MLE error propagation:

| Our line | threeML's line |
|---|---|
| `rng.multivariate_normal(mean, cov, n_samples, method="svd")` (`:155`) | `np.random.multivariate_normal(values, covariance_matrix, n_samples)` — `analysis_results.py:1597` |
| loop rejecting samples outside `p.min_value/p.max_value` (`:157-165`) | bound-rejection loop over `_get_internal_min_value/_get_internal_max_value` — `analysis_results.py:1613-1640` |
| `if n_skipped > 0.01*n_samples: return None` (`:175-177`) | `if n_removed_samples > samples.shape[0]/100.0: log.warning("…not be suitable for error propagation…")` — `analysis_results.py:1643-1650` |
| `np.nanpercentile(C, qlo/qhi)` (`:180`) | equal-tailed quantiles, `equal_tailed=True` default — `model_plot.py:80` |

Our comment at `:172-173` attributes the ">1% railed" rule to *astromodels*. It is not
astromodels'. It is **threeML's own, at `analysis_results.py:1643`** — we reimplemented the
rule and then mis-cited it. That is exactly the kind of thing the PI's rule exists to catch.

**Replacement.** `plot_spectra` accepts `subplot` (documented at `model_plot.py:60`, in
`_defaults` at `:96`, honoured by `SpectralContourPlot` at `:695-699`), so the native band
draws straight onto our own axes:

```python
from threeML import plot_spectra
plot_spectra(jl.results,
             flux_unit="erg2/(cm2 s keV)",
             ene_min=E[0], ene_max=E[-1], num_ene=len(E),
             confidence_level=0.68, show_contours=True,
             subplot=[ax], xscale="log", yscale="log")
```

Four things to check on the swap, none of them blocking:
1. **Units.** Native y is `erg²/(cm² s keV)`; our data points are keV²-based. Convert one or the
   other or the band sits ~15 decades off the points.
2. **Sample count.** Ours is `n_samples=400`; `MLEResults` defaults to 5000. The native band will
   be smoother, and slightly different at the percentile tails. Expected, not a regression.
3. **EAC nuisance norms.** Ours deliberately skips free params matching `cons_*` (`:160, 167`).
   `plot_spectra` propagates through the *source spectrum*, where EAC constants do not appear —
   so the native result is correct by construction, and our skip logic becomes unnecessary.
   **Verify on one joint NaI+BGO+LLE fit that the native band is not visibly wider.**
4. **Band suppression.** Our Shipping-Gate behaviour (2026-08-12, bn200524211) is to *refuse to
   draw* a band when >1% of samples rail. threeML only **warns**. That refusal is a project policy
   we should keep — implement it by checking `jl.results` for the railed fraction (or catching the
   warning) and skipping the `plot_spectra` call, **not** by keeping the whole reimplementation.

`scripts/41b_nufnu_display.py` imports `_rebin_for_plot` and `unfold_detector` from
`41` (`41b:71-73`) and does not carry its own band code — so fixing `41` fixes both.

### `ResidualPlot` as our canvas — **do not adopt** (deliberate)

`io/plotting/data_residual_plot.py:17` is genuinely unit-agnostic — `add_data` /
`finalize` take arbitrary y values and an arbitrary ylabel, so a nuFnu panel would render
on it. But it carries no scientific content, and our figure standard
(`scripts/plot_style.py`, F1–F13, enforced by `tests/test_figure_style.py`) is normative for
this project. Adopting `ResidualPlot` would subordinate a locked project style to threeML's
config system for zero physics. The PI's rule is about *capabilities*, not furniture.
(If ever revisited: `add_model_step` divides y by xwidth internally at `:147` — an easy trap;
and `add_data` forces `residual_yerr = 1` when `ratio_residuals=False` at `:203`, which
happens to match our unit-error-bar residual grammar exactly.)

### Summary table

| Function | Verdict | Native call |
|---|---|---|
| `unfold_detector` — the ratio unfold | KEEP-AS-BLESSED-EXCEPTION | none exists |
| `unfold_detector` / `_plugin_counts` — plumbing | KEEP-BUT-BUILD-ON-NATIVE | `pl.source_rate`, `pl.source_rate_error`, `pl.expected_model_rate`, `pl.energy_boundaries`, `Significance(...)` |
| `_rebin_for_plot` | KEEP-AS-BLESSED-EXCEPTION (rewrite the justification) | none; `_construct_counts_arrays` exists but groups on the model |
| `model_error_band` | **DELETE-AND-USE-NATIVE** | `plot_spectra(jl.results, flux_unit="erg2/(cm2 s keV)", subplot=[ax], ...)` |
| bin centres | BUILD-ON-NATIVE (idea) | count-weighted mean à la `SpectrumLike.py:3270-3309` |
| fit-time safety | NEW ACTION | assert `plugin._rebinner is None` before every fit in `scripts/10` |

---

## 4. Where the three searches disagreed, and which is right

**(a) What happens to AIC/BIC when a plugin is rebinned. `by-api` is right; `by-vocab` is wrong.**
`by-vocab` claimed `n_data_points` switches to `rebinner.n_bins` "so AIC/BIC change too" — i.e.
that the statistic stays consistent. `by-api` claimed the opposite: `get_number_of_data_points()`
ignores the rebinner and *that* is what feeds AIC. A full-tree grep settles it — `n_data_points`
is consumed **nowhere** in the statistics path; `joint_likelihood.py:384` and
`sampler_base.py:231` both call the method. PROBE after `rebin_on_source(50)`: property = 19,
method = 120. The hazard is the **de**-synchronisation, and it is real.

**(b) Where the display-rebin logic actually lives. `by-vocab` and `by-task` are right.**
`by-api` initially framed `display_spectrum_model_counts` as doing the display rebin. It does
not — it is a colour/layout wrapper that forwards `min_rate` to `plugin.display_model`
(`post_process_data_plots.py:368-385`); the engine is `SpectrumLike._construct_counts_arrays`.
This matters practically: the reusable seam is the **plugin method**, not the top-level function.

**(c) How serious the counts-vs-significance difference is. `by-task` is right, and its finding
changes the decision.** `by-api` and `by-vocab` both recommended adopting `_construct_counts_arrays`
as "the adoptable piece", treating the different criterion as a caveat. `by-task` found — and I
independently reproduced — that because the grouping vector is `expected_model_rate`, the **groups
move when the model changes**: PL 71, CPL 70, Band 76 on identical data. For our all-models
diagnostic panel that is disqualifying, not a caveat. **Do not adopt.**

**(d) `model_error_band` duplicates native code. Only `by-task` found it; verified, and it is the
highest-value item in this whole exercise.** Not a disagreement, a coverage gap in the other two
searches — both stopped at "does threeML give nuFnu data?" and never asked "does our file
reimplement anything else threeML ships?". Worth noting as a lesson about search framing: two of
three angles answered only the question asked.

**(e) The `NO_REBIN` sentinel. Only `by-vocab` found it; verified true, and harmless for us.**
`plugins/SpectrumLike.py:47` and `io/plotting/post_process_data_plots.py:38` each define their own
`NO_REBIN = 1e-99`, and `SpectrumLike.py:3243` tests it with the **identity** operator
(`min_rate is not NO_REBIN`). PROBE: `SpectrumLike.NO_REBIN is post_process_data_plots.NO_REBIN`
→ **False**. So `display_spectrum_model_counts(jl)` with no `min_rate` silently takes the
"build a fresh rebinner" branch and **ignores** any rebinner set on the plugin, while
`plugin.display_model()` with defaults honours it. We never rebin fit plugins, so there is no
impact on us — but it is one more reason never to read channel counts off a
`display_spectrum_model_counts` figure. (`scripts/34_example_spectra.py:108` passes an explicit
`min_rate=[5]*len(plugins)`, so it takes the same branch either way and is unaffected.)

**(f) Li&Ma NaN at zero background. Only `by-task` found it; verified.**
`Significance(Non=[172,180,5], Noff=[0,3,0], alpha=10).li_and_ma()` → `[nan, 4.25, nan]`. Relevant
the moment we act on the recommendation to delegate the sigma computation.

---

## What to tell the PI in one paragraph

We *are* using threeML, and after this audit we will be using more of it, not less. threeML has
no `eeufspec` — there is no code path anywhere in the package that puts a data point into a flux
unit, and the closest thing (`_construct_counts_arrays`) stops one multiplication short. So the
unfolding stays ours, legitimately. threeML *does* have a display-only rebinner, which I had
wrongly said it did not; but it groups on the fitted **model** rate, which makes the data points
move from panel to panel when we compare 24 models on one time bin (measured: 71 vs 70 vs 76
groups), and it has no max-group cap and no upper limits — so the significance grouping stays
ours too, on much better-argued grounds than before. The real finding is a third function nobody
asked about: our `model_error_band` reimplements threeML's own covariance→MVN→quantile error
propagation, including the ">1% samples railed" rule that our comment mis-credits to astromodels
when it is threeML's own line. That one gets deleted in favour of
`plot_spectra(..., flux_unit="erg2/(cm2 s keV)", subplot=[ax])`. Separately, and unrelated to
plotting: threeML's `get_number_of_data_points()` ignores the rebinner while the likelihood does
not, so a stray `rebin_on_source` before a fit would silently corrupt our ΔAIC — we should assert
against it in `scripts/10`.

---

# ADJUDICATION AT THE PRIMITIVE (Claude, 2026-08-13, after the search above)

The search's `model_error_band` = DELETE-AND-USE-NATIVE call is **upheld, and it is
worse than duplication — the function is numerically wrong.**

## The defect
`scripts/41_nuFnu_panels.py::model_error_band` draws its MVN with

    mean = [fp[n].value for n in names]        # EXTERNAL (linear) parameter values
    cov  = jl.covariance_matrix               # INTERNAL (transformed) space

astromodels applies a log10 transformation to positive-definite parameters. Measured
on freshly built components (`_transformation is not None`):

| model | transformed params | external | internal |
|---|---|---|---|
| Band | `K`, `xp` | 1e-4, 500 | -4, 2.699 |
| Cutoff_powerlaw | `K`, `xc` | 1, 10 | 0, 1 |
| Powerlaw | `K` | 1 | 0 |
| Blackbody | none | — | — |

threeML itself samples in internal space — `analysis_results.py:1571`
`values = [x._get_internal_value() ...]`, bounds from `_get_internal_min_value()`
(`parameter.py:748`, which returns `self._transformation.forward(...)` when a
transformation exists). We paired its covariance with the untransformed means.

## Consequences, measured on bn081125496 (real fits, engine-seeded)

**(1) Bands that ARE drawn are wrong.** The quoted σ of a transformed parameter is a
σ in dex read as if it were linear:

| blk | model | param | external | σ we use | σ that is true | factor |
|---|---|---|---|---|---|---|
| 7 | CPL | `xc` | 57.0 keV | 0.119 | 15.6 keV | **131x too narrow** |
| 0 | CPL | `xc` | 281.9 keV | 0.241 | 156 keV | **649x too narrow** |
| 2 | Band+PL | `xp` | 190.2 keV | 0.065 | 28.3 keV | **438x too narrow** |

bin7 is the one panel of the nine that shows a grey 68 % band. That band is not a
68 % band.

**(2) Bands are suppressed for the wrong reason.** Replicating the function's own
rail test faithfully (it skips `cons_*` EAC nuisances), external vs internal mean:

| blk | model | ours (external) | 3ML (internal) |
|---|---|---|---|
| 0 | CPL | **191/400** | **8/400** |
| 2 | Band+PL | 236/400 | 206/400 |
| 7 | CPL | 0/400 | 0/400 |

191/400 and 236/400 reproduce the montage run log exactly, so the replication is
faithful. Block 0's band was suppressed by our bug: correctly sampled it rails 8/400,
comfortably inside the 1 % rule, and was drawable all along.

**(3) A real fit finding, separable from the display bug.** Block 2's railing is
mostly genuine: `K_2` (the additive power law) sits at 1.0002e-15 against its 1e-15
floor. That component is the entire reason the engine prefers Band+PL over Band on
this block. BOUND_CAPPED, L9 — belongs in the fit review, not here.

## Containment — the stored numbers are NOT affected
`scripts/10` takes parameter errors from `jl.get_errors()` (MINOS, native, line 734)
and never builds an MVN. `model_error_band` is called only at
`41_nuFnu_panels.py:331` and `:538`, both display paths. So: **no catalogued
parameter, error, AIC or flux is touched by this.** The damage is confined to the grey
band on the νFν figures — wrong where drawn, absent where it should have been drawn.

## Action
1. Delete `model_error_band`; propagate with threeML's own machinery (`jl.results` /
   `plot_spectra(..., flux_unit="erg2/(cm2 s keV)", subplot=[ax])`), keeping our
   Shipping-Gate refusal-to-draw as a policy check *around* the native call.
2. Add to the 41b adjudication list: 41b was briefed to reuse scripts/41's helpers by
   import, so unless it replaced this function it inherits the bug.
3. Regression test: assert that for a component with a transformed parameter, the
   band's width in that parameter matches the native propagation, not `sqrt(Cii)`.

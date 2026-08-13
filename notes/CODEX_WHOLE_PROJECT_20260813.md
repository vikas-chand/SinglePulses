# CODEX whole-project audit — Two_Breaks — 2026-08-13

## Verdict

**DO NOT SIGN OFF.**

The spectral engine contains several sound repairs, and two important checks succeed: the `bn150721242` per-bin response fallback preserves interval identity for the demonstrated case, and the independent Khushboo comparison really is below `0.6 sigma` for alpha, Ep, and beta. Those successes do not make the current system publishable. The current T90 Monte Carlo samples a different, positively biased estimator from the reported T90; the population path does not enforce its own class, burst-admission, bin-adequacy, and all-band rules; the significant-BB census is not a complete or uniquely defined census; canonical spectral panels can use a different detector set, reference detector, interval, or table row from the engine; and one LLE row remains explicitly pending human approval while being used in fits.

This is a system-level rejection, not a judgement that all engine rows are wrong. The engine tables are currently more trustworthy than the downstream figures and prose, but they are not yet a frozen, provenance-complete basis for paper numbers.

## Audit frame and reproducible baseline

- Repository HEAD: `42a2a9c145f1...`.
- All seven artefact hashes in the brief were recomputed and matched, including engine SHA-256 `af053a99a6ce1a3c...` and handbook `temporal.py` SHA-256 `c715198b94610c61...`.
- I froze the live-sweep evidence at **2026-08-13 04:33:44 UTC**: 67 non-empty fit tables whose mtimes preceded the freeze, 611 rows (544 resolved and 67 `T_INT`). The combined sorted path-plus-SHA-256 manifest hash is `f9a2b75d14abb13c1a356286e63209440ab426e728cb07260338636f395cd6f1`. Later-arriving sweep products are excluded from all frozen-census numbers below.
- `pytest tests/ -q`: **3 failed, 78 passed, 1 xfailed**, reproduced without writing pytest caches or bytecode.
- `scripts/43_catalog_validator.py`: **436 rows, 20 adjudicated accepted overrides, 0 unadjudicated**.
- `tests/test_lessons.py`: **33 passed, 1 xfailed**. The pass count materially overstates its coverage; see C1.
- A 04:53 UTC inventory, before later sweep arrivals, found 70 sweep fit tables, 71 complete six-figure step sets, 71 montages, 62 P0 freezes, 54 harvest manifests, 49 step-1 QC tables, 13 doctrine-guide files, and 238 corpus PDFs. `Skills_training/corpus_index.csv` has 177 data records (178 physical lines including the header). These are moving-state counts, not final campaign denominators.
- At a separate **04:55:02.655 UTC** campaign-log snapshot (log SHA-256 `a64f16dc1e72f11f2df2e2123e1a1f137df4439fafd47673d8afbf1583335f5b`), 71 bursts were recorded as exit-zero completions, but only 70 had matching fit ECSV/JSON products. That frozen log state is used only in D2; the live file subsequently grew.
- The working tree was already dirty because the live campaign and user artefacts were present. I did not alter them. This report is the only file written by this audit.

## A. Correctness of the analysis chain

### A1 — NOT CONFIRMED: two tests are stale, one correctly exposes a real open gate

The three failures have different meanings.

1. `test_ordering_and_source_in_gap` is a **stale test**. Its 20 failures are exactly the 20 accepted human overrides in `results/human_review_qc_flags.txt`, with no additional row.
2. `test_margin_band` is also a **stale test**. It fails on the same 20 rows and no others. A legitimate convention that predictably fails CI is itself a test defect.
3. `test_approval_stamps` is a **real catalog defect/open gate**, not an accepted gap override.

The 20 rows that both stale tests reject are:

| Trigger | Detector row(s) |
|---|---|
| bn090530760 | n1, b0 |
| bn100614498 | n6, b1 |
| bn101126198 | b1 |
| bn110605183 | b0 |
| bn110920546 | b0 |
| bn110928180 | b0 |
| bn120905657 | n7, na |
| bn171210493 | b0 |
| bn180723757 | b1 |
| bn190401139 | b1 |
| bn200524211 | b0 |
| bn220525008 | b0 |
| bn221209243 | n1, n5 |
| bn230802285 | n5 |
| bn240204630 | b1 |
| bn241223506 | b0 |

Representative recomputed `(pre gap, post gap)` values are bn090530760/b0 `(5.338, -136.002)` s, bn100614498/b1 `(-1.598, 6.598)` s, and bn230802285/n5 `(41.218, -9.218)` s. These are not being re-flagged as catalog bugs: they are precisely the ledgered overrides.

The one real approval failure is:

| Field | Value |
|---|---|
| `TRIGGER_NAME`, `DETECTOR` | `bn120624933`, `lle` |
| `APPROVED_BY` | `Claude (AI)` |
| `APPROVAL_MODE` | `ai_inherited_PENDING_HUMAN` |
| `APPROVED_UTC` | `2026-08-08T21:28:00Z` |
| `WINDOW_SOURCE` | `inherited from n0; LLE bkg NOT independently reviewed` |

The engine includes LLE in this burst's fit rows, so the open gate is scientifically active. It must be human-reviewed and stamped, or LLE must be excluded under a typed quality reason until approval. Adding the pending mode to the test allow-list would conceal, not fix, the defect.

**Exact test fix:** make each adjudication bind the exact source/gap values or a catalog-row hash, and waive only the named source-overrun inequality. A pair-only `(trigger, detector)` allow-list could conceal a later, unrelated change to that row. Continue to enforce internal interval ordering and every non-overridden margin side. Replace the current free-text comma parser as well: commas inside `[gap lo, hi]` currently create 20 valid detector tokens plus 20 spurious numeric tokens. Use structured ECSV/JSON or a detector-ID regex.

### A2 — NOT CONFIRMED overall; identity is confirmed for bn150721242

The specific MF-3 repair works for the target case:

- Requested block 0: `[-0.8036799431, 0.9400070608]` s.
- First n6 DRM start: `+0.0639660358` s relative to trigger.
- Batched conversion failed; per-bin retries returned blocks 1–7.
- Each returned plugin carried its own interval. Endpoint differences from the requested blocks were only `3.6e-8`–`6.9e-8` s.
- The walkthrough table contains blocks 1–7, not block 0, and each row has `PLUGIN_DETS=n6,n7,n8,nb,b1`.

Because the destination slots start empty and are filled by each plugin's own `tstart/tstop`, unique separated intervals are not positionally shifted or double-counted. The demonstrated uncovered block is correctly omitted.

The fallback is nevertheless not production-safe:

- It catches every `Exception` and calls it `RESPONSE_UNCOVERED`. A covered bin that fails for another reason is printed under the wrong permitted omission class and remains absent from structured outputs.
- ThreeML can catch `NegativeBackground` internally and omit a plugin; the engine records only an aggregate count, not a detector/block/reason ledger.
- The 0.5 ms identity tolerance has no uniqueness assertion, while the campaign already contains sub-ms intervals.
- A fully absent block disappears from the ECSV; only JSON `n_blocks` hints that something is missing.

**Exact fix:** catch `IntervalOfInterestNotCovered` specifically, re-raise unexpected exceptions, require a one-to-one unique interval mapping, and serialize an exclusion row `(trigger, detector, block, exact interval, reason)` for every omitted plugin or block. Missing reference material must fail loudly.

### A3 — NOT CONFIRMED: the union repair is narrow, but the claimed census is incomplete

Frozen recomputation over the 67 tables, excluding `T_INT`:

| Quantity | Recomputed value |
|---|---:|
| Passing Band+BB/Band arms | 61 |
| Passing CPL+BB/CPL arms | 137 |
| Passing arms in total | 198 |
| Unique operational detections `(burst, block)` under the uncalibrated project rule | 152 |
| Bursts with at least one | 43/67 |
| Blocks passing both arms | 46 |
| Above-temperature candidates rejected by child validity | 20 |
| Additional CPL+BB candidates at `kT≈1.0`, also invalid | 2 |

The implemented narrow rule does use the union of the Band and CPL nested arms, requires `LRT >= 9.2`, applies child `VALID`, and excludes the lower kT rail. The exact L27 floor for bounds `(1, 200)` is

`10 ** (0.01 * log10(200)) = 1.0544119031 keV`,

so `1.0544` is the correct four-decimal threshold. Its truncation is harmless because the exact child-validity geometry is also applied.

The ten bursts in `results/walkthrough_night_summary_v2.json` have **zero overlap** with the frozen/current sweep set, so the requested direct comparison cannot be made. This is a coverage gap, not a numerical mismatch.

`fig_step9` consults both arms but stops at the first passing arm. Four of 46 dual-pass blocks change L28 class with continuum choice:

- bn090530760 block 4: edge-marginal versus in-band;
- bn100122616 block 3: edge-constrained versus edge-marginal;
- bn110920546 block 4: edge-constrained versus in-band;
- bn130310840 block 4: edge-constrained versus in-band.

The engine also fits nested +BB pairs that the current census ignores. Applying the same raw `delta N2LL >= 9.2`, valid-child, off-rail test gives:

| Nested arm | Passing arms |
|---|---:|
| CPL+BB+PL / CPL+PL | 96 |
| Band+BB+PL / Band+PL | 35 |
| SBPL+BB / SBPL | 26 |
| SBPL+BB+PL / SBPL+PL | 19 |
| CPL+BB+CPL / CPL+CPL | 17 |
| Band+BB+CPL / Band+CPL | 16 |
| SBPL+BB+CPL / SBPL+CPL | 6 |

Those arms occupy 122 unique blocks and add 12 beyond the current 152, producing 164 under an expanded conditional-BB definition. SBPL+BB alone adds bn111017657 block 7 and bn210803497 block 2. Both 152 and 164 are operational arithmetic counts, not calibrated component detections: BB normalization lies on a boundary, kT is unidentified under the null, and searching multiple continua/pairs adds multiplicity. Pooling three-component comparisons would additionally require a predeclared chain gate and response-folded null calibration; it should not be done ad hoc.

**Exact fix:** define the estimand first. Either rename the present number “Band/CPL-baseline BB census,” or serialize generic LRTs for every registered exact parent-child pair and use one centralized registry rule. For dual-arm class disagreements, store both results and classify as continuum-dependent rather than taking the first.

### A4 — NOT CONFIRMED: current T90 errors are invalid and can change paper numbers

The new implementation is in `calculate_t90`, not the generic `calculate_duration`; T50 still uses the older rough path. Four independent failures are present:

1. `scripts/40_temporal_survey.py` builds the curve over the full pre-background-start to post-background-stop range. The approved source window controls bin width, not the duration search interval.
2. The input is already background-subtracted. `max(net_counts, 0)` is not a Poisson mean: rectification creates a positive noise floor, drops the raw-count variance, and omits background-fit covariance.
3. The point cumulative sum has downward steps, so `np.interp` receives a non-monotonic `xp`. The Monte Carlo curves are monotone only because they use the rectified estimator, and their plateaus still need an explicit crossing convention.
4. `n_mc=200` leaves several-percent numerical uncertainty in the reported uncertainty.

Direct production-path demonstrations:

| Burst | Negative/downward bins | Signed counts | Rectified counts | Reported T90 | Same code's MC center | External GBM 50–300 keV |
|---|---:|---:|---:|---:|---:|---:|
| bn081224887, n9 | 660/1533 | 17,456.89 | 22,614.97 (+29.55%) | `19.0443 ± 0.9461 s` | `108.465 s` | `16.448 ± 1.159 s` |
| bn110721200, n9 | 468/1120 | 17,481.06 | 21,225.95 (+21.42%) | `15.4431 ± 0.8909 s` | `55.758 s` | `21.822 ± 0.572 s` |

The external values come from the published GBM catalog and combine several detectors in 50–300 keV; this is an external sanity check, not an exact replication of the pipeline's one-detector 8–900 keV measurement. A closer single-n9 50–300 keV recomputation gives `17.4029 ± 1.3079 s` and `14.1095 ± 2.1890 s`, respectively. The [official HEASARC GBM burst-catalog description](https://heasarc.gsfc.nasa.gov/W3Browse/fermi/fermigbrst.html) confirms the catalog's duration method and nominal energy band.

The decisive internal contradiction is independent of the external comparison: the uncertainty distribution is centered at 108.5 or 55.8 s while the point estimates are 19.0 or 15.4 s. It is sampling a different estimator.

With 20,000 realizations, the two MC sigmas are `1.02312` and `0.92468 s`; the fixed 200-draw values are lower by 7.5% and 3.6%. Across 100 alternative 200-draw seeds, sigma has means/SDs `1.01835/0.05632 s` and `0.91725/0.03071 s`. For an ideal sample standard deviation, approximately 800 draws give a roughly +/-5% 95%-confidence half-width and about 5,000 give +/-2%.

A fixed seed does not bias an expectation by itself. Resetting the same seed for each burst freezes one noisy estimate and reuses the same deterministic stream, creating avoidable dependence potential across bursts; this audit did not measure the resulting correlation. The scientific bias comes primarily from rectifying a background-subtracted residual and using different point and MC estimators.

**Exact fix:** carry raw counts, exposure, fitted background, and background covariance into the duration estimator; simulate raw source-plus-background observations, refit or sample the background per realization, and use the same explicitly monotone quantile-crossing estimator for point and MC values inside a declared search/source window. Use and record a deterministic per-trigger seed and `n_mc >= 1000` after a convergence study. Because the point cumulative/search window are also invalid—and T50 remains on the broken generic path—do not publish the current T90 or T50 estimates or uncertainties.

### A5 — NOT CONFIRMED: labels are safer, but panels are not faithful displays of stored fits

The parameter-name audit succeeded:

- `mode=best` selects the stored `BEST_AIC_MODEL`; it does not independently choose another family.
- All 24 `pmap` short names occur exactly once in their constructed astromodels component.
- Band+BB maps `alpha_1,xp_1,beta_1,K_1,kT_2,K_2` correctly.
- CPL+BB+PL maps `index_1,xc_1,K_1,kT_2,K_2,index_3,K_3` correctly.
- Contrary to the stale `_row_seed` docstring, normalizations are stored and applied.
- The known bn200524211 block-7 panel does carry `PANEL!=ENGINE dAIC=+6`.

The path still fails the intended invariant because it rebuilds plugins and minimizes the named model again. The label can be the engine's family while the displayed curve comes from a different minimum or even a different effective dataset:

- `scripts/45_all_products.py::approved` removes LLE, while the engine auto-adds it. Ten of the frozen completed bursts used LLE in every engine row and already had montages generated without LLE.
- The product driver chooses the smallest detector angle as the effective-area reference; the engine's serialized `reference_det` differs in 47/67 frozen bursts.
- Boundaries are rounded to four decimals. bn120905657 block 3 is only `1.6987e-5 s` wide and becomes a zero-width interval.
- Engine rows are keyed at two-decimal `(tstart,tstop)`. `T_INT` collides with block 0 for bn100614498 and bn130215063, allowing a dictionary overwrite.
- No assertion binds `PLUGIN_DETS`, reference detector, exact intervals, background catalog, blocks file, or code hash to the engine row.
- `aic_stamp` lets `NaN` differences bypass the check (`abs(NaN)>2` is false), misses parameter/curve divergence at `|dAIC| <= 2`, and does not compare validity. Infinite drift does stamp. Formatting also turns `2.01` into `+2`.

**Exact fix:** key by integer `BLOCK` with a distinct `T_INT`; load ECSV and JSON together; use exact edges, `PLUGIN_DETS`, and `reference_det`; include LLE if the engine did; and assert hashes before plotting. Current tables do not serialize fitted effective-area/LAT nuisance values or full covariance, so spectral parameters alone cannot reproduce folded predictions, residuals, ratio-unfolded points, or uncertainty bands. Serialize and apply the complete best-fit nuisance vector/covariance, or generate and hash panels inside the engine before that state is lost. If refitting is retained, call it a refit and fail on non-finite AIC, validity, parameter-distance, detector/reference, provenance, or identity disagreement.

## B. New scripts

### B1 — NOT CONFIRMED: several step figures state a different analysis from production

**Step 3 background.** `scripts/44_step_figures.py::polyfit_bkg` fits 0.128-s total-TTE bins with an unweighted reduced-SSE degree-0–3 choice. The production engine uses ThreeML background handling: 1-s bins/exposure, a total-count Poisson likelihood-ratio order choice, then per-channel Poisson fits. For bn081224887, the figure chose degrees `3/3/3/1` for n6/n7/n9/b1; the production log chose `0/0/2/0`. This is the exact forbidden estimator-mismatch failure class. Steps 3, 5, and 7 therefore do not visualize the production background.

**Step 7 channel mapping.** The present mapping is numerically correct only for the currently audited files: all 1,549 NaI TTE files had EBOUNDS `CHANNEL=0..127`, and no event channel was out of range. Nevertheless, `emid[np.clip(ch,...)]` silently maps corrupt or noncanonical channels onto an endpoint. It must map PHA through the FITS EBOUNDS `CHANNEL` column, assert complete and unique coverage, and use a predeclared mutually exclusive channel-boundary convention.

**Step 7 durations.** Across 106 bursts times five bands, 520 curves were evaluable and **507/520 (97.5%)** had a non-monotonic cumulative; ten more were skipped. For example, bn081125496 at 350–1000 keV has 21 negative steps and a normalized cumulative range `-0.0957..1.4146`. These panels are not valid T90 measurements.

**Step 9.** Its raw margin `min(AIC_simple)-min(AIC_extra)` has the intended positive sign, and thresholds 6/10 match the scorecard convention, but negative simple-model wins are plotted instead of being represented as zero evidence for extra structure. In the 71-table live snapshot, 358/558 resolved rows were negative (`-5.953..-0.025`). The code does not use the canonical registry chain/top-two rule. Its BB union also takes the first passing arm, causing the four continuum-dependent classes listed in A3.

**Exact fix:** serialize the production background prediction/coefficients/covariance and duration products rather than re-estimating them in a figure script; assert FITS channel identity; and create one shared evidence helper called by both the scorecard producer and step 9.

### B2 — NOT CONFIRMED: the product manifest is existence-based, not honest

The driver discards subprocess return codes and primarily tests `exists()`. It can count an empty, corrupt, stale, wrong-provenance, or placeholder file as present. It checks the fit ECSV but not the companion JSON. It expects Ep-kT products even when fewer than two valid rows make “not applicable” the correct outcome, and it assumes every enumerated bin has a panel even when a quality-excluded/no-plugin bin is legitimate.

More seriously, its `approved()` helper removes LLE and does not carry LAT, so products can be generated from a different dataset than the engine. Thirteen catalog bursts have LLE rows; ten frozen completed fits include LLE. One sampled `PRODUCTS.md` (bn081125496) happened to have 21/21 non-empty parseable files, but the code does not enforce that invariant.

**Exact fix:** validate schema, parseability, nonzero content, expected page/image count, semantic status, companion JSON, and input/output hashes; preserve subprocess return codes; distinguish `PRESENT`, `N/A(reason)`, `FAILED(reason)`, and `STALE`. Construct each panel from the row's ECSV `PLUGIN_DETS` plus the serialized reference detector; extend JSON provenance to record attempted/included/excluded bands per block, because current JSON `fit_dets` omits dynamically appended LAT.

### B3 — NOT CONFIRMED operationally; the shared worker is behaviorally identical

The good part is real: `scripts/46_temporal_all106.py` imports the exact `survey_one` function from script 40. For the 89 roster overlaps, the arguments are identical; the 17 extras are fed through the same function, not special-cased:

`bn090530760, bn100614498, bn101126198, bn110605183, bn110920546, bn110928180, bn120905657, bn171210493, bn180723757, bn190401139, bn200524211, bn210812699, bn220525008, bn221209243, bn230802285, bn240204630, bn241223506`.

The operational wrapper is broken on macOS spawn. The dynamically imported module is not registered under an importable name; `pickle.dumps(survey_one)` raises `PicklingError`. The wrapper catches individual failures and can exit zero after a partial or total failure.

**Exact fix:** put the worker in a normally importable module, add a spawn-mode integration test, require exactly 106 terminal records or an explicit typed exclusion, write atomically, and return nonzero if any result is absent.

### B4 — NOT CONFIRMED: the cross-system diff can confuse binning with parameter disagreement

- Intervals are rounded to 0.01 s and stored in a dict, so collisions overwrite. Across 643 extant non-sweep tables/6,163 rows, 41 bins are narrower than 20 ms; the minimum width is `1.699e-5 s`. Existing examples differ by only 2.435 ms (bn081222) or 0.805 ms (bn111017) and can false-match.
- Literal `T_INT` is treated as a match even when the underlying windows differ.
- Intersection-only denominators can report 100% agreement while most bins are unmatched.
- The script compares standalone Band parameters regardless of either system's winner, validity, or common model.
- Its sigma distance assumes independent Gaussian symmetric errors despite shared photons, asymmetric errors, covariance, and rails. NaN comparisons can leave the “worst” score at zero.
- The divergence prose can call same-verdict/different-winner a bin-2 issue without testing model degeneracy; its grade variable is dead.

**Exact fix:** bind both systems to provenance and block-file hashes; match exact block IDs when inputs agree, otherwise use an overlap assignment with unmatched bins in the denominator; compare a common valid model or an explicitly transformed physical quantity; propagate covariance/asymmetric errors; and separate binning divergence, optimization divergence, and model-class divergence.

## C. Doctrine versus implementation

### C1 — NOT CONFIRMED: the lesson suite is nominal, and several claimed controls are not in force

`tests/test_lessons.py` loads only five fixed audit-era tables, not current sweep output. Its 34 cases come from ten named tests and several use `pytest.skip` when artefacts, columns, or rows are absent—the opposite of the required fail-loud behavior. Two tests are mislabeled: nominal L11 tests DSBPL break ordering although current L11 is RUNS/CUSUM residual logic; nominal L13 tests bin edges although current L13 is burst-level component admission. The L16 map recognizes only 9 of 24 model prefixes; 53/575 resolved winners in the live snapshot therefore pass unchecked. The sole xfail is an old b6-v2 displaced-curve symptom, not a current direct engine test.

Lesson-by-lesson audit:

| Lesson | Current state |
|---|---|
| L1–L3 | Procedural/manual; no actual engine or test gate for frame choice, per-bin LAT statistics, or similar decisions. |
| L4 | **Partial.** 10 MeV cutoff floor and unconditional cutoff grid exist; per-plugin likelihood decomposition and validity versus maximum LAT photon do not. A code comment incorrectly says 100 MeV. No direct test. |
| L5 | **Core engine fix confirmed** for BandxCut/SBPLxCut unconditional multistarts; no regression test. |
| L6 | **Absent.** No count/N2LL bin-adequacy floor; `_n_data` is used only for BIC. Decisive near-empty bins can enter population counts. |
| L6b | **Absent/pending.** Stage-2 significance is reference-NaI, not joint-fit significance. |
| L7 | Procedural comparison rule only. |
| L8 | **Partial/stale claim.** DSBPL has unconditional ordered seeds; DSBPLfree does not and is omitted from generic parent restarts. In the live snapshot 13/554 converged (`STATUS=OK`) DSBPLF fits are >0.5 N2LL worse than a converged SBPL, maximum 8.54. These are optimization diagnostics, not 13 selectable valid children: only two children were physically valid and none of those had a valid parent in the frozen audit. |
| L9 | Bound caps and `BOUND_CAPPED` are serialized, but selection proceeds and population scripts ignore the stamp. No enforcement test. |
| L10 | Panel generator exists; “mandatory for every reconciliation block” is not a gate, and B2 shows why existence is insufficient. |
| L11 | **Not implemented.** No production RUNS/CUSUM diagnostic; nominal test is unrelated. |
| L12 | Registry helpers exist, but scripts 31, 33, 44, and 47 use bespoke model maps/raw margins. Class-aware reporting is not in force. |
| L13 | Admission/track functions exist but have no callers. Engine evolution selects per-bin physically valid Band+BB fits directly, without an LRT/significance condition or burst-level admission; nominal test is unrelated. |
| L14 | No heading exists in doctrine. |
| L15 | Manual derived-quantity rule; not mechanized. |
| L16 | **Inconsistent.** Figure 44 grades 6/10; `model_registry` chain/top-two gates at 10; scripts 31/33 use BB LRT 14; current BB scorecards use LRT 9.2. Engine emits no canonical grade/evidence ratio. Test ignores 15 model prefixes. |
| L17 | **Not in force.** The authoritative driver always requests BGO, but LAT remains operator opt-in. Twelve frozen completed bursts meet the engine's on-disk LAT test, yet zero ECSV `PLUGIN_DETS` rows contain LAT. (JSON `fit_dets` is not evidence here because it omits dynamically appended LAT.) LLE has no attempted/excluded ledger. |
| L18 | **Partial; literal claim false.** Simple families restart; BB/composites are conditional and DSBPLfree has none. Regressed converged (`STATUS=OK`) children remain: 13 DSBPLF>SBPL, 2 SBPLBB>SBPL, 5 BandPL>Band, and 6 CPLPL>CPL cases in the live snapshot. These counts diagnose incomplete optimization; they are not all physically valid/selectable. In the frozen audit the both-valid subsets were 0, 0, 1, and 1, respectively. |
| L19 | Core negative-LRT invalidation/stamp works for the three emitted LRTs; test coverage is indirect and limited to old tables. |
| L20 | `restore_best_fit` is called before derived curves; core repair confirmed. Exceptions are swallowed and curves still compute. The test is a symptom heuristic and xfails one stale table. |
| L21–L23 | Manual source/frame/primitive rules; not mechanized. |
| L24 | **Promised algorithm absent.** T_INT is fitted first and seeds blocks; there is no second-pass flux-weighted resolved-kT T_INT refit. The motivating row improved for another reason, so the nominal test now no-ops. |
| L25 | No production `xb/(3.92 kT)` track/correlation computation. |
| L26 | No heading exists in doctrine. |
| L27 | Log-geometry gate and exact kT floor are implemented. Test imports the gate directly but tests Band Ep only, not kT/all bounded families. |
| L28 | Dual-input classifier and boundary behavior are implemented and directly tested. **Open MF-2 remains:** class is not serialized, quarantined, or enforced downstream. Code uses 3.92 while prose says 3.9207, numerically negligible but not exact. |

The highest paper-number risks are L6/L6b, L12/L13, L17, L18, and L28. The exact repair is to make the model registry the only population path; serialize class/admission/adequacy/band-attempt records; implement unconditional family restarts and a child-not-worse-than-exact-parent invariant; and rewrite lesson tests around direct fixtures/current products with no skips for missing required references.

### C2 — NOT CONFIRMED overall: the population-mean correction is right, but one source audit is false

I rendered and visually inspected all nine pages of [Qin et al. (2013)](/Users/salim/Desktop/Projects/SingleRest/Two_Breaks/Skills_training/Qin_2013_2013ApJ76315Q_PUB.pdf), not merely the derived note.

- **Population-mean rule confirmed.** Qin forms a typical `Tbar90` from a Gaussian fit to the log-T90 population in each energy band and reports `Tbar90 proportional to E^(-0.20 +/- 0.02)`. It is not a per-burst law.
- **091010/090910 typo confirmed.** Figure 1's panel and body text identify GRB 091010; its caption says GRB 090910.
- **Hardness-ratio audit confirmed as under-signposting.** The body first defines the BATSE ratio 100–350/25–50; Figure 4's caption gives the GBM/BATSE comparison ratio as 100–350/50–100. The GBM denominator is introduced too late, but this is not an internal numerical contradiction.
- **1:6.5 audit is false.** Table 2 gives GBM short:long `39:253 = 1:6.49`, and the main text says 1:6.5. However, the conclusion explicitly says **1:5**. The reference note's statement that “No 1:5 appears anywhere” is wrong.
- **Block reproducibility gap confirmed.** The paper does not state the Bayesian-block fitness, prior, `ncp_prior`, `p0`, or false-alarm setting.

The Qin note and Temporal doctrine must explicitly record the conclusion's 1:5 inconsistency rather than declaring universal 1:6.5 consistency. A separate unresolved source issue also remains: the paper treats KMM probabilities below 0.05 as rejecting a single Gaussian in the two lowest bands while prose elsewhere says low-energy bimodality is rejected.

### C3 — NOT CONFIRMED: ShippingGate is mostly aspirational

No implementation outside the guide writes or validates the required `VERIFIED_BY`, `VERIFIED_UTC`, or `CHECKLIST_VERSION` fields. There is no central command whose success gates publication.

Mechanized fragments are:

- lesson tests, albeit with the C1 coverage problems;
- the catalog validator and human-override ledger;
- the panel AIC drift stamp, with the A5 blind spots;
- syntax/import smoke checks.

Still dependent on someone remembering are fresh-context visual review, full label-to-table comparison, input/code hash provenance, page/layout/style checks, external anchors, frame labels, provisional/tie language, ADS/source checks, and final verification stamps.

**Exact fix:** implement one `shipping_gate` command with typed schema validators and a hash-bound JSON attestation. The publish/product wrapper must refuse to succeed without it; manual items must be explicit signed records, not prose checkboxes.

## D. Campaign integrity

### D1 — NOT CONFIRMED: one sampled P0 contains demonstrable post-fit leakage

Twelve of 62 P0 files were sampled across eras. The time delta below is current P0 mtime minus current fit-table mtime. A negative value is consistent with blind-first timing; a positive value only means the present filesystem mtime is later and is not proof of original creation chronology.

| Burst | Delta | Audit result |
|---|---:|---|
| bn090530760 | -1590 s | literature-only; no detected leakage |
| bn090620400 | -3309.5 s | no detected leakage |
| bn170114917 | -3917.1 s | no detected leakage |
| bn180728728 | +7206.3 s | disclosed post-fit archival P0 |
| bn150306993 | +6651.7 s | literature content; timing not blind proof |
| bn151021791 | +5713.9 s | literature content; timing not blind proof |
| bn150213001 | +1270.1 s | disclosed archival P0 |
| bn170921168 | +132 s | disclosed archival P0 |
| **bn150721242** | **+55.8 s** | **actual leakage** |
| bn081125496 | -2449.6 s | no detected leakage |
| bn090719063 | -2285.4 s | no detected leakage |
| bn100614498 | -1840.5 s | no detected leakage |

bn150721242's P0 copies current fit values to the displayed precision: alpha `-0.546491 -> -0.55`, Ep `30.000 -> 30`, kT `4.4304 -> 4.4`, LRT `29.8316 -> 29.8`, and winner `SBPLfree`; it even says `POST-FIT`. This record must be excluded from blind-prediction scoring and labeled `POST_FIT_NONBLIND`.

No other sampled file showed direct value leakage, but mtime ordering is not a commitment protocol. **Exact fix:** create P0 atomically before fitting, hash it into an append-only ledger, and require a status enum (`BLIND_FROZEN`, `ARCHIVAL_POSTFIT`, `NONBLIND_CONTAMINATED`). Downstream blind scorecards must reject anything but the first state.

### D2 — NOT CONFIRMED: one exit-zero “completion” produced no fit

At the 04:55:02.655 UTC log snapshot bound above to SHA-256 `a64f16dc...`, 71 bursts were recorded complete; 70 had corresponding parseable fit ECSV/JSON files. The sole false success was the known bn100130729, but its cause is now demonstrated:

- approved source interval: `58–97 s`;
- spectral blocks: `62.237–81.154 s`;
- all available RSP2 first matrices begin at trigger `+139.267 s` and extend to `+475.145 s`;
- TTE itself covers about `-32.4..300.7 s`.

Every science block is outside response coverage, so the engine finds no plugin, writes no fit table, and exits zero. An older montage remains and can be mistaken for a current product. The step-1 QC already says `FAIL`, so this is not an ambiguous scientific outcome; it is an orchestration/status defect.

**Exact fix:** preflight response coverage against every requested block, regenerate/fetch a covering DRM when possible, otherwise emit `NO_USABLE_RESPONSE` with a quality ledger and non-success product state. An all-block failure must not exit as fit success. Product manifests must invalidate stale outputs by input/code hashes. Also rename the sweep-log fields: current `blocks=0 fit=0 montage=0` values are subprocess exit codes, not product counts.

### D3 — NOT CONFIRMED / COULD NOT COMPLETE A COLD RERUN

I selected completed bn110721200 and froze its current artefacts:

- fit ECSV SHA-256 `a8ae9d744b7a546d47560fead789897127c929c6d76ff84231de231f3c6b129c`;
- fit JSON `9ac4c8cfd561b37d7e68e297b1c5f505fd59dc00dc281a5d8fc9740713bfa999`;
- exact sweep blocks `results/sweep106/bn110721200/blocks/bb_blocks_spectral_bn110721200.ecsv`, SHA-256 `78b8f8202be47f6769646edcdf09d3b4f59a43ecd4e03e2799385986884bf982`;
- catalog `4a2343bb921e1f1428bb3bb82f957277d71aade3cf0e0f9b3ccc52134feae938`;
- engine `af053a99a6ce1a3cb4d9c2764e6a5d177729d3e397739995d99c980e7fa323c9`.

I did not launch a cold heavy-tier fit because the brief allows writing only this report and explicitly warns not to contend with the live 12-way sweep. Existing historical bn110721 tables are not substitutes: they were generated with different menus/inputs/code and have different hashes.

Code inspection does not guarantee exact reproduction. Central multistart starts are explicit, so the optimum should normally reproduce; however, ThreeML/astromodels covariance-error sampling calls unseeded `np.random.multivariate_normal`, and the fit JSON does not bind code, environment, catalog, blocks, responses, and raw data by hash. Exact byte equality is therefore not currently promised.

After adding provenance and deterministic seeds, an appropriate acceptance rule is exact model winners outside declared AIC ties, `|delta N2LL| <= 1e-3`, parameters within `1e-4` relative or `0.01 sigma` (whichever is looser), and separately tested stochastic uncertainty summaries. This item remains unverified until a cold run in an isolated output root is diffed against the frozen hashes.

## E. Claims approaching paper numbers

### E1 — NOT CONFIRMED: several current manuscript claims are false, not merely stale

The manuscript is allowed to be provisional. Provisional marking does not make a statement true when the current products contradict it.

Claims confirmed from current products/source records:

- 106-burst roster.
- 24-model menu partitioned as 4 one-break, 5 added-low-energy, and 15 high-energy composites.
- Evidence-ratio anchors: `exp(6/2)=20.09` and `exp(10/2)=148.41`.
- Learning-curve figure currently covers eight walked bursts.
- The published lag anchor `+7.08 +/- 0.45 s` and recorded internal `-5.99 s` sign inversion.
- For the eighth burst: alpha reaches about `+0.6`, Ep is monotonically hard-to-soft in the recorded track, and no bin has strong extra-structure evidence after the L27 repair.
- The unrequired kT comparison is approximately 52 versus 54.6 keV.
- 22 sample overlaps with the Lu temporal catalog, the planned 25-burst benchmark size, and six tracked raw-data sample bursts.

Claims now false:

| Manuscript claim | Recomputed state |
|---|---|
| “Each burst is analyzed blind” | False: bn150721242 P0 contains exact post-fit values; several P0s are explicitly archival/post-fit. |
| “A human approves every step, every approval stamped” / no system approval | False: Stage-1 catalog has 433 `human_gui`, 2 `ai_vision`, and 1 `ai_inherited_PENDING_HUMAN`; the pending LLE row entered fits. |
| “First ten walkthroughs” / “Ten bursts have been walked” | False as an end-to-end record claim: the complete ledger contains eight; b9/b10 lack complete P0–P6/ledger records. |
| “Twenty-seven lessons ... each with an executable test” | False as written. There are 27 spectral lessons, but 34 distinct guide headings overall (27 spectral, 5 Data Inventory, 2 GCN); the ledger has 33 rows/32 IDs, duplicates L6, and omits L28. C1 shows most are not executable enforcement tests. |
| “Unconditional multistarts for every family” | False; see C1 L18. |
| Soft burst Ep `~50–140 keV` | False lower bound: current track is `35.636–136.019 keV`. |
| Before L27 most blocks preferred extra structure; after none | The “after” no-strong-extra statement is true. The “before preferred” wording is false/misleading: 4/6 simple fits were invalid, so extra families won by forfeit rather than measured preference. |
| bn130518580 low-energy break and BB peak track at the “few-percent level across eleven bins” | False. Current 11-bin sweep gives correlation `r=0.80938` and median signed ratio `1.00753`, but median absolute fractional difference is `10.270%`; only 1/11 bins is within 5%, range `0.8–89.6%`. |
| The production fitting step is deterministic in a broad reproducibility sense | Not established and too broad; D3 identifies unseeded uncertainty sampling and absent provenance. |

Quantitative/historical claims that are **unsupported by a reproducible current artefact**, and therefore may not be stated as demonstrated facts yet:

- five identical reruns with exactly zero spread;
- “found and fixed five engine defects” as a uniquely classified count (the ledger mixes more categories);
- three retracted claims with a complete trace;
- the manufactured `5.6 sigma` incident;
- the 24 historically documented-failure corpus;
- the asserted post-2020 human versus 2015–2019 agent-operated arm.

These are not called stale merely because the manuscript predates two days of work. They are either contradicted by present products or lack the audit artefact needed to support the claim. The exact repair is to generate the manuscript's quantitative statements from hash-bound campaign tables and replace unsupported history with a cited incident ledger.

### E2 — NOT CONFIRMED overall; the <0.6 sigma headline is exactly confirmed

For the `T_INT` row, the current engine fit is:

| Parameter | Engine | Khushboo independent | Combined-sigma distance |
|---|---:|---:|---:|
| alpha | `-0.7548525 ± 0.0556713` | `-0.710 ± 0.068` | `0.51037 sigma` |
| Ep | `252.4125 ± 28.5933 keV` | `228.7 ± 30 keV` | `0.57216 sigma` |
| beta | `-1.8932822 ± 0.0902301` | `-1.862 ± 0.091` | `0.24411 sigma` |

I recomputed each as `abs(x1-x2)/sqrt(sigma1^2+sigma2^2)`. **All three are below 0.6 sigma.** The engine's SBPL/Band AICs are `6782.1448/6782.5129`, a `0.3681` tie, so this agreement should not be inflated into a unique-family claim.

The published-frame primitives were independently checked against the archived [Fermi GBM GCN 27809](https://gcn.nasa.gov/circulars/27809), [Konus-Wind GCN 27867](https://gcn.nasa.gov/circulars/27867), and the local [Ghosh et al. preprint](/Users/salim/Desktop/Projects/SingleRest/Two_Breaks/Skills_training/Ghosh_2026_2026arXiv260809704G_bn200524211.pdf), rather than only against the derived verification record. The five-frame proximity/rank claim is false. Recomputed values include:

- GBM: `(1.159, 1.844, 1.297)` sigma — record correct.
- Ghosh `[-1,40]`: `(1.843, 3.203, 3.173)` — record correct.
- Ghosh `[-1,15]`: `(1.000, 1.498, 1.654)`, not `(0.84,1.50,1.72)`.
- Konus directional 90%-confidence errors converted by `1.64485`: `(0.0395, 0.9157, 1.5634)`, not `(0.04,0.90,1.08)`.

Mean-sigma order is Khushboo `0.4422`, Konus `0.8395`, Ghosh-15 `1.3841`, GBM `1.4331`, Ghosh-40 `2.7398`; it does **not** rank monotonically by frame proximity. Preserve the strong `<0.6 sigma` independent-operator result, correct the frame table, and delete the proximity-ranking interpretation unless a predeclared multivariate frame metric supports it.

## Ranked discrepancies and exact fixes

### Tier 1 — can directly change paper numbers

1. **Invalid duration likelihood/estimator (A4, B1).** Rebuild from raw counts plus background covariance, one monotone point/MC estimator, source-window restriction, calibrated MC size, and per-trigger seed; regenerate all temporal products.
2. **Population doctrine is not connected to products (C1 L6/L12/L13/L17/L18/L28).** Centralize model classification, evidence, admission, adequacy, detector-band attempts, and quality exclusions in one registry-backed table; refit LAT-eligible/all-band cases and rerun population products.
3. **BB census is incompletely defined (A3).** Predeclare the nested-pair universe and chain/multiplicity rule, serialize every exact LRT, handle continuum-dependent classes, and recompute the census. Until then call the number Band/CPL-baseline only.
4. **Panels/products can use different data from the engine (A5, B2).** Rebuild from exact JSON detector/reference inventory, exact block IDs/edges, stored parameters, and hash provenance; invalidate current mismatched montages.
5. **Active unapproved LLE input (A1).** Obtain the human decision for bn120624933/LLE or exclude it under a typed quality record, then refit that burst.
6. **T_INT source-window provenance remains incomplete.** The engine generally fits the block union (or one of only two reviewed override rows), not the approved `SRC_START/SRC_STOP`. Make approved source columns the authoritative T_INT window, serialize it, and refit T_INT claims.

### Tier 2 — can misclassify evidence or silently omit data

7. **Broad exception-to-`RESPONSE_UNCOVERED` conversion (A2).** Catch only the coverage exception and serialize every omission; fail everything else.
8. **No-plugin exit zero/stale products (D2).** Add response preflight, typed terminal states, non-success semantics, and hash-based stale invalidation.
9. **Figure 44 uses a non-production background and invalid T90 (B1).** Consume serialized production estimators; do not reimplement science in the renderer.
10. **Cross-system interval matching is lossy (B4).** Use provenance/block IDs or explicit overlap assignment and report unmatched bins.
11. **Temporal all-106 wrapper can pickle-fail and exit zero (B3).** Move the worker to an importable module and enforce 106 typed terminal outcomes.

### Tier 3 — auditability and claim-integrity blockers

12. **Blind-first leakage (D1).** Hash/freeze P0 before fits and exclude nonblind records from blind scoring.
13. **Lesson tests overclaim coverage (C1).** Replace old-table heuristics/skips with direct engine fixtures and current hash-bound outputs.
14. **Shipping gate is prose (C3).** Implement a blocking command and signed/hash-bound verification attestation.
15. **Manuscript contains false/unsupported counts and episode claims (E1/E2).** Generate claims from authoritative products and an incident ledger; retain only the verified `<0.6 sigma` headline.
16. **Qin source note falsely says no 1:5 appears (C2).** Correct the note/doctrine and preserve the actual source inconsistency.

## Could not verify

- A3's requested sweep-versus-night-summary comparison: there were no overlapping bursts at the frozen snapshot.
- D3 exact cold reproducibility: prohibited by the report-only write contract and unsafe during the live heavy sweep. It requires an isolated fresh output root after the campaign stops.
- A final all-106 population count: the sweep was still writing. All census values in this report are bound to the 67-table frozen manifest.
- Exact equivalence to external GBM T90 values: the external catalog uses a different band and detector combination. It is an external sanity anchor, not a reproduction of this pipeline.
- Several historical manuscript incident counts (five zero-spread reruns, three retractions, 5.6-sigma episode, 24-failure corpus): the necessary primitive artefacts were not present, so self-referential prose was not treated as evidence.

## Independent judgement beyond the brief

1. **The T_INT window is still not the approved source window.** This known audit item remains active in the production engine and affects every time-integrated paper comparison unless an override happens to exist.
2. **Response coverage in step figures is checked by an outer min/max envelope.** That can present a gap between DRM matrices as covered. Coverage must be tested against the union of valid matrix intervals for every science bin.
3. **The project has no single estimand authority.** “Significant BB,” “strong evidence,” “best model,” and “admitted component track” have several script-local implementations and thresholds. This is the structural reason fixed engine logic keeps diverging again downstream.
4. **Success is currently a process exit code, not a scientific terminal state.** The same defect appears in the spectral sweep, temporal wrapper, and product manifest. A production campaign needs a small typed state machine: `VALID`, `QUALITY_EXCLUDED(reason)`, `FAILED(reason)`, `N/A(reason)`, and `STALE(provenance)`.
5. **Absence is too often treated as permission to continue.** Required references, rows, plugins, and tests sometimes skip or disappear. The project's own fail-loud rule should be implemented once and shared by tests, engine, campaign driver, product generator, and shipping gate.

## Sign-off condition

Do not bless paper numbers merely when the live sweep reaches 106. Sign-off requires, at minimum: close the pending LLE gate; repair and regenerate temporal products; freeze the nested-pair/population estimand; enforce class/admission/adequacy/all-band records; rebuild provenance-faithful panels; obtain a clean ledger-aware test run; cold-reproduce at least one burst from hash-bound inputs; and run a mechanized shipping gate over the frozen final manifest.

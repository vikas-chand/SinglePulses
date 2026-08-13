# Skill: Temporal (Step 7) — T90/T50, MVT, lag, pulse fits

**Purpose:** the per-burst temporal measurements (durations, minimum variability timescale,
spectral lag, pulse morphology) from the SAME approved Stage-1 selections that drive the
spectroscopy. **Audience:** anyone running `scripts/40_temporal_survey.py` or reading
`results/temporal_catalog_human.ecsv`.
**⚠ STATUS: the weakest step of the pipeline.** Codex's audit verdict — the temporal numbers
*"should not be used scientifically"* until the defects below are fixed — stands. This skill
documents the method AND the defect ledger; quoting a temporal number without checking the
ledger is a fake pass.

## Inputs
```yaml
trigger:   bn<XXXXXXXXX>
stage1:    results/background_intervals.ecsv    # approved dets + bkg windows
data:      data/<trigger>/glg_tte_<refNaI>_*    # reference NaI TTE
env:       LIGHT tier (numpy/astropy) — no threeML needed
chain:     ~/Desktop/Projects/GRB_Handbook_Project/grb_pipeline/analysis/temporal.py
           (vendored handbook: analyze_single_pulse = T90 -> MVT -> lag -> pulse)
```

## Outputs
`results/temporal_catalog_human.ecsv` — one row per burst: T90/T50 (+errs), MVT-Haar, lag,
Gowri pulse parameters (A, s_l, s_r, r_l, r_r), φ = s_l/s_r, R², class.

## The four measurements
1. **T90/T50** — cumulative background-subtracted counts between 5%/95% (25%/75%);
   errors from **Poisson realizations of the RAW counts minus the fitted background, the
   same estimator as the point value, inside the approved source window** (n=1000,
   per-trigger seed, explicit first-crossing convention) — `scripts/40::_tx_with_mc`,
   audited 2026-08-13; see the defect ledger for the two earlier broken versions.
2. **MVT** — Haar-wavelet cross-check in this chain; the CANONICAL MVT is Bala's
   `mvt_runner` run separately (the upstream Bala code was NOT adoptable unmodified —
   repaired fork; the old classifier is quarantined; LATBright-era MVT MC numbers are
   unsafe. Memory: `project_mvt_audit_2026-07-18`).
3. **Spectral lag** — asymmetric-Gaussian peak of the band-band CCF, Monte-Carlo errors.
   ⚠ **SIGN CONVENTION INVERTED — see defect ledger.**
4. **Pulse fit** — the Gowri+2025 two-sigmoid:
   `I(t) = (A/4)·[1−tanh((t−r_r)/s_r)]·[1+tanh((t−r_l)/s_l)]`, asymmetry φ = s_l/s_r
   (φ<1 = FRED-like). Protocol adopted EXACTLY from the paper: rebin to ≤300 bins
   (`_GOWRI_MAX_BINS`), accept only R² ≥ 0.7 (`_GOWRI_R2_MIN`), and **require r_l ≤ r_r**
   — the handoff that said `r_l ≥ r_r` was wrong and would have collapsed every pulse
   (caught against the paper verbatim: *"we always require rl ≤ rr"*). Fit `dr = r_r − r_l ≥ 0`
   as the parameter, never the raw pair.

```bash
# full-sample survey (12-core cap):
python scripts/40_temporal_survey.py
```

## Frame rule: T90 is BAND-DEPENDENT — correct before diffing (Qin+2013, verified 2026-08-09)
Comprehensive Analysis III (`2013ApJ...763...15Q`, published PDF on disk) measures
**T̄₉₀ ∝ E^(−0.20 ± 0.02)** for long GRBs across six GBM sub-bands. Consequence: a harder-band
instrument reports a SHORTER duration for the same burst, lawfully.
Live demonstration (bn090530760): GBM catalog 157.7 s (8–1000 keV) vs Suzaku-WAM 113 s
(50 keV–5 MeV). Band-centre ratio ⇒ predicted factor ≈ 0.72; observed 113/157.7 = **0.72**.
What looked like three inconsistent durations was one burst obeying one power law.
**RULE:** never diff a published T90 against ours without the E^−0.2 band correction (an L21
frame-alignment item with a number attached). Cite Qin+2013; note their caveat that bright-burst
samples give steeper (−0.4, Bissaldi+2011).

### ⚠ CORRECTION (Vikas's Qin reading, 2026-08-13; PDF-verified same day)
**The exponent is a POPULATION-MEAN relation, not a per-burst law.** Their §Figure 7 fits
`T̄₉₀` — the *sample mean* T90 — against the central energy of each band; the slope
−0.20 ± 0.02 describes how the population average moves, and says nothing about the scatter
of any single burst around it. Our rule above applies it to INDIVIDUAL bursts (bn090530760
matched to 0.72 — a good outcome, but one draw from a distribution whose width we never
measured).
**Consequences, binding from now on:**
1. A band-corrected T90 diff is a CONSISTENCY CHECK with population-level scatter attached,
   never a precision prediction. Never call a residual mismatch a discrepancy on the strength
   of E^−0.20 alone.
2. To use it per-burst we must measure the per-burst relation ourselves — `scripts/40` already
   computes T90 per band, so the campaign's own multi-band T90s give both the population slope
   AND its scatter. Do that before the frozen numbers are quoted.
3. **Their T90 is count-space by their own statement** — verbatim: *"Our calculation is done
   purely in count space. Since the GBM is constantly slewing in orbit, this method could skew
   the T90 estimation for long GRBs."* The GBM catalog instead accumulates response-corrected
   photon fluence. So a Qin-vs-catalog T90 difference can be METHOD, not band (a T9-class
   coverage/estimator distinction). Label which space every harvested T90 lives in.
4. Source audits (resolved 2026-08-13 against the PDF; full record in skill reference 22):
   the HR "inconsistency" is **under-signposting, not contradiction** — the 25–50 keV
   denominator is quoted as the legacy BATSE definition (Kouveliotou+1993), the Fig. 4 caption
   states the 50–100 keV denominator actually plotted for GBM; their GBM hardness is
   model-derived from GCN spectral parameters, not counts. The `091010`/`090910` clash is a
   CAPTION typo (text + panel label say 091010). The short:long ratio 1:6.5 (39:253) is
   internally consistent. **Genuinely open:** Table 2's soft-band P_KMM (2.25e−2, 5.9e−4)
   reject one Gaussian under their own `P<0.05` rule while the text says bimodality is
   rejected — do not inherit; and the paper NEVER states its Bayesian-block fitness function
   or prior, so Figure 1 is not reproducible from the paper alone.
5. Their σ_T90 combines separate t5/t95 Monte Carlo spreads in quadrature; t5 and t95 come
   from the SAME cumulative light curve and are correlated. Our MC must form
   `T90^(j) = t95^(j) − t5^(j)` per realization and take the spread of that distribution
   directly (covariance included by construction). Check `scripts/40`'s estimator against this
   before quoting any T90 error.

## L29 — the T90 SEARCH WINDOW dominates the error budget; our quoted σ is ~10× too small  *(bn081125496, 2026-08-13; Vikas: "should we start from background subtracted rates without marking tstart or tstop by ourselves?")*
Measured directly on bn081125496 by sliding only the search-window STOP:

| window stop (s) | T90 (s) | MC error |
|---|---|---|
| 9.90 | 7.84 | ±0.14 |
| 11.90 (**the approved window**) | **8.65** | ±0.20 |
| 14.90 | 9.59 | ±0.29 |
| 17.90 | 10.01 | ±0.43 |

**The statistical error is ~2%; the window-choice systematic is ~25%.** Every T90 we
quote carries an uncertainty an order of magnitude smaller than the choice that
actually sets it.

**Root cause — a window doing two jobs.** `SRC_START/SRC_STOP` is a **spectroscopy**
selection: a human choosing an interval that captures the emission for fitting. We
then reuse it as the **duration search interval**, which is a different job with a
different optimum. A wide window is harmless for spectroscopy (extra background bins
add noise, not bias) but T90 grows with it, because the 95% point drifts into the
tail as more of the noisy decay is admitted.

**RULES:**
1. A quoted T90 states its search window. Two T90s measured over different windows
   are not comparable — this is the T9/component-coverage rule applied to duration.
2. The MC error is the STATISTICAL error only. Until a window systematic is measured
   per burst, do not present T90 ± σ_MC as the total uncertainty.
3. **Before any T90 population result**, run the window-sensitivity scan per burst and
   quote σ_window alongside σ_MC (a scan of ±2 s costs ~1 s of compute per burst).
4. Related open choice: a genuinely data-driven interval (extend until the cumulative
   flattens within noise, à la the catalog method) would remove the human choice but
   introduces its own convergence criterion. Not adopted; **measure the sensitivity
   first**, then decide with numbers.

**Also now recorded per burst** (Vikas's second request): the MC keeps the full t5 and
t95 DISTRIBUTIONS, not just a spread — `T90_ERR_LO/HI` (16th/84th percentiles, so
asymmetry shows), `T5_SD`, `T95_SD`, and `T5_T95_RHO`, the realised correlation
between the two edges. bn081125496: ρ = +0.083, so quadrature (0.188 s) and the
covariance-correct value (0.182 s) differ by only 1% here — Qin's quadrature
approximation is mild for THIS burst, but ρ is now measured per burst instead of
assumed.

## L26 — LAG SIGN is a systematic trap: state the convention, verify against a known burst  *(2026-08-10)*
Two independent instances, one ours and one published:
1. **Ours:** the handbook lag sign is INVERTED (defect ledger above) — caught only by cross-check.
2. **Lu+2018 (`2018ApJ...865..153L`), published ApJ, verified in the PDF:** the text states t_p is
   *"negatively related to the photon energy E"* — i.e. HIGH energy peaks EARLIER, low energy later,
   the conventional positive lag — and then the very next sentence says the opposite: *"the pulse
   profile in a lower energy band tends to **peak earlier**"*. One of the two is wrong; the trend
   statement and their own positive τ̂₃₁ values (e.g. +7.08 s for bn090530760) say the sentence is.

Two instances make it a class, not a slip. Sign errors survive refereeing because both conventions
are "obvious" to their users and neither is usually written down.
**RULE:** (a) every quoted lag carries its convention explicitly — *positive lag = low-energy
photons arrive LATER* is ours; (b) validate the pipeline's sign on a burst with an unambiguous
published direction before any lag science; (c) when diffing a published lag, check the paper's
OWN internal consistency (trend statement vs prose vs table sign) rather than assuming.
**TEST:** `test_L26_lag_sign_on_reference_burst` — pending the handbook sign fix.

## 🔴 Defect ledger (check BEFORE quoting any number)
| defect | evidence | state |
|---|---|---|
| **T90/T50 errors** | `T90_ERR > T90` in 84/89 (orig); then a WRONG FIX | ✅ **FIXED PROPERLY 2026-08-13** after the Codex whole-project audit (item A4). History worth keeping: the original estimator resampled BIN INDICES, destroying time order. My first repair replaced it with Poisson draws of **rectified** counts `max(net,0)` while the point value still came from **signed** net — two different estimators: on bn081224887 the point value was 18.9 s and the MC distribution sat at **116.6 s**, so the quoted σ described something that was not T90. That is more dangerous than the original bug, which at least looked broken. **The real fix (`scripts/40::_tx_core` + `_tx_with_mc`):** search window = the approved SOURCE window (declared); point and MC call the SAME estimator; realizations are Poisson draws of the **RAW** counts (non-negative by construction) minus the same fitted background — no rectification of a residual; explicit first-crossing convention because the cumulative net curve is NOT monotonic (so `np.interp` was invalid); n_mc=1000; deterministic PER-TRIGGER seed. Adds `T90_WINDOW_TRUNCATED` when t5/t95 land on the window edge (then T90 is a LOWER LIMIT, not comparable to a catalog T90). Validation vs frame-matched external values: bn081224887 14.84±0.39 (ext 17.40±1.31, 1.9σ); bn110721200 13.24±0.36 (ext 14.11±2.19, 0.4σ). ⚠ NOT propagated: background-model uncertainty (polynomial held fixed) — stated, not hidden. |
| **bn130310840 committed row is a FAILED fit** | T90 = 17.91 ± 68.24 s vs 2.09 s blind re-run and ~2.4 s published | OPEN — refit + replace row |
| **Lag sign inverted** | handbook lag sign convention opposite to the standard (positive = soft lags hard) | OPEN — fix at source, then re-survey |
| MVT: only the Haar cross-check is in the catalog | canonical Bala MVT runs separately | by design — label which MVT you quote |

**Rule:** any use of `temporal_catalog_human.ecsv` states which columns it used and which
ledger entries apply. The catalog is survey-grade scaffolding, not results.

## Quality checklist
- [ ] Reference NaI + background windows come from the APPROVED catalog, never re-derived.
- [ ] Pulse fit: r_l ≤ r_r enforced via `dr ≥ 0`; R² ≥ 0.7 or the row carries no φ.
- [ ] T90 sanity: `T90_ERR < T90` and T90 within ~2× of the block-span — else flag, don't record
      (the bn130310840 lesson: a failed fit sat in a committed catalog for weeks).
- [ ] Lag: state the sign convention next to every quoted value until the source fix lands.
- [ ] MVT: label Haar vs Bala. They are different estimators; do not mix in one column.
- [ ] Cross-step: temporal window ⊆ Stage-1 source window (D4: never assume trigger = start).

## Common pitfalls
- **Bootstrap error > value** means the bootstrap is resampling noise, not the burst — treat as
  measurement failure, not a large error bar.
- **φ compared across papers**: Gowri's φ is s_l/s_r of the SIGMOIDS, not rise/decay time
  ratio — do not diff against Norris asymmetries without a mapping.
- **Lag–MVT plans**: this territory is a REDO, not a discovery (Sonbas+2013; Göktaş+2025
  slope 1.01) — see memory `project_lagmvt_is_a_redo` before proposing science here.
- **Blind-first applies here too**: the temporal chain runs before reading the published
  T90/lag; the P3 diff then attributes mismatches (the 120624933 T90 "mismatch" was a FRAME
  difference — episode 3 vs whole burst — not an error).

## Hand-off
Step 9 QC (`qc_flagging.md`) consumes the catalog with the ledger; the lag–Ep/lag–MVT science
projects (#37, #38) are BLOCKED on the defect ledger clearing, by design.

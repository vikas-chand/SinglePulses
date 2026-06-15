# Failed Spectral Fits — Diagnosis (2026-05-16)

Diagnosis-only document. No re-fits were performed; no scripts were modified.

## Headline counts (`results/spectral_fit_results.ecsv`)

| Status | # bins | # GRBs |
|--------|--------|--------|
| `OK`            | 837 | 99 |
| `BAND_ONLY_OK`  |   8 |  6 |
| `FAILED`        |   2 |  2 |
| **Total**       | **847** | **101** |

`FAILED` ⇔ both BB+Band and Band-only fits raised an exception or returned
no convergence (`06_spectral_fitting.py:358-364`).
`BAND_ONLY_OK` ⇔ only the BB+Band fit failed; Band-only converged.

The histogram `plots/failures_histogram.png` is **mis-named** — it shows the
distribution of horizontal-line **failure counts** from Phase 2 (Busby &
Lazzati metric), not spectral-fit failures. The spectral-fit failure rate
is well under 1% and there is no dedicated failure plot.

---

## `FAILED` bins (BB+Band and Band-only both failed)

| GRB | Trigger | NaI | spec_num | Bin context (T90 = ?, # total bins) |
|-----|---------|-----|----------|-------------------------------------|
| GRB200524211 | bn200524211 | n0 | 10 | T90=37.8 s, 12 BB bins total (12 sig) |
| GRB120420858 | bn120420858 | n4 |  7 | T90=254.9 s, 8 BB bins total (4 sig) |

Both failures are **isolated**: the preceding and following bins in the same
GRB succeeded (see timeline check below). This is the classic signature of a
bad-seed convergence problem, not a data problem.

```
GRB200524211 timeline (FIT_STATUS per spec_num 1..12):
  OK OK OK OK OK OK OK OK OK FAILED OK OK
GRB120420858 timeline (FIT_STATUS per spec_num 1..8):
  OK OK OK OK OK OK FAILED OK
```

The previous-bin best-fit values feeding spec_num 10 of GRB200524211 were
`EP≈9961` (next to the upper bound 1e4) and `KT≈1.000` (at the lower bound
1.0); for GRB120420858 spec_num 7 the seed had `EP≈17.3` (a hair above the
lower bound 10) and similarly pinned parameters. In both cases the seed lay
on or beyond a parameter boundary set in `06_spectral_fitting.py:246-251`,
so the JointLikelihood minimiser starts inside an inactive region of
parameter space and the covariance step cannot be inverted.

**Category: seed-from-previous-bin pushed parameters onto a hard boundary.**
**Mode: minimiser exception (Hessian inversion / boundary clip).**

**Suggested fix (do not implement now):** when `prev_bb` or `prev_band` has
any parameter within, say, 1% of a bound, fall back to `DEFAULT_BAND_BB` /
`DEFAULT_BAND` constants instead of using the railed seed. A 2-line edit
inside `fit_time_bin()` around lines 230–231 of `06_spectral_fitting.py`.
Verify by re-running just those two bins.

---

## `BAND_ONLY_OK` bins (BB+Band failed, Band-only succeeded)

| GRB | NaI | spec_num | Likely cause |
|-----|-----|----------|--------------|
| GRB170114833 | n7 | 1  | 1st bin: no prev seed, defaults used; T90=29 s, 4 BB bins total, mean significance 12.5 — BB component weak/unconstrained |
| GRB210803497 | n2 | 1  | 1st bin: same defaults-only situation; T90=9 s, 7 bins, mean sig 31.9 |
| GRB160330827 | n9 | 1  | 1st bin: T90=42 s, 5 bins (3 sig); marginal significance |
| GRB210410037 | n6 | 1  | 1st bin: T90=48 s, 9 bins, sig 19.3 |
| GRB130427324 | n6 | 7  | mid-burst bin in a 65-bin sequence; flanking bins OK |
| GRB130427324 | n6 | 20 | as above |
| GRB130427324 | n6 | 24 | as above |
| GRB150202999 | n0 | 20 | mid-burst bin in a 21-bin sequence; flanking bins OK |

Two sub-patterns:

**(a) First-bin failures (4 of 8 cases).** Spec_num 1 has no `prev_bb` seed,
so `DEFAULT_BAND_BB` constants are used. The first bin is also typically the
rise of the pulse with the *lowest* S/N — the BB component is poorly
constrained on its own, the joint Hessian is near-singular, but Band-only
(4 params) is well-posed. **Category: low S/N + naïve initial seed.**

**(b) Mid-burst single-bin failures inside GRB130427324 (very bright, 65
bins, fluence near top of sample) and GRB150202999.** Flanking bins
converged with `KT≈1–5 keV` for GRB130427324 — i.e. BB is railing on the
low-kT boundary. Spec_num 7, 20, 24 are likely bins where the local Band
slope is steep enough that the BB component is mathematically degenerate
with a steepened Band low-energy curvature; the minimiser walks the BB into
the boundary and exception-exits. **Category: model degeneracy / parameter
near boundary.**

**Suggested fixes (do not implement now):**

- For (a): give spec_num=1 a more conservative seed (`kT=30 keV`, `xp=200 keV`)
  rather than the global default, and/or fit Band-only first then add BB
  with the Band fit as a seed. A 5-line edit around lines 229–232 of
  `06_spectral_fitting.py`.
- For (b): widen the kT lower bound (currently 1 keV at line 251) to e.g.
  3 keV — any "BB" with kT < 3 keV is below the GBM NaI threshold (~8 keV)
  and is fitting noise / Band curvature. This is consistent with Burgess
  2014, who imposes kT > a few keV.

---

## Latent "OK"-but-railed bins (worth flagging, not technical failures)

Among the 837 `FIT_STATUS=OK` rows, the parameter-railing rates are:

| Parameter | At bound | Bound | % of OK |
|-----------|----------|-------|---------|
| `ALPHA` at upper (3.0) or lower (−1.5) | 276 | `band.alpha.bounds = (−1.5, 3.0)` (line 247) | 33% |
| `EP` at lower (10) | 25 | `band.xp.bounds = (10, 1e4)` (line 248) | 3% |
| `KT` at lower (1) | 67 | `bb.kT.bounds = (1, 200)` (line 251) | 8% |
| `BETA` at lower (−5.0) | 114 | `band.beta.bounds = (−5.0, −1.6)` (line 249) | 14% |

These bins **passed** the success check (both BB+Band and Band-only
converged), but the listed parameter is unphysically pinned. A third of all
"successful" bins have ALPHA railed at the upper or lower bound, and 8%
have KT at the lower bound — both red flags for the Ep–kT correlation
analysis.

**Category: parameter at boundary — quiet model-selection problem, not a
hard failure.**

**Suggested filter for the publication sample:** drop any bin with ALPHA,
EP, KT, or BETA within 1% of any bound from the Ep–kT scatter and the
per-GRB α-fit. This is a "no script changes" filter applied at the
plotting/table stage. Roughly half of the OK bins may survive — Gor needs
to weigh in (see GOR_REVIEW_STATUS.md item 4).

---

## Schema notes (`spectral_fit_results.ecsv`)

Columns (definitive, from the file header):
`NAME, TRIGGER_NAME, DETECTOR, SPEC_NUM, TSTART, TSTOP,
K_BAND, ALPHA, ALPHA_ERR, EP, EP_NEG_ERR, EP_POS_ERR, BETA, BETA_ERR,
K_BB, KT, KT_NEG_ERR, KT_POS_ERR,
LOGLIKE_BBBAND, AIC_BBBAND, BIC_BBBAND,
ALPHA_BAND, EP_BAND, BETA_BAND, LOGLIKE_BAND, AIC_BAND, BIC_BAND,
DELTA_AIC, DELTA_BIC, FIT_STATUS, N_DATA_POINTS`

Unclear / potentially missing fields:

- **No flux columns.** `PLAN.md` Phase 4.2 asks for fluxes of Band and BB
  components per bin; nothing is stored.
- **No N_DATA_POINTS values visible.** Column exists in the schema, but in
  a spot check (e.g. GRB200524211) the field is empty/whitespace where awk
  expected a number — possibly because ECSV writes empty strings for `None`
  and the script's `result['N_DATA_POINTS'] = n_data if n_data is not None
  else 0` (line 366) is firing the `else` branch for many rows. Worth a
  separate verification pass.
- **No `BB_DETECTED` boolean.** ΔBIC is recorded, but the decision of
  "this bin has BB" is made (or not) downstream in `07_spectral_plots.py`,
  not persisted.
- **No fit time / iteration counter.** Useful for diagnosing slow-converging
  bins but not currently logged.

---

## TL;DR for Gor

10 out of 847 time-bin fits failed in some way. The 2 hard failures are
isolated single-bin glitches from bad seed propagation (easy fix, ~5 lines).
The 8 soft failures are mostly first-bin low-S/N or BB-at-boundary cases
(also fixable). The bigger concern is the **276 / 837 "OK" bins with ALPHA
railed and 67 / 837 with KT railed** — these contaminate the Ep–kT
scatter and need a stated filter before publication.

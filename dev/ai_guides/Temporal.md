# Skill: Temporal (Step 7) — T90/T50, MVT, lag, pulse fits

**Lesson IDs in this file are TM1–TM5** *(PI ruling 2026-09-02, verbatim: lesson IDs "should be
specific to the skills"; before that date these five carried L-numbers that collided with
SpectralFitting.md — each header keeps its old number as "(was Lnn)", and any record dated
before 2026-09-02 that cites L26/L29/L31/L32/L33 in a temporal context means the TM lesson).*

**Purpose:** the per-burst temporal measurements (durations, minimum variability timescale,
spectral lag, pulse morphology) from the SAME approved Stage-1 selections that drive the
spectroscopy. **Audience:** anyone running `scripts/40_temporal_survey.py` or reading
`results/temporal_catalog_human.ecsv`.
**⚠ STATUS: the weakest step of the pipeline.** Codex's audit verdict — the temporal numbers
*"should not be used scientifically"* until the defects below are fixed — stands. This skill
documents the method AND the defect ledger; quoting a temporal number without checking the
ledger is a fake pass.

**🔴 STALE-PENDING-REWALK (PI ruling 5, 2026-08-30, gate 1 of the Lane-A #21 bn110920546
walkthrough), verbatim:** "Temporal: NO all-106 sweep. #21's wf-temporal regenerates its own
T90/MVT/lag with the validated tools and REPLACES its rows in the catalog, keyed to the new
receipt. The two campaign-wide wrong columns (lag sign, MVT) get a STALE-PENDING-REWALK label
in the catalog header + a register row — every later burst repairs its own rows the same way,
as it is walked." **Caveat, verbatim:** "the committed catalog keeps its proven-wrong lag sign
and MVT for every burst not yet walked, so nothing downstream may quote
temporal_catalog_all106.ecsv for an un-walked burst — that's what the STALE label enforces
mechanically rather than by memory." Mechanics: `results/temporal_catalog_all106.ecsv` carries
`meta.stale_pending_rewalk` (label, ruling, the LAG_*/MVT_* columns it covers, the rule) and
`meta.rewalked_triggers`; a consumer may quote LAG_*/MVT_* only for a TRIGGER_NAME in
`rewalked_triggers` (NR-31 code guard in 48 / assembler / numbers-verifier). Preamble, verbatim:
"one burst at a time, repairs included: each burst fixes its own rows as it's walked, no
campaign-wide sweeps."

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
2. **MVT** — THREE estimators exist and are named on every quote (TM5, 2026-08-30):
   (i) **Bala** `mvt_runner`, run separately — the CANONICAL value (the upstream Bala code
   was NOT adoptable unmodified — repaired fork; the old classifier is quarantined;
   LATBright-era MVT MC numbers are unsafe. Memory: `project_mvt_audit_2026-07-18`);
   (ii) **CWT** — `scripts/47_mvt_cwt_crosscheck.py`, a verbatim import of LATBright
   s02g:351-514 (Vianello 2018 continuous-wavelet method; noise percentile 99.5, n_sim 1e4;
   declared deviations: LSQ poly-2 background on the approved windows, approved ref NaI,
   channel-centre energy cut), sidecar `results/mvt_cwt/<trig>_mvt_cwt.json`, role =
   EXTENSION cross-check, value is grid-quantized (dt·2^(k·dj)); (iii) **Haar** — the
   in-chain wavelet cross-check that populates `MVT_S/MVT_ERR_S/MVT_TYPE` in the catalog;
   `MVT_TYPE=detection` is a HAAR statement only. Precedence: Bala > CWT > Haar.
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

## TM1 (was L29) — T90 is measured INSIDE the approved source window, by decision; where emission continues past it, T90 is a LOWER LIMIT  *(bn081125496, 2026-08-13)*

**Vikas asked** whether t5/t95 should come from the background-subtracted rates
"without marking tstart or tstop by ourselves". Testing that produced a finding, and
my first diagnosis of it was WRONG — recorded here because the wrong version is the
tempting one.

**What I first claimed:** T90 grows with the search window (7.84 s at stop=9.9 →
10.01 s at stop=17.9) because the 95% crossing drifts into a noisy tail. **Vikas's
objection killed it:** on background-subtracted rates the extra bins scatter about
ZERO, so noise cannot systematically inflate the total.

**What is actually happening (measured, det na, 8–900 keV):**

| region | mean net rate | reading |
|---|---|---|
| PRE window (fitted) | +0.1 ± 9.3 cts/s | zero by construction |
| POST window (fitted) | −0.0 ± 3.5 cts/s | zero by construction |
| far tail 120–140 s | −1.5 ± 8.2 cts/s | **zero — the polynomial is good (the control)** |
| last 3 s inside the source window | +222.5 ± 22.5 | 10σ |
| **gap 11.9 → 30.0 s (in NO fit)** | **+43.3 ± 8.7** | **5σ, ≈780 net counts** |

The background model is sound; the burst simply **continues past the approved source
window**. The window-sensitivity scan was not measuring a systematic — it was the
estimator correctly finding more real emission each time the window opened.

**DECISION (Vikas, 2026-08-13): "so we better do with the start and stop we marked."**
T90/T50 are measured inside the approved source window. The window is a human
decision and is not re-derived by the temporal step.

**Consequences that must be stated wherever a duration is quoted:**
1. Ours is a **windowed T90**: the duration of the emission *inside the approved
   interval*. Where emission continues beyond it, T90 is a **LOWER LIMIT**.
2. It is therefore **not directly comparable to a catalogue T90**, which uses its own
   interval (and, for GBM, response-corrected photon fluence rather than counts).
   bn081125496: ours 8.50 ± 0.18 s vs Shao+2017's 9.28 ± 0.61 s — the difference is
   largely the tail we exclude by choice, not a disagreement about the data.
3. `TAIL_OUTSIDE_WINDOW_SIG` is recorded per burst: the significance of net emission
   in `[SRC_STOP, BKG_POS_START]`, the region belonging to no fit. ≥3σ means the
   window truncates real emission and the duration is a lower limit.
4. The same truncation applies to the SPECTROSCOPY: those counts are outside the
   fitted interval, so our spectral results describe the emission in the window, not
   necessarily the whole burst (T9 component coverage — say so in any P3 diff).

**Also implemented (Vikas's second request):** the MC keeps the full t5/t95
DISTRIBUTIONS, not just a spread — `T90_ERR_LO/HI` (16th/84th percentiles, so
asymmetry shows), `T5_SD`, `T95_SD`, and `T5_T95_RHO`, the realised correlation
between the edges. bn081125496: ρ = +0.083, so quadrature (0.188 s) and the
covariance-correct value (0.182 s) differ by 1% — Qin's approximation is mild here,
but ρ is now measured per burst instead of assumed.

## TM2 (was L33) — THE CATALOG T90 IS NOT A GROUND TRUTH: it is detector-specific and carries its own subjective choices  *(PI ruling, #21 bn110920546, 2026-08-31)*

**PI, VERBATIM** (asked whether the catalog T90 end at 165.9 s should be marked on the
step-4 panel, given that 58.7% of b0's amended background window lies inside it):

> "the reported values are also detector specific, and I think that's useful that someday
> we will look for it and do physical modeling and then get it done correctly; for now it's
> ok to jsut take what it is, by selecting visually and that is subjective (so the catalog
> people might have done so by selecting some part by themselves)."

**What this settles.** TM1 already says OUR T90 is a windowed LOWER LIMIT. TM2 says the
thing it is usually compared against is not an absolute either: a catalog T90 is computed
on a chosen detector set, in a chosen band, over a chosen background — the same class of
subjective choices this project makes at Stage 1 (see `background_selection.md`, PI ruling
2026-08-31: "all choices of background selection are subjective to the user"). The catalog
team "might have done so by selecting some part by themselves."

**Operative consequences.**
1. A windowed-vs-catalog T90 difference is a **FRAME COMPARISON, never an error** on either
   side — extend the existing L21/T9 frame discipline: name the detector set, band, and
   background convention on BOTH sides before any diff, and never write "discrepancy".
2. Percentages computed *against* a catalog T90 (e.g. "58.7% of b0's window lies inside
   T90") inherit that subjectivity. Quote them as **oriented context, not as measurements**.
3. It is therefore CORRECT, not lax, to leave the T90 end unmarked on the step-4 panel and
   to accept the visually-selected window as it stands: "for now it's ok to jsut take what
   it is". Marking it would imply a boundary the datum does not carry.
4. **Scoring:** the NR-40 concordance rule extends here — a duration difference against a
   catalog value is not an accuracy measure.
5. **Banked, not started:** physical background modelling is what would "get it done
   correctly" and make BOTH the background boundary and T90 objective — registry entry #47
   (see `background_selection.md` ruling block and `notes/PROJECTS_registry.md`).

**Standing on #21:** windowed T90 = 88.67 ± 0.82 s (LOWER LIMIT, TM1; 11.95σ of net emission
outside the window) vs GBM catalog 160.771 ± 5.221 s (50–300 keV). Under TM2 these are two
differently-framed, differently-chosen quantities — the gap is DEFINITIONAL. Report both with
their frames; claim neither as the burst's duration.

## TM3 (was L26) — LAG SIGN is a systematic trap: state the convention, verify against a known burst  *(2026-08-10)*
Two independent instances, one ours and one published:
1. **Ours:** the handbook lag sign is INVERTED (defect ledger above) — caught only by cross-check.
2. **Lu+2018 (`2018ApJ...865..153L`), published ApJ, verified in the PDF:** the text states t_p is
   *"negatively related to the photon energy E"* — i.e. HIGH energy peaks EARLIER, low energy later,
   the conventional positive lag — and then the very next sentence says the opposite: *"the pulse
   profile in a lower energy band tends to **peak earlier**"*. One of the two is wrong; the trend
   statement and their own positive τ̂₃₁ values (e.g. +7.08 s for bn090530760) say the sentence is.

Two instances make it a class, not a slip. Sign errors survive refereeing because both conventions
are "obvious" to their users and neither is usually written down.

**ROOT CAUSE FOUND (2026-08-15, prompted by Vikas: "did you follow the tool we developed
ourselves?"):** the handbook lag is a PORT of LATBright's `s02c_spectral_lag.py` (provenance
comments at temporal.py:1372,1402,1428 admit it) — but the DCCF was re-implemented from
s02c's DOCSTRING, whose formula is sign-flipped relative to the code (LATBright's own review
flagged this: LAG-10 "docstring CCF formula sign-flipped (code correct)"). temporal.py:1060
computes `Σ soft[i]·hard[i+k]`; s02c's code computes `Σ soft[n+τ]·hard[n]`. Numeric proof:
synthetic hard-peaks-at-1.0s / soft-at-1.2s gives +0.192 s (s02c) vs −0.192 s (handbook).
The port also degrades the estimator: AG-μ-on-observed + symmetric MC std (handbook) vs
MC MEDIAN + asymmetric 16/84 (s02c); no restricted peak search; mean-rate background.
**Lesson: a port must copy the CODE, never the documentation — documentation is a bug
vector (this is the false-corroboration principle applied to lineage).**
**FIX PATH:** correct temporal.py:1060-1062 to the s02c code formula (or call s02c
directly), adopt MC-median + 16/84, then re-survey all 106 LAG columns. Until then the
per-burst validated number comes from `scripts/47c_lag_latbright.py` (imports s02c
unmodified; convention POSITIVE = soft lags hard, Norris+1996).
**RULE:** (a) every quoted lag carries its convention explicitly — *positive lag = low-energy
photons arrive LATER* is ours; (b) validate the pipeline's sign on a burst with an unambiguous
published direction before any lag science; (c) when diffing a published lag, check the paper's
OWN internal consistency (trend statement vs prose vs table sign) rather than assuming.
**TEST:** `test_L26_lag_sign_on_reference_burst` — pending the handbook sign fix.

**VALIDATION CASE (b) FOUND — #21 bn110920546 (2026-08-30):** the catalog row carries
LAG_S = −5.250 ± 0.029 s, LAG_ACCEPTED = True (handbook estimator); `scripts/47c` on the same
burst gives **+0.715 s (−0.215/+0.244, window systematic 0.387 s; POSITIVE = soft lags hard,
s02c unmodified import;** `results/sweep106/bn110920546/bn110920546_step7_lag_latbright.json`);
Lu+2018 tabulates **+1.22 ± 1.27 s** for this burst — the published direction is unambiguous
and agrees with 47c. The shipped report (`REPORT_bn110920546.md:168`) printed the −5.250 value
WITH the standard-convention text "(positive = low-energy photons arrive later)" — a MISLABEL,
not a convention choice. Note the magnitude: negating −5.250 does NOT give +0.715, because the
handbook value is the μ of a split-normal fitted over the full offset grid, not the CCF peak
(LAG_SIGN_VERIFICATION.md, 2026-07-31, two skeptics, analytic + injection) — the column is
irreparable by sign flip and is STALE-PENDING-REWALK (banner; NR-31). #21's own rows are
replaced by its wf-temporal (ruling 5); no other row is touched.

## TM4 (was L31) — Two truncation flags, ONE rule: lower-limit language fires on their UNION  *(CONFLICT-4 / NR-33, #21 bn110920546, 2026-08-30 — PROPOSED pending PI)*
This file carried two truncation signals with no stated precedence: `T90_WINDOW_TRUNCATED`
(ledger row 1: t5/t95 land on the window edge) and `TAIL_OUTSIDE_WINDOW_SIG ≥ 3σ` (TM1 item 3:
net emission in the region belonging to no fit). They are different tests and disagree on real
bursts — #21 has `T90_WINDOW_TRUNCATED = False` and `TAIL_OUTSIDE_WINDOW_SIG = 11.95σ`
(2444 net counts), so a consumer that reads only the first quotes 88.67 ± 0.82 s as a
measurement when TM1 says it is a LOWER LIMIT. **PROPOSED RULE:** `T90 is a lower limit` ⇔
`T90_WINDOW_TRUNCATED OR TAIL_OUTSIDE_WINDOW_SIG ≥ 3`; scripts/40 emits a derived
`T90_IS_LOWER_LIMIT` column and every consumer keys on that single column (code layer, NR-33),
never on either flag alone. Pending the PI's word; until then quote #21's T90 as "≥ 88.7 s
(windowed; tail 11.9σ outside the window)".

## TM5 (was L32) — MVT has three estimators; name them, order them, and screen a DETECTION against the published limit  *(CONFLICT-3 / NR-32, #21 bn110920546, 2026-08-30)*
**What was found:** this file described only Haar (in-catalog) and Bala (canonical), yet the
products shipped a third value — CWT, `results/mvt_cwt/bn110920546_mvt_cwt.json`,
0.724 ± 0.058 s, "verbatim CWT from LATBright s02g", role "EXTENSION cross-check" — and
AgentArchitecture's step-7 roster already named all three. On #21 the catalog value
`MVT_S = 5.342 ± 0.107 s` (Haar, `MVT_TYPE = detection`) exceeds the PUBLISHED UPPER LIMIT
of Golkhou+2015 Table 2, Δt_min < 2.096 s for trigger 110920546, by 2.5×; the CWT value is
consistent with the limit; Bala was never run for this burst
(`results/mvt_upstream/run_step7/bn110920546/` holds only an empty `logs/`). Also:
`scripts/47_mvt_cwt_crosscheck.py`'s current sha (5452cb2169…) differs from the sha the CWT
sidecar recorded (abf1290f92…) — the sidecar certifies which code EXISTED, not which code
exists (NR-22 instance; re-run before quoting).
**Trap inside the published table:** `golkhou2015_table2.tsv` lists BOTH 110920338 (0.337 s)
and 110920546 (< 2.096 s) under the name "110920A" — match on the TRIGGER NUMBER, never on
the name.
**RULES:** (a) precedence Bala (canonical) > CWT (cross-check) > Haar (in-chain); a quote
names its estimator and, if it is not Bala, says why Bala is absent; (b) `MVT_TYPE=detection`
is a Haar-only statement and is never read as "the burst's MVT is detected"; (c)
PUBLISHED-LIMIT CONSISTENCY SCREEN (NR-32, admission gate, code layer): where a Golkhou+2015
row exists for the trigger number, an MVT DETECTION above the published upper limit is an
admission REFUSE with the reason written into the row — it may not enter a catalog as a
detection; (d) the MVT columns of the committed catalog are STALE-PENDING-REWALK (banner)
for every un-walked burst; #21's are replaced by its own wf-temporal with all three
estimators run and labelled.

## 🔴 Defect ledger (check BEFORE quoting any number)
| defect | evidence | state |
|---|---|---|
| **T90/T50 errors** | `T90_ERR > T90` in 84/89 (orig); then a WRONG FIX | ✅ **FIXED PROPERLY 2026-08-13** after the Codex whole-project audit (item A4). History worth keeping: the original estimator resampled BIN INDICES, destroying time order. My first repair replaced it with Poisson draws of **rectified** counts `max(net,0)` while the point value still came from **signed** net — two different estimators: on bn081224887 the point value was 18.9 s and the MC distribution sat at **116.6 s**, so the quoted σ described something that was not T90. That is more dangerous than the original bug, which at least looked broken. **The real fix (`scripts/40::_tx_core` + `_tx_with_mc`):** search window = the approved SOURCE window (declared); point and MC call the SAME estimator; realizations are Poisson draws of the **RAW** counts (non-negative by construction) minus the same fitted background — no rectification of a residual; explicit first-crossing convention because the cumulative net curve is NOT monotonic (so `np.interp` was invalid); n_mc=1000; deterministic PER-TRIGGER seed. Adds `T90_WINDOW_TRUNCATED` when t5/t95 land on the window edge (then T90 is a LOWER LIMIT, not comparable to a catalog T90). Validation vs frame-matched external values: bn081224887 14.84±0.39 (ext 17.40±1.31, 1.9σ); bn110721200 13.24±0.36 (ext 14.11±2.19, 0.4σ). ⚠ NOT propagated: background-model uncertainty (polynomial held fixed) — stated, not hidden. |
| **bn130310840 committed row is a FAILED fit** | T90 = 17.91 ± 68.24 s vs 2.09 s blind re-run and ~2.4 s published | OPEN — refit + replace row |
| **Lag sign inverted** | handbook lag sign convention opposite to the standard (positive = soft lags hard) | **ROOT-CAUSED 2026-08-15** (see TM3): DCCF ported from s02c's sign-flipped DOCSTRING (LAG-10), not its correct code; numeric proof ±0.192 s on synthetic pair. Fix specified (temporal.py:1060 → s02c code formula + MC-median/16-84); interim validated tool = scripts/47c (imports s02c unmodified). **2026-08-30: NO re-survey — PI ruling 5 (banner): the LAG_* columns are STALE-PENDING-REWALK in `temporal_catalog_all106.ecsv`; each burst replaces its own rows as it is walked (NR-31 consumer guard). Sign flip does NOT repair the column (split-normal μ over the full grid, not the CCF peak). #21 = the TM3 validation case: catalog −5.250 vs 47c +0.715 vs Lu+2018 +1.22 ± 1.27 s; shipped report mislabelled the stale value with the standard-convention text** |
| MVT: only the Haar cross-check is in the catalog | canonical Bala MVT runs separately; CWT (scripts/47) ships as a sidecar | by design — label which MVT you quote. **2026-08-30 (TM5): MVT_* columns are STALE-PENDING-REWALK (ruling 5); #21 Haar 5.342 s > Golkhou+2015 limit < 2.096 s (2.5×) while CWT 0.724 s is consistent and Bala was never run → NR-32 published-limit screen at admission; scripts/47 sha drift vs its sidecar (NR-22)** |
| **Catalog T90 treated as ground truth** | a windowed-vs-catalog T90 diff read as an error; percentages quoted against a catalog T90 as if measured | **RULED 2026-08-31** → TM2: catalog T90 is detector-specific and carries its own subjective choices; the diff is a FRAME comparison, never an error (NR-40 concordance) |
| **Truncation flags without precedence** (CONFLICT-4) | `T90_WINDOW_TRUNCATED` (edge test) vs `TAIL_OUTSIDE_WINDOW_SIG ≥ 3σ` (TM1) disagree on #21 (False vs 11.95σ) | **RAISED 2026-08-30** → TM4 / NR-33: lower-limit language on the UNION; derived `T90_IS_LOWER_LIMIT` column PROPOSED pending PI |

**Rule:** any use of `temporal_catalog_human.ecsv` states which columns it used and which
ledger entries apply. The catalog is survey-grade scaffolding, not results.

## Quality checklist
- [ ] Reference NaI + background windows come from the APPROVED catalog, never re-derived.
- [ ] Pulse fit: r_l ≤ r_r enforced via `dr ≥ 0`; R² ≥ 0.7 or the row carries no φ.
- [ ] T90 sanity: `T90_ERR < T90` and T90 within ~2× of the block-span — else flag, don't record
      (the bn130310840 lesson: a failed fit sat in a committed catalog for weeks).
- [ ] STALE guard: the burst is in `meta.rewalked_triggers` of the catalog before ANY LAG_*/MVT_*
      value is quoted (ruling 5, NR-31) — otherwise quote only the burst's own wf-temporal outputs.
- [ ] Lag: state the sign convention next to every quoted value until the source fix lands.
- [ ] MVT: label Bala / CWT / Haar (three estimators, precedence in that order; TM5); never mix in
      one column; a Haar "detection" above a Golkhou+2015 limit is a REFUSE, not a result.
- [ ] T90: lower-limit language if EITHER `T90_WINDOW_TRUNCATED` or `TAIL_OUTSIDE_WINDOW_SIG ≥ 3`
      (TM4, PROPOSED).
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

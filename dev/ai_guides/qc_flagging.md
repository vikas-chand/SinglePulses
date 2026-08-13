# AI Guide: QC / bad-fit & bad-background flagging

> Part of the benchmark framework (dev/BENCHMARK_PLAN.md, task #6). Complements the decision.json schema in scripts/39_approve_all.py by giving the JUDGEMENT CRITERIA.

**Purpose** — After Stage 1 (selections) and Stage 2–3 (blocking + fitting) have run, flag the bins and bursts whose **background** or **spectral fit** is untrustworthy, so they can be excluded from population statistics. This is the last human-judgement gate before the physics tables.

**When to use** — Run once per burst after `results/clean_per_burst/<trigger>/spectral_fits.ecsv` exists. Two distinct failure classes, both flagged here: (a) **bad background** — the source window sits on quiet sky, the polyfit baseline is not flat, or the window is over-wide (caught early by scripts/36; the data-integrity bug behind 6 bursts in project memory); (b) **bad fit** — a converged fit that is physically meaningless (railed parameters, inverted DSBPL breaks, railed blackbody).

**Which decision.json field this fills** — scripts/39's `decision.json` has no QC field, so QC writes a **sibling file** `results/approval/<trigger>_decision.json` is NOT modified. Instead emit `results/approval/<trigger>_qc.json` with the contract in the Output section. (If a `qc` key is later added to the main decision schema, mirror it there; for now keep it separate so ingest is untouched.)

## Inputs (what to read)
1. **`plots/approval_lc/<trigger>_<det>.png`** — the rendered light curve (counts/s vs time) used for Stage-1 approval. Source window = the gap between the gold pre/post background spans; emission marked by vertical lines. This is your visual evidence for the **background** flags.
2. **`results/approval/<trigger>_pending.json`** — `suggested_source` {t1,t2} and per-detector `suggested_bkg`; `detectors[].angle_deg`. Cross-check the approved source against where the peak actually is.
3. **`results/background_intervals.ecsv`** (or `…_clean.ecsv`) — the approved BKG_NEG/POS and SRC_START/SRC_STOP per (trigger, det). Use for window-width QC.
4. **`results/clean_per_burst/<trigger>/spectral_fits.ecsv`** — one row per Bayesian block (BLOCK=-1 is T_INT) × 6 models. Per-model columns: `<P>_STATUS`, `<P>_N2LL`, `<P>_VALID`, `<P>_AIC`, parameter values + errors; plus `BEST_AIC_MODEL`, `LRT_BANDBB_BAND`, `LRT_DSBPL_SBPL`. Prefixes P ∈ {BAND, CPL, SBPL, DSBPL, BANDBB, CPLBB}.
5. **`results/clean_per_burst/<trigger>/spectral_evolution.png`** and **`ep_kt_correlation.png`** — visual sanity of the time series (a kT or Ep that jumps to a rail in one block is a flag).

## Decision criteria (the heart)
Flag at two granularities: **per-burst** (background) and **per-bin** (fit). Use these concrete, mostly already-computed rules.

### A. Bad-background flags (per burst; visual + catalog)
- **Source on pure background (CRITICAL).** In the LC PNG, the gap between the gold spans must straddle the obvious burst peak. Flag `source_on_background` if the marked source window contains **no peak above the background baseline** — i.e. the source-region rate ≈ the pre/post baseline rate (ratio ≲ 1.3). This is the exact bug that made 6 bursts' fits meaningless (bn090620400, bn090719063, bn100612726, bn100614498, bn110920546, bn200524211 in project memory) and collapsed them to 1 Bayesian block. A burst with **only 1 fitted block** is a strong corroborating signal.
- **Over-wide window.** Flag `window_too_wide` if `max(pre_width, post_width) > 200 s` (scripts/36 hard QC) — softer note at > 150 s (violates the 50–150 s rule). Wide windows interpolate the polynomial across orbital trends and bias the baseline.
- **Non-flat polyfit baseline.** In the LC PNG residual panel, the background-region residuals should scatter around 0 within ±~3σ with no slope/curvature. Flag `bkg_baseline_not_flat` if you see a visible trend, a step, or residuals systematically off zero in the pre/post spans.
- **Window sanity.** Flag `window_degenerate` if any pre/post width ≤ 0 (scripts/36) or post does not start at/after pre ends.

### B. Bad-fit flags (per bin; mostly read straight off the ECSV)
The engine already pre-screens via the **physical-validity gate** (`_fit_is_physical`, scripts/10): a model's `<P>_VALID=False` when any shape parameter sits within 0.1% of its bound, or (DSBPL) the low break `xb ≥ peak xp`. Use VALID as ground truth, then add visual judgement:
- **No physical winner.** Flag bin `inconclusive_winner` if `BEST_AIC_MODEL == 'INCONCLUSIVE'` (every OK fit was railed/invalid) — these are excluded from physics anyway but must be counted.
- **Winner is railed.** Flag `winner_railed` if the model named by `BEST_AIC_MODEL` has its own `<P>_VALID == False`. (Selection falls back to railed fits only when nothing is valid; treat as bad.)
- **Railed blackbody.** When BANDBB/CPLBB is the winner, flag `bb_railed` if `BANDBB_KT` (or `CPLBB_KT`) is within ~2% of its bounds [1.0, 200.0] keV, OR if the BB is claimed but `LRT_BANDBB_BAND < 9.2` (not significantly required → spurious thermal component).
- **Impossible nested LRT.** Flag `lrt_negative` if `LRT_BANDBB_BAND < -0.1` or `LRT_DSBPL_SBPL < -0.1`. A nested superset cannot fit worse than its parent at the true optimum; a negative value means the bigger model is stuck in a worse local minimum (the multistart should prevent this — a residual negative is a convergence flag).
- **Fit failed.** Flag `fit_failed` if a key model's `<P>_STATUS != 'OK'` for the winner.
- **Visual outlier.** In `spectral_evolution.png` / `ep_kt_correlation.png`, flag `param_outlier` for a bin whose Ep, kT, or α jumps to a rail or has an error bar spanning the full allowed range (uninformative fit).

**Verdict per bin:** `bad` if any B-flag fires; **per burst:** `bad` if any A-flag fires (the burst's fits are then suspect regardless of per-bin status).

## Output contract
Write `results/approval/<trigger>_qc.json`:
```json
{
  "trigger": "bn090719063",
  "approver": "Claude (AI)",
  "mode": "ai_vision",
  "burst_verdict": "bad",
  "burst_flags": ["source_on_background", "window_too_wide"],
  "bins": [
    {"block": -1, "verdict": "ok",  "flags": []},
    {"block": 0,  "verdict": "bad", "flags": ["winner_railed", "bb_railed"]},
    {"block": 1,  "verdict": "bad", "flags": ["inconclusive_winner"]}
  ],
  "reasoning": "Source gap sits at t~115-350s on flat baseline; peak is at t~0-10s. Single block. All fits are to background."
}
```
- `burst_verdict` ∈ {ok, bad}; `verdict` per bin ∈ {ok, bad}. `flags` use only the strings named in §A/§B.
- One bin entry per BLOCK in spectral_fits.ecsv (include BLOCK=-1).
- `mode` = `ai_vision`; `approver` = your agent name (mirrors the decision.json gate stamp so human vs AI QC is comparable).

## QC checklist (self-check before approving)
- [ ] Looked at the LC PNG for every approved NaI detector, not just one.
- [ ] Confirmed the source gap straddles a real peak (ratio > 1.3 over baseline).
- [ ] Read VALID/STATUS for the **winner** model in every bin, not just Band.
- [ ] Cross-checked any `bad` bin against the evolution PNG for a rail/jump.
- [ ] Counted INCONCLUSIVE bins explicitly (they must appear in the bins list).
- [ ] Every flag string is from the allowed set; reasoning quotes concrete times/values.

## Common pitfalls (failure modes a human reviewer would catch)
- **Trusting BEST_AIC_MODEL blindly.** It can name a *railed* fit when no valid model exists; always re-check the winner's `<P>_VALID`.
- **Missing the pure-background source.** A clean-looking polyfit on quiet sky still produces "fits" — flat residuals do NOT mean the source window is right. The tell is the *absence* of a peak in the gap, not the background quality.
- **Calling a real two-break fit "railed."** xp near 5000 keV or α near a bound can be physical for hard bursts; only flag when the gate (`<P>_VALID`) agrees or the error bar is uninformative.
- **Over-flagging faint bins.** Few-count blocks legitimately give large errors; flag `param_outlier` only for rail-pinned values, not merely large but finite errors.
- **Ignoring T_INT (BLOCK=-1).** It seeds every block; a bad T_INT fit poisons the burst.

## How this is scored vs humans
From dev/BENCHMARK_PLAN.md task #6: **agreement on flagged-bad bins/bursts via precision/recall vs the human flag set.** Treat the human's flagged-bad set as ground truth; compute, per benchmark burst: precision = (AI-flagged ∩ human-flagged) / AI-flagged, recall = (AI-flagged ∩ human-flagged) / human-flagged, at both bin and burst granularity, with F1 reported. Inter-human scatter (if multiple experts) is the denominator: the AI is "good" if its precision/recall against humans matches how well humans agree with each other. The decisive secondary check is downstream — does excluding the AI-flagged-bad bins change the population Ep/kT/α/classification the same way excluding the human-flagged-bad bins does (BENCHMARK_PLAN downstream-impact metric)?

## Step-9 addition — Amati & Yonetoku plane placement for z-known bursts (Vikas, 2026-08-11)
*Gated in by Vikas: "putting a burst into Amati and Yonetoku correlation plane gives us good
plot in any case as it maybe that some burst some day violate the correlation." A standing
per-burst PRODUCT (not just a pass/fail line), and a discovery-plane hook.*

**Applies to:** every burst with a redshift in its dossier (z with its circular/paper as
source — never assumed). Expected yield: the handful of z-known bursts in the 106 (~4–8,
mostly low-z SN-associated — which is precisely the historical neighborhood of Amati-plane
violators; 980425/031203-class, bibcodes to be ADS-verified before any writeup).

**Procedure (native to what the pipeline already emits):**
1. From the T_INT row of the AIC-winning model: Ep,obs and the model-integrated fluence;
   Ep,i = Ep,obs·(1+z); Eγ,iso in the 1–10⁴ keV REST frame via k-correction integrating the
   best-fit model (record the model used — the k-correction is model-dependent, say so).
2. For Yonetoku: peak flux over the catalog peak interval → Liso = 4π d_L² F_peak,bolo
   (same k-correction discipline; record the peak-interval definition).
3. Place the burst on BOTH planes against the published relations with their ±2σ bands
   (Amati; Yonetoku; exact reference samples ADS-verified at implementation).
4. **Frame discipline before any verdict** (this is where violations go to die):
   - T9 component coverage — OUR fluence covers our stamped window; a precursor or missed
     tail changes Eiso (the 180728A lesson: BAT T90 covers the main pulse only);
   - multi-instrument consensus (Phase 4 rule): if published Ep values disagree across
     instruments, the spread is a systematic on the placement, drawn as an error inflation;
   - the L27/L28 stamps: an EDGE_CONSTRAINED or BOUND_CAPPED Ep never anchors a violation.
5. Verdicts: `CONSISTENT` (inside 2σ) → one QC line + the plot filed with the burst record;
   `OUTLIER_CANDIDATE` → discovery-plane flag, NEVER a claimed violation in a record — the
   claim path runs through the frame checklist above, the with/without-precursor pair, and
   Vikas's gate (scorecard-after-the-game rule applies).
**Output:** `results/walkthrough_b<i>/<trig>_amati_yonetoku.png` + a one-line verdict in the
burst record. Implementation: small product script in the next products batch (rides with the
hardening items; no engine change).

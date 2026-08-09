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
   errors by bootstrap resampling (n=100). ⚠ **BROKEN — see defect ledger.**
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

## 🔴 Defect ledger (check BEFORE quoting any number)
| defect | evidence | state |
|---|---|---|
| **T90 bootstrap errors broken** | `T90_ERR > T90` in **84/89** rows | OPEN — fix in handbook `temporal.py` |
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

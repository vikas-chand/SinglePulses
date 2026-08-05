# HANDOFF → Codex — Two_Breaks burst walkthrough, 2026-08-04

**Claude session UUID:** `ca170c1c-e33e-41ca-ab82-bda497c3c36f`
**Session URL:** https://claude.ai/code/session_01JJ69pCiiAH9vVeWyUxPQEf
**Raw transcript:** `/Users/salim/.claude/projects/-Users-salim-Desktop-Projects-SingleRest-Two-Breaks/ca170c1c-e33e-41ca-ab82-bda497c3c36f.jsonl` (34 MB, 6326 lines — **do not read whole**; grep it)
**Read these first instead:** `AGENTS.md`, `dev/ai_guides/BurstWalkthrough.md`,
`dev/ai_guides/SpectralFitting.md`, `dev/ai_guides/DataInventory.md`, this file.

---

## 1. What this campaign is
A **gated, burst-by-burst walkthrough** of the whole pipeline (ledger steps 0–9 in
`BurstWalkthrough.md`). Each step is RUN → PRESENTED → **STOPS for Vikas's approval**.
Bursts run **ONE AT A TIME** (a list of N is a queue, not a batch). Vikas chooses the burst.
Cheap pre-flight sweeps (Step 0/1) across the queue are fine and have already caught 2 bugs.

**Blind-first rule (CLARIFIED by Vikas 2026-08-03):** blindness governs the **FIT**, not what
you may read. Step 0 may harvest published spectral values (file them under
`PUBLISHED VALUES (for the P3 diff)`). Never seed/restrict/re-bound a fit toward a published
number; freeze P0 before diffing; disclose prior exposure in the record.

## 2. State of the queue
| # | trigger | GRB | steps done | notes |
|---|---|---|---|---|
| 1 | bn081125496 | GRB 081125 | 0–9 ✅ | GBM-only. Photosphere (α>−2/3). Reproduces Yu+2019. |
| 2 | bn081222204 | GRB 081222 | 0–9 ✅ | GBM-only, z=2.77. Synchrotron (α≤−2/3). Matches Ghirlanda. |
| 3 | bn081224887 | GRB 081224 | 0–9 ✅ | **1st LLE burst.** Ep 2141→133 keV; α crosses −2/3 mid-burst. **All 10 blocks DEGENERATE.** |
| 4 | bn120624933 | GRB 120624B | 0,1 ✅ | **BLOCKED — needs Vikas's LLE decision (below).** z=2.1974, E_iso 3.0e54. |
| 5 | bn130310840 | GRB 130310A | 0–9 ✅ | ms structure (8 ms blocks), Ep→12.4 MeV, thermal at blk2-4. |
Remaining in queue: **bn130427324** (⚠ blocked, see §4), **bn130518580**.

Products: `results/walkthrough_b3/bn081224887/`, `results/walkthrough_b5/bn130310840/`
(each: `spectral_fits.ecsv/.json`, `spectral_evolution.png`, `ep_kt_correlation.png`).
QC: `results/approval/<trig>_qc.json`. Dossiers: `results/gcn/<trig>/<trig>_dossier.md`.
νFν: `results/figures/<trig>_nuFnu_best_montage.png`. ⚠ **`results/` is gitignored** — products
are LOCAL ONLY; the records in `notes/` are what's tracked.

## 3. How to run a burst (exact commands)
```bash
# heavy tier env (AGENTS.md §2) — NOTE: CALDB is $FERMI_DIR/data/caldb  (NOT refdata/caldb)
conda activate threeML
export FERMI_DIR=$CONDA_PREFIX/share/fermitools
export CALDB=$FERMI_DIR/data/caldb
export CALDBCONFIG=$CALDB/software/tools/caldb.config
export CALDBALIAS=$CALDB/software/tools/alias_config.fits
export CALDBROOT=$CALDB EXTFILESSYS=$FERMI_DIR/refdata/fermi
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1

# STEP 6 — fit (~45-60 min/burst, 24-model 'highe' menu)
python scripts/10_spectral_fit_burst.py --trigger <TRIG> \
  --blocks-file results/clean_blocks_human_final/bb_blocks_spectral_<TRIG>.ecsv \
  --bkg-file results/background_intervals.ecsv \
  --out-dir results/walkthrough_bN/<TRIG> --include-bgo --models highe

# STEP 8 — nuFnu (MUST set BLOCKS_ROOT + FIT_ROOT)
export BLOCKS_ROOT=$PWD/results/clean_blocks_human_final
export FIT_ROOT=$PWD/results/walkthrough_bN
python scripts/41_nuFnu_panels.py --trig <TRIG> --dets <dets,incl lle> --ref <canonical NaI> --mode best --out results/figures
```
Step 7 (temporal) = one-burst driver mirroring `scripts/40_temporal_survey.py::survey_one`
(scripts/40 itself runs the WHOLE sample and rewrites `temporal_catalog_human.ecsv` — do not
use it for one burst). Step 9 = `dev/ai_guides/qc_flagging.md` + the ΔAIC margin table (§5).

## 4. 🔴 OPEN DECISIONS / BLOCKERS (need Vikas)
1. **Burst #4 LLE.** GRB 120624B has a **10σ Fermi-LAT detection (GCN 13379, not retracted)** and
   LLE+LAT files on disk, but the approved catalog has **no `lle` row** (only n0,n1,n2,b0).
   Fitting GBM-only discards the detector that constrains the high-E component on a burst where
   high-E emission is confirmed. **Stage-1 re-open decision required before Step 6.**
2. **bn130427324 (GRB 130427A) LLE DRM is INVALID — fix before its turn.** Its LLE `.rsp` was
   built at off-axis θ=48.1°; the stamped source window (the **2nd pulse**, 119–178 s) sits at
   θ=36.5°→23.0° ⇒ **Δθ=19.9°** (Fermi slewed). Regenerate the DRM (`mkdrm_ez`/gtburst) for the
   actual interval, or quarantine LLE and fit GBM-only. See D1 in `DataInventory.md`.
3. **Bursts #1/#2 block-provenance fork (deferred by Vikas).** `clean_per_burst_human_final` fits
   = right blocks + OLD engine (2026-07-19, pre L4/L5/L8/L9); the reconciliation
   `<trig>_evolution.ecsv` = fixed engine + WRONG blocks (a completion script read the stale
   `results/clean_blocks/`). Both QC files carry `cross_step_flags:["reconciliation_run_mismatch"]`.
   Science is robust to the choice. Plan: let the frozen full-sample run settle it.
4. **Burst #3 reconciliation record not yet written** (Vikas said he'd help with it).

## 5. 🔬 THE KEY METHODOLOGICAL FINDING (carry this forward)
**Best-AIC winners are NOT decisive.** Under the project's own **ΔAIC ≥ 10** doctrine:
- **Burst #3: 0/10 blocks decisive**; in 6/10 the *simplest* model (Band/CPL/SBPL) was **tied**
  (ΔAIC_simplest = 0.0) — the 24-model menu bought nothing.
- **Burst #5: 0/11 decisive vs runner-up**, BUT ΔAIC vs simplest = **26.0 (blk2), 8.0 (blk3),
  9.0 (blk4)** ⇒ an extra component IS decisively required there.
**Always report TWO margins per block:** ΔAIC(winner − runner-up) *and* ΔAIC(winner − simplest).
They answer different questions: "which model" vs "is an extra component needed at all".

**2SBPL vs additive-component test (Vikas's question, 2026-08-04) — run this on every burst.**
On burst #5, in exactly the blocks needing an extra component, **2SBPL is worse by ΔAIC 11–26**
(blk2 +26.5 vs SBPL+BB, blk3 +11.0, blk4 +13.2) — clearing the ≥10 bar. ⇒ The low-energy feature
is an **additive component, NOT a second break**; the DSBPL members of the `extra_lowE_curvature`
class are decisively excluded there. **But BB vs PL is unresolvable** (blk2 winner = SBPL+PL,
CPL+BB+PL only 0.8 behind) — which is exactly registry **#42**'s photosphere-vs-forward-shock
question, and it says AIC alone cannot settle it.

## 6. Bugs fixed this session (do not regress)
- **`BLOCKS_ROOT` env override** added to `scripts/34`, `scripts/38`, `scripts/41` — all three
  hardcoded `results/clean_blocks/` while the human arm lives in `clean_blocks_human_final/`.
  Defaults unchanged. `scripts/41` also gained a per-detector row de-dup.
- **Gowri+2025 protocol adopted EXACTLY** in `GRB_Handbook_Project/grb_pipeline/analysis/temporal.py`:
  `r_l ≤ r_r` enforced by reparameterising `r_r = r_l + dr, dr ≥ 0`; ≤300-bin rebin; `r² = 1−RSS/TSS`
  + `r2_pass`; `phi_class` (<0.3 FRED / 0.3–1 mixed / >1 symmetric-like). ⚠ A circulated summary
  said `r_l ≥ r_r` — **INVERTED**; the paper says `rl ≤ rr`.
- **PGSTAT verified for the LLE path** (not just GBM): both plugins probe to poisson obs +
  gaussian bkg → `PoissonObservedGaussianBackgroundStatistic`. We never set a statistic.

## 7. Known-broken / open bugs
- **Handbook spectral-lag SIGN is INVERTED** vs Ukwatta (h.t.s. ⇒ positive). Confirmed on 3 bursts.
  Interim: negate `LAG_S` at point of use. **Fix at source in `grb_pipeline`.**
- **T90 bootstrap error is garbage** (`calculate_t90` resamples `lc.time[idx]` with shuffled
  indices) — returns 42–56 s on a 2–20 s T90, non-deterministic. Do not quote T90 errors.
- **No `LRT_SBPLBB_SBPL` column** ⇒ BB-necessity cannot be tested for SBPL+BB winners.
- **`results/temporal_catalog_human.ecsv` is HELD BACK from commits** — its `LAG_S` column uses
  the inverted convention. Regenerate only after the source-level sign fix.
- `DSBPL xb.bounds` still caps at 5000 keV (Band `xp` is fine at 5e4).

## 8. Literature state
Corpus: `Skills_training/corpus_index.csv` (tracked; **PDFs are gitignored**). ~47 rows.
Dedup rule G2: look up the bibcode before fetching; append the trigger to `cited_by_bursts`.
**Registry `notes/PROJECTS_registry.md` owns projects #33+.** Live ones: **#37** lag–MVT
(reframed to a *controlled redo* of Sonbas+2013 — see the retraction note), **#39** Hakkila
lineage, **#40** bright-end energy functions, **#41** Einstein Probe timing (GATED, verdict WAIT),
**#42** two-arm pulse physics: Gowri+2025 (photosphere) vs **Rahaman, Granot & Beniamini 2024,
MNRAS 528 L45** (`2024MNRAS.528L..45R`) FS+RS internal shocks — RGB2024 predicts BOTH the
low-energy "photospheric-like" bump AND the doubly-broken power law, i.e. it is a one-mechanism
origin for the two shapes this project is named after.
Verification briefs: `notes/litverify_2026-07-31_*.md` (every claim carries a bibcode).
---

## 9. ⚠ CORRECTIONS TO §5 (added 2026-08-04 after the Codex audit + a Vikas catch)
**Read this section BEFORE acting on §5 — it retracts two claims made there.**

**(a) "Ep = 12.4 MeV" — retracted, then RE-INSTATED with the right provenance.**
The Codex audit correctly noted the blk2 **Band** fit is `VALID=False` (beta railed at our -5 floor)
and said to stop quoting 12.4 MeV. But Vikas pointed out XSPEC allows beta to ~-10. Test: widening
the floor to -10 changes Ep by 0.2% (12278 → 12301 keV, ΔAIC -0.08) — beta simply runs to whatever
floor exists, i.e. the likelihood wants beta → -inf (= no measurable high-energy tail; Band → CPL).
**The peak is bound-independent, and the VALID CPL fit gives 12499 keV, agreeing to 0.3%.**
⇒ Correct statement: **peak = 12.4 MeV from a valid single-component CPL; 7.7–9.7 MeV once an
additive component is included** (SBPL+BB 7681, CPL+BB 9716 keV). That range BRACKETS Qin+2021's
8.5–11 MeV. See lesson **L15** in `SpectralFitting.md`.

**(b) "2SBPL decisively loses by ΔAIC 11–26" — RETRACTED (Codex is right).**
The blk2 head-to-head is void because the saved 2SBPL fit there is itself invalid. blk3/blk4 do show
2SBPL losing by 11.0–13.2, but under the corrected grading those blocks are STRONG/VERY STRONG, not
decisive, for needing extra structure at all. ⇒ **"additive component, not a second break" is NOT
established.** Only blk2 robustly requires extra structure, and BB vs PL is unresolved there.

**(c) The ΔAIC ≥ 10 rule is REPLACED by a graded scale (new doctrine, lesson L16).**
ΔAIC is an evidence ratio `exp(ΔAIC/2)`: **≥6 = STRONG (20:1), ≥10 = DECISIVE (148:1)**; always
report the ratio. bn130310840 becomes blk2 DECISIVE (26.0), blk4 VERY STRONG (9.0, 91:1), blk3
STRONG (8.0, 54:1). **Doctrine bug found:** the `+BB` gate `LRT ≥ 9.2` is equivalent to ΔAIC ≈ 5.2,
so it CONTRADICTS the ΔAIC ≥ 10 rule by ~5 AIC — make them consistent.
**Calibration caveat:** for additive components the LRT is not asymptotically chi-square (bounded
normalization), so both gates are optimistic; component significance needs MC calibration.

**(d) The QC records used unvalidated fits.** `results/approval/bn130310840_qc.json` (and burst #3's)
computed ΔAIC margins straight off the `*_AIC` columns **without checking `*_VALID`**. Recompute
margins over VALID fits only — this is what made (a) and (b) wrong.

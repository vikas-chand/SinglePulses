# Running ONE burst, end to end, with every product

**For:** Khushboo — one GRB at a time, look at every plot, judge how the fits are going.
**Written:** 2026-08-13 (Vikas). Pull `main` first — it carries fixes that change what you see.

---

## 0. Pull first (this matters)

```bash
git checkout main && git pull
```

Your branch predates these, and two of them change results you already looked at:

- **`scripts/10` — `find_tte` matched only `*.fit.gz`.** Your F-1 finding. An uncompressed
  `.fit` TTE made the detector vanish silently. Now it matches both, **and an approved
  detector that resolves to no file prints a loud `!!` line** instead of disappearing.
- **`scripts/10` — per-bin response coverage.** One bin outside the RSP2's span used to
  discard every other bin of that detector. Now each bin is judged on its own; uncovered
  bins are recorded as `RESPONSE_UNCOVERED` (never extrapolated).
- **`scripts/41` — the montage was lying.** `--mode best` used to *refit* each bin with a
  weaker fitter and print that fit's winner. On one burst it labelled a panel `SBPL` while
  the engine's winner was `Band+BB`. It now **displays the engine's stored winner** from
  `spectral_fits.ecsv` and stamps `[! PANEL!=ENGINE dAIC=...]` on any panel that drifts.
  **Your `BKG_FILE` and `--bin tint` patches are folded in with credit** — so drop them from
  your branch when you rebase.
- **`scripts/41` — error bands.** If >1% of covariance samples rail at bounds the band is
  suppressed and *says so on the figure*, instead of drawing a band displaced off its curve.
- **T90 errors were broken in 84/89 rows** (the estimator shuffled time-bin order). Fixed in
  the handbook `temporal.py`; T90 uncertainties are now meaningful.

---

## 0b. ⚠ THE SELECTIONS ARE ALREADY MADE — ADOPT THEM, NEVER RE-PICK

**Vikas, 2026-08-13: the detector selection, the background windows and the source interval
are already done by him, and they pass to you AS THEY ARE. Your products are built on those
prior selections.**

They live in `results/background_intervals.ecsv` — **tracked in git, so `git pull` gives you
the exact file** (436 rows, 106 bursts; `APPROVAL_MODE` = `human_gui` on 433 of them,
`APPROVED_BY` = Vikas Chand). Every command below already reads it via
`--bkg-file results/background_intervals.ecsv`. Do **not** run the picker, do not adjust a
window, do not drop a detector — not even one that looks wrong.

If a selection looks wrong to you, that is a **finding to report, not a change to make**:
write it down (burst, detector, what you see) and send it to Vikas. Two things to check first,
because both have already produced false alarms:
- `results/human_review_qc_flags.txt` — 20 detector-rows carry an **accepted** source-overruns-
  background-gap override. Those are Vikas's decisions, not defects. `scripts/43_catalog_validator.py`
  does this join for you and currently reports 20 adjudicated / 0 unadjudicated.
- individual detectors may legitimately have **different** background windows for the same burst.

Why this matters beyond tidiness: with Stage-1 held fixed and identical on both systems, any
difference between your run and ours comes from binning, fitting or execution — not from
different selections. That is what makes the cross-system comparison interpretable.

## 1. Run the burst (heavy tier)

```bash
conda activate threeML
export FERMI_DIR=$CONDA_PREFIX/share/fermitools
export CALDB=$FERMI_DIR/data/caldb
export CALDBCONFIG=$CALDB/software/tools/caldb.config
export CALDBALIAS=$CALDB/software/tools/alias_config.fits
export CALDBROOT=$CALDB
export EXTFILESSYS=$FERMI_DIR/refdata/fermi

TRIG=bn0812224887          # <-- your burst
OUT=results/mine/$TRIG

python scripts/27b_reblock_3ml.py --burst $TRIG --out $OUT/blocks
python scripts/10_spectral_fit_burst.py --trigger $TRIG \
  --blocks-file $OUT/blocks/bb_blocks_spectral_${TRIG}.ecsv \
  --bkg-file results/background_intervals.ecsv \
  --out-dir $OUT/$TRIG --include-bgo --models highe --no-log
```

## 2. Make EVERY product + the manifest

```bash
python scripts/45_all_products.py --trig $TRIG --out $OUT
cat $OUT/PRODUCTS.md          # <-- what exists, and what is MISSING and why
```

`45` runs the light-tier step figures, the montage, and **one all-models overlay per time
bin**; `PRODUCTS.md` lists every expected artifact with a checkbox. A missing product is
always *stated* — if a directory looks empty, read the manifest, then the fit log.
Add `--skip-overlays` for a fast pass (no per-bin refits, no threeML needed).

---

## 2b. APPROVE each step as you go (this is the deliverable)

Vikas: *run one burst at a time, look at and approve each product and each step of the
analysis.* So the review is a **signed record**, not just a look:

```bash
mkdir -p notes/approvals
cp handoff_background_approval/KHUSHBOO_APPROVAL_SHEET_TEMPLATE.md \
   notes/approvals/${TRIG}_approval.md
# fill it in step by step, then:
git add notes/approvals/${TRIG}_approval.md && git commit -m "approval: $TRIG" && git push
```

Approve each step **before** moving to the next; if a step is not OK, stop there and write
why rather than carrying the doubt forward. Your sheets are the second-operator record the
whole comparison rests on.

## 3. What each figure is for (this is the diagnosis order)

| figure | look for |
|---|---|
| `step1_inventory` | every approved detector's DRM must bracket the source window (PASS/FAIL bars); angles under 60° |
| `step3_background` | does the polynomial track the pre/post windows *and* extrapolate sanely under the burst? A drifting or curved extrapolation is the usual cause of a bad net rate |
| `step4_source` | the source window inside the common background gap. If it overruns, the figure says so — those are **adjudicated, accepted decisions** (`results/human_review_qc_flags.txt`), not defects |
| `step5_binning` | blocks should track real structure; the number on each block is its significance |
| `<trig>/spectral_evolution.png`, `ep_kt_correlation.png` | parameter tracks across blocks — look for jumps that no emission mechanism can make |
| `nuFnu_bin<N>_allmodels_overlay` | **all models in one bin, engine winner in bold black.** If several curves sit on top of each other, the winner's identity is undetermined even if its AIC is lowest |
| `nuFnu_best_montage` | winner per bin. **Any `[! PANEL!=ENGINE]` stamp = trust the table, not the curve** |
| `step9_qc` | ΔAIC per block against the DECISIVE (≥10) / STRONG (≥6) lines, with the winner labelled; below it, `3.92·kT` for significant blackbodies against the 20/30 keV L28 boundaries |

---

## 4. Two rules that will save you from wrong conclusions

- **A tie is a tie.** A winner by ΔAIC 2 is not a detection — say "the data mildly prefer X
  and are equally well described by Y" (your own GRB 200524A phrasing; it is now doctrine).
- **A feature below ~20 keV is edge-constrained (L28).** A blackbody's νFν turnover sits at
  3.92·kT, so kT ≈ 4 keV means the evidence lives in the worst-calibrated channels. Those
  values are kept in the record but excluded from population statistics until the L28 checks
  pass (`dev/ai_guides/SpectralFitting.md`).

## 5. When something looks wrong

Write it down the way you did in `notes/PIPELINE_FLAGS_2026-08.md` — that file found two real
engine defects. One request from that round: **check `results/human_review_qc_flags.txt`
before flagging a selection**, since 20 detector-rows carry accepted overruns that are Vikas's
decisions, not bugs (`scripts/43_catalog_validator.py` does this join automatically).

# CODEX BRIEF — whole-project audit, Two_Breaks (2026-08-13)

**Run mode:** GPT-5.6, Sol, Ultra.
**Working directory:** `/Users/salim/Desktop/Projects/SingleRest/Two_Breaks`
**READ-ONLY except your report. Write only `notes/CODEX_WHOLE_PROJECT_20260813.md`.**

Scope requested by the PI (Vikas Chand): **audit of the whole project** — engine, products,
doctrine, campaign state, and the claims that are about to become paper numbers. This is a
production run in flight, not a finished manuscript: judge whether the *system* is sound and
whether its outputs may be trusted, and say plainly where they may not.

## Environment
- `/Users/salim/anaconda3/bin/python3` — numpy/pandas/astropy/scipy/pymupdf (light tier).
- Heavy tier: `conda activate threeML` + `export FERMI_DIR=$CONDA_PREFIX/share/fermitools;
  export CALDB=$FERMI_DIR/data/caldb; export CALDBCONFIG=$CALDB/software/tools/caldb.config;
  export CALDBALIAS=$CALDB/software/tools/alias_config.fits; export CALDBROOT=$CALDB;
  export EXTFILESSYS=$FERMI_DIR/refdata/fermi`. threeML/astromodels are installed there.
- `pdflatex` present. ADS token: `set -a; source ~/Desktop/Projects/FXTs/.env; set +a`
  (plain `source` does NOT export it).
- ⚠ **A 12-way parallel fit sweep is RUNNING** (`results/sweep106/`, ~16 python processes).
  Do not kill it, do not write into `results/sweep106/`, and expect files to appear while you
  work. Anything under `results/sweep106/<trig>/<trig>/` that is currently absent may simply
  be mid-flight — check `notes/sweep106_log.md` for that burst before calling it a failure.

## Artefacts of record (SHA-256, first 16, at brief time, HEAD = 42a2a9c)
| file | sha256[:16] |
|---|---|
| `scripts/10_spectral_fit_burst.py` (the engine) | `af053a99a6ce1a3c` |
| `scripts/41_nuFnu_panels.py` (νFν panels) | `94fcc646a4372164` |
| `scripts/44_step_figures.py` (NEW, unreviewed) | `bb4767cf1a56d326` |
| `scripts/45_all_products.py` (NEW, unreviewed) | `4a99a5ab100d0f94` |
| `scripts/46_temporal_all106.py` (NEW, unreviewed) | `a15677163e1d965c` |
| `scripts/47_compare_systems.py` (NEW, unreviewed) | `c0394ca47adda8a3` |
| `~/Desktop/Projects/GRB_Handbook_Project/grb_pipeline/analysis/temporal.py` | `c715198b94610c61` |

Doctrine of record: `dev/ai_guides/*.md` (13 files). Campaign log: `notes/sweep106_log.md`.
Ignore `paper/two_break.tex` for this audit (science paper, separate track); the agentic
manuscript `paper_agentic/agentic_grb_v2.tex` is IN scope only for whether its *claims* match
the products (it is known to be current only to 2026-08-10 — do not report staleness as a
defect, report any claim that is now FALSE).

## Deliberate conventions — do not relitigate these
1. `results/human_review_qc_flags.txt` records **accepted human overrides**: 20 detector-rows
   where the source window overruns the background gap. The gap rule in
   `dev/ai_guides/source_selection.md` is a **Stage-1 warning**, overridable at the human
   gate — not an invariant of the shipped catalog. `scripts/43_catalog_validator.py` joins the
   ledger and currently reports **20 adjudicated / 0 unadjudicated**. Two operators have
   already re-flagged these as bugs; a third would be noise.
2. Walkthrough-era numbers are **provisional by doctrine** until the PI blesses them.
3. Data-dropping hierarchy (`dev/ai_guides/DataInventory.md`): production never drops
   quality-passing data; with/without runs are diagnostics only; documented quality exclusion
   (e.g. `RESPONSE_UNCOVERED`) is the sole omission path.
4. `results/` is gitignored except `results/gcn/` and `results/qc/`.

## Prior review
`dev/audits/CODEX_AUDIT_REPORT_2026-08-11_night_L28.txt` (your own, 2026-08-11) and my
adjudication `dev/audits/ADJUDICATION_2026-08-11_night_L28.md`.
**Do NOT re-derive what you already confirmed there** — specifically the 18 DECISIVE/STRONG
scorecard values (you reproduced them exactly) and the Tierney/Ravasio numeric anchors.
Items you raised and how they were addressed — **verify the fixes, not the findings**:
- MF-1 (BB census consulted only Band+BB; 31 vs 55 blocks) → scorecards regenerated under the
  UNION of the Band+BB and CPL+BB nested pairs, child-VALID gated. Verify the rule as
  implemented now, incl. in `scripts/44_step_figures.py::fig_step9`.
- MF-3 (b12: one uncovered bin discarded the whole detector batch) → per-bin
  `to_spectrumlike` fallback in `scripts/10` (search `RESPONSE_UNCOVERED`).
- MF-4 (L28 misstated both papers) → rewritten in `dev/ai_guides/SpectralFitting.md`.
- MF-5 (kT rail geometry doc vs code) → corrected in the L27 text.
- SC-6/SC-7 (record policy; classifier dual-input + boundaries) → `edge_feature_class` now
  raises on kt AND xb; boundary tests added.
- **STILL OPEN (do not report as new; do assess risk):** MF-2 edge class is not serialized
  into fit tables nor enforced in population scripts; SC-1 the 30 keV boundary and the
  20-keV→BB transfer are uncalibrated project policy; SC-2 P0 files are written after their
  fit tables exist (mtime-ordered only, not hash-committed).

## Verified state at brief time — recompute, do not trust these
- `pytest tests/ -q` → **3 failed, 78 passed, 1 xfailed**. The three failures are all in
  `tests/test_catalog_qc.py` (`test_approval_stamps`, `test_ordering_and_source_in_gap`,
  `test_margin_band`). At least one is the convention clash of item 1 above
  (`APPROVAL_MODE == 'ai_inherited_PENDING_HUMAN'` for bn120624933's LLE row, a known pending
  human confirmation). **I have NOT diagnosed the other two — that is item A1 below.**
- `scripts/43_catalog_validator.py` → 436 rows, 20 adjudicated, 0 unadjudicated.
- Products: 67/85 fits, 71 step-figure sets, 68 montages, 62 P0 freezes, 54 harvest
  manifests, 49 step-1 QC tables, 13 skills, corpus 178 rows / 238 PDFs.

---

# What to verify

**Recompute everything from the products. Do not trust any printed value, including every
number in this brief.**

## A. Correctness of the analysis chain (highest value)

- **A1.** Diagnose all three `tests/test_catalog_qc.py` failures. For each: is it a real
  defect in the catalog, a stale test encoding a superseded rule, or the documented human
  override of item 1? State which, with the offending rows. A test that fails for a legitimate
  convention is itself a defect — say so and give the fix.
- **A2.** `scripts/10_spectral_fit_burst.py`: audit the per-bin `to_spectrumlike` fallback
  added 2026-08-13. Does it preserve bin→plugin identity (the existing identity-match logic
  further down assumes `speclikes_raw` entries carry their own tstart/tstop)? Can it
  mis-assign a bin, double-count, or silently drop a covered bin? Demonstrate on
  `bn150721242` (whose block 0 starts −0.804 s while its first DRM starts +0.064 s;
  `results/walkthrough_b12/`).
- **A3.** The **union BB rule** as now implemented (`LRT_BANDBB_BAND` and `LRT_CPLBB_CPL`,
  ≥9.2, kT > 1.0544, child `*_VALID`). Recompute the significant-BB census over
  `results/sweep106/*/*/spectral_fits.ecsv` and check it against
  `results/walkthrough_night_summary_v2.json` for the overlapping bursts. Is 1.0544 the
  correct rail floor given `PARAM_BOUNDS` and the L27 log rule? Are there other nested pairs
  the engine emits that the census still ignores (e.g. SBPL+BB)?
- **A4.** The **T90 Monte-Carlo fix** in the handbook `temporal.py` (`calculate_duration`).
  It replaced index-resampling with in-place Poisson realizations, forming `T90 = t95 − t5`
  per realization. Verify: (i) is the Poisson seed correct when `lc.rate` is
  *background-subtracted* and can be negative — I clamp with `np.maximum(...,0)`, does that
  bias T90 or its error? (ii) is `np.interp` receiving monotonic `x`? (iii) does `n_mc = 200`
  suffice for a stable σ? (iv) the fixed RNG seed 20260813 — does it make the reported error
  reproducible-but-biased in any way that matters? Recompute T90 ± σ for two bursts and
  compare against the GBM catalog value (external check).
- **A5.** `scripts/41_nuFnu_panels.py` `mode=best` now warm-seeds from the engine row and
  displays the engine's stored winner. Verify it cannot silently display a *different* model
  than the label claims, that `_row_seed`/`_apply_short_names` map parameters correctly for
  composite models (e.g. `Band+BB`, `CPL+BB+PL`), and that the `PANEL!=ENGINE` stamp triggers
  when it should. This code path shipped a figure that contradicted its own table on
  2026-08-12 — that is the failure class to hunt.

## B. The new, entirely unreviewed scripts
- **B1.** `scripts/44_step_figures.py` — do the figures state the truth? Especially
  `fig_step9` (does its ΔAIC match the engine's own margin definition and the scorecards?) and
  `fig_step7` (is the energy-band selection `emid[np.clip(ch,...)]` a correct channel→energy
  mapping, or does it mis-bin?). Check the step-3 background polynomial against what
  `scripts/10` actually fits — if the figure's polynomial is not the production estimator,
  the figure lies about the pipeline (this exact class of error has bitten us twice).
- **B2.** `scripts/45_all_products.py` — is the manifest honest? Does it ever mark a product
  present that is empty/corrupt, or expect one that cannot exist for a legitimate reason?
- **B3.** `scripts/46_temporal_all106.py` — it imports `survey_one` from `scripts/40` to avoid
  a fork; confirm no behavioural divergence from the roster sweep, and that the 17 non-roster
  bursts are handled identically rather than specially.
- **B4.** `scripts/47_compare_systems.py` — will its cross-system diff be *meaningful*? Check
  the block-matching key (rounded intervals), the σ formula, and the divergence-bin logic.
  Would it mistake a binning difference for a parameter disagreement?

## C. Doctrine vs implementation
- **C1.** For each numbered lesson in `dev/ai_guides/SpectralFitting.md` (L1–L28) that claims
  an ENGINE or TEST, verify that the claim is true of the current code. Report any lesson
  whose stated fix is not actually in force. (`tests/test_lessons.py` is the intended
  mechanism — check its coverage is real, not nominal.)
- **C2.** `dev/ai_guides/Temporal.md` — I corrected the Qin+2013 rule to state that
  T̄₉₀ ∝ E^−0.20 is a **population-mean** relation, not per-burst. Verify against
  `Skills_training/Qin_2013_2013ApJ76315Q_PUB.pdf` (external source). Also verify my four
  resolved source audits recorded in
  `.claude/skills/grb-two-shock-analysis/references/22_qin_2013_energy_dependent_t90.md`
  (091010-vs-090910 caption typo; the HR denominator being under-signposting rather than
  contradiction; 1:6.5 consistency; the block fitness/prior never being stated).
- **C3.** `dev/ai_guides/ShippingGate.md` is new doctrine. Is it enforceable as written, or
  is it aspirational prose? Name the checks that are actually mechanized versus those that
  depend on someone remembering.

## D. Campaign integrity
- **D1.** Blind-first: P0 files under `notes/reconciliation/*_P0_frozen.json` must not contain
  values derivable from the burst's own *new* fit table. Sample ~10 across eras and check.
  Note the known weakness (SC-2) — assess whether any P0 shows actual leakage, which is the
  part that matters.
- **D2.** `notes/sweep106_log.md` vs reality: does every burst marked complete have the
  products the log implies? Find bursts that reported exit 0 and produced nothing (I know of
  `bn100130729` — all blocks "no plugins"; confirm the cause and whether it is honest).
- **D3.** Reproducibility: pick ONE completed burst and check that the checked-in producers
  reproduce its fit table from cold (same blocks file, same catalog → same winners). If exact
  reproduction is not expected (multistart randomness), say what the tolerance should be and
  whether the code guarantees it.

## E. Claims that will become paper numbers
- **E1.** In `paper_agentic/agentic_grb_v2.tex`: verify every quantitative claim against the
  products as they stand today, and list the ones that are now FALSE (not merely stale).
- **E2.** The two-operator reproduction record `notes/reconciliation/bn200524211_verification.md`
  asserts agreement < 0.6σ on α/Ep/β against Khushboo's independent run, and that σ-distance
  ranks by frame proximity across five frames. Recompute from
  `results/verification_khushboo_200524211/bn200524211/spectral_fits.ecsv` and the quoted
  published values. This is destined to be §5's headline — it must be exactly right.

---

## Verification rules that matter (these are why past reviews found real bugs)
- Check against **external** sources — the published PDF, the archived GCN circular, the FITS
  header, the threeML/astromodels source — **never** against a file we derived. A
  self-consistency check is circular by construction and will pass while wrong.
- An invariant that cannot find its reference must **fail loudly**, not skip.
- For any generated artefact, check that the checked-in producer reproduces it **from cold**.
- Prefer a demonstration (recompute, re-render, diff) over an argument.

## Output contract
```
VERDICT — SIGN OFF or DO NOT SIGN OFF (state plainly)
Per item (A1..E2): CONFIRMED / NOT CONFIRMED, with the derivation shown
DISCREPANCIES: each with the exact fix
COULD NOT VERIFY: what and why
```
Rank discrepancies by whether they can change a paper number.

Finally, your own independent judgement: anything wrong or fragile that this brief did not
ask about.

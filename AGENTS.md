# AGENTS.md — operating guide for an AI agent running this repo

This file orients an AI coding agent (Codex or Claude Code, in a local terminal) to
the **Two_Breaks** single-pulse GRB time-resolved spectroscopy pipeline. It is
self-contained: everything needed to run the pipeline is here, with exact commands.
Claude Code reads `CLAUDE.md` (a pointer to this file); Codex reads this file directly.

**Your role.** You drive the repo end-to-end — install, fetch data, run the stages,
QC. One step (approval of detectors / background / source) is a *judgement* call: it
may be made by a **human** (interactive GUI) **or by you, the AI** (read the
light-curve PNGs and decide). Either way the decision is **recorded with a gate
stamp** (who approved, when, how) so it is auditable. **Never fabricate an approval
silently** — if you approve, stamp it as AI-approved; if a human must decide, say so.

---

## 1. What this pipeline does

Selects single-pulse GRBs from Fermi/GBM, and for each: picks detectors, fits a
polynomial background, defines the source/emission window, **bins** the light curve
(Bayesian Blocks + significance hybrid), and **fits 6 spectral models** per time bin,
choosing a winner by AIC. Population products (figures, tables, numbers) follow.

Authoritative flow (locked; see `dev/AUTHORITATIVE_PIPELINE.md`):
**Stage 1 Approve** (detectors + background + source, gated) → **Stage 2 Bin**
(`27b`) → **Stage 3 Fit** (`29`→`10`) → **Products** (`31`–`38`).

---

## 2. Environment

Two tiers. Use the light tier where it suffices; the heavy tier is needed for
anything that touches 3ML response handling (data download, binning, fitting).

**Heavy tier — threeML + fermitools (binning, fitting, data download):**
```bash
conda activate threeML          # env at /Users/salim/anaconda3/envs/threeML
export FERMI_DIR=$CONDA_PREFIX/share/fermitools
export CALDB=$FERMI_DIR/data/caldb
export CALDBCONFIG=$CALDB/software/tools/caldb.config
export CALDBALIAS=$CALDB/software/tools/alias_config.fits
export CALDBROOT=$CALDB
export EXTFILESSYS=$FERMI_DIR/refdata/fermi
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
```
Scripts `02, 10, 27b, 29, 31, 32, 34` (and `00` phases 1/3) need this. `10`/`29`
auto-set CALDB from a hardcoded fallback if unset, but **export it explicitly** for
portability to a new machine — do not rely on the fallback path existing.

**Light tier — numpy/scipy/astropy/matplotlib only (no threeML):**
Scripts `01, 03, 28, 30, 33, 35, 36, 38` and `handoff_background_approval/fetch_tte.py`.
Install: `pip install -r handoff_background_approval/requirements.txt` (plus a GUI
backend — PyQt5 — for the interactive picker; force with `MPLBACKEND=QtAgg`/`TkAgg`).

If you (the agent) need to *install* threeML to run the heavy tier — do it. Heaviness
is not a reason to skip a stage.

---

## 3. Data

Raw GBM data is **not** all in the repo (only 6 sample bursts are committed:
`bn110721200, bn081125496, bn150902733, bn160625945, bn090620400, bn201016019`).
For the full 106 you must download.

- **Full data (TTE + CSPEC + RSP + POSHIST), heavy tier:**
  `python scripts/02_download_data.py` (uses 3ML's `download_GBM_trigger_data`; reads
  `results/single_pulse_grbs.ecsv`; idempotent; writes `data/<trigger>/...`).
- **TTE only (light tier, for the picker):**
  `python handoff_background_approval/fetch_tte.py` (stdlib urllib from HEASARC; reads
  `results/background_starting_points.ecsv`; idempotent).
- Binning and fitting need the **responses** (`.rsp`/`.rsp2`) and POSHIST too, so for
  the full chain use `scripts/02` (or fetch the responses some other way), not the
  TTE-only fetcher.

Committed catalogs (the entry points — already present, no rebuild needed):
`results/single_pulse_grbs.ecsv` (106-burst sample), `results/background_starting_points.ecsv`
(418 (trigger,det) review rows), `results/background_intervals_clean.ecsv` (provisional
algorithmic backgrounds), `results/clean_blocks/` (provisional blocks).

---

## 4. The pipeline — exact commands

> **Built vs planned.** Commands below marked ✅ are runnable today. Items marked 🔧
> are the **locked-but-not-yet-built** approval extension (detector + per-burst source
> + unified AI/human gate) — see `dev/AUTHORITATIVE_PIPELINE.md`. Do **not** invent
> commands for 🔧 items; build them per the spec, or run the ✅ path.

### Stage 1 — Approval (gated: human GUI *or* AI-vision)
**Background windows ✅ (runnable, stamped):**
```bash
python scripts/30_background_picker.py --approver "<name or 'Claude (AI)'>"
python scripts/36_progress_check.py        # progress + QC (418/418, 106/106, stamp check)
```
`scripts/30` opens each detector's light curve pre-drawn with a suggested window;
Accept / Clear+redraw / Skip / Quit. Every accepted row is stamped `APPROVED_BY,
APPROVED_UTC, WINDOW_SOURCE` into `results/background_intervals.ecsv`. Resumable.
`--approver` is required. (The AI-vision path renders LC PNGs via
`scripts/00_prototype_one_burst.py` and you read them to propose windows.)

**Detector approval 🔧** — exists today only as a single-burst GUI
(`00_prototype_one_burst.py:pick_detectors_with_angles_gui`, POSHIST ≤50° angle math).
Not yet wired into a scaled, stamped driver. **Currently the detector SET is taken
as-is** from the sample catalog; gating it is the planned build.

**Source/emission window 🔧** — to be approved **explicitly per burst** (mark
start+stop on the brightest-NaI light curve), written as `SRC_START, SRC_STOP`.
Today the source is *implicit* (`[pre_stop, post_start]`, auto-tightened by an
`emission_window` heuristic inside `27b`). The explicit per-burst approval is planned.

### Stage 2 — Binning ✅ (heavy tier)
```bash
python scripts/27b_reblock_3ml.py --bkg results/background_intervals.ecsv \
       --out results/clean_blocks --sigma 5.0
```
3ML Bayesian Blocks (`use_background=True`) + **significance-merge hybrid**: trim
sub-`SIGMA_FLOOR` (=5σ) leading/trailing blocks, then merge interior sub-floor blocks
into a neighbour. Significance from 3ML's `Significance.li_and_ma_equivalent_for_gaussian_background`.
Writes `results/clean_blocks/bb_blocks_spectral_<trigger>.ecsv`. (`scripts/27` is the
**deprecated** astropy-BB predecessor — do not use it for authoritative runs.)
*Planned:* read explicit `SRC_START/SRC_STOP` instead of the `emission_window` heuristic.

### Stage 3 — Spectral fits ✅ (heavy tier)
```bash
python scripts/29_refit_clean.py --bkg-file results/background_intervals.ecsv \
       --blocks-dir results/clean_blocks --out-root results/clean_per_burst --nproc 8
```
`29` is the parallel, resumable driver; per burst it runs `scripts/10`. For each bin
interval, `10` builds a per-bin 3ML spectrum: `TimeSeriesBuilder.from_gbm_tte` /
`from_lat_lle` with the **response** loaded (`.rsp`/`.rsp2`, with an rsp2→single-matrix
collapse fallback), `set_background_interval(pre,post)` to load the **polynomial
background** (auto order via LRT, carried into every bin → pgstat: Poisson source +
Gaussian background), `create_time_bins(method='custom')` on the approved edges →
`to_spectrumlike(from_bins=True)` → per-bin `DispersionSpectrumLike` **plugins**, with
`set_active_measurements` per detector (NaI 8.1–33/40–900 keV + K-edge mask, BGO
0.3–40 MeV, LLE 30–100 MeV) and cross-calibration constants 0.8–1.2 (frozen to 1 for
the reference NaI). It then fits the 6 models (Band, CPL, SBPL, DSBPL, Band+BB,
CPL+BB) jointly across plugins per block + time-integrated, selects a winner by
AIC/BIC/LRT with a physical-validity gate + DSBPL multi-start, and writes
`results/clean_per_burst/<trigger>/spectral_fits.{ecsv,json}`.
**Use a FRESH `--out-root` for an authoritative run** (don't clobber/mistake provenance).

### Products ✅ (after fits)
```bash
python scripts/31_draft_numbers.py     # -> results/draft_numbers.json + clean_sample_all_models.ecsv  (heavy)
python scripts/32_make_figures.py      # -> paper/two_break_figures/*.pdf                                (heavy)
python scripts/33_machine_tables.py    # -> paper/two_break_tables/*.csv                                 (light)
python scripts/34_example_spectra.py   # -> fig_spec_a/b.pdf (130427A, 110721A)                          (heavy)
python scripts/35_variability_bb.py    # -> results/variability_bb.ecsv                                  (light)
python scripts/38_build_manifest.py    # -> results/master_manifest.csv                                  (light)
python scripts/37_build_full_notebook.py   # -> notebooks/Two_Breaks_single_GRB_pipeline.ipynb (template) (light)
```

---

## 5. Key files & schemas

- `results/single_pulse_grbs.ecsv` — sample: `TRIGGER_NAME, T90, FLUENCE, DETECTOR
  (brightest NaI), CLASSIFICATION, HAS_LAT`.
- `results/background_starting_points.ecsv` — 418 review rows (== current clean).
- `results/background_intervals.ecsv` — **the approved catalog** (Stage 1 output):
  `..., BKG_NEG/POS_START/STOP, APPROVED_BY, APPROVED_UTC, WINDOW_SOURCE` (+ planned
  `SRC_START/STOP`). Consumed by `27b` (`--bkg`) and `29`/`10` (`--bkg-file`).
- `results/clean_blocks/bb_blocks_spectral_<trig>.ecsv` — bins: `TRIGGER_NAME,
  DETECTOR, BLOCK_INDEX, T_START, T_STOP, SIGNIFICANCE, IS_MERGED, CONSTITUENT_COUNT,
  POLY_ORDER`.
- `results/clean_per_burst/<trig>/spectral_fits.{ecsv,json}` — the fit catalog
  (one row per bin×model + winner) and metadata (`canonical_det`, `fit_dets`, bins).

---

## 6. Gotchas (must-know to run correctly)

- **Run from repo root** — relative `data/`, `results/`, `plots/` paths assume it.
- **Heavy tier needs CALDB exported** (§2) — symptom if not: 3ML response/IntervalOfInterest errors.
- **GUI backend on macOS**: use `macosx` (auto-selected), not `TkAgg` (crashes on the
  2nd figure). Override via `MPLBACKEND`. A cloud/no-display agent cannot run the GUI —
  use the AI-vision approval path instead.
- **`27b`/`29`/`10` require explicit `--bkg`/`--bkg-file`** — no silent defaults, by design.
- **Resumability**: `30` (per row), `29`/`10` (skip if `spectral_fits.ecsv` exists),
  `02`/`fetch_tte` (skip present files). Safe to re-run.
- **`scripts/27` and `scripts/11` are legacy** (astropy-BB binning; old full runner).
  Use `27b` + `29` for authoritative runs.
- **The current numbers/catalog are PROVISIONAL** (built on algorithmic backgrounds).
  The authoritative run requires the approved `background_intervals.ecsv` (Stage 1).

---

## 7. Known audit items (resolve in the authoritative re-fit)

From `dev/CODEX_AUDIT_REPORT_PIPELINE.md` / `notes/PROJECT_AUDIT_2026-06-09.md`:
1. Sample selection has an undocumented `T90>2s` cut; Busby procedure not enforced.
2. Ep–kT pairing should use the same composite (Band+BB) fit consistently.
3. ν_m–ν_c relation should restrict to *decisive* 2SBPL bins.
4. Sub-128 ms variability claim needs a calibrated false-alarm test (stub only).
5. DSBPL/2SBPL multi-start convergence — handled in `10` now; verify in the re-fit.

---

## 8. Pointers
- `dev/AUTHORITATIVE_PIPELINE.md` — the locked end-to-end plan + the Stage-1 build spec.
- `BACKGROUND_SELECTION_PROCESS.md` — full detector/background selection ruleset.
- `handoff_background_approval/` — the approval-step handoff (SKILL + fetcher + reqs).
- `README.md` — project overview + references.

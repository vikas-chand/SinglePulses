# AGENTS.md — operating guide for an AI agent running this repo

This file orients an AI coding agent (Codex or Claude Code, in a local terminal) to
the **Two_Breaks** single-pulse GRB time-resolved spectroscopy pipeline. It is
self-contained: everything needed to run the pipeline is here, with exact commands.
Claude Code reads `CLAUDE.md` (a pointer to this file); Codex reads this file directly.

**YOU ARE THIS SYSTEM'S AGENT, NOT AN INDEPENDENT AI.** (Vikas, 2026-08-13, after an
afternoon lost to exactly this.) This repo is an instrument with a decade of decisions
built into it. Your first move when asked for anything — a figure, a table, a check, a
product — is **INVENTORY, NOT BUILD**:

```bash
python scripts/00_inventory.py            # what already exists and what it produces
python scripts/00_inventory.py --find "background"   # or search by topic
```

Then one of three outcomes, in this order of preference:
1. **A tool already does it** → run it. Do not rewrite it.
2. **A tool nearly does it** → extend THAT tool. One implementation per job.
3. **Nothing does it** → build, and say plainly in your reply what you searched and why
   nothing fit.

Cross-project tools count: `~/Desktop/LATBright/GRB260226A/plot_config.py` (figure
style), `~/Desktop/LATBright/skills/` (GCN, QPO, bibliography), `~/Desktop/Projects/
CaptionHelper/` (captions), `~/Desktop/Projects/reference_general_figure_style.md`
(the figure authority). The global `~/.claude/CLAUDE.md` says it directly: *prefer the
existing workflows over re-inventing.*

**Why this is a hard rule, not advice.** On 2026-08-13 an agent asked for "a figure for
every pipeline step" wrote `scripts/44_step_figures.py` from scratch — reimplementing
`scripts/approved_selection_png.py` (background + source panels, working since
2026-07-16) and `scripts/block_plots.py` (Bayesian blocks, since 2026-07-17) — and then
spent hours rediscovering the bugs those scripts had already fixed: zero-cliff bins,
y-limits anchored at zero, polynomials drawn past their fitting windows, light curves
as lines instead of histograms. Reimplementation does not start from zero; it starts
from *negative*, because it discards the debugging already paid for.

**Your role.** You drive the repo end-to-end — install, fetch data, run the stages,
QC. One step (approval of detectors / background / source) is a *judgement* call: it
may be made by a **human** (interactive GUI) **or by you, the AI** (read the
light-curve PNGs and decide). Either way the decision is **recorded with a gate
stamp** (who approved, when, how) so it is auditable. **Never fabricate an approval
silently** — if you approve, stamp it as AI-approved; if a human must decide, say so.

**THE OPERATING PROTOCOL for the burst-by-burst campaign.** Any per-burst request —
"next burst", "step by step", a review, a walkthrough — is governed by
**`dev/ai_guides/BurstWalkthrough.md`. Read it BEFORE running the first step.** In brief:

> **Agent roster:** `dev/ai_guides/AgentArchitecture.md` — the deliberate
> per-step agent design (producer/verifier/approver/auditor/distiller +
> mechanical enforcement), born 2026-08-15. Every step declares its agents
> and their single purpose; contracts derive from PI rulings.
- Step ledger **0b, 0, 1–9** (literature harvest → identity/GCN → data inventory →
  detectors → background → source → binning → spectral fitting → temporal → νFν → QC),
  each step bound to its skill file in `dev/ai_guides/`.
- Per step: **RUN → PRESENT** (what the step does / what actually ran / conclusions with
  honest flags / anomalies) **→ GATE** (Vikas approves EVERY step; nothing advances on
  silence) **→ LITERATURE** diff **→ DISTILL** lessons into the step's skill file.
- **Steps 2–5 are ADOPT mode**: Stage-1 selections and blocks are recorded human
  decisions — present their provenance stamps, never re-pick or re-adjudicate; they
  re-open only if a downstream check implicates them.
- Burst order + per-burst product locations: `notes/REVIEW_INDEX_106.md`. Read the
  burst's `REPORT_<trig>.md` + `PRODUCTS.md` (in its products dir) **before** deriving
  anything by hand — the generated report already carries the literature, the frozen
  P0 predictions, and every figure.
- One command rebuilds a burst's complete product set + manifest:
  `python scripts/45_all_products.py --trig <trig> --out <dir>`.

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

**`grb_pipeline` (the GRB_Handbook inheritance) — needed for the SCIENCE path only.**
`scripts/pipeline_grb.py` and `parity_grb.py` do `import grb_pipeline as grb` — the
shared, audited binning + fitting package that Two_Breaks Stage 2–3 delegates to.
**The Stage-1 approval tools (`scripts/39`, `scripts/00`) do NOT need it** — they are
self-contained (light tier). Install `grb_pipeline` only if you run the science path:
```bash
# from the main branch of the package repo (grb_pipeline lives on `main`, NOT the
# default `master` branch, which is the original notebook-era GRB_Handbook):
pip install "git+https://github.com/vikas-chand/GRB-Handbook.git@main#egg=grb-pipeline"
# or, if you have it cloned locally (editable):  pip install -e /path/to/GRB_Handbook_Project
```
Verify: `python -c "import grb_pipeline as g; print(g.__version__)"`. NOTE the repo's
default branch is `master` (a *different*, older tree); always pin `@main` for the
package.

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

> All stages below are ✅ runnable. The unified gated approval driver (`scripts/39`)
> is built; its `gui` path needs a live display, the `render`+`ingest` paths do not.
> See `dev/AUTHORITATIVE_PIPELINE.md` for the design rationale.

### Stage 1 — Approval (gated: human GUI *or* AI-vision) ✅
**`scripts/39_approve_all.py` is the unified, gated driver** — it approves all three
(detectors + background + per-burst source) and writes ONE stamped catalog
`results/background_intervals.ecsv` (schema in §5; gate columns `APPROVED_BY,
APPROVED_UTC, APPROVAL_MODE, WINDOW_SOURCE`). Approval may be human *or* AI; the gate
records which. Three steps:

```bash
# 1) render candidates + LC PNGs + a per-burst manifest (light; no threeML)
python scripts/39_approve_all.py render --all          # or --trigger bn...

# 2) AI-VISION (you, the agent): read results/approval/<trig>_pending.json + the PNGs
#    in plots/approval_lc/, decide approved detectors + per-det bkg windows + the
#    per-burst source, and WRITE results/approval/<trig>_decision.json (schema in the
#    scripts/39 docstring; set "approver":"Claude (AI)"/"Codex (AI)", "mode":"ai_vision").
#    NEVER fabricate silently — the stamp records that the AI approved it.

# 3) ingest the decisions -> the stamped catalog (light)
python scripts/39_approve_all.py ingest --all
```

**Two-AI consensus (how the current catalog was built, 2026-07).** For robustness the
AI-vision step was run as a **Claude + Codex consensus**: each independently wrote a
`decision.json` reading the SAME guides; agreements auto-approved (detector-Jaccard ≥
0.8 **and** source-IoU ≥ 0.5), disagreements were adjudicated by a third vision pass,
then a **margin re-selection** enforced the hug-the-burst rule. Machinery:
`scripts/consensus_reconcile.py`, `consensus_codex_track.py`, `consensus_flag_lc.py`,
`approved_selection_png.py`. Provenance is in `APPROVED_BY` (`Claude+Codex (AI
consensus)[, adjudicated][ + margin-reselect]`). A final independent Codex QA lives in
`notes/codex_bkg_review.md`.

**The judgement rules** live in `dev/ai_guides/` — read them before approving:
`background_selection.md` (incl. the **HUG-THE-BURST 5–20 s margin band** — the inner
edge sits near the burst but with a safe buffer; never anchor on a data-gap/SAA-exit
edge, never on a no-data segment), `detector_selection.md`, `source_selection.md`.
Current catalog: **106/106 bursts, 0 source-in-gap violations, all margins in [5,40] s**;
a human (Khushboo) sign-off pass is the last gate before the Stage 2–3 re-fit.

**Human GUI path** (when a person clicks): `python scripts/39_approve_all.py gui
--trigger bn... --approver "Khushboo Sharma"` — runs the detector picker (POSHIST ≤50°
angle math) → background selector per detector → a 2-click source marker, then writes
the same `decision.json` (`mode=human_gui`) and ingests it.

`scripts/30_background_picker.py` (+ `scripts/36_progress_check.py` for progress/QC)
remains as the **background-only** human picker if you want to approve just windows;
its output schema is a subset of the unified catalog.

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
It uses the **approved** `SRC_START/SRC_STOP` from the catalog when present, falling
back to the `emission_window` heuristic only if the burst has no approved source.

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
- `results/background_intervals.ecsv` — **the approved catalog** (Stage 1 output from
  `scripts/39`): `TRIGGER_NAME, DETECTOR, BKG_NEG/POS_START/STOP, SRC_START, SRC_STOP,
  DET_ANGLE, APPROVED_BY, APPROVED_UTC, APPROVAL_MODE, WINDOW_SOURCE`. Only approved
  detectors get rows (detector approval is implicit in row presence). Consumed by `27b`
  (`--bkg`, uses `SRC_*`) and `29`/`10` (`--bkg-file`, uses `BKG_*`).
- `results/approval/<trig>_pending.json` (render output) / `<trig>_decision.json`
  (the agent's or GUI's approval; `scripts/39` ingests it). Schema in the `scripts/39` docstring.
- `results/clean_blocks/bb_blocks_spectral_<trig>.ecsv` — bins: `TRIGGER_NAME,
  DETECTOR, BLOCK_INDEX, T_START, T_STOP, SIGNIFICANCE, IS_MERGED, CONSTITUENT_COUNT,
  POLY_ORDER`.
- `results/clean_per_burst/<trig>/spectral_fits.{ecsv,json}` — the fit catalog
  (one row per bin×model + winner) and metadata (`canonical_det`, `fit_dets`, bins).

---

## 6. Gotchas (must-know to run correctly)

- **Run from repo root** — relative `data/`, `results/`, `plots/` paths assume it.
- **Heavy tier needs CALDB exported** (§2) — symptom if not: 3ML response/IntervalOfInterest errors.
- **GUI backend**: macOS = `macosx` (auto-selected); Linux = `MPLBACKEND=TkAgg` (the
  verified backend — the old 2nd-figure TclError crash is FIXED by the keep-alive root
  + between-window event drain, see `dev/GUI_REQUIREMENTS.md` R-BG-20). A cloud/
  no-display agent cannot run the GUI — use the AI-vision approval path instead.
- **`29`/`10` require explicit `--bkg-file`** — no silent defaults (H2, done 2026-07-16).
  `27b --bkg` has a fallback chain that PREFERS the gated `background_intervals.ecsv`
  and prints which file it used — still pass `--bkg` explicitly in authoritative runs.
- **Resumability**: `30` (per row), `29`/`10` (skip if `spectral_fits.ecsv` exists),
  `02`/`fetch_tte` (skip present files). Safe to re-run.
- **`scripts/27` and `scripts/11` are legacy** (astropy-BB binning; old full runner).
  Use `27b` + `29` for authoritative runs.
- **Catalog vs numbers state (2026-07-16):** the approved consensus
  `results/background_intervals.ecsv` EXISTS (106/106, stamped, margin-band clean;
  Khushboo sign-off pending). The PAPER NUMBERS remain provisional: the Stage 2–3 fits
  in `results/clean_per_burst_consensus/` predate the margin re-selection for **59
  bursts** (worklist: `dev/stale_refit_worklist.txt`) — re-block + re-fit those after
  the human sign-off, then regenerate `31`–`38`.

---

## 7. Known audit items (resolve in the authoritative re-fit)

From `dev/CODEX_AUDIT_REPORT_PIPELINE.md` / `notes/PROJECT_AUDIT_2026-06-09.md`:
1. Sample selection has an undocumented `T90>2s` cut; Busby procedure not enforced.
2. Ep–kT pairing should use the same composite (Band+BB) fit consistently.
3. ν_m–ν_c relation should restrict to *decisive* 2SBPL bins.
4. Sub-128 ms variability claim needs a calibrated false-alarm test (stub only).
5. DSBPL/2SBPL multi-start convergence — handled in `10` now; verify in the re-fit.
6. `scripts/10`'s time-integrated (T_INT) window does not yet read the approved
   `SRC_START/SRC_STOP`; the per-block bins do (via `27b`). Small follow-up to make
   T_INT use the approved source too.

---

## 8. Pointers
- `PROJECT.md` — the two-part program: Part 1 (AI-vs-human benchmark, methods paper,
  V. Chand) validates the method; Part 2 (the single-pulse science, K. Sharma) uses it.
- `dev/BENCHMARK_PLAN.md` + `dev/ai_guides/` — Part 1 framework + per-task AI judgement guides.
- `dev/AUTHORITATIVE_PIPELINE.md` — the locked end-to-end plan + the Stage-1 build spec.
- `BACKGROUND_SELECTION_PROCESS.md` — full detector/background selection ruleset.
- `handoff_background_approval/` — the approval-step handoff (SKILL + fetcher + reqs).
- `README.md` — project overview + references.

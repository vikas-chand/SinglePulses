# QUICKSTART — running the Two_Breaks pipeline from a fresh clone
Written 2026-08-05 for **Khushboo Sharma** and **Jagdish C. Joshi**, from an actual end-to-end
run of **GRB 110721A** on the maintainer's machine. Every command below was executed, not guessed.

> **Read `AGENTS.md` for the full pipeline description.** This file is the minimum path to a
> working run, plus an honest list of what a clone does NOT give you.

---

## 0. What you get in the clone (and what you don't)

**✅ Tracked (you get these):** all `scripts/`, the skills in `dev/ai_guides/`, `AGENTS.md`,
`requirements.txt`, the **approved Stage-1 catalog** `results/background_intervals.ecsv`
(435 detector rows, human-stamped), `results/grb_sample.ecsv`, and **raw data for 6 bursts**.

| burst | files | LLE? | LAT? | approved selection |
|---|---|---|---|---|
| **bn110721200** (GRB 110721A) | 20 | **yes** | no | yes ← **use this one** |
| bn160625945 | 20 | yes | no | yes |
| bn150902733 | 17 | yes | no | yes |
| bn090620400 | 16 | no | no | yes |
| bn201016019 | 13 | no | no | yes |
| bn081125496 | 7 | no | no | yes |

**❌ NOT in the clone — do not be surprised:**
- **`results/` is gitignored** except the two catalogs above. So there are **no pre-made Bayesian
  blocks and no pre-made fits.** You regenerate them — that is the point of Step 5 below.
- **No LAT (>100 MeV) data.** The `data/<trig>/LAT/` directories are local-only, so
  `--include-lat` will not work from a clone. GBM + LLE does.
- **The other 100 bursts' data** (~18 GB locally). Download with the FSSC tools if you need them.
- **`GRB_Handbook_Project`** — a SEPARATE repo. Step 7 (temporal) imports it from a hardcoded
  `~/Desktop/Projects/GRB_Handbook_Project`; without it, Step 7 will fail. Steps 0,1,5,6,8,9 do not need it.

---

## 1. Environment (the heavy tier)

You need **threeML + astromodels + Fermitools** in one conda env. On the maintainer's Mac the env
is called `threeML`.

```bash
conda create -n threeML -c conda-forge -c threeml python=3.9 threeml astromodels fermitools
conda activate threeML
pip install -r requirements.txt
```

**CALDB must be exported before every heavy step** — this is the single most common failure:

```bash
export FERMI_DIR=$CONDA_PREFIX/share/fermitools
export CALDB=$FERMI_DIR/data/caldb          # NOTE: data/caldb, NOT refdata/caldb
export CALDBCONFIG=$CALDB/software/tools/caldb.config
export CALDBALIAS=$CALDB/software/tools/alias_config.fits
export CALDBROOT=$CALDB
export EXTFILESSYS=$FERMI_DIR/refdata/fermi
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
```

Check it: `ls $CALDB/data/glast/lat/caldb.indx` must exist. If it doesn't, the fit dies with
`TipException: File not found: .../caldb.indx`.

**Always run from the repo root** — every path in the scripts is relative to it.

---

## 2. The demo run — GRB 110721A, step by step

```bash
git clone https://github.com/vikas-chand/SinglePulses.git
cd SinglePulses
conda activate threeML          # + the CALDB exports above
export T=bn110721200
```

### Step 5 — Binning (Bayesian blocks + significance merge)
```bash
python scripts/27b_reblock_3ml.py --burst $T \
  --out results/demo/blocks \
  --bkg results/background_intervals.ecsv
```
**Expected (this is the reproducibility check — your numbers should match):**
```
bn110721200 [n6]: src=[-0.756,18.933] (approved+tightened) BB=11 -> trim+merge(>= 5 sigma)=10
  blk 0:  -0.043- 0.081  sig= 11.3   ...   blk 2: 0.470- 1.955  sig= 76.7
  blk 9:  13.865-18.933  sig=  7.8
```
10 blocks, peak significance ≈ 77. If you get 10 blocks with those edges, the chain is working.

### Step 6 — Spectral fitting (GBM + LLE, 24-model menu)
```bash
python scripts/10_spectral_fit_burst.py --trigger $T \
  --blocks-file results/demo/blocks/bb_blocks_spectral_$T.ecsv \
  --bkg-file results/background_intervals.ecsv \
  --out-dir results/demo/fit \
  --include-bgo --models highe
```
- `--models highe` = the 24-model menu (6 base + free-smoothness + 16 high-energy composites).
  Use `--models default` for just the frozen 6 — **much faster**, good for a first test.
- `--blocks-file` and `--bkg-file` are **REQUIRED with no defaults** (deliberate: no silent inputs).
- LLE is added automatically when `data/<trig>/gll_*` exists and an `lle` row is approved.
- **Runtime: ~45–60 min** for `highe` on 10 blocks × 6 detectors. `default` is far quicker.
- Writes: `spectral_fits.ecsv` (10 rows × 830 cols), `spectral_fits.json`,
  `spectral_evolution.png`, `ep_kt_correlation.png`.

### Step 8 — νFν diagnostic panels
```bash
export BLOCKS_ROOT=$PWD/results/demo/blocks
export FIT_ROOT=$PWD/results/demo
python scripts/41_nuFnu_panels.py --trig $T \
  --dets n6,n7,n9,nb,b1,lle --ref n6 --mode best --out results/figures
```
Three modes: `--mode best` (best model per bin), `--mode model --model Band+BB` (one model across
all bins), `--mode bin --bin 3` (all models in one bin — the diagnostic view).
⚠ **`BLOCKS_ROOT` and `FIT_ROOT` must be set**, or it silently reads a different run's blocks.
⚠ Known limitation: `--mode best` internally refits only the **6 base models**, so its "best" can
disagree with the saved 24-model winner. Use `--mode bin` when you need the full picture.

---

## 3. How to know it worked

| check | expected |
|---|---|
| Step 5 blocks | **10** blocks, `[-0.043, 18.933]`, peak σ ≈ 77 |
| Step 6 rows | `spectral_fits.ecsv` = **11 rows** (10 blocks + T_INT), 830 columns |
| detectors used | `spectral_fits.json` → `fit_dets: [n6,n7,n9,nb,b1,lle]` |
| T_INT fit | Band α ≈ −1.0, Ep ≈ 520 keV; a **strong** blackbody (LRT ≈ 62) |
| statistic | threeML picks **PGSTAT** automatically — we never set one |

Published comparison for this burst (GCN 12187): Band Ep = 372 ± 25 keV, α = −0.94, β = −1.77,
time-integrated. Our per-block Ep runs higher early — that is real evolution, not an error.

---

## 4. Things that will bite you

1. **CALDB path.** `$FERMI_DIR/data/caldb`, not `refdata/caldb`. Wrong path → `caldb.indx` not found.
2. **Not running from the repo root.** All relative paths break.
3. **Forgetting `BLOCKS_ROOT`/`FIT_ROOT` in Step 8** → panels drawn on the wrong run's bins.
4. **`--include-lat` from a clone** → no LAT data tracked; it will fail. GBM+LLE only.
5. **Step 7 (temporal)** needs the separate `GRB_Handbook_Project` repo at
   `~/Desktop/Projects/GRB_Handbook_Project`. Also: its **spectral-lag sign is currently INVERTED**
   vs the standard convention, and its **T90 errors are unreliable** — do not quote either yet.
6. **Hardcoded maintainer paths** remain in `scripts/29_refit_clean.py`, `scripts/08_*`,
   `scripts/37_*`, `scripts/consensus_flag_lc.py`. The steps above avoid them; if you use those
   scripts, edit the path first.
7. **macOS has no `timeout`**; long runs should use `nohup ... &` and a log file.

---

## 5. Where the method is written down
- `AGENTS.md` — the authoritative, tool-agnostic pipeline description.
- `dev/ai_guides/` — one skill file per pipeline step, each carrying its own distilled lessons:
  `GCNIntelligence.md` (Step 0), `DataInventory.md` (Step 1, response-validity checks),
  `detector_selection.md` / `background_selection.md` / `source_selection.md` (Steps 2–4),
  **`SpectralFitting.md` (Steps 6+8 — the flagship, 17 lessons L1–L17)**, `qc_flagging.md` (Step 9),
  `BurstWalkthrough.md` (the master gated protocol).
- `notes/reconciliation/<trigger>.md` — per-burst records comparing our result to the literature.
- ⚠ `Binning.md` (Step 5) and `Temporal.md` (Step 7) **do not exist yet** — those two steps are the
  least documented and least verified parts of the pipeline.

## 6. Doctrine worth knowing before you interpret anything
- **ΔAIC is an evidence ratio** `exp(ΔAIC/2)`: ≥6 = strong (20:1), ≥10 = decisive (148:1). Report the
  ratio, not a bare verdict (lesson L16).
- **A railed parameter does not invalidate a derived quantity** — check whether the quantity is
  stable across models and quote it from a VALID one (L15).
- **Never drop a detector for low significance.** The inclusion gate is DATA QUALITY (valid response,
  reviewed background), never detection significance — dropping on significance biases the census
  toward spurious high-energy components (L17).
- Significance floor **S ≥ 10 is a quality FLAG, not a hard cut** (L6b).

# Two Breaks Project — Implementation Plan

## Goal
Apply the Busby & Lazzati (2024) horizontal-line algorithm to identify single-pulse GRBs among bright Fermi GBM + LAT-LLE detected GRBs, then perform BB+Band spectral fitting (à la Burgess 2014/2019) on the single-pulse sample to search for the Ep–kT correlation.

---

## Phase 1: Build the GRB Sample

### Step 1.1 — Query the Fermi catalogs
- Query `fermilgrb` (Fermi LAT GRB catalog) via `astroquery.heasarc` to get all LAT-detected GRBs (includes LLE detections)
- Query `fermigbrst` (Fermi GBM burst catalog) for fluence, T90, trigger names
- Cross-match on trigger name to get GBM+LAT/LLE GRBs
- Apply a **fluence cut**: fluence > **1e-5 erg/cm²** (very bright GRBs)
- **No T90 restriction** — include both short and long GRBs
- Save the final sample as a table

### Step 1.2 — Download TTE data
- For each GRB in the sample, use `download_GBM_trigger_data()` from 3ML to download TTE + RSP files
- Select the 2 brightest NaI detectors (from detector mask in catalog)
- Store data in organized directories: `data/{trigger_name}/`

---

## Phase 2: Implement Busby & Lazzati Single-Pulse Classification

### Step 2.1 — Build light curves from TTE data
- For each GRB, load TTE data using 3ML's `TimeSeriesBuilder`
- Define the region of interest per Busby & Lazzati Eq. 1:
  `max(T90start - 0.5*T90, Tdstart) ≤ t ≤ min(T90start + 2*T90, Tend)`
- Bin into **120 equal-length bins** (bin duration = T90/48 when possible)
- Compute background from median counts outside T90 interval

### Step 2.2 — Horizontal line algorithm
Implement the algorithm from Section 2.2 of Busby & Lazzati:
- Place 16 equally-spaced horizontal lines between:
  - Highest: 2σ below peak count rate
  - Lowest: 2σ above background (exclude this line from scoring)
- For each of the 15 scoring lines:
  - Find points ≥ 1σ above the line
  - Identify first and last crossing
  - Count "failure points" between crossings that are ≥ 1σ below the line
  - Add failure count to running total
- Normalize: score = 1 - (total_failures / (15 × 120))
- Score ≈ 1 → single-pulse; score ≈ 0 → multi-pulse

### Step 2.3 — Classify GRBs
- Apply a threshold (Busby & Lazzati used 0.9983, corresponding to ≤3 unnormalized failures) to split into:
  - **Single-pulse GRBs** (score ≥ threshold)
  - **Rest** (multi-pulse / ambiguous)
- Output: two lists of GRBs with their scores

---

## Phase 3: Bayesian Blocks Binning (Burgess method)

For the **single-pulse GRBs**:
### Step 3.1 — Bayesian blocks time binning
- Use 3ML `TimeSeriesBuilder.create_time_bins(method='bayesblocks')`
- This replaces the equal-binning from Phase 2 with physically motivated bins
- Generate PHA files for each time bin

---

## Phase 4: BB + Band Spectral Fitting (Burgess 2014 approach)

For each time bin of each single-pulse GRB:
### Step 4.1 — Set up spectral model
- Model: **Band function + Blackbody** (BB+Band)
- In 3ML/astromodels: `Band() + Blackbody()`
- Fit using 3ML joint likelihood with GBM NaI + BGO (+ LAT-LLE if available)

### Step 4.2 — Extract Ep and kT
- From each time-bin fit, extract:
  - `Ep` (peak energy of Band component)
  - `kT` (blackbody temperature)
  - Fluxes of both components
  - Uncertainties on all parameters

### Step 4.3 — Correlation analysis
- For each GRB: fit `Ep ∝ T^α` (power law) to the (kT, Ep) pairs
- Determine α and its uncertainty
- Classify jet type: α ≈ 1 → baryonic; α ≈ 2 → magnetic
- Compute Spearman correlation across the full sample

---

## File Structure
```
Two_Breaks/
├── PLAN.md
├── scripts/
│   ├── 01_build_sample.py        # Phase 1: catalog query + sample selection
│   ├── 02_download_data.py       # Phase 1: TTE data download
│   ├── 03_build_lightcurves.py   # Phase 2: light curve generation
│   ├── 04_horizontal_line.py     # Phase 2: Busby-Lazzati algorithm
│   ├── 05_classify_grbs.py       # Phase 2: single vs multi classification
│   ├── 06_bayesian_blocks.py     # Phase 3: Bayesian blocks binning
│   ├── 07_spectral_fitting.py    # Phase 4: BB+Band fitting
│   └── 08_correlation.py         # Phase 4: Ep-kT correlation analysis
├── data/                         # Downloaded TTE/RSP files
├── results/                      # Fitted parameters, tables, plots
└── plots/                        # Light curves, correlation plots
```

## Environment
- Python env: `threeML` conda environment (`/Users/salim/anaconda3/envs/threeML/bin/python`)
- 3ML 2.4.2 with `TimeSeriesBuilder`, `download_GBM_trigger_data`, `astromodels`
- `astropy` 6.0.1 (has `bayesian_blocks`)
- `astroquery` for HEASARC catalog access
- `scipy`, `numpy`, `matplotlib` for analysis and plotting

## Decisions Made
- **Fluence cut**: > 1e-5 erg/cm²
- **T90 restriction**: None (include short + long)
- **Single-pulse threshold**: Busby & Lazzati's 0.9983 (≤3 unnormalized failures)

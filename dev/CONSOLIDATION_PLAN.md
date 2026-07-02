# Cross-project consolidation plan — one shared package for the agentic pipeline

Goal (Vikas, 2026-07-01): the analysis elements are forked across **SinglePulses /
Two_Breaks / PulsewiseAmatiYonetoku / LATBright** and have diverged — fixes made in
one fork never reach the others, and platform assumptions (hardcoded paths, backends)
break agents on other machines/sandboxes. Consolidate the shared components into ONE
package that every project imports, per the long-standing GRB_Handbook plan.
Grounded in the 4-reader divergence-map workflow (2026-07-01).

## What the map found (the duplication matrix)

| Component | Canonical / best copy | Forks + what diverged |
|---|---|---|
| POSHIST quaternion angle math | Two_Breaks `00_prototype` (verbatim-copied everywhere) | Pulsewise `detector_picker_gui.py`, LATBright `Two_Breaks_pipeline/00_prototype` — identical ⇒ pure library material |
| Detector picker GUI | **Two_Breaks (now)** — hemisphere split ported back 2026-07-01 + keep-alive fix | Pulsewise had the split but not keep-alive; LATBright has neither |
| BackgroundSelector (residuals + keyboard adjust) | Two_Breaks `00_prototype` | Inlined copies in Pulsewise + LATBright; LATBright fork **removed the approval stamp** |
| Approval gate / stamp / decision.json | Two_Breaks `30`/`39` ONLY | No fork has it — gate must ship in the package |
| Multi-location TTE/RSP resolver | **Pulsewise `10_fit_pulses_3ml.py`** (Two_Breaks/data → HDD → spectral_data chain) | Two_Breaks/LATBright search one dir only — adopt Pulsewise's |
| AI-vision bkg proposal renderer | **Pulsewise `bkg_select.py`** (χ²ᵣ polyfit overlay, dropout detection) | Two_Breaks `39 render` is simpler — merge the dropout check + χ²ᵣ overlay |
| BB binning | **Two_Breaks `27b`** (trim+merge+emission_window+SRC_*) | LATBright `04` = older, noisier (~70 vs ~20 blocks); Pulsewise `single_pulse/02` = no merge |
| Fast BB for >10⁶ events | **LATBright `s02p_bb_threeml_hybrid.py`** (astropy BB on 1-ms 3ML residuals) | Nowhere else — adopt as the big-burst option in the package |
| 6-model spectral engine | Two_Breaks `10` (rsp2-collapse, validity gate, MINOS+Hessian) | Pulsewise 4-model per-pulse variant; LATBright 17-model + LLE/LAT joint + MINOS-profile — keep as extensions |
| gtburst-faithful Cash polyfit / MAD imodpoly | **LATBright `gtburst_bkg.py` / `robust_polyfit.py`** (standalone, no hardcodes) | Package as utilities |

## Platform sins to fix once, centrally (the Codex-trial lessons)
- Hardcoded `/Users/salim/...` everywhere: CALDB paths (10, 08, 09, Pulsewise, LATBright),
  Pulsewise `DATA_DIR` → Two_Breaks/data, Two_Breaks `08` → a path inside LATBright(!).
- Hardcoded `matplotlib.use('macosx'/'TkAgg'/'Agg')` in forks vs the portable
  fallback chain + `MPLBACKEND` respect (best copy: Two_Breaks `30` / Pulsewise `bkg_picker_gui`).
- Unwritable `HOME`/caches in agent sandboxes (Codex hit `~/.matplotlib`,
  `~/.astromodels`) → one `env.py` shim: detect CALDB from `$FERMI_DIR`/conda env,
  fall back MPLCONFIGDIR/astromodels-log to a temp dir, honor `THREEML_PY`.

## Package design (working name `grbhandbook`)
```
grbhandbook/
  env.py        # CALDB/fermitools discovery, writable-cache shims, backend chain
  geometry.py   # POSHIST download + quaternion angle math (single copy)
  data.py       # multi-location TTE/RSP resolver (Pulsewise) + GBM download
  gui.py        # detector picker (hemisphere), BackgroundSelector, source marker
  approve.py    # the gate: pending/decision.json, stamp, validate, ingest
  binning.py    # 27b hybrid + LATBright residual-BB fast path
  fitting.py    # engine-10 core (models, validity gate, rsp2 collapse, MINOS)
  qc.py         # progress/QC checks (36) + flags
```
Projects `pip install -e` it; project scripts become thin wrappers (paths + sample
catalogs stay per-project). AI guides (`dev/ai_guides/`) move with it so every
project's agents read the same criteria.

## Migration order (fix-forward, no big-bang)
1. `env.py` + `geometry.py` + `data.py` (pure code, no GUI risk) — projects adopt immediately.
2. `gui.py` + `approve.py` (Two_Breaks canonical + Pulsewise best-features merged).
3. `binning.py` + `fitting.py` last (they gate the science numbers — adopt for the
   authoritative Part-2 run, not mid-provisional).

## Timing constraint (IMPORTANT)
The **benchmark is mid-flight** (Expert runs + Codex trial on the current Two_Breaks
scripts). Do NOT change Stage-1 semantics mid-benchmark — raters must see the same
tool. The package is built and validated in parallel; projects switch AFTER the
benchmark data collection (or the benchmark is explicitly re-based).

## Where it lives — RESOLVED 2026-07-02
The handbook repo already exists: **`~/Desktop/Projects/GRB_Handbook_Project`**
(github.com/vikas-chand/GRB-Handbook), with an installable `grb_pipeline` package —
6-stage orchestrator + CLI (`python -m grb_pipeline run <GRB>`), data fetchers
(Fermi/Swift/GCN), analysis (gbm_analysis/temporal/spectral/classification), an `ai`
module, tests, and LATBright's `gtburst_bkg.py` already migrated in. **That is the
consolidation home** — port the map's best-of-breed components INTO `grb_pipeline`
rather than seeding a new package.

### What `grb_pipeline` is missing (from the divergence map)
- POSHIST detector-angle selection + the hemisphere picker GUI
- the **approval gate** (stamp / decision.json / APPROVAL_MODE) — no approval logic exists in it
- multi-location TTE/RSP resolver (Pulsewise)
- the 27b BB + significance-merge hybrid (its temporal BB is plain)
- engine-10's validity-gated 6-model fitting + rsp2-collapse
- agent legibility (AGENTS.md + dev/ai_guides/) and the env/writable-cache shims

### ⚠ Conventions must be RECONCILED, not just moved
`grb_pipeline.analysis.gbm_analysis` selects background polynomial order by **BIC over
0–4**; the Two_Breaks papers use **LRT with order ≤3**. Similar checks needed for BB
priors/floors and model sets. If these aren't unified (one documented choice each),
the "uniform" pipeline silently diverges from the published methods.

## Remaining decision (Vikas)
**When**: build/port now in parallel (benchmark stays frozen on the current Two_Breaks
scripts; adopt the package for the authoritative Part-2 run) — or after the benchmark
data collection completes.

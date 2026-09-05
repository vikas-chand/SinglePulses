# bn090530760 — reproduction record

The exact code state that produced this burst's paper products. Verify
any script by comparing its SHA-256 on disk with the value recorded
here (which came from the product sidecar written at render time).

## Repository state

- commit: `996dba253020f42c6075ec0ca290cd86740fd46e`
- uncommitted changes under `scripts/`+`dev/` at record time: YES — see list below

```
M scripts/41e_sed_montage.py
?? dev/ai_guides/CODEX_QUOTA_DISCIPLINE.md
?? dev/ai_guides/PI_REVIEW_PROTOCOL.md
?? dev/campaign20_refits.sh
?? dev/campaign_products_driver.sh
?? dev/gen_param_tables.py
?? dev/logfilter.py
?? dev/make_repro_record.py
?? dev/merge_campaign_families.py
?? dev/rebuild_step9_canonical.py
```

## Producing scripts (SHA-256 as recorded when each product was made)

| script | sha256 recorded | sha256 on disk now | match |
|---|---|---|---|
| `/Users/salim/Desktop/Projects/SingleRest/Two_Breaks/scripts/44_step_figures.py` | `64d4961cc89ff3aa…` | `64d4961cc89ff3aa…` | YES |
| `/Users/salim/Desktop/Projects/SingleRest/Two_Breaks/scripts/46_temporal_all106.py` | `2690f293b626af80…` | `2690f293b626af80…` | YES |
| `41c_paper_sed.py` | `19cce0784fa403dd…` | `19cce0784fa403dd…` | YES |
| `41d_param_evolution.py` | `2bb02e84473cbb0e…` | `2bb02e84473cbb0e…` | YES |
| `47b_temporal_figs.py` | `e01907d225fa7a91…` | `e01907d225fa7a91…` | YES |
| `47c_lag_latbright.py` | `275d82c78088d9cc…` | `275d82c78088d9cc…` | YES |

## Exact commands (argv recorded per product)

```
python scripts/41c_paper_sed.py --trig bn090530760 --bin 0 --model BAND --out results/convention_check/sed_grid_bn090530760 --fit-root results/convention_check
python scripts/41c_paper_sed.py --trig bn090530760 --bin 0 --model BANDBB --out results/convention_check/sed_grid_bn090530760 --fit-root results/convention_check
python scripts/41c_paper_sed.py --trig bn090530760 --bin 0 --model BANDBBCPL --out results/convention_check/sed_grid_bn090530760 --fit-root results/convention_check
python scripts/41c_paper_sed.py --trig bn090530760 --bin 0 --model BANDBBPL --out results/convention_check/sed_grid_bn090530760 --fit-root results/convention_check
python scripts/41c_paper_sed.py --trig bn090530760 --bin 0 --model BANDCPL --out results/convention_check/sed_grid_bn090530760 --fit-root results/convention_check
python scripts/41c_paper_sed.py --trig bn090530760 --bin 0 --model BANDCUT --out results/convention_check/sed_grid_bn090530760 --fit-root results/convention_check
# … 162 more (one per model/bin panel; same form)
python3 scripts/41e_sed_montage.py --trig bn090530760
python dev/rebuild_step9_canonical.py --trig bn090530760
python3 dev/gen_param_tables.py --trig bn090530760
python scripts/10_spectral_fit_burst.py --trigger bn090530760 --include-bgo --no-log --models highe \
    --blocks-file results/sweep106/bn090530760/blocks/bb_blocks_spectral_bn090530760.ecsv \
    --bkg-file results/background_intervals.ecsv --out-dir results/campaign20_fam/bn090530760_highe
```

## Model menu and parameter bounds (from the engine, final state)

| model | prefix | n_params | bounds / notes |
|---|---|---|---|
| Band | `BAND` | 4 | set in the model builder (see `build` in the spec) |
| CPL | `CPL` | 3 | set in the model builder (see `build` in the spec) |
| SBPL | `SBPL` | 4 | set in the model builder (see `build` in the spec) |
| DSBPL | `DSBPL` | 6 | set in the model builder (see `build` in the spec) |
| Band+BB | `BANDBB` | 6 | set in the model builder (see `build` in the spec) |
| CPL+BB | `CPLBB` | 5 | set in the model builder (see `build` in the spec) |
| SBPLfree | `SBPLF` | 5 | set in the model builder (see `build` in the spec) |
| DSBPLfree | `DSBPLF` | 8 | set in the model builder (see `build` in the spec) |
| Band+PL | `BANDPL` | 6 | set in the model builder (see `build` in the spec) |
| Band+CPL | `BANDCPL` | 7 | set in the model builder (see `build` in the spec) |
| CPL+PL | `CPLPL` | 5 | set in the model builder (see `build` in the spec) |
| CPL+CPL | `CPLCPL` | 6 | set in the model builder (see `build` in the spec) |
| BandR+CPL | `BANDRCPL` | 7 | set in the model builder (see `build` in the spec) |
| BandxCut | `BANDCUT` | 5 | set in the model builder (see `build` in the spec) |
| SBPLxCut | `SBPLCUT` | 5 | set in the model builder (see `build` in the spec) |
| SBPL+PL | `SBPLPL` | 6 | set in the model builder (see `build` in the spec) |
| SBPL+CPL | `SBPLCPL` | 7 | set in the model builder (see `build` in the spec) |
| Band+BB+PL | `BANDBBPL` | 8 | set in the model builder (see `build` in the spec) |
| Band+BB+CPL | `BANDBBCPL` | 9 | set in the model builder (see `build` in the spec) |
| CPL+BB+PL | `CPLBBPL` | 7 | set in the model builder (see `build` in the spec) |
| CPL+BB+CPL | `CPLBBCPL` | 8 | set in the model builder (see `build` in the spec) |
| SBPL+BB | `SBPLBB` | 6 | set in the model builder (see `build` in the spec) |
| SBPL+BB+PL | `SBPLBBPL` | 8 | set in the model builder (see `build` in the spec) |
| SBPL+BB+CPL | `SBPLBBCPL` | 9 | set in the model builder (see `build` in the spec) |

Bounds enforced at fit time (engine source, authoritative):
```
321: b.alpha.bounds = (-1.9, 1.9)
333: c.K.bounds = (1e-10, 1e4)
334: c.index.bounds = (-2.0, 1.0)
335: c.xc.bounds = (10.0, 5e4)
344: bb.K.bounds = (1e-15, 1e4)
345: bb.kT.bounds = (1.0, 200.0)
353: s.K.bounds = (1e-10, 1e4)
354: s.alpha.bounds = (-2.5, 1.5)
355: s.break_energy.bounds = (10.0, 5.0e4)
356: s.beta.bounds = (-5.0, -1.5)
367: d.K.bounds = (1e-10, 1e4)
368: d.alpha1.bounds = (-2.5, 2.5)
369: d.xb.bounds = (10.0, 5000.0)
370: d.alpha2.bounds = (-3.0, 0.5)
371: d.xp.bounds = (30.0, 5.0e4)
372: d.beta.bounds = (-5.0, -1.5)
391: s.break_scale.bounds = (0.01, 2.0)
398: d.n1.bounds = (0.5, 10.0)
401: d.n2.bounds = (0.5, 10.0)
414: pl.K.bounds = (1e-15, 1e2)
415: pl.index.bounds = (-4.0, -1.0)
424: c.K.bounds = (1e-15, 1e2)
425: c.index.bounds = (-4.0, -1.0)
426: c.xc.bounds = (5e4, 1e8)                   # 50 MeV - 100 GeV
436: b.xp.bounds = (10.0, 2000.0)
457: c.xc.bounds = (1e4, 1e8)
```

## Inputs (never re-derived)

Approved Stage-1 selections (`results/background_intervals.ecsv`):

| det | bkg pre | bkg post | source | approved by |
|---|---|---|---|---|
| n1 | (-26.76, -9.76) | (157.24, 273.24) | (-2.43, 169.24) | Vikas Chand |
| n2 | (-26.76, -6.76) | (203.24, 284.24) | (-2.43, 169.24) | Vikas Chand |
| n5 | (-24.76, -9.76) | (225.24, 288.24) | (-2.43, 169.24) | Vikas Chand |
| b0 | (-26.76, -7.76) | (33.24, 130.24) | (-2.43, 169.24) | Vikas Chand |

Block table: `results/sweep106/bn090530760/blocks/bb_blocks_spectral_bn090530760.ecsv`
- sha256 `7da29cd3e8f6f87d…`
- reused unchanged from the 2026-08-12 binning run; re-deriving blocks
  per convention would break cross-burst comparability.

Canonical fit table: `results/convention_check/bn090530760/spectral_fits.ecsv`
- sha256 `9328644c9cc7080d…`; 24 models × 7 spectra
- canonicalization: best optimizer minimum per (bin, model) across
  all invocations we possess (multistart luck reaches ΔAIC ≈ 9).

## Notebook

`notebooks/Two_Breaks_single_GRB_pipeline.ipynb` (config `notebooks/configs/bn090530760.yaml`) runs the same chain interactively and
contains no LLM calls. It imports the engine above, so the model menu
and bounds it uses are the same objects listed here. It fits one
representative block (the full source window) rather than the whole
per-bin grid — to regenerate the paper's per-bin panels use the
commands in the section above.


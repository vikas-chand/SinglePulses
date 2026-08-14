# CODEX BRIEF — rescue the νFν display layer (2026-08-13)

**Run mode:** GPT-5.6, Sol, Ultra.
**Working directory:** `/Users/salim/Desktop/Projects/SingleRest/Two_Breaks`
**You MAY WRITE, but only these two paths:**
- `scripts/41b_nufnu_display.py` — your corrected implementation (NEW file; do not edit
  `scripts/41_nuFnu_panels.py` in place, it is live)
- `notes/CODEX_DISPLAY_20260813.md` — your report

Everything else is READ-ONLY. Do not touch `results/`, do not run the fit engine.

The PI's words: *"rescue us from the mess that is happening here."* This is a build
task, not only an audit. The science engine is sound; the layer that DRAWS it is not,
and it has failed the same way four times in two days.

## Environment
`/Users/salim/anaconda3/bin/python3` has numpy/astropy/matplotlib/scipy (enough to
build and test the display path against stored numbers — you do NOT need threeML for
the core fix). Heavy tier if you want to render a real panel:
`conda activate threeML` plus
`export FERMI_DIR=$CONDA_PREFIX/share/fermitools; export CALDB=$FERMI_DIR/data/caldb;
export CALDBCONFIG=$CALDB/software/tools/caldb.config;
export CALDBALIAS=$CALDB/software/tools/alias_config.fits; export CALDBROOT=$CALDB;
export EXTFILESSYS=$FERMI_DIR/refdata/fermi`.

## Artefacts of record (sha256[:16], now)
| file | hash |
|---|---|
| `scripts/41_nuFnu_panels.py` (the thing to replace) | `fe6566e7e0787d23` |
| `scripts/10_spectral_fit_burst.py` (the ENGINE — authority) | `af053a99a6ce1a3c` |
| `scripts/plot_style.py` (style; delegates to LATBright) | `8aca91019bca137c` |

Test burst: `bn081125496`, products in `results/sweep106/bn081125496/`, fit table
`results/sweep106/bn081125496/bn081125496/spectral_fits.ecsv` (832 columns).

## Rules you are enforcing
`dev/ai_guides/Figures.md` (F1–F13), `dev/ai_guides/ShippingGate.md`,
`~/Desktop/Projects/reference_general_figure_style.md` (the cross-project authority),
and `~/Desktop/LATBright/GRB260226A/s01a_gbm_lightcurves.py` +
`plot_config.py` as the PROVEN reference implementations — reuse them, do not restate
them (AGENTS.md now forbids reimplementation; see its first section).

---

# THE DIAGNOSIS (established, do not re-derive)

**One bug, four instances: the figure RECOMPUTES what the engine already decided.**
`scripts/41` has four modes. `best` and `binall` were patched to read the engine row;
`bin` and `model` were not, and printed cold-refit AICs — five panels 137–172 AIC
units from the stored values (the L8 default-seed artifact). Those labels are now
fixed and verified 24/24 against the table.

**But the deeper half is NOT fixed, and it is the thing to solve.** Even the "fixed"
modes still call `fit_spec()`, which warm-starts from the stored row and then **re-runs
minuit with normalisations free**. So the CURVE is a refit, not the engine's fit.
Three panels admit it (`[! PANEL!=ENGINE dAIC=+17]` on Band+BB); the other 21 are
unstamped but unverified, because equal AIC does not imply equal parameters.

**KEY FACT I ESTABLISHED FOR YOU — the engine stores everything needed for a faithful
redraw, including normalisations.** For example `BANDBB_*` carries `ALPHA, EP, BETA,
K_BAND, KT, K_BB` (+ errors); the simple models carry `BAND_K, CPL_K, SBPL_K, …`; the
composites carry their second-component norms (`BANDPL_PL_K`, `BANDCPL_HE_K`, …).
**So the correct design is: build the astromodels component, set every parameter from
the stored row, and EVALUATE it. No `jl.fit()` anywhere in the display path.**

---

# WHAT TO BUILD — `scripts/41b_nufnu_display.py`

A display module whose contract is: **it cannot draw a number or a curve it did not
read from the engine table.** Requirements, in priority order:

1. **`model_from_row(spec, row)`** — construct the spec's component and set EVERY
   parameter (shape + normalisations) from the stored columns. Return `None` (and the
   caller must say so on the panel) if any required column is missing or non-finite.
   The engine's builders and the column naming are in `scripts/10` (`MODEL_SPECS`,
   `SHAPE_MODEL_SPECS`, `HIGHE_MODEL_SPECS`, `_setup_*`, and the row-writing code) —
   derive the mapping from the source, do not guess it.
   **Verification (do this and report it): for ≥3 models on ≥2 blocks, recompute the
   AIC implied by the stored parameters against the plugins and show it reproduces
   `<PREFIX>_AIC` to within the tolerance you justify.** If it cannot, that is a real
   engine finding — report it, do not hide it behind a refit.
2. **Energy range (rejected by the PI three times).** The axis must not run decades
   past the data. Define the DETECTED span (channels that are not upper limits, across
   the plotted detectors), clip the axis to it with a stated pad, and draw every model
   **solid only over the detected span, dotted outside** (F5). On this burst the axis
   ran 6.5 keV–43 MeV while the last detection is ≈330 keV: 47% of the range carried
   no data, with models drawn boldly through it.
3. **Labels and keys (F13, the project checklist).** Every panel/grid gets
   `Energy (keV)`, `$\nu F_\nu$ (keV$^2$ s$^{-1}$ cm$^{-2}$ keV$^{-1}$)`,
   `resid ($\sigma$)`; ONE shared figure-level legend naming the detectors and
   explaining the upper-limit marker (its tail is currently `0.35×value`, decorative —
   say so or draw a bare arrow). Significance in σ.
4. **Winner marking** without violating F2: `[BEST]` plus a highlight that is NOT a
   detector identity colour (`PUB["c_bgo"]` is BGO — the current frame uses it, and it
   renders as an L because these axes have no top/right spines).
5. **ΔAIC zero-point bug.** The reference must be the minimum over **VALID** models
   (what `scripts/10` uses for `BEST_AIC_MODEL`), not over all models. They coincide on
   this block; on some block in the 106 they will not, and `[BEST]` will print a
   positive ΔAIC while an `[INVALID]` panel prints +0.0.
6. **Layout that is readable at print size.** The current grid is 16.8×21.6 in with
   9 pt titles → ~3.5 pt on a 6.5-in page. Sizes from `PUB` only (there is a failing
   test, `tests/test_figure_style.py::test_no_hardcoded_style_numbers`, on both figure
   scripts — make your file pass it).
7. **Unfolding honesty.** Points are ratio-unfolded under the panel's own model, so
   they MOVE between panels — which defeats cross-panel comparison, the whole point of
   a grid. Either unfold everything under the engine's winner (as `binall` does) and
   say so in the suptitle, or make the caveat prominent. Your call; justify it.

Keep the existing modes' semantics (`bin`, `model`, `best`, `binall`) and the same CLI
so it is a drop-in. Reuse `unfold_detector`, `_rebin_for_plot`, `data_range` etc. from
`scripts/41` by import if that is cleanest — but the DRAWING path must not refit.

---

# VERIFICATION RULES (these are why past reviews found real bugs)
- Check against **external** authority — the engine source and the stored table — never
  against another derived figure. A self-consistency check passes while wrong.
- An invariant that cannot find its reference must **FAIL LOUDLY**, not skip or refit.
- Prefer a demonstration (recompute, re-render, diff) over an argument.
- If a fix is impossible without an engine change, say so plainly and name the change.

# Output contract (`notes/CODEX_DISPLAY_20260813.md`)
```
VERDICT — is the display layer now trustworthy? SIGN OFF / DO NOT SIGN OFF
DESIGN — what you built and why, in ~10 lines
VERIFIED — the parameter-fidelity demonstration, with numbers
FIXED — each of the 7 requirements: DONE / PARTIAL / NOT DONE, with evidence
FOUND — anything wrong in the ENGINE that the display work exposed
COULD NOT — what you could not do and why
```

Finally, your own independent judgement: **is a per-model 24-panel grid even the right
figure**, or is the project asking the display layer to do something the data cannot
support? The PI's underlying question is "which model does this bin prefer, and is that
preference real" — say plainly whether this figure answers it, and if not, what would.

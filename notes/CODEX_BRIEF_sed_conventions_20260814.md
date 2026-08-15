# CODEX BRIEF — νFν/SED plotting conventions vs XSPEC + threeML source (2026-08-14)

Run mode: GPT-5.6, Sol, **Ultra**. Working directory:
`/Users/salim/Desktop/Projects/SingleRest/Two_Breaks` (repo root; run everything from here).

**READ-ONLY except your report. Write only `notes/CODEX_SED_CONVENTIONS_20260814.md`.**
Do NOT modify any script, figure, table, or note. You are ADVISORY: confirm/refute and
SUGGEST exact fixes; we implement.

Environment: `/Users/salim/anaconda3/bin/python3` has numpy/pandas/astropy/scipy/pymupdf.
The threeML env python is `/Users/salim/anaconda3/envs/threeML/bin/python` (threeML 2.5.0
installed at `/Users/salim/anaconda3/envs/threeML/lib/python3.9/site-packages/threeML`).
XSPEC runtime exists but you should not need it; the **XSPEC SOURCE TREE** is the ground
truth: `/Users/salim/Downloads/heasoft-6.30.1/Xspec/src/`. If you run any heavy-tier
threeML code, first: `conda activate threeML` + the CALDB exports in AGENTS.md §2.

## Context (deliberate conventions — do not relitigate)

- Energy ranges were CHANGED TODAY to the PI's published convention (Chand et al. 2020,
  ApJ 903, 9, p.3): NaI `8.1-900` keV, K-edge exclude `30-40`, BGO `200-38000` keV, LLE
  `20000-100000`. This is a PI decision, documented in `scripts/10` constants (lines
  ~67-92). All pre-change fits carry old ranges; `scripts/41b::_assert_range_convention`
  refuses cross-convention replay. Do not question the choice of ranges; verify only that
  code implements what it claims.
- Winner selection doctrine (valid-only AIC, ΔAIC≥10 DECISIVE) is frozen — out of scope.
- `results/convention_check/` is a DEMO root (new-convention re-fit of bn081125496);
  the authoritative sweep lives elsewhere and is out of scope tonight.

## The artefact of record

`scripts/41c_paper_sed.py` (sha256 prefix `6e4391b48151024f`) — a NEW single-bin,
single-model "paper SED" generator written tonight: live JointLikelihood fit using the
ENGINE's own builders (`scripts/10` `MODEL_SPECS` etc.), then a νFν figure: ratio-unfolded
data points per detector, 68% band, σ-residual panel, per-detector-class shading.
Supporting primitives it imports: `scripts/41_nuFnu_panels.py` (`21d36b2449148e93`) —
`_plugin_counts`, `_rebin_for_plot`, `build_plugins`. Engine: `scripts/10_spectral_fit_burst.py`
(`f501b11a8519c96b`). Products to inspect: `results/convention_check/bn081125496_SED_TINT_Band.png` and
`results/convention_check/bn081125496_SED_bin4_CPL.png` — REGENERATED just before your
launch under the corrected item-5 rule (do not trust any hash written here; the fit table
`results/convention_check/bn081125496/spectral_fits.ecsv` is stable at `ef96e8eaaba03def`).
Ignore any other SED/overlay copies on disk (results/sweep106 figures are the OLD
conventions era).

## What we claim, and what to verify (recompute from sources/products; trust no prose)

Ground truth for XSPEC semantics =
`/Users/salim/Downloads/heasoft-6.30.1/Xspec/src/XSPlot/Commands/PlotUnfolded.cxx` and
`/Users/salim/Downloads/heasoft-6.30.1/Xspec/src/XSPlot/Plot/CreateBinnedPlotGroups.cxx`
(+ PlotSettings.*). Ground truth for threeML = the INSTALLED package above.

1. **eeufspec algorithm.** We claim XSPEC's unfolded point = `yData × unfoldedModel/foldedModel`
   per plot group (PlotUnfolded.cxx ~lines 67-81) with eeufspec weight `(X-dX)(X+dX) = E_lo·E_hi`
   (~lines 114-129). CONFIRM from source, and additionally PIN DOWN what `unfoldedModel[j]`
   actually contains for a binned plot group (CreateBinnedPlotGroups constructed with
   `unfolded=true`): is it Σ_channels ∫F dE over the group divided by the group width (per
   keV), per cm²? Does `isDivisibleByArea(false)` (PlotUnfolded ctor) change the units story?
   Our implementation approximates it as `E_lo·E_hi × (∫_group F(E) dE)/(E_hi−E_lo)` via
   16-point log-trapz (`41c_paper_sed.py::unfold_all_points`). State whether that is
   EQUIVALENT to XSPEC's per-channel construction or introduces a bias for wide groups
   (channel-weighted vs continuous integral), and if so the exact correction.

2. **Model-invariance claim.** We claim: with the group-integrated numerator, the diagonal
   (effective-area) part of the fold cancels exactly in the ratio, so data points are
   model-invariant up to detector dispersion; point-evaluation `Ē²F(Ē)` (the OLD behaviour,
   still live in `scripts/41::unfold_detector` and `scripts/41b::unfold_detector`) breaks
   this. Verify by DEMONSTRATION: in the threeML env, rebuild bin-4 plugins (the demo root's
   fit table has the parameters; `41c` shows the build path), unfold the same data under CPL
   and under Band with BOTH constructions, and report the max |Δpoint|/point for each. Our
   prediction: group-integrated ≲ dispersion-level; point-evaluated visibly larger.

3. **setplot rebin semantics.** We claim: `CreateBinnedPlotGroups.cxx` accumulates until
   `S ≥ minSig` (line ~675 `doneBin = (latestChannel >= chanEnd) || (datapt > 0 && datapt² >=
   errorpt*critVar)`) or the maxBins cap (line ~558 via `m_critNumChans`), then EMITS the
   group regardless; `datapt > 0` is required for the significance exit; there is NO
   upper-limit machinery anywhere in XSPlot. CONFIRM each clause from source. Our rendering
   rule (all groups = points; bare 2σ arrow ONLY when net < 2σ) is a DECLARED deviation —
   assess whether it misrepresents anything XSPEC would show.

4. **Group/mask interaction.** We claim the legacy `scripts/41::_rebin_for_plot` can merge
   channels ACROSS a mask discontinuity (it iterates the compressed masked arrays), placing
   a merged point visually inside an excluded range (the 30-40 keV K-edge); `41c` breaks
   groups at discontinuities (`breaks = flatnonzero(ene_lo[1:] > ene_hi[:-1]*(1+1e-9))+1`).
   CONFIRM the legacy flaw by reading `_rebin_for_plot` + `_plugin_counts`, confirm 41c's
   fix is airtight (edge cases: single-channel runs, float-equal edges, detectors whose
   ebounds are descending?), and confirm from the current PNGs that no point/errorbar sits
   inside 30-40 keV.

5. **Full-fitted-range axis rule (corrected by the PI mid-review, 2026-08-14).** The rule
   is now: curve/band/axis span the FULL FITTED range [first fitted channel edge, last
   fitted channel edge] — nothing beyond either edge, and NOTHING WITHIN it dropped: every
   rebin group is shown, sparse high-BGO groups as 2σ arrows, a group dropped only when its
   folded model is exactly zero (the XSPEC NO_VAL rule). An earlier `pred > 0.5` counts
   filter silently erased the sparse upper-BGO groups (channels that ARE in the likelihood)
   — the PI caught it on the bin-4 figure; it is now `pred > 0`. Confirm in code
   (`41c::unfold_all_points`, the E-grid and xlim lines) and in both regenerated PNGs
   (measure axis edges: NaI channel-true low edge ~7.31 keV; BGO fitted top 38 MeV region).
   Also assess: with pred→tiny (0.76-s bin, tens-of-MeV channels), the unfolded 2σ arrow
   value (net+2σ)/pred can sit far above the curve — XSPEC shows the same forest — is our
   arrow placement numerically sane there, or does it need a cap/legend note?

6. **The 68% band.** `41c::live_band` draws MVN samples from `jl.covariance_matrix`,
   rejection-resamples to 400 in-bounds draws, DISCLOSES the spill fraction on the figure
   (currently 2.7% for T_INT Band), suppresses above 10% spill; the archival rule
   (`41::model_error_band`, >1% → suppress, from the bn200524211 incident) stays for the
   archival path. Questions: (a) is bounded rejection sampling statistically defensible for
   a display band at these spill levels, or does it bias the band inward enough to matter?
   (b) does threeML 2.5.0 ship a NATIVE better path from a JointLikelihood result —
   e.g. `AnalysisResults.propagate` / the `plot_spectra` contour machinery — that we should
   use instead for the live-fit band (cite file:line in the installed package)? We WANT the
   native path if it exists and is correct — that is this project's standing rule.
7. **EAC/constant conventions.** Reference NaI frozen at k≡1; non-reference free in
   (0.8,1.2) (`scripts/10` ~line 1171; `41::build_plugins` re-activates for non-ref).
   In our figure the single curve is the k=1 source model and each detector's points are
   unfolded against ITS OWN prediction (which contains its k) — i.e. cross-normalized onto
   the reference curve; XSPEC instead cancels k in the ratio and draws per-dataset curves.
   Confirm our arithmetic actually does what this paragraph says (read `_plugin_counts`:
   `predicted = pl.get_model()` — does threeML's `get_model()` include the EAC nuisance for
   that plugin? cite SpectrumLike source line), and state whether the figure's caption/legend
   needs anything to make the convention unambiguous.

8. **Residuals.** Ours: `(net − pred)/sqrt(var)` per group with `var = max(obs,1) + bkg_var`
   (see `_rebin_for_plot`). XSPEC `plot delchi` uses (data−model)/error with the same error
   as the data plot. Is our σ definition consistent with a pgstat-fitted Poisson+Gaussian
   setting, and consistent with what the paired data panel shows? If a different residual
   definition would be more standard for publication (e.g. sign(d−m)·sqrt(Δstat)), say so.

9. **Live-fit-at-figure-time design.** `41c` fits the named model fresh (engine builders,
   default seeds, MINUIT) and stamps `live fit: AIC=... (k=...)`. The engine's stored
   winner for the same bin came from multistart + gates. Assess the failure modes of the
   single-start live fit for FIGURE purposes (local minima → curve that isn't the engine's
   solution) and suggest the cheapest guard (e.g. seed from the stored table row when
   present + assert |AIC_live − AIC_stored| < tol, printing both).

10. **threeML rooting.** Our note `notes/THREEML_NATIVE_NUFNU_20260813.md` claims threeML
    ships NO unfolded-data plotting (verified against 2.5.0), display rebin thresholds on
    the EXPECTED MODEL RATE (`SpectrumLike.py` ~line 3245 `Rebinner(expected_model_rate,...)`),
    and `_construct_counts_arrays` is the sanctioned extraction point. Spot-verify these
    three claims at the installed source (cite lines). If threeML has ANY machinery that
    makes part of `41c` redundant, name it.

## Open items from previous Codex reports touching this scope

- `notes/CODEX_DISPLAY_20260813.md` (display-layer rescue): EAC serialization was the
  blocker — since fixed (engine writes `<PREFIX>_EAC_<DET>`; recovery backfilled; you may
  see the columns in the demo fit table). Its DO-NOT-PROMOTE for 41b stands; 41b is NOT
  tonight's artefact. Do not re-audit 41b beyond the two flaws we ourselves assert (items
  2 and 4: point-evaluation + gap-bridging in its `unfold_detector`).
- `notes/CODEX_WHOLE_PROJECT_20260813.md` A5 (panels not faithful displays): 41c's answer
  is live-fit-at-figure-time; assess per item 9.

## Verification rules

- Check against the XSPEC SOURCE and the INSTALLED threeML — never against our notes.
- Prefer demonstration (run the comparison in item 2; measure the PNGs) over argument.
- An invariant that cannot find its reference must fail loudly — flag any silent skip you
  see in the code paths under review.
- Recompute from products; do not trust any printed value, including hashes in this brief.

## Output contract

```
VERDICT — SIGN OFF or DO NOT SIGN OFF (on: "41c's conventions are correct and rooted
         in XSPEC/threeML, subject to the listed fixes")
Per item 1-10: CONFIRMED / NOT CONFIRMED / NEEDS-CHANGE, with the derivation shown
DISCREPANCIES: each with the exact suggested fix (advisory — code snippets welcome,
              but change no files)
COULD NOT VERIFY: what and why
```

Finally, your own independent judgement: anything wrong or fragile that this brief did
not ask about.

# CODEX display-layer rescue — 2026-08-13

## VERDICT — is the display layer now trustworthy? **DO NOT SIGN OFF**

`scripts/41b_nufnu_display.py` is trustworthy as a fail-closed, non-refitting renderer
of the engine's stored source-model parameters and table labels for engine rows that
exist in a supported product. It is **not yet an archival replay of the joint engine
likelihood**: the engine did not serialize its
fitted effective-area-correction (EAC) constants, covariance, or exact folded-input
provenance. The code therefore omits non-reference-detector folded diagnostics and
states the limitation on every page. Rebuilt plugins retain their library defaults, but
41b never uses unit-EAC folded diagnostics for the affected detectors. It never refits a
source model; for a selected existing row, an unavailable curve is stated on the panel.

Shipping-gate stamp:

- `VERIFIED_BY`: Codex primary (machine/table checks and final renders) plus an
  independent fresh-context GPT-5.6 Sol/Ultra code gate and fresh vision gate.
- `VERIFIED_UTC`: 2026-08-14T02:38:30Z.
- `CHECKLIST_VERSION`: `ShippingGate.md` born 2026-08-12; `Figures.md` F1–F13 as
  inspected 2026-08-13; cross-project figure guide as inspected 2026-08-13.
- `DEFECTS_FOUND`: missing engine EAC/covariance/input serialization; frozen artifact
  hashes for the live figure/style files changed during this task; the live authority
  still points at the refitting script.
- `DISPOSITION`: new renderer retained; no existing authority, result, fit, or test file
  changed; do not promote it to the live path until the engine serialization change and
  a fresh archival-replay gate are complete.

Frozen evidence used here:

- engine `scripts/10_spectral_fit_burst.py` SHA-256
  `af053a99a6ce1a3cb4d9c2764e6a5d177729d3e397739995d99c980e7fa323c9`;
- test table SHA-256
  `f5f0e003284e14f858b917390d49bdc3eb49ee749b11e0a77923ebbfc424800f`;
- fit sidecar SHA-256
  `47427dff0f710dc041b3a0d3fd730df050e1945620c93cdc5f46f0e65e551b00`;
- block product SHA-256
  `5c388552b46775897b7761041a8e9fe3547803f839e3258056df3bb9d27b1e60`;
- implementation SHA-256
  `9b4704738b588b31e0ebfc5d1cb836408f0cee5c690c05e852522f34b251d5b6`.
- background catalog SHA-256
  `4a2343bb921e1f1428bb3bb82f957277d71aade3cf0e0f9b3ccc52134feae938`;
- source-position catalog SHA-256
  `d7b22925edaac9a427102c65287027a98982b3f544576650a1c871692793fb25`;
- selected NA/NB/B1 TTE SHA-256 values, respectively:
  `bf3c870491a52a1b853b1f3e0dd6d7515e7e6c0fdd4e5f3a8a2029645c324aae`,
  `53b207b08347b28add203f06fe77e48316c4cfd4c5e7c2b33e9a2757edd0d2a7`,
  `ad429740bc4c15765e3199646d94f8df6089a7e8a3816bcad48c6e5b799a62f9`;
- selected NA/NB/B1 RSP2 SHA-256 values, respectively:
  `24155f860b21cda959d2b486278fa683143a31c0edcb43dc1332de2713bfd26c`,
  `dbff23c76b2d4a9eda757512879be5e434b1e36d065811ed38539e64e815bdcb`,
  `82bdf2b008fc5d241ebf8d0d7b2a63d05f16f23bcfe030052e742088080afcf2`;
- sorted `(file SHA-256, path)` manifest digest for the 84 census fit tables:
  `a6f87b28534649b71cab2c8e0658c4639e190f056feff2961e24b30335a62a47`.
- exact-final-source overlay PNG SHA-256 (temporary verification render):
  `feeaf22bfe6a9f8a5f5d69256b8dbea9d7acc1b225321e2b3fdb2c0c58b7abcc`.

The replay environment was Python 3.9.20, threeML 2.5.0, astromodels 2.4.2,
NumPy 1.26.4, SciPy 1.13.1, Astropy 6.0.1, Matplotlib 3.9.2, and iminuit 2.30.0.

## DESIGN — what was built and why

1. Inventory selected `scripts/41_nuFnu_panels.py` as the implementation to extend,
   so 41b imports its proven grouping/evaluation primitives instead of replacing them.
2. The active `default`, `shape`, `highe`, or `threecomp` suite is read from the
   sidecar/table; every mapping then comes from the frozen engine's registries, builders,
   and `pmap` fields.
3. `model_from_row` requires an exact match between the builder's free parameter leaves
   and `pmap`, then assigns every stored shape and normalization value without clamping.
4. Missing, masked, non-finite, ambiguous, or schema-drifted parameters return `None`;
   all four render modes put the reason on the panel instead of fitting or guessing.
5. Labels, winners, validity, intervals, significance, and AIC values are read from the
   fit table/block product; valid-only AIC invariants fail loudly on contradictions.
6. Detected energy support is built from non-upper-limit grouped channels while preserving
   masked channel gaps; the axis gets only a 0.08-dex outer pad.
7. Curves are solid in each detected domain and dotted in every unsupported outer or
   internal interval.
8. Grids use the engine winner for one common unfolding, with candidate-specific
   count-space residuals; this keeps the points fixed across model panels.
9. Detector identity, a bare upper-limit arrow, `[BEST]`, `[INVALID]`, and every axis/unit
   are explicit; winner emphasis is a full black frame, not a detector color.
10. The test product's 24-model diagnostic is paginated at four panels per page using
    `PUB` sizes; smaller engine suites paginate naturally while the legacy output stem and
    the `bin`, `model`, `best`, and `binall` CLI remain intact.

## VERIFIED — parameter fidelity and external checks

### Exact source-parameter restoration

Against the frozen engine and stored table, blocks 2 and 5 each restored **24/24
registered models**. For all 48 model/block constructions, the builder's free leaf set
equaled the engine `pmap` target set and every assigned float equaled its table value
exactly. This includes all source normalizations. Removing `BAND_K` in an in-memory test
returned `None` with `required engine column BAND_K is absent`. Static search found no
`JointLikelihood` and no `.fit(` call in 41b.

### Required AIC replay

The strict test exposed a real serialization omission. With every **stored source
parameter** fixed but the two absent EAC constants necessarily left at unity, the replay
gave the following offsets:

| Block | Model | AIC(unit EAC) − stored AIC |
|---:|---|---:|
| 2 | Band | +2.173 |
| 2 | CPL | +2.278 |
| 2 | Band+BB | +3.938 |
| 5 | Band | +11.602 |
| 5 | CPL | +12.020 |
| 5 | Band+BB | +12.561 |

Thus a table-only joint AIC replay does **not** pass. As a forensic localization only,
outside the display path, I kept every stored source parameter fixed and profiled only
the two unrecorded EAC constants. That recovers all six stored AIC values:

| Block | Model | Stored AIC | Forensic replay AIC | Absolute difference |
|---:|---|---:|---:|---:|
| 2 | Band | 1877.687570 | 1877.687543 | 0.0000275 |
| 2 | CPL | 1879.961464 | 1879.961377 | 0.0000864 |
| 2 | Band+BB | 1877.988500 | 1877.988499 | 0.0000006 |
| 5 | Band | 1483.020946 | 1483.020941 | 0.0000043 |
| 5 | CPL | 1483.398228 | 1483.398182 | 0.0000459 |
| 5 | Band+BB | 1483.961488 | 1483.961461 | 0.0000270 |

The acceptance tolerance was `1e-3` AIC: it is over ten times the largest observed
`8.64e-5` floating/profile-termination difference while still negligible relative to
the 2–13 AIC failure produced by unit EAC. The result localizes the mismatch to the
unserialized nuisance constants; it does not reveal a numerical error in the engine's
stored AIC.

### AIC zero point and label checks

Across the 84 available `results/sweep106` fit tables, 848 of 849 rows had at least one
finite `STATUS=OK, VALID` model. The minimum over all finite models differed from the
valid-only minimum in **127/848 rows (15.0%)**. One direct regression case is
`bn081224887`, block 3: invalid `SBPLBB` has AIC `3333.178813`, while valid winner
`DSBPL` has AIC `3335.219230`. 41b reports DSBPL at valid-only ΔAIC = 0. An in-memory
invalid tied-winner test also failed closed with `stored winner 'CPL+CPL' is not
STATUS=OK and VALID`.

For the real block-2 grid, all 24 displayed AIC/validity labels matched the frozen table;
the interval was `[0.42, 1.66] s`, the independently read significance was
`26.381203... sigma` (displayed `26.4 sigma`), and the engine winner was `Band+PL`.

### Render and mechanical gates

- Real `binall` render: 3243×3330 px; one-page PDF 779.754×799.2 pt.
- Real 24-model grid: six PDF pages, each four panels; page PNGs 3269×3474 px;
  PDF page size 786.129×833.76 pt.
- Detected hull: 17.315–347.452 keV; axis: 14.402–417.729 keV; three separate
  detected domains. Visual inspection confirmed solid/dotted transitions, unclipped
  labels, complete spines, one shared legend, and readable print scaling.
- A synthetic no-valid-model/no-domain case saved both PNG and PDF with the failure on
  the plot face and in the footer; it did not abort or invent ticks/curves.
- Source compilation, `git diff --check`, and the three applicable functions from
  `tests/test_figure_style.py` passed when applied directly to 41b. The governed script
  list itself was not edited because the brief permitted only two output paths.
- An independent fresh-context final code gate passed both adversarial fixes: an invalid
  tied stored winner is rejected, and `binall` renders reconstruction/domain failures
  visibly instead of raising before artifact creation.
- Synthetic registry checks passed for all engine suites: default 6/6, shape 8/8,
  highe 24/24, and threecomp 18/18; the real product resolved to highe 24/24.

## FIXED — status of the seven requirements

1. **PARTIAL.** `model_from_row` is complete and exact for every serialized free source
   parameter, including all normalizations; all curve-producing modes use it and never
   optimize. Strict joint-AIC replay is impossible because fitted EAC constants are absent.
2. **DONE.** The axis is the detected non-upper-limit hull plus 0.08 dex, and disjoint
   detected domains control solid versus dotted curve segments. Block 2 now stops at
   417.729 keV rather than extending to 43 MeV.
3. **DONE.** Every panel has Energy, full nu-F-nu units, residual sigma, and significance
   in sigma. Each page has one figure legend with stable detector names and an explicitly
   bare `2 sigma` upper-limit arrow.
4. **DONE.** `[BEST]` is paired with a complete black figure-coordinate frame. It cannot
   be confused with the BGO identity color and no longer produces an L-shaped highlight.
5. **DONE.** Delta-AIC is referenced only to finite `STATUS=OK, VALID` models. Stored
   winners must themselves be OK/VALID and equal that minimum; 127 real regression rows
   exercise the distinction.
6. **DONE.** The 24-panel grid is six print-readable pages, four panels per page. Figure,
   font, marker, line, legend, and DPI sizes come from `PUB`; direct style tests and fresh
   vision inspection passed.
7. **DONE.** All panels in a comparison grid use points unfolded under the engine winner,
   stated in the suptitle and footer; residuals remain candidate-specific in count space.
   Missing covariance suppresses the uncertainty band and is stated, not approximated.

## FOUND — engine and provenance findings

- The engine fits EAC constants for non-reference detectors but writes only `EAC_DETS`,
  not their fitted values. This is the direct cause of the failed strict AIC replay and
  makes exact non-reference folded points/residuals impossible.
- The fit sidecar does not serialize the joint covariance, fitted background coefficients,
  effective background windows, selected TTE/RSP filenames and hashes, or a complete
  versioned snapshot of fixed builder parameters. Current-input plugin reconstruction is
  therefore diagnostic, not archival. 41b says so on every page and omits the EAC-affected
  folded diagnostics.
- No engine AIC arithmetic defect was found in the six tested block/model cases:
  profiling only the missing EAC nuisance constants recovers those stored AICs within
  `8.64e-5`. This is not a claim about every fit in the population.
- The real render emitted threeML warnings that the NA/NB/B1 TTE files contain duplicate
  time tags. I did not modify or independently adjudicate those raw inputs.
- The brief's live-file hashes drifted during execution: `scripts/41_nuFnu_panels.py` is
  now `21d36b2449148e93...` rather than `fe6566e7e0787d23...`, and `plot_style.py` is now
  `11360613ae7aec04...` rather than `8aca91019bca137c...` at repository HEAD
  `c3402e9dbcb4d05b648728e84266bdb5b52d99ab`. The frozen engine hash did not drift.

## COULD NOT — blocked work and required upstream change

- I could not make strict AIC replay pass without inventing or re-optimizing the missing
  EAC constants. 41b refuses that fallback. The engine must serialize each fitted EAC
  value per block/model (plus its detector binding) before an archival joint replay can
  be signed.
- I could not reproduce the exact original folded points/residuals or a 68% model band
  without fitted background state, input hashes, and covariance. Those elements are
  omitted or labelled as current-input diagnostics.
- I could not update `dev/ai_guides/Figures.md`, `tests/test_figure_style.py`, or replace
  live script 41 under the two-path write restriction. Consequently, the documented live
  authority still invokes the old refitting path; 41b is drop-in at the CLI but is not yet
  the repository's routed authority.
- A product with a genuinely absent engine row has no stored component to display. Direct
  selection fails loudly; `best` and `model` enumerate only rows that exist rather than
  manufacturing placeholder rows from sidecar edges.
- I did not run the spectral fit engine or write anything under `results/`; verification
  used stored products and temporary renders only.

## Independent judgment — is the 24-panel grid the right figure?

No—not as the primary answer to “which model does this bin prefer, and is that preference
real?” It is a useful diagnostic atlas or supplement, but 24 nearly coincident unfolded
curves invite shape-matching by eye and obscure the inferential question. In block 2 the
winner `Band+PL` leads `SBPL+PL` by only Delta-AIC = 1.0, which is weak relative evidence,
not a decisive physical preference.

The primary figure should instead combine: (1) a ranked valid-only Delta-AIC scorecard with
invalid/rail/convergence flags; (2) count-space residual-contribution comparisons for the
winner and strongest valid challenger, split by detector; and (3) a calibrated parametric
bootstrap/model-recovery distribution showing how often the preference survives noise,
initialization, and response perturbations. Keep the paginated 24-model grid as the audit
trail. AIC ranks models; it does not by itself establish that the preference is real.

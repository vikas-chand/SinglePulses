# Montage defect list — `bn081125496_nuFnu_best_montage.png`

**Date: 2026-08-13.** How this was produced: three reviewers examined the same PNG
(`results/sweep106/bn081125496/bn081125496_nuFnu_best_montage.png`, produced by
`scripts/41_nuFnu_panels.py --mode best`) independently and without sight of each other's
output, each through a different lens — (a) *rules*: conformance to
`~/Desktop/Projects/reference_general_figure_style.md` §S1–S13 and `dev/ai_guides/Figures.md`
F1–F13; (b) *honesty*: does the figure claim more than the stored fits support; (c) *reference*:
comparison against the LATBright montage implementation
(`~/Desktop/LATBright/GRB260226A/…/s05a_spectral_plots.py`) as a known-good sibling.
A fourth pass was a **measurement, not an opinion**: `scripts/41_nuFnu_panels.py` was imported as a
module in the `threeML` env and its `--mode best` data path re-run verbatim (`load_ctx` →
`build_plugins` → `load_engine_rows` → `fit_spec` → `data_range` → `unfold_detector`), so the
drawn x-limits and the detected/upper-limit masks below are the panel's own numbers, not estimates
off the image. Nothing in the repo was modified. This synthesis merges the three lenses, records
where they independently converged (that is corroboration, not repetition), and drops anything a
lens asserted but could not point at in the image. **All three lenses returned DO_NOT_SHIP.**

Load-bearing claims were re-verified during synthesis: the `threeML` mplstyle root cause
(`…/envs/threeML/lib/python3.9/site-packages/threeML/data/threeml.mplstyle` lines 14/17/21–25/30),
the fact that LATBright's `apply_pub_style()` (`plot_config.py:192`) never re-sets those keys, and
that `data_max` is fed by upper limits as well as detections (`41_nuFnu_panels.py:355–357`).

---

## Measurement summary (the empty-axis problem)

Every one of the 9 panels draws the **identical** energy axis, **6.58 keV → 44 672 keV = 3.832
decades**, because `data_range()` returns the union of ACTIVE channel ranges and BGO `b1` is active
to 40.6 MeV. Detected data never comes close to filling it.

| block | detected span (keV) | N det | N upper-limit | fraction of axis with no detection |
|---|---|---|---|---|
| 0 | — (none) | 0 | 50 | **1.000** |
| 1 | — (none) | 0 | 50 | **1.000** |
| 2 | 17.3 – 347.5 | 18 | 59 | 0.660 |
| 3 | 40.1 – 450.8 | 15 | 36 | 0.726 |
| 4 | 11.9 – 381.9 | 42 | 28 | 0.607 |
| 5 | 11.9 – 190.5 | 32 | 37 | 0.686 |
| 6 | 7.3 – 228.9 | 63 | 20 | 0.610 |
| 7 | 11.9 – 85.2 | 9 | 25 | 0.777 |
| 8 | 11.9 – 64.3 | 6 | 42 | 0.809 |

Mean 0.764, median 0.726. For the seven panels that have detections at all, the detected span is
**0.73–1.51 decades out of 3.83 drawn**, and **2.0–2.8 decades of axis (a factor 99× to 695× in
energy) lie ABOVE the last real data point in every panel**. Aggregated over the montage, **347 of
532 drawn markers (65 %) are upper limits, not measurements.** BGO contributes detected channels in
only 3 of 9 blocks (5 detected groups out of 185); its highest detection anywhere in this burst is
451 keV, so the top ~2 decades of BGO's own drawn range carry nothing but triangles or blank space.

---

## Ranked defects

### D1 — BLOCKER — The model is drawn solid, at full weight, across the ~76 % of the axis where nothing is detected
*Found independently by all three lenses (honesty, reference, rules); quantified by the measurement.*

**Where:** all 9 panels; worst in **bin8** (Band, last detection 64 keV, solid curve carried to
4×10⁴ keV — 2.8 decades of pure extrapolation), **bin5** (last detection 190 keV, solid to
4×10⁴ keV) and **bin2** (the additive PL component, dashed at identical weight, from ~350 keV to
4×10⁴ keV over a field of BGO non-detections). Producer: `41_nuFnu_panels.py:333–337` (band and
`med` drawn on the full `E = logspace(dlo, dhi, 200)` grid) and `:329` (sub-components likewise).

**Why it matters:** the x-limits themselves are defensible — they are the active-channel union, and
showing the full instrument range is honest. The dishonesty is in **line weight**: a reader cannot
distinguish the segment where the curve is pinned by data from the segment where it is the model's
own analytic continuation, because the two are rendered identically. In bin2 this is not cosmetic —
the flat 350 keV–40 MeV tail is the *entire reason* the engine chose Band+PL over Band, it lives
wholly in the undetected region, and it sits ~0.7 dex **below** a run of BGO upper limits. The
figure therefore asserts a measured MeV power law that the data do not carry. `Figures.md` F5 is an
earned project rule written for exactly this: *"Solid where constrained, dotted where extrapolated.
Applies to any fitted curve shown outside its fitting domain."*

**Fix in `41_nuFnu_panels.py`:** inside `draw_panel`, after the per-detector loop, accumulate
`E_min_det`/`E_max_det` as the min/max `emid` over all detectors where `det_ok` is True (the mask
already exists at line 344). Then draw the total model and every sub-component **twice**: solid
`lw=1.8` on `E ∈ [E_min_det, E_max_det]`, dotted at `lw=1.0, alpha=0.5` outside. Fade the 68 % band
the same way. Optionally add light vertical rules or an `axvspan(alpha=0.04)` over the undetected
region so the extrapolated third of the axis is visible as such. Keep the x-limits unchanged.

---

### D2 — BLOCKER — bin0 and bin1 contain ZERO measured points, and the panel never says so
*Found independently by all three lenses.*

**Where:** panels `bin0 [-1.70,-0.27] S=5 CPL` and `bin1 [-0.27,0.42] S=10 CPL`, main axes and
residual strips. Residual mask at `41_nuFnu_panels.py:358` (`rd = isfinite(resid) & ~is_ul`).

**Why it matters:** measured, not inferred — 0 detected channels, 50 upper-limit groups in each; the
residual strips contain exactly 0 coloured pixels (bin2/bin3 contain ~3000 each). Every symbol in
those two panels is a 2σ upper limit. What the reader actually sees is (a) a dense cloud of what
look like data points climbing from 10 to 10³, (b) a heavy solid CPL curve sitting ~0.5 dex *below*
that cloud, and (c) a blank residual box with a zero line through it. All three available readings
are false: *"the fit badly undershoots the data"*, *"the residuals are clean"*, or *"the panel is
broken"*. The true statement — *no channel group in this block reached the 5σ display floor; the
plotted CPL parameters come entirely from count-space channels that appear nowhere on this figure* —
is written nowhere. The titles compound it by advertising `S=5` and `S=10`, inviting the reader to
look for a detection. F8: *"Absence is stated, never silent. A panel that cannot be built says why
on its face."* This is the class of defect the Shipping Gate was created after.

**Fix:** in `draw_panel`, count detections per panel (`n_det = Σ det_ok` across detectors) and per
residual strip (`Σ rd`). Always stamp the count in the panel header or corner
(`"det groups: 18/77"`). When it is zero, print across the residual strip
`axr.text(0.5, 0.5, "no detected channels — all upper limits", ha="center", va="center",
transform=axr.transAxes, color="0.35")` and render that panel's model dashed/greyed so it visibly
stops claiming to be a fit to data.

---

### D3 — BLOCKER — Not one axis in the figure is labelled: no energy, no νFν, no σ, no units anywhere
*Found independently by all three lenses.*

**Where:** all 9 main panels (x and y) and all 9 residual strips. `draw_panel`
(`41_nuFnu_panels.py:311–371`) never calls `set_xlabel`/`set_ylabel`; the residual axis gets only
`set_yticks([-4,0,4])` at line 367.

**Why it matters:** the ordinate carries bare numerals 10⁰–10⁴, the abscissa bare 10¹–10⁴, the
residual strip bare −4/0/4. Nothing says the ordinate is νFν in keV² s⁻¹ cm⁻² keV⁻¹, nothing says
x is energy in keV, nothing says the residual is in σ. The only place on the entire 4820-px canvas
that names the ordinate at all is the 7 pt grey footnote in the far bottom-right corner. A reader is
free to take the ordinate as a photon spectrum in assumed units and the residual numbers as counts
or as a ratio. This is not a house convention: **the sibling routine in the same file already does
it correctly** — `41_nuFnu_panels.py:572–573` sets `resid (σ)`, `Energy (keV)` and the full νFν
label. So the montage path is a straight omission, and it is strictly less legible than a figure the
same script produces. LATBright's equivalent montage labels the bottom row and the left column and
suppresses interior tick labels.

**Fix:** in `draw_panel`, take the grid position (pass `row`/`col`, or use
`ax.get_subplotspec().is_last_row()/is_first_col()`) and apply the edge-only pattern —
`axr.set_xlabel("Energy (keV)")` on the bottom row else `axr.tick_params(labelbottom=False)`;
`ax.set_ylabel(r"$\nu F_\nu$ (keV$^2$ s$^{-1}$ cm$^{-2}$ keV$^{-1}$)")` and
`axr.set_ylabel(r"resid ($\sigma$)")` on the left column else `labelleft=False`. Reuse the exact
strings from lines 572–573. The suppressed interior labels also buy back the space to tighten the
layout (D12).

---

### D4 — BLOCKER — Three detector colours and a triangle glyph carry all the identity in the figure, and none is ever decoded; upper limits are additionally faded into a phantom fourth detector
*Found independently by all three lenses.*

**Where:** whole figure. `label=detlabel(det)` is attached to every detection errorbar at
`41_nuFnu_panels.py:348` and `label="68% band"` at `:333` and `label="Model"` at `:337` — then all
of them are discarded at `:371`, which calls `ax.legend(handles=comp_h, ...)`. Upper limits are
drawn at `alpha=0.5` (`:354`) against detections at `alpha=0.85` (`:349`).

**Why it matters:** the only legend in the entire 9-panel figure reads "Component 1 / Component 2".
Nothing states that the triangles are 2σ upper limits, nothing states that they too were computed
under this panel's own model, and nothing states which colour is which instrument. Because the whole
>1 MeV field is BGO non-detection (measurement: BGO's highest detection anywhere in the burst is
451 keV), the reader cannot tell which instrument is carrying the high-energy claim — the single
judgement D1 requires. Worse, F2 is broken *inside* a single panel: sampled in bin7, `na` renders as
deep navy (75,88,126) for its detections and as pale slate (149,156,179) for its limits, a 2:1
lightness split, and the same split hits `nb` (87,179,174 → 156,210,207) and `b1` (190,66,128 →
217,144,180). The eye reads 4–6 detectors in bin0. *(Inference, flagged as such: the pale slate sits
within a few units of the project's reserved LLE violet `#5b3fa0` at α 0.5 → (173,159,207), so in a
project that routinely plots LLE it can be misread as an LLE point.)* Finally the UL glyph is drawn
with a horizontal cap bar and a cosmetic 35 %-of-value stem (`yerr=ud["nufnu"]*0.35`, `:352`), which
on a log axis is visually the grammar of a measured error bar and encodes nothing.

**Fix:** collect handles/labels across detectors, de-duplicate with `dict(zip(labels, handles))`,
and draw **one** figure-level key — this montage has three free grid cells in row 3, or use
`fig.legend(..., ncol=4)`. It must contain: `na`/`nb`/`b1` colour swatches with instrument names,
filled circle = detection, open downward arrow = 2σ upper limit, grey fill = 68 % band
(covariance), and the extrapolated-line style from D1. Separately, **stop encoding detection vs
limit as an alpha change on the detector colour**: keep `alpha` identical for both, differentiate by
glyph (open/hollow arrow, no cap bar, fixed display-space stem length via matplotlib's arrow UL
marker).

---

### D5 — MAJOR — Every panel auto-scales its own y-axis off its own brightest **upper limit**, so the spectral evolution the montage exists to show is erased
*Found independently by all three lenses.*

**Where:** all 9 panels. `41_nuFnu_panels.py:355–357` updates `data_max` from `ud["nufnu"][ul]`
(non-detections!) as well as from detections, and `:365` sets
`ax.set_ylim(data_max*3e-4, data_max*4)`.

**Why it matters:** the ceiling of each frame is set by a channel in which nothing was measured, and
each panel is then normalised to its own maximum, so every fitted peak lands at roughly the same
height on the page. Reading the tick labels off the image: bin4 peaks near 2×10³, bin6 near 5×10²,
bin7 near 2×10², bin8 near 8×10¹ — a factor ~25 decline in peak νFν through the pulse — and none of
it is visible, because bin4's frame tops at 10⁴ while bin7's tops at 10³. The suptitle sells this as
"engine winner per bin" across the 9 blocks; the one quantity a per-block montage exists to show is
the one the axis choice suppresses. A reader flicking across the row sees nine similar humps and
must read four y-axes digit by digit to recover the truth. Two visible side-effects: bin0's y-axis
labels only every *other* decade (10¹, 10³) while its neighbours label every decade, so it reads as
a coarser scale; and where each model curve appears to *stop* is an artefact of the frame, not of
the band (bin0's curve exits at 3×10³ keV, bin2's at 4×10⁴, for no physical reason). All nine peaks
lie within ~1.5 decades, so a single shared range is entirely feasible.

**Fix:** exclude upper limits from `data_max` (drop lines 356–357's UL branch). Compute one global
`(ylo, yhi)` over **all** blocks from detected points plus the model curves, and apply it to every
panel. If a faint block then collapses, keep the shared limits and annotate that block rather than
rescaling it. If per-panel scaling is ever kept deliberately, it must be stated on the figure
("each panel independently scaled — peak heights are NOT comparable").

---

### D6 — MAJOR — threeML's stylesheet silently overrode the project style: no top or right spine on any panel, inward ticks left floating in white space, and every frame #3D3D3D instead of black
*Found independently by two lenses (rules, reference); root cause re-verified during synthesis.*

**Where:** all 9 main panels + all 9 residual strips. Pixel-verified on bin0: the left spine is a
solid dark run at x=122–126 and the bottom at y=903–907, but no row near the panel top and no column
at the right edge contains a continuous dark run (max 53 dark px of 830; <15 % coverage).

**Why it matters:** the visible result at the top of every panel is a broken row of tally marks
attached to nothing, and two orphan dashes at the right edge. In the residual strips the unattached
right-side minor ticks line up into what reads as a plotted dotted vertical — which in this
project's own grammar (F12) means *"edge of the analysed span"*. Reference §S3 calls inward ticks
visible on all four sides the most distinctive element of the house style, and §S2 requires a closed
black frame. **Root cause, verified:**
`/Users/salim/anaconda3/envs/threeML/lib/python3.9/site-packages/threeML/data/threeml.mplstyle`
sets `axes.spines.top: False` (line 23), `axes.spines.right: False` (24),
`axes.edgecolor: 3D3D3D` (30), `axes.labelcolor: 3D3D3D` (25), `xtick.color`/`ytick.color: 3D3D3D`
(14, 17). `threeML` is imported at `41_nuFnu_panels.py:35`, `apply_pub_style()` runs at `:39` — but
it takes the LATBright-delegate branch (`scripts/plot_style.py:89–95`), and LATBright's
`apply_pub_style()` (`plot_config.py:192`) never sets those six keys, so threeML's values survive.
`scripts/44`'s step figures, which never import threeML, DO have closed 4-sided black frames — so
this figure set is internally inconsistent, and `tests/test_figure_style.py` cannot see it because
it reads scripts as text and this is a runtime clobber.

**Fix:** add the clobbered keys to **both** branches of `scripts/plot_style.py:apply_pub_style()` —
`"axes.spines.top": True, "axes.spines.right": True, "axes.edgecolor": "black",
"axes.labelcolor": "black", "xtick.color": "black", "ytick.color": "black"`. Then extend
`tests/test_figure_style.py` with a render-and-inspect check (import threeML, call
`apply_pub_style()`, draw one axes, assert `ax.spines['top'].get_visible()` and black edgecolor) so
a third-party style clobber fails CI instead of shipping.

---

### D7 — MAJOR — The "no 68 % band" caveat is struck through by the axis and its ticks, clipped at the left spine, and in bin2 overprinted by the legend — while the band, when present, is never named
*Found independently by all three lenses.*

**Where:** the grey note in 7 of 9 panels, drawn at axes fraction (0.02, 0.02),
`41_nuFnu_panels.py:335`, `fontsize=PUB["tick_size"]-8` ≈ 6 pt, `color="0.4"`. Grey band present and
unlabelled in bin6 and bin7 (`label="68% band"` set at `:333`, never legended).

**Why it matters:** the collision is deterministic, not incidental — 0.02 axes-fraction on a ~600 px
panel puts the baseline ~12 px above the bottom spine while the inward major ticks are 6 pt ≈ 25 px
tall, so the ticks strike straight through the descenders in every panel (in bin0 it reads
"nq 68% band"). In bin2 the component legend and this text both target the lower-left corner, so all
that survives is "…available)". And the mirror problem is the real one: scanning the montage, bin7
is the *only* panel with a wide grey envelope and every other panel shows a hairline-precise black
curve. The inference a reader draws — bin7 is the poorly-determined block, the rest are tight — is
**backwards**: the band is absent precisely where the covariance railed, i.e. where the parameters
are LEAST trustworthy. F8 is satisfied in letter and defeated in fact.

**Fix:** promote the statement into the panel title where it is the same size as the winner name
(append `"  [no 68% band: railed]"` to the title string at `:466`), or move the text to
(0.98, 0.06) with `ha="right"` clear of both the tick zone and the legend corner. Give the band a
real entry ("68 % band (covariance)") in the shared key from D4. Consider hatched
"uncertainty not available" shading so the absence is graphically visible, not only textual.

---

### D8 — MAJOR — The one legend in the figure sits on top of the data and refuses to name the components that decided the model selection
*Found independently by all three lenses.*

**Where:** bin2 (Band+PL). `41_nuFnu_panels.py:329` builds labels as `"Component %d"`; `:371` hard-
codes `loc="lower left"`; `:329`/`:336` colour every sub-component `#222222` against the total's
`0.15` grey.

**Why it matters:** on a log–log νFν panel the lower left is never vacant — it is where the
low-energy end of the spectrum lives — and the box visibly swallows the dotted Component-1 curve and
the NaI points around 15–30 keV (F6: never put a legend over data; §S5/§S13 say the same). More
substantively, bin2 is the only panel in the montage claiming an additive second component and it
carries the figure's most interesting result; the title says "Band+PL" and the legend says
"Component 1 / Component 2", so the reader cannot attribute the flat 350 keV–40 MeV tail to the PL
rather than the Band. That tail is the whole claim and it lives entirely in D1's extrapolated
region. Colour compounds it: `#222222` and `0.15` grey are indistinguishable, and reference §14a
reserves linestyle-per-variant for variants of the *same* model — a Band and a power law are
different physics and LATBright keeps named colours for exactly this (`PUB["color_band"]` etc.).

**Fix:** pull the real sub-function names off the composite where `:326` iterates `subs`, label them
"Band" / "PL", colour them from the model palette, fold them into the shared figure-level key from
D4, and if a per-panel legend is retained choose its corner against where the data actually is
(upper-left is empty in bin2) rather than hard-coding `"lower left"`.

---

### D9 — MAJOR — The residual strips are clean by construction: every upper-limit group is silently dropped before plotting, and no panel says how many
*Found by one lens (honesty); code-verified.*

**Where:** residual strip of every panel; `41_nuFnu_panels.py:358`,
`rd = np.isfinite(ud["resid"]) & (~ud["is_ul"])`.

**Why it matters:** the strip only ever shows groups that passed the 5σ display floor, while the fit
behind it used the full active channel set. bin8 shows 6 points out of 48 groups; bin2 shows 18 of
77; bin0/bin1 show 0 of 50. So the visual message *"this model describes the data"* is produced by
the display's own selection, not by the fit, and the reader has no way to know the strip is a
filtered subset — no panel prints N shown / N total, and the footnote's "residuals count-space" says
nothing about the filter. A montage whose purpose is to let a human eyeball goodness-of-fit must not
hide which channels were excluded from that eyeballing.

**Fix:** print `"resid: N of M groups (UL groups omitted)"` on each residual strip, or plot the UL
groups' residuals in a muted open symbol so the exclusion is visible rather than invisible. Pairs
naturally with the D2 detection count.

---

### D10 — MAJOR — Panel headers drop every unit and hide the decision margin
*Found independently by all three lenses (units) and one (margin).*

**Where:** all 9 titles, built at `41_nuFnu_panels.py:466`, e.g. `bin0 [-1.70,-0.27] S=5  CPL`.

**Why it matters:** F13 names this exact case — *"`S` alone is not a label; significance is in σ"* —
and the interval likewise carries no seconds, even though the same script writes `[%.2f,%.2f] s`
correctly in the single-bin suptitle at `:576`. On this figure the missing unit does extra damage:
`S=5` sits above a panel with zero measured points (D2), and a reader trying to reconcile "S=5" with
an empty residual strip has no way to know that S is an aggregate count-space block significance and
not a per-channel display quantity. More substantively, the winner is a bare model name, so bin0
(S=5, zero detections, CPL) and bin6 (S=56, 63 detections, CPL) are typographically identical — a
coin-flip selection and a decisive one look the same. For a project whose central claim is model
selection, the montage shows the verdict and hides the margin. The figure also says "bin" throughout
for what this project calls a Bayesian block.

**Fix:** `bin0` → `block 0`; `[-1.70, -0.27] s`; `S = 5$\sigma$`; append
`ΔAIC = +x.x vs <runner-up>` (available from the engine row already loaded at `:557`); add the
detected-group count from D2. Add bold `(a)`–`(i)` panel labels so panels can be referred to in
text. Also fix the footnote's ASCII `nuFnu` → `$\nu F_\nu$` at `:583`.

---

### D11 — MAJOR — The text hierarchy is inverted, and at the size the report actually renders it the winning model name is unreadable
*Found by one lens (rules); measured on the rendered PNG.*

**Where:** panel titles `PUB["tick_size"]-5` = 9 pt (`:370`); bin2 legend `-7` = 7 pt (`:371`);
"no 68 % band" note `-8` = 6 pt (`:335`); footnote `-7` = 7 pt (`:583`) — against tick labels at
14 pt. Measured glyph extents at 300 dpi: title 33 px ≈ 9 pt, tick numerals 52 px ≈ 14 pt.

**Why it matters:** pure scaffolding (the numeral "10³") is 1.6× the size of the only text that
carries content (which block, what significance, which model won), and the legend at 7 pt is 42 %
below the mandated 12 pt (§S5, Figures.md §1). This is not academic: the figure is 16.8 × 10.8 in
(`figsize=(4.2*ncol, 3.6*nrow)`, `:454`) and `scripts/48_burst_report.py:216` embeds it as a plain
markdown image scaled to page width (~7 in, ×0.42). At delivered scale the panel title renders at
3.8 pt, the legend at 2.9 pt, the band caveat at 2.5 pt — the winning model name becomes unreadable
in the PDF the PI actually reads.

**Fix:** stop deriving sizes by arbitrary arithmetic offsets from `tick_size`. Use
`PUB["legend_size"]` (12) for the legend and `PUB["tick_size"]` (14) for panel titles, drop tick
labels to ~11–12 in a 9-panel montage so the hierarchy points the right way, and re-check at the
delivered scale rather than at native size.

---

### D12 — MINOR — A quarter of the canvas is empty and the figure's one model-dependence caveat is exiled into that emptiness, one sentence short of its consequence
*Found independently by two lenses (honesty, reference).*

**Where:** `_grid_shape` (`:375`, `ncol = min(4, n)`) forces 9 panels into 4 columns, leaving cells
(2,1)–(2,3) blank; gutters `hspace=0.42, wspace=0.26` (`:455`) are ~5× looser than LATBright's
0.08/0.08. The footnote is placed at figure coords (0.99, 0.004) in `color="0.45"` (`:582–583`),
diagonally opposite bin8.

**Why it matters:** the footnote — *"nuFnu data ratio-unfolded (model-dependent); residuals
count-space; XSPEC rebin 5,5; inference is count-space"* — is the statement that the plotted DATA
POINTS depend on the very model overplotted on them, i.e. the most important caveat on the page, and
it is the first thing lost when the montage is cropped into a slide or scaled into the report. It
also stops one sentence short of what matters here: each panel's points are unfolded under **that
panel's own winner** (bin2's under Band+PL, bin3's under CPL), so the identical detector channel
sits at a different ordinate in adjacent panels — and a 9-panel time sequence exists to be read
across, which is exactly what the unfolding forbids. `REPORT_bn081125496.md` repeats none of this.

**Fix:** use a near-square grid (`ncol = ceil(sqrt(n))` → 3×3 here), tighten to hspace/wspace ≈ 0.08
once D3's edge-only tick labels are in, and move the caveat to a caption line immediately under the
suptitle at `PUB["legend_size"]` in `color="0.3"`, completed: *"data points are ratio-unfolded under
EACH PANEL's own model — the same channel differs between panels; compare a model to its own points,
not points across panels."* Mirror the sentence into `48_burst_report.py:216–219`.

---

### D13 — MINOR — The panel-vs-engine agreement check is invisible when it passes, so "checked and agreed" cannot be told from "never checked"
*Found by one lens (reference); code-verified.*

**Where:** all 9 titles; `aic_stamp()` at `41_nuFnu_panels.py:450–453` returns `""` when
`|ΔAIC| ≤ 2`, and `"  [no engine AIC]"` only when the engine value is missing.

**Why it matters:** F7 requires that a figure never restate a number it did not read from the
product, and the `[! PANEL!=ENGINE dAIC=…]` stamp implements the failure branch — but the success
branch prints nothing. No stamp appears anywhere on this figure, which could equally mean the refit
agreed with the engine in all 9 blocks or that no engine row was matched in any. F8's principle
governs: absence is stated, never silent. This matters more here than usual, because the montage is
a re-fit display of stored fits — the exact configuration that produced the bn200524211
panel-vs-engine incident that the Shipping Gate was written after.

**Fix:** print the passing case too — a compact `panel=engine (ΔAIC +0.3)` in each title, or a single
figure-level line "panel refits agree with the engine winner in 9/9 blocks".

---

## FOR ADJUDICATING CODEX 41b

When `scripts/41b_nufnu_display.py` arrives, check it against these specific things. Each is a
yes/no on the rendered PNG plus a code check — do not accept a claim that a defect is fixed without
opening the image.

1. **Constrained vs extrapolated (D1).** Open the produced montage and confirm the model curve
   changes style at the lowest and highest detected channel. Re-derive `E_min_det`/`E_max_det`
   independently (from the same `det_ok` mask) for at least bin8 and bin2 and check the transition
   is at those energies, not at a hardcoded value or at the y-frame edge. Confirm the *sub-components*
   are treated the same way, not just the total — bin2's PL is the whole point.
2. **Zero-detection panels (D2).** bin0 and bin1 must carry an explicit on-face statement and a
   visually de-weighted model curve. Check the detection count is *computed*, not hardcoded, and
   that it is printed on all nine panels (including the non-zero ones) so a reader can calibrate.
3. **Axis labels (D3).** Confirm "Energy (keV)", the full νFν label with units, and "resid (σ)"
   appear. If edge-only labelling is used, confirm interior tick labels are suppressed rather than
   simply absent-by-omission, and that the *bottom-most panel of each column* is labelled — with a
   ragged 9-into-3×3 grid it is easy to leave a column's last panel unlabelled.
4. **The key (D4).** One legend must decode: detector colours with instrument names, detection vs
   2σ upper-limit glyph, the 68 % band, and the extrapolated line style from item 1. Then check the
   thing most likely to be missed: **upper limits must be the same hue and alpha as their
   detector.** Sample pixels in one panel and confirm `na` detections and `na` limits give the same
   RGB. Confirm the UL stem is no longer `value*0.35` (a fixed display-space arrow instead) and that
   the horizontal cap bar is gone.
5. **Shared y-range and the UL contamination (D5).** Confirm `data_max` no longer ingests
   `is_ul` points — this is a one-line regression that will silently return. Then confirm all panels
   share one `(ylo, yhi)`, and verify on the image that bin4 and bin8 now visibly differ in peak
   height by the true ~25×. Check every panel labels the same decade cadence (bin0's every-other-
   decade artefact must be gone).
6. **Spines and colour (D6).** This is a *runtime* clobber, so a code read is not sufficient: render
   with 41b and pixel-check the top and right edges of one panel for a continuous dark run, and
   sample the spine RGB for black rather than #3D3D3D. If 41b fixes it locally (per-axes
   `spine.set_visible(True)`) rather than in `scripts/plot_style.py`, flag that — the fix belongs in
   `apply_pub_style()` plus a CI test, or every future script that imports threeML inherits the bug.
7. **Caveat legibility (D7, D11, D12).** Re-render and then **look at the image at the size the
   report embeds it (~7 in wide)**, not at native size. The "no 68 % band" statement, the panel
   titles and the unfolding caveat must all be readable there. Check nothing is struck through by a
   spine or tick, and that no legend overlaps text or data.
8. **Component naming (D8).** bin2's legend must say "Band" and "PL", not "Component 1/2", and the
   names must be pulled from the model spec rather than hardcoded — check it still works for a
   different composite (e.g. Band+BB) on another burst.
9. **Residual filtering disclosed (D9).** Confirm N-shown/N-total appears per strip, or that UL
   residuals are drawn in a muted glyph.
10. **Titles (D10).** `S = Nσ`, interval in seconds, block (not bin) numbering, ΔAIC margin vs the
    runner-up, panel letters. Verify the ΔAIC is *read from the engine table row*, not recomputed by
    the panel — F7. If 41b recomputes it, that is a new instance of the bn200524211 failure.
11. **Agreement stamp (D13).** The passing branch must print something.
12. **Cross-cutting, and the one to check hardest: did 41b change any number?** 41b is a *display*
    of stored fits. Diff the winner names, significances and ΔAIC values it prints against
    `results/sweep106/bn081125496/bn081125496/spectral_fits.ecsv` row by row. Any disagreement is a
    blocker regardless of how good the figure looks, and the panel must say so on its face rather
    than silently adopting its own refit.
13. **Regression scope.** Confirm 41b's changes did not degrade the `bin`, `model` and `binall`
    modes that share `draw_panel`'s helpers — in particular that the already-correct labels at
    `41_nuFnu_panels.py:572–573` are preserved rather than replaced by a new abstraction that drops
    them.

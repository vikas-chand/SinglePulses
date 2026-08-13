# Skill: Figures & presentation — every plot this project ships

**Purpose:** one place that decides how a Two_Breaks figure looks, so figure quality
stops being re-litigated per plot. **Audience:** anyone (human or agent) producing a
figure here. **Reusable:** yes — the rules are project-agnostic except §2.

**Authority chain:** `~/Desktop/Projects/reference_general_figure_style.md` is the
cross-project default and wins on anything below. `scripts/plot_style.py` is its
executable form for this repo (`apply_pub_style()`, `PUB`, `det_color()`). Never
set rcParams in a figure script — import the style.

```python
import sys, os
sys.path.insert(0, os.path.join(REPO, "scripts"))
from plot_style import apply_pub_style, PUB, det_color
apply_pub_style()
```

---

## 1 · The non-negotiables (from the reference guide)
serif + `mathtext='stix'`; base 16, axis labels 18, ticks 14, legend 12; ticks
`direction='in'` on **all four sides** with minors visible; axis linewidth 1.2;
`savefig.dpi=300`, white background, `bbox='tight'`; no grid; never the matplotlib
default palette.

## 2 · Project conventions (earned, each from a real defect)

**F1 — A LIGHT CURVE IS A HISTOGRAM.** Binned counts are drawn with
`ax.step(..., where="mid")`, never `ax.plot`. A line implies interpolation between
bin centres, which is not what a binned rate is. (Vikas, 2026-08-13: *"we want
lightcurves as histograms rather"* — restating the gtburst-mirror convention.)

**F2 — Colour means IDENTITY, not order.** A detector keeps one colour in every
panel of every figure of every burst (`det_color()`): NaI cycle blue→teal→green→
orange by first appearance, BGO magenta, LLE violet. Never encode a verdict in the
fill of something whose colour already means something else — put the verdict in the
**edge**, a marker, or text.

**F3 — Mask what was never measured.** Bins outside the data's time coverage are
`NaN`, not zero. Drawing them as zero produced a cliff at the panel edge that
squashed every burst into the top half of its axes.

**F4 — Limits come from the data, not from zero.** Use the 1st–99.7th percentile
spread with a small pad. A background-dominated light curve otherwise wastes half
the panel. Zoom the x-range to the figure's SUBJECT: step 4 is about the source
window inside the gap, so it shows the gap ± half a span, not 150 s of quiet.

**F5 — Solid where constrained, dotted where extrapolated.** A background polynomial
drawn far past its fitting windows looked like a broken fit; the same curve dotted
reads correctly as extrapolation. Applies to any fitted curve shown outside its
fitting domain.

**F6 — Never put a legend over data** (reference §5). If there is no vacant space,
label the thing directly (annotation on the band) or move the explanation to a single
caption line above the axes. One shared explanation beats three repeated legends.

**F7 — A figure may not restate a number it did not read from the product.** Every
label that mirrors a table value (winner, AIC, kT, block interval) is diffed against
that table, and a mismatch is stamped ON the figure (`[! PANEL!=ENGINE]`). Born from
a montage that labelled a panel `SBPL` while the engine's winner was `Band+BB`.

**F8 — Absence is stated, never silent.** A panel that cannot be built says why on
its face; a suppressed error band says it is suppressed; a capped model list prints
what was dropped. (Shipping Gate.)

**F9 — Say what the figure is about in the title, and put the caveat in the caption.**
Titles are declarative ("9 Bayesian blocks; bar colour and number give each block's
significance"), not decorative.

**F10 — A CONTINUOUS QUANTITY GETS A COLOURBAR, NOT PRINTED NUMBERS.** Block
significance was written as a number over every block; at the peak, where blocks are
narrowest, the labels collided and the eye could not rank them. Use a colourbar
(`viridis`) and label it with the quantity AND its unit: `block significance ($\sigma$)`.
Numbers on the figure only for a handful of values that must be read exactly.

**F11 — DRAW THE THING, NOT A PRETTIER VERSION OF IT.** Bayesian blocks are
independent piecewise-constant estimates: draw them as **horizontal bars, no vertical
connectors**. Connectors made them read as one continuous step function, implying a
continuity the method does not assert. (Vikas, 2026-08-13.)

**F12 — BRACKET THE ANALYSED SPAN.** Where a figure shows a region that was analysed
inside a wider plotted range, mark BOTH edges (dotted verticals at the first block
start and last block stop). Marking only the end is worse than marking neither: it
reads as a feature rather than a boundary.

**F13 — UNITS ON EVERY SCALE, INCLUDING COLOUR.** `S` alone is not a label;
significance is in σ. Same rule as an axis: the reader must not have to guess.

## 3 · Before declaring a figure done
- [ ] rendered and **looked at** (vision or eyes) — not just "the script ran"
- [ ] no clipped text, no legend over data, no label colliding with a frame
- [ ] every axis labelled with units; math in math mode
- [ ] limits leave the data clear of the frame but waste no space
- [ ] colours consistent with F2 across the whole figure set
- [ ] the caption states what to LOOK FOR, not just what is plotted
- [ ] **a FRESH-CONTEXT reviewer has seen it** — the producer never signs off its own
      figure (ShippingGate). In practice: launch the figure-review agent over the set
      and act on its list BEFORE showing a human.

## 4 · Common pitfalls seen here
- Copying rcParams into a new script instead of importing the style (drift).
- `plt.plot` on binned data (F1).
- Anchoring y at 0 "because counts are positive" (F4).
- A percentile y-limit clipping a real feature — check, and widen if it does.
- Insets that collide with data: prefer a second panel (step 7 was rebuilt this way).

## 5 · Enforcement (why this file is not advice)
`tests/test_figure_style.py` reads the figure scripts as text and fails if: a script
does not import and apply `plot_style`; a script sets its own `rcParams`; a style
number (dpi, fontsize) is hard-coded instead of derived from `PUB`; a light curve is
drawn with a bare `plot()`; or `plot_style` drifts from the values the cross-project
reference states. Mechanical checks cannot judge whether a figure is GOOD — that is
the review agent's job — but they guarantee it is CONSISTENT. Vikas, 2026-08-13:
*"all this should be standardized and not like everytime we run something and we get
something different."*

## Hand-off
Every figure-producing script: `scripts/44_step_figures.py` (steps 1–9),
`scripts/41_nuFnu_panels.py` (νFν montage + per-bin overlays),
`scripts/48_burst_report.py` (assembles them with captions).
Shipping Gate (`ShippingGate.md`) verifies the result before it leaves.

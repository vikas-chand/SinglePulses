# Skill: Figure Vision QC — the fresh-context plot-quality gate

**Purpose:** every delivered/regenerated figure gets an INDEPENDENT vision + label-fidelity
check by a fresh-context agent (Claude subagent or Codex) — the producer NEVER verifies its
own render (ShippingGate.md). Born 2026-08-14 (bn081125496 step-1 re-render shipped
self-verified; the fresh pass then found 2 text–line collisions + 1 clipped axis the
producer had missed). **Integration is mandatory: `scripts/45` stamps every PRODUCTS.md
with the VISION QC verdict, or "PENDING — NOT yet vision-gated" (stated, never silent).**

**Audience:** whoever orchestrates a figure (re)build. **Time:** ~3–5 min/figure set.

## Inputs
```yaml
figure(s):   path(s) to the PNG/PDF under review
primitives:  the data files whose values the figure restates
             (background_intervals.ecsv, grb_sample.ecsv, qc/*.ecsv,
              spectral_fits.ecsv, block tables — whichever apply)
authorities: dev/ai_guides/Figures.md (F1–F13), detector/background/source rule files,
             ~/Desktop/Projects/reference_general_figure_style.md
```

## The gate (run in a FRESH agent context — no producer reasoning passed in)
Give the agent ONLY: the figure path(s), the primitive paths, the authorities, and this
checklist. Instruct it to be adversarial ("find problems, do not approve").

1. **VISION — collisions:** overlapping/clipped/colliding text, lines, markers, legends;
   any glyph struck by a line; anything clipped by an axis or figure edge.
2. **VISION — geometry:** axes/limits sane; data clear of the frame with padding;
   legend not over data.
3. **MACHINE — label fidelity:** every figure element that restates a data value is
   diffed against its primitive (bar lengths, shaded spans, PASS/FAIL text, winner
   labels, AIC/σ numbers, rule lines vs the rule file). A label–primitive mismatch is
   a HARD FAIL (the bn200524211 montage class).
4. **STYLE:** serif/STIX, ticks in on all 4 sides, dpi/fonts per the reference guide.

## Verdict + recording (both mandatory)
- Verdict block: `VERDICT: PASS | PASS-WITH-NITS | FAIL`, then each defect with
  severity (HARD-FAIL / NIT), location, and the primitive value if a mismatch.
- Append the full report to `<products_dir>/VISION_QC.md` (create if absent; the file
  `scripts/45` reads for the manifest stamp). Include date + verifier identity.
- HARD FAIL ⇒ the figure does not ship; fix and RE-VERIFY (same or new fresh agent).
  NITs ⇒ fix when touched; record them.

## Common pitfalls
- The producer "just quickly checking" its own render — that IS the violation.
- Verifying only vision and skipping label-fidelity (or vice versa) — both, always.
- Fixing a nit and shipping without the re-verify round.
- Passing the producer's reasoning into the verifier context (inherits blind spots).

## Hand-off
Verdicts feed `scripts/45` PRODUCTS.md (stamp) and, at burst end, the walkthrough
record `notes/reconciliation/<trig>.md`. Lessons distill into Figures.md / the step's
skill file per BurstWalkthrough.md.

## STANDING PRODUCT CONTRACT — SED figures (41c) — derives from the PI's spec, NOT the producer's code
The verifier prompt for any SED figure MUST include these items verbatim. A producer
may add per-round items but may NEVER remove or invert a standing item. This section
exists because on 2026-08-15 the producer wrote "C7: NO shaded band" into a round
contract — encoding his own wrong decision — and the gate passed a figure missing the
band the PI had explicitly required. The gate verifies the PI's spec.
S1. The threeML-like 68% error band IS part of the product (Vikas). It must be DRAWN
    whenever threeML's native machinery returns an interval AND fewer than 95% of the
    native draws railed at bounds; the retained-draw fraction is disclosed on-figure
    when <99%. AMENDMENT (Vikas, 2026-08-15: "Yes ok" to the F2 proposal): at >=95%
    railed the band is bounds geometry, not a credible interval — SUPPRESS with the
    on-figure note "(bounds geometry)". Absence of the band is a VIOLATION unless the
    figure carries that note or a technical-failure note.
S1b. EAC bounds STAY [0.8, 1.2] (Vikas, 2026-08-15: "we let them not go outside") —
    rails at 0.8/1.2 are an accepted calibration prior, NOT a defect to fix by
    widening; F10's low-energy caution stands but no bounds change.
S1c. The top-margin stamp prints PGstat/dof AND AIC (Vikas, 2026-08-15: the statistic
    "is supplementary to see residuals with these values") — format
    "PGstat/dof=X/N | AIC=Y (k free) | matches stored".
S2. Data: strict XSPEC — every rebin group a point, no upper-limit arrows
    (--ul-arrows opt-in only), rebin 5 5 semantics, groups never bridge a mask gap,
    no point inside an excluded range.
S3. One black model curve; all points in the k=1 reference frame (points / k), k
    values disclosed in legend labels + a footer disclosure line.
S4. Nothing drawn outside the fitted energy range; y-range data-driven (XSPEC
    setRanges rule).
S5. Every number printed on the figure is verified against the SAME-RUN provenance
    sidecar JSON — never against producer-typed values.
S6. Residual panel labeled (net−model)/σ until exact PGstat delchi lands.
Amendments to this section require the PI's word, quoted with date.


## NO-EXCEPTION DELIVERY RULE (2026-08-15, after the Bala-figure violation)
EVERY figure delivered to the PI passes a fresh-context vision gate FIRST — including
third-party / upstream-native figures. There is no "not our figure" exception; the
producer inventing an exception unilaterally IS the violation (4th instance of
producer-eyes-only shipping, caught by Vikas: "what about the agent that was supposed
to look at it"). For third-party figures the gate checks the G-items (numbers vs the
run's own output files; occlusion/legibility; internal sanity + what a PI would
misread), NOT our style contract — their layout is their layout; remediation is
caption/caveat, never restyling their output. The retroactive gate on the Bala MVT
figure proved the point: it surfaced a sub-3-sigma z-score (2.49) on the headline
number that the producer had presented without qualification.


## NO-MODEL-DROPPED RULE (Vikas, 2026-08-16: "we are not dropping any models ok")
Every (model, bin) pair in the engine table gets a PANEL: live-verified
(|dAIC|<=0.1), or FROZEN REPLAY (stored solution evaluated exactly, stamped, no
band), or — only for a STRUCTURAL mismatch where even the frozen replay cannot
reproduce the stored likelihood — a labeled refusal cell that is simultaneously
a bug report (data/mask difference requiring investigation). Guard-drift alone
never empties a cell again.

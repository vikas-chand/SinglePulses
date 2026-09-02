# Batch-1 review agenda — the 7 reports (for the session with Vikas)

Plan agreed 2026-08-17: **review this batch → feedback → improve → distil into
skills → then start fresh on the next 20.** Meanwhile all 106 bursts get fitted
and montaged, so the next batch never waits on compute.

Capture protocol: `dev/ai_guides/PI_REVIEW_PROTOCOL.md` (every comment routed to
the layer that can enforce it, in the same session).

## The batch

| # | burst | paper | pages | what it contributes |
|---|---|---|---|---|
| 1 | bn081125496 | GRB081125496 | 13 | line-of-death violator, no thermal, spurious integrated composite |
| 2 | bn081222204 | GRB081222 | 14 | first z (2.77), synchrotron-compatible, one thermal candidate |
| 4 | bn090530760 | GRB090530 | 13 | first DSBPL winner; violation+compliance in ONE burst; kT cooling track 22→6 keV |
| 5 | bn090620400 | GRB090620 | 16 | first non-FRED (mixed) pulse; edge-artifact BB caught (kT=1.1 keV) |
| 6 | bn090719063 | GRB090719 | 17 | fastest MVT (8.9 ms); CWT new rung; first off-rail integrated fit |
| 7 | bn090804940 | GRB090804 | 15 | first BB-bearing INTEGRATED winner; quasi-stable kT; zero-consistent lag |
| 8 | bn090809978 | GRB090809 | 15 | largest lag fraction; sharpest AIC-vs-LRT thermal split |

(#3 bn081224887, the GBM+LLE+LAT broadband burst, has fits + products in flight;
its report is deliberately held until after this review so it inherits whatever
we change.)

## What I think is GOOD (my own read, to be challenged)

1. **Numbers are twice-checked and the checks bite.** Three of seven failed
   first verification; every correction is ledgered with the recomputed value.
2. **Failures are reported as failures** — estimator refusals (Bala admission
   gate, CWT no-minimum), bound-railed invalid winners, engine-FAIL cells now
   rendered as labelled refusal panels.
3. **Metric disagreements are surfaced, not adjudicated silently** — AIC winner
   vs nested-LRT BB significance (sharpest in #8), and both reported.
4. **Cross-burst quantities are accumulating into real curves** — lag fraction
   0→8.8%, CWT rung ladder 181/215/256, φ 0.017→0.41, thermal phenomenology in
   three distinct flavours.
5. **Every product carries provenance**: script SHA-256 + exact argv, now
   assembled per burst into `REPRODUCTION_<trig>.md`.

## What I think is NOT good (my own list, before you add yours)

1. **Cross-burst claims are the weakest class.** Superlatives and counts drift:
   the CWT rung count was wrong in four papers at once because unpapered burst
   #3 was invisible to a papers-only count. Needs a single computed
   cross-burst table that every paper quotes from — not prose per paper.
2. **Tie-level preferences carry too much narrative weight.** In #6 and #8
   *every* spectrum is decided by ΔAIC < 2, yet the text still names "winners"
   per bin. We need a stated rule for when a winner is reportable.
3. **Undefined criteria leak into prose**: "robust", "strong candidate",
   "reliable blocks", "quasi-stable". Each needs a number or must go.
4. **The uniform-Band α trend is fit in bins where a composite model wins.**
   The line-of-death claim rests on reading a single-Band α in bins where Band
   is not the preferred shape. Is that legitimate? (My guess: needs a stated
   caveat or a different estimator.)
5. **EAC rails are pervasive and disclosed but not quantified.** We never show
   how much a railed b0 = 0.80 moves α. One test fit per burst with EACs frozen
   at 1.0 would bound it.
6. **Prose is AI-written and unreviewed by a physicist** — register, hedging,
   and paragraph density have had no human pass.
7. **Papers repeat the same methods text** seven times; a shared methods
   section would cut ~2 pages each and remove drift between copies.

8. **The notebook read a different input catalog than the papers.** Found
   2026-08-17 when notebooks were first shipped with the reports: the notebook
   hardcoded `background_intervals_human_clean.ecsv` (89 bursts, July human-review
   subset) while every paper was produced from `background_intervals.ecsv`
   (106, stamped). 17 bursts — including paper #4's — could not be reproduced at
   all. Fixed (notebook now reads the production catalog, overridable via
   `GRB_BKG_CATALOG`), but it is the clearest evidence yet that **"ships with a
   runnable notebook" is a real check, not a formality** — the divergence was
   invisible while the notebook was never run against a papered burst.

## Questions only you can settle

1. Reportability rule for tie-level winners (ΔAIC threshold? report the tie set?).
2. Whether the α trend may use non-winning Band fits, and with what caveat.
3. Whether thermal claims should be AIC-led, LRT-led, or always both.
4. Whether the 21 newly-binned bursts (never human-reviewed at Stage 1) may
   enter the census, or stay a separate tier.
5. Whether each burst gets its own paper at all, or becomes a section of one
   population paper with per-burst appendices.

## Intended outputs of the session

- `notes/PI_REVIEW_20BURST_FEEDBACK.md` — your comments verbatim + routing.
- Amendments to `FigureVisionQC.md` (figure conventions) and the L-series
  (physics lessons), quoted and dated.
- New/edited skills: a `PerBurstReport` skill capturing the report recipe with
  your rules baked in, so the next 20 are produced correctly by construction.
- A computed `results/campaign/CROSS_BURST_TABLE.ecsv` that every future paper
  quotes, killing failure class #1 above.

9. **Papers #1 and #2 carry figures rendered by superseded script versions.**
   Found by the invariant checker (I5) 2026-08-17: burst #1's temporal figures
   predate the `47b_temporal_figs.py` fixes (Haar upper-limit arrow visibility,
   per-burst parameterisation) and burst #2's SED panels predate the `41c`
   refusal-cell handling. Both are being re-rendered with current code.
   **Consequence: both papers need a figure re-gate before they ship** — the
   numbers are unaffected (the fit tables did not change), but the figures in
   the PDFs are not the ones current code produces.

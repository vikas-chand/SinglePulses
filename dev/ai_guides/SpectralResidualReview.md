# Skill: Spectral Residual Review — per-fit vision notes + band-resolved likelihood

**Purpose:** for each time bin, each SIMPLE model's rendered fit (its own SED+residual
panel from the `scripts/41b --mode bin` atlas) is READ by a fresh-context vision agent
and annotated; alongside, a quantitative per-energy-band likelihood decomposition says
*which part of the spectrum each model fails*. Together they answer: does the model
describe the data; where are the systematic deviations; what do they suggest.
**Origin:** Vikas, 2026-08-14 (bn081125496 walkthrough, step 8, product #3), verbatim
intent: *"the simplest models be seen by a vision agent and comment/notes be provided on
each fit — how it is, how are parameters, does the plot model well; if not, where are
systematic deviations or trends, higher or lower energy, what does that suggest; which
range is better modeled; and compare models on energy ranges by likelihood (likelihood
is a sum over energy channels)."*

## Scope
- **Models:** the simple continua — BAND, CPL, SBPL, DSBPL (+PL where registered) —
  NOT the composites; composites enter only as the hypothesis the notes point toward.
- **Bins:** every ordinary block + T_INT.
- **Inputs per (bin, model):** the atlas panel (SED + count-space σ residuals per
  detector), the stored parameters/errors from `spectral_fits.ecsv`, and the band-stat
  table (below).

## Arm 1 — vision notes (fresh-context agent; producer≠reviewer)
For each (bin, model) panel, the agent writes, in this order:
1. **Fit verdict** — good / adequate / poor, with the residual evidence named.
2. **Parameters** — values ± errors sane? railed? (bounds in the table); error size
   vs the block's significance.
3. **Systematic residual structure** — runs/trends and WHERE: low (NaI <~30 keV),
   mid (~30–300 keV), high (NaI >300 keV / BGO). Use the L10/L11 grammar:
   monotonic run → break at onset; up-down/down-up mode → peaked component
   (BB on the shoulder; line if localized); terminal negative run → cutoff beyond.
4. **Which range is better modeled** — explicit low/mid/high statement per detector.
5. **What it suggests** — the named next hypothesis, tied to the menu (e.g. "terminal
   BGO run → CPL-family cutoff; test = LRT vs Band").
Notes are COMPARATIVE within a bin: the same agent reads all simple models of that bin
so "model X absorbs the 100 keV weave that model Y shows" is stateable.

## Arm 2 — band-resolved likelihood table (machine, exact)
The joint −2lnL is a sum over channels; partition it over DECLARED bands and models:
- Bands: NaI 8–30 / 30–300 / 300–900 keV; BGO 0.3–1 / 1–10 / 10–40 MeV (K-edge mask
  respected; per-bin RESPONSE_UNCOVERED channels excluded).
- For each (bin, model, band): Σ pgstat contributions with the STORED parameters +
  recovered EAC (no refit — 41b machinery); report Δband-stat vs the bin's winner.
- Product: `results/<root>/<trig>/bandstat_<trig>.ecsv` + a per-bin heat table in the
  review note. Positive Δ localizes WHERE a model loses; the vision note and the
  Δband column must AGREE — a disagreement is a finding about the figure or the stat.
- ⚠ These per-band sums are DIAGNOSTIC decompositions, not selection statistics —
  winner selection stays the gated whole-band AIC (no per-band model shopping).

## Outputs
- `notes/residual_review/<trig>_bin<N>.md` — one note per bin (all simple models).
- `bandstat_<trig>.ecsv` as above; referenced by the notes.
- Burst-level synthesis paragraph into the step-8 section of `REPORT_<trig>`.

## Pitfalls
- Reviewing the winner only — the POINT is the simple models' failures (L10: unfold
  under a SIMPLE model so structure stands off the curve).
- Letting the vision agent see the engine's winner/AIC before writing (bias) — give
  it panels + parameters, not the verdict; it may see AIC labels burned into panels
  only AFTER its structure notes are drafted (two-pass prompt).
- Treating band Δstat as a fit test (it is localization, not calibrated inference).
- One agent for all bins (context bleed) — one fresh agent per bin.

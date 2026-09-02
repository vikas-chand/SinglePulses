# CODEX BRIEF — one-pass external audit of the campaign papers

Run mode: GPT-5.6, Sol, Ultra. Working directory:
/Users/salim/Desktop/Projects/SingleRest/Two_Breaks
**READ-ONLY except your report.** Write only
`notes/CODEX_AUDIT_CAMPAIGN_<YYYYMMDD>.md`. No fits, no renders, no git.

## Why you and not Claude
Every paper here was produced by Claude and gated by fresh-context Claude
verifier agents. Those gates caught real defects (a stale-table QC figure, an
invisible-refusal-cell contract violation, several wrong cross-burst counts) —
but they share a model family, a training lineage, and the campaign's own
vocabulary with the producer. You are the **different-family check**: the
failure modes we cannot see because we all see alike. Your quota is scarce and
paid for; this is the one task worth spending it on.

## The artifacts of record
`paper/GRB081125496/`, `paper/GRB081222/`, `paper/GRB090530/`,
`paper/GRB090620/`, `paper/GRB090719/`, `paper/GRB090804/`,
`paper/GRB090809/` (each: `main.tex`, compiled `GRB*.pdf`, `figs/`).
Ground truth for every number:
- `results/convention_check/<TRIG>/spectral_fits.ecsv` (24 models x N spectra;
  winner = min AIC per BLOCK row; BLOCK=-1 is the integrated spectrum;
  `<MODEL>_VALID` = validity gate; `<MODEL>_STATUS` = engine status)
- `results/temporal_catalog_all106.ecsv` (durations)
- `results/sweep106/<TRIG>/*_step7_figs.json`, `*_step7_lag_latbright.json`
- `results/mvt_upstream/run_step7/<TRIG>/result.json` (canonical MVT)
- `results/background_intervals.ecsv` (human-approved Stage-1 selections)
- per-burst ledgers `results/sweep106/<TRIG>/VISION_QC.md` (what we already
  found and fixed — do NOT re-report those; go past them)

## What to audit (in priority order)

**A. Cross-burst claims.** These are the campaign's weakest class: every paper
asserts things about the *other* bursts (rung counts, "campaign's largest",
"Nth consecutive", shape-class counts, thermal-track comparisons). One such
error propagated through four papers before a verifier caught it, and the
sample includes bursts with products but no paper (#3 bn081224887 above all).
Recompute each superlative and each count directly from the products of ALL
fitted bursts (`results/campaign20_fam/*_highe/spectral_fits.ecsv`,
`results/temporal_catalog_all106.ecsv`), not from what the papers say.

**B. Whether the physics conclusions survive the caveats we ourselves state.**
Each paper discloses bound-railed fits, EAC rails, tie-level margins, edge-zone
blackbodies, metric splits (AIC winner vs nested-LRT). Ask the question we may
be too invested to ask: **given those caveats, is the stated conclusion still
supported?** In particular:
 - the "epoch-dependent line-of-death violation" claimed in five consecutive
   bursts — is it robust, or an artifact of fitting a Band α in bins where a
   composite model wins and the single-Band read is unreliable?
 - the thermal claims (#4 cooling track, #7 quasi-stable track, #8 AIC-vs-LRT
   split) — are these the same phenomenon reported three ways?
 - the CWT grid-quantization finding — is our interpretation (estimator scale
   ladder) correct, or could it be a real physical clustering we are dismissing?
 - the lag--width relation spanning 0 to ~9% of T90 — is the window-scan
   systematic large enough to make the whole spread consistent with a constant?

**C. Method conformance.** Spot-check that the papers describe what the code
does: response weighting (threeML count-weighted `.rsp2`), the K-edge
exclusion, LLE/LAT inclusion gated on data not significance, blocks reused not
re-derived, best-minimum-per-(bin,model) canonicalization. Read the scripts
(`scripts/10_spectral_fit_burst.py`, `41c_paper_sed.py`, `44_step_figures.py`,
`47b/47c`) rather than trusting the prose.

**D. Anything a referee would reject.** Register, units, undefined symbols,
claims without a stated criterion ("robust", "strong candidate", "reliable
blocks" — are these defined anywhere?), figure/caption mismatches.

## Output contract
```
VERDICT — SIGN OFF or DO NOT SIGN OFF (state plainly)
A. CROSS-BURST CLAIMS: per claim CONFIRMED / WRONG (with the recomputed value)
B. CONCLUSIONS VS CAVEATS: per conclusion SURVIVES / WEAKENED / UNSUPPORTED,
   with the specific caveat that does the damage
C. METHOD CONFORMANCE: per item CONFORMS / DIVERGES (quote code and prose)
D. REFEREE-BAIT: list
COULD NOT VERIFY: what and why
```
Close with: *"Finally, your own independent judgement: anything wrong or
fragile that this brief did not ask about"* — on past evidence that section has
been the most valuable part.

Efficiency notes (your quota is paid for and finite): read the seven `main.tex`
files and the product tables directly; do not re-derive what the per-burst
`VISION_QC.md` ledgers already record as found-and-fixed; one pass, no retries.

# Audit brief — night-shift scorecards + L28 edge protocol (2026-08-11)

You are an independent auditor. Work READ-ONLY from the repo root
`/Users/salim/Desktop/Projects/SingleRest/Two_Breaks`. Adjudication happens by
RE-DERIVATION: for Task 1 you must compute your own numbers from the primitive
files BEFORE opening ours. Independence lives at the primitive — derive your
column semantics from the engine source, not from our summaries.

## Task 1 — BLIND re-derivation of the night scorecards (do this FIRST)
⚠ Until Task 1's derivation is written down, do NOT open any `*_scorecard.txt`,
`results/walkthrough_night_summary.json`, or `notes/reconciliation/*` file.

Nine bursts, fit tables at `results/walkthrough_b<i>/<trig>/spectral_fits.ecsv`:
b11=bn180728728 b13=bn150306993 b14=bn151021791 b15=bn150213001 b16=bn170921168
b17=bn171210493 b18=bn160910722 b19=bn160330827 b20=bn180723757 (b12=bn150721242
failed; see Task 4).

Derive the schema (model list, `*_VALID`, `*_AIC`, `LRT_*`, `*_KT` columns, block
column, negative-index conventions) from `scripts/10_spectral_fit_burst.py`
(MODEL_SPECS etc.), then compute per burst:
1. N blocks where the best VALID extra-component model beats the best VALID
   simple/one-break model by ΔAIC ≥ 10 (DECISIVE) and 6 ≤ ΔAIC < 10 (STRONG).
   Decide yourself, from the engine source, which models count as "simple" —
   document your list.
2. Blocks with a significant blackbody: nested LRT ≥ 9.2 AND kT off the low rail
   (engine bounds (1,200); L27 log rule ⇒ rail zone kT < ~1.05).
3. The kT track (block, kT) for those blocks.
THEN open `results/walkthrough_night_summary.json` + the five scorecard txts and
emit a DIFF TABLE: our value vs yours, per burst, with the cause of every
mismatch (e.g. if our ad-hoc model partition differs from the engine's).

## Task 2 — L28 verification against the source papers
Files: `scripts/10_spectral_fit_burst.py` (`edge_feature_class`, constants),
`tests/test_lessons.py::test_L28_edge_feature_class`, the L28 entry in
`dev/ai_guides/SpectralFitting.md`. Source PDFs (extract text with fitz or
strings): `Skills_training/Tierney_2013_2013AA550A102T.pdf`,
`Skills_training/Ravasio_2019_2019AA625A60R.pdf`.
Verify EVERY factual claim: Tierney's GRB 090323 Band+BB kT = 4.99±0.5 keV;
090424 kT ≈ 9 keV and DBPL Ebreak1 = 32.7 keV; LET values and ~1000 simulations;
Ravasio App. B: 20 keV boundary, 171010 Ebreak = 12.39 keV with α1 = +1.16,
quarantine of Ebreak < 20 keV from population stats; the 3.92·kT νFν-peak factor.
Flag any misquote, over-reach, or place where the lesson claims more than the
papers support; check the classifier boundaries match the lesson text.

## Task 3 — blind-first trail for the nine P0 freezes
`notes/reconciliation/<trig>_P0_frozen.json` for all nine bursts: verify each
exists, its mtime PRECEDES the burst's scorecard/summary mtimes, and its
`predictions` contain NO numbers derivable from the burst's own fit table
(archival-census priors and literature snippets are allowed; leaked fit results
are a violation).

## Task 4 — diagnose the b12 failure
bn150721242's fit died: `KeyError: "Extension ('MATRIX', N) not found"` on v00
RSP2 files, every block reporting "no plugins". Inspect the RSP2 headers under
`data/bn150721242/` (astropy.io.fits), the response-resolution code in
`scripts/10_spectral_fit_burst.py`, any log under `results/walkthrough_b12/`,
and the historical single-matrix extraction fix (grep the repo for rsp2
collapse / extract). State the root cause and the minimal fix. Do NOT edit.

## Report format (stdout)
Severity-ranked: MUST-FIX / SHOULD-CONSIDER / NOTE, each with file:line and a
one-line fix; Task 1's diff table in full; end with a 5-line executive summary.

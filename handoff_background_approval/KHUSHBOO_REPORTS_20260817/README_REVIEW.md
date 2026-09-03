# Campaign reports for review — 7 bursts (2026-08-17)

Hi Khushboo — these are the first seven per-burst reports from the single-pulse
campaign. Everything here is **provisional** and none of it has had a human
sign-off yet; that is what we are asking you for.

## What is in this bundle

| folder | contents |
|---|---|
| `reports/` | the seven papers as PDFs (compressed for e-mail; the full-resolution originals live in `paper/GRB*/`) |
| `notebooks/` | one **executable end-to-end notebook per burst** — the whole analysis chain, runnable and adjustable (see below) |
| `tables/` | the per-burst all-model AIC tables + `HEADLINE_NUMBERS_CROSSCHECK.md` |
| `ledgers/` | each burst's `VISION_QC.md`: what our own gates already found and fixed |

## How these were produced (so you know what to distrust)

Each report was written by an AI agent from the product files, then checked by a
*separate* fresh-context agent that recomputed every number from the products
and inspected every figure. Those checks failed three of the seven papers on
first pass and forced corrections — the ledgers record each one. That means:

* the numbers have been machine-checked against the products **twice**, but
* nobody has yet asked whether the *physics conclusions* are sound, and
* an AI wrote the prose, so the interpretation carries AI judgement that has
  never been reviewed by a physicist.

## What we would most value from you (in priority order)

1. **Recompute the headline numbers independently.** Use
   `tables/HEADLINE_NUMBERS_CROSSCHECK.md`: every row names the product file it
   came from. Take the numbers from the products, not from the PDFs, and flag
   any mismatch. This is the single most useful thing.
2. **Run at least one notebook end-to-end** (below) and tell us whether it
   reproduces the report's spectral result for that burst. Change something —
   a model, an energy range, a bin — and see whether the machinery behaves
   sensibly when pushed.
3. **Challenge the interpretation.** Especially: (a) the claim that the
   synchrotron "line of death" is violated in early epochs and respected in the
   decay, which appears in five consecutive bursts; (b) the thermal claims,
   which come in three flavours (a cooling track, a quasi-stable track, and a
   case where AIC and the nested likelihood-ratio test disagree); (c) whether
   the tie-level model preferences (many winners are decided by
   ΔAIC < 2) can carry the weight the text puts on them.
4. **Flag anything a referee would reject** — undefined criteria, register,
   figures that do not show what their captions claim.

Please do **not** spend time re-finding what the ledgers already list as found
and fixed; go past those.

## Running a notebook

```bash
conda activate threeML
cd <repo root>
export GRB_BURST=bn090530760          # or any of the seven
jupyter lab notebooks/Two_Breaks_single_GRB_pipeline.ipynb
```
or headless:
```bash
python notebooks/run_grb.py bn090530760 --depth full --execute
```

**Important design point:** this notebook contains **no LLM calls at all** —
it is pure `threeML` plus our production scripts, so every number in it is
computed, never generated. (There is a *separate* `Two_Breaks_llm_review.ipynb`
that asks a model to comment on finished products; it can never write into
`results/` and is forbidden from stating any number not present in what it was
given. Keep the two straight when you review.)

The executed copies in `notebooks/` are that same notebook run against the
current data — they are the human-verifiable trace of the analysis, and you can
edit and re-run any cell.

## Known gaps we already know about

* The 21 bursts without Bayesian-block tables are out of scope for now; 85 of
  106 are being fitted, and reports exist for 7.
* Burst #3 (`bn081224887`, the GBM+LLE+LAT broadband one) has fits but its
  report is still being produced.
* Effective-area (EAC) factors rail at their bounds in many fits; this is
  disclosed in every paper but is a real systematic on the low-energy indices.
* The older executed notebooks in `notebooks/outputs/` from July predate an
  energy-convention refit, so ignore any of those you may still have.

# Notebooks: the fitting/LLM separation (PI ruling 2026-08-17)

> "I don't know, I want to trust these fits and that none is produced or
> hallucinated data; so maybe we keep only the fitting part in notebooks?"
> — Vikas, 2026-08-17

Accepted, and implemented as a hard split.

## The two notebooks

| notebook | contains | may it call an LLM? |
|---|---|---|
| `Two_Breaks_single_GRB_pipeline.ipynb` | the analysis: inventory → detectors → background → blocks → temporal → 24-model spectroscopy → census → evolution → literature table | **NO. Ever.** |
| `Two_Breaks_llm_review.ipynb` | reads finished products, asks a model to comment | yes, commentary only |

The first is the **trust anchor**: every number in it comes from threeML and the
production scripts, reproducibly, with no network call in the data path. A
mechanical check, `grb_llm.assert_pipeline_is_pure()`, greps that notebook for
`grb_llm` / `anthropic` / `ANTHROPIC_API_KEY` and raises if any appears — so the
separation cannot erode by accident. The review notebook calls it on startup,
which means the guard runs every time anyone uses the LLM side.

## What the LLM is allowed to do

Read products. Emit prose. That is all. Three enforcements in `grb_llm.py`:

1. **Quote-only numbers.** The system prompt forbids stating any number not
   present verbatim in the supplied context ("say MISSING instead"), and every
   response is scanned: numeric tokens absent from the context are listed as a
   **GUARD FLAG** in the output file's header. (Unit-tested: given context
   `kT=22.4`, the answer "kT is 22.4 and Ep is 999.9" flags `999.9`.)
2. **Quarantine.** Output goes only to `notebooks/llm_review/<trig>/`, with an
   `AI-GENERATED COMMENTARY — NOT A MEASUREMENT` banner and a provenance sidecar
   (model id, prompt/context sha256, UTC, token usage, flagged tokens). Nothing
   under `results/` is written. No paper takes a number from here — papers quote
   products.
3. **Fail-soft, never fake.** Missing key, missing SDK, or an API error returns
   `None` and prints why. It never substitutes a placeholder verdict. (Verified
   live: with a stale key the call returned `None` and produced no file.)

## Setup

`pip install anthropic` (already done in the `threeML` env) and put a working
key in the project `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

The stale key in `~/Desktop/LATBright/GRB260226A/.env` returns 401 — the module
finds it but the call fails soft, so a real key must go in the project `.env`.
Model defaults to `claude-opus-5` (override: `TWO_BREAKS_LLM_MODEL`).

## Regenerating the pure pipeline notebook per burst

```
python notebooks/run_grb.py <trigger> --execute        # -> notebooks/outputs/<trigger>.ipynb
```

Note: the executed notebooks currently in `notebooks/outputs/` and
`notebooks/verified/` date from 2026-07-19/30 and therefore **predate the
energy-convention refit** — their numbers do not match the current canonical
tables or the campaign papers. They need re-execution before being shown
alongside a paper.

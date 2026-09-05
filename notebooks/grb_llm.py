#!/usr/bin/env python
"""Anthropic LLM helpers for the Two_Breaks notebooks — COMMENTARY ONLY.

PI ruling (Vikas, 2026-08-17): "I want to trust these fits and that none is
produced or hallucinated data; so maybe we keep only the fitting part in
notebooks?" — accepted. The architecture that follows from it:

  * `Two_Breaks_single_GRB_pipeline.ipynb` is the TRUST ANCHOR: pure
    threeML/scripts computation, no LLM, no network. It must never import this
    module. (`assert_pipeline_is_pure()` below enforces that mechanically.)
  * This module is used ONLY by the separate review notebook. It may READ
    finished products and EMIT PROSE. It never writes into results/, never
    returns numbers for downstream use, and its output is never a measurement.

Three hard guarantees, each enforced in code below:
  1. QUOTE-ONLY NUMBERS. Every prompt carries a system rule: state no number
     that is not present verbatim in the supplied context; if a needed number
     is absent, say MISSING. Responses are scanned and any numeric token not
     found in the context is flagged in the output header.
  2. QUARANTINE. All output goes to notebooks/llm_review/<trig>/ with an
     AI-GENERATED banner and a provenance sidecar (model id, prompt sha256,
     UTC, context files). Nothing under results/ is touched.
  3. FAIL-SOFT, NEVER FAKE. No API key or no network => returns None with a
     clear message. It never invents a placeholder verdict.

Model default: claude-opus-5 with adaptive thinking (override with
TWO_BREAKS_LLM_MODEL). Requires ANTHROPIC_API_KEY (this module looks in the
project .env, then ~/Desktop/LATBright/GRB260226A/.env).
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import time
from typing import Iterable, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUARANTINE = os.path.join(ROOT, "notebooks", "llm_review")
MODEL = os.environ.get("TWO_BREAKS_LLM_MODEL", "claude-opus-5")

SYSTEM = """You are a commentary agent for a Fermi/GBM gamma-ray-burst analysis
pipeline. You are reading FINISHED products produced by deterministic code.

ABSOLUTE RULES:
1. Never state a numeric value that is not present verbatim in the context you
   were given. If a number would be needed and it is not in the context, write
   MISSING instead. Do not compute, estimate, round differently, or infer
   numbers.
2. You are not measuring anything. Your output is commentary and will be stored
   in a quarantine directory labelled AI-GENERATED. Never phrase anything as a
   new result.
3. If the products contradict each other, say so plainly and point at the two
   sources. Contradictions are the most valuable thing you can report.
4. Uncertainty is information: say "cannot tell from these products" rather
   than guessing.
5. Be terse. A first-year PhD student is the reader."""


def _load_key() -> Optional[str]:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    for cand in (os.path.join(ROOT, ".env"),
                 os.path.expanduser("~/Desktop/LATBright/GRB260226A/.env")):
        if os.path.exists(cand):
            for line in open(cand):
                if line.startswith("ANTHROPIC_API_KEY"):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val:
                        os.environ["ANTHROPIC_API_KEY"] = val
                        return val
    return None


def assert_pipeline_is_pure(nb_path: str = None) -> None:
    """Fail loudly if the fitting notebook has acquired an LLM dependency."""
    nb_path = nb_path or os.path.join(ROOT, "notebooks",
                                      "Two_Breaks_single_GRB_pipeline.ipynb")
    src = open(nb_path).read()
    for bad in ("grb_llm", "anthropic", "ANTHROPIC_API_KEY"):
        if bad in src:
            raise AssertionError(
                f"TRUST ANCHOR VIOLATED: '{bad}' appears in {nb_path}. "
                "The fitting notebook must contain no LLM dependency.")
    print(f"trust anchor OK: {os.path.basename(nb_path)} is LLM-free")


def _unquoted_numbers(answer: str, context: str) -> list:
    """Numeric tokens in the answer that do not appear in the context."""
    ctx = context.replace(",", "")
    out = []
    for tok in set(re.findall(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?", answer)):
        if len(tok) <= 1:          # bare digits: list numbering, "1 of 3"
            continue
        if tok not in ctx and tok.lstrip("-") not in ctx:
            out.append(tok)
    return sorted(out)


def ask(prompt: str, context: str, images: Iterable[str] = (),
        trig: str = "campaign", tag: str = "note",
        max_tokens: int = 2000) -> Optional[str]:
    """One commentary call. Returns prose, or None if unavailable.

    `context` is the ONLY source the model may quote numbers from; it is also
    what the numeric guard checks against. `images` are figure paths (PNG).
    """
    key = _load_key()
    if not key:
        print("LLM unavailable: no ANTHROPIC_API_KEY found "
              "(project .env or LATBright .env). No commentary produced.")
        return None
    try:
        import anthropic
    except ImportError:
        print("LLM unavailable: `pip install anthropic` in this env.")
        return None

    blocks = [{"type": "text", "text": f"CONTEXT (the only source you may "
                                       f"quote numbers from):\n\n{context}"}]
    for p in images:
        if not os.path.exists(p):
            continue
        with open(p, "rb") as fh:
            blocks.append({"type": "image",
                           "source": {"type": "base64",
                                      "media_type": "image/png",
                                      "data": base64.standard_b64encode(
                                          fh.read()).decode()}})
    blocks.append({"type": "text", "text": prompt})

    client = anthropic.Anthropic(api_key=key)
    try:
        with client.messages.stream(
                model=MODEL,
                max_tokens=max_tokens,
                thinking={"type": "adaptive"},
                system=SYSTEM,
                messages=[{"role": "user", "content": blocks}]) as stream:
            msg = stream.get_final_message()
    except Exception as exc:                      # never fake a verdict
        print(f"LLM call failed ({type(exc).__name__}: {exc}). "
              "No commentary produced.")
        return None

    answer = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    unquoted = _unquoted_numbers(answer, context)

    out_dir = os.path.join(QUARANTINE, trig)
    os.makedirs(out_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    header = (f"<!-- AI-GENERATED COMMENTARY — NOT A MEASUREMENT -->\n"
              f"# {trig} — {tag}\n\n"
              f"*Model {MODEL}; generated {stamp}; commentary only. Numbers in\n"
              f"this file are quotations from the products listed in the\n"
              f"sidecar — never a new computation.*\n\n")
    if unquoted:
        header += ("> **GUARD FLAG — numeric tokens not found in the supplied\n"
                   "> context:** " + ", ".join(unquoted) +
                   ". Treat these as unverified and do not propagate them.\n\n")
    body = header + answer + "\n"
    open(os.path.join(out_dir, f"{tag}.md"), "w").write(body)
    json.dump({"model": MODEL, "utc": stamp, "tag": tag, "trigger": trig,
               "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
               "context_sha256": hashlib.sha256(context.encode()).hexdigest(),
               "images": list(images), "unquoted_numeric_tokens": unquoted,
               "usage": {"input": msg.usage.input_tokens,
                         "output": msg.usage.output_tokens},
               "role": "commentary_only__never_a_measurement"},
              open(os.path.join(out_dir, f"{tag}.json"), "w"), indent=1)
    if unquoted:
        print(f"[guard] {len(unquoted)} unquoted numeric token(s) flagged in "
              f"{tag}: {unquoted}")
    return body


# ---- the four commentary jobs the review notebook uses -------------------

def review_figure(png: str, contract: str, context: str, trig: str,
                  tag: str) -> Optional[str]:
    return ask("Inspect the attached figure against the contract above. Report: "
               "(a) does it show what its context claims; (b) any element that "
               "is missing, illegible, or contradicts the context; (c) whether "
               "a reader could be misled. Quote on-figure text you rely on.",
               context=f"CONTRACT:\n{contract}\n\nPRODUCT CONTEXT:\n{context}",
               images=[png], trig=trig, tag=tag)


def review_model_census(table_md: str, trig: str) -> Optional[str]:
    return ask("This is the per-bin all-model AIC census for one burst. Comment "
               "on: which preferences are decisive vs tie-level; whether any "
               "winner is a bound-railed or invalid fit; whether the pattern "
               "across bins is physically coherent or looks like optimizer "
               "noise. Do not restate the whole table.",
               context=table_md, trig=trig, tag="model_census_commentary")


def review_temporal(summary: str, trig: str) -> Optional[str]:
    return ask("These are the burst's temporal measurements with their estimator "
               "labels. Comment on internal consistency (do the estimators "
               "disagree beyond their quoted errors?), and on whether any value "
               "is quoted without the caveat its own sidecar records.",
               context=summary, trig=trig, tag="temporal_commentary")


def literature_check(ours: str, published: str, trig: str) -> Optional[str]:
    return ask("Compare our values with the published ones. For each: agree "
               "within errors / disagree / not comparable (state why). Where a "
               "definition differs (e.g. windowed vs catalogue duration), say "
               "so instead of calling it a disagreement.",
               context=f"OURS:\n{ours}\n\nPUBLISHED:\n{published}",
               trig=trig, tag="literature_commentary")

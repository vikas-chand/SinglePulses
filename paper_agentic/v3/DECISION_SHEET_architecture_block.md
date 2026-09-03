# DECISION SHEET — architecture block (§3 + §4 + §7) for the PI gate (decision 20: hybrid blocks)

**Date:** 2026-09-03 (early). **Block =** `paper_agentic/v3/sec3_harness.tex` (r4, ~2,770 words),
`sec4_lifecycle.tex` (r1, ~1,720 words), `sec7_objects.tex` (r1, ~1,010 words); figures F1 (delta, re-approval
needed), F2, F3 (= v2's fitting-step TikZ, unchanged), F5; table T1 (generated, `dev/build_t1_roster.py`).
Compiles in an aastex631 twocolumn wrapper: 0 errors, 0 overfull; the three sections + appendix table = 12 pages
with the appendix table taking 4 (the outline budgeted ~3 + ~2 + ~1 pp for the prose; prose lands at ~7 pp
because the three figures are full-width — trim is possible on request).

**Fresh-context numbers/status verifier:** IN FLIGHT at the time of writing; verdict appended below when it lands.

## 1. What you are approving (one word each, or "revise: …")
| # | item | your options |
|---|---|---|
| A | §3 r4 — the harness by job (loop, tools, context, state, boundaries), vocabulary paragraph, corrected authority table | approve / revise |
| B | §4 r1 — the eleven steps in ledger order, guides/sensors per step (F2), the fitting step (F3), fan-out and gates | approve / revise |
| C | §7 r1 — objects, links, actions, roles; "one reality" gap named once (F5) | approve / revise |
| D | F1 delta (two boxes reworded after Codex; verifier PASS-WITH-NITS at png 27361512) | re-approve / revise |
| E | vendor + versions: name the hosted harness (Claude Code) and the model identities in the reproducibility section, as T1 already names them and the provenance stamp records them. Recommendation: YES — the paper describes a harness; an unnamed, unversioned outer harness is the one reproducibility hole a referee will find first | yes / no / later |

## 2. The statements that carry weight (read these even if you skip the prose)
1. **Vocabulary (decision 21 applied):** the whole system = *the agent* (published usage: 48 "agent" vs 0
   "harness"/"scaffold" in 15 abstracts); *harness* = the machinery around the language model, two layers (hosted
   product + repository); *roles* and *subagents* inside. Your gloss survives as the closing sentence of the paragraph.
2. **Authority table (corrected):** the workflow AND THE ENGINE decide the fixed things, including the
   physical-validity flag and the validity-gated AIC ranking (code: `_fit_is_physical`, `select_best`); the AI audits,
   verifies sources, attributes mismatches, drafts lessons, escalates; the human gates. Stage-1 is "human arm / AI
   arm", not human-only. Two planes defined in one paragraph before the table.
3. **Status statements (decision 18):** DEPLOYED/PROPOSED only. The five PROPOSED roster rows are named once, in §3's
   last paragraph: queue manager + typed workflows; first-class action wrappers; report-conformance gate; queued
   boundary package (loop caps, spend ledger, hook points, pre-commit, sandbox); queued science guards. Everything else
   is described as it runs today; where a mechanism is procedural in the interactive session (skill reader, dispatcher,
   fresh-context verification, role separation) the text says "by protocol" once, not as a refrain.
4. **Counts** (working tree 2026-09-02, tracked code 4df6884; `\prov` only on these): 24 models (6+2+16); 14 states;
   11 workflow files specified; 27 guide files / 10 step skills; 3 hooks; 1 of 5 transitions covered by the dispatch
   hook; 44/49 roster rows deployed; 6 bursts with promotion receipts; 10 schemas; 106 bursts on the board; 13 object
   types drawn in F5, 5 of them with schemas.
5. **Incidents kept (§3.4):** the late-stamped step-3 approval and the byte-identical reinstatement of step 5 on the
   walkthrough burst — cited to its approvals record and the block-table hash. They illustrate the mechanism working
   in both directions (decision 18: "describe what worked").
6. **No claims (decision 19):** no sentence asserts that reliability is a property of the harness; §3–§4–§7 describe
   the design. The thesis line in the outline was rewritten accordingly.
7. **No blog citations (decision 17):** the five posts are gone from the text; §1 will cite published works from
   `notes/RELATED_WORK_candidates_20260903.md` once their PDFs are local.

## 3. What moves from v2 §3 (lines 202–504), and where — nothing is dropped
| v2 passage | destination |
|---|---|
| "The campaign loop" step descriptions (264–288) | §4.1 (re-ordered to the official ledger; step 8 = νFν panels) |
| P0 freeze + three-way attribution (290–301) | §6 (verification doctrine) — pointer in §4.3 |
| K-clean / freeze / production sweep (303–310) | §5 (steering loop) — pointer in §4.3; the "only the frozen sweep produces citable numbers" sentence kept in §4.3 |
| "Inside the fitting step" (312–340) + fig:fitstep | §4.2 verbatim in substance; figure kept as F3 |
| specialist definition (342–357) | §3.3 opening |
| fan-out + verifier duties + hash-bound verdicts (359–371) | §4.3 |
| domain instruments (390–404) | §3.2 |
| "Who decides what" table (406–435) | §3.5 (corrected) |
| "Two planes" (436–445) | §3.5 definition paragraph; mechanics → §6/§7 |
| "The doctrine" (447–462) | split: fit rules → §4.2; lessons-as-tests + hierarchy → §5; blind-first/primitive/fresh-context → §6; no-silent-approval → §3.5 |
| "The operating skeleton" (464–502) | states → §3.1; stamps/receipts/cascade → §3.4; hooks → §3.5; register + hierarchy → §5; failure taxonomy → §10 |

## 4. How the splice will happen on "approve"
One chng entry: v2 lines 202–504 replaced by `\input{v3/sec3_harness}`, `\input{v3/sec4_lifecycle}`, and — after
v2 §5 and §6 — `\input{v3/sec7_objects}`; `\input{v3/tab_T1_roster}` in an appendix `\section{Component roster}
\label{app:roster}`; preamble gains the `\ac` cell macro. Then pdflatex, undefined-reference count, Preview open
("once done open the paper"). v2 stays on disk as `agentic_grb_v2.tex`; the spliced file is `agentic_grb_v3.tex`.

## 5. Known nits carried (none blocking)
- F1: pre-existing 1-px touch of the "stamps" label on a dashed border (fix when the figure is next touched).
- §4 caption for F1 in §3 does not repeat the "10 of 11 skills written" detail; the prose carries it.
- The authority table is a float and may land a page after its paragraph in the final layout.

## 6. Full-document test build (scratch copy; v2 untouched; 2026-09-03 ~01:40)
`dev/paper_v3_splice.py --write --out <scratch>` + pdflatex/bibtex/pdflatex×2: **0 errors, 0 undefined references,
0 undefined citations, 0 overfull; 19 pages** (v2: 12). Page map: §3 p3, F1 p4, §4 p6, authority table p7, F2 p8,
F3 p9 (with §5 start), §6 + §7 p11, F5 p12, §8 p13, appendix T1 p16–19. The growth is the three full-width figures
and the 4-page roster table; the prose of the block is ~5.5 k words.
- Note for item D/E: F1's top box reads "THE MODEL: reasoning only (Claude session, Mode B) — no memory between
  calls, no ground truth" and its header "agent = model + harness". The equation is consistent with decision 21
  (the agent contains the harness); the box names Claude (item E) and states the bare-model limits absolutely (the
  prose now says "retains no project state between calls and observes nothing outside its context"). If E = yes,
  F1 stays; if E = no, the box loses "Claude session" and F1 re-gates.

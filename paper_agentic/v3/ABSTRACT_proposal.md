# Abstract proposal (chng[abstract]) — 2026-09-03, awaiting the PI's approved / revise / skip

PI: "abstract needs to be concise, and one the lines are they write for A&A (without giving titles)".
Flow = A&A structured abstract without headings: context → aims → methods → results → conclusions.
Decisions honoured: 19 (describe the design, no claims), 21 (the whole system = an agent; harness = its machinery).
Counts: only "106" (sample); the lesson count of v2 ("thirty-two") is v2-era and NOT reproduced here until a census.
Words: ~200 (was 423).

```latex
\begin{abstract}
Time-resolved spectroscopy of gamma-ray bursts (GRBs) rests on judgement
calls: which detectors to trust, where the background lies, where the burst
begins and ends, how finely to bin it in time, and which of two dozen
spectral models to adopt. We describe the design of an agent that makes
those calls for a campaign of 106 single-pulse \textit{Fermi}/GBM bursts,
with a human approving every step. The language model runs inside a
harness of deterministic tools, plain-language skill documents, state
derived from disk, and enforced boundaries; specialist roles read, produce,
and verify, and a producer never verifies its own work. Each burst is
analysed blind, compared with the published literature only after its own
numbers are frozen, and every mismatch is attributed and distilled into a
numbered lesson that ships with an executable test. We present the harness
component by component, the guides and sensors that act at each step, and
the object-and-action model that binds every product to its inputs by hash,
and we report what the walkthrough burst caught: engine defects fixed and
tested, blind predictions confirmed, one refuted. The trained artifact is
the skill library, readable by a student or by another AI system, and we
state plainly where the human gate still does the deciding. We release the
library, the engine, the tests, and the per-burst records.
\end{abstract}
```

## Domain-model referee runs (AbstractHelper engine B) — adjudicated 2026-09-03
Runs recorded in `~/Desktop/Projects/AbstractHelper/runs/` (model tag + digest, prompt sha, raw output).
| model | mode | what it said | adjudication |
|---|---|---|---|
| AstroSage-70B Q4 (before the 8 GB cap) | critique, brief only | flow mapped sentence by sentence (context s1, aims s3, methods s5–7, results s8, conclusions s10); "blind predictions confirmed, one refuted" flagged as a claim; jargon: Bayesian-block binning, SED panels; 220 words / 11 sentences dense; "omits the 106 bursts" | flow map CORRECT; the two jargon items CONFIRMED (define or drop in the abstract); "omits 106" REJECTED (sentence 3 states it); the claims flag is the brief's own caveat (carry only if §9 still says so) |
| AstroSage-8B Q4 (the permitted model) | rank current vs proposed, brief | proposed (B) ranked first: clearer, concise, no claims beyond the brief | agrees with the direction; reasoning thin |
| AstroSage-8B Q4 | critique, brief + paper sections | "lacks headings" (by design), "omits 106" (false), jargon list drawn from the PAPER BODY not the abstract ("gated workflow", "operating skeleton", "specialist roster" do not occur in the abstract) | REJECTED except the length remark; the 8B confuses the paper with the abstract when both are in context |
| generic llama3.1:8b (plumbing test) | critique | quoted three sentences that do not exist | REJECTED — the reason engine B is advisory |
**Verdict on engine B:** the 70B was a usable referee (sentence-indexed flow, one error in five findings); the 8B Q4 is
not reliable as a referee and its drafts are generic. Within the 8 GB budget the domain model's honest role is a second
opinion on register and jargon, never on facts. The composer (Claude) + the brief + the PI gate carry the abstract.
**Applied to the proposal (r2):** define the two jargon items at first use or drop them — "Bayesian-block binning" →
"adaptive time binning"; "SED panels" → "spectral-energy panels" (already the paper's phrasing elsewhere).

# Abstract proposal (chng[abstract]) — r5, 2026-09-03, awaiting the PI's approved / revise / skip

**r5 (13:20), PI on r4: "goes too much into like whole summary and started to describe all architecture, it should be brief
with A&A kind of guiding"** → six sentences in the A&A flow: context (the judgement calls) · aims (the design, and what it
caught) · methods (the harness in one sentence; blind-first + lessons in one) · results (106 bursts, 24-model menu,
reports recompute from disk; the first burst's catches) · conclusions (the skill library, released). The census list and
the "this paper describes" sentence of r4 are gone.

**r4 (13:10), in the shape of Schüssler et al. 2026 (arXiv:2608.23270, the PI's pointer: "look at their abstract"):** one
sentence on what is presented, one on how it works, one on what it produces, then the NUMBERS (their 1,775 Circulars /
25,827 of 25,880 decisions / 228 of 249 redshifts / 68,393 observations → our census: 106 bursts; 24-model menu; 49
components, 44 on disk, 5 proposed; 27 guides, 10 roles, 3 hooks, 10 schemas, 49 register rows, 134 tests; 433 of 436
Stage-1 rows human-approved; six of eleven steps approved on the walkthrough burst), then the release, then a closing
"this paper describes …" sentence listing the sections. Every number re-verified on disk 2026-09-03 13:05 (the roster
44/5 and the register 49 by the figure gates today). Decision 19 kept: these are census counts, not claims.

**r3 (12:55):** same facts as r1; register tuned against the retrieval corpus of 2,399 published abstracts (ADS; A&A/ApJ/ApJS/
MNRAS GRB spectroscopy, astronomy LLM-agent papers, pipeline-provenance papers). Corpus medians: 237 words, 9 sentences,
25 words/sentence, 2.0 clause hinges/100 words, 7.7 passives/1k. r1 ran 31 words/sentence and 5.5 hinges; r3 shortens the
sentences and turns the passives into agent-first verbs (the agent analyses, freezes, attributes).

PI: "abstract needs to be concise, and one the lines are they write for A&A (without giving titles)".
Flow = A&A structured abstract without headings: context → aims → methods → results → conclusions.
Decisions honoured: 19 (describe the design, no claims), 21 (the whole system = an agent; harness = its machinery).
Counts: only "106" (sample); the lesson count of v2 ("thirty-two") is v2-era and NOT reproduced here until a census.
Words: ~200 (was 423).

```latex
\begin{abstract}
Time-resolved spectroscopy of gamma-ray bursts (GRBs) rests on judgement
calls: which detectors to trust, where the background lies, where the
burst begins and ends, how finely to bin it, and which of two dozen
spectral models to adopt. We describe the design of an agent that makes
those calls under human approval, and what it caught on its first burst.
A language model runs inside a harness of deterministic tools,
plain-language skill documents, state derived from disk, and enforced
boundaries; a producer never verifies its own work. The agent analyses
each burst blind, freezes its numbers before it reads the published
literature, and turns every mismatch into a numbered lesson with an
executable test. Applied to a campaign of 106 single-pulse
\textit{Fermi}/GBM bursts, the design fits a 24-model menu to every time
bin and assembles reports whose numbers recompute from the products on
disk; on the first burst walked end to end it caught engine defects, now
fixed and tested, and confirmed blind predictions while refuting one.
The trained artifact is the skill library, readable by a student or by
another AI system, which we release with the engine, the tests, and the
per-burst records.
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

# DRAFT — review request to ChatGPT for paper v3 (architecture block spliced) — for the PI to edit before sending

**Status:** READY TO SEND (2026-09-03 ~16:30). PI: "once you are done I think we should get a review from chatGPT and start
writing and finalzing our manuscript". The PDF to attach is paper_agentic/agentic_grb_v3.pdf at commit 06d6171 or later
(19 pages; §3/§4/§7 new; four figures in the colour + style grammar; abstract PROVISIONAL, decision 23). Standing rule for the reply (memory: absorb ChatGPT packages critically): advisory, not spec — every
factual or bibliographic claim it makes gets verified against the PDF/ADS before anything changes; anything it
proposes as a root CLAUDE.md/AGENTS.md is rejected on sight.

## What to attach
- `paper_agentic/agentic_grb_v3.pdf` (the spliced draft; §3, §4, §7 new; §1, §5, §6, §8–§11 still v2 text; the abstract is a
  provisional placeholder to be rewritten last — do not review it for polish).
- Optionally `paper_agentic/T1_component_roster_DRAFT.md` (the source of the appendix table, with the evidence column
  the PDF omits).

## The request (paste as the prompt)

You are refereeing a manuscript for an AAS journal (ApJ/ApJS style). The authors are gamma-ray-burst astronomers who
built and ran an AI-agent system for time-resolved Fermi/GBM spectroscopy over a 106-burst sample, with a human
approving every step. The manuscript is a design description: it says what the system contains, how each component
works, what it caught on one walkthrough burst, and what is specified but not built. It does not claim that the
design is the reason for any result, and it deliberately cites no blog posts.

Sections 3 (the harness, component by component), 4 (guides and sensors along the burst) and 7 (the object-and-action
model) are new and are what we want reviewed most closely; the abstract is a provisional placeholder (skip it); sections 1, 5, 6, 8–11 are older text that will be revised
next and may contradict the new sections — flag contradictions, do not review the old text for style.

Please answer in numbered findings, each with the section and page it refers to, a severity (blocking / should-fix /
nit), and the exact sentence you object to where one exists.

1. Legibility for the audience. Could a first-year PhD student in high-energy astrophysics, with no software
   background, follow §3–§4–§7 and explain the system back? Where does the text assume engineering knowledge it has
   not supplied? Which terms need a definition earlier than they get one?
2. Overclaims. Every sentence that says or implies something is enforced, automatic, universal, or complete —
   quote it, and say what evidence a referee would demand to accept it. The authors intend every status to be one of
   deployed (exists on disk and runs) or proposed (specified, not built).
3. The figures and the table. Do Figures 1, 2, 3 and 4 (the anatomy, the lifecycle with guides and sensors, the
   fitting step, the object-and-action model) each earn their full-width page? Is the colour grammar (blue = code,
   green = model role, white = documents, amber = human, dashed = proposed) understood from the captions alone? Is the appendix roster table useful to a
   reader or only to the authors? What would you cut or merge?
4. The authority table (§3). Is the split "the workflow and the engine decide / the AI does / the human decides"
   clear and complete? Is anything in the wrong column?
5. Structure. The paper now runs 19 pages against 12 before; §3 alone is ~2,800 words. Where would you cut, and what
   would you move to an appendix or a companion repository document, without losing the design description?
6. The referee's three strongest objections to publishing a design-description paper of this kind in an astronomy
   journal, and what the authors could add — from material they plausibly already have (a walkthrough burst, a
   verification ledger, a requirements register, an evaluation battery) — to answer each.
7. Related work. Name published works (journal or arXiv, with the identifier) that a referee would expect the
   introduction to cite for: LLM agents in astronomy; LLM agents for scientific workflows or provenance; the
   limits of model self-verification; agent evaluation. Mark anything you are not certain exists as UNCERTAIN.
   Do not invent identifiers; we verify every one against ADS/arXiv before use.

Do not rewrite the paper. Do not propose new sections. Where you suggest a rewording, quote the original and give the
replacement.

## After the reply lands (our side)
1. Save the reply verbatim to `notes/CHATGPT_REVIEW_paper_v3_<date>.md`.
2. Adjudicate finding by finding at the primitive (as with the Codex review): CONFIRMED / MODIFIED / REJECTED, with
   file:line; write `notes/CHATGPT_ADJUDICATION_paper_v3_<date>.md`.
3. Every suggested citation: ADS lookup → PDF local → quoted sentence, or it does not enter the tex.
4. Findings that survive become a decision sheet for the PI, not direct edits.

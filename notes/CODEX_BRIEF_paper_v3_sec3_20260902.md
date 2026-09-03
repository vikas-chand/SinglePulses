# CODEX BRIEF — paper v3, §3 draft and spine (SUPERVISOR hat, full context)

**Hat:** A15 SUPERVISOR (auditor + brainstormer), per dev/ai_guides/RefereeLoop.md. This is a
draft in progress; the blind referee panel (T0/T1/T2) is reserved for the finished v3 and will
run on a different product version. PI-triggered 2026-09-02 ("how about getting an opinion of
codex"). One shot. Paid quota.

**Repository:** /Users/salim/Desktop/Projects/SingleRest/Two_Breaks, branch memory-guard,
HEAD 7d15c20 (or later; everything cited below is committed unless marked).

## Run frame (codex-review skill contract)
- Run mode: GPT-5.6, Sol, Ultra. Working directory: /Users/salim/Desktop/Projects/SingleRest/Two_Breaks.
- READ-ONLY except your report. Write only notes/CODEX_REVIEW_paper_v3_sec3_20260902.md.
- Artefacts of record (absolute paths; ignore any other copy on disk):
  - /Users/salim/Desktop/Projects/SingleRest/Two_Breaks/paper_agentic/v3/sec3_harness.tex (the DRAFT §3)
  - /Users/salim/Desktop/Projects/SingleRest/Two_Breaks/paper_agentic/agentic_grb_v2.tex (the standing v2; lines 202–504 are what §3-v3 would replace)
  - /Users/salim/Desktop/Projects/SingleRest/Two_Breaks/paper_agentic/REWRITE_OUTLINE_v3.md
  - /Users/salim/Desktop/Projects/SingleRest/Two_Breaks/paper_agentic/T1_component_roster_DRAFT.md and .../paper_agentic/v3/tab_T1_roster.tex
  - /Users/salim/Desktop/Projects/SingleRest/Two_Breaks/paper_agentic/figures/fig_F{1,2,4,5}_*.pdf
  - /Users/salim/Desktop/Projects/SingleRest/Two_Breaks/notes/HARNESS_COMPARISON_20260902.md
- Environment: /Users/salim/anaconda3/bin/python3 has numpy/pandas/astropy/scipy/pymupdf; pdflatex present. No pipeline producer may be run; nothing under results/ needs opening for this brief except results/campaign/agentfigs/VISION_QC.md (figure verdicts).
- Deliberate conventions that could look like defects: `\prov` marks a walkthrough-era count bound to a commit (not a defect); the five harness posts are cited as URL footnotes by design (question 4 asks whether that is right); T1 is GENERATED from the markdown roster (do not "fix" the .tex by hand); v2 stays untouched until the PI approves each change entry (the paperedit protocol).
- Previous Codex reports touching this scope: notes/CODEX_REVIEW_skillgraph_20260901.md and _r2 (action-indexed rules; their open items — action registry, queue manager, finalize barrier — are NOT in this brief's scope; do not re-derive them). No prior Codex review of the paper's architecture section exists.
- Recompute from the products; do not trust any printed value, including the counts pinned in this brief.
- Check against sources outside our own derived files where possible (the five posts' own text; the engine source; the agent files), never against a file that merely restates them.

## Output contract
```
VERDICT — SIGN OFF (the spine and §3-v3 are sound to proceed) or DO NOT SIGN OFF (state plainly what must change first)
Per question 1–6: your answer, with file:line for every claim
OVERCLAIMS (question 2): each sentence quoted, with the evidence that contradicts or fails to support it, and the exact rewording
DISCREPANCIES: each with the exact fix
COULD NOT VERIFY: what and why
```
Finally, your own independent judgement: anything wrong or fragile that this brief did not ask about.

## What to read (in this order; nothing else is needed)
1. `paper_agentic/REWRITE_OUTLINE_v3.md` — the approved outline (PI decisions 11, 15, 16 in its
   decision log): spine = the harness component by component; eight figures in the grammar of
   five engineering posts on agent harnesses; a component roster T1.
2. `paper_agentic/v3/sec3_harness.tex` — the DRAFT §3 (uncommitted fragment, ~1,500 words),
   proposed to replace v2 §3 (`paper_agentic/agentic_grb_v2.tex` lines 202–504). v2 stays on
   disk unchanged for comparison.
3. `paper_agentic/T1_component_roster_DRAFT.md` — the approved roster (49 rows; four
   fresh-context verification rounds; commit 427fdc5) and `paper_agentic/v3/tab_T1_roster.tex`
   (generated from it).
4. `paper_agentic/figures/fig_F1_harness_anatomy.pdf` (+ F2, F4, F5 in the same directory) —
   gated diagrams; verdicts and sha256 in `results/campaign/agentfigs/VISION_QC.md` (last
   section).
5. `notes/HARNESS_COMPARISON_20260902.md` — the five-source comparison the section rests on
   (§19 needs, §20 strengths). The five sources: Bowne-Anderson (Substack, "How to build an
   effective agent harness"), Böckeler (martinfowler.com, "Harness engineering for coding agent
   users", 2026-04-02), Palantir Ontology page + Foundry docs, PuppyGraph blog "Agent harness"
   (2026-07-01), LangChain blog "How to build a custom agent harness" (2026-06-03).

## Facts pinned for you (recompute if you doubt; do not take from the draft)
- 10 agent files in `.claude/agents/`; 9 carry tools Read/Grep/Glob/Bash, distiller adds Edit/Write.
- 3 PreToolUse hooks in `.claude/settings.json`; the dispatch hook regex covers 1 of 5 pipeline
  transitions (register NR-30) and matches command TEXT (FreshSessionBoot.md:166–169).
- 27 skill files in `dev/ai_guides/`; register 49 NR rows + 11 unnumbered (NR-11 retired) at
  `dev/ai_guides/AgentArchitecture.md` (header :132); 10 schemas in `dev/schemas/`; 134 tests in
  11 files; 106 burst_state files; state machine S0–S12 + SX (AgentSkeleton.md §1); 11 `wf-*`
  workflows specified (§3) and absent on disk; `dev/queue_manager.py` absent.
- Engine: 24 models (`scripts/10_spectral_fit_burst.py` spec tables 6+2+16).
- The census commit for the draft's `\prov` counts: 4df6884.

## Questions (answer in order; be adversarial; name file:line for every claim you make)
1. **Is the spine right?** For a paper whose audience is GRB astronomers (ApJ/ApJS style, aastex631,
   first-year-PhD readability rule), does "the harness, component by component" carry the
   argument better than v2's "The Agentic Workflow"? What is lost from v2 §3 that §3-v3 must keep,
   and where do v2's "doctrine", "two planes", and "operating skeleton" paragraphs belong
   (the draft says §5, §6, §3.4/§5)?
2. **Overclaims.** Read §3-v3 sentence by sentence against the roster and the register. List every
   sentence that claims more than the evidence on disk supports, or describes as built something
   marked PROPOSED. Include the counts marked `\prov`.
3. **Vocabulary.** The draft uses: model, harness, agent, subagent, Mode B, guide, sensor,
   computational/inferential, action, receipt, stamp. Is "agent = model + harness" (LangChain's
   phrase, PuppyGraph's definition) the right frame for an astronomy paper, and is the nesting
   (a product harness under our repository harness; subagents inside the roster) explained where
   a physicist would need it? Propose replacements only where a term will mislead.
4. **Citing blog posts.** The outline cites the five posts as URL footnotes, not as references.
   For an AAS journal, is that acceptable, and is there any peer-reviewed literature on agent
   harnesses / LLM-agent architectures for scientific pipelines that the paper should cite
   instead or in addition? Name only works you can identify with a DOI or arXiv id; mark anything
   you are unsure of as UNVERIFIED (the session will verify every id against ADS/arXiv before use).
5. **Referee's attack.** What will a skeptical astronomer referee say about §3 as drafted, and
   about the paper's claim that reliability over a long scientific run is a property of the
   harness? Give the three strongest objections and, for each, what evidence the paper already has
   on disk (or does not) to answer it.
6. **Process.** The PI's paperedit protocol gates each section on his approval; six sections
   remain. Independent judgement: is per-section review or draft-all-then-review the better use of
   his time for THIS rewrite, given the outline is already approved? One paragraph.

Write your review to `notes/CODEX_REVIEW_paper_v3_sec3_20260902.md`. Modify no other file. Do
not run any pipeline producer. Do not read `results/sweep106/` or burst products; this brief is
about the paper's architecture section only.

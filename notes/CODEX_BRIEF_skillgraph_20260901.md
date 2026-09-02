# CODEX BRIEF — should the GRBs Agent get a SKILL-GRAPH actor?

You are an INDEPENDENT ADVERSARIAL REVIEWER on a design question. Advisory only; every
finding will be adjudicated at the primitive before action. Be blunt. If the proposal is
wrong, say so.

## The question (from the PI, verbatim)
"do you think we need to add an agent that makes sure that some technical skills or all the
rules are always checked before the first step, specially if we can make knowledge graph or
graph of the skills and one is picked up faster and we don't have to compare all, all the
time if they are applied but ones attached to that node and node to node be checked before
proceeding/finalizing anything?"

## Context you need (facts, verifiable in this repo — do not take them on trust)
This is an AI agent that runs a 13-step gated pipeline over 106 gamma-ray bursts, one burst
at a time, with a human PI approving every step. Read these, they are the design:
- `dev/ai_guides/AgentArchitecture.md` — principles P1-P9 and a 39-row requirements register
  (NR-1..NR-40). NOTE its FIRST COLUMN ("where"): `every figure delivery`, `every numeric
  artifact`, `each step opening`, `any code port`, `catalog writes`, `any MC product`. That
  column is an edge list written as prose.
- `dev/ai_guides/AgentRoster.md` §A1 — the SKILL-READER actor. Its stated position is
  "re-invoked at every step open". Its OWN recorded honest limits include: "checklist
  compliance unverified downstream" and "end-to-end reading is expensive every step ... a
  cheaper repeat-tier is possible".
- `dev/ai_guides/SpectralFitting.md` (28 L-series lessons), `Temporal.md` (5),
  `LiteratureHarvest.md` (11 traps), `BurstWalkthrough.md`, `Binning.md`, `ReportSpec.md`.
- Total: ~97 numbered rules across ~4,937 lines in `dev/ai_guides/`.

## The measured evidence that provoked the question
In ONE session (2026-08-30/09-01) the operating agent walked burst bn110920546 through steps
0b,0,1,2,3,4,5 and broke FIVE rules that were in its context the whole time:
1. **G1** (`BurstWalkthrough.md`): per-burst filenames must carry the trigger id. Seven
   notebooks shipped without it.
2. **Stamp-on-answer**: told the PI step 4 was approved, never wrote the stamp; it lived only
   in chat for ~7 h, found mechanically by the NR-19 cascade.
3-4. **PI ruling 3** (`SpectralFitting.md`): "never print either word without its reference" —
   mislabelled TRACKED (dAIC>6 vs runner-up) as DECISIVE (dAIC>=10 vs best simpler ancestor)
   TWICE, in numbers presented to the PI.
5. **Counterfactual quoted as outcome** in a provenance record (`decision.json`): quoted the
   chi2 improvement of REMOVING dropout bins as if it were the effect of the cut actually made.
Every one of those rules is in the skill file for the step the agent was in.
In the SAME session, every CODE-layer guard held: the P9 dispatch hook (3x), the no-ship
VISION_QC hook, `live_report.py` refusing a PRESENTED stamp without on-disk evidence, and the
NR-19 cascade. The agent invoked the skill-reader ONCE (session open) across seven steps.
The project's own principle P8 predicts exactly this: "prose instructions to the ACTOR are the
weakest layer and will be ignored under momentum", enforcement order code > hook > artifact >
agent > prose.

## The proposal on the table (critique this, do not just improve it)
- NODES: pipeline steps (0b..9), artifact classes (figure, catalog row, fit table, MC product,
  code port, deliverable), quantities (T90, lag, MVT, dAIC, kT, significance).
- EDGES: each lesson/register row gets machine-readable front-matter naming its nodes; the
  graph is DERIVED from that front-matter, never hand-maintained.
- USE 1 (retrieval): at step open, query the graph for the binding subset instead of reading
  ~4,937 lines end-to-end.
- USE 2 (the part believed more valuable): at step FINALIZE, every rule attached to that
  step's nodes must be discharged or explicitly waived with a recorded reason.
- Staging proposed: front-matter tags now (cheap, additive, useful even if the agent is never
  built); graph + finalize-gate at the freeze, validated by replaying the five failures above —
  if it does not catch all five it is not finished.

## Standing constraints you must respect in your answer
- An external review already cautioned this project: BUILD THE QUEUE MANAGER BEFORE ADDING
  ACTORS. `dev/queue_manager.py` still does not exist. A19 (truth-grounding) is already queued
  as "the LAST actor admitted before freeze". This proposal would be another actor.
- The PI's correction to the operating agent, which you should take seriously: the rules are
  SKILLS, and a human does hold them. "Too many rules" is not accepted as an excuse.
- Contracts change only by the PI's quoted words. You are advising, not legislating.

## Output contract — answer these, in this order, and nothing else
1. VERDICT: is a skill-graph actor NEEDED, or is this solving the wrong problem? If the wrong
   problem, name the right one.
2. Which half is more valuable — retrieval, or the finalize-time compliance gate — and why.
3. The strongest ARGUMENT AGAINST building it. Specifically: does a derived graph move the
   failure mode from "didn't read" to "nobody drew the edge", and is that worse because it is
   invisible? How would you detect a missing edge?
4. Is the node taxonomy above right? What is missing or wrong in it?
5. SEQUENCING: given the queue manager does not exist and the caution above, what should be
   built first, and what should NOT be built at all?
6. Anything a cheaper mechanism would achieve better (e.g. lint rules, a pre-finalize
   checklist in code, per-step contract tests) — be concrete.
7. INDEPENDENT JUDGEMENT: what is the operating agent, or the PI, most likely getting wrong
   about this that neither has asked you about?

Write your answer to `notes/CODEX_REVIEW_skillgraph_20260901.md`. Do not modify any other file.

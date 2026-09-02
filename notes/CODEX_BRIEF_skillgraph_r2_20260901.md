# CODEX BRIEF ROUND 2 — ACTION-INDEXED skills, not step-indexed

You reviewed this yesterday: `notes/CODEX_REVIEW_skillgraph_20260901.md`. **Do not repeat or
re-litigate round 1.** Its conclusions are ACCEPTED and are now premises here:
- no new SKILL-GRAPH actor; the real problem is unverified action becoming state;
- the finalize-time compliance gate matters more than retrieval;
- discharge must be evidence (test result / hash / independent verdict / recorded human
  waiver), never the operating agent ticking a box — otherwise it is self-approval renamed;
- do not front-load mass tagging before rule IDs, authority model and coverage lint exist;
- queue manager first; A19 stays the last actor before freeze;
- replaying only the five known failures is overfitting.

**The proposal has CHANGED.** Evaluate the NEW one.

## The PI's refined framing, VERBATIM
"suppose me as human don't check against every skill but when I am going to name a result
product I know I need to get a trigger ID attached to it to distinguish it from other events,
so there is something that when a file is saved what is being done, when a file is created
what is being done and so one so I have actions and I have skills specific to actions so every
step has kind of entities with I think an Agent what does it do and the semantic knoweledge of
what it is doing to do and what skills there should be checked, so it is kind of graph or I
don't know graph RAG etc"

The claim: the routing key is the **ACTION (verb)**, not the pipeline step. A human does not
scan 97 rules; the act of *naming a product* summons the trigger-ID rule. Rules attach to
verbs. Note this converges with your own round-1 sentence: "the graph query should start from
the attempted transition and concrete artifacts/actions, then evaluate predicates. Otherwise
cross-cutting rules will be missed precisely because they are not owned by one step."

## The operating agent's enumeration (critique it; it is certainly incomplete)
14 verbs, 46 rule-attachments, assembled from one session's reading of `dev/ai_guides/`:

| verb | attached rules |
|---|---|
| name / save a per-burst product | G1 trigger-in-filename |
| write a row into a committed catalog | NR-4 admission gate; failure-transparency screens; NR-22 hash currency; NR-31 stale-column guard |
| write an approval / presentation stamp | no fabricated approvals; identity required; evidence required; stamp-on-answer; NR-19 cascade |
| print a model-preference word | PI ruling 3 (name the reference); NR-3 tie-reporter; R3 tie language; tie-adoption by simplicity |
| quote a temporal number | estimator label; L26 lag convention; L32 MVT precedence; L33 catalog T90 not truth; NR-31 rewalked_triggers |
| quote a duration (T90) | L29 windowed lower limit; L31 union of truncation flags |
| deliver a figure | FigureVisionQC S-items; no-ship hook; NR-5 pixel collision; producer never verifies |
| produce a stochastic result | NR-2 seed auditor; seed recorded AND honored; PYTHONHASHSEED |
| port code from another project | A12 port-verifier; L26 copy CODE not docstring |
| assemble a deliverable | R1..R5; R3a claim typing |
| amend a Stage-1 window | provenance + PI words verbatim; NR-19 cascade; backup before mutate; surgical verification |
| claim a component is required | boundary calibration (LRT not chi2); NR-25/A19 null+injection; gate pairing; L28 edge-constrained |
| start a root-cause or redo | A13 prior-art-reader first |
| close an incident | A14 distiller, same session, correct layer |

The operating agent's reading: **14 verbs is a TABLE, not a graph** — the retrieval problem
largely evaporates because each list is short enough to hold; what remains is making the check
FIRE AT THE VERB rather than depending on recall. It also observes that all five of its
failures were verb-indexed rules (naming, stamping, printing a preference word) missed while
it was indexing on "which step am I in".

## Answer these, in order, and nothing else
1. Does action-indexing DISSOLVE your round-1 missing-edge objection, or merely relocate it?
   Be precise: a missing rule→step edge is one of ~97x10; a missing VERB is one of ~14. Is the
   smaller, enumerable key genuinely safer, or is "which verb am I performing" the new
   unreliable judgement?
2. **How do you detect a MISSING VERB?** This is the new silent failure. Give a concrete
   detection method, not a principle.
3. Is the 14-verb list right? Name verbs that are MISSING, verbs that are actually two verbs,
   and any that are not verbs at all. Ground it in this repo's actual operations.
4. Is "table, not graph" correct — or does something in this domain genuinely need edges
   (e.g. rules that fire only on verb+context combinations, or verb sequences)?
5. Which verbs are mechanisable AT THE ACTION BOUNDARY (a hook/guard fires when the operation
   happens), which need an independent agent, and which are irreducibly human? Be concrete
   per verb.
6. Does this change your round-1 SEQUENCING at all? Specifically: is a verb→rule table cheap
   enough to build BEFORE the queue manager, or does it inherit the same "nothing makes it
   fire" problem and therefore wait?
7. INDEPENDENT JUDGEMENT: what is wrong with the action-indexed framing that neither the PI
   nor the operating agent has asked about?

Write to `notes/CODEX_REVIEW_skillgraph_r2_20260901.md`. Modify no other file.

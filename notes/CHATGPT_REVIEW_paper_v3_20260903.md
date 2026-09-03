# ChatGPT referee report — paper v3 (agentic_grb_v3.pdf, 23 pp, commit ba42046)

**Received 2026-09-03. Recommendation: MAJOR REVISION before submission.** Scope as briefed: §§3–7 and §10 read as new
material; §§1, 8, 9, 11 checked only for contradictions; the provisional abstract not reviewed. Full text of the report
is in this session's transcript (`~/.claude/projects/-Users-salim-Desktop-Projects-SingleRest-Two-Breaks/c864d34c-*.jsonl`);
this file captures every finding with its severity, the sentence objected to, and the replacement offered, which is the
actionable content. Adjudication (what survives checking at the primitive) is in
`notes/CHATGPT_ADJUDICATION_paper_v3_20260903.md`.

## The referee's summary judgement
> "There is a potentially strong and distinctive paper here. Its best contribution is not the general claim that an LLM
> can operate a GRB pipeline. It is the attempt to make model judgement subordinate to deterministic scientific tools,
> explicit authority boundaries, content-addressed evidence, independent verification channels, and an incident-to-test
> learning process. The independence-at-the-primitive doctrine in §6.2 and the object-and-action model in §7 are
> particularly good."

Four stated problems: (1) "deployed", "enforced", "blind", "independent", "learning" used more strongly than the
implementation permits; (2) the 24-model decision process is not calibrated against synthetic truth; (3) central claims
conflict across the new sections, the roster, the old introduction and the old conclusion; (4) too much
repository-internal vocabulary before an astronomy reader gets a stable conceptual map.

Closing paragraph, verbatim:
> "The present weaknesses arise mainly because the paper sometimes converts a **protocol requirement** into a **deployed
> guarantee**, a **lesson-accrual history** into a **learning curve**, a **separate fresh context** into an **independent
> reviewer**, and a **prospectively recorded comparison** into a **blind analysis**."

## Findings (39). Severity as given: B = blocking, S = should-fix.

| # | where | sev | objection (quoted) | replacement offered |
|---|---|---|---|---|
| 1 | §1 vs §3.5/T1 | B | "an AI exercises agency … which of twenty-four spectral models wins a gated comparison, whether a fit is valid or sits on a parameter rail" | "the AI audits and interprets the engine's validity-gated model comparisons … it does not compute fit validity or determine the numerical ranking" |
| 2 | §3.5, §4.1, F5 | B | "The human decides everything consequential" vs "decided by a human … or by a vision-capable role" | separate proposer / accepter / gate-approver; show the stamp schemas; if one identity field, call it a provenance gap; T1 gains "proposes Stage-1 selections in the AI arm" |
| 3 | §3.1, §3.5, §5.1, App. A | B | "DEPLOYED = a file or product exists" used as proof the mechanism operates | four evidence levels: specified / artifact implemented / exercised in a recorded run / mechanically enforced |
| 4 | §3.5, §4.3 | B | the universals: "never verifies", "Every figure passes", "Every printed number is recomputed", "must rerun bit-identically", "No row … unscreened", "Nothing is re-derived", "Every incident is closed … same session", "A verdict is bound to a content hash" | "the protocol requires" for procedure; "enforces" only for code paths with measured coverage; example rewrite given for the no-ship hook |
| 5 | §3.1 vs App. A | B | roster: "Derives every burst's state from evidence on disk" vs §3.1's "does not yet implement every declared state" | roster row: "Derives the subset of currently implemented burst states … unimplemented states and unverified currency are reported explicitly" |
| 6 | §3.2, §3.4, App. A | B | roster: "Binds every product to its inputs and generator by hash" | name the covered product classes with a count ("six promoted fit tables and their receipts") |
| 7 | §3.2 vs App. A | S | roster: "refusing any panel that disagrees with the stored fit" | paper-grade path refuses; legacy and montage paths expose the mismatch |
| 8 | §4.2, App. A | B | the 24-model selection is described but never calibrated | injection/recovery battery: false extra-component rate under single-component truth, recovery by fluence regime, rail and invalid rates, tie frequency, detector/background dependence, before/after the validity guards |
| 9 | §4.2 | S | "converted to an evidence ratio e^{ΔAIC/2} and graded" | define ΔAIC's sign and comparator; call "strong"/"decisive" prespecified descriptive thresholds, not calibrated probabilities; cite the threshold source |
| 10 | §4.2 | S | "conditioning inclusion on significance manufactures spurious detections" | "avoiding selection on an upward significance fluctuation" (or cite/simulate) |
| 11 | §1, §5, F4, App. A | B | three incompatible statements: every lesson has a test / some are prose only / only invariant-shaped lessons become tests | report the lesson inventory by enforcement class and say which classes count toward convergence: "Every lesson is recorded with provenance and an explicit enforcement class; lessons that admit a mechanical invariant also enter the regression suite" |
| 12 | §3.1, §4.1, §6.1 | B | "blind-first" while the same session retains context and the harvest precedes fitting | either show the information barrier (sealed predictions, fresh-context manifest, timestamps, replayable trace) or rename it "prospectively frozen comparison" |
| 13 | §5, F4–F5 | B | "a learning curve … whose flattening is the campaign's stopping criterion" | rename to walkthrough lesson-accrual curve; label the axis "cumulative lessons attributed to walked bursts"; state the counting rule; set K and the clean-pass eligibility; add a performance quantity (defects per completed step, gate-correction rate) |
| 14 | §5 | S | "training of the fifth kind carrying the fourth kind's essential ingredient"; "properties that gradient methods cannot offer" | "We revise the harness rather than the model weights, using mechanically checkable regression conditions wherever the lesson admits one"; advantages of representation, not impossibility results |
| 15 | §5.2 | S | "regime coverage, not burst count, is what a training sample must supply" | "burst count alone is an inadequate measure of curriculum coverage" |
| 16 | §5.3, §6.2–6.3 | B | "two independent agent passes"; "Four reviewer channels examined disjoint evidence primitives" | "two separate fresh-context agent passes"; "different assigned evidence views; independence claimed only where load-bearing primitives were disjoint"; add a primitive-sharing matrix for the four-channel experiment |
| 17 | §5, §10.4 | B | "executed by different vendors' agents", "transfers across model families", "survives model upgrades" | state as design hypotheses; the cross-vendor gate-by-gate replay is the test and is pending |
| 18 | §8 vs §10.4 | B | "so that differences isolate the model rather than the prompt" | same library ≠ isolated model effect unless scaffold, compaction, prompts, tools, retries are held fixed; record scaffold variables; repeat trials |
| 19 | §7 vs §3.4 | S | "validates every instance on disk against its schema" | "every covered instance … with four frozen pre-contract records in the exception ledger" |
| 20 | §7, App. A | B | "Four are first-class on disk today" vs the roster's PROPOSED first-class actions | "four verbs leave domain-specific records; the uniform intent–preflight–commit–receipt wrapper is not implemented; two verbs partially instantiate it" |
| 21 | §10.1 | S | "Every mode … converted into doctrine" while two countermeasures are proposed | say which remain incomplete; support "none was caught by the failing agent" from the incident ledger |
| 22 | §10.3, T4 | B | "present here, described in none of them" — a negative novelty claim | name and cite the five accounts, state the comparison method, give a source-by-feature matrix, distinguish "not discussed" from "not implemented"; ALSO: the brief said no blog posts are cited while the PDF cites Anthropic's "Building Effective AI Agents" |
| 23 | §10.4, App. B | S | "Both are released" with a pending Zenodo DOI | "will be released at the archived commit", or give repository, commit, licence, archive status |
| 24 | §3.5 vs §9 | S | "§9 reports that count with its denominator" — §9 does not | add the override count with a denominator of eligible proposals, or drop the forward reference |
| 25 | §11 vs §3.1/§5 | B | "thirty-two durable lessons"; "runs as written in a fresh session"; "walks bursts end to end" | conclusion must distinguish total lessons, lessons credited to walked bursts, mechanically tested lessons, and the number of steps completed in the fresh-session arm (seven of eleven) |
| 26 | §3.5, §5.1, T2/T4 | S | two different 49-row universes (component roster, requirements register) with reused status words | name each whenever a count appears; explain that a component can exist while its hardening requirement is proposed |
| 27 | §§3–4, §7 | S | too much repository vocabulary before a stable map | one plain-language clause at first use for ~22 terms (hosted product, Mode B, compaction, fresh context, tool grant, hook, dispatch plan, working tree, state board, content hash, sidecar, promotion receipt, schema, typed state, fail closed, parameter rail, count coordinates, simpler ancestor, promotion/quarantine, invalidation cascade, one reality, read-as-approval) |
| 28 | §§3–7, figures | S | implementation labels (A7, A10, A17, NR-44, scripts/41c, Mode B, Codex) in the narrative | scientific role names in text and figures; keep identifiers in the appendix/machine-readable mapping. Two repetitions to delete |
| 29 | F1, F2 | S | both earn their space; too dense; "no memory between calls" contradicts the text's in-session compaction | strip file-level labels from F1; in F2 keep the ledger, gates and one guide/sensor per stage; add a redundant non-colour channel (C/I/H markers) |
| 30 | F3, F4 | S | F3 is the weakest figure: it repeats the surrounding text | remove F3 or merge as an inset, unless it becomes a real decision tree; F4 stays, with "Codex" → "external auditor" and "ONE layer is chosen" → "the strongest enforcement layer is chosen" |
| 31 | F7 (learning curve) | B | the nine-burst splice is correct and the old contradiction is gone, but it is not evidence of learning without a performance ordinate | rename to walkthrough-attributed lesson accrual; add a prospectively measured error quantity; describe flattening as a proposed stopping rule |
| 32 | F5, F8 | S | F5 is probably the strongest architecture figure; F8 earns its space | F5: separate selector / approver / recorder, and state schema coverage; F8: say what the three flagged tables mean (stale, new defects, expected rails, or unresolved failures) |
| 33 | T1 (authority) | S | "decides" does too much work; provenance stamping is not a decision; the AI column omits Stage-1 proposal | headings: "preset workflow/code computes or enforces" / "AI proposes, audits, or interprets" / "human authorizes or adjudicates" |
| 34 | T2, T3, T4 | S | table load | T2: three exemplar rows at different enforcement levels; T3: evidenced comparison or cut; T4: condense to ~1.5 pp, full roster in the release |
| 35 | whole | S | cut plan, about six pages: compress §3 by a third; remove or merge F3; shorten T2; rebuild or cut T3; condense T4; remove repeated doctrine; compress §10.5 to a paragraph; KEEP the concrete episodes |
| 36 | whole | B | objection 1: "project documentation, not yet an astronomy-methods result" | make the walkthrough burst a complete quantitative acceptance case: per step, input hash, producer, verifier, human decision, defect, lesson/test, status, reproducible output |
| 37 | §4, §8 | B | objection 2: "the scientific decision engine has not been validated, so the architecture may faithfully automate a biased model-selection procedure" | injection/recovery in the existing evaluation harness; score Stage-1 concordance, rule compliance, recovery under known truth, downstream impact separately |
| 38 | §5–§6 | B | objection 3: "'blind', 'independent' and 'learning' are labels rather than measured properties" | context manifests and timestamps; the primitive-sharing matrix; predefine K; plot corrections per eligible step; run the battery after one controlled model change; one cross-model replay |
| 39 | §1, §10.3 | B | the bibliography is too small for the claims | 20 identifiers offered, all verified below |

## Literature the referee expects (all 20 verified at ADS by this session, 2026-09-03)
Astronomy agents: Kostunin+2025 (2025arXiv250300821K, ground-based gamma astronomy agents — the closest domain
precursor); Laverick+2024 (2024arXiv241200431L); Wang+2024 StarWhisper (2024arXiv241206412W); Moss+2025 AI Cosmologist
(2025arXiv250403424M); Ye+2025 ReplicationBench (2025arXiv251024591Y); Panek+2026 ASTER (2026arXiv260326953P);
Borrett+2026 (2026arXiv260409621B).
Workflows, reproducibility, provenance: Lu+2024 AI Scientist (2024arXiv240806292L); Siegel+2024 CORE-Bench
(2024arXiv240911363S); Chen+2024 ScienceAgentBench (2024arXiv241005080C); Starace+2025 PaperBench
(2025arXiv250401848S); Souza+2025 PROV-AGENT (2025arXiv250802866S); Souza+2025 workflow provenance
(2025arXiv250913978S); W3C PROV-O (standard, not arXiv).
Self-verification limits and correlated reviewers: Huang+2023 (2023arXiv231001798H); Stechly+2024
(2024arXiv240208115S); Valmeekam+2023 (2023arXiv231008118V); Kamoi+2024 (2024arXiv240601297K); Kim+2025 correlated
errors (2025arXiv250607962K); Panickssery+2024 self-preference (2024arXiv240413076P).
Agent evaluation: Liu+2023 AgentBench (2023arXiv230803688L).

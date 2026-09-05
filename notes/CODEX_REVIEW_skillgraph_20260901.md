# 1. VERDICT

**A new SKILL-GRAPH actor is not needed. This proposal is mostly solving the wrong problem.** The right problem is **uncontrolled workflow execution plus missing evidence-backed compliance at transition boundaries**.

The repository already specifies the actor that retrieves the law: A1 SKILL-READER is first at session open and is to be re-invoked at every step open. Its own contract already identifies the actual hole: “checklist compliance unverified downstream,” with `wf-gate` checking each checklist item's trace as the proposed closure (`AgentRoster.md`, A1). The observed session did not lack access to the rules; it failed to invoke the existing actor six times and then finalized/presented work without proving compliance. Adding another actor does not cure non-invocation. It creates another actor that the same unbuilt orchestrator can fail to call.

The five incidents support that diagnosis:

- The missing trigger identifiers were an artifact-contract violation detectable from filenames.
- The missing approval stamp was an illegal state transition detectable from `APPROVALS.json`.
- The two incorrect uses of DECISIVE were claim-semantics violations detectable by recomputing the stated comparison and linting the required reference phrase.
- The counterfactual presented as an observed outcome was a provenance/schema violation requiring typed fields and source binding.

None required a knowledge graph to detect. All required a gate that refused to advance without evidence.

A **derived rule index** could eventually be useful as a non-authoritative view for routing. It should not be an actor, a second source of truth, or a substitute for the skills. This matches the repository's own claim-evidence-graph decision: schema-on-read over canonical files, not duplicated truth (`AgentSkeleton.md` §8).

# 2. RETRIEVAL OR FINALIZE-TIME GATE

**The finalize-time compliance gate is much more valuable.** Retrieval reduces reading cost; finalization prevents a bad state transition. The measured failures occurred despite the rules being in context, so retrieval latency is not the limiting variable.

The valuable design is:

1. At step open, the existing SKILL-READER emits a versioned, structured checklist for this burst.
2. During production, each applicable item accumulates machine-readable evidence.
3. At FINALIZE, the workflow refuses to advance unless every applicable item is either:
   - mechanically passed;
   - verified by the correct independent verifier with evidence; or
   - waived by an authorized human, with identity, reason, scope, and source rule recorded.

“Discharged” cannot mean “the operating agent checked a box.” That would let the same actor that made the error certify its own compliance, recreating the producer-verifies-producer failure. Each discharge needs a test result, artifact hash, verifier verdict, or human waiver. The gate must be a transition precondition owned by the queue/workflow machinery.

Retrieval is useful only as a later optimization. A safe repeat tier could cache the full-read result by hashes of all binding law files and re-read the complete owning skill whenever any hash, burst configuration, open register row, or workflow version changes. Until equivalence against full reading is demonstrated, graph-subset retrieval should supplement rather than replace the required end-to-end read.

# 3. STRONGEST ARGUMENT AGAINST

**Yes: a derived graph can move the failure from visible non-reading to invisible missing-edge confidence. That is potentially worse.** A reader who did not open a skill leaves an auditable invocation gap. A graph query can return a clean-looking, internally consistent subset while silently omitting the one untagged rule that matters. The system may then claim “all applicable rules passed” when it has proved only “all represented edges passed.”

Deriving the graph from front matter prevents graph/document drift only after an annotation exists. It does not prove that the annotation is complete or correct. The person or model assigning nodes becomes a new semantic bottleneck. The proposed nodes are also broad enough that a superficially plausible but wrong tag will be hard to notice. For example, the trigger-ID rule is cross-step and cross-artifact; DECISIVE depends not merely on the `dAIC` quantity but on the comparator and claim type; stamp-on-answer attaches to a transition and actor identity, not primarily to a pipeline step.

A missing edge cannot be detected from the graph alone. The independent completeness oracle must remain the authoritative prose plus executable contracts. Minimum detection machinery would be:

- Give every normative rule an immutable rule ID and exact source span/hash. Every numbered rule, checklist item, PI ruling, and active register row must appear exactly once in the rule manifest; unregistered normative language fails lint.
- Run bidirectional coverage lint: every active rule has at least one applicability mapping and one enforcement/discharge method; every graph edge resolves to a current source span; orphan rules and orphan edges fail.
- Represent authority and lifecycle explicitly: `proposed`, `PI-approved`, `active`, `superseded`, `conflicting`, and effective version. A graph that mixes proposals with law is unsafe.
- Diff-gate law changes. A changed rule hash invalidates cached checklists and requires review of its mappings and tests.
- Compare graph-selected checklists against fresh full-skill reads on a stratified burst sample and after every law change. Any omitted applicable rule is a release-blocking false negative.
- Use mutation tests: deliberately remove or mis-tag each edge and confirm that coverage lint or a full-read audit fails. Replay the five known incidents, but also inject unseen violations.
- Track false-negative incidents: any rule found applicable after finalization is an F-SILENT event, invalidates the affected products, and adds a regression test at the primitive.

Even these measures do not make the graph complete; they make incompleteness more observable. The graph must therefore report its coverage boundary and never certify its own completeness.

# 4. NODE TAXONOMY

**The proposed taxonomy is not sufficient and mixes different kinds of things.** Steps are lifecycle locations; figures and catalogs are artifact types; `code port` is an action; `deliverable` is an aggregate/lifecycle status; quantities are claim subjects. Treating all of them as peer nodes loses the predicates that make a rule binding.

The first-class node should be the **rule/obligation**, not the step. It needs at least:

- stable rule ID and exact source span/hash;
- authority, status, effective date, and supersession/conflict links;
- applicability predicate;
- required evidence;
- enforcement mechanism and responsible verifier;
- permitted waiver authority;
- failure class, invalidation scope, and remediation.

The graph then needs separate typed dimensions:

- **Lifecycle:** session intake, step open, run, write, finalize, present, approve, ship, invalidate; state and state transition.
- **Action/event:** quote a number, write a catalog row, create a filename, port code, launch Monte Carlo work, retry, assemble, waive.
- **Actor/role:** producer, presenter, verifier, approver, skill-reader, dispatcher; including independence and identity constraints.
- **Artifact and field:** artifact instance/class, filename, table column, JSON field, sidecar, ledger, report sentence, figure label, approval stamp.
- **Claim semantics:** observed/estimated/counterfactual/causal/mechanistic/speculative; estimator; reference frame; comparator; threshold; units. `dAIC` without “versus which model?” is not a sufficient node.
- **Runtime/data predicates:** burst identity, detector configuration, instrument, model family, block significance, redshift availability, structural exclusion, execution mode, code hash, and open debt.
- **Evidence/provenance:** input/output hashes, run receipt, verifier verdict, source record, citation, human ruling.
- **Relationships:** requires, forbids, applies-when, verified-by, derived-from, conflicts-with, supersedes, invalidates, exception-to, and waived-by.

Quantities should usually be typed fields or claim subjects, not the primary routing key. The graph query should start from the attempted transition and concrete artifacts/actions, then evaluate predicates. Otherwise cross-cutting rules will be missed precisely because they are not owned by one step.

# 5. SEQUENCING

**Build the queue manager and typed workflow transitions first.** The repository currently has no `dev/queue_manager.py`; A17 is a specification, not an implementation. That fact also conflicts with the “queue manager v1” wording in `FreshSessionBoot.md`'s hand-off state, which should be reconciled as status drift before it is relied upon.

Recommended order:

1. Implement the queue manager's minimal durable loop: legal state transitions, resume, typed failures, and mandatory stage invocation.
2. Put the existing SKILL-READER at every step open and persist its structured checklist, source hashes, and applicability decisions.
3. Implement `wf-gate` checklist-compliance as a transition barrier, initially using explicit per-step contract manifests and existing verifiers.
4. Add deterministic guards and regression/mutation tests for the five known failures and other high-risk rules.
5. Only after that works end-to-end, add a schema-on-read rule index if measured retrieval cost justifies it. Validate it against full reads before allowing it to select a reduced subset.
6. Preserve A19 as the last new actor before freeze, as already decided. A rule index is infrastructure, not an actor, and must not displace truth-grounding work.

**Do not build a standalone SKILL-GRAPH actor, a graph database, a second hand-maintained rule store, or an autonomous rule-waiver agent.** Also do not front-load mass tagging before the rule-ID schema, authority model, coverage lint, and consumer exist. “Cheap and additive” tags are not cheap if they create an unaudited representation that later acquires authority. Tag only through the same change that supplies a rule ID, source binding, applicability test, and discharge contract.

# 6. CHEAPER MECHANISMS

Several cheaper mechanisms catch the reported failures more reliably than semantic graph traversal:

- **Trigger-ID filename lint:** before step finalization, enumerate declared per-burst outputs and fail if the basename does not contain the canonical trigger. Test nested directories and all extensions. This catches failure 1 directly.
- **State/stamp transition guard:** the manager may not record approval or advance beyond presentation unless `APPROVALS.json` contains the required identity-bound stamp and current evidence hashes. Chat text has no transition authority. This catches failure 2 directly.
- **Terminology lint plus semantic recomputation:** fail any bare `DECISIVE` or `TRACKED`; require `DECISIVE vs <named simpler ancestor>` or `TRACKED vs <named runner-up>`. Then recompute the margin from the bound fit table and verify the named comparator and threshold. Text lint catches omission; recomputation catches confident mislabelling. This catches failures 3–4.
- **Typed decision provenance:** replace a free-text effect sentence with separate fields such as `action_taken`, `observed_outcome`, `counterfactual_definition`, `counterfactual_result`, `source_artifact_sha256`, and `claim_type`. Refuse prose whose claimed outcome is not traceable to the action actually taken. This is the appropriate primitive for failure 5; a graph edge alone cannot determine whether the quoted number describes the factual or counterfactual branch.
- **Per-step contract manifest:** a small version-controlled schema maps rule IDs to applicability predicates, evidence paths, check commands, verifier role, and invalidation scope. The finalize receipt records PASS/NOT-APPLICABLE/WAIVED plus evidence for every row. This delivers most of the graph's useful behavior without graph machinery.
- **Contract tests:** for each step, construct one conforming fixture and mutations that violate each rule. The workflow must reject every mutation. Known-incident replay is a regression suite, not the acceptance suite by itself.
- **Law lint:** detect unnumbered normative terms (`must`, `never`, `only`, `refuses`, `required`) outside registered rule blocks; detect duplicate IDs, unresolved cross-references, conflicting active thresholds, proposed rules represented as active, and active rules with no check or verifier.
- **Hash-keyed repeat reading:** cache the SKILL-READER's full-read checklist and invalidate it on any relevant law, register, workflow, or burst-configuration hash change. This addresses cost without claiming that a reduced graph query is equivalent to reading the law.

These mechanisms follow P8's own ordering: push enforceable rules into code, hooks, schemas, and self-describing artifacts. Leave genuinely semantic judgments to an independent verifier or the PI, but still require evidence and an explicit verdict.

# 7. INDEPENDENT JUDGEMENT

The operating agent is most likely confusing **having rules in context** with **being constrained by them**. The PI is right that “too many rules” is not an excuse, but human possession of a skill is not an enforcement mechanism. The five failures are not evidence that the human or model needs a faster memory; they are evidence that the system allowed an unverified action to become state.

The proposal also underestimates three risks neither side states clearly:

1. **Self-discharge becomes disguised self-approval.** If the same operating agent queries the graph, performs the work, and says each rule is satisfied, the new gate violates the architecture's independence principle in substance even if it is named “compliance.” Mechanical checks and independent verdicts must provide the discharge evidence.
2. **Passing replay of five known failures is vulnerable to overfitting.** Four have straightforward signatures; the fifth requires semantic truth about factual versus counterfactual branches. A system can special-case all five and still fail the next paraphrase. Acceptance needs mutation tests, held-out incidents, full-read differential audits, and measured false-negative rates.
3. **The dangerous optimization target is the wrong one.** Most failures occurred at presentation/finalization, not during rule discovery. Making rule pickup faster may increase confidence and throughput before correctness exists. The project should first make illegal finalization impossible, then optimize reading cost from measured latency.

There is also a live design-state warning: `FreshSessionBoot.md` describes a queue-manager v1 in its hand-off facts while the named file is absent and the brief says it does not exist. That is the same class of invisible status drift the proposed graph could amplify. Before building a new semantic layer, make status derived from executable evidence and make every claimed capability distinguish **specified**, **deployed**, and **verified in the current workflow**.

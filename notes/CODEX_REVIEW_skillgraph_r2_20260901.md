# 1. DOES ACTION-INDEXING DISSOLVE THE MISSING-EDGE PROBLEM?

**It reduces the search space, but it does not dissolve the missing-edge problem. It relocates the completeness decision from “which rules attach to this step?” to “what action is actually occurring, and which contexts qualify it?”**

That relocation is useful. The step is a poor primary key for cross-cutting obligations: naming, stamping, quoting, saving, and shipping occur in several steps. Starting from a concrete action is therefore safer than starting from one of ten pipeline steps and hoping every cross-step rule was copied there. A curated list of roughly 14 action families is also easier to audit than roughly 970 possible rule-to-step pairs.

But the comparison is not really 14 versus 970. A usable key is closer to:

`action × artifact class × lifecycle phase × actor role × scientific context × authority state`

For example, “write” is insufficient. Writing a temporary cache, a canonical catalog row, a provenance sidecar, a human approval, and a released manifest are different regulated events. “Quote” is insufficient without the source artifact, estimator, comparator, frame, and claim type. The smaller action vocabulary reduces duplication; the applicability predicates still carry most of the semantic burden.

The decisive safety condition is **who identifies the action**. If the operating agent asks itself “which verb am I performing?” and selects the rules, the new key is another unreliable judgment and can be self-serving. If the workflow executor emits a typed action event from the command, destination, schema, and attempted state transition, action indexing is genuinely safer. Ambiguity must produce `UNCLASSIFIED_ACTION` or multiple simultaneous actions, never a best-guess single label.

So the round-one objection becomes two narrower failure modes:

1. a real operation has no registered action type; or
2. a registered action is missing a context-qualified rule attachment.

Both remain missing edges, but they can be made mechanically observable. The action table is a good routing index; it is not a completeness proof.

# 2. HOW TO DETECT A MISSING VERB

Use **side-effect trace coverage with a fail-closed unclassified event**, not prose review alone.

Implement one action envelope at the workflow boundary:

```text
ACTION_EVENT = {
  event_id,
  primitive,              # create/write/rename/render/stamp/launch/send/...
  caller_path_and_sha,
  argv_or_tool_call,
  actor_identity_and_role,
  workflow_and_transition,
  input_paths_and_hashes,
  output_path,
  output_artifact_class,
  schema_or_mime,
  before_state,
  intended_after_state,
  action_type_ids[]
}
```

Then detect missing verbs concretely as follows:

1. **Inventory side-effect primitives statically.** Scan executable entry points for durable writes and external effects: `open(..., 'w'/'a')`, `Path.write_*`, `json.dump`, Astropy/Pandas table writes, `savefig`, file rename/replace, subprocess launches, downloader/network calls, approval/state writers, bundle/release creation, and delivery tools. Each call site must map to at least one action type or an explicitly exempt internal-temporary class. A new unmatched call site fails continuous integration.
2. **Trace representative workflows dynamically.** In a clean test workspace, wrap file writes/renames, producer launches, state transitions, and delivery calls. Compare observed events with declared action events. An observed durable or external effect with no action type is `UNCLASSIFIED_ACTION`, an F-CONTRACT stop. A declared output that never appears is also a failure; this catches non-events such as NR-16 product absence.
3. **Reconcile declared and observed effects at finalize.** The transition receipt contains the complete event set. Finalization fails on any undeclared write, unclassified event, missing declared product, or event lacking a rule-discharge receipt. The operating agent cannot remove an event from this set.
4. **Mutation-test the detector.** Add a new helper that writes a catalog under a different filename, save a figure through a different library, rename a product after a compliant save, wrap a producer in another shell script, and omit a declared PDF. Each mutation must still be classified or must fail as unclassified/missing. Replaying the five historical incidents remains regression coverage, not the completeness test.
5. **Audit semantic, non-I/O actions at their consuming boundary.** Claims do not always create a distinct filesystem syscall. Assemblers must emit typed claim records for every number, preference term, component-requirement statement, and factual/counterfactual assertion. A final text scanner reconciles rendered claims against those records. Unbound claim-like prose becomes `UNCLASSIFIED_CLAIM`, not an accepted sentence.

This method does not claim to enumerate all English verbs. It makes every durable effect, external effect, transition, and published claim either mapped or loudly unknown. That is the observable completeness boundary the proposal currently lacks.

The repository already contains pieces of this pattern: `dev/live_report.py` separates presentation from approval and requires identity; `dev/invalidate_downstream.py` models downstream effects; `.claude/hooks/no_unverified_figures.py` intercepts one delivery surface; and `.claude/hooks/require_dispatch.py` intercepts a small list of producer launches. Their narrow, pattern-based coverage also demonstrates why the missing-verb detector must compare all observed effects with a registry rather than assume the current hook list is complete.

# 3. IS THE 14-VERB LIST RIGHT?

**It is a strong incident-derived seed, not a complete action vocabulary. It mixes atomic actions, compound workflows, objects, and contexts.**

## Missing action families

- **Launch / execute a producer or heavy computation.** This is where the dispatcher, skill-reader receipt, invocation provenance (NR-7), resource claim (NR-12), checkpoint/resume contract, and producer version must fire. `.claude/hooks/require_dispatch.py` currently recognizes only a regex list of launch surfaces, which is direct evidence that launch is an action family and that wrappers can escape an incomplete enumeration.
- **Finalize / promote / advance state.** Creating bytes is not the same as accepting them as current state. This action carries completeness, model census, product-absence, hash-currency, verifier-discharge, and legal-transition rules. It is the most important missing verb because the round-one diagnosis was “unverified action becoming state.”
- **Consume / select an authoritative input.** NR-23 same-source, approved-catalog selection, campaign pinning, stale-column exclusion, and source-hash binding fire when a downstream product reads or chooses an input, not only when that input was written. A stale file can be perfectly named and validly saved.
- **Verify / record a verdict.** Verification has independence, contract-version, artifact-hash, checker-version, and F-GUARD requirements. It cannot be folded into “deliver a figure”; the verifier acts before delivery and may itself be wrong.
- **Present / send / release.** Presentation to the PI, file delivery, publication, collaborator handoff, and bundle release are distinct external-boundary events. The existing no-ship hook covers only delivered PNGs; R4/R5 cover broader release surfaces.
- **Classify and handle a failure.** The queue manager alone classifies the six failure classes and chooses HOLD/LABEL/STOP/WAIT/DEMOTE/FIX-GUARD. A bare failing command is not the regulated action; accepting and routing its failure is.
- **Waive / override / authorize an exception.** A waiver is neither approval nor amendment. It needs authorized identity, reason, scope, expiry, affected rules, and invalidation consequences. No operating-agent waiver is valid.
- **Acquire / ingest external data.** Data download, literature import, response acquisition, and catalog ingestion need source identity, checksums, licensing/citation provenance, raw-data protection, and failure labeling. `protect_rawdata.py` explicitly exempts acquisition commands, proving that acquisition is already a meaningful action class.
- **Cite / attribute / compare with literature.** Blind-first freezing, bibcode verification, frame alignment, and the prohibition on calling a frame difference a discrepancy fire when literature is cited or compared, not at generic assembly alone.
- **Estimate / derive a scientific quantity.** “Quote” governs consumption and presentation, but the estimator run itself carries units, parameter scaling, validity, null/injection testing, and structural-refusal behavior. Temporal estimation, spectral selection, binning, and detector/background decisions need typed subactions or contexts under this family.
- **Delete / supersede / invalidate.** Mutation is not limited to Stage-1 windows. Marker deletion, stamp demotion, output supersession, cache invalidation, and cleanup require target validation, auditability, and correct cascade. `dev/invalidate_downstream.py` already makes this a first-class operation.

## Entries that are actually compound actions

- **“name / save a per-burst product”** is at least `assign_identity`, `persist`, and often `finalize`. A correct basename does not prove an atomic or provenance-bound save.
- **“write an approval / presentation stamp”** combines `present`, `approve`, `record_feedback`, and potentially `waive`. `dev/live_report.py` implements different semantics for `--present` and `--approve`; the taxonomy should preserve that distinction.
- **“print a model-preference word”** combines `derive a comparison`, `select a claim term`, and `render the claim`. The semantic recomputation and the lexical lint are different checks.
- **“quote a temporal number”** combines `select source`, `validate currency`, `transform/round`, and `publish claim`.
- **“deliver a figure”** omits `render`, `verify`, `approve`, and `send`. These must not collapse because producer/verifier separation depends on their being different events and actors.
- **“produce a stochastic result”** combines `execute stochastic estimator`, `record seed/environment`, `persist`, and `replay-verify`.
- **“assemble a deliverable”** combines `select inputs`, `assemble`, `compile`, `finalize`, and later `release`.
- **“amend a Stage-1 window”** combines `make a scientific decision`, `record its provenance`, `mutate canonical state`, and `invalidate dependents`. The first and third require different authorities.
- **“claim a component is required”** combines `run/calibrate evidence`, `evaluate the claim predicate`, and `publish the claim`.
- **“start a root-cause or redo”** contains two different verbs. Root-cause analysis requires prior-art retrieval; a redo additionally requires invalidation, authorization, resource admission, and new provenance.
- **“close an incident”** combines `classify`, `root-cause`, `remediate`, `test`, `distill`, and `register`.

## Entries that are contexts or objects, not action types

- **“per-burst product,” “committed catalog,” “temporal number,” “duration (T90),” “figure,” “stochastic result,” “Stage-1 window,” and “component”** are artifact or scientific-context dimensions.
- **“model-preference word”** is a claim/lexical class.
- **“required”** is a claim predicate, not a verb family.

The duplication between “quote a temporal number” and “quote a duration” makes the taxonomy problem visible: `quote` is the action; `temporal_quantity=T90` plus truncation flags is the applicability context. Keep T90 as an explicit high-risk context, not as a peer verb.

# 4. TABLE OR GRAPH?

**Use a table for action routing, but retain typed edges for applicability, evidence, ordering, and invalidation. No graph database is needed.**

A flat `action_type → candidate rule IDs` table is the correct first lookup and probably handles most routing cheaply. It cannot by itself express the domain's load-bearing conditions:

- `quote_number + estimator=T90 + (window_truncated OR tail_outside_window)` requires lower-limit language;
- `quote_temporal + source=temporal_catalog_all106 + trigger∉rewalked_triggers` forbids the quote;
- `deliver_figure` requires a prior `render` event, a verdict by a different actor, and a verdict bound to the exact delivered SHA;
- `approve_step` requires a prior presented artifact and an identity authorized for approval, not merely an identity string;
- `amend_background + detector=reference_NaI` invalidates binning and fits, while a non-reference-detector background amendment leaves the block grid eligible for hash-based reinstatement (`dev/invalidate_downstream.py`, step 3);
- `port_code + source_hash_changed` invalidates the prior port-verifier verdict;
- `assemble + fit_source=X` requires figures, tables, and prose numbers to derive from X, and a later change to X invalidates the assembly;
- a rule may be active, proposed, superseded, conflicting, or waived by a particular authority over a limited scope.

Those are edges: `applies-when`, `requires-before`, `verified-by`, `derived-from`, `invalidates`, `supersedes`, `conflicts-with`, and `waived-by`. Sequence edges are essential because saving, verifying, presenting, approving, and releasing the same artifact are not interchangeable.

Therefore the right design is a **relational action-rule registry rendered as schema-on-read views over canonical files**. It may be stored initially as a few normalized tables or manifests. “Graph” describes the semantics and traversals; it does not justify Neo4j, graph RAG, duplicated skill text, embeddings, or a new actor. The action table selects candidate obligations; context predicates and dependency edges decide which obligations fire and what becomes stale later.

# 5. WHICH BOUNDARIES ARE MECHANICAL, INDEPENDENT, OR HUMAN?

| Proposed entry | Mechanical action-boundary enforcement | Independent agent required | Irreducibly human in this campaign |
|---|---|---|---|
| name / save per-burst product | Intercept declared-output commit; canonical trigger/path/schema lint; atomic-write and sidecar/hash checks; reject undeclared writes | Only when artifact classification or provenance meaning is ambiguous | None for routine naming/saving |
| write committed catalog row | Schema/range/duplicate/identity/currency screens before atomic catalog replacement; provenance receipt | Admission-gate for semantic cross-field and failure-transparency screens | Human only for a scientific exception or contract change |
| write approval / presentation stamp | Separate typed commands; require current evidence hash, identity, legal prior state, and invalidate downstream state on feedback/change | Independent conformance check can verify the trail; it cannot choose approval | Approval identity, waivers, and PI feedback; presenter identity must be the actor who actually presented |
| print model-preference word | Lexical lint plus recomputation of named comparator, validity gate, threshold, and tie set from bound table | Tie-reporter/numbers-verifier for semantic claim context | Human only to amend terminology or thresholds |
| quote temporal number | Require source row hash, estimator label, units, freshness/rewalk membership, and printed-precision recomputation | Numbers-verifier; scientific reviewer for interpretation | Human only for an explicit scoped waiver or new convention |
| quote duration (T90) | Same quote guard plus union of truncation/tail flags and automatic lower-limit wording | Numbers-verifier | Human only to change the lower-limit rule |
| deliver figure | Delivery hook checks exact SHA, current vision verdict, format, destination, and release membership | Fresh figure-verifier; report-conformance gate when embedded | PI approval at the walkthrough gate; a visual contract amendment is human |
| produce stochastic result | Seed field required, `PYTHONHASHSEED`/RNG provenance, deterministic replay test where promised, resource claim | Seed-auditor; A19 at engine-hash/freeze truth tests | Human only to approve a changed stochastic/scientific contract |
| port code | Detect imported/copied implementation or require explicit port manifest; bind source hash; expire verdict on source change | Port-verifier runs source and port on synthetic fixtures | Human only to accept a changed tolerance/contract |
| assemble deliverable | Pin/clean-generator checks; same-source hashes; required-product census; compile success; no raw `nan`; R1–R5 receipt | Figure-verifier, numbers-verifier, and NR-24 conformance verifier, all non-producers | PI approval/release decision |
| amend Stage-1 window | Validate target/backup; record old/new hashes and stated provenance; transactionally invoke NR-19 cascade | Independent presenter/verifier may confirm the mutation and affected scope | The Stage-1 judgment and approval remain human; historical reasoning cannot be invented |
| claim component required | Require typed claim, named test/reference, validity flags, edge status, null/injection evidence, and exact source hashes | Numbers/scientific verifier plus A19 truth-grounding at the declared cadence | Human sets or amends the scientific claim standard; final interpretive adoption may remain a PI gate |
| start root-cause or redo | Queue refuses start without prior-art receipt; redo requires invalidation receipt, legal state, resource admission, and new run ID | Prior-art-reader before diagnosis; distiller after; verifiers rerun on new artifacts | Human where the redo changes a frozen method, approval, or scope |
| close incident | Refuse closure until failure class, primitive cause, remediation test, affected-artifact invalidation, and lesson/register evidence are linked | Distiller must be separate from the actor whose failure is being closed; F-GUARD reruns affected gates | PI wording is required for contract amendments; the PI accepts rulings/freezes |

The useful division is not “mechanical versus agent versus human” once per verb. One compound operation often has all three: a mechanical precondition, an independent semantic verdict, and a human authority decision. The registry must attach each obligation to its exact phase (`preflight`, `commit`, `finalize`, `present`, or `approve`) so a later human choice cannot erase a failed mechanical check and an operating agent cannot self-discharge a semantic obligation.

# 6. DOES THIS CHANGE THE ROUND-ONE SEQUENCING?

**It changes the queue-manager implementation slightly, not the architectural priority.**

A minimal action registry is cheap enough to write **as the queue manager's input contract** before or alongside its first implementation:

1. define stable action IDs and the `ACTION_EVENT` envelope;
2. register the first high-risk actions: producer launch, durable write, catalog commit, stamp, finalization/state advance, figure delivery, and invalidation;
3. make `UNCLASSIFIED_ACTION` fail closed;
4. have the queue manager emit, sequence, and reconcile those events;
5. add discharge receipts and coverage/mutation lint;
6. expand rule attachments incrementally from observed operations and incidents;
7. add A19 last, as already sequenced.

That small registry may precede the queue-manager code by a short design step because the manager needs typed events to orchestrate. It must not be presented as deployed enforcement, used to replace full skill reading, or expanded into mass tagging before it has a consumer and coverage tests.

Building the full 14×46 table as a standalone artifact first would inherit exactly the same “nothing makes it fire” problem. The repository demonstrates the distinction: the G1 filename rule is clear prose in `BurstWalkthrough.md`, while the no-ship and dispatch rules fire only on the particular tool surfaces their hooks intercept. A table on disk has the enforcement strength of prose until the executor emits an event, the workflow blocks on its receipts, and finalize reconciles observed effects.

Thus the round-one sequence remains: durable queue/state machinery first; mandatory action emission and existing skill-reader invocation inside it; evidence-backed finalize barrier; then broader indexing as measured utility warrants. The only refinement is to make the action schema part of the queue manager's foundation rather than a later retrieval optimization.

# 7. INDEPENDENT JUDGEMENT

The central unasked problem is that **many dangerous obligations are triggered by a state relation, an absence, or a later consumption—not by an affirmative verb at the moment a file is created.**

Examples from this repository include:

- a declared PDF is absent (NR-16): no “save PDF” action occurs to trigger the rule;
- an input hash changes after a verifier passed: the old verdict becomes stale without the original verification action recurring;
- an upstream approval changes: downstream products become invalid by dependency, even if nobody performs an explicit “invalidate” verb;
- a `max_tokens` stop returns a confident partial response: the danger is the termination condition, not a content-production verb;
- two active law files conflict: the obligation arises from inconsistent authority state, not a pipeline action;
- a cleanup never happens after `SIGKILL`: the missing release action is observable only against an expected lifecycle;
- a product is saved compliantly and then renamed or copied to a release path: save-time checks do not prove delivery-time compliance;
- a valid number is later consumed in an invalid context, such as an unrewalked burst or a different frame.

This means action indexing needs an **event-plus-invariant model**. Verbs route event-local rules; state invariants and dependency edges run continuously or at transition/finalize/consume boundaries. Expected-but-absent events need deadlines and completeness manifests. Hash changes need reverse-dependency invalidation. Termination reasons need typed handling. No finite verb list substitutes for those mechanisms.

A second unasked issue is transactional timing. A hook that fires “when a file is saved” may run after the canonical file has already been mutated. Every regulated action therefore needs `INTENT → PREFLIGHT → COMMIT → FINALIZE`, with the guard before commit and a recoverable/atomic write. Otherwise a failed rule can still leave partial state that later readers mistake for canonical.

A third issue is ontology authority. The operating agent must not invent an action label, decompose a compound action to avoid a stricter rule, or declare a write “temporary.” Action types must be emitted or derived by trusted wrappers from the actual target, schema, tool, and transition. The registry needs alias/composition rules, versioning, conflict/supersession status, and an owner. Without those, “verb-indexed” becomes a new vocabulary that can drift from the code exactly as step numbering and queue-manager status already drifted in the repository.

The refined framing is therefore directionally right but incomplete: **action is the best first routing key, not the unit of safety.** The unit of safety is an attempted state-changing or claim-publishing event, evaluated with context, sequence, dependencies, authority, and independently bound evidence. A compact action table can summon rules; only the queue/workflow machinery and invariant checks can ensure that every relevant event was summoned at all.

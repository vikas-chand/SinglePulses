# agentic_grb.tex v3 — rewrite outline (for the PI's gate; no v2 text deleted until approved)

**Trigger:** PI, 2026-09-02, verbatim: *"we have also enough now to write our paper in a better
way, the posts I shared has very nice flowcharts (and also maybe descriptions) and we can adopt
that way of creating ours, also we can nicely describe in breif the work of each of the component
we have"*. Sources whose diagram grammar we adopt: Bowne-Anderson (five runtime jobs; the
context × action map; the loop as pseudocode), Böckeler/Fowler (guides vs sensors, computational
vs inferential, the lifecycle timing diagram), Palantir (data · logic · action · security),
PuppyGraph (five components, four failure modes), LangChain (capability matrix). The comparison
that grounds every claim: `notes/HARNESS_COMPARISON_20260902.md` (§19 needs, §20 strengths).

**What stays from v2 (2026-09-01, 7,928 words, 3 figure environments = 2 TikZ + 1 PNG, 2 tables; corrected 2026-09-02 by the dispatcher's numbers check):** the sample, the
fitting-step figure, the campaign-loop figure (re-drawn in the new grammar), Learning Without
Gradients, the Verification Doctrine, the Human-vs-Agent design, the provisional results, the
failure taxonomy, the appendices. **What changes:** the spine becomes *the harness, component
by component*; every component gets one figure or one table row that says what it does; the
five-source comparison becomes the frame for "what generalizes" and for the limitations.
**What is cut:** nothing until the PI approves this outline (the 40→26-page rule).

**Rules that bind the rewrite:** paperedit protocol (one change at a time after this outline);
figure-verifier on every figure, including diagrams; numbers-verifier + ReportSpec R1–R5 before
the PI sees a PDF; provenance adjectives quoted never recalled; every number carries its
`\prov` row; PROPOSED vs DEPLOYED status stated for every component (nothing described as built
that is not on disk); the harness posts are cited as URLs in footnotes (not as scholarly work).

**Title:** unchanged from the v2 proposal — PI picks between the two forms.

---

## Figures (the "flowchart way")

| # | figure | grammar borrowed | content | status |
|---|---|---|---|---|
| F1 | **Harness anatomy** | Bowne-Anderson's five runtime jobs; PuppyGraph's five components | one block per job — loop · tools · context · state · boundaries — and under each the components WE have (session/queue manager; engine + scripts; skills + skill-reader + memory; disk-derived state + stamps + receipts; hooks + permissions + roles), DEPLOYED in solid, PROPOSED dashed | new (TikZ) |
| F2 | **The per-burst lifecycle with guides above and sensors below** | Böckeler's timing diagram | the eleven steps left→right; above each step the GUIDES that fire (skill file, checklist, contract); below it the SENSORS (tests, hooks, verifiers, the PI gate); computational in one colour, inferential in another; the human gate marked as a diamond; distillation and the drift janitor drawn as the continuous band underneath | new (TikZ) — replaces v2 Fig. 1's ledger box |
| F3 | **Inside the fitting step** | — | v2 Fig. 2 unchanged (deterministic engine, validity gates, two margins, evidence ratios, typed terminal states) | keep |
| F4 | **The steering loop** | Böckeler's steering loop; our enforcement hierarchy | incident → prior-art → distiller → lesson at the RIGHT layer (code > hook > artifact > agent) → register row with its origin → test that fails on recurrence → next burst runs a better pipeline; the `K clean passes → freeze` decision from v2 Fig. 1 moves here | new (TikZ) |
| F5 | **The object-and-action model** | Palantir's four-part language | our objects (burst, selection, block, fit, verdict, stamp, receipt, register row) with their declared links, the first-class actions (present, approve, promote, invalidate, deliver) with preflight → commit → receipt, and the actor roles (human / agent, model id) — DEPLOYED solid, PROPOSED dashed | new (TikZ) |
| F6 | **Where GRB analysis sits on the context × action map** | Bowne-Anderson's two-dimensional map | our job placed against support agents and coding agents: high on both axes; the consequence (reduce/offload/isolate + strict gates) annotated | new, small |
| F7 | **Campaign learning curve** | — | v2's `campaign_learning_curve.png` (lessons and register rows vs burst number; the id-collision incidents of 2026-09-02 as the newest points) | keep, re-render with the new points |
| F8 | **Runtime harness vs eval harness** | Bowne-Anderson's two harnesses | left: the campaign run; right: the eval battery (lessons-as-tests, known-results battery, benchmark, the case-study cases) and the arrow "every harness change, every model change" — with the PROPOSED parts dashed | new, small |

## Tables

| # | table | content |
|---|---|---|
| T1 | **Component roster — the work of each component in one line** (the PI's "describe in brief the work of each component") | one row per component: name · job (one sentence) · kind (guide / sensor / action / store) · execution (computational / inferential / human) · fires at · born from (incident or ruling, dated) · status (DEPLOYED / PROPOSED). ~35 rows: the 10 agents, 3 hooks, the engine, the 8 orchestrator tools, the 27 skills grouped, the register, the ledgers, the referee panel |
| T2 | **The register by layer** | counts of rows landed at code / hook / artifact / agent, DEPLOYED vs PROPOSED, and the "sensor-for-every-rule" coverage (rows with a sensor vs rows with none) — v2's table re-cut |
| T3 | **Known-results battery** | the reproductions that anchor the engine (v2 content) |
| T4 | **What we lack and what we do better** (Discussion) | the §19/§20 synthesis condensed: 8 needs with status, 10 strengths — each with the source that asked for it |

---

## Sections

### §1 Introduction (~2 pp) — *the vocabulary is the thesis*
- model vs harness ("the model supplies reasoning; the harness supplies everything else");
  workflow vs agent (predefined paths vs model-directed process); ours is a workflow with
  narrow, named, bounded agency and human gates — v2's opening, sharpened with the harness
  vocabulary now common to the five posts.
- why GRB spectroscopy is the right testbed (decisions without ground truth; instrument
  systematics; a 106-burst census as stakes) — keep.
- related work: Denario and the AI-scientist line (scholarly) + published agent-architecture works
  (ReAct, surveys, scientific-agent exemplars, agent evaluation, workflow provenance) — verified at ADS/
  publisher with local PDFs before any \cite. The five harness-engineering posts are NOT cited (PI ruling
  2026-09-03, decision 17); they remain internal design references in notes/HARNESS_COMPARISON_20260902.md.
- the paper's claim, stated plainly: reliability over a long scientific run is a property of
  the harness, and we show what that harness contains, what it caught, and what it lacks.

### §2 Sample and Data (~0.5 pp) — keep v2.

### §3 The harness, component by component (~3 pp) — NEW SPINE; F1, T1
- 3.1 the loop and the state machine (Mode B today; the 14 states; the queue manager as
  PROPOSED); 3.2 tools (the deterministic engine and scripts; the four-tool core the agents
  carry); 3.3 context (skills as files, the skill-reader checklist at every step, memory,
  reduce/offload/isolate); 3.4 state (disk-derived state board, identity stamps, receipts,
  provenance sidecars, commit pin); 3.5 boundaries (hooks, permission modes, roles, the
  no-ship gate, what the hooks do NOT cover).
- each subsection ends with its T1 rows; every component's status stated.

### §4 Guides and sensors along the burst (~2 pp) — F2, F3
- the eleven steps; what steers before each (guides) and what checks after (sensors);
  computational vs inferential census (≈100 guide rules; ≈50 computational checks; 7
  inferential agents + Codex + PI); where the human gate sits and why (cost of being wrong).
- F3 inside step 6 (keep).

### §5 The steering loop: learning without gradients (~2 pp) — F4, F7, T2
- v2 §5 content: the register, distillation the same session, lessons-as-tests, divergence
  learning; reframed as the steering loop; the enforcement hierarchy; the 2026-09-02 id
  collisions as the worked example (two sessions, one number, a test born the same day).

### §6 Verification doctrine (~2 pp) — keep v2 §6
- blind-first with frozen predictions; independence at the primitive; the four channels;
  sha-bound fresh-context verdicts; the blind referee panel (new since v2).

### §7 The object-and-action model (~1 pp) — F5, NEW, short and honest
- what is typed on disk today, what links exist by convention, which actions are
  first-class; the campaign ontology as the build in progress (PROPOSED parts dashed).

### §8 Experimental design: human versus agent (~1 pp) — keep v2.
### §9 Walkthrough-era results (~1.5 pp) — keep v2, provisional flag on every number.

### §10 Discussion (~2 pp) — T4, F6, F8
- failure taxonomy (keep); the capability boundary (keep);
- **what we lack** (the 8 needs, with the source that asked and our status) and **what we
  do better** (the 10 strengths) — the five-source synthesis as the limitations and the
  contribution in one table;
- what generalizes: the component model is the level to design at (the posts' own
  conclusion), and the science-specific behaviour harness (numbers discipline, blind-first)
  is what a physics pipeline adds to it.

### §11 Conclusions (~0.5 pp) — rewritten to the new spine.
### Appendices — keep (reproducibility; adversarial verification); add the full T1 if too long for the body.

**Length:** ~8.5–9 k words + 8 figures + 4 tables; v2 was 7.9 k + 4 + 2.

---

## Order of work after the PI approves this outline
1. T1 component roster first (it is the inventory everything else cites; sourced from
   `notes/AGENTS_REVIEW_20260902.md`, `notes/SKILLS_REVIEW_20260902.md`, the register).
2. F1, F2, F4, F5 as TikZ; each rendered and sent through the figure-verifier before it
   enters the tex.
3. §3, §4, §7 prose (new); §5, §10 re-cut; §1, §11 rewritten last.
4. Numbers-verifier + R1–R5 conformance on the assembled PDF; provenance manifest v3.
5. PI reads. Referee panel after the PI blesses (PAID, his call).

## Decision log
| when | item | PI ruling (verbatim) | applied |
|---|---|---|---|
| 2026-09-02 18:30 | outline gate (decision 11) | "Approve, start with the roster table (Recommended)" | outline APPROVED; order: T1 roster → F1/F2/F4/F5 diagrams (figure-verifier each) → §3/§4/§7 prose → §5/§10 re-cut → §1/§11 → numbers-verifier + R1–R5 → PI |
| 2026-09-02 ~19:15 | builds 1–5 (decision 12) | "Approve (verified, nits closed) (Recommended)" | fit-table auditor, 10 schemas + test, provenance stamp + action trace, eval battery, model-id module APPROVED on the delta verifier's PASS-WITH-NITS (f99bc30); approve event recorded in the trace |
| 2026-09-02 ~19:15 | keep-condition (decision 13) | "A 'keep:' clause inside each row's status cell (Recommended)" | register header rule + non-failing count test; distiller adds the clause when touching a row |
| 2026-09-02 ~19:15 | next non-invasive items (decision 14) | "After the diagrams (Recommended)" | drift janitor, spend ledger, component-inventory sidecar wait for F1/F2/F4/F5 to pass |
| 2026-09-02 ~23:20 | T1 roster (decision 15) | "Approve (verified 4 rounds) (Recommended)" | T1 APPROVED at 427fdc5 (49 rows; 4 verifier rounds); may be cited by the prose |
| 2026-09-02 ~23:20 | diagrams F1/F2/F4/F5 (decision 16) | "Approve all four (Recommended)" | APPROVED at the shas in results/campaign/agentfigs/VISION_QC.md (F1 d355cbec, F2 6165ad96, F4 755a0fee, F5 73bf5bf3); enter the tex as figure* with captions naming the census commit; K/freeze = rules not yet exercised |
| 2026-09-03 ~00:30 | citing the harness posts (decision 17) | "I think we don't need to cite blog posts, we engineered something and then discovered those posts to find if we are doing good but it is not needed to cite them, we can cite published works on which maybe those blogposts if they cited some" | §3 r3: footnote + post attributions removed; five-job / guides-sensors / code-vs-judgement kept as our exposition vocabulary; published related work → §1 after verification; PROV_MANIFEST_v3 drops the post URLs |

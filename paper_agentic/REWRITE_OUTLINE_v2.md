# agentic_grb.tex v2 — rewrite outline (for Vikas's gate; no v1 text deleted until approved)

**Trigger:** Vikas, 2026-08-10 — *"after our discussion on Agents that paper needs a rewrite
(all that html you made for the collabs)"*. The spine = `docs/agentic_workflow_map.md`
(the collaborator page): workflow-with-bounded-agency, gates, doctrine, learning curve.

**Title (proposal — sharpened from v1):**
> **"Can AI Agents Analyze Gamma-Ray Bursts? A Gated Human–Agent Workflow for
> Time-Resolved Fermi/GBM Spectroscopy, and What It Learns"**
(v1 title kept as alt: "Can AI Do GRB Data Analysis?…" — Vikas picks.)

**Voice:** WritingHelper register (agent-first, one action per sentence); PhD-1 audience rule
(one plain-language explanation per concept); every number anchors to a pipeline product
(Block-5 anchor-linter discipline); all walkthrough-era numbers carry the provisional flag
until the frozen sweep.

---

## §1 Introduction — *the vocabulary is the thesis*
- The distinction that carries the paper: **workflow** (predefined, gated paths) vs **agent**
  (model-directed process); ours is deliberately a workflow with **narrow, named, bounded
  agency** + human gates. [source: map §4; Anthropic 2024 framing]
- Why GRB spectroscopy is the right testbed: decisions without ground truth
  (Siddique-vs-Dirirsa on one burst), instrument systematics, a 106-burst census as stakes.
- Related work: **Denario** (breadth-first idea→paper; evaluation gap demonstrated at scale)
  vs our depth-first, verification-heavy design. [source: AI_SCIENTIST_PROGRAM notes]
- KEEP from v1: sample motivation (Busby–Lazzati). CUT from v1: any "autonomous scientist"
  framing.
~2.5 pp

## §2 The Agentic Workflow — *the full flow, properly named (Vikas 2026-08-10: include ALL of
the collaborator-page flow; no internal filenames — give each component a NAME)*

**NOMENCLATURE TABLE (internal → paper name; used consistently everywhere):**
| internal | paper name |
|---|---|
| dev/ai_guides/ corpus | **the Skill Library** — versioned procedural documents any agent (or human) executes |
| BurstWalkthrough.md | **the Campaign Protocol** (RUN → PRESENT → GATE → LITERATURE → DISTILL) |
| GCNIntelligence.md | the **Identity & Circulars skill** |
| LiteratureHarvest.md | the **Literature Harvest skill** (four-form query, version-of-record, frame alignment, seven named traps) |
| DataInventory.md | the **Data Inventory skill** (response-validity D-checks incl. blockage) |
| detector/background/source selection | the **Selection skills** (human-gated, stamp-recorded) |
| Binning.md / 27b+27c | the **Adaptive Binning skill** + **binning engine** (two-tier) |
| SpectralFitting.md / scripts 10 | the **Spectral Fitting skill** (flagship; numbered lessons L1–L27) + **fitting engine** (24-model menu, validity gates, graded evidence) |
| Temporal.md / 40 | the **Temporal skill** (with its public DEFECT LEDGER) + temporal chain |
| qc_flagging.md | the **QC skill** (typed terminal states; `non-identifiable` = success) |
| P0–P6 | **the Reconciliation Protocol** (freeze → verify-at-source → frame-align → diff → attribute → verdict) |
| tests/test_lessons.py | **the Lesson Test-Suite** (a lesson = claim + provenance + executable test) |
| *_VALID / BOUND_CAPPED / SHARPNESS_CAPPED | the **validity gates** and **capped-bound stamps** |
| notes/reconciliation/ | the **Burst Records** |
| campaign_ledger.csv | the **Campaign Ledger** (the training log) |

**§2.1 The campaign loop (Fig 1 = the map's first diagram, redrawn vector):**
scope gate (human) → Stage-1 gated selections (human GUI or vision-agent, always stamped) →
per-burst ledger of eleven steps (Identity & Circulars → Literature Harvest → Data Inventory →
Selections (adopt) → Adaptive Binning → blind Spectral Fitting → Temporal → νFν panels → QC) →
P0 freeze → Reconciliation Protocol → attribution (we-wrong / they-wrong / frame) → lesson
distilled into the Skill Library **with its test** → next burst runs a better pipeline →
K clean passes → FREEZE at a commit → one production sweep over all 106 → paper numbers.
State plainly: *the per-burst numbers are not the product; the matured Skill Library is.*

**§2.2 Inside the fitting step (Fig 2 = the map's second diagram):** every band with data +
valid response (quality-gated, never significance-gated); the 24-model menu; unconditional
multistarts for EVERY family; validity gates (geometry-aware rail tests); AIC over valid fits
ONLY; TWO margins (vs runner-up; vs simplest) reported as evidence ratios exp(ΔAIC/2) with
graded verdicts; adequacy ≠ identity (degeneracy classes); typed terminal states.

**§2.3 The authority split (the paper's honesty table, verbatim from the map):** what the
workflow decides / what the AI decides (bounded agency: winners via gated criteria, validity
verdicts, literature verification, mismatch attribution, anomaly flagging) / what humans
decide (scope, every step gate, lesson acceptance, freeze, promotion, claims).

**§2.4 The two planes:** production plane (this workflow) vs discovery plane (open hypotheses,
sandboxed, promoted only through the human gate; the scorecard-after-the-game rule).

**§2.5 The doctrine (the map's seven earned rules, one paragraph each, each citing the
failure it prevents):** blind-first ordering · margins over valid fits only · evidence ratios
never bare verdicts · quality-gated inclusion · lesson = claim + test · no silent approvals ·
verify at the source, attribute at the primitive.

- The gates as data: approval stamps, the QC-flag ledger ("record, don't reject"), the
  bn090530760 gate exchange as the worked example of human authority.
~5 pp (grows by ~2 pp; §6 Results compresses by 1 to compensate)

## §3 Learning Without Gradients — *the harness-learning claim (NEW, now the core)*
- Thesis: weights frozen; the SKILLS learn. Lesson = **claim + provenance + executable test**
  (the RLVR analogy stated once, plainly).
- **Fig 3 = the learning curve** (campaign_ledger.csv; lessons/burst + bugs/burst + cumulative).
- Convergence criterion = K clean passes → freeze → one production sweep (train→deploy).
- The L27 story as the central worked example: invisible for 7 hard bursts, exposed by the
  first soft burst under serial ordering, fixed + unit-tested same session, pre/post census
  bias quantified (4/6 spurious BB winners → 0). Curriculum diversity as a *finding*.
- L26 as the cross-validation example (published lag sign validates the pipeline's known
  inversion, live).
~3.5 pp

## §4 Verification Doctrine — *what makes agent output trustworthy*
- Blind-first P0→P6 with FROZEN predictions; the #8/#9/#10 P0 scorecards as evidence
  (P-A ✅ P-B ✅ P-C ✗ — a refuted prediction is the honesty proof).
- **False corroboration**: independence must live at the PRIMITIVE (kT 52.0-vs-54.6 shared
  minimum; FXT B-49 lineage; the DSBPL-symmetry double-error in the four-channel run).
- **The four-channel experiment** (§ its own): differently-primed lookers = good GENERATOR,
  bad ADJUDICATOR; prescribed unanimity; the confabulated channel CAUGHT by adjudication;
  the one genuine cross-primitive corroboration (image ↔ railed cross-norms = n6 blockage,
  independently confirmed by Siddique's published exclusion). "Verify the adversary too"
  (the 5×-run determinism refutation).
- KEEP v1's adversarial-verification appendix as the protocol; feed it these results.
~3 pp

## §5 Human–Agent Experimental Design — *kept, updated*
- v1's benchmark design KEPT (25-burst expert set; Expert-2 status honest).
- ADD: the natural two-arm design that emerged — Khushboo post-2020 / this arm 2015–19 —
  inter-operator consistency as the missing denominator.
- ADD: evaluation-gap argument — score the unpublished DECISIONS against the expert band;
  literature is a distribution, not an answer key (Siddique/Dirirsa adjudication as the
  worked case, incl. detector-set as the discriminant).
~2 pp

## §6 Results (walkthrough era, provisional-flagged)
- 10 bursts walked; per-burst one-liners from the records (081224 corroborated-null;
  130310A menu-forced identity; 130518A one-feature xb≈3.92kT; 090530760 positive-α
  one-break null; 090620400 first tracker + open Ec(t) tension; 170114A polarization
  constraints). The ledger table (campaign_ledger.csv) as Table 1.
- Blind-prediction scoreboard across bursts.
~2 pp

## §7 Discussion — failure modes, then creativity (Vikas 2026-08-10: "add failure modes
as well and creativity jumps etc at the end")
- **7.1 Failure taxonomy** (each mode with its caught instance): over-claiming (3 retractions,
  caught by human+Codex, never self-caught); prescribed unanimity (shared-prior consensus
  masquerading as measurement); confabulation (the evolution channel inventing its own figure's
  statistics — caught by adjudication); estimator mismatch (ad-hoc QC using a different
  background model than production → manufactured 5.6σ alarm); tool-interface misuse (invented
  CLI args); stale-order anchoring (skipping presented steps under momentum). Sept-7 material.
- **7.2 Generator vs adjudicator** — the four-channel result as the honest capability boundary.
- **7.3 The discovery plane and creativity as graph operations (outlook):** production plane
  is this paper; the discovery plane's promotion rule ("the agent may invent a new scorecard
  after seeing the game; it may not pretend it was chosen before"). Then the creativity
  hypothesis, carefully scoped as OUTLOOK: creative jumps as typed knowledge-graph operations —
  **A′** (bridging long/stale/never-co-cited paths), **B′** (negating a NAMED load-bearing
  assumption of a specific derivation, as the first generative move), **C** (generative
  construction: new node / new question / new topology). Adversarially stress-tested against
  24 historical discoveries: survives as 2/3 of a taxonomy (C required; acts, not results, are
  what classify — GW170817 is a landmark with no creative jump). The genuinely open slot:
  assumptions as first-class metadata + a provenance-tracked NEGATE operator on a literature-
  scale graph. [TODOcite Boden; Swanson; Uzzi+2013; Foster-Rzhetsky-Evans 2015; Wiggins 2006 —
  ALL to verify before submission]
- **7.4 What generalizes** vs what is GRB-specific.
~3 pp

## §8 Conclusions + Reproducibility
- KEEP v1 reproducibility appendix; update to QUICKSTART truths (fresh clone starts at
  Step 5; 6 tracked bursts) + tests/ suite + provenance spine.

---

**Mechanics:** draft v2 as `agentic_grb_v2.tex` alongside v1 (v1 untouched until you approve
the swap); section-by-section drafting, each section presented at a gate (/paperedit rhythm);
figures: map diagrams → vector; learning curve regenerated from the ledger at draft time.
**Estimate:** ~18–20 pp ApJ two-column incl. figures; 6 drafting sessions.
**Numbers policy:** real walkthrough-era values, every one provisional-flagged; refreshed
mechanically at the frozen sweep (anchor-linter pass).

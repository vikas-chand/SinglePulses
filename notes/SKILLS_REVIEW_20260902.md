# EVERY SKILL FILE, FOR DISCUSSION — 2026-09-02

**Why this document exists.** PI, 2026-09-02, verbatim: *"write more skills, this time we
will discuss all the skill files"*, then *"finally understand the whole workflow and need
of agents and merge some of them if they can act at same place with some roles"*, then
*"do a case study on one GRB and then write the paper"*, then *"build whole bunch of domain
specific tools and laydown framework for future works"*.

This is the DISCUSSION document for the first item. Nothing here is applied. Facts come
from a read-only inventory (fresh-context agent, 27 files, 5,388 lines in
`dev/ai_guides/`, plus the skill-shaped files outside it); every fact carries a
file:line. Proposals are marked PROPOSAL and wait for the PI's word, one at a time.

Companion documents: `notes/AGENTS_REVIEW_20260902.md` (agents/hooks/workflows, program
item 2), `notes/CODEX_REVIEW_skillgraph_r2_20260901.md` (the action-indexed verdict that
bounds how new skills are shaped).

---

## §1 The inventory in one table

Step = ledger step served. Ledger = named in the BurstWalkthrough step ledger (:104–114).
Structure column: L = numbered lessons, D = defect/trap ledger, C = checklist,
R = PI ruling inline, — = none.

| file | KB | last commit | step | in ledger? | structure | health signal |
|---|---|---|---|---|---|---|
| LiteratureHarvest.md | 14.5 | 08-30 | 0b | yes | phases, D (traps T1–T11 as bold bullets), C | traps are numbered but not headers, so the header census and the guard test do not see them; phases out of order (3, 3c, 3b, 4); "Step 0a" naming stale |
| GCNIntelligence.md | 5.2 | 07-31 | 0 | yes, **still marked ✎** | C, L (G1–G2, out of order) | ledger stale: file exists since 07-31 |
| DataInventory.md | 10.1 | 08-12 | 1 | yes, **still marked ✎** | C, L (D1–D5) | ledger stale |
| detector_selection.md | 16.6 | 08-31 | 2 | yes | criteria, contract, C, pitfalls | carries a live rule-vs-practice divergence (:43, NR-38) |
| background_selection.md | 20.8 | 08-31 | 3 | yes | PI ruling banner, criteria, contract, C | a root-level near-duplicate exists (§2.7) |
| source_selection.md | 8.8 | 08-12 | 4 | yes | special-bursts first, criteria, contract, C | untouched since 08-12 while siblings moved 08-31 |
| Binning.md | 7.6 | 08-31 | 5 | yes | tiers, R, C, pitfalls | PI rulings inline, unnumbered |
| SpectralFitting.md | 79.5 | 09-02 | 6 (+8) | yes | **L1–L33** (L14, L26, L29 absent), C | ledger says "L1–L13" (:111); **L31/L32/L33 collide with Temporal's** |
| Temporal.md | 26.3 | 08-31 | 7 | yes | L29, L33, L26, L31, L32 (non-monotonic), D, C | L31 stamped "PROPOSED pending PI" (:253) but in the active body |
| qc_flagging.md | 11.8 | 08-30 | 9 | yes | criteria, contract, C, scoring | header still says "task #6 of BENCHMARK_PLAN" (:3) |
| BurstWalkthrough.md | 15.2 | 09-01 | gates | — | the ledger itself (:97–114) | the ledger is the primary stale artefact (§2) |
| FigureVisionQC.md | 6.6 | 08-16 | 1/7/8 delivery | **no** | gate, S-items contract, no-exception rule | gates three steps yet absent from the ledger |
| SpectralResidualReview.md | 4.0 | 08-15 | 6/8 | no | arms 1–2, outputs | no ledger, no checklist; 3 references repo-wide |
| Figures.md | 6.7 | 08-13 | all figures | no | §1–§5 | overlaps FigureVisionQC + global style guide, no precedence line |
| ShippingGate.md | 4.1 | 08-15 | delivery | no | product-typed checklists, **Honest limits** | only file with a limits section; superseded in practice by roster verifiers |
| ReportSpec.md | 9.8 | 09-01 | 9 / assembly | no | R1–R5, R3a (appended after R5) | R-namespace collides with GUI_REQUIREMENTS R-items |
| RefereeLoop.md | 6.9 | 09-01 | milestone | no | two hats, loop, C, machinery | newest; machinery lives in dev/referee/ |
| AgentArchitecture.md | 60.3 | 09-02 | law | — | P1–P9, rosters, **register NR-1..47** | per-step roster (:70–102) duplicates the ledger with different content (step 8) |
| AgentRoster.md | 39.3 | 09-01 | law | — | A1–A18, decision sheet | A1 says "L1..L30+" (:64); A17 queue manager "to be built TODAY" (:569), unbuilt |
| AgentSkeleton.md | 14.9 | 08-30 | law | — | §1–§8 | 3-day build dated 08-27 overdue; `.claude/workflows/` does not exist |
| FreshSessionBoot.md | 16.2 | 08-31 | boot | — | §0–§10 | Codex flagged its queue-manager hand-off claim as status drift |
| BURST1_LESSONS.md | 44.8 | 08-15 | evidence | — | F-1..F-17 taxonomy, catch ledger | frozen at burst #1; bursts #2–#21 not folded in |
| PI_REVIEW_PROTOCOL.md | 3.6 | 08-29 | PI session | — | routing table | describes a session not yet held |
| CODEX_QUOTA_DISCIPLINE.md | 2.2 | 08-29 | ops | — | rules, queue | operations policy filed among science skills |
| ASSUMPTION_REGISTRY.md | 1.6 | 08-16 | synthesis | — | one table | **0 references repo-wide**; "after 2 bursts" |
| GAP_REGISTRY.md | 1.6 | 08-16 | synthesis | — | one table | **0 references repo-wide** |
| handoffs_HLE_Li2021.md | 1.7 | 08-10 | none (#17) | — | handoff | not a skill; misfiled |

Cross-set facts: lesson-ID prefixes are per file and unreconciled (L, G, D, F, R/R3a,
S, NR). No file has a "what may NOT be claimed" section (the per-burst notebooks do,
per their README). Nine of 27 files carry a lesson or defect ledger; 14 carry a
checklist; only two use numbered L-lessons. Eight of the ten deployed agents cite no
skill file at all (only skill-reader and figure-verifier do).

---

## §2 Defects the inventory found (facts; fixes are PROPOSALS in §5)

1. **Ledger marks steps 0 and 1 "✎ to be created"**; both files exist (BurstWalkthrough.md:105–106).
2. **Ledger says step 6 = "SpectralFitting.md (flagship, L1–L13)"**; the file is at L33 (:111).
3. **Lesson-ID collision**: SpectralFitting L31/L32/L33 (chain-gate, railed nuisance, absolute AIC) vs Temporal L31/L32/L33 (different lessons). A citation "L32" is now ambiguous.
4. **Temporal's lessons are out of order** (L29, L33, L26, L31, L32) and L31 is "PROPOSED pending PI" inside the active body (Temporal.md:253).
5. **Step 8 has two definitions**: ledger = "νFν panels & residual reading" (:113); AgentArchitecture per-step roster = "products" (:93).
6. **Step 8 has no owning skill file** while five producer scripts (41, 41b, 41c, 41d, 41e) and four design notes exist (`notes/CODEX_DISPLAY_20260813.md`, `MONTAGE_DEFECTS_20260813.md`, `THREEML_NATIVE_NUFNU_20260813.md`, `CODEX_SED_CONVENTIONS_20260814.md`).
7. **Three authorities for background selection**: repo-root `BACKGROUND_SELECTION_PROCESS.md` (15.3 KB, cited by AGENTS.md:321), `dev/ai_guides/background_selection.md` (20.8 KB, in the ledger), `KHUSHBOO_BACKGROUNDS.md` (4.0 KB); 560 diff lines between the first two.
8. **Two step decompositions of one pipeline with no precedence**: `dev/AUTHORITATIVE_PIPELINE.md` (locked 06-26, cited 3× in AGENTS.md) vs the ledger.
9. **R-item namespace collision**: `dev/GUI_REQUIREMENTS.md` R-BG-nn vs `ReportSpec.md` R1–R5.
10. **Orphans**: ASSUMPTION_REGISTRY.md and GAP_REGISTRY.md (0 references); handoffs_HLE_Li2021.md (a handoff, not a skill).
11. **Cross-cutting gates absent from the ledger**: FigureVisionQC, ReportSpec, ShippingGate, RefereeLoop, the register (distillation) — the ledger indexes steps only, so a reader opening "the ledger" never meets them.
12. **Precedence unstated** for the two global defaults the user's CLAUDE.md imposes: `~/Desktop/Projects/WritingHelper.md` (prose; Two_Breaks declares no override) and `reference_general_figure_style.md` (Figures.md is the override layer but neither file says so).
13. **The register ID collision of 2026-09-01** (two sessions minted NR-41; fixed a9c7250 + `tests/test_register_ids.py`) is the same defect class as items 3 and 9: IDs allocated by recall, not from disk.

---

## §3 Pre-existing skill-gap ledgers (read these into the discussion, do not redo them)

- `notes/skills_from_Yu2019.md` (11.2 KB, 08-09): "turn what a scientist NOTICES while
  reading a paper into explicit, reusable AI skills", status ✓ HAVE / ◐ PARTIAL / ✗ MISSING.
- `.claude/skills/grb-two-shock-analysis/` (24 numbered reference files) — items 14
  (detector + LAT quality) and 24 (Bayesian-blocks T90 audit) overlap ledger steps 2, 5, 7.
- `~/Desktop/LATBright/skills/` — gcn_intelligence (the named seed of step 0),
  pulsewise_lag, clean_pulse_selection, bibliography_apj, tables_apj map onto steps 0, 7, 9.
- `AgentRoster.md` A1 (:47–90): the skill→agent routing table and its Honest limits
  ("checklist compliance unverified downstream").

---

## §4 Candidate NEW skills (the "write more skills" list) — PROPOSALS

Ordered by how directly they serve the PI's program. Each names what exists on disk,
so writing is consolidation, not invention. Shape for all: the user-level skill
convention (Purpose · Inputs · Outputs · Phases with commands · QC checklist ·
Pitfalls · Hand-off), plus a **"What may NOT be claimed"** section, plus a numbered
lesson ledger with a file-unique prefix (see §5.2).

| # | skill | step / action | what exists on disk | why now |
|---|---|---|---|---|
| N1 | **SEDPanels.md** | step 8 (νFν panels, residual reading, montages, param-evolution) | scripts 41/41b/41c/41d/41e; the strict-XSPEC rulings (2026-08-14) and the S1–S6 standing contract in FigureVisionQC.md:55; SpectralResidualReview.md; four design notes; VISION_QC rounds | the one homeless ledger step (§2.6); the case study needs it |
| N2 | **RunProvenance.md** | action: launch a producer / record a run | NR-7 (invocation recorder), NR-12 (resource claim), NR-2 (seed), the dispatch plan + P9 hook, `results/campaign/CAMPAIGN_COMMIT_PIN.json`; the #21 refit of today has NO provenance json | Codex's missing family "launch/execute"; the gap is live on #21 right now |
| N3 | **Promotion.md** | action: finalize / promote / quarantine / invalidate | promotion receipts, quarantine manifests, NR-46 read-path vacancy, NR-19 cascade, `dev/invalidate_downstream.py`, `dev/live_report.py` stamps | Codex: "the most important missing verb"; the step-6 CONFLICT-6 (which table is binding) is exactly this |
| N4 | **Distillation.md** | action: close an incident | register header rule, AgentRoster A14 routing table (:490), `.claude/agents/distiller.md`, `tests/test_register_ids.py`, BURST1_LESSONS taxonomy | the ID-allocation defects (§2.3, §2.9, §2.13) show the procedure is unwritten |
| N5 | **ReportAssembly.md** | step 9b: assemble REPORT / paper from products | ReportSpec.md (the contract R1–R5), scripts 44/45/48, the per-burst paper chain in `dev/`, `notes/WRITING_TEMPLATE_li2021.md`, `.claude/skills/scientific-draft-writing/` | ReportSpec says WHAT must hold, nothing says HOW to build; the paper is item 4 of the program |
| N6 | **Writing.md** (project override) | prose | `~/Desktop/Projects/WritingHelper.md` (global default), Li+2021 template, PhD-1 audience rule (memory), loaded-word table | precedence unstated (§2.12); "Step-10 Writing planned at #20 checkpoint" (memory) — #21 is done |
| N7 | **Reconciliation.md** | blind-first compare → diff → attribute → distill | currently the head of SpectralFitting.md ("the skill: blind-reproduce→diff→reconcile→distill") + BurstWalkthrough blind-first rules + `notes/reconciliation/<trig>.md` records | separating it shrinks the 79.5 KB flagship and gives step 9's literature verdict its own procedure |
| N8 | **CaseStudy.md** | the PI's item 4: consolidated pipeline end-to-end on ONE burst → the paper's demonstration | AgentSkeleton §3 workflow set, FreshSessionBoot boot ritual, the #21 walkthrough as the live template, `notebooks/walkthrough/<trig>/` per-step notebooks | it is the next program item; writing the protocol first is what "discuss then run" means |
| N9 | **Release.md** | action: present / send / release a bundle | ShippingGate.md checklists, R5 manifest, `hooks/no_unverified_figures.py`, Khushboo release bundles (`handoff_background_approval/`) | Codex family "present/send/release"; could instead be a merge of ShippingGate into FigureVisionQC + ReportSpec (§5.5) |

Not proposed now (belongs to program item 5, domain tools): photospheric diagnostics
(#43), lag–MVT redo, two-shock model tests, population census rules.

---

## §5 Structural decisions to discuss FIRST (they shape every edit below)

### 5.1 The ledger becomes the single index
PROPOSAL: the BurstWalkthrough ledger lists every skill file: fix ✎ on steps 0/1; step 6
line → "SpectralFitting.md (L1–L33)"; add rows for the cross-cutting gates (FigureVisionQC,
ReportSpec, ShippingGate or Release, RefereeLoop, Distillation) under a "cross-cutting"
band; resolve step 8's two definitions (ledger "νFν panels" vs roster "products") by one
PI word; state precedence over `dev/AUTHORITATIVE_PIPELINE.md` (historical, locked
06-26) in one line.

### 5.2 One lesson-ID namespace
Today: L (two files, colliding), G, D, F, R, R-BG, S, NR. PROPOSAL, two options:
(a) **global L-numbers** across all skill files, allocated max+1 from disk, one test
guards uniqueness (extend `tests/test_register_ids.py` to L-IDs); or (b) **per-file
prefixes made unique** (SF-31, TM-31, LH-Tn, GC-n, DI-n, RS-n …) with a one-line prefix
table in the ledger. (b) keeps existing citations readable; (a) matches how the PI
already cites ("L28", "L32"). Either way the Temporal/SpectralFitting L31–L33 collision
is resolved by renumbering the LATER-written set (Temporal's, 08-31) and leaving a
tombstone line.

### 5.3 One skill shape
PROPOSAL: adopt the user-level convention (Purpose · Inputs · Outputs · Phases · QC
checklist · Pitfalls · Hand-off) + "What may NOT be claimed" + lesson ledger + newest-first
precedence banner (SpectralFitting.md:2–5 already has one). Existing files are brought
to shape only when next edited, never in a bulk pass (the 40→26-page lesson).

### 5.4 One authority per decision
PROPOSAL: background selection → `dev/ai_guides/background_selection.md` is the law;
`BACKGROUND_SELECTION_PROCESS.md` becomes a pointer or is folded in (its 560 diff lines
reviewed first, nothing lost); `KHUSHBOO_BACKGROUNDS.md` stays a task brief.
GUI R-items renamed G-… or kept with the "R-BG-" prefix declared in ReportSpec.

### 5.5 Retire, move, merge
- ASSUMPTION_REGISTRY + GAP_REGISTRY: fold into a synthesis skill (the Layer-4
  SCIENCE_INTERPRETATION engine input, memory 2026-08-16) or delete — PI's call.
- handoffs_HLE_Li2021.md → `notes/handoffs/`. CODEX_QUOTA_DISCIPLINE → `dev/ops/` or
  into RefereeLoop's machinery section. PI_REVIEW_PROTOCOL → a section of BurstWalkthrough.
- ShippingGate.md: keep the product-typed checklists, point verification duties at the
  roster verifiers (or become N9 Release.md).
- BURST1_LESSONS.md: fold bursts #2–#21 catches in, or freeze it as the burst-1 record
  and start a campaign-wide catch ledger.

### 5.6 The action layer (Codex r2) — where it lives
Codex: rules attach to actions; a flat `action → rule IDs` table is right; do NOT build
it standalone before rule IDs exist and something makes it fire. PROPOSAL: 5.2 first
(rule IDs unique), then an **ActionIndex section in AgentArchitecture.md** (routing only,
IDs not text), consumed by skill-reader at step open and by the queue manager when built.
No new file, no new actor.

---

## §6 Proposed discussion order (file by file) — SUPERSEDED 2026-09-02 by decisions 4–5: existing files stay as they are; rounds later. The live agenda is the INTERPRETATION skill family (see the plan document).

1. §5.1–5.2 (ledger + IDs) — two decisions, unlock everything.
2. Per-step, in step order: LiteratureHarvest → GCNIntelligence → DataInventory →
   detector → background (+5.4) → source → Binning → SpectralFitting (+N7 split) →
   Temporal (+L renumber) → [step 8 = N1 new] → qc_flagging (+N5).
3. Cross-cutting: FigureVisionQC + Figures (+precedence) → ReportSpec (+N6 Writing) →
   ShippingGate (+N9) → RefereeLoop → AgentArchitecture/Roster/Skeleton/Boot (these
   belong to program item 2, the agent merge — discussed there).
4. New: N2 RunProvenance, N3 Promotion, N4 Distillation, N8 CaseStudy.

Each item: I present the file's purpose, its defects, the proposal; the PI rules; the
edit is made and a one-line entry lands in this document's log (§7) before the next.

## §7 Decision log (appended as we go)
| when | file | PI ruling (verbatim) | applied in |
|---|---|---|---|
| 2026-09-02 | BurstWalkthrough.md ledger | "Yes, one index" (decision 1) | ledger: ✎ marks cleared on steps 0/1; step 6 L1–L33; cross-cutting band (FigureVisionQC, ReportSpec, ShippingGate, RefereeLoop, register); precedence over AUTHORITATIVE_PIPELINE stated |
| 2026-09-02 | all skill files | lesson IDs "it should be specific to the skills" (decision 2) | L stays SpectralFitting's; Temporal L29/L33/L26/L31/L32 → TM1–TM5 (file order, tombstoned); prefix table in the ledger; live citations updated (AgentArchitecture, AgentSkeleton, port-verifier); frozen records, logs, memory notes and the figure-rendering scripts (47b/47c/40/run_p2) left as-is — tombstone resolves them; tests/test_lesson_ids.py guards |
| 2026-09-02 | step 8 | "νFν panels + residual reading" (decision 3) | ledger step-8 row → ✎ SEDPanels.md (N1); AgentArchitecture per-step roster row 8 re-titled; tables and report assembly = step 9 |
| 2026-09-02 | LiteratureHarvest.md (decision 4) | REDIRECT, verbatim: "We look at the literature, keep it to the end where if there is literature on the event we are doing we then compare our results with them and reconcile any differences and at the same time there is different thing I guess which is literature in general and that is required to build skill files to intrepret and put our analysis to use like Amati correlation, or calculations from all the things we got, basically some physics, whether it goes even into unsupervised learning those people did on some of the properties of GRBs, we should be able to provide any number for any kind of analysis people want to perform on our GRB" | no shape pass applied. Two consequences recorded: (i) per-EVENT literature = an END step (compare + reconcile), not step 0b — ledger re-order to be confirmed before applying (the 0b numbering was the PI's own 2026-08-30 ruling and live_report.py keys on it); (ii) the NEW skills to write are INTERPRETATION skills built from the GENERAL literature (energetics, correlations, physics estimates, population/unsupervised analyses) → plan in notes/INTERPRETATION_SKILLS_PLAN_20260902.md |
| 2026-09-02 | all existing skill files (decision 5) | verbatim: "this was that if we keep doing burst #1, #2, #3... then by #20 our skill files will probably have not much to add, but we didn't do that... so skill files stays as they are, and we will do rounds to improve them and consolidate them" | existing skill files are NOT restructured now; §4 N1–N9 and §5.3–5.6 become ROUND items for later; the harvester tool is not built now |

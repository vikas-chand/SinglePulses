---
name: scientific-paper-reading
description: Use to read, triage, deeply analyze, compare, and extract project and writing lessons from scientific papers; maintain a ten-paper daily ledger; distinguish source claims from critique, inference, and new hypotheses; and promote only project-changing insights into active skills.
metadata:
  version: 1.0.0
  domain: scientific-research
---

# ⚠ LOCAL WIRING (Two_Breaks, 2026-08-09) — read before using this skill

For papers that bear on a burst we analyse, the binding protocol is **P0–P6 in
`dev/ai_guides/SpectralFitting.md`**, not this skill's generic workflow:
P0 freeze our numbers -> P1 verify published values at SOURCE (snippet-backed) ->
P2 frame-align (L21: Ep-vs-Ec, sign, band, interval AND its T0, detector set) ->
P3 diff -> P4 test explanations -> P5 attribute (we-wrong / they-wrong / frame-difference)
-> P6 verdict, written to `notes/reconciliation/<trigger>.md`.
This skill governs GENERAL reading (triage, breadth, ledger); the reconciliation protocol
governs any paper whose numbers touch ours. Where they differ, P0–P6 wins.

Also binding here:
- **L22**: a published component claim is a claim about the CONTINUUM it was measured
  against; verify chained citations at the PRIMARY source (Li 2019 -> Iyyani 2016 was wrong).
- **L23**: agreement can be a shared bad minimum — name the deepest primitive two paths
  share before counting agreement as verification.
- **Stamp at merge (added 2026-08-10 after missing Lu+2018):** when Vikas delivers a
  reading package for a paper, that IS the read — stamp `read=Y` + date in the corpus
  ledger AS PART OF the merge, never as a separate later step. A merged package with an
  unstamped ledger is a bookkeeping bug.
- **Corpus ledger**: `Skills_training/corpus_index.csv` (`read`, `read_date`). Fetch the
  PUBLISHED version when ADS reports `PUB_OPENACCESS`; keep the arXiv copy for extraction.
- **Idea bank stays LOCAL** (`notes/PROJECTS_registry.md`, and the gitignored
  `11_project_idea_bank.md`) — never pushed.
- **Reading cadence (Vikas, 2026-08-09):** per burst, read what THAT burst needs; then one
  paper from a DIFFERENT methodological family (different statistics or competing model
  family — e.g. Yu+2019 Bayesian/DIC or Ravasio 2SBPL-first vs the Lu/Zhang χ²/RMFIT series)
  before returning to the same group. Reason: the Comprehensive-Analysis papers are one
  group/toolchain — reading them back-to-back anchors their conventions as defaults (L23
  applied to reading). Interleave to break the anchor.
- ⚠ The "ten papers per day" default is this skill's suggestion, NOT a project target.
  The campaign cadence is Vikas's: read what the current burst needs.

# Mission

Turn paper reading into cumulative scientific capability rather than passive summarization.

For each paper, preserve four channels:

```text
SOURCE     what the paper actually states or shows
CRITIQUE   weaknesses, inconsistencies, and methodological questions
PROJECT    concrete changes to active analysis or code
DISCOVERY  new hypotheses, jumps, and future experiments
```

A fifth channel records **WRITING MOVES** for the scientific-draft-writing skill.

# Reading depths

## Deep

Read equations, tables, figures, assumptions, appendices, and primary references. Use for core papers.

## Structured

Read abstract, introduction, methods, principal figures/tables, discussion, and limitations.

## Triage

Determine question, method, result, project relevance, and whether deeper reading is warranted.

# Ten-paper daily target

Default mix:

```text
2 deep
3 structured
5 triage
```

The target is ten papers **processed**, not ten papers read line by line.

# Workflow

1. Identify the paper and reading depth.
2. State the paper's question in one sentence.
3. Extract data/sample, methods, statistics, results, assumptions, limitations.
4. Inspect the most informative figures and tables.
5. Separate source claims from your critique.
6. Ask what would falsify the main claim.
7. Connect the paper to active projects.
8. Generate at least one conceptual jump or discriminating test when justified.
9. Record useful writing moves without copying prose.
10. Decide whether to update an active skill, idea bank, code task, or bibliography.

# Anti-anchoring rule

Previous skills and papers are priors, not prisons. The reader may challenge them, propose a new statistic, invent a new model, or reframe the project. Novel ideas remain exploratory until calibrated and independently tested.

# Output

Use `templates/paper_entry.md`. For the daily session, update `templates/daily_ledger.md`.

# Promotion rules

Promote a lesson to an active project skill only if it changes:

```text
analysis inputs
method or statistic
quality control
model comparison
physical interpretation
reproducibility
manuscript structure
```

Send speculative but non-blocking ideas to the idea bank.

---
name: scientific-draft-writing
description: Use to draft, revise, critique, and structure scientific prose using a layered system of universal prose principles, project-specific overrides, voice fingerprints, and task helpers for abstracts, introductions, methods, results, discussions, captions, decision summaries, and bibliographies.
metadata:
  version: 1.0.0
  domain: scientific-writing
---

# ⚠ LOCAL WIRING (Two_Breaks, 2026-08-09) — read before using this skill

This skill is the LAYERED SCAFFOLD. The project's actual prose authority already exists and
takes precedence; do not duplicate it here:

- **Layer 1 (foundation) = `~/Desktop/Projects/WritingHelper.md`** (58 KB, cross-project).
  Target voice = Principe et al. 2023; density metrics (clause-hinges/100 w, nominalizations
  and passives per 1k) BEFORE diagnosing; the loaded-word table (e.g. `prompt` collides with
  prompt emission -> use `contemporaneous`). This file's `references/01_foundation_prose_style.md`
  is a SUMMARY of that, never a replacement.
- **Layer 2 (project overrides)** = audience is first-year PhD students (ONE plain-language
  explanation per concept at first use, additive edits only) + style model **Li et al. 2021
  ApJS 254,35**, template `notes/WRITING_TEMPLATE_li2021.md`.
- **Voice fingerprint**: `references/04_voice_fingerprint_template.md` starts EMPTY by design.
  Populate it only from prose Vikas has approved — never from a source paper.
- **Bibliography**: ADS API is the DEFAULT and hand-writing journal-article BibTeX is
  FORBIDDEN (token in `~/Desktop/Projects/FXTs/.env`). Full protocol:
  `~/Desktop/LATBright/skills/bibliography_apj.md`. `templates/bibliography_helper.md`
  defers to it.
- **Captions**: retrieve with `caption-suggest` first (`~/Desktop/Projects/CaptionHelper/`),
  as a VOICE CORPUS not a phrase bank.
- **Tables**: `~/Desktop/LATBright/skills/tables_apj.md`.
- **Manuscript edits**: the `/paperedit` protocol (one gated `chng` at a time) governs.
- **Machine gates**: the Handbook Block-5 writing gates (prior_work gate + anchor linter —
  every number in prose must anchor to a pipeline product) are BINDING for this project.

# Architecture

## Layer 1 — foundation

Universal scientific prose and argument principles.

## Layer 2 — project overrides

Notation, terminology, evidential standards, journal constraints, preferred ordering, and project voice.

## Layer 3 — task helpers

Specialized templates for a caption, abstract, methods paragraph, decision summary, bibliography, and other local tasks.

The voice fingerprint sits between Layers 2 and 3 and may evolve over time.

# Core rule

Learn **rhetorical moves**, not strings of source prose. Never imitate a paper by copying its sentences. Record:

```text
what the move does
why it works
when it is appropriate
how it can fail
```

# Reasoning modes

Before writing, identify one mode:

```text
draft
rewrite
line edit
structural edit
critique
compress
expand
translate technical reasoning into prose
caption
bibliography synthesis
```

Do not silently change scientific content during a style edit.

# Source fidelity

Separate:

```text
measured result
model-derived result
assumption
literature claim
project inference
speculation
```

Use calibrated verbs. Never upgrade “compatible with” into “demonstrates.”

# Default drafting workflow

1. Identify audience, section, and purpose.
2. Write the paragraph's claim in one sentence.
3. List evidence and caveats.
4. Choose a rhetorical blueprint.
5. Draft with one logical function per sentence.
6. Check transitions and referents.
7. Remove inflation, repetition, and empty scene-setting.
8. Verify symbols, units, intervals, and citations.
9. Apply project override and voice fingerprint.
10. Return a clean draft plus a short change rationale when editing.

# Supporting files

- `references/01_foundation_prose_style.md`
- `references/02_rhetorical_moves_bank.md`
- `references/03_grb_project_overrides.md`
- `references/04_voice_fingerprint_template.md`
- `references/05_source_pattern_log_siddique_2022.md`
- `templates/paragraph_blueprints.md`
- `templates/abstract_helper.md`
- `templates/introduction_helper.md`
- `templates/methods_helper.md`
- `templates/results_helper.md`
- `templates/discussion_helper.md`
- `templates/caption_helper.md`
- `templates/decision_summary_helper.md`
- `templates/bibliography_helper.md`

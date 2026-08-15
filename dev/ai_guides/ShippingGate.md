# Skill: the SHIPPING GATE — verify every product before it ships

**Born:** 2026-08-12, from the bn200524211 montage incident: a delivered figure carried a
winner label (SBPL) contradicting the engine's stored winner (Band+BB), a collapsed panel
refit, and 68% bands displaced off their own best-fit curves — caught by Vikas's eyes, not
by any check. Vikas: *"we need to have an agent that always checks if the result is correct
before we ship it."*

**Purpose:** nothing outward-facing ships unverified. "Ship" = SendUserFile to Vikas, a gate
presentation, a git push, a PR merge, a collaborator hand-off, a paper number.

**The independence rule (generator ≠ adjudicator):** the producer of a product never verifies
it in the same context. Machine checks run inline; judgment/vision checks run in a FRESH
subagent context given only the product + its primitives — never the producer's reasoning.
A verifier that inherits the producer's context inherits its blind spots.

## Product-typed checklists

### Fit tables / scorecards / summaries
- [ ] `tests/test_lessons.py` green on the guarded roots (regression layer)
- [ ] margin arithmetic spot-re-derived from the ecsv by a fresh pass (the Codex Task-1
      pattern, sampled — full blind re-derivation for anything census-grade)
- [ ] union BB rule + child-VALID + L28 stamps present (audit MF-1 class)
- [ ] catalog inputs validated adjudication-aware (`scripts/43_catalog_validator.py`)

### Figures (montages, panels, learning curves, TikZ)
- [ ] **MACHINE:** every label on the figure that restates a table value (winner, AIC, kT,
      block interval) is diffed against the table — a label-table mismatch is a hard FAIL
      (the bin7 incident; wire as `PANEL_AIC vs ENGINE_AIC` stamps in scripts/41)
- [ ] **VISION (fresh-context agent):** bands bracket their curves; residual panels show no
      coherent |run| ≥ 3σ on a "good" fit; axes/limits sane; no overlapping/clipped text
      (the Fig-1 TikZ incident); winner labels legible and consistent across panels.
      **The runnable brief + recording rule: `FigureVisionQC.md`** — verdict lands in
      `<products>/VISION_QC.md`; `scripts/45` stamps it into PRODUCTS.md (PENDING if absent)
- [ ] error-band sampling did not rail (>1% sample loss ⇒ band suppressed + stated)
- [ ] figure style conforms to the reference guide (serif/STIX, ticks in, 300 dpi)

### Records / notes / dossiers (anything with numbers)
- [ ] every number anchors to a named product file (anchor-linter discipline, Block-5)
- [ ] every published number carries frame labels (L21 + T9 component coverage)
- [ ] provisional numbers flagged provisional; ties phrased as ties (graded evidence, L16)

### Citations / reading lists / bibliography
- [ ] every bibcode resolved against ADS (identity), never hand-written
      (`scripts/ads_verify.py` once merged; the four-form + Scholar-resolve rules)

### Code / skill changes
- [ ] `py_compile` + full lesson suite before the next pipeline invocation (a running chain
      loads the engine fresh per burst — a syntax error mid-sweep kills every later burst)
- [ ] skill edits: additive, provenance-stamped, cross-referenced from the authority files

## Stamp
Every gated product records: `VERIFIED_BY` (agent/human + context type), `VERIFIED_UTC`,
`CHECKLIST_VERSION`, defects found + disposition. A product that fails ships only with the
failure stated on its face (e.g. "montage: display-layer defects known, engine numbers
authoritative") — or not at all.

## Honest limits
The gate catches producer-vs-primitive divergence and display-layer lies. It CANNOT catch
errors in shared upstream primitives (same tables, same DRMs — that is what cross-system
audits and cross-instrument checks are for), and vision checks are probabilistic. Defense in
depth: machine stamps → fresh-context verifier → periodic Codex audit → Vikas.

## Hand-off
Feeds every step that produces an artifact; BurstWalkthrough rules reference this gate.
The managed-agents mapping (paper Table 2): this is the `verify(product) → stamp | defects`
interface — the adjudicator component the coded-agent world doesn't ship.

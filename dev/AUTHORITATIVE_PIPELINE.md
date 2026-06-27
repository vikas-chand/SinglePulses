# Authoritative pipeline — approval → binning → fits

Agreed end-to-end flow for the final (paper) run. Locked 2026-06-26 with Vikas.
Everything downstream is provisional until Stage 1 (human approval) is complete.

## Stage 1 — Human approval (NEW / extended; the only real build left)

THREE things get approved, each row STAMPED so approval is auditable from the file.
Per Vikas (refined 2026-06-26): **human approval is NOT mandatory — an AI may approve**,
but there must be a **settable flag/gate recording who/how**. Ideally the AI runs the
codes interactively (as in our sessions) and SETS the flag per the user's choice.
So the stamp records the approver (human name OR "Claude/Codex (AI)") and an approval
MODE/gate (e.g. human_gui / ai_vision / ai_auto). This matches the existing AI-
selection preference (AI selects; optional human gate). The AI-vision selection path
already exists (00_prototype Phase-2: AI reads LC PNGs -> ai_selections.json).

1. **Detectors** — reuse the existing GUI `00_prototype_one_burst.py:
   pick_detectors_with_angles_gui` (CheckButtons + POSHIST ≤50° NaI angle math).
   Output: the approved detector SET per burst.
2. **Background windows** — reuse `scripts/30` BackgroundSelector, per approved
   detector (pre + post). Already built + stamped tonight.
3. **Source / emission interval** — **explicit, per-burst** (Vikas's choice): user
   clicks emission start + stop ONCE per burst on the brightest detector's light
   curve. Emission is a burst property, not per-detector. Replaces the implicit
   `[pre_stop, post_start]` gap and the `emission_window` heuristic.

### Plan for the unified approval driver
A single driver that, per burst, runs: detector-approval → (per approved det)
background-approval → source-approval. Reuses the two existing GUIs; the only new
GUI piece is the per-burst source marker (2 clicks on the brightest-det LC).

### Output schema (one stamped catalog)
`results/background_intervals.ecsv`, per (trigger, detector) row:
```
TRIGGER_NAME, DETECTOR, BKG_NEG_START, BKG_NEG_STOP, BKG_POS_START, BKG_POS_STOP,
SRC_START, SRC_STOP,          # per-burst emission window (same across a burst's dets)
APPROVED_BY, APPROVED_UTC, WINDOW_SOURCE
```
Detector approval is implicit in which (trigger, det) rows exist (only approved dets
are written). SRC_START/SRC_STOP are denormalized (repeated per detector of a burst).

## Stage 2 — Binning (BUILT: scripts/27b_reblock_3ml.py)

3ML Bayesian blocks with `use_background=True` **+** significance binning = the
HYBRID: BB for structure, then merge any block below SIGMA_FLOOR (=5, significance-
only) per the trim-edges-then-merge-interior scheme. Per-block significance from
3ML's own `Significance.li_and_ma_equivalent_for_gaussian_background`.
- **Change needed:** read the explicit approved SRC_START/SRC_STOP from the catalog
  and bin within that, INSTEAD of the `emission_window` heuristic. (One-line swap of
  the `src_lo, src_hi` source in `reblock_burst`.)
- Run: `python scripts/27b_reblock_3ml.py --bkg results/background_intervals.ecsv --out <fresh>/clean_blocks`

## Stage 3 — Spectral fits (BUILT: scripts/10 + scripts/29 driver)

The 6 GBM models (Band, CPL, SBPL, DSBPL, Band+BB, CPL+BB) per block; winner by
ΔAIC≥10 (with the physical-validity gate + DSBPL multistart). Driver:
`python scripts/29_refit_clean.py --bkg-file results/background_intervals.ecsv ...`

## Built vs to-build
| Stage | Component | Status |
|---|---|---|
| 1 | detector-approval GUI | exists (00_prototype), needs wiring into scaled driver + stamp |
| 1 | background-approval GUI | BUILT + stamped (scripts/30) |
| 1 | source-approval (per-burst clicks) | TO BUILD (new GUI step) |
| 1 | unified approval driver + schema | TO BUILD |
| 2 | BB+significance hybrid | BUILT (27b); needs SRC_START/STOP wiring |
| 3 | 6-model fits + selection | BUILT (10/29) |

## Execution model — AI agent drives it (Codex local OR Claude)
Target (Vikas 2026-06-27): Khushboo runs **Codex locally in the terminal**; it should
"understand our repo and execute just like you [Claude]." Codex-local is a PEER to how
Claude Code operates here — it has a display (GUI *or* vision works), installs deps,
fetches data, reads the LC PNGs, reasons, SETS the gate flag, and runs the scripts.
So the env-weight and GUI/cloud worries are moot; the approval is ai_vision-first
(AI reads PNGs, proposes detector/bkg/source, sets gate per the user's choice), with
the click-GUI as an optional human override.

### Repo legibility (NEW requirement — the piece that makes "just like you" real)
A fresh agent (Codex, or a fresh Claude) has NEITHER our chat context NOR Claude's
private ~/.claude memory. Every decision made in-session (5sigma significance-only
hybrid, explicit per-burst source, the AI-or-human gate, the run order, env setup)
must therefore live **in-repo and self-contained**:
- **`AGENTS.md`** at repo root (Codex's convention, ~ CLAUDE.md): orients any agent to
  the repo + pipeline (approve -> bin -> fit), gate semantics, run order, env.
- Upgrade `handoff_background_approval/SKILL_*.md` from background-only to the WHOLE
  chain, ai_vision-first.
- TO BUILD alongside the approval driver (so docs point only at code that exists).

## Notes
- GUI steps can't be smoke-tested headlessly — verify on a live display
  (`--limit 1`) before a full pass.
- Bridge/refactor (shared package with PulsewiseAmatiYonetoku, which already forked
  the detector picker) is the GRB_Handbook consolidation — deferred, not forgotten.

# PLAN: ship the science paper (two_break.tex)

Written 2026-07-18 (Vikas: "write a plan and set a goal to complete the paper").
Successor to `PLAN_review_to_science.md` (which covered review→science wiring;
still valid for mechanics). This is the END-GAME plan: current state → submitted.

**GOAL: submission-ready draft (all real numbers, no placeholders) by
2026-08-22 (5 weeks). Rate limiter = Khushboo's 65 Stage-1 selections.**

---

## Current state (2026-07-18, verified)

| Track | State |
|---|---|
| Stage-1 approvals | AI-consensus 106/106 stamped; HUMAN arm: 13 LLE bursts (Vikas) done; 65 remain (Khushboo worklist pushed) |
| Spectral prototype | 13 LLE bursts, all-model menu: v2 (GBM+LLE) done; v3 (+LAT) running |
| Model doctrine | 24-model registry + ΔAIC≥10 top-two + degeneracy classes BUILT (`scripts/model_registry.py`); scripts/31–33 integration PENDING |
| Temporal | Canonical Bala MVTfermi engine BUILT today (handbook `mvt_engine`); golden run in flight; 106-burst run ≈ 6–12 h once cleared |
| Paper | Intro (shape-hunt) ✓; §3 Temporal skeleton ✓ (numbers `\PHt{}`); Methodology/Results/Discussion = OLD framing, rewrite pending |
| Known debts | 59 stale fits (windows moved post-fit); 130427A analyse 2nd pulse; BB seed-poisoning re-derivation folded into full re-fit |

## Phase A — close the prototype loop (this week, no external deps)
1. v3 (+LAT) fits complete → registry census on the 13; v2↔v3 diff = "what LAT adds" (does it break the 160625B flavor tie?). → feeds Methods+Results.
2. MVT: golden bn110721200 → Codex audit #3 verdict → 6-burst smoke matrix → **106-burst MVT run** (needs only the AI-consensus catalog — not blocked on Khushboo).
3. Temporal batch: T90/T50, pulse fits, lags over 106 via handbook chain → fills §3 numbers.
4. **DECISION (Vikas): structural degeneracy classes** — merge continuum flavors? (pending question)
5. **DECISION (Vikas): headline** — census / shape-migration with phase / high-E+nulls.

## Phase B — full-sample production (gated on Khushboo)
1. Khushboo: 65 Stage-1 selections (her worklist; INSTRUCTIONS + BRIEFING pushed).
2. Ingest → `background_intervals_human.ecsv` full 106 (arm-separated from AI catalog).
3. Re-block (27b + 27c where LLE) → re-fit ALL 106 with the full menu
   (subsumes the 59 stale fits + 130427A-2nd-pulse + BB multi-start re-derivation).
   Budget ≈ 4–6 days on 12 cores. Fresh out-root, provenance-stamped.
4. Two-tier (coarse LLE/LAT + fine GBM) for the LLE subset via 27c.

## Phase C — products (scripts, ~2 days after B)
1. `scripts/31` → registry-driven three-level census (exact/class/family + flavor-degenerate stat).
2. `scripts/32` → figures into `two_break_figures/` (incl. new: phase-resolved shape migration; MVT(E); census bar).
3. `scripts/33` → machine tables; NEW temporal catalog table (T90/shape/MVT/lag per burst).
4. Ep–kT, νm–νc (decisive-only, true D'Agostini), Single-vs-Rest nulls (3-comp, MeV absorption).

## Phase D — writing + QC (~1.5 weeks, overlaps C)
1. Methodology rewrite: wide-band data (GBM+LLE+LAT), two-tier binning, 24-model menu + doctrine + degeneracy classes, temporal chain, TLDB-equivalence. (Per `PAPER_shaping_from_codex.md`.)
2. Results/Discussion in shape-hunt framing; temporal §3 numbers in; Single-vs-Rest framing.
3. Bibliography: verify EVERY user-named cite vs ADS (standing rule; Bala2025 done).
4. QC: full Codex ultra audit of numbers-vs-scripts; my adversarial pass; nbconvert-free notebook check.
5. Khushboo + Jagdish read; Vikas final voice pass; submit (ApJ).

## Decision register (all Vikas's; none block Phase A start)
- D1 structural classes (Phase A.4) — needed before final census.
- D2 headline (A.5) — needed before Results writing.
- D3 old scope OPENs: variability section? redshift subset? atlas appendix? (default: no/no/no for THIS paper.)
- D4 Bala coauthorship = GRB_Handbook only, NOT this paper (default; confirm).
- D5 submission target journal ApJ (default per drafts).

## Weekly goal line
- W1 (→07-25): Phase A complete incl. 106 MVT run; Khushboo started.
- W2 (→08-01): Khushboo done + ingest; full re-fit launched.
- W3 (→08-08): re-fit + products; census frozen.
- W4 (→08-15): full draft, all numbers real.
- W5 (→08-22): QC + coauthor pass → **submission-ready**.

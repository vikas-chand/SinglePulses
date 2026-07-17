# GUI Requirements — Stage-1 Approval Instrument (`scripts/39_approve_all.py gui`)

> Written 2026-07-03 after Khushboo's first Linux field test (detector picker never
> appeared; window dead after a background refit; source marker has no buttons).
> This is the *"write cleanly what we want"* document: numbered, testable
> requirements for the three approval windows. **Khushboo co-authors**: OPEN items
> below are assigned; edit this file directly or add
> `dev/GUI_REQUIREMENTS_notes_khushboo.md` and we merge.

Tags: **[EXISTING]** already implemented+documented (pointer, no new work) ·
**[DECISION]** resolves a contradiction (ruling stated) · **[NEW]** fills a gap ·
**[OPEN]** to be decided (owner named). Phase column: P1 = shipped with this
commit series; P3 = implement after this spec is signed off.

## 0. Scope & freeze policy
This spec governs the three windows of `scripts/39_approve_all.py gui`:
**detector picker → per-detector background selector → source marker**, and their
lifecycle. Normative companions: `BACKGROUND_SELECTION_PROCESS.md` (Steps 1, 4, 5 —
selection *criteria*), `dev/ai_guides/` (judgement criteria), `dev/BENCHMARK_PLAN.md`
(raters + isolation), `handoff_background_approval/INSTRUCTIONS_KHUSHBOO.md` (ops).

**FREEZE:** while the 25-burst benchmark runs, selection *semantics* are frozen —
criteria, angle thresholds, seeds, the time-order rule, the 3ML two-stage polyfit,
and the stamp schema may not change. Allowed: crash/blocked-UI/lifecycle fixes,
louder messages, and *additive* audit fields. UX behavior changes (P3) land only
after both raters have finished or the tool-commit split is recorded (§6).

## 1. Session lifecycle (R-GL)
| # | Req | Tag/Phase |
|---|---|---|
| R-GL-1 | Window order per burst: picker → one background selector per selected detector → source marker → decision.json written → immediate ingest with the verdict printed. | [EXISTING] `39:gui_one/main` |
| R-GL-2 | **Quit** in any window aborts the whole burst; nothing is written for it. | [EXISTING] |
| R-GL-3 | **No silent path may alter what the rater is asked to judge.** Every fallback, skip, or auto-adoption prints an explanatory line naming the cause and the consequence. | [NEW] P1 (done) |
| R-GL-4 | If the burst has no source RA/DEC (`results/grb_sample.ecsv` missing or lacks the trigger): **hard stop** for that burst with a remedy message (`git pull` — the catalog is now tracked). An `--all` run continues to the next burst. *Decided 2026-07-03 (alternative was warn-and-continue).* | [DECISION] P1 (done) |
| R-GL-5 | If RA/DEC is known but angle computation fails (POSHIST download/network): loud boxed warning, picker skipped, continue with seeded pre-ticks. Offline ≠ stale clone. | [DECISION] P1 (done) |
| R-GL-6 | Each gui decision.json additionally records `"tool_commit"` (short git hash) so the benchmark can verify all raters used the same instrument. Additive; ingest ignores unknown keys (verified). | [NEW] P3 |
| R-GL-7 | Re-running gui on a burst that already has a decision.json: overwrite silently, or prompt? | **[OPEN — Khushboo]** |

## 2. Detector picker (R-DP)
| # | Req | Tag/Phase |
|---|---|---|
| R-DP-1 | Two-column hemisphere layout (LOW n0–n5+b0 / HIGH n6–nb+b1), labels carry angle + BCAT mark; both-sides selection warns once and requires a second Accept. | [EXISTING] `00_prototype:pick_detectors_with_angles_gui` |
| R-DP-2 | Pre-tick rules: NaI θ≤50°; BCAT rescue 50–60°; closest-BCAT fallback; matching same-side BGO; in gui mode only *seeded* detectors are pre-ticked and an unpaired BGO is un-ticked (Codex patch `d797029`). | [EXISTING] `BACKGROUND_SELECTION_PROCESS.md` Step 1 |
| R-DP-3 | A detector ticked without a background seed is allowed; its background is then drawn fresh in the selector (printed). | [EXISTING→documented here] |
| R-DP-4 | The picker MUST appear whenever gui mode runs. The only permitted skip is R-GL-5, and it must print exactly why. | [NEW] P1 (done via R-GL-4/5) |
| R-DP-5 | Detectors without TTE on disk are downloaded on Accept; a failed download prints and drops that detector. | [EXISTING] |
| R-DP-6 | **Window-close (×) on the picker = Quit the burst** (abort, nothing written). *Current behavior is the dangerous opposite — × silently accepts the ticked set. Decided 2026-07-03.* | [DECISION] **P3** |
| R-DP-7 | A no-angle picker variant (θ shown as `nan`, no source coords in the title) — needed, or is the R-GL-4 hard stop sufficient? (Guard the `src_ra:.2f` title crash if built.) | **[OPEN — Khushboo]** |

## 3. Background selector (R-BG)
| # | Req | Tag/Phase |
|---|---|---|
| R-BG-1..10 | Two-panel layout (LC + residual panel, top-capped at 10σ); gold pre/post intervals; red polyfit overlay; transient cursor line; 2-pixel click-vs-drag tolerance; bin snapping; time-order interval rule; Clear = wipe + 4 fresh clicks; toolbar zoom/pan guard (`isNormalMode`); buttons Clear/Accept/Skip GRB/Quit; keyboard adjust `a/s/d/f` + arrows ±1 bin, shift ±16, `esc` exits. | [EXISTING] process doc Step 4 + `00_prototype:BackgroundSelector` |
| R-BG-11 | The overlay/residuals come from the **3ML two-stage polyfit** (broadband LRT grade selection + per-channel refit) — *not* `numpy.polyfit(deg=2)`; the process-doc line saying otherwise is stale (correct in P3). | [DECISION] |
| R-BG-12 | The Stage-1 selector shows **no T90 shading** (`review_one_detector` passes `t90=None`); the T90 display capability exists only for legacy entry points. | [DECISION] |
| R-BG-13 | During a refit the GUI is **BUSY**: the status line says "Refitting… input paused"; all mouse/keyboard input is ignored; the window must respond to the next input within ~100 ms after the refit ends. | [NEW] P1 (done) |
| R-BG-14 | Input arriving during a refit is **dropped, never replayed** — Accept must always act on residuals the rater has seen. A held arrow key coalesces to ~1 refit per fit-duration (no cascade). | [NEW] P1 (done) |
| R-BG-15 | Window-close (×) = **Skip this detector** (not the burst), and the skip is printed. Codifies previous implicit behavior. | [DECISION] P1 (done) |
| R-BG-16 | Any polyfit/overlay exception is surfaced on the status line (type + message); the window stays fully usable (adjust, Clear, Skip, Quit). | [NEW] P1 (done) |
| R-BG-17 | Keyboard adjust requires that window to be placed first; pressing `a/s/d/f` before placement shows "(unset — place window first)". | [EXISTING→documented here] |
| R-BG-18 | Accept requires both intervals (status message otherwise). The 50–150 s/side width rule is **advisory** at Accept — warn only, or block? | **[OPEN — Vikas]** |
| R-BG-19 | Residual-panel y-limits after refit: currently `min(resid)−1 … min(max,10)+0.5`. Keep, or fix bounds across detectors? | **[OPEN — Khushboo]** |
| R-BG-20 | Between successive detector windows — and picker→first-detector and last-detector→source-marker — pending GUI events are **drained** (`_drain_gui_events()` = `plt.close('all')` + a Tk `update()`), so the just-approved detector's Tk window finishes its **deferred destroy** before the next `plt.show()`. Without it, on **Ubuntu/TkAgg** the approved window (e.g. n6) reappears as a **dead, non-interactive zombie** alongside the next detector (n7), forcing a manual ×. macOS/Qt: no-op. (Field bug, Khushboo, 2026-07-15.) | [NEW] P1 (done) |

## 4. Source marker (R-SM) — all P3 (rebuild)
| # | Req | Tag/Phase |
|---|---|---|
| R-SM-1 | Marked on the best-angle accepted NaI light curve (0.256 s bins); the suggested window is pre-shaded in gold. | [EXISTING] |
| R-SM-2 | Buttons **Accept / Clear** (same `fig.text(..., picker=20)` idiom as the background selector). Accept adopts the gold suggestion when there are zero picks, else the clicked pair; Clear resets. A clicked pair is shown as a red span + status line. | [NEW] **P3 — DONE** (commit 4aeba8d) |
| R-SM-3 | Click feedback: each pick draws a labelled line and a status line ("start = 12.30 s"). Third click: replaces the nearer pick, or is rejected? | [NEW] P3 + **[OPEN — Khushboo]** |
| R-SM-4 | **Real-time gap validation**: the allowed band `[max(pre_stop), min(post_start)]` over all accepted detectors is shaded; Accept refuses a pair outside it (ingest remains the backstop). Removes the current failure mode where a bad source silently rejects the whole burst at ingest. | [NEW] P3 |
| R-SM-7 | **Background context on the marker**: the reference detector's **just-approved** pre/post windows are drawn in green (with dashed gap-boundary lines at `pre_stop`/`post_start`) so the source is judged against the same background the rater accepted seconds earlier; the view is widened to cover them. `bkg=windows.get(nai_ref[0])` is passed from `gui_one` into `source_marker_gui`. Single-detector precursor to R-SM-4's multi-detector allowed-band. | [NEW] **DONE** (commit cca962c) |
| R-SM-5 | Window-close (×) without Accept **aborts the burst**; closing may not silently adopt the suggestion (adoption = explicit Accept with zero picks). *Until P3 lands, adoption-on-close prints loudly (P1, done).* | [DECISION] P3 |
| R-SM-6 | Picks snap to LC bins (parity with the background selector)? | **[OPEN — Khushboo]** |

## 5. Contradiction register (doc says / code does / RULING)
| Doc says | Code does | Ruling |
|---|---|---|
| "red `numpy.polyfit(deg=2)` overlay" (process doc Step 4) | 3ML two-stage polyfit | **Code is right** (R-BG-11); fix doc in P3 |
| "use `matplotlib.use('macosx')` not TkAgg" | TkAgg supported since keep-alive fix `00c40dd`; Linux runs use `MPLBACKEND=TkAgg` | **Doc stale**; fix in P3 |
| "NO T90 shading" | Stage-1 path shows none; legacy paths can | **Both true**; pinned as R-BG-12 |
| `--auto-approve` flag (process doc Step 4) | No such flag in `scripts/39` | **Doc stale** (legacy scripts only); mark in P3 |
| 6-column output schema (process doc Step 4) | 13-column stamped SCHEMA (`39:90–92`) | **Code is right**; fix doc in P3 |

## 6. Benchmark tool-freeze bookkeeping
Every rater records `git rev-parse --short HEAD` before their first and after their
last benchmark burst (table in `dev/BENCHMARK_PLAN.md`). All raters must be on the
post-fix commit **before** the 25-burst set begins; any earlier catalogs are
discarded or the commit split recorded. R-GL-6's `tool_commit` stamp makes this
machine-checkable.

## 7. Acceptance tests (map to the smoke checklist)
1. Fresh clone: `results/grb_sample.ecsv` present (`git archive | grep`). [R-GL-4]
2. Catalog moved aside → `render` prints the boxed warning; `gui` hard-stops with
   the remedy; `--all` continues to the next burst. [R-GL-3/4]
3. Linux/TkAgg live: picker appears with angles [R-DP-4]; hold an arrow ~3 s →
   "Refitting… input paused", no fit cascade, responsive right after [R-BG-13/14];
   click Accept *during* a refit → nothing; after → advances [R-BG-14]; × a
   background window → prints skip, session continues [R-BG-15]; finish the source
   marker → adoption (if any) printed + ingest verdict line [R-GL-3].
4. macOS regression: same steps once without `MPLBACKEND`. [R-BG-13]

## 8. OPEN items
| Item | Owner |
|---|---|
| R-GL-7 re-run/overwrite policy | Khushboo |
| R-DP-7 no-angle picker variant vs hard-stop-only | Khushboo |
| R-BG-18 width rule: warn vs block at Accept | Vikas |
| R-BG-19 residual y-scale policy | Khushboo |
| R-SM-3 third-click semantics | Khushboo |
| R-SM-6 source-pick bin snapping | Khushboo |

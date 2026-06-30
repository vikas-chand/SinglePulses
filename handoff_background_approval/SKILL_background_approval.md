# Skill: GBM Background-Interval Approval (AI-operated tool)

> **Full pipeline:** this is the detailed protocol for the **approval step** only.
> For the whole chain (approve → bin → fit → products), env/CALDB setup, and exact
> commands, read **`../AGENTS.md`** first.

**Purpose:** Get the pre-/post-burst background windows for every detector of the 106
single-pulse GRBs **approved** — by a human at the GUI **or** by an AI reading the
light-curve PNGs — and return one audited, stamped file the downstream pipeline consumes.
**Audience:** An AI assistant (Codex or Claude Code) operating this repo locally, with
or without a human reviewer present.
**Time required:** ~30 min setup + data; the human review is ~106 bursts × a few
detectors (clicking, can be done over several sittings — the tool resumes).
**Reusable:** Yes — re-runnable, resumable, idempotent.

---

## What this is, and your role as the AI

This behaves like a **tool in a larger pipeline**, but one step is irreducibly
**human-in-the-loop**: a person must *look* at each light curve and approve (or
adjust) the background window. That judgement is the entire point of the step.

**You (the AI) DO:** set up the environment, fetch the data, launch the GUI, monitor
progress, run QC, validate completeness, and package the result.
**You (the AI) DO NOT:** click "Accept" on the reviewer's behalf, invent windows, or
edit the output `.ecsv` by hand. **Never fabricate an approval.** If the reviewer is
not present, stop and say so — the deliverable is *human-approved* windows, and a
faked approval silently corrupts every downstream spectral fit.

Each accepted window is stamped with **who** approved it, **when** (UTC), and whether
they took the pre-drawn window unchanged or adjusted it — so "were these approved, and
by whom?" is answerable from the file itself.

---

## Inputs (already in the repo)

- `results/background_starting_points.ecsv` — the 418 (trigger, detector) rows with the
  auto-suggested background windows the GUI pre-draws for the reviewer to accept or
  drag-adjust.
- `results/single_pulse_grbs.ecsv` — the 106-burst sample list.
- `scripts/39_approve_all.py` — the Stage-1 approval driver (this is the tool). Per
  burst it opens a **detector picker**, a **background selector per detector**, then a
  **source marker** — so the reviewer judges the detector set, the windows, AND the
  source window (not just windows).
- `scripts/36_progress_check.py` — progress + QC tracker.
- `handoff_background_approval/fetch_tte.py` — the data downloader.

**NOT in the repo:** the raw TTE event data (too large). Phase 2 fetches it.

## Output (the deliverable)

`results/background_intervals.ecsv`, one row per (trigger, detector), columns:
```
TRIGGER_NAME, DETECTOR, BKG_NEG_START, BKG_NEG_STOP, BKG_POS_START, BKG_POS_STOP,
SRC_START, SRC_STOP, DET_ANGLE, APPROVED_BY, APPROVED_UTC, APPROVAL_MODE, WINDOW_SOURCE
```
`APPROVAL_MODE` ∈ {human_gui, ai_vision}; `WINDOW_SOURCE` ∈ {accepted_suggestion,
adjusted, drawn_fresh}. Target: **418 rows / 106 bursts, all with APPROVED_BY set**
(no "unknown").

---

## Phase 1 — Environment (light; NO threeML/fermitools)

This step does not fit spectra, so it does **not** need threeML or fermitools — keep
the environment small.

```bash
python -m venv .venv-picker && source .venv-picker/bin/activate   # or conda env
pip install -r handoff_background_approval/requirements.txt
python -c "import numpy, astropy, matplotlib; print('deps OK')"
```
GUI backend: on **Linux, run with `MPLBACKEND=TkAgg`** (the backend the picker is
verified against — it keeps the GUI alive across every per-detector window; without it
later detectors can crash with `TclError: ... "wm" ... application has been destroyed`).
macOS needs no prefix (Cocoa).

## Phase 2 — Data (download only what's needed)

```bash
python handoff_background_approval/fetch_tte.py            # all 106 bursts' TTE
# spot-check first:  python handoff_background_approval/fetch_tte.py --limit 3
```
Stdlib-only; pulls each needed TTE from the public HEASARC GBM archive into
`data/<trigger>/`. Re-runnable (skips files already present). If some files fail,
re-run, or ask Vikas to share the `data/` subset. (Alternative: Vikas shares `data/`
directly and you skip this phase.)

## Phase 3 — Launch the picker (human reviews)

```bash
MPLBACKEND=TkAgg python scripts/39_approve_all.py gui --all --approver "Khushboo Sharma"
```
`--approver` is REQUIRED — it stamps every accepted row. (One burst at a time:
`gui --trigger bn… ` instead of `gui --all`.) Tell the reviewer:

- Each detector opens showing the light curve with the suggested **pre** (negative
  time) and **post** (positive time) background windows pre-shaded, plus a polynomial
  fit overlay for a sanity check.
- **Accept** (green) — save this window, go to next detector.
- **Clear** (red) — wipe it and click 4 points yourself (2 pre, 2 post; time-ordered).
- **Skip GRB** (orange) — drop this whole GRB.
- **Quit** (gray) — stop; progress is saved per-detector, resume later by re-running.
- Judge windows from the light curve only — they should sit on flat background, avoid
  the burst and any nearby features, and be ~50–150 s wide each.

Resume anytime: re-running reviews only what's not yet accepted. To revisit one burst:
`--redo-grb bn090719063`. To redo everything: `--redo`.

## Phase 4 — Progress & QC (run anytime)

```bash
python scripts/36_progress_check.py
```
Reports completion (target 418/418, 106/106 bursts), flags duplicates, stray rows,
zero/negative-width or >200 s windows, and **any rows missing APPROVED_BY**. Also
prints the approver tally and the accepted_seed/adjusted/drawn_fresh breakdown.

## Phase 5 — Final validation (before returning)

Done only when ALL are true:
- `scripts/36_progress_check.py` shows 418/418 and 106/106;
- QC line reads "clean";
- every row has APPROVED_BY set (no "unknown");
- no zero-width or absurdly wide windows remain.

## Phase 6 — Return the deliverable

Send `results/background_intervals.ecsv` back to Vikas (commit on a branch + push, or
share the file). That single stamped file is the entire output of this step.

---

## Quality checklist
- [ ] Light env only (no threeML pulled in).
- [ ] `fetch_tte.py` finished with 0 missing (or missing files explicitly flagged).
- [ ] Picker launched with `--approver "<reviewer's name>"`.
- [ ] No approval was clicked or invented by the AI — a human reviewed each window.
- [ ] `scripts/36` shows 418/418, 106/106, QC clean, no missing APPROVED_BY.
- [ ] Deliverable is `results/background_intervals.ecsv` with the 9-column schema.

## Common pitfalls
- **No window appears, or it crashes after the first detector** (`TclError: ... "wm" ...
  application has been destroyed`) → run with `MPLBACKEND=TkAgg` (Linux).
- **Running in the threeML/fermitools env** → unnecessary and heavy; use the light env.
- **`--approver` missing** → the picker refuses to start (by design); supply it.
- **Editing the .ecsv by hand to "finish faster"** → forbidden; it destroys the
  approval guarantee. Only the GUI writes rows.
- **Wrong working directory** → run all commands from the repo root so the relative
  `results/` and `data/` paths resolve.
- **TTE download fails for old/odd bursts** → re-run `fetch_tte.py`; if still missing,
  Vikas shares those `data/<trigger>/` dirs.

## Hand-off — continue the full pipeline (you can run all of it)
This file is the detailed protocol for the **approval step only**. The same agent can
run the **rest of the pipeline** — install whatever is needed (incl. threeML); env
weight is not a reason to stop. See **`../AGENTS.md`** for the full chain, env/CALDB
setup, and exact commands. In short, the approved `background_intervals.ecsv` feeds:
- Bin: `python scripts/27b_reblock_3ml.py --bkg results/background_intervals.ecsv --out <fresh>/clean_blocks --sigma 5.0`
- Fit: `python scripts/29_refit_clean.py --bkg-file results/background_intervals.ecsv --blocks-dir results/clean_blocks --out-root <fresh>/clean_per_burst`
- Products: `scripts/31`–`38` (figures, tables, numbers, manifest).
Until the approved file exists and is fully approved, these run on PROVISIONAL
backgrounds and their numbers are not final.

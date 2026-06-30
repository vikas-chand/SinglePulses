# Background-Interval Approval — handoff bundle

This folder packages the **background-window approval** step of the Two_Breaks
single-pulse GRB pipeline so it can be run by a collaborator (Khushboo) on her own
machine, optionally driven by an AI assistant.

## What gets produced

One file: `results/background_intervals.ecsv` — the pre-/post-burst background windows
for every detector of all 106 GRBs, **each row stamped with who approved it and when**.
That file is the input to the authoritative re-block and spectral re-fit on Vikas's
side. Nothing downstream is final until it exists and is fully approved.

## Files here

| File | What it is |
|---|---|
| `INSTRUCTIONS_KHUSHBOO.md` | **Start here (human guide)** — step-by-step for running the approval, either AI-assisted or by hand in the GUI. |
| `SKILL_background_approval.md` | **Operating protocol for an AI assistant** — point Claude at this; it covers install → data → run → QC → return. |
| `fetch_tte.py` | Stdlib TTE downloader (no threeML) — gets only the event files the picker needs from the public HEASARC archive. |
| `requirements.txt` | Light dependencies (numpy, astropy, matplotlib, PyQt5). |

The tool itself is in the repo: `scripts/39_approve_all.py` (the Stage-1 approval
driver — detectors + background + source, GUI or AI) and
`scripts/36_progress_check.py` (progress + QC).

## Quick start (human)

```bash
# from the repo root, in a light env:
pip install -r handoff_background_approval/requirements.txt
python handoff_background_approval/fetch_tte.py            # download the TTE data
# Stage-1 approval (detectors + background + source), all bursts, resumable.
# On Linux, prefix MPLBACKEND=TkAgg (see note below) so the GUI survives all windows:
MPLBACKEND=TkAgg python scripts/39_approve_all.py gui --all --approver "Khushboo Sharma"
python scripts/36_progress_check.py                       # check progress + QC
```
(Do one burst at a time with `gui --trigger bn... ` instead of `gui --all`.)

> **Linux backend note.** On Linux, run the picker with `MPLBACKEND=TkAgg` (as
> shown). The picker survives opening a fresh selector window for every detector
> across all bursts only on a backend it has been verified against; `TkAgg` is
> that backend (a persistent hidden Tk root keeps the GUI alive between windows).
> Without forcing it, the first window may open and then later detectors can crash
> with `TclError: can't invoke "wm" command: application has been destroyed`, or
> Qt may fail to open a window at all. On macOS the default Cocoa backend works
> as-is; no prefix needed.

Per burst you get, in sequence: a **detector picker** (tick the NaI ≤50° + matching
BGO, pre-ticked), then a **background selector for each detector** (a suggested pre/post
window is drawn — **Accept** it, or **Clear** and click your own: 2 pre-burst points,
2 post-burst points), then a **source marker** (click the burst start, then end, on the
brightest NaI). Quit and re-run anytime; it resumes where you left off.
Target: 418 windows across 106 bursts.

## Quick start (AI-driven)

Open `SKILL_background_approval.md` and follow it top to bottom. Key rule: the AI sets
everything up and launches the GUI, but **a human must review and approve each window
— approvals are never clicked or invented by the AI.**

## Notes

- This step needs **no threeML / fermitools** — keep the environment light.
- Raw TTE data is not in the repo (too large); `fetch_tte.py` downloads it, or Vikas
  can share the `data/` directory.
- Run all commands from the repo root so `results/` and `data/` resolve.
